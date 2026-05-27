# 🤖 JobScout Bot

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![APScheduler](https://img.shields.io/badge/APScheduler-FF6F00?style=for-the-badge&logo=clockify&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)
![JobSpy](https://img.shields.io/badge/JobSpy-0A66C2?style=for-the-badge&logo=briefcase&logoColor=white)

A Telegram bot that scans **20+ job platforms** every 4 hours and sends you jobs matching your resume — completely free.

---

## 🌐 Platforms Covered

| Source | Platforms |
|---|---|
| **JobSpy** | LinkedIn, Indeed, Naukri, Glassdoor, Google Jobs, ZipRecruiter, Bayt |
| **Free APIs** | Remotive, Jobicy (ML / AI / DS tags) |
| **Via Google Jobs** | Wellfound, Foundit, Shine, TimesJobs, Monster, SimplyHired, Internshala, Hirist, and more |

---

## 📌 Bot Commands

| Command | Description |
|---|---|
| `/start` | Start the bot and enable scanning |
| `/upload` | Upload a resume (PDF or paste text) |
| `/list` | See all active resumes |
| `/delete` | Delete a resume |
| `/scan` | Trigger a manual scan right now |
| `/stop` | Pause scanning |
| `/status` | See bot status |

---

## ⚙️ Setup Guide

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/jobscout-bot.git
cd jobscout-bot
```

### 2️⃣ Get Your API Keys

**🤖 Telegram Bot Token:**
- Open Telegram → search `@BotFather`
- Send `/newbot` and follow the instructions
- Copy the generated **Bot Token**

**✨ Gemini API Key (free):**
- Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- Click **"Create API Key"** and copy it

**🪪 Your Telegram User ID:**
- Open Telegram → search `@userinfobot`
- Send `/start` and copy your numeric **User ID**

### 3️⃣ Deploy to Render

1. Go to [https://render.com](https://render.com) and sign up with GitHub
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repo
4. Render will detect `render.yaml` automatically
5. Add the following environment variables:

   | Variable | Value |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | Your bot token |
   | `GEMINI_API_KEY` | Your Gemini API key |
   | `AUTHORIZED_USER_ID` | Your Telegram numeric user ID |

6. Click **Deploy**

### 4️⃣ Start Using the Bot

1. Open Telegram → find your bot
2. Send `/start`
3. Send `/upload` and attach your resume PDF
4. Give it a label like `"ML Engineer"`
5. Send `/scan` for immediate results or wait for the auto-scan every 4 hours

---

## 🔄 Updating Your Resume

Send `/upload` anytime to add a new resume. You can have **multiple resumes active simultaneously** — each gets its own set of matched jobs.

---

## 🎯 Match Scoring

| Score | Label | Meaning |
|---|---|---|
| 🟢 8–10 | Strong Match | Highly relevant — sent to you immediately |
| 🟡 6–7 | Good Match | Worth reviewing |
| 🔴 Below 6 | Filtered Out | Not shown to reduce noise |

---

## 🛠️ Tech Stack

![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)
![JobSpy](https://img.shields.io/badge/python--jobspy-0A66C2?style=for-the-badge&logo=briefcase&logoColor=white)
![Gemini](https://img.shields.io/badge/google--generativeai-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![APScheduler](https://img.shields.io/badge/APScheduler-FF6F00?style=for-the-badge&logo=clockify&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

| Library | Purpose |
|---|---|
| `python-telegram-bot` | Telegram bot interface |
| `python-jobspy` | Multi-platform job scraping |
| `google-generativeai` | Gemini 2.0 Flash for resume scoring (free tier) |
| `APScheduler` | 4-hour automatic scan scheduling |
| `SQLite` | Resume and job history storage |
| `Render` | Free cloud hosting |

---

## 👨‍💻 Developer

**Chaitanya Naik**

[![GitHub](https://img.shields.io/badge/GitHub-ChaitanyaNaik2026-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ChaitanyaNaik2026)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-naikchaitanya-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/naikchaitanya)

---

## ⚠️ Disclaimer

This project is intended for **educational purposes only**. Job scraping may be subject to the Terms of Service of individual platforms. Use responsibly and at your own risk.
