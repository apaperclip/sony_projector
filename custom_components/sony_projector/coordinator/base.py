"""Lifecycle-aware DataUpdateCoordinator for Sony projectors."""

from __future__ import annotations

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
    CONF_SETUP_SOURCE,
    DEFAULT_INPUT_SOURCES,
    LOGGER,
    PASSIVE_POLL_INTERVAL_SECONDS,
    SETUP_SOURCE_MANUAL,
)
from custom_components.sony_projector.data import SonyProjectorAdvertisement, SonyProjectorState
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

if TYPE_CHECKING:
    from logging import Logger

    from custom_components.sony_projector.data import SonyProjectorConfigEntry
    from homeassistant.core import HomeAssistant

SDAP_VISIBLE_POWER_STATES = {"start_up", "start_up_lamp", "on"}


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
            always_update=True,
        )
        self._state = SonyProjectorState(source_list=list(DEFAULT_INPUT_SOURCES))
        self._pending_power_target: bool | None = None

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
            else:
                LOGGER.debug("Polling passive projector data for %s", self.config_entry.entry_id)
                passive_state = await client.async_get_passive_data(self._state.identity)
                self._merge_state(passive_state)
                if self._should_poll_active_data():
                    LOGGER.debug(
                        "Projector %s is active after passive poll; fetching active data", self.config_entry.entry_id
                    )
                    active_state = await client.async_get_active_data(self._state.identity)
                    self._merge_state(active_state)
            self.update_interval = self._poll_interval()
            self._state.last_update_error = None
        except SonyProjectorApiClientAuthenticationError as exception:
            LOGGER.warning("Projector authentication error: %s", exception)
            raise ConfigEntryAuthFailed(
                translation_domain="sony_projector",
                translation_key="authentication_failed",
            ) from exception
        except SonyProjectorApiClientCommunicationError as exception:
            self._state.last_update_error = str(exception)
            self._mark_unavailable()
            self.async_set_updated_data(self._state)
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
        self._state.last_advertisement = advertisement
        if self.config_entry.data.get(CONF_SETUP_SOURCE) == SETUP_SOURCE_MANUAL:
            self.async_set_updated_data(self._state)
            return

        power_status = normalize_power_status(advertisement.power_status)
        if self._state.identity is not None:
            self._state.identity.model = self._state.identity.model or advertisement.product_name
            self._state.identity.location = self._state.identity.location or advertisement.location

        if power_status not in SDAP_VISIBLE_POWER_STATES:
            self.async_set_updated_data(self._state)
            return

        self._state.power_status = power_status
        self._state.normalized_power_status = power_status
        self._state.device_available = True
        self._state.logical_power = is_logically_on(power_status)
        self._state.operational_available = is_operational_power_status(power_status)
        self._clear_pending_power_target_if_complete()

        if previous_mode != self._state.operational_available:
            LOGGER.info(
                "Projector %s monitoring changed to %s",
                advertisement.unique_id,
                "active" if self._state.operational_available else "passive",
            )

        self.update_interval = self._poll_interval()
        self.async_set_updated_data(self._state)
        self.hass.async_create_task(self.async_request_refresh())

    async def async_set_power(self, power: bool) -> None:
        """Set logical power and temporarily use active polling."""
        await self.config_entry.runtime_data.client.async_set_power(power)
        self._pending_power_target = power
        self._state.logical_power = power
        self._state.device_available = True
        if not power:
            self._state.operational_available = False
        self.update_interval = self._poll_interval()
        self.async_set_updated_data(self._state)

    async def async_set_input(self, source: str) -> None:
        """Set projector input and update state optimistically."""
        await self.config_entry.runtime_data.client.async_set_input(source)
        self._state.input = source
        if source not in self._state.source_list:
            self._state.source_list.append(source)
        self.async_set_updated_data(self._state)
        await self.async_request_refresh()

    async def async_set_picture_mode(self, picture_mode: str) -> None:
        """Set ADCP picture mode and update state optimistically."""
        await self.config_entry.runtime_data.client.async_set_picture_mode(picture_mode)
        self._state.picture_mode = picture_mode
        self.async_set_updated_data(self._state)
        await self.async_request_refresh()

    async def async_set_calibration_preset(self, calibration_preset: str) -> None:
        """Set SDCP calibration preset and update state optimistically."""
        await self.config_entry.runtime_data.client.async_set_calibration_preset(calibration_preset)
        self._state.calibration_preset = calibration_preset
        self.async_set_updated_data(self._state)
        await self.async_request_refresh()

    async def async_set_color_space(self, color_space: str) -> None:
        """Set color space and update state optimistically."""
        await self.config_entry.runtime_data.client.async_set_color_space(color_space)
        self._state.color_space = color_space
        self.async_set_updated_data(self._state)
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Cancel background work and close client resources."""
        await self.config_entry.runtime_data.client.close()

    def _merge_state(self, state: SonyProjectorState) -> None:
        self._state.device_available = state.device_available
        self._state.operational_available = state.operational_available
        self._state.power_status = state.power_status
        self._state.normalized_power_status = state.normalized_power_status
        self._state.logical_power = is_logically_on(state.normalized_power_status)
        self._state.input = state.input or self._state.input
        self._state.signal = state.signal or self._state.signal
        self._state.signal_supported = state.signal_supported
        self._state.warning = state.warning
        self._state.warning_supported = state.warning_supported
        self._state.error = state.error
        self._state.error_supported = state.error_supported
        self._state.picture_mode = state.picture_mode
        self._state.picture_mode_supported = state.picture_mode_supported
        self._state.calibration_preset = state.calibration_preset or self._state.calibration_preset
        self._state.calibration_preset_supported = state.calibration_preset_supported
        self._state.color_space = state.color_space
        self._state.color_space_supported = state.color_space_supported
        self._state.lamp_timer = state.lamp_timer
        self._state.lamp_timer_supported = state.lamp_timer_supported
        self._state.identity = state.identity or self._state.identity
        self._state.last_update_error = state.last_update_error
        self._state.source_list = state.source_list or self._state.source_list
        self._clear_pending_power_target_if_complete()

    def _mark_unavailable(self) -> None:
        """Mark live projector state unavailable after a failed poll."""
        self._state.device_available = False
        self._state.operational_available = False
        self._state.power_status = None
        self._state.normalized_power_status = None
        self._state.logical_power = None
        self._state.input = None
        self._state.signal = None
        self._state.warning = None
        self._state.error = None
        self._state.picture_mode = None
        self._state.calibration_preset = None
        self._state.color_space = None

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
        return (
            self._state.operational_available or self._state.logical_power is True or self._pending_power_target is True
        )

    def _poll_interval(self) -> timedelta:
        """Return the next coordinator polling interval."""
        return timedelta(
            seconds=ACTIVE_POLL_INTERVAL_SECONDS if self._should_poll_active_data() else PASSIVE_POLL_INTERVAL_SECONDS,
        )

    def _clear_pending_power_target_if_complete(self) -> None:
        """Clear pending power command once the requested stable state is reached."""
        if self._pending_power_target is True and self._state.normalized_power_status == "on":
            self._pending_power_target = None
        if self._pending_power_target is False and self._state.normalized_power_status in {"standby", "off"}:
            self._pending_power_target = None
