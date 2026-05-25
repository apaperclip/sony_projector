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
    PROTOCOLS,
)
from homeassistant.const import CONF_HOST
from homeassistant.helpers import selector

CONF_DISCOVERED_PROJECTOR = "discovered_projector"


def get_user_schema(
    defaults: Mapping[str, Any] | None = None,
    discoveries: Mapping[str, str] | None = None,
) -> vol.Schema:
    """Get schema for manual setup or selecting a discovered projector."""
    defaults = defaults or {}
    discoveries = discoveries or {}
    schema: dict[Any, Any] = {}
    if discoveries:
        schema[
            vol.Optional(
                CONF_DISCOVERED_PROJECTOR,
                default=defaults.get(CONF_DISCOVERED_PROJECTOR),
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=unique_id, label=label) for unique_id, label in discoveries.items()
                ],
            ),
        )

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
    ] = selector.SelectSelector(selector.SelectSelectorConfig(options=list(PROTOCOLS)))
    schema[
        vol.Optional(
            CONF_COMMUNITY,
            default=defaults.get(CONF_COMMUNITY, DEFAULT_SDCP_COMMUNITY),
        )
    ] = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT))
    schema[
        vol.Optional(
            CONF_ADCP_PASSWORD,
            default=defaults.get(CONF_ADCP_PASSWORD, DEFAULT_ADCP_PASSWORD),
        )
    ] = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD))
    return vol.Schema(schema)


def get_sdap_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    """Get schema for confirming an SDAP-discovered projector."""
    return vol.Schema(
        {
            vol.Required(
                CONF_PROTOCOL,
                default=defaults.get(CONF_PROTOCOL, PROTOCOLS[0]),
            ): selector.SelectSelector(selector.SelectSelectorConfig(options=list(PROTOCOLS))),
            vol.Optional(
                CONF_COMMUNITY,
                default=defaults.get(CONF_COMMUNITY, DEFAULT_SDCP_COMMUNITY),
            ): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)),
            vol.Optional(
                CONF_ADCP_PASSWORD,
                default=defaults.get(CONF_ADCP_PASSWORD, DEFAULT_ADCP_PASSWORD),
            ): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        },
    )


def get_reconfigure_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    """Get schema for reconfiguration."""
    return get_user_schema(defaults)


__all__ = [
    "CONF_DISCOVERED_PROJECTOR",
    "get_reconfigure_schema",
    "get_sdap_schema",
    "get_user_schema",
]
