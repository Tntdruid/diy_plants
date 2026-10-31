"""Sensor entities for DIY Plants."""

from __future__ import annotations

import math
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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.helpers.typing import StateType
from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEVICE_LABEL,
    CONF_PLANT_NAME,
    CONF_PLANTBOOK_ENABLED,
    CONF_PLANTBOOK_LIMITS,
    CONF_PLANTBOOK_PLANT_ID,
    CONF_PLANTBOOK_PLANT_NAME,
    DEFAULT_LUX_TO_PPFD,
    DOMAIN,
    METRICS,
    SIGNAL_PLANTBOOK_UPDATED,
)
_LOGGER = logging.getLogger(__name__)

_NUMBER_RE = re.compile(r"[-+]?\d+(?:[,.]\d+)?")
_SUN_ENTITY = "sun.sun"
_OPENPLANTBOOK = "openplantbook"

HEALTH_OK = "ok"
HEALTH_ATTENTION = "attention"
HEALTH_SENSOR_UNAVAILABLE = "sensor_unavailable"
HEALTH_NO_SENSORS = "no_sensors"
HEALTH_STATES = [HEALTH_OK, HEALTH_ATTENTION, HEALTH_SENSOR_UNAVAILABLE, HEALTH_NO_SENSORS]

PLANTBOOK_NO_PLANT = "no_plant_configured"
PLANTBOOK_WAITING = "waiting_for_openplantbook"
PLANTBOOK_LOOKING_UP = "looking_up"
PLANTBOOK_FOUND = "found"
PLANTBOOK_NOT_FOUND = "not_found"
PLANTBOOK_ERROR = "error"


def _number(value: StateType) -> float | None:
    """Parse a numeric state, including values with a decimal comma."""
    if value in (None, STATE_UNKNOWN, STATE_UNAVAILABLE):
        return None
    match = _NUMBER_RE.search(str(value))
    if not match:
        return None
    try:
        parsed = float(match.group().replace(",", "."))
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _conductivity(value: float, unit: str | None) -> float:
    """Return conductivity in the Home Assistant canonical unit, µS/cm."""
    normalized_unit = (unit or "").replace("μ", "µ").lower().replace(" ", "")
    if "ms/cm" in normalized_unit or "mscm" in normalized_unit:
        return value * 1000
    return value


def _calibrate(value: float, entry: ConfigEntry, metric: str) -> float:
    """Map a normalized source value to the user's calibrated range."""
    if not _entry_value(entry, f"{metric}_calibration_enabled", False):
        return value
    raw_min = float(_entry_value(entry, f"{metric}_raw_min", 0))
    raw_max = float(_entry_value(entry, f"{metric}_raw_max", 100))
    calibrated_min = float(_entry_value(entry, f"{metric}_calibrated_min", 0))
    calibrated_max = float(_entry_value(entry, f"{metric}_calibrated_max", 100))
    if raw_min == raw_max:
        return value
    ratio = (value - raw_min) / (raw_max - raw_min)
    calibrated = calibrated_min + ratio * (calibrated_max - calibrated_min)
    low, high = sorted((calibrated_min, calibrated_max))
    return max(low, min(high, calibrated))


def _entry_value(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    """Return a config value, preferring options over original entry data."""
    return entry.options.get(key, entry.data.get(key, default))


def _sun_is_below_horizon(hass: HomeAssistant) -> bool:
    """Return whether Home Assistant reports that the sun has set."""
    sun_state = hass.states.get(_SUN_ENTITY)
    return sun_state is not None and sun_state.state == "below_horizon"


def _value(
    hass: HomeAssistant,
    entity_id: str | None,
    metric: str,
    entry: ConfigEntry,
) -> tuple[float | None, str | None, str | None]:
    """Read and normalize one source entity."""
    if not entity_id:
        return None, None, "No source sensor configured"
    state = hass.states.get(entity_id)
    if state is None:
        return None, None, "Source sensor does not exist"
    raw = _number(state.state)
    if raw is None:
        return None, state.state, f"Source state is {state.state}"
    if metric == "conductivity":
        raw = _conductivity(raw, state.attributes.get("unit_of_measurement"))
    return _calibrate(raw, entry, metric), state.state, None


class DiyPlantEntity(SensorEntity):
    """Common entity behavior for one plant."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.plant_name = _entry_value(entry, CONF_PLANT_NAME)
        self._source_ids = {
            metric: _entry_value(entry, spec["config"])
            for metric, spec in METRICS.items()
        }

    def _limits(self, metric: str) -> tuple[float, float, str]:
        """Return the limits and where they come from.

        Plantbook values win over the configured limits when enabled, because
        the config flow always stores limits, even when they are untouched defaults.
        """
        spec = METRICS[metric]
        minimum = float(_entry_value(self.entry, f"{metric}_min", spec["minimum"]))
        maximum = float(_entry_value(self.entry, f"{metric}_max", spec["maximum"]))
        source = "configured"
        if _entry_value(self.entry, CONF_PLANTBOOK_LIMITS, True):
            plantbook = _plantbook_data(self.entry)
            low_key, high_key = spec["plantbook"]
            if (low := _number(plantbook.get(low_key))) is not None:
                minimum, source = low, "plantbook"
            if (high := _number(plantbook.get(high_key))) is not None:
                maximum, source = high, "plantbook"
        return minimum, maximum, source

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

    @callback
    def _source_changed(self, event: Event) -> None:
        """Refresh when a DIY source publishes a new value."""
        self.async_write_ha_state()


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

    async def async_added_to_hass(self) -> None:
        """Also refresh the limits once Plantbook data arrives."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_PLANTBOOK_UPDATED.format(self.entry.entry_id),
                self.async_write_ha_state,
            )
        )

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
        minimum, maximum, limit_source = self._limits(self.metric)
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

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._plantbook_info: dict[str, Any] = {}
        self._plantbook_status: str | None = None
        self._attr_unique_id = f"{entry.entry_id}-health"

    async def async_added_to_hass(self) -> None:
        """Refresh health when the sun sets or rises and look up Plantbook data."""
        await super().async_added_to_hass()
        if self._source_ids["illuminance"]:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [_SUN_ENTITY], self._sun_changed
                )
            )
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

    @callback
    def _sun_changed(self, event: Event) -> None:
        """Refresh the LX status when the sun changes horizon state."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        """Return ok, attention, sensor_unavailable or no_sensors."""
        statuses = self._statuses()
        if not statuses:
            return HEALTH_NO_SENSORS
        if any(status["status"] == "unavailable" for status in statuses.values()):
            return HEALTH_SENSOR_UNAVAILABLE
        if any(status["status"] != "ok" for status in statuses.values()):
            return HEALTH_ATTENTION
        return HEALTH_OK

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return a compact status report for dashboards and automations."""
        attributes: dict[str, Any] = {"measurements": self._statuses()}
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

    def _statuses(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        sun_is_below_horizon = _sun_is_below_horizon(self.hass)
        for metric, spec in METRICS.items():
            if not self._source_ids[metric]:
                continue
            value, raw, error = _value(
                self.hass, self._source_ids[metric], metric, self.entry
            )
            minimum, maximum, limit_source = self._limits(metric)
            if value is None:
                status = "unavailable"
            elif value < minimum and not (
                metric == "illuminance" and sun_is_below_horizon
            ):
                status = "low"
            elif value > maximum:
                status = "high"
            else:
                status = "ok"
            result[metric] = {
                "entity_id": self._source_ids[metric],
                "value": value,
                "raw": raw,
                "unit": spec["unit"],
                "minimum": minimum,
                "maximum": maximum,
                "limit_source": limit_source,
                "status": status,
                "error": error,
            }
        return result


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


def _plantbook_data(entry: ConfigEntry) -> dict[str, Any]:
    runtime = getattr(entry, "runtime_data", None)
    return getattr(runtime, "plantbook", None) or {}


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
