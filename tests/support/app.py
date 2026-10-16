"""Load the dashboard app against the fake hardware."""

import importlib
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parents[2] / "src"
SRC_MODULES = (
    "config",
    "i18n",
    "graphics",
    "compositor",
    "van_sprite",
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


def load_app(reference_file):
    """Import app.py fresh and run setup() against the fake hardware.

    reference_file replaces /level_reference.cfg so tests never touch the
    real filesystem root.
    """
    app = fresh_import("app")
    app.LEVEL_REFERENCE_FILE = str(reference_file)
    app.i18n.TEXT_DIR = str(SRC) + "/"
    app.i18n.LANGUAGE_FILE = str(reference_file.parent / "language.cfg")
    app.setup()
    return app
