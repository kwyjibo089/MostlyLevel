"""MostlyLevel hardware, sensor, vehicle, and display tuning settings."""

# WT901BLE67-compatible sensor connection and GATT settings.
SENSOR_NAME = "WT901BLE67"
SENSOR_MAC = bytes.fromhex("F0A07ADB7D45")
SENSOR_WRITE_UUID = "0000ffe9-0000-1000-8000-00805f9a34fb"
SENSOR_NOTIFY_UUID = "0000ffe4-0000-1000-8000-00805f9a34fb"
SENSOR_CCCD_HANDLE = 16  # Candidate handle; not yet derived from discovery.
SENSOR_POWER_REGISTER = 0x64
SENSOR_POWER_READ_COMMAND = bytes((0xFF, 0xAA, 0x27, SENSOR_POWER_REGISTER, 0x00))

# Fixed assumptions used by the current sensor packet decoder.
SENSOR_PACKET_HEADER = 0x55
SENSOR_ATTITUDE_PACKET_TYPE = 0x61
SENSOR_REGISTER_PACKET_TYPE = 0x71
SENSOR_ATTITUDE_PACKET_LENGTH = 20
SENSOR_RAW_FULL_SCALE = 32768.0
SENSOR_ACCEL_RANGE_G = 16.0
SENSOR_GYRO_RANGE_DPS = 2000.0
SENSOR_ANGLE_RANGE_DEG = 180.0
SENSOR_POWER_VOLTAGE_DIVISOR = 100.0
SENSOR_BATTERY_PERCENT_BANDS = (
    (397, 100),
    (393, 90),
    (387, 75),
    (382, 60),
    (379, 50),
    (377, 40),
    (373, 30),
    (370, 20),
    (368, 15),
    (350, 10),
    (340, 5),
)

# Decoded sensor channels mapped to vehicle axes. Hardware-tested 2026-10-16 with
# the installed sensor: front up gives positive pitch, left up positive roll.
# Recheck if the sensor is remounted.
DISPLAY_PITCH_SENSOR_KEY = "roll"
DISPLAY_PITCH_SIGN = 1.0
DISPLAY_ROLL_SENSOR_KEY = "pitch"
DISPLAY_ROLL_SIGN = 1.0

# Vehicle geometry used for corner lift estimates.
WHEELBASE_MM = 4035.0
FRONT_TRACK_MM = 1810.0
REAR_TRACK_MM = 1790.0
NO_WEDGE_NEEDED_THRESHOLD_CM = 0.5

# Display update tuning.
PITCH_PIXELS_PER_DEGREE = 1.8
# Rows at the top of the LCD hidden by the printed case. Header, navigation,
# and the top of each page move down by this amount; bottom and side
# positions stay fixed. Owner-observed from a photo (~9 rows hidden).
SCREEN_TOP_INSET = 10
LEVEL_FRAME_THRESHOLD_DEG = 0.5
LEVEL_FRAME_RELEASE_THRESHOLD_DEG = 0.7
RENDER_INTERVAL_MS = 250
ATTITUDE_REDRAW_THRESHOLD_DEG = 0.2
SENSOR_STALE_MS = 1500
BATTERY_POLL_INTERVAL_MS = 60000
# HORIZON page strip buffer height: 240 * rows * 2 bytes (19.2 KB at 40).
# If allocation fails at startup, smaller strips are tried. Untested value.
HORIZON_STRIP_ROWS = 40

# ILI9341 SPI wiring for the current board setup.
LCD_SPI_ID = 2
LCD_SPI_BAUDRATE = 20000000
LCD_SPI_SCK_PIN = 12
LCD_SPI_MOSI_PIN = 11
LCD_SPI_MISO_PIN = 13
LCD_CS_PIN = 10
LCD_DC_PIN = 46
LCD_BACKLIGHT_PIN = 45
# Reused per-colour fill buffers: CHUNK_PIXELS * 2 bytes each, at most
# CACHE_COLOURS buffers (16 KB with these values). Untested tuning values.
LCD_FILL_CHUNK_PIXELS = 512
LCD_FILL_CACHE_COLOURS = 16

# FT5x06-compatible touchscreen wiring from the reference BSP.
TOUCH_I2C_ID = 0
TOUCH_I2C_SCL_PIN = 15
TOUCH_I2C_SDA_PIN = 16
TOUCH_I2C_FREQUENCY = 400000
TOUCH_RESET_PIN = 18
TOUCH_ADDRESS = 0x38
TOUCH_DATA_REGISTER = 0x02
TOUCH_RESET_LOW_MS = 10
TOUCH_STARTUP_DELAY_MS = 150
