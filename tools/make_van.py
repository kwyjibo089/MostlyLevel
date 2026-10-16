#!/usr/bin/env python3
"""Generate src/van_sprite.py, the camper drawn on the HORIZON page.

The shape follows a Fiat Ducato panel-van campervan (proportions of an
L3H2: ~5.4 m long, 3.45 m wheelbase): high roof curving into a steeply raked
windscreen, very short bonnet, big black bumper, black wheel-arch trims and
side strip, sliding door, and dark-tinted camper windows. No logo.

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
WIDTH, HEIGHT = 80, 42

# RGB565 colours, matching app.py where the same colour is used there.
DARK = 0x2104
BODY = 0xFFFF
GLASS = 0x35BF
TRIM = 0x7BEF
TYRE = 0x0000
HUB = 0xC618
HEADLIGHT = 0xFFE0
TAIL_LIGHT = 0xF800
PLASTIC = 0x18E3  # Black bumpers, trims, and window frames.
TINT = 0x3186  # Dark-tinted camper windows.
LENS = 0xE73C  # Clear headlight lens.

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

    sill = 31  # Bottom edge of the body.
    rear_wheel, front_wheel = 15, 61  # 46 px wheelbase, short overhangs.

    # Body: high roof with rounded rear corner, roof curving down into the
    # raked windscreen, very short sloped bonnet, upright nose.
    polygon(at([
        (2, 8), (2.4, 5.5), (3.6, 3.6), (5.5, 2.4), (8, 2), (50, 2), (54, 2.5), (57, 4), (59, 6),
        (67, 17), (71, 19), (73, 20.5), (74.5, 22.5), (75, 24),
        (75, sill), (2, sill),
    ]), BODY)
    rect(22 + ox, 0 + oy, 30 + ox, 1 + oy, TRIM)  # Roof vent.

    # Windows: tinted camper windows in black frames; clear cab window.
    rounded(8 + ox, 6 + oy, 28 + ox, 16 + oy, 2, PLASTIC)
    rounded(9 + ox, 7 + oy, 27 + ox, 15 + oy, 1.5, TINT)
    rounded(36 + ox, 6 + oy, 48 + ox, 16 + oy, 2, PLASTIC)
    rounded(37 + ox, 7 + oy, 47 + ox, 15 + oy, 1.5, TINT)
    polygon(at([(51, 7), (57.5, 7), (64, 16.5), (51, 16.5)]), PLASTIC)
    polygon(at([(52, 8), (57, 8), (62.5, 15.5), (52, 15.5)]), GLASS)
    polygon(at([(61, 11), (64.5, 11.5), (64.5, 16), (62, 16)]), PLASTIC)  # Mirror.

    # Panel lines: sliding door, B-pillar, and the sliding-door rail.
    rect(34 + ox, 4 + oy, 34 + ox, 29 + oy, TRIM)
    rect(50 + ox, 6 + oy, 50 + ox, 29 + oy, TRIM)
    rect(5 + ox, 18 + oy, 33 + ox, 18 + oy, TRIM)
    rect(36 + ox, 20 + oy, 38 + ox, 20 + oy, TRIM)  # Sliding door handle.
    rect(52 + ox, 19 + oy, 54 + ox, 19 + oy, TRIM)  # Cab door handle.

    # Lights: big swept-back headlight, upright rear lights.
    polygon(at([(65.5, 17), (73, 19.8), (75, 23.8), (66.5, 21.8)]), PLASTIC)
    polygon(at([(67, 18.2), (72.5, 20.4), (73.8, 22.9), (67.6, 21)]), LENS)
    rect(72 + ox, 21 + oy, 73 + ox, 22 + oy, HEADLIGHT)
    rect(2 + ox, 19 + oy, 3 + ox, 27 + oy, TAIL_LIGHT)

    # Black plastic: front bumper, rear bumper corner, side strip.
    polygon(at([(68, 24), (75, 24), (75, sill), (69, sill)]), PLASTIC)
    rect(2 + ox, 28 + oy, 6 + ox, sill - 1 + oy, PLASTIC)
    rect(24 + ox, 25 + oy, 52 + ox, 26 + oy, PLASTIC)

    # Wheel arches with black trims, then tyres, steel rims, and hubs.
    for wheel_x in (rear_wheel, front_wheel):
        cx, cy = wheel_x + ox, sill + oy
        for y in range(HEIGHT):
            for x in range(WIDTH):
                distance = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2
                if distance <= 8.5 ** 2 and y < sill + oy:
                    canvas[y][x] = PLASTIC if distance > 7.5 ** 2 else None
        circle(cx, cy, 6.5, TYRE)
        circle(cx, cy, 4.2, TRIM)
        circle(cx, cy, 2.0, HUB)

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
        "VAN_COLOURS = (",
        "    None,",
    ]
    lines += ["    0x%04X," % colour for colour in colours]
    lines += [
        ")",
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
