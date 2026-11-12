"""Shared measurement evaluation for DIY Plants entities."""

from __future__ import annotations

import math
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import (
    CONF_HYSTERESIS,
    CONF_PLANTBOOK_LIMITS,
    CONF_STALE_HOURS,
    DEFAULT_HYSTERESIS,
    DEFAULT_STALE_HOURS,
    METRICS,
)

_NUMBER_RE = re.compile(r"[-+]?\d+(?:[,.]\d+)?")
SUN_ENTITY = "sun.sun"

STATUS_OK = "ok"
STATUS_LOW = "low"
STATUS_HIGH = "high"
STATUS_UNAVAILABLE = "unavailable"
STATUS_STALE = "stale"

# Measurements whose source does not report on its own schedule are never stale.
_NEVER_STALE = {"dli"}


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


def _entry_value(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    """Return a config value, preferring options over original entry data."""
    return entry.options.get(key, entry.data.get(key, default))


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


def _sun_is_below_horizon(hass: HomeAssistant) -> bool:
    """Return whether Home Assistant reports that the sun has set."""
    sun_state = hass.states.get(SUN_ENTITY)
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


def plantbook_data(entry: ConfigEntry) -> dict[str, Any]:
    runtime = getattr(entry, "runtime_data", None)
    return getattr(runtime, "plantbook", None) or {}


def limits(entry: ConfigEntry, metric: str) -> tuple[float, float, str]:
    """Return the limits and where they come from.

    Plantbook values win over the configured limits when enabled, because
    the config flow always stores limits, even when they are untouched defaults.
    """
    spec = METRICS[metric]
    minimum = float(_entry_value(entry, f"{metric}_min", spec["minimum"]))
    maximum = float(_entry_value(entry, f"{metric}_max", spec["maximum"]))
    source = "configured"
    if _entry_value(entry, CONF_PLANTBOOK_LIMITS, True):
        plantbook = plantbook_data(entry)
        low_key, high_key = spec["plantbook"]
        if (low := _number(plantbook.get(low_key))) is not None:
            minimum, source = low, "plantbook"
        if (high := _number(plantbook.get(high_key))) is not None:
            maximum, source = high, "plantbook"
    return minimum, maximum, source


def _last_reported(state: State):
    """Return when the source last reported, even if its value did not change."""
    return getattr(state, "last_reported", None) or state.last_updated


def _stale_hours(entry: ConfigEntry, metric: str, state: State | None) -> float | None:
    """Return how many hours ago a stale source reported, or None if it is fresh."""
    max_hours = float(_entry_value(entry, CONF_STALE_HOURS, DEFAULT_STALE_HOURS))
    if max_hours <= 0 or state is None or metric in _NEVER_STALE:
        return None
    age = (dt_util.utcnow() - _last_reported(state)).total_seconds() / 3600
    return round(age, 1) if age > max_hours else None


def _limit_status(
    value: float,
    minimum: float,
    maximum: float,
    previous: str | None,
    margin: float,
) -> str:
    """Compare a value with its limits, keeping a low/high status inside the margin.

    Without the margin a value hovering at a limit would flip between ok and
    low on every reading.
    """
    if previous == STATUS_LOW and value < minimum + margin:
        return STATUS_LOW
    if previous == STATUS_HIGH and value > maximum - margin:
        return STATUS_HIGH
    if value < minimum:
        return STATUS_LOW
    if value > maximum:
        return STATUS_HIGH
    return STATUS_OK


def evaluate(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, dict[str, Any]]:
    """Return the status of every configured measurement of one plant."""
    runtime = getattr(entry, "runtime_data", None)
    memory: dict[str, str] = getattr(runtime, "limit_status", None)
    if memory is None:
        memory = {}
    hysteresis = float(_entry_value(entry, CONF_HYSTERESIS, DEFAULT_HYSTERESIS))
    sun_is_below_horizon = _sun_is_below_horizon(hass)
    result: dict[str, dict[str, Any]] = {}
    for metric, spec in METRICS.items():
        entity_id = _entry_value(entry, spec["config"])
        if not entity_id:
            continue
        value, raw, error = _value(hass, entity_id, metric, entry)
        minimum, maximum, limit_source = limits(entry, metric)
        stale_for = _stale_hours(entry, metric, hass.states.get(entity_id))
        if value is None:
            status = STATUS_UNAVAILABLE
        elif stale_for is not None:
            status = STATUS_STALE
            error = f"Source has not reported for {stale_for} hours"
        elif metric == "illuminance" and sun_is_below_horizon and value < minimum:
            # Low light after sunset is expected.
            status = memory[metric] = STATUS_OK
        else:
            margin = max(0.0, (maximum - minimum) * hysteresis / 100)
            status = memory[metric] = _limit_status(
                value, minimum, maximum, memory.get(metric), margin
            )
        result[metric] = {
            "entity_id": entity_id,
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
