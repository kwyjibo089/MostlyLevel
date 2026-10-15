"""Fake MicroPython `framebuf` module (RGB565 only, as the app uses it).

Pixels are stored little-endian like the real module, so code that
byte-swaps colours for the LCD is exercised as on the device.
"""

RGB565 = 1


class FrameBuffer:
    def __init__(self, buffer, width, height, fmt):
        if fmt != RGB565:
            raise ValueError("only RGB565 is supported by this fake")
        self.buffer = buffer
        self.width = width
        self.height = height

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes((colour & 0xFF, (colour >> 8) & 0xFF)) * (x1 - x0)
        for row_y in range(y0, y1):
            offset = (row_y * self.width + x0) * 2
            self.buffer[offset:offset + len(row)] = row

    def fill(self, colour):
        self.fill_rect(0, 0, self.width, self.height, colour)

    def pixel(self, x, y, colour=None):
        if colour is None:
            offset = (y * self.width + x) * 2
            return self.buffer[offset] | (self.buffer[offset + 1] << 8)
        self.fill_rect(x, y, 1, 1, colour)
        return None

    def hline(self, x, y, w, colour):
        self.fill_rect(x, y, w, 1, colour)

    def vline(self, x, y, h, colour):
        self.fill_rect(x, y, 1, h, colour)
