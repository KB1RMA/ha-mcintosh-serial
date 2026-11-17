"""McIntosh (serial) integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_BAUDRATE, CONF_SERIAL_PORT, MAIN_ZONE
from .hub import Hub

PLATFORMS = [Platform.MEDIA_PLAYER]

type McIntoshConfigEntry = ConfigEntry[Hub]


async def async_setup_entry(hass: HomeAssistant, entry: McIntoshConfigEntry) -> bool:
    """Connect to the receiver and set up its platforms."""
    hub = Hub(entry.data[CONF_SERIAL_PORT], entry.data[CONF_BAUDRATE], MAIN_ZONE)
    try:
        await hub.async_connect()
    except Exception as err:
        raise ConfigEntryNotReady(
            f"Cannot reach McIntosh receiver on {hub.port}: {err}"
        ) from err
    entry.runtime_data = hub
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _options_updated(hass: HomeAssistant, entry: McIntoshConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: McIntoshConfigEntry) -> bool:
    """Unload the platforms and close the serial port."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_close()
    return unloaded
