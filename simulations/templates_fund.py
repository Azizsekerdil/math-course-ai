# -*- coding: utf-8 -*-
"""Temel matematik simülasyonları: tam sayılar (sayı doğrusu), kesirler,
işlem önceliği, yüzdeler, üslü sayılar, oran-orantı, EBOB-EKOK, alan-çevre,
asal çarpanlar ve ondalık sayılar.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Sorular kurs
kitaplarından KOPYALANMAZ: kendi ifademizle yazılmış, sayıları değiştirilmiş
tipik ders örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["number_line"] = {
    "course": "fund",
    "title": ("Sayı doğrusunda tam sayılarla toplama ve çıkarma",
              "Adding and subtracting integers on a number line"),
    "topics": ["integers", "adding integers", "subtracting integers", "negative numbers",
               "number line", "signed numbers", "integer operations", "opposite numbers",
               "tam sayılar", "sayı doğrusu", "negatif sayılar", "tam sayılarla toplama",
               "tam sayılarla çıkarma", "tamsayılar"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Rectangle


def _s(v):
    return str(v).replace("-", "−")


def _p(v):
    return f"(−{abs(v)})" if v < 0 else str(v)


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def _parts(P):
    a = int(round(float(P.get("a", 0))))
    b = int(round(float(P.get("b", 0))))
    op = "-" if str(P.get("op", "+")).strip() in ("-", "−", "–") else "+"
    move = b if op == "+" else -b
    return a, b, op, move, a + move


def _expr(a, b, op):
    return f"{_s(a)} {'+' if op == '+' else '−'} {_p(b)}"


def _nice(x):
    if x <= 1:
        return 1
    mag = 10 ** int(math.floor(math.log10(x)))
    for m in (1, 2, 5, 10):
        if m * mag >= x:
            return int(m * mag)
    return int(10 * mag)


def solve(P):
    a, b, op, move, r = _parts(P)
    ex = _expr(a, b, op)
    steps = [(f"Başlangıç: sayı doğrusunda {_s(a)} noktası", f"Start at {_s(a)} on the number line")]
    if op == "-":
        steps.append((f"Çıkarmak, tersini eklemektir: {ex} = {_s(a)} + {_p(-b)}",
                      f"Subtracting means adding the opposite: {ex} = {_s(a)} + {_p(-b)}"))
    if move > 0:
        steps.append((f"{_p(move)} pozitif → {move} birim SAĞA git",
                      f"{_p(move)} is positive → move {move} units RIGHT"))
    elif move < 0:
        steps.append((f"{_p(move)} negatif → {-move} birim SOLA git",
                      f"{_p(move)} is negative → move {-move} units LEFT"))
    else:
        steps.append(("0 eklemek konumu değiştirmez", "Adding 0 does not move you"))
    if a != 0 and move != 0:
        if (a > 0) == (move > 0):
            steps.append((f"İşaretler aynı: mutlak değerler toplanır ({abs(a)} + {abs(move)} = "
                           f"{abs(a) + abs(move)}), ortak işaret korunur",
                           f"Same signs: add the absolute values ({abs(a)} + {abs(move)} = "
                           f"{abs(a) + abs(move)}) and keep the common sign"))
        elif abs(a) == abs(move):
            steps.append(("Zıt işaretli eşit büyüklükte sayılar: toplam 0",
                          "Opposites with the same size cancel: the sum is 0"))
        else:
            big = a if abs(a) > abs(move) else move
            hi_, lo_ = max(abs(a), abs(move)), min(abs(a), abs(move))
            steps.append((f"İşaretler farklı: {hi_} − {lo_} = {hi_ - lo_}; mutlak değeri büyük olanın "
                           f"({_s(big)}) işareti alınır",
                           f"Different signs: {hi_} − {lo_} = {hi_ - lo_}; take the sign of the number "
                           f"with the larger absolute value ({_s(big)})"))
    steps.append((f"Varış noktası {_s(r)}  ⇒  {ex} = {_s(r)}", f"Landing point {_s(r)}  ⇒  {ex} = {_s(r)}"))
    return {"answer": f"{ex} = {_s(r)}", "steps": steps, "fmt": {"expr": ex, "aa": _s(a), "bb": _s(b)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, op, move, r = _parts(P)
    ex = _expr(a, b, op)
    n = abs(move)
    st = 1 if n <= 12 else _nice(n / 10.0)
    H = int(math.ceil(n / float(st))) if n else 0
    sg = 1 if move >= 0 else -1
    pts = [a + sg * min(k * st, n) for k in range(H + 1)]
    lo, hi = min(a, r, 0), max(a, r, 0)
    span = max(hi - lo, 1)
    tstep = _nice(span / 18.0)
    pad = max(2 * tstep, int(math.ceil(span * 0.1)))
    lo, hi = lo - pad, hi + pad
    L, R = lo - 0.035 * (hi - lo), hi + 0.035 * (hi - lo)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.03)
    ax.axis("off")
    ax.set_xlim(L, R)
    hgt = 1.3 if st == 1 else 1.7
    if H == 1:
        hgt = 1.9
    ax.set_ylim(-2.6, max(3.2, hgt + 1.95))
    ax.add_patch(Rectangle((L, -0.1), 0 - L, 0.2, fc="#FEE2E2", ec="none", zorder=0))
    ax.add_patch(Rectangle((0, -0.1), R, 0.2, fc="#DBEAFE", ec="none", zorder=0))
    ax.plot([L, R], [0, 0], color="#374151", lw=2, zorder=1)
    ax.plot([R], [0], marker=">", ms=10, color="#374151")
    ax.plot([L], [0], marker="<", ms=10, color="#374151")
    first = int(math.ceil(lo / float(tstep))) * tstep
    nt = int((hi - first) // tstep) + 1
    fs_t = 11 if nt <= 16 else 9
    xs, ys = [], []
    v = first
    while v <= hi:
        xs += [v, v, np.nan]
        ys += [-0.24, 0.24, np.nan]
        ax.text(v, -0.38, _s(v), ha="center", va="top", fontsize=fs_t,
                color="#111827" if v == 0 else "#374151", fontweight="bold" if v == 0 else "normal")
        v += tstep
    ax.plot(xs, ys, color="#374151", lw=1.4)
    if tstep > 1 and (hi - lo) <= 150:
        mx, my = [], []
        for u in range(lo, hi + 1):
            if u % tstep:
                mx += [u, u, np.nan]
                my += [-0.1, 0.1, np.nan]
        ax.plot(mx, my, color="#9CA3AF", lw=0.8)
    ax.text(L + 0.01 * (R - L), -2.45, "← negatif" if tr else "← negative", color="#DC2626", fontsize=10)
    ax.text(R - 0.01 * (R - L), -2.45, "pozitif →" if tr else "positive →", color="#2563EB",
            fontsize=10, ha="right")
    tt = np.linspace(0, 1, 40)
    arcs = []
    for k in range(H):
        x0_, x1_ = pts[k], pts[k + 1]
        X = x0_ + (x1_ - x0_) * tt
        Y = hgt * np.sin(np.pi * tt)
        ln, = ax.plot([], [], color="#E07B39", lw=2.4, zorder=3)
        tip, = ax.plot([], [], marker="v", ms=7, color="#E07B39", zorder=3)
        lab_txt = str(k + 1) if st == 1 else (("+" if sg > 0 else "−") + str(abs(x1_ - x0_)))
        lab = ax.text((x0_ + x1_) / 2.0, hgt + 0.1, "", ha="center", va="bottom",
                      fontsize=9 if st == 1 else 11, color="#E07B39", fontweight="bold")
        arcs.append((X, Y, ln, tip, lab, lab_txt, x1_))
    start_dot, = ax.plot([], [], "o", ms=12, color="#2563EB", zorder=5)
    start_lab = ax.text(a, -1.15, ("başla: " if tr else "start: ") + _s(a), ha="center", va="center",
                        fontsize=11, color="#2563EB", fontweight="bold", alpha=0)
    frog, = ax.plot([], [], "o", ms=11, color="#E07B39", mec="white", mew=1.5, zorder=6)
    band = Rectangle((min(a, r), -0.1), abs(r - a), 0.2, fc="#E07B39", alpha=0.5, ec="none", zorder=2)
    ax.add_patch(band)
    res_dot, = ax.plot([], [], "o", ms=14, color="#DC2626", zorder=7)
    res_lab = ax.text(r, -1.8, ("sonuç: " if tr else "result: ") + _s(r), ha="center", va="center",
                      fontsize=13, color="#DC2626", fontweight="bold", alpha=0)
    ttl = ax.text(0.5, 1.02, "", transform=ax.transAxes, ha="center", va="bottom", fontsize=17,
                  fontweight="bold", color="#111827")
    info = ax.text(0.01, 0.985, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    T0, T1, N = 34, 124, 150
    conv = f" = {_s(a)} + {_p(-b)}" if op == "-" else ""

    def update(i):
        on = i >= 6
        start_dot.set_data([a], [0]) if on else start_dot.set_data([], [])
        start_lab.set_alpha(_r(i, 6, 12))
        prog = _r(i, T0, T1) * H
        cur, done = a, 0
        for k, (X, Y, ln, tip, lab, lab_txt, x1_) in enumerate(arcs):
            f = min(1.0, max(0.0, prog - k))
            if f <= 0:
                ln.set_data([], [])
                tip.set_data([], [])
                lab.set_text("")
                continue
            m = max(2, int(round(f * len(X))))
            ln.set_data(X[:m], Y[:m])
            if f >= 1:
                tip.set_data([x1_], [0.32])
                lab.set_text(lab_txt)
                cur = x1_
                done = abs(x1_ - a)
            else:
                tip.set_data([], [])
                lab.set_text("")
        if H and 0 < prog < H:
            k = int(prog)
            f = prog - k
            fx, fy = pts[k] + (pts[k + 1] - pts[k]) * f, hgt * np.sin(np.pi * f)
        else:
            fx, fy = (r if (H and prog >= H) else a), 0.0
        fin = i >= T1
        if on and not fin:
            frog.set_data([fx], [fy])
        else:
            frog.set_data([], [])
        band.set_visible(fin and r != a)
        res_dot.set_data([r], [0]) if fin else res_dot.set_data([], [])
        res_lab.set_alpha(_r(i, T1, T1 + 6))
        if fin:
            ttl.set_text(f"{ex}{conv} = {_s(r)}")
            ttl.set_color("#DC2626")
        else:
            ttl.set_text(f"{ex}{conv if i >= 12 else ''} = ?")
            ttl.set_color("#111827")
        if i < 12:
            info.set_text("1) Sayı doğrusu: sağa gidildikçe sayılar büyür" if tr else
                          "1) Number line: numbers grow to the right")
        elif i < T0:
            if op == "-":
                info.set_text((f"2) Çıkarma = tersini ekleme: {ex} = {_s(a)} + {_p(-b)}") if tr else
                              (f"2) Subtract = add the opposite: {ex} = {_s(a)} + {_p(-b)}"))
            elif move >= 0:
                info.set_text((f"2) {_p(move)} pozitif → {n} birim sağa") if tr else
                              (f"2) {_p(move)} is positive → {n} units to the right"))
            else:
                info.set_text((f"2) {_p(move)} negatif → {n} birim sola") if tr else
                              (f"2) {_p(move)} is negative → {n} units to the left"))
        elif not fin:
            if n == 0:
                info.set_text("3) 0 birim: yerinde kal" if tr else "3) 0 units: stay where you are")
            else:
                info.set_text((f"3) {'Sağa' if move > 0 else 'Sola'} zıpla: {done}/{n} birim, konum {_s(cur)}")
                              if tr else
                              (f"3) Jump {'right' if move > 0 else 'left'}: {done}/{n} units, now at {_s(cur)}"))
        else:
            info.set_text((f"4) Varış noktası {_s(r)}  ⇒  {ex} = {_s(r)}") if tr else
                          (f"4) We land on {_s(r)}  ⇒  {ex} = {_s(r)}"))
        return []

    return N, update


def vary(P, rnd):
    a0, b0, op, _, _ = _parts(P)
    sa = -1 if a0 < 0 else 1
    sb = -1 if b0 < 0 else 1
    while True:
        a = sa * rnd.randint(1, 9)
        b = sb * rnd.randint(2, 9)
        if b != a:
            return {"a": a, "b": b, "op": op}
''',
}
EXAMPLES += [
    {"id": "fund-numline-1", "kind": "number_line",
     "title": ("Pozitif ile negatifin toplamı", "Adding a positive and a negative"),
     "q": ("Sayı doğrusunu kullanarak {expr} işleminin sonucunu bul.",
           "Use a number line to find {expr}."),
     "P": {"a": 3, "b": -7, "op": "+"}},
    {"id": "fund-numline-2", "kind": "number_line",
     "title": ("Negatif bir sayıyı çıkarmak", "Subtracting a negative number"),
     "q": ("{expr} işlemini sayı doğrusunda göster ve sonucu bul.",
           "Show {expr} on a number line and find the result."),
     "P": {"a": -4, "b": -6, "op": "-"}},
    {"id": "fund-numline-3", "kind": "number_line", "topics": ["temperature", "sıcaklık", "word problem"],
     "title": ("Sözel problem: sıcaklık değişimi", "Word problem: temperature change"),
     "q": ("Sabah hava sıcaklığı {aa} °C idi; öğlene kadar {bb} derece yükseldi. Öğlen sıcaklık kaç "
           "derecedir? ({expr})",
           "The morning temperature was {aa} °C and it rose by {bb} degrees by noon. What was the "
           "temperature at noon? ({expr})"),
     "P": {"a": -5, "b": 9, "op": "+"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["fraction_add"] = {
    "course": "fund",
    "title": ("Kesirlerle toplama ve çıkarma", "Adding and subtracting fractions"),
    "topics": ["fractions", "adding fractions", "subtracting fractions", "common denominator",
               "least common denominator", "unlike denominators", "equivalent fractions",
               "simplifying fractions", "mixed numbers", "kesirler", "kesirlerde toplama",
               "kesirlerde çıkarma", "payda eşitleme", "denk kesirler", "sadeleştirme",
               "kesirlerle işlemler"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle


def _f(v):
    v = Fraction(v)
    s = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    return s.replace("-", "−")


def _nd(n, d):
    s = f"{abs(n)}/{d}"
    return ("−" + s) if n < 0 else s


def _tx(n, d):
    body = (r"\frac{" + str(abs(n)) + "}{" + str(d) + "}") if d != 1 else str(abs(n))
    return ("-" + body) if n < 0 else body


def _mixed(v):
    v = Fraction(v)
    if v.denominator == 1 or abs(v) < 1:
        return "", ""
    w = abs(v.numerator) // v.denominator
    rem = abs(v.numerator) % v.denominator
    sg = "−" if v < 0 else ""
    return (f"{sg}{w} {rem}/{v.denominator}",
            ("-" if v < 0 else "") + str(w) + r"\frac{" + str(rem) + "}{" + str(v.denominator) + "}")


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def _sm(m):
    return m * m * (3 - 2 * m)


def _parts(P):
    a, b, c, d = (int(round(float(P.get(k, 1)))) for k in ("a", "b", "c", "d"))
    op = "-" if str(P.get("op", "+")).strip() in ("-", "−", "–") else "+"
    if b < 0:
        a, b = -a, -b
    if d < 0:
        c, d = -c, -d
    return a, b, c, d, op


def _expr(a, b, c, d, op):
    second = _nd(c, d)
    if c < 0:
        second = "(" + second + ")"
    return f"{_nd(a, b)} {'+' if op == '+' else '−'} {second}"


def _calc(a, b, c, d, op):
    L = b * d // math.gcd(b, d)
    m1, m2 = L // b, L // d
    A, C = a * m1, c * m2
    S = A + C if op == "+" else A - C
    res = Fraction(S, L)
    g = math.gcd(abs(S), L) if S else L
    return L, m1, m2, A, C, S, res, g


def solve(P):
    a, b, c, d, op = _parts(P)
    ex = _expr(a, b, c, d, op)
    fmt = {"expr": ex, "f1": _nd(a, b), "f2": _nd(c, d)}
    if b == 0 or d == 0:
        msg = ("Payda 0 olamaz: kesir tanımsız", "A denominator cannot be 0: the fraction is undefined")
        return {"answer": msg, "steps": [(f"İfade: {ex}", f"Expression: {ex}"), msg], "fmt": fmt}
    L, m1, m2, A, C, S, res, g = _calc(a, b, c, d, op)
    sym = "+" if op == "+" else "−"
    steps = []
    if b == d:
        steps.append((f"Paydalar zaten eşit ({b}); doğrudan paylarla işlem yapılır.",
                      f"The denominators already match ({b}); work with the numerators directly."))
    else:
        steps.append((f"Paydalar farklı ({b} ve {d}): önce paydalar eşitlenir.",
                      f"Unlike denominators ({b} and {d}): first find a common denominator."))
        steps.append((f"Ortak payda = EKOK({b}, {d}) = {L}",
                      f"Least common denominator = lcm({b}, {d}) = {L}"))
        for n_, d_, m_, N_ in ((a, b, m1, A), (c, d, m2, C)):
            if m_ == 1:
                steps.append((f"{_nd(n_, d_)} kesrinin paydası zaten {L}", f"{_nd(n_, d_)} already has denominator {L}"))
            else:
                steps.append((f"{_nd(n_, d_)} = ({n_}·{m_})/({d_}·{m_}) = {_nd(N_, L)}",
                              f"{_nd(n_, d_)} = ({n_}·{m_})/({d_}·{m_}) = {_nd(N_, L)}"))
    steps.append((f"Payları {'topla' if op == '+' else 'çıkar'}, payda aynı kalır: {_nd(A, L)} {sym} "
                   f"{_nd(C, L)} = ({A} {sym} {C})/{L} = {_nd(S, L)}",
                   f"{'Add' if op == '+' else 'Subtract'} the numerators, keep the denominator: "
                   f"{_nd(A, L)} {sym} {_nd(C, L)} = ({A} {sym} {C})/{L} = {_nd(S, L)}"))
    if S == 0:
        steps.append(("Sonuç 0", "The result is 0"))
    elif g > 1:
        steps.append((f"Sadeleştir (pay ve paydayı {g} ile böl): {_nd(S, L)} = {_f(res)}",
                      f"Simplify (divide top and bottom by {g}): {_nd(S, L)} = {_f(res)}"))
    else:
        steps.append((f"{_nd(S, L)} en sade hâlde (EBOB = 1)", f"{_nd(S, L)} is already in lowest terms (gcd = 1)"))
    mx = _mixed(res)[0]
    if mx:
        steps.append((f"Tam sayılı kesir olarak: {_f(res)} = {mx}", f"As a mixed number: {_f(res)} = {mx}"))
    ans = f"{ex} = {_f(res)}" + (f" = {mx}" if mx else "")
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, c, d, op = _parts(P)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.03)
    ax.axis("off")
    info = ax.text(0.01, 0.985, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    if b == 0 or d == 0:
        ax.text(0.5, 0.5, "Payda 0 olamaz!" if tr else "A denominator cannot be 0!", ha="center",
                fontsize=18, color="#DC2626", transform=ax.transAxes)

        def upd0(i):
            info.set_text(_expr(a, b, c, d, op))
            return []
        return 60, upd0
    L, m1, m2, A, C, S, res, g = _calc(a, b, c, d, op)
    p, q = res.numerator, res.denominator
    v1 = Fraction(a, b)
    w2 = Fraction(c, d)
    v2 = w2 if op == "+" else -w2
    r = v1 + v2
    lo = int(math.floor(min(0, v1, w2, r)))
    hi = int(math.ceil(max(0, v1, w2, r)))
    if hi - lo < 1:
        hi = lo + 1
    W = hi - lo
    xl = lo - 0.03 * W / 0.62
    ax.set_xlim(xl, xl + W / 0.62)
    ax.set_ylim(-0.75, 3.85)
    rows = [2.45, 1.25, 0.05]
    hgt = 0.62
    for y in rows:
        for k in range(lo, hi):
            ax.add_patch(Rectangle((k, y), 1, hgt, fill=False, ec="#6B7280", lw=1.4, zorder=4))
    if lo < 0:
        ax.plot([0, 0], [rows[2] - 0.15, rows[0] + hgt + 0.15], color="#111827", lw=1.2, ls=":")

    def seps(y, qq):
        xs, ys = [], []
        if qq * W > 400:
            return xs, ys
        for k in range(lo * qq + 1, hi * qq):
            if k % qq == 0:
                continue
            xs += [k / float(qq), k / float(qq), np.nan]
            ys += [y, y + hgt, np.nan]
        return xs, ys

    def mk(y, qq, style, lw, color):
        xs, ys = seps(y, qq)
        ln, = ax.plot(xs, ys, ls=style, lw=lw, color=color, zorder=5)
        return ln

    BLUE, ORANGE = (0.145, 0.388, 0.922, 0.85), (0.878, 0.482, 0.224, 0.85)
    bar1 = Rectangle((0, rows[0]), 0, hgt, fc=BLUE, ec="none", zorder=2)
    bar2 = Rectangle((0, rows[1]), 0, hgt, fc=ORANGE, ec="none", zorder=2)
    ax.add_patch(bar1)
    ax.add_patch(bar2)
    coarse1 = mk(rows[0], b, "-", 1.3, "#374151")
    coarse2 = mk(rows[1], d, "-", 1.3, "#374151")
    fine1 = mk(rows[0], L, "--", 0.9, "#111827")
    fine2 = mk(rows[1], L, "--", 0.9, "#111827")
    fine3 = mk(rows[2], L, "--", 0.9, "#111827")
    coarse3 = mk(rows[2], q, "-", 2.0, "#111827")
    cp1 = Rectangle((min(0, v1), rows[0]), abs(float(v1)), hgt, fc=BLUE, ec="white", lw=1, zorder=2)
    x2a = float(min(0, w2))
    x2b = float(min(v1, v1 + v2))
    cp2 = Rectangle((x2a, rows[1]), abs(float(w2)), hgt, fc=ORANGE, ec="white", lw=1, zorder=3)
    ax.add_patch(cp1)
    ax.add_patch(cp2)
    resf = Rectangle((0, rows[2] - 0.06), 0, hgt + 0.12, fill=False, ec="#16A34A", lw=3.5, zorder=6)
    ax.add_patch(resf)
    tf = ax.get_yaxis_transform()
    lab1 = ax.text(0.715, rows[0] + hgt / 2, "", transform=tf, va="center", fontsize=20, color="#2563EB")
    lab2 = ax.text(0.715, rows[1] + hgt / 2, "", transform=tf, va="center", fontsize=20, color="#E07B39")
    lab3 = ax.text(0.715, rows[2] + hgt / 2, "", transform=tf, va="center", fontsize=19, color="#16A34A")
    ax.text(0.685, rows[1] + hgt / 2, "+" if op == "+" else "−", transform=tf, va="center", ha="center",
            fontsize=22, fontweight="bold", color="#111827")
    ax.text(0.685, rows[2] + hgt / 2, "=", transform=tf, va="center", ha="center",
            fontsize=22, fontweight="bold", color="#111827")
    ax.plot([0.67, 0.99], [rows[1] - 0.25, rows[1] - 0.25], transform=tf, color="#9CA3AF", lw=1)
    sym = "+" if op == "+" else "−"
    mtx = _mixed(res)[1]
    t1a = "$" + _tx(a, b) + "$"
    t1b = ("$" + _tx(a, b) + "=" + _tx(A, L) + "$") if L != b else t1a
    t2a = "$" + _tx(c, d) + "$"
    t2b = ("$" + _tx(c, d) + "=" + _tx(C, L) + "$") if L != d else t2a
    t3a = "$" + _tx(S, L) + "$"
    t3b = "$" + _tx(S, L) + ("=" + _tx(p, q) if g > 1 and S != 0 else "") + ("=" + mtx if mtx else "") + "$"
    if b == d:
        info2 = (f"2) Paydalar eşit ({b}): parçalar zaten aynı boyda", f"2) Same denominator ({b}): the pieces already match")
    else:
        info2 = (f"2) EKOK({b}, {d}) = {L}: her bütünü {L} eşit parçaya böl",
                 f"2) lcm({b}, {d}) = {L}: cut every whole into {L} equal pieces")
    info3 = ((f"3) {A} mavi parça ile {C} turuncu parçayı birleştir" if op == "+" else
              f"3) {A} mavi parçadan {C} parçayı çıkar (taralı)"),
             (f"3) Put the {A} blue pieces and {C} orange pieces together" if op == "+" else
              f"3) Take {C} pieces away from the {A} blue pieces (hatched)"))
    info4 = (f"4) {A} {sym} {C} = {S} parça  ⇒  {_nd(S, L)}", f"4) {A} {sym} {C} = {S} pieces  ⇒  {_nd(S, L)}")
    if S != 0 and g > 1:
        info5 = (f"5) Sadeleştir (÷{g}): {_nd(S, L)} = {_f(res)}", f"5) Simplify (÷{g}): {_nd(S, L)} = {_f(res)}")
    else:
        info5 = (f"5) Sonuç: {_f(res)}", f"5) Result: {_f(res)}")
    mx = _mixed(res)[0]
    if mx:
        info5 = (info5[0] + f" = {mx}", info5[1] + f" = {mx}")
    N = 160

    def update(i):
        g1 = _r(i, 0, 14)
        w = abs(float(v1)) * g1
        bar1.set_width(w)
        bar1.set_x(0 if v1 >= 0 else -w)
        g2 = _r(i, 14, 28)
        w = abs(float(w2)) * g2
        bar2.set_width(w)
        bar2.set_x(0 if w2 >= 0 else -w)
        fade = _r(i, 28, 44)
        fine1.set_alpha(fade * 0.85 if L != b else 0)
        fine2.set_alpha(fade * 0.85 if L != d else 0)
        m1_ = _sm(_r(i, 58, 72))
        cp1.set_visible(i >= 58)
        cp1.set_y(rows[0] + (rows[2] - rows[0]) * m1_)
        m2_ = _sm(_r(i, 72, 86))
        cp2.set_visible(i >= 72)
        cp2.set_xy((x2a + (x2b - x2a) * m2_, rows[1] + (rows[2] - rows[1]) * m2_))
        if op == "-" and i >= 86:
            cp2.set_facecolor((1, 1, 1, 0.55))
            cp2.set_edgecolor("#DC2626")
            cp2.set_hatch("xx")
        else:
            cp2.set_facecolor(ORANGE)
            cp2.set_edgecolor("white")
            cp2.set_hatch(None)
        simp = g > 1 and S != 0 and q != L
        fine3.set_alpha(_r(i, 86, 96) * (1 - _r(i, 116, 130) if simp else 1) * 0.85)
        coarse3.set_alpha(_r(i, 116, 130) if simp else 0)
        gr = _r(i, 86, 104)
        w = abs(float(r)) * gr
        resf.set_width(w)
        resf.set_x(0 if r >= 0 else -w)
        resf.set_visible(i >= 86 and r != 0)
        lab1.set_text(t1b if i >= 44 else (t1a if i >= 4 else ""))
        lab2.set_text(t2b if i >= 44 else (t2a if i >= 18 else ""))
        lab3.set_text(t3b if i >= 116 else (t3a if i >= 92 else "?"))
        lab3.set_color("#16A34A" if i >= 92 else "#9CA3AF")
        k = 0 if i < 28 else (1 if i < 58 else (2 if i < 86 else (3 if i < 116 else 4)))
        txt = [(f"1) Kesirleri şerit olarak çiz: {_nd(a, b)} ve {_nd(c, d)}",
                f"1) Draw each fraction as a bar: {_nd(a, b)} and {_nd(c, d)}"),
               info2, info3, info4, info5][k]
        info.set_text(txt[0] if tr else txt[1])
        return []

    return N, update


def vary(P, rnd):
    a0, b0, c0, d0, op = _parts(P)
    dens = [2, 3, 4, 5, 6, 8, 10, 12]
    while True:
        b, d = rnd.choice(dens), rnd.choice(dens)
        if b == d or b * d // math.gcd(b, d) > 24:
            continue
        a, c = rnd.randint(1, b - 1), rnd.randint(1, d - 1)
        if math.gcd(a, b) != 1 or math.gcd(c, d) != 1:
            continue
        if op == "-" and Fraction(a, b) <= Fraction(c, d):
            continue
        return {"a": a, "b": b, "c": c, "d": d, "op": op}
''',
}
EXAMPLES += [
    {"id": "fund-frac-1", "kind": "fraction_add",
     "title": ("Paydaları farklı kesirleri toplama", "Adding fractions with unlike denominators"),
     "q": ("{expr} işlemini yap; sonucu en sade hâliyle yaz.",
           "Compute {expr} and write the answer in lowest terms."),
     "P": {"a": 2, "b": 3, "c": 1, "d": 4, "op": "+"}},
    {"id": "fund-frac-2", "kind": "fraction_add",
     "title": ("Kesirlerde çıkarma ve sadeleştirme", "Subtracting and simplifying fractions"),
     "q": ("{expr} farkını bul ve sadeleştir.", "Find {expr} and simplify."),
     "P": {"a": 5, "b": 6, "c": 1, "d": 3, "op": "-"}},
    {"id": "fund-frac-3", "kind": "fraction_add", "topics": ["recipe", "tarif", "word problem"],
     "title": ("Sözel problem: tarifteki un", "Word problem: flour in a recipe"),
     "q": ("Bir kek için {f1} su bardağı un, kurabiye için {f2} su bardağı un gerekiyor. Toplam kaç "
           "bardak un gerekir? ({expr})",
           "A cake needs {f1} cup of flour and a batch of cookies needs {f2} cup. How much flour is "
           "needed altogether? ({expr})"),
     "P": {"a": 3, "b": 4, "c": 2, "d": 3, "op": "+"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["order_ops"] = {
    "course": "fund",
    "title": ("İşlem önceliği", "Order of operations"),
    "topics": ["order of operations", "pemdas", "bodmas", "bidmas", "evaluating expressions",
               "numerical expressions", "arithmetic expressions", "operations with integers",
               "işlem önceliği", "işlem sırası", "dört işlem", "aritmetik ifade", "parantezli işlemler",
               "ifadenin değeri"],
    "code": r'''
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle, FancyBboxPatch

_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸",
        "9": "⁹", "-": "⁻"}
_SUPIN = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8",
          "⁹": "9", "⁻": "-"}
_SYM = {"+": "+", "-": "−", "*": "×", "/": "÷"}
_MAXTOK = 140


class _Err(Exception):
    pass


def _clean(s):
    s = str(s)
    if "=" in s:
        s = s.split("=")[0]
    for k, v in (("**", "^"), ("×", "*"), ("·", "*"), ("∙", "*"), ("⋅", "*"), ("÷", "/"), (":", "/"),
                 ("−", "-"), ("–", "-"), ("—", "-"), ("[", "("), ("]", ")"), ("{", "("), ("}", ")"),
                 (" ", " ")):
        s = s.replace(k, v)
    letters = [ch for ch in s if ch.isalpha()]
    if letters and all(ch in "xX" for ch in letters):
        s = s.replace("x", "*").replace("X", "*")
    out = []
    k = 0
    while k < len(s):
        if s[k] in _SUPIN:
            j = k
            buf = ""
            while j < len(s) and s[j] in _SUPIN:
                buf += _SUPIN[s[j]]
                j += 1
            out.append(("^(" + buf + ")") if buf.startswith("-") else ("^" + buf))
            k = j
        else:
            out.append(s[k])
            k += 1
    return "".join(out).strip().rstrip("?").strip()


def _tokens(s):
    toks = []
    k, n = 0, len(s)
    while k < n:
        ch = s[k]
        if ch in " \t\r\n":
            k += 1
            continue
        if ch.isdigit() or (ch in ".," and k + 1 < n and s[k + 1].isdigit()):
            j = k
            while j < n and (s[j].isdigit() or s[j] in ".,"):
                j += 1
            txt = s[k:j].rstrip(".,")
            k = j
            groups = txt.split(",")
            if "," in txt and "." in txt:
                txt = txt.replace(",", "")
            elif txt.count(",") > 1:
                txt = txt.replace(",", "")
            elif "," in txt and len(groups[1]) == 3 and groups[0] not in ("", "0") and len(groups[0]) <= 3:
                txt = txt.replace(",", "")
            elif "," in txt:
                txt = txt.replace(",", ".")
            if txt.count(".") > 1:
                txt = txt.replace(".", "")
            try:
                val = Fraction(txt)
            except (ValueError, ZeroDivisionError):
                raise _Err((f"Sayı okunamadı: {txt}", f"Cannot read the number {txt}"))
            toks.append(["n", val, "." in txt])
            continue
        if ch in "+-*/^":
            toks.append(["o", ch])
            k += 1
            continue
        if ch in "()":
            toks.append([ch])
            k += 1
            continue
        raise _Err((f"Tanınmayan simge: '{ch}'", f"Unrecognised symbol: '{ch}'"))
    out = []
    for t in toks:
        if out and ((out[-1][0] in ("n", ")") and t[0] == "(") or (out[-1][0] == ")" and t[0] == "n")):
            out.append(["o", "*"])
        out.append(t)
    if not out:
        raise _Err(("Boş ifade", "Empty expression"))
    if len(out) > _MAXTOK:
        raise _Err(("İfade çok uzun", "The expression is too long"))
    return out


def _parse(toks):
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        t = peek()
        pos[0] += 1
        return t

    def isop(t, chars):
        return t is not None and t[0] == "o" and t[1] in chars

    def expr():
        node = term()
        while isop(peek(), "+-"):
            op = take()[1]
            node = ["b", op, node, term()]
        return node

    def term():
        node = unary()
        while isop(peek(), "*/"):
            op = take()[1]
            node = ["b", op, node, unary()]
        return node

    def unary():
        t = peek()
        if isop(t, "-"):
            take()
            return ["u", unary()]
        if isop(t, "+"):
            take()
            return unary()
        return power()

    def power():
        base = atom()
        if isop(peek(), "^"):
            take()
            return ["b", "^", base, unary()]
        return base

    def atom():
        t = take()
        if t is None:
            raise _Err(("İfade yarım kalmış (sonda işlem var)", "The expression ends with an operator"))
        if t[0] == "n":
            return ["n", t[1], t[2]]
        if t[0] == "(":
            inner = expr()
            c = take()
            if c is None or c[0] != ")":
                raise _Err(("Kapanmayan parantez var", "There is an unclosed parenthesis"))
            return ["p", inner]
        sym = _SYM.get(t[1], t[1]) if t[0] == "o" else t[0]
        raise _Err((f"Beklenmeyen simge: '{sym}'", f"Unexpected symbol: '{sym}'"))

    tree = expr()
    if pos[0] != len(toks):
        raise _Err(("Fazladan simge veya eşleşmeyen parantez", "Extra symbol or unmatched parenthesis"))
    return tree


def _norm(nd, track):
    k = nd[0]
    if k == "n":
        return
    if k in ("p", "u"):
        _norm(nd[1], track)
        c = nd[1]
        if c[0] == "n":
            was = c is track[0]
            nd[:] = ["n", c[1] if k == "p" else -c[1], c[2]]
            if was:
                track[0] = nd
        return
    _norm(nd[2], track)
    _norm(nd[3], track)


def _places(v):
    for k in range(0, 9):
        if (v * 10 ** k).denominator == 1:
            return k
    return None


def _num(v, dec, tr):
    v = Fraction(v)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        k = _places(v) if dec else None
        if k is not None:
            n = abs(v.numerator) * 10 ** k // v.denominator
            t = str(n).rjust(k + 1, "0")
            s = ("-" if v < 0 else "") + t[:-k] + "." + t[-k:]
        else:
            s = f"{v.numerator}/{v.denominator}"
    s = s.replace("-", "−")
    return s.replace(".", ",") if tr else s


def _render(tree, tr, target=None):
    buf = []
    cnt = [0]
    span = [-1, -1]

    def emit(s):
        buf.append(s)
        cnt[0] += len(s)

    def go(nd, left, whole):
        if nd is target:
            span[0] = cnt[0]
        k = nd[0]
        if k == "n":
            s = _num(nd[1], nd[2], tr)
            if not whole and ((nd[1] < 0 and not left) or "/" in s):
                s = "(" + s + ")"
            emit(s)
        elif k == "p":
            emit("(")
            go(nd[1], True, False)
            emit(")")
        elif k == "u":
            if not left:
                emit("(")
            emit("−")
            go(nd[1], False, False)
            if not left:
                emit(")")
        elif nd[1] == "^":
            go(nd[2], False, False)
            e = nd[3]
            if e[0] == "n" and e[1].denominator == 1 and abs(e[1]) < 10 ** 6:
                emit("".join(_SUP[ch] for ch in str(e[1].numerator)))
            else:
                emit("^")
                if e[0] == "b":
                    emit("(")
                    go(e, True, False)
                    emit(")")
                else:
                    go(e, False, False)
        else:
            go(nd[2], left, False)
            emit(" " + _SYM[nd[1]] + " ")
            go(nd[3], False, False)
        if nd is target:
            span[1] = cnt[0]

    go(tree, True, True)
    return "".join(buf), (span[0], span[1])


def _inorder(nd, out):
    k = nd[0]
    if k == "n":
        return
    if k == "p":
        out.append(nd)
        return
    if k == "u":
        _inorder(nd[1], out)
        return
    _inorder(nd[2], out)
    out.append(nd)
    _inorder(nd[3], out)


def _next(scope, inpar):
    seq = []
    _inorder(scope, seq)
    for nd in seq:
        if nd[0] == "p":
            return _next(nd[1], True)
    for group in ("^", "*/", "+-"):
        for nd in seq:
            if nd[0] == "b" and nd[1] in group and nd[2][0] == "n" and nd[3][0] == "n":
                return nd, inpar
    return None, inpar


def _iroot(n, q):
    r = int(round(abs(n) ** (1.0 / q)))
    for c in (r - 1, r, r + 1):
        if c >= 0 and c ** q == abs(n):
            return c
    return None


def _pow(x, y):
    big = (("Sayı çok büyük; hesaplanamıyor", "The number is too large to compute"))
    if y.denominator == 1:
        e = y.numerator
        if x == 0 and e < 0:
            raise _Err(("0'ın negatif kuvveti tanımsızdır (sıfıra bölme)",
                        "0 to a negative power is undefined (division by zero)"))
        digits = max(len(str(abs(x.numerator))), len(str(x.denominator)))
        if abs(e) > 400 or (abs(x) != 1 and x != 0 and abs(e) * digits > 45):
            raise _Err(big)
        return x ** e
    p, q = y.numerator, y.denominator
    if x < 0 and q % 2 == 0:
        raise _Err(("Negatif sayının çift dereceden kökü reel değildir",
                    "An even root of a negative number is not real"))
    if q > 12 or abs(p) > 60:
        raise _Err(big)
    rn, rd = _iroot(x.numerator, q), _iroot(x.denominator, q)
    if rn is None or rd is None:
        raise _Err(("Sonuç rasyonel değil (köklü sayı); tam değer yazılamaz",
                    "The result is irrational (a root); no exact value"))
    base = Fraction(rn, rd) * (-1 if x < 0 else 1)
    return _pow(base, Fraction(p))


def _apply(op, x, y):
    if op == "+":
        r = x + y
    elif op == "-":
        r = x - y
    elif op == "*":
        r = x * y
    elif op == "/":
        if y == 0:
            raise _Err(("Sıfıra bölme tanımsızdır!", "Division by zero is undefined!"))
        r = x / y
    else:
        r = _pow(x, y)
    if abs(r.numerator) > 10 ** 40 or r.denominator > 10 ** 40:
        raise _Err(("Sayı çok büyük; hesaplanamıyor", "The number is too large to compute"))
    return r


def _run(expr, tr):
    R = {"lines": [], "red": [], "green": [], "ops": [], "cats": [], "vals": [], "err": None,
         "perr": False, "val": None, "dec": False}
    raw = _clean(expr)
    try:
        tree = _parse(_tokens(raw))
    except _Err as e:
        R["err"] = e.args[0]
        R["perr"] = True
        R["lines"] = [raw[:90] or "?"]
        R["red"], R["green"] = [None], [None]
        return R
    except (RuntimeError, ValueError, ZeroDivisionError, OverflowError):
        R["err"] = ("İfade çözümlenemedi", "The expression could not be read")
        R["perr"] = True
        R["lines"] = [raw[:90] or "?"]
        R["red"], R["green"] = [None], [None]
        return R
    track = [None]
    _norm(tree, track)
    R["lines"].append(_render(tree, tr)[0])
    R["green"].append(None)
    guard = 0
    while tree[0] != "n" and guard < 200:
        guard += 1
        node, inpar = _next(tree, False)
        if node is None:
            R["err"] = ("İfade çözümlenemedi", "The expression could not be read")
            break
        R["red"].append(_render(tree, tr, node)[1])
        op, x, y = node[1], node[2][1], node[3][1]
        dec = node[2][2] or node[3][2]
        desc = _render(node, tr)[0]
        R["cats"].append((inpar, op))
        try:
            val = _apply(op, x, y)
        except _Err as e:
            R["err"] = e.args[0]
            R["ops"].append(desc)
            break
        except (OverflowError, ValueError, ZeroDivisionError):
            R["err"] = ("Sayı çok büyük; hesaplanamıyor", "The number is too large to compute")
            R["ops"].append(desc)
            break
        R["ops"].append(f"{desc} = {_num(val, dec, tr)}")
        R["vals"].append(val)
        node[:] = ["n", val, dec]
        track[0] = node
        _norm(tree, track)
        s2, sp2 = _render(tree, tr, track[0])
        R["lines"].append(s2)
        R["green"].append(sp2)
    while len(R["red"]) < len(R["lines"]):
        R["red"].append(None)
    if tree[0] == "n" and R["err"] is None:
        R["val"], R["dec"] = tree[1], tree[2]
    return R


def _final(v, dec, tr):
    s = _num(v, dec, tr)
    if v.denominator != 1 and "/" in s:
        k = _places(v)
        if k is not None:
            s += " = " + _num(v, True, tr)
        else:
            t = f"{float(v):.4f}"
            s += " ≈ " + (t.replace(".", ",") if tr else t).replace("-", "−")
    return s


def _cat(inpar, op):
    base = {"^": ("Üs", "Exponent"), "*": ("Çarpma (soldan sağa)", "Multiply (left to right)"),
            "/": ("Bölme (soldan sağa)", "Divide (left to right)"),
            "+": ("Toplama (soldan sağa)", "Add (left to right)"),
            "-": ("Çıkarma (soldan sağa)", "Subtract (left to right)")}[op]
    if inpar:
        return ("Parantez içi · " + base[0], "Inside parentheses · " + base[1])
    return base


_ORDER = ("Sıra: parantez → üs → çarpma/bölme (soldan sağa) → toplama/çıkarma (soldan sağa)",
          "Order: parentheses → exponents → multiply/divide (left to right) → add/subtract (left to right)")


def solve(P):
    rt = _run(P.get("expr", ""), True)
    re_ = _run(P.get("expr", ""), False)
    steps = [(f"İfade: {rt['lines'][0]}", f"Expression: {re_['lines'][0]}")]
    if not rt["perr"]:
        steps.append(_ORDER)
    for k in range(len(rt["ops"])):
        c = _cat(*rt["cats"][k])
        if k + 1 < len(rt["lines"]):
            steps.append((f"{c[0]}: {rt['ops'][k]}  ⇒  {rt['lines'][k + 1]}",
                          f"{c[1]}: {re_['ops'][k]}  ⇒  {re_['lines'][k + 1]}"))
        else:
            steps.append((f"{c[0]}: {rt['ops'][k]}", f"{c[1]}: {re_['ops'][k]}"))
    if rt["err"] is not None:
        steps.append((f"Hata: {rt['err'][0]}", f"Error: {rt['err'][1]}"))
        ans = (f"Tanımsız / hata: {rt['err'][0]}", f"Undefined / error: {rt['err'][1]}")
    else:
        vt, ve = _final(rt["val"], rt["dec"], True), _final(re_["val"], re_["dec"], False)
        steps.append((f"Sonuç: {vt}", f"Result: {ve}"))
        ans = (f"{rt['lines'][0]} = {vt}", f"{re_['lines'][0]} = {ve}") if len(rt["lines"]) > 1 else (vt, ve)
    return {"answer": ans, "steps": steps, "fmt": {"pretty": (rt["lines"][0], re_["lines"][0])}}


def _safe(s):
    return str(s).replace("$", r"\$")


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    R = _run(P.get("expr", ""), tr)
    lines = [_safe(s) for s in R["lines"]]
    S = len(R["ops"])
    gs = fig.add_gridspec(1, 2, width_ratios=[3.1, 1], left=0.02, right=0.985, top=0.95, bottom=0.03,
                          wspace=0.03)
    ax = fig.add_subplot(gs[0, 0])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    lad = fig.add_subplot(gs[0, 1])
    lad.axis("off")
    lad.set_xlim(0, 1)
    lad.set_ylim(0, 1)
    fw, fh = fig.get_size_inches()
    pos = ax.get_position()
    aw, ah = pos.width * fw * 72.0, pos.height * fh * 72.0
    X0 = 0.075
    maxlen = max(6, max(len(s) for s in R["lines"]))
    ytop, ybot = 0.76, 0.06
    nwant = min(len(lines), 7)
    fs = min(22.0, (1.0 - X0 - 0.03) * aw / (0.602 * maxlen))
    if nwant > 1:
        fs = min(fs, (ytop - ybot) * ah / (1.75 * (nwant - 1)))
    fs = max(6.0, fs)
    dy = 1.75 * fs / ah
    K = max(1, int((ytop - ybot) / dy + 1e-9) + 1)
    cw = 0.602 * fs / aw
    bh = 1.35 * fs / ah
    fsn = max(6.0, min(10.0, fs * 0.55))
    cwn = 0.602 * fsn / aw
    mono = "DejaVu Sans Mono"
    items = []
    for j, s in enumerate(lines):
        t = ax.text(X0, 0, s, family=mono, fontsize=fs, va="center", ha="left", color="#111827", zorder=5)
        tag = ax.text(0.0, 0, f"{j}." if j else "", fontsize=max(6.0, fs * 0.55), va="center",
                      color="#9CA3AF")
        red = Rectangle((0, 0), 0, bh, fill=False, ec="#DC2626", lw=2.2, zorder=6)
        grn = Rectangle((0, 0), 0, bh, fc="#DCFCE7", ec="#16A34A", lw=1.2, zorder=2)
        ax.add_patch(red)
        ax.add_patch(grn)
        note_s = _safe(R["ops"][j - 1]) if 1 <= j <= len(R["ops"]) else ""
        fits = note_s and (X0 + len(R["lines"][j]) * cw + 0.03 + len(note_s) * cwn <= 1.0)
        note = ax.text(1.0, 0, note_s if fits else "", family=mono, fontsize=fsn, ha="right", va="center",
                       color="#6B7280")
        rs = R["red"][j] if j < len(R["red"]) else None
        gsp = R["green"][j] if j < len(R["green"]) else None
        if rs is not None and rs[0] >= 0:
            red.set_x(X0 + (rs[0] - 0.2) * cw)
            red.set_width((rs[1] - rs[0] + 0.4) * cw)
        if gsp is not None and gsp[0] >= 0:
            grn.set_x(X0 + (gsp[0] - 0.2) * cw)
            grn.set_width((gsp[1] - gsp[0] + 0.4) * cw)
        items.append((t, tag, red, grn, note, rs is not None and rs[0] >= 0, gsp is not None and gsp[0] >= 0))
    mark = ax.text(0, 0, "", fontsize=fs * 1.1, va="center", fontweight="bold")
    info = ax.text(0.0, 0.995, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"), wrap=False)
    sc = fw / 8.0
    lad.text(0.5, 0.965, "Öncelik sırası" if tr else "Order of operations", ha="center", va="top",
             fontsize=11 * sc, fontweight="bold", color="#374151")
    rows = [("( )", "Parantez", "Parentheses", "en içteki önce", "innermost first"),
            ("xⁿ", "Üsler", "Exponents", "", ""),
            ("× ÷", "Çarpma / Bölme", "Multiply / Divide", "soldan sağa", "left to right"),
            ("+ −", "Toplama / Çıkarma", "Add / Subtract", "soldan sağa", "left to right")]
    cols = ["#EDE9FE", "#FFEDD5", "#DBEAFE", "#DCFCE7"]
    edges = ["#7C3AED", "#E07B39", "#2563EB", "#16A34A"]
    boxes = []
    for k, rw in enumerate(rows):
        yc = 0.79 - k * 0.2
        bx = FancyBboxPatch((0.05, yc - 0.075), 0.9, 0.15, boxstyle="round,pad=0.005,rounding_size=0.03",
                            fc="#F9FAFB", ec="#D1D5DB", lw=1.2, transform=lad.transAxes)
        lad.add_patch(bx)
        lad.text(0.09, yc, f"{k + 1}", fontsize=9 * sc, va="center", color="#6B7280")
        lad.text(0.25, yc, rw[0], fontsize=13 * sc, va="center", ha="center", fontweight="bold",
                 color=edges[k])
        lad.text(0.38, yc + (0.025 if rw[3] else 0), rw[1] if tr else rw[2], fontsize=7.8 * sc, va="center",
                 color="#111827")
        if rw[3]:
            lad.text(0.38, yc - 0.035, rw[3] if tr else rw[4], fontsize=7 * sc, va="center", color="#6B7280")
        boxes.append(bx)
    intro = 14.0
    per = min(24.0, max(2.0, 132.0 / max(1, S)))
    tail = 26.0
    N = int(round(intro + S * per + tail))
    if N < 60:
        N = 60
    N = min(N, 180)

    def born(j):
        if j == 0:
            return 0.0
        return intro + (j - 1) * per + 0.45 * per

    def alpha_line(i, j):
        t0 = born(j)
        if i < t0:
            return 0.0
        span_ = 8.0 if j == 0 else max(1.0, 0.4 * per)
        return min(1.0, (i - t0 + 1.0) / span_)

    rowidx = {"^": 1, "*": 2, "/": 2, "+": 3, "-": 3}

    def update(i):
        f = 0
        for j in range(len(lines)):
            if alpha_line(i, j) > 0:
                f = j
        top = max(0, f - K + 1)
        stepf = (i - intro) / per
        kcur = int(stepf) if (i >= intro and stepf < S) else -1
        done = i >= intro + S * per
        for j, (t, tag, red, grn, note, has_r, has_g) in enumerate(items):
            al = alpha_line(i, j) if j >= top else 0.0
            vis = al > 0
            t.set_visible(vis)
            tag.set_visible(vis)
            note.set_visible(vis)
            y = ytop - (j - top) * dy
            t.set_y(y)
            tag.set_y(y)
            note.set_y(y)
            t.set_alpha(al)
            tag.set_alpha(al)
            note.set_alpha(al)
            red.set_y(y - bh / 2)
            grn.set_y(y - bh / 2)
            ts = intro + j * per
            if has_r and i >= ts and al > 0:
                ra = min(1.0, (i - ts + 1) / max(1.0, 0.3 * per))
                if i >= ts + per and not (R["err"] is not None and j == len(lines) - 1):
                    ra = 0.3
                red.set_visible(True)
                red.set_alpha(ra)
            else:
                red.set_visible(False)
            if has_g and al > 0:
                grn.set_visible(True)
                grn.set_alpha(al * (1.0 if i < intro + j * per else 0.55))
            else:
                grn.set_visible(False)
            t.set_color("#111827")
            t.set_fontweight("normal")
        last = len(lines) - 1
        if done and last >= top:
            yl = ytop - (last - top) * dy
            mark.set_position((X0 + len(R["lines"][last]) * cw + 0.02, yl))
            if R["err"] is None:
                mark.set_text("✓")
                mark.set_color("#16A34A")
                items[last][0].set_color("#15803D")
                items[last][0].set_fontweight("bold")
            else:
                mark.set_text("✗")
                mark.set_color("#DC2626")
        else:
            mark.set_text("")
        for k, bx in enumerate(boxes):
            bx.set_facecolor("#F9FAFB")
            bx.set_edgecolor("#D1D5DB")
            bx.set_linewidth(1.2)
        if 0 <= kcur < S:
            inpar, op = R["cats"][kcur]
            k = rowidx[op]
            boxes[k].set_facecolor(cols[k])
            boxes[k].set_edgecolor(edges[k])
            boxes[k].set_linewidth(2.4)
            if inpar:
                boxes[0].set_facecolor(cols[0])
                boxes[0].set_edgecolor(edges[0])
                boxes[0].set_linewidth(2.4)
        if R["perr"]:
            info.set_text(((f"Hata: {R['err'][0]}") if tr else (f"Error: {R['err'][1]}")) if i >= 10 else
                          ("İfade okunuyor…" if tr else "Reading the expression…"))
            info.set_color("#DC2626" if i >= 10 else "#111827")
        elif i < intro:
            info.set_text("Kural: önce parantez, sonra üs, sonra × ÷, en son + −\n"
                          "(aynı düzeydeki işlemler soldan sağa)" if tr else
                          "Rule: parentheses, then exponents, then × ÷, then + −\n"
                          "(operations on the same level go left to right)")
            info.set_color("#111827")
        elif not done:
            c = _cat(*R["cats"][kcur])
            info.set_text(f"{'Adım' if tr else 'Step'} {kcur + 1}/{S}: {c[0] if tr else c[1]}\n"
                          f"{_safe(R['ops'][kcur])}")
            info.set_color("#111827")
        elif R["err"] is not None:
            info.set_text(f"{'Hata' if tr else 'Error'}: {R['err'][0] if tr else R['err'][1]}\n"
                          f"{_safe(R['ops'][-1]) if R['ops'] else ''}")
            info.set_color("#DC2626")
        else:
            info.set_text(f"{'Sonuç' if tr else 'Result'}: {_safe(_final(R['val'], R['dec'], tr))}")
            info.set_color("#15803D")
        return []

    return N, update


def vary(P, rnd):
    src = _clean(P.get("expr", ""))
    try:
        toks = _tokens(src)
    except _Err:
        toks = None
    forms = ["{a} + {b}*({c} - {d})^2 / {e}", "({a} + {b})*{c} - {d}^2", "{a} - {b}*{c} + {d}*{e}",
             "({a} - {b})^2 + {c}*{d}", "{a}*({b} + {c}) - {d}*{e}", "{a}^2 - ({b} + {c}*{d})"]
    for attempt in range(400):
        if toks and attempt < 320:
            parts = []
            prev = None
            for t in toks:
                if t[0] == "n":
                    if prev is not None and prev[0] == "o" and prev[1] == "^":
                        v = rnd.choice([2, 2, 3])
                    elif prev is not None and prev[0] == "o" and prev[1] == "/":
                        v = rnd.randint(2, 9)
                    else:
                        v = rnd.randint(1, 12)
                    parts.append(str(v))
                elif t[0] == "o":
                    unary = t[1] == "-" and (prev is None or prev[0] in ("o", "("))
                    parts.append("-" if unary else {"+": " + ", "-": " - ", "*": "*", "/": " / ",
                                                    "^": "^"}[t[1]])
                else:
                    parts.append(t[0])
                prev = t
            cand = "".join(parts).strip()
        else:
            vals = {k: rnd.randint(1, 12) for k in "abcde"}
            cand = rnd.choice(forms).format_map(vals)
        R = _run(cand, False)
        if (R["err"] is None and R["val"] is not None and len(R["ops"]) >= 2 and abs(R["val"]) <= 999
                and all(v.denominator == 1 for v in R["vals"]) and cand != src):
            return {"expr": cand}
    return {"expr": "3 + 4*(6 - 2)^2 / 8"}
''',
}
EXAMPLES += [
    {"id": "fund-ops-1", "kind": "order_ops",
     "title": ("Parantez, üs ve dört işlem", "Parentheses, exponents and the four operations"),
     "q": ("İşlem önceliğine dikkat ederek hesapla: {pretty}",
           "Evaluate using the order of operations: {pretty}"),
     "P": {"expr": "3 + 4*(6 - 2)^2 / 8"}},
    {"id": "fund-ops-2", "kind": "order_ops", "topics": ["shopping", "alışveriş", "word problem"],
     "title": ("Sözel problem: alışveriş hesabı", "Word problem: a shopping bill"),
     "q": ("Ece tanesi 12 TL olan 3 defter ve tanesi 5 TL olan 2 kalem alıp kasaya 100 TL verdi. "
           "Para üstü {pretty} işlemiyle bulunur. Kaç TL para üstü alır?",
           "Ece buys 3 notebooks at 12 each and 2 pens at 5 each and pays with 100. Her change is "
           "{pretty}. How much change does she get?"),
     "P": {"expr": "100 - (3*12 + 2*5)"}},
    {"id": "fund-ops-3", "kind": "order_ops", "topics": ["negative numbers", "negatif sayılar"],
     "title": ("Negatif sayılar ve üsler", "Negative numbers and powers"),
     "q": ("{pretty} ifadesinin değeri kaçtır? (−2² ile (−3)² farkına dikkat!)",
           "What is the value of {pretty}? (Watch the difference between −2² and (−3)²!)"),
     "P": {"expr": "-2^2 + (-3)^2*2 - 12/(-4)"}},
]

# ──────────────────────────────────────────────────────────────────────────
_PCT_HELPERS = r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle


def _fr(v):
    try:
        return Fraction(str(v).strip().replace(",", "."))
    except (ValueError, ZeroDivisionError):
        return Fraction(float(v)).limit_denominator(10 ** 6)


def _n(v, tr=True):
    v = Fraction(v)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        k = None
        for kk in range(1, 7):
            if (v * 10 ** kk).denominator == 1:
                k = kk
                break
        if k is not None:
            n = abs(v.numerator) * 10 ** k // v.denominator
            t = str(n).rjust(k + 1, "0")
            s = ("-" if v < 0 else "") + t[:-k] + "." + t[-k:]
        else:
            s = "≈" + f"{float(v):.2f}".rstrip("0").rstrip(".")
    s = s.replace("-", "−")
    return s.replace(".", ",") if tr else s


def _pc(p, tr=True):
    sg = "−" if p < 0 else ""
    return (sg + "%" + _n(abs(p), True)) if tr else (sg + _n(abs(p), False) + "%")


_ONES = {"0": "ı", "1": "i", "2": "si", "3": "ü", "4": "ü", "5": "i", "6": "sı", "7": "si", "8": "i", "9": "u"}
_TENS = {"1": "u", "2": "si", "3": "u", "4": "ı", "5": "si", "6": "ı", "7": "i", "8": "i", "9": "ı"}


def _poss(s):
    digits = [ch for ch in s if ch.isdigit()]
    if not digits:
        return "'i"
    if "," in s or "." in s:
        return "'" + _ONES[digits[-1]]
    n = int("".join(digits))
    if n == 0:
        return "'ı"
    if n % 10:
        return "'" + _ONES[str(n % 10)]
    if n % 100:
        return "'" + _TENS[str((n // 10) % 10)]
    if n % 1000:
        return "'ü"
    if n % 1000000:
        return "'i"
    return "'u"


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def _sm(m):
    return m * m * (3 - 2 * m)
'''

TEMPLATES["percent_of"] = {
    "course": "fund",
    "title": ("Bir sayının yüzdesi", "Percent of a number"),
    "topics": ["percent", "percents", "percentage", "percent of a number", "finding a percent",
               "hundred grid", "yüzde", "yüzdeler", "yüzde hesaplama", "bir sayının yüzdesi",
               "yüzdelik"],
    "code": _PCT_HELPERS + r'''


def solve(P):
    p, T = _fr(P.get("pct", 0)), _fr(P.get("total", 0))
    unit = T / 100
    res = p * T / 100
    steps = [
        (f"{_pc(p, True)} = {_n(p, True)}/100 = {_n(p / 100, True)}",
         f"{_pc(p, False)} = {_n(p, False)}/100 = {_n(p / 100, False)}"),
        (f"Bütün ({_n(T, True)}) = 100 kare  ⇒  %1 = {_n(T, True)} ÷ 100 = {_n(unit, True)}",
         f"The whole ({_n(T, False)}) = 100 squares  ⇒  1% = {_n(T, False)} ÷ 100 = {_n(unit, False)}"),
        (f"{_pc(p, True)} = {_n(p, True)} kare × {_n(unit, True)} = {_n(res, True)}",
         f"{_pc(p, False)} = {_n(p, False)} squares × {_n(unit, False)} = {_n(res, False)}"),
        (f"Kısaca: {_n(p / 100, True)} × {_n(T, True)} = {_n(res, True)}",
         f"In one line: {_n(p / 100, False)} × {_n(T, False)} = {_n(res, False)}"),
    ]
    ptr = _pc(p, True)
    ans = (f"{_n(T, True)} sayısının {ptr}{_poss(ptr)} = {_n(res, True)}",
           f"{_pc(p, False)} of {_n(T, False)} = {_n(res, False)}")
    return {"answer": ans, "steps": steps,
            "fmt": {"pp": (ptr, _pc(p, False)), "ppi": (ptr + _poss(ptr), _pc(p, False)),
                    "tt": (_n(T, True), _n(T, False))}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    p, T = _fr(P.get("pct", 0)), _fr(P.get("total", 0))
    unit = T / 100
    res = p * T / 100
    pv = max(0.0, min(200.0, float(p)))
    G = 1 if pv <= 100 else 2
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.1], left=0.02, right=0.985, top=0.86, bottom=0.04,
                          wspace=0.06)
    axg = fig.add_subplot(gs[0, 0])
    axr = fig.add_subplot(gs[0, 1])
    axg.axis("off")
    axr.axis("off")
    axr.set_xlim(0, 1)
    axr.set_ylim(0, 1)
    ims = []
    gx, gy = [], []
    for g in range(G):
        ox = g * 10.8
        im = axg.imshow(np.ones((10, 10, 4)), extent=(ox, ox + 10, 0, 10), interpolation="nearest",
                        origin="upper", zorder=1)
        ims.append(im)
        for k in range(11):
            gx += [ox + k, ox + k, np.nan, ox, ox + 10, np.nan]
            gy += [0, 10, np.nan, k, k, np.nan]
    axg.plot(gx, gy, color="#9CA3AF", lw=0.8, zorder=2)
    for g in range(G):
        axg.add_patch(Rectangle((g * 10.8, 0), 10, 10, fill=False, ec="#374151", lw=1.8, zorder=3))
    axg.set_xlim(-0.3, 10 * G + 0.8 * (G - 1) + 0.3)
    axg.set_ylim(-1.6, 10.3)
    axg.set_aspect("equal")
    hl = Rectangle((0, 9), 1, 1, fill=False, ec="#E07B39", lw=3, zorder=4)
    axg.add_patch(hl)
    cnt = axg.text((10 * G + 0.8 * (G - 1)) / 2.0, -0.45, "", ha="center", va="top", fontsize=12,
                   fontweight="bold", color="#2563EB")
    idx = np.arange(100).reshape(10, 10)
    empty = np.array([1.0, 1.0, 1.0, 1.0])
    fillc = np.array([0.145, 0.388, 0.922, 0.85])
    fig.suptitle((f"{_n(T, True)} sayısının {_pc(p, True)}{_poss(_pc(p, True))} kaçtır?") if tr else
                 (f"What is {_pc(p, False)} of {_n(T, False)}?"), fontsize=15, fontweight="bold")
    info = axr.text(0.02, 0.985, "", transform=axr.transAxes, va="top", fontsize=11,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    x0, x1 = 0.06, 0.94
    smax = max(100.0, pv)
    xw = x0 + (x1 - x0) * 100.0 / smax
    xp = x0 + (x1 - x0) * pv / smax
    yb = 0.56
    axr.add_patch(Rectangle((x0, yb), xw - x0, 0.08, fill=False, ec="#374151", lw=1.6))
    pbar = Rectangle((x0, yb), 0, 0.08, fc="#2563EB", alpha=0.85, ec="none")
    axr.add_patch(pbar)
    lab = dict(ha="center", fontsize=10)
    axr.text(x0, yb + 0.1, "%0" if tr else "0%", va="bottom", color="#6B7280", **lab)
    axr.text(xw, yb + 0.1, "%100" if tr else "100%", va="bottom", color="#6B7280", **lab)
    axr.text(x0, yb - 0.02, "0", va="top", color="#6B7280", **lab)
    axr.text(xw, yb - 0.02, _n(T, tr), va="top", color="#6B7280", **lab)
    tp = axr.text(xp, yb + 0.17, _pc(p, tr), va="bottom", color="#2563EB", fontweight="bold", alpha=0, **lab)
    tv = axr.text(xp, yb - 0.09, _n(res, tr), va="top", color="#DC2626", fontweight="bold", alpha=0, **lab)
    mk, = axr.plot([], [], color="#DC2626", lw=1.5, ls="--")
    axr.text(0.5, yb + 0.28, "yüzde şeridi" if tr else "percent bar", ha="center", fontsize=10,
             color="#6B7280", style="italic")
    l1 = axr.text(0.04, 0.33, (f"%1 = {_n(T, True)} ÷ 100 = {_n(unit, True)}" if tr else
                               f"1% = {_n(T, False)} ÷ 100 = {_n(unit, False)}"),
                  fontsize=12, color="#E07B39", alpha=0)
    l2 = axr.text(0.04, 0.22, (f"{_pc(p, True)} = {_n(p, True)} × {_n(unit, True)} = {_n(res, True)}" if tr else
                               f"{_pc(p, False)} = {_n(p, False)} × {_n(unit, False)} = {_n(res, False)}"),
                  fontsize=12, color="#2563EB", alpha=0)
    ptr = _pc(p, True)
    l3 = axr.text(0.04, 0.08, (f"{_n(T, True)} sayısının {ptr}{_poss(ptr)} = {_n(res, True)}" if tr else
                               f"{_pc(p, False)} of {_n(T, False)} = {_n(res, False)}"),
                  fontsize=14, color="#16A34A", fontweight="bold", alpha=0,
                  bbox=dict(boxstyle="round", fc="#F0FDF4", ec="#16A34A"))
    l3.get_bbox_patch().set_alpha(0)
    N = 150

    def update(i):
        c = pv * _r(i, 30, 100)
        k = int(c)
        frac = c - k
        for g, im in enumerate(ims):
            gidx = idx + 100 * g
            arr = np.where((gidx < k)[:, :, None], fillc, empty)
            if frac > 1e-9:
                part = (gidx == k)[:, :, None]
                arr = np.where(part, np.array([0.145, 0.388, 0.922, 0.85 * frac + 0.0]), arr)
                arr[:, :, 3] = np.where(gidx == k, np.maximum(arr[:, :, 3], 0.15), arr[:, :, 3])
            im.set_data(arr)
        hl.set_visible(15 <= i < 34)
        if i < 30:
            cnt.set_text("")
        else:
            cd = p if (i >= 100 and p <= 200) else Fraction(k)
            cnt.set_text(f"{_n(cd, tr)} {'kare' if tr else 'squares'} × {_n(unit, tr)} = {_n(cd * unit, tr)}")
        l1.set_alpha(_r(i, 15, 22))
        l2.set_alpha(_r(i, 100, 106))
        a3 = _r(i, 125, 131)
        l3.set_alpha(a3)
        l3.get_bbox_patch().set_alpha(a3)
        g2 = _r(i, 100, 122)
        pbar.set_width((xp - x0) * g2)
        tp.set_alpha(_r(i, 118, 122))
        tv.set_alpha(_r(i, 118, 122))
        if i >= 118:
            mk.set_data([xp, xp], [yb - 0.08, yb + 0.16])
        else:
            mk.set_data([], [])
        if i < 15:
            info.set_text((f"1) Bütün = {_n(T, True)} → 100 eşit kareye böl") if tr else
                          (f"1) The whole = {_n(T, False)} → split it into 100 equal squares"))
        elif i < 30:
            info.set_text((f"2) Bir kare = %1 = {_n(unit, True)}") if tr else
                          (f"2) One square = 1% = {_n(unit, False)}"))
        elif i < 100:
            info.set_text((f"3) {_n(p, True)} kareyi boya") if tr else (f"3) Shade {_n(p, False)} squares"))
        elif i < 125:
            info.set_text((f"4) {_n(p, True)} × {_n(unit, True)} = {_n(res, True)}") if tr else
                          (f"4) {_n(p, False)} × {_n(unit, False)} = {_n(res, False)}"))
        else:
            info.set_text(("5) Sonuç: " if tr else "5) Result: ") + _n(res, tr))
        return []

    return N, update


def vary(P, rnd):
    p0 = _fr(P.get("pct", 10))
    if p0 > 100:
        pc = rnd.choice([110, 120, 125, 150, 175, 200])
    else:
        pc = rnd.choice([5, 10, 15, 20, 25, 30, 35, 40, 45, 60, 70, 75, 80, 90])
    step = 100 // math.gcd(pc, 100)
    lo_k = max(1, -(-20 // step))
    hi_k = max(lo_k, min(600 // step, lo_k + 30))
    return {"pct": pc, "total": step * rnd.randint(lo_k, hi_k)}
''',
}
EXAMPLES += [
    {"id": "fund-pctof-1", "kind": "percent_of",
     "title": ("Bir sayının yüzdesini bulma", "Finding a percent of a number"),
     "q": ("{tt} sayısının {ppi} kaçtır?", "What is {pp} of {tt}?"),
     "P": {"pct": 30, "total": 70}},
    {"id": "fund-pctof-2", "kind": "percent_of", "topics": ["word problem", "sözel problem"],
     "title": ("Sözel problem: sınıftaki öğrenciler", "Word problem: students in a class"),
     "q": ("{tt} kişilik bir sınıfta öğrencilerin {ppi} gözlük takıyor. Kaç öğrenci gözlük takıyor?",
           "In a class of {tt} students, {pp} wear glasses. How many students wear glasses?"),
     "P": {"pct": 35, "total": 40}},
    {"id": "fund-pctof-3", "kind": "percent_of", "topics": ["tip", "bahşiş", "decimal percent"],
     "title": ("Ondalıklı yüzde: bahşiş", "A decimal percent: the tip"),
     "q": ("{tt} TL'lik bir hesaba {pp} bahşiş bırakılacak. Bahşiş kaç TL'dir?",
           "A diner leaves a {pp} tip on a bill of {tt}. How large is the tip?"),
     "P": {"pct": 12.5, "total": 64}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["percent_change"] = {
    "course": "fund",
    "title": ("Yüzde değişim: artış ve azalış", "Percent change: increase and decrease"),
    "topics": ["percent change", "percent increase", "percent decrease", "discount", "markup",
               "sale price", "percent of change", "yüzde değişim", "yüzde artış", "yüzde azalış",
               "indirim", "zam", "kâr zarar", "kar zarar", "satış fiyatı"],
    "code": _PCT_HELPERS + r'''


def _calc(P):
    o, nw = _fr(P.get("old", 1)), _fr(P.get("new", 1))
    if o == 0:
        return o, nw, None, None
    ch = nw - o
    return o, nw, ch, ch / o * 100


def _word(pc, tr):
    if pc > 0:
        return "artış" if tr else "increase"
    if pc < 0:
        return "azalış" if tr else "decrease"
    return "değişim yok" if tr else "no change"


def _sg(v, tr):
    s = _n(abs(v), tr)
    return ("+" + s) if v > 0 else (("−" + s) if v < 0 else s)


def solve(P):
    o, nw, ch, pc = _calc(P)
    fmt = {"oo": (_n(o, True), _n(o, False)), "nn": (_n(nw, True), _n(nw, False))}
    if ch is None:
        msg = ("Başlangıç değeri 0 olduğundan yüzde değişim tanımsız", "The original value is 0, so percent change is undefined")
        return {"answer": msg, "steps": [("Yüzde değişim = değişim / eski × 100", "Percent change = change / original × 100"), msg],
                "fmt": fmt}
    ratio = ch / o
    steps = [
        (f"Değişim = yeni − eski = {_n(nw, True)} − {_n(o, True)} = {_sg(ch, True)}",
         f"Change = new − original = {_n(nw, False)} − {_n(o, False)} = {_sg(ch, False)}"),
        ("Yüzde değişim = (değişim ÷ eski değer) × 100", "Percent change = (change ÷ original value) × 100"),
        (f"= ({_sg(ch, True)} ÷ {_n(o, True)}) × 100 = {_n(ratio, True)} × 100 = {_pc(pc, True)}",
         f"= ({_sg(ch, False)} ÷ {_n(o, False)}) × 100 = {_n(ratio, False)} × 100 = {_pc(pc, False)}"),
    ]
    if pc > 0:
        steps.append(("Pozitif değişim → artış (zam)", "Positive change → increase (markup)"))
    elif pc < 0:
        steps.append(("Negatif değişim → azalış (indirim)", "Negative change → decrease (discount)"))
    mult = 1 + ratio
    steps.append((f"Kontrol: {_n(o, True)} × {_n(mult, True)} = {_n(o * mult, True)} ✓",
                   f"Check: {_n(o, False)} × {_n(mult, False)} = {_n(o * mult, False)} ✓"))
    ans = (f"{_pc(abs(pc), True)} {_word(pc, True)}", f"{_pc(abs(pc), False)} {_word(pc, False)}")
    fmt["pcs"] = ans
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    o, nw, ch, pc = _calc(P)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.08)
    info = ax.text(0.01, 0.985, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    if ch is None or o < 0 or nw < 0:
        ax.axis("off")
        ax.text(0.5, 0.5, ("Başlangıç değeri pozitif olmalı" if tr else "The original value must be positive"),
                transform=ax.transAxes, ha="center", fontsize=16, color="#DC2626")

        def upd0(i):
            return []
        return 60, upd0
    of, nf, cf = float(o), float(nw), float(ch)
    M = max(of, nf)
    up = cf >= 0
    ax.set_xlim(-0.8, 4.4)
    ax.set_ylim(0, M * 1.75)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks([0, 1.4])
    ax.set_xticklabels(["Eski" if tr else "Original", "Yeni" if tr else "New"], fontsize=12)
    ax.grid(axis="y", alpha=0.25)
    BW = 0.7
    oldb = Rectangle((-BW / 2, 0), BW, 0, fc="#2563EB", alpha=0.85)
    newb = Rectangle((1.4 - BW / 2, 0), BW, 0, fc="#60A5FA", alpha=0.9)
    extra = Rectangle((1.4 - BW / 2, of), BW, 0, fc="#16A34A", alpha=0.85)
    miss = Rectangle((1.4 - BW / 2, nf), BW, of - nf if not up else 0, fill=False, ec="#DC2626", ls="--",
                     lw=2, hatch="//")
    for pt in (oldb, newb, extra, miss):
        ax.add_patch(pt)
    lvl, = ax.plot([], [], ls="--", color="#6B7280", lw=1.2)
    sl_x, sl_y = [], []
    for k in range(1, 10):
        sl_x += [-BW / 2, BW / 2, np.nan]
        sl_y += [of * k / 10.0, of * k / 10.0, np.nan]
    slices, = ax.plot(sl_x, sl_y, color="white", lw=1.3)
    t_old = ax.text(0, 0, "", ha="center", va="bottom", fontsize=12, fontweight="bold", color="#2563EB")
    t_new = ax.text(1.4, 0, "", ha="center", va="bottom", fontsize=12, fontweight="bold", color="#1D4ED8")
    t_o100 = ax.text(0, of / 2, "%100" if tr else "100%", ha="center", va="center", fontsize=12,
                     color="white", fontweight="bold", alpha=0)
    pct_new = 100 + float(pc)
    t_n100 = ax.text(1.4, nf / 2, _pc(Fraction(pct_new).limit_denominator(1000), tr), ha="center",
                     va="center", fontsize=12, color="white", fontweight="bold", alpha=0)
    col = "#16A34A" if up else "#DC2626"
    arr, = ax.plot([], [], color=col, lw=2.5)
    arr_tip, = ax.plot([], [], marker="^" if up else "v", color=col, ms=11)
    t_ch = ax.text(2.05, (of + nf) / 2, "", va="center", fontsize=13, color=col, fontweight="bold")
    cp = Rectangle((BW / 2 + 0.05, 0), 0.22, abs(cf), fc=col, alpha=0.8, ec="none")
    ax.add_patch(cp)
    t_cp = ax.text(BW / 2 + 0.33, 0, "", va="center", fontsize=11, color=col, fontweight="bold")
    ratio = ch / o
    fl = [ax.text(0.97, 0.80 - 0.075 * k, "", transform=ax.transAxes, ha="right", va="top", fontsize=12,
                  color="#111827") for k in range(3)]
    flines = [((f"Değişim = {_n(nw, True)} − {_n(o, True)} = {_sg(ch, True)}"),
               (f"Change = {_n(nw, False)} − {_n(o, False)} = {_sg(ch, False)}")),
              ((f"{_sg(ch, True)} ÷ {_n(o, True)} = {_n(ratio, True)}"),
               (f"{_sg(ch, False)} ÷ {_n(o, False)} = {_n(ratio, False)}")),
              ((f"{_n(ratio, True)} × 100 = {_pc(pc, True)}"), (f"{_n(ratio, False)} × 100 = {_pc(pc, False)}"))]
    for k, t in enumerate(fl):
        t.set_text(flines[k][0] if tr else flines[k][1])
    big = ax.text(0.97, 0.56, (f"{_pc(abs(pc), True)} {_word(pc, True)}" if tr else
                               f"{_pc(abs(pc), False)} {_word(pc, False)}"),
                  transform=ax.transAxes, ha="right", va="top", fontsize=20, fontweight="bold", color=col,
                  alpha=0)
    N = 150

    def update(i):
        g = _sm(_r(i, 0, 25))
        oldb.set_height(of * g)
        t_old.set_position((0, of * g + M * 0.02))
        t_old.set_text(_n(o, tr) if i >= 4 else "")
        t_o100.set_alpha(_r(i, 20, 25))
        base = min(of, nf)
        g1 = _sm(_r(i, 25, 40))
        newb.set_height(base * g1)
        g2 = _r(i, 40, 50)
        if up:
            extra.set_height(cf * g2)
            miss.set_visible(False)
        else:
            extra.set_height(0)
            miss.set_visible(i >= 40)
            miss.set_alpha(g2)
        top_new = base * g1 + (cf * g2 if up else 0)
        t_new.set_position((1.4, max(top_new, (of if (not up and i >= 40) else 0)) + M * 0.02))
        t_new.set_text(_n(nw, tr) if i >= 40 else "")
        t_n100.set_position((1.4, nf / 2))
        t_n100.set_alpha(_r(i, 110, 115))
        if i >= 25:
            lvl.set_data([-BW / 2, 1.4 + BW / 2 + 0.5], [of, of])
        else:
            lvl.set_data([], [])
        a = _r(i, 50, 60)
        if i >= 50:
            yt = of + (nf - of) * a
            arr.set_data([1.95, 1.95], [of, yt])
            arr_tip.set_data([1.95], [yt])
            t_ch.set_text(_sg(ch, tr))
        else:
            arr.set_data([], [])
            arr_tip.set_data([], [])
            t_ch.set_text("")
        slices.set_alpha(_r(i, 80, 90))
        m = _sm(_r(i, 85, 105))
        cp.set_visible(i >= 85)
        y_from = of if up else nf
        cp.set_xy((1.4 + BW / 2 + 0.05 + (BW / 2 + 0.05 - 1.4 - BW / 2 - 0.05) * m, y_from * (1 - m)))
        t_cp.set_position((BW / 2 + 0.33, abs(cf) / 2))
        t_cp.set_text((f"= {_pc(abs(pc), True)}" if tr else f"= {_pc(abs(pc), False)}") if i >= 108 else "")
        fl[0].set_alpha(_r(i, 52, 58))
        fl[1].set_alpha(_r(i, 88, 94))
        fl[2].set_alpha(_r(i, 108, 114))
        big.set_alpha(_r(i, 115, 122))
        if i < 25:
            info.set_text((f"1) Eski (başlangıç) değer: {_n(o, True)} = %100") if tr else
                          (f"1) Original value: {_n(o, False)} = 100%"))
        elif i < 50:
            info.set_text((f"2) Yeni değer: {_n(nw, True)}") if tr else (f"2) New value: {_n(nw, False)}"))
        elif i < 85:
            info.set_text((f"3) Değişim: {_sg(ch, True)}") if tr else (f"3) Change: {_sg(ch, False)}"))
        elif i < 115:
            info.set_text("4) Değişimi ESKİ değerle karşılaştır (her dilim %10)" if tr else
                          "4) Compare the change with the ORIGINAL value (each slice is 10%)")
        else:
            info.set_text((f"5) Sonuç: {_pc(abs(pc), True)} {_word(pc, True)}") if tr else
                          (f"5) Result: {_pc(abs(pc), False)} {_word(pc, False)}"))
        return []

    return N, update


def vary(P, rnd):
    o0, n0 = _fr(P.get("old", 80)), _fr(P.get("new", 100))
    sign = 1 if n0 >= o0 else -1
    olds = [40, 50, 60, 80, 120, 150, 200, 240, 250, 400, 500]
    pcs = [10, 20, 25, 30, 40, 50, 60, 75] if sign > 0 else [10, 15, 20, 25, 30, 40, 50]
    while True:
        o = rnd.choice(olds)
        p = rnd.choice(pcs)
        nw = Fraction(o * (100 + sign * p), 100)
        if nw.denominator == 1:
            return {"old": o, "new": int(nw)}
''',
}
EXAMPLES += [
    {"id": "fund-pctchg-1", "kind": "percent_change",
     "title": ("Yüzde artış", "Percent increase"),
     "q": ("Bir ürünün fiyatı {oo} TL iken {nn} TL oldu. Fiyat yüzde kaç artmıştır?",
           "A price went from {oo} to {nn}. By what percent did it increase?"),
     "P": {"old": 80, "new": 100}},
    {"id": "fund-pctchg-2", "kind": "percent_change", "topics": ["sale", "indirimli fiyat", "word problem"],
     "title": ("Sözel problem: indirim oranı", "Word problem: the discount rate"),
     "q": ("Etiket fiyatı {oo} TL olan bir mont, indirimde {nn} TL'ye satılıyor. İndirim yüzde kaçtır?",
           "A jacket with a tag price of {oo} is on sale for {nn}. What is the percent discount?"),
     "P": {"old": 250, "new": 200}},
    {"id": "fund-pctchg-3", "kind": "percent_change", "topics": ["profit", "kâr", "word problem"],
     "title": ("Sözel problem: kâr oranı", "Word problem: the markup rate"),
     "q": ("Bir dükkân tanesini {oo} TL'ye aldığı bir oyuncağı {nn} TL'ye satıyor. Fiyata yüzde kaç zam "
           "(kâr) eklenmiştir?",
           "A shop buys a toy for {oo} and sells it for {nn}. What is the percent markup?"),
     "P": {"old": 60, "new": 87}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["exponent_power"] = {
    "course": "fund",
    "title": ("Üslü sayılar: tekrarlı çarpma, sıfır ve negatif üs",
              "Powers: repeated multiplication, zero and negative exponents"),
    "topics": ["exponents", "powers", "exponent rules", "negative exponents", "zero exponent",
               "repeated multiplication", "powers of ten", "üslü sayılar", "üslü ifadeler", "üs",
               "kuvvet", "negatif üs", "sıfırıncı kuvvet"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle

_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸",
        "9": "⁹", "-": "⁻"}


def _sup(k):
    return "".join(_SUP[ch] for ch in str(int(k)))


def _f(v):
    v = Fraction(v)
    s = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    if len(s) > 16:
        s = f"{float(v):.4g}"
    return s.replace("-", "−")


def _dec(v, tr):
    v = Fraction(v)
    for k in range(1, 9):
        if (v * 10 ** k).denominator == 1:
            n = abs(v.numerator) * 10 ** k // v.denominator
            t = str(n).rjust(k + 1, "0")
            s = ("−" if v < 0 else "") + t[:-k] + "." + t[-k:]
            return s.replace(".", ",") if tr else s
    return ""


def _parts(P):
    try:
        b = Fraction(str(P.get("base", 2)))
    except (ValueError, ZeroDivisionError):
        b = Fraction(2)
    n = int(round(float(P.get("n", 1))))
    return b, n


def _B(b):
    s = _f(b)
    return f"({s})" if (b < 0 or b.denominator != 1) else s


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def solve(P):
    b, n = _parts(P)
    B = _B(b)
    pw = f"{B}{_sup(n)}"
    if b == 0 and n < 0:
        msg = (f"{pw} = 1/0{_sup(-n)} = 1/0 → tanımsız", f"{pw} = 1/0{_sup(-n)} = 1/0 → undefined")
        return {"answer": msg, "steps": [("Negatif üs, tabanın tersini almak demektir", "A negative exponent means taking the reciprocal"), msg],
                "fmt": {"pw": pw}}
    if abs(n) > 300:
        msg = ("Üs çok büyük", "The exponent is too large")
        return {"answer": msg, "steps": [(f"{pw}", f"{pw}"), msg], "fmt": {"pw": pw}}
    val = b ** n
    steps = []
    if n > 0:
        if n <= 8:
            prod = " × ".join([B] * n)
        else:
            prod = f"{B} × {B} × … × {B}"
        steps.append((f"{pw} = {prod}  ({n} tane {B} çarpılır)", f"{pw} = {prod}  ({n} factors of {B})"))
        run, cur = [], Fraction(1)
        for k in range(1, min(n, 10) + 1):
            cur = cur * b
            run.append(_f(cur))
        steps.append((("Adım adım: " + " → ".join(run)) + (" → …" if n > 10 else ""),
                      ("Step by step: " + " → ".join(run)) + (" → …" if n > 10 else "")))
        if b < 0:
            steps.append((f"Negatif taban, {'çift' if n % 2 == 0 else 'tek'} kuvvet → sonuç "
                           f"{'pozitif' if n % 2 == 0 else 'negatif'}",
                           f"Negative base with an {'even' if n % 2 == 0 else 'odd'} power → "
                           f"{'positive' if n % 2 == 0 else 'negative'} result"))
    else:
        if b == 0:
            steps.append(("0⁰ = 1 kabul edilir (boş çarpım)", "0⁰ is taken as 1 (the empty product)"))
        else:
            seq = [f"{B}{_sup(k)} = {_f(b ** k)}" for k in (3, 2, 1)]
            steps.append(("Örüntü: " + ", ".join(seq), "Pattern: " + ", ".join(seq)))
            steps.append((f"Üs 1 azaldıkça değer tabana bölünür (÷{B})",
                          f"Each time the exponent drops by 1, divide by the base (÷{B})"))
            steps.append((f"{B}⁰ = {B}¹ ÷ {B} = 1", f"{B}⁰ = {B}¹ ÷ {B} = 1"))
            if n < 0:
                m = -n
                steps.append((f"{pw} = 1 / {B}{_sup(m)} = 1 / {_f(b ** m)} = {_f(val)}",
                              f"{pw} = 1 / {B}{_sup(m)} = 1 / {_f(b ** m)} = {_f(val)}"))
    d_tr, d_en = _dec(val, True), _dec(val, False)
    ans = (f"{pw} = {_f(val)}" + (f" = {d_tr}" if d_tr and val.denominator != 1 else ""),
           f"{pw} = {_f(val)}" + (f" = {d_en}" if d_en and val.denominator != 1 else ""))
    steps.append((f"Sonuç: {ans[0]}", f"Result: {ans[1]}"))
    return {"answer": ans, "steps": steps, "fmt": {"pw": pw}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    b, n = _parts(P)
    B = _B(b)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.1)
    info = ax.text(0.01, 0.985, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"), zorder=10)
    if (b == 0 and n < 0) or abs(n) > 300:
        ax.axis("off")
        ax.text(0.5, 0.5, f"{B}{_sup(n)}: " + ("tanımsız / çok büyük" if tr else "undefined / too large"),
                transform=ax.transAxes, ha="center", fontsize=18, color="#DC2626")

        def upd0(i):
            return []
        return 60, upd0
    if n > 0:
        ks = list(range(1, n + 1))[-12:]
    else:
        ks = list(range(3, n - 1, -1))[-12:]
    vals = [b ** k for k in ks]
    fv = [float(v) for v in vals]
    nb = len(ks)
    vmax = max(abs(v) for v in fv) or 1.0
    neg = any(v < 0 for v in fv)
    ax.set_xlim(-0.7, nb - 0.3)
    if neg:
        ax.set_ylim(-vmax * 1.35, vmax * 1.75)
        ax.axhline(0, color="#374151", lw=1)
    else:
        ax.set_ylim(0, vmax * 1.75)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xticks(range(nb))
    ax.set_xticklabels([f"{B}{_sup(k)}" for k in ks], fontsize=12 if nb <= 8 else 10)
    ax.grid(axis="y", alpha=0.25)
    bars, labs = [], []
    fsl = 11 if nb <= 7 else 9
    for j, v in enumerate(fv):
        k = ks[j]
        colr = "#2563EB" if k > 0 else ("#16A34A" if k == 0 else "#7C3AED")
        rc = Rectangle((j - 0.32, 0), 0.64, 0, fc=colr, ec="#B45309" if v < 0 else colr, lw=2 if v < 0 else 0,
                       alpha=0.85)
        ax.add_patch(rc)
        bars.append(rc)
        labs.append(ax.text(j, v + (vmax * 0.03 if v >= 0 else -vmax * 0.03), _f(vals[j]), ha="center",
                            va="bottom" if v >= 0 else "top", fontsize=fsl, fontweight="bold", alpha=0,
                            color=colr))
    ops = []
    opsym = (f"×{B}" if n > 0 else f"÷{B}")
    for j in range(nb - 1):
        yo = max(fv[j], fv[j + 1], 0) + vmax * 0.16
        ops.append(ax.text(j + 0.5, yo, "→ " + opsym, ha="center", va="center", fontsize=10,
                           color="#E07B39", fontweight="bold", alpha=0))
    hl = Rectangle((nb - 1 - 0.36, min(0, fv[-1])), 0.72, abs(fv[-1]), fill=False, ec="#DC2626", lw=3)
    ax.add_patch(hl)
    head = ax.text(0.5, 0.86, "", transform=ax.transAxes, ha="center", va="center", fontsize=15,
                   fontweight="bold", color="#111827")
    t0, t1 = 12.0, 112.0
    per = (t1 - t0) / nb
    N = 150

    def head_text(j):
        k = ks[j]
        if n > 0:
            m = k
            fac = " × ".join([B] * m) if m <= 6 else f"{B} × {B} × … × {B} ({m} {'kez' if tr else 'times'})"
            return f"{B}{_sup(k)} = {fac} = {_f(vals[j])}"
        if k < 0:
            return f"{B}{_sup(k)} = 1 / {B}{_sup(-k)} = {_f(vals[j])}"
        if k == 0:
            return f"{B}⁰ = {B}¹ ÷ {B} = 1"
        return f"{B}{_sup(k)} = {_f(vals[j])}"

    def update(i):
        shown = -1
        for j in range(nb):
            g = _r(i, t0 + j * per, t0 + (j + 0.8) * per)
            v = fv[j]
            bars[j].set_height(v * g)
            labs[j].set_alpha(1.0 if g >= 1 else 0.0)
            if g > 0:
                shown = j
            if j > 0:
                ops[j - 1].set_alpha(1.0 if g > 0 else 0.0)
        fin = i >= t1
        hl.set_visible(fin)
        if shown >= 0:
            head.set_text(head_text(shown))
        else:
            head.set_text(f"{B}{_sup(n)} = ?")
        head.set_color("#DC2626" if fin else "#111827")
        if i < t0:
            info.set_text("1) Üs, tabanın kendisiyle kaç kez çarpıldığını söyler" if (tr and n > 0) else
                          ("1) The exponent counts how many times the base is multiplied" if n > 0 else
                           ((f"1) Örüntü: üs 1 azaldıkça ÷{B}") if tr else (f"1) Pattern: exponent down by 1 → ÷{B}"))))
        elif not fin:
            if n > 0:
                info.set_text((f"2) Her adımda bir kez daha ×{B}") if tr else (f"2) Each step multiplies by {B} once more"))
            else:
                info.set_text((f"2) Sağa doğru her adımda ÷{B}") if tr else (f"2) Moving right, divide by {B} each step"))
        else:
            sol = solve(P)["answer"]
            info.set_text(("3) Sonuç: " if tr else "3) Result: ") + (sol[0] if tr else sol[1]))
        return []

    return N, update


def vary(P, rnd):
    b0, n0 = _parts(P)
    bases = [-2, -3] if b0 < 0 else [2, 3, 4, 5, 10]
    b = rnd.choice(bases)
    if n0 > 0:
        top = max(2, int(math.floor(math.log(1000) / math.log(abs(b)))))
        n = rnd.randint(2, min(top, 7))
    elif n0 == 0:
        n = 0
    else:
        top = max(1, int(math.floor(math.log(1000) / math.log(abs(b)))))
        n = -rnd.randint(1, min(3, top))
    return {"base": b, "n": n}
''',
}
EXAMPLES += [
    {"id": "fund-pow-1", "kind": "exponent_power",
     "title": ("Tekrarlı çarpma olarak üs", "A power as repeated multiplication"),
     "q": ("{pw} değerini tekrarlı çarpma ile hesapla.", "Evaluate {pw} as repeated multiplication."),
     "P": {"base": 2, "n": 5}},
    {"id": "fund-pow-2", "kind": "exponent_power", "topics": ["growth", "bacteria", "büyüme", "word problem"],
     "title": ("Sözel problem: bakteri çoğalması", "Word problem: growing bacteria"),
     "q": ("Bir kültürde her bakteri bir saat içinde bölünerek {base} bakteri oluyor. Tek bakteriyle "
           "başlanırsa {n} saat sonra kaç bakteri olur? ({pw})",
           "In a culture every bacterium becomes {base} bacteria each hour. Starting from a single "
           "bacterium, how many are there after {n} hours? ({pw})"),
     "P": {"base": 3, "n": 4}},
    {"id": "fund-pow-3", "kind": "exponent_power",
     "title": ("Negatif üs ve sıfırıncı kuvvet", "Negative and zero exponents"),
     "q": ("{pw} kaçtır? Örüntüyü kullanarak sıfırıncı ve negatif kuvvetleri açıkla.",
           "What is {pw}? Use the pattern to explain zero and negative exponents."),
     "P": {"base": 2, "n": -3}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["ratio_proportion"] = {
    "course": "fund",
    "title": ("Oran ve orantı (çift sayı doğrusu)", "Ratios and proportions (double number line)"),
    "topics": ["ratio", "ratios", "proportion", "proportions", "proportional reasoning", "rates",
               "unit rate", "scale drawing", "scale factor", "cross multiplication",
               "oran", "orantı", "oran orantı", "doğru orantı", "birim oran", "ölçek", "içler dışlar"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction


def _fr(v):
    try:
        return Fraction(str(v).strip().replace(",", "."))
    except (ValueError, ZeroDivisionError):
        return Fraction(float(v)).limit_denominator(10 ** 6)


def _n(v, tr=True):
    v = Fraction(v)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        k = None
        for kk in range(1, 7):
            if (v * 10 ** kk).denominator == 1:
                k = kk
                break
        if k is not None:
            n = abs(v.numerator) * 10 ** k // v.denominator
            t = str(n).rjust(k + 1, "0")
            s = ("-" if v < 0 else "") + t[:-k] + "." + t[-k:]
            s = s.replace(".", ",") if tr else s
        else:
            s = f"{v.numerator}/{v.denominator}"
    return s.replace("-", "−")


def _unit(P, key, tr, default):
    u = P.get(key)
    if isinstance(u, (list, tuple)) and len(u) == 2:
        return str(u[0] if tr else u[1])
    if isinstance(u, str) and u:
        return u
    return default


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def solve(P):
    a, b, c = _fr(P.get("a", 1)), _fr(P.get("b", 1)), _fr(P.get("c", 1))
    fmt = {"ratio": f"{_n(a)} : {_n(b)}"}
    if a == 0 or b == 0:
        msg = ("Oranın terimleri 0 olamaz", "The terms of a ratio cannot be 0")
        return {"answer": msg, "steps": [(f"{_n(a)} : {_n(b)} = {_n(c)} : x", f"{_n(a, False)} : {_n(b, False)} = {_n(c, False)} : x"), msg],
                "fmt": fmt}
    k = c / a
    x = b * k
    utr, uen = _unit(P, "ub", True, ""), _unit(P, "ub", False, "")
    steps = [
        (f"Orantı: {_n(a)} : {_n(b)} = {_n(c)} : x   ⇔   {_n(a)}/{_n(b)} = {_n(c)}/x",
         f"Proportion: {_n(a, False)} : {_n(b, False)} = {_n(c, False)} : x   ⇔   {_n(a, False)}/{_n(b, False)} = {_n(c, False)}/x"),
        (f"Ölçek çarpanı: k = {_n(c)} ÷ {_n(a)} = {_n(k)}",
         f"Scale factor: k = {_n(c, False)} ÷ {_n(a, False)} = {_n(k, False)}"),
        (f"Diğer terim de aynı çarpanla büyür: x = {_n(b)} × {_n(k)} = {_n(x)}",
         f"The other term scales the same way: x = {_n(b, False)} × {_n(k, False)} = {_n(x, False)}"),
        (f"İçler dışlar çarpımı: {_n(a)}·x = {_n(b)}·{_n(c)} = {_n(b * c)}  ⇒  x = {_n(b * c)} ÷ {_n(a)} = {_n(x)}",
         f"Cross-multiply: {_n(a, False)}·x = {_n(b, False)}·{_n(c, False)} = {_n(b * c, False)}  ⇒  "
         f"x = {_n(b * c, False)} ÷ {_n(a, False)} = {_n(x, False)}"),
        (f"Kontrol: {_n(a)}/{_n(b)} = {_n(c)}/{_n(x)} = {_n(a / b)}",
         f"Check: {_n(a, False)}/{_n(b, False)} = {_n(c, False)}/{_n(x, False)} = {_n(a / b, False)}"),
    ]
    ans = (f"x = {_n(x)}" + (f" {utr}" if utr else ""), f"x = {_n(x, False)}" + (f" {uen}" if uen else ""))
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, c = _fr(P.get("a", 1)), _fr(P.get("b", 1)), _fr(P.get("c", 1))
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.03)
    ax.axis("off")
    info = ax.text(0.01, 0.985, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"), zorder=10)
    if a <= 0 or b <= 0 or c <= 0:
        ax.text(0.5, 0.5, ("Oran terimleri pozitif olmalı" if tr else "Ratio terms must be positive"),
                transform=ax.transAxes, ha="center", fontsize=16, color="#DC2626")

        def upd0(i):
            return []
        return 60, upd0
    k = c / a
    x = b * k
    kf = float(k)
    ua = _unit(P, "ua", tr, "A")
    ub = _unit(P, "ub", tr, "B")
    tmax = max(1.0, kf) * 1.1
    ax.set_xlim(-0.2 * tmax, tmax * 1.03)
    ax.set_ylim(-2.4, 3.75)
    yT, yB = 1.45, 0.15
    lT, = ax.plot([], [], color="#2563EB", lw=2.6)
    lB, = ax.plot([], [], color="#E07B39", lw=2.6)
    ax.text(-0.025 * tmax, yT, ua, ha="right", va="center", color="#2563EB", fontsize=12, fontweight="bold")
    ax.text(-0.025 * tmax, yB, ub, ha="right", va="center", color="#E07B39", fontsize=12, fontweight="bold")
    kint = k.denominator == 1 and 2 <= k <= 10
    unit_ok = (not kint) and a.denominator == 1 and 2 <= a <= 12 and k.denominator != 1
    marks = [(0.0, "0", "0", 0)]
    marks.append((1.0, _n(a, tr), _n(b, tr), 18))
    if kint:
        km = int(k)
        for m in range(2, km):
            marks.append((float(m), _n(a * m, tr), _n(b * m, tr), 40 + (m - 1) * 50.0 / (km - 1)))
    elif unit_ok:
        marks.append((1.0 / float(a), "1", _n(b / a, tr), 60))
    marks.append((kf, _n(c, tr), "?", 90))
    fsz = 11 if len(marks) <= 7 else 9
    mk_art = []
    for (t, sT, sB, t_on) in marks:
        tickT, = ax.plot([t, t], [yT - 0.12, yT + 0.12], color="#2563EB", lw=1.8)
        tickB, = ax.plot([t, t], [yB - 0.12, yB + 0.12], color="#E07B39", lw=1.8)
        txT = ax.text(t, yT + 0.18, sT, ha="center", va="bottom", fontsize=fsz, color="#1E3A8A", fontweight="bold")
        txB = ax.text(t, yB - 0.18, sB, ha="center", va="top", fontsize=fsz, color="#9A3412", fontweight="bold")
        mk_art.append((t_on, tickT, tickB, txT, txB))
    con1, = ax.plot([1, 1], [yB + 0.12, yT - 0.12], ls=":", color="#6B7280", lw=1.5)
    conk, = ax.plot([kf, kf], [yB + 0.12, yT - 0.12], ls=":", color="#DC2626", lw=1.8)
    tt = np.linspace(0, 1, 50)

    def arc(t0, t1, ybase, up, h):
        xs = t0 + (t1 - t0) * tt
        ys = ybase + (1 if up else -1) * h * np.sin(np.pi * tt)
        return xs, ys

    arcs = []
    if kint:
        km = int(k)
        for m in range(1, km):
            ta = 40 + (m - 1) * 50.0 / (km - 1)
            arcs.append((arc(m, m + 1, yT + 0.55, True, 0.35), ta, f"+{_n(a, tr)}", "#2563EB", True))
            arcs.append((arc(m, m + 1, yB - 0.55, False, 0.35), ta, f"+{_n(b, tr)}", "#E07B39", False))
    elif unit_ok:
        arcs.append((arc(1, 1.0 / float(a), yT - 0.14, False, 0.3), 40, f"÷{_n(a, tr)}", "#2563EB", False))
        arcs.append((arc(1, 1.0 / float(a), yB + 0.14, True, 0.3), 40, f"÷{_n(a, tr)}", "#E07B39", True))
        arcs.append((arc(1.0 / float(a), kf, yT + 0.55, True, 0.6), 65, f"×{_n(c, tr)}", "#2563EB", True))
        arcs.append((arc(1.0 / float(a), kf, yB - 0.55, False, 0.6), 65, f"×{_n(c, tr)}", "#E07B39", False))
    else:
        arcs.append((arc(1, kf, yT + 0.55, True, 0.5), 50, f"×{_n(k, tr)}", "#2563EB", True))
        arcs.append((arc(1, kf, yB - 0.55, False, 0.5), 50, f"×{_n(k, tr)}", "#E07B39", False))
    arc_art = []
    for (xs, ys), ta, lab, colr, up in arcs:
        ln, = ax.plot([], [], color=colr, lw=2)
        tx = ax.text(xs[len(xs) // 2], ys[len(ys) // 2] + (0.06 if up else -0.06), lab, ha="center",
                     va="bottom" if up else "top", fontsize=11, color=colr, fontweight="bold")
        arc_art.append((xs, ys, ta, ln, tx))
    if unit_ok:
        arc_art[0][4].set_position(((1.0 + 1.0 / float(a)) / 2.0, (yT + yB) / 2.0))
        arc_art[0][4].set_va("center")
        arc_art[0][4].set_color("#374151")
        arc_art[1][4].set_text("")
    xlab = ax.text(kf, yB - 0.18, _n(x, tr), ha="center", va="top", fontsize=fsz + 2, color="#DC2626",
                   fontweight="bold")
    cross = ax.text(0.5, 0.06, "", transform=ax.transAxes, ha="center", va="bottom", fontsize=13,
                    bbox=dict(boxstyle="round", fc="#F0FDF4", ec="#16A34A"))
    cross.set_text((f"İçler dışlar: {_n(a)}·x = {_n(b)}·{_n(c)}  ⇒  x = {_n(b * c)} ÷ {_n(a)} = {_n(x)}") if tr else
                   (f"Cross-multiply: {_n(a, False)}·x = {_n(b, False)}·{_n(c, False)}  ⇒  "
                    f"x = {_n(b * c, False)} ÷ {_n(a, False)} = {_n(x, False)}"))
    N = 150

    def update(i):
        g = _r(i, 0, 16)
        lT.set_data([0, tmax * g], [yT, yT])
        lB.set_data([0, tmax * g], [yB, yB])
        for (t_on, tickT, tickB, txT, txB) in mk_art:
            on = i >= t_on
            for art in (tickT, tickB, txT, txB):
                art.set_visible(on)
        con1.set_visible(i >= 18)
        for xs, ys, ta, ln, tx in arc_art:
            d = 12.0 if kint else 22.0
            f = _r(i, ta, ta + d)
            if f > 0:
                m = max(2, int(f * len(xs)))
                ln.set_data(xs[:m], ys[:m])
            else:
                ln.set_data([], [])
            tx.set_visible(f >= 1)
        fin = i >= 100
        mk_art[-1][4].set_visible(i >= 90 and not fin)
        xlab.set_visible(fin)
        conk.set_visible(fin)
        cross.set_visible(i >= 115)
        cross.get_bbox_patch().set_visible(i >= 115)
        if i < 18:
            info.set_text("1) Çift sayı doğrusu: üstte ve altta aynı oranda büyüyen iki nicelik" if tr else
                          "1) Double number line: two quantities that grow at the same rate")
        elif i < 40:
            info.set_text((f"2) Verilen oran: {_n(a)} {ua} ↔ {_n(b)} {ub}") if tr else
                          (f"2) Given ratio: {_n(a, False)} {ua} ↔ {_n(b, False)} {ub}"))
        elif i < 100:
            if kint:
                info.set_text((f"3) Aynı adımları tekrarla: {_n(c)} = {int(k)} × {_n(a)}") if tr else
                              (f"3) Repeat the same steps: {_n(c, False)} = {int(k)} × {_n(a, False)}"))
            elif unit_ok:
                info.set_text((f"3) Önce birim orana in (÷{_n(a)}), sonra ×{_n(c)}") if tr else
                              (f"3) Go to the unit rate (÷{_n(a, False)}), then ×{_n(c, False)}"))
            else:
                info.set_text((f"3) Ölçek çarpanı k = {_n(c)} ÷ {_n(a)} = {_n(k)}") if tr else
                              (f"3) Scale factor k = {_n(c, False)} ÷ {_n(a, False)} = {_n(k, False)}"))
        else:
            ubi = _unit(P, "ub", tr, "")
            info.set_text((f"4) x = {_n(b)} × {_n(k)} = {_n(x)} {ubi}") if tr else
                          (f"4) x = {_n(b, False)} × {_n(k, False)} = {_n(x, False)} {ubi}"))
        return []

    return N, update


def vary(P, rnd):
    while True:
        p = rnd.choice([1, 1, 2, 3])
        q = rnd.randint(2, 9)
        if q == p or math.gcd(p, q) != 1:
            continue
        s, t = rnd.randint(1, 5), rnd.randint(2, 8)
        if s == t:
            continue
        out = {"a": p * s, "b": p * t, "c": q * s}
        for key in ("ua", "ub"):
            if key in P:
                out[key] = P[key]
        if out["a"] != out["c"]:
            return out
''',
}
EXAMPLES += [
    {"id": "fund-ratio-1", "kind": "ratio_proportion",
     "title": ("Orantıda bilinmeyen terim", "Missing term in a proportion"),
     "q": ("{a} : {b} = {c} : x orantısında x kaçtır?", "In the proportion {a} : {b} = {c} : x, find x."),
     "P": {"a": 3, "b": 5, "c": 12}},
    {"id": "fund-ratio-2", "kind": "ratio_proportion", "topics": ["recipe", "tarif", "word problem"],
     "title": ("Sözel problem: kurabiye tarifi", "Word problem: a cookie recipe"),
     "q": ("{a} bardak unla {b} kurabiye yapılıyor. Aynı tarifle {c} bardak undan kaç kurabiye çıkar?",
           "{a} cups of flour make {b} cookies. How many cookies can {c} cups make with the same recipe?"),
     "P": {"a": 2, "b": 15, "c": 6, "ua": ["bardak un", "cups of flour"], "ub": ["kurabiye", "cookies"]}},
    {"id": "fund-ratio-3", "kind": "ratio_proportion", "topics": ["map scale", "harita ölçeği", "scale model"],
     "title": ("Sözel problem: harita ölçeği", "Word problem: a map scale"),
     "q": ("Bir haritada {a} cm, gerçekte {b} km'ye karşılık geliyor. Haritada {c} cm olan yol gerçekte "
           "kaç km'dir?",
           "On a map, {a} cm stands for {b} km. How long is a road that measures {c} cm on the map?"),
     "P": {"a": 4, "b": 50, "c": 10, "ua": ["cm (harita)", "cm (map)"], "ub": ["km (gerçek)", "km (real)"]}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["gcd_lcm"] = {
    "course": "fund",
    "title": ("EBOB ve EKOK (Öklid algoritması ve katlar)", "GCD and LCM (Euclid's algorithm and multiples)"),
    "topics": ["gcd", "gcf", "greatest common factor", "greatest common divisor", "lcm",
               "least common multiple", "euclidean algorithm", "factors and multiples", "common factors",
               "ebob", "ekok", "obeb", "okek", "en büyük ortak bölen", "en küçük ortak kat",
               "bölünebilme", "ortak bölen", "ortak kat"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Rectangle


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def _parts(P):
    a = abs(int(round(float(P.get("a", 0)))))
    b = abs(int(round(float(P.get("b", 0)))))
    return a, b


def _euclid(a, b):
    big, small = max(a, b), min(a, b)
    out = []
    while small > 0 and len(out) < 60:
        q, r = divmod(big, small)
        out.append((big, q, small, r))
        big, small = small, r
    return out


def solve(P):
    a, b = _parts(P)
    if a == 0 and b == 0:
        msg = ("EBOB(0, 0) tanımsızdır", "gcd(0, 0) is undefined")
        return {"answer": msg, "steps": [("İki sayı da 0", "Both numbers are 0"), msg], "fmt": {}}
    if a == 0 or b == 0:
        g = max(a, b)
        return {"answer": (f"EBOB = {g}, EKOK = 0", f"GCD = {g}, LCM = 0"),
                "steps": [(f"0 her sayıya bölünür → EBOB = {g}", f"0 is divisible by everything → gcd = {g}"),
                          ("0'ın katı yalnız 0'dır → EKOK = 0", "The only multiple of 0 is 0 → lcm = 0")],
                "fmt": {}}
    g = math.gcd(a, b)
    l = a * b // g
    steps = [("Öklid algoritması: büyük sayıyı küçüğe böl, sonra bölen ile kalanla devam et",
              "Euclid's algorithm: divide the larger by the smaller, then repeat with the divisor and remainder")]
    for big, q, small, r in _euclid(a, b):
        steps.append((f"{big} = {q}·{small} + {r}", f"{big} = {q}·{small} + {r}"))
    steps.append((f"Kalan 0 oldu → son bölen EBOB({a}, {b}) = {g}",
                  f"The remainder is 0 → the last divisor is gcd({a}, {b}) = {g}"))
    ma = ", ".join(str(a * k) for k in range(1, min(l // a, 8) + 1)) + (", …" if l // a > 8 else "")
    mb = ", ".join(str(b * k) for k in range(1, min(l // b, 8) + 1)) + (", …" if l // b > 8 else "")
    steps.append((f"Katlar: {a} → {ma};  {b} → {mb};  ilk ortak kat {l}",
                   f"Multiples: {a} → {ma};  {b} → {mb};  first common one is {l}"))
    steps.append((f"EKOK = a·b ÷ EBOB = {a}·{b} ÷ {g} = {l}", f"lcm = a·b ÷ gcd = {a}·{b} ÷ {g} = {l}"))
    steps.append((f"Kontrol: EBOB × EKOK = {g} × {l} = {g * l} = {a} × {b} ✓",
                  f"Check: gcd × lcm = {g} × {l} = {g * l} = {a} × {b} ✓"))
    return {"answer": (f"EBOB = {g}, EKOK = {l}", f"GCD = {g}, LCM = {l}"), "steps": steps,
            "fmt": {"g": g, "l": l}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b = _parts(P)
    gs = fig.add_gridspec(2, 2, height_ratios=[0.15, 1], width_ratios=[1, 1.15], left=0.02, right=0.98,
                          top=0.97, bottom=0.03, hspace=0.06, wspace=0.06)
    axh = fig.add_subplot(gs[0, :])
    axh.axis("off")
    info = axh.text(0.0, 0.5, "", transform=axh.transAxes, va="center", fontsize=12,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    axl = fig.add_subplot(gs[1, 0])
    axr = fig.add_subplot(gs[1, 1])
    axl.axis("off")
    axr.axis("off")
    if a == 0 or b == 0:
        info.set_text("EBOB/EKOK için iki pozitif tam sayı gerekir" if tr else "GCD/LCM needs two positive integers")

        def upd0(i):
            return []
        return 60, upd0
    g = math.gcd(a, b)
    l = a * b // g
    W, H = max(a, b), min(a, b)
    fw, fh = fig.get_size_inches()
    pos = axl.get_position()
    wl, hl = pos.width * fw, pos.height * fh
    s = min(0.9 * wl / W, 0.5 * hl / H)
    XW, YH = wl / s, hl / s
    axl.set_xlim(0, XW)
    axl.set_ylim(0, YH)
    x0 = (XW - W) / 2.0
    y0 = 0.97 * YH - H
    axl.add_patch(Rectangle((x0, y0), W, H, fill=False, ec="#374151", lw=2, zorder=5))
    axl.text(x0 + W / 2.0, y0 - 0.015 * YH, str(W), ha="center", va="top", fontsize=11, color="#374151")
    axl.text(x0 - 0.015 * XW, y0 + H / 2.0, str(H), ha="right", va="center", fontsize=11, color="#374151")
    colors = ["#2563EB", "#E07B39", "#16A34A", "#7C3AED", "#DC2626", "#0891B2", "#6B7280"]
    strips = []
    x, y, w, h = x0, y0, W, H
    j = 0
    while w > 0 and h > 0 and j < 30:
        if w >= h:
            q, sd = w // h, h
            geo = (x, y, q * sd, sd, True)
            x, w = x + q * sd, w - q * sd
        else:
            q, sd = h // w, w
            geo = (x, y, sd, q * sd, False)
            y, h = y + q * sd, h - q * sd
        rect = Rectangle((geo[0], geo[1]), 0, 0, fc=colors[j % len(colors)], alpha=0.55,
                         ec=colors[j % len(colors)], lw=1.5, zorder=2)
        axl.add_patch(rect)
        dl, = axl.plot([], [], color="white", lw=1.6, zorder=3)
        lab = axl.text(geo[0] + sd / 2.0, geo[1] + sd / 2.0, str(sd), ha="center", va="center",
                       fontsize=10, color="white", fontweight="bold", zorder=4)
        lab.set_visible(False)
        strips.append((geo, q, sd, rect, dl, lab, sd * s >= 0.28))
        j += 1
    J = len(strips)
    eu = _euclid(a, b)
    fse = max(7.0, min(12.0, 0.36 * hl * 72 / max(1, len(eu) + 1) / 1.5))
    eq_txt = []
    for k, (bg, q, sm, r) in enumerate(eu):
        col = colors[k % len(colors)]
        eq_txt.append(axl.text(0.5, 0.34 - k * (0.32 / max(1, len(eu))), f"{bg} = {q}·{sm} + {r}",
                               transform=axl.transAxes, ha="center", va="top", fontsize=fse, color=col,
                               fontweight="bold", family="DejaVu Sans Mono"))
    last = strips[-1]
    glow = Rectangle((last[0][0], last[0][1]), last[0][2], last[0][3], fill=False, ec="#DC2626", lw=3.5,
                     zorder=6)
    axl.add_patch(glow)
    ext = l * 1.04
    axr.set_xlim(-0.17 * l, l * 1.24)
    axr.set_ylim(-1.3, 2.4)
    ya, yb = 1.15, 0.0
    axr.plot([0, ext], [ya, ya], color="#9CA3AF", lw=1.2)
    axr.plot([0, ext], [yb, yb], color="#9CA3AF", lw=1.2)
    axr.text(-0.03 * ext, ya, str(a), ha="right", va="center", fontsize=13, fontweight="bold", color="#2563EB")
    axr.text(-0.03 * ext, yb, str(b), ha="right", va="center", fontsize=13, fontweight="bold", color="#E07B39")
    axr.text(0.5, 0.985, ("Katlar" if tr else "Multiples"), transform=axr.transAxes, ha="center", va="top",
             fontsize=12, color="#374151", fontweight="bold")
    ma = [a * k for k in range(1, min(l // a, 80) + 1)]
    mb = [b * k for k in range(1, min(l // b, 80) + 1)]
    msz = 9 if max(len(ma), len(mb)) <= 20 else 5
    da, = axr.plot([], [], "o", ms=msz, color="#2563EB", zorder=4)
    db, = axr.plot([], [], "o", ms=msz, color="#E07B39", zorder=4)
    labs = []
    for vals, yy, col, off in ((ma, ya, "#1E3A8A", 0.2), (mb, yb, "#9A3412", -0.2)):
        step = 1 if len(vals) <= 10 else int(math.ceil(len(vals) / 8.0))
        for k, v in enumerate(vals):
            if k % step == 0 or v == l:
                t = axr.text(v, yy + off, str(v), ha="center", va="bottom" if off > 0 else "top", fontsize=9,
                             color=col)
                labs.append((v, t))
    lcm_line, = axr.plot([l, l], [yb - 0.55, ya + 0.6], ls="--", color="#16A34A", lw=2.2)
    lcm_lab = axr.text(l, ya + 0.65, ("EKOK = " if tr else "LCM = ") + str(l), ha="center", va="bottom",
                       fontsize=13, color="#16A34A", fontweight="bold")
    T0, T1 = 10.0, 80.0
    per = (T1 - T0) / J
    M0, M1 = 95.0, 145.0
    N = 170

    def update(i):
        for k, (geo, q, sd, rect, dl, lab, big) in enumerate(strips):
            f = _r(i, T0 + k * per, T0 + (k + 0.85) * per)
            m = int(math.ceil(f * q)) if f > 0 else 0
            gx, gy, gw, gh, horiz = geo
            if horiz:
                rect.set_width(m * sd)
                rect.set_height(sd if m else 0)
                xs, ys = [], []
                for t in range(1, m):
                    xs += [gx + t * sd, gx + t * sd, np.nan]
                    ys += [gy, gy + sd, np.nan]
            else:
                rect.set_width(sd if m else 0)
                rect.set_height(m * sd)
                xs, ys = [], []
                for t in range(1, m):
                    xs += [gx, gx + sd, np.nan]
                    ys += [gy + t * sd, gy + t * sd, np.nan]
            if m > 1 and q <= 200:
                dl.set_data(xs, ys)
            else:
                dl.set_data([], [])
            lab.set_visible(big and m > 0)
            if k < len(eq_txt):
                eq_txt[k].set_alpha(_r(i, T0 + (k + 0.5) * per, T0 + (k + 0.85) * per))
        glow.set_visible(i >= 82)
        ma_v = [v for v in ma if i >= M0 + (M1 - M0) * v / float(l)]
        mb_v = [v for v in mb if i >= M0 + (M1 - M0) * v / float(l)]
        da.set_data(ma_v, [ya] * len(ma_v))
        db.set_data(mb_v, [yb] * len(mb_v))
        for v, t in labs:
            t.set_visible(i >= M0 + (M1 - M0) * v / float(l))
        lcm_line.set_visible(i >= M1)
        lcm_lab.set_visible(i >= M1)
        if i < T0:
            info.set_text((f"1) {W} × {H} dikdörtgeni: içine sığan en büyük kareleri yerleştir") if tr else
                          (f"1) A {W} × {H} rectangle: fill it with the largest squares that fit"))
        elif i < 82:
            info.set_text("2) Her adım bir bölme: büyük = bölüm × küçük + kalan" if tr else
                          "2) Each step is a division: larger = quotient × smaller + remainder")
        elif i < M0:
            info.set_text((f"3) En küçük kare {g} × {g} her şeyi tam kaplar → EBOB = {g}") if tr else
                          (f"3) The last {g} × {g} squares tile everything → GCD = {g}"))
        elif i < M1:
            info.set_text("4) İki sayının katlarını yan yana say; ilk ortak kat EKOK'tur" if tr else
                          "4) Count up multiples of both numbers; the first common one is the LCM")
        else:
            info.set_text((f"5) EBOB({a}, {b}) = {g},  EKOK = {l},  {g}·{l} = {a}·{b}") if tr else
                          (f"5) GCD({a}, {b}) = {g},  LCM = {l},  {g}·{l} = {a}·{b}"))
        return []

    return N, update


def vary(P, rnd):
    while True:
        g = rnd.choice([2, 3, 4, 5, 6])
        m, n = rnd.randint(2, 9), rnd.randint(2, 9)
        if m != n and math.gcd(m, n) == 1 and g * m * n <= 200:
            return {"a": g * m, "b": g * n}
''',
}
EXAMPLES += [
    {"id": "fund-gcd-1", "kind": "gcd_lcm",
     "title": ("İki sayının EBOB ve EKOK'u", "GCD and LCM of two numbers"),
     "q": ("{a} ve {b} sayılarının EBOB ve EKOK'unu bul.", "Find the GCD and the LCM of {a} and {b}."),
     "P": {"a": 18, "b": 24}},
    {"id": "fund-gcd-2", "kind": "gcd_lcm", "topics": ["word problem", "sözel problem", "schedules"],
     "title": ("Sözel problem: otobüs seferleri", "Word problem: bus timetables"),
     "q": ("İki otobüs aynı duraktan her {a} dakikada ve her {b} dakikada bir kalkıyor. Birlikte kalktıktan "
           "kaç dakika sonra yine birlikte kalkarlar?",
           "Two buses leave the same stop every {a} minutes and every {b} minutes. After leaving together, "
           "how many minutes until they leave together again?"),
     "P": {"a": 12, "b": 20}},
    {"id": "fund-gcd-3", "kind": "gcd_lcm", "topics": ["tiles", "fayans", "word problem"],
     "title": ("Sözel problem: kare fayanslar", "Word problem: square tiles"),
     "q": ("{a} dm × {b} dm boyutlarındaki bir zemin, kesilmeden en büyük eş kare fayanslarla döşenecek. "
           "Bir fayansın kenarı kaç dm olmalıdır?",
           "A floor of {a} dm × {b} dm is to be covered with the largest equal square tiles without "
           "cutting. What is the side of one tile?"),
     "P": {"a": 48, "b": 36}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["area_perimeter"] = {
    "course": "fund",
    "title": ("Dikdörtgende alan ve çevre", "Area and perimeter of a rectangle"),
    "topics": ["area", "perimeter", "area and perimeter", "rectangle", "square units", "measurement",
               "unit squares", "alan", "çevre", "alan ve çevre", "dikdörtgen", "birim kare",
               "dikdörtgenin alanı", "ölçme"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle


def _fr(v):
    try:
        return Fraction(str(v).strip().replace(",", "."))
    except (ValueError, ZeroDivisionError):
        return Fraction(float(v)).limit_denominator(10 ** 6)


def _n(v, tr=True):
    v = Fraction(v)
    if v.denominator == 1:
        s = str(v.numerator)
    else:
        s = f"{float(v):.4f}".rstrip("0").rstrip(".")
        s = s.replace(".", ",") if tr else s
    return s.replace("-", "−")


def _units(P, tr):
    u = str(P.get("unit", "") or "")
    if u:
        return u + "²", u
    return ("br²", "br") if tr else ("sq units", "units")


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def solve(P):
    w, h = _fr(P.get("w", 1)), _fr(P.get("h", 1))
    if w <= 0 or h <= 0:
        msg = ("Kenar uzunlukları pozitif olmalı", "Side lengths must be positive")
        return {"answer": msg, "steps": [(f"{_n(w)} × {_n(h)}", f"{_n(w, False)} × {_n(h, False)}"), msg], "fmt": {}}
    A, Pm = w * h, 2 * (w + h)
    ua_t, ul_t = _units(P, True)
    ua_e, ul_e = _units(P, False)
    steps = [(f"Alan = uzunluk × genişlik = {_n(w)} × {_n(h)} = {_n(A)} {ua_t}",
              f"Area = length × width = {_n(w, False)} × {_n(h, False)} = {_n(A, False)} {ua_e}")]
    if w.denominator == 1 and h.denominator == 1:
        steps.append((f"Birim karelerle: her sırada {_n(w)} kare, {_n(h)} sıra → {_n(A)} kare",
                      f"With unit squares: {_n(w, False)} squares in each row, {_n(h, False)} rows → {_n(A, False)} squares"))
    steps.append((f"Çevre = 2 × (uzunluk + genişlik) = 2 × ({_n(w)} + {_n(h)}) = 2 × {_n(w + h)} = {_n(Pm)} {ul_t}",
                  f"Perimeter = 2 × (length + width) = 2 × ({_n(w, False)} + {_n(h, False)}) = 2 × {_n(w + h, False)} = {_n(Pm, False)} {ul_e}"))
    steps.append((f"Kenarları tek tek topla: {_n(w)} + {_n(h)} + {_n(w)} + {_n(h)} = {_n(Pm)} {ul_t}",
                  f"Or add the four sides: {_n(w, False)} + {_n(h, False)} + {_n(w, False)} + {_n(h, False)} = {_n(Pm, False)} {ul_e}"))
    return {"answer": (f"Alan = {_n(A)} {ua_t}, Çevre = {_n(Pm)} {ul_t}",
                       f"Area = {_n(A, False)} {ua_e}, Perimeter = {_n(Pm, False)} {ul_e}"),
            "steps": steps, "fmt": {"ww": (_n(w), _n(w, False)), "hh": (_n(h), _n(h, False))}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    w, h = _fr(P.get("w", 1)), _fr(P.get("h", 1))
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    ax.axis("off")
    info = ax.text(0.01, 0.985, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"), zorder=10)
    if w <= 0 or h <= 0:
        ax.text(0.5, 0.5, "Kenarlar pozitif olmalı" if tr else "Sides must be positive", transform=ax.transAxes,
                ha="center", fontsize=16, color="#DC2626")

        def upd0(i):
            return []
        return 60, upd0
    wf, hf = float(w), float(h)
    A, Pm = w * h, 2 * (w + h)
    ua, ul = _units(P, tr)
    fw, fh = fig.get_size_inches()
    pos = ax.get_position()
    aw, ah = pos.width * fw, pos.height * fh
    s = min(0.56 * aw / wf, 0.66 * ah / hf)
    XW, YH = aw / s, ah / s
    nx, ny = int(math.ceil(wf - 1e-9)), int(math.ceil(hf - 1e-9))
    x0 = 0.06 * XW + (0.56 * XW - wf) / 2.0
    y0 = 0.1 * YH + (0.66 * YH - hf) / 2.0
    im = ax.imshow(np.ones((ny, nx, 4)), extent=(x0, x0 + nx, y0, y0 + ny), origin="lower",
                   interpolation="nearest", aspect="auto", zorder=1)
    clip = Rectangle((x0, y0), wf, hf, transform=ax.transData, fill=False, ec="none")
    ax.add_patch(clip)
    im.set_clip_path(clip)
    ax.set_xlim(0, XW)
    ax.set_ylim(0, YH)
    if nx <= 60 and ny <= 60:
        gx, gy = [], []
        for k in range(1, nx):
            if k < wf:
                gx += [x0 + k, x0 + k, np.nan]
                gy += [y0, y0 + hf, np.nan]
        for k in range(1, ny):
            if k < hf:
                gx += [x0, x0 + wf, np.nan]
                gy += [y0 + k, y0 + k, np.nan]
        ax.plot(gx, gy, color="#9CA3AF", lw=0.8, zorder=2)
    ax.add_patch(Rectangle((x0, y0), wf, hf, fill=False, ec="#374151", lw=1.6, ls="--", zorder=3))
    off = 0.045 * max(XW, YH) * 0.5
    lab_b = ax.text(x0 + wf / 2, y0 - off, _n(w, tr), ha="center", va="top", fontsize=13, color="#374151")
    lab_r = ax.text(x0 + wf + off, y0 + hf / 2, _n(h, tr), ha="left", va="center", fontsize=13, color="#374151")
    lab_t = ax.text(x0 + wf / 2, y0 + hf + off, _n(w, tr), ha="center", va="bottom", fontsize=13, color="#374151")
    lab_l = ax.text(x0 - off, y0 + hf / 2, _n(h, tr), ha="right", va="center", fontsize=13, color="#374151")
    side_labs = [lab_b, lab_r, lab_t, lab_l]
    trace, = ax.plot([], [], color="#E07B39", lw=5, solid_capstyle="round", zorder=6)
    dot, = ax.plot([], [], "o", ms=11, color="#DC2626", zorder=7)
    cnt = ax.text(x0 + wf / 2, y0 + hf / 2, "", ha="center", va="center", fontsize=22, fontweight="bold",
                  color="#1E3A8A", zorder=8, bbox=dict(boxstyle="round", fc="white", ec="none", alpha=0.8))
    fx = 0.66
    f1 = ax.text(fx, 0.62, (f"Alan = {_n(w)} × {_n(h)}\n= {_n(A)} {ua}" if tr else
                            f"Area = {_n(w, False)} × {_n(h, False)}\n= {_n(A, False)} {ua}"),
                 transform=ax.transAxes, fontsize=14, color="#2563EB", va="top", fontweight="bold")
    f2 = ax.text(fx, 0.40, "", transform=ax.transAxes, fontsize=13, color="#E07B39", va="top", fontweight="bold")
    f3 = ax.text(fx, 0.22, (f"Çevre = 2 × ({_n(w)} + {_n(h)})\n= {_n(Pm)} {ul}" if tr else
                            f"Perimeter = 2 × ({_n(w, False)} + {_n(h, False)})\n= {_n(Pm, False)} {ul}"),
                 transform=ax.transAxes, fontsize=14, color="#E07B39", va="top", fontweight="bold")
    total = nx * ny
    order = np.arange(total).reshape(ny, nx)
    empty = np.array([1.0, 1.0, 1.0, 1.0])
    fillc = np.array([0.145, 0.388, 0.922, 0.55])
    corners = [(x0, y0), (x0 + wf, y0), (x0 + wf, y0 + hf), (x0, y0 + hf), (x0, y0)]
    sides = [wf, hf, wf, hf]
    Pf = float(Pm)
    sidestr = [_n(w, tr), _n(h, tr), _n(w, tr), _n(h, tr)]
    N = 170

    def point_at(dist):
        pts = [corners[0]]
        acc = 0.0
        for k in range(4):
            if dist >= acc + sides[k]:
                pts.append(corners[k + 1])
                acc += sides[k]
            else:
                t = (dist - acc) / sides[k]
                (ax_, ay_), (bx_, by_) = corners[k], corners[k + 1]
                pts.append((ax_ + (bx_ - ax_) * t, ay_ + (by_ - ay_) * t))
                return pts, k
        return pts, 4

    def update(i):
        c = int(round(total * _r(i, 12, 82)))
        im.set_data(np.where((order < c)[:, :, None], fillc, empty))
        if 12 <= i < 92:
            if w.denominator == 1 and h.denominator == 1:
                cnt.set_text(f"{c}")
            else:
                cnt.set_text("≈" + _n(Fraction(c * float(A) / max(1, total)).limit_denominator(100), tr))
        else:
            cnt.set_text("")
        cnt.get_bbox_patch().set_visible(12 <= i < 92)
        f1.set_alpha(_r(i, 82, 88))
        f3.set_alpha(_r(i, 152, 158))
        d = Pf * _r(i, 92, 150)
        if i >= 92:
            pts, k = point_at(d)
            trace.set_data([p[0] for p in pts], [p[1] for p in pts])
            dot.set_data([pts[-1][0]], [pts[-1][1]])
            done = min(4, k)
            f2.set_text(" + ".join(sidestr[:done]) + (f" = {_n(Pm, tr)}" if done == 4 else ""))
        else:
            trace.set_data([], [])
            dot.set_data([], [])
            done = 0
            f2.set_text("")
        for k, lb in enumerate(side_labs):
            on = i >= 92 and done > k
            lb.set_color("#E07B39" if on else "#374151")
            lb.set_fontweight("bold" if on else "normal")
        if i < 12:
            info.set_text((f"1) {_n(w)} × {_n(h)} dikdörtgeni, 1 × 1 birim karelerle") if tr else
                          (f"1) A {_n(w, False)} × {_n(h, False)} rectangle on a grid of unit squares"))
        elif i < 82:
            info.set_text("2) Alan: içini dolduran birim kareleri say" if tr else
                          "2) Area: count the unit squares that fill it")
        elif i < 92:
            info.set_text((f"3) Alan = {_n(w)} × {_n(h)} = {_n(A)} {ua}") if tr else
                          (f"3) Area = {_n(w, False)} × {_n(h, False)} = {_n(A, False)} {ua}"))
        elif i < 152:
            info.set_text("4) Çevre: kenarların üzerinden bir tur yürü" if tr else
                          "4) Perimeter: walk once around the edge")
        else:
            info.set_text((f"5) Alan = {_n(A)} {ua},  Çevre = {_n(Pm)} {ul}") if tr else
                          (f"5) Area = {_n(A, False)} {ua},  Perimeter = {_n(Pm, False)} {ul}"))
        return []

    return N, update


def vary(P, rnd):
    while True:
        w, h = rnd.randint(3, 12), rnd.randint(2, 9)
        if w != h:
            out = {"w": w, "h": h}
            if P.get("unit"):
                out["unit"] = P["unit"]
            return out
''',
}
EXAMPLES += [
    {"id": "fund-area-1", "kind": "area_perimeter",
     "title": ("Dikdörtgenin alanı ve çevresi", "Area and perimeter of a rectangle"),
     "q": ("Kenarları {ww} ve {hh} birim olan dikdörtgenin alanını ve çevresini bul.",
           "Find the area and the perimeter of a rectangle with sides {ww} and {hh} units."),
     "P": {"w": 6, "h": 4}},
    {"id": "fund-area-2", "kind": "area_perimeter", "topics": ["garden", "fence", "bahçe", "çit", "word problem"],
     "title": ("Sözel problem: bahçe ve çit", "Word problem: a garden and its fence"),
     "q": ("{ww} m × {hh} m boyutlarındaki bahçeye çim ekilecek ve etrafı çitle çevrilecek. Kaç m² çim ve "
           "kaç m çit gerekir?",
           "A {ww} m × {hh} m garden will be covered with grass and fenced all around. How many m² of grass "
           "and how many metres of fence are needed?"),
     "P": {"w": 9, "h": 5, "unit": "m"}},
    {"id": "fund-area-3", "kind": "area_perimeter", "topics": ["carpet", "halı", "word problem"],
     "title": ("Sözel problem: halı ve kenar şeridi", "Word problem: a rug and its border"),
     "q": ("{ww} m × {hh} m bir halı için kaç m² kumaş gerekir? Kenarlarına dikilecek şerit kaç m olur?",
           "How many m² of fabric does a {ww} m × {hh} m rug need, and how long is the trim sewn around it?"),
     "P": {"w": 7, "h": 3, "unit": "m"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["prime_factor_tree"] = {
    "course": "fund",
    "title": ("Çarpan ağacı ile asal çarpanlara ayırma", "Prime factorisation with a factor tree"),
    "topics": ["prime factorization", "prime factorisation", "prime factors", "factor tree",
               "prime numbers", "primes", "composite numbers", "factors", "asal çarpanlar",
               "asal sayılar", "çarpan ağacı", "asal çarpanlara ayırma", "çarpanlar ve katlar",
               "bölenler"],
    "code": r'''
import math
import numpy as np

_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}


def _sup(k):
    return "".join(_SUP[ch] for ch in str(k))


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def _isprime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def _split(n):
    d = int(math.isqrt(n))
    while d >= 2:
        if n % d == 0:
            return d, n // d
        d -= 1
    return None


def _tree(n):
    nodes = [{"v": n, "d": 0, "kids": [], "par": -1}]
    stack = [0]
    while stack:
        k = stack.pop()
        v = nodes[k]["v"]
        sp = _split(v)
        if sp is None:
            continue
        for c in sp:
            nodes.append({"v": c, "d": nodes[k]["d"] + 1, "kids": [], "par": k})
            nodes[k]["kids"].append(len(nodes) - 1)
        stack.extend(reversed(nodes[k]["kids"]))
    return nodes


def _layout(nodes):
    cnt = [0]

    def place(k):
        kids = nodes[k]["kids"]
        if not kids:
            nodes[k]["x"] = float(cnt[0])
            cnt[0] += 1
        else:
            for c in kids:
                place(c)
            nodes[k]["x"] = sum(nodes[c]["x"] for c in kids) / len(kids)

    place(0)
    return cnt[0]


def _parts(P):
    try:
        return int(round(float(P.get("n", 0))))
    except (ValueError, TypeError):
        return 0


def _factors(n):
    out = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            out.append(d)
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out.append(n)
    return out


def _expform(fs):
    parts = []
    for p in sorted(set(fs)):
        e = fs.count(p)
        parts.append(f"{p}{_sup(e)}" if e > 1 else str(p))
    return " × ".join(parts)


def solve(P):
    n = _parts(P)
    if n < 2 or n > 10 ** 12:
        msg = ("2 ile 10¹² arasında bir tam sayı gerekir", "An integer between 2 and 10¹² is needed")
        return {"answer": msg, "steps": [(f"n = {n}", f"n = {n}"), msg], "fmt": {}}
    if _isprime(n):
        r = int(math.isqrt(n))
        ps = [p for p in range(2, r + 1) if _isprime(p)][:12]
        tried = ", ".join(str(p) for p in ps) if ps else "—"
        return {"answer": (f"{n} asaldır: {n} = {n}", f"{n} is prime: {n} = {n}"),
                "steps": [(f"√{n} ≈ {math.sqrt(n):.2f}; bu sayıya kadarki asallar denenir: {tried}",
                           f"√{n} ≈ {math.sqrt(n):.2f}; try the primes up to it: {tried}"),
                          (f"Hiçbiri {n} sayısını tam bölmüyor → {n} asal; ağaç tek düğüm",
                           f"None of them divides {n} → {n} is prime; the tree is a single node")],
                "fmt": {}}
    nodes = _tree(n)
    steps = []
    for nd in nodes:
        if nd["kids"]:
            a, b = (nodes[c]["v"] for c in nd["kids"])
            steps.append((f"{nd['v']} = {a} × {b}", f"{nd['v']} = {a} × {b}"))
    fs = _factors(n)
    flat = " × ".join(str(p) for p in fs)
    steps.append((f"Asal yapraklar (daire içinde): {', '.join(str(p) for p in fs)}",
                  f"Prime leaves (circled): {', '.join(str(p) for p in fs)}"))
    steps.append((f"{n} = {flat}", f"{n} = {flat}"))
    ex = _expform(fs)
    steps.append((f"Üslü yazım: {n} = {ex}", f"Exponent form: {n} = {ex}"))
    exps = [fs.count(p) for p in set(fs)]
    if all(e % 2 == 0 for e in exps):
        r = int(math.isqrt(n))
        steps.append((f"Bütün üsler çift → {n} tam karedir: √{n} = {r}",
                      f"All exponents are even → {n} is a perfect square: √{n} = {r}"))
    return {"answer": f"{n} = {ex}", "steps": steps, "fmt": {}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    n = _parts(P)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.02)
    ax.axis("off")
    info = ax.text(0.01, 0.99, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"), zorder=10)
    if n < 2 or n > 10 ** 12:
        ax.text(0.5, 0.5, "Geçersiz sayı" if tr else "Invalid number", transform=ax.transAxes, ha="center",
                fontsize=18, color="#DC2626")

        def upd0(i):
            return []
        return 60, upd0
    nodes = _tree(n)
    nl = _layout(nodes)
    D = max(nd["d"] for nd in nodes)
    leaves = [k for k, nd in enumerate(nodes) if not nd["kids"]]
    span_x = max(1.0, nl - 1.0)
    ax.set_xlim(-0.9, span_x + 0.9)
    ybot = -(D + 2.6)
    ax.set_ylim(ybot, 1.25)
    fs = 16 if nl <= 6 else (14 if nl <= 9 else (12 if nl <= 13 else 9))
    ax.set_title((f"{n} sayısının çarpan ağacı" if tr else f"Factor tree of {n}"), fontsize=14, fontweight="bold")
    per = 80.0 / max(1, D)
    t_level = [8.0 + d * per for d in range(D + 1)]
    edges = []
    arts = []
    for k, nd in enumerate(nodes):
        prime = not nd["kids"]
        style = dict(boxstyle="circle,pad=0.3", fc="#DCFCE7", ec="#16A34A", lw=2) if prime else \
            dict(boxstyle="round,pad=0.35", fc="#DBEAFE", ec="#2563EB", lw=1.5)
        t = ax.text(nd["x"], -nd["d"], str(nd["v"]), ha="center", va="center", fontsize=fs, fontweight="bold",
                    color="#14532D" if prime else "#1E3A8A", bbox=style, zorder=5)
        arts.append(t)
        if nd["par"] >= 0:
            pn = nodes[nd["par"]]
            ln, = ax.plot([], [], color="#6B7280", lw=1.8, zorder=1)
            edges.append((ln, pn["x"], -pn["d"], nd["x"], -nd["d"], t_level[nd["d"]]))
    fsorted = sorted(nodes[k]["v"] for k in leaves)
    leaf_by_val = sorted(leaves, key=lambda k: (nodes[k]["v"], nodes[k]["x"]))
    yb = -(D + 1.35)
    gap = min(1.0, (span_x + 1.0) / max(1, len(leaves)))
    cx = span_x / 2.0
    targets = [cx + (j - (len(leaves) - 1) / 2.0) * gap for j in range(len(leaves))]
    movers = []
    for j, k in enumerate(leaf_by_val):
        t = ax.text(nodes[k]["x"], -nodes[k]["d"], str(nodes[k]["v"]), ha="center", va="center", fontsize=fs,
                    fontweight="bold", color="#DC2626", zorder=6)
        movers.append((t, nodes[k]["x"], -nodes[k]["d"], targets[j]))
    times = [ax.text((targets[j] + targets[j + 1]) / 2.0, yb, "×", ha="center", va="center", fontsize=fs - 2,
                     color="#374151") for j in range(len(leaves) - 1)]
    ex = _expform(fsorted)
    sq = all(fsorted.count(p) % 2 == 0 for p in set(fsorted))
    tail = (f"   →   √{n} = {int(math.isqrt(n))}" if sq else "")
    final = ax.text(cx, yb - 0.95, f"{n} = {ex}{tail}", ha="center", va="center", fontsize=18, fontweight="bold",
                    color="#DC2626", bbox=dict(boxstyle="round", fc="#FEF2F2", ec="#DC2626"))
    N = 150
    single = D == 0

    def update(i):
        for k, nd in enumerate(nodes):
            tl = t_level[nd["d"]]
            al = _r(i, tl - 0.25 * per, tl) if nd["d"] > 0 else _r(i, 0, 6)
            arts[k].set_alpha(al)
            arts[k].get_bbox_patch().set_alpha(al)
            arts[k].set_visible(al > 0)
        for ln, x0, y0, x1, y1, tl in edges:
            f = _r(i, tl - 0.75 * per, tl - 0.25 * per)
            if f > 0:
                ln.set_data([x0, x0 + (x1 - x0) * f], [y0 - 0.2, y0 - 0.2 + (y1 + 0.2 - y0 + 0.2) * f])
            else:
                ln.set_data([], [])
        m = _r(i, 100, 122)
        sm = m * m * (3 - 2 * m)
        for t, xa, ya, xt in movers:
            t.set_visible(i >= 100)
            t.set_position((xa + (xt - xa) * sm, ya + (yb - ya) * sm))
        for t in times:
            t.set_visible(i >= 122)
        final.set_visible(i >= 128)
        if single:
            info.set_text((f"{n} asaldır: yalnızca 1'e ve kendisine bölünür") if tr else
                          (f"{n} is prime: its only divisors are 1 and itself"))
        elif i < 8:
            info.set_text((f"1) {n} sayısını iki çarpana ayır") if tr else (f"1) Split {n} into two factors"))
        elif i < 92:
            info.set_text("2) Asal olmayan her dalı bölmeye devam et; asallar (yeşil daire) dalı bitirir" if tr else
                          "2) Keep splitting every composite branch; primes (green circles) end a branch")
        elif i < 122:
            info.set_text("3) Asal yaprakları küçükten büyüğe topla" if tr else
                          "3) Collect the prime leaves from smallest to largest")
        else:
            info.set_text((f"4) {n} = {ex}") if tr else (f"4) {n} = {ex}"))
        return []

    return N, update


def vary(P, rnd):
    pool = [2, 2, 2, 3, 3, 5, 7, 11, 13]
    while True:
        k = rnd.randint(3, 5)
        fs = [rnd.choice(pool) for _ in range(k)]
        v = 1
        for p in fs:
            v *= p
        if 30 <= v <= 1000 and not _isprime(v):
            return {"n": v}
''',
}
EXAMPLES += [
    {"id": "fund-prime-1", "kind": "prime_factor_tree",
     "title": ("Çarpan ağacı", "A factor tree"),
     "q": ("{n} sayısını çarpan ağacı kullanarak asal çarpanlarına ayır.",
           "Use a factor tree to write {n} as a product of primes."),
     "P": {"n": 360}},
    {"id": "fund-prime-2", "kind": "prime_factor_tree",
     "title": ("Asal çarpanlar ve üslü yazım", "Prime factors in exponent form"),
     "q": ("{n} sayısının asal çarpanlarını bul ve üslü biçimde yaz.",
           "Find the prime factors of {n} and write them in exponent form."),
     "P": {"n": 84}},
    {"id": "fund-prime-3", "kind": "prime_factor_tree", "topics": ["perfect square", "tam kare", "square root"],
     "title": ("Tam kare mi?", "Is it a perfect square?"),
     "q": ("{n} sayısını asal çarpanlarına ayır. Bu çarpanlara bakarak {n} tam kare midir?",
           "Write {n} as a product of primes. Using the factors, decide whether {n} is a perfect square."),
     "P": {"n": 196}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["decimal_ops"] = {
    "course": "fund",
    "title": ("Ondalık sayılarla işlemler", "Operations with decimals"),
    "topics": ["decimals", "decimal numbers", "adding decimals", "subtracting decimals",
               "multiplying decimals", "dividing decimals", "decimal point", "place value",
               "ondalık sayılar", "ondalık gösterim", "ondalık", "basamak değeri",
               "ondalık sayılarla toplama", "ondalık sayılarla çarpma", "ondalık sayılarla bölme"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle

_PL_TR = ["birler", "onlar", "yüzler", "binler", "on binler", "yüz binler", "milyonlar"]
_PL_EN = ["ones", "tens", "hundreds", "thousands", "ten-thousands", "hundred-thousands", "millions"]
_DP_TR = ["onda birler", "yüzde birler", "binde birler", "on binde birler", "yüz binde birler",
          "milyonda birler"]
_DP_EN = ["tenths", "hundredths", "thousandths", "ten-thousandths", "hundred-thousandths", "millionths"]


def _fr(v):
    try:
        return Fraction(str(v).strip().replace(",", "."))
    except (ValueError, ZeroDivisionError):
        return Fraction(float(v)).limit_denominator(10 ** 9)


def _dp(v):
    for k in range(0, 13):
        if (v * 10 ** k).denominator == 1:
            return k
    return None


def _dec(v, tr, k=None):
    v = Fraction(v)
    neg = v < 0
    v = abs(v)
    kk = _dp(v)
    if kk is None:
        s = f"{float(v):.6f}" + "…"
    else:
        if k is not None and k > kk:
            kk = k
        n = int(v * 10 ** kk)
        t = str(n).rjust(kk + 1, "0")
        s = t if kk == 0 else t[:-kk] + "." + t[-kk:]
    s = ("−" if neg else "") + s
    return s.replace(".", ",") if tr else s


def _op(P):
    o = str(P.get("op", "+")).strip()
    if o in ("-", "−", "–"):
        return "-"
    if o in ("*", "×", "x", "·"):
        return "*"
    if o in ("/", "÷", ":"):
        return "/"
    return "+"


def _place(j, tr):
    if j >= 0:
        lst = _PL_TR if tr else _PL_EN
        return lst[j] if j < len(lst) else f"10^{j}"
    lst = _DP_TR if tr else _DP_EN
    return lst[-j - 1] if -j - 1 < len(lst) else f"10^{j}"


def _r(i, t0, t1):
    return min(1.0, max(0.0, (i - t0) / float(t1 - t0)))


def _mag(a, b, op):
    y = b if op == "+" else -b
    if (a >= 0 and y >= 0) or (a <= 0 and y <= 0):
        return "+", abs(a), abs(y), (-1 if (a < 0 or y < 0) else 1)
    if abs(a) >= abs(y):
        return "-", abs(a), abs(y), (1 if a > 0 else -1)
    return "-", abs(y), abs(a), (1 if y > 0 else -1)


def _columns(top, bot, mode):
    D = min(8, max(_dp(top) or 0, _dp(bot) or 0))
    res = top + bot if mode == "+" else top - bot

    def digs(v):
        n = int(v * 10 ** D)
        s = str(n).rjust(D + 1, "0")
        return (s[:-D], s[-D:]) if D else (s, "")

    ti, tf = digs(top)
    bi, bf = digs(bot)
    ri, rf = digs(res)
    I = max(len(ti), len(bi), len(ri))
    tdig = [None] * (I - len(ti)) + [int(c) for c in ti + tf]
    bdig = [None] * (I - len(bi)) + [int(c) for c in bi + bf]
    rdig = [None] * (I - len(ri)) + [int(c) for c in ri + rf]
    padt = [False] * I + [k >= (_dp(top) or 0) for k in range(D)]
    padb = [False] * I + [k >= (_dp(bot) or 0) for k in range(D)]
    ev = []
    carry = 0
    for j in range(I + D - 1, -1, -1):
        t = tdig[j] or 0
        u = bdig[j] or 0
        if mode == "+":
            s = t + u + carry
            ev.append({"j": j, "t": t, "u": u, "cin": carry, "s": s, "dig": s % 10, "cout": s // 10})
            carry = s // 10
        else:
            eff = t - carry
            bout = 0
            if eff < u:
                eff += 10
                bout = 1
            ev.append({"j": j, "t": t, "u": u, "bin": carry, "eff": eff, "dig": eff - u, "bout": bout})
            carry = bout
    for k in range(I - 1):
        if rdig[k] in (None, 0):
            rdig[k] = None
        else:
            break
    return {"D": D, "I": I, "top": tdig, "bot": bdig, "res": rdig, "padt": padt, "padb": padb, "ev": ev,
            "val": res}


def _colstep(e, I, mode, tr):
    pl = _place(I - 1 - e["j"], tr)
    if mode == "+":
        if tr:
            s = f"{pl}: {e['t']} + {e['u']}" + (f" + {e['cin']} (elde)" if e["cin"] else "") + f" = {e['s']}"
            return s + (f" → {e['dig']} yaz, {e['cout']} elde" if e["cout"] else "")
        s = f"{pl}: {e['t']} + {e['u']}" + (f" + {e['cin']} (carry)" if e["cin"] else "") + f" = {e['s']}"
        return s + (f" → write {e['dig']}, carry {e['cout']}" if e["cout"] else "")
    t_eff = e["t"] - e["bin"]
    if t_eff < 0:
        return (f"{pl}: bu 0 ödünç verdiği için 9 olur → 9 − {e['u']} = {e['dig']}" if tr else
                f"{pl}: this 0 passes the borrow on and becomes 9 → 9 − {e['u']} = {e['dig']}")
    if e["bout"]:
        return (f"{pl}: {t_eff} < {e['u']}, soldan 1 ödünç al → {e['eff']} − {e['u']} = {e['dig']}" if tr else
                f"{pl}: {t_eff} < {e['u']}, borrow 1 from the left → {e['eff']} − {e['u']} = {e['dig']}")
    return f"{pl}: {e['eff']} − {e['u']} = {e['dig']}"


def _symb(op):
    return {"+": "+", "-": "−", "*": "×", "/": "÷"}[op]


def solve(P):
    a, b, op = _fr(P.get("a", 0)), _fr(P.get("b", 0)), _op(P)
    A = (_dec(a, True), _dec(a, False))
    B = (_dec(b, True), _dec(b, False))
    Bp = tuple(("(" + x + ")") if b < 0 else x for x in B)
    ex = (f"{A[0]} {_symb(op)} {Bp[0]}", f"{A[1]} {_symb(op)} {Bp[1]}")
    fmt = {"A": A, "B": B, "expr": ex}
    steps = []
    if op in "+-":
        mode, top, bot, sg = _mag(a, b, op)
        if a < 0 or b < 0 or (mode == "-" and top != abs(a)):
            steps.append(((f"İşaretlere göre {_dec(top, True)} {_symb(mode)} {_dec(bot, True)} hesaplanır, "
                           f"sonucun işareti {'−' if sg < 0 else '+'}"),
                          (f"By the signs we compute {_dec(top, False)} {_symb(mode)} {_dec(bot, False)}; "
                           f"the result is {'negative' if sg < 0 else 'positive'}")))
        C = _columns(top, bot, mode)
        D = C["D"]
        steps.append(((f"Virgülleri alt alta hizala, eksik basamaklara 0 yaz: {_dec(top, True, D)} ve "
                       f"{_dec(bot, True, D)}"),
                      (f"Line up the decimal points and pad with zeros: {_dec(top, False, D)} and "
                       f"{_dec(bot, False, D)}")))
        for e in C["ev"]:
            steps.append((_colstep(e, C["I"], mode, True), _colstep(e, C["I"], mode, False)))
        val = (a + b) if op == "+" else (a - b)
    elif op == "*":
        da, db = _dp(abs(a)) or 0, _dp(abs(b)) or 0
        na, nb = int(abs(a) * 10 ** da), int(abs(b) * 10 ** db)
        prod = na * nb
        val = a * b
        steps.append((f"Virgülleri yok sayarak çarp: {na} × {nb} = {prod}",
                      f"Ignore the decimal points and multiply: {na} × {nb} = {prod}"))
        steps.append((f"Ondalık basamak sayısı: {da} + {db} = {da + db}",
                      f"Count the decimal places: {da} + {db} = {da + db}"))
        steps.append((f"{prod} sayısında virgülü sağdan {da + db} basamak sola kaydır → {_dec(abs(val), True, da + db)}",
                      f"Move the point in {prod} {da + db} places to the left → {_dec(abs(val), False, da + db)}"))
        if val < 0:
            steps.append(("İşaretler farklı → sonuç negatif", "Different signs → negative result"))
    else:
        if b == 0:
            msg = ("Sıfıra bölme tanımsızdır!", "Division by zero is undefined!")
            return {"answer": msg, "steps": [(f"İfade: {ex[0]}", f"Expression: {ex[1]}"), msg], "fmt": fmt}
        db = _dp(abs(b)) or 0
        a2, b2 = abs(a) * 10 ** db, abs(b) * 10 ** db
        val = a / b
        if db:
            steps.append((f"Böleni tam sayı yap: iki sayıda da virgülü {db} basamak sağa kaydır",
                          f"Make the divisor whole: move the point {db} places right in both numbers"))
        else:
            steps.append(("Bölen zaten tam sayı; doğrudan böl", "The divisor is already whole; divide directly"))
        steps.append((f"{_dec(abs(a), True)} ÷ {_dec(abs(b), True)} = {_dec(a2, True)} ÷ {_dec(b2, True)} = {_dec(abs(val), True)}",
                      f"{_dec(abs(a), False)} ÷ {_dec(abs(b), False)} = {_dec(a2, False)} ÷ {_dec(b2, False)} = {_dec(abs(val), False)}"))
        if _dp(abs(val)) is None:
            steps.append((f"Bölüm devirli ondalık: {_dec(abs(val), True)} = {abs(val).numerator}/{abs(val).denominator}",
                          f"The quotient repeats: {_dec(abs(val), False)} = {abs(val).numerator}/{abs(val).denominator}"))
        if val < 0:
            steps.append(("İşaretler farklı → sonuç negatif", "Different signs → negative result"))
    rt, re_ = _dec(val, True), _dec(val, False)
    if _dp(abs(val)) is None:
        rt += f" ({val.numerator}/{val.denominator})".replace("-", "−")
        re_ += f" ({val.numerator}/{val.denominator})".replace("-", "−")
    steps.append((f"Sonuç: {ex[0]} = {rt}", f"Result: {ex[1]} = {re_}"))
    return {"answer": (f"{ex[0]} = {rt}", f"{ex[1]} = {re_}"), "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, op = _fr(P.get("a", 0)), _fr(P.get("b", 0)), _op(P)
    sep = "," if tr else "."
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    ax.axis("off")
    info = ax.text(0.01, 0.985, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"), zorder=10)
    sol = solve(P)
    ans = sol["answer"][0] if tr else sol["answer"][1]
    fw, fh = fig.get_size_inches()
    pos = ax.get_position()
    aw, ah = pos.width * fw * 72.0, pos.height * fh * 72.0
    if op == "/" and b == 0:
        ax.text(0.5, 0.5, ans, transform=ax.transAxes, ha="center", fontsize=16, color="#DC2626")

        def upd0(i):
            return []
        return 60, upd0
    N = 150
    if op in "+-":
        mode, top, bot, sg = _mag(a, b, op)
        C = _columns(top, bot, mode)
        D, I = C["D"], C["I"]
        ncol = I + D
        Wu = max(ncol + 2.6, 11.0)
        xl = -(Wu - ncol - 1) / 2.0
        ax.set_xlim(xl, xl + Wu)
        ax.set_ylim(-0.6, 6.4)
        cell = aw / Wu
        rowpt = ah / 7.0
        fsd = max(8.0, min(30.0, 0.95 * cell, 0.62 * rowpt))
        yC, yT, yB, yL, yR, yH = 3.75, 3.0, 2.0, 1.45, 0.75, 4.55
        hl = Rectangle((0, 0.25), 1, 4.0, fc="#FEF3C7", ec="none", zorder=0)
        ax.add_patch(hl)
        fsh = max(6.0, min(9.0, cell * 0.24))
        for j in range(ncol):
            ax.text(j + 1.5, yH, _place(I - 1 - j, tr), rotation=35, ha="left", va="bottom", fontsize=fsh,
                    color="#6B7280", rotation_mode="anchor")
        tops, bots, ress = [], [], []
        for j in range(ncol):
            d = C["top"][j]
            tops.append(ax.text(j + 1.5, yT, "" if d is None else str(d), ha="center", va="center",
                                fontsize=fsd, color="#9CA3AF" if C["padt"][j] else "#1E3A8A", fontweight="bold"))
            d = C["bot"][j]
            bots.append(ax.text(j + 1.5, yB, "" if d is None else str(d), ha="center", va="center",
                                fontsize=fsd, color="#9CA3AF" if C["padb"][j] else "#9A3412", fontweight="bold"))
            ress.append(ax.text(j + 1.5, yR, "", ha="center", va="center", fontsize=fsd, color="#15803D",
                                fontweight="bold"))
        if D:
            for yy in (yT, yB):
                ax.text(I + 1, yy - 0.28, sep, ha="center", va="center", fontsize=fsd, fontweight="bold")
            rsep = ax.text(I + 1, yR - 0.28, sep, ha="center", va="center", fontsize=fsd, fontweight="bold",
                           color="#15803D")
        else:
            rsep = ax.text(0, 0, "")
        ax.text(0.5, yB, _symb(mode), ha="center", va="center", fontsize=fsd, fontweight="bold")
        ax.plot([0.2, ncol + 1.1], [yL, yL], color="#111827", lw=2.2)
        rsign = ax.text(0.5, yR, "−" if sg < 0 else "", ha="center", va="center", fontsize=fsd, color="#15803D",
                        fontweight="bold")
        extras = []
        for e in C["ev"]:
            j = e["j"]
            if mode == "+":
                tx = ax.text(j + 0.5, yC, str(e["cout"]) if e["cout"] else "", ha="center", va="center",
                             fontsize=fsd * 0.6, color="#DC2626", fontweight="bold")
                extras.append((tx, None))
            else:
                changed = e["bin"] or e["bout"]
                tx = ax.text(j + 1.5, yC, str(e["eff"]) if changed else "", ha="center", va="center",
                             fontsize=fsd * 0.6, color="#DC2626", fontweight="bold")
                st_, = ax.plot([j + 1.2, j + 1.8], [yT - 0.3, yT + 0.3], color="#DC2626", lw=2)
                st_.set_visible(False)
                extras.append((tx, st_ if changed else None))
        T0, T1 = 20.0, 125.0
        per = (T1 - T0) / max(1, ncol)
        steps_txt = [_colstep(e, I, mode, tr) for e in C["ev"]]
        pad_any = any(C["padt"]) or any(C["padb"])

        def update(i):
            for j in range(ncol):
                tops[j].set_alpha(1.0 if (not C["padt"][j] or i >= 10) else 0.0)
                bots[j].set_alpha(1.0 if (not C["padb"][j] or i >= 10) else 0.0)
            cur = -1
            for m, e in enumerate(C["ev"]):
                j = e["j"]
                t0 = T0 + m * per
                on = i >= t0 + 0.45 * per
                d = C["res"][j]
                ress[j].set_text("" if (d is None or not on) else str(d))
                tx, st_ = extras[m]
                tx.set_visible(i >= t0 + 0.3 * per)
                if st_ is not None:
                    st_.set_visible(i >= t0 + 0.3 * per)
                if t0 <= i < t0 + per:
                    cur = m
            if 0 <= cur and i < T1:
                hl.set_visible(True)
                hl.set_x(C["ev"][cur]["j"] + 1)
            else:
                hl.set_visible(False)
            rsep.set_alpha(1.0 if i >= T1 else 0.0)
            rsign.set_alpha(1.0 if i >= T1 else 0.0)
            if i < T0:
                info.set_text(("1) Virgülleri alt alta hizala" + (", boş basamaklara 0 yaz" if pad_any else "")) if tr else
                              ("1) Line up the decimal points" + (" and fill empty places with 0" if pad_any else "")))
            elif i < T1 and cur >= 0:
                info.set_text(f"{'2) Sağdan sola' if tr else '2) Right to left'} — {steps_txt[cur]}")
            else:
                info.set_text("3) " + ans)
            return []

        return N, update
    if op == "*":
        A_s, B_s = _dec(abs(a), tr), _dec(abs(b), tr)
        ai, af = (A_s.split(sep) + [""])[:2]
        bi, bf = (B_s.split(sep) + [""])[:2]
        da, db = len(af), len(bf)
        na, nb = int(ai + af), int(bi + bf)
        prod = na * nb
        Dt = da + db
        ps = str(prod).rjust(Dt + 1, "0")
        padn = len(ps) - len(str(prod))
        row2 = f"{na} × {nb} = {prod}"
        res_s = _dec(a * b, tr)
        shown = ps[:len(ps) - Dt] + ((sep + ps[len(ps) - Dt:]) if Dt else "")
        tail_s = ("= " + res_s) if (res_s != shown) else ""
        lenA, lenB = len(ai + af), len(bi + bf)
        Wu = max(14.0, lenA + lenB + 6.0, len(row2) * 0.75 + 4.0, len(ps) + len(tail_s) * 0.8 + 4.0)
        ax.set_xlim(0, Wu)
        ax.set_ylim(0, 6.0)
        cell = aw / Wu
        fsd = max(8.0, min(28.0, 1.25 * cell, ah / 6.0 * 0.55))
        c0 = 1.0
        cB = c0 + lenA + 3
        y1, y2, y3 = 4.15, 2.75, 1.2
        r1 = []
        for k, ch in enumerate(ai + af):
            r1.append(ax.text(c0 + k + 0.5, y1, ch, ha="center", va="center", fontsize=fsd, fontweight="bold",
                              color="#1E3A8A"))
        for k, ch in enumerate(bi + bf):
            r1.append(ax.text(cB + k + 0.5, y1, ch, ha="center", va="center", fontsize=fsd, fontweight="bold",
                              color="#9A3412"))
        r1.append(ax.text(c0 + lenA + 1.5, y1, "×", ha="center", va="center", fontsize=fsd, fontweight="bold"))
        if da:
            r1.append(ax.text(c0 + len(ai), y1 - 0.32, sep, ha="center", va="center", fontsize=fsd * 1.2,
                              fontweight="bold"))
        if db:
            r1.append(ax.text(cB + len(bi), y1 - 0.32, sep, ha="center", va="center", fontsize=fsd * 1.2,
                              fontweight="bold"))
        unders = []
        for x_0, dd, colr in ((c0 + len(ai), da, "#2563EB"), (cB + len(bi), db, "#E07B39")):
            if dd:
                ln, = ax.plot([x_0 + 0.08, x_0 + dd - 0.08], [y1 - 0.66, y1 - 0.66], color=colr, lw=3)
                t = ax.text(x_0 + dd / 2.0, y1 - 0.76, str(dd), ha="center", va="top", fontsize=fsd * 0.5,
                            color=colr, fontweight="bold")
                unders += [ln, t]
        t2 = ax.text(c0, y2, row2, ha="left", va="center", fontsize=fsd * 0.8, color="#7C3AED")
        r3 = []
        for k, ch in enumerate(ps):
            r3.append(ax.text(c0 + k + 0.5, y3, ch, ha="center", va="center", fontsize=fsd, fontweight="bold",
                              color="#9CA3AF" if k < padn else "#111827"))
        pt = ax.text(0, y3 - 0.32, sep, ha="center", va="center", fontsize=fsd * 1.2, fontweight="bold",
                     color="#DC2626")
        hops = []
        tt = np.linspace(0, 1, 30)
        for m in range(Dt):
            xa = c0 + len(ps) - m
            ln, = ax.plot([], [], color="#DC2626", lw=1.8)
            lab = ax.text(xa - 0.5, y3 - 0.98, str(m + 1), ha="center", va="top", fontsize=fsd * 0.45,
                          color="#DC2626", fontweight="bold")
            hops.append((xa - tt, y3 - 0.5 - 0.4 * np.sin(np.pi * tt), ln, lab))
        sgn = "−" if a * b < 0 else ""
        tail = ax.text(c0 + len(ps) + 0.8, y3, tail_s, ha="left", va="center", fontsize=fsd, fontweight="bold",
                       color="#16A34A")
        H0, H1 = 55.0, 110.0

        def update(i):
            for t in r1:
                t.set_alpha(_r(i, 0, 8))
            for u in unders:
                u.set_alpha(_r(i, 10, 16))
            t2.set_alpha(_r(i, 22, 30))
            for k, t in enumerate(r3):
                t.set_alpha(_r(i, 40, 48) if k >= padn else _r(i, H0 - 4, H0))
            prog = _r(i, H0, H1) * Dt
            for m, (xs, ys, ln, lab) in enumerate(hops):
                f = min(1.0, max(0.0, prog - m))
                if f > 0:
                    q = max(2, int(f * len(xs)))
                    ln.set_data(xs[:q], ys[:q])
                else:
                    ln.set_data([], [])
                lab.set_alpha(1.0 if f >= 1 else 0.0)
            fr_ = prog - int(prog) if prog < Dt else 0.0
            pt.set_position((c0 + len(ps) - prog, y3 - 0.32 - 0.4 * np.sin(np.pi * fr_)))
            pt.set_alpha(_r(i, 48, 54) if Dt else 0.0)
            tail.set_alpha(_r(i, H1 + 5, H1 + 12))
            if i < 22:
                info.set_text((f"1) Çarpanlarda ondalık basamakları say: {da} + {db} = {Dt}") if tr else
                              (f"1) Count the decimal places in the factors: {da} + {db} = {Dt}"))
            elif i < H0:
                info.set_text((f"2) Virgülleri yok say: {na} × {nb} = {prod}") if tr else
                              (f"2) Ignore the points: {na} × {nb} = {prod}"))
            elif i < H1 + 5:
                info.set_text((f"3) Virgülü sağdan {Dt} basamak sola kaydır") if tr else
                              (f"3) Move the point {Dt} places to the left"))
            else:
                info.set_text("4) " + ans)
            return []

        return N, update
    A_s, B_s = _dec(abs(a), tr), _dec(abs(b), tr)
    da, db = _dp(abs(a)) or 0, _dp(abs(b)) or 0
    ai, af = (A_s.split(sep) + [""])[:2]
    bi, bf = (B_s.split(sep) + [""])[:2]
    need = max(0, db - len(af))
    dvd = ai + af + "0" * need
    dvs = bi + bf
    a2, b2 = abs(a) * 10 ** db, abs(b) * 10 ** db
    q = abs(a / b)
    row2 = f"{_dec(a2, tr)} ÷ {_dec(b2, tr)} = {_dec(q, tr)}"
    gap = 3
    Wu = max(14.0, len(dvd) + len(dvs) + gap + 4.0, len(row2) * 0.75 + 4.0, len(ans) * 0.7 + 2)
    ax.set_xlim(0, Wu)
    ax.set_ylim(0, 6.0)
    cell = aw / Wu
    fsd = max(8.0, min(28.0, 1.25 * cell, ah / 6.0 * 0.55))
    c0 = 1.0
    cB = c0 + len(dvd) + gap
    y1, y2, y3 = 4.2, 2.35, 1.05
    d1 = []
    for k, ch in enumerate(dvd):
        isp = k >= len(ai) + len(af)
        d1.append((ax.text(c0 + k + 0.5, y1, ch, ha="center", va="center", fontsize=fsd, fontweight="bold",
                           color="#9CA3AF" if isp else "#1E3A8A"), isp, k))
    d2 = [ax.text(cB + k + 0.5, y1, ch, ha="center", va="center", fontsize=fsd, fontweight="bold",
                  color="#9A3412") for k, ch in enumerate(dvs)]
    ax.text(c0 + len(dvd) + gap / 2.0, y1, "÷", ha="center", va="center", fontsize=fsd, fontweight="bold")
    pa = ax.text(0, y1 - 0.32, sep, ha="center", va="center", fontsize=fsd * 1.2, fontweight="bold", color="#DC2626")
    pb = ax.text(0, y1 - 0.32, sep, ha="center", va="center", fontsize=fsd * 1.2, fontweight="bold", color="#DC2626")
    tt = np.linspace(0, 1, 30)
    hops = []
    for m in range(db):
        for base_x, colr in ((c0 + len(ai) + m, "#2563EB"), (cB + len(bi) + m, "#E07B39")):
            ln, = ax.plot([], [], color=colr, lw=1.8)
            hops.append((base_x + tt, y1 - 0.5 - 0.4 * np.sin(np.pi * tt), ln, m))
    lz_a = 0
    while lz_a < len(ai) + db - 1 and dvd[lz_a] == "0":
        lz_a += 1
    lz_b = 0
    while lz_b < len(dvs) - 1 and dvs[lz_b] == "0":
        lz_b += 1
    t2 = ax.text(c0, y2, row2, ha="left", va="center", fontsize=fsd * 0.8, color="#7C3AED")
    t3 = ax.text(c0, y3, ans, ha="left", va="center", fontsize=fsd * 0.8, fontweight="bold", color="#16A34A")
    H0, H1 = 20.0, 75.0

    def update(i):
        prog = _r(i, H0, H1) * db
        fin = db > 0 and prog >= db
        for t, isp, k in d1:
            t.set_alpha(_r(i, 0, 8) if not isp else (1.0 if prog > k - len(ai) else 0.0))
            t.set_color("#9CA3AF" if (isp and not fin) or (fin and k < lz_a) else "#1E3A8A")
        for k, t in enumerate(d2):
            t.set_alpha(_r(i, 0, 8))
            t.set_color("#9CA3AF" if (fin and k < lz_b) else "#9A3412")
        for xs, ys, ln, m in hops:
            f = min(1.0, max(0.0, prog - m))
            if f > 0:
                qq = max(2, int(f * len(xs)))
                ln.set_data(xs[:qq], ys[:qq])
            else:
                ln.set_data([], [])
        fr_ = prog - int(prog) if prog < db else 0.0
        dy_ = 0.4 * np.sin(np.pi * fr_)
        pa.set_position((c0 + len(ai) + prog, y1 - 0.32 - dy_))
        pb.set_position((cB + len(bi) + prog, y1 - 0.32 - dy_))
        g0 = _r(i, 0, 8)
        pa.set_alpha(g0 if (len(ai) + prog < len(dvd) - 1e-9) or (0 < prog < db) else 0.0)
        pb.set_alpha(g0 if (len(bi) + prog < len(dvs) - 1e-9) or (0 < prog < db) else 0.0)
        if db == 0:
            pa.set_alpha(g0 if af else 0.0)
            pb.set_alpha(0.0)
        t2.set_alpha(_r(i, H1 + 2, H1 + 10))
        t3.set_alpha(_r(i, 112, 120))
        if i < H0:
            info.set_text(("1) Bölen tam sayı olmalı" if db else "1) Bölen zaten tam sayı") if tr else
                          ("1) The divisor must be a whole number" if db else "1) The divisor is already whole"))
        elif i < H1 + 2:
            info.set_text((f"2) İki virgülü de {db} basamak sağa kaydır (×{10 ** db})") if tr else
                          (f"2) Move both points {db} places right (×{10 ** db})"))
        elif i < 112:
            info.set_text("3) Şimdi tam sayıya böl: " + row2 if tr else "3) Now divide by a whole number: " + row2)
        else:
            info.set_text("4) " + ans)
        return []

    return N, update


def vary(P, rnd):
    op = _op(P)

    def mk(lo, hi, places):
        return float(Fraction(rnd.randint(lo, hi), 10 ** places))

    if op == "+":
        return {"a": mk(11, 999, rnd.choice([1, 2])), "b": mk(11, 999, rnd.choice([1, 2])), "op": "+"}
    if op == "-":
        while True:
            a = mk(101, 3000, rnd.choice([0, 1, 2]))
            b = mk(11, 999, 2)
            if b < a:
                return {"a": a, "b": b, "op": "-"}
    if op == "*":
        return {"a": mk(12, 99, 1), "b": mk(12, 99, rnd.choice([1, 2])), "op": "*"}
    b = rnd.choice([0.25, 0.5, 0.4, 0.2, 1.5, 0.75, 0.05, 2.5, 1.2, 0.3])
    q = rnd.choice([4, 6, 8, 12, 15, 20, 24, 30, 1.5, 2.5, 3.5])
    return {"a": float(Fraction(str(b)) * Fraction(str(q))), "b": b, "op": "/"}
''',
}
EXAMPLES += [
    {"id": "fund-dec-1", "kind": "decimal_ops", "topics": ["money", "change", "para üstü", "word problem"],
     "title": ("Sözel problem: para üstü", "Word problem: getting change"),
     "q": ("{B} TL'lik bir ürün için kasaya {A} TL verdin. Kaç TL para üstü alırsın? ({expr})",
           "You pay {A} for an item costing {B}. How much change do you get? ({expr})"),
     "P": {"a": 20.0, "b": 7.85, "op": "-"}},
    {"id": "fund-dec-2", "kind": "decimal_ops",
     "title": ("Ondalık sayılarla çarpma", "Multiplying decimals"),
     "q": ("{expr} çarpımını hesapla.", "Compute the product {expr}."),
     "P": {"a": 3.6, "b": 2.5, "op": "*"}},
    {"id": "fund-dec-3", "kind": "decimal_ops", "topics": ["juice", "meyve suyu", "word problem"],
     "title": ("Sözel problem: bardaklara paylaştırma", "Word problem: filling cups"),
     "q": ("{A} litre meyve suyu {B} litrelik bardaklara dolduruluyor. Kaç bardak dolar? ({expr})",
           "{A} litres of juice are poured into {B}-litre cups. How many cups are filled? ({expr})"),
     "P": {"a": 7.5, "b": 0.25, "op": "/"}},
]
