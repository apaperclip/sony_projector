"""Sony Projector media player entity."""

from __future__ import annotations

from custom_components.sony_projector.entity import SonyProjectorEntity
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityDescription
from homeassistant.components.media_player.const import MediaPlayerEntityFeature, MediaPlayerState

ENTITY_DESCRIPTION = MediaPlayerEntityDescription(
    key="projector",
    translation_key="projector",
)


class SonyProjectorMediaPlayer(MediaPlayerEntity, SonyProjectorEntity):
    """Media player for projector power and source control."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, coordinator) -> None:  # type: ignore[no-untyped-def]
        """Initialize the media player."""
        super().__init__(coordinator, ENTITY_DESCRIPTION)

    @property
    def state(self) -> MediaPlayerState | None:
        """Return media player state."""
        if not self.available:
            return None
        if self.coordinator.data.logical_power is False:
            return MediaPlayerState.OFF
        if self.coordinator.data.logical_power is True:
            return MediaPlayerState.ON
        return MediaPlayerState.IDLE

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return self.coordinator.data.input

    @property
    def source_list(self) -> list[str]:
        """Return available input sources."""
        return self.coordinator.data.source_list

    async def async_turn_on(self) -> None:
        """Turn the projector on."""
        await self.coordinator.async_set_power(True)

    async def async_turn_off(self) -> None:
        """Turn the projector off."""
        await self.coordinator.async_set_power(False)

    async def async_select_source(self, source: str) -> None:
        """Select an input source."""
        await self.coordinator.async_set_input(source)
