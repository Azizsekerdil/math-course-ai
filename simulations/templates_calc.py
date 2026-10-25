# -*- coding: utf-8 -*-
"""Kalkülüs 1 simülasyonları: limit, türev (kesenden teğete), belirli integral
(işaretli alan), ekstremumlar, Riemann toplamları, optimizasyon (açık kutu),
ilişkili oranlar (kayan merdiven), Newton yöntemi, ortalama değer teoremi.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Sorular kurs
kitaplarından KOPYALANMAZ: kendi ifademizle yazılmış, sayıları değiştirilmiş
tipik ders örnekleridir.

`limit_expr`, `derivative_expr` ve `integral_expr` PDF tarayıcısından gelen
rastgele fonksiyonlarla da çalışır (sympy dizesi, x değişkeni). Bu yüzden
ayrıştırma, sayısal değerlendirme (nan / karmaşık / tanımsız noktalar) ve
sympy'nin kapalı form bulamadığı durumlar için sayısal yedekler ortak
yardımcı kodda (_COMMON) toplanmıştır; _COMMON her kaynağın başına eklenir,
böylece her kaynak yine tek başına çalışır (düzenleyicide ve bağımsız
betikte de).
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
# Ortak yardımcılar (sympy tabanlı türler için)
# ──────────────────────────────────────────────────────────────────────────
_COMMON = r'''
import math
import numpy as np
import sympy as sp
from matplotlib.mathtext import MathTextParser

BLUE, ORANGE, GREEN, RED, PURPLE, GRAY = ("#2563EB", "#E07B39", "#16A34A", "#DC2626",
                                          "#7C3AED", "#6B7280")
_CACHE = {}
_MTP = MathTextParser("path")
_SUP = dict(zip("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻"))
_SUBS = dict(zip("0123456789", "₀₁₂₃₄₅₆₇₈₉"))


def _T(P, tr_text, en_text):
    return en_text if P.get("lang", "tr") == "en" else tr_text


def _sub(n):
    return "".join(_SUBS.get(c, c) for c in str(n))


def _ramp(i, i0, i1):
    if i1 <= i0:
        return 1.0 if i >= i1 else 0.0
    return min(1.0, max(0.0, (i - i0) / float(i1 - i0)))


def _key(tag, P):
    return (tag,) + tuple(sorted((str(k), repr(v)) for k, v in P.items() if k != "lang"))


def _clean(s):
    s = str(s).strip()
    for a, b in (("^", "**"), ("−", "-"), ("·", "*"), ("×", "*"), ("÷", "/"),
                 ("π", "pi"), ("∞", "oo"), ("√", "sqrt"), ("{", "("), ("}", ")")):
        s = s.replace(a, b)
    return s


def _locals(x):
    return {"x": x, "e": sp.E, "E": sp.E, "pi": sp.pi, "ln": sp.log, "abs": sp.Abs,
            "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan}


def _parse(s):
    # sympy string -> (symbol, expr). expr is None when the text cannot be parsed.
    x = sp.Symbol("x", real=True)
    txt = _clean(s)
    f = None
    try:
        f = sp.sympify(txt, locals=_locals(x))
    except Exception:
        f = None
    if not isinstance(f, sp.Expr):
        try:
            from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                                    implicit_multiplication_application)
            f = parse_expr(txt, local_dict=_locals(x), transformations=(
                standard_transformations + (implicit_multiplication_application,)))
        except Exception:
            f = None
    if not isinstance(f, sp.Expr):
        return x, None
    try:
        syms = sorted(f.free_symbols, key=lambda z: z.name)
        if syms and x not in syms:
            v = sp.Symbol(syms[0].name, real=True)
            f = f.subs(syms[0], v)
            x = v
        rest = [z for z in f.free_symbols if z != x]
        if rest:
            f = f.subs({z: 1 for z in rest})
        if f.has(sp.zoo) or f.has(sp.nan):
            return x, None
    except Exception:
        return x, None
    return x, f


def _realize(f):
    # x**(p/q) with odd q -> real root (so x**(1/3), x**(2/3) are real for x < 0, as in calculus)
    try:
        return f.replace(
            lambda e: e.is_Pow and e.exp.is_Rational and not e.exp.is_Integer and e.exp.q % 2 == 1,
            lambda e: sp.sign(e.base) ** e.exp.p * sp.Abs(e.base) ** e.exp)
    except Exception:
        return f


def _num(f, x):
    # vectorised real evaluator: complex / inf / errors -> nan, never raises
    g = None
    try:
        f = _realize(f)
        g = sp.lambdify(x, f, "numpy")
    except Exception:
        g = None

    def h(v):
        v = np.asarray(v, dtype=float)
        out = None
        if g is not None:
            try:
                with np.errstate(all="ignore"):
                    out = np.broadcast_to(np.asarray(g(v), dtype=complex), v.shape)
            except Exception:
                out = None
        if out is None:
            vals = []
            for t in v.ravel():
                try:
                    vals.append(complex(f.subs(x, float(t)).evalf()))
                except Exception:
                    vals.append(complex(float("nan"), 0.0))
            out = np.array(vals, dtype=complex).reshape(v.shape)
        with np.errstate(all="ignore"):
            re_ = np.where(np.abs(out.imag) <= 1e-9 * (1.0 + np.abs(out.real)), out.real, np.nan)
            re_ = np.where(np.isfinite(re_), re_, np.nan)
        return np.array(re_, dtype=float)
    return h


def _h1(h, t):
    try:
        return float(h(np.array([float(t)]))[0])
    except Exception:
        return float("nan")


def _fl(e):
    # sympy / python number -> float (nan when not a finite real)
    try:
        c = complex(sp.N(e))
    except Exception:
        try:
            c = complex(e)
        except Exception:
            return float("nan")
    if c.imag != c.imag or abs(c.imag) > 1e-9 * (1.0 + abs(c.real)):
        return float("nan")
    return float(c.real)


def _finite(e):
    v = _fl(e)
    return v == v and abs(v) != float("inf")


def _sval(v, default=0):
    # P value (int, float or text such as "pi/2") -> exact sympy number
    if isinstance(v, bool):
        return sp.Integer(int(v))
    if isinstance(v, int):
        return sp.Integer(v)
    if isinstance(v, float):
        if v != v:
            return sp.Integer(default)
        if abs(v) == float("inf"):
            return sp.oo if v > 0 else -sp.oo
        return sp.nsimplify(v, rational=True)
    try:
        e = sp.sympify(_clean(v), locals={"e": sp.E, "pi": sp.pi, "oo": sp.oo,
                                          "inf": sp.oo, "infinity": sp.oo})
        if isinstance(e, sp.Expr) and not e.free_symbols:
            return e
    except Exception:
        pass
    return sp.Integer(default)


def _simp(e, lim=50):
    try:
        if sp.count_ops(e) <= lim:
            return sp.simplify(e)
    except Exception:
        pass
    return e


def _wrep(s, a, b):
    # replace the whole word a by b ("oo" -> "∞" but not inside "floor")
    out = ""
    i, n, m = 0, len(s), len(a)
    while i < n:
        if s.startswith(a, i) and (i == 0 or not s[i - 1].isalnum()) and (
                i + m >= n or not s[i + m].isalnum()):
            out += b
            i += m
        else:
            out += s[i]
            i += 1
    return out


def _pretty(s):
    # "3*x**2 - 4*sqrt(x)" -> "3x² − 4√(x)"
    s = str(s).replace("**", "^").replace("{", "(").replace("}", ")")
    for a, b in (("sqrt", "√"), ("pi", "π"), ("oo", "∞"), ("Abs", "abs"), ("log", "ln"),
                 ("E", "e"), ("exp", "e^")):
        s = _wrep(s, a, b)
    out = ""
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "^":
            j = i + 1
            if j < n and s[j] == "-":
                j += 1
            k = j
            while k < n and s[k].isdigit():
                k += 1
            if k > j and not (k < n and s[k] == "."):
                out += "".join(_SUP[d] for d in s[i + 1:k])
                i = k
                continue
        if c == "*":
            prev = out[-1:]
            nxt = s[i + 1:i + 2]
            nxt2 = s[i + 2:i + 3]
            if (prev.isdigit() or prev == ")") and (nxt in ("(", "√", "π") or (
                    nxt.isalpha() and not nxt2.isalpha())):
                i += 1
                continue
            out += "·"
            i += 1
            continue
        out += c
        i += 1
    return out.replace("-", "−")


def _ps(e):
    try:
        return _pretty(sp.sstr(e))
    except Exception:
        return _pretty(str(e))


def _g(v, d=6):
    try:
        v = float(v)
    except Exception:
        return "?"
    if v != v:
        return "—"
    if abs(v) == float("inf"):
        return "∞" if v > 0 else "−∞"
    if abs(v) < 1e-12:
        v = 0.0
    s = f"{v:.{d}g}"
    if "e" in s:
        m, ex = s.split("e")
        s = m + "·10" + "".join(_SUP.get(c, "") for c in str(int(ex)))
    return s.replace("-", "−")


def _ex(e, d=6):
    # exact sympy number -> "8/3", "√2/2 ≈ 0.707107", "∞"
    try:
        e = sp.sympify(e)
    except Exception:
        return _g(e, d)
    try:
        if e == sp.oo:
            return "∞"
        if e == -sp.oo:
            return "−∞"
        if e.is_Integer:
            return _pretty(str(int(e)))
        if e.is_Rational:
            if e.q > 50:
                return _pretty(f"{e.p}/{e.q}") + " ≈ " + _g(_fl(e), d)
            return _pretty(f"{e.p}/{e.q}")
        if e.is_Float:
            return _g(e, d)
    except Exception:
        return _g(_fl(e), d)
    fv = _fl(e)
    s = _ps(e)
    if fv != fv:
        return s
    if len(s) > 26 or e.has(sp.Float):
        return _g(fv, d)
    return f"{s} ≈ {_g(fv, d)}"


def _at(e):
    # point label: "2", "1/2", "π/2" (exact when short) or a decimal
    try:
        e = sp.sympify(e)
        if e.is_Rational:
            return _ex(e)
        t = _ps(e)
        if len(t) <= 10:
            return t
    except Exception:
        pass
    return _g(_fl(e), 5)


def _big(f, x, t, y):
    # display value of f(t); falls back to sympy for overflowing values such as e^1000
    if y == y:
        return _g(y)
    try:
        v = sp.N(f.subs(x, t), 8)
        if v.is_real and v.is_finite and v != 0:
            ee = int(sp.floor(sp.log(abs(v), 10)))
            mm = float(v / sp.Integer(10) ** ee)
            return f"{mm:.4g}·10" + "".join(_SUP.get(c, "") for c in str(ee))
    except Exception:
        pass
    return "—"


def _exd(e):
    # exact value plus a short decimal for physical answers: "−3/2 = −1.5"
    s_ = _ex(e)
    try:
        e = sp.sympify(e)
        if e.is_Rational and not e.is_Integer and e.q <= 50:
            return s_ + " = " + _g(_fl(e), 6)
    except Exception:
        pass
    return s_


def _short(e, d=5):
    # compact exact (rational) or decimal, for labels
    try:
        e = sp.sympify(e)
        if e.is_Rational:
            return _ex(e)
    except Exception:
        pass
    return _g(_fl(e), d)


def _mt(latex, fb):
    s = "$" + latex + "$"
    try:
        _MTP.parse(s)
        return s
    except Exception:
        return fb


def _texf(f, fb):
    try:
        return _mt(sp.latex(f), fb)
    except Exception:
        return fb


def _yr(vals, extra=(), pad=0.12):
    v = np.asarray(vals, dtype=float).ravel()
    v = v[np.isfinite(v)]
    ex = [float(t) for t in extra if t == t and abs(t) != float("inf")]
    if len(v) == 0:
        lo, hi = -1.0, 1.0
    else:
        p1, p2 = np.percentile(v, 3), np.percentile(v, 97)
        if v.max() - v.min() <= 6 * (p2 - p1) + 1e-12:
            lo, hi = float(v.min()), float(v.max())
        else:
            lo, hi = float(p1), float(p2)
    if ex:
        lo, hi = min([lo] + ex), max([hi] + ex)
    if hi - lo < 1e-9:
        lo, hi = lo - 1.0, hi + 1.0
    p = (hi - lo) * pad
    return lo - p, hi + p


def _brk(ys, span):
    # insert gaps at jumps / vertical asymptotes so no false vertical segments are drawn
    ys = np.array(ys, dtype=float)
    if len(ys) < 3:
        return ys
    d = np.abs(np.diff(ys))
    fin = d[np.isfinite(d)]
    med = float(np.median(fin)) if len(fin) else 0.0
    bad = (d > 0.5 * span) | ((d > 0.04 * span) & (d > 60 * med + 1e-12))
    idx = np.nonzero(bad)[0]
    ys[idx + 1] = np.nan
    return ys


def _info(ax, fs=10.5, xs=None, ys=None, wide=0.5):
    # info box in the corner where the curve (xs, ys) leaves the most room
    pos = (0.02, 0.97, "left", "top")
    if xs is not None and ys is not None:
        try:
            (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
            u = (np.asarray(xs, dtype=float) - x0) / (x1 - x0)
            v = (np.asarray(ys, dtype=float) - y0) / (y1 - y0)
            ok = np.isfinite(u) & np.isfinite(v)
            u, v = u[ok], v[ok]
            best = None
            for cand in ((0.02, 0.97, "left", "top"), (0.98, 0.97, "right", "top"),
                         (0.02, 0.03, "left", "bottom"), (0.98, 0.03, "right", "bottom")):
                cu = (u < wide) if cand[2] == "left" else (u > 1 - wide)
                cv = (v > 0.72) if cand[3] == "top" else (v < 0.28)
                score = int(np.sum(cu & cv))
                if best is None or score < best[0]:
                    best = (score, cand)
            pos = best[1]
        except Exception:
            pass
    return ax.text(pos[0], pos[1], "", transform=ax.transAxes, va=pos[3], ha=pos[2], fontsize=fs,
                   zorder=30, multialignment="left", bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#D1D5DB",
                                        alpha=0.94))


def _axes_style(ax):
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.0, zorder=1)
    ax.tick_params(labelsize=9)


def _zeros(h, a, b, n=2001):
    xs = np.linspace(a, b, n)
    ys = h(xs)
    out = []
    for k in range(n - 1):
        y0, y1 = ys[k], ys[k + 1]
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        if y0 == 0:
            if k > 0 and ys[k - 1] != 0 and y1 != 0:
                out.append(float(xs[k]))
        elif y0 * y1 < 0:
            lo, hi, flo = xs[k], xs[k + 1], y0
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                fm = _h1(h, mid)
                if not np.isfinite(fm):
                    break
                if flo * fm <= 0:
                    hi = mid
                else:
                    lo, flo = mid, fm
            z = 0.5 * (lo + hi)
            if abs(_h1(h, z)) < 1e-6 * (1 + abs(y0) + abs(y1)):
                out.append(float(z))
    res = []
    for z in sorted(out):
        if not res or abs(z - res[-1]) > 1e-7 * (1 + abs(z)):
            res.append(z)
    return res[:40]


def _poles(h, a, b, n=8001):
    # interior points where |f| blows up (vertical asymptotes), found by sampling + refinement
    xs = np.linspace(a, b, n)
    ys = np.abs(h(xs))
    fin = np.isfinite(ys)
    if not np.any(fin):
        return []
    med = float(np.median(ys[fin]))
    yy = np.where(fin, ys, 0.0)
    out = []
    cand = [k for k in range(1, n - 1) if yy[k] > 30 * (med + 1) and yy[k] >= yy[k - 1] and yy[k] >= yy[k + 1]]
    cand = sorted(cand, key=lambda k: -yy[k])[:6]
    for k in cand:
        lo, hi = xs[k - 1], xs[k + 1]
        for _ in range(80):
            m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
            v1, v2 = abs(_h1(h, m1)), abs(_h1(h, m2))
            v1 = v1 if v1 == v1 else 1e300
            v2 = v2 if v2 == v2 else 1e300
            if v1 < v2:
                lo = m1
            else:
                hi = m2
        c = 0.5 * (lo + hi)
        vc = abs(_h1(h, c))
        if (vc != vc or vc > 1e7) and a < c < b:
            out.append(float(c))
    return sorted(out)


def _simpson(h, a, b, n=2000):
    if a == b:
        return 0.0
    xs = np.linspace(a, b, n + 1)
    ys = h(xs)
    if not np.all(np.isfinite(ys)):
        return float("nan")
    w = np.ones(n + 1)
    w[1:-1:2] = 4
    w[2:-1:2] = 2
    return float((b - a) / (3 * n) * np.dot(w, ys))


def _quad(h, a, b, n=4000):
    # Simpson's rule split at jump discontinuities (floor, piecewise, |x|/x ...)
    if a == b:
        return 0.0
    sg = 1.0
    if a > b:
        a, b, sg = b, a, -1.0
    xs = np.linspace(a, b, n + 1)
    ys = h(xs)
    if not np.all(np.isfinite(ys[1:-1])):
        return float("nan")
    d = np.abs(np.diff(ys))
    fin = d[np.isfinite(d)]
    med = float(np.median(fin)) if len(fin) else 0.0
    span = float(np.nanmax(ys) - np.nanmin(ys)) if np.any(np.isfinite(ys)) else 0.0
    cuts = []
    for k in np.nonzero(np.isfinite(d) & (d > 40 * med + 1e-9) & (d > 1e-3 * (span + 1e-12)))[0][:60]:
        lo, hi = xs[k], xs[k + 1]
        ylo = ys[k]
        for _ in range(55):
            mid = 0.5 * (lo + hi)
            ym = _h1(h, mid)
            if ym == ym and abs(ym - ylo) < 0.5 * d[k]:
                lo = mid
            else:
                hi = mid
        cuts.append(0.5 * (lo + hi))
    pts = [a] + cuts + [b]
    tot = 0.0
    for k in range(len(pts) - 1):
        u, w = pts[k], pts[k + 1]
        if w - u < 1e-12:
            continue
        e = 1e-11 * (1 + abs(u) + abs(w)) if len(pts) > 2 else 0.0
        m = max(20, int(n * (w - u) / (b - a)) // 2 * 2)
        uu = np.linspace(u + (e if k > 0 else 0.0), w - (e if k < len(pts) - 2 else 0.0), m + 1)
        yy = h(uu)
        if not np.all(np.isfinite(yy)):
            if np.all(np.isfinite(yy[1:-1])):
                yy = yy.copy()
                yy[0] = yy[1] if not np.isfinite(yy[0]) else yy[0]
                yy[-1] = yy[-2] if not np.isfinite(yy[-1]) else yy[-1]
            else:
                return float("nan")
        wts = np.ones(m + 1)
        wts[1:-1:2] = 4
        wts[2:-1:2] = 2
        tot += float((uu[-1] - uu[0]) / (3 * m) * np.dot(wts, yy))
    return sg * tot


def _badfig(fig, P, msg):
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.text(0.5, 0.55, msg, ha="center", va="center", fontsize=13, color=RED, wrap=True)
    ax.text(0.5, 0.4, str(P.get("f", ""))[:80], ha="center", va="center", fontsize=11,
            color=GRAY, family="DejaVu Sans Mono")

    def update(i):
        return []
    return 60, update
'''


def _code(body):
    """Ortak yardımcıları türe özgü kaynağın başına ekler."""
    return _COMMON + body


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["limit_expr"] = {
    "course": "calc1",
    "title": ("Limit: soldan ve sağdan yaklaşım", "Limits: approaching from the left and right"),
    "topics": ["limit", "limits", "one-sided limit", "one sided limits", "limits at infinity",
               "infinite limits", "evaluating limits", "limit laws", "indeterminate form",
               "removable discontinuity", "jump discontinuity", "continuity", "vertical asymptote",
               "horizontal asymptote", "limits by factoring", "l'hopital", "l'hôpital",
               "limit", "tek taraflı limit", "soldan limit", "sağdan limit", "sonsuzda limit",
               "sonsuz limit", "belirsizlik", "süreklilik", "süreksizlik", "asimptot"],
    "code": _code(r'''


def _infsign(v):
    s = str(v).strip().lower().replace(" ", "").replace("−", "-")
    if s in ("oo", "+oo", "inf", "+inf", "infinity", "+infinity", "∞", "+∞"):
        return 1
    if s in ("-oo", "-inf", "-infinity", "-∞"):
        return -1
    return 0


def _sidekey(v):
    s = str(v or "").strip().lower()
    if s in ("+", "right", "r", "sağ", "sag", "+0", "from the right"):
        return "+"
    if s in ("-", "left", "l", "sol", "-0", "from the left"):
        return "-"
    return ""


def _lv(r):
    # sympy limit result -> ("fin", value) | ("+inf", None) | ("-inf", None) | None
    try:
        if r == sp.oo:
            return ("+inf", None)
        if r == -sp.oo:
            return ("-inf", None)
        if isinstance(r, sp.AccumBounds) or r.has(sp.Limit) or r.free_symbols:
            return None
        if r == sp.zoo or r == sp.nan:
            return None
        if _finite(r):
            return ("fin", r)
    except Exception:
        return None
    return None


def _probe(h, af, sgn, inf):
    # numeric look at one side: ("fin", v) | ("+inf"/"-inf", None) | ("dne", None) | ("undef", None)
    if inf:
        ts = sgn * 10.0 ** np.arange(1, 10)
    else:
        ts = af + sgn * 10.0 ** -np.arange(1, 8)
    ys = h(ts)
    ok = np.isfinite(ys)
    if not np.any(ok):
        return ("undef", None)
    if not np.all(ok):
        first_bad = int(np.argmin(ok))
        if np.all(~ok[first_bad:]) and first_bad >= 3 and abs(ys[first_bad - 1]) > 1e6:
            return ("+inf" if ys[first_bad - 1] > 0 else "-inf", None)
        if not np.all(ok[-5:]):
            return ("dne", None)
    last = ys[-5:]
    d = np.diff(last)
    if abs(last[-1] - last[-2]) <= 1e-4 * (1 + abs(last[-1])):
        return ("fin", float(last[-1]))
    mono = bool(np.all(d > 0) or np.all(d < 0))
    if mono and abs(d[-1]) >= 0.6 * abs(d[-2]) and abs(last[-1]) > 10:
        return ("+inf" if last[-1] > 0 else "-inf", None)
    return ("dne", None)


def _side(f, x, h, a, af, sgn, inf):
    num = _probe(h, af, sgn, inf)
    if num[0] == "undef":
        return {"k": "undef", "v": None, "approx": False}
    sy = None
    try:
        if inf:
            r = sp.limit(f, x, sp.oo if sgn > 0 else -sp.oo)
        else:
            r = sp.limit(f, x, a, dir="+" if sgn > 0 else "-")
        sy = _lv(r)
    except Exception:
        sy = None
    if sy is not None:
        return {"k": sy[0], "v": sy[1], "approx": False}
    if num[0] == "fin":
        return {"k": "fin", "v": float(num[1]), "approx": True}
    return {"k": num[0], "v": None, "approx": False}


def _same(s1, s2):
    if s1["k"] != s2["k"]:
        return False
    if s1["k"] != "fin":
        return True
    v1, v2 = _fl(s1["v"]), _fl(s2["v"])
    return abs(v1 - v2) <= 1e-7 * (1 + abs(v1))


def _lval(s, P):
    k = s["k"]
    if k == "fin":
        return ("≈ " + _g(s["v"])) if s["approx"] else _ex(s["v"])
    if k == "+inf":
        return "∞"
    if k == "-inf":
        return "−∞"
    if k == "undef":
        return _T(P, "tanımsız", "undefined")
    return _T(P, "yok", "does not exist")


def _lval2(s):
    k = s["k"]
    if k == "fin":
        return ("≈ " + _g(s["v"])) if s["approx"] else _ex(s["v"])
    if k == "+inf":
        return "∞"
    if k == "-inf":
        return "−∞"
    if k == "undef":
        return ("tanımsız", "undefined")
    return ("yok", "does not exist")


def _pick(v, tr):
    if isinstance(v, tuple):
        return v[0] if tr else v[1]
    return v


def _analyze(P):
    key = _key("limit", P)
    if key in _CACHE:
        return _CACHE[key]
    x, f = _parse(P.get("f", "x"))
    A = {"ok": f is not None, "x": x, "f": f, "raw": str(P.get("f", ""))}
    inf = _infsign(P.get("a", 0))
    side = "" if inf else _sidekey(P.get("dir", ""))
    A["inf"], A["side"] = inf, side
    a = None if inf else _sval(P.get("a", 0))
    if a is not None and not _finite(a):
        inf = 1 if _fl(a) > 0 else -1
        A["inf"], a, side = inf, None, ""
        A["side"] = ""
    A["a"] = a
    A["af"] = 0.0 if a is None else _fl(a)
    vn = str(x)
    A["vn"] = vn
    if inf:
        A["at"] = "∞" if inf > 0 else "−∞"
    else:
        A["at"] = _at(a)
    A["arrow"] = f"{vn} → {A['at']}" + ("⁺" if side == "+" else ("⁻" if side == "-" else ""))
    A["fx"] = _pretty(_clean(A["raw"])) if f is not None else A["raw"].replace("{", "(").replace("}", ")")
    if f is None:
        _CACHE[key] = A
        return A
    h = _num(f, x)
    A["h"] = h
    af = A["af"]
    L = R = None
    if inf:
        R = _side(f, x, h, None, 0.0, inf, inf)
        res = dict(R)
    else:
        if side in ("", "-"):
            L = _side(f, x, h, a, af, -1, 0)
        if side in ("", "+"):
            R = _side(f, x, h, a, af, 1, 0)
        if side == "-":
            res = dict(L)
        elif side == "+":
            res = dict(R)
        elif L["k"] == "undef" and R["k"] == "undef":
            res = {"k": "undef", "v": None, "approx": False}
        elif L["k"] == "undef":
            res = dict(R)
        elif R["k"] == "undef":
            res = dict(L)
        elif _same(L, R):
            res = dict(L)
            if L["approx"] and not R["approx"]:
                res = dict(R)
        else:
            res = {"k": "dne", "v": None, "approx": False}
    A["L"], A["R"], A["res"] = L, R, res
    # value of f at the point itself
    fa = None
    if not inf:
        try:
            v = f.subs(x, a)
            if _finite(v) and not v.free_symbols:
                fa = _simp(v)
        except Exception:
            fa = None
        if fa is None:
            v = _h1(h, af)
            if v == v and abs(_h1(h, af + 1e-9) - v) < 1e-3 * (1 + abs(v)):
                fa = sp.Float(v, 8)
    A["fa"] = fa
    # classification
    if inf:
        kind = {"fin": "hasym", "+inf": "infty", "-inf": "infty"}.get(res["k"], res["k"])
    else:
        if res["k"] == "fin":
            if side:
                kind = "one"
            elif (L["k"] == "undef") or (R["k"] == "undef"):
                kind = "domain"
            elif fa is None:
                kind = "hole"
            elif abs(_fl(fa) - _fl(res["v"])) <= 1e-7 * (1 + abs(_fl(fa))):
                kind = "cont"
            else:
                kind = "remov"
        elif res["k"] in ("+inf", "-inf"):
            kind = "vasym"
        elif res["k"] == "dne":
            if L is not None and R is not None and L["k"] == "fin" and R["k"] == "fin":
                kind = "jump"
            elif L is not None and R is not None and "inf" in L["k"] + R["k"]:
                kind = "vasym"
            else:
                kind = "osc"
        else:
            kind = "undef"
    A["kind"] = kind
    # value tables
    if inf:
        xs = [inf * 10.0 ** k for k in range(1, 7)]
        A["rows"] = [("", [(t, _h1(h, t), _big(f, x, t, _h1(h, t))) for t in xs])]
    else:
        hs = [0.1, 0.01, 0.001, 0.0001]
        rows = []
        if side in ("", "-"):
            rows.append(("-", [(af - t, _h1(h, af - t), _g(_h1(h, af - t))) for t in hs]))
        if side in ("", "+"):
            rows.append(("+", [(af + t, _h1(h, af + t), _g(_h1(h, af + t))) for t in hs]))
        A["rows"] = rows
    A["tex"] = _texf(f, A["fx"])
    _CACHE[key] = A
    return A


def _alg_steps(A):
    f, x, a, af = A["f"], A["x"], A["a"], A["af"]
    vn, at = A["vn"], A["at"]
    res = A["res"]
    st = []
    try:
        num, den = sp.fraction(sp.together(f))
    except Exception:
        num, den = f, sp.Integer(1)
    if not den.has(x):
        num, den = f, sp.Integer(1)
    nA = _fl(num.subs(x, a)) if den.has(x) else float("nan")
    dA = _fl(den.subs(x, a)) if den.has(x) else 1.0
    fa = A["fa"]
    if not den.has(x) or (dA == dA and abs(dA) > 1e-12):
        if fa is not None:
            st.append((f"Doğrudan yerine koy: f({at}) = {_ex(fa)}",
                       f"Direct substitution: f({at}) = {_ex(fa)}"))
            if A["kind"] == "cont":
                st.append(("Fonksiyon bu noktada sürekli; limit, fonksiyonun değerine eşittir.",
                           "The function is continuous here, so the limit equals the function value."))
            elif A["kind"] in ("jump", "remov"):
                st.append(("Ancak limit, f(a) değerine değil yaklaşılan değerlere bağlıdır: "
                           "soldan ve sağdan ayrı ayrı bak.",
                           "But a limit depends on nearby values, not on f(a): "
                           "look from the left and from the right."))
        else:
            st.append((f"{vn} = {at} tanım kümesinde değil (f({at}) tanımsız); yaklaşan değerlere bak.",
                       f"{vn} = {at} is not in the domain (f({at}) undefined); look at nearby values."))
    elif abs(nA) < 1e-12 and abs(dA) < 1e-12:
        st.append((f"Yerine koyma 0/0 belirsizliği verir: pay({at}) = 0, payda({at}) = 0.",
                   f"Substitution gives the indeterminate form 0/0: numerator({at}) = 0, denominator({at}) = 0."))
        done = False
        if f.has(sp.Abs):
            try:
                hl, hr = {}, {}
                for t in f.atoms(sp.Abs):
                    u = t.args[0]
                    hu = _num(u, x)
                    hl[t] = u if _h1(hu, af - 1e-6) >= 0 else -u
                    hr[t] = u if _h1(hu, af + 1e-6) >= 0 else -u
                fl_ = sp.cancel(f.xreplace(hl))
                fr_ = sp.cancel(f.xreplace(hr))
                st.append((f"Mutlak değeri aç: {vn} < {at} için f = {_ps(fl_)},  {vn} > {at} için f = {_ps(fr_)}",
                           f"Open the absolute value: for {vn} < {at}, f = {_ps(fl_)};  for {vn} > {at}, f = {_ps(fr_)}"))
                done = True
            except Exception:
                done = False
        if not done and f.is_rational_function(x):
            try:
                fn, fd = sp.factor(num), sp.factor(den)
                g = sp.cancel(f)
                st.append((f"Çarpanlara ayır: ({_ps(fn)}) / ({_ps(fd)})  →  ortak çarpanı sadeleştir: {_ps(g)}",
                           f"Factor: ({_ps(fn)}) / ({_ps(fd)})  →  cancel the common factor: {_ps(g)}"))
                gv = g.subs(x, a)
                if _finite(gv):
                    st.append((f"Sadeleşmiş ifadeye {vn} = {at} koy: {_ex(_simp(gv))}",
                               f"Substitute {vn} = {at} into the simplified form: {_ex(_simp(gv))}"))
                done = True
            except Exception:
                done = False
        if not done and res["k"] == "fin" and not res["approx"]:
            n_, d_ = num, den
            for _ in range(3):
                try:
                    n_, d_ = sp.diff(n_, x), sp.diff(d_, x)
                    nv, dv = n_.subs(x, a), d_.subs(x, a)
                except Exception:
                    break
                if _finite(dv) and abs(_fl(dv)) > 1e-12 and _finite(nv):
                    val = _simp(nv / dv)
                    if abs(_fl(val) - _fl(res["v"])) <= 1e-7 * (1 + abs(_fl(val))):
                        st.append((f"L'Hôpital kuralı: lim ({_ps(n_)}) / ({_ps(d_)}) = {_ex(val)}",
                                   f"L'Hôpital's rule: lim ({_ps(n_)}) / ({_ps(d_)}) = {_ex(val)}"))
                    break
                if not (_finite(nv) and abs(_fl(nv)) < 1e-12):
                    break
                st.append((f"L'Hôpital: türevler ({_ps(n_)}) / ({_ps(d_)}) hâlâ 0/0 — bir kez daha uygula",
                           f"L'Hôpital: derivatives ({_ps(n_)}) / ({_ps(d_)}) still 0/0 — apply again"))
    elif dA == dA and nA == nA:
        st.append((f"Yerine koyma {_g(nA)}/0 biçimini verir: pay sıfırdan farklı, payda 0 → "
                   "sonsuz limit; işaret için tek taraflı limitlere bak.",
                   f"Substitution gives {_g(nA)}/0: nonzero over zero → an infinite limit; "
                   "check the signs from each side."))
    else:
        st.append((f"f({at}) tanımsız; yaklaşan değerlere bak.",
                   f"f({at}) is undefined; look at nearby values."))
    return st


def _inf_steps(A):
    f, x = A["f"], A["x"]
    vn, at = A["vn"], A["at"]
    st = []
    try:
        if f.is_rational_function(x):
            num, den = sp.fraction(sp.cancel(sp.together(f)))
            n, m = sp.degree(num, x), sp.degree(den, x)
            ln, ld = sp.LC(num, x), sp.LC(den, x)
            pw = vn + "".join(_SUP.get(c, c) for c in str(m)) if m > 1 else vn
            if m >= 1:
                st.append((f"Rasyonel fonksiyon: pay derecesi {n}, payda derecesi {m}. "
                           f"Pay ve paydayı {pw} ile böl.",
                           f"Rational function: numerator degree {n}, denominator degree {m}. "
                           f"Divide numerator and denominator by {pw}."))
            else:
                st.append((f"Polinom (derece {n}): baş terim baskındır.",
                           f"Polynomial (degree {n}): the leading term dominates."))
            if n < m:
                st.append((f"{n} < {m}: pay paydaya göre yavaş büyür ⇒ limit 0.",
                           f"{n} < {m}: the numerator grows more slowly ⇒ the limit is 0."))
            elif n == m:
                st.append((f"Dereceler eşit ⇒ limit = baş katsayıların oranı = {_ex(ln)}/{_ex(ld)} = {_ex(sp.nsimplify(ln / ld))}",
                           f"Equal degrees ⇒ limit = ratio of leading coefficients = {_ex(ln)}/{_ex(ld)} = {_ex(sp.nsimplify(ln / ld))}"))
            elif m >= 1:
                st.append((f"{n} > {m}: pay daha hızlı büyür ⇒ |f| sınırsız büyür (işareti baş katsayılar belirler).",
                           f"{n} > {m}: the numerator wins ⇒ |f| grows without bound (leading coefficients give the sign)."))
            elif n >= 1:
                st.append((f"Baş terim {_ps(sp.LT(num, x))} ⇒ |f| sınırsız büyür.",
                           f"Leading term {_ps(sp.LT(num, x))} ⇒ |f| grows without bound."))
        else:
            st.append((f"{vn} çok büyürken baskın terimleri karşılaştır ve değer tablosuna bak.",
                       f"As {vn} grows, compare the dominant terms and look at a table of values."))
    except Exception:
        st.append((f"{vn} çok büyürken değer tablosuna bak.", f"Look at a table of values as {vn} grows."))
    return st


def solve(P):
    A = _analyze(P)
    if not A["ok"]:
        return {"answer": ("İfade çözümlenemedi", "Could not parse the expression"),
                "steps": [(f"Girdi: {A['raw']}", f"Input: {A['raw']}"),
                          ("İfadeyi x değişkeniyle, * ve ** kullanarak yazın.",
                           "Write the expression in x using * and **.")],
                "fmt": {"fx": A["fx"], "pretty_f": A["fx"], "a": A["at"], "lim": A["arrow"]}}
    vn, at, arrow = A["vn"], A["at"], A["arrow"]
    res, L, R, kind = A["res"], A["L"], A["R"], A["kind"]
    st = [(f"İstenen: lim ({arrow}) f({vn}),  f({vn}) = {A['fx']}",
           f"Find: lim ({arrow}) f({vn}),  f({vn}) = {A['fx']}")]
    st += _inf_steps(A) if A["inf"] else _alg_steps(A)
    if not A["inf"] and not A["side"]:
        lt, rt = _lval2(L), _lval2(R)
        st.append((f"Soldan: lim ({vn} → {at}⁻) = {_pick(lt, True)};  sağdan: lim ({vn} → {at}⁺) = {_pick(rt, True)}",
                   f"From the left: lim ({vn} → {at}⁻) = {_pick(lt, False)};  from the right: lim ({vn} → {at}⁺) = {_pick(rt, False)}"))
    rows = A["rows"]
    parts = []
    for sd, rr in rows:
        for t, y, ys_ in (rr[1:3] if not A["inf"] else [rr[0], rr[2], rr[5]]):
            parts.append(f"f({_g(t, 8)}) ≈ {ys_}")
    tb = ", ".join(parts)
    st.append((f"Sayısal kontrol: {tb}", f"Numerical check: {tb}"))
    v = _lval2(res)
    vt, ve = _pick(v, True), _pick(v, False)
    concl = {
        "cont": (f"Sonuç: limit = {vt}; f sürekli olduğundan f({at}) ile aynı.",
                 f"Result: the limit is {ve}; f is continuous, so it equals f({at})."),
        "hole": (f"Sonuç: limit = {vt}. f({at}) tanımsız: grafikte ({at}, {_short(res['v']) if res['k'] == 'fin' else ''}) noktasında delik var (kaldırılabilir süreksizlik).",
                 f"Result: the limit is {ve}. f({at}) is undefined: the graph has a hole at ({at}, {_short(res['v']) if res['k'] == 'fin' else ''}) (removable discontinuity)."),
        "remov": (f"Sonuç: limit = {vt}, fakat f({at}) = {_ex(A['fa']) if A['fa'] is not None else ''} — kaldırılabilir süreksizlik.",
                  f"Result: the limit is {ve}, but f({at}) = {_ex(A['fa']) if A['fa'] is not None else ''} — a removable discontinuity."),
        "jump": ("Sonuç: tek taraflı limitler farklı ⇒ iki taraflı limit YOK (sıçrama süreksizliği).",
                 "Result: the one-sided limits differ ⇒ the two-sided limit does NOT exist (jump discontinuity)."),
        "vasym": (f"Sonuç: {vn} = {at} dikey asimptot; limit {vt}" + ("" if res["k"] != "dne" else " (iki taraf farklı sonsuzluklara gider)"),
                  f"Result: {vn} = {at} is a vertical asymptote; the limit {'is ' + ve if res['k'] != 'dne' else 'does not exist (the sides go to different infinities)'}"),
        "osc": ("Sonuç: değerler bir sayıya yerleşmiyor (salınım) ⇒ limit yok.",
                "Result: the values do not settle down (oscillation) ⇒ the limit does not exist."),
        "domain": (f"Sonuç: f yalnızca bir taraftan tanımlı; o taraftan limit = {vt}.",
                   f"Result: f is defined on one side only; the limit from that side is {ve}."),
        "one": (f"Sonuç: tek taraflı limit = {vt}.", f"Result: the one-sided limit is {ve}."),
        "hasym": (f"Sonuç: limit = {vt} ⇒ y = {vt} yatay asimptot.",
                  f"Result: the limit is {ve} ⇒ y = {ve} is a horizontal asymptote."),
        "infty": (f"Sonuç: f sınırsız büyür; limit {vt}.", f"Result: f grows without bound; the limit is {ve}."),
        "dne": ("Sonuç: limit yok.", "Result: the limit does not exist."),
        "undef": (f"Sonuç: f, {vn} = {at} yakınında tanımlı değil; limit tanımsız.",
                  f"Result: f is not defined near {vn} = {at}; the limit is undefined."),
    }[kind]
    st.append(concl)
    tag = {"hole": (f"  (delik: {vn} = {at})", f"  (hole at {vn} = {at})"),
           "remov": ("  (kaldırılabilir süreksizlik)", "  (removable discontinuity)"),
           "jump": (f"  (soldan {_pick(_lval2(L), True)}, sağdan {_pick(_lval2(R), True)})" if L and R else "",
                    f"  (left {_pick(_lval2(L), False)}, right {_pick(_lval2(R), False)})" if L and R else ""),
           "vasym": (f"  (dikey asimptot {vn} = {at})", f"  (vertical asymptote {vn} = {at})"),
           "hasym": (f"  (yatay asimptot y = {vt})", f"  (horizontal asymptote y = {ve})")}.get(kind, ("", ""))
    ans = (f"lim ({arrow}) f({vn}) = {vt}{tag[0]}", f"lim ({arrow}) f({vn}) = {ve}{tag[1]}")
    if kind == "jump" or (kind == "vasym" and res["k"] == "dne"):
        ans = (f"Limit yok{tag[0]}", f"The limit does not exist{tag[1]}")
    elif res["k"] == "dne":
        ans = (f"lim ({arrow}) f({vn}) yok (değerler bir sayıya yerleşmiyor)",
               f"lim ({arrow}) f({vn}) does not exist (the values do not settle)")
    elif res["k"] == "undef":
        ans = (f"lim ({arrow}) f({vn}) tanımsız (f bu yakında tanımlı değil)",
               f"lim ({arrow}) f({vn}) is undefined (f is not defined there)")
    return {"answer": ans, "steps": st,
            "fmt": {"fx": A["fx"], "pretty_f": A["fx"], "a": at, "lim": arrow}}


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    A = _analyze(P)
    if not A["ok"]:
        return _badfig(fig, P, _T(P, "İfade çözümlenemedi", "Could not parse the expression"))
    if A["inf"]:
        return _build_inf(fig, P, A, tr)
    return _build_fin(fig, P, A, tr)


def _table(tb, A, tr):
    tb.axis("off")
    tb.set_xlim(0, 1)
    tb.set_ylim(0, 1)
    vn = A["vn"]
    tb.text(0.02, 0.985, _T({"lang": "tr" if tr else "en"}, "Değer tablosu", "Table of values"),
            fontsize=11, fontweight="bold", va="top", color="#111827")
    cells = []
    y = 0.9
    for sd, rr in A["rows"]:
        if sd:
            head = (f"{vn} → {A['at']}⁻ (" + ("soldan" if tr else "left") + ")") if sd == "-" else \
                   (f"{vn} → {A['at']}⁺ (" + ("sağdan" if tr else "right") + ")")
        else:
            head = f"{vn} → {A['at']}"
        col = ORANGE if sd == "-" else PURPLE
        tb.text(0.02, y, head, fontsize=10, color=col, fontweight="bold", va="top")
        y -= 0.065
        tb.text(0.04, y, f"{vn:>3}", fontsize=9.5, family="DejaVu Sans Mono", va="top", color=GRAY)
        tb.text(0.52, y, "f(" + vn + ")", fontsize=9.5, family="DejaVu Sans Mono", va="top", color=GRAY)
        y -= 0.06
        for t, v, vs in rr:
            c1 = tb.text(0.04, y, _g(t, 8), fontsize=9.5, family="DejaVu Sans Mono", va="top", alpha=0)
            c2 = tb.text(0.52, y, _g(v, 7) if v == v else (vs if vs != "—" else ("tanımsız" if tr else "undef.")),
                         fontsize=9.5, family="DejaVu Sans Mono", va="top", alpha=0, color=col)
            cells.append((c1, c2))
            y -= 0.058
        y -= 0.03
    res = tb.text(0.02, max(y, 0.02) if y > 0.1 else 0.05, "", fontsize=11, color=GREEN,
                  fontweight="bold", va="top")
    return cells, res


def _build_fin(fig, P, A, tr):
    h, af, kind, res = A["h"], A["af"], A["kind"], A["res"]
    L, R, side = A["L"], A["R"], A["side"]
    W = float(P.get("w", 3.0) or 3.0)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.85, 1], left=0.07, right=0.99, top=0.9,
                          bottom=0.1, wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    tb = fig.add_subplot(gs[0, 1])
    xs = af + W * np.linspace(-1, 1, 801)
    ys = h(xs)
    ext = []
    for s in (L, R):
        if s is not None and s["k"] == "fin":
            ext.append(_fl(s["v"]))
    if A["fa"] is not None:
        ext.append(_fl(A["fa"]))
    v = np.asarray(ys, dtype=float)
    v = v[np.isfinite(v)]
    if kind == "vasym" and len(v):
        q1, q2 = np.percentile(v, 12), np.percentile(v, 88)
        lo, hi = float(min(q1, 0)), float(max(q2, 0))
        pad = 0.15 * (hi - lo + 1e-9)
        lo, hi = lo - pad, hi + pad
    else:
        lo, hi = _yr(ys, ext)
    span = hi - lo
    yb = _brk(ys, span)
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(lo, hi)
    _axes_style(ax)
    ax.set_xlabel(A["vn"], fontsize=10)
    ax.set_title(_mt(r"\lim_{" + A["vn"] + r"\to " + sp.latex(A["a"]) + ("^{+}" if side == "+" else ("^{-}" if side == "-" else "")) + "}\\ " + sp.latex(A["f"]), "lim  " + A["fx"]),
                 fontsize=13)
    curve, = ax.plot([], [], color=BLUE, lw=2.4, zorder=3)
    ax.axvline(af, color=GRAY, ls=":", lw=1.2, zorder=1)
    ax.text(af, lo + 0.02 * span, f" {A['vn']} = {A['at']}", color=GRAY, fontsize=9, va="bottom")
    dots, guides_h, guides_v, edge = {}, {}, {}, {}
    for sd, col in (("-", ORANGE), ("+", PURPLE)):
        dots[sd], = ax.plot([], [], "o", color=col, ms=9, zorder=6)
        guides_h[sd], = ax.plot([], [], ":", color=col, lw=1.3, zorder=2)
        guides_v[sd], = ax.plot([], [], ":", color=col, lw=1.3, zorder=2)
        edge[sd], = ax.plot([], [], ">", color=col, ms=9, zorder=6, clip_on=False)
    limline, = ax.plot([], [], "--", color=GREEN, lw=1.6, zorder=2)
    asym, = ax.plot([], [], "--", color=RED, lw=1.6, zorder=2)
    hole, = ax.plot([], [], "o", ms=11, mfc="white", mec=BLUE, mew=2.2, zorder=7)
    filled, = ax.plot([], [], "o", ms=8, color=BLUE, zorder=8)
    ring, = ax.plot([], [], "o", ms=20, mfc="none", mec=GREEN, mew=2, zorder=7)
    rlab = ax.text(0, 0, "", color=GREEN, fontsize=12, fontweight="bold", zorder=9,
                   bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.8))
    info = _info(ax)
    cells, restxt = _table(tb, A, tr)
    sides = [s for s in ("-", "+") if (s == side or not side)]
    h0, h1 = 0.85 * W, 0.004 * W
    N = 150
    holes, fills = [], []
    if kind in ("hole", "remov"):
        holes = [(af, _fl(res["v"]))]
    if kind == "jump":
        holes = [(af, _fl(L["v"])), (af, _fl(R["v"]))]
    if kind in ("one", "domain") and res["k"] == "fin" and (A["fa"] is None or abs(_fl(A["fa"]) - _fl(res["v"])) > 1e-7):
        holes = [(af, _fl(res["v"]))]
    if A["fa"] is not None and kind in ("remov", "jump", "cont", "one", "domain"):
        fills = [(af, _fl(A["fa"]))]
    sol = solve(P)
    ans = _pick(sol["answer"], tr)
    vn, at = A["vn"], A["at"]

    def update(i):
        p = _ramp(i, 0, 24)
        m = max(2, int(p * len(xs)))
        curve.set_data(xs[:m], yb[:m])
        q = _ramp(i, 26, 96)
        hh = h0 * (h1 / h0) ** q
        xl, yl = ax.get_xlim()[0], lo
        for sd in ("-", "+"):
            if i >= 26 and sd in sides:
                xp = af - hh if sd == "-" else af + hh
                yp = _h1(h, xp)
                if yp == yp:
                    yc = min(max(yp, lo), hi)
                    dots[sd].set_data([xp], [yp])
                    guides_h[sd].set_data([xl, xp], [yc, yc])
                    guides_v[sd].set_data([xp, xp], [yl, yc])
                    edge[sd].set_data([xl], [yc])
                    continue
            dots[sd].set_data([], [])
            guides_h[sd].set_data([], [])
            guides_v[sd].set_data([], [])
            edge[sd].set_data([], [])
        for k, (c1, c2) in enumerate(cells):
            kk = k % 4
            al = _ramp(i, 30 + 15 * kk, 36 + 15 * kk)
            c1.set_alpha(al)
            c2.set_alpha(al)
        fin = i >= 100
        if fin and res["k"] == "fin":
            lv = _fl(res["v"])
            limline.set_data([xs[0], xs[-1]], [lv, lv])
            ring.set_data([af], [lv])
            ring.set_markersize(16 + 10 * ((i - 100) % 16) / 16.0)
            rising = _h1(h, af + 0.3 * W) >= _h1(h, af - 0.3 * W)
            rlab.set_position((af + (-0.1 * W if rising else 0.06 * W), lv + 0.06 * span))
            rlab.set_ha("right" if rising else "left")
            rlab.set_text(f"L = {_short(res['v'])}" if not res["approx"] else f"L ≈ {_g(lv, 5)}")
        else:
            limline.set_data([], [])
            ring.set_data([], [])
            rlab.set_text("")
        if fin and kind == "jump":
            rlab.set_position((af + 0.06 * W, 0.5 * (_fl(L["v"]) + _fl(R["v"]))))
            rlab.set_text((f"L⁻ = {_short(L['v'])}\nL⁺ = {_short(R['v'])}"))
        if fin and kind == "vasym":
            asym.set_data([af, af], [lo, hi])
        else:
            asym.set_data([], [])
        if fin and holes:
            hole.set_data([u for u, _ in holes], [w for _, w in holes])
        else:
            hole.set_data([], [])
        if fin and fills:
            filled.set_data([u for u, _ in fills], [w for _, w in fills])
        else:
            filled.set_data([], [])
        if i < 26:
            info.set_text(_T(P, f"1) f({vn}) grafiği; hedef {vn} → {at}",
                             f"1) Graph of f({vn}); target {vn} → {at}"))
        elif not fin:
            parts = []
            for sd in sides:
                xp = af - hh if sd == "-" else af + hh
                yp = _h1(h, xp)
                parts.append(f"f({_g(xp, 5)}) = {_g(yp, 5) if yp == yp else ('tanımsız' if tr else 'undefined')}")
            info.set_text(_T(P, f"2) {vn}, {at} sayısına yaklaşıyor  (h = {_g(hh, 2)})\n",
                             f"2) {vn} approaches {at}  (h = {_g(hh, 2)})\n") + "\n".join(parts))
        else:
            info.set_text("3) " + ans)
        restxt.set_text(("lim = " + _pick(_lval2(res), tr)) if fin else "")
        return []

    return N, update


def _build_inf(fig, P, A, tr):
    h, sg, res = A["h"], A["inf"], A["res"]
    gs = fig.add_gridspec(1, 2, width_ratios=[1.85, 1], left=0.08, right=0.99, top=0.9,
                          bottom=0.1, wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    tb = fig.add_subplot(gs[0, 1])
    _axes_style(ax)
    ax.set_xlabel(A["vn"], fontsize=10)
    ax.set_title(_mt(r"\lim_{" + A["vn"] + r"\to " + ("" if sg > 0 else "-") + r"\infty}\ " + sp.latex(A["f"]),
                     "lim  " + A["fx"]), fontsize=13)
    curve, = ax.plot([], [], color=BLUE, lw=2.4, zorder=3)
    dot, = ax.plot([], [], "o", color=PURPLE, ms=9, zorder=6)
    gline, = ax.plot([], [], ":", color=PURPLE, lw=1.3)
    asym, = ax.plot([], [], "--", color=GREEN, lw=1.8, zorder=2)
    alab = ax.text(0, 0, "", color=GREEN, fontsize=12, fontweight="bold", ha="right", va="bottom")
    info = _info(ax)
    cells, restxt = _table(tb, A, tr)
    lv = _fl(res["v"]) if res["k"] == "fin" else float("nan")
    sol = solve(P)
    ans = _pick(sol["answer"], tr)
    vn = A["vn"]
    N = 150
    smp = sg * np.concatenate([np.linspace(0.0, 10.0, 200), np.geomspace(10.0, 1e5, 300)])
    sv = h(smp)
    sv = sv[np.isfinite(sv)]
    fixed = None
    if lv == lv and len(sv):
        q1, q2 = np.percentile(sv, 5), np.percentile(sv, 95)
        lo0, hi0 = min(q1, lv), max(q2, lv)
        if hi0 - lo0 < 1e-9:
            lo0, hi0 = lo0 - 1, hi0 + 1
        pd = 0.12 * (hi0 - lo0)
        fixed = (lo0 - pd, hi0 + pd)

    def update(i):
        q = _ramp(i, 22, 100)
        Rr = 10.0 ** (1 + 4 * q)
        if sg > 0:
            x0, x1 = -0.04 * Rr, 1.04 * Rr
        else:
            x0, x1 = -1.04 * Rr, 0.04 * Rr
        xs = np.linspace(x0, x1, 700)
        ys = h(xs)
        if fixed is not None:
            lo, hi = fixed
        else:
            lo, hi = _yr(ys[np.abs(xs) > 0.02 * Rr], [lv] if lv == lv else [])
        ax.set_xlim(x0, x1)
        ax.set_ylim(lo, hi)
        p = _ramp(i, 0, 20)
        m = max(2, int(p * len(xs)))
        yb = _brk(ys, hi - lo)
        if sg > 0:
            curve.set_data(xs[:m], yb[:m])
        else:
            curve.set_data(xs[::-1][:m], yb[::-1][:m])
        if i >= 22:
            xt = sg * 0.85 * Rr
            yt = _h1(h, xt)
            if yt == yt:
                dot.set_data([xt], [yt])
                gline.set_data([xt, xt], [lo, min(max(yt, lo), hi)])
            else:
                dot.set_data([], [])
                gline.set_data([], [])
        else:
            dot.set_data([], [])
            gline.set_data([], [])
        for k, (c1, c2) in enumerate(cells):
            al = _ramp(i, 24 + 15 * k, 30 + 15 * k) if k < 5 else _ramp(i, 100, 106)
            c1.set_alpha(al)
            c2.set_alpha(al)
        fin = i >= 100
        if fin and lv == lv:
            asym.set_data([x0, x1], [lv, lv])
            alab.set_position((x1 - 0.03 * (x1 - x0) if sg > 0 else x0 + 0.35 * (x1 - x0), lv + 0.02 * (hi - lo)))
            alab.set_text(f"y = {_short(res['v'])}")
        else:
            asym.set_data([], [])
            alab.set_text("")
        if i < 22:
            info.set_text(_T(P, f"1) f({vn}) grafiği", f"1) Graph of f({vn})"))
        elif not fin:
            xt = sg * 0.85 * Rr
            yt = _h1(h, xt)
            info.set_text(_T(P, f"2) {vn} büyüdükçe görüntüyü uzaklaştır\n", f"2) Zoom out as {vn} grows\n")
                          + f"f({_g(xt, 4)}) = {_g(yt, 6)}")
        else:
            info.set_text("3) " + ans)
        restxt.set_text(("lim = " + _pick(_lval2(res), tr)) if fin else "")
        return []

    return N, update


def _lin(c):
    if c == 0:
        return "x"
    return f"x - {c}" if c > 0 else f"x + {-c}"


def vary(P, rnd):
    f = str(P.get("f", "")).lower()
    inf = _infsign(P.get("a", 0))
    out = {}
    if inf:
        k = rnd.choice([2, 3, 4, 5, 6, 8, 10, 12, 20, 30, 40])
        s = rnd.choice([1, 2, 3, 4, 5, 6, 8, 10])
        if "**2" in f:
            r = rnd.choice([1, 2, 3])
            c = rnd.choice([1, 2, 3, 5, 7])
            out = {"f": f"({k * r}*x**2 + {c})/({r}*x**2 + {s})", "a": "oo" if inf > 0 else "-oo"}
        else:
            out = {"f": f"{k}*x/(x + {s})", "a": "oo" if inf > 0 else "-oo"}
    elif "abs" in f:
        c = rnd.randint(-3, 4)
        k = rnd.choice([1, 2, 3])
        out = {"f": (f"{k}*" if k != 1 else "") + f"abs({_lin(c)})/({_lin(c)})", "a": c}
    else:
        r = rnd.choice([v for v in range(-4, 6) if v != 0])
        s = rnd.choice([v for v in range(-5, 6) if v != -r])
        x = sp.Symbol("x")
        num = sp.expand((x - r) * (x + s))
        out = {"f": f"({sp.sstr(num)})/({_lin(r)})", "a": r}
    if "dir" in P and not inf:
        out["dir"] = P["dir"]
    for k2, v2 in P.items():
        if k2 not in out and k2 not in ("f", "a", "dir", "lang"):
            out[k2] = v2
    return out
'''),
}
EXAMPLES += [
    {"id": "calc1-limit-1", "kind": "limit_expr",
     "title": ("0/0 belirsizliği: delikli grafik", "0/0 form: a graph with a hole"),
     "q": ("lim ({lim}) {pretty_f} limitini hesapla. Fonksiyon x = {a} noktasında tanımlı mı?",
           "Evaluate lim ({lim}) {pretty_f}. Is the function defined at x = {a}?"),
     "P": {"f": "(x**2 - 4)/(x - 2)", "a": 2}},
    {"id": "calc1-limit-2", "kind": "limit_expr", "topics": ["jump", "sıçrama", "absolute value"],
     "title": ("Tek taraflı limitler ve sıçrama", "One-sided limits and a jump"),
     "q": ("f(x) = {pretty_f} için x → {a} iken soldan ve sağdan limitleri bul. İki taraflı limit var mı?",
           "For f(x) = {pretty_f}, find the left- and right-hand limits as x → {a}. "
           "Does the two-sided limit exist?"),
     "P": {"f": "abs(x - 1)/(x - 1)", "a": 1}},
    {"id": "calc1-limit-3", "kind": "limit_expr",
     "topics": ["word problem", "sözel problem", "concentration", "derişim", "long run"],
     "title": ("Sonsuzda limit: ilaç derişimi", "Limit at infinity: drug concentration"),
     "q": ("Bir ilacın kandaki derişimi C(t) = {pretty_f} mg/L (t saat). Uzun vadede ({lim}) "
           "derişim hangi değere yaklaşır?",
           "The concentration of a drug in the blood is C(t) = {pretty_f} mg/L (t in hours). "
           "In the long run ({lim}), what value does it approach?"),
     "P": {"f": "30*t/(t + 5)", "a": "oo"}},
]


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["derivative_expr"] = {
    "course": "calc1",
    "title": ("Türev: kesenden teğete", "Derivative: from secant to tangent"),
    "topics": ["derivative", "derivatives", "definition of the derivative", "difference quotient",
               "tangent line", "secant line", "slope of the tangent", "power rule", "product rule",
               "quotient rule", "chain rule", "differentiation", "derivative rules",
               "instantaneous rate of change", "instantaneous velocity",
               "türev", "türevin tanımı", "teğet doğrusu", "teğet", "kesen", "türev kuralları",
               "zincir kuralı", "çarpım kuralı", "bölüm kuralı", "anlık değişim", "anlık hız"],
    "code": _code(r'''


_RULES = {
    "power": ("Kuvvet kuralı: (xⁿ)' = n·xⁿ⁻¹", "Power rule: (xⁿ)' = n·xⁿ⁻¹"),
    "sum": ("Toplam/fark kuralı: (u ± v)' = u' ± v'", "Sum/difference rule: (u ± v)' = u' ± v'"),
    "const": ("Sabit çarpan kuralı: (c·u)' = c·u'", "Constant multiple rule: (c·u)' = c·u'"),
    "prod": ("Çarpım kuralı: (u·v)' = u'·v + u·v'", "Product rule: (u·v)' = u'·v + u·v'"),
    "quot": ("Bölüm kuralı: (u/v)' = (u'·v − u·v')/v²", "Quotient rule: (u/v)' = (u'·v − u·v')/v²"),
    "chain": ("Zincir kuralı: (f(g(x)))' = f'(g(x))·g'(x)", "Chain rule: (f(g(x)))' = f'(g(x))·g'(x)"),
    "trig": ("Trigonometrik türevler: (sin x)' = cos x, (cos x)' = −sin x, (tan x)' = sec²x",
             "Trig derivatives: (sin x)' = cos x, (cos x)' = −sin x, (tan x)' = sec²x"),
    "exp": ("Üstel fonksiyon: (eˣ)' = eˣ, (aˣ)' = aˣ·ln a", "Exponential: (eˣ)' = eˣ, (aˣ)' = aˣ·ln a"),
    "log": ("Logaritma: (ln x)' = 1/x", "Logarithm: (ln x)' = 1/x"),
    "invtrig": ("Ters trigonometrik: (arctan x)' = 1/(1 + x²), (arcsin x)' = 1/√(1 − x²)",
                "Inverse trig: (arctan x)' = 1/(1 + x²), (arcsin x)' = 1/√(1 − x²)"),
    "logdiff": ("Logaritmik türev: y = u^v ⇒ ln y = v·ln u", "Logarithmic differentiation: y = u^v ⇒ ln y = v·ln u"),
    "other": ("Diğer fonksiyonlar sympy ile türevlendi", "Other functions differentiated with sympy"),
}


def _rules(f, x):
    found = []

    def add(k):
        if k not in found:
            found.append(k)

    def walk(e):
        if not e.has(x):
            return
        if e == x:
            add("power")
            return
        if e.is_Add:
            add("sum")
            for t in e.args:
                walk(t)
        elif e.is_Mul:
            nc = [t for t in e.args if t.has(x)]
            if len(nc) < len(e.args):
                add("const")
            dens = [t for t in nc if t.is_Pow and t.exp.is_number and t.exp.is_negative and t.base != x]
            if dens and len(nc) > len(dens):
                add("quot")
            elif len(nc) >= 2:
                add("prod")
            for t in nc:
                walk(t)
        elif e.is_Pow:
            b, ex = e.args
            if b.has(x) and not ex.has(x):
                add("power")
                if b != x:
                    add("chain")
                walk(b)
            elif not b.has(x):
                add("exp")
                if ex != x:
                    add("chain")
                walk(ex)
            else:
                add("logdiff")
                walk(b)
                walk(ex)
        elif isinstance(e, sp.Function):
            fn = e.func
            if fn in (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc):
                add("trig")
            elif fn == sp.exp:
                add("exp")
            elif fn == sp.log:
                add("log")
            elif fn in (sp.asin, sp.acos, sp.atan):
                add("invtrig")
            else:
                add("other")
            for t in e.args:
                if t.has(x) and t != x:
                    add("chain")
                walk(t)
        else:
            add("other")
    try:
        walk(f)
    except Exception:
        pass
    order = ["sum", "const", "power", "prod", "quot", "chain", "trig", "exp", "log", "invtrig",
             "logdiff", "other"]
    return [k for k in order if k in found]


def _analyze(P):
    key = _key("deriv", P)
    if key in _CACHE:
        return _CACHE[key]
    x, f = _parse(P.get("f", "x"))
    A = {"ok": f is not None, "x": x, "f": f, "raw": str(P.get("f", "")), "vn": str(x)}
    A["fx"] = _pretty(_clean(A["raw"])) if f is not None else A["raw"].replace("{", "(").replace("}", ")")
    x0 = _sval(P.get("x0", 1))
    if not _finite(x0):
        x0 = sp.Integer(0)
    A["x0"], A["x0f"] = x0, _fl(x0)
    A["at"] = _at(x0)
    if f is None:
        _CACHE[key] = A
        return A
    h = _num(f, x)
    A["h"] = h
    d = None
    try:
        d = sp.diff(f, x)
        if d.has(sp.Derivative) or d.has(sp.Subs):
            d = None
    except Exception:
        d = None
    ds = None
    if d is not None:
        try:
            if d.is_polynomial(x):
                ds = sp.expand(d)
            elif d.is_rational_function(x):
                ds = sp.factor(sp.together(d))
            else:
                ds = d
                s2 = _simp(d)
                if len(sp.sstr(s2)) < 0.6 * len(sp.sstr(d)):
                    ds = s2
        except Exception:
            ds = d
    A["d"] = ds
    if ds is not None:
        A["dh"] = _num(ds, x)
    else:
        def dh(v, _h=h):
            v = np.asarray(v, dtype=float)
            e = 1e-5 * (1 + np.abs(v))
            return (_h(v + e) - _h(v - e)) / (2 * e)
        A["dh"] = dh
    x0f = A["x0f"]
    y0 = None
    try:
        v = f.subs(x, x0)
        if _finite(v):
            y0 = _simp(v)
    except Exception:
        y0 = None
    if y0 is None:
        v = _h1(h, x0f)
        if v == v:
            y0 = sp.Float(v, 10)
    A["y0"] = y0
    hh = 1e-6 * (1 + abs(x0f))
    fy = _h1(h, x0f)
    dl = (fy - _h1(h, x0f - hh)) / hh
    dr = (_h1(h, x0f + hh) - fy) / hh
    A["dl"], A["dr"] = dl, dr
    smooth = (fy == fy and dl == dl and dr == dr and
              abs(dl - dr) <= 1e-2 * (1 + abs(dl) + abs(dr)))
    m = None
    if smooth and ds is not None:
        try:
            v = ds.subs(x, x0)
            if _finite(v):
                m = _simp(v)
            elif abs(dl) > 1e6:
                smooth = False
        except Exception:
            m = None
    if smooth and m is None:
        m = sp.Float(0.5 * (dl + dr), 8)
    A["m"] = m
    A["smooth"] = smooth and y0 is not None
    A["tan"] = None
    A["tans"] = ""
    if m is not None and y0 is not None:
        b = _simp(y0 - m * x0)
        A["tan"] = sp.expand(m * x + b)
        ts = _ps(A["tan"])
        if len(ts) > 28 or A["tan"].has(sp.Float):
            mf_, bf_ = _fl(m), _fl(b)
            ts = f"{_g(mf_, 5)}{str(x)} {'−' if bf_ < 0 else '+'} {_g(abs(bf_), 5)}"
            A["tans"] = "≈ " + ts
        else:
            A["tans"] = "= " + ts
    A["rules"] = _rules(f, x)
    dq = None
    try:
        if f.is_polynomial(x) and sp.degree(f, x) <= 4 and y0 is not None:
            hs = sp.Symbol("h")
            dq = sp.expand(sp.cancel((f.subs(x, x0 + hs) - y0) / hs))
    except Exception:
        dq = None
    A["dq"] = dq
    A["sec"] = [(t, (_h1(h, x0f + t) - _h1(h, x0f)) / t) for t in (1.0, 0.1, 0.01, 0.001)]
    A["tex"] = _texf(f, A["fx"])
    _CACHE[key] = A
    return A


def solve(P):
    A = _analyze(P)
    vn = A["vn"]
    fmt = {"fx": A["fx"], "pretty_f": A["fx"], "x0": A["at"]}
    if not A["ok"]:
        return {"answer": ("İfade çözümlenemedi", "Could not parse the expression"),
                "steps": [(f"Girdi: {A['raw']}", f"Input: {A['raw']}"),
                          ("İfadeyi x değişkeniyle, * ve ** kullanarak yazın.",
                           "Write the expression in x using * and **.")], "fmt": fmt}
    at, d, m, y0 = A["at"], A["d"], A["m"], A["y0"]
    st = [(f"f({vn}) = {A['fx']}", f"f({vn}) = {A['fx']}")]
    if A["rules"]:
        st.append(("Kullanılan kurallar: " + " • ".join(_RULES[k][0] for k in A["rules"]),
                   "Rules used: " + " • ".join(_RULES[k][1] for k in A["rules"])))
    dtxt = _ps(d) if d is not None else _T(P, "(sayısal)", "(numerical)")
    if d is not None:
        st.append((f"Türev: f'({vn}) = {dtxt}", f"Derivative: f'({vn}) = {dtxt}"))
        fmt["dfx"] = dtxt
    else:
        st.append(("Sembolik türev bulunamadı; eğim sayısal olarak (merkezî fark) hesaplandı.",
                   "No symbolic derivative; the slope is computed numerically (central difference)."))
        fmt["dfx"] = "f'"
    if y0 is None:
        st.append((f"f({at}) tanımsız: {vn} = {at} tanım kümesinde değil, teğet yok.",
                   f"f({at}) is undefined: {vn} = {at} is outside the domain, no tangent line."))
        return {"answer": (f"f'({vn}) = {dtxt};  {vn} = {at} noktasında f tanımsız",
                           f"f'({vn}) = {dtxt};  f is undefined at {vn} = {at}"), "steps": st, "fmt": fmt}
    if A["dq"] is not None and m is not None:
        q = _ps(A["dq"]).replace("h", "h")
        st.append((f"Tanımdan: [f({at} + h) − f({at})]/h = {q}  →  h → 0 iken {_ex(m)}",
                   f"From the definition: [f({at} + h) − f({at})]/h = {q}  →  as h → 0: {_ex(m)}"))
    secs = ", ".join(f"h = {_g(t)}: {_g(s, 6)}" for t, s in A["sec"][:3])
    st.append((f"Kesen eğimleri [f({at} + h) − f({at})]/h:  {secs}  → h küçüldükçe teğet eğimine yaklaşır",
               f"Secant slopes [f({at} + h) − f({at})]/h:  {secs}  → they approach the tangent slope as h shrinks"))
    if not A["smooth"] or m is None:
        st.append((f"Soldan eğim ≈ {_g(A['dl'], 5)}, sağdan eğim ≈ {_g(A['dr'], 5)}: eşit değil ⇒ "
                   f"f, {vn} = {at} noktasında türevlenemez (köşe/dik teğet).",
                   f"Left slope ≈ {_g(A['dl'], 5)}, right slope ≈ {_g(A['dr'], 5)}: not equal ⇒ "
                   f"f is not differentiable at {vn} = {at} (corner/vertical tangent)."))
        return {"answer": (f"f'({vn}) = {dtxt};  f, {vn} = {at} noktasında türevlenemez",
                           f"f'({vn}) = {dtxt};  f is not differentiable at {vn} = {at}"),
                "steps": st, "fmt": fmt}
    st.append((f"f({at}) = {_ex(y0)},  f'({at}) = {_ex(m)}  (teğetin eğimi)",
               f"f({at}) = {_ex(y0)},  f'({at}) = {_ex(m)}  (slope of the tangent)"))
    tl = A["tans"]
    st.append((f"Teğet: y − {_short(y0)} = {_short(m)}·({vn} − {_short(A['x0'])})  ⇒  y {tl}",
               f"Tangent: y − {_short(y0)} = {_short(m)}·({vn} − {_short(A['x0'])})  ⇒  y {tl}"))
    fmt["tangent"] = "y " + tl
    ans = (f"f'({vn}) = {dtxt};  f'({at}) = {_ex(m)};  teğet: y {tl}",
           f"f'({vn}) = {dtxt};  f'({at}) = {_ex(m)};  tangent: y {tl}")
    return {"answer": ans, "steps": st, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    A = _analyze(P)
    if not A["ok"]:
        return _badfig(fig, P, _T(P, "İfade çözümlenemedi", "Could not parse the expression"))
    h, dh, x0f, vn = A["h"], A["dh"], A["x0f"], A["vn"]
    if "xmin" in P and "xmax" in P and float(P["xmin"]) < x0f < float(P["xmax"]):
        xa, xb = float(P["xmin"]), float(P["xmax"])
    elif abs(x0f) <= 6:
        xa, xb = min(-3.0, x0f - 2.0), max(3.0, x0f + 2.0)
    else:
        xa, xb = x0f - 3.0, x0f + 3.0
    xs = np.linspace(xa, xb, 601)
    ys = h(xs)
    fin = np.nonzero(np.isfinite(ys))[0]
    if len(fin) > 20 and not ("xmin" in P and "xmax" in P):
        ia, ib = fin[0], fin[-1]
        if xs[ia] < x0f < xs[ib] and (ib - ia) < 590:
            xa, xb = xs[ia], xs[ib]
            xs = np.linspace(xa, xb, 601)
            ys = h(xs)
    dys = dh(xs)
    y0f = _fl(A["y0"]) if A["y0"] is not None else float("nan")
    mf = _fl(A["m"]) if A["m"] is not None else float("nan")
    ok = A["smooth"] and A["m"] is not None

    def clip(vals, extra):
        lo_, hi_ = _yr(vals, extra)
        near = np.abs(xs - x0f) <= 0.25 * (xb - xa)
        lv = vals[near]
        lv = lv[np.isfinite(lv)]
        if len(lv) > 5:
            l1, l2 = _yr(lv, extra, pad=0.0)
            if hi_ - lo_ > 3.2 * (l2 - l1 + 1e-9):
                c, r = 0.5 * (l1 + l2), (l2 - l1 + 1e-9)
                lo_, hi_ = max(lo_, c - 1.1 * r), min(hi_, c + 1.1 * r)
        return lo_, hi_
    lo, hi = clip(ys, [y0f])
    dlo, dhi = clip(dys, [mf, 0.0])
    gs = fig.add_gridspec(2, 1, height_ratios=[1.75, 1], left=0.085, right=0.98, top=0.93,
                          bottom=0.08, hspace=0.3)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[1, 0], sharex=ax)
    ax.set_xlim(xa, xb)
    ax.set_ylim(lo, hi)
    bx.set_ylim(dlo, dhi)
    _axes_style(ax)
    _axes_style(bx)
    bx.set_xlabel(vn, fontsize=10)
    ax.set_title(_mt(f"f({vn}) = " + sp.latex(A["f"]), "f(" + vn + ") = " + A["fx"]), fontsize=12)
    dlab = _mt(f"f'({vn}) = " + sp.latex(A["d"]), "f'(" + vn + ") = " + (_ps(A["d"]) if A["d"] is not None else "?")) \
        if A["d"] is not None else "f'(" + vn + ")"
    bx.text(0.01, 0.95, dlab, transform=bx.transAxes, fontsize=10.5, va="top", color=PURPLE,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85), zorder=20)
    yb = _brk(ys, hi - lo)
    dyb = _brk(dys, dhi - dlo)
    curve, = ax.plot([], [], color=BLUE, lw=2.4, zorder=3)
    pdot, = ax.plot([], [], "o", color=RED, ms=9, zorder=7)
    qdot, = ax.plot([], [], "o", color=ORANGE, ms=8, zorder=7)
    sec, = ax.plot([], [], color=ORANGE, lw=1.8, zorder=4)
    hbr, = ax.plot([], [], color=ORANGE, lw=1.2, ls=":", zorder=4)
    tan, = ax.plot([], [], color=RED, lw=2.0, zorder=5)
    mtan, = ax.plot([], [], color=GREEN, lw=2.6, zorder=6)
    mdot, = ax.plot([], [], "o", color=GREEN, ms=7, zorder=7)
    yend = _h1(h, xb - 0.02 * (xb - xa))
    tlow = not (yend == yend and yend < 0.5 * (lo + hi))
    tlab = ax.text(0.98, 0.04 if tlow else 0.96, "", transform=ax.transAxes, color=RED, fontsize=11,
                   fontweight="bold", zorder=9, ha="right", va="bottom" if tlow else "top",
                   bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    dcurve, = bx.plot([], [], color=PURPLE, lw=2.2, zorder=3)
    ddot, = bx.plot([], [], "o", color=GREEN, ms=7, zorder=6)
    dmark, = bx.plot([], [], "o", color=RED, ms=9, zorder=7)
    dvl, = bx.plot([], [], ":", color=RED, lw=1.2)
    dlab2 = bx.text(0, 0, "", color=RED, fontsize=10.5, fontweight="bold", zorder=9,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    info = _info(ax, 10.5, xs, ys)
    rgt, lft = xb - x0f, x0f - xa
    okr = _h1(h, x0f + 0.5 * rgt) == _h1(h, x0f + 0.5 * rgt)
    okl = _h1(h, x0f - 0.5 * lft) == _h1(h, x0f - 0.5 * lft)
    sgn = 1.0 if (okr and (rgt >= lft or not okl)) else -1.0
    room = rgt if sgn > 0 else lft
    h0, h1 = 0.85 * room, 0.004 * (xb - xa)
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    seg = 0.12 * (xb - xa)
    N = 160

    def update(i):
        p = _ramp(i, 0, 18)
        m_ = max(2, int(p * len(xs)))
        curve.set_data(xs[:m_], yb[:m_])
        if i >= 10 and y0f == y0f:
            pdot.set_data([x0f], [y0f])
        else:
            pdot.set_data([], [])
        q = _ramp(i, 20, 78)
        if 20 <= i < 96 and y0f == y0f:
            hv = sgn * h0 * (h1 / h0) ** q
            yq = _h1(h, x0f + hv)
            if yq == yq:
                ms = (yq - y0f) / hv
                qdot.set_data([x0f + hv], [yq])
                sec.set_data([xa, xb], [y0f + ms * (xa - x0f), y0f + ms * (xb - x0f)])
                hbr.set_data([x0f, x0f + hv, x0f + hv], [y0f, y0f, yq])
            else:
                ms = float("nan")
                qdot.set_data([], [])
                sec.set_data([], [])
                hbr.set_data([], [])
            if i < 78:
                info.set_text(_T(P, f"1) Kesen: P({A['at']}, f({A['at']})) ve Q({A['at']} + h, f({A['at']} + h))\n"
                                    f"h = {_g(hv, 3)},  eğim = {_g(ms, 5)}",
                                 f"1) Secant through P and Q = ({A['at']} + h, f({A['at']} + h))\n"
                                 f"h = {_g(hv, 3)},  slope = {_g(ms, 5)}"))
        else:
            qdot.set_data([], [])
            sec.set_data([], [])
            hbr.set_data([], [])
        if i >= 78 and ok:
            r = _ramp(i, 78, 92)
            L2 = (xb - xa) * r
            tan.set_data([x0f - L2, x0f + L2], [y0f - mf * L2, y0f + mf * L2])
            tlab.set_text(_T(P, "teğet: ", "tangent: ") + sol["fmt"].get("tangent", ""))
        else:
            tan.set_data([], [])
            tlab.set_text("")
        if 78 <= i < 96:
            if ok:
                info.set_text(_T(P, f"2) h → 0: kesen teğete dönüşür\nf'({A['at']}) = {_short(A['m'])}",
                                 f"2) h → 0: the secant becomes the tangent\nf'({A['at']}) = {_short(A['m'])}"))
            else:
                info.set_text(_T(P, f"2) {vn} = {A['at']} noktasında teğet yok\n(sol ve sağ eğimler farklı)",
                                 f"2) No tangent at {vn} = {A['at']}\n(left and right slopes differ)"))
        u = _ramp(i, 96, 146)
        if i >= 96:
            k = max(2, int(u * len(xs)))
            dcurve.set_data(xs[:k], dyb[:k])
            xt = xs[k - 1]
            yt, st_ = _h1(h, xt), _h1(dh, xt)
            if yt == yt and st_ == st_ and i < 148:
                mtan.set_data([xt - seg, xt + seg], [yt - st_ * seg, yt + st_ * seg])
                mdot.set_data([xt], [yt])
                ddot.set_data([xt], [st_])
            else:
                mtan.set_data([], [])
                mdot.set_data([], [])
                ddot.set_data([], [])
            if i < 148:
                info.set_text(_T(P, f"3) Her noktadaki teğet eğimi f'({vn}) grafiğini çizer\n"
                                    f"{vn} = {_g(xt, 3)}:  eğim = {_g(st_, 4)}",
                                 f"3) The tangent slope at every point draws f'({vn})\n"
                                 f"{vn} = {_g(xt, 3)}:  slope = {_g(st_, 4)}"))
        else:
            dcurve.set_data([], [])
            mtan.set_data([], [])
            mdot.set_data([], [])
            ddot.set_data([], [])
        if i >= 148 and ok:
            dmark.set_data([x0f], [mf])
            dvl.set_data([x0f, x0f], [dlo, mf])
            dlab2.set_position((x0f + 0.02 * (xb - xa), mf + 0.05 * (dhi - dlo)))
            dlab2.set_text(f"f'({A['at']}) = {_short(A['m'])}")
        else:
            dmark.set_data([], [])
            dvl.set_data([], [])
            dlab2.set_text("")
        if i >= 148:
            info.set_text("4) " + ans.replace(";  ", "\n"))
        elif i < 20:
            info.set_text(_T(P, f"0) f({vn}) grafiği ve P({A['at']}, f({A['at']})) noktası",
                             f"0) Graph of f({vn}) and the point P({A['at']}, f({A['at']}))"))
        return []

    return N, update


def vary(P, rnd):
    x, f = _parse(P.get("f", "x"))
    vn = str(x)
    raw = str(P.get("f", "")).lower()
    out = {}
    if "sqrt" in raw:
        k, x0 = rnd.choice([(3, 4), (4, 3), (5, 12), (12, 5), (6, 8), (8, 6), (8, 15)])
        out = {"f": f"sqrt({vn}**2 + {k * k})", "x0": x0}
    elif ("xmin" in P or "xmax" in P) and float(P.get("xmin", -1)) >= 0:
        a = rnd.choice([2, 3, 4, 5])
        T = rnd.choice([3, 4, 5, 6])
        b = a * T
        x0 = rnd.randint(1, T - 1)
        out = {"f": f"-{a}*{vn}**2 + {b}*{vn}", "x0": x0, "xmin": 0, "xmax": T}
    else:
        z = sp.Symbol(vn)
        while True:
            c3 = rnd.choice([0, 1, 1, -1])
            c2 = rnd.choice([-3, -2, -1, 0, 1, 2, 3])
            c1 = rnd.choice([-6, -4, -3, -2, 2, 3, 4, 5])
            c0 = rnd.randint(-4, 4)
            if c3 == 0 and c2 == 0:
                continue
            poly = sp.expand(c3 * z ** 3 + c2 * z ** 2 + c1 * z + c0)
            break
        out = {"f": sp.sstr(poly), "x0": rnd.choice([-2, -1, 1, 2, 3])}
    for k2, v2 in P.items():
        if k2 not in out and k2 not in ("f", "x0", "xmin", "xmax", "lang"):
            out[k2] = v2
    return out
'''),
}
EXAMPLES += [
    {"id": "calc1-deriv-1", "kind": "derivative_expr",
     "title": ("Kesenden teğete: kübik fonksiyon", "From secant to tangent: a cubic"),
     "q": ("f(x) = {pretty_f} için f'(x)'i bul ve x = {x0} noktasındaki teğet doğrusunun denklemini yaz.",
           "For f(x) = {pretty_f}, find f'(x) and the equation of the tangent line at x = {x0}."),
     "P": {"f": "x**3 - 3*x", "x0": 2, "xmin": -2.5, "xmax": 3}},
    {"id": "calc1-deriv-2", "kind": "derivative_expr",
     "topics": ["velocity", "hız", "position", "konum", "word problem", "sözel problem"],
     "title": ("Anlık hız: yukarı atılan top", "Instantaneous velocity: a ball thrown upward"),
     "q": ("Yukarı atılan bir topun yüksekliği s(t) = {pretty_f} metredir (t saniye). "
           "t = {x0} s anındaki hızı türevle bul ve kesen eğimlerinin buna yaklaştığını göster.",
           "A ball thrown upward has height s(t) = {pretty_f} metres (t in seconds). "
           "Use the derivative to find its velocity at t = {x0} s and show the secant slopes approach it."),
     "P": {"f": "-5*t**2 + 20*t", "x0": 1, "xmin": 0, "xmax": 4}},
    {"id": "calc1-deriv-3", "kind": "derivative_expr", "topics": ["chain rule", "zincir kuralı"],
     "title": ("Zincir kuralı ile teğet", "Tangent line with the chain rule"),
     "q": ("f(x) = {pretty_f} fonksiyonunun türevini zincir kuralıyla bul; x = {x0} noktasındaki teğeti yaz.",
           "Differentiate f(x) = {pretty_f} with the chain rule and write the tangent line at x = {x0}."),
     "P": {"f": "sqrt(x**2 + 9)", "x0": 4}},
]


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["integral_expr"] = {
    "course": "calc1",
    "title": ("Belirli integral: işaretli alan", "Definite integral: signed area"),
    "topics": ["integral", "integrals", "definite integral", "fundamental theorem of calculus",
               "antiderivative", "antiderivatives", "area under the curve", "area under a curve",
               "net area", "signed area", "net change", "evaluating definite integrals",
               "integration", "belirli integral", "ters türev", "eğri altındaki alan",
               "kalkülüsün temel teoremi", "temel teorem", "net alan", "işaretli alan", "integral"],
    "code": _code(r'''


_BADF = (sp.Integral, sp.hyper, sp.meijerg, sp.exp_polar)


def _antider(f, x):
    G = None
    try:
        G = sp.integrate(f, x, manual=True)
        if G.has(*_BADF):
            G = None
    except Exception:
        G = None
    if G is None:
        try:
            if sp.count_ops(f) <= 30:
                G = sp.integrate(f, x)
                if G.has(*_BADF):
                    G = None
        except Exception:
            G = None
    return G


def _Fat(F, x, v, side):
    try:
        r = F.subs(x, v)
        if _finite(r):
            return r
    except Exception:
        pass
    try:
        r = sp.limit(F, x, v, dir=side)
        if _finite(r):
            return r
    except Exception:
        pass
    return None


def _nice(z):
    try:
        q = sp.nsimplify(z, tolerance=1e-10, rational=True)
        if q.is_Rational and q.q <= 100 and abs(_fl(q) - z) < 1e-9:
            return q
        q = sp.nsimplify(z, [sp.pi, sp.sqrt(2), sp.sqrt(3), sp.sqrt(5)], tolerance=1e-11)
        if sp.count_ops(q) <= 4 and abs(_fl(q) - z) < 1e-9:
            return q
    except Exception:
        pass
    return None


def _bnd(e):
    if e == sp.oo:
        return "∞"
    if e == -sp.oo:
        return "−∞"
    return _at(e)


def _isym(a, b):
    sa, sb = _bnd(a).replace("−", "-"), _bnd(b).replace("−", "-")
    sub = dict(zip("0123456789-", "₀₁₂₃₄₅₆₇₈₉₋"))
    if all(c in sub for c in sa) and all(c in _SUP for c in sb):
        return "∫" + "".join(sub[c] for c in sa) + "".join(_SUP[c] for c in sb)
    return f"∫[{_bnd(a)}, {_bnd(b)}]"


def _analyze(P):
    key = _key("integral", P)
    if key in _CACHE:
        return _CACHE[key]
    x, f = _parse(P.get("f", "x"))
    A = {"ok": f is not None, "x": x, "f": f, "raw": str(P.get("f", "")), "vn": str(x)}
    A["fx"] = _pretty(_clean(A["raw"])) if f is not None else A["raw"].replace("{", "(").replace("}", ")")
    a, b = _sval(P.get("a", 0)), _sval(P.get("b", 1))
    if a == b:
        b = a + 1
    A["a"], A["b"] = a, b
    A["sa"], A["sb"] = _bnd(a), _bnd(b)
    A["isym"] = _isym(a, b)
    if f is None:
        _CACHE[key] = A
        return A
    h = _num(f, x)
    A["h"] = h
    af, bf = _fl(a), _fl(b)
    inf = not (_finite(a) and _finite(b))
    A["inf"] = inf
    # finite plotting interval (an infinite bound is cut off for the picture)
    pa = af if _finite(a) else (bf - max(10.0, 3 * abs(bf)) if _finite(b) else -10.0)
    pb = bf if _finite(b) else (af + max(10.0, 3 * abs(af)) if _finite(a) else 10.0)
    A["pa"], A["pb"] = pa, pb
    lo_, hi_ = min(pa, pb), max(pa, pb)
    xs = np.linspace(lo_, hi_, 4001)
    ys = h(xs)
    bad = ~np.isfinite(ys)
    nanfrac = float(np.mean(bad))
    A["undef"] = nanfrac > 0.02
    inner = bool(np.any(bad[1:-1]))
    poles = []
    for c in ([] if A["undef"] else _poles(h, lo_, hi_)):
        if not poles or abs(c - poles[-1]) > 1e-6 * (1 + abs(c)):
            poles.append(c)
    A["poles"] = poles
    A["improper"] = inf or inner or bool(poles)
    A["endnan"] = bool(bad[0] or bad[-1])
    F = _antider(f, x)
    A["F"] = F
    val, how = None, ""
    if F is not None and not A["improper"]:
        Fb, Fa = _Fat(F, x, b, "-"), _Fat(F, x, a, "+")
        if Fb is not None and Fa is not None:
            val = _simp(Fb - Fa)
            A["Fa"], A["Fb"] = _simp(Fa), _simp(Fb)
            how = "ftc"
            nchk = _quad(h, af, bf)
            if nchk == nchk and abs(_fl(val) - nchk) > 1e-4 * (1 + abs(nchk)):
                val, how = None, ""
    if val is None and (A["improper"] or F is None) and not A["undef"]:
        try:
            if sp.count_ops(f) <= 30:
                r = sp.integrate(f, (x, a, b))
                if not r.has(*_BADF):
                    if r in (sp.oo, -sp.oo, sp.zoo, sp.nan) or not _finite(r):
                        how = "div"
                    else:
                        val, how = _simp(r), ("improper" if A["improper"] else "sympy")
        except Exception:
            pass
    nval = float("nan")
    if not A["improper"]:
        nval = _quad(h, af, bf)
    A["nval"] = nval
    if val is None and how != "div" and nval == nval:
        how = "num"
    if val is None and how == "" and A["improper"] and not A["undef"]:
        how = "div?"
    A["val"], A["how"] = val, how
    vf = _fl(val) if val is not None else nval
    A["vf"] = vf
    # sign changes and signed parts
    zs = [] if (A["undef"]) else [z for z in _zeros(h, lo_, hi_) if lo_ + 1e-9 < z < hi_ - 1e-9]
    pts = [lo_] + zs + [hi_]
    parts = []
    Fh = _num(F, x) if F is not None else None
    for k in range(len(pts) - 1):
        u, w = pts[k], pts[k + 1]
        ex_ = None
        if F is not None and not A["improper"]:
            nu = a if k == 0 else _nice(u)
            nw = b if k == len(pts) - 2 else _nice(w)
            if af > bf:
                nu = b if k == 0 else _nice(u)
                nw = a if k == len(pts) - 2 else _nice(w)
            if nu is not None and nw is not None:
                Fu, Fw = _Fat(F, x, nu, "+"), _Fat(F, x, nw, "-")
                if Fu is not None and Fw is not None:
                    ex_ = _simp(Fw - Fu)
        num_ = _quad(h, u, w, 2000) if not A["improper"] else float("nan")
        parts.append((u, w, ex_, num_ if ex_ is None else _fl(ex_)))
    A["zeros"], A["parts"] = zs, parts
    if af > bf:
        A["total"] = sum(abs(p[3]) for p in parts)
    else:
        A["total"] = sum(abs(p[3]) for p in parts)
    tex_ok = all(p[2] is not None for p in parts)
    A["total_ex"] = sum(abs(p[2]) for p in parts) if tex_ok and parts else None
    A["tex"] = _texf(f, A["fx"])
    _CACHE[key] = A
    return A


def _impr(A):
    if A.get("inf"):
        return ("Aralık sonsuz", "The interval is infinite")
    if A.get("poles"):
        ps = ", ".join(_at(_nice(c)) if _nice(c) is not None else _g(c, 5) for c in A["poles"])
        return (f"f, {A['vn']} = {ps} noktasında sınırsız (dikey asimptot)",
                f"f is unbounded at {A['vn']} = {ps} (vertical asymptote)")
    return ("f aralığın içinde tanımsız bir noktaya sahip", "f is undefined at a point inside the interval")


def solve(P):
    A = _analyze(P)
    vn = A["vn"]
    fmt = {"fx": A["fx"], "pretty_f": A["fx"], "a": A["sa"], "b": A["sb"], "int": A["isym"]}
    if not A["ok"]:
        return {"answer": ("İfade çözümlenemedi", "Could not parse the expression"),
                "steps": [(f"Girdi: {A['raw']}", f"Input: {A['raw']}"),
                          ("İfadeyi x değişkeniyle, * ve ** kullanarak yazın.",
                           "Write the expression in x using * and **.")], "fmt": fmt}
    I = A["isym"]
    fxp = f"({A['fx']})" if A["f"].is_Add else A["fx"]
    st = [(f"İstenen: {I} {fxp} d{vn}", f"Find: {I} {fxp} d{vn}")]
    F, how, val = A["F"], A["how"], A["val"]
    if A["undef"]:
        st.append((f"f, [{A['sa']}, {A['sb']}] aralığının bir kısmında reel değerli değil (tanımsız).",
                   f"f is not real-valued on part of [{A['sa']}, {A['sb']}] (undefined there)."))
        return {"answer": ("İntegral tanımsız: f aralığın bir kısmında tanımlı değil",
                           "The integral is undefined: f is not defined on all of the interval"),
                "steps": st, "fmt": fmt}
    if F is not None:
        Fs = _ps(F)
        hint = ("  (kuvvet kuralı: ∫xⁿ dx = xⁿ⁺¹/(n + 1))", "  (power rule: ∫xⁿ dx = xⁿ⁺¹/(n + 1))") \
            if A["f"].is_polynomial(A["x"]) else ("", "")
        st.append((f"Ters türev: F({vn}) = {Fs}{hint[0]}", f"Antiderivative: F({vn}) = {Fs}{hint[1]}"))
        fmt["F"] = Fs
    else:
        st.append(("Ters türev elemanter (kapalı) biçimde bulunamadı → sayısal yöntem.",
                   "No closed-form antiderivative was found → numerical method."))
    if how == "ftc" and A.get("endnan"):
        st.append(("f bir uç noktada tanımsız; F'nin o uçtaki değeri tek taraflı limitle alınır.",
                   "f is undefined at an endpoint; F there is taken as a one-sided limit."))
    if how == "ftc":
        st.append((f"Temel teorem: {I} f d{vn} = F({A['sb']}) − F({A['sa']}) = ({_ex(A['Fb'])}) − ({_ex(A['Fa'])}) = {_ex(val)}",
                   f"Fundamental theorem: {I} f d{vn} = F({A['sb']}) − F({A['sa']}) = ({_ex(A['Fb'])}) − ({_ex(A['Fa'])}) = {_ex(val)}"))
    elif how in ("improper", "sympy"):
        why = _impr(A)
        st.append((f"{why[0]} ⇒ genelleştirilmiş integral (limit ile) = {_ex(val)}",
                   f"{why[1]} ⇒ improper integral (as a limit) = {_ex(val)}"))
    elif how in ("div", "div?"):
        why = _impr(A)
        st.append((f"{why[0]} ve limit sonlu değil ⇒ integral ıraksar.",
                   f"{why[1]} and the limit is not finite ⇒ the integral diverges."))
        return {"answer": ("İntegral ıraksak (sonlu bir değeri yok)", "The integral diverges (no finite value)"),
                "steps": st, "fmt": fmt}
    elif how == "num":
        st.append((f"Simpson kuralı (n = 4000): {I} f d{vn} ≈ {_g(A['nval'], 8)}",
                   f"Simpson's rule (n = 4000): {I} f d{vn} ≈ {_g(A['nval'], 8)}"))
    vtxt = _ex(val) if val is not None else "≈ " + _g(A["vf"], 7)
    eq = "= " + vtxt if val is not None else vtxt
    fxp = f"({A['fx']})" if A["f"].is_Add else A["fx"]
    parts = A["parts"]
    if len(parts) > 1 and not A["improper"]:
        zt = ", ".join(_at(_nice(z)) if _nice(z) is not None else _g(z, 6) for z in A["zeros"])
        pt = "; ".join(f"[{_g(u, 4)}, {_g(w, 4)}]: {_ex(e) if e is not None else _g(n_, 6)}" for u, w, e, n_ in parts)
        tot = _ex(A["total_ex"]) if A["total_ex"] is not None else _g(A["total"], 6)
        st.append((f"f, {vn} = {zt} noktasında işaret değiştirir. Parçalar: {pt}",
                   f"f changes sign at {vn} = {zt}. Pieces: {pt}"))
        st.append((f"Eksenin üstü pozitif, altı negatif sayılır: net (işaretli) alan = {vtxt}, toplam (geometrik) alan = {tot}",
                   f"Area above the axis counts positive, below negative: net (signed) area = {vtxt}, total (geometric) area = {tot}"))
        fmt["total"] = tot
    elif not A["improper"]:
        sg = "≥" if A["vf"] >= 0 else "≤"
        st.append((f"[{A['sa']}, {A['sb']}] üzerinde f {sg} 0 ⇒ integral, eğri ile {vn} ekseni arasındaki alanın {'kendisidir' if A['vf'] >= 0 else 'negatifidir'}.",
                   f"On [{A['sa']}, {A['sb']}], f {sg} 0 ⇒ the integral is {'the area' if A['vf'] >= 0 else 'minus the area'} between the curve and the {vn}-axis."))
    if how == "ftc" and A["nval"] == A["nval"]:
        st.append((f"Sayısal kontrol (Simpson): ≈ {_g(A['nval'], 8)} ✓", f"Numerical check (Simpson): ≈ {_g(A['nval'], 8)} ✓"))
    fmt["value"] = vtxt
    ans = (f"{I} {fxp} d{vn} {eq}", f"{I} {fxp} d{vn} {eq}")
    if len(parts) > 1 and not A["improper"]:
        ans = (ans[0] + f"  (toplam alan {fmt['total']})", ans[1] + f"  (total area {fmt['total']})")
    return {"answer": ans, "steps": st, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    A = _analyze(P)
    if not A["ok"]:
        return _badfig(fig, P, _T(P, "İfade çözümlenemedi", "Could not parse the expression"))
    h, pa, pb, vn = A["h"], A["pa"], A["pb"], A["vn"]
    lo_, hi_ = min(pa, pb), max(pa, pb)
    pad = max(0.5, 0.15 * (hi_ - lo_))
    X = np.linspace(lo_ - pad, hi_ + pad, 700)
    Y = h(X)
    ylo, yhi = _yr(Y, [0.0])
    gs = fig.add_gridspec(2, 1, height_ratios=[1.75, 1], left=0.085, right=0.98, top=0.93,
                          bottom=0.08, hspace=0.3)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[1, 0], sharex=ax)
    ax.set_xlim(X[0], X[-1])
    ax.set_ylim(ylo, yhi)
    _axes_style(ax)
    _axes_style(bx)
    bx.set_xlabel(vn, fontsize=10)
    ftex = sp.latex(A["f"])
    if A["f"].is_Add:
        ftex = r"\left(" + ftex + r"\right)"
    ax.set_title(_mt(r"\int_{" + sp.latex(A["a"]) + "}^{" + sp.latex(A["b"]) + "} " + ftex + r"\,d" + vn,
                     A["isym"] + " " + A["fx"] + " d" + vn), fontsize=12)
    T = np.linspace(pa, pb, 401)
    YT = h(T)
    # accumulation A(t) = ∫_a^t f
    Fh = _num(A["F"], A["x"]) if (A["F"] is not None and not A["improper"]) else None
    acc = None
    if Fh is not None:
        FT = Fh(T)
        if np.all(np.isfinite(FT)):
            acc = FT - FT[0]
            if A["val"] is not None and abs(acc[-1] - _fl(A["val"])) > 1e-6 * (1 + abs(acc[-1])):
                acc = None
    if acc is None:
        fine = np.linspace(pa, pb, 4001)
        yf = np.nan_to_num(h(fine), nan=0.0)
        yf = np.clip(yf, -1e6, 1e6)
        c = np.concatenate([[0.0], np.cumsum(0.5 * (yf[1:] + yf[:-1]) * np.diff(fine))])
        acc = np.interp(T, fine, c) if pa < pb else np.interp(T, fine[::-1], c[::-1])
    alo, ahi = _yr(acc, [0.0, A["vf"]])
    bx.set_ylim(alo, ahi)
    bx.text(0.01, 0.95, _T(P, f"A({vn}) = ∫ f :  [{A['sa']}, {vn}] üzerinde birikmiş alan",
                           f"A({vn}) = ∫ f :  area accumulated over [{A['sa']}, {vn}]"),
            transform=bx.transAxes, fontsize=10, va="top", color=PURPLE,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85), zorder=20)
    curve, = ax.plot([], [], color=BLUE, lw=2.4, zorder=4)
    Yb = _brk(Y, yhi - ylo)
    ax.axvline(pa, color=GRAY, ls=":", lw=1.2)
    ax.axvline(pb, color=GRAY, ls=":", lw=1.2)
    ax.text(pa, ylo + 0.02 * (yhi - ylo), " " + A["sa"], color=GRAY, fontsize=9)
    ax.text(pb, ylo + 0.02 * (yhi - ylo), " " + A["sb"], color=GRAY, fontsize=9)
    sweep, = ax.plot([], [], color=PURPLE, lw=1.6, zorder=5)
    sdot, = ax.plot([], [], "o", color=PURPLE, ms=7, zorder=6)
    acurve, = bx.plot([], [], color=PURPLE, lw=2.2)
    adot, = bx.plot([], [], "o", color=PURPLE, ms=7)
    aline, = bx.plot([], [], "--", color=GREEN, lw=1.5)
    alab = bx.text(0, 0, "", color=GREEN, fontsize=11, fontweight="bold", ha="right", va="bottom",
                   bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    plabs, ptxt = [], []
    for u, w, e, n_ in A["parts"]:
        mid = 0.5 * (u + w)
        ym = _h1(h, mid)
        if ym != ym:
            ym = 0.0
        ym = min(max(0.45 * ym, ylo + 0.1 * (yhi - ylo)), yhi - 0.1 * (yhi - ylo))
        txt = (("+" if n_ >= 0 else "") + (_short(e) if e is not None else _g(n_, 4))).replace("+−", "−")
        plabs.append(ax.text(mid, ym, "", ha="center", va="center", fontsize=11, fontweight="bold",
                             color=BLUE if n_ >= 0 else RED, zorder=8,
                             bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8)))
        ptxt.append(txt)
    inside = (X >= lo_) & (X <= hi_)
    info = _info(ax, 10.5, np.concatenate([X, X[inside], X[inside]]),
                 np.concatenate([Y, 0.5 * Y[inside], 0.15 * Y[inside]]))
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    Fs = sol["fmt"].get("F", "")
    fills = []
    N = 150

    def update(i):
        for c in fills:
            c.remove()
        del fills[:]
        p = _ramp(i, 0, 18)
        m = max(2, int(p * len(X)))
        curve.set_data(X[:m], Yb[:m])
        q = _ramp(i, 20, 100)
        k = int(round(q * (len(T) - 1)))
        if i >= 20 and k >= 1:
            xx, yy = T[:k + 1], np.nan_to_num(YT[:k + 1], nan=0.0)
            yy = np.clip(yy, ylo - (yhi - ylo), yhi + (yhi - ylo))
            fills.append(ax.fill_between(xx, 0, yy, where=yy >= 0, interpolate=True, color=BLUE,
                                         alpha=0.33, lw=0, zorder=2))
            fills.append(ax.fill_between(xx, 0, yy, where=yy <= 0, interpolate=True, color=RED,
                                         alpha=0.33, lw=0, zorder=2))
        if i >= 20:
            t = T[k]
            yt = YT[k] if YT[k] == YT[k] else 0.0
            sweep.set_data([t, t], [0, min(max(yt, ylo), yhi)])
            sdot.set_data([t], [yt])
            acurve.set_data(T[:k + 1], acc[:k + 1])
            adot.set_data([t], [acc[k]])
        else:
            sweep.set_data([], [])
            sdot.set_data([], [])
            acurve.set_data([], [])
            adot.set_data([], [])
        done = i >= 102
        for lab, txt in zip(plabs, ptxt):
            lab.set_text(txt if done and len(plabs) > 1 else "")
        if done:
            aline.set_data([pa, pb], [acc[-1], acc[-1]])
            alab.set_position((X[-1] - 0.01 * (X[-1] - X[0]), acc[-1]))
            alab.set_text(A["isym"] + " = " + (_short(A["val"]) if A["val"] is not None else _g(A["vf"], 5)))
        else:
            aline.set_data([], [])
            alab.set_text("")
        if i < 20:
            info.set_text(_T(P, f"1) f({vn}) ve [{A['sa']}, {A['sb']}] aralığı",
                             f"1) f({vn}) and the interval [{A['sa']}, {A['sb']}]"))
        elif not done:
            info.set_text(_T(P, f"2) Alan süpürülüyor: mavi +, kırmızı −\nA({_g(T[k], 3)}) = {_g(acc[k], 5)}",
                             f"2) Sweeping the area: blue +, red −\nA({_g(T[k], 3)}) = {_g(acc[k], 5)}"))
        elif i < 126 and Fs:
            info.set_text(_T(P, f"3) F({vn}) = {Fs}\nF({A['sb']}) − F({A['sa']})",
                             f"3) F({vn}) = {Fs}\nF({A['sb']}) − F({A['sa']})"))
        else:
            info.set_text(("4) " if Fs else "3) ") + ans.replace("  (", "\n("))
        return []

    return N, update


def vary(P, rnd):
    x, f = _parse(P.get("f", "x"))
    vn = str(x)
    z = sp.Symbol(vn)
    raw = str(P.get("f", "")).lower()
    out = {}
    change = False
    if f is not None:
        try:
            hh = _num(f, x)
            vv = hh(np.linspace(_fl(_sval(P.get("a", 0))), _fl(_sval(P.get("b", 1))), 200))
            change = bool(np.nanmin(vv) < 0 < np.nanmax(vv))
        except Exception:
            change = False
    if "sqrt" in raw:
        c = rnd.choice([0, 2, 5, 10, 12])
        k = rnd.choice([3, 6, 9]) if rnd.random() < 0.5 else rnd.choice([2, 4, 5])
        mm = rnd.choice([1, 2, 3, 4]) if k % 3 == 0 else 3
        expr = (f"{c} + " if c else "") + f"{k}*sqrt({vn})"
        out = {"f": expr, "a": 0, "b": mm * mm}
    elif change:
        r1 = rnd.randint(-2, 1)
        r2 = r1 + rnd.choice([2, 3, 4])
        a = r1 + rnd.choice([0, 1]) if rnd.random() < 0.5 else r1 - 1
        b = r2 + rnd.choice([1, 2])
        if a >= r2:
            a = r1
        out = {"f": sp.sstr(sp.expand((z - r1) * (z - r2))), "a": a, "b": b}
    else:
        c2 = rnd.choice([1, 2, 3])
        c1 = rnd.choice([0, 1, 2, 4])
        c0 = rnd.choice([0, 1, 3, 5])
        a = rnd.choice([0, 0, 1])
        b = a + rnd.choice([1, 2, 3])
        out = {"f": sp.sstr(sp.expand(c2 * z ** 2 + c1 * z + c0)), "a": a, "b": b}
    for k2, v2 in P.items():
        if k2 not in out and k2 not in ("f", "a", "b", "lang"):
            out[k2] = v2
    return out
'''),
}
EXAMPLES += [
    {"id": "calc1-integral-1", "kind": "integral_expr",
     "title": ("Parabol altındaki alan", "Area under a parabola"),
     "q": ("{int} {pretty_f} dx integralini temel teoremle hesapla ve eğri altındaki alan olarak yorumla.",
           "Evaluate {int} {pretty_f} dx with the fundamental theorem and interpret it as the area under the curve."),
     "P": {"f": "x**2", "a": 0, "b": 2}},
    {"id": "calc1-integral-2", "kind": "integral_expr", "topics": ["net area", "total area", "toplam alan"],
     "title": ("Net alan ve toplam alan", "Net area versus total area"),
     "q": ("f(x) = {pretty_f} için [{a}, {b}] aralığında belirli integrali (net alan) ve eğri ile x ekseni "
           "arasındaki toplam alanı bul.",
           "For f(x) = {pretty_f} on [{a}, {b}], find the definite integral (net area) and the total area "
           "between the curve and the x-axis."),
     "P": {"f": "x**2 - 2*x - 3", "a": 0, "b": 4}},
    {"id": "calc1-integral-3", "kind": "integral_expr",
     "topics": ["word problem", "sözel problem", "rate", "accumulation", "birikim", "net change theorem"],
     "title": ("Birikim: depoya akan su", "Accumulation: water flowing into a tank"),
     "q": ("Bir depoya su r(t) = {pretty_f} litre/dakika hızıyla akıyor (t dakika). t = {a} ile t = {b} "
           "arasında depoya kaç litre su girer?",
           "Water flows into a tank at r(t) = {pretty_f} litres per minute (t in minutes). How many litres "
           "enter the tank between t = {a} and t = {b}?"),
     "P": {"f": "10 + 4*sqrt(t)", "a": 0, "b": 9}},
]


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["extrema_expr"] = {
    "course": "calc1",
    "title": ("Ekstremumlar: artan/azalan, konkavlık, mutlak maks/min",
              "Extrema: increasing/decreasing, concavity, absolute max/min"),
    "topics": ["extrema", "extreme values", "critical points", "critical numbers", "local extrema",
               "relative extrema", "absolute extrema", "maximum and minimum", "first derivative test",
               "second derivative test", "increasing and decreasing", "concavity", "inflection point",
               "inflection points", "closed interval method", "curve sketching",
               "ekstremum", "kritik nokta", "yerel maksimum", "yerel minimum", "mutlak maksimum",
               "mutlak minimum", "artan azalan", "konkavlık", "büküm noktası", "birinci türev testi",
               "ikinci türev testi", "eğri çizimi"],
    "code": _code(r'''


def _roots_in(e, x, a, b, eh):
    # roots of e in the open interval (a, b): exact when sympy can, numeric otherwise
    out = []
    ok = False
    try:
        if e is not None and not e.is_zero:
            sol = sp.solveset(sp.Eq(e, 0), x, sp.Interval.open(a, b))
            if isinstance(sol, sp.FiniteSet):
                out = [(_simp(c), _fl(c)) for c in sol if _finite(c)]
                ok = True
    except Exception:
        ok = False
    if not ok:
        for z in _zeros(eh, _fl(a), _fl(b)):
            if _fl(a) < z < _fl(b):
                q = None
                try:
                    q = sp.nsimplify(z, tolerance=1e-10, rational=True)
                    if not (q.is_Rational and q.q <= 50 and abs(_fl(q) - z) < 1e-9):
                        q = None
                except Exception:
                    q = None
                out.append((q, z))
    out = sorted(out, key=lambda t: t[1])
    res = []
    for c, z in out:
        if not res or abs(z - res[-1][1]) > 1e-8 * (1 + abs(z)):
            res.append((c, z))
    return res[:12]


def _sgn(eh, u, w):
    ts = np.linspace(u, w, 9)[1:-1]
    v = eh(ts)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return 0
    m = float(np.median(v))
    return 1 if m > 1e-12 else (-1 if m < -1e-12 else 0)


def _analyze(P):
    key = _key("extrema", P)
    if key in _CACHE:
        return _CACHE[key]
    x, f = _parse(P.get("f", "x"))
    A = {"ok": f is not None, "x": x, "f": f, "raw": str(P.get("f", "")), "vn": str(x)}
    A["fx"] = _pretty(_clean(A["raw"])) if f is not None else A["raw"].replace("{", "(").replace("}", ")")
    a, b = _sval(P.get("a", -3)), _sval(P.get("b", 3))
    if not (_finite(a) and _finite(b)):
        a, b = sp.Integer(-3), sp.Integer(3)
    if _fl(a) > _fl(b):
        a, b = b, a
    if a == b:
        b = a + 1
    A["a"], A["b"], A["af"], A["bf"] = a, b, _fl(a), _fl(b)
    A["sa"], A["sb"] = _at(a), _at(b)
    if f is None:
        _CACHE[key] = A
        return A
    h = _num(f, x)
    A["h"] = h
    af, bf = A["af"], A["bf"]
    try:
        d = sp.diff(f, x)
        d2 = sp.diff(d, x)
        if d.has(sp.Derivative) or d2.has(sp.Derivative):
            raise ValueError
    except Exception:
        d = d2 = None
    if d is not None:
        dh, d2h = _num(d, x), _num(d2, x)
    else:
        def dh(v, _h=h):
            v = np.asarray(v, dtype=float)
            e = 1e-5 * (1 + np.abs(v))
            return (_h(v + e) - _h(v - e)) / (2 * e)

        def d2h(v, _h=h):
            v = np.asarray(v, dtype=float)
            e = 1e-4 * (1 + np.abs(v))
            return (_h(v + e) - 2 * _h(v) + _h(v - e)) / (e * e)
    A["dh"], A["d2h"] = dh, d2h

    def nice(e):
        if e is None:
            return None
        try:
            if e.is_polynomial(x):
                return sp.factor(e) if len(sp.sstr(sp.factor(e))) <= len(sp.sstr(sp.expand(e))) + 4 else sp.expand(e)
            if e.is_rational_function(x):
                return sp.factor(sp.together(e))
            s2 = _simp(e)
            return s2 if len(sp.sstr(s2)) < len(sp.sstr(e)) else e
        except Exception:
            return e
    A["d"], A["d2"] = nice(d), nice(d2)
    A["poles"] = _poles(h, af, bf)
    const = d is not None and d.is_zero
    A["const"] = const
    crit = [] if const else _roots_in(d, x, a, b, dh)
    # points where f' is undefined but f is defined (corners / cusps)
    try:
        if d is not None and not const:
            den = sp.denom(sp.together(d))
            if den.has(x):
                for c, z in _roots_in(den, x, a, b, _num(den, x)):
                    if _h1(h, z) == _h1(h, z) and all(abs(z - w) > 1e-9 for _, w in crit):
                        crit.append((c, z))
    except Exception:
        pass
    crit = sorted([t for t in crit if _h1(h, t[1]) == _h1(h, t[1])], key=lambda t: t[1])
    A["crit"] = crit
    # monotonic intervals
    pts = [af] + [z for _, z in crit] + [bf]
    mono = []
    for k in range(len(pts) - 1):
        mono.append((pts[k], pts[k + 1], _sgn(dh, pts[k], pts[k + 1])))
    A["mono"] = mono
    kinds = []
    for k, (c, z) in enumerate(crit):
        sl, sr = mono[k][2], mono[k + 1][2]
        kd = "max" if (sl > 0 and sr < 0) else ("min" if (sl < 0 and sr > 0) else "none")
        v2 = None
        if d2 is not None:
            try:
                vv = d2.subs(x, c if c is not None else z)
                if _finite(vv):
                    v2 = _simp(vv) if c is not None else sp.Float(_fl(vv), 6)
            except Exception:
                v2 = None
        kinds.append((kd, v2))
    A["kinds"] = kinds
    infl = [] if const else _roots_in(d2, x, a, b, d2h)
    infl = [t for t in infl if _sgn(d2h, t[1] - 1e-4 * (bf - af), t[1]) * _sgn(d2h, t[1], t[1] + 1e-4 * (bf - af)) < 0
            and _h1(h, t[1]) == _h1(h, t[1])]
    A["infl"] = infl
    p2 = [af] + [z for _, z in infl] + [bf]
    A["conc"] = [(p2[k], p2[k + 1], _sgn(d2h, p2[k], p2[k + 1])) for k in range(len(p2) - 1)]
    # closed interval method
    cands = []
    for tag, c, z in [("end", a, af)] + [("crit", c, z) for c, z in crit] + [("end", b, bf)]:
        val = None
        if c is not None:
            try:
                vv = f.subs(x, c)
                if _finite(vv):
                    val = _simp(vv)
            except Exception:
                val = None
        fv = _fl(val) if val is not None else _h1(h, z)
        if fv == fv:
            cands.append((tag, c, z, val, fv))
    A["cands"] = cands
    if cands and not A["poles"]:
        mx = max(t[4] for t in cands)
        mn = min(t[4] for t in cands)
        tol = 1e-9 * (1 + abs(mx) + abs(mn))
        A["amax"] = [t for t in cands if abs(t[4] - mx) <= tol]
        A["amin"] = [t for t in cands if abs(t[4] - mn) <= tol]
    else:
        A["amax"] = A["amin"] = []
    A["tex"] = _texf(f, A["fx"])
    _CACHE[key] = A
    return A


def _pt(c, z):
    return _at(c) if c is not None else _g(z, 5)


def _val(v, fv):
    return _ex(v) if v is not None else _g(fv, 6)


def solve(P):
    A = _analyze(P)
    vn = A["vn"]
    fmt = {"fx": A["fx"], "pretty_f": A["fx"], "a": A["sa"], "b": A["sb"]}
    if not A["ok"]:
        return {"answer": ("İfade çözümlenemedi", "Could not parse the expression"),
                "steps": [(f"Girdi: {A['raw']}", f"Input: {A['raw']}"),
                          ("İfadeyi x değişkeniyle, * ve ** kullanarak yazın.",
                           "Write the expression in x using * and **.")], "fmt": fmt}
    st = []
    ds = _ps(A["d"]) if A["d"] is not None else "?"
    d2s = _ps(A["d2"]) if A["d2"] is not None else "?"
    st.append((f"f({vn}) = {A['fx']},  [{A['sa']}, {A['sb']}] aralığında.  f'({vn}) = {ds}",
               f"f({vn}) = {A['fx']} on [{A['sa']}, {A['sb']}].  f'({vn}) = {ds}"))
    if A["const"]:
        st.append(("f' = 0 her yerde: f sabittir; her nokta hem maksimum hem minimumdur.",
                   "f' = 0 everywhere: f is constant; every point is both a max and a min."))
        v = A["cands"][0][4] if A["cands"] else 0.0
        return {"answer": (f"f sabit: f = {_g(v)}", f"f is constant: f = {_g(v)}"), "steps": st, "fmt": fmt}
    crit = A["crit"]
    if crit:
        cs = ", ".join(_pt(c, z) for c, z in crit)
        st.append((f"Kritik noktalar (f' = 0 ya da tanımsız), ({A['sa']}, {A['sb']}) içinde: {vn} = {cs}",
                   f"Critical points (f' = 0 or undefined) in ({A['sa']}, {A['sb']}): {vn} = {cs}"))
    else:
        st.append((f"({A['sa']}, {A['sb']}) içinde kritik nokta yok.", f"No critical points in ({A['sa']}, {A['sb']})."))
    mt, me = [], []
    for u, w, sg in A["mono"]:
        iv = f"({_g(u, 4)}, {_g(w, 4)})"
        mt.append(f"{iv}: f' {'>' if sg > 0 else ('<' if sg < 0 else '=')} 0 {'↗ artan' if sg > 0 else ('↘ azalan' if sg < 0 else 'sabit')}")
        me.append(f"{iv}: f' {'>' if sg > 0 else ('<' if sg < 0 else '=')} 0 {'↗ increasing' if sg > 0 else ('↘ decreasing' if sg < 0 else 'constant')}")
    st.append(("Birinci türev işaret tablosu: " + ";  ".join(mt), "First-derivative sign chart: " + ";  ".join(me)))
    if crit:
        t2, e2 = [], []
        for (c, z), (kd, v2) in zip(crit, A["kinds"]):
            p = _pt(c, z)
            kt = {"max": "yerel maks", "min": "yerel min", "none": "ekstremum değil"}[kd]
            ke = {"max": "local max", "min": "local min", "none": "not an extremum"}[kd]
            if v2 is not None:
                sv = _fl(v2)
                rel = "< 0" if sv < -1e-12 else ("> 0" if sv > 1e-12 else "= 0 (test sonuçsuz)")
                rele = "< 0" if sv < -1e-12 else ("> 0" if sv > 1e-12 else "= 0 (test inconclusive)")
                t2.append(f"f''({p}) = {_short(v2)} {rel} ⇒ {kt}")
                e2.append(f"f''({p}) = {_short(v2)} {rele} ⇒ {ke}")
            else:
                t2.append(f"{vn} = {p}: f' işareti ⇒ {kt}")
                e2.append(f"{vn} = {p}: sign of f' ⇒ {ke}")
        st.append((f"İkinci türev testi, f''({vn}) = {d2s}:  " + ";  ".join(t2),
                   f"Second-derivative test, f''({vn}) = {d2s}:  " + ";  ".join(e2)))
    ct, ce = [], []
    for u, w, sg in A["conc"]:
        iv = f"({_g(u, 4)}, {_g(w, 4)})"
        ct.append(f"{iv} {'∪ yukarı konkav' if sg > 0 else ('∩ aşağı konkav' if sg < 0 else 'doğrusal')}")
        ce.append(f"{iv} {'∪ concave up' if sg > 0 else ('∩ concave down' if sg < 0 else 'linear')}")
    if A["infl"]:
        ip = ", ".join(_pt(c, z) for c, z in A["infl"])
        st.append((f"Büküm noktası (f'' işaret değiştirir): {vn} = {ip}.  " + ";  ".join(ct),
                   f"Inflection point (f'' changes sign): {vn} = {ip}.  " + ";  ".join(ce)))
    else:
        st.append(("Büküm noktası yok.  " + ";  ".join(ct), "No inflection point.  " + ";  ".join(ce)))
    if A["poles"]:
        st.append(("f bu aralıkta sınırsız (dikey asimptot): mutlak maks/min yok.",
                   "f is unbounded on this interval (vertical asymptote): no absolute max/min."))
    cv = ", ".join(f"f({_pt(c, z)}) = {_val(v, fv)}" for _, c, z, v, fv in A["cands"])
    st.append((f"Kapalı aralık yöntemi (uç noktalar + kritik noktalar): {cv}",
               f"Closed interval method (endpoints + critical points): {cv}"))
    loc_t = [f"yerel {'maks' if kd == 'max' else 'min'} {vn} = {_pt(c, z)}" for (c, z), (kd, _) in zip(crit, A["kinds"]) if kd != "none"]
    loc_e = [f"local {'max' if kd == 'max' else 'min'} at {vn} = {_pt(c, z)}" for (c, z), (kd, _) in zip(crit, A["kinds"]) if kd != "none"]
    if A["amax"]:
        mxs = " ve ".join(_pt(c, z) for _, c, z, _, _ in A["amax"])
        mxe = " and ".join(_pt(c, z) for _, c, z, _, _ in A["amax"])
        mns = " ve ".join(_pt(c, z) for _, c, z, _, _ in A["amin"])
        mne = " and ".join(_pt(c, z) for _, c, z, _, _ in A["amin"])
        vmax = _val(A["amax"][0][3], A["amax"][0][4])
        vmin = _val(A["amin"][0][3], A["amin"][0][4])
        st.append((f"En büyük değer {vmax} ({vn} = {mxs}) ⇒ mutlak maksimum;  en küçük değer {vmin} ({vn} = {mns}) ⇒ mutlak minimum.",
                   f"Largest value {vmax} ({vn} = {mxe}) ⇒ absolute maximum;  smallest value {vmin} ({vn} = {mne}) ⇒ absolute minimum."))
        ans = (f"Mutlak maks {vmax} ({vn} = {mxs}), mutlak min {vmin} ({vn} = {mns})" + ("; " + ", ".join(loc_t) if loc_t else ""),
               f"Absolute max {vmax} (at {vn} = {mxe}), absolute min {vmin} (at {vn} = {mne})" + ("; " + ", ".join(loc_e) if loc_e else ""))
        fmt["absmax"], fmt["absmin"] = vmax, vmin
    else:
        ans = (("; ".join(loc_t) or "Yerel ekstremum yok") + "; mutlak ekstremum yok",
               ("; ".join(loc_e) or "No local extrema") + "; no absolute extrema")
    return {"answer": ans, "steps": st, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    A = _analyze(P)
    if not A["ok"]:
        return _badfig(fig, P, _T(P, "İfade çözümlenemedi", "Could not parse the expression"))
    h, af, bf, vn = A["h"], A["af"], A["bf"], A["vn"]
    pad = 0.06 * (bf - af)
    X = np.linspace(af - pad, bf + pad, 700)
    Y = h(X)
    inside = (X >= af) & (X <= bf)
    ylo, yhi = _yr(Y[inside], [t[4] for t in A["cands"]], pad=0.16)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.3, 0.85], left=0.085, right=0.98, top=0.93,
                          bottom=0.08, hspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    sx = fig.add_subplot(gs[1, 0], sharex=ax)
    ax.set_xlim(X[0], X[-1])
    ax.set_ylim(ylo, yhi)
    _axes_style(ax)
    ax.set_title(_mt(f"f({vn}) = " + sp.latex(A["f"]) + r",\ \ [" + sp.latex(A["a"]) + ", " + sp.latex(A["b"]) + "]",
                     f"f({vn}) = {A['fx']},  [{A['sa']}, {A['sb']}]"), fontsize=12)
    Yb = _brk(Y, yhi - ylo)
    Yin = np.where(inside, Yb, np.nan)
    Yout = np.where(inside, np.nan, Yb)
    curve, = ax.plot([], [], color=BLUE, lw=2.5, zorder=4)
    ghost, = ax.plot([], [], color=BLUE, lw=1.5, alpha=0.35, zorder=3)
    ax.axvline(af, color=GRAY, ls=":", lw=1)
    ax.axvline(bf, color=GRAY, ls=":", lw=1)
    bands = []
    for u, w, sg in A["mono"]:
        col = GREEN if sg > 0 else (RED if sg < 0 else GRAY)
        bands.append(ax.axvspan(u, w, color=col, alpha=0.0, lw=0, zorder=0))
    cdots, = ax.plot([], [], "o", color=ORANGE, ms=9, zorder=7)
    idots, = ax.plot([], [], "D", color=PURPLE, ms=8, zorder=7)
    edots, = ax.plot([], [], "s", color=GRAY, ms=8, zorder=7)
    smax, = ax.plot([], [], "*", color=RED, ms=20, zorder=8, mec="white")
    smin, = ax.plot([], [], "*", color=BLUE, ms=20, zorder=8, mec="white")
    span = yhi - ylo
    labs = []
    dd = 0.01 * (bf - af)
    for tag, c, z, v, fv in A["cands"]:
        nb = [_h1(h, w) for w in (z - dd, z + dd) if af <= w <= bf]
        nb = [w for w in nb if w == w]
        above = (not nb) or fv >= max(nb)
        if fv + 0.1 * span > yhi:
            above = False
        if fv - 0.1 * span < ylo:
            above = True
        t = ax.text(z, fv + (0.05 if above else -0.05) * span, "", fontsize=9.5, ha="center",
                    va="bottom" if above else "top", zorder=9, color="#111827",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
        labs.append((t, f"f({_pt(c, z)}) = {_short(v) if v is not None else _g(fv, 4)}"))
    # sign chart
    sx.set_ylim(0, 2)
    sx.set_yticks([0.35, 1.35])
    sx.set_yticklabels(["f''", "f'"], fontsize=11)
    sx.tick_params(labelsize=9)
    sx.set_xlabel(vn, fontsize=10)
    for s_ in ("top", "right", "left"):
        sx.spines[s_].set_visible(False)
    segs1, segs2 = [], []
    for u, w, sg in A["mono"]:
        col = GREEN if sg > 0 else (RED if sg < 0 else GRAY)
        ln, = sx.plot([u, w], [1.35, 1.35], color=col, lw=7, alpha=0, solid_capstyle="butt")
        tx = sx.text(0.5 * (u + w), 1.55, ("+ ↗" if sg > 0 else ("− ↘" if sg < 0 else "0")), ha="center",
                     va="bottom", fontsize=10.5, fontweight="bold", color=col, alpha=0)
        segs1.append((ln, tx))
    for u, w, sg in A["conc"]:
        col = BLUE if sg > 0 else (ORANGE if sg < 0 else GRAY)
        ln, = sx.plot([u, w], [0.35, 0.35], color=col, lw=7, alpha=0, solid_capstyle="butt")
        tx = sx.text(0.5 * (u + w), 0.55, ("+ ∪" if sg > 0 else ("− ∩" if sg < 0 else "0")), ha="center",
                     va="bottom", fontsize=10.5, fontweight="bold", color=col, alpha=0)
        segs2.append((ln, tx))
    vls = []
    for c, z in A["crit"]:
        vls.append((sx.axvline(z, ymin=0.5, ymax=1.0, color=ORANGE, ls=":", lw=1.4, alpha=0), 0))
    for c, z in A["infl"]:
        vls.append((sx.axvline(z, ymin=0.0, ymax=0.5, color=PURPLE, ls=":", lw=1.4, alpha=0), 1))
    info = _info(ax, 10.5, X, Y)
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    cz = [z for _, z in A["crit"]]
    iz = [z for _, z in A["infl"]]
    N = 170

    def update(i):
        p = _ramp(i, 0, 22)
        m = max(2, int(p * len(X)))
        curve.set_data(X[:m], Yin[:m])
        ghost.set_data(X[:m], Yout[:m])
        q1 = _ramp(i, 24, 30)
        cdots.set_data(cz, [_h1(h, z) for z in cz]) if q1 > 0 else cdots.set_data([], [])
        for k, (ln, tx) in enumerate(segs1):
            al = _ramp(i, 28 + 6 * k, 34 + 6 * k)
            ln.set_alpha(al)
            tx.set_alpha(al)
            bands[k].set_alpha(0.11 * al)
        for k, (ln, tx) in enumerate(segs2):
            al = _ramp(i, 62 + 6 * k, 68 + 6 * k)
            ln.set_alpha(al)
            tx.set_alpha(al)
        for vl, row in vls:
            vl.set_alpha(_ramp(i, 26, 32) if row == 0 else _ramp(i, 60, 66))
        idots.set_data(iz, [_h1(h, z) for z in iz]) if i >= 62 else idots.set_data([], [])
        if i >= 96:
            edots.set_data([af, bf], [_h1(h, af), _h1(h, bf)])
        else:
            edots.set_data([], [])
        for k, (t, s_) in enumerate(labs):
            t.set_text(s_ if i >= 98 + 6 * k else "")
        if i >= 132 and A["amax"]:
            smax.set_data([t[2] for t in A["amax"]], [t[4] for t in A["amax"]])
            smin.set_data([t[2] for t in A["amin"]], [t[4] for t in A["amin"]])
        else:
            smax.set_data([], [])
            smin.set_data([], [])
        if i < 24:
            info.set_text(_T(P, f"0) f({vn}) grafiği, [{A['sa']}, {A['sb']}]", f"0) Graph of f({vn}) on [{A['sa']}, {A['sb']}]"))
        elif i < 60:
            info.set_text(_T(P, "1) f' = 0 ⇒ kritik noktalar (turuncu)\nf' > 0 artan (yeşil), f' < 0 azalan (kırmızı)",
                             "1) f' = 0 ⇒ critical points (orange)\nf' > 0 increasing (green), f' < 0 decreasing (red)"))
        elif i < 96:
            info.set_text(_T(P, "2) f'' işareti ⇒ konkavlık (∪ / ∩)\nmor: büküm noktaları",
                             "2) Sign of f'' ⇒ concavity (∪ / ∩)\npurple: inflection points"))
        elif i < 132:
            info.set_text(_T(P, "3) Kapalı aralık yöntemi: uç noktalar\nve kritik noktalarda f değerleri",
                             "3) Closed interval method: values of f\nat the endpoints and critical points"))
        else:
            info.set_text("4) " + ans.replace("; ", "\n").replace(", mutlak", "\nmutlak").replace(", absolute", "\nabsolute"))
        return []

    return N, update


def vary(P, rnd):
    x, f = _parse(P.get("f", "x"))
    vn = str(x)
    z = sp.Symbol(vn)
    raw = str(P.get("f", "")).lower()
    if "exp" in raw:
        k = rnd.choice([1, 2, 3])
        c = rnd.choice([2, 3, 4])
        return {"f": f"{c}*{vn}*exp(-{vn}/{k})" if k != 1 else f"{c}*{vn}*exp(-{vn})", "a": 0, "b": 4 * k}
    while True:
        p = rnd.randint(-3, 2)
        q = p + rnd.choice([2, 4])
        k = rnd.choice([1, -1, 2])
        # f' = 3k(x - p)(x - q)  ->  f = k(x^3 - 3/2 (p+q) x^2 + 3pq x) + c
        c0 = rnd.randint(-6, 6)
        poly = sp.expand(k * (z ** 3 - sp.Rational(3, 2) * (p + q) * z ** 2 + 3 * p * q * z) + c0)
        if all(t.is_Integer for t in sp.Poly(poly, z).all_coeffs()):
            a = p - rnd.choice([1, 2])
            b = q + rnd.choice([1, 2])
            return {"f": sp.sstr(poly), "a": a, "b": b}
'''),
}
EXAMPLES += [
    {"id": "calc1-extrema-1", "kind": "extrema_expr",
     "title": ("Kübik fonksiyonun ekstremumları", "Extrema of a cubic"),
     "q": ("f(x) = {pretty_f} için [{a}, {b}] aralığında kritik noktaları, artan/azalan aralıkları, "
           "konkavlığı ve mutlak maksimum/minimumu bul.",
           "For f(x) = {pretty_f} on [{a}, {b}], find the critical points, where f increases/decreases, "
           "the concavity and the absolute maximum/minimum."),
     "P": {"f": "x**3 - 3*x**2 - 9*x + 5", "a": -2, "b": 4}},
    {"id": "calc1-extrema-2", "kind": "extrema_expr",
     "topics": ["word problem", "sözel problem", "profit", "kâr", "business"],
     "title": ("Kâr fonksiyonunun en büyük değeri", "Maximum of a profit function"),
     "q": ("Bir atölyenin haftalık kârı K(x) = {pretty_f} bin TL (x yüz adet, 0 ≤ x ≤ {b}). "
           "Kâr hangi üretimde en büyük, hangisinde en küçüktür?",
           "A workshop's weekly profit is P(x) = {pretty_f} thousand (x in hundreds of units, 0 ≤ x ≤ {b}). "
           "At which production level is the profit largest and smallest?"),
     "P": {"f": "-2*x**3 + 27*x**2 - 84*x", "a": 0, "b": 8}},
    {"id": "calc1-extrema-3", "kind": "extrema_expr", "topics": ["exponential", "üstel"],
     "title": ("Üstel çarpanlı fonksiyon", "A function with an exponential factor"),
     "q": ("f(x) = {pretty_f} fonksiyonunu [{a}, {b}] aralığında incele: yerel ve mutlak ekstremumlar, büküm noktası.",
           "Study f(x) = {pretty_f} on [{a}, {b}]: local and absolute extrema, inflection point."),
     "P": {"f": "x*exp(-x)", "a": 0, "b": 4}},
]


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["riemann_sum"] = {
    "course": "calc1",
    "title": ("Riemann toplamları: n büyüdükçe integrale yakınsama",
              "Riemann sums converging to the integral"),
    "topics": ["riemann sum", "riemann sums", "riemann", "left endpoint", "right endpoint",
               "midpoint rule", "midpoint", "trapezoidal rule", "trapezoid rule", "approximating area",
               "area approximation", "estimating area", "sigma notation", "definite integral",
               "riemann toplamı", "riemann toplamları", "sol uç nokta", "sağ uç nokta", "orta nokta kuralı",
               "yamuk kuralı", "alan yaklaşımı", "belirli integral"],
    "code": _code(r'''
from matplotlib.patches import Rectangle, Polygon

_NS = [2, 4, 8, 16, 32, 64]
_MNAME = {"left": ("sol uç nokta", "left endpoint"), "right": ("sağ uç nokta", "right endpoint"),
          "mid": ("orta nokta", "midpoint"), "trap": ("yamuk", "trapezoid")}
_MSYM = {"left": "L", "right": "R", "mid": "M", "trap": "T"}


def _method(v):
    s = str(v or "left").strip().lower()
    if s.startswith(("r", "sağ", "sag")):
        return "right"
    if s.startswith(("m", "orta", "c")):
        return "mid"
    if s.startswith(("t", "yamuk")):
        return "trap"
    return "left"


def _sum(h, a, b, n, meth):
    dx = (b - a) / n
    xs = a + dx * np.arange(n + 1)
    if meth == "trap":
        ys = h(xs)
        return dx * (0.5 * ys[0] + ys[1:-1].sum() + 0.5 * ys[-1]), xs, ys
    if meth == "left":
        sx = xs[:-1]
    elif meth == "right":
        sx = xs[1:]
    else:
        sx = xs[:-1] + 0.5 * dx
    ys = h(sx)
    return dx * ys.sum(), sx, ys


def _analyze(P):
    key = _key("riemann", P)
    if key in _CACHE:
        return _CACHE[key]
    x, f = _parse(P.get("f", "x"))
    A = {"ok": f is not None, "x": x, "f": f, "raw": str(P.get("f", "")), "vn": str(x)}
    A["fx"] = _pretty(_clean(A["raw"])) if f is not None else A["raw"].replace("{", "(").replace("}", ")")
    a, b = _sval(P.get("a", 0)), _sval(P.get("b", 1))
    if not (_finite(a) and _finite(b)):
        a, b = sp.Integer(0), sp.Integer(1)
    if _fl(a) > _fl(b):
        a, b = b, a
    if a == b:
        b = a + 1
    A["a"], A["b"], A["af"], A["bf"] = a, b, _fl(a), _fl(b)
    A["sa"], A["sb"] = _at(a), _at(b)
    meth = _method(P.get("method", "left"))
    A["meth"], A["S"] = meth, _MSYM[meth]
    if f is None:
        _CACHE[key] = A
        return A
    h = _num(f, x)
    A["h"] = h
    af, bf = A["af"], A["bf"]
    A["sums"] = [(n, _sum(h, af, bf, n, meth)[0]) for n in _NS]
    exact = None
    try:
        F = sp.integrate(f, x, manual=True)
        if not F.has(sp.Integral):
            v = _simp(F.subs(x, b) - F.subs(x, a))
            if _finite(v):
                exact = v
    except Exception:
        exact = None
    A["exact"] = exact
    A["ef"] = _fl(exact) if exact is not None else _quad(h, af, bf)
    # exact n = 4 sum when everything is rational
    n4 = 4
    dx = (b - a) / n4
    if meth == "left":
        pts = [a + k * dx for k in range(n4)]
    elif meth == "right":
        pts = [a + (k + 1) * dx for k in range(n4)]
    elif meth == "mid":
        pts = [a + (k + sp.Rational(1, 2)) * dx for k in range(n4)]
    else:
        pts = [a + k * dx for k in range(n4 + 1)]
    vals = []
    for t in pts:
        try:
            v = f.subs(x, t)
            v = _simp(v) if _finite(v) else None
        except Exception:
            v = None
        vals.append(v)
    A["pts4"], A["vals4"], A["dx4"] = pts, vals, _simp(dx)
    if all(v is not None for v in vals):
        if meth == "trap":
            s4 = dx / 2 * (vals[0] + 2 * sum(vals[1:-1]) + vals[-1])
        else:
            s4 = dx * sum(vals)
        A["s4"] = _simp(s4)
    else:
        A["s4"] = None
    # monotonicity / concavity for over/under estimate statements
    xs = np.linspace(af, bf, 401)
    ys = h(xs)
    dy = np.diff(ys)
    d2 = np.diff(ys, 2)
    A["inc"] = bool(np.all(dy >= -1e-12)) and not bool(np.all(np.abs(dy) < 1e-12))
    A["dec"] = bool(np.all(dy <= 1e-12)) and not bool(np.all(np.abs(dy) < 1e-12))
    A["cvx"] = bool(np.all(d2 >= -1e-9)) and bool(np.any(d2 > 1e-9))
    A["ccv"] = bool(np.all(d2 <= 1e-9)) and bool(np.any(d2 < -1e-9))
    _CACHE[key] = A
    return A


def solve(P):
    A = _analyze(P)
    vn = A["vn"]
    fmt = {"fx": A["fx"], "pretty_f": A["fx"], "a": A["sa"], "b": A["sb"]}
    if not A["ok"]:
        return {"answer": ("İfade çözümlenemedi", "Could not parse the expression"),
                "steps": [(f"Girdi: {A['raw']}", f"Input: {A['raw']}"),
                          ("İfadeyi x değişkeniyle, * ve ** kullanarak yazın.",
                           "Write the expression in x using * and **.")], "fmt": fmt}
    meth, S = A["meth"], A["S"]
    nm = _MNAME[meth]
    fmt["method"] = nm
    fmt["S"] = S
    st = [(f"Δ{vn} = (b − a)/n = ({A['sb']} − {A['sa']})/n;  n = 4 için Δ{vn} = {_ex(A['dx4'])}",
           f"Δ{vn} = (b − a)/n = ({A['sb']} − {A['sa']})/n;  for n = 4, Δ{vn} = {_ex(A['dx4'])}")]
    rule = {"left": (f"Sol uç noktalar: {vn}ᵢ = a + iΔ{vn}, i = 0, …, n − 1;  Lₙ = Δ{vn}·Σ f({vn}ᵢ)",
                     f"Left endpoints: {vn}ᵢ = a + iΔ{vn}, i = 0, …, n − 1;  Lₙ = Δ{vn}·Σ f({vn}ᵢ)"),
            "right": (f"Sağ uç noktalar: {vn}ᵢ = a + iΔ{vn}, i = 1, …, n;  Rₙ = Δ{vn}·Σ f({vn}ᵢ)",
                      f"Right endpoints: {vn}ᵢ = a + iΔ{vn}, i = 1, …, n;  Rₙ = Δ{vn}·Σ f({vn}ᵢ)"),
            "mid": (f"Orta noktalar: {vn}ᵢ = a + (i − 1/2)Δ{vn}, i = 1, …, n;  Mₙ = Δ{vn}·Σ f({vn}ᵢ)",
                    f"Midpoints: {vn}ᵢ = a + (i − 1/2)Δ{vn}, i = 1, …, n;  Mₙ = Δ{vn}·Σ f({vn}ᵢ)"),
            "trap": (f"Yamuk kuralı: Tₙ = (Δ{vn}/2)·[f({vn}₀) + 2f({vn}₁) + … + 2f({vn}ₙ₋₁) + f({vn}ₙ)]",
                     f"Trapezoidal rule: Tₙ = (Δ{vn}/2)·[f({vn}₀) + 2f({vn}₁) + … + 2f({vn}ₙ₋₁) + f({vn}ₙ)]")}[meth]
    st.append(rule)
    vals = A["vals4"]
    if A["s4"] is not None and all(v is not None for v in vals):
        terms = " + ".join(_short(v) if _fl(v) >= 0 else f"({_short(v)})" for v in vals)
        args = ", ".join(_short(t) for t in A["pts4"])
        if meth == "trap":
            mid_ = " + ".join(f"2·{_short(v)}" if 0 < k < len(vals) - 1 else _short(v) for k, v in enumerate(vals))
            st.append((f"n = 4: noktalar {args};  Δ{vn}/2 = {_short(A['dx4'] / 2)};  T₄ = {_short(A['dx4'] / 2)}·[{mid_}] = {_ex(A['s4'])}",
                       f"n = 4: points {args};  Δ{vn}/2 = {_short(A['dx4'] / 2)};  T₄ = {_short(A['dx4'] / 2)}·[{mid_}] = {_ex(A['s4'])}"))
        else:
            st.append((f"n = 4: {vn}ᵢ = {args};  {S}₄ = {_short(A['dx4'])}·[{terms}] = {_ex(A['s4'])}",
                       f"n = 4: {vn}ᵢ = {args};  {S}₄ = {_short(A['dx4'])}·[{terms}] = {_ex(A['s4'])}"))
        s4t = _ex(A["s4"])
    else:
        s4t = _g(A["sums"][1][1], 6)
        st.append((f"n = 4: {S}₄ ≈ {s4t}", f"n = 4: {S}₄ ≈ {s4t}"))
    tab = ",  ".join(f"{S}{_sub(n)} ≈ {_g(v, 6)}" for n, v in A["sums"])
    st.append((f"n arttıkça: {tab}", f"As n grows: {tab}"))
    ex = _ex(A["exact"]) if A["exact"] is not None else "≈ " + _g(A["ef"], 7)
    err = abs(A["sums"][-1][1] - A["ef"])
    st.append((f"Gerçek değer: ∫ f d{vn} = {ex};  n = 64 için hata ≈ {_g(err, 3)}",
               f"Exact value: ∫ f d{vn} = {ex};  error for n = 64 ≈ {_g(err, 3)}"))
    note = None
    if meth == "left" and A["inc"]:
        note = ("f artan ⇒ sol toplam her n için integralden küçüktür (alttan yaklaşır).",
                "f is increasing ⇒ the left sum underestimates for every n.")
    elif meth == "left" and A["dec"]:
        note = ("f azalan ⇒ sol toplam integralden büyüktür (üstten yaklaşır).",
                "f is decreasing ⇒ the left sum overestimates.")
    elif meth == "right" and A["inc"]:
        note = ("f artan ⇒ sağ toplam integralden büyüktür (üstten yaklaşır).",
                "f is increasing ⇒ the right sum overestimates.")
    elif meth == "right" and A["dec"]:
        note = ("f azalan ⇒ sağ toplam integralden küçüktür (alttan yaklaşır).",
                "f is decreasing ⇒ the right sum underestimates.")
    elif meth == "trap" and A["cvx"]:
        note = ("f yukarı konkav ⇒ yamuklar eğrinin üstünde kalır: Tₙ fazla tahmin eder.",
                "f is concave up ⇒ the trapezoids lie above the curve: Tₙ overestimates.")
    elif meth == "trap" and A["ccv"]:
        note = ("f aşağı konkav ⇒ Tₙ eksik tahmin eder.", "f is concave down ⇒ Tₙ underestimates.")
    elif meth == "mid" and A["cvx"]:
        note = ("f yukarı konkav ⇒ orta nokta toplamı eksik tahmin eder.", "f is concave up ⇒ the midpoint sum underestimates.")
    elif meth == "mid" and A["ccv"]:
        note = ("f aşağı konkav ⇒ orta nokta toplamı fazla tahmin eder.", "f is concave down ⇒ the midpoint sum overestimates.")
    if note:
        st.append(note)
    fmt["s4"] = s4t
    ans = (f"{S}₄ = {s4t};  n → ∞ iken {S}ₙ → ∫ = {ex}", f"{S}₄ = {s4t};  as n → ∞, {S}ₙ → ∫ = {ex}")
    return {"answer": ans, "steps": st, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    A = _analyze(P)
    if not A["ok"]:
        return _badfig(fig, P, _T(P, "İfade çözümlenemedi", "Could not parse the expression"))
    h, af, bf, vn, meth, S = A["h"], A["af"], A["bf"], A["vn"], A["meth"], A["S"]
    pad = 0.08 * (bf - af)
    X = np.linspace(af - pad, bf + pad, 600)
    Y = h(X)
    ylo, yhi = _yr(Y, [0.0])
    gs = fig.add_gridspec(1, 2, width_ratios=[1.7, 1], left=0.07, right=0.98, top=0.9, bottom=0.11,
                          wspace=0.25)
    ax = fig.add_subplot(gs[0, 0])
    cx = fig.add_subplot(gs[0, 1])
    ax.set_xlim(X[0], X[-1])
    ax.set_ylim(ylo, yhi)
    _axes_style(ax)
    ax.set_xlabel(vn, fontsize=10)
    ax.set_title(_mt(f"f({vn}) = " + sp.latex(A["f"]) + r",\ \ [" + sp.latex(A["a"]) + ", " + sp.latex(A["b"]) + "]",
                     f"f({vn}) = {A['fx']}"), fontsize=12)
    ax.plot(X, _brk(Y, yhi - ylo), color=BLUE, lw=2.4, zorder=5)
    ax.axvline(af, color=GRAY, ls=":", lw=1)
    ax.axvline(bf, color=GRAY, ls=":", lw=1)
    shapes = []
    for k in range(64):
        if meth == "trap":
            pch = Polygon([[0, 0], [0, 0], [0, 0], [0, 0]], closed=True, visible=False, zorder=3,
                          lw=0.8, ec="#1E3A8A")
        else:
            pch = Rectangle((0, 0), 0, 0, visible=False, zorder=3, lw=0.8, ec="#1E3A8A")
        ax.add_patch(pch)
        shapes.append(pch)
    sdots, = ax.plot([], [], "o", color=ORANGE, ms=5, zorder=6)
    info = _info(ax, 10.5, X, Y)
    # convergence panel
    sums = A["sums"]
    sv = [v for _, v in sums]
    clo, chi = _yr(sv, [A["ef"]], pad=0.25)
    cx.set_xlim(0.5, 6.5)
    cx.set_ylim(clo, chi)
    cx.set_xticks(range(1, 7))
    cx.set_xticklabels([str(n) for n in _NS], fontsize=9)
    cx.tick_params(labelsize=9)
    cx.grid(alpha=0.3)
    cx.set_xlabel("n", fontsize=10)
    cx.set_title(f"{S}ₙ → ∫ f d{vn}", fontsize=11)
    cx.axhline(A["ef"], color=GREEN, ls="--", lw=1.5)
    cx.text(0.6, A["ef"], " ∫ = " + (_short(A["exact"]) if A["exact"] is not None else _g(A["ef"], 5)),
            color=GREEN, fontsize=10, va="bottom")
    cpts, = cx.plot([], [], "o-", color=ORANGE, lw=1.5, ms=7)
    clab = cx.text(0, 0, "", fontsize=9.5, color=ORANGE, ha="left", va="bottom")
    data = []
    for n in _NS:
        s_, sx_, sy_ = _sum(h, af, bf, n, meth)
        data.append((n, s_, sx_, np.nan_to_num(sy_, nan=0.0)))
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    nm = _MNAME[meth][0 if tr else 1]
    N = 165

    def update(i):
        ph = -1 if i < 14 else min(5, (i - 14) // 22)
        if ph >= 0:
            n, s_, sx_, sy_ = data[ph]
            dx = (bf - af) / n
            g = _ramp(i - 14 - 22 * ph, 0, 7) if i < 146 else 1.0
            for k, pch in enumerate(shapes):
                if k < n:
                    x0 = af + k * dx
                    if meth == "trap":
                        pch.set_xy([[x0, 0], [x0, g * sy_[k]], [x0 + dx, g * sy_[k + 1]], [x0 + dx, 0]])
                        pos = sy_[k] + sy_[k + 1] >= 0
                    else:
                        pch.set_x(x0)
                        pch.set_y(0)
                        pch.set_width(dx)
                        pch.set_height(g * sy_[k])
                        pos = sy_[k] >= 0
                    pch.set_facecolor(BLUE if pos else RED)
                    pch.set_alpha(0.30 if n <= 16 else 0.38)
                    pch.set_linewidth(0.8 if n <= 16 else 0.3)
                    pch.set_visible(True)
                else:
                    pch.set_visible(False)
            if n <= 16:
                if meth == "trap":
                    sdots.set_data(sx_, g * sy_)
                else:
                    sdots.set_data(sx_, g * sy_)
            else:
                sdots.set_data([], [])
            cpts.set_data(list(range(1, ph + 2)), [v for _, v in sums[:ph + 1]])
            clab.set_position((ph + 1.1 if ph < 3 else ph + 0.9, sums[ph][1]))
            clab.set_ha("left" if ph < 3 else "right")
            clab.set_va("bottom" if ph < 3 else "top")
            clab.set_text(_g(sums[ph][1], 5))
            if i < 146:
                info.set_text(f"{nm}:  n = {n},  Δ{vn} = {_g(dx, 4)}\n{S}{_sub(n)} = {_g(s_, 6)}   "
                              + _T(P, "(gerçek ", "(exact ") + _g(A["ef"], 6) + ")")
            else:
                info.set_text(ans.replace(";  ", "\n"))
        else:
            for pch in shapes:
                pch.set_visible(False)
            sdots.set_data([], [])
            cpts.set_data([], [])
            clab.set_text("")
            info.set_text(_T(P, f"f({vn}) ve [{A['sa']}, {A['sb']}]: alanı dikdörtgenlerle yaklaşık hesapla",
                             f"f({vn}) on [{A['sa']}, {A['sb']}]: approximate the area with rectangles")
                          if meth != "trap" else
                          _T(P, f"f({vn}) ve [{A['sa']}, {A['sb']}]: alanı yamuklarla yaklaşık hesapla",
                             f"f({vn}) on [{A['sa']}, {A['sb']}]: approximate the area with trapezoids"))
        return []

    return N, update


def vary(P, rnd):
    x, f = _parse(P.get("f", "x"))
    vn = str(x)
    z = sp.Symbol(vn)
    meth = _method(P.get("method", "left"))
    raw = str(P.get("f", "")).lower()
    if "1/" in raw:
        a = rnd.choice([1, 2])
        return {"f": f"{rnd.choice([1, 2, 3, 4])}/{vn}", "a": a, "b": a + rnd.choice([1, 2, 3]), "method": meth}
    if "sin" in raw or "cos" in raw:
        return {"f": rnd.choice([f"sin({vn})", f"2*sin({vn})", f"sin({vn}) + 1"]), "a": 0,
                "b": rnd.choice(["pi", "pi/2"]), "method": meth}
    if "-" in raw and "**2" in raw:
        T = rnd.choice([2, 3, 4, 5])
        return {"f": f"{T * T} - {vn}**2", "a": 0, "b": T, "method": meth}
    c2 = rnd.choice([1, 2, 3])
    c0 = rnd.choice([0, 1, 2])
    b = rnd.choice([2, 3, 4])
    return {"f": sp.sstr(sp.expand(c2 * z ** 2 + c0)) if rnd.random() < 0.7 else sp.sstr(z ** 3 + c0),
            "a": 0, "b": b, "method": meth}
'''),
}
EXAMPLES += [
    {"id": "calc1-riemann-1", "kind": "riemann_sum",
     "title": ("Sol uç nokta toplamı", "Left-endpoint Riemann sum"),
     "q": ("f(x) = {pretty_f} eğrisi altında [{a}, {b}] üzerindeki alanı n = 4 dikdörtgenle, {method} kuralıyla "
           "yaklaşık hesapla; n büyüdükçe toplamın integrale yaklaştığını göster.",
           "Approximate the area under f(x) = {pretty_f} on [{a}, {b}] with n = 4 rectangles using the "
           "{method} rule; show that the sums approach the integral as n grows."),
     "P": {"f": "x**2", "a": 0, "b": 2, "method": "left"}},
    {"id": "calc1-riemann-2", "kind": "riemann_sum",
     "topics": ["distance from velocity", "word problem", "sözel problem", "hız", "yol"],
     "title": ("Hızdan yol tahmini (sağ uç nokta)", "Estimating distance from velocity (right endpoints)"),
     "q": ("Frene basan bir aracın hızı v(t) = {pretty_f} m/s (0 ≤ t ≤ {b}). Durana kadar aldığı yolu n = 4 "
           "aralıkla {method} toplamıyla tahmin et ve gerçek değerle karşılaştır.",
           "A braking car has velocity v(t) = {pretty_f} m/s (0 ≤ t ≤ {b}). Estimate the distance it travels "
           "with a {method} sum using n = 4 subintervals and compare with the exact value."),
     "P": {"f": "16 - t**2", "a": 0, "b": 4, "method": "right"}},
    {"id": "calc1-riemann-3", "kind": "riemann_sum", "topics": ["natural logarithm", "ln 2", "doğal logaritma"],
     "title": ("Yamuk kuralı ile ln 2", "ln 2 with the trapezoidal rule"),
     "q": ("{a} ile {b} arasında f(x) = {pretty_f} altındaki alan ln 2'dir. Bu alanı {method} kuralıyla n = 4 "
           "için yaklaşık hesapla; n arttıkça hata nasıl küçülür?",
           "The area under f(x) = {pretty_f} from {a} to {b} equals ln 2. Approximate it with the {method} rule "
           "for n = 4; how does the error shrink as n grows?"),
     "P": {"f": "1/x", "a": 1, "b": 2, "method": "trap"}},
]


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["optimization_box"] = {
    "course": "calc1",
    "title": ("Optimizasyon: en büyük hacimli açık kutu", "Optimization: the open box of largest volume"),
    "topics": ["optimization", "optimisation", "applied optimization", "optimization problems", "open box",
               "maximum volume", "max min problems", "applications of derivatives", "applied maxima and minima",
               "optimizasyon", "en büyük hacim", "kutu problemi", "maksimum minimum problemleri",
               "türevin uygulamaları", "ekstremum problemleri"],
    "code": _code(r'''
from matplotlib.patches import Polygon, Rectangle


def _dims(P):
    L, W = float(P.get("L", 12)), float(P.get("W", 12))
    L, W = abs(L) or 12.0, abs(W) or 12.0
    if W > L:
        L, W = W, L
    return L, W


def _analyze(P):
    key = _key("box", P)
    if key in _CACHE:
        return _CACHE[key]
    L, W = _dims(P)
    Ls, Ws = _sval(L), _sval(W)
    x = sp.Symbol("x", positive=True)
    V = x * (Ls - 2 * x) * (Ws - 2 * x)
    dV = sp.expand(sp.diff(V, x))
    roots = []
    try:
        for r in sp.solve(sp.Eq(dV, 0), x):
            r = sp.radsimp(sp.simplify(r))
            if _finite(r):
                roots.append(r)
    except Exception:
        roots = []
    if not roots:
        disc = L * L - L * W + W * W
        roots = [sp.Float((L + W - math.sqrt(disc)) / 6, 12), sp.Float((L + W + math.sqrt(disc)) / 6, 12)]
    roots = sorted(roots, key=_fl)
    xs = [r for r in roots if 0 < _fl(r) < W / 2]
    xstar = xs[0] if xs else roots[0]
    Vstar = sp.simplify(V.subs(x, xstar))
    d2 = sp.expand(sp.diff(V, x, 2))
    A = {"L": L, "W": W, "Ls": Ls, "Ws": Ws, "x": x, "V": V, "Vexp": sp.expand(V), "dV": dV, "roots": roots,
         "xstar": xstar, "Vstar": Vstar, "d2": d2, "d2v": sp.simplify(d2.subs(x, xstar)),
         "xf": _fl(xstar), "Vf": _fl(Vstar), "unit": str(P.get("unit", "cm"))}
    _CACHE[key] = A
    return A


def _vol(L, W, t):
    return t * (L - 2 * t) * (W - 2 * t)


def solve(P):
    A = _analyze(P)
    L, W, u = A["L"], A["W"], A["unit"]
    Lt, Wt = _g(L), _g(W)
    xs_, Vs_ = _ex(A["xstar"]), _ex(A["Vstar"])
    st = [(f"Kesilen karenin kenarı x olsun. Katlayınca taban ({Lt} − 2x) × ({Wt} − 2x), yükseklik x olur; 0 < x < {_g(W / 2)}.",
           f"Let x be the side of each cut square. After folding, the base is ({Lt} − 2x) × ({Wt} − 2x) and the height is x; 0 < x < {_g(W / 2)}."),
          (f"Hacim: V(x) = x({Lt} − 2x)({Wt} − 2x) = {_ps(A['Vexp'])}",
           f"Volume: V(x) = x({Lt} − 2x)({Wt} − 2x) = {_ps(A['Vexp'])}"),
          (f"V'(x) = {_ps(A['dV'])} = 0", f"V'(x) = {_ps(A['dV'])} = 0")]
    try:
        cf = sp.Poly(A["dV"], A["x"]).all_coeffs()
        qa, qb, qc = cf[0], cf[1], cf[2]
        D = sp.expand(qb * qb - 4 * qa * qc)
        st.append((f"x = [−b ± √(b² − 4ac)]/(2a) = [{_short(-qb)} ± √({_short(D)})]/{_short(2 * qa)} = [{_short(-qb)} ± {_short(sp.sqrt(D))}]/{_short(2 * qa)}",
                   f"x = [−b ± √(b² − 4ac)]/(2a) = [{_short(-qb)} ± √({_short(D)})]/{_short(2 * qa)} = [{_short(-qb)} ± {_short(sp.sqrt(D))}]/{_short(2 * qa)}"))
    except Exception:
        pass
    rs_t = " veya ".join(f"x = {_ex(r)}" for r in A["roots"])
    rs_e = " or ".join(f"x = {_ex(r)}" for r in A["roots"])
    bad = [r for r in A["roots"] if not (0 < _fl(r) < W / 2)]
    tail_t = (f";  {', '.join(_short(r) for r in bad)} değeri 0 < x < {_g(W / 2)} aralığında değil") if bad else ""
    tail_e = (f";  {', '.join(_short(r) for r in bad)} is outside 0 < x < {_g(W / 2)}") if bad else ""
    st.append((f"Kökler: {rs_t}{tail_t}", f"Roots: {rs_e}{tail_e}"))
    st.append((f"V''(x) = {_ps(A['d2'])} ⇒ V''({_short(A['xstar'])}) = {_ex(A['d2v'])} < 0 ⇒ yerel (ve mutlak) maksimum",
               f"V''(x) = {_ps(A['d2'])} ⇒ V''({_short(A['xstar'])}) = {_ex(A['d2v'])} < 0 ⇒ local (and absolute) maximum"))
    l, w, hgt = L - 2 * A["xf"], W - 2 * A["xf"], A["xf"]
    st.append((f"V({_short(A['xstar'])}) = {Vs_} {u}³;  kutu {_g(l, 4)} × {_g(w, 4)} × {_g(hgt, 4)} {u}",
               f"V({_short(A['xstar'])}) = {Vs_} {u}³;  the box is {_g(l, 4)} × {_g(w, 4)} × {_g(hgt, 4)} {u}"))
    st.append((f"Uç noktalarda (x → 0 veya x → {_g(W / 2)}) hacim 0'a gider; bu yüzden bulunan değer en büyük hacimdir.",
               f"At the ends (x → 0 or x → {_g(W / 2)}) the volume tends to 0, so this is the largest volume."))
    return {"answer": (f"x = {xs_} {u} kesilirse V_maks = {Vs_} {u}³", f"Cut x = {xs_} {u}: V_max = {Vs_} {u}³"),
            "steps": st, "fmt": {"L": Lt, "W": Wt, "unit": u}}


def _proj(X, Y, Z):
    c, s = 0.5 * math.cos(math.radians(35)), 0.5 * math.sin(math.radians(35))
    return [X + c * Y, Z + s * Y]


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    A = _analyze(P)
    L, W, xs_, u = A["L"], A["W"], A["xf"], A["unit"]
    xm = W / 2
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.12], left=0.03, right=0.98, top=0.92, bottom=0.1,
                          wspace=0.16, hspace=0.18)
    nax = fig.add_subplot(gs[0, 0])
    bax = fig.add_subplot(gs[1, 0])
    vax = fig.add_subplot(gs[:, 1])
    for a_ in (nax, bax):
        a_.set_aspect("equal")
        a_.axis("off")
    nax.set_xlim(-0.06 * L, 1.06 * L)
    nax.set_ylim(-0.2 * W, 1.08 * W)
    nax.set_title(_T(P, f"Karton: {_g(L)} × {_g(W)} {u}", f"Sheet: {_g(L)} × {_g(W)} {u}"), fontsize=10.5)
    sheet = Polygon([[0, 0]] * 12, closed=True, fc="#F3D9B1", ec="#8B5E34", lw=1.4)
    nax.add_patch(sheet)
    cuts = [Rectangle((0, 0), 0, 0, fc="white", ec=RED, ls="--", lw=1.2) for _ in range(4)]
    for c in cuts:
        nax.add_patch(c)
    folds = [nax.plot([], [], ls=":", color="#8B5E34", lw=1)[0] for _ in range(4)]
    nlab = nax.text(0.5 * L, -0.1 * W, "", ha="center", va="center", fontsize=9.5)
    xlab = nax.text(0, 0, "x", color=RED, fontsize=10, ha="center", va="center")
    cx_, sy_ = 0.5 * math.cos(math.radians(35)), 0.5 * math.sin(math.radians(35))
    bax.set_xlim(-0.05 * L, L + cx_ * W + 0.05 * L)
    bax.set_ylim(-0.06 * W, xm + sy_ * W + 0.08 * W)
    faces = []
    for fc, al in (("#F3D9B1", 1.0), ("#E9B872", 1.0), ("#E2A65A", 1.0), ("#E2A65A", 0.8), ("#E9B872", 0.55)):
        pg = Polygon([[0, 0]] * 4, closed=True, fc=fc, ec="#8B5E34", lw=1.1, alpha=al)
        bax.add_patch(pg)
        faces.append(pg)
    blab = bax.text(0.5, -0.02, "", transform=bax.transAxes, ha="center", va="top", fontsize=9.5)
    # volume graph
    T = np.linspace(0, xm, 300)
    V = _vol(L, W, T)
    vax.set_xlim(0, xm)
    vax.set_ylim(0, A["Vf"] * 1.25)
    vax.grid(alpha=0.3)
    vax.tick_params(labelsize=9)
    vax.set_xlabel("x (" + u + ")", fontsize=10)
    vax.set_ylabel("V (" + u + "³)", fontsize=10)
    vax.set_title(_mt(r"V(x) = x\,(" + _g(L).replace("−", "-") + r" - 2x)(" + _g(W).replace("−", "-") + " - 2x)",
                      f"V(x) = x({_g(L)} − 2x)({_g(W)} − 2x)"), fontsize=11)
    vax.plot(T, V, color=GRAY, lw=1.2, alpha=0.5)
    vtr, = vax.plot([], [], color=BLUE, lw=2.6)
    vdot, = vax.plot([], [], "o", color=ORANGE, ms=9, zorder=6)
    vline, = vax.plot([], [], ":", color=ORANGE, lw=1.2)
    tang, = vax.plot([], [], "--", color=GREEN, lw=1.6)
    star, = vax.plot([], [], "*", color=RED, ms=18, zorder=7, mec="white")
    slab = vax.text(0, 0, "", color=RED, fontsize=11, fontweight="bold", ha="center", va="bottom")
    info = _info(vax, 10.5, T, V)
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    x1 = 0.22 * xm
    x2 = 0.93 * xm
    N = 170

    def xsched(i):
        if i < 16:
            return x1 * _ramp(i, 0, 14)
        if i < 34:
            return x1
        if i < 84:
            return x1 + (x2 - x1) * _ramp(i, 34, 84)
        if i < 112:
            t = _ramp(i, 84, 112)
            t = t * t * (3 - 2 * t)
            return x2 + (xs_ - x2) * t
        return xs_

    def update(i):
        xv = xsched(i)
        fold = _ramp(i, 16, 34)
        sheet.set_xy([[xv, 0], [L - xv, 0], [L - xv, xv], [L, xv], [L, W - xv], [L - xv, W - xv], [L - xv, W],
                      [xv, W], [xv, W - xv], [0, W - xv], [0, xv], [xv, xv]])
        for c, (cx0, cy0) in zip(cuts, ((0, 0), (L - xv, 0), (L - xv, W - xv), (0, W - xv))):
            c.set_xy((cx0, cy0))
            c.set_width(xv)
            c.set_height(xv)
        folds[0].set_data([xv, L - xv], [xv, xv])
        folds[1].set_data([xv, L - xv], [W - xv, W - xv])
        folds[2].set_data([xv, xv], [xv, W - xv])
        folds[3].set_data([L - xv, L - xv], [xv, W - xv])
        xlab.set_position((xv / 2, xv / 2))
        xlab.set_text("x" if xv > 0.05 * W else "")
        nlab.set_text(f"x = {_g(xv, 3)} {u}" if i >= 4 else "")
        l, w = L - 2 * xv, W - 2 * xv
        H = xv * fold
        pts = {"b": [(0, 0, 0), (l, 0, 0), (l, w, 0), (0, w, 0)],
               "k": [(0, w, 0), (l, w, 0), (l, w, H), (0, w, H)],
               "l": [(0, 0, 0), (0, w, 0), (0, w, H), (0, 0, H)],
               "r": [(l, 0, 0), (l, w, 0), (l, w, H), (l, 0, H)],
               "f": [(0, 0, 0), (l, 0, 0), (l, 0, H), (0, 0, H)]}
        for pg, kk in zip(faces, ("b", "k", "l", "r", "f")):
            pg.set_xy([_proj(*q) for q in pts[kk]])
            pg.set_visible(i >= 16)
        blab.set_text((f"{_g(l, 3)} × {_g(w, 3)} × {_g(H, 3)} {u}") if i >= 16 else "")
        if i >= 34:
            hi_x = max(xv, x1) if i < 84 else x2
            m = T <= hi_x
            mm = T >= x1
            vtr.set_data(T[m & mm], V[m & mm])
        else:
            vtr.set_data([], [])
        if i >= 16:
            vv = _vol(L, W, xv)
            vdot.set_data([xv], [vv])
            vline.set_data([xv, xv], [0, vv])
        else:
            vdot.set_data([], [])
            vline.set_data([], [])
        if i >= 112:
            star.set_data([xs_], [A["Vf"]])
            tang.set_data([xs_ - 0.18 * xm, xs_ + 0.18 * xm], [A["Vf"], A["Vf"]])
            slab.set_position((xs_, A["Vf"] * 1.04))
            slab.set_text("V'(x) = 0")
        else:
            star.set_data([], [])
            tang.set_data([], [])
            slab.set_text("")
        if i < 16:
            info.set_text(_T(P, "1) Köşelerden x kenarlı\nkareler kes", "1) Cut x-by-x squares\nfrom the corners"))
        elif i < 34:
            info.set_text(_T(P, "2) Kenarları katla:\naçık kutu", "2) Fold up the sides:\nan open box"))
        elif i < 112:
            info.set_text(_T(P, f"3) x değişince hacim değişir\nx = {_g(xv, 3)},  V = {_g(_vol(L, W, xv), 5)}",
                             f"3) The volume depends on x\nx = {_g(xv, 3)},  V = {_g(_vol(L, W, xv), 5)}"))
        else:
            info.set_text("4) " + ans.replace(" kesilirse ", "\n").replace(": ", "\n"))
        return []

    return N, update


def vary(P, rnd):
    fam = rnd.choice(["sq", "85", "85", "2116"])
    if fam == "sq":
        m = rnd.choice([1, 2, 3, 4, 5])
        L = W = 6 * m
    elif fam == "85":
        k = rnd.choice([1, 2, 3, 4])
        L, W = 8 * k, 5 * k
    else:
        L, W = 21, 16
    out = {"L": L, "W": W}
    if "unit" in P:
        out["unit"] = P["unit"]
    return out
'''),
}
EXAMPLES += [
    {"id": "calc1-box-1", "kind": "optimization_box",
     "title": ("Kare kartondan açık kutu", "Open box from a square sheet"),
     "q": ("Kenarı {L} {unit} olan kare bir kartonun köşelerinden eş kareler kesilip kenarlar katlanarak üstü "
           "açık bir kutu yapılacak. Hacmin en büyük olması için kesilen karelerin kenarı ne olmalı?",
           "Equal squares are cut from the corners of a {L} {unit} square sheet and the sides are folded up to "
           "make an open box. What size squares give the largest volume?"),
     "P": {"L": 12, "W": 12, "unit": "cm"}},
    {"id": "calc1-box-2", "kind": "optimization_box", "topics": ["word problem", "sözel problem", "packaging", "ambalaj"],
     "title": ("Dikdörtgen kartondan ambalaj kutusu", "Packaging box from a rectangular sheet"),
     "q": ("Bir ambalaj firması {L} × {W} {unit} kartonların köşelerinden kare kesip katlayarak üstü açık kutular "
           "üretiyor. En büyük hacim için kesim boyu ve bu hacim nedir?",
           "A packaging company makes open boxes from {L} × {W} {unit} sheets by cutting squares from the corners "
           "and folding. Find the cut size that maximises the volume, and that volume."),
     "P": {"L": 16, "W": 10, "unit": "cm"}},
    {"id": "calc1-box-3", "kind": "optimization_box", "topics": ["radical answer", "köklü sonuç"],
     "title": ("Köklü çıkan optimum", "An optimum with a radical"),
     "q": ("{L} × {W} {unit} bir levhadan köşeleri kesilerek açık kutu yapılıyor. Kesim boyunu tam (köklü) "
           "biçimde ve ondalık olarak bul; en büyük hacmi hesapla.",
           "An open box is made from a {L} × {W} {unit} plate by cutting out the corners. Find the cut size "
           "exactly (with a radical) and as a decimal, and the largest volume."),
     "P": {"L": 30, "W": 20, "unit": "cm"}},
]


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["related_rates_ladder"] = {
    "course": "calc1",
    "title": ("İlişkili oranlar: kayan merdiven", "Related rates: the sliding ladder"),
    "topics": ["related rates", "related rate", "sliding ladder", "ladder problem", "ladder",
               "implicit differentiation", "rates of change", "chain rule application",
               "ilişkili oranlar", "bağımlı değişim oranları", "kayan merdiven", "merdiven problemi",
               "kapalı türev", "değişim hızı"],
    "code": _code(r'''
from matplotlib.patches import FancyArrowPatch, Rectangle


def _pars(P):
    L = abs(float(P.get("L", 10))) or 10.0
    v = float(P.get("v", 1)) or 1.0
    x0 = abs(float(P.get("x0", 0.6 * L)))
    if not 0 < x0 < L:
        x0 = 0.6 * L
    return L, v, x0


def solve(P):
    L, v, x0 = _pars(P)
    u = str(P.get("unit", "m"))
    Ls, vs, xs = _sval(L), _sval(v), _sval(x0)
    y0 = sp.sqrt(Ls ** 2 - xs ** 2)
    dy = _simp(-xs * vs / y0)
    dth = _simp(-vs / y0)
    st = [(f"Duvardan uzaklık x(t), yükseklik y(t). Pisagor: x² + y² = {_g(L)}² = {_g(L * L)}",
           f"Distance from the wall x(t), height y(t). Pythagoras: x² + y² = {_g(L)}² = {_g(L * L)}"),
          ("Zamana göre türev al (zincir kuralı): 2x·dx/dt + 2y·dy/dt = 0  ⇒  dy/dt = −(x/y)·dx/dt",
           "Differentiate with respect to time (chain rule): 2x·dx/dt + 2y·dy/dt = 0  ⇒  dy/dt = −(x/y)·dx/dt"),
          (f"x = {_g(x0)} iken y = √({_g(L * L)} − {_g(x0 * x0)}) = {_ex(y0)} {u}",
           f"When x = {_g(x0)}, y = √({_g(L * L)} − {_g(x0 * x0)}) = {_ex(y0)} {u}"),
          (f"dx/dt = {_g(v)} {u}/s  ⇒  dy/dt = −({_g(x0)}/{_short(y0)})·{_g(v)} = {_ex(dy)} {u}/s",
           f"dx/dt = {_g(v)} {u}/s  ⇒  dy/dt = −({_g(x0)}/{_short(y0)})·{_g(v)} = {_ex(dy)} {u}/s")]
    down = _fl(dy) < 0
    st.append(((f"Eksi işaret: merdivenin üst ucu aşağı kayıyor, hızı {_short(abs(dy))} {u}/s." if down else
                f"Artı işaret: üst uç yukarı çıkıyor, hızı {_short(abs(dy))} {u}/s."),
               (f"The minus sign means the top slides down at {_short(abs(dy))} {u}/s." if down else
                f"The plus sign means the top moves up at {_short(abs(dy))} {u}/s.")))
    st.append((f"Ek: zeminle açı θ için cos θ = x/{_g(L)} ⇒ dθ/dt = −(dx/dt)/y = {_ex(dth)} rad/s",
               f"Extra: for the angle θ with the floor, cos θ = x/{_g(L)} ⇒ dθ/dt = −(dx/dt)/y = {_ex(dth)} rad/s"))
    st.append(("y küçüldükçe |dy/dt| = x·v/y büyür: üst uç yere yaklaşırken giderek hızlanır.",
               "As y shrinks, |dy/dt| = x·v/y grows: the top speeds up as it nears the floor."))
    return {"answer": (f"dy/dt = {_exd(dy)} {u}/s  (üst uç {_g(abs(_fl(dy)), 5)} {u}/s hızla {'aşağı' if down else 'yukarı'})",
                       f"dy/dt = {_exd(dy)} {u}/s  (the top moves {'down' if down else 'up'} at {_g(abs(_fl(dy)), 5)} {u}/s)"),
            "steps": st, "fmt": {"L": _g(L), "v": _g(v), "x0": _g(x0), "unit": u, "y0": _short(y0)}}


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    L, v, x0 = _pars(P)
    u = str(P.get("unit", "m"))
    av = abs(v)
    xs = max(0.12 * L, x0 - 0.55 * (L - x0) - 0.25 * x0)
    xs = min(xs, 0.8 * x0)
    xe = 0.975 * L
    if v < 0:
        xs, xe = min(0.98 * L, x0 + 0.6 * (L - x0)), 0.15 * L
    t0 = abs(x0 - xs) / av
    T = abs(xe - xs) / av
    sg = 1.0 if v > 0 else -1.0

    def X(t):
        return xs + sg * av * t

    def Y(t):
        return math.sqrt(max(L * L - X(t) ** 2, 0.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.12, 1], left=0.05, right=0.98, top=0.9, bottom=0.11,
                          wspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    gx = fig.add_subplot(gs[0, 1])
    ax.set_aspect("equal")
    ax.set_xlim(-0.34 * L, 1.1 * L)
    ax.set_ylim(-0.12 * L, 1.08 * L)
    ax.axis("off")
    ax.add_patch(Rectangle((-0.08 * L, -0.05 * L), 0.08 * L, 1.1 * L, fc="#D1D5DB", ec="#6B7280"))
    ax.add_patch(Rectangle((-0.08 * L, -0.08 * L), 1.2 * L, 0.08 * L, fc="#E5E7EB", ec="#6B7280"))
    ax.set_title(_T(P, f"Merdiven: L = {_g(L)} {u}, alt uç dx/dt = {_g(v)} {u}/s",
                    f"Ladder: L = {_g(L)} {u}, foot dx/dt = {_g(v)} {u}/s"), fontsize=11)
    lad, = ax.plot([], [], color=ORANGE, lw=5, solid_capstyle="round", zorder=4)
    ends, = ax.plot([], [], "o", color="#7C2D12", ms=8, zorder=5)
    xdim, = ax.plot([], [], color=BLUE, lw=1.5)
    ydim, = ax.plot([], [], color=GREEN, lw=1.5)
    xt = ax.text(0, 0, "", color=BLUE, fontsize=10, ha="center", va="top")
    yt = ax.text(0, 0, "", color=GREEN, fontsize=10, ha="right", va="center")
    Lt = ax.text(0, 0, f"L = {_g(L)}", color="#7C2D12", fontsize=10, ha="left", va="bottom")
    a1 = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>", mutation_scale=16, color=BLUE, lw=2.2, zorder=6)
    a2 = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>", mutation_scale=16, color=RED, lw=2.2, zorder=6)
    ax.add_patch(a1)
    ax.add_patch(a2)
    info = ax.text(0.98, 0.98, "", transform=ax.transAxes, ha="right", va="top", fontsize=10, zorder=30,
                   multialignment="left",
                   bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#D1D5DB", alpha=0.94))
    # y(t) graph
    tt = np.linspace(0, T, 300)
    yy = np.sqrt(np.maximum(L * L - (xs + sg * av * tt) ** 2, 0))
    gx.set_xlim(0, T)
    gx.set_ylim(0, L * 1.05)
    gx.grid(alpha=0.3)
    gx.tick_params(labelsize=9)
    gx.set_xlabel(_T(P, "t (s)", "t (s)"), fontsize=10)
    gx.set_ylabel("y (" + u + ")", fontsize=10)
    gx.set_title(_T(P, "Üst ucun yüksekliği y(t)", "Height of the top y(t)"), fontsize=11)
    gcur, = gx.plot([], [], color=GREEN, lw=2.4)
    gdot, = gx.plot([], [], "o", color=GREEN, ms=8)
    gtan, = gx.plot([], [], "--", color=RED, lw=1.8)
    gtx = gx.text(0, 0, "", color=RED, fontsize=10.5, fontweight="bold", ha="left", va="bottom")
    y0 = math.sqrt(L * L - x0 * x0)
    dy0 = -x0 * v / y0
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    N = 165

    def tof(i):
        if i < 14:
            return 0.0
        if i < 80:
            return t0 * _ramp(i, 14, 80)
        if i < 120:
            return t0
        return t0 + (T - t0) * _ramp(i, 120, 160)

    def update(i):
        t = tof(i)
        x, y = X(t), Y(t)
        lad.set_data([x, 0], [0, y])
        ends.set_data([x, 0], [0, y])
        xdim.set_data([0, x], [-0.03 * L, -0.03 * L])
        xt.set_position((x / 2, -0.035 * L))
        xt.set_text(f"x = {_g(x, 3)}")
        ydim.set_data([-0.11 * L, -0.11 * L], [0, y])
        yt.set_position((-0.13 * L, y / 2))
        yt.set_text(f"y = {_g(y, 3)}")
        Lt.set_position((x / 2 + 0.04 * L, y / 2 + 0.04 * L))
        dyv = -x * v / y if y > 1e-9 else -1e9
        s1 = 0.12 * L * (1 if v > 0 else -1)
        a1.set_positions((x, 0.04 * L), (x + s1, 0.04 * L))
        s2 = max(-0.45 * L, min(0.45 * L, 0.12 * L * dyv / av))
        a2.set_positions((-0.02 * L, y), (-0.02 * L, y + s2))
        k = int(np.searchsorted(tt, t, side="right"))
        gcur.set_data(tt[:max(k, 1)], yy[:max(k, 1)])
        gdot.set_data([t], [y])
        if 80 <= i:
            w = 0.18 * T
            gtan.set_data([t0 - w, t0 + w], [y0 - dy0 * w, y0 + dy0 * w])
            late = t0 > 0.55 * T
            gtx.set_position((t0 - 0.04 * T if late else t0 + 0.03 * T, y0 - 0.06 * L if late else y0 + 0.03 * L))
            gtx.set_ha("right" if late else "left")
            gtx.set_va("top" if late else "bottom")
            gtx.set_text(f"dy/dt = {_g(dy0, 4)} {u}/s")
        else:
            gtan.set_data([], [])
            gtx.set_text("")
        if i < 14:
            info.set_text(_T(P, f"x² + y² = {_g(L)}²\nalt uç {_g(av)} {u}/s ile kayıyor",
                             f"x² + y² = {_g(L)}²\nthe foot slides at {_g(av)} {u}/s"))
        elif i < 80:
            info.set_text(_T(P, f"x = {_g(x, 3)}, y = {_g(y, 3)}\ndy/dt = −(x/y)·dx/dt = {_g(dyv, 3)} {u}/s",
                             f"x = {_g(x, 3)}, y = {_g(y, 3)}\ndy/dt = −(x/y)·dx/dt = {_g(dyv, 3)} {u}/s"))
        elif i < 120:
            info.set_text(_T(P, f"x = {_g(x0)} anında:\ny = {sol['fmt']['y0']},  ", f"At x = {_g(x0)}:\ny = {sol['fmt']['y0']},  ")
                          + ans.split("  (")[0])
        else:
            info.set_text(_T(P, f"Sonra hızlanır: y = {_g(y, 3)}\ndy/dt = {_g(dyv, 3)} {u}/s",
                             f"Then it speeds up: y = {_g(y, 3)}\ndy/dt = {_g(dyv, 3)} {u}/s"))
        return []

    return N, update


def vary(P, rnd):
    trip = rnd.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (7, 24, 25), (9, 12, 15), (12, 16, 20)])
    a, b, c = trip
    if rnd.random() < 0.5:
        a, b = b, a
    v = rnd.choice([0.5, 1, 1.5, 2, 3])
    out = {"L": c, "v": v, "x0": a}
    if "unit" in P:
        out["unit"] = P["unit"]
    return out
'''),
}
EXAMPLES += [
    {"id": "calc1-ladder-1", "kind": "related_rates_ladder",
     "title": ("Duvardan kayan merdiven", "A ladder sliding down a wall"),
     "q": ("{L} {unit} uzunluğundaki bir merdivenin alt ucu duvardan {v} {unit}/s hızla uzaklaşıyor. Alt uç duvardan "
           "{x0} {unit} uzaktayken üst uç hangi hızla aşağı kayar?",
           "A {L} {unit} ladder leans against a wall and its foot slides away at {v} {unit}/s. How fast is the top "
           "sliding down when the foot is {x0} {unit} from the wall?"),
     "P": {"L": 10, "v": 2, "x0": 6, "unit": "m"}},
    {"id": "calc1-ladder-2", "kind": "related_rates_ladder",
     "topics": ["word problem", "sözel problem", "painter", "boyacı"],
     "title": ("Boyacının merdiveni", "The painter's ladder"),
     "q": ("Bir boyacının {L} {unit} merdiveni kayıyor; alt uç {v} {unit}/s hızla duvardan uzaklaşıyor. Alt uç "
           "{x0} {unit} uzaktayken üst ucun düşey hızı nedir? Neden üst uç sona doğru hızlanır?",
           "A painter's {L} {unit} ladder slips: its foot moves away from the wall at {v} {unit}/s. What is the "
           "vertical velocity of the top when the foot is {x0} {unit} out? Why does the top speed up near the end?"),
     "P": {"L": 13, "v": 0.5, "x0": 12, "unit": "m"}},
]


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["newton_method"] = {
    "course": "calc1",
    "title": ("Newton yöntemi: teğetlerle köke yaklaşma", "Newton's method: tangent lines to a root"),
    "topics": ["newton's method", "newtons method", "newton method", "newton-raphson", "newton raphson",
               "root finding", "approximating roots", "approximating zeros", "numerical methods",
               "linear approximation", "newton yöntemi", "kök bulma", "yaklaşık kök", "sayısal yöntem",
               "doğrusal yaklaşım"],
    "code": _code(r'''


def _analyze(P):
    key = _key("newton", P)
    if key in _CACHE:
        return _CACHE[key]
    x, f = _parse(P.get("f", "x**2 - 2"))
    A = {"ok": f is not None, "x": x, "f": f, "raw": str(P.get("f", "")), "vn": str(x)}
    A["fx"] = _pretty(_clean(A["raw"])) if f is not None else A["raw"].replace("{", "(").replace("}", ")")
    x0s = _sval(P.get("x0", 1))
    if not _finite(x0s):
        x0s = sp.Integer(1)
    try:
        n = int(P.get("n", 4))
    except Exception:
        n = 4
    n = max(1, min(10, n))
    A["x0s"], A["x0"], A["n"] = x0s, _fl(x0s), n
    if f is None:
        _CACHE[key] = A
        return A
    h = _num(f, x)
    d = None
    try:
        d = sp.diff(f, x)
        if d.has(sp.Derivative):
            d = None
    except Exception:
        d = None
    if d is not None:
        dh = _num(d, x)
    else:
        def dh(v, _h=h):
            v = np.asarray(v, dtype=float)
            e = 1e-6 * (1 + np.abs(v))
            return (_h(v + e) - _h(v - e)) / (2 * e)
    A["h"], A["dh"], A["d"] = h, dh, d
    its = []
    xk = A["x0"]
    status = "ok"
    for k in range(n):
        fk, dk = _h1(h, xk), _h1(dh, xk)
        if fk != fk or dk != dk:
            status = "undef"
            break
        if abs(dk) < 1e-14:
            status = "flat"
            break
        xn = xk - fk / dk
        its.append((k, xk, fk, dk, xn))
        if xn != xn or abs(xn) > 1e8:
            status = "div"
            break
        xk = xn
    A["its"], A["status"] = its, status
    xr, conv = xk, False
    if status == "ok":
        for _ in range(80):
            fr, dr = _h1(h, xr), _h1(dh, xr)
            if fr != fr or dr != dr or dr == 0:
                break
            xn = xr - fr / dr
            if abs(xn - xr) <= 1e-15 * (1 + abs(xr)):
                xr = xn
                break
            xr = xn
        conv = abs(_h1(h, xr)) < 1e-9 * (1 + abs(_h1(dh, xr)))
    A["root"], A["conv"] = xr, conv
    exact = None
    try:
        if conv and f.is_polynomial(x) and sp.degree(f, x) <= 2:
            for r in sp.solve(f, x):
                if _finite(r) and abs(_fl(r) - xr) < 1e-8:
                    exact = r
    except Exception:
        exact = None
    A["exact"] = exact
    # exact first iterates when everything is rational
    ex_it = []
    try:
        if d is not None and f.is_rational_function(x) and x0s.is_Rational:
            xe = x0s
            for k in range(min(2, len(its))):
                xe = sp.nsimplify(xe - f.subs(x, xe) / d.subs(x, xe))
                if not xe.is_Rational or xe.q > 10 ** 6:
                    break
                ex_it.append(xe)
    except Exception:
        ex_it = []
    A["ex_it"] = ex_it
    try:
        Nf = sp.simplify(x - f / d) if d is not None and sp.count_ops(f) <= 15 else None
        if Nf is not None and len(sp.sstr(Nf)) > 30:
            Nf = None
    except Exception:
        Nf = None
    A["Nf"] = Nf
    _CACHE[key] = A
    return A


def _xx(v):
    return _g(v, 11)


def solve(P):
    A = _analyze(P)
    vn = A["vn"]
    fmt = {"fx": A["fx"], "pretty_f": A["fx"], "x0": _at(A["x0s"]), "n": str(A["n"])}
    if not A["ok"]:
        return {"answer": ("İfade çözümlenemedi", "Could not parse the expression"),
                "steps": [(f"Girdi: {A['raw']}", f"Input: {A['raw']}"),
                          ("İfadeyi x değişkeniyle, * ve ** kullanarak yazın.",
                           "Write the expression in x using * and **.")], "fmt": fmt}
    ds = _ps(A["d"]) if A["d"] is not None else _T(P, "(sayısal)", "(numerical)")
    st = [(f"f({vn}) = {A['fx']},  f'({vn}) = {ds}", f"f({vn}) = {A['fx']},  f'({vn}) = {ds}")]
    nf = f"  = {_ps(A['Nf'])}" if A["Nf"] is not None else ""
    st.append((f"Newton adımı: {vn}ₖ₊₁ = {vn}ₖ − f({vn}ₖ)/f'({vn}ₖ){nf}  (teğet doğrunun {vn} eksenini kestiği yer)",
               f"Newton step: {vn}ₖ₊₁ = {vn}ₖ − f({vn}ₖ)/f'({vn}ₖ){nf}  (where the tangent line meets the {vn}-axis)"))
    for k, xk, fk, dk, xn in A["its"]:
        ex_ = ""
        if k < len(A["ex_it"]) and A["ex_it"][k].q <= 100000:
            q_ = A["ex_it"][k]
            ex_ = f" = {q_.p}/{q_.q}".replace("-", "−") if not q_.is_Integer else f" = {_ex(q_)}"
            if not q_.is_Integer:
                ex_ += f" ≈ {_xx(xn)}"
        else:
            ex_ = f" ≈ {_xx(xn)}"
        line = f"{vn}{_sub(k + 1)} = {_xx(xk)} − ({_g(fk, 7)})/({_g(dk, 7)}){ex_}"
        st.append((line, line))
    stt = A["status"]
    if stt == "flat":
        st.append(("f'(xₖ) = 0: teğet yatay, x eksenini kesmez ⇒ yöntem durur. Başka bir başlangıç değeri seçin.",
                   "f'(xₖ) = 0: the tangent is horizontal and never meets the axis ⇒ the method stops. Pick another start."))
    elif stt == "div":
        st.append(("Ardışık değerler büyüyerek uzaklaşıyor ⇒ bu başlangıçla yöntem ıraksıyor.",
                   "The iterates run away ⇒ the method diverges from this start."))
    elif stt == "undef":
        st.append(("f ya da f' bir iterasyonda tanımsız ⇒ yöntem durdu.",
                   "f or f' is undefined at an iterate ⇒ the method stopped."))
    its = A["its"]
    if not its:
        return {"answer": ("Newton yöntemi başlatılamadı (f'(x₀) = 0 ya da tanımsız)",
                           "Newton's method could not start (f'(x₀) = 0 or undefined)"), "steps": st, "fmt": fmt}
    last = its[-1][4]
    m = len(its)
    fl = _h1(A["h"], last)
    if A["conv"]:
        rt = _xx(A["root"])
        exs = f" (= {_ps(A['exact'])})" if A["exact"] is not None else ""
        st.append((f"{vn}{_sub(m)} ≈ {_xx(last)},  f({vn}{_sub(m)}) ≈ {_g(fl, 3)};  gerçek kök ≈ {rt}{exs}",
                   f"{vn}{_sub(m)} ≈ {_xx(last)},  f({vn}{_sub(m)}) ≈ {_g(fl, 3)};  true root ≈ {rt}{exs}"))
        errs = [abs(it[1] - A["root"]) for it in its] + [abs(last - A["root"])]
        et = ", ".join(_g(e, 2) for e in errs)
        st.append((f"Hatalar |{vn}ₖ − kök|: {et}  — her adımda doğru basamak sayısı kabaca iki katına çıkar (karesel yakınsama).",
                   f"Errors |{vn}ₖ − root|: {et}  — the number of correct digits roughly doubles each step (quadratic convergence)."))
    fmt["root"] = _xx(last)
    ans = (f"{vn} ≈ {_xx(last)}  ({vn}{_sub(m)}, {m} adım)", f"{vn} ≈ {_xx(last)}  ({vn}{_sub(m)}, {m} steps)")
    if stt != "ok":
        ans = (ans[0] + " — yöntem durdu", ans[1] + " — the method stopped")
    return {"answer": ans, "steps": st, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    A = _analyze(P)
    if not A["ok"]:
        return _badfig(fig, P, _T(P, "İfade çözümlenemedi", "Could not parse the expression"))
    h, vn, its = A["h"], A["vn"], A["its"]
    m = len(its)
    x0 = A["x0"]
    r = A["root"] if A["conv"] else (its[-1][4] if its else x0)
    pts = [x0] + [it[4] for it in its]
    w0 = max(1.5 * abs(x0 - r), 1.2, 0.8 * max([abs(p - x0) for p in pts] + [0.0]))
    views = [((x0 + r) / 2 if A["conv"] else x0, w0)]
    wmin = w0 * 0.004
    for k in range(1, m + 1):
        xa_ = pts[k]
        xb_ = pts[k + 1] if k + 1 < len(pts) else r
        span = max(abs(xa_ - xb_), abs(xa_ - r))
        w = min(views[-1][1], max(0.9 * span, wmin) * 1.6)
        views.append((0.5 * (xa_ + xb_), w))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.6, 1], left=0.07, right=0.99, top=0.9, bottom=0.1, wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    tb = fig.add_subplot(gs[0, 1])
    tb.axis("off")
    tb.set_xlim(0, 1)
    tb.set_ylim(0, 1)
    _axes_style(ax)
    ax.set_xlabel(vn, fontsize=10)
    ax.set_title(_mt(f"f({vn}) = " + sp.latex(A["f"]) + r",\ \ " + vn + "_0 = " + sp.latex(A["x0s"]),
                     f"f({vn}) = {A['fx']},  {vn}₀ = {_at(A['x0s'])}"), fontsize=12)
    curve, = ax.plot([], [], color=BLUE, lw=2.4, zorder=3)
    vls, tls, cps, axd = [], [], [], []
    for k in range(m):
        vls.append(ax.plot([], [], "--", color=GRAY, lw=1.3, zorder=2)[0])
        tls.append(ax.plot([], [], color=ORANGE, lw=2.0, zorder=4)[0])
        cps.append(ax.plot([], [], "o", color=RED, ms=7, zorder=6)[0])
    xdots, = ax.plot([], [], "o", color="#111827", ms=7, zorder=7)
    xlab = [ax.text(0, 0, "", fontsize=11, color="#111827", ha="center", va="top", zorder=8) for _ in range(2)]
    rstar, = ax.plot([], [], "*", color=GREEN, ms=18, zorder=9, mec="white")
    info = _info(ax, 10.5)
    tb.text(0.02, 0.985, _T(P, "İterasyon tablosu", "Iteration table"), fontsize=11, fontweight="bold", va="top")
    tb.text(0.02, 0.92, f"k   {vn}ₖ", fontsize=9.5, family="DejaVu Sans Mono", color=GRAY, va="top")
    tb.text(0.62, 0.92, f"f({vn}ₖ)", fontsize=9.5, family="DejaVu Sans Mono", color=GRAY, va="top")
    rows = []
    step = min(0.075, 0.82 / (m + 2))
    for k in range(m + 1):
        y = 0.86 - k * step
        xv = pts[k]
        fv = _h1(h, xv)
        c1 = tb.text(0.02, y, f"{k:<3d} {xv:.10f}" if abs(xv) < 1e5 else f"{k:<3d} {_g(xv, 6)}", fontsize=9,
                     family="DejaVu Sans Mono", va="top", alpha=0)
        c2 = tb.text(0.62, y, _g(fv, 4), fontsize=9, family="DejaVu Sans Mono", va="top", alpha=0,
                     color=GREEN if abs(fv) < 1e-6 else "#111827")
        rows.append((c1, c2))
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    F = max(14, min(32, (150 - 38) // max(m, 1)))
    N = 16 + m * F + 22

    def view_at(i):
        if i < 16 or m == 0:
            return views[0]
        k = min(m - 1, (i - 16) // F)
        if i >= 16 + m * F:
            return views[m]
        u = ((i - 16) - k * F) / float(F)
        if u < 0.7:
            return views[k]
        t = _ramp(u, 0.7, 1.0)
        t = t * t * (3 - 2 * t)
        (c1, w1), (c2, w2) = views[k], views[k + 1]
        return (c1 + (c2 - c1) * t, math.exp(math.log(w1) + (math.log(w2) - math.log(w1)) * t))

    def update(i):
        c, w = view_at(i)
        X = np.linspace(c - w, c + w, 400)
        Y = h(X)
        k_now = -1 if i < 16 else min(m - 1, (i - 16) // F)
        extra = [0.0]
        if 0 <= k_now < m:
            extra.append(its[k_now][2])
        lo, hi = _yr(Y, extra, pad=0.15)
        ax.set_xlim(c - w, c + w)
        ax.set_ylim(lo, hi)
        p = _ramp(i, 0, 14)
        mm = max(2, int(p * len(X))) if i < 16 else len(X)
        curve.set_data(X[:mm], _brk(Y, hi - lo)[:mm])
        shown = [x0] if i >= 6 else []
        for k in range(m):
            _, xk, fk, dk, xn = its[k]
            start = 16 + k * F
            u = (i - start) / float(F)
            if u < 0:
                vls[k].set_data([], [])
                tls[k].set_data([], [])
                cps[k].set_data([], [])
                continue
            a1 = _ramp(u, 0.0, 0.25)
            vls[k].set_data([xk, xk], [0, fk * a1])
            cps[k].set_data([xk], [fk]) if a1 >= 1 else cps[k].set_data([], [])
            a2 = _ramp(u, 0.25, 0.6)
            if a2 > 0:
                ex_x = xn + 0.3 * (xn - xk)
                ex_y = -0.3 * fk
                ex_x = xk + (ex_x - xk) * a2
                ex_y = fk + (ex_y - fk) * a2
                tls[k].set_data([xk, ex_x], [fk, ex_y])
            else:
                tls[k].set_data([], [])
            al = 1.0 if k == k_now else 0.45
            tls[k].set_alpha(al)
            vls[k].set_alpha(al)
            if u >= 0.6:
                shown.append(xn)
        xdots.set_data(shown, [0] * len(shown))
        lab_idx = [len(shown) - 2, len(shown) - 1] if len(shown) >= 2 else [0]
        for j, t in enumerate(xlab):
            if j < len(lab_idx) and lab_idx[j] >= 0 and shown:
                q = lab_idx[j]
                t.set_position((shown[q], -0.03 * (hi - lo)))
                t.set_text(f"{vn}{_sub(q)}")
            else:
                t.set_text("")
        for k, (c1, c2) in enumerate(rows):
            al = 1.0 if (k == 0 and i >= 6) or (k > 0 and i >= 16 + (k - 1) * F + 0.6 * F) else 0.0
            c1.set_alpha(al)
            c2.set_alpha(al)
        fin = i >= 16 + m * F
        if fin and A["conv"]:
            rstar.set_data([r], [0])
        else:
            rstar.set_data([], [])
        if i < 16:
            info.set_text(_T(P, f"Başlangıç: {vn}₀ = {_xx(x0)}", f"Start: {vn}₀ = {_xx(x0)}"))
        elif not fin:
            _, xk, fk, dk, xn = its[k_now]
            info.set_text(_T(P, f"{k_now + 1}. adım: ({vn}{_sub(k_now)}, f({vn}{_sub(k_now)})) noktasındaki teğet\n",
                             f"Step {k_now + 1}: tangent at ({vn}{_sub(k_now)}, f({vn}{_sub(k_now)}))\n")
                          + f"{vn}{_sub(k_now + 1)} = {_g(xk, 8)} − ({_g(fk, 4)})/({_g(dk, 4)})\n   = {_xx(xn)}")
        else:
            info.set_text(ans + "\n" + _T(P, f"görüntü ×{_g(w0 / w, 3)} yakınlaştırıldı", f"view zoomed ×{_g(w0 / w, 3)}"))
        return []

    return N, update


def vary(P, rnd):
    x, f = _parse(P.get("f", "x**2 - 2"))
    vn = str(x)
    raw = str(P.get("f", "")).lower()
    n = int(P.get("n", 4)) if str(P.get("n", 4)).isdigit() else 4
    if "cos" in raw:
        c = rnd.choice([1, 2, 3])
        return {"f": f"cos({vn}) - {vn}" if c == 1 else f"cos({vn}) - {vn}/{c}", "x0": 1, "n": n}
    if "**3" in raw:
        a = rnd.choice([1, 2, 3])
        b = rnd.choice([1, 3, 4, 5, 7])
        g = sp.Symbol(vn)
        hh = _num(g ** 3 - a * g - b, g)
        z = _zeros(hh, -10, 10)
        x0 = int(round(z[-1])) if z else 2
        if x0 == 0:
            x0 = 1
        return {"f": f"{vn}**3 - {a}*{vn} - {b}" if a != 1 else f"{vn}**3 - {vn} - {b}", "x0": x0, "n": n}
    k = rnd.choice([2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 17, 19])
    x0 = int(math.isqrt(k)) + 1
    return {"f": f"{vn}**2 - {k}", "x0": x0, "n": n}
'''),
}
EXAMPLES += [
    {"id": "calc1-newton-1", "kind": "newton_method", "topics": ["square root", "karekök"],
     "title": ("Newton yöntemiyle √2", "√2 by Newton's method"),
     "q": ("f(x) = {pretty_f} fonksiyonunun pozitif kökünü x₀ = {x0} başlangıcıyla Newton yönteminin {n} adımıyla "
           "yaklaşık bul.",
           "Approximate the positive root of f(x) = {pretty_f} with {n} steps of Newton's method starting "
           "at x₀ = {x0}."),
     "P": {"f": "x**2 - 2", "x0": 1, "n": 4}},
    {"id": "calc1-newton-2", "kind": "newton_method",
     "title": ("Kübik denklemin kökü", "A root of a cubic equation"),
     "q": ("{pretty_f} = 0 denkleminin gerçek kökünü x₀ = {x0} ile başlayıp {n} Newton adımıyla hesapla.",
           "Find the real root of {pretty_f} = 0 with {n} Newton steps starting from x₀ = {x0}."),
     "P": {"f": "x**3 - 2*x - 5", "x0": 2, "n": 4}},
    {"id": "calc1-newton-3", "kind": "newton_method", "topics": ["transcendental equation", "fixed point"],
     "title": ("cos x = x denklemi", "Solving cos x = x"),
     "q": ("cos x = x denklemini f(x) = {pretty_f} = 0 olarak yaz ve x₀ = {x0} ile {n} Newton adımı uygula.",
           "Write cos x = x as f(x) = {pretty_f} = 0 and apply {n} Newton steps from x₀ = {x0}."),
     "P": {"f": "cos(x) - x", "x0": 1, "n": 4}},
]


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["mean_value_theorem"] = {
    "course": "calc1",
    "title": ("Ortalama değer teoremi: kesene paralel teğet", "Mean value theorem: a tangent parallel to the secant"),
    "topics": ["mean value theorem", "mvt", "rolle's theorem", "rolles theorem", "rolle", "average rate of change",
               "instantaneous rate of change", "secant slope", "ortalama değer teoremi", "rolle teoremi",
               "ortalama değişim hızı", "kesen eğimi", "anlık değişim hızı"],
    "code": _code(r'''


def _analyze(P):
    key = _key("mvt", P)
    if key in _CACHE:
        return _CACHE[key]
    x, f = _parse(P.get("f", "x"))
    A = {"ok": f is not None, "x": x, "f": f, "raw": str(P.get("f", "")), "vn": str(x)}
    A["fx"] = _pretty(_clean(A["raw"])) if f is not None else A["raw"].replace("{", "(").replace("}", ")")
    a, b = _sval(P.get("a", 0)), _sval(P.get("b", 1))
    if not (_finite(a) and _finite(b)):
        a, b = sp.Integer(0), sp.Integer(1)
    if _fl(a) > _fl(b):
        a, b = b, a
    if a == b:
        b = a + 1
    A["a"], A["b"], A["af"], A["bf"] = a, b, _fl(a), _fl(b)
    A["sa"], A["sb"] = _at(a), _at(b)
    if f is None:
        _CACHE[key] = A
        return A
    h = _num(f, x)
    A["h"] = h
    af, bf = A["af"], A["bf"]
    fa, fb = None, None
    try:
        fa, fb = _simp(f.subs(x, a)), _simp(f.subs(x, b))
        if not (_finite(fa) and _finite(fb)):
            fa = fb = None
    except Exception:
        fa = fb = None
    if fa is None:
        va, vb = _h1(h, af), _h1(h, bf)
        if va == va and vb == vb:
            fa, fb = sp.Float(va, 10), sp.Float(vb, 10)
    A["fa"], A["fb"] = fa, fb
    d = None
    try:
        d = sp.diff(f, x)
        if d.has(sp.Derivative):
            d = None
    except Exception:
        d = None
    if d is not None:
        try:
            d = sp.expand(d) if d.is_polynomial(x) else d
        except Exception:
            pass
        dh = _num(d, x)
    else:
        def dh(v, _h=h):
            v = np.asarray(v, dtype=float)
            e = 1e-6 * (1 + np.abs(v))
            return (_h(v + e) - _h(v - e)) / (2 * e)
    A["d"], A["dh"] = d, dh
    # hypotheses
    xs = np.linspace(af, bf, 2001)
    ys = h(xs)
    cont = bool(np.all(np.isfinite(ys))) and not _poles(h, af, bf)
    if cont:
        dyy = np.abs(np.diff(ys))
        med = float(np.median(dyy)) + 1e-12
        if np.any(dyy > 60 * med + 1e-6 * (1 + float(np.nanmax(np.abs(ys))))):
            cont = False
    ds = dh(xs[1:-1])
    diffb = cont and bool(np.all(np.isfinite(ds)))
    if diffb:
        dd = np.abs(np.diff(ds))
        med = float(np.median(dd)) + 1e-12
        spn = float(np.max(ds) - np.min(ds)) + 1e-12
        if np.any((dd > 60 * med) & (dd > 0.2 * spn)):
            diffb = False
    A["cont"], A["diffb"] = cont, diffb
    m = None
    if fa is not None and fb is not None:
        m = _simp((fb - fa) / (b - a))
    A["m"] = m
    cs = []
    if m is not None:
        try:
            if d is not None:
                sol = sp.solveset(sp.Eq(d, m), x, sp.Interval.open(a, b))
                if isinstance(sol, sp.FiniteSet):
                    cs = [(_simp(c), _fl(c)) for c in sol if _finite(c)]
                else:
                    raise ValueError
            else:
                raise ValueError
        except Exception:
            mf = _fl(m)

            def g(v, _d=dh, _m=mf):
                return _d(v) - _m
            cs = [(None, z) for z in _zeros(g, af, bf) if af < z < bf]
    cs = sorted(cs, key=lambda t: t[1])[:6]
    A["cs"] = cs
    _CACHE[key] = A
    return A


def solve(P):
    A = _analyze(P)
    vn = A["vn"]
    fmt = {"fx": A["fx"], "pretty_f": A["fx"], "a": A["sa"], "b": A["sb"]}
    if not A["ok"]:
        return {"answer": ("İfade çözümlenemedi", "Could not parse the expression"),
                "steps": [(f"Girdi: {A['raw']}", f"Input: {A['raw']}"),
                          ("İfadeyi x değişkeniyle, * ve ** kullanarak yazın.",
                           "Write the expression in x using * and **.")], "fmt": fmt}
    sa, sb = A["sa"], A["sb"]
    st = []
    if A["cont"] and A["diffb"]:
        st.append((f"Koşullar: f, [{sa}, {sb}] üzerinde sürekli ve ({sa}, {sb}) üzerinde türevlenebilir ✓",
                   f"Hypotheses: f is continuous on [{sa}, {sb}] and differentiable on ({sa}, {sb}) ✓"))
    else:
        st.append(((f"Koşul sağlanmıyor: f [{sa}, {sb}] üzerinde sürekli değil" if not A["cont"] else
                    f"Koşul sağlanmıyor: f ({sa}, {sb}) üzerinde her yerde türevlenebilir değil") +
                   " ⇒ teorem bir c garanti etmez.",
                   (f"Hypothesis fails: f is not continuous on [{sa}, {sb}]" if not A["cont"] else
                    f"Hypothesis fails: f is not differentiable everywhere on ({sa}, {sb})") +
                   " ⇒ the theorem does not guarantee a c."))
    if A["m"] is None:
        st.append(("f uç noktalarda tanımsız; kesen eğimi hesaplanamaz.", "f is undefined at an endpoint; no secant slope."))
        return {"answer": ("Teorem uygulanamaz (f uç noktada tanımsız)", "The theorem does not apply (f undefined at an endpoint)"),
                "steps": st, "fmt": fmt}
    fa, fb, m = A["fa"], A["fb"], A["m"]
    st.append((f"f({sa}) = {_ex(fa)},  f({sb}) = {_ex(fb)}", f"f({sa}) = {_ex(fa)},  f({sb}) = {_ex(fb)}"))
    st.append((f"Kesen eğimi (ortalama değişim): m = [f({sb}) − f({sa})]/({sb} − {sa}) = ({_short(fb - fa)})/({_short(A['b'] - A['a'])}) = {_ex(m)}",
               f"Secant slope (average rate of change): m = [f({sb}) − f({sa})]/({sb} − {sa}) = ({_short(fb - fa)})/({_short(A['b'] - A['a'])}) = {_ex(m)}"))
    ds = _ps(A["d"]) if A["d"] is not None else "f'"
    eqs = ""
    out_t = out_e = ""
    if A["d"] is not None:
        try:
            cc = sp.Symbol("c", real=True)
            eqs = f":  {_ps(A['d'].subs(A['x'], cc))} = {_short(m)}"
            alls = sp.solveset(sp.Eq(A["d"], m), A["x"], sp.S.Reals)
            if isinstance(alls, sp.FiniteSet):
                outs = [r for r in alls if _finite(r) and not (A["af"] < _fl(r) < A["bf"])]
                if outs:
                    o = ", ".join(_ex(r) for r in outs[:4])
                    out_t = f"  ({o} aralık dışında kalır)"
                    out_e = f"  ({o} lies outside the interval)"
        except Exception:
            eqs = ""
    st.append((f"f'({vn}) = {ds};  f'(c) = m denklemini ({sa}, {sb}) aralığında çöz{eqs}",
               f"f'({vn}) = {ds};  solve f'(c) = m on ({sa}, {sb}){eqs}"))
    cs = A["cs"]
    if cs:
        ct = ", ".join((_ex(c) if c is not None else "≈ " + _g(z, 7)) for c, z in cs)
        st.append((f"c = {ct}  ∈ ({sa}, {sb}) ✓{out_t}  — bu noktada teğet, kesene paraleldir.",
                   f"c = {ct}  ∈ ({sa}, {sb}) ✓{out_e}  — here the tangent line is parallel to the secant."))
        if abs(_fl(m)) < 1e-12:
            st.append(("f(a) = f(b) olduğundan bu, Rolle teoremidir: f'(c) = 0 (yatay teğet).",
                       "Since f(a) = f(b) this is Rolle's theorem: f'(c) = 0 (horizontal tangent)."))
        fmt["c"] = ct
        ans = (f"m = {_short(m)};  c = {ct}", f"m = {_short(m)};  c = {ct}")
    else:
        st.append((f"({sa}, {sb}) içinde f'(c) = m sağlayan c yok.", f"No c in ({sa}, {sb}) satisfies f'(c) = m."))
        ans = (f"m = {_short(m)};  uygun c yok", f"m = {_short(m)};  no such c")
    return {"answer": ans, "steps": st, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") != "en"
    A = _analyze(P)
    if not A["ok"]:
        return _badfig(fig, P, _T(P, "İfade çözümlenemedi", "Could not parse the expression"))
    h, dh, af, bf, vn = A["h"], A["dh"], A["af"], A["bf"], A["vn"]
    pad = 0.12 * (bf - af)
    X = np.linspace(af - pad, bf + pad, 600)
    Y = h(X)
    DY = dh(X)
    ok = A["m"] is not None
    mf = _fl(A["m"]) if ok else float("nan")
    fa, fb = (_fl(A["fa"]), _fl(A["fb"])) if ok else (float("nan"), float("nan"))
    inside = (X >= af) & (X <= bf)
    ylo, yhi = _yr(Y[inside], [fa, fb], pad=0.18)
    dlo, dhi = _yr(DY[inside], [mf, 0.0], pad=0.18)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.75, 1], left=0.085, right=0.98, top=0.93, bottom=0.08, hspace=0.3)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[1, 0], sharex=ax)
    ax.set_xlim(X[0], X[-1])
    ax.set_ylim(ylo, yhi)
    bx.set_ylim(dlo, dhi)
    _axes_style(ax)
    _axes_style(bx)
    bx.set_xlabel(vn, fontsize=10)
    ax.set_title(_mt(f"f({vn}) = " + sp.latex(A["f"]) + r",\ \ [" + sp.latex(A["a"]) + ", " + sp.latex(A["b"]) + "]",
                     f"f({vn}) = {A['fx']},  [{A['sa']}, {A['sb']}]"), fontsize=12)
    bx.text(0.01, 0.95, _T(P, f"f'({vn}) ve y = m (kesen eğimi)", f"f'({vn}) and y = m (secant slope)"),
            transform=bx.transAxes, fontsize=10, va="top", color=PURPLE,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85), zorder=20)
    Yb = _brk(Y, yhi - ylo)
    DYb = _brk(DY, dhi - dlo)
    curve, = ax.plot([], [], color=BLUE, lw=2.4, zorder=3)
    ab, = ax.plot([], [], "o", color="#111827", ms=8, zorder=7)
    abl = [ax.text(0, 0, "", fontsize=10, zorder=8) for _ in range(2)]
    sec, = ax.plot([], [], color=ORANGE, lw=2.2, zorder=4)
    mtan, = ax.plot([], [], color=GRAY, lw=2.2, zorder=5)
    mdot, = ax.plot([], [], "o", color=GRAY, ms=7, zorder=6)
    ctans = [ax.plot([], [], color=GREEN, lw=2.4, zorder=5)[0] for _ in A["cs"]]
    cdots, = ax.plot([], [], "o", color=GREEN, ms=9, zorder=7)
    clabs = [ax.text(0, 0, "", color=GREEN, fontsize=11, fontweight="bold", ha="center", va="top", zorder=9)
             for _ in A["cs"]]
    dcur, = bx.plot([], [], color=PURPLE, lw=2.2)
    ddot, = bx.plot([], [], "o", color=GRAY, ms=7)
    mline, = bx.plot([], [], "--", color=ORANGE, lw=1.6)
    cdd, = bx.plot([], [], "o", color=GREEN, ms=9, zorder=6)
    cvl = [bx.plot([], [], ":", color=GREEN, lw=1.4)[0] for _ in A["cs"]]
    info = _info(ax, 10.5, X, Y)
    sol = solve(P)
    ans = sol["answer"][0 if tr else 1]
    L2 = 0.18 * (bf - af)
    N = 150
    czs = [z for _, z in A["cs"]]

    def update(i):
        p = _ramp(i, 0, 18)
        mm = max(2, int(p * len(X)))
        curve.set_data(X[:mm], Yb[:mm])
        if i >= 12 and ok:
            ab.set_data([af, bf], [fa, fb])
            abl[0].set_position((af, fa))
            abl[0].set_text("  A")
            abl[1].set_position((bf, fb))
            abl[1].set_text("  B")
        else:
            ab.set_data([], [])
            for t in abl:
                t.set_text("")
        q = _ramp(i, 20, 38)
        if q > 0 and ok:
            e = af + (bf - af) * q
            sec.set_data([af, e], [fa, fa + mf * (e - af)])
        else:
            sec.set_data([], [])
        if i >= 30 and ok:
            mline.set_data([X[0], X[-1]], [mf, mf])
        else:
            mline.set_data([], [])
        u = _ramp(i, 40, 115)
        if 40 <= i < 118:
            xt = af + (bf - af) * u
            yt, st_ = _h1(h, xt), _h1(dh, xt)
            near = ok and st_ == st_ and abs(st_ - mf) < 0.04 * (abs(dhi - dlo) + 1e-9)
            if yt == yt and st_ == st_:
                mtan.set_data([xt - L2, xt + L2], [yt - st_ * L2, yt + st_ * L2])
                mtan.set_color(GREEN if near else GRAY)
                mdot.set_data([xt], [yt])
                ddot.set_data([xt], [st_])
            else:
                mtan.set_data([], [])
                mdot.set_data([], [])
                ddot.set_data([], [])
            k = max(2, int(np.searchsorted(X, xt)))
            dcur.set_data(X[:k], DYb[:k])
        else:
            mtan.set_data([], [])
            mdot.set_data([], [])
            ddot.set_data([], [])
            dcur.set_data(X, DYb) if i >= 118 else dcur.set_data([], [])
        fin = i >= 118
        for k, z in enumerate(czs):
            if fin:
                yz = _h1(h, z)
                W2 = 0.45 * (bf - af)
                ctans[k].set_data([z - W2, z + W2], [yz - mf * W2, yz + mf * W2])
                clabs[k].set_position((z, yz - 0.05 * (yhi - ylo)))
                clabs[k].set_text("c" + (_sub(k + 1) if len(czs) > 1 else ""))
                cvl[k].set_data([z, z], [dlo, mf])
            else:
                ctans[k].set_data([], [])
                clabs[k].set_text("")
                cvl[k].set_data([], [])
        if fin:
            cdots.set_data(czs, [_h1(h, z) for z in czs])
            cdd.set_data(czs, [mf] * len(czs))
        else:
            cdots.set_data([], [])
            cdd.set_data([], [])
        if i < 20:
            info.set_text(_T(P, f"1) f, [{A['sa']}, {A['sb']}] üzerinde", f"1) f on [{A['sa']}, {A['sb']}]"))
        elif i < 40:
            info.set_text(_T(P, f"2) Kesen AB: m = {_short(A['m']) if ok else '?'}",
                             f"2) Secant AB: m = {_short(A['m']) if ok else '?'}"))
        elif not fin:
            xt = af + (bf - af) * u
            info.set_text(_T(P, f"3) Teğeti kaydır: f'({_g(xt, 3)}) = {_g(_h1(dh, xt), 4)}\nhedef: m = {_g(mf, 4)}",
                             f"3) Slide the tangent: f'({_g(xt, 3)}) = {_g(_h1(dh, xt), 4)}\ntarget: m = {_g(mf, 4)}"))
        else:
            info.set_text("4) " + ans.replace(";  ", "\n"))
        return []

    return N, update


def vary(P, rnd):
    x, f = _parse(P.get("f", "x"))
    vn = str(x)
    raw = str(P.get("f", "")).lower()
    if "sqrt" in raw:
        p_ = rnd.choice([0, 1, 2])
        q_ = p_ + rnd.choice([2, 4])
        return {"f": f"sqrt({vn})", "a": p_ * p_, "b": q_ * q_}
    if "**3" in raw:
        k = rnd.choice([-3, -2, -1, 1, 2])
        b = rnd.choice([1, 2, 3])
        return {"f": f"{vn}**3 - {abs(k)}*{vn}" if k < 0 else f"{vn}**3 + {k}*{vn}", "a": 0, "b": b}
    A_ = rnd.choice([10, 20, 30, 40])
    B_ = rnd.choice([5, 10, 15, 20])
    T = rnd.choice([2, 3, 4])
    return {"f": f"{A_}*{vn}**2 + {B_}*{vn}", "a": 0, "b": T}
'''),
}
EXAMPLES += [
    {"id": "calc1-mvt-1", "kind": "mean_value_theorem",
     "title": ("Kübik fonksiyonda ortalama değer teoremi", "Mean value theorem for a cubic"),
     "q": ("f(x) = {pretty_f} fonksiyonu [{a}, {b}] aralığında ortalama değer teoreminin koşullarını sağlar mı? "
           "Sağlıyorsa f'(c) = [f({b}) − f({a})]/({b} − {a}) olacak şekilde c değer(ler)ini bul.",
           "Does f(x) = {pretty_f} satisfy the hypotheses of the mean value theorem on [{a}, {b}]? If so, find "
           "all c with f'(c) = [f({b}) − f({a})]/({b} − {a})."),
     "P": {"f": "x**3 - x", "a": 0, "b": 2}},
    {"id": "calc1-mvt-2", "kind": "mean_value_theorem",
     "topics": ["word problem", "sözel problem", "speed", "hız", "average velocity", "ortalama hız"],
     "title": ("Hız göstergesi ortalama hızı gösterir", "The speedometer shows the average speed"),
     "q": ("Bir aracın konumu s(t) = {pretty_f} km (t saat, {a} ≤ t ≤ {b}). Ortalama hızı bul ve hız göstergesinin "
           "tam bu değeri gösterdiği bir t = c anı olduğunu göster.",
           "A car's position is s(t) = {pretty_f} km (t in hours, {a} ≤ t ≤ {b}). Find the average speed and show "
           "there is an instant t = c when the speedometer reads exactly this value."),
     "P": {"f": "30*t**2 + 15*t", "a": 0, "b": 2}},
    {"id": "calc1-mvt-3", "kind": "mean_value_theorem", "topics": ["square root", "karekök"],
     "title": ("Karekök fonksiyonu için c", "Finding c for the square-root function"),
     "q": ("f(x) = {pretty_f} için [{a}, {b}] aralığında ortalama değer teoremindeki c sayısını bul.",
           "For f(x) = {pretty_f} on [{a}, {b}], find the number c promised by the mean value theorem."),
     "P": {"f": "sqrt(x)", "a": 1, "b": 9}},
]
