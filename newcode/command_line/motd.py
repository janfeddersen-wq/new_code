"""
MOTD (Message of the Day) feature for the code agent.
Stores seen versions in XDG_CONFIG_HOME/newcode/motd.txt.
"""

import os

from newcode.config import CONFIG_DIR
from newcode.messaging import emit_info

MOTD_VERSION = "2026-01-02"
MOTD_MESSAGE = """
Reminder that the application supports these model setups:

### Claude Code - Via `/model-setup`
- Opus / Haiku / Sonnet

### ChatGPT - Via `/model-setup`
- gpt-5.2 and gpt-5.2 codex

### Firepass - Via `/model-setup`
- Kimi K2.5 Turbo via Fireworks router.
"""
MOTD_TRACK_FILE = os.path.join(CONFIG_DIR, "motd.txt")


def get_motd_content() -> tuple[str, str]:
    """Get MOTD content, checking plugins first.

    Returns:
        Tuple of (message, version) - either from plugin or built-in.
    """
    # Check if plugins want to override MOTD
    try:
        from newcode.callbacks import on_get_motd

        results = on_get_motd()
        # Use the last non-None result
        for result in reversed(results):
            if result is not None and isinstance(result, tuple) and len(result) == 2:
                return result
    except Exception:
        pass

    # Fall back to built-in MOTD
    return (MOTD_MESSAGE, MOTD_VERSION)


def has_seen_motd(version: str) -> bool:
    if not os.path.exists(MOTD_TRACK_FILE):
        return False
    with open(MOTD_TRACK_FILE, "r") as f:
        seen_versions = {line.strip() for line in f if line.strip()}
    return version in seen_versions


def mark_motd_seen(version: str):
    os.makedirs(os.path.dirname(MOTD_TRACK_FILE), exist_ok=True)

    seen_versions = set()
    if os.path.exists(MOTD_TRACK_FILE):
        with open(MOTD_TRACK_FILE, "r") as f:
            seen_versions = {line.strip() for line in f if line.strip()}

    if version not in seen_versions:
        with open(MOTD_TRACK_FILE, "a") as f:
            f.write(f"{version}\n")


def print_motd(console=None, force: bool = False) -> bool:
    """Print the message of the day to the user.

    Args:
        console: Optional console object (for backward compatibility).
        force: Whether to force printing even if the MOTD has been seen.

    Returns:
        True if the MOTD was printed, False otherwise.
    """
    message, version = get_motd_content()
    if force or not has_seen_motd(version):
        from rich.markdown import Markdown

        markdown_content = Markdown(message)
        emit_info(markdown_content)
        mark_motd_seen(version)
        return True
    return False
