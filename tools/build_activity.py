"""Build the two activity drawings, each in a light and a dark file.

assets/activity-*.svg  the last year of contributions as an iris: one spike per day round a red pupil.
assets/habits-*.svg    a 24-hour dial of commit times, and the languages of the public repositories as a constellation.

Standard library only and a single API request, because this also runs daily in
GitHub Actions where the fonts are absent: numerals come from tools/digits.json.

Token: $GITHUB_TOKEN, else `gh auth token`. Login: $GITHUB_LOGIN, else TKY-27.
"""

import collections
import datetime
import json
import math
import os
import subprocess
import sys
import urllib.request
import zlib

LOGIN = os.environ.get("GITHUB_LOGIN", "TKY-27")
LOCAL = datetime.timezone(datetime.timedelta(hours=9))  # JST, where the commits are made
THEMES = {
    "light": dict(ink="#15100f", label="#4a3f44"),
    "dark": dict(ink="#f1ebe6", label="#b9aab1"),
}
RED = "#e8232a"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
SPARK = "M0 -2.6Q0 0 1 0Q0 0 0 2.6Q0 0 -1 0Q0 0 0 -2.6Z"  # unit four-point star, scaled per use

# Everything comes from one request. Commit history is capped by the API at 100 per
# repository, so the dial is a sample of recent commits, and is captioned as one.
QUERY = """
query($login: String!, $since: GitTimestamp!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
    repositories(first: 40, privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
        defaultBranchRef { target { ... on Commit {
          history(first: 100, since: $since) { nodes { authoredDate author { user { login } } } }
        } } }
      }
    }
  }
}
"""

with open(os.path.join(os.path.dirname(__file__), "digits.json")) as f:
    DIGITS = json.load(f)


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or subprocess.run(
        ["gh", "auth", "token"], check=True, capture_output=True, text=True
    ).stdout.strip()
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN, "since": since}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    user = payload["data"]["user"]

    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in calendar["weeks"] for d in w["contributionDays"]]

    hours, sizes = [0] * 24, collections.Counter()
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
        history = ((repo["defaultBranchRef"] or {}).get("target") or {}).get("history") or {"nodes": []}
        for commit in history["nodes"]:
            # Bots and other contributors also commit to these repositories.
            if ((commit["author"] or {}).get("user") or {}).get("login") != LOGIN:
                continue
            stamp = datetime.datetime.strptime(commit["authoredDate"], "%Y-%m-%dT%H:%M:%SZ")
            hours[stamp.replace(tzinfo=datetime.timezone.utc).astimezone(LOCAL).hour] += 1
    whole = sum(sizes.values()) or 1
    languages = [(name, size / whole) for name, size in sizes.most_common()]
    return calendar["totalContributions"], days, hours, languages


def numeral(value, size):
    """Outlined digits at `size` px with the baseline at y=0. Returns (markup, width)."""
    text = value if isinstance(value, str) else f"{value:,}"
    scale, x, parts = size / 1000, 0.0, []
    for ch in text:
        d, advance = DIGITS[ch]
        parts.append(f'<path transform="translate({x:.1f} 0) scale({scale})" d="{d}"/>')
        x += advance * scale
    return "".join(parts), x


def polar(cx, cy, r, degrees):
    a = math.radians(degrees)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def document(width, height, title, summary, css, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t d">\n'
        f'<title id="t">{title}</title>\n<desc id="d">{summary}</desc>\n<style>\n{css}\n{REDUCED}\n</style>\n{body}\n</svg>\n'
    )


# --- the year as an iris -------------------------------------------------------------

IRIS_W, IRIS_H = 1600, 640
CX, CY, R0 = 390, 320, 130
GAP_DAYS = 12  # an opening at the top, between the oldest day and today
WAVE = 9  # seconds for the ripple to travel once round


def longest_streak(days):
    best = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        best = max(best, run)
    return best


def iris(days, t):
    peak = max(count for _, count in days)
    best_index = max(i for i, (_, count) in enumerate(days) if count == peak)
    step = 360 / (len(days) + GAP_DAYS)
    spikes, months = [], []
    for i, (date, count) in enumerate(days):
        angle = -90 + (GAP_DAYS / 2 + i + 0.5) * step
        if date.endswith("-01"):
            x, y = polar(CX, CY, R0 - 30, angle)
            name = datetime.date.fromisoformat(date).strftime("%b").upper()
            months.append(f'<text x="{x:.1f}" y="{y + 6:.1f}" text-anchor="middle" class="month">{name}</text>')
        if not count:
            spikes.append(f'<g transform="rotate({angle:.2f} {CX} {CY})"><circle cx="{CX + R0 + 4}" cy="{CY}" r="1.8" class="rest"/></g>')
            continue
        # Square root keeps quiet days visible beside the loudest one.
        length = 16 + 165 * math.sqrt(count / peak)
        fill = RED if i == best_index else t["ink"]
        wait = WAVE * (1 - i / len(days))
        spikes.append(
            f'<g transform="rotate({angle:.2f} {CX} {CY})"><path class="spike" fill="{fill}" '
            f'style="animation-delay:calc(var(--t0,0s) - {wait:.2f}s)" '
            f'd="M{CX + R0} {CY - 1.9}L{CX + R0 + length:.1f} {CY}L{CX + R0} {CY + 1.9}Z"/></g>'
        )
    return (
        f'<circle cx="{CX}" cy="{CY}" r="{R0 - 7}" fill="none" stroke="{t["ink"]}" stroke-width="1.2" opacity=".3"/>'
        + "".join(spikes) + "".join(months)
        + f'<circle class="pupil" cx="{CX}" cy="{CY}" r="37" fill="{RED}"/>'
        + f'<path transform="translate({CX - 9} {CY - 10}) scale(4 3.5)" d="{SPARK}" fill="#fff" opacity=".9"/>'
    )


def stat(x, y, label, value, unit, t):
    return (
        f'<text x="{x}" y="{y}" class="label">{label}</text>'
        f'<g transform="translate({x} {y + 96})" fill="{t["ink"]}">{numeral(value, 104)[0]}</g>'
        f'<text x="{x + 3}" y="{y + 132}" class="unit">{unit}</text>'
    )


def build_iris(total, days, t):
    peak_date, peak = max(reversed(days), key=lambda day: day[1])
    active = sum(1 for _, count in days if count)
    streak = longest_streak(days)
    summary = (
        f"{total:,} contributions in the last 12 months. Best day {peak} on {peak_date}. "
        f"Longest streak {streak} days. Active on {active} of {len(days)} days."
    )
    css = (
        f'.label{{font:500 20px {MONO};letter-spacing:.14em;fill:{t["label"]}}}\n'
        f'.unit{{font:500 18px {MONO};letter-spacing:.12em;fill:{t["label"]}}}\n'
        f'.month{{font:500 17px {MONO};letter-spacing:.06em;fill:{t["label"]}}}\n'
        f'.rest{{fill:{t["ink"]};opacity:.35}}\n'
        f".spike{{transform-box:fill-box;transform-origin:0 50%;animation:ripple {WAVE}s ease-in-out infinite}}\n"
        ".pupil{transform-box:fill-box;transform-origin:center;animation:dilate 6s ease-in-out var(--t0,0s) infinite}\n"
        "@keyframes ripple{0%,16%,100%{transform:scaleX(1)}8%{transform:scaleX(1.22)}}\n"
        "@keyframes dilate{0%,100%{transform:scale(.86)}50%{transform:scale(1.08)}}"
    )
    body = (
        iris(days, t)
        + stat(820, 144, "CONTRIBUTIONS", total, "LAST 12 MONTHS", t)
        + stat(820, 372, "BEST DAY", peak, peak_date, t)
        + stat(1230, 144, "LONGEST STREAK", streak, "DAYS", t)
        + stat(1230, 372, "ACTIVE DAYS", active, f"OF {len(days)}", t)
    )
    return document(IRIS_W, IRIS_H, "Activity", summary, css, body)


# --- the day as a dial, the languages as a constellation ------------------------------

HABITS_W, HABITS_H = 1600, 580
DIAL_X, DIAL_Y, DIAL_IN, DIAL_OUT = 390, 280, 84, 206
NAMED_SHARE, NAMED_MAX = 0.03, 6  # smaller languages stay in the sky, unnamed


def dial(hours, t):
    peak = max(hours) or 1
    peak_hour = max(range(24), key=lambda h: hours[h])
    parts = [f'<circle cx="{DIAL_X}" cy="{DIAL_Y}" r="{DIAL_OUT}" fill="none" stroke="{t["ink"]}" stroke-width="1.2" opacity=".3"/>']
    for h in range(24):
        # Midnight at the top, noon at the bottom, clockwise.
        a0, a1 = -90 + h * 15 + 1.5, -90 + (h + 1) * 15 - 1.5
        r = DIAL_IN + 6 + 100 * hours[h] / peak
        (x0, y0), (x1, y1) = polar(DIAL_X, DIAL_Y, DIAL_IN, a0), polar(DIAL_X, DIAL_Y, r, a0)
        (x2, y2), (x3, y3) = polar(DIAL_X, DIAL_Y, r, a1), polar(DIAL_X, DIAL_Y, DIAL_IN, a1)
        fill = RED if h == peak_hour else t["ink"]
        extra = "" if hours[h] else ' opacity=".3"'
        parts.append(
            f'<path{extra} fill="{fill}" d="M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}A{r:.1f} {r:.1f} 0 0 1 {x2:.1f} {y2:.1f}'
            f'L{x3:.1f} {y3:.1f}A{DIAL_IN} {DIAL_IN} 0 0 0 {x0:.1f} {y0:.1f}Z"/>'
        )
        tx, ty = polar(DIAL_X, DIAL_Y, DIAL_OUT, -90 + h * 15)
        ux, uy = polar(DIAL_X, DIAL_Y, DIAL_OUT + (9 if h % 6 == 0 else 5), -90 + h * 15)
        parts.append(f'<path d="M{tx:.1f} {ty:.1f}L{ux:.1f} {uy:.1f}" stroke="{t["ink"]}" stroke-width="1.2" opacity=".5"/>')
        if h % 6 == 0:
            lx, ly = polar(DIAL_X, DIAL_Y, DIAL_OUT + 32, -90 + h * 15)
            parts.append(f'<text x="{lx:.1f}" y="{ly + 6:.1f}" text-anchor="middle" class="month">{h:02d}</text>')
    digits, width = numeral(f"{peak_hour:02d}", 70)
    parts.append(f'<g transform="translate({DIAL_X - width / 2:.1f} {DIAL_Y + 10})" fill="{t["ink"]}">{digits}</g>')
    parts.append(f'<text x="{DIAL_X}" y="{DIAL_Y + 40}" text-anchor="middle" class="tiny">PEAK HOUR</text>')
    # A bead runs the rim once a loop, the way an hour hand would over a day.
    parts.append(f'<g class="hand"><circle cx="{DIAL_X}" cy="{DIAL_Y - DIAL_OUT}" r="5" fill="{t["ink"]}"/></g>')
    return "".join(parts), peak_hour


def constellation(languages, t):
    named = [(name, share) for name, share in languages if share >= NAMED_SHARE][:NAMED_MAX]
    unnamed = [(name, share) for name, share in languages if (name, share) not in named]
    top = named[0][1]
    left, right = 900, 1470
    heights = [150, 285, 165, 300, 155, 290]
    points, stars, labels = [], [], []
    for i, (name, share) in enumerate(named):
        x = left + (right - left) * (i / (len(named) - 1) if len(named) > 1 else 0.5)
        y = heights[i]
        r = 7 + 25 * math.sqrt(share / top)
        points.append((x, y))
        # The red lead star holds steady: faded red reads as pink on a white page.
        stars.append(
            f'<g transform="translate({x:.1f} {y})"><path class="{"lead" if i == 0 else "star"}" fill="{RED if i == 0 else t["ink"]}" '
            f'style="animation-delay:calc(var(--t0,0s) - {i * 1.3:.1f}s)" transform="scale({r:.1f})" d="{SPARK}"/></g>'
        )
        base = y + 2.6 * r + 36
        digits, width = numeral(str(round(share * 100)), 56)
        labels.append(
            f'<text x="{x:.1f}" y="{base:.1f}" text-anchor="middle" class="label">{name.upper()}</text>'
            f'<g transform="translate({x - width / 2 - 8:.1f} {base + 58:.1f})" fill="{t["ink"]}">{digits}</g>'
            f'<text x="{x + width / 2 - 2:.1f}" y="{base + 58:.1f}" class="unit">%</text>'
        )
    sky = []
    for name, share in unnamed:
        # Placed by a checksum of the name, so a language keeps its place from day to day.
        seed = zlib.crc32(name.encode())
        x, y = 830 + seed % 700, 56 + (seed >> 12) % 60
        r = 2.2 + 14 * math.sqrt(share)
        sky.append(
            f'<g transform="translate({x} {y})"><path class="star" fill="{t["ink"]}" opacity=".7" '
            f'style="animation-delay:calc(var(--t0,0s) - {seed % 50 / 10}s)" transform="scale({r:.1f})" d="{SPARK}"/></g>'
        )
    line = "M" + "L".join(f"{x:.1f} {y}" for x, y in points)
    thread = (
        f'<path d="{line}" fill="none" stroke="{t["ink"]}" stroke-width="1.3" stroke-dasharray="2 9" stroke-linecap="round" opacity=".45"/>'
        f'<path class="bead" d="{line}" pathLength="100" fill="none" stroke="{t["ink"]}" stroke-width="4" '
        'stroke-dasharray="1.5 200" stroke-linecap="round"/>'
    )
    return thread + "".join(sky) + "".join(stars) + "".join(labels), named


def build_habits(hours, languages, t):
    dial_art, peak_hour = dial(hours, t)
    sky_art, named = constellation(languages, t)
    commits = sum(hours)
    summary = (
        f"Of {commits} recent commits, most were made around {peak_hour:02d}:00 JST. Languages by code size in public repositories: "
        + ", ".join(f"{name} {round(share * 100)}%" for name, share in named) + "."
    )
    css = (
        f'.label{{font:500 20px {MONO};letter-spacing:.14em;fill:{t["label"]}}}\n'
        f'.unit{{font:500 18px {MONO};letter-spacing:.12em;fill:{t["label"]}}}\n'
        f'.month{{font:500 17px {MONO};letter-spacing:.06em;fill:{t["label"]}}}\n'
        f'.tiny{{font:500 13px {MONO};letter-spacing:.16em;fill:{t["label"]}}}\n'
        ".star{transform-box:fill-box;transform-origin:center;animation:twinkle 6.5s ease-in-out infinite}\n"
        f".hand{{transform-origin:{DIAL_X}px {DIAL_Y}px;animation:sweep 24s linear var(--t0,0s) infinite}}\n"
        ".bead{stroke-dashoffset:0;animation:thread 8s cubic-bezier(.6,0,.3,1) var(--t0,0s) infinite}\n"
        "@keyframes twinkle{0%,100%{opacity:.6}50%{opacity:1}}\n"
        "@keyframes sweep{to{transform:rotate(360deg)}}\n"
        "@keyframes thread{0%{stroke-dashoffset:0}80%,100%{stroke-dashoffset:-100}}"
    )
    captions = (
        f'<text x="{DIAL_X}" y="{HABITS_H - 26}" text-anchor="middle" class="unit">COMMITS BY HOUR · JST · {commits} RECENT COMMITS</text>'
        f'<text x="1185" y="{HABITS_H - 26}" text-anchor="middle" class="unit">LANGUAGES BY CODE SIZE · PUBLIC REPOSITORIES</text>'
    )
    return document(HABITS_W, HABITS_H, "Habits", summary, css, dial_art + sky_art + captions)


if __name__ == "__main__":
    out = sys.argv[1]
    total, days, hours, languages = fetch()
    for theme, t in THEMES.items():
        with open(os.path.join(out, f"activity-{theme}.svg"), "w") as f:
            f.write(build_iris(total, days, t))
        with open(os.path.join(out, f"habits-{theme}.svg"), "w") as f:
            f.write(build_habits(hours, languages, t))
