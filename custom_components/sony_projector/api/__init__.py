"""API package for sony_projector."""

from .client import (
    SonyProjectorApiClient,
    SonyProjectorApiClientAuthenticationError,
    SonyProjectorApiClientCommunicationError,
    SonyProjectorApiClientError,
    SonyProjectorApiClientUnsupportedError,
    SonyProjectorCannotIdentifyError,
    is_logically_on,
    is_operational_power_status,
    normalize_power_status,
)

__all__ = [
    "SonyProjectorApiClient",
    "SonyProjectorApiClientAuthenticationError",
    "SonyProjectorApiClientCommunicationError",
    "SonyProjectorApiClientError",
    "SonyProjectorApiClientUnsupportedError",
    "SonyProjectorCannotIdentifyError",
    "is_logically_on",
    "is_operational_power_status",
    "normalize_power_status",
]
