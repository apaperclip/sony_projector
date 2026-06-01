# Sony Projector

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

Home Assistant custom integration for Sony projectors using the local SDCP/ADCP protocols.

## Features

- Local control, no cloud account required
- UI setup with SDAP discovery or manual host entry
- Media player entity for power and HDMI source selection
- Capability-backed HDMI/source selection
- Protocol-specific picture mode, calibration preset, and color space selects
- Power status sensor using protocol state names
- ADCP signal diagnostic sensor
- Projector error and warning diagnostic sensors
- Lamp timer diagnostic sensor
- SDAP advertisements for passive availability and power-state updates

## Platforms

| Platform       | Description                                                     |
| -------------- | --------------------------------------------------------------- |
| `media_player` | Projector power control and capability-backed source selection  |
| `select`       | Picture mode for ADCP, calibration preset for SDCP, color space |
| `sensor`       | Power status, IP address, error/warning, and lamp diagnostics   |

## Installation

### HACS

1. Open HACS in Home Assistant.
2. Go to **Integrations**.
3. Add `https://github.com/apaperclip/sony_projector` as a custom repository with category **Integration**.
4. Download **Sony Projector**.
5. Restart Home Assistant.

### Manual

1. Download the latest release.
2. Copy `custom_components/sony_projector/` into your Home Assistant configuration directory.
3. Restart Home Assistant.

## Setup

1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration**.
3. Search for **Sony Projector**.
4. Choose **Listen for discovery (up to 60 seconds)** or **Add manually**.
5. If listening, wait for the discovery screen to find projectors, then select the projector to add.
   If no projector is found within 60 seconds, choose **Search again** or **Add manually**.
6. If adding manually, enter the projector host/IP address.
7. Choose the protocol:
   - `adcp`: recommended default. Uses password `Projector` unless changed; leave blank if ADCP authentication is disabled on the projector.
   - `sdcp`: uses community `SONY` unless changed.
8. Submit the form.

The discovery picker shows the model, IP address, and serial number when SDAP advertisements are received.

## Entities

### Media Player

The projector media player supports:

- Turn on
- Turn off
- Select source

The source list comes from the model capability matrix in `sony_projector_protocol`. If the projector reports a different active source, the integration keeps that value in the source list.

### Power Status Sensor

The power status sensor reports the protocol state name:

- `standby`
- `start_up`
- `start_up_lamp`
- `on`
- `cooling`
- `cooling2`

### Lamp Timer Sensor

The lamp timer is a diagnostic sensor. Some models or protocols may not support reading the lamp timer.

## Troubleshooting

### Projector Not Discovered

- Confirm the projector and Home Assistant are on the same network segment.
- Confirm UDP SDAP advertisements can reach Home Assistant on port `53862`.
- Open the integration setup window and wait for the discovery search to finish.
- If discovery still does not appear, add the projector manually by IP address.

### Cannot Connect

- Verify the projector IP address.
- Confirm the selected protocol is supported by the model.
- For SDCP, confirm the community string.
- For ADCP, confirm the password.
- Check **Settings** -> **System** -> **Logs** for `custom_components.sony_projector` messages.

### Power State Looks Wrong

The integration intentionally reports Sony protocol power states exactly. During power transitions, `start_up`, `start_up_lamp`, `cooling`, and `cooling2` are expected.
The media player maps startup states to on and cooling states to off; use the power status sensor when automations need exact transition states.

## Development

Use the project scripts from the devcontainer:

```bash
script/develop
script/python
script/type-check
script/test
```

See [AGENTS.md](AGENTS.md) for agent and development workflow rules.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

[commits-shield]: https://img.shields.io/github/commit-activity/y/apaperclip/sony_projector.svg?style=for-the-badge
[commits]: https://github.com/apaperclip/sony_projector/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/apaperclip/sony_projector.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40apaperclip-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/apaperclip/sony_projector.svg?style=for-the-badge
[releases]: https://github.com/apaperclip/sony_projector/releases
