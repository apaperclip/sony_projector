# Getting Started

This guide covers installing and adding the Sony Projector integration to Home Assistant.

## Prerequisites

- Home Assistant 2026.4.0 or newer
- HACS 2.0.5 or newer for HACS installation
- Network access from Home Assistant to the projector
- A Sony projector that supports SDCP or ADCP

## Installation

### HACS

1. Open HACS.
2. Go to **Integrations**.
3. Add `https://github.com/apaperclip/sony_projector` as a custom repository.
4. Download **Sony Projector**.
5. Restart Home Assistant.

### Manual

1. Download the latest release from GitHub.
2. Copy `custom_components/sony_projector/` into your Home Assistant configuration directory.
3. Restart Home Assistant.

## Initial Setup

1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration**.
3. Search for **Sony Projector**.
4. Choose **Listen for discovery (up to 60 seconds)** or **Add manually**.
5. If listening, wait for the discovery screen to find projectors, then select the projector to add.
   If no projector is found within 60 seconds, choose **Search again** or **Add manually**.
6. If adding manually, enter the projector host/IP address.
7. Choose `sdcp` or `adcp`.
8. Keep the default community/password unless your projector is configured differently.

Discovered projectors are shown with model, IP address, and serial number when those fields are available.

## Created Entities

The integration creates one device for each config entry.

The default entities are:

- `media_player.<projector>_projector`
- `sensor.<projector>_power_status`
- `sensor.<projector>_lamp_timer`

The lamp timer sensor is diagnostic and disabled by default.

## First Dashboard Card

```yaml
type: entities
title: Sony Projector
entities:
  - media_player.vpl_vw285es_projector
  - sensor.vpl_vw285es_power_status
  - sensor.vpl_vw285es_lamp_timer
```

Replace the entity IDs with the ones Home Assistant created for your projector.

## Troubleshooting

### Discovery Does Not Show the Projector

- Confirm Home Assistant and the projector are on the same network segment.
- Confirm UDP traffic on port `53862` is not blocked.
- Choose **Listen for discovery** and keep the search screen open for up to 60 seconds.
- If no projector is found, choose **Search again** or add the projector manually.
- Add the projector manually by IP address if SDAP discovery is unavailable.

### Setup Fails

- Check the projector IP address.
- Try the other protocol if your model supports it.
- Confirm the SDCP community or ADCP password.
- Review Home Assistant logs for `custom_components.sony_projector`.

## Next Steps

- See [CONFIGURATION.md](./CONFIGURATION.md) for setup fields and entity details.
- See [EXAMPLES.md](./EXAMPLES.md) for automation and dashboard examples.
