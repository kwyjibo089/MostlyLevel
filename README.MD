# MostlyLevel

MostlyLevel is a campervan levelling system prototype. The repository currently contains a MicroPython display demo and separate BLE tools for exploring and reading a WT901BLE67-like sensor.

## Current status

- The display app draws a static artificial-horizon-style screen using hard-coded demo pitch and roll values.
- The BLE reader attempts to decode sensor notifications and prints measurements to the serial console.
- Sensor readings are not connected to the display app.
- No hardware validation results are documented in this repository. Display operation, BLE protocol assumptions, physical board variant, and installed firmware remain unverified.

## Repository layout

- `src/main.py` — demo screen and render flow.
- `src/ili9341.py` — direct SPI display driver.
- `src/graphics.py` — drawing helpers and bitmap font.
- `src/ble_scan.py` — BLE service and characteristic discovery utility.
- `src/ble_read.py` — BLE notification reader and packet decoder.
- `firmware/` — ESP32_GENERIC_S3 MicroPython firmware image.
- `reference/esp32_s3_es3c28p/` — separate ESP-IDF board support reference; it is not integrated with the MicroPython application.

## Setup and running

The repository does not yet include a documented firmware flashing or source deployment procedure, dependency manifest, or hardware test procedure. The firmware image's presence does not establish that it is installed on a device. Confirm the target board, MicroPython version, and wiring before running the application.

The apparent application entry point is `src/main.py`. The BLE scripts are standalone utilities and should be run separately on a MicroPython runtime with BLE support. Their address, GATT handle, UUID, and packet format assumptions have not been validated in checked-in test records.

## Documentation

- [Project context](PROJECT_CONTEXT.md) — current project snapshot and status vocabulary.
- [Architecture](docs/architecture.md) — display and BLE code paths and reference BSP boundary.
- [Hardware](docs/hardware.md) — source-configured pin map and unresolved hardware details.
- [Decisions and open questions](docs/decisions.md) — implementation choices, assumptions, and questions to resolve.
- [Changelog](CHANGELOG.md) — notable changes.

See [AGENTS.md](AGENTS.md) for guidance intended for future development sessions.
