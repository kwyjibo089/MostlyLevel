"""Test setup: run the MicroPython sources from src/ under CPython.

The directory tests/fakes provides stand-ins for the firmware modules
(`machine`, `bluetooth`, `framebuf`); support.clock adds MicroPython's ticks
API to `time`. Nothing here talks to real hardware.
"""

import pathlib
import sys

import pytest

TESTS = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(TESTS / "fakes"), str(TESTS.parent / "src"), str(TESTS)]

import fakehw  # noqa: E402
from support import clock  # noqa: E402
from support.app import fresh_import, load_app  # noqa: E402

clock.install()


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        help="rewrite tests/golden/*.png from the current rendering",
    )


@pytest.fixture(autouse=True)
def fresh_hardware():
    """Give every test a blank panel, no touch, no BLE, and time zero."""
    fakehw.reset()
    clock.clock.now_ms = 0
    yield


@pytest.fixture
def panel():
    return fakehw.panel


@pytest.fixture
def touch():
    return fakehw.touch


@pytest.fixture
def fake_clock():
    return clock.clock


@pytest.fixture
def reference_file(tmp_path):
    return tmp_path / "level_reference.cfg"


@pytest.fixture
def app(reference_file):
    """The dashboard after setup(), with no touch controller fitted."""
    return load_app(reference_file)


@pytest.fixture
def app_with_touch(reference_file):
    """The dashboard after setup(), with the FT5x06 controller present."""
    fakehw.touch.present = True
    return load_app(reference_file)


@pytest.fixture
def import_fresh():
    return fresh_import
