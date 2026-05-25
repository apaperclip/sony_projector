"""Tests for SDAP discovery handling."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from custom_components.sony_projector.const import DOMAIN
from custom_components.sony_projector.discovery import SonyProjectorDiscoveryManager


class FakeFlowManager:
    """Fake config flow manager."""

    def __init__(self) -> None:
        self.inits: list[dict[str, Any]] = []
        self.progress: list[dict[str, Any]] = []

    async def async_init(self, domain: str, *, context: dict[str, Any], data: dict[str, Any]) -> None:
        """Record a flow init."""
        self.inits.append({"domain": domain, "context": context, "data": data})

    def async_progress_by_handler(
        self,
        handler: str,
        *,
        match_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return matching fake flows in progress."""
        assert handler == DOMAIN
        if match_context is None:
            return self.progress
        return [flow for flow in self.progress if match_context.items() <= flow.get("context", {}).items()]


class FakeConfigEntries:
    """Fake config entries manager."""

    def __init__(self, entries: list[Any] | None = None) -> None:
        self.flow = FakeFlowManager()
        self.entries = entries or []
        self.updated: list[tuple[Any, dict[str, Any]]] = []

    def async_entries(self, domain: str) -> list[Any]:
        """Return entries for a domain."""
        assert domain == DOMAIN
        return self.entries

    def async_update_entry(self, entry: Any, *, data: dict[str, Any]) -> None:
        """Record entry updates."""
        self.updated.append((entry, data))
        entry.data = data


class FakeHass:
    """Small fake Home Assistant object."""

    def __init__(self, entries: list[Any] | None = None) -> None:
        self.data: dict[str, Any] = {}
        self.config_entries = FakeConfigEntries(entries)

    def async_create_task(self, task: Any) -> Any:
        """Return scheduled task placeholder."""
        return task


@pytest.fixture(autouse=True)
def fake_protocol_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install a fake protocol parser."""

    def parse_sdap_packet(data: bytes, ip: str) -> SimpleNamespace:
        return SimpleNamespace(
            ip=ip,
            serial_number=12345,
            id="DA",
            community="SONY",
            product_name="VPL-XW",
            power_status=1,
            location="Cinema",
        )

    monkeypatch.setattr(
        "custom_components.sony_projector.discovery.parse_sdap_packet",
        parse_sdap_packet,
    )


@pytest.mark.asyncio
async def test_unknown_advertisement_starts_discovery_flow() -> None:
    """Unknown SDAP advertisements create a config flow."""
    hass = FakeHass()
    manager = SonyProjectorDiscoveryManager(hass)  # type: ignore[arg-type]

    await manager._async_handle_datagram(b"packet", "192.0.2.20")  # noqa: SLF001

    assert "12345" in manager.advertisements
    assert hass.config_entries.flow.inits == [
        {
            "domain": DOMAIN,
            "context": {"source": "sdap", "unique_id": "12345"},
            "data": {
                "host": "192.0.2.20",
                "unique_id": "12345",
                "received_at": manager.advertisements["12345"].received_at,
                "power_status": 1,
                "community": "SONY",
                "product_name": "VPL-XW",
                "serial_number": "12345",
                "location": "Cinema",
            },
        },
    ]


@pytest.mark.asyncio
async def test_known_advertisement_updates_entry_and_callback() -> None:
    """Known SDAP advertisements refresh host and loaded coordinator callback."""
    entry = SimpleNamespace(unique_id="12345", data={"host": "192.0.2.10"})
    hass = FakeHass([entry])
    manager = SonyProjectorDiscoveryManager(hass)  # type: ignore[arg-type]
    seen = []
    manager.async_register_entry_callback("12345", seen.append)

    await manager._async_handle_datagram(b"packet", "192.0.2.21")  # noqa: SLF001

    assert entry.data["host"] == "192.0.2.21"
    assert hass.config_entries.updated[0][1]["host"] == "192.0.2.21"
    assert seen[0].host == "192.0.2.21"
    assert hass.config_entries.flow.inits == []


@pytest.mark.asyncio
async def test_repeated_advertisement_does_not_create_duplicate_flow() -> None:
    """Repeated SDAP advertisements do not create duplicate discovery flows."""
    hass = FakeHass()
    hass.config_entries.flow.progress.append({"context": {"source": "sdap", "unique_id": "12345"}})
    manager = SonyProjectorDiscoveryManager(hass)  # type: ignore[arg-type]

    await manager._async_handle_datagram(b"packet", "192.0.2.20")  # noqa: SLF001

    assert "12345" in manager.advertisements
    assert hass.config_entries.flow.inits == []


@pytest.mark.asyncio
async def test_user_flow_suppresses_automatic_discovery_flow() -> None:
    """An open user setup flow lets advertisements populate the picker only."""
    hass = FakeHass()
    hass.config_entries.flow.progress.append({"context": {"source": "user"}})
    manager = SonyProjectorDiscoveryManager(hass)  # type: ignore[arg-type]

    await manager._async_handle_datagram(b"packet", "192.0.2.20")  # noqa: SLF001

    assert "12345" in manager.advertisements
    assert hass.config_entries.flow.inits == []
