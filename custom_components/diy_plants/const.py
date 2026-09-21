"""Constants for the DIY Plants integration."""

from homeassistant.const import Platform

DOMAIN = "diy_plants"
PLATFORMS = [Platform.SENSOR]

CONF_PLANT_NAME = "plant_name"
CONF_MOISTURE_SENSOR = "moisture_sensor"
CONF_CONDUCTIVITY_SENSOR = "conductivity_sensor"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_ILLUMINANCE_SENSOR = "illuminance_sensor"
CONF_DLI_SENSOR = "dli_sensor"
CONF_LIMITS = "limits"

METRICS = {
    "moisture": {
        "config": CONF_MOISTURE_SENSOR,
        "label": "Soil moisture",
        "unit": "%",
        "minimum": 20.0,
        "maximum": 70.0,
    },
    "conductivity": {
        "config": CONF_CONDUCTIVITY_SENSOR,
        "label": "Soil conductivity",
        "unit": "µS/cm",
        "minimum": 300.0,
        "maximum": 2500.0,
    },
    "temperature": {
        "config": CONF_TEMPERATURE_SENSOR,
        "label": "Temperature",
        "unit": "°C",
        "minimum": 10.0,
        "maximum": 35.0,
    },
    "humidity": {
        "config": CONF_HUMIDITY_SENSOR,
        "label": "Air humidity",
        "unit": "%",
        "minimum": 30.0,
        "maximum": 80.0,
    },
    "illuminance": {
        "config": CONF_ILLUMINANCE_SENSOR,
        "label": "Illuminance",
        "unit": "lx",
        "minimum": 100.0,
        "maximum": 100000.0,
    },
    "dli": {
        "config": CONF_DLI_SENSOR,
        "label": "DLI",
        "unit": "mol/m²/d",
        "minimum": 2.0,
        "maximum": 60.0,
    },
}
