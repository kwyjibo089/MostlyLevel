# Guidance for future sessions

- Treat the application source in `src/` as the implementation source of truth.
- `reference/esp32_s3_es3c28p/` is a separate ESP-IDF board-support reference. Do not describe its features as part of the MicroPython application unless the application is changed to use them.
- Keep confirmed repository facts, hardware-tested behavior, plans, and assumptions distinct. Do not infer missing wiring, sensor settings, or successful hardware behavior.
- Preserve the current MicroPython application architecture unless the project owner directs a change.
- Touchscreen support is implemented as a basic FT5x06-compatible reader using reference BSP wiring; its physical controller, wiring, and coordinate orientation are unverified. Keep those distinctions explicit.
- Before editing source, inspect the relevant code and configuration. Do not modify source merely to update documentation.
- Update `CHANGELOG.md` when making a meaningful project change. Record documentation-only changes as such.
- Record new technical decisions and unresolved questions in `docs/decisions.md` or the relevant hardware/architecture document.

See `PROJECT_CONTEXT.md` for the current project snapshot and `docs/` for detail.
