# Aurora Access Control for Home Assistant

A Home Assistant custom integration for Aurora Access Control. It polls the Aurora API for locks, binary sensors, and lights, and sends control commands through the authenticated Aurora webhook API.

## Installation

### HACS

1. Add this repository as a custom HACS repository with category **Integration**.
2. Install **Aurora Access Control**.
3. Restart Home Assistant.
4. Add the integration from **Settings -> Devices & services**.

### Manual

Copy `custom_components/aurora_access` into the Home Assistant configuration directory:

```bash
cp -R custom_components/aurora_access \
  /config/custom_components/aurora_access
```

Restart Home Assistant and add the integration through the UI.

## Configuration

- **API base URL:** The Aurora application URL, without a trailing slash.
- **API token:** A Sanctum bearer token with permission to the desired areas.
- **Area ID:** Optional numeric area filter. Leave empty to expose all permitted areas.

The integration subscribes to Aurora MQTT state topics for live lock and sensor updates. It also polls `GET /api/ha/status` every 5 seconds by default as a recovery fallback. Change the fallback interval from the integration's **Configure** options in Home Assistant; valid values are 2-300 seconds. Device commands are sent to `POST /api/ha/webhook` with the configured token.

For live updates, configure Home Assistant's MQTT integration against the same broker used by Aurora. If MQTT is unavailable, entities remain functional through HTTP polling.

## Supported Platforms

- `lock`: Lock and unlock doors.
- `binary_sensor`: Read Aurora sensor state and device class.
- `light`: Turn lights on/off and control brightness or color when supported.

## Development

Compile-check the Python package locally with:

```bash
python3 -m compileall -q custom_components
```

The integration expects the API contract documented in `../docs/home-assistant.md`.
