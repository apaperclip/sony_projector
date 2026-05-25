"""Media player platform for Sony Projector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.const import PARALLEL_UPDATES as PARALLEL_UPDATES

from .projector import SonyProjectorMediaPlayer

if TYPE_CHECKING:
    from custom_components.sony_projector.data import SonyProjectorConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SonyProjectorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player platform."""
    async_add_entities([SonyProjectorMediaPlayer(entry.runtime_data.coordinator)])
