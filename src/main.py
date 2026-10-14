from ili9341 import ILI9341
from graphics import Graphics, BLACK, WHITE, CYAN, YELLOW, GREEN, GREY, RED
from ble_read import WT901BLEClient
from touch import TouchInput
from config import (
    ATTITUDE_REDRAW_THRESHOLD_DEG,
    BATTERY_POLL_INTERVAL_MS,
    DISPLAY_PITCH_SENSOR_KEY,
    DISPLAY_PITCH_SIGN,
    DISPLAY_ROLL_SENSOR_KEY,
    DISPLAY_ROLL_SIGN,
    FRONT_TRACK_MM,
    LEVEL_FRAME_RELEASE_THRESHOLD_DEG,
    LEVEL_FRAME_THRESHOLD_DEG,
    NO_WEDGE_NEEDED_THRESHOLD_CM,
    PITCH_PIXELS_PER_DEGREE,
    REAR_TRACK_MM,
    RENDER_INTERVAL_MS,
    SENSOR_STALE_MS,
    WHEELBASE_MM,
)

import math
import time


# MostlyLevel virtual horizon for the 240 x 320 ILI9341 display.
# The app provides a virtual horizon and a four-corner lift estimate page.
WIDTH = 240
HEIGHT = 320

SKY = 0x249F
GROUND = 0xB383
DARK = 0x2104
PILL = 0x194D
VAN_BODY = 0xFFFF
VAN_GLASS = 0x35BF
VAN_TRIM = 0x7BEF

HORIZON_TOP = 40
HORIZON_BOTTOM = HEIGHT - 1
HORIZON_CENTER_X = WIDTH // 2
HORIZON_CENTER_Y = (HORIZON_TOP + HORIZON_BOTTOM) // 2
print("Starting MostlyLevel dashboard")

lcd = ILI9341()
lcd.backlight(True)
g = Graphics(lcd)
sensor = WT901BLEClient()
try:
    touch = TouchInput()
    print("Touchscreen ready.")
except Exception as exc:
    touch = None
    print("Touchscreen unavailable:", exc)

active_screen = 0
corner_view = 0
corner_content = None
LEVEL_REFERENCE_FILE = "/level_reference.cfg"


def load_level_reference():
    try:
        with open(LEVEL_REFERENCE_FILE, "r") as reference_file:
            pitch_offset = float(reference_file.readline())
            roll_offset = float(reference_file.readline())
        return pitch_offset, roll_offset
    except (OSError, ValueError):
        return 0.0, 0.0


pitch_zero, roll_zero = load_level_reference()
level_frame_active = False


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


def draw_navigation():
    buttons = (
        (4, 21, 112, "HORIZON", active_screen == 0),
        (124, 21, 112, "LEVELLING", active_screen == 1),
    )
    for x, y, width, label, selected in buttons:
        fill = PILL if selected else DARK
        edge = CYAN if selected else GREY
        g.fill_rect(x, y, width, 17, fill)
        g.rect(x, y, width, 17, edge)
        g.text(x + (width - len(label) * 6) // 2, y + 5, label, WHITE)



def draw_calibrate_button():
    button_x = 140
    button_y = 50
    button_width = 88
    button_height = 18
    radius = 5
    g.fill_rect(
        button_x + radius,
        button_y,
        button_width - radius * 2,
        button_height,
        YELLOW,
    )
    g.fill_rect(
        button_x,
        button_y + radius,
        button_width,
        button_height - radius * 2,
        YELLOW,
    )
    for row in range(radius):
        distance = radius - row - 0.5
        inset = radius - int(math.sqrt(radius * radius - distance * distance))
        g.fill_rect(
            button_x + inset,
            button_y + row,
            button_width - inset * 2,
            1,
            YELLOW,
        )
        g.fill_rect(
            button_x + inset,
            button_y + button_height - row - 1,
            button_width - inset * 2,
            1,
            YELLOW,
        )
    g.text(
        button_x + (button_width - len("CALIBRATE") * 6) // 2,
        button_y + 5,
        "CALIBRATE",
        BLACK,
    )


def draw_corner_view_tabs():
    tabs = ((12, "2 WEDGES"), (128, "4 CORNERS"))
    for index, (x, label) in enumerate(tabs):
        fill = PILL if index == corner_view else DARK
        edge = CYAN if index == corner_view else GREY
        g.fill_rect(x, 42, 100, 17, fill)
        g.rect(x, 42, 100, 17, edge)
        g.text(x + (100 - len(label) * 6) // 2, 47, label, WHITE)


def corner_lift_heights(values):
    """Return minimum lift to level all four corners, in centimeters.

    Positive display pitch is assumed to mean front-high; positive display
    roll is assumed to mean left-high. Validate these signs after mounting.
    """
    display_values, pitch, roll = vehicle_values(values)
    if display_values is None:
        return None

    pitch_slope = math.tan(math.radians(pitch))
    roll_slope = math.tan(math.radians(roll))
    front_x = WHEELBASE_MM / 2.0
    rear_x = -front_x
    front_y = FRONT_TRACK_MM / 2.0
    rear_y = REAR_TRACK_MM / 2.0

    elevations = {
        "FRONT LEFT": front_x * pitch_slope + front_y * roll_slope,
        "FRONT RIGHT": front_x * pitch_slope - front_y * roll_slope,
        "REAR LEFT": rear_x * pitch_slope + rear_y * roll_slope,
        "REAR RIGHT": rear_x * pitch_slope - rear_y * roll_slope,
    }
    highest = max(elevations.values())
    return {corner: (highest - height) / 10.0 for corner, height in elevations.items()}


CORNER_ORDER = ("FRONT LEFT", "FRONT RIGHT", "REAR LEFT", "REAR RIGHT")
CORNER_CONTENT_TOP = 60
CORNER_VALUE_HEIGHT = 16  # Scale-2 glyph rows.
LEVEL_CONTENT = "LEVEL"


def cm_text(height_cm):
    return "--.- cm" if height_cm is None else "%.1f cm" % height_cm


def corner_page_content(values):
    """Return the text the active LEVELLING view should show.

    The result is LEVEL_CONTENT or a tuple of (label, value text) cells, so
    redraws can be limited to cells whose displayed text changed.
    """
    heights = corner_lift_heights(values)
    if corner_view == 0:
        if heights is None:
            return (("--", cm_text(None)), ("--", cm_text(None)))
        ranked = sorted(heights.items(), key=lambda item: item[1], reverse=True)
        if ranked[0][1] < NO_WEDGE_NEEDED_THRESHOLD_CM:
            return LEVEL_CONTENT
        return tuple((label, cm_text(height)) for label, height in ranked[:2])

    return tuple(
        (label, cm_text(None if heights is None else heights[label]))
        for label in CORNER_ORDER
    )


def draw_corner_cell(index, label, value, full):
    """Draw one LEVELLING cell; when not full, repaint only its value line."""
    if corner_view == 0:
        x = 4
        y = (68, 188)[index]
        width = 232
        height = 100
        label_text = "%d. %s" % (index + 1, label)
        label_x = x + 12
        label_y = y + 14
        value_y = y + 43
    else:
        x, y = ((4, 62), (124, 62), (4, 190), (124, 190))[index]
        width = 112
        height = 116
        label_text = label
        label_x = x + (width - len(label) * 6) // 2
        label_y = y + 23
        value_y = y + 50

    if full:
        g.fill_rect(x, y, width, height, DARK)
        g.rect(x, y, width, height, GREY)
        g.text(label_x, label_y, label_text, CYAN)
    else:
        g.fill_rect(x + 1, value_y, width - 2, CORNER_VALUE_HEIGHT, DARK)

    value_x = x + (width - len(value) * 12) // 2
    g.text(value_x, value_y, value, WHITE, scale=2)


def draw_corner_content(content):
    if content == LEVEL_CONTENT:
        g.text(69, 157, "NO WEDGES NEEDED", GREEN)
        g.text(62, 178, "VAN IS LEVEL", WHITE)
        return
    for index, (label, value) in enumerate(content):
        draw_corner_cell(index, label, value, True)


def draw_corner_heights(values):
    """Draw the complete LEVELLING page below the navigation bar."""
    global corner_content
    corner_content = corner_page_content(values)
    g.fill_rect(0, HORIZON_TOP, WIDTH, HEIGHT - HORIZON_TOP, BLACK)
    draw_corner_view_tabs()
    draw_corner_content(corner_content)


def update_corner_heights(values):
    """Repaint only the LEVELLING cells whose displayed text changed."""
    global corner_content
    content = corner_page_content(values)
    if content == corner_content:
        return

    previous = corner_content
    corner_content = content
    if (
        previous is None
        or content == LEVEL_CONTENT
        or previous == LEVEL_CONTENT
        or len(content) != len(previous)
    ):
        g.fill_rect(
            0,
            CORNER_CONTENT_TOP,
            WIDTH,
            HEIGHT - CORNER_CONTENT_TOP,
            BLACK,
        )
        draw_corner_content(content)
        return

    for index, (label, value) in enumerate(content):
        old_label, old_value = previous[index]
        if label != old_label:
            draw_corner_cell(index, label, value, True)
        elif value != old_value:
            draw_corner_cell(index, label, value, False)


def draw_readouts(values):
    box_height = 36
    box_y = HEIGHT - box_height - 8
    box_width = 108
    pitch_x = 10
    roll_x = WIDTH - pitch_x - box_width

    g.fill_rect(pitch_x, box_y, box_width, box_height, PILL)
    g.fill_rect(roll_x, box_y, box_width, box_height, PILL)
    g.text(pitch_x + 4, box_y + 10, "P " + angle_text(values, "pitch") + "°", WHITE, scale=2)
    g.text(roll_x + 4, box_y + 10, "R " + angle_text(values, "roll") + "°", WHITE, scale=2)


def is_level(pitch, roll, was_level=False):
    threshold = (
        LEVEL_FRAME_RELEASE_THRESHOLD_DEG
        if was_level
        else LEVEL_FRAME_THRESHOLD_DEG
    )
    return (
        abs(pitch) <= threshold
        and abs(roll) <= threshold
    )


def draw_level_frame():
    draw_status_frame(GREEN)


def draw_status_frame(colour):
    thickness = 6
    g.fill_rect(0, HORIZON_TOP, WIDTH, thickness, colour)
    g.fill_rect(0, HEIGHT - thickness, WIDTH, thickness, colour)
    g.fill_rect(0, HORIZON_TOP, thickness, HEIGHT - HORIZON_TOP, colour)
    g.fill_rect(WIDTH - thickness, HORIZON_TOP, thickness, HEIGHT - HORIZON_TOP, colour)


def draw_sensor_warning(state, message=None):
    if message is None:
        if state == "NO DATA":
            message = "SENSOR DATA STALE"
        elif state in ("DISCONNECTED", "ERROR"):
            message = "SENSOR DISCONNECTED"
        else:
            message = "WAITING FOR SENSOR"

    panel_x = 9
    panel_y = 143
    panel_width = WIDTH - 18
    panel_height = 34
    g.fill_rect(panel_x, panel_y, panel_width, panel_height, DARK)
    g.rect(panel_x, panel_y, panel_width, panel_height, RED)
    text_x = (WIDTH - len(message) * 6) // 2
    g.text(text_x, panel_y + 13, message, YELLOW)
    draw_status_frame(RED)


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
            run_start = None
            run_y = None
            for x in range(start_x, end_x, 3):
                y = int(base_y + roll_slope * (x - HORIZON_CENTER_X))
                if HORIZON_TOP < y < HORIZON_BOTTOM and y == run_y:
                    continue
                if run_start is not None:
                    g.fill_rect(run_start, run_y, x - run_start, 2, WHITE)
                if HORIZON_TOP < y < HORIZON_BOTTOM:
                    run_start = x
                    run_y = y
                else:
                    run_start = None
                    run_y = None
            if run_start is not None:
                g.fill_rect(run_start, run_y, end_x - run_start, 2, WHITE)

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

    # Group adjacent strips with the same boundary height. Near level, this
    # replaces dozens of tiny SPI windows with only a few wide rectangles.
    run_x = 0
    run_y = horizon_y(2, pitch_deg, roll_slope)
    for x in range(4, WIDTH + 1, 4):
        next_y = (
            horizon_y(x + 2, pitch_deg, roll_slope)
            if x < WIDTH
            else None
        )
        if next_y == run_y:
            continue

        run_width = x - run_x
        g.fill_rect(run_x, HORIZON_TOP, run_width, run_y - HORIZON_TOP, SKY)
        g.fill_rect(
            run_x,
            run_y,
            run_width,
            HORIZON_BOTTOM - run_y + 1,
            GROUND,
        )
        if next_y is not None:
            run_x = x
            run_y = next_y

    # Merge adjacent horizontal horizon segments that share the same row.
    run_x = 0
    run_y = horizon_y(2, pitch_deg, roll_slope)
    for x in range(4, WIDTH + 1, 4):
        next_y = (
            horizon_y(x + 2, pitch_deg, roll_slope)
            if x < WIDTH
            else None
        )
        if next_y == run_y:
            continue
        g.fill_rect(run_x, run_y, x - run_x, 1, WHITE)
        if next_y is not None:
            run_x = x
            run_y = next_y

    draw_pitch_arc()
    draw_ladder(pitch_deg, roll_deg)
    draw_van_side(HORIZON_CENTER_Y)


def vehicle_values(values):
    # The observed installation responds on crossed sensor axes: raising the
    # front changes the decoded X/roll channel, while raising the left changes
    # the decoded Y/pitch channel. Map those channels to vehicle pitch/roll here.
    if values is None:
        return None, 0.0, 0.0

    pitch = values[DISPLAY_PITCH_SENSOR_KEY] * DISPLAY_PITCH_SIGN - pitch_zero
    roll = values[DISPLAY_ROLL_SENSOR_KEY] * DISPLAY_ROLL_SIGN - roll_zero
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


def save_level_reference():
    with open(LEVEL_REFERENCE_FILE, "w") as reference_file:
        reference_file.write("%.5f\n%.5f\n" % (pitch_zero, roll_zero))


def set_level_reference(values):
    global pitch_zero, roll_zero
    if values is None:
        return False

    pitch_zero = values[DISPLAY_PITCH_SENSOR_KEY] * DISPLAY_PITCH_SIGN
    roll_zero = values[DISPLAY_ROLL_SENSOR_KEY] * DISPLAY_ROLL_SIGN
    try:
        save_level_reference()
    except OSError as exc:
        print("Level reference active until restart; save failed:", exc)
    return True


def draw_dashboard(values, state):
    g.clear(BLACK)
    draw_header(state)
    draw_navigation()
    if active_screen == 0:
        display_values, pitch, roll = vehicle_values(values)
        draw_horizon(pitch, roll)
        draw_calibrate_button()
        draw_readouts(display_values)
        if state == "LIVE" and display_values is not None and level_frame_active:
            draw_level_frame()
    else:
        draw_corner_heights(values)
    if state != "LIVE":
        draw_sensor_warning(state)


def touch_screen_at(point):
    if point is None:
        return None
    x, y = point
    if 21 <= y < 38:
        if 4 <= x < 116:
            return 0
        if 124 <= x < 236:
            return 1
    return None


def touch_calibrate_at(point):
    if point is None or active_screen != 0:
        return False
    x, y = point
    return 140 <= x < 228 and 50 <= y < 68


def touch_corner_view_at(point):
    if point is None:
        return None
    x, y = point
    if 42 <= y < 59:
        if 12 <= x < 112:
            return 0
        if 128 <= x < 228:
            return 1
    return None


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
        # Invert vehicle_values() so draw_dashboard reproduces the last
        # rendered attitude: restore the level reference and sensor mapping.
        values = {
            DISPLAY_PITCH_SENSOR_KEY: (last_attitude[0] + pitch_zero) / DISPLAY_PITCH_SIGN,
            DISPLAY_ROLL_SENSOR_KEY: (last_attitude[1] + roll_zero) / DISPLAY_ROLL_SIGN,
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
last_level = None
last_render_ms = 0
screen_initialized = False
last_battery_request_ms = None
last_battery_percent = None
touch_was_down = False

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
        level_frame_active = (
            state == "LIVE"
            and sensor.latest is not None
            and is_level(pitch, roll)
        )
        draw_dashboard(sensor.latest, state)
        screen_initialized = True
        last_state = state
        last_attitude = attitude if sensor.latest is not None else None
        last_level = level_frame_active
        last_render_ms = time.ticks_ms()
    else:
        state_changed = state != last_state
        if state_changed:
            draw_header(state)
            last_state = state
            last_battery_percent = sensor.power_percent
            if state == "LIVE":
                level_frame_active = is_level(pitch, roll)
                draw_dashboard(sensor.latest, state)
                last_attitude = attitude
                last_level = level_frame_active
                last_render_ms = time.ticks_ms()
            elif state_changed:
                level_frame_active = False
                last_level = False
                draw_sensor_warning(state)
        elif sensor.power_percent != last_battery_percent:
            draw_header(state)
            last_battery_percent = sensor.power_percent

        level_now = (
            state == "LIVE"
            and sensor.latest is not None
            and is_level(pitch, roll, level_frame_active)
        )
        level_frame_active = level_now
        if state == "LIVE" and sensor.latest is not None and (
            attitude_changed(attitude, last_attitude) or level_now != last_level
        ) and (
            last_render_ms == 0
            or time.ticks_diff(now, last_render_ms) >= RENDER_INTERVAL_MS
        ):
            if active_screen == 0:
                draw_horizon(pitch, roll)
                draw_calibrate_button()
                draw_readouts(display_values)
                if level_now:
                    draw_level_frame()
            else:
                update_corner_heights(sensor.latest)
            last_attitude = attitude
            last_level = level_now
            last_render_ms = time.ticks_ms()

    if touch is not None:
        try:
            touch_point = touch.read()
            if touch_point is not None and not touch_was_down:
                selected_screen = touch_screen_at(touch_point)
                if touch_calibrate_at(touch_point):
                    if state == "LIVE" and set_level_reference(sensor.latest):
                        display_values, pitch, roll = vehicle_values(sensor.latest)
                        level_frame_active = is_level(pitch, roll)
                        draw_dashboard(sensor.latest, state)
                        attitude = (pitch, roll)
                        last_attitude = attitude
                        last_level = level_frame_active
                        last_render_ms = time.ticks_ms()
                    else:
                        draw_sensor_warning(state, "ZERO NEEDS LIVE SENSOR")
                elif selected_screen is not None and selected_screen != active_screen:
                    active_screen = selected_screen
                    draw_dashboard(sensor.latest, state)
                elif active_screen == 1:
                    selected_view = touch_corner_view_at(touch_point)
                    if selected_view is not None and selected_view != corner_view:
                        corner_view = selected_view
                        draw_dashboard(sensor.latest, state)
            touch_was_down = touch_point is not None
        except Exception as exc:
            print("Touch read failed:", exc)
            touch = None

    time.sleep_ms(30)
