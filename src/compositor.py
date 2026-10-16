"""Off-screen strip compositing for flicker-free full-page redraws.

Drawing code records filled rectangles into a DisplayList. StripRenderer then
paints the list into one small RGB565 strip buffer at a time and sends each
finished strip to the LCD in a single transfer, so every pixel is written once
with its final colour. Strips whose rectangles did not change are skipped.
"""

import framebuf


class DisplayList:
    """LCD stand-in for Graphics that records (x, y, w, h, colour) fills."""

    def __init__(self):
        self.items = []

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
            y = item[1]
            first = (y - top) // rows
            end = (y + item[3] - 1 - top) // rows
            if end < 0 or first > last:
                continue
            for index in range(max(0, first), min(last, end) + 1):
                buckets[index].append(item)

        framebuffer = self.framebuffer
        for index in range(self.count):
            bucket = buckets[index]
            if bucket == self.previous[index]:
                continue

            strip_top = top + index * rows
            strip_rows = min(rows, self.bottom - strip_top)
            framebuffer.fill(0)
            for x, y, w, h, colour in bucket:
                # framebuf stores RGB565 little-endian; the ILI9341 expects
                # the high byte first, so swap the bytes when drawing.
                framebuffer.fill_rect(
                    x,
                    y - strip_top,
                    w,
                    h,
                    ((colour & 0xFF) << 8) | (colour >> 8),
                )
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
            framebuffer.fill_rect(
                item_x - x,
                item_y - y,
                item_w,
                item_h,
                ((colour & 0xFF) << 8) | (colour >> 8),
            )
        self.lcd.blit(x, y, w, h, self.view[:w * h * 2])
        first = max(0, (y - self.top) // self.rows)
        last = min(self.count - 1, (y + h - 1 - self.top) // self.rows)
        for index in range(first, last + 1):
            self.previous[index] = None
