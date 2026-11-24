#!/usr/bin/env python3
"""Tuesday 24 November 2026 world news, summed up in one 1024x1024 image.

Pure Python 3.13 standard library: no third-party imports, no network,
no clock, no randomness. The page (masthead, UTC timeline, three lead
panels, twelve medium stories, world map, 39-item story list, date check)
is drawn procedurally from the tables at the bottom of this file, and the
PNG bytes are encoded here as well, on top of stdlib zlib.

Run:  python3 main.py [--output entry.png] [--check]
The default output is /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
Two runs write byte-identical output.
"""

import argparse
import base64
import math
import os
import struct
import sys
import zlib

# ------------------------------------------------------------------ fonts
# 1-bit bitmap fonts, rasterised from Liberation fonts when the first
# version of this renderer was built. Blob layout: glyphs in codepoint
# order; each glyph starts with one width byte, then
# ceil(width/8)*height bitmap bytes (MSB-first, row-major).
# CHARS is ASCII 32-126 plus middle dot, em dash, right quote, euro.
CHARS = [chr(c) for c in range(32, 127)] + ["\u00b7", "\u2014", "\u2019", "\u20ac"]

F_SANS10 = "AwAAAAAAAAAAAAAAAAADAAAAQEBAQEAAQAAAAAQAAACgIAAAAAAAAAAABgAAAAgI/ED4EBAAAAAGAAAAeIBgMAgIeAAAAAkAAAAAAABiAIQAgABrABQAFAAjAAAAAAAAAAcAAAA4CDBklIh0AAAAAgAAAAAAAAAAAAAAAAAEAAAAIEBAQEBAQEAgAAQAAACAQAAgICAAQIAABAAAAADgYCAAAAAAAAAGAAAAAAAAeAAAAAAAAAMAAAAAAAAAAABAQAAABAAAAAAAAABgAAAAAAADAAAAAAAAAAAAQAAAAAMAAAAgAEBAQICAAAAABgAAAHBIiIiISHAAAAAGAAAAIGAgICAgeAAAAAYAAABwSAgQIEB4AAAABgAAAHAICDAICHAAAAAGAAAAEDAwUBD4EAAAAAYAAAB4QHAICAhwAAAABgAAADBAcEhISDAAAAAGAAAAeAgQICAgIAAAAAYAAABwSEhwSEhwAAAABgAAAHBICEh4CHAAAAADAAAAAABAAAAAQAAAAAMAAAAAAEAAAABAQAAABgAAAAAIMMAwCAAAAAAGAAAAAAB4AHgAAAAAAAYAAAAAQDAIMEAAAAAABgAAAHBICBAgACAAAAALAAAAAAAAHwAggE4AUgASgFsAQAAeAAAAAAAHAAAAECAoSHxEggAAAAcAAAB4RER4RER4AAAACAAAADxCQEBAQjwAAAAIAAAAeERCQkJEeAAAAAcAAAB8QEB8QEB8AAAABwAAAHxAQHhAQEAAAAAIAAAAPEJADkJCPAAAAAgAAABERER8REREAAAAAwAAAEBAQEBAQEAAAAAFAAAAMBAQEBCQcAAAAAcAAABESFBwUEhEAAAABgAAAEBAQEBAQHgAAAAJAAAAAAAAQwBjAGUARQBRAFkASQAAAAAAAAAIAAAAYmJSUkpGQgAAAAgAAAA8QkKCQkI8AAAABwAAAHhERER4QEAAAAAIAAAAPEJCgkJCPAgMAAgAAAB8RER4SEREAAAABwAAADhEQDgERHgAAAAHAAAA/BAQEBAQEAAAAAgAAABEREREREQ4AAAABwAAAIREREgoMBAAAAAKAAAAAAAAiICMgESAVQBRADMAIwAAAAAAAAAHAAAARAgwEChIRAAAAAcAAABESCgwEBAQAAAABwAAAHwIECAgQPwAAAADAAAAQEBAQEBAQEBAAAMAAACAgABAQAAgAAAAAwAAAMBAQEBAQEBAwAAFAAAAIFAQgAAAAAAAAAYAAAAAAAAAAAAAAPgABAAAQAAAAAAAAAAAAAAGAAAAAABwCHiIaAAAAAYAAABAQHBISEhwAAAABQAAAAAAcECAQHAAAAAGAAAACAh4SIhIeAAAAAYAAAAAAHBI+EBwAAAAAwAAAGBA4EBAQEAAAAAGAAAAAAB4CIgIaAhwAAYAAABAQHBISEhIAAAAAwAAAAAAQEBAQEAAAAADAAAAAABAQEBAQECAAAUAAABAQFBgYFBIAAAAAwAAAEBAQEBAQEAAAAAJAAAAAAAAAAAAAHYASQBJAEkASQAAAAAAAAAGAAAAAABwSEhISAAAAAYAAAAAAHBIiEhwAAAABgAAAAAAcEhISHBAQAAGAAAAAAB4SIhIeAgIAAQAAAAAAGBAQEBAAAAABQAAAAAAcEAwCHAAAAADAAAAAEDAQEBAQAAAAAYAAAAAAEhISEhoAAAABQAAAAAAiFBQUCAAAAAIAAAAAACSmmhsZAAAAAUAAAAAAFBQIFCIAAAABQAAAAAAiFBQMCAgQAAFAAAAAABwECBA8AAAAAQAAAAgQEBAwEBAQCAAAwAAAEBAQEBAQEBAQAAEAAAAwEBAQCBAQEDAAAYAAAAAAGAYAAAAAAAABAAAAAAAAEAAAAAAAAAKAAAAAAAAAAAAAAAAAAD/wAAAAAAAAAAAAAADAAAAQAAAAAAAAAAAAAYAAAA4QPBA8EA4AAAA"
F_SANS12 = "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"
F_SANSB10 = "AwAAAAAAAAAAAAAAAAAEAAAAQEBAQEAAQAAAAAUAAABQUFAAAAAAAAAABgAAACgIeFD4UBAAAAAGAAAAeMBgeAgIeAAAAAkAAAAAAABiAJQAlABrABSAFIAjAAAAAAAAAAgAAAA4KDh0XEx+AAAAAwAAAEBAQAAAAAAAAAAEAAAAIEBAQEBAQEAgAAQAAADAQGBgYGBgQMAABAAAAEDwYCAAAAAAAAAGAAAAACAg+DAgAAAAAAMAAAAAAAAAAABAQEAABAAAAAAAAADgAAAAAAADAAAAAAAAAAAAQAAAAAMAAABgQEBAQMCAAAAABgAAAHBYyMjIWHAAAAAGAAAAcHAwMDAweAAAAAYAAABwWBgQIED4AAAABgAAAHBYGDAYyHAAAAAGAAAAGDg4WNj8GAAAAAYAAAB4QHBYCNhwAAAABgAAADBYwPjISHAAAAAGAAAA+BgQMCAgIAAAAAYAAABwSFhwyMhwAAAABgAAAHDYyHgIWHAAAAAEAAAAAABAAAAAQAAAAAQAAAAAAEAAAABAAEAABgAAAAAIcMBwCAAAAAAGAAAAAAD4APgAAAAAAAYAAAAAwDgIOMAAAAAABwAAAHhICBgwADAAAAAKAAAAAAAAHgAhgE6AUoACgAaAWwBAAD4AAAAIAAAAGDgoLHxExgAAAAgAAAB8RER8RkZ8AAAACAAAADxmQMBAZjwAAAAIAAAAeExGRkZMeAAAAAcAAAB8QEB8QEB8AAAABwAAAHxAQHxAQEAAAAAIAAAAPGZAzkJmPAAAAAgAAABGRkZ+RkZGAAAAAwAAAEBAQEBAQEAAAAAGAAAAOBgYGBjYcAAAAAgAAABESFBwSExGAAAABwAAAEBAQEBAQHwAAAAJAAAAAAAAYwBnAGcAVwBbAFsASwAAAAAAAAAIAAAAZmZ2Vl5ORgAAAAgAAAA8ZkLCQmY8AAAABwAAAHhMREx4QEAAAAAIAAAAPGZCwkJmPAgOAAgAAAB8RkZ8TERGAAAABwAAAHhMYDwERHgAAAAHAAAA/DAwMDAwMAAAAAgAAABGRkZGRmQ4AAAABwAAAMRETGgoODAAAAAKAAAAAAAAzIDMgF2AVYB3AHMAMwAAAAAAAAAHAAAARGg4MDhsxAAAAAcAAADEbCgwEBAQAAAABwAAAHwIEDBgQPwAAAAEAAAAYEBAQEBAQEBgAAMAAACAwEBAQEBgAAAABAAAAOBgYGBgYGBg4AAGAAAAMHBIyAAAAAAAAAYAAAAAAAAAAAAAAPgABAAAQCAAAAAAAAAAAAAGAAAAAABwGHjYbAAAAAcAAABAQHhMTEx4AAAABgAAAAAAcEjASHAAAAAHAAAACAh4SMhIeAAAAAYAAAAAAHBI+EB4AAAABAAAAGBA4EBAQEAAAAAHAAAAAAB4SMhIeAh4AAcAAABAQHhISEhIAAAAAwAAAEAAQEBAQEAAAAADAAAAQABAQEBAQEDAAAYAAABAQFhQcFhIAAAAAwAAAEBAQEBAQEAAAAAJAAAAAAAAAAAAAFsASQBJAEkASQAAAAAAAAAHAAAAAABYSEhISAAAAAcAAAAAAHhMzEh4AAAABwAAAAAAeExMTHhAQAAHAAAAAAB4SMhIeAgIAAQAAAAAAHBAQEBAAAAABgAAAAAAcEB4CHgAAAAEAAAAAEDgQEBAYAAAAAcAAAAAAEhISEh4AAAABgAAAAAAyEhYcDAAAAAIAAAAAACb2mpmZgAAAAYAAAAAAEhwMHDIAAAABgAAAAAAyEhYMDAgYAAFAAAAAABwMCBA+AAAAAQAAAAwYGBgwGBgYDAAAwAAAEBAQEBAQEBAQAAEAAAAwGBgYDBgYGDAAAYAAAAAAGAYAAAAAAAABAAAAAAAAEAAAAAAAAAKAAAAAAAAAAAAAAAAAAD/wAAAAAAAAAAAAAADAAAAQEBAAAAAAAAAAAYAAAA4QOBA4EA4AAAA"
F_SANSB15 = "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"
F_SANSB22 = "BwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAA4ODg4ODg4ODg4AAA4ODgAAAAAAAsAAAAAAAAAAAAAc4AzgDOAM4AzgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAADGAMYAhACEB/8H/wGMAQgDGA/+B/4DGAIQBjAGMAAAAAAAAAAAAAAA0AAAAAAAAAAAIAH4A/4HLgcmByAH4AP4AfwAfgAnBicHJwfvA/4B+AAgACAAAAAAAAABQAAAAAAAAAAAAAAAAAAAA8BwB+BgBjDABjHABjGABjMABjd4B+b8A8zOAB3GABnGADHGAHDOAGD8AMB4AAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAPAD+AMcAxwDOAPwA+AHwg7HHOYcfhw8Hj4P/4fjgAAAAAAAAAAAAAGAAAAAABwcHBwcAAAAAAAAAAAAAAAAAAAAAgAAAAADhwcODg4OHBwcHBwcHA4ODg4HBwOCAAAAADgcHA4OBwcHBwcHBwcHBwcODhwcOAJAAAAAAAAAAAAABgAGABbAP8APAA+AHcAIgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAHAAcABwAHAH/wf/AHAAcABwAHAAcAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAAAA4ODgYMDAAAAgAAAAAAAAAAAAAAAAAfHx8AAAAAAAAAAAABwAAAAAAAAAAAAAAAAAAAAAAeHh4AAAAAAAHAAAAABwcGBg4ODgwMHBwcGBgYOAAAAAAAA0AAAAAAAAAAAAADwA/wDnAcOBw4HDgcOBw4HDgcOBw4HDgOcAfwA8AAAAAAAAAAAAAAA0AAAAAAAAAAAAABwAfAD8AdwAHAAcABwAHAAcABwAHAAcABwB/8H/wAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOAA4ADgAcADwAeAHgA8ADgAeAB/4H/gAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOAA4AHgD4APgAPgAOAA4HDgf+A/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAA8ADwAfAD8ANwB3AGcAxwHHAYcD/8P/wAcABwAHAAAAAAAAAAAAAAA0AAAAAAAAAAAAAP+A/4HgAcABwAHeAf8B/4ADgAPAA8HDgeeA/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAD4AfwD3gcOBwAHeAf8B54HDgcOBw4HDgPeAfwA+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAf+B/4ADgAOABwAOAA4AHAAcADgAOAA4AHgAcABwAAAAAAAAAAAAAAA0AAAAAAAAAAAAAH4A/wHngcOBw4DjgH8AfwHjgcOBw8HDgeOA/wB+AAAAAAAAAAAAAAA0AAAAAAAAAAAAAHwA/wHnAcOBw4HDgcOB54D/gHuAA4HDge8A/wB8AAAAAAAAAAAAAAAgAAAAAAAAAADg4OAAAAAAAADg4OAAAAAAACAAAAAAAAAAAODg4AAAAAAAAODg4GBgwAAANAAAAAAAAAAAAAAAAAAAAEADwB/AfgH4AcABwAH4AH4AD8ADwABAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAAAAAAf/B/8AAAAAAAAH/wf/AAAAAAAAAAAAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAABAAHgAfgAPwAPwAHAAcAPwD8B+AHgAQAAAAAAAAAAAAAAAAAAOAAAAAAAAAAAAAA/AH+A98HhwcHAAcAHgA8AHAAcAAAAAAAcABwAHAAAAAAAAAAAAAAAWAAAAAAAAAAAAAAAAAAAAAP4AA/+ABgDADABgGHswMP8wMYYwIwYQYwYwYgYwYgwwYwxgI/fAMeOAGAAAHAEAB/8AAfwAAAAAAAAAEAAAAAAAAAAAAAADwAPAB+AH4A5gDnAOcBw4HDgf+D/8OBx4HHAOcA4AAAAAAAAAAAAAEAAAAAAAAAAAAAB/8H/4eHx4HHgceDx/+H/4eDx4HngOeB54PH/8f/AAAAAAAAAAAAAAEAAAAAAAAAAAAAAH4B/4P/w8HngMcABwAHAAcABwAHgMPB4//A/4B+AAAAAAAAAAAAAAEAAAAAAAAAAAAAB/wH/wefh4PHgeeA54DngOeA54HngceDx4+H/wf8AAAAAAAAAAAAAADwAAAAAAAAAAAAB/+H/4eAB4AHgAeAB/+H/4eAB4AHgAeAB4AH/8f/wAAAAAAAAAAAAADgAAAAAAAAAAAAB/+H/4eAB4AHgAeAB/8H/weAB4AHgAeAB4AHgAeAAAAAAAAAAAAAAAEgAAAAAAAAAAAAAAAAAAAAfwAB/8AD/+ADweAHgMAHAAAHAAAHB/AHB/AHAHAHgHADwPAD//AB/8AAfwAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAeBx4HHgceBx4HHgcf/x//H/8eBx4HHgceBx4HHgcAAAAAAAAAAAAAAcAAAAAAHh4eHh4eHh4eHh4eHh4eAAAAAAADQAAAAAAAAAAAAAH4AfgAeAA4ADgAOAA4ADgAOAA4HDgceB/wD/AHwAAAAAAAAAAAAAAEAAAAAAAAAAAAAB4Hng8eHh48Hnge8B/gH/AfcB44HjweHh4PHgceA4AAAAAAAAAAAAADgAAAAAAAAAAAAB4AHgAeAB4AHgAeAB4AHgAeAB4AHgAeAB4AH/4f/gAAAAAAAAAAAAAEwAAAAAAAAAAAAAAAAAAAHwPgHwPgH4PgH4PgH4fgHYbgHcbgHM7gHMzgHOzgHHzgHHjgHHjgHDjgHDDgAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAeAx8DH4Mfgx3DHcMc4xzjHHMcOxw7HB8cHxwPHA8AAAAAAAAAAAAABIAAAAAAAAAAAAAAAAAAAAH8AAP/AA//gA8HgB4DwBwBwBwBwBwBwBwBwBwBwB4DwA8HgAf/AAP+AAH4AAAAAAAAAAAAAAAAAAAAAAPAAAAAAAAAAAAAH/gf/h4+Hg8eBx4HHg8ePh/8H/geAB4AHgAeAB4AAAAAAAAAAAAAAASAAAAAAAAAAAAAAAAAAAAB/AAD/gAP/4APB4AeA8AcAcAcAcAcAcAcAcAcAcAeA8APA4APj4AH/wAB/AAAOAAAPAAAH4AAD4AAAAAEAAAAAAAAAAAAAB/8H/8eHx4HngeeBx4fH/4f/B4cHh4eDh4PHgeeA4AAAAAAAAAAAAADwAAAAAAAAAAAAAP4D/wPHh4OHgAPAA/wA/wAfgAPHAccDx8eD/4D+AAAAAAAAAAAAAADgAAAAAAAAAAAAD/+P/4B4AHAAcABwAHAAcABwAHAAcABwAHAAcABwAAAAAAAAAAAAAAEAAAAAAAAAAAAABwHnAecB5wHnAecB5wHnAecB54HngcODw//B/4B+AAAAAAAAAAAAAADwAAAAAAAAAAAADwHHAccDx4ODg4OHAccBxwHOAO4A7gD8AHwAfAA4AAAAAAAAAAAAAAFQAAAAAAAAAAAAAAAAAAAOBwePD4cHD4cHD4cHDYcHHc4Dnc4Dmc4DmM4DuNwB+PwB+PwB8PgA8HgA8HgAAAAAAAAAAAAAAAAAAAAA8AAAAAAAAAAAAAcDw4ODxwHPAO4A/AB8AHwAfADuAc8BxwODhwPHAcAAAAAAAAAAAAAA8AAAAAAAAAAAAAcBx4ODh4PHAc8A7gD8AHwAeAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAA4AAAAAAAAAAAAAf/B/8ADwAOAB4APAA4AHAA4AHgA8ADgAeAB/+H/4AAAAAAAAAAAAAAgAAAAAfn5wcHBwcHBwcHBwcHBwcHBwcH5+BwAAAADgYGBgcHBwMDA4ODgYGBwcAAAAAAAIAAAAAPz8HBwcHBwcHBwcHBwcHBwcHBz8/A0AAAAAAAAAAAAADwAPgA2AHcAYwDjAMOAwYHBwYDAAAAAAAAAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/wAAAAAAgAAAAAcDgMAAAAAAAAAAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOcAw4ADgH+B/4HDgceBz4H7wPHAAAAAAAAAAAAAADgAAAAAAAAAAOAA4ADgAOAA7wD/gPPA4cDhwOHg4eDhwOHA88D/gc8AAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOOBw4HAAcABwAHAAcOA44D/AD4AAAAAAAAAAAAAADgAAAAAAAAAAAHAAcABwAHAecD/wOPBw8HBwcHBwcHBwcPA48D/wHnAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAPgD/AOOBw4HDgf+B/4HAAcAA44D/AD4AAAAAAAAAAAAAACAAAAAAePjg4/v44ODg4ODg4ODg4AAAAAAAOAAAAAAAAAAAAAAAAAAAAAB5wP/A48HDwcHBwcHBwcHBw8DjwP/AecABwAHA44D/gD4AOAAAAAAAAAAA4ADgAOAA4ADvAP+A88DhwOHA4cDhwOHA4cDhwOHA4cAAAAAAAAAAAAAAHAAAAADg4AAA4ODg4ODg4ODg4ODgAAAAAAAcAAAAAODgAADg4ODg4ODg4ODg4ODg4cPDgDQAAAAAAAAAAOAA4ADgAOAA48DngOcA7gD8APwA/gDvAOcA44DjgOHAAAAAAAAAAAAAABwAAAAA4ODg4ODg4ODg4ODg4ODg4AAAAAAAUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAc8eAN++APfvAOPHAOPHAOOHAOOHAOOHAOOHAOOHAOOHAOOHAAAAAAAAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAABzwDfgPPA4cDhwOHA4cDhwOHA4cDhwOHAAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAAAPgB/gOPB4cHBwcHhweHBweHA48B/gD4AAAAAAAAAAAAAADgAAAAAAAAAAAAAAAAAAAABzwD/gPPA4cDhwOHg4eDhwOHA88D/gO8A4ADgAOAA4ADgADgAAAAAAAAAAAAAAAAAAAAAecD/wOPBw8HBwcHBwcHBwcPA48D/wHnAAcABwAHAAcABwCQAAAAAAAAAAAAAAAAAAAABzADcAPwA4ADgAOAA4ADgAOAA4ADgAOAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAAAfgD/AcOBwwHwAP4AP4AHgcOBw4D/gH4AAAAAAAAAAAAAACAAAAAAAGDg4/v44ODg4ODg4OD4eAAAAAAAOAAAAAAAAAAAAAAAAAAAAAHBwcHBwcHBwcHBwcHBwcHB48D3wP3AecAAAAAAAAAAAAAANAAAAAAAAAAAAAAAAAAAAAOBwcHBw4HDgOOA5wDnAHYAfgB+ADwAPAAAAAAAAAAAAAAASAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA4cOA4eOAY+OAY2MAc2cAc3cANzcANjYAPj4APj4AHhwAHBwAAAAAAAAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAABw4HjgOcAfgB+ADwAPAB+AHcA5wHDg8PAAAAAAAAAAAAAADQAAAAAAAAAAAAAAAAAAAADwcHBwcOAw4DjAOcAZwB2AH4APgA8ABwAHAA4AHgB8AHgACwAAAAAAAAAAAAAAAAAAAAB/wH/AA4AHgAcADgAeABwAOAB4AH/Af8AAAAAAAAAAAAAACQAAAAAAAAAADwAfABwAHAAcABwAHAAcADgA8ADwADgAHAAcABwAHAAcABwAHAAfAA8ABwAAAAAwMDAwMDAwMDAwMDAwMDAwMDAwMDAJAAAAAAAAAADwAPgAPAAcABwAHAAcABwAHgAPAA8AHgAcABwAHAAcABwAHAA8APgA8AANAAAAAAAAAAAAAAAAAAAAAAAAAAA8AH8wR/AB4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAA4ODgAAAAAAAAAAAAAABYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///z///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAAA4ODgQEDAAAAAAAAAAAAAAAAAAAA0AAAAAAAAAAAAAD4Af4DzgOHA4AP8AfgB4AP8AfwA4ADhwPOAf4AeAAAAAAAAAAAAAAA=="

# Each entry: (name, characters, pixel height, blob, decoded byte size).
_FONT_TABLE = [
    ("sans10", CHARS, 13, F_SANS10, 1464),
    ("sans12", CHARS, 14, F_SANS12, 1709),
    ("sansb10", CHARS, 13, F_SANSB10, 1464),
    ("sansb15", CHARS, 18, F_SANSB15, 3123),
    ("sansb22", CHARS, 25, F_SANSB22, 4699),
]


def _decode_fonts():
    """Turn the blobs above into {name: (height, {char: (width, bits)})}."""
    fonts = {}
    for name, chars, height, blob, want in _FONT_TABLE:
        raw = base64.b64decode(blob)
        if len(raw) != want:
            raise ValueError("font %s decoded to %d bytes, expected %d"
                             % (name, len(raw), want))
        glyphs = {}
        pos = 0
        for ch in chars:
            w = raw[pos]
            pos += 1
            step = (w + 7) // 8
            glyphs[ch] = (w, raw[pos:pos + step * height])
            pos += step * height
        if pos != len(raw):
            raise ValueError("font %s parse ended at %d of %d"
                             % (name, pos, len(raw)))
        fonts[name] = (height, glyphs)
    return fonts


# ------------------------------------------------------------------ canvas
W = H = 1024

PAPER = (247, 243, 235)
INK = (24, 24, 24)
RED = (166, 38, 38)
NAVY = (15, 28, 46)
GOLD = (212, 164, 65)
GREY = (96, 90, 74)
OCEAN = (214, 228, 232)
LAND = (232, 220, 190)
DUSK = (38, 52, 74)
CREAM = (239, 231, 214)
BURST = (205, 72, 25)
WHITE = (255, 255, 255)


class Canvas:
    """A plain RGB bytearray picture with small drawing helpers.

    The buffer is one flat bytearray, three bytes per pixel, row-major.
    Every helper clips to the 1024x1024 frame, so callers never have
    to check bounds themselves.
    """

    def __init__(self, bg):
        self.px = bytearray(bytes(bg) * (W * H))

    def put(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            o = (y * W + x) * 3
            self.px[o:o + 3] = bytes(c)

    def fill(self, x, y, w, h, c):
        """Solid rectangle, clipped."""
        x0 = x if x > 0 else 0
        y0 = y if y > 0 else 0
        x1 = x + w if x + w < W else W
        y1 = y + h if y + h < H else H
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            o = (yy * W + x0) * 3
            self.px[o:o + len(row)] = row

    def hline(self, x0, x1, y, c, t=1):
        for k in range(t):
            self.fill(x0, y + k, x1 - x0, 1, c)

    def vline(self, x, y0, y1, c, t=1):
        for k in range(t):
            self.fill(x + k, y0, 1, y1 - y0, c)

    def rect(self, x, y, w, h, c, t=1):
        self.hline(x, x + w, y, c, t)
        self.hline(x, x + w, y + h - t, c, t)
        self.vline(x, y, y + h, c, t)
        self.vline(x + w - t, y, y + h, c, t)

    def disc(self, cx, cy, r, c):
        """Filled disc."""
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.fill(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def poly(self, pts, c):
        """Filled polygon (scanline fill)."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                x0 = int(math.ceil(xs[i]))
                x1 = int(xs[i + 1])
                if x1 > x0:
                    self.fill(x0, y, x1 - x0, 1, c)

# ------------------------------------------------------------------ typing
_FONTS = _decode_fonts()


def _glyph(font, ch):
    """(width, bits) for one char; unknown chars fall back to '?'."""
    height, glyphs = _FONTS[font]
    if ch not in glyphs:
        ch = "?"
    return glyphs[ch]


def text_w(font, s):
    """Pixel width of s in font (1px tracking)."""
    height, glyphs = _FONTS[font]
    total = 0
    for ch in s:
        w, _bits = _glyph(font, ch)
        total += w + 1
    return total - 1 if total else 0


def draw_text(cv, font, x, y, s, color):
    """Draw s with its top at y; returns the x just past the text."""
    height, glyphs = _FONTS[font]
    cx = x
    for ch in s:
        w, bits = _glyph(font, ch)
        step = (w + 7) // 8
        for row in range(height):
            brow = bits[row * step:(row + 1) * step]
            for col in range(w):
                if brow[col // 8] & (0x80 >> (col % 8)):
                    cv.put(cx + col, y + row, color)
        cx += w + 1
    return cx


def draw_text_right(cv, font, x_right, y, s, color):
    draw_text(cv, font, x_right - text_w(font, s), y, s, color)


def draw_text_centred(cv, font, cx, y, s, color):
    draw_text(cv, font, cx - text_w(font, s) // 2, y, s, color)


def wrap(font, s, max_w):
    """Greedy word wrap; returns a list of lines, each <= max_w px."""
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(font, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


_CUTS = []


def fit_lines(font, s, max_w, max_lines):
    """Wrap s, keep at most max_lines, '...' on the last if cut."""
    lines = wrap(font, s, max_w)
    if len(lines) <= max_lines:
        return lines
    _CUTS.append("fit_lines(%r, %d lines -> %d)" % (s, len(lines), max_lines))
    lines = lines[:max_lines]
    while lines and text_w(font, lines[-1] + "...") > max_w:
        lines[-1] = lines[-1][:-1]
    lines[-1] = lines[-1] + "..."
    return lines


def trunc(font, s, max_w):
    """One line, cut with '...' if it does not fit."""
    if text_w(font, s) <= max_w:
        return s
    _CUTS.append("trunc(%r)" % (s,))
    while s and text_w(font, s + "...") > max_w:
        s = s[:-1]
    return s + "..."


def _check_chars():
    """Every drawn string must use only glyphs the fonts carry.

    A missing glyph prints as '?', which is how the 20261123 build's
    '?' artefacts looked — fail loudly here instead of shipping them.
    """
    allowed = set(CHARS)
    fixed = ["THE WORLD IN ONE PICTURE", "TUESDAY 24 NOVEMBER 2026",
             "54 STORIES \u00b7 ALL TIMES UTC",
             "The day's world news, summed up in one picture \u2014 "
             "every fact checked, every source named.",
             "THE DAY IN UTC \u2014 TUESDAY 24 NOVEMBER 2026",
             "WHERE IT HAPPENED \u2014 15 PLACES",
             "MORE NEWS", "MORE NEWS, CONTINUED",
             "DATE CHECK \u2014 events in this picture that happened on "
             "other days",
             "Sources: Reuters \u00b7 CNN \u00b7 WSJ \u00b7 BBC \u00b7 AFP \u00b7 AP \u00b7 "
             "Kyiv Independent \u00b7 ISW \u00b7 USGS \u00b7 Xinhua \u00b7 dailysummaryof"]
    strings = list(fixed)
    for kicker, head, deck, src, _motif in LEADS:
        strings += [kicker, head, deck, src]
    for head, deck in MEDIUM:
        strings += [head, deck]
    for head, src in LIST_A + LIST_B:
        strings += [head, src]
    for t, text in TIMELINE:
        strings += [t, text]
    for label, when in DATECHECK:
        strings += [label, when]
    for _n, label, _lon, _lat in MAP_DOTS:
        strings.append(label)
    bad = sorted({ch for s in strings for ch in s if ch not in allowed})
    if bad:
        raise ValueError("characters with no glyph: %r" % (bad,))


# ------------------------------------------------------------------ PNG out
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    """Encode the canvas as a deterministic PNG (filter 0, zlib level 6)."""
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.px[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    return png

# ------------------------------------------------------------------ data
# Every story below was verified against a named source on 24 Nov 2026
# (see news-research-2026-11-24.md). Headlines and decks are written to
# fit the boxes they land in; sources are the outlet that reported it.

LEADS = [
    # (kicker, headline, deck, source, motif)
    ("MARKETS \u00b7 WASHINGTON",
     "Huang is back at Nvidia \u2014 and the markets roar",
     "Nvidia's board reinstated Jensen Huang as CEO, 11 days after he "
     "resigned, after President Trump personally pressed the board. "
     "Shares soared 31.5% on Monday, adding a record $952bn of value. "
     "The S&P 500 jumped 4.7% and the Nasdaq 6.5%.",
     "Reuters \u00b7 CNN \u00b7 WSJ", "bars"),
    ("JUSTICE \u00b7 MYANMAR",
     "14 nations back the ICJ genocide ruling on Myanmar",
     "Fourteen countries jointly acknowledged the court's binding ruling "
     "that Myanmar committed genocide against the Rohingya in 2017. "
     "Britain formally recognised the genocide, sanctioned five senior "
     "military figures and pledged $6.5m in aid.",
     "AFP \u00b7 France 24 \u00b7 UK FCDO", "scales"),
    ("SECURITY \u00b7 NATO",
     "NATO vows to defend space as Russia 'plans nuclear satellite'",
     "NATO chief Mark Rutte said the alliance will defend against any "
     "threat in space after reports that Russia may launch a nuclear-"
     "armed satellite, dubbed Sputnik-S, within 60 days. Moscow "
     "dismissed the reports as 'unfounded allegations'.",
     "BBC \u00b7 Kyiv Independent", "orbit"),
]

MEDIUM = [
    # (headline, deck) — deck ends with its source.
    ("US blacklists Megaspeed in Nvidia spy scandal",
     "Megaspeed and six firms hit the Entity List; licences now "
     "needed. \u2014 dailysummaryof"),
    ("US drone helped capture El Chapo Isidro",
     "A US drone helped nab the cartel boss in Sinaloa; Mexico will "
     "try him. \u2014 dailysummaryof"),
    ("Nepal quake 5.6, no casualties reported",
     "Taplejung shook at 07:17 local; tremors felt in India, Bhutan "
     "and China. \u2014 Xinhua \u00b7 USGS"),
    ("Sanofi buys Insmed for $41bn",
     "Sanofi's takeover of US biotech Insmed is the biggest biotech "
     "deal in years. \u2014 Reuters"),
    ("Malaysia to return migrants to Myanmar",
     "Thousands to be sent back: 1,500 by ship in Dec, 5,303 by air. "
     "\u2014 dailysummaryof"),
    ("Hasina plans December 16 return",
     "The exiled ex-PM will fly home on Victory Day; Dhaka wants her "
     "extradited. \u2014 dailysummaryof"),
    ("Indonesia names two VP candidates",
     "Prabowo names Amran Sulaiman and Sugiono to replace Gibran. "
     "\u2014 dailysummaryof"),
    ("China sentences spy official to death",
     "An official surnamed Ma got death for spying: 35 secrets passed, "
     "over 1m yuan paid. \u2014 dailysummaryof"),
    ("700,000+ Russian soldiers killed",
     "Meduza and Mediazona, using breached Rosstat data, put Russia's "
     "dead past 700,000. \u2014 RFE/RL"),
    ("Ukraine hits Russian ships off Libya",
     "Kyiv confirms Nov 22 drone strikes near Benghazi; a Russian "
     "warship exploded and sank. \u2014 ISW \u00b7 UN"),
    ("Gaza strikes kill six; 77 years undone",
     "Israeli strikes killed six in Gaza; the UN says 77 years of "
     "progress erased. \u2014 Reuters"),
    ("DRC fighting traps Ebola teams",
     "Fighting in Ituri forced responders to shelter 'for their lives' "
     "for over 24 hours, the WHO says. \u2014 UN News"),
]

LIST_A = [
    ("COP31 collapse splits world", "Analysis"),
    ("States sue over Grok images", "Principia"),
    ("Arm extends CEO Haas to 2033", "IQMIA"),
    ("Somalia, Uganda vs al-Shabaab", "IQMIA"),
    ("EU visa curbs on Russians", "Kyiv Ind."),
    ("Germany gets Ukraine Delta", "Kyiv Ind."),
    ("Iraq takes Kurdish oilfields", "Reuters"),
    ("Zaporizhzhia strike kills 2", "Kyiv Ind."),
    ("Drone crash in Transnistria", "Kyiv Ind."),
    ("Russian UAV enters Poland", "Kyiv Ind."),
    ("Russia rejects security vow", "ISW"),
    ("Russia fired 134 drones", "ISW"),
    ("Zelensky: 4-party talks", "DSummary"),
    ("Pentagon rebukes Canada", "DSummary"),
    ("Russian jets in Korea zone", "DSummary"),
    ("Bukele names 3 slain men", "DSummary"),
    ("Iran tankers hit mines", "DSummary"),
    ("Iran lashes singer Ahmadi", "Horizon"),
    ("Iran rules out US talks", "Horizon"),
    ("Dozens die in Saudi strikes", "Horizon"),
]

LIST_B = [
    ("Netanyahu urges Iran strikes", "10things"),
    ("Solomons ends China pact", "10things"),
    ("Russia warns Estonia of war", "IQMIA"),
    ("Burnham: no EU rejoin", "Global Eye"),
    ("KOSPI +6% as Asia rebounds", "Horizon"),
    ("Europe up; gold $3,620", "Horizon"),
    ("US measles status lost", "Principia"),
    ("FDA okays limb-girdle drug", "Principia"),
    ("Farthest black hole found", "Principia"),
    ("First foreigner on Tiangong", "Horizon"),
    ("Car bomb rocks Villavicencio", "Horizon"),
    ("WHO chief visits ailing Cuba", "Horizon"),
    ("Hernandez de Cos for ECB", "Horizon"),
    ("Macron eyes rare-earth stock", "Horizon"),
    ("47,000 women killed in 2025", "Principia"),
    ("Food aid at risk for 7.3m", "10things"),
    ("Guterres wants AI rules soon", "Horizon"),
    ("Oxfam: Gaza a 'toxic land'", "Horizon"),
    ("Lilly Jones stabbed in Blaina", "IQMIA"),
]

# Six events, every one first reported on Tue 24 Nov 2026 UTC
# (times from dailysummaryof.com). No hours borrowed from other days.
TIMELINE = [
    ("00:30", "Zelensky urges four-party talks"),
    ("00:52", "US blacklists Megaspeed"),
    ("01:04", "Russian jets enter Korea zone"),
    ("02:09", "US drone helped nab El Chapo Isidro"),
    ("02:38", "Indonesia names two VP picks"),
    ("03:50", "Hasina plans Dec 16 return"),
]

DATECHECK = [
    ("Huang reinstated", "Mon 23 Nov"),
    ("US rally: S&P +4.7%", "Mon 23 Nov"),
    ("ICJ ruling on Myanmar", "Thu 19 Nov"),
    ("14 nations back ruling", "Mon 23 Nov"),
    ("COP31 collapsed", "Sun 22 Nov"),
    ("Ships hit off Libya", "Sun 22 Nov"),
    ("Missiles into Poland", "Fri 20 Nov"),
    ("UAV into Poland", "late Sun 22 Nov"),
    ("Zaporizhzhia strike", "late Mon 23 Nov"),
    ("Transnistria drone", "eve Mon 23 Nov"),
    ("NATO address; visa letter", "Mon 23 Nov"),
    ("700,000-killed tally", "Mon 23 Nov"),
]

# (number, short label, lon, lat) — plotted on the map.
MAP_DOTS = [
    (1, "California, US", -122.0, 37.0),
    (2, "Myanmar", 96.0, 21.0),
    (3, "Brussels", 4.4, 50.8),
    (4, "Strait of Hormuz", 56.5, 26.5),
    (5, "Sinaloa, Mexico", -107.0, 24.5),
    (6, "Taplejung, Nepal", 87.9, 27.9),
    (7, "Benghazi, Libya", 20.1, 32.1),
    (8, "Gaza", 34.5, 31.5),
    (9, "Zaporizhzhia", 35.2, 47.8),
    (10, "South Korea", 129.0, 36.0),
    (11, "Haiti", -72.5, 18.9),
    (12, "Ituri, DR Congo", 29.5, 1.5),
    (13, "Paris", 2.35, 48.85),
    (14, "London", -0.1, 51.5),
    (15, "Jakarta", 106.8, -6.2),
]

# Simplified continent outlines, (lon, lat) points, my own approximations.
NORTH_AMERICA = [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-115, 73),
                 (-100, 73), (-90, 74), (-85, 70), (-80, 73), (-75, 72),
                 (-70, 62), (-65, 60), (-60, 52), (-55, 47), (-60, 45),
                 (-65, 44), (-70, 42), (-75, 38), (-76, 35), (-80, 32),
                 (-81, 26), (-84, 30), (-89, 29), (-91, 19), (-94, 17),
                 (-97, 16), (-100, 20), (-105, 20), (-110, 23), (-114, 29),
                 (-120, 34), (-124, 40), (-124, 48), (-130, 54), (-140, 60),
                 (-150, 61), (-158, 58), (-165, 60)]
GREENLAND = [(-58, 64), (-52, 60), (-45, 60), (-40, 64), (-32, 68),
             (-25, 70), (-20, 74), (-25, 78), (-35, 80), (-50, 80),
             (-58, 76), (-60, 70)]
ICELAND = [(-22, 64), (-18, 63), (-14, 64), (-16, 66), (-20, 66), (-23, 65)]
SOUTH_AMERICA = [(-80, 9), (-75, 11), (-70, 12), (-62, 10), (-55, 6),
                 (-52, 4), (-50, 0), (-48, -5), (-40, -10), (-35, -8),
                 (-38, -15), (-40, -22), (-48, -27), (-52, -33), (-58, -38),
                 (-62, -41), (-65, -45), (-68, -50), (-70, -54), (-74, -53),
                 (-73, -45), (-73, -37), (-71, -30), (-70, -23), (-75, -15),
                 (-80, -6), (-81, -1), (-80, 5)]
AFRICA = [(-17, 15), (-16, 20), (-12, 26), (-9, 31), (-5, 35), (0, 36),
          (10, 37), (20, 32), (25, 32), (30, 31), (33, 27), (35, 28),
          (38, 22), (40, 15), (43, 11), (48, 11), (51, 10), (46, 5),
          (42, 0), (40, -5), (38, -12), (36, -18), (33, -25), (28, -32),
          (20, -35), (16, -30), (14, -22), (12, -15), (13, -10), (12, -5),
          (9, 0), (9, 4), (-8, 5), (-13, 8), (-17, 12)]
EURASIA = [(-10, 36), (-9, 43), (-2, 48), (0, 50), (-5, 50), (2, 51),
           (5, 53), (8, 57), (10, 59), (5, 60), (5, 62), (10, 64),
           (12, 66), (18, 69), (25, 71), (30, 70), (40, 68), (50, 69),
           (60, 70), (70, 72), (80, 73), (90, 75), (100, 77), (110, 76),
           (120, 73), (130, 72), (140, 72), (150, 70), (160, 70),
           (170, 69), (178, 66), (170, 64), (162, 60), (158, 56),
           (150, 60), (142, 55), (140, 50), (135, 45), (130, 42),
           (127, 40), (122, 38), (120, 32), (122, 28), (118, 25),
           (110, 20), (108, 12), (105, 8), (100, 6), (98, 10), (95, 15),
           (92, 20), (90, 22), (86, 20), (82, 17), (80, 13), (77, 8),
           (74, 12), (72, 20), (68, 23), (62, 25), (58, 26), (55, 27),
           (52, 28), (50, 29), (48, 30), (44, 29), (40, 28), (38, 24),
           (36, 20), (35, 15), (38, 18), (42, 18), (44, 16), (48, 14),
           (52, 12), (55, 15), (58, 18), (60, 20), (62, 22), (60, 25),
           (57, 26), (54, 24), (50, 26), (48, 28), (46, 30), (42, 32),
           (40, 36), (35, 36), (30, 36), (26, 38), (23, 40), (20, 40),
           (18, 42), (15, 44), (12, 44), (8, 44), (3, 42), (0, 38),
           (-2, 37), (-6, 36)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
      (-2, 50)]
JAPAN = [(130, 31), (132, 33), (135, 34), (138, 35), (140, 37), (141, 40),
         (142, 43), (144, 44), (142, 45), (140, 42), (139, 38), (137, 36),
         (133, 35), (131, 33)]
SUMATRA = [(95, 5), (98, 2), (101, -1), (104, -3), (106, -6), (103, -4),
           (100, 0), (97, 4)]
BORNEO = [(109, 1), (112, 3), (116, 6), (118, 2), (117, -2), (114, -4),
          (110, -3), (109, -1)]
JAVA = [(105, -6), (110, -7), (114, -8), (114, -9), (108, -8), (105, -7)]
NEW_GUINEA = [(131, -1), (136, -2), (141, -3), (146, -6), (148, -8),
              (143, -8), (138, -8), (133, -4), (131, -2)]
AUSTRALIA = [(113, -22), (114, -30), (115, -34), (118, -35), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
             (146, -19), (142, -15), (142, -11), (140, -17), (136, -15),
             (135, -12), (132, -11), (130, -13), (126, -14), (122, -17),
             (118, -20)]
NEW_ZEALAND = [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38),
               (178, -37), (175, -40), (172, -43), (169, -46)]
MADAGASCAR = [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24),
              (45, -25), (43, -22), (43, -18)]
CONTINENTS = [NORTH_AMERICA, GREENLAND, ICELAND, SOUTH_AMERICA, AFRICA,
              EURASIA, UK, JAPAN, SUMATRA, BORNEO, JAVA, NEW_GUINEA,
              AUSTRALIA, NEW_ZEALAND, MADAGASCAR]

# ------------------------------------------------------------------ layout
M = 20            # outer margin
CW = 1024 - 2 * M  # content width


def draw_motif(cv, kind, x, y, w, h):
    """Small geometric picture inside a lead panel."""
    if kind == "bars":
        base = y + h - 4
        bw = 26
        gap = 10
        for i in range(5):
            bh = 8 + i * 7
            col = BURST if i % 2 == 0 else NAVY
            cv.fill(x + 8 + i * (bw + gap), base - bh, bw, bh, col)
        cv.hline(x + 4, x + w - 4, base, INK, 2)
    elif kind == "scales":
        cx = x + w // 2
        top = y + 6
        cv.vline(cx, top, top + h - 12, NAVY, 3)
        cv.hline(cx - 56, cx + 56, top + 4, NAVY, 3)
        for side in (-1, 1):
            px = cx + side * 52
            cv.vline(px, top + 4, top + 22, NAVY, 2)
            cv.disc(px, top + 30, 12, GOLD)
            cv.fill(px - 12, top + 30, 24, 2, NAVY)
        cv.disc(cx, top + 2, 4, RED)
    elif kind == "orbit":
        cx = x + w // 2
        cy = y + h // 2
        cv.disc(cx, cy, 12, NAVY)
        for k in range(-70, 71, 2):
            px = cx + k
            py = cy + int(0.42 * k)
            cv.put(px, py, RED)
            cv.put(px, py + 1, RED)
        cv.disc(cx + 58, cy + 24, 4, BURST)
        cv.disc(cx - 58, cy - 24, 3, GOLD)


def draw_masthead(cv):
    draw_text(cv, "sansb22", M, 12, "THE WORLD IN ONE PICTURE", INK)
    draw_text_right(cv, "sansb15", 1024 - M, 14,
                    "TUESDAY 24 NOVEMBER 2026", NAVY)
    draw_text_right(cv, "sans10", 1024 - M, 36,
                    "54 STORIES \u00b7 ALL TIMES UTC", GREY)
    draw_text(cv, "sans12", M, 46,
              "The day's world news, summed up in one picture \u2014 "
              "every fact checked, every source named.", INK)
    cv.hline(M, 1024 - M, 82, INK, 3)
    cv.hline(M, 1024 - M, 87, GOLD, 2)


def draw_timeline(cv):
    y0 = 94
    draw_text(cv, "sansb10", M, y0,
              "THE DAY IN UTC \u2014 TUESDAY 24 NOVEMBER 2026", RED)
    slot_w = CW // 6
    for i, (t, text) in enumerate(TIMELINE):
        x = M + i * slot_w
        draw_text(cv, "sansb10", x + 2, y0 + 18, t, RED)
        for j, line in enumerate(fit_lines("sans10", text, slot_w - 8, 2)):
            draw_text(cv, "sans10", x + 2, y0 + 33 + j * 12, line, INK)
        if i:
            cv.vline(x, y0 + 16, y0 + 56, GREY, 1)


def draw_leads(cv):
    y0 = 156
    h = 236
    col_w = 322
    for i, (kicker, head, deck, src, motif) in enumerate(LEADS):
        x = M + i * (col_w + 10)
        cv.fill(x, y0, col_w, h, CREAM)
        cv.rect(x, y0, col_w, h, GREY, 1)
        draw_text(cv, "sansb10", x + 10, y0 + 8, kicker, RED)
        for j, line in enumerate(fit_lines("sansb15", head, col_w - 20, 3)):
            draw_text(cv, "sansb15", x + 10, y0 + 26 + j * 18, line, INK)
        draw_motif(cv, motif, x + 10, y0 + 86, col_w - 20, 42)
        for j, line in enumerate(fit_lines("sans10", deck, col_w - 20, 5)):
            draw_text(cv, "sans10", x + 10, y0 + 136 + j * 12, line, INK)
        cv.hline(x + 10, x + col_w - 10, y0 + 204, GREY, 1)
        draw_text(cv, "sansb10", x + 10, y0 + 212, src, GREY)


def draw_medium(cv):
    y0 = 398
    col_w = 322
    cell_h = 59
    for r in range(4):
        for c in range(3):
            idx = r * 3 + c
            head, deck = MEDIUM[idx]
            x = M + c * (col_w + 10)
            y = y0 + r * cell_h
            for j, line in enumerate(fit_lines("sansb10", head,
                                               col_w - 8, 2)):
                draw_text(cv, "sansb10", x + 4, y + 2 + j * 13, line, INK)
            for j, line in enumerate(fit_lines("sans10", deck,
                                               col_w - 8, 2)):
                draw_text(cv, "sans10", x + 4, y + 30 + j * 12, line, GREY)
            if r < 3:
                cv.hline(x, x + col_w, y + cell_h - 1, GREY, 1)
            if c < 2:
                cv.vline(x + col_w + 5, y, y + cell_h - 1, GREY, 1)


def _lonlat_to_xy(lon, lat, mx, my, mw, mh):
    x = mx + int((lon + 180.0) / 360.0 * mw)
    y = my + int((75.0 - lat) / 130.0 * mh)
    return x, y


def draw_map(cv, mx, my, mw, mh):
    cv.fill(mx, my, mw, mh, OCEAN)
    cv.rect(mx, my, mw, mh, GREY, 1)
    for poly in CONTINENTS:
        pts = [_lonlat_to_xy(lon, lat, mx, my, mw, mh) for lon, lat in poly]
        cv.poly(pts, LAND)
    for n, label, lon, lat in MAP_DOTS:
        x, y = _lonlat_to_xy(lon, lat, mx, my, mw, mh)
        cv.disc(x, y, 8, RED)
        cv.disc(x, y, 8, RED)
        num = str(n)
        draw_text(cv, "sansb10", x - text_w("sansb10", num) // 2,
                  y - 5, num, WHITE)


def draw_bottom(cv):
    y0 = 640
    # Map box.
    draw_text(cv, "sansb10", M, y0 + 6, "WHERE IT HAPPENED \u2014 15 PLACES",
              NAVY)
    draw_map(cv, M, y0 + 24, 480, 184)
    for row in range(5):
        for col in range(3):
            idx = row * 3 + col
            if idx >= len(MAP_DOTS):
                break
            n, label, _lon, _lat = MAP_DOTS[idx]
            x = M + 8 + col * 160
            y = y0 + 214 + row * 17
            draw_text(cv, "sansb10", x, y, "%d" % n, RED)
            draw_text(cv, "sans10", x + 16, y,
                      trunc("sans10", label, 138), INK)
    # Story lists.
    for ci, (title, items) in enumerate(
            (("MORE NEWS", LIST_A), ("MORE NEWS, CONTINUED", LIST_B))):
        x = 512 + ci * 252
        col_w = 244 if ci == 0 else 240
        draw_text(cv, "sansb10", x, y0 + 6, title, NAVY)
        for i, (head, src) in enumerate(items):
            y = y0 + 22 + i * 14
            suffix = " \u00b7 " + src
            avail = col_w - text_w("sans10", suffix) - 10
            cv.disc(x + 14, y + 6, 2, RED)
            draw_text(cv, "sans10", x + 20, y, trunc("sans10", head, avail),
                      INK)
            draw_text(cv, "sans10", x + 20 + text_w(
                "sans10", trunc("sans10", head, avail)), y, suffix, GREY)


def draw_datecheck(cv):
    y0 = 942
    draw_text(cv, "sansb10", M, y0,
              "DATE CHECK \u2014 events in this picture that happened on "
              "other days", RED)
    col_w = CW // 4
    for i, (label, when) in enumerate(DATECHECK):
        x = M + (i % 4) * col_w
        y = y0 + 17 + (i // 4) * 16
        line = trunc("sans10", label + " \u2014 " + when, col_w - 6)
        draw_text(cv, "sans10", x + 2, y, line, INK)


def draw_footer(cv):
    draw_text(cv, "sans10", M, 1010,
              trunc("sans10",
                    "Sources: Reuters \u00b7 CNN \u00b7 WSJ \u00b7 BBC \u00b7 AFP \u00b7 AP \u00b7 "
                    "Kyiv Independent \u00b7 ISW \u00b7 USGS \u00b7 Xinhua \u00b7 dailysummaryof",
                    CW), GREY)


def build():
    cv = Canvas(PAPER)
    draw_masthead(cv)
    draw_timeline(cv)
    draw_leads(cv)
    draw_medium(cv)
    draw_bottom(cv)
    draw_datecheck(cv)
    draw_footer(cv)
    return cv


# ------------------------------------------------------------------ main
def story_count():
    return len(LEADS) + len(MEDIUM) + len(LIST_A) + len(LIST_B)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", "-o", default=None,
                    help="where to write entry.png")
    ap.add_argument("--check", action="store_true",
                    help="validate the entry and print its stats")
    args = ap.parse_args(argv)
    out = args.output
    if out is None:
        out = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"),
                           "entry.png")
    assert len(LEADS) == 3, "want 3 leads"
    assert len(MEDIUM) == 12, "want 12 medium stories"
    assert len(LIST_A) + len(LIST_B) == 39, "want 39 list stories"
    assert len(TIMELINE) == 6, "want 6 timeline slots"
    assert len(DATECHECK) == 12, "want 12 date-check rows"
    assert len(MAP_DOTS) == 15, "want 15 map dots"
    _check_chars()
    png = encode_png(build())
    if args.check:
        print("CHECK OK: %d stories (%d leads + %d medium + %d list), "
              "1024x1024, PNG %d bytes (%0.1f KB)"
              % (story_count(), len(LEADS), len(MEDIUM),
                 len(LIST_A) + len(LIST_B), len(png), len(png) / 1024.0))
        print("density: %.3f stories/KB" % (story_count() / (len(png) / 1024.0)))
        assert len(png) <= 1048576, "PNG over 1 MiB"
        if _CUTS:
            print("TEXT CUT (%d):" % len(_CUTS))
            for c in _CUTS:
                print("  -", c)
            return 1
        print("no text cut: every headline, deck, list item and label fits")
        return 0
    parent = os.path.dirname(os.path.abspath(out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out, "wb") as fh:
        fh.write(png)
    print("wrote %s (%d bytes, sha256 %s)"
          % (out, len(png),
             __import__("hashlib").sha256(png).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
