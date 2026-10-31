"""DIY-friendly plant monitoring for Home Assistant."""

import hashlib
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CARD_FILENAME, CARD_URL, DOMAIN, PLATFORMS

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_CARD_PATH = Path(__file__).parent / "frontend" / CARD_FILENAME


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the bundled Lovelace card and load it in the frontend."""
    digest = await hass.async_add_executor_job(_card_digest)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(_CARD_PATH), True)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={digest}")
    return True


def _card_digest() -> str:
    """Return a short content hash so browsers reload an updated card."""
    return hashlib.sha256(_CARD_PATH.read_bytes()).hexdigest()[:8]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a plant from a config entry."""
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the plant when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a plant config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
