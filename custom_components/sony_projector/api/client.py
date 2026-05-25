"""API client wrapper for Sony projector protocols."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from custom_components.sony_projector.const import (
    CONF_ADCP_PASSWORD,
    CONF_COMMUNITY,
    DEFAULT_INPUT_SOURCES,
    DEFAULT_SDCP_COMMUNITY,
    PROTOCOL_ADCP,
    PROTOCOL_SDCP,
)
from custom_components.sony_projector.data import SonyProjectorIdentity, SonyProjectorState


class SonyProjectorApiClientError(Exception):
    """Base exception for projector API errors."""


class SonyProjectorApiClientCommunicationError(SonyProjectorApiClientError):
    """Exception raised for network or timeout errors."""


class SonyProjectorApiClientAuthenticationError(SonyProjectorApiClientError):
    """Exception raised for authentication errors."""


class SonyProjectorApiClientUnsupportedError(SonyProjectorApiClientError):
    """Exception raised when a command is unsupported by protocol or model."""


class SonyProjectorCannotIdentifyError(SonyProjectorApiClientError):
    """Exception raised when a stable projector identity cannot be determined."""


def _protocol_module() -> Any:
    """Return the protocol package imported lazily for HA dependency installation."""
    return import_module("sony_projector_protocol")


def normalize_power_status(power_status: int | str | None) -> str | None:
    """Normalize raw SDAP/protocol power states into specification states."""
    if power_status is None:
        return None
    if isinstance(power_status, int):
        return {
            0: "standby",
            1: "start_up",
            2: "start_up_lamp",
            3: "on",
            4: "cooling",
            5: "cooling2",
        }.get(power_status, str(power_status))

    normalized = power_status.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in {"on", "power_on", "lamp_on", "active", "operational"}:
        return "on"
    if normalized in {"off", "standby", "power_off"}:
        return "standby"
    if normalized in {"cooling", "cool_down", "cooldown"}:
        return "cooling"
    if normalized in {"cooling2", "cooling_2"}:
        return "cooling2"
    if normalized in {"warming", "warm_up", "startup", "start_up", "starting"}:
        return "start_up"
    if normalized in {"start_up_lamp", "startup_lamp"}:
        return "start_up_lamp"
    return normalized or None


def is_operational_power_status(power_status: int | str | None) -> bool:
    """Return true when projector commands beyond power should be available."""
    return normalize_power_status(power_status) == "on"


def is_logically_on(power_status: int | str | None) -> bool | None:
    """Return logical media-player power state from lifecycle status."""
    normalized = normalize_power_status(power_status)
    if normalized is None:
        return None
    if normalized in {"on", "start_up", "start_up_lamp"}:
        return True
    if normalized in {"standby", "off", "cooling", "cooling2"}:
        return False
    return None


class SonyProjectorApiClient:
    """Small async wrapper around sony_projector_protocol.Projector."""

    def __init__(
        self,
        *,
        host: str,
        protocol: str,
        community: str | None = None,
        adcp_password: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        """Initialize the API client."""
        self.host = host
        self.protocol = protocol
        self.community = community or DEFAULT_SDCP_COMMUNITY
        self.adcp_password = adcp_password
        self.timeout = timeout

    async def validate_and_identify(self) -> SonyProjectorIdentity:
        """Validate the connection and return a stable identity."""
        identity = await self.get_identity()
        if identity.unique_id:
            return identity
        msg = "Projector did not expose a serial number or MAC address"
        raise SonyProjectorCannotIdentifyError(msg)

    async def get_identity(self) -> SonyProjectorIdentity:
        """Read projector identity using the configured protocol."""
        async with self._connected_projector() as projector:
            raw_identity = await self._call(projector.get_identity)

        serial = self._string_or_none(getattr(raw_identity, "serial", None))
        mac_address = self._string_or_none(getattr(raw_identity, "mac_address", None))
        model = self._string_or_none(getattr(raw_identity, "model", None))
        location = self._string_or_none(getattr(raw_identity, "location", None))
        unique_id = serial or mac_address
        if unique_id is None:
            msg = "Projector identity did not include a stable identifier"
            raise SonyProjectorCannotIdentifyError(msg)
        return SonyProjectorIdentity(
            unique_id=unique_id,
            model=model,
            serial=serial,
            mac_address=mac_address,
            location=location,
        )

    async def async_get_power_status(self) -> str | None:
        """Fetch the current power status."""
        async with self._connected_projector() as projector:
            return normalize_power_status(await self._call(projector.get_power))

    async def async_get_active_data(self, current_identity: SonyProjectorIdentity | None = None) -> SonyProjectorState:
        """Fetch active-mode data from the projector."""
        async with self._connected_projector() as projector:
            power_status = await self._call(projector.get_power)
            normalized_power_status = normalize_power_status(power_status)
            state = SonyProjectorState(
                device_available=True,
                operational_available=is_operational_power_status(normalized_power_status),
                power_status=normalized_power_status,
                normalized_power_status=normalized_power_status,
                logical_power=is_logically_on(normalized_power_status),
                identity=current_identity,
                source_list=list(DEFAULT_INPUT_SOURCES),
            )

            if state.operational_available:
                state.input = await self._call(projector.get_input)
                state.source_list = self._merge_sources(state.input)
                try:
                    state.lamp_timer = await self._call(projector.get_lamp_timer)
                except SonyProjectorApiClientUnsupportedError:
                    state.lamp_timer_supported = False
            return state

    async def async_set_power(self, power: bool) -> None:
        """Set projector power."""
        async with self._connected_projector() as projector:
            await self._call(projector.set_power, power)

    async def async_set_input(self, source: str) -> None:
        """Set projector input/source."""
        async with self._connected_projector() as projector:
            await self._call(projector.set_input, source)

    async def close(self) -> None:
        """Close any persistent resources."""

    def update_host(self, host: str) -> None:
        """Update the connection target after a DHCP-related advertisement."""
        self.host = host

    def _projector_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "host": self.host,
            "protocol": self.protocol,
            "timeout": self.timeout,
        }
        if self.protocol == PROTOCOL_SDCP:
            kwargs[CONF_COMMUNITY] = self.community
        if self.protocol == PROTOCOL_ADCP:
            kwargs[CONF_ADCP_PASSWORD] = self.adcp_password
        return kwargs

    def _connected_projector(self) -> _ProjectorConnection:
        return _ProjectorConnection(self._projector_kwargs())

    async def _call(self, func: Any, *args: Any) -> Any:
        protocol = _protocol_module()
        try:
            return await func(*args)
        except protocol.ProjectorAuthenticationError as exception:
            msg = f"Projector authentication failed: {exception}"
            raise SonyProjectorApiClientAuthenticationError(msg) from exception
        except protocol.UnsupportedCommandError as exception:
            msg = f"Projector command is unsupported: {exception}"
            raise SonyProjectorApiClientUnsupportedError(msg) from exception
        except (protocol.ProjectorTimeoutError, TimeoutError) as exception:
            msg = f"Projector timed out: {exception}"
            raise SonyProjectorApiClientCommunicationError(msg) from exception
        except protocol.ProjectorConnectionError as exception:
            msg = f"Projector connection failed: {exception}"
            raise SonyProjectorApiClientCommunicationError(msg) from exception
        except protocol.ProjectorError as exception:
            msg = f"Projector protocol failed: {exception}"
            raise SonyProjectorApiClientError(msg) from exception

    def _merge_sources(self, current_source: str | None) -> list[str]:
        sources: list[str] = list(DEFAULT_INPUT_SOURCES)
        if current_source and current_source not in sources:
            sources.append(current_source)
        return sources

    def _string_or_none(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class _ProjectorConnection:
    """Async context manager for one projector protocol session."""

    def __init__(self, kwargs: dict[str, Any]) -> None:
        self._kwargs = kwargs
        self._projector: Any | None = None

    async def __aenter__(self) -> Any:
        protocol = _protocol_module()
        projector = protocol.Projector(**self._kwargs)
        self._projector = projector
        await projector.connect()
        return projector

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._projector is not None:
            await self._projector.close()
