"""Rendering invariants: the optimised redraw paths must produce exactly the
pixels a full, direct redraw would."""

import random
from array import array

import pytest

WIDTH = 240


def sensor_values(pitch, roll):
    return {"roll": pitch, "pitch": roll, "yaw": 0.0}


def snapshot(panel):
    return array("H", panel.pixels)


def full_direct_redraw(app, panel, values, state="LIVE"):
    """Reference image: redraw everything without the strip compositor."""
    saved_pixels = snapshot(panel)
    renderer = app.horizon_renderer
    app.horizon_renderer = None
    try:
        app.draw_dashboard(values, state)
        return snapshot(panel)
    finally:
        app.horizon_renderer = renderer
        panel.pixels = saved_pixels


def below_header(pixels, app):
    return pixels[app.HORIZON_TOP * WIDTH:]


@pytest.mark.parametrize(
    "pitch, roll, level",
    [(0.0, 0.0, True), (3.0, -2.0, False), (-20.0, 30.0, False), (50.0, -60.0, False)],
)
def test_composited_page_matches_direct_drawing(app, panel, pitch, roll, level):
    app.active_screen = 0
    app.level_frame_active = level
    values = sensor_values(pitch, roll)
    app.draw_dashboard(values, "LIVE")
    assert snapshot(panel) == full_direct_redraw(app, panel, values)


def random_walk(seed, steps):
    rng = random.Random(seed)
    pitch = roll = 0.0
    for _ in range(steps):
        if rng.random() < 0.1:
            pitch, roll = rng.uniform(-60, 60), rng.uniform(-60, 60)
        else:
            pitch += rng.uniform(-1.5, 1.5)
            roll += rng.uniform(-1.5, 1.5)
        yield pitch, roll


@pytest.mark.parametrize("seed", [1, 2])
def test_live_horizon_updates_match_full_redraw(app, panel, seed):
    app.active_screen = 0
    app.level_frame_active = False
    app.draw_dashboard(sensor_values(0.0, 0.0), "LIVE")
    for pitch, roll in random_walk(seed, 40):
        level = abs(pitch) <= 0.6 and abs(roll) <= 0.6
        app.level_frame_active = level
        values = sensor_values(pitch, roll)
        display, vehicle_pitch, vehicle_roll = app.vehicle_values(values)
        app.draw_horizon_page(vehicle_pitch, vehicle_roll, display, level)
        reference = full_direct_redraw(app, panel, values)
        assert below_header(snapshot(panel), app) == below_header(reference, app), (pitch, roll)


def test_unchanged_horizon_sends_no_pixels(app, panel):
    app.active_screen = 0
    values = sensor_values(1.0, 2.0)
    app.draw_dashboard(values, "LIVE")
    display, pitch, roll = app.vehicle_values(values)
    panel.pixel_bytes = 0
    app.draw_horizon_page(pitch, roll, display, False)
    assert panel.pixel_bytes == 0


def test_horizon_repaints_after_warning_overlay(app, panel):
    app.active_screen = 0
    values = sensor_values(1.0, 2.0)
    app.draw_dashboard(values, "LIVE")
    app.draw_sensor_warning("NO DATA")
    display, pitch, roll = app.vehicle_values(values)
    app.draw_horizon_page(pitch, roll, display, False)
    reference = full_direct_redraw(app, panel, values)
    assert below_header(snapshot(panel), app) == below_header(reference, app)


@pytest.mark.parametrize("view", [0, 1])
def test_levelling_updates_match_full_redraw(app, panel, view):
    app.active_screen = 1
    app.corner_view = view
    app.draw_dashboard(sensor_values(2.0, 1.0), "LIVE")
    walk = [(2.0, 1.0), (0.01, 0.0), (0.0, 0.0), (-3.0, 2.0), (-3.05, 2.02)]
    walk += list(random_walk(view + 10, 20))
    for pitch, roll in walk:
        values = sensor_values(pitch, roll)
        app.update_corner_heights(values)
        reference = full_direct_redraw(app, panel, values)
        assert below_header(snapshot(panel), app) == below_header(reference, app), (pitch, roll)


def test_strip_buffer_falls_back_to_smaller_rows(app, monkeypatch):
    sizes = []

    class FlakyRenderer:
        def __init__(self, lcd, top, bottom, rows):
            sizes.append(rows)
            if rows > 10:
                raise MemoryError
            self.rows = rows

    monkeypatch.setattr(app, "StripRenderer", FlakyRenderer, raising=False)
    renderer = app.create_horizon_renderer()
    assert sizes == [40, 20, 10]
    assert renderer.rows == 10


def bmp_pixels(path):
    data = path.read_bytes()
    assert data[:2] == b"BM"
    width = int.from_bytes(data[18:22], "little")
    height = int.from_bytes(data[22:26], "little", signed=True)
    assert (width, height) == (240, -320)  # Top-down rows.
    return data[54:]


def test_screenshot_matches_screen(app, panel, tmp_path):
    from support.png import rgb565_to_rgb

    app.active_screen = 0
    app.level_frame_active = False
    values = sensor_values(2.0, -3.0)
    app.draw_dashboard(values, "LIVE")
    _, pitch, roll = app.vehicle_values(values)
    app.last_attitude = (pitch, roll)
    app.last_state = "LIVE"

    path = tmp_path / "shot.bmp"
    app.save_screenshot(str(path))
    pixels = bmp_pixels(path)
    for index, colour in enumerate(panel.pixels):
        red, green, blue = rgb565_to_rgb(colour)
        assert pixels[index * 3:index * 3 + 3] == bytes((blue, green, red)), index


def test_cached_layers_match_fresh_drawing(app):
    """Fixed HORIZON layers are recorded once and replayed unchanged."""
    from compositor import DisplayList
    from graphics import Graphics

    def fresh(draw, *args):
        saved = app.g
        recorder = DisplayList()
        app.g = Graphics(recorder)
        try:
            draw(*args)
        finally:
            app.g = saved
        return recorder.items

    app.layer_cache.clear()
    first = app.horizon_page_items(3.0, -2.0, {"pitch": 3.0, "roll": -2.0}, True)
    assert set(app.layer_cache) == {"arc", "van", "calibrate", "level"}
    assert list(app.layer_cache["arc"]) == fresh(app.draw_pitch_arc)
    assert list(app.layer_cache["van"]) == fresh(app.draw_van_side, app.HORIZON_CENTER_Y)
    assert list(app.layer_cache["calibrate"]) == fresh(app.draw_calibrate_button)
    assert list(app.layer_cache["level"]) == fresh(app.draw_level_frame)

    calls = []
    app.draw_pitch_arc = lambda: calls.append("arc")
    again = app.horizon_page_items(3.0, -2.0, {"pitch": 3.0, "roll": -2.0}, True)
    assert calls == [] and again == first


def test_glyph_runs_cover_exactly_the_set_pixels():
    from graphics import FONT, glyph_runs

    for glyph in FONT.values():
        pixels = {
            (x, row) for col, row, width in glyph_runs(glyph) for x in range(col, col + width)
        }
        expected = {
            (col, row) for col, bits in enumerate(glyph) for row in range(8) if bits & (1 << row)
        }
        assert pixels == expected
