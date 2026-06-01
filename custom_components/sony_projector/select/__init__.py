"""Select platform for Sony Projector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.const import (
    CONF_PROTOCOL,
    PARALLEL_UPDATES as PARALLEL_UPDATES,
    PROTOCOL_ADCP,
    PROTOCOL_SDCP,
)

from .calibration_preset import SonyProjectorCalibrationPresetSelect
from .color_space import SonyProjectorColorSpaceSelect
from .picture_mode import SonyProjectorPictureModeSelect

if TYPE_CHECKING:
    from custom_components.sony_projector.data import SonyProjectorConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SonyProjectorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    protocol = entry.data[CONF_PROTOCOL]
    entities = []
    if protocol == PROTOCOL_ADCP:
        entities.append(SonyProjectorPictureModeSelect(entry.runtime_data.coordinator))
    if protocol == PROTOCOL_SDCP:
        entities.append(SonyProjectorCalibrationPresetSelect(entry.runtime_data.coordinator))
    entities.append(SonyProjectorColorSpaceSelect(entry.runtime_data.coordinator))
    async_add_entities(entities)
