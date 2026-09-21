"""Sensor entities for DIY Plants."""

from __future__ import annotations

import math
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import StateType
from homeassistant.components.sensor import SensorEntity

from .const import CONF_PLANT_NAME, DOMAIN, METRICS

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
    if not entry.data.get(f"{metric}_calibration_enabled", False):
        return value
    raw_min = float(entry.data.get(f"{metric}_raw_min", 0))
    raw_max = float(entry.data.get(f"{metric}_raw_max", 100))
    calibrated_min = float(entry.data.get(f"{metric}_calibrated_min", 0))
    calibrated_max = float(entry.data.get(f"{metric}_calibrated_max", 100))
    if raw_min == raw_max:
        return value
    ratio = (value - raw_min) / (raw_max - raw_min)
    calibrated = calibrated_min + ratio * (calibrated_max - calibrated_min)
    low, high = sorted((calibrated_min, calibrated_max))
    return max(low, min(high, calibrated))


def _display_precision(metric: str) -> int:
    """Return a useful display precision for a plant measurement."""
    if metric in ("moisture", "conductivity", "temperature", "humidity"):
        return 1
    return 0


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
        self.plant_name = entry.data[CONF_PLANT_NAME]
        self._source_ids = {
            metric: entry.data.get(spec["config"])
            for metric, spec in METRICS.items()
        }

    def _limits(self, metric: str) -> tuple[float, float]:
        """Return configured limits, falling back to sensible defaults."""
        spec = METRICS[metric]
        return (
            float(self.entry.data.get(f"{metric}_min", spec["minimum"])),
            float(self.entry.data.get(f"{metric}_max", spec["maximum"])),
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
        self._attr_icon = "mdi:sprout"

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
            "calibration_enabled": self.entry.data.get(
                f"{self.metric}_calibration_enabled", False
            ),
        }


class DiyPlantHealthSensor(DiyPlantEntity):
    """Report whether configured measurements are within their limits."""

    _attr_icon = "mdi:flower"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_name = "Health"
        self._attr_unique_id = f"{entry.entry_id}-health"

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
    entities: list[SensorEntity] = [DiyPlantHealthSensor(hass, entry)]
    entities.extend(
        DiyPlantMetricSensor(hass, entry, metric)
        for metric, spec in METRICS.items()
        if entry.data.get(spec["config"])
    )
    async_add_entities(entities)
