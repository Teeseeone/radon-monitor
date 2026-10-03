"""Configure Radon Monitor entirely through the UI."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DEFAULTS, DOMAIN


def options_schema(hass, values):
    services = ["none", "persistent_notification.create"]
    services += [f"notify.{key}" for key in hass.services.async_services().get("notify", {}) if key != "send_message"]
    fields = {}
    for key, default in DEFAULTS.items():
        value = values.get(key, default)
        if key == "notification_service":
            fields[vol.Required(key, default=value)] = selector.SelectSelector(
                selector.SelectSelectorConfig(options=sorted(set(services + [value])), mode=selector.SelectSelectorMode.DROPDOWN))
        else:
            fields[vol.Required(key, default=value)] = selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.1, max=10000 if key in ("warning", "high", "recovery") else 168, step=0.1, mode=selector.NumberSelectorMode.BOX))
    return vol.Schema(fields)


def errors_for(data):
    return {} if data["recovery"] < data["warning"] < data["high"] else {"base": "invalid_thresholds"}


class RadonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """One entry per source sensor."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            source = user_input["source"]
            await self.async_set_unique_id(source)
            self._abort_if_unique_id_configured()
            state = self.hass.states.get(source)
            if state is None or state.attributes.get("unit_of_measurement") not in ("Bq/m³", "Bq/m3", "pCi/L"):
                errors["base"] = "invalid_unit"
            elif source.startswith("sensor.radon_monitor_") or state.attributes.get("radon_monitor_derived"):
                errors["base"] = "derived_source"
            else:
                return self.async_create_entry(title=user_input["name"], data=user_input)
        return self.async_show_form(step_id="user", errors=errors, data_schema=vol.Schema({
            vol.Required("name", default="Radon Monitor"): str,
            vol.Required("source"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        }))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RadonOptionsFlow()


class RadonOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = errors_for(user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init", errors=errors, data_schema=options_schema(self.hass, user_input or self.config_entry.options))
