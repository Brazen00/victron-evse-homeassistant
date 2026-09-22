"""Config flow for Victron EVSE."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.const import CONF_HOST, CONF_PORT
import homeassistant.helpers.config_validation as cv
from modbus_connection import ModbusTcpParams

from .const import CONF_UNIT_ID, DEFAULT_PORT, DEFAULT_UNIT_ID, DOMAIN
from .device import VictronEvseClient

_LOGGER = logging.getLogger(__name__)


class VictronEvseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Victron EVSE."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            unit_id = user_input[CONF_UNIT_ID]

            params = ModbusTcpParams(host=host, port=port)

            try:
                async with async_get_temporary_unit(self.hass, params, unit_id) as unit:
                    client = VictronEvseClient(unit)
                    await client.async_init()
                    serial = client.device_info.serial_id or f"{host}:{unit_id}"

                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Victron EVCS ({client.device_info.model_name})",
                    data=user_input,
                )
            except Exception as err:
                _LOGGER.exception("Failed to connect to Victron EVCS at %s:%s - %s", host, port, err)
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): cv.positive_int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)