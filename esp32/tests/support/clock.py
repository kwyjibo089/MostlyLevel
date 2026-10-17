"""Controllable stand-in for MicroPython's time.ticks_* functions."""

import time


class FakeClock:
    def __init__(self):
        self.now_ms = 0

    def ticks_ms(self):
        return self.now_ms

    @staticmethod
    def ticks_diff(end, start):
        return end - start

    def sleep_ms(self, ms):
        self.now_ms += ms

    def advance(self, ms):
        self.now_ms += ms


clock = FakeClock()


def install():
    """Add MicroPython's ticks API to CPython's time module."""
    time.ticks_ms = clock.ticks_ms
    time.ticks_diff = clock.ticks_diff
    time.sleep_ms = clock.sleep_ms
