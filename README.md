# FRIDAY AI OS v3

A JARVIS-class personal AI assistant, rebuilt from the ground up inspired by [OpenJarvis](https://github.com/open-jarvis/OpenJarvis).

## Install

```bash
pipx install --force 'friday[all] @ git+https://github.com/AslamOP/Friday.git'
friday
```

## Usage

```
friday              CLI mode
friday --gui        Desktop GUI mode
```

### Commands

| Command | Description |
|---------|-------------|
| `<ask anything>` | Natural conversation |
| `/research <q>` | Deep research with web search |
| `/code <q>` | Software engineering |
| `/study <q>` | Study mentor |
| `/plan <q>` | Project planning |
| `/agents` | List agents |
| `/status` | System state |
| `/history` | Conversation history |
| `/learn` | Self-reflect & extract lessons |
| `/feedback <1-5>` | Rate last response |
| `/clear` | Clear screen |
| `/help` | Show this help |

### GUI Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+H | Toggle help |
| Ctrl+Q | Quit |
| Escape | Close overlay / minimize |
| Up/Down | Command history |

## Architecture

```
friday/
├── core/          # Agent base, Tool base, Router, Orchestrator, Memory, MCP, Learning, Config
├── agents/        # Chat, Research, Code, Study, Planner, Gaming
├── tools/         # Web search, Shell, File ops, Calculator, Code interpreter, Git, Think
├── interfaces/    # CLI, Desktop (PyQt6), Voice (STT/TTS)
├── presets/       # TOML config presets
├── personas/      # Personality definitions
└── router/        # Provider registry (Zen, Ollama)
```

### Key features

- **MCP-ready**: Model Context Protocol support for tool interoperability
- **Tool system**: Extensible tool base with OpenAI function-calling schema
- **Intent router**: NLP-based agent routing with scoring
- **Memory**: JSONL-persisted conversation history
- **Learning**: Trace-based self-improvement with lesson extraction
- **Config presets**: TOML-based presets for different use cases
- **Personas**: Separate personality definitions
- **Multiple LLM providers**: Zen free tier, Ollama local
