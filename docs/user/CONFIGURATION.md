# Configuration Reference

This page describes the current configuration surface for the Sony Projector integration.

## Setup Fields

| Field                | Required | Default     | Description                                                                            |
| -------------------- | -------- | ----------- | -------------------------------------------------------------------------------------- |
| Discovered projector | No       | -           | SDAP-discovered projector to add                                                       |
| Host or IP address   | Manual   | -           | Projector hostname or IP address                                                       |
| Protocol             | Yes      | `sdcp`      | `sdcp` or `adcp`                                                                       |
| SDCP community       | SDCP     | `SONY`      | Community string used for SDCP communication                                           |
| ADCP password        | ADCP     | `Projector` | Password used for ADCP communication; leave blank when ADCP authentication is disabled |

When a discovered projector is selected, the host is filled from the SDAP advertisement.

The first setup screen asks whether to listen for discovery or add manually. The discovery path shows a searching progress screen for up to 60 seconds. If one or more projectors are found, the next screen lists them so the right projector can be selected. If none are found, the flow offers **Search again** or **Add manually**.

## Discovery

The integration listens for Sony SDAP advertisements on UDP port `53862`.

Discovery is used for:

- Showing projectors in the setup flow
- Updating the stored host if the projector IP changes
- Updating passive power status from advertisement packets
- If a projector is manually added do not depend on discovery packets for passive state information, instead only use polling.

## Reconfigure

Use **Settings** -> **Devices & Services** -> **Sony Projector** -> **Reconfigure** to update connection settings.

The reconfigure flow validates that the new host is the same projector by checking the stable identity exposed by the device.

## Options

There are no configurable options in v1. The options flow is present only to provide a stable place for future settings.

## Entities

Add the calibration preset entity to SDCP
Add the picture mode settting to ADCP

## Device

Device info should have serial number

### Media Player

The media player supports:

- Turn on
- Turn off
- Select source

Default sources are `hdmi1` and `hdmi2`.

The media player uses the projector's lifecycle state for logical on/off. Startup states such as `start_up` and `start_up_lamp` display as on. Cooling states such as `cooling` and `cooling2` display as off. The power status sensor keeps the exact protocol state for automations that need transition details.

### Power Status Sensor

The power status sensor reports Sony protocol state names:

| State           | Meaning                                   |
| --------------- | ----------------------------------------- |
| `standby`       | Projector is off or in standby            |
| `start_up`      | Projector is starting                     |
| `start_up_lamp` | Lamp/startup sequence is in progress      |
| `on`            | Projector is operational                  |
| `cooling`       | Projector is cooling down                 |
| `cooling2`      | Secondary cooling state from the protocol |

### Lamp Timer Sensor

The lamp timer sensor is diagnostic and enabled by default. It becomes available only when the projector is operational and the model/protocol supports reading lamp hours.

## Services

The integration does not define custom service actions in v1. Use the media player services provided by Home Assistant:

- `media_player.turn_on`
- `media_player.turn_off`
- `media_player.select_source`

## Diagnostics

Diagnostics include config entry data, coordinator state, projector identity, and the last SDAP advertisement. Sensitive values such as ADCP password and SDCP community are redacted.

Add a diagnostic sensor of last seen that has the timestamp of the last received disovery advertisment packet for that specific projector.

## Error handling

If the projector is not available for when it is polled, the entites should all be unavailable.
