from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.diy_plants.const import (
    CONF_HYSTERESIS,
    CONF_ILLUMINANCE_SENSOR,
    CONF_MOISTURE_SENSOR,
    CONF_PLANT_NAME,
    CONF_STALE_HOURS,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_frontend")


async def _setup(hass: HomeAssistant, **data) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PLANT_NAME: "Basilikum", CONF_MOISTURE_SENSOR: "sensor.soil", **data},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _state(hass: HomeAssistant, entry: MockConfigEntry, domain: str, key: str):
    entity_id = er.async_get(hass).async_get_entity_id(
        domain, DOMAIN, f"{entry.entry_id}-{key}"
    )
    return hass.states.get(entity_id) if entity_id else None


async def _set_moisture(hass: HomeAssistant, value: float) -> None:
    hass.states.async_set("sensor.soil", str(value), {"unit_of_measurement": "%"})
    await hass.async_block_till_done()


async def test_source_that_stops_reporting_becomes_stale(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _set_moisture(hass, 40)
    entry = await _setup(hass)
    assert _state(hass, entry, "sensor", "health").state == "ok"
    assert _state(hass, entry, "binary_sensor", "sensor_problem").state == "off"

    freezer.tick(timedelta(hours=7))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    health = _state(hass, entry, "sensor", "health")
    assert health.state == "sensor_stale"
    assert health.attributes["measurements"]["moisture"]["status"] == "stale"
    assert _state(hass, entry, "binary_sensor", "sensor_problem").state == "on"

    # Reporting the same value again counts as fresh.
    hass.states.async_set(
        "sensor.soil", "40", {"unit_of_measurement": "%"}, force_update=True
    )
    await hass.async_block_till_done()
    assert _state(hass, entry, "sensor", "health").state == "ok"


async def test_stale_check_can_be_turned_off(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _set_moisture(hass, 40)
    entry = await _setup(hass, **{CONF_STALE_HOURS: 0})
    freezer.tick(timedelta(hours=48))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert _state(hass, entry, "sensor", "health").state == "ok"


async def test_hysteresis_keeps_low_until_value_recovers(hass: HomeAssistant) -> None:
    # Default limits 20-70 % and 5 % hysteresis give a 2.5 % margin.
    await _set_moisture(hass, 40)
    entry = await _setup(hass)

    await _set_moisture(hass, 19)
    assert _state(hass, entry, "binary_sensor", "needs_water").state == "on"
    await _set_moisture(hass, 21)
    assert _state(hass, entry, "binary_sensor", "needs_water").state == "on"
    assert _state(hass, entry, "sensor", "health").state == "attention"
    await _set_moisture(hass, 23)
    assert _state(hass, entry, "binary_sensor", "needs_water").state == "off"
    assert _state(hass, entry, "sensor", "health").state == "ok"


async def test_no_hysteresis_when_turned_off(hass: HomeAssistant) -> None:
    await _set_moisture(hass, 19)
    entry = await _setup(hass, **{CONF_HYSTERESIS: 0})
    assert _state(hass, entry, "binary_sensor", "needs_water").state == "on"
    await _set_moisture(hass, 21)
    assert _state(hass, entry, "binary_sensor", "needs_water").state == "off"


async def test_problem_sensors_follow_configured_measurements(
    hass: HomeAssistant,
) -> None:
    await _set_moisture(hass, 40)
    entry = await _setup(hass)
    assert _state(hass, entry, "binary_sensor", "attention") is not None
    assert _state(hass, entry, "binary_sensor", "needs_water") is not None
    assert _state(hass, entry, "binary_sensor", "too_dark") is None
    assert _state(hass, entry, "binary_sensor", "too_cold") is None
    assert (
        _state(hass, entry, "binary_sensor", "needs_water").attributes["friendly_name"]
        == "Basilikum Needs water"
    )


async def test_too_dark_ignores_night(hass: HomeAssistant) -> None:
    await _set_moisture(hass, 40)
    hass.states.async_set("sensor.lux", "10")
    hass.states.async_set("sun.sun", "above_horizon")
    entry = await _setup(hass, **{CONF_ILLUMINANCE_SENSOR: "sensor.lux"})
    too_dark = lambda: _state(hass, entry, "binary_sensor", "too_dark").state  # noqa: E731
    assert too_dark() == "on"

    hass.states.async_set("sun.sun", "below_horizon")
    await hass.async_block_till_done()
    assert too_dark() == "off"
