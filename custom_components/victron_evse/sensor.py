"""Sensor platform for Victron EVSE."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VictronEvseCoordinator
from .device import VictronEvseClient

STATUS_LABELS = {
    0: "Disconnected",
    1: "Connected",
    2: "Charging",
    3: "Charged",
    4: "Waiting for sun",
    5: "Waiting for RFID",
    6: "Waiting for start",
    7: "Low SOC",
    8: "Ground test error",
    9: "Welded contacts test error",
    10: "CP input test error",
    11: "Residual current detected",
    12: "Undervoltage detected",
    13: "Overvoltage detected",
    14: "Overheating detected",
    20: "Charging limit",
    21: "Start charging",
    22: "Switching to 3 phase",
    23: "Switching to 1 phase",
    24: "Stop charging",
}

MODE_LABELS = {0: "Manual", 1: "Auto", 2: "Scheduled"}


@dataclass(frozen=True, kw_only=True)
class VictronSensorDescription(SensorEntityDescription):
    """Entity description with custom value getter."""

    value_fn: Callable[[VictronEvseClient], Any]


SENSOR_DESCRIPTIONS: tuple[VictronSensorDescription, ...] = (
    VictronSensorDescription(
        key="status",
        name="Charger Status",
        device_class=SensorDeviceClass.ENUM,
        options=list(STATUS_LABELS.values()),
        value_fn=lambda c: STATUS_LABELS.get(
            int(c.telemetry.status), f"Reserved ({c.telemetry.status})"
        ),
    ),
    VictronSensorDescription(
        key="charge_mode",
        name="Charge Mode",
        device_class=SensorDeviceClass.ENUM,
        options=list(MODE_LABELS.values()),
        value_fn=lambda c: MODE_LABELS.get(int(c.telemetry.charge_mode), "Unknown"),
    ),
    VictronSensorDescription(
        key="total_power",
        name="Total Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.telemetry.total_power,
    ),
    VictronSensorDescription(
        key="l1_power",
        name="L1 Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.telemetry.l1_power,
    ),
    VictronSensorDescription(
        key="actual_charging_current",
        name="Actual Charging Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.telemetry.actual_charging_current,
    ),
    VictronSensorDescription(
        key="session_time",
        name="Session Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda c: c.telemetry.session_time,
    ),
    VictronSensorDescription(
        key="session_energy",
        name="Session Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.telemetry.session_energy,
    ),
    VictronSensorDescription(
        key="total_energy",
        name="Total Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.telemetry.total_energy,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VictronEvseCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VictronSensor(coordinator, desc) for desc in SENSOR_DESCRIPTIONS
    )


class VictronSensor(CoordinatorEntity[VictronEvseCoordinator], SensorEntity):
    """Coordinator-backed sensor entity for Victron EVSE."""

    entity_description: VictronSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VictronEvseCoordinator,
        description: VictronSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        serial = coordinator.client.device_info.serial_id or coordinator.entry.entry_id
        self._attr_unique_id = f"{serial}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.client)