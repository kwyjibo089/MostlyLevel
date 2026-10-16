BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
CYAN = 0x07FF
YELLOW = 0xFFE0
GREY = 0x8410

# 5x7 font, likely derived from Adafruit GFX glcdfont.c (BSD license,
# Copyright (c) 2012 Adafruit Industries); see THIRD_PARTY_NOTICES.md.
FONT = {
    ' ': (0, 0, 0, 0, 0),
    '-': (8, 8, 8, 8, 8),
    '+': (8, 8, 62, 8, 8),
    '.': (0, 96, 96, 0, 0),
    ':': (0, 54, 54, 0, 0),
    '%': (99, 19, 8, 100, 99),
    '°': (6, 9, 9, 6, 0),
    '0': (62, 81, 73, 69, 62),
    '1': (0, 66, 127, 64, 0),
    '2': (66, 97, 81, 73, 70),
    '3': (33, 65, 69, 75, 49),
    '4': (24, 20, 18, 127, 16),
    '5': (39, 69, 69, 69, 57),
    '6': (60, 74, 73, 73, 48),
    '7': (1, 113, 9, 5, 3),
    '8': (54, 73, 73, 73, 54),
    '9': (6, 73, 73, 41, 30),
    'A': (126, 17, 17, 17, 126),
    'B': (127, 73, 73, 73, 54),
    'C': (62, 65, 65, 65, 34),
    'D': (127, 65, 65, 34, 28),
    'E': (127, 73, 73, 73, 65),
    'F': (127, 9, 9, 9, 1),
    'G': (62, 65, 73, 73, 122),
    'H': (127, 8, 8, 8, 127),
    'I': (0, 65, 127, 65, 0),
    'J': (32, 64, 65, 63, 1),
    'K': (127, 8, 20, 34, 65),
    'L': (127, 64, 64, 64, 64),
    'M': (127, 2, 12, 2, 127),
    'N': (127, 4, 8, 16, 127),
    'O': (62, 65, 65, 65, 62),
    'P': (127, 9, 9, 9, 6),
    'Q': (62, 65, 81, 33, 94),
    'R': (127, 9, 25, 41, 70),
    'S': (70, 73, 73, 73, 49),
    'T': (1, 1, 127, 1, 1),
    'U': (63, 64, 64, 64, 63),
    'V': (31, 32, 64, 32, 31),
    'W': (63, 64, 56, 64, 63),
    'X': (99, 20, 8, 20, 99),
    'Y': (7, 8, 112, 8, 7),
    'Z': (97, 81, 73, 69, 67),
    ',': (0, 224, 96, 0, 0),
}

# Accented capitals for the German, French, and Spanish texts: a full-height
# FONT capital plus a mark. Marks above sit in rows -3 and -2 (above the
# text line, one row clear of the letter); the cedilla sits in row 7. Marks
# are (column, row, width, height) rects. MostlyLevel's own glyphs, not
# derived from Adafruit's font.
ACCENT_MARKS = {
    'umlaut': ((1, -2, 1, 1), (3, -2, 1, 1)),
    'acute': ((3, -3, 1, 1), (2, -2, 1, 1)),
    'grave': ((1, -3, 1, 1), (2, -2, 1, 1)),
    'circumflex': ((2, -3, 1, 1), (1, -2, 1, 1), (3, -2, 1, 1)),
    'tilde': ((1, -3, 2, 1), (4, -3, 1, 1), (0, -2, 1, 1), (3, -2, 1, 1)),
    'cedilla': ((2, 7, 2, 1),),
}
ACCENTED = {
    'Ä': ('A', 'umlaut'),
    'Ö': ('O', 'umlaut'),
    'Ü': ('U', 'umlaut'),
    'À': ('A', 'grave'),
    'Á': ('A', 'acute'),
    'É': ('E', 'acute'),
    'È': ('E', 'grave'),
    'Ê': ('E', 'circumflex'),
    'Í': ('I', 'acute'),
    'Ó': ('O', 'acute'),
    'Ú': ('U', 'acute'),
    'Ñ': ('N', 'tilde'),
    'Ç': ('C', 'cedilla'),
}

# Filled rects per character, worked out on first use.
GLYPH_RECTS = {}


def merge_runs(lines):
    """Merge identical runs on consecutive lines into taller rects.

    `lines` holds, per line, a list of (start, length) runs. Returns
    (start, line, length, line_count) tuples.
    """
    rects = []
    open_runs = {}
    for line, runs in enumerate(lines):
        still_open = {}
        for run in runs:
            first_line = open_runs.pop(run, line)
            still_open[run] = first_line
        for (start, length), first_line in open_runs.items():
            rects.append((start, first_line, length, line - first_line))
        open_runs = still_open
    for (start, length), first_line in open_runs.items():
        rects.append((start, first_line, length, len(lines) - first_line))
    return rects


def bit_runs(bits, count):
    """Return (start, length) runs of set bits among the lowest `count`."""
    runs = []
    start = None
    for index in range(count + 1):
        if index < count and bits & (1 << index):
            if start is None:
                start = index
        elif start is not None:
            runs.append((start, index - start))
            start = None
    return runs


def glyph_rects(glyph):
    """Return a glyph's set pixels as few (column, row, width, height) rects.

    Merges either horizontal runs over rows or vertical runs over columns,
    whichever gives fewer rects; both cover exactly the same pixels.
    """
    row_lines = []
    for row in range(8):
        bits = 0
        for col, column_bits in enumerate(glyph):
            if column_bits & (1 << row):
                bits |= 1 << col
        row_lines.append(bit_runs(bits, len(glyph)))
    by_rows = merge_runs(row_lines)

    by_columns = [
        (col, row, width, height)
        for row, col, height, width in merge_runs(
            [bit_runs(column_bits, 8) for column_bits in glyph]
        )
    ]
    return tuple(by_columns if len(by_columns) < len(by_rows) else by_rows)


def char_rects(char):
    """Return the rects that draw `char`, or None if the font lacks it."""
    if char in ACCENTED:
        base, mark = ACCENTED[char]
        return glyph_rects(FONT[base]) + ACCENT_MARKS[mark]
    glyph = FONT.get(char)
    return None if glyph is None else glyph_rects(glyph)


class Graphics:
    def __init__(self, lcd):
        self.lcd = lcd

    def clear(self, colour=BLACK):
        self.lcd.fill(colour)

    def pixel(self, x, y, colour):
        self.lcd.pixel(x, y, colour)

    def hline(self, x, y, w, colour):
        self.lcd.hline(x, y, w, colour)

    def vline(self, x, y, h, colour):
        self.lcd.vline(x, y, h, colour)

    def rect(self, x, y, w, h, colour):
        self.hline(x, y, w, colour)
        self.hline(x, y + h - 1, w, colour)
        self.vline(x, y, h, colour)
        self.vline(x + w - 1, y, h, colour)

    def fill_rect(self, x, y, w, h, colour):
        self.lcd.fill_rect(x, y, w, h, colour)

    def text(self, x, y, message, colour=WHITE, scale=1):
        cursor_x = x

        fill_rect = self.fill_rect

        for char in str(message).upper():
            rects = GLYPH_RECTS.get(char)
            if rects is None:
                rects = char_rects(char)
                if rects is None:
                    cursor_x += 6 * scale
                    continue
                GLYPH_RECTS[char] = rects

            for col, row, width, height in rects:
                fill_rect(
                    cursor_x + col * scale,
                    y + row * scale,
                    width * scale,
                    height * scale,
                    colour,
                )

            cursor_x += 6 * scale
