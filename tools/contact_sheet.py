"""Freeze an animated SVG at evenly spaced moments and screenshot them side by side.

usage: contact_sheet.py <svg> <seconds> <frames> <background> <cell_px> <out.png>

Works because every animation delay in these SVGs is offset by the --t0 variable.
"""

import os
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main(svg_path, seconds, frames, background, cell, out):
    seconds, frames, cell = float(seconds), int(frames), int(cell)
    with open(svg_path) as f:
        source = f.read()
    cols = min(frames, 6)
    rows = -(-frames // cols)
    with tempfile.TemporaryDirectory() as tmp:
        cells = []
        for i in range(frames):
            t = seconds * i / frames
            freeze = f"<style>:root{{--t0:-{t:.3f}s}}*{{animation-play-state:paused!important}}</style></svg>"
            frame = os.path.join(tmp, f"{i}.svg")
            with open(frame, "w") as f:
                f.write(source.replace("</svg>", freeze))
            cells.append(
                f'<figure><img src="file://{frame}" width="{cell}"><figcaption>{t:.2f}s</figcaption></figure>'
            )
        page = os.path.join(tmp, "sheet.html")
        with open(page, "w") as f:
            f.write(
                f'<body style="margin:0;background:{background};display:grid;grid-template-columns:repeat({cols},{cell}px)">'
                "<style>figure{margin:0;position:relative}img{display:block}"
                "figcaption{position:absolute;left:4px;top:2px;font:11px monospace;color:#888}</style>"
                + "".join(cells)
            )
        with open(svg_path) as f:
            head = f.read(400)
        vb = head.split('viewBox="')[1].split('"')[0].split()
        height = round(cell * float(vb[3]) / float(vb[2])) * rows
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
             f"--window-size={cell * cols},{height}", f"--screenshot={out}", f"file://{page}"],
            check=True, capture_output=True,
        )


if __name__ == "__main__":
    main(*sys.argv[1:])
