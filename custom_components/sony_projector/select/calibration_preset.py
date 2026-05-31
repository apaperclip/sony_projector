"""SDCP calibration preset select for Sony Projector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription

if TYPE_CHECKING:
    from custom_components.sony_projector.coordinator import SonyProjectorDataUpdateCoordinator

ENTITY_DESCRIPTION = SelectEntityDescription(
    key="calibration_preset",
    translation_key="calibration_preset",
    icon="mdi:tune-variant",
)


class SonyProjectorCalibrationPresetSelect(SelectEntity, SonyProjectorEntity):
    """Select entity for SDCP calibration preset."""

    def __init__(self, coordinator: SonyProjectorDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def current_option(self) -> str | None:
        """Return the current calibration preset."""
        return self.coordinator.data.calibration_preset

    @property
    def options(self) -> list[str]:
        """Return available calibration presets."""
        identity = self.coordinator.data.identity
        model = identity.model if identity else None
        return self.coordinator.config_entry.runtime_data.client.calibration_preset_options(model, self.current_option)

    @property
    def available(self) -> bool:
        """Return if calibration preset is available."""
        return bool(
            super().available
            and self.coordinator.data.operational_available
            and self.coordinator.data.calibration_preset_supported,
        )

    async def async_select_option(self, option: str) -> None:
        """Select calibration preset."""
        await self.coordinator.async_set_calibration_preset(option)
