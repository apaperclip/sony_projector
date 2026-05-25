"""Shared SDAP discovery listener for Sony projectors."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, cast

from sony_projector_protocol import parse_sdap_packet

from custom_components.sony_projector.const import DOMAIN, LOGGER, SDAP_PORT
from custom_components.sony_projector.data import SonyProjectorAdvertisement
from homeassistant.const import CONF_HOST
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigFlowContext
    from homeassistant.core import HomeAssistant

_DISCOVERY_DATA = "discovery_manager"


def async_get_discovery_manager(hass: HomeAssistant) -> SonyProjectorDiscoveryManager:
    """Return the shared discovery manager for this integration."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    manager = domain_data.get(_DISCOVERY_DATA)
    if manager is None:
        manager = SonyProjectorDiscoveryManager(hass)
        domain_data[_DISCOVERY_DATA] = manager
    return manager


class SonyProjectorDiscoveryManager:
    """Manage one global SDAP UDP listener and cached advertisements."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the discovery manager."""
        self.hass = hass
        self.advertisements: dict[str, SonyProjectorAdvertisement] = {}
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: _SdapProtocol | None = None
        self._entry_callbacks: dict[str, Callable[[SonyProjectorAdvertisement], None]] = {}

    async def async_start(self) -> None:
        """Start listening for SDAP packets if not already running."""
        if self._transport is not None:
            return
        loop = asyncio.get_running_loop()
        self._transport, protocol = await loop.create_datagram_endpoint(
            lambda: _SdapProtocol(self),
            local_addr=("0.0.0.0", SDAP_PORT),
            allow_broadcast=True,
        )
        self._protocol = protocol
        LOGGER.info("Started Sony projector SDAP listener on UDP port %s", SDAP_PORT)

    async def async_stop(self) -> None:
        """Stop listening for SDAP packets."""
        if self._transport is not None:
            self._transport.close()
            self._transport = None
            self._protocol = None
            LOGGER.info("Stopped Sony projector SDAP listener")

    def async_register_entry_callback(
        self,
        unique_id: str,
        callback: Callable[[SonyProjectorAdvertisement], None],
    ) -> Callable[[], None]:
        """Register a loaded config entry for advertisement updates."""
        self._entry_callbacks[unique_id] = callback
        if advertisement := self.advertisements.get(unique_id):
            callback(advertisement)

        def remove_callback() -> None:
            self._entry_callbacks.pop(unique_id, None)

        return remove_callback

    def datagram_received(self, data: bytes, ip: str) -> None:
        """Schedule advertisement handling from the UDP protocol callback."""
        self.hass.async_create_task(self._async_handle_datagram(data, ip))

    async def _async_handle_datagram(self, data: bytes, ip: str) -> None:
        try:
            discovered = parse_sdap_packet(data, ip)
        except Exception as exception:  # noqa: BLE001
            LOGGER.warning("Failed to parse Sony projector SDAP packet from %s: %s", ip, exception)
            return

        unique_id = _unique_id_from_discovery(discovered)
        if unique_id is None:
            LOGGER.debug("Ignoring Sony projector advertisement from %s without stable identity", ip)
            return

        advertisement = SonyProjectorAdvertisement(
            host=ip,
            unique_id=unique_id,
            received_at=dt_util.utcnow(),
            power_status=getattr(discovered, "power_status", None),
            community=getattr(discovered, "community", None),
            product_name=getattr(discovered, "product_name", None),
            serial_number=_string_or_none(getattr(discovered, "serial_number", None)),
            location=getattr(discovered, "location", None),
        )
        self.advertisements[unique_id] = advertisement
        LOGGER.debug(
            "Received Sony projector advertisement unique_id=%s host=%s power=%s",
            advertisement.unique_id,
            advertisement.host,
            advertisement.power_status,
        )

        entry = next(
            (entry for entry in self.hass.config_entries.async_entries(DOMAIN) if entry.unique_id == unique_id),
            None,
        )
        if entry is not None:
            if entry.data.get(CONF_HOST) != advertisement.host:
                entry_data = {**entry.data, CONF_HOST: advertisement.host}
                self.hass.config_entries.async_update_entry(entry, data=entry_data)
                if hasattr(entry, "runtime_data"):
                    entry.runtime_data.client.update_host(advertisement.host)
                LOGGER.info("Updated Sony projector host from advertisement for %s", unique_id)
            if callback := self._entry_callbacks.get(unique_id):
                callback(advertisement)
            return

        if self._has_in_progress_flow({"source": "user"}):
            LOGGER.debug(
                "Cached Sony projector advertisement for %s while user setup is in progress",
                unique_id,
            )
            return

        flow_context: ConfigFlowContext = {"source": "sdap", "unique_id": unique_id}
        if self._has_in_progress_flow(cast("dict[str, Any]", flow_context)):
            LOGGER.debug("Sony projector discovery flow already in progress for %s", unique_id)
            return

        LOGGER.info("Discovered Sony projector %s at %s", unique_id, advertisement.host)
        await self.hass.config_entries.flow.async_init(
            DOMAIN,
            context=flow_context,
            data=asdict(advertisement),
        )

    def _has_in_progress_flow(self, match_context: dict[str, Any]) -> bool:
        """Return true if a matching Sony projector config flow is active."""
        return bool(
            self.hass.config_entries.flow.async_progress_by_handler(
                DOMAIN,
                match_context=match_context,
            )
        )


class _SdapProtocol(asyncio.DatagramProtocol):
    """Datagram protocol that forwards packets to the discovery manager."""

    def __init__(self, manager: SonyProjectorDiscoveryManager) -> None:
        self._manager = manager

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self._manager.datagram_received(data, addr[0])


def _unique_id_from_discovery(discovered: Any) -> str | None:
    serial = _string_or_none(getattr(discovered, "serial_number", None))
    if serial is not None:
        return serial
    return _string_or_none(getattr(discovered, "id", None))


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
