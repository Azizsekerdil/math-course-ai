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
_NAMES = {"pi": "π", "E": "e", "oo": "∞", "theta": "θ", "log": "ln", "I": "i"}
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
                    out.append("e" + _sup(inner) if ok else "e^(" + inner + ")")
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
                out.append("^")
                i = j
                continue
            prev = out[-1][-1:] if out else ""
            nxt = s[i + 1:i + 2]
            if prev.isdigit() and (nxt.isalpha() or nxt == "("):
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
            e = sp.Rational(str(v)) if abs(v) < 1e9 else sp.Float(v)
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


def _ylim(arrs, pad=0.12, zero=True):
    vals = [np.asarray(a, dtype=float).ravel() for a in arrs]
    vals = np.concatenate(vals) if vals else np.array([])
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return -1.0, 1.0
    lo, hi = float(np.percentile(vals, 1)), float(np.percentile(vals, 99))
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
        res = _ex(total_ex)
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


def vary(P, rnd):
    if "a" in P and "b" in P:
        if "x**3" in str(P.get("f", "")) or "x**3" in str(P.get("g", "")):
            k = rnd.choice([1, 2])
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


def vary(P, rnd):
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
