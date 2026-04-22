"""CDP-based screenshot tool for browser automation.

Captures screenshots and returns them via ToolReturn with BinaryContent
so multimodal models can directly see and analyze - no separate VQA agent needed.

These tools mirror the existing Playwright-based browser_screenshot.py API
but use Chrome DevTools Protocol (CDP) instead.
"""

import time
from datetime import datetime
from pathlib import Path
from tempfile import gettempdir, mkdtemp
from typing import Any, Dict, Optional, Union

from pydantic_ai import BinaryContent, RunContext, ToolReturn

from newcode.image_utils import constrain_image_dimensions
from newcode.messaging import emit_error, emit_info, emit_success
from newcode.tools.common import generate_group_id

from .cdp_domains import PageDomain, RuntimeDomain
from .cdp_manager import get_session_cdp_manager

_TEMP_SCREENSHOT_ROOT = Path(mkdtemp(prefix="newcode_screenshots_", dir=gettempdir()))


def _build_screenshot_path(timestamp: str) -> Path:
    """Return the target path for a screenshot."""
    filename = f"screenshot_{timestamp}.png"
    return _TEMP_SCREENSHOT_ROOT / filename


async def _capture_screenshot(
    full_page: bool = False,
    element_selector: Optional[str] = None,
    save_screenshot: bool = True,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal screenshot capture function via CDP."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        page = PageDomain(client)
        runtime = RuntimeDomain(client)

        # Take screenshot via CDP
        if element_selector:
            # Get element clip rect via JavaScript
            element_selector_escaped = element_selector.replace("'", "\\'")
            js = f"""
                const el = document.querySelector('{element_selector_escaped}');
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return {{
                    x: rect.left,
                    y: rect.top,
                    width: rect.width,
                    height: rect.height,
                    scale: 1
                }};
            """
            clip = await runtime.evaluate(js, return_by_value=True, await_promise=False)

            if not clip:
                return {
                    "success": False,
                    "error": f"Element '{element_selector}' is not visible or not found",
                }

            screenshot_bytes = await page.capture_screenshot(
                clip=clip, from_surface=True
            )
        else:
            screenshot_bytes = await page.capture_screenshot(
                full_page=full_page, from_surface=True
            )

        result: Dict[str, Any] = {
            "success": True,
            "screenshot_bytes": screenshot_bytes,
            "timestamp": timestamp,
        }

        if save_screenshot:
            screenshot_path = _build_screenshot_path(timestamp)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            with open(screenshot_path, "wb") as f:
                f.write(screenshot_bytes)
            result["screenshot_path"] = str(screenshot_path)

            if group_id:
                emit_success(
                    f"Screenshot saved: {screenshot_path}", message_group=group_id
                )

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


async def take_screenshot(
    full_page: bool = False,
    element_selector: Optional[str] = None,
    save_screenshot: bool = True,
) -> Union[ToolReturn, Dict[str, Any]]:
    """Take a screenshot of the browser page via CDP.

    Returns a ToolReturn with BinaryContent so multimodal models can
    directly see and analyze the screenshot.

    Args:
        full_page: Whether to capture full page or just viewport.
        element_selector: Optional selector to screenshot specific element.
        save_screenshot: Whether to save the screenshot to disk.

    Returns:
        ToolReturn containing:
            - return_value: Success message with screenshot path
            - content: List with description and BinaryContent image
            - metadata: Screenshot details (path, target, timestamp)
        Or Dict with error info if failed.
    """
    target = element_selector or ("full_page" if full_page else "viewport")
    group_id = generate_group_id("browser_screenshot", target)
    emit_info(f"BROWSER SCREENSHOT 📷 target={target}", message_group=group_id)

    try:
        browser_manager = get_session_cdp_manager()

        if not browser_manager._initialized:
            error_msg = "Browser not initialized. Use browser_initialize first."
            emit_error(error_msg, message_group=group_id)
            return {"success": False, "error": error_msg}

        result = await _capture_screenshot(
            full_page=full_page,
            element_selector=element_selector,
            save_screenshot=save_screenshot,
            group_id=group_id,
        )

        if not result["success"]:
            emit_error(result.get("error", "Screenshot failed"), message_group=group_id)
            return {"success": False, "error": result.get("error")}

        screenshot_path = result.get("screenshot_path", "(not saved)")

        # Constrain dimensions for API compliance (Claude max 2000px for many-image requests)
        constrained_bytes = constrain_image_dimensions(result["screenshot_bytes"])

        # Return as ToolReturn with BinaryContent so the model can SEE the image!
        return ToolReturn(
            return_value=f"Screenshot captured successfully. Saved to: {screenshot_path}",
            content=[
                f"Here's the browser screenshot ({target}):",
                BinaryContent(
                    data=constrained_bytes,
                    media_type="image/png",
                ),
                "Please analyze what you see and describe any relevant details.",
            ],
            metadata={
                "success": True,
                "screenshot_path": screenshot_path,
                "target": target,
                "full_page": full_page,
                "element_selector": element_selector,
                "timestamp": time.time(),
            },
        )

    except Exception as e:
        error_msg = f"Screenshot failed: {str(e)}"
        emit_error(error_msg, message_group=group_id)
        return {"success": False, "error": error_msg}


def register_take_screenshot_and_analyze(agent):
    """Register the screenshot tool."""

    @agent.tool
    async def browser_screenshot_analyze(
        context: RunContext,
        full_page: bool = False,
        element_selector: Optional[str] = None,
    ) -> Union[ToolReturn, Dict[str, Any]]:
        """
        Take a screenshot of the browser page.

        Returns the screenshot via ToolReturn with BinaryContent that you can
        see directly. Use this to see what's displayed in the browser.

        Args:
            full_page: Capture full page (True) or just viewport (False).
            element_selector: Optional CSS selector to screenshot specific element.

        Returns:
            ToolReturn with the screenshot image you can analyze, or error dict.
        """
        return await take_screenshot(
            full_page=full_page,
            element_selector=element_selector,
        )
