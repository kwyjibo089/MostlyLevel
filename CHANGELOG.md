# Changelog

Notable project changes are recorded here. This file was introduced with the initial project documentation; earlier implementation history is not available from the top-level repository metadata.

## Unreleased

- Added a persistent level-reference calibration action on the HORIZON screen, a prominent red warning for unavailable sensor data, and separate 0.5°/0.7° level-frame on/off thresholds. Styled `CALIBRATE` as a rounded yellow button in the upper-right above the horizon arc. Grouped repeated horizon and ladder drawing operations, batched LCD address-window commands, and rasterized text in horizontal runs to reduce redraw flicker; hardware speedup remains to be measured.
- Added a thicker green frame around the HORIZON display region when live pitch and roll are both within ±0.5°; inset the pitch/roll readout boxes with clear spacing. The threshold is configurable.
- Added `src/config.py` for sensor identity/protocol settings, sensor axis mapping and scaling, vehicle geometry, display timing, and LCD/touch wiring; updated the client, scanner, and drivers to use it.
- Updated the README screenshot gallery with the HORIZON, 4 CORNERS, and 2 WEDGES screens.
- Renamed the first touchscreen page button from `LEVEL` to `HORIZON` to describe its virtual-horizon display.
- Added a touch-selectable second page that ranks the estimated wheel-corner lift heights and shows the two largest for a two-wedge setup. Values use pitch, roll, wheelbase, and front/rear track width. The FT5x06-compatible touch reader uses reference board wiring; physical touch behavior and corner-height sign assumptions remain unverified.
- Added a `4 CORNERS` view alongside `2 WEDGES` on the `LEVELLING` page, with touch tabs; `2 WEDGES` remains the default.
- Added an automatic battery percentage read every 60 seconds and display beside `LIVE` in the top bar. The 385 (3.85 V) reading maps to 60% using a related WT9011DCL-BT50 voltage table and matched the Android app on the connected unit.
- Removed the compass and expanded the virtual horizon to occupy the display area below the status and pitch/roll readout bars.
- Swapped decoded pitch/roll channels at the display boundary to match the owner's reported sensor movement; signs still need hardware confirmation.
- Avoided full-screen clears during normal updates; the header now redraws only on connection-status changes, and the readouts/horizon redraw only when displayed pitch or roll changes.
- Added a 0.2° attitude redraw deadband to suppress display updates from small sensor fluctuations.
- Added an on-demand software-rendered BMP screenshot function using an 8-row tile buffer after controller MISO readback returned all-zero pixels and a full-screen buffer allocation failed.
- Replaced the static demo screen with a mockup-inspired attitude and compass dashboard driven by the WT901 BLE client.
- Refactored `ble_read.py` into an import-safe client while retaining its console diagnostic mode.
- Added project guidance, context, architecture, hardware, and decision documentation.
- Documented MicroPython source deployment and startup steps in the README.
- Hardware rendering and sensor notification behavior remain unverified.
