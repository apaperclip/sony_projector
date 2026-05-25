"""Service actions package for Sony Projector.

V1 exposes projector controls through the media_player entity and does not
register custom services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register v1 services."""
