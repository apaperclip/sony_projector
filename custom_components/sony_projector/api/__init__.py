"""
API package for sony_projector.

Architecture:
    Three-layer data flow: Entities → Coordinator → API Client.
    Only the coordinator should call the API client. Entities must never
    import or call the API client directly.

Exception hierarchy:
    SonyProjectorApiClientError (base)
    ├── SonyProjectorApiClientCommunicationError (network/timeout)
    └── SonyProjectorApiClientAuthenticationError (401/403)

Coordinator exception mapping:
    ApiClientAuthenticationError → ConfigEntryAuthFailed (triggers reauth)
    ApiClientCommunicationError → UpdateFailed (auto-retry)
    ApiClientError             → UpdateFailed (auto-retry)
"""

from .client import (
    SonyProjectorApiClient,
    SonyProjectorApiClientAuthenticationError,
    SonyProjectorApiClientCommunicationError,
    SonyProjectorApiClientError,
)

__all__ = [
    "SonyProjectorApiClient",
    "SonyProjectorApiClientAuthenticationError",
    "SonyProjectorApiClientCommunicationError",
    "SonyProjectorApiClientError",
]
