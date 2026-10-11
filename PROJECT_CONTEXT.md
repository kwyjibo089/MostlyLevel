# MostlyLevel project context

## Purpose and current shape

MostlyLevel is a campervan levelling display prototype. The active application is a small MicroPython program under `src/`; it draws a static artificial-horizon demo on an ILI9341 display. Separate BLE scripts explore and read a WT901BLE67-like sensor. The reader currently prints decoded values to the serial console; it is not connected to the display app.

The repository also contains an ESP-IDF board support package under `reference/esp32_s3_es3c28p/`. Treat it as reference material, not as the active application build. A MicroPython ESP32_GENERIC_S3 firmware image is present under `firmware/`; its presence does not document how it was flashed or which device currently runs it.

## Status vocabulary

- **Implemented (source):** behavior present in the checked-in code.
- **Tested:** behavior supported by a recorded test result. No hardware test log or test procedure is present in this repository snapshot.
- **Planned:** intended future work, not implemented.
- **Unverified:** assumptions or behavior not established by repository evidence or a recorded hardware test.

## Current status

- **Implemented (source):** MicroPython ILI9341 SPI driver and graphics primitives; static demo screen; BLE scan/discovery utility; BLE notification reader and fixed-format packet decoder.
- **Tested:** No tests or hardware validation results are documented in the repository.
- **Planned:** Live sensor-to-display integration is the apparent project direction, but no formal roadmap or acceptance criteria existed in the source snapshot.
- **Unverified:** exact physical board variant, deployed firmware, display behavior on the current device, BLE GATT details, sensor packet assumptions/scales, and physical angle conventions.

## Important constraints

Do not claim the demo values come from the sensor. Do not treat features in the reference BSP (touch, LVGL, audio, storage, etc.) as application features. Consult `docs/architecture.md`, `docs/hardware.md`, and `docs/decisions.md` before making assumptions.
