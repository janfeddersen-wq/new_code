"""Backward-compatible browser manager shim.

This project moved from the old Playwright-based ``browser_manager`` module to
CDP-based browser management in ``cdp_manager``.

A bunch of runtime code — and, let's be honest, some crusty tests too — still
import ``newcode.tools.browser.browser_manager``. Deleting the module outright
means sub-agent startup faceplants with ``ModuleNotFoundError`` before doing
anything useful.

So this shim keeps the old import path alive and forwards the session-management
API to the CDP implementation.
"""

from .cdp_manager import (
    CDPManager,
    _active_managers,
    _cdp_session_var,
    _cleanup_done,
    _sync_cleanup_all,
    cleanup_all_cdp_browsers,
    find_available_port,
    get_cdp_manager,
    get_cdp_session,
    get_session_cdp_manager,
    set_cdp_session,
)

# Old names kept for compatibility with legacy imports.
BrowserManager = CDPManager
CamoufoxManager = CDPManager

_browser_session_var = _cdp_session_var


def set_browser_session(session_id: str | None):
    """Compatibility alias for the legacy browser session setter."""
    return set_cdp_session(session_id)


def get_browser_session() -> str | None:
    """Compatibility alias for the legacy browser session getter."""
    return get_cdp_session()


def get_browser_manager(
    session_id: str | None = None,
    host: str = "localhost",
    port: int | None = None,
    headless: bool | None = None,
    chrome_path: str | None = None,
) -> CDPManager:
    """Compatibility alias for the legacy browser manager factory."""
    return get_cdp_manager(
        session_id=session_id,
        host=host,
        port=port,
        headless=headless,
        chrome_path=chrome_path,
    )


def get_camoufox_manager(*args, **kwargs):
    """Legacy alias kept for ancient callers."""
    return get_browser_manager(*args, **kwargs)


def get_session_browser_manager() -> CDPManager:
    """Compatibility alias for the legacy session-scoped manager getter."""
    return get_session_cdp_manager()


async def cleanup_all_browsers() -> None:
    """Compatibility alias for global browser cleanup."""
    await cleanup_all_cdp_browsers()


def _sync_cleanup_browsers() -> None:
    """Compatibility alias for the old atexit cleanup wrapper."""
    _sync_cleanup_all()


__all__ = [
    "BrowserManager",
    "CamoufoxManager",
    "_active_managers",
    "_browser_session_var",
    "_cleanup_done",
    "_sync_cleanup_browsers",
    "cleanup_all_browsers",
    "find_available_port",
    "get_browser_manager",
    "get_browser_session",
    "get_camoufox_manager",
    "get_session_browser_manager",
    "set_browser_session",
]
