# DIY Plants for Home Assistant

A DIY-friendly plant monitor for Home Assistant. Sensor selection is based on entity ID, not `device_class`, so ESPHome, MQTT, and template sensors can be used even when their metadata is incomplete.

## Install

1. Copy `custom_components/diy_plants` into the `custom_components` directory of Home Assistant.
2. Restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration** and add **DIY Plants**.
4. Choose a sensor entity for each measurement you want to track.

Choose any sensor entity for the available measurements. Conductivity is normalized to `µS/cm`; both `μS/cm` and `µS/cm` are accepted, and `mS/cm` is converted automatically.

## Current features

- Manual entity selection without device-class filtering
- Soil moisture, conductivity, temperature, humidity, illuminance, and DLI
- Configurable minimum and maximum limits
- Immediate updates when source sensors change
- Health entity with per-measurement status and diagnostics
- Raw source values preserved in attributes for troubleshooting
- Duplicate sensor protection so the same entity cannot be assigned to multiple measurements
- Danish and English translations for the config flow

## Calibration

Open the integration's options and enable calibration for the measurement you want to adjust. Enter the raw values measured at two known points and the desired output values.

For soil moisture, for example:

- Raw dry value: `820`
- Raw wet value: `410`
- Output at dry value: `0`
- Output at wet value: `100`

The mapping is linear and is clamped to the configured output range. The raw value can be inverted by entering a higher raw dry value than raw wet value. Calibration is disabled by default.

The integration currently uses default limits as starting points. Calibration transforms, smoothing, hysteresis, and irrigation actions are planned next.

## What’s new

- Added DLI support as a plant metric
- Added duplicate sensor protection to avoid assigning the same entity to multiple measurements
- Added Danish and English translations for the config flow
- Stabilized the config and options flow for calibration settings
- Improved HACS compatibility metadata

## Notes

- Each measurement is a single sensor field, so you can only assign one entity to each metric.
- DLI is treated as a daily light integral measurement in `mol/m²/d`.
