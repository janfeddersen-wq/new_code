# NewCode

An AI-powered code generation and modification agent for the terminal.

NewCode is a fork of [code-puppy](https://github.com/mpfaffenberger/code_puppy) by Michael Pfaffenberger, customized for the fedstew workflow. We wanted a clean, professional CLI agent with opinionated defaults, streamlined prompts, and a focus on practical code generation without the playful branding.

## What changed from code-puppy

- Removed all dog/puppy-themed branding and emojis in favor of a clean, professional interface
- Renamed "Pack" multi-agent system to use functional names (Orchestrator, Tracker, Executor, Reviewer, etc.)
- Rewrote all agent system prompts for clarity and professionalism
- Increased output validation retries from 3 to 10 for more robust model interactions
- Updated configuration keys and display names throughout
- Published to PyPI as `newcode` instead of `code-puppy`

## Installation

```bash
pip install newcode
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install newcode
```

## Quick Start

```bash
# Run the agent
newcode

# Or use the short alias
nc
```

On first run, you'll be guided through a setup wizard to configure your API keys and preferences.

## Requirements

- Python 3.11 - 3.13
- An API key for at least one supported provider (OpenAI, Anthropic, Cerebras, Google Gemini, etc.)

## Features

- Multi-model support: OpenAI, Anthropic Claude, Google Gemini, Cerebras, and more
- Multi-agent workflows with specialized agents (Orchestrator, Tracker, Executor, Reviewer, QA Checker, Workspace Manager, Merger)
- File operations: read, write, edit, delete with diff previews and permission prompts
- Shell command execution with safety controls
- Browser-based terminal via built-in API server
- Scheduled task execution with a background daemon
- Plugin system with lifecycle callbacks and event-based hooks
- Interactive TUI menus for configuration, model selection, and task management
- Session auto-save and restore
- MCP (Model Context Protocol) server support

## Configuration

Configuration is stored in `~/.config/code_puppy/puppy.cfg` (XDG-compliant paths). The setup wizard handles initial configuration. You can also use CLI commands:

```bash
# Inside the agent REPL:
/config          # Show current configuration
/model           # Switch models
/agent           # Switch agents
/scheduler       # Manage scheduled tasks
/colors          # Customize terminal colors
```

## Agents

| Agent | Purpose |
|-------|---------|
| Code Agent | General-purpose code generation and modification (default) |
| Orchestrator | Multi-agent workflow coordination |
| Tracker | Code search and navigation |
| Executor | Shell command execution |
| Reviewer | Code review and quality checks |
| QA Checker | Testing and validation |
| Workspace Manager | File system operations |
| Merger | Result integration |
| Python Reviewer | Python-specific code review |
| QA Expert | Testing strategy and quality assurance |
| Security Auditor | Security analysis |

## Development

```bash
# Clone the repo
git clone https://github.com/janfeddersen-wq/new_code.git
cd new_code

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest tests/ -v

# Lint
ruff check .
ruff format --check .
```

## Credits

This project is a fork of [code-puppy](https://github.com/mpfaffenberger/code_puppy) by [Michael Pfaffenberger](https://github.com/mpfaffenberger), licensed under the MIT License. We are grateful for the original work and the open-source foundation it provides.

## License

MIT License - see [LICENSE](LICENSE) for details.
