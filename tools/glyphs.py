"""Outline text from a local font into SVG path data, so the font file itself never ships."""

import os

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

SPIKES = os.path.expanduser("~/Fonts/Spikes-Regular.otf")
METRICA = os.path.expanduser("~/Fonts/MetricaFF/Metrica-Regular.otf")
CELESTIAL = os.path.expanduser("~/Fonts/160K-AnnivPack-FREE/Y1_Standard_Fonts/CelestialModern/Y1CelestialModern.otf")

_cache = {}


def _load(path):
    if path not in _cache:
        with open(path, "rb") as f:
            hb_font = hb.Font(hb.Face(f.read()))
        tt = TTFont(path)
        _cache[path] = (hb_font, tt, tt.getGlyphSet(), tt.getGlyphOrder())
    return _cache[path]


def _shape(font_path, text):
    hb_font, tt, glyph_set, order = _load(font_path)
    missing = [c for c in text if c != " " and ord(c) not in tt.getBestCmap()]
    if missing:
        # A silent .notdef box would otherwise be baked into the artwork.
        raise ValueError(f"{os.path.basename(font_path)} has no glyph for {missing}")
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf)
    return buf, tt, glyph_set, order


def outline(font_path, text, size, tracking=0.0):
    """Return (path_d, width, spans) for `text` at `size` px, baseline y=0, origin x=0.

    `tracking` is extra letter spacing in em. `spans` is one (x, advance) per glyph.
    """
    buf, tt, glyph_set, order = _shape(font_path, text)
    scale = size / tt["head"].unitsPerEm
    pen = SVGPathPen(glyph_set, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    x, spans = 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        dx = x + pos.x_offset * scale
        # SVG's y axis points down, font units point up.
        glyph_set[order[info.codepoint]].draw(
            TransformPen(pen, (scale, 0, 0, -scale, dx, -pos.y_offset * scale))
        )
        spans.append((x, pos.x_advance * scale))
        x += pos.x_advance * scale + tracking * size
    return pen.getCommands(), x - tracking * size, spans


# The free Metrica ships empty outlines for lowercase, digits and punctuation.
# These are drawn to its rules: 20-unit monoline, rounded-rectangle bowls,
# an echo of the left curve, one construction diagonal. Units are 1/1000 em, y down.
METRICA_STROKE = 20
METRICA_DRAWN = {
    "@": (
        820,
        "M600 0H330A250 250 0 0 1 80 -250V-519A250 250 0 0 1 330 -769H480A250 250 0 0 1 730 -519"
        "V-330A77 77 0 0 1 576 -330V-560"
        "M576 -420V-340A140 140 0 0 1 436 -200H416A140 140 0 0 1 276 -340V-420"
        "A140 140 0 0 1 416 -560H436A140 140 0 0 1 576 -420"
        "M318 -520L534 -240",
    ),
    "g": (
        660,
        "M581 -315V-205A205 205 0 0 1 376 0A205 205 0 0 1 171 -205V-315"
        "A205 205 0 0 1 376 -520A205 205 0 0 1 581 -315"
        "M581 -520V25A205 205 0 0 1 376 230H190"
        "M262 -487A205 190 0 0 0 54 -300V-220A205 190 0 0 0 262 -33"
        "M452 -506L300 -14",
    ),
    "b": (
        650,
        "M54 -769V0M171 -769V0M54 -769L171 -660M54 0L171 -110"
        "M171 -520H376A205 205 0 0 1 581 -315V-205A205 205 0 0 1 376 0H171"
        "M171 -520L523 -62",
    ),
    "2": (
        600,
        "M60 -555A214 214 0 0 1 274 -769H326A214 214 0 0 1 540 -555L60 0H540"
        "M540 -420L177 0",
    ),
}


def metrica_mixed(text, size, tracking=0.0, color="currentColor", weight=0):
    """Set `text` in Metrica, substituting the drawn glyphs where the font is empty.

    `weight` thickens every stroke by that many 1/1000 em, for small sizes where
    the 20-unit hairline would fall below a device pixel.
    Returns (svg_markup, width) with the baseline at y=0.
    """
    scale = size / 1000
    parts, x = [], 0.0
    for ch in text:
        if ch in METRICA_DRAWN:
            advance, d = METRICA_DRAWN[ch]
            parts.append(
                f'<path transform="translate({x:.2f} 0) scale({scale:.4f})" d="{d}" fill="none" stroke="{color}" '
                f'stroke-width="{METRICA_STROKE + weight}" stroke-linecap="round" stroke-linejoin="round"/>'
            )
            x += advance * scale
        else:
            d, w, _ = outline(METRICA, ch, size)
            parts.append(
                f'<path transform="translate({x:.2f} 0)" d="{d}" fill="{color}" stroke="{color}" '
                f'stroke-width="{weight * scale:.3f}" stroke-linejoin="round"/>'
            )
            x += w
        x += tracking * size
    return "".join(parts), x - tracking * size
