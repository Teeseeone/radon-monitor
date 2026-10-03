# First installation checklist

## Source and history

1. Check `sensor.view_plus_radon` has a radon unit and appears in Developer tools → Statistics.
2. Install the integration and add the source through the UI.
3. Confirm a single virtual device contains concentration, status, five averages and three binary sensors.
4. Compare concentration to the original sensor, allowing for pCi/L conversion if applicable.
5. Compare a seven-day average to a Home Assistant statistics card for the same source and period; account for the incomplete latest hour.
6. Open each average's attributes. A short history must show `partial: true`, and a two-year window must not claim full coverage.
7. If there are no source statistics, average entities must show unknown, not zero. Current monitoring must still work.

## Safe simulation through the UI

Use a separate source so the real sensor history stays intact:

1. Settings → Devices & services → Helpers → Create helper → Number; name it Radon test, range 0–500.
2. Create a Template **sensor** helper using the UI. State template: `{{ states('input_number.radon_test') }}` (adjust to the actual Number entity ID), unit `Bq/m³`, device class Radon, state class Measurement.
3. Add a second Radon Monitor entry for that template sensor.
4. Configure persistence delays to 0.1 hours (six minutes). Set stale age higher than the total test duration; a manual test source does not report continuously.
5. Set test number to 120. Immediate status should be Elevated; sustained elevated binary sensor and one notification should follow six minutes later.
6. Set to 220. High should notify once after its own six-minute timer; holding the value must not spam.
7. Set to 90. High alert should remain latched. Set to 79 and leave it for six minutes: one recovery notification, both concentration alerts cleared.
8. Test invalidity by temporarily changing the test template to `{{ 'unavailable' }}` through its UI. Problem indicator should turn on; problem notification should wait for configured persistence. Restore the valid template and expect one source-restored notification.
9. Set stale age to 0.1 hours on a source that does not re-report. Confirm stale detection and its separate problem delay. Restore the intended settings afterward.
10. Select a phone destination and confirm an actual phone notification. A listed service is not proof of delivery.

## Lifecycle and regression checks

- Restart during a pending elevated timer: concentration persistence must start over.
- Restart with an already active alert: alert remains active without a duplicate notification.
- Configure thresholds in the wrong order: the form should reject them.
- Add the same source twice: duplicate setup should abort.
- Add multiple sources: entities and notifications must stay independent.
- Reload / remove the integration: no orphan listener warnings or background polling.
- Exclude the source from Recorder: average coverage should decrease as the window advances.
- Check Settings → System → Logs for `radon_monitor` errors.

Record the HA version, source unit, observed entities, notification result and any logs in a GitHub issue. The initial local checks do not replace this installation testing.

## Bundled card (0.2.0)

Run `node tests/test_card.cjs` for dependency-free rendering checks. These checks exercise formatting and events with a minimal DOM fixture; they are not a browser or HA frontend runtime test.

After adding the resource described in README, check the card in a real HA dashboard:

- Select your concentration sensor using the visual editor; confirm all five averages and coverage match Developer Tools.
- Tap current/average/alert rows and confirm the correct more-info dialog opens.
- Verify the source statistics graph loads, and turn it off for a compact card.
- Try dark/light themes and phone width; no clipped values or horizontal scrolling.
- Use the simulated test source described above to exercise high, recovery, missing-source and sensor-problem states.
- For renamed sensors, select the optional entity overrides.
- After updating an existing 0.1.0 install, check the Integrations tile and confirm entity IDs and configuration are retained.
