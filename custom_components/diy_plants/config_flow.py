"""Config flow for DIY Plants."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import ATTR_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_CONDUCTIVITY_SENSOR,
    CONF_DLI_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_ILLUMINANCE_SENSOR,
    CONF_MOISTURE_SENSOR,
    CONF_PLANT_NAME,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
    METRICS,
)

SENSOR_KEYS = {
    CONF_MOISTURE_SENSOR,
    CONF_CONDUCTIVITY_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_ILLUMINANCE_SENSOR,
    CONF_DLI_SENSOR,
}


SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", multiple=False)
)


def _validate_unique_sensor_selection(data: dict) -> dict[str, str]:
    """Reject reusing the same entity in multiple measurement fields."""
    errors: dict[str, str] = {}
    used: dict[str, str] = {}
    for key in SENSOR_KEYS:
        entity_id = data.get(key)
        if not entity_id:
            continue
        if entity_id in used:
            errors[key] = "duplicate_sensor"
            errors[used[entity_id]] = "duplicate_sensor"
        else:
            used[entity_id] = key
    return errors


def _calibration_schema(current: dict | None = None) -> dict:
    """Build optional linear calibration fields for every measurement."""
    current = current or {}
    schema = {}
    for metric in METRICS:
        schema[vol.Optional(
            f"{metric}_calibration_enabled",
            default=current.get(f"{metric}_calibration_enabled", False),
        )] = selector.BooleanSelector()
        schema[vol.Optional(
            f"{metric}_raw_min", default=current.get(f"{metric}_raw_min", 0)
        )] = vol.Coerce(float)
        schema[vol.Optional(
            f"{metric}_raw_max", default=current.get(f"{metric}_raw_max", 100)
        )] = vol.Coerce(float)
        schema[vol.Optional(
            f"{metric}_calibrated_min",
            default=current.get(f"{metric}_calibrated_min", 0),
        )] = vol.Coerce(float)
        schema[vol.Optional(
            f"{metric}_calibrated_max",
            default=current.get(f"{metric}_calibrated_max", 100),
        )] = vol.Coerce(float)
    return schema


class DiyPlantsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup of a DIY plant."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        return DiyPlantsOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Create a plant."""
        errors = {}
        if user_input is not None:
            name = user_input[CONF_PLANT_NAME].strip()
            if not name:
                errors[CONF_PLANT_NAME] = "name_required"
            else:
                errors.update(_validate_unique_sensor_selection(user_input))
                if not errors:
                    return self.async_create_entry(title=name, data=user_input)

        schema = {
            vol.Required(CONF_PLANT_NAME): str,
            vol.Optional(CONF_MOISTURE_SENSOR): SENSOR_SELECTOR,
            vol.Optional(CONF_CONDUCTIVITY_SENSOR): SENSOR_SELECTOR,
            vol.Optional(CONF_TEMPERATURE_SENSOR): SENSOR_SELECTOR,
            vol.Optional(CONF_HUMIDITY_SENSOR): SENSOR_SELECTOR,
            vol.Optional(CONF_ILLUMINANCE_SENSOR): SENSOR_SELECTOR,
            vol.Optional(CONF_DLI_SENSOR): SENSOR_SELECTOR,
        }
        for metric, spec in METRICS.items():
            schema[vol.Optional(f"{metric}_min", default=spec["minimum"])] = vol.Coerce(float)
            schema[vol.Optional(f"{metric}_max", default=spec["maximum"])] = vol.Coerce(float)
        schema.update(_calibration_schema())

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )


class DiyPlantsOptionsFlow(config_entries.OptionsFlow):
    """Configure sensors after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Update the selected sensors."""
        if user_input is not None:
            errors = _validate_unique_sensor_selection(user_input)
            if errors:
                current = self.config_entry.data
                schema = {
                    vol.Optional(
                        CONF_MOISTURE_SENSOR,
                        default=current.get(CONF_MOISTURE_SENSOR, ""),
                    ): SENSOR_SELECTOR,
                    vol.Optional(
                        CONF_CONDUCTIVITY_SENSOR,
                        default=current.get(CONF_CONDUCTIVITY_SENSOR, ""),
                    ): SENSOR_SELECTOR,
                    vol.Optional(
                        CONF_TEMPERATURE_SENSOR,
                        default=current.get(CONF_TEMPERATURE_SENSOR, ""),
                    ): SENSOR_SELECTOR,
                    vol.Optional(
                        CONF_HUMIDITY_SENSOR,
                        default=current.get(CONF_HUMIDITY_SENSOR, ""),
                    ): SENSOR_SELECTOR,
                    vol.Optional(
                        CONF_ILLUMINANCE_SENSOR,
                        default=current.get(CONF_ILLUMINANCE_SENSOR, ""),
                    ): SENSOR_SELECTOR,
                    vol.Optional(
                        CONF_DLI_SENSOR,
                        default=current.get(CONF_DLI_SENSOR, ""),
                    ): SENSOR_SELECTOR,
                }
                for metric, spec in METRICS.items():
                    schema[vol.Optional(f"{metric}_min", default=current.get(f"{metric}_min", spec["minimum"]))] = vol.Coerce(float)
                    schema[vol.Optional(f"{metric}_max", default=current.get(f"{metric}_max", spec["maximum"]))] = vol.Coerce(float)
                schema.update(_calibration_schema(current))
                return self.async_show_form(
                    step_id="init",
                    data_schema=vol.Schema(schema),
                    errors=errors,
                )
            data = dict(self.config_entry.data)
            for key, value in user_input.items():
                if key in SENSOR_KEYS and not value:
                    data.pop(key, None)
                else:
                    data[key] = value
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)
            return self.async_create_entry(title="", data={})

        current = self.config_entry.data
        schema = {
            vol.Optional(
                CONF_MOISTURE_SENSOR,
                default=current.get(CONF_MOISTURE_SENSOR, ""),
            ): SENSOR_SELECTOR,
            vol.Optional(
                CONF_CONDUCTIVITY_SENSOR,
                default=current.get(CONF_CONDUCTIVITY_SENSOR, ""),
            ): SENSOR_SELECTOR,
            vol.Optional(
                CONF_TEMPERATURE_SENSOR,
                default=current.get(CONF_TEMPERATURE_SENSOR, ""),
            ): SENSOR_SELECTOR,
            vol.Optional(
                CONF_HUMIDITY_SENSOR,
                default=current.get(CONF_HUMIDITY_SENSOR, ""),
            ): SENSOR_SELECTOR,
            vol.Optional(
                CONF_ILLUMINANCE_SENSOR,
                default=current.get(CONF_ILLUMINANCE_SENSOR, ""),
            ): SENSOR_SELECTOR,
            vol.Optional(
                CONF_DLI_SENSOR,
                default=current.get(CONF_DLI_SENSOR, ""),
            ): SENSOR_SELECTOR,
        }
        for metric, spec in METRICS.items():
            schema[vol.Optional(f"{metric}_min", default=current.get(f"{metric}_min", spec["minimum"]))] = vol.Coerce(float)
            schema[vol.Optional(f"{metric}_max", default=current.get(f"{metric}_max", spec["maximum"]))] = vol.Coerce(float)
        schema.update(_calibration_schema(current))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
