"""Build the CelestialModern wordmarks in assets/type/: full-width section rules and project names.

CelestialModern is unicase: a capital in the source text gives the ornamented letter,
a lowercase one the plain letter. Text is therefore set in its real mixed case.
"""

import base64
import io
import json
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from glyphs import CELESTIAL, outline  # noqa: E402

INK = {"light": "#15100f", "dark": "#f1ebe6"}
RED = "#e8232a"
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
PROJECTS_DIR = os.path.expanduser("~/Projects")

SECTIONS = {"selected-work": "Selected Work", "stack": "Stack", "activity": "Activity", "find-me": "Find Me"}


def png_uri(image):
    buf = io.BytesIO()
    image.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def macease_badge(size):
    icon = Image.open(os.path.join(PROJECTS_DIR, "MacEase/docs/images/app-icon.png")).convert("RGBA")
    # macOS icons carry transparent padding; trim it so the badge matches the others optically.
    icon = icon.crop(icon.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox())
    icon = icon.resize((168, 168), Image.LANCZOS)
    return f'<image href="{png_uri(icon)}" width="{size}" height="{size}"/>'


def openshogi_badge(size):
    # OpenShogiAI has no icon of its own; this is the piece mark of its companion UI, kept as vector.
    with open(os.path.join(PROJECTS_DIR, "OpenShogiUI/public/favicon.svg")) as f:
        inner = re.search(r"<svg[^>]*>(.*)</svg>", f.read(), re.S).group(1)
    return f'<g transform="scale({size / 64:.4f})">{" ".join(inner.split())}</g>'


def qrnel_badge(size):
    # The real bootable code: 177 modules plus a 4-module quiet zone, kept at 2 px per module.
    qr = Image.open(os.path.join(PROJECTS_DIR, "qrnel/release/qrnel.png")).convert("L")
    qr = qr.resize((370, 370), Image.NEAREST).point(lambda v: 255 if v > 127 else 0).convert("1")
    return (
        f'<clipPath id="q"><rect width="{size}" height="{size}" rx="{size * 0.09:.1f}"/></clipPath>'
        f'<image href="{png_uri(qr)}" width="{size}" height="{size}" clip-path="url(#q)" style="image-rendering:pixelated"/>'
    )


PROJECTS = {
    "macease": ("MacEase", macease_badge),
    "openshogiai": ("OpenShogiAI", openshogi_badge),
    "qrnel": ("QRnel", qrnel_badge),
}


def spark(x, y, r, offset, ink):
    d = f"M0 {-2.6*r:.1f}Q0 0 {r:.1f} 0Q0 0 0 {2.6*r:.1f}Q0 0 {-r:.1f} 0Q0 0 0 {-2.6*r:.1f}Z"
    return (
        f'<g transform="translate({x:.1f} {y})"><path class="spark" fill="{ink}" d="{d}" '
        f'style="animation-delay:calc(var(--t0,0s) - {offset}s)"/></g>'
    )


def section(text, ink):
    """A 1600-wide rule with the words in the middle, so it always spans the hero's width."""
    w, h, size = 1600, 150, 76
    d, tw, _ = outline(CELESTIAL, text, size, tracking=0.24)
    left, right = (w - tw) / 2, (w + tw) / 2
    gap, y = 70, 75
    css = (
        ".spark{transform-box:fill-box;transform-origin:center;animation:spark 5.4s ease-in-out infinite}"
        ".bead{stroke-dashoffset:-2;animation:bead 7s cubic-bezier(.6,0,.3,1) var(--t0,0s) infinite}"
        "@keyframes spark{0%,100%{opacity:.25;transform:scale(.55)}50%{opacity:1;transform:scale(1)}}"
        "@keyframes bead{0%{stroke-dashoffset:4;opacity:0}8%{opacity:1}72%,100%{stroke-dashoffset:-104;opacity:1}}"
        + REDUCED
    )
    rules = ""
    for x1, x2 in ((left - gap, 40), (right + gap, w - 40)):
        line = f'd="M{x1:.1f} {y}H{x2}" fill="none"'
        # The one red point leaves the words along each rule.
        rules += (
            f'<path {line} stroke="{ink}" stroke-width="1.4" opacity=".28"/>'
            f'<path class="bead" {line} stroke="{RED}" pathLength="100" stroke-dasharray="4 200" '
            'stroke-width="3.4" stroke-linecap="round"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{text}">'
        f"<title>{text}</title><style>{css}</style>{rules}"
        f"{spark(left - gap / 2, y, 4.6, 0, ink)}{spark(right + gap / 2, y, 4.6, 2.7, ink)}"
        f'<path transform="translate({left:.1f} {y + size * 0.35:.1f})" d="{d}" fill="{ink}"/></svg>\n'
    )


# Every project shares one canvas width, so they shrink by the same factor on a
# narrow screen and the badges stay the same size as each other.
PROJECT_W, PROJECT_H = 560, 96


def project(text, badge, ink):
    badge_size, size, gap = 56, 58, 24
    d, tw, _ = outline(CELESTIAL, text, size, tracking=0.06)
    content = badge_size + gap + tw
    if content > PROJECT_W:
        raise ValueError(f"{text} needs {content:.0f} units, canvas is {PROJECT_W}")
    x = (PROJECT_W - content) / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {PROJECT_W} {PROJECT_H}" role="img" aria-label="{text}">'
        f"<title>{text}</title>"
        f'<g transform="translate({x:.1f} {(PROJECT_H - badge_size) / 2})">{badge(badge_size)}</g>'
        f'<path transform="translate({x + badge_size + gap:.1f} {PROJECT_H / 2 + size * 0.35:.1f})" d="{d}" fill="{ink}"/></svg>\n'
    )


def export_digits(path):
    """Outline the numerals once, so build_activity.py can set numbers where the font is absent."""
    digits = {}
    for ch in "0123456789,":
        d, advance, _ = outline(CELESTIAL, ch, 1000)
        digits[ch] = [d, round(advance + 40)]
    with open(path, "w") as f:
        json.dump(digits, f)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    export_digits(os.path.join(os.path.dirname(__file__), "digits.json"))
    for theme, ink in INK.items():
        for slug, text in SECTIONS.items():
            with open(os.path.join(out, f"{slug}-{theme}.svg"), "w") as f:
                f.write(section(text, ink))
        for slug, (text, badge) in PROJECTS.items():
            with open(os.path.join(out, f"{slug}-{theme}.svg"), "w") as f:
                f.write(project(text, badge, ink))
