# Victron EV Charging Station (Home Assistant Integration)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Brazen00&repository=victron-evse-homeassistant&category=Integration)

Native Home Assistant integration for the **Victron Energy EV Charging Station (EVCS, EVCS NS, and EVCS Pro)** communicating directly via Modbus TCP using Home Assistant 2026.9+'s central connection broker.

## Features
- **Zero YAML configuration:** UI-based Config Flow setup.
- **Connection Broker:** Uses Core's `async_get_unit` connection pool to prevent socket and bus contention.
- **Batched Polling:** Collects telemetry registers in a single PDU read.
- **Entities:**
  - Switch: Charging Enable / Disable
  - Number: Dynamic Charging Current Limit (6 A - 32 A)
  - Sensors: Voltage, Power (L1, Total), Energy (Session, Total), Duration, and Status enums

## Installation

### Standard Installation (Recommended)
1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Go to **HACS** > **Integrations**.
3. Search for `Victron EV Charging Station`.
4. Click **Download**, then restart Home Assistant.

### Manual / Custom Repository (Fallback)
If it does not appear in search yet:
1. Open **HACS** > **Integrations** > Three dots (top right) > **Custom repositories**.
2. Add `https://github.com/Brazen00/victron-evse-homeassistant` with category `Integration`.
3. Click **Download** and restart Home Assistant.

## Setup
1. Enable **Modbus TCP** in your Victron EVCS web UI.
2. In Home Assistant: **Settings** -> **Devices & Services** -> **Add Integration**.
3. Search for **Victron EV Charging Station**.
4. Enter Host IP, Port (`502`), and Unit ID (`1`).
