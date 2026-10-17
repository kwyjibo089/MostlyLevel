"""Sensor-to-vehicle axis mapping, level detection, and calibration."""

import pytest


def test_axis_mapping_matches_owner_observation(app):
    # The owner reported that lifting the front changes the decoded X/roll
    # channel and lifting the left changes the decoded Y/pitch channel, so
    # config.py swaps them. Change this test only with new hardware evidence.
    assert (app.DISPLAY_PITCH_SENSOR_KEY, app.DISPLAY_PITCH_SIGN) == ("roll", 1.0)
    assert (app.DISPLAY_ROLL_SENSOR_KEY, app.DISPLAY_ROLL_SIGN) == ("pitch", 1.0)


def test_vehicle_values_apply_mapping_and_level_reference(app):
    app.pitch_zero = 0.5
    app.roll_zero = -0.25
    display, pitch, roll = app.vehicle_values({"roll": 2.0, "pitch": 1.0, "yaw": 9.0})
    assert pitch == pytest.approx(1.5)
    assert roll == pytest.approx(1.25)
    assert display == {"pitch": pitch, "roll": roll}


def test_vehicle_values_without_data(app):
    assert app.vehicle_values(None) == (None, 0.0, 0.0)


@pytest.mark.parametrize(
    "pitch, roll, was_level, expected",
    [
        (0.5, -0.5, False, True),
        (0.6, 0.0, False, False),
        (0.6, 0.0, True, True),  # Hysteresis keeps the frame on up to 0.7°.
        (0.0, -0.7, True, True),
        (0.71, 0.0, True, False),
    ],
)
def test_level_frame_hysteresis(app, pitch, roll, was_level, expected):
    assert app.is_level(pitch, roll, was_level) is expected


def test_attitude_redraw_deadband(app):
    assert app.attitude_changed((1.0, 1.0), None)
    assert not app.attitude_changed((1.0, 1.0), (1.1, 0.9))
    assert app.attitude_changed((1.0, 1.0), (1.25, 1.0))


def test_calibration_is_saved_and_reloaded(app, tmp_path):
    reference = tmp_path / "level_reference.cfg"
    app.LEVEL_REFERENCE_FILE = str(reference)
    assert app.set_level_reference({"roll": 1.25, "pitch": -0.5, "yaw": 0.0})

    assert app.pitch_zero == pytest.approx(1.25)
    assert app.roll_zero == pytest.approx(-0.5)
    assert reference.read_text() == "1.25000\n-0.50000\n"
    assert app.load_level_reference() == (pytest.approx(1.25), pytest.approx(-0.5))
    _, pitch, roll = app.vehicle_values({"roll": 1.25, "pitch": -0.5})
    assert (pitch, roll) == (0.0, 0.0)


def test_calibration_needs_data(app):
    assert app.set_level_reference(None) is False


def test_unreadable_reference_falls_back_to_zero(app, tmp_path):
    reference = tmp_path / "level_reference.cfg"
    reference.write_text("not a number\n")
    app.LEVEL_REFERENCE_FILE = str(reference)
    assert app.load_level_reference() == (0.0, 0.0)
    app.LEVEL_REFERENCE_FILE = str(tmp_path / "missing.cfg")
    assert app.load_level_reference() == (0.0, 0.0)
