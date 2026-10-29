#!/usr/bin/env python3
"""Builds the animated SVGs used by the profile README.

    python assets/make_svgs.py

Writes assets/terminal.svg (the header), assets/room.svg (the cat's room)
and assets/divider.svg (paw prints). Everything a visitor reads is in the
SESSION and ROOM TEXT sections below, so that is where to make edits.

The robot cat is the same one that lives on mishkat2025.github.io: its
geometry is ported from cat.js there, so the two always match.
GitHub plays SVG animations (SMIL and CSS) but not scripts or web fonts,
so text uses the viewer's monospace font and every animation is SMIL/CSS.
"""
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent

# Portfolio palette.
ACCENT = "#00ff88"
BG = "#0c0d0e"
CAT_FILL = "#0b2018"          # page background tinted 8% with the accent, as on the site
TEXT = "#d4d4d8"
MUTED = "#8b8b94"
DIM = "#5b5b63"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def n(v):
    """Compact number for SVG attributes."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def esc(s):
    return escape(s, {'"': "&quot;"})


# ---------------------------------------------------------------------------
# Small SMIL helpers. Every looping scene shares one cycle length, so all the
# timelines line up.

def discrete(attr, changes, total, initial, extra=""):
    """A looping attribute that jumps between values at given times.
    changes: [(time_s, value), ...] in order; initial applies from t=0."""
    times, values = [0.0], [initial]
    for t, v in changes:
        if t <= 0:
            values[0] = v
            continue
        times.append(t / total)
        values.append(v)
    return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{n(total)}s" '
            f'repeatCount="indefinite" keyTimes="{";".join(n(k) if k else "0" for k in times)}" '
            f'values="{";".join(str(v) for v in values)}"{extra}/>')


def frames_cycle(count, index, period):
    """Show frame `index` of `count` in turn, forever."""
    vals = ";".join("1" if j == index else "0" for j in range(count))
    keys = ";".join(n(j / count) for j in range(count))
    return (f'<animate attributeName="opacity" calcMode="discrete" dur="{n(period)}s" '
            f'repeatCount="indefinite" keyTimes="{keys}" values="{vals}"/>')


def glow_filter(fid, blur=2.2, strength=1):
    merges = "".join('<feMergeNode in="b"/>' for _ in range(strength))
    return (f'<filter id="{fid}" x="-40%" y="-40%" width="180%" height="180%">'
            f'<feGaussianBlur stdDeviation="{n(blur)}" result="b"/>'
            f'<feMerge>{merges}<feMergeNode in="SourceGraphic"/></feMerge></filter>')


# ---------------------------------------------------------------------------
# The robot cat, ported from cat.js on the portfolio. Local coordinates:
# facing right, the ground point under the middle of the body at (0, 0).

def mix(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def add(a, x, y):
    return (a[0] + x, a[1] + y)


def bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def solid(sw):
    return f'fill="{CAT_FILL}" stroke="{ACCENT}" stroke-width="{n(sw)}"'


def joint(p, r):
    return (f'<circle cx="{n(p[0])}" cy="{n(p[1])}" r="{n(r)}" {solid(1.4)}/>'
            f'<circle cx="{n(p[0])}" cy="{n(p[1])}" r="{n(r * .35)}" fill="{ACCENT}"/>')


def leg(top, foot, knee, alpha):
    m = mix(top, foot, .5)
    k = (m[0] + knee, m[1])
    op = f' opacity="{n(alpha)}"' if alpha < 1 else ""
    return (f'<g{op}><polyline points="{n(top[0])},{n(top[1])} {n(k[0])},{n(k[1])} {n(foot[0])},{n(foot[1])}" '
            f'fill="none" stroke="{ACCENT}" stroke-width="2.4"/>{joint(k, 1.9)}'
            f'<rect x="{n(foot[0] - 2)}" y="{n(foot[1] - 2.2)}" width="6" height="2.6" rx="1.2" {solid(1.3)}/></g>')


def cat(sit=0.0, lie=0.0, walk=0.0, phase=0.0, tail=0.0, closed=0.0, happy=0.0,
        lx=.6, ly=.1, stride=7.0, lift=3.0, battery=False):
    """One frame of the cat as SVG markup. Returns (markup, head_point)."""
    bob = math.sin(phase * 2) * 1.2 * walk
    hip = mix(mix((-20, -21), (-12, -11), sit), (-18, -8), lie)
    sh = mix(mix((12, -23), (3, -35), sit), (12, -9), lie)
    hip = (hip[0], hip[1] + bob)
    sh = (sh[0], sh[1] + bob * .6)
    head = mix(mix(add(sh, 11, -11), add(sh, 7, -14), sit), add(sh, 13, -1), lie)

    axis = math.atan2(sh[1] - hip[1], sh[0] - hip[0])
    length = math.hypot(sh[0] - hip[0], sh[1] - hip[1])
    mid = mix(hip, sh, .5)
    bw = length + 14
    bh = 18 + (19 - 18) * sit
    rear = (mid[0] - math.cos(axis) * (bw / 2 - 3), mid[1] - math.sin(axis) * (bw / 2 - 3))

    swing = stride * walk * (1 - sit)
    lft = lift * walk * (1 - sit)

    def foot(x, ph):
        return (x + math.sin(ph) * swing, -max(0, math.cos(ph)) * lft)

    legs = {
        "frontFar": [add(sh, 3, 5), foot(sh[0] + 4 + 3 * sit, phase + math.pi)],
        "backFar": [add(hip, 3 + 2 * sit, 5), foot(hip[0] + 1 + 15 * sit, phase)],
        "backNear": [add(hip, 5 * sit, 6), foot(hip[0] - 2 + 15 * sit, phase + math.pi)],
        "frontNear": [add(sh, 0, 6), foot(sh[0] + 1 + 2 * sit, phase)],
    }
    for L in legs.values():
        L[1] = mix(L[1], add(L[0], 5, 2), lie)

    back_knee = -4 * (1 - sit) - 1
    front_knee = 1.5 * (1 - sit)
    o = []
    o.append(leg(*legs["frontFar"], front_knee, .5))
    o.append(leg(*legs["backFar"], back_knee, .5))

    # Segmented tail.
    sway = math.sin(tail)
    curl = max(sit, lie)
    c1 = mix(add(rear, -12, -2), (rear[0] - 12, -1), curl)
    c2 = mix(add(rear, -17 + sway * 2, -16), (rear[0] - 4, 2.5), curl)
    end = mix(add(rear, -11 + sway * 6, -27), (rear[0] + 16 + sway * 2, -1.5), curl)
    pts = [bezier(rear, c1, c2, end, i / 6) for i in range(7)]
    o.append(f'<polyline points="{" ".join(f"{n(x)},{n(y)}" for x, y in pts)}" fill="none" '
             f'stroke="{ACCENT}" stroke-width="1.4" opacity=".7"/>')
    for i in range(1, 6):
        sz = 2.8 - i * .25
        o.append(f'<rect x="{n(pts[i][0] - sz)}" y="{n(pts[i][1] - sz)}" width="{n(sz * 2)}" '
                 f'height="{n(sz * 2)}" rx="1" {solid(1.2)}/>')
    o.append(f'<circle class="pulse" cx="{n(pts[6][0])}" cy="{n(pts[6][1])}" r="2.2" fill="{ACCENT}"/>')

    # Chassis.
    o.append(f'<g transform="translate({n(mid[0])} {n(mid[1])}) rotate({n(math.degrees(axis))})">'
             f'<rect x="{n(-bw / 2)}" y="{n(-bh / 2)}" width="{n(bw)}" height="{n(bh)}" rx="6" {solid(2)}/>')
    seam = -bw / 2 + bw * .38
    o.append(f'<g opacity=".55" stroke="{ACCENT}" stroke-width="1">'
             f'<line x1="{n(seam)}" y1="{n(-bh / 2 + 2)}" x2="{n(seam)}" y2="{n(bh / 2 - 2)}"/>')
    for i in range(3):
        x = -bw / 2 + 5 + i * 3
        o.append(f'<line x1="{n(x)}" y1="-3" x2="{n(x)}" y2="3"/>')
    o.append(f'<circle cx="{n(seam + 4)}" cy="{n(-bh / 2 + 3)}" r=".9" fill="{ACCENT}" stroke="none"/>'
             f'<circle cx="{n(bw / 2 - 5)}" cy="{n(-bh / 2 + 3)}" r=".9" fill="{ACCENT}" stroke="none"/></g>')
    o.append(f'<line class="pulse-slow" x1="{n(bw * .05)}" y1="2.5" x2="{n(bw * .3)}" y2="2.5" '
             f'stroke="{ACCENT}" stroke-width="1.6"/></g>')

    if sit > .05:
        o.append(f'<g opacity="{n(sit)}">{joint((hip[0] + 2, hip[1] + 1), 7.5)}</g>')

    o.append(leg(*legs["backNear"], back_knee, 1))
    o.append(leg(*legs["frontNear"], front_knee, 1))
    o.append(joint((sh[0], sh[1] + 5), 2.6))
    o.append(joint(mix(sh, head, .5), 3.2))

    # Head.
    h = [f'<g transform="translate({n(head[0])} {n(head[1])})">']
    h.append(f'<line x1="3" y1="-9.5" x2="5" y2="-18" stroke="{ACCENT}" stroke-width="1.4"/>')
    tip_cls = "" if closed > .9 else ' class="pulse-fast"'
    tip_op = ' opacity=".35"' if closed > .9 else ""
    h.append(f'<circle{tip_cls}{tip_op} cx="5" cy="-19.5" r="1.8" fill="{ACCENT}"/>')
    for s in (-1, 1):
        h.append(f'<polygon points="{n(s * 11)},-5 {n(s * 10)},-17 {n(s * 3.5)},-9.5" {solid(1.8)}/>'
                 f'<line x1="{n(s * 8.6)}" y1="-8" x2="{n(s * 8.3)}" y2="-13" stroke="{ACCENT}" '
                 f'stroke-width="1" opacity=".5"/>')
    h.append(f'<rect x="-12" y="-10" width="24" height="19" rx="6" {solid(2)}/>')
    fx, fy = lx * 2.4, ly * 1.6
    vx, vy = fx * .5, fy * .5
    h.append(f'<rect x="{n(-8.5 + vx)}" y="{n(-5.5 + vy)}" width="17" height="9" rx="3" fill="{BG}" '
             f'stroke="{ACCENT}" stroke-opacity=".7" stroke-width="1.2"/>')
    for s in (-1, 1):
        ex, ey = s * 3.8 + fx * .9, -1 + fy
        if happy > .5:
            h.append(f'<polyline points="{n(ex - 2)},{n(ey + 1)} {n(ex)},{n(ey - 1.2)} {n(ex + 2)},{n(ey + 1)}" '
                     f'fill="none" stroke="{ACCENT}" stroke-width="1.4"/>')
        elif closed > .8:
            h.append(f'<line x1="{n(ex - 2)}" y1="{n(ey)}" x2="{n(ex + 2)}" y2="{n(ey)}" '
                     f'stroke="{ACCENT}" stroke-width="1.4"/>')
        else:
            eh = 4.4 * (1 - closed * .85)
            h.append(f'<rect x="{n(ex - 1.2)}" y="{n(ey - eh / 2)}" width="2.4" height="{n(eh)}" rx="1" fill="{ACCENT}"/>')
    h.append(f'<circle cx="-10" cy="5" r=".9" fill="{ACCENT}"/><circle cx="10" cy="5" r=".9" fill="{ACCENT}"/>')
    mx = vx
    h.append(f'<path d="M{n(mx)} 5.8A1.1 1.1 0 0 1 {n(mx - 2.2)} 5.8M{n(mx + 2.2)} 5.8A1.1 1.1 0 0 1 {n(mx)} 5.8" '
             f'fill="none" stroke="{ACCENT}" stroke-width="1"/>')
    h.append(f'<g opacity=".5" stroke="{ACCENT}" stroke-width=".8">')
    for s in (-1, 1):
        h.append(f'<line x1="{s * 12}" y1="3" x2="{s * 18}" y2="1.5"/><line x1="{s * 12}" y1="4.5" x2="{s * 18}" y2="6"/>')
    h.append('</g>')
    if battery:
        h.append(f'<rect x="-6" y="-31" width="12" height="6" rx="1.2" fill="none" stroke="{ACCENT}" stroke-width="1.2"/>'
                 f'<circle cx="7" cy="-28" r="1" fill="{ACCENT}"/>'
                 f'<rect x="-4.5" y="-29.5" width="0" height="3" fill="{ACCENT}">'
                 f'<animate attributeName="width" values="0;9" dur="2.8s" repeatCount="indefinite"/></rect>')
    h.append('</g>')
    o.extend(h)
    eyes = [(s * 3.8 + fx * .9 + head[0], -1 + fy + head[1]) for s in (-1, 1)]
    return "".join(o), head, eyes


def blink_overlay(eyes, every=3.4, start=1.2):
    """Covers the eyes with closed lids for a moment, every few seconds."""
    lids = "".join(
        f'<rect x="{n(x - 2.4)}" y="{n(y - 2.8)}" width="4.8" height="5.6" fill="{BG}"/>'
        f'<line x1="{n(x - 2)}" y1="{n(y)}" x2="{n(x + 2)}" y2="{n(y)}" stroke="{ACCENT}" stroke-width="1.4"/>'
        for x, y in eyes)
    k0, k1 = start / every, (start + .14) / every
    return (f'<g opacity="0">{lids}<animate attributeName="opacity" calcMode="discrete" dur="{n(every)}s" '
            f'repeatCount="indefinite" keyTimes="0;{n(k0)};{n(k1)}" values="0;1;0"/></g>')


def sitting_cat(frames=8, period=1.6, lx=.6, ly=.1):
    """A sitting cat whose tail sways, with a blink now and then."""
    parts = []
    eyes = None
    for i in range(frames):
        body, _, eyes = cat(sit=1, tail=2 * math.pi * i / frames, lx=lx, ly=ly)
        parts.append(f'<g opacity="{1 if i == 0 else 0}">{frames_cycle(frames, i, period)}{body}</g>')
    parts.append(blink_overlay(eyes))
    return "".join(parts)


def running_cat(frames=8, period=.42):
    parts = []
    for i in range(frames):
        ph = 2 * math.pi * i / frames
        body, _, _ = cat(walk=1, phase=ph, tail=ph, stride=10, lift=5, lx=1, ly=0)
        parts.append(f'<g opacity="{1 if i == 0 else 0}">{frames_cycle(frames, i, period)}{body}</g>')
    return "".join(parts)


CAT_STYLE = """
.pulse{animation:pulse 1.6s ease-in-out infinite}
.pulse-fast{animation:pulse .9s ease-in-out infinite}
.pulse-slow{animation:pulse 2.5s ease-in-out infinite}
@keyframes pulse{50%{opacity:.3}}
"""


# ---------------------------------------------------------------------------
# Text laid out on a fixed monospace grid. Each character gets its own x, so
# the columns line up whatever monospace font the viewer has.

CW = 8.4   # cell width for 14px text


def grid_text(x0, y, runs, size=14, cw=CW, extra=""):
    """runs: [(text, fill, weight)] laid end to end. Returns (markup, columns used)."""
    out, col = [], 0
    for text, fill, weight in runs:
        if not text:
            continue
        xs = " ".join(n(x0 + (col + i) * cw) for i in range(len(text)))
        w = f' font-weight="{weight}"' if weight else ""
        out.append(f'<text x="{xs}" y="{n(y)}" fill="{fill}" font-size="{size}"{w}{extra}>{esc(text)}</text>')
        col += len(text)
    return "".join(out), col


# ---------------------------------------------------------------------------
# SESSION: what the header terminal types out.

NAME = "MISHKAT"
FULL_NAME = "Abu Zafar Mohammad Saleh Billah Mishkat"
NAME_LINES = ("Abu Zafar Mohammad", "Saleh Billah Mishkat")
TAGLINE = "Full-Stack Developer  │  Data Science & AI @ East West University, Dhaka"

G, W_, M_, D_ = ACCENT, TEXT, MUTED, DIM
SESSION = [
    ("comment", "// session restored · mishkat-workbench · dhaka, bd"),
    ("cmd", "whoami"),
    ("out", [("mishkat", W_, 600), ("  — full-stack developer, final-year CSE student (class of 2027)", M_, None)]),
    ("cmd", 'fetch-profile --target="Abu Zafar Md. S. B. Mishkat"'),
    ("out", [("✓ ", G, None), ("production ", M_, None), ("Student Management System  ", W_, 600), ("React · Node · MongoDB · Nginx", D_, None)]),
    ("out", [("✓ ", G, None), ("research   ", M_, None), ("EWU Bulletin RAG Assistant ", W_, 600), ("ChromaDB + BM25 · local Gemma", D_, None)]),
    ("out", [("✓ ", G, None), ("built      ", M_, None), ("CS² for Everyone           ", W_, 600), ("28 CS concepts, simulated live", D_, None)]),
    ("out", [("✓ ", G, None), ("focus      ", M_, None), ("Full-stack development & applied AI/ML", W_, None)]),
    ("cmd", "cat contact.txt"),
    ("out", [("portfolio ", M_, None), ("mishkat2025.github.io", G, None), ("   email ", M_, None), ("sbmishkat10@gmail.com", G, None)]),
    ("cmd", "ready-to-ship --mode=production"),
    ("out", [("● ", G, None), ("open to freelance projects and full-time roles", W_, None)]),
    ("prompt", ""),
]

PIXEL_FONT = {
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
}


def terminal_svg():
    rnd = random.Random(7)
    W = 900
    bar_h = 36
    px = 9                                  # pixel size for the name
    name_x, name_y = 44, bar_h + 30
    session_y = name_y + 7 * px + 92        # first session baseline
    lh = 22
    lines = len(SESSION)
    status_h = 28
    H = session_y + (lines - 1) * lh + 26 + status_h
    x0 = 44

    defs = [glow_filter("glow", 2.4, 2), glow_filter("soft", 1.4)]
    defs.append('<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
                '<rect width="4" height="1" fill="#ffffff" opacity=".035"/></pattern>')
    defs.append(f'<clipPath id="win"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12"/></clipPath>')
    defs.append(f'<radialGradient id="vignette" cx="30%" cy="20%" r="90%">'
                f'<stop offset="0" stop-color="{ACCENT}" stop-opacity=".07"/>'
                f'<stop offset=".6" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>')

    body = []
    # Window and title bar, like the terminal card on the portfolio.
    body.append(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="#111215" stroke="#27272a" stroke-width="1.5"/>')
    body.append(f'<g clip-path="url(#win)"><rect width="{W}" height="{H}" fill="url(#vignette)"/>')
    body.append(f'<rect width="{W}" height="{bar_h}" fill="#17181c"/><line x1="0" y1="{bar_h}" x2="{W}" y2="{bar_h}" stroke="#27272a"/>')
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        body.append(f'<circle cx="{22 + i * 20}" cy="{bar_h / 2}" r="6" fill="{c}"/>')
    body.append(f'<text x="96" y="{bar_h / 2 + 4.5}" fill="{MUTED}" font-size="13">mishkat-workbench ~ bash</text>')
    body.append(f'<circle class="pulse-fast" cx="{W - 64}" cy="{bar_h / 2}" r="4" fill="{ACCENT}"/>'
                f'<text x="{W - 54}" y="{bar_h / 2 + 4.5}" fill="{ACCENT}" font-size="13">live</text>')

    # A few stars drifting in the dark.
    for _ in range(26):
        sx, sy = rnd.uniform(470, W - 30), rnd.uniform(bar_h + 14, name_y + 7 * px + 50)
        r = rnd.choice((.8, 1, 1.2, 1.6))
        d = rnd.uniform(1.8, 4.5)
        body.append(f'<circle cx="{n(sx)}" cy="{n(sy)}" r="{r}" fill="{rnd.choice((TEXT, ACCENT))}" opacity=".5">'
                    f'<animate attributeName="opacity" values=".15;.8;.15" dur="{n(d)}s" begin="{n(rnd.uniform(0, 3))}s" repeatCount="indefinite"/></circle>')

    # Big pixel name, swept in column by column, with a dark drop shadow.
    cols = []
    for li, ch in enumerate(NAME):
        rows = PIXEL_FONT[ch]
        for c in range(5):
            on = [(r, c) for r in range(7) if rows[r][c] == "#"]
            cols.append((li * 6 + c, on))
    shadow, lit = [], []
    for col, on in cols:
        t = .15 + col * .022
        cells_s = "".join(f'<rect x="{name_x + col * px + 3}" y="{name_y + r * px + 3}" width="{px - 1}" height="{px - 1}"/>' for r, _ in on)
        cells_l = "".join(f'<rect x="{name_x + col * px}" y="{name_y + r * px}" width="{px - 1}" height="{px - 1}"/>' for r, _ in on)
        setter = f'<set attributeName="opacity" to="1" begin="{n(t)}s" fill="freeze"/>'
        shadow.append(f'<g opacity="0">{setter}{cells_s}</g>')
        lit.append(f'<g opacity="0">{setter}{cells_l}</g>')
    body.append(f'<g fill="#0b4d2f">{"".join(shadow)}</g>')
    body.append(f'<g fill="{ACCENT}" filter="url(#glow)">{"".join(lit)}'
                f'<animate attributeName="opacity" values="1;.55;1;1;.8;1" keyTimes="0;.02;.04;.6;.62;1" dur="7s" begin="1.2s" repeatCount="indefinite"/></g>')
    name_w = (len(NAME) * 6 - 1) * px

    # Name in full and tagline, then a boot bar.
    sub_y = name_y + 7 * px + 30
    body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin=".9s" fill="freeze"/>'
                f'<text x="{name_x + name_w + 24}" y="{name_y + 26}" fill="{TEXT}" font-size="14" font-weight="600">{esc(NAME_LINES[0])}</text>'
                f'<text x="{name_x + name_w + 24}" y="{name_y + 47}" fill="{TEXT}" font-size="14" font-weight="600">{esc(NAME_LINES[1])}</text>'
                f'<text x="{name_x}" y="{sub_y}" fill="{MUTED}" font-size="13.5">{esc(TAGLINE)}</text></g>')
    bar_y = sub_y + 20
    seg = 12
    body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="1.0s" fill="freeze"/>'
                f'<text x="{name_x}" y="{bar_y + 9}" fill="{DIM}" font-size="11">boot</text>')
    for i in range(seg):
        t = 1.05 + i * .1
        body.append(f'<rect x="{name_x + 42 + i * 16}" y="{bar_y}" width="12" height="10" fill="#16301f">'
                    f'<set attributeName="fill" to="{ACCENT}" begin="{n(t)}s" fill="freeze"/></rect>')
    done_t = 1.05 + seg * .1
    body.append(f'<text x="{name_x + 42 + seg * 16 + 8}" y="{bar_y + 9}" fill="{DIM}" font-size="11">'
                f'<tspan opacity="0"><set attributeName="opacity" to="1" begin="{n(done_t)}s" fill="freeze"/>'
                f'mishkat.sys ready</tspan></text></g>')

    # The session, typed out once and then kept on screen.
    t = done_t + .5
    cursor = [(0.0, -50, session_y - 13)]    # (time, x, y_top); starts hidden
    clips = []
    y = session_y
    for idx, (kind, payload) in enumerate(SESSION):
        if kind == "comment":
            body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{n(t)}s" fill="freeze"/>'
                        f'{grid_text(x0, y, [(payload, DIM, None)])[0]}</g>')
            t += .45
        elif kind in ("cmd", "prompt"):
            prompt, _ = grid_text(x0, y, [("$", ACCENT, 700)])
            body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{n(t)}s" fill="freeze"/>{prompt}</g>')
            cx = x0 + 2 * CW
            cursor.append((t, cx, y - 13))
            if kind == "prompt":
                break
            text = payload
            t += .25
            times = [0.0]
            for ch in text:
                times.append(times[-1] + rnd.uniform(.03, .075) + (.12 if ch == " " and rnd.random() < .3 else 0))
            dur = times[-1]
            cid = f"c{len(clips)}"
            widths = ";".join(n(i * CW) for i in range(len(text) + 1))
            keys = ";".join(n(tt / dur) if tt else "0" for tt in times)
            clips.append(f'<clipPath id="{cid}"><rect x="{n(cx)}" y="{n(y - 16)}" width="0" height="22">'
                         f'<animate attributeName="width" calcMode="discrete" values="{widths}" keyTimes="{keys}" '
                         f'begin="{n(t)}s" dur="{n(dur)}s" fill="freeze"/></rect></clipPath>')
            body.append(f'<g clip-path="url(#{cid})">{grid_text(cx, y, [(text, TEXT, None)])[0]}</g>')
            for i, tt in enumerate(times[1:], 1):
                cursor.append((t + tt, cx + i * CW, y - 13))
            t += dur + .35
        else:
            body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{n(t)}s" fill="freeze"/>'
                        f'{grid_text(x0 + 2 * CW, y, payload)[0]}</g>')
            cursor.append((t, -50, y - 13))       # hidden while output prints
            t += .1
            if SESSION[idx + 1][0] != "out":
                t += .35
        y += lh
    end = t
    # One block cursor follows the typing, then blinks at the last prompt.
    ks = ";".join(n(c[0] / end) if c[0] else "0" for c in cursor)
    xs = ";".join(n(c[1]) for c in cursor)
    ys = ";".join(n(c[2]) for c in cursor)
    body.append(f'<rect x="-50" y="{n(cursor[0][2])}" width="{n(CW)}" height="17" fill="{ACCENT}" opacity=".9">'
                f'<animate attributeName="x" calcMode="discrete" values="{xs}" keyTimes="{ks}" dur="{n(end)}s" fill="freeze"/>'
                f'<animate attributeName="y" calcMode="discrete" values="{ys}" keyTimes="{ks}" dur="{n(end)}s" fill="freeze"/>'
                f'<animate attributeName="opacity" calcMode="discrete" values=".9;0" keyTimes="0;.5" dur="1.06s" begin="{n(end)}s" repeatCount="indefinite"/></rect>')

    # The robot cat sits on the right and watches the screen.
    # (Mirrored so it faces left, toward the text.)
    body.append(f'<g transform="translate({W - 110} {name_y + 7 * px + 10}) scale(-1.55 1.55)" filter="url(#soft)" '
                f'stroke-linecap="round" stroke-linejoin="round">{sitting_cat(lx=.7, ly=.5)}</g>')

    # tmux-style status bar.
    sy = H - status_h
    body.append(f'<rect x="0" y="{sy}" width="{W}" height="{status_h}" fill="#0e1a14"/>'
                f'<line x1="0" y1="{sy}" x2="{W}" y2="{sy}" stroke="#1d3a2b"/>'
                f'<rect x="0" y="{sy}" width="92" height="{status_h}" fill="{ACCENT}"/>'
                f'<text x="14" y="{sy + 18.5}" fill="#06120c" font-size="12.5" font-weight="700">[mishkat]</text>'
                f'<text x="106" y="{sy + 18.5}" font-size="12.5"><tspan fill="{ACCENT}">0:bash*</tspan>'
                f'<tspan fill="{MUTED}">  1:node  2:python  3:rag</tspan></text>'
                f'<text x="{W - 16}" y="{sy + 18.5}" text-anchor="end" font-size="12.5" fill="{MUTED}">'
                f'<tspan fill="{ACCENT}">●</tspan> online · dhaka, bd · UTC+6</text>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#scan)"/></g>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'xml:space="preserve" font-family="{MONO}" role="img" '
            f'aria-label="Terminal: {esc(FULL_NAME)}, full-stack developer, data science and AI student at East West University">'
            f'<style>text{{white-space:pre}}{CAT_STYLE}</style><defs>{"".join(defs)}{"".join(clips)}</defs>{"".join(body)}</svg>')


# ---------------------------------------------------------------------------
# ROOM TEXT: what the things in the cat's room say.

NEON_SIGN = "mishkat2025.github.io"
DIPLOMA = ("B.Sc. in CSE", "East West University", "Data Science & AI", "class of 2027")
NOTES = [  # (lines, paper colour, tilt)
    (("✓ student", "mgmt system", "● LIVE"), "#f6d776", -4),
    (("✓ RAG", "assistant", "chromadb+bm25"), "#8ef0c0", 3),
    (("✓ CS² for", "Everyone", "28 simulations"), "#9fd3ff", 2),
    (("open to", "work!", "freelance+FT"), "#ffb3c7", -3),
]
BOOKS = [
    ["PYTHON", "C++", "JS", "TS", "SQL", "JAVA"],
    ["PYTORCH", "PANDAS", "ML", "LLMS", "RAG"],
    ["REACT", "NODE", "EXPRESS", "MONGO", "POSTGRES"],
    ["LINUX", "DOCKER", "NGINX", "GIT", "PM2"],
]
SCREEN = ["$ npm run dev", "  ready on :5173 ✓", "$ python rag.py", "> answer: grounded", "$ git push origin main"]
PLACE = "Dhaka, BD"

OUTLINE = "#1f5c41"     # furniture drawn in dim neon
FURN = "#0f1419"
LINE_W = 1.6


def basket_back(charging_vis):
    """The cat's charging pod (back half), from cat.js. charging_vis: SMIL for the beam."""
    o = [f'<rect x="38" y="-62" width="12" height="62" rx="3" {solid(1.8)}/>']
    for i in range(3):
        o.append(f'<rect x="41" y="{-22 - i * 7}" width="6" height="4" fill="{ACCENT}" opacity=".9">'
                 f'<animate attributeName="opacity" calcMode="discrete" values=".25;.9" keyTimes="0;{n((i + 1) / 4)}" '
                 f'dur="2.6s" repeatCount="indefinite"/></rect>')
    o.append(f'<circle cx="44" cy="-68" r="8" {solid(1.8)}/>'
             f'<polyline points="45.5,-73 42,-67.5 45.5,-67.5 42.5,-62.5" fill="none" stroke="{ACCENT}" stroke-width="1.5"/>'
             f'<path d="M37 -71Q22 -84 8 -60" fill="none" stroke="{ACCENT}" stroke-width="2"/>'
             f'<path d="M3 -57A4 4 0 0 1 11 -57Z" {solid(1.4)}/>'
             f'<polygon points="3,-56 11,-56 28,-22 -14,-22" fill="{ACCENT}" opacity="0">{charging_vis}</polygon>'
             f'<ellipse cx="0" cy="-22" rx="40" ry="8" {solid(2)}/>'
             f'<path d="M-31 -20Q-17 -30 0 -25Q17 -30 31 -20Z" {solid(1.3)} opacity=".7"/>')
    return "".join(o)


def basket_front():
    bowl = "M40 -22A40 8 0 0 1 -40 -22C-39 -4 -24 0 -14 0L14 0C24 0 39 -4 40 -22Z"
    o = [f'<path d="{bowl}" {solid(2)}/>', f'<g clip-path="url(#bowl)" stroke="{ACCENT}" stroke-width="1" fill="none">']
    rows = [-14, -8, -2]
    for y in rows:
        o.append(f'<path d="M-44 {y - 2}Q0 {y + 5} 44 {y - 2}" opacity=".45"/>')
    for r, y in enumerate(rows):
        top = -16 if r == 0 else rows[r - 1] + 1.5
        x = -36 + (r % 2) * 5
        while x <= 36:
            o.append(f'<line x1="{x}" y1="{n(top + 1)}" x2="{x}" y2="{n(y + 1)}" opacity=".35"/>')
            x += 10
    o.append('</g>')
    o.append(f'<path d="M40 -22A40 8 0 0 1 -40 -22" fill="none" stroke="{ACCENT}" stroke-width="3"/>')
    return "".join(o)


def room_svg():
    rnd = random.Random(11)
    W, H = 900, 340
    FLOOR_Y = 264
    T = 18.0                                     # one loop of the cat's routine
    S = 1.35                                     # cat and pod size
    dock = (100, 320)
    A = (dock[0] - 2 * S, dock[1] - 15 * S)      # curled up in the pod
    B = (218, 320)                               # sitting beside it
    C = (706, 320)                               # where the chase ends

    defs = [glow_filter("glow", 2.2), glow_filter("neon", 2.6, 2), glow_filter("soft", 1.2),
            f'<clipPath id="frame"><rect width="{W}" height="{H}" rx="12"/></clipPath>',
            '<clipPath id="bowl"><path d="M40 -22A40 8 0 0 1 -40 -22C-39 -4 -24 0 -14 0L14 0C24 0 39 -4 40 -22Z"/></clipPath>',
            '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#050b14"/><stop offset="1" stop-color="#0d1c2c"/></linearGradient>',
            '<linearGradient id="moonbeam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#bfe8ff" stop-opacity=".07"/><stop offset="1" stop-color="#bfe8ff" stop-opacity="0"/></linearGradient>',
            '<linearGradient id="lamp" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd27a" stop-opacity=".28"/><stop offset="1" stop-color="#ffd27a" stop-opacity="0"/></linearGradient>',
            f'<radialGradient id="screenglow"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".16"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>',
            '<radialGradient id="vig" cx="50%" cy="45%" r="75%"><stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>']
    o = [f'<g clip-path="url(#frame)">']

    # Wall, floor, baseboard.
    o.append(f'<rect width="{W}" height="{FLOOR_Y}" fill="#0f1217"/>')
    for x in range(14, W, 28):
        o.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{FLOOR_Y}" stroke="#13171d" stroke-width="2"/>')
    o.append(f'<rect y="{FLOOR_Y}" width="{W}" height="{H - FLOOR_Y}" fill="#0a0c10"/>')
    for i, y in enumerate((FLOOR_Y + 20, FLOOR_Y + 42, FLOOR_Y + 64)):
        o.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#14181e" stroke-width="1.5"/>')
        for x in range(60 + i * 70, W, 210):
            o.append(f'<line x1="{x}" y1="{y - 20}" x2="{x}" y2="{y}" stroke="#14181e" stroke-width="1.5"/>')
    o.append(f'<rect y="{FLOOR_Y - 8}" width="{W}" height="8" fill="#151a20"/>'
             f'<line x1="0" y1="{FLOOR_Y - 8}" x2="{W}" y2="{FLOOR_Y - 8}" stroke="#1f262f"/>')

    # Window: night sky over Dhaka, with a moon and a twinkling skyline.
    wx, wy, ww, wh = 46, 42, 168, 136
    o.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="url(#sky)"/>')
    for _ in range(18):
        sx, sy = rnd.uniform(wx + 6, wx + ww - 6), rnd.uniform(wy + 6, wy + 70)
        o.append(f'<circle cx="{n(sx)}" cy="{n(sy)}" r="{rnd.choice((.7, .9, 1.2))}" fill="#e6f1ff">'
                 f'<animate attributeName="opacity" values=".2;1;.2" dur="{n(rnd.uniform(1.6, 4))}s" begin="{n(rnd.uniform(0, 3))}s" repeatCount="indefinite"/></circle>')
    o.append(f'<g filter="url(#soft)"><circle cx="{wx + ww - 40}" cy="{wy + 30}" r="15" fill="#eaf6ef"/>'
             f'<circle cx="{wx + ww - 33}" cy="{wy + 25}" r="13" fill="#071120"/></g>')
    bx = wx
    while bx < wx + ww:
        bw = rnd.randint(14, 26)
        bh = rnd.randint(26, 62)
        top = wy + wh - bh
        o.append(f'<rect x="{bx}" y="{top}" width="{bw - 2}" height="{bh}" fill="#08111d"/>')
        for wy2 in range(top + 6, wy + wh - 4, 8):
            for wx2 in range(bx + 3, bx + bw - 5, 6):
                if rnd.random() < .28:
                    col = rnd.choice(("#ffcf70", "#ffcf70", ACCENT))
                    anim = (f'<animate attributeName="opacity" values=".9;.2;.9" dur="{n(rnd.uniform(3, 9))}s" '
                            f'begin="{n(rnd.uniform(0, 5))}s" repeatCount="indefinite"/>') if rnd.random() < .3 else ""
                    o.append(f'<rect x="{wx2}" y="{wy2}" width="2.4" height="3" fill="{col}" opacity=".75">{anim}</rect>')
        bx += bw
    o.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="none" stroke="#2a3440" stroke-width="6"/>'
             f'<line x1="{wx + ww / 2}" y1="{wy}" x2="{wx + ww / 2}" y2="{wy + wh}" stroke="#2a3440" stroke-width="4"/>'
             f'<line x1="{wx}" y1="{wy + wh / 2 - 6}" x2="{wx + ww}" y2="{wy + wh / 2 - 6}" stroke="#2a3440" stroke-width="4"/>'
             f'<rect x="{wx - 10}" y="{wy + wh}" width="{ww + 20}" height="8" rx="2" fill="#1b222a"/>')
    # Curtains on a rod.
    o.append(f'<line x1="{wx - 26}" y1="{wy - 12}" x2="{wx + ww + 26}" y2="{wy - 12}" stroke="#2f3a45" stroke-width="3"/>'
             f'<circle cx="{wx - 28}" cy="{wy - 12}" r="4" fill="#2f3a45"/><circle cx="{wx + ww + 28}" cy="{wy - 12}" r="4" fill="#2f3a45"/>')
    for side in (-1, 1):
        x_in = wx + 14 if side < 0 else wx + ww - 14
        x_out = wx - 22 if side < 0 else wx + ww + 22
        o.append(f'<path d="M{x_out} {wy - 12}L{x_in} {wy - 12}Q{x_in - side * 4} {wy + 60} {x_in + side * 10} {wy + wh + 30}'
                 f'L{x_out} {wy + wh + 30}Z" fill="#0f241b" stroke="{OUTLINE}" stroke-width="{LINE_W}"/>')
        for k in range(1, 3):
            fx = x_out + (x_in - x_out) * k / 3
            o.append(f'<path d="M{n(fx)} {wy - 10}Q{n(fx - side * 3)} {wy + 70} {n(fx + side * 4)} {wy + wh + 28}" '
                     f'fill="none" stroke="{OUTLINE}" stroke-width="1" opacity=".6"/>')
    # Moonlight falling on the floor.
    o.append(f'<polygon points="{wx + 10},{wy + wh + 8} {wx + ww - 10},{wy + wh + 8} {wx + ww + 120},{H} {wx + 40},{H}" fill="url(#moonbeam)"/>')

    # Bookshelf: the spines are the skills.
    sx0, sy0, sw, sh = 258, 64, 136, FLOOR_Y - 64
    o.append(f'<rect x="{sx0}" y="{sy0}" width="{sw}" height="{sh}" fill="{FURN}" stroke="{OUTLINE}" stroke-width="2"/>')
    shelf_ys = [sy0 + 50, sy0 + 100, sy0 + 150, sy0 + sh - 2]
    spine_cols = ["#1d6b4a", "#2b4a6f", "#6b4f2b", "#4a2f6b", "#1f5f5f", "#6b2b45", "#3f5f1f"]
    for row, y in enumerate(shelf_ys):
        if row < 3:
            o.append(f'<line x1="{sx0}" y1="{y}" x2="{sx0 + sw}" y2="{y}" stroke="{OUTLINE}" stroke-width="2"/>')
        x = sx0 + 6
        for label in BOOKS[row]:
            bw = max(13, min(20, 6 + len(label) * 1.6))
            bh = rnd.randint(36, 44)
            col = rnd.choice(spine_cols)
            o.append(f'<rect x="{n(x)}" y="{y - bh}" width="{n(bw)}" height="{bh}" rx="1.5" fill="{col}" stroke="#0b0e12"/>'
                     f'<text transform="translate({n(x + bw / 2 + 2.6)} {y - 4}) rotate(-90)" font-size="7" fill="#e6e6ea" '
                     f'opacity=".9" font-weight="600">{esc(label)}</text>')
            x += bw + 1.5
        if row == 1:   # a tipped-over book at the end of the row
            o.append(f'<rect x="{n(x + 2)}" y="{y - 13}" width="{n(sx0 + sw - x - 8)}" height="12" rx="1.5" fill="#2b4a6f" stroke="#0b0e12"/>')
    # On top: a plant and a CS² cube.
    o.append(f'<path d="M{sx0 + 18} {sy0}L{sx0 + 21} {sy0 - 16}L{sx0 + 37} {sy0 - 16}L{sx0 + 40} {sy0}Z" fill="#2a1f17" stroke="{OUTLINE}" stroke-width="{LINE_W}"/>')
    o.append(f'<g fill="#0f3a27" stroke="{ACCENT}" stroke-width="1" stroke-opacity=".6">'
             f'<animateTransform attributeName="transform" type="rotate" values="-2 {sx0 + 29} {sy0 - 16};2 {sx0 + 29} {sy0 - 16};-2 {sx0 + 29} {sy0 - 16}" dur="5s" repeatCount="indefinite"/>')
    for ang, ln in ((-60, 22), (-25, 26), (10, 24), (40, 20), (-90, 18)):
        a = math.radians(ang - 90)
        ex, ey = sx0 + 29 + math.cos(a) * ln, sy0 - 16 + math.sin(a) * ln
        o.append(f'<path d="M{sx0 + 29} {sy0 - 16}Q{n(ex - 6)} {n(ey + 4)} {n(ex)} {n(ey)}Q{n(ex + 6)} {n(ey + 8)} {sx0 + 29} {sy0 - 16}Z"/>')
    o.append('</g>')
    o.append(f'<g transform="translate({sx0 + 84} {sy0 - 26})"><rect width="26" height="26" rx="3" fill="#10161b" stroke="{ACCENT}" stroke-width="1.4"/>'
             f'<line x1="0" y1="9" x2="26" y2="9" stroke="{OUTLINE}"/><line x1="0" y1="17" x2="26" y2="17" stroke="{OUTLINE}"/>'
             f'<line x1="9" y1="0" x2="9" y2="26" stroke="{OUTLINE}"/><line x1="17" y1="0" x2="17" y2="26" stroke="{OUTLINE}"/>'
             f'<text x="13" y="17" text-anchor="middle" font-size="10" font-weight="700" fill="{ACCENT}" filter="url(#soft)">CS²</text></g>')

    # Wall clock above the corkboard, its hands turning.
    cx, cy = 490, 40
    o.append(f'<circle cx="{cx}" cy="{cy}" r="21" fill="{FURN}" stroke="{OUTLINE}" stroke-width="2.4"/>')
    for i in range(12):
        a = math.radians(i * 30)
        o.append(f'<line x1="{n(cx + math.sin(a) * 16)}" y1="{n(cy - math.cos(a) * 16)}" x2="{n(cx + math.sin(a) * 18.5)}" '
                 f'y2="{n(cy - math.cos(a) * 18.5)}" stroke="{OUTLINE}" stroke-width="1.4"/>')
    o.append(f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - 10}" stroke="{TEXT}" stroke-width="2" stroke-linecap="round">'
             f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="216s" repeatCount="indefinite"/></line>'
             f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - 15}" stroke="{TEXT}" stroke-width="1.4" stroke-linecap="round">'
             f'<animateTransform attributeName="transform" type="rotate" from="120 {cx} {cy}" to="480 {cx} {cy}" dur="{n(T)}s" repeatCount="indefinite"/></line>'
             f'<circle cx="{cx}" cy="{cy}" r="2" fill="{ACCENT}"/>')

    # Corkboard with sticky notes: the projects.
    kx, ky, kw, kh = 412, 72, 160, 124
    o.append(f'<rect x="{kx}" y="{ky}" width="{kw}" height="{kh}" rx="3" fill="#2a2016" stroke="#5a4630" stroke-width="4"/>')
    for _ in range(70):
        o.append(f'<circle cx="{n(rnd.uniform(kx + 4, kx + kw - 4))}" cy="{n(rnd.uniform(ky + 4, ky + kh - 4))}" r=".9" fill="#3b2e20"/>')
    for i, (lines, paper, tilt) in enumerate(NOTES):
        nx = kx + 10 + (i % 2) * 74
        ny = ky + 8 + (i // 2) * 58
        g = [f'<g transform="rotate({tilt} {nx + 33} {ny + 25})">'
             f'<rect x="{nx}" y="{ny}" width="66" height="50" fill="{paper}"/>'
             f'<rect x="{nx}" y="{ny + 44}" width="66" height="6" fill="#000" opacity=".08"/>']
        for j, line in enumerate(lines):
            weight = ' font-weight="700"' if j < 2 else ""
            size = 8.5 if j < 2 else 7
            g.append(f'<text x="{nx + 5}" y="{ny + 14 + j * 12}" font-size="{size}"{weight} fill="#1c1c1c">{esc(line)}</text>')
        g.append(f'<circle cx="{nx + 33}" cy="{ny + 3}" r="3" fill="#ff4d6d" stroke="#7a1c2e"/></g>')
        o.append("".join(g))

    # Framed degree, and a small map with a pin on home.
    dx, dy, dw, dh = 594, 62, 100, 76
    o.append(f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="#13151a" stroke="#b39a52" stroke-width="3"/>'
             f'<rect x="{dx + 6}" y="{dy + 6}" width="{dw - 12}" height="{dh - 12}" fill="none" stroke="#b39a52" stroke-width=".8" opacity=".6"/>')
    for j, (line, size, col, wt) in enumerate(zip(DIPLOMA, (10, 7, 6.5, 6.5), ("#efe6c4", "#cfc6a4", MUTED, MUTED), (700, 600, None, None))):
        wtxt = f' font-weight="{wt}"' if wt else ""
        o.append(f'<text x="{dx + dw / 2}" y="{dy + 22 + j * 12}" text-anchor="middle" font-size="{size}"{wtxt} fill="{col}">{esc(line)}</text>')
    o.append(f'<circle cx="{dx + dw - 16}" cy="{dy + dh - 15}" r="6" fill="#b39a52"/>'
             f'<path d="M{dx + dw - 19} {dy + dh - 10}l-2 8 3-2 2 3 1-8Z" fill="#8f2d3a"/>')
    mx_, my_, mw, mh = 600, 146, 88, 52
    o.append(f'<rect x="{mx_}" y="{my_}" width="{mw}" height="{mh}" fill="#0d1914" stroke="{OUTLINE}" stroke-width="2"/>'
             f'<path d="M{mx_ + 8} {my_ + 40}Q{mx_ + 20} {my_ + 14} {mx_ + 40} {my_ + 20}T{mx_ + 78} {my_ + 12}" fill="none" stroke="#2c7a8a" stroke-width="2" opacity=".7"/>'
             f'<path d="M{mx_ + 10} {my_ + 10}h22v10h-8v12h-14Z M{mx_ + 52} {my_ + 26}h24v18h-24Z" fill="#163526" opacity=".9"/>'
             f'<g transform="translate({mx_ + 44} {my_ + 30})"><circle r="6" fill="none" stroke="#ff4d6d" stroke-width="1.2">'
             f'<animate attributeName="r" values="3;10" dur="1.8s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values=".9;0" dur="1.8s" repeatCount="indefinite"/></circle>'
             f'<path d="M0 0C-4 -5 -5 -8 -5 -10A5 5 0 0 1 5 -10C5 -8 4 -5 0 0Z" fill="#ff4d6d"/><circle cy="-10" r="1.8" fill="#13151a"/></g>'
             f'<text x="{mx_ + mw / 2}" y="{my_ + mh - 5}" text-anchor="middle" font-size="7.5" font-weight="600" fill="{TEXT}">{esc(PLACE)}</text>')

    # Neon sign over the desk: the portfolio address.
    nx0, ny0 = 714, 34
    o.append(f'<line x1="{nx0 + 20}" y1="0" x2="{nx0 + 20}" y2="{ny0}" stroke="#2a3440"/><line x1="{nx0 + 150}" y1="0" x2="{nx0 + 150}" y2="{ny0}" stroke="#2a3440"/>'
             f'<rect x="{nx0}" y="{ny0}" width="172" height="32" rx="6" fill="#0a0f0c" stroke="#1a3a2a" stroke-width="1.5"/>'
             f'<text x="{nx0 + 86}" y="{ny0 + 21}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{ACCENT}" filter="url(#neon)">{esc(NEON_SIGN)}'
             f'<animate attributeName="opacity" calcMode="discrete" values="1;.35;1;.6;1" keyTimes="0;.71;.72;.74;.75" dur="6.5s" repeatCount="indefinite"/></text>')

    # Desk with monitor, lamp and mug.
    o.append(f'<ellipse cx="776" cy="148" rx="80" ry="54" fill="url(#screenglow)"/>')
    o.append(f'<rect x="700" y="196" width="190" height="9" rx="2" fill="#1a1f26" stroke="#2a333d"/>'
             f'<rect x="708" y="205" width="8" height="{FLOOR_Y - 8 - 205}" fill="#161b21"/>'
             f'<rect x="820" y="205" width="62" height="{FLOOR_Y - 8 - 205}" fill="{FURN}" stroke="{OUTLINE}" stroke-width="{LINE_W}"/>'
             f'<line x1="820" y1="232" x2="882" y2="232" stroke="{OUTLINE}" stroke-width="{LINE_W}"/>'
             f'<line x1="844" y1="218" x2="858" y2="218" stroke="{ACCENT}" stroke-width="2" opacity=".6"/>'
             f'<line x1="844" y1="244" x2="858" y2="244" stroke="{ACCENT}" stroke-width="2" opacity=".6"/>')
    o.append(f'<rect x="720" y="108" width="112" height="72" rx="4" fill="#06100b" stroke="#2b3a33" stroke-width="4"/>'
             f'<rect x="770" y="180" width="12" height="11" fill="#2b3a33"/><rect x="752" y="191" width="48" height="5" rx="2" fill="#2b3a33"/>')
    period = 9.0
    for j, line in enumerate(SCREEN):
        t0 = .4 + j * 1.2
        keys = f"0;{n(t0 / period)};{n((period - .3) / period)}"
        o.append(f'<text x="728" y="{122 + j * 11}" font-size="7" fill="{ACCENT}" opacity="0">{esc(line)}'
                 f'<animate attributeName="opacity" calcMode="discrete" values="0;.95;0" keyTimes="{keys}" dur="{n(period)}s" repeatCount="indefinite"/></text>')
    o.append(f'<rect x="728" y="168" width="4" height="7" fill="{ACCENT}"><animate attributeName="opacity" calcMode="discrete" values="1;0" keyTimes="0;.5" dur="1s" repeatCount="indefinite"/></rect>')
    o.append(f'<polygon points="852,132 878,132 900,196 834,196" fill="url(#lamp)"/>'
             f'<ellipse cx="872" cy="195" rx="12" ry="3" fill="#2a333d"/>'
             f'<polyline points="872,194 862,160 870,128" fill="none" stroke="#3a4552" stroke-width="3" stroke-linejoin="round"/>'
             f'<path d="M852 132L860 116L874 116L880 132Z" fill="#2c3540" stroke="#ffd27a" stroke-width="1" stroke-opacity=".5"/>')
    o.append(f'<rect x="806" y="182" width="14" height="14" rx="2" fill="#1d2a24" stroke="{OUTLINE}" stroke-width="1.4"/>'
             f'<path d="M820 186a4 4 0 0 1 0 7" fill="none" stroke="{OUTLINE}" stroke-width="1.6"/>'
             f'<text x="813" y="192" text-anchor="middle" font-size="5" fill="{ACCENT}">&lt;/&gt;</text>')
    for k in range(2):
        o.append(f'<path d="M{810 + k * 6} 178q-4 -6 0 -12t0 -12" fill="none" stroke="#c9d1d9" stroke-width="1.2" opacity="0">'
                 f'<animate attributeName="opacity" values="0;.45;0" dur="3s" begin="{k * 1.5}s" repeatCount="indefinite"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="0 4;0 -6" dur="3s" begin="{k * 1.5}s" repeatCount="indefinite"/></path>')

    # A bushy plant in a pot by the desk, short enough to leave the map in view.
    py = FLOOR_Y - 30
    o.append(f'<path d="M642 {FLOOR_Y - 8}L645 {py}L675 {py}L678 {FLOOR_Y - 8}Z" fill="#2a1f17" stroke="{OUTLINE}" stroke-width="{LINE_W}"/>')
    o.append(f'<g fill="#0f3a27" stroke="{ACCENT}" stroke-width="1" stroke-opacity=".5">'
             f'<animateTransform attributeName="transform" type="rotate" values="-2 660 {py};2 660 {py};-2 660 {py}" dur="6s" repeatCount="indefinite"/>')
    for ang, ln in ((-62, 30), (-32, 33), (0, 30), (30, 32), (60, 28), (-88, 24), (86, 22)):
        a = math.radians(ang - 90)
        ex, ey = 660 + math.cos(a) * ln, py + math.sin(a) * ln
        o.append(f'<path d="M660 {py}Q{n(ex - 10)} {n(ey + 8)} {n(ex)} {n(ey)}Q{n(ex + 9)} {n(ey + 13)} 660 {py}Z"/>')
    o.append('</g>')

    # Rug.
    o.append(f'<ellipse cx="470" cy="318" rx="250" ry="17" fill="#0e1d16" stroke="{OUTLINE}" stroke-width="2"/>'
             f'<ellipse cx="470" cy="318" rx="226" ry="11" fill="none" stroke="{OUTLINE}" stroke-width="1" stroke-dasharray="4 5" opacity=".7"/>')

    # ---- The cat's routine ----
    sleeping = [(0, 3.2), (15.4, T)]
    def vis(intervals, on="1", off="0"):
        """Opacity that is `on` during the given (start, end) seconds of each loop."""
        changes = sorted([(a, on) for a, _ in intervals] + [(b, off) for _, b in intervals])
        init = on if any(a <= 0 for a, _ in intervals) else off
        return discrete("opacity", [(t, v) for t, v in changes if 0 < t < T], T, init)

    o.append(f'<g transform="translate({dock[0]} {dock[1]}) scale({S})" filter="url(#glow)" stroke-linecap="round" '
             f'stroke-linejoin="round">{basket_back(vis(sleeping, on=".12"))}</g>')

    # The laser dot the cat chases.
    dot_pts = [(0, (330, 324)), (4.6, (330, 324)), (8.2, (796, 324)), (8.6, (796, 324)), (9.0, (774, 316)),
               (9.4, (806, 312)), (9.8, (788, 324)), (10.2, (788, 324)), (T, (330, 324))]
    o.append(f'<g opacity="0">{vis([(3.9, 10.2)])}'
             f'<g><animateTransform attributeName="transform" type="translate" dur="{n(T)}s" repeatCount="indefinite" '
             f'keyTimes="{";".join(n(t / T) if t else "0" for t, _ in dot_pts)}" values="{";".join(f"{x} {y}" for _, (x, y) in dot_pts)}"/>'
             f'<circle r="7" fill="#ff2d55" opacity=".25"/><circle r="3.2" fill="#ff4d6d" filter="url(#glow)"/></g></g>')

    path = [(0, A), (3.2, A), (3.4, (160, 290)), (3.6, B), (4.6, B), (8.6, C), (11.0, C), (15.0, B),
            (15.2, (160, 290)), (15.4, A), (T, A)]
    lie_body, _, _ = cat(lie=1, closed=1, tail=.6, battery=True)
    o.append(f'<g><animateTransform attributeName="transform" type="translate" dur="{n(T)}s" repeatCount="indefinite" '
             f'keyTimes="{";".join(n(t / T) if t else "0" for t, _ in path)}" values="{";".join(f"{n(x)} {n(y)}" for _, (x, y) in path)}"/>'
             f'<g><animateTransform attributeName="transform" type="scale" calcMode="discrete" dur="{n(T)}s" repeatCount="indefinite" '
             f'keyTimes="0;{n(11 / T)};{n(15.4 / T)}" values="1 1;-1 1;1 1"/>'
             f'<g transform="scale({S})" filter="url(#glow)" stroke-linecap="round" stroke-linejoin="round">'
             f'<g>{vis(sleeping)}{lie_body}</g>'
             f'<g opacity="0">{vis([(3.6, 4.6), (8.6, 11.0)])}{sitting_cat(lx=1, ly=.45)}</g>'
             f'<g opacity="0">{vis([(3.2, 3.6), (4.6, 8.6), (11.0, 15.4)])}{running_cat()}</g>'
             f'</g></g></g>')

    o.append(f'<g transform="translate({dock[0]} {dock[1]}) scale({S})" filter="url(#glow)" stroke-linecap="round" stroke-linejoin="round">{basket_front()}</g>')

    # Zs while it sleeps, and a heart when the chase is over.
    zx, zy = A[0] + 25 * S, A[1] - 22 * S
    zs = []
    for k in range(3):
        zs.append(f'<text x="{n(zx)}" y="{n(zy)}" font-size="{10 + k * 2}" font-weight="700" fill="{ACCENT}" opacity="0">z'
                  f'<animate attributeName="opacity" values="0;.9;0" dur="2.4s" begin="{k * .8}s" repeatCount="indefinite"/>'
                  f'<animateTransform attributeName="transform" type="translate" values="0 0;{8 + k * 3} -26" dur="2.4s" begin="{k * .8}s" repeatCount="indefinite"/></text>')
    o.append(f'<g filter="url(#soft)">{vis(sleeping)}{"".join(zs)}</g>')
    hx, hy = C[0] + 14 * S, C[1] - 62 * S
    o.append(f'<g opacity="0" filter="url(#glow)">{vis([(10.2, 11.2)])}<g>'
             f'<animateTransform attributeName="transform" type="translate" dur="{n(T)}s" repeatCount="indefinite" '
             f'keyTimes="0;{n(10.2 / T)};{n(11.2 / T)};1" values="0 0;0 0;0 -18;0 -18"/>'
             f'<path d="M{n(hx)} {n(hy + 6)}C{n(hx - 7)} {n(hy + 1)} {n(hx - 5)} {n(hy - 5)} {n(hx)} {n(hy - 1)}'
             f'C{n(hx + 5)} {n(hy - 5)} {n(hx + 7)} {n(hy + 1)} {n(hx)} {n(hy + 6)}Z" fill="#ff4d6d"/></g></g>')

    o.append(f'<rect width="{W}" height="{H}" fill="url(#vig)"/></g>')
    o.append(f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="12" fill="none" stroke="#27272a" stroke-width="1.5"/>')

    label = ("A cozy night-time room where Mishkat's neon robot cat sleeps in its charging basket, wakes up, "
             "chases a laser dot across the rug and goes back to bed. On the walls: a neon sign for mishkat2025.github.io, "
             "a B.Sc. in CSE from East West University (class of 2027), sticky notes for the student management system, "
             "the RAG assistant and CS² for Everyone, and a map pinned on Dhaka. The bookshelf spines list the skills.")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" xml:space="preserve" '
            f'font-family="{MONO}" role="img" aria-label="{esc(label)}">'
            f'<style>text{{white-space:pre}}{CAT_STYLE}</style><defs>{"".join(defs)}</defs>{"".join(o)}</svg>')


def divider_svg():
    """Paw prints trotting across the page."""
    W, H, count, period = 900, 30, 16, 6.0
    o = [f'<g fill="{ACCENT}">']
    for x in range(6, W, 12):
        o.append(f'<rect x="{x}" y="{H / 2 - 1}" width="2" height="2" opacity=".18"/>')
    for i in range(count):
        x = 40 + i * (W - 80) / (count - 1)
        y = H / 2 + (-6 if i % 2 else 6)
        a = .55 * i / count
        keys = f"0;{n(a)};{n(a + .02)};{n(min(a + .45, .99))};1"
        o.append(f'<g transform="translate({n(x)} {n(y)}) rotate(90)" opacity="0">'
                 f'<animate attributeName="opacity" values="0;0;.85;0;0" keyTimes="{keys}" dur="{period}s" repeatCount="indefinite"/>'
                 f'<ellipse cx="0" cy="2" rx="3.6" ry="3"/><circle cx="-4" cy="-3" r="1.5"/><circle cx="-1.4" cy="-5" r="1.5"/>'
                 f'<circle cx="1.4" cy="-5" r="1.5"/><circle cx="4" cy="-3" r="1.5"/></g>')
    o.append('</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="">'
            f'{"".join(o)}</svg>')


if __name__ == "__main__":
    for name, build in (("terminal.svg", terminal_svg), ("room.svg", room_svg), ("divider.svg", divider_svg)):
        (OUT / name).write_text(build(), encoding="utf-8")
        print("wrote", name)
