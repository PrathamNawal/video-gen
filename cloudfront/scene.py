"""Closer: how Amazon CloudFront works. One world: a dotted globe on the left, the request pipeline
(phone, DNS, edge racks, regional cache, origin) running off to the right. One camera glides between them.
Cyan = a request, orange = a file. Illustrative positions throughout (stated on screen)."""
import math

import numpy as np

from engine import LOOKS, Film
from cf_items import (CYAN, DIM, EDGE, GREEN, ORANGE, RED, WHITE, Bars, Crowd, DNSCard, Globe, GridFloor, Link, Mover, Num, Phone, Rack, Ring,
                      Stars, Text, Verdict, midpoint)

MUM, ASH = (19.08, 72.88), (39.04, -77.49)
NEAR = (16.2, 74.2)                       # an illustrative nearby edge, a short hop from Mumbai
US = [(39.04, -77.49), (40.7, -74.0), (41.9, -87.6), (33.7, -84.4), (32.8, -96.8), (25.8, -80.2), (34.0, -118.2), (47.6, -122.3)]
EU = [(51.5, -0.1), (50.1, 8.7), (48.9, 2.3), (59.3, 18.0)]
AS = [(35.7, 139.7), (1.35, 103.8)]
COPY_TO = [(51.5, -0.1), (50.1, 8.7), (40.4, -3.7), (6.5, 3.4), (-23.5, -46.6), (41.9, -87.6), (25.2, 55.3)]


def build_film(doc):
    L, E, W = doc.L, doc.E, doc.W
    look = dict(LOOKS["night"]); look.update(grain=0.016, vignette=0.7, glow=0.34)
    film = Film(doc.duration, fps=30, look=look)
    mlat, mlon = midpoint(MUM, ASH)

    def shot(t, x, y, z, rot=0.0, s=0.28, rad=None):
        film.shot(t, x, y, z, rot, radius=rad or 2600 / z, strength=s)

    film.add(Stars((-9000, -9000, 40000, 12000), n=2600))
    film.add(GridFloor((6000, -6000, 28000, 10000), step=640))

    # ------------------------------------------------------------------ the globe (lines 1-7, 18)
    views = [(0.0, mlat - 8, mlon + 16), (L(3), mlat - 5, mlon + 4), (L(4) + 0.4, mlat - 4, mlon - 2),
             (E(4) - 0.2, 24, 62), (L(5) + 0.1, 22, 66), (L(5) + 1.6, 30, -34),
             (22.6, 30, -90), (25.4, 28, 115), (E(7) + 0.2, 22, 42), (E(16), 22, 40),
             (L(18) - 0.3, mlat - 4, mlon + 3), (W(18, "next") - 0.6, mlat - 4, mlon + 3), (W(18, "next") + 0.5, 20, 72), (film.duration, 19.5, 73)]
    G = film.add(Globe(0, 0, 1500, views))

    # lines 1-4: the long way round, then the short hop
    G.dot(MUM, W(1, "mumbai") - 0.1, CYAN, 30, "MUMBAI", label_dx=1.1, label_dy=1.35, lsize=120, t_out=E(5) + 0.6)
    G.dot(ASH, W(1, "virginia") - 0.2, ORANGE, 30, "VIRGINIA", label_dx=-0.5, label_dy=-1.5, lsize=120, t_out=E(5) + 0.6)
    t_arc = W(1, "lives")
    far = G.arc(MUM, ASH, t_arc, 2.4, CYAN, 15, 0.34, t_out=W(4, "shorten") - 0.1,
                pulses=[(W(3, "light"), W(3, "light") + 1.5, -1), (W(3, "light") + 1.7, W(3, "light") + 3.2, +1)])
    G.dot(NEAR, W(4, "shorten"), GREEN, 17, None, ping=True, t_out=L(5) + 0.4)
    G.arc(MUM, NEAR, W(4, "trip") - 0.2, 0.7, GREEN, 9, 0.5, t_out=L(5) + 0.4, pulses=[(W(4, "trip") + 0.3, W(4, "trip") + 0.9, +1)])
    film.add(Num(0, -930, 400, 12855, W(2, "thirteen") - 0.5, dur=1.4, suffix=" KM", t_out=L(3) - 0.1))
    film.add(Num(0, -930, 400, 130, W(3, "light"), dur=3.1, suffix=" MS+", t_out=L(4) - 0.1, rgb=CYAN))
    film.add(Text("CLOSER", 380, -900, 560, L(4) + 0.1, t_out=W(4, "shorten") + 0.4, rgb=WHITE, glow_a=1.0, track=0.12, sfx_kind="impact", gain=0.9))

    # line 5: the idea. Copies leave Virginia for cities near people
    t5 = W(5, "copy") - 0.3
    for k, ll in enumerate(COPY_TO):
        t0 = t5 + 0.16 * k
        G.arc(ASH, ll, t0, 1.3, ORANGE, 10, 0.16, t_out=E(5) + 0.6, pulses=[(t0, t0 + 1.3, +1)], gain=0.2)
        G.dot(ll, t0 + 1.2, ORANGE, 18, None, ping=False)
    film.add(Text("A COPY, NEAR YOU", 0, -960, 330, W(5, "put"), t_out=E(5) + 0.4, rgb=ORANGE, glow_a=1.0, track=0.1))

    # lines 6-7: fourteen at launch, hundreds now (positions illustrative)
    def t_lon(lon):
        return 22.6 + (lon + 90) / 73.0
    for grp, rgb in ((US, CYAN), (EU, CYAN), (AS, CYAN)):
        for ll in grp:
            G.dot(ll, max(W(6, "launched") - 0.2, t_lon(ll[1]) - 0.15), rgb, 22, None, ping=False, shimmer=False)
    film.add(Text("2008", 3250, -560, 380, W(6, "two"), t_out=L(7) - 0.1, rgb=DIM, glow_a=0.6, track=0.16))
    film.add(Num(3250, 620, 820, 14, W(6, "fourteen") - 0.2, dur=0.9, t_out=L(7) - 0.1))
    rng = np.random.default_rng(5)
    land = G.land_ll[(G.land_ll[:, 0] > -45) & (G.land_ll[:, 0] < 62)]
    centers = land[rng.choice(len(land), 112, replace=False)]
    pts = centers[rng.integers(0, 112, 640)] + rng.normal(0, 1.6, (640, 2))
    tt = np.sort(rng.uniform(W(7, "six") - 0.2, E(7) + 0.1, 640))
    G.set_swarm(pts, tt, ORANGE, 13)
    film.add(Num(3250, 300, 980, 640, W(7, "six") - 0.4, dur=2.0, suffix="+", t_out=L(8) - 0.1, rgb=WHITE))
    film.add(Text("LOCATIONS ILLUSTRATIVE", 3250, -1350, 110, L(6) + 0.5, t_out=L(8) - 0.2, rgb=DIM, track=0.25))

    # ------------------------------------------------------------------ the pipeline (lines 8-17)
    t13 = L(13) + 0.25
    PA, PB = (8600, -250), (8600, 1900)
    DNS = (10900, -2300)
    E1, E0, E2 = (13300, 350), (14900, -2500), (14900, 3200)
    RG = (17900, 350)
    OR = (24200, 350)

    phoneA = film.add(Phone(*PA, L(8) + 0.05, s=1.35, modes=[(W(8, "asks"), "loading"), (E(10) - 0.2, "playing"), (L(11) + 0.3, "loading"), (t13 + 3.0, "playing")]))
    phoneB = film.add(Phone(*PB, L(14), s=1.35, modes=[(L(14) + 0.35, "loading"), (L(14) + 1.7, "playing")]))
    film.add(DNSCard(DNS[0], DNS[1], W(8, "dns") - 0.5, L(9) + 0.7, w=2100, h=1100))
    film.add(Mover((PA[0] + 450, PA[1] - 400), (DNS[0] - 900, DNS[1] + 100), W(8, "asks"), W(8, "asks") + 0.9, "req", bend=-0.2, size=70))
    film.add(Mover((DNS[0] - 900, DNS[1] + 300), (PA[0] + 470, PA[1] - 300), L(9) + 0.7, L(9) + 1.5, "req", bend=-0.2, size=70))

    edge1 = film.add(Rack(*E1, 1800, 2200, 4, W(9, "nearby") - 0.2, "EDGE", label_size=200,
                          contents=[(1, W(10, "file"), L(11) + 0.35), (1, t13 + 2.15, None)],
                          flashes=[(0, W(10, "checks") + 0.1, W(10, "checks") + 0.45, CYAN), (1, W(10, "checks") + 0.45, W(10, "checks") + 0.9, CYAN), (2, W(10, "checks") + 0.9, W(10, "checks") + 1.2, CYAN),
                                   (1, W(11, "miss"), W(11, "miss") + 1.0, RED)],
                          halos=[(W(9, "fastest") - 0.2, W(9, "fastest") + 6.0, CYAN)]))
    film.add(Rack(*E0, 1800, 2200, 4, W(9, "nearby") - 0.2, "EDGE", dim=0.45, label_size=200))
    film.add(Rack(*E2, 1800, 2200, 4, W(9, "nearby") - 0.1, "EDGE", dim=0.45, label_size=200))
    film.add(Link((PA[0] + 450, PA[1] + 100), (E1[0] - 950, E1[1]), W(9, "nearby"), 0.9, 0.05, CYAN, 0.7, 12))
    film.add(Link((PA[0] + 450, PA[1] - 100), (E0[0] - 950, E0[1] + 200), W(9, "nearby") + 0.15, 1.1, -0.04, EDGE, 0.25, 8))
    film.add(Link((PA[0] + 450, PA[1] + 300), (E2[0] - 950, E2[1] - 200), W(9, "nearby") + 0.3, 1.1, 0.04, EDGE, 0.25, 8))
    film.add(Mover((PA[0] + 450, PA[1] + 100), (E1[0] - 950, E1[1]), W(9, "fastest") - 0.2, W(9, "fastest") + 0.9, "req", size=70))

    # line 10: a hit
    film.add(Verdict("CACHE HIT", E1[0], E1[1] - 1550, W(10, "hit") - 0.1, GREEN, 280, t_out=L(11) + 0.1))
    bay1 = edge1.bay_center(1)
    film.add(Mover(bay1, (PA[0] + 470, PA[1] + 100), E(10) - 1.2, E(10) - 0.2, "file", bend=0.08, size=70))
    # line 11: a miss, one layer up
    regional = film.add(Rack(*RG, 3000, 2500, 6, L(11), "REGIONAL EDGE CACHE", cols=2, label_size=180,
                             contents=[(1, t13 + 1.1, None)],
                             flashes=[(i, L(12) + 0.2 + 0.12 * i, L(12) + 0.6 + 0.12 * i, RED) for i in range(6)],
                             halos=[(W(11, "regional") - 0.2, W(11, "regional") + 3.8, CYAN)]))
    film.add(Verdict("CACHE MISS", E1[0], E1[1] - 1550, W(11, "miss") - 0.1, RED, 280, t_out=W(11, "asks") + 1.5))
    film.add(Link((E1[0] + 950, E1[1]), (RG[0] - 1550, RG[1]), L(11) + 0.3, 0.9, 0.0, EDGE, 0.6, 10))
    film.add(Mover((E1[0] + 950, E1[1]), (RG[0] - 1550, RG[1]), W(11, "asks"), W(11, "asks") + 1.3, "req", size=70))
    # line 12: all the way to the origin
    film.add(Rack(*OR, 1900, 3600, 8, L(12) - 0.3, "ORIGIN", origin=True, label_size=220))
    film.add(Link((RG[0] + 1550, RG[1]), (OR[0] - 1000, OR[1]), L(12), 1.6, 0.0, ORANGE, 0.45, 12))
    film.add(Mover((RG[0] + 1550, RG[1]), (OR[0] - 1000, OR[1]), W(12, "only") + 0.2, W(12, "only") + 2.6, "req", size=95))
    # line 13: the file comes back, every layer keeps a copy
    film.add(Mover((OR[0] - 1000, OR[1]), (RG[0] + 1550, RG[1]), t13, t13 + 1.1, "file", size=95))
    film.add(Mover((RG[0] - 1550, RG[1]), (E1[0] + 950, E1[1]), t13 + 1.15, t13 + 2.15, "file", size=75))
    film.add(Mover((E1[0] - 950, E1[1]), (PA[0] + 470, PA[1] + 100), t13 + 2.2, t13 + 3.0, "file", size=70))
    # line 14: the next viewer, a hit
    film.add(Link((PB[0] + 450, PB[1]), (E1[0] - 950, E1[1] + 300), L(14) + 0.1, 0.4, -0.05, CYAN, 0.7, 12))
    film.add(Mover((PB[0] + 450, PB[1]), (E1[0] - 950, E1[1] + 300), L(14) + 0.3, L(14) + 0.7, "req", size=70))
    film.add(Verdict("CACHE HIT", E1[0], E1[1] - 1550, L(14) + 0.7, GREEN, 280, t_out=L(15) - 0.05))
    film.add(Mover((E1[0] - 950, E1[1] + 300), (PB[0] + 470, PB[1]), L(14) + 0.8, L(14) + 1.7, "file", bend=0.05, size=70))
    # line 15: a thousand become one
    film.add(Crowd(E1, W(15, "thousand") - 0.3, W(15, "merges") + 0.1, E(15) - 0.2, n=130, spread=3400, out_to=(OR[0] - 1000, OR[1]), bend=-0.04, size=52))
    film.add(Num(E1[0], E1[1] - 2000, 560, 1, W(15, "thousand") - 0.2, dur=W(15, "merges") - W(15, "thousand") + 0.2, start=1000, t_out=E(15) + 0.2, rgb=WHITE, caption="REQUEST TO ORIGIN"))
    # line 16: time to live
    bay_y = bay1[1]
    ring = (E1[0] + 900 + 600, bay_y)
    film.add(Ring(ring[0], ring[1], 340, L(16) + 0.2, W(16, "expires") + 0.2, E(16) + 0.1))
    film.add(Text("TTL", ring[0], ring[1] + 85, 260, L(16) + 0.1, t_out=E(16) + 0.9, rgb=WHITE, glow_a=0.7))
    film.add(Mover((E1[0] + 950, E1[1]), (RG[0] - 1550, RG[1]), W(16, "checks"), W(16, "checks") + 0.9, "req", size=70))
    film.add(Mover((RG[0] - 1550, RG[1] + 150), (E1[0] + 950, E1[1] + 150), W(16, "checks") + 1.0, W(16, "checks") + 1.8, "req", size=70))
    # line 17: less load, less wait
    film.add(Bars(16000, 6700, 5400, [("ORIGIN LOAD", W(17, "works") + 0.1, 0.16, ORANGE), ("VIEWER WAIT", W(17, "waits") + 0.1, 0.1, CYAN)], L(17) - 0.2, size=260))

    # ------------------------------------------------------------------ camera
    gx, gy, _ = G.to_screen(MUM, E(4) - 0.2)
    shot(0.0, 0, 0, 0.58, -0.6)
    shot(L(2), 0, 80, 0.6, -0.3)
    shot(L(3), 0, 80, 0.62, 0.2)
    shot(L(4) + 0.3, 0, 60, 0.66, 0.0)
    shot(W(4, "shorten") + 0.2, gx * 0.4, gy * 0.3, 0.9)
    shot(E(4) + 0.3, gx, gy, 2.6, 0.5, s=0.2)
    shot(L(5) + 0.15, gx * 0.9, gy * 0.8, 1.5, 0.3, s=0.2)
    shot(L(5) + 1.8, 0, 100, 0.6, -0.3)
    shot(E(5), 80, 40, 0.58, 0.0)
    shot(L(6) + 0.3, 1100, 0, 0.56, 0.3)
    shot(E(7) - 0.4, 1200, 0, 0.55, -0.2)
    # pipeline
    shot(L(8) - 0.1, 8900, -450, 0.62, 0.3)
    shot(W(8, "dns") - 0.2, 9700, -1100, 0.55, 0.0)
    shot(E(8), 9900, -1300, 0.54, 0.0)
    shot(L(9) + 0.5, 10600, -700, 0.5)
    shot(W(9, "nearby") + 0.3, 11700, 150, 0.42, 0.3, s=0.2)
    shot(W(9, "fastest") + 0.2, 11300, 250, 0.5, 0.0)
    shot(L(10), 11300, 250, 0.52, 0.4)
    shot(E(10), 11300, 250, 0.5, 0.0)
    shot(L(11) + 0.2, 14800, 350, 0.47, -0.3)
    shot(E(11), 15600, 350, 0.44, 0.2)
    shot(L(12) + 0.2, 19400, 350, 0.4, 0.0)
    shot(W(12, "only") + 1.4, 21400, 350, 0.37, 0.3, s=0.2)
    shot(E(12), 22200, 350, 0.42, 0.0, s=0.2)
    shot(t13, 22200, 350, 0.42, 0.0)
    shot(t13 + 1.0, 19800, 350, 0.42, -0.3)
    shot(t13 + 2.1, 15500, 350, 0.46, 0.2)
    shot(t13 + 3.0, 11400, 300, 0.52, 0.0)
    shot(L(14), 11300, 400, 0.5, 0.3)
    shot(E(14), 11400, 350, 0.48, 0.0)
    shot(L(15) + 0.2, 13600, 100, 0.36, -0.2, s=0.2)
    shot(W(15, "merges") + 0.4, 15600, 300, 0.36, 0.2, s=0.2)
    shot(E(15) - 0.4, 21200, 350, 0.34, 0.0, s=0.2)
    shot(L(16) + 0.1, 15000, 900, 0.56, 0.3)
    shot(E(16), 15300, 880, 0.54, 0.0)
    shot(L(17) + 0.1, 16000, 6950, 0.56, -0.3)
    shot(E(17) - 0.4, 16000, 6980, 0.54, 0.2)
    # back to the globe
    shot(L(18) - 0.1, 0, 60, 0.6, -0.4)
    shot(W(18, "virginia") + 0.2, 0, 60, 0.64, 0.2)
    shot(W(18, "next") - 0.1, 0, 0, 0.7, 0.0)
    gx2, gy2, _ = G.to_screen(MUM, W(18, "next") + 0.7)
    shot(W(18, "next") + 0.9, gx2, gy2, 2.4, 0.3, s=0.2)
    shot(E(18) + 0.4, gx2 * 0.5, gy2 * 0.5, 1.1, -0.2, s=0.2)
    shot(film.duration, 0, 0, 0.62, 0.0, s=0.15)

    # line 18: the payoff on the globe
    G.arc(ASH, MUM, L(18), 1.8, CYAN, 12, 0.22, t_out=W(18, "next") - 0.4, pulses=[(L(18) + 0.2, L(18) + 1.8, -1)], gain=0.3)
    G.dot(MUM, L(18) - 0.2, CYAN, 30, "MUMBAI", label_dx=0.4, label_dy=-1.7, lsize=120, ping=True)
    G.dot(ASH, L(18) - 0.2, ORANGE, 30, "VIRGINIA", label_dx=-0.5, label_dy=-1.5, lsize=120, t_out=W(18, "next") - 0.3)
    G.dot(NEAR, W(18, "next") - 0.2, GREEN, 17, None, ping=True)
    G.arc(MUM, NEAR, W(18, "next") + 0.4, 0.6, GREEN, 9, 0.5, pulses=[(W(18, "next") + 0.9, W(18, "next") + 1.5, +1)], gain=0.2)

    film.cue("riser", E(7) - 1.0, 0.7, dur=1.2)
    film.cue("boom", L(4) + 0.15, 0.8)
    film.cue("boom", L(18) + 2.4, 0.5)
    return film
