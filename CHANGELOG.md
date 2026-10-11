# Changelog

Notable project changes are recorded here. This file was introduced with the initial project documentation; earlier implementation history is not available from the top-level repository metadata.

## Unreleased

- Removed the compass and expanded the virtual horizon to occupy the display area below the status and pitch/roll readout bars.
- Swapped decoded pitch/roll channels at the display boundary to match the owner's reported sensor movement; signs still need hardware confirmation.
- Replaced the static demo screen with a mockup-inspired attitude and compass dashboard driven by the WT901 BLE client.
- Refactored `ble_read.py` into an import-safe client while retaining its console diagnostic mode.
- Added project guidance, context, architecture, hardware, and decision documentation.
- Documented MicroPython source deployment and startup steps in the README.
- Hardware rendering and sensor notification behavior remain unverified.
