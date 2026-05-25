"""Lifecycle-aware DataUpdateCoordinator for Sony projectors."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING

from custom_components.sony_projector.api import (
    SonyProjectorApiClientAuthenticationError,
    SonyProjectorApiClientCommunicationError,
    SonyProjectorApiClientError,
    is_logically_on,
    is_operational_power_status,
    normalize_power_status,
)
from custom_components.sony_projector.const import (
    ACTIVE_POLL_INTERVAL_SECONDS,
    ADVERTISEMENT_TIMEOUT_SECONDS,
    DEFAULT_INPUT_SOURCES,
    LOGGER,
    PASSIVE_POLL_INTERVAL_SECONDS,
    POWER_CONFIRMATION_INTERVAL_SECONDS,
    POWER_CONFIRMATION_TIMEOUT_SECONDS,
)
from custom_components.sony_projector.data import SonyProjectorAdvertisement, SonyProjectorState
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from logging import Logger

    from custom_components.sony_projector.data import SonyProjectorConfigEntry
    from homeassistant.core import HomeAssistant


class SonyProjectorDataUpdateCoordinator(DataUpdateCoordinator[SonyProjectorState]):
    """Manage lifecycle-aware projector state for entities."""

    config_entry: SonyProjectorConfigEntry

    def __init__(
        self,
        *,
        hass: HomeAssistant,
        logger: Logger,
        name: str,
        config_entry: SonyProjectorConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            config_entry=config_entry,
            update_interval=timedelta(seconds=PASSIVE_POLL_INTERVAL_SECONDS),
            always_update=False,
        )
        self._state = SonyProjectorState(source_list=list(DEFAULT_INPUT_SOURCES))
        self._confirmation_task: asyncio.Task[None] | None = None

    async def _async_setup(self) -> None:
        """Read identity before the first refresh."""
        identity = await self.config_entry.runtime_data.client.validate_and_identify()
        self._state.identity = identity
        self._state.device_available = True
        LOGGER.debug("Coordinator setup complete for projector %s", identity.unique_id)

    async def _async_update_data(self) -> SonyProjectorState:
        """Fetch data based on current lifecycle state."""
        self._apply_advertisement_timeout()
        client = self.config_entry.runtime_data.client

        try:
            if self._should_poll_active_data():
                LOGGER.debug("Polling active projector data for %s", self.config_entry.entry_id)
                active_state = await client.async_get_active_data(self._state.identity)
                self._merge_state(active_state)
                self.update_interval = timedelta(seconds=ACTIVE_POLL_INTERVAL_SECONDS)
            else:
                LOGGER.debug("Polling passive projector data for %s", self.config_entry.entry_id)
                passive_state = await client.async_get_passive_data(self._state.identity)
                self._merge_state(passive_state)
                if self._state.operational_available:
                    self.update_interval = timedelta(seconds=ACTIVE_POLL_INTERVAL_SECONDS)
                else:
                    self.update_interval = timedelta(seconds=PASSIVE_POLL_INTERVAL_SECONDS)
            self._state.last_update_error = None
        except SonyProjectorApiClientAuthenticationError as exception:
            LOGGER.warning("Projector authentication error: %s", exception)
            raise ConfigEntryAuthFailed(
                translation_domain="sony_projector",
                translation_key="authentication_failed",
            ) from exception
        except SonyProjectorApiClientCommunicationError as exception:
            self._state.last_update_error = str(exception)
            if self._state.last_advertisement is None:
                self._state.device_available = False
                self._state.operational_available = False
            LOGGER.warning("Projector communication failed: %s", exception)
            raise UpdateFailed(
                translation_domain="sony_projector",
                translation_key="update_failed",
            ) from exception
        except SonyProjectorApiClientError as exception:
            self._state.last_update_error = str(exception)
            LOGGER.exception("Projector update failed")
            raise UpdateFailed(
                translation_domain="sony_projector",
                translation_key="update_failed",
            ) from exception

        return self._state

    def async_apply_advertisement(self, advertisement: SonyProjectorAdvertisement) -> None:
        """Apply an SDAP advertisement and publish updated lifecycle state."""
        previous_mode = self._state.operational_available
        self._state.device_available = True
        self._state.last_advertisement = advertisement
        power_status = normalize_power_status(advertisement.power_status)
        self._state.power_status = power_status
        self._state.normalized_power_status = power_status
        self._state.logical_power = is_logically_on(power_status)
        self._state.operational_available = is_operational_power_status(power_status)
        if self._state.identity is not None:
            self._state.identity.model = self._state.identity.model or advertisement.product_name
            self._state.identity.location = self._state.identity.location or advertisement.location

        if previous_mode != self._state.operational_available:
            LOGGER.info(
                "Projector %s monitoring changed to %s",
                advertisement.unique_id,
                "active" if self._state.operational_available else "passive",
            )

        self.update_interval = timedelta(
            seconds=ACTIVE_POLL_INTERVAL_SECONDS
            if self._state.operational_available
            else PASSIVE_POLL_INTERVAL_SECONDS,
        )
        self.async_set_updated_data(self._state)

    async def async_set_power(self, power: bool) -> None:
        """Set logical power and start temporary confirmation polling."""
        await self.config_entry.runtime_data.client.async_set_power(power)
        self._state.logical_power = power
        self._state.device_available = True
        if not power:
            self._state.operational_available = False
        self.async_set_updated_data(self._state)
        self._start_confirmation_polling(power)

    async def async_set_input(self, source: str) -> None:
        """Set projector input and update state optimistically."""
        await self.config_entry.runtime_data.client.async_set_input(source)
        self._state.input = source
        if source not in self._state.source_list:
            self._state.source_list.append(source)
        self.async_set_updated_data(self._state)
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Cancel background work and close client resources."""
        if self._confirmation_task is not None:
            self._confirmation_task.cancel()
        await self.config_entry.runtime_data.client.close()

    def _merge_state(self, state: SonyProjectorState) -> None:
        self._state.device_available = state.device_available
        self._state.operational_available = state.operational_available
        self._state.power_status = state.power_status
        self._state.normalized_power_status = state.normalized_power_status
        self._state.logical_power = state.logical_power
        self._state.input = state.input or self._state.input
        self._state.lamp_timer = state.lamp_timer
        self._state.lamp_timer_supported = state.lamp_timer_supported
        self._state.identity = state.identity or self._state.identity
        self._state.last_update_error = state.last_update_error
        self._state.source_list = state.source_list or self._state.source_list

    def _apply_advertisement_timeout(self) -> None:
        advertisement = self._state.last_advertisement
        if advertisement is None:
            return
        age = (dt_util.utcnow() - advertisement.received_at).total_seconds()
        if age <= ADVERTISEMENT_TIMEOUT_SECONDS:
            return
        LOGGER.warning("Projector advertisement timed out after %.0f seconds", age)
        self._state.device_available = False
        self._state.operational_available = False

    def _should_poll_active_data(self) -> bool:
        return self._state.operational_available or self._state.logical_power is True

    def _start_confirmation_polling(self, target_power: bool) -> None:
        if self._confirmation_task is not None:
            self._confirmation_task.cancel()
        self._confirmation_task = self.hass.async_create_task(self._confirm_power(target_power))

    async def _confirm_power(self, target_power: bool) -> None:
        deadline = dt_util.utcnow().timestamp() + POWER_CONFIRMATION_TIMEOUT_SECONDS
        while dt_util.utcnow().timestamp() < deadline:
            await asyncio.sleep(POWER_CONFIRMATION_INTERVAL_SECONDS)
            try:
                power_status = await self.config_entry.runtime_data.client.async_get_power_status()
            except SonyProjectorApiClientError as exception:
                LOGGER.debug("Power confirmation poll failed: %s", exception)
                continue
            self._state.power_status = power_status
            self._state.normalized_power_status = power_status
            self._state.logical_power = is_logically_on(power_status)
            self._state.operational_available = is_operational_power_status(power_status)
            self._state.device_available = True
            self.async_set_updated_data(self._state)
            if self._is_power_confirmation_complete(target_power):
                LOGGER.debug("Power confirmation complete for target=%s", target_power)
                return

    def _is_power_confirmation_complete(self, target_power: bool) -> bool:
        """Return true when the projector has finished the requested transition."""
        if target_power:
            return self._state.operational_available
        return self._state.normalized_power_status in {"standby", "off"}
