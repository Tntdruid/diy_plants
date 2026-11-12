"""Sensor entities for DIY Plants."""

from __future__ import annotations

import re
import logging
from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_SERVICE_REGISTERED,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PLANTBOOK_ENABLED,
    CONF_PLANTBOOK_PLANT_ID,
    CONF_PLANTBOOK_PLANT_NAME,
    DEFAULT_LUX_TO_PPFD,
    METRICS,
    SIGNAL_PLANTBOOK_UPDATED,
)
from .entity import DiyPlantBase
from .status import (
    STATUS_OK,
    STATUS_STALE,
    STATUS_UNAVAILABLE,
    _entry_value,
    _number,
    _value,
    evaluate,
    limits,
)

_LOGGER = logging.getLogger(__name__)

_OPENPLANTBOOK = "openplantbook"

HEALTH_OK = "ok"
HEALTH_ATTENTION = "attention"
HEALTH_SENSOR_UNAVAILABLE = "sensor_unavailable"
HEALTH_SENSOR_STALE = "sensor_stale"
HEALTH_NO_SENSORS = "no_sensors"
HEALTH_STATES = [
    HEALTH_OK,
    HEALTH_ATTENTION,
    HEALTH_SENSOR_UNAVAILABLE,
    HEALTH_SENSOR_STALE,
    HEALTH_NO_SENSORS,
]

PLANTBOOK_NO_PLANT = "no_plant_configured"
PLANTBOOK_WAITING = "waiting_for_openplantbook"
PLANTBOOK_LOOKING_UP = "looking_up"
PLANTBOOK_FOUND = "found"
PLANTBOOK_NOT_FOUND = "not_found"
PLANTBOOK_ERROR = "error"


class DiyPlantEntity(DiyPlantBase, SensorEntity):
    """Common sensor behavior for one plant."""


class DiyPlantMetricSensor(DiyPlantEntity):
    """Expose a normalized source value and diagnostics."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, metric: str) -> None:
        super().__init__(hass, entry)
        self.metric = metric
        spec = METRICS[metric]
        self._attr_translation_key = metric
        self._attr_unique_id = f"{entry.entry_id}-{metric}"
        self._attr_native_unit_of_measurement = spec["unit"]
        self._attr_device_class = spec["device_class"]
        self._attr_state_class = spec["state_class"]
        self._attr_suggested_display_precision = spec["precision"]

    @property
    def native_value(self) -> float | None:
        """Return the normalized value."""
        value, _, _ = _value(
            self.hass, self._source_ids[self.metric], self.metric, self.entry
        )
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose source and parsing information for troubleshooting."""
        source = self._source_ids[self.metric]
        value, raw, error = _value(self.hass, source, self.metric, self.entry)
        minimum, maximum, limit_source = limits(self.entry, self.metric)
        return {
            "source_entity": source,
            "raw_state": raw,
            "normalized_value": value,
            "minimum": minimum,
            "maximum": maximum,
            "limit_source": limit_source,
            "error": error,
            "calibration_enabled": _entry_value(
                self.entry, f"{self.metric}_calibration_enabled", False
            ),
        }


class DiyPlantDliSensor(DiyPlantEntity, RestoreSensor):
    """Calculate daily light integral from the configured illuminance sensor."""

    _attr_translation_key = "dli"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        spec = METRICS["dli"]
        self._attr_unique_id = f"{entry.entry_id}-dli"
        self._attr_native_unit_of_measurement = spec["unit"]
        self._attr_state_class = spec["state_class"]
        self._attr_suggested_display_precision = spec["precision"]
        self._daily_dli = 0.0
        self._last_lux: float | None = None
        self._last_timestamp = None
        self._day = None

    @property
    def native_value(self) -> float | None:
        """Return the accumulated DLI for the current calendar day."""
        return self._daily_dli

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the source and conversion used for the calculation."""
        return {
            "source_entity": self._source_ids["illuminance"],
            "lux_to_ppfd_factor": DEFAULT_LUX_TO_PPFD,
            "daily_reset": "midnight",
        }

    async def async_added_to_hass(self) -> None:
        """Restore the accumulated value and track source/midnight updates."""
        await super().async_added_to_hass()
        self._day = dt_util.now().date()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                if dt_util.as_local(last_state.last_updated).date() == self._day:
                    self._daily_dli = float(last_state.state)
            except (AttributeError, TypeError, ValueError):
                self._daily_dli = 0.0

        source = self._source_ids["illuminance"]
        if source:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [source], self._illuminance_changed
                )
            )
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._reset_at_midnight, hour=0, minute=0, second=0
            )
        )
        self._update_from_source()

    @callback
    def _illuminance_changed(self, event: Event) -> None:
        """Integrate the new illuminance reading."""
        self._update_from_source()
        self.async_write_ha_state()

    @callback
    def _reset_at_midnight(self, _now) -> None:
        """Reset the daily accumulator when the calendar day changes."""
        today = dt_util.now().date()
        if today != self._day:
            self._daily_dli = 0.0
            self._last_lux = None
            self._last_timestamp = None
            self._day = today
            self.async_write_ha_state()

    def _update_from_source(self) -> None:
        """Add the trapezoidal PPFD integral since the previous update."""
        source = self._source_ids["illuminance"]
        state = self.hass.states.get(source) if source else None
        if state is None:
            return
        lux = _number(state.state)
        if lux is None:
            return

        now = state.last_updated
        local_date = dt_util.as_local(now).date()
        if self._day is not None and local_date < self._day:
            return
        if self._day != local_date:
            self._daily_dli = 0.0
            self._last_lux = None
            self._day = local_date
        if self._last_lux is not None and self._last_timestamp is not None:
            elapsed = (now - self._last_timestamp).total_seconds()
            if elapsed > 0:
                average_lux = (self._last_lux + lux) / 2
                self._daily_dli += (
                    average_lux * DEFAULT_LUX_TO_PPFD / 1_000_000 * elapsed
                )
        self._last_lux = lux
        self._last_timestamp = now


class DiyPlantHealthSensor(DiyPlantEntity):
    """Report whether configured measurements are within their limits."""

    _attr_translation_key = "health"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = HEALTH_STATES
    _tracks_status = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._plantbook_info: dict[str, Any] = {}
        self._plantbook_status: str | None = None
        self._attr_unique_id = f"{entry.entry_id}-health"

    async def async_added_to_hass(self) -> None:
        """Look up Plantbook data once OpenPlantbook is available."""
        await super().async_added_to_hass()
        if not _entry_value(self.entry, CONF_PLANTBOOK_ENABLED, False):
            return
        if not _plantbook_query(self.entry):
            self._plantbook_status = PLANTBOOK_NO_PLANT
            return
        if self.hass.services.has_service(_OPENPLANTBOOK, "get"):
            self._start_plantbook_lookup()
            return
        # OpenPlantbook may load after DIY Plants during startup.
        self._plantbook_status = PLANTBOOK_WAITING
        self._unsub_plantbook_wait = self.hass.bus.async_listen(
            EVENT_SERVICE_REGISTERED,
            self._openplantbook_registered,
            event_filter=_is_openplantbook_get,
        )
        self.async_on_remove(self._cancel_plantbook_wait)

    @callback
    def _openplantbook_registered(self, event: Event) -> None:
        """Look up the plant once OpenPlantbook's get service exists."""
        self._cancel_plantbook_wait()
        self._start_plantbook_lookup()

    @callback
    def _cancel_plantbook_wait(self) -> None:
        if unsub := getattr(self, "_unsub_plantbook_wait", None):
            unsub()
            self._unsub_plantbook_wait = None

    @callback
    def _start_plantbook_lookup(self) -> None:
        self._plantbook_status = PLANTBOOK_LOOKING_UP
        self.entry.async_create_background_task(
            self.hass, self._async_plantbook_lookup(), "diy_plants_plantbook_lookup"
        )

    async def _async_plantbook_lookup(self) -> None:
        """Fetch Plantbook data and expose the image and species."""
        self._plantbook_info, self._plantbook_status = await _fetch_plantbook_info(
            self.hass, _plantbook_query(self.entry)
        )
        self._attr_entity_picture = _plantbook_image(self._plantbook_info)
        _set_plantbook_data(self.entry, self._plantbook_info)
        self.async_write_ha_state()
        async_dispatcher_send(
            self.hass, SIGNAL_PLANTBOOK_UPDATED.format(self.entry.entry_id)
        )

    @property
    def native_value(self) -> str:
        """Return the most important problem, or ok."""
        statuses = {info["status"] for info in evaluate(self.hass, self.entry).values()}
        if not statuses:
            return HEALTH_NO_SENSORS
        if STATUS_UNAVAILABLE in statuses:
            return HEALTH_SENSOR_UNAVAILABLE
        if STATUS_STALE in statuses:
            return HEALTH_SENSOR_STALE
        if statuses != {STATUS_OK}:
            return HEALTH_ATTENTION
        return HEALTH_OK

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return a compact status report for dashboards and automations."""
        attributes: dict[str, Any] = {"measurements": evaluate(self.hass, self.entry)}
        if self._plantbook_status:
            attributes["plantbook_status"] = self._plantbook_status
        if pid := self._plantbook_info.get("pid"):
            attributes["plantbook_pid"] = pid
        if self._attr_entity_picture:
            attributes["plantbook_image"] = self._attr_entity_picture
        species = _plantbook_species(self._plantbook_info)
        if species:
            attributes["plantbook_species"] = species
        return attributes


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up plant sensor entities."""
    illuminance_entity = _entry_value(entry, METRICS["illuminance"]["config"])
    entities: list[SensorEntity] = [DiyPlantHealthSensor(hass, entry)]
    entities.extend(
        DiyPlantMetricSensor(hass, entry, metric)
        for metric, spec in METRICS.items()
        if metric != "dli" and _entry_value(entry, spec["config"])
    )
    if illuminance_entity:
        entities.append(DiyPlantDliSensor(hass, entry))
    async_add_entities(entities)


def _set_plantbook_data(entry: ConfigEntry, plant: dict[str, Any]) -> None:
    if (runtime := getattr(entry, "runtime_data", None)) is not None:
        runtime.plantbook = plant


def _plantbook_query(entry: ConfigEntry) -> str:
    """Return the Plantbook plant ID, falling back to the plant name."""
    for key in (CONF_PLANTBOOK_PLANT_ID, CONF_PLANTBOOK_PLANT_NAME):
        value = str(_entry_value(entry, key, "") or "").strip()
        if value:
            return value
    return ""


@callback
def _is_openplantbook_get(event_data: Mapping[str, Any]) -> bool:
    return event_data.get("domain") == _OPENPLANTBOOK and event_data.get("service") == "get"


async def _openplantbook_call(
    hass: HomeAssistant, service: str, data: dict[str, Any]
) -> dict[str, Any]:
    response = await hass.services.async_call(
        _OPENPLANTBOOK, service, data, blocking=True, return_response=True
    )
    return response if isinstance(response, dict) else {}


async def _fetch_plantbook_info(
    hass: HomeAssistant, query: str
) -> tuple[dict[str, Any], str]:
    """Look up a plant by pid, or search for it by name when that fails."""
    try:
        plant = await _openplantbook_call(
            hass, "get", {"species": query.lower(), "include": "care"}
        )
        if not plant.get("pid"):
            matches = await _openplantbook_call(hass, "search", {"alias": query})
            if matches:
                pid = next(iter(matches))
                plant = await _openplantbook_call(
                    hass, "get", {"species": pid, "include": "care"}
                )
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Plantbook lookup for %s failed: %s", query, err)
        return {}, PLANTBOOK_ERROR
    if not plant.get("pid"):
        _LOGGER.warning("Plantbook has no plant matching %s", query)
        return {}, PLANTBOOK_NOT_FOUND
    return plant, PLANTBOOK_FOUND


def _nested_string_value(value: Any, keys: tuple[str, ...]) -> str | None:
    """Recursively find the first string-valued match for any of the given keys."""
    normalized = {re.sub(r"[^a-z0-9]", "", key.lower()) for key in keys}

    def search(candidate: Any) -> str | None:
        if isinstance(candidate, dict):
            for key, nested_value in candidate.items():
                key_token = re.sub(r"[^a-z0-9]", "", str(key).lower())
                if key_token in normalized and isinstance(nested_value, str):
                    text = nested_value.strip()
                    if text:
                        return text
                found = search(nested_value)
                if found:
                    return found
        elif isinstance(candidate, list):
            for item in candidate:
                found = search(item)
                if found:
                    return found
        return None

    return search(value)


def _plantbook_image(plant: dict[str, Any]) -> str | None:
    image_keys = (
        "image",
        "default_image",
        "defaultImage",
        "image_url",
        "imageUrl",
        "plant_image",
        "plantImage",
        "image_uri",
        "imageUri",
        "photo",
        "photo_url",
        "thumbnail",
        "url",
        "uri",
        "src",
    )
    image = _nested_string_value(plant, image_keys)
    if image and image.startswith(("http://", "https://", "data:image/")):
        return image
    return None


def _plantbook_species(plant: dict[str, Any]) -> str | None:
    species_keys = (
        "scientific_name",
        "scientificName",
        "display_name",
        "displayName",
        "species",
        "latin_name",
        "latinName",
        "default_common_name",
        "defaultCommonName",
        "default_common_name_or_alias",
        "defaultCommonNameOrAlias",
        "common_name",
        "commonName",
    )
    value = _nested_string_value(plant, species_keys)
    return value.strip() if isinstance(value, str) and value.strip() else None
