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
    try:
        if f.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
            raise ValueError("undefined")
        g = sp.lambdify(args, f, "numpy")
    except Exception:
        def g(*a):
            return np.nan

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
    if isinstance(e, str):
        s = e
    else:
        s = sp.sstr(e)
        if isinstance(e, sp.Add):
            c0, rest = e.as_coeff_Add()
            rs = sp.sstr(rest)
            if c0.is_number and c0 > 0 and rs.startswith("-"):
                s = sp.sstr(c0) + " - " + rs[1:]
            elif c0.is_number and c0 < 0 and not rs.startswith("-"):
                s = rs + " - " + sp.sstr(-c0)
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
            if out.endswith("pi") and not out[-3:-2].isalpha() and q in ("x", "y", "t", "("):
                out = out[:-2] + "π"
                i += 1
                continue
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


def _dn(v):
    v = sp.sympify(v)
    if v.is_Rational and not v.is_Integer:
        q, k = int(v.q), 0
        for pr in (2, 5):
            while q % pr == 0:
                q //= pr
                k += 1
        if q == 1 and k <= 12:
            s = f"{float(v):.{k}f}".rstrip("0").rstrip(".")
            return "0" if s == "-0" else s
    return _pp(v)


def _eqv(v, dec=False, d=4):
    try:
        v = _simp(sp.sympify(v))
    except Exception:
        return "= ? (tanımsız / undefined)", float("nan")
    fv = _cplx(v)
    if not np.isfinite(fv):
        return "= ? (tanımsız / undefined)", fv
    if v.is_Rational:
        if dec or v.is_Integer:
            return "= " + (_dn(v) if dec else _pp(v)), fv
        dn = _dn(v)
        return (f"= {_pp(v)} = {dn}" if dn != _pp(v) else f"= {_pp(v)} ≈ {_g(fv, d)}"), fv
    if v.has(sp.Float):
        return "≈ " + _g(fv, d), fv
    s = _pp(v)
    if len(s) > 22:
        return "≈ " + _g(fv, d), fv
    return f"= {s} ≈ {_g(fv, d)}", fv


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
    if len(s) <= 10 and not v.has(sp.Float):
        return s
    return _g(fv, d)


def _nm(v, alt=False):
    v = sp.sympify(v)
    s = _pp(v)
    name = s if (v.is_Integer and v >= 0) or (v.is_Float and v >= 0) else "(" + s + ")"
    return sp.Symbol(name, real=True) if alt else sp.Symbol(name)


def _shown(e, xv=None, yv=None, tv=None):
    rep = {}
    if xv is not None:
        rep[_X] = _nm(xv)
    if yv is not None:
        rep[_Y] = _nm(yv, True)
    if tv is not None:
        rep[_T] = _nm(tv)
    try:
        s = _pp(e.subs(rep, simultaneous=True))
    except Exception:
        return ""
    return s if len(s) <= 64 else ""


_MEMO = {}


def _cached(tag, P, fn):
    key = (tag,) + tuple(sorted((str(k), repr(v)) for k, v in P.items() if k != "lang"))
    if key not in _MEMO:
        if len(_MEMO) > 48:
            _MEMO.clear()
        _MEMO[key] = fn(P)
    return _MEMO[key]


def _cut(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


def _ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)
'''

# Izgara yardımcıları (z aralığı, seviye değerleri) ve 3B çizim yardımcıları:
# yüzey dörtgenleri (nan olanlar atılır), gölgeli renk, eksen biçimi, 3B ok.
_CGRID = r'''
from matplotlib import colormaps
from matplotlib.ticker import MaxNLocator


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


'''

_C3D = r'''
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


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


def _set_alpha(S, a, ea=None):
    fc = S["fc"].copy()
    ec = S["ec"].copy()
    fc[:, 3] = fc[:, 3] * a
    ec[:, 3] = ec[:, 3] * (a if ea is None else ea)
    S["pc"].set_facecolor(fc)
    S["pc"].set_edgecolor(ec)


def _surface(ax, X, Y, Z, cmap, lo, hi, box, alpha=0.9, zorder=1, c0=0.08, c1=0.92):
    q = _quads(X, Y, Z)
    if len(q) == 0:
        q = np.array([[[box[0], box[2], lo], [box[1], box[2], lo],
                       [box[1], box[3], lo], [box[0], box[3], lo]]], dtype=float)
    col = _colors(q, cmap, lo, hi, box, c0, c1)
    ec = col.copy()
    ec[:, :3] *= 0.82
    pc = Poly3DCollection(q, facecolors=col, edgecolors=ec, linewidths=0.3, zorder=zorder)
    ax.add_collection3d(pc)
    S = {"pc": pc, "fc": col, "ec": ec}
    _set_alpha(S, alpha)
    return S


def _poly(ax, verts, color, zorder=2, lw=1.0, ec=None):
    from matplotlib.colors import to_rgba
    pc = Poly3DCollection(verts, linewidths=lw, zorder=zorder)
    ax.add_collection3d(pc)
    S = {"pc": pc, "fc": np.array([to_rgba(color)]), "ec": np.array([to_rgba(ec or color)])}
    _set_alpha(S, 0.0)
    return S


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
        a.set_major_locator(MaxNLocator(5))
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
    "code": _CORE + _CGRID + _C3D + r'''

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
        return "const", [], []
    try:
        deg = sp.Poly(f, _X, _Y).total_degree() if f.is_polynomial(_X, _Y) else 99
    except Exception:
        deg = 99
    pts, kind, curves = [], "num", []
    if deg <= 4:
        try:
            kind = "exact"
            for s in sp.solve([fx, fy], [_X, _Y], dict=True):
                if _X not in s or _Y not in s or s[_X].free_symbols or s[_Y].free_symbols:
                    curves.append(", ".join(f"{_pp(k)} = {_pp(v)}" for k, v in s.items()))
                    continue
                cx, cy = _cplx(s[_X]), _cplx(s[_Y])
                if np.isfinite(cx) and np.isfinite(cy):
                    pts.append((s[_X], s[_Y], cx, cy))
        except Exception:
            pts, kind, curves = [], "num", []
    if kind == "num":
        pts = _newton(fx, fy, box)
    pts.sort(key=lambda p: (round(p[2], 6), round(p[3], 6)))
    return kind, pts[:6], curves


def _classify(f, xv, yv):
    sub = {_X: xv, _Y: yv}
    A = _simp(sp.diff(f, _X, 2).subs(sub, simultaneous=True))
    C = _simp(sp.diff(f, _Y, 2).subs(sub, simultaneous=True))
    B = _simp(sp.diff(f, _X, _Y).subs(sub, simultaneous=True))
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
    return _cached("analyse", P, _analyse0)


def _analyse0(P):
    f = _parse(P["f"])
    box = _box(P)
    kind, pts, curves = _crit(f, box)
    info = []
    for xv, yv, cx, cy in pts:
        key, A, B, C, D = _classify(f, xv, yv)
        fv = _simp(f.subs({_X: xv, _Y: yv}, simultaneous=True))
        info.append({"x": xv, "y": yv, "cx": cx, "cy": cy, "key": key, "A": A, "B": B,
                     "C": C, "D": D, "f": fv, "cf": _cplx(fv)})
    return f, box, kind, info, curves


def _pt(p):
    return f"({_short(p['x'])}, {_short(p['y'])})"


def solve(P):
    f, box, kind, info, curves = _analyse(P)
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
    elif not info and not curves:
        steps.append(("f_x = 0 ve f_y = 0 sisteminin bu bölgede çözümü yok ⇒ kritik nokta yok",
                      "f_x = 0 and f_y = 0 has no solution here ⇒ no critical points"))
        ans = ("Kritik nokta yok", "No critical points")
    elif not info:
        cv = "; ".join(curves)
        steps.append((f"f_x = 0 ve f_y = 0 bir eğri boyunca sağlanır: {cv} ⇒ bu eğrinin her noktası kritiktir "
                      "(orada D = 0, test sonuç vermez)",
                      f"f_x = 0 and f_y = 0 hold along a whole curve: {cv} ⇒ every point on it is critical "
                      "(D = 0 there, the test is inconclusive)"))
        ans = (f"Kritik noktalar bir eğri boyunca: {cv}", f"Critical points fill a curve: {cv}")
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
    f, (a, b, c, d), kind, info, curves = _analyse(P)
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
    plane = _poly(ax, [[[a, c, lo], [b, c, lo], [b, d, lo], [a, d, lo]]], "#6B7280", 2, 1.0, "#374151")
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
    Zf = _grid(h, a, b, c, d, 161)[2]
    fin = Zf[np.isfinite(Zf)]
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
    elif curves:
        rows.append((110, _cut(T("Kritik eğri: ", "Critical curve: ") + "; ".join(curves), 40), GRAY))
    else:
        rows.append((110, T("Kritik nokta yok", "No critical points"), GRAY))
    texts = []
    for k, (t0, s, col) in enumerate(rows):
        texts.append((t0, tx.text(0.0, 0.97 - k * 0.125, s, fontsize=9.5, color=col, va="top",
                                  transform=tx.transAxes, alpha=0)))
    N = 150

    def update(i):
        ax.view_init(elev=27, azim=-60 + 38 * np.sin(np.pi * i / (N - 1)))
        fa = _ease(i / 22)
        _set_alpha(surf, 0.9 * fa, 0.55 + 0.35 * fa)
        cl = lo + (hi - lo) * min(1.0, max(0.0, (i - 26) / 70))
        if 26 <= i < 100:
            plane["pc"].set_verts([[[a, c, cl], [b, c, cl], [b, d, cl], [a, d, cl]]])
            _set_alpha(plane, 0.22, 0.6)
        else:
            _set_alpha(plane, 0.0)
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
            elif curves:
                s = _cut(T("Kritik noktalar bir eğri boyunca: ", "Critical points along: ") + "; ".join(curves), 48)
            else:
                s = T("Bu bölgede kritik nokta yok", "No critical points in this region")
            info_t.set_text(T("4) Sonuç\n", "4) Result\n") + s)
        return []

    return N, update


def vary(P, rnd):
    form = rnd.choice(["bowl", "cubic", "shift", "saddle"])
    x, y = _X, _Y
    if "exp" in str(P.get("f", "")):
        A, s, h0, k0 = rnd.choice([2, 3, 4, 5]), rnd.choice([2, 4]), rnd.randint(-1, 1), rnd.randint(-1, 1)
        f = A * sp.exp(-((x - h0) ** 2 + (y - k0) ** 2) / s)
        return {"f": sp.sstr(f), "xmin": h0 - 3, "xmax": h0 + 3, "ymin": k0 - 3, "ymax": k0 + 3}
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

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["partial_derivatives"] = {
    "course": "calc3",
    "title": ("Kısmi türevler: yüzey kesitleri ve eğimler", "Partial derivatives: slices and slopes"),
    "topics": ["partial derivative", "partial derivatives", "partial differentiation",
               "first-order partial", "rate of change in x", "traces", "slope of a trace",
               "fx and fy", "kısmi türev", "kısmi türevler", "kısmi türev geometrik anlam",
               "iz eğrisi", "değişim hızı"],
    "code": _CORE + _CGRID + _C3D + r'''


def _setup(P):
    f = _parse(P["f"])
    x0, y0 = _exact(P["x0"]), _exact(P["y0"])
    return f, x0, y0, _simp(sp.diff(f, _X)), _simp(sp.diff(f, _Y))


def solve(P):
    f, x0, y0, fx, fy = _setup(P)
    pt = f"({_pp(x0)}, {_pp(y0)})"
    sub = {_X: x0, _Y: y0}
    z0s, _ = _eqv(f.subs(sub, simultaneous=True))
    vxs, _ = _eqv(fx.subs(sub, simultaneous=True))
    vys, _ = _eqv(fy.subs(sub, simultaneous=True))
    shx, shy = _shown(fx, x0, y0), _shown(fy, x0, y0)
    ex = f"f_x{pt} = {shx} {vxs}" if shx and ("= " + shx) != vxs else f"f_x{pt} {vxs}"
    ey = f"f_y{pt} = {shy} {vys}" if shy and ("= " + shy) != vys else f"f_y{pt} {vys}"
    X0, Y0 = _pp(x0), _pp(y0)
    steps = [
        (f"f(x, y) = {_pp(f)};  nokta P{pt}:  f{pt} {z0s}", f"f(x, y) = {_pp(f)};  point P{pt}:  f{pt} {z0s}"),
        (f"f_x = ∂f/∂x: y sabit tutulur, x'e göre türev alınır ⇒ f_x = {_pp(fx)}",
         f"f_x = ∂f/∂x: hold y constant and differentiate in x ⇒ f_x = {_pp(fx)}"),
        (ex, ex),
        (f"f_y = ∂f/∂y: x sabit tutulur, y'ye göre türev alınır ⇒ f_y = {_pp(fy)}",
         f"f_y = ∂f/∂y: hold x constant and differentiate in y ⇒ f_y = {_pp(fy)}"),
        (ey, ey),
        (f"Geometrik anlam: y = {Y0} düzlemi yüzeyi z = f(x, {Y0}) eğrisinde keser; bu eğrinin x = {X0} "
         f"noktasındaki eğimi f_x {vxs}. x = {X0} düzlemindeki z = f({X0}, y) eğrisinin y = {Y0} "
         f"noktasındaki eğimi f_y {vys}.",
         f"Geometric meaning: the plane y = {Y0} cuts the surface in the curve z = f(x, {Y0}); its slope at "
         f"x = {X0} is f_x {vxs}. The curve z = f({X0}, y) in the plane x = {X0} has slope f_y {vys} "
         f"at y = {Y0}."),
        ("Teğet doğrular: z = z₀ + f_x·(x − x₀) (y = y₀ düzleminde) ve z = z₀ + f_y·(y − y₀) (x = x₀ düzleminde)",
         "Tangent lines: z = z₀ + f_x·(x − x₀) (in the plane y = y₀) and z = z₀ + f_y·(y − y₀) (in the plane x = x₀)"),
    ]
    ans = f"f_x{pt} {vxs},  f_y{pt} {vys}"
    return {"answer": ans, "steps": steps,
            "fmt": {"fx": _pp(f), "pt": pt}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = lambda s_tr, s_en: s_tr if tr else s_en
    f, x0e, y0e, fx, fy = _setup(P)
    x0, y0 = float(x0e), float(y0e)
    R = abs(_fl(P.get("r", 2))) or 2.0
    h = _num(f, (_X, _Y))
    a, b, c, d = x0 - R, x0 + R, y0 - R, y0 + R
    X, Y, Z = _grid(h, a, b, c, d, 30)
    z0 = float(h(x0, y0))
    vx = _cplx(fx.subs({_X: x0e, _Y: y0e}, simultaneous=True))
    vy = _cplx(fy.subs({_X: x0e, _Y: y0e}, simultaneous=True))
    xs = np.linspace(a, b, 161)
    ys = np.linspace(c, d, 161)
    zx, zy = h(xs, y0), h(x0, ys)
    lo, hi = _zlims(np.concatenate([Z.ravel(), zx, zy, [z0]]))
    span = hi - lo
    lo, hi = lo - 0.06 * span, hi + 0.06 * span
    box = (a, b, c, d, lo, hi)
    sc = _sc(box)
    Zc = _clipz(Z, lo, hi)
    zx = np.where((zx >= lo) & (zx <= hi), zx, np.nan)
    zy = np.where((zy >= lo) & (zy <= hi), zy, np.nan)
    okp = np.isfinite(z0)

    def tlen(v):
        if not (okp and np.isfinite(v)):
            return 0.0
        return min(0.8 * R, 0.42 * (hi - lo) / max(abs(v), 1e-9))
    Lx, Ly = tlen(vx), tlen(vy)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.45, 1], left=0.0, right=0.975, top=0.93,
                          bottom=0.09, wspace=0.2, hspace=0.5)
    ax = fig.add_subplot(gs[:, 0], projection="3d")
    p1 = fig.add_subplot(gs[0, 1])
    p2 = fig.add_subplot(gs[1, 1])
    _style3d(ax, box)
    surf = _surface(ax, X, Y, Zc, "Blues", lo, hi, box, alpha=0.0, c0=0.3, c1=0.85)
    py = _poly(ax, [[[a, y0, lo], [b, y0, lo], [b, y0, hi], [a, y0, hi]]], ORANGE, 2, 1.0)
    px = _poly(ax, [[[x0, c, lo], [x0, d, lo], [x0, d, hi], [x0, c, hi]]], GREEN, 2, 1.0)
    cxl = _line3(ax, ORANGE, 3.0, zorder=4)
    cyl = _line3(ax, GREEN, 3.0, zorder=4)
    txl = _line3(ax, "#111827", 2.2, zorder=5)
    tyl = _line3(ax, "#111827", 2.2, zorder=5)
    dot = _line3(ax, RED, 0, zorder=7, marker="o", ms=8, mec="white", mew=1.3)
    info = ax.text2D(0.02, 1.0, "", transform=ax.transAxes, va="top", fontsize=10, bbox=BOX, zorder=20)
    X0, Y0 = _pp(x0e), _pp(y0e)
    pt = f"({X0}, {Y0})"
    panels = []
    for pan, ss, zz, v, L, col, var, other in ((p1, xs, zx, vx, Lx, ORANGE, "x", f"y = {Y0}"),
                                                (p2, ys, zy, vy, Ly, GREEN, "y", f"x = {X0}")):
        s0 = x0 if var == "x" else y0
        fin = zz[np.isfinite(zz)]
        vals = list(fin) + ([z0 - abs(v) * L, z0 + abs(v) * L] if L > 0 else []) + ([z0] if okp else [])
        ylo, yhi = (min(vals), max(vals)) if vals else (-1.0, 1.0)
        pd_ = 0.12 * (yhi - ylo) + 1e-6
        pan.set_xlim(ss[0], ss[-1])
        pan.set_ylim(ylo - pd_, yhi + pd_)
        pan.grid(alpha=0.3)
        pan.tick_params(labelsize=7.5)
        pan.set_xlabel(var, fontsize=9, labelpad=1)
        pan.set_ylabel("z", fontsize=9, labelpad=1)
        lab = f"z = f(x, {Y0})" if var == "x" else f"z = f({X0}, y)"
        pan.set_title(T(f"{other} kesiti: {lab}", f"Slice {other}: {lab}"), fontsize=9.5, color=col)
        cv, = pan.plot([], [], color=col, lw=2.4)
        tl, = pan.plot([], [], color="#111827", lw=1.8)
        dp, = pan.plot([], [], "o", color=RED, ms=7, mec="white", mew=1.0, zorder=5)
        right = np.isfinite(v) and v < 0
        tt = pan.text(0.97 if right else 0.03, 0.93, "", transform=pan.transAxes, va="top",
                      ha="right" if right else "left", fontsize=9.5, color="#111827",
                      bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=col, alpha=0.9))
        panels.append((cv, tl, dp, tt, ss, zz, v, L, s0, var))
    N = 150
    vxs, vys = _short(fx.subs({_X: x0e, _Y: y0e}, simultaneous=True)), _short(fy.subs({_X: x0e, _Y: y0e}, simultaneous=True))

    def stage(i, t0, t1):
        return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))

    def update(i):
        az = -72 + 54 * _ease((i - 62) / 18.0) - 26 * _ease((i - 114) / 20.0)
        ax.view_init(elev=22, azim=az)
        _set_alpha(surf, 0.15 + 0.47 * _ease(i / 12.0))
        ay = 0.2 * stage(i, 14, 22) - 0.13 * stage(i, 62, 70)
        _set_alpha(py, ay, 3 * ay)
        ax_ = 0.2 * stage(i, 64, 72)
        _set_alpha(px, ax_, 3 * ax_)
        on = okp and i >= 6
        dot.set_data_3d(*(([x0], [y0], [z0]) if on else ([], [], [])))
        for k, (cv, tl, dp, tt, ss, zz, v, L, s0, var) in enumerate(panels):
            off = 0 if k == 0 else 50
            pr = stage(i, 20 + off, 46 + off)
            m = int(pr * len(ss))
            pt_ = stage(i, 46 + off, 60 + off)
            line3 = cxl if k == 0 else cyl
            tan3 = txl if k == 0 else tyl
            if m >= 2:
                cv.set_data(ss[:m], zz[:m])
                if var == "x":
                    line3.set_data_3d(ss[:m], np.full(m, y0), zz[:m])
                else:
                    line3.set_data_3d(np.full(m, x0), ss[:m], zz[:m])
            else:
                cv.set_data([], [])
                line3.set_data_3d([], [], [])
            if pt_ > 0 and L > 0:
                e = np.array([s0 - L * pt_, s0 + L * pt_])
                zt = z0 + v * (e - s0)
                tl.set_data(e, zt)
                if var == "x":
                    tan3.set_data_3d(e, [y0, y0], zt)
                else:
                    tan3.set_data_3d([x0, x0], e, zt)
            else:
                tl.set_data([], [])
                tan3.set_data_3d([], [], [])
            dp.set_data(*(([s0], [z0]) if (okp and i >= 20 + off) else ([], [])))
            if i >= 56 + off:
                nm = "f_x" if var == "x" else "f_y"
                tt.set_text(T(f"eğim = {nm}{pt} = {vxs if var == 'x' else vys}",
                              f"slope = {nm}{pt} = {vxs if var == 'x' else vys}"))
            else:
                tt.set_text("")
        if i < 14:
            info.set_text(T(f"1) Yüzey z = f(x, y) ve\n   P{pt}, z₀ = {_g(z0, 4)}",
                            f"1) Surface z = f(x, y) and\n   P{pt}, z₀ = {_g(z0, 4)}"))
        elif i < 64:
            info.set_text(T(f"2) y = {Y0} sabit: düzlem yüzeyi keser\n   → z = f(x, {Y0}) eğrisi;"
                            f"\n   P'deki eğimi f_x = {vxs}",
                            f"2) Hold y = {Y0}: the plane cuts the\n   surface → curve z = f(x, {Y0});"
                            f"\n   its slope at P is f_x = {vxs}"))
        elif i < 114:
            info.set_text(T(f"3) x = {X0} sabit: z = f({X0}, y) eğrisi;\n   P'deki eğimi f_y = {vys}",
                            f"3) Hold x = {X0}: curve z = f({X0}, y);\n   its slope at P is f_y = {vys}"))
        else:
            info.set_text(T(f"Sonuç:\n   f_x{pt} = {vxs}\n   f_y{pt} = {vys}",
                            f"Result:\n   f_x{pt} = {vxs}\n   f_y{pt} = {vys}"))
        return []

    return N, update


def vary(P, rnd):
    x, y = _X, _Y
    src = _parse(P.get("f", "x*y"))
    if "sqrt" in str(P.get("f", "")):
        x0, y0 = rnd.choice([(3, 4), (4, 3), (5, 12), (6, 8), (8, 6), (-3, 4), (4, -3), (12, 5)])
        return {"f": "sqrt(x**2 + y**2)", "x0": x0, "y0": y0}
    if src.as_coeff_Add()[0] > 0:
        C, p, q = rnd.choice([50, 60, 80, 100]), rnd.choice([1, 2, 3]), rnd.choice([1, 2, 3])
        return {"f": sp.sstr(C - p * x ** 2 - q * y ** 2), "x0": rnd.randint(1, 3), "y0": rnd.randint(1, 3)}
    form = rnd.choice(["quad", "mixed", "cubic"])
    x0, y0 = rnd.choice([-2, -1, 1, 2]), rnd.choice([-2, -1, 1, 2])
    if form == "quad":
        p, q, r = rnd.choice([1, 2, 3, -1]), rnd.choice([1, 2, -1, -2, 3]), rnd.choice([1, 2, -1])
        f = p * x ** 2 + q * x * y + r * y ** 2
    elif form == "mixed":
        k = rnd.choice([1, 2, 3, -1, -2])
        f = x ** 2 * y + k * y ** 2
    else:
        k = rnd.choice([1, 2, 3, 4])
        f = x * y ** 2 - k * x + y
    return {"f": sp.sstr(sp.expand(f)), "x0": x0, "y0": y0}
''',
}
EXAMPLES += [
    {"id": "calc3-pd-1", "kind": "partial_derivatives",
     "title": ("Bir noktada kısmi türevler", "Partial derivatives at a point"),
     "q": ("f(x, y) = {fx} için f_x ve f_y kısmi türevlerini bul ve {pt} noktasında hesapla. "
           "Bu sayıların yüzey üzerindeki anlamını göster.",
           "For f(x, y) = {fx}, find the partial derivatives f_x and f_y and evaluate them at {pt}. "
           "Show what these numbers mean on the surface."),
     "P": {"f": "x**2*y - y**2", "x0": 1, "y0": 2}},
    {"id": "calc3-pd-2", "kind": "partial_derivatives", "topics": ["temperature", "sıcaklık", "rate of change"],
     "title": ("Isınan levha: sıcaklığın değişim hızı", "Heated plate: rate of change of temperature"),
     "q": ("Bir metal levhanın sıcaklığı T(x, y) = {fx} (°C, x ve y cm). {pt} noktasında sıcaklık x ve y "
           "yönlerinde santimetre başına ne hızla değişir?",
           "The temperature of a metal plate is T(x, y) = {fx} (°C, x and y in cm). At {pt}, how fast does "
           "the temperature change per cm in the x and y directions?"),
     "P": {"f": "60 - 2*x**2 - y**2", "x0": 2, "y0": 3}},
    {"id": "calc3-pd-3", "kind": "partial_derivatives", "topics": ["distance function", "uzaklık"],
     "title": ("Uzaklık fonksiyonunun kısmi türevleri", "Partial derivatives of the distance function"),
     "q": ("Orijine uzaklık f(x, y) = {fx}. f_x ve f_y değerlerini {pt} noktasında bul.",
           "The distance to the origin is f(x, y) = {fx}. Find f_x and f_y at {pt}."),
     "P": {"f": "sqrt(x**2 + y**2)", "x0": 3, "y0": 4}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["tangent_plane"] = {
    "course": "calc3",
    "title": ("Teğet düzlem ve doğrusal yaklaşım", "Tangent plane and linear approximation"),
    "topics": ["tangent plane", "tangent planes", "linear approximation", "linearization",
               "local linearity", "differentials", "total differential", "normal line",
               "teğet düzlem", "doğrusal yaklaşım", "lineerleştirme", "diferansiyel", "tam diferansiyel"],
    "code": _CORE + _CGRID + _C3D + r'''


def _setup(P):
    f = _parse(P["f"])
    x0, y0 = _exact(P["x0"]), _exact(P["y0"])
    x1 = _exact(P.get("x1", x0 + sp.Rational(1, 10)))
    y1 = _exact(P.get("y1", y0 - sp.Rational(1, 10)))
    sub = {_X: x0, _Y: y0}
    z0 = _simp(f.subs(sub, simultaneous=True))
    fx, fy = _simp(sp.diff(f, _X)), _simp(sp.diff(f, _Y))
    return f, x0, y0, x1, y1, z0, fx, fy, _simp(fx.subs(sub, simultaneous=True)), _simp(fy.subs(sub, simultaneous=True))


def _lin(z0, A, B, x0, y0):
    def term(k, v, c):
        if k == 0:
            return ""
        inner = v if c == 0 else f"({v} {'-' if c > 0 else '+'} {_pp(abs(c))})"
        ks = "" if k == 1 else ("-" if k == -1 else _pp(k))
        sgn = " - " if ks.startswith("-") else " + "
        return sgn + ks.lstrip("-") + ("·" if ks.lstrip("-") and not ks.lstrip("-")[-1:].isdigit() else "") + inner
    return _pp(z0) + term(A, "x", x0) + term(B, "y", y0)


def _solve0(P):
    f, x0, y0, x1, y1, z0, fx, fy, A, B = _setup(P)
    pt = f"({_pp(x0)}, {_pp(y0)})"
    z0s, z0v = _eqv(z0)
    As, _ = _eqv(A)
    Bs, _ = _eqv(B)
    Lform = _lin(z0, A, B, x0, y0)
    Lexp = sp.expand(z0 + A * (_X - x0) + B * (_Y - y0))
    dx, dy = x1 - x0, y1 - y0
    Lval = _simp(z0 + A * dx + B * dy)
    fval = _simp(f.subs({_X: x1, _Y: y1}, simultaneous=True))
    Ls, Lv = _eqv(Lval, True, 6)
    fs_, fv = _eqv(fval, True, 6)
    p1 = f"({_dn(x1)}, {_dn(y1)})"
    steps = [
        (f"f(x, y) = {_pp(f)};  P{pt}:  z₀ = f{pt} {z0s}", f"f(x, y) = {_pp(f)};  P{pt}:  z₀ = f{pt} {z0s}"),
        (f"f_x = {_pp(fx)} ⇒ f_x{pt} {As};   f_y = {_pp(fy)} ⇒ f_y{pt} {Bs}",
         f"f_x = {_pp(fx)} ⇒ f_x{pt} {As};   f_y = {_pp(fy)} ⇒ f_y{pt} {Bs}"),
        ("Teğet düzlem: z = z₀ + f_x(x₀, y₀)(x − x₀) + f_y(x₀, y₀)(y − y₀)",
         "Tangent plane: z = z₀ + f_x(x₀, y₀)(x − x₀) + f_y(x₀, y₀)(y − y₀)"),
        (f"Yerine koy: z = {Lform}  ⇔  z = {_pp(Lexp)}", f"Substitute: z = {Lform}  ⇔  z = {_pp(Lexp)}"),
        (f"Normal vektör: n = ⟨f_x, f_y, −1⟩ = ⟨{_short(A)}, {_short(B)}, −1⟩",
         f"Normal vector: n = ⟨f_x, f_y, −1⟩ = ⟨{_short(A)}, {_short(B)}, −1⟩"),
        (f"Doğrusal yaklaşım: Δx = {_dn(dx)}, Δy = {_dn(dy)} ⇒ f{p1} ≈ L{p1} = {_pp(z0)} + ({_pp(A)})({_dn(dx)}) "
         f"+ ({_pp(B)})({_dn(dy)}) {Ls}",
         f"Linear approximation: Δx = {_dn(dx)}, Δy = {_dn(dy)} ⇒ f{p1} ≈ L{p1} = {_pp(z0)} + ({_pp(A)})({_dn(dx)}) "
         f"+ ({_pp(B)})({_dn(dy)}) {Ls}"),
        (f"Gerçek değer: f{p1} {fs_};  hata ≈ {_g(abs(fv - Lv), 3)} (nokta P'ye yakın olduğundan küçük)",
         f"Exact value: f{p1} {fs_};  error ≈ {_g(abs(fv - Lv), 3)} (small because the point is close to P)"),
    ]
    ans = f"z = {_pp(Lexp)};  L{p1} {Ls}  (f{p1} {fs_})"
    if not all(np.isfinite(_cplx(v)) for v in (z0, A, B)):
        steps = steps[:2] + [(f"f veya kısmi türevleri P{pt} noktasında tanımlı değil ⇒ orada teğet düzlem yok.",
                              f"f or its partial derivatives are undefined at P{pt} ⇒ no tangent plane there.")]
        ans = (f"P{pt} noktasında teğet düzlem yok (f_x veya f_y tanımsız)",
               f"No tangent plane at P{pt} (f_x or f_y undefined)")
    return {"answer": ans, "steps": steps, "fmt": {"fx": _pp(f), "pt": pt, "p1": p1}}


def solve(P):
    return _cached("solve", P, _solve0)


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = lambda s_tr, s_en: s_tr if tr else s_en
    f, x0e, y0e, x1e, y1e, z0e, fx, fy, Ae, Be = _setup(P)
    x0, y0, x1, y1 = float(x0e), float(y0e), float(x1e), float(y1e)
    z0, A, B = _cplx(z0e), _cplx(Ae), _cplx(Be)
    okp = np.isfinite(z0) and np.isfinite(A) and np.isfinite(B)
    if not np.isfinite(A):
        A = 0.0
    if not np.isfinite(B):
        B = 0.0
    R = abs(_fl(P.get("r", 2))) or 2.0
    h = _num(f, (_X, _Y))
    X, Y, Z = _grid(h, x0 - R, x0 + R, y0 - R, y0 + R, 28)
    lo0, hi0 = _zlims(np.concatenate([Z.ravel(), [z0]]))
    sp0 = hi0 - lo0
    lo0, hi0 = lo0 - 0.08 * sp0, hi0 + 0.08 * sp0
    ax = fig.add_subplot(111, projection="3d")
    fig.subplots_adjust(left=0.0, right=1.0, top=0.98, bottom=0.0)
    _style3d(ax, (x0 - R, x0 + R, y0 - R, y0 + R, lo0, hi0))
    ax.set_box_aspect((1.3, 1, 0.8), zoom=1.0)
    surf = _surface(ax, X, Y, _clipz(Z, lo0, hi0), "Blues", lo0, hi0,
                    (x0 - R, x0 + R, y0 - R, y0 + R, lo0, hi0), alpha=0.0, c0=0.3, c1=0.88)
    plane = _poly(ax, [[[x0, y0, z0]] * 4], ORANGE, 3, 0.9, "#B45309")
    txl = _line3(ax, ORANGE, 2.6, zorder=5)
    tyl = _line3(ax, GREEN, 2.6, zorder=5)
    dot = _line3(ax, RED, 0, zorder=8, marker="o", ms=8, mec="white", mew=1.3)
    dot1 = _line3(ax, PURPLE, 0, zorder=8, marker="D", ms=6, mec="white", mew=1.0)
    info = ax.text2D(0.01, 0.99, "", transform=ax.transAxes, va="top", fontsize=10, bbox=BOX, zorder=20)
    form = ax.text2D(0.99, 0.02, "", transform=ax.transAxes, va="bottom", ha="right", fontsize=10.5,
                     bbox=dict(boxstyle="round", fc="#FFF7ED", ec=ORANGE, alpha=0.95), zorder=20)
    sol = solve(P)
    Lexp = sp.expand(z0e + Ae * (_X - x0e) + Be * (_Y - y0e)) if okp else sp.Integer(0)
    pt = f"({_pp(x0e)}, {_pp(y0e)})"
    p1 = f"({_dn(x1e)}, {_dn(y1e)})"
    Lv = z0 + A * (x1 - x0) + B * (y1 - y0)
    fv = float(h(x1, y1))
    N = 150

    def plane_quad(w, s=1.0):
        e = w * s
        cs = [(x0 - e, y0 - e), (x0 + e, y0 - e), (x0 + e, y0 + e), (x0 - e, y0 + e)]
        return [[(u, v, z0 + A * (u - x0) + B * (v - y0)) for u, v in cs]]

    def zoom_state(i):
        return R * (1.0 - 0.85 * _ease((i - 78) / 40.0)) if okp else R

    cache = {"w": None}

    def set_window(w):
        if cache["w"] == w:
            return
        cache["w"] = w
        if w >= R - 1e-12:
            Xw, Yw, Zw = X, Y, Z
            lo, hi = lo0, hi0
        else:
            Xw, Yw, Zw = _grid(h, x0 - w, x0 + w, y0 - w, y0 + w, 22)
            fin = np.concatenate([Zw[np.isfinite(Zw)], [z0 - (abs(A) + abs(B)) * w, z0 + (abs(A) + abs(B)) * w]])
            fin = fin[np.isfinite(fin)]
            lo, hi = (float(np.min(fin)), float(np.max(fin))) if fin.size else (lo0, hi0)
            pad = 0.1 * (hi - lo) + 1e-9
            lo, hi = lo - pad, hi + pad
        bx = (x0 - w, x0 + w, y0 - w, y0 + w, lo, hi)
        q = _quads(Xw, Yw, _clipz(Zw, lo, hi))
        if len(q):
            col = _colors(q, "Blues", lo, hi, bx, 0.3, 0.88)
            ec = col.copy()
            ec[:, :3] *= 0.82
            surf["pc"].set_verts(q)
            surf["fc"], surf["ec"] = col, ec
        ax.set_xlim(bx[0], bx[1])
        ax.set_ylim(bx[2], bx[3])
        ax.set_zlim(bx[4], bx[5])
        cache["box"] = bx

    def update(i):
        w = zoom_state(i)
        set_window(w)
        ax.view_init(elev=24, azim=-58 + 22 * np.sin(np.pi * i / (N - 1)))
        _set_alpha(surf, 0.15 + 0.6 * _ease(i / 12.0))
        on = okp and i >= 5
        dot.set_data_3d(*(([x0], [y0], [z0]) if on else ([], [], [])))
        lt = 0.75 * w * _ease((i - 14) / 18.0) if okp else 0.0
        if lt > 0:
            txl.set_data_3d([x0 - lt, x0 + lt], [y0, y0], [z0 - A * lt, z0 + A * lt])
            tyl.set_data_3d([x0, x0], [y0 - lt, y0 + lt], [z0 - B * lt, z0 + B * lt])
        else:
            txl.set_data_3d([], [], [])
            tyl.set_data_3d([], [], [])
        sp_ = _ease((i - 40) / 25.0) if okp else 0.0
        if sp_ > 0:
            bx = cache["box"]
            e = min(0.8 * w, 0.5 * (bx[5] - bx[4]) / (abs(A) + abs(B) + 1e-12))
            plane["pc"].set_verts(plane_quad(e, sp_))
            _set_alpha(plane, 0.5, 0.9)
        else:
            _set_alpha(plane, 0.0)
        show1 = i >= 120 and abs(x1 - x0) <= w and abs(y1 - y0) <= w
        dot1.set_data_3d(*(([x1], [y1], [Lv]) if (show1 and okp) else ([], [], [])))
        if i < 14:
            info.set_text(T(f"1) Yüzey z = f(x, y), nokta P{pt}\n   z₀ = {_g(z0, 4)}",
                            f"1) Surface z = f(x, y), point P{pt}\n   z₀ = {_g(z0, 4)}"))
        elif i < 40:
            info.set_text(T(f"2) İki teğet doğru: x-yönünde eğim f_x = {_short(Ae)}\n"
                            f"   y-yönünde eğim f_y = {_short(Be)}",
                            f"2) Two tangent lines: slope f_x = {_short(Ae)} in x,\n"
                            f"   slope f_y = {_short(Be)} in y"))
        elif i < 78:
            info.set_text(T("3) Bu iki doğrunun belirlediği düzlem:\n   P'deki teğet düzlem z = L(x, y)",
                            "3) The plane spanned by both lines:\n   the tangent plane z = L(x, y) at P"))
        elif i < 120:
            info.set_text(T(f"4) Yakınlaştır (pencere ±{_g(w, 2)}):\n   yüzey düzleme yapışır → f ≈ L",
                            f"4) Zoom in (window ±{_g(w, 2)}):\n   the surface hugs the plane → f ≈ L"))
        elif not okp:
            info.set_text(T(f"P{pt} noktasında f_x / f_y tanımsız:\n   teğet düzlem yok",
                            f"f_x / f_y undefined at P{pt}:\n   no tangent plane"))
        else:
            info.set_text(T(f"5) L{p1} = {_g(Lv, 5)}\n   f{p1} = {_g(fv, 5)}\n   fark ≈ {_g(abs(fv - Lv), 2)}",
                            f"5) L{p1} = {_g(Lv, 5)}\n   f{p1} = {_g(fv, 5)}\n   difference ≈ {_g(abs(fv - Lv), 2)}"))
        form.set_text(("L(x, y) = " + _cut(_pp(Lexp), 40)) if (okp and i >= 50) else "")
        return []

    return N, update


def vary(P, rnd):
    x, y = _X, _Y
    if "pi" in str(P.get("f", "")):
        x0, y0 = rnd.choice([2, 3, 4, 5]), rnd.choice([6, 8, 10, 12])
        return {"f": "pi*x**2*y", "x0": x0, "y0": y0, "x1": round(x0 + rnd.choice([0.1, -0.1]), 2),
                "y1": round(y0 + rnd.choice([0.2, -0.2, 0.1]), 2)}
    form = rnd.choice(["bowl", "mixed", "prod"])
    x0, y0 = rnd.choice([1, 2, -1]), rnd.choice([1, 2, -2])
    if form == "bowl":
        f = rnd.choice([1, 2]) * x ** 2 + rnd.choice([1, 3]) * y ** 2
    elif form == "mixed":
        f = x ** 2 + x * y + rnd.choice([1, 2]) * y ** 2
    else:
        f = rnd.choice([1, 2, 3]) * x * y ** 2
    dx, dy = rnd.choice([0.1, -0.1, 0.2]), rnd.choice([0.1, -0.1, -0.2])
    return {"f": sp.sstr(sp.expand(f)), "x0": x0, "y0": y0,
            "x1": round(x0 + dx, 2), "y1": round(y0 + dy, 2)}
''',
}
EXAMPLES += [
    {"id": "calc3-tp-1", "kind": "tangent_plane",
     "title": ("Paraboloide teğet düzlem", "Tangent plane to a paraboloid"),
     "q": ("z = {fx} yüzeyine {pt} noktasında teğet düzlemin denklemini bul ve bu düzlemle f{p1} "
           "değerini yaklaşık hesapla.",
           "Find the tangent plane to z = {fx} at {pt} and use it to approximate f{p1}."),
     "P": {"f": "x**2 + y**2", "x0": 1, "y0": 2, "x1": 1.1, "y1": 1.9}},
    {"id": "calc3-tp-2", "kind": "tangent_plane",
     "title": ("Üstel fonksiyonun doğrusallaştırılması", "Linearizing an exponential function"),
     "q": ("f(x, y) = {fx} fonksiyonunun {pt} noktasındaki doğrusallaştırması L(x, y)'yi bul; "
           "f{p1} için tahmin yap.",
           "Find the linearization L(x, y) of f(x, y) = {fx} at {pt} and estimate f{p1}."),
     "P": {"f": "x*exp(x*y)", "x0": 1, "y0": 0, "x1": 1.1, "y1": -0.1, "r": 1}},
    {"id": "calc3-tp-3", "kind": "tangent_plane", "topics": ["error estimate", "volume", "hacim", "ölçüm hatası"],
     "title": ("Silindir hacminde ölçüm değişimi", "Change in a cylinder's volume"),
     "q": ("Bir silindirin hacmi V = {fx} (x: yarıçap, y: yükseklik, cm). Ölçüler {pt} iken {p1} olursa "
           "hacmi teğet düzlemle (doğrusal yaklaşımla) tahmin et.",
           "A cylinder has volume V = {fx} (x: radius, y: height, in cm). If the measurements change from "
           "{pt} to {p1}, estimate the new volume with the tangent plane (linear approximation)."),
     "P": {"f": "pi*x**2*y", "x0": 3, "y0": 10, "x1": 3.1, "y1": 9.8}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["gradient_contour"] = {
    "course": "calc3",
    "title": ("Gradyan, yönlü türev ve en dik çıkış", "Gradient, directional derivative and steepest ascent"),
    "topics": ["gradient", "gradient vector", "directional derivative", "directional derivatives",
               "steepest ascent", "steepest descent", "gradient descent", "maximum rate of change",
               "level curves", "contour map", "gradyan", "gradyan vektörü", "yönlü türev",
               "en dik çıkış", "en hızlı artış", "en büyük artış hızı", "seviye eğrileri", "kontur haritası"],
    "code": _CORE + _CGRID + r'''
from matplotlib.patches import FancyArrowPatch


def _setup(P):
    f = _parse(P["f"])
    x0, y0 = _exact(P["x0"]), _exact(P["y0"])
    ux, uy = _exact(P.get("ux", 1)), _exact(P.get("uy", 1))
    if ux == 0 and uy == 0:
        ux = sp.Integer(1)
    fx, fy = _simp(sp.diff(f, _X)), _simp(sp.diff(f, _Y))
    sub = {_X: x0, _Y: y0}
    return f, x0, y0, ux, uy, fx, fy, _simp(fx.subs(sub, simultaneous=True)), _simp(fy.subs(sub, simultaneous=True))


def _box(P, x0, y0):
    R = max(3.0, abs(x0) + 1.5, abs(y0) + 1.5)
    a, b = _rng(P, "xmin", "xmax", -R, R)
    c, d = _rng(P, "ymin", "ymax", -R, R)
    return a, b, c, d


def _vec(p, q):
    return f"⟨{_short(p)}, {_short(q)}⟩"


def solve(P):
    f, x0, y0, ux, uy, fx, fy, gx, gy = _setup(P)
    pt = f"({_pp(x0)}, {_pp(y0)})"
    nu = _simp(sp.sqrt(ux ** 2 + uy ** 2))
    u1, u2 = _simp(ux / nu), _simp(uy / nu)
    mag = _simp(sp.sqrt(gx ** 2 + gy ** 2))
    Du = _simp(gx * u1 + gy * u2)
    mags, _ = _eqv(mag)
    Dus, _ = _eqv(Du)
    shx, shy = _shown(fx, x0, y0), _shown(fy, x0, y0)
    sub_line = (f"∇f{pt} = ⟨{shx}, {shy}⟩ = {_vec(gx, gy)}" if shx and shy and len(shx + shy) < 60
                else f"∇f{pt} = {_vec(gx, gy)}")
    c0s, _ = _eqv(f.subs({_X: x0, _Y: y0}, simultaneous=True))
    steps = [
        (f"f(x, y) = {_pp(f)};  ∇f = ⟨f_x, f_y⟩ = ⟨{_pp(fx)}, {_pp(fy)}⟩",
         f"f(x, y) = {_pp(f)};  ∇f = ⟨f_x, f_y⟩ = ⟨{_pp(fx)}, {_pp(fy)}⟩"),
        (sub_line, sub_line),
        (f"|∇f{pt}| = √(({_short(gx)})² + ({_short(gy)})²) {mags}: f bu noktada en hızlı ∇f yönünde artar, "
         "en büyük artış hızı |∇f|",
         f"|∇f{pt}| = √(({_short(gx)})² + ({_short(gy)})²) {mags}: f grows fastest in the direction of ∇f, "
         "at the rate |∇f|"),
        ((f"Birim yön: u = ⟨{_pp(ux)}, {_pp(uy)}⟩ / {_short(nu)} = {_vec(u1, u2)}",
          f"Unit direction: u = ⟨{_pp(ux)}, {_pp(uy)}⟩ / {_short(nu)} = {_vec(u1, u2)}") if nu != 1 else
         (f"u = ⟨{_pp(ux)}, {_pp(uy)}⟩ zaten birim vektör (|u| = 1)",
          f"u = ⟨{_pp(ux)}, {_pp(uy)}⟩ is already a unit vector (|u| = 1)")),
        (f"D_u f{pt} = ∇f·u = ({_short(gx)})({_short(u1)}) + ({_short(gy)})({_short(u2)}) {Dus}",
         f"D_u f{pt} = ∇f·u = ({_short(gx)})({_short(u1)}) + ({_short(gy)})({_short(u2)}) {Dus}"),
        ("D_u f = |∇f|·cos θ (θ: u ile ∇f arasındaki açı) ⇒ θ = 0°: en büyük (|∇f|), θ = 180°: en küçük "
         "(−|∇f|), θ = 90°: 0 (seviye eğrisi boyunca)",
         "D_u f = |∇f|·cos θ (θ: angle between u and ∇f) ⇒ θ = 0°: largest (|∇f|), θ = 180°: smallest "
         "(−|∇f|), θ = 90°: 0 (along the level curve)"),
        (f"∇f, f(x, y) = f{pt} {c0s} seviye eğrisine diktir; eğrinin teğet yönü ⟨{_short(-gy)}, {_short(gx)}⟩. "
         "Noktadan sürekli ∇f yönünde ilerlemek en dik çıkış yolunu verir.",
         f"∇f is perpendicular to the level curve f(x, y) = f{pt} {c0s}; its tangent direction is "
         f"⟨{_short(-gy)}, {_short(gx)}⟩. Moving along ∇f at every step traces the steepest-ascent path."),
    ]
    ans = f"∇f{pt} = {_vec(gx, gy)};  D_u f {Dus};  |∇f| {mags}"
    return {"answer": ans, "steps": steps,
            "fmt": {"fx": _pp(f), "pt": pt, "u": f"⟨{_pp(ux)}, {_pp(uy)}⟩"}}


def _ascent(h, hx, hy, x0, y0, box):
    a, b, c, d = box
    stp = 0.006 * max(b - a, d - c)
    x, y = x0, y0
    fp = float(h(x, y))
    pts = [(x, y)]
    for _ in range(900):
        gx, gy = float(hx(x, y)), float(hy(x, y))
        n = float(np.hypot(gx, gy))
        if not np.isfinite(n) or n < 1e-10:
            break
        xn, yn = x + stp * gx / n, y + stp * gy / n
        if not (a <= xn <= b and c <= yn <= d):
            break
        fn = float(h(xn, yn))
        if not np.isfinite(fn) or fn < fp:
            break
        x, y, fp = xn, yn, fn
        pts.append((x, y))
    return np.array(pts)


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = lambda s_tr, s_en: s_tr if tr else s_en
    f, x0e, y0e, uxe, uye, fx, fy, gxe, gye = _setup(P)
    x0, y0 = float(x0e), float(y0e)
    a, b, c, d = _box(P, x0, y0)
    args = (_X, _Y)
    h, hx, hy = _num(f, args), _num(fx, args), _num(fy, args)
    X, Y, Z = _grid(h, a, b, c, d, 121)
    lo, hi = _zlims(Z)
    Zm = np.ma.masked_invalid(_clipz(Z, lo, hi))
    gx, gy = _cplx(gxe), _cplx(gye)
    gx, gy = (gx if np.isfinite(gx) else 0.0), (gy if np.isfinite(gy) else 0.0)
    G = float(np.hypot(gx, gy))
    ux, uy = float(uxe), float(uye)
    nu = float(np.hypot(ux, uy))
    ux, uy = ux / nu, uy / nu
    thg = float(np.degrees(np.arctan2(gy, gx))) % 360
    thu = float(np.degrees(np.arctan2(uy, ux))) % 360
    Du = gx * ux + gy * uy
    z0 = float(h(x0, y0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.3, 1], left=0.06, right=0.98, top=0.83, bottom=0.1,
                          wspace=0.24)
    ax = fig.add_subplot(gs[0, 0])
    px = fig.add_subplot(gs[0, 1])
    ax.set_xlim(a, b)
    ax.set_ylim(c, d)
    if 0.33 < (d - c) / (b - a) < 3:
        ax.set_aspect("equal", adjustable="box")
    ax.tick_params(labelsize=8)
    lv = [float(v) for v in MaxNLocator(12).tick_values(lo, hi)]
    fills, lines, labs = [], [], []
    try:
        fcols = [colormaps["Blues"](v) for v in np.linspace(0.04, 0.62, max(1, len(lv) - 1))]
        fills = [ax.contourf(X, Y, Zm, levels=lv, colors=fcols, alpha=0.0, zorder=0)]
        cl = ax.contour(X, Y, Zm, levels=lv, colors="#334155", linewidths=0.8, linestyles="solid", zorder=1)
        lines = [cl]
        labs = list(ax.clabel(cl, fmt=lambda val: _g(val, 3), fontsize=7, inline=True))
    except Exception:
        pass
    lvl0 = []
    if np.isfinite(z0) and lo < z0 < hi:
        try:
            lvl0 = [ax.contour(X, Y, Zm, levels=[z0], colors="#111827", linewidths=2.4,
                               linestyles="solid", zorder=4)]
        except Exception:
            lvl0 = []
    nq = 15
    QX, QY = np.meshgrid(np.linspace(a, b, nq + 2)[1:-1], np.linspace(c, d, nq + 2)[1:-1])
    U, V = hx(QX, QY), hy(QX, QY)
    M = np.hypot(U, V)
    good = np.isfinite(M) & (M > 1e-12)
    cell = 0.62 * min((b - a), (d - c)) / (nq + 1)
    U = np.where(good, U / np.where(good, M, 1.0), 0.0) * cell
    V = np.where(good, V / np.where(good, M, 1.0), 0.0) * cell
    Q = ax.quiver(QX, QY, U * 0, V * 0, angles="xy", scale_units="xy", scale=1, color="#1F2937",
                  alpha=0.85, width=0.005, zorder=3, pivot="mid")
    Lg = 0.24 * min(b - a, d - c)
    ga = FancyArrowPatch((x0, y0), (x0 + 1e-9, y0), arrowstyle="-|>", mutation_scale=18, color=RED,
                         lw=2.6, zorder=7)
    ua = FancyArrowPatch((x0, y0), (x0 + 1e-9, y0), arrowstyle="-|>", mutation_scale=16, color=PURPLE,
                         lw=2.4, zorder=8)
    for art in (ga, ua):
        ax.add_patch(art)
        art.set_visible(False)
    proj, = ax.plot([], [], color=GREEN, lw=5, alpha=0.75, solid_capstyle="butt", zorder=6)
    drop, = ax.plot([], [], ":", color=GRAY, lw=1.4, zorder=6)
    dot, = ax.plot([], [], "o", color=RED, ms=8, mec="white", mew=1.2, zorder=9)
    gl = ax.text(0, 0, "", color=RED, fontsize=11, fontweight="bold", zorder=9)
    ul = ax.text(0, 0, "", color=PURPLE, fontsize=11, fontweight="bold", zorder=9)
    path = _ascent(h, hx, hy, x0, y0, (a, b, c, d))
    pl, = ax.plot([], [], color=ORANGE, lw=3, zorder=8)
    pdot, = ax.plot([], [], "o", color=ORANGE, ms=8, mec="white", mew=1.2, zorder=10)
    info = fig.text(0.015, 0.985, "", va="top", fontsize=10, bbox=BOX, zorder=12)
    ax.set_title("f(x, y) = " + _cut(_pp(f), 42), fontsize=10.5)
    th = np.linspace(0, 360, 361)
    Dc = gx * np.cos(np.radians(th)) + gy * np.sin(np.radians(th))
    Gs = G if G > 1e-12 else 1.0
    px.set_xlim(0, 360)
    px.set_ylim(-1.3 * Gs, 1.3 * Gs)
    px.set_xticks([0, 90, 180, 270, 360])
    px.set_xticklabels(["0°", "90°", "180°", "270°", "360°"], fontsize=8)
    px.tick_params(labelsize=8)
    px.grid(alpha=0.3)
    px.axhline(0, color="#9CA3AF", lw=1)
    for sg in (1, -1):
        px.axhline(sg * G, color=RED, lw=1, ls="--", alpha=0.6)
    px.text(4, G + 0.05 * Gs, f"|∇f| = {_g(G, 4)}", color=RED, fontsize=8.5, va="bottom")
    px.text(356, -G - 0.05 * Gs, "−|∇f|", color=RED, fontsize=8.5, va="top", ha="right")
    px.set_xlabel(T("u'nun açısı θ (x ekseninden)", "angle θ of u (from the x-axis)"), fontsize=9)
    px.set_title("D_u f = ∇f · ⟨cos θ, sin θ⟩", fontsize=10.5)
    dcur, = px.plot([], [], color=PURPLE, lw=2.2)
    dmk, = px.plot([], [], "o", color=PURPLE, ms=8, zorder=5)
    gmk, = px.plot([], [], "o", color=RED, ms=7, zorder=5)
    vline, = px.plot([], [], ":", color=PURPLE, lw=1.2)
    dtx = px.text(0.03, 0.04, "", transform=px.transAxes, fontsize=9.5,
                  bbox=dict(boxstyle="round", fc="white", ec=PURPLE, alpha=0.9))
    N = 170
    gvx, gvy = _short(gxe), _short(gye)
    pt = f"({_pp(x0e)}, {_pp(y0e)})"

    def st(i, t0, t1):
        return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))

    def theta(i):
        if i < 50:
            return None
        if i < 110:
            return 360.0 * st(i, 50, 110)
        return thu * _ease((i - 110) / 14.0)

    def update(i):
        al = st(i, 0, 18)
        for cs in fills:
            cs.set_alpha(0.25 + 0.6 * al)
        for cs in lines:
            cs.set_alpha(0.3 + 0.7 * al)
        for t in labs:
            t.set_alpha(0.3 + 0.7 * al)
        for cs in lvl0:
            cs.set_alpha(1.0 if i >= 42 else 0.0)
        s = st(i, 20, 38)
        Q.set_UVC(U * s, V * s)
        Q.set_alpha(0.85 if s > 0 else 0.0)
        on = i >= 40
        dot.set_data(*(([x0], [y0]) if on else ([], [])))
        gr = _ease((i - 40) / 8.0)
        if on and G > 1e-12 and gr > 0:
            tip = (x0 + Lg * gr * gx / G, y0 + Lg * gr * gy / G)
            ga.set_positions((x0, y0), tip)
            ga.set_visible(True)
            gl.set_position((tip[0] + 0.03 * Lg, tip[1] + 0.03 * Lg))
            gl.set_text("∇f" if gr >= 1 else "")
        else:
            ga.set_visible(False)
            gl.set_text("")
        t = theta(i)
        if t is not None and i < 124 + 1000:
            ex, ey = np.cos(np.radians(t)), np.sin(np.radians(t))
            utip = (x0 + Lg * ex, y0 + Lg * ey)
            ua.set_positions((x0, y0), utip)
            ua.set_visible(i < 124)
            ul.set_position((utip[0] + 0.04 * Lg, utip[1] + 0.04 * Lg))
            ul.set_text("u" if i < 124 else "")
            cosv = (gx * ex + gy * ey) / Gs
            if i < 124 and G > 1e-12:
                proj.set_data([x0, x0 + Lg * cosv * ex], [y0, y0 + Lg * cosv * ey])
                tipg = (x0 + Lg * gx / G, y0 + Lg * gy / G)
                drop.set_data([tipg[0], x0 + Lg * cosv * ex], [tipg[1], y0 + Lg * cosv * ey])
            else:
                proj.set_data([], [])
                drop.set_data([], [])
            tm = t % 360 if i >= 110 else t
            if i < 110:
                k = int(round(t))
                dcur.set_data(th[:k + 1], Dc[:k + 1])
            else:
                dcur.set_data(th, Dc)
            dv = gx * ex + gy * ey
            dmk.set_data([tm], [dv])
            vline.set_data([tm, tm], [0, dv])
            if i < 110:
                dtx.set_text(f"θ = {tm:.0f}°:  D_u f = {_g(dv, 3)}")
            else:
                dtx.set_text(T(f"verilen u: θ = {thu:.1f}°\nD_u f = {_g(Du, 4)}",
                               f"given u: θ = {thu:.1f}°\nD_u f = {_g(Du, 4)}"))
        else:
            ua.set_visible(False)
            ul.set_text("")
            proj.set_data([], [])
            drop.set_data([], [])
            dcur.set_data([], [])
            dmk.set_data([], [])
            vline.set_data([], [])
            dtx.set_text("")
        gmk.set_data(*(([thg], [G]) if i >= 110 else ([], [])))
        pp = st(i, 126, 160)
        if pp > 0 and len(path) > 1:
            m = max(2, int(pp * len(path)))
            pl.set_data(path[:m, 0], path[:m, 1])
            pdot.set_data([path[m - 1, 0]], [path[m - 1, 1]])
        else:
            pl.set_data([], [])
            pdot.set_data([], [])
        if i < 20:
            info.set_text(T("1) Kontur haritası: f(x, y) = c eğrileri", "1) Contour map: curves f(x, y) = c"))
        elif i < 40:
            info.set_text(T("2) ∇f her noktada seviye eğrisine dik,\n   f'nin arttığı yönü gösterir",
                            "2) ∇f is perpendicular to the level curves\n   and points uphill"))
        elif i < 50:
            info.set_text(T(f"3) P{pt}: ∇f = ⟨{gvx}, {gvy}⟩\n   |∇f| = {_g(G, 4)}",
                            f"3) P{pt}: ∇f = ⟨{gvx}, {gvy}⟩\n   |∇f| = {_g(G, 4)}"))
        elif i < 110:
            info.set_text(T("4) u'yu döndür: D_u f = ∇f·u = |∇f| cos θ\n   (yeşil: ∇f'nin u üzerindeki izdüşümü)",
                            "4) Rotate u: D_u f = ∇f·u = |∇f| cos θ\n   (green: projection of ∇f onto u)"))
        elif i < 126:
            info.set_text(T(f"5) Verilen yön: D_u f = {_g(Du, 4)}\n   en büyük değer |∇f| = {_g(G, 4)} (u ∥ ∇f)",
                            f"5) Given direction: D_u f = {_g(Du, 4)}\n   largest value |∇f| = {_g(G, 4)} (u ∥ ∇f)"))
        else:
            info.set_text(T(f"6) Hep ∇f yönünde yürü → en dik çıkış yolu\n   ∇f = ⟨{gvx}, {gvy}⟩, D_u f = {_g(Du, 4)}",
                            f"6) Keep walking along ∇f → steepest ascent\n   ∇f = ⟨{gvx}, {gvy}⟩, D_u f = {_g(Du, 4)}"))
        return []

    return N, update


def vary(P, rnd):
    x, y = _X, _Y
    src = str(P.get("f", ""))
    form = rnd.choice(["hill", "prod", "bowl"])
    if "/" in src:
        form = "heat"
    elif _parse(src or "x*y").as_coeff_Add()[0] > 0:
        form = "hill"
    x0, y0 = rnd.choice([-2, -1, 1, 2]), rnd.choice([-2, -1, 1, 2])
    ux, uy = rnd.choice([(3, 4), (4, 3), (-3, 4), (1, 0), (0, 1), (1, 1), (-1, 2), (5, 12)])
    if P.get("ux", 1) == 0 or P.get("uy", 1) == 0:
        ux, uy = P.get("ux", 1), P.get("uy", 0)
    if form == "heat":
        C = rnd.choice([50, 100, 200])
        return {"f": f"{C}/(1 + x**2 + y**2)", "x0": x0, "y0": y0, "ux": ux, "uy": uy}
    if form == "hill":
        k = rnd.choice([1, 2, 3])
        f = rnd.choice([10, 12, 16]) - x ** 2 - k * y ** 2
    elif form == "prod":
        f = x ** 2 * y + rnd.choice([1, 2, -1]) * y
    else:
        f = x ** 2 + rnd.choice([2, 3, 4]) * y ** 2
    return {"f": sp.sstr(sp.expand(f)), "x0": x0, "y0": y0, "ux": ux, "uy": uy}
''',
}
EXAMPLES += [
    {"id": "calc3-grad-1", "kind": "gradient_contour",
     "title": ("Gradyan ve yönlü türev", "Gradient and directional derivative"),
     "q": ("f(x, y) = {fx} için ∇f'yi bul; {pt} noktasında u = {u} yönündeki yönlü türevi hesapla. "
           "f bu noktada en hızlı hangi yönde artar?",
           "For f(x, y) = {fx}, find ∇f and the directional derivative at {pt} in the direction "
           "u = {u}. In which direction does f increase fastest there?"),
     "P": {"f": "x**2*y", "x0": 1, "y0": 2, "ux": 3, "uy": 4}},
    {"id": "calc3-grad-2", "kind": "gradient_contour", "topics": ["hiking", "mountain", "dağ", "tırmanış"],
     "title": ("Dağcı ve en dik çıkış", "A hiker and the steepest climb"),
     "q": ("Bir dağın yüksekliği h(x, y) = {fx} (yüz metre). {pt} noktasındaki dağcı kuzeye, yani "
           "u = {u} yönüne yürürse yükseklik hangi hızla değişir? En dik çıkış yönü nedir?",
           "The height of a mountain is h(x, y) = {fx} (hundreds of metres). A hiker at {pt} walks "
           "north, u = {u}. How fast does the height change? Which way is the steepest climb?"),
     "P": {"f": "12 - x**2 - 2*y**2", "x0": 2, "y0": 1, "ux": 0, "uy": 1}},
    {"id": "calc3-grad-3", "kind": "gradient_contour", "topics": ["temperature", "heat", "sıcaklık"],
     "title": ("Sıcaklık alanında yönlü türev", "Directional derivative in a temperature field"),
     "q": ("Bir levhanın sıcaklığı T(x, y) = {fx}. {pt} noktasında u = {u} yönünde sıcaklık hangi hızla "
           "değişir? Isınmak isteyen bir böcek hangi yöne gitmeli?",
           "A plate's temperature is T(x, y) = {fx}. At {pt}, how fast does the temperature change in "
           "the direction u = {u}? Which way should a bug that wants to warm up go?"),
     "P": {"f": "100/(1 + x**2 + y**2)", "x0": 1, "y0": 2, "ux": -1, "uy": 0}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["double_integral"] = {
    "course": "calc3",
    "title": ("Çift katlı integral: yüzey altındaki hacim", "Double integral: volume under a surface"),
    "topics": ["double integral", "double integrals", "iterated integral", "iterated integrals",
               "fubini", "volume under a surface", "riemann sum in two variables", "midpoint rule",
               "integrals over rectangles", "average value of a function of two variables",
               "çift katlı integral", "iki katlı integral", "ardışık integral", "yinelemeli integral",
               "yüzey altındaki hacim", "dikdörtgen bölge", "hacim"],
    "code": _CORE + _CGRID + _C3D + r'''

_NS = [1, 2, 3, 4, 6, 8, 12, 16]


def _setup(P):
    f = _parse(P["f"])
    a, b, c, d = (_exact(P[k]) for k in ("a", "b", "c", "d"))
    if float(b) < float(a):
        a, b = b, a
    if float(d) < float(c):
        c, d = d, c
    order = str(P.get("order", "dxdy")).lower().replace(" ", "")
    return f, a, b, c, d, ("dydx" if order == "dydx" else "dxdy")


def _mid(h, a, b, c, d, n):
    dx, dy = (b - a) / n, (d - c) / n
    xm = a + dx * (np.arange(n) + 0.5)
    ym = c + dy * (np.arange(n) + 0.5)
    XM, YM = np.meshgrid(xm, ym)
    H = h(XM, YM)
    return XM, YM, np.where(np.isfinite(H), H, 0.0), dx, dy


def _lim(v):
    s = _pp(v)
    return s if len(s) == 1 or (s.lstrip("-").isdigit()) else "(" + s + ")"


def _solve0(P):
    f, a, b, c, d, order = _setup(P)
    h = _num(f, (_X, _Y))
    fa, fb, fc, fd = float(a), float(b), float(c), float(d)
    sums = {n: float(_mid(h, fa, fb, fc, fd, n)[2].sum() * (fb - fa) * (fd - fc) / n ** 2) for n in (2, 4, 8, 16)}
    vnum = float(_mid(h, fa, fb, fc, fd, 400)[2].sum() * (fb - fa) * (fd - fc) / 400 ** 2)
    if order == "dxdy":
        iv, ov, ia, ib, oa, ob = _X, _Y, a, b, c, d
    else:
        iv, ov, ia, ib, oa, ob = _Y, _X, c, d, a, b
    g, V = None, None
    try:
        if sp.count_ops(f) <= 60:
            g = sp.integrate(f, (iv, ia, ib))
            if g.has(sp.Integral):
                raise ValueError("inner")
            g = _simp(g)
            V = sp.integrate(g, (ov, oa, ob))
            if V.has(sp.Integral):
                raise ValueError("outer")
            V = _simp(V)
    except Exception:
        g, V = None, None
    Rs = f"[{_pp(a)}, {_pp(b)}] × [{_pp(c)}, {_pp(d)}]"
    iname, oname = sp.sstr(iv), sp.sstr(ov)
    keep = ("y", "x") if order == "dxdy" else ("x", "y")
    steps = [
        (f"R = {Rs};  V = ∬_R f(x, y) dA,  f(x, y) = {_pp(f)}",
         f"R = {Rs};  V = ∬_R f(x, y) dA,  f(x, y) = {_pp(f)}"),
        (f"Fubini: V = ∫_{_lim(oa)}^{_lim(ob)} ( ∫_{_lim(ia)}^{_lim(ib)} f(x, y) d{iname} ) d{oname}",
         f"Fubini: V = ∫_{_lim(oa)}^{_lim(ob)} ( ∫_{_lim(ia)}^{_lim(ib)} f(x, y) d{iname} ) d{oname}"),
    ]
    if V is not None:
        Vs, Vf = _eqv(V)
        steps += [
            (f"İç integral ({keep[0]} sabit): ∫_{_lim(ia)}^{_lim(ib)} ({_pp(f)}) d{iname} = {_pp(g)}",
             f"Inner integral ({keep[0]} held fixed): ∫_{_lim(ia)}^{_lim(ib)} ({_pp(f)}) d{iname} = {_pp(g)}"),
            (f"Dış integral: ∫_{_lim(oa)}^{_lim(ob)} ({_pp(g)}) d{oname} {Vs}",
             f"Outer integral: ∫_{_lim(oa)}^{_lim(ob)} ({_pp(g)}) d{oname} {Vs}"),
        ]
    else:
        Vs, Vf = "≈ " + _g(vnum, 6), vnum
        steps.append(("Kapalı biçimli ilkel bulunamadı; integral sayısal olarak (400×400 orta nokta) hesaplandı: V "
                      + Vs, "No closed-form antiderivative; the integral was computed numerically "
                      "(400×400 midpoint): V " + Vs))
    ms = ", ".join(f"{n}×{n}: {_g(v, 5)}" for n, v in sums.items())
    steps.append((f"Kontrol – orta nokta Riemann toplamları Σ f(xᵢ*, yⱼ*)·ΔA: {ms} → V",
                  f"Check – midpoint Riemann sums Σ f(xᵢ*, yⱼ*)·ΔA: {ms} → V"))
    if all(abs(v - Vf) < 1e-9 * (1 + abs(Vf)) for v in sums.values()):
        steps.append(("f doğrusal olduğundan orta nokta toplamı her ızgarada tam sonucu verir.",
                      "Because f is linear, the midpoint sum is exact on every grid."))
    area = (b - a) * (d - c)
    avs, _ = _eqv(V / area) if V is not None else ("≈ " + _g(vnum / float(area), 5), 0)
    steps.append((f"Alan(R) = {_pp(area)};  ortalama değer f_ort = V / Alan {avs}",
                  f"Area(R) = {_pp(area)};  average value f_avg = V / Area {avs}"))
    X, Y = np.meshgrid(np.linspace(fa, fb, 81), np.linspace(fc, fd, 81))
    Z = h(X, Y)
    if np.nanmin(np.where(np.isfinite(Z), Z, 0.0)) < -1e-12:
        steps.append(("Not: f < 0 olan yerler hacme negatif katkı verir (işaretli/net hacim).",
                      "Note: where f < 0 the contribution is negative (signed / net volume)."))
    return {"answer": f"V {Vs}", "steps": steps,
            "fmt": {"fx": _pp(f), "R": Rs, "V": Vs}}


def solve(P):
    return _cached("solve", P, _solve0)


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = lambda s_tr, s_en: s_tr if tr else s_en
    f, ae, be, ce, de, order = _setup(P)
    a, b, c, d = float(ae), float(be), float(ce), float(de)
    h = _num(f, (_X, _Y))
    sol = solve(P)
    X, Y, Z = _grid(h, a, b, c, d, 30)
    lo, hi = _zlims(Z)
    lo, hi = min(lo, 0.0), max(hi, 0.0)
    span = hi - lo
    box = (a, b, c, d, lo - 0.02 * span, hi + 0.08 * span)
    Zc = _clipz(Z, lo, hi)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1], left=0.0, right=0.975, top=0.86, bottom=0.12,
                          wspace=0.22)
    ax = fig.add_subplot(gs[0, 0], projection="3d")
    px = fig.add_subplot(gs[0, 1])
    _style3d(ax, box)
    surf = _surface(ax, X, Y, Zc, "viridis", lo, hi, box, alpha=0.25, zorder=4, c0=0.2, c1=0.95)
    base = _line3(ax, PURPLE, 2.0, zorder=0.5)
    base.set_data_3d([a, b, b, a, a], [c, c, d, d, c], [0] * 5)
    walls = []
    for xs_, ys_, zw in (((a, b), (c, c), 5), ((b, b), (c, d), 5), ((a, b), (d, d), 0.8), ((a, a), (c, d), 0.8)):
        tt = np.linspace(0, 1, 30)
        wx = xs_[0] + (xs_[1] - xs_[0]) * tt
        wy = ys_[0] + (ys_[1] - ys_[0]) * tt
        wz = np.clip(np.where(np.isfinite(h(wx, wy)), h(wx, wy), 0.0), lo, hi)
        verts = [[(wx[k], wy[k], 0.0), (wx[k + 1], wy[k + 1], 0.0), (wx[k + 1], wy[k + 1], wz[k + 1]),
                  (wx[k], wy[k], wz[k])] for k in range(29)]
        walls.append((_poly(ax, verts, "#93C5FD", zw, 0.0), 0.35 if zw > 1 else 0.6))
    approx = []
    for n in _NS:
        _, _, H, dx, dy = _mid(h, a, b, c, d, n)
        approx.append(float(H.sum() * dx * dy))
    Vf = None
    for tok in sol["answer"].replace("V", "").replace("=", " ").replace("≈", " ").split():
        try:
            Vf = float(tok)
        except ValueError:
            continue
    if Vf is None:
        Vf = float(_mid(h, a, b, c, d, 400)[2].sum() * (b - a) * (d - c) / 400 ** 2)
    ks = np.arange(len(_NS))
    px.set_xlim(-0.5, len(_NS) - 0.5)
    allv = approx + [Vf]
    vlo, vhi = min(allv), max(allv)
    pad = 0.15 * (vhi - vlo) + 0.05 * abs(Vf) + 1e-6
    px.set_ylim(vlo - pad, vhi + pad)
    px.set_xticks(ks)
    px.set_xticklabels([f"{n}×{n}" for n in _NS], fontsize=7.5, rotation=45)
    px.tick_params(labelsize=8)
    px.grid(alpha=0.3)
    px.axhline(Vf, color=GREEN, lw=2, ls="--")
    px.text(-0.35, Vf + 0.02 * (vhi - vlo + pad), "V " + sol["fmt"]["V"], color=GREEN, fontsize=9,
            ha="left", va="bottom", fontweight="bold")
    px.set_title(T("Orta nokta toplamı → tam değer", "Midpoint sum → exact value"), fontsize=10)
    px.set_xlabel(T("kutu ızgarası", "grid of boxes"), fontsize=9)
    seq, = px.plot([], [], "-o", color=BLUE, ms=6, lw=1.6)
    cur, = px.plot([], [], "o", color=ORANGE, ms=11, mec="white", mew=1.5, zorder=5)
    info = fig.text(0.015, 0.985, "", va="top", fontsize=10, bbox=BOX)
    ax.set_title("f(x, y) = " + _cut(_pp(f), 40) + f",  R = [{_g(a)}, {_g(b)}] × [{_g(c)}, {_g(d)}]",
                 fontsize=10, y=1.0)
    cache = {"key": None, "art": None}
    cmap = colormaps["Blues"]
    N0, per = 10, 14
    N = N0 + per * len(_NS) + 30

    def bars(k):
        if cache["key"] == k:
            return
        if cache["art"] is not None:
            cache["art"].remove()
            cache["art"] = None
        cache["key"] = k
        if k is None:
            return
        n = _NS[k]
        XM, YM, H, dx, dy = _mid(h, a, b, c, d, n)
        Hc = np.clip(H.ravel(), lo, hi)
        cols = [cmap(0.25 + 0.3 * min(1.0, abs(v) / (abs(hi) + abs(lo) + 1e-12))) if v >= 0 else
                (0.98, 0.6, 0.55, 1.0) for v in Hc]
        gap = 0.06 if n <= 8 else 0.0
        art = ax.bar3d((XM - dx / 2).ravel() + gap * dx / 2, (YM - dy / 2).ravel() + gap * dy / 2,
                       np.zeros(n * n), dx * (1 - gap), dy * (1 - gap), Hc, color=cols, shade=True,
                       edgecolor=(0.1, 0.15, 0.3, 0.35), linewidth=0.3, zorder=2)
        cache["art"] = art

    def update(i):
        ax.view_init(elev=26, azim=-58 + 28 * np.sin(np.pi * i / (N - 1)))
        k = min(len(_NS) - 1, (i - N0) // per) if i >= N0 else None
        final = i >= N0 + per * len(_NS)
        bars(None if final else k)
        _set_alpha(surf, 0.9 if final else 0.22, 0.9 if final else 0.35)
        for w, wa in walls:
            _set_alpha(w, wa if final else 0.0)
        if k is not None:
            kk = k if not final else len(_NS) - 1
            seq.set_data(ks[:kk + 1], approx[:kk + 1])
            cur.set_data([ks[kk]], [approx[kk]])
        else:
            seq.set_data([], [])
            cur.set_data([], [])
        if k is None:
            info.set_text(T("1) R tabanı üzerindeki yüzey z = f(x, y): altındaki hacim V = ∬_R f dA",
                            "1) The surface z = f(x, y) over the base R: the volume below is V = ∬_R f dA"))
        elif not final:
            n = _NS[k]
            dA = (b - a) * (d - c) / n ** 2
            info.set_text(T(f"2) {n}×{n} = {n * n} kutu, ΔA = {_g(dA, 3)}, yükseklik = f(orta nokta)\n"
                            f"   Σ f(xᵢ*, yⱼ*)·ΔA = {_g(approx[k], 5)}   (tam değer {_g(Vf, 5)})",
                            f"2) {n}×{n} = {n * n} boxes, ΔA = {_g(dA, 3)}, height = f(midpoint)\n"
                            f"   Σ f(xᵢ*, yⱼ*)·ΔA = {_g(approx[k], 5)}   (exact {_g(Vf, 5)})"))
        else:
            info.set_text(T(f"3) Kutular inceldikçe toplam ardışık integrale yakınsar:\n   V {sol['fmt']['V']}",
                            f"3) As the boxes shrink the sum converges to the iterated integral:\n   V {sol['fmt']['V']}"))
        return []

    return N, update


def vary(P, rnd):
    x, y = _X, _Y
    src = _parse(P.get("f", "x*y"))
    if src.has(sp.exp):
        return {"f": "x*exp(x*y)", "a": 0, "b": rnd.choice([1, 2]), "c": 0, "d": rnd.choice([1, 2]),
                "order": P.get("order", "dydx")}
    if src.is_polynomial(x, y) and sp.Poly(src, x, y).total_degree() == 1:
        b, d = rnd.choice([8, 10, 12, 20]), rnd.choice([4, 5, 6, 10])
        p, q = rnd.choice([4, 5, 10]), rnd.choice([5, 10, 20])
        return {"f": f"1 + x/{p} + y/{q}", "a": 0, "b": b, "c": 0, "d": d}
    form = rnd.choice(["poly", "plane", "prod"])
    a, c = 0, 0
    b, d = rnd.choice([1, 2, 3]), rnd.choice([1, 2, 3])
    if form == "poly":
        f = rnd.choice([1, 2]) * x ** 2 + rnd.choice([1, 3]) * y ** 2 + rnd.choice([0, 1, 2])
    elif form == "plane":
        p, q = rnd.choice([1, 2]), rnd.choice([1, 2, 3])
        f = p * b + q * d + 2 - p * x - q * y
    else:
        f = rnd.choice([1, 2, 3, 6]) * x * y + rnd.choice([1, 2])
    return {"f": sp.sstr(f), "a": a, "b": b, "c": c, "d": d}
''',
}
EXAMPLES += [
    {"id": "calc3-dint-1", "kind": "double_integral",
     "title": ("Dikdörtgen üzerinde çift katlı integral", "Double integral over a rectangle"),
     "q": ("∬_R ({fx}) dA integralini R = {R} için ardışık integral olarak hesapla.",
           "Evaluate ∬_R ({fx}) dA over R = {R} as an iterated integral."),
     "P": {"f": "x**2 + y**2", "a": 0, "b": 2, "c": 0, "d": 1}},
    {"id": "calc3-dint-2", "kind": "double_integral", "topics": ["pool", "water volume", "havuz", "su hacmi"],
     "title": ("Havuzdaki su hacmi", "Water in a swimming pool"),
     "q": ("Bir havuzun tabanı R = {R} (metre) dikdörtgenidir; (x, y) noktasındaki derinlik "
           "d(x, y) = {fx} metredir. Havuz ağzına kadar doluysa içinde kaç m³ su vardır?",
           "A swimming pool covers the rectangle R = {R} (metres) and its depth at (x, y) is "
           "d(x, y) = {fx} metres. How many cubic metres of water does the full pool hold?"),
     "P": {"f": "1 + x/5 + y/10", "a": 0, "b": 10, "c": 0, "d": 5}},
    {"id": "calc3-dint-3", "kind": "double_integral", "topics": ["order of integration", "integrasyon sırası"],
     "title": ("Uygun integrasyon sırası", "Choosing the order of integration"),
     "q": ("∬_R {fx} dA integralini R = {R} üzerinde hesapla (önce y'ye göre integral almak işi kolaylaştırır).",
           "Evaluate ∬_R {fx} dA over R = {R} (integrating with respect to y first makes it easy)."),
     "P": {"f": "x*exp(x*y)", "a": 0, "b": 1, "c": 0, "d": 1, "order": "dydx"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["vector_field"] = {
    "course": "calc3",
    "title": ("Vektör alanı: akış, diverjans ve rotasyonel", "Vector field: flow, divergence and curl"),
    "topics": ["vector field", "vector fields", "divergence", "curl", "flow lines", "streamlines",
               "conservative vector field", "potential function", "gradient field", "source and sink",
               "irrotational", "incompressible", "vektör alanı", "vektör alanları", "diverjans",
               "rotasyonel", "dönel", "akış çizgileri", "korunumlu alan", "potansiyel fonksiyonu",
               "kaynak", "kuyu"],
    "code": _CORE + r'''
from matplotlib.collections import LineCollection


def _setup(P):
    Fp, Fq = _parse(P["P"]), _parse(P["Q"])
    x0, y0 = _exact(P.get("x0", 1)), _exact(P.get("y0", 1))
    return Fp, Fq, x0, y0


def _parts(Fp, Fq):
    px, qy = _simp(sp.diff(Fp, _X)), _simp(sp.diff(Fq, _Y))
    qx, py = _simp(sp.diff(Fq, _X)), _simp(sp.diff(Fp, _Y))
    return px, qy, qx, py, _simp(px + qy), _simp(qx - py)


def _sign_txt(v, kind):
    if not np.isfinite(v):
        return ("tanımsız", "undefined")
    if kind == "div":
        if v > 1e-12:
            return ("kaynak: akış dışarı yayılır", "source: the flow spreads out")
        if v < -1e-12:
            return ("kuyu: akış içeri toplanır", "sink: the flow converges")
        return ("sıkıştırılamaz: alan korunur", "incompressible: area is preserved")
    if v > 1e-12:
        return ("saat yönünün tersine dönme", "counter-clockwise spin")
    if v < -1e-12:
        return ("saat yönünde dönme", "clockwise spin")
    return ("dönmesiz (irrotasyonel)", "irrotational (no spin)")


def solve(P):
    Fp, Fq, x0, y0 = _setup(P)
    px, qy, qx, py, div, curl = _parts(Fp, Fq)
    pt = f"({_pp(x0)}, {_pp(y0)})"
    sub = {_X: x0, _Y: y0}
    dvs, dv = _eqv(div.subs(sub, simultaneous=True))
    cvs, cv = _eqv(curl.subs(sub, simultaneous=True))
    sd, sc_ = _sign_txt(dv, "div"), _sign_txt(cv, "curl")
    F = f"⟨{_pp(Fp)}, {_pp(Fq)}⟩"
    steps = [
        (f"F(x, y) = ⟨P, Q⟩ = {F}", f"F(x, y) = ⟨P, Q⟩ = {F}"),
        (f"∂P/∂x = {_pp(px)},  ∂Q/∂y = {_pp(qy)}  ⇒  div F = ∂P/∂x + ∂Q/∂y = {_pp(div)}",
         f"∂P/∂x = {_pp(px)},  ∂Q/∂y = {_pp(qy)}  ⇒  div F = ∂P/∂x + ∂Q/∂y = {_pp(div)}"),
        (f"∂Q/∂x = {_pp(qx)},  ∂P/∂y = {_pp(py)}  ⇒  curl F = (∂Q/∂x − ∂P/∂y) k = ({_pp(curl)}) k",
         f"∂Q/∂x = {_pp(qx)},  ∂P/∂y = {_pp(py)}  ⇒  curl F = (∂Q/∂x − ∂P/∂y) k = ({_pp(curl)}) k"),
        (f"{pt} noktasında: div F {dvs} ⇒ {sd[0]}", f"At {pt}: div F {dvs} ⇒ {sd[1]}"),
        ((f"{pt} noktasında: curl F {cvs} ⇒ {sc_[0]}; buraya konan küçük bir çark ω = curl/2 açısal "
          "hızıyla döner",
          f"At {pt}: curl F {cvs} ⇒ {sc_[1]}; a small paddle wheel placed here spins at ω = curl/2")
         if np.isfinite(cv) and abs(cv) > 1e-12 else
         (f"{pt} noktasında: curl F {cvs} ⇒ {sc_[0]}; küçük bir çark burada dönmez",
          f"At {pt}: curl F {cvs} ⇒ {sc_[1]}; a small paddle wheel here does not spin")),
    ]
    if curl == 0:
        phi = None
        try:
            p1 = sp.integrate(Fp, _X)
            gp = _simp(Fq - sp.diff(p1, _Y))
            if not gp.has(_X) and not p1.has(sp.Integral):
                phi = _simp(p1 + sp.integrate(gp, _Y))
        except Exception:
            phi = None
        if phi is not None and not phi.has(sp.Integral):
            steps.append((f"curl F ≡ 0 ⇒ F korunumlu: φ = ∫P dx + g(y) ⇒ φ(x, y) = {_pp(phi)} (+ C), ∇φ = F",
                          f"curl F ≡ 0 ⇒ F is conservative: φ = ∫P dx + g(y) ⇒ φ(x, y) = {_pp(phi)} (+ C), ∇φ = F"))
        else:
            steps.append(("curl F ≡ 0 ⇒ F (basit bağlantılı bölgede) korunumludur.",
                          "curl F ≡ 0 ⇒ F is conservative (on a simply connected region)."))
    else:
        steps.append(("curl F ≢ 0 ⇒ F korunumlu değil (potansiyel fonksiyonu yoktur).",
                      "curl F ≢ 0 ⇒ F is not conservative (no potential function)."))
    ans = f"div F = {_pp(div)},  curl F = {_pp(curl)}"
    if div.free_symbols or curl.free_symbols:
        ans += f";  {pt}: div {dvs}, curl {cvs}"
    return {"answer": ans, "steps": steps, "fmt": {"F": F, "pt": pt}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = lambda s_tr, s_en: s_tr if tr else s_en
    Fp, Fq, x0e, y0e = _setup(P)
    x0, y0 = float(x0e), float(y0e)
    px_, qy_, qx_, py_, div, curl = _parts(Fp, Fq)
    args = (_X, _Y)
    fP, fQ = _num(Fp, args), _num(Fq, args)
    fD, fC = _num(div, args), _num(curl, args)
    L = abs(_fl(P.get("L", 3))) or 3.0
    L = max(L, abs(x0) + 0.8, abs(y0) + 0.8)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.6, 1], left=0.06, right=0.98, top=0.85, bottom=0.08,
                          wspace=0.18, hspace=0.38)
    ax = fig.add_subplot(gs[:, 0])
    pd_ = fig.add_subplot(gs[0, 1])
    pc_ = fig.add_subplot(gs[1, 1])
    for a_ in (ax, pd_, pc_):
        a_.set_xlim(-L, L)
        a_.set_ylim(-L, L)
        a_.set_aspect("equal", adjustable="box")
        a_.tick_params(labelsize=7.5)
    ax.grid(alpha=0.25)
    nq = 17
    QX, QY = np.meshgrid(np.linspace(-L, L, nq + 2)[1:-1], np.linspace(-L, L, nq + 2)[1:-1])
    U, V = fP(QX, QY), fQ(QX, QY)
    M = np.hypot(U, V)
    good = np.isfinite(M) & (M > 1e-12)
    cell = 0.8 * 2 * L / (nq + 1)
    Un = np.where(good, U / np.where(good, M, 1.0), 0.0) * cell
    Vn = np.where(good, V / np.where(good, M, 1.0), 0.0) * cell
    Mf = np.where(good, M, 0.0)
    Cm = np.log1p(Mf / (np.median(Mf[good]) if good.any() else 1.0))
    Q = ax.quiver(QX, QY, Un * 0, Vn * 0, Cm, cmap="viridis", angles="xy", scale_units="xy", scale=1,
                  width=0.0045, pivot="mid", zorder=2, alpha=0.9)
    Q.set_clim(0.0, float(Cm.max()) * 1.3 + 1e-9)
    # particles (pre-computed, seek-safe)
    rng = np.random.default_rng(int(P.get("seed", 0)))
    Mp, N, start, life = 70, 150, 18, 46
    K = N - start
    GX, GY = np.meshgrid(np.linspace(-L, L, 41), np.linspace(-L, L, 41))
    sp_all = np.hypot(fP(GX, GY), fQ(GX, GY))
    fs_ = sp_all[np.isfinite(sp_all)]
    Fs = float(np.percentile(fs_, 75)) if fs_.size and np.percentile(fs_, 75) > 1e-9 else 1.0
    dt = 2 * L / 75.0

    def vel(p):
        u, v = fP(p[:, 0], p[:, 1]) / Fs, fQ(p[:, 0], p[:, 1]) / Fs
        sp_ = np.hypot(u, v)
        cap = np.where(sp_ > 2.5, 2.5 / np.where(sp_ > 0, sp_, 1.0), 1.0)
        return np.stack([u * cap, v * cap], axis=1)

    pos = np.zeros((K, Mp, 2))
    born = np.zeros((K, Mp), dtype=int)
    p = rng.uniform(-L, L, size=(Mp, 2))
    age = rng.integers(0, life, size=Mp)
    b = np.zeros(Mp, dtype=int)
    for k in range(K):
        pos[k] = p
        born[k] = b
        for _ in range(2):
            h2 = dt / 2
            k1 = vel(p)
            k2 = vel(p + 0.5 * h2 * k1)
            k3 = vel(p + 0.5 * h2 * k2)
            k4 = vel(p + h2 * k3)
            p = p + h2 * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        age = age + 1
        bad = (~np.isfinite(p).all(axis=1)) | (np.abs(p) > L).any(axis=1) | (age >= life)
        if bad.any():
            p[bad] = rng.uniform(-L, L, size=(int(bad.sum()), 2))
            age[bad] = 0
            b[bad] = k + 1
    tail = 6
    trails = LineCollection([], linewidths=1.6, zorder=4)
    ax.add_collection(trails)
    heads, = ax.plot([], [], "o", color=ORANGE, ms=4.2, mec="#9A3412", mew=0.5, zorder=5)
    # paddle wheel at (x0, y0)
    c0 = float(fC(x0, y0))
    om = (c0 if np.isfinite(c0) else 0.0) / 2 * dt / Fs * 2
    rw = 0.11 * L
    wheel, = ax.plot([], [], color=PURPLE, lw=2.4, zorder=7, solid_capstyle="round")
    ring, = ax.plot([], [], color=PURPLE, lw=1.2, zorder=7)
    pdot, = ax.plot([], [], "o", color=PURPLE, ms=6, zorder=8)
    tt = np.linspace(0, 2 * np.pi, 60)
    info = fig.text(0.015, 0.985, "", va="top", fontsize=10, bbox=BOX)
    F = f"⟨{_pp(Fp)}, {_pp(Fq)}⟩"
    ax.set_title("F(x, y) = " + _cut(F, 44), fontsize=10.5)
    # divergence / curl maps
    G = 81
    HX, HY = np.meshgrid(np.linspace(-L, L, G), np.linspace(-L, L, G))
    imgs = []
    for pan, fn, nm, expr in ((pd_, fD, "div F", div), (pc_, fC, "curl F", curl)):
        Dm = fn(HX, HY)
        fin = Dm[np.isfinite(Dm)]
        vmax = 1.6 * float(np.percentile(np.abs(fin), 98)) if fin.size else 1.0
        vmax = vmax if vmax > 1e-9 else 1.0
        im = pan.imshow(np.ma.masked_invalid(Dm), extent=(-L, L, -L, L), origin="lower", cmap="RdBu_r",
                        vmin=-vmax, vmax=vmax, alpha=0.0, interpolation="bilinear")
        mk, = pan.plot([], [], "o", color="#111827", ms=5)
        ttl = pan.set_title("", fontsize=9.5)
        const = "" if expr.free_symbols else T(f"her yerde {_pp(expr)}", f"{_pp(expr)} everywhere")
        ct = pan.text(0.5, 0.5, "", transform=pan.transAxes, ha="center", va="center", fontsize=10,
                      fontweight="bold", color="#111827",
                      bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.85))
        imgs.append((im, mk, ttl, nm + " = " + _cut(_pp(expr), 22), ct, const))
    d0 = float(fD(x0, y0))
    sd, sc_ = _sign_txt(d0, "div"), _sign_txt(c0, "curl")
    pt = f"({_pp(x0e)}, {_pp(y0e)})"

    def st(i, t0, t1):
        return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))

    def update(i):
        s = 0.2 + 0.8 * _ease(st(i, 0, 16))
        Q.set_UVC(Un * s, Vn * s, Cm)
        Q.set_alpha(0.9 if s > 0 else 0.0)
        if i >= start:
            k = i - start
            P_ = pos[k]
            heads.set_data(P_[:, 0], P_[:, 1])
            segs, cols = [], []
            for j in range(1, tail + 1):
                if k - j < 0:
                    break
                okj = born[k] <= k - j
                for m in np.nonzero(okj)[0]:
                    segs.append([pos[k - j, m], pos[k - j + 1, m]])
                    cols.append((0.85, 0.4, 0.12, 0.95 * (1 - (j - 1) / (tail + 1))))
            trails.set_segments(segs)
            trails.set_color(cols if cols else [(0, 0, 0, 0)])
        else:
            heads.set_data([], [])
            trails.set_segments([])
        for k_, (im, mk, ttl, label, ct, const) in enumerate(imgs):
            t0 = 45 if k_ == 0 else 90
            al = 0.85 * st(i, t0, t0 + 10)
            im.set_alpha(al)
            mk.set_data(*(([x0], [y0]) if al > 0 else ([], [])))
            ttl.set_text(label if al > 0 else "")
            ct.set_text(const if al > 0 else "")
        if i >= 90:
            ang = om * (i - 90)
            xs, ys = [], []
            for q in range(4):
                th = ang + q * np.pi / 2
                xs += [x0, x0 + rw * np.cos(th), np.nan]
                ys += [y0, y0 + rw * np.sin(th), np.nan]
            wheel.set_data(xs, ys)
            ring.set_data(x0 + rw * np.cos(tt), y0 + rw * np.sin(tt))
            pdot.set_data([x0], [y0])
        else:
            wheel.set_data([], [])
            ring.set_data([], [])
            pdot.set_data(*(([x0], [y0]) if i >= 45 else ([], [])))
        if i < start:
            info.set_text(T(f"1) Vektör alanı F = {_cut(F, 40)}: her noktada bir ok (yön; renk = büyüklük)",
                            f"1) Vector field F = {_cut(F, 40)}: an arrow at every point (direction; colour = size)"))
        elif i < 45:
            info.set_text(T("2) Parçacıklar alanı izler: akış çizgileri (hız = F)",
                            "2) Particles follow the field: flow lines (velocity = F)"))
        elif i < 90:
            info.set_text(T(f"3) div F = ∂P/∂x + ∂Q/∂y = {_cut(_pp(div), 26)}\n   {pt}: div = {_g(d0, 4)} ⇒ {sd[0]}",
                            f"3) div F = ∂P/∂x + ∂Q/∂y = {_cut(_pp(div), 26)}\n   {pt}: div = {_g(d0, 4)} ⇒ {sd[1]}"))
        elif i < 136:
            info.set_text(T(f"4) curl F = ∂Q/∂x − ∂P/∂y = {_cut(_pp(curl), 26)}\n   {pt}: curl = {_g(c0, 4)} ⇒ {sc_[0]} (mor çark)",
                            f"4) curl F = ∂Q/∂x − ∂P/∂y = {_cut(_pp(curl), 26)}\n   {pt}: curl = {_g(c0, 4)} ⇒ {sc_[1]} (purple wheel)"))
        else:
            info.set_text(T(f"Sonuç: div F = {_cut(_pp(div), 24)},  curl F = {_cut(_pp(curl), 24)}\n"
                            f"   {pt}: div = {_g(d0, 4)}, curl = {_g(c0, 4)}",
                            f"Result: div F = {_cut(_pp(div), 24)},  curl F = {_cut(_pp(curl), 24)}\n"
                            f"   {pt}: div = {_g(d0, 4)}, curl = {_g(c0, 4)}"))
        return []

    return N, update


def vary(P, rnd):
    x, y = _X, _Y
    form = rnd.choice(["rot", "grad", "spiral", "shear"])
    k = rnd.choice([1, 2, 3])
    try:
        d0 = _parts(_parse(P["P"]), _parse(P["Q"]))
        dv, cv = d0[4], d0[5]
        if cv == 0:
            form = "grad"
        elif dv == 0:
            form = "rot"
        elif not dv.free_symbols and not cv.free_symbols:
            s = rnd.choice([1, 2, 3])
            sg = -1 if dv < 0 else 1
            return {"P": sp.sstr(sg * x / (2 * s) - k * y), "Q": sp.sstr(k * x + sg * y / (2 * s)),
                    "x0": rnd.choice([1, -1, 2]), "y0": rnd.choice([1, 2, -1])}
    except Exception:
        pass
    if form == "rot":
        Fp, Fq = -k * y, k * x
    elif form == "grad":
        Fp, Fq = 2 * x * y, x ** 2 + rnd.choice([0, 1, 2]) * y
    elif form == "spiral":
        s = rnd.choice([-1, 1])
        Fp, Fq = s * x - k * y, k * x + s * y
    else:
        Fp, Fq = y, rnd.choice([0, 1, -1]) * x
    return {"P": sp.sstr(Fp), "Q": sp.sstr(Fq), "x0": rnd.choice([1, -1, 2]), "y0": rnd.choice([1, 2, -1])}
''',
}
EXAMPLES += [
    {"id": "calc3-vf-1", "kind": "vector_field",
     "title": ("Dönme alanı", "A rotation field"),
     "q": ("F(x, y) = {F} vektör alanını çiz; div F ve curl F'yi hesapla ve {pt} noktasında yorumla.",
           "Sketch the vector field F(x, y) = {F}; compute div F and curl F and interpret them at {pt}."),
     "P": {"P": "-y", "Q": "x", "x0": 1, "y0": 1}},
    {"id": "calc3-vf-2", "kind": "vector_field", "topics": ["gradient field", "potential", "gradyan alanı"],
     "title": ("Korunumlu alan ve potansiyel", "Conservative field and its potential"),
     "q": ("F(x, y) = {F} alanının diverjansını ve rotasyonelini bul. F korunumlu mu? Öyleyse bir "
           "potansiyel fonksiyonu φ bul.",
           "Find the divergence and the curl of F(x, y) = {F}. Is F conservative? If so, find a "
           "potential function φ."),
     "P": {"P": "2*x*y", "Q": "x**2", "x0": 1, "y0": 1}},
    {"id": "calc3-vf-3", "kind": "vector_field", "topics": ["whirlpool", "fluid flow", "girdap", "akışkan"],
     "title": ("Girdaptaki su akışı", "Water flow in a whirlpool"),
     "q": ("Bir girdapta yüzeydeki suyun hızı F(x, y) = {F} ile modelleniyor. div F ve curl F'yi hesapla: "
           "su merkeze mi toplanıyor, hangi yönde dönüyor?",
           "The surface velocity of water in a whirlpool is modelled by F(x, y) = {F}. Compute div F and "
           "curl F: is the water drawn to the centre, and which way does it spin?"),
     "P": {"P": "-y - x/4", "Q": "x - y/4", "x0": 1, "y0": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["space_curve"] = {
    "course": "calc3",
    "title": ("Uzay eğrisi, hız vektörü ve yay uzunluğu", "Space curve, velocity vector and arc length"),
    "topics": ["space curve", "space curves", "vector function", "vector-valued function",
               "vector valued functions", "parametric curve in space", "helix", "arc length",
               "tangent vector", "unit tangent vector", "velocity vector", "derivative of a vector function",
               "uzay eğrisi", "vektör değerli fonksiyon", "vektör fonksiyon", "helis", "sarmal",
               "yay uzunluğu", "teğet vektör", "birim teğet vektör", "hız vektörü"],
    "code": _CORE + _CGRID + _C3D + r'''


def _setup(P):
    r = [_parse(P[k], (_T,)) for k in ("x", "y", "z")]
    t0, t1 = _exact(P.get("t0", 0)), _exact(P.get("t1", 1))
    if float(t1) < float(t0):
        t0, t1 = t1, t0
    if float(t1) - float(t0) < 1e-9:
        t1 = t0 + 1
    return r, t0, t1


def _speed(r):
    d = [_simp(sp.diff(e, _T)) for e in r]
    sq = _simp(sp.expand(sum(e ** 2 for e in d)))
    try:
        spd = _simp(sp.sqrt(sp.factor(sq)))
    except Exception:
        spd = sp.sqrt(sq)
    return d, sq, spd


def _iv(t0, t1):
    return f"[{_pp(t0)}, {_pp(t1)}]"


def _solve0(P):
    r, t0, t1 = _setup(P)
    d, sq, spd = _speed(r)
    hs = _num(spd, (_T,))
    ts = np.linspace(float(t0), float(t1), 4001)
    vs = hs(ts)
    defined = bool(np.all(np.isfinite(vs)))
    vs = np.where(np.isfinite(vs), vs, 0.0)
    Lnum = float(np.sum((vs[1:] + vs[:-1]) / 2) * (ts[1] - ts[0])) if defined else float("nan")
    Lx = None
    easy = defined and sp.count_ops(spd) <= 40
    for q in sp.preorder_traversal(spd):
        if isinstance(q, sp.Pow) and q.has(_T) and not q.exp.is_Integer:
            if not (q.base.is_polynomial(_T) and sp.degree(q.base, _T) <= 2):
                easy = False
    try:
        if easy:
            Lx = sp.integrate(spd, (_T, t0, t1))
            if Lx.has(sp.Integral):
                Lx = None
            else:
                Lx = _simp(Lx)
                if abs(_cplx(Lx) - Lnum) > 1e-4 * (1 + abs(Lnum)):
                    Lx = None
    except Exception:
        Lx = None
    Ls = _eqv(Lx)[0] if Lx is not None else ("≈ " + _g(Lnum, 6) if defined else "= ? (tanımsız / undefined)")
    rv = f"⟨{_pp(r[0])}, {_pp(r[1])}, {_pp(r[2])}⟩"
    dv = f"⟨{_pp(d[0])}, {_pp(d[1])}, {_pp(d[2])}⟩"
    sqs = " + ".join(f"({_pp(e)})²" for e in d)
    rad = "√" + _pp(sq) if _pp(sq).isdigit() else "√(" + _pp(sq) + ")"
    ig = _pp(spd)
    ig = f"({ig})" if (" + " in ig or " - " in ig) else ig
    T0 = [_simp(e.subs(_T, t0)) for e in d]
    s0 = _simp(spd.subs(_T, t0))
    steps = [
        (f"r(t) = {rv},  t ∈ {_iv(t0, t1)}", f"r(t) = {rv},  t ∈ {_iv(t0, t1)}"),
        (f"Hız (teğet) vektörü: r'(t) = {dv}", f"Velocity (tangent) vector: r'(t) = {dv}"),
        (f"Hız büyüklüğü: |r'(t)| = √({_cut(sqs, 70)}) = {rad} = {_pp(spd)}",
         f"Speed: |r'(t)| = √({_cut(sqs, 70)}) = {rad} = {_pp(spd)}"),
        (f"Yay uzunluğu: L = ∫_{_pp(t0)}^{_pp(t1)} |r'(t)| dt = ∫_{_pp(t0)}^{_pp(t1)} {ig} dt {Ls}",
         f"Arc length: L = ∫_{_pp(t0)}^{_pp(t1)} |r'(t)| dt = ∫_{_pp(t0)}^{_pp(t1)} {ig} dt {Ls}"),
    ]
    if _cplx(s0) > 1e-12:
        Tv = ", ".join(_short(_simp(e / s0)) for e in T0)
        steps.append((f"t = {_pp(t0)} anında: r'({_pp(t0)}) = ⟨{', '.join(_short(e) for e in T0)}⟩, birim teğet "
                      f"T = r'/|r'| = ⟨{Tv}⟩",
                      f"At t = {_pp(t0)}: r'({_pp(t0)}) = ⟨{', '.join(_short(e) for e in T0)}⟩, unit tangent "
                      f"T = r'/|r'| = ⟨{Tv}⟩"))
    steps.append(("Yorum: L, hız eğrisi |r'(t)| altında kalan alandır (sağdaki grafik).",
                  "Meaning: L is the area under the speed graph |r'(t)| (right-hand plot)."))
    return {"answer": f"L {Ls}", "steps": steps,
            "fmt": {"r": rv, "I": _iv(t0, t1), "L": Ls}}


def solve(P):
    return _cached("solve", P, _solve0)


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = lambda s_tr, s_en: s_tr if tr else s_en
    r, t0e, t1e = _setup(P)
    d, sq, spd = _speed(r)
    t0, t1 = float(t0e), float(t1e)
    ts = np.linspace(t0, t1, 401)
    R = np.stack([_num(e, (_T,))(ts) for e in r], axis=1)
    D = np.stack([_num(e, (_T,))(ts) for e in d], axis=1)
    ok = np.isfinite(R).all(axis=1)
    R = np.where(np.isfinite(R), R, np.nan)
    D = np.where(np.isfinite(D), D, 0.0)
    S = np.linalg.norm(D, axis=1)
    cum = np.concatenate([[0.0], np.cumsum((S[1:] + S[:-1]) / 2 * np.diff(ts))])
    lo_, hi_ = [], []
    for k in range(3):
        col = R[ok, k] if ok.any() else np.array([-1.0, 1.0])
        a_, b_ = float(np.min(col)), float(np.max(col))
        if b_ - a_ < 1e-6:
            a_, b_ = a_ - 1.0, b_ + 1.0
        pad = 0.12 * (b_ - a_)
        lo_.append(a_ - pad)
        hi_.append(b_ + pad)
    box = (lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2])
    sc = _sc(box)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1], left=0.0, right=0.975, top=0.84, bottom=0.12,
                          wspace=0.2)
    ax = fig.add_subplot(gs[0, 0], projection="3d")
    px = fig.add_subplot(gs[0, 1])
    _style3d(ax, box)
    ghost = _line3(ax, "#9CA3AF", 1.2, ls="--", zorder=1)
    ghost.set_data_3d(R[:, 0], R[:, 1], R[:, 2])
    shadow = _line3(ax, "#CBD5E1", 1.6, zorder=0.5)
    curve = _line3(ax, BLUE, 2.8, zorder=3)
    dot = _line3(ax, RED, 0, zorder=8, marker="o", ms=8, mec="white", mew=1.2)
    vel = _arrow3(ax, ORANGE, 2.6, zorder=7)
    smax = float(np.max(S)) if np.max(S) > 0 else 1.0
    kv = 0.28 / smax
    info = fig.text(0.015, 0.985, "", va="top", fontsize=10, bbox=BOX)
    rv = f"r(t) = ⟨{_pp(r[0])}, {_pp(r[1])}, {_pp(r[2])}⟩"
    ax.set_title(_cut(rv, 52), fontsize=10, y=1.0)
    px.set_xlim(t0, t1)
    px.set_ylim(0, 1.25 * smax)
    px.grid(alpha=0.3)
    px.tick_params(labelsize=8)
    px.set_xlabel("t", fontsize=9)
    px.set_title(T("Hız |r'(t)|: altındaki alan = yay uzunluğu", "Speed |r'(t)|: area below = arc length"),
                 fontsize=9.5)
    px.plot(ts, S, color=PURPLE, lw=2.2)
    from matplotlib.patches import Polygon
    area = Polygon([[t0, 0], [t0, 0]], closed=True, fc=PURPLE, alpha=0.22, ec="none")
    px.add_patch(area)
    cur, = px.plot([], [], "o", color=RED, ms=7, zorder=5)
    vl, = px.plot([], [], ":", color=RED, lw=1.2)
    stx = px.text(0.04, 0.95, "", transform=px.transAxes, va="top", fontsize=10,
                  bbox=dict(boxstyle="round", fc="white", ec=PURPLE, alpha=0.9))
    sol = solve(P)
    ig = _pp(spd)
    ig = f"({ig})" if (" + " in ig or " - " in ig) else ig
    N = 160

    def update(i):
        ax.view_init(elev=24, azim=-60 + 36 * np.sin(np.pi * i / (N - 1)))
        p = min(1.0, max(0.0, (i - 12) / 118.0))
        k = int(round(p * (len(ts) - 1)))
        if i < 12:
            k = 0
        curve.set_data_3d(R[:k + 1, 0], R[:k + 1, 1], R[:k + 1, 2])
        shadow.set_data_3d(R[:k + 1, 0], R[:k + 1, 1], np.full(k + 1, box[4]))
        pr = R[k]
        if np.isfinite(pr).all():
            dot.set_data_3d([pr[0]], [pr[1]], [pr[2]])
            vel(pr, pr + kv * D[k] * sc, sc) if i < 132 else vel(None, None, sc)
        else:
            dot.set_data_3d([], [], [])
            vel(None, None, sc)
        poly = np.concatenate([[[ts[0], 0.0]], np.stack([ts[:k + 1], S[:k + 1]], axis=1), [[ts[k], 0.0]]])
        area.set_xy(poly)
        cur.set_data([ts[k]], [S[k]])
        vl.set_data([ts[k], ts[k]], [0, S[k]])
        stx.set_text(f"s({_g(ts[k], 3)}) = {_g(cum[k], 4)}" if i < 132 else "L " + sol["fmt"]["L"])
        if i < 12:
            info.set_text(T(f"1) {_cut(rv, 60)},  t ∈ {sol['fmt']['I']}",
                            f"1) {_cut(rv, 60)},  t ∈ {sol['fmt']['I']}"))
        elif i < 132:
            vv = ", ".join(_g(v, 3) for v in D[k])
            info.set_text(T(f"2) t = {_g(ts[k], 3)}:  r'(t) = ⟨{vv}⟩ (turuncu: hız vektörü, eğriye teğet)\n"
                            f"   |r'(t)| = {_g(S[k], 4)},  katedilen yol s = ∫|r'| dt = {_g(cum[k], 4)}",
                            f"2) t = {_g(ts[k], 3)}:  r'(t) = ⟨{vv}⟩ (orange: velocity, tangent to the curve)\n"
                            f"   |r'(t)| = {_g(S[k], 4)},  distance so far s = ∫|r'| dt = {_g(cum[k], 4)}"))
        else:
            info.set_text(T(f"3) Yay uzunluğu L = ∫ |r'(t)| dt = ∫ {_cut(ig, 26)} dt\n   L {sol['fmt']['L']}",
                            f"3) Arc length L = ∫ |r'(t)| dt = ∫ {_cut(ig, 26)} dt\n   L {sol['fmt']['L']}"))
        return []

    return N, update


def vary(P, rnd):
    src = " ".join(str(P.get(k, "")) for k in ("x", "y", "z"))
    form = "helix" if ("cos" in src or "sin" in src) else ("cubic" if "**" in src else "line")
    t = _T
    if form == "helix":
        a, b = rnd.choice([(3, 4), (4, 3), (1, 1), (5, 12), (2, 1)])
        k = rnd.choice([1, 2])
        return {"x": sp.sstr(a * sp.cos(t)), "y": sp.sstr(a * sp.sin(t)), "z": sp.sstr(b * t), "t0": 0,
                "t1": sp.sstr(k * sp.pi)}
    if form == "cubic":
        c = rnd.choice([1, 2, 3])
        return {"x": "t", "y": sp.sstr(c * t ** 2), "z": sp.sstr(sp.Rational(2 * c * c, 3) * t ** 3), "t0": 0,
                "t1": rnd.choice([1, 2, 3])}
    p, q, s = rnd.choice([(1, 2, 2), (2, 3, 6), (2, 6, 9), (4, 4, 7)])
    return {"x": sp.sstr(p * t + 1), "y": sp.sstr(q * t), "z": sp.sstr(s * t - 2), "t0": 0,
            "t1": rnd.choice([1, 2, 3])}
''',
}
EXAMPLES += [
    {"id": "calc3-curve-1", "kind": "space_curve",
     "title": ("Helisin yay uzunluğu", "Arc length of a helix"),
     "q": ("r(t) = {r} helisinin t ∈ {I} aralığındaki yay uzunluğunu bul; hız vektörünü yorumla.",
           "Find the arc length of the helix r(t) = {r} for t ∈ {I}, and interpret its velocity vector."),
     "P": {"x": "cos(t)", "y": "sin(t)", "z": "t/4", "t0": 0, "t1": "2*pi"}},
    {"id": "calc3-curve-2", "kind": "space_curve", "topics": ["twisted cubic", "bükülmüş kübik"],
     "title": ("Tam kare çıkan hız: kübik eğri", "A perfect-square speed: a cubic curve"),
     "q": ("r(t) = {r} eğrisi için r'(t), |r'(t)| ve t ∈ {I} aralığındaki yay uzunluğunu hesapla.",
           "For r(t) = {r}, compute r'(t), |r'(t)| and the arc length over t ∈ {I}."),
     "P": {"x": "t", "y": "t**2", "z": "2*t**3/3", "t0": 0, "t1": 1}},
    {"id": "calc3-curve-3", "kind": "space_curve", "topics": ["spiral staircase", "handrail", "döner merdiven"],
     "title": ("Döner merdivenin korkuluğu", "Handrail of a spiral staircase"),
     "q": ("Döner bir merdivenin korkuluğu r(t) = {r} (metre), t ∈ {I} ile veriliyor. Korkuluk kaç metre "
           "uzunluğundadır?",
           "The handrail of a spiral staircase follows r(t) = {r} (metres), t ∈ {I}. How long is the "
           "handrail?"),
     "P": {"x": "3*cos(t)", "y": "3*sin(t)", "z": "4*t", "t0": 0, "t1": "2*pi"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["lagrange"] = {
    "course": "calc3",
    "title": ("Lagrange çarpanları: çember üzerinde ekstremum", "Lagrange multipliers: extrema on a circle"),
    "topics": ["lagrange multiplier", "lagrange multipliers", "constrained optimization",
               "optimization with constraints", "extrema with a constraint", "absolute extrema",
               "lagrange", "lagrange çarpanları", "kısıtlı optimizasyon", "kısıtlı ekstremum",
               "koşullu ekstremum", "mutlak ekstremum"],
    "code": _CORE + r'''
from matplotlib.patches import FancyArrowPatch


def _setup(P):
    a, b, r = _exact(P["a"]), _exact(P["b"]), _exact(P["r"])
    r = abs(r)
    if r == 0:
        r = sp.Integer(1)
    return a, b, r


def _fstr(a, b):
    return _pp(a * _X + b * _Y)


def _solve0(P):
    a, b, r = _setup(P)
    fs, r2 = _fstr(a, b), _pp(r ** 2)
    if a == 0 and b == 0:
        return {"answer": ("f sabit (0): her nokta hem maks hem min", "f is constant (0): every point is both max and min"),
                "steps": [(f"f(x, y) = 0 sabit fonksiyon", "f(x, y) = 0 is constant"),
                          ("∇f = 0 olduğundan λ = 0; çember üzerindeki her nokta ekstremumdur.",
                           "∇f = 0 so λ = 0; every point on the circle is an extremum.")],
                "fmt": {"fx": "0", "g": f"x² + y² = {r2}"}}
    s = _simp(sp.sqrt(a ** 2 + b ** 2))
    lam = _simp(s / (2 * r))
    xm, ym, fm = _simp(a * r / s), _simp(b * r / s), _simp(r * s)
    P1 = f"({_short(xm)}, {_short(ym)})"
    P2 = f"({_short(-xm)}, {_short(-ym)})"
    fms, _ = _eqv(fm)
    steps = [
        (f"Amaç: f(x, y) = {fs};  kısıt: g(x, y) = x² + y² = {r2}",
         f"Objective: f(x, y) = {fs};  constraint: g(x, y) = x² + y² = {r2}"),
        (f"∇f = ⟨{_pp(a)}, {_pp(b)}⟩,  ∇g = ⟨2x, 2y⟩", f"∇f = ⟨{_pp(a)}, {_pp(b)}⟩,  ∇g = ⟨2x, 2y⟩"),
        (f"∇f = λ∇g ⇒ {_pp(a)} = 2λx,  {_pp(b)} = 2λy ⇒ x = {_pp(a)}/(2λ), y = {_pp(b)}/(2λ)",
         f"∇f = λ∇g ⇒ {_pp(a)} = 2λx,  {_pp(b)} = 2λy ⇒ x = {_pp(a)}/(2λ), y = {_pp(b)}/(2λ)"),
        (f"Kısıta koy: ({_pp(a ** 2)} + {_pp(b ** 2)})/(4λ²) = {r2} ⇒ λ² = {_pp(_simp(lam ** 2))} ⇒ λ = ±{_short(lam)}",
         f"Plug into the constraint: ({_pp(a ** 2)} + {_pp(b ** 2)})/(4λ²) = {r2} ⇒ λ² = {_pp(_simp(lam ** 2))} "
         f"⇒ λ = ±{_short(lam)}"),
        (f"λ = {_short(lam)} ⇒ {P1}, f = {_short(fm)};   λ = −{_short(lam)} ⇒ {P2}, f = {_short(-fm)}",
         f"λ = {_short(lam)} ⇒ {P1}, f = {_short(fm)};   λ = −{_short(lam)} ⇒ {P2}, f = {_short(-fm)}"),
        ("Geometri: f = c seviye doğruları çembere teğet olduğunda (∇f ∥ ∇g) c en büyük / en küçük değerini alır.",
         "Geometry: c is largest / smallest exactly when the level line f = c is tangent to the circle (∇f ∥ ∇g)."),
        (f"Çember kapalı ve sınırlı ⇒ ekstremumlar vardır: {P1} noktasında maks f {fms};  {P2} noktasında "
         f"min f = {_short(-fm)}",
         f"The circle is closed and bounded ⇒ extrema exist: max f {fms} at {P1};  min f = {_short(-fm)} at {P2}"),
    ]
    ans = (f"{P1} noktasında maks f = {_short(fm)};  {P2} noktasında min f = {_short(-fm)}",
           f"max f = {_short(fm)} at {P1};  min f = {_short(-fm)} at {P2}")
    return {"answer": ans, "steps": steps, "fmt": {"fx": fs, "g": f"x² + y² = {r2}"}}


def solve(P):
    return _cached("solve", P, _solve0)


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = lambda s_tr, s_en: s_tr if tr else s_en
    ae, be, re_ = _setup(P)
    a, b, r = float(ae), float(be), float(re_)
    s = float(np.hypot(a, b))
    M = r * s
    deg = s < 1e-12
    ua, ub = (a / s, b / s) if not deg else (1.0, 0.0)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1], left=0.06, right=0.98, top=0.83, bottom=0.11,
                          wspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    px = fig.add_subplot(gs[0, 1])
    W = 1.6 * r
    ax.set_xlim(-W, W)
    ax.set_ylim(-W, W)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#9CA3AF", lw=1)
    ax.axvline(0, color="#9CA3AF", lw=1)
    ax.tick_params(labelsize=8)
    tt = np.linspace(0, 2 * np.pi, 361)
    circ, = ax.plot([], [], color="#111827", lw=2.4, zorder=4)
    fam = []
    for cv in np.linspace(-1.5 * M, 1.5 * M, 13) if not deg else []:
        c0 = np.array([ua, ub]) * cv / s
        e = np.array([-ub, ua]) * 3 * W
        ln, = ax.plot([c0[0] - e[0], c0[0] + e[0]], [c0[1] - e[1], c0[1] + e[1]], color=GRAY, lw=0.8,
                      alpha=0.0, zorder=1)
        fam.append(ln)
    lvl, = ax.plot([], [], color=ORANGE, lw=2.6, zorder=5)
    hits, = ax.plot([], [], "o", color=ORANGE, ms=8, mec="white", mew=1.2, zorder=7)
    pmin, = ax.plot([], [], "o", color=BLUE, ms=10, mec="white", mew=1.4, zorder=8)
    pmax, = ax.plot([], [], "o", color=RED, ms=10, mec="white", mew=1.4, zorder=8)
    lmin = ax.text(0, 0, "", color=BLUE, fontsize=9.5, fontweight="bold", zorder=9, ha="center",
                   bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=BLUE, alpha=0.85))
    lmax = ax.text(0, 0, "", color=RED, fontsize=9.5, fontweight="bold", zorder=9, ha="center",
                   bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=RED, alpha=0.85))
    arrows = []
    for k_, col in enumerate((RED, GREEN, RED, GREEN)):
        ar = FancyArrowPatch((0, 0), (1e-9, 0), arrowstyle="-|>", mutation_scale=15, color=col,
                             lw=3.2 if k_ % 2 == 0 else 2.2, zorder=10 + k_ % 2)
        ar.set_visible(False)
        ax.add_patch(ar)
        arrows.append(ar)
    alab = [ax.text(0, 0, "", color=c, fontsize=10, fontweight="bold", zorder=10) for c in (RED, GREEN, RED, GREEN)]
    ctx = ax.text(0.98, 0.02, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=10, color=ORANGE,
                  fontweight="bold", bbox=dict(boxstyle="round", fc="white", ec=ORANGE, alpha=0.9), zorder=11)
    sol = solve(P)
    ax.set_title(T(f"f = {sol['fmt']['fx']},  kısıt {sol['fmt']['g']}", f"f = {sol['fmt']['fx']},  constraint {sol['fmt']['g']}"),
                 fontsize=10)
    info = fig.text(0.015, 0.985, "", va="top", fontsize=10, bbox=BOX)
    th = np.degrees(tt)
    Fth = r * (a * np.cos(tt) + b * np.sin(tt))
    Ms = M if M > 1e-12 else 1.0
    px.set_xlim(0, 360)
    px.set_ylim(-1.55 * Ms, 1.55 * Ms)
    px.set_xticks([0, 90, 180, 270, 360])
    px.set_xticklabels(["0°", "90°", "180°", "270°", "360°"], fontsize=8)
    px.tick_params(labelsize=8)
    px.grid(alpha=0.3)
    px.plot(th, Fth, color="#111827", lw=2.2)
    px.set_xlabel(T("çember üzerindeki açı θ  (x = r cos θ, y = r sin θ)", "angle θ on the circle  (x = r cos θ, y = r sin θ)"),
                  fontsize=8.5)
    px.set_title(T("Çember boyunca f(θ) ve c seviyesi", "f along the circle and the level c"), fontsize=10)
    hl, = px.plot([], [], color=ORANGE, lw=2.2)
    hh, = px.plot([], [], "o", color=ORANGE, ms=7, zorder=5)
    mm, = px.plot([], [], "o", color=BLUE, ms=9, zorder=6)
    MM, = px.plot([], [], "o", color=RED, ms=9, zorder=6)
    fmx = _simp(re_ * sp.sqrt(ae ** 2 + be ** 2))
    fmS = (_short(fmx), _short(-fmx))
    thM = float(np.degrees(np.arctan2(ub, ua))) % 360
    thm = (thM + 180) % 360
    pM = np.array([ua, ub]) * r
    N = 150

    def cval(i):
        if i < 15:
            return None
        if i < 35:
            return -1.45 * M + 0.45 * M * _ease((i - 15) / 20.0)
        if i < 55:
            return -M
        if i < 95:
            return -M + 2 * M * _ease((i - 55) / 40.0)
        return M

    perp = np.array([-ub, ua])

    def put_arrows(k, p, sgn):
        tip_f = p + np.array([ua, ub]) * 0.6 * r
        tip_g = p + p / r * 0.36 * r
        arrows[2 * k].set_positions(tuple(p), tuple(tip_f))
        arrows[2 * k + 1].set_positions(tuple(p), tuple(tip_g))
        arrows[2 * k].set_visible(True)
        arrows[2 * k + 1].set_visible(True)
        q = tip_f + perp * 0.13 * r
        alab[2 * k].set_position((q[0], q[1]))
        alab[2 * k].set_text("∇f")
        q = tip_g - perp * 0.22 * r
        alab[2 * k + 1].set_position((q[0], q[1]))
        alab[2 * k + 1].set_text("∇g")

    def update(i):
        m = int(min(1.0, 0.15 + i / 14.0) * (len(tt) - 1))
        circ.set_data(r * np.cos(tt[:m + 1]), r * np.sin(tt[:m + 1]))
        for ln in fam:
            ln.set_alpha(0.35 if i >= 15 else 0.0)
        c = None if deg else cval(i)
        if c is not None:
            c0 = np.array([ua, ub]) * c / s
            e = np.array([-ub, ua]) * 3 * W
            lvl.set_data([c0[0] - e[0], c0[0] + e[0]], [c0[1] - e[1], c0[1] + e[1]])
            dd = c / s
            if abs(dd) <= r + 1e-9:
                hw = np.sqrt(max(r * r - dd * dd, 0.0))
                p1 = c0 + np.array([-ub, ua]) * hw
                p2 = c0 - np.array([-ub, ua]) * hw
                hits.set_data([p1[0], p2[0]], [p1[1], p2[1]])
                angs = [float(np.degrees(np.arctan2(q[1], q[0]))) % 360 for q in (p1, p2)]
                hh.set_data(angs, [c, c])
            else:
                hits.set_data([], [])
                hh.set_data([], [])
            hl.set_data([0, 360], [c, c])
            ctx.set_text(f"c = {_g(c, 3)}")
        else:
            lvl.set_data([], [])
            hits.set_data([], [])
            hl.set_data([], [])
            hh.set_data([], [])
            ctx.set_text("")
        show_min, show_max = (i >= 35 and not deg), (i >= 95 and not deg)
        pmin.set_data(*(([-pM[0]], [-pM[1]]) if show_min else ([], [])))
        pmax.set_data(*(([pM[0]], [pM[1]]) if show_max else ([], [])))
        mm.set_data(*(([thm], [-M]) if show_min else ([], [])))
        MM.set_data(*(([thM], [M]) if show_max else ([], [])))
        for ar in arrows:
            ar.set_visible(False)
        for t in alab:
            t.set_text("")
        if 35 <= i < 55 and not deg:
            put_arrows(0, -pM, -1)
        if 95 <= i < 122 and not deg:
            put_arrows(1, pM, 1)
        lmin.set_text(f"min {fmS[1]}" if show_min else "")
        lmin.set_position((-pM[0] * 0.55 - perp[0] * 0.45 * r, -pM[1] * 0.55 - perp[1] * 0.45 * r))
        lmax.set_text(T("maks ", "max ") + fmS[0] if show_max else "")
        lmax.set_position((pM[0] * 0.55 - perp[0] * 0.45 * r, pM[1] * 0.55 - perp[1] * 0.45 * r))
        if i < 15:
            info.set_text(T(f"1) Kısıt: {sol['fmt']['g']} (çember). Amaç: f(x, y) = {sol['fmt']['fx']}",
                            f"1) Constraint: {sol['fmt']['g']} (a circle). Objective: f(x, y) = {sol['fmt']['fx']}"))
        elif i < 35:
            info.set_text(T("2) f = c seviye doğrularını kaydır: çemberi kestikleri sürece c değeri çember üzerinde alınır",
                            "2) Slide the level lines f = c: as long as they meet the circle, the value c is attained"))
        elif i < 55:
            info.set_text(T(f"3) İlk temas: doğru çembere teğet ⇒ ∇f ∥ ∇g (zıt yönlü, λ < 0)\n   min f = {fmS[1]}",
                            f"3) First touch: the line is tangent ⇒ ∇f ∥ ∇g (opposite, λ < 0)\n   min f = {fmS[1]}"))
        elif i < 95:
            info.set_text(T("4) Aradaki her c için doğru çemberi iki noktada keser (sağda iki turuncu nokta)",
                            "4) For every c in between the line cuts the circle twice (two orange dots on the right)"))
        elif i < 122:
            info.set_text(T(f"5) Son temas: yine teğet ⇒ ∇f = λ∇g (aynı yön, λ > 0)\n   maks f = {fmS[0]}",
                            f"5) Last touch: tangent again ⇒ ∇f = λ∇g (same direction, λ > 0)\n   max f = {fmS[0]}"))
        else:
            ans = sol["answer"][0 if tr else 1] if isinstance(sol["answer"], tuple) else sol["answer"]
            info.set_text(T("Sonuç: ", "Result: ") + ans)
        return []

    return N, update


def vary(P, rnd):
    a, b = rnd.choice([(3, 4), (4, 3), (5, 12), (12, 5), (6, 8), (8, 15), (1, 1), (1, 2)])
    a, b = a * rnd.choice([1, -1]), b * rnd.choice([1, -1])
    return {"a": a, "b": b, "r": rnd.choice([1, 2, 3, 4, 5])}
''',
}
EXAMPLES += [
    {"id": "calc3-lag-1", "kind": "lagrange",
     "title": ("Çember üzerinde doğrusal fonksiyonun ekstremumları", "Extrema of a linear function on a circle"),
     "q": ("Lagrange çarpanları yöntemiyle f(x, y) = {fx} fonksiyonunun {g} çemberi üzerindeki en büyük ve "
           "en küçük değerlerini bul.",
           "Use Lagrange multipliers to find the maximum and minimum values of f(x, y) = {fx} on the circle {g}."),
     "P": {"a": 3, "b": 4, "r": 2}},
    {"id": "calc3-lag-2", "kind": "lagrange",
     "title": ("Köklü sonuç çıkan kısıtlı ekstremum", "A constrained extremum with a radical answer"),
     "q": ("{g} kısıtı altında f(x, y) = {fx} ifadesinin ekstremum değerlerini ve alındıkları noktaları bul.",
           "Subject to {g}, find the extreme values of f(x, y) = {fx} and where they occur."),
     "P": {"a": 1, "b": 1, "r": 2}},
    {"id": "calc3-lag-3", "kind": "lagrange", "topics": ["signal strength", "robot", "sinyal"],
     "title": ("Çembersel raydaki robot", "A robot on a circular track"),
     "q": ("Bir robot, merkezi şarj istasyonu olan {g} (metre) çembersel rayında hareket ediyor. Ölçülen "
           "sinyal gücü S(x, y) = {fx}. Sinyal en güçlü ve en zayıf nerede olur?",
           "A robot moves on the circular track {g} (metres) centred at its charging station. The measured "
           "signal strength is S(x, y) = {fx}. Where is the signal strongest and weakest?"),
     "P": {"a": 5, "b": 12, "r": 13}},
]
