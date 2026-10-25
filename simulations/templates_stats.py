# -*- coding: utf-8 -*-
"""Olasılık ve İstatistik simülasyonları (2/2 — İSTATİSTİK): betimsel istatistik,
normal dağılım altındaki alan, merkezi limit teoremi, doğrusal regresyon, güven
aralığı, z-hipotez testi, ki-kare testleri ve örneklem oranının dağılımı.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Tüm rastgelelik build()
içinde np.random.default_rng(P.get("seed", 0)) ile ÖNCEDEN üretilir; böylece
kareler deterministiktir ve kareye atlama güvenlidir. scipy kullanılmaz:
normal dağılım math.erf ile, ters normal ikiye bölme ile, ki-kare dağılımı
düzenlenmiş eksik gama fonksiyonu ile hesaplanır.

Sorular kitaplardan KOPYALANMAZ: kendi ifademizle yazılmış, kendi
sayılarımızla kurulmuş tipik ders örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["descriptive_stats"] = {
    "course": "prob",
    "title": ("Betimsel istatistik: merkez ve yayılım", "Descriptive statistics: center and spread"),
    "topics": ["descriptive statistics", "measures of center", "measures of central tendency",
               "measures of spread", "measures of variation", "mean median mode", "median",
               "quartile", "interquartile range", "iqr", "five number summary", "five-number summary",
               "box plot", "boxplot", "box-and-whisker", "box and whisker", "dot plot",
               "standard deviation", "variance", "outlier",
               "betimsel istatistik", "tanımlayıcı istatistik", "merkezi eğilim", "yayılım ölçüleri",
               "aritmetik ortalama", "medyan", "ortanca", "çeyrekler", "çeyrekler açıklığı",
               "kutu grafiği", "standart sapma", "varyans", "aykırı değer"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle, Polygon
from matplotlib.collections import LineCollection


def _d(v, k=3):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _eq(v):
    v = Fraction(v)
    return ("= " if (v * 1000).denominator == 1 else "≈ ") + _d(v)


def _root(v):
    r = math.sqrt(float(v))
    if abs(r * 1000 - round(r * 1000)) < 1e-6:
        return "= " + _d(r)
    return "≈ " + f"{r:.3f}"


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _fr(v):
    return Fraction(str(v)) if isinstance(v, float) else Fraction(v)


def _median(xs):
    m = len(xs)
    if m == 0:
        return Fraction(0)
    if m % 2:
        return xs[m // 2]
    return (xs[m // 2 - 1] + xs[m // 2]) / 2


def _stats(P):
    xs = sorted(_fr(v) for v in P["data"])
    n = len(xs)
    S = sum(xs)
    mean = S / n
    lower, upper = xs[: n // 2], xs[(n + 1) // 2:]
    q1 = _median(lower) if lower else xs[0]
    q3 = _median(upper) if upper else xs[-1]
    iqr = q3 - q1
    counts = {}
    for v in xs:
        counts[v] = counts.get(v, 0) + 1
    top = max(counts.values())
    modes = sorted(v for v, c in counts.items() if c == top) if top > 1 else []
    lof = q1 - Fraction(3, 2) * iqr
    hif = q3 + Fraction(3, 2) * iqr
    inside = [v for v in xs if lof <= v <= hif]
    ss = sum((v - mean) ** 2 for v in xs)
    vp = ss / n
    vs = ss / (n - 1) if n > 1 else Fraction(0)
    return {"xs": xs, "n": n, "S": S, "mean": mean, "med": _median(xs), "lower": lower,
            "upper": upper, "q1": q1, "q3": q3, "iqr": iqr, "modes": modes, "top": top,
            "lof": lof, "hif": hif, "out": [v for v in xs if v < lof or v > hif],
            "wlo": min(inside), "whi": max(inside), "ss": ss, "vp": vp, "vs": vs,
            "sp": math.sqrt(vp), "ssd": math.sqrt(vs)}


def _mode_txt(st, tr):
    ms = st["modes"]
    if not ms:
        return "mod yok" if tr else "no mode"
    return ("mod = " if tr else "mode = ") + ", ".join(_d(v) for v in ms)


def solve(P):
    st = _stats(P)
    xs, n = st["xs"], st["n"]
    L = ", ".join(_d(v) for v in xs)
    steps = [(f"Veriyi küçükten büyüğe sırala (n = {n}): {L}",
              f"Sort the data (n = {n}): {L}"),
             (f"Ortalama: x̄ = Σx / n = {_d(st['S'])}/{n} {_eq(st['mean'])}",
              f"Mean: x̄ = Σx / n = {_d(st['S'])}/{n} {_eq(st['mean'])}")]
    if n % 2:
        k = (n + 1) // 2
        steps.append((f"Medyan: n tek ⇒ ortadaki ({k}. sıradaki) değer = {_d(st['med'])}",
                      f"Median: n is odd ⇒ the middle value (position {k}) = {_d(st['med'])}"))
    else:
        k = n // 2
        steps.append((f"Medyan: n çift ⇒ ({k}. ve {k + 1}. değerin ortalaması) = "
                      f"({_d(xs[k - 1])} + {_d(xs[k])})/2 = {_d(st['med'])}",
                      f"Median: n is even ⇒ average of values {k} and {k + 1} = "
                      f"({_d(xs[k - 1])} + {_d(xs[k])})/2 = {_d(st['med'])}"))
    ms = st["modes"]
    if not ms:
        steps.append(("Mod: her değer bir kez geçiyor ⇒ mod yok",
                      "Mode: every value occurs once ⇒ no mode"))
    elif len(ms) == 1:
        steps.append((f"Mod: en sık tekrarlanan değer {_d(ms[0])} ({st['top']} kez)",
                      f"Mode: the most frequent value is {_d(ms[0])} ({st['top']} times)"))
    else:
        steps.append((f"Mod: {' ve '.join(_d(v) for v in ms)} (her biri {st['top']} kez) ⇒ çok modlu veri",
                      f"Modes: {' and '.join(_d(v) for v in ms)} ({st['top']} times each) ⇒ multimodal data"))
    lo, hi = xs[0], xs[-1]
    steps.append((f"Açıklık = en büyük − en küçük = {_d(hi)} − {_d(lo)} = {_d(hi - lo)}",
                  f"Range = max − min = {_d(hi)} − {_d(lo)} = {_d(hi - lo)}"))
    lw = ", ".join(_d(v) for v in st["lower"])
    up = ", ".join(_d(v) for v in st["upper"])
    steps.append((f"Q₁ = alt yarının medyanı ({lw}) = {_d(st['q1'])};  Q₃ = üst yarının medyanı ({up}) = {_d(st['q3'])}",
                  f"Q₁ = median of the lower half ({lw}) = {_d(st['q1'])};  Q₃ = median of the upper half ({up}) = {_d(st['q3'])}"))
    steps.append((f"Çeyrekler açıklığı: IQR = Q₃ − Q₁ = {_d(st['q3'])} − {_d(st['q1'])} = {_d(st['iqr'])}",
                  f"Interquartile range: IQR = Q₃ − Q₁ = {_d(st['q3'])} − {_d(st['q1'])} = {_d(st['iqr'])}"))
    ol = ", ".join(_d(v) for v in st["out"])
    steps.append((f"Aykırı değer sınırları: Q₁ − 1.5·IQR = {_d(st['lof'])},  Q₃ + 1.5·IQR = {_d(st['hif'])}  ⇒  "
                  + (f"aykırı değer: {ol}" if ol else "aykırı değer yok"),
                  f"Outlier fences: Q₁ − 1.5·IQR = {_d(st['lof'])},  Q₃ + 1.5·IQR = {_d(st['hif'])}  ⇒  "
                  + (f"outlier(s): {ol}" if ol else "no outliers")))
    steps.append((f"Beş sayı özeti: min {_d(lo)}, Q₁ {_d(st['q1'])}, medyan {_d(st['med'])}, Q₃ {_d(st['q3'])}, maks {_d(hi)}",
                  f"Five-number summary: min {_d(lo)}, Q₁ {_d(st['q1'])}, median {_d(st['med'])}, Q₃ {_d(st['q3'])}, max {_d(hi)}"))
    mstr = _d(st["mean"])
    terms = [f"({_d(v)} − {mstr})²" for v in xs]
    if n > 6:
        terms = terms[:2] + ["…"] + terms[-1:]
    sm = " + ".join(terms)
    steps.append((f"Sapma kareleri toplamı: Σ(x − x̄)² = {sm} {_eq(st['ss'])}",
                  f"Sum of squared deviations: Σ(x − x̄)² = {sm} {_eq(st['ss'])}"))
    steps.append((f"Kitle varyansı σ² = Σ(x − x̄)²/n = {_d(st['ss'])}/{n} {_eq(st['vp'])}  ⇒  σ = √σ² {_root(st['vp'])}",
                  f"Population variance σ² = Σ(x − x̄)²/n = {_d(st['ss'])}/{n} {_eq(st['vp'])}  ⇒  σ = √σ² {_root(st['vp'])}"))
    steps.append((f"Örneklem varyansı s² = Σ(x − x̄)²/(n − 1) = {_d(st['ss'])}/{n - 1} {_eq(st['vs'])}  ⇒  s {_root(st['vs'])}",
                  f"Sample variance s² = Σ(x − x̄)²/(n − 1) = {_d(st['ss'])}/{n - 1} {_eq(st['vs'])}  ⇒  s {_root(st['vs'])}"))
    ans_tr = (f"x̄ {_eq(st['mean'])}, medyan = {_d(st['med'])}, {_mode_txt(st, True)}, açıklık = {_d(hi - lo)}, "
              f"IQR = {_d(st['iqr'])}, σ {_root(st['vp'])}, s {_root(st['vs'])}")
    ans_en = (f"x̄ {_eq(st['mean'])}, median = {_d(st['med'])}, {_mode_txt(st, False)}, range = {_d(hi - lo)}, "
              f"IQR = {_d(st['iqr'])}, σ {_root(st['vp'])}, s {_root(st['vs'])}")
    return {"answer": (ans_tr, ans_en), "steps": steps, "fmt": {"n": str(n)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    st = _stats(P)
    raw = [float(v) for v in P["data"]]
    n = len(raw)
    xs = [float(v) for v in st["xs"]]
    order = sorted(range(n), key=lambda k: (raw[k], k))
    rank = [0] * n
    for r, k in enumerate(order):
        rank[k] = r
    lev = [sum(1 for q in range(r) if xs[q] == xs[r]) for r in range(n)]
    top = max(lev) + 1.0
    mean, med = float(st["mean"]), float(st["med"])
    q1, q3 = float(st["q1"]), float(st["q3"])
    wlo, whi = float(st["wlo"]), float(st["whi"])
    sp = st["sp"]
    lo, hi = xs[0], xs[-1]
    span = max(hi - lo, 1.0)
    xl = min(lo - 0.1 * span, mean - sp - 0.04 * span)
    xr = max(hi + 0.1 * span, mean + sp + 0.04 * span)
    half = (xr - xl) / 2.0
    medr = {(n - 1) // 2} if n % 2 else {n // 2 - 1, n // 2}
    modev = set(float(v) for v in st["modes"])
    outv = [float(v) for v in st["out"]]

    gs = fig.add_gridspec(3, 2, width_ratios=[2.45, 1], height_ratios=[0.7, 3.1, 1.15],
                          left=0.035, right=0.985, top=0.95, bottom=0.075, wspace=0.06, hspace=0.25)
    ca = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[1, 0])
    bx = fig.add_subplot(gs[2, 0], sharex=ax)
    tp = fig.add_subplot(gs[:, 1])
    ca.axis("off")
    ca.set_xlim(-0.7, n - 0.3)
    ca.set_ylim(-1.3, 1.3)
    tp.axis("off")
    tp.set_xlim(0, 1)
    tp.set_ylim(0, 1)
    yb, yt = -1.7, top + 4.0
    ax.set_xlim(xl, xr)
    ax.set_ylim(yb, yt)
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.25)
    ax.tick_params(labelbottom=False)
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
        bx.spines[s].set_visible(False)
    bx.set_ylim(-1.3, 1.25)
    bx.set_yticks([])
    bx.grid(axis="x", alpha=0.25)
    fw_in, fh_in = fig.get_size_inches()
    pos = ax.get_position()
    unit_in = pos.height * fh_in / (yt - yb)
    xin = pos.width * fw_in / (xr - xl)
    gaps = [b - a for a, b in zip(xs, xs[1:]) if b > a]
    diam = min(0.78 * unit_in, (min(gaps) if gaps else span) * xin)
    dsz = min(260.0, max(25.0, (diam * 72) ** 2))
    H6 = top + 1.6 - 0.55
    gap6 = min(0.8, H6 / max(1, n - 1))
    row6 = [0.55 + r * gap6 for r in range(n)]
    d6 = min(diam, 0.85 * gap6 * unit_in)
    dsz6 = max(12.0, (d6 * 72) ** 2)
    off6 = 0.75 * d6 / xin

    fs = 10 if n <= 10 else (9 if n <= 13 else 7.5)
    cards = [ca.text(k, 0, _d(raw[k]), ha="center", va="center", fontsize=fs, zorder=3,
                     bbox=dict(boxstyle="round,pad=0.28", fc="#EFF6FF", ec="#93C5FD"))
             for k in range(n)]
    beam, = ax.plot([], [], color="#374151", lw=3, solid_capstyle="round", zorder=2)
    fwid, fhgt = 0.022 * (xr - xl), 1.15
    ful = Polygon([[0, 0], [0, 0], [0, 0]], closed=True, fc="#DC2626", ec="#991B1B", zorder=3)
    ax.add_patch(ful)
    band = Rectangle((mean - sp, 0), 2 * sp, row6[-1] + 0.45, fc="#2563EB", alpha=0.12, ec="none", zorder=0)
    ax.add_patch(band)
    devc = LineCollection([], linewidths=2.2, zorder=3)
    ax.add_collection(devc)
    mline, = ax.plot([], [], "--", color="#DC2626", lw=1.4, zorder=2)
    dtx = []
    for r in range(n):
        dv = xs[r] - mean
        sgn = 1 if dv >= 0 else -1
        dtx.append(ax.text(xs[r] + sgn * off6, row6[r], "", fontsize=8, va="center",
                           ha="left" if sgn > 0 else "right",
                           color="#C2410C" if dv > 0 else ("#6D28D9" if dv < 0 else "#374151")))
    dots = ax.scatter([], [], s=dsz, c="#2563EB", edgecolors="white", zorder=4)
    rings = ax.scatter([], [], s=dsz * 2.3, facecolors="none", edgecolors="#7C3AED", linewidths=2, zorder=5)
    mlab = ax.text(mean + 0.03 * (xr - xl), -0.75, "", color="#DC2626", fontsize=10.5,
                   fontweight="bold", va="center")
    medl, = ax.plot([], [], "--", color="#16A34A", lw=1.8, zorder=1)
    medt = ax.text(med, top + 0.4, "", color="#16A34A", fontsize=10, ha="center", va="bottom")
    rngl, = ax.plot([], [], color="#E07B39", lw=1.8, marker="|", ms=12, mew=2)
    rngt = ax.text((lo + hi) / 2, top + 1.5, "", color="#E07B39", fontsize=10, ha="center", va="bottom")
    info = ax.text(0.01, 0.97, "", transform=ax.transAxes, va="top", fontsize=10.5, zorder=8,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))

    box = Rectangle((q1, -0.38), q3 - q1, 0.76, fc="#DBEAFE", ec="#2563EB", lw=2, zorder=2)
    bx.add_patch(box)
    bmed, = bx.plot([], [], color="#16A34A", lw=3, zorder=3)
    whisk, = bx.plot([], [], color="#2563EB", lw=1.8, zorder=2)
    qmk, = bx.plot([], [], ":", color="#2563EB", lw=1.3)
    outs = bx.scatter([], [], s=45, c="#DC2626", zorder=5)
    tq1 = bx.text(q1, -0.55, "", ha="right", va="top", fontsize=10, color="#2563EB")
    tq3 = bx.text(q3, -0.55, "", ha="left", va="top", fontsize=10, color="#2563EB")
    tiqr = bx.text((q1 + q3) / 2, 0.5, "", ha="center", va="bottom", fontsize=10, color="#2563EB", zorder=4,
                   bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))
    tout = bx.text(outv[-1] if outv else hi, 0.3, "", ha="center", va="bottom", fontsize=9, color="#DC2626")
    bx.set_title("Kutu grafiği" if tr else "Box plot", fontsize=10, loc="left", pad=2)

    tp.text(0.04, 0.975, "Sonuçlar" if tr else "Results", fontsize=12, fontweight="bold", va="top")
    S, ss = st["S"], st["ss"]
    ent = [(0, f"n = {n}", "#111827"),
           (88, r"$\bar{x}$ = " + f"{_d(S)}/{n} {_eq(st['mean'])}", "#DC2626"),
           (95, ("Medyan = " if tr else "Median = ") + _d(med), "#16A34A"),
           (100, (("Mod = " if tr else "Mode = ") + ", ".join(_d(v) for v in st["modes"])) if st["modes"]
            else ("Mod yok" if tr else "No mode"), "#7C3AED"),
           (106, ("Açıklık = " if tr else "Range = ") + f"{_d(hi)} − {_d(lo)} = {_d(hi - lo)}", "#E07B39"),
           (116, r"$Q_1$ = " + _d(q1) + r",   $Q_3$ = " + _d(q3), "#2563EB"),
           (124, f"IQR = {_d(q3)} − {_d(q1)} = {_d(q3 - q1)}", "#2563EB"),
           (131, (("Aykırı: " if tr else "Outlier: ") + ", ".join(_d(v) for v in outv)) if outv
            else ("Aykırı değer yok" if tr else "No outliers"), "#DC2626" if outv else "#6B7280"),
           (160, r"$\Sigma(x-\bar{x})^2$ " + _eq(ss), "#111827"),
           (166, r"$\sigma^2$ = " + f"{_d(ss)}/{n} {_eq(st['vp'])}", "#7C3AED"),
           (166, r"$\sigma$ " + _root(st["vp"]), "#7C3AED"),
           (172, r"$s^2$ = " + f"{_d(ss)}/{n - 1} {_eq(st['vs'])}", "#7C3AED"),
           (172, r"$s$ " + _root(st["vs"]), "#7C3AED")]
    etxt = [tp.text(0.05, 0.9 - k * 0.068, "", fontsize=10.5, color=c, va="top")
            for k, (f0, t0, c) in enumerate(ent)]
    N = 180

    def update(i):
        t = _ease((i - 8) / 26.0)
        for k in range(n):
            dk = rank[k] - k
            yk = (0.6 if dk > 0 else -0.6) * math.sin(math.pi * t) if dk != 0 else 0.0
            cards[k].set_position((k + dk * t, yk))
            r = rank[k]
            fc, ec = "#EFF6FF", "#93C5FD"
            if i >= 98 and xs[r] in modev:
                fc, ec = "#EDE9FE", "#7C3AED"
            if i >= 90 and r in medr:
                fc, ec = "#DCFCE7", "#16A34A"
            if i >= 104 and (r == 0 or r == n - 1):
                ec = "#E07B39"
            bp = cards[k].get_bbox_patch()
            bp.set_facecolor(fc)
            bp.set_edgecolor(ec)
        if i < 58:
            f, tilt, showf = mean, 0.0, False
        elif i < 90:
            tt = (i - 58) / 32.0
            f = mean + (lo - mean) * math.exp(-3.2 * tt) * math.cos(3 * math.pi * tt)
            tilt = max(-1.3, min(1.3, -2.4 * (mean - f) / half)) / half
            showf = True
        else:
            f, tilt, showf = mean, 0.0, True
        pts = []
        u6 = _ease((i - 140) / 10.0)
        for r in range(n):
            s0 = 34 + r * 15.0 / n
            if i < s0:
                continue
            u = _ease((i - s0) / 7.0)
            y = (yt + 0.5) * (1 - u) + (lev[r] + 0.5) * u
            y = y * (1 - u6) + row6[r] * u6
            pts.append((xs[r], y + tilt * (xs[r] - f)))
        dots.set_offsets(np.array(pts) if pts else np.empty((0, 2)))
        dots.set_sizes([dsz + (dsz6 - dsz) * u6])
        ph6 = i >= 140
        beam.set_data([xl, xr], [tilt * (xl - f), tilt * (xr - f)])
        if showf:
            ful.set_xy([[f, 0], [f - fwid, -fhgt], [f + fwid, -fhgt]])
            ful.set_visible(True)
        else:
            ful.set_visible(False)
        mlab.set_text((r"$\bar{x}$ = " + _d(mean) + (" (denge noktası)" if tr else " (balance point)"))
                      if i >= 90 else "")
        if 90 <= i < 140:
            medl.set_data([med, med], [0, top + 0.3])
            medt.set_text(("medyan = " if tr else "median = ") + _d(med))
        else:
            medl.set_data([], [])
            medt.set_text("")
        if 98 <= i < 140 and modev:
            rings.set_offsets(np.array([(xs[r], lev[r] + 0.5) for r in range(n) if xs[r] in modev]))
        else:
            rings.set_offsets(np.empty((0, 2)))
        if 104 <= i < 140:
            rngl.set_data([lo, hi], [top + 1.25, top + 1.25])
            rngt.set_text(("açıklık = " if tr else "range = ") + _d(hi - lo))
        else:
            rngl.set_data([], [])
            rngt.set_text("")
        # box plot
        if i >= 114:
            qmk.set_data([q1, q1, np.nan, q3, q3], [-0.9, 0.9, np.nan, -0.9, 0.9])
            tq1.set_text(r"$Q_1$")
            tq3.set_text(r"$Q_3$")
        else:
            qmk.set_data([], [])
            tq1.set_text("")
            tq3.set_text("")
        box.set_visible(i >= 118)
        bmed.set_data(([med, med], [-0.38, 0.38]) if i >= 122 else ([], []))
        if i >= 126:
            whisk.set_data([wlo, q1, np.nan, q3, whi, np.nan, wlo, wlo, np.nan, whi, whi],
                           [0, 0, np.nan, 0, 0, np.nan, -0.22, 0.22, np.nan, -0.22, 0.22])
            tiqr.set_text(f"IQR = {_d(q3 - q1)}")
        else:
            whisk.set_data([], [])
            tiqr.set_text("")
        if i >= 130 and outv:
            outs.set_offsets(np.array([(v, 0.0) for v in outv]))
            tout.set_text("aykırı" if tr else "outlier")
        else:
            outs.set_offsets(np.empty((0, 2)))
            tout.set_text("")
        # deviations and sd band
        segs, cols = [], []
        mline.set_data(([mean, mean], [0, row6[-1] + 0.45]) if i >= 146 else ([], []))
        for r in range(n):
            on = i >= 150 + r * 12.0 / n
            if on:
                segs.append([(mean, row6[r]), (xs[r], row6[r])])
                cols.append("#E07B39" if xs[r] > mean else "#7C3AED")
            dv = xs[r] - mean
            dtx[r].set_text(((("+" if dv > 0 else "") + _d(dv, 2)).replace("-", "−")) if on else "")
        devc.set_segments(segs)
        devc.set_color(cols if cols else "#E07B39")
        band.set_visible(i >= 168)
        for (f0, t0, c), tx in zip(ent, etxt):
            tx.set_text(t0 if i >= f0 else "")
        if i < 8:
            info.set_text("1) Ham veri (sırasız)" if tr else "1) Raw data (unsorted)")
        elif i < 34:
            info.set_text("1) Veriyi küçükten büyüğe sırala" if tr else "1) Sort the data from smallest to largest")
        elif i < 58:
            info.set_text("2) Nokta grafiği: her değer bir nokta" if tr else "2) Dot plot: one dot per value")
        elif i < 90:
            tq = sum(v - f for v in xs)
            info.set_text(("3) Ortalama = denge noktası\n" if tr else "3) The mean is the balance point\n")
                          + (r"destek d = " if tr else r"pivot d = ") + f"{f:.2f}:  "
                          + r"$\Sigma(x-d)$ = " + f"{tq:+.1f}")
        elif i < 112:
            info.set_text("4) Medyan, mod ve açıklık" if tr else "4) Median, mode and range")
        elif i < 140:
            info.set_text("5) Çeyrekler ve kutu grafiği" if tr else "5) Quartiles and the box plot")
        else:
            info.set_text((r"6) Sapmalar $x-\bar{x}$ (toplamları 0) ⇒ varyans, standart sapma" if tr else
                           r"6) Deviations $x-\bar{x}$ (they sum to 0) ⇒ variance, standard deviation")
                          + ("\n" + (r"mavi bant: $\bar{x}\pm\sigma$ = " if tr else r"blue band: $\bar{x}\pm\sigma$ = ")
                             + f"[{mean - sp:.2f}, {mean + sp:.2f}]" if i >= 168 else ""))
        return []

    return N, update


def vary(P, rnd):
    orig = _stats(P)
    lo0 = int(math.floor(float(orig["xs"][0])))
    span0 = max(6, int(float(orig["xs"][-1] - orig["xs"][0])))
    want_out = bool(orig["out"])
    n0 = orig["n"]
    best = None
    for _ in range(400):
        n = max(6, min(13, n0 + rnd.choice([-1, 0, 0, 1])))
        base = max(0, lo0 + rnd.randint(-3, 3))
        spread = max(5, min(span0, 14) + rnd.randint(-2, 2))
        m = n - 1 if want_out else n
        data = [base + rnd.randint(0, spread) for _ in range(m)]
        data[1] = data[3]
        if want_out:
            data.append(max(data) + spread + rnd.randint(spread // 2, spread))
        rem = sum(data) % n
        data[0] -= rem
        if data[0] < 0:
            data[0] += n
        rnd.shuffle(data)
        st = _stats({"data": data})
        if bool(st["out"]) != want_out or st["xs"][-1] - st["xs"][0] < 4 or st["iqr"] == 0:
            continue
        best = data
        break
    if best is None:
        best = list(P["data"])
    return {"data": best}
''',
}
EXAMPLES += [
    {"id": "prob-desc-1", "kind": "descriptive_stats",
     "title": ("Quiz puanlarının özeti", "Summarizing quiz scores"),
     "q": ("Bir sınıftaki {n} öğrencinin quiz puanları: {data}. Ortalama, medyan, mod, açıklık, "
           "çeyrekler, IQR ile kitle ve örneklem standart sapmasını bul.",
           "Quiz scores of {n} students: {data}. Find the mean, median, mode, range, quartiles, IQR, "
           "and the population and sample standard deviations."),
     "P": {"data": [12, 15, 11, 18, 15, 20, 14, 15, 17, 13]}},
    {"id": "prob-desc-2", "kind": "descriptive_stats",
     "topics": ["outliers", "skewed", "çarpık", "word problem", "sözel problem"],
     "title": ("Aykırı değerli yolculuk süreleri", "Commute times with an outlier"),
     "q": ("Bir çalışanın {n} günlük işe gidiş süreleri (dakika): {data}. Beş sayı özetini ve kutu "
           "grafiğini oluştur. Aykırı değer var mı? Merkezi ortalama mı medyan mı daha iyi temsil eder?",
           "A commuter's travel times (minutes) on {n} days: {data}. Build the five-number summary and "
           "the box plot. Is there an outlier? Which describes the center better, the mean or the median?"),
     "P": {"data": [22, 25, 19, 24, 31, 25, 55, 21, 25, 27, 23]}},
    {"id": "prob-desc-3", "kind": "descriptive_stats",
     "title": ("İki modlu küçük veri kümesi", "A small bimodal data set"),
     "q": ("{data} veri kümesi için modu, medyanı, çeyrekleri ve kitle (σ) ile örneklem (s) standart "
           "sapmalarını hesapla.",
           "For the data set {data}, compute the mode, median, quartiles, and the population (σ) and "
           "sample (s) standard deviations."),
     "P": {"data": [4, 8, 6, 5, 8, 3, 5, 9]}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["normal_area"] = {
    "course": "prob",
    "title": ("Normal dağılımda alan ve z-skorları", "Area under the normal curve and z-scores"),
    "topics": ["normal distribution", "normal curve", "bell curve", "z-score", "z score", "z-scores",
               "standard normal", "z-table", "z table", "empirical rule", "68-95-99.7",
               "area under the normal curve", "normal probability", "standardizing",
               "normal dağılım", "standart normal", "z-skoru", "z skoru", "z puanı", "deneysel kural",
               "çan eğrisi", "normal eğri altındaki alan"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Polygon


def _d(v, k=3):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _z(v):
    s = f"{v:.2f}"
    return "0.00" if s == "-0.00" else s.replace("-", "−")


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _bound(v, default):
    if v is None:
        return default
    if isinstance(v, str):
        s = v.strip().lower().replace("−", "-")
        if s in ("", "none", "null"):
            return default
        if s in ("-inf", "-oo", "-infinity"):
            return -math.inf
        if s in ("inf", "+inf", "oo", "+oo", "infinity"):
            return math.inf
        return float(s)
    return float(v)


def _setup(P):
    mu, sg = float(P["mu"]), abs(float(P["sigma"])) or 1.0
    a = _bound(P.get("a"), -math.inf)
    b = _bound(P.get("b"), math.inf)
    if a > b:
        a, b = b, a
    return mu, sg, a, b


def _event(a, b):
    if math.isinf(a) and math.isinf(b):
        return "P(−∞ < X < ∞)"
    if math.isinf(a):
        return f"P(X < {_d(b)})"
    if math.isinf(b):
        return f"P(X > {_d(a)})"
    return f"P({_d(a)} < X < {_d(b)})"


def _calc(P):
    mu, sg, a, b = _setup(P)
    za = None if math.isinf(a) else round((a - mu) / sg, 2)
    zb = None if math.isinf(b) else round((b - mu) / sg, 2)
    if za is not None and zb is not None:
        pa, pb = round(_phi(za), 4), round(_phi(zb), 4)
        p = pb - pa
        zev = f"P({_z(za)} < Z < {_z(zb)})"
        calc = f"Φ({_z(zb)}) − Φ({_z(za)}) = {pb:.4f} − {pa:.4f} = {p:.4f}"
    elif zb is not None:
        pb = round(_phi(zb), 4)
        p = pb
        zev = f"P(Z < {_z(zb)})"
        calc = f"Φ({_z(zb)}) = {pb:.4f}"
    elif za is not None:
        pa = round(_phi(za), 4)
        p = 1 - pa
        zev = f"P(Z > {_z(za)})"
        calc = f"1 − Φ({_z(za)}) = 1 − {pa:.4f} = {p:.4f}"
    else:
        p, zev, calc = 1.0, "P(−∞ < Z < ∞)", "1"
    return mu, sg, a, b, za, zb, round(p, 4), zev, calc


def solve(P):
    mu, sg, a, b, za, zb, p, zev, calc = _calc(P)
    ev = _event(a, b)
    steps = [(f"X ~ N(μ = {_d(mu)}, σ = {_d(sg)})", f"X ~ N(μ = {_d(mu)}, σ = {_d(sg)})"),
             ("Standartlaştır: z = (x − μ)/σ  (Z ~ N(0, 1))", "Standardize: z = (x − μ)/σ  (Z ~ N(0, 1))")]
    for nm, xv, zv in (("a", a, za), ("b", b, zb)):
        if zv is None:
            continue
        raw = (xv - mu) / sg
        sgn = "=" if abs(raw - zv) < 1e-9 else "≈"
        steps.append((f"x = {_d(xv)}:  z = ({_d(xv)} − {_d(mu)})/{_d(sg)} {sgn} {_z(zv)}",
                      f"x = {_d(xv)}:  z = ({_d(xv)} − {_d(mu)})/{_d(sg)} {sgn} {_z(zv)}"))
    steps.append((f"{ev} = {zev} = {calc}  (z-tablosu)", f"{ev} = {zev} = {calc}  (z-table)"))
    steps.append((f"Deneysel kural: μ ± σ = [{_d(mu - sg)}, {_d(mu + sg)}] ≈ %68,  μ ± 2σ = [{_d(mu - 2 * sg)}, "
                  f"{_d(mu + 2 * sg)}] ≈ %95,  μ ± 3σ = [{_d(mu - 3 * sg)}, {_d(mu + 3 * sg)}] ≈ %99.7",
                  f"Empirical rule: μ ± σ = [{_d(mu - sg)}, {_d(mu + sg)}] ≈ 68%,  μ ± 2σ = [{_d(mu - 2 * sg)}, "
                  f"{_d(mu + 2 * sg)}] ≈ 95%,  μ ± 3σ = [{_d(mu - 3 * sg)}, {_d(mu + 3 * sg)}] ≈ 99.7%"))
    steps.append((f"Yorum: X değerinin bu bölgeye düşme olasılığı yaklaşık %{100 * p:.2f}.",
                  f"Interpretation: about {100 * p:.2f}% of all values fall in this region."))
    return {"answer": (f"{ev} ≈ {p:.4f}  (%{100 * p:.2f})", f"{ev} ≈ {p:.4f}  ({100 * p:.2f}%)"),
            "steps": steps, "fmt": {"event": ev}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    mu, sg, a, b, za, zb, p, zev, calc = _calc(P)
    ev = _event(a, b)
    lo, hi = mu - 4 * sg, mu + 4 * sg
    for v in (a, b):
        if not math.isinf(v):
            lo, hi = min(lo, v - 0.6 * sg), max(hi, v + 0.6 * sg)

    def pdf(x):
        return np.exp(-0.5 * ((np.asarray(x, dtype=float) - mu) / sg) ** 2) / (sg * math.sqrt(2 * math.pi))

    peak = float(pdf(mu))
    xs = np.linspace(lo, hi, 400)
    ys = pdf(xs)
    ax = fig.add_axes([0.07, 0.11, 0.9, 0.66])
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, 1.42 * peak)
    ax.set_xticks([mu + k * sg for k in range(-3, 4)])
    ax.set_xticklabels([_d(mu + k * sg) for k in range(-3, 4)])
    ax.set_yticks([])
    for s in ("left", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", alpha=0.25)

    def to_z(x):
        return (x - mu) / sg

    def from_z(z):
        return mu + z * sg

    sec = ax.secondary_xaxis("top", functions=(to_z, from_z))
    sec.set_xticks(list(range(-3, 4)))
    sec.set_xlabel("z", fontsize=10, labelpad=2)
    ax.set_xlabel("x", fontsize=10, labelpad=2)
    curve, = ax.plot([], [], color="#2563EB", lw=2.6, zorder=4)
    muline, = ax.plot([], [], ":", color="#6B7280", lw=1.3)
    cols = ["#2563EB", "#16A34A", "#7C3AED"]
    alphas = [0.35, 0.25, 0.18]
    bands, anns, drops, blabs = [], [], [], []
    for k in (3, 2, 1):
        bx = np.linspace(mu - k * sg, mu + k * sg, 150)
        pg = Polygon(np.column_stack([np.r_[bx[0], bx, bx[-1]], np.r_[0, pdf(bx), 0]]), closed=True,
                     fc=cols[k - 1], alpha=alphas[k - 1], ec="none", zorder=1)
        ax.add_patch(pg)
        bands.insert(0, pg)
    for k in (1, 2, 3):
        h = (1.04 + 0.12 * (k - 1)) * peak
        an = ax.annotate("", xy=(mu - k * sg, h), xytext=(mu + k * sg, h),
                         arrowprops=dict(arrowstyle="<->", color=cols[k - 1], lw=1.5))
        anns.append(an)
        dl, = ax.plot([mu - k * sg, mu - k * sg, np.nan, mu + k * sg, mu + k * sg],
                      [float(pdf(mu - k * sg)), h, np.nan, float(pdf(mu + k * sg)), h],
                      "--", color=cols[k - 1], lw=1)
        drops.append(dl)
        pct = ["68", "95", "99.7"][k - 1]
        blabs.append(ax.text(mu, h, ("%" + pct) if tr else (pct + "%"), ha="center", va="center",
                             fontsize=10, color=cols[k - 1], fontweight="bold",
                             bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none")))
    area = Polygon(np.zeros((3, 2)), closed=True, fc="#E07B39", alpha=0.55, ec="#C2410C", lw=1.2, zorder=3)
    ax.add_patch(area)
    both = not math.isinf(a) and not math.isinf(b)
    blines, btexts, bpos = [], [], []
    for k, (xv, zv) in enumerate(((a, za), (b, zb))):
        ln, = ax.plot([], [], color="#DC2626", lw=2, zorder=5)
        blines.append(ln)
        if zv is None:
            left = k == 0
            yl = 0.0
        else:
            left = (k == 0) if both else (xv < mu)
            span = np.linspace(xv - 0.95 * sg, xv, 30) if left else np.linspace(xv, xv + 0.95 * sg, 30)
            yl = float(np.max(pdf(span))) + 0.04 * peak
        bpos.append((xv + (-0.08 if left else 0.08) * sg if zv is not None else 0.0, yl))
        btexts.append(ax.text(0, 0, "", color="#DC2626", fontsize=10, ha="right" if left else "left",
                              va="bottom", zorder=6))
    atext = ax.text(0, 0, "", fontsize=12, fontweight="bold", color="#9A3412", ha="center", va="center",
                    zorder=6, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#E07B39", alpha=0.9))
    res = ax.text(0.985, 0.95, "", transform=ax.transAxes, ha="right", va="top", fontsize=13,
                  fontweight="bold", color="#16A34A")
    info = fig.text(0.02, 0.975, "", va="top", fontsize=11,
                    bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    L = a if not math.isinf(a) else lo
    R = b if not math.isinf(b) else hi
    xc = (max(L, lo) + min(R, hi)) / 2
    lab_y = max(0.5 * float(pdf(xc)), 0.16 * peak) if both else max(0.5 * float(pdf(xc)), 0.42 * peak)
    N = 150

    def update(i):
        m = max(2, int(_ease(i / 22.0) * len(xs)))
        curve.set_data(xs[:m], ys[:m])
        muline.set_data([mu, mu], [0, peak] if i >= 22 else [0, 0])
        for k in range(3):
            st0 = 26 + 14 * k
            on = 26 <= i < 72 and i >= st0
            bands[k].set_visible(on)
            anns[k].set_visible(on)
            drops[k].set_visible(on)
            blabs[k].set_visible(on)
        for k, (xv, zv) in enumerate(((a, za), (b, zb))):
            if zv is not None and i >= 72 + 6 * k:
                yv = float(pdf(xv))
                blines[k].set_data([xv, xv], [0, yv])
                btexts[k].set_position(bpos[k])
                btexts[k].set_text(f"x = {_d(xv)}\nz = {_z(zv)}")
            else:
                blines[k].set_data([], [])
                btexts[k].set_text("")
        if i >= 84:
            t = _ease((i - 84) / 38.0)
            xt = L + (R - L) * t
            sx = np.linspace(L, max(xt, L + 1e-9), 120)
            area.set_xy(np.column_stack([np.r_[L, sx, sx[-1]], np.r_[0, pdf(sx), 0]]))
            area.set_visible(True)
            za0 = -math.inf if math.isinf(a) else (a - mu) / sg
            cur = _phi((xt - mu) / sg) - (_phi(za0) if not math.isinf(za0) else 0.0)
            val = p if i >= 122 else cur
            atext.set_position((xc, lab_y))
            atext.set_text(f"{val:.4f}")
        else:
            area.set_visible(False)
            atext.set_text("")
        res.set_text((f"{ev} ≈ {p:.4f}") if i >= 124 else "")
        if i < 24:
            info.set_text((f"1) Normal eğri: X ~ N(μ = {_d(mu)}, σ = {_d(sg)})" if tr else
                           f"1) Normal curve: X ~ N(μ = {_d(mu)}, σ = {_d(sg)})"))
        elif i < 72:
            info.set_text(("2) Deneysel kural (68–95–99.7): μ ± σ, μ ± 2σ, μ ± 3σ" if tr else
                           "2) Empirical rule (68–95–99.7): μ ± σ, μ ± 2σ, μ ± 3σ"))
        elif i < 84:
            info.set_text(("3) Sınırları standartlaştır: z = (x − μ)/σ" if tr else
                           "3) Standardize the bounds: z = (x − μ)/σ"))
        elif i < 124:
            info.set_text((f"4) Olasılık = eğri altındaki alan: {ev} = {zev}" if tr else
                           f"4) Probability = area under the curve: {ev} = {zev}"))
        else:
            info.set_text(f"5) {ev} = {zev}\n    = {calc}")
        return []

    return N, update


def vary(P, rnd):
    mu0, sg0, a0, b0 = _setup(P)
    sigmas = [s for s in (2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100) if sg0 / 1.6 <= s <= sg0 * 1.6]
    sg = rnd.choice(sigmas or [sg0])
    mu = int(round(mu0)) + rnd.choice([-2, -1, 0, 1, 2]) * max(1, int(round(0.5 * sg0)))
    zs = [-2.5, -2.0, -1.5, -1.25, -1.0, -0.75, -0.5, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5]
    while True:
        z1, z2 = sorted(rnd.sample(zs, 2))
        a = None if math.isinf(a0) else int(round(mu + z1 * sg))
        b = None if math.isinf(b0) else int(round(mu + z2 * sg))
        if a is not None and b is None:
            a = int(round(mu + rnd.choice(zs) * sg))
        if b is not None and a is None:
            b = int(round(mu + rnd.choice(zs) * sg))
        if a is None or b is None or a < b:
            break
    return {"mu": mu, "sigma": sg, "a": "-inf" if a is None else a, "b": "inf" if b is None else b}
''',
}
EXAMPLES += [
    {"id": "prob-normarea-1", "kind": "normal_area",
     "title": ("İki değer arasındaki olasılık", "Probability between two values"),
     "q": ("Sınav puanları ortalaması {mu}, standart sapması {sigma} olan normal dağılıma uyuyor. "
           "{event} olasılığını z-skorlarıyla bul.",
           "Exam scores are normally distributed with mean {mu} and standard deviation {sigma}. "
           "Use z-scores to find {event}."),
     "P": {"mu": 70, "sigma": 8, "a": 62, "b": 86}},
    {"id": "prob-normarea-2", "kind": "normal_area", "topics": ["word problem", "sözel problem", "upper tail"],
     "title": ("Sağ kuyruk: uzun boylular", "Upper tail: tall adults"),
     "q": ("Yetişkin boyları ortalaması {mu} cm, standart sapması {sigma} cm olan normal dağılıma uyuyor. "
           "Rastgele seçilen bir yetişkinin {a} cm'den uzun olma olasılığı nedir? ({event})",
           "Adult heights are normal with mean {mu} cm and standard deviation {sigma} cm. What is the "
           "probability that a randomly chosen adult is taller than {a} cm? ({event})"),
     "P": {"mu": 170, "sigma": 6, "a": 182, "b": "inf"}},
    {"id": "prob-normarea-3", "kind": "normal_area", "topics": ["lower tail", "percentile", "yüzdelik"],
     "title": ("Sol kuyruk: pil ömrü", "Lower tail: battery life"),
     "q": ("Bir pilin ömrü ortalaması {mu} saat, standart sapması {sigma} saat olan normal dağılıma sahip. "
           "Bir pilin {b} saatten önce bitme olasılığı nedir? ({event})",
           "Battery life is normal with mean {mu} hours and standard deviation {sigma} hours. What is the "
           "probability that a battery dies before {b} hours? ({event})"),
     "P": {"mu": 500, "sigma": 40, "a": "-inf", "b": 450}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["clt"] = {
    "course": "prob",
    "title": ("Merkezi limit teoremi", "Central limit theorem"),
    "topics": ["central limit theorem", "clt", "sampling distribution", "sampling distribution of the mean",
               "sampling distribution of the sample mean", "distribution of sample means", "sample mean",
               "standard error", "merkezi limit teoremi", "merkezi limit", "örnekleme dağılımı",
               "örneklem ortalaması", "örneklem ortalamalarının dağılımı", "standart hata"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Rectangle


def _d(v, k=3):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _pop(P):
    d = str(P.get("dist", "dice")).strip().lower()
    if d.startswith("u"):
        return {"key": "uniform", "mu": 5.0, "sd": 10 / math.sqrt(12), "lo": 0.0, "hi": 10.0,
                "name": ("Düzgün dağılım U(0, 10)", "Uniform distribution U(0, 10)"),
                "sdtxt": "10/√12"}
    if d.startswith("e"):
        return {"key": "exponential", "mu": 2.0, "sd": 2.0, "lo": 0.0, "hi": 10.0,
                "name": ("Üstel dağılım (ortalama 2, sağa çarpık)", "Exponential distribution (mean 2, right-skewed)"),
                "sdtxt": ""}
    return {"key": "dice", "mu": 3.5, "sd": math.sqrt(35 / 12), "lo": 0.5, "hi": 6.5,
            "name": ("Hilesiz zar (1–6)", "Fair die (1–6)"), "sdtxt": "√(35/12)"}


def _draw(P):
    pop = _pop(P)
    rng = np.random.default_rng(P.get("seed", 0))
    n, K = max(1, int(P["n"])), max(20, int(P.get("samples", 400)))
    if pop["key"] == "uniform":
        data = rng.uniform(0, 10, size=(K, n))
    elif pop["key"] == "exponential":
        data = rng.exponential(2.0, size=(K, n))
    else:
        data = rng.integers(1, 7, size=(K, n)).astype(float)
    jit = rng.uniform(0.0, 1.0, size=(K, n))
    return pop, data, data.mean(axis=1), jit


def solve(P):
    pop, data, means, jit = _draw(P)
    n, K = data.shape[1], data.shape[0]
    se = pop["sd"] / math.sqrt(n)
    nm = pop["name"]
    sds = f"{pop['sdtxt']} ≈ {pop['sd']:.3f}" if pop["sdtxt"] else _d(pop["sd"])
    steps = [(f"Kitle: {nm[0]};  μ = {_d(pop['mu'])},  σ = {sds}",
              f"Population: {nm[1]};  μ = {_d(pop['mu'])},  σ = {sds}"),
             ("Merkezi limit teoremi: n yeterince büyükse x̄ ≈ N(μ, σ²/n) — kitle normal olmasa bile",
              "Central limit theorem: for large enough n, x̄ ≈ N(μ, σ²/n) — even if the population is not normal"),
             (f"Örnekleme dağılımının ortalaması: μ_x̄ = μ = {_d(pop['mu'])}",
              f"Mean of the sampling distribution: μ_x̄ = μ = {_d(pop['mu'])}"),
             (f"Standart hata: σ_x̄ = σ/√n = {pop['sd']:.3f}/√{n} ≈ {se:.3f}",
              f"Standard error: σ_x̄ = σ/√n = {pop['sd']:.3f}/√{n} ≈ {se:.3f}"),
             (f"Ortalamaların yaklaşık %95'i μ ± 2σ_x̄ = [{pop['mu'] - 2 * se:.2f}, {pop['mu'] + 2 * se:.2f}] aralığındadır",
              f"About 95% of sample means lie in μ ± 2σ_x̄ = [{pop['mu'] - 2 * se:.2f}, {pop['mu'] + 2 * se:.2f}]"),
             (f"Simülasyon ({K} örneklem, her biri n = {n}): x̄'lerin ortalaması ≈ {means.mean():.3f}, "
              f"standart sapması ≈ {means.std():.3f}",
              f"Simulation ({K} samples of size n = {n}): mean of the x̄'s ≈ {means.mean():.3f}, "
              f"their standard deviation ≈ {means.std():.3f}")]
    if pop["key"] == "exponential" and n < 30:
        steps.append(("Kitle çarpık olduğundan n küçükken x̄ dağılımı da hafif sağa çarpık kalır; n büyüdükçe çan eğrisine yaklaşır.",
                      "Because the population is skewed, x̄ is still slightly right-skewed for small n; it becomes bell-shaped as n grows."))
    else:
        steps.append(("n arttıkça histogram daralır (σ/√n) ve çan eğrisine yaklaşır.",
                      "As n increases the histogram narrows (σ/√n) and looks more and more like a bell curve."))
    ans = f"x̄ ≈ N({_d(pop['mu'])}, {se:.3f}²);  σ_x̄ = σ/√n ≈ {se:.3f}"
    return {"answer": (ans, ans), "steps": steps,
            "fmt": {"popname": nm, "se": f"{se:.3f}"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    pop, data, means, jit = _draw(P)
    K, n = data.shape
    mu, sd = pop["mu"], pop["sd"]
    se = sd / math.sqrt(n)
    lo, hi = pop["lo"], pop["hi"]
    if pop["key"] == "dice":
        m = max(1, int(round((se / 3.0) * n)))
        w = m / n
        e0 = 1 - 0.5 / n
        nb = int(math.ceil((6 + 0.5 / n - e0) / w))
        edges = e0 + w * np.arange(nb + 1)
    else:
        w = max(se / 3.0, (hi - lo) / 90.0)
        a0, b0 = max(lo, mu - 5 * se), min(hi, mu + 5.5 * se)
        nb = max(8, int(math.ceil((b0 - a0) / w)))
        edges = a0 + w * np.arange(nb + 1)
    centers = (edges[:-1] + edges[1:]) / 2
    idx = np.searchsorted(edges, means, side="right") - 1
    ok = (idx >= 0) & (idx < nb)
    oh = np.zeros((K, nb))
    oh[np.arange(K)[ok], idx[ok]] = 1
    cum = np.vstack([np.zeros((1, nb)), np.cumsum(oh, axis=0)])
    cs = np.r_[0.0, np.cumsum(means)]
    cs2 = np.r_[0.0, np.cumsum(means ** 2)]
    gx = np.linspace(lo, hi, 400)
    gy = K * w * np.exp(-0.5 * ((gx - mu) / se) ** 2) / (se * math.sqrt(2 * math.pi))
    ytop = max(float(cum[-1].max()), float(gy.max())) * 1.5

    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.75], left=0.075, right=0.98, top=0.93, bottom=0.08, hspace=0.32)
    pa = fig.add_subplot(gs[0, 0])
    hx = fig.add_subplot(gs[1, 0], sharex=pa)
    pa.set_xlim(lo, hi)
    if pop["key"] == "dice":
        pmax = 1 / 6
        pa.bar(range(1, 7), [1 / 6] * 6, width=0.8, color="#93C5FD", alpha=0.45, ec="#2563EB")
        pa.set_xticks(range(1, 7))
    elif pop["key"] == "uniform":
        pmax = 0.1
        pa.fill_between([0, 10], [0.1, 0.1], color="#93C5FD", alpha=0.45)
        pa.plot([0, 0, 10, 10], [0, 0.1, 0.1, 0], color="#2563EB", lw=2)
    else:
        pmax = 0.5
        px = np.linspace(0, 10, 300)
        pa.fill_between(px, 0.5 * np.exp(-px / 2), color="#93C5FD", alpha=0.45)
        pa.plot(px, 0.5 * np.exp(-px / 2), color="#2563EB", lw=2)
    pa.set_ylim(0, pmax * 1.45)
    pa.set_yticks([])
    pa.axvline(mu, color="#6B7280", ls=":", lw=1.3)
    pa.set_title((("Kitle: " + pop["name"][0]) if tr else ("Population: " + pop["name"][1]))
                 + f"   μ = {_d(mu)},  σ ≈ {sd:.2f}", fontsize=10.5, loc="left")
    sdots = pa.scatter([], [], s=60 if n <= 6 else (38 if n <= 12 else 20), c="#E07B39", edgecolors="#9A3412",
                       lw=0.5, zorder=5)
    smean, = pa.plot([], [], color="#DC2626", lw=2.2, zorder=6)
    smtext = pa.text(0, pmax * 1.32, "", color="#DC2626", fontsize=10, ha="center", va="center", zorder=7,
                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    stacks = []
    for j in range(K):
        row = data[j]
        if pop["key"] == "dice":
            cnt = {}
            ys = []
            for v in row:
                c = cnt.get(v, 0)
                cnt[v] = c + 1
                ys.append(c)
            mx = max(cnt.values())
            dy = min(0.11, 0.95 / mx) * pmax
            stacks.append([(c + 0.6) * dy for c in ys])
        else:
            stacks.append(list(pmax * (0.08 + 0.85 * jit[j])))

    bars = hx.bar(centers, np.zeros(nb), width=w * 0.92, color="#2563EB", alpha=0.85)
    hx.set_ylim(0, ytop)
    hx.set_xlim(lo, hi)
    hx.set_ylabel("sayı" if tr else "count", fontsize=9)
    hx.axvline(mu, color="#6B7280", ls=":", lw=1.3)
    hx.set_title((r"Örneklem ortalamalarının ($\bar{x}$) histogramı, n = " if tr else
                  r"Histogram of sample means ($\bar{x}$), n = ") + str(n), fontsize=10.5, loc="left")
    hline, = hx.plot([], [], color="#DC2626", lw=1.6, ls="--")
    ncurve, = hx.plot([], [], color="#E07B39", lw=2.6, zorder=6)
    sebar, = hx.plot([], [], color="#7C3AED", lw=2.2, marker="|", ms=10, mew=2, zorder=7)
    setext = hx.text(mu, 0, "", color="#7C3AED", fontsize=10, ha="left", va="center", zorder=7,
                     bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    info = hx.text(0.01, 0.96, "", transform=hx.transAxes, va="top", fontsize=10.5, zorder=8,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    stat = hx.text(0.99, 0.96, "", transform=hx.transAxes, va="top", ha="right", fontsize=10, zorder=8,
                   bbox=dict(boxstyle="round", fc="#F9FAFB", ec="#D1D5DB"))
    N = 170
    slow = 12

    def kof(i):
        if i < 18:
            return 0
        if i < 78:
            return min(slow, 1 + (i - 18) // 5)
        if i < 140:
            t = (i - 78) / 62.0
            return int(round(slow * (K / float(slow)) ** t))
        return K

    def update(i):
        k = max(0, min(K, kof(i)))
        h = cum[k]
        yl = ytop if i >= 140 else min(ytop, max(6.0, 1.6 * float(h.max())))
        hx.set_ylim(0, yl)
        newest = idx[k - 1] if (k >= 1 and ok[k - 1]) else -1
        for b, (rect, hh) in enumerate(zip(bars, h)):
            rect.set_height(hh)
            rect.set_facecolor("#DC2626" if (b == newest and i < 78) else "#2563EB")
        if k >= 1:
            j = k - 1
            sdots.set_offsets(np.column_stack([data[j], stacks[j]]))
            xm = means[j]
            smean.set_data([xm, xm], [0, pmax * 1.22])
            smtext.set_position((min(max(xm, lo + 0.08 * (hi - lo)), hi - 0.08 * (hi - lo)), pmax * 1.32))
            smtext.set_text((r"$\bar{x}$ = " + f"{xm:.2f}"))
            hline.set_data(([xm, xm], [0, yl * 0.62]) if i < 78 else ([], []))
        else:
            sdots.set_offsets(np.empty((0, 2)))
            smean.set_data([], [])
            smtext.set_text("")
            hline.set_data([], [])
        if i >= 140:
            m = max(2, int(_ease((i - 140) / 16.0) * len(gx)))
            ncurve.set_data(gx[:m], gy[:m])
        else:
            ncurve.set_data([], [])
        if i >= 152:
            yb = float(gy.max()) * 0.6065
            sebar.set_data([mu - se, mu + se], [yb, yb])
            setext.set_position((mu + se + 0.01 * (hi - lo), yb))
            setext.set_text(r"$\mu \pm \sigma/\sqrt{n}$")
        else:
            sebar.set_data([], [])
            setext.set_text("")
        if k >= 1:
            mk = cs[k] / k
            sk = math.sqrt(max(0.0, cs2[k] / k - mk * mk))
            lines = [("örneklem sayısı: " if tr else "samples: ") + str(k),
                     r"ort($\bar{x}$) = " + f"{mk:.3f}" if tr else r"mean($\bar{x}$) = " + f"{mk:.3f}",
                     r"ss($\bar{x}$) = " + f"{sk:.3f}" if tr else r"sd($\bar{x}$) = " + f"{sk:.3f}"]
            if i >= 146:
                lines.append(r"$\sigma/\sqrt{n}$ = " + f"{sd:.3f}/√{n} = {se:.3f}")
            stat.set_text("\n".join(lines))
            stat.set_visible(True)
        else:
            stat.set_text("")
            stat.set_visible(False)
        if i < 18:
            info.set_text(("1) Kitleden n = " + str(n) + " büyüklüğünde örneklemler çekeceğiz") if tr else
                          ("1) We will draw samples of size n = " + str(n) + " from the population"))
        elif i < 78:
            info.set_text((f"2) Örneklem #{k}: ortalamasını histograma ekle" if tr else
                           f"2) Sample #{k}: add its mean to the histogram"))
        elif i < 140:
            info.set_text(("3) Yüzlerce tekrar… ortalamalar μ etrafında toplanıyor" if tr else
                           "3) Hundreds of repetitions… the means pile up around μ"))
        else:
            info.set_text((r"4) MLT: $\bar{x}$ ≈ N(μ, σ/√n), σ/√n ≈ " + f"{se:.3f}" if tr else
                           r"4) CLT: $\bar{x}$ ≈ N(μ, σ/√n), σ/√n ≈ " + f"{se:.3f}"))
        return []

    return N, update


def vary(P, rnd):
    return {"dist": _pop(P)["key"], "n": rnd.choice([4, 5, 8, 10, 16, 20, 25, 30]),
            "samples": rnd.choice([300, 400, 500, 600]), "seed": rnd.randint(1, 9999)}
''',
}
EXAMPLES += [
    {"id": "prob-clt-1", "kind": "clt",
     "title": ("Zar ortalamalarının dağılımı", "Distribution of dice averages"),
     "q": ("Bir zar {n} kez atılıp ortalaması alınıyor; bu deney {samples} kez tekrarlanıyor. Örneklem "
           "ortalamalarının dağılımı nasıl görünür? Ortalaması ve standart hatası nedir?",
           "A die is rolled {n} times and the average is recorded; this is repeated {samples} times. What "
           "does the distribution of the sample means look like? What are its mean and standard error?"),
     "P": {"dist": "dice", "n": 5, "samples": 400, "seed": 11}},
    {"id": "prob-clt-2", "kind": "clt", "topics": ["skewed population", "çarpık dağılım", "exponential", "üstel"],
     "title": ("Çarpık kitleden örneklem ortalamaları", "Sample means from a skewed population"),
     "q": ("Bir bankada bekleme süreleri ortalaması 2 dakika olan sağa çarpık (üstel) bir dağılıma uyuyor. "
           "{n} müşterilik örneklemlerin ortalama bekleme süresi nasıl dağılır? Standart hata nedir?",
           "Waiting times at a bank follow a right-skewed (exponential) distribution with mean 2 minutes. "
           "How is the average waiting time of samples of {n} customers distributed? What is the standard error?"),
     "P": {"dist": "exponential", "n": 30, "samples": 500, "seed": 5}},
    {"id": "prob-clt-3", "kind": "clt", "topics": ["uniform", "düzgün dağılım"],
     "title": ("Düzgün dağılımdan ortalamalar", "Means from a uniform distribution"),
     "q": ("0 ile 10 arasında düzgün dağılımlı {n} rastgele sayının ortalaması alınıyor. Merkezi limit "
           "teoremine göre bu ortalamanın yaklaşık dağılımı nedir?",
           "The average of {n} random numbers drawn uniformly from 0 to 10 is computed. By the central "
           "limit theorem, what is the approximate distribution of this average?"),
     "P": {"dist": "uniform", "n": 10, "samples": 400, "seed": 3}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["regression"] = {
    "course": "prob",
    "title": ("Doğrusal regresyon: en küçük kareler", "Linear regression: least squares"),
    "topics": ["linear regression", "regression", "least squares", "least-squares line", "line of best fit",
               "best fit line", "best-fit line", "scatter plot", "scatterplot", "residual", "residuals",
               "correlation coefficient", "coefficient of determination", "r squared", "r-squared",
               "correlation and regression", "prediction",
               "doğrusal regresyon", "regresyon", "en küçük kareler", "saçılım grafiği", "serpme diyagramı",
               "artık", "korelasyon katsayısı", "belirlilik katsayısı", "en iyi uyan doğru"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Rectangle
from matplotlib.collections import LineCollection


def _d(v, k=3):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _eq(v):
    v = Fraction(v)
    return ("= " if (v * 10000).denominator == 1 else "≈ ") + _d(v, 4)


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _fr(v):
    return Fraction(str(v)) if isinstance(v, float) else Fraction(v)


def _fit(P):
    x = [_fr(v) for v in P["x"]]
    y = [_fr(v) for v in P["y"]]
    n = min(len(x), len(y))
    x, y = x[:n], y[:n]
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    if sxx == 0:
        sxx = Fraction(1)
    b1 = sxy / sxx
    b0 = my - b1 * mx
    r = float(sxy) / math.sqrt(float(sxx * syy)) if syy > 0 else 1.0
    sse = syy - b1 * sxy
    xp = _fr(P.get("xp", float(max(x)) + 1))
    return {"x": x, "y": y, "n": n, "mx": mx, "my": my, "sxx": sxx, "syy": syy, "sxy": sxy,
            "b1": b1, "b0": b0, "r": r, "sse": sse, "xp": xp, "yp": b0 + b1 * xp}


def _line(b0, b1):
    if b1 == 0:
        return f"ŷ = {_d(b0, 4)}"
    c = "" if abs(b1) == 1 else _d(abs(b1), 4)
    if b0 == 0:
        return "ŷ = " + ("−" if b1 < 0 else "") + c + "x"
    return f"ŷ = {_d(b0, 4)}" + (" + " if b1 > 0 else " − ") + c + "x"


def solve(P):
    F = _fit(P)
    n = F["n"]
    sx, sy = sum(F["x"]), sum(F["y"])
    steps = [(f"n = {n};  x̄ = Σx/n = {_d(sx)}/{n} {_eq(F['mx'])};  ȳ = Σy/n = {_d(sy)}/{n} {_eq(F['my'])}",
              f"n = {n};  x̄ = Σx/n = {_d(sx)}/{n} {_eq(F['mx'])};  ȳ = Σy/n = {_d(sy)}/{n} {_eq(F['my'])}"),
             (f"Sxx = Σ(x − x̄)² {_eq(F['sxx'])};  Syy = Σ(y − ȳ)² {_eq(F['syy'])};  "
              f"Sxy = Σ(x − x̄)(y − ȳ) {_eq(F['sxy'])}",
              f"Sxx = Σ(x − x̄)² {_eq(F['sxx'])};  Syy = Σ(y − ȳ)² {_eq(F['syy'])};  "
              f"Sxy = Σ(x − x̄)(y − ȳ) {_eq(F['sxy'])}"),
             (f"Eğim: b₁ = Sxy / Sxx = {_d(F['sxy'], 4)}/{_d(F['sxx'], 4)} {_eq(F['b1'])}",
              f"Slope: b₁ = Sxy / Sxx = {_d(F['sxy'], 4)}/{_d(F['sxx'], 4)} {_eq(F['b1'])}"),
             (f"Kesen: b₀ = ȳ − b₁·x̄ = {_d(F['my'], 4)} − ({_d(F['b1'], 4)})·{_d(F['mx'], 4)} {_eq(F['b0'])}",
              f"Intercept: b₀ = ȳ − b₁·x̄ = {_d(F['my'], 4)} − ({_d(F['b1'], 4)})·{_d(F['mx'], 4)} {_eq(F['b0'])}"),
             (f"En küçük kareler doğrusu: {_line(F['b0'], F['b1'])}",
              f"Least-squares line: {_line(F['b0'], F['b1'])}"),
             (f"Korelasyon: r = Sxy / √(Sxx·Syy) = {_d(F['sxy'], 4)}/√({_d(F['sxx'], 4)}·{_d(F['syy'], 4)}) ≈ {F['r']:.4f}",
              f"Correlation: r = Sxy / √(Sxx·Syy) = {_d(F['sxy'], 4)}/√({_d(F['sxx'], 4)}·{_d(F['syy'], 4)}) ≈ {F['r']:.4f}"),
             (f"Belirlilik katsayısı r² ≈ {F['r'] ** 2:.4f} ⇒ y'deki değişkenliğin yaklaşık %{100 * F['r'] ** 2:.1f} kadarı x ile açıklanır",
              f"Coefficient of determination r² ≈ {F['r'] ** 2:.4f} ⇒ about {100 * F['r'] ** 2:.1f}% of the variation in y is explained by x"),
             (f"Artık kareler toplamı (en küçük): SSE = Σ(y − ŷ)² = Syy − b₁·Sxy {_eq(F['sse'])}",
              f"Sum of squared residuals (the minimum): SSE = Σ(y − ŷ)² = Syy − b₁·Sxy {_eq(F['sse'])}"),
             (f"Tahmin: x = {_d(F['xp'])} ⇒ ŷ = {_d(F['b0'], 4)} + ({_d(F['b1'], 4)})·{_d(F['xp'])} {_eq(F['yp'])}",
              f"Prediction: x = {_d(F['xp'])} ⇒ ŷ = {_d(F['b0'], 4)} + ({_d(F['b1'], 4)})·{_d(F['xp'])} {_eq(F['yp'])}")]
    a = f"{_line(F['b0'], F['b1'])};  r ≈ {F['r']:.3f},  r² ≈ {F['r'] ** 2:.3f};  ŷ({_d(F['xp'])}) {_eq(F['yp'])}"
    pairs = ", ".join(f"({_d(a1)}, {_d(b1)})" for a1, b1 in zip(F["x"], F["y"]))
    return {"answer": (a, a), "steps": steps, "fmt": {"pairs": pairs, "line": _line(F["b0"], F["b1"])}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    F = _fit(P)
    n = F["n"]
    X = np.array([float(v) for v in F["x"]])
    Y = np.array([float(v) for v in F["y"]])
    mx, my = float(F["mx"]), float(F["my"])
    b1, b0 = float(F["b1"]), float(F["b0"])
    sxx, syy, sxy = float(F["sxx"]), float(F["syy"]), float(F["sxy"])
    xp, yp = float(F["xp"]), float(F["yp"])
    xmin, xmax = min(X.min(), xp), max(X.max(), xp)
    xs = max(xmax - xmin, 1.0)
    ymin, ymax = min(Y.min(), yp), max(Y.max(), yp)
    ys = max(ymax - ymin, 1.0)
    xl, xr = xmin - 0.1 * xs, xmax + 0.12 * xs
    yl, yr = ymin - 0.15 * ys, ymax + 0.5 * ys
    m0 = -0.6 * b1 if abs(b1) > 1e-9 else 0.8 * ys / xs
    c0 = 0.28 * ys

    def sse_of(m, c):
        return syy - 2 * m * sxy + m * m * sxx + n * c * c

    gs = fig.add_gridspec(2, 2, width_ratios=[1.75, 1], height_ratios=[1, 1.3], left=0.07, right=0.985,
                          top=0.93, bottom=0.09, wspace=0.2, hspace=0.42)
    ax = fig.add_subplot(gs[:, 0])
    sx = fig.add_subplot(gs[0, 1])
    tp = fig.add_subplot(gs[1, 1])
    tp.axis("off")
    tp.set_xlim(0, 1)
    tp.set_ylim(0, 1)
    ax.set_xlim(xl, xr)
    ax.set_ylim(yl, yr)
    ax.grid(alpha=0.3)
    ax.set_xlabel("x", fontsize=10)
    ax.set_ylabel("y", fontsize=10)
    fw_in, fh_in = fig.get_size_inches()
    pos = ax.get_position()
    kx = ((xr - xl) / (pos.width * fw_in)) / ((yr - yl) / (pos.height * fh_in))
    squares = []
    for k in range(n):
        rc = Rectangle((0, 0), 0, 0, fc="#E07B39", alpha=0.18, ec="#E07B39", lw=0.8, zorder=1)
        ax.add_patch(rc)
        squares.append(rc)
    resid = LineCollection([], colors="#DC2626", linewidths=1.6, linestyles="--", zorder=2)
    ax.add_collection(resid)
    pts = ax.scatter([], [], s=55, c="#2563EB", edgecolors="white", zorder=5)
    cen, = ax.plot([], [], "P", color="#DC2626", ms=11, zorder=6)
    cent = ax.text(mx, my, "", color="#DC2626", fontsize=10, ha="left", va="top" if b1 >= 0 else "bottom", zorder=6)
    line, = ax.plot([], [], color="#16A34A", lw=2.6, zorder=4)
    pdot, = ax.plot([], [], "*", color="#7C3AED", ms=17, zorder=7)
    pguide, = ax.plot([], [], ":", color="#7C3AED", lw=1.6, zorder=3)
    ptext = ax.text(xp, yp, "", color="#7C3AED", fontsize=11, fontweight="bold", ha="right",
                    va="bottom" if b1 >= 0 else "top", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    info = ax.text(0.015, 0.975, "", transform=ax.transAxes, va="top", fontsize=10.5, zorder=8,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))

    mlo, mhi = min(m0, b1), max(m0, b1)
    dm = max(mhi - mlo, 0.5)
    mg = np.linspace(mlo - 0.25 * dm, mhi + 0.25 * dm, 200)
    sg = sse_of(mg, 0.0)
    smax = max(float(sg.max()), sse_of(m0, c0)) * 1.12
    sx.plot(mg, sg, color="#2563EB", lw=2)
    sx.set_xlim(mg[0], mg[-1])
    sx.set_ylim(0, smax)
    sx.grid(alpha=0.3)
    sx.set_xlabel(("eğim m" if tr else "slope m"), fontsize=9, labelpad=1)
    sx.tick_params(labelsize=8)
    sx.set_title(("SSE(m): (x̄, ȳ)'den geçen doğrular" if tr else "SSE(m): lines through (x̄, ȳ)"),
                 fontsize=9.5)
    sdot, = sx.plot([], [], "o", color="#DC2626", ms=9, zorder=5)
    smin, = sx.plot([], [], "--", color="#16A34A", lw=1.4)
    smint = sx.text(b1, smax * 0.92, "", color="#16A34A", fontsize=9.5, ha="center", va="top",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
    yhat_lbl = _line(F["b0"], F["b1"])
    rows = [(100, r"$\bar{x}$ = " + _d(mx, 4) + r",   $\bar{y}$ = " + _d(my, 4), "#111827"),
            (106, r"$S_{xx}$ = " + _d(sxx, 4) + r",   $S_{xy}$ = " + _d(sxy, 4), "#111827"),
            (112, r"$b_1 = S_{xy}/S_{xx}$ = " + _d(b1, 4), "#16A34A"),
            (118, r"$b_0 = \bar{y} - b_1\bar{x}$ = " + _d(b0, 4), "#16A34A"),
            (124, yhat_lbl, "#16A34A"),
            (130, r"$r = S_{xy}/\sqrt{S_{xx}S_{yy}}$ ≈ " + f"{F['r']:.3f}", "#2563EB"),
            (136, r"$r^2$ ≈ " + f"{F['r'] ** 2:.3f}", "#2563EB"),
            (150, ("tahmin: " if tr else "prediction: ") + r"$\hat{y}$(" + _d(xp) + ") = " + _d(yp, 4), "#7C3AED")]
    rtx = [tp.text(0.0, 0.97 - k * 0.125, "", fontsize=10, color=c, va="top") for k, (f0, t0, c) in enumerate(rows)]
    N = 175

    def params(i):
        if i < 22:
            return None
        if i < 55:
            return m0, c0 * (1 - _ease((i - 22) / 30.0))
        if i < 100:
            return m0 + (b1 - m0) * _ease((i - 55) / 42.0), 0.0
        return b1, 0.0

    def update(i):
        k = n if i >= 18 else min(n, int(i * n / 16.0) + 1)
        pts.set_offsets(np.column_stack([X[:k], Y[:k]]))
        if i >= 18:
            cen.set_data([mx], [my])
            cent.set_position((mx + 0.015 * (xr - xl), my + (-0.02 if b1 >= 0 else 0.02) * (yr - yl)))
            cent.set_text(r"$(\bar{x}, \bar{y})$")
        else:
            cen.set_data([], [])
            cent.set_text("")
        pr = params(i)
        segs = []
        if pr is None:
            line.set_data([], [])
            for rc in squares:
                rc.set_visible(False)
            sdot.set_data([], [])
            cur = None
        else:
            m, c = pr
            lx = np.array([xl, xr])
            line.set_data(lx, my + m * (lx - mx) + c)
            yh = my + m * (X - mx) + c
            fade = 1.0 - _ease((i - 128) / 10.0)
            for kk, rc in enumerate(squares):
                rr = Y[kk] - yh[kk]
                rc.set_xy((X[kk], min(Y[kk], yh[kk])))
                rc.set_width(abs(rr) * kx)
                rc.set_height(abs(rr))
                rc.set_alpha(0.2 * fade)
                rc.set_visible(fade > 0.01)
                segs.append([(X[kk], Y[kk]), (X[kk], yh[kk])])
            cur = sse_of(m, c)
            sdot.set_data([m], [cur])
        resid.set_segments(segs)
        if i >= 100:
            smin.set_data([b1, b1], [0, smax * 0.8])
            smint.set_text(r"min: $b_1$ = " + _d(b1, 4))
        else:
            smin.set_data([], [])
            smint.set_text("")
        for (f0, t0, c), tx in zip(rows, rtx):
            tx.set_text(t0 if i >= f0 else "")
        if i >= 145:
            pdot.set_data([xp], [yp])
            pguide.set_data([xp, xp, xl], [yl, yp, yp])
            ptext.set_position((xp - 0.02 * (xr - xl), yp + (0.03 if b1 >= 0 else -0.03) * (yr - yl)))
            ptext.set_text(r"$\hat{y}$(" + _d(xp) + ") = " + _d(yp, 4))
        else:
            pdot.set_data([], [])
            pguide.set_data([], [])
            ptext.set_text("")
        ss = "" if cur is None else ("\nSSE = Σ(y − ŷ)² = " + f"{cur:.2f}")
        if i < 22:
            info.set_text("1) Saçılım grafiği: (x, y) noktaları" if tr else "1) Scatter plot of the (x, y) points")
        elif i < 55:
            info.set_text(("2) Kötü bir doğru: artıklar ve kareleri" if tr else
                           "2) A poor line: residuals and their squares") + ss)
        elif i < 100:
            info.set_text(("3) Doğruyu (x̄, ȳ) etrafında döndür: SSE küçülür" if tr else
                           "3) Rotate the line about (x̄, ȳ): SSE shrinks") + ss)
        elif i < 145:
            info.set_text(("4) En küçük kareler doğrusu: " if tr else "4) Least-squares line: ") + yhat_lbl + ss)
        else:
            info.set_text(("5) Tahmin: x = " if tr else "5) Prediction: x = ") + _d(xp) + " ⇒ ŷ = " + _d(yp, 4))
        return []

    return N, update


def vary(P, rnd):
    F = _fit(P)
    xs0 = sorted(float(v) for v in F["x"])
    n0 = len(xs0)
    h = max(1, int(round((xs0[-1] - xs0[0]) / max(1, n0 - 1))))
    n = rnd.choice([5, 7])
    c = (n - 1) // 2
    x0 = max(0, int(xs0[0]) + rnd.choice([-1, 0, 1]) * h)
    sgn = 1 if float(F["b1"]) >= 0 else -1
    mag = max(0.5, round(abs(float(F["b1"])) * rnd.choice([0.5, 0.75, 1.0, 1.25, 1.5]) * 2) / 2)
    if h % 2 == 1 and mag != int(mag):
        mag = float(int(mag) + 1)
    b1 = sgn * mag
    patt = {5: [1, -2, 0, 2, -1], 7: [1, -1, -1, 2, -1, -1, 1]}[n]
    lim = max(1, min(3, int(round(abs(b1) * h))))
    e = None
    for _ in range(600):
        t = [k - c for k in range(n)]
        e = [rnd.randint(-lim, lim) for _ in range(n - 2)]
        A, B = sum(e), sum(tk * ek for tk, ek in zip(t, e))
        last = t[n - 2] * A - B
        prev = -A - last
        if abs(last) <= lim + 1 and abs(prev) <= lim + 1:
            e = e + [prev, last]
            if any(e):
                break
        e = None
    if e is None:
        e = list(patt)
    scale = rnd.choice([1, 1, 2]) if abs(b1) * h >= 3 else 1
    ybar = int(round(float(F["my"]))) + rnd.randint(-4, 4)
    xs = [x0 + h * k for k in range(n)]
    ys = [ybar + b1 * h * (k - c) + scale * e[k] for k in range(n)]
    lift = 0
    if min(ys) < 1:
        lift = int(1 - min(ys)) + 1
    ys = [v + lift for v in ys]
    ys = [int(v) if float(v) == int(v) else float(v) for v in ys]
    return {"x": xs, "y": ys, "xp": xs[-1] + h}
''',
}
EXAMPLES += [
    {"id": "prob-reg-1", "kind": "regression", "topics": ["word problem", "sözel problem"],
     "title": ("Çalışma saati ve sınav puanı", "Study hours and exam score"),
     "q": ("Çalışma saati (x) ve sınav puanı (y) verileri: {pairs}. En küçük kareler doğrusunu, r ve r² "
           "değerlerini bul; {xp} saat çalışan bir öğrencinin puanını tahmin et.",
           "Study hours (x) and exam scores (y): {pairs}. Find the least-squares line, r and r², and "
           "predict the score of a student who studies {xp} hours."),
     "P": {"x": [2, 4, 6, 8, 10], "y": [50, 55, 61, 63, 71], "xp": 7}},
    {"id": "prob-reg-2", "kind": "regression", "topics": ["negative correlation", "negatif korelasyon"],
     "title": ("Araç yaşı ve fiyatı (negatif eğim)", "Car age and price (negative slope)"),
     "q": ("Bir modelin yaşı (x, yıl) ve ikinci el fiyatı (y, bin TL): {pairs}. Regresyon doğrusunu ve "
           "korelasyon katsayısını bul; {xp} yaşındaki bir aracın fiyatını tahmin et.",
           "A car model's age (x, years) and resale price (y, thousands): {pairs}. Find the regression line "
           "and the correlation coefficient, and predict the price of a {xp}-year-old car."),
     "P": {"x": [1, 2, 3, 4, 5, 6, 7], "y": [19, 16, 16, 14, 13, 10, 10], "xp": 8}},
    {"id": "prob-reg-3", "kind": "regression",
     "title": ("Orta kuvvetli ilişki", "A moderate linear relationship"),
     "q": ("Veri noktaları: {pairs}. ŷ = b₀ + b₁x doğrusunu, r ve r² değerlerini ve x = {xp} için tahmini bul.",
           "Data points: {pairs}. Find the line ŷ = b₀ + b₁x, the values of r and r², and the prediction at x = {xp}."),
     "P": {"x": [2, 3, 5, 7, 8], "y": [4, 3, 6, 5, 7], "xp": 6}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["confidence_interval"] = {
    "course": "prob",
    "title": ("Ortalama için güven aralığı", "Confidence interval for a mean"),
    "topics": ["confidence interval", "confidence intervals", "confidence level", "margin of error",
               "interval estimate", "estimating the mean", "estimating a population mean", "z-interval",
               "coverage", "güven aralığı", "güven düzeyi", "hata payı", "aralık tahmini",
               "ortalama için güven aralığı"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Polygon, Rectangle
from matplotlib.collections import LineCollection


def _d(v, k=3):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _invphi(p):
    lo, hi = -10.0, 10.0
    for _ in range(90):
        mid = (lo + hi) / 2
        if _phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _r2(v):
    return f"{v + (1e-9 if v >= 0 else -1e-9):.2f}"


def _iv(xb, me):
    return f"({_r2(xb - me)}, {_r2(xb + me)})"


def _setup(P):
    mu, sg, n = float(P["mu"]), abs(float(P["sigma"])) or 1.0, max(1, int(P["n"]))
    conf = float(P["conf"])
    if conf < 1:
        conf *= 100
    zs = round(_invphi(1 - (1 - conf / 100) / 2), 3)
    se = sg / math.sqrt(n)
    return mu, sg, n, conf, zs, se, zs * se


def _sim(P):
    mu, sg, n, conf, zs, se, me = _setup(P)
    K = max(10, min(80, int(P.get("samples", 50))))
    rng = np.random.default_rng(P.get("seed", 0))
    means = rng.normal(mu, sg, size=(K, n)).mean(axis=1)
    if "xbar" in P:
        means[0] = float(P["xbar"])
    else:
        means[0] = round(float(means[0]), 2)
    longrun = rng.normal(mu, se, size=1000)
    lr = float(np.mean(np.abs(longrun - mu) <= me))
    return means, lr


def solve(P):
    mu, sg, n, conf, zs, se, me = _setup(P)
    means, lr = _sim(P)
    xb = float(means[0])
    lo, hi = xb - me, xb + me
    K = len(means)
    cov = int(np.sum(np.abs(means - mu) <= me))
    al = 1 - conf / 100
    sq = math.sqrt(n)
    sqs = _d(sq) if abs(sq - round(sq)) < 1e-9 else f"{sq:.3f}"
    steps = [("σ bilindiği için z-güven aralığı kullanılır: x̄ ± z*·σ/√n",
              "σ is known, so use the z-interval: x̄ ± z*·σ/√n"),
             (f"Güven düzeyi %{_d(conf)} ⇒ α = {_d(al, 3)} ⇒ z* = z(α/2) = {zs:.3f}",
              f"Confidence level {_d(conf)}% ⇒ α = {_d(al, 3)} ⇒ z* = z(α/2) = {zs:.3f}"),
             (f"Standart hata: σ/√n = {_d(sg)}/√{n} = {_d(sg)}/{sqs} {'=' if abs(se * 1000 - round(se * 1000)) < 1e-9 else '≈'} {_d(se, 4)}",
              f"Standard error: σ/√n = {_d(sg)}/√{n} = {_d(sg)}/{sqs} {'=' if abs(se * 1000 - round(se * 1000)) < 1e-9 else '≈'} {_d(se, 4)}"),
             (f"Hata payı: E = z*·σ/√n = {zs:.3f}·{_d(se, 4)} ≈ {me:.3f}",
              f"Margin of error: E = z*·σ/√n = {zs:.3f}·{_d(se, 4)} ≈ {me:.3f}"),
             (f"Örneklem: x̄ = {_d(xb)} ⇒ {_d(xb)} ± {me:.3f} ⇒ {_iv(xb, me)}",
              f"Sample: x̄ = {_d(xb)} ⇒ {_d(xb)} ± {me:.3f} ⇒ {_iv(xb, me)}"),
             (f"Yorum: Bu yöntemle kurulan her 100 aralıktan uzun vadede yaklaşık {_d(conf)} tanesi gerçek μ değerini kapsar.",
              f"Interpretation: in the long run about {_d(conf)} out of every 100 intervals built this way contain the true μ."),
             (f"Simülasyon (gerçek μ = {_d(mu)}): {K} aralıktan {cov} tanesi μ'yü kapsadı (%{100 * cov / K:.1f}); 1000 aralıkta %{100 * lr:.1f}",
              f"Simulation (true μ = {_d(mu)}): {cov} of {K} intervals contain μ ({100 * cov / K:.1f}%); over 1000 intervals {100 * lr:.1f}%")]
    return {"answer": (f"%{_d(conf)} GA: {_iv(xb, me)};  E ≈ {me:.3f}",
                       f"{_d(conf)}% CI: {_iv(xb, me)};  E ≈ {me:.3f}"),
            "steps": steps, "fmt": {"xbar": _d(xb), "me": f"{me:.3f}"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    mu, sg, n, conf, zs, se, me = _setup(P)
    means, lr = _sim(P)
    K = len(means)
    cover = np.abs(means - mu) <= me
    ccount = np.r_[0, np.cumsum(cover)]
    ext = max(4.6 * se, float(np.max(np.abs(means - mu))) + me + 0.4 * se)
    xl, xr = mu - ext, mu + ext
    gs = fig.add_gridspec(2, 2, width_ratios=[1.9, 1], height_ratios=[1, 3], left=0.035, right=0.985,
                          top=0.9, bottom=0.08, wspace=0.05, hspace=0.08)
    ta = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[1, 0], sharex=ta)
    tp = fig.add_subplot(gs[:, 1])
    tp.axis("off")
    tp.set_xlim(0, 1)
    tp.set_ylim(0, 1)
    gx = np.linspace(xl, xr, 400)
    pk = 1 / (se * math.sqrt(2 * math.pi))
    gy = pk * np.exp(-0.5 * ((gx - mu) / se) ** 2)
    ta.set_xlim(xl, xr)
    ta.set_ylim(0, pk * 1.35)
    ta.set_yticks([])
    ta.tick_params(labelbottom=False)
    for s in ("left", "right", "top"):
        ta.spines[s].set_visible(False)
    tcur, = ta.plot([], [], color="#2563EB", lw=2)
    cx = np.linspace(mu - me, mu + me, 150)
    cpoly = Polygon(np.column_stack([np.r_[cx[0], cx, cx[-1]], np.r_[0, pk * np.exp(-0.5 * ((cx - mu) / se) ** 2), 0]]),
                    closed=True, fc="#16A34A", alpha=0.25, ec="none")
    ta.add_patch(cpoly)
    ctext = ta.text(mu, pk * 0.35, ("%" + _d(conf)) if tr else (_d(conf) + "%"), ha="center", fontsize=10,
                    color="#166534", fontweight="bold")
    xdot, = ta.plot([], [], "o", ms=9, zorder=5)
    ta.text(0.0, 1.0, (r"$\bar{x}$'in örnekleme dağılımı: N(μ, σ/√n)" if tr else
                       r"Sampling distribution of $\bar{x}$: N(μ, σ/√n)"),
            transform=ta.transAxes, fontsize=9.5, va="top", color="#374151")
    ax.set_xlim(xl, xr)
    ax.set_ylim(K + 0.8, 0.2)
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.25)
    ax.axvline(mu, color="#111827", lw=1.4, ls="--", zorder=1)
    ax.text(mu, 0.15, f"μ = {_d(mu)}", ha="center", va="bottom", fontsize=10, color="#111827",
            transform=ax.transData, clip_on=False,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))
    lw = 2.4 if K <= 40 else (1.8 if K <= 60 else 1.4)
    ivs = LineCollection([], linewidths=lw, zorder=3)
    ax.add_collection(ivs)
    cdots = ax.scatter([], [], s=14 if K <= 50 else 9, c="#111827", zorder=4)
    first, = ax.plot([], [], color="#7C3AED", lw=lw + 1.6, solid_capstyle="butt", zorder=5)
    ftext = ax.text(0, 1, "", color="#7C3AED", fontsize=10, fontweight="bold", va="center", ha="left", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    info = fig.text(0.02, 0.975, "", va="top", fontsize=11, bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    xb = float(means[0])
    sq = math.sqrt(n)
    sqs = _d(sq) if abs(sq - round(sq)) < 1e-9 else f"{sq:.2f}"
    rows = [(0, ("Formül (σ biliniyor):" if tr else "Formula (σ known):"), "#374151", 10),
            (0, r"$\bar{x} \pm z^{*}\,\sigma/\sqrt{n}$", "#111827", 13),
            (6, (f"%{_d(conf)} ⇒ " if tr else f"{_d(conf)}% ⇒ ") + r"$z^{*}$ = " + f"{zs:.3f}", "#111827", 10.5),
            (11, r"$\sigma/\sqrt{n}$ = " + f"{_d(sg)}/{sqs} = {_d(se, 4)}", "#111827", 10.5),
            (16, r"E = $z^{*}\sigma/\sqrt{n}$ ≈ " + f"{me:.3f}", "#111827", 10.5),
            (21, r"$\bar{x}$ = " + _d(xb) + " ⇒ " + _iv(xb, me), "#7C3AED", 10.5)]
    rtx = [tp.text(0.03, 0.96 - k * 0.075 - (0.02 if k >= 2 else 0), "", fontsize=fsz, color=c, va="top")
           for k, (f0, t0, c, fsz) in enumerate(rows)]
    tp.plot([0.03, 0.97], [0.47, 0.47], color="#E5E7EB", lw=1)
    ctitle = tp.text(0.03, 0.43, "", fontsize=10.5, va="top", color="#374151")
    cval = tp.text(0.03, 0.35, "", fontsize=14, va="top", fontweight="bold")
    bar_bg = Rectangle((0.03, 0.2), 0.94, 0.05, fc="#F3F4F6", ec="#D1D5DB")
    bar_fg = Rectangle((0.03, 0.2), 0.0, 0.05, fc="#16A34A", ec="none")
    tp.add_patch(bar_bg)
    tp.add_patch(bar_fg)
    tline, = tp.plot([], [], color="#DC2626", lw=2)
    ttext = tp.text(0.03 + 0.94 * conf / 100, 0.27, "", fontsize=9, color="#DC2626", ha="right", va="bottom")
    lrtext = tp.text(0.03, 0.12, "", fontsize=10, va="top", color="#374151")
    N = 160

    def kof(i):
        if i < 24:
            return 0
        if i < 32:
            return 1
        return min(K, 1 + int((i - 32) * (K - 1) / 106.0) + (1 if i >= 138 else 0))

    def update(i):
        m = max(2, int(_ease(i / 14.0) * len(gx)))
        tcur.set_data(gx[:m], gy[:m])
        cpoly.set_visible(i >= 14)
        ctext.set_visible(i >= 14)
        k = kof(i)
        segs, cols = [], []
        for j in range(1, k):
            segs.append([(means[j] - me, j + 1), (means[j] + me, j + 1)])
            cols.append("#16A34A" if cover[j] else "#DC2626")
        ivs.set_segments(segs)
        ivs.set_color(cols if cols else "#16A34A")
        cdots.set_offsets(np.column_stack([means[:k], np.arange(1, k + 1)]) if k else np.empty((0, 2)))
        if k >= 1:
            pr = _ease((i - 24) / 7.0) if i < 32 else 1.0
            first.set_data([xb - me * pr, xb + me * pr], [1, 1])
            if xr - (xb + me) >= (xb - me) - xl:
                ftext.set_position((xb + me + 0.015 * (xr - xl), 1))
                ftext.set_ha("left")
            else:
                ftext.set_position((xb - me - 0.015 * (xr - xl), 1))
                ftext.set_ha("right")
            ftext.set_text(_iv(xb, me) if pr > 0.99 else "")
            last = means[k - 1]
            xdot.set_data([last], [pk * 0.06])
            xdot.set_color("#16A34A" if cover[k - 1] else "#DC2626")
        else:
            first.set_data([], [])
            ftext.set_text("")
            xdot.set_data([], [])
        for (f0, t0, c, fsz), tx in zip(rows, rtx):
            tx.set_text(t0 if i >= f0 else "")
        if k >= 1:
            cc = int(ccount[k])
            rate = cc / k
            ctitle.set_text("Kapsayan aralıklar:" if tr else "Intervals containing μ:")
            cval.set_text(f"{cc}/{k} = " + (f"%{100 * rate:.1f}" if tr else f"{100 * rate:.1f}%"))
            cval.set_color("#16A34A" if rate >= conf / 100 - 0.03 else "#DC2626")
            bar_fg.set_width(0.94 * rate)
            bar_bg.set_visible(True)
            bar_fg.set_visible(True)
            tx0 = 0.03 + 0.94 * conf / 100
            tline.set_data([tx0, tx0], [0.185, 0.265])
            ttext.set_text(("hedef %" + _d(conf)) if tr else ("target " + _d(conf) + "%"))
        else:
            ctitle.set_text("")
            cval.set_text("")
            bar_bg.set_visible(False)
            bar_fg.set_visible(False)
            tline.set_data([], [])
            ttext.set_text("")
        lrtext.set_text((("1000 aralıkta kapsama: %" + f"{100 * lr:.1f}") if tr else
                         ("Coverage over 1000 intervals: " + f"{100 * lr:.1f}%")) if i >= 145 else "")
        if i < 24:
            info.set_text(("1) Formülü kur: hata payı E = z*·σ/√n" if tr else
                           "1) Set up the formula: margin of error E = z*·σ/√n"))
        elif i < 34:
            info.set_text((f"2) Bizim örneklemimiz: x̄ = {_d(xb)} ⇒ {_iv(xb, me)}" if tr else
                           f"2) Our sample: x̄ = {_d(xb)} ⇒ {_iv(xb, me)}"))
        elif i < 140:
            info.set_text(("3) Deneyi tekrarla: her örneklem yeni bir aralık verir (yeşil: μ'yü kapsar, kırmızı: kaçırır)"
                           if tr else "3) Repeat: every sample gives a new interval (green: contains μ, red: misses)"))
        else:
            info.set_text((f"4) Güven düzeyi = uzun vadeli kapsama oranı ≈ %{_d(conf)}" if tr else
                           f"4) Confidence level = long-run coverage rate ≈ {_d(conf)}%"))
        return []

    return N, update


def vary(P, rnd):
    mu0, sg0 = float(P["mu"]), abs(float(P["sigma"]))
    if mu0 >= 20:
        mu = int(round(mu0 * rnd.choice([0.9, 1.0, 1.0, 1.1])))
    else:
        mu = mu0 + rnd.choice([-0.5, 0.0, 0.0, 0.5])
        mu = int(mu) if mu == int(mu) else mu
    sg = sg0 * rnd.choice([0.5, 0.75, 1.0, 1.25, 1.5, 2.0])
    sg = round(sg, 1) if sg0 < 5 else int(round(sg))
    sg = int(sg) if sg == int(sg) else sg
    n = rnd.choice([16, 25, 36, 49, 64, 100])
    conf = rnd.choice([90, 95, 99])
    xbar = round(mu + rnd.uniform(-1.6, 1.6) * sg / math.sqrt(n), 1 if sg0 >= 1 else 2)
    return {"mu": mu, "sigma": sg, "n": n, "conf": conf, "xbar": xbar,
            "samples": rnd.choice([40, 50, 60]), "seed": rnd.randint(1, 9999)}
''',
}
EXAMPLES += [
    {"id": "prob-ci-1", "kind": "confidence_interval",
     "title": ("%95 güven aralığı", "A 95% confidence interval"),
     "q": ("Kitle standart sapması σ = {sigma} olarak biliniyor. n = {n} birimlik bir örneklemin ortalaması "
           "x̄ = {xbar}. μ için %{conf} güven aralığını kur ve ne anlama geldiğini açıkla.",
           "The population standard deviation is known to be σ = {sigma}. A sample of n = {n} has mean "
           "x̄ = {xbar}. Construct a {conf}% confidence interval for μ and explain what it means."),
     "P": {"mu": 50, "sigma": 10, "n": 25, "conf": 95, "xbar": 52.4, "samples": 50, "seed": 7}},
    {"id": "prob-ci-2", "kind": "confidence_interval", "topics": ["word problem", "sözel problem"],
     "title": ("Dolum makinesi (%90)", "Filling machine (90%)"),
     "q": ("Bir dolum makinesi σ = {sigma} ml ile çalışıyor. {n} şişelik bir örneklemde ortalama dolum "
           "{xbar} ml. Ortalama dolum miktarı için %{conf} güven aralığını bul.",
           "A filling machine works with σ = {sigma} ml. A sample of {n} bottles has a mean fill of {xbar} ml. "
           "Find a {conf}% confidence interval for the mean fill."),
     "P": {"mu": 500, "sigma": 6, "n": 36, "conf": 90, "xbar": 498.7, "samples": 50, "seed": 21}},
    {"id": "prob-ci-3", "kind": "confidence_interval", "topics": ["99%", "%99"],
     "title": ("Uyku süresi (%99)", "Hours of sleep (99%)"),
     "q": ("Öğrencilerin gece uyku süresi için σ = {sigma} saat varsayılıyor. {n} öğrencinin ortalaması "
           "{xbar} saat. %{conf} güven aralığını bul ve yorumla.",
           "Assume σ = {sigma} hours for students' nightly sleep. A sample of {n} students averages {xbar} "
           "hours. Find and interpret a {conf}% confidence interval."),
     "P": {"mu": 7, "sigma": 1.2, "n": 16, "conf": 99, "xbar": 6.8, "samples": 50, "seed": 4}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["hypothesis_test"] = {
    "course": "prob",
    "title": ("Ortalama için z-hipotez testi", "z-test for a mean"),
    "topics": ["hypothesis test", "hypothesis testing", "null hypothesis", "alternative hypothesis",
               "z-test", "z test", "p-value", "p value", "significance level", "rejection region",
               "critical value", "one-tailed", "two-tailed", "one-sample z test",
               "hipotez testi", "sıfır hipotezi", "alternatif hipotez", "p-değeri", "p değeri",
               "anlamlılık düzeyi", "red bölgesi", "kritik değer", "tek kuyruklu", "çift kuyruklu"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Polygon, Patch


def _d(v, k=3):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _z(v, k=2):
    s = f"{v:.{k}f}"
    return s.replace("-", "−") if float(s) != 0 else s.replace("-", "")


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _invphi(p):
    lo, hi = -10.0, 10.0
    for _ in range(90):
        mid = (lo + hi) / 2
        if _phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _setup(P):
    mu0, xb = float(P["mu0"]), float(P["xbar"])
    sg, n, al = abs(float(P["sigma"])) or 1.0, max(1, int(P["n"])), float(P["alpha"])
    tl = str(P.get("tail", "two")).strip().lower()
    tail = "left" if tl.startswith(("l", "<", "s")) else ("right" if tl.startswith(("r", ">", "g", "u")) else "two")
    se = sg / math.sqrt(n)
    zraw = (xb - mu0) / se
    z = round(zraw, 2)
    if tail == "two":
        zc = _invphi(1 - al / 2)
        ph = round(_phi(abs(z)), 4)
        p = 2 * (1 - ph)
    elif tail == "right":
        zc = _invphi(1 - al)
        ph = round(_phi(z), 4)
        p = 1 - ph
    else:
        zc = -_invphi(1 - al)
        ph = round(_phi(z), 4)
        p = ph
    p = round(p, 4)
    return {"mu0": mu0, "xb": xb, "sg": sg, "n": n, "al": al, "tail": tail, "se": se, "zraw": zraw, "z": z,
            "zc": zc, "ph": ph, "p": p, "rej": p <= al}


def _ptxt(p):
    return "< 0.0001" if p < 0.0001 else f"= {p:.4f}"


def solve(P):
    T = _setup(P)
    mu0, tail, z, zc = T["mu0"], T["tail"], T["z"], T["zc"]
    h1 = {"two": "≠", "right": ">", "left": "<"}[tail]
    tname = {"two": ("çift kuyruklu", "two-tailed"), "right": ("sağ kuyruklu", "right-tailed"),
             "left": ("sol kuyruklu", "left-tailed")}[tail]
    sq = math.sqrt(T["n"])
    sqs = _d(sq) if abs(sq - round(sq)) < 1e-9 else f"{sq:.3f}"
    seq = "=" if abs(T["se"] * 10000 - round(T["se"] * 10000)) < 1e-9 else "≈"
    zeq = "=" if abs(T["zraw"] - z) < 1e-9 else "≈"
    steps = [(f"H₀: μ = {_d(mu0)}   H₁: μ {h1} {_d(mu0)}  ({tname[0]}), α = {_d(T['al'])}",
              f"H₀: μ = {_d(mu0)}   H₁: μ {h1} {_d(mu0)}  ({tname[1]}), α = {_d(T['al'])}"),
             (f"σ bilindiği için z-testi. Standart hata: SE = σ/√n = {_d(T['sg'])}/√{T['n']} = {_d(T['sg'])}/{sqs} {seq} {_d(T['se'], 4)}",
              f"σ is known, so use a z-test. Standard error: SE = σ/√n = {_d(T['sg'])}/√{T['n']} = {_d(T['sg'])}/{sqs} {seq} {_d(T['se'], 4)}"),
             (f"Test istatistiği: z = (x̄ − μ₀)/SE = ({_d(T['xb'])} − {_d(mu0)})/{_d(T['se'], 4)} {zeq} {_z(z)}",
              f"Test statistic: z = (x̄ − μ₀)/SE = ({_d(T['xb'])} − {_d(mu0)})/{_d(T['se'], 4)} {zeq} {_z(z)}")]
    if tail == "two":
        steps.append((f"Kritik değerler: ±z(α/2) = ±{zc:.3f} ⇒ red bölgesi |z| > {zc:.3f}",
                      f"Critical values: ±z(α/2) = ±{zc:.3f} ⇒ rejection region |z| > {zc:.3f}"))
        pexpr = f"2·P(Z > {_z(abs(z))}) = 2·(1 − {T['ph']:.4f}) {_ptxt(T['p'])}"
    elif tail == "right":
        steps.append((f"Kritik değer: z(α) = {zc:.3f} ⇒ red bölgesi z > {zc:.3f}",
                      f"Critical value: z(α) = {zc:.3f} ⇒ rejection region z > {zc:.3f}"))
        pexpr = f"P(Z > {_z(z)}) = 1 − {T['ph']:.4f} {_ptxt(T['p'])}"
    else:
        steps.append((f"Kritik değer: −z(α) = {_z(zc, 3)} ⇒ red bölgesi z < {_z(zc, 3)}",
                      f"Critical value: −z(α) = {_z(zc, 3)} ⇒ rejection region z < {_z(zc, 3)}"))
        pexpr = f"P(Z < {_z(z)}) {_ptxt(T['p'])}"
    steps.append((f"p-değeri = {pexpr}", f"p-value = {pexpr}"))
    ps = _ptxt(T["p"]).replace("= ", "")
    if T["rej"]:
        steps.append((f"Karar: p = {ps} ≤ α = {_d(T['al'])} ⇒ H₀ reddedilir (z red bölgesinde)",
                      f"Decision: p = {ps} ≤ α = {_d(T['al'])} ⇒ reject H₀ (z is in the rejection region)"))
        steps.append((f"Sonuç: α = {_d(T['al'])} düzeyinde μ {h1} {_d(mu0)} için yeterli kanıt vardır.",
                      f"Conclusion: at α = {_d(T['al'])} there is enough evidence that μ {h1} {_d(mu0)}."))
        ans = (f"z = {_z(z)}, p {_ptxt(T['p'])} ≤ {_d(T['al'])} ⇒ H₀ reddedilir",
               f"z = {_z(z)}, p {_ptxt(T['p'])} ≤ {_d(T['al'])} ⇒ reject H₀")
    else:
        steps.append((f"Karar: p = {ps} > α = {_d(T['al'])} ⇒ H₀ reddedilemez (z red bölgesinde değil)",
                      f"Decision: p = {ps} > α = {_d(T['al'])} ⇒ fail to reject H₀ (z is not in the rejection region)"))
        steps.append((f"Sonuç: α = {_d(T['al'])} düzeyinde μ {h1} {_d(mu0)} iddiasını destekleyen yeterli kanıt yok.",
                      f"Conclusion: at α = {_d(T['al'])} there is not enough evidence that μ {h1} {_d(mu0)}."))
        ans = (f"z = {_z(z)}, p {_ptxt(T['p'])} > {_d(T['al'])} ⇒ H₀ reddedilemez",
               f"z = {_z(z)}, p {_ptxt(T['p'])} > {_d(T['al'])} ⇒ fail to reject H₀")
    return {"answer": ans, "steps": steps, "fmt": {"h1": f"μ {h1} {_d(mu0)}"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = _setup(P)
    mu0, se, z, zc, tail, al, p = T["mu0"], T["se"], T["z"], T["zc"], T["tail"], T["al"], T["p"]
    zl = max(4.0, abs(z) + 0.7)
    gx = np.linspace(-zl, zl, 500)

    def pdf(x):
        return np.exp(-0.5 * np.asarray(x, dtype=float) ** 2) / math.sqrt(2 * math.pi)

    gy = pdf(gx)
    gs = fig.add_gridspec(1, 2, width_ratios=[2.15, 1], left=0.04, right=0.985, top=0.76, bottom=0.11, wspace=0.06)
    ax = fig.add_subplot(gs[0, 0])
    tp = fig.add_subplot(gs[0, 1])
    tp.axis("off")
    tp.set_xlim(0, 1)
    tp.set_ylim(0, 1)
    ax.set_xlim(-zl, zl)
    ax.set_ylim(-0.06, 0.47)
    ax.set_yticks([])
    for s in ("left", "right"):
        ax.spines[s].set_visible(False)
    ax.axhline(0, color="#374151", lw=1)
    ax.set_xticks(list(range(-int(zl), int(zl) + 1)))
    ax.set_xlabel("z", fontsize=10, labelpad=1)

    def to_x(v):
        return mu0 + v * se

    def to_z(v):
        return (v - mu0) / se

    sec = ax.secondary_xaxis("top", functions=(to_x, to_z))
    sec.set_xticks([mu0 + k * se for k in range(-3, 4)])
    sec.set_xticklabels([_d(mu0 + k * se, 2) for k in range(-3, 4)], fontsize=8.5)
    sec.set_xlabel(r"$\bar{x}$", fontsize=10, labelpad=2)
    curve, = ax.plot([], [], color="#2563EB", lw=2.5, zorder=4)
    rej = [Polygon(np.zeros((3, 2)), closed=True, fc="#DC2626", alpha=0.35, ec="none", zorder=1) for _ in range(2)]
    pav = [Polygon(np.zeros((3, 2)), closed=True, fc="#E07B39", alpha=0.35, ec="#C2410C", hatch="///", lw=0.8,
                   zorder=2) for _ in range(2)]
    for pg in rej + pav:
        ax.add_patch(pg)
    clines, = ax.plot([], [], "--", color="#DC2626", lw=1.6, zorder=3)
    ctexts = [ax.text(0, -0.03, "", color="#DC2626", fontsize=9.5, ha="center", va="top") for _ in range(2)]
    zline, = ax.plot([], [], color="#7C3AED", lw=2.4, zorder=5)
    zmark, = ax.plot([], [], "^", color="#7C3AED", ms=9, zorder=6)
    ztext = ax.text(0, 0, "", color="#7C3AED", fontsize=11, fontweight="bold", ha="center", va="bottom", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    leg = ax.legend(handles=[Patch(fc="#DC2626", alpha=0.35, label="r"),
                             Patch(fc="#E07B39", alpha=0.35, ec="#C2410C", hatch="///", label="p")],
                    loc="upper right", fontsize=9, framealpha=0.95)
    ltx = leg.get_texts()
    info = fig.text(0.02, 0.975, "", va="top", fontsize=11, bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    h1 = {"two": "≠", "right": ">", "left": "<"}[tail]
    tname = {"two": ("çift kuyruk", "two-tailed"), "right": ("sağ kuyruk", "right-tailed"),
             "left": ("sol kuyruk", "left-tailed")}[tail]
    sq = math.sqrt(T["n"])
    sqs = _d(sq) if abs(sq - round(sq)) < 1e-9 else f"{sq:.2f}"
    if tail == "two":
        crit = f"|z| > {zc:.3f}"
        pform = f"p = 2·P(Z > {_z(abs(z))})"
    elif tail == "right":
        crit = f"z > {zc:.3f}"
        pform = f"p = P(Z > {_z(z)})"
    else:
        crit = f"z < {_z(zc, 3)}"
        pform = f"p = P(Z < {_z(z)})"
    rows = [(0, f"H₀: μ = {_d(mu0)}", "#111827", 11),
            (5, f"H₁: μ {h1} {_d(mu0)}", "#111827", 11),
            (9, f"α = {_d(al)}  ({tname[0] if tr else tname[1]})", "#111827", 10.5),
            (24, ("red: " if tr else "reject if ") + crit, "#DC2626", 10.5),
            (52, r"SE = $\sigma/\sqrt{n}$ = " + f"{_d(T['sg'])}/√{T['n']} = {_d(se, 4)}", "#111827", 10.5),
            (60, r"z = $(\bar{x}-\mu_0)/SE$", "#7C3AED", 10.5),
            (64, f"   = ({_d(T['xb'])} − {_d(mu0)})/{_d(se, 4)} = {_z(z)}", "#7C3AED", 10.5),
            (84, pform, "#C2410C", 10.5),
            (114, "   " + _ptxt(p), "#C2410C", 11)]
    rtx = [tp.text(0.02, 0.97 - k * 0.083, "", fontsize=fsz, color=c, va="top") for k, (f0, t0, c, fsz) in enumerate(rows)]
    dec1 = tp.text(0.02, 0.17, "", fontsize=11, va="top", color="#111827")
    dec2 = tp.text(0.02, 0.08, "", fontsize=12.5, va="top", fontweight="bold")
    if tail == "two":
        rtails = [(-zl, -zc), (zc, zl)]
        ptails = [(-zl, -abs(z)), (abs(z), zl)]
    elif tail == "right":
        rtails, ptails = [(zc, zl)], [(z, zl)]
    else:
        rtails, ptails = [(-zl, zc)], [(-zl, z)]
    N = 150

    def region(x0, x1):
        sx = np.linspace(x0, max(x1, x0 + 1e-9), 100)
        return np.column_stack([np.r_[x0, sx, sx[-1]], np.r_[0, pdf(sx), 0]])

    def update(i):
        m = max(2, int(_ease(i / 18.0) * len(gx)))
        curve.set_data(gx[:m], gy[:m])
        tr_ = _ease((i - 22) / 26.0)
        for k in range(2):
            if k < len(rtails) and i >= 22:
                a0, a1 = rtails[k]
                if a0 <= -zl + 1e-9:
                    rej[k].set_xy(region(a0, a0 + (a1 - a0) * tr_))
                else:
                    rej[k].set_xy(region(a1 - (a1 - a0) * tr_, a1))
                rej[k].set_visible(True)
            else:
                rej[k].set_visible(False)
        if i >= 46:
            cz = [-zc, zc] if tail == "two" else [zc]
            xx, yy = [], []
            for c in cz:
                xx += [c, c, np.nan]
                yy += [0, float(pdf(c)) + 0.05, np.nan]
            clines.set_data(xx, yy)
            for k in range(2):
                if k < len(cz):
                    ctexts[k].set_position((cz[k], -0.006))
                    ctexts[k].set_text(_z(cz[k], 3))
                else:
                    ctexts[k].set_text("")
        else:
            clines.set_data([], [])
            for t in ctexts:
                t.set_text("")
        if i >= 52:
            zt = z * _ease((i - 52) / 24.0)
            zline.set_data([zt, zt], [0, float(pdf(zt))])
            zmark.set_data([zt], [0.009])
            ztext.set_position((zt, float(pdf(zt)) + 0.015))
            ztext.set_text(f"z = {_z(zt)}")
        else:
            zline.set_data([], [])
            zmark.set_data([], [])
            ztext.set_text("")
        tp_ = _ease((i - 84) / 28.0)
        for k in range(2):
            if k < len(ptails) and i >= 84:
                a0, a1 = ptails[k]
                if a0 <= -zl + 1e-9:
                    pav[k].set_xy(region(a1 - (a1 - a0) * tp_, a1))
                else:
                    pav[k].set_xy(region(a0, a0 + (a1 - a0) * tp_))
                pav[k].set_visible(True)
            else:
                pav[k].set_visible(False)
        leg.set_visible(i >= 22)
        ltx[0].set_text((f"red bölgesi (α = {_d(al)})" if tr else f"rejection region (α = {_d(al)})"))
        if i >= 84:
            if i >= 112:
                pv = _ptxt(p).replace("= ", "")
            else:
                cur = 0.0
                for a0, a1 in ptails:
                    if a0 <= -zl + 1e-9:
                        cur += _phi(a1) - _phi(a1 - (a1 - a0) * tp_)
                    else:
                        cur += _phi(a0 + (a1 - a0) * tp_) - _phi(a0)
                pv = f"{cur:.4f}"
            ltx[1].set_text(("p-değeri alanı = " if tr else "p-value area = ") + pv)
        else:
            ltx[1].set_text(("p-değeri alanı" if tr else "p-value area"))
        for (f0, t0, c, fsz), tx in zip(rows, rtx):
            tx.set_text(t0 if i >= f0 else "")
        ps = _ptxt(p).replace("= ", "")
        if i >= 120:
            dec1.set_text((f"p = {ps} ≤ α = {_d(al)}" if T["rej"] else f"p = {ps} > α = {_d(al)}"))
            dec2.set_text(("H₀ reddedilir" if tr else "Reject H₀") if T["rej"] else
                          ("H₀ reddedilemez" if tr else "Fail to reject H₀"))
            dec2.set_color("#DC2626" if T["rej"] else "#16A34A")
        else:
            dec1.set_text("")
            dec2.set_text("")
        if i < 22:
            info.set_text((f"1) H₀ doğruysa z ~ N(0, 1).  H₀: μ = {_d(mu0)},  H₁: μ {h1} {_d(mu0)}" if tr else
                           f"1) If H₀ is true, z ~ N(0, 1).  H₀: μ = {_d(mu0)},  H₁: μ {h1} {_d(mu0)}"))
        elif i < 52:
            info.set_text((f"2) Red bölgesi: alanı α = {_d(al)} olan kuyruk(lar)" if tr else
                           f"2) Rejection region: tail area(s) totalling α = {_d(al)}"))
        elif i < 84:
            info.set_text((f"3) Test istatistiği: z = (x̄ − μ₀)/(σ/√n) = {_z(z)}" if tr else
                           f"3) Test statistic: z = (x̄ − μ₀)/(σ/√n) = {_z(z)}"))
        elif i < 120:
            info.set_text(("4) p-değeri: z kadar veya daha uç sonuç alma olasılığı" if tr else
                           "4) p-value: probability of a result at least as extreme as z"))
        else:
            info.set_text(("5) Karar: " if tr else "5) Decision: ") +
                          (f"p = {ps} {'≤' if T['rej'] else '>'} α = {_d(al)} ⇒ " +
                           (("H₀ reddedilir" if tr else "reject H₀") if T["rej"] else
                            ("H₀ reddedilemez" if tr else "fail to reject H₀"))))
        return []

    return N, update


def vary(P, rnd):
    T = _setup(P)
    tail = T["tail"]
    mu0 = T["mu0"]
    mu0 = int(round(mu0 * rnd.choice([0.8, 1.0, 1.25]))) if mu0 >= 10 else mu0
    al = rnd.choice([0.01, 0.05, 0.05, 0.10])
    n = rnd.choice([16, 25, 36, 49, 64, 100])
    se = rnd.choice([0.5, 1.0, 1.5, 2.0, 2.5])
    if mu0 < 30:
        se = rnd.choice([0.2, 0.4, 0.5, 0.6])
    from_crit = {"two": _invphi(1 - al / 2), "right": _invphi(1 - al), "left": _invphi(1 - al)}[tail]
    zs = [v for v in (0.8, 1.2, 1.4, 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0) if abs(v - from_crit) > 0.12]
    z = rnd.choice(zs)
    if tail == "left":
        z = -z
    elif tail == "two" and rnd.random() < 0.5:
        z = -z
    sg = round(se * math.sqrt(n), 2)
    sg = int(sg) if sg == int(sg) else sg
    xbar = round(mu0 + z * se, 2)
    return {"mu0": mu0, "xbar": xbar, "sigma": sg, "n": n, "alpha": al, "tail": tail}
''',
}
EXAMPLES += [
    {"id": "prob-ztest-1", "kind": "hypothesis_test",
     "title": ("Çift kuyruklu z-testi", "Two-tailed z-test"),
     "q": ("Bir yetenek testinin ortalamasının μ₀ = {mu0} olduğu iddia ediliyor (σ = {sigma}). n = {n} kişilik bir "
           "örneklemde x̄ = {xbar} bulundu. α = {alpha} düzeyinde H₀: μ = {mu0} hipotezini H₁: {h1} karşısında test et.",
           "An aptitude test is claimed to have mean μ₀ = {mu0} (σ = {sigma}). A sample of n = {n} gives "
           "x̄ = {xbar}. At α = {alpha}, test H₀: μ = {mu0} against H₁: {h1}."),
     "P": {"mu0": 100, "xbar": 104.5, "sigma": 15, "n": 36, "alpha": 0.05, "tail": "two"}},
    {"id": "prob-ztest-2", "kind": "hypothesis_test", "topics": ["right-tailed", "sağ kuyruklu", "word problem"],
     "title": ("Sağ kuyruklu test: gübre verimi", "Right-tailed test: fertilizer yield"),
     "q": ("Yeni bir gübrenin ortalama verimi {mu0} kg'ın üzerine çıkardığı iddia ediliyor (σ = {sigma} kg). "
           "{n} parselde ortalama verim {xbar} kg ölçüldü. α = {alpha} düzeyinde H₁: {h1} iddiasını test et.",
           "A new fertilizer is claimed to raise the mean yield above {mu0} kg (σ = {sigma} kg). On {n} plots the "
           "mean yield is {xbar} kg. Test the claim H₁: {h1} at α = {alpha}."),
     "P": {"mu0": 20, "xbar": 21.2, "sigma": 3, "n": 25, "alpha": 0.05, "tail": "right"}},
    {"id": "prob-ztest-3", "kind": "hypothesis_test", "topics": ["left-tailed", "sol kuyruklu", "claim"],
     "title": ("Sol kuyruklu test: pil ömrü", "Left-tailed test: battery life"),
     "q": ("Bir üretici pillerinin ortalama ömrünün {mu0} saat olduğunu söylüyor (σ = {sigma} saat). {n} pilin "
           "ortalaması {xbar} saat. α = {alpha} ile ortalamanın daha düşük olup olmadığını (H₁: {h1}) test et.",
           "A maker says its batteries last {mu0} hours on average (σ = {sigma} hours). A sample of {n} batteries "
           "averages {xbar} hours. At α = {alpha}, test whether the mean is lower (H₁: {h1})."),
     "P": {"mu0": 40, "xbar": 38.5, "sigma": 4.2, "n": 49, "alpha": 0.01, "tail": "left"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["chi_square"] = {
    "course": "prob",
    "title": ("Ki-kare testi: uyum iyiliği ve bağımsızlık", "Chi-square test: goodness of fit and independence"),
    "topics": ["chi-square", "chi square", "chi-squared", "goodness of fit", "goodness-of-fit",
               "test of independence", "independence test", "contingency table", "two-way table",
               "observed and expected", "ki-kare", "ki kare", "uyum iyiliği", "bağımsızlık testi",
               "çapraz tablo", "olumsallık tablosu", "gözlenen ve beklenen"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.patches import Polygon, Rectangle


def _d(v, k=3):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _eq(v):
    v = Fraction(v)
    return ("= " if (v * 1000).denominator == 1 else "≈ ") + _d(v)


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _gammp(s, x):
    if x <= 0:
        return 0.0
    if x < s + 1:
        term = 1.0 / s
        total = term
        a = s
        for _ in range(1000):
            a += 1
            term *= x / a
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    b = x + 1 - s
    c = 1e300
    d = 1 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - s)
        b += 2
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return 1 - math.exp(-x + s * math.log(x) - math.lgamma(s)) * h


def _cdf(x, k):
    return _gammp(k / 2.0, x / 2.0)


def _crit(al, k):
    lo, hi = 0.0, 400.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if _cdf(mid, k) < 1 - al:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _pdf(x, k):
    x = np.asarray(x, dtype=float)
    h = k / 2.0
    out = np.zeros_like(x)
    m = x > 0
    out[m] = np.exp((h - 1) * np.log(x[m]) - x[m] / 2 - h * math.log(2) - math.lgamma(h))
    return out


def _lab(v, tr):
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return str(v[0] if tr else v[1])
    return str(v)


def _data(P):
    obs = P["observed"]
    al = float(P.get("alpha", 0.05))
    if isinstance(obs[0], (list, tuple)):
        O = [[Fraction(int(v)) for v in row] for row in obs]
        r, c = len(O), len(O[0])
        rt = [sum(row) for row in O]
        ct = [sum(O[i][j] for i in range(r)) for j in range(c)]
        N = sum(rt)
        E = [[rt[i] * ct[j] / N for j in range(c)] for i in range(r)]
        C = [[(O[i][j] - E[i][j]) ** 2 / E[i][j] for j in range(c)] for i in range(r)]
        chi = sum(sum(row) for row in C)
        df = (r - 1) * (c - 1)
        return {"mode": "ind", "O": O, "E": E, "C": C, "rt": rt, "ct": ct, "N": N, "r": r, "c": c,
                "chi": chi, "df": df, "al": al}
    O = [Fraction(int(v)) for v in obs]
    k = len(O)
    ratio = P.get("ratio") or [1] * k
    ratio = [Fraction(str(v)) if isinstance(v, float) else Fraction(v) for v in ratio]
    N = sum(O)
    E = [N * q / sum(ratio) for q in ratio]
    C = [(o - e) ** 2 / e for o, e in zip(O, E)]
    return {"mode": "gof", "O": O, "E": E, "C": C, "N": N, "k": k, "ratio": ratio, "chi": sum(C),
            "df": k - 1, "al": al}


def _result(D):
    chi = float(D["chi"])
    df = D["df"]
    crit = _crit(D["al"], df)
    p = 1 - _cdf(chi, df)
    return chi, crit, p, p <= D["al"]


def _ps(p):
    return "< 0.0001" if p < 0.0001 else f"≈ {p:.4f}"


def solve(P):
    D = _data(P)
    chi, crit, p, rej = _result(D)
    al, df = D["al"], D["df"]
    if D["mode"] == "gof":
        rs = ":".join(_d(q) for q in D["ratio"])
        es = ", ".join(_d(e) for e in D["E"])
        terms = " + ".join(f"({_d(o)} − {_d(e)})²/{_d(e)}" for o, e in zip(D["O"], D["E"]))
        cs = " + ".join(_d(c) for c in D["C"])
        steps = [(f"H₀: veriler iddia edilen oranlara uyar ({rs});  H₁: uymaz",
                  f"H₀: the data follow the claimed proportions ({rs});  H₁: they do not"),
                 (f"Toplam N = {_d(D['N'])};  beklenen E = N·pᵢ ⇒ {es}",
                  f"Total N = {_d(D['N'])};  expected E = N·pᵢ ⇒ {es}"),
                 (f"χ² = Σ(O − E)²/E = {terms}", f"χ² = Σ(O − E)²/E = {terms}"),
                 (f"   = {cs} {_eq(D['chi'])}", f"   = {cs} {_eq(D['chi'])}"),
                 (f"Serbestlik derecesi: sd = k − 1 = {D['k']} − 1 = {df}",
                  f"Degrees of freedom: df = k − 1 = {D['k']} − 1 = {df}")]
    else:
        r, c = D["r"], D["c"]
        rts = ", ".join(_d(v) for v in D["rt"])
        cts = ", ".join(_d(v) for v in D["ct"])
        etab = " / ".join("[" + ", ".join(_d(e) for e in row) + "]" for row in D["E"])
        ctab = " + ".join(_d(v) for row in D["C"] for v in row)
        steps = [("H₀: satır ve sütun değişkenleri bağımsızdır;  H₁: bağımlıdır",
                  "H₀: the row and column variables are independent;  H₁: they are associated"),
                 (f"Satır toplamları: {rts};  sütun toplamları: {cts};  N = {_d(D['N'])}",
                  f"Row totals: {rts};  column totals: {cts};  N = {_d(D['N'])}"),
                 (f"Beklenen: E = (satır toplamı × sütun toplamı)/N, ör. E₁₁ = {_d(D['rt'][0])}·{_d(D['ct'][0])}/{_d(D['N'])} {_eq(D['E'][0][0])}",
                  f"Expected: E = (row total × column total)/N, e.g. E₁₁ = {_d(D['rt'][0])}·{_d(D['ct'][0])}/{_d(D['N'])} {_eq(D['E'][0][0])}"),
                 (f"Beklenen tablo: {etab}", f"Expected table: {etab}"),
                 (f"χ² = Σ(O − E)²/E = {ctab} {_eq(D['chi'])}", f"χ² = Σ(O − E)²/E = {ctab} {_eq(D['chi'])}"),
                 (f"Serbestlik derecesi: sd = (r − 1)(c − 1) = ({r} − 1)({c} − 1) = {df}",
                  f"Degrees of freedom: df = (r − 1)(c − 1) = ({r} − 1)({c} − 1) = {df}")]
    steps.append((f"Kritik değer (α = {_d(al)}): χ²({_d(al)}; {df}) = {crit:.3f}",
                  f"Critical value (α = {_d(al)}): χ²({_d(al)}; {df}) = {crit:.3f}"))
    steps.append((f"p-değeri = P(χ²_{df} > {chi:.3f}) {_ps(p)}", f"p-value = P(χ²_{df} > {chi:.3f}) {_ps(p)}"))
    if rej:
        steps.append((f"Karar: χ² = {chi:.3f} > {crit:.3f} (p ≤ α) ⇒ H₀ reddedilir",
                      f"Decision: χ² = {chi:.3f} > {crit:.3f} (p ≤ α) ⇒ reject H₀"))
        ans = (f"χ² {_eq(D['chi'])}, sd = {df}, p {_ps(p)} ⇒ H₀ reddedilir",
               f"χ² {_eq(D['chi'])}, df = {df}, p {_ps(p)} ⇒ reject H₀")
    else:
        steps.append((f"Karar: χ² = {chi:.3f} < {crit:.3f} (p > α) ⇒ H₀ reddedilemez",
                      f"Decision: χ² = {chi:.3f} < {crit:.3f} (p > α) ⇒ fail to reject H₀"))
        ans = (f"χ² {_eq(D['chi'])}, sd = {df}, p {_ps(p)} ⇒ H₀ reddedilemez",
               f"χ² {_eq(D['chi'])}, df = {df}, p {_ps(p)} ⇒ fail to reject H₀")
    fmt = {"N": _d(D["N"]), "df": str(df)}
    if D["mode"] == "gof":
        fmt["ratio_s"] = ":".join(_d(q) for q in D["ratio"])
        labs = P.get("labels") or [str(k + 1) for k in range(D["k"])]
        fmt["labels_s"] = (", ".join(_lab(v, True) for v in labs), ", ".join(_lab(v, False) for v in labs))
    else:
        fmt["table"] = " / ".join("[" + ", ".join(_d(v) for v in row) + "]" for row in D["O"])
    return {"answer": ans, "steps": steps, "fmt": fmt}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    D = _data(P)
    chi, crit, p, rej = _result(D)
    al, df = D["al"], D["df"]
    gs = fig.add_gridspec(2, 2, width_ratios=[1.3, 1], height_ratios=[1.25, 1], left=0.06, right=0.985,
                          top=0.86, bottom=0.08, wspace=0.16, hspace=0.3)
    lx = fig.add_subplot(gs[:, 0])
    cx = fig.add_subplot(gs[0, 1])
    tp = fig.add_subplot(gs[1, 1])
    tp.axis("off")
    tp.set_xlim(0, 1)
    tp.set_ylim(0, 1)
    info = fig.text(0.02, 0.975, "", va="top", fontsize=11, bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    # chi-square curve
    xmax = max(crit * 1.6, chi * 1.25, df + 4 * math.sqrt(2 * df), 6.0)
    gx = np.linspace(xmax / 600, xmax, 500)
    gy = _pdf(gx, df)
    yref = float(_pdf(np.array([max(0.35, df - 2.0)]), df)[0]) if df <= 2 else float(gy.max())
    cx.set_xlim(0, xmax)
    cx.set_ylim(0, yref * 1.35)
    cx.set_yticks([])
    for s in ("left", "right", "top"):
        cx.spines[s].set_visible(False)
    cx.set_title((f"Ki-kare dağılımı, sd = {df}" if tr else f"Chi-square distribution, df = {df}"), fontsize=10)
    cx.tick_params(labelsize=8.5)
    ccurve, = cx.plot([], [], color="#2563EB", lw=2.2, zorder=4)
    rpoly = Polygon(np.zeros((3, 2)), closed=True, fc="#DC2626", alpha=0.35, ec="none", zorder=1)
    ppoly = Polygon(np.zeros((3, 2)), closed=True, fc="#E07B39", alpha=0.35, ec="#C2410C", hatch="///", lw=0.8, zorder=2)
    cx.add_patch(rpoly)
    cx.add_patch(ppoly)
    crl, = cx.plot([], [], "--", color="#DC2626", lw=1.5)
    crt = cx.text(crit, 0, "", color="#DC2626", fontsize=9, ha="left", va="bottom")
    chl, = cx.plot([], [], color="#7C3AED", lw=2.4, zorder=5)
    chm, = cx.plot([], [], "^", color="#7C3AED", ms=10, zorder=6, clip_on=False)
    cht = cx.text(0, 0, "", color="#7C3AED", fontsize=10, fontweight="bold", ha="center", va="bottom", zorder=6,
                  bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    ylim_c = yref * 1.35

    def region(x0, x1):
        sx = np.linspace(x0, max(x1, x0 + 1e-9), 120)
        return np.column_stack([np.r_[x0, sx, sx[-1]], np.r_[0, np.minimum(_pdf(sx, df), ylim_c), 0]])

    rows = [(100, (f"sd = {df}", f"df = {df}"), "#111827", 10.5),
            (104, (f"kritik değer (α = {_d(al)}) = {crit:.3f}", f"critical value (α = {_d(al)}) = {crit:.3f}"), "#DC2626", 10.5),
            (128, (f"p-değeri {_ps(p)}", f"p-value {_ps(p)}"), "#C2410C", 10.5)]
    rtx = [tp.text(0.02, 0.6 - k * 0.12, "", fontsize=fsz, color=c, va="top") for k, (f0, t0, c, fsz) in enumerate(rows)]
    dec = tp.text(0.02, 0.24, "", fontsize=11.5, fontweight="bold", va="top")
    chisum = tp.text(0.02, 0.98, "", fontsize=10.5, va="top", color="#7C3AED")

    if D["mode"] == "gof":
        k = D["k"]
        O = [float(v) for v in D["O"]]
        E = [float(v) for v in D["E"]]
        C = [float(v) for v in D["C"]]
        labs = P.get("labels") or [str(j + 1) for j in range(k)]
        labs = [_lab(v, tr) for v in labs]
        top = max(max(O), max(E)) * 1.45
        lx.set_xlim(-0.6, k - 0.4)
        lx.set_ylim(0, top)
        lx.set_xticks(range(k))
        lx.set_xticklabels(labs, fontsize=9.5)
        lx.grid(axis="y", alpha=0.3)
        for s in ("right", "top"):
            lx.spines[s].set_visible(False)
        ob = lx.bar(np.arange(k) - 0.2, [0] * k, width=0.38, color="#2563EB", label=("gözlenen O" if tr else "observed O"))
        eb = lx.bar(np.arange(k) + 0.2, [0] * k, width=0.38, color="#E07B39", alpha=0.55, hatch="//", ec="#C2410C",
                    label=("beklenen E" if tr else "expected E"))
        lx.legend(loc="upper right", fontsize=9)
        otx = [lx.text(j - 0.2, 0, "", ha="center", va="bottom", fontsize=9, color="#1E3A8A") for j in range(k)]
        etx = [lx.text(j + 0.2, 0, "", ha="center", va="bottom", fontsize=9, color="#9A3412") for j in range(k)]
        ctx = [lx.text(j, top * 0.8, "", ha="center", va="center", fontsize=9.5, color="#7C3AED", fontweight="bold",
                       bbox=dict(boxstyle="round,pad=0.15", fc="#F5F3FF", ec="#C4B5FD")) for j in range(k)]
        chdr = lx.text(0.01, 0.87, "", transform=lx.transAxes, fontsize=9.5, color="#7C3AED", va="bottom")
        ncell = k
    else:
        r, c = D["r"], D["c"]
        O = [[float(v) for v in row] for row in D["O"]]
        E = [[float(v) for v in row] for row in D["E"]]
        C = [[float(v) for v in row] for row in D["C"]]
        rl = [_lab(v, tr) for v in (P.get("rows") or [f"R{i + 1}" for i in range(r)])]
        cl = [_lab(v, tr) for v in (P.get("cols") or [f"C{j + 1}" for j in range(c)])]
        lx.axis("off")
        lx.set_xlim(0, 2.25 + c)
        lx.set_ylim(1.95 + r, -0.05)
        cmax = max(max(row) for row in C) or 1.0
        bgs, otx, etx, ctx = [], [], [], []
        for i in range(r):
            for j in range(c):
                rc = Rectangle((1.2 + j, 0.85 + i), 1, 1, fc="#7C3AED", alpha=0.0, ec="#9CA3AF", lw=1)
                lx.add_patch(rc)
                bgs.append(rc)
                otx.append(lx.text(1.7 + j, 1.18 + i, "", ha="center", va="center", fontsize=14, fontweight="bold",
                                   color="#1E3A8A"))
                etx.append(lx.text(1.7 + j, 1.5 + i, "", ha="center", va="center", fontsize=9, color="#9A3412"))
                ctx.append(lx.text(1.7 + j, 1.74 + i, "", ha="center", va="center", fontsize=9.5, color="#6D28D9",
                                   fontweight="bold"))
        for j in range(c):
            lx.text(1.7 + j, 0.62, cl[j], ha="center", va="center", fontsize=10, fontweight="bold")
        for i in range(r):
            lx.text(1.12, 1.35 + i, rl[i], ha="right", va="center", fontsize=10, fontweight="bold")
        lx.text(1.7 + c, 0.62, ("Toplam" if tr else "Total"), ha="center", va="center", fontsize=10, color="#6B7280")
        lx.text(1.12, 1.35 + r, ("Toplam" if tr else "Total"), ha="right", va="center", fontsize=10, color="#6B7280")
        tots = []
        for i in range(r):
            tots.append(lx.text(1.7 + c, 1.35 + i, "", ha="center", va="center", fontsize=11, color="#374151"))
        for j in range(c):
            tots.append(lx.text(1.7 + j, 1.35 + r, "", ha="center", va="center", fontsize=11, color="#374151"))
        tots.append(lx.text(1.7 + c, 1.35 + r, "", ha="center", va="center", fontsize=11, fontweight="bold"))
        tvals = [_d(v) for v in D["rt"]] + [_d(v) for v in D["ct"]] + [_d(D["N"])]
        leg = lx.text(0.02, 0.0, "", transform=lx.transAxes, fontsize=9, va="bottom", color="#374151")
        ncell = r * c
    cum = [0.0]
    flat_c = C if D["mode"] == "gof" else [v for row in C for v in row]
    for v in flat_c:
        cum.append(cum[-1] + v)
    N = 170

    def update(i):
        if D["mode"] == "gof":
            g = _ease(i / 22.0)
            for j in range(k):
                ob[j].set_height(O[j] * g)
                otx[j].set_position((j - 0.2, O[j] * g + top * 0.01))
                otx[j].set_text(_d(O[j]) if i >= 20 else "")
                ge = _ease((i - 25) / 20.0)
                eb[j].set_height(E[j] * ge)
                etx[j].set_position((j + 0.2, E[j] * ge + top * 0.01))
                etx[j].set_text(_d(E[j], 2) if i >= 45 else "")
                ctx[j].set_text(_d(C[j], 2) if i >= 52 + j * 46.0 / k else "")
                ctx[j].set_visible(i >= 52 + j * 46.0 / k)
            chdr.set_text(r"$(O-E)^2/E$:" if i >= 52 else "")
        else:
            for q in range(ncell):
                ii, jj = divmod(q, c)
                otx[q].set_text(_d(O[ii][jj]) if i >= 2 + q * 18.0 / ncell else "")
                etx[q].set_text(("E = " + _d(E[ii][jj], 2)) if i >= 25 + q * 25.0 / ncell else "")
                on = i >= 52 + q * 46.0 / ncell
                ctx[q].set_text(_d(C[ii][jj], 2) if on else "")
                bgs[q].set_alpha((0.06 + 0.42 * C[ii][jj] / cmax) if on else 0.0)
            for t, v in zip(tots, tvals):
                t.set_text(v if i >= 20 else "")
            leg.set_text(("büyük sayı: gözlenen O · turuncu: beklenen E\nmor: hücre katkısı (O − E)²/E" if tr else
                          "big number: observed O · orange: expected E\npurple: cell contribution (O − E)²/E")
                         if i >= 25 else "")
        m = max(2, int(_ease((i - 6) / 20.0) * len(gx)))
        ccurve.set_data(gx[:m], np.minimum(gy[:m], ylim_c))
        nc = 0
        if i >= 52:
            nc = min(ncell, int((i - 52) * ncell / 46.0) + 1)
        cur = cum[nc]
        if i >= 52:
            chl.set_data([cur, cur], [0, min(float(_pdf(np.array([max(cur, 1e-6)]), df)[0]), ylim_c)])
            chm.set_data([cur], [0])
            cht.set_position((min(cur, xmax * 0.92), min(float(_pdf(np.array([max(cur, 1e-6)]), df)[0]), ylim_c * 0.8)
                              + ylim_c * 0.04))
            cht.set_text(f"χ² = {cur:.2f}")
        else:
            chl.set_data([], [])
            chm.set_data([], [])
            cht.set_text("")
        if i >= 100:
            tt = _ease((i - 100) / 20.0)
            rpoly.set_xy(region(xmax - (xmax - crit) * tt, xmax))
            rpoly.set_visible(True)
            crl.set_data([crit, crit], [0, ylim_c * 0.55])
            crt.set_position((crit + xmax * 0.01, ylim_c * 0.5))
            crt.set_text((f"kritik {crit:.2f}" if tr else f"critical {crit:.2f}"))
        else:
            rpoly.set_visible(False)
            crl.set_data([], [])
            crt.set_text("")
        if i >= 124:
            tt = _ease((i - 124) / 22.0)
            ppoly.set_xy(region(chi, chi + (xmax - chi) * tt))
            ppoly.set_visible(True)
        else:
            ppoly.set_visible(False)
        for (f0, t0, cc, fsz), tx in zip(rows, rtx):
            tx.set_text((t0[0] if tr else t0[1]) if i >= f0 else "")
        if i >= 52 and ncell <= 9:
            terms = [_d(v, 2) for v in flat_c[:nc]]
            h1 = " + ".join(terms[:3])
            h2 = " + ".join(terms[3:6])
            h3 = " + ".join(terms[6:])
            txt = r"$\chi^2 = \Sigma(O-E)^2/E$" + "\n= " + h1
            if h2:
                txt += "\n+ " + h2
            if h3:
                txt += "\n+ " + h3
            txt += (f" = {cur:.3f}" if nc == ncell else " …")
            chisum.set_text(txt)
        elif i >= 52:
            chisum.set_text(r"$\chi^2 = \Sigma(O-E)^2/E$" + f"\n= {cur:.3f}")
        else:
            chisum.set_text("")
        if i >= 148:
            dec.set_text(((f"χ² = {chi:.3f} > {crit:.3f}\n⇒ H₀ reddedilir" if tr else
                           f"χ² = {chi:.3f} > {crit:.3f}\n⇒ reject H₀") if rej else
                          (f"χ² = {chi:.3f} < {crit:.3f}\n⇒ H₀ reddedilemez" if tr else
                           f"χ² = {chi:.3f} < {crit:.3f}\n⇒ fail to reject H₀")))
            dec.set_color("#DC2626" if rej else "#16A34A")
        else:
            dec.set_text("")
        if D["mode"] == "gof":
            if i < 25:
                txt = ("1) Gözlenen sıklıklar O" if tr else "1) Observed counts O")
            elif i < 52:
                txt = (f"2) Beklenen sıklıklar: E = N·p (N = {_d(D['N'])})" if tr else
                       f"2) Expected counts: E = N·p (N = {_d(D['N'])})")
            elif i < 100:
                txt = ("3) Her kategorinin katkısı (O − E)²/E toplanır" if tr else
                       "3) Add up each category's contribution (O − E)²/E")
            elif i < 124:
                txt = (f"4) sd = k − 1 = {df}; α = {_d(al)} için red bölgesi" if tr else
                       f"4) df = k − 1 = {df}; rejection region for α = {_d(al)}")
            elif i < 148:
                txt = ("5) p-değeri = χ² değerinin sağındaki alan" if tr else
                       "5) p-value = area to the right of χ²")
            else:
                txt = ("6) Karar: " if tr else "6) Decision: ") + (
                    ("H₀ reddedilir — dağılım iddiaya uymuyor" if tr else "reject H₀ — the data do not fit the claim") if rej else
                    ("H₀ reddedilemez — veriler iddiayla uyumlu" if tr else "fail to reject H₀ — the data are consistent with the claim"))
        else:
            if i < 25:
                txt = ("1) Gözlenen tablo ve satır/sütun toplamları" if tr else "1) Observed table with row/column totals")
            elif i < 52:
                txt = ("2) Beklenen: E = (satır toplamı × sütun toplamı)/N" if tr else
                       "2) Expected: E = (row total × column total)/N")
            elif i < 100:
                txt = ("3) Hücre katkıları (O − E)²/E toplanır" if tr else "3) Add up the cell contributions (O − E)²/E")
            elif i < 124:
                txt = (f"4) sd = (r − 1)(c − 1) = {df}; α = {_d(al)} için red bölgesi" if tr else
                       f"4) df = (r − 1)(c − 1) = {df}; rejection region for α = {_d(al)}")
            elif i < 148:
                txt = ("5) p-değeri = χ² değerinin sağındaki alan" if tr else "5) p-value = area to the right of χ²")
            else:
                txt = ("6) Karar: " if tr else "6) Decision: ") + (
                    ("H₀ reddedilir — değişkenler ilişkili" if tr else "reject H₀ — the variables are associated") if rej else
                    ("H₀ reddedilemez — bağımsızlık reddedilmez" if tr else "fail to reject H₀ — no evidence of association"))
        info.set_text(txt)
        return []

    return N, update


def vary(P, rnd):
    D = _data(P)
    al = float(P.get("alpha", 0.05))
    if D["mode"] == "gof":
        L = 1
        for q in D["ratio"]:
            L = L * q.denominator // math.gcd(L, q.denominator)
        ratio = [int(q * L) for q in D["ratio"]]
        g = 0
        for q in ratio:
            g = math.gcd(g, q)
        ratio = [q // max(1, g) for q in ratio]
        s = sum(ratio)
        lo_m = max(2, int(math.ceil(8.0 / min(ratio))))
        base = float(D["N"]) / s
        mult = max(lo_m, int(round(base * rnd.choice([0.6, 0.8, 1.0, 1.25, 1.5]))))
        E = [mult * q for q in ratio]
        k = len(E)
        while True:
            dev = [rnd.randint(-max(2, e // 4), max(2, e // 4)) for e in E]
            dev[-1] = -sum(dev[:-1])
            O = [e + d for e, d in zip(E, dev)]
            if min(O) >= 1:
                break
        out = {"observed": O, "alpha": al}
        if P.get("ratio"):
            out["ratio"] = list(P["ratio"])
        if P.get("labels"):
            out["labels"] = P["labels"]
        return out
    r, c = D["r"], D["c"]
    while True:
        O = [[rnd.randint(8, 40) for _ in range(c)] for _ in range(r)]
        dd = _data({"observed": O})
        if min(float(v) for row in dd["E"] for v in row) >= 5:
            break
    out = {"observed": O, "alpha": al}
    for key in ("rows", "cols"):
        if P.get(key):
            out[key] = P[key]
    return out
''',
}
EXAMPLES += [
    {"id": "prob-chisq-1", "kind": "chi_square",
     "title": ("Zar hilesiz mi? (uyum iyiliği)", "Is the die fair? (goodness of fit)"),
     "q": ("Bir zar {N} kez atılıyor; 1–6 yüzleri için gözlenen sıklıklar: {observed}. α = {alpha} düzeyinde "
           "ki-kare uyum iyiliği testiyle zarın hilesiz olup olmadığını sına.",
           "A die is rolled {N} times; the observed counts for faces 1–6 are {observed}. At α = {alpha}, use a "
           "chi-square goodness-of-fit test to decide whether the die is fair."),
     "P": {"observed": [15, 22, 18, 25, 17, 23], "alpha": 0.05}},
    {"id": "prob-chisq-2", "kind": "chi_square", "topics": ["claimed proportions", "iddia edilen oranlar"],
     "title": ("Renk oranları iddiası", "Claimed color proportions"),
     "q": ("Bir şekerleme firması renklerin ({labels_s}) {ratio_s} oranında olduğunu iddia ediyor. {N} şekerlik "
           "bir torbada gözlenen sayılar: {observed}. α = {alpha} düzeyinde iddiayı test et.",
           "A candy maker claims its colors ({labels_s}) come in the ratio {ratio_s}. A bag of {N} candies has "
           "counts {observed}. Test the claim at α = {alpha}."),
     "P": {"observed": [44, 54, 36, 66], "ratio": [3, 2, 2, 3],
           "labels": [["Kırmızı", "Red"], ["Mavi", "Blue"], ["Yeşil", "Green"], ["Sarı", "Yellow"]],
           "alpha": 0.05}},
    {"id": "prob-chisq-3", "kind": "chi_square", "topics": ["contingency table", "two-way table", "çapraz tablo"],
     "title": ("Yaş grubu ve ulaşım tercihi (bağımsızlık)", "Age group and transport choice (independence)"),
     "q": ("İki yaş grubunun ulaşım tercihleri (otobüs, araba, bisiklet) gözlenen tablo olarak {table}. "
           "α = {alpha} düzeyinde yaş grubu ile ulaşım tercihinin bağımsız olup olmadığını test et.",
           "Transport choices (bus, car, bike) of two age groups form the observed table {table}. At α = {alpha}, "
           "test whether age group and transport choice are independent."),
     "P": {"observed": [[28, 10, 12], [12, 20, 18]],
           "rows": [["18–29 yaş", "Age 18–29"], ["30+ yaş", "Age 30+"]],
           "cols": [["Otobüs", "Bus"], ["Araba", "Car"], ["Bisiklet", "Bike"]], "alpha": 0.05}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["sampling_distribution_proportion"] = {
    "course": "prob",
    "title": ("Örneklem oranının dağılımı", "Sampling distribution of a sample proportion"),
    "topics": ["sampling distribution of the sample proportion", "sampling distribution of a proportion",
               "sample proportion", "sampling distribution", "p-hat", "p hat", "proportion",
               "standard error of a proportion", "normal approximation",
               "örneklem oranı", "oranın örnekleme dağılımı", "örnekleme dağılımı", "oran",
               "normal yaklaşım", "standart hata"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Polygon


def _d(v, k=3):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _z(v):
    s = f"{v:.2f}"
    return s.replace("-", "−") if float(s) != 0 else s.replace("-", "")


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _setup(P):
    p, n = float(P["p"]), max(2, int(P["n"]))
    p = min(0.99, max(0.01, p))
    c = float(P.get("c", round(p + 0.1, 2)))
    dd = str(P.get("dir", "greater")).strip().lower()
    dirn = "less" if dd.startswith(("l", "<")) else "greater"
    se = math.sqrt(p * (1 - p) / n)
    zraw = (c - p) / se
    z = round(zraw, 2)
    ph = round(_phi(z), 4)
    pr = round(1 - ph if dirn == "greater" else ph, 4)
    nc = n * c
    m = int(round(nc))
    if abs(nc - m) < 1e-9:
        ks = range(m + 1, n + 1) if dirn == "greater" else range(0, m)
    else:
        f = int(math.floor(nc))
        ks = range(f + 1, n + 1) if dirn == "greater" else range(0, f + 1)
    ks = list(ks)
    exact = sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in ks)
    return {"p": p, "n": n, "c": c, "dir": dirn, "se": se, "zraw": zraw, "z": z, "ph": ph, "pr": pr,
            "ks": ks, "exact": exact}


def _event(T, plain=True):
    op = ">" if T["dir"] == "greater" else "<"
    hat = "p̂" if plain else r"$\hat{p}$"
    return f"P({hat} {op} {_d(T['c'])})"


def _kev(T):
    ks = T["ks"]
    if not ks:
        return "∅"
    if T["dir"] == "greater":
        return f"X ≥ {ks[0]}"
    return f"X ≤ {ks[-1]}"


def _sim(P, T):
    K = max(50, min(800, int(P.get("samples", 400))))
    rng = np.random.default_rng(P.get("seed", 0))
    S = rng.random((K, T["n"])) < T["p"]
    return S, S.sum(axis=1)


def solve(P):
    T = _setup(P)
    p, n, c, se, z = T["p"], T["n"], T["c"], T["se"], T["z"]
    S, X = _sim(P, T)
    K = len(X)
    ev = _event(T)
    hit = int(np.sum(X > n * c + 1e-9)) if T["dir"] == "greater" else int(np.sum(X < n * c - 1e-9))
    np_, nq = n * p, n * (1 - p)
    okc = np_ >= 10 and nq >= 10
    zeq = "=" if abs(T["zraw"] - z) < 1e-9 else "≈"
    steps = [(f"p = {_d(p)}, n = {n};  p̂ = X/n, burada X ~ Binom(n, p)",
              f"p = {_d(p)}, n = {n};  p̂ = X/n where X ~ Binom(n, p)"),
             ((f"Koşul: np = {_d(np_)} ≥ 10 ve n(1 − p) = {_d(nq)} ≥ 10 ✓ ⇒ normal yaklaşım uygun" if okc else
               f"Koşul: np = {_d(np_)}, n(1 − p) = {_d(nq)} — en az biri 10'dan küçük ⇒ normal yaklaşım kaba kalır"),
              (f"Check: np = {_d(np_)} ≥ 10 and n(1 − p) = {_d(nq)} ≥ 10 ✓ ⇒ the normal approximation is fine" if okc else
               f"Check: np = {_d(np_)}, n(1 − p) = {_d(nq)} — at least one is below 10 ⇒ the normal approximation is rough")),
             (f"Ortalama: μ_p̂ = p = {_d(p)}", f"Mean: μ_p̂ = p = {_d(p)}"),
             (f"Standart hata: σ_p̂ = √(p(1 − p)/n) = √({_d(p)}·{_d(1 - p)}/{n}) ≈ {se:.4f}",
              f"Standard error: σ_p̂ = √(p(1 − p)/n) = √({_d(p)}·{_d(1 - p)}/{n}) ≈ {se:.4f}"),
             (f"z = (p̂ − p)/σ_p̂ = ({_d(c)} − {_d(p)})/{se:.4f} {zeq} {_z(z)}",
              f"z = (p̂ − p)/σ_p̂ = ({_d(c)} − {_d(p)})/{se:.4f} {zeq} {_z(z)}")]
    if T["dir"] == "greater":
        steps.append((f"{ev} ≈ P(Z > {_z(z)}) = 1 − {T['ph']:.4f} = {T['pr']:.4f}",
                      f"{ev} ≈ P(Z > {_z(z)}) = 1 − {T['ph']:.4f} = {T['pr']:.4f}"))
    else:
        steps.append((f"{ev} ≈ P(Z < {_z(z)}) = {T['pr']:.4f}", f"{ev} ≈ P(Z < {_z(z)}) = {T['pr']:.4f}"))
    steps.append((f"Kesin binom değeri: {ev} = P({_kev(T)}) ≈ {T['exact']:.4f} (normal yaklaşımla karşılaştır)",
                  f"Exact binomial value: {ev} = P({_kev(T)}) ≈ {T['exact']:.4f} (compare with the normal approximation)"))
    steps.append((f"Simülasyon: {K} örneklemin {hit} tanesinde olay gerçekleşti (%{100 * hit / K:.1f})",
                  f"Simulation: the event happened in {hit} of {K} samples ({100 * hit / K:.1f}%)"))
    ans = (f"μ_p̂ = {_d(p)}, σ_p̂ ≈ {se:.4f};  {ev} ≈ {T['pr']:.4f}",
           f"μ_p̂ = {_d(p)}, σ_p̂ ≈ {se:.4f};  {ev} ≈ {T['pr']:.4f}")
    return {"answer": ans, "steps": steps, "fmt": {"event": ev, "se": f"{se:.4f}"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    T = _setup(P)
    p, n, c, se = T["p"], T["n"], T["c"], T["se"]
    S, X = _sim(P, T)
    K = len(X)
    ph = X / float(n)
    grp = max(1, int(math.ceil(n / 60.0)))
    kmin = max(0, int(math.floor(n * (p - 5 * se))))
    kmax = min(n, int(math.ceil(n * (p + 5 * se))))
    kmin -= kmin % grp
    nb = (kmax - kmin) // grp + 1
    w = grp / float(n)
    centers = (kmin + grp * np.arange(nb) + (grp - 1) / 2.0) / n
    idx = (X - kmin) // grp
    ok = (idx >= 0) & (idx < nb)
    oh = np.zeros((K, nb))
    oh[np.arange(K)[ok], idx[ok]] = 1
    cum = np.vstack([np.zeros((1, nb)), np.cumsum(oh, axis=0)])
    cs = np.r_[0.0, np.cumsum(ph)]
    cs2 = np.r_[0.0, np.cumsum(ph ** 2)]
    xl = min(p - 4.5 * se, c - 0.6 * se, centers[0] - w)
    xr = max(p + 4.5 * se, c + 0.6 * se, centers[-1] + w)
    xl, xr = max(-0.02, xl), min(1.02, xr)
    gx = np.linspace(xl, xr, 400)
    gy = K * w * np.exp(-0.5 * ((gx - p) / se) ** 2) / (se * math.sqrt(2 * math.pi))
    ytop = max(float(cum[-1].max()), float(gy.max())) * 1.5
    if T["dir"] == "greater":
        inev = centers > c + 1e-9
    else:
        inev = centers < c - 1e-9

    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.9], height_ratios=[1.15, 1], left=0.02, right=0.985,
                          top=0.9, bottom=0.09, wspace=0.12, hspace=0.25)
    ga = fig.add_subplot(gs[0, 0])
    tp = fig.add_subplot(gs[1, 0])
    hx = fig.add_subplot(gs[:, 1])
    tp.axis("off")
    tp.set_xlim(0, 1)
    tp.set_ylim(0, 1)
    cols = 10 if n <= 100 else 20
    rows = int(math.ceil(n / float(cols)))
    gxp = np.array([k % cols for k in range(n)], dtype=float)
    gyp = np.array([k // cols for k in range(n)], dtype=float)
    ga.set_xlim(-0.7, cols - 0.3)
    ga.set_ylim(max(rows, 5) - 0.3, -0.7)
    ga.set_aspect("equal")
    ga.axis("off")
    msz = 70 if cols == 10 and rows <= 6 else (45 if cols == 10 else 14)
    gdots = ga.scatter(gxp, gyp, s=msz, c=["#E5E7EB"] * n, edgecolors="#9CA3AF", linewidths=0.5)
    gtitle = ga.set_title("", fontsize=10.5)
    bars = hx.bar(centers, np.zeros(nb), width=w * 0.9, color="#2563EB", alpha=0.85)
    hx.set_xlim(xl, xr)
    hx.set_ylim(0, ytop)
    hx.axvline(p, color="#6B7280", ls=":", lw=1.3)
    hx.set_ylabel("sayı" if tr else "count", fontsize=9)
    hx.set_xlabel(r"$\hat{p}$", fontsize=11, labelpad=1)
    hx.set_title((r"$\hat{p}$ değerlerinin histogramı (p = " if tr else r"Histogram of $\hat{p}$ (p = ")
                 + _d(p) + f", n = {n})", fontsize=10.5, loc="left")
    ncurve, = hx.plot([], [], color="#E07B39", lw=2.6, zorder=6)
    tail = Polygon(np.zeros((3, 2)), closed=True, fc="#E07B39", alpha=0.3, ec="#C2410C", hatch="///", lw=0.8, zorder=5)
    hx.add_patch(tail)
    cline, = hx.plot([], [], "--", color="#DC2626", lw=1.8, zorder=7)
    ctext = hx.text(c, 0, "", color="#DC2626", fontsize=10, ha="center", va="bottom", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    newl, = hx.plot([], [], color="#DC2626", lw=1.5, ls="--")
    info = hx.text(0.01, 0.97, "", transform=hx.transAxes, va="top", fontsize=10.5, zorder=8,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    stat = hx.text(0.99, 0.97, "", transform=hx.transAxes, va="top", ha="right", fontsize=10, zorder=8,
                   bbox=dict(boxstyle="round", fc="#F9FAFB", ec="#D1D5DB"))
    np_, nq = n * p, n * (1 - p)
    okc = np_ >= 10 and nq >= 10
    hit = int(np.sum(inev[idx[ok]])) if np.any(ok) else 0
    hitx = int(np.sum(X > n * c + 1e-9)) if T["dir"] == "greater" else int(np.sum(X < n * c - 1e-9))
    lines = [(0, f"p = {_d(p)},  n = {n}", "#111827"),
             (6, f"np = {_d(np_)},  n(1−p) = {_d(nq)}  " + ("✓" if okc else "✗"), "#16A34A" if okc else "#DC2626"),
             (132, r"$\mu_{\hat{p}}$ = p = " + _d(p), "#111827"),
             (136, r"$\sigma_{\hat{p}} = \sqrt{p(1-p)/n}$ ≈ " + f"{se:.4f}", "#111827"),
             (150, f"z = ({_d(c)} − {_d(p)})/{se:.4f} ≈ {_z(T['z'])}", "#C2410C"),
             (156, _event(T, False) + f" ≈ {T['pr']:.4f}", "#C2410C"),
             (160, ("binom (kesin): " if tr else "binomial (exact): ") + f"{T['exact']:.4f}", "#6B7280"),
             (164, ("simülasyon: " if tr else "simulation: ") + f"{hitx}/{K} = {hitx / K:.3f}", "#6B7280")]
    ltx = [tp.text(0.04, 0.98 - k * 0.123, "", fontsize=9.8, color=col, va="top") for k, (f0, t0, col) in enumerate(lines)]
    N = 175
    slow = 12

    def kof(i):
        if i < 14:
            return 1
        if i < 74:
            return min(slow, 1 + (i - 14) // 5)
        if i < 130:
            t = (i - 74) / 56.0
            return int(round(slow * (K / float(slow)) ** t))
        return K

    def update(i):
        k = max(1, min(K, kof(i)))
        j = k - 1
        gdots.set_facecolors(np.where(S[j], "#16A34A", "#E5E7EB"))
        gtitle.set_text((f"Örneklem #{k}: " if tr else f"Sample #{k}: ") + r"$\hat{p}$ = " + f"{X[j]}/{n} = {ph[j]:.3f}")
        h = cum[k] if i >= 10 else cum[0]
        yl = ytop if i >= 132 else min(ytop, max(6.0, 1.6 * float(h.max())))
        hx.set_ylim(0, yl)
        newest = idx[j] if ok[j] else -1
        for b, (rect, hh) in enumerate(zip(bars, h)):
            rect.set_height(hh)
            if i >= 150 and inev[b]:
                col = "#E07B39"
            elif b == newest and i < 74 and i >= 10:
                col = "#DC2626"
            else:
                col = "#2563EB"
            rect.set_facecolor(col)
        newl.set_data(([ph[j], ph[j]], [0, yl * 0.6]) if (10 <= i < 74) else ([], []))
        if i >= 132:
            m = max(2, int(_ease((i - 132) / 14.0) * len(gx)))
            ncurve.set_data(gx[:m], gy[:m])
        else:
            ncurve.set_data([], [])
        if i >= 146:
            cline.set_data([c, c], [0, ytop * 0.72])
            ctext.set_position((c, ytop * 0.73))
            ctext.set_text(r"$\hat{p}$ = " + _d(c))
        else:
            cline.set_data([], [])
            ctext.set_text("")
        if i >= 150:
            tt = _ease((i - 150) / 16.0)
            if T["dir"] == "greater":
                a0, a1 = c, c + (xr - c) * tt
            else:
                a0, a1 = c - (c - xl) * tt, c
            sx = np.linspace(a0, max(a1, a0 + 1e-9), 100)
            sy = K * w * np.exp(-0.5 * ((sx - p) / se) ** 2) / (se * math.sqrt(2 * math.pi))
            tail.set_xy(np.column_stack([np.r_[a0, sx, sx[-1]], np.r_[0, sy, 0]]))
            tail.set_visible(True)
        else:
            tail.set_visible(False)
        mk = cs[k] / k
        sk = math.sqrt(max(0.0, cs2[k] / k - mk * mk))
        st = [("örneklem sayısı: " if tr else "samples: ") + str(k),
              (r"ort($\hat{p}$) = " if tr else r"mean($\hat{p}$) = ") + f"{mk:.4f}",
              (r"ss($\hat{p}$) = " if tr else r"sd($\hat{p}$) = ") + f"{sk:.4f}"]
        if i >= 136:
            st.append(r"$\sqrt{p(1-p)/n}$ = " + f"{se:.4f}")
        stat.set_text("\n".join(st) if i >= 10 else "")
        stat.set_visible(i >= 10)
        for (f0, t0, col), tx in zip(lines, ltx):
            tx.set_text(t0 if i >= f0 else "")
        if i < 14:
            info.set_text((f"1) Bir örneklem: {n} birey, her biri p = {_d(p)} olasılıkla 'evet'" if tr else
                           f"1) One sample: {n} individuals, each 'yes' with probability p = {_d(p)}"))
        elif i < 74:
            info.set_text((r"2) Her örneklemin $\hat{p}$ değerini histograma ekle" if tr else
                           r"2) Add each sample's $\hat{p}$ to the histogram"))
        elif i < 132:
            info.set_text(("3) Yüzlerce örneklem… " if tr else "3) Hundreds of samples… ") + r"$\hat{p}$ ≈ p")
        elif i < 150:
            info.set_text((r"4) Normal yaklaşım: $\hat{p}$ ≈ N(p, $\sqrt{p(1-p)/n}$)" if tr else
                           r"4) Normal approximation: $\hat{p}$ ≈ N(p, $\sqrt{p(1-p)/n}$)"))
        else:
            info.set_text("5) " + _event(T, False) + f" ≈ {T['pr']:.4f}")
        return []

    return N, update


def vary(P, rnd):
    T = _setup(P)
    small = T["n"] * min(T["p"], 1 - T["p"]) < 10
    if small:
        p = rnd.choice([0.05, 0.08, 0.1, 0.12])
        n = rnd.choice([30, 40, 50])
    else:
        p = rnd.choice([0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8])
        n = rnd.choice([n for n in (50, 60, 80, 100, 120, 150, 200) if n * min(p, 1 - p) >= 10])
    se = math.sqrt(p * (1 - p) / n)
    step = 0.01 if se < 0.04 else 0.05
    off = max(step, round(rnd.choice([0.6, 0.9, 1.2, 1.5, 1.8]) * se / step) * step)
    c = round(p + off, 2) if T["dir"] == "greater" else round(p - off, 2)
    c = min(0.98, max(0.02, c))
    return {"p": p, "n": n, "c": c, "dir": T["dir"], "samples": rnd.choice([300, 400, 500]),
            "seed": rnd.randint(1, 9999)}
''',
}
EXAMPLES += [
    {"id": "prob-phat-1", "kind": "sampling_distribution_proportion", "topics": ["poll", "anket", "survey"],
     "title": ("Anket oranının dağılımı", "Distribution of a poll proportion"),
     "q": ("Seçmenler arasında bir öneriyi destekleyenlerin oranı p = {p}. {n} kişilik rastgele anketlerde destek "
           "oranı p̂ nasıl dağılır? Ortalamasını, standart hatasını ve {event} olasılığını bul.",
           "The proportion of voters who support a proposal is p = {p}. In random polls of {n} people, how is the "
           "sample proportion p̂ distributed? Find its mean, standard error and {event}."),
     "P": {"p": 0.3, "n": 50, "c": 0.4, "dir": "greater", "samples": 400, "seed": 2}},
    {"id": "prob-phat-2", "kind": "sampling_distribution_proportion", "topics": ["word problem", "sözel problem"],
     "title": ("Sol kuyruk: bisiklet sahipliği", "Lower tail: bike ownership"),
     "q": ("Bir şehirdeki öğrencilerin bisiklet sahibi olma oranı p = {p}. {n} öğrencilik rastgele örneklemlerde "
           "örneklem oranının ortalaması ve standart hatası nedir? {event} kaçtır?",
           "The proportion of students in a city who own a bike is p = {p}. For random samples of {n} students, "
           "what are the mean and standard error of the sample proportion? What is {event}?"),
     "P": {"p": 0.6, "n": 100, "c": 0.55, "dir": "less", "samples": 400, "seed": 8}},
    {"id": "prob-phat-3", "kind": "sampling_distribution_proportion",
     "topics": ["success-failure condition", "başarı-başarısızlık koşulu", "defective", "kusurlu"],
     "title": ("Normal yaklaşım koşulu sağlanmazsa", "When the normal condition fails"),
     "q": ("Bir üretim hattında kusurlu ürün oranı p = {p}. {n} ürünlük örneklemlerde {event} olasılığını normal "
           "yaklaşımla bul, kesin binom değeri ve simülasyonla karşılaştır. np ≥ 10 koşulu sağlanıyor mu?",
           "The defect rate on a production line is p = {p}. For samples of {n} items, find {event} with the normal "
           "approximation and compare it with the exact binomial value and a simulation. Is np ≥ 10 satisfied?"),
     "P": {"p": 0.1, "n": 40, "c": 0.15, "dir": "greater", "samples": 500, "seed": 6}},
]
