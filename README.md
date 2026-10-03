# Radon Monitor — 0.1.0 experimental

A UI-configured Home Assistant integration that monitors an existing radon sensor.
Built for `sensor.view_plus_radon`, without needing Airthings credentials or editing YAML.
Supports Bq/m³, Bq/m3 and pCi/L (converted to Bq/m³).

**This is a first test version. Calculation and alert logic have automated tests; installation, config flows, Recorder queries and notifications still require testing in a real Home Assistant instance.** It has not been accepted into the public HACS catalogue. GitHub validation workflows must pass before a release is recommended.

## Features

- Current concentration and immediate Normal / Watch / Elevated / High / Sensor problem status.
- Rolling 7-day, 30-day, 6-calendar-month, 1-calendar-year and 2-calendar-year averages.
- Partial-data flags, recorded hours and hourly bucket coverage for every average.
- Sustained elevated/high alert indicators and advisory notifications.
- Recovery hysteresis and unavailable/stale-source notifications.
- One device per source; multiple sources are supported.
- Settings and notification destination editable through Configure.

## Install through HACS

Once this repository has been published:

1. HACS → three-dot menu → Custom repositories.
2. Add `https://github.com/Teeseeone/radon-monitor`, type **Integration**.
3. Find **Radon Monitor**, download and restart Home Assistant.
4. Settings → Devices & services → Add integration → **Radon Monitor**.
5. Select your original radon sensor and name the monitor.
6. Open **Configure** to choose thresholds, delays and notification destination.

For manual testing, copy `custom_components/radon_monitor` into `/config/custom_components/radon_monitor`, restart, then follow steps 4–6.

Requires Home Assistant 2026.9 or newer and Recorder.

## Default behavior

| Setting | Default |
|---|---|
| Watch / recovery boundary | 80 Bq/m³ |
| Elevated threshold | 100 Bq/m³ |
| High threshold | 200 Bq/m³ |
| Elevated/high persistence | 2 hours |
| Recovery below 80 | 6 hours |
| Maximum source report age | 3 hours |
| Sensor problem persistence | 2 hours |
| Notifications | Home Assistant persistent notification |

Select an existing legacy `notify.mobile_app_…` action in Configure for phone notifications, or `none` to disable notifications. Notify entity-only destinations are not supported in this prototype.

Status changes immediately; sustained alert binary sensors and notifications wait for persistence. High alerts remain latched until recovery, even if the current status drops to Elevated or Watch. No repeated notifications while the same alert remains active. Missing or stale data resets concentration persistence timers. Source age uses `last_reported`, so unchanged values do not count as stale if the integration continues reporting them. Report timestamps indicate HA activity, not independently verified device sampling timestamps.

A source is stale after three hours without a report; its problem notification follows another two hours of continuous invalidity with defaults. Unavailable/unknown readings start the problem timer immediately. Changing settings or restarting HA resets persistence timers, because continuity while stopped is not known. Active alert levels are retained to avoid duplicate alerts.

## Historical data

Averages read **the original sensor's Recorder long-term statistics**, refreshed hourly. Existing statistics are used automatically. No Airthings cloud history is downloaded. Missing history cannot be recreated.

The source must have long-term statistics (normally `state_class: measurement`) and be included in Recorder. Check Developer tools → Statistics. If no statistics exist, averages remain unknown; they never substitute missing readings with zero. The concentration entity this integration creates has measurement statistics for future history graphs, but this prototype does **not** use that entity as a fallback for the original source's averages.

Hourly means are weighted by overlap with the requested window. Coverage indicates populated hourly buckets, not the number of real measurements or proof of uninterrupted sampling within each hour. Gaps are omitted; partial coverage below 99% is flagged. Averages with very little history are available but must be read together with coverage attributes. The incomplete current hour is normally absent until Recorder compiles it.

Calendar months and years are used for 6-month, 1-year and 2-year windows, including leap years. For an Airthings sensor reporting a rolling 24-hour value, these are averages of that reported value. They are for home trend monitoring and should not be presented as a certified radon measurement.

Long-term statistics survive normal Recorder history purges. Database deletion, targeted statistics deletion or loss of the database removes that history; include it in backups. Use HA's History / statistics graph UI to browse historical values. No dedicated chart card is bundled.

## Existing alternatives and scope

- [Historical Statistics](https://github.com/krissen/historical_stats) already offers UI-created historical numeric statistics over custom periods, with long-term-statistics fallback.
- [Air Quality Card](https://github.com/KadenThomp36/air-quality-card) already offers a visual editor, radon display, graphs and a radon advisory banner.
- [EcoSense Radon](https://github.com/rwestergren/hass-ecosense-radon) connects EcoSense cloud devices and exposes alert levels; it does not monitor an arbitrary Airthings source.
- [Airthings](https://www.home-assistant.io/integrations/airthings/) supplies device readings; [Airthings BLE](https://www.home-assistant.io/integrations/airthings_ble/) supports certain devices' short/long-term readings.

Radon Monitor combines selected periods, coverage metadata, sustained radon alerts and source health in one UI-configured device. The search found partial alternatives; it does not prove no equivalent project exists.

## Test it

Read [TESTING.md](TESTING.md) before installing in a production system. No ventilation equipment is controlled by this prototype.

Run pure calculation/state-machine tests locally:

```sh
python -m unittest discover -s tests -v
python -m compileall -q custom_components
```

CI also runs hassfest and HACS validation. Branding is temporarily excluded from HACS CI; add an approved Home Assistant Brands entry before applying for the public catalogue.

## Radon interpretation

Norwegian DSA guidance uses annual-average exposure. A short-term reading over 100 or 200 Bq/m³ is an advisory to examine sustained conditions, not an immediate emergency classification. See [DSA recommended limits](https://www.dsa.no/radon/anbefalte-grenser-for-radon) and [measurement procedure](https://www.dsa.no/radon/slik-maler-du-radon).

## License

MIT. Experimental, community-maintained custom integration.
