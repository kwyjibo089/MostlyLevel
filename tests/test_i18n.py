"""Screen texts: language files, font coverage, fit, and runtime switching."""

import json

import pytest
from support.app import SRC, load_app

CODES = ("en", "de", "fr", "es")
CHAR = 6  # Pixels per character at scale 1.

# Pixel width available to each text, from the layout in app.py.
WIDTHS = {
    "status_": 240 - 189,  # Header status, right of the state square.
    "nav_": 112 - 4,
    "calibrate": 88 - 6,
    "tab_": 100 - 6,
    "front_": 112 - 6,  # 4 CORNERS cells; the 2 WEDGES cells are wider.
    "rear_": 112 - 6,
    "no_wedges_needed": 240 - 12,
    "van_is_level": 240 - 12,
    "warning_": 240 - 18 - 8,  # Inside the warning panel.
}


def texts(code):
    return json.loads((SRC / ("lang_%s.json" % code)).read_text(encoding="utf-8"))


@pytest.mark.parametrize("code", CODES)
def test_language_has_exactly_the_english_keys(code):
    assert sorted(texts(code)) == sorted(texts("en"))


@pytest.mark.parametrize("code", CODES)
def test_every_character_is_in_the_font(code):
    from graphics import char_rects

    for key, text in texts(code).items():
        # Graphics.text() upper-cases ASCII only, so texts must be uppercase.
        assert text == text.upper(), key
        missing = {char for char in text if char_rects(char) is None}
        assert not missing, (key, missing)


def test_accent_marks_stay_clear_of_their_letters():
    from graphics import ACCENT_MARKS, ACCENTED, FONT, glyph_rects

    def pixels(rects):
        return {
            (x, y)
            for col, row, width, height in rects
            for x in range(col, col + width)
            for y in range(row, row + height)
        }

    for char, (base, mark) in ACCENTED.items():
        letter = pixels(glyph_rects(FONT[base]))
        accent = pixels(ACCENT_MARKS[mark])
        if mark == "cedilla":
            continue  # Hangs from the letter by design.
        # Not touching, even diagonally.
        near = {(x + dx, y + dy) for x, y in letter for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        assert not accent & near, char
        assert all(0 <= x < 5 for x, _ in accent), char


@pytest.mark.parametrize("code", CODES)
def test_every_text_fits_its_space(code):
    for key, text in texts(code).items():
        for prefix, width in WIDTHS.items():
            if key.startswith(prefix):
                assert len(text) * CHAR - 1 <= width, (key, text)
    values = texts(code)
    # Readouts at scale 2 ("P +12.5°") and number formatting need one character.
    assert len(values["pitch_short"]) == len(values["roll_short"]) == 1
    assert len(values["decimal"]) == 1


def test_language_cycles_and_is_saved(app, reference_file):
    i18n = app.i18n
    assert i18n.language == "en"
    seen = []
    for _ in CODES:
        app.switch_language(None, "SCANNING")
        seen.append(i18n.language)
    assert seen == ["de", "fr", "es", "en"]

    app.switch_language(None, "SCANNING")
    saved = reference_file.parent / "language.cfg"
    assert saved.read_text() == "de\n"
    restarted = load_app(reference_file)
    assert restarted.i18n.language == "de"
    assert restarted.t("calibrate") == "KALIBRIEREN"


def test_unknown_saved_language_falls_back_to_english(reference_file):
    (reference_file.parent / "language.cfg").write_text("xx\n")
    assert load_app(reference_file).i18n.language == "en"


def test_missing_language_file_falls_back_to_english(app, tmp_path, capsys):
    i18n = app.i18n
    (tmp_path / "lang_en.json").write_text(json.dumps(texts("en")))
    i18n.TEXT_DIR = str(tmp_path) + "/"
    (tmp_path / "language.cfg").write_text("de\n")
    i18n.LANGUAGE_FILE = str(tmp_path / "language.cfg")
    i18n.start()
    assert i18n.language == "en"
    assert "Language de unavailable" in capsys.readouterr().out


def test_numbers_use_the_language_decimal_separator(app):
    app.i18n.load("de")
    assert app.readout_text({"pitch": 1.25, "roll": -0.5}) == ("P +1,2°", "R -0,5°")
    assert app.cm_text(3.45) == "3,5 cm"
    app.i18n.load("en")
    assert app.cm_text(3.45) == "3.5 cm"


def test_holding_the_language_button_switches_language(app_with_touch, fake_clock, touch, panel):
    from test_app_flow import go_live, hold, tap
    from test_rendering import full_direct_redraw, snapshot

    app = app_with_touch
    go_live(app, fake_clock)
    x, y, width, height = app.LANGUAGE_RECT
    tap(app, fake_clock, touch, (x + width // 2, y + height // 2))
    assert app.i18n.language == "en"  # A tap is not enough.
    hold(app, fake_clock, touch, (x + width // 2, y + height // 2))
    assert app.i18n.language == "de"
    # Cached layers were dropped: the page matches a fresh German redraw.
    assert snapshot(panel) == full_direct_redraw(app, panel, app.sensor.latest)
    assert app.layer_cache["calibrate"] == tuple(
        app.record_items(app.draw_calibrate_button)
    )


def test_language_button_is_only_on_horizon(app):
    x, y, width, height = app.LANGUAGE_RECT
    centre = (x + width // 2, y + height // 2)
    app.active_screen = 0
    assert app.touch_language_at(centre)
    app.active_screen = 1
    assert not app.touch_language_at(centre)


def test_language_touch_area_stays_clear_of_calibrate(app):
    tx, ty, tw, th = app.LANGUAGE_TOUCH_RECT
    cx, cy, cw, ch = app.CALIBRATE_RECT
    assert tx + tw <= cx or cx + cw <= tx or ty + th <= cy or cy + ch <= ty
    # The visible button lies inside its touch area, below the navigation bar.
    x, y, width, height = app.LANGUAGE_RECT
    assert tx <= x and x + width <= tx + tw and ty <= y and y + height <= ty + th
    assert ty >= app.HORIZON_TOP
