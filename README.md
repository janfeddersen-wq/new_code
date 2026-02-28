# NewCode

NewCode is an AI-powered terminal coding agent for generating, editing, and reviewing code.

It is maintained as a fork of [code-puppy](https://github.com/mpfaffenberger/code_puppy), with a more professional default UX and workflow-focused agent setup.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Features](#features)
- [Configuration](#configuration)
- [Agents](#agents)
- [Development](#development)
- [Credits](#credits)
- [License](#license)

## Installation

Install from PyPI:

```bash
pip install newcode
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install newcode
```

## Quick Start

Start NewCode:

```bash
newcode
```

Short alias:

```bash
nc
```

On first run, NewCode launches an onboarding wizard to help configure API keys and defaults.

## Requirements

- Python **3.11 to 3.13** (`>=3.11,<3.14`)
- At least one provider/API key for a supported model backend
  - Examples include OpenAI, Anthropic, Gemini, Cerebras, and compatible custom OpenAI-style endpoints

## Features

- **Multi-provider model support**
  - OpenAI, Anthropic, Gemini, Cerebras, and additional configured/custom providers
- **Terminal-first coding workflow**
  - Read/search/edit/delete files, run commands, and review diffs from the CLI
- **Agent system**
  - Default general-purpose code agent plus optional specialist/multi-agent workflows
- **MCP support**
  - Model Context Protocol server management and integration
- **Interactive UX**
  - Built-in command menus for model, agent, and settings management
- **Session and workflow utilities**
  - Session autosave/restore and scheduler capabilities
- **Extensibility**
  - Plugin/callback hooks for custom behavior

## Configuration

NewCode uses a legacy-compatible `puppy.cfg` filename.

By default (no XDG env vars set), config is stored in:

- `~/.newcode/puppy.cfg`

If XDG environment variables are set, config is stored under:

- `$XDG_CONFIG_HOME/newcode/puppy.cfg`

Useful in-app commands:

```bash
/config         # Show current configuration
/model          # Select or switch model
/agent          # Select or switch agent
/scheduler      # Manage scheduled tasks
/colors         # Customize terminal UI colors
/api            # Manage built-in API server (start|stop|status)
```

## Agents

NewCode includes a default coding agent and additional specialized agents.

- **Default:** `code-agent` (general-purpose coding and project modifications)
- **Specialist examples:** language reviewers, QA-focused agents, security auditor, and planning-oriented agents
- **Optional pack agents:** orchestrated multi-agent workflow roles (disabled by default unless enabled in config)

Use `/agent` in the CLI to view and switch available agents in your current setup.

## Development

```bash
# Clone the repository
git clone https://github.com/janfeddersen-wq/new_code.git
cd new_code

# Install editable package with development dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest tests/ -v

# Lint and formatting checks
ruff check .
ruff format --check .
```

## Credits

- NewCode repository: <https://github.com/janfeddersen-wq/new_code>
- Upstream project: [code-puppy](https://github.com/mpfaffenberger/code_puppy)
- Original code-puppy author: [Michael Pfaffenberger](https://github.com/mpfaffenberger)
- NewCode author: Jan Feddersen

## License

MIT — see [LICENSE](LICENSE).
