"""Color space select for Sony Projector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription

if TYPE_CHECKING:
    from custom_components.sony_projector.coordinator import SonyProjectorDataUpdateCoordinator

ENTITY_DESCRIPTION = SelectEntityDescription(
    key="color_space",
    translation_key="color_space",
    icon="mdi:palette-outline",
)


class SonyProjectorColorSpaceSelect(SelectEntity, SonyProjectorEntity):
    """Select entity for projector color space."""

    def __init__(self, coordinator: SonyProjectorDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def current_option(self) -> str | None:
        """Return the current color space."""
        return self.coordinator.data.color_space

    @property
    def options(self) -> list[str]:
        """Return available color spaces."""
        identity = self.coordinator.data.identity
        model = identity.model if identity else None
        return self.coordinator.config_entry.runtime_data.client.color_space_options(model, self.current_option)

    @property
    def available(self) -> bool:
        """Return if color space is available."""
        return bool(
            super().available
            and self.coordinator.data.operational_available
            and self.coordinator.data.color_space_supported,
        )

    async def async_select_option(self, option: str) -> None:
        """Select color space."""
        await self.coordinator.async_set_color_space(option)
