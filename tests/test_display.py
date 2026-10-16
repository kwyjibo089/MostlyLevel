"""ILI9341 driver, Graphics text drawing, and the strip compositor."""

import pytest


@pytest.fixture
def lcd(import_fresh):
    return import_fresh("ili9341").ILI9341()


@pytest.fixture
def graphics(import_fresh, lcd):
    return import_fresh("graphics").Graphics(lcd)


def region(panel, x, y, w, h):
    return [panel.pixel(px, py) for py in range(y, y + h) for px in range(x, x + w)]


def test_init_turns_display_on(lcd, panel):
    assert 0x01 in panel.commands  # Software reset.
    assert panel.commands[-1] == 0x29  # Display on.


def test_fill_rect_clips_to_screen(lcd, panel):
    lcd.fill_rect(-5, -5, 10, 10, 0xF800)
    assert region(panel, 0, 0, 5, 5) == [0xF800] * 25
    assert panel.pixel(5, 0) == 0
    assert panel.pixel(0, 5) == 0

    lcd.fill_rect(235, 315, 20, 20, 0x07E0)
    assert region(panel, 235, 315, 5, 5) == [0x07E0] * 25


def test_fill_larger_than_chunk(lcd, panel):
    lcd.fill(0x1234)
    assert panel.pixel(0, 0) == 0x1234
    assert panel.pixel(239, 319) == 0x1234


def test_lines_and_pixels(lcd, panel):
    lcd.hline(10, 20, 5, 0xFFFF)
    lcd.vline(30, 40, 3, 0x001F)
    lcd.pixel(239, 319, 0xF800)
    lcd.pixel(240, 0, 0xF800)  # Off screen: ignored.
    assert region(panel, 10, 20, 5, 1) == [0xFFFF] * 5
    assert region(panel, 30, 40, 1, 3) == [0x001F] * 3
    assert panel.pixel(239, 319) == 0xF800


def test_blit_writes_big_endian_block(lcd, panel):
    lcd.blit(100, 200, 2, 1, bytes((0x12, 0x34, 0xAB, 0xCD)))
    assert region(panel, 100, 200, 2, 1) == [0x1234, 0xABCD]


def test_text_draws_glyph_columns(graphics, panel):
    graphics.text(0, 0, "1", 0xFFFF)
    # Glyph "1" is (0, 66, 127, 64, 0): column 2 is fully lit for rows 0-6.
    assert [panel.pixel(2, y) for y in range(8)] == [0xFFFF] * 7 + [0]
    assert panel.pixel(0, 0) == 0


def test_text_is_upper_cased_and_scaled(graphics, panel):
    graphics.text(0, 0, "l", 0xFFFF, scale=2)
    # Glyph "L" column 0 is 127: rows 0-6, doubled to 14 rows and 2 columns.
    assert region(panel, 0, 0, 2, 14) == [0xFFFF] * 28
    assert panel.pixel(0, 14) == 0


def test_unknown_characters_advance_cursor(graphics, panel):
    graphics.text(0, 0, "~1", 0xFFFF)
    assert panel.pixel(6 + 2, 0) == 0xFFFF


@pytest.fixture
def compositor(import_fresh):
    return import_fresh("compositor")


def test_display_list_records_fills(compositor):
    items = compositor.DisplayList()
    items.fill_rect(1, 2, 3, 4, 0xFFFF)
    items.fill_rect(0, 0, 0, 5, 0xFFFF)  # Empty: skipped.
    items.hline(5, 6, 7, 0x1)
    items.vline(8, 9, 10, 0x2)
    items.pixel(11, 12, 0x3)
    assert items.items == [
        (1, 2, 3, 4, 0xFFFF),
        (5, 6, 7, 1, 0x1),
        (8, 9, 1, 10, 0x2),
        (11, 12, 1, 1, 0x3),
    ]


def test_strip_renderer_composites_and_skips_unchanged_strips(compositor, lcd, panel):
    renderer = compositor.StripRenderer(lcd, 40, 320, 40)
    assert renderer.count == 7
    items = [(0, 40, 240, 280, 0x249F), (10, 100, 20, 30, 0xF800)]

    renderer.render(items)
    assert panel.pixel(0, 40) == 0x249F
    assert panel.pixel(15, 110) == 0xF800
    assert panel.pixel(0, 39) == 0  # Above the composited region.

    panel.pixel_bytes = 0
    renderer.render(list(items))
    assert panel.pixel_bytes == 0

    # Moving the red rect only touches the strips it covers (80-119, 120-159).
    renderer.render([items[0], (10, 101, 20, 30, 0xF800)])
    assert panel.pixel_bytes == 2 * 240 * 40 * 2
    assert panel.pixel(15, 100) == 0x249F

    panel.pixel_bytes = 0
    renderer.invalidate()
    renderer.render([items[0], (10, 101, 20, 30, 0xF800)])
    assert panel.pixel_bytes == 240 * 280 * 2


def test_strip_renderer_handles_partial_last_strip(compositor, lcd, panel):
    renderer = compositor.StripRenderer(lcd, 50, 320, 40)
    assert renderer.count == 7
    renderer.render([(0, 300, 240, 20, 0x07E0)])
    assert panel.pixel(239, 319) == 0x07E0
    assert panel.pixel(0, 299) == 0


def picture(compositor):
    """A 4x3 two-colour Bitmap: a red top row and a white dot, rest clear."""
    bitmap = compositor.Bitmap(4, 3, [None, 0xF800, 0xFFFF])
    bitmap.fill_rect(0, 0, 4, 1, 0xF800)
    bitmap.fill_rect(2, 2, 1, 1, 0xFFFF)
    return bitmap


def test_bitmap_composites_with_transparency(compositor, lcd, panel):
    renderer = compositor.StripRenderer(lcd, 40, 320, 40)
    bitmap = picture(compositor)
    renderer.render([(0, 40, 240, 280, 0x249F), (10, 78, 4, 3, bitmap)])  # Spans 2 strips.
    assert region(panel, 10, 78, 4, 3) == [
        0xF800, 0xF800, 0xF800, 0xF800,
        0x249F, 0x249F, 0x249F, 0x249F,  # Transparent: the sky shows.
        0x249F, 0x249F, 0xFFFF, 0x249F,
    ]


def test_bitmap_in_render_area_and_rects(compositor, lcd, panel):
    renderer = compositor.StripRenderer(lcd, 40, 320, 40)
    bitmap = picture(compositor)
    renderer.render_area(10, 50, 6, 4, [(10, 50, 6, 4, 0x07E0), (11, 50, 4, 3, bitmap)])
    assert panel.pixel(11, 50) == 0xF800 and panel.pixel(11, 51) == 0x07E0
    assert bitmap.rects() == [(0, 0, 4, 1, 0xF800), (2, 2, 1, 1, 0xFFFF)]


def test_bitmap_on_targets_without_blit(compositor, graphics, panel):
    graphics.fill_rect(0, 0, 10, 10, 0x001F)
    graphics.bitmap(2, 2, picture(compositor))
    assert region(panel, 2, 2, 4, 3) == [
        0xF800, 0xF800, 0xF800, 0xF800,
        0x001F, 0x001F, 0x001F, 0x001F,
        0x001F, 0x001F, 0xFFFF, 0x001F,
    ]


def test_bitmap_in_screenshot_tiles(compositor, import_fresh):
    screenshot = import_fresh("screenshot")
    tile = screenshot.TileFramebufferDisplay(8, 2, 10)
    tile.fill(0x001F)
    import compositor as module

    bitmap = module.Bitmap(4, 3, [None, 0xF800, 0xFFFF])
    bitmap.fill_rect(0, 0, 4, 1, 0xF800)
    tile.bitmap(1, 9, bitmap)  # Rows 9-11; the tile holds rows 10-11.
    assert tile.framebuffer.pixel(1, 0) == 0x001F  # Row 10 is transparent.
    bitmap.fill_rect(0, 1, 1, 1, 0xFFFF)
    tile.bitmap(1, 9, bitmap)
    assert tile.framebuffer.pixel(1, 0) == 0xFFFF  # Native byte order.
