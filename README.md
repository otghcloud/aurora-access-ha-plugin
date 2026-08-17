[<img src="https://otgh-static-assets.s3.otgh.cloud/branding/logos/otgh_cloud_2024.png" width="200px" />](https://github.com/otghcloud/aurora-manage)

# Aurora Access Control for Home Assistant

A Home Assistant custom integration for Aurora Access Control. It polls the Aurora API for locks, binary sensors, lights, and lock configuration, and sends control commands through the authenticated Aurora webhook API.

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

The integration subscribes to Aurora MQTT state topics for live lock, sensor, light, and auto-lock updates. It also polls `GET /api/ha/status` every 5 seconds by default as a recovery fallback. Change the fallback interval from the integration's **Configure** options in Home Assistant; valid values are 2-300 seconds. Device commands are sent to `POST /api/ha/webhook` with the configured token.

For live updates, configure Home Assistant's MQTT integration against the same broker used by Aurora Access Control. If MQTT is unavailable, entities remain functional through HTTP polling.

## Supported Platforms

- `lock`: Lock and unlock doors.
- `binary_sensor`: Read Aurora sensor state and device class.
- `light`: Turn lights on/off and control brightness or color when supported.
- `switch`: Enable or disable auto-lock for an individual lock.
- `number`: Set an individual lock's auto-lock timeout from 0 to 3600 seconds.

## Auto-lock Controls

Each lock device includes an **Auto-lock** switch and **Auto-lock timeout** number entity. The entities initially show the lock's effective policy, including any inherited area default. Changing either entity creates an explicit per-lock override while preserving the other setting: toggling auto-lock keeps the current timeout, and changing the timeout keeps the current enabled state.

Clear a lock override from the Aurora Access admin interface to return the lock to its area default. Auto-lock configuration is synchronized immediately through the lock's retained MQTT state topic, with HTTP polling providing recovery if MQTT is unavailable.