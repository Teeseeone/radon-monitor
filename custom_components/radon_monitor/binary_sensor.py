"""Sustained alert and source health indicators."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .entity import RadonEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RadonBinary(entry.runtime_data, key, name) for key, name in (("elevated", "Sustained elevated radon"), ("high", "Sustained high radon"), ("problem", "Sensor problem"))])


class RadonBinary(RadonEntity, BinarySensorEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self.key = key
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self):
        if self.key == "problem":
            return self.coordinator.data["value"] is None
        alert = self.coordinator.alerts.data["alert"]
        return alert in ("elevated", "high") if self.key == "elevated" else alert == "high"
