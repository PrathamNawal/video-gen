#!/usr/bin/env python3
"""30-second ink-doodle animation: "What if the Moon vanished?"

Everything is drawn from code: hand-wobbled pen strokes that are progressively
inked, a single-stroke lettering font, "line boil" (the whole drawing jitters at
8 fps like traced hand animation), loose misregistered colour washes, and a
synthesised soundtrack (pen scratch, pop, chimes, soft pad).

Usage: python3 ink_doodle.py out.mp4 [--stills dir t1 t2 ...]
"""
import math, subprocess, sys, os, wave
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, SS, FPS, DUR = 1280, 720, 2, 24, 30
INK = (28, 28, 48)
PAPER = (246, 240, 225)
RED = (222, 78, 58)
YEL = (252, 220, 110)
BLUE = (120, 176, 226)
GREEN = (134, 196, 128)
BROWN = (206, 156, 104)
WHITE = (255, 253, 248)

# ---------------------------------------------------------------- stroke font
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
 '?': [[(0,1),(1,0),(3,0),(4,1),(4,2),(2,3.5),(2,4.5)], [(2,5.5),(2,6)]],
 '.': [[(2,5.5),(2,6)]],
 '!': [[(2,0),(2,4.2)], [(2,5.5),(2,6)]],
 ',': [[(2.3,5),(1.7,6.8)]],
 "'": [[(2,0),(2,1.6)]],
}
ROUND = set("CGOQSUDJBPR?")

# ----------------------------------------------------------------- geometry
def densify(p, step=7.0):
    p = np.asarray(p, float)
    if len(p) < 2:
        return p
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] == 0:
        return p
    n = max(2, int(s[-1] / step) + 1)
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, p[:, 0]), np.interp(ss, s, p[:, 1])], 1)

def chaikin(p, it):
    p = np.asarray(p, float)
    for _ in range(it):
        q = 0.75 * p[:-1] + 0.25 * p[1:]
        r = 0.25 * p[:-1] + 0.75 * p[1:]
        out = np.empty((len(q) * 2, 2)); out[0::2] = q; out[1::2] = r
        p = np.vstack([p[:1], out, p[-1:]])
    return p

def wobble(p, amp, r, step=7.0):
    p = densify(p, step)
    seg = np.hypot(*np.diff(p, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    ph = r.uniform(0, 6.28, 4); f = r.uniform(0.02, 0.07, 4)
    dx = amp * (np.sin(s * f[0] + ph[0]) + 0.5 * np.sin(s * f[1] * 2.3 + ph[1]))
    dy = amp * (np.sin(s * f[2] + ph[2]) + 0.5 * np.sin(s * f[3] * 2.3 + ph[3]))
    return p + np.stack([dx, dy], 1)

def boil(p, seed):
    x, y = p[:, 0], p[:, 1]
    return np.stack([1.3 * np.sin(y * 0.031 + seed * 1.9) + 0.8 * np.sin(x * 0.017 + seed * 3.1),
                     1.3 * np.sin(x * 0.027 + seed * 2.3) + 0.8 * np.sin(y * 0.021 + seed * 1.3)], 1)

# -------------------------------------------------------------------- items
class Stroke:
    def __init__(s, P, t0, dur, w, color, hide, ease):
        s.P = np.asarray(P, float); s.t0, s.dur, s.w = t0, max(dur, 1e-3), w
        s.color, s.hide, s.ease = color, hide, ease
        seg = np.hypot(*np.diff(s.P, axis=0).T) if len(s.P) > 1 else np.zeros(0)
        s.cum = np.concatenate([[0], np.cumsum(seg)]); s.L = s.cum[-1]

class Fill:
    def __init__(s, poly, t0, dur, color, hide):
        s.poly, s.t0, s.dur, s.color, s.hide = np.asarray(poly, float), t0, max(dur, 1e-3), color, hide

class Dot:
    def __init__(s, x, y, r, t0, color, hide):
        s.x, s.y, s.r, s.t0, s.color, s.hide = x, y, r, t0, color, hide

class Dyn:
    def __init__(s, t0, hide, fn, w, color):
        s.t0, s.hide, s.fn, s.w, s.color = t0, hide, fn, w, color

STROKES, FILLS, DOTS, DYNS = [], [], [], []
SCENE_ENDS, PINGS, POPS = [], [], []
RNG = np.random.default_rng(11)
INF = 1e9

def stroke(pts, t0, dur, w=5, color=INK, hide=INF, ease=True, amp=1.4):
    P = wobble(pts, amp, RNG)
    STROKES.append(Stroke(P, t0, dur, w, color, hide, ease))

def fill(poly, t0, dur, color, hide=INF):
    FILLS.append(Fill(poly, t0, dur, color, hide))

def dot(x, y, r, t0, color=INK, hide=INF):
    DOTS.append(Dot(x, y, r, t0, color, hide))

def seq(strokes, t0, t1, w, color, hide=INF):
    Ls = [max(1.0, float(np.sum(np.hypot(*np.diff(P, axis=0).T)))) for P in strokes]
    tot = sum(Ls); t = t0
    for P, L in zip(strokes, Ls):
        d = (t1 - t0) * L / tot
        STROKES.append(Stroke(P, t, d, w, color, hide, False)); t += d

def text_width(s, h):
    return sum(0.6 * h if c == ' ' else 0.887 * h for c in s) - 0.22 * h

def text(s, x, y, h, t0, t1, color=INK, align='l', hide=INF):
    sc = h / 6.0
    if align == 'c':
        x -= text_width(s, h) / 2
    cx = x; out = []
    step = max(3.0, min(7.0, h / 12))
    for c in s:
        if c == ' ':
            cx += 0.6 * h; continue
        for pts in FONT.get(c, []):
            P = chaikin(np.array(pts, float), 2 if c in ROUND else 0)
            X = cx + P[:, 0] * sc + (6 - P[:, 1]) * 0.1 * sc
            Y = y + P[:, 1] * sc
            out.append(wobble(np.stack([X, Y], 1), h * 0.012, RNG, step))
        cx += 0.887 * h
    seq(out, t0, t1, max(3.5, h * 0.075), color, hide)

def circle_pts(cx, cy, r, ry=None, over=0.3, a0=None):
    ry = ry or r
    a0 = RNG.uniform(0, 6.28) if a0 is None else a0
    n = int(2 * math.pi * max(r, ry) / 6) + 10
    th = np.linspace(a0, a0 + 2 * math.pi + over, n)
    p1, p2 = RNG.uniform(0, 6.28, 2)
    k = 1 + 0.012 * np.sin(2 * th + p1) + 0.01 * np.sin(3 * th + p2)
    grow = np.linspace(0, 1, n) ** 3 * (3 if over > 0 else 0)
    return np.stack([cx + (r * k + grow) * np.cos(th), cy + (ry * k + grow) * np.sin(th)], 1)

def circle(cx, cy, r, t0, dur, w=5, color=INK, ry=None, hide=INF):
    stroke(circle_pts(cx, cy, r, ry), t0, dur, w, color, hide, amp=1.2)

def blob(cx, cy, rx, ry, n=9, irr=0.3):
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    k = 1 - irr / 2 + irr * RNG.random(n)
    pts = np.stack([cx + rx * k * np.cos(th), cy + ry * k * np.sin(th)], 1)
    pts = np.vstack([pts, pts[:1], pts[1:2]])
    return chaikin(pts, 3)

def arc(cx, cy, R, a0, a1, n=40):
    th = np.radians(np.linspace(a0, a1, n))
    return np.stack([cx + R * np.cos(th), cy + R * np.sin(th)], 1)

def arrow_head(tip, frm, size=18):
    d = np.array(tip) - np.array(frm); d = d / (np.hypot(*d) + 1e-9)
    n = np.array([-d[1], d[0]])
    a = tip - d * size + n * size * 0.55
    b = tip - d * size - n * size * 0.55
    return np.array([a, tip, b])

def sparkle(x, y, s, t0, color=RED, w=4):
    stroke([(x, y - s), (x, y + s)], t0, 0.25, w, color, amp=0.3)
    stroke([(x - s, y), (x + s, y)], t0 + 0.12, 0.25, w, color, amp=0.3)
    d = s * 0.45
    stroke([(x - d, y - d), (x + d, y + d)], t0 + 0.2, 0.18, w - 1, color, amp=0.3)
    stroke([(x - d, y + d), (x + d, y - d)], t0 + 0.28, 0.18, w - 1, color, amp=0.3)
    PINGS.append(t0 + 0.1)

def wave_pts(x0, x1, y0, amp, lam, ph=0):
    x = np.arange(x0, x1 + 1, 5.0)
    return np.stack([x, y0 + amp * np.sin(2 * math.pi * (x - x0) / lam + ph)], 1)

# ---------------------------------------------------------- composite pieces
def moon(cx, cy, r, t0, dur, face, hide=INF, fill_at=None):
    circle(cx, cy, r, t0, dur, 6, hide=hide)
    fa = t0 + dur * 0.8 if fill_at is None else fill_at
    fill(circle_pts(cx, cy, r, over=0), fa, 0.5, YEL, hide)
    for (ox, oy, rr, dt) in [(0.50, -0.52, 0.17, 0.2), (-0.58, 0.38, 0.13, 0.3), (0.38, 0.62, 0.11, 0.4)]:
        circle(cx + ox * r, cy + oy * r, rr * r, t0 + dur * (0.7 + dt * 0.5), 0.25, 3.5, hide=hide)
    tf = t0 + dur + 0.05
    if face == 'smile':
        for ex in (-0.28, 0.28):
            dot(cx + ex * r, cy - 0.1 * r, 6, tf, hide=hide)
        stroke(arc(cx, cy + 0.02 * r, 0.42 * r, 35, 145, 20), tf, 0.3, 5, hide=hide, amp=0.6)
    elif face == 'shock':
        for ex in (-0.28, 0.28):
            circle(cx + ex * r, cy - 0.12 * r, 0.1 * r, tf, 0.2, 4, hide=hide)
            dot(cx + ex * r, cy - 0.12 * r, 4, tf + 0.2, hide=hide)
        circle(cx, cy + 0.38 * r, 0.1 * r, tf + 0.1, 0.25, 4, ry=0.15 * r, hide=hide)

def boat(bx, by, t0):
    stroke([(bx - 36, by), (bx + 36, by), (bx + 26, by + 18), (bx - 26, by + 18), (bx - 36, by)], t0, 0.25, 4, amp=0.6)
    stroke([(bx, by), (bx, by - 62)], t0 + 0.2, 0.15, 4, amp=0.4)
    sail = [(bx + 2, by - 60), (bx + 2, by - 8), (bx + 34, by - 8), (bx + 2, by - 60)]
    stroke(sail, t0 + 0.3, 0.2, 4, amp=0.4)
    fill(sail, t0 + 0.4, 0.4, RED)

_MARK = [0, 0, 0, 0]

def end_scene(E):
    """Hide everything created since the previous scene ended."""
    SCENE_ENDS.append(E)
    for k, lst in enumerate((STROKES, FILLS, DOTS, DYNS)):
        for it in lst[_MARK[k]:]:
            it.hide = min(it.hide, E)
        _MARK[k] = len(lst)

# =============================================================== the story
def build():
    # ---- S1: title (0 - 4.5)
    T = 0.0
    text("WHAT IF", 90, 110, 100, T + .15, T + 1.0, RED)
    text("THE MOON", 90, 270, 100, T + 1.0, T + 1.9)
    text("VANISHED?", 90, 430, 100, T + 1.9, T + 3.0)
    u = np.stack([np.linspace(90, 866, 40), 565 + 7 * np.sin(np.linspace(0, 14, 40))], 1)
    stroke(u, T + 3.0, 0.5, 6, RED, amp=0.8)
    moon(1040, 310, 130, T + .3, 0.9, 'smile', fill_at=T + 1.1)
    circle(1040, 610, 45, T + 2.4, 0.5, 5)
    fill(circle_pts(1040, 610, 45, over=0), T + 2.8, 0.4, BLUE)
    fill(blob(1030, 600, 18, 14), T + 3.0, 0.3, GREEN)
    sparkle(900, 190, 16, T + 2.0); sparkle(1180, 150, 12, T + 2.5)
    sparkle(1190, 420, 14, T + 3.0); sparkle(920, 470, 10, T + 3.4)
    end_scene(4.5)

    # ---- S2: poof (4.5 - 9.5)
    T = 4.5
    cx, cy = 640, 340
    moon(cx, cy, 170, T + .1, 0.7, 'shock', hide=T + 2.45, fill_at=T + 0.6)
    zz = []
    for i in range(11):
        y = cy - 150 + i * 30
        half = math.sqrt(max(0, 175 ** 2 - (y - cy) ** 2))
        zz += [(cx - half, y), (cx + half, y + 14)] if i % 2 == 0 else [(cx + half, y), (cx - half, y + 14)]
    stroke(zz, T + 1.6, 0.8, 7, INK, hide=T + 2.45, ease=False, amp=1.0)
    for i in range(14):
        a = 2 * math.pi * i / 14 + 0.2
        r0, r1 = 215, 285
        stroke([(cx + r0 * math.cos(a), cy + r0 * 0.75 * math.sin(a)),
                (cx + r1 * math.cos(a), cy + r1 * 0.75 * math.sin(a))],
               T + 2.45 + 0.02 * i, 0.2, 6, YEL if i % 2 else RED, hide=T + 3.7, amp=0.6)
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.5
        circle(cx + 130 * math.cos(a), cy + 100 * math.sin(a), 14 + 4 * (i % 3), T + 2.5 + .03 * i, 0.25, 3.5, hide=T + 3.7)
    text("POOF!", cx, 268, 140, T + 2.6, T + 3.5, RED, align='c')
    text("JUST LIKE THAT.", cx, 590, 42, T + 3.7, T + 4.4, align='c')
    POPS.append(T + 2.45)
    end_scene(9.5)

    # ---- S3: oceans (9.5 - 15.5)
    T = 9.5
    text("WHAT HAPPENS TO THE OCEANS?", 640, 30, 44, T + .1, T + 1.2, align='c')
    def rect(x0, y0, x1, y1, t0):
        stroke([(x0, y0), (x1, y0 + 2), (x1 - 2, y1), (x0 + 2, y1 - 2), (x0 - 1, y0 + 6)], t0, 0.5, 4, amp=1.5, ease=False)
    rect(70, 130, 610, 520, T + .9); rect(670, 130, 1210, 520, T + 1.0)
    text("BEFORE", 90, 148, 34, T + 1.4, T + 1.9, RED)
    text("AFTER", 690, 148, 34, T + 1.6, T + 2.1, RED)
    lw = wave_pts(85, 595, 390, 36, 150)
    stroke(lw, T + 1.9, 0.9, 5, INK, amp=0.8)
    fill(np.vstack([lw, [(595, 505), (85, 505)]]), T + 2.7, 0.5, BLUE)
    lb = float(390 + 36 * math.sin(2 * math.pi * (300 - 85) / 150))
    boat(300, lb - 16, T + 2.8)
    moon_x, moon_y = 520, 230
    circle(moon_x, moon_y, 42, T + 3.2, 0.4, 4.5)
    fill(circle_pts(moon_x, moon_y, 42, over=0), T + 3.5, 0.3, YEL)
    rw = wave_pts(685, 1195, 390, 7, 150)
    stroke(rw, T + 3.7, 0.7, 5, INK, amp=0.8)
    fill(np.vstack([rw, [(1195, 505), (685, 505)]]), T + 4.3, 0.4, BLUE)
    rb = float(390 + 7 * math.sin(2 * math.pi * (940 - 685) / 150))
    boat(940, rb - 16, T + 4.4)
    for i in range(10):  # dashed ghost-moon
        a0 = i * 36 + 4
        stroke(arc(1120, 230, 42, a0, a0 + 20, 8), T + 4.7 + 0.04 * i, 0.08, 4, INK, amp=0.2, ease=False)
    text("?", 1120, 212, 36, T + 5.1, T + 5.3, RED, align='c')
    text("TIDES SHRINK BY TWO THIRDS.", 640, 590, 40, T + 4.9, T + 5.7, align='c')
    end_scene(15.5)

    # ---- S4: wobble (15.5 - 21)
    T = 15.5
    C = (640, 350)
    text("THE EARTH STARTS TO WOBBLE", 640, 30, 44, T + .1, T + 1.1, align='c')
    circle(C[0], C[1], 150, T + 1.0, 0.9, 6)
    fill(circle_pts(C[0], C[1], 150, over=0), T + 1.8, 0.5, BLUE)
    for (ox, oy, rx, ry, dt) in [(-60, -40, 52, 40, 0), (55, 25, 45, 62, .25), (-25, 88, 34, 22, .5)]:
        b = blob(C[0] + ox, C[1] + oy, rx, ry)
        fill(b, T + 2.1 + dt, 0.35, GREEN)
        stroke(b, T + 2.1 + dt, 0.35, 3.5, amp=0.5)
    a0 = math.radians(23.5); dv = np.array([math.sin(a0), -math.cos(a0)])
    p_top = np.array(C) + 235 * dv; p_bot = np.array(C) - 235 * dv
    stroke([tuple(p_bot), tuple(p_top)], T + 2.7, 0.5, 6, RED, hide=T + 3.2, amp=0.3, ease=False)
    def axis_fn(t):
        k = min(1.0, max(0.0, (t - (T + 3.2)) / 1.6))
        ang = a0 + math.radians(30) * k * math.sin(2 * math.pi * (t - (T + 3.2)) / 2.4)
        d = np.array([math.sin(ang), -math.cos(ang)])
        top = np.array(C) + 235 * d; bot = np.array(C) - 235 * d
        return [("poly", np.array([bot, top])), ("poly", arrow_head(top, top - d * 30, 22))]
    DYNS.append(Dyn(T + 3.2, INF, axis_fn, 6, RED))
    arcp = arc(C[0], C[1], 250, -150, -30, 40)
    stroke(arcp, T + 3.6, 0.6, 4.5, INK, amp=0.8, ease=False)
    STROKES.append(Stroke(arrow_head(arcp[-1], arcp[-3], 18), T + 4.15, 0.12, 4.5, INK, INF, False))
    STROKES.append(Stroke(arrow_head(arcp[0], arcp[2], 18), T + 4.2, 0.12, 4.5, INK, INF, False))
    text("SEASONS GET WEIRD.", 640, 625, 40, T + 4.4, T + 5.2, align='c')
    end_scene(21.0)

    # ---- S5: owl (21 - 26)
    T = 21.0
    text("NIGHTS GET MUCH DARKER", 640, 30, 44, T + .1, T + .95, align='c')
    stroke([(230, 550), (500, 545), (800, 552)], T + .8, 0.4, 8, INK, amp=1.5, ease=False)
    ox, oy = 500, 390
    body = circle_pts(ox, oy, 105, ry=135, over=0)
    fill(body, T + 1.5, 0.4, BROWN)
    stroke(circle_pts(ox, oy, 105, ry=135), T + 1.1, 0.7, 6)
    for sgn in (-1, 1):
        ear = [(ox + sgn * 98, oy - 78), (ox + sgn * 105, oy - 150), (ox + sgn * 45, oy - 118)]
        fill(ear, T + 1.7, 0.2, BROWN)
        stroke(ear, T + 1.8, 0.25, 6, amp=0.6)
    for sgn in (-1, 1):
        ex = ox + sgn * 40
        fill(circle_pts(ex, oy - 70, 36, over=0), T + 2.1, 0.2, WHITE)
        circle(ex, oy - 70, 36, T + 2.1, 0.35, 5)
    beak = [(ox - 12, oy - 52), (ox + 12, oy - 52), (ox, oy - 22), (ox - 12, oy - 52)]
    fill(beak, T + 2.5, 0.2, RED)
    stroke(beak, T + 2.5, 0.25, 4.5, amp=0.4)
    for sgn in (-1, 1):  # wings
        w = [(ox + sgn * 98, oy - 20), (ox + sgn * 120, oy + 40), (ox + sgn * 90, oy + 105), (ox + sgn * 62, oy + 70)]
        stroke(chaikin(np.array(w), 2), T + 2.7, 0.3, 5, amp=0.8)
    for k, (fx, fy) in enumerate([(-40, 30), (0, 30), (40, 30), (-20, 70), (20, 70), (0, 108)]):
        stroke([(ox + fx - 12, oy + fy), (ox + fx, oy + fy + 12), (ox + fx + 12, oy + fy)], T + 2.95 + k * 0.05, 0.1, 3.5, amp=0.3)
    for sgn in (-1, 1):
        for j in (-1, 0, 1):
            stroke([(ox + sgn * 40 + j * 10, 520 + abs(j) * 2), (ox + sgn * 40 + j * 10, 548)], T + 3.2, 0.15, 5, amp=0.2)
    def pupil(sgn):
        def fn(t):
            q = t - (T + 3.3)
            return [("dot", ox + sgn * 40 + 15 * math.sin(1.9 * q), oy - 70 + 11 * math.cos(2.7 * q), 11)]
        return fn
    DYNS.append(Dyn(T + 2.3, INF, pupil(-1), 0, INK)); DYNS.append(Dyn(T + 2.3, INF, pupil(1), 0, INK))
    for k, (qx, qy, qh) in enumerate([(700, 230, 100), (800, 150, 80), (880, 300, 120)]):
        text("?", qx, qy, qh, T + 3.3 + k * 0.25, T + 3.5 + k * 0.25, RED, align='c')
        PINGS.append(T + 3.4 + k * 0.25)
    text("OWLS ARE CONFUSED.", 640, 625, 40, T + 3.9, T + 4.6, align='c')
    end_scene(26.0)

    # ---- S6: thanks (26 - 30)
    T = 26.0
    moon(640, 250, 130, T + .2, 0.8, 'smile', fill_at=T + .8)
    for (sx, sy, ss, dt) in [(450, 110, 16, 1.3), (850, 150, 12, 1.45), (500, 380, 12, 1.6), (830, 360, 16, 1.75), (400, 250, 10, 1.9)]:
        sparkle(sx, sy, ss, T + dt)
    text("THANK YOU, MOON.", 640, 440, 70, T + 1.4, T + 2.6, RED, align='c')
    text("KEEP LOOKING UP.", 640, 575, 38, T + 2.7, T + 3.4, align='c')
    end_scene(30.0)

# ================================================================ rendering
BASE = BASE_SMALL = None

def make_base():
    r = np.random.default_rng(3)
    n = r.normal(0, 3.2, (H * SS, W * SS)).astype(np.float32)
    n = np.asarray(Image.fromarray(np.clip(n * 8 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.3)), np.float32)
    n = (n - 128) / 8
    yy, xx = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32)
    vig = ((xx / (W * SS) - .5) ** 2 + (yy / (H * SS) - .5) ** 2) * 14
    arr = np.array(PAPER, np.float32)[None, None, :] + n[..., None] * 1.6 - vig[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)

def partial(st, u):
    if u >= 1:
        return st.P
    target = u * st.L
    i = int(np.searchsorted(st.cum, target))
    if i <= 0:
        return st.P[:1]
    seglen = st.cum[i] - st.cum[i - 1]
    f = (target - st.cum[i - 1]) / seglen if seglen > 0 else 1
    last = st.P[i - 1] + (st.P[i] - st.P[i - 1]) * f
    return np.vstack([st.P[:i], last])

def ink_line(d, pts, w, color, seed):
    if len(pts) < 2:
        return
    p = (pts + boil(pts, seed)) * SS
    xy = [tuple(q) for q in p]
    wi = max(2, int(round(w * SS)))
    d.line(xy, fill=color, width=wi, joint="curve")
    r = wi / 2
    for q in (xy[0], xy[-1]):
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=color)

def render(fi, t_override=None):
    t = fi / FPS if t_override is None else t_override
    seed = int(t * 8)
    img = BASE.copy(); d = ImageDraw.Draw(img)
    for f in FILLS:
        if t < f.t0 or t >= f.hide:
            continue
        a = smooth((t - f.t0) / f.dur)
        c = tuple(int(PAPER[i] * (1 - a * .92) + f.color[i] * a * .92) for i in range(3))
        poly = [tuple((q + np.array([5, 4])) * SS) for q in f.poly]
        d.polygon(poly, fill=c)
    for s in STROKES:
        if t < s.t0 or t >= s.hide:
            continue
        u = (t - s.t0) / s.dur
        u = smooth(u) if s.ease else min(1.0, u)
        ink_line(d, partial(s, u), s.w, s.color, seed)
    for o in DOTS:
        if t < o.t0 or t >= o.hide:
            continue
        x, y = (o.x + 0.8 * math.sin(seed * 2.1 + o.y)) * SS, (o.y + 0.8 * math.sin(seed * 1.7 + o.x)) * SS
        r = o.r * SS
        d.ellipse([x - r, y - r, x + r, y + r], fill=o.color)
    for dy in DYNS:
        if t < dy.t0 or t >= dy.hide:
            continue
        for sh in dy.fn(t):
            if sh[0] == "poly":
                ink_line(d, np.asarray(sh[1], float), dy.w, dy.color, seed)
            else:
                x, y, r = sh[1] * SS, sh[2] * SS, sh[3] * SS
                d.ellipse([x - r, y - r, x + r, y + r], fill=dy.color)
    out = img.reduce(SS)
    a = 1.0
    for E in SCENE_ENDS:
        if E - 0.35 < t <= E:
            a = (E - t) / 0.35
    if a < 1:
        out = Image.blend(BASE_SMALL, out, a)
    return out

def render_bytes(fi):
    return render(fi).tobytes()

# ==================================================================== audio
def make_audio(path):
    sr = 44100; n = sr * DUR
    t = np.arange(n) / sr
    r = np.random.default_rng(5)
    pad = np.zeros(n)
    for k, f in enumerate([110.0, 164.81, 220.0, 261.63, 329.63]):
        pad += np.sin(2 * np.pi * f * t + k) * (0.6 + 0.4 * np.sin(2 * np.pi * (0.07 + .02 * k) * t + k))
    env = np.minimum(1, t / 2.0) * np.minimum(1, (DUR - t) / 2.0)
    pad *= env * 0.018
    act = np.zeros(n)
    for s in STROKES:
        act[int(s.t0 * sr):min(n, int((s.t0 + s.dur) * sr))] = 1.0
    k = np.hanning(int(0.05 * sr)); act = np.convolve(act, k / k.sum(), 'same')
    nz = np.diff(r.normal(size=n + 1))
    nz = np.convolve(nz, np.ones(3) / 3, 'same')
    flutter = 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t + np.cumsum(r.normal(0, .02, n)))
    scratch = nz * act * flutter * 0.05
    sfx = np.zeros(n)
    for tp in POPS:
        i = int(tp * sr); m = int(0.5 * sr); tt = np.arange(m) / sr
        f = 900 * np.exp(-tt * 14) + 120
        sfx[i:i + m] += np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 12) * 0.5
        sfx[i:i + m] += r.normal(size=m) * np.exp(-tt * 7) * 0.12
    notes = [1318.5, 1568.0, 1760.0, 2093.0, 1975.5]
    for j, tp in enumerate(sorted(PINGS)):
        i = int(tp * sr); m = int(0.7 * sr)
        if i + m > n:
            continue
        tt = np.arange(m) / sr
        sfx[i:i + m] += np.sin(2 * np.pi * notes[j % 5] * tt) * np.exp(-tt * 6) * 0.07
    mix = pad + scratch + sfx
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.8
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((mix * 32767).astype('<i2').tobytes())

# ====================================================================== main
def init():
    global BASE, BASE_SMALL
    BASE = make_base(); BASE_SMALL = BASE.reduce(SS)

if __name__ == "__main__":
    build(); init()
    if len(sys.argv) > 2 and sys.argv[2] == "--stills":
        os.makedirs(sys.argv[3], exist_ok=True)
        for ts in sys.argv[4:]:
            render(0, float(ts)).save(os.path.join(sys.argv[3], f"t{float(ts):05.2f}.png"))
        sys.exit()
    out = sys.argv[1]
    wav = out + ".wav"
    make_audio(wav)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
                          stdin=subprocess.PIPE)
    with Pool(4) as p:
        for i, b in enumerate(p.imap(render_bytes, range(FPS * DUR), chunksize=4)):
            ff.stdin.write(b)
            if i % 120 == 0:
                print("frame", i, flush=True)
    ff.stdin.close(); ff.wait(); os.remove(wav)
    print("done", out)
