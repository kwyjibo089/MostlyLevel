"""The green level frame around the whole screen, on every page and view."""

import pytest
from test_app_flow import step
from test_rendering import full_direct_redraw, sensor_values, snapshot

from support.sensor import SensorSimulator

PAGES = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (page, sub-page)
IDS = ["van", "horizon", "wedges", "corners"]


def frame_points(app):
    edge = app.LEVEL_FRAME_THICKNESS - 1
    return {
        "header top": (120, app.HEADER_Y),
        "header left": (edge, app.HEADER_Y + 8),
        "menu left": (0, app.NAV_Y + 5),
        "menu right": (app.WIDTH - 1, app.NAV_Y + 5),
        "page left": (0, 200),
        "page right": (app.WIDTH - 1 - edge, 200),
        "bottom": (120, app.HEIGHT - 1),
    }


def show(app, page, view):
    app.active_screen = page
    if page == 0:
        app.attitude_view = view
    else:
        app.corner_view = view


@pytest.mark.parametrize("page, view", PAGES, ids=IDS)
def test_frame_surrounds_header_menu_and_page(app, panel, page, view):
    from graphics import GREEN

    show(app, page, view)
    app.level_frame_active = True
    app.draw_dashboard(sensor_values(0.1, 0.1), "LIVE")
    for name, (x, y) in frame_points(app).items():
        assert panel.pixel(x, y) == GREEN, name
    # The menu buttons themselves are not covered.
    assert panel.pixel(app.LEVEL_FRAME_THICKNESS, app.NAV_Y + 5) != GREEN


@pytest.mark.parametrize("page, view", PAGES, ids=IDS)
def test_frame_appears_and_goes_while_live(app, fake_clock, panel, page, view):
    from graphics import GREEN

    sim = SensorSimulator()
    step(app, fake_clock)
    sim.connect()
    show(app, page, view)
    sim.attitude(roll=3.0, pitch=2.0)  # Not level.
    step(app, fake_clock)
    app.draw_dashboard(app.sensor.latest, "LIVE")
    tilted = snapshot(panel)
    header_top = frame_points(app)["header top"]
    assert panel.pixel(*header_top) != GREEN

    fake_clock.advance(300)
    sim.attitude(roll=0.1, pitch=0.1)  # Level.
    step(app, fake_clock)
    assert app.level_frame_active
    for name, (x, y) in frame_points(app).items():
        assert panel.pixel(x, y) == GREEN, name

    fake_clock.advance(300)
    sim.attitude(roll=3.0, pitch=2.0)
    step(app, fake_clock)
    assert not app.level_frame_active
    # Exactly as before the frame came on, and as a full redraw draws it.
    assert snapshot(panel) == tilted
    assert snapshot(panel) == full_direct_redraw(app, panel, app.sensor.latest)


def test_frame_goes_when_data_turns_stale(app, fake_clock, panel):
    from graphics import GREEN

    sim = SensorSimulator()
    step(app, fake_clock)
    sim.connect()
    sim.attitude(roll=0.1, pitch=0.1)
    step(app, fake_clock)
    assert app.level_frame_active
    fake_clock.advance(1600)  # SENSOR_STALE_MS is 1500.
    step(app, fake_clock)
    assert app.last_state == "NO DATA"
    for name in ("header top", "menu left", "menu right"):
        assert panel.pixel(*frame_points(app)[name]) != GREEN, name
