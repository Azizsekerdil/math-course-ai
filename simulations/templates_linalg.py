# -*- coding: utf-8 -*-
"""Lineer cebir simülasyonları: vektör toplama, matris dönüşümü, özdeğer ve
özvektör, Gauss yok etme, iç çarpım ve izdüşüm, lineer kombinasyon, matris
çarpımı, 3×3 determinant.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Ortak yardımcılar
(_NUM, _ARROW, _PANEL, _MATRIX) kaynağın BAŞINA eklenir, böylece her kaynak
yine tek başına çalışır. Sorular kitaplardan KOPYALANMAZ: kendi ifademizle
yazılmış, kendi sayılarımızla tipik ders örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
# Ortak yardımcı kaynak parçaları (her şablon kaynağına metin olarak eklenir)
# ──────────────────────────────────────────────────────────────────────────
_NUM = r'''
import math
import numpy as np
from fractions import Fraction

BLUE, ORANGE, GREEN, RED, PURPLE, GRAY = ("#2563EB", "#E07B39", "#16A34A", "#DC2626",
                                          "#7C3AED", "#6B7280")
INK, LIGHT = "#111827", "#D1D5DB"
SUB = "₀₁₂₃₄₅₆₇₈₉"


def _q(v):
    if isinstance(v, Fraction):
        return v
    if isinstance(v, float):
        return Fraction(v).limit_denominator(10 ** 6)
    return Fraction(v)


def _f(v):
    v = _q(v)
    s = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    return s.replace("-", "−")


def _g(x):
    return f"{x:.4g}".replace("-", "−")


def _p(v):
    s = _f(v)
    return "(" + s + ")" if (s.startswith("−") or "/" in s) else s


def _cf(v):
    s = _f(v)
    if s == "1":
        return ""
    if s == "−1":
        return "−"
    return "(" + s + ")" if "/" in s else s


def _vec(v):
    return "(" + ", ".join(_f(x) for x in v) + ")"


def _isq(q):
    q = _q(q)
    if q < 0:
        return None
    n, d = q.numerator, q.denominator
    rn, rd = math.isqrt(n), math.isqrt(d)
    return Fraction(rn, rd) if (rn * rn == n and rd * rd == d) else None


def _root(q):
    q = _q(q)
    r = _isq(q)
    if r is not None:
        return _f(r)
    if q.denominator == 1 and q > 0:
        k, m, p = 1, q.numerator, 2
        while p * p <= m:
            while m % (p * p) == 0:
                m //= p * p
                k *= p
            p += 1
        return f"{k}√{m}" if k > 1 else f"√{m}"
    return f"√({_f(q)})"


def _mag(v):
    sq = sum(_q(x) * _q(x) for x in v)
    terms = " + ".join(_p(x) + "²" for x in v)
    rad = _f(sq) if sq.denominator == 1 else "(" + _f(sq) + ")"
    r = _root(sq)
    s = f"√({terms}) = √{rad}"
    if r != "√" + rad:
        s += " = " + r
    approx = "" if _isq(sq) is not None else f" ≈ {_g(math.sqrt(float(sq)))}"
    return s + approx, r, approx


def _side(coefs, names):
    s = ""
    for c, v in zip(coefs, names):
        c = _q(c)
        if c == 0:
            continue
        mag = "" if abs(c) == 1 else _f(abs(c))
        if "/" in mag:
            mag = "(" + mag + ")"
        if s == "":
            s = ("−" if c < 0 else "") + mag + v
        else:
            s += (" − " if c < 0 else " + ") + mag + v
    return s or "0"


def _ph(i, a, b):
    if b <= a:
        return 1.0 if i >= a else 0.0
    return min(1.0, max(0.0, (i - a) / (b - a)))


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)
'''

_ARROW = r'''
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle


def _arrow(ax, color, lw=2.6, z=4, ls="-", ms=18):
    a = FancyArrowPatch((0, 0), (1, 0), arrowstyle="-|>", mutation_scale=ms, lw=lw,
                        color=color, zorder=z, shrinkA=0, shrinkB=0, linestyle=ls)
    ax.add_patch(a)
    a.set_visible(False)
    return a


def _set_arrow(a, p, q, alpha=1.0):
    lim = a.axes.get_xlim() if a.axes is not None else (0.0, 1.0)
    if alpha <= 0.0 or math.hypot(q[0] - p[0], q[1] - p[1]) < 0.02 * abs(lim[1] - lim[0]):
        a.set_visible(False)
        return
    a.set_positions((float(p[0]), float(p[1])), (float(q[0]), float(q[1])))
    a.set_alpha(min(1.0, alpha))
    a.set_visible(True)


def _side_label(vec, other, off, t=0.55):
    vec = np.asarray(vec, dtype=float)
    n = np.array([-vec[1], vec[0]])
    nn = math.hypot(n[0], n[1])
    if nn < 1e-9:
        return t * vec + np.array([off, off])
    n = n / nn
    if float(np.dot(n, np.asarray(other, dtype=float))) > 0:
        n = -n
    return t * vec + n * off
'''

_PANEL = r'''
def _wrap(s, width):
    parts = s.split(" = ")
    lines, cur = [], parts[0]
    for p in parts[1:]:
        if len(cur) + 3 + len(p) <= width:
            cur += " = " + p
        else:
            lines.append(cur)
            cur = "    = " + p
    lines.append(cur)
    return lines


def _panel(tx, entries, top=0.92, bottom=0.03, fs=11, width=26, dy=0.075):
    rows = []
    for start, text, color in entries:
        for piece in _wrap(text, width):
            rows.append((start, piece, color))
    if rows:
        dy = min(dy, (top - bottom) / len(rows))
    out = []
    for k, (start, piece, color) in enumerate(rows):
        t = tx.text(0.02, top - k * dy, piece, transform=tx.transAxes, fontsize=fs, color=color,
                    va="top", ha="left", alpha=0.0)
        out.append((t, start))
    return out


def _panel_show(items, i):
    for t, start in items:
        t.set_alpha(_ph(i, start, start + 6))
'''

_MATRIX = r'''
def _mat(ax, x, y, cells, cw, ch, fs=15, color=INK, bar=None, kind="[]", lw=1.6):
    R, C = len(cells), len(cells[0])
    T = []
    for i in range(R):
        row = []
        for j in range(C):
            row.append(ax.text(x + j * cw, y - i * ch, cells[i][j], ha="center", va="center",
                               fontsize=fs, family="DejaVu Sans Mono", color=color, zorder=5))
        T.append(row)
    left, right = x - 0.62 * cw, x + (C - 1) * cw + 0.62 * cw
    top, bot = y + 0.55 * ch, y - (R - 1) * ch - 0.55 * ch
    t = 0.16 * cw
    lines = []
    if kind == "[]":
        l1, = ax.plot([left + t, left, left, left + t], [top, top, bot, bot], color="#374151", lw=lw)
        l2, = ax.plot([right - t, right, right, right - t], [top, top, bot, bot], color="#374151", lw=lw)
    else:
        l1, = ax.plot([left, left], [top, bot], color="#374151", lw=lw)
        l2, = ax.plot([right, right], [top, bot], color="#374151", lw=lw)
    lines += [l1, l2]
    if bar is not None:
        xb = x + (bar - 0.5) * cw
        l3, = ax.plot([xb, xb], [top, bot], color=GRAY, lw=1.2, ls="--")
        lines.append(l3)
    return T, (left, right, top, bot), lines
'''


def _code(*parts):
    return "".join(parts)


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["vector_add"] = {
    "course": "linalg",
    "title": ("Vektör toplama ve skalerle çarpma", "Vector addition and scalar multiples"),
    "topics": ["vector", "vectors", "vector addition", "adding vectors", "scalar multiplication",
               "scalar multiple", "magnitude", "length of a vector", "parallelogram law",
               "tip to tail", "vector operations", "vektör", "vektörler", "vektör toplama",
               "skalerle çarpma", "vektörün uzunluğu", "büyüklük", "paralelkenar kuralı",
               "vektör işlemleri"],
    "code": _code(_NUM, _ARROW, _PANEL, r'''

def solve(P):
    u = [_q(x) for x in P["u"]]
    v = [_q(x) for x in P["v"]]
    s = _q(P["s"])
    w = [a + b for a, b in zip(u, v)]
    su = [s * a for a in u]
    mw, rw, aw = _mag(w)
    mu, ru, au = _mag(u)
    comp = ", ".join(f"{_f(a)} + {_p(b)}" for a, b in zip(u, v))
    scomp = ", ".join(f"{_p(s)}·{_p(a)}" for a in u)
    cs = _cf(s) + "u"
    sq_su = sum(x * x for x in su)
    msu = _root(sq_su)
    tail = f"{_f(abs(s))}·{ru}" + ("" if msu == f"{_f(abs(s))}·{ru}" else f" = {msu}")
    asu = "" if _isq(sq_su) is not None else f" ≈ {_g(math.sqrt(float(sq_su)))}"
    steps = [
        (f"Verilen: u = {_vec(u)}, v = {_vec(v)}, s = {_f(s)}",
         f"Given: u = {_vec(u)}, v = {_vec(v)}, s = {_f(s)}"),
        (f"Bileşen bileşen topla: u + v = ({comp}) = {_vec(w)}",
         f"Add component-wise: u + v = ({comp}) = {_vec(w)}"),
        ("Uç uca kuralı: v'yi u'nun ucuna taşı; başlangıçtan son uca giden ok u + v'dir "
         "(u ve v üzerine kurulan paralelkenarın köşegeni).",
         "Tip-to-tail: slide v to the tip of u; the arrow from the start to the final tip is u + v "
         "(the diagonal of the parallelogram built on u and v)."),
        (f"Uzunluk: |u + v| = {mw}", f"Length: |u + v| = {mw}"),
        (f"Skalerle çarpma: {cs} = ({scomp}) = {_vec(su)}",
         f"Scalar multiple: {cs} = ({scomp}) = {_vec(su)}"),
        (f"|{cs}| = |{_f(s)}|·|u| = {tail}" + (" — s < 0 olduğundan yön ters döner" if s < 0 else ""),
         f"|{cs}| = |{_f(s)}|·|u| = {tail}" + (" — s < 0, so the direction reverses" if s < 0 else "")),
    ]
    ans = f"u + v = {_vec(w)}, |u + v| = {rw}{aw}, {cs} = {_vec(su)}"
    fmt = {"U": _vec(u), "V": _vec(v), "W": _vec(w), "SU": _vec(su), "su": cs, "rw": rw + aw,
           "comp": f"u + v = ({comp}) = {_vec(w)}", "mag": f"|u + v| = {mw}",
           "scomp": f"{cs} = ({scomp}) = {_vec(su)}", "smag": f"|{cs}| = {tail}{asu}"}
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    u = np.array([float(x) for x in P["u"]])
    v = np.array([float(x) for x in P["v"]])
    s = float(P["s"])
    w, su = u + v, s * u
    sol = solve(P)
    F = sol["fmt"]
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1], left=0.06, right=0.98, top=0.93,
                          bottom=0.07, wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    pts = np.array([[0.0, 0.0], u, v, w, su])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    span = max(float((hi - lo).max()), 4.0)
    pad = 0.1 * span + 0.6
    ax.set_xlim(lo[0] - pad, hi[0] + pad)
    ax.set_ylim(lo[1] - pad, hi[1] + pad + 0.2 * span)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color=GRAY, lw=1)
    ax.axvline(0, color=GRAY, lw=1)
    ax.tick_params(labelsize=8)
    para = Polygon([[0, 0], u, w, v], closed=True, fc=GREEN, ec="none", alpha=0.0, zorder=1)
    ax.add_patch(para)
    a_su = _arrow(ax, PURPLE, lw=5.5, z=2)
    a_u = _arrow(ax, BLUE, z=5)
    a_v = _arrow(ax, ORANGE, z=5)
    a_vc = _arrow(ax, ORANGE, lw=2, ls="--", z=4)
    a_uc = _arrow(ax, BLUE, lw=2, ls="--", z=4)
    a_w = _arrow(ax, GREEN, lw=3.4, z=6)
    off = 0.06 * span
    kw = dict(fontsize=13, fontweight="bold", ha="center", va="center", zorder=8)
    t_u = ax.text(*_side_label(u, v, off), "u", color=BLUE, **kw)
    t_v = ax.text(*_side_label(v, u, off), "v", color=ORANGE, **kw)
    t_vc = ax.text(0, 0, "v", color=ORANGE, alpha=0, **kw)
    t_uc = ax.text(*(v + _side_label(u, -v, off)), "u", color=BLUE, alpha=0, **kw)
    t_w = ax.text(*_side_label(w, u, off, 0.62), "u + v", color=GREEN, **kw)
    cx = (ax.get_xlim()[0] + ax.get_xlim()[1]) / 2
    nw = max(math.hypot(w[0], w[1]), 1e-9)
    mpos = w + w / nw * 0.6 * off + np.array([0.0, 1.1 * off if w[1] >= 0 else -1.1 * off])
    t_mag = ax.text(mpos[0], mpos[1], f"|u + v| = {F['rw']}",
                    color=GREEN, fontsize=10.5, ha="right" if w[0] > cx else "left",
                    va="bottom" if w[1] >= 0 else "top", zorder=8,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=GREEN, alpha=0.9))
    t_su = ax.text(0, 0, F["su"], color=PURPLE, fontsize=13, fontweight="bold", ha="center",
                   va="center", zorder=8)
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=11, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    tx.set_title("Hesaplar" if tr else "Calculations", fontsize=12, loc="left")
    items = _panel(tx, [(0, f"u = {F['U']}", BLUE), (12, f"v = {F['V']}", ORANGE),
                        (60, F["comp"], GREEN), (82, F["mag"], GREEN),
                        (98, F["scomp"], PURPLE), (116, F["smag"], PURPLE)], fs=11, width=24)
    N = 140

    def update(i):
        pu = _ease(_ph(i, 0, 14))
        pv = _ease(_ph(i, 12, 28))
        _set_arrow(a_u, (0, 0), pu * u)
        _set_arrow(a_v, (0, 0), pv * v)
        t_u.set_alpha(1.0 if pu >= 1 else 0.0)
        t_v.set_alpha(1.0 if pv >= 1 else 0.0)
        if i >= 32:
            sh = _ease(_ph(i, 32, 56)) * u
            _set_arrow(a_vc, sh, sh + v)
            t_vc.set_position(sh + _side_label(v, -u, off))
            t_vc.set_alpha(1.0)
        else:
            _set_arrow(a_vc, (0, 0), (0, 0))
            t_vc.set_alpha(0.0)
        pw = _ease(_ph(i, 60, 78))
        _set_arrow(a_w, (0, 0), pw * w)
        t_w.set_alpha(1.0 if pw >= 1 else 0.0)
        pp = _ph(i, 62, 80)
        para.set_alpha(0.16 * pp)
        _set_arrow(a_uc, v, v + u, alpha=0.85 * pp)
        t_uc.set_alpha(pp)
        t_mag.set_alpha(_ph(i, 82, 88))
        t_mag.get_bbox_patch().set_alpha(0.9 * _ph(i, 82, 88))
        if i >= 96:
            k = 1 + (s - 1) * _ease(_ph(i, 96, 120))
            tip = k * u
            _set_arrow(a_su, (0, 0), tip, alpha=0.55)
            n = math.hypot(tip[0], tip[1])
            d = tip / n if n > 1e-9 else np.array([0.0, 0.0])
            t_su.set_position(tip + d * 1.3 * off)
            t_su.set_alpha(1.0)
        else:
            _set_arrow(a_su, (0, 0), (0, 0))
            t_su.set_alpha(0.0)
        if i < 30:
            info.set_text("1) u ve v'yi başlangıç noktasından çiz" if tr else
                          "1) Draw u and v from the origin")
        elif i < 58:
            info.set_text("2) Uç uca: v'yi u'nun ucuna taşı" if tr else
                          "2) Tip-to-tail: slide v to the tip of u")
        elif i < 94:
            info.set_text(f"3) u + v = {F['W']}: paralelkenarın köşegeni" if tr else
                          f"3) u + v = {F['W']}: the parallelogram's diagonal")
        elif i < 124:
            info.set_text((f"4) Skalerle çarpma: {F['su']} = {F['SU']}" if tr else
                           f"4) Scalar multiple: {F['su']} = {F['SU']}"))
        else:
            info.set_text(f"u + v = {F['W']},  |u + v| = {F['rw']}\n{F['su']} = {F['SU']}")
        _panel_show(items, i)
        return []

    return N, update


def vary(P, rnd):
    good =[(3, 4), (4, 3), (6, 8), (8, 6), (0, 5), (5, 0), (0, 4), (4, 0), (6, 0), (0, 6)]
    for _ in range(2000):
        wx, wy = rnd.choice(good)
        wx *= rnd.choice([1, -1])
        wy *= rnd.choice([1, -1])
        ux, uy = rnd.randint(-5, 6), rnd.randint(-5, 6)
        vx, vy = wx - ux, wy - uy
        if (ux, uy) == (0, 0) or (vx, vy) == (0, 0) or ux * vy - uy * vx == 0:
            continue
        if max(abs(vx), abs(vy)) > 8:
            continue
        neg = float(P.get("s", 2)) < 0
        s = rnd.choice([-1, -2, -3]) if neg else rnd.choice([2, 3])
        return {"u": [ux, uy], "v": [vx, vy], "s": s}
    return {"u": [3, 1], "v": [1, 2], "s": 2}
'''),
}
EXAMPLES += [
    {"id": "linalg-vec-1", "kind": "vector_add",
     "title": ("Vektör toplama ve uzunluk", "Adding vectors and finding the length"),
     "q": ("u = {U} ve v = {V} veriliyor. u + v'yi uç uca kuralıyla bul, |u + v| uzunluğunu ve "
           "{su} vektörünü hesapla.",
           "Given u = {U} and v = {V}, find u + v with the tip-to-tail rule, its length |u + v|, "
           "and the vector {su}."),
     "P": {"u": [3, 1], "v": [1, 2], "s": 2}},
    {"id": "linalg-vec-2", "kind": "vector_add",
     "topics": ["velocity", "resultant", "hız vektörü", "bileşke"],
     "title": ("Uçak ve rüzgâr: bileşke hız", "Plane and wind: resultant velocity"),
     "q": ("Bir uçağın durgun havadaki hız vektörü u = {U}, rüzgârın hız vektörü v = {V} "
           "(birim: 100 km/sa). Yere göre hız vektörü u + v ve sürat |u + v| nedir? "
           "Uçak hızını değiştirip {su} ile uçarsa hız vektörü ne olur?",
           "A plane's velocity in still air is u = {U} and the wind's velocity is v = {V} "
           "(unit: 100 km/h). What are the ground velocity u + v and the ground speed |u + v|? "
           "What is the velocity if the plane flies at {su} instead?"),
     "P": {"u": [8, 3], "v": [-2, 5], "s": 2}},
    {"id": "linalg-vec-3", "kind": "vector_add",
     "title": ("Negatif skalerle çarpma", "Multiplying by a negative scalar"),
     "q": ("u = {U}, v = {V} için u + v ve |u + v| değerlerini bul. Ayrıca {su} vektörünü çiz: "
           "negatif skaler yönü nasıl değiştirir?",
           "For u = {U}, v = {V} find u + v and |u + v|. Also draw {su}: how does a negative "
           "scalar change the direction?"),
     "P": {"u": [-2, 3], "v": [5, 1], "s": -2}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["matrix_transform"] = {
    "course": "linalg",
    "title": ("Matris dönüşümü ve determinant", "Matrix transformation and the determinant"),
    "topics": ["linear transformation", "linear transformations", "matrix transformation",
               "transformation matrix", "matrix as a transformation", "determinant", "shear",
               "rotation matrix", "reflection", "basis vectors", "doğrusal dönüşüm",
               "lineer dönüşüm", "dönüşüm matrisi", "taban vektörleri", "kayma dönüşümü",
               "yansıma"],
    "code": _code(_NUM, _ARROW, _PANEL, _MATRIX, r'''
from matplotlib.collections import LineCollection
from matplotlib.ticker import MultipleLocator


def _ms(m):
    return "[" + ", ".join("[" + ", ".join(_f(x) for x in r) + "]" for r in m) + "]"


def solve(P):
    a, b, c, d = (_q(P[k]) for k in ("a", "b", "c", "d"))
    D = a * d - b * c
    As = _ms([[a, b], [c, d]])
    steps = [
        (f"A = {As}; A'nın sütunları taban vektörlerinin görüntüleridir",
         f"A = {As}; the columns of A are the images of the basis vectors"),
        (f"Aî = A·(1, 0) = ({_f(a)}, {_f(c)})  → 1. sütun",
         f"Aî = A·(1, 0) = ({_f(a)}, {_f(c)})  → column 1"),
        (f"Aĵ = A·(0, 1) = ({_f(b)}, {_f(d)})  → 2. sütun",
         f"Aĵ = A·(0, 1) = ({_f(b)}, {_f(d)})  → column 2"),
        (f"Birim kare → köşeleri (0, 0), ({_f(a)}, {_f(c)}), ({_f(a + b)}, {_f(c + d)}), "
         f"({_f(b)}, {_f(d)}) olan paralelkenar",
         f"The unit square → the parallelogram with corners (0, 0), ({_f(a)}, {_f(c)}), "
         f"({_f(a + b)}, {_f(c + d)}), ({_f(b)}, {_f(d)})"),
        (f"det A = ad − bc = {_p(a)}·{_p(d)} − {_p(b)}·{_p(c)} = {_f(D)}",
         f"det A = ad − bc = {_p(a)}·{_p(d)} − {_p(b)}·{_p(c)} = {_f(D)}"),
    ]
    if D > 0:
        steps.append((f"Her alan |det A| = {_f(D)} katına çıkar; det A > 0 olduğundan yönelim korunur "
                      "(î'den ĵ'ye dönüş yine saat yönünün tersine).",
                      f"Every area is multiplied by |det A| = {_f(D)}; det A > 0 so orientation is "
                      "preserved (î → ĵ still turns counter-clockwise)."))
        ans = (f"det A = {_f(D)}: alanlar ×{_f(D)}, yönelim korunur",
               f"det A = {_f(D)}: areas ×{_f(D)}, orientation preserved")
    elif D < 0:
        steps.append((f"Her alan |det A| = {_f(-D)} katına çıkar; det A < 0 olduğundan yönelim ters "
                      "döner (düzlem ayna gibi 'ters yüz' olur, î'den ĵ'ye dönüş saat yönünde).",
                      f"Every area is multiplied by |det A| = {_f(-D)}; det A < 0 so orientation "
                      "flips (the plane is turned over like a mirror; î → ĵ now turns clockwise)."))
        ans = (f"det A = {_f(D)}: alanlar ×{_f(-D)}, yönelim ters döner",
               f"det A = {_f(D)}: areas ×{_f(-D)}, orientation reversed")
    else:
        steps.append(("det A = 0: düzlem bir doğruya (veya noktaya) çöker; A tersinir değildir.",
                      "det A = 0: the plane collapses onto a line (or a point); A is not invertible."))
        ans = ("det A = 0: düzlem bir doğruya çöker", "det A = 0: the plane collapses to a line")
    return {"answer": ans, "steps": steps, "fmt": {"Am": As, "detA": _f(D)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    qa, qb, qc, qd = (_q(P[k]) for k in ("a", "b", "c", "d"))
    a, b, c, d = float(qa), float(qb), float(qc), float(qd)
    A = np.array([[a, b], [c, d]])
    D = a * d - b * c
    QD = qa * qd - qb * qc
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1], left=0.06, right=0.98, top=0.95,
                          bottom=0.06, wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    tx.set_xlim(0, 1)
    tx.set_ylim(0, 1)
    cs = np.array([[0, 0], [1, 1], [a, c], [b, d], [a + b, c + d]], dtype=float)
    lo, hi = cs.min(axis=0) - 1.0, cs.max(axis=0) + 1.0
    mid = (lo + hi) / 2
    wdt, hgt = max(float(hi[0] - lo[0]), 4.0), max(float(hi[1] - lo[1]), 4.0)
    ax.set_xlim(mid[0] - wdt / 2, mid[0] + wdt / 2)
    ax.set_ylim(mid[1] - hgt / 2, mid[1] + hgt / 2 + 0.22 * max(wdt, hgt))
    ax.set_aspect("equal")
    stp = 1 if max(wdt, hgt) <= 12 else 2
    ax.xaxis.set_major_locator(MultipleLocator(stp))
    ax.yaxis.set_major_locator(MultipleLocator(stp))
    ax.grid(alpha=0.35, color="#9CA3AF")
    ax.tick_params(labelsize=8)
    xl, yl = ax.get_xlim(), ax.get_ylim()
    corners = np.array([[xl[0], yl[0]], [xl[0], yl[1]], [xl[1], yl[0]], [xl[1], yl[1]]])
    need = 3.0
    for t in np.linspace(0, 1, 41):
        Mt = (1 - t) * np.eye(2) + t * A
        if abs(np.linalg.det(Mt)) < 0.08:
            continue
        need = max(need, float(np.abs(np.linalg.solve(Mt, corners.T)).max()))
    G = int(min(16, math.ceil(need) + 1))
    ks = [k for k in range(-G, G + 1) if k != 0]
    base = ([np.array([[k, -G], [k, G]], dtype=float) for k in ks] +
            [np.array([[-G, k], [G, k]], dtype=float) for k in ks])
    lc = LineCollection([], colors=BLUE, linewidths=0.8, alpha=0.4, zorder=2)
    ax.add_collection(lc, autolim=False)
    axx, = ax.plot([], [], color=BLUE, lw=1.8, alpha=0.85, zorder=2)
    axy, = ax.plot([], [], color=BLUE, lw=1.8, alpha=0.85, zorder=2)
    unit = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    sq = Polygon(unit, closed=True, fc=BLUE, ec=BLUE, alpha=0.3, lw=1.5, zorder=3)
    ax.add_patch(sq)
    ai = _arrow(ax, GREEN, lw=3, z=6)
    aj = _arrow(ax, PURPLE, lw=3, z=6)
    kw = dict(fontsize=12, fontweight="bold", ha="center", va="center", zorder=8,
              bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.75))
    ti = ax.text(0, 0, "", color=GREEN, **kw)
    tj = ax.text(0, 0, "", color=PURPLE, **kw)
    tarea = ax.text(0, 0, "", fontsize=9.5, ha="center", va="center", color=INK, zorder=8)
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=11, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    tx.text(0.02, 0.885, "A =", fontsize=15, va="center")
    T, _box, _ln = _mat(tx, 0.36, 0.94, [[_f(qa), _f(qb)], [_f(qc), _f(qd)]], 0.22, 0.11, fs=15)
    for r in range(2):
        T[r][0].set_color(GREEN)
        T[r][1].set_color(PURPLE)
    orient = ((f"yönelim korunur", "orientation preserved") if QD > 0 else
              (("yönelim ters döner!", "orientation flips!") if QD < 0 else
               ("düzlem bir doğruya çöker", "the plane collapses")))
    E = [(12, f"det A = ad − bc = {_p(qa)}·{_p(qd)} − {_p(qb)}·{_p(qc)} = {_f(QD)}", INK),
         (97, f"Aî = ({_f(qa)}, {_f(qc)})  (1. sütun)" if tr else f"Aî = ({_f(qa)}, {_f(qc)})  (col. 1)", GREEN),
         (101, f"Aĵ = ({_f(qb)}, {_f(qd)})  (2. sütun)" if tr else f"Aĵ = ({_f(qb)}, {_f(qd)})  (col. 2)", PURPLE),
         (106, (f"Alan: 1 → |det A| = {_f(abs(QD))}" if tr else f"Area: 1 → |det A| = {_f(abs(QD))}"),
          BLUE if QD >= 0 else RED),
         (110, orient[0] if tr else orient[1], BLUE if QD >= 0 else RED)]
    items = _panel(tx, E, top=0.74, bottom=0.12, fs=11, width=27)
    live = tx.text(0.02, 0.04, "", fontsize=11, family="DejaVu Sans Mono", color=INK,
                   bbox=dict(boxstyle="round", fc="#F3F4F6", ec="#D1D5DB"))
    off = 0.045 * max(wdt, hgt)
    N = 140

    def place(t, vv):
        n = math.hypot(vv[0], vv[1])
        if n < 1e-6:
            t.set_position((vv[0] + off, vv[1] + off))
            t.set_ha("left")
            t.set_va("bottom")
            return
        p = vv + vv / n * off * 0.7
        t.set_position((p[0], p[1]))
        t.set_ha("left" if vv[0] > 0.3 * n else ("right" if vv[0] < -0.3 * n else "center"))
        t.set_va("bottom" if vv[1] > 0.3 * n else ("top" if vv[1] < -0.3 * n else "center"))

    def update(i):
        t = 0.0 if i < 15 else (_ease((i - 15) / 80) if i < 95 else 1.0)
        Mt = (1 - t) * np.eye(2) + t * A
        lc.set_segments([s @ Mt.T for s in base])
        ex = np.array([[-G, 0], [G, 0]], dtype=float) @ Mt.T
        ey = np.array([[0, -G], [0, G]], dtype=float) @ Mt.T
        axx.set_data(ex[:, 0], ex[:, 1])
        axy.set_data(ey[:, 0], ey[:, 1])
        sq.set_xy(unit @ Mt.T)
        dt = Mt[0, 0] * Mt[1, 1] - Mt[0, 1] * Mt[1, 0]
        col = BLUE if dt >= 0 else RED
        sq.set_facecolor(col)
        sq.set_edgecolor(col)
        ci, cj = Mt[:, 0], Mt[:, 1]
        _set_arrow(ai, (0, 0), ci)
        _set_arrow(aj, (0, 0), cj)
        place(ti, ci)
        place(tj, cj)
        if i >= 97:
            ti.set_text(f"Aî = ({_f(qa)}, {_f(qc)})")
            tj.set_text(f"Aĵ = ({_f(qb)}, {_f(qd)})")
        else:
            ti.set_text("î" if i < 15 else "Aî")
            tj.set_text("ĵ" if i < 15 else "Aĵ")
        cen = Mt @ np.array([0.5, 0.5])
        tarea.set_position((cen[0], cen[1]))
        tarea.set_text(f"{abs(dt):.2f}" if i < 97 else f"|det| = {abs(D):g}")
        live.set_text(f"t = {t:.2f}   det = {dt:+.2f}")
        if i < 15:
            info.set_text("1) Başlangıç: standart ızgara, î ve ĵ" if tr else
                          "1) Start: the standard grid, î and ĵ")
        elif i < 95:
            info.set_text((f"2) I'dan A'ya: alan = {abs(dt):.2f}" + ("  (ters!)" if dt < 0 else "")) if tr
                          else (f"2) From I to A: area = {abs(dt):.2f}" + ("  (flipped!)" if dt < 0 else "")))
        else:
            if QD > 0:
                info.set_text(f"3) det A = {_f(QD)}: alan ×{_f(QD)}, yönelim korunur" if tr else
                              f"3) det A = {_f(QD)}: area ×{_f(QD)}, orientation kept")
            elif QD < 0:
                info.set_text(f"3) det A = {_f(QD)}: alan ×{_f(-QD)}, yönelim ters" if tr else
                              f"3) det A = {_f(QD)}: area ×{_f(-QD)}, orientation flipped")
            else:
                info.set_text("3) det A = 0: düzlem bir doğruya çöker" if tr else
                              "3) det A = 0: the plane collapses to a line")
        _panel_show(items, i)
        return []

    return N, update


def vary(P, rnd):
    a0, b0, c0, d0 = (P[k] for k in ("a", "b", "c", "d"))
    D0 = a0 * d0 - b0 * c0
    if a0 == 1 and d0 == 1 and (b0 == 0) != (c0 == 0):
        k = rnd.choice([1, 2, -1, -2, 3])
        return {"a": 1, "b": k, "c": 0, "d": 1} if rnd.random() < 0.5 else {"a": 1, "b": 0, "c": k, "d": 1}
    for _ in range(2000):
        a, b, c, d = (rnd.randint(-3, 3) for _ in range(4))
        D = a * d - b * c
        if D == 0 or (a, b, c, d) == (1, 0, 0, 1) or D * D0 < 0:
            continue
        if max(abs(x) for x in (a, b, c, d, a + b, c + d)) > 5:
            continue
        return {"a": a, "b": b, "c": c, "d": d}
    return {"a": 2, "b": 1, "c": 1, "d": 2}
'''),
}
EXAMPLES += [
    {"id": "linalg-trans-1", "kind": "matrix_transform",
     "topics": ["shear transformation", "kayma"],
     "title": ("Kayma dönüşümü", "A shear transformation"),
     "q": ("A = {Am} matrisinin düzlemi nasıl dönüştürdüğünü göster: î ve ĵ nereye gider, "
           "birim karenin alanı ne olur? (det A = {detA})",
           "Show how A = {Am} transforms the plane: where do î and ĵ go, and what happens to the "
           "area of the unit square? (det A = {detA})"),
     "P": {"a": 1, "b": 1, "c": 0, "d": 1}},
    {"id": "linalg-trans-2", "kind": "matrix_transform",
     "title": ("Alanı ölçekleyen dönüşüm", "A transformation that scales area"),
     "q": ("A = {Am} birim kareyi hangi paralelkenara götürür? Alanlar kaç katına çıkar?",
           "Which parallelogram does A = {Am} send the unit square to? By what factor do areas change?"),
     "P": {"a": 2, "b": -1, "c": 1, "d": 1}},
    {"id": "linalg-trans-3", "kind": "matrix_transform",
     "topics": ["orientation", "negative determinant", "yönelim"],
     "title": ("Yönelimi ters çeviren dönüşüm", "An orientation-reversing transformation"),
     "q": ("A = {Am} için det A'yı bul. Negatif determinant geometrik olarak ne anlama gelir?",
           "Find det A for A = {Am}. What does a negative determinant mean geometrically?"),
     "P": {"a": 1, "b": 2, "c": 2, "d": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["eigen"] = {
    "course": "linalg",
    "title": ("Özdeğerler ve özvektörler", "Eigenvalues and eigenvectors"),
    "topics": ["eigenvalue", "eigenvalues", "eigenvector", "eigenvectors", "eigenspace",
               "characteristic polynomial", "characteristic equation", "diagonalization",
               "steady state", "özdeğer", "özdeğerler", "özvektör", "özvektörler",
               "karakteristik polinom", "karakteristik denklem", "köşegenleştirme", "öz uzay"],
    "code": _code(_NUM, _ARROW, _PANEL, _MATRIX, r'''

def _e(v):
    v = _q(v)
    if v.denominator == 1:
        return _f(v)
    dd = v.denominator
    while dd % 2 == 0:
        dd //= 2
    while dd % 5 == 0:
        dd //= 5
    if dd == 1:
        return f"{float(v):.6g}".replace("-", "−")
    return _f(v)


def _num(v):
    if isinstance(v, float):
        return f"{v:.4g}".replace("-", "−")
    return _e(v)


def _pe(v):
    s = _num(v)
    return "(" + s + ")" if s.startswith("−") else s


def _vs(v):
    return "(" + ", ".join(_num(x) for x in v) + ")"


def _poly(tr_, det_):
    s = "λ²"
    if tr_ != 0:
        m = abs(tr_)
        s += (" − " if tr_ > 0 else " + ") + ("" if m == 1 else _e(m)) + "λ"
    if det_ != 0:
        s += (" + " if det_ > 0 else " − ") + _e(abs(det_))
    return s


def _lin(p, q):
    s = ""
    for c, var in ((p, "x"), (q, "y")):
        if abs(c) < 1e-12:
            continue
        mag = "" if abs(abs(c) - 1) < 1e-12 else _num(abs(c))
        if s == "":
            s = ("−" if c < 0 else "") + mag + var
        else:
            s += (" − " if c < 0 else " + ") + mag + var
    return (s or "0") + " = 0"


def _evec(a, b, c, d, lam):
    r1 = (a - lam, b)
    r2 = (c, d - lam)
    s1 = abs(r1[0]) + abs(r1[1])
    s2 = abs(r2[0]) + abs(r2[1])
    if s1 < 1e-12 and s2 < 1e-12:
        return None, None
    if s1 >= s2:
        row, x, y = r1, b, lam - a
    else:
        row, x, y = r2, lam - d, c
    if isinstance(x, Fraction) and isinstance(y, Fraction):
        den = x.denominator * y.denominator // math.gcd(x.denominator, y.denominator)
        xi, yi = int(x * den), int(y * den)
        g = math.gcd(abs(xi), abs(yi)) or 1
        xi, yi = xi // g, yi // g
        if xi < 0 or (xi == 0 and yi < 0):
            xi, yi = -xi, -yi
        return row, (Fraction(xi), Fraction(yi))
    x, y = float(x), float(y)
    nrm = math.hypot(x, y)
    x, y = x / nrm, y / nrm
    if x < -1e-12 or (abs(x) < 1e-12 and y < 0):
        x, y = -x, -y
    return row, (x, y)


def _eig(P):
    a, b, c, d = (_q(P[k]) for k in ("a", "b", "c", "d"))
    tr_, det_ = a + d, a * d - b * c
    D = tr_ * tr_ - 4 * det_
    E = {"abcd": (a, b, c, d), "tr": tr_, "det": det_, "D": D, "lams": [], "rows": [],
         "vecs": [], "exact": True, "all": False}
    if D < 0:
        return E
    r = _isq(D)
    if r is None:
        E["exact"] = False
        sD = math.sqrt(float(D))
        lams = [(float(tr_) + sD) / 2, (float(tr_) - sD) / 2]
        a, b, c, d = float(a), float(b), float(c), float(d)
    elif r == 0:
        lams = [tr_ / 2]
    else:
        lams = [(tr_ + r) / 2, (tr_ - r) / 2]
    for lam in lams:
        row, v = _evec(a, b, c, d, lam)
        E["lams"].append(lam)
        E["rows"].append(row)
        E["vecs"].append(v)
    if len(lams) == 1 and E["vecs"][0] is None:
        E["all"] = True
    return E


def solve(P):
    E = _eig(P)
    a, b, c, d = E["abcd"]
    tr_, det_, D = E["tr"], E["det"], E["D"]
    As = f"[[{_e(a)}, {_e(b)}], [{_e(c)}, {_e(d)}]]"
    poly = _poly(tr_, det_)
    steps = [
        (f"A − λI = [[{_e(a)} − λ, {_e(b)}], [{_e(c)}, {_e(d)} − λ]];  özdeğerler det(A − λI) = 0 "
         "denkleminin kökleridir",
         f"A − λI = [[{_e(a)} − λ, {_e(b)}], [{_e(c)}, {_e(d)} − λ]];  the eigenvalues solve "
         "det(A − λI) = 0"),
        (f"({_e(a)} − λ)({_e(d)} − λ) − {_pe(b)}·{_pe(c)} = {poly} = 0   (iz = {_e(tr_)}, det = {_e(det_)})",
         f"({_e(a)} − λ)({_e(d)} − λ) − {_pe(b)}·{_pe(c)} = {poly} = 0   (trace = {_e(tr_)}, det = {_e(det_)})"),
        (f"Δ = iz² − 4·det = {_pe(tr_)}² − 4·{_pe(det_)} = {_e(D)}",
         f"Δ = trace² − 4·det = {_pe(tr_)}² − 4·{_pe(det_)} = {_e(D)}"),
    ]
    if D < 0:
        re_, im = float(tr_) / 2, math.sqrt(-float(D)) / 2
        steps.append((f"Δ < 0 ⇒ reel özdeğer yok: λ = {re_:.4g} ± {im:.4g}i. Hiçbir reel v için Av, "
                      "v'ye paralel olmaz (dönme benzeri dönüşüm).",
                      f"Δ < 0 ⇒ no real eigenvalues: λ = {re_:.4g} ± {im:.4g}i. Av is never parallel "
                      "to a real v (a rotation-like map)."))
        return {"answer": (f"Reel özdeğer yok (λ = {re_:.4g} ± {im:.4g}i)",
                           f"No real eigenvalues (λ = {re_:.4g} ± {im:.4g}i)"),
                "steps": steps, "fmt": {"Am": As, "poly": poly}}
    lams = E["lams"]
    if len(lams) == 2:
        if E["exact"]:
            line = (f"λ = ({_e(tr_)} ± √{_e(D)})/2 = ({_e(tr_)} ± {_e(_isq(D))})/2  ⇒  "
                    f"λ₁ = {_num(lams[0])}, λ₂ = {_num(lams[1])}")
        else:
            line = f"λ = ({_e(tr_)} ± √{_e(D)})/2  ⇒  λ₁ ≈ {_num(lams[0])}, λ₂ ≈ {_num(lams[1])}"
        steps.append((line, line))
    else:
        steps.append((f"Δ = 0 ⇒ çift katlı özdeğer λ = {_num(lams[0])}",
                      f"Δ = 0 ⇒ a repeated eigenvalue λ = {_num(lams[0])}"))
    p_tr, p_en = [], []
    for k, (lam, row, v) in enumerate(zip(lams, E["rows"], E["vecs"])):
        ln, vn = "λ" + SUB[k + 1], "v" + SUB[k + 1]
        if v is None:
            steps.append((f"A − {_num(lam)}I = 0 ⇒ sıfırdan farklı her vektör özvektördür",
                          f"A − {_num(lam)}I = 0 ⇒ every nonzero vector is an eigenvector"))
            p_tr.append(f"λ = {_num(lam)} (her vektör özvektör)")
            p_en.append(f"λ = {_num(lam)} (every vector is an eigenvector)")
            continue
        eq = _lin(row[0], row[1])
        steps.append((f"{ln} = {_num(lam)}: (A − {_pe(lam)}I)v = 0 ⇒ {eq} ⇒ {vn} = {_vs(v)}",
                      f"{ln} = {_num(lam)}: (A − {_pe(lam)}I)v = 0 ⇒ {eq} ⇒ {vn} = {_vs(v)}"))
        av = (a * v[0] + b * v[1], c * v[0] + d * v[1])
        rel = "=" if E["exact"] else "≈"
        steps.append((f"Kontrol: A{vn} = {_vs(av)} {rel} {_pe(lam)}·{_vs(v)} ✓",
                      f"Check: A{vn} = {_vs(av)} {rel} {_pe(lam)}·{_vs(v)} ✓"))
        p_tr.append(f"{ln} = {_num(lam)}, {vn} = {_vs(v)}")
        p_en.append(f"{ln} = {_num(lam)}, {vn} = {_vs(v)}")
    if E["exact"] and len(lams) == 2 and any(lam == 1 for lam in lams):
        k1 = [lam == 1 for lam in lams].index(True)
        v = E["vecs"][k1]
        if v is not None and v[0] * v[1] > 0:
            tot = v[0] + v[1]
            steps.append((f"λ = 1 ⇒ Av = v: kararlı durum. Oranlar {_f(v[0])} : {_f(v[1])} "
                          f"⇒ %{float(v[0] / tot) * 100:.4g} ve %{float(v[1] / tot) * 100:.4g}",
                          f"λ = 1 ⇒ Av = v: a steady state. Ratio {_f(v[0])} : {_f(v[1])} "
                          f"⇒ {float(v[0] / tot) * 100:.4g}% and {float(v[1] / tot) * 100:.4g}%"))
    return {"answer": ("; ".join(p_tr), "; ".join(p_en)), "steps": steps,
            "fmt": {"Am": As, "poly": poly}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    E = _eig(P)
    A = np.array([[float(P["a"]), float(P["b"])], [float(P["c"]), float(P["d"])]])
    gs = fig.add_gridspec(1, 2, width_ratios=[1.3, 1], left=0.05, right=0.98, top=0.95,
                          bottom=0.06, wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    tx.set_xlim(0, 1)
    tx.set_ylim(0, 1)
    sig = float(np.linalg.svd(A, compute_uv=False).max())
    L = max(1.6, 1.12 * sig + 0.3)
    ax.set_xlim(-L, L)
    ax.set_ylim(-L, 1.34 * L)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color=GRAY, lw=1)
    ax.axvline(0, color=GRAY, lw=1)
    ax.tick_params(labelsize=8)
    th = np.linspace(0, 2 * np.pi, 241)
    ax.plot(np.cos(th), np.sin(th), color=GRAY, lw=1, ls="--", alpha=0.7)
    trace, = ax.plot([], [], color=ORANGE, lw=1.4, alpha=0.5)
    dirs, keys = [], []
    for k, v in enumerate(E["vecs"]):
        if v is None:
            dirs.append(None)
            continue
        vx, vy = float(v[0]), float(v[1])
        nv = math.hypot(vx, vy)
        vx, vy = vx / nv, vy / nv
        if vy > 1e-9 or (abs(vy) <= 1e-9 and vx < 0):
            vx, vy = -vx, -vy
        dirs.append((vx, vy))
        phi = math.atan2(vy, vx) % math.pi
        keys += [(phi, k), (phi + math.pi, k)]
    keys.sort()
    T0, S, H = 10, 120, 10
    move = S - H * len(keys)
    TH, HK = [], []
    prev = 0.0
    for ang, k in keys + [(2 * math.pi, -1)]:
        nseg = int(round(move * (ang - prev) / (2 * math.pi)))
        for m in range(nseg):
            TH.append(prev + (ang - prev) * m / nseg)
            HK.append(-1)
        if k >= 0:
            TH += [ang] * H
            HK += [k] * H
        prev = ang
    while len(TH) < S:
        TH.append(2 * math.pi)
        HK.append(-1)
    TH, HK = TH[:S], HK[:S]
    first = [HK.index(k) if k in HK else S for k in range(len(E["lams"]))]
    lam_f = [float(x) for x in E["lams"]]
    spans, elabs, ev_arrows = [], [], []
    for k, dv in enumerate(dirs):
        if dv is None:
            spans.append(None)
            elabs.append(None)
            ev_arrows.append(None)
            continue
        ln, = ax.plot([-3 * L * dv[0], 3 * L * dv[0]], [-3 * L * dv[1], 3 * L * dv[1]], ls="--",
                      lw=1.6, color=PURPLE, alpha=0.0, zorder=2)
        spans.append(ln)
        R = 0.95 * L / max(abs(dv[0]), abs(dv[1]))
        elabs.append(ax.text(R * dv[0], R * dv[1], f"λ{SUB[k + 1]} = {_num(E['lams'][k])}",
                             color=PURPLE, fontsize=11, fontweight="bold", alpha=0.0,
                             ha="left" if dv[0] < -1e-9 else ("right" if dv[0] > 1e-9 else "center"),
                             va="bottom", zorder=8,
                             bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.0)))
        ev_arrows.append((_arrow(ax, BLUE, lw=2.0, z=7, ms=14),
                          _arrow(ax, GREEN if lam_f[k] >= 0 else RED, lw=6, z=5, ms=22)))
    av = _arrow(ax, BLUE, lw=2.4, z=6)
    aAv = _arrow(ax, ORANGE, lw=3, z=5)
    ring, = ax.plot([], [], "o", ms=18, mfc="none", mec=GREEN, mew=2.2, zorder=7)
    tv = ax.text(0, 0, "v", color=BLUE, fontsize=13, fontweight="bold", ha="center", va="center", zorder=8)
    tAv = ax.text(0, 0, "Av", color=ORANGE, fontsize=13, fontweight="bold", ha="center", va="center", zorder=8)
    angt = tx.text(0.02, 0.03, "", transform=tx.transAxes, ha="left", fontsize=11, color=GRAY,
                   family="DejaVu Sans Mono")
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=10.5, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    a, b, c, d = E["abcd"]
    tx.text(0.02, 0.885, "A =", fontsize=15, va="center")
    _mat(tx, 0.36, 0.94, [[_e(a), _e(b)], [_e(c), _e(d)]], 0.24, 0.11, fs=15)
    ent = [(0, "det(A − λI) = 0", INK), (6, _poly(E["tr"], E["det"]) + " = 0", INK)]
    if E["D"] < 0:
        ent.append((14, "Δ < 0 ⇒ reel λ yok" if tr else "Δ < 0 ⇒ no real λ", RED))
    elif len(lam_f) == 2:
        rel = " = " if E["exact"] else " ≈ "
        ent.append((14, f"λ₁{rel}{_num(E['lams'][0])},  λ₂{rel}{_num(E['lams'][1])}", INK))
    else:
        ent.append((14, f"λ = {_num(E['lams'][0])} (" + ("çift katlı)" if tr else "repeated)"), INK))
    for k, v in enumerate(E["vecs"]):
        if v is not None:
            ent.append((T0 + first[k], f"v{SUB[k + 1]} = {_vs(v)}  (λ{SUB[k + 1]} = {_num(E['lams'][k])})",
                        PURPLE))
    ent.append((T0 + S, "Özvektör: Av, v ile aynı doğruda kalır" if tr else
                "Eigenvector: Av stays on the line of v", GRAY))
    items = _panel(tx, ent, top=0.74, bottom=0.1, fs=11, width=30, dy=0.085)
    N = T0 + S + 30

    def lab_at(t, vec, extra):
        n = math.hypot(vec[0], vec[1])
        if n < 1e-9:
            t.set_position((0.12 * L, 0.12 * L))
        else:
            t.set_position((vec[0] + vec[0] / n * extra, vec[1] + vec[1] / n * extra))

    def update(i):
        final = i >= T0 + S
        j = S if final else (i - T0 if i >= T0 else -1)
        for k, ln in enumerate(spans):
            if ln is None:
                continue
            al = 0.75 if j >= first[k] else 0.0
            ln.set_alpha(al)
            elabs[k].set_alpha(1.0 if al > 0 else 0.0)
            elabs[k].get_bbox_patch().set_alpha(0.8 if al > 0 else 0.0)
            va, vb = ev_arrows[k]
            if final:
                dv = np.array(dirs[k])
                _set_arrow(va, (0, 0), dv)
                _set_arrow(vb, (0, 0), lam_f[k] * dv, alpha=0.55)
            else:
                _set_arrow(va, (0, 0), (0, 0))
                _set_arrow(vb, (0, 0), (0, 0))
        if final:
            for art in (av, aAv):
                _set_arrow(art, (0, 0), (0, 0))
            ring.set_data([], [])
            tv.set_text("")
            tAv.set_text("")
            tt = np.linspace(0, 2 * np.pi, 160)
            pts = A @ np.vstack([np.cos(tt), np.sin(tt)])
            trace.set_data(pts[0], pts[1])
            angt.set_text("")
            if E["D"] < 0:
                info.set_text("3) Reel özdeğer yok: Av hiç v'ye paralel olmadı" if tr else
                              "3) No real eigenvalues: Av was never parallel to v")
            else:
                parts = []
                for k, v in enumerate(E["vecs"]):
                    rel = " = " if E["exact"] else " ≈ "
                    if v is None:
                        parts.append(f"λ = {_num(E['lams'][k])}: " + ("her v" if tr else "every v"))
                    else:
                        parts.append(f"λ{SUB[k + 1]}{rel}{_num(E['lams'][k])},  v{SUB[k + 1]} = {_vs(v)}")
                info.set_text("3) " + "\n    ".join(parts))
            _panel_show(items, i)
            return []
        if j < 0:
            theta, hold, g = 0.0, -1, _ease(_ph(i, 0, 8))
        else:
            theta, hold, g = TH[j], HK[j], 1.0
        vv = g * np.array([math.cos(theta), math.sin(theta)])
        Avv = A @ vv
        _set_arrow(av, (0, 0), vv)
        _set_arrow(aAv, (0, 0), Avv)
        is_eig = hold >= 0 or (E["all"] and g >= 1)
        lam = lam_f[hold] if hold >= 0 else (lam_f[0] if E["all"] else 0.0)
        col = (GREEN if lam >= 0 else RED) if is_eig else ORANGE
        aAv.set_color(col)
        tAv.set_color(col)
        if is_eig and g >= 1:
            ring.set_data([Avv[0]], [Avv[1]])
            ring.set_markeredgecolor(col)
        else:
            ring.set_data([], [])
        lab_at(tv, vv, 0.16 * L)
        lab_at(tAv, Avv, 0.2 * L)
        tv.set_text("v" if g >= 1 else "")
        tAv.set_text("Av" if g >= 1 else "")
        if j >= 0:
            tt = np.linspace(0, theta, max(2, int(theta / (2 * np.pi) * 160)))
            pts = A @ np.vstack([np.cos(tt), np.sin(tt)])
            trace.set_data(pts[0], pts[1])
        else:
            trace.set_data([], [])
        angt.set_text(f"θ = {math.degrees(theta) % 360:.0f}°")
        if j < 0:
            info.set_text("1) v birim çember üzerinde dönecek; turuncu ok Av" if tr else
                          "1) v will turn around the unit circle; orange arrow = Av")
        elif is_eig:
            lm = _num(E["lams"][hold if hold >= 0 else 0])
            info.set_text((f"Av ∥ v ⇒ özvektör!  Av = {lm}·v" if tr else
                           f"Av ∥ v ⇒ eigenvector!  Av = {lm}·v") +
                          (("\n(λ < 0: Av ters yönde)" if tr else "\n(λ < 0: Av points backwards)")
                           if lam < 0 else ""))
        else:
            info.set_text("2) v'yi döndür: Av genelde başka yöne bakar" if tr else
                          "2) Turn v: Av usually points somewhere else")
        _panel_show(items, i)
        return []

    return N, update


def vary(P, rnd):
    vals = [P[k] for k in ("a", "b", "c", "d")]
    markov = (any(isinstance(x, float) and not float(x).is_integer() for x in vals)
              and abs(vals[0] + vals[2] - 1) < 1e-9 and abs(vals[1] + vals[3] - 1) < 1e-9)
    if markov:
        a = rnd.choice([0.6, 0.7, 0.8, 0.9])
        b = rnd.choice([0.1, 0.2, 0.3, 0.4])
        return {"a": a, "b": b, "c": round(1 - a, 1), "d": round(1 - b, 1)}
    for _ in range(4000):
        a, b, c, d = rnd.randint(-3, 5), rnd.randint(-3, 4), rnd.randint(-3, 4), rnd.randint(-3, 5)
        if b == 0 and c == 0:
            continue
        t_, dt = a + d, a * d - b * c
        D = t_ * t_ - 4 * dt
        if D <= 0:
            continue
        r = math.isqrt(D)
        if r * r != D:
            continue
        l1, l2 = (t_ + r) // 2, (t_ - r) // 2
        if l1 == 0 or l2 == 0 or max(abs(l1), abs(l2)) > 5:
            continue
        return {"a": a, "b": b, "c": c, "d": d}
    return {"a": 2, "b": 1, "c": 1, "d": 2}
'''),
}
EXAMPLES += [
    {"id": "linalg-eig-1", "kind": "eigen",
     "title": ("Simetrik matrisin özdeğerleri", "Eigenvalues of a symmetric matrix"),
     "q": ("A = {Am} matrisinin karakteristik polinomunu yaz; özdeğerlerini ve özvektörlerini bul.",
           "Write the characteristic polynomial of A = {Am}; find its eigenvalues and eigenvectors."),
     "P": {"a": 2, "b": 1, "c": 1, "d": 2}},
    {"id": "linalg-eig-2", "kind": "eigen",
     "title": ("Negatif özdeğer", "A negative eigenvalue"),
     "q": ("A = {Am} için det(A − λI) = 0 denklemini çöz ve her özdeğere ait bir özvektör bul. "
           "Negatif özdeğer geometrik olarak ne demektir?",
           "For A = {Am}, solve det(A − λI) = 0 and find an eigenvector for each eigenvalue. "
           "What does a negative eigenvalue mean geometrically?"),
     "P": {"a": 1, "b": 2, "c": 3, "d": 0}},
    {"id": "linalg-eig-3", "kind": "eigen",
     "topics": ["markov chain", "markov", "transition matrix", "geçiş matrisi", "kararlı durum"],
     "title": ("Göç modeli: kararlı dağılım", "Migration model: the steady state"),
     "q": ("Şehir ve kırsal nüfus payları her yıl x ↦ Ax ile değişiyor; A = {Am} (sütun toplamları 1). "
           "Özdeğerleri ve özvektörleri bul; λ = 1'e ait özvektör uzun vadeli dağılımı verir.",
           "City and countryside population shares change every year by x ↦ Ax with A = {Am} "
           "(columns sum to 1). Find the eigenvalues and eigenvectors; the eigenvector for λ = 1 "
           "gives the long-run distribution."),
     "P": {"a": 0.8, "b": 0.3, "c": 0.2, "d": 0.7}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["gaussian_elim"] = {
    "course": "linalg",
    "title": ("Gauss yok etme ve RREF", "Gaussian elimination and RREF"),
    "topics": ["inverse of a matrix", "matrix inverse", "inverse matrices", "null space", "ters matris", "sıfır uzayı", "gaussian elimination", "gauss-jordan", "gauss jordan", "row operations",
               "elementary row operations", "row echelon form", "reduced row echelon", "rref",
               "augmented matrix", "systems of linear equations", "linear systems",
               "back substitution", "gauss eliminasyonu", "gauss yok etme", "satır işlemleri",
               "elemanter satır işlemleri", "eşelon form", "genişletilmiş matris",
               "lineer denklem sistemi", "doğrusal denklem sistemleri"],
    "code": _code(_NUM, _PANEL, _MATRIX, r'''
from matplotlib.patches import Rectangle

VARS = "xyzw"


def _R(k):
    return "R" + SUB[k + 1]


def _gj(M):
    A = [[_q(x) for x in row] for row in M]
    n = len(A)
    ops = []

    def snap():
        return [row[:] for row in A]

    singular = False
    for k in range(n):
        cand = [r for r in range(k, n) if A[r][k] != 0]
        if not cand:
            singular = True
            break
        if abs(A[k][k]) == 1:
            piv = k
        else:
            ones = [r for r in cand if abs(A[r][k]) == 1]
            piv = ones[0] if ones else cand[0]
        if piv != k:
            A[k], A[piv] = A[piv], A[k]
            ops.append({"t": "swap", "rows": (k, piv), "col": k, "ph": 0,
                        "lab": f"{_R(k)} ↔ {_R(piv)}", "M": snap()})
        p = A[k][k]
        if p != 1:
            A[k] = [x / p for x in A[k]]
            ops.append({"t": "scale", "rows": (k,), "col": k, "ph": 0,
                        "lab": f"{_R(k)} ← {_cf(1 / p)}{_R(k)}", "M": snap()})
        for r in range(k + 1, n):
            m = A[r][k]
            if m != 0:
                A[r] = [x - m * y for x, y in zip(A[r], A[k])]
                ops.append({"t": "add", "rows": (r, k), "col": k, "ph": 0,
                            "lab": f"{_R(r)} ← {_R(r)} {'−' if m > 0 else '+'} {_cf(abs(m))}{_R(k)}",
                            "M": snap()})
    ref = len(ops)
    U = snap()
    if not singular:
        for k in range(n - 1, 0, -1):
            for r in range(k - 1, -1, -1):
                m = A[r][k]
                if m != 0:
                    A[r] = [x - m * y for x, y in zip(A[r], A[k])]
                    ops.append({"t": "add", "rows": (r, k), "col": k, "ph": 1,
                                "lab": f"{_R(r)} ← {_R(r)} {'−' if m > 0 else '+'} {_cf(abs(m))}{_R(k)}",
                                "M": snap()})
    return ops, ref, singular, U, snap()


def _backsub(U):
    n = len(U)
    vals = {}
    lines = []
    for r in range(n - 1, -1, -1):
        terms = [c for c in range(r + 1, n) if U[r][c] != 0]
        val = U[r][n] - sum(U[r][c] * vals[c] for c in terms)
        expr = _f(U[r][n]) + "".join(f" − ({_f(U[r][c])})({_f(vals[c])})" for c in terms)
        lines.append(f"{VARS[r]} = {expr}" + (f" = {_f(val)}" if terms else ""))
        vals[r] = val
    return lines, [vals[r] for r in range(n)]


def _mline(M):
    n = len(M)
    return "[" + "; ".join(" ".join(_f(x) for x in row[:n]) + " | " + _f(row[n]) for row in M) + "]"


def solve(P):
    M = P["M"]
    n = len(M)
    ops, ref, sing, U, R = _gj(M)
    eqs = [_side(row[:n], VARS[:n]) + " = " + _f(row[n]) for row in M]
    steps = [(f"Genişletilmiş matris [A | b] = {_mline([[_q(x) for x in r] for r in M])}",
              f"Augmented matrix [A | b] = {_mline([[_q(x) for x in r] for r in M])}")]
    for k, op in enumerate(ops):
        if k == ref:
            break
        steps.append((f"{op['lab']}  ⇒  {_mline(op['M'])}", f"{op['lab']}  ⇒  {_mline(op['M'])}"))
    fmt = {f"eq{k + 1}": e for k, e in enumerate(eqs)}
    fmt["system"] = ",  ".join(eqs)
    if sing:
        steps.append(("Bir sütunda pivot bulunamadı ⇒ katsayı matrisi tekil; tek çözüm yok.",
                      "No pivot in some column ⇒ the coefficient matrix is singular; no unique solution."))
        return {"answer": ("Tek çözüm yok (tekil sistem)", "No unique solution (singular system)"),
                "steps": steps, "fmt": fmt}
    steps.append(("Satır eşelon form (REF) elde edildi; geriye doğru yerine koyma:",
                  "Row echelon form (REF) reached; back substitution:"))
    bl, vals = _backsub(U)
    for s in bl:
        steps.append((s, s))
    if len(ops) > ref:
        steps.append(("Gauss–Jordan: pivotların üstünü de sıfırla (RREF):",
                      "Gauss–Jordan: also clear above the pivots (RREF):"))
        for op in ops[ref:]:
            steps.append((f"{op['lab']}  ⇒  {_mline(op['M'])}", f"{op['lab']}  ⇒  {_mline(op['M'])}"))
    ans = ", ".join(f"{VARS[r]} = {_f(vals[r])}" for r in range(n))
    chk = "; ".join(_side(row[:n], [f"({_f(v)})" for v in vals]).replace(")(", ")·(") + " = " + _f(row[n])
                    for row in M[:1])
    steps.append((f"RREF = {_mline(R)}  ⇒  {ans}", f"RREF = {_mline(R)}  ⇒  {ans}"))
    steps.append((f"Kontrol (1. denklem): {eqs[0].split(' = ')[0]} → {chk} ✓",
                  f"Check (equation 1): {eqs[0].split(' = ')[0]} → {chk} ✓"))
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    M = P["M"]
    n = len(M)
    ops, ref, sing, U, R = _gj(M)
    M0 = [[_q(x) for x in row] for row in M]
    states = [M0] + [op["M"] for op in ops]
    nops = len(ops)
    nb = nops - ref
    D = max(9, min(14, (172 - 46) // max(1, nops)))
    T0, HB = 12, 16
    starts = [T0 + k * D if k < ref else T0 + ref * D + HB + (k - ref) * D for k in range(nops)]
    t_ref = T0 + ref * D
    t_back = t_ref + HB
    t_end = t_back + nb * D
    N = max(60, t_end + 18)
    app = int(D * 0.45)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1], left=0.02, right=0.99, top=0.97,
                          bottom=0.03, wspace=0.04)
    ax = fig.add_subplot(gs[0, 0])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    lg = fig.add_subplot(gs[0, 1])
    lg.axis("off")
    lg.add_patch(Rectangle((0, 0), 1, 1, transform=lg.transAxes, fc="#F9FAFB", ec="#E5E7EB", zorder=0))
    cols = n + 1
    cw = min(0.17, 0.74 / cols)
    ch = min(0.13, 0.42 / n)
    x0 = 0.53 - (cols - 1) * cw / 2
    y0 = 0.55 + (n - 1) * ch / 2
    wmax = max(len(_f(x)) for S_ in states for row in S_ for x in row)
    fs = 16 if wmax <= 3 else (14 if wmax <= 5 else 12)
    T, box, _ = _mat(ax, x0, y0, [[""] * cols for _ in range(n)], cw, ch, fs=fs, bar=n)
    left, right, top, bot = box
    for r in range(n):
        ax.text(left - 0.045, y0 - r * ch, _R(r), ha="center", va="center", fontsize=11, color=GRAY)
    for c in range(cols):
        ax.text(x0 + c * cw, top + 0.03, VARS[c] if c < n else "b", ha="center", va="bottom",
                fontsize=10, color=GRAY, style="italic")
    rect_t = Rectangle((left, 0), right - left, 0.92 * ch, fc=ORANGE, ec="none", alpha=0.22, zorder=1)
    rect_s = Rectangle((left, 0), right - left, 0.92 * ch, fc=BLUE, ec="none", alpha=0.16, zorder=1)
    ax.add_patch(rect_t)
    ax.add_patch(rect_s)
    oplab = ax.text(0.53, 0.2, "", ha="center", va="center", fontsize=17, color=INK,
                    family="DejaVu Sans Mono")
    opexp = ax.text(0.53, 0.1, "", ha="center", va="center", fontsize=10.5, color=GRAY)
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=11, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    ent = [(T0 - 6, "1) İleri yok etme" if tr else "1) Forward elimination", BLUE)]
    for k in range(ref):
        ent.append((starts[k], "    " + ops[k]["lab"], INK))
    if sing:
        ent.append((t_ref, "Pivot yok ⇒ tek çözüm yok" if tr else "No pivot ⇒ no unique solution", RED))
        vals = []
    else:
        bl, vals = _backsub(U)
        ent.append((t_ref, "2) Geriye doğru yerine koyma" if tr else "2) Back substitution", BLUE))
        for q, s in enumerate(bl):
            ent.append((t_ref + 2 + 4 * q, "    " + s, INK))
        if nb:
            ent.append((t_back, "3) Gauss–Jordan → RREF", BLUE))
        for k in range(ref, nops):
            ent.append((starts[k], "    " + ops[k]["lab"], INK))
    sol_s = ",  ".join(f"{VARS[r]} = {_f(vals[r])}" for r in range(len(vals)))
    if not sing:
        ent.append((t_end, sol_s, GREEN))
    rows = sum(len(_wrap(e[1], 40)) for e in ent)
    items = _panel(lg, ent, top=0.96, bottom=0.02, fs=10 if rows > 14 else 10.5, width=40, dy=0.062)
    expl = {"swap": ("Kullanılabilir bir pivot için satırları değiştir", "Swap rows to get a usable pivot"),
            "scale": ("Pivotu 1 yap", "Make the pivot 1")}

    def update(i):
        applied = sum(1 for k in range(nops) if i >= starts[k] + app)
        act = -1
        for k in range(nops):
            if starts[k] <= i < starts[k] + D:
                act = k
        S = states[applied]
        prev = states[applied - 1] if applied > 0 else S
        done = i >= t_end and not sing
        for r in range(n):
            for c in range(cols):
                T[r][c].set_text(_f(S[r][c]))
                changed = act >= 0 and applied == act + 1 and prev[r][c] != S[r][c]
                if changed:
                    T[r][c].set_color(ORANGE)
                    T[r][c].set_fontweight("bold")
                else:
                    T[r][c].set_color(GREEN if (done and c == n) else INK)
                    T[r][c].set_fontweight("bold" if (done and c == n) else "normal")
        if act >= 0:
            op = ops[act]
            rows_ = op["rows"]
            rect_t.set_y(y0 - rows_[0] * ch - 0.46 * ch)
            rect_t.set_visible(True)
            rect_t.set_facecolor(PURPLE if op["t"] == "swap" else ORANGE)
            if len(rows_) > 1:
                rect_s.set_y(y0 - rows_[1] * ch - 0.46 * ch)
                rect_s.set_facecolor(PURPLE if op["t"] == "swap" else BLUE)
                rect_s.set_visible(True)
            else:
                rect_s.set_visible(False)
            oplab.set_text(op["lab"])
            oplab.set_color(INK)
            if op["t"] in expl:
                e = expl[op["t"]]
            elif op["ph"] == 0:
                e = (f"{VARS[op['col']]} sütununda pivotun altını sıfırla",
                     f"Clear below the pivot in the {VARS[op['col']]} column")
            else:
                e = (f"{VARS[op['col']]} sütununda pivotun üstünü sıfırla",
                     f"Clear above the pivot in the {VARS[op['col']]} column")
            opexp.set_text(e[0] if tr else e[1])
        else:
            rect_t.set_visible(False)
            rect_s.set_visible(False)
            if i < T0:
                oplab.set_text("[A | b]")
                oplab.set_color(INK)
                opexp.set_text("")
            elif sing and i >= t_ref:
                oplab.set_text("Tek çözüm yok" if tr else "No unique solution")
                oplab.set_color(RED)
                opexp.set_text("")
            elif t_ref <= i < t_back:
                oplab.set_text("REF ✓")
                oplab.set_color(BLUE)
                opexp.set_text("Satır eşelon form: alttan yukarı yerine koy" if tr else
                               "Row echelon form: substitute from the bottom up")
            elif done:
                oplab.set_text(sol_s)
                oplab.set_color(GREEN)
                opexp.set_text("İndirgenmiş satır eşelon form (RREF) ✓" if tr else
                               "Reduced row echelon form (RREF) ✓")
            else:
                oplab.set_text("")
                opexp.set_text("")
        if i < T0:
            info.set_text("Genişletilmiş matris [A | b]" if tr else "Augmented matrix [A | b]")
        elif i < t_ref:
            info.set_text("1) İleri yok etme: pivotu 1 yap, altını sıfırla" if tr else
                          "1) Forward elimination: pivot → 1, clear below")
        elif sing:
            info.set_text("Pivot bulunamadı: sistem tekil" if tr else "No pivot found: singular system")
        elif i < t_back:
            info.set_text("2) Geriye doğru yerine koyma" if tr else "2) Back substitution")
        elif i < t_end:
            info.set_text("3) Gauss–Jordan: pivotların üstünü sıfırla" if tr else
                          "3) Gauss–Jordan: clear above the pivots")
        else:
            info.set_text(("Çözüm: " if tr else "Solution: ") + sol_s)
        _panel_show(items, i)
        return []

    return N, update


def vary(P, rnd):
    n = len(P["M"])
    need_swap = P["M"][0][0] == 0
    nonneg = all(x >= 0 for row in P["M"] for x in row)
    for _ in range(4000):
        lo = 0 if nonneg else -2
        L = [[1 if i == j else (rnd.randint(lo, 3) if i > j else 0) for j in range(n)] for i in range(n)]
        if need_swap:
            L[1][0] = 0
        U = [[0] * n for _ in range(n)]
        for i in range(n):
            if nonneg:
                U[i][i] = rnd.choice([1, 1, 2]) if i < n - 1 else rnd.choice([1, 2, 3])
            else:
                U[i][i] = rnd.choice([1, 1, -1, 2]) if i < n - 1 else rnd.choice([1, -1, 2, 3, -2])
            for j in range(i + 1, n):
                U[i][j] = rnd.randint(0 if nonneg else -2, 2)
        A = [[sum(L[i][k] * U[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
        if max(abs(x) for row in A for x in row) > 7:
            continue
        if any(sum(1 for x in row if x != 0) < 2 for row in A):
            continue
        if need_swap:
            A[0], A[1] = A[1], A[0]
            if A[0][0] != 0:
                continue
        sol = [rnd.randint(1, 9) if nonneg else rnd.randint(-4, 5) for _ in range(n)]
        b = [sum(A[i][j] * sol[j] for j in range(n)) for i in range(n)]
        if max(abs(x) for x in b) > (60 if nonneg else 30):
            continue
        return {"M": [A[i] + [b[i]] for i in range(n)]}
    return {"M": [list(r) for r in P["M"]]}
'''),
}
EXAMPLES += [
    {"id": "linalg-gauss-1", "kind": "gaussian_elim",
     "title": ("3×3 sistem: Gauss yok etme", "3×3 system by Gaussian elimination"),
     "q": ("Sistemi genişletilmiş matris ve satır işlemleriyle çöz:  {eq1};  {eq2};  {eq3}",
           "Solve the system with an augmented matrix and row operations:  {eq1};  {eq2};  {eq3}"),
     "P": {"M": [[1, 1, 1, 6], [2, -1, 1, 3], [1, 2, -1, 2]]}},
    {"id": "linalg-gauss-2", "kind": "gaussian_elim",
     "topics": ["word problem", "sözel problem"],
     "title": ("Sözel problem: kırtasiye fiyatları", "Word problem: stationery prices"),
     "q": ("Bir kırtasiyede defterin fiyatı x, kalemin y, dosyanın z TL. Üç farklı alışverişin "
           "tutarları şu denklemleri veriyor: {eq1};  {eq2};  {eq3}. Fiyatları Gauss–Jordan "
           "yöntemiyle bul.",
           "At a stationery shop a notebook costs x, a pen y and a folder z. Three different "
           "purchases give the equations {eq1};  {eq2};  {eq3}. Find the prices with "
           "Gauss–Jordan elimination."),
     "P": {"M": [[1, 1, 1, 13], [2, 1, 3, 29], [3, 2, 1, 24]]}},
    {"id": "linalg-gauss-3", "kind": "gaussian_elim",
     "topics": ["row swap", "pivot", "satır değiştirme"],
     "title": ("Satır değiştirme gerektiren sistem", "A system that needs a row swap"),
     "q": ("İlk pivot sıfır olduğunda ne yapılır? Sistemi RREF'e indirerek çöz:  {eq1};  {eq2};  {eq3}",
           "What do we do when the first pivot is zero? Solve by reducing to RREF:  {eq1};  {eq2};  {eq3}"),
     "P": {"M": [[0, 2, 1, 7], [1, -1, 2, 5], [2, 1, -1, 1]]}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["dot_projection"] = {
    "course": "linalg",
    "title": ("İç çarpım, açı ve izdüşüm", "Dot product, angle and projection"),
    "topics": ["dot product", "scalar product", "inner product", "angle between vectors",
               "projection", "vector projection", "orthogonal projection", "orthogonal",
               "orthogonality", "work", "nokta çarpım", "iç çarpım", "skaler çarpım", "izdüşüm",
               "vektörler arası açı", "dik izdüşüm", "diklik"],
    "code": _code(_NUM, _ARROW, _PANEL, r'''

def _dp(P):
    u = [_q(x) for x in P["u"]]
    v = [_q(x) for x in P["v"]]
    dot = u[0] * v[0] + u[1] * v[1]
    uu = u[0] * u[0] + u[1] * u[1]
    vv = v[0] * v[0] + v[1] * v[1]
    k = dot / vv
    pr = [k * x for x in v]
    pe = [a - b for a, b in zip(u, pr)]
    return u, v, dot, uu, vv, k, pr, pe


def solve(P):
    u, v, dot, uu, vv, k, pr, pe = _dp(P)
    expr = f"({_f(u[0])})({_f(v[0])}) + ({_f(u[1])})({_f(v[1])})"
    mu, ru, _ = _mag(u)
    mv, rv, _ = _mag(v)
    rp = _isq(uu * vv)
    cosf = float(dot) / math.sqrt(float(uu * vv))
    ang = math.degrees(math.acos(max(-1.0, min(1.0, cosf))))
    cos_s = f"{_f(dot)} / ({ru}·{rv})" + (f" = {_f(dot / rp)}" if rp is not None else "") + f" ≈ {_g(cosf)}"
    rvq = _isq(vv)
    comp = f"{_f(dot)}/{rv}" + (f" = {_f(dot / rvq)}" if rvq is not None else
                                 f" ≈ {_g(float(dot) / math.sqrt(float(vv)))}")
    if dot > 0:
        kind = ("dar açı", "acute angle")
    elif dot < 0:
        kind = ("geniş açı", "obtuse angle")
    else:
        kind = ("dik açı: u ⊥ v", "right angle: u ⊥ v")
    chk = pe[0] * v[0] + pe[1] * v[1]
    steps = [
        (f"u·v = u₁v₁ + u₂v₂ = {expr} = {_f(dot)}", f"u·v = u₁v₁ + u₂v₂ = {expr} = {_f(dot)}"),
        (f"|u| = {mu},   |v| = {mv}", f"|u| = {mu},   |v| = {mv}"),
        (f"cos θ = u·v / (|u|·|v|) = {cos_s}  ⇒  θ ≈ {ang:.2f}° ({kind[0]})",
         f"cos θ = u·v / (|u|·|v|) = {cos_s}  ⇒  θ ≈ {ang:.2f}° ({kind[1]})"),
        (f"Vektör izdüşümü: proj_v(u) = (u·v / |v|²)·v = ({_f(dot)}/{_f(vv)})·{_vec(v)} = {_vec(pr)}",
         f"Vector projection: proj_v(u) = (u·v / |v|²)·v = ({_f(dot)}/{_f(vv)})·{_vec(v)} = {_vec(pr)}"),
        (f"Skaler izdüşüm: comp_v(u) = u·v / |v| = {comp}",
         f"Scalar projection: comp_v(u) = u·v / |v| = {comp}"),
        (f"Dik bileşen: u − proj_v(u) = {_vec(pe)};  {_vec(pe)}·v = {_f(chk)} ✓ (v'ye dik)",
         f"Orthogonal part: u − proj_v(u) = {_vec(pe)};  {_vec(pe)}·v = {_f(chk)} ✓ (perpendicular to v)"),
    ]
    ans = f"u·v = {_f(dot)}, θ ≈ {ang:.2f}°, proj_v(u) = {_vec(pr)}"
    fmt = {"U": _vec(u), "V": _vec(v), "PR": _vec(pr), "PE": _vec(pe), "dot": _f(dot),
           "expr": expr, "mu": mu, "mv": mv, "cos": cos_s, "ang": f"{ang:.2f}°",
           "kq": f"({_f(dot)}/{_f(vv)})·{_vec(v)}"}
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    sol = solve(P)
    F = sol["fmt"]
    u = np.array([float(x) for x in P["u"]])
    v = np.array([float(x) for x in P["v"]])
    k = float(np.dot(u, v) / np.dot(v, v))
    Fp = k * v
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], left=0.06, right=0.98, top=0.93,
                          bottom=0.07, wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    pts = np.array([[0.0, 0.0], u, v, Fp])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    span = max(float((hi - lo).max()), 4.0)
    pad = 0.12 * span + 0.6
    ax.set_xlim(lo[0] - pad, hi[0] + pad)
    ax.set_ylim(lo[1] - pad, hi[1] + pad + 0.2 * span)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color=GRAY, lw=1)
    ax.axvline(0, color=GRAY, lw=1)
    ax.tick_params(labelsize=8)
    e = v / np.linalg.norm(v)
    spanl, = ax.plot([-4 * span * e[0], 4 * span * e[0]], [-4 * span * e[1], 4 * span * e[1]],
                     ls="--", color=GRAY, lw=1.3, alpha=0.0, zorder=1)
    a_u = _arrow(ax, BLUE, z=5)
    a_v = _arrow(ax, ORANGE, z=5)
    a_pr = _arrow(ax, GREEN, lw=3.6, z=6)
    a_pe = _arrow(ax, PURPLE, lw=2.2, ls="--", z=4)
    arc, = ax.plot([], [], color=INK, lw=1.5, zorder=3)
    drop, = ax.plot([], [], ls="--", color=RED, lw=1.8, zorder=4)
    mover, = ax.plot([], [], "o", color=RED, ms=7, zorder=7)
    rmark, = ax.plot([], [], color=RED, lw=1.4, zorder=4)
    off = 0.06 * span
    kw = dict(fontsize=13, fontweight="bold", ha="center", va="center", zorder=8)
    t_u = ax.text(*_side_label(u, v, off), "u", color=BLUE, **kw)
    t_v = ax.text(*_side_label(v, u, off), "v", color=ORANGE, **kw)
    t_pr = ax.text(*_side_label(Fp, -u, 1.4 * off, 0.55), "proj", color=GREEN, fontsize=11,
                   fontweight="bold", ha="center", va="center", zorder=8)
    au_, av_ = math.atan2(u[1], u[0]), math.atan2(v[1], v[0])
    dlt = (au_ - av_ + math.pi) % (2 * math.pi) - math.pi
    rr = 0.25 * min(np.linalg.norm(u), np.linalg.norm(v), 0.4 * span)
    t_th = ax.text(1.55 * rr * math.cos(av_ + dlt / 2), 1.55 * rr * math.sin(av_ + dlt / 2), "",
                   fontsize=10.5, ha="center", va="center", color=INK, zorder=8)
    sm = 0.045 * span
    nrm_v = u - Fp
    nn = np.linalg.norm(nrm_v)
    sg = 1.0 if np.dot(Fp, e) > 0 else -1.0
    if nn > 1e-9:
        nv = nrm_v / nn
        mk = np.array([Fp + sm * nv, Fp + sm * nv - sg * sm * e, Fp - sg * sm * e])
    else:
        mk = np.zeros((0, 2))
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=11, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    tx.set_title("Hesaplar" if tr else "Calculations", fontsize=12, loc="left")
    items = _panel(tx, [(0, f"u = {F['U']}", BLUE), (8, f"v = {F['V']}", ORANGE),
                        (22, f"u·v = {F['expr']} = {F['dot']}", INK),
                        (32, f"|u| = {F['mu']}", BLUE), (36, f"|v| = {F['mv']}", ORANGE),
                        (44, f"cos θ = {F['cos']}", INK), (48, f"θ ≈ {F['ang']}", INK),
                        (82, "proj_v(u) = (u·v/|v|²)·v", GREEN),
                        (88, f"= {F['kq']} = {F['PR']}", GREEN),
                        (106, f"u − proj = {F['PE']} ⊥ v", PURPLE)], fs=10.5, width=27, dy=0.07)
    N = 140

    def update(i):
        pu = _ease(_ph(i, 0, 14))
        pv = _ease(_ph(i, 8, 22))
        _set_arrow(a_u, (0, 0), pu * u)
        _set_arrow(a_v, (0, 0), pv * v)
        t_u.set_alpha(1.0 if pu >= 1 else 0.0)
        t_v.set_alpha(1.0 if pv >= 1 else 0.0)
        pa = _ease(_ph(i, 24, 42))
        if pa > 0:
            tt = np.linspace(av_, av_ + dlt * pa, 40)
            arc.set_data(rr * np.cos(tt), rr * np.sin(tt))
        else:
            arc.set_data([], [])
        t_th.set_text("θ" if i >= 42 else "")
        spanl.set_alpha(0.8 * _ph(i, 46, 54))
        pd = _ease(_ph(i, 56, 80))
        if i >= 56:
            cur = u + (Fp - u) * pd
            drop.set_data([u[0], cur[0]], [u[1], cur[1]])
            drop.set_alpha(1.0 - _ph(i, 104, 112))
            mover.set_data([cur[0]], [cur[1]]) if i < 104 else mover.set_data([], [])
        else:
            drop.set_data([], [])
            mover.set_data([], [])
        if i >= 80 and len(mk):
            rmark.set_data(mk[:, 0], mk[:, 1])
        else:
            rmark.set_data([], [])
        pp = _ease(_ph(i, 82, 102))
        _set_arrow(a_pr, (0, 0), pp * Fp)
        t_pr.set_alpha(1.0 if pp >= 1 else 0.0)
        _set_arrow(a_pe, Fp, u, alpha=_ph(i, 104, 116))
        if i < 24:
            info.set_text("1) u ve v vektörleri" if tr else "1) The vectors u and v")
        elif i < 46:
            info.set_text(("2) Açı: cos θ = u·v / (|u||v|)" if tr else "2) Angle: cos θ = u·v / (|u||v|)") +
                          (f"  ⇒  θ ≈ {sol['fmt']['ang']}" if i >= 42 else ""))
        elif i < 82:
            info.set_text("3) u'nun ucundan v doğrultusuna dik in" if tr else
                          "3) Drop a perpendicular from u's tip onto v's line")
        elif i < 104:
            info.set_text("4) İzdüşüm: proj_v(u) = (u·v/|v|²)·v" if tr else
                          "4) Projection: proj_v(u) = (u·v/|v|²)·v")
        elif i < 120:
            info.set_text("5) u = proj_v(u) + (v'ye dik bileşen)" if tr else
                          "5) u = proj_v(u) + (part perpendicular to v)")
        else:
            a = sol["answer"].split(", proj")
            info.set_text(a[0] + "\nproj" + a[1])
        _panel_show(items, i)
        return []

    return N, update


def vary(P, rnd):
    d0 = P["u"][0] * P["v"][0] + P["u"][1] * P["v"][1]
    for _ in range(3000):
        u = [rnd.randint(-5, 6), rnd.randint(-5, 6)]
        v = [rnd.randint(-5, 6), rnd.randint(-5, 6)]
        if u == [0, 0] or v == [0, 0] or u[0] * v[1] - u[1] * v[0] == 0:
            continue
        d = u[0] * v[0] + u[1] * v[1]
        if d == 0 or (d0 > 0) != (d > 0):
            continue
        return {"u": u, "v": v}
    return {"u": [1, 3], "v": [3, 1]}
'''),
}
EXAMPLES += [
    {"id": "linalg-dot-1", "kind": "dot_projection",
     "title": ("İç çarpım ve izdüşüm", "Dot product and projection"),
     "q": ("u = {U} ve v = {V} için u·v'yi, aradaki açıyı ve u'nun v üzerine izdüşümünü bul.",
           "For u = {U} and v = {V}, find u·v, the angle between them and the projection of u onto v."),
     "P": {"u": [1, 3], "v": [3, 1]}},
    {"id": "linalg-dot-2", "kind": "dot_projection",
     "title": ("Geniş açı ve negatif iç çarpım", "Obtuse angle and a negative dot product"),
     "q": ("u = {U}, v = {V}. u·v negatif çıkarsa açı ve izdüşüm hakkında ne söylenir? "
           "θ'yı ve proj_v(u)'yu hesapla.",
           "u = {U}, v = {V}. What does a negative u·v say about the angle and the projection? "
           "Compute θ and proj_v(u)."),
     "P": {"u": [-2, 3], "v": [4, 1]}},
    {"id": "linalg-dot-3", "kind": "dot_projection",
     "topics": ["work", "force", "iş", "kuvvet", "word problem"],
     "title": ("Kuvvetin yaptığı iş", "Work done by a force"),
     "q": ("Bir kutuya F = {U} N kuvvet uygulanıyor ve kutu d = {V} m yer değiştiriyor. "
           "Yapılan iş W = F·d nedir? Kuvvetin hareket yönündeki bileşeni (izdüşümü) nedir?",
           "A force F = {U} N acts on a box that moves by d = {V} m. What is the work W = F·d? "
           "What is the component (projection) of the force along the motion?"),
     "P": {"u": [5, 5], "v": [8, 6]}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["linear_combination"] = {
    "course": "linalg",
    "title": ("Lineer kombinasyon ve germe (span)", "Linear combination and span"),
    "topics": ["cramer's rule", "cramers rule", "cramer kuralı", "linear combination", "linear combinations", "span", "spanning set", "basis",
               "linear independence", "linearly independent", "coordinates", "change of basis",
               "lineer kombinasyon", "doğrusal birleşim", "germe", "gerilen uzay", "taban",
               "lineer bağımsızlık", "doğrusal bağımsızlık", "koordinat"],
    "code": _code(_NUM, _ARROW, _PANEL, r'''
from matplotlib.collections import LineCollection


def _lc(P):
    v1 = [_q(x) for x in P["v1"]]
    v2 = [_q(x) for x in P["v2"]]
    t = [_q(x) for x in P["t"]]
    D = v1[0] * v2[1] - v2[0] * v1[1]
    return v1, v2, t, D


def solve(P):
    v1, v2, t, D = _lc(P)
    names = ["c₁", "c₂"]
    e1 = _side([v1[0], v2[0]], names) + " = " + _f(t[0])
    e2 = _side([v1[1], v2[1]], names) + " = " + _f(t[1])
    V1, V2, Tt = _vec(v1), _vec(v2), _vec(t)
    steps = [
        (f"c₁·{V1} + c₂·{V2} = {Tt}", f"c₁·{V1} + c₂·{V2} = {Tt}"),
        (f"Bileşen bileşen: {e1};  {e2}", f"Component-wise: {e1};  {e2}"),
        (f"D = det[v₁ v₂] = ({_f(v1[0])})({_f(v2[1])}) − ({_f(v2[0])})({_f(v1[1])}) = {_f(D)}",
         f"D = det[v₁ v₂] = ({_f(v1[0])})({_f(v2[1])}) − ({_f(v2[0])})({_f(v1[1])}) = {_f(D)}"),
    ]
    fmt = {"V1": V1, "V2": V2, "T": Tt, "e1": e1, "e2": e2}
    if D == 0:
        on = (v1[0] * t[1] - v1[1] * t[0] == 0) and (v2[0] * t[1] - v2[1] * t[0] == 0)
        if on:
            msg = ("D = 0: v₁ ∥ v₂ ve t aynı doğru üzerinde ⇒ sonsuz çözüm",
                   "D = 0: v₁ ∥ v₂ and t lies on their line ⇒ infinitely many solutions")
        else:
            msg = ("D = 0: v₁ ∥ v₂, span bir doğru ve t onun dışında ⇒ çözüm yok",
                   "D = 0: v₁ ∥ v₂, the span is a line and t is off it ⇒ no solution")
        steps.append(msg)
        return {"answer": msg, "steps": steps, "fmt": fmt}
    n1 = t[0] * v2[1] - v2[0] * t[1]
    n2 = v1[0] * t[1] - t[0] * v1[1]
    c1, c2 = n1 / D, n2 / D
    w1 = [c1 * x for x in v1]
    w2 = [c2 * x for x in v2]
    steps += [
        ("D ≠ 0 ⇒ v₁ ve v₂ doğrusal bağımsız; span{v₁, v₂} tüm düzlemdir ⇒ tek çözüm var",
         "D ≠ 0 ⇒ v₁ and v₂ are linearly independent; span{v₁, v₂} is the whole plane ⇒ a unique solution"),
        (f"Cramer: c₁ = (({_f(t[0])})({_f(v2[1])}) − ({_f(v2[0])})({_f(t[1])})) / D = {_f(n1)}/{_p(D)} = {_f(c1)}",
         f"Cramer: c₁ = (({_f(t[0])})({_f(v2[1])}) − ({_f(v2[0])})({_f(t[1])})) / D = {_f(n1)}/{_p(D)} = {_f(c1)}"),
        (f"c₂ = (({_f(v1[0])})({_f(t[1])}) − ({_f(t[0])})({_f(v1[1])})) / D = {_f(n2)}/{_p(D)} = {_f(c2)}",
         f"c₂ = (({_f(v1[0])})({_f(t[1])}) − ({_f(t[0])})({_f(v1[1])})) / D = {_f(n2)}/{_p(D)} = {_f(c2)}"),
        (f"Kontrol: {_p(c1)}·{V1} + {_p(c2)}·{V2} = {_vec(w1)} + {_vec(w2)} = {Tt} ✓",
         f"Check: {_p(c1)}·{V1} + {_p(c2)}·{V2} = {_vec(w1)} + {_vec(w2)} = {Tt} ✓"),
        (f"Yol: başlangıçtan v₁ yönünde {_f(c1)} kez, sonra v₂ yönünde {_f(c2)} kez git ⇒ t'ye varılır",
         f"Path: go {_f(c1)} times along v₁, then {_f(c2)} times along v₂ ⇒ you reach t"),
    ]
    fmt.update({"c1": _f(c1), "c2": _f(c2), "D": _f(D),
                "n1": f"c₁ = {_f(n1)}/{_p(D)} = {_f(c1)}", "n2": f"c₂ = {_f(n2)}/{_p(D)} = {_f(c2)}",
                "comb": f"{_cf(c1)}v₁ {'−' if c2 < 0 else '+'} {_cf(abs(c2))}v₂",
                "w1lab": _cf(c1) + "v₁", "w2lab": _cf(c2) + "v₂"})
    ans = f"c₁ = {_f(c1)}, c₂ = {_f(c2)}  ⇒  t = {fmt['comb']}"
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    sol = solve(P)
    F = sol["fmt"]
    v1 = np.array([float(x) for x in P["v1"]])
    v2 = np.array([float(x) for x in P["v2"]])
    t = np.array([float(x) for x in P["t"]])
    D = v1[0] * v2[1] - v2[0] * v1[1]
    ok = abs(D) > 1e-12
    if ok:
        c1 = (t[0] * v2[1] - v2[0] * t[1]) / D
        c2 = (v1[0] * t[1] - t[0] * v1[1]) / D
    else:
        c1 = c2 = 0.0
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], left=0.06, right=0.98, top=0.93,
                          bottom=0.07, wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    pts = np.array([[0.0, 0.0], v1, v2, t, c1 * v1])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    span = max(float((hi - lo).max()), 4.0)
    pad = 0.12 * span + 0.8
    ax.set_xlim(lo[0] - pad, hi[0] + pad)
    ax.set_ylim(lo[1] - pad, hi[1] + pad + 0.2 * span)
    ax.set_aspect("equal")
    ax.axhline(0, color=GRAY, lw=1)
    ax.axvline(0, color=GRAY, lw=1)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.15)
    xl, yl = ax.get_xlim(), ax.get_ylim()
    lc1 = lc2 = None
    if ok:
        Binv = np.linalg.inv(np.column_stack([v1, v2]))
        corners = np.array([[xl[0], yl[0]], [xl[0], yl[1]], [xl[1], yl[0]], [xl[1], yl[1]]]).T
        K = int(min(25, math.ceil(float(np.abs(Binv @ corners).max())) + 1))
        lc1 = LineCollection([np.array([k * v1 - K * v2, k * v1 + K * v2]) for k in range(-K, K + 1)],
                             colors=ORANGE, linewidths=0.9, alpha=0.0, zorder=1)
        lc2 = LineCollection([np.array([s * v2 - K * v1, s * v2 + K * v1]) for s in range(-K, K + 1)],
                             colors=BLUE, linewidths=0.9, alpha=0.0, zorder=1)
        ax.add_collection(lc1, autolim=False)
        ax.add_collection(lc2, autolim=False)
    a1 = _arrow(ax, BLUE, z=5)
    a2 = _arrow(ax, ORANGE, z=5)
    p1 = _arrow(ax, BLUE, lw=4.5, z=4)
    p2 = _arrow(ax, ORANGE, lw=4.5, z=4)
    at = _arrow(ax, RED, lw=2.6, z=6)
    tdot, = ax.plot([], [], "o", color=RED, ms=10, zorder=7)
    mover, = ax.plot([], [], "o", color=INK, ms=7, zorder=8)
    off = 0.06 * span
    kw = dict(fontsize=12.5, fontweight="bold", ha="center", va="center", zorder=8)
    t1 = ax.text(*_side_label(v1, v2, off), "v₁", color=BLUE, **kw)
    t2 = ax.text(*_side_label(v2, v1, off), "v₂", color=ORANGE, **kw)
    nt = math.hypot(t[0], t[1])
    tpos = t + (t / nt * 1.2 * off if nt > 1e-9 else np.array([off, off]))
    tt_ = ax.text(tpos[0], tpos[1], "t", color=RED, **kw)
    w1 = c1 * v1
    lp1 = _side_label(w1, v2, 1.3 * off, 0.5) if ok else np.zeros(2)
    lp2 = w1 + _side_label(c2 * v2, -w1, 1.3 * off, 0.5) if ok else np.zeros(2)
    tp1 = ax.text(lp1[0], lp1[1], F.get("w1lab", ""),
                  color=BLUE, fontsize=11, fontweight="bold", ha="center", va="center", zorder=8,
                  bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    tp2 = ax.text(lp2[0], lp2[1], F.get("w2lab", ""), color=ORANGE, fontsize=11,
                  fontweight="bold", ha="center", va="center", zorder=8,
                  bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=11, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    tx.set_title("Hesaplar" if tr else "Calculations", fontsize=12, loc="left")
    ent = [(0, f"v₁ = {F['V1']}", BLUE), (6, f"v₂ = {F['V2']}", ORANGE), (18, f"t = {F['T']}", RED),
           (44, "c₁v₁ + c₂v₂ = t", INK), (48, F["e1"], INK), (51, F["e2"], INK),
           (54, f"D = {F['D'] if ok else '0'}", INK)]
    if ok:
        ent += [(62, F["n1"], BLUE), (90, F["n2"], ORANGE), (120, f"t = {F['comb']} ✓", GREEN)]
    else:
        ent += [(62, sol["answer"][0] if tr else sol["answer"][1], RED)]
    items = _panel(tx, ent, fs=11, width=26)
    N = 150

    def update(i):
        g1 = _ease(_ph(i, 0, 14))
        g2 = _ease(_ph(i, 6, 20))
        _set_arrow(a1, (0, 0), g1 * v1)
        _set_arrow(a2, (0, 0), g2 * v2)
        t1.set_alpha(1.0 if g1 >= 1 else 0.0)
        t2.set_alpha(1.0 if g2 >= 1 else 0.0)
        if i >= 18:
            tdot.set_data([t[0]], [t[1]])
            tt_.set_alpha(1.0)
        else:
            tdot.set_data([], [])
            tt_.set_alpha(0.0)
        if ok:
            ga = 0.4 * _ph(i, 22, 42)
            lc1.set_alpha(ga)
            lc2.set_alpha(ga)
            q1 = _ease(_ph(i, 58, 86))
            q2 = _ease(_ph(i, 88, 116))
            _set_arrow(p1, (0, 0), q1 * w1, alpha=0.6)
            _set_arrow(p2, w1, w1 + q2 * c2 * v2, alpha=0.6)
            tp1.set_alpha(1.0 if q1 >= 1 else 0.0)
            tp1.get_bbox_patch().set_alpha(0.8 if q1 >= 1 else 0.0)
            tp2.set_alpha(1.0 if q2 >= 1 else 0.0)
            tp2.get_bbox_patch().set_alpha(0.8 if q2 >= 1 else 0.0)
            if 58 <= i < 118:
                cur = q1 * w1 + q2 * c2 * v2
                mover.set_data([cur[0]], [cur[1]])
            else:
                mover.set_data([], [])
            _set_arrow(at, (0, 0), _ease(_ph(i, 118, 130)) * t)
        if i < 22:
            info.set_text("1) v₁, v₂ ve hedef vektör t" if tr else "1) v₁, v₂ and the target vector t")
        elif i < 58 or not ok:
            info.set_text(("2) span{v₁, v₂}: eğik ızgara = tüm kombinasyonlar" if tr else
                           "2) span{v₁, v₂}: the skewed grid = all combinations") if ok else
                          (sol["answer"][0] if tr else sol["answer"][1]))
        elif i < 88:
            info.set_text(f"3) v₁ yönünde c₁ = {F['c1']} kez" if tr else f"3) c₁ = {F['c1']} times along v₁")
        elif i < 118:
            info.set_text(f"4) v₂ yönünde c₂ = {F['c2']} kez" if tr else f"4) c₂ = {F['c2']} times along v₂")
        else:
            info.set_text(f"t = {F['comb']}  (c₁ = {F['c1']}, c₂ = {F['c2']})")
        _panel_show(items, i)
        return []

    return N, update


def vary(P, rnd):
    pos = all(x >= 0 for x in list(P["v1"]) + list(P["v2"]) + list(P["t"]))
    for _ in range(3000):
        if pos:
            v1 = [rnd.randint(1, 4), rnd.randint(0, 4)]
            v2 = [rnd.randint(0, 3), rnd.randint(1, 5)]
            c1, c2 = rnd.randint(1, 3), rnd.randint(1, 3)
        else:
            v1 = [rnd.randint(-3, 3), rnd.randint(-3, 3)]
            v2 = [rnd.randint(-3, 3), rnd.randint(-3, 3)]
            c1, c2 = rnd.choice([-3, -2, -1, 1, 2, 3]), rnd.choice([-3, -2, -1, 1, 2, 3])
        if v1[0] * v2[1] - v2[0] * v1[1] == 0:
            continue
        t = [c1 * v1[0] + c2 * v2[0], c1 * v1[1] + c2 * v2[1]]
        if max(abs(x) for x in t) > 12 or t == [0, 0]:
            continue
        return {"v1": v1, "v2": v2, "t": t}
    return {"v1": [1, 2], "v2": [3, 1], "t": [5, 5]}
'''),
}
EXAMPLES += [
    {"id": "linalg-comb-1", "kind": "linear_combination",
     "title": ("Vektörü lineer kombinasyon olarak yazma", "Writing a vector as a linear combination"),
     "q": ("t = {T} vektörünü v₁ = {V1} ve v₂ = {V2} vektörlerinin lineer kombinasyonu olarak yaz: "
           "c₁v₁ + c₂v₂ = t.",
           "Write t = {T} as a linear combination of v₁ = {V1} and v₂ = {V2}: c₁v₁ + c₂v₂ = t."),
     "P": {"v1": [1, 2], "v2": [3, 1], "t": [5, 5]}},
    {"id": "linalg-comb-2", "kind": "linear_combination",
     "title": ("Negatif katsayılı kombinasyon", "A combination with a negative coefficient"),
     "q": ("t = {T}, v₁ = {V1} ve v₂ = {V2} vektörlerinin gerdiği uzayda mı? Öyleyse c₁ ve c₂'yi bul.",
           "Is t = {T} in the span of v₁ = {V1} and v₂ = {V2}? If so, find c₁ and c₂."),
     "P": {"v1": [2, 1], "v2": [-1, 2], "t": [7, -4]}},
    {"id": "linalg-comb-3", "kind": "linear_combination",
     "topics": ["word problem", "mixture", "karışım", "sözel problem"],
     "title": ("Sözel problem: besin karışımı", "Word problem: mixing foods"),
     "q": ("Bir porsiyon A yemeği (protein, karbonhidrat) = {V1}, bir porsiyon B yemeği {V2} birim "
           "veriyor. Tam olarak {T} birim almak için kaçar porsiyon gerekir?",
           "One serving of food A gives (protein, carbs) = {V1} units and one serving of food B gives "
           "{V2}. How many servings of each give exactly {T}?"),
     "P": {"v1": [2, 3], "v2": [1, 4], "t": [7, 18]}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["matrix_multiply"] = {
    "course": "linalg",
    "title": ("Matris çarpımı: satır × sütun", "Matrix multiplication: row × column"),
    "topics": ["matrix multiplication", "multiplying matrices", "matrix product",
               "product of matrices", "matrix operations", "matrices", "composition of transformations",
               "matris çarpımı", "matrislerin çarpımı", "matris işlemleri", "matrisler",
               "dönüşümlerin bileşkesi"],
    "code": _code(_NUM, _MATRIX, r'''
from matplotlib.patches import Rectangle


def _ms(m):
    return "[" + ", ".join("[" + ", ".join(_f(x) for x in r) + "]" for r in m) + "]"


def _mm(X, Y):
    return [[sum(X[i][k] * Y[k][j] for k in range(len(Y))) for j in range(len(Y[0]))]
            for i in range(len(X))]


def _cij(i, j):
    return "c" + SUB[i + 1] + SUB[j + 1]


def solve(P):
    A = [[_q(x) for x in r] for r in P["A"]]
    B = [[_q(x) for x in r] for r in P["B"]]
    m, n, n2, p = len(A), len(A[0]), len(B), len(B[0])
    fmt = {"Am": _ms(A), "Bm": _ms(B), "dims": f"({m}×{n})·({n2}×{p})"}
    if n != n2:
        msg = (f"Tanımsız: A {m}×{n}, B {n2}×{p}; iç boyutlar ({n} ≠ {n2}) eşit değil",
               f"Undefined: A is {m}×{n}, B is {n2}×{p}; inner sizes differ ({n} ≠ {n2})")
        return {"answer": msg, "steps": [msg, ("AB için A'nın sütun sayısı = B'nin satır sayısı olmalı",
                                               "AB needs (columns of A) = (rows of B)")], "fmt": fmt}
    C = _mm(A, B)
    steps = [
        (f"Boyutlar: A {m}×{n}, B {n}×{p} ⇒ AB {m}×{p} (iç boyutlar eşit: {n} = {n})",
         f"Sizes: A is {m}×{n}, B is {n}×{p} ⇒ AB is {m}×{p} (inner sizes match: {n} = {n})"),
        ("c_ij = (A'nın i. satırı)·(B'nin j. sütunu) = Σ a_ik·b_kj",
         "c_ij = (row i of A)·(column j of B) = Σ a_ik·b_kj"),
    ]
    for i in range(m):
        for j in range(p):
            s = f"{_cij(i, j)} = " + " + ".join(f"({_f(A[i][k])})({_f(B[k][j])})" for k in range(n)) + \
                f" = {_f(C[i][j])}"
            steps.append((s, s))
    steps.append((f"AB = {_ms(C)}", f"AB = {_ms(C)}"))
    steps.append(("Dönüşüm olarak: (AB)x = A(Bx) — AB önce B'yi, sonra A'yı uygular (bileşke).",
                  "As transformations: (AB)x = A(Bx) — AB applies B first, then A (composition)."))
    if m == n == p:
        BA = _mm(B, A)
        if BA != C:
            steps.append((f"BA = {_ms(BA)} ≠ AB: matris çarpımı değişmeli değildir (sıra önemli).",
                          f"BA = {_ms(BA)} ≠ AB: matrix multiplication is not commutative (order matters)."))
        else:
            steps.append((f"BA = {_ms(BA)} = AB (bu iki matris için sıra fark etmiyor).",
                          f"BA = {_ms(BA)} = AB (for these two matrices the order happens not to matter)."))
    fmt["Cm"] = _ms(C)
    return {"answer": f"AB = {_ms(C)}", "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    sol = solve(P)
    A = [[_q(x) for x in r] for r in P["A"]]
    B = [[_q(x) for x in r] for r in P["B"]]
    m, n, n2, p = len(A), len(A[0]), len(B), len(B[0])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10.8)
    info = ax.text(0.015, 0.975, "", transform=ax.transAxes, va="top", fontsize=11.5, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    if n != n2:
        ax.text(8, 5.4, sol["answer"][0] if tr else sol["answer"][1], ha="center", va="center",
                fontsize=14, color=RED)

        def upd0(i):
            info.set_text(f"A {m}×{n} · B {n2}×{p}")
            return []
        return 60, upd0
    C = _mm(A, B)
    sA = [[_f(x) for x in r] for r in A]
    sB = [[_f(x) for x in r] for r in B]
    sC = [[_f(x) for x in r] for r in C]
    wmax = max(len(s) for s in [x for r in sB for x in r] + [x for r in sC for x in r])
    wA = max(len(x) for r in sA for x in r)
    cwA = max(1.15, 0.34 * wA + 0.6)
    cwC = max(1.4, 0.34 * wmax + 0.7)
    ch = 1.05
    total = n * cwA + 1.8 + p * cwC
    xs = (16 - total) / 2
    xA = xs + 0.5 * cwA
    xC = xs + n * cwA + 1.8 + 0.5 * cwC
    yC = 4.75 - (3 - m) * 0.3
    yB = yC + 1.1 + n * ch
    TA, bA, _ = _mat(ax, xA, yC, sA, cwA, ch, fs=17)
    TB, bB, _ = _mat(ax, xC, yB, sB, cwC, ch, fs=17)
    TC, bC, _ = _mat(ax, xC, yC, [["?"] * p for _ in range(m)], cwC, ch, fs=17)
    ax.text(bA[0] - 0.25, (bA[2] + bA[3]) / 2, "A", ha="right", va="center", fontsize=16,
            fontweight="bold", color=BLUE)
    ax.text(bB[0] - 0.25, (bB[2] + bB[3]) / 2, "B", ha="right", va="center", fontsize=16,
            fontweight="bold", color=ORANGE)
    ax.text(bC[1] + 0.25, (bC[2] + bC[3]) / 2, "AB", ha="left", va="center", fontsize=16,
            fontweight="bold", color=GREEN)
    bandA = Rectangle((bA[0], 0), 1, 0.9 * ch, fc=BLUE, ec="none", alpha=0.09, zorder=1)
    rowA = Rectangle((bA[0], 0), bA[1] - bA[0], 0.9 * ch, fc=BLUE, ec="none", alpha=0.2, zorder=1)
    bandB = Rectangle((0, 0), cwC, 1, fc=ORANGE, ec="none", alpha=0.09, zorder=1)
    colB = Rectangle((0, bB[3]), cwC, bB[2] - bB[3], fc=ORANGE, ec="none", alpha=0.24, zorder=1)
    cell = Rectangle((0, 0), cwC, 0.9 * ch, fc=GREEN, ec=GREEN, alpha=0.3, lw=1.5, zorder=1)
    for rp in (bandA, rowA, bandB, colB, cell):
        ax.add_patch(rp)
        rp.set_visible(False)
    comp = ax.text(8, 1.15, "", ha="center", va="center", fontsize=15.5, color=INK)
    ba_t = ax.text(8, 0.45, "", ha="center", va="center", fontsize=12.5, color=PURPLE)
    if m == n == p:
        BA = _mm(B, A)
        ba_s = (f"BA = {_ms(BA)} " + ("≠" if BA != C else "=") + " AB" +
                ((" — sıra önemli!" if tr else " — order matters!") if BA != C else ""))
    else:
        ba_s = ""
    cs_ = _ms(C)
    ents = [(i, j) for i in range(m) for j in range(p)]
    T0 = 12
    Dd = max(12, min(22, 120 // len(ents)))
    T_end = T0 + len(ents) * Dd
    N = T_end + 26
    fill_at = int(0.72 * Dd)
    term_dur = 0.68 * Dd / n
    remark = ("Bileşke: x ↦ Bx ↦ A(Bx) = (AB)x" if tr else "Composition: x ↦ Bx ↦ A(Bx) = (AB)x")

    def update(i):
        if i < T0:
            e, f = -1, 0
        elif i < T_end:
            e, f = (i - T0) // Dd, (i - T0) % Dd
        else:
            e, f = len(ents), 0
        filled = len(ents) if e >= len(ents) else max(0, e) + (1 if (e >= 0 and f >= fill_at) else 0)
        done = e >= len(ents)
        ba_t.set_text(ba_s if (done and i >= T_end + 8) else "")
        for idx, (r, c) in enumerate(ents):
            if idx < filled:
                TC[r][c].set_text(sC[r][c])
                TC[r][c].set_color(GREEN if (idx == e or done) else INK)
                TC[r][c].set_fontweight("bold" if (idx == e or done) else "normal")
            else:
                TC[r][c].set_text("?")
                TC[r][c].set_color(LIGHT)
                TC[r][c].set_fontweight("normal")
        for row in TA + TB:
            for t in row:
                t.set_color(INK)
                t.set_fontweight("normal")
        if 0 <= e < len(ents):
            r, c = ents[e]
            yr = yC - r * ch - 0.45 * ch
            xc = xC + c * cwC - 0.5 * cwC
            bandA.set_bounds(bA[0], yr, xc + cwC - bA[0], 0.9 * ch)
            rowA.set_y(yr)
            bandB.set_bounds(xc, yr, cwC, bB[2] - yr)
            colB.set_x(xc)
            cell.set_xy((xc, yr))
            for rp in (bandA, rowA, bandB, colB, cell):
                rp.set_visible(True)
            ka = min(n - 1, int(f / term_dur))
            terms = [f"({sA[r][k]})({sB[k][c]})" for k in range(n)]
            if f < fill_at:
                TA[r][ka].set_color(RED)
                TA[r][ka].set_fontweight("bold")
                TB[ka][c].set_color(RED)
                TB[ka][c].set_fontweight("bold")
                comp.set_text(f"{_cij(r, c)} = " + " + ".join(terms[:ka + 1]) + (" + …" if ka < n - 1 else ""))
            else:
                comp.set_text(f"{_cij(r, c)} = " + " + ".join(terms) + f" = {sC[r][c]}")
            info.set_text((f"2) {_cij(r, c)} = (A'nın {r + 1}. satırı)·(B'nin {c + 1}. sütunu)" if tr else
                           f"2) {_cij(r, c)} = (row {r + 1} of A)·(column {c + 1} of B)"))
        else:
            for rp in (bandA, rowA, bandB, colB, cell):
                rp.set_visible(False)
            if e < 0:
                comp.set_text(f"({m}×{n})·({n}×{p}) → {m}×{p}")
                info.set_text(f"1) Boyutlar: iç boyutlar eşit ({n} = {n}) ⇒ AB {m}×{p}" if tr else
                              f"1) Sizes: inner sizes match ({n} = {n}) ⇒ AB is {m}×{p}")
            else:
                comp.set_text(remark)
                info.set_text(f"3) AB = {cs_} ✓   Dönüşüm olarak önce B, sonra A uygulanır" if tr else
                              f"3) AB = {cs_} ✓   As a map it applies B first, then A")
        return []

    return N, update


def vary(P, rnd):
    A0, B0 = P["A"], P["B"]
    nonneg = all(x >= 0 for r in A0 + B0 for x in r)
    lo, hi = (0, 9) if nonneg else (-3, 5)
    A = [[rnd.randint(lo, hi) for _ in r] for r in A0]
    B = [[rnd.randint(lo, hi) for _ in r] for r in B0]
    return {"A": A, "B": B}
'''),
}
EXAMPLES += [
    {"id": "linalg-mult-1", "kind": "matrix_multiply",
     "title": ("2×2 matrislerin çarpımı", "Multiplying 2×2 matrices"),
     "q": ("A = {Am} ve B = {Bm} için AB'yi satır × sütun kuralıyla hesapla. BA ile aynı mı?",
           "For A = {Am} and B = {Bm}, compute AB with the row × column rule. Is it the same as BA?"),
     "P": {"A": [[1, 2], [3, 4]], "B": [[2, 0], [1, 3]]}},
    {"id": "linalg-mult-2", "kind": "matrix_multiply",
     "title": ("2×3 ile 3×2 çarpımı", "A 2×3 times a 3×2 matrix"),
     "q": ("A = {Am} (2×3) ve B = {Bm} (3×2). AB tanımlı mı, boyutu nedir? AB'yi hesapla.",
           "A = {Am} (2×3) and B = {Bm} (3×2). Is AB defined and what is its size? Compute AB."),
     "P": {"A": [[1, 0, 2], [-1, 3, 1]], "B": [[3, 1], [2, 1], [1, 0]]}},
    {"id": "linalg-mult-3", "kind": "matrix_multiply",
     "topics": ["word problem", "sözel problem", "revenue", "gelir"],
     "title": ("Sözel problem: satış ve gelir tablosu", "Word problem: sales and revenue table"),
     "q": ("Bir dükkânın iki günde üç üründen sattığı adetler A = {Am} (satır: gün, sütun: ürün). "
           "B = {Bm} her ürünün satış fiyatını (1. sütun) ve maliyetini (2. sütun) veriyor. "
           "AB'yi hesapla: her günün toplam geliri ve maliyeti nedir?",
           "A shop's unit sales of three products on two days are A = {Am} (rows: days, columns: "
           "products). B = {Bm} lists each product's price (column 1) and cost (column 2). Compute AB: "
           "what are each day's total revenue and cost?"),
     "P": {"A": [[4, 2, 5], [3, 6, 1]], "B": [[10, 6], [15, 9], [8, 5]]}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["determinant_3x3"] = {
    "course": "linalg",
    "title": ("3×3 determinant ve paralelyüz hacmi", "3×3 determinant and parallelepiped volume"),
    "topics": ["determinant", "determinants", "3x3 determinant", "cofactor", "cofactor expansion",
               "laplace expansion", "minor", "minors", "sarrus", "triple product",
               "volume of a parallelepiped", "parallelepiped", "kofaktör", "eş çarpan",
               "minör", "laplace açılımı", "paralelyüz", "paralelyüz hacmi", "karma çarpım"],
    "code": _code(_NUM, _MATRIX, r'''
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def _cof(M):
    minors, parts = [], []
    for j in range(3):
        cs = [c for c in range(3) if c != j]
        e, f_ = M[1][cs[0]], M[1][cs[1]]
        g, h = M[2][cs[0]], M[2][cs[1]]
        minors.append(e * h - f_ * g)
        parts.append((e, f_, g, h))
    det = M[0][0] * minors[0] - M[0][1] * minors[1] + M[0][2] * minors[2]
    return det, minors, parts


def _expansion(M, minors, det):
    terms = []
    for j in range(3):
        s = f"{_p(M[0][j])}·{_p(minors[j])}"
        terms.append(s if j == 0 else ((" − " if j == 1 else " + ") + s))
    prods = [(-1 if j == 1 else 1) * M[0][j] * minors[j] for j in range(3)]
    sm = "= " + _f(prods[0]) + "".join((" − " + _f(-x)) if x < 0 else (" + " + _f(x)) for x in prods[1:])
    return terms, sm + f" = {_f(det)}"


def solve(P):
    M = [[_q(x) for x in r] for r in P["M"]]
    det, minors, parts = _cof(M)
    Ms = "[" + ", ".join("[" + ", ".join(_f(x) for x in r) + "]" for r in M) + "]"
    steps = [(f"M = {Ms}", f"M = {Ms}"),
             ("1. satıra göre kofaktör açılımı (işaretler + − +): det M = a₁₁·M₁₁ − a₁₂·M₁₂ + a₁₃·M₁₃",
              "Cofactor expansion along row 1 (signs + − +): det M = a₁₁·M₁₁ − a₁₂·M₁₂ + a₁₃·M₁₃")]
    for j in range(3):
        e, f_, g, h = parts[j]
        s = (f"M₁{SUB[j + 1]} = |{_f(e)} {_f(f_)}; {_f(g)} {_f(h)}| = ({_f(e)})({_f(h)}) − "
             f"({_f(f_)})({_f(g)}) = {_f(minors[j])}")
        steps.append((s + f"   (1. satır ve {j + 1}. sütun silindi)", s + f"   (row 1 and column {j + 1} deleted)"))
    terms, sm = _expansion(M, minors, det)
    steps.append((f"det M = {''.join(terms)} {sm}", f"det M = {''.join(terms)} {sm}"))
    (a, b, c), (d, e, f_), (g, h, k) = M
    pos = [a * e * k, b * f_ * g, c * d * h]
    neg = [c * e * g, a * f_ * h, b * d * k]
    sar = (f"({' + '.join(_p(x) for x in pos)}) − ({' + '.join(_p(x) for x in neg)}) = "
           f"{_f(sum(pos))} − {_p(sum(neg))} = {_f(sum(pos) - sum(neg))}")
    steps.append((f"Sarrus kontrolü: {sar} ✓", f"Sarrus check: {sar} ✓"))
    if det > 0:
        o = ("det > 0: r₁, r₂, r₃ sağ el sistemi (pozitif yönelim)", "det > 0: r₁, r₂, r₃ are right-handed")
    elif det < 0:
        o = ("det < 0: r₁, r₂, r₃ sol el sistemi (yönelim ters)", "det < 0: r₁, r₂, r₃ are left-handed (orientation reversed)")
    else:
        o = ("det = 0: satırlar aynı düzlemde; hacim 0, M tersinir değil",
             "det = 0: the rows are coplanar; volume 0, M is not invertible")
    steps.append((f"Satır vektörlerinin gerdiği paralelyüzün hacmi = |det M| = {_f(abs(det))}; " + o[0],
                  f"Volume of the parallelepiped spanned by the rows = |det M| = {_f(abs(det))}; " + o[1]))
    fmt = {"Mm": Ms, "r1": _vec(M[0]), "r2": _vec(M[1]), "r3": _vec(M[2])}
    return {"answer": (f"det M = {_f(det)}, hacim = {_f(abs(det))}",
                       f"det M = {_f(det)}, volume = {_f(abs(det))}"), "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    M = [[_q(x) for x in r] for r in P["M"]]
    det, minors, parts = _cof(M)
    terms, sm = _expansion(M, minors, det)
    Mf = np.array([[float(x) for x in r] for r in M])
    gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 1], left=0.01, right=0.99, top=0.93,
                          bottom=0.03, wspace=0.02)
    ax = fig.add_subplot(gs[0, 0])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    a3 = fig.add_subplot(gs[0, 1], projection="3d")
    cw, ch = 0.14, 0.1
    x0, y0 = 0.42, 0.7
    T, box, _ = _mat(ax, x0, y0, [[_f(x) for x in r] for r in M], cw, ch, fs=16)
    left, right, top, bot = box
    ax.text(left - 0.03, y0 - ch, "M =", ha="right", va="center", fontsize=15)
    signs = ["+", "−", "+"]
    sg_t = [ax.text(x0 + j * cw, top + 0.012, signs[j], ha="center", va="bottom", fontsize=13,
                    color=PURPLE, fontweight="bold", alpha=0.0) for j in range(3)]
    hl = Rectangle((0, 0), 0.9 * cw, 0.9 * ch, fc="none", ec=ORANGE, lw=2.2, zorder=6)
    ax.add_patch(hl)
    hl.set_visible(False)
    srow, = ax.plot([left + 0.02, right - 0.02], [y0, y0], color=RED, lw=1.3, alpha=0.0)
    scol, = ax.plot([x0, x0], [top - 0.01, bot + 0.01], color=RED, lw=1.3, alpha=0.0)
    mlab = ax.text(0.03, 0.325, "", ha="left", va="center", fontsize=13, color=ORANGE, fontweight="bold")
    mx0, my0, mcw, mch = 0.27, 0.37, 0.1, 0.09
    MT, mbox, mlines = _mat(ax, mx0, my0, [["", ""], ["", ""]], mcw, mch, fs=13, kind="||")
    for ln in mlines:
        ln.set_alpha(0.0)
    mc1 = ax.text(mbox[1] + 0.03, my0, "", ha="left", va="center", fontsize=11.5, color=INK)
    mc2 = ax.text(mbox[1] + 0.03, my0 - mch, "", ha="left", va="center", fontsize=12,
                  color=ORANGE, fontweight="bold")
    exp1 = ax.text(0.03, 0.15, "", ha="left", va="center", fontsize=12.5, color=INK)
    exp2 = ax.text(0.03, 0.065, "", ha="left", va="center", fontsize=12.5, color=INK)
    info = ax.text(0.02, 0.985, "", transform=ax.transAxes, va="top", fontsize=10.5, zorder=9,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    ra, rb, rc = Mf[0], Mf[1], Mf[2]
    O = np.zeros(3)
    V = np.array([O, ra, rb, rc, ra + rb, ra + rc, rb + rc, ra + rb + rc])
    faces = [[O, ra, ra + rb, rb], [O, rb, rb + rc, rc], [O, ra, ra + rc, rc],
             [rc, ra + rc, ra + rb + rc, rb + rc], [ra, ra + rb, ra + rb + rc, ra + rc],
             [rb, ra + rb, ra + rb + rc, rb + rc]]
    rgb = (0.145, 0.388, 0.922) if det >= 0 else (0.863, 0.149, 0.149)
    poly = Poly3DCollection(faces, facecolors=[rgb + (0.0,)], edgecolors=[rgb + (0.0,)], linewidths=1.0)
    a3.add_collection3d(poly)
    lo = np.minimum(V.min(axis=0), 0) - 0.4
    hi = np.maximum(V.max(axis=0), 0) + 0.4
    half = max(float((hi - lo).max()), 2.0) / 2
    cen = (lo + hi) / 2
    a3.set_xlim(cen[0] - half, cen[0] + half)
    a3.set_ylim(cen[1] - half, cen[1] + half)
    a3.set_zlim(cen[2] - half, cen[2] + half)
    a3.set_box_aspect((1, 1, 1))
    for axis_ in (a3.xaxis, a3.yaxis, a3.zaxis):
        axis_.set_major_locator(MaxNLocator(5, integer=True))
    a3.tick_params(labelsize=7, pad=0)
    a3.set_xlabel("x", fontsize=9)
    a3.set_ylabel("y", fontsize=9)
    a3.set_zlabel("z", fontsize=9)
    cols3 = [BLUE, ORANGE, GREEN]
    lines3, tips3, labs3 = [], [], []
    for k in range(3):
        ln, = a3.plot([0, 0], [0, 0], [0, 0], color=cols3[k], lw=3)
        tp, = a3.plot([0], [0], [0], "o", color=cols3[k], ms=6)
        lb = a3.text(Mf[k][0] * 1.1, Mf[k][1] * 1.1, Mf[k][2] * 1.1, "r" + SUB[k + 1], color=cols3[k],
                     fontsize=12, fontweight="bold", alpha=0.0)
        lines3.append(ln)
        tips3.append(tp)
        labs3.append(lb)
    T0, TD = 12, 26
    t_sum = T0 + 3 * TD + 2
    t_vol = t_sum + 10
    N = 165
    vol = _f(abs(det))
    if det > 0:
        orient = ("sağ el sistemi", "right-handed")
    elif det < 0:
        orient = ("sol el sistemi: yönelim ters", "left-handed: orientation reversed")
    else:
        orient = ("vektörler aynı düzlemde", "the vectors are coplanar")

    def update(i):
        a3.view_init(elev=20, azim=-60 + 0.75 * i)
        g = _ease(_ph(i, 0, 20))
        for k in range(3):
            pk = Mf[k] * g
            lines3[k].set_data_3d([0, pk[0]], [0, pk[1]], [0, pk[2]])
            tips3[k].set_data_3d([pk[0]], [pk[1]], [pk[2]])
            labs3[k].set_alpha(1.0 if g >= 1 else 0.0)
        pf = _ph(i, t_vol, t_vol + 16)
        poly.set_facecolor([rgb + (0.22 * pf,)])
        poly.set_edgecolor([rgb + (0.9 * pf,)])
        if i >= t_vol:
            a3.set_title((f"Hacim = |det M| = {vol}" if tr else f"Volume = |det M| = {vol}"),
                         fontsize=12, color=BLUE if det >= 0 else RED)
        else:
            a3.set_title("Satır vektörleri r₁, r₂, r₃" if tr else "Row vectors r₁, r₂, r₃",
                         fontsize=11, color=INK)
        for t in sg_t:
            t.set_alpha(_ph(i, 4, 10))
        j = (i - T0) // TD if T0 <= i < T0 + 3 * TD else -1
        f = (i - T0) % TD
        for r in range(3):
            for c in range(3):
                T[r][c].set_color(INK)
                T[r][c].set_fontweight("normal")
        if j >= 0:
            cs = [c for c in range(3) if c != j]
            for c in range(3):
                T[0][c].set_color(LIGHT)
            for r in range(3):
                T[r][j].set_color(LIGHT)
            for r in (1, 2):
                for c in cs:
                    T[r][c].set_color(BLUE)
            T[0][j].set_color(ORANGE)
            T[0][j].set_fontweight("bold")
            hl.set_xy((x0 + j * cw - 0.45 * cw, y0 - 0.45 * ch))
            hl.set_visible(True)
            srow.set_alpha(0.55)
            scol.set_data([x0 + j * cw, x0 + j * cw], [top - 0.01, bot + 0.01])
            scol.set_alpha(0.55)
            e, f_, gg, h = parts[j]
            if f >= 5:
                mlab.set_text(f"M₁{SUB[j + 1]} =")
                for q, val in enumerate((e, f_, gg, h)):
                    MT[q // 2][q % 2].set_text(_f(val))
                    MT[q // 2][q % 2].set_color(BLUE)
                for ln in mlines:
                    ln.set_alpha(1.0)
            else:
                mlab.set_text("")
                for q in range(4):
                    MT[q // 2][q % 2].set_text("")
                for ln in mlines:
                    ln.set_alpha(0.0)
            mc1.set_text(f"= ({_f(e)})({_f(h)}) − ({_f(f_)})({_f(gg)})" if f >= 10 else "")
            mc2.set_text(f"= {_f(minors[j])}" if f >= 15 else "")
            info.set_text((f"2) a₁{SUB[j + 1]} = {_f(M[0][j])}: 1. satırı ve {j + 1}. sütunu sil → minör M₁{SUB[j + 1]}"
                           if tr else
                           f"2) a₁{SUB[j + 1]} = {_f(M[0][j])}: delete row 1 and column {j + 1} → minor M₁{SUB[j + 1]}"))
        else:
            hl.set_visible(False)
            srow.set_alpha(0.0)
            scol.set_alpha(0.0)
            mlab.set_text("")
            for q in range(4):
                MT[q // 2][q % 2].set_text("")
            for ln in mlines:
                ln.set_alpha(0.0)
            mc1.set_text("")
            mc2.set_text("")
            if i < T0:
                info.set_text("1) 1. satıra göre kofaktör açılımı; işaretler + − +" if tr else
                              "1) Cofactor expansion along row 1; signs + − +")
            elif i < t_vol:
                info.set_text(f"det M = {_f(det)}")
            else:
                info.set_text((f"3) Hacim = |det M| = {vol}; {orient[0]}" if tr else
                               f"3) Volume = |det M| = {vol}; {orient[1]}"))
        nterms = sum(1 for q in range(3) if i >= T0 + q * TD + 18)
        exp1.set_text("det M = " + "".join(terms[:nterms]) if nterms else "")
        exp2.set_text(sm if i >= t_sum else "")
        exp2.set_color(BLUE if det >= 0 else RED)
        exp2.set_fontweight("bold" if i >= t_sum else "normal")
        return []

    return N, update


def vary(P, rnd):
    nonneg = all(x >= 0 for r in P["M"] for x in r)
    lo, hi = (0, 4) if nonneg else (-3, 4)
    for _ in range(3000):
        M = [[rnd.randint(lo, hi) for _ in range(3)] for _ in range(3)]
        Mq = [[_q(x) for x in r] for r in M]
        d = _cof(Mq)[0]
        if d == 0 or abs(d) > 40:
            continue
        return {"M": M}
    return {"M": [[2, 1, 3], [0, -1, 4], [1, 2, 0]]}
'''),
}
EXAMPLES += [
    {"id": "linalg-det-1", "kind": "determinant_3x3",
     "title": ("Kofaktör açılımıyla 3×3 determinant", "3×3 determinant by cofactor expansion"),
     "q": ("M = {Mm} matrisinin determinantını 1. satıra göre kofaktör açılımıyla hesapla.",
           "Compute the determinant of M = {Mm} by cofactor expansion along the first row."),
     "P": {"M": [[2, 1, 3], [0, -1, 4], [1, 2, 0]]}},
    {"id": "linalg-det-2", "kind": "determinant_3x3",
     "title": ("Minörler ve Sarrus kontrolü", "Minors and a Sarrus check"),
     "q": ("M = {Mm} için minörleri ve kofaktörleri bul, det M'yi hesapla ve Sarrus kuralıyla kontrol et.",
           "For M = {Mm} find the minors and cofactors, compute det M and check it with Sarrus' rule."),
     "P": {"M": [[3, 1, 0], [1, 2, 1], [0, 1, 2]]}},
    {"id": "linalg-det-3", "kind": "determinant_3x3",
     "topics": ["volume", "hacim", "word problem"],
     "title": ("Paralelyüzün hacmi", "Volume of a parallelepiped"),
     "q": ("Bir paralelyüzün bir köşeden çıkan kenar vektörleri a = {r1}, b = {r2}, c = {r3}. "
           "Hacmi, bu vektörleri satır olarak yazdığın matrisin determinantının mutlak değeridir. Hacmi bul.",
           "The edges of a parallelepiped from one corner are a = {r1}, b = {r2}, c = {r3}. Its volume is "
           "the absolute value of the determinant of the matrix with these rows. Find the volume."),
     "P": {"M": [[2, 0, 1], [1, 3, 0], [0, 1, 4]]}},
]
