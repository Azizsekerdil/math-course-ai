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
    tA = ax.text(a / 2, -a / 2, "", ha="center", va="center", fontsize=fs, color="#7C2D12", zorder=8)
    tB = ax.text(-b / 2, b / 2, "", ha="center", va="center", fontsize=fs, color="#14532D", zorder=8)
    ctr = (A + B) / 2 + nv * c / 2
    tC = ax.text(ctr[0], ctr[1], "", ha="center", va="center", fontsize=fs + 0.5,
                 color="#4C1D95", zorder=8)
    la = ax.text(a / 2, 0.03 * span, "", ha="center", va="bottom", fontsize=fs, color="#1E3A8A", zorder=7)
    lb = ax.text(0.03 * span, b / 2, "", ha="left", va="center", fontsize=fs, color="#1E3A8A", zorder=7)
    mid = (A + B) / 2 - nv * 0.05 * span
    lc = ax.text(mid[0], mid[1], "", ha="center", va="center", fontsize=fs, color="#1E3A8A",
                 rotation=math.degrees(math.atan2(-b, a)), rotation_mode="anchor", zorder=7)
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
        la.set_text(f"a = {_n(a)}" if i >= 4 else "")
        tA.set_text(f"a² = {_n(sa)}" if gA > 0.6 else "")
        done = i >= 124
        if unk == "c":
            lb.set_text(f"b = {_n(b)}" if i >= 4 else "")
            lc.set_text((f"c = {_n(c, 3)}" if done else "c = ?") if i >= 4 else "")
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
            else:
                tC.set_text(f"c² = {_n(sa)} + {_n(sb)}\n= {_n(sa + sb)}")
        else:
            lb.set_text((f"b = {_n(b, 3)}" if done else "b = ?") if i >= 4 else "")
            lb.set_color("#DC2626" if done else "#1E3A8A")
            lc.set_text(f"c = {_n(c)}" if i >= 4 else "")
            ps = _ph(i, 90, 102)
            pm = _ph(i, 104, 122)
            cC.set_xy(band(0, c * gC))
            cC.set_alpha(0.3 * (1 - ps))
            cA.set_xy(band(0, dA))
            cA.set_alpha(0.5 * ps)
            cB.set_xy(band(dA, dA + (c - dA) * (1 - pm)))
            cB.set_alpha(0.5 * ps)
            pBf.set_xy(sq_b(pm))
            tB.set_text("" if gB <= 0.6 else ("b² = ?" if pm < 1 else
                                               f"b² = {_n(sc)} − {_n(sa)}\n= {_n(sc - sa)}"))
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
    th = ax.text(0, 0, "", fontsize=11, color="#DC2626", va="center")
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
        th.set_text(f"h = {_d(hF)}")
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
    out.update({"base": b, "height": h, "shift": rnd.randint(-2, b + 2)})
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
    # arc of length 2πρ, bottom point at (0, 0); t = 0 full circle, t = 1 straight segment
    L = 2 * math.pi * rho
    s = np.linspace(-L / 2, L / 2, n)
    if rho <= 0:
        return np.zeros(n), np.zeros(n)
    k = (1 - t) / rho
    if k < 1e-6:
        return s, np.zeros(n)
    return np.sin(k * s) / k, (1 - np.cos(k * s)) / k


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
        a0 = _ph(i, 0, 12)
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

# ── END OF GEO TEMPLATES ──
