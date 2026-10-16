#!/usr/bin/env python3
"""Generate src/van_shapes.py, the HORIZON vans as packed shapes.

The shapes follow a Fiat Ducato panel-van campervan (L3H2 proportions: about
5.4 m long, 3.45 m wheelbase), seen from the right and from behind. No logo.
Coordinates are pixels, y down, with the wheels standing on y = ground. This
runs on the desktop so the board only loads small integer tables: shape code
and float constants would otherwise stay in its RAM. src/vans.py rotates and
draws them.

Usage:
  tools/make_vans.py           # rewrite src/van_shapes.py
  tools/make_vans.py --check   # exit 1 if src/van_shapes.py is stale
"""

import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "van_shapes.py"

DARK = 0x2104
BODY = 0xFFFF
GLASS = 0x35BF
TRIM = 0x7BEF
TYRE = 0x0000
HUB = 0xC618
AMBER = 0xFD20
HEADLIGHT = 0xFFE0
TAIL_LIGHT = 0xF800
PLASTIC = 0x18E3  # Black bumpers, trims, and window frames.
TINT = 0x3186  # Dark-tinted camper windows.
LENS = 0xE73C  # Clear headlight lens and number plate.
COLOURS = [
    None, DARK, BODY, GLASS, TRIM, TYRE, HUB, AMBER, HEADLIGHT, TAIL_LIGHT, PLASTIC, TINT, LENS,
]
CLEAR = None  # Pixel value 0: transparent, used to cut out wheel arches.


def box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rounded_box(x0, y0, x1, y1, radius, steps=3):
    """Polygon of a box whose corners are quarter circles."""
    points = []
    corners = (
        (x1 - radius, y0 + radius, -90),
        (x1 - radius, y1 - radius, 0),
        (x0 + radius, y1 - radius, 90),
        (x0 + radius, y0 + radius, 180),
    )
    for cx, cy, start in corners:
        for step in range(steps + 1):
            angle = math.radians(start + 90 * step / steps)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def half_ring(cx, cy, outer, inner, steps=8):
    """Upper half of a ring (a wheel-arch trim)."""
    top = [
        (cx + outer * math.cos(math.pi + math.pi * i / steps),
         cy + outer * math.sin(math.pi + math.pi * i / steps))
        for i in range(steps + 1)
    ]
    bottom = [
        (cx + inner * math.cos(-math.pi * i / steps), cy + inner * math.sin(-math.pi * i / steps))
        for i in range(steps + 1)
    ]
    return top + bottom


def half_disc(cx, cy, radius, steps=8):
    return [
        (cx + radius * math.cos(math.pi + math.pi * i / steps),
         cy + radius * math.sin(math.pi + math.pi * i / steps))
        for i in range(steps + 1)
    ]


# Points are stored in quarter pixels, as small integers: on the board every
# float result is a new heap object, so rotating with integers is far faster.
SUBPIXEL = 4


def quarter(value):
    return int(value * SUBPIXEL + 0.5 if value >= 0 else value * SUBPIXEL - 0.5)


KINDS = ("poly", "outline", "line", "disc")


def view(ground, wheels, shapes):
    """Pack a view: all points in one tuple of quarter pixels; per shape
    (kind, pixel value, first point, point count, radius in pixels). A disc
    keeps one point (its centre)."""
    points = []
    packed = []
    for kind, colour, data in shapes:
        start = len(points) // 2
        if kind == "disc":
            corners = [(data[0], data[1])]
            radius = int(data[2] + 0.5)
        elif kind == "line":
            corners = [(data[0], data[1]), (data[2], data[3])]
            radius = 0
        else:
            corners = data
            radius = 0
        for x, y in corners:
            points += [quarter(x), quarter(y)]
        packed.append((KINDS.index(kind), COLOURS.index(colour), start, len(corners), radius))
    return {
        "ground": quarter(ground),
        "wheels": (quarter(wheels[0]), quarter(wheels[1])),
        "points": points,
        "shapes": packed,
    }


def _side_view():
    """Side view from the right, front to the right: the passenger side
    with the sliding door, as on European vans."""
    _SIDE_BODY = [
        (2, 8), (2.4, 5.5), (3.6, 3.6), (5.5, 2.4), (8, 2), (50, 2), (54, 2.5), (57, 4), (59, 6),
        (67, 17), (71, 19), (73, 20.5), (74.5, 22.5), (75, 24), (75, 31), (2, 31),
    ]
    _SIDE_SHAPES = [
        ("poly", BODY, _SIDE_BODY),
        ("poly", TRIM, box(22, 0, 31, 2)),  # Roof vent.
        # Tinted window in the sliding door (none further back) and the cab
        # window, both in black frames; the door mirror.
        ("poly", PLASTIC, rounded_box(36, 6, 49, 17, 2)),
        ("poly", TINT, rounded_box(37, 7, 48, 16, 1.5)),
        ("poly", PLASTIC, [(51, 7), (57.5, 7), (64, 16.5), (51, 16.5)]),
        ("poly", GLASS, [(52, 8), (57, 8), (62.5, 15.5), (52, 15.5)]),
        ("poly", PLASTIC, [(61, 11), (64.5, 11.5), (64.5, 16), (62, 16)]),
        # Panel lines: sliding door, B-pillar, sliding-door rail, handles.
        ("line", TRIM, (34, 4, 34, 29)),
        ("line", TRIM, (50, 6, 50, 29)),
        ("line", TRIM, (5, 18, 33, 18)),
        ("line", TRIM, (36, 20, 38, 20)),
        ("line", TRIM, (52, 19, 54, 19)),
        # Big swept-back headlight, upright rear light.
        ("poly", PLASTIC, [(65.5, 17), (73, 19.8), (75, 23.8), (66.5, 21.8)]),
        ("poly", LENS, [(67, 18.2), (72.5, 20.4), (73.8, 22.9), (67.6, 21)]),
        ("poly", HEADLIGHT, box(72, 21, 74, 23)),
        ("poly", TAIL_LIGHT, box(2, 19, 4, 28)),
        # Black plastic: front bumper, rear bumper corner, side strip.
        ("poly", PLASTIC, [(68, 24), (75, 24), (75, 31), (69, 31)]),
        ("poly", PLASTIC, box(2, 28, 7, 31)),
        ("poly", PLASTIC, box(24, 25, 53, 27)),
        ("outline", DARK, _SIDE_BODY),
    ]
    for _wheel_x in (15, 61):
        _SIDE_SHAPES += [
            ("poly", PLASTIC, half_ring(_wheel_x, 31, 8.5, 7.5)),  # Arch trim.
            ("poly", CLEAR, half_disc(_wheel_x, 31, 7.5)),  # Arch opening.
            ("disc", TYRE, (_wheel_x, 31, 6.5)),
            ("disc", TRIM, (_wheel_x, 31, 4.2)),  # Steel rim.
            ("disc", HUB, (_wheel_x, 31, 2.0)),
        ]
    return view(37.5, (15, 61), _SIDE_SHAPES)


def _rear_view():
    """Rear view: the vehicle's left side is on the left, as seen from behind."""
    _REAR_BODY = [
        (0, 6), (1, 3), (3, 1), (6, 0), (40, 0), (43, 1), (45, 3), (46, 6), (46, 41), (0, 41),
    ]
    return view(52, (7.5, 38.5), [
        # Tyres first: the bumper covers their tops.
        ("poly", TYRE, rounded_box(3, 43, 12, 52, 2)),
        ("poly", TYRE, rounded_box(34, 43, 43, 52, 2)),
        ("poly", BODY, _REAR_BODY),
        ("poly", TRIM, box(16, -2, 30, 0)),  # Roof vent.
        # Rear door windows, tinted in black frames, and the door split.
        ("poly", PLASTIC, rounded_box(3, 4, 22, 18, 2)),
        ("poly", TINT, rounded_box(4, 5, 21, 17, 1.5)),
        ("poly", PLASTIC, rounded_box(24, 4, 43, 18, 2)),
        ("poly", TINT, rounded_box(25, 5, 42, 17, 1.5)),
        ("line", TRIM, (23, 3, 23, 39)),
        ("poly", TRIM, box(19, 24, 22, 25)),  # Door handles.
        ("poly", TRIM, box(24, 24, 27, 25)),
        # Tall rear lights with an amber indicator at the top.
        ("poly", TAIL_LIGHT, box(0, 24, 3, 39)),
        ("poly", TAIL_LIGHT, box(43, 24, 46, 39)),
        ("poly", AMBER, box(0, 24, 3, 28)),
        ("poly", AMBER, box(43, 24, 46, 28)),
        ("outline", DARK, _REAR_BODY),
        # Wide black bumper with the number plate.
        ("poly", PLASTIC, box(-1, 39, 47, 45)),
        ("poly", LENS, box(16, 40, 30, 44)),
    ])


def source():
    lines = [
        '"""HORIZON van shapes. Generated by tools/make_vans.py; do not edit.',
        "",
        "Points are quarter pixels (x, y pairs); shapes are (kind, pixel value,",
        "first point, point count, radius) with kinds poly, outline, line, disc.",
        '"""',
        "",
        "COLOURS = (",
    ]
    lines += ["    None,"] + ["    0x%04X," % colour for colour in COLOURS[1:]] + [")"]
    for name, van in (("SIDE", _side_view()), ("REAR", _rear_view())):
        lines += [
            "",
            "%s_GROUND = %d" % (name, van["ground"]),
            "%s_WHEELS = (%d, %d)" % ((name,) + van["wheels"]),
            "%s_POINTS = (" % name,
        ]
        points = van["points"]
        for offset in range(0, len(points), 16):
            row = points[offset:offset + 16]
            lines.append("    " + ", ".join(str(value) for value in row) + ",")
        lines += [")", "%s_SHAPES = (" % name]
        lines += ["    (%d, %d, %d, %d, %d)," % shape for shape in van["shapes"]]
        lines.append(")")
    return "\n".join(lines) + "\n"


def main(args):
    text = source()
    if "--check" in args:
        if TARGET.read_text() != text:
            print("src/van_shapes.py is out of date; run tools/make_vans.py", file=sys.stderr)
            return 1
        return 0
    TARGET.write_text(text)
    print("Wrote %s" % TARGET.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
