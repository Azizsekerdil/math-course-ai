# -*- coding: utf-8 -*-
"""Diferansiyel denklem simülasyonları: eğim alanı, üstel büyüme/azalma,
Newton soğuma yasası, lojistik büyüme, kütle-yay sistemi, Euler yöntemi,
av-avcı (Lotka-Volterra) modeli, karışım tankı ve sabit katsayılı ikinci
mertebe homojen denklemler.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Ortak yardımcılar
(_FMT, _ODE_CORE, _SECOND) kaynak metnin başına eklenir, böylece her şablon
yine tek parça ve bağımsızdır. Sorular kurs kitaplarından KOPYALANMAZ: kendi
ifademizle yazılmış, sayıları değiştirilmiş tipik ders örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
# Ortak yardımcı kaynaklar (her şablonun başına eklenir)
# ──────────────────────────────────────────────────────────────────────────
_FMT = r'''
import math
import numpy as np


def _n(v, dec=2):
    v = float(v)
    if not math.isfinite(v):
        return "∞" if v > 0 else ("-∞" if v < 0 else "—")
    if abs(v - round(v)) < 1e-9 * max(1.0, abs(v)):
        s = str(int(round(v)))
    elif abs(v) >= 1:
        s = f"{v:.{dec}f}".rstrip("0").rstrip(".")
    else:
        s = f"{v:.{max(3, dec)}g}"
    return "0" if s in ("-0", "") else s


def _ramp(i, a, b):
    if b <= a:
        return 1.0 if i >= a else 0.0
    return min(1.0, max(0.0, (i - a) / float(b - a)))


def _box(ax, x=0.02, y=0.97, size=11, ha="left"):
    return ax.text(x, y, "", transform=ax.transAxes, va="top", ha=ha, fontsize=size, zorder=30,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB", alpha=0.95))


def _banner(fig, size=10.5):
    return fig.text(0.012, 0.985, "", va="top", ha="left", fontsize=size, zorder=30,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))


def _affine(c0, c1, body, dec=4):
    # "c0 + c1·body" with clean signs (no "+ (-3)·...", no "0 + ...")
    s1 = _n(abs(c1), dec)
    term = body if s1 == "1" else f"{s1}·{body}"
    if abs(c0) < 1e-12:
        return ("−" if c1 < 0 else "") + term
    return f"{_n(c0, dec)} {'−' if c1 < 0 else '+'} {term}"


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[k:k + 2], 16) / 255.0 for k in (0, 2, 4))


def _mix(c1, c2, u):
    u = min(1.0, max(0.0, float(u)))
    a, b = _rgb(c1), _rgb(c2)
    return tuple((1 - u) * p + u * q for p, q in zip(a, b))
'''

# y' = f(x, y): sağlam ayrıştırıcı + sayısal (RK4) + güvenli kapalı form arama
_ODE_CORE = r'''
import sympy as sp
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application, convert_xor)
from matplotlib.collections import LineCollection

_X = sp.Symbol("x", real=True)
_Y = sp.Symbol("y", real=True)
_D = sp.Symbol("yprime")
_CACHE = {}


def _num(v, default):
    if v is None or v == "":
        return float(default)
    try:
        return float(v)
    except Exception:
        pass
    try:
        return float(sp.sympify(str(v).replace("^", "**").replace("−", "-")))
    except Exception:
        return float(default)


def _pretty(e):
    s = sp.sstr(e).replace("**", "^").replace("*", "·").replace("sqrt", "√").replace("log(", "ln(")
    s = s.replace("exp(", "e^(")
    out = []
    for k, ch in enumerate(s):
        prev = s[k - 1] if k > 0 else " "
        nxt = s[k + 1] if k + 1 < len(s) else " "
        out.append("e" if (ch == "E" and not prev.isalnum() and not nxt.isalnum()) else ch)
    return "".join(out)


def _clean(raw):
    s = str(raw).strip()
    pairs = (("−", "-"), ("–", "-"), ("—", "-"), ("·", "*"), ("×", "*"), ("÷", "/"),
             ("²", "**2"), ("³", "**3"), ("′", "'"), ("’", "'"), ("{", "("), ("}", ")"),
             ("[", "("), ("]", ")"), ("π", "pi"), ("√", "sqrt"), ("^", "**"))
    for a, b in pairs:
        s = s.replace(a, b)
    for a in ("y(x)", "y(t)", "y (x)", "y (t)"):
        s = s.replace(a, "y")
    for a in ("dy/dx", "dy/dt", "dy / dx", "dy / dt", "y'"):
        s = s.replace(a, " yprime ")
    return s.strip()


def _loc():
    return {"x": _X, "y": _Y, "t": _X, "e": sp.E, "E": sp.E, "pi": sp.pi, "ln": sp.log,
            "yprime": _D}


def _parse_part(s):
    s = s.strip()
    if not s:
        return sp.Integer(0)
    try:
        return sp.sympify(s, locals=_loc())
    except Exception:
        pass
    trs = standard_transformations + (implicit_multiplication_application, convert_xor)
    return parse_expr(s, local_dict=_loc(), transformations=trs)


def _parse_f(raw):
    try:
        return _parse_f0(raw)
    except ValueError:
        raise
    except Exception:
        raise ValueError("y' = f(x, y) ifadesi okunamadı / could not read y' = f(x, y): " + str(raw))


def _parse_f0(raw):
    r0 = str(raw).replace("′", "'").replace("’", "'")
    if "''" in r0 or "d2y" in r0 or "d^2y" in r0 or "d²y" in r0:
        raise ValueError("Yalnızca birinci mertebe y' = f(x, y) desteklenir / only first-order y' = f(x, y) "
                         "is supported: " + str(raw))
    s = _clean(raw)
    expr, rhs = None, None
    if "=" in s:
        parts = s.split("=")
        R = sp.sympify(_parse_part(parts[-1]))
        try:
            L = sp.sympify(_parse_part(parts[0]))
        except Exception:
            L = None
        if L is not None and L.has(_D):
            expr = L - R
        else:
            rhs = R
    else:
        e = sp.sympify(_parse_part(s))
        if e.has(_D):
            expr = e
        else:
            rhs = e
    if expr is not None:
        sols = sp.solve(expr, _D)
        if len(sols) != 1:
            raise ValueError("y' yalnız bırakılamadı / could not isolate y': " + str(raw))
        rhs = sols[0]
    f = sp.sympify(rhs)
    ren = {}
    for v in f.free_symbols:
        if v.name in ("x", "t"):
            ren[v] = _X
        elif v.name == "y":
            ren[v] = _Y
    if ren:
        f = f.subs(ren)
    extra = sorted([v for v in f.free_symbols if v not in (_X, _Y)], key=str)
    if len(extra) > 2:
        raise ValueError("Tanınmayan ifade / unrecognised expression: " + str(raw))
    if extra:
        f = f.subs({v: 1 for v in extra})
    if f.has(sp.Float):
        f = sp.nsimplify(f, rational=True)
    return f, [str(v) for v in extra]


def _fxs(raw, f, extra):
    # Soru metni için: kullanıcının yazdığı biçimi koru (ör. -0.1·(y - 20)), yoksa sympy biçimi.
    s = _clean(raw)
    if extra or "yprime" in s or "=" in s:
        return _pretty(f)
    return " ".join(s.split()).replace("**", "^").replace("*", "·")


def _has_null(num, F, xa, xb, ya, yb):
    if not (num.has(_X) or num.has(_Y)):
        return False
    try:
        XX, YY = np.meshgrid(np.linspace(xa, xb, 160), np.linspace(ya, yb, 120))
        Z = _fnum(num)(XX, YY)
        return bool(np.isfinite(Z).all() and Z.min() < 0 < Z.max())
    except Exception:
        return False


def _fnum(f):
    g = sp.lambdify((_X, _Y), f, "numpy")

    def F(xv, yv):
        xa = np.asarray(xv, dtype=float)
        ya = np.asarray(yv, dtype=float)
        shp = np.broadcast(xa, ya).shape
        try:
            with np.errstate(all="ignore"):
                out = np.asarray(g(xa, ya), dtype=complex)
                out = np.where(np.abs(out.imag) < 1e-9, out.real, np.nan)
        except Exception:
            return np.full(shp, np.nan)
        return np.broadcast_to(out, shp).astype(float)
    return F


def _scalar(F):
    def h(a, b):
        return float(F(a, b))
    return h


def _rk4(F1, x0, y0, x1, n, lo, hi):
    xs, ys = [x0], [y0]
    if n <= 0 or x1 == x0:
        return np.array(xs, dtype=float), np.array(ys, dtype=float)
    hh = (x1 - x0) / n
    y = y0
    for k in range(n):
        x = x0 + k * hh
        k1 = F1(x, y)
        k2 = F1(x + hh / 2, y + hh * k1 / 2)
        k3 = F1(x + hh / 2, y + hh * k2 / 2)
        k4 = F1(x + hh, y + hh * k3)
        ks = (k1, k2, k3, k4)
        if not all(math.isfinite(v) for v in ks):
            break
        # tutarsız eğimler = tekillik (ör. 1/(x-1)) ya da patlama: eğriyi orada kes
        if abs(hh) * (max(ks) - min(ks)) > 0.1 * (1.0 + abs(y)):
            break
        y = y + hh * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        if not math.isfinite(y) or y < lo or y > hi:
            break
        xs.append(x0 + (k + 1) * hh)
        ys.append(y)
    return np.array(xs, dtype=float), np.array(ys, dtype=float)


def _is_lin(e, v):
    return e.is_polynomial(v) and sp.degree(e, v) <= 1


def _nice(e, rational_ok):
    # polinom × e^(ax+b) × sin/cos(ax+b) toplamları (ve izin varsa rasyonel/ln/√ terimler):
    # integralleri elemanter ve sympy için hızlıdır.
    e = sp.expand(e)
    if not e.has(_X):
        return True
    for term in sp.Add.make_args(e):
        trans, ratp, other = 0, 0, 0
        for fac in sp.Mul.make_args(term):
            if not fac.has(_X) or fac.is_polynomial(_X):
                continue
            if fac.func in (sp.exp, sp.sin, sp.cos) and _is_lin(fac.args[0], _X):
                trans += 1
                continue
            if fac.is_Pow and fac.args[0].is_polynomial(_X) and fac.args[1].is_Rational:
                if fac.args[1].is_Integer:
                    ratp += 1
                elif _is_lin(fac.args[0], _X):
                    other += 1
                else:
                    return False
                continue
            if fac.func == sp.log and _is_lin(fac.args[0], _X):
                other += 1
                continue
            return False
        if (ratp or other) and (trans or not rational_ok):
            return False
        if other and (ratp or other > 1):
            return False
    return True


def _h_ok(h):
    if h.is_polynomial(_Y):
        return sp.degree(h, _Y) <= 2
    inv = sp.together(1 / h)
    if inv.is_polynomial(_Y) and sp.degree(inv, _Y) <= 1:
        return True
    if h.func == sp.exp and _is_lin(h.args[0], _Y):
        return True
    b, ex = h.as_base_exp()
    return b == _Y and ex.is_Rational


def _bad(v):
    v = sp.sympify(v)
    return (not v.is_number) or v.has(sp.zoo, sp.nan, sp.oo, -sp.oo, sp.I)


def _linear(f, x0r, y0r):
    fe = sp.expand(f)
    p = sp.expand(sp.diff(fe, _Y))
    q = sp.expand(fe - p * _Y)
    if p.has(_Y) or q.has(_Y):
        return None
    C = sp.Symbol("C")
    if p == 0:
        if not _nice(q, True):
            return None
        G = sp.integrate(q, _X)
        if G.has(sp.Integral):
            return None
        Cv = sp.simplify(y0r - G.subs(_X, x0r))
        if _bad(Cv):
            return None
        return {"method": "quad", "G": G, "C": Cv, "sol": G + Cv}
    if not _nice(p, True):
        return None
    I = sp.integrate(-p, _X)
    if I.has(sp.Integral):
        return None
    mu = sp.powsimp(sp.exp(I))
    if q == 0:
        muq, Fm = sp.Integer(0), sp.Integer(0)
    else:
        muq = sp.expand(sp.powsimp(sp.expand(mu * q)))
        if not _nice(muq, True):
            return None
        Fm = sp.integrate(muq, _X)
        if Fm.has(sp.Integral):
            return None
    mu0 = mu.subs(_X, x0r)
    if _bad(mu0) or mu0 == 0:
        return None
    Cv = sp.simplify(y0r * mu0 - Fm.subs(_X, x0r))
    if _bad(Cv):
        return None
    gen = sp.expand(sp.powsimp(sp.expand((Fm + C) / mu)))
    sol = sp.expand(sp.powsimp(sp.expand((Fm + Cv) / mu)))
    return {"method": "linear", "P": -p, "Q": q, "mu": mu, "muq": muq, "F": Fm, "C": Cv,
            "gen": gen, "sol": sol}


def _separable(f, x0r, y0r):
    sep = sp.separatevars(f, symbols=[_X, _Y], dict=True)
    if not sep:
        return []
    g = sep["coeff"] * sep[_X]
    h = sep[_Y]
    if not h.has(_Y) or not _nice(g, True) or not _h_ok(h):
        return []
    Yf = sp.Function("y")
    ode = sp.Eq(Yf(_X).diff(_X), f.subs(_Y, Yf(_X)))
    gen = sp.dsolve(ode, Yf(_X), hint="separable")
    gens = gen if isinstance(gen, list) else [gen]
    out = []
    for eq in gens:
        if eq.lhs != Yf(_X):
            continue
        rhs = eq.rhs
        cs = [s for s in rhs.free_symbols if s.name.startswith("C")]
        if len(cs) != 1:
            continue
        try:
            vals = sp.solve(sp.Eq(rhs.subs(_X, x0r), y0r), cs[0])
        except Exception:
            continue
        for cv in vals:
            out.append({"method": "sep", "g": g, "h": h, "gen": rhs, "Cs": str(cs[0]), "C": cv,
                        "sol": rhs.subs(cs[0], cv)})
    return out


def _verify(sol, rx, ry, bound):
    try:
        g = sp.lambdify(_X, sol, "numpy")
        with np.errstate(all="ignore"):
            v = np.asarray(g(np.asarray(rx, dtype=float)), dtype=complex)
        v = np.broadcast_to(v, np.shape(rx))
    except Exception:
        return False
    good = np.isfinite(ry) & (np.abs(ry) < bound) & np.isfinite(v.real) & np.isfinite(v.imag)
    if good.sum() < 5:
        return False
    if np.max(np.abs(v.imag[good])) > 1e-6:
        return False
    err = np.abs(v.real[good] - ry[good]) / (1.0 + np.abs(ry[good]))
    return bool(err.max() < 1e-3)


def _closed(f, x0, y0, rx, ry, F, xa, xb):
    # Yalnızca güvenli sınıflar denenir (doğrusal / basit ayrılabilir); her aday
    # RK4 çözümüyle sayısal olarak doğrulanır. Böylece sympy asla takılmaz.
    y0r = sp.nsimplify(y0, rational=True)
    x0r = sp.nsimplify(x0, rational=True)
    xt = np.linspace(xa, xb, 41)
    ev = F(xt, np.full_like(xt, y0))
    if np.all(np.isfinite(ev)) and np.max(np.abs(ev)) < 1e-12:
        return {"method": "eq", "sol": y0r}
    try:
        if sp.count_ops(f) > 24:
            return None
        cands = []
        if sp.diff(f, _Y, 2) == 0:
            r = _linear(f, x0r, y0r)
            if r is not None:
                cands.append(r)
        if not cands:
            cands = _separable(f, x0r, y0r)
        bound = 30.0 * (1.0 + abs(y0))
        for c in cands:
            if _verify(c["sol"], rx, ry, bound):
                return c
    except Exception:
        return None
    return None


def _evalx(e, xv):
    try:
        v = complex(sp.sympify(e).subs(_X, xv).evalf())
    except Exception:
        return None
    if abs(v.imag) > 1e-9 or not math.isfinite(v.real):
        return None
    return v.real


def _seg_ratio(fig, ax, W, H):
    fw, fh = fig.get_size_inches()
    pos = ax.get_position()
    return (pos.height * fh / H) / (pos.width * fw / W)


def _field(F, xmin, xmax, ymin, ymax, ratio, nx, ny, frac=0.36):
    W, H = xmax - xmin, ymax - ymin
    gx = xmin + (np.arange(nx) + 0.5) * W / nx
    gy = ymin + (np.arange(ny) + 0.5) * H / ny
    GX, GY = np.meshgrid(gx, gy, indexing="ij")
    S = F(GX, GY)
    ang = np.arctan(S * ratio)
    L = frac * W / nx
    dx = L * np.cos(ang)
    dy = L * np.sin(ang) / ratio
    segs = np.stack([np.stack([GX - dx, GY - dy], -1), np.stack([GX + dx, GY + dy], -1)], -2)
    segs = segs.reshape(-1, 2, 2)
    col = np.repeat(np.arange(nx), ny)
    ok = np.isfinite(segs).all(axis=(1, 2))
    return segs[ok], col[ok]
'''

# Sabit katsayılı a·y'' + b·y' + c·y = 0: kökler, genel/özel çözüm, güzel yazım
_SECOND = r'''
import sympy as sp

_T = sp.Symbol("t", real=True)


def _q(v):
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, int):
        return sp.Integer(v)
    if isinstance(v, str):
        return sp.nsimplify(sp.sympify(v.replace("^", "**")), rational=True)
    return sp.nsimplify(float(v), rational=True)


def _ps(e):
    e = sp.sympify(e)
    if e.is_Rational:
        return str(e.p) if e.q == 1 else f"{e.p}/{e.q}"
    s = sp.sstr(e)
    if len(s) > 16:
        return _n(float(e), 3)
    return s.replace("sqrt", "√").replace("**", "^").replace("*", "·")


def _lin(v, var="t"):
    v = sp.sympify(v)
    if v == 1:
        return var
    if v == -1:
        return "-" + var
    if v.is_Rational:
        p, q = int(v.p), int(v.q)
        head = ("-" if p < 0 else "") + ("" if abs(p) == 1 else str(abs(p))) + var
        return head if q == 1 else f"{head}/{q}"
    s = _ps(v)
    if "+" in s or "-" in s[1:]:
        return f"({s})·{var}"
    return f"{s}·{var}"


def _join(terms):
    out = ""
    for cf, body in terms:
        cf = sp.sympify(cf)
        if cf == 0:
            continue
        neg = bool(cf < 0)
        mag = -cf if neg else cf
        ms = _ps(mag)
        if "+" in ms or "-" in ms:
            ms = "(" + ms + ")"
        if body:
            if mag == 1:
                txt = body
            elif ms.isdigit():
                txt = ms + body
            elif "/" in ms and not ms.startswith("("):
                txt = "(" + ms + ")·" + body
            else:
                txt = ms + "·" + body
        else:
            txt = ms
        if not out:
            out = ("-" if neg else "") + txt
        else:
            out += (" - " if neg else " + ") + txt
    return out or "0"


def _ept(r):
    r = sp.sympify(r)
    return "" if r == 0 else "e^(" + _lin(r) + ")"


def _im(v):
    s = _ps(v)
    if s == "1":
        return "i"
    return s + "i" if s.replace(".", "").isdigit() else "(" + s + ")i"


def _pp(v):
    v = sp.sympify(v)
    return "(" + _ps(v) + ")" if bool(v < 0) else _ps(v)


def _times(inner, e, front=False):
    if not e:
        return inner
    if inner == "1":
        return e
    if inner == "-1":
        return "-" + e
    if front:
        return f"{e}·({inner})" if " " in inner else f"{e}·{inner}"
    if " " in inner:
        return f"({inner})·{e}"
    return f"{inner}·{e}"


def _lamt(expr):
    g = sp.lambdify(_T, expr, "numpy")

    def lam(tv):
        tv = np.asarray(tv, dtype=float)
        with np.errstate(all="ignore"):
            out = np.asarray(g(tv), dtype=float)
        return np.broadcast_to(out, tv.shape).astype(float)
    return lam


def _sol2(a, b, c, y0, v0, var="y"):
    a, b, c, y0, v0 = _q(a), _q(b), _q(c), _q(y0), _q(v0)
    if a == 0:
        raise ValueError("Baş katsayı sıfır olamaz / leading coefficient must be nonzero")
    if a < 0:
        a, b, c = -a, -b, -c
    t = _T
    D = sp.simplify(b * b - 4 * a * c)
    y0s, v0s = _ps(y0), _ps(v0)
    R = {"a": a, "b": b, "c": c, "y0": y0, "v0": v0, "D": D, "al": None, "om": None}
    if D > 0:
        sq = sp.sqrt(D)
        r1 = sp.radsimp((-b + sq) / (2 * a))
        r2 = sp.radsimp((-b - sq) / (2 * a))
        C1 = sp.radsimp(sp.simplify((v0 - r2 * y0) / (r1 - r2)))
        C2 = sp.radsimp(sp.simplify(y0 - C1))
        expr = C1 * sp.exp(r1 * t) + C2 * sp.exp(r2 * t)
        e1, e2 = _ept(r1) or "1", _ept(r2) or "1"
        R.update(case="real", roots=[r1, r2], C1=C1, C2=C2, expr=expr,
                 basis=[sp.exp(r1 * t), sp.exp(r2 * t)], btxt=[e1, e2],
                 gen=f"C₁·{e1} + C₂·{e2}",
                 part=_join([(C1, _ept(r1)), (C2, _ept(r2))]),
                 rtxt=(f"r₁ = {_ps(r1)}, r₂ = {_ps(r2)} (iki farklı reel kök)",
                       f"r₁ = {_ps(r1)}, r₂ = {_ps(r2)} (two distinct real roots)"),
                 rshort=f"r₁ = {_ps(r1)},  r₂ = {_ps(r2)}",
                 cst=(f"{var}(0) = C₁ + C₂ = {y0s},  {var}'(0) = r₁·C₁ + r₂·C₂ = {v0s}  ⇒  "
                      f"C₁ = {_ps(C1)}, C₂ = {_ps(C2)}",) * 2,
                 rv=[complex(float(r1), 0.0), complex(float(r2), 0.0)])
    elif D == 0:
        r = sp.simplify(-b / (2 * a))
        C1 = y0
        C2 = sp.simplify(v0 - r * y0)
        e = _ept(r)
        expr = (C1 + C2 * t) * sp.exp(r * t)
        R.update(case="double", roots=[r, r], C1=C1, C2=C2, expr=expr,
                 basis=[sp.exp(r * t), t * sp.exp(r * t)],
                 btxt=[e or "1", ("t·" + e) if e else "t"],
                 gen=(f"(C₁ + C₂·t)·{e}" if e else "C₁ + C₂·t"),
                 part=_times(_join([(C1, ""), (C2, "t")]), e),
                 rtxt=(f"r₁ = r₂ = {_ps(r)} (çift katlı kök)", f"r₁ = r₂ = {_ps(r)} (repeated root)"),
                 rshort=f"r₁ = r₂ = {_ps(r)}",
                 cst=(f"{var}(0) = C₁ = {y0s},  {var}'(0) = r·C₁ + C₂ = {v0s}  ⇒  C₂ = {_ps(C2)}",) * 2,
                 rv=[complex(float(r), 0.0), complex(float(r), 0.0)])
    else:
        al = sp.simplify(-b / (2 * a))
        om = sp.radsimp(sp.sqrt(-D) / (2 * a))
        C1 = y0
        C2 = sp.radsimp(sp.simplify((v0 - al * y0) / om))
        e = _ept(al)
        cw, sw = f"cos({_lin(om)})", f"sin({_lin(om)})"
        expr = sp.exp(al * t) * (C1 * sp.cos(om * t) + C2 * sp.sin(om * t))
        pre = (e + "·") if e else ""
        rshort = (f"r = {_ps(al)} ± {_im(om)}" if al != 0 else f"r = ± {_im(om)}")
        R.update(case="complex", roots=[al, om], C1=C1, C2=C2, expr=expr, al=al, om=om,
                 basis=[sp.exp(al * t) * sp.cos(om * t), sp.exp(al * t) * sp.sin(om * t)],
                 btxt=[pre + cw, pre + sw],
                 gen=(f"{e}·(C₁·{cw} + C₂·{sw})" if e else f"C₁·{cw} + C₂·{sw}"),
                 part=_times(_join([(C1, cw), (C2, sw)]), e, True),
                 rtxt=(rshort + (" (karmaşık eşlenik kökler)" if al != 0 else " (sanal kökler)"),
                       rshort + (" (complex conjugate roots)" if al != 0 else " (purely imaginary roots)")),
                 rshort=rshort,
                 cst=(f"{var}(0) = C₁ = {y0s},  {var}'(0) = α·C₁ + ω·C₂ = {v0s}  "
                      f"(α = {_ps(al)}, ω = {_ps(om)})  ⇒  C₂ = {_ps(C2)}",) * 2,
                 rv=[complex(float(al), float(om)), complex(float(al), -float(om))])
    R["lam"] = _lamt(R["expr"])
    R["blam"] = [_lamt(bb) for bb in R["basis"]]
    return R
'''


# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["slope_field_expr"] = {
    "course": "diffeq",
    "title": ("Eğim alanı ve çözüm eğrisi", "Slope field and a solution curve"),
    "topics": ["slope field", "slope fields", "direction field", "direction fields", "isocline",
               "first order", "first-order", "initial value problem", "solution curve",
               "separable", "linear differential", "autonomous", "equilibrium solution",
               "eğim alanı", "yön alanı", "doğrultu alanı", "başlangıç değer problemi",
               "birinci mertebe", "izoklin", "ayrılabilir", "denge çözümü"],
    "code": _FMT + _ODE_CORE + r'''

def _eqpts(f, F1):
    if f.has(_X) or not f.has(_Y):
        return []
    try:
        num = sp.fraction(sp.together(f))[0]
        if not num.is_polynomial(_Y) or sp.degree(num, _Y) > 4:
            return []
        out = []
        for r in sp.solve(num, _Y):
            if not r.is_real:
                continue
            rv = float(r)
            eps = 1e-4 * (1.0 + abs(rv))
            lft, rgt = F1(0.0, rv - eps), F1(0.0, rv + eps)
            if lft > 0 and rgt < 0:
                kind = "stable"
            elif lft < 0 and rgt > 0:
                kind = "unstable"
            else:
                kind = "semi"
            out.append((rv, r, kind))
        return sorted(out, key=lambda t: t[0])
    except Exception:
        return []


def _analyze(P):
    key = ("sf", repr(sorted((str(k), str(v)) for k, v in P.items() if k not in ("lang", "seed"))))
    if key in _CACHE:
        return _CACHE[key]
    f, extra = _parse_f(P.get("f", "x - y"))
    F = _fnum(f)
    F1 = _scalar(F)
    x0 = _num(P.get("x0"), 0.0)
    y0 = _num(P.get("y0"), 1.0)
    xmin = _num(P.get("xmin"), x0 - 3.0)
    xmax = _num(P.get("xmax"), x0 + 3.0)
    if not xmax > xmin:
        xmin, xmax = x0 - 3.0, x0 + 3.0
    xmin, xmax = min(xmin, x0), max(xmax, x0)
    W = xmax - xmin
    probe = F(np.linspace(xmin, xmax, 9)[:, None], np.linspace(y0 - 3, y0 + 3, 9)[None, :])
    if not np.isfinite(probe).any():
        raise ValueError("f(x, y) hesaplanamadı / f(x, y) could not be evaluated: " + str(P.get("f")))
    big = 1e4 * (1.0 + abs(y0))
    xf, yf = _rk4(F1, x0, y0, xmax, int(round(500 * (xmax - x0) / W)), -big, big)
    xb, yb = _rk4(F1, x0, y0, xmin, int(round(500 * (x0 - xmin) / W)), -big, big)
    ymin, ymax = _num(P.get("ymin"), float("nan")), _num(P.get("ymax"), float("nan"))
    if not (math.isfinite(ymin) and math.isfinite(ymax) and ymax > ymin):
        allv = np.concatenate([yb, yf])
        lo = min(y0 - 2.0, float(np.percentile(allv, 3)))
        hi = max(y0 + 2.0, float(np.percentile(allv, 97)))
        lo, hi = max(lo, y0 - 6.0), min(hi, y0 + 6.0)
        pad = 0.08 * (hi - lo)
        ymin, ymax = lo - pad, hi + pad
    ymin, ymax = min(ymin, y0), max(ymax, y0)
    H = ymax - ymin
    rx = np.concatenate([xb[::-1], xf[1:]])
    ry = np.concatenate([yb[::-1], yf[1:]])
    closed = _closed(f, x0, y0, rx, ry, F, xmin, xmax)
    if P.get("xe") is not None:
        xe = _num(P.get("xe"), x0 + 1.0)
    elif xmax - x0 >= 0.5:
        xe = min(xmax, x0 + 2.0)
    else:
        xe = max(xmin, x0 - 2.0)
    reach = xb[-1] - 1e-9 <= xe <= xf[-1] + 1e-9
    if closed is not None and not reach:
        # RK4 sınırda durdu: kapalı form [son nokta, xe] üzerinde sonlu, tek işaretli ve monoton ise
        # bu bir patlama değil yalnızca çok büyük değerlerdir (ör. y' = 10y).
        try:
            xr = xf[-1] if xe > x0 else xb[-1]
            g = sp.lambdify(_X, closed["sol"], "numpy")
            with np.errstate(all="ignore"):
                v = np.broadcast_to(np.asarray(g(np.linspace(xr, xe, 300)), dtype=complex), (300,))
            dv = np.diff(v.real)
            reach = bool(np.all(np.isfinite(v)) and np.max(np.abs(v.imag)) < 1e-9
                         and (np.all(v.real > 0) or np.all(v.real < 0))
                         and (np.all(dv >= 0) or np.all(dv <= 0)))
        except Exception:
            reach = False
    ye = _evalx(closed["sol"], xe) if (closed is not None and reach) else None
    if ye is None:
        if xe == x0:
            ye = y0
        elif x0 < xe <= xf[-1] + 1e-12 and len(xf) > 1:
            ye = float(np.interp(xe, xf, yf))
        elif xb[-1] - 1e-12 <= xe < x0 and len(xb) > 1:
            ye = float(np.interp(xe, xb[::-1], yb[::-1]))

    def cut(xs, ys):
        out = np.nonzero((ys < ymin - 0.5 * H) | (ys > ymax + 0.5 * H))[0]
        if len(out):
            return xs[:out[0] + 1], ys[:out[0] + 1]
        return xs, ys

    xf, yf = cut(xf, yf)
    xb, yb = cut(xb, yb)
    num = sp.fraction(sp.together(f))[0]
    A = {"f": f, "extra": extra, "F": F, "F1": F1, "x0": x0, "y0": y0,
         "win": (xmin, xmax, ymin, ymax), "xf": xf, "yf": yf, "xb": xb, "yb": yb,
         "closed": closed, "xe": xe, "ye": ye, "eqs": _eqpts(f, F1),
         "num": num, "null": _has_null(num, F, xmin, xmax, ymin, ymax),
         "fxs": _fxs(P.get("f", "x - y"), f, extra), "s0": F1(x0, y0), "h": W / 500.0}
    if len(_CACHE) > 60:
        _CACHE.clear()
    _CACHE[key] = A
    return A


def _closed_steps(C, x0s, y0s):
    m = C["method"]
    if m == "eq":
        return [(f"f(x, {y0s}) = 0 (her x için) ⇒ y = {y0s} sabit fonksiyonu bir denge çözümüdür",
                 f"f(x, {y0s}) = 0 for every x ⇒ the constant function y = {y0s} is an equilibrium solution")]
    sol = _pretty(C["sol"])
    if m == "quad":
        G, Cv = _pretty(C["G"]), _pretty(C["C"])
        return [(f"y' yalnızca x'e bağlı ⇒ y = ∫ f(x) dx = {G} + C",
                 f"y' depends on x only ⇒ y = ∫ f(x) dx = {G} + C"),
                (f"y({x0s}) = {y0s} ⇒ C = {Cv}", f"y({x0s}) = {y0s} ⇒ C = {Cv}"),
                (f"Özel çözüm: y = {sol}", f"Particular solution: y = {sol}")]
    if m == "linear":
        Pp, Qq, mu = _pretty(C["P"]), _pretty(C["Q"]), _pretty(C["mu"])
        st = [(f"Doğrusal denklem y' + P(x)·y = Q(x):  P(x) = {Pp},  Q(x) = {Qq}",
               f"Linear equation y' + P(x)·y = Q(x):  P(x) = {Pp},  Q(x) = {Qq}"),
              (f"İntegral çarpanı: μ(x) = e^(∫P dx) = {mu}", f"Integrating factor: μ(x) = e^(∫P dx) = {mu}")]
        if C["Q"] == 0:
            st.append(("(μ·y)' = 0 ⇒ μ·y = C", "(μ·y)' = 0 ⇒ μ·y = C"))
        else:
            s = f"(μ·y)' = μ·Q ⇒ μ·y = ∫ {_pretty(C['muq'])} dx = {_pretty(C['F'])} + C"
            st.append((s, s))
        gen, Cv = _pretty(C["gen"]), _pretty(C["C"])
        st += [(f"Genel çözüm: y = {gen}", f"General solution: y = {gen}"),
               (f"y({x0s}) = {y0s} ⇒ C = {Cv}", f"y({x0s}) = {y0s} ⇒ C = {Cv}"),
               (f"Özel çözüm: y = {sol}", f"Particular solution: y = {sol}")]
        return st
    h, g, gen, Cv = _pretty(C["h"]), _pretty(C["g"]), _pretty(C["gen"]), _pretty(C["C"])
    gdx = "dx" if C["g"] == 1 else f"({g}) dx"
    return [(f"Değişkenlerine ayrılabilir: dy / ({h}) = {gdx}",
             f"Separable: dy / ({h}) = {gdx}"),
            (f"İki tarafın integrali alınıp y yalnız bırakılır: y = {gen}",
             f"Integrate both sides and solve for y: y = {gen}"),
            (f"y({x0s}) = {y0s} ⇒ {C['Cs']} = {Cv}", f"y({x0s}) = {y0s} ⇒ {C['Cs']} = {Cv}"),
            (f"Özel çözüm: y = {sol}", f"Particular solution: y = {sol}")]


_KIND = {"stable": ("kararlı", "stable"), "unstable": ("kararsız", "unstable"),
         "semi": ("yarı kararlı", "semi-stable")}


def solve(P):
    A = _analyze(P)
    fx = A["fxs"]
    x0s, y0s, xes = _n(A["x0"], 3), _n(A["y0"], 3), _n(A["xe"], 3)
    steps = [(f"Denklem: y' = f(x, y) = {fx},  başlangıç koşulu y({x0s}) = {y0s}",
              f"Equation: y' = f(x, y) = {fx},  initial condition y({x0s}) = {y0s}")]
    if A["extra"]:
        names = ", ".join(A["extra"])
        steps.append((f"Not: ifadedeki {names} sabit(ler)i 1 alındı",
                      f"Note: the constant(s) {names} in the expression were set to 1"))
    s0 = A["s0"]
    if math.isfinite(s0):
        steps.append((f"Eğim alanı: her (x, y) noktasına eğimi f(x, y) olan kısa bir çizgi çizilir; "
                      f"başlangıç noktasında eğim f({x0s}, {y0s}) = {_n(s0, 3)}",
                      f"Slope field: at every point (x, y) draw a short segment of slope f(x, y); "
                      f"at the initial point the slope is f({x0s}, {y0s}) = {_n(s0, 3)}"))
    else:
        steps.append((f"f({x0s}, {y0s}) tanımsız: çözüm bu noktadan başlatılamaz",
                      f"f({x0s}, {y0s}) is undefined: no solution can start here"))
    if A["null"]:
        nl = _pretty(A["num"])
        steps.append((f"Yatay eğimler (f = 0 izoklini): {nl} = 0",
                      f"Horizontal slopes (the isocline f = 0): {nl} = 0"))
    if A["eqs"]:
        trs = ", ".join(f"y = {_pretty(r)} ({_KIND[k][0]})" for _, r, k in A["eqs"])
        ens = ", ".join(f"y = {_pretty(r)} ({_KIND[k][1]})" for _, r, k in A["eqs"])
        steps.append(("Otonom denklem; denge çözümleri f(y) = 0: " + trs,
                      "Autonomous equation; equilibria where f(y) = 0: " + ens))
    C = A["closed"]
    if C is not None:
        steps += _closed_steps(C, x0s, y0s)
        if C["method"] != "eq":
            steps.append(("Kontrol: kapalı form, sayısal RK4 çözümüyle örtüşüyor ✓",
                          "Check: the closed form agrees with the numerical RK4 solution ✓"))
    else:
        steps.append(("Denklem doğrusal ya da basit ayrılabilir değil (kapalı form bulunamadı) ⇒ "
                      "sayısal çözüm: Runge–Kutta 4 (RK4)",
                      "The equation is not linear or simply separable (no closed form found) ⇒ "
                      "numerical solution: Runge–Kutta 4 (RK4)"))
    ye, hs = A["ye"], _n(A["h"], 3)
    if ye is not None:
        tail = f"y({xes}) ≈ {_n(ye, 4)}"
        steps.append((f"Eğri (x₀, y₀) noktasından RK4 ile iki yöne izlenir (h ≈ {hs}): {tail}",
                       f"The curve is traced from (x₀, y₀) in both directions with RK4 (h ≈ {hs}): {tail}"))
    else:
        tail = ""
        steps.append((f"Çözüm x = {xes} noktasına ulaşmadan sınırsız büyüyor ya da tanımsız oluyor",
                      f"The solution blows up or becomes undefined before reaching x = {xes}"))
    if C is not None:
        a = f"y = {_pretty(C['sol'])}" + (f";  {tail}" if tail else "")
        answer = (a, a)
    elif tail:
        answer = (f"Sayısal (RK4): {tail}", f"Numerical (RK4): {tail}")
    else:
        answer = (f"Çözüm x = {xes} öncesinde patlıyor", f"The solution blows up before x = {xes}")
    return {"answer": answer, "steps": steps,
            "fmt": {"fx": fx, "ic": f"y({x0s}) = {y0s}", "xe": xes}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    A = _analyze(P)
    F = A["F"]
    x0, y0 = A["x0"], A["y0"]
    xmin, xmax, ymin, ymax = A["win"]
    W, H = xmax - xmin, ymax - ymin
    xf, yf, xb, yb = A["xf"], A["yf"], A["xb"], A["yb"]
    x0s, y0s, xes = _n(x0, 3), _n(y0, 3), _n(A["xe"], 3)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.8, bottom=0.1)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.grid(alpha=0.2)
    if ymin < 0 < ymax:
        ax.axhline(0, color="#9CA3AF", lw=1)
    if xmin < 0 < xmax:
        ax.axvline(0, color="#9CA3AF", lw=1)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"y' = {A['fxs']},    y({x0s}) = {y0s}", fontsize=12)
    ratio = _seg_ratio(fig, ax, W, H)
    nx, ny = 25, 17
    segs, col = _field(F, xmin, xmax, ymin, ymax, ratio, nx, ny)
    field = LineCollection([], colors="#6B7280", linewidths=1.1, alpha=0.75, zorder=2)
    ax.add_collection(field)
    null_cs = None
    if A["null"]:
        try:
            XX, YY = np.meshgrid(np.linspace(xmin, xmax, 160), np.linspace(ymin, ymax, 120))
            Z = _fnum(A["num"])(XX, YY)
            null_cs = ax.contour(XX, YY, Z, levels=[0.0], colors="#16A34A", linewidths=1.5,
                                 linestyles="--", zorder=3)
        except Exception:
            null_cs = None
    eq_txt = []
    for rv, r, k in A["eqs"]:
        if ymin < rv < ymax:
            eq_txt.append(ax.text(xmax - 0.01 * W, rv + 0.015 * H,
                                  f"y = {_pretty(r)} ({_KIND[k][0 if tr else 1]})",
                                  ha="right", va="bottom", color="#16A34A", fontsize=9, zorder=4,
                                  bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8)))
    curve_f, = ax.plot([], [], color="#2563EB", lw=2.6, zorder=6)
    curve_b, = ax.plot([], [], color="#2563EB", lw=2.6, zorder=6)
    tang, = ax.plot([], [], color="#E07B39", lw=3.4, zorder=7, solid_capstyle="round")
    tracer, = ax.plot([], [], "o", color="#2563EB", ms=8, zorder=8)
    p0, = ax.plot([], [], "o", color="#DC2626", ms=10, zorder=9)
    s0 = A["s0"]
    up_left = math.isfinite(s0) and s0 > 0
    p0lab = ax.text(x0 + (-0.015 if up_left else 0.015) * W, y0 + 0.035 * H, "", color="#DC2626",
                    fontsize=11, fontweight="bold", zorder=9, ha="right" if up_left else "left",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
    pe, = ax.plot([], [], "D", color="#7C3AED", ms=9, zorder=9)
    right = A["xe"] > xmin + 0.6 * W
    pelab = ax.text(0, 0, "", color="#7C3AED", fontsize=11, fontweight="bold", zorder=9,
                    ha="right" if right else "left",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    info = _banner(fig)

    def tangents(xs, ys):
        s = F(xs, ys)
        a = np.arctan(s * ratio)
        Lt = 0.065 * W
        return s, Lt * np.cos(a), Lt * np.sin(a) / ratio

    sf, dxf, dyf = tangents(xf, yf)
    sb, dxb, dyb = tangents(xb, yb)
    C = A["closed"]
    ye = A["ye"]
    if C is not None:
        sol = _pretty(C["sol"])
        fin1 = (f"4) Çözüm: y = {sol}" if tr else f"4) Solution: y = {sol}") if len(sol) <= 60 else \
            ("4) Kapalı form bulundu (adımlara bakın)" if tr else "4) Closed form found (see the steps)")
    else:
        fin1 = "4) Kapalı form yok → sayısal çözüm (RK4)" if tr else "4) No closed form → numerical solution (RK4)"
    if ye is not None:
        fin2 = f"y({xes}) ≈ {_n(ye, 4)}"
    else:
        fin2 = (f"çözüm x = {xes} öncesinde patlıyor" if tr else f"the solution blows up before x = {xes}")
    ph1 = "1) Eğim alanı: (x, y) noktasındaki çizginin eğimi f(x, y)" if tr else \
        "1) Slope field: the segment at (x, y) has slope f(x, y)"
    ph1b = "Yeşil kesikli: f = 0 (yatay eğimler)" if tr else "Green dashed: f = 0 (horizontal slopes)"
    ph2 = (f"2) Başlangıç noktası ({x0s}, {y0s}):  eğim f = {_n(s0, 3)}" if tr else
           f"2) Initial point ({x0s}, {y0s}):  slope f = {_n(s0, 3)}")
    ph3 = "3) Çözüm eğrisi her noktada eğim alanına teğettir (RK4)" if tr else \
        "3) The solution curve is tangent to the field everywhere (RK4)"
    show_e = ye is not None and ymin <= ye <= ymax and xmin <= A["xe"] <= xmax
    N = 160

    def show(xs, ys, ss, ddx, ddy, m, head):
        tracer.set_data([xs[m]], [ys[m]])
        if np.isfinite(ddx[m]):
            tang.set_data([xs[m] - ddx[m], xs[m] + ddx[m]], [ys[m] - ddy[m], ys[m] + ddy[m]])
            info.set_text(head + f"\nx = {xs[m]:.2f},   y = {ys[m]:.3f},   y' = f(x, y) = {ss[m]:.3f}")
        else:
            tang.set_data([], [])
            info.set_text(head + f"\nx = {xs[m]:.2f},   y = {ys[m]:.3f}")

    def update(i):
        if i < 24:
            field.set_segments(segs[:int(np.searchsorted(col, nx * _ramp(i, 0, 24), side="left"))])
        else:
            field.set_segments(segs)
        if null_cs is not None:
            null_cs.set_visible(i >= 18)
        for t in eq_txt:
            t.set_visible(i >= 18)
        if i >= 28:
            p0.set_data([x0], [y0])
            p0lab.set_text(f"({x0s}, {y0s})")
        else:
            p0.set_data([], [])
            p0lab.set_text("")
        mf = int(round(_ramp(i, 40, 100) * (len(xf) - 1)))
        mb = int(round(_ramp(i, 102, 128) * (len(xb) - 1)))
        if i >= 40:
            curve_f.set_data(xf[:mf + 1], yf[:mf + 1])
        else:
            curve_f.set_data([], [])
        if i >= 102:
            curve_b.set_data(xb[:mb + 1], yb[:mb + 1])
        else:
            curve_b.set_data([], [])
        if i >= 130 and show_e:
            pe.set_data([A["xe"]], [ye])
            pelab.set_position((A["xe"] + (-0.02 if right else 0.02) * W, ye + 0.04 * H))
            pelab.set_text(f"y({xes}) ≈ {_n(ye, 3)}")
        else:
            pe.set_data([], [])
            pelab.set_text("")
        if 28 <= i < 40:
            show(xf, yf, sf, dxf, dyf, 0, ph2)
        elif 40 <= i < 101:
            show(xf, yf, sf, dxf, dyf, mf, ph3)
        elif 101 <= i < 130:
            show(xb, yb, sb, dxb, dyb, mb, ph3)
        else:
            tracer.set_data([], [])
            tang.set_data([], [])
            if i < 28:
                info.set_text(ph1 + ("\n" + ph1b if (null_cs is not None and i >= 18) else ""))
            else:
                info.set_text(fin1 + "\n" + fin2)
        return []

    return N, update


def vary(P, rnd):
    A = _analyze(P)
    F1, x0, y0 = A["F1"], A["x0"], A["y0"]
    xmin, xmax, ymin, ymax = A["win"]
    opts = [v for v in (-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5, 3)
            if ymin < v < ymax and abs(v - y0) > 1e-9]
    rnd.shuffle(opts)
    for v in opts:
        if not math.isfinite(F1(x0, v)):
            continue
        Q = dict(P)
        Q["y0"] = int(v) if v == int(v) else v
        try:
            if _analyze(Q)["ye"] is not None:
                return Q
        except Exception:
            continue
    return dict(P)
''',
}
EXAMPLES += [
    {"id": "diffeq-slope-1", "kind": "slope_field_expr",
     "title": ("Doğrusal denklemin eğim alanı", "Slope field of a linear equation"),
     "q": ("y' = {fx} denkleminin eğim alanını çiz ve {ic} koşulunu sağlayan çözüm eğrisini bul.",
           "Sketch the slope field of y' = {fx} and find the solution curve satisfying {ic}."),
     "P": {"f": "x - y", "x0": 0, "y0": 1}},
    {"id": "diffeq-slope-2", "kind": "slope_field_expr",
     "topics": ["autonomous", "equilibrium", "otonom", "denge"],
     "title": ("Otonom denklem ve denge çözümleri", "Autonomous equation and equilibria"),
     "q": ("y' = {fx} otonom denkleminin denge çözümlerini bul, kararlılıklarını eğim alanından oku ve "
           "{ic} ile başlayan çözümü çiz.",
           "Find the equilibrium solutions of the autonomous equation y' = {fx}, read their stability "
           "from the slope field and sketch the solution starting at {ic}."),
     "P": {"f": "y*(2 - y)", "x0": 0, "y0": 0.5, "xmin": -1, "xmax": 4, "ymin": -1, "ymax": 3}},
    {"id": "diffeq-slope-3", "kind": "slope_field_expr",
     "topics": ["numerical", "sayısal"],
     "title": ("Kapalı formu olmayan denklem", "An equation with no elementary solution"),
     "q": ("y' = {fx}, {ic} başlangıç değer problemini eğim alanı üzerinde incele ve y({xe}) değerini "
           "sayısal olarak tahmin et.",
           "Study the initial value problem y' = {fx}, {ic} on its slope field and estimate y({xe}) "
           "numerically."),
     "P": {"f": "x**2 + y**2", "x0": 0, "y0": 0, "xmin": -2, "xmax": 2, "ymin": -3, "ymax": 3, "xe": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["exp_growth_decay"] = {
    "course": "diffeq",
    "title": ("Üstel büyüme ve azalma", "Exponential growth and decay"),
    "topics": ["exponential growth", "exponential decay", "growth and decay", "half-life", "half life",
               "doubling time", "radioactive decay", "radioactive", "population growth", "bacteria",
               "carbon dating", "üstel büyüme", "üstel azalma", "büyüme ve azalma", "yarı ömür",
               "yarılanma", "ikiye katlanma", "radyoaktif bozunma", "nüfus artışı", "bakteri"],
    "code": _FMT + r'''
import sympy as sp
from matplotlib.patches import Circle


def _kexpr(P):
    v = P.get("k", 0.1)
    if isinstance(v, str):
        s = v.replace("^", "**").replace("−", "-").replace("·", "*")
        return sp.sympify(s, locals={"ln": sp.log, "e": sp.E})
    return sp.nsimplify(float(v), rational=True)


def _kstr(P):
    v = P.get("k", 0.1)
    if isinstance(v, str):
        return sp.sstr(_kexpr(P)).replace("log", "ln").replace("**", "^").replace("*", "·")
    return _n(v, 4)


def _vals(P):
    k = _kexpr(P)
    kv = float(k)
    if kv == 0:
        raise ValueError("k sıfır olamaz / k must be nonzero")
    y0, te = float(P["y0"]), float(P["t_end"])
    T = math.log(2) / abs(kv)
    yend = sp.nsimplify(P["y0"], rational=True) * sp.exp(k * sp.nsimplify(P["t_end"], rational=True))
    return k, kv, y0, te, T, yend


def solve(P):
    k, kv, y0, te, T, yend = _vals(P)
    grow = kv > 0
    ks, kn = _kstr(P), _n(kv, 4)
    y0s, tes = _n(y0), _n(te)
    yv = float(yend)
    exact = yend.is_Rational
    kshow = ks if ks == kn else f"{ks} ≈ {kn}"
    steps = [(f"Model: dy/dt = k·y,  y(0) = {y0s},  k = {kshow}",
              f"Model: dy/dt = k·y,  y(0) = {y0s},  k = {kshow}"),
             ("Değişkenlere ayır: dy/y = k·dt ⇒ ln|y| = k·t + C ⇒ y = C·e^(k·t)",
              "Separate variables: dy/y = k·dt ⇒ ln|y| = k·t + C ⇒ y = C·e^(k·t)"),
             (f"y(0) = {y0s} ⇒ C = {y0s} ⇒ y(t) = {y0s}·e^({kn}·t)",
              f"y(0) = {y0s} ⇒ C = {y0s} ⇒ y(t) = {y0s}·e^({kn}·t)")]
    if grow:
        steps.append((f"İkiye katlanma süresi: T = ln 2 / k = {_n(T, 3)}",
                      f"Doubling time: T = ln 2 / k = {_n(T, 3)}"))
    else:
        steps.append((f"Yarı ömür: T½ = ln 2 / |k| = {_n(T, 3)}", f"Half-life: T½ = ln 2 / |k| = {_n(T, 3)}"))
    nT = te / T
    base = "2" if grow else "(1/2)"
    val = _n(yv, 2)
    eqs = "=" if exact else "≈"
    pw = str(int(round(nT))) if abs(nT - round(nT)) < 1e-9 else f"({_n(nT, 3)})"
    s = f"y({tes}) = {y0s}·e^({kn}·{tes}) = {y0s}·e^({_n(kv * te, 4)}) = {y0s}·{base}^{pw} {eqs} {val}"
    steps.append((s, s))
    if abs(nT - round(nT)) < 1e-9 and 1 <= round(nT) <= 12:
        m = int(round(nT))
        steps.append(((f"{tes} / {_n(T, 3)} = {m} kez ikiye katlanma ⇒ {y0s}·2^{m} = {val}" if grow else
                       f"{tes} / {_n(T, 3)} = {m} yarı ömür ⇒ {y0s}·(1/2)^{m} = {val}"),
                      (f"{tes} / {_n(T, 3)} = {m} doublings ⇒ {y0s}·2^{m} = {val}" if grow else
                       f"{tes} / {_n(T, 3)} = {m} half-lives ⇒ {y0s}·(1/2)^{m} = {val}")))
    ans_tr = f"y({tes}) {eqs} {val};  " + (f"ikiye katlanma süresi T ≈ {_n(T, 3)}" if grow else
                                         f"yarı ömür T½ ≈ {_n(T, 3)}")
    ans_en = f"y({tes}) {eqs} {val};  " + (f"doubling time T ≈ {_n(T, 3)}" if grow else
                                         f"half-life T½ ≈ {_n(T, 3)}")
    return {"answer": (ans_tr, ans_en), "steps": steps, "fmt": {"kk": ks, "T": _n(T, 3)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    k, kv, y0, te, T, yend = _vals(P)
    grow = kv > 0
    yv = float(yend)
    scene = str(P.get("scene", "bacteria" if grow else "atoms"))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.55], left=0.02, right=0.97, bottom=0.12, top=0.9,
                          wspace=0.14)
    axL = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[0, 1])
    axL.set_xlim(-1.15, 1.15)
    axL.set_ylim(-1.35, 1.2)
    axL.set_aspect("equal")
    axL.axis("off")
    axL.add_patch(Circle((0, 0), 1.0, fc="#F9FAFB", ec="#9CA3AF", lw=2.5, zorder=1))
    names = {"bacteria": ("Petri kabı", "Petri dish"), "atoms": ("Radyoaktif numune", "Radioactive sample"),
             "population": ("Nüfus", "Population")}
    nm = names.get(scene, names["bacteria" if grow else "atoms"])
    axL.set_title(nm[0 if tr else 1], fontsize=11)
    rng = np.random.default_rng(P.get("seed", 0))
    if grow:
        M = 260
        rr = 0.9 * np.sqrt(rng.random(M))
        th = 2 * np.pi * rng.random(M)
        pos = np.column_stack([rr * np.cos(th), rr * np.sin(th)])
        col = "#16A34A" if scene != "population" else "#2563EB"
        sc = axL.scatter(np.zeros(0), np.zeros(0), s=22, color=col, alpha=0.85, zorder=3,
                         edgecolors="white", linewidths=0.4)
        ymax_curve = max(yv, y0)
    else:
        M = 150
        rr = 0.88 * np.sqrt(rng.random(M))
        th = 2 * np.pi * rng.random(M)
        pos = np.column_stack([rr * np.cos(th), rr * np.sin(th)])
        rank = np.empty(M, dtype=int)
        rank[rng.permutation(M)] = np.arange(M)
        sc = axL.scatter(pos[:, 0], pos[:, 1], s=34, color="#E07B39", zorder=3,
                         edgecolors="white", linewidths=0.5)
        alive_c = np.array(_rgb("#E07B39") + (1.0,))
        dead_c = np.array(_rgb("#D1D5DB") + (1.0,))
        ymax_curve = y0
    cnt = axL.text(0, -1.2, "", ha="center", fontsize=12, fontweight="bold", color="#111827")
    clock = axL.text(-1.1, 1.08, "", ha="left", fontsize=10, color="#6B7280")
    ts = np.linspace(0, te, 400)
    ys = y0 * np.exp(kv * ts)
    ax.set_xlim(0, te * 1.02)
    ax.set_ylim(0, ymax_curve * 1.38)
    ax.grid(alpha=0.3)
    ax.set_xlabel("t")
    ax.set_ylabel("y(t)")
    ax.set_title(f"y(t) = {_n(y0)}·e^({_n(kv, 4)}·t)", fontsize=12)
    curve, = ax.plot([], [], color="#2563EB", lw=2.6)
    dot, = ax.plot([], [], "o", color="#2563EB", ms=8, zorder=6)
    nT = int(te / T + 1e-9)
    marks = []
    if 1 <= nT <= 10:
        for j in range(1, nT + 1):
            tj = j * T
            yj = y0 * np.exp(kv * tj)
            vl, = ax.plot([tj, tj], [0, yj], ":", color="#7C3AED", lw=1.3)
            pt, = ax.plot([tj], [yj], "o", color="#7C3AED", ms=6, zorder=5)
            lb = ax.text(tj, yj + ymax_curve * 0.035, "×2" if grow else "×½", color="#7C3AED", fontsize=10,
                         ha="right" if grow else "left", fontweight="bold")
            if tj >= te - 1e-9:
                lb.set_text("")
            marks.append((tj, vl, pt, lb))
    fin, = ax.plot([], [], "o", color="#DC2626", ms=11, zorder=7)
    finl, = ax.plot([], [], "--", color="#DC2626", lw=1.2)
    fint = ax.text(te * 0.97, 0, "", color="#DC2626", fontsize=12, fontweight="bold", ha="right",
                   va="bottom" if grow else "bottom")
    info = _box(ax)
    sol = solve(P)
    kn = _n(kv, 4)
    l1 = (f"1) dy/dt = k·y,  k = {kn} " + ("> 0 ⇒ üstel büyüme" if grow else "< 0 ⇒ üstel azalma")) if tr \
        else (f"1) dy/dt = k·y,  k = {kn} " + ("> 0 ⇒ exponential growth" if grow else "< 0 ⇒ exponential decay"))
    l2 = ((f"2) Her T = {_n(T, 3)} sürede ikiye katlanır" if grow else
           f"2) Her T½ = {_n(T, 3)} sürede yarıya iner") if tr else
          (f"2) Doubles every T = {_n(T, 3)}" if grow else f"2) Halves every T½ = {_n(T, 3)}"))
    eqs = "=" if yend.is_Rational else "≈"
    l3 = f"3) y({_n(te)}) {eqs} {_n(yv, 2)}"
    N = 150

    def update(i):
        tc = te * _ramp(i, 15, 120)
        yc = y0 * math.exp(kv * tc)
        m = max(1, int(round(_ramp(i, 15, 120) * (len(ts) - 1))) + 1)
        curve.set_data(ts[:m], ys[:m])
        dot.set_data([tc], [yc])
        if grow:
            cnt_d = int(round(M * yc / ymax_curve))
            sc.set_offsets(pos[:max(1, min(M, cnt_d))])
        else:
            alive = int(round(M * yc / y0))
            sc.set_facecolors(np.where((rank < alive)[:, None], alive_c, dead_c))
        cnt.set_text(f"y ≈ {_n(yc, 1)}")
        clock.set_text(f"t = {_n(tc, 2)}")
        for tj, vl, pt, lb in marks:
            on = tc >= tj - 1e-9
            vl.set_visible(on)
            pt.set_visible(on)
            lb.set_visible(on)
        if i >= 120:
            fin.set_data([te], [yv])
            finl.set_data([0, te], [yv, yv])
            fint.set_position((te * 0.97, yv + ymax_curve * 0.05))
            fint.set_text(f"y({_n(te)}) {eqs} {_n(yv, 2)}")
        else:
            fin.set_data([], [])
            finl.set_data([], [])
            fint.set_text("")
        if i < 15:
            info.set_text(l1)
        elif i < 120:
            info.set_text(l1 + "\n" + l2)
        else:
            info.set_text(l2 + "\n" + l3)
        return []

    return N, update


def vary(P, rnd):
    Q = dict(P)
    grow = float(_kexpr(P)) > 0
    sgn = "" if grow else "-"
    if isinstance(P.get("k"), str):
        T = math.log(2) / abs(float(_kexpr(P)))
        Tn = int(round(T)) if abs(T - round(T)) < 1e-9 else round(T, 4)
        Q["t_end"] = Tn * rnd.choice([2, 3, 4, 5])
        Q["y0"] = rnd.choice([100, 200, 250, 400, 500, 800, 1000] if grow else [16, 32, 40, 64, 80, 160, 200])
    else:
        kk = rnd.choice([0.02, 0.03, 0.04, 0.05, 0.08, 0.1, 0.12, 0.2])
        Q["k"] = kk if grow else -kk
        Q["t_end"] = rnd.choice([5, 8, 10, 12, 15, 20])
        Q["y0"] = rnd.choice([2000, 5000, 8000, 12000, 20000, 50000])
    return Q
''',
}
EXAMPLES += [
    {"id": "diffeq-exp-1", "kind": "exp_growth_decay",
     "topics": ["bacteria", "bakteri", "doubling"],
     "title": ("Bakteri kültürü", "Bacteria culture"),
     "q": ("Bir bakteri kültürü {y0} hücreyle başlıyor ve her {T} saatte ikiye katlanıyor "
           "(dy/dt = k·y, k = {kk}). {t_end} saat sonra kaç bakteri olur?",
           "A bacteria culture starts with {y0} cells and doubles every {T} hours "
           "(dy/dt = k·y, k = {kk}). How many bacteria are there after {t_end} hours?"),
     "P": {"y0": 500, "k": "ln(2)/3", "t_end": 12, "scene": "bacteria"}},
    {"id": "diffeq-exp-2", "kind": "exp_growth_decay",
     "topics": ["carbon dating", "half-life", "karbon"],
     "title": ("Radyoaktif bozunma: karbon-14", "Radioactive decay: carbon-14"),
     "q": ("Karbon-14'ün yarı ömrü {T} yıldır (k = {kk}). {y0} mg'lık bir numuneden {t_end} yıl sonra "
           "ne kadar kalır?",
           "Carbon-14 has a half-life of {T} years (k = {kk}). How much of a sample of {y0} mg is left "
           "after {t_end} years?"),
     "P": {"y0": 80, "k": "-ln(2)/5730", "t_end": 17190, "scene": "atoms"}},
    {"id": "diffeq-exp-3", "kind": "exp_growth_decay",
     "topics": ["population", "nüfus", "continuous growth"],
     "title": ("Sürekli nüfus artışı", "Continuous population growth"),
     "q": ("Bir kasabanın nüfusu {y0} kişi ve sürekli büyüme oranı k = {k} (1/yıl). dy/dt = k·y modeline "
           "göre {t_end} yıl sonra nüfus kaç olur? İkiye katlanma süresi nedir?",
           "A town has {y0} people and a continuous growth rate k = {k} per year. Using dy/dt = k·y, "
           "what is the population after {t_end} years, and what is the doubling time?"),
     "P": {"y0": 12000, "k": 0.03, "t_end": 10, "scene": "population"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["newton_cooling"] = {
    "course": "diffeq",
    "title": ("Newton'un soğuma yasası", "Newton's law of cooling"),
    "topics": ["newton's law of cooling", "law of cooling", "newton cooling", "cooling", "heating and cooling",
               "temperature", "ambient temperature", "newton'un soğuma yasası", "soğuma yasası", "soğuma",
               "ısınma", "sıcaklık", "ortam sıcaklığı"],
    "code": _FMT + r'''
from matplotlib.patches import Polygon, Rectangle, Circle, Arc


def _vals(P):
    T0, Ta, k = float(P["T0"]), float(P["Ta"]), float(P["k"])
    if k <= 0 or T0 == Ta:
        raise ValueError("k > 0 ve T0 ≠ Ta olmalı / need k > 0 and T0 ≠ Ta")
    t1 = float(P.get("t1", 10))
    Tt = P.get("T_target")
    tt = None
    if Tt is not None:
        Tt = float(Tt)
        if min(T0, Ta) < Tt < max(T0, Ta):
            tt = math.log((T0 - Ta) / (Tt - Ta)) / k
        else:
            Tt = None
    return T0, Ta, k, t1, Tt, tt


def _T(T0, Ta, k, t):
    return Ta + (T0 - Ta) * np.exp(-k * np.asarray(t, dtype=float))


def solve(P):
    T0, Ta, k, t1, Tt, tt = _vals(P)
    d = T0 - Ta
    s0, sa, sk, s1 = _n(T0), _n(Ta), _n(k, 4), _n(t1)
    T1 = float(_T(T0, Ta, k, t1))
    ex = math.exp(-k * t1)
    TT = _affine(Ta, d, "e^(−" + sk + "·t)")
    T1a = _affine(Ta, d, "e^(−" + _n(k * t1, 4) + ")")
    T1b = _affine(Ta, d, f"{ex:.4f}")
    steps = [(f"Newton: dT/dt = −k·(T − Tₐ),  Tₐ = {sa} °C,  k = {sk},  T(0) = {s0} °C",
              f"Newton: dT/dt = −k·(T − Tₐ),  Tₐ = {sa} °C,  k = {sk},  T(0) = {s0} °C"),
             ("Ayrılabilir: dT/(T − Tₐ) = −k·dt ⇒ ln|T − Tₐ| = −k·t + C ⇒ T = Tₐ + C·e^(−k·t)",
              "Separable: dT/(T − Tₐ) = −k·dt ⇒ ln|T − Tₐ| = −k·t + C ⇒ T = Tₐ + C·e^(−k·t)"),
             (f"T(0) = {s0} ⇒ C = {s0} − {sa} = {_n(d)} ⇒ T(t) = {TT}",
              f"T(0) = {s0} ⇒ C = {s0} − {sa} = {_n(d)} ⇒ T(t) = {TT}"),
             (f"T({s1}) = {T1a} = {T1b} ≈ {_n(T1)} °C", f"T({s1}) = {T1a} = {T1b} ≈ {_n(T1)} °C")]
    ans_tr = f"T({s1}) ≈ {_n(T1)} °C"
    ans_en = ans_tr
    if Tt is not None:
        st, q = _n(Tt), (Tt - Ta) / d
        steps.append((f"T(t) = {st} ⇒ e^(−{sk}·t) = ({st} − {sa})/({_n(d)}) = {q:.4f} ⇒ "
                       f"t = ln({_n(1 / q, 4)})/{sk} ≈ {_n(tt)} dk",
                       f"T(t) = {st} ⇒ e^(−{sk}·t) = ({st} − {sa})/({_n(d)}) = {q:.4f} ⇒ "
                       f"t = ln({_n(1 / q, 4)})/{sk} ≈ {_n(tt)} min"))
        ans_tr += f";  T = {st} °C için t ≈ {_n(tt)} dk"
        ans_en += f";  T = {st} °C at t ≈ {_n(tt)} min"
    steps.append((f"t → ∞ iken e^(−k·t) → 0 ⇒ T → Tₐ = {sa} °C ({'soğur' if d > 0 else 'ısınır'})",
                  f"As t → ∞, e^(−k·t) → 0 ⇒ T → Tₐ = {sa} °C ({'cools down' if d > 0 else 'warms up'})"))
    return {"answer": (ans_tr, ans_en), "steps": steps, "fmt": {}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T0, Ta, k, t1, Tt, tt = _vals(P)
    cool = T0 > Ta
    tm = max(t1, tt or 0.0)
    tmax = max(1.35 * tm, min(3.0 / k, 5.0 * tm))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.5], left=0.02, right=0.97, bottom=0.12, top=0.9,
                          wspace=0.14)
    axL = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[0, 1])
    axL.set_xlim(0, 10)
    axL.set_ylim(0, 10)
    axL.set_aspect("equal")
    axL.axis("off")
    axL.plot([1.2, 7.6], [1.35, 1.35], color="#9CA3AF", lw=6, solid_capstyle="round")
    axL.add_patch(Arc((6.95, 4.0), 1.9, 2.3, theta1=-80, theta2=80, color="#6B7280", lw=4.5, zorder=2))
    axL.add_patch(Polygon([(1.9, 6.4), (2.4, 1.5), (6.4, 1.5), (6.9, 6.4)], closed=True, fc="#F9FAFB",
                          ec="#6B7280", lw=2.5, zorder=3))
    liquid = Polygon([(2.1, 5.7), (2.52, 1.72), (6.28, 1.72), (6.7, 5.7)], closed=True, fc="#DC2626",
                     ec="none", zorder=4)
    axL.add_patch(liquid)
    steam = [axL.plot([], [], color="#9CA3AF", lw=2.2, solid_capstyle="round", zorder=5)[0] for _ in range(3)]
    Tlo = min(T0, Ta) - 0.15 * abs(T0 - Ta)
    Thi = max(T0, Ta) + 0.12 * abs(T0 - Ta)
    axL.add_patch(Rectangle((8.62, 2.0), 0.56, 6.7, fc="white", ec="#6B7280", lw=1.5, zorder=3))
    axL.add_patch(Circle((8.9, 1.72), 0.45, fc="#DC2626", ec="#6B7280", lw=1.5, zorder=4))
    merc = Rectangle((8.76, 2.0), 0.28, 0.1, fc="#DC2626", ec="none", zorder=4)
    axL.add_patch(merc)
    ya = 2.0 + 6.7 * (Ta - Tlo) / (Thi - Tlo)
    axL.plot([8.45, 8.62], [ya, ya], color="#6B7280", lw=2)
    axL.text(8.4, ya, "Tₐ", ha="right", va="center", fontsize=9, color="#6B7280")
    Ttxt = axL.text(8.9, 9.05, "", ha="center", fontsize=11, fontweight="bold", color="#111827")
    clock = axL.text(0.2, 9.1, "", ha="left", fontsize=11, color="#374151")
    axL.text(4.4, 0.35, (f"Ortam: {_n(Ta)} °C" if tr else f"Room: {_n(Ta)} °C"), ha="center", fontsize=10,
             color="#6B7280")
    ts = np.linspace(0, tmax, 400)
    Ts = _T(T0, Ta, k, ts)
    ax.set_xlim(0, tmax)
    lo, hi = min(T0, Ta), max(T0, Ta)
    span = hi - lo
    ax.set_ylim(lo - 0.12 * span, hi + 0.42 * span)
    ax.grid(alpha=0.3)
    ax.set_xlabel("t (dk)" if tr else "t (min)")
    ax.set_ylabel("T (°C)")
    d = T0 - Ta
    TT = _affine(Ta, d, "e^(−" + _n(k, 4) + "t)")
    ax.set_title(f"T(t) = {TT}", fontsize=12)
    ax.axhline(Ta, color="#6B7280", ls="--", lw=1.3)
    ax.text(tmax * 0.02, Ta + (0.03 if cool else -0.03) * span, (f"Tₐ = {_n(Ta)} °C"), ha="left",
            va="bottom" if cool else "top", color="#6B7280", fontsize=10)
    curve, = ax.plot([], [], color="#E07B39", lw=2.6)
    dot, = ax.plot([], [], "o", color="#E07B39", ms=8, zorder=6)
    T1 = float(_T(T0, Ta, k, t1))
    m1, = ax.plot([], [], "o", color="#7C3AED", ms=10, zorder=7)
    m1l, = ax.plot([], [], ":", color="#7C3AED", lw=1.3)
    m1t = ax.text(t1, T1, "", color="#7C3AED", fontsize=11, fontweight="bold",
                  va="bottom" if cool else "top", ha="left")
    m2, = ax.plot([], [], "s", color="#16A34A", ms=9, zorder=7)
    m2l, = ax.plot([], [], ":", color="#16A34A", lw=1.3)
    m2t = ax.text(0, 0, "", color="#16A34A", fontsize=11, fontweight="bold",
                  va="top" if cool else "bottom", ha="right")
    info = _box(ax, x=0.98, ha="right")
    l1 = (f"1) dT/dt = −k·(T − Tₐ),  k = {_n(k, 4)}")
    l2 = f"2) T(t) = {TT}"
    l3 = f"3) T({_n(t1)}) ≈ {_n(T1)} °C"
    if Tt is not None:
        l3 += (f";  T = {_n(Tt)} °C ⇒ t ≈ {_n(tt)} dk" if tr else f";  T = {_n(Tt)} °C ⇒ t ≈ {_n(tt)} min")
    unit = "dk" if tr else "min"
    sy = np.linspace(6.7, 9.0, 30)
    N = 150

    def update(i):
        tc = tmax * _ramp(i, 12, 118)
        Tc = float(_T(T0, Ta, k, tc))
        m = max(1, int(round(_ramp(i, 12, 118) * (len(ts) - 1))) + 1)
        curve.set_data(ts[:m], Ts[:m])
        dot.set_data([tc], [Tc])
        liquid.set_facecolor(_mix("#2563EB", "#DC2626", Tc / 100.0))
        hot = (Tc - Ta) / (T0 - Ta) if cool else 0.0
        for j, ln in enumerate(steam):
            xc = 3.2 + 1.2 * j
            ln.set_data(xc + 0.22 * np.sin(2.6 * sy - 0.35 * i + j), sy)
            ln.set_alpha(max(0.0, min(0.85, 0.85 * hot)))
        merc.set_height(max(0.05, 6.7 * (Tc - Tlo) / (Thi - Tlo)))
        Ttxt.set_text(f"{_n(Tc, 1)} °C")
        clock.set_text(f"t = {tc:.1f} {unit}")
        if tc >= t1 - 1e-9:
            m1.set_data([t1], [T1])
            m1l.set_data([t1, t1], [ax.get_ylim()[0], T1])
            m1t.set_position((t1 + tmax * 0.015, T1 + (0.04 if cool else -0.04) * span))
            m1t.set_text(f"T({_n(t1)}) ≈ {_n(T1, 1)}")
        else:
            m1.set_data([], [])
            m1l.set_data([], [])
            m1t.set_text("")
        if Tt is not None and tc >= tt - 1e-9:
            m2.set_data([tt], [Tt])
            m2l.set_data([0, tt], [Tt, Tt])
            m2t.set_position((tt - tmax * 0.015, Tt - (0.04 if cool else -0.04) * span))
            m2t.set_text(f"t ≈ {_n(tt, 1)} {unit}")
        else:
            m2.set_data([], [])
            m2l.set_data([], [])
            m2t.set_text("")
        if i < 12:
            info.set_text(l1)
        elif i < 118:
            info.set_text(l1 + "\n" + l2)
        else:
            info.set_text(l2 + "\n" + l3)
        return []

    return N, update


def vary(P, rnd):
    Q = dict(P)
    cool = float(P["T0"]) > float(P["Ta"])
    Ta = rnd.choice([18, 20, 22, 24, 25])
    if cool:
        T0 = max(Ta + 30, int(P["T0"]) + rnd.choice([-20, -10, -5, 5, 10, 20]))
    else:
        T0 = rnd.choice([2, 4, 5, 6, 8])
    k = rnd.choice([0.04, 0.05, 0.06, 0.08, 0.1, 0.12])
    Q.update({"T0": T0, "Ta": Ta, "k": k, "t1": rnd.choice([5, 8, 10, 12, 15])})
    if "T_target" in P:
        lo, hi = min(T0, Ta), max(T0, Ta)
        Q["T_target"] = int(round(lo + (hi - lo) * rnd.choice([0.3, 0.4, 0.5, 0.6])))
    return Q
''',
}
EXAMPLES += [
    {"id": "diffeq-cool-1", "kind": "newton_cooling",
     "topics": ["coffee", "kahve"],
     "title": ("Soğuyan kahve", "Cooling coffee"),
     "q": ("{T0} °C sıcaklıktaki bir kahve, sıcaklığı {Ta} °C olan bir odada soğuyor (k = {k} 1/dk). "
           "{t1} dakika sonra kahvenin sıcaklığı kaç olur? Kahve ne zaman {T_target} °C'ye iner?",
           "A cup of coffee at {T0} °C cools in a room at {Ta} °C (k = {k} per minute). What is its "
           "temperature after {t1} minutes, and when does it reach {T_target} °C?"),
     "P": {"T0": 90, "Ta": 20, "k": 0.05, "t1": 10, "T_target": 50}},
    {"id": "diffeq-cool-2", "kind": "newton_cooling",
     "topics": ["warming", "ısınma"],
     "title": ("Isınan soğuk içecek", "A cold drink warming up"),
     "q": ("Buzdolabından çıkan {T0} °C'lik bir içecek {Ta} °C'lik ortamda ısınıyor (k = {k} 1/dk). "
           "{t1} dakika sonra sıcaklığı nedir ve ne zaman {T_target} °C olur?",
           "A drink taken out of the fridge at {T0} °C warms up in a {Ta} °C room (k = {k} per minute). "
           "What is its temperature after {t1} minutes, and when does it reach {T_target} °C?"),
     "P": {"T0": 4, "Ta": 24, "k": 0.1, "t1": 5, "T_target": 14}},
    {"id": "diffeq-cool-3", "kind": "newton_cooling",
     "topics": ["oven", "fırın"],
     "title": ("Fırından çıkan kek", "A cake out of the oven"),
     "q": ("Fırından {T0} °C'de çıkan bir kek {Ta} °C'lik mutfakta soğuyor (k = {k} 1/dk). "
           "{t1} dakika sonra sıcaklığı kaç derecedir? Kek ne zaman {T_target} °C'ye düşer?",
           "A cake leaves the oven at {T0} °C and cools in a {Ta} °C kitchen (k = {k} per minute). "
           "What is its temperature after {t1} minutes, and when does it drop to {T_target} °C?"),
     "P": {"T0": 180, "Ta": 22, "k": 0.08, "t1": 15, "T_target": 40}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["logistic"] = {
    "course": "diffeq",
    "title": ("Lojistik büyüme", "Logistic growth"),
    "topics": ["logistic", "logistic growth", "logistic equation", "logistic model", "logistic differential",
               "carrying capacity", "population model", "limited growth", "lojistik", "lojistik büyüme",
               "lojistik denklem", "taşıma kapasitesi", "sınırlı büyüme", "nüfus modeli"],
    "code": _FMT + r'''
from fractions import Fraction
from matplotlib.collections import LineCollection


def _vals(P):
    P0, r, K = float(P["P0"]), float(P["r"]), float(P["K"])
    if P0 <= 0 or r <= 0 or K <= 0:
        raise ValueError("P0, r, K pozitif olmalı / P0, r, K must be positive")
    t1 = float(P.get("t1", 10))
    A = (K - P0) / P0
    ts = math.log(A) / r if A > 0 else None
    return P0, r, K, t1, A, ts


def _P(P0, r, K, t):
    A = (K - P0) / P0
    return K / (1 + A * np.exp(-r * np.asarray(t, dtype=float)))


def _fs(v):
    fr = Fraction(v).limit_denominator(1000)
    if abs(float(fr) - v) > 1e-9:
        return _n(v, 4)
    return str(fr.numerator) if fr.denominator == 1 else f"{fr.numerator}/{fr.denominator}"


def _den(A, body):
    mag = _fs(abs(A))
    if "/" in mag:
        mag = "(" + mag + ")"
    term = body if mag == "1" else f"{mag}·{body}"
    return f"1 {'+' if A >= 0 else '−'} {term}"


def solve(P):
    P0, r, K, t1, A, ts = _vals(P)
    sP, sr, sK, s1, sA = _n(P0), _n(r, 4), _n(K), _n(t1), _fs(A)
    P1 = float(_P(P0, r, K, t1))
    dn = _den(A, "e^(−" + sr + "t)")
    dn1 = _den(A, "e^(−" + _n(r * t1, 4) + ")")
    steps = [(f"Lojistik model: dP/dt = r·P·(1 − P/K),  r = {sr},  K = {sK},  P(0) = {sP}",
              f"Logistic model: dP/dt = r·P·(1 − P/K),  r = {sr},  K = {sK},  P(0) = {sP}"),
             ("Ayır ve kısmi kesirlere böl: ∫ [1/P + 1/(K − P)] dP = ∫ r dt ⇒ ln|P/(K − P)| = r·t + C",
              "Separate and use partial fractions: ∫ [1/P + 1/(K − P)] dP = ∫ r dt ⇒ ln|P/(K − P)| = r·t + C"),
             (f"P(t) = K / (1 + A·e^(−r·t)),  A = (K − P₀)/P₀ = ({sK} − {sP})/{sP} = {sA}",
              f"P(t) = K / (1 + A·e^(−r·t)),  A = (K − P₀)/P₀ = ({sK} − {sP})/{sP} = {sA}"),
             (f"P(t) = {sK} / ({dn})", f"P(t) = {sK} / ({dn})")]
    if ts is not None and ts > 0:
        steps.append((f"Dönüm noktası P = K/2 = {_n(K / 2)} olduğunda: e^(−r·t) = 1/A ⇒ t = ln(A)/r = "
                      f"ln({sA})/{sr} ≈ {_n(ts)};  en büyük hız r·K/4 = {_n(r * K / 4)}",
                      f"Inflection point when P = K/2 = {_n(K / 2)}: e^(−r·t) = 1/A ⇒ t = ln(A)/r = "
                      f"ln({sA})/{sr} ≈ {_n(ts)};  maximum rate r·K/4 = {_n(r * K / 4)}"))
    elif P0 < K:
        steps.append(("P₀ ≥ K/2: büyüme hızı başlangıçtan itibaren azalır (t > 0 için dönüm noktası yok)",
                      "P₀ ≥ K/2: the growth rate decreases from the start (no inflection for t > 0)"))
    else:
        steps.append(("P₀ > K: dP/dt < 0, nüfus K'ya doğru azalır (dönüm noktası yok)",
                      "P₀ > K: dP/dt < 0, the population decreases toward K (no inflection point)"))
    steps.append((f"P({s1}) = {sK} / ({dn1}) ≈ {_n(P1)}", f"P({s1}) = {sK} / ({dn1}) ≈ {_n(P1)}"))
    steps.append((f"t → ∞ iken P → K = {sK} (taşıma kapasitesi)", f"As t → ∞, P → K = {sK} (carrying capacity)"))
    a_tr = f"P({s1}) ≈ {_n(P1)}"
    a_en = a_tr
    if ts is not None and ts > 0:
        a_tr += f";  dönüm noktası t ≈ {_n(ts)} (P = {_n(K / 2)})"
        a_en += f";  inflection at t ≈ {_n(ts)} (P = {_n(K / 2)})"
    return {"answer": (a_tr, a_en), "steps": steps, "fmt": {"A": sA}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    P0, r, K, t1, A, ts = _vals(P)
    infl = ts is not None and ts > 0
    tmax = max(1.15 * t1, (ts if infl else 0.0) + 5.0 / r)
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.55], left=0.08, right=0.97, bottom=0.12, top=0.9,
                          wspace=0.24)
    axL = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[0, 1])
    Pm = max(P0, K) * 1.12
    pp = np.linspace(0, Pm, 300)
    rate = r * pp * (1 - pp / K)
    axL.plot(pp, rate, color="#7C3AED", lw=2.2)
    axL.axhline(0, color="#6B7280", lw=1)
    axL.set_xlim(0, Pm)
    rlo, rhi = float(rate.min()), r * K / 4
    axL.set_ylim(min(rlo, -0.08 * rhi) * 1.1, rhi * 1.35)
    axL.grid(alpha=0.3)
    axL.set_xlabel("P")
    axL.set_ylabel("dP/dt")
    axL.set_title("Büyüme hızı" if tr else "Growth rate", fontsize=11)
    axL.plot([K / 2], [rhi], "*", color="#16A34A", ms=13, zorder=5)
    axL.text(K / 2, rhi * 1.08, f"K/2 = {_n(K / 2)}", ha="center", color="#16A34A", fontsize=9)
    axL.plot([K], [0], "o", color="#DC2626", ms=7)
    axL.text(K, rhi * 0.08, "K", ha="center", color="#DC2626", fontsize=10, fontweight="bold")
    rdot, = axL.plot([], [], "o", color="#2563EB", ms=9, zorder=6)
    ts_ = np.linspace(0, tmax, 400)
    Ps = _P(P0, r, K, ts_)
    ax.set_xlim(0, tmax)
    top = max(P0, K) * 1.3
    ax.set_ylim(0, top)
    W, H = tmax, top
    fw, fh = fig.get_size_inches()
    pos = ax.get_position()
    ratio = (pos.height * fh / H) / (pos.width * fw / W)
    nx, ny = 20, 13
    gx = (np.arange(nx) + 0.5) * W / nx
    gy = (np.arange(ny) + 0.5) * H / ny
    GX, GY = np.meshgrid(gx, gy, indexing="ij")
    S = r * GY * (1 - GY / K)
    ang = np.arctan(S * ratio)
    L = 0.34 * W / nx
    dx, dy = L * np.cos(ang), L * np.sin(ang) / ratio
    segs = np.stack([np.stack([GX - dx, GY - dy], -1), np.stack([GX + dx, GY + dy], -1)], -2).reshape(-1, 2, 2)
    ax.add_collection(LineCollection(segs, colors="#9CA3AF", linewidths=1.0, alpha=0.6, zorder=1))
    ax.axhline(K, color="#DC2626", ls="--", lw=1.4)
    ax.text(tmax * 0.99, K + top * 0.015, f"K = {_n(K)}", ha="right", va="bottom", color="#DC2626", fontsize=10)
    ax.axhline(K / 2, color="#6B7280", ls=":", lw=1.2)
    ax.text(tmax * 0.99, K / 2 + top * 0.015, "K/2", ha="right", va="bottom", color="#6B7280", fontsize=9)
    ax.grid(alpha=0.25)
    ax.set_xlabel("t")
    ax.set_ylabel("P(t)")
    dn = _den(A, "e^(−" + _n(r, 4) + "t)")
    ax.set_title(f"P(t) = {_n(K)} / ({dn})", fontsize=11)
    curve, = ax.plot([], [], color="#2563EB", lw=2.6, zorder=4)
    dot, = ax.plot([], [], "o", color="#2563EB", ms=8, zorder=6)
    istar, = ax.plot([], [], "*", color="#16A34A", ms=16, zorder=7)
    itxt = ax.text(0, 0, "", color="#16A34A", fontsize=10, fontweight="bold", ha="left", va="top")
    P1 = float(_P(P0, r, K, t1))
    m1, = ax.plot([], [], "o", color="#7C3AED", ms=10, zorder=7)
    m1l, = ax.plot([], [], ":", color="#7C3AED", lw=1.3)
    m1t = ax.text(0, 0, "", color="#7C3AED", fontsize=11, fontweight="bold", ha="left")
    info = _box(ax)
    l1 = "1) dP/dt = r·P·(1 − P/K)"
    if P0 < K:
        l2 = ("2) Önce hızlı büyüme, K'ya yaklaştıkça yavaşlama" if tr else
              "2) Fast growth first, slowing down near K")
    else:
        l2 = "2) P > K: nüfus K'ya doğru azalır" if tr else "2) P > K: the population decreases toward K"
    l3 = f"3) P({_n(t1)}) ≈ {_n(P1)}" + ((f";  dönüm t ≈ {_n(ts)}" if tr else f";  inflection t ≈ {_n(ts)}")
                                         if infl else "")
    N = 150

    def update(i):
        tc = tmax * _ramp(i, 15, 115)
        Pc = float(_P(P0, r, K, tc))
        m = max(1, int(round(_ramp(i, 15, 115) * (len(ts_) - 1))) + 1)
        curve.set_data(ts_[:m], Ps[:m])
        dot.set_data([tc], [Pc])
        rdot.set_data([Pc], [r * Pc * (1 - Pc / K)])
        if infl and tc >= ts - 1e-9:
            istar.set_data([ts], [K / 2])
            itxt.set_position((ts + tmax * 0.02, K / 2 - top * 0.02))
            itxt.set_text((f"dönüm noktası (t ≈ {_n(ts, 1)})" if tr else f"inflection (t ≈ {_n(ts, 1)})"))
        else:
            istar.set_data([], [])
            itxt.set_text("")
        if i >= 115:
            m1.set_data([t1], [P1])
            m1l.set_data([t1, t1], [0, P1])
            m1t.set_position((t1 + tmax * 0.015, P1 + top * (-0.07 if P0 < K else 0.04)))
            m1t.set_text(f"P({_n(t1)}) ≈ {_n(P1, 1)}")
        else:
            m1.set_data([], [])
            m1l.set_data([], [])
            m1t.set_text("")
        if i < 15:
            info.set_text(l1)
        elif i < 115:
            info.set_text(l1 + "\n" + l2)
        else:
            info.set_text(l3)
        return []

    return N, update


def vary(P, rnd):
    Q = dict(P)
    K = rnd.choice([400, 500, 800, 1000, 2000, 5000])
    if float(P["P0"]) > float(P["K"]):
        Q["P0"] = int(K * rnd.choice([1.25, 1.5, 1.6, 2]))
    else:
        Q["P0"] = K // rnd.choice([10, 20, 25, 40, 50])
    Q["K"] = K
    Q["r"] = rnd.choice([0.2, 0.3, 0.4, 0.5, 0.6, 0.8])
    Q["t1"] = rnd.choice([4, 5, 6, 8, 10])
    return Q
''',
}
EXAMPLES += [
    {"id": "diffeq-logistic-1", "kind": "logistic",
     "topics": ["fish", "balık"],
     "title": ("Göldeki balık nüfusu", "Fish population in a lake"),
     "q": ("Bir göle {P0} balık bırakılıyor. Göl en fazla {K} balık besleyebiliyor ve büyüme oranı r = {r} "
           "(1/yıl). Lojistik modele göre {t1} yıl sonra kaç balık olur? Nüfus en hızlı ne zaman artar?",
           "{P0} fish are released into a lake that can support at most {K} fish; the growth rate is "
           "r = {r} per year. Using the logistic model, how many fish are there after {t1} years? When is "
           "the population growing fastest?"),
     "P": {"P0": 100, "r": 0.4, "K": 1000, "t1": 10}},
    {"id": "diffeq-logistic-2", "kind": "logistic",
     "topics": ["spread of a rumor", "epidemic", "söylenti", "salgın"],
     "title": ("Söylentinin yayılması", "Spread of a rumor"),
     "q": ("{K} öğrencili bir okulda bir söylenti {P0} kişiyle başlıyor ve dP/dt = {r}·P·(1 − P/{K}) "
           "ile yayılıyor (t gün). {t1} gün sonra kaç kişi duymuştur?",
           "In a school of {K} students a rumor starts with {P0} people and spreads according to "
           "dP/dt = {r}·P·(1 − P/{K}) (t in days). How many have heard it after {t1} days?"),
     "P": {"P0": 5, "r": 0.9, "K": 500, "t1": 6}},
    {"id": "diffeq-logistic-3", "kind": "logistic",
     "title": ("Taşıma kapasitesinin üzerinde başlangıç", "Starting above the carrying capacity"),
     "q": ("dP/dt = {r}·P·(1 − P/{K}), P(0) = {P0}. Nüfus taşıma kapasitesinin üzerinde başlıyor: "
           "P({t1}) nedir ve uzun vadede ne olur?",
           "dP/dt = {r}·P·(1 − P/{K}), P(0) = {P0}. The population starts above the carrying capacity: "
           "find P({t1}) and describe the long-term behaviour."),
     "P": {"P0": 1500, "r": 0.5, "K": 1000, "t1": 4}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["spring_mass"] = {
    "course": "diffeq",
    "title": ("Kütle-yay sistemi (sönümlü titreşim)", "Mass-spring system (damped vibration)"),
    "topics": ["spring", "mass-spring", "spring mass", "mass on a spring", "damped", "damping",
               "harmonic motion", "simple harmonic", "mechanical vibrations", "vibration", "oscillation",
               "underdamped", "overdamped", "critically damped", "yay", "kütle-yay", "sönümlü", "sönüm",
               "salınım", "harmonik hareket", "titreşim", "mekanik titreşim"],
    "code": _FMT + _SECOND + r'''
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator


def _spring(P):
    if float(P["m"]) <= 0 or float(P["k"]) <= 0 or float(P["c"]) < 0:
        raise ValueError("m > 0, k > 0, c ≥ 0 olmalı / need m > 0, k > 0, c ≥ 0")
    S = _sol2(P["m"], P["c"], P["k"], P["x0"], P["v0"], "x")
    if S["case"] == "complex":
        om, al = float(S["om"]), float(S["al"])
        Tq = 2 * math.pi / om
        te = min(6 * Tq, max(2 * Tq, math.log(25) / -al)) if al < 0 else 3 * Tq
        S["Tq"] = Tq
    else:
        sig = min(abs(float(r)) for r in S["roots"])
        te = min(40.0, max(1.0, math.log(60) / sig)) if sig > 1e-9 else 10.0
        S["Tq"] = None
    S["t_end"] = te
    S["undamped"] = float(P["c"]) == 0
    return S


def _cls(S):
    if S["undamped"]:
        return ("sönümsüz (basit harmonik hareket)", "undamped (simple harmonic motion)")
    return {"complex": ("az sönümlü: genliği azalan salınım", "underdamped: oscillation with decaying amplitude"),
            "double": ("kritik sönümlü: salınım yok, en hızlı dönüş", "critically damped: no oscillation, fastest return"),
            "real": ("aşırı sönümlü: salınım yok, yavaş dönüş", "overdamped: no oscillation, slow return")}[S["case"]]


def _short(S):
    if S["undamped"]:
        return ("sönümsüz", "undamped")
    return {"complex": ("az sönümlü", "underdamped"), "double": ("kritik sönümlü", "critically damped"),
            "real": ("aşırı sönümlü", "overdamped")}[S["case"]]


def solve(P):
    S = _spring(P)
    m, c, k = S["a"], S["b"], S["c"]
    ode = _join([(m, "x''"), (c, "x'"), (k, "x")]) + " = 0"
    char = _join([(m, "r²"), (c, "r"), (k, "")]) + " = 0"
    zeta = float(c) / (2 * math.sqrt(float(m) * float(k)))
    cl = _cls(S)
    x0s, v0s = _ps(S["y0"]), _ps(S["v0"])
    steps = [(f"m·x'' + c·x' + k·x = 0:  {ode},  x(0) = {x0s} m,  x'(0) = {v0s} m/s",
              f"m·x'' + c·x' + k·x = 0:  {ode},  x(0) = {x0s} m,  x'(0) = {v0s} m/s"),
             (f"x = e^(rt) dene ⇒ karakteristik denklem: {char}",
              f"Try x = e^(rt) ⇒ characteristic equation: {char}"),
             (f"Δ = c² − 4mk = {_ps(c * c)} − {_pp(4 * m * k)} = {_ps(S['D'])}  ⇒  {S['rtxt'][0]}",
              f"Δ = c² − 4mk = {_ps(c * c)} − {_pp(4 * m * k)} = {_ps(S['D'])}  ⇒  {S['rtxt'][1]}"),
             (f"Sönüm oranı ζ = c / (2√(mk)) = {zeta:.3g} ⇒ {cl[0]}",
              f"Damping ratio ζ = c / (2√(mk)) = {zeta:.3g} ⇒ {cl[1]}"),
             (f"Genel çözüm: x(t) = {S['gen']}", f"General solution: x(t) = {S['gen']}"),
             S["cst"],
             (f"Özel çözüm: x(t) = {S['part']}", f"Particular solution: x(t) = {S['part']}")]
    if S["Tq"] is not None:
        nm = ("periyot" if S["undamped"] else "sanki-periyot", "period" if S["undamped"] else "quasi-period")
        steps.append((f"ω = {_ps(S['om'])} rad/s ⇒ {nm[0]} T = 2π/ω ≈ {S['Tq']:.3f} s",
                      f"ω = {_ps(S['om'])} rad/s ⇒ {nm[1]} T = 2π/ω ≈ {S['Tq']:.3f} s"))
    sh = _short(S)
    return {"answer": (f"x(t) = {S['part']}  ({sh[0]})", f"x(t) = {S['part']}  ({sh[1]})"),
            "steps": steps, "fmt": {"ode": ode}}


def _coil(yT, yB, xc, w, n):
    Lg = yT - yB
    ys = [yT, yT - 0.1 * Lg]
    xs = [xc, xc]
    for j in range(n):
        ys.append(yT - 0.1 * Lg - (j + 0.5) * 0.8 * Lg / n)
        xs.append(xc + (w if j % 2 == 0 else -w))
    ys += [yB + 0.1 * Lg, yB]
    xs += [xc, xc]
    return xs, ys


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _spring(P)
    lam, te = S["lam"], S["t_end"]
    tt = np.linspace(0, te, 700)
    xx = lam(tt)
    A = float(np.max(np.abs(xx[np.isfinite(xx)]))) if np.isfinite(xx).any() else 1.0
    A = A if A > 1e-9 else 1.0
    lo, hi = -1.35 * A, 2.05 * A
    gs = fig.add_gridspec(1, 2, width_ratios=[0.5, 1.5], left=0.02, right=0.97, bottom=0.12, top=0.9,
                          wspace=0.08)
    axL = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[0, 1])
    axL.set_xlim(-1, 1)
    axL.set_ylim(lo, hi)
    axL.axis("off")
    ceil = 1.78 * A
    axL.add_patch(Rectangle((-0.95, ceil), 1.9, 0.12 * A, fc="#E5E7EB", ec="#6B7280", hatch="///", lw=1))
    axL.plot([-1, 1], [0, 0], "--", color="#9CA3AF", lw=1)
    axL.text(-0.98, -0.07 * A, "denge" if tr else "equilibrium", fontsize=8, color="#6B7280", va="top")
    hb = 0.17 * A
    damper = float(P["c"]) > 0
    mx0, mw = (-0.58, 0.74) if damper else (-0.45, 0.9)
    xsp = mx0 + mw / 2
    xd = 0.42
    spr, = axL.plot([], [], color="#374151", lw=1.6, zorder=3)
    mass = Rectangle((mx0, -hb), mw, 2 * hb, fc="#2563EB", ec="#1E3A8A", lw=1.5, zorder=5)
    axL.add_patch(mass)
    mlab = axL.text(xsp, 0, f"{_ps(S['a'])} kg", color="white", ha="center", va="center", fontsize=9,
                    fontweight="bold", zorder=6)
    if damper:
        rod_len = 0.32 * A
        cb, ct = -A + hb + rod_len - 0.08 * A, A + hb + rod_len + 0.1 * A
        axL.add_patch(Rectangle((xd - 0.14, cb), 0.28, ct - cb, fc="#F3F4F6", ec="#6B7280", lw=1.4, zorder=2))
        axL.plot([xd, xd], [ct, ceil], color="#6B7280", lw=1.6)
        rod, = axL.plot([], [], color="#6B7280", lw=1.8, zorder=3)
        piston, = axL.plot([], [], color="#374151", lw=3.5, zorder=3)
    axL.text(0.0, lo + 0.01 * (hi - lo), (f"k = {_ps(S['c'])} N/m" + (f",  c = {_ps(S['b'])} N·s/m" if damper else "")),
             ha="center", va="bottom", fontsize=8, color="#374151")
    ax.set_xlim(0, te)
    ax.set_ylim(lo, hi)
    ax.set_yticks([v for v in MaxNLocator(5).tick_values(-A, A) if -1.3 * A <= v <= 1.3 * A])
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.set_xlabel("t (s)")
    ax.set_ylabel("x (m)")
    sh = _short(S)
    ax.set_title(f"x(t) = {S['part']}" if len(S["part"]) <= 52 else sh[0 if tr else 1], fontsize=11)
    guide, = ax.plot([], [], ":", color="#9CA3AF", lw=1.2)
    curve, = ax.plot([], [], color="#2563EB", lw=2.4)
    dot, = ax.plot([], [], "o", color="#DC2626", ms=8, zorder=6)
    env1, = ax.plot([], [], "--", color="#7C3AED", lw=1.2)
    env2, = ax.plot([], [], "--", color="#7C3AED", lw=1.2)
    if S["case"] == "complex" and float(S["al"]) < 0:
        Rm = math.sqrt(float(S["C1"]) ** 2 + float(S["C2"]) ** 2)
        envy = Rm * np.exp(float(S["al"]) * tt)
    else:
        envy = None
    info = _box(ax)
    read = ax.text(0.98, 0.03, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=10,
                   family="DejaVu Sans Mono", color="#374151",
                   bbox=dict(boxstyle="round", fc="#F9FAFB", ec="#D1D5DB", alpha=0.9))
    char = _join([(S["a"], "r²"), (S["b"], "r"), (S["c"], "")]) + " = 0"
    l1 = f"1) {char}  ⇒  {S['rshort']}"
    l2 = ("2) " + _cls(S)[0]) if tr else ("2) " + _cls(S)[1])
    l3 = f"3) x(t) = {S['part']}" if len(S["part"]) <= 46 else f"3) {S['rshort']}  ({sh[0 if tr else 1]})"
    N = 170

    def update(i):
        tc = te * _ramp(i, 20, 150)
        k_ = max(1, int(round(_ramp(i, 20, 150) * (len(tt) - 1))) + 1)
        xc = float(lam(np.array([tc]))[0])
        mass.set_y(xc - hb)
        mlab.set_position((xsp, xc))
        sx, sy = _coil(ceil, xc + hb, xsp, 0.16, 10)
        spr.set_data(sx, sy)
        if damper:
            rod.set_data([mx0 + mw - 0.06, xd, xd], [xc + hb, xc + hb, xc + hb + rod_len])
            piston.set_data([xd - 0.11, xd + 0.11], [xc + hb + rod_len, xc + hb + rod_len])
        curve.set_data(tt[:k_], xx[:k_])
        dot.set_data([tc], [xc])
        guide.set_data([0, tc], [xc, xc])
        read.set_text(f"t = {tc:5.2f} s   x = {xc:+.3f} m")
        if i >= 150 and envy is not None:
            env1.set_data(tt, envy)
            env2.set_data(tt, -envy)
        else:
            env1.set_data([], [])
            env2.set_data([], [])
        if i < 20:
            info.set_text(l1)
        elif i < 150:
            info.set_text(l1 + "\n" + l2)
        else:
            info.set_text(l2 + "\n" + l3)
        return []

    return N, update


def vary(P, rnd):
    S = _spring(P)
    case = "undamped" if float(P["c"]) == 0 else S["case"]
    m = rnd.choice([1, 1, 2])
    if case == "undamped":
        w = rnd.choice([2, 3, 4, 5])
        c, k = 0, m * w * w
    elif case == "complex":
        al, w = rnd.choice([1, 2]), rnd.choice([2, 3, 4])
        c, k = 2 * m * al, m * (al * al + w * w)
    elif case == "double":
        r = rnd.choice([1, 2, 3])
        c, k = 2 * m * r, m * r * r
    else:
        p, q = rnd.sample([1, 2, 3, 4, 5], 2)
        c, k = m * (p + q), m * p * q
    x0 = rnd.choice([0.5, 1, 1, 1.5, 2])
    v0 = rnd.choice([0, 0, 1, -1, 2])
    return {"m": m, "c": c, "k": k, "x0": x0, "v0": v0}
''',
}
EXAMPLES += [
    {"id": "diffeq-spring-1", "kind": "spring_mass",
     "topics": ["underdamped", "az sönümlü"],
     "title": ("Az sönümlü yay", "Underdamped spring"),
     "q": ("Kütlesi {m} kg olan bir cisim yay sabiti {k} N/m olan bir yaya bağlı ve sönüm katsayısı "
           "c = {c} N·s/m. Cisim denge konumundan {x0} m uzaklaştırılıp ilk hızı {v0} m/s olacak şekilde "
           "bırakılıyor. Hareket denklemini ({ode}) çöz ve hareketi sınıflandır.",
           "A {m} kg mass hangs on a spring with k = {k} N/m and damping coefficient c = {c} N·s/m. It is "
           "pulled {x0} m from equilibrium and released with initial velocity {v0} m/s. Solve the equation "
           "of motion ({ode}) and classify the motion."),
     "P": {"m": 1, "c": 2, "k": 10, "x0": 1, "v0": 0}},
    {"id": "diffeq-spring-2", "kind": "spring_mass",
     "topics": ["critically damped", "kritik sönümlü"],
     "title": ("Kritik sönüm", "Critical damping"),
     "q": ("m = {m} kg, c = {c} N·s/m, k = {k} N/m olan sistem için {ode} denklemini x(0) = {x0}, "
           "x'(0) = {v0} koşullarıyla çöz. Cisim denge noktasını geçer mi?",
           "For m = {m} kg, c = {c} N·s/m, k = {k} N/m solve {ode} with x(0) = {x0}, x'(0) = {v0}. "
           "Does the mass ever pass the equilibrium position?"),
     "P": {"m": 1, "c": 4, "k": 4, "x0": 1, "v0": 0}},
    {"id": "diffeq-spring-3", "kind": "spring_mass",
     "topics": ["overdamped", "aşırı sönümlü", "shock absorber", "amortisör"],
     "title": ("Aşırı sönümlü sistem (amortisör)", "Overdamped system (shock absorber)"),
     "q": ("Bir amortisör modeli: m = {m} kg, c = {c} N·s/m, k = {k} N/m. Kütle {x0} m sıkıştırılıp "
           "{v0} m/s hızla bırakılıyor. {ode} denklemini çöz; sistem salınım yapar mı?",
           "A shock-absorber model: m = {m} kg, c = {c} N·s/m, k = {k} N/m. The mass is displaced {x0} m "
           "and released with velocity {v0} m/s. Solve {ode}; does the system oscillate?"),
     "P": {"m": 1, "c": 5, "k": 4, "x0": 1, "v0": 0}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["euler_method"] = {
    "course": "diffeq",
    "title": ("Euler yöntemi", "Euler's method"),
    "topics": ["euler's method", "euler method", "euler", "numerical method", "numerical methods",
               "numerical solution", "step size", "approximate solution", "approximation",
               "euler yöntemi", "euler metodu", "sayısal çözüm", "sayısal yöntem", "adım aralığı",
               "yaklaşık çözüm"],
    "code": _FMT + _ODE_CORE + r'''
_SUBD = "₀₁₂₃₄₅₆₇₈₉"


def _sub(k):
    return "".join(_SUBD[int(ch)] for ch in str(int(k)))


def _d(v):
    v = float(v)
    if not math.isfinite(v):
        return "—"
    s = f"{v:.6g}"
    return "0" if s == "-0" else s


def _e(v):
    v = float(v)
    return "—" if not math.isfinite(v) else f"{v:.4g}"


def _dt(v):
    v = float(v)
    if not math.isfinite(v):
        return "—"
    if abs(v) < 1e-12:
        return "0"
    if abs(v) < 1:
        s = f"{v:.5f}".rstrip("0").rstrip(".")
        return "0" if s in ("", "-0", "0", "-") else s
    return f"{v:.6g}"


def _analyze_euler(P):
    key = ("eu", repr(sorted((str(k), str(v)) for k, v in P.items() if k not in ("lang", "seed"))))
    if key in _CACHE:
        return _CACHE[key]
    f, extra = _parse_f(P.get("f", "x + y"))
    F = _fnum(f)
    F1 = _scalar(F)
    x0 = _num(P.get("x0"), 0.0)
    y0 = _num(P.get("y0"), 1.0)
    h = _num(P.get("h"), 0.1)
    if h == 0 or not math.isfinite(h):
        h = 0.1
    n = max(1, min(30, int(round(_num(P.get("n"), 5)))))
    xs, ys, sl = [x0], [y0], []
    for k in range(n):
        s = F1(xs[-1], ys[-1])
        yn = ys[-1] + h * s
        if not (math.isfinite(s) and math.isfinite(yn)) or abs(yn) > 1e9:
            break
        sl.append(s)
        xs.append(x0 + (k + 1) * h)
        ys.append(yn)
    if len(xs) < 2:
        raise ValueError("Euler adımı hesaplanamadı: f başlangıçta tanımsız / f is undefined at the start")
    xs, ys, sl = np.array(xs), np.array(ys), np.array(sl)
    xn = float(xs[-1])
    rx, ry = _rk4(F1, x0, y0, xn, max(240, 60 * (len(xs) - 1)), -1e9, 1e9)
    closed = _closed(f, x0, y0, rx, ry, F, min(x0, xn), max(x0, xn))
    order = np.argsort(rx)
    rxs, rys = rx[order], ry[order]
    g = None
    if closed is not None:
        try:
            g = sp.lambdify(_X, closed["sol"], "numpy")
        except Exception:
            g = None

    def ref(xq):
        xq = np.asarray(xq, dtype=float)
        inside = (xq >= rxs[0] - 1e-9) & (xq <= rxs[-1] + 1e-9)
        if g is not None:
            try:
                with np.errstate(all="ignore"):
                    v = np.broadcast_to(np.asarray(g(xq), dtype=complex), xq.shape)
                return np.where((np.abs(v.imag) < 1e-9) & inside, v.real, np.nan).astype(float)
            except Exception:
                pass
        out = np.interp(xq, rxs, rys)
        return np.where((xq >= rxs[0] - 1e-12) & (xq <= rxs[-1] + 1e-12), out, np.nan)

    cx = np.linspace(x0, xn, 300)
    A = {"f": f, "extra": extra, "F": F, "x0": x0, "y0": y0, "h": h, "n": len(xs) - 1,
         "fxs": _fxs(P.get("f", "x + y"), f, extra),
         "xs": xs, "ys": ys, "sl": sl, "ye": ref(xs), "cx": cx, "cy": ref(cx), "closed": closed,
         "xr": float(rx[-1])}
    if len(_CACHE) > 60:
        _CACHE.clear()
    _CACHE[key] = A
    return A


def solve(P):
    A = _analyze_euler(P)
    fx = A["fxs"]
    h, n, xs, ys, sl = A["h"], A["n"], A["xs"], A["ys"], A["sl"]
    hs = _d(h)
    steps = [(f"Euler yöntemi: yₖ₊₁ = yₖ + h·f(xₖ, yₖ),  xₖ₊₁ = xₖ + h;   f(x, y) = {fx},  h = {hs}",
              f"Euler's method: yₖ₊₁ = yₖ + h·f(xₖ, yₖ),  xₖ₊₁ = xₖ + h;   f(x, y) = {fx},  h = {hs}"),
             (f"Başlangıç: x₀ = {_d(xs[0])}, y₀ = {_d(ys[0])}", f"Start: x₀ = {_d(xs[0])}, y₀ = {_d(ys[0])}")]
    if A["extra"]:
        steps.append((f"Not: {', '.join(A['extra'])} = 1 alındı", f"Note: {', '.join(A['extra'])} set to 1"))
    show = list(range(n)) if n <= 6 else [0, 1, 2, n - 2, n - 1]
    for k in show:
        if n > 6 and k == n - 2:
            steps.append(("⋮", "⋮"))
        s = (f"k = {k}:  y{_sub(k + 1)} = {_d(ys[k])} + {hs}·f({_d(xs[k])}, {_d(ys[k])}) = "
             f"{_d(ys[k])} + {hs}·({_d(sl[k])}) = {_d(ys[k + 1])}")
        steps.append((s, s))
    xn, yn = _d(xs[-1]), _d(ys[-1])
    steps.append((f"Euler sonucu: y({xn}) ≈ y{_sub(n)} = {yn}", f"Euler result: y({xn}) ≈ y{_sub(n)} = {yn}"))
    yex = float(A["ye"][-1])
    C = A["closed"]
    a_tr = f"y({xn}) ≈ {yn} (Euler)"
    a_en = a_tr
    if math.isfinite(yex):
        if C is not None:
            sol = _pretty(C["sol"])
            steps.append((f"Kesin çözüm: y = {sol} ⇒ y({xn}) = {_d(yex)}",
                          f"Exact solution: y = {sol} ⇒ y({xn}) = {_d(yex)}"))
            a_tr += f";  kesin değer {_d(yex)}"
            a_en += f";  exact value {_d(yex)}"
        else:
            steps.append((f"Kapalı form yok; referans (RK4, çok küçük adım): y({xn}) ≈ {_d(yex)}",
                          f"No closed form; reference (RK4, tiny steps): y({xn}) ≈ {_d(yex)}"))
            a_tr += f";  referans {_d(yex)}"
            a_en += f";  reference {_d(yex)}"
        err = abs(yex - float(ys[-1]))
        rel = (f"  (%{100 * err / abs(yex):.2f})", f"  ({100 * err / abs(yex):.2f}%)") if yex != 0 else ("", "")
        steps.append((f"Hata = |{_d(yex)} − {yn}| = {_e(err)}{rel[0]}",
                      f"Error = |{_d(yex)} − {yn}| = {_e(err)}{rel[1]}"))
        steps.append(("Euler birinci mertebeden bir yöntemdir: h yarıya inerse hata da yaklaşık yarıya iner",
                      "Euler's method is first order: halving h roughly halves the error"))
        a_tr += f";  hata {_e(err)}"
        a_en += f";  error {_e(err)}"
    else:
        xr = _d(A["xr"])
        steps.append((f"Gerçek çözüm x ≈ {xr} civarında sınırsız büyüyor (tanımsız); Euler adımları bunu fark etmez",
                      f"The true solution blows up near x ≈ {xr}; the Euler steps do not notice this"))
        a_tr += f";  gerçek çözüm x ≈ {xr} civarında patlıyor"
        a_en += f";  the true solution blows up near x ≈ {xr}"
    return {"answer": (a_tr, a_en), "steps": steps,
            "fmt": {"fx": fx, "xn": xn, "ic": f"y({_d(xs[0])}) = {_d(ys[0])}"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    A = _analyze_euler(P)
    F = A["F"]
    xs, ys, sl, ye = A["xs"], A["ys"], A["sl"], A["ye"]
    n, h = A["n"], A["h"]
    cx, cy = A["cx"], A["cy"]
    exact = A["closed"] is not None
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1], left=0.07, right=0.99, bottom=0.1, top=0.9,
                          wspace=0.05)
    ax = fig.add_subplot(gs[0, 0])
    tb = fig.add_subplot(gs[0, 1])
    tb.axis("off")
    tb.set_xlim(0, 1)
    tb.set_ylim(0, 1)
    xa, xb = float(min(xs[0], xs[-1])), float(max(xs[0], xs[-1]))
    W = xb - xa
    vals = np.concatenate([ys, cy[np.isfinite(cy)], ye[np.isfinite(ye)]])
    lo, hi = float(vals.min()), float(vals.max())
    if hi - lo < 1e-9:
        lo, hi = lo - 1, hi + 1
    pad = 0.12 * (hi - lo)
    X0, X1, Y0, Y1 = xa - 0.05 * W, xb + 0.06 * W, lo - pad, hi + pad
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.grid(alpha=0.25)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    fx = A["fxs"]
    ax.set_title(f"y' = {fx},   h = {_d(h)}", fontsize=11)
    ratio = _seg_ratio(fig, ax, X1 - X0, Y1 - Y0)
    segs, _c = _field(F, X0, X1, Y0, Y1, ratio, 17, 13, 0.32)
    ax.add_collection(LineCollection(segs, colors="#9CA3AF", linewidths=1.0, alpha=0.55, zorder=1))
    refl, = ax.plot([], [], "--", color="#16A34A", lw=2.2, zorder=4,
                    label=(("kesin çözüm" if exact else "referans (RK4)") if tr else
                           ("exact solution" if exact else "reference (RK4)")))
    eul, = ax.plot([], [], "-o", color="#E07B39", lw=2.2, ms=5, zorder=6, label="Euler")
    cur, = ax.plot([], [], color="#DC2626", lw=3.2, zorder=7, solid_capstyle="round")
    curdot, = ax.plot([], [], "o", color="#DC2626", ms=9, zorder=8)
    errs = LineCollection([], colors="#DC2626", linewidths=2.2, zorder=5)
    ax.add_collection(errs)
    ax.legend(handles=[eul, refl], loc=("lower right" if ys[-1] >= ys[0] else "upper right"), fontsize=9)
    rows = list(range(n + 1)) if n + 1 <= 12 else [0, 1, 2, 3, 4, None, n - 4, n - 3, n - 2, n - 1, n]
    colx = [0.07, 0.25, 0.47, 0.70, 0.91]
    top = 0.72
    dyr = min(0.052, 0.6 / (len(rows) + 1))
    hdr = ["k", "xₖ", "yₖ", "y(xₖ)", "|hata|" if tr else "|error|"]
    for j, t in enumerate(hdr):
        tb.text(colx[j], top, t, ha="center", va="center", fontsize=9, fontweight="bold")
    tb.plot([0.0, 1.0], [top - 0.55 * dyr] * 2, color="#9CA3AF", lw=0.8)
    tb.text(0.5, top + 0.055, ("yₖ: Euler    y(xₖ): " + ("kesin" if exact else "referans")) if tr else
            ("yₖ: Euler    y(xₖ): " + ("exact" if exact else "reference")),
            ha="center", va="center", fontsize=8.5, color="#6B7280")
    cells = []
    for j, k in enumerate(rows):
        yy = top - (j + 1) * dyr
        if k is None:
            cells.append((None, [tb.text(colx[0], yy, "⋮", ha="center", va="center", fontsize=9)]))
            continue
        er = abs(ye[k] - ys[k])
        vals_ = [str(k), _dt(xs[k]), _dt(ys[k]), _dt(ye[k]), ("—" if not math.isfinite(er) else f"{er:.3g}")]
        cols = ["#111827", "#111827", "#E07B39", "#16A34A", "#DC2626"]
        cells.append((k, [tb.text(colx[q], yy, vals_[q], ha="center", va="center", fontsize=8.5,
                                  family="DejaVu Sans Mono", color=cols[q]) for q in range(5)]))
    info = tb.text(0.0, 0.99, "", ha="left", va="top", fontsize=9.5, zorder=30,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    t0 = 12
    S = max(3, min(16, 114 // n))
    p3 = t0 + n * S + 4
    N = p3 + 45
    eseg = [[(xs[k], ys[k]), (xs[k], ye[k])] for k in range(n + 1) if math.isfinite(ye[k])]
    yex = float(ye[-1])
    intro = ("Euler: yₖ₊₁ = yₖ + h·f(xₖ, yₖ)\n" if tr else "Euler: yₖ₊₁ = yₖ + h·f(xₖ, yₖ)\n") + \
        f"f(x, y) = {fx},  h = {_d(h)}"
    cmp_ = ("Kesin çözümle karşılaştır (yeşil)\nkırmızı: her adımdaki hata" if tr else
            "Compare with the exact solution (green)\nred: the error at each step") if exact else \
        ("Referans çözümle karşılaştır (yeşil)\nkırmızı: her adımdaki hata" if tr else
         "Compare with the reference (green)\nred: the error at each step")
    fin = f"y({_d(xs[-1])}) ≈ {_d(ys[-1])}  (Euler)\n" + \
        ((("kesin: " if exact else "referans: ") if tr else ("exact: " if exact else "reference: ")) +
         f"{_d(yex)}\n" + ("hata: " if tr else "error: ") + _e(abs(yex - ys[-1])) if math.isfinite(yex) else "")

    def update(i):
        if i < t0:
            done, u = 0, 0.0
        else:
            q = (i - t0) / S
            done = min(n, int(q))
            u = q - int(q) if done < n else 0.0
        shown = done + (1 if (done < n and i >= t0 and u >= 0.65) else 0)
        eul.set_data(xs[:shown + 1], ys[:shown + 1])
        if i >= t0 and done < n:
            k = done
            g = min(1.0, u / 0.65)
            cur.set_data([xs[k], xs[k] + g * h], [ys[k], ys[k] + g * h * sl[k]])
            curdot.set_data([xs[k]], [ys[k]])
        else:
            cur.set_data([], [])
            curdot.set_data([], [])
        show_ref = i >= p3 + 22
        for k, txts in cells:
            if k is None:
                txts[0].set_visible(shown >= 5)
                continue
            for q, t in enumerate(txts):
                t.set_visible(k <= shown and (q < 3 or show_ref))
        pr = _ramp(i, p3, p3 + 22)
        if pr > 0:
            m = int(pr * (len(cx) - 1)) + 1
            refl.set_data(cx[:m], cy[:m])
        else:
            refl.set_data([], [])
        errs.set_segments(eseg if show_ref else [])
        if i < t0:
            info.set_text(intro)
        elif done < n:
            k = done
            info.set_text(((f"Adım {k + 1}: eğim f(x{_sub(k)}, y{_sub(k)}) = {_d(sl[k])}\n") if tr else
                           (f"Step {k + 1}: slope f(x{_sub(k)}, y{_sub(k)}) = {_d(sl[k])}\n")) +
                          f"y{_sub(k + 1)} = {_d(ys[k])} + {_d(h)}·({_d(sl[k])}) = {_d(ys[k + 1])}")
        elif i < p3 + 30:
            info.set_text(cmp_)
        else:
            info.set_text(fin)
        return []

    return N, update


def _clean_num(v):
    v = round(float(v), 6)
    return int(v) if v == int(v) else v


def vary(P, rnd):
    A = _analyze_euler(P)
    h0, n0, y00 = A["h"], A["n"], A["y0"]
    span0 = abs(h0 * n0)
    for _ in range(40):
        h = _clean_num(rnd.choice([h0 / 2, h0, h0 * 2]))
        n = rnd.choice([4, 5, 6, 8, 10])
        if not 0.3 * span0 <= abs(h * n) <= 1.3 * span0:
            continue
        dy = rnd.choice([-1, -0.5, 0, 0.5, 1]) * (1.0 if abs(y00) < 10 else 0.2 * abs(y00))
        y0 = _clean_num(y00 + dy)
        if h == h0 and n == n0 and y0 == y00:
            continue
        Q = dict(P)
        Q.update({"h": h, "n": n, "y0": y0})
        try:
            B = _analyze_euler(Q)
            ok = B["n"] == n and np.all(np.isfinite(B["ye"])) and np.max(np.abs(B["ye"])) < 1e4
        except Exception:
            ok = False
        if ok:
            return Q
    return dict(P)
''',
}
EXAMPLES += [
    {"id": "diffeq-euler-1", "kind": "euler_method",
     "title": ("Euler yöntemiyle yaklaşık çözüm", "Approximating a solution with Euler's method"),
     "q": ("y' = {fx}, {ic} başlangıç değer problemi için h = {h} adımıyla {n} Euler adımı uygula ve "
           "y({xn}) değerini tahmin et. Kesin çözümle karşılaştır.",
           "For the initial value problem y' = {fx}, {ic}, take {n} Euler steps with h = {h} to estimate "
           "y({xn}). Compare with the exact solution."),
     "P": {"f": "x + y", "x0": 0, "y0": 1, "h": 0.1, "n": 5}},
    {"id": "diffeq-euler-2", "kind": "euler_method",
     "topics": ["cooling", "soğuma"],
     "title": ("Euler ile soğuma tahmini", "Estimating cooling with Euler's method"),
     "q": ("Bir çorbanın sıcaklığı y' = {fx} (t dakika) denklemine uyuyor ve {ic}. h = {h} dk adımla "
           "{n} Euler adımı kullanarak t = {xn} dakikadaki sıcaklığı tahmin et; hatayı bul.",
           "The temperature of a bowl of soup satisfies y' = {fx} (t in minutes) with {ic}. Using {n} Euler "
           "steps of h = {h} min, estimate the temperature at t = {xn} min and find the error."),
     "P": {"f": "-0.1*(y - 20)", "x0": 0, "y0": 90, "h": 2, "n": 5}},
    {"id": "diffeq-euler-3", "kind": "euler_method",
     "topics": ["no closed form", "kapalı form yok"],
     "title": ("Kapalı formu olmayan denklemde Euler", "Euler on an equation with no closed form"),
     "q": ("y' = {fx}, {ic} için h = {h} ile {n} Euler adımı yap ve y({xn}) değerini, küçük adımlı "
           "RK4 referansıyla karşılaştır.",
           "For y' = {fx}, {ic}, take {n} Euler steps with h = {h} and compare y({xn}) with a small-step "
           "RK4 reference value."),
     "P": {"f": "x**2 + y**2", "x0": 0, "y0": 0, "h": 0.2, "n": 5}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["predator_prey"] = {
    "course": "diffeq",
    "title": ("Av-avcı modeli (Lotka–Volterra)", "Predator-prey model (Lotka–Volterra)"),
    "topics": ["predator-prey", "predator prey", "lotka-volterra", "lotka volterra", "population dynamics",
               "interacting populations", "nonlinear system", "phase plane", "phase portrait",
               "av-avcı", "av avcı", "lotka", "faz düzlemi", "faz portresi", "popülasyon dinamiği",
               "doğrusal olmayan sistem"],
    "code": _FMT + r'''
_CACHE = {}


def _run(P):
    key = repr(sorted((str(k), str(v)) for k, v in P.items() if k not in ("lang", "seed")))
    if key in _CACHE:
        return _CACHE[key]
    a, b, c, d = (float(P[k]) for k in ("a", "b", "c", "d"))
    x0, y0 = float(P["x0"]), float(P["y0"])
    if min(a, b, c, d) <= 0 or x0 <= 0 or y0 <= 0:
        raise ValueError("Tüm parametreler pozitif olmalı / all parameters must be positive")
    xs_, ys_ = c / d, a / b
    T0 = 2 * math.pi / math.sqrt(a * c)
    dt = T0 / 400.0
    X, Y = [x0], [y0]
    x, y = x0, y0
    prev = math.atan2(y - ys_, x - xs_)
    tot = 0.0
    for _ in range(4000):
        k1x, k1y = a * x - b * x * y, -c * y + d * x * y
        x2, y2 = x + dt / 2 * k1x, y + dt / 2 * k1y
        k2x, k2y = a * x2 - b * x2 * y2, -c * y2 + d * x2 * y2
        x3, y3 = x + dt / 2 * k2x, y + dt / 2 * k2y
        k3x, k3y = a * x3 - b * x3 * y3, -c * y3 + d * x3 * y3
        x4, y4 = x + dt * k3x, y + dt * k3y
        k4x, k4y = a * x4 - b * x4 * y4, -c * y4 + d * x4 * y4
        x = x + dt * (k1x + 2 * k2x + 2 * k3x + k4x) / 6
        y = y + dt * (k1y + 2 * k2y + 2 * k3y + k4y) / 6
        if not (math.isfinite(x) and math.isfinite(y)):
            break
        X.append(x)
        Y.append(y)
        ang = math.atan2(y - ys_, x - xs_)
        dd = ang - prev
        if dd > math.pi:
            dd -= 2 * math.pi
        elif dd < -math.pi:
            dd += 2 * math.pi
        tot += dd
        prev = ang
        if abs(tot) >= 4 * math.pi + 0.3:
            break
    X, Y = np.array(X), np.array(Y)
    t = np.arange(len(X)) * dt
    th = np.unwrap(np.arctan2(Y - ys_, X - xs_))
    dth = np.abs(th - th[0])
    idx = np.nonzero(dth >= 2 * math.pi)[0]
    T = None
    if len(idx) and idx[0] > 0:
        j = idx[0]
        T = float(t[j - 1] + (2 * math.pi - dth[j - 1]) / (dth[j] - dth[j - 1]) * dt)
    tend = min(t[-1], 2 * T) if T else t[-1]
    keep = t <= tend + 1e-12
    one = t <= (T if T else t[-1]) + 1e-12
    R = {"a": a, "b": b, "c": c, "d": d, "x0": x0, "y0": y0, "xs": xs_, "ys": ys_, "T0": T0, "T": T,
         "t": t[keep], "X": X[keep], "Y": Y[keep],
         "rng": (float(X[one].min()), float(X[one].max()), float(Y[one].min()), float(Y[one].max()))}
    if len(_CACHE) > 40:
        _CACHE.clear()
    _CACHE[key] = R
    return R


def _cv(v, var):
    s = _n(v, 4)
    return var if s == "1" else s + var


def _sys(R):
    return (f"x' = {_cv(R['a'], 'x')} − {_cv(R['b'], 'xy')},   "
            f"y' = −{_cv(R['c'], 'y')} + {_cv(R['d'], 'xy')}")


def solve(P):
    R = _run(P)
    a, b, c, d = R["a"], R["b"], R["c"], R["d"]
    sa, sb, sc, sd = (_n(v, 4) for v in (a, b, c, d))
    xs_, ys_ = R["xs"], R["ys"]
    w = math.sqrt(a * c)
    x1, x2, y1, y2 = R["rng"]
    steps = [(f"Sistem: {_sys(R)},  x(0) = {_n(R['x0'])}, y(0) = {_n(R['y0'])}  (x: av, y: avcı)",
              f"System: {_sys(R)},  x(0) = {_n(R['x0'])}, y(0) = {_n(R['y0'])}  (x: prey, y: predators)"),
             (f"Denge noktaları: x' = x(a − by) = 0 ve y' = y(−c + dx) = 0 ⇒ (0, 0) ve "
              f"(c/d, a/b) = ({sc}/{sd}, {sa}/{sb}) = ({_n(xs_)}, {_n(ys_)})",
              f"Equilibria: x' = x(a − by) = 0 and y' = y(−c + dx) = 0 ⇒ (0, 0) and "
              f"(c/d, a/b) = ({sc}/{sd}, {sa}/{sb}) = ({_n(xs_)}, {_n(ys_)})"),
             (f"Dengede doğrusallaştırma: özdeğerler ±i·√(ac) = ±{_n(w, 4)}i ⇒ merkez; küçük salınımların "
              f"periyodu 2π/√(ac) ≈ {_n(R['T0'])}",
              f"Linearising at the equilibrium: eigenvalues ±i·√(ac) = ±{_n(w, 4)}i ⇒ a centre; small "
              f"oscillations have period 2π/√(ac) ≈ {_n(R['T0'])}"),
             ("Korunan nicelik V(x, y) = d·x − c·ln x + b·y − a·ln y sabittir ⇒ yörüngeler kapalı eğrilerdir",
              "The quantity V(x, y) = d·x − c·ln x + b·y − a·ln y is conserved ⇒ orbits are closed curves")]
    if R["T"]:
        steps.append((f"Sayısal çözüm (RK4): periyot T ≈ {_n(R['T'])};  av {_n(x1, 1)} ile {_n(x2, 1)}, "
                      f"avcı {_n(y1, 1)} ile {_n(y2, 1)} arasında salınır",
                      f"Numerical solution (RK4): period T ≈ {_n(R['T'])};  prey oscillates between "
                      f"{_n(x1, 1)} and {_n(x2, 1)}, predators between {_n(y1, 1)} and {_n(y2, 1)}"))
    steps.append(("Avcı tepe noktaları av tepe noktalarından çeyrek periyot kadar sonra gelir "
                  "(önce av artar, sonra avcı)",
                  "Predator peaks lag the prey peaks by about a quarter period (prey rise first, then predators)"))
    eqs = f"({_n(xs_)}, {_n(ys_)})"
    if R["T"]:
        ans = (f"Denge {eqs};  periyot T ≈ {_n(R['T'])}", f"Equilibrium {eqs};  period T ≈ {_n(R['T'])}")
    else:
        ans = (f"Denge {eqs}", f"Equilibrium {eqs}")
    return {"answer": ans, "steps": steps, "fmt": {"sys": _sys(R)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    R = _run(P)
    a, b, c, d = R["a"], R["b"], R["c"], R["d"]
    t, X, Y = R["t"], R["X"], R["Y"]
    xs_, ys_ = R["xs"], R["ys"]
    x1, x2, y1, y2 = R["rng"]
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.25], left=0.08, right=0.98, bottom=0.11, top=0.8,
                          wspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    at = fig.add_subplot(gs[0, 1])
    dxr, dyr = max(x2 - x1, 1e-6), max(y2 - y1, 1e-6)
    XL0, XL1 = max(0.0, x1 - 0.3 * dxr), x2 + 0.22 * dxr
    YL0, YL1 = max(0.0, y1 - 0.3 * dyr), y2 + 0.3 * dyr
    ax.set_xlim(XL0, XL1)
    ax.set_ylim(YL0, YL1)
    ax.grid(alpha=0.25)
    ax.set_xlabel("x (av)" if tr else "x (prey)")
    ax.set_ylabel("y (avcı)" if tr else "y (predators)")
    ax.set_title("Faz düzlemi" if tr else "Phase plane", fontsize=11)
    fw, fh = fig.get_size_inches()
    pos = ax.get_position()
    sx, sy = pos.width * fw / (XL1 - XL0), pos.height * fh / (YL1 - YL0)
    gx = XL0 + (np.arange(13) + 0.5) * (XL1 - XL0) / 13
    gy = YL0 + (np.arange(11) + 0.5) * (YL1 - YL0) / 11
    GX, GY = np.meshgrid(gx, gy)
    U, V = a * GX - b * GX * GY, -c * GY + d * GX * GY
    nrm = np.hypot(U * sx, V * sy) + 1e-12
    Ls = 0.13
    ax.quiver(GX, GY, U * Ls / nrm, V * Ls / nrm, color="#9CA3AF", angles="xy",
              scale_units="xy", scale=1, width=0.004, headwidth=4, zorder=1)
    ax.axvline(xs_, color="#7C3AED", ls="--", lw=1.1)
    ax.axhline(ys_, color="#E07B39", ls="--", lw=1.1)
    ax.text(xs_, YL1 - 0.01 * (YL1 - YL0), " y' = 0", color="#7C3AED", fontsize=8.5, va="top")
    ax.text(XL1 - 0.01 * (XL1 - XL0), ys_, "x' = 0", color="#E07B39", fontsize=8.5, va="bottom", ha="right")
    ax.plot([xs_], [ys_], "o", color="#16A34A", ms=9, zorder=6)
    ax.text(xs_, ys_ - 0.04 * (YL1 - YL0), f"({_n(xs_)}, {_n(ys_)})", color="#16A34A", fontsize=9,
            ha="center", va="top", fontweight="bold", zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    orb, = ax.plot([], [], color="#2563EB", lw=2.2, zorder=4)
    od, = ax.plot([], [], "o", color="#DC2626", ms=8, zorder=7)
    ax.plot([R["x0"]], [R["y0"]], "s", color="#DC2626", ms=6, zorder=6)
    te = t[-1]
    at.set_xlim(0, te)
    top = 1.3 * max(X.max(), Y.max())
    at.set_ylim(0, top)
    at.grid(alpha=0.25)
    at.set_xlabel("t")
    at.set_title("Zamana göre nüfuslar" if tr else "Populations over time", fontsize=11)
    lx, = at.plot([], [], color="#2563EB", lw=2.2, label="x(t) " + ("av" if tr else "prey"))
    ly, = at.plot([], [], color="#E07B39", lw=2.2, label="y(t) " + ("avcı" if tr else "predators"))
    at.axhline(xs_, color="#2563EB", ls=":", lw=1)
    at.axhline(ys_, color="#E07B39", ls=":", lw=1)
    vt, = at.plot([], [], color="#9CA3AF", lw=1)
    dx_, = at.plot([], [], "o", color="#2563EB", ms=6)
    dy_, = at.plot([], [], "o", color="#E07B39", ms=6)
    at.legend(loc="upper right", fontsize=9, ncol=2)
    T = R["T"]
    ya = 1.1 * X.max()
    arr = at.annotate("", xy=(T if T else te, ya), xytext=(0, ya),
                      arrowprops=dict(arrowstyle="<->", color="#7C3AED", lw=1.6))
    arrt = at.text((T if T else te) / 2, ya + 0.01 * top, f"T ≈ {_n(T)}" if T else "", ha="center",
                   va="bottom", color="#7C3AED", fontsize=11, fontweight="bold")
    info = _banner(fig)
    l1 = (f"1) Denge: x* = c/d = {_n(xs_)}, y* = a/b = {_n(ys_)}  (kesikli: x' = 0, y' = 0)" if tr else
          f"1) Equilibrium: x* = c/d = {_n(xs_)}, y* = a/b = {_n(ys_)}  (dashed: x' = 0, y' = 0)")
    l2 = ("2) Yörünge dengenin etrafında kapalı bir eğri: önce av, sonra avcı artar" if tr else
          "2) A closed orbit around the equilibrium: prey rise first, then predators")
    l3 = (f"3) Periyot T ≈ {_n(T)}" if tr else f"3) Period T ≈ {_n(T)}") if T else "3)"
    l3b = (f"av: {_n(x1, 1)} – {_n(x2, 1)},   avcı: {_n(y1, 1)} – {_n(y2, 1)}" if tr else
           f"prey: {_n(x1, 1)} – {_n(x2, 1)},   predators: {_n(y1, 1)} – {_n(y2, 1)}")
    N = 170

    def update(i):
        p = _ramp(i, 18, 150)
        m = max(1, int(round(p * (len(t) - 1))) + 1)
        orb.set_data(X[:m], Y[:m])
        od.set_data([X[m - 1]], [Y[m - 1]])
        lx.set_data(t[:m], X[:m])
        ly.set_data(t[:m], Y[:m])
        vt.set_data([t[m - 1], t[m - 1]], [0, top])
        dx_.set_data([t[m - 1]], [X[m - 1]])
        dy_.set_data([t[m - 1]], [Y[m - 1]])
        fin = i >= 150
        arr.set_visible(fin and T is not None)
        arrt.set_visible(fin and T is not None)
        if i < 18:
            info.set_text(l1)
        elif i < 150:
            info.set_text(l1 + "\n" + l2 + f"\nt = {t[m - 1]:.2f}:   x = {X[m - 1]:.1f},   y = {Y[m - 1]:.1f}")
        else:
            info.set_text(l3 + "\n" + l3b)
        return []

    return N, update


def vary(P, rnd):
    xs_ = rnd.choice([20, 25, 40, 50, 80])
    ys_ = rnd.choice([5, 8, 10, 20, 25])
    a = rnd.choice([0.5, 0.8, 1.0, 1.2])
    c = rnd.choice([0.3, 0.4, 0.5, 0.6, 0.8])
    b = round(a / ys_, 6)
    d = round(c / xs_, 6)
    x0 = int(round(xs_ * rnd.choice([1.3, 1.5, 1.6, 1.8])))
    y0 = int(round(ys_ * rnd.choice([0.6, 0.8, 1.0, 1.2])))
    return {"a": a, "b": b, "c": c, "d": d, "x0": x0, "y0": y0}
''',
}
EXAMPLES += [
    {"id": "diffeq-lv-1", "kind": "predator_prey",
     "topics": ["rabbits and foxes", "tavşan tilki"],
     "title": ("Tavşanlar ve tilkiler", "Rabbits and foxes"),
     "q": ("Bir ormanda tavşan (x, yüz cinsinden) ve tilki (y) nüfusları {sys} sistemine uyuyor. "
           "x(0) = {x0}, y(0) = {y0} için denge noktasını bul, faz düzlemindeki yörüngeyi ve "
           "salınımın periyodunu incele.",
           "Rabbits (x, in hundreds) and foxes (y) in a forest follow the system {sys}. With x(0) = {x0}, "
           "y(0) = {y0}, find the equilibrium, sketch the orbit in the phase plane and estimate the period."),
     "P": {"a": 1, "b": 0.1, "c": 0.5, "d": 0.02, "x0": 40, "y0": 9}},
    {"id": "diffeq-lv-2", "kind": "predator_prey",
     "topics": ["insects", "böcek"],
     "title": ("Yaprak bitleri ve uğur böcekleri", "Aphids and ladybugs"),
     "q": ("Bir bahçede yaprak biti (x) ve uğur böceği (y) sayıları {sys} ile modelleniyor; "
           "x(0) = {x0}, y(0) = {y0}. Denge durumunu bul ve iki nüfusun zaman içindeki salınımını açıkla.",
           "Aphids (x) and ladybugs (y) in a garden are modelled by {sys} with x(0) = {x0}, y(0) = {y0}. "
           "Find the equilibrium and describe how the two populations oscillate over time."),
     "P": {"a": 0.8, "b": 0.04, "c": 0.6, "d": 0.01, "x0": 80, "y0": 15}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["mixing_tank"] = {
    "course": "diffeq",
    "title": ("Karışım (tuzlu su tankı) problemi", "Mixing problem (brine tank)"),
    "topics": ["mixing", "mixing problem", "mixing problems", "tank problem", "brine", "salt tank", "salt",
               "concentration", "inflow outflow", "karışım", "karışım problemi", "tank problemi",
               "tuzlu su", "tuz", "derişim", "konsantrasyon"],
    "code": _FMT + r'''
from fractions import Fraction
from matplotlib.patches import Rectangle


def _vals(P):
    V, cin, r, A0 = float(P["V"]), float(P["c_in"]), float(P["r"]), float(P["A0"])
    if V <= 0 or r <= 0 or cin < 0 or A0 < 0:
        raise ValueError("V, r > 0 ve c_in, A0 ≥ 0 olmalı / need V, r > 0 and c_in, A0 ≥ 0")
    t1 = float(P.get("t1", 20))
    At = P.get("A_target")
    Ae = V * cin
    tau = V / r
    ts = None
    if At is not None:
        At = float(At)
        if min(A0, Ae) < At < max(A0, Ae):
            ts = tau * math.log((A0 - Ae) / (At - Ae))
        else:
            At = None
    return V, cin, r, A0, t1, At, Ae, tau, ts


def _A(V, cin, r, A0, t):
    Ae = V * cin
    return Ae + (A0 - Ae) * np.exp(-(r / V) * np.asarray(t, dtype=float))


def _fr(v):
    f = Fraction(v).limit_denominator(10000)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def _expo(r, V):
    f = Fraction(r).limit_denominator(10000) / Fraction(V).limit_denominator(10000)
    if f.numerator == 1:
        return f"−t/{f.denominator}"
    return f"−{_fr(float(f))}·t" if f.denominator != 1 else f"−{f.numerator}t"


def _out(r, V):
    f = Fraction(r).limit_denominator(10000) / Fraction(V).limit_denominator(10000)
    if f.numerator == 1:
        return f"A/{f.denominator}"
    return f"({f.numerator}/{f.denominator})·A" if f.denominator != 1 else f"{f.numerator}A"


def solve(P):
    V, cin, r, A0, t1, At, Ae, tau, ts = _vals(P)
    sV, sc, sr, sA0, s1 = _n(V), _n(cin, 4), _n(r, 4), _n(A0), _n(t1)
    rin = r * cin
    A1 = float(_A(V, cin, r, A0, t1))
    ex = _expo(r, V)
    AA = _affine(Ae, A0 - Ae, "e^(" + ex + ")")
    AA1 = _affine(Ae, A0 - Ae, "e^(−" + _n(t1 / tau, 4) + ")")
    rhs = f"{_n(rin, 4)} − {_out(r, V)}" if rin > 0 else f"−{_out(r, V)}"
    steps = [(f"Giren tuz hızı = r·c_giriş = {sr}·{sc} = {_n(rin, 4)} g/dk",
              f"Salt in = r·c_in = {sr}·{sc} = {_n(rin, 4)} g/min"),
             (f"Çıkan tuz hızı = r·(A/V) = {sr}·A/{sV} = {_out(r, V)} g/dk (karışım homojen)",
              f"Salt out = r·(A/V) = {sr}·A/{sV} = {_out(r, V)} g/min (well mixed)"),
             (f"dA/dt = {rhs},  A(0) = {sA0}", f"dA/dt = {rhs},  A(0) = {sA0}"),
             (f"Doğrusal 1. mertebe: integral çarpanı e^(t/{_n(tau, 4)}) ⇒ "
              f"A(t) = {AA}",
              f"Linear first order: integrating factor e^(t/{_n(tau, 4)}) ⇒ "
              f"A(t) = {AA}"),
             (f"A({s1}) = {AA1} ≈ {_n(A1)} g  "
              f"(derişim {_n(A1 / V, 4)} g/L)",
              f"A({s1}) = {AA1} ≈ {_n(A1)} g  "
              f"(concentration {_n(A1 / V, 4)} g/L)")]
    a_tr = f"A({s1}) ≈ {_n(A1)} g"
    a_en = a_tr
    if At is not None:
        q = (At - Ae) / (A0 - Ae)
        steps.append((f"A(t) = {_n(At)} ⇒ e^(−t/{_n(tau, 4)}) = {q:.4f} ⇒ t = {_n(tau, 4)}·ln({_n(1 / q, 4)}) "
                      f"≈ {_n(ts)} dk",
                      f"A(t) = {_n(At)} ⇒ e^(−t/{_n(tau, 4)}) = {q:.4f} ⇒ t = {_n(tau, 4)}·ln({_n(1 / q, 4)}) "
                      f"≈ {_n(ts)} min"))
        a_tr += f";  A = {_n(At)} g için t ≈ {_n(ts)} dk"
        a_en += f";  A = {_n(At)} g at t ≈ {_n(ts)} min"
    steps.append((f"t → ∞ iken A → V·c_giriş = {_n(Ae)} g (derişim → {sc} g/L)",
                  f"As t → ∞, A → V·c_in = {_n(Ae)} g (concentration → {sc} g/L)"))
    return {"answer": (a_tr, a_en), "steps": steps, "fmt": {}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    V, cin, r, A0, t1, At, Ae, tau, ts = _vals(P)
    tm = max(t1, ts or 0.0)
    tmax = max(1.4 * tm, min(3.0 * tau, 6.0 * tm))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.45], left=0.02, right=0.97, bottom=0.12, top=0.9,
                          wspace=0.14)
    axL = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[0, 1])
    axL.set_xlim(0, 10)
    axL.set_ylim(0, 10)
    axL.set_aspect("equal")
    axL.axis("off")
    cref = max(cin, A0 / V, 1e-9)
    water = Rectangle((2.08, 1.68), 5.84, 5.9, fc="#DBEAFE", ec="none", zorder=1)
    axL.add_patch(water)
    axL.plot([2, 2, 8, 8], [8.4, 1.6, 1.6, 8.4], color="#374151", lw=3, zorder=3)
    axL.add_patch(Rectangle((0.0, 8.7), 3.0, 0.42, fc="#9CA3AF", ec="#6B7280", zorder=3))
    axL.add_patch(Rectangle((2.58, 8.2), 0.42, 0.6, fc="#9CA3AF", ec="#6B7280", zorder=3))
    axL.add_patch(Rectangle((8.0, 2.0), 2.0, 0.42, fc="#9CA3AF", ec="#6B7280", zorder=3))
    axL.add_patch(Rectangle((4.55, 9.25), 0.9, 0.55, fc="#6B7280", ec="#374151", zorder=4))
    axL.plot([5, 5], [9.25, 3.0], color="#374151", lw=2, zorder=4)
    blade, = axL.plot([], [], color="#374151", lw=4, solid_capstyle="round", zorder=4)
    rng = np.random.default_rng(P.get("seed", 0))
    M = 150
    salt = np.column_stack([2.3 + 5.4 * rng.random(M), 1.9 + 5.4 * rng.random(M)])
    sc = axL.scatter(np.zeros(0), np.zeros(0), s=10, color="#E07B39", zorder=2)
    amax = max(A0, Ae, 1e-9)
    drops = axL.scatter(np.zeros(0), np.zeros(0), s=42, zorder=2,
                        color=_mix("#DBEAFE", "#1D4ED8", 0.12 + 0.8 * cin / cref), edgecolors="#1E3A8A",
                        linewidths=0.5)
    outp = axL.scatter(np.zeros(0), np.zeros(0), s=18, zorder=4, color="#1D4ED8")
    unit = "dk" if tr else "min"
    axL.text(1.5, 9.35, f"{_n(r)} L/{unit} · {_n(cin, 4)} g/L", ha="center", va="bottom", fontsize=9,
             color="#1E3A8A")
    axL.text(9.0, 1.55, f"{_n(r)} L/{unit}", ha="center", va="top", fontsize=9, color="#1E3A8A")
    axL.text(2.2, 7.3, f"V = {_n(V)} L", ha="left", va="top", fontsize=9, color="#111827", zorder=5)
    amt = axL.text(5.0, 0.75, "", ha="center", va="center", fontsize=11, fontweight="bold", color="#111827")
    ts_ = np.linspace(0, tmax, 400)
    As = _A(V, cin, r, A0, ts_)
    ax.set_xlim(0, tmax)
    top = max(A0, Ae, float(As.max())) * 1.38 + 1e-9
    ax.set_ylim(0, top)
    ax.grid(alpha=0.3)
    ax.set_xlabel(f"t ({unit})")
    ax.set_ylabel("A(t) (g)")
    AA = _affine(Ae, A0 - Ae, "e^(" + _expo(r, V) + ")")
    ax.set_title(f"A(t) = {AA}", fontsize=11)
    if Ae > 0:
        ax.axhline(Ae, color="#DC2626", ls="--", lw=1.3)
        ax.text(tmax * 0.98, Ae + top * 0.015, f"V·c = {_n(Ae)} g", ha="right", va="bottom", color="#DC2626",
                fontsize=9)
    curve, = ax.plot([], [], color="#2563EB", lw=2.6)
    dot, = ax.plot([], [], "o", color="#2563EB", ms=8, zorder=6)
    A1 = float(_A(V, cin, r, A0, t1))
    up = A1 >= A0
    m1, = ax.plot([], [], "o", color="#7C3AED", ms=10, zorder=7)
    m1l, = ax.plot([], [], ":", color="#7C3AED", lw=1.3)
    lab_left = up and t1 > 0.3 * tmax
    m1t = ax.text(0, 0, "", color="#7C3AED", fontsize=11, fontweight="bold", ha="right" if lab_left else "left",
                  va="top" if (up and not lab_left) else "bottom")
    m2, = ax.plot([], [], "s", color="#16A34A", ms=9, zorder=7)
    m2l, = ax.plot([], [], ":", color="#16A34A", lw=1.3)
    m2t = ax.text(0, 0, "", color="#16A34A", fontsize=11, fontweight="bold", ha="right",
                  va="bottom" if up else "top")
    info = _box(ax)
    l1 = ("1) dA/dt = " + (f"{_n(r * cin, 4)} − {_out(r, V)}" if cin > 0 else f"−{_out(r, V)}")) + ("  (giren − çıkan)" if tr else "  (in − out)")
    l2 = f"2) A(t) = {AA}"
    l3 = f"3) A({_n(t1)}) ≈ {_n(A1)} g"
    if At is not None:
        l3 += f";  A = {_n(At)} ⇒ t ≈ {_n(ts)} {unit}"
    N = 150

    def update(i):
        tc = tmax * _ramp(i, 12, 118)
        Ac = float(_A(V, cin, r, A0, tc))
        m = max(1, int(round(_ramp(i, 12, 118) * (len(ts_) - 1))) + 1)
        curve.set_data(ts_[:m], As[:m])
        dot.set_data([tc], [Ac])
        conc = Ac / V
        wc = _mix("#EFF6FF", "#1D4ED8", 0.12 + 0.8 * conc / cref)
        water.set_facecolor(wc)
        sc.set_offsets(salt[:int(round(M * Ac / amax))])
        ph = (np.arange(4) / 4.0 + 0.045 * i) % 1.0
        drops.set_offsets(np.column_stack([np.full(4, 2.79), 8.15 - 0.6 * ph]))
        po = (np.arange(3) / 3.0 + 0.035 * i) % 1.0
        outp.set_offsets(np.column_stack([8.15 + 1.75 * po, np.full(3, 2.21)]))
        outp.set_color(wc)
        ang = 0.35 * i
        L = 1.1 * math.cos(ang)
        blade.set_data([5 - L, 5 + L], [3.0, 3.0])
        amt.set_text(f"t = {tc:.1f} {unit}   A = {_n(Ac, 1)} g   c = {_n(conc, 3)} g/L")
        if tc >= t1 - 1e-9:
            m1.set_data([t1], [A1])
            m1l.set_data([t1, t1], [0, A1])
            m1t.set_position((t1 + (-0.015 if lab_left else 0.015) * tmax,
                              A1 + top * (-0.03 if (up and not lab_left) else 0.03)))
            m1t.set_text(f"A({_n(t1)}) ≈ {_n(A1, 1)}")
        else:
            m1.set_data([], [])
            m1l.set_data([], [])
            m1t.set_text("")
        if At is not None and tc >= ts - 1e-9:
            m2.set_data([ts], [At])
            m2l.set_data([ts, ts], [0, At])
            m2t.set_position((ts - tmax * 0.015, At + top * (0.03 if up else -0.03)))
            m2t.set_text(f"t ≈ {_n(ts, 1)} {unit}")
        else:
            m2.set_data([], [])
            m2l.set_data([], [])
            m2t.set_text("")
        if i < 12:
            info.set_text(l1)
        elif i < 118:
            info.set_text(l1 + "\n" + l2)
        else:
            info.set_text(l2 + "\n" + l3)
        return []

    return N, update


def vary(P, rnd):
    Q = dict(P)
    V = rnd.choice([100, 200, 400, 500, 1000])
    r = rnd.choice([2, 4, 5, 10, 20])
    flush = float(P["c_in"]) == 0
    cin = 0 if flush else rnd.choice([0.5, 1, 2, 3])
    Ae0 = float(P["V"]) * float(P["c_in"])
    if flush:
        A0 = rnd.choice([100, 200, 300, 500])
    elif float(P["A0"]) == 0:
        A0 = 0
    elif float(P["A0"]) > Ae0:
        A0 = int(V * cin * rnd.choice([1.5, 1.6, 2, 2.5]))
    else:
        A0 = int(V * cin * rnd.choice([0.2, 0.25, 0.4, 0.5]))
    Q.update({"V": V, "r": r, "c_in": cin, "A0": A0, "t1": rnd.choice([10, 20, 30, 40])})
    if "A_target" in P:
        Ae = V * cin
        Q["A_target"] = int(round(Ae + (A0 - Ae) * rnd.choice([0.25, 0.5]))) if A0 != Ae else A0
    return Q
''',
}
EXAMPLES += [
    {"id": "diffeq-mix-1", "kind": "mixing_tank",
     "title": ("Tuzlu su ile dolan tank", "Tank filling with brine"),
     "q": ("{V} L saf su içeren bir tanka litresinde {c_in} g tuz bulunan su {r} L/dk hızla giriyor; iyi "
           "karışan çözelti aynı hızla dışarı akıyor (başlangıçta {A0} g tuz). {t1} dakika sonra tankta "
           "kaç gram tuz vardır? Uzun vadede ne olur?",
           "A tank holds {V} L of pure water. Brine with {c_in} g of salt per litre flows in at {r} L/min "
           "and the well-mixed solution flows out at the same rate (initially {A0} g of salt). How much "
           "salt is in the tank after {t1} minutes? What happens in the long run?"),
     "P": {"V": 200, "c_in": 2, "r": 5, "A0": 0, "t1": 20}},
    {"id": "diffeq-mix-2", "kind": "mixing_tank",
     "topics": ["flushing", "yıkama", "temizleme"],
     "title": ("Tankın saf suyla temizlenmesi", "Flushing a tank with pure water"),
     "q": ("{V} L'lik bir tankta {A0} g tuz çözünmüş. Tanka {r} L/dk hızla saf su giriyor ve karışım aynı "
           "hızla çıkıyor. {t1} dakika sonra kaç gram tuz kalır? Tuz miktarı ne zaman {A_target} g'a düşer?",
           "A {V} L tank contains {A0} g of dissolved salt. Pure water enters at {r} L/min and the mixture "
           "leaves at the same rate. How much salt remains after {t1} minutes? When does the amount drop "
           "to {A_target} g?"),
     "P": {"V": 1000, "c_in": 0, "r": 10, "A0": 300, "t1": 30, "A_target": 150}},
    {"id": "diffeq-mix-3", "kind": "mixing_tank",
     "topics": ["dilution", "seyreltme"],
     "title": ("Daha seyreltik tuzlu su girişi", "Weaker brine flowing in"),
     "q": ("{V} L'lik tankta başlangıçta {A0} g tuz var. Litresinde {c_in} g tuz olan su {r} L/dk hızla "
           "giriyor ve karışım aynı hızla çıkıyor. A(t)'yi bul ve {t1} dakika sonraki tuz miktarını hesapla.",
           "A {V} L tank initially contains {A0} g of salt. Brine with {c_in} g/L enters at {r} L/min and "
           "the mixture leaves at the same rate. Find A(t) and the amount of salt after {t1} minutes."),
     "P": {"V": 100, "c_in": 0.5, "r": 4, "A0": 80, "t1": 25}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["second_order_linear"] = {
    "course": "diffeq",
    "title": ("Sabit katsayılı ikinci mertebe homojen denklem",
              "Second-order linear homogeneous equation"),
    "topics": ["second order", "second-order", "homogeneous", "constant coefficients", "characteristic equation",
               "auxiliary equation", "distinct real roots", "repeated roots", "complex roots",
               "higher order", "linear differential equations", "ikinci mertebe", "homojen", "sabit katsayılı",
               "karakteristik denklem", "yardımcı denklem", "karmaşık kökler", "katlı kök", "çift kök"],
    "code": _FMT + _SECOND + r'''
from matplotlib.patches import Rectangle


def _get(P):
    S = _sol2(P["a"], P["b"], P["c"], P["y0"], P["dy0"], "y")
    re = [z.real for z in S["rv"]]
    if max(re) > 1e-9:
        te = min(3.0, max(0.5, 2.5 / max(re)))
    elif max(re) < -1e-9:
        te = min(12.0, max(1.5, math.log(50) / min(abs(v) for v in re)))
        if S["case"] == "complex":
            te = max(te, 1.5 * 2 * math.pi / float(S["om"]))
            te = min(te, 4 * 2 * math.pi / float(S["om"]))
    else:
        te = 2 * 2 * math.pi / float(S["om"]) if S["case"] == "complex" else 5.0
    S["t_end"] = te
    return S


def solve(P):
    S = _get(P)
    a, b, c = S["a"], S["b"], S["c"]
    ode = _join([(a, "y''"), (b, "y'"), (c, "y")]) + " = 0"
    char = _join([(a, "r²"), (b, "r"), (c, "")]) + " = 0"
    ics = f"y(0) = {_ps(S['y0'])}, y'(0) = {_ps(S['v0'])}"
    sign = {"real": ("> 0", "> 0"), "double": ("", ""), "complex": ("< 0", "< 0")}[S["case"]]
    steps = [(f"Denklem: {ode},  {ics}", f"Equation: {ode},  {ics}"),
             (f"y = e^(rt) dene ⇒ karakteristik denklem: {char}", f"Try y = e^(rt) ⇒ characteristic equation: {char}"),
             (f"Δ = b² − 4ac = {_ps(b * b)} − {_pp(4 * a * c)} = {_ps(S['D'])} {sign[0]}  ⇒  {S['rtxt'][0]}",
              f"Δ = b² − 4ac = {_ps(b * b)} − {_pp(4 * a * c)} = {_ps(S['D'])} {sign[1]}  ⇒  {S['rtxt'][1]}"),
             (f"Temel çözümler: y₁ = {S['btxt'][0]},  y₂ = {S['btxt'][1]}",
              f"Fundamental solutions: y₁ = {S['btxt'][0]},  y₂ = {S['btxt'][1]}"),
             (f"Genel çözüm: y = {S['gen']}", f"General solution: y = {S['gen']}"),
             S["cst"],
             (f"Özel çözüm: y(t) = {S['part']}", f"Particular solution: y(t) = {S['part']}")]
    re = max(z.real for z in S["rv"])
    if re < -1e-9:
        steps.append(("Tüm köklerin reel kısmı negatif ⇒ t → ∞ iken y → 0",
                      "All roots have negative real part ⇒ y → 0 as t → ∞"))
    elif re > 1e-9:
        steps.append(("Pozitif reel kısımlı kök var ⇒ çözüm (genelde) sınırsız büyür",
                      "A root has positive real part ⇒ the solution (generally) grows without bound"))
    return {"answer": f"y(t) = {S['part']}", "steps": steps, "fmt": {"ode": ode, "ics": ics}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    S = _get(P)
    te = S["t_end"]
    tt = np.linspace(0, te, 500)
    yy = S["lam"](tt)
    b1, b2 = S["blam"][0](tt), S["blam"][1](tt)
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.5], left=0.06, right=0.98, bottom=0.11, top=0.8,
                          wspace=0.2)
    axL = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[0, 1])
    rv = S["rv"]
    Rr = max(1.0, max(max(abs(z.real), abs(z.imag)) for z in rv)) * 1.45 + 0.3
    axL.set_xlim(-Rr, Rr)
    axL.set_ylim(-Rr, Rr)
    axL.set_aspect("equal")
    axL.add_patch(Rectangle((-Rr, -Rr), Rr, 2 * Rr, fc="#DCFCE7", ec="none", alpha=0.6, zorder=0))
    axL.text(-Rr * 0.95, -Rr * 0.93, "Re r < 0: sönüm" if tr else "Re r < 0: decay", fontsize=8.5,
             color="#16A34A", va="bottom")
    axL.axhline(0, color="#6B7280", lw=1)
    axL.axvline(0, color="#6B7280", lw=1)
    axL.grid(alpha=0.25)
    axL.set_xlabel("Re r")
    axL.set_ylabel("Im r")
    char = _join([(S["a"], "r²"), (S["b"], "r"), (S["c"], "")]) + " = 0"
    axL.set_title(char, fontsize=11)
    rdots, = axL.plot([], [], "o", color="#DC2626", ms=11, zorder=5)
    ring, = axL.plot([], [], "o", mfc="none", mec="#DC2626", ms=11, zorder=5)
    if S["case"] == "complex":
        rl = [axL.text(z.real + 0.06 * Rr, z.imag, "", color="#DC2626", fontsize=10, fontweight="bold",
                       va="center") for z in rv]
        if S["al"] == 0:
            rlab = [f"{_im(S['om'])}", f"−{_im(S['om'])}"]
        else:
            rlab = [f"{_ps(S['al'])} + {_im(S['om'])}", f"{_ps(S['al'])} − {_im(S['om'])}"]
    elif S["case"] == "double":
        rl = [axL.text(rv[0].real, 0.12 * Rr, "", color="#DC2626", fontsize=10, fontweight="bold",
                       ha="center")]
        rlab = [f"r = {_ps(S['roots'][0])} (×2)"]
    else:
        rl = [axL.text(z.real, (0.12 if k == 0 else -0.12) * Rr, "", color="#DC2626", fontsize=10,
                       fontweight="bold", ha="center", va="center") for k, z in enumerate(rv)]
        rlab = [f"r₁ = {_ps(S['roots'][0])}", f"r₂ = {_ps(S['roots'][1])}"]
    fin = yy[np.isfinite(yy)]
    lo, hi = float(min(fin.min(), 0)), float(max(fin.max(), 0))
    if hi - lo < 1e-9:
        lo, hi = lo - 1, hi + 1
    span = hi - lo
    ax.set_xlim(0, te)
    ax.set_ylim(lo - 0.1 * span, hi + 0.15 * span)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.set_xlabel("t")
    ax.set_ylabel("y(t)")
    ode = _join([(S["a"], "y''"), (S["b"], "y'"), (S["c"], "y")]) + " = 0"
    ics = f"y(0) = {_ps(S['y0'])}, y'(0) = {_ps(S['v0'])}"
    ax.set_title(f"{ode},   {ics}", fontsize=11)
    bl1, = ax.plot([], [], "--", color="#7C3AED", lw=1.4, alpha=0.8, label="y₁ = " + S["btxt"][0])
    bl2, = ax.plot([], [], "--", color="#E07B39", lw=1.4, alpha=0.8, label="y₂ = " + S["btxt"][1])
    curve, = ax.plot([], [], color="#2563EB", lw=2.6, zorder=5, label="y(t)")
    dot, = ax.plot([], [], "o", color="#2563EB", ms=8, zorder=6)
    ic, = ax.plot([], [], "o", color="#DC2626", ms=10, zorder=7)
    tan, = ax.plot([], [], color="#DC2626", lw=3, zorder=7, solid_capstyle="round")
    grows = max(z.real for z in rv) > 1e-9
    ax.legend(handles=[bl1, bl2, curve], loc="upper left" if grows else "upper right", fontsize=8.5)
    y0f, v0f = float(S["y0"]), float(S["v0"])
    fw, fh = fig.get_size_inches()
    pos = ax.get_position()
    ratio = (pos.height * fh / (1.25 * span)) / (pos.width * fw / te)
    angt = math.atan(v0f * ratio)
    Lt = 0.09 * te
    tdx, tdy = Lt * math.cos(angt), Lt * math.sin(angt) / ratio
    info = _banner(fig)
    l1 = f"1) {char}  ⇒  {S['rshort']}"
    l2 = (f"2) y₁ = {S['btxt'][0]},  y₂ = {S['btxt'][1]}" if tr else f"2) y₁ = {S['btxt'][0]},  y₂ = {S['btxt'][1]}")
    l3 = (f"3) {ics}  ⇒  C₁ = {_ps(S['C1'])},  C₂ = {_ps(S['C2'])}")
    l4 = f"4) y(t) = {S['part']}"
    N = 160

    def update(i):
        rr = i >= 8
        rdots.set_data([z.real for z in rv] if rr else [], [z.imag for z in rv] if rr else [])
        if 8 <= i < 30:
            ring.set_data([z.real for z in rv], [z.imag for z in rv])
            ring.set_markersize(11 + 16 * ((i - 8) % 11) / 11.0)
        else:
            ring.set_data([], [])
        for t_, s_ in zip(rl, rlab):
            t_.set_text(s_ if i >= 14 else "")
        pb = _ramp(i, 30, 58)
        mb = int(pb * (len(tt) - 1)) + 1 if pb > 0 else 0
        bl1.set_data(tt[:mb], b1[:mb])
        bl2.set_data(tt[:mb], b2[:mb])
        if i >= 60:
            ic.set_data([0], [y0f])
            if i < 132:
                tan.set_data([0, tdx], [y0f, y0f + tdy])
            else:
                tan.set_data([], [])
        else:
            ic.set_data([], [])
            tan.set_data([], [])
        pc = _ramp(i, 66, 128)
        mc = int(pc * (len(tt) - 1)) + 1 if pc > 0 else 0
        curve.set_data(tt[:mc], yy[:mc])
        if 0 < mc < len(tt):
            dot.set_data([tt[mc - 1]], [yy[mc - 1]])
        else:
            dot.set_data([], [])
        if i < 30:
            info.set_text(l1)
        elif i < 60:
            info.set_text(l1 + "\n" + l2)
        elif i < 132:
            info.set_text(l2 + "\n" + l3)
        else:
            info.set_text(l3 + "\n" + l4)
        return []

    return N, update


def vary(P, rnd):
    S = _get(P)
    C1 = rnd.choice([1, 2, -1, 3])
    C2 = rnd.choice([1, -1, 2, -2, 3])
    if S["case"] == "real":
        r1, r2 = rnd.sample([-4, -3, -2, -1, 1, 2, 3], 2)
        return {"a": 1, "b": -(r1 + r2), "c": r1 * r2, "y0": C1 + C2, "dy0": r1 * C1 + r2 * C2}
    if S["case"] == "double":
        r = rnd.choice([-3, -2, -1, 1, 2])
        return {"a": 1, "b": -2 * r, "c": r * r, "y0": C1, "dy0": r * C1 + C2}
    al, w = rnd.choice([-2, -1, -1, 0, 1]), rnd.choice([1, 2, 3])
    return {"a": 1, "b": -2 * al, "c": al * al + w * w, "y0": C1, "dy0": al * C1 + w * C2}
''',
}
EXAMPLES += [
    {"id": "diffeq-2nd-1", "kind": "second_order_linear",
     "topics": ["distinct real roots", "farklı reel kökler"],
     "title": ("Farklı iki reel kök", "Two distinct real roots"),
     "q": ("{ode} denklemini {ics} başlangıç koşullarıyla çöz.",
           "Solve {ode} subject to {ics}."),
     "P": {"a": 1, "b": -1, "c": -6, "y0": 1, "dy0": 8}},
    {"id": "diffeq-2nd-2", "kind": "second_order_linear",
     "topics": ["repeated roots", "katlı kök"],
     "title": ("Çift katlı kök", "A repeated root"),
     "q": ("Karakteristik denklemi çift köklü olan {ode} denklemini {ics} için çöz.",
           "The equation {ode} has a repeated characteristic root. Solve it with {ics}."),
     "P": {"a": 1, "b": 6, "c": 9, "y0": 2, "dy0": -1}},
    {"id": "diffeq-2nd-3", "kind": "second_order_linear",
     "topics": ["complex roots", "karmaşık kökler"],
     "title": ("Karmaşık kökler: sönen salınım", "Complex roots: a decaying oscillation"),
     "q": ("{ode},  {ics} başlangıç değer problemini çöz ve çözümün davranışını açıkla.",
           "Solve the initial value problem {ode}, {ics} and describe how the solution behaves."),
     "P": {"a": 1, "b": 2, "c": 5, "y0": 1, "dy0": 1}},
]
