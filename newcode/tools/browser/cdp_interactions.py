"""CDP-based browser element interaction tools for clicking, typing, and form manipulation.

These tools mirror the existing Playwright-based browser_interactions.py API
but use Chrome DevTools Protocol (CDP) instead.
"""

import asyncio
from typing import Any, Dict, List, Optional

from pydantic_ai import RunContext

from newcode.messaging import emit_error, emit_info, emit_success
from newcode.tools.common import generate_group_id

from .cdp_domains import InputDomain, RuntimeDomain
from .cdp_manager import get_session_cdp_manager


async def click_element(
    selector: str,
    timeout: int = 10000,
    force: bool = False,
    button: str = "left",
    modifiers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Click on an element via CDP."""
    group_id = generate_group_id("browser_click", selector[:100])
    emit_info(
        f"BROWSER CLICK 🖱️ selector='{selector}' button={button}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)
        input_domain = InputDomain(client)

        # Get element position
        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            return {{
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
                visible: rect.width > 0 && rect.height > 0 && el.offsetParent !== null
            }};
        """

        pos = await runtime.evaluate(js, return_by_value=True, await_promise=False)

        if not pos:
            return {
                "success": False,
                "error": f"Element not found: {selector}",
                "selector": selector,
            }

        if not pos.get("visible") and not force:
            return {
                "success": False,
                "error": f"Element not visible: {selector}",
                "selector": selector,
            }

        # Calculate modifiers bitmask
        modifier_mask = 0
        if modifiers:
            if "Alt" in modifiers:
                modifier_mask |= 1
            if "Control" in modifiers:
                modifier_mask |= 2
            if "Meta" in modifiers:
                modifier_mask |= 4
            if "Shift" in modifiers:
                modifier_mask |= 8

        # Click via Input domain
        x, y = pos["x"], pos["y"]
        await input_domain.click(x, y, button=button)

        emit_success(f"Clicked element: {selector}", message_group=group_id)

        return {"success": True, "selector": selector, "action": f"{button}_click"}

    except Exception as e:
        emit_error(f"Click failed: {str(e)}", message_group=group_id)
        return {"success": False, "error": str(e), "selector": selector}


async def double_click_element(
    selector: str,
    timeout: int = 10000,
    force: bool = False,
) -> Dict[str, Any]:
    """Double-click on an element via CDP."""
    group_id = generate_group_id("browser_double_click", selector[:100])
    emit_info(
        f"BROWSER DOUBLE CLICK 🖱️🖱️ selector='{selector}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)
        input_domain = InputDomain(client)

        # Get element position
        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            return {{
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
                visible: rect.width > 0 && rect.height > 0 && el.offsetParent !== null
            }};
        """

        pos = await runtime.evaluate(js, return_by_value=True, await_promise=False)

        if not pos:
            return {
                "success": False,
                "error": f"Element not found: {selector}",
                "selector": selector,
            }

        if not pos.get("visible") and not force:
            return {
                "success": False,
                "error": f"Element not visible: {selector}",
                "selector": selector,
            }

        x, y = pos["x"], pos["y"]

        # Double click: mousePressed, mouseReleased twice with click_count
        await input_domain.dispatch_mouse_event(
            "mousePressed", x, y, "left", click_count=1
        )
        await input_domain.dispatch_mouse_event(
            "mouseReleased", x, y, "left", click_count=1
        )
        await asyncio.sleep(0.05)
        await input_domain.dispatch_mouse_event(
            "mousePressed", x, y, "left", click_count=2
        )
        await input_domain.dispatch_mouse_event(
            "mouseReleased", x, y, "left", click_count=2
        )

        emit_success(f"Double-clicked element: {selector}", message_group=group_id)

        return {"success": True, "selector": selector, "action": "double_click"}

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


async def hover_element(
    selector: str,
    timeout: int = 10000,
    force: bool = False,
) -> Dict[str, Any]:
    """Hover over an element via CDP."""
    group_id = generate_group_id("browser_hover", selector[:100])
    emit_info(
        f"BROWSER HOVER 👆 selector='{selector}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)
        input_domain = InputDomain(client)

        # Get element position
        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            return {{
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
                visible: rect.width > 0 && rect.height > 0 && el.offsetParent !== null
            }};
        """

        pos = await runtime.evaluate(js, return_by_value=True, await_promise=False)

        if not pos:
            return {
                "success": False,
                "error": f"Element not found: {selector}",
                "selector": selector,
            }

        if not pos.get("visible") and not force:
            return {
                "success": False,
                "error": f"Element not visible: {selector}",
                "selector": selector,
            }

        # Hover via mouse move
        await input_domain.move_mouse(pos["x"], pos["y"])

        emit_success(f"Hovered over element: {selector}", message_group=group_id)

        return {"success": True, "selector": selector, "action": "hover"}

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


async def set_element_text(
    selector: str,
    text: str,
    clear_first: bool = True,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Set text in an input element via CDP."""
    group_id = generate_group_id("browser_set_text", f"{selector[:50]}_{text[:30]}")
    emit_info(
        f"BROWSER SET TEXT ✏️ selector='{selector}' text='{text[:50]}{'...' if len(text) > 50 else ''}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)
        input_domain = InputDomain(client)

        # Focus the element
        selector_escaped = selector.replace("'", "\\'")
        focus_js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (!el) return null;
            el.focus();
            el.click();
            return {{ success: true, tagName: el.tagName }};
        """

        result = await runtime.evaluate(
            focus_js, return_by_value=True, await_promise=False
        )

        if not result:
            return {
                "success": False,
                "error": f"Element not found: {selector}",
                "selector": selector,
                "text": text,
            }

        # Clear if requested
        if clear_first:
            clear_js = f"""
                const el = document.querySelector('{selector_escaped}');
                if (el) {{ el.value = ''; el.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
            """
            await runtime.evaluate(clear_js, return_by_value=False, await_promise=False)

        # Type text using Input.dispatchKeyEvent
        await input_domain.type_text(text)

        # Trigger input event
        event_js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (el) {{ el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}
        """
        await runtime.evaluate(event_js, return_by_value=False, await_promise=False)

        emit_success(f"Set text in element: {selector}", message_group=group_id)

        return {
            "success": True,
            "selector": selector,
            "text": text,
            "action": "set_text",
        }

    except Exception as e:
        emit_error(f"Set text failed: {str(e)}", message_group=group_id)
        return {"success": False, "error": str(e), "selector": selector, "text": text}


async def get_element_text(
    selector: str,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Get text content from an element via CDP."""
    group_id = generate_group_id("browser_get_text", selector[:100])
    emit_info(
        f"BROWSER GET TEXT 📝 selector='{selector}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (!el) return null;
            return {{
                text: el.textContent,
                innerText: el.innerText,
                visible: el.offsetParent !== null
            }};
        """

        result = await runtime.evaluate(js, return_by_value=True, await_promise=False)

        if not result:
            return {
                "success": False,
                "error": f"Element not found: {selector}",
                "selector": selector,
            }

        return {
            "success": True,
            "selector": selector,
            "text": result.get("text"),
            "inner_text": result.get("innerText"),
        }

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


async def get_element_value(
    selector: str,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Get value from an input element via CDP."""
    group_id = generate_group_id("browser_get_value", selector[:100])
    emit_info(
        f"BROWSER GET VALUE 📎 selector='{selector}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        selector_escaped = selector.replace("'", "\\'")
        js = f"""
            const el = document.querySelector('{selector_escaped}');
            if (!el) return null;
            return {{
                value: el.value,
                tagName: el.tagName,
                type: el.type,
                visible: el.offsetParent !== null
            }};
        """

        result = await runtime.evaluate(js, return_by_value=True, await_promise=False)

        if not result:
            return {
                "success": False,
                "error": f"Element not found: {selector}",
                "selector": selector,
            }

        return {"success": True, "selector": selector, "value": result.get("value")}

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


async def select_option(
    selector: str,
    value: Optional[str] = None,
    label: Optional[str] = None,
    index: Optional[int] = None,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Select an option in a dropdown/select element via CDP."""
    option_desc = value or label or str(index) if index is not None else "unknown"
    group_id = generate_group_id(
        "browser_select_option", f"{selector[:50]}_{option_desc}"
    )
    emit_info(
        f"BROWSER SELECT OPTION 📄 selector='{selector}' option='{option_desc}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        selection_js = ""
        if value is not None:
            selector_escaped = selector.replace("'", "\\'")
            value_escaped = value.replace("'", "\\'")
            selection_js = f"""
                const el = document.querySelector('{selector_escaped}');
                if (!el) return {{ error: 'Element not found' }};
                el.value = '{value_escaped}';
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return {{ success: true, value: el.value }};
            """
            selection = value
        elif label is not None:
            selector_escaped = selector.replace("'", "\\'")
            label_escaped = label.replace("'", "\\'")
            selection_js = f"""
                const el = document.querySelector('{selector_escaped}');
                if (!el) return {{ error: 'Element not found' }};
                const options = Array.from(el.options);
                const option = options.find(o => o.text === '{label_escaped}');
                if (option) {{ el.value = option.value; el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}
                return {{ success: !!option, value: el.value }};
            """
            selection = label
        elif index is not None:
            selector_escaped = selector.replace("'", "\\'")
            selection_js = f"""
                const el = document.querySelector('{selector_escaped}');
                if (!el) return {{ error: 'Element not found' }};
                if (el.options[{index}]) {{ el.selectedIndex = {index}; el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}
                return {{ success: !!el.options[{index}], value: el.value }};
            """
            selection = str(index)
        else:
            return {
                "success": False,
                "error": "Must specify value, label, or index",
                "selector": selector,
            }

        result = await runtime.evaluate(
            selection_js, return_by_value=True, await_promise=False
        )

        if not result or not result.get("success"):
            error = result.get("error") if result else "Selection failed"
            return {"success": False, "error": error, "selector": selector}

        emit_success(
            f"Selected option in {selector}: {selection}",
            message_group=group_id,
        )

        return {"success": True, "selector": selector, "selection": selection}

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


async def check_element(
    selector: str,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Check a checkbox or radio button via CDP."""
    group_id = generate_group_id("browser_check", selector[:100])
    emit_info(
        f"BROWSER CHECK ☑️ selector='{selector}'",
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
            if (el.type !== 'checkbox' && el.type !== 'radio') return {{ error: 'Not a checkbox/radio' }};
            el.checked = true;
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return {{ success: true }};
        """

        result = await runtime.evaluate(js, return_by_value=True, await_promise=False)

        if not result or not result.get("success"):
            error = result.get("error") if result else "Check failed"
            return {"success": False, "error": error, "selector": selector}

        emit_success(f"Checked element: {selector}", message_group=group_id)

        return {"success": True, "selector": selector, "action": "check"}

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


async def uncheck_element(
    selector: str,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Uncheck a checkbox via CDP."""
    group_id = generate_group_id("browser_uncheck", selector[:100])
    emit_info(
        f"BROWSER UNCHECK ☐️ selector='{selector}'",
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
            if (el.type !== 'checkbox') return {{ error: 'Not a checkbox' }};
            el.checked = false;
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return {{ success: true }};
        """

        result = await runtime.evaluate(js, return_by_value=True, await_promise=False)

        if not result or not result.get("success"):
            error = result.get("error") if result else "Uncheck failed"
            return {"success": False, "error": error, "selector": selector}

        emit_success(f"Unchecked element: {selector}", message_group=group_id)

        return {"success": True, "selector": selector, "action": "uncheck"}

    except Exception as e:
        return {"success": False, "error": str(e), "selector": selector}


# Tool registration functions
def register_click_element(agent):
    """Register the click element tool."""

    @agent.tool
    async def browser_click(
        context: RunContext,
        selector: str,
        timeout: int = 10000,
        force: bool = False,
        button: str = "left",
        modifiers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Click on an element in the browser.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds to wait for element
            force: Skip actionability checks and force the click
            button: Mouse button to click (left, right, middle)
            modifiers: Modifier keys to hold (Alt, Control, Meta, Shift)

        Returns:
            Dict with click results
        """
        return await click_element(selector, timeout, force, button, modifiers)


def register_double_click_element(agent):
    """Register the double-click element tool."""

    @agent.tool
    async def browser_double_click(
        context: RunContext,
        selector: str,
        timeout: int = 10000,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Double-click on an element in the browser.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds to wait for element
            force: Skip actionability checks and force the double-click

        Returns:
            Dict with double-click results
        """
        return await double_click_element(selector, timeout, force)


def register_hover_element(agent):
    """Register the hover element tool."""

    @agent.tool
    async def browser_hover(
        context: RunContext,
        selector: str,
        timeout: int = 10000,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Hover over an element in the browser.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds to wait for element
            force: Skip actionability checks and force the hover

        Returns:
            Dict with hover results
        """
        return await hover_element(selector, timeout, force)


def register_set_element_text(agent):
    """Register the set element text tool."""

    @agent.tool
    async def browser_set_text(
        context: RunContext,
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Set text in an input element.

        Args:
            selector: CSS or XPath selector for the input element
            text: Text to enter
            clear_first: Whether to clear existing text first
            timeout: Timeout in milliseconds to wait for element

        Returns:
            Dict with text input results
        """
        return await set_element_text(selector, text, clear_first, timeout)


def register_get_element_text(agent):
    """Register the get element text tool."""

    @agent.tool
    async def browser_get_text(
        context: RunContext,
        selector: str,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Get text content from an element.

        Args:
            selector: CSS or XPath selector for the element
            timeout: Timeout in milliseconds to wait for element

        Returns:
            Dict with element text content
        """
        return await get_element_text(selector, timeout)


def register_get_element_value(agent):
    """Register the get element value tool."""

    @agent.tool
    async def browser_get_value(
        context: RunContext,
        selector: str,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Get value from an input element.

        Args:
            selector: CSS or XPath selector for the input element
            timeout: Timeout in milliseconds to wait for element

        Returns:
            Dict with element value
        """
        return await get_element_value(selector, timeout)


def register_select_option(agent):
    """Register the select option tool."""

    @agent.tool
    async def browser_select_option(
        context: RunContext,
        selector: str,
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Select an option in a dropdown/select element.

        Args:
            selector: CSS or XPath selector for the select element
            value: Option value to select
            label: Option label text to select
            index: Option index to select (0-based)
            timeout: Timeout in milliseconds to wait for element

        Returns:
            Dict with selection results
        """
        return await select_option(selector, value, label, index, timeout)


def register_browser_check(agent):
    """Register checkbox/radio button check tool."""

    @agent.tool
    async def browser_check(
        context: RunContext,
        selector: str,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Check a checkbox or radio button.

        Args:
            selector: CSS or XPath selector for the checkbox/radio
            timeout: Timeout in milliseconds to wait for element

        Returns:
            Dict with check results
        """
        return await check_element(selector, timeout)


def register_browser_uncheck(agent):
    """Register checkbox uncheck tool."""

    @agent.tool
    async def browser_uncheck(
        context: RunContext,
        selector: str,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Uncheck a checkbox.

        Args:
            selector: CSS or XPath selector for the checkbox
            timeout: Timeout in milliseconds to wait for element

        Returns:
            Dict with uncheck results
        """
        return await uncheck_element(selector, timeout)
