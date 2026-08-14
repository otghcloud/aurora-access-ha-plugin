from __future__ import annotations

import colorsys
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity

from .entity import AuroraEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = hass.data["aurora_access"][entry.entry_id]
    async_add_entities(
        AuroraLight(coordinator, area, device)
        for area, device in coordinator.devices("lights")
    )


class AuroraLight(AuroraEntity, LightEntity):
    _attr_icon = "mdi:shield-light"

    @property
    def device_type(self) -> str:
        return "lights"

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        device = self.current_device
        modes = {ColorMode.ONOFF}
        if "brightness" in device:
            modes.add(ColorMode.BRIGHTNESS)
        if "color" in device:
            modes.add(ColorMode.HS)
        return modes

    @property
    def color_mode(self) -> ColorMode:
        modes = self.supported_color_modes
        if ColorMode.HS in modes:
            return ColorMode.HS
        if ColorMode.BRIGHTNESS in modes:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    @property
    def is_on(self) -> bool:
        return self.current_device.get("state") == "on"

    @property
    def brightness(self) -> int | None:
        value = self.current_device.get("brightness")
        return round(int(value) * 255 / 100) if value is not None else None

    @property
    def hs_color(self) -> tuple[float, float] | None:
        color = self.current_device.get("color")
        if not color or not isinstance(color, str) or not color.startswith("#"):
            return None
        try:
            red = int(color[1:3], 16) / 255
            green = int(color[3:5], 16) / 255
            blue = int(color[5:7], 16) / 255
        except ValueError:
            return None
        hue, saturation, _ = colorsys.rgb_to_hsv(red, green, blue)
        return hue * 360, saturation * 100

    @property
    def available(self) -> bool:
        return bool(self.current_device.get("available", True)) and super().available

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness = kwargs.get("brightness")
        if brightness is not None:
            value = str(round(int(brightness) * 100 / 255))
            action = "brightness"
        else:
            value = None
            action = "on"
        await self.coordinator.client.async_send_command(
            command_type="light_command",
            device_id=self._attr_unique_id,
            action=action,
            area_id=self.area_id,
            value=value,
        )
        hs_color = kwargs.get("hs_color")
        if hs_color is not None:
            await self.coordinator.client.async_send_command(
                command_type="light_command",
                device_id=self._attr_unique_id,
                action="color",
                area_id=self.area_id,
                value=self._hs_to_hex(hs_color),
            )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_send_command(
            command_type="light_command",
            device_id=self._attr_unique_id,
            action="off",
            area_id=self.area_id,
        )
        await self.coordinator.async_request_refresh()

    @staticmethod
    def _hs_to_hex(hs_color: tuple[float, float]) -> str:
        red, green, blue = colorsys.hsv_to_rgb(hs_color[0] / 360, hs_color[1] / 100, 1)
        return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"
