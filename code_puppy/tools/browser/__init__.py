"""Browser tools for terminal automation.

This module provides browser-based terminal automation tools.
"""

from code_puppy.config import get_banner_color

from .browser_manager import (
    cleanup_all_browsers,
    get_browser_session,
    get_session_browser_manager,
    set_browser_session,
)


def format_terminal_banner(text: str) -> str:
    """Format a terminal tool banner with the configured terminal_tool color.

    Returns Rich markup string that can be used with Text.from_markup().

    Args:
        text: The banner text (e.g., "TERMINAL OPEN 🖥️ localhost:8765")

    Returns:
        Rich markup formatted string
    """
    color = get_banner_color("terminal_tool")
    return f"[{color}]───[/{color}] [bold]{text.upper()}[/bold] [{color}]───[/{color}]"


__all__ = [
    "format_terminal_banner",
    "cleanup_all_browsers",
    "get_browser_session",
    "get_session_browser_manager",
    "set_browser_session",
]
