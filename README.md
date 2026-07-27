# FRIDAY v2.7.0

> **A Personal AI Operating System.**
>
> Not a chatbot. Not a frontend. An intelligent system that reasons, plans, remembers, chooses tools, and acts on behalf of the user.
> 
> Inspired by JARVIS. Built for real work.

---

## Quick Install

```bash
bash <(curl -s https://raw.githubusercontent.com/AslamOP/Friday/master/install/setup.sh)
```

Or clone and install manually:

```bash
git clone https://github.com/AslamOP/Friday.git /opt/friday
cd /opt/friday
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python friday/main.py
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
| **Academic Tutor** | Teaches subjects, solves problems, generates PYQ questions | "Explain...", "Solve...", "Study...", "PYQ..." |
| **Gaming Assistant** | Performance monitoring, walkthroughs, optimizations | Game detected, "Help with...", performance drops |

Every agent has:
- Its own memory slice
- Its own tool set
- Its own model preference via OmniRoute
- The ability to delegate to other agents

---

## AI Routing (OmniRoute)

Users never select models. FRIDAY decides automatically.

| Task Type | Route |
|-----------|-------|
| Coding | Local Qwen Coder (Ollama) or DeepSeek via OmniRoute |
| Large reasoning | Claude / Gemini via OmniRoute |
| Research | Best reasoning model via OmniRoute |
| Image understanding | Vision model via OmniRoute |
| Fast chat | Local Ollama |
| Offline | Ollama only |

If one provider fails, OmniRoute automatically falls back to another.

Manual provider selection exists only in Advanced Settings for debugging.

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
- **Voice** — Speech-to-text (whisper), TTS (piper). Wake word support.
- **System Tray** — KDE widget. Quick commands, status, notifications.
- **Cursor Plugin** — FRIDAY inside your IDE.
- **Web Dashboard** — Optional. For monitoring and advanced settings.

---

## Quick Start

### Prerequisites (Arch Linux)
```bash
sudo pacman -S python nodejs npm tesseract-data-eng xclip maim scrot
# Ollama for local models
curl -fsSL https://ollama.com/install.sh | sh
```

### Setup
```bash
cd friday
./setup.sh        # Installs deps, sets up .env
nano .env         # Add your OpenRouter API key
```

### Run
```bash
./start.sh        # Starts FRIDAY core + optional UI
```

Or as a systemd user service:
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
