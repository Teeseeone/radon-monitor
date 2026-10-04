"""Current concentration, status and historical averages."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from .engine import PERIODS
from .entity import RadonEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([RadonValue(c), RadonStatus(c)] + [RadonAverage(c, key) for key in PERIODS])


class RadonValue(RadonEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.RADON
    _attr_native_unit_of_measurement = "Bq/m³"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator):
        super().__init__(coordinator, "concentration", "Concentration")

    @property
    def native_value(self):
        return self.coordinator.data["value"]

    @property
    def extra_state_attributes(self):
        return {"radon_monitor_derived": True, "source": self.coordinator.source}


class RadonStatus(RadonEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["normal", "watch", "elevated", "high", "sensor_problem"]
    _attr_icon = "mdi:radioactive"

    def __init__(self, coordinator):
        super().__init__(coordinator, "status", "Status")

    @property
    def native_value(self):
        return self.coordinator.data["status"]

    @property
    def extra_state_attributes(self):
        return {"sustained_alert": self.coordinator.alerts.data["alert"], "source_age_seconds": self.coordinator.data["source_age_seconds"], "history_error": self.coordinator.data["history_error"], "weekly_trend": self.coordinator.data["weekly_trend"]}


class RadonAverage(RadonEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.RADON
    _attr_native_unit_of_measurement = "Bq/m³"
    _attr_suggested_display_precision = 1
    # Deliberately no state_class: do not generate statistics of rolling averages.

    def __init__(self, coordinator, key):
        super().__init__(coordinator, key, f"{key.replace('_', ' ')} average")
        self.key = key

    @property
    def native_value(self):
        return self.coordinator.data["averages"][self.key]["value"]

    @property
    def extra_state_attributes(self):
        info = self.coordinator.data["averages"][self.key]
        return {"radon_monitor_derived": True, **{k: v for k, v in info.items() if k != "value"}, "calculation": "Hourly means of source sensor; coverage is hourly bucket availability"}
