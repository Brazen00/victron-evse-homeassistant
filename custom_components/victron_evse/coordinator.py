"""DataUpdateCoordinator for Victron EVSE."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.modbus import async_get_unit
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection import ModbusTcpParams

from .const import CONF_UNIT_ID, DEFAULT_SCAN_INTERVAL, DOMAIN
from .device import VictronEvseClient

_LOGGER = logging.getLogger(__name__)


class VictronEvseCoordinator(DataUpdateCoordinator[None]):
    """Manage fetching Victron EVSE data using batched Modbus calls."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Victron EVSE ({entry.data[CONF_HOST]})",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry

        params = ModbusTcpParams(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
        )

        self.unit = async_get_unit(
            hass,
            entry,
            params,
            entry.data[CONF_UNIT_ID],
        )
        self.client = VictronEvseClient(self.unit)

    async def _async_setup(self) -> None:
        """Fetch static device hardware information once during setup."""
        await self.client.async_init()

    async def _async_update_data(self) -> None:
        """Fetch real-time telemetry block."""
        try:
            await self.client.async_update()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Victron EVSE: {err}") from err

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry info for grouping entities."""
        info = self.client.device_info
        return DeviceInfo(
            identifiers={(DOMAIN, info.serial_id or self.entry.entry_id)},
            name=f"Victron EVCS ({info.serial_id})",
            manufacturer="Victron Energy",
            model=info.model_name,
            sw_version=info.firmware_version,
        )