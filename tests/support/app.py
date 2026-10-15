"""Load the dashboard app against the fake hardware."""

import importlib
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
SRC_MODULES = (
    "config",
    "graphics",
    "compositor",
    "ili9341",
    "ble_read",
    "touch",
    "screenshot",
    "app",
    "main",
)


def fresh_import(name):
    """Import a src module with all src modules reloaded from scratch."""
    for module in SRC_MODULES:
        sys.modules.pop(module, None)
    return importlib.import_module(name)


class AppNamespace:
    """Attribute access to the globals of an exec'd main.py."""

    def __init__(self, namespace):
        object.__setattr__(self, "_ns", namespace)

    def __getattr__(self, name):
        try:
            return self._ns[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self._ns[name] = value


def load_app():
    """Run main.py's setup code (everything before its endless loop)."""
    for module in SRC_MODULES:
        sys.modules.pop(module, None)
    path = SRC / "main.py"
    head, marker, _ = path.read_text().partition("\nsensor.start()")
    if not marker:
        raise AssertionError("main.py no longer has the expected sensor.start() line")
    namespace = {"__name__": "main"}
    exec(compile(head, str(path), "exec"), namespace)
    return AppNamespace(namespace)
