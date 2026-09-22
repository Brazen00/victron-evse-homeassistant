"""Switch platform for Victron EVSE."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VictronEvseCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VictronEvseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VictronEvseChargeSwitch(coordinator)])


class VictronEvseChargeSwitch(CoordinatorEntity[VictronEvseCoordinator], SwitchEntity):
    """Switch entity mapped to register 5010 (Start/Stop charging)."""

    _attr_has_entity_name = True
    _attr_translation_key = "charging_switch"
    _attr_name = "Charging"
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator: VictronEvseCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        serial = coordinator.client.device_info.serial_id or coordinator.entry.entry_id
        self._attr_unique_id = f"{serial}_charging_switch"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.client.telemetry.charging_active == 1)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_set_charging(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_set_charging(False)
        await self.coordinator.async_request_refresh()