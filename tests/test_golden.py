"""Reference-image tests for each page and state.

Each scene is rendered on the fake panel and compared pixel for pixel with
tests/golden/<scene>.png. After an intentional visual change, regenerate the
images with `tools/test.sh --update-golden` and review them in the diff.
On a mismatch the actual image is written to tests/golden/_actual/.
"""

import pathlib

import pytest
from support.png import read_png, screen_rgb, write_png

GOLDEN = pathlib.Path(__file__).resolve().parent / "golden"
ACTUAL = GOLDEN / "_actual"


def sensor_values(pitch, roll):
    return {"roll": pitch, "pitch": roll, "yaw": 0.0}


# name: (page, corner view, displayed pitch/roll or None, state, level frame)
SCENES = {
    "horizon_live": (0, 0, (3.7, -0.2), "LIVE", False),
    "horizon_level": (0, 0, (0.2, -0.1), "LIVE", True),
    "horizon_tilted": (0, 0, (-12.0, 18.0), "LIVE", False),
    "horizon_waiting": (0, 0, None, "SCANNING", False),
    "horizon_stale": (0, 0, (1.0, 1.0), "NO DATA", False),
    "levelling_wedges": (1, 0, (3.7, -0.2), "LIVE", False),
    "levelling_corners": (1, 1, (3.7, -0.2), "LIVE", False),
    "levelling_level": (1, 0, (0.05, 0.02), "LIVE", False),
}


@pytest.mark.parametrize("name", sorted(SCENES))
def test_scene_matches_golden(app, panel, request, name):
    page, view, attitude, state, level = SCENES[name]
    app.active_screen = page
    app.corner_view = view
    app.level_frame_active = level
    app.sensor.power_percent = 60
    values = None if attitude is None else sensor_values(*attitude)
    app.draw_dashboard(values, state)
    actual = screen_rgb(panel.pixels)

    path = GOLDEN / (name + ".png")
    if request.config.getoption("--update-golden"):
        GOLDEN.mkdir(exist_ok=True)
        write_png(path, actual)
        return
    if not path.exists():
        pytest.fail("missing %s; run tools/test.sh --update-golden" % path.name)

    expected = read_png(path)
    if actual != expected:
        ACTUAL.mkdir(parents=True, exist_ok=True)
        write_png(ACTUAL / path.name, actual)
        differing = sum(
            1
            for actual_row, expected_row in zip(actual, expected)
            for x in range(0, len(actual_row), 3)
            if actual_row[x:x + 3] != expected_row[x:x + 3]
        )
        pytest.fail(
            "%s differs in %d pixels; see tests/golden/_actual/%s"
            % (path.name, differing, path.name)
        )
