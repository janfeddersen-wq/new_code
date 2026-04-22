"""Shared pytest fixtures for plugin tests."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic_ai.models import ModelRequestParameters


# Workaround for pydantic/MCP compatibility issue during pytest collection
def pytest_configure(config):
    """Configure pytest with compatibility workarounds."""
    # Pre-patch sys.modules to provide a mock mcp.types during collection
    # This prevents the ValueError in pydantic's RootModel metaclass
    if "mcp" not in sys.modules:
        mcp_mock = MagicMock()
        mcp_mock.types = MagicMock()
        sys.modules["mcp"] = mcp_mock
        sys.modules["mcp.types"] = mcp_mock.types
        sys.modules["mcp.client"] = MagicMock()
        sys.modules["mcp.client.session"] = MagicMock()


class ClientShim:
    """A shim that makes client._api_client._async_httpx_client point to model._http_client."""

    def __init__(self, model):
        self._model = model
        self._api_client = ApiClientShim(model)


class ApiClientShim:
    """Inner shim for _api_client."""

    def __init__(self, model):
        self._model = model

    @property
    def _async_httpx_client(self):
        return self._model._http_client

    @_async_httpx_client.setter
    def _async_httpx_client(self, value):
        self._model._http_client = value


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Create a mock httpx client."""
    return AsyncMock()


@pytest.fixture
def model_request_params() -> ModelRequestParameters:
    """Create model request parameters fixture."""
    return ModelRequestParameters(
        function_tools=[],
    )
