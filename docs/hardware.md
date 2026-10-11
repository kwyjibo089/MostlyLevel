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

The firmware directory contains `ESP32_GENERIC_S3-20260824-v1.29.0.bin`. This is evidence of a firmware artifact in the repository only; the installed firmware is unknown.

## Sensor interface in source

`ble_scan.py` and `ble_read.py` target BLE address `F0:A0:7A:DB:7D:45`. `ble_read.py` assumes notify UUID `0000ffe4-0000-1000-8000-00805f9a34fb`, write UUID `0000ffe9-0000-1000-8000-00805f9a34fb`, and CCCD handle 16. The code names the sensor WT901BLE67; the scanner also prints WT901BLECL. These labels and protocol details have not been reconciled with a recorded device discovery or capture.

## Tested versus unverified

No wiring inspection, board identification record, sensor discovery transcript, packet capture, or hardware test result is checked in. Therefore the pin map is **implemented/configured in source**, not independently confirmed against the physical build. Sensor GATT handles, packet structure, scaling, orientation, and sensor mounting are **unverified**. Do not infer power supply, connector, mounting, or other wiring details from the current files.

## Questions to resolve

- What exact board model and variant is physically used, and is its wiring consistent with the source mapping?
- What firmware version is installed on the target, and how are files deployed/run?
- What are the sensor's actual BLE address behavior, service/characteristic/descriptor handles, and notification format? Is the address stable?
- Does the sensor packet require checksum validation, and are the implemented field order and scale ranges correct for its configuration?
- Which sensor axes/signs correspond to vehicle pitch and roll after mounting, and how will zero/calibration be defined?
