from custom_components.diy_plants.const import CONF_DLI_SENSOR, METRICS


def test_dli_metric_exists():
    assert "dli" in METRICS
    assert METRICS["dli"]["config"] == CONF_DLI_SENSOR
    assert METRICS["dli"]["label"] == "DLI"
    assert METRICS["dli"]["unit"] == "mol/m²/d"
