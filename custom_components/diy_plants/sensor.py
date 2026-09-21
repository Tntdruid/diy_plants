"""Sensor entities for DIY Plants."""

from __future__ import annotations

import math
import re
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.typing import StateType
from homeassistant.components.sensor import RestoreSensor, SensorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_PLANT_NAME, DEFAULT_LUX_TO_PPFD, DOMAIN, METRICS
from .plantbook import (
    async_upload_sensor_data,
    build_sensor_payload,
    can_share_data,
)

_LOGGER = logging.getLogger(__name__)

_NUMBER_RE = re.compile(r"[-+]?\d+(?:[,.]\d+)?")


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


def _display_precision(metric: str) -> int:
    """Return a useful display precision for a plant measurement."""
    if metric in (
        "moisture",
        "conductivity",
        "temperature",
        "air_temperature",
        "humidity",
    ):
        return 1
    return 0


def _entry_value(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    """Return a config value, preferring options over original entry data."""
    return entry.options.get(key, entry.data.get(key, default))


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
    def device_info(self) -> dict[str, Any]:
        """Group all entities belonging to this plant."""
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.plant_name,
            "manufacturer": "DIY Plants",
            "model": "Flexible plant monitor",
        }

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

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, metric: str) -> None:
        super().__init__(hass, entry)
        self.metric = metric
        spec = METRICS[metric]
        self._attr_name = spec["label"]
        self._attr_unique_id = f"{entry.entry_id}-{metric}"
        self._attr_native_unit_of_measurement = spec["unit"]
        icon_map = {
            "moisture": "mdi:water-percent",
            "conductivity": "mdi:leaf",
            "temperature": "mdi:thermometer",
            "air_temperature": "mdi:thermometer-lines",
            "humidity": "mdi:water-percent",
            "illuminance": "mdi:brightness-5",
            "dli": "mdi:weather-sunny",
        }
        self._attr_icon = icon_map.get(metric, "mdi:sprout")

    @property
    def native_value(self) -> float | None:
        """Return the normalized value."""
        value, _, _ = _value(
            self.hass, self._source_ids[self.metric], self.metric, self.entry
        )
        return round(value, _display_precision(self.metric)) if value is not None else None

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

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_name = METRICS["dli"]["label"]
        self._attr_unique_id = f"{entry.entry_id}-dli"
        self._attr_native_unit_of_measurement = METRICS["dli"]["unit"]
        self._attr_icon = "mdi:weather-sunny"
        self._daily_dli = 0.0
        self._last_lux: float | None = None
        self._last_timestamp = None
        self._day = None

    @property
    def native_value(self) -> float | None:
        """Return the accumulated DLI for the current calendar day."""
        return round(self._daily_dli, 2)

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
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                if dt_util.as_local(last_state.last_updated).date() == dt_util.now().date():
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
            async_track_time_interval(
                self.hass, self._reset_at_midnight, timedelta(minutes=1)
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
        if self._day is not None and today != self._day:
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

    _attr_icon = "mdi:flower"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_name = "Health"
        self._attr_unique_id = f"{entry.entry_id}-health"
        self._attr_icon = "mdi:heart-pulse"

    @property
    def native_value(self) -> str:
        """Return OK, attention, or unavailable."""
        statuses = self._statuses()
        if not statuses:
            return "No sensors"
        if any(status["status"] == "unavailable" for status in statuses.values()):
            return "Unavailable"
        return "Attention" if any(status["status"] != "ok" for status in statuses.values()) else "OK"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return a compact status report for dashboards and automations."""
        return {"measurements": self._statuses()}

    def _statuses(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for metric, spec in METRICS.items():
            if not self._source_ids[metric]:
                continue
            value, raw, error = _value(
                self.hass, self._source_ids[metric], metric, self.entry
            )
            minimum, maximum = self._limits(metric)
            if value is None:
                status = "unavailable"
            elif value < minimum:
                status = "low"
            elif value > maximum:
                status = "high"
            else:
                status = "ok"
            result[metric] = {
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
    entities: list[SensorEntity] = [DiyPlantHealthSensor(hass, entry)]
    entities.extend(
        DiyPlantMetricSensor(hass, entry, metric)
        for metric, spec in METRICS.items()
        if metric != "dli" and _entry_value(entry, spec["config"])
    )
    if illuminance_entity:
        entities.append(DiyPlantDliSensor(hass, entry))
    async_add_entities(entities)

    plantbook_enabled = _entry_value(entry, "plantbook_enabled", False)
    plantbook_api_key = _entry_value(entry, "plantbook_api_key", "")
    plantbook_id = _entry_value(entry, "plantbook_plant_id", "")
    if not can_share_data(plantbook_enabled, plantbook_api_key) or not plantbook_id:
        return

    source_ids = [
        source
        for metric, spec in METRICS.items()
        if metric != "dli" and (source := _entry_value(entry, spec["config"]))
    ]

    @callback
    def _source_changed_for_plantbook(_event: Event) -> None:
        hass.async_create_task(_upload_plantbook_reading(hass, entry))

    if source_ids:
        hass.async_create_task(_upload_plantbook_reading(hass, entry))
        entry.async_on_unload(
            async_track_state_change_event(
                hass, source_ids, _source_changed_for_plantbook
            )
        )


async def _upload_plantbook_reading(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Upload the current configured readings when Plantbook sharing is enabled."""
    measurements: dict[str, dict[str, Any]] = {}
    for metric, spec in METRICS.items():
        if metric == "dli":
            continue
        source = _entry_value(entry, spec["config"])
        value, raw, error = _value(hass, source, metric, entry)
        if value is not None:
            measurements[metric] = {
                "value": value,
                "unit": spec["unit"],
                "raw": raw,
            }
        elif error:
            _LOGGER.debug("Skipping Plantbook reading for %s: %s", metric, error)

    if not measurements:
        return

    payload = build_sensor_payload(
        _entry_value(entry, "plantbook_plant_id"),
        _entry_value(entry, "plantbook_plant_name", _entry_value(entry, CONF_PLANT_NAME)),
        measurements,
        dt_util.utcnow(),
    )
    try:
        await async_upload_sensor_data(
            hass,
            _entry_value(entry, "plantbook_api_key"),
            payload,
            enabled=True,
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Plantbook upload failed: %s", err)
