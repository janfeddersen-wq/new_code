"""CDP-based browser initialization and control tools.

These tools mirror the existing Playwright-based browser_control.py API
but use Chrome DevTools Protocol (CDP) instead.
"""

from typing import Any, Dict, Optional

from pydantic_ai import RunContext

from newcode.messaging import emit_error, emit_info, emit_success, emit_warning
from newcode.tools.common import generate_group_id

from .cdp_domains import PageDomain
from .cdp_manager import get_session_cdp_manager


async def initialize_browser(
    headless: bool = False,
    browser_type: str = "chromium",
    homepage: str = "https://www.google.com",
) -> Dict[str, Any]:
    """Initialize the browser with specified settings via CDP."""
    group_id = generate_group_id("browser_initialize", f"{browser_type}_{homepage}")
    emit_info(
        f"BROWSER INITIALIZE 🌐 {browser_type} → {homepage}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()

        # Configure browser settings
        browser_manager.headless = headless

        # Launch browser
        await browser_manager.launch()

        # Get CDP client and navigate to homepage
        client = browser_manager.get_client()
        page = PageDomain(client)

        # Navigate to homepage
        await page.navigate(homepage)

        # Get page info via JavaScript
        runtime = __import__(
            "newcode.tools.browser.cdp_domains", fromlist=["RuntimeDomain"]
        ).RuntimeDomain
        runtime_domain = runtime(client)

        try:
            url = await runtime_domain.evaluate(
                "window.location.href", return_by_value=True
            )
            title = await runtime_domain.evaluate(
                "document.title", return_by_value=True
            )
        except Exception:
            url = homepage
            title = "Unknown"

        return {
            "success": True,
            "browser_type": browser_type,
            "headless": headless,
            "homepage": homepage,
            "current_url": url,
            "current_title": title,
        }

    except Exception as e:
        emit_error(
            f"Browser initialization failed: {str(e)}",
            message_group=group_id,
        )
        return {
            "success": False,
            "error": str(e),
            "browser_type": browser_type,
            "headless": headless,
        }


async def close_browser() -> Dict[str, Any]:
    """Close the browser and clean up resources."""
    group_id = generate_group_id("browser_close")
    emit_info(
        "BROWSER CLOSE 🔒",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        await browser_manager.close()

        emit_warning("Browser closed successfully", message_group=group_id)

        return {"success": True, "message": "Browser closed"}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_browser_status() -> Dict[str, Any]:
    """Get current browser status and information."""
    group_id = generate_group_id("browser_status")
    emit_info(
        "BROWSER STATUS 📊",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()

        if not browser_manager._initialized:
            return {
                "success": True,
                "status": "not_initialized",
                "browser_type": "chromium",
                "headless": browser_manager.headless,
            }

        # Get targets (pages)
        targets = await browser_manager.get_targets()
        page_count = len([t for t in targets if t.get("type") == "page"])

        # Get current page info
        client = browser_manager.get_client()
        runtime = __import__(
            "newcode.tools.browser.cdp_domains", fromlist=["RuntimeDomain"]
        ).RuntimeDomain
        runtime_domain = runtime(client)

        try:
            url = await runtime_domain.evaluate(
                "window.location.href", return_by_value=True
            )
            title = await runtime_domain.evaluate(
                "document.title", return_by_value=True
            )
        except Exception:
            url = None
            title = None

        return {
            "success": True,
            "status": "initialized",
            "browser_type": "chromium",
            "headless": browser_manager.headless,
            "current_url": url,
            "current_title": title,
            "page_count": page_count,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def create_new_page(url: Optional[str] = None) -> Dict[str, Any]:
    """Create a new browser page/tab."""
    group_id = generate_group_id("browser_new_page", url or "blank")
    emit_info(
        f"BROWSER NEW PAGE 📄 {url or 'blank page'}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()

        if not browser_manager._initialized:
            return {
                "success": False,
                "error": "Browser not initialized. Use browser_initialize first.",
            }

        # Create new target via CDP
        target_info = await browser_manager.create_new_page(url)
        target_id = target_info.get("targetId")

        # Get page info
        client = browser_manager.get_client()
        runtime = __import__(
            "newcode.tools.browser.cdp_domains", fromlist=["RuntimeDomain"]
        ).RuntimeDomain
        runtime_domain = runtime(client)

        # Wait a moment for navigation
        import asyncio

        await asyncio.sleep(0.5)

        try:
            final_url = await runtime_domain.evaluate(
                "window.location.href", return_by_value=True
            )
            title = await runtime_domain.evaluate(
                "document.title", return_by_value=True
            )
        except Exception:
            final_url = url or "about:blank"
            title = "New Tab"

        emit_success(f"Created new page: {final_url}", message_group=group_id)

        return {
            "success": True,
            "url": final_url,
            "title": title,
            "requested_url": url,
            "target_id": target_id,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


async def list_pages() -> Dict[str, Any]:
    """List all open browser pages/tabs."""
    group_id = generate_group_id("browser_list_pages")
    emit_info(
        "BROWSER LIST PAGES 📋",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()

        if not browser_manager._initialized:
            return {"success": False, "error": "Browser not initialized"}

        # Get targets via CDP
        targets = await browser_manager.get_targets()

        pages_info = []
        for i, target in enumerate(targets):
            if target.get("type") == "page":
                pages_info.append(
                    {
                        "index": i,
                        "target_id": target.get("targetId"),
                        "url": target.get("url"),
                        "title": target.get("title"),
                        "type": target.get("type"),
                    }
                )

        return {
            "success": True,
            "page_count": len(pages_info),
            "pages": pages_info,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Tool registration functions
def register_initialize_browser(agent):
    """Register the browser initialization tool."""

    @agent.tool
    async def browser_initialize(
        context: RunContext,
        headless: bool = False,
        browser_type: str = "chromium",
        homepage: str = "https://www.google.com",
    ) -> Dict[str, Any]:
        """
        Initialize the browser with specified settings. Must be called before using other browser tools.

        Args:
            headless: Run browser in headless mode (no GUI)
            browser_type: Browser engine (chromium, firefox, webkit)
            homepage: Initial page to load

        Returns:
            Dict with initialization results
        """
        return await initialize_browser(headless, browser_type, homepage)


def register_close_browser(agent):
    """Register the browser close tool."""

    @agent.tool
    async def browser_close(context: RunContext) -> Dict[str, Any]:
        """
        Close the browser and clean up all resources.

        Returns:
            Dict with close results
        """
        return await close_browser()


def register_get_browser_status(agent):
    """Register the browser status tool."""

    @agent.tool
    async def browser_status(context: RunContext) -> Dict[str, Any]:
        """
        Get current browser status and information.

        Returns:
            Dict with browser status and metadata
        """
        return await get_browser_status()


def register_create_new_page(agent):
    """Register the new page creation tool."""

    @agent.tool
    async def browser_new_page(
        context: RunContext,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new browser page/tab.

        Args:
            url: Optional URL to navigate to in the new page

        Returns:
            Dict with new page results
        """
        return await create_new_page(url)


def register_list_pages(agent):
    """Register the list pages tool."""

    @agent.tool
    async def browser_list_pages(context: RunContext) -> Dict[str, Any]:
        """
        List all open browser pages/tabs.

        Returns:
            Dict with information about all open pages
        """
        return await list_pages()
