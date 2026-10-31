from types import SimpleNamespace

from custom_components.diy_plants.const import CONF_DLI_SENSOR, METRICS
from custom_components.diy_plants.sensor import _sun_is_below_horizon


def test_dli_metric_exists():
    assert "dli" in METRICS
    assert METRICS["dli"]["config"] == CONF_DLI_SENSOR
    assert METRICS["dli"]["label"] == "DLI"
    assert METRICS["dli"]["unit"] == "mol/m²/d"


def test_sun_is_below_horizon():
    hass = SimpleNamespace(
        states=SimpleNamespace(
            get=lambda entity_id: SimpleNamespace(state="below_horizon")
            if entity_id == "sun.sun"
            else None
        )
    )

    assert _sun_is_below_horizon(hass)
