# 🤖 JobScout Bot

A Telegram bot that scans 20+ job platforms every 4 hours and sends you jobs matching your resume — completely free.

## Platforms Covered
- **JobSpy**: LinkedIn, Indeed, Naukri, Glassdoor, Google Jobs, ZipRecruiter, Bayt
- **Free APIs**: Remotive, Jobicy (ML/AI/DS tags)
- **Via Google Jobs**: Wellfound, Foundit, Shine, TimesJobs, Monster, SimplyHired, Internshala, Hirist and more

## Bot Commands
| Command | Description |
|---------|-------------|
| `/start` | Start the bot and enable scanning |
| `/upload` | Upload a resume (PDF or paste text) |
| `/list` | See all active resumes |
| `/delete` | Delete a resume |
| `/scan` | Trigger a manual scan right now |
| `/stop` | Pause scanning |
| `/status` | See bot status |

## Setup Guide

### 1. Clone this repo
```bash
git clone https://github.com/YOUR_USERNAME/jobscout-bot.git
cd jobscout-bot
```

### 2. Get your API keys

**Telegram Bot Token:**
- Open Telegram → search @BotFather
- Send `/newbot` and follow instructions
- Copy the token

**Gemini API Key (free):**
- Go to https://aistudio.google.com/apikey
- Click "Create API Key"
- Copy it

**Your Telegram User ID:**
- Open Telegram → search @userinfobot
- Send `/start`
- Copy your numeric ID

### 3. Deploy to Render

1. Go to https://render.com and sign up with GitHub
2. Click "New" → "Blueprint"
3. Connect your GitHub repo
4. Render will detect `render.yaml` automatically
5. Add environment variables:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `GEMINI_API_KEY` = your Gemini key
   - `AUTHORIZED_USER_ID` = your Telegram numeric user ID
6. Click Deploy

### 4. Start using
- Open Telegram → find your bot
- Send `/start`
- Send `/upload` and upload your resume PDF
- Give it a label like "ML Engineer"
- Send `/scan` for immediate results or wait for auto-scan

## Updating Your Resume
Just send `/upload` again anytime. You can have multiple resumes active simultaneously — each gets its own set of matched jobs.

## Scoring
- 🟢 8-10 — Strong match
- 🟡 6-7 — Good match  
- 🔴 Below 6 — Filtered out (you won't see these)

## Tech Stack
- `python-telegram-bot` — Telegram interface
- `python-jobspy` — Multi-platform job scraping
- `google-generativeai` — Gemini 2.0 Flash for scoring (free tier)
- `APScheduler` — 4-hour scan scheduling
- `SQLite` — Resume and job history storage
- `Render` — Free hosting
