# Decisions, assumptions, and open questions

This document records choices visible in the current implementation separately from confirmed project decisions. The repository contains no decision log predating this document.

## Current implementation choices

| Choice | Evidence/status |
| --- | --- |
| Use MicroPython for the active app | Source imports `machine`, `bluetooth`, and MicroPython timing APIs; firmware artifact is ESP32_GENERIC_S3. Deployment and installed runtime are unverified. |
| Drive an ILI9341 over SPI with direct writes | Implemented in `src/ili9341.py`; runtime operation is unverified. |
| Use a 240 × 320 drawing coordinate space and RGB565 colors | Implemented in driver and graphics app. The reference BSP has a conflicting 320 × 240 prose comment, while its constants are 240 × 320. |
| Use an artificial-horizon-style screen for the demo | Implemented in `src/main.py`; values are fixed demo inputs, not sensor data. |
| Explore/read the sensor over BLE using a fixed address and assumed UUIDs | Implemented in separate scripts; assumptions require confirmation from live discovery/captures. |
| Keep the ESP-IDF BSP as reference material | Structural fact: it is nested under `reference/` and is not part of the MicroPython import path or a top-level build. Treating it as non-active is a documentation convention, not proof of long-term intent. |

## Status distinctions

- **Implemented:** source-level functionality described above.
- **Tested:** no test or hardware validation evidence is present in the repository snapshot.
- **Planned:** no formal approved roadmap is present. Connecting live sensor readings to the display appears to be the intended next capability, but must be treated as proposed until confirmed.
- **Unverified:** physical hardware identity/wiring, deployed firmware, actual BLE behavior and protocol, conversions, and vehicle coordinate conventions.

## Open questions

1. Is the physical board specifically an ES3C28P, and is the active software expected to remain MicroPython or migrate to the ESP-IDF BSP?
2. What exact WT901 model/configuration is used? Are its BLE address and GATT UUIDs stable, and what descriptor enables notifications? The current reader writes to handle 16 without discovery.
3. Does the sensor emit complete 20-byte `55 61` notifications as assumed? What checksum/framing and scaling rules apply?
4. What sensor-to-vehicle axis mapping, sign convention, zeroing procedure, and displayed angle limits are desired?
5. Should the app reconnect automatically and how should it show stale/missing sensor data?
6. What hardware test procedure and acceptance criteria define a working display and accurate levelling readout?

No unresolved question should be filled in by guessing; capture hardware observations or obtain project-owner direction and record the result here or in `hardware.md`.
