# Architecture Overview

This document describes the current Sony Projector custom integration architecture.

## Directory Structure

```text
custom_components/sony_projector/
├── __init__.py                  # Integration setup, coordinator, platforms
├── api/                         # Wrapper around sony_projector_protocol
├── config_flow.py               # Home Assistant config flow entry point
├── config_flow_handler/         # Config flow, schemas, validation
├── const.py                     # Constants
├── coordinator/                 # Lifecycle-aware DataUpdateCoordinator
├── data.py                      # Runtime dataclasses and typed config entry
├── diagnostics.py               # Diagnostics with sensitive data redaction
├── discovery.py                 # Shared SDAP UDP listener and advertisement cache
├── entity/                      # Base entity class
├── entity_utils/                # Device info and state helpers
├── media_player/                # Projector power/source entity
├── select/                      # Protocol-specific projector controls
├── repairs.py                   # Repair flow entry point
├── sensor/                      # Power status, IP address, and lamp timer sensors
├── services.yaml                # Empty in v1; controls use media_player services
└── translations/                # Home Assistant translations
```

## Runtime Components

### Protocol Boundary

The integration does not implement Sony wire protocols directly. It uses the external `sony_projector_protocol` library for SDCP, ADCP, and SDAP parsing.

Protocol-library changes must be made in the separate `sony_projector_protocol` repository and then pulled into this integration through the dependency pin.

### API Client

`api/client.py` is a Home Assistant friendly wrapper around the protocol library.

Responsibilities:

- Create short-lived protocol connections
- Normalize power status values to Sony protocol state names
- Translate protocol exceptions to integration exceptions
- Read identity, power, input, and lamp timer data
- Send power and input commands

### Discovery Manager

`discovery.py` owns one shared UDP listener for SDAP advertisements.

Responsibilities:

- Listen on UDP port `53862`
- Parse advertisements through `sony_projector_protocol`
- Cache discovered projectors for config flow setup
- Update loaded config entries when projector host changes
- Forward matching advertisements to the coordinator

### Coordinator

`coordinator/base.py` owns projector lifecycle state.

The coordinator has two polling modes:

- Passive mode: poll only power status
- Active mode: poll power, input, optional lamp timer, ADCP signal, and protocol-specific select state

SDAP advertisements can update power state without waiting for the next poll. The coordinator stores normalized spec-state strings so polling and discovery produce consistent entity states.

### Config Flow

`config_flow_handler/config_flow.py` supports:

- Initial setup through SDAP discovery or manual host entry
- A short discovery wait step before the first user form
- Reconfigure with identity validation
- SDCP community and ADCP password inputs

The options flow currently has no configurable settings.

### Entities

Current platforms:

- `media_player`: turn on, turn off, select source
- `select`: ADCP picture mode or SDCP calibration preset
- `sensor`: power status, IP address, and lamp timer

Entities read from coordinator data and do not call the API client directly.

## Data Flow

```text
SDAP advertisements ─┐
                     ▼
Protocol library -> API client -> Coordinator -> Entities
                     ▲
Manual commands -----┘
```

## Power States

Power states are reported using Sony protocol names:

- `standby`
- `start_up`
- `start_up_lamp`
- `on`
- `cooling`
- `cooling2`

The media player maps these to Home Assistant's logical on/off state, but the power status sensor preserves the protocol state name.

## Development Notes

- Use project scripts for validation and Home Assistant runtime.
- Keep protocol fixes out of this repository.
- Add new entities through the existing platform directories.
- Add custom service actions only when media player services are not sufficient.
