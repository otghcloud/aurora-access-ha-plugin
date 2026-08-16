from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTime

from .entity import AuroraLockConfigurationEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aurora_access"][entry.entry_id]
    async_add_entities(
        AuroraAutolockDurationNumber(coordinator, area, device)
        for area, device in coordinator.devices("locks")
    )


class AuroraAutolockDurationNumber(AuroraLockConfigurationEntity, NumberEntity):
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_icon = "mdi:timer-lock"
    _attr_name = "Auto-lock delay"
    _attr_native_max_value = 3600
    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_mode = NumberMode.BOX
    _attr_translation_key = "autolock_duration"

    def __init__(self, coordinator, area: dict[str, Any], device: dict[str, Any]) -> None:
        super().__init__(coordinator, area, device, "autolock_duration")

    @property
    def native_value(self) -> float | None:
        value = self.autolock.get("duration_seconds")
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        duration = int(value)
        if value != duration or not 0 <= duration <= 3600:
            raise ValueError("Auto-lock duration must be a whole number between 0 and 3600 seconds")

        await self.coordinator.client.async_send_command(
            command_type="autolock_command",
            device_id=self.lock_unique_id,
            action="set_duration",
            area_id=self.area_id,
            value=str(duration),
        )
        await self.coordinator.async_request_refresh()
