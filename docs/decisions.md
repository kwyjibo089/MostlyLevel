# Decisions, assumptions, and open questions

This document records choices visible in the current implementation separately from confirmed project decisions. The repository contains no decision log predating this document.

## Current implementation choices

| Choice | Evidence/status |
| --- | --- |
| Use MicroPython for the active app | Source imports `machine`, `bluetooth`, and MicroPython timing APIs; firmware artifact is ESP32_GENERIC_S3. Deployment and installed runtime are unverified. |
| Drive an ILI9341 over SPI with direct writes | Implemented in `src/ili9341.py`; runtime operation is unverified. |
| Use a 240 × 320 drawing coordinate space and RGB565 colors | Implemented in driver and graphics app. The reference BSP has a conflicting 320 × 240 prose comment, while its constants are 240 × 320. |
| Display a virtual horizon using pitch and roll; omit the compass | Implemented in `src/main.py`; the BLE decoder still provides yaw but the display does not use it. Physical orientation is unverified. |
| Swap the sensor's decoded X/roll and Y/pitch channels for vehicle display axes | Implemented in `src/main.py` after the owner reported front lift affecting horizon tilt and left lift appearing as positive pitch. This empirical mapping and its signs still need validation. |
| Connect to the sensor over BLE using the configured address and UUIDs | Implemented in `src/ble_read.py`; GATT and packet assumptions still require confirmation from live captures. |
| Keep the ESP-IDF BSP as reference material | Structural fact: it is nested under `reference/` and is not part of the MicroPython import path or a top-level build. Treating it as non-active is a documentation convention, not proof of long-term intent. |

## Dashboard integration update

The display uses a virtual horizon with pitch/roll readouts, a pitch ladder, and a camper marker. It fills the screen area below the status and readout bars; the compass has been removed. `main.py` swaps the client's decoded `roll` and `pitch` values to match the reported installed sensor response; the client continues to decode yaw, but the display ignores it. The mapping signs and operation remain to be checked on hardware.

`ble_scan.py` remains an optional diagnostic utility. The application does not import it; normal startup and scanning are handled by `WT901BLEClient`.

## Status distinctions

- **Implemented:** source-level functionality described above.
- **Tested:** no test or hardware validation evidence is present for the dashboard/sensor integration.
- **Planned:** no formal approved roadmap is present. Confirm BLE notification setup and validate the dashboard's sensor axes/signs on the installed hardware.
- **Unverified:** physical hardware identity/wiring, deployed firmware, actual BLE behavior and protocol, conversions, and vehicle coordinate conventions.

## Open questions

1. Is the physical board specifically an ES3C28P, and is the active software expected to remain MicroPython or migrate to the ESP-IDF BSP?
2. What exact WT901 model/configuration is used? Are its BLE address and GATT UUIDs stable, and what descriptor enables notifications? The current reader writes to handle 16 without discovery.
3. Does the sensor emit complete 20-byte `55 61` notifications as assumed? What checksum/framing and scaling rules apply?
4. Does the swapped virtual-horizon axis mapping produce correct pitch/roll movement and sign in all directions? What zeroing procedure and angle limits are desired?
5. Should the app reconnect automatically and how should it show stale/missing sensor data?
6. What hardware test procedure and acceptance criteria define a working display and accurate levelling readout?

No unresolved question should be filled in by guessing; capture hardware observations or obtain project-owner direction and record the result here or in `hardware.md`.
