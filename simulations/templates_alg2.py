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
        mid = f"−1/{_co(m1)}"
        mid = "" if mid.replace("−", "-") == _f(m2) else mid + " = "
        steps.append((f"Dik doğrularda m₁·m₂ = −1  ⇒  m₂ = −1/m₁ = {mid}{_f(m2)}",
                      f"Perpendicular lines: m₁·m₂ = −1  ⇒  m₂ = −1/m₁ = {mid}{_f(m2)}"))
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
    L = 4 * R
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.92, bottom=0.07)
    fw, fh = fig.get_size_inches()
    ratio = max(1.0, (fw * 0.91) / (fh * 0.85))
    ax.set_xlim(-R * ratio, R * ratio)
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
    ox, oy = (ux, uy) if perp else (vx, vy)
    if perp and ox * (-px) + oy * (-py) < 0:
        ox, oy = -ox, -oy
    ptxt = ax.text(px + 0.11 * R * ox, py + 0.11 * R * oy, "", color="#DC2626", fontsize=11,
                   fontweight="bold", zorder=8, ha="center", va="center")
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
                chk = "yatay ⊥ düşey ✓" if tr else "horizontal ⊥ vertical ✓"
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
    "topics": ["function transformations", "transformations of functions", "shifting graphs", "shifting",
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
    ghost, = ax.plot(xs, _base(par, xs), "--", color="#6B7280", lw=1.6, alpha=0.8,
                     label=f"f(x) = {f0}")
    cur, = ax.plot([], [], color="#2563EB", lw=2.6, label=f"g(x) = {s3}")
    sdots, = ax.plot([], [], "o", ms=8, color="#E07B39", zorder=6)
    kdot, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=7)
    ktxt = ax.text(0, 0, "", color="#DC2626", fontsize=11, fontweight="bold", zorder=8,
                   va="top" if a > 0 else "bottom")
    harr = FancyArrowPatch((0, 0), (1, 0), arrowstyle="-|>", mutation_scale=16, color="#16A34A", lw=2.2)
    karr = FancyArrowPatch((0, 0), (0, 1), arrowstyle="-|>", mutation_scale=16, color="#7C3AED", lw=2.2)
    ax.add_patch(harr)
    ax.add_patch(karr)
    harr.set_visible(False)
    karr.set_visible(False)
    htxt = ax.text(h / 2, -(hi - lo) * 0.05, "", color="#16A34A", fontsize=11, ha="center", va="top")
    ktx2 = ax.text(h + (xhi - xlo) * 0.015, k / 2, "", color="#7C3AED", fontsize=11, va="center",
                   bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    fig.legend(handles=[ghost, cur], loc="upper right", bbox_to_anchor=(0.985, 0.985), fontsize=10)
    N = 150

    def update(i):
        pa = _cl((i - 24) / 30)
        ph = _cl((i - 60) / 30)
        pk = _cl((i - 96) / 30)
        at, ht, kt = 1 + (a - 1) * pa, h * ph, k * pk
        ghost.set_visible(i >= 22)
        if i < 22:
            m = max(2, int(_cl(i / 20) * len(xs)))
            cur.set_data(xs[:m], _base(par, xs[:m]))
        else:
            cur.set_data(xs, at * _base(par, xs - ht) + kt)
        if i >= 8:
            sdots.set_data(sx0 + ht, at * sy0 + kt)
            kdot.set_data([ht], [kt])
            ktxt.set_position((ht + (xhi - xlo) * 0.025, kt + (hi - lo) * (-0.02 if a > 0 else 0.02)))
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
        (f"{dv[0]}  ⇒  x {S2} {_f(c - b)}/{_f(a) if a > 0 else '(' + _f(a) + ')'} = {_f(x0)}",
         f"{dv[1]}  ⇒  x {S2} {_f(c - b)}/{_f(a) if a > 0 else '(' + _f(a) + ')'} = {_f(x0)}"),
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
    sign = P.get("sign", "<")
    if P["a"] > 0 and P["b"] > 0 and P["c"] > P["b"]:
        a = rnd.choice([2, 3, 4, 5, 6])
        b = rnd.choice([5, 10, 12, 15, 20, 25, 30])
        return {"a": a, "b": b, "c": b + a * rnd.randint(3, 12) + rnd.choice([0, 0, 1, 2]), "sign": sign}
    a = rnd.choice([2, 3, 4, 5]) * (1 if P["a"] > 0 else -1)
    x0 = rnd.randint(-6, 6)
    b = rnd.choice([v for v in range(-12, 13) if v != 0])
    return {"a": a, "b": b, "c": a * x0 + b, "sign": sign}
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
    ax.tick_params(labelbottom=False)
    ax.axhline(0, color="#6B7280", lw=1)
    if lo - 0.6 < 0 < hi + 0.6:
        ax.axvline(0, color="#6B7280", lw=1)
    vcur, = ax.plot([], [], color="#2563EB", lw=2.5, label=f"y = {e}")
    dline, = ax.plot([], [], color="#E07B39", lw=2.2, label=f"y = {_f(D)}")
    good = np.where(np.array([_ok(abs(x - h), rel, d) for x in xs]), V, np.nan)
    gcur, = ax.plot([], [], color="#16A34A", lw=5, alpha=0.6, solid_capstyle="butt")
    idots, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=6)
    pv, = ax.plot([], [], "o", ms=9, zorder=7)
    ax.legend(loc="lower left", fontsize=10)
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
    ptxt = ax.text(0.5, 0.97, "", transform=ax.transAxes, ha="center", va="top", fontsize=11.5,
                   fontweight="bold", bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
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

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["exponential_growth"] = {
    "course": "alg",
    "title": ("Üstel büyüme ve bileşik faiz", "Exponential growth and compound interest"),
    "topics": ["exponential growth", "exponential decay", "compound interest", "exponential function",
               "exponential functions", "growth and decay", "continuous compounding", "depreciation",
               "population growth", "half-life", "doubling time",
               "üstel büyüme", "üstel azalma", "bileşik faiz", "üstel fonksiyon", "nüfus artışı"],
    "code": r'''
import math
import numpy as np


def _cl(t):
    return min(1.0, max(0.0, t))


def _pct(r):
    return f"{abs(r) * 100:g}"


def _freq(m):
    names = {1: ("yıllık", "annually"), 2: ("6 ayda bir", "semi-annually"),
             4: ("3 ayda bir", "quarterly"), 12: ("aylık", "monthly"), 365: ("günlük", "daily")}
    if m <= 0:
        return ("sürekli", "continuously")
    return names.get(m, (f"yılda {m} kez", f"{m} times a year"))


def _model(P):
    P0, r, n = float(P["P0"]), float(P["r"]), float(P["n"])
    m = int(P.get("compound", 1))
    dec = int(P.get("dec", 2))
    if m <= 0:
        return P0, r, n, m, dec, None, P0 * math.exp(r * n)
    g = 1 + r / m
    return P0, r, n, m, dec, g, P0 * g ** (m * n)


def _value(P0, r, m, t):
    t = np.asarray(t, dtype=float)
    if m <= 0:
        return P0 * np.exp(r * t)
    return P0 * (1 + r / m) ** (m * t)


def _m(v, dec):
    return f"{v:.{dec}f}"


def solve(P):
    P0, r, n, m, dec, g, A = _model(P)
    grow = r >= 0
    fr = _freq(m)
    sg = "+" if grow else "−"
    if m == 1:
        cmp_ = ("yıllık dönemler", "yearly periods")
    else:
        cmp_ = (f"{fr[0]} bileşik", f"compounded {fr[1]}")
    steps = [(f"P₀ = {P0:g}, oran r = {sg}%{_pct(r)} = {r:g}, süre t = {n:g}, {cmp_[0]}",
              f"P₀ = {P0:g}, rate r = {sg}{_pct(r)}% = {r:g}, time t = {n:g}, {cmp_[1]}")]
    if m <= 0:
        steps.append(("Sürekli bileşik: A = P₀·e^(r·t)", "Continuous compounding: A = P₀·e^(r·t)"))
        steps.append((f"A = {P0:g}·e^({r:g}·{n:g}) = {P0:g}·e^{r * n:g} ≈ {_m(A, dec)}",
                      f"A = {P0:g}·e^({r:g}·{n:g}) = {P0:g}·e^{r * n:g} ≈ {_m(A, dec)}"))
        k_rate = r
    else:
        mt = m * n
        if m == 1:
            steps.append(("Formül: A = P₀(1 + r)^t", "Formula: A = P₀(1 + r)^t"))
            steps.append((f"Yıllık çarpan: 1 + r = 1 {'+' if grow else '−'} {abs(r):g} = {g:g}  "
                           f"(her yıl değer {g:g} ile çarpılır)",
                           f"Yearly factor: 1 + r = 1 {'+' if grow else '−'} {abs(r):g} = {g:g}  "
                           f"(each year the value becomes {g * 100:g}% of the previous one)"))
        else:
            steps.append(("Formül: A = P₀(1 + r/m)^(m·t)", "Formula: A = P₀(1 + r/m)^(m·t)"))
            steps.append((f"Dönem çarpanı: 1 + r/m = 1 + {r:g}/{m} = {g:.6g};  dönem sayısı m·t = {m}·{n:g} = {mt:g}",
                           f"Factor per period: 1 + r/m = 1 + {r:g}/{m} = {g:.6g};  number of periods m·t = {m}·{n:g} = {mt:g}"))
        steps.append((f"A = {P0:g}·{g:.6g}^{mt:g} = {P0:g}·{g ** mt:.6f} ≈ {_m(A, dec)}",
                      f"A = {P0:g}·{g:.6g}^{mt:g} = {P0:g}·{g ** mt:.6f} ≈ {_m(A, dec)}"))
        k_rate = m * math.log(g)
    if grow:
        steps.append((f"Toplam artış: A − P₀ ≈ {_m(A - P0, dec)}", f"Total increase: A − P₀ ≈ {_m(A - P0, dec)}"))
        steps.append((f"Doğrusal (basit) artışla olsaydı: P₀(1 + r·t) = {_m(P0 * (1 + r * n), dec)}",
                      f"With simple (linear) growth it would be: P₀(1 + r·t) = {_m(P0 * (1 + r * n), dec)}"))
        if k_rate > 0:
            td = math.log(2) / k_rate
            steps.append((f"İkiye katlanma süresi ≈ ln 2 / {k_rate:.5f} ≈ {td:.2f}",
                          f"Doubling time ≈ ln 2 / {k_rate:.5f} ≈ {td:.2f}"))
    else:
        steps.append((f"Toplam azalma: P₀ − A ≈ {_m(P0 - A, dec)}", f"Total decrease: P₀ − A ≈ {_m(P0 - A, dec)}"))
        if k_rate < 0:
            th = math.log(0.5) / k_rate
            steps.append((f"Yarılanma süresi ≈ ln(0.5) / ({k_rate:.5f}) ≈ {th:.2f}",
                          f"Half-life ≈ ln(0.5) / ({k_rate:.5f}) ≈ {th:.2f}"))
    return {"answer": f"A ≈ {_m(A, dec)}", "steps": steps,
            "fmt": {"pct": _pct(r), "freq": fr}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    P0, r, n, m, dec, g, A = _model(P)
    grow = r >= 0
    per = m >= 1 and m * n <= 30 and abs(m * n - round(m * n)) < 1e-9
    if per:
        nb = int(round(m * n))
        ts = np.arange(nb + 1) / m
    else:
        nb = int(math.ceil(n - 1e-9))
        ts = np.minimum(np.arange(nb + 1, dtype=float), n)
    vals = _value(P0, r, m, ts)
    step = ts[1] - ts[0] if len(ts) > 1 else 1.0
    tt = np.linspace(0, n, 300)
    yy = _value(P0, r, m, tt)
    lin = P0 * (1 + r * tt)
    top = max(float(vals.max()), float(yy.max()), float(lin.max()) if grow else 0.0, P0) * 1.2
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.82, bottom=0.11)
    ax.set_xlim(-0.7 * step, n + 0.7 * step)
    ax.set_ylim(0, top)
    ax.grid(alpha=0.3, axis="y")
    ax.set_xlabel("t (yıl)" if tr else "t (years)")
    ax.set_ylabel("A")
    bars = ax.bar(ts, np.zeros(len(ts)), width=0.7 * step, color="#2563EB", alpha=0.35,
                  edgecolor="#2563EB", label=("dönem sonu değeri" if tr else "value at end of period"))
    curve, = ax.plot([], [], color="#2563EB", lw=2.6,
                     label=("üstel model A(t)" if tr else "exponential model A(t)"))
    simple, = ax.plot([], [], "--", color="#6B7280", lw=1.8,
                      label=("doğrusal (basit) artış" if tr else "linear (simple) growth"))
    vtxt = ax.text(0, 0, "", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#E07B39")
    final_t = ax.text(ts[-1] + 0.35 * step, A + top * 0.035, "", ha="right", va="bottom", fontsize=12,
                      fontweight="bold", color="#DC2626", zorder=8,
                      bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    hl, = ax.plot([], [], ":", color="#DC2626", lw=1.4)
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    handles = [bars, curve] + ([simple] if grow else [])
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.985), fontsize=9.5)
    fr = _freq(m)
    starts = [4 + k * 84.0 / max(1, nb) for k in range(nb + 1)]
    N = 150

    def expo(k):
        if m <= 0:
            return f"e^({r:g}·{ts[k]:g})"
        return f"{g:.6g}^{m * ts[k]:g}"

    def update(i):
        cur = -1
        for k, b in enumerate(bars):
            if i >= starts[k]:
                grow_k = _cl((i - starts[k]) / 4)
                b.set_height(vals[k] * grow_k)
                cur = k
            else:
                b.set_height(0)
        for k, b in enumerate(bars):
            if i >= 122 and k == len(bars) - 1:
                b.set_facecolor("#DC2626")
                b.set_alpha(0.75)
            elif k == cur and i < 92:
                b.set_facecolor("#E07B39")
                b.set_alpha(0.8)
            else:
                b.set_facecolor("#2563EB")
                b.set_alpha(0.35)
        if 0 <= cur and i < 92:
            vtxt.set_position((ts[cur], vals[cur] + top * 0.01))
            vtxt.set_text(_m(vals[cur], dec))
        else:
            vtxt.set_text("")
        q = _cl((i - 92) / 28)
        mm = max(2, int(q * len(tt)))
        if q > 0:
            curve.set_data(tt[:mm], yy[:mm])
            if grow:
                simple.set_data(tt[:mm], lin[:mm])
            else:
                simple.set_data([], [])
        else:
            curve.set_data([], [])
            simple.set_data([], [])
        if i >= 122:
            final_t.set_text(f"A ≈ {_m(A, dec)}")
            hl.set_data([0, n], [A, A])
        else:
            final_t.set_text("")
            hl.set_data([], [])
        if i < 92:
            k = max(cur, 0)
            if per and m > 1:
                lab = ("Dönem" if tr else "Period") + f" {int(round(m * ts[k]))}"
            else:
                lab = ("Yıl" if tr else "Year") + f" {ts[k]:g}"
            head = (f"1) P₀ = {P0:g}, %{_pct(r)} {'artış' if grow else 'azalış'}, {fr[0]}" if tr else
                    f"1) P₀ = {P0:g}, {_pct(r)}% {'growth' if grow else 'decay'}, {fr[1]}")
            info.set_text(head + f"\n    {lab}: A = {P0:g}·{expo(k)} ≈ {_m(vals[k], dec)}")
        elif i < 122:
            if m <= 0:
                form = "A(t) = P₀·e^(r·t)"
            elif m == 1:
                form = f"A(t) = {P0:g}·{g:g}^t"
            else:
                form = f"A(t) = {P0:g}·(1 + {r:g}/{m})^({m}t)"
            info.set_text((f"2) Sürekli eğri: {form}" + ("\n    kesikli çizgi: doğrusal artış" if grow else "")) if tr else
                          (f"2) Smooth curve: {form}" + ("\n    dashed: linear growth" if grow else "")))
        else:
            diff = A - P0
            info.set_text((f"t = {n:g}:  A ≈ {_m(A, dec)}\n" +
                           (f"artış ≈ {_m(diff, dec)}" if grow else f"azalış ≈ {_m(-diff, dec)}")) if tr else
                          (f"t = {n:g}:  A ≈ {_m(A, dec)}\n" +
                           (f"increase ≈ {_m(diff, dec)}" if grow else f"decrease ≈ {_m(-diff, dec)}")))
        return []

    return N, update


def vary(P, rnd):
    m = int(P.get("compound", 1))
    if float(P["r"]) < 0:
        r = -rnd.choice([0.05, 0.08, 0.1, 0.12, 0.15, 0.2])
    else:
        r = rnd.choice([0.02, 0.03, 0.04, 0.05, 0.06, 0.08])
    P0 = int(round(float(P["P0"]) * rnd.choice([0.5, 0.8, 1.2, 1.5, 2.0])))
    out = {"P0": max(P0, 10), "r": r, "n": rnd.randint(3, 12), "compound": m}
    if "dec" in P:
        out["dec"] = P["dec"]
    return out
''',
}
EXAMPLES += [
    {"id": "alg-expgrowth-1", "kind": "exponential_growth", "topics": ["interest", "faiz"],
     "title": ("Aylık bileşik faiz", "Interest compounded monthly"),
     "q": ("{P0} TL, yıllık %{pct} faizle {freq} bileşik olarak {n} yıl bankada kalıyor. "
           "Sonunda hesapta ne kadar para olur?",
           "{P0} is deposited at {pct}% annual interest compounded {freq} for {n} years. "
           "How much is in the account at the end?"),
     "P": {"P0": 1000, "r": 0.06, "n": 10, "compound": 12}},
    {"id": "alg-expgrowth-2", "kind": "exponential_growth", "topics": ["population", "nüfus"],
     "title": ("Nüfus artışı", "Population growth"),
     "q": ("{P0} nüfuslu bir kasabanın nüfusu her yıl %{pct} artıyor. {n} yıl sonra nüfus yaklaşık kaç olur?",
           "A town of {P0} people grows by {pct}% every year. About how many people live there after {n} years?"),
     "P": {"P0": 25000, "r": 0.03, "n": 8, "compound": 1, "dec": 0}},
    {"id": "alg-expgrowth-3", "kind": "exponential_growth", "topics": ["depreciation", "değer kaybı"],
     "title": ("Üstel azalma: araç değer kaybı", "Exponential decay: car depreciation"),
     "q": ("{P0} TL değerindeki bir aracın değeri her yıl %{pct} azalıyor. {n} yıl sonra değeri ne olur?",
           "A car worth {P0} loses {pct}% of its value every year. What is it worth after {n} years?"),
     "P": {"P0": 30000, "r": -0.15, "n": 5, "compound": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["logarithm"] = {
    "course": "alg",
    "title": ("Logaritma ve taban değiştirme", "Logarithms and change of base"),
    "topics": ["logarithm", "logarithms", "logarithmic function", "logarithmic functions",
               "change of base", "inverse of exponential", "exponential and logarithmic",
               "solving exponential equations", "logaritma", "logaritma fonksiyonu",
               "taban değiştirme", "üstel ve logaritmik"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle

_SUBD = "₀₁₂₃₄₅₆₇₈₉"
_SUPD = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def _cl(t):
    return min(1.0, max(0.0, t))


def _num(v):
    v = float(v)
    if abs(v - round(v)) < 1e-9 and abs(v) < 1e12:
        return str(int(round(v)))
    return f"{v:.6g}"


def _sub(b):
    s = _num(b)
    if all(ch.isdigit() for ch in s):
        return "".join(_SUBD[int(ch)] for ch in s)
    return "_" + s


def _sup(k):
    return "".join("⁻" if ch == "-" else _SUPD[int(ch)] for ch in str(int(k)))


def _lg(b, v):
    return f"log{_sub(b)} {_num(v)}"


def _exact(b, v):
    fb = Fraction(b).limit_denominator(10 ** 6)
    fv = Fraction(v).limit_denominator(10 ** 6)
    if fb <= 0 or fb == 1 or fv <= 0:
        return None
    for k in range(-12, 31):
        if fb ** k == fv:
            return k
    return None


def solve(P):
    b, v = float(P["base"]), float(P["value"])
    k = _exact(b, v)
    y = math.log(v) / math.log(b)
    L = _lg(b, v)
    B, V = _num(b), _num(v)
    steps = [(f"Tanım: {L} = y  ⇔  {B}^y = {V}", f"Definition: {L} = y  ⇔  {B}^y = {V}")]
    if k is not None:
        steps.append((f"{V} = {B}{_sup(k)} olduğundan y = {k}", f"Since {V} = {B}{_sup(k)}, y = {k}"))
    else:
        lo = math.floor(y)
        p1, p2 = b ** lo, b ** (lo + 1)
        if p1 < p2:
            a1, a2, e1, e2 = p1, p2, lo, lo + 1
        else:
            a1, a2, e1, e2 = p2, p1, lo + 1, lo
        txt = f"{B}{_sup(e1)} = {_num(a1)} < {V} < {_num(a2)} = {B}{_sup(e2)}  ⇒  {lo} < y < {lo + 1}"
        steps.append((f"Tahmin: {txt}", f"Estimate: {txt}"))
    ln_v, ln_b = math.log(v), math.log(b)
    steps.append((f"Taban değiştirme: {L} = ln {V} / ln {B} = {ln_v:.4f} / {ln_b:.4f} ≈ {y:.4f}",
                  f"Change of base: {L} = ln {V} / ln {B} = {ln_v:.4f} / {ln_b:.4f} ≈ {y:.4f}"))
    steps.append((f"10 tabanıyla da aynı: log {V} / log {B} = {math.log10(v):.4f} / {math.log10(b):.4f} ≈ {y:.4f}",
                  f"Base 10 gives the same: log {V} / log {B} = {math.log10(v):.4f} / {math.log10(b):.4f} ≈ {y:.4f}"))
    steps.append((f"Kontrol: {B}^{y:.4f} ≈ {b ** y:.4f} ✓", f"Check: {B}^{y:.4f} ≈ {b ** y:.4f} ✓"))
    steps.append((f"y = {B}ˣ ile y = log{_sub(b)} x ters fonksiyonlardır; grafikleri y = x doğrusuna göre simetriktir.",
                  f"y = {B}ˣ and y = log{_sub(b)} x are inverse functions; their graphs are mirror images in y = x."))
    ans = f"{L} = {k}" if k is not None else f"{L} ≈ {y:.4f}"
    return {"answer": ans, "steps": steps, "fmt": {"L": L, "eq": f"{B}^y = {V}"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    b, v = float(P["base"]), float(P["value"])
    k = _exact(b, v)
    ys = math.log(v) / math.log(b)
    B, V = _num(b), _num(v)
    L = _lg(b, v)
    lb = math.log(b)
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.25], left=0.05, right=0.98, top=0.82, bottom=0.09,
                          wspace=0.16)
    ax = fig.add_subplot(gs[0, 0])
    ar = fig.add_subplot(gs[0, 1])
    lo_, hi_ = -3.0, 7.0
    ax.set_xlim(lo_, hi_)
    ax.set_ylim(lo_, hi_)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    ax.plot([lo_, hi_], [lo_, hi_], "--", color="#6B7280", lw=1.2, label="y = x")
    xe = np.linspace(lo_, hi_, 800)
    ye = b ** xe
    mask = (ye <= hi_ + 0.5) & (ye >= lo_ - 0.5)
    xe, ye = xe[mask], ye[mask]
    ecur, = ax.plot([], [], color="#2563EB", lw=2.5, label=f"y = {B}ˣ")
    lcur, = ax.plot([], [], color="#E07B39", lw=2.5, label=f"y = log{_sub(b)} x")
    kx = [0.0, 1.0] if b <= 6.5 else [0.0, -1.0]
    ky = [b ** t for t in kx]
    pe, = ax.plot([], [], "o", color="#2563EB", ms=7, zorder=6)
    pl, = ax.plot([], [], "o", color="#E07B39", ms=7, zorder=6)
    links = [ax.plot([], [], ":", color="#7C3AED", lw=1.6)[0] for _ in kx]
    plab = [ax.text(ky[j] + 0.25, kx[j] - 0.15, "", color="#E07B39", fontsize=9, va="top")
            for j in range(len(kx))]
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title((f"y = {B}ˣ ve tersi y = log{_sub(b)} x") if tr else (f"y = {B}ˣ and its inverse y = log{_sub(b)} x"),
                 fontsize=11)
    top = 1.9 * v
    if b > 1:
        xa, xb = ys + math.log(0.03) / lb, ys + math.log(1.9) / lb
    else:
        xa, xb = ys + math.log(1.9) / lb, ys + math.log(0.03) / lb
    pad = (xb - xa) * 0.04
    ar.set_xlim(xa - pad, xb + pad)
    ar.set_ylim(-0.04 * top, top)
    ar.grid(alpha=0.3)
    ar.axhline(0, color="#6B7280", lw=1)
    if xa - pad < 0 < xb + pad:
        ar.axvline(0, color="#6B7280", lw=1)
    xr = np.linspace(xa - pad, xb + pad, 500)
    yr = b ** xr
    rcur, = ar.plot([], [], color="#2563EB", lw=2.5)
    hline, = ar.plot([], [], color="#E07B39", lw=2.0)
    hlab = ar.text(xa, v, "", color="#E07B39", fontsize=11, ha="left", va="bottom", fontweight="bold")
    idot, = ar.plot([], [], "o", color="#DC2626", ms=10, zorder=7)
    drop, = ar.plot([], [], "--", color="#DC2626", lw=1.5)
    right_half = (ys - xa) / (xb - xa) > 0.5
    ylab = ar.text(ys, 0.02 * top, "", color="#DC2626", fontsize=12, fontweight="bold",
                   ha="right" if right_half else "left", va="bottom",
                   bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    flo = math.floor(ys)
    band = Rectangle((flo, -0.04 * top), 1.0, 1.04 * top, fc="#16A34A", ec="none", alpha=0.12)
    ar.add_patch(band)
    band.set_visible(False)
    bx = min(max(flo + 0.5, xa), xb)
    blab = ar.text(bx, 0.62 * top, "", color="#16A34A", fontsize=11, ha="center", fontweight="bold")
    ar.set_title((f"{B}^y = {V} denklemini çöz") if tr else (f"Solve {B}^y = {V}"), fontsize=11)
    ln_v = math.log(v)
    rows = [f"y = {L}", f"   = ln {V} / ln {B}", f"   = {ln_v:.4f} / {lb:.4f}",
            (f"   = {k}" if k is not None else f"   ≈ {ys:.4f}")]
    box = ar.text(0.03, 0.97, "", transform=ar.transAxes, va="top", fontsize=11.5, family="DejaVu Sans Mono",
                  bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"), zorder=9)
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    N = 150

    def update(i):
        p = _cl(i / 34)
        m = max(2, int(p * len(xe)))
        ecur.set_data(xe[:m], ye[:m])
        t = _cl((i - 38) / 32)
        if t > 0:
            lcur.set_data((1 - t) * xe + t * ye, (1 - t) * ye + t * xe)
        else:
            lcur.set_data([], [])
        if i >= 34:
            pe.set_data(kx, ky)
        else:
            pe.set_data([], [])
        if i >= 72:
            pl.set_data(ky, kx)
            for j in range(len(kx)):
                links[j].set_data([kx[j], ky[j]], [ky[j], kx[j]])
                plab[j].set_text(f"({_num(ky[j])}, {_num(kx[j])})" if abs(ky[j] - round(ky[j])) < 1e-9
                                 else f"({ky[j]:.2f}, {_num(kx[j])})")
        else:
            pl.set_data([], [])
            for j in range(len(kx)):
                links[j].set_data([], [])
                plab[j].set_text("")
        q = _cl((i - 78) / 20)
        mr = max(2, int(q * len(xr)))
        if q > 0:
            rcur.set_data(xr[:mr], yr[:mr])
        else:
            rcur.set_data([], [])
        h = _cl((i - 92) / 12)
        if h > 0:
            hline.set_data([xa - pad, xa - pad + (ys - xa + pad) * h], [v, v])
            hlab.set_text(f"y = {V}")
        else:
            hline.set_data([], [])
            hlab.set_text("")
        if i >= 104:
            idot.set_data([ys], [v])
            dd = _cl((i - 104) / 10)
            drop.set_data([ys, ys], [v, v - v * dd])
        else:
            idot.set_data([], [])
            drop.set_data([], [])
        ylab.set_text((f" y = {k} " if k is not None else f" y ≈ {ys:.3f} ") if i >= 114 else "")
        band.set_visible(k is None and i >= 108)
        blab.set_text(f"{flo} < y < {flo + 1}" if (k is None and i >= 108) else "")
        nshow = 0 if i < 118 else min(4, 1 + (i - 118) // 8)
        box.set_text("\n".join(rows[:nshow]))
        box.set_visible(nshow > 0)
        if i < 36:
            info.set_text((f"1) Üstel fonksiyon y = {B}ˣ") if tr else (f"1) Exponential function y = {B}ˣ"))
        elif i < 72:
            info.set_text((f"2) y = x doğrusuna göre yansıt: (x, y) → (y, x)\n    ⇒ y = log{_sub(b)} x (ters fonksiyon)") if tr else
                          (f"2) Reflect in y = x: (x, y) → (y, x)\n    ⇒ y = log{_sub(b)} x (inverse function)"))
        elif i < 92:
            info.set_text((f"3) {L} = y  ⇔  {B}^y = {V}") if tr else (f"3) {L} = y  ⇔  {B}^y = {V}"))
        elif i < 118:
            info.set_text((f"4) y = {V} doğrusu eğriyi nerede kesiyor?") if tr else
                          (f"4) Where does the line y = {V} meet the curve?"))
        else:
            res = f"{L} = {k}" if k is not None else f"{L} ≈ {ys:.4f}"
            info.set_text(("5) Taban değiştirme: " if tr else "5) Change of base: ") + res)
        return []

    return N, update


def vary(P, rnd):
    b0, v0 = float(P["base"]), float(P["value"])
    if _exact(b0, v0) is not None:
        b = rnd.choice([2, 3, 4, 5, 10])
        kmax = {2: 9, 3: 6, 4: 5, 5: 4, 10: 4}[b]
        k = rnd.randint(2, kmax)
        return {"base": b, "value": b ** k}
    b = rnd.choice([2, 3, 5, 7])
    while True:
        v = rnd.randint(10, 500)
        if _exact(b, v) is None:
            return {"base": b, "value": v}
''',
}
EXAMPLES += [
    {"id": "alg-log-1", "kind": "logarithm",
     "title": ("Logaritmanın tanımı", "Definition of a logarithm"),
     "q": ("{L} değerini hesapla ({eq} denklemini çözerek).", "Evaluate {L} (by solving {eq})."),
     "P": {"base": 2, "value": 32}},
    {"id": "alg-log-2", "kind": "logarithm",
     "title": ("Taban değiştirme kuralı", "Change-of-base formula"),
     "q": ("Taban değiştirme kuralını kullanarak {L} değerini dört ondalık basamağa kadar bul.",
           "Use the change-of-base formula to find {L} to four decimal places."),
     "P": {"base": 5, "value": 40}},
    {"id": "alg-log-3", "kind": "logarithm", "topics": ["exponential equation", "üstel denklem", "word problem"],
     "title": ("Sözel problem: bakteri kolonisi", "Word problem: bacteria colony"),
     "q": ("Bir bakteri kolonisi her saat {base} katına çıkıyor. Koloni kaç saatte başlangıçtakinin {value} "
           "katı olur? ({eq}, y = {L})",
           "A bacteria colony multiplies by {base} every hour. After how many hours is it {value} times its "
           "starting size? ({eq}, y = {L})"),
     "P": {"base": 3, "value": 200}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["polynomial_roots"] = {
    "course": "alg",
    "title": ("Polinomun kökleri ve katlılık", "Polynomial zeros and multiplicity"),
    "topics": ["polynomial", "polynomials", "polynomial functions", "zeros of polynomials",
               "roots of polynomials", "multiplicity", "factored form", "end behavior",
               "graphing polynomials", "factor theorem", "polinom", "polinomlar", "polinom kökleri",
               "katlı kök", "polinom fonksiyonları", "çarpanlara ayırma"],
    "code": r'''
import numpy as np
from collections import Counter

_SUPD = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def _cl(t):
    return min(1.0, max(0.0, t))


def _sup(n):
    return "".join(_SUPD[int(ch)] for ch in str(int(n)))


def _pstr(coeffs):
    c = [int(round(float(t))) for t in coeffs]
    deg = len(c) - 1
    out = ""
    for j, cj in enumerate(c):
        p = deg - j
        if cj == 0:
            continue
        mag = abs(cj)
        if p == 0:
            body = str(mag)
        else:
            body = ("" if mag == 1 else str(mag)) + "x" + (_sup(p) if p > 1 else "")
        if out == "":
            out = ("-" if cj < 0 else "") + body
        else:
            out += (" - " if cj < 0 else " + ") + body
    return out or "0"


def _order(roots):
    cnt = Counter(int(r) for r in roots)
    return sorted(cnt, key=lambda r: (r != 0, r)), cnt


def _factor(r, m):
    base = "x" if r == 0 else (f"(x - {r})" if r > 0 else f"(x + {-r})")
    return base + (_sup(m) if m > 1 else "")


def _fact(k, roots):
    order, cnt = _order(roots)
    pre = "" if k == 1 else ("-" if k == -1 else str(k))
    return pre + "".join(_factor(r, cnt[r]) for r in order)


def _kind(m):
    if m % 2 == 0:
        return (f"katlılık {m} (çift) ⇒ eksene değip geri döner", f"multiplicity {m} (even) ⇒ touches and turns back",
                "teğet", "touches")
    if m == 1:
        return ("katlılık 1 (tek) ⇒ x-eksenini keser", "multiplicity 1 (odd) ⇒ crosses the x-axis",
                "keser", "crosses")
    return (f"katlılık {m} (tek) ⇒ düzleşerek keser", f"multiplicity {m} (odd) ⇒ crosses, flattening out",
            "keser", "crosses")


def _ends(k, n):
    right = "+∞" if k > 0 else "−∞"
    if n % 2 == 0:
        return right, right
    return ("−∞" if k > 0 else "+∞"), right


def solve(P):
    roots = [int(r) for r in P["roots"]]
    k = int(P.get("k", 1))
    order, cnt = _order(roots)
    seq = [r for r in order for _ in range(cnt[r])]
    coeffs = k * np.poly(seq)
    fact = _fact(k, roots)
    expd = _pstr(coeffs)
    n = len(seq)
    steps = [(f"Çarpanlı form: f(x) = {fact}", f"Factored form: f(x) = {fact}")]
    for j in range(1, n):
        prev = _factor(seq[0], 1) if j == 1 else f"({_pstr(np.poly(seq[:j]))})"
        nxt = _pstr(np.poly(seq[:j + 1]))
        steps.append((f"Çarp: {prev}·{_factor(seq[j], 1)} = {nxt}", f"Multiply: {prev}·{_factor(seq[j], 1)} = {nxt}"))
    if k != 1:
        steps.append((f"{k} ile çarp: f(x) = {expd}", f"Multiply by {k}: f(x) = {expd}"))
    else:
        steps.append((f"Açılmış form: f(x) = {expd}", f"Expanded form: f(x) = {expd}"))
    le, ri = _ends(k, n)
    steps.append((f"Derece {n}, baş katsayı {k}: x → −∞ iken f(x) → {le}, x → +∞ iken f(x) → {ri}",
                  f"Degree {n}, leading coefficient {k}: as x → −∞, f(x) → {le}; as x → +∞, f(x) → {ri}"))
    for r in sorted(cnt):
        kd = _kind(cnt[r])
        steps.append((f"x = {r}: {kd[0]}", f"x = {r}: {kd[1]}"))
    c0 = int(round(float(coeffs[-1])))
    steps.append((f"y-kesişimi: f(0) = {c0}", f"y-intercept: f(0) = {c0}"))
    ztr = ", ".join(f"{r} ({'×' + str(cnt[r]) + ', ' if cnt[r] > 1 else ''}{_kind(cnt[r])[2]})" for r in sorted(cnt))
    zen = ", ".join(f"{r} ({'×' + str(cnt[r]) + ', ' if cnt[r] > 1 else ''}{_kind(cnt[r])[3]})" for r in sorted(cnt))
    return {"answer": (f"f(x) = {expd};  sıfırlar: {ztr}", f"f(x) = {expd};  zeros: {zen}"),
            "steps": steps, "fmt": {"fact": fact, "expanded": expd}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    roots = [int(r) for r in P["roots"]]
    k = int(P.get("k", 1))
    order, cnt = _order(roots)
    dist = sorted(cnt)
    seq = [r for r in order for _ in range(cnt[r])]
    coeffs = k * np.poly(seq)
    n = len(seq)
    fact = _fact(k, roots)
    expd = _pstr(coeffs)
    rmin, rmax = min(roots), max(roots)
    c = (rmin + rmax) / 2
    half = max(2.6, (rmax - rmin) / 2 + 1.3)
    xl, xr = c - half, c + half
    xin = np.linspace(rmin - 0.7, rmax + 0.7, 400)
    yin = np.polyval(coeffs, xin)
    ymin, ymax = min(float(yin.min()), 0.0), max(float(yin.max()), 0.0)
    span = (ymax - ymin) or 1.0
    ylo, yhi = ymin - 0.32 * span, ymax + 0.32 * span
    xs = np.linspace(xl, xr, 700)
    ys = np.polyval(coeffs, xs)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.8, bottom=0.08)
    ax.set_xlim(xl, xr)
    ax.set_ylim(ylo, yhi)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.2)
    if xl < 0 < xr:
        ax.axvline(0, color="#9CA3AF", lw=1)
    ax.set_title(f"f(x) = {fact}", fontsize=13)
    curve, = ax.plot([], [], color="#2563EB", lw=2.6)
    tracer, = ax.plot([], [], "o", color="#2563EB", ms=8)
    rdots = []
    rlabs = []
    rings = []
    for r in dist:
        rdots.append(ax.plot([], [], "o", ms=10, color="#DC2626", zorder=7)[0])
        rings.append(ax.plot([], [], "o", ms=26, mfc="none", mew=2.2, zorder=6)[0])
        near = np.polyval(coeffs, [r - 0.35, r + 0.35])
        above = bool(cnt[r] % 2 == 0 and near.mean() < 0)
        rlabs.append(ax.text(r, (0.06 if above else -0.06) * (yhi - ylo), "", ha="center",
                             va="bottom" if above else "top", fontsize=10.5, fontweight="bold", zorder=8,
                             bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85)))
    c0 = float(np.polyval(coeffs, 0.0))
    show_y = xl < 0 < xr and ylo < c0 < yhi
    ydot, = ax.plot([], [], "s", ms=9, color="#7C3AED", zorder=8)
    ylab = ax.text(0.15 * (xr - xl) / 10, c0, "", color="#7C3AED", fontsize=10.5, va="bottom", zorder=8)
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    le, ri = _ends(k, n)
    nd = len(dist)
    N = 150

    def update(i):
        for j, r in enumerate(dist):
            m = cnt[r]
            kd = _kind(m)
            base = f"x = {r}" + (f" (×{m})" if m > 1 else "")
            if i >= 4 + j * 30 / nd:
                rdots[j].set_data([r], [0])
                if i >= 92 + j * 30 / nd:
                    rlabs[j].set_text(base + "\n" + (kd[2] if tr else kd[3]))
                    rings[j].set_data([r], [0])
                    rings[j].set_color("#7C3AED" if m % 2 == 0 else "#16A34A")
                else:
                    rlabs[j].set_text(base)
                    rings[j].set_data([], [])
            else:
                rdots[j].set_data([], [])
                rlabs[j].set_text("")
                rings[j].set_data([], [])
        p = _cl((i - 40) / 48)
        if p > 0:
            mm = max(2, int(p * len(xs)))
            curve.set_data(xs[:mm], ys[:mm])
            if p < 1:
                tracer.set_data([xs[mm - 1]], [min(max(ys[mm - 1], ylo), yhi)])
            else:
                tracer.set_data([], [])
        else:
            curve.set_data([], [])
            tracer.set_data([], [])
        if i >= 124 and show_y:
            ydot.set_data([0], [c0])
            ylab.set_text(f" f(0) = {int(round(c0))}")
        else:
            ydot.set_data([], [])
            ylab.set_text("")
        if i < 40:
            info.set_text(("1) Sıfırlar: her çarpan (x − r) = 0 ⇒ x = r" if tr else
                           "1) Zeros: each factor (x − r) = 0 ⇒ x = r"))
        elif i < 92:
            info.set_text((f"2) Grafik: derece {n}, baş katsayı {k}" if tr else
                           f"2) Graph: degree {n}, leading coefficient {k}"))
        elif i < 124:
            info.set_text(("3) Tek katlılık: keser · çift katlılık: teğet (değip döner)" if tr else
                           "3) Odd multiplicity: crosses · even multiplicity: touches and turns"))
        else:
            info.set_text((f"f(x) = {expd}\nx → −∞: f → {le},  x → +∞: f → {ri}" if tr else
                           f"f(x) = {expd}\nas x → −∞: f → {le},  as x → +∞: f → {ri}"))
        return []

    return N, update


def vary(P, rnd):
    roots = [int(r) for r in P["roots"]]
    pattern = sorted(Counter(roots).values(), reverse=True)
    pool = list(range(-3, 4)) if len(roots) >= 4 else list(range(-4, 5))
    vals = rnd.sample(pool, len(pattern))
    new = []
    for v, m in zip(vals, pattern):
        new += [v] * m
    return {"roots": sorted(new), "k": rnd.choice([1, -1, 2, -2]) if len(roots) <= 3 else rnd.choice([1, -1])}
''',
}
EXAMPLES += [
    {"id": "alg-polyroots-1", "kind": "polynomial_roots",
     "title": ("Çift katlı kök: teğet geçen grafik", "Double root: the graph touches"),
     "q": ("f(x) = {fact} polinomunu açarak yaz, sıfırlarını katlılıklarıyla belirle ve grafiğini çiz.",
           "Expand f(x) = {fact}, list its zeros with multiplicities and sketch the graph."),
     "P": {"roots": [-1, 2, 2], "k": 2}},
    {"id": "alg-polyroots-2", "kind": "polynomial_roots",
     "title": ("Dördüncü derece polinom", "A quartic polynomial"),
     "q": ("Sıfırları {roots} ve baş katsayısı {k} olan dördüncü derece polinomu yaz ({fact}); uç davranışını açıkla.",
           "Write the quartic with zeros {roots} and leading coefficient {k} ({fact}); describe its end behaviour."),
     "P": {"roots": [-3, -1, 0, 2], "k": -1}},
    {"id": "alg-polyroots-3", "kind": "polynomial_roots",
     "title": ("Üç katlı kök", "A triple root"),
     "q": ("f(x) = {fact} için üç katlı kök, grafiğin x-eksenini kesme biçimini nasıl etkiler? Açılmış biçimi de bul.",
           "For f(x) = {fact}, how does the triple zero shape the way the graph crosses the x-axis? Also find the expanded form."),
     "P": {"roots": [-2, 1, 1, 1], "k": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["rational_function"] = {
    "course": "alg",
    "title": ("Rasyonel fonksiyon ve asimptotlar", "Rational function and its asymptotes"),
    "topics": ["rational function", "rational functions", "asymptote", "asymptotes", "vertical asymptote",
               "horizontal asymptote", "graphing rational functions", "domain of a rational function",
               "rasyonel fonksiyon", "rasyonel fonksiyonlar", "asimptot", "düşey asimptot", "yatay asimptot"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction


def _F(v):
    return Fraction(v).limit_denominator(1000)


def _f(v):
    v = _F(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _cl(t):
    return min(1.0, max(0.0, t))


def _lin(a, b):
    a, b = _F(a), _F(b)
    if a == 0:
        return _f(b), False
    ax = ("" if a == 1 else ("-" if a == -1 else _f(a))) + "x"
    if b == 0:
        return ax, False
    return f"{ax} {'+' if b > 0 else '-'} {_f(abs(b))}", True


def _expr(a, b, c, d):
    n, n2 = _lin(a, b)
    m, m2 = _lin(c, d)
    return (f"({n})" if n2 else n) + "/" + (f"({m})" if m2 else m)


def _data(P):
    a, b, c, d = (_F(P[k]) for k in ("a", "b", "c", "d"))
    va = -d / c
    ha = a / c
    K = (b * c - a * d) / (c * c)
    xi = None if a == 0 else -b / a
    yi = None if d == 0 else b / d
    return a, b, c, d, va, ha, K, xi, yi


def solve(P):
    a, b, c, d, va, ha, K, xi, yi = _data(P)
    fx = _expr(a, b, c, d)
    num = _lin(a, b)[0]
    den = _lin(c, d)[0]
    steps = [(f"f(x) = {fx}  (sadeleşmez: ad − bc = {_f(a * d - b * c)} ≠ 0)",
              f"f(x) = {fx}  (does not simplify: ad − bc = {_f(a * d - b * c)} ≠ 0)")]
    dz = f"{den} = 0" if den == "x" else f"{den} = 0 ⇒ x = {_f(va)}"
    steps.append((f"Payda sıfır olamaz: {dz};  tanım kümesi x ≠ {_f(va)}",
                  f"The denominator cannot be 0: {dz};  domain x ≠ {_f(va)}"))
    steps.append((f"x = {_f(va)} için pay {_f(a * va + b)} ≠ 0 ⇒ düşey asimptot x = {_f(va)}",
                  f"At x = {_f(va)} the numerator is {_f(a * va + b)} ≠ 0 ⇒ vertical asymptote x = {_f(va)}"))
    if a == 0:
        steps.append(("Payın derecesi paydanınkinden küçük ⇒ yatay asimptot y = 0",
                      "Degree of numerator < degree of denominator ⇒ horizontal asymptote y = 0"))
    else:
        ac = f"{_f(a)}/{_f(c)}"
        ac = ac if ac == _f(ha) else f"{ac} = {_f(ha)}"
        steps.append((f"Pay ve payda aynı dereceli ⇒ yatay asimptot y = a/c = {ac}",
                      f"Equal degrees ⇒ horizontal asymptote y = a/c = {ac}"))
    if xi is not None:
        steps.append((f"x-kesişimi: pay = 0 ⇒ {num} = 0 ⇒ x = {_f(xi)}",
                      f"x-intercept: numerator = 0 ⇒ {num} = 0 ⇒ x = {_f(xi)}"))
    else:
        steps.append(("Pay hiç sıfır olmaz ⇒ x-kesişimi yok", "The numerator is never 0 ⇒ no x-intercept"))
    if yi is not None:
        bd = f"{_f(b)}/{_f(d) if d > 0 else '(' + _f(d) + ')'}"
        bd = bd if bd == _f(yi) else f"{bd} = {_f(yi)}"
        steps.append((f"y-kesişimi: f(0) = {bd}", f"y-intercept: f(0) = {bd}"))
    else:
        steps.append(("x = 0 tanımsız ⇒ y-kesişimi yok", "x = 0 is excluded ⇒ no y-intercept"))
    rp, rm = ("+∞", "−∞") if K > 0 else ("−∞", "+∞")
    ks = _f(K) if (K > 0 and K.denominator == 1) else f"({_f(K)})"
    sf = f"{_f(ha)} + {ks}/({_lin(1, -va)[0]})" if ha != 0 else f"{ks}/({_lin(1, -va)[0]})"
    steps.append((f"f(x) = {sf}:  x → {_f(va)}⁺ iken f → {rp},  x → {_f(va)}⁻ iken f → {rm}",
                  f"f(x) = {sf}:  as x → {_f(va)}⁺, f → {rp};  as x → {_f(va)}⁻, f → {rm}"))
    steps.append((f"x → ±∞ iken f(x) → {_f(ha)};  görüntü kümesi y ≠ {_f(ha)}",
                  f"As x → ±∞, f(x) → {_f(ha)};  range y ≠ {_f(ha)}"))
    t_tr = f"Düşey asimptot x = {_f(va)}, yatay asimptot y = {_f(ha)}"
    t_en = f"Vertical asymptote x = {_f(va)}, horizontal asymptote y = {_f(ha)}"
    if xi is not None:
        t_tr += f"; x-kesişimi {_f(xi)}"
        t_en += f"; x-intercept {_f(xi)}"
    if yi is not None:
        t_tr += f"; y-kesişimi {_f(yi)}"
        t_en += f"; y-intercept {_f(yi)}"
    return {"answer": (t_tr, t_en), "steps": steps, "fmt": {"fx": fx}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, c, d, va, ha, K, xi, yi = _data(P)
    vaf, haf, Kf = float(va), float(ha), float(K)
    W = max(5.0, 2.6 * math.sqrt(abs(Kf)))
    xl, xr = vaf - W, vaf + W
    yl, yr = haf - W * 0.85, haf + W * 0.85
    if xi is not None:
        xl, xr = min(xl, float(xi) - 1.0), max(xr, float(xi) + 1.0)
        yl, yr = min(yl, -1.0), max(yr, 1.0)
    if yi is not None:
        xl, xr = min(xl, -1.0), max(xr, 1.0)
        yl, yr = min(yl, float(yi) - 1.0), max(yr, float(yi) + 1.0)
    yspan = yr - yl
    eps = max(abs(Kf) / (2.5 * yspan), 1e-4)
    s = np.linspace(0, 1, 500)
    xL = vaf - np.maximum((vaf - xl) * (1 - s) ** 2, eps)
    xR = vaf + np.maximum((xr - vaf) * (1 - s) ** 2, eps)
    yL = np.clip(haf + Kf / (xL - vaf), yl - yspan, yr + yspan)
    yR = np.clip(haf + Kf / (xR - vaf), yl - yspan, yr + yspan)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.82, bottom=0.08)
    ax.set_xlim(xl, xr)
    ax.set_ylim(yl, yr)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.1)
    if xl < 0 < xr:
        ax.axvline(0, color="#374151", lw=1.1)
    fx = _expr(a, b, c, d)
    ax.set_title(f"f(x) = {fx}", fontsize=13)
    vline, = ax.plot([], [], "--", color="#DC2626", lw=1.8)
    hline, = ax.plot([], [], "--", color="#7C3AED", lw=1.8)
    vlab = ax.text(vaf + (-0.015 if Kf > 0 else 0.015) * (xr - xl), yr - 0.05 * yspan, "", color="#DC2626",
                   fontsize=11, fontweight="bold", ha="right" if Kf > 0 else "left", va="top")
    hlab = ax.text(xl + 0.01 * (xr - xl), haf + (0.02 if Kf > 0 else -0.02) * yspan, "", color="#7C3AED",
                   fontsize=11, fontweight="bold", va="bottom" if Kf > 0 else "top")
    ipts = []
    if xi is not None:
        ipts.append((float(xi), 0.0, f"({_f(xi)}, 0)"))
    if yi is not None:
        ipts.append((0.0, float(yi), f"(0, {_f(yi)})"))
    idots, = ax.plot([], [], "o", ms=9, color="#E07B39", zorder=7)
    ilabs = [ax.text(px + (0.0 if py == 0 else 0.012 * (xr - xl)), py + (0.03 if py == 0 else -0.03) * yspan, "",
                     color="#E07B39", fontsize=10.5, fontweight="bold", zorder=8,
                     ha="center" if py == 0 else "left", va="bottom" if py == 0 else "top",
                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8)) for px, py, _ in ipts]
    left, = ax.plot([], [], color="#2563EB", lw=2.6)
    right, = ax.plot([], [], color="#2563EB", lw=2.6)
    tracer, = ax.plot([], [], "o", color="#16A34A", ms=9, zorder=9)
    corner_y = 0.03 if Kf > 0 else 0.97
    coord = ax.text(0.98, corner_y, "", transform=ax.transAxes, ha="right",
                    va="bottom" if Kf > 0 else "top", fontsize=11, zorder=10,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    rp, rm = ("+∞", "−∞") if Kf > 0 else ("−∞", "+∞")
    top_side = 1 if Kf > 0 else -1
    wb = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85)
    b_top = ax.text(vaf + top_side * 0.02 * (xr - xl), yr - 0.16 * yspan, "", color="#16A34A", fontsize=10.5,
                    ha="left" if top_side > 0 else "right", va="top", bbox=wb, zorder=9)
    b_bot = ax.text(vaf - top_side * 0.02 * (xr - xl), yl + 0.04 * yspan, "", color="#16A34A", fontsize=10.5,
                    ha="right" if top_side > 0 else "left", va="bottom", bbox=wb, zorder=9)
    b_inf = ax.text(xr - 0.01 * (xr - xl), haf + (-0.03 if Kf > 0 else 0.03) * yspan, "", color="#7C3AED",
                    fontsize=10.5, ha="right", va="top" if Kf > 0 else "bottom")
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    VA, HA = _f(va), _f(ha)
    N = 160

    def update(i):
        p = _cl(i / 18)
        if p > 0:
            vline.set_data([vaf, vaf], [yl, yl + yspan * p])
        else:
            vline.set_data([], [])
        q = _cl((i - 10) / 18)
        if q > 0:
            hline.set_data([xl, xl + (xr - xl) * q], [haf, haf])
        else:
            hline.set_data([], [])
        vlab.set_text(f"x = {VA}" if i >= 18 else "")
        hlab.set_text(f"y = {HA}" if i >= 28 else "")
        if i >= 32 and ipts:
            idots.set_data([t[0] for t in ipts], [t[1] for t in ipts])
            for lab, t in zip(ilabs, ipts):
                lab.set_text(t[2])
        else:
            idots.set_data([], [])
            for lab in ilabs:
                lab.set_text("")
        a1 = _cl((i - 48) / 44)
        a2 = _cl((i - 96) / 44)
        if a1 > 0:
            m = max(2, int(a1 * len(xL)))
            left.set_data(xL[:m], yL[:m])
        else:
            left.set_data([], [])
        if a2 > 0:
            m2 = max(2, int(a2 * len(xR)))
            right.set_data(xR[:m2], yR[:m2])
        else:
            right.set_data([], [])
        tx = None
        if 0 < a1 < 1:
            tx, ty = xL[max(1, int(a1 * len(xL))) - 1], yL[max(1, int(a1 * len(xL))) - 1]
        elif 0 < a2 < 1:
            tx, ty = xR[max(1, int(a2 * len(xR))) - 1], yR[max(1, int(a2 * len(xR))) - 1]
        if tx is not None:
            fv = haf + Kf / (tx - vaf)
            tracer.set_data([tx], [min(max(ty, yl), yr)])
            coord.set_text(f"x = {tx:.3f}\nf(x) = {fv:.2f}")
            coord.set_visible(True)
        else:
            tracer.set_data([], [])
            coord.set_text("")
            coord.set_visible(False)
        fin = i >= 142
        b_top.set_text((f"x → {VA}{'⁺' if top_side > 0 else '⁻'}: f → +∞") if fin else "")
        b_bot.set_text((f"x → {VA}{'⁻' if top_side > 0 else '⁺'}: f → −∞") if fin else "")
        b_inf.set_text((f"x → ±∞: f → {HA}") if fin else "")
        if i < 30:
            info.set_text((f"1) Asimptotlar: payda = 0 ⇒ x = {VA};  a/c ⇒ y = {HA}") if tr else
                          (f"1) Asymptotes: denominator = 0 ⇒ x = {VA};  a/c ⇒ y = {HA}"))
        elif i < 48:
            info.set_text("2) Eksenleri kestiği noktalar" if tr else "2) Intercepts")
        elif i < 96:
            info.set_text((f"3) Sol kol: x → {VA}⁻ iken f → {rm}") if tr else (f"3) Left branch: as x → {VA}⁻, f → {rm}"))
        elif i < 142:
            info.set_text((f"4) Sağ kol: x → {VA}⁺ iken f → {rp};  uzakta f → {HA}") if tr else
                          (f"4) Right branch: as x → {VA}⁺, f → {rp};  far away f → {HA}"))
        else:
            info.set_text((f"Düşey asimptot x = {VA}, yatay asimptot y = {HA}\n"
                           f"tanım: x ≠ {VA},  görüntü: y ≠ {HA}") if tr else
                          (f"Vertical asymptote x = {VA}, horizontal asymptote y = {HA}\n"
                           f"domain: x ≠ {VA},  range: y ≠ {HA}"))
        return []

    return N, update


def vary(P, rnd):
    if P.get("d", 1) == 0 and P.get("a", 0) > 0 and P.get("b", 0) > 0:
        return {"a": rnd.randint(2, 9), "b": rnd.choice([50, 100, 120, 150, 200, 300, 500]), "c": 1, "d": 0}
    h = rnd.randint(-4, 4)
    q = rnd.randint(-3, 3)
    k = rnd.choice([-6, -4, -3, -2, -1, 1, 2, 3, 4, 6])
    c = rnd.choice([1, 1, 2])
    return {"a": q * c, "b": c * (k - q * h), "c": c, "d": -c * h}
''',
}
EXAMPLES += [
    {"id": "alg-rational-1", "kind": "rational_function",
     "title": ("Asimptotları bulma", "Finding the asymptotes"),
     "q": ("f(x) = {fx} fonksiyonunun düşey ve yatay asimptotlarını, eksen kesişimlerini bul ve grafiğini çiz.",
           "Find the vertical and horizontal asymptotes and the intercepts of f(x) = {fx}, then sketch it."),
     "P": {"a": 2, "b": 1, "c": 1, "d": -3}},
    {"id": "alg-rational-2", "kind": "rational_function",
     "title": ("Kesirli yatay asimptot", "A fractional horizontal asymptote"),
     "q": ("f(x) = {fx} için tanım ve görüntü kümesini, asimptotları ve kesişim noktalarını belirle.",
           "For f(x) = {fx}, determine the domain, range, asymptotes and intercepts."),
     "P": {"a": 1, "b": -4, "c": 2, "d": 2}},
    {"id": "alg-rational-3", "kind": "rational_function", "topics": ["average cost", "ortalama maliyet", "word problem"],
     "title": ("Sözel problem: ortalama maliyet", "Word problem: average cost"),
     "q": ("Bir atölyenin sabit gideri {b} TL, ürün başına maliyeti {a} TL. x ürün için ortalama maliyet "
           "C(x) = {fx}. Asimptotları bul; çok sayıda ürün üretilince ortalama maliyet neye yaklaşır?",
           "A workshop has fixed costs of {b} and a cost of {a} per item. The average cost of x items is "
           "C(x) = {fx}. Find the asymptotes; what does the average cost approach for large production runs?"),
     "P": {"a": 5, "b": 200, "c": 1, "d": 0}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["complex_multiply"] = {
    "course": "alg",
    "title": ("Karmaşık sayılarla çarpma", "Multiplying complex numbers"),
    "topics": ["complex numbers", "complex number", "imaginary numbers", "multiplying complex numbers",
               "complex plane", "polar form", "modulus and argument", "argand diagram",
               "karmaşık sayılar", "karmaşık sayı", "sanal sayı", "karmaşık düzlem", "kutupsal biçim"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import FancyArrowPatch


def _cl(t):
    return min(1.0, max(0.0, t))


def _n(v):
    v = float(v)
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:g}"


def _p(v):
    return f"({_n(v)})" if float(v) < 0 else _n(v)


def _cx(re, im):
    re, im = float(re), float(im)
    if im == 0:
        return _n(re)
    ims = ("" if abs(im) == 1 else _n(abs(im))) + "i"
    if re == 0:
        return ("-" if im < 0 else "") + ims
    return f"{_n(re)} {'+' if im > 0 else '-'} {ims}"


def _terms(items):
    out = ""
    for coef, unit in items:
        if coef == 0:
            continue
        mag = abs(coef)
        body = ("" if (mag == 1 and unit) else _n(mag)) + unit
        if out == "":
            out = ("-" if coef < 0 else "") + body
        else:
            out += (" - " if coef < 0 else " + ") + body
    return out or "0"


def _rt(s):
    s = float(s)
    if abs(s - round(s)) < 1e-9:
        r = math.isqrt(int(round(s)))
        if r * r == int(round(s)):
            return str(r)
        return f"√{int(round(s))}"
    return f"{math.sqrt(s):.4g}"


def _data(P):
    a, b, c, d = (float(P[k]) for k in ("a", "b", "c", "d"))
    re, im = a * c - b * d, a * d + b * c
    r1, r2 = math.hypot(a, b), math.hypot(c, d)
    t1, t2 = math.degrees(math.atan2(b, a)), math.degrees(math.atan2(d, c))
    return a, b, c, d, re, im, r1, r2, t1, t2


def solve(P):
    a, b, c, d, re, im, r1, r2, t1, t2 = _data(P)
    z1, z2, w = _cx(a, b), _cx(c, d), _cx(re, im)
    dist = _terms([(a * c, ""), (a * d, "i"), (b * c, "i"), (b * d, "i²")])
    steps = [
        (f"z₁·z₂ = ({z1})({z2})", f"z₁·z₂ = ({z1})({z2})"),
        (f"Dağıt (her terimi her terimle çarp): = {dist}", f"Distribute (FOIL): = {dist}"),
        (f"i² = −1 kullan: = ({_n(a * c)} − {_p(b * d)}) + ({_n(a * d)} + {_p(b * c)})i = {w}",
         f"Use i² = −1: = ({_n(a * c)} − {_p(b * d)}) + ({_n(a * d)} + {_p(b * c)})i = {w}"),
    ]
    if r1 > 0 and r2 > 0:
        s1, s2 = a * a + b * b, c * c + d * d
        tw = t1 + t2
        tn = tw - 360 if tw > 180 else (tw + 360 if tw <= -180 else tw)
        wrap = "" if abs(tn - tw) < 1e-9 else f" ≡ {tn:.2f}°"
        t2s = f"{t2:.2f}°" if t2 >= 0 else f"({t2:.2f}°)"
        steps += [
            (f"Kutupsal: |z₁| = √({_p(a)}² + {_p(b)}²) = {_rt(s1)} ≈ {r1:.4f},  arg z₁ ≈ {t1:.2f}°",
             f"Polar: |z₁| = √({_p(a)}² + {_p(b)}²) = {_rt(s1)} ≈ {r1:.4f},  arg z₁ ≈ {t1:.2f}°"),
            (f"|z₂| = √({_p(c)}² + {_p(d)}²) = {_rt(s2)} ≈ {r2:.4f},  arg z₂ ≈ {t2:.2f}°",
             f"|z₂| = √({_p(c)}² + {_p(d)}²) = {_rt(s2)} ≈ {r2:.4f},  arg z₂ ≈ {t2:.2f}°"),
            (f"Modüller çarpılır: |z₁z₂| = |z₁|·|z₂| = {_rt(s1 * s2)} ≈ {r1 * r2:.4f}",
             f"Moduli multiply: |z₁z₂| = |z₁|·|z₂| = {_rt(s1 * s2)} ≈ {r1 * r2:.4f}"),
            (f"Argümanlar toplanır: arg(z₁z₂) = {t1:.2f}° + {t2s} = {tw:.2f}°{wrap}",
             f"Arguments add: arg(z₁z₂) = {t1:.2f}° + {t2s} = {tw:.2f}°{wrap}"),
            (f"Kontrol: |{w}| = √({_p(re)}² + {_p(im)}²) ≈ {math.hypot(re, im):.4f},  açı ≈ {math.degrees(math.atan2(im, re)):.2f}° ✓",
             f"Check: |{w}| = √({_p(re)}² + {_p(im)}²) ≈ {math.hypot(re, im):.4f},  angle ≈ {math.degrees(math.atan2(im, re)):.2f}° ✓"),
        ]
    return {"answer": f"z₁·z₂ = {w}", "steps": steps, "fmt": {"z1": z1, "z2": z2}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, c, d, re, im, r1, r2, t1, t2 = _data(P)
    z1, z2, w = _cx(a, b), _cx(c, d), _cx(re, im)
    rw = r1 * r2
    th1, th2 = math.radians(t1), math.radians(t2)
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.3], left=0.02, right=0.98, top=0.86, bottom=0.07, wspace=0.05)
    tx = fig.add_subplot(gs[0, 0])
    tx.axis("off")
    tx.set_xlim(0, 1)
    tx.set_ylim(0, 1)
    ax = fig.add_subplot(gs[0, 1])
    R = max(2.5, max(r1, r2, rw) * 1.32)
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.1)
    ax.axvline(0, color="#374151", lw=1.1)
    ax.text(R * 0.97, R * 0.02, "Re", ha="right", va="bottom", fontsize=10, color="#374151")
    ax.text(R * 0.02, R * 0.97, "Im", ha="left", va="top", fontsize=10, color="#374151")

    def arrow(col, lw=2.4):
        ar = FancyArrowPatch((0, 0), (1, 0), arrowstyle="-|>", mutation_scale=18, color=col, lw=lw, zorder=6)
        ax.add_patch(ar)
        ar.set_visible(False)
        return ar

    A1, A2, AM, AW = arrow("#2563EB"), arrow("#E07B39"), arrow("#7C3AED", 2.0), arrow("#16A34A", 3.0)
    arc1, = ax.plot([], [], color="#2563EB", lw=1.6)
    arc2, = ax.plot([], [], color="#E07B39", lw=1.6)
    arcr, = ax.plot([], [], color="#7C3AED", lw=1.6)
    trace, = ax.plot([], [], ":", color="#7C3AED", lw=1.8)
    l1 = ax.text(0, 0, "", color="#2563EB", fontsize=11, fontweight="bold", ha="center", va="center")
    l2 = ax.text(0, 0, "", color="#E07B39", fontsize=11, fontweight="bold", ha="center", va="center")
    lw_ = ax.text(0, 0, "", color="#16A34A", fontsize=12, fontweight="bold", ha="center", va="center",
                  bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    dist = _terms([(a * c, ""), (a * d, "i"), (b * c, "i"), (b * d, "i²")])
    tw = t1 + t2
    rows = [
        (("Cebirsel çarpım" if tr else "Algebraic product"), 12, "#6B7280"),
        (f"({z1})({z2})", 14, "#111827"),
        (f"= {dist}", 14, "#111827"),
        (f"= {w}", 15, "#16A34A"),
        (("Kutupsal bakış" if tr else "Polar view"), 12, "#6B7280"),
        (f"|z₁| = {r1:.3f},  θ₁ = {t1:.1f}°", 11.5, "#2563EB"),
        (f"|z₂| = {r2:.3f},  θ₂ = {t2:.1f}°", 11.5, "#E07B39"),
        (f"|z₁z₂| = {r1:.3f}·{r2:.3f} = {rw:.3f}", 11.5, "#7C3AED"),
        (f"θ = {t1:.1f}° + {t2:.1f}° = {tw:.1f}°".replace("+ -", "− "), 11.5, "#7C3AED"),
    ]
    times = [0, 4, 14, 26, 36, 36, 44, 70, 104]
    ys_ = [0.95, 0.86, 0.77, 0.67, 0.52, 0.43, 0.35, 0.26, 0.17]
    txts = [tx.text(0.03, ys_[j], rows[j][0], fontsize=rows[j][1], color=rows[j][2], va="center",
                    family="DejaVu Sans Mono" if j in (1, 2, 3) else None, alpha=0) for j in range(len(rows))]
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))

    def setarrow(ar, x, y):
        if math.hypot(x, y) < 0.03 * R:
            ar.set_visible(False)
        else:
            ar.set_positions((0, 0), (x, y))
            ar.set_visible(True)

    def place(t, x, y, s):
        rr = math.hypot(x, y)
        k = 1 + 0.05 * R / rr if rr > 1e-9 else 1
        t.set_position((x * k, y * k + (0.03 * R if y >= 0 else -0.03 * R)))
        t.set_ha("right" if x > 0.3 * R else ("left" if x < -0.3 * R else "center"))
        t.set_va("bottom" if y >= 0 else "top")
        t.set_text(s)

    def arc(line, rad, ta, tb):
        angs = np.linspace(ta, tb, 40)
        line.set_data(rad * np.cos(angs), rad * np.sin(angs))

    N = 160

    def update(i):
        for j, t in enumerate(txts):
            t.set_alpha(_cl((i - times[j]) / 8))
        p1 = _cl(i / 18)
        setarrow(A1, a * p1, b * p1)
        if p1 >= 1:
            place(l1, a, b, f"z₁ = {z1}")
            arc(arc1, 0.16 * R, 0, th1)
        else:
            l1.set_text("")
            arc1.set_data([], [])
        p2 = _cl((i - 20) / 18)
        if p2 > 0:
            setarrow(A2, c * p2, d * p2)
        else:
            A2.set_visible(False)
        if p2 >= 1:
            place(l2, c, d, f"z₂ = {z2}")
            arc(arc2, 0.24 * R, 0, th2)
        else:
            l2.set_text("")
            arc2.set_data([], [])
        s = _cl((i - 55) / 30)
        rot = _cl((i - 90) / 35)
        if 55 <= i < 126:
            ln = r1 * (1 + (r2 - 1) * s)
            ang = th1 + th2 * rot
            setarrow(AM, ln * math.cos(ang), ln * math.sin(ang))
        else:
            AM.set_visible(False)
        if 90 <= i and rot > 0:
            arc(arcr, 0.32 * R, th1, th1 + th2 * rot)
            arc(trace, rw, th1, th1 + th2 * rot)
        else:
            arcr.set_data([], [])
            trace.set_data([], [])
        if i >= 126:
            setarrow(AW, re, im)
            place(lw_, re, im, f"z₁z₂ = {w}")
        else:
            AW.set_visible(False)
            lw_.set_text("")
        if i < 40:
            info.set_text((f"1) z₁ = {z1} ve z₂ = {z2} vektör olarak") if tr else
                          (f"1) z₁ = {z1} and z₂ = {z2} as vectors"))
        elif i < 55:
            info.set_text("2) Cebirsel çarpım: dağıt ve i² = −1 kullan" if tr else
                          "2) Algebra: distribute and use i² = −1")
        elif i < 90:
            if abs(r2 - 1) < 1e-9:
                info.set_text("3) |z₂| = 1: uzunluk değişmez" if tr else "3) |z₂| = 1: the length stays the same")
            else:
                info.set_text((f"3) z₁'i |z₂| = {r2:.3f} katına uzat: {r1:.3f} → {rw:.3f}") if tr else
                              (f"3) Scale z₁ by |z₂| = {r2:.3f}: {r1:.3f} → {rw:.3f}"))
        elif i < 126:
            info.set_text((f"4) arg z₂ = {t2:.1f}° kadar döndür: {t1:.1f}° → {tw:.1f}°") if tr else
                          (f"4) Rotate by arg z₂ = {t2:.1f}°: {t1:.1f}° → {tw:.1f}°"))
        else:
            info.set_text((f"Sonuç: z₁·z₂ = {w}  (modüller çarpılır, açılar toplanır)") if tr else
                          (f"Result: z₁·z₂ = {w}  (moduli multiply, angles add)"))
        return []

    return N, update


def vary(P, rnd):
    while True:
        a, b, c, d = (rnd.randint(-4, 4) for _ in range(4))
        if b != 0 and d != 0 and (a, b) != (0, 0) and (c, d) != (0, 0) and abs(a * c - b * d) + abs(a * d + b * c) > 0:
            if math.hypot(a, b) * math.hypot(c, d) <= 22:
                return {"a": a, "b": b, "c": c, "d": d}
''',
}
EXAMPLES += [
    {"id": "alg-complex-1", "kind": "complex_multiply",
     "title": ("İki karmaşık sayının çarpımı", "Product of two complex numbers"),
     "q": ("z₁ = {z1} ve z₂ = {z2} için z₁·z₂ çarpımını hesapla; sonucu karmaşık düzlemde yorumla.",
           "For z₁ = {z1} and z₂ = {z2}, compute z₁·z₂ and interpret it in the complex plane."),
     "P": {"a": 2, "b": 1, "c": 1, "d": 3}},
    {"id": "alg-complex-2", "kind": "complex_multiply",
     "title": ("Modül ve argüman", "Modulus and argument"),
     "q": ("({z1})({z2}) çarpımını bul ve |z₁z₂| = |z₁|·|z₂| olduğunu doğrula.",
           "Find ({z1})({z2}) and verify that |z₁z₂| = |z₁|·|z₂|."),
     "P": {"a": 3, "b": 4, "c": 1, "d": -2}},
    {"id": "alg-complex-3", "kind": "complex_multiply", "topics": ["rotation", "döndürme"],
     "title": ("i ile çarpmak = 90° döndürmek", "Multiplying by i is a 90° rotation"),
     "q": ("z = {z1} sayısını {z2} ile çarp. Çarpım z'yi düzlemde nasıl hareket ettirir?",
           "Multiply z = {z1} by {z2}. How does the product move z in the plane?"),
     "P": {"a": 4, "b": 2, "c": 0, "d": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["sequence"] = {
    "course": "alg",
    "title": ("Aritmetik ve geometrik diziler", "Arithmetic and geometric sequences"),
    "topics": ["sequence", "sequences", "arithmetic sequence", "geometric sequence", "arithmetic series",
               "geometric series", "nth term", "partial sum", "common difference", "common ratio",
               "dizi", "diziler", "aritmetik dizi", "geometrik dizi", "genel terim", "kısmi toplam"],
    "code": r'''
import numpy as np
from fractions import Fraction

_SUBD = "₀₁₂₃₄₅₆₇₈₉"
_SUPD = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def _F(v):
    return Fraction(v).limit_denominator(1000)


def _f(v):
    v = _F(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _p(v):
    v = _F(v)
    return _f(v) if (v >= 0 and v.denominator == 1) else f"({_f(v)})"


def _cl(t):
    return min(1.0, max(0.0, t))


def _sub(n):
    return "".join(_SUBD[int(ch)] for ch in str(int(n)))


def _sup(n):
    return "".join(_SUPD[int(ch)] for ch in str(int(n)))


def _data(P):
    geo = P.get("type", "arithmetic") == "geometric"
    a1, q, n = _F(P["a1"]), _F(P["d_or_r"]), int(P["n"])
    if geo:
        terms = [a1 * q ** k for k in range(n)]
    else:
        terms = [a1 + k * q for k in range(n)]
    sums = []
    acc = Fraction(0)
    for t in terms:
        acc += t
        sums.append(acc)
    return geo, a1, q, n, terms, sums


def solve(P):
    geo, a1, q, n, terms, sums = _data(P)
    an, Sn = terms[-1], sums[-1]
    A, S = f"a{_sub(n)}", f"S{_sub(n)}"
    first = ", ".join(_f(t) for t in terms[:4]) + ", ..."
    steps = [(f"İlk terimler: {first}", f"First terms: {first}")]
    if geo:
        steps.append((f"Ortak oran: r = a₂ / a₁ = {_f(terms[1])} / {_p(a1)} = {_f(q)}",
                      f"Common ratio: r = a₂ / a₁ = {_f(terms[1])} / {_p(a1)} = {_f(q)}"))
        steps.append((f"Genel terim: aₙ = a₁·rⁿ⁻¹  ⇒  {A} = {_p(a1)}·{_p(q)}{_sup(n - 1)} = {_p(a1)}·{_p(q ** (n - 1))} = {_f(an)}",
                      f"General term: aₙ = a₁·rⁿ⁻¹  ⇒  {A} = {_p(a1)}·{_p(q)}{_sup(n - 1)} = {_p(a1)}·{_p(q ** (n - 1))} = {_f(an)}"))
        if q != 1:
            steps.append((f"Toplam: Sₙ = a₁(1 − rⁿ)/(1 − r)  ⇒  {S} = {_p(a1)}·(1 − {_p(q)}{_sup(n)})/(1 − {_p(q)}) "
                           f"= {_p(a1)}·({_f(1 - q ** n)})/({_f(1 - q)}) = {_f(Sn)}",
                           f"Sum: Sₙ = a₁(1 − rⁿ)/(1 − r)  ⇒  {S} = {_p(a1)}·(1 − {_p(q)}{_sup(n)})/(1 − {_p(q)}) "
                           f"= {_p(a1)}·({_f(1 - q ** n)})/({_f(1 - q)}) = {_f(Sn)}"))
        else:
            steps.append((f"r = 1 ⇒ {S} = n·a₁ = {n}·{_p(a1)} = {_f(Sn)}", f"r = 1 ⇒ {S} = n·a₁ = {n}·{_p(a1)} = {_f(Sn)}"))
    else:
        steps.append((f"Ortak fark: d = a₂ − a₁ = {_f(terms[1])} − {_p(a1)} = {_f(q)}",
                      f"Common difference: d = a₂ − a₁ = {_f(terms[1])} − {_p(a1)} = {_f(q)}"))
        steps.append((f"Genel terim: aₙ = a₁ + (n − 1)d  ⇒  {A} = {_f(a1)} + {n - 1}·{_p(q)} = {_f(an)}",
                      f"General term: aₙ = a₁ + (n − 1)d  ⇒  {A} = {_f(a1)} + {n - 1}·{_p(q)} = {_f(an)}"))
        steps.append((f"Toplam: Sₙ = n(a₁ + aₙ)/2  ⇒  {S} = {n}·({_f(a1)} + {_p(an)})/2 = {_f(Sn)}",
                       f"Sum: Sₙ = n(a₁ + aₙ)/2  ⇒  {S} = {n}·({_f(a1)} + {_p(an)})/2 = {_f(Sn)}"))
    if n <= 8:
        chk = " + ".join(_p(t) for t in terms)
    else:
        chk = " + ".join(_p(t) for t in terms[:3]) + " + … + " + _p(an)
    steps.append((f"Kontrol: {chk} = {_f(Sn)} ✓", f"Check: {chk} = {_f(Sn)} ✓"))
    return {"answer": f"{A} = {_f(an)},  {S} = {_f(Sn)}", "steps": steps,
            "fmt": {"first": first, "an": A, "Sn": S}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    geo, a1, q, n, terms, sums = _data(P)
    tv = np.array([float(t) for t in terms])
    sv = np.array([float(s) for s in sums])
    ks = np.arange(1, n + 1)
    A, S = f"a{_sub(n)}", f"S{_sub(n)}"
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1], left=0.07, right=0.98, top=0.8, bottom=0.1, wspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[0, 1])

    def lims(v):
        lo, hi = min(0.0, float(v.min())), max(0.0, float(v.max()))
        pad = (hi - lo) * 0.16 or 1.0
        return lo - (pad if lo < 0 else 0.02 * pad), hi + pad

    ax.set_xlim(0.3, n + 0.7)
    ax.set_ylim(*lims(tv))
    bx.set_xlim(0.3, n + 0.7)
    bx.set_ylim(*lims(sv))
    for a_ in (ax, bx):
        a_.grid(alpha=0.3, axis="y")
        a_.axhline(0, color="#374151", lw=1)
        a_.set_xlabel("n")
    step_x = 1 if n <= 12 else 2
    ax.set_xticks(range(1, n + 1, step_x))
    bx.set_xticks(range(1, n + 1, step_x))
    ax.set_title(("Terimler aₙ" if tr else "Terms aₙ"), fontsize=11)
    bx.set_title(("Kısmi toplamlar Sₙ" if tr else "Partial sums Sₙ"), fontsize=11)
    tb = ax.bar(ks, np.zeros(n), width=0.62, color="#2563EB", alpha=0.45, edgecolor="#2563EB")
    sb = bx.bar(ks, np.zeros(n), width=0.62, color="#16A34A", alpha=0.45, edgecolor="#16A34A")
    dots, = ax.plot([], [], "o", color="#2563EB", ms=6, zorder=5)
    span_t = ax.get_ylim()[1] - ax.get_ylim()[0]
    span_s = bx.get_ylim()[1] - bx.get_ylim()[0]
    show_all = n <= 10
    vlabs = [ax.text(k, tv[k - 1] + (0.015 if tv[k - 1] >= 0 else -0.015) * span_t, "", ha="center",
                     va="bottom" if tv[k - 1] >= 0 else "top", fontsize=9 if n <= 8 else 8, color="#1F2937")
             for k in ks]
    stxt = ax.text(0, 0, "", ha="center", va="bottom", fontsize=11, fontweight="bold", color="#E07B39")
    slab = bx.text(0, 0, "", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#16A34A")
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    starts = [4 + j * 72.0 / n for j in range(n)]
    sstarts = [100 + j * 34.0 / n for j in range(n)]
    opname = (f"×{_p(q)}" if geo else (f"+{_f(q)}" if q >= 0 else f"−{_f(-q)}"))
    N = 150

    def update(i):
        cur = -1
        for j in range(n):
            g = _cl((i - starts[j]) / 4)
            tb[j].set_height(tv[j] * g)
            if i >= starts[j]:
                cur = j
            if i >= 80 and j == n - 1:
                tb[j].set_facecolor("#DC2626")
                tb[j].set_alpha(0.75)
            elif j == cur and i < 80:
                tb[j].set_facecolor("#E07B39")
                tb[j].set_alpha(0.8)
            else:
                tb[j].set_facecolor("#2563EB")
                tb[j].set_alpha(0.45)
            on = i >= starts[j] + 4 and (show_all or j == cur or j == n - 1 or j == 0)
            vlabs[j].set_text(_f(terms[j]) if on else "")
        shown = [j for j in range(n) if i >= starts[j] + 4]
        dots.set_data([ks[j] for j in shown], [tv[j] for j in shown])
        if 1 <= cur and i < 80:
            ytop = max(tv[cur], tv[cur - 1], 0.0)
            stxt.set_position((cur + 0.5, ytop + 0.08 * span_t))
            stxt.set_text(opname)
        else:
            stxt.set_text("")
        lastc = -1
        for j in range(n):
            g = _cl((i - sstarts[j]) / 3)
            sb[j].set_height(sv[j] * g)
            if i >= sstarts[j]:
                lastc = j
            if i >= 136 and j == n - 1:
                sb[j].set_facecolor("#DC2626")
                sb[j].set_alpha(0.75)
            else:
                sb[j].set_facecolor("#16A34A")
                sb[j].set_alpha(0.45)
        if lastc >= 0:
            yv = sv[lastc]
            slab.set_position((ks[lastc], yv + (0.015 if yv >= 0 else -0.015) * span_s))
            slab.set_va("bottom" if yv >= 0 else "top")
            slab.set_text(_f(sums[lastc]))
        else:
            slab.set_text("")
        if i < 80:
            j = max(cur, 0)
            if geo:
                rule = f"r = {_f(q)}: her terim bir öncekinin {_p(q)} katı" if tr else f"r = {_f(q)}: each term is {_p(q)} × the previous"
            else:
                rule = f"d = {_f(q)}: her adımda {opname}" if tr else f"d = {_f(q)}: add {_f(q)} each step"
            info.set_text(("1) Geometrik dizi, " if geo else "1) Aritmetik dizi, ") + rule + f"\n    a{_sub(j + 1)} = {_f(terms[j])}"
                          if tr else
                          ("1) Geometric sequence, " if geo else "1) Arithmetic sequence, ") + rule + f"\n    a{_sub(j + 1)} = {_f(terms[j])}")
        elif i < 100:
            if geo:
                info.set_text(f"2) aₙ = a₁·rⁿ⁻¹  ⇒  {A} = {_p(a1)}·{_p(q)}{_sup(n - 1)} = {_f(terms[-1])}")
            else:
                info.set_text(f"2) aₙ = a₁ + (n − 1)d  ⇒  {A} = {_f(a1)} + {n - 1}·{_p(q)} = {_f(terms[-1])}")
        elif i < 136:
            info.set_text(("3) Kısmi toplamlar: Sₖ = a₁ + a₂ + … + aₖ" if tr else
                           "3) Partial sums: Sₖ = a₁ + a₂ + … + aₖ"))
        else:
            if geo and q != 1:
                frm = f"Sₙ = a₁(1 − rⁿ)/(1 − r) ⇒ {S} = {_f(sums[-1])}"
            elif geo:
                frm = f"Sₙ = n·a₁ ⇒ {S} = {_f(sums[-1])}"
            else:
                frm = f"Sₙ = n(a₁ + aₙ)/2 ⇒ {S} = {n}·({_f(a1)} + {_p(terms[-1])})/2 = {_f(sums[-1])}"
            info.set_text(f"{A} = {_f(terms[-1])}\n{frm}")
        return []

    return N, update


def vary(P, rnd):
    if P.get("type", "arithmetic") == "geometric":
        r0 = float(P["d_or_r"])
        if abs(r0) < 1:
            a1, r = rnd.choice([(16, 0.5), (32, 0.5), (64, 0.5), (64, 0.25), (80, 0.5), (128, 0.5)])
            return {"type": "geometric", "a1": a1, "d_or_r": r, "n": rnd.randint(5, 7)}
        r = rnd.choice([2, 3, -2, 2])
        n = rnd.randint(5, 7) if abs(r) == 3 else rnd.randint(5, 9)
        return {"type": "geometric", "a1": rnd.choice([1, 2, 3, 4, 5]), "d_or_r": r, "n": n}
    d = rnd.choice([v for v in range(-5, 7) if v != 0])
    return {"type": "arithmetic", "a1": rnd.randint(-5, 12), "d_or_r": d, "n": rnd.randint(8, 15)}
''',
}
EXAMPLES += [
    {"id": "alg-seq-1", "kind": "sequence",
     "title": ("Aritmetik dizi: genel terim ve toplam", "Arithmetic sequence: nth term and sum"),
     "q": ("{first} aritmetik dizisinin {n}. terimini ({an}) ve ilk {n} teriminin toplamını ({Sn}) bul.",
           "For the arithmetic sequence {first}, find the {n}th term ({an}) and the sum of the first {n} terms ({Sn})."),
     "P": {"type": "arithmetic", "a1": 3, "d_or_r": 4, "n": 12}},
    {"id": "alg-seq-2", "kind": "sequence",
     "title": ("Geometrik dizi: genel terim ve toplam", "Geometric sequence: nth term and sum"),
     "q": ("İlk terimi {a1}, ortak oranı {d_or_r} olan geometrik dizinin {an} terimini ve {Sn} toplamını hesapla.",
           "A geometric sequence has first term {a1} and common ratio {d_or_r}. Compute {an} and {Sn}."),
     "P": {"type": "geometric", "a1": 2, "d_or_r": 3, "n": 6}},
    {"id": "alg-seq-3", "kind": "sequence", "topics": ["bouncing ball", "word problem", "sözel problem", "zıplayan top"],
     "title": ("Sözel problem: zıplayan top", "Word problem: bouncing ball"),
     "q": ("Bir top yere çarpıp ilk seferde {a1} m yükseliyor; her sıçrayışta bir önceki yüksekliğin {d_or_r} katına "
           "çıkıyor. {n}. sıçrayışın yüksekliği ({an}) ve ilk {n} sıçrayış yüksekliklerinin toplamı ({Sn}) nedir?",
           "A ball rebounds {a1} m after its first bounce, and each rebound reaches {d_or_r} of the previous height. "
           "What is the height of the {n}th rebound ({an}) and the total of the first {n} rebound heights ({Sn})?"),
     "P": {"type": "geometric", "a1": 16, "d_or_r": 0.5, "n": 6}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["circle_equation"] = {
    "course": "alg",
    "title": ("Çemberin denklemi", "Equation of a circle"),
    "topics": ["circle", "circles", "equation of a circle", "standard form of a circle", "center and radius",
               "completing the square", "conic sections", "conics", "general form", "çember", "çemberin denklemi",
               "merkez ve yarıçap", "kareye tamamlama", "konikler"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction


def _F(v):
    return Fraction(v).limit_denominator(1000)


def _f(v):
    v = _F(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _cl(t):
    return min(1.0, max(0.0, t))


def _sq(name, c):
    c = _F(c)
    if c == 0:
        return f"{name}²"
    return f"({name} - {_f(c)})²" if c > 0 else f"({name} + {_f(-c)})²"


def _lin(coef, name):
    coef = _F(coef)
    if coef == 0:
        return ""
    mag = "" if abs(coef) == 1 else _f(abs(coef))
    return f" {'+' if coef > 0 else '-'} {mag}{name}"


def _const(c):
    c = _F(c)
    if c == 0:
        return ""
    return f" {'+' if c > 0 else '-'} {_f(abs(c))}"


def _forms(P):
    h, k, r = _F(P["h"]), _F(P["k"]), _F(P["r"])
    r2 = r * r
    D, E, Fc = -2 * h, -2 * k, h * h + k * k - r2
    std = f"{_sq('x', h)} + {_sq('y', k)} = {_f(r2)}"
    gen = "x² + y²" + _lin(D, "x") + _lin(E, "y") + _const(Fc) + " = 0"
    return h, k, r, r2, D, E, Fc, std, gen


def solve(P):
    h, k, r, r2, D, E, Fc, std, gen = _forms(P)
    hx, ky = D * D / 4, E * E / 4
    gx = "(x²" + _lin(D, "x") + ")"
    gy = "(y²" + _lin(E, "y") + ")"
    cx = "(x²" + _lin(D, "x") + _const(hx) + ")"
    cy = "(y²" + _lin(E, "y") + _const(ky) + ")"
    if P.get("given", "center") == "general":
        steps = [
            (f"Genel form: {gen}", f"General form: {gen}"),
            (f"x'li ve y'li terimleri grupla, sabiti sağa al: {gx} + {gy} = {_f(-Fc)}",
             f"Group the x and y terms, move the constant: {gx} + {gy} = {_f(-Fc)}"),
            (f"Kareye tamamla: (D/2)² = ({_f(D)}/2)² = {_f(hx)},  (E/2)² = ({_f(E)}/2)² = {_f(ky)}; her iki tarafa ekle",
             f"Complete the square: (D/2)² = ({_f(D)}/2)² = {_f(hx)},  (E/2)² = ({_f(E)}/2)² = {_f(ky)}; add to both sides"),
            (f"{cx} + {cy} = {_f(-Fc)} + {_f(hx)} + {_f(ky)}", f"{cx} + {cy} = {_f(-Fc)} + {_f(hx)} + {_f(ky)}"),
            (f"Standart form: {std}", f"Standard form: {std}"),
            (f"Merkez (h, k) = ({_f(h)}, {_f(k)}),  yarıçap r = √{_f(r2)} = {_f(r)}",
             f"Centre (h, k) = ({_f(h)}, {_f(k)}),  radius r = √{_f(r2)} = {_f(r)}"),
        ]
    else:
        ex = f"x²{_lin(D, 'x')}{_const(h * h)} + y²{_lin(E, 'y')}{_const(k * k)} = {_f(r2)}"
        steps = [
            (f"Merkez (h, k) = ({_f(h)}, {_f(k)}),  yarıçap r = {_f(r)}",
             f"Centre (h, k) = ({_f(h)}, {_f(k)}),  radius r = {_f(r)}"),
            ("Çember: merkeze uzaklığı r olan noktalar ⇒ (x − h)² + (y − k)² = r²  (Pisagor / uzaklık formülü)",
             "A circle is every point at distance r from the centre ⇒ (x − h)² + (y − k)² = r²  (Pythagoras / distance formula)"),
            (f"Yerine koy: {std}", f"Substitute: {std}"),
            (f"Parantezleri aç: {ex}", f"Expand: {ex}"),
            (f"Genel form: {gen}", f"General form: {gen}"),
        ]
    steps.append((f"Kontrol noktaları: ({_f(h + r)}, {_f(k)}), ({_f(h - r)}, {_f(k)}), ({_f(h)}, {_f(k + r)}), ({_f(h)}, {_f(k - r)}) çember üzerinde",
                  f"Check points: ({_f(h + r)}, {_f(k)}), ({_f(h - r)}, {_f(k)}), ({_f(h)}, {_f(k + r)}), ({_f(h)}, {_f(k - r)}) lie on the circle"))
    return {"answer": (f"{std};  merkez ({_f(h)}, {_f(k)}), r = {_f(r)}",
                       f"{std};  centre ({_f(h)}, {_f(k)}), r = {_f(r)}"),
            "steps": steps,
            "fmt": {"std": std, "gen": gen, "center": f"({_f(h)}, {_f(k)})"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    h, k, r, r2, D, E, Fc, std, gen = _forms(P)
    hf, kf, rf = float(h), float(k), float(r)
    general = P.get("given", "center") == "general"
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.32], left=0.02, right=0.98, top=0.86, bottom=0.07, wspace=0.04)
    tx = fig.add_subplot(gs[0, 0])
    tx.axis("off")
    tx.set_xlim(0, 1)
    tx.set_ylim(0, 1)
    ax = fig.add_subplot(gs[0, 1])
    x0, x1 = min(hf - rf, 0.0) - 1.9, max(hf + rf, 0.0) + 1.9
    y0, y1 = min(kf - rf, 0.0) - 1.5, max(kf + rf, 0.0) + 1.5
    side = max(x1 - x0, y1 - y0)
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    ax.set_xlim(cx_ - side / 2, cx_ + side / 2)
    ax.set_ylim(cy_ - side / 2, cy_ + side / 2)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.1)
    ax.axvline(0, color="#374151", lw=1.1)
    hx, ky = D * D / 4, E * E / 4
    if general:
        rows = [(gen, "#111827"),
                ("(x²" + _lin(D, "x") + ") + (y²" + _lin(E, "y") + f") = {_f(-Fc)}", "#111827"),
                ("(x²" + _lin(D, "x") + _const(hx) + ") + (y²" + _lin(E, "y") + _const(ky) + ")", "#111827"),
                (f"     = {_f(-Fc)} + {_f(hx)} + {_f(ky)}", "#111827"),
                (std, "#2563EB"),
                (f"M({_f(h)}, {_f(k)}),  r = {_f(r)}", "#DC2626")]
        notes = [("genel form", "general form"), ("grupla", "group"), ("kareye tamamla", "complete the square"),
                 ("", ""), ("standart form", "standard form"), ("merkez ve yarıçap", "centre and radius")]
    else:
        rows = [(f"M({_f(h)}, {_f(k)}),  r = {_f(r)}", "#DC2626"),
                ("(x − h)² + (y − k)² = r²", "#6B7280"),
                (std, "#2563EB"),
                (f"x²{_lin(D, 'x')}{_const(h * h)} + y²{_lin(E, 'y')}{_const(k * k)}", "#111827"),
                (f"     = {_f(r2)}", "#111827"),
                (gen, "#111827")]
        notes = [("verilen", "given"), ("uzaklık formülü", "distance formula"), ("standart form", "standard form"),
                 ("aç", "expand"), ("", ""), ("genel form", "general form")]
    txts = []
    for j, (row, col) in enumerate(rows):
        t1 = tx.text(0.03, 0.93 - j * 0.155, row, fontsize=11.5, family="DejaVu Sans Mono", color=col,
                     va="center", alpha=0)
        t2 = tx.text(0.05, 0.93 - j * 0.155 - 0.055, notes[j][0 if tr else 1], fontsize=9, color="#6B7280",
                     va="center", alpha=0)
        txts.append((t1, t2))
    th = np.linspace(0, 2 * np.pi, 361)
    circ, = ax.plot([], [], color="#2563EB", lw=2.6)
    arm, = ax.plot([], [], color="#E07B39", lw=2.2)
    cdot, = ax.plot([], [], "o", color="#DC2626", ms=9, zorder=7)
    clab = ax.text(hf, kf - 0.06 * side, "", color="#DC2626", fontsize=11, fontweight="bold", ha="center", va="top")
    pdot, = ax.plot([], [], "o", color="#E07B39", ms=9, zorder=7)
    rlab = ax.text(0, 0, "", color="#E07B39", fontsize=11, fontweight="bold", ha="center", va="center")
    kpts, = ax.plot([], [], "s", color="#7C3AED", ms=8, zorder=7)
    pts4 = [(hf + rf, kf), (hf - rf, kf), (hf, kf + rf), (hf, kf - rf)]
    plabs = []
    for (px, py), (ha_, va_) in zip(pts4, [("left", "center"), ("right", "center"), ("center", "bottom"), ("center", "top")]):
        dx = 0.03 * side if ha_ == "left" else (-0.03 * side if ha_ == "right" else 0)
        dy = 0.03 * side if va_ == "bottom" else (-0.03 * side if va_ == "top" else 0)
        plabs.append(ax.text(px + dx, py + dy, "", color="#7C3AED", fontsize=10, ha=ha_, va=va_,
                             bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8)))
    info = fig.text(0.02, 0.975, "", va="top", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    sh = "-" if h >= 0 else "+"
    sk = "-" if k >= 0 else "+"
    nrow = len(rows)
    N = 150

    def update(i):
        for j, (t1, t2) in enumerate(txts):
            al = _cl((i - j * 9) / 8)
            t1.set_alpha(al)
            t2.set_alpha(al)
        if i >= 40:
            cdot.set_data([hf], [kf])
            clab.set_text(f"M({_f(h)}, {_f(k)})")
        else:
            cdot.set_data([], [])
            clab.set_text("")
        sw = _cl((i - 55) / 55)
        if sw > 0:
            m = max(2, int(sw * (len(th) - 1)) + 1)
            circ.set_data(hf + rf * np.cos(th[:m]), kf + rf * np.sin(th[:m]))
            ang = th[m - 1]
            px, py = hf + rf * math.cos(ang), kf + rf * math.sin(ang)
            arm.set_data([hf, px], [kf, py])
            pdot.set_data([px], [py])
            rlab.set_position((hf + 0.55 * rf * math.cos(ang) - 0.05 * side * math.sin(ang),
                               kf + 0.55 * rf * math.sin(ang) + 0.05 * side * math.cos(ang)))
            rlab.set_text(f"r = {_f(r)}")
        else:
            circ.set_data([], [])
            arm.set_data([], [])
            pdot.set_data([], [])
            rlab.set_text("")
            px = py = None
        if i >= 112:
            kpts.set_data([p[0] for p in pts4], [p[1] for p in pts4])
            for (qx, qy), t in zip(pts4, plabs):
                t.set_text(f"({_f(_F(qx))}, {_f(_F(qy))})")
        else:
            kpts.set_data([], [])
            for t in plabs:
                t.set_text("")
        if i < 40:
            info.set_text(("1) Denklemi adım adım düzenle" if tr else "1) Rewrite the equation step by step")
                          if general else ("1) Merkez ve yarıçaptan denklem" if tr else "1) Equation from centre and radius"))
        elif i < 55:
            info.set_text((f"2) Merkez M({_f(h)}, {_f(k)})") if tr else (f"2) Centre M({_f(h)}, {_f(k)})"))
        elif i < 112 and px is not None:
            info.set_text((f"3) r = {_f(r)} uzunluğundaki kolu döndür;  P({px:.2f}, {py:.2f}):\n"
                           f"    ({px:.2f} {sh} {_f(abs(h))})² + ({py:.2f} {sk} {_f(abs(k))})² = "
                           f"{(px - hf) ** 2 + (py - kf) ** 2:.2f} = r²") if tr else
                          (f"3) Sweep an arm of length r = {_f(r)};  P({px:.2f}, {py:.2f}):\n"
                           f"    ({px:.2f} {sh} {_f(abs(h))})² + ({py:.2f} {sk} {_f(abs(k))})² = "
                           f"{(px - hf) ** 2 + (py - kf) ** 2:.2f} = r²"))
        elif i < 132:
            info.set_text("4) Merkezden sağa, sola, yukarı, aşağı r birim" if tr else
                          "4) r units right, left, up and down from the centre")
        else:
            info.set_text((f"{std}\nmerkez ({_f(h)}, {_f(k)}), r = {_f(r)}") if tr else
                          (f"{std}\ncentre ({_f(h)}, {_f(k)}), r = {_f(r)}"))
        return []

    return N, update


def vary(P, rnd):
    return {"h": rnd.randint(-5, 5), "k": rnd.randint(-5, 5), "r": rnd.randint(2, 6),
            "given": P.get("given", "center")}
''',
}
EXAMPLES += [
    {"id": "alg-circle-1", "kind": "circle_equation",
     "title": ("Merkez ve yarıçaptan çember denklemi", "Circle from centre and radius"),
     "q": ("Merkezi {center} ve yarıçapı {r} olan çemberin standart ve genel denklemini yaz.",
           "Write the standard and general equations of the circle with centre {center} and radius {r}."),
     "P": {"h": 2, "k": -3, "r": 5, "given": "center"}},
    {"id": "alg-circle-2", "kind": "circle_equation",
     "title": ("Kareye tamamlayarak merkez ve yarıçap", "Centre and radius by completing the square"),
     "q": ("{gen} denklemiyle verilen çemberin merkezini ve yarıçapını kareye tamamlayarak bul.",
           "Complete the square to find the centre and radius of the circle {gen}."),
     "P": {"h": -3, "k": 4, "r": 4, "given": "general"}},
    {"id": "alg-circle-3", "kind": "circle_equation", "topics": ["word problem", "sözel problem", "coverage"],
     "title": ("Sözel problem: verici menzili", "Word problem: transmitter range"),
     "q": ("Bir radyo vericisi koordinat düzleminde {center} noktasında ve {r} km menzile sahip. Kapsama alanının "
           "sınırını veren çemberin denklemini yaz.",
           "A radio transmitter stands at {center} on a coordinate grid and has a range of {r} km. Write the "
           "equation of the circle that bounds its coverage."),
     "P": {"h": 4, "k": 1, "r": 6, "given": "center"}},
]
