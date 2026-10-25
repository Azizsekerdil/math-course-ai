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


def _num(f, x):
    # vectorised real evaluator: complex / inf / errors -> nan, never raises
    g = None
    try:
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


def _pretty(s):
    # "3*x**2 - 4*sqrt(x)" -> "3x² − 4√(x)"
    s = str(s).replace("**", "^")
    for a, b in (("sqrt", "√"), ("pi", "π"), ("oo", "∞"), ("Abs", "abs"), ("log", "ln"),
                 ("{", "("), ("}", ")")):
        s = s.replace(a, b)
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


def _info(ax, fs=10.5):
    return ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", ha="left", fontsize=fs,
                   zorder=30, bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#D1D5DB",
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
    if np.isfinite(ys[-1]) and ys[-1] == 0:
        out.append(float(xs[-1]))
    res = []
    for z in sorted(out):
        if not res or abs(z - res[-1]) > 1e-7 * (1 + abs(z)):
            res.append(z)
    return res


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
        A["at"] = _short(a)
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
        A["rows"] = [("", [(t, _h1(h, t)) for t in xs])]
    else:
        hs = [0.1, 0.01, 0.001, 0.0001]
        rows = []
        if side in ("", "-"):
            rows.append(("-", [(af - t, _h1(h, af - t)) for t in hs]))
        if side in ("", "+"):
            rows.append(("+", [(af + t, _h1(h, af + t)) for t in hs]))
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
            else:
                st.append((f"{n} > {m}: pay daha hızlı büyür ⇒ |f| sınırsız büyür (işareti baş katsayılar belirler).",
                           f"{n} > {m}: the numerator wins ⇒ |f| grows without bound (leading coefficients give the sign)."))
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
        for t, y in (rr[1:3] if not A["inf"] else [rr[0], rr[2], rr[5]]):
            parts.append(f"f({_g(t, 8)}) ≈ {_g(y)}")
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
    tag = {"hole": (f"  ({vn} = {at}'de delik)", f"  (hole at {vn} = {at})"),
           "remov": ("  (kaldırılabilir süreksizlik)", "  (removable discontinuity)"),
           "jump": (f"  (soldan {_pick(_lval2(L), True)}, sağdan {_pick(_lval2(R), True)})" if L and R else "",
                    f"  (left {_pick(_lval2(L), False)}, right {_pick(_lval2(R), False)})" if L and R else ""),
           "vasym": (f"  (dikey asimptot {vn} = {at})", f"  (vertical asymptote {vn} = {at})"),
           "hasym": (f"  (yatay asimptot y = {vt})", f"  (horizontal asymptote y = {ve})")}.get(kind, ("", ""))
    ans = (f"lim ({arrow}) f({vn}) = {vt}{tag[0]}", f"lim ({arrow}) f({vn}) = {ve}{tag[1]}")
    if kind == "jump" or (kind == "vasym" and res["k"] == "dne"):
        ans = (f"Limit yok{tag[0]}", f"The limit does not exist{tag[1]}")
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
        for t, v in rr:
            c1 = tb.text(0.04, y, _g(t, 8), fontsize=9.5, family="DejaVu Sans Mono", va="top", alpha=0)
            c2 = tb.text(0.52, y, _g(v, 7) if v == v else ("tanımsız" if tr else "undef."),
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
            rlab.set_position((af + 0.06 * W, lv + 0.04 * span))
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

    def update(i):
        q = _ramp(i, 22, 100)
        Rr = 10.0 ** (1 + 4 * q)
        if sg > 0:
            x0, x1 = -0.04 * Rr, 1.04 * Rr
        else:
            x0, x1 = -1.04 * Rr, 0.04 * Rr
        xs = np.linspace(x0, x1, 700)
        ys = h(xs)
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
