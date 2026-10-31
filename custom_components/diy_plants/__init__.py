"""DIY-friendly plant monitoring for Home Assistant."""

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CARD_FILENAME, CARD_URL, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_CARD_PATH = Path(__file__).parent / "frontend" / CARD_FILENAME


@dataclass
class DiyPlantData:
    """State shared between one plant's entities."""

    plantbook: dict[str, Any] = field(default_factory=dict)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the bundled Lovelace card and load it on every dashboard."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(_CARD_PATH), cache_headers=False)]
    )
    versioned_url = f"{CARD_URL}?v={await hass.async_add_executor_job(_card_digest)}"
    # frontend is an after_dependency: always there in a normal install, absent in tests.
    if "frontend" in hass.config.components:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, versioned_url)
    else:
        _LOGGER.debug("frontend not loaded; card served at %s but not auto-loaded", CARD_URL)
    # The extra module URL is not picked up by every frontend, so also keep a
    # dashboard resource for the card.
    await _async_ensure_card_resource(hass, versioned_url)
    return True


async def _async_ensure_card_resource(hass: HomeAssistant, url: str) -> None:
    """Add or update the card's dashboard resource when dashboards use storage mode."""
    lovelace = hass.data.get("lovelace")
    if isinstance(lovelace, dict):
        mode = lovelace.get("resource_mode", lovelace.get("mode"))
        resources = lovelace.get("resources")
    else:
        mode = getattr(lovelace, "resource_mode", None)
        resources = getattr(lovelace, "resources", None)
    if mode != "storage" or resources is None:
        _LOGGER.debug("Dashboard resources are not in storage mode; add %s manually", CARD_URL)
        return

    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True
    for item in resources.async_items():
        if item.get("url", "").split("?")[0] == CARD_URL:
            if item["url"] != url:
                await resources.async_update_item(
                    item["id"], {"res_type": "module", "url": url}
                )
            return
    await resources.async_create_item({"res_type": "module", "url": url})
    _LOGGER.info("Added dashboard resource %s", url)


def _card_digest() -> str:
    """Return a short content hash so browsers reload an updated card."""
    return hashlib.sha256(_CARD_PATH.read_bytes()).hexdigest()[:8]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a plant from a config entry."""
    entry.runtime_data = DiyPlantData()
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the plant when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a plant config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
