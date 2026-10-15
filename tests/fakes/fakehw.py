"""Shared state behind the fake MicroPython hardware modules.

The fake `machine`, `bluetooth`, and `framebuf` modules in this directory
stand in for the ESP32 firmware when the app runs under CPython. `Panel`
decodes the ILI9341 command stream the driver sends over SPI into a 240 x 320
RGB565 pixel array, so tests can check exactly what the LCD would show.
"""

import sys
from array import array

WIDTH = 240
HEIGHT = 320

CASET = 0x2A
PASET = 0x2B
RAMWR = 0x2C


class Panel:
    """ILI9341 model covering the commands the app uses to draw."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.pixels = array("H", bytes(WIDTH * HEIGHT * 2))
        self.command = None
        self.args = bytearray()
        self.columns = (0, WIDTH - 1)
        self.rows = (0, HEIGHT - 1)
        self.position = 0
        self.pending = b""
        self.commands = []
        self.pixel_bytes = 0
        self.transfers = 0

    def write(self, data, dc):
        data = bytes(data)
        self.transfers += 1
        if not dc:
            self.command = data[0]
            self.commands.append(self.command)
            self.args = bytearray()
            if self.command == RAMWR:
                self.position = 0
                self.pending = b""
            return

        if self.command in (CASET, PASET):
            self.args += data
            if len(self.args) >= 4:
                start = (self.args[0] << 8) | self.args[1]
                end = (self.args[2] << 8) | self.args[3]
                if self.command == CASET:
                    self.columns = (start, end)
                else:
                    self.rows = (start, end)
        elif self.command == RAMWR:
            self._write_memory(data)

    def _write_memory(self, data):
        self.pixel_bytes += len(data)
        data = self.pending + data
        usable = len(data) - len(data) % 2
        self.pending = data[usable:]
        values = array("H", data[:usable])
        if sys.byteorder == "little":
            values.byteswap()  # The panel receives RGB565 high byte first.

        x0, x1 = self.columns
        y0, y1 = self.rows
        width = x1 - x0 + 1
        index = 0
        while index < len(values):
            row, column = divmod(self.position, width)
            y = y0 + row
            if y > y1:
                raise AssertionError("pixel data overflows the address window")
            count = min(width - column, len(values) - index)
            start = y * WIDTH + x0 + column
            self.pixels[start:start + count] = values[index:index + count]
            index += count
            self.position += count

    def pixel(self, x, y):
        return self.pixels[y * WIDTH + x]

    def rows_slice(self, top, bottom=HEIGHT):
        return self.pixels[top * WIDTH:bottom * WIDTH]


class TouchController:
    """FT5x06-style register reads for one optional touch point."""

    def __init__(self):
        self.present = False
        self.point = None

    def read(self, register, count):
        if self.point is None:
            data = bytes(5)
        else:
            x, y = self.point
            data = bytes((1, (x >> 8) & 0x0F, x & 0xFF, (y >> 8) & 0x0F, y & 0xFF))
        return data[:count]


panel = Panel()
pins = {}
touch = TouchController()
ble = None


def reset():
    global ble
    panel.reset()
    pins.clear()
    touch.__init__()
    ble = None
