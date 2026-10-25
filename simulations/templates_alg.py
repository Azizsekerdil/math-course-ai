# -*- coding: utf-8 -*-
"""Cebir simülasyonları (1/2): doğrusal denklem, doğru denklemleri, sistemler,
ikinci derece denklem, genel fonksiyon grafiği.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Sorular kurs
kitaplarından KOPYALANMAZ: kendi ifademizle yazılmış, sayıları değiştirilmiş
tipik ders örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# Ortak kesir yardımcıları. Her şablonun kaynağına AYNEN eklenir; böylece her
# kaynak yine tek başına çalışır (düzenleyicide ve bağımsız betikte).
_FRAC = r'''
from fractions import Fraction


def _q(v):
    # P değeri -> tam kesir (0.5 -> 1/2; 1.2 -> 6/5, ikili kayan nokta hatası olmadan)
    if isinstance(v, bool):
        raise ValueError(f"sayı bekleniyordu / a number was expected: {v}")
    if isinstance(v, float):
        if v != v or abs(v) == float("inf"):
            raise ValueError("sonlu bir sayı gerekli / a finite number is required")
        return Fraction(repr(v))
    if isinstance(v, str):
        try:
            return Fraction(v.strip())
        except (ValueError, ZeroDivisionError):
            raise ValueError(f"sayı okunamadı / not a number: {v}")
    return Fraction(v)


def _f(v):
    v = Fraction(v)
    if v.denominator == 1:
        return str(v.numerator)
    if v.denominator > 10000:
        return f"{float(v):.6g}"
    return f"{v.numerator}/{v.denominator}"


def _pp(v):
    # negatif ya da kesirli sayıyı parantez içinde yazar: (-3), (2/3)
    v = Fraction(v)
    return f"({_f(v)})" if (v < 0 or v.denominator != 1) else _f(v)


def _cx(m, var="x"):
    # m·var: 1 -> x, -1 -> -x, 3 -> 3x, 2/3 -> (2/3)x, -2/3 -> -(2/3)x
    m = Fraction(m)
    if m == 1:
        return var
    if m == -1:
        return "-" + var
    if m.denominator == 1:
        return f"{m.numerator}{var}"
    return ("-" if m < 0 else "") + f"({_f(abs(m))}){var}"


def _lin(m, b, var="x"):
    # m·var + b
    m, b = Fraction(m), Fraction(b)
    if m == 0:
        return _f(b)
    s = _cx(m, var)
    if b == 0:
        return s
    return f"{s} {'+' if b > 0 else '-'} {_f(abs(b))}"
'''

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["linear_equation"] = {
    "course": "alg",
    "title": ("Doğrusal denklem çözümü", "Solving a linear equation"),
    "topics": ["linear equation", "solving equations", "solving linear equations", "one step equation",
               "two step equation", "multi step equation", "equations with variables on both sides",
               "variables on both sides", "solve for x", "first degree equation",
               "doğrusal denklem", "birinci dereceden", "birinci derece", "bir bilinmeyenli denklem",
               "denklem çözme", "denklem çözümü"],
    "code": r'''
import numpy as np
''' + _FRAC + r'''

def _abc(P):
    a, b, c = _q(P["a"]), _q(P["b"]), _q(P["c"])
    if a == 0:
        raise ValueError("a = 0: denklemde x yok, birinci dereceden değil / a = 0: not a linear equation in x")
    return a, b, c


def _rows(a, b, c):
    # sol paneldeki satırlar: (denklem, (tr not, en not))
    r = c - b
    x = r / a
    rows = [(f"{_lin(a, b)} = {_f(c)}", ("Denklem", "Equation"))]
    if b > 0:
        rows.append((f"{_cx(a)} = {_f(r)}", (f"iki taraftan {_f(b)} çıkar", f"subtract {_f(b)} from both sides")))
    elif b < 0:
        rows.append((f"{_cx(a)} = {_f(r)}", (f"iki tarafa {_f(-b)} ekle", f"add {_f(-b)} to both sides")))
    if a != 1:
        rows.append((f"x = {_pp(r)}/{_pp(a)}", (f"iki tarafı {_f(a)} ile böl", f"divide both sides by {_f(a)}")))
    last = f"x = {_f(x)}"
    if rows[-1][0] == last:
        rows[-1] = (last, (rows[-1][1][0] + " ⇒ çözüm", rows[-1][1][1] + " ⇒ solution"))
    else:
        rows.append((last, ("Çözüm", "Solution")))
    return rows, x


def _check(a, x, b):
    s = f"{_pp(a)}·{_pp(x)}"
    if b != 0:
        s += f" {'+' if b > 0 else '-'} {_f(abs(b))}"
    return s


def solve(P):
    a, b, c = _abc(P)
    r = c - b
    x = r / a
    lhs = _lin(a, b)
    steps = [(f"Denklem: {lhs} = {_f(c)}", f"Equation: {lhs} = {_f(c)}")]
    if b > 0:
        steps.append((f"Her iki taraftan {_f(b)} çıkar: {lhs} - {_f(b)} = {_f(c)} - {_f(b)}  ⇒  {_cx(a)} = {_f(r)}",
                      f"Subtract {_f(b)} from both sides: {lhs} - {_f(b)} = {_f(c)} - {_f(b)}  ⇒  {_cx(a)} = {_f(r)}"))
    elif b < 0:
        steps.append((f"Her iki tarafa {_f(-b)} ekle: {lhs} + {_f(-b)} = {_f(c)} + {_f(-b)}  ⇒  {_cx(a)} = {_f(r)}",
                      f"Add {_f(-b)} to both sides: {lhs} + {_f(-b)} = {_f(c)} + {_f(-b)}  ⇒  {_cx(a)} = {_f(r)}"))
    if a != 1:
        steps.append((f"Her iki tarafı {_f(a)} ile böl: x = {_pp(r)}/{_pp(a)} = {_f(x)}",
                      f"Divide both sides by {_f(a)}: x = {_pp(r)}/{_pp(a)} = {_f(x)}"))
    steps.append((f"Sonuç: x = {_f(x)}", f"Result: x = {_f(x)}"))
    steps.append((f"Kontrol: {_check(a, x, b)} = {_f(a * x + b)} ✓", f"Check: {_check(a, x, b)} = {_f(a * x + b)} ✓"))
    return {"answer": f"x = {_f(x)}", "steps": steps, "fmt": {"lhs": lhs}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, c = _abc(P)
    rows, xq = _rows(a, b, c)
    fa, fb, fc, x0 = float(a), float(b), float(c), float(xq)
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.25], left=0.03, right=0.97, wspace=0.12)
    tx = fig.add_subplot(gs[0, 0])
    tx.axis("off")
    ax = fig.add_subplot(gs[0, 1])
    span = max(6.0, abs(x0) * 1.6 + 2)
    xs = np.linspace(x0 - span, x0 + span, 300)
    ys = fa * xs + fb
    ax.set_xlim(xs[0], xs[-1])
    yr = max(ys.max(), fc) - min(ys.min(), fc)
    lo, hi = min(ys.min(), fc) - 0.08 * yr - 1, max(ys.max(), fc) + 0.08 * yr + 1
    ax.set_ylim(lo, hi)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#9CA3AF", lw=1)
    ax.axvline(0, color="#9CA3AF", lw=1)
    line, = ax.plot([], [], color="#2563EB", lw=2.4, label=f"y = {_lin(a, b)}")
    hline, = ax.plot([], [], color="#E07B39", lw=2.4, label=f"y = {_f(c)}")
    dot, = ax.plot([], [], "o", ms=11, color="#DC2626", zorder=5)
    vline, = ax.plot([], [], "--", color="#DC2626", lw=1.4)
    # the line rises to the right when a > 0: keep the legend and the label off it
    lab = ax.text(x0 + span * 0.05, fc + (-1 if fa > 0 else 1) * (hi - lo) * 0.04, "", color="#DC2626",
                  fontsize=12, fontweight="bold", va="top" if fa > 0 else "bottom")
    ax.legend(loc="upper left" if fa > 0 else "upper right", fontsize=9)
    longest = max(len(t) for t, _ in rows)
    fs = 19 if longest <= 14 else max(11, int(19 * 14 / longest))
    txts = []
    for k, (eq, note) in enumerate(rows):
        t1 = tx.text(0.04, 0.84 - k * 0.2, eq, fontsize=fs, family="DejaVu Sans Mono", color="#111827", alpha=0)
        t2 = tx.text(0.06, 0.77 - k * 0.2, note[0 if tr else 1], fontsize=10, color="#6B7280", alpha=0)
        txts.append((t1, t2))
    tx.set_title("Adım adım çözüm" if tr else "Step by step", fontsize=12, loc="left")
    ax.set_title("Grafikle kontrol: iki doğrunun kesişimi" if tr else
                 "Graphical check: where the lines meet", fontsize=11)
    last = len(txts) - 1
    N = 120

    def update(i):
        for k, (t1, t2) in enumerate(txts):
            al = min(1.0, max(0.0, (i - k * 18) / 12))
            t1.set_alpha(al)
            t2.set_alpha(al)
            t1.set_color("#DC2626" if (k == last and al >= 1.0) else "#111827")
        p = min(1.0, max(0.0, (i - 60) / 30))
        m = int(p * len(xs))
        if m >= 2:
            line.set_data(xs[:m], ys[:m])
            hline.set_data(xs[:m], np.full(m, fc))
        else:
            line.set_data([], [])
            hline.set_data([], [])
        if i >= 92:
            dot.set_data([x0], [fc])
            vline.set_data([x0, x0], [lo, fc])
            lab.set_text(f"x = {_f(xq)}")
        else:
            dot.set_data([], [])
            vline.set_data([], [])
            lab.set_text("")
        return []

    return N, update


def vary(P, rnd):
    try:
        a0, b0, c0 = _abc(P)
        positive = a0 > 0 and b0 > 0 and c0 > b0      # e.g. a fare / price story: keep it all positive
    except (KeyError, ValueError, TypeError):
        positive = False
    if positive:
        a, b, x = rnd.randint(2, 9), rnd.randint(5, 30), rnd.randint(3, 15)
    else:
        a = rnd.choice([2, 3, 4, 5, 6, -2, -3, -4, -5])
        x = rnd.choice([v for v in range(-7, 10) if v != 0])
        b = rnd.choice([v for v in range(-12, 13) if v != 0])
    return {"a": a, "b": b, "c": a * x + b}
''',
}
EXAMPLES += [
    {"id": "alg-lineq-1", "kind": "linear_equation",
     "title": ("İki adımlı denklem", "Two-step equation"),
     "q": ("{lhs} = {c} denklemini x için çöz.", "Solve {lhs} = {c} for x."),
     "P": {"a": 3, "b": 7, "c": 25}},
    {"id": "alg-lineq-2", "kind": "linear_equation",
     "title": ("Negatif katsayılı denklem", "Equation with a negative coefficient"),
     "q": ("{lhs} = {c} ise x kaçtır?", "If {lhs} = {c}, what is x?"),
     "P": {"a": -4, "b": 9, "c": -11}},
    {"id": "alg-lineq-3", "kind": "linear_equation", "topics": ["word problem", "sözel problem"],
     "title": ("Sözel problem: taksi ücreti", "Word problem: taxi fare"),
     "q": ("Bir taksi açılışta {b} TL, her km için {a} TL alıyor. Yolculuk {c} TL tuttu. "
           "Kaç km gidildi? ({lhs} = {c})",
           "A taxi charges {b} lira to start plus {a} lira per km. The ride cost {c} lira. "
           "How many km was the ride? ({lhs} = {c})"),
     "P": {"a": 6, "b": 15, "c": 69}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["line_slope_point"] = {
    "course": "alg",
    "title": ("Eğim ve bir noktadan doğru", "Line from slope and a point"),
    "topics": ["slope", "point slope", "slope intercept", "point slope form", "slope intercept form",
               "linear function", "equation of a line", "equations of lines", "writing equations of lines",
               "graphing lines", "graphing linear equations", "functions and graphing",
               "eğim", "doğrunun eğimi", "doğru denklemi", "doğrunun denklemi", "nokta eğim", "eğim kesen"],
    "code": r'''
import numpy as np
''' + _FRAC + r'''

def _data(P):
    mn, md = _q(P["mn"]), _q(P["md"])
    if md == 0:
        raise ValueError("md = 0: eğim tanımsız (dikey doğru) / md = 0: the slope is undefined (vertical line)")
    if md < 0:
        mn, md = -mn, -md
    x1, y1 = _q(P["x1"]), _q(P["y1"])
    m = mn / md
    return mn, md, m, x1, y1, y1 - m * x1


def _shift(var, s):
    if s == 0:
        return var
    return f"{var} {'-' if s > 0 else '+'} {_f(abs(s))}"


def _ps(m, x1, y1):
    # nokta-eğim biçimi, sadeleştirilmiş: y - 3 = -(1/4)(x + 4)
    left = _shift("y", y1)
    if m == 0:
        return f"{left} = 0"
    inner = _shift("x", x1)
    if inner == "x":
        return f"{left} = {_cx(m)}"
    coef = "" if m == 1 else ("-" if m == -1 else (_f(m) if m.denominator == 1 else f"({_f(m)})"))
    return f"{left} = {coef}({inner})"


def _mtext(mn, md, m):
    raw = _f(mn) if md == 1 else f"{_f(mn)}/{_f(md)}"
    return raw if raw == _f(m) else f"{raw} = {_f(m)}"


def _u(v):
    return "unit" if v == 1 else "units"


def solve(P):
    mn, md, m, x1, y1, b = _data(P)
    si = "y = " + _lin(m, b)
    ps = _ps(m, x1, y1)
    pt = f"({_f(x1)}, {_f(y1)})"
    steps = [
        (f"Verilen: m = {_mtext(mn, md, m)}, nokta {pt}", f"Given: m = {_mtext(mn, md, m)}, point {pt}"),
        ("Nokta-eğim formu: y − y₁ = m(x − x₁)", "Point-slope form: y − y₁ = m(x − x₁)"),
        (f"Yerine koy: y - {_pp(y1)} = {_pp(m)}·(x - {_pp(x1)})  ⇒  {ps}",
         f"Substitute: y - {_pp(y1)} = {_pp(m)}·(x - {_pp(x1)})  ⇒  {ps}"),
        (f"y-kesen: b = y₁ − m·x₁ = {_f(y1)} - {_pp(m)}·{_pp(x1)} = {_f(b)}",
         f"y-intercept: b = y₁ − m·x₁ = {_f(y1)} - {_pp(m)}·{_pp(x1)} = {_f(b)}"),
        (f"Eğim-kesen formu: {si}", f"Slope-intercept form: {si}"),
    ]
    if mn == 0:
        steps.append((f"Eğim 0: doğru yataydır, her noktada y = {_f(y1)}",
                      f"Slope 0: the line is horizontal, y = {_f(y1)} everywhere"))
    else:
        steps.append((f"Eğim {_f(m)}: sağa {_f(md)} birim gidince {_f(abs(mn))} birim {'yukarı' if mn > 0 else 'aşağı'}",
                      f"Slope {_f(m)}: {_f(md)} {_u(md)} right, then {_f(abs(mn))} {_u(abs(mn))} "
                      f"{'up' if mn > 0 else 'down'}"))
    both = si if ps == si else f"{ps}  ⇔  {si}"
    return {"answer": (f"{both}   (y-kesen b = {_f(b)})", f"{both}   (y-intercept b = {_f(b)})"),
            "steps": steps, "fmt": {"m": _f(m), "point": pt}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    mn, md, m, x1, y1, b = _data(P)
    fmn, fmd, fm, fx1, fy1, fb = (float(v) for v in (mn, md, m, x1, y1, b))
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    R = max(8.0, abs(fx1) + fmd + 3, abs(fy1) + abs(fmn) + 3, abs(fb) + 2)
    u = R / 8
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    x2, y2 = fx1 + fmd, fy1 + fmn
    sg = 1 if fm >= 0 else -1
    # labels go where the line is not: for m > 0 the line leaves a point towards
    # lower-left / upper-right, so upper-left and lower-right are free
    p1_pos = (fx1 - 0.35 * u, fy1 + sg * 0.4 * u)
    run_y = fy1 - 0.4 * u if fmn >= 0 else fy1 + 0.4 * u
    rise_pos = (x2 + 0.3 * u, fy1 + fmn / 2)
    obst = [(fx1, fy1), (x2, y2), (fx1 - 1.4 * u, p1_pos[1]), (max(fx1 + fmd / 2, fx1 + 0.95 * u), run_y),
            (rise_pos[0] + 1.2 * u, rise_pos[1]), (x2, fy1)]

    def free(c):
        cx, cy = c[0] * 1.4 * u, fb + c[1] * 0.6 * u
        return min((cx - ox) ** 2 + (cy - oy) ** 2 for ox, oy in obst)

    bq = max([(-1, sg), (1, -sg)], key=free)
    p1, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=5)
    p2, = ax.plot([], [], "o", ms=9, color="#7C3AED", zorder=5)
    run, = ax.plot([], [], color="#E07B39", lw=3)
    rise, = ax.plot([], [], color="#16A34A", lw=3)
    ln, = ax.plot([], [], color="#2563EB", lw=2.4)
    bdot, = ax.plot([], [], "s", ms=9, color="#2563EB", zorder=6)
    t_run = ax.text(max(fx1 + fmd / 2, fx1 + 0.95 * u), run_y, "", color="#E07B39", fontsize=11,
                    fontweight="bold", ha="center", va="top" if fmn >= 0 else "bottom")
    t_rise = ax.text(rise_pos[0], rise_pos[1], "", color="#16A34A", fontsize=11, fontweight="bold",
                     va="center")
    t_p1 = ax.text(p1_pos[0], p1_pos[1], "", color="#DC2626", fontsize=11, ha="right",
                   va="bottom" if sg > 0 else "top")
    t_b = ax.text(bq[0] * 0.3 * u, fb + bq[1] * 0.3 * u, "", color="#2563EB", fontsize=11, fontweight="bold",
                  ha="left" if bq[0] > 0 else "right", va="bottom" if bq[1] > 0 else "top")
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=12,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.92), zorder=8)
    pt = f"({_f(x1)}, {_f(y1)})"
    ax.set_title((f"m = {_f(m)}, nokta {pt}" if tr else f"m = {_f(m)}, point {pt}"), fontsize=12)
    eq = "y = " + _lin(m, b)
    mt = _mtext(mn, md, m)
    run_txt = (f"sağa {_f(md)}" if tr else f"right {_f(md)}")
    rise_txt = "" if mn == 0 else ((f"yukarı {_f(mn)}" if mn > 0 else f"aşağı {_f(-mn)}") if tr else
                                   (f"up {_f(mn)}" if mn > 0 else f"down {_f(-mn)}"))
    N = 130

    def update(i):
        p1.set_data([fx1], [fy1])
        t_p1.set_text(pt)
        pr = min(1.0, max(0.0, (i - 15) / 20))
        if pr > 0:
            run.set_data([fx1, fx1 + fmd * pr], [fy1, fy1])
        else:
            run.set_data([], [])
        t_run.set_text(run_txt if pr > 0.99 else "")
        pu = min(1.0, max(0.0, (i - 38) / 20))
        if pu > 0:
            rise.set_data([x2, x2], [fy1, fy1 + fmn * pu])
        else:
            rise.set_data([], [])
        t_rise.set_text(rise_txt if pu > 0.99 else "")
        if i >= 58:
            p2.set_data([x2], [y2])
        else:
            p2.set_data([], [])
        pl = min(1.0, max(0.0, (i - 62) / 30))
        if pl > 0:
            half = 2 * R * pl
            lx = np.array([fx1 - half, fx1 + half])
            ln.set_data(lx, fy1 + fm * (lx - fx1))
        else:
            ln.set_data([], [])
        if i >= 95:
            bdot.set_data([0], [fb])
            if x1 == 0:
                t_p1.set_text(f"{pt}:  b = {_f(b)}")
            else:
                t_b.set_text(f"b = {_f(b)}")
        else:
            bdot.set_data([], [])
            t_b.set_text("")
        if i < 15:
            info.set_text((f"1) Noktayı işaretle: {pt}") if tr else (f"1) Plot the point {pt}"))
        elif i < 58:
            info.set_text((f"2) Eğim üçgeni: m = yükselme / ilerleme = {mt}") if tr else
                          (f"2) Slope triangle: m = rise / run = {mt}"))
        elif i < 95:
            info.set_text("3) İki noktadan doğruyu çiz" if tr else "3) Draw the line through both points")
        else:
            info.set_text(f"4) {eq}   (b = {_f(b)})")
        return []

    return N, update


def vary(P, rnd):
    from math import gcd
    try:
        mn0, md0, m0, _x, _y, _b = _data(P)
        sign = -1 if m0 < 0 else 1
        integer = m0.denominator == 1
    except (KeyError, ValueError, TypeError):
        sign, integer = 1, False
    while True:
        if integer:
            md, mn = 1, sign * rnd.randint(1, 4)
        else:
            md = rnd.choice([2, 3, 4, 5])
            mn = sign * rnd.choice([k for k in range(1, 5) if gcd(k, md) == 1])
        # x1 a multiple of md keeps the y-intercept an integer
        x1 = md * rnd.choice([k for k in range(-3, 4) if abs(md * k) <= 6])
        y1 = rnd.randint(-5, 5)
        b = y1 - mn * x1 // md
        if abs(b) <= 9:
            return {"mn": mn, "md": md, "x1": x1, "y1": y1}
''',
}
EXAMPLES += [
    {"id": "alg-slope-1", "kind": "line_slope_point",
     "title": ("Eğim-kesen formu", "Slope-intercept form"),
     "q": ("Eğimi {m} olan ve {point} noktasından geçen doğrunun denklemini bul.",
           "Find the equation of the line with slope {m} passing through {point}."),
     "P": {"mn": 2, "md": 3, "x1": 0, "y1": -1}},
    {"id": "alg-slope-2", "kind": "line_slope_point",
     "title": ("Nokta-eğim formu", "Point-slope form"),
     "q": ("m = {m} ve {point} noktası veriliyor. Doğruyu nokta-eğim ve eğim-kesen formunda yaz.",
           "Given m = {m} and the point {point}, write the line in point-slope and slope-intercept form."),
     "P": {"mn": -1, "md": 4, "x1": -4, "y1": 3}},
    {"id": "alg-slope-3", "kind": "line_slope_point",
     "title": ("Negatif tam sayı eğim", "Negative integer slope"),
     "q": ("{point} noktasından geçen ve eğimi {m} olan doğrunun y-kesenini bul.",
           "Find the y-intercept of the line through {point} with slope {m}."),
     "P": {"mn": -3, "md": 1, "x1": 2, "y1": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["line_two_points"] = {
    "course": "alg",
    "title": ("İki noktadan geçen doğru", "Line through two points"),
    "topics": ["two points", "slope formula", "slope", "slope from two points", "slope between two points",
               "line through two points", "rate of change", "equation of a line",
               "iki nokta", "iki noktası bilinen", "iki noktadan geçen doğru", "eğim formülü", "eğim",
               "değişim oranı"],
    "code": r'''
import numpy as np
''' + _FRAC + r'''

def _pts(P):
    x1, y1, x2, y2 = (_q(P[k]) for k in ("x1", "y1", "x2", "y2"))
    if x1 == x2 and y1 == y2:
        raise ValueError("A ve B aynı nokta: tek bir doğru belirlenemez / A and B coincide: no unique line")
    return x1, y1, x2, y2


def _sgn(v):
    return (v > 0) - (v < 0)


def solve(P):
    x1, y1, x2, y2 = _pts(P)
    A, B = f"({_f(x1)}, {_f(y1)})", f"({_f(x2)}, {_f(y2)})"
    fmt = {"A": A, "B": B}
    if x1 == x2:
        return {"answer": (f"Eğim tanımsız (dikey doğru): x = {_f(x1)}",
                           f"Undefined slope (vertical line): x = {_f(x1)}"),
                "steps": [(f"A{A}, B{B}", f"A{A}, B{B}"),
                          (f"Δx = x₂ − x₁ = {_f(x2)} - {_pp(x1)} = 0  ⇒  eğim tanımsız, doğru dikeydir",
                           f"Δx = x₂ − x₁ = {_f(x2)} - {_pp(x1)} = 0  ⇒  the slope is undefined, the line is vertical"),
                          (f"Denklem: x = {_f(x1)}", f"Equation: x = {_f(x1)}")],
                "fmt": fmt}
    dy, dx = y2 - y1, x2 - x1
    m = dy / dx
    b = y1 - m * x1
    raw = f"{_f(dy)}/{_pp(dx)}"
    mt = raw if raw == _f(m) else f"{raw} = {_f(m)}"
    eq = "y = " + _lin(m, b)
    chk = f"{_pp(m)}·{_pp(x2)}" + (f" {'+' if b > 0 else '-'} {_f(abs(b))}" if b != 0 else "")
    steps = [
        (f"A{A}, B{B}", f"A{A}, B{B}"),
        (f"Eğim: m = (y₂ − y₁)/(x₂ − x₁) = ({_f(y2)} - {_pp(y1)})/({_f(x2)} - {_pp(x1)}) = {mt}",
         f"Slope: m = (y₂ − y₁)/(x₂ − x₁) = ({_f(y2)} - {_pp(y1)})/({_f(x2)} - {_pp(x1)}) = {mt}"),
        (f"y-kesen: b = y₁ − m·x₁ = {_f(y1)} - {_pp(m)}·{_pp(x1)} = {_f(b)}",
         f"y-intercept: b = y₁ − m·x₁ = {_f(y1)} - {_pp(m)}·{_pp(x1)} = {_f(b)}"),
        (f"Denklem: {eq}", f"Equation: {eq}"),
        (f"Kontrol (B noktası): {chk} = {_f(m * x2 + b)} = y₂ ✓", f"Check (point B): {chk} = {_f(m * x2 + b)} = y₂ ✓"),
    ]
    return {"answer": f"m = {_f(m)};  {eq}", "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    qx1, qy1, qx2, qy2 = _pts(P)
    x1, y1, x2, y2 = float(qx1), float(qy1), float(qx2), float(qy2)
    dx, dy = x2 - x1, y2 - y1
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    R = max(8.0, abs(x1) + 2, abs(x2) + 2, abs(y1) + 2, abs(y2) + 2)
    u = R / 8
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    vertical = dx == 0
    sm = 0 if vertical else _sgn(dy / dx)
    # A: away from the horizontal leg; B: beyond the vertical leg; both on the free side of the line
    if vertical:
        qa, qb = (1, -_sgn(dy)), (1, _sgn(dy))
    else:
        sxa = -_sgn(dx)
        qa = (sxa, -sxa * sm if sm else 1)
        syb = _sgn(dy) if dy else 1
        qb = (-syb * sm if sm else _sgn(dx), syb)

    def lab(x, y, q, color):
        return ax.text(x + q[0] * 0.3 * u, y + q[1] * 0.35 * u, "", color=color, fontsize=11, fontweight="bold",
                       ha="left" if q[0] > 0 else "right", va="bottom" if q[1] > 0 else "top")

    pa, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=5)
    pb, = ax.plot([], [], "o", ms=10, color="#7C3AED", zorder=5)
    dxl, = ax.plot([], [], color="#E07B39", lw=3)
    dyl, = ax.plot([], [], color="#16A34A", lw=3)
    ln, = ax.plot([], [], color="#2563EB", lw=2.4)
    bdot, = ax.plot([], [], "s", ms=8, color="#2563EB", zorder=6)
    ta = lab(x1, y1, qa, "#DC2626")
    tb = lab(x2, y2, qb, "#7C3AED")
    up = _sgn(dy) if dy else 1
    # keep the Δx label clear of A (the line passes through A): never closer than ~1 label half-width
    tdx = ax.text(x1 + (_sgn(dx) or 1) * max(abs(dx) / 2, 0.95 * u), y1 - up * 0.35 * u, "", color="#E07B39",
                  fontsize=11, fontweight="bold",
                  ha="center", va="top" if up > 0 else "bottom")
    side = _sgn(dx) if dx else 1
    tdy = ax.text(x2 + side * 0.3 * u, (y1 + y2) / 2, "", color="#16A34A", fontsize=11, fontweight="bold",
                  ha="left" if side > 0 else "right", va="center")
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=12,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.92), zorder=8)
    sol = solve(P)
    ans = sol["answer"] if isinstance(sol["answer"], str) else sol["answer"][0 if tr else 1]
    A, B = sol["fmt"]["A"], sol["fmt"]["B"]
    ax.set_title(f"A{A}, B{B}", fontsize=12)
    if not vertical:
        mq = (qy2 - qy1) / (qx2 - qx1)
        bq = qy1 - mq * qx1
        mt = f"{_f(qy2 - qy1)}/{_pp(qx2 - qx1)}"
        mt = mt if mt == _f(mq) else f"{mt} = {_f(mq)}"
    N = 120

    def update(i):
        pa.set_data([x1], [y1])
        ta.set_text("A" + A)
        if i >= 10:
            pb.set_data([x2], [y2])
            tb.set_text("B" + B)
        else:
            pb.set_data([], [])
            tb.set_text("")
        p = min(1.0, max(0.0, (i - 22) / 20))
        if p > 0 and not vertical:
            dxl.set_data([x1, x1 + dx * p], [y1, y1])
        else:
            dxl.set_data([], [])
        tdx.set_text(f"Δx = {_f(qx2 - qx1)}" if p > 0.99 and not vertical else "")
        q = min(1.0, max(0.0, (i - 45) / 20))
        if q > 0 and dy != 0:
            dyl.set_data([x2, x2], [y1, y1 + dy * q])
        else:
            dyl.set_data([], [])
        tdy.set_text(f"Δy = {_f(qy2 - qy1)}" if q > 0.99 else "")
        r = min(1.0, max(0.0, (i - 75) / 25))
        if r > 0:
            if vertical:
                ln.set_data([x1, x1], [-R * r, R * r])
            else:
                lx = np.array([x1 - 2 * R * r, x1 + 2 * R * r])
                ln.set_data(lx, y1 + float(mq) * (lx - x1))
        else:
            ln.set_data([], [])
        if i >= 100 and not vertical and abs(float(bq)) <= R:
            bdot.set_data([0], [float(bq)])
        else:
            bdot.set_data([], [])
        if i < 22:
            info.set_text("1) Noktaları işaretle" if tr else "1) Plot both points")
        elif i < 66:
            info.set_text("2) Δx ve Δy'yi ölç" if tr else "2) Measure Δx and Δy")
        elif vertical:
            info.set_text("3) " + ans)
        elif i < 100:
            info.set_text(f"2) m = Δy / Δx = {mt}")
        else:
            info.set_text(f"3) m = {_f(mq)}, b = {_f(bq)}  ⇒  y = {_lin(mq, bq)}")
        return []

    return N, update


def vary(P, rnd):
    try:
        x1, y1, x2, y2 = _pts(P)
        sign = 0 if x1 == x2 else _sgn((y2 - y1) / (x2 - x1))
    except (KeyError, ValueError, TypeError):
        sign = 1
    if sign == 0:
        sign = rnd.choice([-1, 1])
    while True:
        q = rnd.choice([1, 2, 3])
        p = sign * rnd.choice([k for k in range(1, 5) if k % q != 0 or q == 1])
        b = rnd.randint(-4, 4)
        xs = [q * k for k in range(-3, 4) if abs(q * k) <= 6]
        xa, xb = rnd.sample(xs, 2)
        ya, yb = b + p * xa // q, b + p * xb // q
        if max(abs(ya), abs(yb)) <= 7:
            return {"x1": xa, "y1": ya, "x2": xb, "y2": yb}
''',
}
EXAMPLES += [
    {"id": "alg-2pt-1", "kind": "line_two_points",
     "title": ("İki noktadan eğim", "Slope from two points"),
     "q": ("{A} ve {B} noktalarından geçen doğrunun eğimini ve denklemini bul.",
           "Find the slope and the equation of the line through {A} and {B}."),
     "P": {"x1": -3, "y1": -1, "x2": 3, "y2": 3}},
    {"id": "alg-2pt-2", "kind": "line_two_points",
     "title": ("Azalan doğru", "Decreasing line"),
     "q": ("{A} ve {B} noktalarını birleştiren doğrunun denklemi nedir?",
           "What is the equation of the line joining {A} and {B}?"),
     "P": {"x1": -2, "y1": 5, "x2": 4, "y2": -4}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["system_2x2"] = {
    "course": "alg",
    "title": ("İki bilinmeyenli denklem sistemi", "System of two linear equations"),
    "topics": ["systems of equations", "system of equations", "systems of linear equations",
               "system of linear equations", "linear systems", "solving systems", "simultaneous equations",
               "elimination method", "substitution method", "solving by elimination", "systems by elimination",
               "systems by substitution", "systems by graphing", "intersection of lines",
               "denklem sistemi", "denklem sistemleri", "doğrusal denklem sistemi", "iki bilinmeyenli",
               "yok etme yöntemi", "yerine koyma yöntemi", "ortak çözüm"],
    "code": r'''
import numpy as np
from math import gcd
''' + _FRAC + r'''

def _side(a, b):
    def term(c, v, first):
        if c == 0:
            return ""
        mag = "" if abs(c) == 1 else _f(abs(c))
        if first:
            return ("-" if c < 0 else "") + mag + v
        return (" - " if c < 0 else " + ") + mag + v
    s = term(a, "x", True)
    s += term(b, "y", s == "")
    return s or "0"


def _coefs(P):
    a1, b1, c1, a2, b2, c2 = (_q(P[k]) for k in ("a1", "b1", "c1", "a2", "b2", "c2"))
    if (a1 == 0 and b1 == 0) or (a2 == 0 and b2 == 0):
        raise ValueError("Her denklemde x ya da y katsayısı sıfırdan farklı olmalı / "
                         "each equation needs a non-zero x or y coefficient")
    return a1, b1, c1, a2, b2, c2


def _xy(a, b, x):
    # a·x + b·y with the value of x already substituted
    if a == 0:
        return _cx(b, "y")
    left = _pp(x) if a == 1 else (f"-{_pp(x)}" if a == -1 else f"{_pp(a)}·{_pp(x)}")
    if b == 0:
        return left
    return f"{left} {'+' if b > 0 else '-'} {_cx(abs(b), 'y')}"


def solve(P):
    a1, b1, c1, a2, b2, c2 = _coefs(P)
    det = a1 * b2 - a2 * b1
    e1 = f"{_side(a1, b1)} = {_f(c1)}"
    e2 = f"{_side(a2, b2)} = {_f(c2)}"
    fmt = {"eq1": e1, "eq2": e2}
    if det == 0:
        same = (a1 * c2 == a2 * c1) and (b1 * c2 == b2 * c1)
        msg = (("Doğrular çakışık: sonsuz çözüm", "Same line: infinitely many solutions") if same
               else ("Doğrular paralel: çözüm yok", "Parallel lines: no solution"))
        d = f"a₁b₂ − a₂b₁ = {_pp(a1)}·{_pp(b2)} - {_pp(a2)}·{_pp(b1)} = 0"
        return {"answer": msg, "steps": [(f"(1) {e1}    (2) {e2}", f"(1) {e1}    (2) {e2}"),
                                         (f"{d}  ⇒  eğimler eşit", f"{d}  ⇒  equal slopes"), msg],
                "fmt": fmt}
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    steps = [(f"(1) {e1}    (2) {e2}", f"(1) {e1}    (2) {e2}")]
    if b1 == 0 or b2 == 0:
        j, a, c = (1, a1, c1) if b1 == 0 else (2, a2, c2)
        tail = "" if a == 1 else f"  ⇒  x = {_pp(c)}/{_pp(a)} = {_f(x)}"
        steps.append((f"({j}) denkleminde y yok: {_cx(a)} = {_f(c)}{tail}",
                      f"Equation ({j}) has no y: {_cx(a)} = {_f(c)}{tail}"))
    else:
        if all(v.denominator == 1 for v in (b1, b2)):
            B1, B2 = abs(b1.numerator), abs(b2.numerator)
            L = B1 * B2 // gcd(B1, B2)
            k1, k2 = Fraction(L, B1), Fraction(L, B2)
        else:
            k1, k2 = abs(b2), abs(b1)
        add = (b1 > 0) != (b2 > 0)          # opposite y-coefficients: add the equations
        A1, Y1, C1 = a1 * k1, b1 * k1, c1 * k1
        A2, Y2, C2 = a2 * k2, b2 * k2, c2 * k2
        r1 = f"{_side(A1, Y1)} = {_f(C1)}"
        r2 = f"{_side(A2, Y2)} = {_f(C2)}"
        mt, me = [], []
        if k1 != 1:
            mt.append(f"(1)'i {_f(k1)} ile")
            me.append(f"(1) by {_f(k1)}")
        if k2 != 1:
            mt.append(f"(2)'yi {_f(k2)} ile")
            me.append(f"(2) by {_f(k2)}")
        if mt:
            steps.append((f"y'yi yok etmek için {' ve '.join(mt)} çarp:  {r1}  ;  {r2}",
                          f"To eliminate y multiply {' and '.join(me)}:  {r1}  ;  {r2}"))
        else:
            steps.append(("y katsayıları zaten eşit büyüklükte", "The y-coefficients already have equal size"))
        op = "+" if add else "-"
        D = A1 + A2 if add else A1 - A2
        Rr = C1 + C2 if add else C1 - C2
        steps.append(((f"Taraf tarafa {'topla' if add else 'çıkar'}: ({_f(A1)} {op} {_pp(A2)})x = "
                       f"{_f(C1)} {op} {_pp(C2)}  ⇒  {_cx(D)} = {_f(Rr)}"),
                      (f"{'Add' if add else 'Subtract'} the equations: ({_f(A1)} {op} {_pp(A2)})x = "
                       f"{_f(C1)} {op} {_pp(C2)}  ⇒  {_cx(D)} = {_f(Rr)}")))
        if D != 1:
            steps.append((f"x = {_pp(Rr)}/{_pp(D)} = {_f(x)}", f"x = {_pp(Rr)}/{_pp(D)} = {_f(x)}"))
    # substitute into the equation with the simplest y-coefficient
    rows = [(abs(b) != 1, abs(a), j, a, b, c) for j, a, b, c in ((1, a1, b1, c1), (2, a2, b2, c2)) if b != 0]
    _, _, j, a, b, c = min(rows)
    mid = "" if b == 1 else f"  ⇒  {_cx(b, 'y')} = {_f(c - a * x)}"
    steps.append((f"x = {_f(x)} değerini ({j})'de yerine koy: {_xy(a, b, x)} = {_f(c)}{mid}  ⇒  y = {_f(y)}",
                  f"Substitute x = {_f(x)} into ({j}): {_xy(a, b, x)} = {_f(c)}{mid}  ⇒  y = {_f(y)}"))
    k1s = f"{_pp(a1)}·{_pp(x)} + {_pp(b1)}·{_pp(y)} = {_f(a1 * x + b1 * y)}"
    k2s = f"{_pp(a2)}·{_pp(x)} + {_pp(b2)}·{_pp(y)} = {_f(a2 * x + b2 * y)}"
    steps.append((f"Kontrol: (1) {k1s} ✓   (2) {k2s} ✓", f"Check: (1) {k1s} ✓   (2) {k2s} ✓"))
    steps.append((f"Kesişim noktası: ({_f(x)}, {_f(y)})", f"Intersection point: ({_f(x)}, {_f(y)})"))
    return {"answer": f"x = {_f(x)}, y = {_f(y)}", "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    Q = _coefs(P)
    a1, b1, c1, a2, b2, c2 = (float(v) for v in Q)
    det = a1 * b2 - a2 * b1
    qdet = Q[0] * Q[4] - Q[3] * Q[1]
    point = "" if qdet == 0 else (f"({_f((Q[2] * Q[4] - Q[5] * Q[1]) / qdet)}, "
                                  f"{_f((Q[0] * Q[5] - Q[3] * Q[2]) / qdet)})")
    if det != 0:
        cx = (c1 * b2 - c2 * b1) / det
        cy = (a1 * c2 - a2 * c1) / det
        R = max(8.0, abs(cx) * 0.3 + 4, abs(cy) * 0.3 + 4)
        if abs(cx) < R * 0.9 and abs(cy) < R * 0.9:
            R = max(R, abs(cx) + 3, abs(cy) + 3)
    else:
        # parallel / same lines: centre between the points of each line closest to the origin
        t1, t2 = c1 / (a1 * a1 + b1 * b1), c2 / (a2 * a2 + b2 * b2)
        px1, py1, px2, py2 = a1 * t1, b1 * t1, a2 * t2, b2 * t2
        cx, cy = (px1 + px2) / 2, (py1 + py2) / 2
        R = max(8.0, 0.8 * ((px1 - px2) ** 2 + (py1 - py2) ** 2) ** 0.5 + 3)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    ax.set_xlim(cx - R, cx + R)
    ax.set_ylim(cy - R, cy + R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    sol = solve(P)
    ans = sol["answer"] if isinstance(sol["answer"], str) else sol["answer"][0 if tr else 1]

    def seg(a, b, c):
        if b != 0:
            xs = np.linspace(cx - R, cx + R, 200)
            return xs, (c - a * xs) / b
        ys = np.linspace(cy - R, cy + R, 200)
        return np.full_like(ys, c / a), ys

    X1, Y1 = seg(a1, b1, c1)
    X2, Y2 = seg(a2, b2, c2)
    # put the legend and the info box into the two emptiest corners (decided once: seek-safe)
    U = (np.concatenate([X1, X2]) - (cx - R)) / (2 * R)
    V = (np.concatenate([Y1, Y2]) - (cy - R)) / (2 * R)
    corners = {"upper left": (U < 0.45) & (V > 0.76), "upper right": (U > 0.55) & (V > 0.76),
               "lower left": (U < 0.45) & (V < 0.24), "lower right": (U > 0.55) & (V < 0.24)}
    order = sorted(corners, key=lambda k: (int(corners[k].sum()), list(corners).index(k)))
    leg_loc, info_loc = order[0], order[1]
    l1, = ax.plot([], [], color="#2563EB", lw=2.4, label="(1) " + sol["fmt"]["eq1"])
    l2, = ax.plot([], [], color="#E07B39", lw=2.4, label="(2) " + sol["fmt"]["eq2"])
    dot, = ax.plot([], [], "o", color="#DC2626", ms=12, zorder=6)
    ring, = ax.plot([], [], "o", mfc="none", mec="#DC2626", ms=12, zorder=6)
    ax.legend(loc=leg_loc, fontsize=10)
    ix = 0.02 if "left" in info_loc else 0.98
    iy = 0.97 if "upper" in info_loc else 0.03
    info = ax.text(ix, iy, "", transform=ax.transAxes, fontsize=11, ha="left" if ix < 0.5 else "right",
                   va="top" if iy > 0.5 else "bottom", zorder=8,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.92))
    # solution label: in the widest angular gap between the two lines
    rays = sorted(float(np.arctan2(-a, b)) % np.pi + k * np.pi for a, b in ((a1, b1), (a2, b2)) for k in (0, 1))
    gaps = [(rays[(k + 1) % 4] - rays[k]) % (2 * np.pi) for k in range(4)]
    k0 = int(np.argmax(gaps))
    phi = rays[k0] + gaps[k0] / 2
    co, si = float(np.cos(phi)), float(np.sin(phi))
    lab = ax.text(cx + 0.07 * R * co, cy + 0.07 * R * si, "", color="#DC2626", fontsize=13, fontweight="bold",
                  ha="left" if co > 0.3 else ("right" if co < -0.3 else "center"),
                  va="bottom" if si > 0.3 else ("top" if si < -0.3 else "center"), zorder=7)
    N = 120

    def update(i):
        p = min(1.0, max(0.0, i / 35))
        m1 = int(p * len(X1))
        l1.set_data(X1[:m1], Y1[:m1]) if m1 >= 2 else l1.set_data([], [])
        q = min(1.0, max(0.0, (i - 38) / 35))
        m2 = int(q * len(X2))
        l2.set_data(X2[:m2], Y2[:m2]) if m2 >= 2 else l2.set_data([], [])
        if i >= 78 and det != 0:
            dot.set_data([cx], [cy])
            ring.set_data([cx], [cy])
            ring.set_markersize(12 + 18 * ((i - 78) % 20) / 20)
            lab.set_text(point)
        else:
            dot.set_data([], [])
            ring.set_data([], [])
            lab.set_text("")
        if i < 38:
            info.set_text(("1) (1) doğrusunu çiz" if tr else "1) Draw line (1)"))
        elif i < 78:
            info.set_text(("2) (2) doğrusunu çiz" if tr else "2) Draw line (2)"))
        elif det != 0:
            info.set_text(("3) Kesişim = ortak çözüm: " if tr else "3) Crossing point = solution: ") + ans)
        else:
            info.set_text("3) " + ans)
        return []

    ax.set_title("Her doğru bir denklem; kesişim noktası ortak çözümdür" if tr else
                 "Each line is one equation; the crossing point solves both", fontsize=11)
    return N, update


def vary(P, rnd):
    try:
        positive = all(v > 0 for v in _coefs(P))       # e.g. a ticket / price story
    except (KeyError, ValueError, TypeError):
        positive = False
    while True:
        if positive:
            y = rnd.choice([10, 15, 20, 25, 30])
            x = y + rnd.choice([5, 10, 15, 20])
            a1, b1, a2, b2 = (rnd.randint(1, 5) for _ in range(4))
        else:
            x, y = rnd.randint(-5, 5), rnd.randint(-5, 5)
            a1, b1, a2, b2 = (rnd.choice([-3, -2, -1, 1, 2, 3, 4]) for _ in range(4))
        if a1 * b2 - a2 * b1 != 0:
            return {"a1": a1, "b1": b1, "c1": a1 * x + b1 * y, "a2": a2, "b2": b2, "c2": a2 * x + b2 * y}
''',
}
EXAMPLES += [
    {"id": "alg-sys-1", "kind": "system_2x2",
     "title": ("Yok etme yöntemi", "Elimination method"),
     "q": ("Sistemi çöz:  {eq1}  ve  {eq2}", "Solve the system:  {eq1}  and  {eq2}"),
     "P": {"a1": 2, "b1": 3, "c1": 12, "a2": 1, "b2": -1, "c2": 1}},
    {"id": "alg-sys-2", "kind": "system_2x2",
     "title": ("Yerine koyma yöntemi", "Substitution method"),
     "q": ("{eq1} ve {eq2} denklemlerini aynı anda sağlayan (x, y) nedir?",
           "Which (x, y) satisfies both {eq1} and {eq2}?"),
     "P": {"a1": 1, "b1": 1, "c1": 7, "a2": 3, "b2": -2, "c2": 1}},
    {"id": "alg-sys-3", "kind": "system_2x2", "topics": ["word problem", "sözel problem"],
     "title": ("Sözel problem: bilet satışı", "Word problem: ticket sales"),
     "q": ("Bir sinemada {a1} yetişkin ve {b1} öğrenci bileti toplam {c1} TL, {a2} yetişkin ve {b2} öğrenci "
           "bileti toplam {c2} TL tutuyor. Yetişkin bileti x TL, öğrenci bileti y TL ise fiyatları bul. "
           "({eq1}; {eq2})",
           "At a cinema, {a1} adult and {b1} student tickets cost {c1} lira in total, while {a2} adult and "
           "{b2} student tickets cost {c2} lira. If an adult ticket costs x and a student ticket y, "
           "find both prices. ({eq1}; {eq2})"),
     "P": {"a1": 2, "b1": 3, "c1": 120, "a2": 1, "b2": 1, "c2": 50}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["quadratic"] = {
    "course": "alg",
    "title": ("İkinci derece denklem ve parabol", "Quadratic equation and parabola"),
    "topics": ["quadratic", "quadratics", "quadratic equation", "quadratic formula", "quadratic function",
               "discriminant", "parabola", "graphing parabolas", "completing the square", "factoring quadratics",
               "factoring trinomials", "solving by factoring", "vertex form", "vertex of a parabola",
               "axis of symmetry", "projectile motion",
               "ikinci dereceden", "ikinci derece", "parabol", "diskriminant", "kök formülü", "tepe noktası",
               "simetri ekseni", "çarpanlara ayırma"],
    "code": r'''
import math
import numpy as np
''' + _FRAC + r'''

def _cf(v):
    # coefficient text: 3, 4.9 (terminating decimals as typed), (1/3) for other fractions
    v = Fraction(v)
    if v.denominator == 1:
        return str(v.numerator)
    d = v.denominator
    while d % 2 == 0:
        d //= 2
    while d % 5 == 0:
        d //= 5
    if d == 1 and v.denominator <= 10000:
        return f"{float(v):.6g}"
    return f"({_f(v)})"


def _poly(a, b, c, v="x"):
    terms = []
    for coef, pw in ((a, v + "²"), (b, v), (c, "")):
        if coef == 0:
            continue
        mag = abs(coef)
        body = ("" if (mag == 1 and pw) else (_cf(mag) if pw else _f(mag) if mag.denominator == 1 else _cf(mag).strip("()"))) + pw
        terms.append(("-" if coef < 0 else "+", body))
    if not terms:
        return "0"
    out = ("-" if terms[0][0] == "-" else "") + terms[0][1]
    for sgn, body in terms[1:]:
        out += f" {sgn} {body}"
    return out


def _abc(P):
    a, b, c = _q(P["a"]), _q(P["b"]), _q(P["c"])
    if a == 0:
        raise ValueError("a = 0: denklem ikinci dereceden değil / a = 0: the equation is not quadratic")
    return a, b, c


def _isqrt_parts(n):
    # n = k² · s, s squarefree as far as small factors go
    k, s, p = 1, n, 2
    while p * p <= s and p < 2000:
        while s % (p * p) == 0:
            s //= p * p
            k *= p
        p += 1
    return k, s


def _num(v):
    # decimals for plot labels / physical quantities: 12.25, -5.125, 45
    return f"{float(v):.4g}"


def _roots_text(a, b, D, v):
    # exact roots of a·v² + b·v + c from Δ = D (Fraction). Returns (formula text, roots or None, approx)
    absd = abs(D)
    k, s = _isqrt_parts(absd.numerator * absd.denominator)
    den = Fraction(1, absd.denominator)      # √(p/q) = √(p·q)/q
    rad = k * den                            # √|Δ| = rad·√s
    i = "i" if D < 0 else ""
    if all(t.denominator == 1 for t in (a, b, rad)):
        nb, kk, d2 = int(-b), int(rad), int(2 * a)
        g = math.gcd(math.gcd(abs(nb), abs(kk)), abs(d2)) or 1
        nb, kk, d2 = nb // g, kk // g, d2 // g
        if d2 < 0:
            nb, d2 = -nb, -d2
        root = (f"{i}√{s}" if kk == 1 else f"{kk}{i}√{s}") if s != 1 else (i if kk == 1 else f"{kk}{i}")
        if not i and s == 1:
            root = str(kk)
        core = f"{nb} ± {root}" if nb != 0 else f"±{root}"
        if d2 == 1:
            return core
        return f"({core})/{d2}"
    re_, co = -b / (2 * a), abs(rad / (2 * a))
    cs = "" if co == 1 else (_f(co) if co.denominator == 1 else f"({_f(co)})")
    root = cs + i + (f"√{s}" if s != 1 else "")
    if not root:
        root = "1"
    return (f"{_f(re_)} ± {root}") if re_ != 0 else f"±{root}"


def _analyse(P):
    a, b, c = _abc(P)
    proj = P.get("ctx") == "projectile"
    v = "t" if proj else str(P.get("var", "x"))[:3] or "x"
    D = b * b - 4 * a * c
    xv = -b / (2 * a)
    yv = a * xv * xv + b * xv + c
    k, s = _isqrt_parts(abs(D).numerator * abs(D).denominator) if D != 0 else (0, 1)
    rational = D >= 0 and s == 1
    roots = []
    if D > 0:
        if rational:
            rD = Fraction(k, abs(D).denominator)     # √Δ, exact
            roots = sorted([(-b - rD) / (2 * a), (-b + rD) / (2 * a)])
        else:
            r = math.sqrt(float(D))
            roots = sorted([(-float(b) - r) / (2 * float(a)), (-float(b) + r) / (2 * float(a))])
    elif D == 0:
        roots = [xv]
    proj = proj and a < 0 and D > 0 and float(roots[-1]) > 0
    return a, b, c, D, xv, yv, roots, rational, v, proj


def solve(P):
    a, b, c, D, xv, yv, roots, rational, v, proj = _analyse(P)
    steps = [
        (f"a = {_f(a)}, b = {_f(b)}, c = {_f(c)}", f"a = {_f(a)}, b = {_f(b)}, c = {_f(c)}"),
        (f"Diskriminant: Δ = b² − 4ac = {_pp(b)}² - 4·{_pp(a)}·{_pp(c)} = {_f(D)}",
         f"Discriminant: Δ = b² − 4ac = {_pp(b)}² - 4·{_pp(a)}·{_pp(c)} = {_f(D)}"),
    ]
    sub = "₁", "₂"
    if D > 0:
        steps.append(("Δ > 0 ⇒ iki farklı reel kök", "Δ > 0 ⇒ two distinct real roots"))
        if rational:
            rD = (roots[1] - roots[0]) * abs(a)              # x₂ − x₁ = √Δ/|a|  ⇒  √Δ
            steps.append((f"√Δ = √{_f(D)} = {_f(rD)};   {v} = (−b ± √Δ) / 2a = ({_f(-b)} ± {_f(rD)}) / {_pp(2 * a)}",
                          f"√Δ = √{_f(D)} = {_f(rD)};   {v} = (−b ± √Δ) / 2a = ({_f(-b)} ± {_f(rD)}) / {_pp(2 * a)}"))
            s1, s2 = ("-", "+") if a > 0 else ("+", "-")      # which sign gives the smaller root
            r1t = f"{v}{sub[0]} = ({_f(-b)} {s1} {_f(rD)})/{_pp(2 * a)} = {_f(roots[0])}"
            r2t = f"{v}{sub[1]} = ({_f(-b)} {s2} {_f(rD)})/{_pp(2 * a)} = {_f(roots[1])}"
            steps.append((f"{r1t},   {r2t}", f"{r1t},   {r2t}"))
            ans = f"{v}{sub[0]} = {_f(roots[0])}, {v}{sub[1]} = {_f(roots[1])}"
        else:
            ex = _roots_text(a, b, D, v)
            steps.append((f"{v} = (−b ± √Δ) / 2a = ({_f(-b)} ± √{_f(D)}) / {_pp(2 * a)} = {ex}",
                          f"{v} = (−b ± √Δ) / 2a = ({_f(-b)} ± √{_f(D)}) / {_pp(2 * a)} = {ex}"))
            ans = f"{v} = {ex}  ≈ {roots[0]:.4g}, {roots[1]:.4g}"
    elif D == 0:
        steps.append((f"Δ = 0 ⇒ çift (tek) kök: {v} = −b/2a = {_pp(-b)}/{_pp(2 * a)} = {_f(xv)}",
                      f"Δ = 0 ⇒ one repeated root: {v} = −b/2a = {_pp(-b)}/{_pp(2 * a)} = {_f(xv)}"))
        ans = (f"{v} = {_f(xv)}  (çift kök)", f"{v} = {_f(xv)}  (double root)")
    else:
        ex = _roots_text(a, b, D, v)
        steps.append(("Δ < 0 ⇒ reel kök yok (parabol x eksenini kesmez); kökler karmaşık eşleniktir",
                      "Δ < 0 ⇒ no real roots (the parabola misses the x-axis); the roots are complex conjugates"))
        steps.append((f"{v} = (−b ± √Δ) / 2a = ({_f(-b)} ± √({_f(D)})) / {_pp(2 * a)} = {ex}",
                      f"{v} = (−b ± √Δ) / 2a = ({_f(-b)} ± √({_f(D)})) / {_pp(2 * a)} = {ex}"))
        ans = (f"Reel kök yok; {v} = {ex}", f"No real roots; {v} = {ex}")
    vfrac = f"{_pp(-b)}/{_pp(2 * a)}"
    vfrac = "" if vfrac == _f(xv) else vfrac + " = "
    yn = "h" if proj else "y"
    steps.append((f"Tepe noktası: {v} = −b/2a = {vfrac}{_f(xv)},  {yn} = {_f(yv)}",
                  f"Vertex: {v} = −b/2a = {vfrac}{_f(xv)},  {yn} = {_f(yv)}"))
    steps.append((f"Simetri ekseni: {v} = {_f(xv)};  a {'>' if a > 0 else '<'} 0 ⇒ parabol {'yukarı' if a > 0 else 'aşağı'} açılır",
                  f"Axis of symmetry: {v} = {_f(xv)};  a {'>' if a > 0 else '<'} 0 ⇒ opens {'up' if a > 0 else 'down'}"))
    if proj:
        t1, t2 = roots
        land = _f(t2) if rational else f"{t2:.4g}"
        neg = _f(t1) if rational else f"{t1:.4g}"
        steps.append((f"Başlangıç yüksekliği: h(0) = c = {_num(c)} m", f"Initial height: h(0) = c = {_num(c)} m"))
        if float(t1) < 0:
            steps.append((f"Yere düşme anı h(t) = 0: t = {neg} < 0 olamaz (zaman negatif değil) ⇒ t = {land} s",
                          f"Landing time h(t) = 0: t = {neg} < 0 is rejected (time is not negative) ⇒ t = {land} s"))
        else:
            steps.append((f"Yere düşme anı h(t) = 0 ⇒ t = {land} s", f"Landing time h(t) = 0 ⇒ t = {land} s"))
        steps.append((f"En yüksek nokta tepe noktasıdır: t = {_num(xv)} s anında h = {_num(yv)} m",
                      f"The peak is the vertex: h = {_num(yv)} m at t = {_num(xv)} s"))
        ans = (f"Top t = {land} s anında yere düşer; en yüksek nokta h = {_num(yv)} m (t = {_num(xv)} s)",
               f"The ball lands at t = {land} s; maximum height h = {_num(yv)} m at t = {_num(xv)} s")
    return {"answer": ans, "steps": steps, "fmt": {"expr": _poly(a, b, c, v)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    qa, qb, qc, qD, qxv, qyv, qroots, rational, v, proj = _analyse(P)
    a, b, c, D = float(qa), float(qb), float(qc), float(qD)
    xv, yv = float(qxv), float(qyv)
    roots = [float(r) for r in qroots] if D > 0 else ([xv] if D == 0 else [])
    sol = solve(P)
    ans = sol["answer"] if isinstance(sol["answer"], str) else sol["answer"][0 if tr else 1]
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.1)
    if proj:
        tl = roots[1]
        xs = np.linspace(0.0, tl, 300)
        xlo, xhi = -0.04 * tl, tl * 1.06
    else:
        span = max([4.0] + [abs(r - xv) * 1.5 for r in roots])
        xs = np.linspace(xv - span, xv + span, 300)
        xlo, xhi = xs[0], xs[-1]
    ys = a * xs ** 2 + b * xs + c
    yr = max(ys.max(), 0) - min(ys.min(), 0)
    pad = yr * 0.15 + 1
    ylo, yhi = min(ys.min(), 0) - pad, max(ys.max(), 0) + pad
    if proj:
        yhi = max(ys.max(), 0) * 1.35 + 1
        ylo = -0.12 * yhi
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ylo, yhi)
    yr = yhi - ylo
    xr = xhi - xlo
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#92400E" if proj else "#374151", lw=3 if proj else 1.2)
    ax.axvline(0, color="#9CA3AF", lw=1)
    if proj:
        ax.set_xlabel("t (s)")
        ax.set_ylabel("h (m)")
    curve, = ax.plot([], [], color="#2563EB", lw=2.6)
    tracer, = ax.plot([], [], "o", color="#E07B39" if proj else "#2563EB", ms=12 if proj else 8, zorder=7)
    vdot, = ax.plot([], [], "D", color="#7C3AED", ms=9, zorder=5)
    axis, = ax.plot([], [], "--", color="#7C3AED", lw=1.3)
    rdots, = ax.plot([], [], "o", color="#DC2626", ms=11, zorder=6)
    up = a > 0
    vname = ("T" if tr else "V")
    vlab = ax.text(xv + 0.02 * xr, yv + (-0.03 if up else 0.03) * yr, "", color="#7C3AED", fontsize=11,
                   ha="left", va="top" if up else "bottom", zorder=8)
    show = [r for r in roots if not proj or r > 0]
    rlabs = []
    for r in show:
        out = -1 if (r < xv or len(show) == 1) else 1
        if proj:
            rlabs.append(ax.text(r, -0.025 * yr, "", color="#DC2626", fontsize=12, fontweight="bold",
                                 ha="right", va="top", zorder=8))
            continue
        rlabs.append(ax.text(r + out * 0.015 * xr, (-0.03 if up else 0.03) * yr, "", color="#DC2626", fontsize=12,
                             fontweight="bold", ha="left" if out > 0 else "right",
                             va="top" if up else "bottom", zorder=8))
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=11, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.92))
    coord = ax.text(0.98, 0.03 if up or proj else 0.97, "", transform=ax.transAxes, ha="right",
                    va="bottom" if up or proj else "top", fontsize=10, zorder=9,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.92))
    ax.set_title(("h(t) = " if proj else "y = ") + sol["fmt"]["expr"], fontsize=13)
    rq = [q for q, r in zip(qroots if D > 0 else ([qxv] if D == 0 else []), roots) if not proj or r > 0]
    rl = [(f"{v} = {_f(q)}" if rational else f"{v} ≈ {float(q):.3g}") + (" s" if proj else "") for q in rq]
    N = 125

    def update(i):
        p = min(1.0, max(0.0, i / 45))
        m = max(1, int(p * len(xs)))
        if m >= 2:
            curve.set_data(xs[:m], ys[:m])
        else:
            curve.set_data([], [])
        if p < 1:
            tracer.set_data([xs[m - 1]], [ys[m - 1]])
            coord.set_text(f"{v} = {xs[m - 1]:.2f},  " + ("h" if proj else "y") + f" = {ys[m - 1]:.2f}")
        else:
            tracer.set_data([], [])
            coord.set_text("")
        if i >= 50:
            vdot.set_data([xv], [yv])
            axis.set_data([xv, xv], [ylo, yhi])
            vlab.set_text(f"{vname}({_num(qxv)}, {_num(qyv)})")
        else:
            vdot.set_data([], [])
            axis.set_data([], [])
            vlab.set_text("")
        if i >= 75:
            rdots.set_data(show, [0] * len(show))
            for t, txt in zip(rlabs, rl):
                t.set_text(txt)
        else:
            rdots.set_data([], [])
            for t in rlabs:
                t.set_text("")
        if i < 50:
            info.set_text(("1) Topun yolu: h(t) eğrisi" if tr else "1) The ball's path: the curve h(t)") if proj else
                          ("1) Parabolü çiz" if tr else "1) Draw the parabola"))
        elif i < 75:
            info.set_text((f"2) En yüksek nokta (tepe): h = {_num(qyv)} m, t = {_num(qxv)} s" if tr else
                           f"2) Highest point (vertex): h = {_num(qyv)} m at t = {_num(qxv)} s") if proj else
                          ("2) Tepe noktası ve simetri ekseni" if tr else "2) Vertex and axis of symmetry"))
        else:
            info.set_text((("3) Yere düşme: h(t) = 0 ⇒ " if tr else "3) Landing: h(t) = 0 ⇒ ") + rl[-1])
                          if proj else (f"3) Δ = {_f(qD)}  ⇒  " + ans))
        return []

    return N, update


def vary(P, rnd):
    try:
        a0, b0, c0 = _abc(P)
        D0 = b0 * b0 - 4 * a0 * c0
        k0, s0 = _isqrt_parts(abs(D0).numerator * abs(D0).denominator) if D0 != 0 else (0, 1)
    except (KeyError, ValueError, TypeError):
        D0, s0 = 1, 1
    if P.get("ctx") == "projectile":
        while True:
            r1, r2 = rnd.choice([-1, -2, -3]), rnd.randint(3, 8)
            if (r1 + r2) % 2 == 0 and r1 + r2 >= 2:
                return {"a": -5, "b": 5 * (r1 + r2), "c": -5 * r1 * r2, "ctx": "projectile"}
    if D0 < 0:
        a, h, s = rnd.choice([1, 1, 2, -1]), rnd.randint(-3, 3), rnd.randint(1, 3)
        return {"a": a, "b": -2 * a * h, "c": a * h * h + a * s * s}
    if D0 == 0:
        a, r = rnd.choice([1, 2, -1]), rnd.randint(-4, 4)
        return {"a": a, "b": -2 * a * r, "c": a * r * r}
    if s0 != 1:
        while True:
            a, b, c = rnd.choice([1, 2, 3]), rnd.randint(-7, 7), rnd.choice([v for v in range(-9, 10) if v != 0])
            D = b * b - 4 * a * c
            if D > 0 and math.isqrt(D) ** 2 != D:
                return {"a": a, "b": b, "c": c}
    a = rnd.choice([1, 1, 1, -1, 2])
    r1 = rnd.randint(-6, 5)
    r2 = rnd.choice([v for v in range(-5, 7) if v != r1])
    return {"a": a, "b": -a * (r1 + r2), "c": a * r1 * r2}
''',
}
EXAMPLES += [
    {"id": "alg-quad-1", "kind": "quadratic",
     "title": ("Çarpanlara ayrılan denklem", "Factorable quadratic"),
     "q": ("{expr} = 0 denkleminin köklerini bul.", "Find the roots of {expr} = 0."),
     "P": {"a": 1, "b": -1, "c": -12}},
    {"id": "alg-quad-2", "kind": "quadratic",
     "title": ("Kök formülü", "Quadratic formula"),
     "q": ("Kök formülüyle çöz: {expr} = 0", "Use the quadratic formula: {expr} = 0"),
     "P": {"a": 2, "b": 3, "c": -4}},
    {"id": "alg-quad-3", "kind": "quadratic",
     "title": ("Reel kökü olmayan denklem", "No real roots"),
     "q": ("{expr} = 0 denkleminin diskriminantını hesapla; reel kökü var mı?",
           "Compute the discriminant of {expr} = 0. Are there real roots?"),
     "P": {"a": 1, "b": 2, "c": 5}},
    {"id": "alg-quad-4", "kind": "quadratic",
     "topics": ["projectile", "word problem", "sözel problem", "eğik atış", "dikey atış", "atış problemi"],
     "title": ("Fırlatılan top", "Thrown ball"),
     "q": ("Bir topun t saniyedeki yüksekliği h(t) = {expr} metredir. Top ne zaman yere düşer ve en fazla "
           "kaç metre yükselir?",
           "A ball's height after t seconds is h(t) = {expr} metres. When does it land and what is its "
           "maximum height?"),
     "P": {"a": -5, "b": 20, "c": 25, "ctx": "projectile"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["function_graph"] = {
    "course": "alg",
    "title": ("Fonksiyon grafiği", "Graph of a function"),
    "topics": ["radicals", "radical functions", "square root functions", "inverse functions", "composite functions", "composition of functions", "ters fonksiyon", "bileşke fonksiyon", "köklü fonksiyon", "graphing functions", "graphs of functions", "graph of a function", "functions and their graphs",
               "functions and graphs", "intro to functions", "introduction to functions", "function notation",
               "evaluating functions", "domain and range", "domain of a function", "zeros of a function",
               "x intercept", "y intercept", "intercepts",
               "fonksiyon grafikleri", "fonksiyonların grafikleri", "fonksiyon grafiği", "fonksiyonlara giriş",
               "tanım kümesi", "değer kümesi", "tanım ve değer kümesi"],
    "code": r'''
import numpy as np
import sympy as sp

_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
        "-": "⁻"}
_TRIG = (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc)


def _pretty(e):
    # 'x**3 - 4*x' -> 'x³ − 4x' (yalnızca görüntü)
    s = e if isinstance(e, str) else sp.sstr(e)
    out, i, n = "", 0, len(s)
    while i < n:
        if s.startswith("**", i):
            j = i + 2
            if j < n and s[j] == "(":
                k = s.find(")", j)
                inner = s[j + 1:k] if k > 0 else ""
                if inner and all(ch in _SUP for ch in inner):
                    out += "".join(_SUP[ch] for ch in inner)
                    i = k + 1
                    continue
            k = j
            while k < n and s[k].isdigit():
                k += 1
            if k > j:
                out += "".join(_SUP[ch] for ch in s[j:k])
                i = k
                continue
            out += "^"
            i = j
            continue
        ch = s[i]
        if ch == "*":
            nxt = s[i + 1] if i + 1 < n else ""
            if out and out[-1].isdigit() and (nxt.isalpha() or nxt == "("):
                i += 1
                continue
            out += "·"
            i += 1
            continue
        out += ch
        i += 1
    out = out.replace("sqrt", "√").replace(" - ", " − ").replace("pi", "π").replace("log(", "ln(")
    k = out.find("√(")
    while k >= 0:
        e = out.find(")", k)
        if e > k + 2 and out[k + 2:e].isdigit():
            out = out[:k + 1] + out[k + 2:e] + out[e + 1:]
        k = out.find("√(", k + 1)
    return out


def _expr(P):
    x = sp.Symbol("x", real=True)
    src = str(P.get("f", "")).strip()
    if not src:
        raise ValueError("f(x) boş / f(x) is empty")
    try:
        f = sp.sympify(src, locals={"x": x, "e": sp.E, "ln": sp.log})
    except Exception:
        raise ValueError(f"f(x) okunamadı / cannot read f(x): {src}")
    if not isinstance(f, sp.Expr):
        raise ValueError(f"f(x) bir ifade olmalı / f(x) must be an expression: {src}")
    other = sorted(str(s) for s in f.free_symbols if s != x)
    if other:
        raise ValueError(f"f yalnızca x'e bağlı olmalı / f may depend on x only (also found: {', '.join(other)})")
    if f.has(sp.Float):
        f = sp.nsimplify(f, rational=True)
    try:
        sp.lambdify(x, f, "numpy")
    except Exception:
        raise ValueError(f"f(x) sayısal olarak hesaplanamıyor / f(x) cannot be evaluated numerically: {src}")
    return x, f


def _realroot(e):
    # x**(1/3) = real cube root (also for x < 0), as in class; sqrt keeps x >= 0
    return e.replace(lambda t: t.is_Pow and t.exp.is_Rational and not t.exp.is_Integer and t.exp.q % 2 == 1,
                     lambda t: sp.sign(t.base) ** t.exp.p * sp.Abs(t.base) ** t.exp)


def _num(f, x):
    try:
        g = sp.lambdify(x, _realroot(f), "numpy")
    except Exception:
        # e.g. an unevaluated Derivative(floor(x), x): no numeric values, nothing to plot or mark
        def g(v):
            return np.full(np.shape(v), np.nan)

    def h(v):
        v = np.asarray(v, dtype=float)
        with np.errstate(all="ignore"):
            try:
                out = np.asarray(g(v), dtype=complex)
            except Exception:
                out = np.full(v.shape, np.nan, dtype=complex)
        out = np.broadcast_to(out, v.shape)
        re_ = np.where(np.abs(out.imag) <= 1e-9 * (1 + np.abs(out.real)), out.real, np.nan)
        return np.where(np.isfinite(re_), re_, np.nan).astype(float)
    return h


def _window(P):
    try:
        a, b = float(P.get("xmin", -6)), float(P.get("xmax", 6))
    except (TypeError, ValueError):
        raise ValueError("xmin / xmax sayı olmalı / xmin and xmax must be numbers")
    if not (np.isfinite(a) and np.isfinite(b)):
        raise ValueError("xmin / xmax sonlu olmalı / xmin and xmax must be finite")
    if a > b:
        a, b = b, a
    if b - a < 1e-6:
        a, b = a - 5, b + 5
    return a, b


def _exact_roots(e, x):
    # all real zeros of a rational function e; 'all' if e == 0; None if e is not rational in x
    try:
        num, den = sp.fraction(sp.together(e))
        if not (num.is_polynomial(x) and den.is_polynomial(x)):
            return None
        pn = sp.Poly(num, x)
        if pn.is_zero:
            return "all"
        if pn.degree() > 24:
            return None
        out = []
        for r in sp.real_roots(pn):
            if r in out:
                continue
            if abs(complex(sp.N(den.subs(x, r)))) < 1e-12:
                continue
            out.append(r)
        return out
    except Exception:
        return None


def _num_roots(h, a, b, n=4001, runs=None):
    # zeros on [a, b]: sign changes (bisection), exact hits, touching zeros. Runs of exact
    # zeros (f = 0 on a whole interval, e.g. floor(x)) are returned through `runs`.
    xs = np.linspace(a, b, n)
    ys = h(xs)
    out = []
    zero = np.isfinite(ys) & (ys == 0)
    k = 0
    while k < n:
        if zero[k]:
            j = k
            while j + 1 < n and zero[j + 1]:
                j += 1
            if j > k and runs is not None:
                runs.append((float(xs[k]), float(xs[j])))
            elif j == k:
                out.append(xs[k])
            k = j + 1
        else:
            k += 1
    for k in range(n - 1):
        y0, y1 = ys[k], ys[k + 1]
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        if y0 * y1 < 0:
            lo, hi, ylo = xs[k], xs[k + 1], y0
            for _ in range(60):
                mid = (lo + hi) / 2
                ym = h(np.array([mid]))[0]
                if not np.isfinite(ym):
                    break
                if ylo * ym <= 0:
                    hi = mid
                else:
                    lo, ylo = mid, ym
            z = (lo + hi) / 2
            yz = h(np.array([z]))[0]
            # a real root makes f tiny; a pole (huge) or a jump (finite step) does not
            if np.isfinite(yz) and abs(yz) <= 1e-7 * (abs(y0) + abs(y1)) + 1e-12:
                out.append(z)
    ay = np.abs(ys)
    fin = ay[np.isfinite(ay)]
    scale = float(np.median(fin)) if len(fin) else 1.0
    for k in range(1, n - 1):
        w = ay[k - 1:k + 2]
        if not np.all(np.isfinite(w)) or not (w[1] <= w[0] and w[1] < w[2]) or ys[k - 1] * ys[k + 1] <= 0:
            continue
        lo, hi = xs[k - 1], xs[k + 1]
        for _ in range(80):
            m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
            if abs(h(np.array([m1]))[0]) < abs(h(np.array([m2]))[0]):
                hi = m2
            else:
                lo = m1
        z = (lo + hi) / 2
        yz = abs(h(np.array([z]))[0])
        if np.isfinite(yz) and yz < 1e-10 * (1 + scale):                   # touches the axis
            out.append(z)
    out.sort()
    res = []
    for z in out:
        if not res or abs(z - res[-1]) > 1e-6 * (b - a):
            res.append(z)
    return res


def _snap(f, x, z):
    # a numerical zero that is really an exact simple number (e.g. -3 or π) -> exact sympy number
    for cand in (lambda: sp.nsimplify(z, tolerance=1e-8, rational=True),
                 lambda: sp.nsimplify(z, [sp.pi], tolerance=1e-9)):
        try:
            r = cand()
            if len(sp.sstr(r)) <= 10 and abs(r) <= 1000 and sp.simplify(f.subs(x, r)) == 0:
                return r
        except Exception:
            pass
    return float(z)


def _txt(v, short=False):
    if isinstance(v, float):
        return f"≈ {v:.4g}"
    if v.is_Rational:
        return str(v) if v.q <= 10000 else f"≈ {float(v):.4g}"
    s = sp.sstr(v)
    if len(s) <= 14 and "RootOf" not in s:
        return _pretty(s) if short else f"{_pretty(s)} ≈ {float(sp.N(v)):.4g}"
    return f"≈ {float(sp.N(v)):.4g}"


def _fmt_set(S):
    def num(v):
        if v == sp.oo:
            return "∞"
        if v == -sp.oo:
            return "-∞"
        return _txt(v, short=True)

    def iv(I):
        return ("(" if (I.left_open or I.start == -sp.oo) else "[") + f"{num(I.start)}, {num(I.end)}" + \
               (")" if (I.right_open or I.end == sp.oo) else "]")
    if S == sp.S.Reals:
        return "ℝ"
    if S == sp.S.EmptySet:
        return "∅"
    gap = sp.S.Reals - S
    if isinstance(gap, sp.FiniteSet) and len(gap) <= 6:
        return "ℝ − {" + ", ".join(num(v) for v in sorted(gap, key=float)) + "}"
    if isinstance(S, sp.Interval):
        return iv(S)
    if isinstance(S, sp.Union) and all(isinstance(t, sp.Interval) for t in S.args) and len(S.args) <= 4:
        return " ∪ ".join(iv(t) for t in S.args)
    return None


def _analyse(P):
    x, f = _expr(P)
    h = _num(f, x)
    a, b = _window(P)
    dom, D = None, None
    if not f.has(*_TRIG):
        try:
            from sympy.calculus.util import continuous_domain
            D = continuous_domain(f, x, sp.S.Reals)
            dom = _fmt_set(D)
        except Exception:
            D, dom = None, None
    zs = _exact_roots(f, x)
    d = sp.diff(f, x)
    crit = _exact_roots(d, x) if zs is not None else None
    asym, holes = [], []
    if zs is not None:
        try:
            g = sp.cancel(sp.together(f))
            den0 = sp.fraction(sp.together(f))[1]
            den1 = sp.fraction(g)[1]
            if den1.has(x):
                asym = sorted(set(sp.real_roots(sp.Poly(den1, x))), key=float)
            if den0.has(x):
                for r in sorted(set(sp.real_roots(sp.Poly(den0, x))), key=float):
                    if r not in asym:
                        holes.append((r, g.subs(x, r)))
        except Exception:
            asym, holes = [], []
    # widen the window so that every exact zero / critical point / asymptote is visible
    keys = [float(sp.N(r)) for r in (zs if isinstance(zs, list) else []) + (crit if isinstance(crit, list) else [])]
    keys += [float(sp.N(r)) for r in asym]
    keys = [k for k in keys if abs(k) <= 60]
    if keys:
        lo, hi = min(keys + [a]), max(keys + [b])
        padx = 0.08 * (hi - lo) + 0.5
        a, b = (lo - padx if lo < a else a), (hi + padx if hi > b else b)
    exact = zs is not None
    zruns = []
    if zs is None:
        zs = [_snap(f, x, z) for z in _num_roots(h, a, b, runs=zruns)]
    hd = _num(d, x)
    if crit is None or crit == "all":
        crit = [] if crit == "all" else [_snap(d, x, z) for z in _num_roots(hd, a, b)]
    cpts = []
    for c in crit:
        xc = float(sp.N(c)) if not isinstance(c, float) else c
        yc = h(np.array([xc]))[0]
        if not np.isfinite(yc):
            continue
        dl = 1e-4 * (b - a)
        s1, s2 = hd(np.array([xc - dl]))[0], hd(np.array([xc + dl]))[0]
        kind = "max" if (s1 > 0 > s2) else ("min" if (s1 < 0 < s2) else "flat")
        cpts.append((c, xc, float(yc), kind))
    y0 = None
    try:
        v0 = f.subs(x, 0)
        if v0.is_real is True and v0.is_finite is True:
            y0 = sp.nsimplify(v0) if v0.is_Float else v0
    except Exception:
        y0 = None
    ends = []
    if D is not None:
        parts = D.args if isinstance(D, sp.Union) else ([D] if isinstance(D, sp.Interval) else [])
        for I in parts:
            if isinstance(I, sp.Interval):
                if not I.left_open and I.start.is_finite:
                    ends.append(float(I.start))
                if not I.right_open and I.end.is_finite:
                    ends.append(float(I.end))
    return {"x": x, "f": f, "h": h, "a": a, "b": b, "dom": dom, "zs": zs, "exact": exact, "d": d, "zruns": zruns,
            "cpts": cpts, "y0": y0, "asym": [float(sp.N(r)) for r in asym], "ends": ends,
            "holes": [(float(sp.N(r)), float(sp.N(v))) for r, v in holes if sp.N(v).is_finite]}


def _zeros_text(A, short=False):
    zs = A["zs"]
    if zs == "all":
        return ("her x (f ≡ 0)", "every x (f ≡ 0)")
    if A["zruns"]:
        r = "; ".join(f"{p:.3g} ≤ x ≤ {q:.3g}" for p, q in A["zruns"][:3])
        pts = _zeros_text(dict(A, zruns=[]), short) if zs else ("", "")
        return ((f"bütün bir aralıkta f = 0: yaklaşık {r}" + (f";  ayrıca {pts[0]}" if zs else "")),
                (f"f = 0 on a whole interval: about {r}" + (f";  also {pts[1]}" if zs else "")))
    if not zs:
        w = f" [{A['a']:.4g}, {A['b']:.4g}]" if not A["exact"] else ""
        return (("yok" + (f" ({w.strip()} aralığında)" if w else "")), ("none" + (f" (on{w})" if w else "")))
    items = [_txt(z, short) for z in zs]
    more = len(items) - 8
    if more > 0:
        items = items[:8]
    if any(s.startswith("≈") for s in items):
        t = ", ".join(("x " + s) if s.startswith("≈") else ("x = " + s) for s in items)
    else:
        t = "x = " + ", ".join(items)
    tt, te = t, t
    if more > 0:
        tt, te = t + f", … ({len(zs)} tane bulundu)", t + f", … ({len(zs)} found)"
    if not A["exact"]:
        return (tt + f"  ([{A['a']:.4g}, {A['b']:.4g}] aralığında)", te + f"  (on [{A['a']:.4g}, {A['b']:.4g}])")
    return (tt, te)


def solve(P):
    A = _analyse(P)
    f, d = A["f"], A["d"]
    pf = _pretty(f)
    steps = [(f"f(x) = {pf}", f"f(x) = {pf}")]
    if A["dom"]:
        steps.append((f"Tanım kümesi: {A['dom']}", f"Domain: {A['dom']}"))
    if A["asym"]:
        t = ", ".join(f"x = {v:.4g}" for v in A["asym"])
        steps.append((f"Payda sıfır olur, pay sıfır olmaz ⇒ düşey asimptot: {t}",
                      f"The denominator vanishes but the numerator does not ⇒ vertical asymptote: {t}"))
    for xh, yh in A["holes"]:
        steps.append((f"Sadeleşen çarpan ⇒ boş nokta (delik): ({xh:.4g}, {yh:.4g})",
                      f"Cancelling factor ⇒ hole at ({xh:.4g}, {yh:.4g})"))
    y0 = A["y0"]
    if y0 is not None:
        steps.append((f"y-kesişimi: f(0) = {_txt(y0)}  ⇒  (0, {_txt(y0, True)})",
                      f"y-intercept: f(0) = {_txt(y0)}  ⇒  (0, {_txt(y0, True)})"))
    else:
        steps.append(("x = 0 tanım kümesinde değil ⇒ y-kesişimi yok", "x = 0 is not in the domain ⇒ no y-intercept"))
    zt = _zeros_text(A)
    steps.append((f"Sıfırlar, f(x) = 0: {zt[0]}", f"Zeros, f(x) = 0: {zt[1]}"))
    try:
        ds = sp.factor(sp.cancel(sp.together(d))) if A["exact"] else sp.simplify(d)
    except Exception:
        ds = d
    if ds.has(sp.Derivative):
        steps.append(("f'(x) bu fonksiyon için sembolik olarak yazılamıyor", "f'(x) has no closed form for this function"))
    else:
        steps.append((f"f'(x) = {_pretty(ds)}  (f' > 0: artan, f' < 0: azalan)",
                      f"f'(x) = {_pretty(ds)}  (f' > 0: increasing, f' < 0: decreasing)"))
    names = {"max": ("Yerel maksimum", "Local maximum"), "min": ("Yerel minimum", "Local minimum"),
             "flat": ("Yatay teğet (ekstremum değil)", "Horizontal tangent (not an extremum)")}
    for c, xc, yc, kind in A["cpts"][:4]:
        ct = _txt(c)
        ct = ("x " + ct) if ct.startswith("≈") else ("x = " + ct)
        steps.append((f"{names[kind][0]}: f'(x) = 0, {ct}, f ≈ {yc:.4g}",
                      f"{names[kind][1]}: f'(x) = 0, {ct}, f ≈ {yc:.4g}"))
    if d == 0:
        steps.append(("f sabit: her x için f'(x) = 0", "f is constant: f'(x) = 0 for every x"))
    elif not A["cpts"]:
        steps.append(("f'(x) = 0 olan nokta yok (gösterilen aralıkta)", "No point with f'(x) = 0 (in the window shown)"))
    zs_short = _zeros_text(A, short=True)
    yi = (f"(0, {_txt(y0, True)})" if y0 is not None else "yok", f"(0, {_txt(y0, True)})" if y0 is not None else "none")
    dom_tr = f"Tanım kümesi: {A['dom']};  " if A["dom"] else ""
    dom_en = f"Domain: {A['dom']};  " if A["dom"] else ""
    ans = (f"{dom_tr}sıfırlar: {zs_short[0]};  y-kesişimi: {yi[0]}",
           f"{dom_en}zeros: {zs_short[1]};  y-intercept: {yi[1]}")
    return {"answer": ans, "steps": steps, "fmt": {"fx": pf}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    A = _analyse(P)
    f, h, a, b = A["f"], A["h"], A["a"], A["b"]
    base = np.linspace(a, b, 801)
    extra = [e for e in A["ends"] if a <= e <= b]
    xs = np.unique(np.concatenate([base, np.array(extra, dtype=float)]))
    ys = h(xs)
    fin = ys[np.isfinite(ys)]
    if len(fin) == 0:
        fin = np.array([-1.0, 1.0])
    lo, hi = float(np.percentile(fin, 2)), float(np.percentile(fin, 98))
    spread = hi - lo + 1
    keys = [0.0] + [yc for _, _, yc, _ in A["cpts"]] + [yh for _, yh in A["holes"]]
    if A["y0"] is not None:
        keys.append(float(sp.N(A["y0"])))
    keys = [k for k in keys if lo - 2 * spread <= k <= hi + 2 * spread]
    lo, hi = min([lo] + keys), max([hi] + keys)
    pad = (hi - lo) * 0.15 + 0.5
    jump = np.abs(np.diff(ys, prepend=ys[0]))
    ys = np.where(jump > (hi - lo + 1) * 2, np.nan, ys)
    for v in A["asym"]:
        if a < v < b:
            k = int(np.searchsorted(xs, v))
            xs = np.insert(xs, k, v)
            ys = np.insert(ys, k, np.nan)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.9, bottom=0.09)
    ax.set_xlim(a, b)
    ax.set_ylim(lo - pad, hi + pad)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.1)
    ax.axvline(0, color="#374151", lw=1.1)
    curve, = ax.plot([], [], color="#2563EB", lw=2.5)
    pt, = ax.plot([], [], "o", color="#E07B39", ms=9, zorder=6)
    coord = ax.text(0.98, 0.03, "", transform=ax.transAxes, ha="right", fontsize=10, zorder=9, ma="left",
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.92))
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=10.5, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.92))
    zx = [float(sp.N(z)) if not isinstance(z, float) else z for z in (A["zs"] if isinstance(A["zs"], list) else [])]
    zx = [z for z in zx if a <= z <= b]
    zdots, = ax.plot([], [], "o", color="#DC2626", ms=10, zorder=7)
    rx, ry = [], []
    for p, q in A["zruns"]:
        rx += [p, q, np.nan]
        ry += [0, 0, np.nan]
    zrun, = ax.plot([], [], color="#DC2626", lw=6, alpha=0.8, solid_capstyle="butt", zorder=7)
    cx = [c[1] for c in A["cpts"] if a <= c[1] <= b][:6]
    cy = [c[2] for c in A["cpts"] if a <= c[1] <= b][:6]
    cdots, = ax.plot([], [], "^", color="#16A34A", ms=10, zorder=7)
    y0 = float(sp.N(A["y0"])) if A["y0"] is not None else None
    ydot, = ax.plot([], [], "s", color="#7C3AED", ms=9, zorder=7)
    edots, = ax.plot([], [], "o", color="#2563EB", ms=7, zorder=7)
    hdots, = ax.plot([], [], "o", mfc="white", mec="#2563EB", mew=2, ms=9, zorder=8)
    alines = [ax.axvline(v, color="#DC2626", ls="--", lw=1.3, alpha=0) for v in A["asym"] if a < v < b]
    ex = [e for e in extra if np.isfinite(h(np.array([e]))[0])]
    ey = [float(h(np.array([e]))[0]) for e in ex]
    hx = [p[0] for p in A["holes"] if a <= p[0] <= b]
    hy = [p[1] for p in A["holes"] if a <= p[0] <= b]
    ax.set_title(f"f(x) = {_pretty(f)}", fontsize=13)
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    short = ans.split(";  ")
    summary = "\n".join(short)
    N = 120

    def update(i):
        p = min(1.0, i / 70)
        m = max(1, int(p * len(xs)))
        if m >= 2:
            curve.set_data(xs[:m], ys[:m])
        else:
            curve.set_data([], [])
        if p < 1:
            pt.set_data([xs[m - 1]], [ys[m - 1]])
            yy = ys[m - 1]
            coord.set_text(f"x = {xs[m - 1]:.2f},  f(x) = {yy:.3f}" if np.isfinite(yy)
                           else f"x = {xs[m - 1]:.2f},  f(x) " + ("tanımsız" if tr else "undefined"))
        else:
            pt.set_data([], [])
            coord.set_text(summary)
        if i >= 75:
            zdots.set_data(zx, [0] * len(zx))
            zrun.set_data(rx, ry)
            edots.set_data(ex, ey)
            hdots.set_data(hx, hy)
            for L in alines:
                L.set_alpha(0.9)
        else:
            zdots.set_data([], [])
            zrun.set_data([], [])
            edots.set_data([], [])
            hdots.set_data([], [])
            for L in alines:
                L.set_alpha(0)
        if i >= 90:
            cdots.set_data(cx, cy)
            ydot.set_data([0], [y0]) if (y0 is not None and a <= 0 <= b) else ydot.set_data([], [])
        else:
            cdots.set_data([], [])
            ydot.set_data([], [])
        if i < 75:
            info.set_text("1) (x, f(x)) noktalarını soldan sağa çiz" if tr else "1) Plot (x, f(x)) from left to right")
        elif i < 90:
            info.set_text(("2) Sıfırlar f(x) = 0 (kırmızı)" + (" · düşey asimptot (kesikli)" if alines else "")) if tr
                          else ("2) Zeros f(x) = 0 (red)" + (" · vertical asymptote (dashed)" if alines else "")))
        else:
            info.set_text("3) y-kesişimi (mor) · f'(x) = 0 noktaları (yeşil)" if tr else
                          "3) y-intercept (purple) · points with f'(x) = 0 (green)")
        return []

    return N, update


def vary(P, rnd):
    s = str(P.get("f", ""))
    form = "cubic"
    if "sqrt" in s:
        form = "sqrt"
    else:
        try:
            x, f = _expr(P)
            num, den = sp.fraction(sp.together(f))
            if den.has(x):
                form = "rational"
            elif f.is_polynomial(x) and sp.degree(f, x) == 2:
                form = "quad"
        except Exception:
            form = "cubic"
    if form == "sqrt":
        h, k = rnd.randint(-5, 1), rnd.choice([1, 2])
        f = sp.sympify(f"sqrt(x - ({h})) - {k}")
        return {"f": str(f), "xmin": h - 1, "xmax": h + k * k + 7}
    if form == "rational":
        r1, r2 = rnd.sample(range(-4, 5), 2)
        p = rnd.choice([v for v in range(-3, 4) if v not in (r1, r2)])
        f = sp.sympify(f"({sp.expand(f'(x - ({r1}))*(x - ({r2}))')})/(x - ({p}))")
        return {"f": str(f), "xmin": -6, "xmax": 6}
    k = rnd.choice([1, -1])
    if form == "quad":
        r1, r2 = rnd.sample(range(-4, 5), 2)
        f = sp.expand(sp.sympify(f"{k}*(x - ({r1}))*(x - ({r2}))"))
        return {"f": str(f), "xmin": min(r1, r2) - 3, "xmax": max(r1, r2) + 3}
    r1, r2, r3 = sorted(rnd.sample(range(-3, 4), 3))
    f = sp.expand(sp.sympify(f"{k}*(x - ({r1}))*(x - ({r2}))*(x - ({r3}))"))
    return {"f": str(f), "xmin": r1 - 1.5, "xmax": r3 + 1.5}
''',
}
EXAMPLES += [
    {"id": "alg-func-1", "kind": "function_graph",
     "title": ("Kübik fonksiyonun grafiği", "Graphing a cubic"),
     "q": ("f(x) = {fx} fonksiyonunun grafiğini çiz; sıfırlarını ve y-kesişimini bul.",
           "Graph f(x) = {fx}; find its zeros and y-intercept."),
     "P": {"f": "x**3 - 4*x", "xmin": -3.5, "xmax": 3.5}},
    {"id": "alg-func-2", "kind": "function_graph", "topics": ["rational function", "rasyonel fonksiyon"],
     "title": ("Rasyonel fonksiyon", "A rational function"),
     "q": ("f(x) = {fx} için tanım kümesini, sıfırları ve grafiği incele.",
           "For f(x) = {fx}, study the domain, zeros and graph."),
     "P": {"f": "(x**2 - 1)/(x - 2)", "xmin": -5, "xmax": 6}},
    {"id": "alg-func-3", "kind": "function_graph",
     "topics": ["square root function", "radical function", "karekök fonksiyonu", "köklü fonksiyon"],
     "title": ("Köklü fonksiyon", "Square-root function"),
     "q": ("f(x) = {fx} fonksiyonunun tanım kümesi ve grafiği nedir?",
           "What are the domain and graph of f(x) = {fx}?"),
     "P": {"f": "sqrt(x + 4) - 1", "xmin": -5, "xmax": 8}},
]


# ──────────────────────────────────────────────────────────────────────────
# Klasör/dosya adları çoğu zaman Türkçe karaktersiz ("Dogru_Denklemi.pdf") ya da
# BÜYÜK harfle ("ÇARPANLARA AYIRMA" -> küçük harfte "ayirma") yazılır; anahtar
# kelimelerin bu biçimlerini de ekleyerek eşleştirmenin kaçırmamasını sağlarız.
_ASCII = str.maketrans("çğıöşü", "cgiosu")


def _spelling_variants(words):
    out = list(words)
    for kw in words:
        for v in (kw.replace("ı", "i"), kw.translate(_ASCII)):
            if v != kw and v not in out:
                out.append(v)
    return out


for _tpl in TEMPLATES.values():
    _tpl["topics"] = _spelling_variants(_tpl["topics"])
for _ex in EXAMPLES:
    if _ex.get("topics"):
        _ex["topics"] = _spelling_variants(_ex["topics"])
