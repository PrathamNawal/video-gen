"""JusRecruit launch film: one studio board, four clusters (problem, reveal, proofs, close)."""
from engine import BigText, Card, Counter, Film, PenMark, Route, Stamp

ACCENT = (0, 122, 98)        # teal-green, close to the site's brand green
RED = (190, 48, 40)
INK = (34, 32, 30)
CW, CH = 3000, 1500
C = [0, 12500, 27000, 42000]  # cluster centres


def build_film(doc):
    L, E, W = doc.L, doc.E, doc.W
    film = Film(doc.duration, fps=30, look="studio")

    # ---- 1 problem: three grey cards in a row
    a, b, c = C[0] - 3400, C[0], C[0] + 3400
    film.add(Card(a, 0, CW, CH, L(1) + 0.05, title="THE ATS", lines=["Every candidate", "Every stage"], rgb=(250, 248, 244), accent=INK, title_size=300, body_size=170))
    film.add(Card(b, 0, CW, CH, L(2) + 0.05, title="BY HAND", lines=["Recruiters do the work"], accent=INK, title_size=300, body_size=170))
    film.add(Stamp("STILL MANUAL", b, 150, size=330, rot=-7, t_in=W(2, "hand") - 0.1, rgb=RED))
    film.add(Card(c, 0, CW, CH, L(3) + 0.05, title="SCREENING", lines=["Hundreds of applicants", "Hundreds of phone screens"], accent=INK, title_size=300, body_size=170))
    film.add(Route((a + CW / 2 + 60, 0), (b - CW / 2 - 60, 0), t_in=L(2) - 0.2, dur=0.5, bend=-0.3, width=24, rgb=INK))
    film.add(Route((b + CW / 2 + 60, 0), (c - CW / 2 - 60, 0), t_in=L(3) - 0.2, dur=0.5, bend=-0.3, width=24, rgb=INK))

    # ---- 2 reveal
    x = C[1]
    film.add(Route((c + CW / 2 + 60, 0), (x - 3600, -1100), t_in=L(4) - 0.5, dur=0.9, bend=-0.25, width=24, rgb=ACCENT))
    film.add(BigText("JUSRECRUIT", x, -1500, 900, L(4) - 0.05, rgb=ACCENT, shadow=False, grunge=False, type_on=0.6))
    film.add(PenMark("underline", x, -1250, 6200, 50, t_in=W(4, "agentic") - 0.1, dur=0.5, width=30, rgb=INK))
    film.add(Card(x - 3400, 700, CW, CH, L(5) + 0.05, title="AI PHONE SCREEN", lines=["The first call, done"], accent=ACCENT, title_size=230, body_size=170))
    film.add(Card(x, 700, CW, CH, W(5, "interviews") - 0.5, title="AI INTERVIEW", lines=["The first round, done"], accent=ACCENT, title_size=240, body_size=170))
    film.add(Card(x + 3400, 700, CW, CH, L(6) + 0.05, title="YOUR TEAM", lines=["Runs the pipeline"], accent=INK, title_size=290, body_size=170))
    film.add(Stamp("YOU DECIDE", x + 3400, 850, size=330, rot=-6, t_in=W(6, "decision") - 0.1, rgb=ACCENT))

    # ---- 3 proofs
    x = C[2]
    p, s, ai, sc, tr = x - 5200, x - 1500, x + 1700, x + 5200, x + 8600
    film.add(Route((C[1] + 3400 + CW / 2 + 60, 700), (p - CW / 2 - 60, -200), t_in=L(7) - 0.5, dur=0.9, bend=-0.25, width=24, rgb=ACCENT))
    film.add(Card(p, -200, CW, 1400, L(7) + 0.05, title="AI PHONE SCREEN", lines=["Calls every applicant", "In their language"], accent=ACCENT, title_size=230, body_size=170))
    film.add(BigText("24/7", p, 1050, 520, W(7, "hour") - 0.2, rgb=ACCENT, shadow=False, grunge=False, type_on=0.4))
    film.add(Counter(p, 1900, 420, 5, W(8, "five") - 0.2, dur=0.9, prefix="< ", suffix=" MIN", rgb=INK))
    film.add(Card(s, 0, 2700, CH, L(9) + 0.05, title="SAI", lines=["AI interviewer"], accent=ACCENT, title_size=420, body_size=170))
    film.add(Card(ai, 0, 2700, CH, W(9, "aina") - 0.3, title="AINA", lines=["AI interviewer"], accent=ACCENT, title_size=420, body_size=170))
    film.add(Card(sc, 0, CW, CH, L(10) + 0.05, title="SCORECARD", lines=["Questions adapt"], accent=INK, title_size=250, body_size=170))
    film.add(Counter(sc, 1600, 520, 100, W(10, "hundred") - 0.9, dur=1.2, suffix="/100", rgb=ACCENT))
    film.add(Card(tr, 0, CW, CH, L(11) + 0.05, title="TRANSCRIPT", lines=["+ replay"], accent=INK, title_size=250, body_size=170))
    film.add(Route((sc + CW / 2 + 60, 0), (tr - CW / 2 - 60, 0), t_in=L(11) - 0.2, dur=0.5, bend=-0.3, width=24, rgb=INK))

    # ---- 4 close
    x = C[3]
    j, o = x - 3400, x + 3400
    film.add(Route((tr + CW / 2 + 60, 0), (j - CW / 2 - 60, 0), t_in=L(12) - 0.6, dur=0.9, bend=-0.2, width=24, rgb=ACCENT))
    film.add(Card(j, 0, CW, CH, L(12) - 0.55, title="JOB POST", lines=["Posted in minutes"], accent=ACCENT, title_size=300, body_size=170))
    film.add(Card(o, 0, CW, CH, W(12, "offer") - 0.4, title="OFFER LETTER", lines=["Sent from the same place"], accent=ACCENT, title_size=250, body_size=170))
    film.add(Route((j + CW / 2 + 60, 0), (o - CW / 2 - 60, 0), t_in=W(12, "offer") - 0.8, dur=0.6, bend=-0.3, width=26, rgb=INK))
    film.add(Card(x, 2200, CW, 1300, L(13) + 0.05, title="START FREE", lines=["Unlimited job posts"], accent=ACCENT, title_size=260, body_size=170))
    film.add(BigText("JUSRECRUIT.COM", x, -1700, 700, L(14) + 0.1, rgb=ACCENT, shadow=False, grunge=False, type_on=0.8))

    # ---- camera
    f = film.shot
    f(0.0, C[0], 0, 0.30)
    f(L(1) + 0.4, a, 150, 0.62, rot=-0.4)
    f(L(2) + 0.45, b, 150, 0.62, rot=0.4)
    f(L(3) + 0.45, c, 150, 0.62, rot=-0.4)
    f(E(3) + 0.2, C[0] + 3400, 0, 0.5)
    f(L(4) + 0.5, C[1], -1400, 0.46, rot=0.3)
    f(L(5) + 0.5, C[1] - 1700, 700, 0.42)
    f(L(6) + 0.45, C[1] + 3400, 760, 0.6, rot=0.4)
    f(L(7) + 0.5, p, -100, 0.55, rot=-0.3)
    f(W(7, "hour") + 0.3, p, 400, 0.5)
    f(L(8) + 0.4, p, 1250, 0.6, rot=0.3)
    f(L(9) + 0.55, (s + ai) / 2, 0, 0.45)
    f(L(10) + 0.5, sc, 650, 0.5, rot=-0.3)
    f(L(11) + 0.45, (sc + tr) / 2, 0, 0.5, rot=0.3)
    f(L(12) + 0.6, x - 1600 if False else C[3], 0, 0.42)
    f(L(13) + 0.45, C[3], 1100, 0.4, rot=-0.3)
    f(L(14) + 0.3, C[3], 300, 0.3)
    f(film.duration, C[3] - 1500, 350, 0.2, radius=20000, strength=0.1)
    return film
