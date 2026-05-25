"""Options flow for Sony Projector."""

from __future__ import annotations

from typing import Any

from custom_components.sony_projector.config_flow_handler.schemas import get_options_schema
from homeassistant import config_entries


class SonyProjectorOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage v1 options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=get_options_schema())


__all__ = ["SonyProjectorOptionsFlow"]
