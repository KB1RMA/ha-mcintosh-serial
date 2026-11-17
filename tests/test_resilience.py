"""Failure handling: rejected commands, lost links, reconnects and unloading."""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from mcintosh_serial.testing import FakeMX119
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.mcintosh_serial import hub as hub_module
from custom_components.mcintosh_serial.const import CONF_INPUT_NAMES, DOMAIN
from custom_components.mcintosh_serial.media_player import INPUT_HOLD
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

ENTITY = "media_player.mcintosh_mx119"


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def call(hass: HomeAssistant, service: str, **data: object) -> None:
    await hass.services.async_call(
        "media_player", service, {ATTR_ENTITY_ID: ENTITY, **data}, blocking=True
    )


async def test_volume_down(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    await call(hass, "volume_down")
    assert patched_serial.volume[1] == 7


async def test_unknown_source_is_rejected(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    with pytest.raises(HomeAssistantError, match="Unknown source"):
        await call(hass, "select_source", source="Betamax")


async def test_a_rejected_command_becomes_a_home_assistant_error(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    patched_serial.rs232_enabled = False  # the unit now answers (ERR 1) to everything
    with pytest.raises(HomeAssistantError, match="volume up failed"):
        await call(hass, "volume_up")


async def test_mute_state_follows_the_unit_once_the_hold_ends(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    await call(hass, "select_source", source="TV")
    await asyncio.sleep(0.2)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=INPUT_HOLD + 2))
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY)
    assert state is not None
    assert state.attributes["is_volume_muted"] is False


async def test_custom_input_names_are_used(
    hass: HomeAssistant, patched_serial: FakeMX119
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="McIntosh MX119",
        data={"serial_port": "/dev/fake", "baudrate": 9600},
        options={CONF_INPUT_NAMES: {"3": "Living room TV"}},
        unique_id="/dev/fake",
    )
    await setup(hass, entry)
    state = hass.states.get(ENTITY)
    assert state is not None
    assert state.attributes["source"] == "Living room TV"


async def test_reconnects_after_the_link_drops(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    hub = entry.runtime_data
    attempts = 0
    real_open = hub_module.open_serial

    async def flaky_open(port: str, baud: int) -> FakeMX119:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            message = "adapter unplugged"
            raise OSError(message)
        return await real_open(port, baud)  # pyright: ignore[reportReturnType]

    with patch.object(hub_module, "open_serial", flaky_open):
        await patched_serial.close()
        await asyncio.sleep(0.02)
        assert hass.states.get(ENTITY).state == STATE_UNAVAILABLE  # pyright: ignore[reportOptionalMemberAccess]
        with pytest.raises(ConnectionError):
            _ = hub.client
        await asyncio.sleep(0.4)
    assert attempts >= 2
    assert hass.states.get(ENTITY).state == STATE_ON  # pyright: ignore[reportOptionalMemberAccess]


async def test_unloading_while_disconnected_stops_reconnecting(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    with patch.object(
        hub_module, "open_serial", AsyncMock(side_effect=OSError("gone"))
    ):
        await patched_serial.close()
        await asyncio.sleep(0.1)
        assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_unload_closes_the_port(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_a_failed_platform_unload_keeps_the_connection(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=False),
    ):
        assert not await hass.config_entries.async_unload(entry.entry_id)
    assert entry.runtime_data.available
    await entry.runtime_data.async_close()


async def test_setup_retries_when_the_receiver_does_not_answer(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    with patch.object(
        hub_module, "open_serial", AsyncMock(side_effect=OSError("no port"))
    ):
        entry.add_to_hass(hass)
        assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
