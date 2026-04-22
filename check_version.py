#!/usr/bin/env python3
"""
Diagnostic script for checking newcode version and command registration.

This script helps diagnose the uvx version mismatch issue by:
1. Printing the current version from newcode.__version__
2. Printing the version from pyproject.toml
3. Checking if expected commands are registered in the command registry
4. Printing all registered commands

Run with: python check_version.py
"""

import sys
from pathlib import Path

# Ensure we import from the local package, not installed version
repo_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(repo_root))

# Now import from the local newcode package (after path setup)  # noqa: E402
import importlib.metadata  # noqa: E402

from newcode import __version__  # noqa: E402

# Import command registry and ensure commands are registered
# This import triggers the registration of all commands via decorators
from newcode.command_line import (  # noqa: E402
    command_handler,  # noqa: F401 - triggers registration
)
from newcode.command_line.command_registry import (  # noqa: E402
    get_all_commands,
    get_command,
    get_unique_commands,
)


def get_pyproject_version():
    """Read version directly from pyproject.toml."""
    import tomllib

    pyproject_path = repo_root / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version", "unknown")
    return "pyproject.toml not found"


def get_installed_version():
    """Get version from installed package metadata (what uvx would see)."""
    try:
        return importlib.metadata.version("newcode")
    except Exception:
        return "not installed or metadata unavailable"


def main():
    """Run the diagnostic check."""
    print("=" * 70)
    print("NEWCODE VERSION DIAGNOSTIC")
    print("=" * 70)
    print()

    # Version Information
    print("📦 VERSION INFORMATION")
    print("-" * 40)
    print(f"  newcode.__version__: {__version__}")
    print(f"  pyproject.toml:      {get_pyproject_version()}")
    print(f"  installed metadata:  {get_installed_version()}")
    print()

    # Check for version mismatch
    pyproject_ver = get_pyproject_version()
    installed_ver = get_installed_version()

    if pyproject_ver != installed_ver:
        print("⚠️  VERSION MISMATCH DETECTED!")
        print(f"   pyproject.toml ({pyproject_ver}) != installed ({installed_ver})")
        print("   This usually happens when:")
        print("   • The package was installed with uvx but the repo has newer changes")
        print("   • Running from repo root without 'uv pip install -e .'")
        print()
    else:
        print("✅ Versions are consistent")
        print()

    # Command Registry Check
    print("🎮 COMMAND REGISTRY")
    print("-" * 40)

    # Get all commands (includes aliases)
    all_commands = get_all_commands()
    unique_commands = get_unique_commands()

    print(f"  Total registered entries: {len(all_commands)}")
    print(f"  Unique commands: {len(unique_commands)}")
    print()

    # Check for expected commands
    expected_commands = ["model-setup"]
    print("🔍 EXPECTED COMMANDS CHECK")
    print("-" * 40)

    for cmd in expected_commands:
        cmd_info = get_command(cmd)
        if cmd_info:
            print(f"  ✅ /{cmd} - {cmd_info.description}")
        else:
            print(f"  ❌ /{cmd} - NOT FOUND")
    print()

    # List all unique commands by category
    print("📋 ALL REGISTERED COMMANDS")
    print("-" * 40)

    # Group by category
    from collections import defaultdict

    categories = defaultdict(list)
    for cmd in unique_commands:
        categories[cmd.category].append(cmd)

    for category, cmds in sorted(categories.items()):
        print(f"\n  [{category.upper()}]")
        for cmd in sorted(cmds, key=lambda c: c.name):
            aliases_str = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
            print(f"    /{cmd.name}{aliases_str}")
            print(f"      → {cmd.description}")

    print()
    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
