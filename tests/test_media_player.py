from __future__ import annotations

import asyncio

from mcintosh_serial.testing import FakeMX119
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.media_player.const import (
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_VOLUME_LEVEL,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

ENTITY = "media_player.mcintosh_mx119"


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def call(hass: HomeAssistant, service: str, **data: object) -> None:
    await hass.services.async_call(
        "media_player", service, {ATTR_ENTITY_ID: ENTITY, **data}, blocking=True
    )


async def test_initial_state(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    state = hass.states.get(ENTITY)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_MEDIA_VOLUME_LEVEL] == 8 / 40
    assert state.attributes[ATTR_INPUT_SOURCE] == "SAT"
    assert state.attributes["is_volume_muted"] is False
    assert state.attributes["source_list"][4] == "TV"


async def test_volume_mute_and_source(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    await call(hass, "volume_set", volume_level=0.25)
    assert patched_serial.volume[1] == 10
    await call(hass, "volume_up")
    assert patched_serial.volume[1] == 11
    await call(hass, "volume_mute", is_volume_muted=True)
    assert hass.states.get(ENTITY).attributes["is_volume_muted"] is True  # type: ignore[union-attr]
    await call(hass, "volume_mute", is_volume_muted=False)
    await call(hass, "select_source", source="TV")
    assert patched_serial.input[1] == 4
    await asyncio.sleep(0.2)
    assert hass.states.get(ENTITY).attributes[ATTR_INPUT_SOURCE] == "TV"  # type: ignore[union-attr]


async def test_transient_mute_during_input_change_is_hidden(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    seen: list[object] = []
    hass.bus.async_listen(
        "state_changed",
        lambda e: (
            seen.append(e.data["new_state"].attributes.get("is_volume_muted"))
            if e.data["entity_id"] == ENTITY
            else None
        ),
    )
    await call(hass, "select_source", source="DVD")
    await asyncio.sleep(0.3)
    assert True not in seen


async def test_power_off_and_on(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    await call(hass, "turn_off")
    assert hass.states.get(ENTITY).state == STATE_OFF  # type: ignore[union-attr]
    await call(hass, "turn_on")
    await asyncio.sleep(0.2)
    assert hass.states.get(ENTITY).state == STATE_ON  # type: ignore[union-attr]


async def test_front_panel_volume_is_pushed(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    await patched_serial.front_panel_volume(1, 20)
    await asyncio.sleep(0.1)
    assert hass.states.get(ENTITY).attributes[ATTR_MEDIA_VOLUME_LEVEL] == 0.5  # type: ignore[union-attr]


async def test_unavailable_on_disconnect_then_recovers(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    await setup(hass, entry)
    await patched_serial.close()  # transport EOF
    await asyncio.sleep(0.05)
    assert hass.states.get(ENTITY).state == STATE_UNAVAILABLE  # type: ignore[union-attr]
