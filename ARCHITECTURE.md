# FRIDAY v2.0 Architecture

## Overview

FRIDAY v2.0 is built as a layered, modular AI operating system. Each layer has a single responsibility and communicates through well-defined interfaces.

The fundamental shift from v1.0: **Agent-first, not chat-first.** FRIDAY is not a chatbot with skills. It is a collection of autonomous agents orchestrated by a central brain.

```
+-------------------------------------------------------------+
|                     INTERFACE LAYER                           |
|  +---------+ +---------+ +-------------+ +----------------+ |
|  |   CLI   | |  Voice  | | System Tray | |  Cursor Plugin | |
|  |(Primary)| |         | |  (KDE)      | |                | |
|  +---------+ +---------+ +-------------+ +----------------+ |
|  +--------------------------------------------------------+ |
|  |         Web Dashboard (JARVIS-style, optional)          | |
|  +--------------------------------------------------------+ |
+--------------------------+----------------------------------+
                           |
+--------------------------v----------------------------------+
|                    ORCHESTRATOR (Core)                       |
|  +-------------+  +-------------+  +---------------------+  |
|  |   Intent    |  |   Context   |  |    Agent Router     |  |
|  |  Parser     |  |  Engine     |  |                     |  |
|  +-------------+  +-------------+  +---------------------+  |
|                                                             |
|  "Build a billing system" -> Parse -> Load Context -> Route   |
+--------------------------+----------------------------------+
                           |
+--------------------------v----------------------------------+
|                      AGENT POOL                            |
|  +----------+ +----------+ +----------+ +----------+        |
|  |  Mentor  | | Planner  | | Software | | Research |        |
|  |          | |          | | Engineer | | Scientist|        |
|  +----------+ +----------+ +----------+ +----------+        |
|  +----------+ +----------+ +----------+ +----------+        |
|  |   CAD    | |Automation| | Knowledge| |  Gaming  |        |
|  | Engineer | | Engineer | | Manager  | | Assistant|        |
|  +----------+ +----------+ +----------+ +----------+        |
|  +----------+                                               |
|  | Academic |                                               |
|  |  Tutor   |                                               |
|  +----------+                                               |
|                                                             |
|  Each agent: memory slice + tools + model preference        |
|  Agents can delegate to other agents via EventBus           |
+--------------------------+----------------------------------+
                           |
+--------------------------v----------------------------------+
|                    TOOL & EXECUTION LAYER                   |
|  +---------+ +---------+ +---------+ +---------+ +--------+ |
|  |Terminal | |Browser | | Filesys | |  Code   | | Docker | |
|  |         | |(Playwrt)| |         | | Editor  | |        | |
|  +---------+ +---------+ +---------+ +---------+ +--------+ |
|  +---------+ +---------+ +---------+ +---------+ +--------+ |
|  |  Git    | | Cursor  | |  Steam  | | Discord | |  OBS   | |
|  |         | |  IDE    | |         | |         | |        | |
|  +---------+ +---------+ +---------+ +---------+ +--------+ |
|  +---------+ +---------+ +---------+                       |
|  | System  | |   PDF   | |  OCR    |                       |
|  | Monitor | | Reader  | |         |                       |
|  +---------+ +---------+ +---------+                       |
|                                                             |
|  Tools execute on YOUR machine. Real files. Real terminal.  |
+--------------------------+----------------------------------+
                           |
+--------------------------v----------------------------------+
|                    MODEL ROUTER (OmniRoute)                |
|                                                             |
|  Coding      -> Local Qwen Coder / DeepSeek via OmniRoute   |
|  Research    -> Claude / Gemini via OmniRoute               |
|  Vision      -> GPT-4o / Gemini Flash via OmniRoute         |
|  Fast chat   -> Local Ollama                                |
|  Fallback    -> Auto-switch on failure                      |
|                                                             |
|  Criteria: quality, speed, cost, privacy, availability     |
+--------------------------+----------------------------------+
                           |
+--------------------------v----------------------------------+
|                    MEMORY & KNOWLEDGE                       |
|  +-------------+  +-------------+  +---------------------+  |
|  |  Knowledge  |  |  Project    |  |    User Profile     |  |
|  |   Graph     |  |   Memory    |  |  (style, goals,     |  |
|  | (entities,  |  | (active     |  |   preferences)      |  |
|  | relations)  |  |  contexts)  |  |                     |  |
|  +-------------+  +-------------+  +---------------------+  |
|  +-------------+  +-------------+  +---------------------+  |
|  | Conversation|  |   Skills    |  |   Long-term         |  |
|  |   History   |  |   Memory    |  |    Goals            |  |
|  +-------------+  +-------------+  +---------------------+  |
|  +-------------+  +-------------+                              |
|  |    PYQ      |  |   Academic  |                              |
|  |  Database   |  |   Profile   |                              |
|  +-------------+  +-------------+                              |
|                                                             |
|  Not just storage. FRIDAY learns from this.                  |
+-------------------------------------------------------------+
```

---

## Layer Responsibilities

### Interface Layer
- **Single responsibility:** Render the interface. No business logic.
- **Design principles:** JARVIS-style, blue holographic, calm, minimal, intentional.
- **Primary interfaces:** CLI (always), Voice, System Tray, Cursor Plugin
- **Optional:** Web dashboard (JARVIS blue UI with holographic core)
- **No provider logic here.** No agent logic in components.

### Orchestrator (Core)
- **Single responsibility:** Decide HOW to fulfill a user request.
- **Intent Parser:** Classifies user input into intent categories (code, research, plan, study, challenge, etc.)
- **Context Engine:** Loads relevant memory (projects, preferences, past conversations) before routing
- **Agent Router:** Selects the best agent(s) for the task. Can spawn multiple agents for complex tasks.
- **EventBus:** Enables inter-agent communication. Agents can publish events and subscribe to others.
- **Does not:** Execute tools directly. Delegates to agents.

### Agent Pool
- **Single responsibility:** Perform specialized work.
- **Each agent is autonomous:** Has its own memory slice, tool set, model preference, and can delegate.
- **Agents can collaborate:** Software Engineer can ask Research Scientist for information. Planner can ask Mentor to validate a plan.
- **Current agents (v2.0 target):** Mentor, Planner, Software Engineer, Research Scientist, Automation Engineer, Knowledge Manager, Academic Tutor, Gaming Assistant
- **Future agents:** CAD Engineer, and more as needed.

#### Agent Interface
```python
class BaseAgent:
    name: str
    memory_slice: MemorySlice      # What this agent remembers
    tools: List[BaseTool]           # Tools this agent can use
    model_preference: ModelPreference  # Preferred model via OmniRoute

    async def handle(self, task: Task, context: Context) -> Result:
        # Execute the task. Can delegate to other agents via EventBus.
        pass

    async def can_handle(self, intent: Intent) -> float:
        # Return confidence score (0-1) for handling this intent.
        pass
```

### Tool & Execution Layer
- **Single responsibility:** Execute actions safely and reliably.
- **Tools:**
  - Terminal (safe shell with blocklist + timeout)
  - Browser (Playwright automation)
  - Filesystem (read/write/organize)
  - Code Editor (Cursor IDE integration)
  - Git (version control)
  - Docker (container management)
  - System Monitor (CPU/GPU/RAM)
  - Steam / Discord / OBS (gaming integrations)
  - PDF Reader + OCR (document processing)
- **Safety:** Blocklist, timeouts, confirmation gates for destructive operations.
- **Real execution:** No simulation. Real files, real terminal, real browser.

### Model Router (OmniRoute)
- **Single responsibility:** Choose the right model for the task.
- **Auto-selection logic:**
  - Coding -> Local Qwen Coder (Ollama) or DeepSeek via OmniRoute
  - Research -> Claude / Gemini via OmniRoute
  - Vision -> GPT-4o / Gemini Flash via OmniRoute
  - Fast chat -> Local Ollama
  - Offline -> Ollama only
- **Manual override:** Exists only in Advanced Settings for debugging.
- **Handles:** Fallback, load balancing, provider health checks, cost tracking.

### Memory & Knowledge
- **Single responsibility:** Remember, retrieve, and learn.
- **Knowledge Graph:** Entities and relations extracted from conversations, code, documents. Improves over time.
- **Project Memory:** Active projects, file contexts, current state.
- **User Profile:** Preferences, coding style, writing style, goals, academic subjects, weak topics.
- **Conversation History:** Not just storage -- intent, decisions, outcomes tracked.
- **PYQ Database:** Parsed previous year questions with topic tagging, difficulty, frequency analysis.
- **Academic Profile:** Subjects, syllabus, study schedule, weak areas.
- **Vector Store:** Embeddings for semantic search (ChromaDB).

---

## Data Flow

### Simple Command
```
User Input: "What do I know about neural networks?"
  -> Interface Layer -> Orchestrator
      -> Intent Parser: "knowledge_query"
      -> Context Engine: Load user's research interests, past papers
      -> Agent Router: Knowledge Manager (confidence: 0.95)
  -> Knowledge Manager Agent
      -> Query knowledge graph for "neural networks"
      -> Search vector store for related documents
      -> Synthesize response
  -> Model Router: Fast local model for synthesis
  -> Response -> Orchestrator -> Interface Layer -> User
```

### Complex Task (Coding)
```
User Input: "Build me a REST API for my shop"
  -> Interface Layer -> Orchestrator
      -> Intent Parser: "code_generation" + "project_creation"
      -> Context Engine: Load user's coding style, preferred stack, past projects
      -> Agent Router: Software Engineer (primary) + Planner (timeline)
  -> Software Engineer Agent
      -> Decompose: "Create project structure", "Write FastAPI main.py", "Write models", "Write tests"
      -> Filesystem Tool: Create directories
      -> Code Editor Tool: Generate files via Cursor
      -> Terminal Tool: Run tests
      -> If tests fail -> Debug -> Retry
  -> Planner Agent (parallel)
      -> Create timeline with milestones
      -> Set deadline reminders
  -> Knowledge Manager Agent (background)
      -> Index new project files
      -> Update project memory
  -> Response (code + timeline + project indexed) -> Interface Layer -> User
```

### Academic Task (PYQ)
```
User Input: "Generate 5 OS questions from previous year papers"
  -> Interface Layer -> Orchestrator
      -> Intent Parser: "academic_practice" + "pyq_generation"
      -> Context Engine: Load user's OS syllabus, weak topics, past PYQ attempts
      -> Agent Router: Academic Tutor (confidence: 0.98)
  -> Academic Tutor Agent
      -> Query PYQ database for Operating Systems
      -> Analyze patterns: "30% deadlock, 25% scheduling, 20% memory..."
      -> Generate 5 questions matching distribution
      -> Tag with difficulty, topic, expected marks
  -> Knowledge Manager (background)
      -> Log: "User practiced OS, weak on deadlock detection"
      -> Update academic profile
  -> Response (5 questions + analysis + weak area alert) -> Interface Layer -> User
```

### Challenge Mode
```
User Input: "I want to start a SaaS"
  -> Interface Layer -> Orchestrator
      -> Intent Parser: "idea_presentation"
      -> Context Engine: Load user's past projects, skills, resources
      -> Agent Router: Mentor (primary) + Planner (if approved)
  -> Mentor Agent
      -> Challenge assumptions: "What's your moat? Who are competitors?"
      -> Point out risks: "You have no marketing experience."
      -> Suggest improvements: "Start with an MVP, validate first."
  -> If user accepts challenges -> Planner Agent creates timeline
  -> If user disagrees -> Mentor provides counter-arguments
  -> Response (critical analysis + next steps) -> Interface Layer -> User
```

---

## Design Principles

1. **Agent-first, not chat-first.** Every feature must fit the agent architecture.
2. **Single Responsibility:** Every module does one thing and does it well.
3. **Dependency Inversion:** Higher layers depend on abstractions, not implementations.
4. **Open/Closed:** Open for extension (new agents, tools, interfaces), closed for modification.
5. **No Shortcuts:** No provider logic in UI. No business logic in components. No duplicated code.
6. **Headless Core:** The brain runs as a service. UI is optional.
7. **Proactive by Default:** FRIDAY should alert, suggest, act without being asked.
8. **Mentor Challenges:** FRIDAY should disagree when the user is wrong.
9. **Think Long-Term:** Scalable architecture over temporary fixes.
10. **Everything Modular:** Agents, tools, interfaces, providers are all swappable.

---

## File Organization

```
friday/
+-- core/                          # The brain. No UI here.
|   +-- __init__.py
|   +-- orchestrator.py            # Intent parsing, context loading, agent routing
|   +-- intent_parser.py           # Classify user input into intents
|   +-- context_engine.py          # Load relevant memory before agent acts
|   +-- agent_router.py            # Route tasks to agents
|   +-- event_bus.py               # Inter-agent communication
|   +-- task_scheduler.py          # Background task scheduling
|   +-- config.py                  # Pydantic settings, env vars
|
+-- agents/                        # Each agent is a package
|   +-- __init__.py
|   +-- base.py                    # BaseAgent class
|   +-- mentor/
|   |   +-- __init__.py
|   |   +-- agent.py               # MentorAgent implementation
|   |   +-- prompts.py             # System prompts
|   |   +-- memory_schema.py       # What this agent remembers
|   +-- planner/
|   +-- software_engineer/
|   +-- research_scientist/
|   +-- automation_engineer/
|   +-- knowledge_manager/
|   +-- academic_tutor/
|   |   +-- __init__.py
|   |   +-- agent.py
|   |   +-- prompts.py
|   |   +-- pyq_analyzer.py        # PYQ pattern analysis
|   |   +-- memory_schema.py
|   +-- gaming_assistant/
|
+-- tools/                         # Execution layer
|   +-- __init__.py
|   +-- base.py                    # BaseTool class
|   +-- terminal.py                # Safe shell execution
|   +-- browser.py                 # Playwright automation
|   +-- filesystem.py              # File operations
|   +-- code_editor.py             # Cursor IDE integration
|   +-- git.py                     # Version control
|   +-- docker.py                  # Container management
|   +-- system_monitor.py          # CPU/GPU/RAM monitoring
|   +-- steam.py                   # Steam API
|   +-- discord.py                 # Discord bot integration
|   +-- obs.py                     # OBS control
|   +-- pdf_reader.py              # PDF processing
|   +-- ocr.py                     # Tesseract OCR
|
+-- memory/                        # Knowledge and persistence
|   +-- __init__.py
|   +-- knowledge_graph.py         # Entity-relation graph (NetworkX)
|   +-- project_memory.py          # Active project contexts
|   +-- user_profile.py            # Preferences, style, goals
|   +-- conversation_store.py      # Chat history (SQLite)
|   +-- vector_store.py            # Embeddings (ChromaDB)
|   +-- pyq_database.py            # Parsed PYQ papers
|   +-- academic_profile.py        # Subjects, syllabus, weak areas
|
+-- router/                        # OmniRoute integration
|   +-- __init__.py
|   +-- omniroute.py               # OmniRoute client
|   +-- model_registry.py          # Available models per task type
|   +-- fallback.py                # Auto-failure recovery
|   +-- cost_tracker.py            # Usage tracking
|
+-- interfaces/                    # Optional UIs
|   +-- cli/                       # Primary interface: terminal
|   |   +-- __init__.py
|   |   +-- main.py
|   +-- voice/                     # Speech-to-text, TTS
|   |   +-- __init__.py
|   |   +-- stt.py                 # Whisper integration
|   |   +-- tts.py                 # Piper TTS integration
|   +-- system_tray/               # KDE system tray widget
|   +-- cursor_plugin/             # Cursor IDE extension
|   +-- web/                       # JARVIS-style blue dashboard
|       +-- __init__.py
|       +-- static/
|       |   +-- css/
|       |   +-- js/
|       |   +-- assets/
|       +-- templates/
|       |   +-- index.html         # JARVIS blue UI
|       +-- app.py                 # FastAPI web server
|
+-- data/                          # Persistent storage
|   +-- knowledge_graph/
|   +-- vector_db/
|   +-- projects/
|   +-- pyq/                       # Previous year question papers
|   |   +-- os/
|   |   +-- dbms/
|   |   +-- networks/
|   |   +-- ...
|   +-- logs/
|
+-- tests/
+-- main.py                        # Entry point: starts orchestrator + agents + interfaces
+-- requirements.txt
+-- setup.sh
+-- start.sh
+-- friday.service                 # systemd user service
+-- .env                           # Environment variables (keep this!)
```

---

## Agent Collaboration Protocol

Agents communicate via the EventBus:

```python
# Software Engineer needs research
await event_bus.publish("research_needed", {
    "topic": "FastAPI best practices",
    "requester": "software_engineer",
    "callback": "research_complete"
})

# Research Scientist picks it up
@event_bus.subscribe("research_needed")
async def handle_research(event):
    result = await research(event["topic"])
    await event_bus.publish(event["callback"], result)

# Software Engineer receives result
@event_bus.subscribe("research_complete")
async def handle_result(result):
    # Use research in code generation
    pass
```

This enables multi-agent workflows without tight coupling.

---

## Memory Schema

### User Profile
```json
{
  "user_id": "default",
  "coding_style": {
    "language_preference": "python",
    "framework_preference": "fastapi",
    "indent_style": "spaces",
    "line_length": 88
  },
  "writing_style": {
    "tone": "professional",
    "citation_format": "ieee"
  },
  "academic_profile": {
    "subjects": ["Operating Systems", "DBMS", "Computer Networks"],
    "weak_topics": ["Deadlock Detection", "Normalization"],
    "strong_topics": ["Process Scheduling", "SQL"],
    "exam_dates": [{"subject": "OS", "date": "2026-08-15"}]
  },
  "goals": ["Build FRIDAY", "Pass semester with 8.5+ CGPA"],
  "preferences": {
    "challenge_mode": true,
    "proactive_alerts": true
  }
}
```

### PYQ Entry
```json
{
  "question_id": "os_2023_1",
  "subject": "Operating Systems",
  "year": 2023,
  "semester": "even",
  "topic": "Deadlock",
  "subtopic": "Banker's Algorithm",
  "difficulty": "medium",
  "marks": 10,
  "question_text": "Explain Banker's Algorithm...",
  "solution": "...",
  "frequency": 3,
  "related_topics": ["Resource Allocation", "Safety Algorithm"]
}
```

---

## Interface Specifications

### CLI (Primary)
```
$ friday
FRIDAY > Build a REST API for my shop
[Software Engineer] Analyzing requirements...
[Software Engineer] Created project structure
[Software Engineer] Generated FastAPI main.py
[Planner] Timeline: 3 milestones, due 2026-08-01
FRIDAY >
```

### Voice
- Wake word: "Hey Friday" or "Friday"
- STT: faster-whisper (local)
- TTS: piper-tts (local)
- Commands processed same as CLI input

### System Tray (KDE)
- Icon: Blue holographic "F"
- Quick commands: "New Task", "Status", "Settings"
- Notifications: Deadline alerts, agent completions

### Web Dashboard (JARVIS Blue)
- Holographic core (animated rings, scanning arc)
- System stats (CPU, RAM, GPU, network)
- Agent activity panel (online/idle/busy)
- Command interface (type or speak)
- Activity log (timestamped agent actions)

---

## Key Decisions

1. **Why agents over skills?** Agents are autonomous. They have memory, goals, and can act without user input. Skills are passive -- they wait to be called.

2. **Why OmniRoute over direct provider APIs?** Provider independence. If OpenRouter changes pricing, we switch providers without touching agent code.

3. **Why headless core?** FRIDAY should run as a system service. You can interact via CLI, voice, or web -- but the brain never stops.

4. **Why knowledge graph over simple database?** Relations matter. "User likes FastAPI" + "User is building an API" -> "Suggest FastAPI for this project."

5. **Why Mentor challenges?** Most AI assistants agree by default. FRIDAY should make you think harder, not easier.
