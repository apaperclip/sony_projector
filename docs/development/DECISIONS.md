# Architectural and Design Decisions

This document records decisions that are specific to the Sony Projector integration.

## Decision Log

### Use External Protocol Library

**Context:** SDCP, ADCP, and SDAP parsing are protocol concerns that can evolve independently from the Home Assistant integration.

**Decision:** Keep Sony protocol implementation in the separate `sony_projector_protocol` library and consume it from this integration.

**Rationale:**

- Keeps Home Assistant code focused on entity, config flow, and coordinator behavior
- Allows protocol fixes to be tested and released independently
- Avoids local patches to installed dependencies

**Consequences:**

- Protocol bugs must be fixed upstream, then repulled here
- The integration wraps and normalizes the public library API
- Installed `sony_projector_protocol` files must not be edited in this repository

### Use SDAP Discovery for Setup and Passive Updates

**Context:** Sony projectors advertise identity, host, and power information over SDAP.

**Decision:** Run one shared SDAP listener and cache advertisements for config flow and loaded entries.

**Rationale:**

- Projectors can be discovered without manually typing an IP address
- IP changes can update the config entry host
- Advertisement power states reduce reliance on active polling

**Consequences:**

- Discovery depends on UDP traffic reaching Home Assistant
- Manual setup remains necessary when SDAP is unavailable
- Config flow includes a short discovery wait before showing the user form

### Preserve Protocol Power State Names

**Context:** Sony exposes lifecycle states such as `start_up_lamp` and `cooling2`.

**Decision:** Report power status using the exact protocol state names.

**Rationale:**

- Avoids hiding useful lifecycle detail
- Prevents mismatch between polled data and advertisement data
- Makes debugging with protocol logs easier

**Consequences:**

- Automations should use protocol states such as `start_up`, `on`, and `cooling2`
- Media player logical state is derived separately from the status sensor

### Use Media Player as the Primary Control Surface

**Context:** Projector power and input selection map naturally to Home Assistant media player behavior.

**Decision:** Expose projector control through a `media_player` entity first.

**Rationale:**

- Uses familiar Home Assistant services
- Avoids custom service actions for standard power/source operations
- Keeps v1 small and focused

**Consequences:**

- `services.yaml` is intentionally empty for v1
- Additional entities or service actions should be added only when they expose behavior not covered by media player services

### Use Lifecycle-Aware Polling

**Context:** Some projector commands are only available when the projector is fully operational.

**Decision:** Poll power status passively when the projector is off or transitioning, and poll active data only when operational or logically on.

**Rationale:**

- Avoids unsupported commands during standby/cooling
- Keeps off-state polling lightweight
- Still refreshes quickly during power transitions

**Consequences:**

- Lamp timer and input are only available in active mode
- Power transition confirmation polling is separate from normal update intervals

## Future Considerations

### More Sources

The default source list is `hdmi1` and `hdmi2`. Add model-aware source discovery if the protocol library exposes it.

### Additional Projector Controls

Future entities or service actions may cover picture modes, lens memory, calibration presets, or blanking if the protocol library supports them.

### Tests

The current focused tests cover API wrapper behavior and SDAP discovery. Broader coordinator and config-flow tests would be useful as behavior stabilizes.
