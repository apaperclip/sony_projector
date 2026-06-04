"""Tests for the Sony projector API client wrapper."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from custom_components.sony_projector.api import (
    SonyProjectorApiClient,
    is_logically_on,
    is_operational_power_status,
    normalize_power_status,
)


class FakeProjectorError(Exception):
    """Base fake projector error."""


class FakeUnsupportedCommandError(FakeProjectorError):
    """Fake unsupported command error."""


class FakeProjector:
    """Fake sony_projector_protocol.Projector."""

    instances: list[FakeProjector] = []
    lamp_unsupported = False

    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.kwargs = kwargs
        FakeProjector.instances.append(self)

    async def connect(self) -> None:
        """Connect fake projector."""

    async def close(self) -> None:
        """Close fake projector."""

    async def get_identity(self) -> SimpleNamespace:
        """Return fake identity."""
        return SimpleNamespace(model="VPL-XW", serial="SERIAL1", mac_address="00:11", location="Cinema")

    async def get_power(self) -> str:
        """Return fake power."""
        return "on"

    async def get_input(self) -> str:
        """Return fake input."""
        return "hdmi2"

    async def get_color_space(self) -> str:
        """Return fake color space."""
        return "bt709"

    async def get_calibration_preset(self) -> str:
        """Return fake calibration preset."""
        return "ref"

    async def get_error_status(self) -> str:
        """Return fake error status."""
        return "no_error"

    async def get_lamp_timer(self) -> int:
        """Return fake lamp timer."""
        if self.lamp_unsupported:
            raise FakeUnsupportedCommandError("no lamp timer")
        return 123

    async def set_power(self, power: bool) -> None:
        """Set fake power."""
        self.power = power

    async def set_input(self, value: str) -> None:
        """Set fake input."""
        self.input = value


@pytest.fixture(autouse=True)
def fake_protocol_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install a fake sony_projector_protocol module."""
    FakeProjector.instances = []
    FakeProjector.lamp_unsupported = False
    module = SimpleNamespace(
        Projector=FakeProjector,
        ProjectorAuthenticationError=type("ProjectorAuthenticationError", (FakeProjectorError,), {}),
        UnsupportedCommandError=FakeUnsupportedCommandError,
        ProjectorTimeoutError=type("ProjectorTimeoutError", (FakeProjectorError,), {}),
        ProjectorConnectionError=type("ProjectorConnectionError", (FakeProjectorError,), {}),
        ProjectorError=FakeProjectorError,
    )
    monkeypatch.setitem(sys.modules, "sony_projector_protocol", module)


def test_power_status_normalization() -> None:
    """Power helpers normalize advertisements and protocol strings."""
    assert normalize_power_status(0) == "standby"
    assert normalize_power_status(1) == "start_up"
    assert normalize_power_status(3) == "on"
    assert normalize_power_status("Power On") == "on"
    assert is_operational_power_status("on") is True
    assert is_operational_power_status("cooling") is False
    assert is_logically_on("warming") is True
    assert is_logically_on("cooling") is False


@pytest.mark.asyncio
async def test_validate_and_active_data_reads_projector() -> None:
    """The client validates identity and reads active projector data."""
    client = SonyProjectorApiClient(host="192.0.2.10", protocol="sdcp", community="SONY")

    identity = await client.validate_and_identify()
    state = await client.async_get_active_data(identity)

    assert identity.unique_id == "SERIAL1"
    assert state.device_available is True
    assert state.operational_available is True
    assert state.input == "hdmi2"
    assert state.color_space == "bt709"
    assert state.calibration_preset == "ref"
    assert state.error == "no_error"
    assert state.lamp_timer == 123
    assert FakeProjector.instances[0].kwargs["host"] == "192.0.2.10"
    assert FakeProjector.instances[0].kwargs["protocol"] == "sdcp"


@pytest.mark.asyncio
async def test_lamp_timer_unsupported_marks_sensor_data_unavailable() -> None:
    """Unsupported lamp timer does not fail the whole update."""
    FakeProjector.lamp_unsupported = True
    client = SonyProjectorApiClient(host="192.0.2.10", protocol="sdcp")

    state = await client.async_get_active_data()

    assert state.operational_available is True
    assert state.lamp_timer is None
    assert state.lamp_timer_supported is False
