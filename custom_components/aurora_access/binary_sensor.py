from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .entity import AuroraEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aurora_access"][entry.entry_id]
    async_add_entities(
        AuroraBinarySensor(coordinator, area, device)
        for area, device in coordinator.devices("sensors")
    )


class AuroraBinarySensor(AuroraEntity, BinarySensorEntity):
    _attr_icon = "mdi:shield-home"

    @property
    def device_type(self) -> str:
        return "sensors"

    @property
    def is_on(self) -> bool:
        state = self.current_device.get("state")
        if self.device_class in (BinarySensorDeviceClass.DOOR, BinarySensorDeviceClass.WINDOW):
            return state == "off"
        return state == "on"

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        value = self.current_device.get("device_class")
        try:
            return BinarySensorDeviceClass(value) if value else None
        except ValueError:
            return None

    @property
    def available(self) -> bool:
        return bool(self.current_device.get("available", True)) and super().available
