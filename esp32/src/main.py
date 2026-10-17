"""MostlyLevel entry point; MicroPython runs this file at startup.

The dashboard lives in app.py (deployed as app.mpy). save_screenshot is
imported here so it stays available in the REPL after Ctrl+C, and the
running app's objects are reachable as app.sensor, app.lcd, and so on.
"""

import app
from app import save_screenshot  # noqa: F401  (REPL helper)

app.run()
