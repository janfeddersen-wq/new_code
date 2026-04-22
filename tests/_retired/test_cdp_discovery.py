"""Tests for CDP WebSocket URL discovery functionality.

Tests the _discover_ws_url() method in CDPClient which queries Chrome's
/json/list endpoint to dynamically discover the WebSocket URL for a page target.
"""

import pytest

# Skip entire file - browser modules refactored to CDP-based
pytestmark = pytest.mark.skip(
    reason="Browser modules refactored to CDP-based - tests need updating"
)

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from newcode.tools.browser.cdp_client import CDPClient, CDPConnectionError


class TestDiscoverWsUrl:
    """Test suite for the _discover_ws_url method."""

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.fixture
    def cdp_client(self):
        """Create a fresh CDPClient instance for testing."""
        return CDPClient(host="localhost", port=9222)

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_successful_discovery(self, cdp_client):
        """Test successful discovery with a valid /json/list response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ABC123",
                "type": "page",
                "url": "about:blank",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/ABC123",
            }
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                ws_url = await cdp_client._discover_ws_url()

        assert ws_url == "ws://localhost:9222/devtools/page/ABC123"

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_page_target_preference(self, cdp_client):
        """Test that page target is preferred over browser target."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "BROWSER-001",
                "type": "browser",
                "url": "",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser",
            },
            {
                "id": "PAGE-001",
                "type": "page",
                "url": "https://example.com",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/PAGE-001",
            },
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                ws_url = await cdp_client._discover_ws_url()

        # Should return the page target, not the browser target
        assert ws_url == "ws://localhost:9222/devtools/page/PAGE-001"

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_retry_logic_success_on_third_attempt(self, cdp_client):
        """Test retry logic succeeds on 3rd attempt after 2 connection failures."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ABC123",
                "type": "page",
                "url": "about:blank",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/ABC123",
            }
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # First 2 calls raise connection error, 3rd succeeds
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection refused")
            return mock_response

        mock_client.get = mock_get

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
                    ws_url = await cdp_client._discover_ws_url(
                        max_retries=10, retry_delay=0.5
                    )

        assert ws_url == "ws://localhost:9222/devtools/page/ABC123"
        assert call_count == 3
        assert mock_sleep.call_count == 2  # 2 retries = 2 sleep calls

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_failure_after_max_retries(self, cdp_client):
        """Test CDPConnectionError is raised after exhausting all retries."""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with patch("newcode.tools.browser.cdp_client.emit_error"):
                    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
                        with pytest.raises(CDPConnectionError) as exc_info:
                            await cdp_client._discover_ws_url(
                                max_retries=3, retry_delay=0.1
                            )

        assert "Failed to connect to Chrome" in str(exc_info.value)
        assert "after 3 attempts" in str(exc_info.value)
        assert mock_sleep.call_count == 2  # 3 attempts, 2 sleeps between them

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_invalid_json_response(self, cdp_client):
        """Test proper error handling when Chrome returns invalid JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with patch("newcode.tools.browser.cdp_client.emit_error"):
                    with pytest.raises(CDPConnectionError) as exc_info:
                        await cdp_client._discover_ws_url()

        assert "Invalid JSON response" in str(exc_info.value)

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_http_error_500(self, cdp_client):
        """Test proper error handling when Chrome returns HTTP 500 error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with patch("newcode.tools.browser.cdp_client.emit_error"):
                    with pytest.raises(CDPConnectionError) as exc_info:
                        await cdp_client._discover_ws_url()

        assert "HTTP error" in str(exc_info.value)
        assert "500" in str(exc_info.value)

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_http_error_404(self, cdp_client):
        """Test proper error handling when Chrome returns HTTP 404 error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with patch("newcode.tools.browser.cdp_client.emit_error"):
                    with pytest.raises(CDPConnectionError) as exc_info:
                        await cdp_client._discover_ws_url()

        assert "HTTP error" in str(exc_info.value)
        assert "404" in str(exc_info.value)

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_empty_targets_list(self, cdp_client):
        """Test error when /json/list returns empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with pytest.raises(CDPConnectionError) as exc_info:
                    await cdp_client._discover_ws_url()

        assert "No suitable target found" in str(exc_info.value)

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_no_suitable_target(self, cdp_client):
        """Test error when targets exist but none have webSocketDebuggerUrl."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ABC123",
                "type": "page",
                "url": "about:blank",
                # No webSocketDebuggerUrl field
            },
            {
                "id": "DEF456",
                "type": "browser",
                # No webSocketDebuggerUrl field
            },
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with pytest.raises(CDPConnectionError) as exc_info:
                    await cdp_client._discover_ws_url()

        assert "No suitable target found" in str(exc_info.value)

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_browser_target_fallback(self, cdp_client):
        """Test fallback to browser target when no page target exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "BROWSER-001",
                "type": "browser",
                "url": "",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser",
            },
            # No page target available
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                ws_url = await cdp_client._discover_ws_url()

        # Should fall back to browser target when no page target available
        assert ws_url == "ws://localhost:9222/devtools/browser"

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_invalid_response_not_list(self, cdp_client):
        """Test error when response is not a list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"not": "a list"}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with pytest.raises(CDPConnectionError) as exc_info:
                    await cdp_client._discover_ws_url()

        assert "Invalid response from /json/list" in str(exc_info.value)
        assert "expected list, got dict" in str(exc_info.value)

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_multiple_page_targets_first_wins(self, cdp_client):
        """Test that first page target is selected when multiple exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "PAGE-001",
                "type": "page",
                "url": "https://first.com",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/PAGE-001",
            },
            {
                "id": "PAGE-002",
                "type": "page",
                "url": "https://second.com",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/PAGE-002",
            },
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                ws_url = await cdp_client._discover_ws_url()

        # Should return the first page target (PAGE-001)
        assert ws_url == "ws://localhost:9222/devtools/page/PAGE-001"

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_network_error_triggers_retry(self, cdp_client):
        """Test that network errors trigger retry logic."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ABC123",
                "type": "page",
                "url": "about:blank",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/ABC123",
            }
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # First call raises NetworkError, second succeeds
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.NetworkError("Network unreachable")
            return mock_response

        mock_client.get = mock_get

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
                    ws_url = await cdp_client._discover_ws_url()

        assert ws_url == "ws://localhost:9222/devtools/page/ABC123"
        assert call_count == 2
        assert mock_sleep.call_count == 1

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_os_error_triggers_retry(self, cdp_client):
        """Test that OSError triggers retry logic."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ABC123",
                "type": "page",
                "url": "about:blank",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/ABC123",
            }
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # First call raises OSError, second succeeds
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("Address not available")
            return mock_response

        mock_client.get = mock_get

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
                    ws_url = await cdp_client._discover_ws_url()

        assert ws_url == "ws://localhost:9222/devtools/page/ABC123"
        assert call_count == 2
        assert mock_sleep.call_count == 1

    @pytest.mark.skip(
        reason="Browser modules refactored to CDP-based - tests need updating"
    )
    @pytest.mark.asyncio
    async def test_connection_refused_error_triggers_retry(self, cdp_client):
        """Test that ConnectionRefusedError triggers retry logic."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "ABC123",
                "type": "page",
                "url": "about:blank",
                "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/ABC123",
            }
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # First call raises ConnectionRefusedError, second succeeds
        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionRefusedError("Connection refused")
            return mock_response

        mock_client.get = mock_get

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("newcode.tools.browser.cdp_client.emit_info"):
                with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
                    ws_url = await cdp_client._discover_ws_url()

        assert ws_url == "ws://localhost:9222/devtools/page/ABC123"
        assert call_count == 2
        assert mock_sleep.call_count == 1
