"""Custom types for sony_projector."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import SonyProjectorApiClient
    from .coordinator import SonyProjectorDataUpdateCoordinator
    from .discovery import SonyProjectorDiscoveryManager


type SonyProjectorConfigEntry = ConfigEntry[SonyProjectorData]


@dataclass(slots=True)
class SonyProjectorIdentity:
    """Stable projector identity and metadata."""

    unique_id: str
    model: str | None = None
    serial: str | None = None
    mac_address: str | None = None
    location: str | None = None


@dataclass(slots=True)
class SonyProjectorAdvertisement:
    """Projector data received from SDAP advertisements."""

    host: str
    unique_id: str
    received_at: datetime
    power_status: int | str | None = None
    community: str | None = None
    product_name: str | None = None
    serial_number: str | None = None
    location: str | None = None


@dataclass(slots=True)
class SonyProjectorState:
    """Cached projector state shared with entities."""

    device_available: bool = False
    operational_available: bool = False
    power_status: int | str | None = None
    normalized_power_status: str | None = None
    logical_power: bool | None = None
    input: str | None = None
    signal: str | None = None
    signal_supported: bool = True
    warning: str | None = None
    warning_supported: bool = True
    error: str | None = None
    error_supported: bool = True
    picture_mode: str | None = None
    picture_mode_supported: bool = True
    calibration_preset: str | None = None
    calibration_preset_supported: bool = True
    color_space: str | None = None
    color_space_supported: bool = True
    lamp_timer: int | float | str | None = None
    lamp_timer_supported: bool = True
    identity: SonyProjectorIdentity | None = None
    last_advertisement: SonyProjectorAdvertisement | None = None
    last_update_error: str | None = None
    source_list: list[str] = field(default_factory=list)


@dataclass
class SonyProjectorData:
    """Runtime data for sony_projector config entries."""

    client: SonyProjectorApiClient
    coordinator: SonyProjectorDataUpdateCoordinator
    integration: Integration
    discovery_manager: SonyProjectorDiscoveryManager
