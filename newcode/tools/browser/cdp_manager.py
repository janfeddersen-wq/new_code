"""Chrome DevTools Protocol (CDP) Browser Manager.

This module manages Chrome/Chromium browser instances via CDP, including
process lifecycle, port detection, and connection management.

Example:
    >>> # Get or create a CDP manager for the current session
    >>> manager = get_cdp_manager("my-session")
    >>> await manager.launch()
    >>>
    >>> # Get the CDP client to send commands
    >>> client = manager.get_client()
    >>> await client.send_command("Page.navigate", {"url": "https://example.com"})
    >>>
    >>> # Clean up when done
    >>> await manager.close()

Features:
    - Auto-detection of available debugging port
    - Headless or visible browser modes
    - Per-session browser instances
    - Automatic cleanup on exit
    - Chrome/Chromium executable auto-detection
"""

from __future__ import annotations

import asyncio
import atexit
import contextvars
import os
import signal
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from newcode.config import get_browser_chrome_path, get_browser_headless
from newcode.messaging import emit_info, emit_success, emit_warning

from .cdp_client import CDPClient, CDPClientError
from .chrome_detector import detect_chrome_executable

# Store active manager instances by session ID
_active_managers: dict[str, "CDPManager"] = {}

# Context variable for CDP browser session
_cdp_session_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "cdp_session", default=None
)

# Flag to track if cleanup has already run
_cleanup_done: bool = False

# Default CDP settings
DEFAULT_CDP_PORT: int = 9222
MAX_PORT_ATTEMPTS: int = 100


def set_cdp_session(session_id: str | None) -> contextvars.Token:
    """Set the CDP browser session ID for the current context.

    This must be called BEFORE any tool calls that use the CDP browser.

    Args:
        session_id: The session ID to use for CDP browser operations.

    Returns:
        A token that can be used to reset the context.
    """
    return _cdp_session_var.set(session_id)


def get_cdp_session() -> str | None:
    """Get the CDP browser session ID for the current context.

    Returns:
        The current session ID, or None if not set.
    """
    return _cdp_session_var.get()


def find_available_port(
    start_port: int = DEFAULT_CDP_PORT, max_attempts: int = MAX_PORT_ATTEMPTS
) -> int:
    """Find an available TCP port starting from start_port.

    Args:
        start_port: The starting port number to check.
        max_attempts: Maximum number of ports to try.

    Returns:
        An available port number.

    Raises:
        RuntimeError: If no available port is found.
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue

    raise RuntimeError(
        f"No available port found in range {start_port}-{start_port + max_attempts - 1}"
    )


class CDPManager:
    """Manager for Chrome/Chromium browser via CDP.

    This class handles launching Chrome with remote debugging enabled,
    managing the browser process lifecycle, and providing access to the
    CDP client for sending commands.

    Attributes:
        session_id: Unique identifier for this browser session.
        host: Host where the browser is running (default "localhost").
        port: Remote debugging port (auto-detected if not specified).
        headless: Whether to run in headless mode.
        chrome_path: Path to Chrome/Chromium executable.
        auto_cleanup: Whether to auto-cleanup on exit.

    Example:
        >>> manager = CDPManager(session_id="test-session")
        >>> await manager.launch()
        >>> client = manager.get_client()
        >>> await client.send_command("Page.navigate", {"url": "https://example.com"})
        >>> await manager.close()
    """

    def __init__(
        self,
        session_id: str | None = None,
        host: str = "localhost",
        port: int | None = None,
        headless: bool | None = None,
        chrome_path: str | None = None,
        auto_cleanup: bool = True,
    ):
        """Initialize the CDP manager.

        Args:
            session_id: Unique session identifier. If None, uses "default".
            host: Host for the CDP connection.
            port: Remote debugging port. If None, auto-detects available port.
            headless: Whether to run in headless mode. If None, uses config default.
            chrome_path: Path to Chrome executable. If None, auto-detects.
            auto_cleanup: Whether to register atexit cleanup handler.
        """
        self.session_id = session_id or "default"
        self.host = host
        self.port = port or find_available_port()
        self.auto_cleanup = auto_cleanup

        # Determine headless mode
        if headless is not None:
            self.headless = headless
        else:
            env_headless = os.getenv("BROWSER_HEADLESS")
            if env_headless is not None:
                self.headless = env_headless.lower() != "false"
            else:
                self.headless = get_browser_headless()

        # Determine Chrome path
        if chrome_path:
            self.chrome_path = chrome_path
        else:
            custom_path = get_browser_chrome_path()
            self.chrome_path = custom_path or detect_chrome_executable() or "chrome"

        # Internal state
        self._process: subprocess.Popen | None = None
        self._client: CDPClient | None = None
        self._initialized: bool = False
        self._profile_dir: Path | None = None
        self._targets: dict[str, Any] = {}

        # Register cleanup handler
        if auto_cleanup:
            atexit.register(self._sync_cleanup)

    def _get_profile_directory(self) -> Path:
        """Get or create the profile directory for this session.

        Returns:
            Path to the profile directory.
        """
        if self._profile_dir is None:
            from newcode import config

            cache_dir = Path(config.CACHE_DIR)
            profiles_base = cache_dir / "cdp_profiles"
            self._profile_dir = profiles_base / self.session_id
            self._profile_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        return self._profile_dir

    def _build_chrome_args(self) -> list[str]:
        """Build the Chrome command-line arguments.

        Returns:
            List of command-line arguments for Chrome.
        """
        args = [
            self.chrome_path,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self._get_profile_directory()}",
            # Security and stability flags
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-breakpad",
            "--disable-component-update",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-dev-shm-usage",  # Overcome limited resource problems
            "--disable-gpu",  # Applicable to windows os only
            "--disable-popup-blocking",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--force-color-profile=srgb",
            "--metrics-recording-only",
            "--safebrowsing-disable-auto-update",
            "--enable-automation",
            "--password-store=basic",
            "--use-mock-keychain",
            "--hide-scrollbars",  # Hide scrollbar for consistent screenshots
            "--mute-audio",  # Mute audio
            "--window-size=1920,1080",  # Set default window size
        ]

        # Headless mode
        if self.headless:
            args.append("--headless=new")  # New headless mode

        # Additional args from environment
        extra_args = os.getenv("BROWSER_EXTRA_ARGS", "")
        if extra_args:
            args.extend(extra_args.split())

        return args

    async def launch(self) -> None:
        """Launch Chrome with remote debugging enabled.

        Raises:
            CDPClientError: If Chrome is not found or fails to start.
            RuntimeError: If the debugging port cannot be verified.
        """
        if self._initialized:
            return

        emit_info(
            f"Launching Chrome for session '{self.session_id}' on port {self.port}"
        )

        # Verify Chrome exists
        if not self.chrome_path or not (
            Path(self.chrome_path).exists() or self._is_in_path(self.chrome_path)
        ):
            raise CDPClientError(f"Chrome executable not found: {self.chrome_path}")

        # Build command args
        args = self._build_chrome_args()

        try:
            # Launch Chrome process
            if sys.platform == "win32":
                # Windows: CREATE_NEW_PROCESS_GROUP for proper signal handling
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
                self._process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=creationflags,
                )
            else:
                # Unix: start_new_session to create new process group
                self._process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )

            emit_info(f"Chrome started with PID {self._process.pid}")

            # Wait for Chrome to start and verify debugging port
            await self._wait_for_chrome()

            # Create and connect CDP client
            self._client = CDPClient(host=self.host, port=self.port)
            await self._client.connect()

            self._initialized = True
            emit_success(
                f"Chrome ready for session '{self.session_id}' (CDP port {self.port})"
            )

        except Exception as e:
            await self.close()
            raise CDPClientError(f"Failed to launch Chrome: {e}") from e

    def _is_in_path(self, executable: str) -> bool:
        """Check if an executable is in the system PATH."""
        import shutil

        return shutil.which(executable) is not None

    async def _wait_for_chrome(
        self, timeout: float = 30.0, poll_interval: float = 0.5
    ) -> None:
        """Wait for Chrome to start and the debugging port to become available.

        Args:
            timeout: Maximum time to wait in seconds.
            poll_interval: Time between polling attempts in seconds.

        Raises:
            RuntimeError: If Chrome does not start within the timeout.
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if process is still running
            if self._process is None or self._process.poll() is not None:
                raise RuntimeError("Chrome process exited unexpectedly")

            # Try to connect to the debugging port
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1.0)
                    result = sock.connect_ex((self.host, self.port))
                    if result == 0:
                        # Port is open, wait a bit more for CDP to be fully ready
                        await asyncio.sleep(0.5)
                        return
            except Exception:
                pass

            await asyncio.sleep(poll_interval)

        raise RuntimeError(
            f"Chrome debugging port did not become available within {timeout}s"
        )

    def get_client(self) -> CDPClient:
        """Get the CDP client for sending commands.

        Returns:
            The CDPClient instance.

        Raises:
            CDPClientError: If the browser is not initialized.
        """
        if not self._initialized or self._client is None:
            raise CDPClientError("Browser not initialized. Call launch() first.")
        return self._client

    async def close(self) -> None:
        """Close the browser and clean up resources."""
        if not self._initialized and self._process is None:
            return

        emit_info(f"Closing Chrome for session '{self.session_id}'")

        # Disconnect CDP client
        if self._client:
            try:
                await self._client.disconnect()
            except Exception as e:
                emit_warning(f"Error disconnecting CDP client: {e}")
            self._client = None

        # Terminate Chrome process
        if self._process:
            await self._terminate_process()
            self._process = None

        self._initialized = False
        emit_success(f"Chrome closed for session '{self.session_id}'")

    async def _terminate_process(self) -> None:
        """Terminate the Chrome process gracefully."""
        if self._process is None:
            return

        try:
            # Try graceful termination first
            if sys.platform == "win32":
                # Windows: send CTRL_BREAK_EVENT to process group
                try:
                    self._process.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
                except Exception:
                    pass
            else:
                # Unix: send SIGTERM to process group
                try:
                    os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass

            # Wait for graceful shutdown
            try:
                self._process.wait(timeout=5.0)
                return
            except subprocess.TimeoutExpired:
                pass

            # Force kill if graceful termination failed
            emit_warning(f"Force killing Chrome process {self._process.pid}")
            self._process.kill()
            self._process.wait(timeout=2.0)

        except ProcessLookupError:
            # Process already gone
            pass
        except Exception as e:
            emit_warning(f"Error terminating Chrome process: {e}")

    def _sync_cleanup(self) -> None:
        """Synchronous cleanup for atexit handler."""
        if not self._initialized or self._process is None:
            return

        try:
            # Try to get running loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.close())
                return
            except RuntimeError:
                pass  # No running loop

            # Create new event loop for cleanup
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.close())
            finally:
                loop.close()
        except Exception:
            # Silently swallow errors during exit
            pass

    async def create_new_page(self, url: str | None = None) -> dict[str, Any]:
        """Create a new browser page/tab via CDP.

        Args:
            url: Optional URL to navigate to in the new page.

        Returns:
            Target information dictionary with 'targetId'.

        Raises:
            CDPClientError: If the browser is not initialized.
        """
        client = self.get_client()

        params: dict[str, Any] = {}
        if url:
            params["url"] = url

        response = await client.send_command("Target.createTarget", params)
        target_info = response.result or {}

        if "targetId" in target_info:
            self._targets[target_info["targetId"]] = target_info

        return target_info

    async def get_targets(self) -> list[dict[str, Any]]:
        """Get all active browser targets (pages).

        Returns:
            List of target information dictionaries.

        Raises:
            CDPClientError: If the browser is not initialized.
        """
        client = self.get_client()
        response = await client.send_command("Target.getTargets", {})
        result = response.result or {}
        return result.get("targetInfos", [])

    async def close_target(self, target_id: str) -> bool:
        """Close a specific browser target.

        Args:
            target_id: The target ID to close.

        Returns:
            True if closed successfully, False otherwise.
        """
        client = self.get_client()

        try:
            await client.send_command("Target.closeTarget", {"targetId": target_id})
            self._targets.pop(target_id, None)
            return True
        except CDPClientError as e:
            emit_warning(f"Failed to close target {target_id}: {e}")
            return False


def get_cdp_manager(
    session_id: str | None = None,
    host: str = "localhost",
    port: int | None = None,
    headless: bool | None = None,
    chrome_path: str | None = None,
) -> CDPManager:
    """Get or create a CDPManager instance.

    This is the preferred way to get a CDP manager. It returns an existing
    manager for the session if one exists, or creates a new one.

    Args:
        session_id: Optional session ID. If provided and a manager with this
            session exists, returns that manager. Otherwise creates a new one.
            If None, uses the context session or 'default'.
        host: Host for the CDP connection (for new managers).
        port: Remote debugging port (for new managers, auto-detected if None).
        headless: Whether to run headless (for new managers).
        chrome_path: Path to Chrome executable (for new managers).

    Returns:
        A CDPManager instance.

    Example:
        >>> # Default session
        >>> manager = get_cdp_manager()
        >>>
        >>> # Named session
        >>> manager = get_cdp_manager("qa-agent-1")
        >>>
        >>> # With specific options
        >>> manager = get_cdp_manager("headless-session", headless=True)
    """
    # Get session from context if not provided
    if session_id is None:
        session_id = get_cdp_session() or "default"

    if session_id not in _active_managers:
        _active_managers[session_id] = CDPManager(
            session_id=session_id,
            host=host,
            port=port,
            headless=headless,
            chrome_path=chrome_path,
        )

    return _active_managers[session_id]


def get_session_cdp_manager() -> CDPManager:
    """Get the CDPManager for the current context's session.

    This is the preferred way to get a CDP manager in tool functions,
    as it automatically uses the correct session ID for the current
    agent context.

    Returns:
        A CDPManager instance for the current session.
    """
    session_id = get_cdp_session()
    return get_cdp_manager(session_id)


async def cleanup_all_cdp_browsers() -> None:
    """Close all active CDP browser manager instances.

    This should be called before application exit to ensure all browser
    connections are properly closed.
    """
    global _cleanup_done

    if _cleanup_done:
        return

    _cleanup_done = True

    # Copy keys since we'll modify dict during cleanup
    session_ids = list(_active_managers.keys())

    for session_id in session_ids:
        manager = _active_managers.get(session_id)
        if manager and manager._initialized:
            try:
                await manager.close()
            except Exception:
                pass  # Ignore errors during cleanup


def _sync_cleanup_all() -> None:
    """Synchronous cleanup wrapper for atexit."""
    global _cleanup_done

    if _cleanup_done or not _active_managers:
        return

    try:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(cleanup_all_cdp_browsers())
            return
        except RuntimeError:
            pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(cleanup_all_cdp_browsers())
        finally:
            loop.close()
    except Exception:
        pass


# Register global cleanup handler
atexit.register(_sync_cleanup_all)


__all__ = [
    "CDPManager",
    "get_cdp_manager",
    "get_session_cdp_manager",
    "set_cdp_session",
    "get_cdp_session",
    "cleanup_all_cdp_browsers",
    "find_available_port",
]
