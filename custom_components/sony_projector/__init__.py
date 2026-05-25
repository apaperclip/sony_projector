"""Sony Projector custom integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, Platform
import homeassistant.helpers.config_validation as cv
from homeassistant.loader import async_get_loaded_integration

from .api import SonyProjectorApiClient
from .const import (
    CONF_ADCP_PASSWORD,
    CONF_COMMUNITY,
    CONF_PROTOCOL,
    DEFAULT_ADCP_PASSWORD,
    DEFAULT_SDCP_COMMUNITY,
    DOMAIN,
    LOGGER,
    PROTOCOL_ADCP,
)
from .coordinator import SonyProjectorDataUpdateCoordinator
from .data import SonyProjectorData
from .discovery import async_get_discovery_manager

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SonyProjectorConfigEntry

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration and shared discovery listener."""
    manager = async_get_discovery_manager(hass)
    try:
        await manager.async_start()
    except OSError as exception:
        LOGGER.warning("Unable to start Sony projector SDAP listener: %s", exception)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SonyProjectorConfigEntry,
) -> bool:
    """Set up a Sony projector config entry."""
    protocol = entry.data[CONF_PROTOCOL]
    client = SonyProjectorApiClient(
        host=entry.data[CONF_HOST],
        protocol=protocol,
        community=entry.data.get(CONF_COMMUNITY, DEFAULT_SDCP_COMMUNITY),
        adcp_password=entry.data.get(CONF_ADCP_PASSWORD, DEFAULT_ADCP_PASSWORD if protocol == PROTOCOL_ADCP else None),
    )

    coordinator = SonyProjectorDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        config_entry=entry,
    )
    manager = async_get_discovery_manager(hass)
    entry.runtime_data = SonyProjectorData(
        client=client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        discovery_manager=manager,
    )

    await coordinator.async_config_entry_first_refresh()

    if entry.unique_id is not None:
        entry.async_on_unload(
            manager.async_register_entry_callback(entry.unique_id, coordinator.async_apply_advertisement)
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SonyProjectorConfigEntry,
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and hasattr(entry, "runtime_data"):
        await entry.runtime_data.coordinator.async_shutdown()
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant,
    entry: SonyProjectorConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
