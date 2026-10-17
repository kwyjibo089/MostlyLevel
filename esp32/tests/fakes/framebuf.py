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

    def line(self, x0, y0, x1, y1, colour):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                self.pixel(x0, y0, colour)
            if x0 == x1 and y0 == y1:
                return
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def ellipse(self, x, y, xr, yr, colour, fill=False):
        """Filled: pixels inside the ellipse; outline: its edge pixels."""
        def inside(px, py):
            return (px * px) * (yr * yr) + (py * py) * (xr * xr) <= (xr * xr) * (yr * yr)

        for py in range(-yr, yr + 1):
            for px in range(-xr, xr + 1):
                if not inside(px, py):
                    continue
                edge = not all(
                    inside(px + dx, py + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                if (fill or edge) and 0 <= x + px < self.width and 0 <= y + py < self.height:
                    self.pixel(x + px, y + py, colour)

    def poly(self, x, y, coords, colour, fill=False):
        """MicroPython's scanline fill: integer rows, crossings rounded."""
        points = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
        if not fill:
            for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
                self.line(x + x0, y + y0, x + x1, y + y1, colour)
            return
        rows = [py for _, py in points]
        for row in range(min(rows), max(rows) + 1):
            nodes = []
            for (px1, py1), (px2, py2) in zip(points, points[1:] + points[:1]):
                if py1 != py2 and ((py1 > row >= py2) or (py1 <= row < py2)):
                    node = 32 * px1 + 32 * (px2 - px1) * (row - py1) / (py2 - py1) + 16
                    nodes.append(int(node / 32))
                elif row == max(py1, py2):
                    if py1 < py2:
                        self.fill_rect(x + px2, y + py2, 1, 1, colour)
                    elif py2 < py1:
                        self.fill_rect(x + px1, y + py1, 1, 1, colour)
                    else:
                        self.line(x + px1, y + py1, x + px2, y + py2, colour)
            nodes.sort()
            for left, right in zip(nodes[::2], nodes[1::2]):
                self.fill_rect(x + left, y + row, right - left + 1, 1, colour)
