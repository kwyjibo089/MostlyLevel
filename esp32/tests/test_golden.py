"""Reference-image tests for each page and state.

Each scene is rendered on the fake panel and compared pixel for pixel with
tests/golden/<scene>.png. After an intentional visual change, regenerate the
images with `tools/test.sh --update-golden` and review them in the diff.
On a mismatch the actual image is written to tests/golden/_actual/.
"""

import pytest
from support.golden import assert_matches_golden


def sensor_values(pitch, roll):
    return {"roll": pitch, "pitch": roll, "yaw": 0.0}


# name: (page, sub-page, displayed pitch/roll or None, state, level frame).
# Page 0 is ATTITUDE (sub-pages VAN, HORIZON); page 1 is LEVELLING
# (sub-pages 2 WEDGES, 4 CORNERS).
SCENES = {
    "van_live": (0, 0, (3.7, -0.2), "LIVE", False),
    "van_level": (0, 0, (0.2, -0.1), "LIVE", True),
    "van_tilted": (0, 0, (-12.0, 18.0), "LIVE", False),
    "van_waiting": (0, 0, None, "SCANNING", False),
    "van_stale": (0, 0, (1.0, 1.0), "NO DATA", False),
    "horizon_live": (0, 1, (3.7, -0.2), "LIVE", False),
    "horizon_level": (0, 1, (0.2, -0.1), "LIVE", True),
    "horizon_tilted": (0, 1, (-12.0, 18.0), "LIVE", False),
    "horizon_stale": (0, 1, (1.0, 1.0), "NO DATA", False),
    "levelling_wedges": (1, 0, (3.7, -0.2), "LIVE", False),
    "levelling_corners": (1, 1, (3.7, -0.2), "LIVE", False),
    "levelling_level": (1, 0, (0.05, 0.02), "LIVE", False),
}


# Scenes repeated per language: every page and the longest texts.
LANGUAGE_SCENES = (
    "van_live",
    "horizon_stale",
    "levelling_wedges",
    "levelling_corners",
    "levelling_level",
)
CASES = [("en", name, name) for name in sorted(SCENES)] + [
    (code, name, "%s_%s" % (code, name))
    for code in ("de", "fr", "es")
    for name in LANGUAGE_SCENES
]


@pytest.mark.parametrize("code, name, golden", CASES, ids=[case[2] for case in CASES])
def test_scene_matches_golden(app, panel, request, code, name, golden):
    app.i18n.load(code)
    page, view, attitude, state, level = SCENES[name]
    app.active_screen = page
    if page == 0:
        app.attitude_view = view
    else:
        app.corner_view = view
    app.level_frame_active = level
    app.sensor.power_percent = 60
    values = None if attitude is None else sensor_values(*attitude)
    app.draw_dashboard(values, state)
    assert_matches_golden(request, golden, panel.pixels)
