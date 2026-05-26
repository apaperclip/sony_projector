"""Lamp timer diagnostic sensor for Sony Projector."""

from __future__ import annotations

from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfTime

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="lamp_timer",
    translation_key="lamp_timer",
    icon="mdi:projector",
    entity_category=EntityCategory.DIAGNOSTIC,
    device_class=SensorDeviceClass.DURATION,
    native_unit_of_measurement=UnitOfTime.HOURS,
    state_class=SensorStateClass.TOTAL_INCREASING,
)


class SonyProjectorLampTimerSensor(SensorEntity, SonyProjectorEntity):
    """Diagnostic sensor showing projector lamp hours."""

    def __init__(self, coordinator) -> None:  # type: ignore[no-untyped-def]
        """Initialize the sensor."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def native_value(self) -> int | float | str | None:
        """Return lamp timer value."""
        return self.coordinator.data.lamp_timer

    @property
    def available(self) -> bool:
        """Return if lamp timer is available."""
        return bool(
            super().available
            and self.coordinator.data.lamp_timer_supported
            and self.coordinator.data.lamp_timer is not None,
        )
