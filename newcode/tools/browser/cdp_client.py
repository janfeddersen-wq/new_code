"""Chrome DevTools Protocol (CDP) WebSocket client.

This module provides a WebSocket client for communicating with Chrome/Chromium
via the Chrome DevTools Protocol (CDP). It supports JSON-RPC 2.0 messaging,
event subscriptions, auto-reconnection, and async context manager support.

Example:
    >>> async with CDPClient() as client:
    ...     await client.connect("localhost", 9222)
    ...     # Subscribe to page load events
    ...     client.on_event("Page.loadEventFired", on_page_load)
    ...     # Navigate to a URL
    ...     response = await client.send_command("Page.navigate", {"url": "https://example.com"})
    ...     print(f"Navigation result: {response}")

References:
    - CDP Documentation: https://chromedevtools.github.io/devtools-protocol/
    - JSON-RPC 2.0: https://www.jsonrpc.org/specification
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any, TypeVar

import httpx
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, InvalidURI

from newcode.messaging import emit_error, emit_info, emit_warning

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CDPCommand:
    """Represents a CDP command to be sent.

    Attributes:
        id: Unique command ID for matching responses.
        method: CDP method name (e.g., "Page.navigate").
        params: Method parameters as a dictionary.
    """

    id: int
    method: str
    params: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize command to JSON-RPC 2.0 format."""
        return json.dumps(
            {
                "id": self.id,
                "method": self.method,
                "params": self.params,
            },
            ensure_ascii=False,
        )


@dataclass
class CDPResponse:
    """Represents a CDP response received from the browser.

    Attributes:
        id: Command ID matching the request.
        result: Response result data (None if error).
        error: Error information (None if success).
    """

    id: int
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    @property
    def is_error(self) -> bool:
        """Check if the response contains an error."""
        return self.error is not None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CDPResponse:
        """Parse a CDP response from JSON data."""
        return cls(
            id=data.get("id", 0),
            result=data.get("result"),
            error=data.get("error"),
        )


@dataclass
class CDPEvent:
    """Represents a CDP event received from the browser.

    Attributes:
        method: Event method name (e.g., "Page.loadEventFired").
        params: Event parameters as a dictionary.
    """

    method: str
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CDPEvent:
        """Parse a CDP event from JSON data."""
        return cls(
            method=data.get("method", ""),
            params=data.get("params", {}),
        )


# Event callback type: function that receives event params
EventCallback = Callable[[dict[str, Any]], Coroutine[Any, Any, None] | None]


class CDPClientError(Exception):
    """Base exception for CDP client errors."""

    pass


class CDPConnectionError(CDPClientError):
    """Exception raised when connection to browser fails."""

    pass


class CDPCommandError(CDPClientError):
    """Exception raised when a CDP command returns an error."""

    def __init__(self, message: str, code: int | None = None, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data


class CDPClient:
    """WebSocket client for Chrome DevTools Protocol.

    This class manages WebSocket connections to Chrome/Chromium and provides
    methods for sending CDP commands and subscribing to CDP events.

    Example:
        >>> client = CDPClient()
        >>> await client.connect("localhost", 9222)
        >>> response = await client.send_command("Runtime.evaluate", {"expression": "1+1"})
        >>> print(response.result)  # {'result': {'type': 'number', 'value': 2, 'description': '2'}}
        >>> await client.disconnect()

    Attributes:
        host: Hostname or IP address of the browser.
        port: Remote debugging port (default 9222).
        ws_path: WebSocket endpoint path (default "/devtools/browser").
        auto_reconnect: Whether to auto-reconnect on disconnect.
        reconnect_delay: Delay in seconds between reconnection attempts.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9222,
        ws_path: str = "/devtools/browser",
        auto_reconnect: bool = True,
        reconnect_delay: float = 1.0,
    ):
        """Initialize the CDP client.

        Args:
            host: Hostname or IP address of the browser.
            port: Remote debugging port.
            ws_path: WebSocket endpoint path.
            auto_reconnect: Whether to auto-reconnect on disconnect.
            reconnect_delay: Delay in seconds between reconnection attempts.
        """
        self.host = host
        self.port = port
        self.ws_path = ws_path
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay

        self._ws: Any = None
        self._connected: bool = False
        self._command_id: int = 0
        self._pending_commands: dict[int, asyncio.Future[CDPResponse]] = {}
        self._event_listeners: dict[str, list[EventCallback]] = {}
        self._receive_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._shutdown_event: asyncio.Event = asyncio.Event()

    @property
    def is_connected(self) -> bool:
        """Check if the client is currently connected."""
        return self._connected and self._ws is not None

    def _get_ws_url(self) -> str:
        """Construct the WebSocket URL (fallback when discovery fails)."""
        return f"ws://{self.host}:{self.port}{self.ws_path}"

    async def _discover_ws_url(
        self, max_retries: int = 10, retry_delay: float = 0.5
    ) -> str:
        """Discover the WebSocket URL from Chrome's /json/list endpoint.

        This method queries Chrome's HTTP endpoint to get the actual WebSocket
        URL for a page target, rather than using hardcoded paths.

        Args:
            max_retries: Maximum number of attempts to discover the URL.
            retry_delay: Delay in seconds between retry attempts.

        Returns:
            The discovered WebSocket URL (e.g., "ws://localhost:9222/devtools/page/ABC123").

        Raises:
            CDPConnectionError: If discovery fails after all retries.
        """
        discovery_url = f"http://{self.host}:{self.port}/json/list"
        emit_info(f"Discovering WebSocket URL from {discovery_url}")

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(discovery_url, timeout=5.0)
                    response.raise_for_status()

                    targets = response.json()
                    logger.debug(f"Discovery response: {targets}")

                    if not isinstance(targets, list):
                        raise CDPConnectionError(
                            f"Invalid response from /json/list: expected list, got {type(targets).__name__}"
                        )

                    # Look for a page target (preferred) or browser target
                    page_target = None
                    browser_target = None

                    for target in targets:
                        target_type = target.get("type", "")
                        ws_url = target.get("webSocketDebuggerUrl", "")

                        if target_type == "page" and ws_url:
                            page_target = ws_url
                            break  # Prefer page targets
                        elif target_type == "browser" and ws_url:
                            browser_target = ws_url

                    # Use page target if found, otherwise fallback to browser target
                    discovered_url = page_target or browser_target

                    if discovered_url:
                        emit_info(f"Discovered WebSocket URL: {discovered_url}")
                        return discovered_url

                    raise CDPConnectionError(
                        "No suitable target found in /json/list response"
                    )

            except (
                httpx.ConnectError,
                httpx.NetworkError,
                ConnectionRefusedError,
                OSError,
            ) as e:
                if attempt < max_retries:
                    emit_info(
                        f"Discovery attempt {attempt}/{max_retries} failed (Chrome may not be ready yet): {e}"
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    emit_error(
                        f"Failed to discover WebSocket URL after {max_retries} attempts"
                    )
                    raise CDPConnectionError(
                        f"Failed to connect to Chrome at {self.host}:{self.port} after {max_retries} attempts: {e}"
                    ) from e

            except httpx.HTTPStatusError as e:
                emit_error(f"HTTP error during discovery: {e.response.status_code}")
                raise CDPConnectionError(
                    f"HTTP error from {discovery_url}: {e.response.status_code}"
                ) from e

            except json.JSONDecodeError as e:
                emit_error(f"Invalid JSON response from discovery endpoint: {e}")
                raise CDPConnectionError(
                    f"Invalid JSON response from {discovery_url}"
                ) from e

            except Exception as e:
                emit_error(f"Unexpected error during WebSocket URL discovery: {e}")
                raise CDPConnectionError(f"Discovery failed: {e}") from e

        # Should not reach here, but just in case
        raise CDPConnectionError("WebSocket URL discovery failed")

    async def connect(self, host: str | None = None, port: int | None = None) -> None:
        """Connect to Chrome/Chromium via WebSocket.

        This method dynamically discovers the WebSocket URL from Chrome's
        /json/list endpoint instead of using a hardcoded path.

        Args:
            host: Optional host to override the default.
            port: Optional port to override the default.

        Raises:
            CDPConnectionError: If connection or discovery fails.
        """
        if host:
            self.host = host
        if port:
            self.port = port

        # Discover the actual WebSocket URL dynamically
        try:
            ws_url = await self._discover_ws_url()
        except CDPConnectionError:
            # Fall back to hardcoded URL if discovery fails
            ws_url = self._get_ws_url()
            emit_warning(f"Discovery failed, falling back to hardcoded URL: {ws_url}")

        emit_info(f"Connecting to CDP at {ws_url}")

        try:
            self._ws = await connect(ws_url, ping_interval=20, ping_timeout=10)
            self._connected = True
            self._shutdown_event.clear()

            # Start the message receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            emit_info(f"Connected to CDP at {ws_url}")

        except (ConnectionRefusedError, OSError) as e:
            raise CDPConnectionError(f"Failed to connect to {ws_url}: {e}") from e
        except InvalidURI as e:
            raise CDPConnectionError(f"Invalid WebSocket URI: {ws_url}") from e

    async def disconnect(self) -> None:
        """Close the WebSocket connection gracefully."""
        if not self._connected or self._ws is None:
            return

        emit_info("Disconnecting from CDP")
        self._shutdown_event.set()

        # Cancel pending commands
        for future in self._pending_commands.values():
            if not future.done():
                future.cancel()
        self._pending_commands.clear()

        # Stop receive loop
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket
        try:
            await self._ws.close()
        except Exception:
            pass

        self._connected = False
        self._ws = None
        emit_info("Disconnected from CDP")

    async def __aenter__(self) -> CDPClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit - ensures cleanup."""
        await self.disconnect()

    def _next_command_id(self) -> int:
        """Generate the next unique command ID."""
        self._command_id += 1
        return self._command_id

    async def send_command(
        self, method: str, params: dict[str, Any] | None = None, timeout: float = 30.0
    ) -> CDPResponse:
        """Send a CDP command and wait for the response.

        Args:
            method: CDP method name (e.g., "Page.navigate").
            params: Method parameters as a dictionary.
            timeout: Maximum time to wait for response in seconds.

        Returns:
            CDPResponse object containing the result or error.

        Raises:
            CDPConnectionError: If not connected.
            CDPCommandError: If the command returns an error.
            asyncio.TimeoutError: If the response timeout is exceeded.

        Example:
            >>> response = await client.send_command("Page.navigate", {"url": "https://example.com"})
            >>> if response.is_error:
            ...     print(f"Error: {response.error}")
            ... else:
            ...     print(f"Frame ID: {response.result['frameId']}")
        """
        if not self._connected or self._ws is None:
            raise CDPConnectionError("Not connected to browser")

        cmd_id = self._next_command_id()
        command = CDPCommand(
            id=cmd_id,
            method=method,
            params=params or {},
        )

        # Create a future for the response
        future: asyncio.Future[CDPResponse] = asyncio.get_event_loop().create_future()
        self._pending_commands[cmd_id] = future

        try:
            # Send the command
            json_msg = command.to_json()
            logger.debug(f"Sending CDP command: {json_msg}")
            await self._ws.send(json_msg)

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)

            if response.is_error:
                error_data = response.error or {}
                raise CDPCommandError(
                    error_data.get("message", "Unknown CDP error"),
                    code=error_data.get("code"),
                    data=error_data.get("data"),
                )

            return response

        except asyncio.TimeoutError:
            # Remove the pending command on timeout
            self._pending_commands.pop(cmd_id, None)
            raise asyncio.TimeoutError(
                f"CDP command '{method}' timed out after {timeout}s"
            )

        except Exception:
            # Clean up pending command on any error
            self._pending_commands.pop(cmd_id, None)
            raise

    def on_event(self, event_name: str, callback: EventCallback) -> None:
        """Subscribe to a CDP event.

        Args:
            event_name: CDP event name (e.g., "Page.loadEventFired").
            callback: Async or sync callback function that receives event params.
                The callback should accept a single dict parameter.

        Example:
            >>> async def on_load(params: dict) -> None:
            ...     print(f"Page loaded: {params}")
            >>> client.on_event("Page.loadEventFired", on_load)
        """
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = []
        self._event_listeners[event_name].append(callback)
        emit_info(f"Subscribed to CDP event: {event_name}")

    def remove_event_listener(
        self, event_name: str, callback: EventCallback | None = None
    ) -> bool:
        """Unsubscribe from a CDP event.

        Args:
            event_name: CDP event name to unsubscribe from.
            callback: Specific callback to remove. If None, removes all
                listeners for the event.

        Returns:
            True if any listeners were removed, False otherwise.
        """
        if event_name not in self._event_listeners:
            return False

        if callback is None:
            # Remove all listeners for this event
            del self._event_listeners[event_name]
            emit_info(f"Removed all listeners for CDP event: {event_name}")
            return True

        # Remove specific callback
        listeners = self._event_listeners[event_name]
        if callback in listeners:
            listeners.remove(callback)
            if not listeners:
                del self._event_listeners[event_name]
            emit_info(f"Removed listener for CDP event: {event_name}")
            return True

        return False

    async def _receive_loop(self) -> None:
        """Main loop for receiving WebSocket messages."""
        while not self._shutdown_event.is_set() and self._connected and self._ws:
            try:
                message = await self._ws.recv()
                await self._handle_message(message)

            except ConnectionClosedOK:
                emit_info("CDP connection closed normally")
                break

            except ConnectionClosed as e:
                emit_warning(f"CDP connection closed unexpectedly: {e}")
                break

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.exception(f"Error in CDP receive loop: {e}")

        self._connected = False

        # Trigger auto-reconnect if enabled
        if self.auto_reconnect and not self._shutdown_event.is_set():
            self._reconnect_task = asyncio.create_task(self._attempt_reconnect())

    async def _handle_message(self, message: str | bytes) -> None:
        """Parse and handle a received WebSocket message."""
        try:
            if isinstance(message, bytes):
                message = message.decode("utf-8")

            data = json.loads(message)
            logger.debug(f"Received CDP message: {data}")

            # Check if it's a response (has 'id') or an event (has 'method')
            if "id" in data:
                # It's a command response
                await self._handle_response(data)
            elif "method" in data:
                # It's an event
                await self._handle_event(data)
            else:
                logger.warning(f"Unknown CDP message format: {data}")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse CDP message: {e}")

    async def _handle_response(self, data: dict[str, Any]) -> None:
        """Handle a command response message."""
        cmd_id = data.get("id", 0)
        response = CDPResponse.from_json(data)

        # Find and resolve the pending command
        future = self._pending_commands.pop(cmd_id, None)
        if future and not future.done():
            future.set_result(response)

    async def _handle_event(self, data: dict[str, Any]) -> None:
        """Handle an event message."""
        event = CDPEvent.from_json(data)
        listeners = self._event_listeners.get(event.method, [])

        if not listeners:
            return

        # Call all registered listeners
        for callback in listeners:
            try:
                result = callback(event.params)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.exception(f"Error in CDP event handler for {event.method}: {e}")

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect to the browser."""
        emit_info(f"Attempting to reconnect to CDP in {self.reconnect_delay}s...")
        await asyncio.sleep(self.reconnect_delay)

        try:
            await self.connect()
            emit_info("Successfully reconnected to CDP")
        except CDPConnectionError as e:
            emit_warning(f"Failed to reconnect: {e}")

    async def enable_domain(self, domain: str) -> CDPResponse:
        """Enable a CDP domain to start receiving its events.

        Args:
            domain: Domain name (e.g., "Page", "Runtime", "DOM").

        Returns:
            CDPResponse from the enable command.

        Example:
            >>> await client.enable_domain("Page")  # Enable Page events
            >>> await client.enable_domain("Runtime")  # Enable Runtime events
        """
        return await self.send_command(f"{domain}.enable", {})

    async def disable_domain(self, domain: str) -> CDPResponse:
        """Disable a CDP domain to stop receiving its events.

        Args:
            domain: Domain name (e.g., "Page", "Runtime", "DOM").

        Returns:
            CDPResponse from the disable command.
        """
        return await self.send_command(f"{domain}.disable", {})


__all__ = [
    "CDPClient",
    "CDPCommand",
    "CDPResponse",
    "CDPEvent",
    "CDPClientError",
    "CDPConnectionError",
    "CDPCommandError",
    "EventCallback",
]
