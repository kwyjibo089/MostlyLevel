# MostlyLevel project context

## Purpose and current shape

MostlyLevel is a campervan levelling display prototype. The active application is a small MicroPython program under `src/`; it draws a pitch-and-roll virtual horizon on an ILI9341 display and consumes decoded readings from the WT901 BLE client in `ble_read.py`. The decoder also returns yaw, which the display currently ignores.

The repository also contains an ESP-IDF board support package under `reference/esp32_s3_es3c28p/`. Treat it as reference material, not as the active application build. A MicroPython ESP32_GENERIC_S3 firmware image is present under `firmware/`; its presence does not document how it was flashed or which device currently runs it.

## Status vocabulary

- **Implemented (source):** behavior present in the checked-in code.
- **Tested:** behavior supported by a recorded test result. No hardware test log or test procedure is present in this repository snapshot.
- **Planned:** intended future work, not implemented.
- **Unverified:** assumptions or behavior not established by repository evidence or a recorded hardware test.

## Current status

- **Implemented (source):** MicroPython ILI9341 SPI driver and graphics primitives; virtual horizon with pitch/roll readouts, pitch ladder, and camper marker; BLE client, notification setup attempt, and fixed-format packet decoder. `main.py` swaps decoded X/roll and Y/pitch for displayed vehicle axes based on the owner's reported sensor movement; signs remain to be checked. `ble_scan.py` remains a standalone discovery diagnostic.
- **Tested:** No tests or hardware validation results are documented for the dashboard integration.
- **Planned:** confirm the sensor protocol and notification descriptor handling; verify the empirically swapped vehicle axis mapping, signs, and display scaling against the installed sensor.
- **Unverified:** exact physical board variant, deployed firmware, dashboard rendering on the current device, BLE GATT details, sensor packet assumptions/scales, and physical angle conventions.

## Important constraints

Do not claim hardware operation has been verified. Do not treat features in the reference BSP (touch, LVGL, audio, storage, etc.) as application features. Consult `docs/architecture.md`, `docs/hardware.md`, and `docs/decisions.md` before making assumptions.
