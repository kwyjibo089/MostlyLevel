from ili9341 import ILI9341

BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
CYAN = 0x07FF
YELLOW = 0xFFE0
GREY = 0x8410

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
}


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

        for char in str(message).upper():
            glyph = FONT.get(char)

            if glyph is None:
                cursor_x += 6 * scale
                continue

            for row in range(8):
                col = 0
                while col < len(glyph):
                    if not glyph[col] & (1 << row):
                        col += 1
                        continue

                    run_start = col
                    col += 1
                    while col < len(glyph) and glyph[col] & (1 << row):
                        col += 1

                    self.fill_rect(
                        cursor_x + run_start * scale,
                        y + row * scale,
                        (col - run_start) * scale,
                        scale,
                        colour,
                    )

            cursor_x += 6 * scale
