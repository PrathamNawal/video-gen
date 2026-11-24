#!/usr/bin/env python3
"""'The Night the Moon Disappeared' - 30s ink-doodle STORY (v2).

Story spine: hook (moon blinks out over a kid on a roof) -> escalating
consequences, each one *happening* on screen (dark, owl, dancing crab, wobbling
Earth) -> payoff (moon returns, smiling) -> loop line.

Engine: hand-wobbled pen strokes + live animated characters, a virtual camera
(push-in / pull-out / shake), parallax depth, per-scene backgrounds, line boil.

Usage: python3 ink_story.py out.mp4 [beats.json]        (silent-voice master + SFX)
       python3 ink_story.py x --stills dir t1 t2 ...
"""
import math, subprocess, sys, os, wave, json
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw

W, H, SS, FPS, DUR = 1280, 720, 2, 24, 30
CX, CY = 640, 360
CHALK = (244, 240, 226); INKD = (28, 28, 48)
YEL = (255, 222, 110); RED = (255, 112, 92); BLUE = (96, 170, 240)
GREEN = (130, 206, 130); BROWN = (206, 156, 104); SKIN = (255, 224, 190)
WHITE = (255, 253, 248); SAND = (214, 184, 132); INF = 1e9

# ------------------------------------------------------------ stroke font
FONT = {
 'A': [[(0,6),(2,0),(4,6)], [(0.9,4),(3.1,4)]],
 'B': [[(0,6),(0,0),(3,0),(4,1),(3,3),(0,3)], [(3,3),(4,4.5),(3,6),(0,6)]],
 'C': [[(4,1),(3,0),(1,0),(0,1),(0,5),(1,6),(3,6),(4,5)]],
 'D': [[(0,0),(0,6),(2.5,6),(4,4.5),(4,1.5),(2.5,0),(0,0)]],
 'E': [[(4,0),(0,0),(0,6),(4,6)], [(0,3),(3,3)]],
 'F': [[(4,0),(0,0),(0,6)], [(0,3),(3,3)]],
 'G': [[(4,1),(3,0),(1,0),(0,1),(0,5),(1,6),(3,6),(4,5),(4,3),(2.2,3)]],
 'H': [[(0,0),(0,6)], [(4,0),(4,6)], [(0,3),(4,3)]],
 'I': [[(1,0),(3,0)], [(2,0),(2,6)], [(1,6),(3,6)]],
 'J': [[(4,0),(4,5),(3,6),(1,6),(0,5)]],
 'K': [[(0,0),(0,6)], [(4,0),(0,3.5)], [(1.5,2.5),(4,6)]],
 'L': [[(0,0),(0,6),(4,6)]],
 'M': [[(0,6),(0,0),(2,4),(4,0),(4,6)]],
 'N': [[(0,6),(0,0),(4,6),(4,0)]],
 'O': [[(2,0),(0.5,1),(0,3),(0.5,5),(2,6),(3.5,5),(4,3),(3.5,1),(2,0)]],
 'P': [[(0,6),(0,0),(3,0),(4,1),(4,2),(3,3),(0,3)]],
 'Q': [[(2,0),(0.5,1),(0,3),(0.5,5),(2,6),(3.5,5),(4,3),(3.5,1),(2,0)], [(2.5,4.5),(4,6.3)]],
 'R': [[(0,6),(0,0),(3,0),(4,1),(4,2),(3,3),(0,3)], [(2,3),(4,6)]],
 'S': [[(4,1),(3,0),(1,0),(0,1),(0,2),(1,3),(3,3),(4,4),(4,5),(3,6),(1,6),(0,5)]],
 'T': [[(0,0),(4,0)], [(2,0),(2,6)]],
 'U': [[(0,0),(0,5),(1,6),(3,6),(4,5),(4,0)]],
 'V': [[(0,0),(2,6),(4,0)]],
 'W': [[(0,0),(1,6),(2,2),(3,6),(4,0)]],
 'X': [[(0,0),(4,6)], [(4,0),(0,6)]],
 'Y': [[(0,0),(2,3)], [(4,0),(2,3),(2,6)]],
 'Z': [[(0,0),(4,0),(0,6),(4,6)]],
 '0': [[(2,0),(0.5,1),(0,3),(0.5,5),(2,6),(3.5,5),(4,3),(3.5,1),(2,0)]],
 '1': [[(1,1.2),(2.2,0),(2.2,6)], [(1,6),(3.4,6)]],
 '?': [[(0,1),(1,0),(3,0),(4,1),(4,2),(2,3.5),(2,4.5)], [(2,5.5),(2,6)]],
 '.': [[(2,5.5),(2,6)]],
 '!': [[(2,0),(2,4.2)], [(2,5.5),(2,6)]],
 ',': [[(2.3,5),(1.7,6.8)]],
 "'": [[(2,0),(2,1.6)]],
 '-': [[(0.5,3),(3.5,3)]],
}
ROUND = set("CGOQSUDJBPR?0")

# ----------------------------------------------------------------- geometry
def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)

def clamp(x, a=0.0, b=1.0):
    return min(b, max(a, x))

def densify(p, step=7.0):
    p = np.asarray(p, float)
    if len(p) < 2: return p
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] == 0: return p
    n = max(2, int(s[-1] / step) + 1)
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, p[:, 0]), np.interp(ss, s, p[:, 1])], 1)

def chaikin(p, it):
    p = np.asarray(p, float)
    for _ in range(it):
        q = 0.75 * p[:-1] + 0.25 * p[1:]; r = 0.25 * p[:-1] + 0.75 * p[1:]
        out = np.empty((len(q) * 2, 2)); out[0::2] = q; out[1::2] = r
        p = np.vstack([p[:1], out, p[-1:]])
    return p

RNG = np.random.default_rng(21)

def wobble(p, amp, step=7.0):
    p = densify(p, step)
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    ph = RNG.uniform(0, 6.28, 4); f = RNG.uniform(0.02, 0.07, 4)
    dx = amp * (np.sin(s * f[0] + ph[0]) + 0.5 * np.sin(s * f[1] * 2.3 + ph[1]))
    dy = amp * (np.sin(s * f[2] + ph[2]) + 0.5 * np.sin(s * f[3] * 2.3 + ph[3]))
    return p + np.stack([dx, dy], 1)

def boil(p, seed):
    x, y = p[:, 0], p[:, 1]
    return np.stack([1.3 * np.sin(y * 0.031 + seed * 1.9) + 0.8 * np.sin(x * 0.017 + seed * 3.1),
                     1.3 * np.sin(x * 0.027 + seed * 2.3) + 0.8 * np.sin(y * 0.021 + seed * 1.3)], 1)

def circ(cx, cy, r, n=36, a0=0.0, a1=2 * math.pi):
    th = np.linspace(a0, a1, n + 1)
    return np.stack([cx + r * np.cos(th), cy + r * np.sin(th)], 1)

def arc(cx, cy, R, a0, a1, n=30):
    return circ(cx, cy, R, n, math.radians(a0), math.radians(a1))

def rot(P, a, c):
    P = np.asarray(P, float); d = P - np.asarray(c, float); ca, sa = math.cos(a), math.sin(a)
    return np.stack([c[0] + d[:, 0] * ca - d[:, 1] * sa, c[1] + d[:, 0] * sa + d[:, 1] * ca], 1)

def blob(cx, cy, rx, ry, n=9, irr=0.3):
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    k = 1 - irr / 2 + irr * RNG.random(n)
    pts = np.stack([cx + rx * k * np.cos(th), cy + ry * k * np.sin(th)], 1)
    return chaikin(np.vstack([pts, pts[:1], pts[1:2]]), 3)

def arrow_head(tip, frm, size=18):
    d = np.array(tip, float) - np.array(frm, float); d = d / (np.hypot(*d) + 1e-9)
    n = np.array([-d[1], d[0]])
    return np.array([tip - d * size + n * size * 0.55, tip, tip - d * size - n * size * 0.55])

# ------------------------------------------------------------------- items
ST = {'hud': False, 'par': 1.0, 'off': (), 'layer': 0, 'ink': CHALK}

class Item:
    def __init__(s, t0, hide):
        s.t0, s.hide = t0, hide
        s.hud, s.par, s.off, s.layer = ST['hud'], ST['par'], tuple(ST['off']), ST['layer']
    def vis(s, t):
        return s.t0 <= t < s.hide and not any(a <= t < b for a, b in s.off)

class Stroke(Item):
    def __init__(s, P, t0, dur, w, color, hide, ease):
        super().__init__(t0, hide)
        s.P = np.asarray(P, float); s.dur, s.w, s.color, s.ease = max(dur, 1e-3), w, color, ease
        seg = np.hypot(*np.diff(s.P, axis=0).T) if len(s.P) > 1 else np.zeros(0)
        s.cum = np.concatenate([[0], np.cumsum(seg)]); s.L = s.cum[-1]

class Fill(Item):
    def __init__(s, poly, t0, dur, color, hide, amax=0.92, fo=0.0):
        super().__init__(t0, hide)
        s.poly, s.dur, s.color, s.amax, s.fo = np.asarray(poly, float), max(dur, 1e-3), color, amax, fo

class Dot(Item):
    def __init__(s, x, y, r, t0, color, hide):
        super().__init__(t0, hide); s.x, s.y, s.r, s.color = x, y, r, color

class Dyn(Item):
    def __init__(s, t0, hide, fn, w, color):
        super().__init__(t0, hide); s.fn, s.w, s.color = fn, w, color

STROKES, FILLS, DOTS, DYNS = [], [], [], []
SCENE_ENDS, SFX = [], []
CAM_KEYS, SHAKES, RAMPS, BG_KEYS = [], [], [], []
_MARK = [0, 0, 0, 0]

def end_scene(E):
    SCENE_ENDS.append(E)
    for k, lst in enumerate((STROKES, FILLS, DOTS, DYNS)):
        for it in lst[_MARK[k]:]:
            it.hide = min(it.hide, E)
        _MARK[k] = len(lst)

def ink(c): return c if c is not None else ST['ink']

def stroke(pts, t0, dur, w=5, color=None, hide=INF, ease=True, amp=1.4):
    STROKES.append(Stroke(wobble(pts, amp), t0, dur, w, ink(color), hide, ease))

def fill(poly, t0, dur, color, hide=INF, amax=0.92, fo=0.0):
    FILLS.append(Fill(poly, t0, dur, color, hide, amax, fo))

def dot(x, y, r, t0, color=None, hide=INF):
    DOTS.append(Dot(x, y, r, t0, ink(color), hide))

def dyn(fn, t0, hide=INF, w=5, color=None):
    DYNS.append(Dyn(t0, hide, fn, w, ink(color)))

def seq(strokes, t0, t1, w, color, hide=INF):
    Ls = [max(1.0, float(np.sum(np.hypot(*np.diff(P, axis=0).T)))) for P in strokes]
    tot = sum(Ls); t = t0
    for P, L in zip(strokes, Ls):
        d = (t1 - t0) * L / tot
        STROKES.append(Stroke(P, t, d, w, color, hide, False)); t += d

def text_width(s, h):
    return sum(0.6 * h if c == ' ' else 0.887 * h for c in s) - 0.22 * h

def text(s, x, y, h, t0, t1, color=None, align='l', hide=INF, hud=False, layer=None):
    old = (ST['hud'], ST['layer'])
    ST['hud'] = hud; ST['layer'] = (1 if hud else 0) if layer is None else layer
    sc = h / 6.0
    if align == 'c': x -= text_width(s, h) / 2
    cx = x; out = []; step = max(3.0, min(7.0, h / 12))
    for c in s:
        if c == ' ': cx += 0.6 * h; continue
        for pts in FONT.get(c, []):
            P = chaikin(np.array(pts, float), 2 if c in ROUND else 0)
            X = cx + P[:, 0] * sc + (6 - P[:, 1]) * 0.1 * sc; Y = y + P[:, 1] * sc
            out.append(wobble(np.stack([X, Y], 1), h * 0.012, step))
        cx += 0.887 * h
    seq(out, t0, t1, max(3.5, h * 0.075), ink(color), hide)
    ST['hud'], ST['layer'] = old

def sparkle_burst(cx, cy, r0, r1, t0, hide, n=14, ry=1.0, colors=(YEL, CHALK)):
    for i in range(n):
        a = 2 * math.pi * i / n + 0.2
        stroke([(cx + r0 * math.cos(a), cy + r0 * ry * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * ry * math.sin(a))],
               t0 + 0.012 * i, 0.16, 6, colors[i % len(colors)], hide, amp=0.5)

# ------------------------------------------------------------- characters
def kid(x, y, t0, pose, s=1.25):
    def fn(t):
        p = pose(t)
        u = clamp((t - t0) / 0.3)
        sc = s * (1.0 if t0 < 0 else smooth(u) * (1 + 0.18 * math.sin(math.pi * u)))
        if sc < 0.02: return []
        hop = p.get('hop', 0.0); jx = p.get('jx', 0.0)
        T = lambda lx, ly: np.array([x + jx + lx * sc, y - hop + ly * sc])
        out = []
        out.append(("fill", np.array([T(-18, -62), T(18, -62), T(14, -102), T(-14, -102)]), RED, 0.97))
        for sd in (-1, 1):
            out.append(("poly", np.array([T(sd * 5, -62), T(sd * 15, -2)]), None, 5))
            out.append(("dot",) + tuple(T(sd * 16, -1) + [0, 0])[:2] + (6 * sc, CHALK))
        out.append(("poly", np.array([T(-18, -62), T(18, -62), T(14, -102), T(-14, -102), T(-18, -62)]), None, 4))
        arms = p.get('arm', (10, 10))
        for sd, a in zip((-1, 1), arms):
            a = math.radians(a); shx, shy = sd * 14, -96
            hand = (shx + sd * 36 * math.sin(a), shy + 36 * math.cos(a))
            out.append(("poly", np.array([T(shx, shy), T(*hand)]), RED, 6))
            out.append(("dot",) + tuple(T(*hand))[:2] + (5.5 * sc, SKIN))
        hc = T(0, -126)
        out.append(("fill", circ(hc[0], hc[1], 22 * sc), SKIN, 1.0))
        out.append(("poly", circ(hc[0], hc[1], 22 * sc), None, 4))
        for hx in (-6, 0, 6):
            out.append(("poly", np.array([T(hx, -146), T(hx * 1.6, -159)]), None, 4))
        lx, ly = p.get('look', (0, 0))
        mood = p.get('mouth', 'smile')
        for sd in (-1, 1):
            e = T(sd * 8 + lx * 3.5, -126 + ly * 3.5)
            big = 1.5 if mood == 'o' else 1.0
            out.append(("dot", e[0], e[1], 3.2 * sc * big, INKD))
        mc = T(lx * 2, -114 + ly * 2)
        if mood == 'smile':
            out.append(("poly", arc(mc[0], mc[1] - 4 * sc, 8 * sc, 25, 155, 10), INKD, 3))
        elif mood == 'o':
            out.append(("fill", circ(mc[0], mc[1], 5 * sc, 12), INKD, 1.0))
        elif mood == 'flat':
            out.append(("poly", np.array([mc + [-6 * sc, 0], mc + [6 * sc, 0]]), INKD, 3))
        return out
    return fn

def moon_dyn(cx, cy, r, t0, face=False, winks=()):
    def fn(t):
        u = clamp((t - t0) / 0.45)
        sc = 1.0 if t0 < 0 else smooth(u) * (1 + 0.14 * math.sin(math.pi * u))
        rr = r * sc * (1 + 0.008 * math.sin(t * 2.4))
        if rr < 3: return []
        out = []
        for k, (m, a) in enumerate([(1.85, .06), (1.5, .09), (1.22, .13)]):
            out.append(("fill", circ(cx, cy, rr * m, 40), YEL, a * (0.8 + 0.2 * math.sin(t * 2 + k))))
        out.append(("fill", circ(cx, cy, rr, 40), YEL, 0.97))
        out.append(("poly", circ(cx, cy, rr, 40), CHALK, 6))
        for (ox, oy, q) in [(0.50, -0.52, 0.17), (-0.58, 0.38, 0.13), (0.38, 0.62, 0.11), (-0.35, -0.55, 0.09)]:
            out.append(("poly", circ(cx + ox * rr, cy + oy * rr, q * rr, 14), (214, 176, 80), 3.5))
        if face:
            winking = any(a <= t < b for a, b in winks)
            for sd in (-1, 1):
                ex, ey = cx + sd * 0.28 * rr, cy - 0.08 * rr
                if winking and sd == 1:
                    out.append(("poly", arc(ex, ey, 0.06 * rr, 200, 340, 8), INKD, 4))
                else:
                    out.append(("dot", ex, ey, 0.06 * rr, INKD))
                out.append(("fill", circ(cx + sd * 0.5 * rr, cy + 0.14 * rr, 0.1 * rr, 14), RED, 0.5))
            out.append(("poly", arc(cx, cy + 0.05 * rr, 0.36 * rr, 30, 150, 14), INKD, 5))
        return out
    return fn

def heart(cx, cy, s):
    th = np.linspace(0, 2 * math.pi, 40)
    return np.stack([cx + s * 16 * np.sin(th) ** 3,
                     cy - s * (13 * np.cos(th) - 5 * np.cos(2 * th) - 2 * np.cos(3 * th) - np.cos(4 * th))], 1)

def stars(t0, hide, n, seed, area, par=0.3):
    r = np.random.default_rng(seed)
    pts = [(r.uniform(area[0], area[2]), r.uniform(area[1], area[3]), r.uniform(0, 6.28), r.uniform(1.6, 3.4)) for _ in range(n)]
    old = ST['par']; ST['par'] = par
    def fn(t):
        g = 1.0 if t0 < 0 else smooth((t - t0) / 1.0)
        return [("dot", x, y, rad * (0.6 + 0.4 * math.sin(t * 3 + ph)) * g, (225, 225, 240)) for x, y, ph, rad in pts]
    dyn(fn, t0, hide)
    ST['par'] = old

def skyline(t0, seed=4):
    old = ST['par']; ST['par'] = 0.5
    r = np.random.default_rng(seed); x = -20
    while x < 1300:
        w = r.uniform(70, 150); h = r.uniform(60, 190)
        fill([(x, 560), (x, 560 - h), (x + w, 560 - h), (x + w, 560)], t0, 0.1, (34, 40, 82), amax=1.0)
        for _ in range(int(w * h / 2600)):
            if r.random() < 0.5:
                dot(x + r.uniform(8, w - 8), 560 - r.uniform(10, h - 10), 2.6, t0, (236, 204, 112))
        x += w + r.uniform(6, 24)
    ST['par'] = old

def rooftop(t0):
    fill([(-50, 560), (1330, 560), (1330, 760), (-50, 760)], t0, 0.1, (12, 14, 30), amax=1.0)
    fill([(900, 500), (960, 500), (960, 562), (900, 562)], t0, 0.1, (12, 14, 30), amax=1.0)
    stroke([(-50, 560), (500, 558), (1330, 561)], t0, 0.5, 5, amp=1.0)
    stroke([(900, 562), (900, 500), (960, 500), (960, 562)], t0, 0.4, 5, amp=0.8)

# -------------------------------------------------------------- the story
BEATS = [
 (0.4, "TONIGHT.", 0.5), (1.3, "THE MOON DISAPPEARS.", 1.8), (3.7, "EVERYTHING GOES PITCH BLACK.", 2.3),
 (6.3, "THE OCEANS FORGET HOW TO DANCE.", 2.4), (9.2, "TIDES SHRINK BY TWO THIRDS.", 2.1),
 (11.7, "BUT HERE'S THE SCARY PART.", 2.0), (14.3, "THE MOON WAS HOLDING EARTH STEADY.", 2.5),
 (17.0, "WITHOUT IT, EARTH STARTS TO WOBBLE.", 2.5), (20.0, "AND OVER MILLIONS OF YEARS,", 1.8),
 (21.9, "THE SEASONS GO WILD.", 1.6), (23.8, "SO TONIGHT, LOOK UP.", 1.6), (25.9, "SAY THANKS TO THE MOON.", 1.9),
 (28.0, "IT DOES MORE THAN YOU THINK.", 1.9),
]
VANISH, RETURN = 2.55, 24.55

def captions():
    meta = json.load(open(BEATS_JSON)) if BEATS_JSON and os.path.exists(BEATS_JSON) else BEATS
    for t, s, d in meta:
        s = s.upper()
        parts = [s]
        if text_width(s, 30) > 1100 and ', ' in s:
            a, b = s.split(', ', 1); parts = [a + ',', b]
        tot = sum(len(p) for p in parts); cur = t
        for p in parts:
            dd = d * len(p) / tot
            text(p, 640, 648, 30, cur, cur + 0.35, align='c', hud=True, hide=cur + dd + (0.3 if p is parts[-1] else 0.0))
            cur += dd

BEATS_JSON = ""

def build():
    ST['ink'] = CHALK
    BG_KEYS[:] = [(0, (24, 28, 64)), (VANISH, (24, 28, 64)), (VANISH + .001, (10, 12, 26)), (5.99, (10, 12, 26)),
                  (6.0, (18, 36, 70)), (11.49, (18, 36, 70)), (11.5, (10, 12, 30)), (23.49, (10, 12, 30)),
                  (23.5, (10, 12, 26)), (RETURN - 0.05, (10, 12, 26)), (RETURN + 0.7, (36, 44, 96)), (30, (36, 44, 96))]
    CAM_KEYS[:] = [
        (0, 1.0, 640, 360, 'l'), (2.45, 1.12, 740, 300, 'l'), (2.9, 1.0, 640, 360, 's'), (3.49, 1.0, 640, 360, 'l'),
        (3.5, 1.0, 520, 520, 'l'), (4.9, 1.14, 600, 500, 's'), (5.4, 1.3, 860, 420, 'l'), (5.99, 1.3, 860, 420, 'l'),
        (6.0, 1.0, 640, 360, 'l'), (7.4, 1.1, 700, 420, 's'), (8.6, 1.5, 850, 480, 'l'), (11.49, 1.4, 850, 480, 'l'),
        (11.5, 4.0, 640, 380, 's'), (12.9, 1.0, 640, 380, 'l'), (16.2, 1.08, 640, 400, 's'), (16.5, 1.0, 640, 380, 'l'),
        (17.0, 1.0, 640, 380, 'l'), (23.45, 1.14, 640, 380, 'l'), (23.49, 1.14, 640, 380, 'l'),
        (23.5, 1.0, 640, 360, 'l'), (24.5, 1.08, 720, 310, 's'), (24.6, 1.0, 640, 360, 's'), (30, 1.0, 640, 360, 'l')]
    SHAKES[:] = [(VANISH, 0.5, 16), (5.0, 0.12, 4), (9.3, 0.25, 8), (11.5, 0.6, 7), (16.3, 0.45, 14),
                 (20.5, 0.2, 8), (21.1, 0.2, 8), (21.7, 0.2, 8), (22.3, 0.3, 10), (RETURN, 0.4, 10)]
    RAMPS[:] = [(17.0, 23.5, 1.5, 9.0)]

    # ============================== S1  HOOK (0 - 3.5)
    ST['ink'] = CHALK
    stars(-1, INF, 30, 1, (0, 0, 1280, 430))
    skyline(-1); rooftop(-1)
    dyn(moon_dyn(820, 240, 150, -1), -1, VANISH, color=CHALK)
    DYNS[-1].off = ((2.05, 2.15), (2.25, 2.33), (2.42, 2.5))
    def pose1(t):
        p = {'look': (0, -1), 'arm': (8 + 4 * math.sin(2 * t), 8 + 4 * math.sin(2 * t + 1)), 'hop': 1.5 * abs(math.sin(3 * t)), 'mouth': 'smile'}
        if t >= VANISH:
            q = t - VANISH
            p.update(arm=(150, 150), hop=30 * abs(math.sin(9 * q)) * math.exp(-q * 2.6), mouth='o',
                     look=(0, -1) if q < 0.5 else (math.sin(q * 4), -0.3))
        elif t > 1.9:
            p.update(mouth='flat')
        return p
    dyn(kid(400, 560, -1, pose1), -1, color=CHALK)
    sparkle_burst(820, 240, 165, 250, VANISH, 3.3)
    def ring(t):
        k = clamp((t - VANISH) / 0.5)
        return [("poly", circ(820, 240, 150 * (1 + 1.5 * k), 40), YEL, max(1.0, 8 * (1 - k)))]
    dyn(ring, VANISH, VANISH + 0.55)
    ST['hud'], ST['layer'] = True, 1
    def flash(t):
        a = clamp(1 - (t - VANISH) / 0.16)
        return [("fill", np.array([(0, 0), (W, 0), (W, H), (0, H)]), WHITE, 0.35 * a)]
    dyn(flash, VANISH, VANISH + 0.17)
    ST['hud'], ST['layer'] = False, 0
    text("!", 400, 285, 80, VANISH + 0.15, VANISH + 0.4, RED, hide=3.5)
    for i in range(10):  # dotted ghost of the moon
        a0 = i * 36 + 4
        stroke(arc(820, 240, 150, a0, a0 + 20, 8), 3.0 + 0.03 * i, 0.08, 4, (150, 150, 170), amp=0.3, ease=False)
    end_scene(3.5)

    # ============================== S2  DARK + OWL (3.5 - 6.0)
    stars(3.5, INF, 36, 2, (0, 0, 1280, 720))
    def pose2(t):
        p = {'arm': (10, 10), 'mouth': 'o', 'jx': 1.6 * math.sin(t * 38) if t < 5.0 else 0.0,
             'look': (math.sin(t * 2.2) * 0.9, -0.1)}
        k = smooth((t - 4.6) / 0.35)
        p['arm'] = (10, 10 + 85 * k)
        if t >= 4.1: p['look'] = (0.9, -0.2)
        return p
    dyn(kid(420, 640, 3.5, pose2, s=1.8), 3.5, color=CHALK)
    for ex in (950, 1000):
        dot(ex, 345, 8, 4.1, YEL, 5.0)
    DOTS[-1].off = DOTS[-2].off = ((4.5, 4.58),)
    stroke([(760, 440), (1000, 428), (1300, 440)], 5.0, 0.3, 9, CHALK, amp=1.5)
    ox, oy = 985, 370
    fill(circ(ox, oy, 50, 24), 5.0, 0.15, BROWN, amax=1.0)
    stroke(circ(ox, oy, 50, 24), 5.0, 0.3, 5, amp=0.8)
    for sd in (-1, 1):
        fill(circ(ox + sd * 20, oy - 18, 16, 16), 5.1, 0.1, WHITE, amax=1.0)
        stroke(circ(ox + sd * 20, oy - 18, 16, 16), 5.1, 0.2, 4, amp=0.3)
        dot(ox + sd * 20, oy - 18, 5.5, 5.2, INKD)
        stroke([(ox + sd * 44, oy - 36), (ox + sd * 46, oy - 66), (ox + sd * 22, oy - 46)], 5.2, 0.15, 4, amp=0.3)
    stroke([(ox - 8, oy - 8), (ox, oy + 6), (ox + 8, oy - 8)], 5.3, 0.1, 4, RED, amp=0.2)
    text("?", ox + 70, 275, 60, 5.4, 5.6, RED, hide=6.0)
    def beam(t):
        fl = 0.8 + 0.2 * math.sin(t * 50)
        return [("fill", np.array([(505, 452), (880, 280), (1130, 520)]), (255, 244, 190), 0.38 * fl)]
    dyn(beam, 5.0, 6.0)
    def torch(t):
        return [("fill", np.array([(500, 446), (520, 446), (520, 460), (500, 460)]), (210, 210, 220), 1.0)] if t >= 4.8 else []
    dyn(torch, 4.8, 6.0)
    end_scene(6.0)

    # ============================== S3  OCEAN + CRAB (6.0 - 11.5)
    stars(6.0, INF, 12, 3, (0, 0, 1280, 280))
    for i in range(10):
        a0 = i * 36 + 4
        stroke(arc(820, 140, 60, a0, a0 + 20, 8), 6.1 + 0.03 * i, 0.08, 4, (150, 150, 170), amp=0.3, ease=False)
    text("?", 820, 118, 44, 6.45, 6.65, RED, align='c', hide=INF)
    def A(t): return 46 - 39 * smooth((t - 7.4) / 1.2)
    def wy(x, t, y0, amp, lam, sp):
        ph = t * sp
        return y0 + amp * (np.sin(2 * np.pi * x / lam + ph) + 0.35 * np.sin(2 * np.pi * x / (lam * 0.45) + 1.6 * ph))
    xs = np.arange(-20, 1301, 8.0)
    def sea(t):
        a = A(t); out = []
        for (y0, k, lam, sp, col, al, wcol, ww) in [(398, 0.55, 260, 2.2, (52, 112, 190), 0.95, (200, 225, 255), 3),
                                                      (452, 1.0, 340, 3.2, BLUE, 0.93, CHALK, 5)]:
            ys = wy(xs, t, y0, a * k, lam, sp)
            P = np.stack([xs, ys], 1)
            out.append(("fill", np.vstack([P, [(1300, 760), (-20, 760)]]), col, al))
            out.append(("poly", P, wcol, ww))
        return out
    dyn(sea, 6.0, color=CHALK)
    def boat(t):
        a = A(t); x0 = 430
        y = float(wy(x0, t, 398, a * 0.55, 260, 2.2)); y2 = float(wy(x0 + 6, t, 398, a * 0.55, 260, 2.2))
        ang = math.atan2(y2 - y, 6)
        base = np.array([x0, y - 6])
        def R(pts): return rot(np.array(pts, float) + base, ang, base)
        hull = R([(-38, -4), (38, -4), (26, 16), (-26, 16), (-38, -4)])
        sail = R([(2, -8), (2, -66), (36, -8), (2, -8)])
        return [("fill", sail, RED, 1.0), ("poly", sail, None, 4), ("fill", hull, (240, 236, 220), 1.0),
                ("poly", hull, None, 4), ("poly", R([(0, -4), (0, -68)]), None, 4)]
    dyn(boat, 6.0, color=CHALK)
    def beach(t):
        return [("fill", np.array([(-20, 760), (-20, 600), (300, 588), (700, 604), (1300, 572), (1300, 760)]), SAND, 0.95),
                ("poly", np.array([(-20, 600), (300, 588), (700, 604), (1300, 572)]), (140, 110, 70), 4)]
    dyn(beach, 6.0, color=CHALK)
    def crab(t):
        cx, cy = 1010, 634
        k = A(t) / 46.0; sad = t > 8.2
        out = []
        for sd in (-1, 1):
            for j in range(3):
                out.append(("poly", np.array([(cx + sd * 26, cy + 6 + j * 6), (cx + sd * (44 + 4 * math.sin(t * 9 + j)), cy + 22 + j * 4)]), RED, 4))
            ang = math.radians((100 + 70 * math.sin(t * 7 + (0 if sd < 0 else 1.5))) * k + 20 * (1 - k) - (25 if sad else 0))
            hx, hy = cx + sd * (34 + 26 * math.sin(ang)), cy - 8 - 30 * math.cos(ang) * (1 if k > .2 else -0.4)
            out.append(("poly", np.array([(cx + sd * 26, cy - 2), (hx, hy)]), RED, 6))
            out.append(("fill", circ(hx, hy, 11, 12), RED, 1.0))
            out.append(("poly", circ(hx, hy, 11, 12), None, 3.5))
            out.append(("poly", np.array([(cx + sd * 12, cy - 16), (cx + sd * 14, cy - 34 + (6 if sad else 0))]), RED, 4))
        out.append(("fill", circ(cx, cy, 34, 20)[:, :] * [1, 0.65] + [0, cy * 0.35], RED, 1.0))
        out.append(("poly", circ(cx, cy, 34, 20) * [1, 0.65] + [0, cy * 0.35], None, 4))
        for sd in (-1, 1):
            ex, ey = cx + sd * 14, cy - 36 + (6 if sad else 0)
            out.append(("fill", circ(ex, ey, 8, 10), WHITE, 1.0))
            out.append(("dot", ex + (1 if sad else 0), ey + (3 if sad else 0), 3.2, INKD))
        if sad:
            out.append(("poly", arc(cx, cy + 14, 8, 200, 340, 8), INKD, 3))
            q = (t * 1.3) % 1.0
            if t > 8.6: out.append(("dot", cx + 14, cy - 22 + q * 40, 3.5, BLUE))
        else:
            out.append(("poly", arc(cx, cy - 2, 9, 20, 160, 8), INKD, 3))
        return out
    dyn(crab, 6.0, color=CHALK)
    text("ONE THIRD TIDES", 640, 96, 64, 9.3, 9.7, YEL, align='c', hud=True, hide=11.5)
    end_scene(11.5)

    # ============================== S4  EARTH (11.5 - 23.5)
    E = (640, 380); R = 140
    stars(11.5, INF, 70, 5, (-100, -100, 1380, 820), par=0.3)
    for i in range(36):
        a0 = i * 10
        t_ = 12.9 + i * 0.02
        stroke([(E[0] + 260 * math.cos(math.radians(a0)), E[1] + 190 * math.sin(math.radians(a0))),
                                                  (E[0] + 260 * math.cos(math.radians(a0 + 5)), E[1] + 190 * math.sin(math.radians(a0 + 5)))],
               t_, 0.08, 3, (120, 120, 150), 16.9, amp=0.2, ease=False)
    cont = [(-50, -35, 44, 34), (45, 25, 38, 52), (-18, 78, 28, 18)]
    blobs = [blob(E[0] + ox, E[1] + oy, rx, ry) for ox, oy, rx, ry in cont]
    a0 = math.radians(23.5)
    def tilt(t):
        k = clamp((t - 17.0) / 3.5)
        return a0 + math.radians(50) * k * math.sin(2 * math.pi * (0.45 + 0.8 * k) * (t - 17.0)) + math.radians(0.8) * math.sin(t * 3)
    def moon_pos(t):
        th = math.radians(-70 + (t - 12.8) * 45)
        return np.array([E[0] + 260 * math.cos(th), E[1] + 190 * math.sin(th)])
    def earth(t):
        ang = tilt(t); rt = ang - a0
        out = [("fill", circ(E[0], E[1], R, 44), BLUE, 0.98)]
        for b in blobs:
            bb = rot(b, rt, E); out += [("fill", bb, GREEN, 0.97), ("poly", bb, None, 3)]
        out.append(("poly", circ(E[0], E[1], R, 44), None, 6))
        d = np.array([math.sin(ang), -math.cos(ang)]); top = np.array(E) + d * (R + 62); bot = np.array(E) - d * (R + 62)
        out += [("poly", np.array([bot, top]), YEL, 6), ("poly", arrow_head(top, top - d * 30, 20), YEL, 6)]
        if t >= 13.0:
            fr = rot(np.array([[-34, -18], [34, -18], [0, 30]], float) + E, rt * 0.4, E)
            ex, ey = fr[0], fr[1]
            if t < 16.3:
                out += [("dot", ex[0], ex[1], 6, INKD), ("dot", ey[0], ey[1], 6, INKD), ("poly", arc(E[0], E[1] + 26, 16, 20, 160, 10), INKD, 4)]
            elif t < 17.0:
                for p_ in (ex, ey):
                    out += [("fill", circ(p_[0], p_[1], 11, 12), WHITE, 1.0), ("poly", circ(p_[0], p_[1], 11, 12), INKD, 3), ("dot", p_[0], p_[1], 4, INKD)]
                out.append(("fill", circ(E[0], E[1] + 30, 9, 12), INKD, 1.0))
            else:
                for p_ in (ex, ey):
                    q = np.linspace(0, 4 * math.pi, 30); rr = np.linspace(1, 11, 30)
                    sp = np.stack([p_[0] + rr * np.cos(q + t * 9), p_[1] + rr * np.sin(q + t * 9)], 1)
                    out.append(("poly", sp, INKD, 3))
                wv = np.linspace(-18, 18, 16)
                out.append(("poly", np.stack([E[0] + wv, E[1] + 30 + 4 * np.sin(wv * 0.5 + t * 14)], 1), INKD, 4))
        return out
    dyn(earth, 11.5, color=CHALK)
    def leash(t):
        if t < 12.9 or t >= 16.95: return []
        M = moon_pos(t); out = []
        dvec = np.array(E) - M; L = np.hypot(*dvec); u = dvec / L; nrm = np.array([-u[1], u[0]])
        a_pt = M + u * 32; b_pt = np.array(E) - u * (R + 4)
        if t < 16.3:
            s = np.linspace(0, 1, 18)[:, None]
            P = a_pt + (b_pt - a_pt) * s + nrm * (7 * np.sin(np.pi * s) * math.sin(t * 5))
            out.append(("poly", P, CHALK, 3))
            sc = 1.0
            out += moon_small(M, 1.0, t)
        else:
            p = (t - 16.3) / 0.6
            mid = (a_pt + b_pt) / 2
            ea = b_pt + (mid - b_pt) * (1 - p) ; ma = a_pt + (mid - a_pt) * (1 - p)
            out.append(("poly", np.array([b_pt, ea]), CHALK, 3)); out.append(("poly", np.array([a_pt, ma]), CHALK, 3))
            out += moon_small(moon_pos(16.3), max(0.0, 1 - (t - 16.3) / 0.25), t)
        return out
    def moon_small(M, k, t):
        if k <= 0.02: return []
        r_ = 30 * k
        return [("fill", circ(M[0], M[1], r_, 24), YEL, 0.97), ("poly", circ(M[0], M[1], r_, 24), CHALK, 4),
                ("dot", M[0] - 9 * k, M[1] - 4 * k, 3 * k, INKD), ("dot", M[0] + 9 * k, M[1] - 4 * k, 3 * k, INKD),
                ("poly", arc(M[0], M[1] + 2 * k, 11 * k, 30, 150, 8), INKD, 3)]
    dyn(leash, 12.9, 16.95, color=CHALK)
    mp = moon_pos(16.3)
    sparkle_burst(mp[0], mp[1], 40, 95, 16.3, 17.0, n=10)
    text("1,000 YEARS", 640, 92, 46, 20.0, 20.5, CHALK, align='c', hud=True, hide=21.9)
    text("1,000,000 YEARS", 640, 92, 46, 21.9, 22.5, RED, align='c', hud=True, hide=23.5)
    ST['hud'], ST['layer'] = False, 0
    def sun(t):
        cx, cy = 300, 250; out = [("fill", circ(cx, cy, 44, 24), YEL, 1.0), ("poly", circ(cx, cy, 44, 24), CHALK, 5)]
        for i in range(12):
            a = i * math.pi / 6 + t * 3
            out.append(("poly", np.array([(cx + 56 * math.cos(a), cy + 56 * math.sin(a)), (cx + 76 * math.cos(a), cy + 76 * math.sin(a))]), YEL, 5))
        return out
    def snow(t):
        cx, cy = 980, 250; out = []
        for i in range(6):
            a = i * math.pi / 3 + t * 2
            tip = (cx + 60 * math.cos(a), cy + 60 * math.sin(a))
            out.append(("poly", np.array([(cx, cy), tip]), (160, 215, 255), 5))
            for sgn in (-1, 1):
                b = (cx + 38 * math.cos(a), cy + 38 * math.sin(a))
                out.append(("poly", np.array([b, (b[0] + 16 * math.cos(a + sgn * 0.9), b[1] + 16 * math.sin(a + sgn * 0.9))]), (160, 215, 255), 4))
        return out
    for i, t0 in enumerate([20.5, 21.1, 21.7, 22.3]):
        t1 = t0 + 0.55
        if i % 2 == 0:
            dyn(sun, t0, t1, color=CHALK); text("HOT!", 300, 335, 52, t0, t0 + 0.2, RED, align='c', hud=False, hide=t1)
        else:
            dyn(snow, t0, t1, color=CHALK); text("FREEZING!", 980, 335, 46, t0, t0 + 0.2, (160, 215, 255), align='c', hud=False, hide=t1)
    dyn(sun, 22.9, 23.5, color=CHALK)
    end_scene(23.5)

    # ============================== S5  PAYOFF (23.5 - 30)
    stars(23.5, INF, 30, 1, (0, 0, 1280, 430))
    skyline(23.5); rooftop(23.5)
    dyn(moon_dyn(820, 240, 150, RETURN, face=True, winks=((26.9, 27.15),)), RETURN, color=CHALK)
    def pose5(t):
        p = {'look': (0, -1), 'arm': (8, 8), 'mouth': 'flat', 'hop': 0}
        if t >= RETURN:
            q = t - RETURN
            p.update(mouth='smile', look=(0.7, -0.7), hop=34 * abs(math.sin(8 * q)) * math.exp(-q * 2.2) if q < 1.6 else 0,
                     arm=(160, 160) if q < 1.2 else (14, 140 + 28 * math.sin(9 * t)))
        return p
    dyn(kid(400, 560, 23.5, pose5), 23.5, color=CHALK)
    sparkle_burst(820, 240, 165, 250, RETURN, RETURN + 0.8)
    ST['hud'], ST['layer'] = True, 1
    def flash2(t):
        a = clamp(1 - (t - RETURN) / 0.4)
        return [("fill", np.array([(0, 0), (W, 0), (W, H), (0, H)]), (255, 240, 200), 0.4 * a)]
    dyn(flash2, RETURN, RETURN + 0.45)
    ST['hud'], ST['layer'] = False, 0
    def hearts(t):
        out = []
        for i in range(4):
            q = (t - 26.1 - i * 0.35)
            if 0 <= q < 1.6:
                out.append(("fill", heart(430 + 22 * math.sin(q * 3 + i) + i * 14, 400 - q * 150, 0.9 + 0.2 * i), RED, 0.9 * (1 - q / 1.6)))
        return out
    dyn(hearts, 26.1, 29.6)
    text("THANK YOU,", 60, 80, 66, 26.0, 26.6, YEL, hud=True)
    text("MOON.", 60, 170, 66, 26.6, 27.1, YEL, hud=True)
    end_scene(30.0)
    captions()

# ===================================================================== render
NOISE = None

def bg_color(t):
    ks = BG_KEYS
    if t <= ks[0][0]: return np.array(ks[0][1], float)
    for a, b in zip(ks, ks[1:]):
        if a[0] <= t < b[0]:
            u = (t - a[0]) / (b[0] - a[0]); return np.array(a[1], float) * (1 - u) + np.array(b[1], float) * u
    return np.array(ks[-1][1], float)

def cam(t):
    ks = CAM_KEYS; z, fx, fy = ks[-1][1:4]
    for a, b in zip(ks, ks[1:]):
        if a[0] <= t < b[0]:
            u = (t - a[0]) / (b[0] - a[0]); u = smooth(u) if a[4] == 's' else u
            z, fx, fy = [a[i] * (1 - u) + b[i] * u for i in (1, 2, 3)]; break
    sx = sy = 0.0
    for t0, dur, amp in SHAKES:
        if t0 <= t < t0 + dur:
            k = 1 - (t - t0) / dur; sx += amp * k * math.sin(t * 71); sy += amp * k * math.cos(t * 63)
    for a, b, a0, a1 in RAMPS:
        if a <= t < b:
            amp = a0 + (a1 - a0) * (t - a) / (b - a); sx += amp * math.sin(t * 53); sy += amp * math.cos(t * 47)
    return z, fx, fy, sx, sy

def xf(P, c, it):
    if it.hud: return P
    z, fx, fy, sx, sy = c
    zp = 1 + (z - 1) * it.par
    return (P - np.array([fx, fy])) * zp + np.array([CX + sx * it.par, CY + sy * it.par])

def zw(w, c, it):
    return w if it.hud else w * (1 + (c[0] - 1) * it.par) ** 0.6

def partial(st, u):
    if u >= 1: return st.P
    target = u * st.L
    i = int(np.searchsorted(st.cum, target))
    if i <= 0: return st.P[:1]
    seglen = st.cum[i] - st.cum[i - 1]
    f = (target - st.cum[i - 1]) / seglen if seglen > 0 else 1
    return np.vstack([st.P[:i], st.P[i - 1] + (st.P[i] - st.P[i - 1]) * f])

def line(d, pts, w, color, seed, c, it):
    pts = np.asarray(pts, float)
    if len(pts) < 2: return
    p = xf(pts + boil(pts, seed), c, it) * SS
    xy = [tuple(q) for q in p]
    wi = max(2, int(round(zw(w, c, it) * SS)))
    d.line(xy, fill=color, width=wi, joint="curve")
    r = wi / 2
    for q in (xy[0], xy[-1]):
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=color)

def mixc(bg, col, a):
    return tuple(int(bg[i] * (1 - a) + col[i] * a) for i in range(3))

def render(fi, t_override=None):
    t = fi / FPS if t_override is None else t_override
    seed = int(t * 8); c = cam(t); bg = bg_color(t)
    arr = np.clip(bg.astype(np.float32)[None, None, :] + NOISE, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr); d = ImageDraw.Draw(img)
    def drawfill(poly, col, a, it):
        if a <= 0.003: return
        p = xf(np.asarray(poly, float), c, it) * SS
        if not it.hud: p = p + np.array([4, 3]) * SS
        if a >= 0.97:
            d.polygon([tuple(q) for q in p], fill=tuple(col)); return
        x0, y0 = max(0, int(p[:, 0].min()) - 1), max(0, int(p[:, 1].min()) - 1)
        x1, y1 = min(W * SS, int(p[:, 0].max()) + 2), min(H * SS, int(p[:, 1].max()) + 2)
        if x1 <= x0 or y1 <= y0: return
        mask = Image.new('L', (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(mask).polygon([(q[0] - x0, q[1] - y0) for q in p], fill=int(255 * a))
        region = img.crop((x0, y0, x1, y1))
        img.paste(Image.composite(Image.new('RGB', region.size, tuple(col)), region, mask), (x0, y0))
    for layer in (0, 1):
        for f in FILLS:
            if f.layer != layer or not f.vis(t): continue
            a = smooth((t - f.t0) / f.dur) * f.amax
            if f.fo: a *= clamp((f.hide - t) / f.fo)
            drawfill(f.poly, f.color, a, f)
        for s in STROKES:
            if s.layer != layer or not s.vis(t): continue
            u = (t - s.t0) / s.dur; u = smooth(u) if s.ease else min(1.0, u)
            line(d, partial(s, u), s.w, s.color, seed, c, s)
        for o in DOTS:
            if o.layer != layer or not o.vis(t): continue
            x, y = o.x + 0.8 * math.sin(seed * 2.1 + o.y), o.y + 0.8 * math.sin(seed * 1.7 + o.x)
            p = xf(np.array([[x, y]]), c, o)[0] * SS; r = zw(o.r, c, o) * SS
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=o.color)
        for dy in DYNS:
            if dy.layer != layer or not dy.vis(t): continue
            for sh in dy.fn(t):
                k = sh[0]
                if k == "poly":
                    line(d, sh[1], sh[3] if len(sh) > 3 and sh[3] else dy.w, sh[2] if len(sh) > 2 and sh[2] else dy.color, seed, c, dy)
                elif k == "fill":
                    drawfill(sh[1], sh[2], sh[3], dy)
                else:
                    p = xf(np.array([[sh[1], sh[2]]]), c, dy)[0] * SS; r = zw(sh[3], c, dy) * SS
                    if r > 0.4:
                        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=sh[4] if len(sh) > 4 and sh[4] else dy.color)
    return img.reduce(SS)

def render_bytes(fi):
    return render(fi).tobytes()

def make_noise():
    r = np.random.default_rng(3)
    n = r.normal(0, 2.0, (H * SS // 2, W * SS // 2)).astype(np.float32)
    n = np.asarray(Image.fromarray(np.clip(n * 12 + 128, 0, 255).astype(np.uint8)).resize((W * SS, H * SS), Image.BILINEAR), np.float32)
    n = (n - 128) / 12
    yy, xx = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32)
    vig = ((xx / (W * SS) - .5) ** 2 + (yy / (H * SS) - .5) ** 2) * 26
    return (n * 1.2 - vig)[..., None]

# ===================================================================== audio
def make_audio(path):
    sr = 44100; n = sr * DUR; t = np.arange(n) / sr
    r = np.random.default_rng(5)
    def put(sig, at):
        i = int(at * sr)
        if i < 0: sig = sig[-i:]; i = 0
        m = min(len(sig), n - i)
        if m > 0: mix_[i:i + m] += sig[:m]
    mix_ = np.zeros(n)
    # pad: dark minor until the moon returns, then warm major
    env = np.minimum(1, t / 1.5) * np.minimum(1, (DUR - t) / 1.5)
    x = np.clip((t - (RETURN - 0.2)) / 0.8, 0, 1)
    dark = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate([110.0, 164.81, 220.0, 261.63]))
    warm = sum(np.sin(2 * np.pi * f * t + k) for k, f in enumerate([110.0, 164.81, 220.0, 277.18, 329.63]))
    mix_ += (dark * (1 - x) + warm * x) * env * 0.016 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.1 * t))
    act = np.zeros(n)
    for s in STROKES:
        if s.hud: continue
        act[max(0, int(s.t0 * sr)):min(n, int((s.t0 + s.dur) * sr))] = 1.0
    k = np.hanning(int(0.05 * sr)); act = np.convolve(act, k / k.sum(), 'same')
    nz = np.convolve(np.diff(r.normal(size=n + 1)), np.ones(3) / 3, 'same')
    mix_ += nz * act * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * 0.035
    def tt(d): return np.arange(int(d * sr)) / sr
    def boom(at):
        x_ = tt(1.6); sig = (np.sin(2 * np.pi * 52 * x_) * np.exp(-x_ * 2.2) * 0.9 + np.sin(2 * np.pi * 130 * x_) * np.exp(-x_ * 6) * 0.35
                             + r.normal(size=len(x_)) * np.exp(-x_ * 9) * 0.22)
        put(sig, at)
        y_ = tt(0.5); put(r.normal(size=len(y_)) * (y_ / 0.5) ** 2 * 0.16, at - 0.5)
    def hit(at, f=70, a=0.55):
        x_ = tt(0.3); put(np.sin(2 * np.pi * f * x_) * np.exp(-x_ * 14) * a + r.normal(size=len(x_)) * np.exp(-x_ * 60) * 0.12, at)
    def sweep(at, d, f0, f1, a, noise=0.0):
        x_ = tt(d); ph = 2 * np.pi * np.cumsum(f0 + (f1 - f0) * (x_ / d)) / sr
        ramp = (x_ / d) ** 1.5 if f1 > f0 else np.sin(np.pi * x_ / d) ** 0.7
        put((np.sin(ph) * a + r.normal(size=len(x_)) * noise) * ramp, at)
    def chime(at):
        for i, f in enumerate([440, 554.4, 659.3, 880, 1108.7, 1318.5]):
            x_ = tt(1.4); put(np.sin(2 * np.pi * f * x_) * np.exp(-x_ * 3.2) * 0.07, at + i * 0.07)
    boom(VANISH)
    put(np.sin(2 * np.pi * 1800 * tt(0.03)) * 0.25 * np.exp(-tt(0.03) * 120), 5.0)
    sweep(7.4, 1.2, 520, 110, 0.12)
    hit(9.3, 60, 0.6); hit(11.5, 55, 0.5)
    sweep(10.9, 0.8, 200, 1300, 0.07, 0.05)
    x_ = tt(0.5); put((r.normal(size=len(x_)) * 0.25 + np.sin(2 * np.pi * np.cumsum(900 * np.exp(-x_ * 8) + 150) / sr) * 0.4) * np.exp(-x_ * 14), 16.3)
    for a in (20.5, 21.1, 21.7, 22.3): hit(a, 80, 0.4)
    # wobble drone
    w0, w1 = int(17.0 * sr), int(23.5 * sr); kk = (t[w0:w1] - 17.0) / 6.5
    mix_[w0:w1] += np.sin(2 * np.pi * 82 * t[w0:w1] + (2 + 5 * kk) * np.sin(2 * np.pi * (1 + 3 * kk) * t[w0:w1])) * (0.03 + 0.09 * kk) * np.minimum(1, (23.5 - t[w0:w1]) / 0.3)
    chime(RETURN); hit(RETURN, 65, 0.5)
    for ph_, at in [(0, 26.9)]: put(np.sin(2 * np.pi * 1568 * tt(0.4)) * np.exp(-tt(0.4) * 10) * 0.06, at)
    mix_ = mix_ / max(1e-6, np.abs(mix_).max()) * 0.85
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((mix_ * 32767).astype('<i2').tobytes())

# ======================================================================= main
def init():
    global NOISE
    NOISE = make_noise()

if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[2] != "--stills":
        BEATS_JSON = sys.argv[3]
    build(); init()
    if len(sys.argv) > 2 and sys.argv[2] == "--stills":
        os.makedirs(sys.argv[3], exist_ok=True)
        for ts in sys.argv[4:]:
            render(0, float(ts)).save(os.path.join(sys.argv[3], f"t{float(ts):05.2f}.png"))
        sys.exit()
    out = sys.argv[1]; wav = out + ".wav"
    make_audio(wav)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
                           "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
                          stdin=subprocess.PIPE)
    with Pool(4) as p:
        for i, b in enumerate(p.imap(render_bytes, range(FPS * DUR), chunksize=4)):
            ff.stdin.write(b)
            if i % 120 == 0: print("frame", i, flush=True)
    ff.stdin.close(); ff.wait(); os.remove(wav)
    print("done", out)
