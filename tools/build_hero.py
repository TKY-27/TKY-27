"""Build assets/hero-{light,dark}.svg.

The icon melts into the page (no frame, transparent canvas) and TKY-27 shows the
art inverted wherever a letter crosses it. The red eye is kept in front of the type.
"""

import base64
import io
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from glyphs import SPIKES, metrica_mixed, outline  # noqa: E402

ICON = os.path.expanduser("~/Desktop/icon.png")
W, H = 1600, 920

# Measured on the source art, as fractions of its width: the sharp lens circle and the red iris.
ART_ASPECT = 6304 / 6000
LENS_CX, LENS_CY, LENS_R = 0.4877, 0.4903, 0.388
EYE_X, EYE_Y, EYE_R = 0.409, 0.534, 0.047

THEMES = {
    "light": dict(ink="#15100f", label="#4a3f44", mist="#c9a7b6", mist_opacity=0.30, star_opacity=0.75),
    "dark": dict(ink="#f1ebe6", label="#b9aab1", mist="#7a4f63", mist_opacity=0.34, star_opacity=0.95),
}


def icon_data_uri(px, gamma):
    """Downscale the icon and deepen its midtones.

    Inversion gives no contrast at 50% grey, and the hair sits right there,
    so the tone curve is bent before the letters invert it.
    """
    im = Image.open(ICON).convert("RGB")
    im = im.resize((px, round(px * ART_ASPECT)), Image.LANCZOS)
    im = im.point([round(255 * (v / 255) ** gamma) for v in range(256)] * 3)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def star(x, y, r, delay, dur):
    # Tall four-point spark, echoing the spikes that grow out of the typeface.
    d = f"M0 {-2.6*r:.1f}Q0 0 {r:.1f} 0Q0 0 0 {2.6*r:.1f}Q0 0 {-r:.1f} 0Q0 0 0 {-2.6*r:.1f}Z"
    return (
        f'<g transform="translate({x:.0f} {y:.0f})"><path class="star" '
        f'style="animation-delay:calc(var(--t0,0s) - {delay:.2f}s);animation-duration:{dur:.2f}s" d="{d}"/></g>'
    )


def build(theme_name):
    t = THEMES[theme_name]

    title_size = 500
    title_d, title_w, spans = outline(SPIKES, "TKY-27", title_size, tracking=0.012)
    title_x, title_y = (W - title_w) / 2, 612
    y_stem_x = title_x + spans[2][0] + spans[2][1] / 2

    # The lens is placed so the iris lands on the stem of the Y.
    lens_r = 352
    art_w = lens_r / LENS_R
    art_h = art_w * ART_ASPECT
    eye_x, eye_y = y_stem_x, 476
    ax, ay = eye_x - EYE_X * art_w, eye_y - EYE_Y * art_w
    cx, cy = ax + LENS_CX * art_w, ay + LENS_CY * art_w
    eye_r = EYE_R * art_w

    handle, handle_w = metrica_mixed("@ANAg2bGOD", 60, tracking=0.2, color=t["ink"], weight=14)

    rng = random.Random(27)
    stars = []
    while len(stars) < 30:
        x, y = rng.uniform(30, W - 30), rng.uniform(100, H - 110)
        # Keep sparks off the lens interior, where they would read as dust on the face.
        if (x - cx) ** 2 + (y - cy) ** 2 < (lens_r * 0.92) ** 2:
            continue
        stars.append(star(x, y, rng.uniform(2.2, 6.8), rng.uniform(0, 9), rng.uniform(4.5, 9)))

    def label(x, y, text, anchor):
        return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="label">{text}</text>'

    labels = "".join([
        label(40, 52, "KOSEN26S", "start"),
        label(W - 40, 52, "NIT, AKASHI COLLEGE", "end"),
        label(40, H - 34, "AI / LLM RESEARCH", "start"),
        label(W - 40, H - 34, "PYTHON · RUST · C", "end"),
    ])

    # The source ends in hard cuts just outside the lens, so the fade must finish before them.
    fade_end = 1.12
    art = f'<image id="art" href="{icon_data_uri(1200, 1.8)}" x="{ax:.1f}" y="{ay:.1f}" width="{art_w:.1f}" height="{art_h:.1f}" preserveAspectRatio="none"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">TKY-27</title>
<desc id="d">TKY-27 (@ANAg2bGOD). KOSEN26S, National Institute of Technology, Akashi College. AI and LLM research. Python, Rust, C.</desc>
<defs>
<radialGradient id="fade" gradientUnits="userSpaceOnUse" cx="{cx:.1f}" cy="{cy:.1f}" r="{lens_r * fade_end:.1f}">
<stop offset="{0.9 / fade_end:.3f}" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
<radialGradient id="iris" gradientUnits="userSpaceOnUse" cx="{eye_x:.1f}" cy="{eye_y:.1f}" r="{eye_r * 1.25:.1f}">
<stop offset=".72" stop-color="#000"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<mask id="melt"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
<mask id="meltNoIris"><rect width="{W}" height="{H}" fill="url(#fade)"/><rect width="{W}" height="{H}" fill="url(#iris)"/></mask>
<clipPath id="type"><path transform="translate({title_x:.1f} {title_y})" d="{title_d}"/></clipPath>
<filter id="invert" color-interpolation-filters="sRGB"><feComponentTransfer><feFuncR type="table" tableValues="1 0"/><feFuncG type="table" tableValues="1 0"/><feFuncB type="table" tableValues="1 0"/></feComponentTransfer></filter>
<radialGradient id="glow"><stop offset="0" stop-color="#ff2020" stop-opacity=".7"/><stop offset=".4" stop-color="#ff2020" stop-opacity=".16"/><stop offset="1" stop-color="#ff2020" stop-opacity="0"/></radialGradient>
<radialGradient id="mistg"><stop offset="0" stop-color="{t['mist']}" stop-opacity="{t['mist_opacity']}"/><stop offset="1" stop-color="{t['mist']}" stop-opacity="0"/></radialGradient>
</defs>
<style>
.label{{font:500 18px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:.14em;fill:{t['label']}}}
.star{{fill:{t['ink']};opacity:{t['star_opacity'] * 0.5};transform-box:fill-box;transform-origin:center;animation:tw 6s ease-in-out infinite}}
.glow{{transform-box:fill-box;transform-origin:center;animation:pulse 5.2s ease-in-out var(--t0,0s) infinite}}
.mist{{animation:drift 26s ease-in-out var(--t0,0s) infinite}}
.m2{{animation-duration:34s;animation-direction:reverse}}
.orbit{{fill:none;stroke:{t['ink']};stroke-width:1.2;opacity:.28;stroke-dasharray:2 14;stroke-linecap:round;transform-origin:{cx:.1f}px {cy:.1f}px;animation:spin 180s linear var(--t0,0s) infinite}}
@keyframes tw{{0%,100%{{opacity:.06;transform:scale(.45)}}50%{{opacity:{t['star_opacity']};transform:scale(1)}}}}
@keyframes pulse{{0%,100%{{opacity:.5;transform:scale(.9)}}50%{{opacity:1;transform:scale(1.12)}}}}
@keyframes drift{{0%,100%{{transform:translate(-50px,0)}}50%{{transform:translate(50px,-14px)}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@media (prefers-reduced-motion:reduce){{.star,.glow,.mist,.orbit{{animation:none}}}}
</style>
<ellipse class="mist" cx="330" cy="650" rx="430" ry="150" fill="url(#mistg)"/>
<ellipse class="mist m2" cx="1280" cy="270" rx="450" ry="160" fill="url(#mistg)"/>
<circle class="orbit" cx="{cx:.1f}" cy="{cy:.1f}" r="{lens_r * 1.19:.1f}"/>
<path transform="translate({title_x:.1f} {title_y})" d="{title_d}" fill="{t['ink']}"/>
<g mask="url(#melt)">{art}</g>
<g clip-path="url(#type)"><g mask="url(#meltNoIris)"><use href="#art" filter="url(#invert)"/></g></g>
<circle class="glow" cx="{eye_x:.1f}" cy="{eye_y:.1f}" r="{eye_r * 3.4:.1f}" fill="url(#glow)"/>
{"".join(stars)}
<g transform="translate({(W - handle_w) / 2:.1f} {H - 28})">{handle}</g>
{labels}
</svg>
'''


if __name__ == "__main__":
    os.makedirs(sys.argv[1], exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(sys.argv[1], f"hero-{theme}.svg"), "w") as f:
            f.write(build(theme))
