# FRIDAY v2.9.0

> **A Personal AI Operating System.**
>
> Not a chatbot. Not a frontend. An intelligent system that reasons, plans, remembers, chooses tools, and acts on behalf of the user.
> 
> Inspired by JARVIS. Built for real work.

---

## Quick Install

### 1. One-liner (easiest — all platforms)
```bash
curl -fsSL https://raw.githubusercontent.com/AslamOP/Friday/main/install/friday-installer.sh | bash
```
On next login, FRIDAY asks permission. Say yes and it starts automatically after every login.

### 2. Direct install from GitHub (no clone needed)
Requires Python ≥3.11 and pip.
```bash
pip install git+https://github.com/AslamOP/Friday.git
friday                    # start REPL
friday --gui              # start desktop UI
friday --daemon           # start background daemon
```

### 3. Clone + dev install (for hacking)
```bash
git clone https://github.com/AslamOP/Friday.git
cd Friday
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
friday --cli
```

---

### Platform-specific notes

**Arch Linux**
```bash
sudo pacman -S python python-pip
pip install git+https://github.com/AslamOP/Friday.git
friday
```

**Debian / Ubuntu**
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
pip install git+https://github.com/AslamOP/Friday.git
friday
```

**macOS**
```bash
brew install python@3.11
pip install git+https://github.com/AslamOP/Friday.git
friday
```

**Windows (WSL2)**
```powershell
wsl --install -d Ubuntu
# In WSL:
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
pip install git+https://github.com/AslamOP/Friday.git
friday
```

### After install
```bash
friday                    # CLI REPL (works immediately — Zen free tier active)
friday --gui              # Desktop GUI (PyQt6, requires display server)
friday --daemon           # Background daemon with IPC
friday --help             # All options
```

---

## What FRIDAY Is

FRIDAY is a **local-first, modular AI operating system** that orchestrates language models, specialized agents, tools, memory, and planning through a unified intelligence layer.

The interface is just a window into the system. The real product is the brain underneath — a collection of autonomous agents working together.

You do not interact with a language model. You interact with an intelligent assistant that understands context, challenges your thinking, and decides how to help.

---

## What FRIDAY Is Not

- Not ChatGPT
- Not Claude
- Not Open WebUI or LibreChat
- Not another LLM frontend
- Not a chatbot with extra features

Those solve "chat." FRIDAY solves **personal intelligence**.

---

## Core Philosophy

```
User
  ↓
Orchestrator (Intent + Context)
  ↓
Agent Router
  ↓
Selected Agent(s)
  ↓
Memory + Tools + Model Router
  ↓
OmniRoute → Best Model
  ↓
Execution + Response
```

The language model is one component of a larger system. FRIDAY thinks before answering. Agents act before being asked.

---

## The Agents

| Agent | Role | Trigger |
|-------|------|---------|
| **Mentor** | Challenges ideas, finds flaws, suggests risks | User presents idea, asks for opinion, or FRIDAY detects low-confidence plan |
| **Planner** | Creates timelines, tracks deadlines, monitors progress | Complex multi-step request, scheduling, project planning |
| **Software Engineer** | Writes code, debugs, tests, uses Cursor IDE | "Build...", "Fix...", "Refactor...", "Add feature..." |
| **Research Scientist** | Reads papers, synthesizes, finds gaps, writes reports | "Research...", "Compare...", "Read these papers..." |
| **CAD Engineer** | SolidWorks, ANSYS, MATLAB scripts, optimization | "Design...", "Simulate...", "Optimize..." |
| **Automation Engineer** | Scripts, cron, monitoring, background tasks | "Automate...", "Watch...", "Schedule..." |
| **Knowledge Manager** | Indexes files, answers from personal knowledge | Background (always), or "What do I know about..." |
| **Study Agent** | Offline-first folder-based learning, study guides | "Study...", "Set folder...", "Generate guide..." |
| **Gaming Assistant** | Performance monitoring, walkthroughs, optimizations | Game detected, "Help with...", performance drops |

Every agent has:
- Its own memory slice
- Its own tool set
- Its own model preference via OmniRoute
- The ability to delegate to other agents

---

## Provider System

FRIDAY works out of the box with **zero configuration** using Zen API's free tier. Add your own providers anytime.

**Default providers shipped:**

| Provider | Type | Works OOTB | Activate |
|----------|------|------------|----------|
| Zen | Cloud | ✅ Free, no key | Automatic |
| OpenRouter | Cloud | If key in `.env` | `/provider key openrouter sk-...` |
| Ollama | Local | If ollama is running | Start `ollama serve` |
| OpenAI | Cloud | Needs key | `/provider key openai sk-...` |
| Anthropic | Cloud | Needs key | `/provider key anthropic sk-...` |
| Google Gemini | Cloud | Needs key | `/provider key google ...` |
| GitHub Copilot | Cloud | Needs token | `/provider key github-copilot ...` |

**Provider commands in REPL:**

```
/providers                    List all providers and their status
/provider key <name> <key>    Set API key (auto-fetches models)
/provider add <name> <type> <endpoint>   Add custom provider
/provider refresh <name>      Re-check status + fetch models
/provider remove <name>       Remove user-added provider
```

Routing auto-selects the first online provider by priority: Zen → OpenRouter → Ollama → OpenAI → Anthropic → Google → GitHub Copilot. If one fails, the next is tried automatically.

---

## Memory

FRIDAY remembers:
- Projects and their contexts
- Conversations (not just chat history — intent, decisions, outcomes)
- Coding style, preferred patterns, tech stack
- Research interests, paper library, citation style
- Academic subjects, weak topics, PYQ patterns
- Personal preferences, goals, habits
- Long-term learnings (improves over time)

Memory is a **knowledge graph** — entities, relations, projects — not just a database.

---

## Tools

FRIDAY can use tools when needed. The user does not manually invoke them. FRIDAY decides.

- Terminal (safe shell with blocklist + timeout)
- Browser (Playwright automation)
- Filesystem (read/write/organize)
- Code Editor (Cursor IDE integration)
- Git (commit, branch, diff, push)
- Docker (container management)
- System Monitor (CPU/GPU/RAM alerts)
- Steam / Discord / OBS APIs
- PDF Reader + OCR
- Camera / Clipboard / Notifications

---

## User Experience

The interface should feel like JARVIS — calm, futuristic, intentional. Blue holographic aesthetic.

Not flashy. Not cluttered. Minimal. Elegant. Professional.

The user opens FRIDAY and sees:
- System status (CPU, RAM, GPU, network)
- Holographic core (animated rings, scanning arc)
- Active agents (which are online, which are working)
- Recent activity log
- Command interface (type or speak)

Then: **"How can I help?"**

The interface is the window into FRIDAY. It is not the product itself.

---

## Interfaces

- **CLI** — Primary interface. Always available.
- **Desktop GUI** — Frameless PyQt6 window with holographic display, live system stats, agent panel, voice input, editable profile, provider settings. Launch with `friday --gui`.
- **Voice** — Speech-to-text (whisper), TTS (piper). Wake word support.
- **System Tray** — Quick actions: Open GUI, Open REPL, Check Status, Refresh Providers.
- **Cursor Plugin** — FRIDAY inside your IDE.
- **Web Dashboard** — Optional. For monitoring and advanced settings.

---

Or as a systemd user service (after clone + setup):
```bash
systemctl --user enable friday
systemctl --user start friday
```

---

## Environment Variables

```bash
# OpenRouter (cloud inference routing)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx

# Ollama (local inference)
OLLAMA_URL=http://127.0.0.1:11434

# Server
FRIDAY_PORT=8000
FRONTEND_URL=http://localhost:5173
DATABASE_URL=sqlite+aiosqlite:///./friday.db

# Optional integrations
CURSOR_PATH=/usr/bin/cursor
STEAM_API_KEY=xxx
DISCORD_BOT_TOKEN=xxx
```

---

## Development Principles

1. **Agent-first, not chat-first.** Every feature must fit the agent architecture.
2. **Headless core.** The brain runs as a service. UI is optional.
3. **Proactive by default.** FRIDAY should alert, suggest, act without being asked.
4. **Mentor challenges.** FRIDAY should disagree when the user is wrong.
5. **One file at a time.** Modify, review, confirm, then proceed.
6. **Preserve existing functionality.** Never break what works.
7. **Never sacrifice architecture for convenience.** No shortcuts.
8. **Think long-term.** Will this design hold in 6 months? 2 years?

---

## License

MIT — Build your own intelligence.

> *"The future is already here — it's just not evenly distributed."*
> **— William Gibson**
