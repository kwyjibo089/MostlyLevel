# Guidance for future sessions

- The repository holds several projects: `esp32/` (the MicroPython display app), `mobile/` (planned React Native Android app with the same functionality), `shared/` (files used by both, such as the screen texts in `shared/i18n/`), `hardware/` (KiCad PCB), and `case/` (enclosure). Run the ESP32 tools from `esp32/`.
- Treat the application source in `esp32/src/` as the implementation source of truth.
- `esp32/reference/esp32_s3_es3c28p/` is a separate ESP-IDF board-support reference. Do not describe its features as part of the MicroPython application unless the application is changed to use them.
- Keep confirmed repository facts, hardware-tested behavior, plans, and assumptions distinct. Do not infer missing wiring, sensor settings, or successful hardware behavior.
- Preserve the current MicroPython application architecture unless the project owner directs a change.
- Keep adjustable hardware, sensor, geometry, and timing values in `esp32/src/config.py`; record whether configured values are tested or remain assumptions.
- Touchscreen support is implemented as a basic FT5x06-compatible reader using reference BSP wiring; its physical controller, wiring, and coordinate orientation are unverified. Keep those distinctions explicit.
- Before editing source, inspect the relevant code and configuration. Do not modify source merely to update documentation.
- Update `CHANGELOG.md` when making a meaningful project change. Record documentation-only changes as such.
- Work on a feature branch and open a pull request into `main`; CI (`esp32/tools/test.sh`, run from `esp32/`) must pass before merging. Run `esp32/tools/test.sh` locally first.
- Passing tests show source behavior against fake hardware only, not hardware operation. Regenerate `esp32/tests/golden/` images only for intentional visual changes, and review them.
- Record new technical decisions and unresolved questions in `docs/decisions.md` or the relevant hardware/architecture document.

See `PROJECT_CONTEXT.md` for the current project snapshot and `docs/` for detail.
