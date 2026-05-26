"""ADCP picture mode select for Sony Projector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription

if TYPE_CHECKING:
    from custom_components.sony_projector.coordinator import SonyProjectorDataUpdateCoordinator

ENTITY_DESCRIPTION = SelectEntityDescription(
    key="picture_mode",
    translation_key="picture_mode",
    icon="mdi:palette",
)


class SonyProjectorPictureModeSelect(SelectEntity, SonyProjectorEntity):
    """Select entity for ADCP picture mode."""

    def __init__(self, coordinator: SonyProjectorDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def current_option(self) -> str | None:
        """Return the current picture mode."""
        return self.coordinator.data.picture_mode

    @property
    def options(self) -> list[str]:
        """Return available picture modes."""
        return self.coordinator.config_entry.runtime_data.client.picture_mode_options(self.current_option)

    @property
    def available(self) -> bool:
        """Return if picture mode is available."""
        return bool(
            super().available
            and self.coordinator.data.operational_available
            and self.coordinator.data.picture_mode_supported,
        )

    async def async_select_option(self, option: str) -> None:
        """Select picture mode."""
        await self.coordinator.async_set_picture_mode(option)
