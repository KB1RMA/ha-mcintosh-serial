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
- A serial connection from the Home Assistant host to the receiver's RS232 port: a USB-to-serial adapter on
  that host, or a network serial server (use a pyserial URL such as `socket://host:port`). On an MX119 the
  port is a DB9 (pin 2 TXD, pin 3 RXD, pin 5 ground) at 9600 baud. When Home Assistant runs in a container,
  the serial device has to be passed through to it.

## Installation

Add this repository to HACS as a custom repository (category: Integration), install **McIntosh (serial)** and
restart Home Assistant.

## Setup

Add the integration from Settings → Devices & services, then enter the serial device path (for example
`/dev/ttyUSB0`) or URL and the baud rate. The integration connects, enables RS232 control on the receiver if
needed and reads its state.

## Development

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pyright
uv run pytest            # 100% branch coverage is required
```

The tests run the integration against the library's emulated MX119. While the library is unreleased it is
taken from `../mcintosh-serial` (see `[tool.uv.sources]` in `pyproject.toml`).

## Licence

MIT. See [LICENSE](LICENSE).
