"""Options flow schemas for Sony projector."""

from __future__ import annotations

import voluptuous as vol


def get_options_schema() -> vol.Schema:
    """Return an empty options schema for v1."""
    return vol.Schema({})


__all__ = ["get_options_schema"]
