# MostlyLevel Android app

A React Native (Expo) app with the same functionality as the ESP32 display in [`../esp32`](../esp32): it connects directly to the WT901 Bluetooth tilt sensor and shows how the camper is tilted and how much to lift each wheel. The screens are designed for a phone rather than copied from the 240 × 320 display.

> **Status: first version.** The levelling maths and sensor decoding are checked against the ESP32 code (see [Parity with the ESP32](#parity-with-the-esp32)). On 2026-10-17 it connected to the owner's sensor on a Pixel 8a (Android 17) and showed live attitude and the battery level; calibration, levelling in the van, reconnection, and long runs on the phone are not yet tested.

## What it does

- **Attitude › Van:** the chosen camper seen from behind (tilting with roll) and from the side (tilting with pitch), pivoting on its lower wheel. The tilt is drawn 3× (max 20°) so small slopes show; the readouts are the true angles. Each ground line turns green when that axis is within ±0.5°.
- **Attitude › Horizon:** aircraft-style virtual horizon with the camper from behind as the fixed symbol. Positive roll (left side high) makes the horizon rise on the right, as on the ESP32.
- **Levelling › 2 wedges / 4 corners:** lift per wheel from pitch, roll, wheelbase, and track widths; 2 wedges ranks the two corners to lift and says "No wedges needed" below 0.5 cm.
- **Calibrate:** hold for 1 s with a live sensor to save the current attitude as level.
- **Level frame:** green around the screen while pitch and roll are within ±0.5°, kept until either exceeds ±0.7°. A red frame and a warning show when data is stale (> 1.5 s), the link is lost, the app is still searching, Bluetooth is off, or access was refused.
- **Battery:** the sensor's battery percentage, polled every 60 s.
- **Sensor source:** the WT901 over Bluetooth, or the **phone's own accelerometer** (no extra hardware). The phone lies flat, screen up, top toward the front of the van, always in the same spot; each source keeps its own calibration. Switching to the phone disconnects the WT901, so the ESP32 display can use it.
- **Settings:** sensor source, language (EN, DE, FR, ES), scanning for and choosing the sensor, camper type (compact van, panel van, alcove, semi-integrated, integrated) and body colour, and wheelbase / track widths.
- The screen stays on while the app is open. In the background the app disconnects, because the sensor accepts one connection at a time (so the ESP32 display can use it).

Differences from the ESP32, by design: the vans and horizon are smoothed between samples (readouts and lifts are not); the language is changed in settings or with the button next to CALIBRATE by a single tap; camper type, colour, dimensions, and the sensor are chosen in the app instead of `config.py`.

## Layout

| Path | Contents |
| --- | --- |
| `src/config.ts` | Sensor, levelling, and timing constants, mirroring `esp32/src/config.py` |
| `src/sensor/protocol.ts` | WT901 packet and battery decoding (port of `ble_read.py`) |
| `src/sensor/client.ts` | BLE client state machine with the ESP32's recovery rules, behind a transport interface |
| `src/sensor/bleManagerTransport.ts` | The transport on `react-native-ble-manager` |
| `src/sensor/phone.ts` | The phone's accelerometer as attitude source: gravity to pitch/roll, low-pass filter |
| `src/levelling.ts` | Axis mapping, level reference, corner lifts, wedge ranking, hysteresis, van tilt (port of `app.py`) |
| `src/campers.ts` | Camper drawings (vector layers), typical dimensions, colours |
| `src/app/` | Screens (Expo Router): Attitude, Levelling, Settings |
| `src/components/` | Drawings and UI pieces |
| `src/i18n/` | Screen texts; mixed case, so separate from the ESP32's all-caps `shared/i18n/` |
| `test/` | Jest tests: parity with the ESP32 fixtures, BLE client behaviour |
| `scripts/make-icons.mjs` | Renders the app icon and splash PNGs in `assets/` (`node scripts/make-icons.mjs`) |

## Development

Needs Node 22, JDK 17, and the Android SDK (`ANDROID_HOME`). On the owner's Mac these come from Homebrew; `~/.zshrc` sets the paths and `JAVA_HOME_ANDROID`.

```bash
cd mobile
npm install
npm run android     # build, install on the connected phone, start the bundler
npm start           # bundler only, once the app is installed
npm run check       # TypeScript and tests
```

`npm run android` builds a development build (`expo-dev-client`); JavaScript changes then reload on the phone without rebuilding. The `android/` folder is generated (`expo prebuild`) and not committed: configure native settings in `app.json`.

Bluetooth does not work in the Android emulator; use a phone with USB or wireless debugging.

## Parity with the ESP32

`esp32/tools/make_fixtures.py` runs the ESP32 code and writes its results for fixed inputs to `shared/fixtures/`: packet decoding, battery bands, axis mapping, level reference, corner lifts, wedge ranking, hysteresis, and van tilt. `test/parity.test.ts` checks this app against them, and an ESP32 test fails if the fixtures are out of date. Change shared behaviour in both apps and regenerate the fixtures.
