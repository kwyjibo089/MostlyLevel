"""Detailed camper drawings (side, rear, top) as SVG, in centimetres.

Used by make_van_art.py, which turns them into src/vanArt.ts for the app.

Side views: x from the rear (0) to the front, ground y = 0, up is negative.
Rear views: centred on x = 0. Top views: front at the top, centred on x = 0.
Body colour comes from one fill; shading is a colour-independent overlay.
"""

import math

DEFS = """
<linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#fff" stop-opacity="0.38"/>
  <stop offset="0.12" stop-color="#fff" stop-opacity="0.12"/>
  <stop offset="0.5" stop-color="#000" stop-opacity="0"/>
  <stop offset="0.85" stop-color="#000" stop-opacity="0.10"/>
  <stop offset="1" stop-color="#000" stop-opacity="0.22"/>
</linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="0.35" y2="1">
  <stop offset="0" stop-color="#5a7387"/>
  <stop offset="0.45" stop-color="#2a3a48"/>
  <stop offset="1" stop-color="#141c24"/>
</linearGradient>
<linearGradient id="tint" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#3a4550"/>
  <stop offset="1" stop-color="#11161b"/>
</linearGradient>
<radialGradient id="tyre" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0.6" stop-color="#2c3036"/>
  <stop offset="0.85" stop-color="#1a1d21"/>
  <stop offset="1" stop-color="#0c0e10"/>
</radialGradient>
<radialGradient id="rim" cx="0.42" cy="0.38" r="0.7">
  <stop offset="0" stop-color="#f2f4f6"/>
  <stop offset="0.55" stop-color="#b9c0c8"/>
  <stop offset="1" stop-color="#7d858f"/>
</radialGradient>
<linearGradient id="plastic" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#3a3e44"/>
  <stop offset="1" stop-color="#1b1e22"/>
</linearGradient>
<linearGradient id="awning" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#f4f6f8"/>
  <stop offset="1" stop-color="#b8bec6"/>
</linearGradient>
<linearGradient id="lamp" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#ffffff"/>
  <stop offset="1" stop-color="#c9d2dc"/>
</linearGradient>
<linearGradient id="tail" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ff6b5e"/>
  <stop offset="1" stop-color="#b3221a"/>
</linearGradient>
<linearGradient id="smoked" x1="0" y1="0" x2="0.3" y2="1">
  <stop offset="0" stop-color="#5d6773"/>
  <stop offset="0.5" stop-color="#2c333b"/>
  <stop offset="1" stop-color="#171b20"/>
</linearGradient>
<radialGradient id="shadow" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="#000" stop-opacity="0.42"/>
  <stop offset="0.7" stop-color="#000" stop-opacity="0.16"/>
  <stop offset="1" stop-color="#000" stop-opacity="0"/>
</radialGradient>
<linearGradient id="solar" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#2d3e5c"/>
  <stop offset="1" stop-color="#121a28"/>
</linearGradient>
"""

PLASTIC = "#23262a"
SEAM = "rgba(0,0,0,0.28)"
HIGHLIGHT = "rgba(255,255,255,0.55)"


def f(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def path(d, fill, extra=""):
    return '<path d="%s" fill="%s"%s/>' % (d, fill, extra)


def rrect(x, y, w, h, r, fill, extra=""):
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s/>' % (
        f(x), f(y), f(w), f(h), f(r), fill, extra)


def line(d, stroke=SEAM, width=1.2):
    return '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (
        d, stroke, width)


def body(d, colour):
    """Body in its colour plus the shading overlay and a thin outline."""
    return (path(d, colour) + path(d, "url(#shade)")
            + '<path d="%s" fill="none" stroke="rgba(0,0,0,0.35)" stroke-width="1"/>' % d)


def glass(d):
    return path(d, "url(#glass)") + path(d, "none", ' stroke="#0d1115" stroke-width="2.5"')


def camper_window(x, y, w, h, r=7):
    """Flush tinted camper window with a black frame and a soft reflection."""
    out = rrect(x - 3, y - 3, w + 6, h + 6, r + 3, "#15181c")
    out += rrect(x, y, w, h, r, "url(#tint)")
    out += path("M%s %s L%s %s L%s %s L%s %s Z" % (
        f(x + w * 0.18), f(y), f(x + w * 0.42), f(y), f(x + w * 0.12), f(y + h), f(x), f(y + h)),
        "rgba(255,255,255,0.07)")
    return out


def wheel(cx, r=35, cy=None):
    cy = -r if cy is None else cy
    out = '<circle cx="%s" cy="%s" r="%s" fill="url(#tyre)"/>' % (f(cx), f(cy), f(r))
    rr = r * 0.6
    out += '<circle cx="%s" cy="%s" r="%s" fill="url(#rim)"/>' % (f(cx), f(cy), f(rr))
    # Five spoke openings.
    for k in range(5):
        a = math.radians(k * 72 - 90)
        pts = []
        for rad, da in ((r * 0.2, -18), (r * 0.5, -13), (r * 0.5, 13), (r * 0.2, 18)):
            b = a + math.radians(da)
            pts.append("%s %s" % (f(cx + rad * math.cos(b)), f(cy + rad * math.sin(b))))
        out += path("M" + " L".join(pts) + " Z", "#3d434b")
    out += '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="#6c747e" stroke-width="1.2"/>' % (f(cx), f(cy), f(rr))
    out += '<circle cx="%s" cy="%s" r="%s" fill="url(#rim)"/>' % (f(cx), f(cy), f(r * 0.17))
    out += '<circle cx="%s" cy="%s" r="%s" fill="#5b626b"/>' % (f(cx), f(cy), f(r * 0.07))
    return out


def arch_shadow(cx, R=44, y=-34):
    return path("M%s %s A%s %s 0 0 1 %s %s Z" % (f(cx - R), f(y), R, R, f(cx + R), f(y)), "#0b0d10")


def flare(cx, R1=44, R2=51, y=-34):
    return path("M%s %s A%s %s 0 0 1 %s %s L%s %s A%s %s 0 0 0 %s %s Z" % (
        f(cx - R2), f(y), R2, R2, f(cx + R2), f(y), f(cx + R1), f(y), R1, R1, f(cx - R1), f(y)), "url(#plastic)")


def ground_shadow(x0, x1):
    cx, rx = (x0 + x1) / 2, (x1 - x0) / 2 + 12
    return '<ellipse cx="%s" cy="0" rx="%s" ry="8" fill="url(#shadow)"/>' % (f(cx), f(rx))


# ---------------------------------------------------------------- Ducato cab
def ducato_front(F, windscreen_top_y=-232):
    """Body outline of a Ducato-style front, from the windscreen top to the front arch.

    The bonnet is short and rises towards a strongly raked windscreen; the
    front is tall. F is the front bumper's x."""
    u = lambda d: F - d  # noqa: E731  distance back from the front
    return ("L%s %s L%s -124 Q%s -117 %s -107 Q%s -104 %s -96 L%s -74 L%s -48 Q%s -35 %s -35"
            % (f(u(154)), f(windscreen_top_y), f(u(70)), f(u(30)), f(u(10)), f(u(2)), f(u(2)),
               f(F), f(F), f(F), f(u(10))))


def ducato_cab_details(F, front_axle, windscreen_top_y=-232):
    u = lambda d: F - d  # noqa: E731
    wt = windscreen_top_y
    out = ""
    # Windscreen seen edge-on, just inside the A-pillar.
    out += glass("M%s %s L%s -124.5 L%s -127 L%s %s Z" % (
        f(u(154)), f(wt + 1), f(u(70.5)), f(u(84)), f(u(168)), f(wt + 10)))
    # Cab door window: its lower edge drops towards the front, ending at the mirror triangle.
    out += glass("M%s %s L%s %s L%s -142 L%s -149 L%s -139 Z" % (
        f(u(198)), f(wt + 14), f(u(158)), f(wt + 14), f(u(97)), f(u(103)), f(u(198))))
    out += path("M%s -149 L%s -142 L%s -139 L%s -152 Z" % (f(u(103)), f(u(97)), f(u(84)), f(u(90))), "#15181b")
    # Door seams, handle, and the black protective strip on the lower door.
    out += line("M%s %s L%s -42" % (f(u(200)), f(wt + 6), f(u(202))))
    out += line("M%s -120 Q%s -98 %s -84" % (f(u(74)), f(u(80)), f(u(72))))
    out += rrect(u(192), -133, 16, 5, 2.5, PLASTIC)
    out += rrect(u(200), -66, 200 - 54 - (F - front_axle), 12, 3, "url(#plastic)")
    # The large two-part mirror on its arm.
    out += path("M%s -146 L%s -150" % (f(u(92)), f(u(84))), "none",
                ' stroke="%s" stroke-width="5" stroke-linecap="round"' % PLASTIC)
    out += rrect(u(94), -196, 16, 44, 5, "url(#plastic)")
    out += rrect(u(93), -150, 14, 15, 4, "url(#plastic)")
    # The big swept headlight: tall at the front corner, tapering back along the bonnet edge.
    out += path("M%s -106 Q%s -112 %s -115 L%s -123 Q%s -121 %s -116 L%s -100 Q%s -88 %s -82 Z" % (
        f(u(2)), f(u(14)), f(u(32)), f(u(68)), f(u(64)), f(u(56)), f(u(30)), f(u(12)), f(u(2))), "#1b1e22")
    out += path("M%s -103 Q%s -108 %s -111 L%s -119 L%s -115 L%s -101 Q%s -91 %s -86 Z" % (
        f(u(5)), f(u(15)), f(u(32)), f(u(60)), f(u(54)), f(u(30)), f(u(14)), f(u(5))), "url(#smoked)")
    out += path("M%s -110 L%s -118 L%s -116 L%s -108 Z" % (f(u(34)), f(u(58)), f(u(55)), f(u(33))), "#9aa4af")
    out += '<circle cx="%s" cy="-98" r="8" fill="url(#rim)" stroke="#0f1215" stroke-width="1.6"/>' % f(u(16))
    out += '<circle cx="%s" cy="-98" r="3.4" fill="#ffffff"/>' % f(u(16))
    out += '<circle cx="%s" cy="-104" r="4.5" fill="url(#rim)" stroke="#0f1215" stroke-width="1.2"/>' % f(u(30))
    out += line("M%s -114 L%s -101 Q%s -91 %s -86" % (f(u(54)), f(u(30)), f(u(14)), f(u(6))), "#ffffff", 2.6)
    out += path("M%s -121 L%s -118 L%s -116 L%s -119 Z" % (f(u(66)), f(u(56)), f(u(53)), f(u(62))), "#ffb03b")
    # Black grille below the headlight, then the big bumper with fog light.
    out += path("M%s -82 L%s -84 L%s -74 L%s -74 Z" % (f(u(2)), f(u(1)), f(F), f(u(4))), "#15181b")
    out += line("M%s -79 L%s -79" % (f(u(3)), f(F)), "#5b626b", 1.2)
    out += path("M%s -74 L%s -74 Q%s -72 %s -62 L%s -35 L%s -35 Q%s -35 %s -48 Z" % (
        f(F), f(u(46)), f(u(52)), f(u(52)), f(u(50)), f(u(10)), f(F), f(F)), "url(#plastic)")
    out += '<circle cx="%s" cy="-56" r="5" fill="#d9dee4" stroke="#0f1113" stroke-width="2"/>' % f(u(16))
    out += rrect(u(40), -48, 30, 6, 3, "#121417")
    # Side indicator on the wing, wiper.
    out += rrect(u(64), -101, 8, 3.5, 1.5, "#ffb03b")
    out += line("M%s -124 L%s -138" % (f(u(76)), f(u(108))), "#1a1d21", 2)
    # Wide black arch flare.
    out += flare(front_axle, 44, 55)
    return out


# ------------------------------------------------------------------- types
def panel_side(colour):
    F, L = 636, 636
    rear_axle, front_axle = 138, 541.5
    d = ("M2 -40 L0 -232 Q0 -252 18 -252 L446 -252 Q474 -252 480 -240 "
         + ducato_front(F, -236)
         + " L%s -34 A44 44 0 0 0 %s -34 L182 -34 A44 44 0 0 0 94 -34 L12 -34 Q2 -34 2 -44 Z"
         % (f(front_axle + 44), f(front_axle - 44)))
    out = ground_shadow(0, L)
    out += arch_shadow(rear_axle) + arch_shadow(front_axle)
    out += body(d, colour)
    # Awning cassette, roof vent, solar panel.
    out += rrect(60, -256, 370, 16, 6, "url(#awning)", ' stroke="#8f979f" stroke-width="1"')
    out += rrect(56, -256, 10, 16, 3, "#9aa2ab") + rrect(424, -256, 10, 16, 3, "#9aa2ab")
    out += path("M190 -252 L196 -263 L244 -263 L250 -252 Z", "#d7dce1", ' stroke="#9aa2ab" stroke-width="1"')
    out += rrect(268, -258, 130, 6, 2, "url(#solar)")
    # Camper windows, sliding door, rail, handles.
    out += camper_window(36, -206, 112, 58)
    out += camper_window(206, -200, 58, 40)
    out += camper_window(302, -206, 88, 58)
    out += line("M286 -236 L286 -42 M404 -236 L404 -42")
    out += rrect(150, -144, 136, 5, 2, "#1b1e22")
    out += rrect(394, -134, 6, 14, 3, PLASTIC)
    # The stamped crease along the side panel, and the black strip on the lower side.
    out += line("M8 -105 L434 -105", "rgba(255,255,255,0.75)", 1.8)
    out += line("M8 -102.5 L434 -102.5", "rgba(0,0,0,0.2)", 1.3)
    out += rrect(rear_axle + 55, -66, 434 - rear_axle - 55, 12, 3, "url(#plastic)")
    # Rear bumper with step and tail light.
    out += path("M0 -64 L40 -64 L40 -34 L12 -34 Q2 -34 2 -44 Z", "url(#plastic)")
    out += rrect(-1, -152, 7, 74, 2, "url(#tail)")
    out += rrect(-1, -100, 7, 12, 2, "#ffb03b")
    out += flare(rear_axle, 44, 55)
    out += ducato_cab_details(F, front_axle, -236)
    out += wheel(rear_axle) + wheel(front_axle)
    return out, L


def motorhome_side(colour, kind):
    """Alcove, semi-integrated, or integrated on a Ducato-style chassis."""
    L = 720 if kind == "integrated" else 700
    H = 320 if kind == "alcove" else 292
    F = L
    front_axle = L - 95 if kind != "integrated" else L - 116
    rear_axle = front_axle - 403.5
    box_end = 500 if kind != "integrated" else 600
    floor = -64
    # Box outline from the rear bottom, over the roof, to the cab.
    d = "M6 -66 L0 -110 L0 %s Q0 %s 22 %s " % (f(-H + 24), f(-H), f(-H))
    if kind == "semi":
        d += "L%s %s C%s %s %s %s %s -232 " % (f(box_end - 30), f(-H), f(box_end + 40), f(-H), f(F - 170), f(-262), f(F - 154))
        d += ducato_front(F, -232)
    elif kind == "alcove":
        d += "L%s %s Q%s %s %s %s Q%s -238 %s -240 L%s -238 Q%s -236 %s -232 " % (
            f(F - 120), f(-H), f(F - 72), f(-H), f(F - 66), f(-262), f(F - 64), f(F - 96), f(F - 142), f(F - 150), f(F - 154))
        d += ducato_front(F, -232)
    else:  # integrated: full front with a big windscreen
        d += ("L%s %s Q%s %s %s %s L%s -128 Q%s -112 %s -96 L%s -46 Q%s -34 %s -34 " % (
            f(F - 80), f(-H), f(F - 42), f(-H), f(F - 32), f(-H + 26), f(F - 6), f(F - 2), f(F), f(F), f(F), f(F - 10)))
    d += "L%s -34 A44 44 0 0 0 %s -34 L%s -40 L%s -40 L%s -34 A44 44 0 0 0 %s -34 L%s -40 L40 -40 Z" % (
        f(front_axle + 44), f(front_axle - 44), f(front_axle - 50), f(rear_axle + 50), f(rear_axle + 44),
        f(rear_axle - 44), f(rear_axle - 50))
    d = d.replace(" L40 -40 Z", " L40 -46 Q14 -46 6 -66 Z")
    out = ground_shadow(0, L)
    out += arch_shadow(rear_axle) + arch_shadow(front_axle)
    out += body(d, colour)
    # Skirt and the floor line of the box.
    out += line("M8 %s L%s %s" % (f(floor), f(box_end), f(floor)), SEAM, 1.2)
    out += path("M%s -40 L%s -40 L%s -34 L%s -34 Z" % (f(rear_axle + 50), f(front_axle - 50), f(front_axle - 50), f(rear_axle + 50)), "url(#plastic)")
    # Decor swoosh along the lower body.
    out += path("M6 -96 C 160 -98 300 -78 %s -112 L%s -104 C 300 -70 160 -88 6 -86 Z" % (f(box_end + 40), f(box_end + 40)), "rgba(70,80,92,0.55)")
    # Awning, roof light, solar.
    out += rrect(70, -H - 4, 380, 17, 6, "url(#awning)", ' stroke="#8f979f" stroke-width="1"')
    out += path("M210 %s L218 %s L300 %s L308 %s Z" % (f(-H), f(-H - 14), f(-H - 14), f(-H)), "#d7dce1", ' stroke="#9aa2ab" stroke-width="1"')
    out += rrect(330, -H - 6, 120, 6, 2, "url(#solar)")
    # Hinged windows, entrance door with window, garage door, hatch.
    out += camper_window(46, -H + 76, 108, 60, 9)
    out += camper_window(214, -H + 76, 80, 60, 9)
    out += line("M%s %s L%s %s L%s -70 L%s -70 Z" % (f(box_end - 140), f(-H + 50), f(box_end - 86), f(-H + 50), f(box_end - 86), f(box_end - 140)), SEAM, 1.6)
    out += camper_window(box_end - 132, -H + 62, 38, 54, 8)
    out += rrect(box_end - 96, -150, 5, 16, 2.5, PLASTIC)
    out += line("M24 -172 L148 -172 L148 -76 L24 -76 Z", SEAM, 1.6)
    out += rrect(84, -128, 14, 5, 2.5, PLASTIC)
    out += rrect(330, -150, 40, 34, 4, "none", ' stroke="%s" stroke-width="1.4"' % SEAM)
    out += line("M8 %s L%s %s" % (f(-H + 46), f(box_end - 30), f(-H + 46)), HIGHLIGHT, 1.6)
    # Rear apron, lights.
    out += path("M0 -112 L44 -112 L44 -48 L40 -46 Q14 -46 6 -66 Z", "url(#plastic)")
    out += rrect(6, -84, 30, 9, 2, "#e9ecef")
    out += rrect(-1, -150, 7, 34, 2, "url(#tail)")
    if kind == "alcove":
        out += camper_window(F - 140, -H + 22, 58, 32, 8)
        out += line("M%s %s L%s -232" % (f(box_end + 10), f(-H), f(box_end + 10)), SEAM, 1.4)
    if kind == "semi":
        out += line("M%s %s L%s -232" % (f(box_end + 6), f(-H + 8), f(box_end + 6)), SEAM, 1.4)
    if kind == "integrated":
        u = lambda dd: F - dd  # noqa: E731
        out += glass("M%s %s Q%s %s %s %s L%s -132 Q%s -128 %s -128 L%s -150 Z" % (
            f(u(46)), f(-H + 32), f(u(36)), f(-H + 30), f(u(30)), f(-H + 50), f(u(10)), f(u(16)), f(u(24)), f(u(56))))
        out += glass("M%s %s L%s %s L%s -150 L%s -150 Z" % (f(u(118)), f(-H + 70), f(u(62)), f(-H + 70), f(u(64)), f(u(118))))
        out += line("M%s %s L%s -46 M%s %s L%s -46" % (f(u(122)), f(-H + 60), f(u(122)), f(u(62)), f(-H + 62), f(u(62))), SEAM, 1.6)
        out += path("M%s -80 L%s -78 Q%s -76 %s -66 L%s -40 L%s -40 L%s -60 Z" % (
            f(u(70)), f(u(4)), f(u(0)), f(u(0)), f(u(0)), f(u(60)), f(u(66))), "url(#plastic)")
        out += path("M%s -108 L%s -104 Q%s -98 %s -92 L%s -96 Z" % (f(u(40)), f(u(6)), f(u(2)), f(u(4)), f(u(36))), "url(#lamp)", ' stroke="#2b3036" stroke-width="1.2"')
        out += rrect(u(84), -200, 12, 30, 4, "url(#plastic)")
        out += flare(front_axle)
    else:
        out += ducato_cab_details(F, front_axle, -232)
    out += flare(rear_axle)
    out += wheel(rear_axle) + wheel(front_axle)
    return out, L


def compact_side(colour):
    """California-style (T6.1): tall nose, rising bonnet, shoulder crease, pop-top roof."""
    L = 490
    rear_axle, front_axle = 94, 394
    r = 34
    d = ("M2 -44 L0 -118 Q-1 -150 4 -172 Q8 -188 26 -188 L334 -188 Q348 -188 354 -180 "
         "L418 -114 Q421 -111 426 -111 L478 -105 Q487 -103 488 -96 L490 -62 Q490 -38 478 -37 "
         "L%s -37 A42 42 0 0 0 %s -37 L%s -37 A42 42 0 0 0 %s -37 L12 -37 Q2 -37 2 -46 Z") % (
        f(front_axle + 42), f(front_axle - 42), f(rear_axle + 42), f(rear_axle - 42))
    out = ground_shadow(0, L)
    out += arch_shadow(rear_axle, 42, -37) + arch_shadow(front_axle, 42, -37)
    out += body(d, colour)
    # Pop-top roof in body colour: sloped front, black seal between roof and shell.
    shell = "M24 -188 L28 -196 Q30 -201 40 -201 L292 -201 Q306 -201 318 -195 L338 -188 Z"
    out += body(shell, colour)
    out += line("M24 -188.5 L338 -188.5", "#1a1d21", 2.4)
    out += rrect(46, -186, 270, 6, 3, "url(#awning)", ' stroke="#8f979f" stroke-width="0.8"')
    # One dark glass band; slim pillars, the windscreen seen edge-on.
    out += path("M12 -176 L336 -176 Q342 -176 346 -172 L398 -122 L10 -124 Z", "#14171a")
    out += glass("M18 -172 L132 -172 L132 -128 L14 -128 Q12 -150 18 -172 Z")
    out += glass("M148 -172 L252 -172 L252 -128 L148 -128 Z")
    out += glass("M266 -172 L338 -172 L384 -126 L266 -126 Z")
    out += glass("M353 -178 L416 -115 L407 -114 L345 -175 Z")
    # Shoulder crease into the headlight, and the crease linking the arches.
    out += line("M6 -121 L404 -117 L452 -110", "rgba(255,255,255,0.75)", 1.8)
    out += line("M6 -118.5 L404 -114.5 L452 -107.5", "rgba(0,0,0,0.22)", 1.2)
    out += line("M%s -78 L%s -78" % (f(rear_axle + 46), f(front_axle - 46)), "rgba(0,0,0,0.22)", 1.4)
    out += line("M%s -80 L%s -80" % (f(rear_axle + 46), f(front_axle - 46)), "rgba(255,255,255,0.55)", 1.2)
    # Sliding door and its rail behind it, under the rear window.
    out += line("M140 -182 L140 -42 M262 -182 L262 -42 M264 -182 L266 -42")
    out += rrect(14, -128, 126, 5, 2, "#1b1e22")
    out += rrect(242, -118, 12, 4, 2, PLASTIC) + rrect(274, -116, 14, 4, 2, PLASTIC)
    out += line("M396 -112 Q392 -84 404 -66")
    # Body-coloured mirror on a black base.
    out += path("M352 -136 L364 -136 L366 -128 L352 -128 Z", PLASTIC)
    out += body("M350 -162 Q350 -166 356 -166 L368 -166 Q372 -166 372 -160 L370 -140 Q370 -136 364 -136 L354 -136 Q350 -136 350 -140 Z", colour)
    # Tall nose: headlight high at the corner, chrome grille bars, black lower bumper.
    out += path("M440 -113 L482 -106 Q489 -104 489 -96 L488 -90 L446 -98 Z", "#1d2126")
    out += path("M446 -110 L480 -104 Q485 -102 485 -97 L484 -94 L450 -100 Z", "url(#lamp)")
    out += line("M452 -99 L483 -93", "#ffffff", 2.2)
    out += path("M446 -100 L456 -98 L456 -96 L446 -98 Z", "#ffb03b")
    for k in range(3):
        out += line("M486 %s L490 %s" % (f(-88 + 7 * k), f(-87 + 7 * k)), "#c9d0d8", 1.8)
    out += path("M444 -60 L490 -60 L490 -50 Q490 -38 478 -37 L%s -37 Q440 -48 444 -60 Z" % f(front_axle + 42), "url(#plastic)")
    out += rrect(462, -56, 18, 6, 3, "#15181b")
    # Rear: body-coloured bumper with black lower edge, tall tail light.
    out += path("M2 -60 L%s -60 L%s -46 L%s -37 L12 -37 Q2 -37 2 -46 Z" % (f(rear_axle - 48), f(rear_axle - 46), f(rear_axle - 42)), "url(#plastic)")
    out += rrect(-1, -172, 7, 54, 2, "url(#tail)")
    out += rrect(-1, -134, 7, 8, 2, "#f2f4f6")
    # Black sill between the arches.
    out += rrect(rear_axle + 44, -46, front_axle - rear_axle - 88, 8, 3, "url(#plastic)")
    out += wheel(rear_axle, r) + wheel(front_axle, r)
    return out, L


# --------------------------------------------------------------- rear views
def rear_view(colour, kind):
    if kind == "compact":
        W, H, track, r = 190, 192, 162, 33
    elif kind == "panel":
        W, H, track, r = 205, 252, 179, 35
    else:
        W, H, track, r = 232, 320 if kind == "alcove" else 292, 198, 35
    w = W / 2
    out = '<ellipse cx="0" cy="0" rx="%s" ry="7" fill="url(#shadow)"/>' % f(w + 14)
    # Tyres below the body.
    for s in (-1, 1):
        out += rrect(s * track / 2 - 13, -2 * r + 6, 26, 2 * r - 6, 9, "#16191c")
    if kind == "compact":
        d = ("M%s -40 L%s -110 Q%s -150 %s -178 Q%s -192 %s -192 L%s -192 Q%s -192 %s -178 Q%s -150 %s -110 L%s -40 Z" % (
            f(-w), f(-w - 1), f(-w + 2), f(-w + 10), f(-w + 14), f(-w + 30), f(w - 30), f(w - 14), f(w - 10), f(w - 2), f(w + 1), f(w)))
        out += path("M%s -192 L%s -192 L%s -205 L%s -205 Z" % (f(-w + 24), f(w - 24), f(w - 30), f(-w + 30)), "url(#awning)",
                    ' stroke="#8f979f" stroke-width="1"')
        out += body(d, colour)
        out += glass("M%s -176 L%s -176 Q%s -150 %s -126 L%s -126 Q%s -150 %s -176 Z" % (
            f(-w + 22), f(w - 22), f(w - 14), f(w - 10), f(-w + 10), f(-w + 14), f(-w + 22)))
        for s in (-1, 1):
            out += rrect(s * (w - 6) - 6, -150, 12, 46, 3, "url(#tail)")
        out += line("M%s -118 L%s -118" % (f(-w + 12), f(w - 12)))
        out += path("M%s -70 L%s -70 L%s -38 L%s -38 Z" % (f(-w - 2), f(w + 2), f(w), f(-w)), "url(#plastic)")
        out += rrect(-26, -98, 52, 12, 2, "#e9ecef", ' stroke="#9aa2ab" stroke-width="1"')
    elif kind == "panel":
        d = "M%s -40 L%s -150 Q%s -236 %s -248 Q%s -252 %s -252 L%s -252 Q%s -252 %s -248 Q%s -236 %s -150 L%s -40 Z" % (
            f(-w), f(-w), f(-w + 3), f(-w + 10), f(-w + 13), f(-w + 22), f(w - 22), f(w - 13), f(w - 10), f(w - 3), f(w), f(w))
        out += body(d, colour)
        out += glass("M%s -236 L-6 -236 L-6 -176 L%s -176 Z" % (f(-w + 18), f(-w + 16)))
        out += glass("M6 -236 L%s -236 L%s -176 L6 -176 Z" % (f(w - 18), f(w - 16)))
        out += line("M0 -244 L0 -64", "rgba(0,0,0,0.4)", 1.6)
        out += rrect(-12, -140, 8, 16, 3, PLASTIC) + rrect(4, -140, 8, 16, 3, PLASTIC)
        for s in (-1, 1):
            x = s * (w - 5)
            out += rrect(x - 6, -158, 12, 80, 3, "url(#tail)") + rrect(x - 6, -112, 12, 12, 2, "#ffb03b") + rrect(x - 6, -92, 12, 10, 2, "#f2f4f6")
        out += rrect(-20, -252, 40, 5, 2, "url(#tail)")
        out += path("M%s -66 L%s -66 L%s -36 L%s -36 Z" % (f(-w - 3), f(w + 3), f(w + 1), f(-w - 1)), "url(#plastic)")
        out += rrect(-26, -62, 52, 12, 2, "#e9ecef", ' stroke="#9aa2ab" stroke-width="1"')
        out += rrect(w - 4, -256, 10, 18, 3, "#9aa2ab")
        out += line("M%s -150 L%s -150" % (f(-w + 4), f(w - 4)), HIGHLIGHT, 1.4)
    else:
        d = "M%s -60 L%s %s Q%s %s %s %s L%s %s Q%s %s %s %s L%s -60 Q%s -46 %s -46 L%s -46 Q%s -46 %s -60 Z" % (
            f(-w), f(-w), f(-H + 20), f(-w), f(-H), f(-w + 20), f(-H), f(w - 20), f(-H), f(w), f(-H), f(w), f(-H + 20),
            f(w), f(w), f(w - 14), f(-w + 14), f(-w), f(-w))
        out += body(d, colour)
        out += path("M%s -96 C %s -100 %s -84 %s -92 L%s -84 C %s -76 %s -92 %s -86 Z" % (
            f(-w), f(-w / 2), f(w / 2), f(w), f(w), f(w / 2), f(-w / 2), f(-w)), "rgba(70,80,92,0.55)")
        out += camper_window(-62, -H + 60, 124, 50, 10)
        for s in (-1, 1):
            out += rrect(s * (w - 30) - 26, -138, 52, 22, 5, "#15181c")
            out += rrect(s * (w - 30) - 24, -136, 26, 18, 3, "url(#tail)")
            out += rrect(s * (w - 30) + 2, -136, 10, 18, 2, "#ffb03b")
            out += rrect(s * (w - 30) + 12, -136, 10, 18, 2, "#f2f4f6")
        out += rrect(-30, -114, 60, 13, 2, "#e9ecef", ' stroke="#9aa2ab" stroke-width="1"')
        out += rrect(-22, -H + 8, 44, 5, 2, "url(#tail)")
        # Ladder on the right.
        lx = w - 34
        out += rrect(lx, -H + 24, 4, H - 110, 2, "#9aa2ab") + rrect(lx + 22, -H + 24, 4, H - 110, 2, "#9aa2ab")
        for y in range(-H + 44, -100, 26):
            out += rrect(lx, y, 26, 3, 1.5, "#9aa2ab")
        out += path("M%s -70 L%s -70 L%s -42 L%s -42 Z" % (f(-w), f(w), f(w - 4), f(-w + 4)), "url(#plastic)")
        out += rrect(w - 4, -H - 2, 10, 18, 3, "#9aa2ab")
        out += line("M%s %s L%s %s" % (f(-w + 4), f(-H + 30), f(w - 4), f(-H + 30)), HIGHLIGHT, 1.4)
    return out, W, H


# ---------------------------------------------------------------- top views
def top_view(colour, kind):
    dims = {"compact": (490, 190, 92), "panel": (636, 205, 170), "alcove": (700, 232, 160),
            "semi": (700, 232, 160), "integrated": (720, 232, 40)}
    L, W, ws = dims[kind]
    w = W / 2
    out = rrect(-w, 0, W, L, 26 if kind != "compact" else 34, colour, ' stroke="rgba(0,0,0,0.35)" stroke-width="1.5"')
    # Windscreen and bonnet.
    if kind == "integrated":
        out += path("M%s 18 Q0 4 %s 18 L%s 46 Q0 36 %s 46 Z" % (f(-w + 14), f(w - 14), f(w - 20), f(-w + 20)), "url(#glass)")
    else:
        out += path("M%s %s Q0 %s %s %s L%s %s Q0 %s %s %s Z" % (
            f(-w + 14), f(ws - 60), f(ws - 72), f(w - 14), f(ws - 60), f(w - 20), f(ws - 22), f(ws - 32), f(-w + 20), f(ws - 22)), "url(#glass)")
        out += line("M%s %s Q0 %s %s %s" % (f(-w + 20), f(ws - 96), f(ws - 104), f(w - 20), f(ws - 96)), SEAM, 1.4)
    # Mirrors.
    my = (ws - 40) if kind != "integrated" else 60
    out += rrect(-w - 16, my, 16, 26, 5, "url(#plastic)") + rrect(w, my, 16, 26, 5, "url(#plastic)")
    # Roof: awning along the right side, skylights, solar panel.
    out += rrect(w - 14, ws + 20, 10, L - ws - 60, 4, "url(#awning)", ' stroke="#8f979f" stroke-width="1"')
    if kind == "compact":
        out += rrect(-w + 18, ws + 6, W - 36, L - ws - 30, 16, "#3a3f46")
    else:
        out += rrect(-46, ws + 60, 92, 70, 10, "#cfd6dd", ' stroke="#9aa2ab" stroke-width="1.5"')
        out += rrect(-40, ws + 66, 80, 58, 8, "url(#glass)", ' opacity="0.55"')
        out += rrect(-56, ws + 170, 112, 150, 4, "url(#solar)")
        for k in range(1, 4):
            out += line("M-56 %s L56 %s" % (f(ws + 170 + 37.5 * k), f(ws + 170 + 37.5 * k)), "rgba(255,255,255,0.18)", 1)
        out += rrect(-24, L - 96, 48, 40, 6, "#cfd6dd", ' stroke="#9aa2ab" stroke-width="1.5"')
    return out, L, W


SIDES = {
    "compact": compact_side,
    "panel": panel_side,
    "alcove": lambda c: motorhome_side(c, "alcove"),
    "semi": lambda c: motorhome_side(c, "semi"),
    "integrated": lambda c: motorhome_side(c, "integrated"),
}
TYPES = ["compact", "panel", "alcove", "semi", "integrated"]


# Geometry the app needs to place, scale, and tilt each drawing (cm).
META = {
    "compact": {"length": 490, "height": 206, "width": 190, "axles": [94, 394], "wheel": 34, "track": 162},
    "panel": {"length": 636, "height": 263, "width": 205, "axles": [138, 541.5], "wheel": 35, "track": 179},
    "alcove": {"length": 700, "height": 334, "width": 232, "axles": [201.5, 605], "wheel": 35, "track": 198},
    "semi": {"length": 700, "height": 306, "width": 232, "axles": [201.5, 605], "wheel": 35, "track": 198},
    "integrated": {"length": 720, "height": 306, "width": 232, "axles": [200.5, 604], "wheel": 35, "track": 198},
}
