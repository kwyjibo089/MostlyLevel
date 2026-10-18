#!/usr/bin/env python3
"""Write the app icon's SVG layers to assets/icon/ (1024 × 1024).

The icon: the camper seen from behind in an attitude indicator (sky, ground,
horizon, bank scale), with a level vial centred in the ground. As an Android
adaptive icon, launchers show only the central 683 px and keep the circle of
radius 313 uncropped, so the motif stays inside it. make-icons.mjs renders
these layers to the PNGs in assets/.

Usage: python3 scripts/app_icon.py
"""

import math
import pathlib

import van_drawings

OUT = pathlib.Path(__file__).resolve().parents[1] / "assets" / "icon"
GREEN = "#4ADE80"
WHITE = "#F4F7FA"
HORIZON_Y = 600
VIAL_Y = 727  # Centre of the visible ground: between the horizon and the crop's lower edge (853.5).

GRADIENTS = """<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#4AA6FF"/><stop offset="1" stop-color="#1C6FD4"/></linearGradient>
<linearGradient id="earth" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#C08024"/><stop offset="1" stop-color="#7E4C10"/></linearGradient>"""


def background():
    return ('<rect width="1024" height="%d" fill="url(#sky)"/>'
            '<rect y="%d" width="1024" height="%d" fill="url(#earth)"/>') % (HORIZON_Y + 10, HORIZON_Y, 1024 - HORIZON_Y)


def foreground(mono=False):
    w = WHITE
    out = "" if mono else '<rect x="0" y="%d" width="1024" height="12" fill="#FFFFFF"/>' % (HORIZON_Y - 6)
    # Bank scale: an arc with five ticks and the pointer at the top.
    cx, cy, r = 512, HORIZON_Y, 292
    a0, a1 = math.radians(-140), math.radians(-40)
    out += ('<path d="M%.1f %.1f A%d %d 0 0 1 %.1f %.1f" fill="none" stroke="%s" stroke-width="16" '
            'stroke-linecap="round"/>') % (cx + r * math.cos(a0), cy + r * math.sin(a0), r, r,
                                            cx + r * math.cos(a1), cy + r * math.sin(a1), w)
    for deg, length in ((-90, 46), (-70, 30), (-110, 30), (-50, 30), (-130, 30)):
        a = math.radians(deg)
        out += ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="14" '
                'stroke-linecap="round"/>') % (cx + r * math.cos(a), cy + r * math.sin(a),
                                                cx + (r - length) * math.cos(a), cy + (r - length) * math.sin(a), w)
    out += '<path d="M512 352 L490 392 L534 392 Z" fill="%s"/>' % w
    # The camper from behind, standing on the horizon.
    body = "M392 572 L392 396 Q392 366 422 366 L602 366 Q632 366 632 396 L632 572 Z"
    if mono:
        out += '<path d="%s" fill="%s"/>' % (body, w)
        out += ('<rect x="404" y="560" width="42" height="40" rx="10" fill="%s"/>'
                '<rect x="578" y="560" width="42" height="40" rx="10" fill="%s"/>') % (w, w)
    else:
        out += ('<rect x="404" y="556" width="42" height="46" rx="10" fill="#14171A"/>'
                '<rect x="578" y="556" width="42" height="46" rx="10" fill="#14171A"/>')
        out += '<path d="%s" fill="#F6F7F9"/><path d="%s" fill="url(#shade)"/>' % (body, body)
        out += ('<rect x="412" y="386" width="92" height="74" rx="12" fill="url(#glass)"/>'
                '<rect x="520" y="386" width="92" height="74" rx="12" fill="url(#glass)"/>')
        out += '<line x1="512" y1="378" x2="512" y2="540" stroke="rgba(0,0,0,0.35)" stroke-width="4"/>'
        out += ('<rect x="392" y="468" width="16" height="72" rx="4" fill="url(#tail)"/>'
                '<rect x="616" y="468" width="16" height="72" rx="4" fill="url(#tail)"/>')
        out += ('<rect x="384" y="540" width="256" height="36" rx="10" fill="url(#plastic)"/>'
                '<rect x="480" y="548" width="64" height="18" rx="3" fill="#E9ECEF"/>')
        out += '<rect x="488" y="368" width="48" height="8" rx="3" fill="url(#tail)"/>'
    # The level vial with its bubble centred.
    y = VIAL_Y
    out += '<rect x="392" y="%d" width="240" height="64" rx="32" fill="%s" stroke="%s" stroke-width="14"/>' % (
        y - 32, "none" if mono else "#3A2508", w)
    for x in (478, 546):
        out += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="8" stroke-linecap="round"/>' % (
            x, y - 18, x, y + 18, w)
    out += '<ellipse cx="512" cy="%d" rx="28" ry="17" fill="%s"/>' % (y, w if mono else GREEN)
    if not mono:
        out += '<ellipse cx="504" cy="%d" rx="10" ry="5" fill="#C9F7DA"/>' % (y - 7)
    return out


def svg(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">'
            "<defs>%s%s</defs>%s</svg>\n") % (van_drawings.DEFS, GRADIENTS, body)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, body in (("background", background()), ("foreground", foreground()),
                       ("monochrome", foreground(mono=True))):
        (OUT / ("%s.svg" % name)).write_text(svg(body))
        print("Wrote assets/icon/%s.svg" % name)


if __name__ == "__main__":
    main()
