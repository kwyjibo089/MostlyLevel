"""Corner lift estimates and LEVELLING page content.

The sign conventions tested here (positive pitch = front high, positive
roll = left high) are the app's documented assumptions, not values validated
on the installed van.
"""

import math

import pytest


def sensor_values(pitch, roll):
    """Decoded sensor values that produce the given displayed pitch/roll."""
    return {"roll": pitch, "pitch": roll, "yaw": 0.0}


def test_level_van_needs_no_lift(app):
    heights = app.corner_lift_heights(sensor_values(0.0, 0.0))
    assert heights == {corner: 0.0 for corner in app.CORNER_ORDER}


def test_no_data_has_no_estimate(app):
    assert app.corner_lift_heights(None) is None


def test_front_high_pitch_lifts_both_rear_corners(app):
    heights = app.corner_lift_heights(sensor_values(1.0, 0.0))
    expected = app.WHEELBASE_MM * math.tan(math.radians(1.0)) / 10.0
    assert heights["FRONT LEFT"] == pytest.approx(0.0)
    assert heights["FRONT RIGHT"] == pytest.approx(0.0)
    assert heights["REAR LEFT"] == pytest.approx(expected)
    assert heights["REAR RIGHT"] == pytest.approx(expected)


def test_left_high_roll_lifts_right_side_by_track_width(app):
    heights = app.corner_lift_heights(sensor_values(0.0, 1.0))
    slope = math.tan(math.radians(1.0))
    assert heights["FRONT LEFT"] == pytest.approx(0.0)
    assert heights["FRONT RIGHT"] == pytest.approx(app.FRONT_TRACK_MM * slope / 10.0)
    assert heights["REAR RIGHT"] == pytest.approx(
        (app.FRONT_TRACK_MM + app.REAR_TRACK_MM) / 2.0 * slope / 10.0
    )
    # Different front/rear track widths leave a tiny lift at the rear left.
    assert heights["REAR LEFT"] == pytest.approx(
        (app.FRONT_TRACK_MM - app.REAR_TRACK_MM) / 2.0 * slope / 10.0
    )


def test_highest_corner_is_the_reference(app):
    heights = app.corner_lift_heights(sensor_values(-2.3, 1.7))
    assert min(heights.values()) == 0.0
    assert all(height >= 0.0 for height in heights.values())


def test_two_wedge_view_lists_two_largest_lifts(app):
    app.corner_view = 0
    content = app.corner_page_content(sensor_values(1.0, 0.5))
    heights = app.corner_lift_heights(sensor_values(1.0, 0.5))
    ranked = sorted(heights.items(), key=lambda item: item[1], reverse=True)
    assert content == tuple((label, "%.1f cm" % height) for label, height in ranked[:2])


def test_two_wedge_view_reports_level_below_threshold(app):
    app.corner_view = 0
    assert app.corner_page_content(sensor_values(0.0, 0.0)) == app.LEVEL_CONTENT


def test_two_wedge_view_without_data(app):
    app.corner_view = 0
    assert app.corner_page_content(None) == (("--", "--.- cm"), ("--", "--.- cm"))


def test_four_corner_view_keeps_fixed_order(app):
    app.corner_view = 1
    content = app.corner_page_content(sensor_values(-1.0, 0.0))
    assert [label for label, _ in content] == list(app.CORNER_ORDER)
    assert content[0][1] == "%.1f cm" % (app.WHEELBASE_MM * math.tan(math.radians(1.0)) / 10)
    assert app.corner_page_content(None)[0] == ("FRONT LEFT", "--.- cm")
