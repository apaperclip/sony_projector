"""IP address diagnostic sensor for Sony Projector."""

from __future__ import annotations

from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory

ENTITY_DESCRIPTION = SensorEntityDescription(
    key="ip_address",
    translation_key="ip_address",
    icon="mdi:ip-network",
    entity_category=EntityCategory.DIAGNOSTIC,
)


class SonyProjectorIpAddressSensor(SensorEntity, SonyProjectorEntity):
    """Diagnostic sensor showing the configured projector host or IP address."""

    def __init__(self, coordinator) -> None:  # type: ignore[no-untyped-def]
        """Initialize the sensor."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def native_value(self) -> str | None:
        """Return configured projector host or IP address."""
        host = self.coordinator.config_entry.data.get("host")
        return str(host) if host else None
