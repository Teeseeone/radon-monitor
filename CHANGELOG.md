# Changelog

## 0.2.5

- Use content-driven section height instead of a fixed row count; display the outer card as a block.
- Ignore report timestamps, source-only updates and status age when displayed values have not changed.
- Forward HA state to the mounted graph at most once per minute; retain its own statistics refresh timer.
- Skip repeated identical configuration and keep the visual editor form stable during sensor updates.
- Show the loaded JavaScript version on the card to identify stale frontend caches.

## 0.2.4

- Expand the visual card editor with average selection, weekly trend, coverage details, compact alerts and graph period controls; keep advanced entity overrides collapsed.
- Add graph buttons for 7 days, 30 days, 6 months, 1 year and 2 years. Long ranges use daily means while graph mounts remain stable during routine updates.
- Compare adjacent seven-day source averages with coverage checks, exposed as status attributes without adding entities.
- Hide detailed coverage by default, retain partial-history warnings, and collapse healthy alerts into an expandable summary. Unknown or active alerts stay visible.
- Preserve existing card YAML, entities, alerts and historical data. Automatically update the card resource to v0.2.4.

## 0.2.3

- Register the card resource automatically, updating existing versions without creating another entry; use frontend module loading for YAML resources.
- Collapse About radon by default and preserve its expanded state during updates.
- Keep the graph mounted during relevant sensor updates and skip unrelated HA state changes. Prevent concurrent graph creation while card helpers load.

## 0.2.2

- Add a short Norway-specific radon explanation to the card, with annual-average guidance and ventilation, sealing and extraction measures.
- Link official DSA sources and add an editor option to hide the explanation.
- Add a device-page Visit link to the radon guide. Alert settings and sensor IDs are unchanged.

## 0.2.1

- Adopt the selected original A house-and-radon icon across the integration, card and repository.
- Bundle light/dark PNG icons at 256 and 512 pixels using HA local brand support.
- Use navy-and-mint card styling by default; keep Dashboard theme as an editor option.
- Refresh resource URLs to v0.2.1 and correct the outdated external brands submission instructions.

## 0.2.0

- Display Radon Monitor on the Integrations page using the service classification.
- Bundle a theme-aware dashboard card with a visual editor, all five averages, hourly coverage, sustained alerts, source health and an optional source statistics graph.
- Serve the card through an async static path; dashboard resource registration remains manual.
- Add original house/radon branding, a banner, sample card preview and a complete card configuration.
- Preserve existing entity IDs, configuration and historical statistics.

## 0.1.0

Initial experimental integration with UI setup, Recorder averages, sustained alerts and source health monitoring.
