# DIY Plants for Home Assistant

A DIY-friendly plant monitor for Home Assistant. Sensor selection is based on entity ID, not `device_class`, so ESPHome, MQTT, and template sensors can be used even when their metadata is incomplete.

## Install with HACS

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tntdruid&repository=diy_plants&category=integration)

In HACS, open **Integrations**, search for **DIY Plants**, and select **Download**. Restart Home Assistant after the download, then add the integration from **Settings > Devices & services**.

## Install

1. Copy `custom_components/diy_plants` into the `custom_components` directory of Home Assistant.
2. Restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration** and add **DIY Plants**.
4. Choose a sensor entity for each measurement you want to track.

Choose any sensor entity for the available measurements. Conductivity is normalized to `µS/cm`; both `μS/cm` and `µS/cm` are accepted, and `mS/cm` is converted automatically.

## Current features

- Manual entity selection without device-class filtering
- Soil moisture, conductivity, soil temperature, air temperature, humidity, and illuminance
- DLI calculated automatically from illuminance using a lux-to-PPFD conversion
- Configurable minimum and maximum limits
- Immediate updates when source sensors change
- Measurement sensors with device and state classes, so Home Assistant keeps long-term statistics and shows them on dashboards
- Health entity with per-measurement status and diagnostics
- Health entity exposes the Plantbook plant image and species when Plantbook is enabled
- Plantbook species lookup uses Home Assistant's OpenPlantbook integration; no API key is stored by DIY Plants
- Raw source values preserved in attributes for troubleshooting
- Duplicate sensor protection so the same entity cannot be assigned to multiple measurements
- Danish and English translations for the config flow, entity names and health states
- Downloadable diagnostics for bug reports (**Settings > Devices & services > DIY Plants > ⋮ > Download diagnostics**)

## Health states

| State | Shown as | Meaning |
|---|---|---|
| `ok` | OK | All configured measurements are within their limits |
| `attention` | Needs attention | At least one measurement is too low or too high |
| `sensor_unavailable` | Sensor unavailable | At least one source sensor has no usable value |
| `no_sensors` | No sensors | No source sensors are configured |

Automations and templates should compare against the state value, for example `is_state('sensor.monstera_health', 'attention')`.

## Dashboard card

The integration ships its own Lovelace card, `custom:diy-plants-card`. It is loaded automatically when DIY Plants is set up, so you do not need to add a dashboard resource. Restart Home Assistant and refresh the browser after installing or updating.

If you previously installed the standalone DIY Plants card through HACS or `/config/www`, remove that dashboard resource; the bundled card replaces it.

### Usage

Use the plant's health sensor as the card entity. Its `measurements` attribute contains the values and limits the card displays:

```yaml
type: custom:diy-plants-card
entity: sensor.monstera_health
fertilizer_sensor: sensor.monstera_fertilizing
```

The card reads these measurements directly:

- `moisture`
- `conductivity`
- `temperature`
- `air_temperature`
- `humidity`
- `illuminance`
- `dli`

This means Plant Monitor and a `plant.*` entity are not required.

### Options

```yaml
type: custom:diy-plants-card
entity: sensor.monstera_health
name: Monstera
subtitle: Stueplanter
image: /local/plants/monstera.jpg
show_measurements:
  - moisture
  - temperature
  - humidity
  - illuminance
  - dli
display_type: full
text_size: medium
hide_units: false
show_health: true
bars_per_row: 2
measurement_entities:
  temperature: sensor.monstera_soil_temperature
  air_temperature: sensor.monstera_air_temperature
moisture_min: 25
moisture_max: 65
moisture_min_sensor: sensor.drivhus_plante1_min_fugt
moisture_max_sensor: sensor.drivhus_plante1_max_fugt
```

`display_type: compact` defaults to one column and hides units. `bars_per_row` can be `1` or `2` and overrides that default.

`text_size` can be `small`, `medium` or `large` and changes the card's text scale.

`subtitle` is optional and can be different for each plant card. If omitted, the card uses `DIY Plants`.

`moisture_min` and `moisture_max` override the acceptable soil-moisture range for this card. If omitted, the limits from DIY Plants are used.

`fertilizer_sensor` is an optional Home Assistant sensor used as a reminder. Its current state is shown in the card header, for example `Gødning: OK`.

`measurement_entities` optionally maps displayed measurements to their Home Assistant sensor entities. Mapped measurements become clickable and open the standard Home Assistant more-info panel. The integration creates entities such as `temperature` and `air_temperature`; use the exact entity IDs from your installation.

For dynamic limits, set `moisture_min_sensor` and `moisture_max_sensor` to sensor entities. Their current numeric states override the fixed values, for example `sensor.drivhus_plante1_min_fugt` and `sensor.drivhus_plante1_max_fugt`.

`image` is optional. It can be a local URL such as `/local/plants/monstera.jpg`, an external image URL, or it can be omitted when the health entity already exposes an `entity_picture` attribute.

## Flower Card

Use the Lovelace Flower Card together with Olen's Plant Monitor integration.
Select the DIY Plants sensor entities as the source sensors in Plant Monitor,
then add a card such as:

```yaml
type: custom:flower-card
entity: plant.my_plant
show_bars:
	- moisture
	- conductivity
	- temperature
	- illuminance
	- humidity
	- dli
```

The `plant.<name>` entity is provided by Plant Monitor, which also supplies the
Flower Card websocket data and optional OpenPlantbook species information.

The DIY Plants health sensor also exposes `entity_picture` and `plantbook_image`
after a Plantbook plant lookup. Lovelace cards can use that image without
requiring a Plantbook API key in DIY Plants.

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

### 0.3.0

- The DIY Plants dashboard card is now bundled with the integration and loaded automatically.
- **Breaking:** the health sensor states are now `ok`, `attention`, `sensor_unavailable` and `no_sensors` (previously `OK`, `Attention`, `Unavailable` and `No sensors`). Update automations that compare against the old values.
- Measurement and DLI sensors now have device and state classes, so they get long-term statistics, proper graphs and unit conversion. They are no longer hidden as diagnostic entities.
- Entity names and health states are translated (Danish and English).
- Fixed the DLI value being reset to 0 when Home Assistant restarts.
- DLI now resets exactly at midnight instead of checking every minute.
- Added downloadable diagnostics and hassfest validation.
- Requires Home Assistant 2024.11 or newer.

### Earlier

- Suppressed low illuminance warnings after sunset; warnings resume at sunrise
- Added DLI support as a plant metric
- Added duplicate sensor protection to avoid assigning the same entity to multiple measurements
- Added Danish and English translations for the config flow
- Stabilized the config and options flow for calibration settings
- Improved HACS compatibility metadata

## Notes

- Each measurement is a single sensor field, so you can only assign one entity to each metric.
- DLI is treated as a daily light integral measurement in `mol/m²/d`.
