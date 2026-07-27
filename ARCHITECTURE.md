# FRIDAY v2.9 Architecture

## Overview

FRIDAY is a layered, modular AI operating system. Each layer has a single responsibility and communicates through well-defined interfaces. Agent-first, not chat-first.

```
INTERFACE LAYER
  CLI (primary) | Desktop GUI (PyQt6) | Voice | System Tray

ORCHESTRATOR
  Intent Parser → Context Engine → Agent Router → Task Delegator

AGENT POOL
  Mentor | Planner | Software Engineer | Research Scientist
  Automation Engineer | Knowledge Manager | Study Agent | Gaming Assistant

TOOLS
  ShellSandbox | FileOps | System Monitor | Web Search | Browser | Git

MEMORY
  UserProfile | ProjectMemory | KnowledgeGraph | ConversationStore
  SemanticStore | VectorStore | EmbeddingService | EntityExtractor

ROUTER
  ProviderRegistry — Generic OpenAI-compatible client
  zen | openrouter | openai | anthropic | google | github-copilot | ollama
```

## Layer Breakdown

### Interface Layer
- **CLI** (`friday/interfaces/cli/`) — Rich-powered REPL with streaming markdown, voice mode, provider management. Primary interface.
- **Desktop GUI** (`friday/interfaces/desktop/`) — Frameless PyQt6 window. QStackedWidget routes Dashboard ↔ Profile. HoloSphere animation, live CPU/RAM/GPU/disk stats, AgentPanel, CommandBar with voice toggle, OutputArea with markdown rendering. Settings dialog for provider management. Keyboard shortcuts.
- **Voice** (`friday/interfaces/audio/`) — Speech-to-text (SpeechRecognition + Google/Sphinx fallback), Text-to-speech (edge-tts / pyttsx3).
- **System Tray** (`friday/interfaces/desktop/tray.py`) — pystray icon. Quick actions: Open GUI, Open REPL, Check Status, Refresh Providers.

### Core
- **Orchestrator** (`friday/core/orchestrator.py`) — Central brain. Manages lifecycle, agent registration, intent parsing, context, persistence.
- **Intent Parser** (`friday/core/intent_parser.py`) — Classifies user input into intent types (coding, research, planning, study, etc.).
- **Context Engine** (`friday/core/context_engine.py`) — Loads relevant memory (KG entities, conversation history, user profile).
- **Agent Router** (`friday/core/agent_router.py`) — Routes intent → best-fit agent based on confidence scores.
- **Task Delegator** (`friday/core/task_delegator.py`) — Breaks complex requests into subtasks, dispatches to specialist agents, merges results.
- **Agent Bus** (`friday/core/agent_bus.py`) — Pub/sub message bus for inter-agent communication.
- **Event Bus** (`friday/core/event_bus.py`) — System-wide event dispatch.
- **Task Scheduler** (`friday/core/task_scheduler.py`) — Background task scheduling.

### Agents
Every agent is a subclass of `BaseAgent` with its own system prompt, memory slice, tool set, and model preference.

| Agent | Package | Role |
|-------|---------|------|
| Mentor | `friday/agents/mentor/` | Challenges ideas, finds flaws, suggests risks |
| Planner | `friday/agents/planner/` | Timelines, deadlines, project tracking |
| Software Engineer | `friday/agents/software_engineer/` | Code, debug, test, Cursor IDE integration |
| Research Scientist | `friday/agents/research_scientist/` | Papers, synthesis, reports |
| Automation Engineer | `friday/agents/automation_engineer/` | Scripts, cron, monitoring |
| Knowledge Manager | `friday/agents/knowledge_manager/` | File indexing, personal knowledge Q&A |
| Study Agent | `friday/agents/study/` | Offline-first folder-based learning, study guides |
| Gaming Assistant | `friday/agents/gaming_assistant/` | Game profiles, performance, walkthroughs |

### Tools
- **ShellSandbox** (`friday/tools/shell_sandbox.py`) — Safe shell execution with blocklist + timeout.
- **FileOps** (`friday/tools/file_ops.py`) — File read/write/search/tree operations.
- **SystemMonitor** (`friday/tools/system_monitor.py`) — CPU (percent/cores/temp), RAM, disk, GPU (nvidia-smi).
- **Web Search** (`friday/tools/web_search.py`) — DuckDuckGo search via httpx.
- **Browser** (`friday/tools/browser.py`) — Playwright-based web automation.
- **Git** (`friday/tools/git_tool.py`) — Git operations.
- **GitHub Installer** (`friday/tools/github_installer.py`) — Clone and install GitHub repos.

### Memory
- **UserProfile** — Singleton. Name, title, coding style, writing style, preferences, goals, skills.
- **ProjectMemory** — Singleton. Project CRUD with metadata.
- **KnowledgeGraph** — Entity-relation store for long-term knowledge.
- **ConversationStore** — SQLite-backed conversation history.
- **SemanticStore** — Embedding-based semantic search.
- **VectorStore** — ChromaDB-backed vector storage.
- **EmbeddingService** — Ollama embedding for semantic search.
- **EntityExtractor** — Regex-based entity extraction.
- **Persistence** — Auto-save orchestration for all memory systems.

### Router
- **ProviderRegistry** — Single generic OpenAI-compatible client. Routes to first online provider by priority. 7 built-in providers: zen (free OOTB), openrouter, openai, anthropic, google, github-copilot, ollama. Auto-fetches models from `/models` endpoint on key set.

### Plugin System
- Simple plugin system under `friday/plugin/`. Plugins in `friday/plugins/` with `on_load` / `on_unload` hooks.

## Boot / Login Integration
- **systemd service** (`install/friday.service`) — `multi-user.target`, runs as configured user.
- **Login profile** (`install/friday-welcome.sh`) — `/etc/profile.d/` script, first-login consent, auto-starts daemon + tray.
- **Installer** (`install/friday-installer.sh`) — Cross-platform one-liner.

## Data Flow
```
User Input → CLI/GUI
  → Intent Parser (classify)
  → Context Engine (load relevant memory)
  → Agent Router (select agent)
  → Task Delegator (break into subtasks if needed)
  → Agent.handle() (system prompt + tools)
  → ProviderRegistry.route() (LLM call)
  → Memory update (KG entities, conversation, profile)
  → Response rendering (markdown → display)
```
