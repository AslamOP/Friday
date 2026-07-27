# FRIDAY Development Roadmap

## v2.7 — Provider System & OOTB Ready ✅

- [x] Dynamic ProviderRegistry (add/remove/key/refresh via REPL)
- [x] 7 default providers: Zen, OpenRouter, OpenAI, Anthropic, Google, GitHub Copilot, Ollama
- [x] Works OOTB — Zen free tier, zero config needed
- [x] Generic OpenAI-compatible client handles all providers
- [x] Auto-fetches models on key set
- [x] Auto-detect online/offline status
- [x] No provider-specific files — pure generic router

## v2.6 — Plugin System & Boot Flow ✅

- [x] Plugin system with auto-discover, load/unload
- [x] systemd service + /etc/profile.d welcome
- [x] pip-installable pyproject.toml
- [x] BrowserTool (Playwright) + GitTool
- [x] GitHubInstaller — clone & setup any repo
- [x] 46 unit tests

## v2.5 — Audio & Streaming ✅

- [x] STT (mic → Google/Sphinx) + TTS (edge-tts/pyttsx3)
- [x] Streaming markdown via Rich Live
- [x] Voice mode toggle, /speak command
- [x] Multi-line input detection
- [x] Memory/entity post-processing (no duplicate LLM calls)

## v2.1 — First Workers ✅

- [x] All 8 agents functional with prompts
- [x] Knowledge Manager: file indexing pipeline
- [x] Software Engineer: code gen, test running
- [x] Mentor: multi-stage critical analysis
- [x] Planner: plan storage in ProjectMemory
- [x] Academic Tutor: PYQ PDF parser
- [x] TaskDelegator: LLM decomposition + parallel dispatch

## v2.0 — Core Brain ✅

- [x] Orchestrator, ContextEngine, AgentRouter, IntentParser
- [x] Memory: KnowledgeGraph, VectorStore, ConversationStore, UserProfile
- [x] Tools: ShellSandbox, FileOps, WebSearchTool
- [x] 3-tier provider chain (Zen → OpenRouter → Ollama)
- [x] Persistence with auto-save
- [x] CLI REPL with help, status, history

## Up Next

- [ ] Web dashboard (optional — CLI is primary)
- [ ] System monitor tool (CPU, RAM, disk, GPU)
- [ ] FRIDAY-to-FRIDAY agent communication protocol
