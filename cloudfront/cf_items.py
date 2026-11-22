"""Custom items for the CloudFront film: a dotted 3D globe with great-circle arcs, glassy devices
(phone, cache racks, origin tower), file and request movers, clean numbers. All drawn with Skia,
all timed from the voiceover by the scene. One style: deep navy, cyan = requests, orange = files.
"""
import math
import pathlib

import numpy as np
import skia
from PIL import Image

from engine import Item, Spline, clamp, color, draw_text, ease_in_out, ease_out_back, ease_out_cubic, paint, partial_path, ramp, text_width

HERE = pathlib.Path(__file__).parent

CYAN = (70, 214, 255)
ORANGE = (255, 156, 52)
GREEN = (72, 226, 142)
RED = (255, 88, 96)
WHITE = (238, 244, 255)
DIM = (128, 150, 196)
LAND = (92, 130, 205)
BODY_TOP = (44, 58, 96)
BODY_BOT = (16, 22, 42)
EDGE = (118, 148, 210)


# ------------------------------------------------------------------ small drawing helpers
def lin(x0, y0, x1, y1, c0, c1, a0=1.0, a1=1.0):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [color(c0, a0), color(c1, a1)], [0, 1])


def glow(c, x, y, r, rgb, a):
    """Soft light: a wide blurred disc plus a tighter hot core."""
    if a <= 0.01:
        return
    c.drawCircle(x, y, r * 2.4, paint(rgb, 0.22 * a, blur=r * 1.2))
    c.drawCircle(x, y, r, paint(rgb, 0.95 * a))
    c.drawCircle(x, y, r * 0.45, paint((255, 255, 255), 0.9 * a))


def pool(c, x, y, r, rgb, a):
    """A soft pool of light on the floor under a device: fills the dark and seats the object in the scene."""
    if a <= 0.005:
        return
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [color(rgb, a), color(rgb, 0.0)], [0, 1]))
    c.drawCircle(x, y, r, p)


def body(c, x, y, w, h, r, a, top=BODY_TOP, bot=BODY_BOT, edge=EDGE, shadow=True, halo=None, halo_a=0.0):
    rect = skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)
    rr = skia.RRect.MakeRectXY(rect, r, r)
    if halo is not None and halo_a > 0:
        c.drawRRect(rr, paint(halo, 0.55 * halo_a, stroke=26, blur=34))
    if shadow:
        c.save(); c.translate(0, h * 0.04)
        c.drawRRect(rr, paint((0, 0, 0), 0.5 * a, blur=h * 0.06)); c.restore()
    p = skia.Paint(AntiAlias=True); p.setShader(lin(x, y - h / 2, x, y + h / 2, top, bot, a, a)); c.drawRRect(rr, p)
    c.drawRRect(rr, paint(edge, 0.55 * a, stroke=max(3, w * 0.006)))
    # top sheen
    c.save(); c.clipRRect(rr, skia.ClipOp.kIntersect, True)
    p2 = skia.Paint(AntiAlias=True); p2.setShader(lin(x, y - h / 2, x, y - h / 2 + h * 0.22, (255, 255, 255), (255, 255, 255), 0.10 * a, 0.0))
    c.drawRect(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h * 0.22), p2)
    c.restore()
    return rr


def file_icon(c, x, y, s, a, rgb=ORANGE, play=True):
    """A video file: rounded sheet, folded corner, play triangle. s = width."""
    w, h = s, s * 1.22
    fold = w * 0.3
    path = skia.Path()
    path.moveTo(x - w / 2, y - h / 2 + w * 0.12)
    path.quadTo(x - w / 2, y - h / 2, x - w / 2 + w * 0.12, y - h / 2)
    path.lineTo(x + w / 2 - fold, y - h / 2); path.lineTo(x + w / 2, y - h / 2 + fold)
    path.lineTo(x + w / 2, y + h / 2 - w * 0.12)
    path.quadTo(x + w / 2, y + h / 2, x + w / 2 - w * 0.12, y + h / 2)
    path.lineTo(x - w / 2 + w * 0.12, y + h / 2)
    path.quadTo(x - w / 2, y + h / 2, x - w / 2, y + h / 2 - w * 0.12)
    path.close()
    c.drawPath(path, paint(rgb, 0.28 * a, blur=s * 0.25))
    p = skia.Paint(AntiAlias=True)
    hi = tuple(min(255, int(v * 1.18 + 20)) for v in rgb); lo = tuple(int(v * 0.72) for v in rgb)
    p.setShader(lin(x, y - h / 2, x, y + h / 2, hi, lo, a, a)); c.drawPath(path, p)
    f = skia.Path(); f.moveTo(x + w / 2 - fold, y - h / 2); f.lineTo(x + w / 2 - fold, y - h / 2 + fold); f.lineTo(x + w / 2, y - h / 2 + fold); f.close()
    c.drawPath(f, paint((255, 255, 255), 0.45 * a))
    if play:
        t = skia.Path(); t.moveTo(x - w * 0.12, y - w * 0.2); t.lineTo(x - w * 0.12, y + w * 0.3); t.lineTo(x + w * 0.22, y + w * 0.05); t.close()
        c.drawPath(t, paint((255, 255, 255), 0.95 * a))


def quad_pt(p0, p1, bend, u):
    (x0, y0), (x1, y1) = p0, p1
    d = math.hypot(x1 - x0, y1 - y0) or 1
    nx, ny = -(y1 - y0) / d, (x1 - x0) / d
    cx, cy = (x0 + x1) / 2 + nx * d * bend, (y0 + y1) / 2 + ny * d * bend
    return ((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1)


def quad_path(p0, p1, bend, u0=0.0, u1=1.0, n=40):
    path = skia.Path()
    for i in range(n + 1):
        u = u0 + (u1 - u0) * i / n
        x, y = quad_pt(p0, p1, bend, u)
        path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
    return path


# ------------------------------------------------------------------ the globe
def ll_unit(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


def great_circle(a, b, n, lift):
    """n+1 points along the great circle a->b (unit vectors) with the radius lifted by sin(pi s)."""
    A, B = ll_unit(*a), ll_unit(*b)
    om = math.acos(float(np.clip(A @ B, -1, 1)))
    s = np.linspace(0, 1, n + 1)
    pts = (np.sin((1 - s) * om)[:, None] * A + np.sin(s * om)[:, None] * B) / math.sin(om)
    return pts * (1 + lift * np.sin(math.pi * s))[:, None], om


def midpoint(a, b):
    A, B = ll_unit(*a), ll_unit(*b)
    m = A + B; m /= np.linalg.norm(m)
    return math.degrees(math.asin(m[2])), math.degrees(math.atan2(m[1], m[0]))


class Globe(Item):
    """Dotted globe. View keys rotate it; arcs, pulses, city dots and a swarm of locations are timed by the scene."""
    z = 10

    def __init__(self, cx, cy, R, view_keys, t_in=0.0, n_dots=16000):
        super().__init__(t_in, None, None, True)
        self.cx, self.cy, self.R = cx, cy, R
        self.vl = Spline([(t, la) for t, la, lo in view_keys]); self.vo = Spline([(t, lo) for t, la, lo in view_keys])
        self.arcs, self.dots, self.swarm, self._cue = [], [], None, []
        # land dots on latitude rings (no spiral moire), sampled against the land mask
        step = 1.45
        lats, lons = [], []
        for la in np.arange(-88, 88.01, step):
            nlon = max(1, int(round(360 * math.cos(math.radians(la)) / step)))
            ln = (np.arange(nlon) + 0.5) * 360 / nlon - 180 + (step * 0.5 if int((la + 90) / step) % 2 else 0)
            lats.append(np.full(nlon, la)); lons.append(((ln + 180) % 360) - 180)
        lat = np.concatenate(lats); lon = np.concatenate(lons)
        mask = np.asarray(Image.open(HERE / "assets/prep/land_mask.png"))
        h, w = mask.shape
        px = ((lon + 180) / 360 * w).astype(int).clip(0, w - 1); py = ((90 - lat) / 180 * h).astype(int).clip(0, h - 1)
        keep = mask[py, px] > 127
        self.land_ll = np.stack([lat[keep], lon[keep]], -1)
        self.land_u = ll_unit(self.land_ll[:, 0], self.land_ll[:, 1])
        self.grat = []
        for la in range(-60, 61, 30):
            self.grat.append(ll_unit(np.full(90, la), np.linspace(-180, 180, 90)))
        for lo in range(-180, 180, 30):
            self.grat.append(ll_unit(np.linspace(-85, 85, 70), np.full(70, lo)))

    # ---- scene API
    def arc(self, a, b, t0, dur, rgb=CYAN, width=14, lift=0.22, t_out=None, pulses=(), glow_a=1.0, fade=0.5, dashed=False, gain=0.4):
        pts, om = great_circle(a, b, 140, lift)
        self.arcs.append(dict(pts=pts, t0=t0, dur=dur, rgb=rgb, w=width, t_out=t_out, pulses=list(pulses), ga=glow_a, fade=fade, dashed=dashed))
        self._cue.append(("whoosh", t0, gain, {}))
        return len(self.arcs) - 1

    def dot(self, ll, t_in, rgb=CYAN, r=26, label=None, ping=True, t_out=None, label_dx=0.0, label_dy=-1.0, lsize=96, shimmer=False):
        self.dots.append(dict(ll=ll, u=ll_unit(*ll), t=t_in, rgb=rgb, r=r, label=label, ping=ping, t_out=t_out, dx=label_dx, dy=label_dy, ls=lsize))
        if shimmer:
            self._cue.append(("shimmer", t_in, 0.35, {}))
        return len(self.dots) - 1

    def set_swarm(self, lls, times, rgb=ORANGE, size=15):
        self.swarm = dict(u=ll_unit(lls[:, 0], lls[:, 1]), t=np.asarray(times), rgb=rgb, s=size)
        self._cue.append(("shimmer", float(np.min(times)), 0.5, {}))

    def cues(self):
        return list(self._cue)

    def bounds(self, res):
        r = self.R * 1.6
        return skia.Rect.MakeLTRB(self.cx - r, self.cy - r, self.cx + r, self.cy + r)

    # ---- projection
    def view(self, t):
        return math.radians(float(self.vl(t))), math.radians(float(self.vo(t)))

    def project(self, U, t, radius=1.0):
        la0, lo0 = self.view(t)
        X, Y, Z = U[..., 0], U[..., 1], U[..., 2]
        c0, s0 = math.cos(lo0), math.sin(lo0)
        X1 = X * c0 + Y * s0; Y1 = -X * s0 + Y * c0
        cp, sp = math.cos(la0), math.sin(la0)
        depth = X1 * cp + Z * sp; up = -X1 * sp + Z * cp
        r = self.R * radius
        return self.cx + Y1 * r, self.cy - up * r, depth

    def to_screen(self, ll, t):
        x, y, d = self.project(ll_unit(*ll)[None, :], t)
        return float(x[0]), float(y[0]), float(d[0])

    # ---- drawing
    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.8)
        if a <= 0:
            return
        cx, cy, R = self.cx, self.cy, self.R
        # atmosphere + body
        c.drawCircle(cx, cy, R * 1.25, paint((40, 90, 220), 0.20 * a, blur=R * 0.28))
        c.drawCircle(cx, cy, R * 1.08, paint(CYAN, 0.10 * a, blur=R * 0.10))
        c.drawCircle(cx, cy, R * 1.015, paint(CYAN, 0.30 * a, stroke=R * 0.022, blur=R * 0.03))
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(cx - R * 0.35, cy - R * 0.4), R * 1.5,
                                                   [color((30, 46, 92), a), color((10, 16, 38), a), color((4, 7, 18), a)], [0, 0.55, 1]))
        c.drawCircle(cx, cy, R, p)
        c.drawArc(skia.Rect.MakeXYWH(cx - R, cy - R, 2 * R, 2 * R), 180, 95, False, paint((150, 225, 255), 0.55 * a, stroke=R * 0.012, blur=R * 0.012))
        # graticule
        gp = paint(EDGE, 0.13 * a, stroke=R * 0.0016)
        for g in self.grat:
            x, y, d = self.project(g, t)
            path = skia.Path(); pen = False
            for xi, yi, di in zip(x, y, d):
                if di > 0:
                    path.lineTo(xi, yi) if pen else path.moveTo(xi, yi); pen = True
                else:
                    pen = False
            c.drawPath(path, gp)
        # land dots, three depth bands for a limb falloff
        x, y, d = self.project(self.land_u, t)
        ds = R * 0.0088
        for lo, hi, al, sc in ((0.0, 0.22, 0.22, 0.6), (0.22, 0.55, 0.42, 0.85), (0.55, 1.01, 0.66, 1.0)):
            m = (d > lo) & (d <= hi)
            if m.any():
                pts = [skia.Point(float(xi), float(yi)) for xi, yi in zip(x[m], y[m])]
                c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint(LAND, al * a, stroke=ds * 2 * sc))
        # swarm of locations
        if self.swarm is not None:
            sw = self.swarm
            x, y, d = self.project(sw["u"], t)
            age = t - sw["t"]
            on = (age > 0) & (d > 0.05)
            if on.any():
                old = on & (age > 0.5); new = on & (age <= 0.5)
                if old.any():
                    pts = [skia.Point(float(xi), float(yi)) for xi, yi in zip(x[old], y[old])]
                    c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint(sw["rgb"], 0.95 * a, stroke=sw["s"] * 2))
                for xi, yi, ai in zip(x[new], y[new], age[new]):
                    k = 1 - ai / 0.5
                    c.drawCircle(float(xi), float(yi), sw["s"] * (1 + 3.2 * k), paint(sw["rgb"], 0.5 * k * a, blur=10))
                    c.drawCircle(float(xi), float(yi), sw["s"], paint(sw["rgb"], 0.95 * a))
        # arcs
        for ar in self.arcs:
            self._draw_arc(c, ar, t, a)
        # city dots
        for dt in self.dots:
            if t < dt["t"] - 0.01 or (dt["t_out"] is not None and t > dt["t_out"] + 0.5):
                continue
            x, y, d = self.project(dt["u"][None, :], t)
            x, y, d = float(x[0]), float(y[0]), float(d[0])
            if d < 0.04:
                continue
            fa = ramp(t, dt["t"], 0.35) * (1 - (ramp(t, dt["t_out"], 0.5) if dt["t_out"] is not None else 0)) * a
            pop = ease_out_back(ramp(t, dt["t"], 0.45), 1.8)
            r = dt["r"] * pop * (0.6 + 0.4 * d)
            glow(c, x, y, r, dt["rgb"], fa)
            if dt["ping"]:
                ph = ((t - dt["t"]) % 2.4) / 2.4
                c.drawCircle(x, y, r * (1.5 + 5 * ph), paint(dt["rgb"], 0.5 * (1 - ph) * fa, stroke=r * 0.22))
            if dt["label"]:
                la = ramp(t, dt["t"] + 0.15, 0.4) * fa
                draw_text(c, res, dt["label"], x + dt["dx"] * r * 3.2, y + dt["dy"] * r * 3.4, dt["ls"], "cond", WHITE, la, 0.08, "center")

    def _draw_arc(self, c, ar, t, a):
        if t < ar["t0"] - 0.01:
            return
        fade = 1.0 if ar["t_out"] is None else 1 - ramp(t, ar["t_out"], ar["fade"])
        if fade <= 0:
            return
        u = ease_in_out(ramp(t, ar["t0"], ar["dur"]))
        n = len(ar["pts"]) - 1
        k = max(2, int(u * n) + 1)
        x, y, d = self.project(ar["pts"][:k + 1], t)
        vis = (d > -0.02) | (np.hypot(x - self.cx, y - self.cy) > self.R * 1.001)
        path = skia.Path(); pen = False
        for xi, yi, vi in zip(x, y, vis):
            if vi:
                path.lineTo(float(xi), float(yi)) if pen else path.moveTo(float(xi), float(yi)); pen = True
            else:
                pen = False
        w = ar["w"]
        g = paint(ar["rgb"], 0.45 * ar["ga"] * fade * a, stroke=w * 3.2, blur=w * 1.6)
        core = paint(ar["rgb"], 0.95 * fade * a, stroke=w)
        if ar["dashed"]:
            for p in (g, core):
                p.setPathEffect(skia.DashPathEffect.Make([w * 2.2, w * 2.2], (t * 60) % (w * 4.4)))
        c.drawPath(path, g); c.drawPath(path, core)
        c.drawPath(path, paint((255, 255, 255), 0.7 * fade * a, stroke=max(2, w * 0.3)))
        # pulses: (t0, t1, direction)
        for (pa, pb, dr) in ar["pulses"]:
            if t < pa or t > pb + 0.2:
                continue
            pu = ease_in_out(ramp(t, pa, pb - pa))
            if dr < 0:
                pu = 1 - pu
            idx = pu * n
            for j in range(7, -1, -1):             # comet tail
                ii = idx - j * 1.6 * (1 if dr > 0 else -1)
                if ii < 0 or ii > n:
                    continue
                i0 = int(ii)
                xx, yy, dd = self.project(ar["pts"][i0:i0 + 1], t)
                if dd[0] < -0.02 and math.hypot(xx[0] - self.cx, yy[0] - self.cy) < self.R:
                    continue
                al = (1 - j / 8) ** 2 * (1 - ramp(t, pb, 0.2))
                glow(c, float(xx[0]), float(yy[0]), w * (0.9 + 1.4 * (1 - j / 8)), ar["rgb"] if j else (255, 255, 255), al * fade * a)


# ------------------------------------------------------------------ text + numbers (clean, no distress)
class Text(Item):
    z = 70

    def __init__(self, text, x, y, size, t_in, t_out=None, rgb=WHITE, align="center", track=0.06, type_on=0.0, glow_a=0.0, sfx_kind=None, gain=0.5):
        super().__init__(t_in, t_out, None, True)
        self.text, self.x, self.y, self.size, self.rgb, self.align, self.track = text, x, y, size, rgb, align, track
        self.type_on, self.glow_a, self.kind, self.gain = type_on, glow_a, sfx_kind, gain

    def cues(self):
        return [(self.kind, self.t_in, self.gain, {})] if self.kind else []

    def bounds(self, res):
        r = max(len(self.text) * self.size * 0.5, self.size * 2) + 600
        return skia.Rect.MakeLTRB(self.x - r, self.y - self.size * 2, self.x + r, self.y + self.size)

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.4) * self.fade(t)
        if a <= 0:
            return
        rev = len(self.text) * ramp(t, self.t_in, self.type_on) + 0.999 if self.type_on > 0 else None
        drift = 1 - ease_out_cubic(ramp(t, self.t_in, 1.0))
        tr = self.track + 0.05 * drift
        yy = self.y + 40 * drift
        if self.glow_a:
            c.saveLayerAlpha(None, 255)
            draw_text(c, res, self.text, self.x, yy, self.size, "cond", self.rgb, 0.5 * a * self.glow_a, tr, self.align, rev)
            c.restore()
        c.save(); c.translate(0, self.size * 0.04)
        draw_text(c, res, self.text, self.x, yy, self.size, "cond", (0, 0, 0), 0.6 * a, tr, self.align, rev)
        c.restore()
        draw_text(c, res, self.text, self.x, yy, self.size, "cond", self.rgb, a, tr, self.align, rev)


class Num(Item):
    """A number rolling from start to value, clean type with a soft glow and an optional caption."""
    z = 70

    def __init__(self, x, y, size, value, t_in, dur=1.2, start=0, prefix="", suffix="", caption=None, rgb=WHITE, t_out=None, cap_rgb=DIM):
        super().__init__(t_in, t_out, None, True)
        self.x, self.y, self.size, self.value, self.dur, self.start = x, y, size, value, dur, start
        self.prefix, self.suffix, self.caption, self.rgb, self.cap_rgb = prefix, suffix, caption, rgb, cap_rgb

    def cues(self):
        return [("ticks", self.t_in, 0.5, {})]

    def bounds(self, res):
        r = self.size * 5
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.3) * self.fade(t)
        if a <= 0:
            return
        u = ease_out_cubic(ramp(t, self.t_in, self.dur))
        v = int(round(self.start + (self.value - self.start) * u))
        txt = f"{self.prefix}{v:,}{self.suffix}"
        draw_text(c, res, txt, self.x, self.y, self.size, "cond", self.rgb, 0.4 * a, 0.03, "center")
        c.save(); c.translate(0, self.size * 0.035)
        draw_text(c, res, txt, self.x, self.y, self.size, "cond", (0, 0, 0), 0.55 * a, 0.03, "center"); c.restore()
        draw_text(c, res, txt, self.x, self.y, self.size, "cond", self.rgb, a, 0.03, "center")
        if self.caption:
            ca = ramp(t, self.t_in + self.dur * 0.5, 0.4) * self.fade(t)
            draw_text(c, res, self.caption, self.x, self.y + self.size * 0.36, self.size * 0.2, "cond", self.cap_rgb, 0.95 * ca, 0.22, "center")


class Verdict(Item):
    """HIT / MISS badge: pops in with a glow ring."""
    z = 72

    def __init__(self, text, x, y, t_in, rgb=GREEN, size=330, t_out=None, rot=-4.0):
        super().__init__(t_in, t_out, None, True)
        self.text, self.x, self.y, self.rgb, self.size, self.rot = text, x, y, rgb, size, rot

    def cues(self):
        return [("stamp", self.t_in, 0.7, {})]

    def bounds(self, res):
        r = self.size * 3
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def draw(self, c, res, t):
        u = ease_out_back(ramp(t, self.t_in, 0.35), 2.2); a = ramp(t, self.t_in, 0.1) * self.fade(t)
        if a <= 0:
            return
        tw = text_width(res, self.text, self.size, "cond", 0.08)
        w, h = tw + self.size * 0.7, self.size * 1.05
        c.save(); c.translate(self.x, self.y); c.rotate(self.rot); c.scale(0.7 + 0.3 * u, 0.7 + 0.3 * u)
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), h * 0.2, h * 0.2)
        c.drawRRect(rr, paint(self.rgb, 0.5 * a, stroke=26, blur=30))
        c.drawRRect(rr, paint((6, 10, 24), 0.82 * a))
        c.drawRRect(rr, paint(self.rgb, a, stroke=self.size * 0.045))
        draw_text(c, res, self.text, 0, self.size * 0.36, self.size, "cond", self.rgb, a, 0.08, "center")
        ring = ramp(t, self.t_in, 0.6)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 - 80 * ring, -h / 2 - 80 * ring, w + 160 * ring, h + 160 * ring), h * 0.3, h * 0.3),
                    paint(self.rgb, 0.5 * (1 - ring) * a, stroke=10))
        c.restore()


# ------------------------------------------------------------------ devices
class Phone(Item):
    """A phone. modes = [(t, "idle"|"loading"|"playing")]."""
    z = 20

    def __init__(self, x, y, t_in, modes=(), label=None, s=1.0, rot=0.0):
        super().__init__(t_in, None, None, True)
        self.x, self.y, self.t_in, self.modes, self.label, self.s, self.rot = x, y, t_in, sorted(modes), label, s, rot
        self.w, self.h = 600 * s, 1100 * s

    def cues(self):
        return [("pop", self.t_in, 0.5, {})]

    def mode(self, t):
        m = ("idle", self.t_in)
        for tt, md in self.modes:
            if t >= tt:
                m = (md, tt)
        return m

    def bounds(self, res):
        r = self.h * 0.9
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.3)
        if a <= 0:
            return
        u = ease_out_back(ramp(t, self.t_in, 0.5), 1.3)
        md, t0 = self.mode(t)
        pool(c, self.x, self.y, self.h * 1.0, GREEN if md == 'playing' else (60, 110, 240), 0.16 * a)
        c.save(); c.translate(self.x, self.y + (1 - u) * 80); c.rotate(self.rot); c.scale(0.9 + 0.1 * u, 0.9 + 0.1 * u)
        halo = CYAN if md == "loading" else GREEN if md == "playing" else None
        body(c, 0, 0, self.w, self.h, self.w * 0.17, a, halo=halo, halo_a=0.6 * a)
        sw, sh = self.w * 0.86, self.h * 0.9
        scr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-sw / 2, -sh / 2, sw, sh), self.w * 0.12, self.w * 0.12)
        p = skia.Paint(AntiAlias=True); p.setShader(lin(0, -sh / 2, 0, sh / 2, (14, 22, 48), (6, 10, 24), a, a)); c.drawRRect(scr, p)
        c.save(); c.clipRRect(scr, skia.ClipOp.kIntersect, True)
        if md == "playing":
            k = ramp(t, t0, 0.5); ph = (t - t0) * 0.35
            p = skia.Paint(AntiAlias=True)
            p.setShader(lin(-sw / 2, -sh / 2, sw / 2, sh / 2, (255, 150 + int(40 * math.sin(ph)), 60), (60, 90 + int(50 * math.sin(ph + 1)), 220), a * k, a * k))
            c.drawRect(skia.Rect.MakeXYWH(-sw / 2, -sh / 2, sw, sh * 0.76), p)
            tri = skia.Path(); tri.moveTo(-sw * 0.1, -sh * 0.2); tri.lineTo(-sw * 0.1, sh * 0.05); tri.lineTo(sw * 0.12, -sh * 0.075); tri.close()
            c.drawPath(tri, paint((255, 255, 255), 0.85 * a * k))
            c.drawRect(skia.Rect.MakeXYWH(-sw * 0.4, sh * 0.34, sw * 0.8, sh * 0.02), paint((255, 255, 255), 0.25 * a))
            c.drawRect(skia.Rect.MakeXYWH(-sw * 0.4, sh * 0.34, sw * 0.8 * clamp(0.03 + (t - t0) * 0.12), sh * 0.02), paint(RED, a))
        else:
            tri = skia.Path(); tri.moveTo(-sw * 0.1, -sh * 0.12); tri.lineTo(-sw * 0.1, sh * 0.1); tri.lineTo(sw * 0.13, -sh * 0.01); tri.close()
            c.drawPath(tri, paint((255, 255, 255), 0.55 * a))
            if md == "loading":
                ang = (t - t0) * 360 * 1.3
                c.drawArc(skia.Rect.MakeXYWH(-sw * 0.28, -sh * 0.28 + sh * 0.0, sw * 0.56, sw * 0.56), ang, 250, False, paint(CYAN, a, stroke=sw * 0.045))
            c.drawRect(skia.Rect.MakeXYWH(-sw * 0.4, sh * 0.34, sw * 0.8, sh * 0.02), paint((255, 255, 255), 0.18 * a))
        c.restore()
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-self.w * 0.12, -self.h / 2 + self.h * 0.012, self.w * 0.24, self.h * 0.014), 6, 6), paint((0, 0, 0), 0.7 * a))
        if self.label:
            draw_text(c, res, self.label, 0, self.h / 2 + 150 * self.s, 110 * self.s, "cond", DIM, a * 0.95, 0.2, "center")
        c.restore()


class Rack(Item):
    """A cache: a body with bays. contents = [(bay, t_in, t_out)], flashes = [(bay, t0, t1, rgb)], halos = [(t0, t1, rgb)]."""
    z = 20

    def __init__(self, x, y, w, h, bays, t_in, label, contents=(), flashes=(), halos=(), cols=1, dim_until=None, origin=False, label_size=120, dim=0.0):
        super().__init__(t_in, None, None, True)
        self.x, self.y, self.w, self.h, self.bays, self.cols, self.label = x, y, w, h, bays, cols, label
        self.contents, self.flashes, self.halos, self.origin, self.ls, self.dim = list(contents), list(flashes), list(halos), origin, label_size, dim

    def cues(self):
        return [("pop", self.t_in, 0.5, {})]

    def bay_rect(self, i):
        rows = math.ceil(self.bays / self.cols)
        pad = self.w * 0.07; top = self.h * 0.16
        bw = (self.w - pad * 2 - (self.cols - 1) * pad * 0.5) / self.cols
        bh = (self.h - top - pad) / rows - pad * 0.45
        col, row = i % self.cols, i // self.cols
        bx = self.x - self.w / 2 + pad + col * (bw + pad * 0.5)
        by = self.y - self.h / 2 + top + row * (bh + pad * 0.45)
        return bx, by, bw, bh

    def bay_center(self, i):
        bx, by, bw, bh = self.bay_rect(i)
        return bx + bw / 2, by + bh / 2

    def bounds(self, res):
        r = max(self.w, self.h) * 0.9
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.4)
        if a <= 0:
            return
        u = ease_out_back(ramp(t, self.t_in, 0.5), 1.2)
        ha = 0.0; hc = CYAN
        for (t0, t1, rgb) in self.halos:
            k = ramp(t, t0, 0.3) * (1 - ramp(t, t1, 0.4))
            if k > ha:
                ha, hc = k, rgb
        if self.origin:
            ha, hc = max(ha, 0.55 + 0.1 * math.sin(t * 2.0)), ORANGE
        da = a * (1 - self.dim)
        pool(c, self.x, self.y, max(self.w, self.h) * 1.25, ORANGE if self.origin else (60, 110, 240), 0.16 * da)
        c.save(); c.translate(self.x, self.y + (1 - u) * 90); c.scale(0.92 + 0.08 * u, 0.92 + 0.08 * u); c.translate(-self.x, -self.y)
        body(c, self.x, self.y, self.w, self.h, self.w * 0.07, da, halo=hc, halo_a=ha * da,
             top=(46, 60, 100) if not self.origin else (70, 52, 44), bot=BODY_BOT if not self.origin else (26, 18, 18))
        # header bar with status lights
        hh = self.h * 0.09
        c.drawRect(skia.Rect.MakeXYWH(self.x - self.w / 2 + self.w * 0.07, self.y - self.h / 2 + self.h * 0.045, self.w * 0.18, hh * 0.35), paint(hc if self.origin else CYAN, 0.9 * da))
        for k in range(3):
            c.drawCircle(self.x + self.w / 2 - self.w * 0.09 - k * self.w * 0.055, self.y - self.h / 2 + self.h * 0.045 + hh * 0.17, self.w * 0.014, paint(GREEN if k < 2 else DIM, 0.9 * da))
        for i in range(self.bays):
            bx, by, bw, bh = self.bay_rect(i)
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, by, bw, bh), bh * 0.16, bh * 0.16)
            c.drawRRect(rr, paint((4, 8, 20), 0.9 * da))
            edge, ea = (hc, 0.35) if self.origin else (EDGE, 0.28)
            for (b, t0, t1, rgb) in self.flashes:
                if b == i and t0 <= t <= t1 + 0.4:
                    k = (0.5 + 0.5 * math.sin((t - t0) * 9)) * (1 - ramp(t, t1, 0.4)) * ramp(t, t0, 0.15)
                    edge, ea = rgb, 0.4 + 0.6 * k
                    c.drawRRect(rr, paint(rgb, 0.35 * k * da, stroke=14, blur=16))
            c.drawRRect(rr, paint(edge, ea * da, stroke=max(3, self.w * 0.005)))
            c.drawCircle(bx + bw - bh * 0.28, by + bh / 2, bh * 0.08, paint(GREEN if i % 3 else CYAN, 0.8 * da))
            have = self.origin
            sc = 1.0
            for (b, ti, to) in self.contents:
                if b == i and t >= ti and (to is None or t < to):
                    have = True; sc = ease_out_back(ramp(t, ti, 0.4), 2.0)
                    if to is None and ramp(t, ti, 0.9) < 1:
                        c.drawCircle(bx + bw / 2, by + bh / 2, bh * (0.9 - 0.4 * ramp(t, ti, 0.9)), paint(ORANGE, 0.5 * (1 - ramp(t, ti, 0.9)) * da, stroke=8))
            if have and sc > 0:
                file_icon(c, bx + bw / 2, by + bh / 2, bh * 0.62 * sc, da, play=bh > 140)
        draw_text(c, res, self.label, self.x, self.y + self.h / 2 + self.ls * 1.35, self.ls, "cond", (176, 198, 245) if not self.origin else (255, 200, 140), da * 0.98, 0.2, "center")
        c.restore()


class DNSCard(Item):
    """A lookup card: skeleton rows, the answer row lights up at t_answer."""
    z = 20

    def __init__(self, x, y, t_in, t_answer, w=1700, h=900):
        super().__init__(t_in, None, None, True)
        self.x, self.y, self.t_answer, self.w, self.h = x, y, t_answer, w, h

    def cues(self):
        return [("pop", self.t_in, 0.5, {}), ("pop", self.t_answer, 0.4, {})]

    def bounds(self, res):
        r = self.w
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.35)
        if a <= 0:
            return
        u = ease_out_back(ramp(t, self.t_in, 0.5), 1.2)
        c.save(); c.translate(self.x, self.y + (1 - u) * 90)
        ans = ramp(t, self.t_answer, 0.4)
        pool(c, 0, 0, self.w * 0.9, CYAN, 0.12 * a)
        body(c, 0, 0, self.w, self.h, 60, a, halo=CYAN, halo_a=0.5 * ans * a)
        draw_text(c, res, "DNS", -self.w / 2 + self.w * 0.07, -self.h / 2 + self.h * 0.30, self.h * 0.26, "cond", WHITE, a, 0.1)
        for i in range(3):
            y = -self.h * 0.06 + i * self.h * 0.22
            hit = i == 1
            x0 = -self.w / 2 + self.w * 0.07; w = self.w * 0.86
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y, w, self.h * 0.14), 24, 24), paint((255, 255, 255), 0.07 * a))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0 + w * 0.04, y + self.h * 0.045, w * (0.38 if not hit else 0.30), self.h * 0.05), 12, 12), paint(DIM, 0.45 * a))
            if hit:
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y, w * ans, self.h * 0.14), 24, 24), paint(CYAN, 0.28 * a))
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, y, w, self.h * 0.14), 24, 24), paint(CYAN, 0.9 * ans * a, stroke=6))
                c.drawCircle(x0 + w - self.h * 0.1, y + self.h * 0.07, self.h * 0.04 * ans, paint(CYAN, a * ans))
        c.restore()


# ------------------------------------------------------------------ movers, links, effects
class Link(Item):
    """A dashed line between two points: draws on, then flows."""
    z = 8

    def __init__(self, a, b, t_in, dur=0.8, bend=0.0, rgb=EDGE, alpha=0.5, width=10, t_out=None, flow=True):
        super().__init__(t_in, t_out, None, True)
        self.a, self.b, self.bend, self.dur, self.rgb, self.alpha, self.wd, self.flow = a, b, bend, dur, rgb, alpha, width, flow
        xs = [a[0], b[0]]; ys = [a[1], b[1]]
        self.box = skia.Rect.MakeLTRB(min(xs) - 800, min(ys) - 800 - abs(b[0] - a[0]) * abs(bend), max(xs) + 800, max(ys) + 800 + abs(b[0] - a[0]) * abs(bend))

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        u = ease_in_out(ramp(t, self.t_in, self.dur)); a = self.fade(t)
        if u <= 0 or a <= 0:
            return
        path = quad_path(self.a, self.b, self.bend, 0, u)
        p = paint(self.rgb, self.alpha * a, stroke=self.wd)
        p.setPathEffect(skia.DashPathEffect.Make([self.wd * 2.5, self.wd * 3.0], ((t * 90) % (self.wd * 5.5)) if self.flow else 0))
        c.drawPath(path, p)


class Mover(Item):
    """Something travelling along a curve: a 'req' (cyan comet) or a 'file' (orange file icon)."""
    z = 40

    def __init__(self, a, b, t0, t1, kind="req", bend=0.0, size=60, hold_end=0.0, rgb=None, pop_end=True):
        super().__init__(t0, t1 + hold_end + 0.5, None, True)
        self.a, self.b, self.t0, self.t1, self.kind, self.bend, self.size, self.hold = a, b, t0, t1, kind, bend, size, hold_end
        self.rgb = rgb or (CYAN if kind == "req" else ORANGE)
        xs = [a[0], b[0]]; ys = [a[1], b[1]]
        self.box = skia.Rect.MakeLTRB(min(xs) - 900, min(ys) - 900 - abs(b[0] - a[0]) * abs(bend), max(xs) + 900, max(ys) + 900 + abs(b[0] - a[0]) * abs(bend))

    def bounds(self, res):
        return self.box

    def cues(self):
        return [("whoosh", self.t0, 0.28 if self.kind == "req" else 0.4, {})]

    def draw(self, c, res, t):
        if t < self.t0 or t > self.t1 + self.hold + 0.45:
            return
        u = ease_in_out(ramp(t, self.t0, self.t1 - self.t0))
        end_fade = 1 - ramp(t, self.t1 + self.hold, 0.4)
        x, y = quad_pt(self.a, self.b, self.bend, u)
        if self.kind == "req":
            for j in range(10, -1, -1):
                uu = max(0.0, u - j * 0.012)
                xx, yy = quad_pt(self.a, self.b, self.bend, uu)
                k = (1 - j / 11)
                glow(c, xx, yy, self.size * (0.35 + 0.65 * k), self.rgb, 0.8 * k * k * end_fade if j else end_fade)
        else:
            sc = ease_out_back(ramp(t, self.t0, 0.3), 2.0)
            file_icon(c, x, y, self.size * 2.4 * sc, end_fade)


class Crowd(Item):
    """Many requests converging on one point, then one request leaving."""
    z = 40

    def __init__(self, target, t0, t_merge, t_end, n=64, spread=3200, seed=4, out_to=None, bend=0.0, size=34):
        super().__init__(t0, t_end + 0.6, None, True)
        rng = np.random.default_rng(seed)
        ang = rng.uniform(math.pi * 0.62, math.pi * 1.38, n)           # arrive from the left (the viewers' side)
        rad = rng.uniform(spread * 0.5, spread, n)
        self.start = np.stack([target[0] + np.cos(ang) * rad, target[1] + np.sin(ang) * rad * 0.9], -1)
        self.delay = np.sort(rng.uniform(0, t_merge - t0 - 0.8, n))
        self.target, self.t0, self.tm, self.te, self.out_to, self.bend, self.size = target, t0, t_merge, t_end, out_to, bend, size
        self.n = n

    def cues(self):
        return [("shimmer", self.t0, 0.5, {}), ("whoosh", self.tm, 0.4, {})]

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        for i in range(self.n):
            ts = self.t0 + self.delay[i]
            u = ease_in_out(ramp(t, ts, 0.8))
            if t < ts or (u >= 1 and t > self.tm):
                continue
            sx, sy = self.start[i]
            x = sx + (self.target[0] - sx) * u; y = sy + (self.target[1] - sy) * u
            a = ramp(t, ts, 0.15) * (1 - ramp(t, ts + 0.7, 0.12))
            glow(c, x, y, self.size, CYAN, a * 0.9)
        # the merge: a ring at the target, then one bright request goes on
        k = ramp(t, self.tm - 0.2, 0.5)
        if k > 0 and t < self.tm + 0.6:
            c.drawCircle(self.target[0], self.target[1], 110 * (1 - k) + 40, paint(CYAN, 0.8 * (1 - ramp(t, self.tm + 0.3, 0.3)), stroke=14, blur=8))
        if self.out_to is not None and self.tm <= t <= self.te + 0.4:
            u = ease_in_out(ramp(t, self.tm, self.te - self.tm))
            for j in range(10, -1, -1):
                uu = max(0.0, u - j * 0.01)
                xx, yy = quad_pt(self.target, self.out_to, self.bend, uu)
                kk = 1 - j / 11
                glow(c, xx, yy, self.size * 1.7 * (0.35 + 0.65 * kk), CYAN, (0.8 * kk * kk if j else 1.0) * (1 - ramp(t, self.te, 0.4)))


class Ring(Item):
    """TTL countdown ring: drains from t0 to t1, then refills by t2."""
    z = 45

    def __init__(self, x, y, r, t0, t1, t2, rgb=ORANGE):
        super().__init__(t0 - 0.2, t2 + 0.8, None, True)
        self.x, self.y, self.r, self.t0, self.t1, self.t2, self.rgb = x, y, r, t0, t1, t2, rgb

    def bounds(self, res):
        return skia.Rect.MakeLTRB(self.x - self.r * 2, self.y - self.r * 2, self.x + self.r * 2, self.y + self.r * 2)

    def draw(self, c, res, t):
        a = ramp(t, self.t0 - 0.2, 0.3) * (1 - ramp(t, self.t2 + 0.3, 0.4))
        if a <= 0:
            return
        frac = 1 - ramp(t, self.t0, self.t1 - self.t0)
        if t > self.t1:
            frac = ease_out_cubic(ramp(t, self.t1 + 0.3, self.t2 - self.t1 - 0.3))
        rgb = self.rgb if t < self.t1 else (CYAN if frac < 0.99 else GREEN)
        rect = skia.Rect.MakeXYWH(self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)
        c.drawCircle(self.x, self.y, self.r, paint((255, 255, 255), 0.16 * a, stroke=self.r * 0.2))
        if frac > 0.002:
            c.drawArc(rect, -90, 360 * frac, False, paint(rgb, 0.5 * a, stroke=self.r * 0.34, blur=self.r * 0.2))
            c.drawArc(rect, -90, 360 * frac, False, paint(rgb, a, stroke=self.r * 0.2))


class Bars(Item):
    """Two comparison bars that shrink: (label, t_start) rows."""
    z = 60

    def __init__(self, x, y, w, rows, t_in, rgb=CYAN, size=170):
        super().__init__(t_in, None, None, True)
        self.x, self.y, self.w, self.rows, self.rgb, self.size = x, y, w, rows, rgb, size   # rows: [(label, t_shrink, final_frac, rgb)]

    def cues(self):
        return [("pop", self.t_in, 0.5, {})] + [("drop", t, 0.5, {}) for _, t, _, _ in self.rows]

    def bounds(self, res):
        r = self.w
        return skia.Rect.MakeLTRB(self.x - r, self.y - r, self.x + r, self.y + r)

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.4)
        if a <= 0:
            return
        x0 = self.x - self.w / 2
        ph = self.size * 1.95 * len(self.rows) + self.size * 1.6
        pcy = self.y + (len(self.rows) - 1) * self.size * 1.95 / 2 + self.size * 0.2
        pool(c, self.x, pcy, self.w * 0.8, (60, 110, 240), 0.14 * a)
        body(c, self.x, pcy, self.w + self.size * 2.2, ph, 90, a * 0.9, halo=CYAN, halo_a=0.25 * a)
        for i, (label, ts, fin, rgb) in enumerate(self.rows):
            y = self.y + i * self.size * 1.95
            grow = ease_out_cubic(ramp(t, self.t_in + 0.1 + i * 0.15, 0.7))
            frac = grow * (1 - (1 - fin) * ease_in_out(ramp(t, ts, 0.9)))
            draw_text(c, res, label, x0, y - self.size * 0.2, self.size, "cond", WHITE, a, 0.12)
            bh = self.size * 0.55; by = y
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, by, self.w, bh), bh / 2, bh / 2), paint((255, 255, 255), 0.08 * a))
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0, by, max(bh, self.w * frac), bh), bh / 2, bh / 2)
            c.drawRRect(rr, paint(rgb, 0.45 * a, blur=26))
            p = skia.Paint(AntiAlias=True); p.setShader(lin(x0, 0, x0 + self.w, 0, tuple(int(v * 0.7) for v in rgb), rgb, a, a)); c.drawRRect(rr, p)


class Stars(Item):
    """A faint field of far points for depth: always drawn, very cheap."""
    z = 1

    def __init__(self, box, n=900, seed=11):
        super().__init__(0, None, None, False)
        rng = np.random.default_rng(seed)
        self.box = box
        self.pts = np.stack([rng.uniform(box[0], box[2], n), rng.uniform(box[1], box[3], n)], -1)
        self.mag = rng.uniform(0, 1, n) ** 3
        self.ph = rng.uniform(0, 6.28, n)

    def draw(self, c, res, t):
        v = res.view
        m = (self.pts[:, 0] > v.left()) & (self.pts[:, 0] < v.right()) & (self.pts[:, 1] > v.top()) & (self.pts[:, 1] < v.bottom())
        idx = np.nonzero(m)[0]
        for lo, hi, w, al in ((0, 0.5, 9, 0.35), (0.5, 0.85, 14, 0.5), (0.85, 1.01, 22, 0.8)):
            sel = [i for i in idx if lo <= self.mag[i] < hi]
            if sel:
                pts = [skia.Point(float(self.pts[i, 0]), float(self.pts[i, 1])) for i in sel]
                c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint((170, 200, 255), al * (0.8 + 0.2 * math.sin(t * 0.7 + self.ph[sel[0]])), stroke=w))


class GridFloor(Item):
    """A faint drafting grid under the pipeline, fading out toward its edges."""
    z = 2

    def __init__(self, box, step=700):
        super().__init__(0, None, None, False)
        self.box, self.step = box, step

    def draw(self, c, res, t):
        v = res.view
        x0, y0, x1, y1 = max(self.box[0], v.left()), max(self.box[1], v.top()), min(self.box[2], v.right()), min(self.box[3], v.bottom())
        if x1 <= x0 or y1 <= y0:
            return
        s = self.step
        p = paint(EDGE, 0.11, stroke=3)
        path = skia.Path()
        gx = math.floor(x0 / s) * s
        while gx <= x1:
            path.moveTo(gx, y0); path.lineTo(gx, y1); gx += s
        gy = math.floor(y0 / s) * s
        while gy <= y1:
            path.moveTo(x0, gy); path.lineTo(x1, gy); gy += s
        c.drawPath(path, p)
