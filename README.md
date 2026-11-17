# McIntosh (serial)

[![GitHub release](https://img.shields.io/github/v/release/KB1RMA/ha-mcintosh-serial)](https://github.com/KB1RMA/ha-mcintosh-serial/releases/latest)
[![Marketplace: custom repository](https://img.shields.io/badge/Marketplace-custom_repository-41BDF5)](#installation)
[![Home Assistant 2026.10+](https://img.shields.io/badge/Home_Assistant-2026.10%2B-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![CI](https://github.com/KB1RMA/ha-mcintosh-serial/actions/workflows/ci.yml/badge.svg)](https://github.com/KB1RMA/ha-mcintosh-serial/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/KB1RMA/ha-mcintosh-serial/graph/badge.svg)](https://codecov.io/gh/KB1RMA/ha-mcintosh-serial)
[![License: MIT](https://img.shields.io/github/license/KB1RMA/ha-mcintosh-serial)](LICENSE)

[![Open your Home Assistant instance and open this repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=KB1RMA&repository=ha-mcintosh-serial&category=integration)

A Home Assistant custom integration that controls a McIntosh receiver over its RS232 port, so it can be
driven from automations and used as the power and volume control for players such as Music Assistant.

This project is independent. It is not affiliated with or endorsed by McIntosh Laboratory.

> **Status:** early. Verified on one unit, a McIntosh MX119 (main zone only). The protocol work lives in the
> [mcintosh-serial](https://github.com/KB1RMA/mcintosh-serial) library, which lists the other command styles
> McIntosh has used and which are not supported yet.

## Entity

One `media_player` for the main zone:

- **Power**, **volume** (set and step), **mute** and **source** selection.
- **Changes made on the receiver** (knob, remote, front panel) appear in Home Assistant immediately; there is no polling.
- **Volume:** Home Assistant's 0-100 % maps onto the receiver's own volume steps, up to a configurable
  "receiver volume at 100 %" (default 40). The MX119's true maximum has not been verified, so treat this as a safety cap.
- **Sources:** names default to the MX119 manual (Tuner, PH/AUX, CD 2, SAT, TV, DVD, VCR 1, Tape 1). If you
  relabeled inputs on the unit, rename them in the integration options.
- **Mute:** the receiver mutes itself briefly while changing input or powering on. Those moments are not
  shown as mute.
- **Availability:** if the link drops the entity becomes unavailable and the integration retries every 10 seconds.

## Requirements

- Home Assistant 2026.10 or later.
- A serial connection from Home Assistant to the receiver's RS-232 port. On an MX119 the port is a DB9
  (pin 2 TXD, pin 3 RXD, pin 5 ground) at 9600 baud. Either:
  - **A Home Assistant Connect AUX-2** (or any ESPHome device with a
    [serial proxy](https://esphome.io/components/serial_proxy/)). Its RS-232 ports appear in the serial port
    list under "Serial proxies", so nothing has to be plugged into the Home Assistant host. Use RS-232 Port 1
    or 2, never the 3.5 mm audio output. Each port has a TX/RX switch on the underside; if the receiver does
    not answer, try the other position. The stock firmware runs the ports at 9600 baud.
  - **A USB-to-serial adapter** on the Home Assistant host. When Home Assistant runs in a container, pass
    the device through to it and pick it by its `/dev/serial/by-id/...` path.
  - **A network serial server** (`ser2net`, `socat`, ...), entered manually as `socket://host:port`. The baud
    rate is then set on the server.

## Installation

Add this repository to HACS as a custom repository (category: Integration), install **McIntosh (serial)** and
restart Home Assistant.

## Setup

Add the integration from Settings → Devices & services and pick the serial port the receiver is connected to
(the AUX-2's RS-232 port, a USB adapter, or enter a URL manually). Leave the baud rate at 9600 for an MX119.
The integration connects, enables RS-232 control on the receiver if needed and reads its state.

### Using it with Music Assistant

In Music Assistant, expose the media player through the Home Assistant plugin, then open the player that feeds
the receiver, go to its Player controls and choose this entity for power, volume and mute. Music Assistant can
then wake the receiver and set its volume when playback starts.

## Development

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pyright
uv run pytest            # 100% branch coverage is required
```

The tests run the integration against the library's emulated MX119. To develop against an unreleased
library, temporarily add `[tool.uv.sources]` with `mcintosh-serial = { path = "../mcintosh-serial", editable = true }`.

## Licence

MIT. See [LICENSE](LICENSE).
