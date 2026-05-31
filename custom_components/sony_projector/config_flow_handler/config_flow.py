"""Config flow for Sony Projector."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from custom_components.sony_projector.api import (
    SonyProjectorApiClientAuthenticationError,
    SonyProjectorApiClientCommunicationError,
    SonyProjectorApiClientError,
    SonyProjectorCannotIdentifyError,
)
from custom_components.sony_projector.config_flow_handler.schemas import (
    CONF_DISCOVERED_PROJECTOR,
    CONF_SETUP_METHOD,
    SETUP_METHOD_LISTEN,
    SETUP_METHOD_MANUAL,
    get_discovery_schema,
    get_manual_schema,
    get_protocol_auth_schema,
    get_reconfigure_schema,
    get_sdap_schema,
    get_setup_method_schema,
)
from custom_components.sony_projector.config_flow_handler.validators import validate_projector_connection
from custom_components.sony_projector.const import (
    CONF_ADCP_PASSWORD,
    CONF_COMMUNITY,
    CONF_PROTOCOL,
    CONF_SETUP_SOURCE,
    DEFAULT_ADCP_PASSWORD,
    DEFAULT_SDCP_COMMUNITY,
    DOMAIN,
    LOGGER,
    PROTOCOL_ADCP,
    PROTOCOL_SDCP,
    SETUP_SOURCE_MANUAL,
    SETUP_SOURCE_SDAP,
)
from custom_components.sony_projector.discovery import async_get_discovery_manager
from homeassistant import config_entries
from homeassistant.const import CONF_HOST

if TYPE_CHECKING:
    from custom_components.sony_projector.config_flow_handler.options_flow import SonyProjectorOptionsFlow
    from custom_components.sony_projector.data import SonyProjectorAdvertisement, SonyProjectorIdentity
    from custom_components.sony_projector.discovery import SonyProjectorDiscoveryManager

ERROR_MAP = {
    SonyProjectorApiClientAuthenticationError: "auth",
    SonyProjectorApiClientCommunicationError: "connection",
    SonyProjectorCannotIdentifyError: "cannot_identify",
    SonyProjectorApiClientError: "unknown",
}
DISCOVERY_TIMEOUT_SECONDS = 60.0
DISCOVERY_WAIT_INTERVAL_SECONDS = 0.5


class SonyProjectorConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sony Projector."""

    VERSION = 1
    _manual_data: dict[str, Any] | None = None
    _sdap_data: dict[str, Any] | None = None
    _sdap_protocol_data: dict[str, Any] | None = None
    _reconfigure_data: dict[str, Any] | None = None
    _discovery_task: asyncio.Task[None] | None = None

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> SonyProjectorOptionsFlow:
        """Get the options flow for this handler."""
        from custom_components.sony_projector.config_flow_handler.options_flow import (  # noqa: PLC0415
            SonyProjectorOptionsFlow,
        )

        return SonyProjectorOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Ask how the user wants to add a projector."""
        if user_input is not None:
            if user_input[CONF_SETUP_METHOD] == SETUP_METHOD_LISTEN:
                return await self.async_step_listen()
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=get_setup_method_schema(),
        )

    async def async_step_manual(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle manual setup from the UI."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST, "").strip()
            if not host:
                errors[CONF_HOST] = "required"
            else:
                self._manual_data = user_input | {CONF_HOST: host}
                return self._show_protocol_auth_form("manual", self._manual_data)

        return self.async_show_form(
            step_id="manual",
            data_schema=get_manual_schema(user_input),
            errors=errors,
        )

    async def async_step_manual_adcp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle ADCP-specific manual setup fields."""
        return await self._async_finish_manual_protocol(user_input)

    async def async_step_manual_sdcp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle SDCP-specific manual setup fields."""
        return await self._async_finish_manual_protocol(user_input)

    async def async_step_listen(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Listen for SDAP advertisements before continuing setup."""
        manager = async_get_discovery_manager(self.hass)
        await self._async_start_discovery(manager)

        if self._discovery_task is None:
            self._discovery_task = self.hass.async_create_task(self._async_wait_for_discovery(manager))

        if not self._discovery_task.done():
            return self.async_show_progress(
                step_id="listen",
                progress_action="discovering",
                progress_task=self._discovery_task,
            )

        self._discovery_task = None
        return self.async_show_progress_done(next_step_id="discovered")

    async def async_step_discovered(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Show discovered projectors or continue with the first result."""
        manager = async_get_discovery_manager(self.hass)
        discoveries = self._discovery_labels()
        if not discoveries:
            return await self.async_step_discovery_failed()

        if user_input is not None:
            selected = user_input[CONF_DISCOVERED_PROJECTOR]
            return await self.async_step_sdap(self._advertisement_data(manager.advertisements[selected]))

        return self.async_show_form(
            step_id="discovered",
            data_schema=get_discovery_schema(user_input, discoveries),
        )

    async def async_step_sdap(
        self,
        discovery_info: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a projector discovered via SDAP advertisement."""
        if discovery_info is not None:
            self._sdap_data = discovery_info
            unique_id = discovery_info["unique_id"]
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info["host"]})
            self.context["title_placeholders"] = {
                "name": discovery_info.get("product_name") or "Sony Projector",
            }

        assert self._sdap_data is not None
        return self.async_show_form(
            step_id="sdap_confirm",
            data_schema=get_sdap_schema(self._sdap_defaults(self._sdap_data)),
            description_placeholders={
                "host": self._sdap_data["host"],
                "name": self._sdap_data.get("product_name") or "Sony Projector",
                "serial_number": self._sdap_data.get("serial_number") or self._sdap_data["unique_id"],
            },
        )

    async def async_step_sdap_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Confirm adding an SDAP-discovered projector."""
        assert self._sdap_data is not None
        if user_input is None:
            return await self.async_step_sdap()

        self._sdap_protocol_data = user_input
        return self._show_protocol_auth_form("sdap", user_input)

    async def async_step_sdap_adcp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle ADCP-specific SDAP confirmation fields."""
        return await self._async_finish_sdap_protocol(user_input)

    async def async_step_sdap_sdcp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle SDCP-specific SDAP confirmation fields."""
        return await self._async_finish_sdap_protocol(user_input)

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration of an existing projector."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST, "").strip()
            if not host:
                errors[CONF_HOST] = "required"
            else:
                self._reconfigure_data = user_input | {CONF_HOST: host}
                return self._show_protocol_auth_form("reconfigure", self._reconfigure_data)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_reconfigure_schema(entry.data),
            errors=errors,
        )

    async def async_step_reconfigure_adcp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle ADCP-specific reconfiguration fields."""
        return await self._async_finish_reconfigure_protocol(user_input)

    async def async_step_reconfigure_sdcp(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle SDCP-specific reconfiguration fields."""
        return await self._async_finish_reconfigure_protocol(user_input)

    async def async_step_discovery_failed(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle no projectors found after discovery timeout."""
        if user_input is not None:
            if user_input[CONF_SETUP_METHOD] == SETUP_METHOD_LISTEN:
                return await self.async_step_listen()
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="discovery_failed",
            data_schema=get_setup_method_schema(default=SETUP_METHOD_MANUAL),
        )

    async def _async_create_from_advertisement(
        self,
        advertisement: SonyProjectorAdvertisement,
        user_input: dict[str, Any],
    ) -> config_entries.ConfigFlowResult:
        return await self._async_create_from_advertisement_data(
            self._advertisement_data(advertisement),
            user_input,
        )

    async def _async_create_from_advertisement_data(
        self,
        discovery_data: dict[str, Any],
        user_input: dict[str, Any],
    ) -> config_entries.ConfigFlowResult:
        unique_id = discovery_data["unique_id"]
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_data["host"]})
        entry_input = {
            **user_input,
            CONF_HOST: discovery_data["host"],
        }
        if entry_input[CONF_PROTOCOL] == PROTOCOL_SDCP:
            entry_input[CONF_COMMUNITY] = (
                user_input.get(CONF_COMMUNITY) or discovery_data.get("community") or DEFAULT_SDCP_COMMUNITY
            )
        data = self._entry_data(
            entry_input,
            unique_id,
            setup_source=SETUP_SOURCE_SDAP,
        )
        return self.async_create_entry(
            title=discovery_data.get("product_name") or f"Sony Projector {discovery_data['host']}",
            data=data,
        )

    async def _async_validate(self, user_input: dict[str, Any]) -> SonyProjectorIdentity:
        return await validate_projector_connection(
            host=user_input[CONF_HOST],
            protocol=user_input[CONF_PROTOCOL],
            community=user_input.get(CONF_COMMUNITY) or DEFAULT_SDCP_COMMUNITY,
            adcp_password=self._adcp_password_or_none(user_input),
        )

    def _entry_data(
        self,
        user_input: dict[str, Any],
        unique_id: str,
        *,
        setup_source: str,
    ) -> dict[str, Any]:
        protocol = user_input[CONF_PROTOCOL]
        data: dict[str, Any] = {
            CONF_HOST: user_input[CONF_HOST],
            CONF_PROTOCOL: protocol,
            CONF_SETUP_SOURCE: setup_source,
        }
        if protocol == PROTOCOL_ADCP:
            data[CONF_ADCP_PASSWORD] = self._adcp_password_or_none(user_input)
        else:
            data[CONF_COMMUNITY] = user_input.get(CONF_COMMUNITY) or DEFAULT_SDCP_COMMUNITY
        data["unique_id"] = unique_id
        return data

    def _entry_title(self, identity: SonyProjectorIdentity, host: str) -> str:
        return identity.model or identity.location or f"Sony Projector {host}"

    def _discovery_labels(self) -> dict[str, str]:
        manager = async_get_discovery_manager(self.hass)
        return {
            unique_id: self._discovery_label(unique_id, advertisement)
            for unique_id, advertisement in manager.advertisements.items()
        }

    def _discovery_label(self, unique_id: str, advertisement: SonyProjectorAdvertisement) -> str:
        """Return a useful label for a discovered projector."""
        model = advertisement.product_name or "Sony Projector"
        serial = advertisement.serial_number or unique_id
        return f"{model} - {advertisement.host} - {serial}"

    def _sdap_defaults(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            CONF_PROTOCOL: data.get(CONF_PROTOCOL) or PROTOCOL_ADCP,
            CONF_COMMUNITY: data.get(CONF_COMMUNITY) or data.get("community") or DEFAULT_SDCP_COMMUNITY,
            CONF_ADCP_PASSWORD: DEFAULT_ADCP_PASSWORD,
        }

    def _adcp_password_or_none(self, data: dict[str, Any]) -> str | None:
        password = data.get(CONF_ADCP_PASSWORD)
        if password is None:
            return DEFAULT_ADCP_PASSWORD
        return password or None

    async def _async_finish_manual_protocol(
        self,
        user_input: dict[str, Any] | None,
    ) -> config_entries.ConfigFlowResult:
        if self._manual_data is None:
            return await self.async_step_manual()
        if user_input is None:
            return self._show_protocol_auth_form("manual", self._manual_data)

        data = self._manual_data | user_input
        try:
            identity = await self._async_validate(data)
        except Exception as exception:  # noqa: BLE001
            return self._show_protocol_auth_form(
                "manual",
                data,
                errors={"base": self._map_exception_to_error(exception)},
            )

        host = data[CONF_HOST]
        await self.async_set_unique_id(identity.unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        return self.async_create_entry(
            title=self._entry_title(identity, host),
            data=self._entry_data(data, identity.unique_id, setup_source=SETUP_SOURCE_MANUAL),
        )

    async def _async_finish_sdap_protocol(
        self,
        user_input: dict[str, Any] | None,
    ) -> config_entries.ConfigFlowResult:
        if self._sdap_data is None or self._sdap_protocol_data is None:
            return await self.async_step_sdap()
        if user_input is None:
            return self._show_protocol_auth_form(
                "sdap", self._sdap_defaults(self._sdap_data) | self._sdap_protocol_data
            )
        return await self._async_create_from_advertisement_data(
            self._sdap_data,
            self._sdap_protocol_data | user_input,
        )

    async def _async_finish_reconfigure_protocol(
        self,
        user_input: dict[str, Any] | None,
    ) -> config_entries.ConfigFlowResult:
        if self._reconfigure_data is None:
            return await self.async_step_reconfigure()
        if user_input is None:
            return self._show_protocol_auth_form("reconfigure", self._reconfigure_data)

        entry = self._get_reconfigure_entry()
        data = self._reconfigure_data | user_input
        try:
            identity = await self._async_validate(data)
        except Exception as exception:  # noqa: BLE001
            return self._show_protocol_auth_form(
                "reconfigure",
                data,
                errors={"base": self._map_exception_to_error(exception)},
            )

        if entry.unique_id != identity.unique_id:
            return self._show_protocol_auth_form("reconfigure", data, errors={"base": "wrong_device"})

        return self.async_update_reload_and_abort(
            entry,
            data=self._entry_data(
                data,
                identity.unique_id,
                setup_source=entry.data.get(CONF_SETUP_SOURCE, SETUP_SOURCE_MANUAL),
            ),
        )

    def _show_protocol_auth_form(
        self,
        step_prefix: str,
        data: dict[str, Any],
        *,
        errors: dict[str, str] | None = None,
    ) -> config_entries.ConfigFlowResult:
        protocol = data[CONF_PROTOCOL]
        return self.async_show_form(
            step_id=self._protocol_step_id(step_prefix, protocol),
            data_schema=get_protocol_auth_schema(protocol, data),
            errors=errors,
        )

    def _protocol_step_id(self, step_prefix: str, protocol: str) -> str:
        suffix = "adcp" if protocol == PROTOCOL_ADCP else "sdcp"
        return f"{step_prefix}_{suffix}"

    async def _async_start_discovery(self, manager: Any) -> None:
        """Start SDAP discovery when the user opens the config flow."""
        try:
            await manager.async_start()
        except OSError as exception:
            LOGGER.warning("Unable to start Sony projector SDAP listener: %s", exception)

    async def _async_wait_for_discovery(self, manager: SonyProjectorDiscoveryManager) -> None:
        """Keep discovery open for the full timeout so all advertisements can arrive."""
        for _ in range(round(DISCOVERY_TIMEOUT_SECONDS / DISCOVERY_WAIT_INTERVAL_SECONDS)):
            await asyncio.sleep(DISCOVERY_WAIT_INTERVAL_SECONDS)

    def _advertisement_data(self, advertisement: SonyProjectorAdvertisement) -> dict[str, Any]:
        """Return config-flow data for an SDAP advertisement."""
        return {
            "host": advertisement.host,
            "unique_id": advertisement.unique_id,
            "community": advertisement.community,
            "product_name": advertisement.product_name,
            "serial_number": advertisement.serial_number,
        }

    def _map_exception_to_error(self, exception: Exception) -> str:
        LOGGER.warning("Error in config flow: %s", exception)
        for exception_type, error in ERROR_MAP.items():
            if isinstance(exception, exception_type):
                return error
        return "unknown"


__all__ = ["SonyProjectorConfigFlowHandler"]
