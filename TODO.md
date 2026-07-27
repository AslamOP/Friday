# FRIDAY v2.0 Development Roadmap

## Current Version: v2.1 (First Workers) — ✅ COMPLETE

---

## v2.0 — Core Brain ✅

- [x] Core: Orchestrator, ContextEngine, AgentRouter, EventBus, TaskScheduler
- [x] Agents: All 8 (Mentor, Planner, Software Engineer, Research Scientist, Automation Engineer, Knowledge Manager, Academic Tutor, Gaming Assistant)
- [x] Model Router: OmniRouteClient, ModelRegistry, FallbackHandler, CostTracker
- [x] Memory: KnowledgeGraph, ProjectMemory, UserProfile, ConversationStore, VectorStore
- [x] Tools: Terminal (safe), Filesystem, Browser (Playwright), CodeEditor (Cursor), Git
- [x] Interfaces: Rich CLI, JARVIS-style Web Dashboard (FastAPI)
- [x] Infrastructure: setup.sh, start.sh, friday.service, requirements.txt

---

## v2.1 — First Workers ✅

**Goal:** Agents become functional. Real work gets done.

- [x] Terminal confirmation gates (modify commands require token)
- [x] Knowledge Manager: File indexing pipeline (SHA256 dedup, KG + VS storage)
- [x] Software Engineer: Code gen with file extraction, test running
- [x] Mentor: Multi-stage critical analysis (assumptions, risks, flaws, alternatives)
- [x] Planner: Plan storage in ProjectMemory, date detection, plan IDs
- [x] Academic Tutor: PYQ PDF parser (PyMuPDF), topic classification, marks extraction
- [x] Voice Interface: Whisper STT (faster-whisper), Piper TTS

---

## v2.2 — Knowledge & Memory 🟡 Next

**Goal:** FRIDAY remembers and improves.

- [ ] Semantic search (vector embeddings with ChromaDB)
- [ ] Conversation history with context recall
- [ ] Project memory (active projects, file relationships)
- [ ] Knowledge graph learning (auto-extract entities from conversations)
- [ ] PYQ knowledge graph

---

## v2.3 — Research & Automation

**Goal:** FRIDAY interacts with the world.

- [ ] Research Scientist: Full web search, PDF reading
- [ ] Browser Tool: Full Playwright automation
- [ ] Automation Engineer: Cron, systemd, monitoring
- [ ] System Monitor Tool: CPU/GPU/RAM alerts
- [ ] Notification system (KDE desktop)

---

## v2.4 — Desktop Integration

**Goal:** FRIDAY becomes part of the desktop.

- [ ] System tray widget (KDE)
- [ ] Clipboard read/write
- [ ] Application launcher
- [ ] Screen understanding (screenshot analysis)

---

## v2.5 — Specialized Agents

**Goal:** Domain-specific expertise.

- [ ] CAD Engineer Agent
- [ ] Gaming Assistant: Full Steam/Discord/OBS integration
- [ ] Academic Tutor: Full PYQ analysis

---

## v2.6 — Intelligence

**Goal:** FRIDAY reasons and plans deeply.

- [ ] Multi-agent collaboration (delegation via EventBus)
- [ ] Proactive behavior
- [ ] Self-improvement loops

---

## v2.7 — FRIDAY Operating System

**Goal:** Complete personal AI assistant.

- [ ] All agents working in harmony
- [ ] Seamless OmniRoute orchestration
- [ ] Rich knowledge graph and memory
