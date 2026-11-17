# Changelog

## Unreleased

### Features

* a media player for the main zone of a McIntosh MX119 over RS232: power, volume, mute and source, with changes made on the receiver pushed to Home Assistant
* a config flow for the serial port and baud rate, and options for the volume cap and input names
* reconnects automatically after the serial link drops
* serial ports are picked with Home Assistant's serial port selector, so a Home Assistant Connect AUX-2's RS-232 ports (ESPHome serial proxy), USB adapters and manual `socket://` URLs all work
