# -*- coding: utf-8 -*-
"""Geometri (ve temel trigonometri) simülasyonları.

Pisagor, üçgen/daire alanı, açı toplamları, benzerlik, dönüşümler, uzaklık ve
orta nokta, katı cisimler (3B), yay/daire dilimi, birim çember, sinüs dalgası
ve dik üçgen trigonometrisi.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Sorular kitaplardan
KOPYALANMAZ: kendi ifademizle yazılmış, kendi sayılarımızla tipik ders
örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["pythagorean"] = {
    "course": "geo",
    "title": ("Pisagor teoremi", "Pythagorean theorem"),
    "topics": ["pythagorean", "pythagoras", "pythagorean theorem", "pythagorean triple",
               "right triangle", "right triangles", "hypotenuse", "missing side", "legs",
               "pisagor", "pisagor teoremi", "dik üçgen", "hipotenüs", "dik kenar"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Polygon, Rectangle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _n(v, nd=2):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        s = str(int(round(v)))
    else:
        s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s.replace("-", "−")


def _layout(fig, wr=(1.35, 1.0)):
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=list(wr), left=0.02,
                          right=0.98, top=0.98, bottom=0.03, wspace=0.04, hspace=0.06)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left",
                    fontsize=11.5, color="#111827",
                    bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    return ax, tx, info


def _panel(tx, title, lines, fs=12.5, dy=0.105):
    tx.text(0.05, 0.96, title, transform=tx.transAxes, va="top", fontsize=11,
            color="#6B7280", fontweight="bold")
    out = []
    for k, s in enumerate(lines):
        out.append(tx.text(0.05, 0.86 - k * dy, s, transform=tx.transAxes, va="top",
                           fontsize=fs, color="#111827", alpha=0.0))
    if out:
        out[-1].set_color("#DC2626")
        out[-1].set_fontweight("bold")
    return out


def _root(v):
    # exact square root of an integer as text: 25 -> '5', 50 -> '5√2'; None otherwise
    if v < 0 or abs(v - round(v)) > 1e-9:
        return None
    n = int(round(v))
    r = math.isqrt(n)
    if r * r == n:
        return str(r)
    k, m, f = 1, n, 2
    while f * f <= m:
        while m % (f * f) == 0:
            k *= f
            m //= f * f
        f += 1
    return (str(k) if k > 1 else "") + "√" + str(m)


def _sides(P):
    # legs a, b given -> find c;   leg a and hypotenuse c given (no b) -> find b
    a = float(P["a"])
    if "b" in P or "c" not in P:
        b = float(P["b"])
        return "c", a, b, math.hypot(a, b)
    c = float(P["c"])
    return "b", a, math.sqrt(max(c * c - a * a, 0.0)), c


def _val(name, sq, v):
    r = _root(sq)
    head = f"{name} = √{_n(sq)}"
    if r is not None and "√" not in r:
        return head + f" = {r}", f"{name} = {r}"
    if r is not None:
        return head + f" = {r} ≈ {_n(v, 3)}", f"{name} = {r} ≈ {_n(v, 3)}"
    return head + f" ≈ {_n(v, 3)}", f"{name} ≈ {_n(v, 3)}"


def solve(P):
    unk, a, b, c = _sides(P)
    unit = P.get("unit", "")
    us = f" {unit}" if unit else ""
    if unk == "c":
        s = a * a + b * b
        full, short = _val("c", s, c)
        steps = [
            ("Pisagor teoremi: a² + b² = c²  (c: hipotenüs, a ve b: dik kenarlar)",
             "Pythagorean theorem: a² + b² = c²  (c: hypotenuse, a and b: legs)"),
            (f"Yerine koy: {_n(a)}² + {_n(b)}² = c²", f"Substitute: {_n(a)}² + {_n(b)}² = c²"),
            (f"{_n(a * a)} + {_n(b * b)} = c²  ⇒  c² = {_n(s)}",
             f"{_n(a * a)} + {_n(b * b)} = c²  ⇒  c² = {_n(s)}"),
            (f"Karekök al (uzunluk pozitif): {full}{us}",
             f"Take the square root (length is positive): {full}{us}"),
            (f"Geometrik anlam: {_n(a * a)} ve {_n(b * b)} birim karelik alanlar birlikte "
             f"{_n(s)} birim karelik hipotenüs karesini doldurur.",
             f"Geometric meaning: the areas {_n(a * a)} and {_n(b * b)} together fill the "
             f"hypotenuse square of area {_n(s)}."),
        ]
        return {"answer": short + us, "steps": steps, "fmt": {"c2": _n(s)}}
    if c <= a:
        msg = ("Hipotenüs dik kenardan uzun olmalı (c > a).",
               "The hypotenuse must be longer than the leg (c > a).")
        return {"answer": msg, "steps": [msg, ("b² = c² − a² pozitif olmalı.",
                                                "b² = c² − a² must be positive.")], "fmt": {}}
    s = c * c - a * a
    full, short = _val("b", s, b)
    steps = [
        ("Pisagor teoremi: a² + b² = c²  (c: hipotenüs)", "Pythagorean theorem: a² + b² = c²  (c: hypotenuse)"),
        ("Eksik dik kenar için düzenle: b² = c² − a²", "Rearrange for the missing leg: b² = c² − a²"),
        (f"Yerine koy: b² = {_n(c)}² − {_n(a)}² = {_n(c * c)} − {_n(a * a)} = {_n(s)}",
         f"Substitute: b² = {_n(c)}² − {_n(a)}² = {_n(c * c)} − {_n(a * a)} = {_n(s)}"),
        (f"Karekök al: {full}{us}", f"Take the square root: {full}{us}"),
        (f"Kontrol: {_n(a)}² + {_n(b)}² = {_n(a * a + b * b)} = {_n(c)}² ✓",
         f"Check: {_n(a)}² + {_n(b)}² = {_n(a * a + b * b)} = {_n(c)}² ✓"),
    ]
    return {"answer": short + us, "steps": steps, "fmt": {"c2": _n(c * c)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    unk, a, b, c = _sides(P)
    if not (b > 0 and c > a):
        b = max(b, 0.5 * a)
        c = math.hypot(a, b)
    ax, tx, info = _layout(fig)
    ax.set_aspect("equal")
    ax.axis("off")
    span = a + b
    pad = 0.06 * span
    ax.set_xlim(-b - pad, a + b + pad)
    ax.set_ylim(-a - pad, a + b + pad)
    A = np.array([a, 0.0])
    B = np.array([0.0, b])
    nv = np.array([b, a]) / c
    CA, CB, CC = "#E07B39", "#16A34A", "#7C3AED"

    def sq_a(g):
        return [(0, 0), (a, 0), (a, -a * g), (0, -a * g)]

    def sq_b(g):
        return [(0, 0), (0, b), (-b * g, b), (-b * g, 0)]

    def band(d0, d1):
        return [A + d0 * nv, B + d0 * nv, B + d1 * nv, A + d1 * nv]

    def patch(xy, **kw):
        p = Polygon(xy, closed=True, **kw)
        ax.add_patch(p)
        return p

    pAf = patch(sq_a(0), fc=CA, ec="none", alpha=0.5, zorder=2)
    pAo = patch(sq_a(0), fc="none", ec=CA, lw=2, zorder=3)
    pBf = patch(sq_b(0), fc=CB, ec="none", alpha=0.5, zorder=2)
    pBo = patch(sq_b(0), fc="none", ec=CB, lw=2, zorder=3)
    cC = patch(band(0, 0), fc=CC, ec="none", alpha=0.3, zorder=2)
    cA = patch(band(0, 0), fc=CA, ec="none", alpha=0.5, zorder=2)
    cB = patch(band(0, 0), fc=CB, ec="none", alpha=0.5, zorder=2)
    pCo = patch(band(0, 0), fc="none", ec=CC, lw=2, zorder=3)
    tri = patch([(0, 0), A, B], fc="#DBEAFE", ec="#2563EB", lw=2.4, zorder=5)
    m = 0.13 * min(a, b)
    rmark, = ax.plot([m, m, 0], [0, m, m], color="#2563EB", lw=1.2, zorder=6)
    fs = 10.5
    lfs = 12
    tA = ax.text(a / 2, -a / 2, "", ha="center", va="center", fontsize=fs, color="#7C2D12", zorder=8)
    tB = ax.text(-b / 2, b / 2, "", ha="center", va="center", fontsize=fs, color="#14532D", zorder=8)
    ctr = (A + B) / 2 + nv * c / 2
    tC = ax.text(ctr[0], ctr[1], "", ha="center", va="center", fontsize=fs + 0.5,
                 color="#4C1D95", zorder=8)
    la = ax.text(a / 2, 0.025 * span, "", ha="center", va="bottom", fontsize=lfs, color="#1E3A8A",
                 style="italic", fontweight="bold", zorder=7)
    lb = ax.text(0.025 * span, 0.62 * b, "", ha="left", va="center", fontsize=lfs, color="#1E3A8A",
                 style="italic", fontweight="bold", zorder=7)
    mid = A + 0.42 * (B - A) - nv * 0.04 * span
    lc = ax.text(mid[0], mid[1], "", ha="center", va="center", fontsize=lfs, color="#1E3A8A",
                 style="italic", fontweight="bold", zorder=7)
    sa, sb, sc = a * a, b * b, c * c
    sol = solve(P)["answer"]
    sol = sol[0 if tr else 1] if isinstance(sol, tuple) else sol
    if unk == "c":
        lines = ["a² + b² = c²", f"{_n(a)}² + {_n(b)}² = c²", f"{_n(sa)} + {_n(sb)} = c²",
                 f"c² = {_n(sa + sb)}", sol]
        narr = [
            (f"1) Dik üçgen: dik kenarlar a = {_n(a)}, b = {_n(b)}; hipotenüs c = ?",
             f"1) Right triangle: legs a = {_n(a)}, b = {_n(b)}; hypotenuse c = ?"),
            (f"2) a kenarı üzerine kare: alanı a² = {_n(sa)}", f"2) Square on leg a: area a² = {_n(sa)}"),
            (f"3) b kenarı üzerine kare: alanı b² = {_n(sb)}", f"3) Square on leg b: area b² = {_n(sb)}"),
            ("4) Hipotenüs üzerine kare: alanı c²", "4) Square on the hypotenuse: area c²"),
            ("5) İki küçük karenin alanı büyük kareyi tam doldurur: a² + b² = c²",
             "5) The two small squares exactly fill the big one: a² + b² = c²"),
            (f"6) c² = {_n(sa + sb)}  ⇒  {sol}", f"6) c² = {_n(sa + sb)}  ⇒  {sol}"),
        ]
    else:
        lines = ["a² + b² = c²", "b² = c² − a²", f"b² = {_n(c)}² − {_n(a)}²",
                 f"b² = {_n(sc)} − {_n(sa)} = {_n(sc - sa)}", sol]
        narr = [
            (f"1) Dik üçgen: dik kenar a = {_n(a)}, hipotenüs c = {_n(c)}; diğer dik kenar b = ?",
             f"1) Right triangle: leg a = {_n(a)}, hypotenuse c = {_n(c)}; other leg b = ?"),
            (f"2) a kenarı üzerine kare: alanı a² = {_n(sa)}", f"2) Square on leg a: area a² = {_n(sa)}"),
            ("3) b kenarı üzerine kare: alanı b² (bilinmiyor)", "3) Square on leg b: area b² (unknown)"),
            (f"4) Hipotenüs üzerine kare: alanı c² = {_n(sc)}", f"4) Square on the hypotenuse: area c² = {_n(sc)}"),
            ("5) c² karesinden a² kadarı çıkınca kalan alan b² karesini doldurur",
             "5) Take a² out of the c² square: the rest fills the b² square"),
            (f"6) b² = {_n(sc)} − {_n(sa)} = {_n(sc - sa)}  ⇒  {sol}",
             f"6) b² = {_n(sc)} − {_n(sa)} = {_n(sc - sa)}  ⇒  {sol}"),
        ]
    arts = _panel(tx, "Adım adım" if tr else "Step by step", lines, fs=12)
    times = [16, 40, 66, 96, 126]
    starts = [0, 14, 38, 62, 90, 126]
    dA = sa / c
    N = 150

    def update(i):
        t0 = _ph(i, 0, 10)
        tri.set_alpha(t0)
        rmark.set_alpha(t0)
        gA = _ease(_ph(i, 14, 36))
        gB = _ease(_ph(i, 38, 60))
        gC = _ease(_ph(i, 62, 86))
        pAf.set_xy(sq_a(gA))
        pAo.set_xy(sq_a(gA))
        pBo.set_xy(sq_b(gB))
        pCo.set_xy(band(0, c * gC))
        la.set_text("a" if i >= 4 else "")
        tA.set_text(f"a² = {_n(sa)}" if gA > 0.6 else "")
        done = i >= 124
        if unk == "c":
            lb.set_text("b" if i >= 4 else "")
            lc.set_text("c" if i >= 4 else "")
            lc.set_color("#DC2626" if done else "#1E3A8A")
            pBf.set_xy(sq_b(gB))
            pa = _ph(i, 90, 106)
            pb = _ph(i, 106, 122)
            cA.set_xy(band(0, dA * pa))
            cB.set_xy(band(dA, dA + (sb / c) * pb) if pb > 0 else band(0, 0))
            pAf.set_alpha(0.5 - 0.38 * pa)
            pBf.set_alpha(0.5 - 0.38 * pb)
            tB.set_text(f"b² = {_n(sb)}" if gB > 0.6 else "")
            if gC <= 0.6:
                tC.set_text("")
            elif pb < 1:
                tC.set_text("c² = ?")
            elif not done:
                tC.set_text(f"c² = {_n(sa)} + {_n(sb)}\n= {_n(sa + sb)}")
            else:
                tC.set_text(f"c² = {_n(sa + sb)}\n{sol}")
            tC.set_color("#DC2626" if done else "#4C1D95")
        else:
            lb.set_text("b" if i >= 4 else "")
            lb.set_color("#DC2626" if done else "#1E3A8A")
            lc.set_text("c" if i >= 4 else "")
            ps = _ph(i, 90, 102)
            pm = _ph(i, 104, 122)
            cC.set_xy(band(0, c * gC))
            cC.set_alpha(0.3 * (1 - ps))
            cA.set_xy(band(0, dA))
            cA.set_alpha(0.5 * ps)
            cB.set_xy(band(dA, dA + (c - dA) * (1 - pm)))
            cB.set_alpha(0.5 * ps)
            pBf.set_xy(sq_b(pm))
            tB.set_text("" if gB <= 0.6 else ("b² = ?" if pm < 1 else (
                f"b² = {_n(sc)} − {_n(sa)}\n= {_n(sc - sa)}" if not done else
                f"b² = {_n(sc - sa)}\n{sol}")))
            tB.set_color("#DC2626" if done else "#14532D")
            tC.set_text(f"c² = {_n(sc)}" if gC > 0.6 else "")
        for t, s in zip(arts, times):
            t.set_alpha(_ph(i, s, s + 8))
        k = max(j for j, s in enumerate(starts) if i >= s)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    base = rnd.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29), (9, 40, 41)])
    k = rnd.choice([1, 1, 2, 3]) if base[2] <= 13 else 1
    a, b, c = (v * k for v in base)
    if rnd.random() < 0.5:
        a, b = b, a
    out = {key: val for key, val in P.items() if key not in ("a", "b", "c")}
    if "b" not in P and "c" in P:
        out.update({"a": a, "c": c})
    else:
        out.update({"a": a, "b": b})
    return out
''',
}
EXAMPLES += [
    {"id": "geo-pyth-1", "kind": "pythagorean",
     "title": ("Hipotenüsü bulma", "Finding the hypotenuse"),
     "q": ("Dik kenarları a = {a} ve b = {b} olan dik üçgenin hipotenüsü c kaçtır?",
           "A right triangle has legs a = {a} and b = {b}. How long is the hypotenuse c?"),
     "P": {"a": 3, "b": 4}},
    {"id": "geo-pyth-2", "kind": "pythagorean", "topics": ["word problem", "sözel problem", "missing leg"],
     "title": ("Eksik dik kenar: direk ve gergi teli", "Missing leg: pole and guy wire"),
     "q": ("{c} m uzunluğundaki bir gergi teli, direğin tepesinden yerde direğin dibinden {a} m "
           "uzaktaki bir kazığa bağlanıyor. Direğin boyu kaç metredir?",
           "A {c} m guy wire runs from the top of a pole to a stake {a} m from the pole's base. "
           "How tall is the pole?"),
     "P": {"a": 5, "c": 13, "unit": "m"}},
    {"id": "geo-pyth-3", "kind": "pythagorean", "topics": ["diagonal", "köşegen", "word problem"],
     "title": ("Parkın köşegeni", "Diagonal path across a park"),
     "q": ("Dikdörtgen bir parkın kenarları {a} m ve {b} m. Bir köşeden karşı köşeye çapraz "
           "yürüyen biri kaç metre yürür?",
           "A rectangular park measures {a} m by {b} m. How far does someone walk going "
           "diagonally from one corner to the opposite corner?"),
     "P": {"a": 8, "b": 15, "unit": "m"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["triangle_area"] = {
    "course": "geo",
    "title": ("Üçgenin alanı", "Area of a triangle"),
    "topics": ["area of a triangle", "triangle area", "base and height", "altitude",
               "parallelogram", "area", "areas of polygons", "üçgenin alanı", "alan",
               "taban", "yükseklik", "paralelkenar", "alan hesabı"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Polygon, Rectangle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _d(v):
    v = Fraction(v).limit_denominator(10000)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        s = f"{float(v):.4f}".rstrip("0").rstrip(".")
    return s.replace("-", "−")


def _layout(fig, wr=(1.35, 1.0)):
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=list(wr), left=0.02,
                          right=0.98, top=0.98, bottom=0.03, wspace=0.04, hspace=0.06)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left",
                    fontsize=11.5, color="#111827",
                    bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    return ax, tx, info


def _panel(tx, title, lines, fs=12.5, dy=0.105):
    tx.text(0.05, 0.96, title, transform=tx.transAxes, va="top", fontsize=11,
            color="#6B7280", fontweight="bold")
    out = []
    for k, s in enumerate(lines):
        out.append(tx.text(0.05, 0.86 - k * dy, s, transform=tx.transAxes, va="top",
                           fontsize=fs, color="#111827", alpha=0.0))
    if out:
        out[-1].set_color("#DC2626")
        out[-1].set_fontweight("bold")
    return out


def _vals(P):
    return Fraction(str(P["base"])), Fraction(str(P["height"]))


def solve(P):
    b, h = _vals(P)
    A = b * h / 2
    unit = P.get("unit", "")
    u2 = f" {unit}²" if unit else ""
    steps = [
        ("Üçgenin alanı: A = ½ · taban · yükseklik (yükseklik: tepeden tabana dik uzaklık)",
         "Area of a triangle: A = ½ · base · height (height: perpendicular distance from apex to base)"),
        (f"Yerine koy: A = ½ · {_d(b)} · {_d(h)}", f"Substitute: A = ½ · {_d(b)} · {_d(h)}"),
        (f"A = {_d(b * h)} / 2 = {_d(A)}{u2}", f"A = {_d(b * h)} / 2 = {_d(A)}{u2}"),
        (f"Neden yarısı? Üçgen ve 180° döndürülmüş kopyası, alanı {_d(b)} · {_d(h)} = {_d(b * h)} "
         "olan bir paralelkenar oluşturur.",
         f"Why half? The triangle and a copy turned 180° form a parallelogram of area "
         f"{_d(b)} · {_d(h)} = {_d(b * h)}."),
        ("Tepe noktası tabana paralel kaydırılırsa taban ve yükseklik değişmez, alan da değişmez.",
         "Sliding the apex parallel to the base keeps the base and height, so the area stays the same."),
    ]
    return {"answer": f"A = {_d(A)}{u2}", "steps": steps, "fmt": {"area2": _d(b * h)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    bF, hF = _vals(P)
    b, h, s = float(bF), float(hF), float(P.get("shift", 0))
    AF = bF * hF / 2
    ax, tx, info = _layout(fig)
    ax.set_aspect("equal")
    ax.axis("off")
    D = 0.45 * b
    xs = [0.0, b, s - D, s + D, b + s, s]
    W = max(xs) - min(xs)
    ax.set_xlim(min(xs) - 0.07 * W, max(xs) + 0.07 * W)
    ax.set_ylim(-0.16 * W - 0.05 * h, h + 0.1 * W)
    ext, = ax.plot([], [], "--", color="#9CA3AF", lw=1.2, zorder=1)
    tri = Polygon([(0, 0), (b, 0), (s, h)], closed=True, fc="#BFDBFE", ec="#2563EB", lw=2.4,
                  alpha=0.95, zorder=4)
    cp = Polygon([(0, 0), (b, 0), (s, h)], closed=True, fc="#FED7AA", ec="#E07B39", lw=2.4,
                 alpha=0.0, zorder=3)
    para = Polygon([(0, 0), (b, 0), (b + s, h), (s, h)], closed=True, fc="none", ec="#7C3AED",
                   lw=3.2, ls="--", alpha=0.0, zorder=6)
    for p in (tri, cp, para):
        ax.add_patch(p)
    alt, = ax.plot([], [], "--", color="#DC2626", lw=1.6, zorder=5)
    rm, = ax.plot([], [], color="#DC2626", lw=1.1, zorder=5)
    apex, = ax.plot([], [], "o", color="#2563EB", ms=7, zorder=7)
    tb = ax.text(b / 2, -0.04 * W, ("taban = " if tr else "base = ") + _d(bF), ha="center",
                 va="top", fontsize=11, color="#1E3A8A")
    th = ax.text(0, 0, "", fontsize=11, color="#DC2626", va="center", zorder=8)
    ta = ax.text(0, 0, "", fontsize=11.5, ha="center", va="center", color="#1E3A8A", fontweight="bold",
                 zorder=8)
    tc = ax.text(0, 0, "", fontsize=11.5, ha="center", va="center", color="#9A3412", fontweight="bold",
                 zorder=8)
    tp = ax.text((b + s) / 2, h + 0.03 * W, "", fontsize=11.5, ha="center", va="bottom",
                 color="#7C3AED", fontweight="bold")
    M = np.array([(b + s) / 2, h / 2])
    V0 = np.array([[0.0, 0.0], [b, 0.0], [s, h]])
    lines = [("A = ½ · taban · yükseklik" if tr else "A = ½ · base · height"),
             ("Tepe kayar: b, h aynı ⇒ A aynı" if tr else "Apex slides: same b, h ⇒ same A"),
             ("2 üçgen = 1 paralelkenar" if tr else "2 triangles = 1 parallelogram"),
             (f"Paralelkenar: {_d(bF)} · {_d(hF)} = {_d(bF * hF)}" if tr else
              f"Parallelogram: {_d(bF)} · {_d(hF)} = {_d(bF * hF)}"),
             f"A = ½ · {_d(bF)} · {_d(hF)} = {_d(AF)}"]
    arts = _panel(tx, "Adım adım" if tr else "Step by step", lines, fs=11.5)
    times = [8, 40, 84, 104, 126]
    narr = [
        (f"1) Taban b = {_d(bF)}, yükseklik h = {_d(hF)} (tepeden tabana dik uzaklık)",
         f"1) Base b = {_d(bF)}, height h = {_d(hF)} (perpendicular distance apex → base)"),
        ("2) Tepe tabana paralel kayıyor: b ve h değişmez ⇒ alan değişmez",
         "2) The apex slides parallel to the base: b and h stay ⇒ the area stays"),
        ("3) Üçgenin 180° döndürülmüş bir kopyası ekleniyor", "3) Add a copy of the triangle turned 180°"),
        (f"4) İki üçgen bir paralelkenar oluşturur: alanı b · h = {_d(bF * hF)}",
         f"4) Two triangles make a parallelogram: area b · h = {_d(bF * hF)}"),
        (f"5) Üçgen bunun yarısıdır: A = ½ · {_d(bF)} · {_d(hF)} = {_d(AF)}",
         f"5) The triangle is half of it: A = ½ · {_d(bF)} · {_d(hF)} = {_d(AF)}"),
    ]
    starts = [0, 20, 62, 100, 124]
    N = 150

    def update(i):
        u = _ph(i, 20, 60)
        sc = s + D * math.sin(2 * math.pi * u)
        tri.set_xy([(0, 0), (b, 0), (sc, h)])
        apex.set_data([sc], [h])
        alt.set_data([sc, sc], [h, 0])
        ext.set_data([min(0.0, sc), max(b, sc)], [0, 0])
        m = 0.035 * W
        d = -1 if sc > b / 2 else 1
        rm.set_data([sc, sc + d * m, sc + d * m], [m, m, 0])
        th.set_position((sc + 0.02 * W, h * 0.55))
        th.set_text(f"h = {_d(hF)}" if i < 62 else "")
        ta.set_position(((b + sc) / 3, h / 3))
        ta.set_text(f"A = {_d(AF)}" if i < 100 else _d(AF))
        ta.set_color("#DC2626" if i >= 124 else "#1E3A8A")
        r = _ph(i, 62, 96)
        if r > 0:
            phi = math.pi * _ease(r)
            R = np.array([[math.cos(phi), -math.sin(phi)], [math.sin(phi), math.cos(phi)]])
            pts = (V0 - M) @ R.T + M
            cp.set_xy(pts)
            cp.set_alpha(0.85)
            g = pts.mean(axis=0)
            tc.set_position((g[0], g[1]))
            tc.set_text(_d(AF) if r >= 1 else "")
        else:
            cp.set_alpha(0.0)
            tc.set_text("")
        q = _ph(i, 100, 110)
        para.set_alpha(q)
        tp.set_text((f"b · h = {_d(bF)} · {_d(hF)} = {_d(bF * hF)}") if q > 0 else "")
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 8))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    while True:
        b = rnd.randint(4, 12)
        h = rnd.randint(3, 10)
        if (b * h) % 2 == 0:
            break
    out = dict(P)
    s0 = float(P.get("shift", 0))
    if s0 > float(P["base"]):
        sh = b + rnd.randint(1, 3)
    elif s0 < 0:
        sh = -rnd.randint(1, 3)
    else:
        sh = rnd.randint(1, b - 1)
    out.update({"base": b, "height": h, "shift": sh})
    return out
''',
}
EXAMPLES += [
    {"id": "geo-tri-area-1", "kind": "triangle_area",
     "title": ("Taban ve yükseklikten alan", "Area from base and height"),
     "q": ("Tabanı {base} birim, bu tabana ait yüksekliği {height} birim olan üçgenin alanı kaçtır?",
           "A triangle has base {base} and height {height} to that base. What is its area?"),
     "P": {"base": 6, "height": 4, "shift": 2}},
    {"id": "geo-tri-area-2", "kind": "triangle_area", "topics": ["obtuse triangle", "geniş açılı"],
     "title": ("Geniş açılı üçgen: yükseklik dışarıda", "Obtuse triangle: height outside"),
     "q": ("Geniş açılı bir üçgende taban {base} cm, tepeden tabanın uzantısına inen dikme {height} cm. "
           "Üçgenin alanını bul.",
           "In an obtuse triangle the base is {base} cm and the perpendicular from the apex to the "
           "extended base is {height} cm. Find the area."),
     "P": {"base": 5, "height": 6, "shift": 8, "unit": "cm"}},
    {"id": "geo-tri-area-3", "kind": "triangle_area", "topics": ["word problem", "sözel problem"],
     "title": ("Üçgen yelken", "Triangular sail"),
     "q": ("Üçgen bir yelkenin tabanı {base} m, yüksekliği {height} m. Kaç m² kumaş gerekir?",
           "A triangular sail has a base of {base} m and a height of {height} m. "
           "How many m² of fabric does it need?"),
     "P": {"base": 5, "height": 9, "shift": 1, "unit": "m"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["circle_area"] = {
    "course": "geo",
    "title": ("Dairenin alanı ve çevresi", "Area and circumference of a circle"),
    "topics": ["circle area", "area of a circle", "circumference", "circles", "radius",
               "diameter", "pi", "dairenin alanı", "daire", "çember", "çevre", "yarıçap",
               "çap", "pi sayısı"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Polygon, Circle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _d(v):
    v = Fraction(v).limit_denominator(10000)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        s = f"{float(v):.4f}".rstrip("0").rstrip(".")
    return s.replace("-", "−")


def _n(v, nd=2):
    v = float(v)
    s = str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return s.replace("-", "−")


def _pi(c):
    c = Fraction(c)
    return "π" if c == 1 else _d(c) + "π"


def _radius(P):
    return Fraction(str(P["r"] if "r" in P else P["radius"]))


def solve(P):
    r = _radius(P)
    r2 = r * r
    unit = P.get("unit", "")
    u1 = f" {unit}" if unit else ""
    u2 = f" {unit}²" if unit else ""
    A = float(r2) * math.pi
    C = float(2 * r) * math.pi
    steps = [
        ("Dairenin alanı: A = π · r²", "Area of a circle: A = π · r²"),
        (f"r = {_d(r)}  ⇒  r² = {_d(r)}² = {_d(r2)}", f"r = {_d(r)}  ⇒  r² = {_d(r)}² = {_d(r2)}"),
        (f"A = π · {_d(r2)} = {_pi(r2)}", f"A = π · {_d(r2)} = {_pi(r2)}"),
        (f"π ≈ 3.14159 alınırsa A ≈ {_n(A)}{u2}", f"With π ≈ 3.14159, A ≈ {_n(A)}{u2}"),
        (f"Çevre: C = 2πr = 2 · π · {_d(r)} = {_pi(2 * r)} ≈ {_n(C)}{u1}",
         f"Circumference: C = 2πr = 2 · π · {_d(r)} = {_pi(2 * r)} ≈ {_n(C)}{u1}"),
        ("Neden πr²? Daire ince halkalara ayrılıp düzleştirilirse tabanı 2πr, yüksekliği r olan "
         "bir üçgen oluşur: ½ · 2πr · r = πr².",
         "Why πr²? Cut the disc into thin rings and straighten them: they form a triangle with "
         "base 2πr and height r, so ½ · 2πr · r = πr²."),
    ]
    return {"answer": f"A = {_pi(r2)} ≈ {_n(A)}{u2}", "steps": steps,
            "fmt": {"d": _d(2 * r), "C": f"{_pi(2 * r)} ≈ {_n(C)}"}}


def _edge(rho, t, n=90):
    # ring of radius ρ cut at the top and opened out, bottom point fixed at (0, 0):
    # t = 0 full circle, t = 1 straight segment of length 2πρ
    al = np.linspace(-math.pi, math.pi, n)
    x = (1 - t) * rho * np.sin(al) + t * rho * al
    y = (1 - t) * rho * (1 - np.cos(al))
    return x, y


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    rF = _radius(P)
    r = float(rF)
    unit = P.get("unit", "")
    u2 = f" {unit}²" if unit else ""
    gs = fig.add_gridspec(3, 1, height_ratios=[0.13, 1.0, 0.34], left=0.02, right=0.98,
                          top=0.98, bottom=0.02, hspace=0.05)
    top = fig.add_subplot(gs[0])
    top.axis("off")
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left",
                    fontsize=11.5, color="#111827",
                    bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    ax = fig.add_subplot(gs[1])
    ax.axis("off")
    ax.set_aspect("equal")
    ax.set_xlim(-math.pi * r - 0.2 * r, math.pi * r + 0.2 * r)
    ax.set_ylim(-1.42 * r, 1.08 * r)
    bt = fig.add_subplot(gs[2])
    bt.axis("off")
    ghost = Circle((0, 0), r, fc="none", ec="#9CA3AF", lw=1.2, ls="--", zorder=1)
    ax.add_patch(ghost)
    K = 12
    c0 = np.array([0.86, 0.92, 1.0])
    c1 = np.array([0.15, 0.39, 0.92])
    bands = []
    for k in range(K):
        col = tuple(c0 + (c1 - c0) * (k + 0.5) / K)
        p = Polygon(np.zeros((4, 2)), closed=True, fc=col, ec="white", lw=0.6, zorder=2)
        ax.add_patch(p)
        bands.append((r * k / K, r * (k + 1) / K, p))
    circ, = ax.plot([], [], color="#DC2626", lw=3, zorder=5)
    rad, = ax.plot([0, r], [0, 0], color="#111827", lw=1.8, zorder=6)
    cdot, = ax.plot([0], [0], "o", color="#111827", ms=4, zorder=6)
    trad = ax.text(r / 2, 0.06 * r, f"r = {_d(rF)}", ha="center", va="bottom", fontsize=11,
                   color="#111827", zorder=7)
    tC = ax.text(0, -1.12 * r, "", ha="center", va="top", fontsize=11.5, color="#DC2626")
    hl, = ax.plot([], [], "--", color="#111827", lw=1.6, zorder=6)
    th = ax.text(0.06 * r, -0.5 * r, "", ha="left", va="center", fontsize=11.5, color="#111827",
                 zorder=7, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    tA = ax.text(0, 0.55 * r, "", ha="center", va="center", fontsize=13, color="#DC2626",
                 fontweight="bold", bbox=dict(boxstyle="round", fc="white", ec="#FCA5A5"))
    A = float(rF * rF) * math.pi
    C = float(2 * rF) * math.pi
    cl = [("A = π · r²", 0.06, 0.78, 124), (f"A = π · {_d(rF)}² = {_pi(rF * rF)}", 0.06, 0.48, 131),
          (f"A ≈ {_n(A)}{u2}", 0.06, 0.18, 138),
          (f"C = 2πr = {_pi(2 * rF)} ≈ {_n(C)}", 0.52, 0.78, 48),
          (("Halkalar → üçgen" if tr else "Rings → triangle"), 0.52, 0.48, 100),
          ("½ · 2πr · r = πr²", 0.52, 0.18, 116)]
    arts = []
    for s, x, y, t0 in cl:
        arts.append((bt.text(x, y, s, transform=bt.transAxes, fontsize=12.5, va="center",
                             color="#111827", alpha=0.0), t0))
    arts[2][0].set_color("#DC2626")
    arts[2][0].set_fontweight("bold")
    narr = [
        (f"1) Yarıçapı r = {_d(rF)} olan daire", f"1) A circle of radius r = {_d(rF)}"),
        (f"2) Çevre açılınca bir doğru parçası olur: C = 2πr = {_pi(2 * rF)} ≈ {_n(C)}",
         f"2) Unrolled, the circumference is a segment: C = 2πr = {_pi(2 * rF)} ≈ {_n(C)}"),
        ("3) Daire ince halkalara bölünür; her halka kesilip düzleştirilir",
         "3) Slice the disc into thin rings; cut each ring and straighten it"),
        ("4) Halkalar tabanı 2πr, yüksekliği r olan bir üçgen oluşturur",
         "4) The rings stack into a triangle with base 2πr and height r"),
        (f"5) A = ½ · 2πr · r = πr² = {_pi(rF * rF)} ≈ {_n(A)}{u2}",
         f"5) A = ½ · 2πr · r = πr² = {_pi(rF * rF)} ≈ {_n(A)}{u2}"),
    ]
    starts = [0, 18, 52, 100, 122]
    N = 155

    def update(i):
        a0 = 0.35 + 0.65 * _ph(i, 0, 12)
        t = _ease(_ph(i, 52, 98))
        for rin, rout, p in bands:
            xo, yo = _edge(rout, t)
            xi, yi = _edge(rin, t)
            pts = np.column_stack([np.concatenate([xo, xi[::-1]]),
                                   np.concatenate([yo - rout, yi[::-1] - rin])])
            p.set_xy(pts)
            p.set_alpha(a0)
        tc = _ease(_ph(i, 20, 46))
        if i >= 14:
            x, y = _edge(r, tc, 160)
            circ.set_data(x, y - r)
        else:
            circ.set_data([], [])
        vis = 1.0 - _ph(i, 50, 56)
        rad.set_alpha(vis * a0)
        cdot.set_alpha(vis * a0)
        trad.set_alpha(vis * a0)
        tC.set_text((f"C = 2πr = {_pi(2 * rF)} ≈ {_n(C)}" + ("  (taban)" if tr else "  (base)")
                     if i >= 100 else f"C = 2πr = {_pi(2 * rF)} ≈ {_n(C)}") if tc >= 1 else "")
        if i >= 102:
            hl.set_data([0, 0], [0, -r])
            th.set_text(f"h = r = {_d(rF)}")
        else:
            hl.set_data([], [])
            th.set_text("")
        tA.set_text(f"A = ½ · {_pi(2 * rF)} · {_d(rF)} = {_pi(rF * rF)} ≈ {_n(A)}" if i >= 122 else "")
        for art, t0 in arts:
            art.set_alpha(_ph(i, t0, t0 + 7))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    out = {k: v for k, v in P.items() if k not in ("r", "radius")}
    out["r"] = rnd.choice([2, 3, 4, 5, 6, 7, 8, 10, 12, 2.5, 1.5])
    return out
''',
}
EXAMPLES += [
    {"id": "geo-circle-1", "kind": "circle_area",
     "title": ("Dairenin alanı", "Area of a circle"),
     "q": ("Yarıçapı {r} birim olan dairenin alanını ve çevresini bul.",
           "Find the area and the circumference of a circle with radius {r}."),
     "P": {"r": 3}},
    {"id": "geo-circle-2", "kind": "circle_area", "topics": ["word problem", "sözel problem", "pizza"],
     "title": ("Pizzanın alanı (çaptan)", "Pizza area from the diameter"),
     "q": ("Çapı {d} cm olan bir pizzanın üst yüzeyinin alanı kaç cm²'dir? (Önce yarıçapı bul.)",
           "A pizza has a diameter of {d} cm. What is the area of its top? (Find the radius first.)"),
     "P": {"r": 15, "unit": "cm"}},
    {"id": "geo-circle-3", "kind": "circle_area", "topics": ["word problem", "sprinkler"],
     "title": ("Fıskiyenin suladığı alan", "Area watered by a sprinkler"),
     "q": ("Bir fıskiye çevresindeki {r} m'ye kadar her yeri suluyor. Sulanan dairesel alan kaç m²'dir?",
           "A rotating sprinkler waters everything up to {r} m away. What area does it water?"),
     "P": {"r": 2.5, "unit": "m"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["triangle_angles"] = {
    "course": "geo",
    "title": ("Üçgenin iç açıları toplamı", "Angle sum of a triangle"),
    "topics": ["angle sum", "triangle angle sum", "interior angles of a triangle", "angles in a triangle",
               "missing angle", "triangles", "180 degrees", "üçgenin iç açıları", "iç açılar toplamı",
               "açılar", "üçgende açı", "180 derece"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Polygon, Rectangle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _n(v, nd=2):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        s = str(int(round(v)))
    else:
        s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s.replace("-", "−")


def _layout(fig, wr=(1.35, 1.0)):
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=list(wr), left=0.02,
                          right=0.98, top=0.98, bottom=0.03, wspace=0.04, hspace=0.06)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left",
                    fontsize=11.5, color="#111827",
                    bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    return ax, tx, info


def _panel(tx, title, lines, fs=12.5, dy=0.105):
    tx.text(0.05, 0.96, title, transform=tx.transAxes, va="top", fontsize=11,
            color="#6B7280", fontweight="bold")
    out = []
    for k, s in enumerate(lines):
        out.append(tx.text(0.05, 0.86 - k * dy, s, transform=tx.transAxes, va="top",
                           fontsize=fs, color="#111827", alpha=0.0))
    if out:
        out[-1].set_color("#DC2626")
        out[-1].set_fontweight("bold")
    return out


def _kind(A, B, C):
    m = max(A, B, C)
    if abs(m - 90) < 1e-9:
        return ("dik üçgen", "a right triangle")
    if m > 90:
        return ("geniş açılı üçgen", "an obtuse triangle")
    return ("dar açılı üçgen", "an acute triangle")


def solve(P):
    A, B = float(P["A"]), float(P["B"])
    C = 180.0 - A - B
    if C <= 0 or A <= 0 or B <= 0:
        msg = ("Geçersiz: iki açının toplamı 180°'den küçük olmalı.",
               "Invalid: the two angles must add up to less than 180°.")
        return {"answer": msg, "steps": [msg, ("A + B + C = 180° ve her açı > 0°.",
                                                "A + B + C = 180° and every angle > 0°.")], "fmt": {}}
    kd = _kind(A, B, C)
    steps = [
        ("Üçgenin iç açıları toplamı 180°'dir: A + B + C = 180°",
         "The interior angles of a triangle add up to 180°: A + B + C = 180°"),
        (f"Yerine koy: {_n(A)}° + {_n(B)}° + C = 180°", f"Substitute: {_n(A)}° + {_n(B)}° + C = 180°"),
        (f"C = 180° − {_n(A)}° − {_n(B)}° = 180° − {_n(A + B)}° = {_n(C)}°",
         f"C = 180° − {_n(A)}° − {_n(B)}° = 180° − {_n(A + B)}° = {_n(C)}°"),
        (f"En büyük açı {_n(max(A, B, C))}° ⇒ {kd[0]}", f"Largest angle {_n(max(A, B, C))}° ⇒ {kd[1]}"),
        ("Neden 180°? Üç köşe koparılıp yan yana konunca bir doğru açı (düz açı) oluşturur.",
         "Why 180°? Tear off the three corners and line them up: together they make a straight angle."),
    ]
    return {"answer": f"C = {_n(C)}°", "steps": steps, "fmt": {"kind": kd}}


def _wedge(V, t1, t2, rho, n=32):
    t = np.radians(np.linspace(t1, t2, n))
    return np.vstack([[V[0], V[1]], np.column_stack([V[0] + rho * np.cos(t), V[1] + rho * np.sin(t)])])


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    A, B = float(P["A"]), float(P["B"])
    if A <= 0 or B <= 0 or A + B >= 179:
        A, B = 50.0, 60.0
    C = 180.0 - A - B
    L = 10.0
    ac = L * math.sin(math.radians(B)) / math.sin(math.radians(C))
    bc = L * math.sin(math.radians(A)) / math.sin(math.radians(C))
    Pa = np.array([0.0, 0.0])
    Pb = np.array([L, 0.0])
    Pc = np.array([ac * math.cos(math.radians(A)), ac * math.sin(math.radians(A))])
    rho = min(0.32 * min(L, ac, bc), 0.75 * Pc[1])
    Q = np.array([L / 2, -1.5 * rho])
    ax, tx, info = _layout(fig)
    ax.set_aspect("equal")
    ax.axis("off")
    xmin = min(0.0, Pc[0], Q[0] - 1.9 * rho)
    xmax = max(L, Pc[0], Q[0] + 2.4 * rho)
    W = xmax - xmin
    ax.set_xlim(xmin - 0.06 * W, xmax + 0.06 * W)
    ax.set_ylim(Q[1] - 0.45 * rho, Pc[1] + 0.1 * W)
    tri = Polygon([Pa, Pb, Pc], closed=True, fc="#EFF6FF", ec="#2563EB", lw=2.4, zorder=2)
    ax.add_patch(tri)
    cols = {"A": "#E07B39", "B": "#16A34A", "C": "#7C3AED"}
    src = {"A": (Pa, 0.0, A), "B": (Pb, 180.0 - B, 180.0), "C": (Pc, 180.0 + A, 360.0 - B)}
    tgt = {"A": B + C, "B": 0.0, "C": B}
    when = {"A": (28, 56), "B": (38, 66), "C": (48, 78)}
    ghosts, moving, labels, rot = {}, {}, {}, {}
    for key in ("A", "B", "C"):
        V, t1, t2 = src[key]
        g = Polygon(_wedge(V, t1, t2, rho), closed=True, fc=cols[key], ec="none", alpha=0.0, zorder=3)
        m = Polygon(_wedge(V, t1, t2, rho), closed=True, fc=cols[key], ec="white", lw=1.2, alpha=0.0,
                    zorder=5)
        ax.add_patch(g)
        ax.add_patch(m)
        ghosts[key] = g
        moving[key] = m
        labels[key] = ax.text(0, 0, "", ha="center", va="center", fontsize=11, color="white",
                              fontweight="bold", zorder=6)
        d = tgt[key] - t1
        while d > 180:
            d -= 360
        while d < -180:
            d += 360
        rot[key] = d
    line, = ax.plot([], [], color="#111827", lw=2, zorder=4)
    arc, = ax.plot([], [], "--", color="#DC2626", lw=1.5, zorder=4)
    t180 = ax.text(Q[0] + 1.62 * rho, Q[1], "", ha="left", va="center", fontsize=12, color="#DC2626",
                   fontweight="bold")
    off = 0.045 * W
    vA = ax.text(Pa[0] - off * 0.5, Pa[1] - off * 0.4, "A", ha="right", va="top", fontsize=13,
                 color="#111827", fontweight="bold")
    vB = ax.text(Pb[0] + off * 0.5, Pb[1] - off * 0.4, "B", ha="left", va="top", fontsize=13,
                 color="#111827", fontweight="bold")
    vC = ax.text(Pc[0], Pc[1] + off * 0.5, "C", ha="center", va="bottom", fontsize=13,
                 color="#111827", fontweight="bold")
    vals = {"A": f"{_n(A)}°", "B": f"{_n(B)}°", "C": "?"}
    kd = _kind(A, B, C)
    lines = ["A + B + C = 180°", f"{_n(A)}° + {_n(B)}° + C = 180°", f"C = 180° − {_n(A + B)}°",
             f"C = {_n(C)}°"]
    arts = _panel(tx, "Adım adım" if tr else "Step by step", lines, fs=12.5)
    times = [86, 100, 112, 124]
    narr = [
        (f"1) Üçgende A = {_n(A)}° ve B = {_n(B)}° veriliyor; C = ?",
         f"1) In the triangle A = {_n(A)}° and B = {_n(B)}°; C = ?"),
        ("2) Üç köşeyi (açıları) üçgenden koparalım", "2) Tear the three corners (angles) off the triangle"),
        ("3) Köşeleri bir doğru üzerinde yan yana dizelim", "3) Line the corners up side by side on a straight line"),
        ("4) Üç açı birlikte bir doğru açı oluşturur: A + B + C = 180°",
         "4) Together the three angles form a straight angle: A + B + C = 180°"),
        (f"5) C = 180° − {_n(A)}° − {_n(B)}° = {_n(C)}°  ({kd[0]})",
         f"5) C = 180° − {_n(A)}° − {_n(B)}° = {_n(C)}°  ({kd[1]})"),
    ]
    starts = [0, 14, 26, 82, 122]
    N = 145

    def update(i):
        tri.set_alpha(0.3 + 0.7 * _ph(i, 0, 10))
        hi = _ph(i, 12, 22)
        done = i >= 122
        for key in ("A", "B", "C"):
            V, t1, t2 = src[key]
            u = _ease(_ph(i, *when[key]))
            pos = V + u * (Q - V)
            d = u * rot[key]
            moving[key].set_xy(_wedge(pos, t1 + d, t2 + d, rho))
            moving[key].set_alpha(0.85 * hi)
            ghosts[key].set_alpha(0.18 if u > 0 else 0.0)
            mid = math.radians((t1 + t2) / 2 + d)
            wide = (t2 - t1) >= 42
            lr = 0.6 if wide else 1.4
            labels[key].set_position((pos[0] + lr * rho * math.cos(mid), pos[1] + lr * rho * math.sin(mid)))
            txt = vals[key] if key != "C" else (f"{_n(C)}°" if done else "?")
            labels[key].set_text(txt if hi > 0.5 else "")
            labels[key].set_color("white" if wide else cols[key])
        vC.set_text(f"C = {_n(C)}°" if done else "C")
        vC.set_color("#DC2626" if done else "#111827")
        s = _ph(i, 80, 90)
        if s > 0:
            line.set_data([Q[0] - 1.55 * rho, Q[0] + 1.55 * rho], [Q[1], Q[1]])
            tt = np.linspace(0, math.pi * s, 60)
            arc.set_data(Q[0] + 1.08 * rho * np.cos(tt), Q[1] + 1.08 * rho * np.sin(tt))
        else:
            line.set_data([], [])
            arc.set_data([], [])
        t180.set_text("180°" if s >= 1 else "")
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 8))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    if float(P["B"]) == 90:
        out["A"] = rnd.choice([v for v in range(20, 71, 5) if v != P["A"]])
        return out
    if P["A"] == P["B"]:
        A = rnd.choice([v for v in (25, 28, 30, 35, 40, 50, 55, 62, 65, 70, 75) if v != P["A"]])
        out.update({"A": A, "B": A})
        return out
    while True:
        A = rnd.randrange(25, 100, 5)
        B = rnd.randrange(25, 100, 5)
        if 25 <= 180 - A - B <= 120 and B != 90:
            out.update({"A": A, "B": B})
            return out
''',
}
EXAMPLES += [
    {"id": "geo-tri-ang-1", "kind": "triangle_angles",
     "title": ("Üçüncü açıyı bulma", "Finding the third angle"),
     "q": ("Bir üçgende A = {A}° ve B = {B}°'dir. C açısı kaç derecedir?",
           "In a triangle A = {A}° and B = {B}°. Find angle C."),
     "P": {"A": 50, "B": 60}},
    {"id": "geo-tri-ang-2", "kind": "triangle_angles", "topics": ["right triangle", "dik üçgen"],
     "title": ("Dik üçgende dar açı", "Acute angle of a right triangle"),
     "q": ("Bir dik üçgende dik açı B = {B}° ve A = {A}°. Diğer dar açı C kaçtır?",
           "In a right triangle the right angle is B = {B}° and A = {A}°. Find the other acute angle C."),
     "P": {"A": 35, "B": 90}},
    {"id": "geo-tri-ang-3", "kind": "triangle_angles",
     "topics": ["isosceles", "ikizkenar", "word problem", "sözel problem"],
     "title": ("İkizkenar çatı makası", "Isosceles roof truss"),
     "q": ("İkizkenar üçgen biçimli bir çatı makasında taban açılarının her biri {A}°. "
           "Tepe açısı kaç derecedir? Üçgen ne tür bir üçgendir?",
           "An isosceles roof truss has base angles of {A}° each. What is the apex angle, "
           "and what kind of triangle is it?"),
     "P": {"A": 32, "B": 32}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["polygon_angles"] = {
    "course": "geo",
    "title": ("Çokgenin iç ve dış açıları", "Interior and exterior angles of a polygon"),
    "topics": ["polygon", "polygons", "interior angles", "exterior angles", "angle sum",
               "regular polygon", "sum of interior angles", "pentagon", "hexagon", "octagon",
               "çokgen", "çokgenler", "iç açılar", "dış açılar", "düzgün çokgen", "iç açılar toplamı"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Polygon, Rectangle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _layout(fig, wr=(1.35, 1.0)):
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=list(wr), left=0.02,
                          right=0.98, top=0.98, bottom=0.03, wspace=0.04, hspace=0.06)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left",
                    fontsize=11.5, color="#111827",
                    bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    return ax, tx, info


def _panel(tx, title, lines, fs=12.5, dy=0.105):
    tx.text(0.05, 0.96, title, transform=tx.transAxes, va="top", fontsize=11,
            color="#6B7280", fontweight="bold")
    out = []
    for k, s in enumerate(lines):
        out.append(tx.text(0.05, 0.86 - k * dy, s, transform=tx.transAxes, va="top",
                           fontsize=fs, color="#111827", alpha=0.0))
    return out


_NAMES = {3: ("üçgen", "triangle"), 4: ("dörtgen", "quadrilateral"), 5: ("beşgen", "pentagon"),
          6: ("altıgen", "hexagon"), 7: ("yedigen", "heptagon"), 8: ("sekizgen", "octagon"),
          9: ("dokuzgen", "nonagon"), 10: ("ongen", "decagon"), 11: ("onbirgen", "hendecagon"),
          12: ("onikigen", "dodecagon")}


def _deg(fr):
    fr = Fraction(fr)
    if fr.denominator == 1:
        return f"{fr.numerator}°"
    v = f"{float(fr):.2f}".rstrip("0").rstrip(".")
    return f"{fr.numerator}°/{fr.denominator} ≈ {v}°"


def _short(fr):
    fr = Fraction(fr)
    if fr.denominator == 1:
        return f"{fr.numerator}°"
    return f"{float(fr):.1f}°"


def _name(n):
    return _NAMES.get(n, (f"{n}-gen", f"{n}-gon"))


def solve(P):
    n = int(P["n"])
    if n < 3:
        msg = ("Çokgenin en az 3 kenarı olmalı.", "A polygon needs at least 3 sides.")
        return {"answer": msg, "steps": [msg, msg], "fmt": {"name": ("çokgen", "polygon")}}
    S = (n - 2) * 180
    each = Fraction(S, n)
    ext = Fraction(360, n)
    nm = _name(n)
    steps = [
        (f"Bir köşeden çizilen {n - 3} köşegen, {n} kenarlı çokgeni n − 2 = {n - 2} üçgene böler.",
         f"The {n - 3} diagonals from one vertex split the {n}-sided polygon into n − 2 = {n - 2} triangles."),
        (f"Her üçgen 180° ⇒ iç açılar toplamı = (n − 2) · 180° = {n - 2} · 180° = {S}°",
         f"Each triangle is 180° ⇒ interior angle sum = (n − 2) · 180° = {n - 2} · 180° = {S}°"),
        (f"Düzgün {nm[0]}de tüm iç açılar eşit: {S}° / {n} = {_deg(each)}",
         f"In a regular {nm[1]} all interior angles are equal: {S}° / {n} = {_deg(each)}"),
        (f"Dış açılar toplamı her zaman 360° ⇒ her dış açı = 360° / {n} = {_deg(ext)}",
         f"Exterior angles always total 360° ⇒ each exterior angle = 360° / {n} = {_deg(ext)}"),
        (f"Kontrol: iç açı + dış açı = {_short(each)} + {_short(ext)} = 180° ✓",
         f"Check: interior + exterior = {_short(each)} + {_short(ext)} = 180° ✓"),
    ]
    fit = Fraction(360) / each
    if fit.denominator == 1:
        steps.append((f"Döşeme: 360° / {_short(each)} = {fit.numerator} ⇒ bir köşede {fit.numerator} tane "
                      f"{nm[0]} boşluksuz birleşir.",
                      f"Tiling: 360° / {_short(each)} = {fit.numerator} ⇒ {fit.numerator} {nm[1]}s meet at a "
                      "corner with no gap."))
    else:
        steps.append((f"Döşeme: 360° / {_short(each)} ≈ {float(fit):.2f} tam sayı değil ⇒ tek başına "
                      "boşluksuz döşenemez.",
                      f"Tiling: 360° / {_short(each)} ≈ {float(fit):.2f} is not a whole number ⇒ it cannot "
                      "tile a floor on its own."))
    ans = (f"Toplam {S}°, her iç açı {_deg(each)}, her dış açı {_deg(ext)}",
           f"Sum {S}°, each interior angle {_deg(each)}, each exterior angle {_deg(ext)}")
    return {"answer": ans, "steps": steps, "fmt": {"name": nm, "S": str(S)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    n = max(3, min(16, int(P["n"])))
    S = (n - 2) * 180
    each = Fraction(S, n)
    ext = Fraction(360, n)
    nm = _name(n)
    ax, tx, info = _layout(fig)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.38, 1.36)
    th0 = -90.0 - 180.0 / n
    ang = np.radians(th0 + 360.0 * np.arange(n) / n)
    V = np.column_stack([np.cos(ang), np.sin(ang)])
    loop = np.vstack([V, V[:1]])
    seg = np.hypot(np.diff(loop[:, 0]), np.diff(loop[:, 1]))
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    fills = ["#DBEAFE", "#FED7AA", "#BBF7D0", "#E9D5FF"]
    tris, tlabs, diags = [], [], []
    fs = 11 if n <= 6 else (9.5 if n <= 9 else 8)
    for j in range(n - 2):
        T = np.array([V[0], V[j + 1], V[j + 2]])
        p = Polygon(T, closed=True, fc=fills[j % 4], ec="none", alpha=0.0, zorder=1)
        ax.add_patch(p)
        tris.append(p)
        g = T.mean(axis=0)
        tlabs.append(ax.text(g[0], g[1], "", ha="center", va="center", fontsize=fs, color="#374151"))
    for j in range(2, n - 1):
        d, = ax.plot([], [], "--", color="#7C3AED", lw=1.4, zorder=2)
        diags.append((j, d))
    edge, = ax.plot([], [], color="#2563EB", lw=2.6, zorder=4)
    dots, = ax.plot([], [], "o", color="#2563EB", ms=5, zorder=5)
    iarcs, ilabs, earcs, elabs, exts = [], [], [], [], []
    inner = 180.0 - 360.0 / n
    for k in range(n):
        P0 = V[k]
        nxt = V[(k + 1) % n] - P0
        prv = P0 - V[k - 1]
        a1 = math.atan2(nxt[1], nxt[0])
        ain = math.atan2(prv[1], prv[0])
        tt = np.linspace(a1, a1 + math.radians(inner), 30)
        rr = 0.17 if n <= 8 else 0.13
        ia, = ax.plot(P0[0] + rr * np.cos(tt), P0[1] + rr * np.sin(tt), color="#DC2626", lw=2, alpha=0.0,
                      zorder=6)
        iarcs.append(ia)
        mid = a1 + math.radians(inner) / 2
        ilabs.append(ax.text(P0[0] + 0.33 * math.cos(mid), P0[1] + 0.33 * math.sin(mid), "",
                             ha="center", va="center", fontsize=fs, color="#DC2626", zorder=7))
        ex, = ax.plot([P0[0], P0[0] + 0.36 * math.cos(ain)], [P0[1], P0[1] + 0.36 * math.sin(ain)], ":",
                      color="#6B7280", lw=1.4, alpha=0.0, zorder=3)
        exts.append(ex)
        te = np.linspace(ain, ain + math.radians(360.0 / n), 20)
        ea, = ax.plot(P0[0] + 0.2 * np.cos(te), P0[1] + 0.2 * np.sin(te), color="#16A34A", lw=2,
                      alpha=0.0, zorder=6)
        earcs.append(ea)
        me = ain + math.radians(180.0 / n)
        elabs.append(ax.text(P0[0] + 0.34 * math.cos(me), P0[1] + 0.34 * math.sin(me), "",
                             ha="center", va="center", fontsize=fs - 0.5, color="#15803D", zorder=7))
    lines = [(f"n = {n} ⇒ {n} − 2 = {n - 2} üçgen" if tr else f"n = {n} ⇒ {n} − 2 = {n - 2} triangles"),
             ("Toplam = (n − 2) · 180°" if tr else "Sum = (n − 2) · 180°"),
             f"= {n - 2} · 180° = {S}°",
             (f"İç açı = {S}°/{n} = {_short(each)}" if tr else f"Interior = {S}°/{n} = {_short(each)}"),
             (f"Dış açı = 360°/{n} = {_short(ext)}" if tr else f"Exterior = 360°/{n} = {_short(ext)}")]
    arts = _panel(tx, "Adım adım" if tr else "Step by step", lines, fs=12)
    arts[2].set_color("#2563EB")
    arts[3].set_color("#DC2626")
    arts[4].set_color("#15803D")
    for t in arts[2:]:
        t.set_fontweight("bold")
    times = [24, 72, 80, 92, 116]
    narr = [
        (f"1) Düzgün {nm[0]}: {n} eş kenar, {n} eş açı", f"1) Regular {nm[1]}: {n} equal sides, {n} equal angles"),
        (f"2) Bir köşeden köşegenler: çokgen n − 2 = {n - 2} üçgene bölünür",
         f"2) Diagonals from one vertex split it into n − 2 = {n - 2} triangles"),
        (f"3) Her üçgen 180° ⇒ iç açılar toplamı = {n - 2} · 180° = {S}°",
         f"3) Each triangle gives 180° ⇒ interior sum = {n - 2} · 180° = {S}°"),
        (f"4) Açılar eşit: her iç açı = {S}° / {n} = {_short(each)}",
         f"4) Equal angles: each interior angle = {S}° / {n} = {_short(each)}"),
        (f"5) Dış açı = 180° − {_short(each)} = {_short(ext)}; dış açılar toplamı 360°",
         f"5) Exterior angle = 180° − {_short(each)} = {_short(ext)}; exterior angles total 360°"),
        (f"Sonuç: toplam {S}° · iç açı {_short(each)} · dış açı {_short(ext)}",
         f"Result: sum {S}° · interior {_short(each)} · exterior {_short(ext)}"),
    ]
    starts = [0, 18, 70, 90, 114, 140]
    N = 160

    def update(i):
        p = (0.12 + 0.88 * _ph(i, 0, 16)) * cum[-1]
        m = int(np.searchsorted(cum, p, side="right"))
        if m >= len(cum):
            edge.set_data(loop[:, 0], loop[:, 1])
        else:
            f = (p - cum[m - 1]) / seg[m - 1] if m > 0 else 0.0
            tip = loop[m - 1] + f * (loop[m] - loop[m - 1])
            pts = np.vstack([loop[:m], tip])
            edge.set_data(pts[:, 0], pts[:, 1])
        dots.set_data(V[:, 0], V[:, 1]) if i >= 16 else dots.set_data([], [])
        dur = 50.0 / (n - 2)
        late = _ph(i, 112, 124)
        for j, (tp, tl) in enumerate(zip(tris, tlabs)):
            a = _ph(i, 18 + j * dur, 18 + j * dur + min(8.0, dur))
            tp.set_alpha(0.9 * a * (1 - 0.6 * late))
            tl.set_text("180°" if a > 0.5 and late < 0.5 else "")
        for j, d in diags:
            a = _ph(i, 18 + (j - 1) * dur, 18 + (j - 1) * dur + min(8.0, dur))
            if a > 0:
                d.set_data([V[0][0], V[0][0] + a * (V[j][0] - V[0][0])],
                           [V[0][1], V[0][1] + a * (V[j][1] - V[0][1])])
            else:
                d.set_data([], [])
        q = _ph(i, 90, 102)
        for ia, il in zip(iarcs, ilabs):
            ia.set_alpha(q)
            il.set_text(_short(each) if q > 0.5 else "")
        e = _ph(i, 114, 126)
        for ea, el, ex in zip(earcs, elabs, exts):
            ea.set_alpha(e)
            ex.set_alpha(e)
            el.set_text(_short(ext) if e > 0.5 else "")
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 8))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    out["n"] = rnd.choice([v for v in (5, 6, 8, 9, 10, 12) if v != P.get("n")])
    return out
''',
}
EXAMPLES += [
    {"id": "geo-poly-1", "kind": "polygon_angles",
     "title": ("Düzgün beşgenin açıları", "Angles of a regular pentagon"),
     "q": ("Düzgün bir {name}in iç açıları toplamını, bir iç açısını ve bir dış açısını bul.",
           "Find the interior angle sum, one interior angle and one exterior angle of a regular {name}."),
     "P": {"n": 5}},
    {"id": "geo-poly-2", "kind": "polygon_angles", "topics": ["stop sign", "word problem", "sözel problem"],
     "title": ("Dur levhası (sekizgen)", "Stop sign (octagon)"),
     "q": ("Bir trafik levhası düzgün {name} biçimindedir. Köşelerindeki iç açılar kaçar derecedir? "
           "Tüm iç açıların toplamı nedir?",
           "A road sign has the shape of a regular {name}. How large is each corner (interior) angle, "
           "and what is the sum of all interior angles?"),
     "P": {"n": 8}},
    {"id": "geo-poly-3", "kind": "polygon_angles", "topics": ["tessellation", "tiling", "döşeme"],
     "title": ("Altıgen fayanslar", "Hexagonal tiles"),
     "q": ("Bir zemin düzgün {name} biçimli fayanslarla döşenecek. Bir iç açı kaç derecedir? "
           "Bir köşede fayanslar boşluksuz birleşebilir mi?",
           "A floor is to be covered with tiles shaped like a regular {name}. How big is each interior "
           "angle? Can the tiles meet at a corner without gaps?"),
     "P": {"n": 6}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["similar_triangles"] = {
    "course": "geo",
    "title": ("Benzer üçgenler", "Similar triangles"),
    "topics": ["similar triangles", "similarity", "scale factor", "proportional sides",
               "corresponding sides", "shadow problem", "indirect measurement", "dilation",
               "benzer üçgenler", "benzerlik", "benzerlik oranı", "orantı", "gölge problemi"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Polygon, Rectangle, Circle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _d(v):
    v = Fraction(v).limit_denominator(10000)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        s = f"{float(v):.4f}".rstrip("0").rstrip(".")
    return s.replace("-", "−")


def _F(v):
    return Fraction(str(v))


def _layout(fig, wr=(1.35, 1.0)):
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=list(wr), left=0.02,
                          right=0.98, top=0.98, bottom=0.03, wspace=0.04, hspace=0.06)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left",
                    fontsize=11.5, color="#111827",
                    bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    return ax, tx, info


def _panel(tx, title, lines, fs=12.5, dy=0.105):
    tx.text(0.05, 0.96, title, transform=tx.transAxes, va="top", fontsize=11,
            color="#6B7280", fontweight="bold")
    out = []
    for k, s in enumerate(lines):
        out.append(tx.text(0.05, 0.86 - k * dy, s, transform=tx.transAxes, va="top",
                           fontsize=fs, color="#111827", alpha=0.0))
    return out


def _shadow(P):
    return P.get("scene") == "shadow"


def solve(P):
    a, b, k = _F(P["a"]), _F(P["b"]), _F(P["k"])
    unit = P.get("unit", "m" if _shadow(P) else "")
    us = f" {unit}" if unit else ""
    if _shadow(P):
        S2, H = k * b, k * a
        steps = [
            ("Güneş ışınları paralel geldiğinden kişi–gölge ve ağaç–gölge dik üçgenleri benzerdir (AA).",
             "Sun rays are parallel, so the person–shadow and tree–shadow right triangles are similar (AA)."),
            ("Boy / gölge oranı iki üçgende aynıdır: h / (ağacın gölgesi) = (kişinin boyu) / (kişinin gölgesi)",
             "Height / shadow is the same in both: h / (tree's shadow) = (person's height) / (person's shadow)"),
            (f"h / {_d(S2)} = {_d(a)} / {_d(b)}", f"h / {_d(S2)} = {_d(a)} / {_d(b)}"),
            (f"Benzerlik oranı k = {_d(S2)} / {_d(b)} = {_d(k)}",
             f"Scale factor k = {_d(S2)} / {_d(b)} = {_d(k)}"),
            (f"h = k · {_d(a)} = {_d(k)} · {_d(a)} = {_d(H)}{us}", f"h = k · {_d(a)} = {_d(k)} · {_d(a)} = {_d(H)}{us}"),
        ]
        return {"answer": (f"Ağacın boyu h = {_d(H)}{us}", f"The tree is h = {_d(H)}{us} tall"),
                "steps": steps, "fmt": {"S": _d(S2), "H": _d(H)}}
    c = _F(P["c"])
    sides = {"a": a, "b": b, "c": c}
    if not (a + b > c and a + c > b and b + c > a):
        msg = ("Bu kenarlarla üçgen oluşmaz (üçgen eşitsizliği).", "These sides do not form a triangle.")
        return {"answer": msg, "steps": [msg, msg], "fmt": {"g": "a", "gv": "?", "gk": "?"}}
    g = P.get("given", "a")
    new = {s: k * v for s, v in sides.items()}
    others = [s for s in ("a", "b", "c") if s != g]
    steps = [
        ("Benzer üçgenlerde karşılık gelen kenarlar orantılıdır: a'/a = b'/b = c'/c = k",
         "In similar triangles corresponding sides are proportional: a'/a = b'/b = c'/c = k"),
        (f"Verilen: {g}' = {_d(new[g])}, {g} = {_d(sides[g])}  ⇒  k = {_d(new[g])} / {_d(sides[g])} = {_d(k)}",
         f"Given: {g}' = {_d(new[g])}, {g} = {_d(sides[g])}  ⇒  k = {_d(new[g])} / {_d(sides[g])} = {_d(k)}"),
    ]
    for s in others:
        steps.append((f"{s}' = k · {s} = {_d(k)} · {_d(sides[s])} = {_d(new[s])}{us}",
                      f"{s}' = k · {s} = {_d(k)} · {_d(sides[s])} = {_d(new[s])}{us}"))
    steps.append((f"Açılar değişmez; çevreler oranı k = {_d(k)}, alanlar oranı k² = {_d(k * k)}",
                  f"Angles stay the same; perimeter ratio k = {_d(k)}, area ratio k² = {_d(k * k)}"))
    ans = ", ".join(f"{s}' = {_d(new[s])}{us}" for s in others) + f"  (k = {_d(k)})"
    return {"answer": ans, "steps": steps,
            "fmt": {"g": g, "gv": _d(new[g]), "gk": _d(sides[g])}}


def _outside(T, j0, j1, dist):
    m = (T[j0] + T[j1]) / 2
    g = T.mean(axis=0)
    d = m - g
    return m + dist * d / (np.hypot(d[0], d[1]) + 1e-12)


def _build_shadow(fig, P, tr):
    a, b, k = float(P["a"]), float(P["b"]), float(P["k"])
    aF, bF, kF = _F(P["a"]), _F(P["b"]), _F(P["k"])
    unit = P.get("unit", "m")
    us = f" {unit}" if unit else ""
    H, S2 = k * a, k * b
    X2 = b + max(1.2 * b, 0.4 * H)
    W0 = X2 + S2
    ax, tx, info = _layout(fig)
    ax.set_aspect("equal")
    ax.axis("off")
    x0 = -0.22 * W0
    ax.set_xlim(x0, W0 + 0.06 * W0)
    ax.set_ylim(-0.12 * max(H, 0.4 * W0), 1.2 * H)
    ax.plot([x0, W0 * 1.06], [0, 0], color="#78716C", lw=2.2, zorder=1)
    sun = Circle((x0 + 0.1 * W0, 1.08 * H), 0.05 * W0, fc="#FDE047", ec="#E07B39", lw=1.5, alpha=0.0, zorder=2)
    ax.add_patch(sun)
    t1 = Polygon([(0, 0), (b, 0), (0, a)], closed=True, fc="#BFDBFE", ec="#2563EB", lw=1.6, alpha=0.0, zorder=2)
    cp = Polygon([(0, 0), (b, 0), (0, a)], closed=True, fc="#FED7AA", ec="#E07B39", lw=1.8, alpha=0.0, zorder=2)
    ax.add_patch(t1)
    ax.add_patch(cp)
    person = []
    for xs, ys in (([0, 0], [0.42 * a, 0.8 * a]), ([-0.12 * a, 0, 0.12 * a], [0, 0.42 * a, 0]),
                   ([-0.15 * a, 0, 0.15 * a], [0.52 * a, 0.72 * a, 0.52 * a])):
        ln, = ax.plot(xs, ys, color="#111827", lw=2, alpha=0.0, zorder=4)
        person.append(ln)
    head = Circle((0, 0.9 * a), 0.1 * a, fc="#111827", ec="none", alpha=0.0, zorder=4)
    ax.add_patch(head)
    sh1, = ax.plot([], [], color="#374151", lw=5, alpha=0.6, solid_capstyle="butt", zorder=3)
    sh2, = ax.plot([], [], color="#374151", lw=5, alpha=0.6, solid_capstyle="butt", zorder=3)
    ray1, = ax.plot([], [], "--", color="#E07B39", lw=1.6, zorder=3)
    ray2, = ax.plot([], [], "--", color="#E07B39", lw=1.6, zorder=3)
    trunk, = ax.plot([], [], color="#92400E", lw=6, solid_capstyle="butt", zorder=3)
    crown = Circle((X2, 0), 0.01, fc="#16A34A", ec="#166534", alpha=0.0, zorder=3)
    ax.add_patch(crown)
    dim, = ax.plot([], [], color="#DC2626", lw=1.4, zorder=5)
    fs = 11
    tpa = ax.text(-0.04 * W0, a / 2, f"{_d(aF)}{us}", ha="right", va="center", fontsize=fs, color="#1E3A8A")
    tps = ax.text(b / 2, -0.03 * W0, f"{_d(bF)}{us}", ha="center", va="top", fontsize=fs, color="#1E3A8A")
    tts = ax.text(X2 + S2 / 2, -0.03 * W0, f"{_d(kF * bF)}{us}", ha="center", va="top", fontsize=fs,
                  color="#9A3412")
    dx = X2 - 0.36 * H
    tth = ax.text(dx - 0.02 * W0, H / 2, "", ha="right", va="center", fontsize=12, color="#DC2626",
                  fontweight="bold")
    tk = ax.text(0, 0, "", ha="center", va="bottom", fontsize=12, color="#9A3412", fontweight="bold")
    lam = 0.55 * W0 / math.hypot(b, a)
    lines = [("Işınlar paralel ⇒ benzer" if tr else "Parallel rays ⇒ similar"),
             f"h / {_d(kF * bF)} = {_d(aF)} / {_d(bF)}",
             f"k = {_d(kF * bF)} / {_d(bF)} = {_d(kF)}",
             f"h = {_d(kF)} · {_d(aF)}",
             f"h = {_d(kF * aF)}{us}"]
    arts = _panel(tx, "Adım adım" if tr else "Step by step", lines, fs=12.5)
    arts[-1].set_color("#DC2626")
    arts[-1].set_fontweight("bold")
    times = [22, 48, 60, 100, 122]
    narr = [
        (f"1) Boyu {_d(aF)}{us} olan kişinin gölgesi {_d(bF)}{us}",
         f"1) A person {_d(aF)}{us} tall casts a {_d(bF)}{us} shadow"),
        ("2) Güneş ışını kişinin başından gölgenin ucuna: bir dik üçgen", "2) A sun ray from the head to the shadow tip: a right triangle"),
        (f"3) Aynı anda ağacın gölgesi {_d(kF * bF)}{us}; ağacın boyu h = ?",
         f"3) At the same time the tree's shadow is {_d(kF * bF)}{us}; tree height h = ?"),
        (f"4) Işınlar paralel ⇒ üçgenler benzer; k = {_d(kF * bF)} / {_d(bF)} = {_d(kF)} kat büyütülür",
         f"4) Parallel rays ⇒ similar triangles; scale by k = {_d(kF * bF)} / {_d(bF)} = {_d(kF)}"),
        (f"5) h = k · {_d(aF)} = {_d(kF)} · {_d(aF)} = {_d(kF * aF)}{us}",
         f"5) h = k · {_d(aF)} = {_d(kF)} · {_d(aF)} = {_d(kF * aF)}{us}"),
    ]
    starts = [0, 16, 36, 52, 98]
    V0 = np.array([[0.0, 0.0], [b, 0.0], [0.0, a]])
    N = 150

    def update(i):
        a0 = 0.3 + 0.7 * _ph(i, 0, 10)
        sun.set_alpha(a0)
        head.set_alpha(a0)
        for ln in person:
            ln.set_alpha(a0)
        sh1.set_data([0, b], [0, 0])
        r1 = _ph(i, 16, 30)
        if r1 > 0:
            st = np.array([0.0, a]) - lam * np.array([b, -a]) * r1
            ray1.set_data([st[0], b], [st[1], 0])
        else:
            ray1.set_data([], [])
        t1.set_alpha(0.55 * _ph(i, 24, 34))
        s2 = _ph(i, 36, 48)
        sh2.set_data([X2, X2 + S2 * s2], [0, 0]) if s2 > 0 else sh2.set_data([], [])
        tts.set_alpha(1.0 if s2 >= 1 else 0.0)
        u = _ease(_ph(i, 52, 92))
        if u > 0:
            f = 1 + (k - 1) * u
            pts = V0 * f + np.array([u * X2, 0.0])
            cp.set_xy(pts)
            cp.set_alpha(0.5)
            tk.set_position((pts[0][0] + 0.25 * f * b, f * a * 0.35))
            tk.set_text(f"× {f:.2f}" if u < 1 else f"× {_d(kF)}")
        else:
            cp.set_alpha(0.0)
            tk.set_text("")
        g = _ease(_ph(i, 96, 118))
        if g > 0:
            trunk.set_data([X2, X2], [0, 0.45 * H * g])
            crown.set_center((X2, 0.72 * H * g))
            crown.set_radius(0.28 * H * g)
            crown.set_alpha(0.85)
            ray2.set_data([X2 - lam * b * g, X2 + S2], [H + lam * a * g, 0])
            dim.set_data([dx, dx], [0, H * g])
        else:
            trunk.set_data([], [])
            crown.set_alpha(0.0)
            ray2.set_data([], [])
            dim.set_data([], [])
        tth.set_text(("h = ?" if i < 118 else f"h = {_d(kF * aF)}{us}") if i >= 40 else "")
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 8))
        kk = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[kk][0 if tr else 1])
        return []

    return N, update


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    if _shadow(P):
        return _build_shadow(fig, P, tr)
    aF, bF, cF, kF = _F(P["a"]), _F(P["b"]), _F(P["c"]), _F(P["k"])
    a, b, c, k = float(aF), float(bF), float(cF), float(kF)
    if not (a + b > c and a + c > b and b + c > a):
        a, b, c = 4.0, 5.0, 6.0
    g = P.get("given", "a")
    unit = P.get("unit", "")
    us = f" {unit}" if unit else ""
    Cx = (b * b + c * c - a * a) / (2 * c)
    Cy = math.sqrt(max(b * b - Cx * Cx, 1e-9))
    T1 = np.array([[0.0, 0.0], [c, 0.0], [Cx, Cy]])
    x1min, x1max = min(0.0, Cx), max(c, Cx)
    gap = 0.22 * (x1max - x1min) * max(1.0, k)
    X2 = x1max + gap - k * x1min
    xr = X2 + k * x1max
    H = max(Cy, k * Cy)
    W = xr - x1min
    ax, tx, info = _layout(fig, (1.6, 1.0))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(x1min - 0.07 * W, xr + 0.07 * W)
    ax.set_ylim(-0.13 * W, H + 0.12 * W)
    p1 = Polygon(T1, closed=True, fc="#DBEAFE", ec="#2563EB", lw=2.2, zorder=2)
    p2 = Polygon(T1, closed=True, fc="#FFEDD5", ec="#E07B39", lw=2.2, alpha=0.0, zorder=3)
    ax.add_patch(p1)
    ax.add_patch(p2)
    hl, = ax.plot([], [], color="#DC2626", lw=4.5, zorder=4)
    acol = ["#DC2626", "#16A34A", "#7C3AED"]
    rr = 0.16 * min(a, b, c)
    arcs1, arcs2 = [], []
    for j in range(3):
        l1, = ax.plot([], [], color=acol[j], lw=2, zorder=5)
        l2, = ax.plot([], [], color=acol[j], lw=2, zorder=5)
        arcs1.append(l1)
        arcs2.append(l2)
    sidx = {"a": (1, 2), "b": (2, 0), "c": (0, 1)}
    vals = {"a": aF, "b": bF, "c": cF}
    fs = 11
    lab1, lab2 = {}, {}
    for s in ("a", "b", "c"):
        pos = _outside(T1, sidx[s][0], sidx[s][1], 0.06 * W)
        lab1[s] = ax.text(pos[0], pos[1], f"{s} = {_d(vals[s])}", ha="center", va="center", fontsize=fs,
                          color="#1E3A8A", zorder=6)
        lab2[s] = ax.text(0, 0, "", ha="center", va="center", fontsize=fs, color="#9A3412", zorder=6)
    tk = ax.text(0, 0, "", ha="center", va="bottom", fontsize=12, color="#9A3412", fontweight="bold")
    others = [s for s in ("a", "b", "c") if s != g]
    lines = ["a'/a = b'/b = c'/c = k",
             f"k = {_d(kF * vals[g])} / {_d(vals[g])} = {_d(kF)}"]
    for s in others:
        lines.append(f"{s}' = {_d(kF)} · {_d(vals[s])} = {_d(kF * vals[s])}")
    lines.append((f"Alan oranı k² = {_d(kF * kF)}" if tr else f"Area ratio k² = {_d(kF * kF)}"))
    arts = _panel(tx, "Adım adım" if tr else "Step by step", lines, fs=12)
    for t in arts[2:4]:
        t.set_color("#DC2626")
        t.set_fontweight("bold")
    times = [76, 96, 112, 124, 134]
    narr = [
        (f"1) △ABC: a = {_d(aF)}, b = {_d(bF)}, c = {_d(cF)}", f"1) △ABC: a = {_d(aF)}, b = {_d(bF)}, c = {_d(cF)}"),
        ("2) Benzer üçgen: aynı şekil, her kenar aynı k katı", "2) A similar triangle: same shape, every side times the same k"),
        ("3) Karşılık gelen açılar eşit (aynı renk), kenarlar orantılı",
         "3) Corresponding angles are equal (same colour), sides are proportional"),
        (f"4) Verilen {g}' = {_d(kF * vals[g])}  ⇒  k = {_d(kF * vals[g])} / {_d(vals[g])} = {_d(kF)}",
         f"4) Given {g}' = {_d(kF * vals[g])}  ⇒  k = {_d(kF * vals[g])} / {_d(vals[g])} = {_d(kF)}"),
        ("5) Diğer kenarlar: " + ", ".join(f"{s}' = {_d(kF * vals[s])}" for s in others) + us,
         "5) Other sides: " + ", ".join(f"{s}' = {_d(kF * vals[s])}" for s in others) + us),
    ]
    starts = [0, 18, 72, 92, 110]
    N = 150

    def arc_pts(T, j, r):
        V = T[j]
        u1 = T[(j + 1) % 3] - V
        u2 = T[(j + 2) % 3] - V
        t1 = math.atan2(u1[1], u1[0])
        t2 = math.atan2(u2[1], u2[0])
        d = (t2 - t1 + math.pi) % (2 * math.pi) - math.pi
        tt = np.linspace(t1, t1 + d, 24)
        return V[0] + r * np.cos(tt), V[1] + r * np.sin(tt)

    def update(i):
        p1.set_alpha(0.3 + 0.7 * _ph(i, 0, 10))
        u = _ease(_ph(i, 22, 68))
        f = 1 + (k - 1) * u
        T2 = T1 * f + np.array([u * X2, 0.0])
        p2.set_xy(T2)
        p2.set_alpha(0.0 if i < 20 else 0.9)
        if 20 <= i:
            tk.set_position(((T2[0][0] + T2[1][0]) / 2, max(T2[:, 1]) + 0.02 * W))
            tk.set_text(f"× {f:.2f}" if u < 1 else f"k = {_d(kF)}")
        else:
            tk.set_text("")
        q = _ph(i, 72, 84)
        for j in range(3):
            x, y = arc_pts(T1, j, rr)
            arcs1[j].set_data(x, y) if q > 0 else arcs1[j].set_data([], [])
            x, y = arc_pts(T2, j, rr * f)
            arcs2[j].set_data(x, y) if q > 0 else arcs2[j].set_data([], [])
            arcs1[j].set_alpha(q)
            arcs2[j].set_alpha(q)
        for s in ("a", "b", "c"):
            pos = _outside(T2, sidx[s][0], sidx[s][1], 0.06 * W)
            lab2[s].set_position((pos[0], pos[1]))
            if i < 70:
                lab2[s].set_text("")
            elif s == g:
                lab2[s].set_text(f"{s}' = {_d(kF * vals[s])}")
            else:
                rev = 112 if s == others[0] else 124
                lab2[s].set_text(f"{s}' = {_d(kF * vals[s])}" if i >= rev else f"{s}' = ?")
                lab2[s].set_color("#DC2626" if i >= rev else "#9A3412")
        if 92 <= i < 110:
            j0, j1 = sidx[g]
            hl.set_data([T2[j0][0], T2[j1][0]], [T2[j0][1], T2[j1][1]])
        else:
            hl.set_data([], [])
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 8))
        kk = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[kk][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    if _shadow(P):
        out.update({"a": rnd.choice([1.5, 1.6, 1.8, 2]), "b": rnd.choice([1, 1.2, 1.5, 2, 2.5, 3]),
                    "k": rnd.randint(4, 9)})
        out.pop("c", None)
        return out
    a0, b0, c0 = float(P["a"]), float(P["b"]), float(P["c"])
    if abs(a0 * a0 + b0 * b0 - c0 * c0) < 1e-9:
        pool = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15)]
    else:
        pool = [(4, 5, 6), (5, 6, 7), (6, 7, 8), (5, 5, 6), (4, 6, 7), (7, 8, 9), (3, 5, 7)]
    a, b, c = rnd.choice(pool)
    out.update({"a": a, "b": b, "c": c, "k": rnd.choice([1.5, 2, 2.5, 3, 0.5])})
    return out
''',
}
EXAMPLES += [
    {"id": "geo-sim-1", "kind": "similar_triangles",
     "title": ("Eksik kenarları bulma", "Finding the missing sides"),
     "q": ("△ABC ~ △A'B'C'. △ABC'nin kenarları a = {a}, b = {b}, c = {c}. Benzer üçgende "
           "{g}' = {gv} ise diğer kenarlar kaçtır?",
           "△ABC ~ △A'B'C'. The sides of △ABC are a = {a}, b = {b}, c = {c}. In the similar triangle "
           "{g}' = {gv}. Find the other sides."),
     "P": {"a": 4, "b": 5, "c": 6, "k": 1.5, "given": "a"}},
    {"id": "geo-sim-2", "kind": "similar_triangles",
     "topics": ["shadow", "gölge", "indirect measurement", "word problem", "sözel problem"],
     "title": ("Gölgeyle ağacın boyunu ölçme", "Measuring a tree with shadows"),
     "q": ("Boyu {a} m olan bir kişinin gölgesi {b} m. Aynı anda bir ağacın gölgesi {S} m. "
           "Ağacın boyu kaç metredir?",
           "A person {a} m tall casts a {b} m shadow. At the same moment a tree casts a {S} m shadow. "
           "How tall is the tree?"),
     "P": {"a": 1.5, "b": 2, "k": 6, "scene": "shadow", "unit": "m"}},
    {"id": "geo-sim-3", "kind": "similar_triangles", "topics": ["area ratio", "alan oranı"],
     "title": ("Dik üçgeni büyütme", "Enlarging a right triangle"),
     "q": ("Kenarları {a}, {b}, {c} cm olan bir dik üçgen büyütülüyor; büyük üçgende en uzun kenar "
           "{gv} cm. Diğer kenarları ve alanlar oranını bul.",
           "A right triangle with sides {a}, {b}, {c} cm is enlarged so that its longest side becomes "
           "{gv} cm. Find the other sides and the ratio of the areas."),
     "P": {"a": 6, "b": 8, "c": 10, "k": 2.5, "given": "c", "unit": "cm"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["transform_shape"] = {
    "course": "geo",
    "title": ("Dönüşümler: öteleme, döndürme, yansıma, genişleme",
              "Transformations: translation, rotation, reflection, dilation"),
    "topics": ["transformations", "transformation", "translation", "rotation", "reflection", "dilation",
               "rigid motion", "image and preimage", "coordinate geometry", "symmetry",
               "dönüşüm", "dönüşümler", "öteleme", "döndürme", "yansıma", "simetri", "homoteti",
               "dönüşüm geometrisi"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Polygon, Rectangle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _F(v):
    return Fraction(str(v))


def _d(v):
    v = Fraction(v).limit_denominator(10000)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        s = f"{float(v):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s.replace("-", "−")


def _pt(p):
    return f"({_d(p[0])}, {_d(p[1])})"


def _lin(var, c):
    # 'x + 3' / 'y − 2' / 'x'
    if c == 0:
        return var
    return f"{var} + {_d(c)}" if c > 0 else f"{var} − {_d(-c)}"


def _cs(P):
    a = float(P.get("angle", 90)) % 360
    table = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}
    if a in table:
        return Fraction(table[a][0]), Fraction(table[a][1])
    r = math.radians(a)
    return math.cos(r), math.sin(r)


def _axis(P):
    ax = str(P.get("axis", "x")).replace(" ", "").replace("−", "-")
    return ax


def _image(P, p):
    x, y = p
    t = P["type"]
    if t == "translate":
        return x + _F(P.get("dx", 0)), y + _F(P.get("dy", 0))
    if t == "rotate":
        cx, cy = _F(P.get("cx", 0)), _F(P.get("cy", 0))
        c, s = _cs(P)
        return cx + c * (x - cx) - s * (y - cy), cy + s * (x - cx) + c * (y - cy)
    if t == "reflect":
        ax = _axis(P)
        if ax == "y=x":
            return y, x
        if ax == "y=-x":
            return -y, -x
        if ax.startswith("x="):
            h = _F(ax[2:])
            return 2 * h - x, y
        if ax.startswith("y="):
            h = _F(ax[2:])
            return x, 2 * h - y
        if ax == "y":
            return -x, y
        return x, -y
    k = _F(P.get("k", 2))
    cx, cy = _F(P.get("cx", 0)), _F(P.get("cy", 0))
    return cx + k * (x - cx), cy + k * (y - cy)


def _rule(P):
    t = P["type"]
    if t == "translate":
        return f"(x, y) → ({_lin('x', _F(P.get('dx', 0)))}, {_lin('y', _F(P.get('dy', 0)))})"
    if t == "rotate":
        cx, cy = _F(P.get("cx", 0)), _F(P.get("cy", 0))
        c, s = _cs(P)
        if not isinstance(c, Fraction):
            return "(x, y) → (x·cos θ − y·sin θ, x·sin θ + y·cos θ)"
        X, Y = _lin("x", -cx), _lin("y", -cy)
        if cx != 0:
            X = f"({X})"
        if cy != 0:
            Y = f"({Y})"

        def comb(a, u, b, v, shift):
            parts = []
            for coef, var in ((a, u), (b, v)):
                if coef == 0:
                    continue
                parts.append(("−" if coef < 0 else "+") + var)
            body = parts[0].lstrip("+") + "".join(" " + q[0] + " " + q[1:] for q in parts[1:])
            if shift != 0:
                body = (f"{_d(shift)} + {body}" if not body.startswith("−")
                        else f"{_d(shift)} − {body[1:]}")
            return body
        return f"(x, y) → ({comb(c, X, -s, Y, cx)}, {comb(s, X, c, Y, cy)})"
    if t == "reflect":
        ax = _axis(P)
        rules = {"y=x": "(x, y) → (y, x)", "y=-x": "(x, y) → (−y, −x)", "y": "(x, y) → (−x, y)",
                 "x": "(x, y) → (x, −y)"}
        if ax in rules:
            return rules[ax]
        if ax.startswith("x="):
            return f"(x, y) → ({_d(2 * _F(ax[2:]))} − x, y)"
        return f"(x, y) → (x, {_d(2 * _F(ax[2:]))} − y)"
    k = _F(P.get("k", 2))
    cx, cy = _F(P.get("cx", 0)), _F(P.get("cy", 0))
    if cx == 0 and cy == 0:
        return f"(x, y) → ({_d(k)}x, {_d(k)}y)"
    return f"(x, y) → ({_d(cx)} + {_d(k)}({_lin('x', -cx)}), {_d(cy)} + {_d(k)}({_lin('y', -cy)}))"


def _desc(P):
    t = P["type"]
    if t == "translate":
        v = f"⟨{_d(_F(P.get('dx', 0)))}, {_d(_F(P.get('dy', 0)))}⟩"
        return (f"{v} vektörü kadar öteleme", f"translation by the vector {v}")
    if t == "rotate":
        a = float(P.get("angle", 90))
        c = (_F(P.get("cx", 0)), _F(P.get("cy", 0)))
        ctr = ("orijin", "the origin") if c == (0, 0) else (f"{_pt(c)} noktası", f"the point {_pt(c)}")
        dr = ("saat yönünün tersine", "counterclockwise") if a > 0 else ("saat yönünde", "clockwise")
        return (f"{ctr[0]} etrafında {_d(_F(abs(a)))}° döndürme ({dr[0]})",
                f"rotation by {_d(_F(abs(a)))}° {dr[1]} about {ctr[1]}")
    if t == "reflect":
        ax = _axis(P)
        names = {"x": ("x eksenine göre yansıma", "reflection across the x-axis"),
                 "y": ("y eksenine göre yansıma", "reflection across the y-axis"),
                 "y=x": ("y = x doğrusuna göre yansıma", "reflection across the line y = x"),
                 "y=-x": ("y = −x doğrusuna göre yansıma", "reflection across the line y = −x")}
        if ax in names:
            return names[ax]
        ln = ax.replace("=", " = ").replace("-", "−")
        return (f"{ln} doğrusuna göre yansıma", f"reflection across the line {ln}")
    k = _d(_F(P.get("k", 2)))
    c = (_F(P.get("cx", 0)), _F(P.get("cy", 0)))
    ctr = ("orijin", "the origin") if c == (0, 0) else (_pt(c), _pt(c))
    return (f"{ctr[0]} merkezli, k = {k} oranlı genişleme (homoteti)",
            f"dilation with scale factor k = {k} centred at {ctr[1]}")


def _prop(P):
    t = P["type"]
    if t == "dilate":
        k = _F(P.get("k", 2))
        return (f"Kenarlar {_d(abs(k))} katı olur, açılar korunur; alan {_d(k * k)} katı olur.",
                f"Sides are multiplied by {_d(abs(k))}, angles are kept; the area is multiplied by {_d(k * k)}.")
    if t == "reflect":
        return ("İzometri: uzunluklar ve açılar korunur; köşelerin dönme yönü (sırası) tersine döner.",
                "Isometry: lengths and angles are kept; the order of the vertices is reversed.")
    return ("İzometri: kenar uzunlukları ve açılar korunur (şekil ve boyut aynı).",
            "Isometry: side lengths and angles are kept (same shape and size).")


def _pts(P):
    return [(_F(p[0]), _F(p[1])) for p in P["pts"]]


_NM = "ABCDEFGH"


def solve(P):
    pts = _pts(P)
    imgs = [_image(P, p) for p in pts]
    rule = _rule(P)
    desc = _desc(P)
    steps = [(f"Dönüşüm: {desc[0]}", f"Transformation: {desc[1]}"),
             (f"Kural: {rule}", f"Rule: {rule}")]
    for j, (p, q) in enumerate(zip(pts, imgs)):
        s = f"{_NM[j]}{_pt(p)} → {_NM[j]}'{_pt(q)}"
        steps.append((s, s))
    steps.append(_prop(P))
    ans = ", ".join(f"{_NM[j]}'{_pt(q)}" for j, q in enumerate(imgs))
    if P["type"] == "dilate":
        ans += f"  (k = {_d(_F(P.get('k', 2)))})"
    shape = ", ".join(f"{_NM[j]}{_pt(p)}" for j, p in enumerate(pts))
    return {"answer": ans, "steps": steps, "fmt": {"shape": shape, "desc": desc, "rule": rule}}


def _morph(P, pre, img, u):
    t = P["type"]
    if t == "rotate":
        cx, cy = float(P.get("cx", 0)), float(P.get("cy", 0))
        a = math.radians(float(P.get("angle", 90))) * u
        c, s = math.cos(a), math.sin(a)
        dx, dy = pre[:, 0] - cx, pre[:, 1] - cy
        return np.column_stack([cx + c * dx - s * dy, cy + s * dx + c * dy])
    if t == "dilate":
        cx, cy = float(P.get("cx", 0)), float(P.get("cy", 0))
        f = 1 + (float(P.get("k", 2)) - 1) * u
        return np.column_stack([cx + f * (pre[:, 0] - cx), cy + f * (pre[:, 1] - cy)])
    return pre + u * (img - pre)


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    L = 0 if tr else 1
    ptsF = _pts(P)
    imgF = [_image(P, p) for p in ptsF]
    pre = np.array([[float(x), float(y)] for x, y in ptsF])
    img = np.array([[float(x), float(y)] for x, y in imgF])
    n = len(pre)
    t = P["type"]
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=[1.3, 1.0], left=0.04,
                          right=0.98, top=0.98, bottom=0.05, wspace=0.08, hspace=0.08)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left", fontsize=11.5,
                    color="#111827", bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    allp = np.vstack([pre, img, [[float(P.get("cx", 0)), float(P.get("cy", 0))]]])
    lox, hix = allp[:, 0].min(), allp[:, 0].max()
    loy, hiy = allp[:, 1].min(), allp[:, 1].max()
    half = max(5.0, (hix - lox) / 2 + 1.6, (hiy - loy) / 2 + 1.6)
    cx0 = 0.0 if (lox >= -half + 1.2 and hix <= half - 1.2) else (lox + hix) / 2
    cy0 = 0.0 if (loy >= -half + 1.2 and hiy <= half - 1.2) else (loy + hiy) / 2
    ax.set_xlim(cx0 - half, cx0 + half)
    ax.set_ylim(cy0 - half, cy0 + half)
    ax.set_aspect("equal")
    step = 1 if half <= 7 else 2
    ax.set_xticks(np.arange(math.ceil(cx0 - half), math.floor(cx0 + half) + 1, step))
    ax.set_yticks(np.arange(math.ceil(cy0 - half), math.floor(cy0 + half) + 1, step))
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.1)
    ax.axvline(0, color="#374151", lw=1.1)
    p0 = Polygon(pre, closed=True, fc="#BFDBFE", ec="#2563EB", lw=2.2, alpha=0.9, zorder=3)
    p1 = Polygon(pre, closed=True, fc="#FED7AA", ec="#E07B39", lw=2.2, alpha=0.0, zorder=4)
    ax.add_patch(p0)
    ax.add_patch(p1)
    g0 = pre.mean(axis=0)
    g1 = img.mean(axis=0)

    def off(p, g, dist=0.55):
        d = p - g
        nn = math.hypot(d[0], d[1]) + 1e-9
        return p + dist * d / nn

    fs = 9.5
    lab0 = []
    for j in range(n):
        q = off(pre[j], g0)
        lab0.append(ax.text(q[0], q[1], f"{_NM[j]}{_pt(ptsF[j])}", ha="center", va="center", fontsize=fs,
                            color="#1E3A8A", zorder=6))
    lab1 = [ax.text(0, 0, "", ha="center", va="center", fontsize=fs, color="#9A3412", fontweight="bold",
                    zorder=6) for _ in range(n)]
    traces = []
    for j in range(n):
        ln, = ax.plot([], [], ":", color="#6B7280", lw=1.3, zorder=2)
        traces.append(ln)
    tool, = ax.plot([], [], color="#7C3AED", lw=2.2, zorder=2)
    cdot, = ax.plot([], [], "o", color="#7C3AED", ms=7, zorder=5)
    ttool = ax.text(0, 0, "", fontsize=10.5, color="#7C3AED", fontweight="bold", zorder=6)
    ctr = np.array([float(P.get("cx", 0)), float(P.get("cy", 0))])
    if t == "reflect":
        axn = _axis(P)
        R = 3 * half
        if axn == "y=x":
            seg = np.array([[-R, -R], [R, R]])
        elif axn == "y=-x":
            seg = np.array([[-R, R], [R, -R]])
        elif axn.startswith("x="):
            h = float(_F(axn[2:]))
            seg = np.array([[h, -R], [h, R]])
        elif axn.startswith("y="):
            h = float(_F(axn[2:]))
            seg = np.array([[-R, h], [R, h]])
        elif axn == "y":
            seg = np.array([[0, -R], [0, R]])
        else:
            seg = np.array([[-R, 0], [R, 0]])
    rule = _rule(P)
    desc = _desc(P)
    rows = [f"{_NM[j]}{_pt(ptsF[j])} → {_NM[j]}'{_pt(imgF[j])}" for j in range(n)]
    tx.text(0.05, 0.96, "Kural" if tr else "Rule", transform=tx.transAxes, va="top", fontsize=11,
            color="#6B7280", fontweight="bold")
    trule = tx.text(0.05, 0.87, rule, transform=tx.transAxes, va="top", fontsize=11 if len(rule) < 30 else 9.5,
                    color="#7C3AED", fontweight="bold", alpha=0.0)
    tx.text(0.05, 0.74, "Köşeler" if tr else "Vertices", transform=tx.transAxes, va="top", fontsize=11,
            color="#6B7280", fontweight="bold")
    trows = [tx.text(0.05, 0.65 - j * 0.09, s, transform=tx.transAxes, va="top", fontsize=11.5,
                     color="#111827", alpha=0.0) for j, s in enumerate(rows)]
    prop = _prop(P)[L]
    words = prop.split(" ")
    wrapped, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 30:
            wrapped.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    wrapped.append(cur)
    tprop = tx.text(0.05, 0.62 - n * 0.09, "\n".join(wrapped), transform=tx.transAxes, va="top",
                    fontsize=10, color="#15803D", alpha=0.0, linespacing=1.4)
    shape = ", ".join(f"{_NM[j]}{_pt(ptsF[j])}" for j in range(n))
    narr = [
        (f"1) İlk şekil: {shape}", f"1) Original figure: {shape}"),
        (f"2) Dönüşüm: {desc[0]}", f"2) Transformation: {desc[1]}"),
        ("3) Şekil hareket ediyor; her köşe aynı kurala uyar", "3) The figure moves; every vertex follows the same rule"),
        (f"4) Görüntünün köşeleri — kural {rule}", f"4) Image vertices — rule {rule}"),
        ("5) Sonuç: " + ", ".join(f"{_NM[j]}'{_pt(imgF[j])}" for j in range(n)),
         "5) Result: " + ", ".join(f"{_NM[j]}'{_pt(imgF[j])}" for j in range(n))),
    ]
    starts = [0, 16, 32, 90, 122]
    N = 140

    def update(i):
        p0.set_alpha(0.3 + 0.6 * _ph(i, 0, 10))
        tl = _ph(i, 16, 28)
        if t == "reflect":
            tool.set_data(seg[:, 0], seg[:, 1])
            tool.set_alpha(tl)
            cdot.set_data([], [])
            ttool.set_text("")
        elif t in ("rotate", "dilate"):
            cdot.set_data([ctr[0]], [ctr[1]]) if tl > 0 else cdot.set_data([], [])
            ttool.set_position((ctr[0] + 0.25, ctr[1] - 0.6))
            ttool.set_text(("merkez" if tr else "centre") if tl > 0 else "")
            tool.set_data([], [])
        else:
            if tl > 0:
                tool.set_data([pre[0][0], pre[0][0] + tl * (img[0][0] - pre[0][0])],
                              [pre[0][1], pre[0][1] + tl * (img[0][1] - pre[0][1])])
            else:
                tool.set_data([], [])
            mid = (pre[0] + img[0]) / 2
            ttool.set_position((mid[0] + 0.25, mid[1] + 0.25))
            ttool.set_text(f"⟨{_d(_F(P.get('dx', 0)))}, {_d(_F(P.get('dy', 0)))}⟩" if tl >= 1 else "")
        u = _ease(_ph(i, 32, 88))
        cur = _morph(P, pre, img, u)
        p1.set_xy(cur)
        p1.set_alpha(0.85 if i >= 30 else 0.0)
        for j in range(n):
            if i < 30:
                traces[j].set_data([], [])
            elif t == "rotate":
                a0 = math.atan2(pre[j][1] - ctr[1], pre[j][0] - ctr[0])
                rr = math.hypot(pre[j][0] - ctr[0], pre[j][1] - ctr[1])
                tt = np.linspace(a0, a0 + math.radians(float(P.get("angle", 90))) * u, 40)
                traces[j].set_data(ctr[0] + rr * np.cos(tt), ctr[1] + rr * np.sin(tt))
            elif t == "dilate":
                far = img[j] if float(P.get("k", 2)) >= 1 else pre[j]
                traces[j].set_data([ctr[0], far[0]], [ctr[1], far[1]])
            else:
                traces[j].set_data([pre[j][0], cur[j][0]], [pre[j][1], cur[j][1]])
            gc = cur.mean(axis=0)
            q = off(cur[j], gc)
            lab1[j].set_position((q[0], q[1]))
            if i < 30:
                lab1[j].set_text("")
            elif i < 92 + 7 * j:
                lab1[j].set_text(f"{_NM[j]}'")
            else:
                lab1[j].set_text(f"{_NM[j]}'{_pt(imgF[j])}")
            trows[j].set_alpha(_ph(i, 92 + 7 * j, 98 + 7 * j))
        trule.set_alpha(_ph(i, 22, 30))
        tprop.set_alpha(_ph(i, 122, 130))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][L])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    t = P["type"]
    even = t == "dilate" and float(P.get("k", 2)) < 1
    while True:
        k = len(P.get("pts", [[0, 0]] * 3))
        rng = [v for v in range(-4, 5) if (v % 2 == 0 or not even)]
        pts = [[rnd.choice(rng), rnd.choice(rng)] for _ in range(max(3, min(4, k)))]
        if len(pts) == 4:
            x0, y0 = rnd.choice(rng), rnd.choice(rng)
            w = rnd.choice([2, 3] if not even else [2, 4])
            pts = [[x0, y0], [x0 + w, y0], [x0 + w, y0 + w], [x0, y0 + w]]
        (x1, y1), (x2, y2), (x3, y3) = pts[0], pts[1], pts[2]
        if (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1) != 0:
            break
    out["pts"] = pts
    if t == "translate":
        while True:
            dx, dy = rnd.randint(-5, 5), rnd.randint(-5, 5)
            if dx != 0 and dy != 0:
                break
        out.update({"dx": dx, "dy": dy})
    elif t in ("rotate", "reflect"):
        pass
    else:
        out.update({"k": 0.5 if even else rnd.choice([2, 2, 3]), "cx": 0, "cy": 0})
    return out
''',
}
EXAMPLES += [
    {"id": "geo-trans-1", "kind": "transform_shape", "topics": ["rotation", "döndürme"],
     "title": ("Orijin etrafında 90° döndürme", "Rotating 90° about the origin"),
     "q": ("{shape} üçgenine {desc} uygula. Görüntünün köşe koordinatları nelerdir?",
           "Apply a {desc} to the triangle {shape}. What are the coordinates of the image?"),
     "P": {"type": "rotate", "pts": [[1, 1], [4, 1], [1, 3]], "angle": 90, "cx": 0, "cy": 0}},
    {"id": "geo-trans-2", "kind": "transform_shape", "topics": ["reflection", "yansıma", "symmetry"],
     "title": ("y = x doğrusuna göre yansıma", "Reflecting across y = x"),
     "q": ("{shape} üçgeninin {desc}sını çiz ve görüntünün köşe koordinatlarını yaz.",
           "Draw the {desc} of the triangle {shape} and give the image coordinates."),
     "P": {"type": "reflect", "pts": [[1, -3], [4, -2], [2, 0]], "axis": "y=x"}},
    {"id": "geo-trans-3", "kind": "transform_shape",
     "topics": ["translation", "öteleme", "word problem", "sözel problem"],
     "title": ("Oyun tahtasında öteleme", "Sliding a piece on a game board"),
     "q": ("Bir oyunda köşeleri {shape} olan kare bir taşa {desc} uygulanıyor. Taşın yeni "
           "köşeleri nerededir?",
           "In a game, a square tile with corners {shape} undergoes a {desc}. Where are its "
           "new corners?"),
     "P": {"type": "translate", "pts": [[-4, 2], [-2, 2], [-2, 4], [-4, 4]], "dx": 6, "dy": -5}},
    {"id": "geo-trans-4", "kind": "transform_shape", "topics": ["dilation", "scale factor", "genişleme"],
     "title": ("Orijin merkezli genişleme", "Dilation about the origin"),
     "q": ("{shape} üçgenine {desc} uygula. Görüntünün köşeleri ve kenar uzunluklarının oranı nedir?",
           "Apply a {desc} to the triangle {shape}. Find the image vertices and the ratio of side lengths."),
     "P": {"type": "dilate", "pts": [[1, 1], [3, 1], [1, 2]], "k": 2, "cx": 0, "cy": 0}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["distance_midpoint"] = {
    "course": "geo",
    "title": ("İki nokta arası uzaklık ve orta nokta", "Distance and midpoint of two points"),
    "topics": ["distance formula", "midpoint", "midpoint formula", "distance between two points",
               "coordinate geometry", "analytic geometry", "line segment", "iki nokta arası uzaklık",
               "uzaklık formülü", "orta nokta", "analitik geometri", "koordinat geometrisi"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _d(v):
    v = Fraction(v).limit_denominator(10000)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        s = f"{float(v):.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s.replace("-", "−")


def _p(v):
    return f"({_d(v)})" if v < 0 else _d(v)


def _root(v):
    v = Fraction(v)
    if v.denominator != 1:
        return None, f"√{_d(v)}"
    n = v.numerator
    r = math.isqrt(n)
    if r * r == n:
        return str(r), str(r)
    k, m, f = 1, n, 2
    while f * f <= m:
        while m % (f * f) == 0:
            k *= f
            m //= f * f
        f += 1
    return None, (str(k) if k > 1 else "") + "√" + str(m)


def _vals(P):
    return [Fraction(str(P[k])) for k in ("x1", "y1", "x2", "y2")]


def _dist_text(s):
    exact, form = _root(s)
    if exact is not None:
        return exact
    return f"{form} ≈ {math.sqrt(float(s)):.2f}"


def solve(P):
    x1, y1, x2, y2 = _vals(P)
    dx, dy = x2 - x1, y2 - y1
    s = dx * dx + dy * dy
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    unit = P.get("unit", "")
    us = f" {unit}" if unit else ""
    dtxt = _dist_text(s)
    steps = [
        ("Uzaklık formülü (Pisagor'dan): d = √((x₂ − x₁)² + (y₂ − y₁)²)",
         "Distance formula (from Pythagoras): d = √((x₂ − x₁)² + (y₂ − y₁)²)"),
        (f"Δx = {_d(x2)} − {_p(x1)} = {_d(dx)},   Δy = {_d(y2)} − {_p(y1)} = {_d(dy)}",
         f"Δx = {_d(x2)} − {_p(x1)} = {_d(dx)},   Δy = {_d(y2)} − {_p(y1)} = {_d(dy)}"),
        (f"d = √({_p(dx)}² + {_p(dy)}²) = √({_d(dx * dx)} + {_d(dy * dy)}) = √{_d(s)} = {dtxt}{us}",
         f"d = √({_p(dx)}² + {_p(dy)}²) = √({_d(dx * dx)} + {_d(dy * dy)}) = √{_d(s)} = {dtxt}{us}"),
        ("Orta nokta formülü: M = ((x₁ + x₂)/2, (y₁ + y₂)/2)  (koordinatların ortalaması)",
         "Midpoint formula: M = ((x₁ + x₂)/2, (y₁ + y₂)/2)  (average of the coordinates)"),
        (f"M = (({_d(x1)} + {_p(x2)})/2, ({_d(y1)} + {_p(y2)})/2) = ({_d(mx)}, {_d(my)})",
         f"M = (({_d(x1)} + {_p(x2)})/2, ({_d(y1)} + {_p(y2)})/2) = ({_d(mx)}, {_d(my)})"),
    ]
    return {"answer": f"d = {dtxt}{us},  M({_d(mx)}, {_d(my)})", "steps": steps,
            "fmt": {"A": f"({_d(x1)}, {_d(y1)})", "B": f"({_d(x2)}, {_d(y2)})"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    x1F, y1F, x2F, y2F = _vals(P)
    x1, y1, x2, y2 = (float(v) for v in (x1F, y1F, x2F, y2F))
    dxF, dyF = x2F - x1F, y2F - y1F
    sF = dxF * dxF + dyF * dyF
    mxF, myF = (x1F + x2F) / 2, (y1F + y2F) / 2
    mx, my = float(mxF), float(myF)
    dtxt = _dist_text(sF)
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=[1.3, 1.0], left=0.04,
                          right=0.98, top=0.98, bottom=0.05, wspace=0.08, hspace=0.08)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left", fontsize=11.5,
                    color="#111827", bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    xs, ys = [x1, x2, 0.0], [y1, y2, 0.0]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half = max(4.0, (max(xs) - min(xs)) / 2 + 1.8, (max(ys) - min(ys)) / 2 + 1.8)
    ax.set_xlim(cx - half, cx + half)
    ax.set_ylim(cy - half, cy + half)
    ax.set_aspect("equal")
    step = 1 if half <= 7 else 2
    ax.set_xticks(np.arange(math.ceil(cx - half), math.floor(cx + half) + 1, step))
    ax.set_yticks(np.arange(math.ceil(cy - half), math.floor(cy + half) + 1, step))
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.1)
    ax.axvline(0, color="#374151", lw=1.1)
    K = (x2, y1)
    lx, = ax.plot([], [], color="#E07B39", lw=3, zorder=3)
    ly, = ax.plot([], [], color="#16A34A", lw=3, zorder=3)
    hyp, = ax.plot([], [], color="#2563EB", lw=3, zorder=4)
    rm, = ax.plot([], [], color="#6B7280", lw=1.1, zorder=3)
    pts, = ax.plot([x1, x2], [y1, y2], "o", color="#111827", ms=8, zorder=6)
    sgx = 1 if x1 > x2 else -1
    sgy = 1 if y1 < y2 else -1
    wb = dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85)
    ta = ax.text(x1, y1 - 0.5 * sgy, f"A({_d(x1F)}, {_d(y1F)})", fontsize=10, ha="center",
                 va="top" if sgy > 0 else "bottom", color="#111827", zorder=7, bbox=wb)
    tb = ax.text(x2, y2 + 0.5 * sgy, f"B({_d(x2F)}, {_d(y2F)})", fontsize=10, ha="center",
                 va="bottom" if sgy > 0 else "top", color="#111827", zorder=7, bbox=wb)
    tdx = ax.text((x1 + x2) / 2, y1 - 0.45 * sgy, "", ha="center", va="center", fontsize=10.5,
                  color="#C2410C", fontweight="bold", bbox=wb, zorder=7)
    tdy = ax.text(x2 - 0.3 * sgx, (y1 + y2) / 2, "", ha="left" if sgx < 0 else "right", va="center",
                  fontsize=10.5, color="#15803D", fontweight="bold", bbox=wb, zorder=7)
    nrm = np.array([-(y2 - y1), x2 - x1])
    nrm = nrm / (np.hypot(nrm[0], nrm[1]) + 1e-9)
    if np.dot(nrm, np.array([K[0] - (x1 + x2) / 2, K[1] - (y1 + y2) / 2])) > 0:
        nrm = -nrm
    hp = np.array([(x1 + x2) / 2, (y1 + y2) / 2]) + 0.25 * half * nrm
    td = ax.text(hp[0], hp[1], "", ha="center", va="center", fontsize=11, color="#1D4ED8",
                 fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85),
                 zorder=7)
    trav, = ax.plot([], [], "o", color="#7C3AED", ms=7, zorder=7)
    mdot, = ax.plot([], [], "D", color="#7C3AED", ms=9, zorder=8)
    proj, = ax.plot([], [], "--", color="#7C3AED", lw=1.2, zorder=2)
    tm = ax.text(0, 0, "", fontsize=11, color="#6D28D9", fontweight="bold", zorder=8, ha="center", va="center",
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    lines = [f"Δx = {_d(x2F)} − {_p(x1F)} = {_d(dxF)}",
             f"Δy = {_d(y2F)} − {_p(y1F)} = {_d(dyF)}",
             f"d = √({_p(dxF)}² + {_p(dyF)}²) = √{_d(sF)}",
             f"d = {dtxt}",
             f"M = (({_d(x1F)} + {_p(x2F)})/2, ({_d(y1F)} + {_p(y2F)})/2)",
             f"M = ({_d(mxF)}, {_d(myF)})"]
    tx.text(0.05, 0.96, "Adım adım" if tr else "Step by step", transform=tx.transAxes, va="top",
            fontsize=11, color="#6B7280", fontweight="bold")
    arts = [tx.text(0.05, 0.86 - k * 0.11, s, transform=tx.transAxes, va="top",
                    fontsize=11.5 if len(s) < 26 else 10, color="#111827", alpha=0.0)
            for k, s in enumerate(lines)]
    arts[0].set_color("#C2410C")
    arts[1].set_color("#15803D")
    arts[3].set_color("#DC2626")
    arts[3].set_fontweight("bold")
    arts[5].set_color("#6D28D9")
    arts[5].set_fontweight("bold")
    times = [24, 44, 66, 80, 96, 112]
    narr = [
        (f"1) A({_d(x1F)}, {_d(y1F)}) ve B({_d(x2F)}, {_d(y2F)}) noktaları",
         f"1) The points A({_d(x1F)}, {_d(y1F)}) and B({_d(x2F)}, {_d(y2F)})"),
        (f"2) Yatay fark: Δx = x₂ − x₁ = {_d(dxF)}", f"2) Horizontal change: Δx = x₂ − x₁ = {_d(dxF)}"),
        (f"3) Dikey fark: Δy = y₂ − y₁ = {_d(dyF)}", f"3) Vertical change: Δy = y₂ − y₁ = {_d(dyF)}"),
        (f"4) AB bir dik üçgenin hipotenüsü: d = √(Δx² + Δy²) = {dtxt}",
         f"4) AB is the hypotenuse of a right triangle: d = √(Δx² + Δy²) = {dtxt}"),
        ("5) Orta nokta: iki uçtan eşit uzaklıkta; koordinatların ortalaması",
         "5) Midpoint: equally far from both ends; average the coordinates"),
        (f"Sonuç: d = {dtxt},  M({_d(mxF)}, {_d(myF)})", f"Result: d = {dtxt},  M({_d(mxF)}, {_d(myF)})"),
    ]
    starts = [0, 14, 34, 56, 84, 112]
    N = 140

    def update(i):
        u = _ease(_ph(i, 14, 32))
        lx.set_data([x1, x1 + u * (x2 - x1)], [y1, y1]) if u > 0 else lx.set_data([], [])
        tdx.set_text(f"Δx = {_d(dxF)}" if u >= 1 else "")
        v = _ease(_ph(i, 34, 52))
        ly.set_data([x2, x2], [y1, y1 + v * (y2 - y1)]) if v > 0 else ly.set_data([], [])
        tdy.set_text(f"Δy = {_d(dyF)}" if v >= 1 else "")
        m = 0.35
        if v >= 1 and x1 != x2 and y1 != y2:
            ex, ey = -m * np.sign(x2 - x1), m * np.sign(y2 - y1)
            rm.set_data([x2 + ex, x2 + ex, x2], [y1, y1 + ey, y1 + ey])
        else:
            rm.set_data([], [])
        w = _ease(_ph(i, 56, 78))
        hyp.set_data([x1, x1 + w * (x2 - x1)], [y1, y1 + w * (y2 - y1)]) if w > 0 else hyp.set_data([], [])
        td.set_text(("d = ?" if i < 78 else f"d = {dtxt}") if w > 0.5 else "")
        z = _ease(_ph(i, 84, 108))
        if 84 <= i < 108:
            trav.set_data([x1 + z * (mx - x1), x2 + z * (mx - x2)], [y1 + z * (my - y1), y2 + z * (my - y2)])
        else:
            trav.set_data([], [])
        if i >= 108:
            mdot.set_data([mx], [my])
            proj.set_data([mx, mx, np.nan, mx, 0], [my, 0, np.nan, my, my])
            mp = np.array([mx, my]) - 0.16 * half * nrm
            tm.set_position((mp[0], mp[1]))
            tm.set_text(f"M({_d(mxF)}, {_d(myF)})")
        else:
            mdot.set_data([], [])
            proj.set_data([], [])
            tm.set_text("")
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 7))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    while True:
        a, b = rnd.choice([(3, 4), (4, 3), (6, 8), (8, 6), (5, 12), (2, 3), (4, 4), (1, 5)])
        x1, y1 = rnd.randint(-6, 4), rnd.randint(-6, 4)
        x2 = x1 + a * rnd.choice([1, -1])
        y2 = y1 + b * rnd.choice([1, -1])
        if max(abs(x2), abs(y2)) <= 9:
            out.update({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
            return out
''',
}
EXAMPLES += [
    {"id": "geo-dist-1", "kind": "distance_midpoint",
     "title": ("Uzaklık ve orta nokta", "Distance and midpoint"),
     "q": ("A{A} ve B{B} noktaları arasındaki uzaklığı ve AB doğru parçasının orta noktasını bul.",
           "Find the distance between A{A} and B{B} and the midpoint of segment AB."),
     "P": {"x1": -2, "y1": 1, "x2": 4, "y2": 9}},
    {"id": "geo-dist-2", "kind": "distance_midpoint", "topics": ["radical", "köklü sayı"],
     "title": ("Köklü uzaklık", "A distance with a square root"),
     "q": ("A{A} ile B{B} arasındaki uzaklığı en sade köklü biçimde yaz; orta noktayı bul.",
           "Write the distance between A{A} and B{B} in simplest radical form and find the midpoint."),
     "P": {"x1": 1, "y1": -3, "x2": 6, "y2": 2}},
    {"id": "geo-dist-3", "kind": "distance_midpoint", "topics": ["word problem", "sözel problem", "map"],
     "title": ("Haritada iki kasaba", "Two towns on a map"),
     "q": ("Bir haritada (birimler km) iki kasaba A{A} ve B{B} noktalarında. Kuş uçuşu uzaklık kaç km? "
           "Tam ortada buluşmak isteyen iki arkadaş hangi noktada buluşur?",
           "On a map (units in km) two towns are at A{A} and B{B}. How far apart are they in a straight "
           "line? Two friends meeting exactly halfway meet at which point?"),
     "P": {"x1": -3, "y1": -2, "x2": 9, "y2": 3, "unit": "km"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["arc_sector"] = {
    "course": "geo",
    "title": ("Yay uzunluğu ve daire dilimi alanı", "Arc length and sector area"),
    "topics": ["arc length", "sector", "sector area", "area of a sector", "central angle", "radian",
               "radians", "degrees to radians", "circles", "yay uzunluğu", "daire dilimi", "merkez açı",
               "radyan", "dilim alanı"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Polygon, Rectangle, Circle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _d(v):
    v = Fraction(v).limit_denominator(10000)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        s = f"{float(v):.4f}".rstrip("0").rstrip(".")
    return s.replace("-", "−")


def _fr(v):
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _pi(c):
    c = Fraction(c).limit_denominator(100000)
    if c == 0:
        return "0"
    num = "" if c.numerator == 1 else str(c.numerator)
    return f"{num}π" if c.denominator == 1 else f"{num}π/{c.denominator}"


def _vals(P):
    return Fraction(str(P["r"])), Fraction(str(P["theta"]))


def solve(P):
    r, th = _vals(P)
    rad = th / 180
    frac = th / 360
    s = 2 * r * frac
    A = r * r * frac
    unit = P.get("unit", "")
    u1 = f" {unit}" if unit else ""
    u2 = f" {unit}²" if unit else ""
    sv, Av = float(s) * math.pi, float(A) * math.pi
    steps = [
        (f"Radyana çevir: θ = {_d(th)}° · π/180° = {_pi(rad)} rad ≈ {float(rad) * math.pi:.4g} rad",
         f"Convert to radians: θ = {_d(th)}° · π/180° = {_pi(rad)} rad ≈ {float(rad) * math.pi:.4g} rad"),
        (f"Dilim, dairenin θ/360° = {_d(th)}/360 = {_fr(frac)} kadarıdır.",
         f"The sector is θ/360° = {_d(th)}/360 = {_fr(frac)} of the circle."),
        (f"Yay uzunluğu: s = 2πr · θ/360° = 2π · {_d(r)} · {_fr(frac)} = {_pi(s)} ≈ {sv:.2f}{u1}",
         f"Arc length: s = 2πr · θ/360° = 2π · {_d(r)} · {_fr(frac)} = {_pi(s)} ≈ {sv:.2f}{u1}"),
        (f"Radyanla aynı sonuç: s = r · θ = {_d(r)} · {_pi(rad)} = {_pi(s)}",
         f"Same with radians: s = r · θ = {_d(r)} · {_pi(rad)} = {_pi(s)}"),
        (f"Dilim alanı: A = πr² · θ/360° = π · {_d(r * r)} · {_fr(frac)} = {_pi(A)} ≈ {Av:.2f}{u2}",
         f"Sector area: A = πr² · θ/360° = π · {_d(r * r)} · {_fr(frac)} = {_pi(A)} ≈ {Av:.2f}{u2}"),
        (f"Radyanla: A = ½ · r² · θ = ½ · {_d(r * r)} · {_pi(rad)} = {_pi(A)}",
         f"With radians: A = ½ · r² · θ = ½ · {_d(r * r)} · {_pi(rad)} = {_pi(A)}"),
    ]
    return {"answer": f"s = {_pi(s)} ≈ {sv:.2f}{u1},  A = {_pi(A)} ≈ {Av:.2f}{u2}", "steps": steps,
            "fmt": {"rad": _pi(rad), "d": _d(2 * r)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    rF, thF = _vals(P)
    r, th = float(rF), float(thF)
    th = max(1.0, min(359.0, th))
    rad = thF / 180
    frac = thF / 360
    sF, AF = 2 * rF * frac, rF * rF * frac
    sv, Av = float(sF) * math.pi, float(AF) * math.pi
    unit = P.get("unit", "")
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=[1.3, 1.0], left=0.02,
                          right=0.98, top=0.98, bottom=0.03, wspace=0.04, hspace=0.06)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left", fontsize=11.5,
                    color="#111827", bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.38 * r, 1.38 * r)
    ax.set_ylim(-1.32 * r, 1.32 * r)
    disk = Circle((0, 0), r, fc="#F3F4F6", ec="#6B7280", lw=1.6, zorder=1)
    ax.add_patch(disk)
    sec = Polygon(np.zeros((3, 2)), closed=True, fc="#93C5FD", ec="#2563EB", lw=1.6, alpha=0.75, zorder=2)
    ax.add_patch(sec)
    arc, = ax.plot([], [], color="#E07B39", lw=5, solid_capstyle="round", zorder=4)
    r0, = ax.plot([0, r], [0, 0], color="#111827", lw=2, zorder=5)
    r1, = ax.plot([], [], color="#111827", lw=2, zorder=5)
    small, = ax.plot([], [], color="#DC2626", lw=1.6, zorder=5)
    ax.plot([0], [0], "o", color="#111827", ms=4, zorder=6)
    trr = ax.text(r / 2, -0.07 * r, f"r = {_d(rF)}", ha="center", va="top", fontsize=11, color="#111827")
    tth = ax.text(0, 0, "", ha="left", va="bottom", fontsize=11, color="#DC2626", fontweight="bold", zorder=7)
    nt = int(math.floor(math.radians(th) + 1e-9))
    ticks = []
    for k in range(1, nt + 1):
        a = float(k)
        tk, = ax.plot([0.93 * r * math.cos(a), 1.07 * r * math.cos(a)],
                      [0.93 * r * math.sin(a), 1.07 * r * math.sin(a)], color="#7C3AED", lw=2, alpha=0.0, zorder=6)
        tl = ax.text(1.17 * r * math.cos(a), 1.17 * r * math.sin(a), f"{k} rad", ha="center", va="center",
                     fontsize=9, color="#7C3AED", alpha=0.0)
        ticks.append((tk, tl))
    mid = math.radians(th / 2)
    ts = ax.text(1.24 * r * math.cos(mid), 1.24 * r * math.sin(mid), "", ha="center", va="center",
                 fontsize=11.5, color="#C2410C", fontweight="bold", zorder=7,
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    narrow = th < 80
    ar = 0.6 if narrow else 0.55
    ta = ax.text(ar * r * math.cos(mid), ar * r * math.sin(mid), "", ha="left" if narrow else "center",
                 va="center", fontsize=11.5, color="#1D4ED8", fontweight="bold", zorder=7,
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    tf = ax.text(0, -1.2 * r, "", ha="center", va="center", fontsize=11, color="#374151")
    lines = [f"θ = {_d(thF)}° = {_pi(rad)} rad",
             f"θ/360° = {_fr(frac)}",
             f"s = 2πr · {_fr(frac)} = {_pi(sF)}",
             f"s ≈ {sv:.2f}",
             f"A = πr² · {_fr(frac)} = {_pi(AF)}",
             f"A ≈ {Av:.2f}"]
    tx.text(0.05, 0.96, "Adım adım" if tr else "Step by step", transform=tx.transAxes, va="top",
            fontsize=11, color="#6B7280", fontweight="bold")
    arts = [tx.text(0.05, 0.86 - k * 0.11, s, transform=tx.transAxes, va="top", fontsize=12,
                    color="#111827", alpha=0.0) for k, s in enumerate(lines)]
    for k in (2, 3):
        arts[k].set_color("#C2410C")
    for k in (4, 5):
        arts[k].set_color("#1D4ED8")
    arts[3].set_fontweight("bold")
    arts[5].set_fontweight("bold")
    times = [62, 82, 88, 94, 104, 110]
    narr = [
        (f"1) Yarıçap r = {_d(rF)}, merkez açı θ = {_d(thF)}°", f"1) Radius r = {_d(rF)}, central angle θ = {_d(thF)}°"),
        (f"2) Yarıçap 0°'den {_d(thF)}°'ye dönüyor: daire dilimi oluşuyor",
         f"2) The radius sweeps from 0° to {_d(thF)}°: a sector appears"),
        (f"3) Radyan = yay / yarıçap: θ = {_pi(rad)} ≈ {math.radians(th):.2f} rad (mor çizgiler 1 rad aralıklı)",
         f"3) Radians = arc / radius: θ = {_pi(rad)} ≈ {math.radians(th):.2f} rad (purple marks every 1 rad)"),
        (f"4) Yay = çevrenin {_fr(frac)} kadarı: s = 2π·{_d(rF)}·{_fr(frac)} = {_pi(sF)} ≈ {sv:.2f}",
         f"4) Arc = {_fr(frac)} of the circumference: s = 2π·{_d(rF)}·{_fr(frac)} = {_pi(sF)} ≈ {sv:.2f}"),
        (f"5) Dilim = dairenin {_fr(frac)} kadarı: A = π·{_d(rF * rF)}·{_fr(frac)} = {_pi(AF)} ≈ {Av:.2f}",
         f"5) Sector = {_fr(frac)} of the disc: A = π·{_d(rF * rF)}·{_fr(frac)} = {_pi(AF)} ≈ {Av:.2f}"),
    ]
    starts = [0, 12, 58, 80, 100]
    N = 140

    def update(i):
        u = _ease(_ph(i, 12, 56))
        phi = math.radians(th) * u
        tt = np.linspace(0, phi, max(2, int(80 * u) + 2))
        sec.set_xy(np.vstack([[0, 0], np.column_stack([r * np.cos(tt), r * np.sin(tt)])]))
        sec.set_alpha(0.75 if u > 0 else 0.0)
        r1.set_data([0, r * math.cos(phi)], [0, r * math.sin(phi)])
        sm = np.linspace(0, phi, 40)
        rs = 0.18 * r
        small.set_data(rs * np.cos(sm), rs * np.sin(sm))
        tth.set_position((0.24 * r * math.cos(phi / 2), 0.24 * r * math.sin(phi / 2)))
        tth.set_text(f"{th * u:.0f}°" if u > 0 else "")
        if i >= 80:
            arc.set_data(r * np.cos(tt), r * np.sin(tt))
        else:
            arc.set_data([], [])
        for k, (tk, tl) in enumerate(ticks):
            a = _ph(i, 60 + 4 * k, 64 + 4 * k)
            tk.set_alpha(a)
            tl.set_alpha(a if i < 80 else 0.0)
        ts.set_text(f"s = {_pi(sF)}" if i >= 84 else "")
        ta.set_text(f"A = {_pi(AF)}" if i >= 104 else "")
        tf.set_text((f"Dilim = dairenin {_fr(frac)} kadarı" if tr else f"Sector = {_fr(frac)} of the circle")
                    if i >= 100 else "")
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 7))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    out.update({"r": rnd.randint(3, 12), "theta": rnd.choice([30, 45, 60, 72, 90, 120, 135, 150, 210, 240, 270, 300])})
    return out
''',
}
EXAMPLES += [
    {"id": "geo-arc-1", "kind": "arc_sector",
     "title": ("Yay uzunluğu ve dilim alanı", "Arc length and sector area"),
     "q": ("Yarıçapı {r} birim olan bir çemberde {theta}°'lik merkez açının gördüğü yayın uzunluğunu ve "
           "daire diliminin alanını bul. Açıyı radyan olarak da yaz.",
           "In a circle of radius {r}, find the length of the arc cut off by a central angle of {theta}° and "
           "the area of the sector. Also give the angle in radians."),
     "P": {"r": 6, "theta": 120}},
    {"id": "geo-arc-2", "kind": "arc_sector", "topics": ["pizza", "word problem", "sözel problem"],
     "title": ("Pizza dilimi", "A slice of pizza"),
     "q": ("Çapı {d} cm olan bir pizzadan merkez açısı {theta}° olan bir dilim kesiliyor. "
           "Dilimin kenar (kabuk) uzunluğu ve alanı nedir?",
           "A slice with a central angle of {theta}° is cut from a pizza {d} cm across. "
           "How long is the slice's crust and what is its area?"),
     "P": {"r": 15, "theta": 45, "unit": "cm"}},
    {"id": "geo-arc-3", "kind": "arc_sector", "topics": ["sprinkler", "word problem"],
     "title": ("Döner fıskiye", "Rotating sprinkler"),
     "q": ("Bir fıskiye {r} m uzağa su atıyor ve {theta}°'lik bir açıyı tarıyor. Sulanan alan kaç m²'dir? "
           "Suyun ulaştığı en dış yayın uzunluğu nedir?",
           "A sprinkler throws water {r} m and turns through {theta}°. What area does it water, and how "
           "long is the outer arc it reaches?"),
     "P": {"r": 10, "theta": 135, "unit": "m"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["volume_3d"] = {
    "course": "geo",
    "title": ("Katı cisimlerin hacmi ve yüzey alanı", "Volume and surface area of solids"),
    "topics": ["volume", "surface area", "solids", "3d shapes", "cylinder", "cone", "sphere",
               "rectangular prism", "prism", "capacity", "hacim", "yüzey alanı", "katı cisimler",
               "silindir", "koni", "küre", "prizma", "dikdörtgenler prizması"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _finite(v):
    q = Fraction(v).denominator
    for p in (2, 5):
        while q % p == 0:
            q //= p
    return q == 1


def _d(v):
    v = Fraction(v).limit_denominator(100000)
    if v.denominator == 1:
        s = str(v.numerator)
    elif _finite(v):
        s = f"{float(v):.6f}".rstrip("0").rstrip(".")
    else:
        s = f"{v.numerator}/{v.denominator}"
    return s.replace("-", "−")


def _pi(c):
    c = Fraction(c).limit_denominator(100000)
    if c == 1:
        return "π"
    if c.denominator != 1 and not _finite(c):
        return f"{c.numerator}π/{c.denominator}"
    return _d(c) + "π"


def _g(v, nd=2):
    if abs(v - round(v)) < 1e-9:
        s = f"{int(round(v)):,}"
    else:
        s = f"{v:,.{nd}f}"
    return s.replace(",", " ")


def _lt(v):
    return f"{v:.3f}".rstrip("0").rstrip(".") if v < 100 else _g(v)


def _F(P, k):
    return Fraction(str(P[k]))


def _sqrt_exact(v):
    v = Fraction(v)
    if v.denominator != 1:
        return None
    r = math.isqrt(v.numerator)
    return r if r * r == v.numerator else None


_NAMES = {"cylinder": ("Silindir", "Cylinder"), "cone": ("Koni", "Cone"), "sphere": ("Küre", "Sphere"),
          "prism": ("Dikdörtgenler prizması", "Rectangular prism")}


def _calc(P):
    sh = P.get("shape", "cylinder")
    unit = P.get("unit", "")
    u3 = f" {unit}³" if unit else ""
    u2 = f" {unit}²" if unit else ""
    S = []
    if sh == "prism":
        l, w, h = _F(P, "l"), _F(P, "w"), _F(P, "h")
        V = l * w * h
        A = 2 * (l * w + l * h + w * h)
        Vn, An = float(V), float(A)
        S = [("Hacim: V = l · w · h (taban alanı × yükseklik)", "Volume: V = l · w · h (base area × height)"),
             (f"V = {_d(l)} · {_d(w)} · {_d(h)} = {_d(V)}{u3}", f"V = {_d(l)} · {_d(w)} · {_d(h)} = {_d(V)}{u3}"),
             ("Yüzey alanı: S = 2(lw + lh + wh)  (altı dikdörtgen yüz)",
              "Surface area: S = 2(lw + lh + wh)  (six rectangular faces)"),
             (f"S = 2({_d(l * w)} + {_d(l * h)} + {_d(w * h)}) = {_d(A)}{u2}",
              f"S = 2({_d(l * w)} + {_d(l * h)} + {_d(w * h)}) = {_d(A)}{u2}")]
        Vt, At = f"{_d(V)}{u3}", f"{_d(A)}{u2}"
        panel = ["V = l · w · h", f"V = {_d(l)}·{_d(w)}·{_d(h)}", f"V = {_d(V)}{u3}",
                 "S = 2(lw + lh + wh)", f"S = 2({_d(l * w)} + {_d(l * h)} + {_d(w * h)})", f"S = {_d(A)}{u2}"]
    elif sh == "sphere":
        r = _F(P, "r")
        Vc, Ac = Fraction(4, 3) * r ** 3, 4 * r * r
        Vn, An = float(Vc) * math.pi, float(Ac) * math.pi
        S = [("Kürenin hacmi: V = (4/3)πr³", "Volume of a sphere: V = (4/3)πr³"),
             (f"V = (4/3) · π · {_d(r)}³ = (4/3) · π · {_d(r ** 3)} = {_pi(Vc)} ≈ {_g(Vn)}{u3}",
              f"V = (4/3) · π · {_d(r)}³ = (4/3) · π · {_d(r ** 3)} = {_pi(Vc)} ≈ {_g(Vn)}{u3}"),
             ("Yüzey alanı: S = 4πr²  (aynı yarıçaplı 4 dairenin alanı)", "Surface area: S = 4πr²  (four circles of the same radius)"),
             (f"S = 4 · π · {_d(r)}² = {_pi(Ac)} ≈ {_g(An)}{u2}", f"S = 4 · π · {_d(r)}² = {_pi(Ac)} ≈ {_g(An)}{u2}")]
        Vt, At = f"{_pi(Vc)} ≈ {_g(Vn)}{u3}", f"{_pi(Ac)} ≈ {_g(An)}{u2}"
        panel = ["V = (4/3)πr³", f"V = (4/3)·π·{_d(r)}³ = {_pi(Vc)}", f"V ≈ {_g(Vn)}{u3}",
                 "S = 4πr²", f"S = 4·π·{_d(r)}² = {_pi(Ac)}", f"S ≈ {_g(An)}{u2}"]
    elif sh == "cone":
        r, h = _F(P, "r"), _F(P, "h")
        Vc = r * r * h / 3
        Vn = float(Vc) * math.pi
        l2 = r * r + h * h
        le = _sqrt_exact(l2)
        ln = math.sqrt(float(l2))
        if le is not None:
            Ac = r * r + r * le
            An = float(Ac) * math.pi
            lt = f"√{_d(l2)} = {le}"
            At = f"{_pi(r * r)} + {_pi(r * le)} = {_pi(Ac)} ≈ {_g(An)}{u2}"
            Ash = f"{_pi(Ac)} ≈ {_g(An)}{u2}"
            pl = f"S = {_pi(r * r)} + {_pi(r * le)} = {_pi(Ac)}"
        else:
            An = math.pi * (float(r * r) + float(r) * ln)
            lt = f"√{_d(l2)} ≈ {ln:.3f}"
            At = f"π · {_d(r)}² + π · {_d(r)} · {ln:.3f} ≈ {_g(An)}{u2}"
            Ash = f"≈ {_g(An)}{u2}"
            pl = f"S = π·{_d(r * r)} + π·{_d(r)}·{ln:.2f}"
        S = [("Koninin hacmi: V = (1/3)πr²h  (aynı taban ve yükseklikteki silindirin üçte biri)",
              "Volume of a cone: V = (1/3)πr²h  (one third of the cylinder with the same base and height)"),
             (f"V = (1/3) · π · {_d(r)}² · {_d(h)} = {_pi(Vc)} ≈ {_g(Vn)}{u3}",
              f"V = (1/3) · π · {_d(r)}² · {_d(h)} = {_pi(Vc)} ≈ {_g(Vn)}{u3}"),
             (f"Ana doğru (eğik yükseklik): l = √(r² + h²) = {lt}", f"Slant height: l = √(r² + h²) = {lt}"),
             (f"Yüzey alanı: S = πr² + πrl = {At}", f"Surface area: S = πr² + πrl = {At}")]
        Vt, At = f"{_pi(Vc)} ≈ {_g(Vn)}{u3}", Ash
        panel = ["V = (1/3)πr²h", f"V = (1/3)·π·{_d(r)}²·{_d(h)} = {_pi(Vc)}", f"V ≈ {_g(Vn)}{u3}",
                 f"l = √(r² + h²) = {lt}", pl, f"S {Ash}" if Ash.startswith("≈") else f"S = {Ash}"]
    else:
        r, h = _F(P, "r"), _F(P, "h")
        Vc, Ac = r * r * h, 2 * r * r + 2 * r * h
        Vn, An = float(Vc) * math.pi, float(Ac) * math.pi
        S = [("Silindirin hacmi: V = πr²h  (taban alanı × yükseklik)", "Volume of a cylinder: V = πr²h  (base area × height)"),
             (f"V = π · {_d(r)}² · {_d(h)} = {_pi(Vc)} ≈ {_g(Vn)}{u3}", f"V = π · {_d(r)}² · {_d(h)} = {_pi(Vc)} ≈ {_g(Vn)}{u3}"),
             ("Yüzey alanı: S = 2πr² (iki taban) + 2πrh (yanal yüzey)", "Surface area: S = 2πr² (two bases) + 2πrh (curved side)"),
             (f"S = {_pi(2 * r * r)} + {_pi(2 * r * h)} = {_pi(Ac)} ≈ {_g(An)}{u2}",
              f"S = {_pi(2 * r * r)} + {_pi(2 * r * h)} = {_pi(Ac)} ≈ {_g(An)}{u2}")]
        Vt, At = f"{_pi(Vc)} ≈ {_g(Vn)}{u3}", f"{_pi(Ac)} ≈ {_g(An)}{u2}"
        panel = ["V = πr²h", f"V = π·{_d(r)}²·{_d(h)} = {_pi(Vc)}", f"V ≈ {_g(Vn)}{u3}",
                 "S = 2πr² + 2πrh", f"S = {_pi(2 * r * r)} + {_pi(2 * r * h)} = {_pi(Ac)}", f"S ≈ {_g(An)}{u2}"]
    lit = ""
    if unit in ("cm", "m", "dm"):
        litres = Vn / 1000.0 if unit == "cm" else (Vn * 1000.0 if unit == "m" else Vn)
        eq = "=" if abs(litres - round(litres, 3)) < 1e-9 else "≈"
        S.append((f"Sığa (litre): {_g(Vn)}{u3} {eq} {_lt(litres)} L  (1 L = 1 dm³ = 1000 cm³)",
                  f"Capacity in litres: {_g(Vn)}{u3} {eq} {_lt(litres)} L  (1 L = 1 dm³ = 1000 cm³)"))
        if unit in ("cm", "dm"):
            lit = f" {eq} {_lt(litres)} L"
    return {"V": Vn, "A": An, "Vt": Vt, "At": At, "steps": S, "panel": panel, "lit": lit}


def solve(P):
    c = _calc(P)
    nm = _NAMES.get(P.get("shape", "cylinder"), _NAMES["cylinder"])
    return {"answer": (f"V = {c['Vt']}{c['lit']};  S = {c['At']}", f"V = {c['Vt']}{c['lit']};  S = {c['At']}"),
            "steps": c["steps"], "fmt": {"name": nm}}


def _water_vol(sh, P, z):
    if sh == "prism":
        return float(P["l"]) * float(P["w"]) * z
    r = float(P["r"])
    if sh == "sphere":
        return math.pi * z * z * (3 * r - z) / 3
    h = float(P["h"])
    if sh == "cone":
        rr = r * z / h
        return math.pi * rr * rr * z / 3
    return math.pi * r * r * z


def _box_faces(x1, y1, z1):
    v = [(0, 0, 0), (x1, 0, 0), (x1, y1, 0), (0, y1, 0), (0, 0, z1), (x1, 0, z1), (x1, y1, z1), (0, y1, z1)]
    idx = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return [[v[j] for j in f] for f in idx]


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    L = 0 if tr else 1
    sh = P.get("shape", "cylinder")
    if sh not in _NAMES:
        sh = "cylinder"
    c = _calc(P)
    unit = P.get("unit", "")
    u3 = f" {unit}³" if unit else ""
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=[1.25, 1.0], left=0.0,
                          right=0.98, top=0.98, bottom=0.02, wspace=0.02, hspace=0.04)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    info = top.text(0.02, 0.5, "", transform=top.transAxes, va="center", ha="left", fontsize=11.5,
                    color="#111827", bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    ax = fig.add_subplot(gs[1, 0], projection="3d")
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    ax.set_axis_off()
    th = np.linspace(0, 2 * np.pi, 41)
    BLUE, ORNG = "#93C5FD", "#FDBA74"
    shells = []
    if sh == "prism":
        l, w, h = float(P["l"]), float(P["w"]), float(P["h"])
        ext = (l, w, h)
        ax.set_xlim(0, l)
        ax.set_ylim(0, w)
        ax.set_zlim(0, h)
        for col in (BLUE, ORNG):
            pc = Poly3DCollection(_box_faces(l, w, h), facecolor=col, edgecolor="#1E3A8A", linewidths=1.2,
                                  alpha=0.12 if col == BLUE else 0.35)
            ax.add_collection3d(pc)
            shells.append(pc)
        top_z = h
        labs = [((l / 2, -0.08 * w, 0), f"l = {_d(Fraction(str(P['l'])))}"),
                ((l * 1.04, w / 2, 0), f"w = {_d(Fraction(str(P['w'])))}"),
                ((l * 1.04, 0, h / 2), f"h = {_d(Fraction(str(P['h'])))}")]
        dims = []
    else:
        r = float(P["r"])
        if sh == "sphere":
            h = 2 * r
            v = np.linspace(0, np.pi, 21)
            X = r * np.outer(np.sin(v), np.cos(th))
            Y = r * np.outer(np.sin(v), np.sin(th))
            Z = r - r * np.outer(np.cos(v), np.ones_like(th))
            ax.plot(r * np.cos(th), r * np.sin(th), np.full_like(th, r), color="#1E3A8A", lw=1, alpha=0.6)
            dims = [([0, r], [0, 0], [r, r])]
            labs = [((r / 2, 0, r * 1.08), f"r = {_d(Fraction(str(P['r'])))}")]
        else:
            h = float(P["h"])
            zz = np.array([0.0, h])
            if sh == "cone":
                R = np.outer(zz / h * r, np.ones_like(th))
            else:
                R = np.full((2, len(th)), r)
                ax.plot(r * np.cos(th), r * np.sin(th), np.zeros_like(th), color="#1E3A8A", lw=1.2)
            X = R * np.cos(th)
            Y = R * np.sin(th)
            Z = np.outer(zz, np.ones_like(th))
            ax.plot(r * np.cos(th), r * np.sin(th), np.full_like(th, h), color="#1E3A8A", lw=1.2)
            dims = [([0, r], [0, 0], [h, h]), ([0, 0], [0, 0], [0, h])]
            labs = [((r / 2, 0, h * 1.06), f"r = {_d(Fraction(str(P['r'])))}"),
                    ((0.06 * r, 0, h / 2), f"h = {_d(Fraction(str(P['h'])))}")]
        ext = (2 * r, 2 * r, h)
        ax.set_xlim(-r, r)
        ax.set_ylim(-r, r)
        ax.set_zlim(0, h)
        for col in (BLUE, ORNG):
            s = ax.plot_surface(X, Y, Z, color=col, alpha=0.16 if col == BLUE else 0.42, linewidth=0.3,
                                edgecolor="#93C5FD" if col == BLUE else "#FB923C", shade=False)
            shells.append(s)
        top_z = h
    try:
        ax.set_box_aspect(ext, zoom=0.88 if sh == "prism" else 1.25)
    except TypeError:
        ax.set_box_aspect(ext)
    for xs, ys, zs in dims:
        ax.plot(xs, ys, zs, "--", color="#111827", lw=1.5)
    lab3 = [ax.text(p[0], p[1], p[2], s, fontsize=11, color="#111827", fontweight="bold") for p, s in labs]
    slant = None
    if sh == "cone":
        slant, = ax.plot([0, float(P["r"])], [0, 0], [0, float(P["h"])], color="#DC2626", lw=2.4)
        tl = ax.text(0.62 * float(P["r"]), 0, 0.45 * float(P["h"]), "l", fontsize=12, color="#DC2626",
                     fontweight="bold")
    live = ax.text2D(0.03, 0.95, "", transform=ax.transAxes, fontsize=11.5, color="#1D4ED8",
                     fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#BFDBFE"))
    tx.text(0.05, 0.96, "Adım adım" if tr else "Step by step", transform=tx.transAxes, va="top",
            fontsize=11, color="#6B7280", fontweight="bold")
    arts = [tx.text(0.05, 0.86 - k * 0.11, s, transform=tx.transAxes, va="top",
                    fontsize=12 if len(s) < 24 else 10.5, color="#111827", alpha=0.0)
            for k, s in enumerate(c["panel"])]
    for k in (0, 1, 2):
        arts[k].set_color("#1D4ED8")
    for k in (3, 4, 5):
        arts[k].set_color("#C2410C")
    arts[2].set_fontweight("bold")
    arts[5].set_fontweight("bold")
    times = [24, 60, 94, 104, 116, 126]
    nm = _NAMES[sh]
    if sh == "prism":
        dtxt = f"l = {P['l']}, w = {P['w']}, h = {P['h']}"
    elif sh == "sphere":
        dtxt = f"r = {P['r']}"
    else:
        dtxt = f"r = {P['r']}, h = {P['h']}"
    fill = {"cylinder": ("su yüksekliği arttıkça hacim düzgün artar", "volume grows steadily with the water level"),
            "cone": ("koni, aynı taban ve yükseklikteki silindirin 1/3'ü kadar su alır",
                     "a cone holds 1/3 of the cylinder with the same base and height"),
            "sphere": ("küre ortasında en geniş; su orada en yavaş yükselir",
                       "the sphere is widest in the middle, where the level rises slowest"),
            "prism": ("her 1 birim yükseklik l · w kadar hacim ekler", "each unit of height adds l · w of volume")}[sh]
    narr = [
        (f"1) {nm[0]}: {dtxt}" + (f" ({unit})" if unit else ""), f"1) {nm[1]}: {dtxt}" + (f" ({unit})" if unit else "")),
        (f"2) Su dolduruluyor: {fill[0]}", f"2) Filling with water: {fill[1]}"),
        (f"3) Dolu: V = {c['Vt']}", f"3) Full: V = {c['Vt']}"),
        ("4) Yüzey alanı: cismin bütün dış yüzeyi (turuncu)", "4) Surface area: the whole outer surface (orange)"),
        (f"5) S = {c['At']}", f"5) S = {c['At']}"),
    ]
    starts = [0, 20, 94, 102, 118]
    water = []
    N = 140

    def update(i):
        ax.view_init(elev=22, azim=-62 + 0.75 * i)
        for art in water:
            art.remove()
        water.clear()
        u = _ease(_ph(i, 20, 92))
        lvl = top_z * u
        sa = i >= 102
        shells[0].set_visible(not sa)
        shells[1].set_visible(sa)
        if slant is not None:
            slant.set_visible(i >= 104)
            tl.set_visible(i >= 104)
        wa = 0.5 if not sa else 0.18
        if lvl > 1e-6 and not sa:
            if sh == "prism":
                pc = Poly3DCollection(_box_faces(float(P["l"]), float(P["w"]), lvl), facecolor="#2563EB",
                                      edgecolor="none", alpha=wa)
                ax.add_collection3d(pc)
                water.append(pc)
            else:
                r = float(P["r"])
                tt = np.linspace(0, 2 * np.pi, 33)
                if sh == "sphere":
                    vl = math.acos(max(-1.0, min(1.0, 1 - lvl / r)))
                    vv = np.linspace(0, vl, 9)
                    X = r * np.outer(np.sin(vv), np.cos(tt))
                    Y = r * np.outer(np.sin(vv), np.sin(tt))
                    Z = r - r * np.outer(np.cos(vv), np.ones_like(tt))
                    rt = r * math.sin(vl)
                else:
                    h = float(P["h"])
                    rr = np.array([0.0, r * lvl / h]) if sh == "cone" else np.array([r, r])
                    X = np.outer(rr, np.cos(tt))
                    Y = np.outer(rr, np.sin(tt))
                    Z = np.outer(np.array([0.0, lvl]), np.ones_like(tt))
                    rt = rr[1]
                water.append(ax.plot_surface(X, Y, Z, color="#2563EB", alpha=wa, linewidth=0, shade=False))
                rg = np.array([0.0, rt])
                water.append(ax.plot_surface(np.outer(rg, np.cos(tt)), np.outer(rg, np.sin(tt)),
                                             np.full((2, len(tt)), lvl), color="#1D4ED8", alpha=wa + 0.1,
                                             linewidth=0, shade=False))
        vw = _water_vol(sh, P, lvl)
        live.set_text((f"Su: {_g(vw)}{u3}" if tr else f"Water: {_g(vw)}{u3}") if i < 102 else
                      (f"S = {c['At']}" if i >= 118 else ("Yüzey alanı" if tr else "Surface area")))
        live.set_color("#1D4ED8" if i < 102 else "#C2410C")
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 7))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][L])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    sh = P.get("shape", "cylinder")
    if sh == "prism":
        out.update({"l": rnd.choice([3, 4, 5, 6, 8, 10]), "w": rnd.choice([2, 3, 4, 5]), "h": rnd.choice([2, 3, 4, 5, 6])})
    elif sh == "sphere":
        out["r"] = rnd.choice([2, 3, 4, 5, 6, 9, 10])
    elif sh == "cone":
        r, h = rnd.choice([(3, 4), (6, 8), (5, 12), (9, 12), (8, 6), (4, 3)])
        out.update({"r": r, "h": h})
    else:
        out.update({"r": rnd.choice([2, 3, 4, 5]), "h": rnd.choice([3, 4, 5, 6, 8, 10])})
    return out
''',
}
EXAMPLES += [
    {"id": "geo-vol-1", "kind": "volume_3d", "topics": ["cylinder", "silindir", "word problem", "tank"],
     "title": ("Silindir su deposu", "Cylindrical water tank"),
     "q": ("Yarıçapı {r} m, yüksekliği {h} m olan silindir biçimli bir su deposu kaç m³ su alır? "
           "Deponun tüm dış yüzeyi (tabanlar dahil) kaç m²'dir?",
           "A cylindrical water tank has radius {r} m and height {h} m. How many m³ of water does it hold, "
           "and what is its total surface area (including both ends)?"),
     "P": {"shape": "cylinder", "r": 3, "h": 5, "unit": "m"}},
    {"id": "geo-vol-2", "kind": "volume_3d", "topics": ["cone", "koni", "slant height"],
     "title": ("Koni biçimli kâğıt bardak", "Cone-shaped paper cup"),
     "q": ("Taban yarıçapı {r} cm, yüksekliği {h} cm olan koni biçimli bir kâğıt bardağın hacmini ve "
           "(taban dahil) yüzey alanını bul.",
           "A cone-shaped paper cup has base radius {r} cm and height {h} cm. Find its volume and its surface "
           "area (including the base)."),
     "P": {"shape": "cone", "r": 3, "h": 4, "unit": "cm"}},
    {"id": "geo-vol-3", "kind": "volume_3d", "topics": ["sphere", "küre", "ball"],
     "title": ("Kürenin hacmi ve yüzeyi", "Volume and surface of a sphere"),
     "q": ("Yarıçapı {r} cm olan bir topun hacmi ve yüzey alanı nedir?",
           "A ball has radius {r} cm. What are its volume and surface area?"),
     "P": {"shape": "sphere", "r": 6, "unit": "cm"}},
    {"id": "geo-vol-4", "kind": "volume_3d", "topics": ["rectangular prism", "aquarium", "akvaryum", "prizma"],
     "title": ("Akvaryum (dikdörtgenler prizması)", "Aquarium (rectangular prism)"),
     "q": ("Boyutları {l} cm × {w} cm × {h} cm olan bir akvaryum kaç litre su alır? Camların toplam alanı "
           "(kapak dahil) kaç cm²'dir?",
           "An aquarium measures {l} cm × {w} cm × {h} cm. How many litres of water does it hold, and what is "
           "its total glass area (lid included)?"),
     "P": {"shape": "prism", "l": 60, "w": 30, "h": 40, "unit": "cm"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["unit_circle"] = {
    "course": "geo",
    "title": ("Birim çember ve özel açılar", "Unit circle and special angles"),
    "topics": ["unit circle", "trigonometric functions", "reference angle", "special angles",
               "sine and cosine", "quadrants", "exact values", "radians and degrees", "trigonometry",
               "birim çember", "trigonometrik fonksiyonlar", "referans açı", "özel açılar", "trigonometri",
               "sinüs", "kosinüs", "bölgeler"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Polygon, Rectangle, Circle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _n(v, nd=2):
    v = float(v)
    s = str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s.replace("-", "−")


_EX = {0: ("1", "0", "0"), 30: ("√3/2", "1/2", "√3/3"), 45: ("√2/2", "√2/2", "1"),
       60: ("1/2", "√3/2", "√3"), 90: ("0", "1", None)}
_ROM = {1: "I", 2: "II", 3: "III", 4: "IV"}


def _sg(sign, txt):
    if txt == "0":
        return "0"
    return ("−" if sign < 0 else "") + txt


def _info(deg):
    t = float(deg) % 360.0
    if abs(t - round(t)) < 1e-9:
        t = float(int(round(t)) % 360)
    if t in (0.0, 90.0, 180.0, 270.0):
        q = 0
    elif t < 90:
        q = 1
    elif t < 180:
        q = 2
    elif t < 270:
        q = 3
    else:
        q = 4
    ref = {0: min(t % 180, 180 - t % 180) if t % 180 else 0.0, 1: t, 2: 180 - t, 3: t - 180, 4: 360 - t}[q]
    if q == 0:
        ref = 90.0 if t in (90.0, 270.0) else 0.0
    sx = -1 if 90 < t < 270 else 1
    sy = -1 if t > 180 else 1
    c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
    key = int(round(ref)) if abs(ref - round(ref)) < 1e-9 else None
    if key in _EX:
        bc, bs, bt = _EX[key]
        ct, st = _sg(sx, bc), _sg(sy, bs)
        tt = None if bt is None else _sg(sx * sy, bt)
        exact = True
    else:
        ct, st = f"{c:.4f}".replace("-", "−"), f"{s:.4f}".replace("-", "−")
        tt = None if abs(c) < 1e-12 else f"{s / c:.4f}".replace("-", "−")
        exact = False
    return {"t": t, "q": q, "ref": ref, "sx": sx, "sy": sy, "c": c, "s": s, "ct": ct, "st": st, "tt": tt,
            "exact": exact}


def _reftext(d):
    t, q, ref = d["t"], d["q"], d["ref"]
    if q == 1:
        return f"θ' = θ = {_n(ref)}°"
    if q == 2:
        return f"θ' = 180° − {_n(t)}° = {_n(ref)}°"
    if q == 3:
        return f"θ' = {_n(t)}° − 180° = {_n(ref)}°"
    if q == 4:
        return f"θ' = 360° − {_n(t)}° = {_n(ref)}°"
    return f"θ' = {_n(ref)}°"


def solve(P):
    deg = float(P["deg"])
    d = _info(deg)
    D = _n(deg)
    eq = "=" if d["exact"] else "≈"
    if d["q"]:
        qtxt = (f"θ = {D}° → {_ROM[d['q']]}. bölge", f"θ = {D}° lies in quadrant {_ROM[d['q']]}")
    else:
        qtxt = (f"θ = {D}° bir eksen üzerinde", f"θ = {D}° lies on an axis")
    steps = []
    if not (0 <= deg < 360):
        steps.append((f"{D}° ile {_n(d['t'])}° aynı yeri gösterir (360°'lik tam turlar atılır).",
                      f"{D}° and {_n(d['t'])}° end in the same place (drop full 360° turns)."))
    steps += [
        qtxt,
        (f"Referans açı (x eksenine olan dar açı): {_reftext(d)}",
         f"Reference angle (acute angle to the x-axis): {_reftext(d)}"),
        (f"İşaretler: x = cos θ {'<' if d['sx'] < 0 else '>'} 0, y = sin θ {'<' if d['sy'] < 0 else '>'} 0"
         if d["q"] else "Eksen üzerinde koordinatlardan biri 0'dır.",
         f"Signs: x = cos θ {'<' if d['sx'] < 0 else '>'} 0, y = sin θ {'<' if d['sy'] < 0 else '>'} 0"
         if d["q"] else "On an axis one of the coordinates is 0."),
        (f"cos {D}° {eq} {d['ct']},   sin {D}° {eq} {d['st']}", f"cos {D}° {eq} {d['ct']},   sin {D}° {eq} {d['st']}"),
        ((f"tan {D}° = sin/cos {eq} {d['tt']}" if d["tt"] is not None else f"tan {D}° tanımsız (cos = 0)"),
         (f"tan {D}° = sin/cos {eq} {d['tt']}" if d["tt"] is not None else f"tan {D}° is undefined (cos = 0)")),
        (f"Birim çember noktası: P({d['ct']}, {d['st']})", f"Point on the unit circle: P({d['ct']}, {d['st']})"),
    ]
    tn = d["tt"] if d["tt"] is not None else ("tanımsız", "undefined")
    if isinstance(tn, tuple):
        ans = (f"cos {D}° {eq} {d['ct']}, sin {D}° {eq} {d['st']}, tan {D}° {tn[0]}",
               f"cos {D}° {eq} {d['ct']}, sin {D}° {eq} {d['st']}, tan {D}° {tn[1]}")
    else:
        a = f"cos {D}° {eq} {d['ct']}, sin {D}° {eq} {d['st']}, tan {D}° {eq} {tn}"
        ans = (a, a)
    return {"answer": ans, "steps": steps, "fmt": {"rad": f"{math.radians(deg):.4f}"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    deg = float(P["deg"])
    d = _info(deg)
    D = _n(deg)
    eq = "=" if d["exact"] else "≈"
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=[1.3, 1.0], left=0.02,
                          right=0.98, top=0.98, bottom=0.03, wspace=0.04, hspace=0.06)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left", fontsize=11.5,
                    color="#111827", bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.42, 1.42)
    ax.plot([-1.4, 1.4], [0, 0], color="#374151", lw=1)
    ax.plot([0, 0], [-1.35, 1.35], color="#374151", lw=1)
    ax.add_patch(Circle((0, 0), 1, fc="none", ec="#6B7280", lw=1.6))
    for a in range(0, 360, 15):
        if a % 30 == 0 or a % 45 == 0:
            ax.plot([math.cos(math.radians(a))], [math.sin(math.radians(a))], "o", color="#D1D5DB", ms=4)
    for x, y, s in ((1.04, -0.09, "1"), (-1.04, -0.09, "−1"), (0.05, 1.04, "1"), (0.05, -1.1, "−1")):
        ax.text(x, y, s, fontsize=9, color="#6B7280", ha="center" if abs(x) > 0.5 else "left")
    for q, (x, y) in {1: (1.18, 1.22), 2: (-1.18, 1.22), 3: (-1.18, -1.28), 4: (1.18, -1.28)}.items():
        sg = {1: "(+, +)", 2: "(−, +)", 3: "(−, −)", 4: "(+, −)"}[q]
        ax.text(x, y, f"{_ROM[q]} {sg}", ha="center", va="center", fontsize=9.5,
                color="#7C3AED" if q == d["q"] else "#9CA3AF", fontweight="bold" if q == d["q"] else "normal")
    refw = Polygon(np.zeros((3, 2)), closed=True, fc="#BBF7D0", ec="#16A34A", lw=1.2, alpha=0.0, zorder=2)
    ax.add_patch(refw)
    rad, = ax.plot([], [], color="#2563EB", lw=2.4, zorder=4)
    cseg, = ax.plot([], [], color="#2563EB", lw=5, solid_capstyle="butt", zorder=3, alpha=0.6)
    sseg, = ax.plot([], [], color="#E07B39", lw=5, solid_capstyle="butt", zorder=3, alpha=0.8)
    arcl, = ax.plot([], [], color="#DC2626", lw=1.8, zorder=4)
    pt, = ax.plot([], [], "o", color="#DC2626", ms=9, zorder=6)
    tth = ax.text(0, 0, "", fontsize=10.5, color="#DC2626", ha="center", va="center", zorder=7)
    tP = ax.text(0, 0, "", fontsize=11, color="#111827", fontweight="bold", zorder=7,
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#E5E7EB", alpha=0.9))
    wb = dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8)
    tc = ax.text(0, 0, "", fontsize=10, color="#1D4ED8", ha="center", zorder=7, bbox=wb)
    ts = ax.text(0, 0, "", fontsize=10, color="#C2410C", va="center", zorder=7, bbox=wb)
    tref = ax.text(0, 0, "", fontsize=10.5, color="#15803D", fontweight="bold", ha="center", va="center", zorder=7)
    T = math.radians(deg)
    qn = _ROM.get(d["q"], "")
    lines = [((f"θ = {D}°: {qn}. bölge" if tr else f"θ = {D}°: quadrant {qn}") if d["q"] else
              (f"θ = {D}°: eksen üzerinde" if tr else f"θ = {D}°: on an axis")),
             ("Referans: " if tr else "Reference: ") + _reftext(d).replace("θ' = ", ""),
             f"cos {D}° {eq} {d['ct']}",
             f"sin {D}° {eq} {d['st']}",
             (f"tan {D}° {eq} {d['tt']}" if d["tt"] is not None else
              (f"tan {D}° tanımsız" if tr else f"tan {D}° undefined"))]
    tx.text(0.05, 0.96, "Adım adım" if tr else "Step by step", transform=tx.transAxes, va="top",
            fontsize=11, color="#6B7280", fontweight="bold")
    arts = [tx.text(0.05, 0.86 - k * 0.11, s, transform=tx.transAxes, va="top",
                    fontsize=12 if len(s) < 26 else 10.5, color="#111827", alpha=0.0) for k, s in enumerate(lines)]
    arts[2].set_color("#1D4ED8")
    arts[3].set_color("#C2410C")
    arts[4].set_color("#7C3AED")
    for t in arts[2:]:
        t.set_fontweight("bold")
    times = [58, 66, 84, 92, 106]
    narr = [
        ("1) Birim çember: yarıçap 1; noktanın koordinatları (cos θ, sin θ)",
         "1) Unit circle: radius 1; a point's coordinates are (cos θ, sin θ)"),
        (f"2) Yarıçap 0°'den {D}°'ye dönüyor; mavi = cos θ (x), turuncu = sin θ (y)",
         f"2) The radius turns from 0° to {D}°; blue = cos θ (x), orange = sin θ (y)"),
        ((f"3) {qn}. bölge; referans açı {_reftext(d)}" if d["q"] else f"3) Eksen açısı; {_reftext(d)}"),
         (f"3) Quadrant {qn}; reference angle {_reftext(d)}" if d["q"] else f"3) Axis angle; {_reftext(d)}")),
        ((f"4) Tam değerler: P({d['ct']}, {d['st']})" if d["exact"] else f"4) Yaklaşık değerler: P({d['ct']}, {d['st']})"),
         (f"4) Exact values: P({d['ct']}, {d['st']})" if d["exact"] else f"4) Approximate values: P({d['ct']}, {d['st']})")),
        (("5) tan θ = sin θ / cos θ " + (f"{eq} {d['tt']}" if d["tt"] is not None else "tanımsız")),
         ("5) tan θ = sin θ / cos θ " + (f"{eq} {d['tt']}" if d["tt"] is not None else "is undefined"))),
    ]
    starts = [0, 10, 58, 82, 104]
    N = 140

    def update(i):
        u = _ease(_ph(i, 10, 54))
        phi = T * u
        c, s = math.cos(phi), math.sin(phi)
        rad.set_data([0, c], [0, s])
        pt.set_data([c], [s])
        cseg.set_data([0, c], [0, 0])
        sseg.set_data([c, c], [0, s])
        n = max(2, int(60 * abs(u)) + 2)
        aa = np.linspace(0, phi, n)
        rr = 0.17 + 0.035 * aa / (2 * math.pi) * np.sign(T if T else 1)
        arcl.set_data(rr * np.cos(aa), rr * np.sin(aa))
        tth.set_position((0.3 * math.cos(phi / 2) if abs(phi) < 2 * math.pi else 0.3, 0.3 * math.sin(phi / 2)))
        tth.set_text(f"{math.degrees(phi):.0f}°" if u > 0 else "")
        ex = i >= 84 and d["exact"]
        cl = d["ct"] if ex else f"{c:.2f}".replace("-", "−")
        sl = d["st"] if ex else f"{s:.2f}".replace("-", "−")
        tP.set_text(f"P({cl}, {sl})")
        tP.set_position((max(-0.98, min(0.98, 1.12 * c)), 1.1 * s + (0.07 if s >= -1e-9 else -0.07)))
        tP.set_ha("center")
        tP.set_va("bottom" if s >= -1e-9 else "top")
        tc.set_text(f"cos θ = {cl}" if u > 0.02 else "")
        tc.set_position((c / 2, -0.13 if s >= 0 else 0.07))
        ts.set_text(f"sin θ = {sl}" if u > 0.02 else "")
        ts.set_position((c + (0.04 if c >= 0 else -0.04), s / 2))
        ts.set_ha("left" if c >= 0 else "right")
        g = _ph(i, 58, 66)
        if g > 0 and d["q"]:
            base = {1: 0.0, 2: math.pi, 3: math.pi, 4: 2 * math.pi}[d["q"]]
            tt = math.radians(d["t"])
            ang = np.linspace(min(base, tt), max(base, tt), 30)
            rr2 = 0.42
            refw.set_xy(np.vstack([[0, 0], np.column_stack([rr2 * np.cos(ang), rr2 * np.sin(ang)])]))
            refw.set_alpha(0.75 * g)
            m = (base + tt) / 2
            tref.set_position((0.58 * math.cos(m), 0.58 * math.sin(m)))
            tref.set_text(f"θ' = {_n(d['ref'])}°")
        else:
            refw.set_alpha(0.0)
            tref.set_text("")
        for t, s0 in zip(arts, times):
            t.set_alpha(_ph(i, s0, s0 + 7))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    q = int((float(P["deg"]) % 360) // 90)
    pool = [v + 90 * q for v in (30, 45, 60) if v + 90 * q != float(P["deg"]) % 360]
    out["deg"] = rnd.choice(pool)
    return out
''',
}
EXAMPLES += [
    {"id": "geo-uc-1", "kind": "unit_circle",
     "title": ("II. bölgede bir açı", "An angle in quadrant II"),
     "q": ("Birim çemberi kullanarak cos {deg}°, sin {deg}° ve tan {deg}° değerlerini tam olarak bul.",
           "Use the unit circle to find the exact values of cos {deg}°, sin {deg}° and tan {deg}°."),
     "P": {"deg": 150}},
    {"id": "geo-uc-2", "kind": "unit_circle",
     "title": ("III. bölge ve referans açı", "Quadrant III and the reference angle"),
     "q": ("{deg}° hangi bölgededir? Referans açısını bul ve sin, cos, tan değerlerini yaz.",
           "Which quadrant is {deg}° in? Find its reference angle and the values of sin, cos and tan."),
     "P": {"deg": 225}},
    {"id": "geo-uc-3", "kind": "unit_circle", "topics": ["coterminal", "eş uçlu açı"],
     "title": ("IV. bölgede özel açı", "A special angle in quadrant IV"),
     "q": ("Birim çemberde {deg}°'lik açının uç noktası P(x, y)'nin koordinatlarını ve tan {deg}° değerini bul.",
           "Find the coordinates of the point P(x, y) where the {deg}° angle meets the unit circle, and tan {deg}°."),
     "P": {"deg": 300}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["sine_wave"] = {
    "course": "geo",
    "title": ("Sinüs ve kosinüs grafikleri", "Graphs of sine and cosine"),
    "topics": ["sine graph", "cosine graph", "graphing sine and cosine", "amplitude", "period",
               "phase shift", "midline", "vertical shift", "sinusoidal", "trigonometric graphs",
               "periodic functions", "sinüs grafiği", "kosinüs grafiği", "genlik", "periyot", "faz kayması",
               "trigonometrik fonksiyonların grafikleri"],
    "code": r'''
import math
import numpy as np
import sympy as sp
from matplotlib.patches import Circle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ex(v):
    return sp.nsimplify(sp.sympify(str(v)), [sp.pi])


def _s(e):
    t = sp.sstr(sp.nsimplify(e, [sp.pi]))
    return t.replace("*pi", "π").replace("pi", "π").replace("*", "·").replace("-", "−")


def _num(e):
    t = _s(e)
    return f"({t})" if ("/" in t or "π" in t) else t


def _vals(P):
    return _ex(P["A"]), _ex(P["B"]), _ex(P.get("C", 0)), _ex(P.get("D", 0))


def _eq(P):
    A, B, C, D = _vals(P)
    f = "cos" if P.get("func", "sin") == "cos" else "sin"
    v = P.get("var", "x")
    yn = P.get("yname", "y")
    a = "" if A == 1 else ("−" if A == -1 else _s(A))
    if a and ("/" in a or "π" in a):
        a = f"({a})"
    b = "" if B == 1 else ("−" if B == -1 else _num(B))
    if C == 0:
        inner = f"{b}{v}"
    else:
        xc = f"{v} − {_s(C)}" if C > 0 else f"{v} + {_s(-C)}"
        inner = f"{b}({xc})" if b else xc
    dd = "" if D == 0 else (f" + {_s(D)}" if D > 0 else f" − {_s(-D)}")
    return f"{yn} = {a}{f}({inner}){dd}"


def solve(P):
    A, B, C, D = _vals(P)
    T = sp.nsimplify(2 * sp.pi / sp.Abs(B))
    f = "cos" if P.get("func", "sin") == "cos" else "sin"
    v = P.get("var", "x")
    eq = _eq(P)
    amp = sp.Abs(A)
    steps = [
        (f"{eq}  ⇒  genel biçim y = A·{f}(B({v} − C)) + D:  A = {_s(A)}, B = {_s(B)}, C = {_s(C)}, D = {_s(D)}",
         f"{eq}  ⇒  general form y = A·{f}(B({v} − C)) + D:  A = {_s(A)}, B = {_s(B)}, C = {_s(C)}, D = {_s(D)}"),
        (f"Genlik = |A| = {_s(amp)}" + ("  (A < 0: grafik orta çizgiye göre ters döner)" if A < 0 else ""),
         f"Amplitude = |A| = {_s(amp)}" + ("  (A < 0: the graph is flipped about the midline)" if A < 0 else "")),
        (f"Periyot T = 2π / |B| = 2π / {_num(sp.Abs(B))} = {_s(T)}", f"Period T = 2π / |B| = 2π / {_num(sp.Abs(B))} = {_s(T)}"),
        ((f"Faz kayması: C = {_s(C)} ⇒ grafik {_s(sp.Abs(C))} birim {'sağa' if C > 0 else 'sola'} kayar"
          if C != 0 else "Faz kayması yok (C = 0)"),
         (f"Phase shift: C = {_s(C)} ⇒ the graph moves {_s(sp.Abs(C))} to the {'right' if C > 0 else 'left'}"
          if C != 0 else "No phase shift (C = 0)")),
        (f"Orta çizgi y = D = {_s(D)};  maks = D + |A| = {_s(D + amp)},  min = D − |A| = {_s(D - amp)}",
         f"Midline y = D = {_s(D)};  max = D + |A| = {_s(D + amp)},  min = D − |A| = {_s(D - amp)}"),
    ]
    sh = (_s(C) + (" sağa" if C > 0 else " sola")) if C != 0 else "0"
    she = (_s(C) + (" right" if C > 0 else " left")) if C != 0 else "0"
    ans = (f"Genlik {_s(amp)}, periyot {_s(T)}, faz kayması {sh}, orta çizgi y = {_s(D)}",
           f"Amplitude {_s(amp)}, period {_s(T)}, phase shift {she}, midline y = {_s(D)}")
    return {"answer": ans, "steps": steps, "fmt": {"eq": eq, "T": _s(T)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    A, B, C, D = _vals(P)
    if B == 0:
        B = sp.Integer(1)
    Af, Bf, Cf, Df = float(A), float(B), float(C), float(D)
    amp = abs(Af) if Af != 0 else 1.0
    T = sp.nsimplify(2 * sp.pi / sp.Abs(B))
    Tf = float(T)
    cosf = P.get("func", "sin") == "cos"
    eq = _eq(P)
    off = (math.pi / 2 if cosf else 0.0) + (math.pi if Af < 0 else 0.0)
    lo = min(0.0, Cf)
    hi = max(0.0, Cf) + 2 * Tf
    xs = np.linspace(lo, hi, 600)
    fn = np.cos if cosf else np.sin
    ys = Df + Af * fn(Bf * (xs - Cf))
    ylo, yhi = Df - amp, Df + amp
    if 0 < ylo < 1.2 * amp:
        ylo = 0.0
    if -1.2 * amp < yhi < 0:
        yhi = 0.0
    pad = 0.38 * amp
    Y0, Y1 = ylo - pad, yhi + pad
    gs = fig.add_gridspec(3, 2, height_ratios=[0.13, 1.0, 0.42], width_ratios=[1.0, 1.9], left=0.03,
                          right=0.95, top=0.98, bottom=0.02, wspace=0.03, hspace=0.12)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    info = top.text(0.0, 0.5, "", transform=top.transAxes, va="center", ha="left", fontsize=11.5,
                    color="#111827", bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    axc = fig.add_subplot(gs[1, 0])
    ax = fig.add_subplot(gs[1, 1])
    bt = fig.add_subplot(gs[2, :])
    bt.axis("off")
    for a in (axc, ax):
        a.set_ylim(Y0, Y1)
    pos = axc.get_position()
    W, H = fig.get_size_inches()
    xr = (Y1 - Y0) * (pos.width * W) / (pos.height * H) / 2
    axc.set_xlim(-xr, xr)
    axc.axis("off")
    ax.set_xlim(lo - 0.02 * (hi - lo), hi + 0.02 * (hi - lo))
    ax.yaxis.tick_right()
    ax.tick_params(labelsize=8.5)
    ax.grid(alpha=0.25)
    ax.axhline(0, color="#374151", lw=1)
    if lo <= 0 <= hi:
        ax.axvline(0, color="#374151", lw=1)
    st = T / 4
    k0 = int(math.ceil(lo / float(st) - 1e-9))
    k1 = int(math.floor(hi / float(st) + 1e-9))
    tks = [k * st for k in range(k0, k1 + 1)]
    ax.set_xticks([float(t) for t in tks])
    ax.set_xticklabels([_s(t) if t != 0 else "0" for t in tks], fontsize=8)
    for a in (axc, ax):
        a.axhline(Df, color="#6B7280", lw=1.2, ls="--")
    axc.add_patch(Circle((0, Df), amp, fc="#EFF6FF", ec="#2563EB", lw=1.8))
    for yy in (Df - amp, Df + amp):
        axc.text(-xr * 0.98, yy, _s(sp.nsimplify(yy, [sp.pi])) if abs(yy - round(yy)) > 1e-9 else str(int(round(yy))),
                 fontsize=8, color="#6B7280", va="center")
    band = [ax.axhline(Df + amp, color="#9CA3AF", lw=0.9, ls=":"), ax.axhline(Df - amp, color="#9CA3AF", lw=0.9, ls=":")]
    curve, = ax.plot([], [], color="#2563EB", lw=2.6, zorder=4)
    pc, = ax.plot([], [], "o", color="#DC2626", ms=8, zorder=6)
    rad, = axc.plot([], [], color="#111827", lw=1.8, zorder=4)
    pw, = axc.plot([], [], "o", color="#DC2626", ms=8, zorder=6)
    con1, = axc.plot([], [], "--", color="#DC2626", lw=1, zorder=3)
    con2, = ax.plot([], [], "--", color="#DC2626", lw=1, zorder=3)
    ttl = ax.text(0.99, 0.97, eq, transform=ax.transAxes, ha="right", va="top", fontsize=12, color="#1E3A8A",
                  fontweight="bold", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#BFDBFE"), zorder=8)
    tmid = ax.text(hi, Df + 0.05 * amp, "", ha="right", va="bottom", fontsize=9, color="#4B5563", zorder=7)
    i0 = int(np.searchsorted(xs, Cf))
    win = (xs >= Cf + 0.05 * Tf) & (xs <= Cf + 1.05 * Tf)
    xm = float(xs[win][np.argmax(ys[win])]) if win.any() else float(xs[np.argmax(ys)])
    arr_a = ax.annotate("", xy=(xm, Df + amp), xytext=(xm, Df),
                        arrowprops=dict(arrowstyle="<->", color="#DC2626", lw=1.8), zorder=7)
    ta = ax.text(xm + 0.012 * (hi - lo), Df + amp / 2, "", fontsize=10, color="#DC2626", fontweight="bold",
                 va="center", zorder=7, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    yb = Df - amp - 0.17 * amp
    arr_t = ax.annotate("", xy=(Cf + Tf, yb), xytext=(Cf, yb),
                        arrowprops=dict(arrowstyle="<->", color="#16A34A", lw=1.8), zorder=7)
    tT = ax.text(Cf + Tf / 2, yb - 0.04 * amp, "", fontsize=10, color="#15803D", fontweight="bold", ha="center",
                 va="top", zorder=7)
    yc = Df + amp + 0.17 * amp
    arr_c = ax.annotate("", xy=(Cf, yc), xytext=(0, yc),
                        arrowprops=dict(arrowstyle="->", color="#7C3AED", lw=1.8), zorder=7)
    tC = ax.text(Cf / 2, yc + 0.04 * amp, "", fontsize=10, color="#6D28D9", fontweight="bold", ha="center",
                 va="bottom", zorder=7)
    cdot, = ax.plot([], [], "D", color="#7C3AED", ms=7, zorder=7)
    for art in (arr_a, arr_t, arr_c):
        art.set_visible(False)
    Tt = _s(T)
    cells = [((f"Genlik |A| = {_s(sp.Abs(A))}" if tr else f"Amplitude |A| = {_s(sp.Abs(A))}"), 0.0, 0.72, 112, "#DC2626"),
             ((f"Periyot T = 2π/|B| = {Tt}" if tr else f"Period T = 2π/|B| = {Tt}"), 0.34, 0.72, 122, "#15803D"),
             (((f"Faz kayması {_s(sp.Abs(C))} " + ("sağa" if C > 0 else "sola")) if C != 0 else "Faz kayması yok")
              if tr else ((f"Phase shift {_s(sp.Abs(C))} " + ("right" if C > 0 else "left")) if C != 0 else "No phase shift"),
              0.68, 0.72, 132, "#6D28D9"),
             ((f"Orta çizgi y = {_s(D)}" if tr else f"Midline y = {_s(D)}"), 0.0, 0.25, 136, "#374151"),
             ((f"Maks = {_s(D + sp.Abs(A))}, Min = {_s(D - sp.Abs(A))}" if tr else
               f"Max = {_s(D + sp.Abs(A))}, Min = {_s(D - sp.Abs(A))}"), 0.34, 0.25, 140, "#374151")]
    arts = []
    for s, x, y, t0, col in cells:
        arts.append((bt.text(x + 0.01, y, s, transform=bt.transAxes, fontsize=11.5, va="center", color=col,
                             fontweight="bold", alpha=0.0), t0))
    narr = [
        (f"1) {eq}: dönen noktanın yüksekliği", f"1) {eq}: the height of a turning point"),
        ("2) Nokta çemberde döndükçe yüksekliği sağdaki grafiğe aktarılıyor",
         "2) As the point turns on the circle its height is copied to the graph"),
        (f"3) Genlik |A| = {_s(sp.Abs(A))}: orta çizgiden en büyük uzaklık",
         f"3) Amplitude |A| = {_s(sp.Abs(A))}: the largest distance from the midline"),
        (f"4) Periyot T = 2π/|B| = {Tt}: bir tam tur (bir dalga)", f"4) Period T = 2π/|B| = {Tt}: one full turn (one wave)"),
        ((f"5) Faz kayması {_s(C)}, orta çizgi y = {_s(D)}" if C != 0 else f"5) Faz kayması yok, orta çizgi y = {_s(D)}"),
         (f"5) Phase shift {_s(C)}, midline y = {_s(D)}" if C != 0 else f"5) No phase shift, midline y = {_s(D)}")),
    ]
    starts = [0, 12, 110, 120, 130]
    N = 150

    def update(i):
        p = _ph(i, 12, 106)
        m = max(2, int(p * (len(xs) - 1)) + 1)
        curve.set_data(xs[:m], ys[:m])
        xc, yv = xs[m - 1], ys[m - 1]
        psi = Bf * (xc - Cf) + off
        cx, cy = amp * math.cos(psi), Df + amp * math.sin(psi)
        rad.set_data([0, cx], [Df, cy])
        pw.set_data([cx], [cy])
        live = i < 108
        pc.set_data([xc], [yv]) if live else pc.set_data([], [])
        con1.set_data([cx, xr], [cy, cy]) if live else con1.set_data([], [])
        con2.set_data([lo - 0.02 * (hi - lo), xc], [yv, yv]) if live else con2.set_data([], [])
        tmid.set_text(("orta çizgi" if tr else "midline") if i >= 4 else "")
        arr_a.set_visible(i >= 110)
        ta.set_text(f"|A| = {_s(sp.Abs(A))}" if i >= 110 else "")
        arr_t.set_visible(i >= 120)
        tT.set_text(f"T = {Tt}" if i >= 120 else "")
        arr_c.set_visible(i >= 130 and C != 0)
        tC.set_text((f"C = {_s(C)}" if C != 0 else "") if i >= 130 else "")
        if i >= 130:
            cdot.set_data([Cf], [Df + Af * (1.0 if cosf else 0.0)])
        else:
            cdot.set_data([], [])
        for art, t0 in arts:
            art.set_alpha(_ph(i, t0, t0 + 6))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k][0 if tr else 1])
        return []

    return N, update


def vary(P, rnd):
    out = dict(P)
    if "pi" in str(P.get("B", "")):
        T = rnd.choice([4, 6, 8, 10, 12])
        amp = rnd.choice([2, 3, 4, 5, 10, 15])
        out.update({"A": amp * (-1 if float(_ex(P["A"])) < 0 else 1), "B": f"pi/{T // 2}",
                    "C": rnd.choice([0, 0, 1, 2]), "D": amp + rnd.choice([1, 2, 3])})
        return out
    out.update({"A": rnd.choice([1, 2, 3, -2, 0.5]), "B": rnd.choice([1, 2, 3, 0.5]),
                "C": rnd.choice(["0", "pi/4", "pi/2", "pi/6", "-pi/3"]), "D": rnd.choice([-2, -1, 0, 1, 2, 3])})
    return out
''',
}
EXAMPLES += [
    {"id": "geo-sine-1", "kind": "sine_wave",
     "title": ("Genlik, periyot, faz kayması", "Amplitude, period and phase shift"),
     "q": ("{eq} fonksiyonunun genliğini, periyodunu, faz kaymasını ve orta çizgisini bul; grafiğini çiz.",
           "Find the amplitude, period, phase shift and midline of {eq}, and sketch its graph."),
     "P": {"A": 2, "B": 2, "C": "pi/4", "D": 1, "func": "sin"}},
    {"id": "geo-sine-2", "kind": "sine_wave",
     "title": ("Uzun periyotlu kosinüs", "A stretched cosine"),
     "q": ("{eq} grafiğinin periyodu ve en büyük / en küçük değerleri nedir?",
           "What are the period and the maximum / minimum values of {eq}?"),
     "P": {"A": 3, "B": 0.5, "C": 0, "D": -1, "func": "cos"}},
    {"id": "geo-sine-3", "kind": "sine_wave",
     "topics": ["ferris wheel", "dönme dolap", "modeling", "word problem", "sözel problem"],
     "title": ("Dönme dolap modeli", "Ferris wheel model"),
     "q": ("Bir dönme dolapta yolcunun yerden yüksekliği (m) t dakika sonra {eq} ile veriliyor. Dolabın "
           "yarıçapı, merkezinin yüksekliği ve bir turun süresi nedir?",
           "A rider's height above the ground (m) after t minutes on a Ferris wheel is {eq}. What are the "
           "wheel's radius, the height of its centre, and the time for one turn?"),
     "P": {"A": -20, "B": "pi/4", "C": 0, "D": 22, "func": "cos", "var": "t", "yname": "h"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["right_triangle_trig"] = {
    "course": "geo",
    "title": ("Dik üçgende trigonometri (SOH-CAH-TOA)", "Right-triangle trigonometry (SOH-CAH-TOA)"),
    "topics": ["right triangle trigonometry", "soh cah toa", "sohcahtoa", "trigonometric ratios",
               "sine cosine tangent", "inverse trig", "angle of elevation", "solving right triangles",
               "ladder problem", "ramp", "dik üçgende trigonometri", "trigonometrik oranlar", "sinüs kosinüs tanjant",
               "yükselme açısı", "dik üçgen çözme"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Polygon, Rectangle


def _ph(i, a, b):
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def _n(v, nd=2):
    v = float(v)
    s = str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s.replace("-", "−")


def _root(v):
    if abs(v - round(v)) < 1e-9:
        n = int(round(v))
        r = math.isqrt(n)
        if r * r == n:
            return str(r), True
    return f"{math.sqrt(v):.2f}", False


_GEN = {"opp": ("karşı", "opposite"), "adj": ("komşu", "adjacent"), "hyp": ("hipotenüs", "hypotenuse")}
_SHORT = {"opp": ("karşı", "opp"), "adj": ("komşu", "adj"), "hyp": ("hip", "hyp")}
_SCN = {"ladder": {"opp": ("duvardaki yükseklik", "height on the wall"), "adj": ("duvara uzaklık", "distance from the wall"),
                   "hyp": ("merdiven boyu", "ladder length")},
        "ramp": {"opp": ("yükseklik", "rise"), "adj": ("yatay mesafe", "run"), "hyp": ("rampa uzunluğu", "ramp length")}}


def _plan(P):
    ks = [k for k in ("opp", "adj", "hyp", "angle") if k in P][:2]
    v = {k: float(P[k]) for k in ks}
    S = set(ks)
    U = []
    if S == {"opp", "adj"}:
        o, a = v["opp"], v["adj"]
        th = math.degrees(math.atan2(o, a))
        hs, ex = _root(o * o + a * a)
        h = math.hypot(o, a)
        e = "=" if ex else "≈"
        U.append({"t": "angle", "r": "TOA",
                  "steps": [(f"TOA: tan θ = karşı / komşu = {_n(o)}/{_n(a)} ≈ {o / a:.4f}",
                             f"TOA: tan θ = opposite / adjacent = {_n(o)}/{_n(a)} ≈ {o / a:.4f}"),
                            (f"θ = tan⁻¹({_n(o)}/{_n(a)}) ≈ {th:.2f}°", f"θ = tan⁻¹({_n(o)}/{_n(a)}) ≈ {th:.2f}°")],
                  "panel": [(f"tan θ = {_n(o)}/{_n(a)}", f"tan θ = {_n(o)}/{_n(a)}"),
                            (f"θ = tan⁻¹({_n(o)}/{_n(a)}) ≈ {th:.2f}°", f"θ = tan⁻¹({_n(o)}/{_n(a)}) ≈ {th:.2f}°")]})
        U.append({"t": "hyp", "r": "PYT", "ex": ex,
                  "steps": [(f"Hipotenüs (Pisagor): √({_n(o)}² + {_n(a)}²) = √{_n(o * o + a * a)} {e} {hs}",
                             f"Hypotenuse (Pythagoras): √({_n(o)}² + {_n(a)}²) = √{_n(o * o + a * a)} {e} {hs}")],
                  "panel": [(f"hip = √({_n(o)}² + {_n(a)}²) {e} {hs}", f"hyp = √({_n(o)}² + {_n(a)}²) {e} {hs}")]})
    elif S == {"opp", "hyp"} or S == {"adj", "hyp"}:
        h = v["hyp"]
        k = "opp" if "opp" in S else "adj"
        x = v[k]
        if x >= h:
            return None
        if k == "opp":
            o = x
            th = math.degrees(math.asin(o / h))
            ys, ex = _root(h * h - o * o)
            a = math.sqrt(h * h - o * o)
            r, fn, inv, other = "SOH", "sin", "sin⁻¹", "adj"
        else:
            a = x
            th = math.degrees(math.acos(a / h))
            ys, ex = _root(h * h - a * a)
            o = math.sqrt(h * h - a * a)
            r, fn, inv, other = "CAH", "cos", "cos⁻¹", "opp"
        e = "=" if ex else "≈"
        nk, no = _GEN[k], _GEN[other]
        sk, so = _SHORT[k], _SHORT[other]
        U.append({"t": "angle", "r": r,
                  "steps": [(f"{r}: {fn} θ = {nk[0]} / hipotenüs = {_n(x)}/{_n(h)} ≈ {x / h:.4f}",
                             f"{r}: {fn} θ = {nk[1]} / hypotenuse = {_n(x)}/{_n(h)} ≈ {x / h:.4f}"),
                            (f"θ = {inv}({_n(x)}/{_n(h)}) ≈ {th:.2f}°", f"θ = {inv}({_n(x)}/{_n(h)}) ≈ {th:.2f}°")],
                  "panel": [(f"{fn} θ = {_n(x)}/{_n(h)}", f"{fn} θ = {_n(x)}/{_n(h)}"),
                            (f"θ = {inv}({_n(x)}/{_n(h)}) ≈ {th:.2f}°", f"θ = {inv}({_n(x)}/{_n(h)}) ≈ {th:.2f}°")]})
        U.append({"t": other, "r": "PYT", "ex": ex,
                  "steps": [(f"{no[0].capitalize()} (Pisagor): √({_n(h)}² − {_n(x)}²) = √{_n(h * h - x * x)} {e} {ys}",
                             f"{no[1].capitalize()} (Pythagoras): √({_n(h)}² − {_n(x)}²) = √{_n(h * h - x * x)} {e} {ys}")],
                  "panel": [(f"{so[0]} = √({_n(h)}² − {_n(x)}²) {e} {ys}", f"{so[1]} = √({_n(h)}² − {_n(x)}²) {e} {ys}")]})
    elif "angle" in S:
        th = v["angle"]
        if not (0 < th < 90):
            return None
        k = [q for q in ks if q != "angle"][0]
        x = v[k]
        t = math.radians(th)
        sn, cs, tn = math.sin(t), math.cos(t), math.tan(t)
        T = _n(th)
        if k == "hyp":
            h = x
            o, a = h * sn, h * cs
            U.append({"t": "opp", "r": "SOH",
                      "steps": [(f"SOH: sin θ = karşı / hipotenüs ⇒ karşı = {_n(h)} · sin {T}° ≈ {_n(h)} · {sn:.4f} ≈ {o:.2f}",
                                 f"SOH: sin θ = opposite / hypotenuse ⇒ opposite = {_n(h)} · sin {T}° ≈ {_n(h)} · {sn:.4f} ≈ {o:.2f}")],
                      "panel": [(f"karşı = {_n(h)} · sin {T}°", f"opp = {_n(h)} · sin {T}°"), (f"karşı ≈ {o:.2f}", f"opp ≈ {o:.2f}")]})
            U.append({"t": "adj", "r": "CAH",
                      "steps": [(f"CAH: cos θ = komşu / hipotenüs ⇒ komşu = {_n(h)} · cos {T}° ≈ {_n(h)} · {cs:.4f} ≈ {a:.2f}",
                                 f"CAH: cos θ = adjacent / hypotenuse ⇒ adjacent = {_n(h)} · cos {T}° ≈ {_n(h)} · {cs:.4f} ≈ {a:.2f}")],
                      "panel": [(f"komşu = {_n(h)} · cos {T}°", f"adj = {_n(h)} · cos {T}°"), (f"komşu ≈ {a:.2f}", f"adj ≈ {a:.2f}")]})
        elif k == "adj":
            a = x
            o, h = a * tn, a / cs
            U.append({"t": "opp", "r": "TOA",
                      "steps": [(f"TOA: tan θ = karşı / komşu ⇒ karşı = {_n(a)} · tan {T}° ≈ {_n(a)} · {tn:.4f} ≈ {o:.2f}",
                                 f"TOA: tan θ = opposite / adjacent ⇒ opposite = {_n(a)} · tan {T}° ≈ {_n(a)} · {tn:.4f} ≈ {o:.2f}")],
                      "panel": [(f"karşı = {_n(a)} · tan {T}°", f"opp = {_n(a)} · tan {T}°"), (f"karşı ≈ {o:.2f}", f"opp ≈ {o:.2f}")]})
            U.append({"t": "hyp", "r": "CAH",
                      "steps": [(f"CAH: cos θ = komşu / hipotenüs ⇒ hipotenüs = {_n(a)} / cos {T}° ≈ {_n(a)} / {cs:.4f} ≈ {h:.2f}",
                                 f"CAH: cos θ = adjacent / hypotenuse ⇒ hypotenuse = {_n(a)} / cos {T}° ≈ {_n(a)} / {cs:.4f} ≈ {h:.2f}")],
                      "panel": [(f"hip = {_n(a)} / cos {T}°", f"hyp = {_n(a)} / cos {T}°"), (f"hip ≈ {h:.2f}", f"hyp ≈ {h:.2f}")]})
        else:
            o = x
            h, a = o / sn, o / tn
            U.append({"t": "hyp", "r": "SOH",
                      "steps": [(f"SOH: sin θ = karşı / hipotenüs ⇒ hipotenüs = {_n(o)} / sin {T}° ≈ {_n(o)} / {sn:.4f} ≈ {h:.2f}",
                                 f"SOH: sin θ = opposite / hypotenuse ⇒ hypotenuse = {_n(o)} / sin {T}° ≈ {_n(o)} / {sn:.4f} ≈ {h:.2f}")],
                      "panel": [(f"hip = {_n(o)} / sin {T}°", f"hyp = {_n(o)} / sin {T}°"), (f"hip ≈ {h:.2f}", f"hyp ≈ {h:.2f}")]})
            U.append({"t": "adj", "r": "TOA",
                      "steps": [(f"TOA: tan θ = karşı / komşu ⇒ komşu = {_n(o)} / tan {T}° ≈ {_n(o)} / {tn:.4f} ≈ {a:.2f}",
                                 f"TOA: tan θ = opposite / adjacent ⇒ adjacent = {_n(o)} / tan {T}° ≈ {_n(o)} / {tn:.4f} ≈ {a:.2f}")],
                      "panel": [(f"komşu = {_n(o)} / tan {T}°", f"adj = {_n(o)} / tan {T}°"), (f"komşu ≈ {a:.2f}", f"adj ≈ {a:.2f}")]})
    else:
        return None
    return {"o": o, "a": a, "h": h, "th": th, "known": ks, "U": U}


def _name(key, scene):
    return _SCN.get(scene, _GEN).get(key, _GEN[key])


def _val(pl, key):
    return {"opp": pl["o"], "adj": pl["a"], "hyp": pl["h"], "angle": pl["th"]}[key]


def solve(P):
    pl = _plan(P)
    if pl is None:
        msg = ("Geçersiz veri: hipotenüs en uzun kenar olmalı ve 0° < θ < 90°.",
               "Invalid data: the hypotenuse must be the longest side and 0° < θ < 90°.")
        return {"answer": msg, "steps": [msg, msg], "fmt": {}}
    scene = P.get("scene", "")
    unit = P.get("unit", "")
    us = f" {unit}" if unit else ""
    kn_tr, kn_en = [], []
    for k in pl["known"]:
        if k == "angle":
            kn_tr.append(f"θ = {_n(P[k])}°")
            kn_en.append(f"θ = {_n(P[k])}°")
        else:
            kn_tr.append(f"{_GEN[k][0]} = {_n(P[k])}{us}")
            kn_en.append(f"{_GEN[k][1]} = {_n(P[k])}{us}")
    steps = [("Bilinenler (θ açısına göre): " + ", ".join(kn_tr), "Known (relative to θ): " + ", ".join(kn_en)),
             ("SOH-CAH-TOA: sin θ = karşı/hipotenüs, cos θ = komşu/hipotenüs, tan θ = karşı/komşu",
              "SOH-CAH-TOA: sin θ = opposite/hypotenuse, cos θ = adjacent/hypotenuse, tan θ = opposite/adjacent")]
    for u in pl["U"]:
        steps += u["steps"]
    o, a, h = pl["o"], pl["a"], pl["h"]
    steps.append((f"Kontrol (Pisagor): karşı² + komşu² ≈ {o * o + a * a:.2f} ve hipotenüs² ≈ {h * h:.2f} ✓",
                  f"Check (Pythagoras): opposite² + adjacent² ≈ {o * o + a * a:.2f} and hypotenuse² ≈ {h * h:.2f} ✓"))
    tr_parts, en_parts = [], []
    for u in pl["U"]:
        t = u["t"]
        if t == "angle":
            tr_parts.append(f"θ ≈ {pl['th']:.2f}°")
            en_parts.append(f"θ ≈ {pl['th']:.2f}°")
        else:
            vv = _val(pl, t)
            ex = u.get("ex") or abs(vv - round(vv)) < 1e-9
            e = "=" if ex else "≈"
            val = _n(vv) if ex else f"{vv:.2f}"
            nm = _name(t, scene)
            tr_parts.append(f"{nm[0]} {e} {val}{us}")
            en_parts.append(f"{nm[1]} {e} {val}{us}")
    return {"answer": (", ".join(tr_parts), ", ".join(en_parts)), "steps": steps, "fmt": {}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    L = 0 if tr else 1
    pl = _plan(P)
    if pl is None:
        pl = _plan({"opp": 3, "adj": 4})
    scene = P.get("scene", "")
    unit = P.get("unit", "")
    o, a, h, th = pl["o"], pl["a"], pl["h"], pl["th"]
    U = pl["U"]
    gs = fig.add_gridspec(2, 2, height_ratios=[0.13, 1.0], width_ratios=[1.3, 1.0], left=0.02,
                          right=0.98, top=0.98, bottom=0.03, wspace=0.04, hspace=0.06)
    top = fig.add_subplot(gs[0, :])
    top.axis("off")
    info = top.text(0.005, 0.5, "", transform=top.transAxes, va="center", ha="left", fontsize=11.5,
                    color="#111827", bbox=dict(boxstyle="round,pad=0.45", fc="#F9FAFB", ec="#D1D5DB"))
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    tx.add_patch(Rectangle((0, 0), 1, 1, transform=tx.transAxes, fc="#F8FAFC", ec="#E5E7EB"))
    ax.set_aspect("equal")
    ax.axis("off")
    W = max(a, o)
    extra = 0.12 * W if scene == "ladder" else 0.0
    ax.set_xlim(-0.16 * W, a + 0.42 * W + extra)
    ax.set_ylim(-0.2 * W, o + 0.16 * W)
    O, R, T = np.array([0.0, 0.0]), np.array([a, 0.0]), np.array([a, o])
    gx = [-0.12 * W, a + 0.3 * W + extra]
    if scene in ("ladder", "ramp"):
        ax.plot(gx, [0, 0], color="#78716C", lw=2.2, zorder=1)
        for xg in np.linspace(gx[0], gx[1], 22):
            ax.plot([xg, xg - 0.03 * W], [0, -0.03 * W], color="#A8A29E", lw=1, zorder=1)
    if scene == "ladder":
        ax.plot([a, a], [0, 1.12 * o], color="#6B7280", lw=5, zorder=1)
        for yg in np.linspace(0.04 * o, 1.1 * o, 14):
            ax.plot([a + 0.012 * W, a + 0.05 * W], [yg, yg + 0.04 * W], color="#9CA3AF", lw=1, zorder=1)
        nv = np.array([-o, a]) / h
        d = 0.03 * W
        for sg in (1, -1):
            p0, p1 = O + sg * d * nv, T + sg * d * nv
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#92400E", lw=2.2, zorder=2)
        for t in np.linspace(0.08, 0.92, 9):
            c = O + t * (T - O)
            p0, p1 = c + d * nv, c - d * nv
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#92400E", lw=1.6, zorder=2)
    elif scene == "ramp":
        ax.add_patch(Polygon([O, R, T], closed=True, fc="#E5E7EB", ec="none", zorder=0))
    sides = {}
    under = {}
    cols = {"opp": "#E07B39", "adj": "#16A34A", "hyp": "#2563EB"}
    ends = {"opp": (R, T), "adj": (O, R), "hyp": (O, T)}
    unk = {u["t"]: j for j, u in enumerate(U)}
    for k, (p0, p1) in ends.items():
        dl, = ax.plot([p0[0], p1[0]], [p0[1], p1[1]], "--", color=cols[k], lw=1.6, alpha=0.6, zorder=3)
        under[k] = dl
        dl.set_visible(k in unk)
        sl, = ax.plot([], [], color=cols[k], lw=2.6, zorder=4, solid_capstyle="round")
        sides[k] = sl
    m = 0.05 * W
    ax.plot([a - m, a - m, a], [0, m, m], color="#374151", lw=1.1, zorder=4)
    ra = 0.24 * min(a, h, 0.9 * W)
    arc, = ax.plot([], [], color="#DC2626", lw=2, zorder=5)
    fs = 10.5
    nv = np.array([-o, a]) / h
    mid = (O + T) / 2 + 0.07 * W * nv
    lab = {"adj": ax.text(a * (0.7 if th < 30 else 0.5), -0.07 * W, "", ha="center", va="top", fontsize=fs,
                          color="#15803D", fontweight="bold"),
           "opp": ax.text(a + 0.05 * W + extra, o / 2, "", ha="left", va="center", fontsize=fs, color="#C2410C",
                          fontweight="bold"),
           "hyp": ax.text(mid[0], mid[1], "", ha="right" if nv[0] < -0.2 else "center", va="bottom", fontsize=fs,
                          color="#1D4ED8", fontweight="bold")}
    thin = th < 30
    tth = ax.text(0, 0, "", fontsize=fs, color="#DC2626", fontweight="bold", va="top" if thin else "bottom",
                  ha="left", zorder=6, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    tx.text(0.05, 0.965, "SOH-CAH-TOA", transform=tx.transAxes, va="top", fontsize=10, color="#6B7280",
            fontweight="bold")
    boxes = {}
    for j, r in enumerate(("SOH", "CAH", "TOA")):
        boxes[r] = tx.text(0.08 + 0.31 * j, 0.865, r, transform=tx.transAxes, va="center", fontsize=13,
                           fontweight="bold", color="#9CA3AF",
                           bbox=dict(boxstyle="round,pad=0.3", fc="#F3F4F6", ec="#D1D5DB"))
    legend = [("sin θ = karşı / hipotenüs", "sin θ = opposite / hypotenuse"),
              ("cos θ = komşu / hipotenüs", "cos θ = adjacent / hypotenuse"),
              ("tan θ = karşı / komşu", "tan θ = opposite / adjacent")]
    for j, s in enumerate(legend):
        tx.text(0.05, 0.78 - j * 0.055, s[L], transform=tx.transAxes, va="top", fontsize=9.5, color="#4B5563")
    plines = [(s[L], 30 + 18 * k if j == 0 else 90 + 12 * k, j)
              for j, u in enumerate(U) for k, s in enumerate(u["panel"])]
    arts = []
    for k, (s, t0, j) in enumerate(plines):
        tt = tx.text(0.05, 0.56 - k * 0.1, s, transform=tx.transAxes, va="top",
                     fontsize=11.5 if len(s) < 27 else 10, color="#111827", alpha=0.0)
        arts.append((tt, t0))
    for j in range(len(U)):
        last = [kk for kk, (_, _, jj) in enumerate(plines) if jj == j][-1]
        arts[last][0].set_color("#DC2626")
        arts[last][0].set_fontweight("bold")
    uses = {"SOH": ("opp", "hyp"), "CAH": ("adj", "hyp"), "TOA": ("opp", "adj"), "PYT": ("opp", "adj", "hyp")}

    def rname(r):
        return ("Pisagor", "Pythagoras")[L] if r == "PYT" else r

    def sidetxt(k, g):
        nm = _GEN[k][L]
        v = _val(pl, k)
        if k not in unk:
            return f"{nm} = {_n(v)}"
        if g <= 0:
            return f"{nm} = ?"
        u = U[unk[k]]
        if g >= 1:
            ex = u.get("ex") or abs(v - round(v)) < 1e-9
            return f"{nm} {'=' if ex else '≈'} {_n(v) if ex else f'{v:.2f}'}"
        return f"{nm} ≈ {v * g:.2f}"

    kn = ", ".join((f"θ = {_n(P['angle'])}°" if k == "angle" else f"{_GEN[k][L]} = {_n(P[k])}") for k in pl["known"])
    res = solve(P)["answer"][L]
    u1, u2 = U[0], U[1]
    nm1 = "θ" if u1["t"] == "angle" else _GEN[u1["t"]][L]
    nm2 = "θ" if u2["t"] == "angle" else _GEN[u2["t"]][L]
    narr = [
        ((f"1) Dik üçgen; θ'ya göre bilinenler: {kn}" if tr else f"1) Right triangle; known relative to θ: {kn}")),
        ((f"2) {nm1} için {rname(u1['r'])} kullan" if tr else f"2) Use {rname(u1['r'])} for {nm1}")),
        ((f"3) {nm1} hesaplanıyor" if tr else f"3) Computing {nm1}")),
        ((f"4) {nm2} için {rname(u2['r'])} kullan" if tr else f"4) Use {rname(u2['r'])} for {nm2}")),
        (("Sonuç: " if tr else "Result: ") + res),
    ]
    starts = [0, 14, 28, 74, 112]
    N = 140

    def update(i):
        act = u1["r"] if 14 <= i < 74 else (u2["r"] if 74 <= i < 112 else None)
        for r, b in boxes.items():
            on = act == r
            b.set_color("#111827" if on else "#9CA3AF")
            b.get_bbox_patch().set_facecolor("#FDE68A" if on else "#F3F4F6")
        g = {u1["t"]: _ease(_ph(i, 28, 62)), u2["t"]: _ease(_ph(i, 88, 110))}
        for k, (p0, p1) in ends.items():
            gk = g.get(k, 1.0)
            if gk > 0:
                q = p0 + gk * (p1 - p0)
                sides[k].set_data([p0[0], q[0]], [p0[1], q[1]])
            else:
                sides[k].set_data([], [])
            sides[k].set_linewidth(5 if (act and k in uses[act]) else 2.6)
            lab[k].set_text(sidetxt(k, gk) if i >= 3 else "")
        ga = g.get("angle", 1.0)
        tt = np.linspace(0, math.radians(th * ga), 30)
        arc.set_data(ra * np.cos(tt), ra * np.sin(tt)) if ga > 0 else arc.set_data([], [])
        tth.set_position((ra * 0.85, -0.035 * W) if thin else (ra * 1.08, 0.02 * W))
        if "angle" in g:
            tth.set_text("θ = ?" if ga <= 0 else (f"θ ≈ {th * ga:.2f}°" if ga < 1 else f"θ ≈ {th:.2f}°"))
        else:
            tth.set_text(f"θ = {_n(th)}°")
        for t, t0 in arts:
            t.set_alpha(_ph(i, t0, t0 + 7))
        k = max(j for j, s0 in enumerate(starts) if i >= s0)
        info.set_text(narr[k])
        return []

    return N, update


def vary(P, rnd):
    out = {k: v for k, v in P.items() if k not in ("opp", "adj", "hyp", "angle")}
    ks = set(k for k in ("opp", "adj", "hyp", "angle") if k in P)
    scene = P.get("scene", "")
    if ks == {"opp", "adj"}:
        if scene == "ramp":
            out.update({"opp": rnd.choice([0.5, 0.6, 0.8, 1, 1.2]), "adj": rnd.choice([6, 8, 10, 12])})
        else:
            o, a = rnd.choice([(3, 4), (5, 12), (8, 15), (7, 24), (6, 8), (9, 12), (20, 21)])
            if rnd.random() < 0.5:
                o, a = a, o
            out.update({"opp": o, "adj": a})
    elif ks in ({"opp", "hyp"}, {"adj", "hyp"}):
        x, hh = rnd.choice([(3, 5), (4, 5), (5, 13), (12, 13), (8, 17), (15, 17), (6, 10)])
        out.update({list(ks - {"hyp"})[0]: x, "hyp": hh})
    else:
        other = list(ks - {"angle"})[0] if len(ks) == 2 else "hyp"
        ang = rnd.choice([60, 65, 70, 75]) if scene == "ladder" else rnd.choice([25, 30, 35, 40, 50, 55, 60])
        out.update({"angle": ang, other: rnd.choice([4, 5, 6, 8, 10, 12])})
    return out
''',
}
EXAMPLES += [
    {"id": "geo-rtt-1", "kind": "right_triangle_trig",
     "title": ("İki dik kenardan açı ve hipotenüs", "Angle and hypotenuse from two legs"),
     "q": ("Bir dik üçgende θ açısının karşısındaki dik kenar {opp}, θ'ya komşu dik kenar {adj}. "
           "θ açısını ve hipotenüsü bul.",
           "In a right triangle the side opposite angle θ is {opp} and the side adjacent to θ is {adj}. "
           "Find θ and the hypotenuse."),
     "P": {"opp": 5, "adj": 12}},
    {"id": "geo-rtt-2", "kind": "right_triangle_trig",
     "topics": ["ladder", "merdiven", "word problem", "sözel problem"],
     "title": ("Duvara dayalı merdiven", "Ladder against a wall"),
     "q": ("{hyp} m uzunluğundaki bir merdiven duvara dayanmış ve yerle {angle}°'lik açı yapıyor. "
           "Merdiven duvarda ne kadar yükseğe ulaşır? Ayağı duvardan ne kadar uzaktadır?",
           "A {hyp} m ladder leans against a wall and makes a {angle}° angle with the ground. "
           "How high up the wall does it reach, and how far is its foot from the wall?"),
     "P": {"hyp": 6, "angle": 70, "scene": "ladder", "unit": "m"}},
    {"id": "geo-rtt-3", "kind": "right_triangle_trig",
     "topics": ["ramp", "rampa", "angle of inclination", "eğim açısı", "word problem"],
     "title": ("Rampanın eğim açısı", "Angle of a ramp"),
     "q": ("Bir tekerlekli sandalye rampası yatayda {adj} m ilerlerken {opp} m yükseliyor. Rampanın yerle "
           "yaptığı açı ve rampanın uzunluğu nedir?",
           "A wheelchair ramp rises {opp} m over a horizontal run of {adj} m. What angle does it make with "
           "the ground, and how long is the ramp?"),
     "P": {"opp": 1.5, "adj": 10, "scene": "ramp", "unit": "m"}},
]

# ── END OF GEO TEMPLATES ──
