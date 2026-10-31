import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache,
)

from custom_components.diy_plants.const import (
    CONF_CONDUCTIVITY_SENSOR,
    CONF_ILLUMINANCE_SENSOR,
    CONF_MOISTURE_SENSOR,
    CONF_PLANT_NAME,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_frontend")


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Monstera",
        data={
            CONF_PLANT_NAME: "Monstera",
            CONF_MOISTURE_SENSOR: "sensor.soil",
            CONF_CONDUCTIVITY_SENSOR: "sensor.ec",
            CONF_ILLUMINANCE_SENSOR: "sensor.lux",
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _entity_id(hass: HomeAssistant, entry: MockConfigEntry, key: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}-{key}"
    )
    assert entity_id
    return entity_id


async def test_metric_sensors_support_statistics(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.soil", "42,5", {"unit_of_measurement": "%"})
    hass.states.async_set("sensor.ec", "1.2", {"unit_of_measurement": "mS/cm"})
    hass.states.async_set("sensor.lux", "500")
    entry = await _setup(hass)

    moisture = hass.states.get(_entity_id(hass, entry, "moisture"))
    assert float(moisture.state) == 42.5
    assert moisture.attributes["device_class"] == "moisture"
    assert moisture.attributes["state_class"] == "measurement"
    assert moisture.attributes["friendly_name"] == "Monstera Soil moisture"

    conductivity = hass.states.get(_entity_id(hass, entry, "conductivity"))
    assert float(conductivity.state) == 1200
    assert conductivity.attributes["device_class"] == "conductivity"

    entity = er.async_get(hass).async_get(_entity_id(hass, entry, "moisture"))
    assert entity.entity_category is None


async def test_health_is_translated_enum(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.soil", "42", {"unit_of_measurement": "%"})
    hass.states.async_set("sensor.ec", "1000", {"unit_of_measurement": "µS/cm"})
    hass.states.async_set("sensor.lux", "500")
    entry = await _setup(hass)
    health_id = _entity_id(hass, entry, "health")

    health = hass.states.get(health_id)
    assert health.state == "ok"
    assert health.attributes["device_class"] == "enum"
    assert "attention" in health.attributes["options"]

    hass.states.async_set("sensor.soil", "5", {"unit_of_measurement": "%"})
    await hass.async_block_till_done()
    assert hass.states.get(health_id).state == "attention"

    hass.states.async_set("sensor.soil", "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(health_id).state == "sensor_unavailable"


async def test_dli_keeps_todays_value_after_restart(hass: HomeAssistant) -> None:
    mock_restore_cache(
        hass, [State("sensor.monstera_daily_light_integral", "3.5")]
    )
    hass.states.async_set("sensor.lux", "500")
    entry = await _setup(hass)

    dli_id = _entity_id(hass, entry, "dli")
    assert dli_id == "sensor.monstera_daily_light_integral"
    dli = hass.states.get(dli_id)
    assert float(dli.state) == 3.5
    assert dli.attributes["state_class"] == "total_increasing"
