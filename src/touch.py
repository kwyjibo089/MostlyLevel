"""Minimal FT5x06 capacitive touch reader for the ES3C28P reference wiring."""

from machine import I2C, Pin
import time


TOUCH_ADDRESS = 0x38
TOUCH_DATA_REGISTER = 0x02


class TouchInput:
    def __init__(self):
        self.reset = Pin(18, Pin.OUT, value=0)
        time.sleep_ms(10)
        self.reset(1)
        time.sleep_ms(150)
        self.i2c = I2C(0, scl=Pin(15), sda=Pin(16), freq=400000)
        if TOUCH_ADDRESS not in self.i2c.scan():
            raise OSError("FT5x06 touch controller not found at 0x38")

    def read(self):
        """Return one (x, y) touch point, or None when the panel is idle."""
        data = self.i2c.readfrom_mem(TOUCH_ADDRESS, TOUCH_DATA_REGISTER, 5)
        if (data[0] & 0x0F) == 0:
            return None

        x = ((data[1] & 0x0F) << 8) | data[2]
        y = ((data[3] & 0x0F) << 8) | data[4]
        return x, y
