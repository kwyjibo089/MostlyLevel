"""Minimal FT5x06 capacitive touch reader for the ES3C28P reference wiring."""

from machine import I2C, Pin
import time
from config import (
    TOUCH_ADDRESS,
    TOUCH_DATA_REGISTER,
    TOUCH_I2C_FREQUENCY,
    TOUCH_I2C_ID,
    TOUCH_I2C_SCL_PIN,
    TOUCH_I2C_SDA_PIN,
    TOUCH_RESET_LOW_MS,
    TOUCH_RESET_PIN,
    TOUCH_STARTUP_DELAY_MS,
)


class TouchInput:
    def __init__(self):
        self.reset = Pin(TOUCH_RESET_PIN, Pin.OUT, value=0)
        time.sleep_ms(TOUCH_RESET_LOW_MS)
        self.reset(1)
        time.sleep_ms(TOUCH_STARTUP_DELAY_MS)
        self.i2c = I2C(
            TOUCH_I2C_ID,
            scl=Pin(TOUCH_I2C_SCL_PIN),
            sda=Pin(TOUCH_I2C_SDA_PIN),
            freq=TOUCH_I2C_FREQUENCY,
        )
        if TOUCH_ADDRESS not in self.i2c.scan():
            raise OSError(
                "FT5x06 touch controller not found at 0x%02X" % TOUCH_ADDRESS
            )

    def read(self):
        """Return one (x, y) touch point, or None when the panel is idle."""
        data = self.i2c.readfrom_mem(TOUCH_ADDRESS, TOUCH_DATA_REGISTER, 5)
        if (data[0] & 0x0F) == 0:
            return None

        x = ((data[1] & 0x0F) << 8) | data[2]
        y = ((data[3] & 0x0F) << 8) | data[4]
        return x, y
