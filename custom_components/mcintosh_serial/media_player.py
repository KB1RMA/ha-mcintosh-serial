"""Media player entity for the main zone."""

from collections.abc import Awaitable, Callable
from time import monotonic
from typing import override

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_call_later
from mcintosh_serial import McIntoshError

from . import McIntoshConfigEntry
from .const import (
    CONF_INPUT_NAMES,
    CONF_MAX_VOLUME,
    DEFAULT_INPUT_NAMES,
    DEFAULT_MAX_VOLUME,
    DOMAIN,
)
from .hub import Hub

# The unit mutes itself while switching input (about 1.5 s) and powering on (about 6 s).
# Those pushes are not user mutes, so they are held back from the entity for a while.
INPUT_HOLD = 3.0
POWER_HOLD = 9.0
_RELEASE_MARGIN = 0.5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: McIntoshConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the main-zone media player."""
    async_add_entities([McIntoshMediaPlayer(entry)])


class McIntoshMediaPlayer(MediaPlayerEntity):
    """The receiver's main zone."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, entry: McIntoshConfigEntry) -> None:
        self._hub: Hub = entry.runtime_data
        self._max_volume: int = entry.options.get(CONF_MAX_VOLUME, DEFAULT_MAX_VOLUME)
        names: dict[str, str] = {
            **DEFAULT_INPUT_NAMES,
            **entry.options.get(CONF_INPUT_NAMES, {}),
        }
        self._name_by_input = {int(number): name for number, name in names.items()}
        self._input_by_name = {
            name: number for number, name in self._name_by_input.items()
        }
        self._attr_unique_id = entry.entry_id
        self._attr_source_list = list(self._name_by_input.values())
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="McIntosh",
            model="MX119",
            name=entry.title,
        )
        self._hold_until = 0.0
        self._last_key: tuple[bool | None, int | None] | None = None
        self._release: CALLBACK_TYPE | None = None

    @override
    async def async_added_to_hass(self) -> None:
        """Read the first state and follow the receiver's pushes."""
        self._sync()
        self.async_on_remove(self._hub.add_listener(self._on_update))
        self.async_on_remove(self._cancel_release)

    # --------------------------------------------------------- state mapping
    @callback
    def _on_update(self) -> None:
        self._sync()
        self.async_write_ha_state()

    @callback
    def _sync(self) -> None:
        zone = self._hub.zone_state
        key = (zone.power, zone.input)
        if self._last_key is not None and key != self._last_key:
            powered_changed = key[0] != self._last_key[0]
            self._hold_for(POWER_HOLD if powered_changed else INPUT_HOLD)
        self._last_key = key
        if monotonic() >= self._hold_until:
            self._attr_is_volume_muted = zone.muted
        self._attr_available = self._hub.available
        self._attr_state = MediaPlayerState.ON if zone.power else MediaPlayerState.OFF
        self._attr_volume_level = (
            None if zone.volume is None else min(zone.volume / self._max_volume, 1.0)
        )
        self._attr_source = (
            None
            if zone.input is None
            else self._name_by_input.get(zone.input, f"Input {zone.input}")
        )

    @callback
    def _hold_for(self, seconds: float) -> None:
        self._hold_until = max(self._hold_until, monotonic() + seconds)
        self._cancel_release()
        self._release = async_call_later(
            self.hass, seconds + _RELEASE_MARGIN, self._release_hold
        )

    @callback
    def _release_hold(self, _now: object) -> None:
        self._release = None
        self._attr_is_volume_muted = self._hub.zone_state.muted
        self.async_write_ha_state()

    @callback
    def _cancel_release(self) -> None:
        release, self._release = self._release, None
        if release is not None:
            release()

    # -------------------------------------------------------------- commands
    @staticmethod
    async def _run(name: str, call: Callable[[], Awaitable[None]]) -> None:
        try:
            await call()
        except (McIntoshError, ConnectionError) as err:
            raise HomeAssistantError(f"McIntosh {name} failed: {err}") from err

    @override
    async def async_turn_on(self) -> None:
        """Turn the zone on."""
        self._hold_for(POWER_HOLD)
        await self._run(
            "power on", lambda: self._hub.client.set_power(self._hub.zone, on=True)
        )

    @override
    async def async_turn_off(self) -> None:
        """Turn the zone off."""
        await self._run(
            "power off", lambda: self._hub.client.set_power(self._hub.zone, on=False)
        )

    @override
    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume as a fraction of the configured maximum."""
        level = round(max(0.0, min(volume, 1.0)) * self._max_volume)
        await self._run(
            "set volume", lambda: self._hub.client.set_volume(self._hub.zone, level)
        )

    @override
    async def async_volume_up(self) -> None:
        """Raise the volume one step."""
        await self._run(
            "volume up", lambda: self._hub.client.volume_step(self._hub.zone, up=True)
        )

    @override
    async def async_volume_down(self) -> None:
        """Lower the volume one step."""
        await self._run(
            "volume down",
            lambda: self._hub.client.volume_step(self._hub.zone, up=False),
        )

    @override
    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute."""
        await self._run(
            "mute", lambda: self._hub.client.set_mute(self._hub.zone, muted=mute)
        )
        self._attr_is_volume_muted = mute

    @override
    async def async_select_source(self, source: str) -> None:
        """Select an input by name."""
        number = self._input_by_name.get(source)
        if number is None:
            raise HomeAssistantError(f"Unknown source {source!r}")
        self._hold_for(INPUT_HOLD)
        await self._run(
            "select source",
            lambda: self._hub.client.select_input(self._hub.zone, number),
        )
