"""Shared fixtures for DIY Plants tests."""

from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_frontend(hass: HomeAssistant) -> Mock:
    """Stand in for the http and frontend integrations the card relies on."""
    hass.config.components.update({"http", "frontend"})
    hass.http = Mock(async_register_static_paths=AsyncMock())
    hass.data[DATA_EXTRA_MODULE_URL] = set()
    return hass.http
