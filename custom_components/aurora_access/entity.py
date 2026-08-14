from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AuroraDataUpdateCoordinator


class AuroraEntity(CoordinatorEntity[AuroraDataUpdateCoordinator]):
    def __init__(
        self,
        coordinator: AuroraDataUpdateCoordinator,
        area: dict[str, Any],
        device: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self.area_id = str(area["id"])
        self.device_id = str(device["id"])
        self.device_data = device
        self._attr_name = device.get("name")
        self._attr_icon = "mdi:shield-lock"
        self._attr_unique_id = device.get("unique_id") or f"{DOMAIN}_{self.device_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": device.get("name"),
            "manufacturer": "Aurora",
            "model": "Access Control",
            "icon": "mdi:shield-lock",
            "suggested_area": area.get("name"),
        }
        self._mqtt_unsubscribe = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        topic = self.device_data.get("state_topic")
        if not topic:
            return

        try:
            self._mqtt_unsubscribe = await mqtt.async_subscribe(
                self.hass,
                topic,
                self._async_mqtt_message,
                qos=1,
            )
        except Exception:
            logging.getLogger("aurora_access").warning(
                "MQTT state subscription unavailable for %s", topic, exc_info=True
            )

    async def async_will_remove_from_hass(self) -> None:
        if self._mqtt_unsubscribe is not None:
            self._mqtt_unsubscribe()
            self._mqtt_unsubscribe = None
        await super().async_will_remove_from_hass()

    async def _async_mqtt_message(self, message) -> None:
        self.coordinator.apply_mqtt_state(self.device_type, self.device_id, message.payload)

    @property
    def current_device(self) -> dict[str, Any]:
        for area, device in self.coordinator.devices(self.device_type):
            if str(device.get("id")) == self.device_id and str(area.get("id")) == self.area_id:
                return device
        return self.device_data

    @property
    def device_type(self) -> str:
        raise NotImplementedError

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
