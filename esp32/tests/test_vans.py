"""The tilting rear and side views on the HORIZON page (src/vans.py)."""

import pytest


@pytest.fixture
def vans(import_fresh):
    return import_fresh("vans")


def opaque(picture):
    """(x, y) of every non-transparent pixel of a vans Bitmap."""
    pixel = picture.framebuffer.pixel
    return [
        (x, y) for y in range(picture.height) for x in range(picture.width) if pixel(x, y)
    ]


def screen_pixels(result):
    """Opaque pixels in coordinates relative to the ground point between the wheels."""
    picture, left, top = result
    return [(left + x, top + y) for x, y in opaque(picture)]


def bottom_of(pixels, x_range):
    return max(y for x, y in pixels if x_range[0] <= x < x_range[1])


@pytest.mark.parametrize("view_name", ["REAR", "SIDE"])
def test_level_van_stands_on_the_ground(vans, view_name):
    pixels = screen_pixels(vans.draw_tilted(getattr(vans, view_name), 0.0, 20.0))
    # The tyres reach the ground line (rounding may sink them by a pixel).
    assert max(y for _, y in pixels) in (-1, 0, 1)


@pytest.mark.parametrize("view_name", ["REAR", "SIDE"])
def test_positive_tilt_turns_clockwise_on_the_low_wheel(vans, view_name):
    van = getattr(vans, view_name)
    level = screen_pixels(vans.draw_tilted(van, 0.0, 20.0))
    tilted = screen_pixels(vans.draw_tilted(van, 10.0, 20.0))
    wheel_left, wheel_right = (wheel / 4 for wheel in van["wheels"])  # Quarter pixels.
    middle = (wheel_left + wheel_right) / 2
    left_wheel = (int(wheel_left - middle) - 3, int(wheel_left - middle) + 4)
    right_wheel = (int(wheel_right - middle) - 3, int(wheel_right - middle) + 4)
    # Clockwise: the left wheel lifts off, the right wheel stays down.
    assert bottom_of(tilted, left_wheel) < bottom_of(level, left_wheel) - 3
    assert bottom_of(tilted, right_wheel) >= bottom_of(level, right_wheel) - 1


def test_tilt_is_clamped(vans):
    clamped = screen_pixels(vans.draw_tilted(vans.REAR, 90.0, 20.0))
    at_limit = screen_pixels(vans.draw_tilted(vans.REAR, 20.0, 20.0))
    assert clamped == at_limit


def test_unchanged_tilt_reuses_the_picture(vans):
    first = vans.draw_tilted(vans.SIDE, 4.0, 20.0)
    assert vans.draw_tilted(vans.SIDE, 4.0, 20.0)[0] is first[0]
    assert vans.draw_tilted(vans.SIDE, 5.0, 20.0)[0] is not first[0]


def test_buffer_fits_the_largest_tilt(vans):
    for angle in (-20.0, -7.5, 0.0, 13.0, 20.0):
        picture, _, _ = vans.draw_tilted(vans.SIDE, angle, 20.0)
        assert (picture.width + 1) // 2 * picture.height <= len(vans._buffers[id(vans.SIDE)])


def wheel_x(app, van, index):
    left, right = van["wheels"]  # Quarter pixels.
    return int(app.HORIZON_CENTER_X + (van["wheels"][index] - (left + right) / 2) / 4)


def test_roll_lifts_the_left_side_of_the_rear_view(app, panel):
    app.active_screen = 0
    app.draw_dashboard({"roll": 0.0, "pitch": 3.0, "yaw": 0.0}, "LIVE")  # Roll +3.
    below = app.REAR_GROUND_Y - 2
    assert panel.pixel(wheel_x(app, app.vans.REAR, 0), below) == app.SKY  # Left lifted.
    assert panel.pixel(wheel_x(app, app.vans.REAR, 1), below) != app.SKY  # Right down.


def test_pitch_lifts_the_front_of_the_side_view(app, panel):
    app.active_screen = 0
    app.draw_dashboard({"roll": 3.0, "pitch": 0.0, "yaw": 0.0}, "LIVE")  # Pitch +3.
    below = app.SIDE_GROUND_Y - 2
    assert panel.pixel(wheel_x(app, app.vans.SIDE, 1), below) == app.SKY  # Front lifted.
    assert panel.pixel(wheel_x(app, app.vans.SIDE, 0), below) != app.SKY  # Rear down.


def test_ground_edge_turns_green_per_level_axis(app, panel):
    from graphics import GREEN, WHITE

    app.active_screen = 0
    app.draw_dashboard({"roll": 0.1, "pitch": 2.0, "yaw": 0.0}, "LIVE")  # Pitch 0.1, roll 2.
    assert panel.pixel(10, app.REAR_GROUND_Y) == WHITE  # Roll 2°: not level.
    assert panel.pixel(10, app.SIDE_GROUND_Y) == GREEN  # Pitch 0.1°: level.
