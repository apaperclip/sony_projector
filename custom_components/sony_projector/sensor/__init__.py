"""Sensor platform for Sony Projector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.const import CONF_PROTOCOL, PARALLEL_UPDATES as PARALLEL_UPDATES, PROTOCOL_ADCP

from .error import SonyProjectorErrorSensor
from .ip_address import SonyProjectorIpAddressSensor
from .lamp_timer import SonyProjectorLampTimerSensor
from .power_status import SonyProjectorPowerStatusSensor
from .signal import SonyProjectorSignalSensor
from .warning import SonyProjectorWarningSensor

if TYPE_CHECKING:
    from custom_components.sony_projector.data import SonyProjectorConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SonyProjectorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    entities = [
        SonyProjectorPowerStatusSensor(entry.runtime_data.coordinator),
        SonyProjectorIpAddressSensor(entry.runtime_data.coordinator),
        SonyProjectorLampTimerSensor(entry.runtime_data.coordinator),
        SonyProjectorErrorSensor(entry.runtime_data.coordinator),
    ]
    if entry.data[CONF_PROTOCOL] == PROTOCOL_ADCP:
        entities.append(SonyProjectorSignalSensor(entry.runtime_data.coordinator))
        entities.append(SonyProjectorWarningSensor(entry.runtime_data.coordinator))
    async_add_entities(entities)
