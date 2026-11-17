"""Constants for the McIntosh (serial) integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "mcintosh_serial"

CONF_SERIAL_PORT: Final = "serial_port"
CONF_BAUDRATE: Final = "baudrate"
CONF_MAX_VOLUME: Final = "max_volume"
CONF_INPUT_NAMES: Final = "input_names"  # dict[str(input number), label]

DEFAULT_BAUDRATE: Final = 9600
BAUDRATES: Final = (9600, 19200, 38400, 57600, 115200)

# The unit's own volume steps that map to 100 % in Home Assistant. A conservative cap:
# the real ceiling of the MX119 has not been verified.
DEFAULT_MAX_VOLUME: Final = 40

# Input names from the MX119 owner's manual. Users relabel inputs in the unit's menu,
# so these are editable in the integration options.
DEFAULT_INPUT_NAMES: Final[dict[str, str]] = {
    "0": "Tuner",
    "1": "PH/AUX",
    "2": "CD 2",
    "3": "SAT",
    "4": "TV",
    "5": "DVD",
    "6": "VCR 1",
    "7": "Tape 1",
}

MAIN_ZONE: Final = 1
