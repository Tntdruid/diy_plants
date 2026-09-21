"""Config flow for DIY Plants."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_CONDUCTIVITY_SENSOR,
    CONF_AIR_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_ILLUMINANCE_SENSOR,
    CONF_MOISTURE_SENSOR,
    CONF_PLANTBOOK_API_KEY,
    CONF_PLANTBOOK_ENABLED,
    CONF_PLANTBOOK_PLANT_ID,
    CONF_PLANTBOOK_PLANT_NAME,
    CONF_PLANT_NAME,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
    METRICS,
)

SENSOR_KEYS = {
    CONF_MOISTURE_SENSOR,
    CONF_CONDUCTIVITY_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    CONF_AIR_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_ILLUMINANCE_SENSOR,
}


def _sensor_selector():
    """Return a selector that accepts any sensor entity."""
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain="sensor",
            multiple=False,
        )
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


def _base_schema(current: dict | None = None) -> dict:
    """Return the standard sensor and limit fields for creation and options."""
    current = current or {}
    schema = {
        vol.Optional(
            CONF_MOISTURE_SENSOR, default=current.get(CONF_MOISTURE_SENSOR, "")
        ): _sensor_selector(),
        vol.Optional(
            CONF_CONDUCTIVITY_SENSOR, default=current.get(CONF_CONDUCTIVITY_SENSOR, "")
        ): _sensor_selector(),
        vol.Optional(
            CONF_TEMPERATURE_SENSOR, default=current.get(CONF_TEMPERATURE_SENSOR, "")
        ): _sensor_selector(),
        vol.Optional(
            CONF_AIR_TEMPERATURE_SENSOR,
            default=current.get(CONF_AIR_TEMPERATURE_SENSOR, ""),
        ): _sensor_selector(),
        vol.Optional(
            CONF_HUMIDITY_SENSOR, default=current.get(CONF_HUMIDITY_SENSOR, "")
        ): _sensor_selector(),
        vol.Optional(
            CONF_ILLUMINANCE_SENSOR, default=current.get(CONF_ILLUMINANCE_SENSOR, "")
        ): _sensor_selector(),
    }
    for metric, spec in METRICS.items():
        schema[vol.Optional(f"{metric}_min", default=current.get(f"{metric}_min", spec["minimum"]))] = vol.Coerce(float)
        schema[vol.Optional(f"{metric}_max", default=current.get(f"{metric}_max", spec["maximum"]))] = vol.Coerce(float)
    return schema


def _metric_calibration_fields(metric: str, current: dict | None = None) -> dict:
    """Return calibration fields for one metric, only when enabled."""
    current = current or {}
    enabled_key = f"{metric}_calibration_enabled"
    schema = {
        vol.Optional(
            enabled_key,
            default=current.get(enabled_key, False),
        ): selector.BooleanSelector(),
    }
    if not current.get(enabled_key, False):
        return schema
    schema.update(
        {
            vol.Optional(
                f"{metric}_raw_min", default=current.get(f"{metric}_raw_min", 0)
            ): vol.Coerce(float),
            vol.Optional(
                f"{metric}_raw_max", default=current.get(f"{metric}_raw_max", 100)
            ): vol.Coerce(float),
            vol.Optional(
                f"{metric}_calibrated_min",
                default=current.get(f"{metric}_calibrated_min", 0),
            ): vol.Coerce(float),
            vol.Optional(
                f"{metric}_calibrated_max",
                default=current.get(f"{metric}_calibrated_max", 100),
            ): vol.Coerce(float),
        }
    )
    return schema


def _calibration_schema(current: dict | None = None) -> dict:
    """Build optional linear calibration fields for every measurement."""
    current = current or {}
    schema = {}
    for metric in METRICS:
        schema.update(_metric_calibration_fields(metric, current))
    return schema


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup of a DIY plant."""

    VERSION = 1
    DOMAIN = DOMAIN

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        return DiyPlantsOptionsFlow()

    async def async_step_user(self, user_input=None):
        """Create a plant."""
        errors = {}
        if user_input is not None:
            name = user_input.get(CONF_PLANT_NAME, "").strip()
            if not name:
                errors[CONF_PLANT_NAME] = "name_required"
            else:
                errors.update(_validate_unique_sensor_selection(user_input))
                if not errors:
                    return self.async_create_entry(title=name, data=user_input)

        schema = {
            vol.Required(CONF_PLANT_NAME, default=(user_input or {}).get(CONF_PLANT_NAME, "")): str,
            vol.Optional(CONF_PLANTBOOK_ENABLED, default=(user_input or {}).get(CONF_PLANTBOOK_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_PLANTBOOK_API_KEY, default=(user_input or {}).get(CONF_PLANTBOOK_API_KEY, "")): str,
            vol.Optional(CONF_PLANTBOOK_PLANT_ID, default=(user_input or {}).get(CONF_PLANTBOOK_PLANT_ID, "")): str,
            vol.Optional(CONF_PLANTBOOK_PLANT_NAME, default=(user_input or {}).get(CONF_PLANTBOOK_PLANT_NAME, "")): str,
        }
        schema.update(_base_schema(user_input or {}))
        schema.update(_calibration_schema(user_input or {}))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )


class DiyPlantsOptionsFlow(config_entries.OptionsFlow):
    """Configure sensors after setup."""

    async def async_step_init(self, user_input=None):
        """Update the selected sensors."""
        if user_input is not None:
            errors = _validate_unique_sensor_selection(user_input)
            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=vol.Schema({**_base_schema(user_input), **_calibration_schema(user_input)}),
                    errors=errors,
                )
            options = dict(self.config_entry.options)
            for key, value in user_input.items():
                if key in SENSOR_KEYS and not value:
                    options[key] = None
                else:
                    options[key] = value
            return self.async_update_reload_and_abort(
                self.config_entry,
                options=options,
            )

        current = {**self.config_entry.data, **self.config_entry.options}
        schema = {
            vol.Optional(CONF_PLANTBOOK_ENABLED, default=current.get(CONF_PLANTBOOK_ENABLED, False)): selector.BooleanSelector(),
            vol.Optional(CONF_PLANTBOOK_API_KEY, default=current.get(CONF_PLANTBOOK_API_KEY, "")): str,
            vol.Optional(CONF_PLANTBOOK_PLANT_ID, default=current.get(CONF_PLANTBOOK_PLANT_ID, "")): str,
            vol.Optional(CONF_PLANTBOOK_PLANT_NAME, default=current.get(CONF_PLANTBOOK_PLANT_NAME, "")): str,
        }
        schema.update(_base_schema(current))
        schema.update(_calibration_schema(current))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
