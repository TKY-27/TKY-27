"""Build assets/icons/scan.svg: a scannable code for the X profile, with red-pupilled finder eyes.

The tile carries its own light background, so one file serves both themes.
"""

import sys

import segno

URL = "https://x.com/ANAg2bGOD"
PAPER, INK, RED = "#f1ebe6", "#15100f", "#e8232a"
QUIET = 4  # modules of margin the QR specification asks for


def build():
    matrix = [list(row) for row in segno.make(URL, error="m", boost_error=False).matrix]
    n = len(matrix)
    side = n + 2 * QUIET
    finders = [(0, 0), (n - 7, 0), (0, n - 7)]

    def in_finder(x, y):
        return any(fx <= x < fx + 7 and fy <= y < fy + 7 for fx, fy in finders)

    cells = "".join(
        f"M{x + QUIET + 0.05:.2f} {y + QUIET + 0.05:.2f}h.9v.9h-.9z"
        for y in range(n) for x in range(n)
        if matrix[y][x] and not in_finder(x, y)
    )
    # The finder ring must stay square: rounding it by even 0.8 of a module stopped OpenCV's
    # detector at every size tried, while a red or fully round pupil decodes down to 104 px.
    eyes = "".join(
        f'<rect x="{fx + QUIET + 0.5}" y="{fy + QUIET + 0.5}" width="6" height="6" fill="none" stroke="{INK}"/>'
        f'<circle cx="{fx + QUIET + 3.5}" cy="{fy + QUIET + 3.5}" r="1.5" fill="{RED}"/>'
        for fx, fy in finders
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" role="img" aria-label="QR code for {URL}">'
        f"<title>QR code for {URL}</title>"
        f'<rect width="{side}" height="{side}" rx="3" fill="{PAPER}"/>'
        f'<path d="{cells}" fill="{INK}"/>{eyes}</svg>\n'
    )


if __name__ == "__main__":
    with open(sys.argv[1], "w") as f:
        f.write(build())
