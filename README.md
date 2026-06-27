# 🤖 AI-Powered Project Management Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?style=for-the-badge&logo=fastapi)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-orange?style=for-the-badge)
![Railway](https://img.shields.io/badge/Deployed-Railway-purple?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Autonomous. Intelligent. Always On.**

[🌐 Live Demo](https://project-manager-bot-production.up.railway.app) • [📹 Demo Video](https://youtu.be/53on8kZlIF4?si=yg1Z66jGzQHhuhvk) • [📊 Analytics](https://project-manager-bot-production.up.railway.app/analytics)

</div>

---

## 🚀 What is this?

An AI-powered project management platform that combines **Generative AI** and **Agentic AI** to automate the entire project management lifecycle — task tracking, risk detection, client communication, and reporting — all without manual effort.

> Built for **Confluence 2.0** | Team Code Raiders

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧠 **AI Daily Briefing** | LLaMA 3.1 generates personalized morning summaries of tasks, risks & priorities |
| 💬 **AI Chat Assistant** | Ask "What's overdue?" or "What's my highest risk task?" in plain English |
| 📅 **AI Rescheduler** | Smart deadline suggestions for overdue tasks with reasoning |
| ⚠️ **Risk Engine** | Auto-classifies tasks as HIGH / MEDIUM / LOW risk based on deadlines |
| 📄 **Auto PDF Reports** | Completion reports generated & emailed to clients automatically |
| 📊 **Analytics Dashboard** | Live charts for task status and risk level breakdown |
| ⚡ **Real-time Dashboard** | Live countdown timers via Server-Sent Events (SSE) |
| 🌙 **Dark Mode** | Theme switcher with persistent preference |

---

## 🏗️ System Architecture
---

## ⚡ Agentic AI Flow
The system **acts without being asked** — true agentic behavior.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI / LLM** | Groq API + Meta LLaMA 3.1 8B Instant |
| **Backend** | FastAPI (Python) + SQLAlchemy + SQLite + APScheduler |
| **Frontend** | HTML5 + CSS3 + JavaScript + Chart.js + SSE |
| **Notifications** | Gmail SMTP + ReportLab PDF |
| **Deployment** | Railway + GitHub CI/CD |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/akashpoojari1450-crypto/project-manager-bot.git
cd project-manager-bot/project-manager-bot/project-manager-bot

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your keys

# Run the application
uvicorn main:app --reload --port 8000
```

### Environment Variables

```env
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key
```

---

## 📁 Project Structure
---

## 📈 Impact Metrics

- ⏰ **Saves 2-3 hours daily** per project manager
- 📄 **100% automated** client report delivery
- ⚡ **<1 second** AI response time (Groq inference)
- 🔄 **24/7 autonomous** background monitoring
- 🌐 **Production deployed** and accessible globally

---

## 🔮 Future Roadmap

- [ ] Multi-user notification system (per-user email & WhatsApp)
- [ ] React Native mobile app (iOS & Android)
- [ ] SaaS platform with Stripe payments
- [ ] Team collaboration with role-based access
- [ ] Client portal with zero-login access
- [ ] Zapier & webhook integrations
- [ ] White-label solution for agencies
- [ ] AI project timeline prediction

---

## 🔗 Links

- 🌐 **Live App**: https://project-manager-bot-production.up.railway.app
- 📹 **Demo Video**: https://youtu.be/53on8kZlIF4?si=yg1Z66jGzQHhuhvk
- 📊 **Analytics**: https://project-manager-bot-production.up.railway.app/analytics

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ by <strong>Akash S</strong> | Team Code Raiders | Confluence 2.0
</div>
