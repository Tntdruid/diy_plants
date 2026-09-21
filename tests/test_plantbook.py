from datetime import UTC, datetime

from custom_components.diy_plants.plantbook import (
    build_sensor_payload,
    can_share_data,
)


def test_plantbook_sharing_requires_enablement_and_api_key():
    assert not can_share_data(False, "key")
    assert not can_share_data(True, "")
    assert can_share_data(True, " key ")


def test_build_sensor_payload_contains_readings_and_timestamp():
    timestamp = datetime(2026, 9, 21, 18, 15, tzinfo=UTC)
    measurements = {"moisture": {"value": 42.0, "unit": "%"}}

    payload = build_sensor_payload(123, "Monstera", measurements, timestamp)

    assert payload == {
        "plant_id": 123,
        "plant_name": "Monstera",
        "timestamp": "2026-09-21T18:15:00+00:00",
        "measurements": measurements,
    }