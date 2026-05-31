"""API client wrapper for Sony projector protocols."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from custom_components.sony_projector.const import (
    CONF_ADCP_PASSWORD,
    CONF_COMMUNITY,
    DEFAULT_CALIBRATION_PRESETS,
    DEFAULT_INPUT_SOURCES,
    DEFAULT_PICTURE_MODES,
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


def _map_protocol_exception(exception: Exception) -> SonyProjectorApiClientError | None:
    """Map protocol exceptions to integration exceptions."""
    protocol = _protocol_module()
    if isinstance(exception, protocol.ProjectorAuthenticationError):
        return SonyProjectorApiClientAuthenticationError(f"Projector authentication failed: {exception}")
    if isinstance(exception, protocol.UnsupportedCommandError):
        return SonyProjectorApiClientUnsupportedError(f"Projector command is unsupported: {exception}")
    if isinstance(exception, protocol.ProjectorProtocolError) and _is_inactive_response(exception):
        return SonyProjectorApiClientError(f"Projector command is inactive: {exception}")
    if isinstance(exception, (protocol.ProjectorTimeoutError, TimeoutError)):
        return SonyProjectorApiClientCommunicationError(f"Projector timed out: {exception}")
    if isinstance(exception, (protocol.ProjectorConnectionError, OSError)):
        return SonyProjectorApiClientCommunicationError(f"Projector connection failed: {exception}")
    if isinstance(exception, protocol.ProjectorError):
        return SonyProjectorApiClientError(f"Projector protocol failed: {exception}")
    return None


def _is_inactive_response(exception: Exception) -> bool:
    """Return true when the projector reports an active-only command is inactive."""
    response_text = getattr(exception, "response_text", None)
    if response_text is None:
        response = getattr(exception, "response", None)
        response_text = response.decode("ascii", errors="replace") if isinstance(response, bytes) else response
    return isinstance(response_text, str) and response_text.strip().lower() in {"err_inactive", "inactive"}


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

    async def async_get_passive_data(self, current_identity: SonyProjectorIdentity | None = None) -> SonyProjectorState:
        """Fetch data available while the projector is off or passive."""
        async with self._connected_projector() as projector:
            return await self._async_read_state(projector, current_identity=current_identity, include_active=False)

    async def async_get_active_data(self, current_identity: SonyProjectorIdentity | None = None) -> SonyProjectorState:
        """Fetch active-mode data from the projector."""
        async with self._connected_projector() as projector:
            return await self._async_read_state(projector, current_identity=current_identity, include_active=True)

    async def _async_read_state(
        self,
        projector: Any,
        *,
        current_identity: SonyProjectorIdentity | None,
        include_active: bool,
    ) -> SonyProjectorState:
        """Read projector state, including data available during standby."""
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
        try:
            state.lamp_timer = await self._call(self._lamp_timer_func(projector))
        except SonyProjectorApiClientUnsupportedError:
            state.lamp_timer_supported = False

        if include_active and state.operational_available:
            state.input = await self._call(projector.get_input)
            state.source_list = self._merge_sources(state.input)
            if self.protocol == PROTOCOL_ADCP:
                try:
                    state.signal = await self._call(projector.get_signal)
                except SonyProjectorApiClientUnsupportedError:
                    state.signal_supported = False
                except SonyProjectorApiClientError:
                    pass
                try:
                    state.picture_mode = self._normalize_picture_mode(await self._call(projector.get_picture_mode))
                except SonyProjectorApiClientUnsupportedError:
                    state.picture_mode_supported = False
                except SonyProjectorApiClientError:
                    state.picture_mode_supported = False
            if self.protocol == PROTOCOL_SDCP:
                try:
                    state.calibration_preset = await self._call(projector.get_calibration_preset)
                except SonyProjectorApiClientUnsupportedError:
                    state.calibration_preset_supported = False
                except SonyProjectorApiClientError:
                    pass
        return state

    async def async_set_power(self, power: bool) -> None:
        """Set projector power."""
        async with self._connected_projector() as projector:
            await self._call(projector.set_power, power)

    async def async_set_input(self, source: str) -> None:
        """Set projector input/source."""
        async with self._connected_projector() as projector:
            await self._call(projector.set_input, source)

    async def async_set_picture_mode(self, picture_mode: str) -> None:
        """Set the ADCP picture mode."""
        async with self._connected_projector() as projector:
            await self._call(projector.set_picture_mode, picture_mode)

    async def async_set_calibration_preset(self, calibration_preset: str) -> None:
        """Set the SDCP calibration preset."""
        async with self._connected_projector() as projector:
            await self._call(projector.set_calibration_preset, calibration_preset)

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

    def _lamp_timer_func(self, projector: Any) -> Any:
        """Return the lamp timer command for the configured protocol."""
        if self.protocol == PROTOCOL_ADCP:
            return projector.get_timer
        return projector.get_lamp_timer

    def _connected_projector(self) -> _ProjectorConnection:
        return _ProjectorConnection(self._projector_kwargs())

    async def _call(self, func: Any, *args: Any) -> Any:
        try:
            return await func(*args)
        except Exception as exception:
            mapped = _map_protocol_exception(exception)
            if mapped is None:
                raise
            raise mapped from exception

    def _merge_sources(self, current_source: str | None) -> list[str]:
        sources: list[str] = list(DEFAULT_INPUT_SOURCES)
        if current_source and current_source not in sources:
            sources.append(current_source)
        return sources

    def picture_mode_options(self, model: str | None = None, current_mode: str | None = None) -> list[str]:
        """Return ADCP picture mode options for a projector model."""
        options = self._adcp_picture_mode_options(model)
        return self._merge_options(options, self._normalize_picture_mode(current_mode))

    def calibration_preset_options(self, current_preset: str | None = None) -> list[str]:
        """Return SDCP calibration preset options, preserving model-specific current presets."""
        return self._merge_options(DEFAULT_CALIBRATION_PRESETS, current_preset)

    def _merge_options(self, defaults: tuple[str, ...], current_value: str | None) -> list[str]:
        options = list(defaults)
        if current_value and current_value not in options:
            options.append(current_value)
        return options

    def _adcp_picture_mode_options(self, model: str | None) -> tuple[str, ...]:
        protocol = _protocol_module()
        get_options = getattr(protocol, "get_adcp_picture_mode_options", None)
        if model and get_options is not None:
            model_options = get_options(model)
            if model_options:
                return tuple(self._normalize_picture_mode(option) or option for option in model_options)

        protocol_options = getattr(protocol, "ADCP_PICTURE_MODE_VALUES", DEFAULT_PICTURE_MODES)
        return tuple(self._normalize_picture_mode(option) or option for option in protocol_options)

    def _normalize_picture_mode(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().strip('"').lower()
        if "=" in normalized:
            normalized = normalized.split("=", 1)[1].strip().strip('"')
        normalized = normalized.replace("-", "_").replace(" ", "_")
        return {
            "bright_cinema": "brt_cinema",
            "bright_tv": "brt_tv",
            "cinema_film_1": "cinema_film1",
            "cinema_film_2": "cinema_film2",
            "ref": "reference",
        }.get(normalized, normalized or None)

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
        try:
            await projector.connect()
        except Exception as exception:
            mapped = _map_protocol_exception(exception)
            if mapped is None:
                raise
            raise mapped from exception
        return projector

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._projector is not None:
            await self._projector.close()
