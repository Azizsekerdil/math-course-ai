# -*- coding: utf-8 -*-
"""Cebir simülasyonları (1/2): doğrusal denklem, doğru denklemleri, sistemler,
ikinci derece denklem, genel fonksiyon grafiği.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Sorular kurs
kitaplarından KOPYALANMAZ: kendi ifademizle yazılmış, sayıları değiştirilmiş
tipik ders örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["linear_equation"] = {
    "course": "alg",
    "title": ("Doğrusal denklem çözümü", "Solving a linear equation"),
    "topics": ["linear equation", "solving equations", "one-step", "two-step", "multi-step",
               "equations", "solve for x", "doğrusal denklem", "birinci derece", "denklem çöz"],
    "code": r'''
import numpy as np
from fractions import Fraction


def _f(v):
    v = Fraction(v).limit_denominator(1000)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _lhs(a, b):
    ax = ("" if a == 1 else ("-" if a == -1 else _f(a))) + "x"
    if b == 0:
        return ax
    return f"{ax} {'+' if b > 0 else '-'} {_f(abs(b))}"


def solve(P):
    a, b, c = P["a"], P["b"], P["c"]
    x = Fraction(c - b) / Fraction(a)
    op1 = (f"Her iki taraftan {_f(b)} çıkar" if b >= 0 else f"Her iki tarafa {_f(-b)} ekle",
           f"Subtract {_f(b)} from both sides" if b >= 0 else f"Add {_f(-b)} to both sides")
    steps = [
        (f"Denklem: {_lhs(a, b)} = {_f(c)}", f"Equation: {_lhs(a, b)} = {_f(c)}"),
        (f"{op1[0]}: {_f(a)}x = {_f(c - b)}", f"{op1[1]}: {_f(a)}x = {_f(c - b)}"),
        (f"Her iki tarafı {_f(a)} ile böl: x = {_f(c - b)}/{_f(a)}",
         f"Divide both sides by {_f(a)}: x = {_f(c - b)}/{_f(a)}"),
        (f"Sonuç: x = {_f(x)}", f"Result: x = {_f(x)}"),
        (f"Kontrol: {_f(a)}·({_f(x)}) {'+' if b >= 0 else '-'} {_f(abs(b))} = {_f(a * x + b)} ✓",
         f"Check: {_f(a)}·({_f(x)}) {'+' if b >= 0 else '-'} {_f(abs(b))} = {_f(a * x + b)} ✓"),
    ]
    return {"answer": f"x = {_f(x)}", "steps": steps, "fmt": {"lhs": _lhs(a, b)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, c = P["a"], P["b"], P["c"]
    x0 = (c - b) / a
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.25], left=0.03, right=0.97, wspace=0.12)
    tx = fig.add_subplot(gs[0, 0])
    tx.axis("off")
    ax = fig.add_subplot(gs[0, 1])
    span = max(6.0, abs(x0) * 1.6 + 2)
    xs = np.linspace(x0 - span, x0 + span, 300)
    ys = a * xs + b
    ax.set_xlim(xs[0], xs[-1])
    lo, hi = min(ys.min(), c) - 2, max(ys.max(), c) + 2
    ax.set_ylim(lo, hi)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#9CA3AF", lw=1)
    ax.axvline(0, color="#9CA3AF", lw=1)
    line, = ax.plot([], [], color="#2563EB", lw=2.4, label=f"y = {_lhs(a, b)}")
    hline, = ax.plot([], [], color="#E07B39", lw=2.4, label=f"y = {_f(c)}")
    dot, = ax.plot([], [], "o", ms=11, color="#DC2626", zorder=5)
    vline, = ax.plot([], [], "--", color="#DC2626", lw=1.4)
    lab = ax.text(0, 0, "", color="#DC2626", fontsize=12, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    lines = [f"{_lhs(a, b)} = {_f(c)}", f"{_f(a)}x = {_f(c - b)}", f"x = {_f(c - b)}/{_f(a)}",
             f"x = {_f(Fraction(c - b) / Fraction(a))}"]
    notes = [("Denklem", "Equation"),
             ((f"−{_f(b)} her iki taraf" if b >= 0 else f"+{_f(-b)} her iki taraf"),
              (f"−{_f(b)} both sides" if b >= 0 else f"+{_f(-b)} both sides")),
             (f"÷{_f(a)} her iki taraf", f"÷{_f(a)} both sides"),
             ("Çözüm", "Solution")]
    txts = []
    for k in range(4):
        t1 = tx.text(0.04, 0.84 - k * 0.2, lines[k], fontsize=19, family="DejaVu Sans Mono",
                     color="#111827", alpha=0)
        t2 = tx.text(0.06, 0.77 - k * 0.2, notes[k][0 if tr else 1], fontsize=10,
                     color="#6B7280", alpha=0)
        txts.append((t1, t2))
    tx.set_title("Adım adım çözüm" if tr else "Step by step", fontsize=12, loc="left")
    ax.set_title("Grafikle kontrol: iki doğrunun kesişimi" if tr else
                 "Graphical check: where the lines meet", fontsize=11)
    N = 120

    def update(i):
        for k, (t1, t2) in enumerate(txts):
            al = min(1.0, max(0.0, (i - k * 18) / 12))
            t1.set_alpha(al)
            t2.set_alpha(al)
            t1.set_color("#DC2626" if (k == 3 and i >= 54) else "#111827")
        p = min(1.0, max(0.0, (i - 60) / 30))
        m = max(2, int(p * len(xs)))
        line.set_data(xs[:m], ys[:m])
        hline.set_data(xs[:m], np.full(m, c))
        if i >= 92:
            dot.set_data([x0], [c])
            vline.set_data([x0, x0], [lo, c])
            lab.set_position((x0 + span * 0.04, c + (hi - lo) * 0.04))
            lab.set_text(f"x = {_f(Fraction(c - b) / Fraction(a))}")
        else:
            dot.set_data([], [])
            vline.set_data([], [])
            lab.set_text("")
        return []

    return N, update


def vary(P, rnd):
    a = rnd.choice([2, 3, 4, 5, -2, -3, 6])
    x = rnd.randint(-6, 9)
    b = rnd.choice([v for v in range(-12, 13) if v != 0])
    return {"a": a, "b": b, "c": a * x + b}
''',
}
EXAMPLES += [
    {"id": "alg-lineq-1", "kind": "linear_equation",
     "title": ("İki adımlı denklem", "Two-step equation"),
     "q": ("{lhs} = {c} denklemini x için çöz.", "Solve {lhs} = {c} for x."),
     "P": {"a": 3, "b": 7, "c": 25}},
    {"id": "alg-lineq-2", "kind": "linear_equation",
     "title": ("Negatif katsayılı denklem", "Equation with a negative coefficient"),
     "q": ("{lhs} = {c} ise x kaçtır?", "If {lhs} = {c}, what is x?"),
     "P": {"a": -4, "b": 9, "c": -11}},
    {"id": "alg-lineq-3", "kind": "linear_equation", "topics": ["word problem", "sözel problem"],
     "title": ("Sözel problem: taksi ücreti", "Word problem: taxi fare"),
     "q": ("Bir taksi açılışta {b} TL, her km için {a} TL alıyor. Yolculuk {c} TL tuttu. "
           "Kaç km gidildi? ({lhs} = {c})",
           "A taxi charges {b} to start plus {a} per km. The ride cost {c}. "
           "How many km? ({lhs} = {c})"),
     "P": {"a": 6, "b": 15, "c": 69}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["line_slope_point"] = {
    "course": "alg",
    "title": ("Eğim ve bir noktadan doğru", "Line from slope and a point"),
    "topics": ["slope", "point-slope", "point slope", "slope-intercept", "slope intercept",
               "linear function", "equation of a line", "lines", "graphing lines", "functions and graphing",
               "eğim", "doğru denklemi", "doğrunun denklemi", "nokta eğim"],
    "code": r'''
import numpy as np
from fractions import Fraction


def _f(v):
    v = Fraction(v).limit_denominator(1000)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _eq(m, b):
    if m == 0:
        return f"y = {_f(b)}"
    ms = "" if m == 1 else ("-" if m == -1 else _f(m))
    if b == 0:
        return f"y = {ms}x"
    return f"y = {ms}x {'+' if b > 0 else '-'} {_f(abs(b))}"


def solve(P):
    m = Fraction(P["mn"], P["md"])
    x1, y1 = Fraction(P["x1"]), Fraction(P["y1"])
    b = y1 - m * x1
    xs = f"x - {_f(x1)}" if x1 >= 0 else f"x + {_f(-x1)}"
    ys = f"y - {_f(y1)}" if y1 >= 0 else f"y + {_f(-y1)}"
    steps = [
        (f"Verilen: m = {_f(m)}, nokta ({_f(x1)}, {_f(y1)})", f"Given: m = {_f(m)}, point ({_f(x1)}, {_f(y1)})"),
        ("Nokta-eğim formu: y − y₁ = m(x − x₁)", "Point-slope form: y − y₁ = m(x − x₁)"),
        (f"Yerine koy: {ys} = {_f(m)}({xs})", f"Substitute: {ys} = {_f(m)}({xs})"),
        (f"b = y₁ − m·x₁ = {_f(y1)} − ({_f(m)})·({_f(x1)}) = {_f(b)}",
         f"b = y₁ − m·x₁ = {_f(y1)} − ({_f(m)})·({_f(x1)}) = {_f(b)}"),
        (f"Eğim-kesen formu: {_eq(m, b)}", f"Slope-intercept form: {_eq(m, b)}"),
        (f"Eğim {_f(m)}: sağa {P['md']} birim gidince {abs(P['mn'])} birim "
         f"{'yukarı' if P['mn'] > 0 else 'aşağı'}",
         f"Slope {_f(m)}: {P['md']} units right, {abs(P['mn'])} units {'up' if P['mn'] > 0 else 'down'}"),
    ]
    return {"answer": f"{ys} = {_f(m)}({xs})  ⇔  {_eq(m, b)}", "steps": steps,
            "fmt": {"m": _f(m), "point": f"({_f(x1)}, {_f(y1)})"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    mn, md, x1, y1 = P["mn"], P["md"], P["x1"], P["y1"]
    m = mn / md
    b = y1 - m * x1
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    R = max(8, abs(x1) + abs(md) + 3, abs(y1) + abs(mn) + 3)
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    p1, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=5)
    p2, = ax.plot([], [], "o", ms=9, color="#7C3AED", zorder=5)
    run, = ax.plot([], [], color="#E07B39", lw=3)
    rise, = ax.plot([], [], color="#16A34A", lw=3)
    ln, = ax.plot([], [], color="#2563EB", lw=2.4)
    bdot, = ax.plot([], [], "s", ms=9, color="#2563EB", zorder=6)
    t_run = ax.text(0, 0, "", color="#E07B39", fontsize=11, fontweight="bold", ha="center")
    t_rise = ax.text(0, 0, "", color="#16A34A", fontsize=11, fontweight="bold")
    t_p1 = ax.text(0, 0, "", color="#DC2626", fontsize=11, ha="right")
    t_b = ax.text(0, 0, "", color="#2563EB", fontsize=11)
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=12,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    ax.set_title((f"m = {mn}/{md}, nokta ({x1}, {y1})" if tr else f"m = {mn}/{md}, point ({x1}, {y1})"),
                 fontsize=12)
    xs = np.linspace(-R, R, 200)
    N = 130

    def update(i):
        if i >= 0:
            p1.set_data([x1], [y1])
            t_p1.set_position((x1 - 0.4, y1 + 0.5))
            t_p1.set_text(f"({x1}, {y1})")
        pr = min(1.0, max(0.0, (i - 15) / 20))
        run.set_data([x1, x1 + md * pr], [y1, y1])
        t_run.set_text((f"sağa {md}" if tr else f"run {md}") if pr > 0.99 else "")
        t_run.set_position((x1 + md / 2, y1 - 1.1 if mn > 0 else y1 + 0.5))
        pu = min(1.0, max(0.0, (i - 38) / 20))
        rise.set_data([x1 + md, x1 + md], [y1, y1 + mn * pu])
        t_rise.set_text(((f"yukarı {mn}" if mn > 0 else f"aşağı {-mn}") if tr else
                         (f"rise {mn}")) if pu > 0.99 else "")
        t_rise.set_position((x1 + md + 0.3, y1 + mn / 2))
        if i >= 58:
            p2.set_data([x1 + md], [y1 + mn])
        else:
            p2.set_data([], [])
        pl = min(1.0, max(0.0, (i - 62) / 30))
        if pl > 0:
            half = R * 1.5 * pl
            lx = np.array([x1 - half, x1 + half])
            ln.set_data(lx, y1 + m * (lx - x1))
        else:
            ln.set_data([], [])
        if i >= 95:
            bdot.set_data([0], [b])
            t_b.set_position((0.4, b + 0.4))
            t_b.set_text(f"b = {_f(b)}")
        else:
            bdot.set_data([], [])
            t_b.set_text("")
        if i < 15:
            info.set_text("1) Noktayı işaretle" if tr else "1) Plot the point")
        elif i < 58:
            info.set_text((f"2) Eğim üçgeni: m = yükselme / ilerleme = {mn}/{md}") if tr else
                          (f"2) Slope triangle: m = rise / run = {mn}/{md}"))
        elif i < 95:
            info.set_text("3) İki noktadan doğruyu çiz" if tr else "3) Draw the line through both points")
        else:
            info.set_text((f"4) {_eq(Fraction(mn, md), Fraction(y1) - Fraction(mn, md) * x1)}"))
        return []

    return N, update


def vary(P, rnd):
    md = rnd.choice([1, 2, 3, 4])
    mn = rnd.choice([v for v in range(-4, 5) if v != 0])
    return {"mn": mn, "md": md, "x1": rnd.randint(-4, 4), "y1": rnd.randint(-4, 4)}
''',
}
EXAMPLES += [
    {"id": "alg-slope-1", "kind": "line_slope_point",
     "title": ("Eğim-kesen formu", "Slope-intercept form"),
     "q": ("Eğimi {m} olan ve {point} noktasından geçen doğrunun denklemini bul.",
           "Find the equation of the line with slope {m} passing through {point}."),
     "P": {"mn": 2, "md": 3, "x1": 0, "y1": -1}},
    {"id": "alg-slope-2", "kind": "line_slope_point",
     "title": ("Nokta-eğim formu", "Point-slope form"),
     "q": ("m = {m} ve {point} noktası veriliyor. Doğruyu nokta-eğim ve eğim-kesen formunda yaz.",
           "Given m = {m} and the point {point}, write the line in point-slope and slope-intercept form."),
     "P": {"mn": -1, "md": 4, "x1": -4, "y1": 3}},
    {"id": "alg-slope-3", "kind": "line_slope_point",
     "title": ("Negatif tam sayı eğim", "Negative integer slope"),
     "q": ("{point} noktasından geçen ve eğimi {m} olan doğrunun y-kesenini bul.",
           "Find the y-intercept of the line through {point} with slope {m}."),
     "P": {"mn": -3, "md": 1, "x1": 2, "y1": 1}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["line_two_points"] = {
    "course": "alg",
    "title": ("İki noktadan geçen doğru", "Line through two points"),
    "topics": ["two points", "slope formula", "slope", "rate of change", "equation of a line",
               "iki nokta", "eğim formülü", "değişim oranı"],
    "code": r'''
import numpy as np
from fractions import Fraction


def _f(v):
    v = Fraction(v).limit_denominator(1000)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _eq(m, b):
    if m == 0:
        return f"y = {_f(b)}"
    ms = "" if m == 1 else ("-" if m == -1 else _f(m))
    if b == 0:
        return f"y = {ms}x"
    return f"y = {ms}x {'+' if b > 0 else '-'} {_f(abs(b))}"


def solve(P):
    x1, y1, x2, y2 = (Fraction(P[k]) for k in ("x1", "y1", "x2", "y2"))
    if x1 == x2:
        return {"answer": f"x = {_f(x1)}",
                "steps": [("x₁ = x₂ olduğundan doğru dikeydir; eğim tanımsız.",
                           "x₁ = x₂, so the line is vertical; the slope is undefined."),
                          (f"Denklem: x = {_f(x1)}", f"Equation: x = {_f(x1)}")],
                "fmt": {"A": f"({_f(x1)}, {_f(y1)})", "B": f"({_f(x2)}, {_f(y2)})"}}
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    steps = [
        (f"A({_f(x1)}, {_f(y1)}), B({_f(x2)}, {_f(y2)})", f"A({_f(x1)}, {_f(y1)}), B({_f(x2)}, {_f(y2)})"),
        (f"Eğim: m = (y₂ − y₁)/(x₂ − x₁) = ({_f(y2)} − {_f(y1)})/({_f(x2)} − {_f(x1)}) = {_f(y2 - y1)}/{_f(x2 - x1)} = {_f(m)}",
         f"Slope: m = (y₂ − y₁)/(x₂ − x₁) = ({_f(y2)} − {_f(y1)})/({_f(x2)} − {_f(x1)}) = {_f(y2 - y1)}/{_f(x2 - x1)} = {_f(m)}"),
        (f"b = y₁ − m·x₁ = {_f(y1)} − ({_f(m)})({_f(x1)}) = {_f(b)}",
         f"b = y₁ − m·x₁ = {_f(y1)} − ({_f(m)})({_f(x1)}) = {_f(b)}"),
        (f"Denklem: {_eq(m, b)}", f"Equation: {_eq(m, b)}"),
    ]
    return {"answer": _eq(m, b), "steps": steps,
            "fmt": {"A": f"({_f(x1)}, {_f(y1)})", "B": f"({_f(x2)}, {_f(y2)})"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    x1, y1, x2, y2 = P["x1"], P["y1"], P["x2"], P["y2"]
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    R = max(8, abs(x1) + 2, abs(x2) + 2, abs(y1) + 2, abs(y2) + 2)
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    pa, = ax.plot([], [], "o", ms=10, color="#DC2626", zorder=5)
    pb, = ax.plot([], [], "o", ms=10, color="#7C3AED", zorder=5)
    dx, = ax.plot([], [], color="#E07B39", lw=3)
    dy, = ax.plot([], [], color="#16A34A", lw=3)
    ln, = ax.plot([], [], color="#2563EB", lw=2.4)
    ta = ax.text(x1 + 0.3, y1 + 0.4, "", color="#DC2626", fontsize=11)
    tb = ax.text(x2 + 0.3, y2 + 0.4, "", color="#7C3AED", fontsize=11)
    tdx = ax.text((x1 + x2) / 2, y1 - 0.9, "", color="#E07B39", fontsize=11, ha="center")
    tdy = ax.text(x2 + 0.3, (y1 + y2) / 2, "", color="#16A34A", fontsize=11)
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=12,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    sol = solve(P)
    N = 120

    def update(i):
        pa.set_data([x1], [y1]) if i >= 0 else None
        ta.set_text(f"A({x1}, {y1})")
        if i >= 10:
            pb.set_data([x2], [y2])
            tb.set_text(f"B({x2}, {y2})")
        else:
            pb.set_data([], [])
            tb.set_text("")
        p = min(1.0, max(0.0, (i - 22) / 20))
        dx.set_data([x1, x1 + (x2 - x1) * p], [y1, y1])
        tdx.set_text(f"Δx = {x2 - x1}" if p > 0.99 else "")
        q = min(1.0, max(0.0, (i - 45) / 20))
        dy.set_data([x2, x2], [y1, y1 + (y2 - y1) * q])
        tdy.set_text(f"Δy = {y2 - y1}" if q > 0.99 else "")
        r = min(1.0, max(0.0, (i - 70) / 25))
        if r > 0:
            if x1 == x2:
                ln.set_data([x1, x1], [-R * r, R * r])
            else:
                mm = (y2 - y1) / (x2 - x1)
                lx = np.array([x1 - 2 * R * r, x1 + 2 * R * r])
                ln.set_data(lx, y1 + mm * (lx - x1))
        else:
            ln.set_data([], [])
        if i < 22:
            info.set_text("1) Noktaları işaretle" if tr else "1) Plot both points")
        elif i < 70:
            info.set_text("2) m = Δy / Δx" if tr else "2) m = Δy / Δx")
        else:
            info.set_text("3) " + sol["answer"])
        return []

    return N, update


def vary(P, rnd):
    while True:
        x1, x2 = rnd.randint(-6, 5), rnd.randint(-6, 6)
        y1, y2 = rnd.randint(-6, 6), rnd.randint(-6, 6)
        if x1 != x2 and (x1, y1) != (x2, y2):
            return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
''',
}
EXAMPLES += [
    {"id": "alg-2pt-1", "kind": "line_two_points",
     "title": ("İki noktadan eğim", "Slope from two points"),
     "q": ("{A} ve {B} noktalarından geçen doğrunun eğimini ve denklemini bul.",
           "Find the slope and the equation of the line through {A} and {B}."),
     "P": {"x1": -3, "y1": -1, "x2": 3, "y2": 3}},
    {"id": "alg-2pt-2", "kind": "line_two_points",
     "title": ("Azalan doğru", "Decreasing line"),
     "q": ("{A} ve {B} noktalarını birleştiren doğrunun denklemi nedir?",
           "What is the equation of the line joining {A} and {B}?"),
     "P": {"x1": -2, "y1": 5, "x2": 4, "y2": -4}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["system_2x2"] = {
    "course": "alg",
    "title": ("İki bilinmeyenli denklem sistemi", "System of two linear equations"),
    "topics": ["system", "systems of equations", "simultaneous", "elimination", "substitution",
               "intersection of lines", "denklem sistemi", "yok etme", "yerine koyma", "ortak çözüm"],
    "code": r'''
import numpy as np
from fractions import Fraction


def _f(v):
    v = Fraction(v).limit_denominator(1000)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _side(a, b):
    def term(c, v, first):
        if c == 0:
            return ""
        mag = "" if abs(c) == 1 else _f(abs(c))
        if first:
            return ("-" if c < 0 else "") + mag + v
        return (" - " if c < 0 else " + ") + mag + v
    s = term(a, "x", True)
    s += term(b, "y", s == "")
    return s or "0"


def solve(P):
    a1, b1, c1, a2, b2, c2 = (Fraction(P[k]) for k in ("a1", "b1", "c1", "a2", "b2", "c2"))
    det = a1 * b2 - a2 * b1
    e1 = f"{_side(a1, b1)} = {_f(c1)}"
    e2 = f"{_side(a2, b2)} = {_f(c2)}"
    fmt = {"eq1": e1, "eq2": e2}
    if det == 0:
        same = (a1 * c2 == a2 * c1) and (b1 * c2 == b2 * c1)
        msg = (("Doğrular çakışık: sonsuz çözüm", "Same line: infinitely many solutions") if same
               else ("Doğrular paralel: çözüm yok", "Parallel lines: no solution"))
        return {"answer": msg, "steps": [(f"Determinant a₁b₂ − a₂b₁ = 0", "Determinant a₁b₂ − a₂b₁ = 0"), msg],
                "fmt": fmt}
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    steps = [
        (f"(1) {e1}    (2) {e2}", f"(1) {e1}    (2) {e2}"),
        (f"y'yi yok etmek için (1)'i {_f(b2)}, (2)'yi {_f(b1)} ile çarp ve çıkar",
         f"To eliminate y multiply (1) by {_f(b2)}, (2) by {_f(b1)} and subtract"),
        (f"({_f(a1 * b2)} − {_f(a2 * b1)})x = {_f(c1 * b2)} − {_f(c2 * b1)}  ⇒  {_f(det)}x = {_f(c1 * b2 - c2 * b1)}",
         f"({_f(a1 * b2)} − {_f(a2 * b1)})x = {_f(c1 * b2)} − {_f(c2 * b1)}  ⇒  {_f(det)}x = {_f(c1 * b2 - c2 * b1)}"),
        (f"x = {_f(x)}", f"x = {_f(x)}"),
        (f"x'i bir denklemde yerine koy ⇒ y = {_f(y)}", f"Substitute x back ⇒ y = {_f(y)}"),
        (f"Kesişim noktası: ({_f(x)}, {_f(y)})", f"Intersection point: ({_f(x)}, {_f(y)})"),
    ]
    return {"answer": f"x = {_f(x)}, y = {_f(y)}", "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a1, b1, c1, a2, b2, c2 = (float(P[k]) for k in ("a1", "b1", "c1", "a2", "b2", "c2"))
    det = a1 * b2 - a2 * b1
    sx = sy = 0.0
    if det != 0:
        sx = (c1 * b2 - c2 * b1) / det
        sy = (a1 * c2 - a2 * c1) / det
    R = max(8.0, abs(sx) + 4, abs(sy) + 4)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.9, bottom=0.09)
    ax.set_xlim(sx - R, sx + R)
    ax.set_ylim(sy - R, sy + R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#6B7280", lw=1)
    ax.axvline(0, color="#6B7280", lw=1)
    sol = solve(P)

    def seg(a, b, c):
        if b != 0:
            xs = np.linspace(sx - R, sx + R, 200)
            return xs, (c - a * xs) / b
        ys = np.linspace(sy - R, sy + R, 200)
        return np.full_like(ys, c / a), ys

    X1, Y1 = seg(a1, b1, c1)
    X2, Y2 = seg(a2, b2, c2)
    l1, = ax.plot([], [], color="#2563EB", lw=2.4, label=sol["fmt"]["eq1"])
    l2, = ax.plot([], [], color="#E07B39", lw=2.4, label=sol["fmt"]["eq2"])
    dot, = ax.plot([], [], "o", color="#DC2626", ms=12, zorder=6)
    ring, = ax.plot([], [], "o", mfc="none", mec="#DC2626", ms=12, zorder=6)
    lab = ax.text(sx + R * 0.05, sy + R * 0.06, "", color="#DC2626", fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=10)
    N = 120

    def update(i):
        p = min(1.0, max(0.0, i / 35))
        m1 = max(2, int(p * len(X1)))
        l1.set_data(X1[:m1], Y1[:m1])
        q = min(1.0, max(0.0, (i - 35) / 35))
        m2 = max(2, int(q * len(X2))) if q > 0 else 0
        l2.set_data(X2[:m2], Y2[:m2])
        if i >= 75 and det != 0:
            dot.set_data([sx], [sy])
            pulse = 12 + 18 * ((i - 75) % 20) / 20
            ring.set_data([sx], [sy])
            ring.set_markersize(pulse)
            lab.set_text(sol["answer"])
        else:
            dot.set_data([], [])
            ring.set_data([], [])
            lab.set_text(sol["answer"] if (i >= 75 and det == 0) else "")
        return []

    ax.set_title("Her doğru bir denklem; kesişim noktası ortak çözümdür" if tr else
                 "Each line is one equation; the crossing point solves both", fontsize=11)
    return N, update


def vary(P, rnd):
    while True:
        x, y = rnd.randint(-5, 5), rnd.randint(-5, 5)
        a1, b1, a2, b2 = (rnd.choice([-3, -2, -1, 1, 2, 3, 4]) for _ in range(4))
        if a1 * b2 - a2 * b1 != 0:
            return {"a1": a1, "b1": b1, "c1": a1 * x + b1 * y, "a2": a2, "b2": b2, "c2": a2 * x + b2 * y}
''',
}
EXAMPLES += [
    {"id": "alg-sys-1", "kind": "system_2x2",
     "title": ("Yok etme yöntemi", "Elimination method"),
     "q": ("Sistemi çöz:  {eq1}  ve  {eq2}", "Solve the system:  {eq1}  and  {eq2}"),
     "P": {"a1": 2, "b1": 3, "c1": 12, "a2": 1, "b2": -1, "c2": 1}},
    {"id": "alg-sys-2", "kind": "system_2x2",
     "title": ("Yerine koyma yöntemi", "Substitution method"),
     "q": ("{eq1} ve {eq2} denklemlerini aynı anda sağlayan (x, y) nedir?",
           "Which (x, y) satisfies both {eq1} and {eq2}?"),
     "P": {"a1": 1, "b1": 1, "c1": 7, "a2": 3, "b2": -2, "c2": 1}},
    {"id": "alg-sys-3", "kind": "system_2x2", "topics": ["word problem", "sözel problem", "mixture"],
     "title": ("Sözel problem: bilet satışı", "Word problem: ticket sales"),
     "q": ("Yetişkin bileti x, öğrenci bileti y TL. {eq1} ve {eq2} bilgisine göre fiyatları bul.",
           "An adult ticket costs x and a student ticket y. Using {eq1} and {eq2}, find both prices."),
     "P": {"a1": 2, "b1": 3, "c1": 130, "a2": 1, "b2": 1, "c2": 50}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["quadratic"] = {
    "course": "alg",
    "title": ("İkinci derece denklem ve parabol", "Quadratic equation and parabola"),
    "topics": ["quadratic", "parabola", "quadratic formula", "discriminant", "factoring",
               "completing the square", "roots", "zeros", "vertex",
               "ikinci derece", "parabol", "diskriminant", "kökler", "çarpanlara ayırma", "tepe noktası"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction


def _f(v):
    v = Fraction(v).limit_denominator(1000)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _poly(a, b, c):
    terms = []
    for coef, pw in ((a, "x²"), (b, "x"), (c, "")):
        if coef == 0:
            continue
        mag = abs(coef)
        body = ("" if (mag == 1 and pw) else _f(mag)) + pw
        terms.append(("-" if coef < 0 else "+", body))
    if not terms:
        return "0"
    out = ("-" if terms[0][0] == "-" else "") + terms[0][1]
    for sgn, body in terms[1:]:
        out += f" {sgn} {body}"
    return out


def _roots(a, b, c):
    D = b * b - 4 * a * c
    if D < 0:
        return D, []
    r = math.sqrt(D)
    return D, sorted({(-b - r) / (2 * a), (-b + r) / (2 * a)})


def solve(P):
    a, b, c = Fraction(P["a"]), Fraction(P["b"]), Fraction(P["c"])
    D = b * b - 4 * a * c
    xv = -b / (2 * a)
    yv = a * xv * xv + b * xv + c
    steps = [
        (f"a = {_f(a)}, b = {_f(b)}, c = {_f(c)}", f"a = {_f(a)}, b = {_f(b)}, c = {_f(c)}"),
        (f"Diskriminant: Δ = b² − 4ac = ({_f(b)})² − 4·({_f(a)})·({_f(c)}) = {_f(D)}",
         f"Discriminant: Δ = b² − 4ac = ({_f(b)})² − 4·({_f(a)})·({_f(c)}) = {_f(D)}"),
    ]
    rD = math.isqrt(int(D.numerator)) if D >= 0 else 0
    exact = D >= 0 and D.denominator == 1 and rD * rD == D.numerator
    if D > 0:
        steps.append(("Δ > 0 ⇒ iki farklı reel kök", "Δ > 0 ⇒ two distinct real roots"))
        if exact:
            r1, r2 = sorted([(-b - rD) / (2 * a), (-b + rD) / (2 * a)])
            steps.append((f"x = (−b ± √Δ) / 2a = ({_f(-b)} ± {rD}) / {_f(2 * a)}",
                           f"x = (−b ± √Δ) / 2a = ({_f(-b)} ± {rD}) / {_f(2 * a)}"))
            ans = f"x₁ = {_f(r1)}, x₂ = {_f(r2)}"
        else:
            _, rs = _roots(float(a), float(b), float(c))
            steps.append((f"x = ({_f(-b)} ± √{_f(D)}) / {_f(2 * a)}", f"x = ({_f(-b)} ± √{_f(D)}) / {_f(2 * a)}"))
            ans = f"x = ({_f(-b)} ± √{_f(D)}) / {_f(2 * a)}  ≈ {rs[0]:.4g}, {rs[1]:.4g}"
    elif D == 0:
        steps.append(("Δ = 0 ⇒ çift (tek) kök", "Δ = 0 ⇒ one repeated root"))
        ans = f"x = {_f(xv)}"
    else:
        steps.append(("Δ < 0 ⇒ reel kök yok (parabol x eksenini kesmez)",
                      "Δ < 0 ⇒ no real roots (the parabola misses the x-axis)"))
        im = math.sqrt(float(-D)) / abs(2 * float(a))
        ans = f"x = {float(xv):.4g} ± {im:.4g}i"
    steps.append((f"Tepe noktası: x = −b/2a = {_f(xv)}, y = {_f(yv)}",
                  f"Vertex: x = −b/2a = {_f(xv)}, y = {_f(yv)}"))
    steps.append((f"Simetri ekseni: x = {_f(xv)};  parabol {'yukarı' if a > 0 else 'aşağı'} açılır",
                  f"Axis of symmetry: x = {_f(xv)};  opens {'up' if a > 0 else 'down'}"))
    return {"answer": ans, "steps": steps, "fmt": {"expr": _poly(a, b, c)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    a, b, c = float(P["a"]), float(P["b"]), float(P["c"])
    D, roots = _roots(a, b, c)
    xv = -b / (2 * a)
    yv = a * xv * xv + b * xv + c
    span = max(4.0, *(abs(r - xv) * 1.5 for r in roots)) if roots else 4.0
    xs = np.linspace(xv - span, xv + span, 300)
    ys = a * xs ** 2 + b * xs + c
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.9, bottom=0.09)
    pad = (ys.max() - ys.min()) * 0.12 + 1
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(min(ys.min(), 0) - pad, max(ys.max(), 0) + pad)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.2)
    ax.axvline(0, color="#9CA3AF", lw=1)
    curve, = ax.plot([], [], color="#2563EB", lw=2.6)
    tracer, = ax.plot([], [], "o", color="#2563EB", ms=8)
    vdot, = ax.plot([], [], "D", color="#7C3AED", ms=9, zorder=5)
    axis, = ax.plot([], [], "--", color="#7C3AED", lw=1.3)
    rdots, = ax.plot([], [], "o", color="#DC2626", ms=11, zorder=6)
    yr = ax.get_ylim()[1] - ax.get_ylim()[0]
    vlab = ax.text(xv, yv - (0.05 if a > 0 else -0.05) * yr, "", color="#7C3AED", fontsize=11,
                   ha="center", va="top" if a > 0 else "bottom")
    rlabs = [ax.text(r, (0.05 if a > 0 else -0.05) * yr, "", color="#DC2626", fontsize=12,
                     fontweight="bold", ha="center", va="bottom" if a > 0 else "top") for r in roots]
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=12,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    sol = solve(P)
    ax.set_title(f"y = {sol['fmt']['expr']}", fontsize=13)
    N = 125

    def update(i):
        p = min(1.0, max(0.0, i / 45))
        m = max(2, int(p * len(xs)))
        curve.set_data(xs[:m], ys[:m])
        tracer.set_data([xs[m - 1]], [ys[m - 1]]) if p < 1 else tracer.set_data([], [])
        if i >= 50:
            vdot.set_data([xv], [yv])
            lim = ax.get_ylim()
            axis.set_data([xv, xv], [lim[0], lim[1]])
            vlab.set_text(f"T({xv:.3g}, {yv:.3g})")
        else:
            vdot.set_data([], [])
            axis.set_data([], [])
            vlab.set_text("")
        if i >= 75:
            rdots.set_data(roots, [0] * len(roots))
            for r, t in zip(roots, rlabs):
                t.set_text(f"x = {r:.3g}")
        else:
            rdots.set_data([], [])
            for t in rlabs:
                t.set_text("")
        if i < 50:
            info.set_text("1) Parabolü çiz" if tr else "1) Draw the parabola")
        elif i < 75:
            info.set_text("2) Tepe noktası ve simetri ekseni" if tr else "2) Vertex and axis of symmetry")
        else:
            info.set_text((f"3) Δ = {D:.4g}  ⇒  " if tr else f"3) Δ = {D:.4g}  ⇒  ") + sol["answer"])
        return []

    return N, update


def vary(P, rnd):
    a = rnd.choice([1, 1, 1, -1, 2])
    r1, r2 = rnd.randint(-6, 5), rnd.randint(-5, 6)
    return {"a": a, "b": -a * (r1 + r2), "c": a * r1 * r2}
''',
}
EXAMPLES += [
    {"id": "alg-quad-1", "kind": "quadratic",
     "title": ("Çarpanlara ayrılan denklem", "Factorable quadratic"),
     "q": ("{expr} = 0 denkleminin köklerini bul.", "Find the roots of {expr} = 0."),
     "P": {"a": 1, "b": -1, "c": -12}},
    {"id": "alg-quad-2", "kind": "quadratic",
     "title": ("Kök formülü", "Quadratic formula"),
     "q": ("Kök formülüyle çöz: {expr} = 0", "Use the quadratic formula: {expr} = 0"),
     "P": {"a": 2, "b": 3, "c": -4}},
    {"id": "alg-quad-3", "kind": "quadratic",
     "title": ("Reel kökü olmayan denklem", "No real roots"),
     "q": ("{expr} = 0 denkleminin diskriminantını hesapla; reel kökü var mı?",
           "Compute the discriminant of {expr} = 0. Are there real roots?"),
     "P": {"a": 1, "b": 2, "c": 5}},
    {"id": "alg-quad-4", "kind": "quadratic", "topics": ["projectile", "word problem", "atış"],
     "title": ("Fırlatılan top", "Thrown ball"),
     "q": ("Bir topun yüksekliği h(t) = {expr} (m). Top ne zaman yere düşer ve en yüksek nokta nedir?",
           "A ball's height is h(t) = {expr} metres. When does it land and what is its peak?"),
     "P": {"a": -5, "b": 20, "c": 25}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["function_graph"] = {
    "course": "alg",
    "title": ("Fonksiyon grafiği", "Graph of a function"),
    "topics": ["function", "graph", "graphing", "intercepts", "domain and range", "zeros",
               "polynomial", "fonksiyon", "grafik", "tanım kümesi", "kesişim"],
    "code": r'''
import numpy as np
import sympy as sp


def _expr(P):
    x = sp.Symbol("x", real=True)
    return x, sp.sympify(P["f"], locals={"x": x})


def _num(f, x):
    g = sp.lambdify(x, f, "numpy")

    def h(v):
        with np.errstate(all="ignore"):
            out = np.asarray(g(v), dtype=complex)
        out = np.where(np.abs(out.imag) < 1e-9, out.real, np.nan).astype(float)
        return np.broadcast_to(out, np.shape(v)).astype(float)
    return h


def _zeros(h, a, b):
    xs = np.linspace(a, b, 4001)
    ys = h(xs)
    out = []
    for k in range(len(xs) - 1):
        y0, y1 = ys[k], ys[k + 1]
        if not (np.isfinite(y0) and np.isfinite(y1)):
            continue
        if y0 == 0:
            out.append(xs[k])
        elif y0 * y1 < 0 and abs(y0 - y1) < 50:
            lo, hi = xs[k], xs[k + 1]
            for _ in range(50):
                mid = (lo + hi) / 2
                if h(np.array([lo]))[0] * h(np.array([mid]))[0] <= 0:
                    hi = mid
                else:
                    lo = mid
            out.append((lo + hi) / 2)
    res = []
    for z in out:
        if not res or abs(z - res[-1]) > 1e-6:
            res.append(z)
    return res


def solve(P):
    x, f = _expr(P)
    h = _num(f, x)
    a, b = float(P.get("xmin", -6)), float(P.get("xmax", 6))
    zs = _zeros(h, a, b)
    y0 = h(np.array([0.0]))[0]
    steps = [(f"f(x) = {sp.sstr(f)}", f"f(x) = {sp.sstr(f)}")]
    if np.isfinite(y0):
        steps.append((f"y-kesişimi: f(0) = {y0:.4g}", f"y-intercept: f(0) = {y0:.4g}"))
    else:
        steps.append(("x = 0 tanım kümesinde değil (y-kesişimi yok)", "x = 0 is not in the domain (no y-intercept)"))
    if zs:
        z = ", ".join(f"{v:.4g}" for v in zs)
        steps.append((f"Sıfırlar (f(x) = 0) [{a:g}, {b:g}] aralığında: x ≈ {z}",
                      f"Zeros (f(x) = 0) on [{a:g}, {b:g}]: x ≈ {z}"))
    else:
        steps.append((f"[{a:g}, {b:g}] aralığında sıfır yok", f"No zeros on [{a:g}, {b:g}]"))
    d = sp.diff(f, x)
    steps.append((f"f'(x) = {sp.sstr(sp.simplify(d))}  (artan/azalan bölgeler için)",
                   f"f'(x) = {sp.sstr(sp.simplify(d))}  (where f rises or falls)"))
    crit = _zeros(_num(d, x), a, b)
    for c in crit[:4]:
        yc = h(np.array([c]))[0]
        steps.append((f"Kritik nokta: x ≈ {c:.4g}, f ≈ {yc:.4g}", f"Critical point: x ≈ {c:.4g}, f ≈ {yc:.4g}"))
    ans = ("sıfırlar: " if P.get("lang", "tr") == "tr" else "zeros: ") + (
        ", ".join(f"{v:.4g}" for v in zs) if zs else "—")
    return {"answer": ans, "steps": steps, "fmt": {"fx": sp.sstr(f)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    x, f = _expr(P)
    h = _num(f, x)
    a, b = float(P.get("xmin", -6)), float(P.get("xmax", 6))
    xs = np.linspace(a, b, 600)
    ys = h(xs)
    jump = np.abs(np.diff(ys, prepend=ys[0]))
    fin = ys[np.isfinite(ys)]
    if len(fin) == 0:
        fin = np.array([-1.0, 1.0])
    lo, hi = np.percentile(fin, 2), np.percentile(fin, 98)
    pad = (hi - lo) * 0.15 + 1
    ys = np.where(jump > (hi - lo + 1) * 2, np.nan, ys)
    zs = _zeros(h, a, b)
    crit = _zeros(_num(sp.diff(f, x), x), a, b)[:6]
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.9, bottom=0.09)
    ax.set_xlim(a, b)
    ax.set_ylim(min(lo, 0) - pad, max(hi, 0) + pad)
    ax.grid(alpha=0.3)
    ax.axhline(0, color="#374151", lw=1.1)
    ax.axvline(0, color="#374151", lw=1.1)
    curve, = ax.plot([], [], color="#2563EB", lw=2.5)
    pt, = ax.plot([], [], "o", color="#E07B39", ms=9, zorder=6)
    coord = ax.text(0.98, 0.03, "", transform=ax.transAxes, ha="right", fontsize=11,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    zdots, = ax.plot([], [], "o", color="#DC2626", ms=10, zorder=7)
    cdots, = ax.plot([], [], "^", color="#16A34A", ms=10, zorder=7)
    ydot, = ax.plot([], [], "s", color="#7C3AED", ms=9, zorder=7)
    y0 = h(np.array([0.0]))[0]
    ax.set_title(f"f(x) = {sp.sstr(f)}", fontsize=13)
    N = 120

    def update(i):
        p = min(1.0, i / 70)
        m = max(2, int(p * len(xs)))
        curve.set_data(xs[:m], ys[:m])
        if p < 1:
            pt.set_data([xs[m - 1]], [ys[m - 1]])
            yy = ys[m - 1]
            coord.set_text(f"x = {xs[m - 1]:.2f},  f(x) = {yy:.3f}" if np.isfinite(yy)
                           else f"x = {xs[m - 1]:.2f},  f(x) " + ("tanımsız" if tr else "undefined"))
        else:
            pt.set_data([], [])
            coord.set_text(("kırmızı: sıfırlar · yeşil: kritik noktalar · mor: y-kesişimi") if tr else
                           ("red: zeros · green: critical points · purple: y-intercept"))
        if i >= 75:
            zdots.set_data(zs, [0] * len(zs))
        else:
            zdots.set_data([], [])
        if i >= 90:
            cdots.set_data(crit, list(h(np.array(crit, dtype=float))) if crit else [])
            ydot.set_data([0], [y0]) if (np.isfinite(y0) and a <= 0 <= b) else ydot.set_data([], [])
        else:
            cdots.set_data([], [])
            ydot.set_data([], [])
        return []

    return N, update


def vary(P, rnd):
    r1, r2, r3 = rnd.sample(range(-4, 5), 3)
    k = rnd.choice([1, -1])
    form = rnd.choice(["cubic", "quad"])
    if form == "cubic":
        f = f"{k}*(x - ({r1}))*(x - ({r2}))*(x - ({r3}))/4"
    else:
        f = f"{k}*(x - ({r1}))*(x - ({r2}))"
    return {"f": str(sp.expand(sp.sympify(f))), "xmin": -6, "xmax": 6}
''',
}
EXAMPLES += [
    {"id": "alg-func-1", "kind": "function_graph",
     "title": ("Kübik fonksiyonun grafiği", "Graphing a cubic"),
     "q": ("f(x) = {fx} fonksiyonunun grafiğini çiz; sıfırlarını ve y-kesişimini bul.",
           "Graph f(x) = {fx}; find its zeros and y-intercept."),
     "P": {"f": "x**3 - 4*x", "xmin": -3.5, "xmax": 3.5}},
    {"id": "alg-func-2", "kind": "function_graph", "topics": ["rational", "rasyonel"],
     "title": ("Rasyonel fonksiyon", "A rational function"),
     "q": ("f(x) = {fx} için tanım kümesini, sıfırları ve grafiği incele.",
           "For f(x) = {fx}, study the domain, zeros and graph."),
     "P": {"f": "(x**2 - 1)/(x - 2)", "xmin": -5, "xmax": 6}},
    {"id": "alg-func-3", "kind": "function_graph", "topics": ["square root", "radical", "karekök"],
     "title": ("Köklü fonksiyon", "Square-root function"),
     "q": ("f(x) = {fx} fonksiyonunun tanım kümesi ve grafiği nedir?",
           "What are the domain and graph of f(x) = {fx}?"),
     "P": {"f": "sqrt(x + 4) - 1", "xmin": -5, "xmax": 8}},
]
