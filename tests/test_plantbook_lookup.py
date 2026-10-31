import pytest
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.diy_plants.const import (
    CONF_MOISTURE_SENSOR,
    CONF_PLANT_NAME,
    CONF_PLANTBOOK_ENABLED,
    CONF_PLANTBOOK_PLANT_ID,
    CONF_PLANTBOOK_PLANT_NAME,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_frontend")

PLANTS = {
    "monstera deliciosa": {
        "pid": "monstera deliciosa",
        "display_pid": "Monstera deliciosa",
        "image_url": "https://example.com/monstera.jpg",
    },
    "ficus lyrata": {
        "pid": "ficus lyrata",
        "display_pid": "Ficus lyrata",
        "image_url": "https://example.com/ficus.jpg",
    },
}


def _register_openplantbook(hass: HomeAssistant) -> list[tuple[str, dict]]:
    calls: list[tuple[str, dict]] = []

    async def get(call: ServiceCall) -> dict:
        calls.append(("get", dict(call.data)))
        return PLANTS.get(call.data["species"], {})

    async def search(call: ServiceCall) -> dict:
        calls.append(("search", dict(call.data)))
        alias = call.data["alias"].lower()
        return {pid: p["display_pid"] for pid, p in PLANTS.items() if alias in pid}

    hass.services.async_register("openplantbook", "get", get, None, SupportsResponse.OPTIONAL)
    hass.services.async_register(
        "openplantbook", "search", search, None, SupportsResponse.OPTIONAL
    )
    return calls


async def _setup(hass: HomeAssistant, **plantbook) -> str:
    hass.states.async_set("sensor.soil", "40", {"unit_of_measurement": "%"})
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_PLANT_NAME: "Stueplante",
            CONF_MOISTURE_SENSOR: "sensor.soil",
            CONF_PLANTBOOK_ENABLED: True,
            **plantbook,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}-health"
    )
    assert entity_id
    return entity_id


async def test_lookup_waits_for_openplantbook_to_load(hass: HomeAssistant) -> None:
    health_id = await _setup(hass, **{CONF_PLANTBOOK_PLANT_ID: "monstera deliciosa"})
    assert hass.states.get(health_id).attributes["plantbook_status"] == "waiting_for_openplantbook"

    _register_openplantbook(hass)
    await hass.async_block_till_done()

    health = hass.states.get(health_id)
    assert health.attributes["plantbook_status"] == "found"
    assert health.attributes["plantbook_pid"] == "monstera deliciosa"
    assert health.attributes["entity_picture"] == "https://example.com/monstera.jpg"


async def test_common_name_falls_back_to_search(hass: HomeAssistant) -> None:
    calls = _register_openplantbook(hass)
    health_id = await _setup(hass, **{CONF_PLANTBOOK_PLANT_NAME: "Ficus"})

    health = hass.states.get(health_id)
    assert health.attributes["plantbook_status"] == "found"
    assert health.attributes["plantbook_pid"] == "ficus lyrata"
    assert [name for name, _ in calls] == ["get", "search", "get"]


async def test_plant_id_is_used_before_name(hass: HomeAssistant) -> None:
    calls = _register_openplantbook(hass)
    await _setup(
        hass,
        **{CONF_PLANTBOOK_PLANT_ID: "ficus lyrata", CONF_PLANTBOOK_PLANT_NAME: "Monstera"},
    )
    assert calls[0] == ("get", {"species": "ficus lyrata", "include": "care"})


async def test_unknown_plant_reports_not_found(hass: HomeAssistant) -> None:
    _register_openplantbook(hass)
    health_id = await _setup(hass, **{CONF_PLANTBOOK_PLANT_NAME: "Kaktus"})

    health = hass.states.get(health_id)
    assert health.attributes["plantbook_status"] == "not_found"
    assert "entity_picture" not in health.attributes
