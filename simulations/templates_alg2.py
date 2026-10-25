# -*- coding: utf-8 -*-
"""Cebir simülasyonları (2/2): paralel/dik doğrular, fonksiyon dönüşümleri,
eşitsizlikler, mutlak değer, üstel büyüme, logaritma, polinom kökleri,
rasyonel fonksiyonlar, karmaşık sayılarla çarpma, diziler, çember denklemi.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Sorular kurs
kitaplarından KOPYALANMAZ: kendi ifademizle yazılmış, sayıları değiştirilmiş
tipik ders örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["parallel_perp"] = {
    "course": "alg",
    "title": ("Paralel ve dik doğrular", "Parallel and perpendicular lines"),
    "topics": ["parallel lines", "perpendicular lines", "parallel and perpendicular",
               "negative reciprocal", "slopes of parallel lines", "slopes of perpendicular lines",
               "equation of a line", "paralel doğrular", "dik doğrular", "paralel ve dik",
               "eğimler çarpımı", "diklik şartı"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import FancyArrowPatch


def _f(v):
    v = Fraction(v).limit_denominator(10000)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _co(v):
    v = Fraction(v)
    return _f(v) if v.denominator == 1 else f"({_f(v)})"


def _cl(t):
    return min(1.0, max(0.0, t))


def _mx(m):
    m = Fraction(m)
    if m == 1:
        return "x"
    if m == -1:
        return "-x"
    if m.denominator == 1:
        return f"{m.numerator}x"
    return ("-" if m < 0 else "") + f"({_f(abs(m))})x"


def _eq(m, b):
    m, b = Fraction(m), Fraction(b)
    if m == 0:
        return f"y = {_f(b)}"
    if b == 0:
        return f"y = {_mx(m)}"
    return f"y = {_mx(m)} {'+' if b > 0 else '-'} {_f(abs(b))}"


def _shift(name, v):
    v = Fraction(v)
    if v == 0:
        return name
    return f"{name} - {_f(v)}" if v > 0 else f"{name} + {_f(-v)}"


def _data(P):
    m1 = Fraction(P["mn"], P["md"])
    b0 = Fraction(P.get("b0", 0))
    x1, y1 = Fraction(P["x1"]), Fraction(P["y1"])
    perp = P.get("mode", "parallel") == "perpendicular"
    m2 = m1
    if perp:
        m2 = None if m1 == 0 else -1 / m1
    b2 = None if m2 is None else y1 - m2 * x1
    return m1, b0, x1, y1, perp, m2, b2


def solve(P):
    m1, b0, x1, y1, perp, m2, b2 = _data(P)
    given = _eq(m1, b0)
    pt = f"({_f(x1)}, {_f(y1)})"
    fmt = {"given": given, "point": pt, "m1": _f(m1)}
    steps = [(f"Verilen doğru: {given}  ⇒  eğim m₁ = {_f(m1)}",
              f"Given line: {given}  ⇒  slope m₁ = {_f(m1)}")]
    if m2 is None:
        steps.append(("Verilen doğru yataydır (m₁ = 0); ona dik olan doğru düşeydir.",
                      "The given line is horizontal (m₁ = 0); a perpendicular line is vertical."))
        steps.append((f"Sonuç: x = {_f(x1)}", f"Result: x = {_f(x1)}"))
        return {"answer": f"x = {_f(x1)}", "steps": steps, "fmt": fmt}
    if perp:
        steps.append((f"Dik doğrularda m₁·m₂ = −1  ⇒  m₂ = −1/m₁ = −1/{_co(m1)} = {_f(m2)}",
                      f"Perpendicular lines: m₁·m₂ = −1  ⇒  m₂ = −1/m₁ = −1/{_co(m1)} = {_f(m2)}"))
    else:
        steps.append((f"Paralel doğruların eğimleri eşittir: m₂ = m₁ = {_f(m2)}",
                      f"Parallel lines have equal slopes: m₂ = m₁ = {_f(m2)}"))
    ys, xs = _shift("y", y1), _shift("x", x1)
    steps.append((f"Nokta-eğim formu y − y₁ = m₂(x − x₁):  {ys} = {_co(m2)}({xs})",
                  f"Point-slope form y − y₁ = m₂(x − x₁):  {ys} = {_co(m2)}({xs})"))
    steps.append((f"b = y₁ − m₂·x₁ = {_f(y1)} − {_co(m2)}·({_f(x1)}) = {_f(b2)}",
                  f"b = y₁ − m₂·x₁ = {_f(y1)} − {_co(m2)}·({_f(x1)}) = {_f(b2)}"))
    ans = _eq(m2, b2)
    steps.append((f"Sonuç: {ans}", f"Result: {ans}"))
    if perp:
        steps.append((f"Kontrol: m₁·m₂ = {_co(m1)}·{_co(m2)} = {_f(m1 * m2)} ✓",
                      f"Check: m₁·m₂ = {_co(m1)}·{_co(m2)} = {_f(m1 * m2)} ✓"))
    elif b2 == b0:
        steps.append(("Not: nokta zaten verilen doğru üzerinde, iki doğru çakışır.",
                      "Note: the point lies on the given line, so the two lines coincide."))
    else:
        steps.append((f"Kontrol: {_co(m2)}·({_f(x1)}) + ({_f(b2)}) = {_f(m2 * x1 + b2)} = y₁ ✓  "
                      f"(b = {_f(b2)} ≠ {_f(b0)}: doğrular çakışmaz)",
                      f"Check: {_co(m2)}·({_f(x1)}) + ({_f(b2)}) = {_f(m2 * x1 + b2)} = y₁ ✓  "
                      f"(b = {_f(b2)} ≠ {_f(b0)}: the lines are distinct)"))
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    m1, b0, x1, y1, perp, m2, b2 = _data(P)
    sol = solve(P)
    th1 = math.atan(float(m1))
    th2 = th1 + (math.pi / 2 if perp else 0.0)
    ux, uy = math.cos(th1), math.sin(th1)
    ax0, ay0 = 0.0, float(b0)
    px, py = float(x1), float(y1)
    tt = (px - ax0) * ux + (py - ay0) * uy
    fx, fy = ax0 + tt * ux, ay0 + tt * uy
    wx, wy = px - fx, py - fy
    wl = math.hypot(wx, wy)
    if wl > 1e-9:
        vx, vy = wx / wl, wy / wl
    else:
        vx, vy = -uy, ux
    g_run, g_rise = m1.denominator, m1.numerator
    if m2 is None:
        n_run, n_rise = 0, 0
    else:
        n_run, n_rise = m2.denominator, m2.numerator
    if abs(px + n_run) + abs(py + n_rise) > abs(px - n_run) + abs(py - n_rise):
        n_run, n_rise = -n_run, -n_rise
    R = max(7.0, abs(px) + 2.5, abs(py) + 2.5, abs(px + n_run) + 1.5, abs(py + n_rise) + 1.5,
            abs(ay0) + 2.5, abs(g_run) + 1.5, abs(ay0 + g_rise) + 1.5,
            min(abs(fx) + 1.5, 14.0), min(abs(fy) + 1.5, 14.0))
    L = 3 * R
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.92, bottom=0.07)
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    given, = ax.plot([], [], color="#2563EB", lw=2.4,
                     label=(f"verilen: {_eq(m1, b0)}" if tr else f"given: {_eq(m1, b0)}"))
    moving, = ax.plot([], [], "--", color="#7C3AED", lw=2.0)
    final, = ax.plot([], [], color="#16A34A", lw=2.8,
                     label=(("dik doğru" if perp else "paralel doğru") if tr else
                            ("perpendicular line" if perp else "parallel line")))
    adot, = ax.plot([], [], "s", ms=7, color="#2563EB", zorder=6)
    pdot, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=7)
    ptxt = ax.text(px + 0.3, py + 0.35, "", color="#DC2626", fontsize=11, fontweight="bold", zorder=8)
    g_tri, = ax.plot([], [], color="#2563EB", lw=2.0, alpha=0.55)
    g_txt = ax.text(ax0 + g_run + 0.25, ay0 + g_rise / 2, "", color="#2563EB", fontsize=10)
    n_tri, = ax.plot([], [], color="#E07B39", lw=2.6)
    n_txt = ax.text(px + n_run + (0.25 if n_run >= 0 else -0.25), py + n_rise / 2, "",
                    color="#E07B39", fontsize=11, fontweight="bold",
                    ha="left" if n_run >= 0 else "right")
    rot_arc, = ax.plot([], [], color="#7C3AED", lw=1.6)
    corner, = ax.plot([], [], color="#DC2626", lw=1.8, zorder=6)
    xdot, = ax.plot([], [], "o", ms=6, color="#DC2626", zorder=6)
    arrow = FancyArrowPatch((fx, fy), (px, py), arrowstyle="-|>", mutation_scale=16,
                            color="#7C3AED", lw=1.6, zorder=5)
    ax.add_patch(arrow)
    arrow.set_visible(False)
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=11.5, zorder=10,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax.set_title((f"{'Dik' if perp else 'Paralel'} doğru: m₁ = {_f(m1)}, P({_f(x1)}, {_f(y1)})") if tr else
                 (f"{'Perpendicular' if perp else 'Parallel'} line: m₁ = {_f(m1)}, P({_f(x1)}, {_f(y1)})"),
                 fontsize=12)
    sz = R * 0.07

    def seg(cx, cy, th, half):
        c, s = math.cos(th), math.sin(th)
        return [cx - half * c, cx + half * c], [cy - half * s, cy + half * s]

    def tri(sx, sy, run, rise, q):
        if q <= 0:
            return [], []
        if q < 0.5:
            return [sx, sx + run * 2 * q], [sy, sy]
        return [sx, sx + run, sx + run], [sy, sy, sy + rise * (2 * q - 1)]

    N = 150

    def update(i):
        gx, gy = seg(ax0, ay0, th1, L * _cl(i / 24))
        given.set_data(gx, gy)
        if i >= 6:
            adot.set_data([ax0], [ay0])
        else:
            adot.set_data([], [])
        qg = _cl((i - 24) / 14)
        tx_, ty_ = tri(ax0, ay0, g_run, g_rise, qg)
        g_tri.set_data(tx_, ty_)
        g_txt.set_text(f"m₁ = {_f(m1)}" if qg >= 1 else "")
        if i >= 30:
            pdot.set_data([px], [py])
            ptxt.set_text(f"P({_f(x1)}, {_f(y1)})")
        else:
            pdot.set_data([], [])
            ptxt.set_text("")
        s = _cl((i - 44) / 30)
        rot = _cl((i - 78) / 28) if perp else 0.0
        if 44 <= i < 108:
            mx_, my_ = seg(fx + s * wx, fy + s * wy, th1 + rot * math.pi / 2, L)
            moving.set_data(mx_, my_)
        else:
            moving.set_data([], [])
        if 44 <= i < 78 and wl > 0.3 and s > 0.05:
            arrow.set_positions((fx, fy), (fx + s * wx, fy + s * wy))
            arrow.set_visible(True)
        else:
            arrow.set_visible(False)
        if perp and 78 <= i < 108 and rot > 0:
            angs = np.linspace(th1, th1 + rot * math.pi / 2, 30)
            rot_arc.set_data(px + 0.12 * R * np.cos(angs), py + 0.12 * R * np.sin(angs))
        else:
            rot_arc.set_data([], [])
        if i >= 108:
            fx_, fy_ = seg(px, py, th2, L)
            final.set_data(fx_, fy_)
        else:
            final.set_data([], [])
        if perp and i >= 108:
            corner.set_data([fx + sz * ux, fx + sz * (ux + vx), fx + sz * vx],
                            [fy + sz * uy, fy + sz * (uy + vy), fy + sz * vy])
            xdot.set_data([fx], [fy])
        else:
            corner.set_data([], [])
            xdot.set_data([], [])
        qn = _cl((i - 112) / 18)
        nx_, ny_ = tri(px, py, n_run, n_rise, qn)
        n_tri.set_data(nx_, ny_)
        n_txt.set_text(f"m₂ = {_f(m2)}" if (qn >= 1 and m2 is not None) else "")
        if i < 30:
            info.set_text((f"1) Verilen doğru: {_eq(m1, b0)}\n    eğim m₁ = {_f(m1)}") if tr else
                          (f"1) Given line: {_eq(m1, b0)}\n    slope m₁ = {_f(m1)}"))
        elif i < 44:
            info.set_text((f"2) P({_f(x1)}, {_f(y1)}) noktasını işaretle") if tr else
                          (f"2) Mark the point P({_f(x1)}, {_f(y1)})"))
        elif i < 78:
            info.set_text("3) Doğruyu eğimini değiştirmeden P'ye kaydır" if tr else
                          "3) Slide the line to P without changing its slope")
        elif i < 108:
            if perp:
                m2s = "tanımsız" if m2 is None else _f(m2)
                m2e = "undefined" if m2 is None else _f(m2)
                info.set_text((f"4) P etrafında 90° döndür\n    m₂ = −1/m₁ = {m2s}") if tr else
                              (f"4) Rotate 90° about P\n    m₂ = −1/m₁ = {m2e}"))
            else:
                info.set_text((f"4) Paralel ⇒ eğimler eşit\n    m₂ = m₁ = {_f(m2)}") if tr else
                              (f"4) Parallel ⇒ equal slopes\n    m₂ = m₁ = {_f(m2)}"))
        else:
            if perp and m2 is not None:
                chk = f"m₁·m₂ = {_co(m1)}·{_co(m2)} = −1 ✓"
            elif perp:
                chk = "yatay ⟂ düşey ✓" if tr else "horizontal ⟂ vertical ✓"
            else:
                chk = f"m₁ = m₂ = {_f(m2)} ✓"
            info.set_text(("Sonuç: " if tr else "Result: ") + sol["answer"] + "\n" + chk)
        return []

    return N, update


def vary(P, rnd):
    mode = P.get("mode", "parallel")
    perp = mode == "perpendicular"
    for _ in range(500):
        md = rnd.choice([1, 1, 2, 3, 4])
        mn = rnd.choice([v for v in range(-4, 5) if v != 0])
        m1 = Fraction(mn, md)
        m2 = -1 / m1 if perp else m1
        x1 = m2.denominator * rnd.choice([-2, -1, 1, 2])
        if abs(x1) > 6:
            continue
        b0 = rnd.randint(-4, 4)
        y1 = rnd.randint(-5, 5)
        if y1 == m1 * x1 + b0:
            continue
        return {"mn": m1.numerator, "md": m1.denominator, "b0": b0, "x1": x1, "y1": y1, "mode": mode}
    return dict(P)
''',
}
EXAMPLES += [
    {"id": "alg-parperp-1", "kind": "parallel_perp",
     "title": ("Paralel doğru denklemi", "Equation of a parallel line"),
     "q": ("{point} noktasından geçen ve {given} doğrusuna paralel olan doğrunun denklemini bul.",
           "Find the equation of the line through {point} that is parallel to {given}."),
     "P": {"mn": 2, "md": 3, "b0": 1, "x1": 3, "y1": 4, "mode": "parallel"}},
    {"id": "alg-parperp-2", "kind": "parallel_perp",
     "title": ("Dik doğru denklemi", "Equation of a perpendicular line"),
     "q": ("{given} doğrusuna dik olan ve {point} noktasından geçen doğruyu eğim-kesen formunda yaz.",
           "Write, in slope-intercept form, the line through {point} perpendicular to {given}."),
     "P": {"mn": 2, "md": 1, "b0": -3, "x1": 4, "y1": 1, "mode": "perpendicular"}},
    {"id": "alg-parperp-3", "kind": "parallel_perp", "topics": ["word problem", "sözel problem"],
     "title": ("Sözel problem: yola dik patika", "Word problem: path perpendicular to a road"),
     "q": ("Bir harita ızgarasında düz bir yol {given} doğrusu boyunca uzanıyor. {point} noktasındaki "
           "evden yola dik açıyla ulaşan bir patika yapılacak. Patikanın üzerinde bulunduğu doğrunun "
           "denklemi nedir?",
           "On a map grid a straight road runs along {given}. A footpath from the house at {point} "
           "must meet the road at a right angle. What is the equation of the line containing the path?"),
     "P": {"mn": -3, "md": 4, "b0": 2, "x1": 6, "y1": 5, "mode": "perpendicular"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["function_transform"] = {
    "course": "alg",
    "title": ("Fonksiyon dönüşümleri", "Transformations of functions"),
    "topics": ["transformation", "transformations of functions", "shifting", "translation",
               "vertical stretch", "reflection", "parent function", "parent functions",
               "graph transformations", "horizontal shift", "vertical shift",
               "fonksiyon dönüşümleri", "öteleme", "kaydırma", "yansıma", "germe", "ana fonksiyon"],
    "code": r'''
import numpy as np
from fractions import Fraction
from matplotlib.patches import FancyArrowPatch


def _F(v):
    return Fraction(v).limit_denominator(1000)


def _f(v):
    v = _F(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _cl(t):
    return min(1.0, max(0.0, t))


def _n(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "", "-") else s


def _base(parent, x):
    x = np.asarray(x, dtype=float)
    if parent == "|x|":
        return np.abs(x)
    if parent == "sqrt":
        return np.where(x >= 0, np.sqrt(np.abs(x)), np.nan)
    if parent == "x^3":
        return x ** 3
    return x ** 2


def _inner(h):
    h = _F(h)
    if h == 0:
        return "x"
    return f"x - {_f(h)}" if h > 0 else f"x + {_f(-h)}"


def _core(parent, h):
    s = _inner(h)
    if parent == "|x|":
        return f"|{s}|"
    if parent == "sqrt":
        return "√x" if _F(h) == 0 else f"√({s})"
    p = "³" if parent == "x^3" else "²"
    return ("x" + p) if _F(h) == 0 else f"({s}){p}"


def _expr(parent, a, h, k):
    a, k = _F(a), _F(k)
    if a == 1:
        pre = ""
    elif a == -1:
        pre = "-"
    elif a.denominator == 1:
        pre = _f(a)
    else:
        pre = ("-" if a < 0 else "") + f"({_f(abs(a))})"
    s = pre + _core(parent, h)
    if k != 0:
        s += f" {'+' if k > 0 else '-'} {_f(abs(k))}"
    return s


def _keyname(parent):
    if parent == "sqrt":
        return ("başlangıç noktası", "starting point")
    if parent == "x^3":
        return ("büküm noktası", "inflection point")
    return ("tepe noktası", "vertex")


def _adesc(a):
    a = _F(a)
    if a == 1:
        return ("a = 1: germe veya yansıma yok", "a = 1: no stretch or reflection")
    t, e = [], []
    if abs(a) > 1:
        t.append(f"dikey {_f(abs(a))} kat uzat")
        e.append(f"stretch vertically ×{_f(abs(a))}")
    elif abs(a) < 1:
        t.append(f"dikey {_f(abs(a))} katına sıkıştır")
        e.append(f"compress vertically ×{_f(abs(a))}")
    if a < 0:
        t.append("x-eksenine göre yansıt")
        e.append("reflect in the x-axis")
    return (f"a = {_f(a)}: " + " ve ".join(t), f"a = {_f(a)}: " + " and ".join(e))


def _hdesc(h):
    h = _F(h)
    if h == 0:
        return ("h = 0: yatay kayma yok", "h = 0: no horizontal shift")
    return (f"h = {_f(h)}: {_f(abs(h))} birim {'sağa' if h > 0 else 'sola'} kaydır",
            f"h = {_f(h)}: shift {_f(abs(h))} unit(s) {'right' if h > 0 else 'left'}")


def _kdesc(k):
    k = _F(k)
    if k == 0:
        return ("k = 0: dikey kayma yok", "k = 0: no vertical shift")
    return (f"k = {_f(k)}: {_f(abs(k))} birim {'yukarı' if k > 0 else 'aşağı'} kaydır",
            f"k = {_f(k)}: shift {_f(abs(k))} unit(s) {'up' if k > 0 else 'down'}")


def _domrange(parent, a, h, k):
    a, h, k = _F(a), _F(h), _F(k)
    rs = "≥" if a > 0 else "≤"
    if parent == "x^3":
        return ("tanım kümesi: tüm reel sayılar, görüntü kümesi: tüm reel sayılar",
                "domain: all real numbers, range: all real numbers")
    if parent == "sqrt":
        return (f"tanım kümesi: x ≥ {_f(h)}, görüntü kümesi: y {rs} {_f(k)}",
                f"domain: x ≥ {_f(h)}, range: y {rs} {_f(k)}")
    return (f"tanım kümesi: tüm reel sayılar, görüntü kümesi: y {rs} {_f(k)}",
            f"domain: all real numbers, range: y {rs} {_f(k)}")


def solve(P):
    par = P.get("parent", "x^2")
    a, h, k = _F(P["a"]), _F(P["h"]), _F(P["k"])
    f0 = _expr(par, 1, 0, 0)
    s1, s2, s3 = _expr(par, a, 0, 0), _expr(par, a, h, 0), _expr(par, a, h, k)
    ad, hd, kd = _adesc(a), _hdesc(h), _kdesc(k)
    kn = _keyname(par)
    sx, sy = 1, 1
    dr = _domrange(par, a, h, k)
    steps = [
        (f"Ana fonksiyon: f(x) = {f0};  g(x) = a·f(x − h) + k ile a = {_f(a)}, h = {_f(h)}, k = {_f(k)}",
         f"Parent function: f(x) = {f0};  g(x) = a·f(x − h) + k with a = {_f(a)}, h = {_f(h)}, k = {_f(k)}"),
        (f"1. {ad[0]}  ⇒  y = {s1}", f"1. {ad[1]}  ⇒  y = {s1}"),
        (f"2. {hd[0]}  ⇒  y = {s2}", f"2. {hd[1]}  ⇒  y = {s2}"),
        (f"3. {kd[0]}  ⇒  y = {s3}", f"3. {kd[1]}  ⇒  y = {s3}"),
        (f"{kn[0].capitalize()}: (0, 0) → (h, k) = ({_f(h)}, {_f(k)})",
         f"{kn[1].capitalize()}: (0, 0) → (h, k) = ({_f(h)}, {_f(k)})"),
        (f"Örnek nokta: ({sx}, {sy}) → ({sx} + h, a·{sy} + k) = ({_f(sx + h)}, {_f(a * sy + k)})",
         f"Sample point: ({sx}, {sy}) → ({sx} + h, a·{sy} + k) = ({_f(sx + h)}, {_f(a * sy + k)})"),
        (dr[0].capitalize(), dr[1].capitalize()),
    ]
    return {"answer": (f"g(x) = {s3};  {kn[0]} ({_f(h)}, {_f(k)})",
                       f"g(x) = {s3};  {kn[1]} ({_f(h)}, {_f(k)})"),
            "steps": steps, "fmt": {"g": s3, "f": f0}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    L = 0 if tr else 1
    par = P.get("parent", "x^2")
    a, h, k = float(P["a"]), float(P["h"]), float(P["k"])
    A, H, K = _F(P["a"]), _F(P["h"]), _F(P["k"])
    f0 = _expr(par, 1, 0, 0)
    s1, s2, s3 = _expr(par, A, 0, 0), _expr(par, A, H, 0), _expr(par, A, H, K)
    ad, hd, kd = _adesc(A), _hdesc(H), _kdesc(K)
    kn = _keyname(par)
    dr = _domrange(par, A, H, K)
    if par == "sqrt":
        xlo, xhi = min(0.0, h) - 2.0, max(0.0, h) + 7.0
        tt = np.linspace(0.0, 4.5, 60)
        sx0 = np.array([1.0, 4.0])
    else:
        W = {"x^2": 3.4, "|x|": 4.5, "x^3": 2.4}.get(par, 3.4)
        core = {"x^2": 2.0, "|x|": 3.0, "x^3": 1.5}.get(par, 2.0)
        xlo, xhi = min(0.0, h) - W, max(0.0, h) + W
        tt = np.linspace(-core, core, 81)
        sx0 = np.array([-2.0, 2.0]) if par == "|x|" else np.array([-1.0, 1.0])
    b0 = _base(par, tt)
    allv = np.concatenate([b0, a * b0, a * b0 + k, np.array([0.0, k])])
    lo, hi = float(np.nanmin(allv)) - 1.0, float(np.nanmax(allv)) + 1.0
    xs = np.linspace(xlo, xhi, 500)
    sy0 = _base(par, sx0)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.82, bottom=0.08)
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(lo, hi)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    ghost, = ax.plot(xs, _base(par, xs), "--", color="#6B7280", lw=1.6, alpha=0.0,
                     label=f"f(x) = {f0}")
    cur, = ax.plot([], [], color="#2563EB", lw=2.6, label=f"g(x) = {s3}")
    sdots, = ax.plot([], [], "o", ms=8, color="#E07B39", zorder=6)
    kdot, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=7)
    ktxt = ax.text(0, 0, "", color="#DC2626", fontsize=11, fontweight="bold", zorder=8)
    harr = FancyArrowPatch((0, 0), (1, 0), arrowstyle="-|>", mutation_scale=16, color="#16A34A", lw=2.2)
    karr = FancyArrowPatch((0, 0), (0, 1), arrowstyle="-|>", mutation_scale=16, color="#7C3AED", lw=2.2)
    ax.add_patch(harr)
    ax.add_patch(karr)
    harr.set_visible(False)
    karr.set_visible(False)
    htxt = ax.text(h / 2, -(hi - lo) * 0.05, "", color="#16A34A", fontsize=11, ha="center", va="top")
    ktx2 = ax.text(h + (xhi - xlo) * 0.015, k / 2, "", color="#7C3AED", fontsize=11, va="center")
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    fig.legend(handles=[ghost, cur], loc="upper right", bbox_to_anchor=(0.985, 0.985), fontsize=10)
    N = 150

    def update(i):
        pa = _cl((i - 24) / 30)
        ph = _cl((i - 60) / 30)
        pk = _cl((i - 96) / 30)
        at, ht, kt = 1 + (a - 1) * pa, h * ph, k * pk
        ghost.set_alpha(0.8 if i >= 22 else 0.0)
        if i < 22:
            m = max(2, int(_cl(i / 20) * len(xs)))
            cur.set_data(xs[:m], _base(par, xs[:m]))
        else:
            cur.set_data(xs, at * _base(par, xs - ht) + kt)
        if i >= 8:
            sdots.set_data(sx0 + ht, at * sy0 + kt)
            kdot.set_data([ht], [kt])
            ktxt.set_position((ht + (xhi - xlo) * 0.02, kt + (hi - lo) * 0.03))
            if i >= 126:
                ktxt.set_text(f"({_f(H)}, {_f(K)})")
            else:
                ktxt.set_text(f"({_n(ht)}, {_n(kt)})")
        else:
            sdots.set_data([], [])
            kdot.set_data([], [])
            ktxt.set_text("")
        if ph > 0.02 and abs(h) > 1e-9:
            harr.set_positions((0, 0), (ht, 0))
            harr.set_visible(True)
        else:
            harr.set_visible(False)
        htxt.set_text(hd[L].split(": ")[1] if (ph >= 1 and abs(h) > 1e-9) else "")
        if pk > 0.02 and abs(k) > 1e-9:
            karr.set_positions((h, 0), (h, kt))
            karr.set_visible(True)
        else:
            karr.set_visible(False)
        ktx2.set_text(kd[L].split(": ")[1] if (pk >= 1 and abs(k) > 1e-9) else "")
        if i < 22:
            info.set_text(("1) Ana fonksiyon: f(x) = " if tr else "1) Parent function: f(x) = ") + f0)
        elif i < 58:
            info.set_text(f"2) {ad[L]}\n    ⇒ y = {s1}")
        elif i < 94:
            info.set_text(f"3) {hd[L]}\n    ⇒ y = {s2}")
        elif i < 128:
            info.set_text(f"4) {kd[L]}\n    ⇒ y = {s3}")
        else:
            info.set_text(f"g(x) = {s3}    {kn[L]} ({_f(H)}, {_f(K)})\n{dr[L]}")
        return []

    return N, update


def vary(P, rnd):
    a = rnd.choice([2, -1, -2, 0.5, 3, -0.5, 1])
    h = rnd.choice([v for v in range(-4, 5) if v != 0])
    k = rnd.choice([v for v in range(-4, 5) if v != 0])
    return {"parent": P.get("parent", "x^2"), "a": a, "h": h, "k": k}
''',
}
EXAMPLES += [
    {"id": "alg-transform-1", "kind": "function_transform",
     "title": ("Parabolü kaydırma ve germe", "Shifting and stretching a parabola"),
     "q": ("f(x) = {f} grafiğinden başlayarak g(x) = {g} grafiğini dönüşümlerle çiz. Tepe noktası nedir?",
           "Starting from the graph of f(x) = {f}, sketch g(x) = {g} using transformations. "
           "What is the vertex?"),
     "P": {"parent": "x^2", "a": 2, "h": 3, "k": 1}},
    {"id": "alg-transform-2", "kind": "function_transform", "topics": ["absolute value function", "mutlak değer fonksiyonu"],
     "title": ("Mutlak değer grafiğinde yansıma", "Reflecting an absolute-value graph"),
     "q": ("g(x) = {g} fonksiyonu f(x) = {f} grafiğinden hangi dönüşümlerle elde edilir? "
           "Görüntü kümesini bul.",
           "Which transformations turn f(x) = {f} into g(x) = {g}? Find the range."),
     "P": {"parent": "|x|", "a": -1, "h": -2, "k": 4}},
    {"id": "alg-transform-3", "kind": "function_transform", "topics": ["square root function", "karekök fonksiyonu"],
     "title": ("Karekök fonksiyonunun dönüşümü", "Transforming the square-root function"),
     "q": ("g(x) = {g} grafiğini f(x) = {f} grafiğinden elde et; tanım ve görüntü kümesini yaz.",
           "Obtain the graph of g(x) = {g} from f(x) = {f}; state its domain and range."),
     "P": {"parent": "sqrt", "a": 0.5, "h": -1, "k": -3}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["inequality_line"] = {
    "course": "alg",
    "title": ("Doğrusal eşitsizlik ve sayı doğrusu", "Linear inequality on a number line"),
    "topics": ["inequality", "inequalities", "linear inequality", "linear inequalities",
               "solving inequalities", "number line", "interval notation", "graphing inequalities",
               "eşitsizlik", "eşitsizlikler", "doğrusal eşitsizlik", "sayı doğrusu", "aralık gösterimi"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import FancyArrowPatch

_SYM = {"<": "<", ">": ">", "<=": "≤", ">=": "≥"}
_FLIP = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}


def _F(v):
    return Fraction(v).limit_denominator(1000)


def _f(v):
    v = _F(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _cl(t):
    return min(1.0, max(0.0, t))


def _lhs(a, b):
    a, b = _F(a), _F(b)
    ax = ("" if a == 1 else ("-" if a == -1 else _f(a))) + "x"
    if b == 0:
        return ax
    return f"{ax} {'+' if b > 0 else '-'} {_f(abs(b))}"


def _holds(v, s, c):
    if s == "<":
        return v < c
    if s == ">":
        return v > c
    if s == "<=":
        return v <= c
    return v >= c


def _interval(s2, x0):
    if s2 == "<":
        return f"(−∞, {_f(x0)})"
    if s2 == "<=":
        return f"(−∞, {_f(x0)}]"
    if s2 == ">":
        return f"({_f(x0)}, ∞)"
    return f"[{_f(x0)}, ∞)"


def _data(P):
    a, b, c = _F(P["a"]), _F(P["b"]), _F(P["c"])
    s = P.get("sign", "<")
    x0 = (c - b) / a
    s2 = _FLIP[s] if a < 0 else s
    d = 1 if s2 in (">", ">=") else -1
    if d > 0:
        t_in, t_out = math.floor(x0) + 2, math.ceil(x0) - 2
    else:
        t_in, t_out = math.ceil(x0) - 2, math.floor(x0) + 2
    return a, b, c, s, x0, s2, d, t_in, t_out


def solve(P):
    a, b, c, s, x0, s2, d, t_in, t_out = _data(P)
    S, S2 = _SYM[s], _SYM[s2]
    lhs = _lhs(a, b)
    if b >= 0:
        op = (f"Her iki taraftan {_f(b)} çıkar", f"Subtract {_f(b)} from both sides")
    else:
        op = (f"Her iki tarafa {_f(-b)} ekle", f"Add {_f(-b)} to both sides")
    if a < 0:
        dv = (f"Her iki tarafı ({_f(a)}) ile böl. NEGATİF sayıya bölünce eşitsizlik yön değiştirir: {S} → {S2}",
              f"Divide both sides by ({_f(a)}). Dividing by a NEGATIVE number flips the sign: {S} → {S2}")
    else:
        dv = (f"Her iki tarafı {_f(a)} ile böl (pozitif sayı: yön değişmez)",
              f"Divide both sides by {_f(a)} (positive number: the sign stays)")
    closed = s2 in ("<=", ">=")
    vin = a * t_in + b
    vout = a * t_out + b
    steps = [
        (f"Eşitsizlik: {lhs} {S} {_f(c)}", f"Inequality: {lhs} {S} {_f(c)}"),
        (f"{op[0]}: {_f(a)}x {S} {_f(c - b)}", f"{op[1]}: {_f(a)}x {S} {_f(c - b)}"),
        (f"{dv[0]}  ⇒  x {S2} {_f(c - b)}/{_f(a)} = {_f(x0)}",
         f"{dv[1]}  ⇒  x {S2} {_f(c - b)}/{_f(a)} = {_f(x0)}"),
        ((f"Sayı doğrusu: x = {_f(x0)} noktasında {'dolu' if closed else 'boş'} daire "
          f"({'dahil' if closed else 'dahil değil'}), {'sağa' if d > 0 else 'sola'} doğru ışın"),
         (f"Number line: {'closed' if closed else 'open'} circle at x = {_f(x0)} "
          f"({'included' if closed else 'not included'}), ray to the {'right' if d > 0 else 'left'}")),
        (f"Test noktası x = {t_in}: {_f(a)}·({t_in}) {'+' if b >= 0 else '-'} {_f(abs(b))} = {_f(vin)} {S} {_f(c)} ✓;  "
         f"x = {t_out}: {_f(vout)} {S} {_f(c)} ✗",
         f"Test point x = {t_in}: {_f(a)}·({t_in}) {'+' if b >= 0 else '-'} {_f(abs(b))} = {_f(vin)} {S} {_f(c)} ✓;  "
         f"x = {t_out}: {_f(vout)} {S} {_f(c)} ✗"),
        (f"Aralık gösterimi: {_interval(s2, x0)}", f"Interval notation: {_interval(s2, x0)}"),
    ]
    return {"answer": f"x {S2} {_f(x0)}  ⇔  {_interval(s2, x0)}", "steps": steps,
            "fmt": {"lhs": lhs, "S": S}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, c, s, x0f, s2, d, t_in, t_out = _data(P)
    x0 = float(x0f)
    S, S2 = _SYM[s], _SYM[s2]
    closed = s2 in ("<=", ">=")
    flip = a < 0
    gs = fig.add_gridspec(2, 1, height_ratios=[1.15, 1], left=0.04, right=0.97, top=0.96,
                          bottom=0.03, hspace=0.05)
    tx = fig.add_subplot(gs[0])
    tx.axis("off")
    tx.set_xlim(0, 1)
    tx.set_ylim(0, 1)
    ax = fig.add_subplot(gs[1])
    ax.axis("off")
    lo, hi = math.floor(x0) - 6, math.ceil(x0) + 6
    ax.set_xlim(lo - 0.8, hi + 0.8)
    ax.set_ylim(-1.45, 1.25)
    axis = FancyArrowPatch((lo - 0.7, 0), (hi + 0.7, 0), arrowstyle="<|-|>", mutation_scale=16,
                           color="#374151", lw=1.4)
    ax.add_patch(axis)
    for t in range(lo, hi + 1):
        ax.plot([t, t], [-0.12, 0.12], color="#374151", lw=1.2)
        ax.text(t, -0.42, str(t), ha="center", va="center", fontsize=10, color="#374151")
    lhs = _lhs(a, b)
    rows = [f"{lhs} {S} {_f(c)}", f"{_f(a)}x {S} {_f(c - b)}", f"x {S} {_f(x0f)}"]
    if b >= 0:
        notes = [("Eşitsizlik", "Inequality"), (f"−{_f(b)} her iki taraf", f"−{_f(b)} both sides")]
    else:
        notes = [("Eşitsizlik", "Inequality"), (f"+{_f(-b)} her iki taraf", f"+{_f(-b)} both sides")]
    if flip:
        notes.append((f"÷({_f(a)}): negatife bölünce yön değişir!", f"÷({_f(a)}): dividing by a negative flips it!"))
    else:
        notes.append((f"÷{_f(a)}: pozitif, yön aynı", f"÷{_f(a)}: positive, sign unchanged"))
    tx.text(0.0, 0.97, "Adım adım çözüm" if tr else "Step by step", fontsize=12, va="top", color="#111827")
    rt, nt = [], []
    for k in range(3):
        rt.append(tx.text(0.02, 0.74 - k * 0.22, rows[k], fontsize=18, family="DejaVu Sans Mono",
                          color="#111827", alpha=0, va="center"))
        nt.append(tx.text(0.52, 0.74 - k * 0.22, notes[k][0 if tr else 1], fontsize=11,
                          color="#6B7280", alpha=0, va="center"))
    chk1 = tx.text(0.02, 0.06, "", fontsize=11.5, color="#16A34A", va="center")
    chk2 = tx.text(0.52, 0.06, "", fontsize=11.5, color="#DC2626", va="center")
    col = "#2563EB"
    ray, = ax.plot([], [], color=col, lw=7, alpha=0.85, solid_capstyle="butt", zorder=4)
    head, = ax.plot([], [], marker=">" if d > 0 else "<", ms=15, color=col, zorder=5, ls="none")
    circ, = ax.plot([], [], "o", ms=15, mec=col, mew=2.6, mfc=(col if closed else "white"), zorder=6)
    clab = ax.text(x0, 0.5, "", ha="center", va="center", fontsize=13, fontweight="bold", color=col)
    tin, = ax.plot([], [], "o", ms=10, color="#16A34A", zorder=7)
    tout, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=7)
    tinl = ax.text(t_in, 0.45, "", ha="center", fontsize=13, color="#16A34A", fontweight="bold")
    toutl = ax.text(t_out, 0.45, "", ha="center", fontsize=13, color="#DC2626", fontweight="bold")
    info = ax.text(0.5, 0.01, "", transform=ax.transAxes, ha="center", va="bottom", fontsize=12,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    end = (hi + 0.45) if d > 0 else (lo - 0.45)
    vin, vout = a * t_in + b, a * t_out + b
    sb = f"{'+' if b >= 0 else '-'} {_f(abs(b))}"
    N = 140

    def update(i):
        for k in range(3):
            al = _cl((i - k * 14) / 10)
            rt[k].set_alpha(al)
            nt[k].set_alpha(al)
        if flip and i < 40:
            rt[2].set_text(f"x {S} {_f(x0f)}")
            rt[2].set_color("#111827")
            nt[2].set_color("#6B7280")
        else:
            rt[2].set_text(f"x {S2} {_f(x0f)}")
            rt[2].set_color("#DC2626" if flip else "#111827")
            nt[2].set_color("#DC2626" if flip else "#6B7280")
        if i >= 50:
            circ.set_data([x0], [0])
            clab.set_text(_f(x0f))
        else:
            circ.set_data([], [])
            clab.set_text("")
        p = _cl((i - 60) / 30)
        if p > 0:
            e = x0 + (end - x0) * p
            ray.set_data([x0, e], [0, 0])
            head.set_data([e], [0])
        else:
            ray.set_data([], [])
            head.set_data([], [])
        if i >= 96:
            tin.set_data([t_in], [0])
            tinl.set_text("✓")
            chk1.set_text(f"x = {t_in}: {_f(a)}·({t_in}) {sb} = {_f(vin)} {S} {_f(c)} ✓")
        else:
            tin.set_data([], [])
            tinl.set_text("")
            chk1.set_text("")
        if i >= 110:
            tout.set_data([t_out], [0])
            toutl.set_text("✗")
            chk2.set_text(f"x = {t_out}: {_f(a)}·({t_out}) {sb} = {_f(vout)} {S} {_f(c)} ✗")
        else:
            tout.set_data([], [])
            toutl.set_text("")
            chk2.set_text("")
        if i < 48:
            info.set_text("1) Cebirsel çözüm: x'i yalnız bırak" if tr else "1) Solve algebraically: isolate x")
        elif i < 60:
            info.set_text((f"2) Sınır x = {_f(x0f)}: " + ("dolu daire (eşitlik dahil)" if closed else "boş daire (dahil değil)"))
                          if tr else (f"2) Boundary x = {_f(x0f)}: " + ("closed circle (included)" if closed else "open circle (not included)")))
        elif i < 94:
            info.set_text((f"3) x {S2} {_f(x0f)}: çözüm bölgesini tara" if tr else
                           f"3) x {S2} {_f(x0f)}: shade the solution set"))
        elif i < 124:
            info.set_text("4) Test noktalarıyla kontrol" if tr else "4) Check with test points")
        else:
            info.set_text(("Çözüm: " if tr else "Solution: ") + f"x {S2} {_f(x0f)}  ⇔  {_interval(s2, x0f)}")
        return []

    return N, update


def vary(P, rnd):
    a = rnd.choice([2, 3, 4, 5, -2, -3, -4, -5])
    x0 = rnd.randint(-6, 6)
    b = rnd.choice([v for v in range(-12, 13) if v != 0])
    return {"a": a, "b": b, "c": a * x0 + b, "sign": rnd.choice(["<", ">", "<=", ">="])}
''',
}
EXAMPLES += [
    {"id": "alg-ineq-1", "kind": "inequality_line",
     "title": ("Negatife bölünce yön değişir", "Dividing by a negative flips the sign"),
     "q": ("{lhs} {S} {c} eşitsizliğini çöz ve çözümü sayı doğrusunda göster.",
           "Solve {lhs} {S} {c} and graph the solution on a number line."),
     "P": {"a": -3, "b": 5, "c": 17, "sign": "<="}},
    {"id": "alg-ineq-2", "kind": "inequality_line",
     "title": ("İki adımlı eşitsizlik", "Two-step inequality"),
     "q": ("{lhs} {S} {c} eşitsizliğinin çözüm kümesini aralık gösterimiyle yaz.",
           "Write the solution set of {lhs} {S} {c} in interval notation."),
     "P": {"a": 2, "b": -7, "c": 3, "sign": ">"}},
    {"id": "alg-ineq-3", "kind": "inequality_line", "topics": ["word problem", "sözel problem", "budget"],
     "title": ("Sözel problem: telefon faturası", "Word problem: phone bill"),
     "q": ("Bir telefon tarifesi aylık {b} TL sabit ücret ve her GB için {a} TL alıyor. Fatura en fazla "
           "{c} TL olacaksa en çok kaç GB kullanılabilir? ({lhs} {S} {c})",
           "A phone plan charges a fixed {b} per month plus {a} per GB. If the bill must be at most {c}, "
           "how many GB can be used? ({lhs} {S} {c})"),
     "P": {"a": 4, "b": 20, "c": 50, "sign": "<="}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["absolute_value_eq"] = {
    "course": "alg",
    "title": ("Mutlak değer: uzaklık olarak", "Absolute value as distance"),
    "topics": ["absolute value", "absolute value equation", "absolute value equations",
               "absolute value inequality", "absolute value inequalities", "distance on the number line",
               "mutlak değer", "mutlak değerli denklem", "mutlak değerli eşitsizlik", "uzaklık"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import FancyArrowPatch

_SYM = {"=": "=", "<": "<", ">": ">", "<=": "≤", ">=": "≥"}


def _F(v):
    return Fraction(v).limit_denominator(1000)


def _f(v):
    v = _F(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _cl(t):
    return min(1.0, max(0.0, t))


def _inner(h):
    h = _F(h)
    if h == 0:
        return "x"
    return f"x - {_f(h)}" if h > 0 else f"x + {_f(-h)}"


def _ok(dist, rel, d):
    if rel == "=":
        return abs(dist - d) < 1e-9
    if rel == "<":
        return dist < d
    if rel == "<=":
        return dist <= d
    if rel == ">":
        return dist > d
    return dist >= d


def _answer(h, d, rel):
    lo, hi = h - d, h + d
    if d < 0 or (d == 0 and rel == "<"):
        if rel in ("=", "<", "<="):
            return ("Çözüm yok (∅)", "No solution (∅)")
        return ("Tüm reel sayılar", "All real numbers")
    if d == 0:
        if rel in ("=", "<="):
            return (f"x = {_f(h)}", f"x = {_f(h)}")
        if rel == ">":
            return (f"x ≠ {_f(h)}", f"x ≠ {_f(h)}")
        return ("Tüm reel sayılar", "All real numbers")
    if rel == "=":
        return (f"x = {_f(lo)} veya x = {_f(hi)}", f"x = {_f(lo)} or x = {_f(hi)}")
    if rel == "<":
        return (f"{_f(lo)} < x < {_f(hi)}  ⇔  ({_f(lo)}, {_f(hi)})",
                f"{_f(lo)} < x < {_f(hi)}  ⇔  ({_f(lo)}, {_f(hi)})")
    if rel == "<=":
        return (f"{_f(lo)} ≤ x ≤ {_f(hi)}  ⇔  [{_f(lo)}, {_f(hi)}]",
                f"{_f(lo)} ≤ x ≤ {_f(hi)}  ⇔  [{_f(lo)}, {_f(hi)}]")
    if rel == ">":
        return (f"x < {_f(lo)} veya x > {_f(hi)}  ⇔  (−∞, {_f(lo)}) ∪ ({_f(hi)}, ∞)",
                f"x < {_f(lo)} or x > {_f(hi)}  ⇔  (−∞, {_f(lo)}) ∪ ({_f(hi)}, ∞)")
    return (f"x ≤ {_f(lo)} veya x ≥ {_f(hi)}  ⇔  (−∞, {_f(lo)}] ∪ [{_f(hi)}, ∞)",
            f"x ≤ {_f(lo)} or x ≥ {_f(hi)}  ⇔  (−∞, {_f(lo)}] ∪ [{_f(hi)}, ∞)")


def solve(P):
    h, d = _F(P["h"]), _F(P["d"])
    rel = P.get("rel", "=")
    S = _SYM[rel]
    e = f"|{_inner(h)}|"
    xi = _inner(h)
    steps = [
        (f"{e} {S} {_f(d)}", f"{e} {S} {_f(d)}"),
        (f"{e} = x ile {_f(h)} arasındaki uzaklık. Soru: {_f(h)} noktasına uzaklığı {S} {_f(d)} olan x'ler hangileri?",
         f"{e} = distance between x and {_f(h)}. Which x lie at a distance {S} {_f(d)} from {_f(h)}?"),
    ]
    ans = _answer(h, d, rel)
    if d > 0:
        if rel == "=":
            steps.append((f"İki durum: {xi} = {_f(d)}  veya  {xi} = −{_f(d)}",
                          f"Two cases: {xi} = {_f(d)}  or  {xi} = −{_f(d)}"))
            steps.append((f"x = {_f(h)} + {_f(d)} = {_f(h + d)}  veya  x = {_f(h)} − {_f(d)} = {_f(h - d)}",
                          f"x = {_f(h)} + {_f(d)} = {_f(h + d)}  or  x = {_f(h)} − {_f(d)} = {_f(h - d)}"))
            steps.append((f"Kontrol: |{_f(h + d)} − ({_f(h)})| = {_f(d)} ✓,  |{_f(h - d)} − ({_f(h)})| = {_f(d)} ✓",
                          f"Check: |{_f(h + d)} − ({_f(h)})| = {_f(d)} ✓,  |{_f(h - d)} − ({_f(h)})| = {_f(d)} ✓"))
        elif rel in ("<", "<="):
            steps.append((f"Uzaklık {S} {_f(d)} ⇒ tek bir bileşik eşitsizlik: −{_f(d)} {S} {xi} {S} {_f(d)}",
                          f"Distance less than {_f(d)} ⇒ one compound inequality: −{_f(d)} {S} {xi} {S} {_f(d)}"))
            steps.append((f"Her tarafa {_f(h)} ekle: {_f(h - d)} {S} x {S} {_f(h + d)}",
                          f"Add {_f(h)} to every part: {_f(h - d)} {S} x {S} {_f(h + d)}"))
        else:
            r2 = "<" if rel == ">" else "≤"
            steps.append((f"Uzaklık {S} {_f(d)} ⇒ iki ayrı parça: {xi} {r2} −{_f(d)}  veya  {xi} {S} {_f(d)}",
                          f"Distance greater than {_f(d)} ⇒ two pieces: {xi} {r2} −{_f(d)}  or  {xi} {S} {_f(d)}"))
            steps.append((f"x {r2} {_f(h - d)}  veya  x {S} {_f(h + d)}",
                          f"x {r2} {_f(h - d)}  or  x {S} {_f(h + d)}"))
    else:
        steps.append(("Uzaklık negatif olamaz; d ≤ 0 için özel durum.", "A distance cannot be negative; d ≤ 0 is a special case."))
    steps.append((f"Sonuç: {ans[0]}", f"Result: {ans[1]}"))
    return {"answer": ans, "steps": steps, "fmt": {"expr": e, "R": S}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    L = 0 if tr else 1
    h, d = float(P["h"]), float(P["d"])
    H, D = _F(P["h"]), _F(P["d"])
    rel = P.get("rel", "=")
    S = _SYM[rel]
    e = f"|{_inner(H)}|"
    ans = _answer(H, D, rel)
    dd = max(d, 0.0)
    lo, hi = math.floor(h - dd) - 3, math.ceil(h + dd) + 3
    gs = fig.add_gridspec(2, 1, height_ratios=[2.0, 1], left=0.07, right=0.97, top=0.84,
                          bottom=0.02, hspace=0.06)
    ax = fig.add_subplot(gs[0])
    nl = fig.add_subplot(gs[1])
    xs = np.linspace(lo - 0.6, hi + 0.6, 601)
    V = np.abs(xs - h)
    top = max(float(V.max()), d) * 1.08 + 0.5
    ax.set_xlim(lo - 0.6, hi + 0.6)
    ax.set_ylim(-0.6, top)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    if lo - 0.6 < 0 < hi + 0.6:
        ax.axvline(0, color="#6B7280", lw=1)
    vcur, = ax.plot([], [], color="#2563EB", lw=2.5, label=f"y = {e}")
    dline, = ax.plot([], [], color="#E07B39", lw=2.2, label=f"y = {_f(D)}")
    good = np.where(np.array([_ok(abs(x - h), rel, d) for x in xs]), V, np.nan)
    gcur, = ax.plot([], [], color="#16A34A", lw=5, alpha=0.6, solid_capstyle="butt")
    idots, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=6)
    pv, = ax.plot([], [], "o", ms=9, zorder=7)
    ax.legend(loc="upper right", fontsize=10)
    nl.axis("off")
    nl.set_xlim(lo - 0.6, hi + 0.6)
    nl.set_ylim(-1.3, 1.15)
    nl.add_patch(FancyArrowPatch((lo - 0.55, 0), (hi + 0.55, 0), arrowstyle="<|-|>", mutation_scale=14,
                                 color="#374151", lw=1.3))
    step = 1 if (hi - lo) <= 20 else 2
    for t in range(lo, hi + 1, step):
        nl.plot([t, t], [-0.1, 0.1], color="#374151", lw=1.1)
        nl.text(t, -0.4, str(t), ha="center", va="center", fontsize=9.5, color="#374151")
    cdot, = nl.plot([], [], "o", ms=10, color="#7C3AED", zorder=7)
    clab = nl.text(h, -0.85, "", ha="center", va="center", fontsize=11, color="#7C3AED", fontweight="bold")
    ar1 = FancyArrowPatch((h, 0.45), (h + 1, 0.45), arrowstyle="-|>", mutation_scale=14, color="#E07B39", lw=2)
    ar2 = FancyArrowPatch((h, 0.45), (h - 1, 0.45), arrowstyle="-|>", mutation_scale=14, color="#E07B39", lw=2)
    nl.add_patch(ar1)
    nl.add_patch(ar2)
    ar1.set_visible(False)
    ar2.set_visible(False)
    dl1 = nl.text(h + d / 2, 0.8, "", ha="center", fontsize=11, color="#E07B39", fontweight="bold")
    dl2 = nl.text(h - d / 2, 0.8, "", ha="center", fontsize=11, color="#E07B39", fontweight="bold")
    col = "#2563EB"
    seg1, = nl.plot([], [], color=col, lw=7, alpha=0.8, solid_capstyle="butt", zorder=4)
    seg2, = nl.plot([], [], color=col, lw=7, alpha=0.8, solid_capstyle="butt", zorder=4)
    hl, = nl.plot([], [], ls="none", marker="<", ms=14, color=col, zorder=5)
    hr, = nl.plot([], [], ls="none", marker=">", ms=14, color=col, zorder=5)
    closed = rel in ("=", "<=", ">=")
    ends, = nl.plot([], [], "o", ms=13, mew=2.4, mec=("#DC2626" if rel == "=" else col),
                    mfc=(("#DC2626" if rel == "=" else col) if closed else "white"), ls="none", zorder=6)
    pn, = nl.plot([], [], "o", ms=9, zorder=8)
    ptxt = nl.text(0.99, 0.97, "", transform=nl.transAxes, ha="right", va="top", fontsize=11,
                   fontweight="bold")
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    has = d > 0
    sols = [h - d, h + d] if has else []
    N = 150

    def update(i):
        p = _cl(i / 24)
        m = max(2, int(p * len(xs)))
        vcur.set_data(xs[:m], V[:m])
        if i >= 5:
            cdot.set_data([h], [0])
            clab.set_text(f"h = {_f(H)}")
        else:
            cdot.set_data([], [])
            clab.set_text("")
        q = _cl((i - 25) / 25)
        if q > 0:
            dline.set_data([xs[0], xs[0] + (xs[-1] - xs[0]) * q], [d, d])
        else:
            dline.set_data([], [])
        if q > 0.03 and has:
            ar1.set_positions((h, 0.45), (h + d * q, 0.45))
            ar2.set_positions((h, 0.45), (h - d * q, 0.45))
            ar1.set_visible(True)
            ar2.set_visible(True)
        else:
            ar1.set_visible(False)
            ar2.set_visible(False)
        dl1.set_text(f"d = {_f(D)}" if (q >= 1 and has) else "")
        dl2.set_text(f"d = {_f(D)}" if (q >= 1 and has) else "")
        if i >= 52 and has:
            idots.set_data(sols, [d, d])
            ends.set_data(sols, [0, 0])
        else:
            idots.set_data([], [])
            ends.set_data([], [])
        r = _cl((i - 62) / 26)
        if r > 0 and has and rel != "=":
            gcur.set_data(xs, good)
            if rel in ("<", "<="):
                seg1.set_data([h - d * r, h + d * r], [0, 0])
                seg2.set_data([], [])
                hl.set_data([], [])
                hr.set_data([], [])
            else:
                el = (h - d) + ((lo - 0.45) - (h - d)) * r
                er = (h + d) + ((hi + 0.45) - (h + d)) * r
                seg1.set_data([h - d, el], [0, 0])
                seg2.set_data([h + d, er], [0, 0])
                hl.set_data([el], [0])
                hr.set_data([er], [0])
        else:
            gcur.set_data([], [])
            seg1.set_data([], [])
            seg2.set_data([], [])
            hl.set_data([], [])
            hr.set_data([], [])
        if i >= 96 and has:
            if rel == "=":
                if i < 121:
                    xp = h + d * _cl((i - 96) / 22)
                else:
                    xp = h - d * _cl((i - 121) / 22)
            else:
                xp = (lo - 0.3) + (hi - lo + 0.6) * _cl((i - 96) / 50)
            dist = abs(xp - h)
            ok = _ok(round(dist, 9), rel, d)
            cc = "#16A34A" if ok else "#DC2626"
            pn.set_data([xp], [0])
            pn.set_color(cc)
            pv.set_data([xp], [dist])
            pv.set_color(cc)
            ptxt.set_color(cc)
            ptxt.set_text(f"x = {xp:.1f}:  {e} = {dist:.1f} {S} {_f(D)} ?  " + ("✓" if ok else "✗"))
        else:
            pn.set_data([], [])
            pv.set_data([], [])
            ptxt.set_text("")
        if i < 25:
            info.set_text((f"1) {e} = x ile {_f(H)} arasındaki uzaklık") if tr else
                          (f"1) {e} = distance from x to {_f(H)}"))
        elif i < 52:
            info.set_text((f"2) Merkez {_f(H)}, her iki yöne {_f(D)} birim") if tr else
                          (f"2) Centre {_f(H)}, go {_f(D)} units both ways"))
        elif i < 90:
            if has:
                info.set_text((f"3) Sınır noktaları: x = {_f(H - D)} ve x = {_f(H + D)}") if tr else
                              (f"3) Boundary points: x = {_f(H - D)} and x = {_f(H + D)}"))
            else:
                info.set_text(ans[L])
        else:
            info.set_text(("Çözüm: " if tr else "Solution: ") + ans[L])
        return []

    return N, update


def vary(P, rnd):
    h0 = P.get("h", 0)
    if abs(h0) > 10:
        h = int(h0) + rnd.randint(-5, 5)
    else:
        h = rnd.randint(-5, 5)
    return {"h": h, "d": rnd.randint(1, 6), "rel": P.get("rel", "=")}
''',
}
EXAMPLES += [
    {"id": "alg-absval-1", "kind": "absolute_value_eq",
     "title": ("Mutlak değerli denklem", "Absolute value equation"),
     "q": ("{expr} = {d} denklemini çöz ve çözümleri sayı doğrusunda uzaklık olarak yorumla.",
           "Solve {expr} = {d} and interpret the solutions as distances on the number line."),
     "P": {"h": 3, "d": 5, "rel": "="}},
    {"id": "alg-absval-2", "kind": "absolute_value_eq",
     "title": ("Mutlak değerli eşitsizlik (küçüktür)", "Absolute value inequality (less than)"),
     "q": ("{expr} {R} {d} eşitsizliğini çöz; çözüm kümesini aralık olarak yaz.",
           "Solve {expr} {R} {d}; write the solution set as an interval."),
     "P": {"h": -2, "d": 4, "rel": "<="}},
    {"id": "alg-absval-3", "kind": "absolute_value_eq", "topics": ["tolerance", "word problem", "sözel problem"],
     "title": ("Sözel problem: tolerans kontrolü", "Word problem: tolerance check"),
     "q": ("Bir fabrikada uzunluğu {h} mm'den {d} mm'den fazla sapan cıvatalar reddediliyor: {expr} {R} {d}. "
           "Hangi uzunluklar reddedilir?",
           "A factory rejects bolts whose length differs from {h} mm by more than {d} mm: {expr} {R} {d}. "
           "Which lengths are rejected?"),
     "P": {"h": 40, "d": 2, "rel": ">"}},
]
