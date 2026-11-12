# Changelog

All notable changes to DIY Plants are documented here. Versions follow the `version` in `custom_components/diy_plants/manifest.json`.

## [0.5.0] - 2026-11-12

### Added
- Binary problem sensors for each plant: Needs attention, Needs water, Too cold, Too dark and Sensor problem. Only the ones that fit the plant's measurements are created.
- Detection of source sensors that stop reporting. After 6 hours without a report (configurable, `0` turns it off) a measurement is `stale`, the health sensor shows `sensor_stale` and Sensor problem turns on.
- Hysteresis: a low or high value must move 5 % of the limit range back inside the limits before it counts as OK again (configurable, `0` turns it off).
- Notification blueprint that alerts a phone when a plant has needed attention for a while.

### Changed
- The dashboard card shows the `sensor_stale` state and stale measurements.

## [0.4.1] - 2026-11-01

### Fixed
- "Custom element doesn't exist: diy-plants-card" in browsers that had cached a broken copy of the card. The card URL now includes the integration version, so every update gets a fresh URL.
- A stale gzip copy of the card, which the web server would serve instead of the new file, is removed at startup.

## [0.4.0] - 2026-10-31

### Added
- Plant limits from OpenPlantbook. With **Use limits from OpenPlantbook** enabled (the default), Plantbook's recommended ranges replace the configured limits for each measurement Plantbook has values for. Each measurement shows its `limit_source`.

## [0.3.2] - 2026-10-31

### Fixed
- The card's dashboard resource is added automatically, or an existing one is versioned, because the frontend did not always load the card on its own.

## [0.3.1] - 2026-10-31

### Fixed
- The card file is served without long-lived cache headers, and the frontend is an optional dependency.

## [0.3.0] - 2026-10-31

### Added
- The DIY Plants dashboard card is bundled with the integration and loaded automatically.
- Downloadable diagnostics.
- Translated entity names and health states (Danish and English).

### Changed
- **Breaking:** health sensor states are now `ok`, `attention`, `sensor_unavailable` and `no_sensors` (previously `OK`, `Attention`, `Unavailable` and `No sensors`). Update automations that compare against the old values.
- Measurement and DLI sensors have device and state classes, so they get long-term statistics, graphs and unit conversion. They are no longer hidden as diagnostic entities.
- Requires Home Assistant 2024.11 or newer.

### Fixed
- The OpenPlantbook lookup waits for OpenPlantbook to load, uses the plant ID field, searches by name and reports its result in `plantbook_status`.
- The DLI value is no longer reset to 0 when Home Assistant restarts.
- DLI resets exactly at midnight instead of checking every minute.

## [0.2.0] - 2026-09-21

### Added
- OpenPlantbook support and separate soil and air temperature sensors.
- DLI calculated from illuminance.
- Low illuminance warnings are suppressed after sunset.
- Duplicate sensor protection.
- Danish and English translations for the config flow.

[0.5.0]: https://github.com/Tntdruid/diy_plants/releases/tag/v0.5.0
[0.4.1]: https://github.com/Tntdruid/diy_plants/compare/7f2e3ba...7aefc2d
[0.4.0]: https://github.com/Tntdruid/diy_plants/commit/7f2e3ba
[0.3.2]: https://github.com/Tntdruid/diy_plants/commit/784280e
[0.3.1]: https://github.com/Tntdruid/diy_plants/commit/a0a44f4
[0.3.0]: https://github.com/Tntdruid/diy_plants/compare/ded8916...60dc4be
[0.2.0]: https://github.com/Tntdruid/diy_plants/commit/ded8916
