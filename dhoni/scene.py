"""Captain Cool: MS Dhoni. Code-drawn cards, counters and stamps only (no photos). Night look.

Two rows of slots, one hero per narration line: lines 1-12 along the top row, 13-19 below it.
"""
from engine import BigText, Card, Counter, Film, PenMark, Route, Stamp

SAFFRON = (255, 153, 51)
BLUE = (24, 70, 160)
CW, CH, GAP, ROWGAP = 3700, 1500, 4400, 3400


def slot(i):
    """World centre of the slot for line i (1-based)."""
    if i <= 12:
        return (i - 1) * GAP, 0
    return (i - 13) * GAP + 2 * GAP, ROWGAP


def build_film(doc):
    L, E, W = doc.L, doc.E, doc.W
    film = Film(doc.duration, fps=30, look="night")
    X = {i: slot(i) for i in range(1, 20)}

    def card(i, title, lines, **kw):
        x, y = X[i]
        return film.add(Card(x, y, CW, CH, L(i) + 0.05, title=title, lines=lines, accent=SAFFRON,
                             title_size=kw.pop("title_size", 330), body_size=kw.pop("body_size", 170), **kw))

    # row 1
    card(1, "APRIL 2, 2011", ["Wankhede Stadium, Mumbai"], title_size=330)
    x, y = X[2]
    film.add(Counter(x, y, 900, 28, W(2, "twenty-eight") - 0.1, dur=1.2, suffix=" YEARS", caption="SINCE 1983", rgb=SAFFRON))
    x, y = X[3]
    film.add(Counter(x, y, 1100, 91, W(3, "ninety-one") - 0.4, dur=1.0, suffix="*", caption="NOT OUT", rgb=(255, 255, 255)))
    film.add(Stamp("SIX", x + 1500, y - 600, size=420, rot=-8, t_in=W(3, "six") + 0.05, rgb=SAFFRON))
    x, y = X[4]
    film.add(BigText("M.S. DHONI", x, y - 500, 420, L(4) + 0.05, rgb=(255, 255, 255), type_on=0.6))
    film.add(BigText("CAPTAIN COOL", x, y + 400, 820, E(4) - 0.9, rgb=SAFFRON, type_on=0.8))
    card(5, "RANCHI · 1981", ["A pump operator's son"], title_size=330)
    card(6, "GLOVES ON", ["Football goalkeeper", "to wicketkeeper"])
    card(7, "TICKET COLLECTOR", ["Kharagpur railway station", "2001"], title_size=260, rgb=(244, 232, 200))
    c8 = card(8, "SIXES", ["Evenings and weekends"], title_size=380)
    x, y = X[8]
    film.add(PenMark("underline", x, y + 120, 2200, 40, t_in=W(8, "sixes") - 0.1, dur=0.5, width=26, rgb=SAFFRON))
    card(9, "DEBUT", ["Dec 23, 2004 · vs Bangladesh"], title_size=400)
    x, y = X[10]
    film.add(BigText("0", x, y, 1900, L(10) + 0.05, rgb=(255, 255, 255)))
    film.add(Stamp("RUN OUT", x, y + 100, size=480, rot=-9, t_in=W(10, "out") - 0.1))
    x, y = X[11]
    film.add(Counter(x, y, 1100, 148, W(11, "hundred") - 0.1, dur=1.2, caption="VS PAKISTAN", rgb=(255, 255, 255)))
    x, y = X[12]
    film.add(Counter(x, y, 1100, 183, W(12, "hundred") - 0.1, dur=1.2, suffix="*", caption="JAIPUR · 2005", rgb=SAFFRON))
    film.add(Stamp("RECORD", x + 1300, y - 650, size=380, rot=-8, t_in=W(12, "record") - 0.1))
    # row 2
    card(13, "WORLD T20", ["2007 · Captain"], title_size=420)
    card(14, "INDIA vs PAKISTAN", ["The last over"], title_size=240)
    x, y = X[15]
    film.add(Counter(x, y, 1100, 5, W(15, "five") - 0.1, dur=0.8, suffix=" RUNS", rgb=SAFFRON))
    film.add(Stamp("WON", x + 1300, y - 650, size=420, rot=-8, t_in=W(15, "runs") - 0.05, rgb=(40, 150, 70)))
    card(16, "ALL THREE", ["World Cup · World T20", "Champions Trophy"], title_size=420, body_size=160)
    card(17, "AUG 15, 2020", ["Retires, on Instagram"], title_size=330)
    x, y = X[18]
    film.add(Counter(x - 1000, y, 640, 350, W(18, "fifty") - 0.1, dur=1.0, caption="ONE-DAY GAMES", rgb=(255, 255, 255)))
    film.add(Counter(x + 1100, y, 640, 10000, W(18, "ten") - 0.1, dur=1.2, suffix="+", caption="RUNS", rgb=SAFFRON))
    x, y = X[19]
    film.add(BigText("6", x, y, 2200, W(19, "six") - 0.2, rgb=SAFFRON))

    # strings between neighbouring slots on the same row
    for i in list(range(2, 13)) + list(range(14, 20)):
        (xa, ya), (xb, yb) = X[i - 1], X[i]
        film.add(Route((xa + CW / 2 + 60, ya), (xb - CW / 2 - 60, yb), t_in=L(i) - 0.25, dur=0.5, bend=-0.25, width=20, rgb=(200, 210, 235)))

    # camera
    film.shot(0.0, X[1][0], X[1][1], 0.5)
    for i in range(1, 20):
        x, y = X[i]
        film.shot(L(i) + 0.4, x, y, 0.62 if i not in (18,) else 0.5, rot=-0.4 if i % 2 else 0.4)
        film.shot(E(i) - 0.1, x + 250, y + 120, 0.58 if i != 18 else 0.47)
        if i == 12:
            film.shot(E(12) + 0.35, 20000, 1600, 0.1, radius=20000, strength=0.15)
    mid = (X[1][0] + X[12][0]) / 2
    film.shot(film.duration - 0.5, mid, ROWGAP / 2, 0.088, radius=20000, strength=0.1)
    film.shot(film.duration, mid, ROWGAP / 2, 0.085, radius=20000, strength=0.1)
    return film
