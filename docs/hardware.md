# Hardware and interfaces

## Evidence in the repository

`src/ili9341.py` labels its wiring as ES3C28P and configures these display connections:

| Display signal | GPIO | Evidence |
| --- | ---: | --- |
| CS | 10 | MicroPython display driver; same mapping in reference BSP |
| DC | 46 | MicroPython display driver; same mapping in reference BSP |
| Backlight | 45 | MicroPython display driver; same mapping in reference BSP |
| SPI SCK | 12 | MicroPython display driver; same mapping in reference BSP |
| SPI MOSI | 11 | MicroPython display driver; same mapping in reference BSP |
| SPI MISO | 13 | MicroPython display driver; same mapping in reference BSP |
| Reset | Shared with MCU reset (not driven by app) | Driver comment and reference BSP definition |

The application uses a 240 × 320 coordinate space and an ILI9341 initialization sequence. The reference BSP README describes an ES3C28P/ES3N28P family board and additional peripherals, but this does not confirm the user's physical board variant or which peripherals are fitted.

`src/config.py` is the editable location for configured sensor identity and protocol assumptions, sensor-to-vehicle axis mapping, owner-provided van geometry, update timing, and board pin assignments. Centralizing a value there does not make that value hardware-verified.

`src/touch.py` implements basic FT5x06-compatible touch reads over I2C address `0x38`, using GPIO 15/16 and reset GPIO 18 as specified by the separate ES3C28P reference BSP. The active application draws `HORIZON` and `LEVELLING` buttons; the levelling page toggles between `2 WEDGES` and `4 CORNERS` views. Controller identity, wiring, touch coordinate orientation, and button operation have not yet been verified on the physical unit.

The owner provided a wheelbase of 4,035 mm, approximate front track width of 1,810 mm, and rear track width of 1,790 mm. The corner-height calculation uses these distances and the live pitch/roll angles, then displays the two corners with the largest estimated lifts for the owner's two-wedge setup. Left and right refer to the vehicle's forward direction. It assumes the sensor is located at the center of the wheel footprint, positive pitch raises the front, and positive roll raises the left side. It models the van floor as a rigid plane and calculates lift amounts relative to the highest corner. These are geometric estimates rather than a guarantee that only those two wheel positions will need adjustment; check the live readings again after placing wedges. Sensor position, angle signs, suspension/tire effects, and the estimates need validation after installation.

An initial ILI9341 GRAM readback screenshot attempt produced an all-zero BMP, and an attempted full-screen software framebuffer allocation failed with `MemoryError`. The owner reported 193,600 bytes free after interrupting the app, but a single contiguous 153,600-byte allocation was still unavailable. The current screenshot implementation renders the dashboard in 8-row RGB565 tiles and streams a BMP to the filesystem; this smaller-allocation approach remains unverified on hardware.

The firmware directory contains `ESP32_GENERIC_S3-20260824-v1.29.0.bin`. This is evidence of a firmware artifact in the repository only; the installed firmware is unknown.

The owner's 3D-printed case covers roughly the top 9 pixel rows of the display (estimated from a photo on 2026-10-15); the sides and bottom were reported as unobstructed. `SCREEN_TOP_INSET` in `src/config.py` moves the top of the UI below that edge.

## Sensor interface in source

`ble_scan.py` and the app's `ble_read.py` client target BLE address `F0:A0:7A:DB:7D:45`. The client listens for notifications on UUID `0000ffe4-0000-1000-8000-00805f9a34fb` and writes commands using the discovered `FFE9` characteristic. The code names the sensor WT901BLE67; the scanner prints WT901BLECL. These labels have not been reconciled against a device label or datasheet.

The owner tested `sensor.request_power_read()` against the connected unit. It returned `55 71 64 00 81 01 ... E8 03`; the diagnostic decoded the power value `0x0181` (385) as 3.85 V. The Android app showed 60% at the same time. The dashboard now polls this register once per minute and shows a percentage in the top bar. Percentage bands are taken from a related WT9011DCL-BT50 protocol table; 385 maps to 60%, matching the one reported app observation. Other battery levels on this exact unit have not been checked.

The HORIZON screen provides a rounded yellow `CALIBRATE` button in the upper-right above the arc that saves pitch/roll offsets to `/level_reference.cfg` on the ESP32. The intended procedure is to level the van using a trusted reference before tapping the button. This file persistence and the calibration result have not yet been checked on the physical device.

## Tested versus unverified

No wiring inspection, board identification record, discovery transcript, or formal hardware test report is checked in; the owner has provided live observations including the power response above. The owner reports that lifting the front changes the displayed horizon tilt, while lifting the left side produces positive displayed pitch. In response, `main.py` currently swaps the decoded X/roll and Y/pitch channels for vehicle display pitch/roll. This is an empirical mapping based on those observations; signs, mounting orientation, and level calibration still need confirmation. Yaw is decoded but not displayed. Do not infer power supply, connector, mounting, or other wiring details from the current files.

## Questions to resolve

- What exact board model and variant is physically used, and is its wiring consistent with the source mapping?
- What firmware version is installed on the target, and how are files deployed/run?
- What are the sensor's actual BLE address behavior, service/characteristic/descriptor handles, and notification format? Is the address stable?
- Does the sensor packet require checksum validation, and are the implemented field order and scale ranges correct for its configuration?
- Does the current swapped mapping produce the correct movement and sign for vehicle pitch and roll across all four directions? How will zero/calibration be defined?
