"""Config and options flow."""

from __future__ import annotations

from typing import Any, override

import probatio as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import McIntoshConfigEntry
from .const import (
    BAUDRATES,
    CONF_BAUDRATE,
    CONF_INPUT_NAMES,
    CONF_MAX_VOLUME,
    CONF_SERIAL_PORT,
    DEFAULT_BAUDRATE,
    DEFAULT_INPUT_NAMES,
    DEFAULT_MAX_VOLUME,
    DOMAIN,
    MAIN_ZONE,
)
from .hub import Hub


class McIntoshConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the serial port and check that a receiver answers on it."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the one setup step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            port = user_input[CONF_SERIAL_PORT].strip()
            baud = int(user_input[CONF_BAUDRATE])
            await self.async_set_unique_id(port)
            self._abort_if_unique_id_configured()
            hub = Hub(port, baud, MAIN_ZONE)
            try:
                await hub.async_connect()
            except Exception:  # noqa: BLE001 - any failure means we cannot talk to it
                errors["base"] = "cannot_connect"
            else:
                await hub.async_close()
                return self.async_create_entry(
                    title="McIntosh MX119",
                    data={CONF_SERIAL_PORT: port, CONF_BAUDRATE: baud},
                )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SERIAL_PORT,
                    default=(user_input or {}).get(CONF_SERIAL_PORT, ""),
                ): str,
                vol.Required(
                    CONF_BAUDRATE, default=str(DEFAULT_BAUDRATE)
                ): selector.SelectSelector(  # pyright: ignore[reportUnknownMemberType]
                    selector.SelectSelectorConfig(options=[str(b) for b in BAUDRATES])
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    @override
    def async_get_options_flow(
        config_entry: McIntoshConfigEntry,
    ) -> OptionsFlow:
        """Return the options flow."""
        return McIntoshOptionsFlow()


class McIntoshOptionsFlow(OptionsFlow):
    """Edit the volume cap and the input names."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show or save the options."""
        current_names: dict[str, str] = {
            **DEFAULT_INPUT_NAMES,
            **self.config_entry.options.get(CONF_INPUT_NAMES, {}),
        }
        if user_input is not None:
            names = {
                number: user_input[f"input_{number}"].strip()
                or DEFAULT_INPUT_NAMES[number]
                for number in DEFAULT_INPUT_NAMES
            }
            return self.async_create_entry(
                data={
                    CONF_MAX_VOLUME: user_input[CONF_MAX_VOLUME],
                    CONF_INPUT_NAMES: names,
                }
            )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MAX_VOLUME,
                    default=self.config_entry.options.get(
                        CONF_MAX_VOLUME, DEFAULT_MAX_VOLUME
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                **{
                    vol.Required(f"input_{number}", default=name): str
                    for number, name in current_names.items()
                },
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
