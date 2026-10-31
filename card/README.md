# DIY Plants card (source)

Source for the `custom:diy-plants-card` Lovelace card, inspired by `Olen/lovelace-flower-card`. The integration serves the built bundle from `custom_components/diy_plants/frontend/` and loads it automatically; see the main [README](../README.md#dashboard-card) for card options.

## Development

```bash
npm install
npm test
npm run typecheck
npm run build
```

`npm run build` writes `diy-plants-card.js` to `custom_components/diy_plants/frontend/`. Commit the rebuilt bundle together with source changes, because Home Assistant installs the integration directory as-is.
