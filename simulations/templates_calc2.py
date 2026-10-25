# -*- coding: utf-8 -*-
"""Kalkülüs 2 simülasyonları: integral uygulamaları (eğriler arası alan, dönel
cisim hacmi, yay uzunluğu), integrasyon teknikleri (kısmi integrasyon,
genelleştirilmiş integral), seriler (Taylor polinomları, yakınsaklık
testleri), parametrik ve kutupsal eğriler.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Sorular kurs
kitaplarından KOPYALANMAZ: kendi ifademizle yazılmış, sayıları değiştirilmiş
tipik ders örnekleridir.

Ortak yardımcılar (_H) her kaynağın başına eklenir; böylece her kaynak yine
tek başına çalışır (düzenleyicide ve bağımsız betikte de).
"""

TEMPLATES = {}
EXAMPLES = []

# Ortak yardımcı kod: ifade ayrıştırma, sayısal değerlendirme, güzel yazım,
# Simpson integrali, güvenli sembolik integral.
_H = r'''
import math
import numpy as np
import sympy as sp
from fractions import Fraction

BLUE, ORANGE, GREEN, RED, PURPLE, GRAY = ("#2563EB", "#E07B39", "#16A34A", "#DC2626",
                                          "#7C3AED", "#6B7280")
_SUPM = dict(zip("0123456789-+()nxtk", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺⁽⁾ⁿˣᵗᵏ"))
_SUBM = dict(zip("0123456789-+()nk", "₀₁₂₃₄₅₆₇₈₉₋₊₍₎ₙₖ"))
_NAMES = {"pi": "π", "E": "e", "oo": "∞", "theta": "θ", "log": "ln", "I": "i", "zeta": "ζ"}
_BAD = (sp.Integral, sp.hyper, sp.meijerg, sp.exp_polar, sp.Piecewise, sp.gamma,
        sp.polylog, sp.LambertW, sp.erf, sp.erfi, sp.Si, sp.Ci, sp.Ei, sp.li,
        sp.fresnels, sp.fresnelc, sp.elliptic_e, sp.elliptic_f, sp.uppergamma,
        sp.lowergamma, sp.Shi, sp.Chi)


def _sup(s):
    s = str(s)
    if s and all(c in _SUPM for c in s):
        return "".join(_SUPM[c] for c in s)
    return "^" + (s if len(s) == 1 else "(" + s + ")")


def _sub(s):
    s = str(s)
    if s and all(c in _SUBM for c in s):
        return "".join(_SUBM[c] for c in s)
    return "_" + (s if len(s) == 1 else "(" + s + ")")


def _I(lo, hi):
    return "∫" + _sub(lo) + _sup(hi)


def _pps(s):
    out = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isalpha() or c == "_":
            j = i
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            w = s[i:j]
            if w in ("exp", "sqrt") and j < n and s[j] == "(":
                k, depth = j, 0
                while k < n:
                    if s[k] == "(":
                        depth += 1
                    elif s[k] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                inner = _pps(s[j + 1:k])
                if w == "exp":
                    ok = inner and all(ch in _SUPM for ch in inner)
                    out.append("e" + _sup(inner) if ok else ("e^" + inner if len(inner) == 1 else "e^(" + inner + ")"))
                else:
                    out.append("√" + inner if inner.isalnum() else "√(" + inner + ")")
                i = k + 1
                continue
            out.append(_NAMES.get(w, w))
            i = j
            continue
        if c == "*":
            if s.startswith("**", i):
                j = i + 2
                k = j + 1 if (j < n and s[j] == "-") else j
                while k < n and s[k].isdigit():
                    k += 1
                tok = s[j:k]
                if tok and tok != "-" and (k >= n or s[k] != "."):
                    out.append("".join(_SUPM[ch] for ch in tok))
                    i = k
                    continue
                if s.startswith("(-", j):
                    k = j + 2
                    while k < n and s[k].isdigit():
                        k += 1
                    if k > j + 2 and k < n and s[k] == ")":
                        out.append("⁻" + "".join(_SUPM[ch] for ch in s[j + 2:k]))
                        i = k + 1
                        continue
                out.append("^")
                i = j
                continue
            prev = out[-1][-1:] if out else ""
            nxt = s[i + 1:i + 2]
            if prev and prev in "0123456789" and (nxt.isalpha() or nxt == "("):
                i += 1
                continue
            out.append("·")
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _pp(e):
    try:
        if isinstance(e, sp.Pow) and e.exp.is_Rational and e.exp.is_negative and e.free_symbols:
            d = _pp(1 / e)
            depth, top = 0, False
            for ch in d:
                depth += 1 if ch == "(" else (-1 if ch == ")" else 0)
                top = top or (depth == 0 and ch in " ·/")
            return "1/" + ("(" + d + ")" if top else d)
        if isinstance(e, sp.Add) and not e.free_symbols:
            c, rest = e.as_coeff_Add()
            if c != 0 and rest != 0:
                rs = _pps(sp.sstr(rest))
                if not rs.startswith("-"):
                    return rs + (" - " + _pps(sp.sstr(-c)) if c < 0 else " + " + _pps(sp.sstr(c)))
        if isinstance(e, sp.Add) and len(e.free_symbols) == 1:
            v = list(e.free_symbols)[0]
            if not e.is_polynomial(v):
                c, rest = e.as_independent(v, as_Add=True)
                if c != 0 and rest != 0:
                    cs, rs = _pps(sp.sstr(c)), _pps(sp.sstr(rest))
                    return cs + (" - " + rs[1:] if rs.startswith("-") else " + " + rs)
        return _pps(sp.sstr(e))
    except Exception:
        return str(e)


def _g(v, d=4):
    try:
        v = float(v)
    except Exception:
        return "?"
    if not np.isfinite(v):
        return "∞" if v > 0 else ("-∞" if v < 0 else "?")
    if abs(v - round(v)) < 1e-9 * max(1.0, abs(v)) and abs(v) < 1e12:
        return str(int(round(v)))
    return f"{v:.{d}g}"


def _ex(val, d=5):
    try:
        val = sp.sympify(val)
        num = float(sp.N(val))
    except Exception:
        return "?"
    if val.is_Rational:
        return _pp(val)
    if val.has(sp.Float) or not val.is_number:
        return _g(num, d)
    s = _pp(val)
    if len(s) > 30:
        return _g(num, d)
    return s + " ≈ " + _g(num, d)


def _exa(val, d=5):
    out = _ex(val, d)
    try:
        v = sp.sympify(val)
        if v.is_Rational and not v.is_Integer:
            return out + " ≈ " + _g(float(v), d)
    except Exception:
        pass
    return out


def _parse(s, var="x", default="x"):
    v = sp.Symbol(var, real=True)
    loc = {var: v, "e": sp.E, "E": sp.E, "pi": sp.pi, "ln": sp.log}
    try:
        e = sp.sympify(str(s), locals=loc)
        if not isinstance(e, sp.Expr) or (e.free_symbols - {v}) or e.has(sp.I):
            raise ValueError("bad expression")
    except Exception:
        e = sp.sympify(default, locals=loc)
    return v, e


def _pv(v, default=0):
    try:
        if isinstance(v, bool):
            raise ValueError("bool")
        if isinstance(v, int):
            e = sp.Integer(v)
        elif isinstance(v, float):
            e = sp.Float(v, 6)
            if abs(v) < 1e9:
                c = sp.nsimplify(v, [sp.pi], tolerance=1e-10)
                if len(sp.sstr(c)) <= 10 and abs(float(c) - v) < 1e-9:
                    e = c
                elif len(str(v)) <= 8:
                    e = sp.Rational(str(v))
        else:
            e = sp.sympify(str(v), locals={"pi": sp.pi, "e": sp.E, "E": sp.E})
        fv = float(sp.N(e))
        if not np.isfinite(fv):
            raise ValueError("inf")
        return e, fv
    except Exception:
        return sp.sympify(default), float(sp.N(sp.sympify(default)))


def _num(e, v):
    try:
        g = sp.lambdify(v, e, "numpy")
    except Exception:
        g = None
    try:
        gm = sp.lambdify(v, e, "math")
    except Exception:
        gm = None

    def h(t):
        t = np.asarray(t, dtype=float)
        out = None
        if g is not None:
            try:
                with np.errstate(all="ignore"):
                    out = np.asarray(g(t), dtype=complex)
            except Exception:
                out = None
        if out is None:
            vals = []
            for tv in t.ravel():
                try:
                    vals.append(complex(gm(float(tv))) if gm is not None else complex(np.nan))
                except Exception:
                    vals.append(complex(np.nan))
            out = np.array(vals, dtype=complex).reshape(t.shape) if t.shape else np.array(vals[0])
        with np.errstate(all="ignore"):
            out = np.where(np.abs(out.imag) < 1e-9, out.real, np.nan).astype(float)
        return np.array(np.broadcast_to(out, t.shape), dtype=float)
    return h


def _at1(h, t):
    return float(h(np.array([float(t)]))[0])


def _simp(h, a, b, n=2000):
    n += n % 2
    xs = np.linspace(a, b, n + 1)
    ys = h(xs)
    ys = np.where(np.isfinite(ys), ys, 0.0)
    w = np.ones(n + 1)
    w[1:-1:2] = 4
    w[2:-1:2] = 2
    return float((b - a) / (3 * n) * np.sum(w * ys))


def _cum(xs, ys):
    ys = np.where(np.isfinite(ys), ys, 0.0)
    return np.concatenate([[0.0], np.cumsum((ys[1:] + ys[:-1]) * np.diff(xs) / 2)])


def _ylim(arrs, pad=0.12, zero=True, pct=1):
    vals = [np.asarray(a, dtype=float).ravel() for a in arrs]
    vals = np.concatenate(vals) if vals else np.array([])
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return -1.0, 1.0
    lo, hi = float(np.percentile(vals, pct)), float(np.percentile(vals, 100 - pct))
    if zero:
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    if hi - lo < 1e-9:
        lo, hi = lo - 1, hi + 1
    p = (hi - lo) * pad
    return lo - p, hi + p


def _anti(e, v, ops=80):
    try:
        if sp.count_ops(e) > ops:
            return None
        F = sp.integrate(e, v)
        if F.has(*_BAD) or F.has(sp.I) or F.has(sp.zoo) or F.has(sp.nan):
            return None
        return F
    except Exception:
        return None


def _at(F, v, p):
    try:
        val = sp.simplify(F.subs(v, p))
        if not (val.is_number and val.is_finite):
            val = sp.limit(F, v, p)
        if val.is_number and val.is_finite:
            return val
    except Exception:
        pass
    return None


def _same(val, num, tol=1e-5):
    try:
        return abs(float(sp.N(val)) - num) <= tol * (1 + abs(num))
    except Exception:
        return False


def _par(s):
    s = str(s)
    return "(" + s + ")" if (" " in s or s.startswith("-")) else s


def _box(ax, fs=11):
    return ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=fs, zorder=20,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.95))


def _ramp(i, i0, i1):
    return min(1.0, max(0.0, (i - i0) / float(max(1, i1 - i0))))


def vary(P, rnd):
    base = {k: v for k, v in P.items() if k != "lang"}
    out = _vary1(P, rnd)
    for _ in range(12):
        if out != base:
            break
        out = _vary1(P, rnd)
    return out
'''

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["area_between"] = {
    "course": "calc2",
    "title": ("İki eğri arasındaki alan", "Area between two curves"),
    "topics": ["area between curves", "area between two curves", "region between curves",
               "applications of integration", "area of a region", "bounded region",
               "top minus bottom", "eğriler arasındaki alan", "iki eğri arasındaki alan",
               "integralin uygulamaları", "bölgenin alanı", "alan hesabı"],
    "code": _H + r'''

def _xroots(x, d, hd, lo, hi):
    out = []
    try:
        if d.is_polynomial(x) and sp.degree(d, x) >= 1:
            for r in sp.Poly(d, x).real_roots():
                rf = float(r)
                if lo - 1e-9 <= rf <= hi + 1e-9:
                    out.append((sp.Float(rf, 6) if r.has(sp.CRootOf) else r, rf))
            res = []
            for r in out:
                if not res or abs(r[1] - res[-1][1]) > 1e-9:
                    res.append(r)
            return res
    except Exception:
        out = []
    xs = np.linspace(lo, hi, 4001)
    ys = hd(xs)
    for k in range(len(xs) - 1):
        y0, y1 = ys[k], ys[k + 1]
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        if y0 == 0:
            r = xs[k]
        elif y0 * y1 < 0 and abs(y0 - y1) < 1e3:
            a, b = xs[k], xs[k + 1]
            for _ in range(60):
                m = (a + b) / 2
                if _at1(hd, a) * _at1(hd, m) <= 0:
                    b = m
                else:
                    a = m
            r = (a + b) / 2
        else:
            continue
        if out and abs(r - out[-1][1]) < 1e-7:
            continue
        ex = sp.Float(r, 6)
        try:
            cand = sp.nsimplify(r, [sp.pi], tolerance=1e-9)
            if len(sp.sstr(cand)) <= 10 and abs(float(cand) - r) < 1e-8:
                ex = cand
        except Exception:
            pass
        out.append((ex, float(r)))
    return out


def _region(P):
    x, f = _parse(P.get("f", "x + 2"), "x", "x + 2")
    _, g = _parse(P.get("g", "x**2"), "x", "x**2")
    if sp.simplify(f - g) == 0:
        g = g - 1
    d = sp.expand(f - g)
    hf, hg, hd = _num(f, x), _num(g, x), _num(d, x)
    given = ("a" in P) and ("b" in P)
    note = False
    if given:
        A, af = _pv(P["a"], 0)
        B, bf = _pv(P["b"], 1)
        if bf < af:
            A, af, B, bf = B, bf, A, af
        if bf - af < 1e-9:
            B, bf = A + 1, af + 1
        roots = _xroots(x, d, hd, af, bf)
    else:
        roots = _xroots(x, d, hd, -10.0, 10.0)
        if len(roots) >= 2:
            (A, af), (B, bf) = roots[0], roots[-1]
        else:
            A, af, B, bf = sp.Integer(-1), -1.0, sp.Integer(1), 1.0
            note = True
    inner = [r for r in roots if af + 1e-9 < r[1] < bf - 1e-9]
    cuts = [(A, af)] + inner + [(B, bf)]
    pieces = []
    for (l, lf), (r, rf) in zip(cuts[:-1], cuts[1:]):
        m = (lf + rf) / 2
        pieces.append((l, lf, r, rf, _at1(hd, m) >= 0, m))
    return x, f, g, d, hf, hg, hd, pieces, roots, given, note


def solve(P):
    x, f, g, d, hf, hg, hd, pieces, roots, given, note = _region(P)
    F = _anti(d, x)
    fs, gs = _pp(f), _pp(g)
    A0, B0 = pieces[0][0], pieces[-1][2]
    steps = [(f"Eğriler: f(x) = {fs},  g(x) = {gs}", f"Curves: f(x) = {fs},  g(x) = {gs}")]
    rs = ", ".join(_pp(r[0]) for r in roots) if roots else "—"
    if given:
        steps.append((f"Sınırlar x = {_pp(A0)} ve x = {_pp(B0)}. f(x) = g(x) ⇔ {_pp(d)} = 0 ⇒ kesişimler: x = {rs}",
                      f"Bounds x = {_pp(A0)} and x = {_pp(B0)}. f(x) = g(x) ⇔ {_pp(d)} = 0 ⇒ crossings: x = {rs}"))
    elif note:
        steps.append(("Eğriler iki noktada kesişmiyor; örnek olarak [-1, 1] aralığı kullanıldı.",
                      "The curves do not cross twice; the interval [-1, 1] is used instead."))
    else:
        steps.append((f"Kesişim: f(x) = g(x) ⇔ {_pp(d)} = 0 ⇒ x = {rs}",
                      f"Intersections: f(x) = g(x) ⇔ {_pp(d)} = 0 ⇒ x = {rs}"))
    total_num = 0.0
    total_ex = sp.Integer(0)
    exact_ok = F is not None
    if F is not None:
        steps.append((f"(f − g) için ters türev: F(x) = {_pp(F)}", f"Antiderivative of f − g: F(x) = {_pp(F)}"))
    for (l, lf, r, rf, ftop, m) in pieces:
        num = abs(_simp(hd, lf, rf))
        total_num += num
        top_tr, top_en = ("f üstte", "f is on top") if ftop else ("g üstte", "g is on top")
        mid = (f"[{_pp(l)}, {_pp(r)}]: x = {_g(m, 3)} test noktası: f = {_g(_at1(hf, m), 4)}, g = {_g(_at1(hg, m), 4)} ⇒ {top_tr}",
               f"[{_pp(l)}, {_pp(r)}]: test x = {_g(m, 3)}: f = {_g(_at1(hf, m), 4)}, g = {_g(_at1(hg, m), 4)} ⇒ {top_en}")
        steps.append(mid)
        integ = (f"{_I(_pp(l), _pp(r))} [{_par(fs)} − {_par(gs)}] dx" if ftop else
                 f"{_I(_pp(l), _pp(r))} [{_par(gs)} − {_par(fs)}] dx")
        val = None
        if F is not None:
            Fl, Fr = _at(F, x, l), _at(F, x, r)
            if Fl is not None and Fr is not None:
                val = sp.simplify((Fr - Fl) if ftop else (Fl - Fr))
                if not _same(val, num, 1e-4):
                    val = None
        if val is not None:
            if ftop:
                ev = f"F({_pp(r)}) − F({_pp(l)}) = {_pp(Fr)} − {_par(_pp(Fl))} = {_ex(val)}"
            else:
                ev = f"−[F({_pp(r)}) − F({_pp(l)})] = −[{_pp(Fr)} − {_par(_pp(Fl))}] = {_ex(val)}"
            steps.append((f"{integ} = {ev}", f"{integ} = {ev}"))
            total_ex += val
        else:
            exact_ok = False
            steps.append((f"{integ} ≈ {_g(num, 6)} (sayısal Simpson)", f"{integ} ≈ {_g(num, 6)} (numerical Simpson)"))
    if exact_ok:
        total_ex = sp.simplify(total_ex)
        res = _exa(total_ex)
    else:
        res = _g(total_num, 6)
    if len(pieces) > 1:
        steps.append((f"Parçaları topla: A = {res}", f"Add the pieces: A = {res}"))
    steps.append((f"Sonuç: A = {_I(_pp(A0), _pp(B0))} |f(x) − g(x)| dx = {res}",
                  f"Result: A = {_I(_pp(A0), _pp(B0))} |f(x) − g(x)| dx = {res}"))
    return {"answer": f"A = {res}", "steps": steps,
            "fmt": {"fx": fs, "gx": gs, "A": _pp(A0), "B": _pp(B0)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    x, f, g, d, hf, hg, hd, pieces, roots, given, note = _region(P)
    sol = solve(P)
    af, bf = pieces[0][1], pieces[-1][3]
    w = bf - af
    xs = np.linspace(af - 0.3 * w, bf + 0.3 * w, 500)
    yf, yg = hf(xs), hg(xs)
    xr = np.linspace(af, bf, 401)
    rf, rg = hf(xr), hg(xr)
    top, bot = np.fmax(rf, rg), np.fmin(rf, rg)
    cum = _cum(xr, top - bot)
    lo, hi = _ylim([yf, yg, top, bot], pad=0.1)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(lo, hi + (hi - lo) * 0.18)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#9CA3AF", lw=1)
    if xs[0] < 0 < xs[-1]:
        ax.axvline(0, color="#9CA3AF", lw=1)
    from matplotlib.patches import Polygon, Rectangle
    region = Polygon(np.zeros((3, 2)), closed=True, fc=GREEN, alpha=0.25, ec="none", zorder=1)
    ax.add_patch(region)
    K = 24
    dx = w / K
    strips = []
    for k in range(K):
        xm = af + (k + 0.5) * dx
        ym1, ym2 = _at1(hf, xm), _at1(hg, xm)
        if not (np.isfinite(ym1) and np.isfinite(ym2)):
            ym1 = ym2 = 0.0
        rect = Rectangle((af + k * dx, min(ym1, ym2)), dx, abs(ym1 - ym2),
                         fc=(BLUE if ym1 >= ym2 else ORANGE), ec="white", lw=0.6, alpha=0.0, zorder=2)
        ax.add_patch(rect)
        strips.append(rect)
    mover = Rectangle((af, 0), dx, 0, fc=PURPLE, ec=PURPLE, alpha=0.0, zorder=4)
    ax.add_patch(mover)
    cf, = ax.plot([], [], color=BLUE, lw=2.5, zorder=5, label="f(x) = " + sol["fmt"]["fx"])
    cg, = ax.plot([], [], color=ORANGE, lw=2.5, zorder=5, label="g(x) = " + sol["fmt"]["gx"])
    marks = sorted(set([round(af, 9), round(bf, 9)] + [round(r[1], 9) for r in roots if af - 1e-9 <= r[1] <= bf + 1e-9]))
    dots, = ax.plot([], [], "o", color=RED, ms=8, zorder=6)
    vls = [ax.plot([], [], "--", color=RED, lw=1, alpha=0.6)[0] for _ in (0, 1)]
    mlabs = [ax.text(m, lo + (hi - lo) * 0.03, "", color=RED, fontsize=10, ha="center", zorder=6,
                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
             for m in marks]
    hlab = ax.text(0, 0, "", color=PURPLE, fontsize=10, fontweight="bold", zorder=7)
    big = ax.text((af + bf) / 2, hi + (hi - lo) * 0.06, "", fontsize=15, color="#111827", ha="center",
                  zorder=8, bbox=dict(boxstyle="round", fc="#ECFDF5", ec=GREEN))
    info = _box(ax)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(("İki eğri arasındaki alan: A = ∫ (üst − alt) dx" if tr else
                  "Area between curves: A = ∫ (top − bottom) dx"), fontsize=12)
    exact = sol["answer"]
    N = 150

    def update(i):
        p = _ramp(i, 0, 30)
        m = max(2, int(p * len(xs)))
        cf.set_data(xs[:m], yf[:m])
        cg.set_data(xs[:m], yg[:m])
        if i >= 30:
            dots.set_data(marks, [_at1(hf, v) for v in marks])
            for t, mv in zip(mlabs, marks):
                t.set_text(f"x = {_g(mv, 3)}")
            for ln, xv in zip(vls, (af, bf)):
                ln.set_data([xv, xv], [lo, hi])
        else:
            dots.set_data([], [])
            for t in mlabs:
                t.set_text("")
            for ln in vls:
                ln.set_data([], [])
        s = _ramp(i, 45, 115)
        xc = af + w * s
        j = int(round(s * (len(xr) - 1)))
        if i >= 45:
            pts = np.concatenate([np.column_stack([xr[:j + 1], top[:j + 1]]),
                                  np.column_stack([xr[:j + 1][::-1], bot[:j + 1][::-1]])])
            region.set_xy(pts if len(pts) >= 3 else np.zeros((3, 2)))
        else:
            region.set_xy(np.zeros((3, 2)))
        fade = 1.0 - _ramp(i, 118, 135)
        for k, rect in enumerate(strips):
            shown = i >= 45 and af + (k + 1) * dx <= xc + 1e-9
            rect.set_alpha(0.55 * fade if shown else 0.0)
        if 45 <= i < 116:
            jj = min(len(xr) - 1, j)
            mover.set_xy((min(xc, bf - dx), bot[jj]))
            mover.set_height(top[jj] - bot[jj])
            mover.set_alpha(0.75)
            hlab.set_position((min(xc, bf - dx) + dx * 1.3, (top[jj] + bot[jj]) / 2))
            hlab.set_text("üst − alt" if tr else "top − bottom")
        else:
            mover.set_alpha(0.0)
            hlab.set_text("")
        big.set_text(exact if i >= 120 else "")
        if i < 30:
            info.set_text("1) Eğrileri çiz" if tr else "1) Draw both curves")
        elif i < 45:
            info.set_text(("2) Sınırlar / kesişimler: x = " if tr else "2) Bounds / crossings: x = ")
                          + ", ".join(_g(v, 3) for v in marks))
        elif i < 118:
            info.set_text((f"3) Dikey şeritler: Δx·(üst − alt)\n   x = {_g(xc, 3)} için A ≈ {_g(cum[j], 4)}" if tr else
                           f"3) Vertical strips: Δx·(top − bottom)\n   up to x = {_g(xc, 3)}: A ≈ {_g(cum[j], 4)}"))
        else:
            info.set_text(("4) Şeritler incelir → integral\n   " if tr else "4) Strips get thin → integral\n   ") + exact)
        return []

    return N, update


def _vary1(P, rnd):
    if "a" in P and "b" in P:
        if "x**3" in str(P.get("f", "")) or "x**3" in str(P.get("g", "")):
            k = rnd.choice([1, 2, 3])
            return {"f": "x**3", "g": f"{k * k}*x" if k > 1 else "x", "a": -k, "b": k}
        xx = sp.Symbol("x")
        while True:
            r1, r2 = -rnd.choice([1, 2, 3]), rnd.choice([2, 3, 4])
            s, c0 = rnd.choice([-1, -2]), rnd.choice([3, 4, 5, 6])
            beta = s - r1 - r2
            if c0 - beta * beta / 4 > 0.5:
                break
        g = sp.expand(xx ** 2 + beta * xx + c0)
        f = sp.expand(g - (xx - r1) * (xx - r2))
        return {"f": str(f), "g": str(g), "a": 0, "b": r2}
    while True:
        r1, r2 = rnd.randint(-3, 1), rnd.randint(1, 4)
        if r2 - r1 >= 2:
            break
    c0 = rnd.randint(-2, 2)
    g = sp.sympify(f"x**2 + ({c0})")
    if rnd.random() < 0.5:
        f = sp.expand(g - sp.sympify(f"(x - ({r1}))*(x - ({r2}))"))
    else:
        f = sp.expand(g - 2 * sp.sympify(f"(x - ({r1}))*(x - ({r2}))"))
    return {"f": str(f), "g": str(g)}
''',
}
EXAMPLES += [
    {"id": "calc2-area-1", "kind": "area_between",
     "title": ("Doğru ile parabol arasındaki alan", "Area between a line and a parabola"),
     "q": ("y = {fx} doğrusu ile y = {gx} parabolü arasında kalan sınırlı bölgenin alanını bul.",
           "Find the area of the region enclosed by the line y = {fx} and the parabola y = {gx}."),
     "P": {"f": "x + 2", "g": "x**2"}},
    {"id": "calc2-area-2", "kind": "area_between",
     "title": ("Yer değiştiren eğriler", "Curves that switch places"),
     "q": ("y = {fx} ve y = {gx} eğrileri arasında, x = {A} ile x = {B} arasında kalan toplam alanı bul. "
           "(Hangi eğrinin üstte olduğu aralık içinde değişir.)",
           "Find the total area between y = {fx} and y = {gx} from x = {A} to x = {B}. "
           "(Which curve is on top changes inside the interval.)"),
     "P": {"f": "x**3", "g": "x", "a": -1, "b": 1}},
    {"id": "calc2-area-3", "kind": "area_between",
     "topics": ["word problem", "profit", "sözel problem", "kâr", "net change"],
     "title": ("Sözel problem: gelir ve gider hızı", "Word problem: revenue and cost rates"),
     "q": ("Bir atölyenin gelir hızı R'(x) = {fx}, gider hızı C'(x) = {gx} (bin TL/ay, x = ay). "
           "x = {A} ile x = {B} arasında elde edilen toplam kâr, iki eğri arasındaki alandır. Bu kârı bul.",
           "A workshop's revenue rate is R'(x) = {fx} and its cost rate is C'(x) = {gx} (thousand $ per month, "
           "x = months). The total profit from x = {A} to x = {B} is the area between the curves. Find it."),
     "P": {"f": "10 - x", "g": "x**2 - 2*x + 4", "a": 0, "b": 3}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["volume_revolution"] = {
    "course": "calc2",
    "title": ("Dönel cismin hacmi (disk, pul, kabuk)", "Volume of revolution (disk, washer, shell)"),
    "topics": ["volume of revolution", "solids of revolution", "disk method", "washer method",
               "shell method", "cylindrical shells", "volumes of solids", "rotating a region",
               "dönel cisim", "dönel cismin hacmi", "disk yöntemi", "pul yöntemi", "kabuk yöntemi",
               "silindirik kabuk", "hacim hesabı"],
    "code": _H + r'''
from matplotlib.patches import Polygon, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def _setup(P):
    meth = str(P.get("method", "disk")).lower()
    if meth not in ("disk", "washer", "shell"):
        meth = "disk"
    x, f = _parse(P.get("f", "sqrt(x)"), "x", "sqrt(x)")
    _, g = _parse(P.get("g", "0"), "x", "0")
    if meth == "disk":
        g = sp.Integer(0)
    A, af = _pv(P.get("a", 0), 0)
    B, bf = _pv(P.get("b", 1), 1)
    if bf < af:
        A, af, B, bf = B, bf, A, af
    if bf - af < 1e-9:
        B, bf = A + 1, af + 1
    if meth == "shell" and af < 0:
        A, af = sp.Integer(0), 0.0
    hf, hg = _num(f, x), _num(g, x)
    m = (af + bf) / 2
    if meth == "washer":
        if abs(_at1(hf, m)) >= abs(_at1(hg, m)):
            R, r = f, g
        else:
            R, r = g, f
        integrand = sp.expand(R ** 2 - r ** 2)
    elif meth == "disk":
        R, r = f, sp.Integer(0)
        integrand = sp.expand(f ** 2)
    else:
        R, r = (f, g) if _at1(hf, m) >= _at1(hg, m) else (g, f)
        integrand = sp.expand(x * (R - r))
    return {"m": meth, "x": x, "f": f, "g": g, "A": A, "B": B, "a": af, "b": bf, "hf": hf, "hg": hg,
            "R": R, "r": r, "hR": _num(R, x), "hr": _num(r, x), "ig": integrand,
            "hi": _num(integrand, x), "c": 2 if meth == "shell" else 1}


def solve(P):
    S = _setup(P)
    x, A, B, ig, c = S["x"], S["A"], S["B"], S["ig"], S["c"]
    Rs, rs = _pp(S["R"]), _pp(S["r"])
    I = _I(_pp(A), _pp(B))
    if S["m"] == "disk":
        steps = [(f"Disk yöntemi (x ekseni etrafında): V = π{I} [R(x)]² dx,  R(x) = {Rs}",
                  f"Disk method (about the x-axis): V = π{I} [R(x)]² dx,  R(x) = {Rs}"),
                 (f"[R(x)]² = {_pp(ig)}", f"[R(x)]² = {_pp(ig)}")]
        pre = "π"
    elif S["m"] == "washer":
        steps = [(f"Pul yöntemi (x ekseni etrafında): V = π{I} (R² − r²) dx", f"Washer method (about the x-axis): V = π{I} (R² − r²) dx"),
                 (f"Dış yarıçap R(x) = {Rs}, iç yarıçap r(x) = {rs}", f"Outer radius R(x) = {Rs}, inner radius r(x) = {rs}"),
                 (f"R² − r² = {_pp(ig)}", f"R² − r² = {_pp(ig)}")]
        pre = "π"
    else:
        steps = [(f"Kabuk yöntemi (y ekseni etrafında): V = 2π{I} (yarıçap)·(yükseklik) dx",
                  f"Shell method (about the y-axis): V = 2π{I} (radius)·(height) dx"),
                 (f"Yarıçap = x, yükseklik h(x) = {_pp(sp.expand(S['R'] - S['r']))}",
                  f"Radius = x, height h(x) = {_pp(sp.expand(S['R'] - S['r']))}"),
                 (f"x·h(x) = {_pp(ig)}", f"x·h(x) = {_pp(ig)}")]
        pre = "2π"
    num = _simp(S["hi"], S["a"], S["b"], 4000)
    F = _anti(ig, x)
    val = None
    if F is not None:
        Fa, Fb = _at(F, x, A), _at(F, x, B)
        if Fa is not None and Fb is not None:
            val = sp.simplify(Fb - Fa)
            if not _same(val, num, 1e-4):
                val = None
    if val is not None:
        V = sp.simplify(c * sp.pi * val)
        steps.append((f"Ters türev: F(x) = {_pp(F)}", f"Antiderivative: F(x) = {_pp(F)}"))
        vs = _pp(val)
        vs = vs if vs.isdigit() else "(" + vs + ")"
        steps.append((f"V = {pre}[F({_pp(B)}) − F({_pp(A)})] = {pre}·({_pp(Fb)} − {_par(_pp(Fa))}) = {pre}·{vs}",
                      f"V = {pre}[F({_pp(B)}) − F({_pp(A)})] = {pre}·({_pp(Fb)} − {_par(_pp(Fa))}) = {pre}·{vs}"))
        res = _ex(V)
    else:
        steps.append((f"İntegral sayısal olarak: {I} ... dx ≈ {_g(num, 6)}", f"Numerically: {I} ... dx ≈ {_g(num, 6)}"))
        res = _g(c * math.pi * num, 6)
    steps.append((f"Hacim: V = {res}", f"Volume: V = {res}"))
    return {"answer": f"V = {res}", "steps": steps,
            "fmt": {"fx": _pp(S["f"]), "gx": _pp(S["g"]), "A": _pp(A), "B": _pp(B)}}


def _rot(px, py, th, shell):
    if shell:
        return px * np.cos(th), px * np.sin(th), py
    return px, py * np.cos(th), py * np.sin(th)


def _piece(xc, dx, top, bot, shell, t0, t1, nseg=24):
    th = np.linspace(t0, t1, nseg + 1)
    cs, sn = np.cos(th), np.sin(th)
    polys = []
    if not shell:
        R, r = max(abs(top), abs(bot)), min(abs(top), abs(bot))
        x0, x1 = xc - dx / 2, xc + dx / 2
        for j in range(nseg):
            polys.append([(x0, R * cs[j], R * sn[j]), (x1, R * cs[j], R * sn[j]),
                          (x1, R * cs[j + 1], R * sn[j + 1]), (x0, R * cs[j + 1], R * sn[j + 1])])
            polys.append([(x1, R * cs[j], R * sn[j]), (x1, R * cs[j + 1], R * sn[j + 1]),
                          (x1, r * cs[j + 1], r * sn[j + 1]), (x1, r * cs[j], r * sn[j])])
            if r > 1e-9:
                polys.append([(x0, r * cs[j], r * sn[j]), (x1, r * cs[j], r * sn[j]),
                              (x1, r * cs[j + 1], r * sn[j + 1]), (x0, r * cs[j + 1], r * sn[j + 1])])
        for k in (0, nseg):
            polys.append([(x0, r * cs[k], r * sn[k]), (x1, r * cs[k], r * sn[k]),
                          (x1, R * cs[k], R * sn[k]), (x0, R * cs[k], R * sn[k])])
    else:
        ri, ro = max(0.0, xc - dx / 2), xc + dx / 2
        zb, zt = min(top, bot), max(top, bot)
        for j in range(nseg):
            for rad in (ro, ri):
                if rad > 1e-9:
                    polys.append([(rad * cs[j], rad * sn[j], zb), (rad * cs[j + 1], rad * sn[j + 1], zb),
                                  (rad * cs[j + 1], rad * sn[j + 1], zt), (rad * cs[j], rad * sn[j], zt)])
            polys.append([(ro * cs[j], ro * sn[j], zt), (ro * cs[j + 1], ro * sn[j + 1], zt),
                          (ri * cs[j + 1], ri * sn[j + 1], zt), (ri * cs[j], ri * sn[j], zt)])
        for k in (0, nseg):
            polys.append([(ri * cs[k], ri * sn[k], zb), (ro * cs[k], ro * sn[k], zb),
                          (ro * cs[k], ro * sn[k], zt), (ri * cs[k], ri * sn[k], zt)])
    return polys


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _setup(P)
    sol = solve(P)
    shell = S["m"] == "shell"
    a, b = S["a"], S["b"]
    w = b - a
    xs = np.linspace(a, b, 160)
    yT, yB = S["hR"](xs), S["hr"](xs)
    yT = np.where(np.isfinite(yT), yT, 0.0)
    yB = np.where(np.isfinite(yB), yB, 0.0)
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.3], left=0.07, right=0.99, top=0.88, bottom=0.1, wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    ax3 = fig.add_subplot(gs[0, 1], projection="3d")
    xlo, xhi = (min(0.0, a) - 0.15 * w, b + 0.15 * w)
    if not shell:
        xlo = a - 0.15 * w
    ylo, yhi = _ylim([yT, yB], pad=0.15)
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ylo, yhi + (yhi - ylo) * 0.35)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#9CA3AF", lw=1)
    ax.axvline(0, color="#9CA3AF", lw=1)
    if shell:
        ax.axvline(0, color=PURPLE, lw=2.2, ls="--")
    else:
        ax.axhline(0, color=PURPLE, lw=2.2, ls="--")
    reg2 = Polygon(np.column_stack([np.concatenate([xs, xs[::-1]]), np.concatenate([yT, yB[::-1]])]),
                   closed=True, fc=GREEN, alpha=0.0, ec="none")
    ax.add_patch(reg2)
    lf, = ax.plot(xs, yT, color=BLUE, lw=2.3)
    lg, = ax.plot(xs, yB, color=ORANGE, lw=2.0 if S["m"] != "disk" else 0.0)
    K = 10
    dx = w / K
    xcs = a + (np.arange(K) + 0.5) * dx
    tops, bots = S["hR"](xcs), S["hr"](xcs)
    tops = np.where(np.isfinite(tops), tops, 0.0)
    bots = np.where(np.isfinite(bots), bots, 0.0)
    if shell:
        vols = 2 * np.pi * xcs * np.abs(tops - bots) * dx
    else:
        vols = np.pi * np.abs(np.maximum(np.abs(tops), np.abs(bots)) ** 2 -
                              np.minimum(np.abs(tops), np.abs(bots)) ** 2) * dx
    csum = np.cumsum(vols)
    strip = Rectangle((a, 0), dx, 0, fc=PURPLE, alpha=0.0, ec=PURPLE)
    ax.add_patch(strip)
    info = _box(ax, 10)
    ax.set_title(("Bölge (mor: dönme ekseni)" if tr else "Region (purple: axis of rotation)"), fontsize=11)

    # 3D panel
    if shell:
        rmax = max(abs(b), abs(a), 1e-3)
        z0, z1 = min(0.0, float(np.min(yB)), float(np.min(yT))), max(float(np.max(yT)), float(np.max(yB)), 1e-3)
        ax3.set_xlim(-rmax, rmax)
        ax3.set_ylim(-rmax, rmax)
        ax3.set_zlim(z0, z1)
        ax3.set_box_aspect((1, 1, min(1.4, max(0.5, (z1 - z0) / (2 * rmax)))))
        ax3.plot([0, 0], [0, 0], [z0, z1 + 0.1 * (z1 - z0)], "--", color=PURPLE, lw=2)
    else:
        rmax = max(float(np.max(np.abs(yT))), float(np.max(np.abs(yB))), 1e-3)
        ax3.set_xlim(a, b)
        ax3.set_ylim(-rmax, rmax)
        ax3.set_zlim(-rmax, rmax)
        ax3.set_box_aspect((min(2.2, max(1.0, w / (2 * rmax))), 1, 1))
        ax3.plot([a - 0.1 * w, b + 0.1 * w], [0, 0], [0, 0], "--", color=PURPLE, lw=2)
    for axis in (ax3.xaxis, ax3.yaxis, ax3.zaxis):
        axis.set_pane_color((1, 1, 1, 0))
    ax3.tick_params(labelsize=7)
    ax3.set_xlabel("x", fontsize=9)
    ax3.set_ylabel("y" if shell else "", fontsize=9)
    ax3.set_zlabel("y" if shell else "", fontsize=9)
    rpoly = np.column_stack([np.concatenate([xs, xs[::-1]]), np.concatenate([yT, yB[::-1]])])
    flat = Poly3DCollection([list(zip(*_rot(rpoly[:, 0], rpoly[:, 1], 0.0, shell)))],
                            facecolors=GREEN, edgecolors=GREEN, alpha=0.55)
    ax3.add_collection3d(flat)
    xs_s = np.linspace(a, b, 26)
    cT, cB = S["hR"](xs_s), S["hr"](xs_s)
    cT = np.where(np.isfinite(cT), cT, 0.0)
    cB = np.where(np.isfinite(cB), cB, 0.0)
    curves = [cT] if (S["m"] == "disk" or float(np.max(np.abs(cB))) < 1e-12) else [cT, cB]
    AZ, EL = -58.0, 20.0
    ce, ca = math.cos(math.radians(EL)), math.radians(AZ)
    if shell:
        gc = math.atan2(ce * math.sin(ca), ce * math.cos(ca))
    else:
        gc = math.atan2(math.sin(math.radians(EL)), ce * math.sin(ca))
    t0, t1 = gc + 0.25 * np.pi, gc + 1.75 * np.pi

    def _surfs(thmax, alpha, th0=0.0):
        out = []
        TH, XX = np.meshgrid(np.linspace(th0, thmax, 25), xs_s)
        for cv in curves:
            YY = np.repeat(cv[:, None], TH.shape[1], axis=1)
            X, Y, Z = _rot(XX, YY, TH, shell)
            out.append(ax3.plot_surface(X, Y, Z, color=BLUE if cv is cT else ORANGE, alpha=alpha,
                                        linewidth=0, antialiased=False, shade=True))
        return out

    full = _surfs(t1, 0.12, t0)
    for s_ in full:
        s_.set_visible(False)
    pieces = []
    for k in range(K):
        pc = Poly3DCollection(_piece(xcs[k], dx * 0.92, tops[k], bots[k], shell, t0, t1),
                              facecolors=(BLUE if k % 2 == 0 else "#60A5FA"), edgecolors="#1E3A8A",
                              linewidths=0.15, alpha=0.85)
        pc.set_visible(False)
        ax3.add_collection3d(pc)
        pieces.append(pc)
    title3 = ax3.set_title("", fontsize=11)
    state = {"surf": []}
    names = {"disk": ("disk", "disks"), "washer": ("pul", "washers"), "shell": ("kabuk", "shells")}[S["m"]]
    N = 160

    def update(i):
        for s_ in state["surf"]:
            s_.remove()
        state["surf"] = []
        ax3.view_init(elev=EL, azim=AZ + 12 * math.sin(2 * math.pi * i / N))
        reg2.set_alpha(0.35 * _ramp(i, 0, 15))
        th = 2 * np.pi * _ramp(i, 20, 65)
        if 20 <= i < 66:
            state["surf"] = _surfs(max(th, 0.05), 0.35)
            X, Y, Z = _rot(rpoly[:, 0], rpoly[:, 1], th, shell)
            flat.set_verts([list(zip(X, Y, Z))])
            flat.set_alpha(0.55)
            flat.set_visible(True)
        elif i < 20:
            X, Y, Z = _rot(rpoly[:, 0], rpoly[:, 1], 0.0, shell)
            flat.set_verts([list(zip(X, Y, Z))])
            flat.set_alpha(0.55 * _ramp(i, 0, 15))
            flat.set_visible(True)
        else:
            flat.set_visible(False)
        for s_ in full:
            s_.set_visible(i >= 66)
        kshow = 0 if i < 70 else min(K, 1 + int((i - 70) / 5))
        for k, pc in enumerate(pieces):
            pc.set_visible(k < kshow)
        if 70 <= i < 125 and kshow > 0:
            k = kshow - 1
            strip.set_xy((xcs[k] - dx / 2, min(tops[k], bots[k])))
            strip.set_height(abs(tops[k] - bots[k]))
            strip.set_width(dx)
            strip.set_alpha(0.6)
        else:
            strip.set_alpha(0.0)
        if i < 20:
            info.set_text("1) Döndürülecek bölge" if tr else "1) The region to rotate")
            title3.set_text("")
        elif i < 66:
            info.set_text((f"2) Bölge eksen etrafında\n   dönüyor: {int(round(np.degrees(th)))}°" if tr else
                           f"2) Rotating about the axis:\n   {int(round(np.degrees(th)))}°"))
            title3.set_text("")
        elif i < 125:
            info.set_text((f"3) {max(kshow, 0)} {names[0]}: ΣΔV ≈ {_g(csum[max(kshow, 1) - 1], 4)}" if tr else
                           f"3) {max(kshow, 0)} {names[1]}: ΣΔV ≈ {_g(csum[max(kshow, 1) - 1], 4)}"))
            title3.set_text((f"{K} {names[0]} ile yaklaşım" if tr else f"Approximation with {K} {names[1]}"))
        else:
            info.set_text((f"4) Δx → 0: ΣΔV → integral\n   {sol['answer']}" if tr else
                           f"4) Δx → 0: ΣΔV → integral\n   {sol['answer']}"))
            title3.set_text(sol["answer"])
        return []

    return N, update


def _vary1(P, rnd):
    m = str(P.get("method", "disk")).lower()
    if m == "washer":
        k = rnd.choice([1, 2, 3])
        if rnd.random() < 0.5:
            return {"f": f"{k}*x" if k > 1 else "x", "g": f"x**2/{k}" if k > 1 else "x**2", "a": 0, "b": k, "method": "washer"}
        return {"f": f"{k}*sqrt(x)" if k > 1 else "sqrt(x)", "g": f"{k}*x" if k > 1 else "x", "a": 0, "b": 1, "method": "washer"}
    if m == "shell":
        c = rnd.choice([2, 3, 4])
        out = {"f": f"{c}*x - x**2", "a": 0, "b": c, "method": "shell"}
        if "g" in P:
            out["g"] = "0"
        return out
    form = rnd.choice(["sqrt", "line", "sqrt"])
    if form == "sqrt":
        return {"f": "sqrt(x)", "a": 0, "b": rnd.choice([1, 2, 3, 5, 6]), "method": "disk"}
    k = rnd.choice([1, 2])
    return {"f": f"x/{k}" if k > 1 else "x", "a": 0, "b": rnd.choice([2, 3, 4]), "method": "disk"}
''',
}
EXAMPLES += [
    {"id": "calc2-vol-1", "kind": "volume_revolution",
     "topics": ["word problem", "paraboloid", "sözel problem"],
     "title": ("Disk yöntemi: far reflektörü", "Disk method: a headlight reflector"),
     "q": ("Bir far reflektörü, y = {fx} eğrisinin x = {A} ile x = {B} arasındaki parçasının x ekseni etrafında "
           "döndürülmesiyle oluşuyor (birimler cm). Reflektörün iç hacmini disk yöntemiyle bul.",
           "A headlight reflector is formed by rotating y = {fx}, from x = {A} to x = {B}, about the x-axis "
           "(units in cm). Use the disk method to find the volume inside it."),
     "P": {"f": "sqrt(x)", "a": 0, "b": 4, "method": "disk"}},
    {"id": "calc2-vol-2", "kind": "volume_revolution",
     "title": ("Pul (washer) yöntemi", "Washer method"),
     "q": ("y = {fx} ve y = {gx} eğrileri arasındaki bölge (x = {A} ile x = {B} arası) x ekseni etrafında "
           "döndürülüyor. Oluşan cismin hacmini pul yöntemiyle bul.",
           "The region between y = {fx} and y = {gx} (from x = {A} to x = {B}) is rotated about the x-axis. "
           "Use the washer method to find the volume of the solid."),
     "P": {"f": "x", "g": "x**2", "a": 0, "b": 1, "method": "washer"}},
    {"id": "calc2-vol-3", "kind": "volume_revolution",
     "title": ("Silindirik kabuk yöntemi", "Cylindrical shell method"),
     "q": ("y = {fx} eğrisi ile x ekseni arasındaki bölge (x = {A} ile x = {B} arası) y ekseni etrafında "
           "döndürülüyor. Hacmi kabuk yöntemiyle bul.",
           "The region between y = {fx} and the x-axis (from x = {A} to x = {B}) is rotated about the y-axis. "
           "Find the volume with the shell method."),
     "P": {"f": "2*x - x**2", "a": 0, "b": 2, "method": "shell"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["taylor_series"] = {
    "course": "calc2",
    "title": ("Taylor polinomları", "Taylor polynomials"),
    "topics": ["taylor series", "taylor polynomial", "maclaurin series", "maclaurin polynomial",
               "power series", "approximating functions", "taylor's remainder", "lagrange error",
               "taylor serisi", "taylor polinomu", "maclaurin serisi", "kuvvet serisi",
               "seri açılımı", "kalan terim"],
    "code": _H + r'''

def _dn(k):
    return "f" + ("'" * k if k <= 3 else "⁽" + _sup(k) + "⁾")


def _setup(P):
    x, f = _parse(P.get("f", "sin(x)"), "x", "sin(x)")
    try:
        n = int(P.get("nmax", 9))
    except Exception:
        n = 9
    n = max(1, min(14, n))
    A0, a0 = _pv(P.get("a", 0), 0)
    for A in (A0, sp.Integer(1), sp.Integer(0), sp.Integer(2)):
        ders, d, ok = [], f, True
        for k in range(n + 2):
            try:
                v = sp.simplify(d.subs(x, A))
                ok = ok and bool(v.is_number and v.is_finite) if k <= n else ok
            except Exception:
                v, ok = sp.nan, False
            ders.append(v)
            if k <= n:
                d = sp.diff(d, x)
        if ok:
            break
    else:
        f = sp.sin(x)
        A = sp.Integer(0)
        ders = [sp.sin(A + k * sp.pi / 2) for k in range(n + 2)]
        d = sp.diff(f, x, n + 1)
    af = float(A)
    E, ef = _pv(P.get("xe", af + 1), af + 1)
    coef = [sp.nsimplify(ders[k]) / sp.factorial(k) for k in range(n + 1)]
    return {"x": x, "f": f, "A": A, "a": af, "n": n, "ders": ders, "coef": coef, "dn1": d,
            "E": E, "e": ef, "h": _num(f, x), "cf": [float(c) for c in coef]}


def _poly_str(coef, A, upto):
    if A == 0:
        base = "x"
    else:
        base = "(x - " + _pp(A) + ")" if float(A) > 0 else "(x + " + _pp(-A) + ")"
    parts = []
    for k in range(upto + 1):
        c = coef[k]
        if c == 0:
            continue
        neg = bool(c < 0)
        mag = -c if neg else c
        pw = "" if k == 0 else (base if k == 1 else base + _sup(k))
        if k == 0:
            body = _pp(mag)
        elif mag == 1:
            body = pw
        elif mag.is_Rational:
            p, q = int(mag.p), int(mag.q)
            body = (pw if p == 1 else f"{p}{pw}") + ("" if q == 1 else f"/{q}")
        else:
            body = _pp(mag) + "·" + pw
        parts.append((neg, body))
    if not parts:
        return "0"
    out = ("-" if parts[0][0] else "") + parts[0][1]
    for neg, body in parts[1:]:
        out += (" - " if neg else " + ") + body
    return out


def _tn(S, k, xs):
    xs = np.asarray(xs, dtype=float)
    out = np.zeros_like(xs)
    t = xs - S["a"]
    for j in range(k + 1):
        out = out + S["cf"][j] * t ** j
    return out


def solve(P):
    S = _setup(P)
    n, A, coef = S["n"], S["A"], S["coef"]
    fs, As = _pp(S["f"]), _pp(A)
    steps = [(f"f(x) = {fs}, merkez a = {As}.  Tₙ(x) = Σ {_dn(0)}⁽ᵏ⁾(a)/k! · (x − a)ᵏ",
              f"f(x) = {fs}, center a = {As}.  Tₙ(x) = Σ {_dn(0)}⁽ᵏ⁾(a)/k! · (x − a)ᵏ")]
    dl = ", ".join(f"{_dn(k)}({As}) = {_pp(S['ders'][k])}" for k in range(min(n, 6) + 1))
    steps.append((f"Türevler: {dl}" + (", …" if n > 6 else ""), f"Derivatives: {dl}" + (", …" if n > 6 else "")))
    nz = [k for k in range(n + 1) if coef[k] != 0]
    cl = ", ".join(f"c{_sub(k)} = {_pp(coef[k])}" for k in nz[:7])
    rest = len(nz) < n + 1
    steps.append((f"Katsayılar cₖ = f⁽ᵏ⁾(a)/k!: {cl}" + (", …" if len(nz) > 7 else "") + (" (diğerleri 0)" if rest else ""),
                   f"Coefficients cₖ = f⁽ᵏ⁾(a)/k!: {cl}" + (", …" if len(nz) > 7 else "") + (" (others are 0)" if rest else "")))
    poly = _poly_str(coef, A, n)
    steps.append((f"T{_sub(n)}(x) = {poly}", f"T{_sub(n)}(x) = {poly}"))
    e = S["e"]
    tv = float(_tn(S, n, [e])[0])
    fv = _at1(S["h"], e)
    err = abs(fv - tv)
    Es = _pp(S["E"])
    steps.append((f"x = {Es} noktasında: T{_sub(n)}({Es}) ≈ {tv:.6f},  f({Es}) ≈ {fv:.6f}",
                  f"At x = {Es}: T{_sub(n)}({Es}) ≈ {tv:.6f},  f({Es}) ≈ {fv:.6f}"))
    steps.append((f"Gerçek hata: |f({Es}) − T{_sub(n)}({Es})| ≈ {err:.3g}",
                  f"Actual error: |f({Es}) − T{_sub(n)}({Es})| ≈ {err:.3g}"))
    lo, hi = min(S["a"], e), max(S["a"], e)
    dvals = np.abs(_num(S["dn1"], S["x"])(np.linspace(lo, hi, 400)))
    dvals = dvals[np.isfinite(dvals)]
    if len(dvals):
        M = float(np.max(dvals))
        bound = M * abs(e - S["a"]) ** (n + 1) / math.factorial(n + 1)
        steps.append((f"Lagrange kalan sınırı: |R{_sub(n)}| ≤ M·|{Es} − {As}|{_sup(n + 1)}/{n + 1}! ≈ {bound:.3g}"
                      f"  (M = max|{_dn(n + 1)}| ≈ {M:.4g})",
                      f"Lagrange remainder bound: |R{_sub(n)}| ≤ M·|{Es} − {As}|{_sup(n + 1)}/{n + 1}! ≈ {bound:.3g}"
                      f"  (M = max|{_dn(n + 1)}| ≈ {M:.4g})"))
    tr = P.get("lang", "tr") == "tr"
    return {"answer": (f"T{_sub(n)}(x) = {poly};  " + ("hata" if tr else "error") + f" ≈ {err:.3g} (x = {Es})"),
            "steps": steps, "fmt": {"fx": fs, "A": As, "XE": Es, "poly": poly}}


def _window(S, P):
    if "xmin" in P and "xmax" in P:
        lo, hi = float(_pv(P["xmin"], -3)[1]), float(_pv(P["xmax"], 3)[1])
        if hi > lo:
            return lo, hi
    a = S["a"]
    h = S["h"]
    fa = abs(_at1(h, a))
    lim = 1e3 * (1 + fa)
    span = 6.0
    xs = np.linspace(a - span, a + span, 2401)
    ys = h(xs)
    bad = ~np.isfinite(ys) | (np.abs(ys) > lim)
    mid = 1200
    lo_i, hi_i = mid, mid
    while lo_i > 0 and not bad[lo_i - 1]:
        lo_i -= 1
    while hi_i < len(xs) - 1 and not bad[hi_i + 1]:
        hi_i += 1
    lo, hi = xs[lo_i], xs[hi_i]
    if lo_i > 0:
        lo += 0.02 * (hi - lo)
    if hi_i < len(xs) - 1:
        hi -= 0.02 * (hi - lo)
    if hi - lo < 0.5:
        lo, hi = a - 1, a + 1
    return lo, hi


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _setup(P)
    sol = solve(P)
    n, a, e = S["n"], S["a"], S["e"]
    lo, hi = _window(S, P)
    lo, hi = min(lo, e - 0.05 * (hi - lo)), max(hi, e + 0.05 * (hi - lo))
    xs = np.linspace(lo, hi, 500)
    ys = S["h"](xs)
    y0, y1 = _ylim([ys], pad=0.35, zero=False)
    if y1 - y0 < 1:
        y0, y1 = y0 - 0.5, y1 + 0.5
    gs = fig.add_gridspec(1, 2, width_ratios=[2.15, 1], left=0.07, right=0.99, top=0.9, bottom=0.09, wspace=0.05)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    ax.set_xlim(lo, hi)
    ax.set_ylim(y0, y1)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#9CA3AF", lw=1)
    if lo < 0 < hi:
        ax.axvline(0, color="#9CA3AF", lw=1)
    cf, = ax.plot([], [], color="#111827", lw=3.2, alpha=0.75, label="f(x) = " + sol["fmt"]["fx"])
    degs = [k for k in range(n + 1) if S["coef"][k] != 0] or [0]
    ghosts = [ax.plot(xs, np.clip(_tn(S, k, xs), y0 - 10 * (y1 - y0), y1 + 10 * (y1 - y0)), color=BLUE,
                      lw=1.0, alpha=0.0)[0] for k in degs]
    cur, = ax.plot([], [], color=ORANGE, lw=2.4, label="Tₖ(x)")
    cdot, = ax.plot([a], [_at1(S["h"], a)], "o", color=PURPLE, ms=8, zorder=6)
    ax.text(a, y0 + 0.03 * (y1 - y0), f"a = {_g(a, 3)}", color=PURPLE, fontsize=9, ha="center")
    ev, = ax.plot([], [], ":", color=RED, lw=1.3)
    edots, = ax.plot([], [], "o", color=RED, ms=7, zorder=7)
    info = _box(ax, 10)
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title(("Taylor polinomları f'yi a çevresinde giderek daha iyi yakalar" if tr else
                  "Taylor polynomials hug f near a better and better"), fontsize=11)
    cols = (0.02, 0.17, 0.55)
    for cx, hd in zip(cols, ("k", "f⁽ᵏ⁾(a)", "cₖ = f⁽ᵏ⁾(a)/k!")):
        tx.text(cx, 0.97, hd, fontsize=10, fontweight="bold", va="top", transform=tx.transAxes)
    rows = []
    dy = min(0.06, 0.88 / (n + 1))
    for k in range(n + 1):
        dv = _pp(S["ders"][k])
        cv = _pp(S["coef"][k])
        dv = dv if len(dv) <= 9 else _g(float(S["ders"][k]), 4)
        cv = cv if len(cv) <= 11 else _g(float(S["coef"][k]), 4)
        rows.append([tx.text(cx, 0.9 - k * dy, txt, fontsize=9.5, va="top", transform=tx.transAxes, alpha=0.0)
                     for cx, txt in zip(cols, (str(k), dv, cv))])
    fe = _at1(S["h"], e)
    nst = len(degs)
    i0, i1, N = 15, 128, 150
    L = (i1 - i0) / nst

    def update(i):
        p = _ramp(i, 0, 14)
        m = max(2, int(p * len(xs)))
        cf.set_data(xs[:m], ys[:m])
        if i < i0:
            st, u = -1, 0.0
        else:
            st = min(nst - 1, int((i - i0) / L))
            u = _ramp(i - i0 - st * L, 0, 0.45 * L)
        for j, gl in enumerate(ghosts):
            gl.set_alpha(0.28 if j < st else 0.0)
        if st >= 0:
            k = degs[st]
            prev = _tn(S, degs[st - 1], xs) if st > 0 else np.zeros_like(xs)
            yy = (1 - u) * prev + u * _tn(S, k, xs)
            cur.set_data(xs, np.clip(yy, y0 - 10 * (y1 - y0), y1 + 10 * (y1 - y0)))
            te = (1 - u) * (float(_tn(S, degs[st - 1], [e])[0]) if st > 0 else 0.0) + u * float(_tn(S, k, [e])[0])
            ev.set_data([e, e], [y0, y1])
            edots.set_data([e, e], [fe, min(max(te, y0), y1)])
            kk = n if (i >= i1 and st == nst - 1) else k
            err = abs(fe - float(_tn(S, k, [e])[0]))
            info.set_text((f"T{_sub(kk)}(x): derece {kk}\n|f({_g(e, 3)}) − T{_sub(kk)}({_g(e, 3)})| ≈ {err:.2g}" if tr else
                           f"T{_sub(kk)}(x): degree {kk}\n|f({_g(e, 3)}) − T{_sub(kk)}({_g(e, 3)})| ≈ {err:.2g}"))
            for r_, row in enumerate(rows):
                for t_ in row:
                    t_.set_alpha(1.0 if r_ <= k else 0.0)
                    t_.set_color(RED if (r_ == k and i < i1) else ("#111827" if S["coef"][r_] != 0 else "#9CA3AF"))
        else:
            cur.set_data([], [])
            ev.set_data([], [])
            edots.set_data([], [])
            info.set_text(("1) f(x) ve merkez a" if tr else "1) f(x) and the center a"))
            for row in rows:
                for t_ in row:
                    t_.set_alpha(0.0)
        if i >= i1:
            for row in rows:
                for t_ in row:
                    t_.set_alpha(1.0)
            info.set_text(info.get_text() + ("\nKırmızı noktalar: f ve Tₙ, x = " if tr else "\nRed dots: f and Tₙ at x = ")
                          + _g(e, 3))
        return []

    return N, update


def _vary1(P, rnd):
    fam = [("sin(x)", 0, -7, 7), ("cos(x)", 0, -7, 7), ("log(1 + x)", 0, -0.95, 2.5),
           ("1/(1 - x)", 0, -2.5, 0.95), ("atan(x)", 0, -2.5, 2.5)]
    if "exp" in str(P.get("f", "")):
        fam = [("exp(x)", 0, -3, 3)]
    if float(_pv(P.get("a", 0), 0)[1]) != 0:
        fam = [("log(x)", 1, 0.05, 2.8), ("sqrt(x)", 4, 0.0, 12), ("1/x", 1, 0.2, 2.6), ("exp(x)", 1, -2, 4)]
    f, a, lo, hi = rnd.choice(fam)
    n = rnd.choice([4, 5, 6, 7, 8])
    near = {"log(1 + x)": [0.5, -0.5, 0.3], "1/(1 - x)": [0.5, -0.5], "atan(x)": [0.5, 0.8],
            "log(x)": [1.5, 0.6], "sqrt(x)": [5, 3, 6], "1/x": [1.5, 0.7], "exp(x)": [1, 2, -1, 0.5]}
    xe = rnd.choice(near.get(f, [1, 2, -1, 1.5]))
    out = {"f": f, "a": a, "nmax": n, "xe": xe}
    if "xmin" in P or "xmax" in P or f not in ("sin(x)", "cos(x)", "exp(x)"):
        out["xmin"], out["xmax"] = lo, hi
    return out
''',
}
EXAMPLES += [
    {"id": "calc2-taylor-1", "kind": "taylor_series",
     "title": ("sin x için Maclaurin polinomları", "Maclaurin polynomials of sin x"),
     "q": ("f(x) = {fx} fonksiyonunun a = {A} merkezli {nmax}. derece Taylor polinomunu yaz ve x = {XE} "
           "noktasındaki yaklaşım hatasını bul.",
           "Write the degree-{nmax} Taylor polynomial of f(x) = {fx} about a = {A} and find the "
           "approximation error at x = {XE}."),
     "P": {"f": "sin(x)", "a": 0, "nmax": 9, "xe": 2, "xmin": -7, "xmax": 7}},
    {"id": "calc2-taylor-2", "kind": "taylor_series",
     "topics": ["approximating e", "e sayısı"],
     "title": ("e sayısına yaklaşmak", "Approximating the number e"),
     "q": ("f(x) = {fx} için a = {A} merkezli {nmax}. derece Taylor polinomunu kullanarak f({XE}) değerini "
           "tahmin et (x = 1 için bu değer e sayısıdır). Hata ne kadar?",
           "Use the degree-{nmax} Taylor polynomial of f(x) = {fx} about a = {A} to estimate f({XE}) "
           "(for x = 1 this is the number e). How large is the error?"),
     "P": {"f": "exp(x)", "a": 0, "nmax": 6, "xe": 1, "xmin": -3, "xmax": 3}},
    {"id": "calc2-taylor-3", "kind": "taylor_series",
     "topics": ["radius of convergence", "yakınsaklık yarıçapı"],
     "title": ("ln x için a = 1 merkezli Taylor polinomu", "Taylor polynomial of ln x centered at 1"),
     "q": ("f(x) = {fx} fonksiyonunun a = {A} merkezli {nmax}. derece Taylor polinomunu bul ve f({XE}) "
           "değerini tahmin et. Polinom merkezden uzaklaştıkça neden kötüleşir?",
           "Find the degree-{nmax} Taylor polynomial of f(x) = {fx} about a = {A} and estimate f({XE}). "
           "Why does the polynomial get worse far from the center?"),
     "P": {"f": "log(x)", "a": 1, "nmax": 5, "xe": 1.5, "xmin": 0.05, "xmax": 2.8}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["series_convergence"] = {
    "course": "calc2",
    "title": ("Serilerin yakınsaklığı ve kısmi toplamlar", "Series convergence and partial sums"),
    "topics": ["series", "infinite series", "convergence", "divergence", "partial sums", "geometric series",
               "p-series", "harmonic series", "alternating series", "telescoping series", "ratio test",
               "integral test", "nth term test", "divergence test", "seriler", "sonsuz seri", "yakınsaklık",
               "ıraksaklık", "geometrik seri", "harmonik seri", "alterne seri", "kısmi toplam", "oran testi"],
    "code": _H + r'''

def _fr(v, default):
    try:
        if isinstance(v, str):
            q = Fraction(v.replace(" ", ""))
        else:
            q = Fraction(v).limit_denominator(1000)
        return q
    except Exception:
        return Fraction(default)


def _ff(q):
    q = Fraction(q)
    return str(q.numerator) if q.denominator == 1 else f"{q.numerator}/{q.denominator}"


def _setup(P):
    t = str(P.get("type", "geometric")).lower()
    if t not in ("geometric", "p", "harmonic", "alternating", "telescoping"):
        t = "geometric"
    S = {"t": t}
    if t == "geometric":
        a, r = _fr(P.get("a", 1), 1), _fr(P.get("r", "1/2"), Fraction(1, 2))
        if a == 0:
            a = Fraction(1)
        nt = 16 if abs(r) < 1 else 12
        S.update(a=a, r=r, n0=0, conv=abs(r) < 1,
                 terms=[float(a * r ** n) for n in range(nt)],
                 limit=(a / (1 - r)) if abs(r) < 1 else None)
    elif t in ("p", "harmonic", "alternating"):
        p = Fraction(1) if t == "harmonic" else _fr(P.get("p", 2 if t == "p" else 1), 1)
        nt = 60 if t == "harmonic" else 40
        sg = (lambda n: (-1) ** (n + 1)) if t == "alternating" else (lambda n: 1)
        terms = [sg(n) / float(n) ** float(p) for n in range(1, nt + 1)]
        ps = sp.Rational(p.numerator, p.denominator)
        lim = None
        if t == "alternating" and p > 0:
            lim = sp.log(2) if p == 1 else sp.simplify((1 - sp.Integer(2) ** (1 - ps)) * sp.zeta(ps))
        elif t != "alternating" and p > 1:
            lim = sp.zeta(ps)
        S.update(p=p, n0=1, terms=terms, limit=lim, conv=lim is not None)
    else:
        try:
            k = max(1, min(6, int(P.get("k", 1))))
        except Exception:
            k = 1
        nt = 30
        Hk = sum(Fraction(1, j) for j in range(1, k + 1))
        S.update(k=k, n0=1, terms=[1.0 / (n * (n + k)) for n in range(1, nt + 1)],
                 limit=Hk / k, conv=True)
    S["sums"] = list(np.cumsum(S["terms"]))
    S["n"] = list(range(S["n0"], S["n0"] + len(S["terms"])))
    return S


def _lim_s(S):
    L = S["limit"]
    if L is None:
        return "∞"
    if isinstance(L, Fraction):
        return _ff(L)
    return _ex(L)


def _lim_f(S):
    L = S["limit"]
    return None if L is None else float(L) if isinstance(L, Fraction) else float(sp.N(L))


def solve(P):
    S = _setup(P)
    t = S["t"]
    sums, n_ = S["sums"], S["n"]
    N = n_[-1]
    Ns = _sub(N)
    tr = P.get("lang", "tr") == "tr"
    if t == "geometric":
        a, r = S["a"], S["r"]
        ser = f"Σ {_ff(a)}·({_ff(r)})ⁿ" if r != 1 else f"Σ {_ff(a)}"
        first = " + ".join(_ff(a * r ** k) for k in range(3)) + " + …"
        steps = [(f"{ser} (n = 0'dan ∞'a) = {first}: geometrik seri, a = {_ff(a)}, r = {_ff(r)}",
                  f"{ser} (n from 0 to ∞) = {first}: geometric series, a = {_ff(a)}, r = {_ff(r)}"),
                 (f"Oran testi: |aₙ₊₁ / aₙ| = |r| = {_ff(abs(r))}", f"Ratio test: |aₙ₊₁ / aₙ| = |r| = {_ff(abs(r))}")]
        if S["conv"]:
            steps.append(("|r| < 1 ⇒ seri (mutlak) yakınsar", "|r| < 1 ⇒ the series converges (absolutely)"))
            steps.append((f"Kısmi toplam Sₙ = a(1 − rⁿ⁺¹)/(1 − r);  S{Ns} ≈ {sums[-1]:.9g}",
                          f"Partial sum Sₙ = a(1 − rⁿ⁺¹)/(1 − r);  S{Ns} ≈ {sums[-1]:.9g}"))
            steps.append((f"Toplam: S = a/(1 − r) = {_ff(a)}/(1 − {_par(_ff(r))}) = {_ff(S['limit'])}",
                          f"Sum: S = a/(1 − r) = {_ff(a)}/(1 − {_par(_ff(r))}) = {_ff(S['limit'])}"))
        else:
            steps.append((f"|r| ≥ 1 ⇒ n. terim testi: aₙ = {_ff(a)}·({_ff(r)})ⁿ ↛ 0 ⇒ seri ıraksar",
                          f"|r| ≥ 1 ⇒ nth-term test: aₙ = {_ff(a)}·({_ff(r)})ⁿ ↛ 0 ⇒ the series diverges"))
    elif t in ("p", "harmonic"):
        p = S["p"]
        ps = _ff(p)
        if t == "harmonic":
            steps = [("Σ 1/n = 1 + 1/2 + 1/3 + …: harmonik seri (p = 1)", "Σ 1/n = 1 + 1/2 + 1/3 + …: the harmonic series (p = 1)"),
                     ("n. terim testi: 1/n → 0, ama bu test sonuç vermez", "nth-term test: 1/n → 0, but that test is inconclusive")]
        else:
            steps = [(f"Σ 1/n{_sup(ps)} (n = 1'den ∞'a): p-serisi, p = {ps}", f"Σ 1/n{_sup(ps)} (n from 1 to ∞): a p-series with p = {ps}"),
                     ("p-testi: Σ 1/nᵖ yakınsar ⇔ p > 1 (integral testinden: ∫₁^∞ x⁻ᵖ dx sonlu ⇔ p > 1)",
                      "p-test: Σ 1/nᵖ converges ⇔ p > 1 (from the integral test: ∫₁^∞ x⁻ᵖ dx is finite ⇔ p > 1)")]
        if S["conv"]:
            pf = float(p)
            rem = f"{N}{_sup(_ff(1 - p))}/{_par(_ff(p - 1))} ≈ {N ** (1 - pf) / (pf - 1):.3g}"
            steps.append((f"p = {ps} > 1 ⇒ yakınsak", f"p = {ps} > 1 ⇒ converges"))
            steps.append((f"Kalan tahmini: S − S{Ns} ≤ ∫{_sub(N)}^∞ x⁻ᵖ dx = N¹⁻ᵖ/(p − 1) = {rem}",
                          f"Remainder: S − S{Ns} ≤ ∫{_sub(N)}^∞ x⁻ᵖ dx = N¹⁻ᵖ/(p − 1) = {rem}"))
            steps.append((f"S{Ns} ≈ {sums[-1]:.6g};  toplam S = ζ({ps}) = {_lim_s(S)}",
                          f"S{Ns} ≈ {sums[-1]:.6g};  the sum is S = ζ({ps}) = {_lim_s(S)}"))
        else:
            if p <= 0:
                steps.append((f"p = {ps} ≤ 0: n. terim testi, 1/nᵖ ↛ 0 ⇒ ıraksak", f"p = {ps} ≤ 0: nth-term test, 1/nᵖ ↛ 0 ⇒ diverges"))
            else:
                steps.append((f"p = {ps} ≤ 1 ⇒ ıraksak; ∫₁^∞ x⁻ᵖ dx = ∞ (integral testi)",
                              f"p = {ps} ≤ 1 ⇒ diverges; ∫₁^∞ x⁻ᵖ dx = ∞ (integral test)"))
            extra = (f" (≈ ln {N} + γ ≈ {math.log(N) + 0.5772:.4g})" if p == 1 else "")
            steps.append((f"Kısmi toplamlar sınırsız büyür: S{Ns} ≈ {sums[-1]:.5g}{extra}",
                          f"Partial sums grow without bound: S{Ns} ≈ {sums[-1]:.5g}{extra}"))
    elif t == "alternating":
        p = S["p"]
        ps = _ff(p)
        e = _sup(ps) if p != 1 else ""
        steps = [(f"Σ (−1)ⁿ⁺¹/n{e} = 1 − 1/2{e} + 1/3{e} − …: alterne seri, bₙ = 1/n{e}",
                  f"Σ (−1)ⁿ⁺¹/n{e} = 1 − 1/2{e} + 1/3{e} − …: alternating series, bₙ = 1/n{e}")]
        if p > 0:
            steps.append(("Alterne seri testi: bₙ > 0, azalan ve bₙ → 0 ⇒ seri yakınsar",
                          "Alternating series test: bₙ > 0, decreasing and bₙ → 0 ⇒ the series converges"))
            if p > 1:
                steps.append((f"Σ |aₙ| = Σ 1/nᵖ, p = {ps} > 1 yakınsar ⇒ mutlak yakınsak",
                              f"Σ |aₙ| = Σ 1/nᵖ with p = {ps} > 1 converges ⇒ absolutely convergent"))
            else:
                steps.append((f"Σ |aₙ| = Σ 1/nᵖ, p = {ps} ≤ 1 ıraksar ⇒ koşullu yakınsak",
                              f"Σ |aₙ| = Σ 1/nᵖ with p = {ps} ≤ 1 diverges ⇒ conditionally convergent"))
            b1 = 1.0 / (N + 1) ** float(p)
            steps.append((f"Hata tahmini: |S − S{Ns}| ≤ b{_sub(N + 1)} = {b1:.3g};  S{Ns} ≈ {sums[-1]:.6g}",
                          f"Error bound: |S − S{Ns}| ≤ b{_sub(N + 1)} = {b1:.3g};  S{Ns} ≈ {sums[-1]:.6g}"))
            steps.append((f"Toplam: S = {_lim_s(S)}", f"Sum: S = {_lim_s(S)}"))
        else:
            steps.append(("n. terim testi: |aₙ| ↛ 0 ⇒ ıraksak", "nth-term test: |aₙ| ↛ 0 ⇒ diverges"))
    else:
        k = S["k"]
        hk = " + ".join(f"1/{j}" if j > 1 else "1" for j in range(1, k + 1))
        tail = " − ".join(f"1/(N + {j})" for j in range(1, k + 1))
        steps = [(f"Σ 1/(n(n + {k})) (n = 1'den ∞'a). Kısmi kesirler: 1/(n(n + {k})) = (1/{k})·(1/n − 1/(n + {k}))",
                  f"Σ 1/(n(n + {k})) (n from 1 to ∞). Partial fractions: 1/(n(n + {k})) = (1/{k})·(1/n − 1/(n + {k}))"),
                 (f"Teleskopik toplam: ara terimler sadeleşir ⇒ S_N = (1/{k})·({hk} − {tail})",
                  f"Telescoping: the middle terms cancel ⇒ S_N = (1/{k})·({hk} − {tail})"),
                 (f"N → ∞ iken 1/(N + j) → 0 ⇒ S = (1/{k})·({hk}) = {_ff(S['limit'])}",
                  f"As N → ∞, 1/(N + j) → 0 ⇒ S = (1/{k})·({hk}) = {_ff(S['limit'])}"),
                 (f"Kontrol: S{Ns} ≈ {sums[-1]:.6g}", f"Check: S{Ns} ≈ {sums[-1]:.6g}")]
    if S["conv"]:
        ans = ("Yakınsak, S = " if tr else "Converges, S = ") + _lim_s(S)
    else:
        ans = "Iraksak" if tr else "Diverges"
    fmt = {}
    if t == "geometric":
        a, r = S["a"], S["r"]
        fmt["series"] = " + ".join(_ff(a * r ** k) for k in range(4)) + " + …"
    elif t in ("p", "harmonic"):
        ps = _ff(S["p"])
        fmt["series"] = "1 + " + " + ".join(f"1/{j}{_sup(ps) if S['p'] != 1 else ''}" for j in range(2, 5)) + " + …"
    elif t == "alternating":
        ps = _ff(S["p"])
        e = _sup(ps) if S["p"] != 1 else ""
        fmt["series"] = f"1 − 1/2{e} + 1/3{e} − 1/4{e} + …"
    else:
        k = S["k"]
        fmt["series"] = " + ".join(f"1/{j * (j + k)}" for j in range(1, 4)) + " + …"
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _setup(P)
    sol = solve(P)
    t = S["t"]
    ns = np.array(S["n"], dtype=float)
    a_n = np.array(S["terms"])
    s_n = np.array(S["sums"])
    nt = len(ns)
    L = _lim_f(S)
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.7], left=0.09, right=0.97, top=0.92, bottom=0.08, hspace=0.32)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0])
    for ax in (ax1, ax2):
        ax.set_xlim(ns[0] - 0.8, ns[-1] + 0.8)
        ax.grid(alpha=0.3)
        ax.axhline(0, color="#9CA3AF", lw=1)
    lo1, hi1 = _ylim([a_n], pad=0.15, pct=0)
    ax1.set_ylim(lo1, hi1)
    vals2 = [s_n] + ([np.array([L])] if L is not None else [])
    lo2, hi2 = _ylim(vals2, pad=0.15, pct=0)
    ax2.set_ylim(lo2, hi2 + (hi2 - lo2) * 0.25)
    bars = ax1.bar(ns, a_n, width=0.7, color=[BLUE if v >= 0 else ORANGE for v in a_n], alpha=0.0)
    ax1.set_title(("Terimler aₙ" if tr else "Terms aₙ"), fontsize=10, loc="left")
    a0 = "a₀" if S["n0"] == 0 else "a₁"
    ax2.set_title((f"Kısmi toplamlar Sₙ = {a0} + … + aₙ" if tr else f"Partial sums Sₙ = {a0} + … + aₙ"), fontsize=10, loc="left")
    ax2.set_xlabel("n")
    line, = ax2.plot([], [], color=BLUE, lw=1.4, alpha=0.7)
    pts, = ax2.plot([], [], "o", color=BLUE, ms=4)
    head, = ax2.plot([], [], "o", color=RED, ms=8, zorder=6)
    limln, = ax2.plot([], [], "--", color=GREEN, lw=2)
    limtx = ax2.text(ns[0] + 0.62 * (ns[-1] - ns[0]), 0, "", color=GREEN, fontsize=11, ha="center", va="bottom",
                     fontweight="bold", zorder=8, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=GREEN, alpha=0.9))
    band = ax2.fill_between([0, 1], [0, 0], [0, 0], color=GREEN, alpha=0.0)
    cmp_line, = ax2.plot([], [], ":", color=PURPLE, lw=1.8)
    cmp_tx = ax2.text(0, 0, "", color=PURPLE, fontsize=9)
    info = _box(ax2, 10)
    test = ax1.text(0.99, 0.95, "", transform=ax1.transAxes, ha="right", va="top", fontsize=10,
                    color="#111827", bbox=dict(boxstyle="round", fc="#F9FAFB", ec="#D1D5DB"))
    tests = {"geometric": ("Oran testi: |r| = " + _ff(abs(S.get("r", 0))), "Ratio test: |r| = " + _ff(abs(S.get("r", 0)))),
             "p": (f"p-testi: p = {_ff(S.get('p', 1))}", f"p-test: p = {_ff(S.get('p', 1))}"),
             "harmonic": ("İntegral testi: ∫ dx/x = ∞", "Integral test: ∫ dx/x = ∞"),
             "alternating": ("Alterne seri testi (AST)", "Alternating series test (AST)"),
             "telescoping": ("Teleskopik: terimler sadeleşir", "Telescoping: terms cancel")}[t]
    i0, i1, N = 8, 112, 150
    state = {"band": band}

    def update(i):
        m = 0 if i < i0 else min(nt, 1 + int((i - i0) / (i1 - i0) * (nt - 1) + 1e-9))
        for k, b in enumerate(bars):
            b.set_alpha(0.85 if k < m else 0.0)
        line.set_data(ns[:m], s_n[:m])
        pts.set_data(ns[:m], s_n[:m])
        if m > 0:
            head.set_data([ns[m - 1]], [s_n[m - 1]])
            info.set_text(f"n = {int(ns[m - 1])}:  aₙ = {a_n[m - 1]:.4g},  Sₙ = {s_n[m - 1]:.6g}")
        else:
            head.set_data([], [])
            info.set_text(("Seri: " if tr else "Series: ") + sol["fmt"]["series"])
        test.set_text(tests[0 if tr else 1] if i >= 40 else "")
        state["band"].remove()
        if t == "alternating" and L is not None and m > 1 and i < i1 + 5:
            bnext = abs(a_n[min(m, nt - 1)])
            state["band"] = ax2.fill_between([ns[0] - 0.8, ns[-1] + 0.8], [s_n[m - 1] - bnext] * 2,
                                             [s_n[m - 1] + bnext] * 2, color=GREEN, alpha=0.12)
        else:
            state["band"] = ax2.fill_between([0, 1], [0, 0], [0, 0], color=GREEN, alpha=0.0)
        if i >= i1 and L is not None:
            limln.set_data([ns[0] - 0.8, ns[-1] + 0.8], [L, L])
            limtx.set_position((ns[0] + 0.62 * (ns[-1] - ns[0]), L + (hi2 - lo2) * 0.1))
            limtx.set_text("S = " + _lim_s(S))
        else:
            limln.set_data([], [])
            limtx.set_text("")
        if i >= i1 and L is None and t in ("p", "harmonic") and S["p"] == 1:
            cmp_line.set_data(ns, np.log(ns) + 0.5772)
            cmp_tx.set_position((ns[int(nt * 0.55)], np.log(ns[int(nt * 0.55)]) + 0.5772 - (hi2 - lo2) * 0.12))
            cmp_tx.set_text("ln n + γ → ∞")
        else:
            cmp_line.set_data([], [])
            cmp_tx.set_text("")
        if i >= i1 + 8:
            info.set_text(f"S{_sub(int(ns[-1]))} ≈ {s_n[-1]:.9g}\n" + sol["answer"])
        return []

    return N, update


def _vary1(P, rnd):
    t = str(P.get("type", "geometric")).lower()
    out = {"type": t}
    if t == "geometric":
        r0 = _fr(P.get("r", "1/2"), Fraction(1, 2))
        if r0.numerator == 1 and r0.denominator in (10, 100):
            d = rnd.choice([1, 2, 4, 5, 7, 8]) if r0.denominator == 10 else rnd.choice([12, 27, 36, 45, 81])
            out.update(a=f"{d}/{r0.denominator}", r=f"1/{r0.denominator}")
        else:
            r = rnd.choice(["1/2", "1/3", "2/3", "1/4", "3/4", "-1/2", "-1/3", "1/5"])
            out.update(a=rnd.choice([1, 2, 3, 4, 5, 6]), r=r)
    elif t in ("p", "alternating"):
        out["p"] = rnd.choice([2, 3, 4, 0.5, 1, 1.5] if t == "p" else [1, 2, 0.5, 3])
    elif t == "telescoping":
        out["k"] = rnd.choice([1, 2, 3, 4])
    return out
''',
}
EXAMPLES += [
    {"id": "calc2-series-1", "kind": "series_convergence",
     "title": ("Geometrik seri", "Geometric series"),
     "q": ("Σ {a}·({r})ⁿ (n = 0, 1, 2, …) serisi yakınsak mı? Yakınsaksa toplamını bul:  {series}",
           "Does Σ {a}·({r})ⁿ (n = 0, 1, 2, …) converge? If so, find its sum:  {series}"),
     "P": {"type": "geometric", "a": 3, "r": "1/2"}},
    {"id": "calc2-series-2", "kind": "series_convergence",
     "topics": ["p-series", "basel", "zeta"],
     "title": ("p-serisi testi", "The p-series test"),
     "q": ("p = {p} için Σ 1/nᵖ = {series} serisi yakınsak mı ıraksak mı? Kısmi toplamları inceleyerek açıkla.",
           "For p = {p}, does Σ 1/nᵖ = {series} converge or diverge? Explain using the partial sums."),
     "P": {"type": "p", "p": 2}},
    {"id": "calc2-series-3", "kind": "series_convergence",
     "topics": ["alternating harmonic", "conditional convergence", "koşullu yakınsaklık"],
     "title": ("Alterne harmonik seri", "Alternating harmonic series"),
     "q": ("{series} serisinin (p = {p}) yakınsaklığını alterne seri testiyle incele. Mutlak mı, koşullu mu yakınsar?",
           "Use the alternating series test on {series} (p = {p}). Is the convergence absolute or conditional?"),
     "P": {"type": "alternating", "p": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["parametric_curve"] = {
    "course": "calc2",
    "title": ("Parametrik eğri ve dy/dx", "Parametric curve and dy/dx"),
    "topics": ["parametric equations", "parametric curves", "parametric curve", "derivative of parametric",
               "tangent line parametric", "dy/dx parametric", "velocity vector", "cycloid",
               "parametrik denklemler", "parametrik eğri", "parametrik türev", "teğet doğrusu",
               "hız vektörü", "sikloid"],
    "code": _H + r'''
from matplotlib.patches import FancyArrowPatch


def _setup(P):
    t, X = _parse(P.get("x", "3*cos(t)"), "t", "3*cos(t)")
    _, Y = _parse(P.get("y", "2*sin(t)"), "t", "2*sin(t)")
    T0, t0 = _pv(P.get("t0", 0), 0)
    T1, t1 = _pv(P.get("t1", "2*pi"), "2*pi")
    if t1 < t0:
        T0, t0, T1, t1 = T1, t1, T0, t0
    if t1 - t0 < 1e-6:
        T1, t1 = T0 + 1, t0 + 1
    TP, tp = _pv(P.get("tp", (t0 + t1) / 2), (t0 + t1) / 2)
    dX, dY = sp.diff(X, t), sp.diff(Y, t)
    return {"t": t, "X": X, "Y": Y, "T0": T0, "T1": T1, "t0": t0, "t1": t1, "TP": TP, "tp": tp,
            "dX": dX, "dY": dY, "hx": _num(X, t), "hy": _num(Y, t), "hdx": _num(dX, t), "hdy": _num(dY, t)}


def _troots(h, lo, hi):
    ts = np.linspace(lo, hi, 4001)
    ys = h(ts)
    scale = float(np.nanmax(np.abs(ys))) if np.any(np.isfinite(ys)) else 1.0
    tol = 2e-4 * max(scale, 1e-9)
    out = []
    for k in range(len(ts)):
        y = ys[k]
        if not np.isfinite(y):
            continue
        r = None
        if k + 1 < len(ts) and np.isfinite(ys[k + 1]) and y * ys[k + 1] < 0:
            a, b = ts[k], ts[k + 1]
            for _ in range(60):
                m = (a + b) / 2
                if _at1(h, a) * _at1(h, m) <= 0:
                    b = m
                else:
                    a = m
            r = (a + b) / 2
        elif abs(y) < tol and (k == 0 or abs(y) <= abs(ys[k - 1])) and (k == len(ts) - 1 or abs(y) <= abs(ys[k + 1])):
            r = ts[k]
        if r is not None and (not out or abs(r - out[-1]) > 1e-3):
            out.append(float(r))
    return out


def _nice_t(r):
    try:
        c = sp.nsimplify(r, [sp.pi], tolerance=1e-4)
        if len(sp.sstr(c)) <= 9 and abs(float(c) - r) < 2e-3:
            return c
    except Exception:
        pass
    return sp.Float(round(r, 4), 4)


def _pm(s):
    s = str(s)
    return "(" + s + ")" if any(c in s for c in " /-+") else s


def _lin(m, b):
    if b == 0:
        return f"y = {_pp(m)}·x"
    try:
        if b.is_number and b < 0:
            return f"y = {_pp(m)}·x - {_par(_pp(-b))}"
    except Exception:
        pass
    return f"y = {_pp(m)}·x + {_par(_pp(b))}"


def _ev(e, t, v):
    try:
        r = sp.simplify(e.subs(t, v))
        if r.is_number and r.is_finite:
            return r
    except Exception:
        pass
    return None


def solve(P):
    S = _setup(P)
    t, X, Y, dX, dY, TP = S["t"], S["X"], S["Y"], S["dX"], S["dY"], S["TP"]
    xs, ys = _pp(X), _pp(Y)
    steps = [(f"x(t) = {xs},  y(t) = {ys},  t ∈ [{_pp(S['T0'])}, {_pp(S['T1'])}]",
              f"x(t) = {xs},  y(t) = {ys},  t ∈ [{_pp(S['T0'])}, {_pp(S['T1'])}]"),
             (f"dx/dt = {_pp(dX)},  dy/dt = {_pp(dY)}", f"dx/dt = {_pp(dX)},  dy/dt = {_pp(dY)}")]
    try:
        dydx = sp.simplify(dY / dX) if dX != 0 else sp.zoo
    except Exception:
        dydx = dY / dX
    steps.append((f"dy/dx = (dy/dt)/(dx/dt) = {_pp(dydx)}", f"dy/dx = (dy/dt)/(dx/dt) = {_pp(dydx)}"))
    x0, y0 = _ev(X, t, TP), _ev(Y, t, TP)
    dx0, dy0 = _ev(dX, t, TP), _ev(dY, t, TP)
    tps = _pp(TP)
    tr = P.get("lang", "tr") == "tr"
    if x0 is None or y0 is None or dx0 is None or dy0 is None:
        steps.append((f"t = {tps} noktasında eğri tanımlı değil.", f"The curve is not defined at t = {tps}."))
        return {"answer": f"dy/dx = {_pp(dydx)}", "steps": steps, "fmt": {"xt": xs, "yt": ys, "TP": tps,
                "T0": _pp(S["T0"]), "T1": _pp(S["T1"])}}
    pt = f"({_pp(x0)}, {_pp(y0)})"
    if not (x0.is_Rational and y0.is_Rational):
        pt += f" ≈ ({_g(float(x0), 4)}, {_g(float(y0), 4)})"
    steps.append((f"t = {tps}: (x, y) = {pt}", f"t = {tps}: (x, y) = {pt}"))
    if dx0 == 0 and dy0 == 0:
        mtxt = ("tanımsız (tekil nokta)", "undefined (singular point)")
        steps.append((f"t = {tps} için dx/dt = dy/dt = 0: tekil nokta (sivri uç olabilir)",
                      f"At t = {tps}, dx/dt = dy/dt = 0: a singular point (possibly a cusp)"))
    elif dx0 == 0:
        mtxt = ("∞ (dikey teğet)", "∞ (vertical tangent)")
        steps.append((f"dx/dt = 0, dy/dt ≠ 0 ⇒ dikey teğet: x = {_pp(x0)}",
                      f"dx/dt = 0, dy/dt ≠ 0 ⇒ vertical tangent: x = {_pp(x0)}"))
    else:
        m = sp.simplify(dy0 / dx0)
        b = sp.simplify(y0 - m * x0)
        mtxt = (_ex(m), _ex(m))
        steps.append((f"Eğim: m = dy/dx|t={tps} = {_par(_pp(dy0))} ÷ {_par(_pp(dx0))} = {_ex(m)}",
                      f"Slope: m = dy/dx|t={tps} = {_par(_pp(dy0))} ÷ {_par(_pp(dx0))} = {_ex(m)}"))
        line = _lin(m, b)
        steps.append((f"Teğet doğru: y − {_pm(_pp(y0))} = {_pm(_pp(m))}(x − {_pm(_pp(x0))})  ⇔  {line}",
                      f"Tangent line: y − {_pm(_pp(y0))} = {_pm(_pp(m))}(x − {_pm(_pp(x0))})  ⇔  {line}"))
        try:
            d2 = sp.simplify(sp.diff(dydx, t) / dX)
            d2v = _ev(d2, t, TP)
            if d2v is not None:
                cc = ("yukarı bükey (∪)", "concave up (∪)") if d2v > 0 else (
                    ("aşağı bükey (∩)", "concave down (∩)") if d2v < 0 else ("bükeylik belirsiz", "no concavity info"))
                steps.append((f"d²y/dx² = [d/dt(dy/dx)]/(dx/dt) = {_ex(d2v)} ⇒ {cc[0]}",
                              f"d²y/dx² = [d/dt(dy/dx)]/(dx/dt) = {_ex(d2v)} ⇒ {cc[1]}"))
        except Exception:
            pass
    sp_ = math.hypot(float(dx0), float(dy0))
    steps.append((f"Hız vektörü v = (dx/dt, dy/dt) = ({_pp(dx0)}, {_pp(dy0)}),  |v| ≈ {_g(sp_, 4)}",
                  f"Velocity vector v = (dx/dt, dy/dt) = ({_pp(dx0)}, {_pp(dy0)}),  |v| ≈ {_g(sp_, 4)}"))
    hz = [r for r in _troots(S["hdy"], S["t0"], S["t1"]) if abs(_at1(S["hdx"], r)) > 1e-6]
    vt = [r for r in _troots(S["hdx"], S["t0"], S["t1"]) if abs(_at1(S["hdy"], r)) > 1e-6]
    sg = [r for r in _troots(S["hdx"], S["t0"], S["t1"]) if abs(_at1(S["hdy"], r)) <= 1e-6]
    if hz or vt:
        hs = ", ".join(_pp(_nice_t(r)) for r in hz[:5]) or "—"
        vs = ", ".join(_pp(_nice_t(r)) for r in vt[:5]) or "—"
        steps.append((f"Yatay teğetler (dy/dt = 0): t = {hs};  dikey teğetler (dx/dt = 0): t = {vs}",
                      f"Horizontal tangents (dy/dt = 0): t = {hs};  vertical tangents (dx/dt = 0): t = {vs}"))
    if sg:
        ss = ", ".join(f"t = {_pp(_nice_t(r))} → ({_g(_at1(S['hx'], r), 4)}, {_g(_at1(S['hy'], r), 4)})" for r in sg[:5])
        steps.append((f"dx/dt = dy/dt = 0 olan tekil noktalar (sivri uç): {ss}",
                      f"Singular points where dx/dt = dy/dt = 0 (cusps): {ss}"))
    ans = (f"dy/dx = {_pp(dydx)};  t = {tps} için m = {mtxt[0]}" if tr else
           f"dy/dx = {_pp(dydx)};  at t = {tps}, m = {mtxt[1]}")
    return {"answer": ans, "steps": steps,
            "fmt": {"xt": xs, "yt": ys, "TP": tps, "T0": _pp(S["T0"]), "T1": _pp(S["T1"])}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _setup(P)
    sol = solve(P)
    t0, t1, tp = S["t0"], S["t1"], S["tp"]
    ts = np.linspace(t0, t1, 700)
    xs, ys = S["hx"](ts), S["hy"](ts)
    vx, vy = S["hdx"](ts), S["hdy"](ts)
    ok = np.isfinite(xs) & np.isfinite(ys)
    if not np.any(ok):
        xs, ys, ok = np.cos(ts), np.sin(ts), np.ones_like(ts, dtype=bool)
    xlo, xhi = float(np.min(xs[ok])), float(np.max(xs[ok]))
    ylo, yhi = float(np.min(ys[ok])), float(np.max(ys[ok]))
    ext = max(xhi - xlo, yhi - ylo, 1e-3)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.9, bottom=0.08)
    if 0.4 <= (xhi - xlo + 1e-9) / (yhi - ylo + 1e-9) <= 2.5:
        pad = 0.15 * ext
        x0_, x1_ = xlo - pad, xhi + pad
        y0_, y1_ = ylo - pad, yhi + pad + 0.12 * ext
        want = (8.0 * 0.91) / (5.4 * 0.82)
        if (x1_ - x0_) / (y1_ - y0_) < want:
            c_, h_ = (x0_ + x1_) / 2, (y1_ - y0_) * want / 2
            x0_, x1_ = c_ - h_, c_ + h_
        else:
            c_, h_ = (y0_ + y1_) / 2, (x1_ - x0_) / want / 2
            y0_, y1_ = c_ - h_, c_ + h_
        ax.set_xlim(x0_, x1_)
        ax.set_ylim(y0_, y1_)
        ax.set_aspect("equal", adjustable="box")
    else:
        xr, yr = max(xhi - xlo, 1e-3), max(yhi - ylo, 1e-3)
        ax.set_xlim(xlo - 0.06 * xr, xhi + 0.06 * xr)
        ax.set_ylim(ylo - 0.25 * yr, yhi + 0.55 * yr)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#9CA3AF", lw=1)
    ax.axvline(0, color="#9CA3AF", lw=1)
    sp_ = np.sqrt(vx ** 2 + vy ** 2)
    vmax = float(np.nanmax(sp_[np.isfinite(sp_)])) if np.any(np.isfinite(sp_)) else 1.0
    sc = 0.22 * ext / max(vmax, 1e-9)
    curve, = ax.plot([], [], color=BLUE, lw=2.4, zorder=3)
    ghost, = ax.plot(xs, ys, color=BLUE, lw=1, alpha=0.0, ls="--")
    dot, = ax.plot([], [], "o", color=RED, ms=9, zorder=6)
    arr = FancyArrowPatch((0, 0), (0, 0), arrowstyle="-|>", mutation_scale=16, color=GREEN, lw=2.2, zorder=7)
    ax.add_patch(arr)
    tan, = ax.plot([], [], color=ORANGE, lw=2.2, zorder=4)
    hz = [r for r in _troots(S["hdy"], t0, t1) if abs(_at1(S["hdx"], r)) > 1e-6]
    vt = [r for r in _troots(S["hdx"], t0, t1) if abs(_at1(S["hdy"], r)) > 1e-6]
    hmk, = ax.plot([], [], "^", color=PURPLE, ms=9, zorder=6, label=("yatay teğet" if tr else "horizontal tangent"))
    vmk, = ax.plot([], [], ">", color=GRAY, ms=9, zorder=6, label=("dikey teğet" if tr else "vertical tangent"))
    sg = [r for r in _troots(S["hdx"], t0, t1) if abs(_at1(S["hdy"], r)) <= 1e-6]
    smk, = ax.plot([], [], "X", color=RED, ms=9, zorder=6,
                   label=(("tekil nokta (sivri uç)" if tr else "singular point (cusp)") if sg else None))
    mtx = ax.text(0, 0, "", color=ORANGE, fontsize=11, fontweight="bold", zorder=8,
                  bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=ORANGE, alpha=0.9))
    info = _box(ax, 10)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(f"x(t) = {sol['fmt']['xt']},   y(t) = {sol['fmt']['yt']}", fontsize=12)
    xp, yp = _at1(S["hx"], tp), _at1(S["hy"], tp)
    dxp, dyp = _at1(S["hdx"], tp), _at1(S["hdy"], tp)
    N = 160

    def update(i):
        s = _ramp(i, 0, 100)
        m = max(2, int(s * (len(ts) - 1)) + 1)
        curve.set_data(xs[:m], ys[:m])
        ghost.set_alpha(0.0)
        if i < 104:
            k = m - 1
            px, py, qx, qy, tc = xs[k], ys[k], vx[k], vy[k], ts[k]
        else:
            u = _ramp(i, 104, 116)
            px, py, qx, qy, tc = xp, yp, dxp, dyp, tp
        if np.isfinite(px) and np.isfinite(py):
            dot.set_data([px], [py])
            if np.isfinite(qx) and np.isfinite(qy):
                arr.set_positions((px, py), (px + sc * qx, py + sc * qy))
                arr.set_alpha(1.0)
            else:
                arr.set_alpha(0.0)
        else:
            dot.set_data([], [])
            arr.set_alpha(0.0)
        if i >= 116 and np.isfinite(xp) and np.isfinite(yp):
            L = 0.45 * ext * _ramp(i, 116, 132)
            nrm = math.hypot(dxp, dyp)
            if nrm > 1e-12:
                ux, uy = dxp / nrm, dyp / nrm
                tan.set_data([xp - L * ux, xp + L * ux], [yp - L * uy, yp + L * uy])
            else:
                tan.set_data([], [])
            mtx.set_position((xp + 0.05 * ext, yp + 0.08 * ext))
            mtx.set_text(("m = " + sol["answer"].split("m = ")[-1]) if "m = " in sol["answer"] else "")
        else:
            tan.set_data([], [])
            mtx.set_text("")
        if i >= 132:
            hmk.set_data([_at1(S["hx"], r) for r in hz], [_at1(S["hy"], r) for r in hz])
            vmk.set_data([_at1(S["hx"], r) for r in vt], [_at1(S["hy"], r) for r in vt])
            smk.set_data([_at1(S["hx"], r) for r in sg], [_at1(S["hy"], r) for r in sg])
        else:
            hmk.set_data([], [])
            vmk.set_data([], [])
            smk.set_data([], [])
        if i < 104:
            info.set_text((f"1) Eğri çiziliyor: t = {tc:.2f}\n   (x, y) = ({px:.2f}, {py:.2f})\n"
                           f"   v = (x'(t), y'(t)) = ({qx:.2f}, {qy:.2f})") if tr else
                          (f"1) Tracing the curve: t = {tc:.2f}\n   (x, y) = ({px:.2f}, {py:.2f})\n"
                           f"   v = (x'(t), y'(t)) = ({qx:.2f}, {qy:.2f})"))
        elif i < 132:
            info.set_text((f"2) t = {sol['fmt']['TP']}: teğet, hız vektörü yönünde\n   dy/dx = (dy/dt)/(dx/dt)" if tr else
                           f"2) t = {sol['fmt']['TP']}: the tangent points along v\n   dy/dx = (dy/dt)/(dx/dt)"))
        else:
            info.set_text(("3) " if tr else "3) ") + sol["answer"].replace(";  ", "\n   "))
        return []

    return N, update


def _vary1(P, rnd):
    xs, ys = str(P.get("x", "")), str(P.get("y", ""))
    if "sin(t)" in xs and "t -" in xs:
        r = rnd.choice([1, 2, 3])
        xs_, ys_ = ("t - sin(t)", "1 - cos(t)") if r == 1 else (f"{r}*(t - sin(t))", f"{r}*(1 - cos(t))")
        return {"x": xs_, "y": ys_, "t0": 0, "t1": rnd.choice(["2*pi", "4*pi"]),
                "tp": rnd.choice(["pi/3", "pi/2", "2*pi/3", "pi/4"])}
    if "cos" in xs or "sin" in ys:
        a, b = rnd.sample([2, 3, 4, 5], 2)
        return {"x": f"{a}*cos(t)", "y": f"{b}*sin(t)", "t0": 0, "t1": "2*pi",
                "tp": rnd.choice(["pi/6", "pi/4", "pi/3", "2*pi/3", "3*pi/4", "5*pi/6"])}
    c, k = rnd.choice([0, 1, 2]), rnd.choice([3, 4])
    return {"x": f"t**2 - {c}" if c else "t**2", "y": f"t**3 - {k}*t", "t0": -2, "t1": 2,
            "tp": rnd.choice([-2, 2, 1, -1])}
''',
}
EXAMPLES += [
    {"id": "calc2-param-1", "kind": "parametric_curve",
     "title": ("Elipsin teğeti", "Tangent to an ellipse"),
     "q": ("x(t) = {xt}, y(t) = {yt} ({T0} ≤ t ≤ {T1}) eğrisi için dy/dx'i bul ve t = {TP} noktasındaki "
           "teğet doğrunun denklemini yaz.",
           "For x(t) = {xt}, y(t) = {yt} ({T0} ≤ t ≤ {T1}), find dy/dx and the tangent line at t = {TP}."),
     "P": {"x": "3*cos(t)", "y": "2*sin(t)", "t0": 0, "t1": "2*pi", "tp": "pi/4"}},
    {"id": "calc2-param-2", "kind": "parametric_curve",
     "topics": ["word problem", "rolling wheel", "sözel problem", "yuvarlanan tekerlek"],
     "title": ("Sözel problem: yuvarlanan tekerlek (sikloid)", "Word problem: a rolling wheel (cycloid)"),
     "q": ("Yuvarlanan bir tekerleğin çemberindeki bir nokta x(t) = {xt}, y(t) = {yt} yolunu çiziyor. "
           "t = {TP} anında hareket yönünün eğimi (dy/dx) nedir? Nokta hangi anlarda yere değer?",
           "A point on the rim of a rolling wheel traces x(t) = {xt}, y(t) = {yt}. What is the slope dy/dx "
           "of its path at t = {TP}? When does the point touch the ground?"),
     "P": {"x": "2*(t - sin(t))", "y": "2*(1 - cos(t))", "t0": 0, "t1": "4*pi", "tp": "pi/3"}},
    {"id": "calc2-param-3", "kind": "parametric_curve",
     "topics": ["particle motion", "parçacık hareketi", "horizontal tangent", "vertical tangent"],
     "title": ("Hareketli parçacık: yatay ve dikey teğetler", "Moving particle: horizontal and vertical tangents"),
     "q": ("Bir parçacığın konumu x(t) = {xt}, y(t) = {yt} ({T0} ≤ t ≤ {T1}). t = {TP} anında yolun eğimini "
           "bul; yatay ve dikey teğetlerin olduğu anları belirle.",
           "A particle moves along x(t) = {xt}, y(t) = {yt} ({T0} ≤ t ≤ {T1}). Find the slope of its path at "
           "t = {TP} and the times of horizontal and vertical tangents."),
     "P": {"x": "t**2 - 1", "y": "t**3 - 3*t", "t0": -2, "t1": 2, "tp": 2}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["polar_curve"] = {
    "course": "calc2",
    "title": ("Kutupsal eğri ve alan", "Polar curve and enclosed area"),
    "topics": ["polar coordinates", "polar curves", "polar curve", "area in polar coordinates",
               "polar area", "cardioid", "rose curve", "limacon", "kutupsal koordinatlar", "kutupsal eğri",
               "kutupsal alan", "kardioid", "gül eğrisi", "limason"],
    "code": _H + r'''
from matplotlib.patches import Polygon


def _setup(P):
    th, r = _parse(P.get("r", "1 + cos(theta)"), "theta", "1 + cos(theta)")
    T0, a0 = _pv(P.get("th0", 0), 0)
    T1, a1 = _pv(P.get("th1", "2*pi"), "2*pi")
    if a1 < a0:
        T0, a0, T1, a1 = T1, a1, T0, a0
    if a1 - a0 < 1e-6:
        T1, a1 = T0 + 2 * sp.pi, a0 + 2 * math.pi
    return {"th": th, "r": r, "T0": T0, "T1": T1, "a0": a0, "a1": a1, "hr": _num(r, th)}


def _area(S):
    th, r = S["th"], S["r"]
    raw = sp.expand(r ** 2)
    try:
        from sympy.simplify.fu import TR8
        red = sp.expand(TR8(raw))
    except Exception:
        red = raw
    h2 = _num(raw, th)
    num = 0.5 * _simp(h2, S["a0"], S["a1"], 4000)
    F = _anti(red, th)
    val = None
    if F is not None:
        Fa, Fb = _at(F, th, S["T0"]), _at(F, th, S["T1"])
        if Fa is not None and Fb is not None:
            val = sp.simplify((Fb - Fa) / 2)
            if not _same(val, num, 1e-4):
                val = None
    else:
        Fa = Fb = None
    return raw, red, F, Fa, Fb, val, num


def _zeros(h, lo, hi):
    ts = np.linspace(lo, hi, 3001)
    ys = h(ts)
    out = []
    for k in range(len(ts) - 1):
        y0, y1 = ys[k], ys[k + 1]
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        hit = None
        if y0 == 0:
            hit = ts[k]
        elif y0 * y1 < 0:
            hit = ts[k] - y0 * (ts[k + 1] - ts[k]) / (y1 - y0)
        elif abs(y0) < 1e-4 and abs(y0) <= abs(y1) and (k == 0 or abs(y0) <= abs(ys[k - 1])):
            hit = ts[k]
        if hit is not None and (not out or abs(hit - out[-1]) > 1e-3):
            out.append(float(hit))
    if np.isfinite(ys[-1]) and abs(ys[-1]) < 1e-9 and (not out or abs(ts[-1] - out[-1]) > 1e-3):
        out.append(float(ts[-1]))
    return out


def _nice(v):
    try:
        c = sp.nsimplify(v, [sp.pi], tolerance=1e-4)
        if len(sp.sstr(c)) <= 9 and abs(float(c) - v) < 2e-3:
            return _pp(c)
    except Exception:
        pass
    return _g(v, 4)


def solve(P):
    S = _setup(P)
    th, r = S["th"], S["r"]
    raw, red, F, Fa, Fb, val, num = _area(S)
    rs, A0, A1 = _pp(r), _pp(S["T0"]), _pp(S["T1"])
    steps = [(f"Kutupsal alan formülü: A = ½ {_I(A0, A1)} r² dθ,  r = {rs}",
              f"Polar area formula: A = ½ {_I(A0, A1)} r² dθ,  r = {rs}"),
             (f"r² = ({rs})² = {_pp(raw)}", f"r² = ({rs})² = {_pp(raw)}")]
    if red != raw:
        steps.append((f"Kuvvet indirgeme (ör. cos²θ = (1 + cos 2θ)/2): r² = {_pp(red)}",
                      f"Power reduction (e.g. cos²θ = (1 + cos 2θ)/2): r² = {_pp(red)}"))
    if val is not None:
        steps.append((f"∫ r² dθ = {_pp(F)}", f"∫ r² dθ = {_pp(F)}"))
        steps.append((f"A = ½[F({A1}) − F({A0})] = ½({_pp(Fb)} − {_par(_pp(Fa))}) = {_ex(val)}",
                      f"A = ½[F({A1}) − F({A0})] = ½({_pp(Fb)} − {_par(_pp(Fa))}) = {_ex(val)}"))
        res = _ex(val)
    else:
        steps.append((f"İntegral sayısal (Simpson): A ≈ {_g(num, 6)}", f"Numerical integral (Simpson): A ≈ {_g(num, 6)}"))
        res = _g(num, 6)
    zs = _zeros(S["hr"], S["a0"], S["a1"])
    if zs:
        zl = ", ".join(_nice(z) for z in zs[:6])
        steps.append((f"Eğri kutup noktasından geçer (r = 0): θ = {zl}", f"The curve passes through the pole (r = 0) at θ = {zl}"))
    steps.append((f"Sonuç: A = {res}", f"Result: A = {res}"))
    return {"answer": f"A = {res}", "steps": steps, "fmt": {"rt": rs, "TH0": A0, "TH1": A1}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _setup(P)
    sol = solve(P)
    a0, a1 = S["a0"], S["a1"]
    ths = np.linspace(a0, a1, 721)
    rr = S["hr"](ths)
    rr = np.where(np.isfinite(rr), rr, 0.0)
    xs, ys = rr * np.cos(ths), rr * np.sin(ths)
    cum = _cum(ths, 0.5 * rr ** 2)
    R = max(float(np.max(np.abs(rr))), 1e-3)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.05, right=0.98, top=0.9, bottom=0.06)
    want = (8.0 * 0.93) / (5.4 * 0.84)
    h_ = 1.22 * R
    ax.set_xlim(-h_ * want, h_ * want)
    ax.set_ylim(-h_, h_)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp_ in ax.spines.values():
        sp_.set_visible(False)
    step = float(10 ** math.floor(math.log10(R)))
    if R / step < 2.5:
        step /= 2
    rad = step
    while rad <= 1.15 * R:
        c = np.linspace(0, 2 * np.pi, 120)
        ax.plot(rad * np.cos(c), rad * np.sin(c), color="#E5E7EB", lw=0.9, zorder=0)
        ax.text(rad * math.cos(math.radians(80)), rad * math.sin(math.radians(80)), _g(rad, 3), fontsize=8,
                color=GRAY, zorder=0)
        rad += step
    for k in range(12):
        ang = k * np.pi / 6
        ax.plot([0, 1.15 * R * math.cos(ang)], [0, 1.15 * R * math.sin(ang)], color="#E5E7EB", lw=0.8, zorder=0)
        if k % 3 == 0:
            ax.text(1.19 * R * math.cos(ang), 1.19 * R * math.sin(ang), ["0", "π/2", "π", "3π/2"][k // 3],
                    fontsize=9, color=GRAY, ha="center", va="center")
    fill = Polygon(np.zeros((3, 2)), closed=True, fc=GREEN, alpha=0.28, ec="none", zorder=1)
    ax.add_patch(fill)
    wedge = Polygon(np.zeros((3, 2)), closed=True, fc=PURPLE, alpha=0.0, ec="none", zorder=2)
    ax.add_patch(wedge)
    curve, = ax.plot([], [], color=BLUE, lw=2.5, zorder=3)
    ray, = ax.plot([], [], "--", color=GRAY, lw=1.3, zorder=2)
    seg, = ax.plot([], [], color=ORANGE, lw=2.2, zorder=4)
    dot, = ax.plot([], [], "o", color=RED, ms=8, zorder=5)
    ax.plot([0], [0], "o", color="#111827", ms=4, zorder=5)
    info = _box(ax, 10)
    big = ax.text(0.98, 0.04, "", transform=ax.transAxes, ha="right", fontsize=15, zorder=9,
                  bbox=dict(boxstyle="round", fc="#ECFDF5", ec=GREEN))
    ax.set_title(f"r = {sol['fmt']['rt']},   {sol['fmt']['TH0']} ≤ θ ≤ {sol['fmt']['TH1']}", fontsize=12)
    nn = len(ths)
    N = 150
    dth = (a1 - a0) / 18

    def update(i):
        s = _ramp(i, 5, 110)
        j = int(round(s * (nn - 1)))
        if i >= 5:
            curve.set_data(xs[:j + 1], ys[:j + 1])
            pts = np.vstack([[0.0, 0.0], np.column_stack([xs[:j + 1], ys[:j + 1]])])
            fill.set_xy(pts if len(pts) >= 3 else np.zeros((3, 2)))
        else:
            curve.set_data([], [])
            fill.set_xy(np.zeros((3, 2)))
        t = ths[j]
        if 5 <= i < 112:
            ray.set_data([0, 1.15 * R * math.cos(t)], [0, 1.15 * R * math.sin(t)])
            seg.set_data([0, xs[j]], [0, ys[j]])
            dot.set_data([xs[j]], [ys[j]])
            jj = max(0, j - int(dth / (ths[1] - ths[0])))
            wp = np.vstack([[0.0, 0.0], np.column_stack([xs[jj:j + 1], ys[jj:j + 1]])])
            wedge.set_xy(wp if len(wp) >= 3 else np.zeros((3, 2)))
            wedge.set_alpha(0.35)
            neg = ("  (r < 0: nokta ışının tersinde)" if tr else "  (r < 0: point opposite the ray)") if rr[j] < -1e-9 else ""
            info.set_text((f"θ = {t:.2f} rad ({math.degrees(t):.0f}°)\nr = {rr[j]:.3f}{neg}\n"
                           f"A(θ) = ½∫ r² dθ ≈ {cum[j]:.4f}") if tr else
                          (f"θ = {t:.2f} rad ({math.degrees(t):.0f}°)\nr = {rr[j]:.3f}{neg}\n"
                           f"A(θ) = ½∫ r² dθ ≈ {cum[j]:.4f}"))
        else:
            ray.set_data([], [])
            seg.set_data([], [])
            dot.set_data([], [])
            wedge.set_alpha(0.0)
            wedge.set_xy(np.zeros((3, 2)))
            if i < 5:
                info.set_text(("Işın θ açısıyla döner; nokta r(θ) uzaklıkta" if tr else
                               "The ray turns through θ; the point sits at distance r(θ)"))
            else:
                info.set_text(("Her ince dilim ≈ ½ r² dθ;\ndilimlerin toplamı = alan" if tr else
                               "Each thin slice ≈ ½ r² dθ;\nthe slices add up to the area"))
        big.set_text(sol["answer"] if i >= 115 else "")
        return []

    return N, update


def _vary1(P, rnd):
    S = _setup(P)
    full = S["a1"] - S["a0"] >= 2 * math.pi - 1e-6
    if not full:
        c, k = rnd.choice([1, 2, 3]), rnd.choice([2, 3, 4])
        fn = rnd.choice(["sin", "cos"])
        if fn == "sin":
            return {"r": f"{c}*sin({k}*theta)" if c > 1 else f"sin({k}*theta)", "th0": 0, "th1": f"pi/{k}"}
        return {"r": f"{c}*cos({k}*theta)" if c > 1 else f"cos({k}*theta)", "th0": f"-pi/{2 * k}", "th1": f"pi/{2 * k}"}
    vals = [abs(_at1(S["hr"], v)) for v in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
    if min(vals) < 1e-9:
        c = rnd.choice([1, 2, 3, 4])
        form = rnd.choice(["1 + cos(theta)", "1 - cos(theta)", "1 + sin(theta)", "1 - sin(theta)"])
        return {"r": f"{c}*({form})" if c > 1 else form, "th0": 0, "th1": "2*pi"}
    a = rnd.choice([2, 3, 4, 5])
    b = rnd.choice([v for v in (1, 2, 3) if v < a])
    return {"r": f"{a} + {b}*cos(theta)" if b > 1 else f"{a} + cos(theta)", "th0": 0, "th1": "2*pi"}
''',
}
EXAMPLES += [
    {"id": "calc2-polar-1", "kind": "polar_curve",
     "title": ("Kardioidin alanı", "Area of a cardioid"),
     "q": ("r = {rt} kardioidinin ({TH0} ≤ θ ≤ {TH1}) çevrelediği alanı bul.",
           "Find the area enclosed by the cardioid r = {rt} ({TH0} ≤ θ ≤ {TH1})."),
     "P": {"r": "1 + cos(theta)", "th0": 0, "th1": "2*pi"}},
    {"id": "calc2-polar-2", "kind": "polar_curve",
     "title": ("Gül eğrisinin bir yaprağı", "One petal of a rose curve"),
     "q": ("r = {rt} gül eğrisinin {TH0} ≤ θ ≤ {TH1} aralığında çizdiği bir yaprağın alanını bul.",
           "Find the area of one petal of the rose r = {rt}, traced for {TH0} ≤ θ ≤ {TH1}."),
     "P": {"r": "2*sin(2*theta)", "th0": 0, "th1": "pi/2"}},
    {"id": "calc2-polar-3", "kind": "polar_curve",
     "topics": ["word problem", "sözel problem", "limaçon"],
     "title": ("Sözel problem: çim fıskiyesi", "Word problem: a lawn sprinkler"),
     "q": ("Bir fıskiye, θ yönünde r = {rt} metreye kadar su püskürtüyor ({TH0} ≤ θ ≤ {TH1}). "
           "Sulanan bölgenin alanı kaç m²'dir?",
           "A sprinkler throws water r = {rt} metres in direction θ ({TH0} ≤ θ ≤ {TH1}). "
           "What area (in m²) gets watered?"),
     "P": {"r": "3 + cos(theta)", "th0": 0, "th1": "2*pi"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["arc_length"] = {
    "course": "calc2",
    "title": ("Eğri yay uzunluğu", "Arc length of a curve"),
    "topics": ["arc length", "length of a curve", "curve length", "arc length formula",
               "applications of integration", "catenary", "yay uzunluğu", "eğri uzunluğu",
               "eğrinin uzunluğu", "zincir eğrisi", "integralin uygulamaları"],
    "code": _H + r'''

def _setup(P):
    x, f = _parse(P.get("f", "2/3*x**(3/2)"), "x", "2/3*x**(3/2)")
    A, af = _pv(P.get("a", 0), 0)
    B, bf = _pv(P.get("b", 1), 1)
    if bf < af:
        A, af, B, bf = B, bf, A, af
    if bf - af < 1e-9:
        B, bf = A + 1, af + 1
    if af >= 0:
        xn = sp.Symbol("x", nonnegative=True)
        f, x = f.subs(x, xn), xn
    d = sp.diff(f, x)
    rad = sp.factor(sp.together(1 + d ** 2))
    try:
        ig = sp.simplify(sp.sqrt(rad))
    except Exception:
        ig = sp.sqrt(rad)
    return {"x": x, "f": f, "A": A, "B": B, "a": af, "b": bf, "d": d, "rad": rad, "ig": ig,
            "h": _num(f, x), "hig": _num(ig, x)}


def _poly_len(S, n):
    xs = np.linspace(S["a"], S["b"], n + 1)
    ys = S["h"](xs)
    ys = np.where(np.isfinite(ys), ys, 0.0)
    return float(np.sum(np.sqrt(np.diff(xs) ** 2 + np.diff(ys) ** 2))), xs, ys


def solve(P):
    S = _setup(P)
    x, ig, A, B = S["x"], S["ig"], S["A"], S["B"]
    I = _I(_pp(A), _pp(B))
    steps = [(f"Yay uzunluğu: L = {I} √(1 + [f'(x)]²) dx,  f(x) = {_pp(S['f'])}",
              f"Arc length: L = {I} √(1 + [f'(x)]²) dx,  f(x) = {_pp(S['f'])}"),
             (f"f'(x) = {_pp(S['d'])}", f"f'(x) = {_pp(S['d'])}"),
             (f"1 + [f'(x)]² = {_pp(S['rad'])}", f"1 + [f'(x)]² = {_pp(S['rad'])}")]
    if not ig.has(sp.sqrt(S["rad"])) and not any(isinstance(a_, sp.Pow) and a_.exp == sp.Rational(1, 2)
                                               for a_ in sp.preorder_traversal(ig)):
        steps.append((f"Tam kare! √(1 + f'²) = {_pp(ig)}", f"A perfect square! √(1 + f'²) = {_pp(ig)}"))
    else:
        steps.append((f"√(1 + f'²) = {_pp(ig)}", f"√(1 + f'²) = {_pp(ig)}"))
    num = _simp(S["hig"], S["a"], S["b"], 4000)
    F = _anti(ig, x, 60)
    val = None
    if F is not None:
        Fa, Fb = _at(F, x, A), _at(F, x, B)
        if Fa is not None and Fb is not None:
            val = sp.simplify(Fb - Fa)
            if not _same(val, num, 1e-4):
                val = None
    if val is not None:
        steps.append((f"Ters türev: F(x) = {_pp(F)}", f"Antiderivative: F(x) = {_pp(F)}"))
        steps.append((f"L = F({_pp(B)}) − F({_pp(A)}) = {_pp(Fb)} − {_par(_pp(Fa))} = {_exa(val)}",
                      f"L = F({_pp(B)}) − F({_pp(A)}) = {_pp(Fb)} − {_par(_pp(Fa))} = {_exa(val)}"))
        res = _exa(val)
    else:
        steps.append((f"Bu integralin temel bir ters türevi yok; Simpson ile: L ≈ {_g(num, 6)}",
                      f"No elementary antiderivative; Simpson's rule gives L ≈ {_g(num, 6)}"))
        res = _g(num, 6)
    approx = ", ".join(f"L{_sub(n)} ≈ {_poly_len(S, n)[0]:.4f}" for n in (1, 2, 4, 8, 16))
    steps.append((f"Çokgen yaklaşımı (n parça, Σ √(Δx² + Δy²)): {approx} → L",
                  f"Polyline check (n pieces, Σ √(Δx² + Δy²)): {approx} → L"))
    return {"answer": f"L = {res}", "steps": steps, "fmt": {"fx": _pp(S["f"]), "A": _pp(A), "B": _pp(B)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _setup(P)
    sol = solve(P)
    a, b = S["a"], S["b"]
    w = b - a
    xs = np.linspace(a, b, 400)
    ys = S["h"](xs)
    lo, hi = _ylim([ys], pad=0.18, zero=False)
    gs = fig.add_gridspec(1, 2, width_ratios=[2.6, 1], left=0.07, right=0.99, top=0.9, bottom=0.09, wspace=0.04)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    ax.set_xlim(a - 0.06 * w, b + 0.06 * w)
    ax.set_ylim(lo, hi + (hi - lo) * 0.3)
    ax.grid(alpha=0.3)
    if lo < 0 < hi:
        ax.axhline(0, color="#9CA3AF", lw=1)
    curve, = ax.plot([], [], color=BLUE, lw=3.0, alpha=0.8, label="y = " + sol["fmt"]["fx"])
    poly, = ax.plot([], [], "-", color=ORANGE, lw=2.0, zorder=4)
    verts, = ax.plot([], [], "o", color=ORANGE, ms=5, zorder=5)
    legx, = ax.plot([], [], color=GREEN, lw=2.2, zorder=6)
    legy, = ax.plot([], [], color=PURPLE, lw=2.2, zorder=6)
    tdx = ax.text(0, 0, "", color=GREEN, fontsize=11, ha="center", va="top", fontweight="bold", zorder=7)
    tdy = ax.text(0, 0, "", color=PURPLE, fontsize=11, ha="left", va="center", fontweight="bold", zorder=7)
    info = _box(ax, 10)
    tx.text(0.05, 0.97, ("Çokgen uzunlukları" if tr else "Polyline lengths"), fontsize=11, fontweight="bold",
            va="top", transform=tx.transAxes)
    table = tx.text(0.05, 0.89, "", transform=tx.transAxes, ha="left", va="top", fontsize=10.5,
                    linespacing=1.6, color="#9A3412")
    big = tx.text(0.05, 0.12, "", transform=tx.transAxes, ha="left", va="bottom", fontsize=13, wrap=True,
                  bbox=dict(boxstyle="round", fc="#ECFDF5", ec=GREEN))
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(("Yay uzunluğu: L = ∫ √(1 + (f')²) dx" if tr else "Arc length: L = ∫ √(1 + (f')²) dx"), fontsize=12)
    ns = [1, 2, 4, 8, 16, 32]
    lens = [_poly_len(S, n) for n in ns]
    i0, i1, N = 15, 111, 150
    L = (i1 - i0) / len(ns)

    def update(i):
        p = _ramp(i, 0, 14)
        m = max(2, int(p * len(xs)))
        curve.set_data(xs[:m], ys[:m])
        st = -1 if i < i0 else min(len(ns) - 1, int((i - i0) / L))
        if st >= 0:
            Ln, px, py = lens[st]
            poly.set_data(px, py)
            verts.set_data(px, py) if ns[st] <= 16 else verts.set_data([], [])
            rows = [f"n = {ns[k]}:   L{_sub(ns[k])} ≈ {lens[k][0]:.4f}" for k in range(st + 1)]
            table.set_text("\n".join(rows))
            info.set_text((f"{ns[st]} parça: Lₙ = Σ √(Δx² + Δy²) ≈ {Ln:.4f}" if tr else
                           f"{ns[st]} pieces: Lₙ = Σ √(Δx² + Δy²) ≈ {Ln:.4f}"))
        else:
            poly.set_data([], [])
            verts.set_data([], [])
            table.set_text("")
            info.set_text(("1) Eğriyi çiz: y = " if tr else "1) Draw the curve: y = ") + sol["fmt"]["fx"])
        if st == 2 and i < i1:
            _, px, py = lens[2]
            k = 1
            legx.set_data([px[k], px[k + 1]], [py[k], py[k]])
            legy.set_data([px[k + 1], px[k + 1]], [py[k], py[k + 1]])
            tdx.set_position(((px[k] + px[k + 1]) / 2, py[k] - 0.02 * (hi - lo)))
            tdx.set_text("Δx")
            tdy.set_position((px[k + 1] + 0.01 * w, (py[k] + py[k + 1]) / 2))
            tdy.set_text("Δy")
            info.set_text(info.get_text() + ("\nHer parça: ΔL = √(Δx² + Δy²) = √(1 + (Δy/Δx)²)·Δx" if tr else
                                             "\nEach piece: ΔL = √(Δx² + Δy²) = √(1 + (Δy/Δx)²)·Δx"))
        else:
            legx.set_data([], [])
            legy.set_data([], [])
            tdx.set_text("")
            tdy.set_text("")
        if i >= i1:
            info.set_text((f"n → ∞: Δy/Δx → f'(x)\n" if tr else "n → ∞: Δy/Δx → f'(x)\n") + sol["answer"])
            big.set_text(sol["answer"].replace(" ≈ ", "\n≈ "))
        else:
            big.set_text("")
        return []

    return N, update


def _vary1(P, rnd):
    f = str(P.get("f", ""))
    if "cosh" in f:
        c = rnd.choice([5, 10, 20])
        d = rnd.choice([c // 2, c])
        return {"f": f"{c}*cosh(x/{c})", "a": -d, "b": d}
    if "3/2" in f:
        a = rnd.choice([0, 0, 3])
        b = rnd.choice([v for v in (3, 8, 15) if v > a])
        return {"f": "2/3*x**(3/2)", "a": a, "b": b}
    if rnd.random() < 0.5:
        return {"f": "x**3/6 + 1/(2*x)", "a": 1, "b": rnd.choice([2, 3])}
    return {"f": "x**4/8 + 1/(4*x**2)", "a": 1, "b": rnd.choice([2, 3])}
''',
}
EXAMPLES += [
    {"id": "calc2-arc-1", "kind": "arc_length",
     "title": ("Yay uzunluğu: kesirli kuvvet", "Arc length: a fractional power"),
     "q": ("y = {fx} eğrisinin x = {A} ile x = {B} arasındaki yay uzunluğunu bul.",
           "Find the arc length of y = {fx} from x = {A} to x = {B}."),
     "P": {"f": "2/3*x**(3/2)", "a": 0, "b": 3}},
    {"id": "calc2-arc-2", "kind": "arc_length",
     "title": ("Tam kareye dönüşen integrand", "An integrand that becomes a perfect square"),
     "q": ("y = {fx} eğrisinin {A} ≤ x ≤ {B} aralığındaki uzunluğunu hesapla. (İpucu: 1 + (y')² bir tam karedir.)",
           "Compute the length of y = {fx} for {A} ≤ x ≤ {B}. (Hint: 1 + (y')² is a perfect square.)"),
     "P": {"f": "x**3/6 + 1/(2*x)", "a": 1, "b": 2}},
    {"id": "calc2-arc-3", "kind": "arc_length",
     "topics": ["word problem", "hanging cable", "sözel problem", "asılı kablo"],
     "title": ("Sözel problem: iki direk arasında asılı kablo", "Word problem: a cable hanging between poles"),
     "q": ("İki direk arasında asılı bir kablo y = {fx} (metre) eğrisini izliyor; direkler x = {A} ve x = {B} "
           "noktalarında. Kablonun uzunluğu kaç metredir?",
           "A cable hanging between two poles follows y = {fx} (metres); the poles stand at x = {A} and "
           "x = {B}. How long is the cable?"),
     "P": {"f": "10*cosh(x/10)", "a": -10, "b": 10}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["integration_by_parts"] = {
    "course": "calc2",
    "title": ("Kısmi integrasyon (tablo yöntemi)", "Integration by parts (tabular method)"),
    "topics": ["integration by parts", "by parts", "tabular integration", "tabular method", "liate",
               "integration techniques", "techniques of integration", "u dv", "kısmi integrasyon",
               "parçalı integrasyon", "tablo yöntemi", "integral teknikleri", "integrasyon yöntemleri"],
    "code": _H + r'''
from matplotlib.patches import FancyArrowPatch, Polygon

_RANK = (("L", "Logaritmik", "Logarithmic"), ("I", "Ters trigonometrik", "Inverse trig"),
         ("A", "Cebirsel", "Algebraic"), ("T", "Trigonometrik", "Trigonometric"), ("E", "Üstel", "Exponential"))


def _rank(e, x):
    if e.has(sp.log):
        return 0
    if e.has(sp.asin, sp.acos, sp.atan, sp.acot, sp.asec, sp.acsc):
        return 1
    if e.has(sp.sin, sp.cos, sp.tan, sp.sec, sp.csc, sp.cot):
        return 3
    if e.has(sp.exp) or (isinstance(e, sp.Pow) and not e.base.has(x)):
        return 4
    return 2


def _tab(f, x):
    c, rest = f.as_coeff_Mul()
    facs = list(sp.Mul.make_args(rest))
    ranks = [_rank(q, x) for q in facs]
    k = min(range(len(facs)), key=lambda j: (ranks[j], j))
    u = facs[k]
    dv = c * sp.Mul(*[q for j, q in enumerate(facs) if j != k])
    D, Iv = [u], [dv]
    G, mode, m, R, cyc, A = None, "fail", 0, None, None, None
    single = len(facs) == 1 and ranks[k] >= 2
    for step in range(0 if single else 6):
        nxt = _anti(Iv[-1], x, 40)
        if nxt is None:
            break
        Iv.append(sp.simplify(nxt))
        D.append(sp.simplify(sp.diff(D[-1], x)))
        m = len(D) - 1
        A = sum(((-1) ** j) * D[j] * Iv[j + 1] for j in range(m))
        if D[m] == 0:
            G, mode = A, "zero"
            break
        rem = sp.simplify(D[m] * Iv[m])
        if m >= 2:
            ratio = sp.simplify(rem / f)
            if not ratio.has(x) and ratio != 0 and (1 - ((-1) ** m) * ratio) != 0:
                cyc = ratio
                G, mode = A / (1 - ((-1) ** m) * ratio), "cyclic"
                break
        if ranks[k] <= 1 or step == 5:
            Rr = _anti(rem, x, 60)
            if Rr is not None:
                R = Rr
                G, mode = A + ((-1) ** m) * Rr, "rest"
                break
    ok = False
    if G is not None:
        try:
            chk = _num(sp.diff(G, x) - f, x)(np.array([0.37, 0.81, 1.23, 1.77]))
            fin = chk[np.isfinite(chk)]
            ok = len(fin) > 0 and float(np.max(np.abs(fin))) < 1e-7
        except Exception:
            ok = False
    if not ok:
        G = _anti(f, x, 80)
        mode = ("direct" if single else "sympy") if G is not None else "fail"
    return {"u": u, "dv": dv, "ranku": ranks[k], "rankv": _rank(dv, x), "D": D, "I": Iv, "m": m,
            "G": G, "mode": mode, "R": R, "cyc": cyc, "A": A}


def _setup(P):
    x, f = _parse(P.get("f", "x*exp(x)"), "x", "x*exp(x)")
    A, af = _pv(P.get("a", 0), 0)
    B, bf = _pv(P.get("b", 1), 1)
    if bf < af:
        A, af, B, bf = B, bf, A, af
    if bf - af < 1e-9:
        B, bf = A + 1, af + 1
    T = _tab(f, x)
    return {"x": x, "f": f, "A": A, "B": B, "a": af, "b": bf, "T": T, "h": _num(f, x)}


def _nice_G(G, x):
    try:
        cands = [sp.factor(G), sp.expand(G), sp.collect(sp.expand(G), [sp.exp(x)] if G.has(sp.exp) else [])]
        cands = [c for c in cands if c is not None]
        return min(cands, key=lambda c: (len(sp.sstr(c)) + (2 if sp.sstr(c).count("(-") else 0), cands.index(c)))
    except Exception:
        return G


def solve(P):
    S = _setup(P)
    x, f, T = S["x"], S["f"], S["T"]
    tr = P.get("lang", "tr") == "tr"
    fs = _pp(f)
    I = _I(_pp(S["A"]), _pp(S["B"]))
    ru, rv = _RANK[T["ranku"]], _RANK[T["rankv"]]
    dvs = "dx" if T["dv"] == 1 else f"{_pp(T['dv'])} dx"
    steps = [(f"LIATE sırası (Logaritmik, Ters trig., Cebirsel, Trig., Üstel) ⇒ u = {_pp(T['u'])} ({ru[1]}), "
              f"dv = {dvs} ({rv[1]})",
              f"LIATE order (Log, Inverse trig, Algebraic, Trig, Exponential) ⇒ u = {_pp(T['u'])} ({ru[2]}), "
              f"dv = {dvs} ({rv[2]})")]
    if T["m"] >= 1:
        d1 = T["D"][1]
        du = "dx" if d1 == 1 else f"{_pp(d1)} dx"
        vdu = _pp(sp.simplify(T["I"][1] * d1))
        steps.append((f"du = {du},  v = {_pp(T['I'][1])}", f"du = {du},  v = {_pp(T['I'][1])}"))
        steps.append((f"∫ u dv = uv − ∫ v du = {_par(_pp(T['u']))}·{_par(_pp(T['I'][1]))} − ∫ {vdu} dx",
                      f"∫ u dv = uv − ∫ v du = {_par(_pp(T['u']))}·{_par(_pp(T['I'][1]))} − ∫ {vdu} dx"))
    if T["mode"] in ("zero", "cyclic", "rest") and T["m"] >= 2 or T["mode"] == "zero":
        rows = "; ".join(f"({'+' if j % 2 == 0 else '−'}) {_pp(T['D'][j])} ↘ {_pp(T['I'][j + 1])}" for j in range(T["m"]))
        steps.append((f"Tablo (D sütunu türev, I sütunu integral): {rows}", f"Tabular (D: derivatives, I: integrals): {rows}"))
    if T["mode"] == "cyclic":
        kk = sp.nsimplify(((-1) ** T["m"]) * T["cyc"])
        As = _pp(sp.expand(T["A"]))
        coef = "" if abs(kk) == 1 else _pp(abs(kk)) + "·"
        eq = f"I = {As} {'−' if kk < 0 else '+'} {coef}I  ⇒  {_pp(1 - kk)}·I = {As}"
        steps.append((f"Aynı integral (I) geri geldi: {eq}", f"The same integral I came back: {eq}"))
    elif T["mode"] == "rest" and T["R"] is not None:
        rem = sp.simplify(T["D"][T["m"]] * T["I"][T["m"]])
        steps.append((f"Kalan integral doğrudan alınır: ∫ {_pp(rem)} dx = {_pp(T['R'])}",
                      f"The remaining integral is direct: ∫ {_pp(rem)} dx = {_pp(T['R'])}"))
    elif T["mode"] == "sympy":
        steps.append(("Tablo kısa kesildi; ters türev sembolik olarak (sympy) bulundu.",
                      "The table was cut short; the antiderivative was found symbolically (sympy)."))
    elif T["mode"] == "direct":
        steps.append(("Tek çarpan var ve doğrudan integrallenebiliyor: kısmi integrasyona gerek yok.",
                      "There is a single factor that integrates directly: no need for integration by parts."))
    num = _simp(S["h"], S["a"], S["b"], 4000)
    G = T["G"]
    val = None
    if G is not None:
        Gn = _nice_G(G, x)
        steps.append((f"∫ {fs} dx = {_pp(Gn)} + C", f"∫ {fs} dx = {_pp(Gn)} + C"))
        Ga, Gb = _at(G, x, S["A"]), _at(G, x, S["B"])
        if Ga is not None and Gb is not None:
            val = sp.simplify(Gb - Ga)
            if not _same(val, num, 1e-4):
                val = None
            else:
                steps.append((f"{I} {fs} dx = G({_pp(S['B'])}) − G({_pp(S['A'])}) = {_pp(sp.simplify(Gb))} − {_par(_pp(sp.simplify(Ga)))} = {_exa(val)}",
                              f"{I} {fs} dx = G({_pp(S['B'])}) − G({_pp(S['A'])}) = {_pp(sp.simplify(Gb))} − {_par(_pp(sp.simplify(Ga)))} = {_exa(val)}"))
    res = _exa(val) if val is not None else _g(num, 6)
    if val is None:
        steps.append((f"Sayısal değer: {I} {fs} dx ≈ {_g(num, 6)}", f"Numerical value: {I} {fs} dx ≈ {_g(num, 6)}"))
    steps.append((f"Grafikte: f'nin [{_pp(S['A'])}, {_pp(S['B'])}] üzerindeki işaretli alanı = {res}",
                  f"On the graph: the signed area under f on [{_pp(S['A'])}, {_pp(S['B'])}] = {res}"))
    return {"answer": f"{I} {fs} dx = {res}", "steps": steps,
            "fmt": {"fx": fs, "A": _pp(S["A"]), "B": _pp(S["B"])}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _setup(P)
    sol = solve(P)
    T, x = S["T"], S["x"]
    a, b = S["a"], S["b"]
    w = b - a
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.25], left=0.02, right=0.98, top=0.9, bottom=0.1, wspace=0.12)
    tx = fig.add_subplot(gs[0, 0])
    tx.axis("off")
    ax = fig.add_subplot(gs[0, 1])
    xs = np.linspace(a - 0.12 * w, b + 0.12 * w, 400)
    ys = S["h"](xs)
    lo, hi = _ylim([ys], pad=0.15)
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(lo, hi + (hi - lo) * 0.3)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#9CA3AF", lw=1)
    curve, = ax.plot([], [], color=BLUE, lw=2.4, label="f(x) = " + sol["fmt"]["fx"])
    xr = np.linspace(a, b, 301)
    yr = S["h"](xr)
    yr = np.where(np.isfinite(yr), yr, 0.0)
    cum = _cum(xr, yr)
    pos = Polygon(np.zeros((3, 2)), closed=True, fc=GREEN, alpha=0.35, ec="none")
    neg = Polygon(np.zeros((3, 2)), closed=True, fc=RED, alpha=0.3, ec="none")
    ax.add_patch(pos)
    ax.add_patch(neg)
    sweep, = ax.plot([], [], color=PURPLE, lw=1.6)
    info = _box(ax, 10)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(("Belirli integral = işaretli alan" if tr else "Definite integral = signed area"), fontsize=11)
    tx.set_xlim(0, 1)
    tx.set_ylim(0, 1)
    tx.text(0.0, 0.98, ("Tablo yöntemi" if tr else "Tabular method"), fontsize=12, fontweight="bold", va="top")
    tx.text(0.0, 0.91, ("u = " + _pp(T["u"]) + ",   dv = " + ("dx" if T["dv"] == 1 else _pp(T["dv"]) + " dx")),
            fontsize=10, va="top", color="#374151")
    heads = [tx.text(0.02, 0.82, ("işaret" if tr else "sign"), fontsize=9, color=GRAY),
             tx.text(0.17, 0.82, ("D (türev)" if tr else "D (derivative)"), fontsize=10, fontweight="bold", color=BLUE),
             tx.text(0.62, 0.82, ("I (integral)" if tr else "I (integral)"), fontsize=10, fontweight="bold", color=ORANGE)]
    nrow = len(T["D"])
    dy = min(0.12, 0.56 / max(1, nrow))
    ys_ = [0.74 - k * dy for k in range(nrow)]
    cells = []
    for k in range(nrow):
        sg = tx.text(0.05, ys_[k], "+" if k % 2 == 0 else "−", fontsize=13, color=RED, ha="center", va="center", alpha=0)
        dt = tx.text(0.17, ys_[k], _pp(T["D"][k]), fontsize=12, color=BLUE, va="center", alpha=0)
        it = tx.text(0.62, ys_[k], (_pp(T["I"][k]) if k < len(T["I"]) else ""), fontsize=12, color=ORANGE,
                     va="center", alpha=0)
        cells.append((sg, dt, it))
    arrows = []
    for k in range(nrow - 1):
        ar = FancyArrowPatch((0.40, ys_[k] - 0.01), (0.6, ys_[k + 1] + 0.015), arrowstyle="-|>", mutation_scale=12,
                             color=GRAY, lw=1.2, alpha=0.0)
        tx.add_patch(ar)
        arrows.append(ar)
    last = None
    if T["mode"] in ("rest", "cyclic") and nrow >= 2:
        last = FancyArrowPatch((0.40, ys_[-1]), (0.6, ys_[-1]), arrowstyle="-|>", mutation_scale=12, color=PURPLE,
                               lw=1.4, alpha=0.0)
        tx.add_patch(last)
    lastlab = tx.text(0.5, ys_[-1] + 0.02, "", fontsize=9, color=PURPLE, ha="center")
    Gtxt = tx.text(0.0, 0.08, "", fontsize=10.5, va="bottom", linespacing=1.5,
                   bbox=dict(boxstyle="round", fc="#EFF6FF", ec=BLUE))
    Gs = _pp(_nice_G(T["G"], x)) if T["G"] is not None else "?"
    N = 160
    rstep = 60 / max(1, nrow)

    def update(i):
        p = _ramp(i, 0, 14)
        m = max(2, int(p * len(xs)))
        curve.set_data(xs[:m], ys[:m])
        shown = 0 if i < 12 else min(nrow, 1 + int((i - 12) / rstep))
        for k, (sg, dt, it) in enumerate(cells):
            al = 1.0 if k < shown else 0.0
            sg.set_alpha(al)
            dt.set_alpha(al)
            it.set_alpha(al)
        for k, ar in enumerate(arrows):
            ar.set_alpha(1.0 if k + 1 < shown else 0.0)
        if last is not None:
            last.set_alpha(1.0 if shown >= nrow and i >= 74 else 0.0)
            lastlab.set_text((("∫ (kalan)" if tr else "∫ (rest)") if T["mode"] == "rest" else
                              ("= I tekrar" if tr else "= I again")) if (shown >= nrow and i >= 74) else "")
        Gtxt.set_text((("∫ f dx = " + Gs + " + C") + (("\n" + sol["answer"]) if i >= 142 else "")) if i >= 80 else "")
        s = _ramp(i, 95, 140)
        j = int(round(s * (len(xr) - 1)))
        if i >= 95:
            xx, yy = xr[:j + 1], yr[:j + 1]
            pp_ = np.concatenate([np.column_stack([xx, np.maximum(yy, 0)]), [[xx[-1], 0.0], [xx[0], 0.0]]])
            nn_ = np.concatenate([np.column_stack([xx, np.minimum(yy, 0)]), [[xx[-1], 0.0], [xx[0], 0.0]]])
            pos.set_xy(pp_)
            neg.set_xy(nn_)
            sweep.set_data([xr[j], xr[j]], [0, yr[j]])
        else:
            pos.set_xy(np.zeros((3, 2)))
            neg.set_xy(np.zeros((3, 2)))
            sweep.set_data([], [])
        if i < 12:
            info.set_text(("1) f(x) ve sınırlar" if tr else "1) f(x) and the limits"))
        elif i < 80:
            info.set_text(("2) D sütununu türetip I sütununu\n   integralleyerek tabloyu doldur" if tr else
                           "2) Differentiate down D and\n   integrate down I"))
        elif i < 95:
            info.set_text(("3) Çapraz çarpımları işaretleriyle topla" if tr else "3) Add the diagonal products with signs"))
        elif i < 142:
            info.set_text((f"4) ∫ₐˣ f dt ≈ {cum[j]:.4f}  (x = {xr[j]:.2f})" if tr else
                           f"4) ∫ₐˣ f dt ≈ {cum[j]:.4f}  (x = {xr[j]:.2f})"))
        else:
            info.set_text("5) = " + sol["answer"].split(" = ")[-1])
        return []

    return N, update


def _vary1(P, rnd):
    f = str(P.get("f", ""))
    if "exp(-" in f:
        k = rnd.choice([2, 3, 4])
        return {"f": f"x*exp(-x/{k})", "a": 0, "b": rnd.choice([k, 2 * k, 3 * k])}
    fam = [("x*exp(x)", 0, 1), ("x*exp(2*x)", 0, 1), ("x*sin(x)", 0, "pi"), ("x*cos(x)", 0, "pi/2"),
           ("x**2*exp(x)", 0, 1), ("x*log(x)", 1, "e"), ("x**2*log(x)", 1, "e"), ("log(x)", 1, "e"),
           ("x**2*cos(x)", 0, "pi/2"), ("x**2*sin(x)", 0, "pi"), ("exp(x)*sin(x)", 0, "pi"), ("x**3*exp(x)", 0, 1)]
    g, a, b = rnd.choice(fam)
    return {"f": g, "a": a, "b": b}
''',
}
EXAMPLES += [
    {"id": "calc2-ibp-1", "kind": "integration_by_parts",
     "title": ("Kısmi integrasyon: x·eˣ", "Integration by parts: x·eˣ"),
     "q": ("Kısmi integrasyonla hesapla:  ∫ {fx} dx,  x = {A} ile x = {B} arasında.",
           "Use integration by parts to evaluate  ∫ {fx} dx  from x = {A} to x = {B}."),
     "P": {"f": "x*exp(x)", "a": 0, "b": 1}},
    {"id": "calc2-ibp-2", "kind": "integration_by_parts",
     "title": ("Tablo yöntemi: x²·sin x", "Tabular method: x²·sin x"),
     "q": ("Tablo (tabular) yöntemini kullanarak ∫ {fx} dx belirli integralini [{A}, {B}] aralığında hesapla.",
           "Use the tabular method to evaluate the definite integral of {fx} over [{A}, {B}]."),
     "P": {"f": "x**2*sin(x)", "a": 0, "b": "pi"}},
    {"id": "calc2-ibp-3", "kind": "integration_by_parts",
     "topics": ["word problem", "drug concentration", "sözel problem", "ilaç", "area under curve"],
     "title": ("Sözel problem: kandaki ilaç miktarı", "Word problem: drug in the bloodstream"),
     "q": ("Bir ilacın kandaki derişimi C(x) = {fx} (mg/L, x saat). İlk {B} saatteki toplam etki "
           "∫ C(x) dx (x = {A} ile {B} arası) ile ölçülüyor. Bu değeri kısmi integrasyonla bul.",
           "A drug's blood concentration is C(x) = {fx} (mg/L, x in hours). The total exposure over the "
           "first {B} hours is ∫ C(x) dx from x = {A} to {B}. Find it with integration by parts."),
     "P": {"f": "x*exp(-x/2)", "a": 0, "b": 4}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["improper_integral"] = {
    "course": "calc2",
    "title": ("Genelleştirilmiş (has olmayan) integral", "Improper integral"),
    "topics": ["improper integral", "improper integrals", "infinite limits of integration", "convergent integral",
               "divergent integral", "p-integral", "comparison test", "has olmayan integral",
               "genelleştirilmiş integral", "sonsuz sınırlı integral", "yakınsak integral", "ıraksak integral"],
    "code": _H + r'''
from matplotlib.patches import Polygon


def _setup(P):
    x, f = _parse(P.get("f", "1/x**2"), "x", "1/x**2")
    A, af = _pv(P.get("a", 1), 1)
    return {"x": x, "f": f, "A": A, "a": af, "h": _num(f, x)}


def _limit(S):
    x, f, A = S["x"], S["f"], S["A"]
    t = sp.Symbol("t", positive=True)
    F = _anti(f, x)
    It = L = None
    if F is not None:
        Fa = _at(F, x, A)
        if Fa is None:
            try:
                La = sp.limit(F, x, A, "+")
                if La in (sp.oo, -sp.oo):
                    return F, None, La, t, "div_a"
            except Exception:
                pass
        if Fa is not None:
            try:
                raw = F.subs(x, t) - Fa
                It = min([sp.simplify(raw), sp.expand(raw)], key=lambda e: len(sp.sstr(e)))
                L = sp.limit(It, t, sp.oo)
            except Exception:
                It = L = None
    status = None
    if L is not None:
        if L.is_number and L.is_finite and L.is_real:
            status = "conv"
        elif L in (sp.oo, -sp.oo):
            status = "div"
        else:
            status = "osc"
    return F, It, L, t, status


def _numeric(S):
    a, h = S["a"], S["h"]
    edges = [a, a + 10, a + 100, a + 1000, a + 10000]
    vals, acc = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        acc += _simp(h, lo, hi, 6000)
        vals.append(acc)
    return edges[1:], vals


def _ptest(S):
    x, f = S["x"], S["f"]
    c, rest = f.as_coeff_Mul()
    if isinstance(rest, sp.Pow) and rest.base == x and rest.exp.is_number and rest.exp < 0:
        return -rest.exp
    return None


def solve(P):
    S = _setup(P)
    x, f, A = S["x"], S["f"], S["A"]
    tr = P.get("lang", "tr") == "tr"
    F, It, L, t, status = _limit(S)
    fs, As = _pp(f), _pp(A)
    I0 = _I(As, "∞")
    steps = [(f"Tanım: {I0} {fs} dx = lim(t→∞) {_I(As, 't')} {fs} dx",
              f"Definition: {I0} {fs} dx = lim(t→∞) {_I(As, 't')} {fs} dx")]
    if status == "div_a":
        steps.append((f"Ters türev: F(x) = {_pp(F)}", f"Antiderivative: F(x) = {_pp(F)}"))
        steps.append((f"f, x = {As} noktasında sınırsız: lim(x→{As}⁺) F(x) = {_pp(L)} ⇒ alt uçta da genelleştirilmiş, ıraksak",
                      f"f is unbounded at x = {As}: lim(x→{As}⁺) F(x) = {_pp(L)} ⇒ improper at the lower end too, divergent"))
        ans = (f"Iraksak (x = {As} noktasında sonsuz alan)" if tr else f"Diverges (infinite area at x = {As})")
    elif status is not None:
        steps.append((f"Ters türev: F(x) = {_pp(F)}", f"Antiderivative: F(x) = {_pp(F)}"))
        steps.append((f"{_I(As, 't')} {fs} dx = F(t) − F({As}) = {_pp(It)}",
                      f"{_I(As, 't')} {fs} dx = F(t) − F({As}) = {_pp(It)}"))
        if status == "conv":
            steps.append((f"lim(t→∞) [{_pp(It)}] = {_exa(L)}  ⇒  integral yakınsak",
                          f"lim(t→∞) [{_pp(It)}] = {_exa(L)}  ⇒  the integral converges"))
            ans = (f"Yakınsak: {I0} {fs} dx = {_exa(L)}" if tr else f"Converges: {I0} {fs} dx = {_exa(L)}")
        elif status == "div":
            steps.append((f"lim(t→∞) [{_pp(It)}] = {_pp(L)}  ⇒  integral ıraksak",
                          f"lim(t→∞) [{_pp(It)}] = {_pp(L)}  ⇒  the integral diverges"))
            ans = (f"Iraksak ({I0} {fs} dx = {_pp(L)})" if tr else f"Diverges ({I0} {fs} dx = {_pp(L)})")
        else:
            steps.append((f"lim(t→∞) [{_pp(It)}] mevcut değil (salınım) ⇒ integral ıraksak",
                          f"lim(t→∞) [{_pp(It)}] does not exist (oscillates) ⇒ the integral diverges"))
            ans = "Iraksak (limit yok)" if tr else "Diverges (no limit)"
    else:
        ts, vals = _numeric(S)
        tab = ", ".join(f"t = {_g(tv, 6)}: {v:.5g}" for tv, v in zip(ts, vals))
        steps.append((f"Temel ters türev bulunamadı; sayısal değerler: {tab}",
                      f"No elementary antiderivative; numerical values: {tab}"))
        d1, d2 = abs(vals[-1] - vals[-2]), abs(vals[-2] - vals[-3])
        if d1 < 1e-3 * (1 + abs(vals[-1])) and d1 <= d2:
            steps.append((f"Değerler durgunlaşıyor ⇒ büyük olasılıkla yakınsak, ≈ {vals[-1]:.5g}",
                          f"The values level off ⇒ most likely convergent, ≈ {vals[-1]:.5g}"))
            ans = (f"Yakınsak (≈ {vals[-1]:.5g})" if tr else f"Converges (≈ {vals[-1]:.5g})")
        else:
            steps.append(("Değerler büyümeyi sürdürüyor ⇒ ıraksak görünüyor", "The values keep growing ⇒ it looks divergent"))
            ans = "Iraksak" if tr else "Diverges"
    p = _ptest(S)
    if p is not None and S["a"] > 0:
        ps = _pp(p)
        steps.append(((f"p-testi: {I0} dx/xᵖ yakınsar ⇔ p > 1;  burada p = {ps} " + ("> 1 ✓" if p > 1 else "≤ 1 ⇒ ıraksak")),
                      (f"p-test: {I0} dx/xᵖ converges ⇔ p > 1;  here p = {ps} " + ("> 1 ✓" if p > 1 else "≤ 1 ⇒ diverges"))))
    return {"answer": ans, "steps": steps, "fmt": {"fx": fs, "A": As}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _setup(P)
    sol = solve(P)
    F, It, L, t, status = _limit(S)
    a, h = S["a"], S["h"]
    Lf = float(sp.N(L)) if status == "conv" else None
    span = 1500.0
    if Lf is not None:
        g = a + np.logspace(-3, 3.3, 900)
        cg = _cum(np.concatenate([[a], g]), h(np.concatenate([[a], g])))[1:]
        close = np.nonzero(np.abs(cg - Lf) < 0.004 * max(abs(Lf), 1e-9))[0]
        if len(close):
            span = float(min(max(g[close[0]] - a, 6.0), 1500.0))
    R = max(3.0, min(400.0, span))
    u = np.linspace(0, 1, 1600)
    tg = a + span * (R ** u - 1) / (R - 1)
    yg = h(tg)
    yg = np.where(np.isfinite(yg), yg, np.nan)
    Ig = None
    if It is not None:
        try:
            Ig = _num(It, t)(tg)
            if not np.all(np.isfinite(Ig)):
                Ig = None
        except Exception:
            Ig = None
    if Ig is None:
        Ig = _cum(tg, np.where(np.isfinite(yg), yg, 0.0))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.25, 1], left=0.09, right=0.97, top=0.92, bottom=0.08, hspace=0.3)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[1, 0])
    near = yg[tg <= a + 4]
    lo, hi = _ylim([near], pad=0.12)
    ax.set_ylim(lo, hi + (hi - lo) * 0.35)
    lo2, hi2 = _ylim([Ig] + ([np.array([Lf])] if Lf is not None else []), pad=0.12, pct=0)
    bx.set_ylim(lo2, hi2 + (hi2 - lo2) * 0.3)
    for axx in (ax, bx):
        axx.grid(alpha=0.3)
        axx.axhline(0, color="#9CA3AF", lw=1)
    curve, = ax.plot(tg, yg, color=BLUE, lw=2.3, label="f(x) = " + sol["fmt"]["fx"])
    fill = Polygon(np.zeros((3, 2)), closed=True, fc=GREEN, alpha=0.35, ec="none")
    ax.add_patch(fill)
    tl, = ax.plot([], [], color=PURPLE, lw=1.6)
    tlab = ax.text(0, 0, "", color=PURPLE, fontsize=10, ha="left", va="bottom")
    info = _box(ax, 10)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(("Alan a'dan t'ye; t → ∞" if tr else "Area from a to t; t → ∞"), fontsize=11, loc="left")
    Icur, = bx.plot([], [], color=ORANGE, lw=2.2)
    Idot, = bx.plot([], [], "o", color=RED, ms=7)
    limln, = bx.plot([], [], "--", color=GREEN, lw=1.8)
    limtx = bx.text(0, 0, "", color=GREEN, fontsize=11, fontweight="bold", va="bottom", ha="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=GREEN, alpha=0.9))
    bx.set_title(("I(t) = ∫ₐᵗ f(x) dx" if tr else "I(t) = ∫ₐᵗ f(x) dx"), fontsize=10, loc="left")
    bx.set_xlabel("t")
    verdict = bx.text(0.02, 0.92, "", transform=bx.transAxes, va="top", fontsize=11, fontweight="bold",
                      bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    i0, i1, N = 15, 125, 155

    def update(i):
        s = _ramp(i, i0, i1)
        j = int(round(s * (len(tg) - 1)))
        tc = tg[j]
        xmax = a + max(4.0, 1.15 * (tc - a))
        ax.set_xlim(a - 0.03 * (xmax - a), xmax)
        bx.set_xlim(a - 0.03 * (xmax - a), xmax)
        if i >= i0:
            yy = np.where(np.isfinite(yg[:j + 1]), yg[:j + 1], 0.0)
            pts = np.concatenate([np.column_stack([tg[:j + 1], yy]), [[tc, 0.0], [a, 0.0]]])
            fill.set_xy(pts)
            tl.set_data([tc, tc], [0, yy[-1]])
            tlab.set_position((tc, max(yy[-1], 0) + 0.03 * (hi - lo)))
            tlab.set_text(f" t = {_g(tc, 4)}")
            Icur.set_data(tg[:j + 1], Ig[:j + 1])
            Idot.set_data([tc], [Ig[j]])
            info.set_text((f"t = {_g(tc, 4)}:  ∫ₐᵗ f dx = {Ig[j]:.5g}" if tr else f"t = {_g(tc, 4)}:  ∫ₐᵗ f dx = {Ig[j]:.5g}"))
        else:
            fill.set_xy(np.zeros((3, 2)))
            tl.set_data([], [])
            tlab.set_text("")
            Icur.set_data([], [])
            Idot.set_data([], [])
            info.set_text("f(x) = " + sol["fmt"]["fx"] + (",  a = " + sol["fmt"]["A"]))
        if i >= i1 + 3:
            if Lf is not None:
                limln.set_data([a - span, a + 2 * span], [Lf, Lf])
                limtx.set_position((a + 0.6 * (xmax - a), Lf + 0.06 * (hi2 - lo2)))
                limtx.set_text(f"I(t) → {_g(Lf, 5)}")
            verdict.set_text(sol["answer"])
            verdict.set_color(GREEN if Lf is not None else RED)
        else:
            limln.set_data([], [])
            limtx.set_text("")
            verdict.set_text("")
        return []

    return N, update


def _vary1(P, rnd):
    f = str(P.get("f", ""))
    if "exp" in f:
        c, k = rnd.choice([10, 50, 100, 200]), rnd.choice([2, 4, 5, 10])
        return {"f": f"{c}*exp(-x/{k})", "a": 0}
    p0 = _ptest(_setup(P))
    p = rnd.choice([1, 1, "1/2"]) if (p0 is not None and p0 <= 1) else rnd.choice([2, 3, 4])
    c = rnd.choice([1, 2, 3, 4])
    if p == "1/2":
        return {"f": f"{c}/sqrt(x)" if c > 1 else "1/sqrt(x)", "a": rnd.choice([1, 4, 9])}
    num = "" if c == 1 else f"{c}"
    expr = (f"{num}/x**{p}" if num else f"1/x**{p}") if p != 1 else (f"{num}/x" if num else "1/x")
    return {"f": expr, "a": rnd.choice([1, 2, 3])}
''',
}
EXAMPLES += [
    {"id": "calc2-improper-1", "kind": "improper_integral",
     "title": ("Yakınsak genelleştirilmiş integral", "A convergent improper integral"),
     "q": ("Alt sınırı x = {A}, üst sınırı ∞ olan ∫ {fx} dx integralini hesapla. Yakınsak mı?",
           "Evaluate the integral of {fx} from x = {A} to ∞. Does it converge?"),
     "P": {"f": "1/x**2", "a": 1}},
    {"id": "calc2-improper-2", "kind": "improper_integral",
     "topics": ["harmonic", "divergent"],
     "title": ("Iraksak örnek: 1/x altındaki alan", "Divergent example: the area under 1/x"),
     "q": ("y = {fx} eğrisinin altında, x = {A} noktasından sağa doğru sonsuza uzanan bölgenin alanı sonlu mu?",
           "Is the area under y = {fx}, stretching from x = {A} to the right forever, finite?"),
     "P": {"f": "1/x", "a": 1}},
    {"id": "calc2-improper-3", "kind": "improper_integral",
     "topics": ["word problem", "sözel problem", "total production", "toplam üretim"],
     "title": ("Sözel problem: bir petrol kuyusunun toplam üretimi", "Word problem: an oil well's total output"),
     "q": ("Bir petrol kuyusu x yıl sonra yılda r(x) = {fx} bin varil üretiyor. Kuyu sonsuza dek çalışsaydı "
           "x = {A} anından itibaren toplam üretim ne olurdu?",
           "An oil well produces r(x) = {fx} thousand barrels per year after x years. If it ran forever, "
           "what would its total output from x = {A} be?"),
     "P": {"f": "100*exp(-x/2)", "a": 0}},
]
