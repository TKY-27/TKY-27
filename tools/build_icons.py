"""Build the looping logo marks in assets/icons/, one light and one dark file each.

Every mark is drawn here, not fetched, in one vocabulary taken from the icon art:
a solid ink shape, a hollow outlined shape, and a single red point.

With animations off (reduced motion) each mark rests in its recognisable pose.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from glyphs import SPIKES, outline  # noqa: E402

INK = {"light": "#15100f", "dark": "#f1ebe6"}
RED = "#e8232a"
HAIR = 2.3


def delay(seconds=0.0):
    return f"calc(var(--t0,0s) - {seconds}s)"


def spark(x, y, r, period, offset, color):
    d = f"M0 {-2.6*r:.2f}Q0 0 {r:.2f} 0Q0 0 0 {2.6*r:.2f}Q0 0 {-r:.2f} 0Q0 0 0 {-2.6*r:.2f}Z"
    return (
        f'<g transform="translate({x} {y})"><path class="spark" fill="{color}" d="{d}" '
        f'style="animation:spark {period}s ease-in-out {delay(offset)} infinite"/></g>'
    )


SPARK_CSS = (
    ".spark{transform-box:fill-box;transform-origin:center}"
    "@keyframes spark{0%,100%{opacity:.1;transform:scale(.4)}50%{opacity:1;transform:scale(1)}}"
)


def svg(title, body, css, ink, label=None):
    # The label is live text in the viewer's monospace, like the corner labels of the hero.
    height, caption = 160, ""
    if label:
        height = 192
        caption = (
            f'<text x="80" y="182" text-anchor="middle" fill="{ink}" opacity=".72" '
            f'style="font:500 13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:.16em">{label}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 {height}" role="img" aria-label="{title}">'
        f"<title>{title}</title><style>{css}{SPARK_CSS}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        f"</style>{body}{caption}</svg>\n"
    )


def python(ink):
    # One closed circuit. Each snake is a dash on it, so crawling is a dash offset.
    # Segment lengths: pose 128, crossing 170, pose 128, crossing 170.
    track = "M14 66V40H63V14H36H12V-12H86V34V60H37V86H64H88V112H14Z"
    pose, total = 128, 596
    half = total // 2
    stroke = f'd="{track}" pathLength="{total}" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    body = f'stroke-dasharray="{pose} {total - pose}"'
    eye = f'stroke-dasharray="0.01 {total - 0.01}" stroke="{RED}" stroke-width="5.6"'
    # The eye rides seven units behind the head end of its snake.
    eye_a, eye_b = -(pose - 7), -(half + pose - 7)
    css = (
        f".a{{stroke-dashoffset:0;animation:crawl-a 9s cubic-bezier(.7,0,.3,1) {delay()} infinite}}"
        f".b{{stroke-dashoffset:{-half};animation:crawl-b 9s cubic-bezier(.7,0,.3,1) {delay()} infinite}}"
        f".ea{{stroke-dashoffset:{eye_a};animation:eye-a 9s cubic-bezier(.7,0,.3,1) {delay()} infinite}}"
        f".eb{{stroke-dashoffset:{eye_b};animation:eye-b 9s cubic-bezier(.7,0,.3,1) {delay()} infinite}}"
        f"@keyframes crawl-a{{0%,30%{{stroke-dashoffset:0}}50%,80%{{stroke-dashoffset:{-half}}}100%{{stroke-dashoffset:{-total}}}}}"
        f"@keyframes crawl-b{{0%,30%{{stroke-dashoffset:{-half}}}50%,80%{{stroke-dashoffset:{-total}}}100%{{stroke-dashoffset:{-total - half}}}}}"
        f"@keyframes eye-a{{0%,30%{{stroke-dashoffset:{eye_a}}}50%,80%{{stroke-dashoffset:{eye_a - half}}}100%{{stroke-dashoffset:{eye_a - total}}}}}"
        f"@keyframes eye-b{{0%,30%{{stroke-dashoffset:{eye_b}}}50%,80%{{stroke-dashoffset:{eye_b - half}}}100%{{stroke-dashoffset:{eye_b - total}}}}}"
    )
    art = (
        '<defs><mask id="hollow" maskUnits="userSpaceOnUse" x="-10" y="-34" width="120" height="168">'
        f'<path class="b" {stroke} {body} stroke="#fff" stroke-width="20"/>'
        f'<path class="b" {stroke} {body} stroke="#000" stroke-width="{20 - 2 * HAIR / 0.8:.2f}"/></mask></defs>'
        '<g transform="translate(80 80) scale(.8) translate(-50 -50)">'
        f'<path d="{track}" fill="none" stroke="{ink}" stroke-width="1" stroke-dasharray="1 5" stroke-linecap="round" opacity=".2"/>'
        f'<path class="a" {stroke} {body} stroke="{ink}" stroke-width="20"/>'
        f'<rect x="-10" y="-34" width="120" height="168" fill="{ink}" mask="url(#hollow)"/>'
        f'<path class="ea" {stroke} {eye}/><path class="eb" {stroke} {eye}/>'
        "</g>"
    )
    return svg("Python", art + spark(140, 78, 3, 5, 1.2, ink) + spark(20, 82, 2.4, 6.5, 4, ink), css, ink, "PYTHON")


def gear(cx, cy, teeth, root, tip, phase_deg):
    pitch = 2 * math.pi / teeth
    pts = []
    for k in range(teeth):
        c = math.radians(phase_deg) + k * pitch
        for frac, r in ((-0.27, root), (-0.14, tip), (0.14, tip), (0.27, root)):
            a = c + frac * pitch
            pts.append(f"{cx + r * math.cos(a):.2f} {cy + r * math.sin(a):.2f}")
    return "M" + "L".join(pts) + "Z"


def ring(cx, cy, r):
    return f"M{cx - r} {cy}a{r} {r} 0 1 0 {2 * r} 0a{r} {r} 0 1 0 {-2 * r} 0Z"


def rust(ink):
    # 16 teeth drive 8, so pitch radii are 2:1 and the centres sit 54.75 apart on a 45 degree line.
    bx, by = 68.0, 92.0
    off = 54.75 / math.sqrt(2)
    sx, sy = bx + off, by - off
    letter, lw, _ = outline(SPIKES, "R", 46)
    css = (
        ".big,.small,.axle{transform-box:fill-box;transform-origin:center}"
        f".big{{animation:tick-big 1.8s cubic-bezier(.3,1.6,.5,1) {delay()} infinite}}"
        f".small{{animation:tick-small 1.8s cubic-bezier(.3,1.6,.5,1) {delay()} infinite}}"
        f".axle{{animation:beat 1.8s ease-out {delay()} infinite}}"
        "@keyframes tick-big{0%,62%{transform:rotate(0)}100%{transform:rotate(22.5deg)}}"
        "@keyframes tick-small{0%,62%{transform:rotate(0)}100%{transform:rotate(-45deg)}}"
        "@keyframes beat{0%,62%{transform:scale(1)}78%{transform:scale(1.7)}100%{transform:scale(1)}}"
    )
    art = (
        f'<path class="big" fill="{ink}" fill-rule="evenodd" d="{gear(bx, by, 16, 33, 40, 0)}{ring(bx, by, 25)}"/>'
        f'<path transform="translate({bx - lw / 2:.2f} {by + 16.1})" fill="{ink}" d="{letter}"/>'
        f'<path class="small" fill="none" stroke="{ink}" stroke-width="{HAIR}" stroke-linejoin="round" '
        f'd="{gear(sx, sy, 8, 14.75, 21.75, 22.5)}{ring(sx, sy, 8.5)}"/>'
        f'<circle class="axle" cx="{sx:.2f}" cy="{sy:.2f}" r="3.6" fill="{RED}"/>'
    )
    return svg("Rust", art + spark(24, 40, 3, 5.4, 0.6, ink) + spark(136, 116, 2.4, 6.3, 3.3, ink), css, ink, "RUST")


def hexagon(ink):
    cx, cy, r = 80, 80, 50
    v = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 270, 60)]
    # Read as a cube lit from one side, the faces are pairs of these six wedges.
    rest = [0, 0.19, 0.19, 0.08, 0.08, 0]
    wedges = "".join(
        f'<path class="wedge" fill="{ink}" opacity="{rest[i]}" '
        f'd="M{cx} {cy}L{v[i][0]:.2f} {v[i][1]:.2f}L{v[(i + 1) % 6][0]:.2f} {v[(i + 1) % 6][1]:.2f}Z" '
        f'style="animation:shade 12s linear {delay(i * 2)} infinite"/>'
        for i in range(6)
    )
    edge = "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in v) + "Z"
    css = (
        "@keyframes shade{0%{opacity:0}16.67%{opacity:.19}33.33%{opacity:.19}"
        "50%{opacity:.08}66.67%{opacity:.08}83.33%{opacity:0}100%{opacity:0}}"
    )
    art = wedges + f'<path d="{edge}" fill="none" stroke="{ink}" stroke-width="{HAIR}" stroke-linejoin="round"/>'
    return art, css


def c(ink):
    hexa, css = hexagon(ink)
    # The letter is a drawn arc open 80 degrees on the right: the Spikes C carries a middle spike and reads as an E.
    r = 20
    dx, dy = r * math.cos(math.radians(40)), r * math.sin(math.radians(40))
    letter = (
        f'<path d="M{80 + dx:.2f} {80 - dy:.2f}A{r} {r} 0 1 0 {80 + dx:.2f} {80 + dy:.2f}" fill="none" '
        f'stroke="{ink}" stroke-width="11"/>'
    )
    css += (
        ".pupil{transform-box:fill-box;transform-origin:center;"
        f"animation:look 8s cubic-bezier(.6,0,.2,1) {delay()} infinite}}"
        "@keyframes look{0%,16%{transform:translate(0,0)}22%,38%{transform:translate(7px,-4px)}"
        "44%,58%{transform:translate(7px,4px)}64%,80%{transform:translate(0,0)}"
        "84%{transform:scale(1,.1)}88%,100%{transform:translate(0,0)}}"
    )
    art = hexa + letter + f'<circle class="pupil" cx="80" cy="80" r="4.4" fill="{RED}"/>'
    return svg("C", art + spark(140, 34, 3, 5.8, 2.1, ink) + spark(18, 124, 2.4, 6.6, 0.4, ink), css, ink, "C")


def x(ink):
    bar = "M36 36H60L124 124H100Z"
    thread = "M121 36L39 124"
    css = (
        f".thread{{stroke-dashoffset:0;animation:pass 6s cubic-bezier(.65,0,.35,1) {delay()} infinite}}"
        f".bead{{stroke-dashoffset:-8;animation:march 7s linear {delay()} infinite}}"
        f".eye{{transform-box:fill-box;transform-origin:center;animation:wink 6s ease-in-out {delay()} infinite}}"
        "@keyframes pass{0%,58%{stroke-dashoffset:0}100%{stroke-dashoffset:-130}}"
        "@keyframes march{from{stroke-dashoffset:-8}to{stroke-dashoffset:-108}}"
        "@keyframes wink{0%,62%{transform:scale(1)}76%{transform:scale(1,.08)}86%{transform:scale(1.6)}100%{transform:scale(1)}}"
    )
    art = (
        '<defs><mask id="behind" maskUnits="userSpaceOnUse" x="0" y="0" width="160" height="160">'
        f'<rect width="160" height="160" fill="#fff"/><path d="{bar}" fill="#000" stroke="#000" stroke-width="7" stroke-linejoin="round"/>'
        "</mask></defs>"
        f'<g mask="url(#behind)"><path class="thread" d="{thread}" pathLength="100" stroke-dasharray="100 30" fill="none" '
        f'stroke="{ink}" stroke-width="5.4" stroke-linecap="round"/></g>'
        f'<path d="{bar}" fill="none" stroke="{ink}" stroke-width="{HAIR}" stroke-linejoin="round"/>'
        f'<path class="bead" d="{bar}" pathLength="100" stroke-dasharray="5 95" fill="none" stroke="{ink}" '
        f'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle class="eye" cx="80" cy="80" r="4.2" fill="{RED}"/>'
    )
    return svg("X", art + spark(134, 62, 3, 5.6, 0.9, ink) + spark(26, 96, 2.4, 6.2, 3.6, ink), css, ink)


MARKS = {"python": python, "rust": rust, "c": c, "x": x}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, draw in MARKS.items():
        for theme, ink in INK.items():
            with open(os.path.join(out, f"{name}-{theme}.svg"), "w") as f:
                f.write(draw(ink))
