"""Base entity shared by all entities of one plant."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)

from .const import (
    CONF_DEVICE_LABEL,
    CONF_PLANT_NAME,
    CONF_STALE_HOURS,
    DEFAULT_STALE_HOURS,
    DOMAIN,
    METRICS,
    SIGNAL_PLANTBOOK_UPDATED,
)
from .status import SUN_ENTITY, _entry_value

# How often status entities re-check for sources that stopped reporting.
STALE_CHECK_INTERVAL = timedelta(minutes=5)


class DiyPlantBase(Entity):
    """Device info and source tracking for one plant."""

    _attr_has_entity_name = True
    # Set by entities whose state depends on limits, the sun and source age.
    _tracks_status = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.plant_name = _entry_value(entry, CONF_PLANT_NAME)
        self._source_ids = {
            metric: _entry_value(entry, spec["config"])
            for metric, spec in METRICS.items()
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Group all entities belonging to this plant."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.plant_name,
            manufacturer=_entry_value(self.entry, CONF_DEVICE_LABEL, "DIY Plants"),
            model="Flexible plant monitor",
        )

    async def async_added_to_hass(self) -> None:
        """Listen for source changes instead of waiting for a poll."""
        await super().async_added_to_hass()
        source_ids = [source for source in self._source_ids.values() if source]
        if source_ids:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, source_ids, self._source_changed
                )
            )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_PLANTBOOK_UPDATED.format(self.entry.entry_id),
                self.async_write_ha_state,
            )
        )
        if not self._tracks_status:
            return
        if self._source_ids["illuminance"]:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [SUN_ENTITY], self._source_changed
                )
            )
        if float(_entry_value(self.entry, CONF_STALE_HOURS, DEFAULT_STALE_HOURS)) > 0:
            # A source that stops reporting sends no event, so check on a timer.
            self.async_on_remove(
                async_track_time_interval(
                    self.hass, self._check_stale, STALE_CHECK_INTERVAL
                )
            )

    @callback
    def _source_changed(self, event: Event) -> None:
        """Refresh when a DIY source publishes a new value."""
        self.async_write_ha_state()

    @callback
    def _check_stale(self, _now) -> None:
        self.async_write_ha_state()
