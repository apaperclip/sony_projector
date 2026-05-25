"""Projector connection validators."""

from __future__ import annotations

from custom_components.sony_projector.api import SonyProjectorApiClient
from custom_components.sony_projector.data import SonyProjectorIdentity


async def validate_projector_connection(
    *,
    host: str,
    protocol: str,
    community: str | None,
    adcp_password: str | None,
) -> SonyProjectorIdentity:
    """Validate projector connection and return stable identity."""
    client = SonyProjectorApiClient(
        host=host,
        protocol=protocol,
        community=community,
        adcp_password=adcp_password,
    )
    return await client.validate_and_identify()


__all__ = ["validate_projector_connection"]
