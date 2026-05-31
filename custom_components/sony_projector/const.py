"""Constants for sony_projector."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "sony_projector"
MANUFACTURER = "Sony"

PARALLEL_UPDATES = 1

CONF_PROTOCOL = "protocol"
CONF_COMMUNITY = "community"
CONF_ADCP_PASSWORD = "adcp_password"
CONF_UNIQUE_ID = "unique_id"
CONF_SETUP_SOURCE = "setup_source"

PROTOCOL_ADCP = "adcp"
PROTOCOL_SDCP = "sdcp"
PROTOCOLS = (PROTOCOL_ADCP, PROTOCOL_SDCP)

SETUP_SOURCE_MANUAL = "manual"
SETUP_SOURCE_SDAP = "sdap"

DEFAULT_SDCP_COMMUNITY = "SONY"
DEFAULT_ADCP_PASSWORD = "Projector"

SDAP_PORT = 53862
ADVERTISEMENT_TIMEOUT_SECONDS = 90
ACTIVE_POLL_INTERVAL_SECONDS = 10
PASSIVE_POLL_INTERVAL_SECONDS = 60

DEFAULT_INPUT_SOURCES = ("hdmi1", "hdmi2")
DEFAULT_PICTURE_MODES = (
    "brt_cinema",
    "brt_tv",
    "cinema_digital",
    "cinema_film1",
    "cinema_film2",
    "game",
    "photo",
    "reference",
    "tv",
    "user",
    "user1",
    "user2",
    "user3",
)
DEFAULT_CALIBRATION_PRESETS = (
    "cinema_film_1",
    "cinema_film_2",
    "ref",
    "tv",
    "photo",
    "game",
    "bright_cinema",
    "bright_tv",
    "user",
)
SENSITIVE_CONFIG_KEYS = {
    CONF_ADCP_PASSWORD,
    CONF_COMMUNITY,
    "password",
    "token",
    "api_key",
}
