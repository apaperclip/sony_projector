"""Power status sensor for Sony Projector."""

from __future__ import annotations

from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="power_status",
    translation_key="power_status",
    icon="mdi:power-cycle",
)


class SonyProjectorPowerStatusSensor(SensorEntity, SonyProjectorEntity):
    """Sensor showing projector lifecycle power status."""

    def __init__(self, coordinator) -> None:  # type: ignore[no-untyped-def]
        """Initialize the sensor."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def native_value(self) -> str | int | None:
        """Return raw/normalized power status."""
        return self.coordinator.data.normalized_power_status or self.coordinator.data.power_status
