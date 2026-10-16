"""Integration tests: drive app.step() through realistic sessions.

The real BLE client receives events from a simulated sensor, touches come
from the fake FT5x06 controller, and time comes from the fake clock. Key
screens are compared with reference images (tests/golden/flow_*.png).
Sensor packets and touch orientation follow the code's assumptions; they
are not recordings from the real hardware.
"""

import sys
import types

import pytest
from support.app import SRC_MODULES, load_app
from support.golden import assert_matches_golden
from support.sensor import WRITE_HANDLE, SensorSimulator

STEP_MS = 30


def step(app, clock, count=1):
    for _ in range(count):
        app.step()
        clock.advance(STEP_MS)


def go_live(app, clock, pitch=2.0, roll=-1.0):
    """Connect the simulated sensor and deliver one attitude sample."""
    sim = SensorSimulator()
    step(app, clock)
    sim.connect()
    sim.attitude(roll=pitch, pitch=roll)  # Decoded channels, before mapping.
    step(app, clock)
    assert app.last_state == "LIVE"
    return sim


def tap(app, clock, touch, point):
    touch.point = point
    step(app, clock)
    touch.point = None
    step(app, clock)


def hold(app, clock, touch, point, ms=None):
    """Press `point`, keep it down for `ms` (default: the long press), release."""
    from config import LONG_PRESS_MS

    touch.point = point
    held = 0
    # Slightly longer than the long press, so it completes before release.
    target = LONG_PRESS_MS + 2 * STEP_MS if ms is None else ms
    while held <= target:
        step(app, clock)
        held += STEP_MS
    touch.point = None
    step(app, clock)


def centre(rect):
    x, y, width, height = rect
    return x + width // 2, y + height // 2


def test_startup_waits_for_sensor(app, fake_clock, panel, request):
    step(app, fake_clock)
    assert app.last_state == "SCANNING"
    assert_matches_golden(request, "flow_waiting", panel.pixels)


def test_live_attitude_and_battery_poll(app, fake_clock, panel, request):
    from config import SENSOR_POWER_READ_COMMAND

    sim = go_live(app, fake_clock)
    assert app.last_attitude == (pytest.approx(2.0, abs=0.01), pytest.approx(-1.0, abs=0.01))
    requests = sim.ble.writes(WRITE_HANDLE)
    assert [call[3] for call in requests] == [SENSOR_POWER_READ_COMMAND]
    assert_matches_golden(request, "flow_live", panel.pixels)

    sim.power(385)
    step(app, fake_clock)
    assert app.last_battery_percent == 60
    assert_matches_golden(request, "flow_live_battery", panel.pixels)

    # The battery is polled again only after BATTERY_POLL_INTERVAL_MS (60 s).
    for _ in range(2):
        fake_clock.advance(30000)
        sim.attitude(roll=2.0, pitch=-1.0)
        step(app, fake_clock)
    assert len(sim.ble.writes(WRITE_HANDLE)) == 2


def test_stale_data_warning_and_recovery(app, fake_clock, panel, request):
    sim = go_live(app, fake_clock)
    live_screen = panel.pixels[:]

    fake_clock.advance(1600)  # SENSOR_STALE_MS is 1500.
    step(app, fake_clock)
    assert app.last_state == "NO DATA"
    assert_matches_golden(request, "flow_stale", panel.pixels)

    sim.attitude(roll=2.0, pitch=-1.0)
    step(app, fake_clock)
    assert app.last_state == "LIVE"
    assert panel.pixels == live_screen


def test_redraws_are_throttled_and_deadbanded(app, fake_clock, panel):
    sim = go_live(app, fake_clock)

    panel.pixel_bytes = 0
    sim.attitude(roll=5.0, pitch=-1.0)
    step(app, fake_clock)  # Within RENDER_INTERVAL_MS of the last redraw.
    assert panel.pixel_bytes == 0

    fake_clock.advance(250)
    sim.attitude(roll=5.0, pitch=-1.0)
    step(app, fake_clock)
    assert panel.pixel_bytes > 0
    assert app.last_attitude[0] == pytest.approx(5.0, abs=0.01)

    fake_clock.advance(250)
    panel.pixel_bytes = 0
    sim.attitude(roll=5.1, pitch=-1.0)  # Below the 0.2° redraw threshold.
    step(app, fake_clock)
    assert panel.pixel_bytes == 0


def test_calibrate_by_touch_saves_reference(
    app_with_touch, fake_clock, touch, panel, request, reference_file
):
    app = app_with_touch
    go_live(app, fake_clock)
    sensor_pitch = app.sensor.latest["roll"]
    sensor_roll = app.sensor.latest["pitch"]

    hold(app, fake_clock, touch, centre(app.CALIBRATE_RECT))
    assert reference_file.read_text() == "%.5f\n%.5f\n" % (sensor_pitch, sensor_roll)
    assert app.last_attitude == (0.0, 0.0)
    assert app.level_frame_active
    assert_matches_golden(request, "flow_calibrated", panel.pixels)

    # The reference survives a restart.
    restarted = load_app(reference_file)
    assert restarted.pitch_zero == pytest.approx(sensor_pitch, abs=1e-5)
    assert restarted.roll_zero == pytest.approx(sensor_roll, abs=1e-5)


def test_calibrate_needs_live_sensor(
    app_with_touch, fake_clock, touch, panel, request, reference_file
):
    app = app_with_touch
    step(app, fake_clock)
    hold(app, fake_clock, touch, centre(app.CALIBRATE_RECT))
    assert not reference_file.exists()
    assert_matches_golden(request, "flow_calibrate_refused", panel.pixels)


def test_touch_navigation(app_with_touch, fake_clock, touch, panel, request):
    app = app_with_touch
    go_live(app, fake_clock)
    nav_y = app.NAV_Y + app.NAV_HEIGHT // 2
    tabs_y = app.CORNER_TABS_Y + app.NAV_HEIGHT // 2

    tap(app, fake_clock, touch, (180, nav_y))
    assert app.active_screen == 1
    tap(app, fake_clock, touch, (180, tabs_y))
    assert app.corner_view == 1
    assert_matches_golden(request, "flow_corners", panel.pixels)

    # A held finger triggers only once: sliding onto HORIZON does nothing.
    touch.point = (180, tabs_y)
    step(app, fake_clock)
    touch.point = (60, nav_y)
    step(app, fake_clock)
    assert app.active_screen == 1
    touch.point = None
    step(app, fake_clock)
    tap(app, fake_clock, touch, (60, nav_y))
    assert app.active_screen == 0


def test_disconnect_shows_warning(app, fake_clock, panel, request):
    from graphics import RED

    sim = go_live(app, fake_clock, pitch=0.1, roll=0.1)
    assert app.level_frame_active
    sim.disconnect()
    step(app, fake_clock)
    # The client is already rescanning, but the screen reports the lost link.
    assert app.sensor.state == "SCANNING"
    assert app.last_state == "DISCONNECTED"
    assert not app.level_frame_active
    assert panel.pixel(0, app.HORIZON_TOP) == RED
    assert_matches_golden(request, "flow_disconnected", panel.pixels)

    # Finding the sensor again does not clear the warning on its own...
    sim.advertise()
    step(app, fake_clock)
    assert app.last_state == "DISCONNECTED"

    # ...only working notifications and fresh data do.
    sim.connect()
    sim.attitude(roll=0.1, pitch=0.1)
    step(app, fake_clock)
    assert app.last_state == "LIVE"
    assert app.level_frame_active


def test_first_connection_waits_rather_than_disconnected(app, fake_clock):
    step(app, fake_clock)
    SensorSimulator().scan_done()
    step(app, fake_clock)
    assert app.last_state == "SCANNING"


def test_touch_failure_disables_touch(app_with_touch, fake_clock):
    app = app_with_touch

    def broken_read():
        raise OSError("I2C bus error")

    app.touch.read = broken_read
    step(app, fake_clock)
    assert app.touch is None
    step(app, fake_clock)  # The loop keeps running without touch.


def test_main_entry_point_runs_app(monkeypatch):
    calls = []
    fake_app = types.ModuleType("app")
    fake_app.run = lambda: calls.append("run")
    fake_app.save_screenshot = object()
    for module in SRC_MODULES:
        monkeypatch.delitem(sys.modules, module, raising=False)
    monkeypatch.setitem(sys.modules, "app", fake_app)

    from support.app import SRC

    namespace = {"__name__": "__main__"}
    exec(compile((SRC / "main.py").read_text(), "main.py", "exec"), namespace)
    assert calls == ["run"]
    # tools/screenshot.sh calls save_screenshot() in the REPL after Ctrl+C.
    assert namespace["save_screenshot"] is fake_app.save_screenshot


class StopLoop(BaseException):
    """Ends run()'s endless loop in a test, like Ctrl+C on the board."""


def run_until(app, monkeypatch, steps):
    """Run app.run() with setup skipped and step() replaced by `steps`."""
    import fakehw
    import machine

    calls = iter(steps)

    def fake_step():
        next(calls, stop)()

    monkeypatch.setattr(app, "setup", lambda: None)
    monkeypatch.setattr(app, "step", fake_step)
    with pytest.raises((StopLoop, machine.BoardReset)) as stopped:
        app.run()
    return stopped.type, fakehw.resets


def fail():
    raise OSError("SPI bus error")


def stop():
    raise StopLoop


def test_step_errors_are_survived(app, monkeypatch, capsys):
    app.screen_initialized = True
    stopped, resets = run_until(app, monkeypatch, [fail, lambda: None, fail, fail, stop])
    assert stopped is StopLoop and resets == 0
    assert "Main loop step failed: OSError('SPI bus error')" in capsys.readouterr().out
    assert app.screen_initialized is False  # Forces a full redraw.


def test_repeated_step_errors_reset_the_board(app, monkeypatch):
    from config import STEP_ERROR_RESET_COUNT

    stopped, resets = run_until(app, monkeypatch, [fail] * STEP_ERROR_RESET_COUNT + [stop])
    assert resets == 1


def test_setup_error_resets_the_board(app, monkeypatch, fake_clock):
    import fakehw
    import machine
    from config import SETUP_ERROR_RESET_MS

    def broken_setup():
        raise OSError("LCD not responding")

    monkeypatch.setattr(app, "setup", broken_setup)
    start = fake_clock.ticks_ms()
    with pytest.raises(machine.BoardReset):
        app.run()
    assert fakehw.resets == 1
    assert fake_clock.ticks_ms() - start >= SETUP_ERROR_RESET_MS


def test_keyboard_interrupt_still_stops_the_loop(app, monkeypatch):
    import fakehw

    def interrupt():
        raise KeyboardInterrupt

    monkeypatch.setattr(app, "setup", lambda: None)
    monkeypatch.setattr(app, "step", interrupt)
    with pytest.raises(KeyboardInterrupt):
        app.run()
    assert fakehw.resets == 0


def test_link_that_never_recovers_resets_the_board(app, fake_clock):
    import fakehw
    import machine
    from config import SENSOR_ERROR_RETRY_MS, SENSOR_RECOVERY_RESET_COUNT

    sim = SensorSimulator()
    step(app, fake_clock)
    with pytest.raises(machine.BoardReset):
        for _ in range(SENSOR_RECOVERY_RESET_COUNT):
            sim.connect(cccd_status=1)  # Notification setup keeps failing.
            fake_clock.advance(SENSOR_ERROR_RETRY_MS)
            step(app, fake_clock)
            sim.disconnect()
        step(app, fake_clock)
    assert fakehw.resets == 1


def test_recovery_shows_disconnected(app, fake_clock):
    from config import SENSOR_SILENT_RECONNECT_MS

    go_live(app, fake_clock)
    fake_clock.advance(SENSOR_SILENT_RECONNECT_MS)
    step(app, fake_clock)
    assert app.sensor.state == "DISCONNECTING"
    assert app.last_state == "DISCONNECTED"


def test_a_tap_on_calibrate_does_nothing(app_with_touch, fake_clock, touch, panel, reference_file):
    app = app_with_touch
    go_live(app, fake_clock)
    before = panel.pixels[:]
    tap(app, fake_clock, touch, centre(app.CALIBRATE_RECT))
    assert not reference_file.exists()
    assert panel.pixels == before


def test_releasing_early_cancels_and_restores_the_button(
    app_with_touch, fake_clock, touch, panel, reference_file
):
    from config import LONG_PRESS_MS
    from graphics import BLACK

    app = app_with_touch
    go_live(app, fake_clock)
    before = panel.pixels[:]
    x, y, width, height = app.CALIBRATE_RECT
    touch.point = centre(app.CALIBRATE_RECT)
    for _ in range(LONG_PRESS_MS // 2 // STEP_MS):
        step(app, fake_clock)
    bar_y = y + height - 4
    bar = [panel.pixel(px, bar_y) for px in range(x + 6, x + 20)]
    assert bar == [BLACK] * len(bar)  # The progress bar is growing.
    assert app.hold_target == "calibrate"

    touch.point = None
    step(app, fake_clock)
    assert app.hold_target is None
    assert not reference_file.exists()
    assert panel.pixels == before


def test_sliding_off_cancels(app_with_touch, fake_clock, touch, reference_file):
    from config import LONG_PRESS_MS

    app = app_with_touch
    go_live(app, fake_clock)
    touch.point = centre(app.CALIBRATE_RECT)
    step(app, fake_clock)
    touch.point = (120, 200)  # Off the button, finger still down.
    for _ in range(2 * LONG_PRESS_MS // STEP_MS):
        step(app, fake_clock)
    assert not reference_file.exists()
    assert app.hold_target is None


def test_a_long_hold_acts_once(app_with_touch, fake_clock, touch):
    from config import LONG_PRESS_MS

    app = app_with_touch
    go_live(app, fake_clock)
    hold(app, fake_clock, touch, centre(app.LANGUAGE_RECT), 3 * LONG_PRESS_MS)
    assert app.i18n.language == "de"
