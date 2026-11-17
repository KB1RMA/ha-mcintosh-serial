# Changelog

## [0.1.0](https://github.com/KB1RMA/ha-mcintosh-serial/releases/tag/v0.1.0) (2026-11-17)


### Features

* a media player for the main zone of a McIntosh MX119 over RS-232: power, volume, mute and source, with changes made on the receiver pushed to Home Assistant
* serial ports are picked with Home Assistant's serial port selector, so a Home Assistant Connect AUX-2's RS-232 ports (ESPHome serial proxy), USB adapters and manual `socket://` URLs all work
* a config flow for the serial port and baud rate, and options for the volume cap and input names
* reconnects automatically after the serial link drops


### Dependencies

* mcintosh-serial 0.3.0
