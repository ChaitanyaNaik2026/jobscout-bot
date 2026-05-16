import os
import asyncio
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import PyPDF2
import io
from scanner import scan_and_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
AUTHORIZED_USER = os.environ.get("AUTHORIZED_USER_ID")  # Your Telegram user ID
SCAN_INTERVAL_HOURS = int(os.environ.get("SCAN_INTERVAL_HOURS", 4))

DB_PATH = "data/jobscout.db"

# ── Database ────────────────────────────────────────────────────────────────

def init_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs("resumes", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            label TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            active INTEGER DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_url TEXT PRIMARY KEY,
            seen_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_resumes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, label, created_at FROM resumes WHERE active=1")
    rows = c.fetchall()
    conn.close()
    return rows

def get_resume_content(resume_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT content FROM resumes WHERE id=? AND active=1", (resume_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def add_resume(name, content, label=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO resumes (name, content, label) VALUES (?,?,?)", (name, content, label))
    conn.commit()
    conn.close()

def delete_resume(resume_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE resumes SET active=0 WHERE id=?", (resume_id,))
    conn.commit()
    conn.close()

def is_seen(url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM seen_jobs WHERE job_url=?", (url,))
    result = c.fetchone()
    conn.close()
    return result is not None

def mark_seen(url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO seen_jobs (job_url) VALUES (?)", (url,))
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, str(value)))
    conn.commit()
    conn.close()

# ── Helpers ──────────────────────────────────────────────────────────────────

def is_authorized(update: Update) -> bool:
    if not AUTHORIZED_USER:
        return True
    return str(update.effective_user.id) == AUTHORIZED_USER

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

# ── Scheduler ────────────────────────────────────────────────────────────────

scheduler = AsyncIOScheduler()
app_ref = None

async def scheduled_scan():
    global app_ref
    if app_ref is None:
        return
    resumes = get_resumes()
    if not resumes:
        logger.info("No active resumes, skipping scan.")
        return

    chat_id = get_setting("chat_id")
    if not chat_id:
        logger.info("No chat_id set yet.")
        return

    await app_ref.bot.send_message(chat_id=chat_id, text="🔍 Scanning for fresh jobs across 20+ platforms...")

    for resume_row in resumes:
        resume_id, name, label, _ = resume_row
        content = get_resume_content(resume_id)
        if not content:
            continue

        display = label or name
        await app_ref.bot.send_message(chat_id=chat_id, text=f"📄 Scanning for resume: *{display}*", parse_mode="Markdown")

        try:
            jobs = await asyncio.get_event_loop().run_in_executor(None, scan_and_score, content)
        except Exception as e:
            logger.error(f"Scan error: {e}")
            await app_ref.bot.send_message(chat_id=chat_id, text=f"⚠️ Scan error for {display}: {str(e)[:200]}")
            continue

        new_jobs = [j for j in jobs if not is_seen(j.get("job_url", ""))]

        if not new_jobs:
            await app_ref.bot.send_message(chat_id=chat_id, text=f"✅ No new jobs found for *{display}* this round.", parse_mode="Markdown")
            continue

        await app_ref.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Found *{len(new_jobs)}* new jobs for *{display}*:",
            parse_mode="Markdown"
        )

        for job in new_jobs[:15]:  # Max 15 per resume per scan
            mark_seen(job.get("job_url", ""))
            score = job.get("score", 0)
            emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
            msg = (
                f"{emoji} *Score: {score}/10*\n"
                f"🏢 *{job.get('company','N/A')}*\n"
                f"💼 {job.get('title','N/A')}\n"
                f"📍 {job.get('location','N/A')}\n"
                f"🌐 {job.get('site','N/A')}\n"
                f"📅 Posted: {job.get('date_posted','N/A')}\n"
                f"🔗 [Apply Here]({job.get('job_url','#')})"
            )
            try:
                await app_ref.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", disable_web_page_preview=True)
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Send error: {e}")

# ── Command Handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    set_setting("chat_id", update.effective_chat.id)
    set_setting("scanning", "true")

    if not scheduler.running:
        scheduler.start()

    await update.message.reply_text(
        "👋 *Welcome to JobScout Bot!*\n\n"
        "I scan 20+ job platforms every few hours and send you jobs matching your resume.\n\n"
        "*Commands:*\n"
        "📎 `/upload` — Upload a resume (PDF or text)\n"
        "📋 `/list` — See your active resumes\n"
        "🗑 `/delete` — Remove a resume\n"
        "🔍 `/scan` — Trigger a manual scan now\n"
        "⏹ `/stop` — Stop scanning\n"
        "▶️ `/start` — Resume scanning\n"
        "ℹ️ `/status` — Current bot status\n\n"
        "Start by uploading your resume with `/upload` 👆",
        parse_mode="Markdown"
    )

async def cmd_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    set_setting("awaiting_upload", "true")
    await update.message.reply_text(
        "📎 *Upload your resume now.*\n\n"
        "You can send:\n"
        "• A *PDF file* directly\n"
        "• Plain *text* — just paste your resume\n\n"
        "After I receive it, I'll ask you for a label (e.g. 'ML Engineer', 'Data Scientist').",
        parse_mode="Markdown"
    )

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    resumes = get_resumes()
    if not resumes:
        await update.message.reply_text("📭 No active resumes. Use /upload to add one.")
        return
    msg = "📋 *Your Active Resumes:*\n\n"
    for r in resumes:
        rid, name, label, created = r
        display = label or name
        date = created[:10] if created else "unknown"
        msg += f"*#{rid}* — {display}\n📅 Added: {date}\n\n"
    msg += "Use /delete to remove one."
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    resumes = get_resumes()
    if not resumes:
        await update.message.reply_text("📭 No resumes to delete.")
        return
    keyboard = []
    for r in resumes:
        rid, name, label, _ = r
        display = label or name
        keyboard.append([InlineKeyboardButton(f"🗑 #{rid} — {display}", callback_data=f"del_{rid}")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")])
    await update.message.reply_text(
        "Which resume do you want to delete?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    resumes = get_resumes()
    if not resumes:
        await update.message.reply_text("📭 No resumes uploaded yet. Use /upload first.")
        return
    await update.message.reply_text("🔍 Starting manual scan now...")
    await scheduled_scan()

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    set_setting("scanning", "false")
    if scheduler.running:
        scheduler.pause()
    await update.message.reply_text("⏹ Scanning paused. Send /start to resume.")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    resumes = get_resumes()
    scanning = get_setting("scanning", "false")
    last_scan = get_setting("last_scan", "Never")
    status = "🟢 Active" if scanning == "true" else "🔴 Paused"
    await update.message.reply_text(
        f"*JobScout Status*\n\n"
        f"Scanner: {status}\n"
        f"Active Resumes: {len(resumes)}\n"
        f"Scan Interval: Every {SCAN_INTERVAL_HOURS} hours\n"
        f"Last Scan: {last_scan}\n"
        f"Platforms: 20+",
        parse_mode="Markdown"
    )

# ── Message Handler (resume upload) ──────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    awaiting = get_setting("awaiting_upload")
    awaiting_label = get_setting("awaiting_label")

    # Handle label input
    if awaiting_label == "true":
        label = update.message.text.strip()
        temp_name = get_setting("temp_resume_name")
        temp_content = get_setting("temp_resume_content")
        if temp_content:
            add_resume(temp_name, temp_content, label)
            set_setting("awaiting_label", "false")
            set_setting("temp_resume_name", "")
            set_setting("temp_resume_content", "")
            await update.message.reply_text(
                f"✅ Resume *\"{label}\"* saved successfully!\n\n"
                f"Use /scan to scan now or wait for the next automatic scan.",
                parse_mode="Markdown"
            )
        return

    # Handle text resume
    if awaiting == "true" and update.message.text:
        content = update.message.text.strip()
        if len(content) < 100:
            await update.message.reply_text("⚠️ That seems too short for a resume. Please paste your full resume text.")
            return
        set_setting("temp_resume_name", f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        set_setting("temp_resume_content", content)
        set_setting("awaiting_upload", "false")
        set_setting("awaiting_label", "true")
        await update.message.reply_text(
            "✅ Resume received!\n\n"
            "What label should I give this resume?\n"
            "e.g. *ML Engineer*, *Data Scientist*, *AI Engineer*",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("Use /upload to upload a resume, or /help to see commands.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    doc = update.message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("⚠️ Please upload a PDF file.")
        return

    await update.message.reply_text("📥 Downloading your resume PDF...")
    file = await context.bot.get_file(doc.file_id)
    pdf_bytes = bytes(await file.download_as_bytearray())

    try:
        content = extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Could not read PDF: {e}")
        return

    if len(content) < 100:
        await update.message.reply_text("⚠️ Could not extract enough text from this PDF. Try pasting as plain text instead.")
        return

    set_setting("temp_resume_name", doc.file_name)
    set_setting("temp_resume_content", content)
    set_setting("awaiting_upload", "false")
    set_setting("awaiting_label", "true")

    await update.message.reply_text(
        f"✅ PDF received and parsed!\n\n"
        f"What label should I give this resume?\n"
        f"e.g. *ML Engineer*, *Data Scientist*, *AI Engineer*",
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "del_cancel":
        await query.edit_message_text("❌ Cancelled.")
        return

    if data.startswith("del_"):
        resume_id = int(data.split("_")[1])
        delete_resume(resume_id)
        await query.edit_message_text(f"🗑 Resume #{resume_id} deleted successfully.")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    global app_ref
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()
    app_ref = app

    # Schedule scans
    scheduler.add_job(scheduled_scan, "interval", hours=SCAN_INTERVAL_HOURS, id="job_scan")
    scheduler.start()

    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("upload", cmd_upload))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("JobScout Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
