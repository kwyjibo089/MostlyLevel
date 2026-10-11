from ili9341 import ILI9341
from graphics import (
    Graphics,
    BLACK,
    WHITE,
    BLUE,
    CYAN,
    YELLOW,
    GREEN,
    GREY,
)

import math


# ============================================================
# MostlyLevel - Artificial Horizon
# Display: ES3C28P, 240 x 320, ILI9341
# ============================================================

WIDTH = 240
HEIGHT = 320

# RGB565 colours
SKY = 0x249F
GROUND = 0xB383
DARK = 0x2104
VAN_BODY = 0xD69A
VAN_GLASS = 0x35BF
VAN_WHEEL = 0x0000
HORIZON_LINE = 0xFFFF
MARKING = 0xFFFF


# ============================================================
# Display setup
# ============================================================

print("Starting MostlyLevel artificial horizon")

lcd = ILI9341()
lcd.backlight(True)

g = Graphics(lcd)


# ============================================================
# Simulated sensor values
# ============================================================

pitch = 4.0
roll = -6.0


# ============================================================
# Header
# ============================================================

def draw_header():
    g.fill_rect(0, 0, WIDTH, 34, DARK)
    g.text(8, 7, "MOSTLYLEVEL", WHITE, 2)

    g.fill_rect(207, 10, 8, 8, YELLOW)
    g.fill_rect(219, 10, 8, 8, GREEN)


# ============================================================
# Artificial horizon
# ============================================================

def draw_horizon(pitch_deg, roll_deg):
    top = 34
    bottom = 286

    center_x = WIDTH // 2
    center_y = 164

    pitch_scale = 3.0

    pitch_deg = max(-35, min(35, pitch_deg))
    roll_deg = max(-45, min(45, roll_deg))

    pitch_offset = int(pitch_deg * pitch_scale)
    roll_slope = math.tan(math.radians(roll_deg))

    strip_width = 4

    # Draw sky and ground in vertical strips.
    for x in range(0, WIDTH, strip_width):
        actual_width = min(strip_width, WIDTH - x)

        horizon_y = int(
            center_y
            + pitch_offset
            + roll_slope * (x - center_x)
        )

        horizon_y = max(top, min(bottom, horizon_y))

        g.fill_rect(
            x,
            top,
            actual_width,
            horizon_y - top,
            SKY,
        )

        g.fill_rect(
            x,
            horizon_y,
            actual_width,
            bottom - horizon_y,
            GROUND,
        )

    # Draw the horizon boundary.
    for x in range(WIDTH - 1):
        y1 = int(
            center_y
            + pitch_offset
            + roll_slope * (x - center_x)
        )

        y2 = int(
            center_y
            + pitch_offset
            + roll_slope * (x + 1 - center_x)
        )

        y1 = max(top, min(bottom - 1, y1))
        y2 = max(top, min(bottom - 1, y2))

        g.pixel(x, y1, HORIZON_LINE)
        g.pixel(x, y2, HORIZON_LINE)

    draw_horizon_markings(
        center_x,
        center_y + pitch_offset,
        roll_slope,
        top,
        bottom,
    )


# ============================================================
# Horizon markings
# ============================================================

def draw_horizon_markings(
    center_x,
    center_y,
    roll_slope,
    top,
    bottom,
):
    marks = [
        (-80, "20"),
        (-60, ""),
        (-40, "10"),
        (-20, ""),
        (20, ""),
        (40, "-10"),
        (60, ""),
        (80, "-20"),
    ]

    for offset, label in marks:
        y = center_y + offset

        if y < top + 4 or y > bottom - 4:
            continue

        left_x = 85
        right_x = 155

        left_y = int(
            y + roll_slope * (left_x - center_x)
        )

        right_y = int(
            y + roll_slope * (right_x - center_x)
        )

        if top < left_y < bottom:
            g.hline(left_x, left_y, 24, MARKING)

        if top < right_y < bottom:
            g.hline(right_x + 12, right_y, 24, MARKING)

        if label:
            label_y = y - 4

            g.text(48, label_y, label, WHITE, 1)
            g.text(190, label_y, label, WHITE, 1)


# ============================================================
# Top-down camper van
# ============================================================

def draw_van():
    cx = WIDTH // 2
    cy = 164

    # Wheels
    g.fill_rect(cx - 24, cy - 26, 7, 20, VAN_WHEEL)
    g.fill_rect(cx + 17, cy - 26, 7, 20, VAN_WHEEL)
    g.fill_rect(cx - 24, cy + 9, 7, 20, VAN_WHEEL)
    g.fill_rect(cx + 17, cy + 9, 7, 20, VAN_WHEEL)

    # Main body
    g.fill_rect(cx - 17, cy - 34, 34, 68, VAN_BODY)

    # Windscreen
    g.fill_rect(cx - 13, cy - 27, 26, 15, VAN_GLASS)

    # Rear window
    g.fill_rect(cx - 12, cy + 16, 24, 10, VAN_GLASS)

    # Roof detail
    g.fill_rect(cx - 11, cy - 7, 22, 19, GREY)

    # Bumpers
    g.fill_rect(cx - 14, cy - 36, 28, 3, WHITE)
    g.fill_rect(cx - 14, cy + 34, 28, 3, WHITE)

    # Front marker
    g.fill_rect(cx - 3, cy - 31, 6, 3, YELLOW)


# ============================================================
# Angle readouts
# ============================================================

def draw_angle_readouts(pitch_deg, roll_deg):
    # MicroPython-compatible numeric formatting.
    pitch_text = "%+.1f" % pitch_deg
    roll_text = "%+.1f" % roll_deg

    g.fill_rect(5, 39, 104, 23, DARK)
    g.text(10, 46, "P:" + pitch_text, WHITE, 1)

    g.fill_rect(131, 39, 104, 23, DARK)
    g.text(136, 46, "R:" + roll_text, WHITE, 1)


# ============================================================
# Footer
# ============================================================

def draw_footer():
    g.fill_rect(0, 287, WIDTH, 33, DARK)

    g.text(8, 295, "CAMPER LEVEL", WHITE, 1)
    g.text(8, 307, "WT901: DEMO", CYAN, 1)

    g.fill_rect(190, 296, 12, 12, GREEN)
    g.text(207, 298, "DEMO", YELLOW, 1)


# ============================================================
# Render screen
# ============================================================

def draw_screen(pitch_deg, roll_deg):
    draw_header()
    draw_horizon(pitch_deg, roll_deg)
    draw_van()
    draw_angle_readouts(pitch_deg, roll_deg)
    draw_footer()


# ============================================================
# Main
# ============================================================

print("Rendering artificial horizon...")

draw_screen(pitch, roll)

print("Artificial horizon rendered")
print("Pitch: %+.1f" % pitch)
print("Roll: %+.1f" % roll)