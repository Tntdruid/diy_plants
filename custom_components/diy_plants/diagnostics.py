"""Diagnostics support for DIY Plants."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_PLANTBOOK_API_KEY,
    CONF_PLANTBOOK_CLIENT_ID,
    CONF_PLANTBOOK_CLIENT_SECRET,
    METRICS,
)

TO_REDACT = {
    CONF_PLANTBOOK_API_KEY,
    CONF_PLANTBOOK_CLIENT_ID,
    CONF_PLANTBOOK_CLIENT_SECRET,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return the plant configuration and the current source sensor states."""
    config = {**entry.data, **entry.options}
    sources: dict[str, Any] = {}
    for metric, spec in METRICS.items():
        entity_id = config.get(spec["config"])
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        sources[metric] = {
            "entity_id": entity_id,
            "state": state.state if state else None,
            "attributes": dict(state.attributes) if state else None,
        }
    return {
        "data": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "sources": sources,
    }
