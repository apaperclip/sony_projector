"""Projector warning diagnostic sensor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.const import PROTOCOL_ADCP
from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory

if TYPE_CHECKING:
    from custom_components.sony_projector.coordinator import SonyProjectorDataUpdateCoordinator

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="warning",
    translation_key="warning",
    icon="mdi:alert-outline",
    entity_category=EntityCategory.DIAGNOSTIC,
)


class SonyProjectorWarningSensor(SensorEntity, SonyProjectorEntity):
    """Diagnostic sensor showing projector warning state."""

    def __init__(self, coordinator: SonyProjectorDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def native_value(self) -> str | None:
        """Return the current projector warning state."""
        return self.coordinator.data.warning

    @property
    def available(self) -> bool:
        """Return if warning state is available."""
        return bool(
            super().available
            and self.coordinator.config_entry.runtime_data.client.protocol == PROTOCOL_ADCP
            and self.coordinator.data.operational_available
            and self.coordinator.data.warning_supported,
        )
