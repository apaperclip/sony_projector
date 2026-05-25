"""Diagnostics support for Sony Projector."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from types import NoneType
from typing import TYPE_CHECKING, Any, cast

from custom_components.sony_projector.const import SENSITIVE_CONFIG_KEYS
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.redact import async_redact_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SonyProjectorConfigEntry


def _dataclass_to_dict(value: object) -> dict[str, Any] | None:
    if isinstance(value, NoneType) or not is_dataclass(value) or isinstance(value, type):
        return None
    return asdict(cast(Any, value))


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: SonyProjectorConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    client = entry.runtime_data.client
    integration = entry.runtime_data.integration

    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)
    devices = []
    for device in dr.async_entries_for_config_entry(device_reg, entry.entry_id):
        entities = er.async_entries_for_device(entity_reg, device.id)
        devices.append(
            {
                "id": device.id,
                "name": device.name,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "serial_number": device.serial_number,
                "entity_count": len(entities),
                "entities": [
                    {
                        "entity_id": entity.entity_id,
                        "platform": entity.platform,
                        "original_name": entity.original_name,
                        "disabled": entity.disabled,
                        "disabled_by": entity.disabled_by.value if entity.disabled_by else None,
                    }
                    for entity in entities
                ],
            },
        )

    state = coordinator.data
    data = {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "domain": entry.domain,
            "title": entry.title,
            "state": str(entry.state),
            "unique_id": entry.unique_id,
            "disabled_by": entry.disabled_by.value if entry.disabled_by else None,
            "data": async_redact_data(entry.data, SENSITIVE_CONFIG_KEYS),
            "options": async_redact_data(entry.options, SENSITIVE_CONFIG_KEYS),
        },
        "integration": {
            "name": integration.name,
            "version": integration.version,
            "domain": integration.domain,
            "documentation": integration.documentation,
            "issue_tracker": integration.issue_tracker,
        },
        "api": {
            "host": client.host,
            "protocol": client.protocol,
            "has_community": bool(client.community),
            "has_adcp_password": bool(client.adcp_password),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "last_exception": str(coordinator.last_exception) if coordinator.last_exception else None,
            "last_exception_type": type(coordinator.last_exception).__name__ if coordinator.last_exception else None,
        },
        "state": {
            "device_available": state.device_available,
            "operational_available": state.operational_available,
            "power_status": state.power_status,
            "normalized_power_status": state.normalized_power_status,
            "logical_power": state.logical_power,
            "input": state.input,
            "lamp_timer_supported": state.lamp_timer_supported,
            "identity": _dataclass_to_dict(state.identity),
            "last_advertisement": _dataclass_to_dict(state.last_advertisement),
            "last_update_error": state.last_update_error,
        },
        "devices": devices,
    }
    return async_redact_data(data, SENSITIVE_CONFIG_KEYS)
