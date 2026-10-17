"""FT5x06 touch reader and the app's touch target hit-tests.

Touch coordinates are assumed to match display coordinates; that orientation
has not been verified on the hardware.
"""

import pytest


@pytest.fixture
def touch_module(import_fresh):
    return import_fresh("touch")


def test_missing_controller_raises(touch_module):
    with pytest.raises(OSError):
        touch_module.TouchInput()


def test_read_returns_point_or_none(touch_module, touch):
    touch.present = True
    reader = touch_module.TouchInput()
    assert reader.read() is None
    touch.point = (300, 17)
    assert reader.read() == (300, 17)


def centre(rect):
    x, y, width, height = rect
    return x + width // 2, y + height // 2


def test_navigation_buttons(app):
    y = app.NAV_Y + app.NAV_HEIGHT // 2
    assert app.touch_screen_at((60, y)) == 0
    assert app.touch_screen_at((180, y)) == 1
    assert app.touch_screen_at((120, y)) is None  # Gap between the buttons.
    assert app.touch_screen_at((60, app.NAV_Y - 1)) is None
    assert app.touch_screen_at(None) is None


def test_calibrate_button_only_on_horizon_page(app):
    point = centre(app.CALIBRATE_RECT)
    app.active_screen = 0
    assert app.touch_calibrate_at(point)
    assert not app.touch_calibrate_at((point[0], point[1] + app.CALIBRATE_RECT[3]))
    app.active_screen = 1
    assert not app.touch_calibrate_at(point)


def test_corner_view_tabs(app):
    y = app.CORNER_TABS_Y + app.NAV_HEIGHT // 2
    assert app.touch_corner_view_at((60, y)) == 0
    assert app.touch_corner_view_at((180, y)) == 1
    assert app.touch_corner_view_at((60, app.CORNER_TABS_Y + app.NAV_HEIGHT)) is None


def test_touch_targets_sit_below_case_inset(app):
    assert app.NAV_Y >= app.SCREEN_TOP_INSET
    assert app.CALIBRATE_RECT[1] >= app.HORIZON_TOP
