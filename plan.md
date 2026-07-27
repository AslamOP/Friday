# FRIDAY v2.1 — First Workers

## Objective
Deepen agent capabilities with real tool integration, safety, indexing, and voice I/O.

## Task Breakdown (ordered)

### 1. Terminal Confirmation Gates
**Files:** `friday/tools/terminal.py`
- Add `confirm_dangerous: bool` flag
- Detect commands that modify files (rm, mv, dd, mkfs, format)
- Return a special ToolResult with `requires_confirmation=True` instead of blocking outright
- Add `async def confirm(confirmation_token: str) -> ToolResult` method

### 2. Knowledge Manager — File Indexing Pipeline
**Files:** `friday/agents/knowledge_manager/indexer.py`, `friday/agents/knowledge_manager/__init__.py`
- Recursively scan directories for files
- Extract metadata: name, size, modified, type
- Hash file content (SHA256) for change detection
- Store in KnowledgeGraph and VectorStore
- `async def index_directory(path: str) -> IndexReport`
- `async def index_file(path: str) -> bool`

### 3. Software Engineer — Test Running & Code Gen
**Files:** `friday/agents/software_engineer/agent.py`
- Enhance handle() to use TerminalTool for running tests
- `async def run_tests(path: str) -> TestResult`
- Use FilesystemTool to create files from generated code
- Parse test output to determine pass/fail
- Iterative: generate -> test -> fix -> retest

### 4. Mentor — Critical Analysis Pipeline
**Files:** `friday/agents/mentor/agent.py`
- Multi-stage analysis: identify assumptions -> find risks -> suggest alternatives
- Use OmniRoute with structured prompting
- Return analysis as structured result with sections

### 5. Planner — Calendar Integration
**Files:** `friday/agents/planner/agent.py`
- Parse dates from user input
- Create structured plans with milestones and deadlines
- Store plans in ProjectMemory
- `async def create_plan(goal: str) -> Plan`
- `async def track_progress(plan_id: str) -> dict`

### 6. Academic Tutor — PYQ Parser
**Files:** `friday/agents/academic_tutor/pyq_parser.py`, `friday/agents/academic_tutor/__init__.py`
- Parse PDF files using PyMuPDF (fitz)
- Extract questions, years, subjects, topics
- Store in structured format
- `async def parse_pdf(path: str) -> list[PYQEntry]`
- `PYQEntry` dataclass with question, year, subject, topic, difficulty, marks

### 7. Voice Interface (Whisper STT + Piper TTS)
**Files:** `friday/interfaces/voice/stt.py`, `friday/interfaces/voice/tts.py`, `friday/interfaces/voice/__init__.py`
- STT: faster-whisper for speech-to-text
- TTS: piper-tts for text-to-speech
- Async wrappers
- `async def transcribe(audio_path: str) -> str`
- `async def speak(text: str) -> None`

## Dependencies
- PyMuPDF for PDF parsing: `pip install pymupdf`
- faster-whisper for STT: `pip install faster-whisper`
- piper-tts for TTS: system package (Arch: `sudo pacman -S piper-tts`)
