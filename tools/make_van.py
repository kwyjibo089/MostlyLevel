#!/usr/bin/env python3
"""Generate src/van_sprite.py, the camper drawn on the HORIZON page.

The van is painted from simple shapes (rounded boxes, polygons, circles) on a
small pixel canvas, given a 1-pixel dark outline, and turned into filled
rects with identical runs on adjacent rows merged. Doing this on the desktop
keeps the board from spending startup time on it.

Usage:
  tools/make_van.py                  # rewrite src/van_sprite.py
  tools/make_van.py --check          # exit 1 if src/van_sprite.py is stale
  tools/make_van.py --preview van.ppm  # also write an 8x zoomed preview
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from graphics import merge_runs  # noqa: E402

TARGET = ROOT / "src" / "van_sprite.py"
WIDTH, HEIGHT = 76, 40

# RGB565 colours, matching app.py where the same colour is used there.
DARK = 0x2104
BODY = 0xFFFF
GLASS = 0x35BF
TRIM = 0x7BEF
TYRE = 0x0000
HUB = 0xC618
HEADLIGHT = 0xFFE0
TAIL_LIGHT = 0xF800

canvas = [[None] * WIDTH for _ in range(HEIGHT)]


def put(x, y, colour):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        canvas[y][x] = colour


def rect(x0, y0, x1, y1, colour):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, colour)


def rounded(x0, y0, x1, y1, radius, colour, bottom_radius=None):
    """Fill a box with rounded corners; pixel centres decide coverage."""
    for y in range(y0, y1 + 1):
        r = radius if bottom_radius is None or y < (y0 + y1) / 2 else bottom_radius
        for x in range(x0, x1 + 1):
            cx = min(max(x + 0.5, x0 + r), x1 + 1 - r)
            cy = min(max(y + 0.5, y0 + r), y1 + 1 - r)
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                put(x, y, colour)


def circle(cx, cy, radius, colour):
    for y in range(int(cy - radius) - 1, int(cy + radius) + 2):
        for x in range(int(cx - radius) - 1, int(cx + radius) + 2):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= radius * radius:
                put(x, y, colour)


def polygon(points, colour):
    """Even-odd scanline fill through pixel centres."""
    for y in range(HEIGHT):
        yc = y + 0.5
        crossings = []
        for (xa, ya), (xb, yb) in zip(points, points[1:] + points[:1]):
            if (ya <= yc < yb) or (yb <= yc < ya):
                crossings.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
        crossings.sort()
        for xa, xb in zip(crossings[::2], crossings[1::2]):
            for x in range(WIDTH):
                if xa <= x + 0.5 < xb:
                    put(x, y, colour)


def paint():
    """Paint the van facing right; (1, 2) leaves room for the outline."""
    ox, oy = 1, 2

    def at(points):
        return [(x + ox, y + oy) for x, y in points]

    # Camper box, cab with sloped windscreen and short bonnet.
    rounded(2 + ox, 2 + oy, 52 + ox, 27 + oy, 5, BODY, bottom_radius=2)
    polygon(at([(48, 9), (59, 9), (66, 17), (71, 19.5), (72, 22), (72, 28), (48, 28)]), BODY)
    rect(20 + ox, 0 + oy, 31 + ox, 1 + oy, TRIM)  # Roof vent.
    # Two habitation windows and the cab side window.
    rounded(7 + ox, 6 + oy, 21 + ox, 13 + oy, 1.5, GLASS)
    rounded(25 + ox, 6 + oy, 42 + ox, 13 + oy, 1.5, GLASS)
    polygon(at([(50, 11), (58, 11), (64, 18), (64, 19), (50, 19)]), GLASS)
    rect(46 + ox, 12 + oy, 46 + ox, 20 + oy, TRIM)  # Sliding door seam.
    rect(42 + ox, 17 + oy, 44 + ox, 17 + oy, TRIM)  # Door handle.
    rect(3 + ox, 21 + oy, 71 + ox, 22 + oy, TRIM)  # Accent stripe.
    rect(69 + ox, 19 + oy, 71 + ox, 20 + oy, HEADLIGHT)
    rect(2 + ox, 15 + oy, 3 + ox, 18 + oy, TAIL_LIGHT)
    rounded(65 + ox, 25 + oy, 72 + ox, 28 + oy, 1, TRIM)  # Front bumper.
    # Wheel arches (cut out, then outlined), tyres, rims, and hubs.
    for wheel_x in (16, 58):
        cx, cy = wheel_x + ox, 29 + oy
        circle(cx, cy, 7.5, None)
        circle(cx, cy, 6.5, TYRE)
        circle(cx, cy, 4.0, TRIM)
        circle(cx, cy, 1.6, HUB)

    # Outline: empty cells touching the van, also diagonally, turn dark.
    solid = [[colour is not None for colour in row] for row in canvas]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if not solid[y][x] and any(
                0 <= x + dx < WIDTH and 0 <= y + dy < HEIGHT and solid[y + dy][x + dx]
                for dx in (-1, 0, 1)
                for dy in (-1, 0, 1)
            ):
                canvas[y][x] = DARK


def rects():
    """Return (x, y, width, height, colour) rects covering the canvas."""
    result = []
    for colour in sorted({c for row in canvas for c in row if c is not None}):
        lines = []
        for row in canvas:
            runs = []
            x = 0
            while x < WIDTH:
                if row[x] == colour:
                    start = x
                    while x < WIDTH and row[x] == colour:
                        x += 1
                    runs.append((start, x - start))
                else:
                    x += 1
            lines.append(runs)
        for x, y, width, height in merge_runs(lines):
            result.append((x, y, width, height, colour))
    return sorted(result, key=lambda item: (item[1], item[0]))


def source():
    """Return src/van_sprite.py: a palette and packed GS4_HMSB pixel rows."""
    colours = sorted({c for row in canvas for c in row if c is not None})
    index = {colour: number + 1 for number, colour in enumerate(colours)}
    packed = bytearray()
    for row in canvas:
        values = [index.get(colour, 0) for colour in row] + [0]
        for x in range(0, WIDTH, 2):
            packed.append(values[x] << 4 | values[x + 1])  # High nibble: left pixel.
    lines = [
        '"""The HORIZON camper as a 4-bit picture. Generated by tools/make_van.py;',
        'do not edit."""',
        "",
        "VAN_WIDTH = %d" % WIDTH,
        "VAN_HEIGHT = %d" % HEIGHT,
        "# RGB565 colour per pixel value; 0 is transparent.",
        "VAN_COLOURS = (None, %s)" % ", ".join("0x%04X" % colour for colour in colours),
        "# GS4_HMSB rows, %d bytes each." % ((WIDTH + 1) // 2),
        "VAN_PIXELS = (",
    ]
    for offset in range(0, len(packed), 19):
        chunk = packed[offset:offset + 19]
        lines.append('    b"%s"' % "".join("\\x%02x" % byte for byte in chunk))
    lines += [")", ""]
    return "\n".join(lines)


def write_preview(path, scale=8, background=(33, 146, 255)):
    def rgb(colour):
        if colour is None:
            return background
        red, green, blue = colour >> 11, colour >> 5 & 63, colour & 31
        return red * 255 // 31, green * 255 // 63, blue * 255 // 31

    with open(path, "w") as preview:
        preview.write("P3\n%d %d\n255\n" % (WIDTH * scale, HEIGHT * scale))
        for row in canvas:
            line = " ".join("%d %d %d" % rgb(colour) for colour in row for _ in range(scale))
            for _ in range(scale):
                preview.write(line + "\n")


def main(args):
    paint()
    text = source()
    if "--preview" in args:
        write_preview(args[args.index("--preview") + 1])
    if "--check" in args:
        if TARGET.read_text() != text:
            print("src/van_sprite.py is out of date; run tools/make_van.py", file=sys.stderr)
            return 1
        return 0
    TARGET.write_text(text)
    print("Wrote %s (%d rects as a picture)" % (TARGET.relative_to(ROOT), len(rects())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
