"""Fake MicroPython `framebuf` module, covering what the app uses.

RGB565 pixels are stored little-endian in the given buffer like the real
module, so code that byte-swaps colours for the LCD is exercised as on the
device. MONO_HLSB and GS4_HMSB (palette-indexed pictures) unpack the buffer once
into a list, using the bit order checked on the board (GS4_HMSB: high
nibble is the left pixel; MONO_HLSB: most significant bit is leftmost),
and later writes go to that list.

blit() follows MicroPython 1.29 as checked on the board: a source pixel is
mapped through the palette first and then skipped if it equals `key`.
"""

RGB565 = 1
MONO_HLSB = 3
GS4_HMSB = 2


class FrameBuffer:
    def __init__(self, buffer, width, height, fmt):
        if fmt not in (RGB565, MONO_HLSB, GS4_HMSB):
            raise ValueError("format not supported by this fake")
        self.buffer = buffer
        self.width = width
        self.height = height
        self.format = fmt
        if fmt == GS4_HMSB:
            stride = (width + 1) // 2
            self.values = [
                buffer[y * stride + x // 2] >> (0 if x % 2 else 4) & 15
                for y in range(height)
                for x in range(width)
            ]
        elif fmt == MONO_HLSB:
            stride = (width + 7) // 8
            self.values = [
                buffer[y * stride + x // 8] >> (7 - x % 8) & 1
                for y in range(height)
                for x in range(width)
            ]

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        if self.format != RGB565:
            limit = 1 if self.format == MONO_HLSB else 15
            for row_y in range(y0, y1):
                for row_x in range(x0, x1):
                    self.values[row_y * self.width + row_x] = colour & limit
            return
        row = bytes((colour & 0xFF, (colour >> 8) & 0xFF)) * (x1 - x0)
        for row_y in range(y0, y1):
            offset = (row_y * self.width + x0) * 2
            self.buffer[offset:offset + len(row)] = row

    def fill(self, colour):
        self.fill_rect(0, 0, self.width, self.height, colour)

    def pixel(self, x, y, colour=None):
        if colour is None:
            if self.format != RGB565:
                return self.values[y * self.width + x]
            offset = (y * self.width + x) * 2
            return self.buffer[offset] | (self.buffer[offset + 1] << 8)
        self.fill_rect(x, y, 1, 1, colour)
        return None

    def hline(self, x, y, w, colour):
        self.fill_rect(x, y, w, 1, colour)

    def vline(self, x, y, h, colour):
        self.fill_rect(x, y, 1, h, colour)

    def blit(self, source, x, y, key=-1, palette=None):
        for source_y in range(source.height):
            target_y = y + source_y
            if not 0 <= target_y < self.height:
                continue
            for source_x in range(source.width):
                target_x = x + source_x
                if not 0 <= target_x < self.width:
                    continue
                colour = source.pixel(source_x, source_y)
                if palette is not None:
                    colour = palette.pixel(colour, 0)
                if colour != key:
                    self.pixel(target_x, target_y, colour)
