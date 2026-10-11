# MostlyLevel

MostlyLevel is a campervan levelling system prototype. The MicroPython app draws a pitch-and-roll virtual horizon on an ILI9341 display using notifications from a WT901BLE67-like sensor. The BLE decoder also provides yaw, but the display does not use it.

## Current status

- `src/main.py` draws a virtual horizon with pitch/roll readouts, a pitch ladder, and a fixed camper marker.
- The display uses decoded pitch and roll from the WT901 BLE client and redraws when new values arrive. Yaw is not displayed.
- No hardware validation results are documented in this repository. Display operation, BLE connection/notification setup, protocol assumptions, physical board variant, and installed firmware remain unverified.

## Repository layout

- `src/main.py` — dashboard and render loop.
- `src/ili9341.py` — direct SPI display driver.
- `src/graphics.py` — drawing helpers and bitmap font.
- `src/ble_read.py` — BLE client and packet decoder used by the dashboard; it can also run as a serial diagnostic.
- `src/ble_scan.py` — standalone BLE discovery diagnostic; not used by the application.
- `firmware/` — ESP32_GENERIC_S3 MicroPython firmware image.
- `reference/esp32_s3_es3c28p/` — separate ESP-IDF board support reference; it is not integrated with the MicroPython application.

## Setup and running

The repository does not include a dependency manifest or hardware test procedure. The firmware image's presence does not establish that it is installed on a device. Confirm the target board, MicroPython version, and wiring before running the application.

The application entry point is `src/main.py`. It starts the BLE client in `src/ble_read.py`; `src/ble_scan.py` is an optional standalone diagnostic. The configured address, CCCD handle, UUID, and packet format assumptions have not been validated in checked-in hardware test records.

### Uploading and running on an ESP32

These instructions deploy the MicroPython application files to the board's filesystem. They assume the ESP32 already has a compatible MicroPython firmware installed; the firmware image in this repository has not been verified on a physical board.

From the repository root, install `mpremote` in the project's virtual environment if needed:

```bash
.venv/bin/python -m pip install mpremote
```

Connect the ESP32 over USB and check that it is detected:

```bash
.venv/bin/mpremote connect list
```

Copy the application and its imported modules to the board's filesystem root:

```bash
.venv/bin/mpremote connect auto fs cp src/main.py :main.py
.venv/bin/mpremote connect auto fs cp src/ili9341.py :ili9341.py
.venv/bin/mpremote connect auto fs cp src/graphics.py :graphics.py
.venv/bin/mpremote connect auto fs cp src/ble_read.py :ble_read.py
```

The files belong in the root because `main.py` imports the modules by name. `ble_scan.py` is a separate discovery diagnostic and is not needed to run the dashboard.

After copying, power-cycle the board. MicroPython runs the board's `main.py` at startup. To open the serial REPL and inspect output or errors, run:

```bash
.venv/bin/mpremote connect auto repl
```

If automatic connection does not find the board, use the serial port shown by `connect list` in place of `auto`. These deployment steps have not been tested against the project's physical ESP32/display/sensor setup.

## Documentation

- [Project context](PROJECT_CONTEXT.md) — current project snapshot and status vocabulary.
- [Architecture](docs/architecture.md) — display and BLE code paths and reference BSP boundary.
- [Hardware](docs/hardware.md) — source-configured pin map and unresolved hardware details.
- [Decisions and open questions](docs/decisions.md) — implementation choices, assumptions, and questions to resolve.
- [Changelog](CHANGELOG.md) — notable changes.

See [AGENTS.md](AGENTS.md) for guidance intended for future development sessions.
