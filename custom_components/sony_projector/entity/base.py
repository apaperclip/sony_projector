"""Base entity class for Sony Projector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.sony_projector.const import DOMAIN, MANUFACTURER
from custom_components.sony_projector.coordinator import SonyProjectorDataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class SonyProjectorEntity(CoordinatorEntity[SonyProjectorDataUpdateCoordinator]):
    """Base entity for all Sony Projector entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SonyProjectorDataUpdateCoordinator,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        base_unique_id = coordinator.config_entry.unique_id or coordinator.config_entry.entry_id
        self._attr_unique_id = f"{base_unique_id}_{entity_description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info from projector identity."""
        identity = self.coordinator.data.identity if self.coordinator.data else None
        identifier = identity.unique_id if identity else self.coordinator.config_entry.unique_id
        return DeviceInfo(
            identifiers={(DOMAIN, identifier or self.coordinator.config_entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=identity.model if identity else None,
            serial_number=identity.serial if identity else None,
            name=self.coordinator.config_entry.title,
            sw_version=None,
            configuration_url=f"http://{self.coordinator.config_entry.data.get('host')}",
        )

    @property
    def available(self) -> bool:
        """Return if the projector device is available."""
        return bool(self.coordinator.data and self.coordinator.data.device_available)
