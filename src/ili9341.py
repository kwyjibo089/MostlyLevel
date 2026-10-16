# Initialisation values in _init_display() come from Adafruit's ILI9341
# library (BSD license, Limor Fried / Adafruit Industries); see
# THIRD_PARTY_NOTICES.md.
from machine import Pin, SPI
import time
from config import (
    LCD_BACKLIGHT_PIN,
    LCD_CS_PIN,
    LCD_DC_PIN,
    LCD_FILL_CACHE_COLOURS,
    LCD_FILL_CHUNK_PIXELS,
    LCD_SPI_BAUDRATE,
    LCD_SPI_ID,
    LCD_SPI_MISO_PIN,
    LCD_SPI_MOSI_PIN,
    LCD_SPI_SCK_PIN,
)


class ILI9341:
    WIDTH = 240
    HEIGHT = 320

    def __init__(self):
        # Display connections for the ES3C28P board
        self.cs = Pin(LCD_CS_PIN, Pin.OUT, value=1)
        self.dc = Pin(LCD_DC_PIN, Pin.OUT, value=1)
        self.bl = Pin(LCD_BACKLIGHT_PIN, Pin.OUT, value=1)

        self.spi = SPI(
            LCD_SPI_ID,
            baudrate=LCD_SPI_BAUDRATE,
            polarity=0,
            phase=0,
            sck=Pin(LCD_SPI_SCK_PIN),
            mosi=Pin(LCD_SPI_MOSI_PIN),
            miso=Pin(LCD_SPI_MISO_PIN),
        )

        # Reused buffers keep the per-shape draw path free of allocations.
        self._window = bytearray(4)
        self._chunks = {}

        self._init_display()

    # ---------------------------------------------------------
    # Low-level display communication
    # ---------------------------------------------------------

    def _command(self, cmd, data=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytes([cmd]))

        if data is not None:
            self.dc(1)
            self.spi.write(data)

        self.cs(1)

    def _init_display(self):
        # Hardware reset is shared with the ESP32-S3 reset.
        time.sleep_ms(150)

        self._command(0x01)  # Software reset
        time.sleep_ms(150)

        self._command(0x28)  # Display off

        self._command(0xCF, bytes([0x00, 0xC1, 0x30]))
        self._command(0xED, bytes([0x64, 0x03, 0x12, 0x81]))
        self._command(0xE8, bytes([0x85, 0x00, 0x78]))
        self._command(0xCB, bytes([0x39, 0x2C, 0x00, 0x34, 0x02]))
        self._command(0xF7, bytes([0x20]))
        self._command(0xEA, bytes([0x00, 0x00]))

        self._command(0xC0, bytes([0x23]))
        self._command(0xC1, bytes([0x10]))
        self._command(0xC5, bytes([0x3E, 0x28]))
        self._command(0xC7, bytes([0x86]))

        # Memory access control:
        # MX + BGR; matches the existing working orientation.
        self._command(0x36, bytes([0x48]))

        self._command(0x3A, bytes([0x55]))  # RGB565
        self._command(0xB1, bytes([0x00, 0x18]))
        self._command(0xB6, bytes([0x08, 0x82, 0x27]))
        self._command(0xF2, bytes([0x00]))
        self._command(0x26, bytes([0x01]))

        # Positive gamma correction
        self._command(
            0xE0,
            bytes([
                0x0F, 0x31, 0x2B, 0x0C, 0x0E,
                0x08, 0x4E, 0xF1, 0x37, 0x07,
                0x10, 0x03, 0x0E, 0x09, 0x00
            ])
        )

        # Negative gamma correction
        self._command(
            0xE1,
            bytes([
                0x00, 0x0E, 0x14, 0x03, 0x11,
                0x07, 0x31, 0xC1, 0x48, 0x08,
                0x0F, 0x0C, 0x31, 0x36, 0x0F
            ])
        )

        self._command(0x11)  # Sleep out
        time.sleep_ms(120)

        self._command(0x21)  # Display inversion on (required by this board)

        self._command(0x29)  # Display on
        time.sleep_ms(20)

    # ---------------------------------------------------------
    # Drawing window and pixel data
    # Coordinates are inclusive: x0, y0, x1, y1.
    # ---------------------------------------------------------

    def _send_window(self, x0, y0, x1, y1):
        """Send the address-window commands; the caller holds CS low."""
        window = self._window
        self.dc(0)
        self.spi.write(b"\x2A")
        window[0] = (x0 >> 8) & 0xFF
        window[1] = x0 & 0xFF
        window[2] = (x1 >> 8) & 0xFF
        window[3] = x1 & 0xFF
        self.dc(1)
        self.spi.write(window)
        self.dc(0)
        self.spi.write(b"\x2B")
        window[0] = (y0 >> 8) & 0xFF
        window[1] = y0 & 0xFF
        window[2] = (y1 >> 8) & 0xFF
        window[3] = y1 & 0xFF
        self.dc(1)
        self.spi.write(window)
        self.dc(0)
        self.spi.write(b"\x2C")

    def _colour_chunk(self, color):
        """Return a reusable RGB565 run for color, avoiding per-call allocation."""
        chunk = self._chunks.get(color)
        if chunk is None:
            if len(self._chunks) >= LCD_FILL_CACHE_COLOURS:
                self._chunks.clear()
            chunk = memoryview(
                bytes(((color >> 8) & 0xFF, color & 0xFF)) * LCD_FILL_CHUNK_PIXELS
            )
            self._chunks[color] = chunk
        return chunk

    def _fill_window(self, x0, y0, x1, y1, color):
        """Fill an inclusive window in one CS transaction."""
        count = (x1 - x0 + 1) * (y1 - y0 + 1)
        chunk = self._colour_chunk(color)

        self.cs(0)
        self._send_window(x0, y0, x1, y1)
        self.dc(1)
        while count >= LCD_FILL_CHUNK_PIXELS:
            self.spi.write(chunk)
            count -= LCD_FILL_CHUNK_PIXELS
        if count:
            self.spi.write(chunk[:count * 2])
        self.cs(1)

    def blit(self, x, y, w, h, data):
        """Write a w x h block of big-endian RGB565 pixel data at (x, y)."""
        self.cs(0)
        self._send_window(x, y, x + w - 1, y + h - 1)
        self.dc(1)
        self.spi.write(data)
        self.cs(1)

    # ---------------------------------------------------------
    # Full-screen operations
    # ---------------------------------------------------------

    def fill(self, color):
        """Fill the complete display with an RGB565 colour."""
        self._fill_window(0, 0, self.WIDTH - 1, self.HEIGHT - 1, color)

    # ---------------------------------------------------------
    # Individual pixel
    # ---------------------------------------------------------

    def pixel(self, x, y, color):
        """Draw one pixel."""
        if not (0 <= x < self.WIDTH and 0 <= y < self.HEIGHT):
            return

        self._fill_window(x, y, x, y, color)

    # ---------------------------------------------------------
    # Horizontal line
    # ---------------------------------------------------------

    def hline(self, x, y, w, color):
        """Draw a horizontal line of width w."""
        if y < 0 or y >= self.HEIGHT or w <= 0:
            return

        x0 = max(0, x)
        x1 = min(self.WIDTH, x + w)

        if x0 >= x1:
            return

        self._fill_window(x0, y, x1 - 1, y, color)

    # ---------------------------------------------------------
    # Vertical line
    # ---------------------------------------------------------

    def vline(self, x, y, h, color):
        """Draw a vertical line of height h."""
        if x < 0 or x >= self.WIDTH or h <= 0:
            return

        y0 = max(0, y)
        y1 = min(self.HEIGHT, y + h)

        if y0 >= y1:
            return

        self._fill_window(x, y0, x, y1 - 1, color)

    # ---------------------------------------------------------
    # Filled rectangle
    # ---------------------------------------------------------

    def fill_rect(self, x, y, w, h, color):
        """Draw a filled rectangle, clipping it to the display."""
        if w <= 0 or h <= 0:
            return

        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.WIDTH, x + w)
        y1 = min(self.HEIGHT, y + h)

        if x0 >= x1 or y0 >= y1:
            return

        self._fill_window(x0, y0, x1 - 1, y1 - 1, color)

    # ---------------------------------------------------------
    # Backlight
    # ---------------------------------------------------------

    def backlight(self, on=True):
        """Turn the display backlight on or off."""
        self.bl.value(1 if on else 0)
