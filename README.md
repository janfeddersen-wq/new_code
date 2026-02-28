# NewCode

NewCode is an open-source, terminal-first AI coding agent for generating, editing, and reviewing code.

This project is maintained as a fork of [code-puppy](https://github.com/mpfaffenberger/code_puppy), with a more professional default UX and workflow-focused agent setup.

## Overview

NewCode helps you work on software projects from the command line with AI-assisted workflows: inspect files, make edits, run tools, and iterate quickly.

## Features

- Multi-provider model support (including OpenAI, Anthropic, Gemini, Cerebras, and compatible OpenAI-style endpoints)
- Terminal-first coding workflow (read/search/edit/delete files and run commands)
- Built-in agent system with a default coding agent and optional specialist workflows
- MCP (Model Context Protocol) integration and server management
- Interactive command-driven UX for model, agent, and settings management
- Session autosave/restore and scheduler utilities
- Plugin/callback extensibility hooks

## Installation

### Requirements

- Python `>=3.11,<3.14`
- At least one provider/API key for a supported model backend

### Install from PyPI

```bash
pip install newcode
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install newcode
```

## Usage

Start NewCode:

```bash
newcode
```

Or use the short alias:

```bash
nc
```

On first run, NewCode starts onboarding to help configure API keys and defaults.

Useful in-app commands:

```bash
/config         # Show current configuration
/model          # Select or switch model
/agent          # Select or switch agent
/scheduler      # Manage scheduled tasks
/colors         # Customize terminal UI colors
/api            # Manage built-in API server (start|stop|status)
```

### Configuration location

NewCode uses a legacy-compatible config filename: `puppy.cfg`.

- Default path: `~/.newcode/puppy.cfg`
- With XDG variables: `$XDG_CONFIG_HOME/newcode/puppy.cfg`

## Development

```bash
git clone https://github.com/janfeddersen-wq/new_code.git
cd new_code
uv pip install -e ".[dev]"
```

## Testing

Run the test suite:

```bash
uv run pytest tests/ -v
```

Run linting and formatting checks:

```bash
ruff check .
ruff format --check .
```

## Contributing

Contributions are welcome.

- Open an issue to discuss bugs, ideas, or improvements
- Submit a pull request with clear scope and rationale
- Keep changes focused and include tests when applicable

## License

MIT — see [LICENSE](LICENSE).
