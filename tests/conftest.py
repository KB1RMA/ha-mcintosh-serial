"""Shared fixtures: the integration talks to the library's emulated MX119."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from mcintosh_serial import Timing
from mcintosh_serial.testing import FakeMX119
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mcintosh_serial import hub as hub_module
from custom_components.mcintosh_serial.const import (
    CONF_BAUDRATE,
    CONF_SERIAL_PORT,
    DOMAIN,
)

FAST = Timing(
    command=0.5, query=1.0, power=2.0, settle=0.05, settle_max=0.5, retry_delay=0.02
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    return None


@pytest.fixture
def device() -> FakeMX119:
    return FakeMX119(time_scale=0.01)


@pytest.fixture
def patched_serial(device: FakeMX119) -> Generator[FakeMX119]:
    async def fake_open(_port: str, _baud: int) -> FakeMX119:
        return device

    with (
        patch.object(hub_module, "open_serial", fake_open),
        patch.object(hub_module, "TIMING", FAST),
        patch.object(hub_module, "RECONNECT_DELAY", 0.05),
    ):
        yield device


@pytest.fixture
def entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="McIntosh MX119",
        data={CONF_SERIAL_PORT: "/dev/fake", CONF_BAUDRATE: 9600},
        unique_id="/dev/fake",
    )
