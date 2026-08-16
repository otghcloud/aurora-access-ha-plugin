from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity

from .entity import AuroraLockConfigurationEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aurora_access"][entry.entry_id]
    async_add_entities(
        AuroraAutolockSwitch(coordinator, area, device)
        for area, device in coordinator.devices("locks")
    )


class AuroraAutolockSwitch(AuroraLockConfigurationEntity, SwitchEntity):
    _attr_icon = "mdi:lock-clock"
    _attr_name = "Auto-lock enabled"
    _attr_translation_key = "autolock"

    def __init__(self, coordinator, area: dict[str, Any], device: dict[str, Any]) -> None:
        super().__init__(coordinator, area, device, "autolock")

    @property
    def is_on(self) -> bool | None:
        enabled = self.autolock.get("enabled")
        return bool(enabled) if enabled is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_enabled(False)

    async def _async_set_enabled(self, enabled: bool) -> None:
        await self.coordinator.client.async_send_command(
            command_type="autolock_command",
            device_id=self.lock_unique_id,
            action="set_enabled",
            area_id=self.area_id,
            value="1" if enabled else "0",
        )
        await self.coordinator.async_request_refresh()
