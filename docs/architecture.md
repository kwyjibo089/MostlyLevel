# Software architecture

## Active application

The active code is MicroPython in `src/`. `main.py` imports `ILI9341` from `ili9341.py` and `Graphics` plus RGB565 colors from `graphics.py`.

### Display path

1. `main.py` creates `ILI9341`, enables its backlight, then creates a `Graphics` wrapper.
2. `ili9341.py` configures SPI bus 2 at 20 MHz with SCK GPIO 12, MOSI 11, MISO 13; CS is GPIO 10, DC GPIO 46, and backlight GPIO 45.
3. The driver sends an ILI9341 initialization sequence, configures RGB565, and writes pixels using address windows and small repeated-color chunks rather than a full-screen framebuffer.
4. `graphics.py` supplies pixel/line/rectangle operations and a small bitmap font.
5. `main.py` starts the BLE client and draws link status, pitch/roll readouts, a moving sky/ground virtual horizon and pitch ladder, and a fixed camper marker. There is no compass in the display.

`main.py` provides `save_screenshot(path)`, which redraws the current page and last rendered values into an 8-row RGB565 tile buffer and streams a 24-bit BMP to the ESP32 filesystem. It avoids a full-screen allocation and does not read from display GRAM. Interrupt the app in the REPL and call `save_screenshot("/screenshot.bmp")`, then copy the file with `mpremote fs cp :screenshot.bmp ./screenshot.bmp`.

The main loop polls the latest decoded sample and FT5x06 touch input. The `HORIZON` and `LEVELLING` controls switch pages. On HORIZON, a separate rounded yellow `CALIBRATE` button in the upper-right above the arc captures live pitch/roll offsets, saved in `/level_reference.cfg` on the ESP32 filesystem and loaded on startup. The levelling page has `2 WEDGES` and `4 CORNERS` touch tabs; the first ranks corner lift estimates and shows the two largest, while the second shows all four. Heights use the configured wheelbase and front/rear track widths relative to the highest corner. The formula assumes positive pitch is front-high, positive roll is left-high, and the sensor is at the footprint center. On HORIZON, a green outline turns on when live pitch and roll are both within ±0.5° and remains on until either exceeds ±0.7°; both thresholds are configurable. Stale, disconnected, or not-yet-available sensor data triggers a red frame and an in-screen warning. The app draws the full page on startup or page changes, redraws the status header when connection or battery status changes, and redraws attitude graphics when either value differs by at least 0.2° or the level state changes (with a 250 ms minimum interval). Drawing code groups matching horizon and ladder runs and batches LCD address commands to reduce small display writes. Live HORIZON redraws clip all drawing around the CALIBRATE button, the readout boxes, and the green frame while it is shown; readouts repaint only changed characters. The LEVELLING page draws its layout on page/view changes and afterwards repaints only cells whose displayed text changed. The driver reuses per-colour fill buffers and a window-coordinate buffer so individual shapes do not allocate memory. BLE callbacks update sensor state only; they do not draw. Data is marked stale if a sample has not arrived for 1.5 seconds. Touch setup uses I2C GPIO 15/16, reset GPIO 18, address 0x38, based on the separate reference BSP and remains to be confirmed on the active hardware.

**Implemented (source):** live-data dashboard flow. **Unverified:** successful runtime operation, visual fidelity/performance, sensor-to-vehicle sign convention, and real-time usability on hardware; no validation record is checked in.

## BLE tools and sensor data path

- `ble_read.py` exposes `WT901BLEClient`, which scans/connects to the configured address, discovers characteristics, looks for UUID `FFE4` (notify), attempts to enable notifications by writing `01 00` to the configured candidate handle 16, and decodes matching notifications as configured 20-byte `55 61` packets. It keeps the latest values for the app and can also run standalone as a console diagnostic.
- `main.py` maps the decoded X/roll channel to displayed vehicle pitch and the decoded Y/pitch channel to displayed vehicle roll, based on the owner's reported movement response. The client still decodes yaw, but the display ignores it. `ble_scan.py` remains a separate discovery diagnostic and is not used by the app. The mapping's signs and physical validity remain to be confirmed.

The decoder checks length and the first two bytes but has no checksum validation or stream reassembly. Field ordering, conversion ranges, configured characteristic UUIDs, CCCD handle, and address remain assumptions pending sensor-side validation. The client retries scanning after scan timeout and reconnects by scanning after disconnection; other BLE errors do not have a full recovery strategy.

## Reference implementation boundary

`reference/esp32_s3_es3c28p/` is a separate ESP-IDF BSP with C source, component metadata, and headers for display, touch, LVGL, audio, and storage. No top-level ESP-IDF project configuration or integration with `src/` is present. Its documentation and code can inform investigation but do not establish active application behavior or the exact physical hardware.

## Configuration and verification gaps

`src/config.py` centralizes sensor identity and protocol assumptions, axis mapping, vehicle geometry, display timing, and LCD/touch pin assignments. The sensor packet decoder and display algorithms remain in their respective modules. There is no top-level dependency manifest, deployment script, build configuration, or documented test procedure. The firmware filename identifies an ESP32_GENERIC_S3 MicroPython image, but does not establish the currently deployed firmware or process used to install it. See `hardware.md` for physical questions and `decisions.md` for current choices and unresolved items.
