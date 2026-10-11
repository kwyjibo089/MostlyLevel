# Software architecture

## Active application

The active code is MicroPython in `src/`. `main.py` imports `ILI9341` from `ili9341.py` and `Graphics` plus RGB565 colors from `graphics.py`.

### Display path

1. `main.py` creates `ILI9341`, enables its backlight, then creates a `Graphics` wrapper.
2. `ili9341.py` configures SPI bus 2 at 20 MHz with SCK GPIO 12, MOSI 11, MISO 13; CS is GPIO 10, DC GPIO 46, and backlight GPIO 45.
3. The driver sends an ILI9341 initialization sequence, configures RGB565, and writes pixels using address windows and small repeated-color chunks rather than a full-screen framebuffer.
4. `graphics.py` supplies pixel/line/rectangle operations and a small bitmap font.
5. `main.py` starts the BLE client and draws link status, pitch/roll readouts, a moving sky/ground virtual horizon and pitch ladder, and a fixed camper marker. There is no compass in the display.

The main loop polls the latest decoded sample and redraws on new samples, with a 250 ms minimum interval. BLE callbacks update sensor state only; they do not draw to the display. The dashboard shows a stale/no-data state if a sample has not arrived for 1.5 seconds. The original phone status bar, tabs, buttons, and photographic van are not recreated; the display uses simple graphics.

**Implemented (source):** live-data dashboard flow. **Unverified:** successful runtime operation, visual fidelity/performance, sensor-to-vehicle sign convention, and real-time usability on hardware; no validation record is checked in.

## BLE tools and sensor data path

- `ble_read.py` exposes `WT901BLEClient`, which scans/connects to the fixed address, discovers characteristics, looks for UUID `FFE4` (notify), attempts to enable notifications by writing `01 00` to hard-coded handle 16, and decodes matching notifications as 20-byte `55 61` packets. It keeps the latest values for the app and can also run standalone as a console diagnostic.
- `main.py` maps the decoded X/roll channel to displayed vehicle pitch and the decoded Y/pitch channel to displayed vehicle roll, based on the owner's reported movement response. The client still decodes yaw, but the display ignores it. `ble_scan.py` remains a separate discovery diagnostic and is not used by the app. The mapping's signs and physical validity remain to be confirmed.

The decoder checks length and the first two bytes but has no checksum validation or stream reassembly. Field ordering, conversion ranges, characteristic UUIDs, CCCD handle, and address remain source-level assumptions pending sensor-side validation. The client retries scanning after scan timeout and reconnects by scanning after disconnection; other BLE errors do not have a full recovery strategy.

## Reference implementation boundary

`reference/esp32_s3_es3c28p/` is a separate ESP-IDF BSP with C source, component metadata, and headers for display, touch, LVGL, audio, and storage. No top-level ESP-IDF project configuration or integration with `src/` is present. Its documentation and code can inform investigation but do not establish active application behavior or the exact physical hardware.

## Configuration and verification gaps

There is no top-level dependency manifest, deployment script, build configuration, or documented test procedure. The firmware filename identifies an ESP32_GENERIC_S3 MicroPython image, but does not establish the currently deployed firmware or process used to install it. See `hardware.md` for physical questions and `decisions.md` for current choices and unresolved items.
