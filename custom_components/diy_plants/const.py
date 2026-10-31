"""Constants for the DIY Plants integration."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    Platform,
    UnitOfConductivity,
    UnitOfTemperature,
)

DOMAIN = "diy_plants"
PLATFORMS = [Platform.SENSOR]

CARD_FILENAME = "diy-plants-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILENAME}"

CONF_PLANT_NAME = "plant_name"
CONF_DEVICE_LABEL = "device_label"
CONF_MOISTURE_SENSOR = "moisture_sensor"
CONF_CONDUCTIVITY_SENSOR = "conductivity_sensor"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_AIR_TEMPERATURE_SENSOR = "air_temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_ILLUMINANCE_SENSOR = "illuminance_sensor"
CONF_DLI_SENSOR = "dli_sensor"
CONF_LIMITS = "limits"
CONF_PLANTBOOK_API_KEY = "plantbook_api_key"
CONF_PLANTBOOK_CLIENT_ID = "plantbook_client_id"
CONF_PLANTBOOK_CLIENT_SECRET = "plantbook_client_secret"
CONF_PLANTBOOK_PLANT_ID = "plantbook_plant_id"
CONF_PLANTBOOK_ENABLED = "plantbook_enabled"
CONF_PLANTBOOK_PLANT_NAME = "plantbook_plant_name"
CONF_PLANTBOOK_LIMITS = "plantbook_limits"
SIGNAL_PLANTBOOK_UPDATED = f"{DOMAIN}_plantbook_updated_{{}}"
DEFAULT_LUX_TO_PPFD = 0.0185

METRICS = {
    "moisture": {
        "config": CONF_MOISTURE_SENSOR,
        "label": "Soil moisture",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.MOISTURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "precision": 1,
        "minimum": 20.0,
        "maximum": 70.0,
        "plantbook": ("min_soil_moist", "max_soil_moist"),
    },
    "conductivity": {
        "config": CONF_CONDUCTIVITY_SENSOR,
        "label": "Soil conductivity",
        "unit": UnitOfConductivity.MICROSIEMENS_PER_CM,
        "device_class": SensorDeviceClass.CONDUCTIVITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "precision": 0,
        "minimum": 300.0,
        "maximum": 2500.0,
        "plantbook": ("min_soil_ec", "max_soil_ec"),
    },
    "temperature": {
        "config": CONF_TEMPERATURE_SENSOR,
        "label": "Soil temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "precision": 1,
        "minimum": 10.0,
        "maximum": 35.0,
        "plantbook": ("min_temp", "max_temp"),
    },
    "air_temperature": {
        "config": CONF_AIR_TEMPERATURE_SENSOR,
        "label": "Air temperature",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "precision": 1,
        "minimum": 10.0,
        "maximum": 35.0,
        "plantbook": ("min_temp", "max_temp"),
    },
    "humidity": {
        "config": CONF_HUMIDITY_SENSOR,
        "label": "Air humidity",
        "unit": PERCENTAGE,
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "precision": 1,
        "minimum": 30.0,
        "maximum": 80.0,
        "plantbook": ("min_env_humid", "max_env_humid"),
    },
    "illuminance": {
        "config": CONF_ILLUMINANCE_SENSOR,
        "label": "Illuminance",
        "unit": LIGHT_LUX,
        "device_class": SensorDeviceClass.ILLUMINANCE,
        "state_class": SensorStateClass.MEASUREMENT,
        "precision": 0,
        "minimum": 100.0,
        "maximum": 100000.0,
        "plantbook": ("min_light_lux", "max_light_lux"),
    },
    "dli": {
        "config": CONF_DLI_SENSOR,
        "label": "DLI",
        "unit": "mol/m²/d",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "precision": 2,
        "minimum": 2.0,
        "maximum": 60.0,
        "plantbook": ("min_dli", "max_dli"),
    },
}
