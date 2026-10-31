from pathlib import Path
from unittest.mock import AsyncMock, Mock

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.diy_plants.const import CARD_URL, CONF_PLANT_NAME, DOMAIN


async def test_bundled_card_is_served_and_loaded(
    hass: HomeAssistant, enable_custom_integrations: None, mock_frontend: Mock
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_PLANT_NAME: "Monstera"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    (paths,), _ = mock_frontend.async_register_static_paths.call_args
    assert paths[0].url_path == CARD_URL
    assert Path(paths[0].path).parts[-2:] == ("frontend", "diy-plants-card.js")
    assert Path(paths[0].path).is_file()

    (url,) = hass.data[DATA_EXTRA_MODULE_URL]
    assert url.startswith(f"{CARD_URL}?v=")


async def test_card_is_served_without_frontend(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    hass.config.components.add("http")
    hass.http = Mock(async_register_static_paths=AsyncMock())
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_PLANT_NAME: "Monstera"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    (paths,), _ = hass.http.async_register_static_paths.call_args
    assert paths[0].cache_headers is False
    assert DATA_EXTRA_MODULE_URL not in hass.data


async def _setup_with_resources(hass: HomeAssistant, items: list[dict], mode: str = "storage"):
    from homeassistant.components.lovelace.resources import ResourceStorageCollection
    from homeassistant.exceptions import HomeAssistantError

    ll_config = Mock(async_load=AsyncMock(side_effect=HomeAssistantError))
    resources = ResourceStorageCollection(hass, ll_config)
    await resources.async_load()
    resources.loaded = True
    for item in items:
        await resources.async_create_item(item)
    hass.data["lovelace"] = Mock(resource_mode=mode, resources=resources)

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_PLANT_NAME: "Monstera"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return resources.async_items()


async def test_card_resource_is_created(
    hass: HomeAssistant, enable_custom_integrations: None, mock_frontend: Mock
) -> None:
    (item,) = await _setup_with_resources(hass, [])
    assert item["type"] == "module"
    assert item["url"].startswith(f"{CARD_URL}?v=")


async def test_manual_card_resource_is_versioned_not_duplicated(
    hass: HomeAssistant, enable_custom_integrations: None, mock_frontend: Mock
) -> None:
    items = await _setup_with_resources(
        hass,
        [
            {"res_type": "module", "url": "/local/other-card.js"},
            {"res_type": "module", "url": CARD_URL},
        ],
    )
    urls = sorted(item["url"] for item in items)
    assert len(urls) == 2
    assert urls[0].startswith(f"{CARD_URL}?v=")
    assert urls[1] == "/local/other-card.js"


async def test_yaml_dashboards_are_left_alone(
    hass: HomeAssistant, enable_custom_integrations: None, mock_frontend: Mock
) -> None:
    assert await _setup_with_resources(hass, [], mode="yaml") == []
