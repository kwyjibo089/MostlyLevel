"""MostlyLevel dashboard: virtual horizon and corner lift estimates.

main.py calls run(). Tests call setup() and then step() to drive one loop
pass at a time against fake hardware.
"""

from ili9341 import ILI9341
from graphics import Graphics, BLACK, WHITE, CYAN, YELLOW, GREEN, GREY, RED
from ble_read import WT901BLEClient
from touch import TouchInput
from compositor import DisplayList, StripRenderer
import vans
import i18n
from i18n import t
from config import (
    ATTITUDE_REDRAW_THRESHOLD_DEG,
    BATTERY_POLL_INTERVAL_MS,
    DISPLAY_PITCH_SENSOR_KEY,
    DISPLAY_PITCH_SIGN,
    DISPLAY_ROLL_SENSOR_KEY,
    DISPLAY_ROLL_SIGN,
    FRONT_TRACK_MM,
    HORIZON_STRIP_ROWS,
    LEVEL_FRAME_RELEASE_THRESHOLD_DEG,
    LEVEL_FRAME_THRESHOLD_DEG,
    LONG_PRESS_MS,
    NO_WEDGE_NEEDED_THRESHOLD_CM,
    REAR_TRACK_MM,
    SCREEN_TOP_INSET,
    RENDER_INTERVAL_MS,
    SENSOR_RECOVERY_RESET_COUNT,
    SENSOR_STALE_MS,
    SETUP_ERROR_RESET_MS,
    VAN_TILT_GAIN,
    VAN_TILT_MAX_DEG,
    STEP_ERROR_RESET_COUNT,
    STEP_ERROR_RETRY_MS,
    WHEELBASE_MM,
)

import gc
import machine
import math
import sys
import time


# MostlyLevel virtual horizon for the 240 x 320 ILI9341 display.
# The app provides a virtual horizon and a four-corner lift estimate page.
WIDTH = 240
HEIGHT = 320

SKY = 0x249F
GROUND = 0xB383
DARK = 0x2104
PILL = 0x194D

HEADER_Y = SCREEN_TOP_INSET
NAV_Y = HEADER_Y + 21
NAV_HEIGHT = 17
HORIZON_TOP = HEADER_Y + 40
HORIZON_BOTTOM = HEIGHT - 1
HORIZON_CENTER_X = WIDTH // 2
HORIZON_CENTER_Y = (HORIZON_TOP + HORIZON_BOTTOM) // 2

# Fixed HORIZON elements.
CALIBRATE_RECT = (140, HORIZON_TOP + 10, 88, 18)
# Language button on HORIZON, left of CALIBRATE on the same line. The header
# is partly hidden by the printed case, so it is not placed there. Its touch
# area is a little larger than the button.
LANGUAGE_RECT = (12, HORIZON_TOP + 10, 44, 18)
LANGUAGE_TOUCH_RECT = (4, HORIZON_TOP + 4, 60, 30)
CALIBRATE_RADIUS = 5
READOUT_WIDTH = 108
READOUT_HEIGHT = 36
READOUT_Y = HEIGHT - READOUT_HEIGHT - 8
READOUT_RECTS = (
    (10, READOUT_Y, READOUT_WIDTH, READOUT_HEIGHT),
    (WIDTH - 10 - READOUT_WIDTH, READOUT_Y, READOUT_WIDTH, READOUT_HEIGHT),
)
READOUT_TEXT_INSET_X = 4
READOUT_TEXT_INSET_Y = 10
FRAME_THICKNESS = 6
FRAME_RECTS = (
    (0, HORIZON_TOP, WIDTH, FRAME_THICKNESS),
    (0, HEIGHT - FRAME_THICKNESS, WIDTH, FRAME_THICKNESS),
    (0, HORIZON_TOP, FRAME_THICKNESS, HEIGHT - HORIZON_TOP),
    (WIDTH - FRAME_THICKNESS, HORIZON_TOP, FRAME_THICKNESS, HEIGHT - HORIZON_TOP),
)
# Hardware objects, created by setup().
lcd = None
g = None
screen_graphics = None
page_renderer = None
sensor = None
touch = None


def create_page_renderer():
    """Allocate the page strip buffer early, before the heap fragments.

    Both pages share it: they cover the same rows below the navigation bar.
    """
    rows = HORIZON_STRIP_ROWS
    while rows >= 8:
        try:
            return StripRenderer(lcd, HORIZON_TOP, HEIGHT, rows)
        except MemoryError:
            print("Strip buffer of %d rows unavailable; trying smaller." % rows)
            rows //= 2
    print("Strip rendering unavailable; drawing pages directly.")
    return None


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


pitch_zero = 0.0
roll_zero = 0.0
level_frame_active = False


def clamp(value, low, high):
    return max(low, min(high, value))


def local_number(text):
    """Use the active language's decimal separator."""
    return text.replace(".", t("decimal"))


def angle_text(values, key):
    if values is None:
        return local_number("--.-")
    return local_number("%+.1f" % values[key])


# Text keys of the connection states shown in the header.
STATUS_KEYS = {
    "LIVE": "status_live",
    "SCANNING": "status_scanning",
    "CONNECTING": "status_connecting",
    "DISCOVERING": "status_setup",
    "SETTING UP": "status_setup",
    "DISCONNECTING": "status_disconnected",
    "DISCONNECTED": "status_disconnected",
    "NO DATA": "status_stale",
    "WAIT": "status_wait",
    "ERROR": "status_error",
    "IDLE": "status_idle",
}


def draw_header(state):
    # Also fills the rows hidden by the case so they never show stale pixels.
    g.fill_rect(0, 0, WIDTH, HEADER_Y + 19, DARK)
    g.text(7, HEADER_Y + 5, "MOSTLYLEVEL", WHITE)

    battery_percent = sensor.power_percent
    g.fill_rect(143, HEADER_Y + 2, 31, 15, DARK)
    if battery_percent is not None:
        g.text(149, HEADER_Y + 5, "%d%%" % battery_percent, GREEN)

    if state == "LIVE":
        status_colour = GREEN
    elif state in ("ERROR", "DISCONNECTED", "NO DATA"):
        status_colour = YELLOW
    else:
        status_colour = CYAN

    status_key = STATUS_KEYS.get(state)
    status_label = t(status_key) if status_key else state
    g.fill_rect(178, HEADER_Y + 6, 7, 7, status_colour)
    g.text(189, HEADER_Y + 5, status_label, status_colour)


def draw_navigation():
    buttons = (
        (4, NAV_Y, 112, t("nav_horizon"), active_screen == 0),
        (124, NAV_Y, 112, t("nav_levelling"), active_screen == 1),
    )
    for x, y, width, label, selected in buttons:
        fill = PILL if selected else DARK
        edge = CYAN if selected else GREY
        g.fill_rect(x, y, width, NAV_HEIGHT, fill)
        g.rect(x, y, width, NAV_HEIGHT, edge)
        g.text(x + (width - len(label) * 6) // 2, y + 5, label, WHITE)



def calibrate_corner_insets():
    """Return the per-row inset of the CALIBRATE button's rounded corners."""
    radius = CALIBRATE_RADIUS
    insets = []
    for row in range(radius):
        distance = radius - row - 0.5
        insets.append(radius - int(math.sqrt(radius * radius - distance * distance)))
    return tuple(insets)


CALIBRATE_INSETS = calibrate_corner_insets()


def draw_rounded_button(rect, colour, label):
    button_x, button_y, button_width, button_height = rect
    radius = CALIBRATE_RADIUS
    g.fill_rect(
        button_x + radius,
        button_y,
        button_width - radius * 2,
        button_height,
        colour,
    )
    g.fill_rect(
        button_x,
        button_y + radius,
        button_width,
        button_height - radius * 2,
        colour,
    )
    for row, inset in enumerate(CALIBRATE_INSETS):
        g.fill_rect(
            button_x + inset,
            button_y + row,
            button_width - inset * 2,
            1,
            colour,
        )
        g.fill_rect(
            button_x + inset,
            button_y + button_height - row - 1,
            button_width - inset * 2,
            1,
            colour,
        )
    g.text(
        button_x + (button_width - len(label) * 6) // 2,
        button_y + 5,
        label,
        BLACK,
    )


# Button being held for a long press: "calibrate", "language", or None.
hold_target = None
hold_start_ms = 0
hold_progress = 0  # Progress bar eighths shown on the held button.
HOLD_STEPS = 8


def hold_rect():
    return CALIBRATE_RECT if hold_target == "calibrate" else LANGUAGE_RECT


def draw_hold_progress():
    """Draw the held button's progress bar along its bottom edge."""
    if hold_target is None or hold_progress == 0:
        return
    x, y, width, height = hold_rect()
    inner = width - CALIBRATE_RADIUS * 2
    g.fill_rect(
        x + CALIBRATE_RADIUS,
        y + height - 4,
        inner * hold_progress // HOLD_STEPS,
        2,
        BLACK,
    )


def draw_calibrate_button():
    draw_rounded_button(CALIBRATE_RECT, YELLOW, t("calibrate"))


def draw_language_button():
    draw_rounded_button(LANGUAGE_RECT, CYAN, (i18n.language or "--").upper())


def draw_corner_view_tabs():
    tabs = ((12, t("tab_wedges")), (128, t("tab_corners")))
    for index, (x, label) in enumerate(tabs):
        fill = PILL if index == corner_view else DARK
        edge = CYAN if index == corner_view else GREY
        g.fill_rect(x, CORNER_TABS_Y, 100, NAV_HEIGHT, fill)
        g.rect(x, CORNER_TABS_Y, 100, NAV_HEIGHT, edge)
        g.text(x + (100 - len(label) * 6) // 2, CORNER_TABS_Y + 5, label, WHITE)


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
# Text keys of the corner names; CORNER_ORDER names are internal keys.
CORNER_TEXT_KEYS = {
    "FRONT LEFT": "front_left",
    "FRONT RIGHT": "front_right",
    "REAR LEFT": "rear_left",
    "REAR RIGHT": "rear_right",
}
CORNER_TABS_Y = HORIZON_TOP + 2
CORNER_CONTENT_TOP = HORIZON_TOP + 20
# Cell rows keep fixed bottom edges and shrink when the top inset grows.
WEDGE_TOP = HORIZON_TOP + 28
WEDGE_BOTTOM = 288
WEDGE_GAP = 20
WEDGE_HEIGHT = (WEDGE_BOTTOM - WEDGE_TOP - WEDGE_GAP) // 2
CORNER_TOP = HORIZON_TOP + 22
CORNER_BOTTOM = 306
CORNER_GAP = 12
CORNER_HEIGHT = (CORNER_BOTTOM - CORNER_TOP - CORNER_GAP) // 2
CORNER_ROW_Y = (CORNER_TOP, CORNER_TOP + CORNER_HEIGHT + CORNER_GAP)
CORNER_VALUE_HEIGHT = 16  # Scale-2 glyph rows.
LEVEL_CONTENT = "LEVEL"


def cm_text(height_cm):
    return local_number("--.- cm" if height_cm is None else "%.1f cm" % height_cm)


def corner_text(corner):
    return t(CORNER_TEXT_KEYS[corner])


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
        return tuple(
            (corner_text(corner), cm_text(height)) for corner, height in ranked[:2]
        )

    return tuple(
        (corner_text(corner), cm_text(None if heights is None else heights[corner]))
        for corner in CORNER_ORDER
    )


def corner_cell_geometry(index):
    """Return (x, y, width, height, value_y) of a cell in the active view."""
    if corner_view == 0:
        y = WEDGE_TOP + index * (WEDGE_HEIGHT + WEDGE_GAP)
        return 4, y, 232, WEDGE_HEIGHT, y + WEDGE_HEIGHT // 2 - 7
    y = CORNER_ROW_Y[index // 2]
    return (4, 124)[index % 2], y, 112, CORNER_HEIGHT, y + CORNER_HEIGHT // 2 - 8


def draw_corner_cell(index, label, value, full):
    """Draw one LEVELLING cell; when not full, repaint only its value line."""
    x, y, width, height, value_y = corner_cell_geometry(index)
    if corner_view == 0:
        label_text = "%d. %s" % (index + 1, label)
        label_x = x + 12
        label_y = y + 14
    else:
        label_text = label
        label_x = x + (width - len(label) * 6) // 2
        label_y = y + height // 5

    if full:
        g.fill_rect(x, y, width, height, DARK)
        g.rect(x, y, width, height, GREY)
        g.text(label_x, label_y, label_text, CYAN)
    else:
        g.fill_rect(x + 1, value_y, width - 2, CORNER_VALUE_HEIGHT, DARK)

    value_x = x + (width - len(value) * 12) // 2
    g.text(value_x, value_y, value, WHITE, scale=2)


def draw_centred_text(y, text, colour):
    g.text((WIDTH - len(text) * 6) // 2, y, text, colour)


def draw_corner_content(content):
    if content == LEVEL_CONTENT:
        middle = (WEDGE_TOP + WEDGE_BOTTOM) // 2
        draw_centred_text(middle - 21, t("no_wedges_needed"), GREEN)
        draw_centred_text(middle, t("van_is_level"), WHITE)
        return
    for index, (label, value) in enumerate(content):
        draw_corner_cell(index, label, value, True)


def draw_levelling_page(content):
    draw_corner_view_tabs()
    draw_corner_content(content)


def draw_corner_heights(values):
    """Draw the complete LEVELLING page below the navigation bar."""
    global corner_content
    corner_content = corner_page_content(values)
    if compositing():
        page_renderer.invalidate()
        page_renderer.render(record_items(draw_levelling_page, corner_content))
        return
    g.fill_rect(0, HORIZON_TOP, WIDTH, HEIGHT - HORIZON_TOP, BLACK)
    draw_levelling_page(corner_content)


def update_corner_heights(values):
    """Repaint the LEVELLING page where its displayed text changed."""
    global corner_content
    content = corner_page_content(values)
    if content == corner_content:
        return

    previous = corner_content
    corner_content = content
    composite = compositing()
    if (
        previous is None
        or content == LEVEL_CONTENT
        or previous == LEVEL_CONTENT
        or len(content) != len(previous)
        or (composite and any(
            label != old[0] for (label, _), old in zip(content, previous)
        ))
    ):
        if composite:
            # Layout change: composite the page; unchanged strips are skipped.
            gc.collect()
            page_renderer.render(record_items(draw_levelling_page, content))
            return
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
            if composite:
                # Composite just the value line off-screen and send it once.
                x, y, width, height, value_y = corner_cell_geometry(index)
                page_renderer.render_area(
                    x + 1,
                    value_y,
                    width - 2,
                    CORNER_VALUE_HEIGHT,
                    record_items(draw_corner_cell, index, label, value, False),
                )
            else:
                draw_corner_cell(index, label, value, False)


def readout_text(values):
    return (
        t("pitch_short") + " " + angle_text(values, "pitch") + "°",
        t("roll_short") + " " + angle_text(values, "roll") + "°",
    )


def draw_readouts(values):
    for (x, y, width, height), text in zip(READOUT_RECTS, readout_text(values)):
        g.fill_rect(x, y, width, height, PILL)
        g.text(
            x + READOUT_TEXT_INSET_X,
            y + READOUT_TEXT_INSET_Y,
            text,
            WHITE,
            scale=2,
        )


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
    for x, y, width, height in FRAME_RECTS:
        g.fill_rect(x, y, width, height, colour)


def draw_sensor_warning(state, message=None):
    if message is None:
        if state == "NO DATA":
            message = t("warning_stale")
        elif state in ("DISCONNECTED", "ERROR"):
            message = t("warning_disconnected")
        else:
            message = t("warning_waiting")

    panel_x = 9
    panel_y = HORIZON_CENTER_Y - 36
    panel_width = WIDTH - 18
    panel_height = 34
    g.fill_rect(panel_x, panel_y, panel_width, panel_height, DARK)
    g.rect(panel_x, panel_y, panel_width, panel_height, RED)
    text_x = (WIDTH - len(message) * 6) // 2
    g.text(text_x, panel_y + 13, message, YELLOW)
    draw_status_frame(RED)
    if page_renderer is not None:
        # The warning covers part of the composited region.
        page_renderer.invalidate()


# The attitude scenes: the van from behind tilts with roll, the van from
# the right tilts with pitch, each standing on fixed, level ground.
REAR_GROUND_Y = HORIZON_TOP + 102
SIDE_GROUND_Y = HEIGHT - READOUT_HEIGHT - 22
GROUND_DEPTH = 8


def van_tilt(angle_deg):
    """Displayed tilt: exaggerated so small angles show, then clamped."""
    return clamp(angle_deg * VAN_TILT_GAIN, -VAN_TILT_MAX_DEG, VAN_TILT_MAX_DEG)


def draw_scene(van, tilt_deg, ground_y, level):
    g.fill_rect(0, ground_y, WIDTH, GROUND_DEPTH, GROUND)
    # The ground's top edge turns green while this axis is level.
    g.fill_rect(0, ground_y, WIDTH, 1, GREEN if level else WHITE)
    picture, x, y = vans.draw_tilted(van, tilt_deg, VAN_TILT_MAX_DEG)
    g.bitmap(HORIZON_CENTER_X + x, ground_y + y, picture)


def draw_attitude(pitch_deg, roll_deg):
    g.fill_rect(0, HORIZON_TOP, WIDTH, HEIGHT - HORIZON_TOP, SKY)
    # Positive roll lifts the left side: seen from behind, the van turns
    # clockwise. Positive pitch lifts the front, which faces right in the
    # side view: the van turns anticlockwise.
    draw_scene(
        vans.REAR, van_tilt(roll_deg), REAR_GROUND_Y,
        abs(roll_deg) < LEVEL_FRAME_THRESHOLD_DEG,
    )
    draw_scene(
        vans.SIDE, -van_tilt(pitch_deg), SIDE_GROUND_Y,
        abs(pitch_deg) < LEVEL_FRAME_THRESHOLD_DEG,
    )


def record_items(draw, *args):
    """Run a drawing function and return its filled rects instead of drawing."""
    global g
    target_graphics = g
    recorder = DisplayList()
    g = Graphics(recorder)
    try:
        draw(*args)
    finally:
        g = target_graphics
    return recorder.items


def compositing():
    """True when pages go through the strip renderer (not for screenshots)."""
    return page_renderer is not None and g is screen_graphics


# Recorded rects of HORIZON layers that never move, keyed by layer name.
layer_cache = {}


def draw_cached(key, draw, *args):
    """Draw a fixed layer, recording its rects only the first time."""
    items = layer_cache.get(key)
    if items is None:
        items = layer_cache[key] = tuple(record_items(draw, *args))

    if isinstance(g.lcd, DisplayList):
        g.lcd.items.extend(items)
    else:
        for item in items:
            g.item(item)


def draw_horizon_layers(pitch, roll, display_values, level):
    draw_attitude(pitch, roll)
    draw_cached("calibrate", draw_calibrate_button)
    draw_cached("language", draw_language_button)
    draw_hold_progress()
    draw_readouts(display_values)
    if level:
        draw_cached("level", draw_level_frame)


def horizon_page_items(pitch, roll, display_values, level):
    """Record the HORIZON page below the navigation bar as filled rects."""
    return record_items(draw_horizon_layers, pitch, roll, display_values, level)


# Arguments of the last HORIZON page drawn, to repaint a held button.
last_horizon_args = None


def draw_held_button():
    """Repaint only the held button (with its progress) in one transfer."""
    if active_screen != 0 or last_horizon_args is None:
        return
    x, y, width, height = hold_rect()
    items = horizon_page_items(*last_horizon_args)
    if compositing():
        page_renderer.render_area(x, y, width, height, items)
    else:
        draw_cached("calibrate", draw_calibrate_button)
        draw_cached("language", draw_language_button)
        draw_hold_progress()


def draw_horizon_page(pitch, roll, display_values, level, force=False):
    """Draw the HORIZON page, compositing off-screen when possible.

    Every pixel is sent once with its final colour, so moving graphics no
    longer erase and repaint the elements drawn over them.
    """
    global last_horizon_args
    last_horizon_args = (pitch, roll, display_values, level)
    items = horizon_page_items(pitch, roll, display_values, level)
    if not compositing():
        # Fallback, and screenshots: draw the same rects directly.
        for item in items:
            g.item(item)
        return
    if force:
        page_renderer.invalidate()
    page_renderer.render(items)


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
    if not (compositing() and screen_initialized):
        g.clear(BLACK)
    # Otherwise skip the clear, which would flash the screen black: the
    # header and navigation repaint themselves, the rows between them stay
    # black, and the compositor repaints the whole page area below.
    draw_header(state)
    draw_navigation()
    if active_screen == 0:
        display_values, pitch, roll = vehicle_values(values)
        level = (
            state == "LIVE" and display_values is not None and level_frame_active
        )
        draw_horizon_page(pitch, roll, display_values, level, force=True)
    else:
        draw_corner_heights(values)
    if state != "LIVE":
        draw_sensor_warning(state)


def touch_screen_at(point):
    if point is None:
        return None
    x, y = point
    if NAV_Y <= y < NAV_Y + NAV_HEIGHT:
        if 4 <= x < 116:
            return 0
        if 124 <= x < 236:
            return 1
    return None


def touch_language_at(point):
    if point is None or active_screen != 0:
        return False
    x, y = point
    touch_x, touch_y, touch_width, touch_height = LANGUAGE_TOUCH_RECT
    return touch_x <= x < touch_x + touch_width and touch_y <= y < touch_y + touch_height


def switch_language(values, state):
    """Show the next language now and remember it across restarts."""
    code = i18n.next_language()
    try:
        i18n.load(code)
    except (OSError, ValueError) as exc:
        print("Language %s unavailable:" % code, exc)
        return
    try:
        i18n.save()
    except OSError as exc:
        print("Language active until restart; save failed:", exc)
    layer_cache.clear()  # The buttons hold translated text.
    draw_dashboard(values, state)


def touch_calibrate_at(point):
    if point is None or active_screen != 0:
        return False
    x, y = point
    button_x, button_y, button_width, button_height = CALIBRATE_RECT
    return (
        button_x <= x < button_x + button_width
        and button_y <= y < button_y + button_height
    )


def touch_corner_view_at(point):
    if point is None:
        return None
    x, y = point
    if CORNER_TABS_Y <= y < CORNER_TABS_Y + NAV_HEIGHT:
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


# Main-loop state, updated by step().
last_state = None
last_attitude = None
last_level = None
last_render_ms = 0
screen_initialized = False
last_battery_request_ms = None
last_battery_percent = None
touch_was_down = False


def setup():
    """Create the display, strip buffer, sensor client, and touch reader."""
    global lcd, g, screen_graphics, page_renderer, sensor, touch
    global pitch_zero, roll_zero

    print("Starting MostlyLevel dashboard")

    lcd = ILI9341()
    lcd.backlight(True)
    g = Graphics(lcd)
    screen_graphics = g
    page_renderer = create_page_renderer()
    sensor = WT901BLEClient()
    try:
        touch = TouchInput()
        print("Touchscreen ready.")
    except Exception as exc:
        touch = None
        print("Touchscreen unavailable:", exc)

    pitch_zero, roll_zero = load_level_reference()
    i18n.start()
    sensor.start()


def step():
    """Run one pass of the main loop: status, redraws, and touch input."""
    global last_battery_request_ms, last_battery_percent, last_state
    global last_attitude, last_level, last_render_ms, screen_initialized
    global level_frame_active, active_screen, corner_view, touch, touch_was_down

    sensor.maintain()
    if sensor.failed_recoveries >= SENSOR_RECOVERY_RESET_COUNT:
        print("Sensor link did not recover; restarting the board.")
        machine.reset()

    now = time.ticks_ms()
    state = sensor.state

    if sensor.latest is not None:
        if time.ticks_diff(now, sensor.last_packet_ms) > SENSOR_STALE_MS:
            state = "NO DATA"
        else:
            state = "LIVE"
    elif state == "LIVE":
        state = "WAIT"
    elif sensor.link_lost and state != "ERROR":
        # The client rescans and reconnects by itself; until notifications
        # run again, report the lost link rather than a first-time wait.
        state = "DISCONNECTED"

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
                # A redraw allocates a few hundred small tuples. Collecting
                # first is faster than the repeated emergency collections a
                # fragmented heap otherwise triggers during the redraw.
                gc.collect()
                draw_horizon_page(pitch, roll, display_values, level_now)
            else:
                update_corner_heights(sensor.latest)
            last_attitude = attitude
            last_level = level_now
            last_render_ms = time.ticks_ms()

    if touch is not None:
        try:
            touch_point = touch.read()
            if hold_target is not None:
                update_hold(touch_point, now, state)
            elif touch_point is not None and not touch_was_down:
                selected_screen = touch_screen_at(touch_point)
                held = held_button_at(touch_point)
                if held is not None:
                    start_hold(held, now)
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


def calibrate_now(state):
    """Save the live attitude as level, or explain why that is not possible."""
    global level_frame_active, last_attitude, last_level, last_render_ms
    if state == "LIVE" and set_level_reference(sensor.latest):
        display_values, pitch, roll = vehicle_values(sensor.latest)
        level_frame_active = is_level(pitch, roll)
        draw_dashboard(sensor.latest, state)
        last_attitude = (pitch, roll)
        last_level = level_frame_active
        last_render_ms = time.ticks_ms()
    else:
        draw_sensor_warning(state, t("warning_calibrate_needs_sensor"))


def held_button_at(point):
    if touch_language_at(point):
        return "language"
    if touch_calibrate_at(point):
        return "calibrate"
    return None


def start_hold(target, now):
    global hold_target, hold_start_ms, hold_progress
    hold_target = target
    hold_start_ms = now
    hold_progress = 0


def update_hold(point, now, state):
    """Track a long press on CALIBRATE or the language button.

    The button acts once it has been held for LONG_PRESS_MS; releasing it
    or sliding off earlier cancels. A bar along the button shows progress.
    """
    global hold_target, hold_start_ms, hold_progress
    if point is None or held_button_at(point) != hold_target:
        hold_target_was = hold_target
        hold_progress = 0
        if hold_target_was is not None:
            draw_held_button()
        hold_target = None
        return

    held_ms = time.ticks_diff(now, hold_start_ms)
    if held_ms >= LONG_PRESS_MS:
        target = hold_target
        hold_progress = 0
        draw_held_button()  # Clear the bar; not every action redraws.
        hold_target = None
        if target == "language":
            switch_language(sensor.latest, state)
        else:
            calibrate_now(state)
        return

    progress = held_ms * HOLD_STEPS // LONG_PRESS_MS
    if progress != hold_progress:
        hold_progress = progress
        draw_held_button()


def report_error(where, exc):
    print("%s failed: %r" % (where, exc))
    if hasattr(sys, "print_exception"):
        sys.print_exception(exc)


def run():
    """Run the dashboard; recover from errors instead of freezing the screen.

    An unexpected error would otherwise end the program and leave the last
    image on screen, possibly a green level frame with no stale-data warning.
    Ctrl+C (KeyboardInterrupt) is not an Exception and still stops the loop.
    """
    global screen_initialized

    try:
        setup()
    except Exception as exc:
        report_error("Setup", exc)
        print("Restarting in %d s." % (SETUP_ERROR_RESET_MS // 1000))
        time.sleep_ms(SETUP_ERROR_RESET_MS)
        machine.reset()

    failures = 0
    while True:
        try:
            step()
            failures = 0
        except Exception as exc:
            failures += 1
            report_error("Main loop step", exc)
            if failures >= STEP_ERROR_RESET_COUNT:
                print("%d errors in a row; restarting the board." % failures)
                machine.reset()
            # The failed step may have stopped mid-draw: redraw everything.
            screen_initialized = False
            time.sleep_ms(STEP_ERROR_RETRY_MS)
        time.sleep_ms(30)
