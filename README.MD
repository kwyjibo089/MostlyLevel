# MostlyLevel

MostlyLevel is a campervan levelling system prototype. The MicroPython app draws a pitch-and-roll virtual horizon on an ILI9341 display using notifications from a WT901BLE67-like sensor. The BLE decoder also provides yaw, but the display does not use it.

## Screenshots

### HORIZON

![HORIZON screen with the virtual horizon and pitch and roll readouts](assets/screenshot1.png)

The main screen shows the live virtual horizon, vehicle attitude, and sensor connection and battery status.

![HORIZON screen with a green frame when the camper is level](assets/screenshot.png)

The green frame appears when both pitch and roll are within ±0.5°.

### LEVELLING — 4 CORNERS

![LEVELLING screen showing estimated lift heights for all four corners](assets/screenshot2.png)

This view shows the estimated lift height at each wheel corner.

### LEVELLING — 2 WEDGES

![LEVELLING screen showing the two corners with the largest lift estimates](assets/screenshot3.png)

This view ranks the two corners with the largest estimated lift amounts for a two-wedge setup.

## Current status

- `src/main.py` provides two touch-selectable pages: **HORIZON** for the virtual horizon dashboard and **LEVELLING** for the corner lift estimates. The levelling page has **2 WEDGES** and **4 CORNERS** views; the two-wedge view is selected by default. The top bar shows the latest sensor battery percentage beside the BLE status.
- The display uses decoded pitch and roll from the WT901 BLE client and redraws the readouts and horizon when either changes by at least 0.2°. The status header redraws at startup or when connection or battery status changes. Yaw is not displayed.
- On the HORIZON page, a green frame turns on when live pitch and roll are both within ±0.5° and stays on until either exceeds ±0.7°. These thresholds are configurable in `src/config.py`; the behavior has not yet been verified on hardware.
- If the sensor is stale or disconnected, the app displays a prominent warning and red frame instead of leaving a green level indication.
- Dashboard operation and BLE connection/notification behavior remain unverified. An initial LCD memory-read screenshot attempt returned all-zero pixels; the replacement software-rendered screenshot path has not yet been tested on hardware. Protocol assumptions, physical board variant, and installed firmware also remain unverified.

The **2 WEDGES** view ranks wheel corners by estimated lift and shows the two largest amounts. The **4 CORNERS** view shows all four estimates. Both use the owner-provided 4,035 mm wheelbase and 1,810/1,790 mm front/rear track widths with live vehicle pitch and roll. The calculation assumes the sensor is mounted level with the chassis at the midpoint of the wheelbase and track, positive pitch means front-high, and positive roll means left-high. These are geometric estimates; after placing wedges, recheck the live readings and adjust as needed. Verify the signs and estimates on the installed van before relying on them.

### Set the level reference

On the **HORIZON** screen, after leveling the van with a trusted reference, tap the rounded yellow **CALIBRATE** button in the upper-right corner above the arc. The app records the current pitch and roll as zero offsets in `/level_reference.cfg` on the ESP32 and uses them after restart. Tap **CALIBRATE** again to replace the reference after changing the sensor mount. The button requires live sensor data. Confirm the result on the physical display before relying on it; this calibration flow has not yet been hardware-verified.

## Repository layout

- `src/main.py` — dashboard and render loop.
- `src/ili9341.py` — direct SPI display driver.
- `src/graphics.py` — drawing helpers and bitmap font.
- `src/screenshot.py` — temporary framebuffer adapter and BMP writer used for screenshots.
- `src/ble_read.py` — BLE client and packet decoder used by the dashboard; it can also run as a serial diagnostic.
- `src/config.py` — editable sensor, vehicle geometry, display, touch, and timing settings.
- `src/touch.py` — minimal FT5x06 I2C touchscreen reader for the reference board wiring.
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
.venv/bin/mpremote connect auto fs cp src/config.py :config.py
.venv/bin/mpremote connect auto fs cp src/main.py :main.py
.venv/bin/mpremote connect auto fs cp src/ili9341.py :ili9341.py
.venv/bin/mpremote connect auto fs cp src/graphics.py :graphics.py
.venv/bin/mpremote connect auto fs cp src/ble_read.py :ble_read.py
.venv/bin/mpremote connect auto fs cp src/touch.py :touch.py
.venv/bin/mpremote connect auto fs cp src/screenshot.py :screenshot.py
```

The files belong in the root because `main.py` imports the modules by name. `ble_scan.py` is a separate discovery diagnostic and is not needed to run the dashboard.

### Configuration

Edit `src/config.py` for the sensor MAC address, GATT UUIDs and notification handle, packet scaling and battery percentage bands, sensor-to-vehicle axis mapping and signs, van geometry, display timing, and LCD/touch pin assignments. The MAC is written as 12 hexadecimal digits without colons. Keep the ESP32's `config.py` in sync when uploading changes. Some values, including the CCCD handle and sensor axis/sign assumptions, remain unverified and should only be changed based on hardware checks.

After copying, power-cycle the board. MicroPython runs the board's `main.py` at startup. To open the serial REPL and inspect output or errors, run:

```bash
.venv/bin/mpremote connect auto repl
```

If automatic connection does not find the board, use the serial port shown by `connect list` in place of `auto`. These deployment steps have not been tested against the project's physical ESP32/display/sensor setup.

### Sensor battery display and diagnostic

The dashboard requests the sensor power register after BLE becomes live and then once per minute. It shows the latest percentage beside the `LIVE` status; until the first reply, the percentage area stays blank. The conversion uses the voltage-to-percentage bands published for a related WT9011DCL-BT50 model. On the connected unit, raw value `385` decoded to `3.85 V`, matching the Android app's 60% reading. The percentage conversion still needs comparison at other battery levels on this exact sensor.

To use the dashboard battery display, upload the updated `main.py` and `ble_read.py` to the board, then restart it. To inspect the reading manually, upload the updated BLE client, connect the dashboard to the sensor, then open the REPL and interrupt the app with Ctrl+C:

```bash
.venv/bin/mpremote connect auto fs cp src/config.py :config.py
.venv/bin/mpremote connect auto fs cp src/ble_read.py :ble_read.py
.venv/bin/mpremote connect auto fs cp src/main.py :main.py
.venv/bin/mpremote connect auto repl
```

At the MicroPython prompt, request the value and check the response:

```python
sensor.request_power_read()
import time
time.sleep_ms(1000)
print(sensor.last_power_response)
print(sensor.power_raw, sensor.power_voltage, sensor.power_percent)
```

The connected unit returned a `55 71` register response, with `power_raw` equal to `385`, `power_voltage` equal to `3.85`, and `power_percent` equal to `60`. If these values remain `None` on another attempt, the expected power-register response was not received during that attempt.

### Capturing a display screenshot

The app can render the last displayed attitude into small temporary RGB565 strips and save it as `/screenshot.bmp` on the ESP32. It renders in 8-row strips to avoid allocating a full-screen buffer. This reproduces the app's last rendered UI state; it does not read pixels back from the LCD controller. Upload `screenshot.py` as shown above before using this feature.

Open the device REPL and interrupt the running application with Ctrl+C. Then call:

```python
save_screenshot("/screenshot.bmp")
```

Exit the REPL and copy the image into the screenshots directory:

```bash
mkdir -p screenshots
.venv/bin/mpremote connect auto fs cp :screenshot.bmp ./screenshots/screenshot1.bmp
```

You can then open `screenshots/screenshot1.bmp` or convert it to PNG for display in Markdown. The device needs enough free RAM for a small strip buffer and enough filesystem space for the BMP.

## Documentation

- [Project context](PROJECT_CONTEXT.md) — current project snapshot and status vocabulary.
- [Architecture](docs/architecture.md) — display and BLE code paths and reference BSP boundary.
- [Hardware](docs/hardware.md) — source-configured pin map and unresolved hardware details.
- [Decisions and open questions](docs/decisions.md) — implementation choices, assumptions, and questions to resolve.
- [Changelog](CHANGELOG.md) — notable changes.

See [AGENTS.md](AGENTS.md) for guidance intended for future development sessions.
