"""Binary problem sensors for DIY Plants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import DiyPlantBase
from .status import (
    STATUS_HIGH,
    STATUS_LOW,
    STATUS_STALE,
    STATUS_UNAVAILABLE,
    _entry_value,
    evaluate,
)
from .const import METRICS


@dataclass(frozen=True)
class ProblemDescription:
    key: str
    # Measurements the sensor looks at; None means all configured measurements.
    metrics: tuple[str, ...] | None
    statuses: frozenset[str]
    entity_category: EntityCategory | None = None


PROBLEMS = (
    ProblemDescription("attention", None, frozenset({STATUS_LOW, STATUS_HIGH})),
    ProblemDescription("needs_water", ("moisture",), frozenset({STATUS_LOW})),
    ProblemDescription(
        "too_cold", ("temperature", "air_temperature"), frozenset({STATUS_LOW})
    ),
    ProblemDescription("too_dark", ("illuminance",), frozenset({STATUS_LOW})),
    ProblemDescription(
        "sensor_problem",
        None,
        frozenset({STATUS_UNAVAILABLE, STATUS_STALE}),
        EntityCategory.DIAGNOSTIC,
    ),
)


class DiyPlantProblemSensor(DiyPlantBase, BinarySensorEntity):
    """On while one of the watched measurements has a matching status."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _tracks_status = True

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, description: ProblemDescription
    ) -> None:
        super().__init__(hass, entry)
        self.description = description
        self._attr_translation_key = description.key
        self._attr_unique_id = f"{entry.entry_id}-{description.key}"
        self._attr_entity_category = description.entity_category

    def _matches(self) -> dict[str, dict[str, Any]]:
        statuses = evaluate(self.hass, self.entry)
        watched = self.description.metrics or tuple(statuses)
        return {
            metric: info
            for metric, info in statuses.items()
            if metric in watched and info["status"] in self.description.statuses
        }

    @property
    def is_on(self) -> bool:
        return bool(self._matches())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Name the measurements that cause the problem."""
        return {
            "measurements": {
                metric: {"value": info["value"], "status": info["status"]}
                for metric, info in self._matches().items()
            }
        }


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the problem sensors that fit the plant's configured measurements."""
    configured = {
        metric for metric, spec in METRICS.items() if _entry_value(entry, spec["config"])
    }
    async_add_entities(
        DiyPlantProblemSensor(hass, entry, description)
        for description in PROBLEMS
        if configured
        and (description.metrics is None or configured & set(description.metrics))
    )
