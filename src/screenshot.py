"""Tiled framebuffer and BMP writer for dashboard screenshots."""

import framebuf
import struct


class TileFramebufferDisplay:
    """Drawing adapter for a horizontal strip of the full display."""

    def __init__(self, width, height, top):
        self.width = width
        self.height = height
        self.top = top
        self.buffer = bytearray(width * height * 2)
        self.framebuffer = framebuf.FrameBuffer(
            self.buffer, width, height, framebuf.RGB565
        )

    def fill(self, colour):
        self.framebuffer.fill(colour)

    def pixel(self, x, y, colour):
        if 0 <= x < self.width and self.top <= y < self.top + self.height:
            self.framebuffer.pixel(x, y - self.top, colour)

    def hline(self, x, y, width, colour):
        if self.top <= y < self.top + self.height:
            x0 = max(0, x)
            x1 = min(self.width, x + width)
            if x0 < x1:
                self.framebuffer.hline(x0, y - self.top, x1 - x0, colour)

    def vline(self, x, y, height, colour):
        y0 = max(self.top, y)
        y1 = min(self.top + self.height, y + height)
        if 0 <= x < self.width and y0 < y1:
            self.framebuffer.vline(x, y0 - self.top, y1 - y0, colour)

    def fill_rect(self, x, y, width, height, colour):
        x0 = max(0, x)
        x1 = min(self.width, x + width)
        y0 = max(self.top, y)
        y1 = min(self.top + self.height, y + height)
        if x0 < x1 and y0 < y1:
            self.framebuffer.fill_rect(
                x0, y0 - self.top, x1 - x0, y1 - y0, colour
            )


def write_bmp_header(image_file, width, height):
    row_size = width * 3
    image_size = row_size * height
    file_size = 54 + image_size
    bmp_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, 54)
    dib_header = struct.pack(
        "<IiiHHIIiiII",
        40,
        width,
        -height,
        1,
        24,
        0,
        image_size,
        2835,
        2835,
        0,
        0,
    )
    image_file.write(bmp_header)
    image_file.write(dib_header)


def write_bmp_tile(image_file, rgb565_buffer, width, tile_height):
    """Convert and write top-down RGB565 rows as 24-bit BMP pixels."""
    row = bytearray(width * 3)

    for y in range(tile_height):
        source_offset = y * width * 2
        for x in range(width):
            source = source_offset + x * 2
            colour = rgb565_buffer[source] | (rgb565_buffer[source + 1] << 8)

            red5 = (colour >> 11) & 0x1F
            green6 = (colour >> 5) & 0x3F
            blue5 = colour & 0x1F
            target = x * 3
            row[target] = (blue5 << 3) | (blue5 >> 2)
            row[target + 1] = (green6 << 2) | (green6 >> 4)
            row[target + 2] = (red5 << 3) | (red5 >> 2)

        image_file.write(row)
