# 🔮 ORPHEUS — Omni-Responsive Processing Matrix

> *A futuristic, privacy-first AI command center — your personal JARVIS.*
> *The Primary Purpose Of This AI is Holistic User Support for example System Monitor, AI chat System, And this can work Offline as well and more...*

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green?style=flat-square&logo=fastapi)
![License](https://img.shields.io/badge/License-Private-red?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active_Development-cyan?style=flat-square)

---

## 🌟 System Overview: What is ORPHEUS?

ORPHEUS (Omni-Responsive Processing Matrix) is an advanced, privacy-first AI command center designed to act as your personal, highly capable digital assistant. Engineered with a multi-agent architecture, ORPHEUS seamlessly integrates natural language processing, real-time web research, autonomous file operations, and code generation into a single, cohesive interface.

**Why ORPHEUS is valuable to you:**
- **Absolute Privacy:** Powered by local LLM inference (Ollama) and robust AES-256 encryption, ensuring your data and conversations never leave your machine.
- **Jarvis-like Voice Control:** Navigate, execute commands, and converse entirely hands-free using its integrated speech recognition functionality.
- **Autonomous Task Execution:** Delegate complex tasks to 5 specialized AI agents that can securely read/write files in a sandboxed environment, search the web, and solve coding problems.
- **Futuristic Interface:** Monitor your system metrics and interact with the AI through a stunning, real-time holographic dashboard.

Whether you're automating workflows, managing projects, or researching new topics, ORPHEUS is the ultimate copilot that supercharges your productivity.

---

## ⚡ Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🧠 **Multi-Agent System** | ✅ Active | 5 specialized AI agents (Commander, FileOS, WebResearch, Creator, LLM) |
| 🎙️ **Voice Commands** | ✅ Active | Browser-based speech recognition (Chrome/Edge) |
| 📊 **Real-time Dashboard** | ✅ Active | Futuristic holographic UI with live system metrics |
| 🌐 **Web Research** | ✅ Active | Internet search via DuckDuckGo integration |
| 📁 **File Operations** | ✅ Active | Sandboxed file read/write/execute in workspace |
| 🔐 **Encrypted Security** | ✅ Active | AES-256 encryption, voice biometrics, encrypted logs |
| 💬 **Neural Chat** | ✅ Active | Conversational AI interface with command history |
| 🤖 **LLM Integration** | ✅ Active | Local Ollama inference (TinyLlama default) |

---

## 🏗️ Architecture

```
ORPHEUS/
├── main.py              # FastAPI server & WebSocket orchestrator
├── agents/
│   └── harness.py       # Multi-agent harness (Commander, FileOS, Web, Creator, LLM)
├── core/
│   └── security.py      # AES encryption, voice biometrics, secure logging
├── voice/
│   └── module.py        # Server-side STT/TTS (optional)
├── ui/
│   ├── index.html       # Holographic dashboard
│   ├── styles.css       # Futuristic design system
│   ├── app.js           # Core application logic & WebSocket client
│   └── particles.js     # Neural particle visualization
├── workspace/           # Sandboxed file operations directory
├── database/            # Encrypted SQLite database
├── logs/                # Encrypted system logs
├── .env                 # 🔒 Secrets (never committed)
└── .env.template        # Environment variable template
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/ORPHEUS.git
cd ORPHEUS
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.template .env
# Edit .env with your values (API keys, master password, etc.)
```

### 3. Run ORPHEUS

```bash
python main.py
```

Open **http://localhost:8000** in your browser (Chrome or Edge recommended for voice support).

---

## 🎙️ Voice Commands

Click the 🎙️ microphone button in the dashboard and speak:

- *"Search for the latest AI research papers"*
- *"Read file notes.txt"*
- *"List files in workspace"*
- *"Create a Python script that calculates fibonacci numbers"*
- *"What is quantum computing?"*

---

## 🔐 Security

- **All secrets** stored in `.env` (protected by `.gitignore`)
- **Database** encrypted with AES-256 via Fernet
- **System logs** double-encrypted (Fernet + SQLite)
- **Voice biometrics** hashed with SHA-256
- **File operations** sandboxed to `workspace/` directory
- **Dangerous commands** blocked at harness level

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Real-time | WebSocket (JSON protocol) |
| AI/LLM | Ollama (local inference) |
| Search | DuckDuckGo API |
| Security | Cryptography (Fernet/AES-256), PBKDF2 |
| Database | SQLite (encrypted fields) |
| Voice (Browser) | Web Speech API (STT + TTS) |
| Voice (Server) | Faster-Whisper, Coqui TTS (optional) |
| Monitoring | psutil (CPU, RAM, Disk) |
| Frontend | Vanilla JS, CSS3, Canvas API |

---

## 📄 License

Private project. All rights reserved.

---

*Lakshya->Anos-Voldigoad-8*
