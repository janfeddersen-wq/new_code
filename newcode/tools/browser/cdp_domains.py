"""Chrome DevTools Protocol (CDP) Domain Wrappers.

This module provides Pythonic wrappers for common CDP domains, converting
low-level CDP commands and responses into easy-to-use Python methods.

Each domain wrapper takes a CDPClient instance and provides methods that
handle CDP-specific parameters and return formats.

Example:
    >>> from newcode.tools.browser.cdp_client import CDPClient
    >>> from newcode.tools.browser.cdp_domains import PageDomain, RuntimeDomain
    >>>
    >>> client = CDPClient()
    >>> await client.connect("localhost", 9222)
    >>>
    >>> # Use Page domain
    >>> page = PageDomain(client)
    >>> await page.navigate("https://example.com")
    >>> screenshot = await page.capture_screenshot()
    >>>
    >>> # Use Runtime domain
    >>> runtime = RuntimeDomain(client)
    >>> result = await runtime.evaluate("document.title")
    >>> print(f"Page title: {result}")

Domains:
    - PageDomain: Page navigation, screenshots, lifecycle
    - DOMDomain: DOM querying and manipulation
    - RuntimeDomain: JavaScript execution
    - InputDomain: Mouse and keyboard events
    - TargetDomain: Browser tab/target management
"""

from __future__ import annotations

import base64
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from newcode.messaging import emit_info, emit_warning

from .cdp_client import CDPClient, CDPClientError, CDPResponse

logger = logging.getLogger(__name__)


@dataclass
class CDPNode:
    """Represents a DOM node from CDP.

    Attributes:
        node_id: CDP node ID (unique per session).
        backend_node_id: Backend node ID (stable across sessions).
        node_type: Node type (e.g., 1 = Element, 3 = Text).
        node_name: HTML tag name (e.g., "DIV", "A").
        local_name: Local name without namespace.
        node_value: Text content for text nodes.
        attributes: List of attribute name-value pairs [name, value, name, value, ...].
        child_node_ids: IDs of child nodes.
        parent_id: ID of parent node.
        document_url: Document URL for document nodes.
        base_url: Base URL for resolving relative URLs.
    """

    node_id: int
    backend_node_id: int | None = None
    node_type: int = 1
    node_name: str = ""
    local_name: str = ""
    node_value: str = ""
    attributes: list[str] = field(default_factory=list)
    child_node_ids: list[int] = field(default_factory=list)
    parent_id: int | None = None
    document_url: str | None = None
    base_url: str | None = None

    @property
    def tag_name(self) -> str:
        """Get the tag name in lowercase (e.g., 'div', 'a')."""
        return self.local_name.lower() if self.local_name else self.node_name.lower()

    @property
    def text_content(self) -> str:
        """Get the text content (node_value)."""
        return self.node_value

    def get_attribute(self, name: str) -> str | None:
        """Get an attribute value by name (case-insensitive).

        Args:
            name: Attribute name to look up.

        Returns:
            Attribute value or None if not found.
        """
        name_lower = name.lower()
        for i in range(0, len(self.attributes), 2):
            if self.attributes[i].lower() == name_lower:
                return self.attributes[i + 1] if i + 1 < len(self.attributes) else None
        return None

    @classmethod
    def from_cdp(cls, data: dict[str, Any]) -> CDPNode:
        """Create a CDPNode from CDP response data."""
        return cls(
            node_id=data.get("nodeId", 0),
            backend_node_id=data.get("backendNodeId"),
            node_type=data.get("nodeType", 1),
            node_name=data.get("nodeName", ""),
            local_name=data.get("localName", ""),
            node_value=data.get("nodeValue", ""),
            attributes=data.get("attributes", []),
            child_node_ids=[c.get("nodeId", 0) for c in data.get("children", [])],
            parent_id=data.get("parentId"),
            document_url=data.get("documentURL"),
            base_url=data.get("baseURL"),
        )


@dataclass
class CDPFrame:
    """Represents a page frame from CDP.

    Attributes:
        id: Frame ID.
        parent_id: Parent frame ID (None for main frame).
        loader_id: Loader ID.
        name: Frame name (from iframe name attribute).
        url: Current URL.
        security_origin: Security origin.
        mime_type: Document MIME type.
    """

    id: str
    parent_id: str | None = None
    loader_id: str | None = None
    name: str | None = None
    url: str = ""
    security_origin: str = ""
    mime_type: str = ""

    @classmethod
    def from_cdp(cls, data: dict[str, Any]) -> CDPFrame:
        """Create a CDPFrame from CDP response data."""
        return cls(
            id=data.get("id", ""),
            parent_id=data.get("parentId"),
            loader_id=data.get("loaderId"),
            name=data.get("name"),
            url=data.get("url", ""),
            security_origin=data.get("securityOrigin", ""),
            mime_type=data.get("mimeType", ""),
        )


class CDPDomain(ABC):
    """Base class for CDP domain wrappers.

    Attributes:
        client: The CDPClient instance to use for commands.
        domain_name: The CDP domain name (e.g., "Page", "Runtime").
    """

    def __init__(self, client: CDPClient):
        """Initialize the domain wrapper.

        Args:
            client: The CDPClient instance.
        """
        self.client = client
        self._enabled: bool = False

    @property
    @abstractmethod
    def domain_name(self) -> str:
        """Return the CDP domain name."""
        raise NotImplementedError

    async def enable(self) -> CDPResponse:
        """Enable this domain to receive its events.

        Returns:
            The CDP response from the enable command.
        """
        response = await self.client.enable_domain(self.domain_name)
        self._enabled = True
        return response

    async def disable(self) -> CDPResponse:
        """Disable this domain to stop receiving its events.

        Returns:
            The CDP response from the disable command.
        """
        response = await self.client.disable_domain(self.domain_name)
        self._enabled = False
        return response


class PageDomain(CDPDomain):
    """Wrapper for the CDP Page domain.

    Provides methods for page navigation, screenshots, and lifecycle management.

    Example:
        >>> page = PageDomain(client)
        >>> await page.enable()  # Enable Page events
        >>> await page.navigate("https://example.com")
        >>> await page.wait_for_load("networkidle")
        >>> screenshot = await page.capture_screenshot()
    """

    @property
    def domain_name(self) -> str:
        return "Page"

    async def navigate(
        self, url: str, frame_id: str | None = None, referrer: str | None = None
    ) -> dict[str, Any]:
        """Navigate to a URL.

        Args:
            url: URL to navigate to.
            frame_id: Optional frame ID to navigate. If None, navigates main frame.
            referrer: Optional referrer URL.

        Returns:
            Navigation result with 'frameId', 'loaderId', etc.

        Raises:
            CDPClientError: If navigation fails.
        """
        params: dict[str, Any] = {"url": url}
        if frame_id:
            params["frameId"] = frame_id
        if referrer:
            params["referrer"] = referrer

        response = await self.client.send_command("Page.navigate", params)
        result = response.result or {}

        emit_info(f"Navigated to {url}, frameId: {result.get('frameId')}")
        return result

    async def reload(
        self,
        ignore_cache: bool = False,
        script_to_evaluate_on_load: str | None = None,
    ) -> None:
        """Reload the current page.

        Args:
            ignore_cache: Whether to ignore browser cache.
            script_to_evaluate_on_load: JavaScript to execute on load.
        """
        params: dict[str, Any] = {"ignoreCache": ignore_cache}
        if script_to_evaluate_on_load:
            params["scriptToEvaluateOnLoad"] = script_to_evaluate_on_load

        await self.client.send_command("Page.reload", params)
        emit_info("Page reloaded")

    async def go_back(self) -> dict[str, Any] | None:
        """Navigate back in history.

        Returns:
            Navigation history result or None if no history.
        """
        try:
            response = await self.client.send_command(
                "Runtime.evaluate",
                {
                    "expression": "history.back()",
                    "awaitPromise": True,
                },
            )
            # Wait a bit for navigation
            import asyncio

            await asyncio.sleep(0.5)
            return response.result
        except CDPClientError as e:
            emit_warning(f"Failed to go back: {e}")
            return None

    async def go_forward(self) -> dict[str, Any] | None:
        """Navigate forward in history.

        Returns:
            Navigation history result or None if no history.
        """
        try:
            response = await self.client.send_command(
                "Runtime.evaluate",
                {
                    "expression": "history.forward()",
                    "awaitPromise": True,
                },
            )
            # Wait a bit for navigation
            import asyncio

            await asyncio.sleep(0.5)
            return response.result
        except CDPClientError as e:
            emit_warning(f"Failed to go forward: {e}")
            return None

    async def capture_screenshot(
        self,
        format: str = "png",
        quality: int | None = None,
        full_page: bool = False,
        clip: dict[str, Any] | None = None,
        from_surface: bool = True,
    ) -> bytes:
        """Capture a screenshot of the page.

        Args:
            format: Image format ("png" or "jpeg").
            quality: JPEG quality (0-100), only for jpeg format.
            full_page: Whether to capture the full scrollable page.
            clip: Optional clip rectangle {"x", "y", "width", "height", "scale"}.
            from_surface: Capture from surface (True) or viewport (False).

        Returns:
            Screenshot image data as bytes.

        Raises:
            CDPClientError: If screenshot capture fails.
        """
        if format not in ("png", "jpeg"):
            raise ValueError(f"Invalid format: {format}. Use 'png' or 'jpeg'")

        params: dict[str, Any] = {
            "format": format,
            "fromSurface": from_surface,
        }

        if format == "jpeg" and quality is not None:
            params["quality"] = quality

        if full_page:
            params["captureBeyondViewport"] = True

        if clip:
            params["clip"] = clip

        response = await self.client.send_command("Page.captureScreenshot", params)
        result = response.result or {}
        data = result.get("data", "")

        if not data:
            raise CDPClientError("Screenshot returned no data")

        return base64.b64decode(data)

    async def get_frame_tree(self) -> dict[str, Any]:
        """Get the page frame tree.

        Returns:
            Frame tree structure with nested frames.
        """
        response = await self.client.send_command("Page.getFrameTree", {})
        return response.result or {}

    async def bring_to_front(self) -> None:
        """Bring the page to front (activate tab)."""
        await self.client.send_command("Page.bringToFront", {})

    async def set_viewport_size(self, width: int, height: int) -> None:
        """Set the viewport size.

        Args:
            width: Viewport width in pixels.
            height: Viewport height in pixels.
        """
        await self.client.send_command(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )
        emit_info(f"Viewport size set to {width}x{height}")

    async def wait_for_load(
        self, wait_until: str = "load", timeout: float = 30.0
    ) -> bool:
        """Wait for page to reach a specific load state.

        This is a helper that waits for CDP events. You must enable the Page
        domain first with await page.enable().

        Args:
            wait_until: Load state to wait for ("load", "domcontentloaded", "networkidle").
            timeout: Maximum time to wait in seconds.

        Returns:
            True if the load state was reached, False if timeout.
        """
        import asyncio

        event_name = {
            "load": "Page.loadEventFired",
            "domcontentloaded": "Page.domContentEventFired",
            "networkidle": "Page.loadEventFired",  # Approximation
        }.get(wait_until, "Page.loadEventFired")

        future: asyncio.Future[dict[str, Any]] = (
            asyncio.get_event_loop().create_future()
        )

        async def on_event(params: dict[str, Any]) -> None:
            if not future.done():
                future.set_result(params)

        self.client.on_event(event_name, on_event)

        try:
            await asyncio.wait_for(future, timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
        finally:
            self.client.remove_event_listener(event_name, on_event)


class DOMDomain(CDPDomain):
    """Wrapper for the CDP DOM domain.

    Provides methods for DOM querying, inspection, and manipulation.

    Example:
        >>> dom = DOMDomain(client)
        >>> await dom.enable()
        >>>
        >>> # Get the document root
        >>> doc = await dom.get_document()
        >>>
        >>> # Query for an element
        >>> node_id = await dom.query_selector(doc.node_id, "#my-element")
        >>> if node_id:
        ...     info = await dom.describe_node(node_id)
        ...     print(f"Found: {info.node_name}")
    """

    @property
    def domain_name(self) -> str:
        return "DOM"

    async def get_document(self, depth: int = 1) -> CDPNode:
        """Get the document root node.

        Args:
            depth: Maximum depth to fetch (0 = unlimited).

        Returns:
            The root document node.
        """
        params: dict[str, Any] = {"pierce": True}
        if depth > 0:
            params["depth"] = depth

        response = await self.client.send_command("DOM.getDocument", params)
        result = response.result or {}
        root_data = result.get("root", {})
        return CDPNode.from_cdp(root_data)

    async def query_selector(self, node_id: int, selector: str) -> int | None:
        """Query for an element using a CSS selector.

        Args:
            node_id: Parent node ID to search within.
            selector: CSS selector string.

        Returns:
            Node ID if found, None otherwise.
        """
        try:
            response = await self.client.send_command(
                "DOM.querySelector",
                {
                    "nodeId": node_id,
                    "selector": selector,
                },
            )
            result = response.result or {}
            node_id_result = result.get("nodeId", 0)
            return node_id_result if node_id_result > 0 else None
        except CDPClientError as e:
            emit_warning(f"Query selector failed: {e}")
            return None

    async def query_selector_all(self, node_id: int, selector: str) -> list[int]:
        """Query for all elements matching a CSS selector.

        Args:
            node_id: Parent node ID to search within.
            selector: CSS selector string.

        Returns:
            List of matching node IDs.
        """
        try:
            response = await self.client.send_command(
                "DOM.querySelectorAll",
                {
                    "nodeId": node_id,
                    "selector": selector,
                },
            )
            result = response.result or {}
            return result.get("nodeIds", [])
        except CDPClientError as e:
            emit_warning(f"Query selector all failed: {e}")
            return []

    async def describe_node(
        self, node_id: int, depth: int = 1, pierce: bool = False
    ) -> CDPNode | None:
        """Describe a node in detail.

        Args:
            node_id: Node ID to describe.
            depth: Maximum depth to fetch children.
            pierce: Whether to pierce through shadow DOM.

        Returns:
            Detailed node information or None if not found.
        """
        try:
            response = await self.client.send_command(
                "DOM.describeNode",
                {
                    "nodeId": node_id,
                    "depth": depth,
                    "pierce": pierce,
                },
            )
            result = response.result or {}
            node_data = result.get("node", {})
            return CDPNode.from_cdp(node_data) if node_data else None
        except CDPClientError as e:
            emit_warning(f"Describe node failed: {e}")
            return None

    async def request_node(self, object_id: str) -> int | None:
        """Request a node ID from a Runtime object ID.

        Args:
            object_id: Runtime remote object ID.

        Returns:
            Node ID if successful, None otherwise.
        """
        try:
            response = await self.client.send_command(
                "DOM.requestNode",
                {
                    "objectId": object_id,
                },
            )
            result = response.result or {}
            node_id = result.get("nodeId", 0)
            return node_id if node_id > 0 else None
        except CDPClientError as e:
            emit_warning(f"Request node failed: {e}")
            return None

    async def focus_node(self, node_id: int) -> None:
        """Focus a DOM node.

        Args:
            node_id: Node ID to focus.
        """
        await self.client.send_command("DOM.focus", {"nodeId": node_id})

    async def set_node_value(self, node_id: int, value: str) -> None:
        """Set the value of a DOM node (text content).

        Args:
            node_id: Node ID to modify.
            value: New text content.
        """
        await self.client.send_command(
            "DOM.setNodeValue",
            {
                "nodeId": node_id,
                "value": value,
            },
        )

    async def set_attribute_value(self, node_id: int, name: str, value: str) -> None:
        """Set an attribute value on a DOM node.

        Args:
            node_id: Node ID to modify.
            name: Attribute name.
            value: Attribute value.
        """
        await self.client.send_command(
            "DOM.setAttributeValue",
            {
                "nodeId": node_id,
                "name": name,
                "value": value,
            },
        )


class RuntimeDomain(CDPDomain):
    """Wrapper for the CDP Runtime domain.

    Provides methods for JavaScript execution and evaluation.

    Example:
        >>> runtime = RuntimeDomain(client)
        >>>
        >>> # Evaluate a simple expression
        >>> result = await runtime.evaluate("1 + 1")
        >>> print(result)  # 2
        >>>
        >>> # Evaluate with return value
        >>> title = await runtime.evaluate("document.title", return_by_value=True)
        >>> print(f"Title: {title}")
        >>>
        >>> # Execute a function
        >>> result = await runtime.evaluate("document.querySelector('h1').textContent")
    """

    @property
    def domain_name(self) -> str:
        return "Runtime"

    async def evaluate(
        self,
        expression: str,
        return_by_value: bool = False,
        await_promise: bool = False,
        context_id: int | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Evaluate a JavaScript expression.

        Args:
            expression: JavaScript expression to evaluate.
            return_by_value: Return the result as a JSON value (not object reference).
            await_promise: Wait for Promise to resolve.
            context_id: Optional execution context ID.
            timeout: Maximum time to wait for execution.

        Returns:
            Evaluation result (value, object, or exception details).

        Raises:
            CDPClientError: If evaluation fails or throws an exception.
        """
        params: dict[str, Any] = {
            "expression": expression,
            "returnByValue": return_by_value,
            "awaitPromise": await_promise,
            "includeCommandLineAPI": True,  # Enable console.* in evaluated code
        }

        if context_id is not None:
            params["contextId"] = context_id

        response = await self.client.send_command(
            "Runtime.evaluate", params, timeout=timeout
        )
        result = response.result or {}

        # Check for exception
        exception = result.get("exceptionDetails")
        if exception:
            description = exception.get("exception", {}).get(
                "description", exception.get("text", "Unknown error")
            )
            raise CDPClientError(f"JavaScript error: {description}")

        # Extract value from result
        remote_object = result.get("result", {})

        if return_by_value:
            return remote_object.get("value")

        # Return full remote object or its value description
        return remote_object.get("value") or remote_object.get("description")

    async def get_properties(self, object_id: str) -> dict[str, Any]:
        """Get properties of a remote object.

        Args:
            object_id: Remote object ID.

        Returns:
            Object properties as a dictionary.
        """
        response = await self.client.send_command(
            "Runtime.getProperties",
            {
                "objectId": object_id,
                "ownProperties": True,
            },
        )
        result = response.result or {}
        return result

    async def call_function_on(
        self,
        object_id: str,
        function_declaration: str,
        arguments: list[Any] | None = None,
        return_by_value: bool = True,
    ) -> Any:
        """Call a function on a remote object.

        Args:
            object_id: Remote object ID to call function on.
            function_declaration: Function declaration string.
            arguments: List of arguments to pass to the function.
            return_by_value: Return the result as a JSON value.

        Returns:
            Function result.
        """
        params: dict[str, Any] = {
            "objectId": object_id,
            "functionDeclaration": function_declaration,
            "returnByValue": return_by_value,
        }

        if arguments:
            params["arguments"] = arguments

        response = await self.client.send_command("Runtime.callFunctionOn", params)
        result = response.result or {}

        # Check for exception
        exception = result.get("exceptionDetails")
        if exception:
            description = exception.get("exception", {}).get(
                "description", exception.get("text", "Unknown error")
            )
            raise CDPClientError(f"Function call error: {description}")

        remote_object = result.get("result", {})
        return remote_object.get("value") if return_by_value else remote_object


class InputDomain(CDPDomain):
    """Wrapper for the CDP Input domain.

    Provides methods for simulating mouse and keyboard input.

    Example:
        >>> input_domain = InputDomain(client)
        >>>
        >>> # Click at coordinates
        >>> await input_domain.dispatch_mouse_event(
        ...     type="mousePressed",
        ...     x=100,
        ...     y=200,
        ...     button="left"
        ... )
        >>> await input_domain.dispatch_mouse_event(
        ...     type="mouseReleased",
        ...     x=100,
        ...     y=200,
        ...     button="left"
        ... )
        >>>
        >>> # Type text
        >>> await input_domain.dispatch_key_event("keyDown", key="H")
        >>> await input_domain.dispatch_key_event("keyUp", key="H")
    """

    @property
    def domain_name(self) -> str:
        return "Input"

    async def dispatch_mouse_event(
        self,
        type: str,
        x: float,
        y: float,
        button: str = "left",
        click_count: int = 1,
        delta_x: float = 0,
        delta_y: float = 0,
        modifiers: int = 0,
    ) -> None:
        """Dispatch a mouse event.

        Args:
            type: Event type ("mousePressed", "mouseReleased", "mouseMoved",
                "mouseWheel").
            x: X coordinate in CSS pixels.
            y: Y coordinate in CSS pixels.
            button: Mouse button ("left", "middle", "right", "back", "forward").
            click_count: Number of clicks (for double-click, etc.).
            delta_x: X delta for mouseWheel events.
            delta_y: Y delta for mouseWheel events.
            modifiers: Bitmask of modifier keys (Alt=1, Ctrl=2, Meta=4, Shift=8).
        """
        params: dict[str, Any] = {
            "type": type,
            "x": x,
            "y": y,
            "button": button,
            "clickCount": click_count,
            "modifiers": modifiers,
        }

        if type == "mouseWheel":
            params["deltaX"] = delta_x
            params["deltaY"] = delta_y

        await self.client.send_command("Input.dispatchMouseEvent", params)

    async def click(self, x: float, y: float, button: str = "left") -> None:
        """Perform a full click (press + release) at coordinates.

        Args:
            x: X coordinate in CSS pixels.
            y: Y coordinate in CSS pixels.
            button: Mouse button ("left", "middle", "right").
        """
        await self.dispatch_mouse_event("mousePressed", x, y, button, click_count=1)
        await self.dispatch_mouse_event("mouseReleased", x, y, button, click_count=1)

    async def move_mouse(self, x: float, y: float) -> None:
        """Move mouse to coordinates.

        Args:
            x: X coordinate in CSS pixels.
            y: Y coordinate in CSS pixels.
        """
        await self.dispatch_mouse_event("mouseMoved", x, y)

    async def scroll(self, x: float, y: float, delta_x: float, delta_y: float) -> None:
        """Scroll the page at the given coordinates.

        Args:
            x: X coordinate to scroll at.
            y: Y coordinate to scroll at.
            delta_x: Horizontal scroll amount.
            delta_y: Vertical scroll amount.
        """
        await self.dispatch_mouse_event(
            "mouseWheel", x, y, delta_x=delta_x, delta_y=delta_y
        )

    async def dispatch_key_event(
        self,
        type: str,
        key: str | None = None,
        code: str | None = None,
        text: str | None = None,
        modifiers: int = 0,
        auto_repeat: bool = False,
    ) -> None:
        """Dispatch a keyboard event.

        Args:
            type: Event type ("keyDown", "keyUp", "rawKeyDown", "char").
            key: Key string (e.g., "Enter", "Tab", "a", "1").
            code: Key code (e.g., "KeyA", "Digit1", "Enter").
            text: Text to input for "char" events.
            modifiers: Bitmask of modifier keys.
            auto_repeat: Whether this is an auto-repeat event.
        """
        params: dict[str, Any] = {
            "type": type,
            "modifiers": modifiers,
        }

        if key:
            params["key"] = key
        if code:
            params["code"] = code
        if text:
            params["text"] = text
        if auto_repeat:
            params["autoRepeat"] = auto_repeat

        await self.client.send_command("Input.dispatchKeyEvent", params)

    async def type_text(self, text: str) -> None:
        """Type a string of text.

        Args:
            text: Text to type.
        """
        for char in text:
            # Determine key and code
            key = char
            code = f"Key{char.upper()}" if char.isalpha() else None

            # KeyDown
            await self.dispatch_key_event("keyDown", key=key, code=code)
            # Char event with text
            await self.dispatch_key_event("char", text=char)
            # KeyUp
            await self.dispatch_key_event("keyUp", key=key, code=code)

    async def press_key(self, key: str, code: str | None = None) -> None:
        """Press a single key.

        Args:
            key: Key string (e.g., "Enter", "Tab", "ArrowDown").
            code: Optional key code.
        """
        if code is None:
            # Common mappings
            code_map = {
                "Enter": "Enter",
                "Tab": "Tab",
                "Escape": "Escape",
                "Backspace": "Backspace",
                "ArrowUp": "ArrowUp",
                "ArrowDown": "ArrowDown",
                "ArrowLeft": "ArrowLeft",
                "ArrowRight": "ArrowRight",
            }
            code = code_map.get(key)

        await self.dispatch_key_event("keyDown", key=key, code=code)
        await self.dispatch_key_event("keyUp", key=key, code=code)


class TargetDomain(CDPDomain):
    """Wrapper for the CDP Target domain.

    Provides methods for managing browser tabs and targets.

    Example:
        >>> target = TargetDomain(client)
        >>>
        >>> # Create a new tab
        >>> new_target = await target.create_target("https://example.com")
        >>> print(f"New tab ID: {new_target.get('targetId')}")
        >>>
        >>> # Get all targets
        >>> targets = await target.get_targets()
        >>> for t in targets:
        ...     print(f"Target: {t.get('title')} ({t.get('type')})")
        >>>
        >>> # Close a target
        >>> await target.close_target(new_target.get('targetId'))
    """

    @property
    def domain_name(self) -> str:
        return "Target"

    async def create_target(
        self,
        url: str | None = None,
        width: int | None = None,
        height: int | None = None,
        browser_context_id: str | None = None,
        enable_begin_frame_control: bool = False,
        new_window: bool = False,
        background: bool = False,
    ) -> dict[str, Any]:
        """Create a new browser tab/target.

        Args:
            url: Initial URL for the new tab.
            width: Window width in pixels.
            height: Window height in pixels.
            browser_context_id: Browser context ID for isolated session.
            enable_begin_frame_control: Enable begin frame control for headless.
            new_window: Open in a new window instead of tab.
            background: Open in background.

        Returns:
            New target information with 'targetId'.
        """
        params: dict[str, Any] = {}

        if url:
            params["url"] = url
        if width is not None:
            params["width"] = width
        if height is not None:
            params["height"] = height
        if browser_context_id:
            params["browserContextId"] = browser_context_id
        if enable_begin_frame_control:
            params["enableBeginFrameControl"] = enable_begin_frame_control
        if new_window:
            params["newWindow"] = new_window
        if background:
            params["background"] = background

        response = await self.client.send_command("Target.createTarget", params)
        return response.result or {}

    async def get_targets(self) -> list[dict[str, Any]]:
        """Get all active targets.

        Returns:
            List of target information dictionaries.
        """
        response = await self.client.send_command("Target.getTargets", {})
        result = response.result or {}
        return result.get("targetInfos", [])

    async def close_target(self, target_id: str) -> bool:
        """Close a target by ID.

        Args:
            target_id: Target ID to close.

        Returns:
            True if closed successfully, False otherwise.
        """
        try:
            response = await self.client.send_command(
                "Target.closeTarget",
                {
                    "targetId": target_id,
                },
            )
            result = response.result or {}
            success = result.get("success", False)
            if success:
                emit_info(f"Closed target: {target_id}")
            return success
        except CDPClientError as e:
            emit_warning(f"Failed to close target {target_id}: {e}")
            return False

    async def activate_target(self, target_id: str) -> None:
        """Activate (focus) a target.

        Args:
            target_id: Target ID to activate.
        """
        await self.client.send_command("Target.activateTarget", {"targetId": target_id})
        emit_info(f"Activated target: {target_id}")

    async def attach_to_target(
        self, target_id: str, flatten: bool = True
    ) -> dict[str, Any]:
        """Attach to a target for debugging.

        Args:
            target_id: Target ID to attach to.
            flatten: Use flat session ID access.

        Returns:
            Session information with 'sessionId'.
        """
        response = await self.client.send_command(
            "Target.attachToTarget",
            {
                "targetId": target_id,
                "flatten": flatten,
            },
        )
        return response.result or {}

    async def detach_from_target(self, session_id: str | None = None) -> None:
        """Detach from a target.

        Args:
            session_id: Session ID to detach. If None, detaches current session.
        """
        params: dict[str, Any] = {}
        if session_id:
            params["sessionId"] = session_id

        await self.client.send_command("Target.detachFromTarget", params)

    async def send_message_to_target(
        self, message: str, session_id: str | None = None, target_id: str | None = None
    ) -> None:
        """Send a protocol message to a target.

        Args:
            message: JSON message to send.
            session_id: Target session ID.
            target_id: Target ID (alternative to session_id).
        """
        params: dict[str, Any] = {"message": message}
        if session_id:
            params["sessionId"] = session_id
        if target_id:
            params["targetId"] = target_id

        await self.client.send_command("Target.sendMessageToTarget", params)


__all__ = [
    # Domain classes
    "PageDomain",
    "DOMDomain",
    "RuntimeDomain",
    "InputDomain",
    "TargetDomain",
    # Data classes
    "CDPNode",
    "CDPFrame",
]
