"""Minimal PNG writer/reader for screen reference images (8-bit RGB)."""

import struct
import zlib

from fakehw import HEIGHT, WIDTH


def rgb565_to_rgb(colour):
    red = (colour >> 11) & 0x1F
    green = (colour >> 5) & 0x3F
    blue = colour & 0x1F
    return (red << 3) | (red >> 2), (green << 2) | (green >> 4), (blue << 3) | (blue >> 2)


def screen_rgb(pixels, width=WIDTH, height=HEIGHT):
    """Return rows of RGB bytes for RGB565 pixel values."""
    rows = []
    for y in range(height):
        row = bytearray()
        for colour in pixels[y * width:(y + 1) * width]:
            row.extend(rgb565_to_rgb(colour))
        rows.append(bytes(row))
    return rows


def _chunk(kind, data):
    return (
        struct.pack(">I", len(data)) + kind + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_png(path, rows):
    width = len(rows[0]) // 3
    raw = b"".join(b"\0" + row for row in rows)
    header = struct.pack(">IIBBBBB", width, len(rows), 8, 2, 0, 0, 0)
    with open(path, "wb") as image_file:
        image_file.write(b"\x89PNG\r\n\x1a\n")
        image_file.write(_chunk(b"IHDR", header))
        image_file.write(_chunk(b"IDAT", zlib.compress(raw, 9)))
        image_file.write(_chunk(b"IEND", b""))


def _paeth(left, up, up_left):
    estimate = left + up - up_left
    to_left = abs(estimate - left)
    to_up = abs(estimate - up)
    to_up_left = abs(estimate - up_left)
    if to_left <= to_up and to_left <= to_up_left:
        return left
    return up if to_up <= to_up_left else up_left


def read_png(path):
    """Return rows of RGB bytes from an 8-bit RGB, non-interlaced PNG."""
    with open(path, "rb") as image_file:
        data = image_file.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)

    offset = 8
    idat = b""
    width = height = None
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        if kind == b"IHDR":
            width, height, depth, colour_type, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if (depth, colour_type, interlace) != (8, 2, 0):
                raise ValueError("expected 8-bit RGB non-interlaced PNG: %s" % path)
        elif kind == b"IDAT":
            idat += body
        offset += 12 + length

    raw = zlib.decompress(idat)
    stride = width * 3
    rows = []
    previous = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind = raw[start]
        row = bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            left = row[i - 3] if i >= 3 else 0
            up = previous[i]
            up_left = previous[i - 3] if i >= 3 else 0
            if kind == 1:
                row[i] = (row[i] + left) & 0xFF
            elif kind == 2:
                row[i] = (row[i] + up) & 0xFF
            elif kind == 3:
                row[i] = (row[i] + (left + up) // 2) & 0xFF
            elif kind == 4:
                row[i] = (row[i] + _paeth(left, up, up_left)) & 0xFF
        rows.append(bytes(row))
        previous = row
    return rows
