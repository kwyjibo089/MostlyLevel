# Software architecture

## Active application

The active code is MicroPython in `src/`. `main.py` imports `ILI9341` from `ili9341.py` and `Graphics` plus RGB565 colors from `graphics.py`.

### Display path

1. `main.py` creates `ILI9341`, enables its backlight, then creates a `Graphics` wrapper.
2. `ili9341.py` configures SPI bus 2 at 20 MHz with SCK GPIO 12, MOSI 11, MISO 13; CS is GPIO 10, DC GPIO 46, and backlight GPIO 45.
3. The driver sends an ILI9341 initialization sequence, configures RGB565, and writes pixels using address windows and small repeated-color chunks rather than a full-screen framebuffer.
4. `graphics.py` supplies pixel/line/rectangle operations and a small bitmap font.
5. `main.py` draws header, horizon, markings, a stationary van graphic, angle readouts, and footer. It calls `draw_screen` once with hard-coded `pitch = 4.0` and `roll = -6.0`.

**Implemented (source):** one-time demo rendering and low-level drawing functions. **Unverified:** successful operation on the current hardware; no display test record is checked in. There is no continuous render loop or sensor-fed display update.

## BLE tools and sensor data path

- `ble_scan.py` scans for the fixed address `F0:A0:7A:DB:7D:45`, connects, discovers services/characteristics, and prints discovery results. It is exploratory tooling.
- `ble_read.py` separately scans/connects to that address, discovers characteristics, looks for UUIDs `FFE4` (notify) and `FFE9` (write), writes `01 00` to hard-coded handle 16 as a notification-enable attempt, and decodes matching notifications as 20-byte `55 61` packets. It prints values to the console.
- `main.py` does not import either BLE script. There is no implemented sensor-to-screen data path.

The decoder checks length and the first two bytes but has no checksum validation or stream reassembly. Field ordering, conversion ranges, characteristic UUIDs, CCCD handle, and address are source-level assumptions pending sensor-side validation. BLE reconnect/rescan behavior is not implemented.

## Reference implementation boundary

`reference/esp32_s3_es3c28p/` is a separate ESP-IDF BSP with C source, component metadata, and headers for display, touch, LVGL, audio, and storage. No top-level ESP-IDF project configuration or integration with `src/` is present. Its documentation and code can inform investigation but do not establish active application behavior or the exact physical hardware.

## Configuration and verification gaps

There is no top-level dependency manifest, deployment script, build configuration, or documented test procedure. The firmware filename identifies an ESP32_GENERIC_S3 MicroPython image, but does not establish the currently deployed firmware or process used to install it. See `hardware.md` for physical questions and `decisions.md` for current choices and unresolved items.
