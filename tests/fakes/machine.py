"""Fake MicroPython `machine` module backed by `fakehw`."""

import fakehw


class Pin:
    IN = 0
    OUT = 1

    def __init__(self, pin_id, mode=-1, value=None, pull=None):
        self.id = pin_id
        if value is not None:
            fakehw.pins[pin_id] = value

    def __call__(self, value=None):
        return self.value(value)

    def value(self, value=None):
        if value is None:
            return fakehw.pins.get(self.id, 0)
        fakehw.pins[self.id] = value
        return None


class SPI:
    def __init__(self, spi_id, baudrate=0, polarity=0, phase=0, sck=None, mosi=None, miso=None):
        self.id = spi_id
        self.baudrate = baudrate

    def write(self, data):
        from config import LCD_DC_PIN

        fakehw.panel.write(data, fakehw.pins.get(LCD_DC_PIN, 1))


class I2C:
    def __init__(self, i2c_id, scl=None, sda=None, freq=0):
        self.id = i2c_id

    def scan(self):
        from config import TOUCH_ADDRESS

        return [TOUCH_ADDRESS] if fakehw.touch.present else []

    def readfrom_mem(self, address, register, count):
        return fakehw.touch.read(register, count)
