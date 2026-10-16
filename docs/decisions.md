# Decisions, assumptions, and open questions

This document records choices visible in the current implementation separately from confirmed project decisions. The repository contains no decision log predating this document.

## Current implementation choices

| Choice | Evidence/status |
| --- | --- |
| Use MicroPython for the active app | Source imports `machine`, `bluetooth`, and MicroPython timing APIs; firmware artifact is ESP32_GENERIC_S3. Deployment and installed runtime are unverified. |
| Drive an ILI9341 over SPI with direct writes | Implemented in `src/ili9341.py`; runtime operation is unverified. |
| Use a 240 × 320 drawing coordinate space and RGB565 colors | Implemented in driver and graphics app. The reference BSP has a conflicting 320 × 240 prose comment, while its constants are 240 × 320. |
| Display a virtual horizon using pitch and roll; omit the compass | Implemented in `src/app.py`; the BLE decoder still provides yaw but the display does not use it. Physical orientation is unverified. |
| Swap the sensor's decoded X/roll and Y/pitch channels for vehicle display axes | Implemented in `src/app.py` after the owner reported front lift affecting horizon tilt and left lift appearing as positive pitch. On 2026-10-16 the owner checked the installed sensor: raising the front gives positive displayed pitch, raising the left side gives positive displayed roll, and the LEVELLING page then asks for lift on the correct (lower) wheels. |
| Connect to the sensor over BLE using the configured address and UUIDs | Implemented in `src/ble_read.py`; GATT and packet assumptions still require confirmation from live captures. |
| Read and display sensor battery percentage | `src/app.py` requests register `0x64` every 60 seconds while live and shows the latest percentage beside `LIVE`. Voltage percentage bands come from a related WT9011DCL-BT50 protocol table. On the owner's unit, raw 385 (3.85 V) matched the Android app's 60%; other levels on this exact model remain unverified. |
| Add touch navigation between pages | `src/app.py` draws `HORIZON` and `LEVELLING` buttons; `src/touch.py` reads an FT5x06-compatible controller using the separate reference BSP's I2C/reset pins. The levelling page toggles between the two largest estimated lift needs and all four corner values. Physical touch operation and orientation remain unverified. |
| Estimate corner lift heights from pitch and roll | Use owner-provided 4,035 mm wheelbase and 1,810/1,790 mm front/rear track widths. The current formula assumes sensor position at the wheel-footprint center, positive pitch means front-high, and positive roll means left-high; lift values raise each lower corner to the highest corner. The pitch and roll signs were confirmed on the installed van on 2026-10-16, and the owner reported correct wheel selection; the sensor-position assumption and lift accuracy remain unmeasured. |
| Indicate level attitude on HORIZON | Turn on a green frame while live displayed pitch and roll are each within ±0.5°; retain it until either exceeds ±0.7° to avoid flicker near the threshold. Both thresholds are configurable in `src/config.py`. Physical behavior remains unverified. |
| Calibrate the display's level reference | The yellow `CALIBRATE` touch button on the HORIZON screen saves current live pitch/roll offsets to `/level_reference.cfg` on the ESP32 and reloads them at startup. The user must first level the van using a trusted reference. Persistence and calibration accuracy are not yet hardware-verified. |
| Warn when sensor readings are unavailable | Show a red frame and in-screen warning for waiting, stale, disconnected, or error states. Source implements this; physical behavior remains unverified. |
| Centralize adjustable hardware and tuning values | `src/config.py` stores sensor identity and protocol assumptions, axis mapping/signs, vehicle geometry, redraw timing, and LCD/touch pin assignments. The existing assumptions are unchanged; values such as the CCCD handle and sensor signs remain unverified. |
| Composite the HORIZON page off-screen in strips | A full-screen buffer (153,600 bytes) could not be allocated, and direct drawing erased and repainted overlays on every update, which the owner observed as flicker even after limiting redraws. `compositor.py` records the page as rects and sends 240 × 40 strips (19.2 KB buffer), skipping unchanged strips. Matches the previous output in a desktop simulation; the owner reported a clear on-device improvement on 2026-10-15. Redraw timing has not been measured. |
| Keep the app in `app.py` with `setup()`/`step()`/`run()`; `main.py` only starts it | Approved by the owner on 2026-10-15 so integration tests can drive the main loop one pass at a time. Behavior is unchanged; `main.py` re-exports `save_screenshot` for the REPL, and other running objects are reachable as `app.sensor` etc. |
| Deploy precompiled `.mpy` modules | `tools/build_mpy.sh` compiles every module except `main.py` and `config.py` with `mpy-cross` 1.29; `tools/deploy.sh` uploads that bundle by default, refuses a board whose `.mpy` major version differs, and deletes stale `.py` copies because MicroPython imports `foo.py` before `foo.mpy`. CI publishes the bundle as an artifact. Chosen by the owner on 2026-10-15; a single-file app would need a custom firmware with frozen modules, which was not pursued. The deploy and app start were checked on the board. |
| Test under CPython with fake firmware modules; gate merges on CI | `tests/fakes/` replaces `machine`, `bluetooth`, and `framebuf`; the fake LCD decodes ILI9341 commands into pixels. Reference images in `tests/golden/` must be regenerated deliberately. `mpy-cross` 1.29 (matching the board's `.mpy` 6.3) checks MicroPython syntax. Running tests under the MicroPython unix port was considered and declined by the owner. Pull requests into `main` must pass the `tests` check. |
| Keep the ESP-IDF BSP as reference material | Structural fact: it is nested under `reference/` and is not part of the MicroPython import path or a top-level build. Treating it as non-active is a documentation convention, not proof of long-term intent. |

## Dashboard integration update

The display uses a virtual horizon with pitch/roll readouts, a pitch ladder, and a camper marker. It fills the screen area below the status and readout bars; the compass has been removed. `app.py` swaps the client's decoded `roll` and `pitch` values to match the reported installed sensor response; the client continues to decode yaw, but the display ignores it. The mapping signs and operation remain to be checked on hardware.

`ble_scan.py` remains an optional diagnostic utility. The application does not import it; normal startup and scanning are handled by `WT901BLEClient`.

## Status distinctions

- **Implemented:** source-level functionality described above.
- **Tested:** automated desktop tests with fake hardware run in CI (see README, "Tests and CI"); they verify source behavior and rendering, not the physical sensor, touch, or display.
- **Planned:** no formal approved roadmap is present. Confirm BLE notification setup and measure the accuracy of the corner lift estimates on the installed van.
- **Unverified:** physical hardware identity/wiring, actual BLE behavior and protocol, conversions, and vehicle coordinate conventions.

## Open questions

1. Is the physical board specifically an ES3C28P, and is the active software expected to remain MicroPython or migrate to the ESP-IDF BSP?
2. What exact WT901 model/configuration is used? Are its BLE address and GATT UUIDs stable, and what descriptor enables notifications? The current reader writes to handle 16 without discovery.
3. Does the sensor emit complete 20-byte `55 61` notifications as assumed? What checksum/framing and scaling rules apply?
4. Resolved 2026-10-16: the swapped axis mapping gives the expected signs (front up positive pitch, left up positive roll). Still open: what angle limits are desired?
5. Confirm the on-device level-reference file persists across restart and that the calibration procedure gives the expected zero on the installed van.
6. What hardware test procedure and acceptance criteria define a working display and accurate levelling readout?
7. Does the related-model voltage-to-percentage table accurately represent the battery level throughout the operating range of this exact sensor? Compare more readings with the Android app.
8. Does the active board use the FT5x06 controller and reference BSP touch pin mapping (I2C GPIO 15/16, reset GPIO 18), and do raw touch coordinates match display coordinates?

No unresolved question should be filled in by guessing; capture hardware observations or obtain project-owner direction and record the result here or in `hardware.md`.
