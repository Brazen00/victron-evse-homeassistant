"""Typed device model for Victron EVCS using modbus-connection."""
from __future__ import annotations

from enum import IntEnum
from modbus_connection import ModbusUnit
from modbus_connection.model import (
    Component,
    enum,
    gauge,
    integer,
    string,
    uint32,
)


class EvseChargeMode(IntEnum):
    MANUAL = 0
    AUTO = 1
    SCHEDULED = 2


class EvseStatus(IntEnum):
    DISCONNECTED = 0
    CONNECTED = 1
    CHARGING = 2
    CHARGED = 3
    WAITING_FOR_SUN = 4
    WAITING_FOR_RFID = 5
    WAITING_FOR_START = 6
    LOW_SOC = 7
    GROUND_TEST_ERROR = 8
    WELDED_CONTACTS_TEST_ERROR = 9
    CP_INPUT_TEST_ERROR = 10
    RESIDUAL_CURRENT_DETECTED = 11
    UNDERVOLTAGE_DETECTED = 12
    OVERVOLTAGE_DETECTED = 13
    OVERHEATING_DETECTED = 14
    CHARGING_LIMIT = 20
    START_CHARGING = 21
    SWITCHING_TO_3_PHASE = 22
    SWITCHING_TO_1_PHASE = 23
    STOP_CHARGING = 24


class VictronDeviceInfo(Component):
    """Static device identity block (5000..5008)."""

    product_id: int = integer(5000, signed=False)
    serial_id: str = string(5001, 6)
    fw_version_h: int = integer(5007, signed=False)
    fw_version_l: int = integer(5008, signed=False)

    @property
    def firmware_version(self) -> str:
        if self.fw_version_h is None or self.fw_version_l is None:
            return "Unknown"
        major = self.fw_version_h & 0xFF
        # Minor is encoded in hex (e.g. 0x30 -> 30)
        minor_raw = (self.fw_version_l >> 8) & 0xFF
        rev = self.fw_version_l & 0xFF

        minor = f"{minor_raw:02x}" if minor_raw < 100 else f"{minor_raw}"

        if rev in (0xFF, 0x00, 255):
            return f"v{major}.{minor}"
        return f"v{major}.{minor}.{rev}"

    @property
    def model_name(self) -> str:
        models = {
            0xC024: "EV Charging Station",
            0xC025: "EV Charging Station NS",
            0xC026: "EV Charging Station Pro",
        }
        return models.get(self.product_id, "EV Charging Station NS")


class VictronTelemetry(Component):
    """Real-time operational telemetry (5009..5024)."""

    charge_mode: EvseChargeMode = enum(5009, EvseChargeMode)
    charging_active: int = integer(5010, signed=False, writable=True)

    l1_power: int = integer(5011, signed=False)
    l2_power: int = integer(5012, signed=False)
    l3_power: int = integer(5013, signed=False)
    total_power: int = integer(5014, signed=False)

    status: EvseStatus = enum(5015, EvseStatus)
    charging_current_limit: int = integer(5016, signed=False, writable=True)
    max_hardware_current: int = integer(5017, signed=False)

    actual_charging_current: float = gauge(5018, 0.1, signed=False, unit="A")
    session_time: int = uint32(5019, unit="s")
    session_energy: float = gauge(5021, 0.01, signed=False, unit="kWh")
    session_cost: float = gauge(5022, 0.01, signed=False)
    total_energy: float = uint32(5023, scale=0.01, unit="kWh")


class VictronEvseClient:
    """Manages unit access and operations."""

    def __init__(self, unit: ModbusUnit) -> None:
        self.unit = unit
        self.device_info = VictronDeviceInfo(unit)
        self.telemetry = VictronTelemetry(unit)

    async def async_init(self) -> None:
        await self.device_info.async_update()

    async def async_update(self) -> None:
        await self.telemetry.async_update()

    async def async_set_charging(self, enabled: bool) -> None:
        await self.unit.write_register(5010, 1 if enabled else 0)

    async def async_set_current_limit(self, current: int) -> None:
        clamped = max(6, min(32, int(current)))
        await self.unit.write_register(5016, clamped)