"""CDP-based JavaScript execution and advanced page manipulation tools.

These tools mirror the existing Playwright-based browser_scripts.py API
but use Chrome DevTools Protocol (CDP) instead.
"""

import asyncio
from typing import Any, Dict, Optional

from pydantic_ai import RunContext

from newcode.messaging import emit_error, emit_info, emit_success
from newcode.tools.common import generate_group_id

from .cdp_domains import RuntimeDomain
from .cdp_manager import get_session_cdp_manager


async def execute_javascript(
    script: str,
    timeout: int = 30000,
) -> Dict[str, Any]:
    """Execute JavaScript code in the browser context via CDP."""
    group_id = generate_group_id("browser_execute_js", script[:100])
    emit_info(
        f"BROWSER EXECUTE JS 📜 script='{script[:100]}{'...' if len(script) > 100 else ''}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        # Execute JavaScript via Runtime.evaluate
        result = await runtime.evaluate(
            script, return_by_value=True, await_promise=True, timeout=timeout / 1000
        )

        emit_success("JavaScript executed successfully", message_group=group_id)

        return {"success": True, "script": script, "result": result}

    except Exception as e:
        emit_error(f"JavaScript execution failed: {str(e)}", message_group=group_id)
        return {"success": False, "error": str(e), "script": script}


async def scroll_page(
    direction: str = "down",
    amount: int = 3,
    element_selector: Optional[str] = None,
) -> Dict[str, Any]:
    """Scroll the page or a specific element via CDP."""
    target = element_selector or "page"
    group_id = generate_group_id("browser_scroll", f"{direction}_{amount}_{target}")
    emit_info(
        f"BROWSER SCROLL 📋 direction={direction} amount={amount} target='{target}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        if element_selector:
            # Scroll specific element
            element_selector_escaped = element_selector.replace("'", "\\'")
            js = f"""
                const el = document.querySelector('{element_selector_escaped}');
                if (!el) return {{ error: 'Element not found' }};
                const rect = el.getBoundingClientRect();
                const scrollAmount = rect.height * {amount} / 3;
                
                if ('{direction}' === 'down') el.scrollTop += scrollAmount;
                else if ('{direction}' === 'up') el.scrollTop -= scrollAmount;
                else if ('{direction}' === 'left') el.scrollLeft -= scrollAmount;
                else if ('{direction}' === 'right') el.scrollLeft += scrollAmount;
                
                return {{
                    scrollTop: el.scrollTop,
                    scrollLeft: el.scrollLeft,
                    scrollHeight: el.scrollHeight,
                    scrollWidth: el.scrollWidth
                }};
            """

            result = await runtime.evaluate(
                js, return_by_value=True, await_promise=False
            )

            if result and result.get("error"):
                return {
                    "success": False,
                    "error": result["error"],
                    "direction": direction,
                    "element_selector": element_selector,
                }

            target = f"element '{element_selector}'"
        else:
            # Scroll page
            js = f"""
                const viewportHeight = window.innerHeight;
                const scrollAmount = viewportHeight * {amount} / 3;
                
                if ('{direction}' === 'down') window.scrollBy(0, scrollAmount);
                else if ('{direction}' === 'up') window.scrollBy(0, -scrollAmount);
                else if ('{direction}' === 'left') window.scrollBy(-scrollAmount, 0);
                else if ('{direction}' === 'right') window.scrollBy(scrollAmount, 0);
                
                return {{
                    x: window.pageXOffset,
                    y: window.pageYOffset
                }};
            """

            result = await runtime.evaluate(
                js, return_by_value=True, await_promise=False
            )
            target = "page"

        emit_success(f"Scrolled {target} {direction}", message_group=group_id)

        return {
            "success": True,
            "direction": direction,
            "amount": amount,
            "target": target,
            "scroll_position": result,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "direction": direction,
            "element_selector": element_selector,
        }


async def scroll_to_element(
    selector: str,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Scroll to bring an element into view via CDP."""
    group_id = generate_group_id("browser_scroll_to_element", selector[:100])
    emit_info(
        f"BROWSER SCROLL TO ELEMENT 🎯 selector='{selector}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (!el) return {{ error: 'Element not found' }};
            el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
            return {{ 
                success: true,
                visible: el.offsetParent !== null,
                rect: el.getBoundingClientRect()
            }};
        """

        result = await runtime.evaluate(js, return_by_value=True, await_promise=False)

        if result and result.get("error"):
            return {"success": False, "error": result["error"], "selector": selector}

        is_visible = result.get("visible", False)

        emit_success(f"Scrolled to element: {selector}", message_group=group_id)

        return {"success": True, "selector": selector, "visible": is_visible}

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


async def set_viewport_size(
    width: int,
    height: int,
) -> Dict[str, Any]:
    """Set the viewport size via CDP."""
    group_id = generate_group_id("browser_set_viewport", f"{width}x{height}")
    emit_info(
        f"BROWSER SET VIEWPORT 🖥️ size={width}x{height}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()

        # Use Runtime domain to set viewport via Emulation
        from .cdp_domains import PageDomain

        page = PageDomain(client)
        await page.set_viewport_size(width, height)

        emit_success(
            f"Set viewport size to {width}x{height}",
            message_group=group_id,
        )

        return {"success": True, "width": width, "height": height}

    except Exception as e:
        return {"success": False, "error": str(e), "width": width, "height": height}


async def wait_for_element(
    selector: str,
    state: str = "visible",
    timeout: int = 30000,
) -> Dict[str, Any]:
    """Wait for an element to reach a specific state via CDP."""
    group_id = generate_group_id("browser_wait_for_element", f"{selector[:50]}_{state}")
    emit_info(
        f"BROWSER WAIT FOR ELEMENT ⏱️ selector='{selector}' state={state} timeout={timeout}ms",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        # Poll for element state
        start_time = asyncio.get_event_loop().time()
        poll_interval = 0.1

        selector_escaped = selector.replace("'", "\\'")
        while (asyncio.get_event_loop().time() - start_time) < (timeout / 1000):
            js = f"""
                const el = document.querySelector('{selector_escaped}');
                if (!el) return {{ exists: false }};
                
                const rect = el.getBoundingClientRect();
                const isVisible = el.offsetParent !== null && rect.width > 0 && rect.height > 0;
                
                if ('{state}' === 'visible') return {{ ready: isVisible }};
                else if ('{state}' === 'hidden') return {{ ready: !isVisible }};
                else if ('{state}' === 'attached') return {{ ready: true }};
                else if ('{state}' === 'detached') return {{ ready: false }};
                
                return {{ ready: isVisible }};
            """

            result = await runtime.evaluate(
                js, return_by_value=True, await_promise=False
            )

            if result and result.get("ready"):
                emit_success(
                    f"Element {selector} is now {state}", message_group=group_id
                )
                return {"success": True, "selector": selector, "state": state}

            await asyncio.sleep(poll_interval)

        return {
            "success": False,
            "error": f"Timeout waiting for element {selector} to be {state}",
            "selector": selector,
            "state": state,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector, "state": state}


async def highlight_element(
    selector: str,
    color: str = "red",
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Highlight an element with a colored border via CDP."""
    group_id = generate_group_id(
        "browser_highlight_element", f"{selector[:50]}_{color}"
    )
    emit_info(
        f"BROWSER HIGHLIGHT ELEMENT 🔦 selector='{selector}' color={color}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        # Add highlight style
        selector_escaped = selector.replace("'", "\\'")
        highlight_js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (!el) return {{ error: 'Element not found' }};
            el.style.outline = '3px solid {color}';
            el.style.outlineOffset = '2px';
            el.style.backgroundColor = '{color}33';  // 20% opacity hex
            el.setAttribute('data-highlighted', 'true');
            return {{ success: true }};
        """

        result = await runtime.evaluate(
            highlight_js, return_by_value=True, await_promise=False
        )

        if result and result.get("error"):
            return {"success": False, "error": result["error"], "selector": selector}

        emit_success(f"Highlighted element: {selector}", message_group=group_id)

        return {"success": True, "selector": selector, "color": color}

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


async def clear_highlights() -> Dict[str, Any]:
    """Clear all element highlights via CDP."""
    group_id = generate_group_id("browser_clear_highlights")
    emit_info(
        "BROWSER CLEAR HIGHLIGHTS 🧹",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        # Remove all highlights
        clear_script = """
            const highlighted = document.querySelectorAll('[data-highlighted="true"]');
            highlighted.forEach(el => {
                el.style.outline = '';
                el.style.outlineOffset = '';
                el.style.backgroundColor = '';
                el.removeAttribute('data-highlighted');
            });
            return highlighted.length;
        """

        count = await runtime.evaluate(
            clear_script, return_by_value=True, await_promise=False
        )

        emit_success(f"Cleared {count} highlights", message_group=group_id)

        return {"success": True, "cleared_count": count}

    except Exception as e:
        return {"success": False, "error": str(e)}


# Tool registration functions
def register_execute_javascript(agent):
    """Register the JavaScript execution tool."""

    @agent.tool
    async def browser_execute_js(
        context: RunContext,
        script: str,
        timeout: int = 30000,
    ) -> Dict[str, Any]:
        """
        Execute JavaScript code in the browser context.

        Args:
            script: JavaScript code to execute
            timeout: Timeout in milliseconds

        Returns:
            Dict with execution results
        """
        return await execute_javascript(script, timeout)


def register_scroll_page(agent):
    """Register the scroll page tool."""

    @agent.tool
    async def browser_scroll(
        context: RunContext,
        direction: str = "down",
        amount: int = 3,
        element_selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Scroll the page or a specific element.

        Args:
            direction: Scroll direction (up, down, left, right)
            amount: Scroll amount multiplier (1-10)
            element_selector: Optional selector to scroll specific element

        Returns:
            Dict with scroll results
        """
        return await scroll_page(direction, amount, element_selector)


def register_scroll_to_element(agent):
    """Register the scroll to element tool."""

    @agent.tool
    async def browser_scroll_to_element(
        context: RunContext,
        selector: str,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Scroll to bring an element into view.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds

        Returns:
            Dict with scroll results
        """
        return await scroll_to_element(selector, timeout)


def register_set_viewport_size(agent):
    """Register the viewport size tool."""

    @agent.tool
    async def browser_set_viewport(
        context: RunContext,
        width: int,
        height: int,
    ) -> Dict[str, Any]:
        """
        Set the browser viewport size.

        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels

        Returns:
            Dict with viewport size results
        """
        return await set_viewport_size(width, height)


def register_wait_for_element(agent):
    """Register the wait for element tool."""

    @agent.tool
    async def browser_wait_for_element(
        context: RunContext,
        selector: str,
        state: str = "visible",
        timeout: int = 30000,
    ) -> Dict[str, Any]:
        """
        Wait for an element to reach a specific state.

        Args:
            selector: CSS or XPath selector for the element
            state: State to wait for (visible, hidden, attached, detached)
            timeout: Timeout in milliseconds

        Returns:
            Dict with wait results
        """
        return await wait_for_element(selector, state, timeout)


def register_browser_highlight_element(agent):
    """Register the element highlighting tool."""

    @agent.tool
    async def browser_highlight_element(
        context: RunContext,
        selector: str,
        color: str = "red",
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Highlight an element with a colored border for visual identification.

        Args:
            selector: CSS or XPath selector for the element
            color: Highlight color (red, blue, green, yellow, etc.)
            timeout: Timeout in milliseconds

        Returns:
            Dict with highlight results
        """
        return await highlight_element(selector, color, timeout)


def register_browser_clear_highlights(agent):
    """Register the clear highlights tool."""

    @agent.tool
    async def browser_clear_highlights(context: RunContext) -> Dict[str, Any]:
        """
        Clear all element highlights from the page.

        Returns:
            Dict with clear results
        """
        return await clear_highlights()
