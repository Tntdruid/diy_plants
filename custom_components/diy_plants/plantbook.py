"""Helpers for integration with Open Plantbook."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from aiohttp import ClientError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLANTBOOK_BASE_URL = "https://open.plantbook.io/api/v1"


def can_share_data(enabled: bool, api_key: str | None) -> bool:
    """Return True only when Plantbook sharing is explicitly enabled and configured."""
    return bool(enabled) and bool(api_key and api_key.strip())


def build_sensor_payload(
    plant_id: str | int,
    plant_name: str,
    measurements: dict[str, dict[str, Any]],
    timestamp: datetime,
) -> dict[str, Any]:
    """Build the JSON payload used for one Plantbook sensor reading."""
    return {
        "plant_id": plant_id,
        "plant_name": plant_name,
        "timestamp": timestamp.isoformat(),
        "measurements": measurements,
    }


class PlantbookError(RuntimeError):
    """Raised when the Plantbook API returns an error."""


class PlantbookClient:
    """Minimal Open Plantbook API client for lookup and upload support."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        *,
        enabled: bool = True,
        base_url: str = PLANTBOOK_BASE_URL,
    ) -> None:
        self.hass = hass
        self.api_key = api_key
        self.enabled = enabled
        self.base_url = base_url.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Perform a request to the Plantbook API."""
        if not can_share_data(self.enabled, self.api_key):
            raise PlantbookError("Plantbook sharing is disabled or no API key is configured.")

        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        session = async_get_clientsession(self.hass)
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if json is not None:
            headers["Content-Type"] = "application/json"

        try:
            async with session.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                params=params,
                json=json,
            ) as response:
                payload = await response.json(content_type=None)
                if 200 <= response.status < 300:
                    return payload
                detail = payload.get("detail") if isinstance(payload, dict) else payload
                raise PlantbookError(
                    f"Plantbook API error {response.status}: {detail or response.reason}"
                )
        except ClientError as err:
            raise PlantbookError(f"Request to Plantbook failed: {err}") from err

    async def search_plants(self, query: str) -> list[dict[str, Any]]:
        """Search by plant name or common name."""
        data = await self._request("GET", "/plant/search", params={"query": query})
        if isinstance(data, dict):
            results = data.get("results", [])
            return results if isinstance(results, list) else []
        if isinstance(data, list):
            return data
        return []

    async def get_plant(self, plant_id: str | int) -> dict[str, Any]:
        """Fetch a single plant record by id."""
        return await self._request("GET", f"/plant/detail/{plant_id}")

    async def create_plant(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a Plantbook plant entry."""
        return await self._request("POST", "/plant/create", json=payload)

    async def register_instance(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register a plant instance for sensor sharing."""
        return await self._request("POST", "/sensor-data/instance", json=payload)

    async def upload_sensor_data(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Upload sensor data in JTS format."""
        return await self._request("POST", "/sensor-data/upload", json=payload)


async def async_search_plant(
    hass: HomeAssistant,
    api_key: str,
    query: str,
    *,
    enabled: bool = True,
) -> list[dict[str, Any]]:
    """Quick lookup helper for a plant search."""
    if not can_share_data(enabled, api_key):
        return []
    client = PlantbookClient(hass, api_key, enabled=enabled)
    return await client.search_plants(query)


async def async_get_plant(
    hass: HomeAssistant,
    api_key: str,
    plant_id: str | int,
    *,
    enabled: bool = True,
) -> dict[str, Any]:
    """Quick fetch helper for a specific plant by id."""
    if not can_share_data(enabled, api_key):
        return {}
    client = PlantbookClient(hass, api_key, enabled=enabled)
    return await client.get_plant(plant_id)


async def async_link_plant(
    hass: HomeAssistant,
    api_key: str,
    plant_id: str | int,
    plant_name: str,
    source_entity: str,
    *,
    enabled: bool = True,
) -> dict[str, Any]:
    """Build a minimal link payload for a Plantbook plant record."""
    if not can_share_data(enabled, api_key):
        return {}
    client = PlantbookClient(hass, api_key, enabled=enabled)
    payload = {
        "plant_id": plant_id,
        "plant_name": plant_name,
        "source_entity": source_entity,
    }
    return await client.register_instance(payload)


async def async_upload_sensor_data(
    hass: HomeAssistant,
    api_key: str,
    payload: dict[str, Any],
    *,
    enabled: bool = True,
) -> dict[str, Any]:
    """Upload sensor time series data to Plantbook."""
    if not can_share_data(enabled, api_key):
        return {}
    client = PlantbookClient(hass, api_key, enabled=enabled)
    return await client.upload_sensor_data(payload)
