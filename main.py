from machine import Pin, I2C
import struct
import time
import math
import json

from display import EPD_2in9

# -----------------------------
# Hardware configuration
# -----------------------------

SDA_PIN = 4
SCL_PIN = 5

BUTTON_PIN = 2

MPU_ADDR = 0x68

# -----------------------------
# Behaviour configuration
# -----------------------------

I2C_FREQ = 100000
ALPHA = 0.90
TOLERANCE = 0.7
LOOP_DELAY = 0.5

# E-paper displays flicker on refresh.
# Keep this fairly high.
DISPLAY_REFRESH_SECONDS = 20
DISPLAY_CHANGE_THRESHOLD = 0.5

CALIBRATION_FILE = "calibration.json"

# -----------------------------
# Setup
# -----------------------------

time.sleep(2)

i2c = I2C(
    0,
    scl=Pin(SCL_PIN),
    sda=Pin(SDA_PIN),
    freq=I2C_FREQ
)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

epd = EPD_2in9()

pitch_offset = 0.0
roll_offset = 0.0

smooth_pitch = 0.0
smooth_roll = 0.0

last_display_update = 0
last_display_pitch = None
last_display_roll = None
last_front_back = None
last_left_right = None

# -----------------------------
# Calibration storage
# -----------------------------

def load_calibration():
    global pitch_offset, roll_offset

    try:
        with open(CALIBRATION_FILE, "r") as f:
            data = json.load(f)

        pitch_offset = float(data.get("pitch_offset", 0.0))
        roll_offset = float(data.get("roll_offset", 0.0))

        print("Loaded calibration")
        print("Pitch offset:", round(pitch_offset, 2))
        print("Roll offset:", round(roll_offset, 2))

    except Exception:
        print("No calibration file found")
        pitch_offset = 0.0
        roll_offset = 0.0


def save_calibration():
    data = {
        "pitch_offset": pitch_offset,
        "roll_offset": roll_offset,
    }

    with open(CALIBRATION_FILE, "w") as f:
        json.dump(data, f)

    print("Calibration saved")

# -----------------------------
# MPU6050 functions
# -----------------------------

def init_mpu():
    devices = i2c.scan()

    print("I2C devices:", devices)

    if MPU_ADDR not in devices:
        print("ERROR: MPU6050 not found")
        return False

    try:
        i2c.writeto_mem(MPU_ADDR, 0x6B, b"\x00")
        i2c.writeto_mem(MPU_ADDR, 0x1C, b"\x00")

        print("MPU6050 ready")
        return True

    except OSError as e:
        print("MPU init error:", e)
        return False


def read_word(reg):
    try:
        data = i2c.readfrom_mem(MPU_ADDR, reg, 2)
        return struct.unpack(">h", data)[0]

    except OSError as e:
        print("I2C read error:", e)
        return None


def read_angles():
    ax_raw = read_word(0x3B)
    ay_raw = read_word(0x3D)
    az_raw = read_word(0x3F)

    if ax_raw is None or ay_raw is None or az_raw is None:
        return None

    ax = ax_raw / 16384.0
    ay = ay_raw / 16384.0
    az = az_raw / 16384.0

    pitch = math.degrees(
        math.atan2(ax, math.sqrt(ay * ay + az * az))
    )

    roll = math.degrees(
        math.atan2(ay, math.sqrt(ax * ax + az * az))
    )

    return pitch, roll

# -----------------------------
# Button handling
# -----------------------------

def button_pressed():
    return button.value() == 0

# -----------------------------
# Calibration functions
# -----------------------------

def average_angles(samples=50, delay=0.02):
    total_pitch = 0.0
    total_roll = 0.0
    valid = 0

    for _ in range(samples):
        result = read_angles()

        if result is not None:
            pitch, roll = result
            total_pitch += pitch
            total_roll += roll
            valid += 1

        time.sleep(delay)

    if valid == 0:
        return None

    return (
        total_pitch / valid,
        total_roll / valid
    )


def calibrate_current_position():
    global pitch_offset, roll_offset
    global smooth_pitch, smooth_roll

    print("Calibrating, keep sensor still...")

    show_status_screen(
        "CALIBRATING",
        "Keep sensor still"
    )

    result = average_angles()

    if result is None:
        print("Calibration failed")

        show_status_screen(
            "CAL FAILED",
            "No MPU readings"
        )

        return

    pitch_offset, roll_offset = result

    smooth_pitch = pitch_offset
    smooth_roll = roll_offset

    print("CALIBRATED")
    print("Pitch offset:", round(pitch_offset, 2))
    print("Roll offset:", round(roll_offset, 2))

    save_calibration()

    show_status_screen(
        "CALIBRATED",
        "Position saved"
    )

# -----------------------------
# Helper functions
# -----------------------------

def guidance(value, positive_label, negative_label):
    if value > TOLERANCE:
        return positive_label

    elif value < -TOLERANCE:
        return negative_label

    else:
        return "OK"


def format_angle(value):
    return "{:+.1f}".format(value)


def show_status_screen(title, message):
    epd.fb.fill(1)

    epd.fb.text("Mostly Level", 10, 8, 0)
    epd.fb.hline(10, 22, 276, 0)

    epd.fb.text(title, 10, 48, 0)
    epd.fb.text(message, 10, 68, 0)

    epd.display()


def show_level_screen(
    level_pitch,
    level_roll,
    front_back,
    left_right
):
    epd.fb.fill(1)

    epd.fb.text("Mostly Level", 10, 8, 0)
    epd.fb.hline(10, 22, 276, 0)

    epd.fb.text("PITCH", 10, 34, 0)
    epd.fb.text(format_angle(level_pitch), 80, 34, 0)
    epd.fb.text(front_back, 150, 34, 0)

    epd.fb.text("ROLL", 10, 54, 0)
    epd.fb.text(format_angle(level_roll), 80, 54, 0)
    epd.fb.text(left_right, 150, 54, 0)

    epd.fb.hline(10, 78, 276, 0)

    center_x = 148
    center_y = 102

    epd.fb.rect(48, 90, 200, 24, 0)
    epd.fb.vline(center_x, 86, 32, 0)

    display_roll = level_roll

    if display_roll > 10:
        display_roll = 10

    if display_roll < -10:
        display_roll = -10

    bubble_x = int(center_x + display_roll * 8)

    epd.fb.fill_rect(
        bubble_x - 8,
        center_y - 6,
        16,
        12,
        0
    )

    if front_back == "OK" and left_right == "OK":
        epd.fb.text("LEVEL", 124, 120, 0)

    else:
        epd.fb.text(
            "Adjust until OK",
            84,
            120,
            0
        )

    epd.display()

# -----------------------------
# Main program
# -----------------------------

print("Mostly Level starting...")
print("Initializing display...")

epd.init()

show_status_screen(
    "STARTING",
    "Initializing MPU"
)

load_calibration()

while not init_mpu():
    print("Waiting for MPU6050...")

    show_status_screen(
        "MPU NOT FOUND",
        "Check wiring"
    )

    time.sleep(2)

first_reading = None

while first_reading is None:
    first_reading = read_angles()

    if first_reading is None:
        print("Waiting for sensor...")

        show_status_screen(
            "WAITING",
            "Sensor reading"
        )

        time.sleep(1)

smooth_pitch, smooth_roll = first_reading

print("Running.")
print("Press button to calibrate.")

show_status_screen(
    "RUNNING",
    "Press button to cal"
)

time.sleep(2)

while True:

    result = read_angles()

    if result is None:
        print("Bad reading")

        show_status_screen(
            "BAD READING",
            "Recovering MPU"
        )

        init_mpu()

        time.sleep(1)

        continue

    raw_pitch, raw_roll = result

    smooth_pitch = (
        ALPHA * smooth_pitch
        + (1 - ALPHA) * raw_pitch
    )

    smooth_roll = (
        ALPHA * smooth_roll
        + (1 - ALPHA) * raw_roll
    )

    # -------------------------
    # Calibration button
    # -------------------------

    if button_pressed():

        calibrate_current_position()

        while button_pressed():
            time.sleep(0.05)

        time.sleep(0.3)

        last_display_update = 0
        last_display_pitch = None
        last_display_roll = None
        last_front_back = None
        last_left_right = None

    # -------------------------
    # Level calculations
    # -------------------------

    level_pitch = smooth_pitch - pitch_offset
    level_roll = smooth_roll - roll_offset

    front_back = guidance(
        level_pitch,
        "FRONT HIGH",
        "REAR HIGH"
    )

    left_right = guidance(
        level_roll,
        "RIGHT HIGH",
        "LEFT HIGH"
    )

    print(
        "Pitch:", round(level_pitch, 1),
        "Roll:", round(level_roll, 1),
        "|", front_back,
        "|", left_right
    )

    # -------------------------
    # Display update control
    # -------------------------

    now = time.time()

    display_changed = False

    if last_display_pitch is None:
        display_changed = True

    elif abs(level_pitch - last_display_pitch) >= DISPLAY_CHANGE_THRESHOLD:
        display_changed = True

    elif abs(level_roll - last_display_roll) >= DISPLAY_CHANGE_THRESHOLD:
        display_changed = True

    elif front_back != last_front_back:
        display_changed = True

    elif left_right != last_left_right:
        display_changed = True

    if display_changed and now - last_display_update >= DISPLAY_REFRESH_SECONDS:
        show_level_screen(
            level_pitch,
            level_roll,
            front_back,
            left_right
        )

        last_display_pitch = level_pitch
        last_display_roll = level_roll
        last_front_back = front_back
        last_left_right = left_right
        last_display_update = now

    time.sleep(LOOP_DELAY)