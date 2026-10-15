# MostlyLevel project context

## Purpose and current shape

MostlyLevel is a campervan levelling display prototype. The active application is a small MicroPython program under `src/`; it draws a pitch-and-roll virtual horizon on an ILI9341 display and consumes decoded readings from the WT901 BLE client in `ble_read.py`. The decoder also returns yaw, which the display currently ignores.

The repository also contains an ESP-IDF board support package under `reference/esp32_s3_es3c28p/`. Treat it as reference material, not as the active application build. A MicroPython ESP32_GENERIC_S3 firmware image is present under `firmware/`. On 2026-10-15 the connected board reported MicroPython 1.29.0, build `ESP32_GENERIC_S3`, the same version as that image; how it was flashed is not recorded.

## Status vocabulary

- **Implemented (source):** behavior present in the checked-in code.
- **Tested:** behavior supported by a recorded test result. No hardware test log or test procedure is present in this repository snapshot.
- **Planned:** intended future work, not implemented.
- **Unverified:** assumptions or behavior not established by repository evidence or a recorded hardware test.

## Current status

- **Implemented (source):** MicroPython ILI9341 SPI driver and graphics primitives; two touch-selectable pages (HORIZON virtual horizon and a LEVELLING page with two-wedge and four-corner views); persistent level-reference calibration, stale-data warning, and a hysteretic green HORIZON frame; grouped display drawing intended to reduce flicker; `src/config.py` centralizes sensor, vehicle, display, touch, and timing settings; FT5x06-compatible I2C touch reader based on reference BSP wiring; BLE client, battery percentage poll, notification setup attempt, and fixed-format packet decoder. `main.py` swaps decoded X/roll and Y/pitch for displayed vehicle axes based on the owner's reported sensor movement; corner-height signs still need validation with the planned centered installation. `ble_scan.py` remains a standalone discovery diagnostic.
- **Tested:** Automated desktop tests (`tools/test.sh`, run in CI) cover decoding, the BLE client handshake, levelling maths, axis mapping, calibration, touch targets, the display driver, compositing, and reference images, all against fake hardware. Owner observations from the device are recorded in `docs/hardware.md`. No automated test runs on the board.
- **Planned:** confirm the sensor protocol and notification descriptor handling; verify the empirically swapped vehicle axis mapping, signs, and display scaling against the installed sensor.
- **Unverified:** exact physical board variant, touchscreen controller/pin mapping and coordinate orientation, dashboard rendering and redraw speed on the current device, calibration persistence/accuracy, BLE GATT details, sensor packet assumptions/scales, and physical angle conventions.

## Important constraints

Do not claim touchscreen hardware operation has been verified. Touch code is now present in the MicroPython application, using controller and pin details drawn from the reference BSP; test the active wiring before treating it as confirmed. Do not treat other features in the reference BSP (LVGL, audio, storage, etc.) as application features. Consult `docs/architecture.md`, `docs/hardware.md`, and `docs/decisions.md` before making assumptions.
