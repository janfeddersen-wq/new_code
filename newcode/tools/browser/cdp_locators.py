"""CDP-based browser element discovery tools using semantic locators and XPath.

These tools mirror the existing Playwright-based browser_locators.py API
but use Chrome DevTools Protocol (CDP) instead.
"""

from typing import Any, Dict, Optional

from pydantic_ai import RunContext

from newcode.messaging import emit_info, emit_success
from newcode.tools.common import generate_group_id

from .cdp_domains import RuntimeDomain
from .cdp_manager import get_session_cdp_manager


async def find_by_role(
    role: str,
    name: Optional[str] = None,
    exact: bool = False,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Find elements by ARIA role via CDP."""
    group_id = generate_group_id("browser_find_by_role", f"{role}_{name or 'any'}")
    emit_info(
        f"BROWSER FIND BY ROLE 🎨 role={role} name={name}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        # Build JavaScript to find elements by role
        if name:
            if exact:
                js = f"""
                    Array.from(document.querySelectorAll('[role=\"{role}\"]'))
                        .filter(el => el.textContent.trim() === '{name}' || 
                                    el.getAttribute('aria-label') === '{name}' ||
                                    el.getAttribute('aria-labelledby') && 
                                    document.getElementById(el.getAttribute('aria-labelledby'))?.textContent.trim() === '{name}')
                        .map((el, i) => ({{
                            index: i,
                            tag: el.tagName.toLowerCase(),
                            text: el.textContent.trim().slice(0, 100),
                            visible: el.offsetParent !== null
                        }}))
                """
            else:
                js = f"""
                    Array.from(document.querySelectorAll('[role=\"{role}\"]'))
                        .filter(el => el.textContent.toLowerCase().includes('{name.lower()}') || 
                                    (el.getAttribute('aria-label') || '').toLowerCase().includes('{name.lower()}'))
                        .map((el, i) => ({{
                            index: i,
                            tag: el.tagName.toLowerCase(),
                            text: el.textContent.trim().slice(0, 100),
                            visible: el.offsetParent !== null
                        }}))
                """
        else:
            js = f"""
                Array.from(document.querySelectorAll('[role=\"{role}\"]'))
                    .map((el, i) => ({{
                        index: i,
                        tag: el.tagName.toLowerCase(),
                        text: el.textContent.trim().slice(0, 100),
                        visible: el.offsetParent !== null
                    }}))
            """

        elements = (
            await runtime.evaluate(js, return_by_value=True, await_promise=False) or []
        )

        # Filter visible elements
        visible_elements = [e for e in elements if e.get("visible")]

        emit_success(
            f"Found {len(visible_elements)} elements with role '{role}'",
            message_group=group_id,
        )

        return {
            "success": True,
            "role": role,
            "name": name,
            "count": len(visible_elements),
            "elements": visible_elements[:10],  # Limit to first 10
        }

    except Exception as e:
        return {"success": False, "error": str(e), "role": role, "name": name}


async def find_by_text(
    text: str,
    exact: bool = False,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Find elements containing specific text via CDP."""
    group_id = generate_group_id("browser_find_by_text", text[:50])
    emit_info(
        f"BROWSER FIND BY TEXT 🔍 text='{text}' exact={exact}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        # Build JavaScript to find elements by text
        if exact:
            js = f"""
                Array.from(document.querySelectorAll('*'))
                    .filter(el => el.children.length === 0 && el.textContent.trim() === '{text}')
                    .map((el, i) => ({{
                        index: i,
                        tag: el.tagName.toLowerCase(),
                        text: el.textContent.trim(),
                        visible: el.offsetParent !== null
                    }}))
            """
        else:
            js = f"""
                Array.from(document.querySelectorAll('*'))
                    .filter(el => el.textContent.toLowerCase().includes('{text.lower()}'))
                    .slice(0, 20)
                    .map((el, i) => ({{
                        index: i,
                        tag: el.tagName.toLowerCase(),
                        text: el.textContent.trim().slice(0, 100),
                        visible: el.offsetParent !== null
                    }}))
            """

        elements = (
            await runtime.evaluate(js, return_by_value=True, await_promise=False) or []
        )
        visible_elements = [e for e in elements if e.get("visible")]

        emit_success(
            f"Found {len(visible_elements)} elements containing text '{text}'",
            message_group=group_id,
        )

        return {
            "success": True,
            "search_text": text,
            "exact": exact,
            "count": len(visible_elements),
            "elements": visible_elements[:10],
        }

    except Exception as e:
        return {"success": False, "error": str(e), "search_text": text}


async def find_by_label(
    text: str,
    exact: bool = False,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Find form elements by their associated label text via CDP."""
    group_id = generate_group_id("browser_find_by_label", text[:50])
    emit_info(
        f"BROWSER FIND BY LABEL 🏷️ label='{text}' exact={exact}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        # Find elements by label (labels with for attribute or label-contained inputs)
        if exact:
            js = f"""
                const labels = Array.from(document.querySelectorAll('label'))
                    .filter(l => l.textContent.trim() === '{text}');
                const results = [];
                labels.forEach((label, i) => {{
                    const forAttr = label.getAttribute('for');
                    if (forAttr) {{
                        const el = document.getElementById(forAttr);
                        if (el) {{
                            results.push({{
                                index: i,
                                tag: el.tagName.toLowerCase(),
                                type: el.type,
                                value: el.value,
                                visible: el.offsetParent !== null
                            }});
                        }}
                    }} else {{
                        const inputs = label.querySelectorAll('input, select, textarea');
                        inputs.forEach((el, j) => {{
                            results.push({{
                                index: i * 100 + j,
                                tag: el.tagName.toLowerCase(),
                                type: el.type,
                                value: el.value,
                                visible: el.offsetParent !== null
                            }});
                        }});
                    }}
                }});
                results;
            """
        else:
            js = f"""
                const labels = Array.from(document.querySelectorAll('label'))
                    .filter(l => l.textContent.toLowerCase().includes('{text.lower()}'));
                const results = [];
                labels.forEach((label, i) => {{
                    const forAttr = label.getAttribute('for');
                    if (forAttr) {{
                        const el = document.getElementById(forAttr);
                        if (el) {{
                            results.push({{
                                index: i,
                                tag: el.tagName.toLowerCase(),
                                type: el.type,
                                value: el.value,
                                visible: el.offsetParent !== null
                            }});
                        }}
                    }} else {{
                        const inputs = label.querySelectorAll('input, select, textarea');
                        inputs.forEach((el, j) => {{
                            results.push({{
                                index: i * 100 + j,
                                tag: el.tagName.toLowerCase(),
                                type: el.type,
                                value: el.value,
                                visible: el.offsetParent !== null
                            }});
                        }});
                    }}
                }});
                results;
            """

        elements = (
            await runtime.evaluate(js, return_by_value=True, await_promise=False) or []
        )
        visible_elements = [e for e in elements if e.get("visible")]

        emit_success(
            f"Found {len(visible_elements)} elements with label '{text}'",
            message_group=group_id,
        )

        return {
            "success": True,
            "label_text": text,
            "exact": exact,
            "count": len(visible_elements),
            "elements": visible_elements[:10],
        }

    except Exception as e:
        return {"success": False, "error": str(e), "label_text": text}


async def find_by_placeholder(
    text: str,
    exact: bool = False,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Find elements by placeholder text via CDP."""
    group_id = generate_group_id("browser_find_by_placeholder", text[:50])
    emit_info(
        f"BROWSER FIND BY PLACEHOLDER 📝 placeholder='{text}' exact={exact}",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        if exact:
            js = f"""
                Array.from(document.querySelectorAll('[placeholder=\"{text}\"]'))
                    .map((el, i) => ({{
                        index: i,
                        tag: el.tagName.toLowerCase(),
                        placeholder: el.placeholder,
                        value: el.value,
                        visible: el.offsetParent !== null
                    }}))
            """
        else:
            js = f"""
                Array.from(document.querySelectorAll('[placeholder]'))
                    .filter(el => el.placeholder.toLowerCase().includes('{text.lower()}'))
                    .map((el, i) => ({{
                        index: i,
                        tag: el.tagName.toLowerCase(),
                        placeholder: el.placeholder,
                        value: el.value,
                        visible: el.offsetParent !== null
                    }}))
            """

        elements = (
            await runtime.evaluate(js, return_by_value=True, await_promise=False) or []
        )
        visible_elements = [e for e in elements if e.get("visible")]

        emit_success(
            f"Found {len(visible_elements)} elements with placeholder '{text}'",
            message_group=group_id,
        )

        return {
            "success": True,
            "placeholder_text": text,
            "exact": exact,
            "count": len(visible_elements),
            "elements": visible_elements[:10],
        }

    except Exception as e:
        return {"success": False, "error": str(e), "placeholder_text": text}


async def find_by_test_id(
    test_id: str,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Find elements by test ID attribute via CDP."""
    group_id = generate_group_id("browser_find_by_test_id", test_id)
    emit_info(
        f"BROWSER FIND BY TEST ID 🧪 test_id='{test_id}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        js = f"""
            Array.from(document.querySelectorAll('[data-testid=\"{test_id}\"]'))
                .map((el, i) => ({{
                    index: i,
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.trim().slice(0, 100),
                    test_id: '{test_id}',
                    visible: el.offsetParent !== null
                }}))
        """

        elements = (
            await runtime.evaluate(js, return_by_value=True, await_promise=False) or []
        )
        visible_elements = [e for e in elements if e.get("visible")]

        emit_success(
            f"Found {len(visible_elements)} elements with test-id '{test_id}'",
            message_group=group_id,
        )

        return {
            "success": True,
            "test_id": test_id,
            "count": len(visible_elements),
            "elements": visible_elements[:10],
        }

    except Exception as e:
        return {"success": False, "error": str(e), "test_id": test_id}


async def run_xpath_query(
    xpath: str,
    timeout: int = 10000,
) -> Dict[str, Any]:
    """Find elements using XPath selector via CDP."""
    group_id = generate_group_id("browser_xpath_query", xpath[:100])
    emit_info(
        f"BROWSER XPATH QUERY 🔍 xpath='{xpath}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        # Use XPath via JavaScript
        xpath_escaped = xpath.replace("'", "\\'")
        js = f"""
            const result = document.evaluate(
                '{xpath_escaped}',
                document,
                null,
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                null
            );
            const elements = [];
            for (let i = 0; i < Math.min(result.snapshotLength, 20); i++) {{
                const el = result.snapshotItem(i);
                elements.push({{
                    index: i,
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.trim().slice(0, 100),
                    class: el.className,
                    id: el.id,
                    visible: el.offsetParent !== null
                }});
            }}
            elements;
        """

        elements = (
            await runtime.evaluate(js, return_by_value=True, await_promise=False) or []
        )
        visible_elements = [e for e in elements if e.get("visible")]

        emit_success(
            f"Found {len(visible_elements)} elements with XPath '{xpath}'",
            message_group=group_id,
        )

        return {
            "success": True,
            "xpath": xpath,
            "count": len(visible_elements),
            "elements": visible_elements,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "xpath": xpath}


async def find_buttons(
    text_filter: Optional[str] = None, timeout: int = 10000
) -> Dict[str, Any]:
    """Find all button elements on the page via CDP."""
    group_id = generate_group_id("browser_find_buttons", text_filter or "all")
    emit_info(
        f"BROWSER FIND BUTTONS 🔘 filter='{text_filter or 'none'}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        if text_filter:
            js = f"""
                Array.from(document.querySelectorAll('button, [role=\"button\"], input[type=\"button\"], input[type=\"submit\"]'))
                    .filter(el => el.textContent.toLowerCase().includes('{text_filter.lower()}') ||
                                el.value?.toLowerCase().includes('{text_filter.lower()}'))
                    .slice(0, 20)
                    .map((el, i) => ({{
                        index: i,
                        text: el.textContent.trim() || el.value || '',
                        visible: el.offsetParent !== null
                    }}))
            """
        else:
            js = """
                Array.from(document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]'))
                    .slice(0, 20)
                    .map((el, i) => ({
                        index: i,
                        text: el.textContent.trim() || el.value || '',
                        visible: el.offsetParent !== null
                    }))
            """

        buttons = (
            await runtime.evaluate(js, return_by_value=True, await_promise=False) or []
        )
        visible_buttons = [b for b in buttons if b.get("visible")]

        emit_success(
            f"Found {len(visible_buttons)} buttons"
            + (f" containing '{text_filter}'" if text_filter else ""),
            message_group=group_id,
        )

        return {
            "success": True,
            "text_filter": text_filter,
            "total_count": len(buttons),
            "filtered_count": len(visible_buttons),
            "buttons": visible_buttons,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "text_filter": text_filter}


async def find_links(
    text_filter: Optional[str] = None, timeout: int = 10000
) -> Dict[str, Any]:
    """Find all link elements on the page via CDP."""
    group_id = generate_group_id("browser_find_links", text_filter or "all")
    emit_info(
        f"BROWSER FIND LINKS 🔗 filter='{text_filter or 'none'}'",
        message_group=group_id,
    )
    try:
        browser_manager = get_session_cdp_manager()
        client = browser_manager.get_client()
        runtime = RuntimeDomain(client)

        if text_filter:
            js = f"""
                Array.from(document.querySelectorAll('a, [role=\"link\"]'))
                    .filter(el => el.textContent.toLowerCase().includes('{text_filter.lower()}'))
                    .slice(0, 20)
                    .map((el, i) => ({{
                        index: i,
                        text: el.textContent.trim(),
                        href: el.href,
                        visible: el.offsetParent !== null
                    }}))
            """
        else:
            js = """
                Array.from(document.querySelectorAll('a, [role="link"]'))
                    .slice(0, 20)
                    .map((el, i) => ({
                        index: i,
                        text: el.textContent.trim(),
                        href: el.href,
                        visible: el.offsetParent !== null
                    }))
            """

        links = (
            await runtime.evaluate(js, return_by_value=True, await_promise=False) or []
        )
        visible_links = [link for link in links if link.get("visible")]

        emit_success(
            f"Found {len(visible_links)} links"
            + (f" containing '{text_filter}'" if text_filter else ""),
            message_group=group_id,
        )

        return {
            "success": True,
            "text_filter": text_filter,
            "total_count": len(links),
            "filtered_count": len(visible_links),
            "links": visible_links,
        }

    except Exception as e:
        return {"success": False, "error": str(e), "text_filter": text_filter}


# Tool registration functions
def register_find_by_role(agent):
    """Register the find by role tool."""

    @agent.tool
    async def browser_find_by_role(
        context: RunContext,
        role: str,
        name: Optional[str] = None,
        exact: bool = False,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find elements by ARIA role (recommended for accessibility).

        Args:
            role: ARIA role (button, link, textbox, heading, etc.)
            name: Optional accessible name to filter by
            exact: Whether to match name exactly
            timeout: Timeout in milliseconds

        Returns:
            Dict with found elements and their properties
        """
        return await find_by_role(role, name, exact, timeout)


def register_find_by_text(agent):
    """Register the find by text tool."""

    @agent.tool
    async def browser_find_by_text(
        context: RunContext,
        text: str,
        exact: bool = False,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find elements containing specific text content.

        Args:
            text: Text to search for
            exact: Whether to match text exactly
            timeout: Timeout in milliseconds

        Returns:
            Dict with found elements and their properties
        """
        return await find_by_text(text, exact, timeout)


def register_find_by_label(agent):
    """Register the find by label tool."""

    @agent.tool
    async def browser_find_by_label(
        context: RunContext,
        text: str,
        exact: bool = False,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find form elements by their associated label text.

        Args:
            text: Label text to search for
            exact: Whether to match label exactly
            timeout: Timeout in milliseconds

        Returns:
            Dict with found form elements and their properties
        """
        return await find_by_label(text, exact, timeout)


def register_find_by_placeholder(agent):
    """Register the find by placeholder tool."""

    @agent.tool
    async def browser_find_by_placeholder(
        context: RunContext,
        text: str,
        exact: bool = False,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find elements by placeholder text.

        Args:
            text: Placeholder text to search for
            exact: Whether to match placeholder exactly
            timeout: Timeout in milliseconds

        Returns:
            Dict with found elements and their properties
        """
        return await find_by_placeholder(text, exact, timeout)


def register_find_by_test_id(agent):
    """Register the find by test ID tool."""

    @agent.tool
    async def browser_find_by_test_id(
        context: RunContext,
        test_id: str,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find elements by test ID attribute (data-testid).

        Args:
            test_id: Test ID to search for
            timeout: Timeout in milliseconds

        Returns:
            Dict with found elements and their properties
        """
        return await find_by_test_id(test_id, timeout)


def register_run_xpath_query(agent):
    """Register the XPath query tool."""

    @agent.tool
    async def browser_xpath_query(
        context: RunContext,
        xpath: str,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find elements using XPath selector (fallback when semantic locators fail).

        Args:
            xpath: XPath expression
            timeout: Timeout in milliseconds

        Returns:
            Dict with found elements and their properties
        """
        return await run_xpath_query(xpath, timeout)


def register_find_buttons(agent):
    """Register the find buttons tool."""

    @agent.tool
    async def browser_find_buttons(
        context: RunContext,
        text_filter: Optional[str] = None,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find all button elements on the page.

        Args:
            text_filter: Optional text to filter buttons by
            timeout: Timeout in milliseconds

        Returns:
            Dict with found buttons and their properties
        """
        return await find_buttons(text_filter, timeout)


def register_find_links(agent):
    """Register the find links tool."""

    @agent.tool
    async def browser_find_links(
        context: RunContext,
        text_filter: Optional[str] = None,
        timeout: int = 10000,
    ) -> Dict[str, Any]:
        """
        Find all link elements on the page.

        Args:
            text_filter: Optional text to filter links by
            timeout: Timeout in milliseconds

        Returns:
            Dict with found links and their properties
        """
        return await find_links(text_filter, timeout)
