"""Sensor entities for DIY Plants."""

from __future__ import annotations

import math
import re
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
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
    DEFAULT_LUX_TO_PPFD,
    DOMAIN,
    METRICS,
)
_LOGGER = logging.getLogger(__name__)

_NUMBER_RE = re.compile(r"[-+]?\d+(?:[,.]\d+)?")
_SUN_ENTITY = "sun.sun"

HEALTH_OK = "ok"
HEALTH_ATTENTION = "attention"
HEALTH_SENSOR_UNAVAILABLE = "sensor_unavailable"
HEALTH_NO_SENSORS = "no_sensors"
HEALTH_STATES = [HEALTH_OK, HEALTH_ATTENTION, HEALTH_SENSOR_UNAVAILABLE, HEALTH_NO_SENSORS]


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

    def _limits(self, metric: str) -> tuple[float, float]:
        """Return configured limits, falling back to sensible defaults."""
        spec = METRICS[metric]
        return (
            float(_entry_value(self.entry, f"{metric}_min", spec["minimum"])),
            float(_entry_value(self.entry, f"{metric}_max", spec["maximum"])),
        )

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
        minimum, maximum = self._limits(self.metric)
        return {
            "source_entity": source,
            "raw_state": raw,
            "normalized_value": value,
            "minimum": minimum,
            "maximum": maximum,
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

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        plantbook_info: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(hass, entry)
        self._plantbook_info = plantbook_info or {}
        self._attr_unique_id = f"{entry.entry_id}-health"
        self._attr_entity_picture = _plantbook_image(self._plantbook_info)

    async def async_added_to_hass(self) -> None:
        """Refresh health when the sun sets or rises."""
        await super().async_added_to_hass()
        if self._source_ids["illuminance"]:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [_SUN_ENTITY], self._sun_changed
                )
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
            minimum, maximum = self._limits(metric)
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
                "status": status,
                "error": error,
            }
        return result


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up plant sensor entities."""
    illuminance_entity = _entry_value(entry, METRICS["illuminance"]["config"])
    plantbook_info = await _fetch_plantbook_info(hass, entry)
    entities: list[SensorEntity] = [DiyPlantHealthSensor(hass, entry, plantbook_info)]
    entities.extend(
        DiyPlantMetricSensor(hass, entry, metric)
        for metric, spec in METRICS.items()
        if metric != "dli" and _entry_value(entry, spec["config"])
    )
    if illuminance_entity:
        entities.append(DiyPlantDliSensor(hass, entry))
    async_add_entities(entities)

async def _fetch_plantbook_info(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    if not _entry_value(entry, "plantbook_enabled", False):
        return {}
    plant_name = _entry_value(entry, "plantbook_plant_name", "").strip()
    if not plant_name or not hass.services.has_service("openplantbook", "get"):
        return {}
    try:
        response = await hass.services.async_call(
            "openplantbook",
            "get",
            {"species": plant_name.lower(), "include": "care"},
            blocking=True,
            return_response=True,
        )
        return response if isinstance(response, dict) else {}
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Plantbook plant lookup failed: %s", err)
        return {}


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
