"""Compare the fake panel with reference images in tests/golden/."""

import pathlib

import pytest

from support.png import read_png, screen_rgb, write_png

GOLDEN = pathlib.Path(__file__).resolve().parents[1] / "golden"
ACTUAL = GOLDEN / "_actual"


def assert_matches_golden(request, name, pixels):
    """Fail unless pixels match tests/golden/<name>.png.

    With --update-golden the image is (re)written instead. On a mismatch the
    actual image is saved to tests/golden/_actual/<name>.png.
    """
    actual = screen_rgb(pixels)
    path = GOLDEN / (name + ".png")
    if request.config.getoption("--update-golden"):
        GOLDEN.mkdir(exist_ok=True)
        write_png(path, actual)
        return
    if not path.exists():
        pytest.fail("missing %s; run tools/test.sh --update-golden" % path.name)

    expected = read_png(path)
    if actual == expected:
        return
    ACTUAL.mkdir(parents=True, exist_ok=True)
    write_png(ACTUAL / path.name, actual)
    differing = sum(
        1
        for actual_row, expected_row in zip(actual, expected)
        for x in range(0, len(actual_row), 3)
        if actual_row[x:x + 3] != expected_row[x:x + 3]
    )
    pytest.fail(
        "%s differs in %d pixels; see tests/golden/_actual/%s" % (path.name, differing, path.name)
    )
