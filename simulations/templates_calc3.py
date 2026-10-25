# -*- coding: utf-8 -*-
"""Kalkülüs 3 (çok değişkenli) simülasyonları: yüzeyler ve seviye eğrileri,
kısmi türevler, gradyan ve yönlü türev, çift katlı integral, vektör alanları,
uzay eğrileri ve yay uzunluğu, Lagrange çarpanları, teğet düzlem.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Ortak yardımcılar
(_CORE, _C3D) her kaynağın başına eklenir; böylece her kaynak tek başına
çalışır ve düzenleyicide tam olarak görünür. Sorular kurs kitaplarından
KOPYALANMAZ: kendi ifademizle yazılmış, sayıları seçilmiş tipik ders
örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
# Ortak yardımcılar: ifade çözümleme (PDF tarayıcısından gelen keyfi f için
# dayanıklı), güvenli sayısal değerlendirme (nan/inf/karmaşık -> nan),
# okunaklı ifade yazımı (x**2*y -> x²y) ve tam/yaklaşık değer biçimi.
# ──────────────────────────────────────────────────────────────────────────
_CORE = r'''
import numpy as np
import sympy as sp
from fractions import Fraction
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application, convert_xor)

_X, _Y, _T = sp.symbols("x y t", real=True)
_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷",
        "8": "⁸", "9": "⁹"}
BLUE, ORANGE, GREEN, RED, PURPLE, GRAY = ("#2563EB", "#E07B39", "#16A34A", "#DC2626",
                                          "#7C3AED", "#6B7280")
BOX = dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.94)


def _parse(s, names=(_X, _Y)):
    txt = str(s).strip()
    for a, b in (("−", "-"), ("–", "-"), ("·", "*"), ("×", "*"), ("²", "**2"),
                 ("³", "**3"), ("π", "pi"), ("^", "**")):
        txt = txt.replace(a, b)
    if "=" in txt:
        txt = txt.split("=")[-1]
    txt = txt.strip() or "0"
    loc = {"x": _X, "y": _Y, "t": _T, "e": sp.E, "pi": sp.pi}
    try:
        e = sp.sympify(txt, locals=loc)
    except Exception:
        tf = standard_transformations + (implicit_multiplication_application, convert_xor)
        e = parse_expr(txt, local_dict=loc, transformations=tf)
    e = sp.sympify(e)
    if not isinstance(e, sp.Expr):
        raise ValueError("ifade çözümlenemedi / could not parse: " + str(s))
    extra = [v for v in e.free_symbols if v not in names]
    if extra:
        e = e.subs({v: 1 for v in extra})
    return e


def _exact(v):
    try:
        fr = Fraction(str(v))
        return sp.Rational(fr.numerator, fr.denominator)
    except (ValueError, ZeroDivisionError, TypeError):
        return _parse(v, ())


def _fl(v):
    return float(sp.N(_exact(v)))


def _rng(P, k0, k1, d0, d1):
    try:
        a, b = _fl(P.get(k0, d0)), _fl(P.get(k1, d1))
    except Exception:
        a, b = d0, d1
    if not (np.isfinite(a) and np.isfinite(b)):
        a, b = d0, d1
    if a > b:
        a, b = b, a
    if b - a < 1e-6:
        a, b = a - 1.0, b + 1.0
    return float(a), float(b)


def _num(f, args):
    g = sp.lambdify(args, f, "numpy")

    def one(*a):
        try:
            return complex(g(*a))
        except Exception:
            return complex(np.nan)

    def h(*vals):
        vals = [np.asarray(v, dtype=float) for v in vals]
        shp = np.broadcast(*vals).shape
        try:
            with np.errstate(all="ignore"):
                out = np.asarray(g(*vals), dtype=complex)
        except Exception:
            with np.errstate(all="ignore"):
                out = np.asarray(np.vectorize(one, otypes=[complex])(*vals), dtype=complex)
        with np.errstate(all="ignore"):
            re = np.where(np.abs(out.imag) <= 1e-9 * (1.0 + np.abs(out.real)), out.real, np.nan)
            re = np.where(np.isfinite(re), re, np.nan)
        return np.array(np.broadcast_to(re, shp), dtype=float)
    return h


def _tok(s, a, b):
    out, i, n, k = "", 0, len(s), len(a)
    while i < n:
        if (s.startswith(a, i) and (i == 0 or not s[i - 1].isalpha())
                and (i + k >= n or not s[i + k].isalpha())):
            out += b
            i += k
        else:
            out += s[i]
            i += 1
    return out


def _pp(e):
    s = e if isinstance(e, str) else sp.sstr(e)
    out, i, n = "", 0, len(s)
    while i < n:
        if s.startswith("**", i):
            j = i + 2
            while j < n and s[j] in "0123456789":
                j += 1
            if j > i + 2 and (j >= n or s[j] != "."):
                out += "".join(_SUP[ch] for ch in s[i + 2:j])
            else:
                out += "^"
                j = i + 2
            i = j
            continue
        ch = s[i]
        if ch == "*":
            p, q = out[-1:], s[i + 1:i + 2]
            dig = p != "" and p in "0123456789"
            if (dig and (q in ("x", "y", "t", "(") or s.startswith("sqrt", i + 1)
                         or s.startswith("pi", i + 1))) or (
                    p != "" and p in "xyt⁰¹²³⁴⁵⁶⁷⁸⁹" and q != "" and q in "xyt"):
                i += 1
                continue
            out += "·"
            i += 1
            continue
        out += ch
        i += 1
    out = out.replace("sqrt(", "√(")
    res, i = "", 0
    while i < len(out):
        if out.startswith("√(", i):
            j = i + 2
            while j < len(out) and out[j] in "0123456789":
                j += 1
            if j > i + 2 and j < len(out) and out[j] == ")":
                res += "√" + out[i + 2:j]
                i = j + 1
                continue
        res += out[i]
        i += 1
    return _tok(_tok(res, "pi", "π"), "E", "e")


def _g(v, d=4):
    v = float(v)
    if not np.isfinite(v):
        return "?"
    if abs(v) < 10.0 ** (-d - 3):
        v = 0.0
    s = f"{v:.{d}g}"
    return "0" if s == "-0" else s


def _simp(e):
    try:
        if sp.count_ops(e) <= 80:
            return sp.simplify(e)
    except Exception:
        pass
    return e


def _cplx(v):
    try:
        c = complex(sp.N(v, 15))
    except Exception:
        return float("nan")
    if not (np.isfinite(c.real) and np.isfinite(c.imag)) or abs(c.imag) > 1e-10 * (1 + abs(c.real)):
        return float("nan")
    return c.real


def _eqv(v):
    try:
        v = _simp(sp.sympify(v))
    except Exception:
        return "= ? (tanımsız / undefined)", float("nan")
    fv = _cplx(v)
    if not np.isfinite(fv):
        return "= ? (tanımsız / undefined)", fv
    if v.is_Rational:
        return "= " + _pp(v), fv
    if v.has(sp.Float):
        return "≈ " + _g(fv), fv
    s = _pp(v)
    if len(s) > 22:
        return "≈ " + _g(fv), fv
    return f"= {s} ≈ {_g(fv)}", fv


def _short(v, d=3):
    try:
        v = sp.sympify(v)
        if v.is_Rational:
            return _pp(v)
    except Exception:
        return "?"
    fv = _cplx(v)
    if not np.isfinite(fv):
        return "?"
    s = _pp(v)
    if len(s) <= 6 and not v.has(sp.Float):
        return s
    return _g(fv, d)


def _cut(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


def _ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)
'''

# 3B çizim yardımcıları: yüzey dörtgenleri (nan olanlar atılır), gölgeli renk,
# eksen biçimi ve 3B ok.
_C3D = r'''
from matplotlib import colormaps
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def _grid(h, a, b, c, d, n=33):
    X, Y = np.meshgrid(np.linspace(a, b, n), np.linspace(c, d, n))
    return X, Y, h(X, Y)


def _zlims(Z):
    fin = Z[np.isfinite(Z)]
    if fin.size < 4:
        return -1.0, 1.0
    p2, p98 = np.percentile(fin, 2), np.percentile(fin, 98)
    w = max(p98 - p2, 1e-9)
    lo = max(fin.min(), p2 - 0.6 * w)
    hi = min(fin.max(), p98 + 0.6 * w)
    if hi - lo < 1e-9:
        lo, hi = lo - 1.0, hi + 1.0
    return float(lo), float(hi)


def _clipz(Z, lo, hi):
    return np.where(np.isfinite(Z), np.clip(Z, lo, hi), np.nan)


def _levels(lo, hi, k=8):
    lv = [float(v) for v in MaxNLocator(k).tick_values(lo, hi) if lo < v < hi]
    return lv if lv else [0.5 * (lo + hi)]


def _quads(X, Y, Z):
    V = np.stack([X, Y, Z], axis=-1)
    q = np.stack([V[:-1, :-1], V[:-1, 1:], V[1:, 1:], V[1:, :-1]], axis=2).reshape(-1, 4, 3)
    return q[np.all(np.isfinite(q[:, :, 2]), axis=1)]


def _colors(q, cmap, lo, hi, box, c0=0.08, c1=0.92):
    if len(q) == 0:
        return np.zeros((0, 4))
    zc = q[:, :, 2].mean(axis=1)
    col = colormaps[cmap](c0 + (c1 - c0) * np.clip((zc - lo) / (hi - lo + 1e-12), 0, 1))
    sc = np.array([box[1] - box[0], box[3] - box[2], (box[5] - box[4]) / 0.75]) + 1e-12
    u = (q[:, 2] - q[:, 0]) / sc
    w = (q[:, 3] - q[:, 1]) / sc
    nrm = np.cross(u, w)
    s = np.abs(nrm @ np.array([-0.45, -0.55, 0.70])) / (np.linalg.norm(nrm, axis=1) + 1e-12)
    col[:, :3] *= (0.62 + 0.38 * s)[:, None]
    return col


def _surface(ax, X, Y, Z, cmap, lo, hi, box, alpha=0.9, zorder=1, c0=0.08, c1=0.92):
    q = _quads(X, Y, Z)
    if len(q) == 0:
        q = np.array([[[box[0], box[2], lo], [box[1], box[2], lo],
                       [box[1], box[3], lo], [box[0], box[3], lo]]], dtype=float)
    col = _colors(q, cmap, lo, hi, box, c0, c1)
    ec = col.copy()
    ec[:, :3] *= 0.82
    pc = Poly3DCollection(q, facecolors=col, edgecolors=ec, linewidths=0.3, zorder=zorder)
    pc.set_alpha(alpha)
    ax.add_collection3d(pc)
    return pc


def _style3d(ax, box):
    ax.set_xlim(box[0], box[1])
    ax.set_ylim(box[2], box[3])
    ax.set_zlim(box[4], box[5])
    ax.set_xlabel("x", labelpad=-4)
    ax.set_ylabel("y", labelpad=-4)
    ax.set_zlabel("z", labelpad=-4)
    ax.tick_params(labelsize=7, pad=-2)
    ax.computed_zorder = False
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.set_pane_color((0.975, 0.977, 0.985, 1.0))
    ax.set_box_aspect((1, 1, 0.75), zoom=1.02)


def _sc(box):
    return np.array([box[1] - box[0], box[3] - box[2], (box[5] - box[4]) / 0.75])


def _line3(ax, color, lw=2.0, ls="-", zorder=4, **kw):
    ln, = ax.plot([], [], [], color=color, lw=lw, ls=ls, zorder=zorder, **kw)
    return ln


def _arrow3(ax, color, lw=2.6, zorder=6):
    shaft = _line3(ax, color, lw, zorder=zorder, solid_capstyle="round")
    head = _line3(ax, color, lw, zorder=zorder, solid_capstyle="round", solid_joinstyle="round")

    def setp(p, q, sc):
        if p is None:
            shaft.set_data_3d([], [], [])
            head.set_data_3d([], [], [])
            return
        p, q = np.asarray(p, float), np.asarray(q, float)
        dd = (q - p) / sc
        L = float(np.linalg.norm(dd))
        if not np.isfinite(L) or L < 1e-9:
            shaft.set_data_3d([], [], [])
            head.set_data_3d([], [], [])
            return
        u = dd / L
        w = np.cross(u, [0.0, 0.0, 1.0])
        if np.linalg.norm(w) < 0.25:
            w = np.cross(u, [1.0, 0.0, 0.0])
        w = w / np.linalg.norm(w)
        hl = min(0.07, 0.4 * L)
        a1 = q - (hl * u + 0.45 * hl * w) * sc
        a2 = q - (hl * u - 0.45 * hl * w) * sc
        shaft.set_data_3d([p[0], q[0]], [p[1], q[1]], [p[2], q[2]])
        head.set_data_3d([a1[0], q[0], a2[0]], [a1[1], q[1], a2[1]], [a1[2], q[2], a2[2]])
    return setp
'''


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["surface_3d"] = {
    "course": "calc3",
    "title": ("İki değişkenli fonksiyonun yüzeyi", "Surface of a function of two variables"),
    "topics": ["surface", "3d graph", "graph of a function of two variables",
               "functions of several variables", "multivariable function", "level curves",
               "level curve", "contour map", "contour plot", "traces", "domain and range",
               "critical points", "second derivative test", "local extrema", "saddle point",
               "quadric surfaces", "yüzey", "çok değişkenli fonksiyon", "iki değişkenli fonksiyon",
               "seviye eğrisi", "seviye eğrileri", "kontur", "eş yükselti", "tanım kümesi",
               "kritik nokta", "eyer noktası", "yerel ekstremum", "ikinci türev testi"],
    "code": _CORE + _C3D + r'''

_NAMES = {"min": ("yerel minimum", "local minimum"), "max": ("yerel maksimum", "local maximum"),
          "saddle": ("eyer noktası", "saddle point"),
          "?": ("test sonuçsuz (D = 0)", "test inconclusive (D = 0)")}
_KCOL = {"min": GREEN, "max": RED, "saddle": PURPLE, "?": GRAY}


def _box(P):
    a, b = _rng(P, "xmin", "xmax", -2.0, 2.0)
    c, d = _rng(P, "ymin", "ymax", -2.0, 2.0)
    return a, b, c, d


def _domain(f):
    conds = []
    for a in sp.preorder_traversal(f):
        if isinstance(a, sp.Pow):
            base, ex = a.as_base_exp()
            if base.is_number:
                continue
            if ex.is_Rational and ex.q % 2 == 0:
                conds.append(f"{_pp(base)} {'>' if ex < 0 else '≥'} 0")
            elif ex.is_number and ex.is_negative:
                conds.append(f"{_pp(base)} ≠ 0")
        elif isinstance(a, sp.log):
            conds.append(f"{_pp(a.args[0])} > 0")
        elif isinstance(a, (sp.asin, sp.acos)):
            conds.append(f"-1 ≤ {_pp(a.args[0])} ≤ 1")
        elif isinstance(a, sp.tan):
            conds.append(f"cos({_pp(a.args[0])}) ≠ 0")
    out = []
    for cnd in conds:
        if cnd not in out:
            out.append(cnd)
    return out


def _newton(fx, fy, box):
    a, b, c, d = box
    args = (_X, _Y)
    gx, gy = _num(fx, args), _num(fy, args)
    hxx, hxy, hyy = _num(sp.diff(fx, _X), args), _num(sp.diff(fx, _Y), args), _num(sp.diff(fy, _Y), args)
    X, Y = np.meshgrid(np.linspace(a, b, 9), np.linspace(c, d, 9))
    X, Y = X.ravel(), Y.ravel()
    for _ in range(40):
        u, v = gx(X, Y), gy(X, Y)
        A, B, C = hxx(X, Y), hxy(X, Y), hyy(X, Y)
        with np.errstate(all="ignore"):
            det = A * C - B * B
            X, Y = X - (C * u - B * v) / det, Y - (A * v - B * u) / det
    u, v = gx(X, Y), gy(X, Y)
    A, B, C = hxx(X, Y), hxy(X, Y), hyy(X, Y)
    with np.errstate(all="ignore"):
        det = A * C - B * B
        step = np.abs((C * u - B * v) / det) + np.abs((A * v - B * u) / det)
    tol = 1e-9 * (1 + b - a + d - c)
    ok = (np.isfinite(X) & np.isfinite(Y) & (np.abs(u) + np.abs(v) < 1e-7) & (step < 1e-7)
          & (X >= a - tol) & (X <= b + tol) & (Y >= c - tol) & (Y <= d + tol))
    pts = []
    for xx, yy in zip(X[ok], Y[ok]):
        xx, yy = round(float(xx), 9), round(float(yy), 9)
        if all(abs(xx - p[2]) + abs(yy - p[3]) > 1e-5 * (1 + b - a) for p in pts):
            pts.append((sp.Float(xx, 8), sp.Float(yy, 8), xx, yy))
    return pts


def _crit(f, box):
    fx, fy = sp.diff(f, _X), sp.diff(f, _Y)
    if fx == 0 and fy == 0:
        return "const", []
    try:
        deg = sp.Poly(f, _X, _Y).total_degree() if f.is_polynomial(_X, _Y) else 99
    except Exception:
        deg = 99
    pts, kind = [], "num"
    if deg <= 4:
        try:
            kind = "exact"
            for s in sp.solve([fx, fy], [_X, _Y], dict=True):
                if _X not in s or _Y not in s or s[_X].free_symbols or s[_Y].free_symbols:
                    kind = "curve"
                    continue
                cx, cy = _cplx(s[_X]), _cplx(s[_Y])
                if np.isfinite(cx) and np.isfinite(cy):
                    pts.append((s[_X], s[_Y], cx, cy))
        except Exception:
            pts, kind = [], "num"
    if kind == "num":
        pts = _newton(fx, fy, box)
    pts.sort(key=lambda p: (round(p[2], 6), round(p[3], 6)))
    return kind, pts[:6]


def _classify(f, xv, yv):
    sub = {_X: xv, _Y: yv}
    A = _simp(sp.diff(f, _X, 2).subs(sub))
    C = _simp(sp.diff(f, _Y, 2).subs(sub))
    B = _simp(sp.diff(f, _X, _Y).subs(sub))
    D = _simp(A * C - B ** 2)
    dv, av = _cplx(D), _cplx(A)
    if not (np.isfinite(dv) and np.isfinite(av)) or abs(dv) < 1e-10:
        key = "?"
    elif dv < 0:
        key = "saddle"
    else:
        key = "min" if av > 0 else "max"
    return key, A, B, C, D


def _analyse(P):
    f = _parse(P["f"])
    box = _box(P)
    kind, pts = _crit(f, box)
    info = []
    for xv, yv, cx, cy in pts:
        key, A, B, C, D = _classify(f, xv, yv)
        fv = _simp(f.subs({_X: xv, _Y: yv}))
        info.append({"x": xv, "y": yv, "cx": cx, "cy": cy, "key": key, "A": A, "B": B,
                     "C": C, "D": D, "f": fv, "cf": _cplx(fv)})
    return f, box, kind, info


def _pt(p):
    return f"({_short(p['x'])}, {_short(p['y'])})"


def solve(P):
    f, box, kind, info = _analyse(P)
    a, b, c, d = box
    fs = _pp(f)
    h = _num(f, (_X, _Y))
    X, Y = np.meshgrid(np.linspace(a, b, 161), np.linspace(c, d, 161))
    Z = h(X, Y)
    fin = Z[np.isfinite(Z)]
    region = f"[{_g(a)}, {_g(b)}] × [{_g(c)}, {_g(d)}]"
    steps = [(f"z = f(x, y) = {fs}: her (x, y) noktasına bir yükseklik atar; grafiği bir yüzeydir.",
              f"z = f(x, y) = {fs} assigns a height to each point (x, y); its graph is a surface.")]
    conds = _domain(f)
    if conds:
        dt = ", ".join(conds)
        steps.append((f"Tanım kümesi: {{(x, y) | {dt}}}", f"Domain: {{(x, y) | {dt}}}"))
    else:
        steps.append(("Tanım kümesi: ℝ² (her (x, y) için tanımlı)", "Domain: ℝ² (defined for every (x, y))"))
    if fin.size:
        zr = f"[{_g(fin.min())}, {_g(fin.max())}]"
        steps.append((f"{region} bölgesinde değerler z ∈ {zr} aralığını doldurur (görüntünün bu parçası).",
                      f"On {region} the values fill z ∈ {zr} (this part of the range)."))
        lv = ", ".join(_g(v, 3) for v in _levels(*_zlims(Z)))
        steps.append((f"Seviye eğrileri f(x, y) = c (c = {lv}): yüzeyi z = c düzlemiyle kesip xy-düzlemine "
                      "izdüşürürüz → kontur haritası.",
                      f"Level curves f(x, y) = c (c = {lv}): slice the surface with the plane z = c and drop "
                      "the cut onto the xy-plane → contour map."))
    else:
        steps.append((f"{region} bölgesinde f tanımlı değil.", f"f is not defined on {region}."))
    fx, fy = _simp(sp.diff(f, _X)), _simp(sp.diff(f, _Y))
    steps.append((f"Kısmi türevler: f_x = {_pp(fx)},  f_y = {_pp(fy)}",
                  f"Partial derivatives: f_x = {_pp(fx)},  f_y = {_pp(fy)}"))
    if kind == "const":
        steps.append(("f sabit: her nokta kritik noktadır.", "f is constant: every point is critical."))
        ans = ("f sabit fonksiyon", "f is constant")
    elif not info:
        extra = (" (ayrıca bir eğri boyunca kritik noktalar var)", " (plus a whole curve of critical points)") \
            if kind == "curve" else ("", "")
        steps.append(("f_x = 0 ve f_y = 0 sisteminin bu bölgede çözümü yok ⇒ kritik nokta yok" + extra[0],
                      "f_x = 0 and f_y = 0 has no solution here ⇒ no critical points" + extra[1]))
        ans = ("Kritik nokta yok" + extra[0], "No critical points" + extra[1])
    else:
        pl = ", ".join(_pt(p) for p in info)
        how = (" (sayısal, Newton)", " (numerically, Newton)") if kind == "num" else ("", "")
        steps.append((f"f_x = 0 ve f_y = 0 sistemini çöz{how[0]} ⇒ kritik nokta(lar): {pl}",
                      f"Solve f_x = 0 and f_y = 0{how[1]} ⇒ critical point(s): {pl}"))
        steps.append(("İkinci türev testi: D = f_xx·f_yy − (f_xy)²; D > 0 ve f_xx > 0 ⇒ min, D > 0 ve "
                      "f_xx < 0 ⇒ maks, D < 0 ⇒ eyer",
                      "Second-derivative test: D = f_xx·f_yy − (f_xy)²; D > 0 and f_xx > 0 ⇒ min, "
                      "D > 0 and f_xx < 0 ⇒ max, D < 0 ⇒ saddle"))
        for p in info[:4]:
            nm = _NAMES[p["key"]]
            dd = (f"f_xx = {_short(p['A'])}, f_yy = {_short(p['C'])}, f_xy = {_short(p['B'])} ⇒ "
                  f"D = ({_short(p['A'])})({_short(p['C'])}) − ({_short(p['B'])})² = {_short(p['D'])}")
            steps.append((f"{_pt(p)}: {dd} ⇒ {nm[0]}, f = {_short(p['f'])}",
                          f"{_pt(p)}: {dd} ⇒ {nm[1]}, f = {_short(p['f'])}"))
        ans = ("; ".join(f"{_pt(p)} {_NAMES[p['key']][0]} (f = {_short(p['f'])})" for p in info),
               "; ".join(f"{_pt(p)} {_NAMES[p['key']][1]} (f = {_short(p['f'])})" for p in info))
    return {"answer": ans, "steps": steps, "fmt": {"fx": fs, "region": region}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = lambda s_tr, s_en: s_tr if tr else s_en
    f, (a, b, c, d), kind, info = _analyse(P)
    h = _num(f, (_X, _Y))
    X, Y, Z = _grid(h, a, b, c, d, 34)
    lo, hi = _zlims(Z)
    Zc = _clipz(Z, lo, hi)
    span = hi - lo
    floor = lo - 0.45 * span
    box = (a, b, c, d, floor, hi + 0.04 * span)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.55, 1], height_ratios=[1.25, 1], left=0.0,
                          right=0.975, top=0.94, bottom=0.03, wspace=0.12, hspace=0.18)
    ax = fig.add_subplot(gs[:, 0], projection="3d")
    cx = fig.add_subplot(gs[0, 1])
    tx = fig.add_subplot(gs[1, 1])
    tx.axis("off")
    _style3d(ax, box)
    surf = _surface(ax, X, Y, Zc, "viridis", lo, hi, box, alpha=0.0)
    outline = _line3(ax, GRAY, 1.0, zorder=0.4)
    outline.set_data_3d([a, b, b, a, a], [c, c, d, d, c], [floor] * 5)
    levels = _levels(lo, hi)
    Zm = np.ma.masked_invalid(Zc)
    cmap = colormaps["viridis"]
    cx.set_xlim(a, b)
    cx.set_ylim(c, d)
    if 0.33 < (d - c) / (b - a) < 3:
        cx.set_aspect("equal", adjustable="box")
    cx.tick_params(labelsize=7)
    cx.set_title(T("Kontur haritası (üstten görünüş)", "Contour map (top view)"), fontsize=9.5)
    cx.grid(alpha=0.25)
    groups = []
    for k, v in enumerate(levels):
        col = cmap(0.08 + 0.84 * (v - lo) / (hi - lo + 1e-12))
        dark = tuple(0.75 * ch for ch in col[:3])
        arts = []
        try:
            arts.append(ax.contour(X, Y, Zm, levels=[v], colors=[col], zdir="z", offset=floor,
                                   linewidths=1.5, linestyles="solid", zorder=0.5))
            arts.append(ax.contour(X, Y, Zm, levels=[v], colors=["white"], linewidths=1.6,
                                   linestyles="solid", zorder=3, alpha=0.95))
            c2 = cx.contour(X, Y, Zm, levels=[v], colors=[dark], linewidths=1.5, linestyles="solid")
            arts.append(c2)
            arts += list(cx.clabel(c2, fmt=lambda val: _g(val, 3), fontsize=7, inline=True))
        except Exception:
            pass
        groups.append((v, arts))
    plane = Poly3DCollection([[[a, c, lo], [b, c, lo], [b, d, lo], [a, d, lo]]],
                             facecolors=[(0.42, 0.45, 0.5, 0.22)], edgecolors=[(0.3, 0.3, 0.35, 0.6)],
                             linewidths=1.0, zorder=2)
    ax.add_collection3d(plane)
    cin = [p for p in info if a <= p["cx"] <= b and c <= p["cy"] <= d and np.isfinite(p["cf"])]
    cart = []
    for p in cin:
        zz = min(max(p["cf"], lo), hi)
        col = _KCOL[p["key"]]
        m1 = _line3(ax, col, 0, zorder=7, marker="o", ms=8, mec="white", mew=1.2)
        m2 = _line3(ax, col, 1.2, ls="--", zorder=6)
        m3 = _line3(ax, col, 0, zorder=1, marker="o", ms=5)
        lab = ax.text(p["cx"], p["cy"], zz + 0.12 * span, "", color=col, fontsize=8.5, zorder=8,
                      fontweight="bold", ha="center",
                      bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col, alpha=0.85))
        dm, = cx.plot([], [], "o", color=col, ms=8, mec="white", mew=1.2, zorder=6)
        dl = cx.text(p["cx"], p["cy"], "", color=col, fontsize=8, fontweight="bold",
                     ha="left", va="bottom", zorder=7)
        cart.append((p, zz, m1, m2, m3, lab, dm, dl))
    info_t = ax.text2D(0.02, 1.0, "", transform=ax.transAxes, va="top", fontsize=10, bbox=BOX,
                       zorder=20)
    fs = _pp(f)
    conds = _domain(f)
    fx, fy = _simp(sp.diff(f, _X)), _simp(sp.diff(f, _Y))
    fin = Z[np.isfinite(Z)]
    rows = [(0, _cut("f(x, y) = " + fs, 40), "#111827"),
            (12, _cut(T("Tanım: ", "Domain: ") + (", ".join(conds) if conds else "ℝ²"), 40), "#111827"),
            (18, _cut(T("Bölgede z ∈ ", "On region z ∈ ") +
                      (f"[{_g(fin.min(), 3)}, {_g(fin.max(), 3)}]" if fin.size else "—"), 40), "#111827"),
            (100, _cut(f"f_x = {_pp(fx)}", 40), "#111827"),
            (100, _cut(f"f_y = {_pp(fy)}", 40), "#111827")]
    if info:
        for p in info[:3]:
            rows.append((110, _cut(f"{_pt(p)}: D = {_short(p['D'])} ⇒ {_NAMES[p['key']][0 if tr else 1]}", 40),
                         _KCOL[p["key"]]))
    elif kind == "const":
        rows.append((110, T("f sabit", "f is constant"), GRAY))
    else:
        rows.append((110, T("Kritik nokta yok", "No critical points"), GRAY))
    texts = []
    for k, (t0, s, col) in enumerate(rows):
        texts.append((t0, tx.text(0.0, 0.97 - k * 0.125, s, fontsize=9.5, color=col, va="top",
                                  transform=tx.transAxes, alpha=0)))
    N = 150

    def update(i):
        ax.view_init(elev=27, azim=-60 + 38 * np.sin(np.pi * i / (N - 1)))
        surf.set_alpha(0.9 * _ease(i / 22))
        cl = lo + (hi - lo) * min(1.0, max(0.0, (i - 26) / 70))
        if 26 <= i < 100:
            plane.set_verts([[[a, c, cl], [b, c, cl], [b, d, cl], [a, d, cl]]])
            plane.set_alpha(0.25)
        else:
            plane.set_verts([[[a, c, floor], [a, c, floor], [a, c, floor]]])
            plane.set_alpha(0.0)
        for v, arts in groups:
            vis = i >= 26 and cl >= v
            for art in arts:
                art.set_visible(vis)
        for p, zz, m1, m2, m3, lab, dm, dl in cart:
            on = i >= 100
            if on:
                m1.set_data_3d([p["cx"]], [p["cy"]], [zz])
                m2.set_data_3d([p["cx"], p["cx"]], [p["cy"], p["cy"]], [floor, zz])
                m3.set_data_3d([p["cx"]], [p["cy"]], [floor])
                dm.set_data([p["cx"]], [p["cy"]])
            else:
                for m in (m1, m2, m3):
                    m.set_data_3d([], [], [])
                dm.set_data([], [])
            lab.set_text(_NAMES[p["key"]][0 if tr else 1] if i >= 108 else "")
            dl.set_text(" " + _pt(p) if i >= 108 else "")
        for t0, t in texts:
            t.set_alpha(min(1.0, max(0.0, (i - t0) / 8)))
        if i < 26:
            info_t.set_text(T("1) z = f(x, y) yüzeyi:\n   her (x, y) için yükseklik f(x, y)",
                              "1) The surface z = f(x, y):\n   height f(x, y) above each (x, y)"))
        elif i < 100:
            info_t.set_text(T(f"2) z = {_g(cl, 3)} düzlemiyle kes →\n   seviye eğrisi f(x, y) = {_g(cl, 3)},"
                              "\n   tabana (xy-düzlemine) izdüşür",
                              f"2) Slice with the plane z = {_g(cl, 3)} →\n   level curve f(x, y) = {_g(cl, 3)},"
                              "\n   dropped onto the xy-plane"))
        elif i < 128:
            info_t.set_text(T("3) ∇f = 0 ⇒ kritik noktalar;\n   D testiyle sınıflandır",
                              "3) ∇f = 0 ⇒ critical points;\n   classify with the D test"))
        else:
            if cin:
                s = "\n".join(f"{_pt(p)}: {_NAMES[p['key']][0 if tr else 1]}, f = {_short(p['f'])}"
                              for p in cin[:3])
            else:
                s = T("Bu bölgede kritik nokta yok", "No critical points in this region")
            info_t.set_text(T("4) Sonuç\n", "4) Result\n") + s)
        return []

    return N, update


def vary(P, rnd):
    form = rnd.choice(["bowl", "cubic", "shift", "saddle"])
    x, y = _X, _Y
    if form == "bowl":
        p, q = rnd.choice([1, 2, 3, -1, -2]), rnd.choice([1, 2, 3, -1, -2])
        f, box = p * x ** 2 + q * y ** 2, (-2, 2, -2, 2)
    elif form == "cubic":
        k = rnd.choice([1, 2, -1, -2])
        f, box = x ** 3 - 3 * x + k * y ** 2, (-2, 2, -2, 2)
    elif form == "shift":
        h0, k0 = rnd.randint(-2, 2), rnd.randint(-2, 2)
        s = rnd.choice([1, -1])
        f, box = s * (x ** 2 + y ** 2 - 2 * h0 * x - 2 * k0 * y), (h0 - 3, h0 + 3, k0 - 3, k0 + 3)
    else:
        p, q = rnd.randint(-2, 2), rnd.choice([1, 2, 3])
        f, box = x * y - p * x - q * y, (q - 3, q + 3, p - 3, p + 3)
    return {"f": sp.sstr(sp.expand(f)), "xmin": box[0], "xmax": box[1], "ymin": box[2], "ymax": box[3]}
''',
}
EXAMPLES += [
    {"id": "calc3-surf-1", "kind": "surface_3d",
     "title": ("Eyer yüzeyi ve seviye eğrileri", "Saddle surface and level curves"),
     "q": ("f(x, y) = {fx} yüzeyini {region} bölgesinde çiz. Tanım kümesini, bu bölgedeki değer "
           "aralığını, seviye eğrilerini ve kritik noktaları incele.",
           "Sketch the surface f(x, y) = {fx} over {region}. Describe its domain, the values it takes "
           "there, its level curves and its critical points."),
     "P": {"f": "x**2 - y**2", "xmin": -2, "xmax": 2, "ymin": -2, "ymax": 2}},
    {"id": "calc3-surf-2", "kind": "surface_3d", "topics": ["relative extrema", "local max", "local min"],
     "title": ("Kübik yüzeyde min ve eyer", "Minimum and saddle on a cubic surface"),
     "q": ("f(x, y) = {fx} fonksiyonunun kritik noktalarını bul ve ikinci türev testiyle sınıflandır. "
           "Yüzeyi {region} üzerinde göster.",
           "Find the critical points of f(x, y) = {fx} and classify them with the second-derivative "
           "test. Show the surface over {region}."),
     "P": {"f": "x**3 - 3*x + y**2", "xmin": -2, "xmax": 2, "ymin": -2, "ymax": 2}},
    {"id": "calc3-surf-3", "kind": "surface_3d", "topics": ["hill", "terrain", "tepe", "arazi"],
     "title": ("Tepe biçimli arazi", "A hill-shaped terrain"),
     "q": ("Bir tepenin yüksekliği h(x, y) = {fx} (km) ile modelleniyor. {region} bölgesinde yüzeyi "
           "ve eş yükselti (seviye) eğrilerini çiz; zirve nerede?",
           "The height of a hill is modelled by h(x, y) = {fx} (km). Over {region} draw the surface "
           "and its contour lines; where is the summit?"),
     "P": {"f": "4*exp(-(x**2 + y**2)/2)", "xmin": -3, "xmax": 3, "ymin": -3, "ymax": 3}},
]
