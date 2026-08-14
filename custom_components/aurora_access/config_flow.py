from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlowWithConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .api import AuroraApiAuthError, AuroraApiClient, AuroraApiError
from .const import (
    CONF_AREA_ID,
    CONF_BASE_URL,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_SCAN_INTERVAL_SECONDS,
)


async def _validate_input(hass: HomeAssistant, data: dict[str, str]) -> None:
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    client = AuroraApiClient(async_get_clientsession(hass), data[CONF_BASE_URL], data[CONF_TOKEN])
    await client.async_get_status()


class AuroraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithConfigEntry:
        return AuroraOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, str] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await _validate_input(self.hass, user_input)
            except AuroraApiAuthError:
                errors["base"] = "invalid_auth"
            except AuroraApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_BASE_URL].rstrip("/"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default="https://api.example.com"): str,
                vol.Required(CONF_TOKEN): str,
                vol.Optional(CONF_AREA_ID): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class AuroraOptionsFlow(OptionsFlowWithConfigEntry):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL_SECONDS,
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_SCAN_INTERVAL_SECONDS,
                        max=MAX_SCAN_INTERVAL_SECONDS,
                    ),
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
