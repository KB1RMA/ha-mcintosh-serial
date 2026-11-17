from __future__ import annotations

from mcintosh_serial.testing import FakeMX119
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mcintosh_serial.const import (
    CONF_INPUT_NAMES,
    CONF_MAX_VOLUME,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_user_flow_creates_entry(
    hass: HomeAssistant, patched_serial: FakeMX119
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(  # pyright: ignore[reportUnknownMemberType]
        result["flow_id"], {"serial_port": "/dev/fake", "baudrate": "9600"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"serial_port": "/dev/fake", "baudrate": 9600}


async def test_user_flow_reports_cannot_connect(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(  # pyright: ignore[reportUnknownMemberType]
        result["flow_id"], {"serial_port": "/dev/does-not-exist", "baudrate": "9600"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_set_names_and_max_volume(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    names = {f"input_{n}": f"Name {n}" for n in range(8)}
    result = await hass.config_entries.options.async_configure(  # pyright: ignore[reportUnknownMemberType]
        result["flow_id"], {CONF_MAX_VOLUME: 50, **names}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_MAX_VOLUME] == 50
    assert entry.options[CONF_INPUT_NAMES]["3"] == "Name 3"
    await hass.async_block_till_done()


async def test_user_flow_aborts_when_the_port_is_already_configured(
    hass: HomeAssistant, patched_serial: FakeMX119, entry: MockConfigEntry
) -> None:
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(  # pyright: ignore[reportUnknownMemberType]
        result["flow_id"], {"serial_port": "/dev/fake", "baudrate": "9600"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
