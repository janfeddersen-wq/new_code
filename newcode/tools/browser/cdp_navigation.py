"""CDP-based browser navigation and control tools.

These tools mirror the existing Playwright-based browser_navigation.py API
but use Chrome DevTools Protocol (CDP) instead.
"""

import asyncio
from typing import Any, Dict

from pydantic_ai import RunContext

from newcode.messaging import emit_error, emit_info, emit_success
from newcode.tools.common import generate_group_id

from .cdp_domains import PageDomain, RuntimeDomain
from .cdp_manager import get_session_cdp_manager


async def navigate_to_url(url: str) -> Dict[str, Any]:
    """Navigate to a specific URL via CDP."""
    group_id = generate_group_id("browser_navigate", url)
    emit_info(
        f"BROWSER NAVIGATE 🌐 {url}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        page = PageDomain(client)

        # Navigate to URL
        await page.navigate(url)

        # Wait for navigation to complete
        await asyncio.sleep(0.5)

        # Get final URL and title via JavaScript
        runtime = RuntimeDomain(client)
        final_url = await runtime.evaluate("window.location.href", return_by_value=True)
        title = await runtime.evaluate("document.title", return_by_value=True)

        emit_success(f"Navigated to: {final_url}", message_group=group_id)

        return {"success": True, "url": final_url, "title": title, "requested_url": url}

    except Exception as e:
        emit_error(f"Navigation failed: {str(e)}", message_group=group_id)
        return {"success": False, "error": str(e), "url": url}


async def get_page_info() -> Dict[str, Any]:
    """Get current page information."""
    group_id = generate_group_id("browser_get_page_info")
    emit_info(
        "BROWSER GET PAGE INFO 📌",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        url = await runtime.evaluate("window.location.href", return_by_value=True)
        title = await runtime.evaluate("document.title", return_by_value=True)

        return {"success": True, "url": url, "title": title}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def go_back() -> Dict[str, Any]:
    """Navigate back in browser history."""
    group_id = generate_group_id("browser_go_back")
    emit_info(
        "BROWSER GO BACK ⬅️",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        page = PageDomain(client)

        # Use Page domain's go_back method
        await page.go_back()

        # Get updated page info
        await asyncio.sleep(0.5)
        runtime = RuntimeDomain(client)
        url = await runtime.evaluate("window.location.href", return_by_value=True)
        title = await runtime.evaluate("document.title", return_by_value=True)

        return {"success": True, "url": url, "title": title}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def go_forward() -> Dict[str, Any]:
    """Navigate forward in browser history."""
    group_id = generate_group_id("browser_go_forward")
    emit_info(
        "BROWSER GO FORWARD ➡️",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        page = PageDomain(client)

        # Use Page domain's go_forward method
        await page.go_forward()

        # Get updated page info
        await asyncio.sleep(0.5)
        runtime = RuntimeDomain(client)
        url = await runtime.evaluate("window.location.href", return_by_value=True)
        title = await runtime.evaluate("document.title", return_by_value=True)

        return {"success": True, "url": url, "title": title}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def reload_page(wait_until: str = "domcontentloaded") -> Dict[str, Any]:
    """Reload the current page."""
    group_id = generate_group_id("browser_reload", wait_until)
    emit_info(
        f"BROWSER RELOAD 🔄 wait_until={wait_until}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        page = PageDomain(client)

        # Reload via CDP
        ignore_cache = wait_until == "networkidle"
        await page.reload(ignore_cache=ignore_cache)

        # Wait for reload
        await asyncio.sleep(0.5)

        # Get updated page info
        runtime = RuntimeDomain(client)
        url = await runtime.evaluate("window.location.href", return_by_value=True)
        title = await runtime.evaluate("document.title", return_by_value=True)

        return {"success": True, "url": url, "title": title}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def wait_for_load_state(
    state: str = "domcontentloaded", timeout: int = 30000
) -> Dict[str, Any]:
    """Wait for page to reach a specific load state."""
    group_id = generate_group_id("browser_wait_for_load", f"{state}_{timeout}")
    emit_info(
        f"BROWSER WAIT FOR LOAD ⏱️ state={state} timeout={timeout}ms",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        page = PageDomain(client)

        # Wait for load via Page domain
        result = await page.wait_for_load(state, timeout=timeout / 1000)

        # Get current URL
        runtime = RuntimeDomain(client)
        url = await runtime.evaluate("window.location.href", return_by_value=True)

        return {
            "success": result,
            "state": state,
            "url": url,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "state": state}


def register_navigate_to_url(agent):
    """Register the navigation tool."""

    @agent.tool
    async def browser_navigate(context: RunContext, url: str) -> Dict[str, Any]:
        """
        Navigate the browser to a specific URL.

        Args:
            url: The URL to navigate to (must include protocol like https://)

        Returns:
            Dict with navigation results including final URL and page title
        """
        return await navigate_to_url(url)


def register_get_page_info(agent):
    """Register the page info tool."""

    @agent.tool
    async def browser_get_page_info(context: RunContext) -> Dict[str, Any]:
        """
        Get information about the current page.

        Returns:
            Dict with current URL and page title
        """
        return await get_page_info()


def register_browser_go_back(agent):
    """Register browser go back tool."""

    @agent.tool
    async def browser_go_back(context: RunContext) -> Dict[str, Any]:
        """
        Navigate back in browser history.

        Returns:
            Dict with navigation results
        """
        return await go_back()


def register_browser_go_forward(agent):
    """Register browser go forward tool."""

    @agent.tool
    async def browser_go_forward(context: RunContext) -> Dict[str, Any]:
        """
        Navigate forward in browser history.

        Returns:
            Dict with navigation results
        """
        return await go_forward()


def register_reload_page(agent):
    """Register the page reload tool."""

    @agent.tool
    async def browser_reload(
        context: RunContext, wait_until: str = "domcontentloaded"
    ) -> Dict[str, Any]:
        """
        Reload the current page.

        Args:
            wait_until: Load state to wait for (networkidle, domcontentloaded, load)

        Returns:
            Dict with reload results
        """
        return await reload_page(wait_until)


def register_wait_for_load_state(agent):
    """Register the wait for load state tool."""

    @agent.tool
    async def browser_wait_for_load(
        context: RunContext, state: str = "domcontentloaded", timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Wait for the page to reach a specific load state.

        Args:
            state: Load state to wait for (networkidle, domcontentloaded, load)
            timeout: Timeout in milliseconds

        Returns:
            Dict with wait results
        """
        return await wait_for_load_state(state, timeout)
