from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity

from .entity import AuroraEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aurora_access"][entry.entry_id]
    async_add_entities(
        AuroraLock(coordinator, area, device)
        for area, device in coordinator.devices("locks")
    )


class AuroraLock(AuroraEntity, LockEntity):
    _attr_code_format = None

    @property
    def device_type(self) -> str:
        return "locks"

    @property
    def is_locked(self) -> bool | None:
        state = self.current_device.get("state")
        if state == "locked":
            return True
        if state == "unlocked":
            return False
        return None

    @property
    def available(self) -> bool:
        return bool(self.current_device.get("available", True)) and super().available

    async def async_lock(self, **kwargs: Any) -> None:
        # Aurora locks do not use PIN/code authentication.
        kwargs.pop("code", None)
        await self.coordinator.client.async_send_command(
            command_type="lock_command",
            device_id=self._attr_unique_id,
            action="lock",
            area_id=self.area_id,
        )
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        # Aurora locks do not use PIN/code authentication.
        kwargs.pop("code", None)
        await self.coordinator.client.async_send_command(
            command_type="lock_command",
            device_id=self._attr_unique_id,
            action="unlock",
            area_id=self.area_id,
        )
        await self.coordinator.async_request_refresh()
