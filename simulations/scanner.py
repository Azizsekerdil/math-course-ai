# -*- coding: utf-8 -*-
"""Kurs kaynaklarındaki örnek soruları bulup çalıştırılabilir simülasyona çevirir.

Akış (kullanıcının kendi bilgisayarında, seçtiği konu klasörü/dosyası için):

    PDF/TXT  ->  sayfa metni  ->  aday satır pencereleri  ->  sınıflandırıcılar
             ->  (tür, parametreler)  ->  [isteğe bağlı: sayıları değiştir]
             ->  gömülü şablonla çalışan simülasyon

TELİF / LİSANS: kitabın metni ne saklanır ne gösterilir. Bir örnekten
yalnızca MATEMATİKSEL İÇERİK (ifade, katsayılar, sınırlar) ve kaynak
referansı (dosya adı + sayfa) alınır; soru cümlesi programın kendi
şablonuyla yeniden yazılır. "Sayıları değiştir" açıkken (varsayılan)
katsayılar da değiştirilir, böylece ortaya kitaptakiyle aynı olmayan,
aynı türde yeni bir alıştırma çıkar.

PDF metni için isteğe bağlı PyMuPDF (fitz), o yoksa pypdf (BSD-3) kullanılır;
ikisi de yoksa yalnızca .txt kaynaklar taranır ve kullanıcıya bu açıkça söylenir.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF — isteğe bağlı (AGPL), bkz. THIRD_PARTY_NOTICES.md
except Exception:  # pragma: no cover - ortama bağlı
    fitz = None

try:
    # pypdf: BSD-3, saf Python. PyMuPDF içermeyen Windows/macOS paketlerinde
    # PDF metnini bu okur (paketleme betikleri onu kurar).
    import pypdf
except Exception:  # pragma: no cover - ortama bağlı
    pypdf = None

from . import engine

SCAN_EXTS = {".pdf", ".txt", ".md"}
MAX_FILES = 120
MAX_PAGES = 60
MAX_PER_FILE = 40
MAX_TOTAL = 400

# ══════════════════════════════════════════════════════════════════════════
# Text extraction
# ══════════════════════════════════════════════════════════════════════════

def pdf_support():
    return fitz is not None or pypdf is not None


def page_texts(path, max_pages=MAX_PAGES):
    """[(sayfa_no, metin), ...] — yalnızca bellekte, diske yazılmaz."""
    p = Path(path)
    suf = p.suffix.lower()
    if suf in (".txt", ".md"):
        try:
            return [(1, p.read_text(encoding="utf-8", errors="replace")[:400_000])]
        except Exception:
            return []
    if suf == ".pdf" and fitz is not None:
        out = []
        try:
            with fitz.open(str(p)) as doc:
                for i, page in enumerate(doc):
                    if i >= max_pages:
                        break
                    out.append((i + 1, page.get_text("text") or ""))
        except Exception:
            return out
        return out
    if suf == ".pdf" and pypdf is not None:
        out = []
        try:
            reader = pypdf.PdfReader(str(p))
            for i, page in enumerate(reader.pages):
                if i >= max_pages:
                    break
                try:
                    out.append((i + 1, page.extract_text() or ""))
                except Exception:
                    out.append((i + 1, ""))
        except Exception:
            return out
        return out
    return []


def resource_files(path):
    p = Path(path)
    if p.is_file():
        return [p] if p.suffix.lower() in SCAN_EXTS else []
    if not p.is_dir():
        return []
    files = []
    for f in sorted(p.rglob("*")):
        if f.is_file() and f.suffix.lower() in SCAN_EXTS and not f.name.startswith(("._", "~$")) \
                and "__MACOSX" not in f.parts and "read me" not in f.name.lower():
            files.append(f)
            if len(files) >= MAX_FILES:
                break
    return files


# ══════════════════════════════════════════════════════════════════════════
# Math normalisation + safe sympy parsing
# ══════════════════════════════════════════════════════════════════════════
_UNI = {
    "−": "-", "–": "-", "—": "-", "×": "*", "·": "*", "⋅": "*", "∙": "*", "÷": "/",
    "²": "^2", "³": "^3", "⁴": "^4", "⁵": "^5", "¹": "^1", "⁰": "^0", "⁻¹": "^(-1)",
    "√": "sqrt", "π": "pi", "θ": "theta", "∞": "oo", "≤": "<=", "≥": ">=", " ": " ",
    " ": " ", "’": "'", "′": "'", "“": "", "”": "", "→": "->", "ℯ": "e",
}
_FUNCS = {"sin", "cos", "tan", "sec", "csc", "cot", "ln", "log", "exp", "sqrt", "asin", "acos",
          "atan", "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "abs", "pi", "e", "oo"}


def normalize_math(s):
    for k, v in _UNI.items():
        s = s.replace(k, v)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _flattened_powers(s, vars_):
    # PDF metninde üst simgeler düz yazılır: "3x2 + 5x" -> "3x^2 + 5x"
    v = "".join(vars_)
    return re.sub(r"(?<![A-Za-z])([" + v + r"\)])([2-9])(?![\d.^])", r"\1^\2", s)


def to_sympy_string(raw, vars_=("x",), allow_const=False):
    """Ham ifadeyi güvenle sympy dizgisine çevirir; olmazsa None."""
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                                implicit_multiplication_application, convert_xor)
    except Exception:  # pragma: no cover
        return None
    s = normalize_math(str(raw)).strip().rstrip(".,;:")
    s = re.sub(r"\barc(sin|cos|tan)\b", r"a\1", s)
    s = re.sub(r"\|([^|]+)\|", r"abs(\1)", s)
    s = _flattened_powers(s, vars_)
    if not s or len(s) > 140 or not re.fullmatch(r"[0-9A-Za-z+\-*/^().,\s]+", s):
        return None
    if s.count("(") != s.count(")"):
        return None
    for w in re.findall(r"[A-Za-z]+", s):
        if w in _FUNCS or w in vars_:
            continue
        if all(ch in vars_ for ch in w):      # "xy" -> x*y
            continue
        return None
    syms = {v: sp.Symbol(v, real=True) for v in vars_}
    local = dict(syms)
    local.update({"ln": sp.log, "e": sp.E, "pi": sp.pi, "oo": sp.oo, "abs": sp.Abs})
    try:
        expr = parse_expr(s, local_dict=local, evaluate=True, transformations=(
            standard_transformations + (implicit_multiplication_application, convert_xor)))
    except Exception:
        return None
    if not isinstance(expr, sp.Expr) or expr.has(sp.zoo, sp.nan):
        return None
    if not allow_const and not (expr.free_symbols & set(syms.values())):
        return None
    if not expr.free_symbols <= set(syms.values()):
        return None
    if sp.count_ops(expr) > 60:
        return None
    out = sp.sstr(expr)
    return out


_MATH_TOKEN = re.compile(r"^[0-9xyt+\-*/^().,=]+$")


def _is_math_token(tok, vars_=("x",)):
    w = tok.strip(",;:")
    if not w:
        return False
    if _MATH_TOKEN.match(w):
        return True
    words = re.findall(r"[A-Za-z]+", w)
    return bool(words) and all(x in _FUNCS or all(ch in vars_ for ch in x) for x in words) \
        and re.fullmatch(r"[0-9A-Za-z+\-*/^().]+", w) is not None


def math_head(text, vars_=("x",)):
    """'(x^2 - 4)/(x - 2) and explain why' -> '(x^2 - 4)/(x - 2)'"""
    out = []
    for tok in text.split():
        if not _is_math_token(tok, vars_):
            break
        out.append(tok)
        if tok.endswith((",", ";")) or (tok.endswith(".") and not re.search(r"\d\.$", tok[:-1] + "0")):
            break
    return " ".join(out).rstrip(".,;:")


def math_tail(text, vars_=("x",)):
    """'Example. Solve 2x^2 - 3x - 5 ' -> '2x^2 - 3x - 5'"""
    out = []
    for tok in reversed(text.split()):
        if not _is_math_token(tok, vars_) or tok.endswith((".", ":", ",")) and out:
            break
        out.append(tok)
    return " ".join(reversed(out)).strip(".,;:")


def _num(s):
    s = normalize_math(s).replace(" ", "")
    try:
        if "/" in s:
            a, b = s.split("/", 1)
            v = float(a) / float(b)
        else:
            v = float(s)
    except Exception:
        return None
    if v != v or abs(v) > 1e6:
        return None
    return int(v) if v == int(v) else round(v, 6)


# ══════════════════════════════════════════════════════════════════════════
# Classifiers  (window text -> (kind, P) or None)
# ══════════════════════════════════════════════════════════════════════════
NUM = r"-?\d+(?:\.\d+)?(?:/\d+)?"
_FX = r"(?<![A-Za-z'])(?:f\s*\(\s*x\s*\)|y|g\s*\(\s*x\s*\)|h\s*\(\s*x\s*\))\s*=\s*([^=;\n]{2,120})"


def _c_ode(t, low):
    m = re.search(r"(?:dy\s*/\s*dx|y\s*')\s*=\s*([^=;\n]{2,100})", t)
    if not m:
        return None
    f = to_sympy_string(math_head(m.group(1), ("x", "y")), ("x", "y"), allow_const=True)
    if f is None:
        return None
    P = {"f": f, "x0": 0, "y0": 1}
    ic = re.search(r"y\s*\(\s*(" + NUM + r")\s*\)\s*=\s*(" + NUM + ")", t)
    if ic:
        P["x0"], P["y0"] = _num(ic.group(1)), _num(ic.group(2))
    return "slope_field_expr", P


def _c_limit(t, low):
    m = re.search(r"lim\w*\s*\(?\s*x\s*(?:->|to|approaches)\s*(" + NUM + r"|[+-]?oo|infinity)\s*[+-]?\s*\)?\s*(?:of\s*)?(.{2,90})$", t)
    if not m:
        return None
    a_raw = m.group(1).replace("infinity", "oo")
    a = a_raw if "oo" in a_raw else _num(a_raw)
    f = to_sympy_string(math_head(m.group(2)))
    if f is None or a is None:
        return None
    return "limit_expr", {"f": f, "a": a}


def _c_integral(t, low):
    if not re.search(r"∫|\bintegral\b|\bintegrate\b|\bantiderivative\b|area under", low):
        return None
    bounds = re.search(r"from\s*(?:x\s*=\s*)?(" + NUM + r")\s*to\s*(?:x\s*=\s*)?(" + NUM + ")", t) or \
        re.search(r"\[\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\]", t)
    m = re.search(_FX, t)
    if m:
        f = to_sympy_string(math_head(m.group(1)))
    else:
        m = re.search(r"(?:∫|integral of|integrate)\s*\(?([^=;\n]{2,80}?)\)?\s*d\s*x", t)
        if not m:
            return None
        f = to_sympy_string(m.group(1))
    if f is None:
        return None
    a, b = (0, 2)
    if bounds:
        a, b = _num(bounds.group(1)), _num(bounds.group(2))
        if a is None or b is None or a == b:
            return None
    return "integral_expr", {"f": f, "a": a, "b": b}


def _c_derivative(t, low):
    if not re.search(r"derivative|differentiate|d\s*/\s*dx|f\s*'\s*\(|tangent line|slope of the tangent|türev", low):
        return None
    m = re.search(_FX, t)
    if not m:
        return None
    f = to_sympy_string(math_head(m.group(1)))
    if f is None:
        return None
    x0 = 1
    at = re.search(r"(?:at|where)\s*x\s*=\s*(" + NUM + ")", t) or re.search(r"\(\s*(" + NUM + r")\s*,", t)
    if at and _num(at.group(1)) is not None:
        x0 = _num(at.group(1))
    return "derivative_expr", {"f": f, "x0": x0}


def _c_surface(t, low):
    m = re.search(r"f\s*\(\s*x\s*,\s*y\s*\)\s*=\s*([^=;\n]{2,120})", t)
    if not m:
        return None
    f = to_sympy_string(math_head(m.group(1), ("x", "y")), ("x", "y"))
    if f is None:
        return None
    return "surface_3d", {"f": f}


def _c_quadratic(t, low):
    for m in re.finditer(r"([^=;:\n]*x\s*\^?\s*2[^=;:\n]*)=\s*(" + NUM + r")(?!\d|\.\d)", _flattened_powers(normalize_math(t), "x")):
        lhs = to_sympy_string(math_tail(m.group(1)))
        if lhs is None:
            continue
        try:
            import sympy as sp
            x = sp.Symbol("x", real=True)
            poly = sp.Poly(sp.sympify(lhs, locals={"x": x}) - sp.sympify(m.group(2)), x)
        except Exception:
            continue
        if poly.degree() != 2:
            continue
        a, b, c = (poly.coeff_monomial(x ** 2), poly.coeff_monomial(x), poly.coeff_monomial(1))
        vals = []
        for v in (a, b, c):
            if not v.is_rational:
                break
            vals.append(int(v) if v.is_integer else float(v))
        if len(vals) == 3 and vals[0] != 0:
            return "quadratic", {"a": vals[0], "b": vals[1], "c": vals[2]}
    return None


def _c_system(t, low):
    eqs = re.findall(r"(-?\s*\d*\s*x\s*[+-]\s*\d*\s*y)\s*=\s*(" + NUM + ")", normalize_math(t))
    if len(eqs) < 2:
        return None
    rows = []
    for lhs, rhs in eqs[:2]:
        s = lhs.replace(" ", "")
        mx = re.match(r"^(-?\d*)x([+-]\d*)y$", s)
        if not mx:
            return None
        a = mx.group(1)
        b = mx.group(2)
        a = -1 if a == "-" else (1 if a == "" else int(a))
        b = -1 if b == "-" else (1 if b == "+" else int(b))
        rows.append((a, b, _num(rhs)))
    (a1, b1, c1), (a2, b2, c2) = rows
    if c1 is None or c2 is None or a1 * b2 - a2 * b1 == 0:
        return None
    return "system_2x2", {"a1": a1, "b1": b1, "c1": c1, "a2": a2, "b2": b2, "c2": c2}


def _c_line(t, low):
    pts = re.findall(r"\(\s*(" + NUM + r")\s*,\s*(" + NUM + r")\s*\)", t)
    if "slope" in low or "eğim" in low:
        sm = re.search(r"slope\s*(?:of|is|=|m\s*=)?\s*(" + NUM + ")", low) or \
            re.search(r"m\s*=\s*(" + NUM + ")", t)
        if sm and pts:
            raw = normalize_math(sm.group(1))
            if "/" in raw:
                n, d = raw.split("/", 1)
                mn, md = int(float(n)), int(float(d))
            else:
                v = _num(raw)
                if v is None or v != int(v):
                    return None
                mn, md = int(v), 1
            if md == 0:
                return None
            if md < 0:
                mn, md = -mn, -md
            x1, y1 = _num(pts[0][0]), _num(pts[0][1])
            if None in (x1, y1):
                return None
            return "line_slope_point", {"mn": mn, "md": md, "x1": x1, "y1": y1}
    if len(pts) >= 2 and re.search(r"\bline\b|slope|doğru|eğim", low):
        (x1, y1), (x2, y2) = [(_num(a), _num(b)) for a, b in pts[:2]]
        if None in (x1, y1, x2, y2) or (x1, y1) == (x2, y2):
            return None
        if re.search(r"distance|midpoint|uzaklık|orta nokta", low):
            return "distance_midpoint", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        return "line_two_points", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    if len(pts) >= 2 and re.search(r"distance|midpoint|uzaklık|orta nokta", low):
        (x1, y1), (x2, y2) = [(_num(a), _num(b)) for a, b in pts[:2]]
        if None in (x1, y1, x2, y2):
            return None
        return "distance_midpoint", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    return None


def _c_pythagorean(t, low):
    if not re.search(r"right triangle|hypotenuse|pythag|dik üçgen|hipotenüs", low):
        return None
    m = re.search(r"legs?\s*(?:of\s*length|of|are|measuring)?\s*(\d+(?:\.\d+)?)\s*(?:and|,)\s*(\d+(?:\.\d+)?)", low)
    if not m:
        m = re.search(r"(?:a|leg)\s*=\s*(\d+(?:\.\d+)?)\D{1,12}(?:b|leg)\s*=\s*(\d+(?:\.\d+)?)", low)
    if not m:
        return None
    a, b = _num(m.group(1)), _num(m.group(2))
    if not a or not b:
        return None
    return "pythagorean", {"a": a, "b": b}


def _c_circle(t, low):
    if not re.search(r"circle|daire|çember", low):
        return None
    m = re.search(r"radius\s*(?:of|is|=)?\s*(\d+(?:\.\d+)?)", low) or re.search(r"\br\s*=\s*(\d+(?:\.\d+)?)", low) \
        or re.search(r"yarıçap\w*\s*(\d+(?:\.\d+)?)", low)
    r = _num(m.group(1)) if m else None
    if r is None:
        d = re.search(r"diameter\s*(?:of|is|=)?\s*(\d+(?:\.\d+)?)|çap\w*\s*(\d+(?:\.\d+)?)", low)
        if d:
            v = _num(d.group(1) or d.group(2))
            r = v / 2 if v else None
    if not r or r > 1000:
        return None
    return "circle_area", {"r": r}


def _c_dice(t, low):
    if not re.search(r"\bdice\b|\bdie\b|zar", low):
        return None
    m = re.search(r"(\d+|two|three|iki|üç)\s*(?:fair\s*)?(?:six-sided\s*)?(?:dice|zar)", low)
    words = {"two": 2, "three": 3, "iki": 2, "üç": 3}
    n = 2
    if m:
        n = words.get(m.group(1)) or int(m.group(1))
    if not 1 <= n <= 4:
        return None
    return "dice_sum", {"dice": n, "trials": 600}


def _c_order_ops(t, low):
    if not re.search(r"evaluate|simplify|calculate|compute|order of operations|pemdas|hesapla|işlem", low):
        return None
    for m in re.finditer(r"([\d\s+\-*/^().×÷·−]{7,80})", normalize_math(t)):
        e = m.group(1).strip().strip(".")
        if len(re.findall(r"\d+", e)) < 3 or not re.search(r"[+\-*/^]", e) or "/" * 2 in e:
            continue
        if e.count("(") != e.count(")"):
            continue
        if not re.fullmatch(r"[\d\s+\-*/^().]+", e):
            continue
        if re.fullmatch(r"[\d\s./-]+", e) and "-" in e and " " not in e:   # dates / ranges
            continue
        return "order_ops", {"expr": re.sub(r"\s+", " ", e)}
    return None


def _c_function(t, low):
    m = re.search(_FX, t)
    if not m:
        return None
    f = to_sympy_string(math_head(m.group(1)))
    if f is None:
        return None
    return "function_graph", {"f": f, "xmin": -6, "xmax": 6}


CLASSIFIERS = [_c_ode, _c_limit, _c_integral, _c_derivative, _c_surface, _c_system, _c_quadratic,
               _c_line, _c_pythagorean, _c_circle, _c_dice, _c_order_ops, _c_function]


def classify(text):
    """Bir metin penceresinden (tür, P) çıkarır; bulamazsa None."""
    t = normalize_math(text)
    low = t.lower()
    kinds = engine.all_templates()
    for fn in CLASSIFIERS:
        try:
            res = fn(t, low)
        except Exception:
            res = None
        if res and res[0] in kinds:
            return res
    return None


# ══════════════════════════════════════════════════════════════════════════
# Number changing (licence-friendly variations that keep the problem type)
# ══════════════════════════════════════════════════════════════════════════

def _nudge(v, rnd):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return v
    if isinstance(v, int):
        nv = v + rnd.choice([-2, -1, 1, 2])
        if v != 0 and nv == 0:
            nv = v + (3 if v > 0 else -3)
        if v > 0 and nv <= 0:
            nv = v + 1
        return nv
    nv = round(v * rnd.choice([0.8, 0.9, 1.1, 1.2, 1.25]), 4)
    return nv


def _nudge_expr(s, rnd):
    # change coefficients / constants, never exponents
    def rep(m):
        before = s[max(0, m.start() - 2):m.start()]
        if before.endswith("**") or before.endswith("^"):
            return m.group(0)
        v = int(m.group(0))
        return str(max(1, v + rnd.choice([-1, 1, 2])))
    return re.sub(r"(?<![\w.])\d+(?![\w.])", rep, s)


def change_numbers(kind, P, seed):
    rnd = random.Random(seed)
    for _ in range(6):
        Q = {}
        for k, v in P.items():
            if isinstance(v, str) and k in ("f", "expr", "P", "Q"):
                Q[k] = _nudge_expr(v, rnd)
            elif k in ("trials", "dice"):
                Q[k] = v
            elif kind == "line_slope_point" and k == "md":
                Q[k] = max(1, _nudge(v, rnd))
            else:
                Q[k] = _nudge(v, rnd)
        if kind == "derivative_expr" or kind == "limit_expr":
            Q["x0" if kind == "derivative_expr" else "a"] = P.get("x0" if kind == "derivative_expr" else "a")
        if _valid(kind, Q):
            return Q
    return dict(P)


def _valid(kind, P):
    try:
        sim = engine.Simulation({"id": "probe", "kind": kind, "q": ("", ""), "P": P}, "tr")
        sol = sim.solution()
        return bool(sol["answer"].strip())
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════
# Generic (own-wording) question texts for scanned items
# ══════════════════════════════════════════════════════════════════════════
SCAN_QUESTIONS = {
    "slope_field_expr": ("y' = {pretty_f}, y({x0}) = {y0} başlangıç değer problemini incele.",
                         "Study the initial value problem y' = {pretty_f}, y({x0}) = {y0}."),
    "limit_expr": ("x → {a} iken {pretty_f} ifadesinin limitini bul.",
                   "Find the limit of {pretty_f} as x → {a}."),
    "integral_expr": ("{pretty_f} fonksiyonunun [{a}, {b}] aralığındaki belirli integralini hesapla.",
                      "Evaluate the definite integral of {pretty_f} on [{a}, {b}]."),
    "derivative_expr": ("f(x) = {pretty_f} için f'(x)'i ve x = {x0} noktasındaki teğeti bul.",
                        "For f(x) = {pretty_f}, find f'(x) and the tangent line at x = {x0}."),
    "surface_3d": ("z = {pretty_f} yüzeyini incele.", "Explore the surface z = {pretty_f}."),
    "system_2x2": ("Denklem sistemini çöz: {eq1}, {eq2}", "Solve the system: {eq1}, {eq2}"),
    "quadratic": ("{expr} = 0 denklemini çöz.", "Solve {expr} = 0."),
    "line_slope_point": ("Eğimi {m} olan ve {point} noktasından geçen doğruyu bul.",
                         "Find the line with slope {m} through {point}."),
    "line_two_points": ("{A} ve {B} noktalarından geçen doğruyu bul.", "Find the line through {A} and {B}."),
    "distance_midpoint": ("({x1}, {y1}) ve ({x2}, {y2}) arasındaki uzaklığı ve orta noktayı bul.",
                          "Find the distance and midpoint between ({x1}, {y1}) and ({x2}, {y2})."),
    "pythagorean": ("Dik kenarları {a} ve {b} olan dik üçgenin hipotenüsünü bul.",
                    "Find the hypotenuse of a right triangle with legs {a} and {b}."),
    "circle_area": ("Yarıçapı {r} olan dairenin alanını ve çevresini bul.",
                    "Find the area and circumference of a circle of radius {r}."),
    "dice_sum": ("{dice} zar atıldığında toplamın dağılımını incele.",
                 "Explore the distribution of the sum of {dice} dice."),
    "order_ops": ("İşlem önceliğiyle hesapla: {pretty_expr}", "Evaluate using the order of operations: {pretty_expr}"),
    "function_graph": ("f(x) = {pretty_f} fonksiyonunun grafiğini incele.", "Graph and study f(x) = {pretty_f}."),
}


def _make_example(kind, P, file, page, course_key, n):
    tpl = engine.all_templates()[kind]
    h = hashlib.sha1(f"{file}|{page}|{kind}|{sorted(P.items())}".encode("utf-8")).hexdigest()[:10]
    t_tr, t_en = tpl["title"]
    q = SCAN_QUESTIONS.get(kind, ("{title}", "{title}"))
    return {
        "id": f"scan-{h}",
        "kind": kind,
        "course": course_key or tpl["course"],
        "title": (f"{t_tr} · kaynak örnek {n}", f"{t_en} · source example {n}"),
        "q": q,
        "P": P,
        "source": {"file": str(file), "page": page},
    }


# ══════════════════════════════════════════════════════════════════════════
# Scan with a small on-disk cache (math content only — no book text)
# ══════════════════════════════════════════════════════════════════════════

def _cache_path():
    try:
        from app_paths import exports_dir
        d = exports_dir() / "course_simulations"
        d.mkdir(parents=True, exist_ok=True)
        return d / "scan_cache_v1.json"
    except Exception:
        return None


def _load_cache():
    p = _cache_path()
    if p and p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache):
    p = _cache_path()
    if p:
        try:
            p.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


def extract_items(path):
    """Tek dosyadan [(sayfa, tür, P), ...] — yalnızca matematiksel içerik."""
    items, seen, exprs = [], set(), set()
    for page, text in page_texts(path):
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for i in range(len(lines)):
            for w in (1, 2, 3):
                if i + w > len(lines):
                    break
                res = classify(" ".join(lines[i:i + w])[:500])
                if not res:
                    continue
                kind, P = res
                key = (kind, json.dumps(P, sort_keys=True))
                expr = P.get("f") if isinstance(P.get("f"), str) else None
                if key in seen or (kind == "function_graph" and expr in exprs):
                    break
                seen.add(key)
                if expr:
                    exprs.add(expr)
                items.append((page, kind, P))
                if len(items) >= MAX_PER_FILE:
                    return items
                break
    return items


def scan(path, course_key="", change=True, progress=None, cancelled=None):
    """Bir konu klasörünü/dosyasını tarar; çalıştırılabilir örnek listesi döndürür.

    Dönen sözlük: {"examples": [...], "files": n, "pdf_support": bool,
                   "skipped_pdfs": n}
    """
    files = resource_files(path)
    cache = _load_cache()
    out, seen = [], set()
    skipped = 0
    for idx, f in enumerate(files):
        if cancelled and cancelled():
            break
        if progress:
            progress(idx, len(files), f.name)
        if f.suffix.lower() == ".pdf" and not pdf_support():
            skipped += 1
            continue
        try:
            st = f.stat()
            ck = f"{f}|{st.st_size}|{int(st.st_mtime)}"
        except Exception:
            ck = str(f)
        items = cache.get(ck)
        if items is None:
            items = [list(t) for t in extract_items(f)]
            cache[ck] = items
        for page, kind, P in items:
            if kind not in engine.all_templates():
                continue
            if change:
                seed = int(hashlib.sha1(f"{f.name}{page}{kind}{P}".encode("utf-8")).hexdigest()[:8], 16)
                P = change_numbers(kind, P, seed)
            elif not _valid(kind, P):
                continue
            key = (kind, json.dumps(P, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            out.append(_make_example(kind, P, f, page, course_key, len(out) + 1))
            if len(out) >= MAX_TOTAL:
                break
        if len(out) >= MAX_TOTAL:
            break
    _save_cache(cache)
    if progress:
        progress(len(files), len(files), "")
    return {"examples": out, "files": len(files), "pdf_support": pdf_support(),
            "skipped_pdfs": skipped}
