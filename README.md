# NewCode

An AI-powered code generation and modification agent for the terminal.

NewCode is a fork of [code-puppy](https://github.com/mpfaffenberger/newcode) by Michael Pfaffenberger, customized for the fedstew workflow. We wanted a clean, professional CLI agent with opinionated defaults, streamlined prompts, and a focus on practical code generation without the playful branding.

## Table of Contents

- [What changed from code-puppy](#what-changed-from-code-puppy)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Features](#features)
- [Configuration](#configuration)
- [Agents](#agents)
- [Development](#development)
- [Credits](#credits)
- [License](#license)

## What changed from code-puppy

- Removed all dog/puppy-themed branding and emojis in favor of a clean, professional interface
- Renamed the "Pack" multi-agent system to functional names (Orchestrator, Tracker, Executor, Reviewer, etc.)
- Rewrote all agent system prompts for clarity and professionalism
- Increased output validation retries from 3 to 10 for more robust model interactions
- Updated configuration keys and display names throughout
- Published to PyPI as `newcode` instead of `code-puppy`

## Installation

Install with `pip`:

```bash
pip install newcode
```

Or install with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install newcode
```

## Quick Start

Run the agent:

```bash
newcode
```

Or use the short alias:

```bash
nc
```

On first run, NewCode opens a setup wizard to help you configure API keys and preferences.

## Requirements

- Python 3.11 - 3.13
- An API key for at least one supported provider (OpenAI, Anthropic, Cerebras, Google Gemini, etc.)

## Features

### Model and agent capabilities

- Multi-model support: OpenAI, Anthropic Claude, Google Gemini, Cerebras, and more
- Multi-agent workflows with specialized agents (Orchestrator, Tracker, Executor, Reviewer, QA Checker, Workspace Manager, Merger)
- MCP (Model Context Protocol) server support

### Core workflow tools

- File operations: read, write, edit, delete with diff previews and permission prompts
- Shell command execution with safety controls
- Session auto-save and restore

### Automation and extensibility

- Scheduled task execution with a background daemon
- Plugin system with lifecycle callbacks and event-based hooks

### Interface and UX

- Interactive TUI menus for configuration, model selection, and task management
- Browser-based terminal via built-in API server

## Configuration

NewCode stores configuration at:

- `~/.config/newcode/puppy.cfg` (XDG-compliant path)

The first-run setup wizard creates and populates this file automatically. After setup, you can manage configuration from inside the agent REPL:

```bash
/config          # Show current configuration
/model           # Switch models
/agent           # Switch agents
/scheduler       # Manage scheduled tasks
/colors          # Customize terminal colors
```

## Agents

| Agent | Primary responsibility |
|-------|------------------------|
| Code Agent | General-purpose code generation and modification (default) |
| Orchestrator | Coordinates multi-agent workflows |
| Tracker | Performs code search and navigation |
| Executor | Runs shell commands |
| Reviewer | Performs code review and quality checks |
| QA Checker | Handles testing and validation |
| Workspace Manager | Manages file system operations |
| Merger | Integrates outputs from multiple agents |
| Python Reviewer | Provides Python-specific code review |
| QA Expert | Defines testing strategy and quality assurance |
| Security Auditor | Performs security analysis |

## Development

```bash
# Clone the repository
git clone https://github.com/janfeddersen-wq/new_code.git
cd new_code

# Install in editable mode with development dependencies
uv pip install -e ".[dev]"

# Run the test suite
uv run pytest tests/ -v

# Run lint checks
ruff check .

# Verify formatting
ruff format --check .
```

## Credits

This project is a fork of [code-puppy](https://github.com/mpfaffenberger/newcode) by [Michael Pfaffenberger](https://github.com/mpfaffenberger), licensed under the MIT License. We are grateful for the original work and the open-source foundation it provides.

## License

MIT License - see [LICENSE](LICENSE) for details.
