from ili9341 import ILI9341
from graphics import Graphics, BLACK, WHITE, CYAN, YELLOW, GREEN, GREY
from ble_read import WT901BLEClient

import math
import time


# MostlyLevel virtual horizon for the 240 x 320 ILI9341 display.
# The phone status bar, tabs, and buttons in the mockup are not device
# hardware, so this screen keeps the attitude display only.
WIDTH = 240
HEIGHT = 320

SKY = 0x249F
GROUND = 0xB383
DARK = 0x2104
PILL = 0x194D
VAN_BODY = 0xFFFF
VAN_GLASS = 0x35BF
VAN_TRIM = 0x7BEF

HORIZON_TOP = 19
HORIZON_BOTTOM = HEIGHT - 1
HORIZON_CENTER_X = WIDTH // 2
HORIZON_CENTER_Y = (HORIZON_TOP + HORIZON_BOTTOM) // 2
PITCH_PIXELS_PER_DEGREE = 1.8
RENDER_INTERVAL_MS = 250
ATTITUDE_REDRAW_THRESHOLD_DEG = 0.2
SENSOR_STALE_MS = 1500
BATTERY_POLL_INTERVAL_MS = 60000


print("Starting MostlyLevel dashboard")

lcd = ILI9341()
lcd.backlight(True)
g = Graphics(lcd)
sensor = WT901BLEClient()


def clamp(value, low, high):
    return max(low, min(high, value))


def angle_text(values, key):
    if values is None:
        return "--.-"
    return "%+.1f" % values[key]


def draw_header(state):
    g.fill_rect(0, 0, WIDTH, 19, DARK)
    g.text(7, 5, "MOSTLYLEVEL", WHITE)

    battery_percent = sensor.power_percent
    g.fill_rect(143, 2, 31, 15, DARK)
    if battery_percent is not None:
        g.text(149, 5, "%d%%" % battery_percent, GREEN)

    if state == "LIVE":
        status_colour = GREEN
    elif state in ("ERROR", "DISCONNECTED", "NO DATA"):
        status_colour = YELLOW
    else:
        status_colour = CYAN

    status_label = {
        "DISCOVERING": "GATT",
        "SETTING UP": "SETUP",
        "DISCONNECTED": "NO LINK",
        "NO DATA": "STALE",
    }.get(state, state)
    g.fill_rect(178, 6, 7, 7, status_colour)
    g.text(189, 5, status_label, status_colour)


def draw_readouts(values):
    box_height = 36
    box_y = HEIGHT - box_height - 8

    g.fill_rect(5, box_y, 112, box_height, PILL)
    g.fill_rect(123, box_y, 112, box_height, PILL)
    g.text(9, box_y + 10, "P " + angle_text(values, "pitch") + "°", WHITE, scale=2)
    g.text(127, box_y + 10, "R " + angle_text(values, "roll") + "°", WHITE, scale=2)


def horizon_y(x, pitch_deg, roll_slope):
    y = int(
        HORIZON_CENTER_Y
        + pitch_deg * PITCH_PIXELS_PER_DEGREE
        + roll_slope * (x - HORIZON_CENTER_X)
    )
    return clamp(y, HORIZON_TOP, HORIZON_BOTTOM)


def draw_pitch_arc():
    """Draw the fixed curved attitude scale above the moving horizon."""
    rx = 105
    ry = 90
    baseline = HORIZON_CENTER_Y + 10
    previous = None

    for x in range(15, 226, 3):
        normalized = (x - HORIZON_CENTER_X) / float(rx)
        if abs(normalized) > 1:
            continue
        y = baseline - int(ry * math.sqrt(1.0 - normalized * normalized))

        if previous is not None:
            px, py = previous
            y0 = min(py, y)
            g.fill_rect(px, y0, x - px + 1, max(1, abs(y - py) + 1), WHITE)
        previous = (x, y)

    for degree in range(-40, 41, 5):
        x = HORIZON_CENTER_X + int(rx * degree / 40.0)
        normalized = (x - HORIZON_CENTER_X) / float(rx)
        y = baseline - int(ry * math.sqrt(max(0.0, 1.0 - normalized * normalized)))
        tick_height = 7 if degree % 10 == 0 else 4
        g.fill_rect(x - 1, y - tick_height // 2, 2, tick_height, WHITE)

        if degree % 10 == 0:
            label = str(degree)
            g.text(x - len(label) * 3, y - 15, label, WHITE)


def draw_ladder(pitch_deg, roll_deg):
    pitch_offset = pitch_deg * PITCH_PIXELS_PER_DEGREE
    roll_slope = math.tan(math.radians(roll_deg))

    for mark in (20, 10, -10, -20):
        base_y = HORIZON_CENTER_Y + pitch_offset - mark * 1.35
        if base_y < HORIZON_TOP + 3 or base_y > HORIZON_BOTTOM - 3:
            continue

        for start_x, end_x in ((73, 103), (137, 167)):
            for x in range(start_x, end_x, 3):
                y = int(base_y + roll_slope * (x - HORIZON_CENTER_X))
                if HORIZON_TOP < y < HORIZON_BOTTOM:
                    g.fill_rect(x, y, 3, 2, WHITE)

        label = "%+d" % mark
        label_y = int(base_y - 3)
        g.text(43, label_y, label, WHITE)
        g.text(177, label_y, label, WHITE)


def draw_van_side(center_y):
    """Draw a larger, high-contrast side-view camper above the marker."""
    x = 87
    y = int(center_y - 26)

    # Stepped dark silhouette: tall camper body, cab roof, and sloped nose.
    g.fill_rect(x + 4, y + 10, 48, 17, DARK)
    g.fill_rect(x + 8, y + 3, 39, 10, DARK)
    g.fill_rect(x + 45, y + 7, 14, 20, DARK)
    g.fill_rect(x + 51, y + 4, 9, 5, DARK)
    g.fill_rect(x + 57, y + 12, 8, 13, DARK)

    # Bright body panels set apart the camper section from the driver's cab.
    g.fill_rect(x + 6, y + 11, 45, 13, VAN_BODY)
    g.fill_rect(x + 10, y + 4, 35, 8, VAN_BODY)
    g.fill_rect(x + 47, y + 8, 11, 16, VAN_BODY)
    g.fill_rect(x + 52, y + 5, 7, 3, VAN_BODY)
    g.fill_rect(x + 58, y + 15, 6, 8, VAN_BODY)

    # Two large habitation windows and a separate driver's window.
    g.fill_rect(x + 12, y + 6, 12, 5, VAN_GLASS)
    g.fill_rect(x + 27, y + 6, 14, 5, VAN_GLASS)
    g.fill_rect(x + 49, y + 10, 8, 7, VAN_GLASS)
    g.fill_rect(x + 58, y + 13, 5, 2, VAN_GLASS)

    # Door, handle, lower accent stripe, bumper, and headlight.
    g.vline(x + 43, y + 12, 12, VAN_TRIM)
    g.fill_rect(x + 38, y + 15, 4, 1, VAN_TRIM)
    g.fill_rect(x + 7, y + 21, 46, 2, VAN_TRIM)
    g.fill_rect(x + 63, y + 22, 3, 3, VAN_TRIM)
    g.fill_rect(x + 63, y + 17, 2, 3, YELLOW)

    # Broad wheels with visible hubs.
    g.fill_rect(x + 10, y + 22, 13, 10, BLACK)
    g.fill_rect(x + 43, y + 22, 13, 10, BLACK)
    g.fill_rect(x + 14, y + 25, 5, 4, VAN_TRIM)
    g.fill_rect(x + 47, y + 25, 5, 4, VAN_TRIM)

    marker_y = int(center_y + 12)
    for row in range(6):
        half_width = row + 1
        g.fill_rect(
            HORIZON_CENTER_X - half_width,
            marker_y + row,
            half_width * 2 + 1,
            1,
            YELLOW,
        )


def draw_horizon(pitch_deg, roll_deg):
    pitch_deg = clamp(pitch_deg, -35.0, 35.0)
    roll_deg = clamp(roll_deg, -45.0, 45.0)
    roll_slope = math.tan(math.radians(roll_deg))

    # Move the sky/ground boundary with pitch and roll. Positive pitch moves
    # the horizon down, expanding the blue sky around the fixed vehicle marker.
    for x in range(0, WIDTH, 4):
        y = horizon_y(x + 2, pitch_deg, roll_slope)
        g.fill_rect(x, HORIZON_TOP, 4, y - HORIZON_TOP, SKY)
        g.fill_rect(x, y, 4, HORIZON_BOTTOM - y + 1, GROUND)

    # Short white segments make the moving horizon line.
    for x in range(0, WIDTH, 4):
        y = horizon_y(x + 2, pitch_deg, roll_slope)
        g.fill_rect(x, y, 4, 1, WHITE)

    draw_pitch_arc()
    draw_ladder(pitch_deg, roll_deg)
    draw_van_side(HORIZON_CENTER_Y)


def vehicle_values(values):
    # The observed installation responds on crossed sensor axes: raising the
    # front changes the decoded X/roll channel, while raising the left changes
    # the decoded Y/pitch channel. Map those channels to vehicle pitch/roll here.
    if values is None:
        return None, 0.0, 0.0

    pitch = values["roll"]
    roll = values["pitch"]
    display_values = {
        "pitch": pitch,
        "roll": roll,
    }
    return display_values, pitch, roll


def attitude_changed(current, displayed):
    if displayed is None:
        return True

    return (
        abs(current[0] - displayed[0]) >= ATTITUDE_REDRAW_THRESHOLD_DEG
        or abs(current[1] - displayed[1]) >= ATTITUDE_REDRAW_THRESHOLD_DEG
    )


def draw_dashboard(values, state):
    display_values, pitch, roll = vehicle_values(values)
    g.clear(BLACK)
    draw_header(state)
    draw_horizon(pitch, roll)
    draw_readouts(display_values)


def save_screenshot(path="/screenshot.bmp"):
    """Render the last displayed attitude to a BMP without reading LCD MISO."""
    global g

    from screenshot import TileFramebufferDisplay, write_bmp_header, write_bmp_tile
    import gc

    gc.collect()
    original_graphics = g

    if last_attitude is None:
        values = None
    else:
        # Convert the displayed vehicle axes back to the sensor-key layout
        # expected by draw_dashboard, preserving the last rendered values.
        values = {
            "roll": last_attitude[0],
            "pitch": last_attitude[1],
        }

    tile_height = 8
    with open(path, "wb") as image_file:
        write_bmp_header(image_file, WIDTH, HEIGHT)

        try:
            for top in range(0, HEIGHT, tile_height):
                rows = min(tile_height, HEIGHT - top)
                tile = TileFramebufferDisplay(WIDTH, rows, top)
                g = Graphics(tile)
                try:
                    draw_dashboard(values, last_state)
                finally:
                    g = original_graphics
                write_bmp_tile(image_file, tile.buffer, WIDTH, rows)
                del tile
                gc.collect()
        finally:
            g = original_graphics

    return path


sensor.start()

last_state = None
last_attitude = None
last_render_ms = 0
screen_initialized = False
last_battery_request_ms = None
last_battery_percent = None

while True:
    now = time.ticks_ms()
    state = sensor.state

    if sensor.latest is not None:
        if time.ticks_diff(now, sensor.last_packet_ms) > SENSOR_STALE_MS:
            state = "NO DATA"
        else:
            state = "LIVE"
    elif state == "LIVE":
        state = "WAIT"

    if state == "LIVE" and sensor.write_handle is not None and (
        last_battery_request_ms is None
        or time.ticks_diff(now, last_battery_request_ms) >= BATTERY_POLL_INTERVAL_MS
    ):
        try:
            sensor.request_power_read(keep_previous=True)
            last_battery_request_ms = now
        except Exception as exc:
            print("Battery read request failed:", exc)

    display_values, pitch, roll = vehicle_values(sensor.latest)
    attitude = (pitch, roll)

    if not screen_initialized:
        draw_dashboard(sensor.latest, state)
        screen_initialized = True
        last_state = state
        last_attitude = attitude if sensor.latest is not None else None
        last_render_ms = time.ticks_ms()
    else:
        if state != last_state or sensor.power_percent != last_battery_percent:
            draw_header(state)
            last_state = state
            last_battery_percent = sensor.power_percent

        if sensor.latest is not None and attitude_changed(attitude, last_attitude) and (
            last_render_ms == 0
            or time.ticks_diff(now, last_render_ms) >= RENDER_INTERVAL_MS
        ):
            draw_horizon(pitch, roll)
            draw_readouts(display_values)
            last_attitude = attitude
            last_render_ms = time.ticks_ms()

    time.sleep_ms(30)
