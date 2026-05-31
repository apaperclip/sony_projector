"""Config flow schemas for Sony projector setup."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from custom_components.sony_projector.const import (
    CONF_ADCP_PASSWORD,
    CONF_COMMUNITY,
    CONF_PROTOCOL,
    DEFAULT_ADCP_PASSWORD,
    DEFAULT_SDCP_COMMUNITY,
    PROTOCOL_ADCP,
    PROTOCOL_SDCP,
    PROTOCOLS,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers import selector

CONF_DISCOVERED_PROJECTOR = "discovered_projector"
CONF_SETUP_METHOD = "setup_method"
SETUP_METHOD_LISTEN = "listen"
SETUP_METHOD_MANUAL = "manual"

PROTOCOL_LABELS = {
    PROTOCOL_ADCP: "ADCP (recommended)",
    PROTOCOL_SDCP: "SDCP",
}


def get_setup_method_schema(default: str = SETUP_METHOD_LISTEN) -> vol.Schema:
    """Get schema for choosing discovery or manual setup."""
    return vol.Schema(
        {
            vol.Required(CONF_SETUP_METHOD, default=default): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(
                            value=SETUP_METHOD_LISTEN,
                            label="Listen for discovery (up to 60 seconds)",
                        ),
                        selector.SelectOptionDict(value=SETUP_METHOD_MANUAL, label="Add manually"),
                    ],
                ),
            ),
        },
    )


def get_discovery_schema(
    defaults: Mapping[str, Any] | None = None,
    discoveries: Mapping[str, str] | None = None,
) -> vol.Schema:
    """Get schema for selecting a discovered projector."""
    defaults = defaults or {}
    discoveries = discoveries or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_DISCOVERED_PROJECTOR,
                default=defaults.get(CONF_DISCOVERED_PROJECTOR),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=unique_id, label=label)
                        for unique_id, label in discoveries.items()
                    ],
                ),
            ),
        },
    )


def get_manual_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """Get schema for choosing manual connection details."""
    defaults = defaults or {}
    schema: dict[Any, Any] = {}
    schema[
        vol.Optional(
            CONF_HOST,
            default=defaults.get(CONF_HOST, ""),
        )
    ] = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT))
    schema[
        vol.Required(
            CONF_PROTOCOL,
            default=defaults.get(CONF_PROTOCOL, PROTOCOLS[0]),
        )
    ] = _protocol_selector()
    return vol.Schema(schema)


def get_protocol_auth_schema(protocol: str, defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """Get protocol-specific authentication settings schema."""
    defaults = defaults or {}
    schema: dict[Any, Any] = {}
    if protocol == PROTOCOL_ADCP:
        default_password = defaults.get(CONF_ADCP_PASSWORD)
        if default_password is None and CONF_ADCP_PASSWORD not in defaults:
            default_password = DEFAULT_ADCP_PASSWORD
        if default_password is None:
            default_password = ""
        schema[
            vol.Optional(
                CONF_ADCP_PASSWORD,
                default=default_password,
            )
        ] = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD))
    if protocol == PROTOCOL_SDCP:
        schema[
            vol.Optional(
                CONF_COMMUNITY,
                default=defaults.get(CONF_COMMUNITY, DEFAULT_SDCP_COMMUNITY),
            )
        ] = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT))
    return vol.Schema(schema)


def get_sdap_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    """Get schema for confirming an SDAP-discovered projector."""
    return vol.Schema(
        {
            vol.Required(
                CONF_PROTOCOL,
                default=defaults.get(CONF_PROTOCOL, PROTOCOLS[0]),
            ): _protocol_selector(),
        },
    )


def get_reconfigure_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    """Get schema for reconfiguration."""
    return get_manual_schema(defaults)


def _protocol_selector() -> selector.SelectSelector:
    """Return protocol options in recommended order."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=protocol, label=PROTOCOL_LABELS[protocol]) for protocol in PROTOCOLS
            ],
        ),
    )


__all__ = [
    "CONF_DISCOVERED_PROJECTOR",
    "CONF_SETUP_METHOD",
    "SETUP_METHOD_LISTEN",
    "SETUP_METHOD_MANUAL",
    "get_discovery_schema",
    "get_manual_schema",
    "get_protocol_auth_schema",
    "get_reconfigure_schema",
    "get_sdap_schema",
    "get_setup_method_schema",
]
