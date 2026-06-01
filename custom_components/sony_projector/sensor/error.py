"""Projector error diagnostic sensor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory

if TYPE_CHECKING:
    from custom_components.sony_projector.coordinator import SonyProjectorDataUpdateCoordinator

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="error",
    translation_key="error",
    icon="mdi:alert-circle-outline",
    entity_category=EntityCategory.DIAGNOSTIC,
)


class SonyProjectorErrorSensor(SensorEntity, SonyProjectorEntity):
    """Diagnostic sensor showing projector error state."""

    def __init__(self, coordinator: SonyProjectorDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def native_value(self) -> str | None:
        """Return the current projector error state."""
        return self.coordinator.data.error

    @property
    def available(self) -> bool:
        """Return if error state is available."""
        return bool(
            super().available and self.coordinator.data.operational_available and self.coordinator.data.error_supported,
        )
