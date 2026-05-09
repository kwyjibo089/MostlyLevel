from machine import Pin, SPI
import framebuf
import utime

LOGICAL_WIDTH = 296
LOGICAL_HEIGHT = 128

PHYSICAL_WIDTH = 128
PHYSICAL_HEIGHT = 296
BUFFER_SIZE = PHYSICAL_WIDTH * PHYSICAL_HEIGHT // 8

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13


class EPD_2in9:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.busy_pin = Pin(BUSY_PIN, Pin.IN)

        self.spi = SPI(
            1,
            baudrate=4_000_000,
            polarity=0,
            phase=0,
            sck=Pin(10),
            mosi=Pin(11),
            miso=None
        )

        self.buffer = bytearray(LOGICAL_WIDTH * LOGICAL_HEIGHT // 8)

        self.fb = framebuf.FrameBuffer(
            self.buffer,
            LOGICAL_WIDTH,
            LOGICAL_HEIGHT,
            framebuf.MONO_HLSB
        )

    def send_command(self, c):
        self.dc_pin(0)
        self.cs_pin(0)
        self.spi.write(bytearray([c]))
        self.cs_pin(1)

    def send_data(self, d):
        self.dc_pin(1)
        self.cs_pin(0)
        self.spi.write(bytearray([d]))
        self.cs_pin(1)

    def write_block(self, data):
        self.dc_pin(1)
        self.cs_pin(0)
        self.spi.write(data)
        self.cs_pin(1)

    def reset(self):
        self.reset_pin(1)
        utime.sleep_ms(200)
        self.reset_pin(0)
        utime.sleep_ms(10)
        self.reset_pin(1)
        utime.sleep_ms(200)

    def wait_busy(self):
        timeout = 0
        while self.busy_pin() == 1:
            utime.sleep_ms(100)
            timeout += 1
            if timeout > 150:
                print("BUSY timeout")
                break

    def init(self):
        print("Init display")

        self.reset()

        self.send_command(0x12)
        self.wait_busy()

        self.send_command(0x01)
        self.send_data(0x27)
        self.send_data(0x01)
        self.send_data(0x00)

        self.send_command(0x11)
        self.send_data(0x03)

        self.send_command(0x44)
        self.send_data(0x00)
        self.send_data(0x0F)

        self.send_command(0x45)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x27)
        self.send_data(0x01)

        self.send_command(0x3C)
        self.send_data(0x05)

        # Important: display update control
        self.send_command(0x21)
        self.send_data(0x00)
        self.send_data(0x80)

        self.send_command(0x18)
        self.send_data(0x80)

        self.set_cursor(0, 0)
        self.wait_busy()

    def set_cursor(self, x, y):
        self.send_command(0x4E)
        self.send_data(x & 0xFF)

        self.send_command(0x4F)
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)

    def make_display_buffer(self):
        out = bytearray(BUFFER_SIZE)
        i = 0

        for py in range(PHYSICAL_HEIGHT):
            for xb in range(PHYSICAL_WIDTH // 8):
                value = 0

                for bit in range(8):
                    px = xb * 8 + bit

                    lx = py
                    ly = LOGICAL_HEIGHT - 1 - px

                    pixel = self.fb.pixel(lx, ly)

                    if pixel:
                        value |= 0x80 >> bit

                out[i] = value
                i += 1

        return out

    def display(self):
        display_buffer = self.make_display_buffer()
        white = bytes([0xFF]) * BUFFER_SIZE

        self.set_cursor(0, 0)
        self.send_command(0x26)
        self.write_block(white)

        self.set_cursor(0, 0)
        self.send_command(0x24)
        self.write_block(display_buffer)

        self.turn_on_display()

    def full_white_refresh(self):
        white = bytes([0xFF]) * BUFFER_SIZE

        self.set_cursor(0, 0)
        self.send_command(0x26)
        self.write_block(white)

        self.set_cursor(0, 0)
        self.send_command(0x24)
        self.write_block(white)

        self.turn_on_display()

    def turn_on_display(self):
        self.send_command(0x22)
        self.send_data(0xF7)
        self.send_command(0x20)
        self.wait_busy()

    def sleep(self):
        self.send_command(0x10)
        self.send_data(0x01)
        utime.sleep_ms(200)


print("Starting ePaper test")

epd = EPD_2in9()
epd.init()

print("Full white refresh")
epd.full_white_refresh()
utime.sleep_ms(500)

epd.fb.fill(1)

epd.fb.text("Pico WH OK", 10, 8, 0)
epd.fb.text("ABCDEFG 1234567", 10, 26, 0)
epd.fb.text("CapTouch ePaper 2.9", 10, 44, 0)

epd.fb.rect(5, 64, 286, 58, 0)
epd.fb.line(5, 64, 291, 122, 0)
epd.fb.line(291, 64, 5, 122, 0)

epd.fb.text("LEFT", 10, 104, 0)
epd.fb.text("RIGHT", 240, 104, 0)

for x in range(20, 280, 20):
    epd.fb.vline(x, 76, 36, 0)

print("Updating display")
epd.display()

print("Done")
epd.sleep()