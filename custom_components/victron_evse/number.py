"""Number platform for Victron EVSE current limit."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
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
    async_add_entities([VictronEvseCurrentLimit(coordinator)])


class VictronEvseCurrentLimit(CoordinatorEntity[VictronEvseCoordinator], NumberEntity):
    """Native number control writing directly to holding register 5016."""

    _attr_has_entity_name = True
    _attr_translation_key = "current_limit"
    _attr_name = "Charging Current Limit"
    _attr_native_min_value = 6
    _attr_native_max_value = 32
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:current-ac"

    def __init__(self, coordinator: VictronEvseCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        serial = coordinator.client.device_info.serial_id or coordinator.entry.entry_id
        self._attr_unique_id = f"{serial}_current_limit"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.client.telemetry.charging_current_limit

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.async_set_current_limit(int(value))
        await self.coordinator.async_request_refresh()