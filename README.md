# FRIDAY AI OS v3

A JARVIS-class personal AI assistant with composable intelligence primitives — agents, tools, memory, MCP, multi-channel gateway, and local-first engine.

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
├── agents/        # Agent implementations (chat, react, hybrid, native, claude-code)
├── analytics/     # Usage & telemetry analytics
├── bench/         # Inference benchmarks
├── channels/      # Multi-channel gateway (Telegram, iMessage, SMS)
├── cli/           # Click-based CLI entry point & commands
├── connectors/    # Data source connectors (Gmail, Obsidian, Notion, etc.)
├── core/          # Base classes, config, paths, MCP, security, patterns
├── daemon/        # Background server daemon
├── engine/        # Inference engine (local, openai-compatible, hybrid)
├── evals/         # Evaluation framework with dataset harnesses
├── intelligence/  # Reasoning & augmentation primitives
├── learning/      # Trace-based self-improvement, spec search
├── mcp/           # Model Context Protocol tool server
├── memory/        # Persistent memory store
├── mining/        # Pearl mining node
├── operators/     # Scheduled persistent operators
├── prompt/        # Prompt library
├── recipes/       # Composable orchestration recipes
├── sandbox/       # Secure code execution sandbox
├── scheduler/     # Cron-like task scheduler
├── security/      # Audit, scanning, vault
├── server/        # OpenAI-compatible API server
├── sessions/      # Session management
├── skills/        # Reusable skill definitions
├── speech/        # STT/TTS
├── system/        # System-level utilities
├── telemetry/     # Inference telemetry store
├── templates/     # File/recipe templates
├── tools/         # Extensible tool implementations
├── traces/        # Trace capture & replay
└── workflow/      # Workflow orchestration
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
