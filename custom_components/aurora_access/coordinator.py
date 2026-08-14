from __future__ import annotations

import logging
from datetime import timedelta
import json
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AuroraApiClient, AuroraApiError
from .const import (
    CONF_AREA_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_SCAN_INTERVAL_SECONDS,
)


class AuroraDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        client: AuroraApiClient,
        entry: ConfigEntry,
    ) -> None:
        self.client = client
        self.area_id = entry.data.get(CONF_AREA_ID)
        try:
            configured_interval = int(
                entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)
            )
        except (TypeError, ValueError):
            configured_interval = DEFAULT_SCAN_INTERVAL_SECONDS
        scan_interval = max(
            MIN_SCAN_INTERVAL_SECONDS,
            min(
                MAX_SCAN_INTERVAL_SECONDS,
                configured_interval,
            ),
        )
        super().__init__(
            hass,
            logger=logging.getLogger(DOMAIN),
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            payload = await self.client.async_get_status()
        except AuroraApiError as err:
            raise UpdateFailed(str(err)) from err

        if self.area_id is None:
            return payload

        selected = [
            area for area in payload.get("areas", [])
            if str(area.get("id")) == str(self.area_id)
        ]
        return {
            **payload,
            "areas": selected,
            "device_count": sum(
                len(area.get("devices", {}).get(device_type, []))
                for area in selected
                for device_type in ("locks", "sensors", "lights")
            ),
        }

    def devices(self, device_type: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        devices: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for area in (self.data or {}).get("areas", []):
            for device in area.get("devices", {}).get(device_type, []):
                devices.append((area, device))
        return devices

    def apply_mqtt_state(self, device_type: str, device_id: str, payload: str) -> None:
        try:
            message = json.loads(payload)
        except json.JSONDecodeError:
            return

        if not isinstance(message, dict):
            return

        data = dict(self.data or {})
        areas = []
        changed = False
        for area in data.get("areas", []):
            updated_area = dict(area)
            devices = []
            for device in area.get("devices", {}).get(device_type, []):
                updated_device = dict(device)
                if str(device.get("id")) == str(device_id):
                    if device_type == "locks" and "lock_power" in message:
                        updated_device["state"] = "locked" if int(message["lock_power"]) else "unlocked"
                        updated_device["available"] = True
                        changed = True
                    elif device_type == "sensors" and "state" in message:
                        updated_device["state_raw"] = bool(message["state"])
                        updated_device["state"] = "on" if updated_device["state_raw"] else "off"
                        changed = True
                devices.append(updated_device)
            updated_area["devices"] = {
                **area.get("devices", {}),
                device_type: devices,
            }
            areas.append(updated_area)

        if changed:
            self.async_set_updated_data({**data, "areas": areas})
