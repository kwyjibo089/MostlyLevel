"""The green level frame around the page (not the header and menu), on every page and view."""

import pytest
from test_app_flow import step
from test_rendering import full_direct_redraw, sensor_values, snapshot

from support.sensor import SensorSimulator

PAGES = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (page, sub-page)
IDS = ["van", "horizon", "wedges", "corners"]


def frame_points(app):
    edge = app.LEVEL_FRAME_THICKNESS - 1
    return {
        "page top": (120, app.HORIZON_TOP + edge),
        "page top left": (0, app.HORIZON_TOP),
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
def test_frame_surrounds_the_page_only(app, panel, page, view):
    from graphics import GREEN

    show(app, page, view)
    app.level_frame_active = True
    app.draw_dashboard(sensor_values(0.1, 0.1), "LIVE")
    for name, (x, y) in frame_points(app).items():
        assert panel.pixel(x, y) == GREEN, name
    # Like the red warning frame, it leaves the header and the menu alone.
    for name, (x, y) in {
        "header top": (120, app.HEADER_Y),
        "header left": (0, app.HEADER_Y + 8),
        "menu left": (0, app.NAV_Y + 5),
        "menu right": (app.WIDTH - 1, app.NAV_Y + 5),
        "above the page": (120, app.HORIZON_TOP - 1),
    }.items():
        assert panel.pixel(x, y) != GREEN, name
    # The tabs start below the frame's top edge.
    assert app.CORNER_TABS_Y >= app.HORIZON_TOP + app.LEVEL_FRAME_THICKNESS


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
    assert panel.pixel(*frame_points(app)["page top"]) != GREEN

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
    # The red warning frame has replaced the green one everywhere.
    for name, (x, y) in frame_points(app).items():
        assert panel.pixel(x, y) != GREEN, name
