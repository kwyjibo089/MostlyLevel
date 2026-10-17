"""Off-screen strip compositing for flicker-free full-page redraws.

Drawing code records filled rectangles into a DisplayList. StripRenderer then
paints the list into one small RGB565 strip buffer at a time and sends each
finished strip to the LCD in a single transfer, so every pixel is written once
with its final colour. Strips whose rectangles did not change are skipped.
"""

import framebuf


def swap_bytes(colour):
    """framebuf stores RGB565 little-endian; the ILI9341 wants high byte first."""
    return ((colour & 0xFF) << 8) | (colour >> 8)


# Shared (palette, transparent key) per colour list and byte order.
PALETTES = {}


class Bitmap:
    """A fixed picture with transparent pixels, drawn with one framebuf.blit.

    Pixels hold indices into `colours` (RGB565); index 0 is transparent. Up
    to 2 colours use 1 bit per pixel (MONO_HLSB), up to 16 use 4 (GS4_HMSB).
    A display-list item whose colour is a Bitmap stands for the whole picture
    at that position, instead of many small rects.
    """

    def __init__(self, width, height, colours, pixels=None, buffer=None):
        """`pixels`, if given, are packed MONO_HLSB or GS4_HMSB rows to copy.
        `buffer`, if given, is used as it is (it may be larger), so pictures
        redrawn every frame need no new allocation."""
        if len(colours) > 16:
            raise ValueError("a Bitmap holds at most 15 colours")
        self.width = width
        self.height = height
        self.colours = colours
        if len(colours) <= 2:
            fmt = framebuf.MONO_HLSB
            size = (width + 7) // 8 * height
        else:
            fmt = framebuf.GS4_HMSB
            size = (width + 1) // 2 * height
        if buffer is not None:
            data = buffer
        elif pixels is not None:
            data = bytearray(pixels)
        else:
            data = bytearray(size)
        self.framebuffer = framebuf.FrameBuffer(data, width, height, fmt)
        self.rect_cache = None
        # The shared palettes, looked up on first use (per byte order).
        self.swapped_palette = None
        self.native_palette = None

    def fill_rect(self, x, y, w, h, colour):
        self.framebuffer.fill_rect(x, y, w, h, self.colours.index(colour))

    def palette(self, swapped):
        """Return (palette, key) for blitting onto a buffer of that byte order.

        Bitmaps with the same colours share one palette, which matters for
        layers split into many tiles.
        """
        cache_key = (tuple(self.colours), swapped)
        if cache_key not in PALETTES:
            values = [swap_bytes(c) if swapped else c for c in self.colours[1:]]
            key = 1
            while key in values:
                key += 1
            count = len(self.colours)
            palette = framebuf.FrameBuffer(bytearray(count * 2), count, 1, framebuf.RGB565)
            palette.pixel(0, 0, key)
            for index, value in enumerate(values):
                palette.pixel(index + 1, 0, value)
            PALETTES[cache_key] = (palette, key)
        return PALETTES[cache_key]

    def blit_into(self, target, x, y, swapped):
        if swapped:
            if self.swapped_palette is None:
                self.swapped_palette = self.palette(True)
            palette, key = self.swapped_palette
        else:
            if self.native_palette is None:
                self.native_palette = self.palette(False)
            palette, key = self.native_palette
        target.blit(self.framebuffer, x, y, key, palette)

    def rects(self):
        """Return the picture as (x, y, w, 1, colour) row runs; for targets
        without framebuf.blit. Worked out once, on first use."""
        if self.rect_cache is None:
            rects = []
            pixel = self.framebuffer.pixel
            for y in range(self.height):
                x = 0
                while x < self.width:
                    index = pixel(x, y)
                    start = x
                    while x < self.width and pixel(x, y) == index:
                        x += 1
                    if index:
                        rects.append((start, y, x - start, 1, self.colours[index]))
            self.rect_cache = rects
        return self.rect_cache


class DisplayList:
    """LCD stand-in for Graphics that records (x, y, w, h, colour) fills."""

    def __init__(self):
        self.items = []

    def bitmap(self, x, y, picture):
        self.items.append((x, y, picture.width, picture.height, picture))

    def fill_rect(self, x, y, w, h, colour):
        if w > 0 and h > 0:
            self.items.append((x, y, w, h, colour))

    def fill(self, colour):
        self.fill_rect(0, 0, 240, 320, colour)

    def pixel(self, x, y, colour):
        self.fill_rect(x, y, 1, 1, colour)

    def hline(self, x, y, w, colour):
        self.fill_rect(x, y, w, 1, colour)

    def vline(self, x, y, h, colour):
        self.fill_rect(x, y, 1, h, colour)


class StripRenderer:
    """Composite a display list into rows top..bottom-1 of the LCD."""

    def __init__(self, lcd, top, bottom, strip_rows):
        self.lcd = lcd
        self.top = top
        self.bottom = bottom
        self.rows = strip_rows
        self.width = lcd.WIDTH
        self.buffer = bytearray(self.width * strip_rows * 2)
        self.view = memoryview(self.buffer)
        self.framebuffer = framebuf.FrameBuffer(
            self.buffer, self.width, strip_rows, framebuf.RGB565
        )
        self.count = (bottom - top + strip_rows - 1) // strip_rows
        self.previous = [None] * self.count

    def invalidate(self):
        """Forget what is on screen, e.g. after drawing over the region."""
        self.previous = [None] * self.count

    def render(self, items):
        top = self.top
        rows = self.rows
        last = self.count - 1
        buckets = [[] for _ in range(self.count)]
        for item in items:
            y = item[1] - top
            first = y // rows
            end = (y + item[3] - 1) // rows
            if first == end:
                # Most rects (text, ladder) lie within one strip.
                if 0 <= first <= last:
                    buckets[first].append(item)
                continue
            if end < 0 or first > last:
                continue
            if first < 0:
                first = 0
            if end > last:
                end = last
            while first <= end:
                buckets[first].append(item)
                first += 1

        framebuffer = self.framebuffer
        for index in range(self.count):
            bucket = buckets[index]
            if bucket == self.previous[index]:
                continue

            strip_top = top + index * rows
            strip_rows = min(rows, self.bottom - strip_top)
            framebuffer.fill(0)
            for x, y, w, h, colour in bucket:
                if isinstance(colour, int):
                    # framebuf stores RGB565 little-endian; the ILI9341
                    # expects the high byte first, so swap when drawing.
                    framebuffer.fill_rect(
                        x,
                        y - strip_top,
                        w,
                        h,
                        ((colour & 0xFF) << 8) | (colour >> 8),
                    )
                else:
                    colour.blit_into(framebuffer, x, y - strip_top, True)
            self.lcd.blit(
                0,
                strip_top,
                self.width,
                strip_rows,
                self.view[:self.width * strip_rows * 2],
            )
            self.previous[index] = bucket

    def render_area(self, x, y, w, h, items):
        """Composite items into one small area and send it in one transfer.

        The area must fit in the strip buffer. Strips it overlaps are marked
        unknown so the next render() repaints them.
        """
        framebuffer = framebuf.FrameBuffer(self.buffer, w, h, framebuf.RGB565)
        framebuffer.fill(0)
        for item_x, item_y, item_w, item_h, colour in items:
            if isinstance(colour, int):
                framebuffer.fill_rect(
                    item_x - x,
                    item_y - y,
                    item_w,
                    item_h,
                    ((colour & 0xFF) << 8) | (colour >> 8),
                )
            else:
                colour.blit_into(framebuffer, item_x - x, item_y - y, True)
        self.lcd.blit(x, y, w, h, self.view[:w * h * 2])
        first = max(0, (y - self.top) // self.rows)
        last = min(self.count - 1, (y + h - 1 - self.top) // self.rows)
        for index in range(first, last + 1):
            self.previous[index] = None
