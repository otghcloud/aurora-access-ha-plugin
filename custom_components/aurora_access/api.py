from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

_LOGGER = logging.getLogger(__name__)


class AuroraApiError(Exception):
    """Base exception for Aurora API failures."""


class AuroraApiAuthError(AuroraApiError):
    """Raised when Aurora rejects the configured token."""


class AuroraApiClient:
    def __init__(self, session: ClientSession, base_url: str, token: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async def async_close(self) -> None:
        # The Home Assistant-owned session must not be closed here.
        return

    async def async_get_status(self) -> dict[str, Any]:
        return await self._request("GET", "/api/ha/status")

    async def async_send_command(
        self,
        *,
        command_type: str,
        device_id: str,
        action: str,
        area_id: str,
        value: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": command_type,
            "device_id": device_id,
            "action": action,
            "area_id": int(area_id),
        }
        if value is not None:
            payload["value"] = value
        return await self._request("POST", "/api/ha/webhook", json=payload)

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            async with self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=self._headers,
                timeout=30,
                **kwargs,
            ) as response:
                if response.status in (401, 403):
                    raise AuroraApiAuthError("Aurora API authentication failed")
                response_text = await response.text()
                if response.status >= 400:
                    _LOGGER.error(
                        "Aurora API request failed with HTTP %s: %s",
                        response.status,
                        response_text[:1000],
                    )
                    raise AuroraApiError(
                        f"Aurora API returned HTTP {response.status}: {response_text[:300]}"
                    )
                try:
                    data = await response.json(content_type=None)
                except ValueError as err:
                    raise AuroraApiError("Aurora API returned invalid JSON") from err
                if not isinstance(data, dict):
                    raise AuroraApiError("Aurora API returned an invalid response")
                return data
        except AuroraApiError:
            raise
        except ClientResponseError as err:
            _LOGGER.error("Aurora API request failed with HTTP %s: %s", err.status, path)
            raise AuroraApiError(f"Aurora API returned HTTP {err.status}") from err
        except (ClientError, TimeoutError) as err:
            _LOGGER.error("Aurora API request could not connect to %s: %s", path, err)
            raise AuroraApiError("Unable to connect to Aurora API") from err
        except Exception as err:
            _LOGGER.exception("Unexpected Aurora API response failure for %s: %s", path, err)
            raise AuroraApiError("Aurora API returned an unexpected response") from err
