"""UI-configured radon monitoring with Recorder-backed averages."""
from pathlib import Path
from datetime import timedelta
import logging
from homeassistant.const import Platform
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from .frontend import async_register_card_resource
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.util import dt as dt_util
from .const import DEFAULTS, DOMAIN
from .engine import AlertState, PERIODS, average, concentration, window_start

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup(hass, config):
    """Serve the bundled dashboard card once per HA process."""
    await hass.http.async_register_static_paths([StaticPathConfig(
        "/radon_monitor/radon-monitor-card.js",
        str(Path(__file__).parent / "www" / "radon-monitor-card.js"), False)])
    card_url = "/radon_monitor/radon-monitor-card.js?v=0.2.3"
    try:
        resources = hass.data[LOVELACE_DATA].resources
        if isinstance(resources, ResourceStorageCollection):
            await async_register_card_resource(resources, card_url)
        else:
            # YAML is user-owned; load globally without rewriting configuration.
            add_extra_js_url(hass, card_url)
    except Exception:
        _LOGGER.exception("Unable to register card automatically; add %s as a dashboard module resource", card_url)
    return True


async def async_setup_entry(hass, entry):
    coordinator = RadonCoordinator(hass, entry)
    await coordinator.async_initialize()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    entry.async_on_unload(async_track_state_change_event(hass, [entry.data["source"]], coordinator.source_changed))
    return True


async def _options_updated(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if result:
        await entry.runtime_data.store.async_save(entry.runtime_data.alerts.data)
    return result


class RadonCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=entry.title, update_interval=timedelta(minutes=1))
        self.entry = entry
        self.source = entry.data["source"]
        self.settings = {**DEFAULTS, **entry.options}
        self.store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self.alerts = AlertState()
        self.rows = []
        self.history_checked = None
        self.history_error = None

    async def async_initialize(self):
        saved = await self.store.async_load()
        if saved:
            self.alerts = AlertState(saved)
        # Time while HA was stopped cannot establish continuous threshold exposure.
        self.alerts.data["since"] = {}
        await self.async_config_entry_first_refresh()

    @callback
    def source_changed(self, event):
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self):
        now = dt_util.utcnow()
        state = self.hass.states.get(self.source)
        value = concentration(state.state, state.attributes.get("unit_of_measurement")) if state else None
        age = (now - state.last_reported).total_seconds() if state else None
        if age is None or age > self.settings["stale_hours"] * 3600:
            value = None
        if self.history_checked is None or now - self.history_checked >= timedelta(hours=1):
            try:
                history = await get_instance(self.hass).async_add_executor_job(
                    statistics_during_period, self.hass, window_start(now, "2_years"), now,
                    {self.source}, "hour", {"radon": "Bq/m³"}, {"mean"})
                self.rows = history.get(self.source, [])
                self.history_error = None
                self.history_checked = now
            except Exception as err:
                # Current monitoring remains operational if Recorder cannot read history.
                _LOGGER.warning("Unable to read radon statistics: %s", err)
                self.history_error = str(err)
                self.history_checked = now - timedelta(minutes=55)
        status, messages = self.alerts.update(now.timestamp(), value, self.settings)
        for message in messages:
            await self.notify(message, value)
        self.store.async_delay_save(lambda: self.alerts.data, 10)
        return {
            "value": value, "status": status, "source_age_seconds": age,
            "history_error": self.history_error,
            "averages": {key: average(self.rows, window_start(now, key), now) for key in PERIODS},
        }

    async def notify(self, kind, value):
        service = self.settings["notification_service"]
        if service == "none":
            return
        domain, name = service.split(".", 1)
        labels = {"elevated": "Sustained elevated radon", "high": "Sustained high radon", "recovered": "Radon recovered", "sensor_problem": "Radon sensor unavailable or stale", "sensor_restored": "Radon sensor restored"}
        text = labels[kind]
        if value is not None:
            text += f": {value:.1f} Bq/m³."
        if kind in ("elevated", "high"):
            text += " Review long-term trends; this is an advisory about sustained readings."
        data = {"title": self.entry.title, "message": text}
        if domain == "persistent_notification":
            data["notification_id"] = f"{DOMAIN}_{self.entry.entry_id}_{'problem' if 'sensor' in kind else 'radon'}"
        try:
            await self.hass.services.async_call(domain, name, data, blocking=True)
        except Exception:
            _LOGGER.exception("Unable to deliver radon notification")
