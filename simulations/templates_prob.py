# -*- coding: utf-8 -*-
"""Olasılık simülasyonları: büyük sayılar yasası (yazı-tura), zar toplamları,
Galton tahtası, binom dağılımı, Monte Carlo ile π, Bayes (doğal frekans ızgarası
ve olasılık ağacı), sayma (permütasyon / kombinasyon), beklenen değer ve
Poisson dağılımı.

Her TEMPLATES["kind"]["code"] kendi başına çalışan bir Python kaynağıdır;
sözleşme için simulations/engine.py başlığına bakın. Tüm rastgelelik build()
içinde np.random.default_rng(P.get("seed", 0)) ile ÖNCEDEN üretilir; böylece
her kare yalnızca kare numarasına bağlıdır (ileri/geri atlama güvenli).
Sorular kitaplardan KOPYALANMAZ: kendi ifademizle yazılmış tipik ders
örnekleridir.
"""

TEMPLATES = {}
EXAMPLES = []

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["coin_lln"] = {
    "course": "prob",
    "title": ("Yazı-tura ve büyük sayılar yasası", "Coin flips and the law of large numbers"),
    "topics": ["law of large numbers", "coin flip", "coin toss", "relative frequency",
               "experimental probability", "empirical probability", "long run proportion",
               "simulation", "büyük sayılar yasası", "yazı tura", "deneysel olasılık",
               "göreli sıklık", "bağıl frekans"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch


def _g(x, nd=4):
    s = f"{float(x):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _flips(P):
    n = max(10, min(20000, int(P["n"])))
    rng = np.random.default_rng(int(P.get("seed", 0)))
    return n, (rng.random(n) < float(P["p"])).astype(int)


def solve(P):
    n, fl = _flips(P)
    p = Fraction(str(P["p"]))
    q = 1 - p
    ex, var = n * p, n * p * q
    sdx = math.sqrt(float(var))
    sdp = math.sqrt(float(p * q) / n)
    band = 1 / math.sqrt(n)
    heads = int(fl.sum())
    ph = heads / n
    ok = abs(ph - float(p)) <= band
    lo, hi = max(0.0, float(p) - band), min(1.0, float(p) + band)
    steps = [
        (f"X = tura sayısı ~ Binom(n = {n}, p = {_g(p)});  E[X] = n·p = {n}·{_g(p)} = {_g(ex)}",
         f"X = number of heads ~ Bin(n = {n}, p = {_g(p)});  E[X] = n·p = {n}·{_g(p)} = {_g(ex)}"),
        (f"Var(X) = n·p·(1 − p) = {n}·{_g(p)}·{_g(q)} = {_g(var)};  σ_X = √{_g(var)} ≈ {_g(sdx, 3)}",
         f"Var(X) = n·p·(1 − p) = {n}·{_g(p)}·{_g(q)} = {_g(var)};  σ_X = √{_g(var)} ≈ {_g(sdx, 3)}"),
        (f"Oran p̂ = X/n:  E[p̂] = p = {_g(p)},  σ(p̂) = √(p(1 − p)/n) = √({_g(p * q)}/{n}) ≈ {_g(sdp)}",
         f"Proportion p̂ = X/n:  E[p̂] = p = {_g(p)},  σ(p̂) = √(p(1 − p)/n) = √({_g(p * q)}/{n}) ≈ {_g(sdp)}"),
        (f"p(1 − p) ≤ 1/4 olduğundan 2σ(p̂) ≤ 1/√n = 1/√{n} ≈ {_g(band)}  ⇒  ≈%95 bant: [{_g(lo)}, {_g(hi)}]",
         f"Since p(1 − p) ≤ 1/4, 2σ(p̂) ≤ 1/√n = 1/√{n} ≈ {_g(band)}  ⇒  ≈95% band: [{_g(lo)}, {_g(hi)}]"),
        (f"Simülasyon: {n} atışta {heads} tura ⇒ p̂ = {heads}/{n} = {_g(ph)}  "
         + ("(bandın içinde ✓)" if ok else "(bandın dışında — nadir bir durum)"),
         f"Simulation: {heads} heads in {n} flips ⇒ p̂ = {heads}/{n} = {_g(ph)}  "
         + ("(inside the band ✓)" if ok else "(outside the band — a rare event)")),
        ("Büyük sayılar yasası: n arttıkça p̂ → p; sapma 1/√n hızıyla küçülür",
         "Law of large numbers: as n grows, p̂ → p; the spread shrinks like 1/√n"),
    ]
    ans = (f"E[X] = {_g(ex)} tura;  p̂ ≈ {_g(p)} ± {_g(band)}  (simülasyon: p̂ = {_g(ph)})",
           f"E[X] = {_g(ex)} heads;  p̂ ≈ {_g(p)} ± {_g(band)}  (simulation: p̂ = {_g(ph)})")
    return {"answer": ans, "steps": steps,
            "fmt": {"pct": _g(100 * p, 2), "band": _g(band), "expected": _g(ex)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    n, fl = _flips(P)
    p = float(P["p"])
    cum = np.cumsum(fl)
    ks = np.arange(1, n + 1)
    ph = cum / ks
    PH = r"$\hat{p}$"
    gs = fig.add_gridspec(1, 2, width_ratios=[2.6, 1], left=0.08, right=0.97, top=0.82,
                          bottom=0.12, wspace=0.3)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[0, 1])
    ax.set_xscale("log")
    ax.set_xlim(1, n * 1.6)
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:g}"))
    ax.grid(alpha=0.3)
    ax.set_xlabel("atış sayısı n (log ölçek)" if tr else "number of flips n (log scale)")
    ax.set_ylabel(("tura oranı " if tr else "proportion of heads ") + PH)
    xb = np.unique(np.round(np.logspace(0, math.log10(n), 300))).astype(float)
    hb = 1.0 / np.sqrt(xb)
    band = ax.fill_between(xb, np.maximum(0, p - hb), np.minimum(1, p + hb), color="#16A34A",
                           alpha=0.0, lw=0)
    pl = ax.axhline(p, color="#E07B39", lw=2, ls="--", label=f"p = {p:g}")
    line, = ax.plot([], [], color="#2563EB", lw=1.6, label=PH)
    dot, = ax.plot([], [], "o", color="#DC2626", ms=7, zorder=5)
    err, = ax.plot([], [], color="#16A34A", lw=3.5, marker="_", ms=16, mew=3, zorder=6)
    flab = ax.text(n, min(0.97, p + 1 / math.sqrt(n) + 0.05), "", ha="right", va="bottom",
                   fontsize=10, color="#15803D", fontweight="bold")
    ax.legend(handles=[line, pl, Patch(color="#16A34A", alpha=0.25, label="p ± 1/√n")],
              loc="lower right" if p >= 0.5 else "upper right", fontsize=9)
    bars = bx.bar([0, 1], [0, 0], color=["#2563EB", "#E07B39"], width=0.6)
    bx.set_xlim(-0.6, 1.6)
    bx.set_ylim(0, 1.15)
    bx.set_xticks([0, 1])
    bx.set_xticklabels(["Tura (T)", "Yazı (Y)"] if tr else ["Heads (H)", "Tails (T)"])
    bx.plot([-0.38, 0.38], [p, p], "--", color="#111827", lw=1.4)
    bx.plot([0.62, 1.38], [1 - p, 1 - p], "--", color="#111827", lw=1.4)
    bx.set_ylabel("oran" if tr else "proportion")
    bx.grid(axis="y", alpha=0.3)
    c0 = bx.text(0, 0, "", ha="center", va="center", fontsize=10, fontweight="bold")
    c1 = bx.text(1, 0, "", ha="center", va="center", fontsize=10, fontweight="bold")
    recent = bx.text(0.5, 1.03, "", transform=bx.transAxes, ha="center", va="bottom",
                     family="DejaVu Sans Mono", fontsize=9.5, color="#374151")
    header = fig.text(0.5, 0.965, "", ha="center", va="top", fontsize=12,
                      bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    N, A, B = 150, 12, 124
    b1 = 1 / math.sqrt(n)
    final_ph = float(ph[-1])

    def kof(i):
        if i < A:
            return 0
        u = min(1.0, (i - A) / (B - A))
        return max(1, min(n, int(round(n ** u))))

    def update(i):
        k = kof(i)
        band.set_alpha(0.16 * min(1.0, max(0.0, (i - A) / 25)))
        if k == 0:
            line.set_data([], [])
            dot.set_data([], [])
            for b in bars:
                b.set_height(0)
            c0.set_text("")
            c1.set_text("")
            recent.set_text("")
            header.set_text(f"Bir para {n} kez atılıyor; her atışta P(tura) = p = {p:g}" if tr else
                            f"A coin is flipped {n} times; each flip has P(heads) = p = {p:g}")
        else:
            line.set_data(ks[:k], ph[:k])
            dot.set_data([k], [ph[k - 1]])
            h = int(cum[k - 1])
            t = k - h
            bars[0].set_height(h / k)
            bars[1].set_height(t / k)
            for ct, v, col in ((c0, h, "#1D4ED8"), (c1, t, "#B45309")):
                ct.set_text(str(v))
                inside_bar = v / k >= 0.14
                ct.set_y(v / k / 2 if inside_bar else v / k + 0.05)
                ct.set_color("white" if inside_bar else col)
            last = fl[max(0, k - 10):k]
            recent.set_text(" ".join((("T" if v else "Y") if tr else ("H" if v else "T")) for v in last))
            if i < B:
                header.set_text((f"{k}. atış: {h} tura  ⇒  " if tr else f"flip {k}: {h} heads  ⇒  ")
                                + PH + f" = {h}/{k} = {h / k:.3f}")
        if i >= B:
            err.set_data([n, n], [p - b1, p + b1])
            flab.set_text(PH + f" = {final_ph:.4f}")
            inside = abs(final_ph - p) <= b1
            if tr:
                header.set_text(f"n = {n}:  " + PH + f" = {final_ph:.4f} ≈ p = {p:g}   "
                                + (f"(±1/√n = ±{b1:.3f} bandının içinde)" if inside else
                                   f"(±{b1:.3f} bandının dışında)"))
            else:
                header.set_text(f"n = {n}:  " + PH + f" = {final_ph:.4f} ≈ p = {p:g}   "
                                + (f"(inside the ±1/√n = ±{b1:.3f} band)" if inside else
                                   f"(outside the ±{b1:.3f} band)"))
        else:
            err.set_data([], [])
            flab.set_text("")
        return []

    return N, update


def vary(P, rnd):
    return {"p": rnd.choice([0.5, 0.5, 0.3, 0.6, 0.7, 0.25, 0.8, 0.4]),
            "n": rnd.choice([400, 900, 1600, 2500, 10000]),
            "seed": rnd.randint(1, 9999)}
''',
}
EXAMPLES += [
    {"id": "prob-coin-1", "kind": "coin_lln",
     "title": ("Hilesiz para: büyük sayılar yasası", "Fair coin: law of large numbers"),
     "q": ("Hilesiz bir para {n} kez atılıyor (P(tura) = {p}). Beklenen tura sayısı nedir? Tura oranı "
           "p'ye hangi aralıkta yaklaşır (yaklaşık %95 bant ±1/√n)?",
           "A fair coin is flipped {n} times (P(heads) = {p}). What is the expected number of heads? "
           "Within what band does the proportion of heads approach p (≈95% band ±1/√n)?"),
     "P": {"p": 0.5, "n": 2500, "seed": 7}},
    {"id": "prob-coin-2", "kind": "coin_lln", "topics": ["free throw", "serbest atış"],
     "title": ("Serbest atış yüzdesi", "Free-throw percentage"),
     "q": ("Bir basketbolcu serbest atışların %{pct}'ini sayıya çeviriyor. {n} atışta beklenen basket "
           "sayısı nedir? İsabet oranı uzun vadede neye yaklaşır?",
           "A basketball player makes {pct}% of free throws. What is the expected number of baskets in "
           "{n} attempts? What does the long-run success rate approach?"),
     "P": {"p": 0.7, "n": 400, "seed": 3}},
    {"id": "prob-coin-3", "kind": "coin_lln", "topics": ["defective", "quality control", "kusurlu ürün"],
     "title": ("Kusurlu ürün oranı", "Defect rate in production"),
     "q": ("Bir hatta ürünlerin %{pct}'i kusurlu. {n} ürün rastgele incelenirse beklenen kusurlu sayısı "
           "nedir? Gözlenen oran p = {p} değerine nasıl yaklaşır?",
           "{pct}% of the items on a production line are defective. If {n} items are inspected, how many "
           "defective items are expected? How does the observed proportion approach p = {p}?"),
     "P": {"p": 0.2, "n": 10000, "seed": 11}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["dice_sum"] = {
    "course": "prob",
    "title": ("Zar toplamlarının dağılımı", "Distribution of the sum of dice"),
    "topics": ["dice", "sum of two dice", "rolling dice", "two dice", "sample space",
               "equally likely outcomes", "classical probability", "probability distribution",
               "zar", "iki zar", "zar atma", "örnek uzay", "eş olası", "olasılık dağılımı",
               "toplamın olasılığı"],
    "code": r'''
import itertools
import numpy as np
from fractions import Fraction
from matplotlib.patches import FancyBboxPatch, Circle

_SYM = {"eq": "=", "ge": "≥", "le": "≤", "gt": ">", "lt": "<"}
_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_PIPS = {"C": (0, 0), "TL": (-1, 1), "TR": (1, 1), "ML": (-1, 0), "MR": (1, 0),
         "BL": (-1, -1), "BR": (1, -1)}
_FACE = {1: ["C"], 2: ["TR", "BL"], 3: ["TR", "C", "BL"], 4: ["TL", "TR", "BL", "BR"],
         5: ["TL", "TR", "C", "BL", "BR"], 6: ["TL", "TR", "ML", "MR", "BL", "BR"]}


def _g(x, nd=4):
    s = f"{float(x):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _fr(v):
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _ways(d):
    c = {0: 1}
    for _ in range(d):
        nc = {}
        for s, w in c.items():
            for f in range(1, 7):
                nc[s + f] = nc.get(s + f, 0) + w
        c = nc
    return c


def _hit(s, t, cmp):
    if cmp == "ge":
        return s >= t
    if cmp == "le":
        return s <= t
    if cmp == "gt":
        return s > t
    if cmp == "lt":
        return s < t
    return s == t


def _setup(P):
    d = max(1, min(5, int(P.get("dice", 2))))
    trials = max(10, min(5000, int(P.get("trials", 600))))
    cmp = P.get("cmp", "eq")
    if cmp not in _SYM:
        cmp = "eq"
    t = int(P.get("target", (7 * d) // 2))
    return d, trials, _ways(d), cmp, t


def _sums(P, d, trials):
    rng = np.random.default_rng(int(P.get("seed", 0)))
    rolls = rng.integers(1, 7, size=(trials, d))
    return rolls, rolls.sum(axis=1)


def solve(P):
    d, trials, ways, cmp, t = _setup(P)
    total = 6 ** d
    sym = _SYM[cmp]
    hits = [s for s in sorted(ways) if _hit(s, t, cmp)]
    w = sum(ways[s] for s in hits)
    prob = Fraction(w, total)
    _, sums = _sums(P, d, trials)
    obs = int(sum(1 for s in sums if _hit(int(s), t, cmp)))
    steps = [(f"{d} zar, her biri 6 yüzlü ⇒ 6{str(d).translate(_SUP)} = {total} eş olası sıralı sonuç",
              f"{d} dice, 6 faces each ⇒ 6{str(d).translate(_SUP)} = {total} equally likely ordered outcomes")]
    if cmp == "eq" and 0 < w <= 8 and d <= 3:
        lst = ", ".join("(" + ",".join(str(v) for v in o) + ")"
                        for o in itertools.product(range(1, 7), repeat=d) if sum(o) == t)
        steps.append((f"Toplamı {t} olan sonuçlar: {lst}  ⇒  {w} yol",
                      f"Outcomes with sum {t}: {lst}  ⇒  {w} ways"))
    elif cmp == "eq":
        steps.append((f"Toplamı {t} olan sıralı sonuç sayısı: {w}", f"Number of ordered outcomes with sum {t}: {w}"))
    else:
        parts = " + ".join(str(ways[s]) for s in hits) if hits else "0"
        lst = ", ".join(f"{s}:{ways[s]}" for s in hits)
        steps.append((f"Toplam {sym} {t} olan toplamlar (toplam:yol) → {lst}  ⇒  {parts} = {w} yol",
                      f"Sums with sum {sym} {t} (sum:ways) → {lst}  ⇒  {parts} = {w} ways"))
    steps.append((f"P(toplam {sym} {t}) = (uygun sonuç)/(tüm sonuç) = {w}/{total} = {_fr(prob)} ≈ {_g(prob)}",
                  f"P(sum {sym} {t}) = favourable / total = {w}/{total} = {_fr(prob)} ≈ {_g(prob)}"))
    mx = max(ways.values())
    modes = ", ".join(str(s) for s in sorted(ways) if ways[s] == mx)
    steps.append((f"E[toplam] = {d}·3.5 = {_g(3.5 * d)};  en olası toplam: {modes} ({mx}/{total})",
                  f"E[sum] = {d}·3.5 = {_g(3.5 * d)};  most likely sum: {modes} ({mx}/{total})"))
    steps.append((f"{trials} atışta beklenen sayı: {trials}·{_fr(prob)} ≈ {_g(trials * prob, 1)};  "
                  f"simülasyonda {obs} kez (oran {_g(obs / trials, 3)})",
                  f"Expected count in {trials} rolls: {trials}·{_fr(prob)} ≈ {_g(trials * prob, 1)};  "
                  f"simulation: {obs} times (rate {_g(obs / trials, 3)})"))
    ans = (f"P(toplam {sym} {t}) = {w}/{total} = {_fr(prob)} ≈ {_g(prob)}",
           f"P(sum {sym} {t}) = {w}/{total} = {_fr(prob)} ≈ {_g(prob)}")
    return {"answer": ans, "steps": steps,
            "fmt": {"event": (f"toplam {sym} {t}", f"sum {sym} {t}"), "total": str(total)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    d, trials, ways, cmp, t = _setup(P)
    total = 6 ** d
    sym = _SYM[cmp]
    rolls, sums = _sums(P, d, trials)
    svals = np.arange(d, 6 * d + 1)
    pmf = np.array([ways[s] / total for s in svals])
    hit = np.array([_hit(int(s), t, cmp) for s in svals])
    w = int(sum(ways[int(s)] for s in svals if _hit(int(s), t, cmp)))
    prob = Fraction(w, total)
    gs = fig.add_gridspec(2, 2, width_ratios=[2.2, 1], height_ratios=[1, 1.9], left=0.08, right=0.985,
                          top=0.92, bottom=0.1, wspace=0.1, hspace=0.08)
    ax = fig.add_subplot(gs[:, 0])
    dx = fig.add_subplot(gs[0, 1])
    tx = fig.add_subplot(gs[1, 1])
    dx.axis("off")
    tx.axis("off")
    cols = ["#DC2626" if h else "#2563EB" for h in hit]
    bars = ax.bar(svals, np.zeros(len(svals)), width=0.8, color=cols, alpha=0.85,
                  edgecolor="#111827", linewidth=0)
    expl, = ax.plot([], [], "o-", color="#E07B39", ms=4, lw=1.6,
                    label=("beklenen: k·P(toplam = s)" if tr else "expected: k·P(sum = s)"))
    ax.bar([0], [0], color="#2563EB", label=("gözlenen sayı" if tr else "observed count"))
    ax.set_xlim(d - 0.7, 6 * d + 0.7)
    ax.set_ylim(0, 1)
    ax.set_xticks(svals if len(svals) <= 16 else svals[::2])
    ax.set_xlabel("zarların toplamı s" if tr else "sum of the dice s")
    ax.set_ylabel("sayı" if tr else "count")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=11,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    # dice faces of the latest roll
    W = max(d, 2) * 1.25
    dx.set_xlim(0, W)
    dx.set_ylim(-0.1, 1.35)
    dx.set_aspect("equal")
    pips = []
    for j in range(d):
        x0 = 0.125 + j * 1.25 + (W - max(d, 2) * 1.25) / 2 + (0.625 if d == 1 else 0)
        dx.add_patch(FancyBboxPatch((x0, 0.1), 1.0, 1.0, boxstyle="round,pad=0,rounding_size=0.15",
                                    fc="white", ec="#111827", lw=1.6))
        row = {}
        for key, (ox, oy) in _PIPS.items():
            c = Circle((x0 + 0.5 + ox * 0.26, 0.6 + oy * 0.26), 0.085, color="#111827", visible=False)
            dx.add_patch(c)
            row[key] = c
        pips.append(row)
    dsum = dx.text(W / 2, 1.3, "", ha="center", va="top", fontsize=11, fontweight="bold")
    lines = [tx.text(0.02, 0.96 - 0.115 * m, "", transform=tx.transAxes, va="top", fontsize=10)
             for m in range(8)]
    tumble = np.random.default_rng(int(P.get("seed", 0)) + 99).integers(1, 7, size=(200, d))
    N, R0, R1, R2 = 165, 8, 44, 128
    slow = min(6, trials)

    def kof(i):
        if i < R0:
            return 0
        if i < R1:
            return min(slow, 1 + (i - R0) * slow // (R1 - R0))
        u = min(1.0, (i - R1) / (R2 - R1))
        return int(round(slow + (trials - slow) * u ** 1.6))

    def show(face_row):
        for j in range(d):
            vis = _FACE[int(face_row[j])]
            for key, c in pips[j].items():
                c.set_visible(key in vis)

    def update(i):
        k = kof(i)
        counts = np.bincount(sums[:k] - d, minlength=len(svals)) if k else np.zeros(len(svals), int)
        for b, c in zip(bars, counts):
            b.set_height(c)
            b.set_linewidth(0)
        top = max(counts.max(), k * pmf.max(), 1) * 1.45 + 1
        ax.set_ylim(0, top)
        if k:
            expl.set_data(svals, k * pmf)
        else:
            expl.set_data([], [])
        if k:
            fresh = i < R1 and (i - R0) % ((R1 - R0) // slow) < 2
            show(tumble[i % 200] if fresh else rolls[k - 1])
            s_last = int(sums[k - 1])
            dsum.set_text("…" if fresh else (f"toplam = {s_last}" if tr else f"sum = {s_last}"))
            if i < R2:
                bars[s_last - d].set_linewidth(2.2)
        else:
            for row in pips:
                for c in row.values():
                    c.set_visible(False)
            dsum.set_text("")
        obs = int(counts[hit].sum())
        ev = (f"toplam {sym} {t}" if tr else f"sum {sym} {t}")
        txt = [(f"{d} zar ⇒ 6{str(d).translate(_SUP)} = {total} sonuç" if tr else
                f"{d} dice ⇒ 6{str(d).translate(_SUP)} = {total} outcomes", "#111827")]
        if i >= R0 + 10:
            txt.append(((f"{ev}: {w} yol" if tr else f"{ev}: {w} ways"), "#DC2626"))
        if i >= R0 + 22:
            txt.append((f"P = {w}/{total} = {_fr(prob)} ≈ {float(prob):.4f}", "#DC2626"))
        if k:
            txt.append(((f"atış: {k} / {trials}" if tr else f"rolls: {k} / {trials}"), "#374151"))
            txt.append(((f"gözlenen: {obs}/{k} = {obs / k:.3f}" if tr else
                         f"observed: {obs}/{k} = {obs / k:.3f}"), "#2563EB"))
        if i >= R2:
            txt.append(((f"beklenen: {trials}·P ≈ {trials * float(prob):.1f}" if tr else
                         f"expected: {trials}·P ≈ {trials * float(prob):.1f}"), "#E07B39"))
            txt.append(((f"fark: {abs(obs / k - float(prob)):.3f}" if tr else
                         f"difference: {abs(obs / k - float(prob)):.3f}"), "#16A34A"))
        for m, tobj in enumerate(lines):
            if m < len(txt):
                tobj.set_text(txt[m][0])
                tobj.set_color(txt[m][1])
                tobj.set_fontweight("bold" if (i >= R2 and m == 2) else "normal")
            else:
                tobj.set_text("")
        if i < R0:
            info.set_text((f"{d} zar atılacak\nkırmızı: {ev}" if tr else
                           f"Rolling {d} dice\nred bars: {ev}"))
        elif i < R1:
            info.set_text(("Her atışın toplamı\nhistograma eklenir" if tr else
                           "Each roll's sum is\nadded to the histogram"))
        elif i < R2:
            info.set_text((f"{k} atış: çubuklar kesin\ndağılıma yaklaşıyor" if tr else
                           f"{k} rolls: bars approach\nthe exact distribution"))
        else:
            info.set_text((f"P({ev}) = {_fr(prob)} ≈ {float(prob):.4f}\ngözlenen oran: {obs / k:.4f}" if tr else
                           f"P({ev}) = {_fr(prob)} ≈ {float(prob):.4f}\nobserved rate: {obs / k:.4f}"))
        return []

    return N, update


def vary(P, rnd):
    d = rnd.choice([2, 2, 2, 3])
    cmp = rnd.choice(["eq", "eq", "ge", "le"])
    if d == 2:
        t = {"eq": rnd.randint(3, 11), "ge": rnd.randint(8, 11), "le": rnd.randint(3, 6)}[cmp]
    else:
        t = {"eq": rnd.randint(6, 15), "ge": rnd.randint(12, 16), "le": rnd.randint(5, 9)}[cmp]
    return {"dice": d, "trials": rnd.choice([300, 600, 1000]), "target": t, "cmp": cmp,
            "seed": rnd.randint(1, 9999)}
''',
}
EXAMPLES += [
    {"id": "prob-dice-1", "kind": "dice_sum",
     "title": ("İki zarın toplamı 7", "Two dice summing to 7"),
     "q": ("İki zar atılıyor. P({event}) nedir? {trials} atışlık bir simülasyonla karşılaştır.",
           "Two dice are rolled. What is P({event})? Compare with a simulation of {trials} rolls."),
     "P": {"dice": 2, "trials": 600, "target": 7, "seed": 1}},
    {"id": "prob-dice-2", "kind": "dice_sum", "topics": ["board game", "kutu oyunu"],
     "title": ("Kutu oyunu: en az 10", "Board game: at least 10"),
     "q": ("Bir kutu oyununda iki zar atılıyor; {event} gelirse ödül var. Ödül kazanma olasılığı nedir? "
           "{trials} turda kaç kez ödül beklenir?",
           "In a board game two dice are rolled and you win a prize if {event}. What is the probability "
           "of winning? How many prizes are expected in {trials} turns?"),
     "P": {"dice": 2, "trials": 600, "target": 10, "cmp": "ge", "seed": 4}},
    {"id": "prob-dice-3", "kind": "dice_sum", "topics": ["three dice", "üç zar"],
     "title": ("Üç zarın toplamı", "Sum of three dice"),
     "q": ("Üç zar birlikte atılıyor. P({event}) olasılığını bul ({total} sıralı sonuç).",
           "Three dice are rolled together. Find P({event}) ({total} ordered outcomes)."),
     "P": {"dice": 3, "trials": 1000, "target": 10, "seed": 2}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["galton_board"] = {
    "course": "prob",
    "title": ("Galton tahtası ve binom dağılımı", "Galton board and the binomial distribution"),
    "topics": ["galton board", "bean machine", "quincunx", "pascal's triangle", "pascal triangle",
               "binomial distribution", "random walk", "bell shape",
               "galton tahtası", "pascal üçgeni", "binom dağılımı", "rastgele yürüyüş", "çan eğrisi"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction

_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _g(x, nd=4):
    s = f"{float(x):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _fr(v):
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _sim(P):
    n = max(2, min(14, int(P.get("rows", 10))))
    B = max(1, min(600, int(P.get("balls", 200))))
    k = max(0, min(n, int(P.get("k", n // 2))))
    rng = np.random.default_rng(int(P.get("seed", 0)))
    steps = (rng.random((B, n)) < 0.5).astype(int)
    R = np.concatenate([np.zeros((B, 1), dtype=int), np.cumsum(steps, axis=1)], axis=1)
    return n, B, k, R


def solve(P):
    n, B, k, R = _sim(P)
    c = math.comb(n, k)
    prob = Fraction(c, 2 ** n)
    obs = int((R[:, -1] == k).sum())
    exp = B * prob
    steps = [
        (f"Her çivide top 1/2 olasılıkla sola, 1/2 olasılıkla sağa sapar; {n} sıra ⇒ {n} bağımsız seçim",
         f"At every peg the ball goes left or right with probability 1/2; {n} rows ⇒ {n} independent choices"),
        (f"Kutu numarası K = sağa sapma sayısı ⇒ K ~ Binom({n}, 1/2); kutular 0, 1, …, {n}",
         f"Bin number K = number of right bounces ⇒ K ~ Bin({n}, 1/2); bins 0, 1, …, {n}"),
        (f"Tüm yollar: 2{str(n).translate(_SUP)} = {2 ** n};  K = {k} kutusuna giden yollar: C({n},{k}) = {c}",
         f"All paths: 2{str(n).translate(_SUP)} = {2 ** n};  paths into bin K = {k}: C({n},{k}) = {c}"),
        (f"P(K = {k}) = C({n},{k})/2{str(n).translate(_SUP)} = {c}/{2 ** n} = {_fr(prob)} ≈ {_g(prob)}",
         f"P(K = {k}) = C({n},{k})/2{str(n).translate(_SUP)} = {c}/{2 ** n} = {_fr(prob)} ≈ {_g(prob)}"),
        (f"{B} topta beklenen: {B}·{_fr(prob)} ≈ {_g(exp, 1)} top;  simülasyonda {obs} top",
         f"Expected among {B} balls: {B}·{_fr(prob)} ≈ {_g(exp, 1)} balls;  simulation: {obs} balls"),
        (f"E[K] = n/2 = {_g(n / 2)},  Var(K) = n/4 = {_g(n / 4)},  σ ≈ {_g(math.sqrt(n) / 2, 3)} — ortada tepe yapan çan biçimi",
         f"E[K] = n/2 = {_g(n / 2)},  Var(K) = n/4 = {_g(n / 4)},  σ ≈ {_g(math.sqrt(n) / 2, 3)} — a bell shape peaking in the middle"),
    ]
    ans = (f"P(K = {k}) = {_fr(prob)} ≈ {_g(prob)};  beklenen ≈ {_g(exp, 1)} top",
           f"P(K = {k}) = {_fr(prob)} ≈ {_g(prob)};  expected ≈ {_g(exp, 1)} balls")
    return {"answer": ans, "steps": steps, "fmt": {"bins": str(n + 1), "paths": str(2 ** n)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    n, B, k, R = _sim(P)
    final = R[:, -1]
    pmf = np.array([math.comb(n, j) / 2 ** n for j in range(n + 1)])
    T, S, N = 24, 96, 165
    js = np.arange(B)
    start = np.round(S * np.sqrt(js / max(1, B - 1))).astype(int)
    land = start + T
    cnt = np.zeros((N, n + 1), dtype=int)
    for i in range(N):
        sel = final[land <= i]
        if len(sel):
            cnt[i] = np.bincount(sel, minlength=n + 1)
    H = max(4.0, 0.8 * n)
    ybot = -n - H
    scale = (H - 0.5) / max(cnt[-1].max(), B * pmf.max(), 1)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1], left=0.02, right=0.985, top=0.92, bottom=0.04,
                          wspace=0.04)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    ax.axis("off")
    ax.set_xlim(-n / 2 - 0.9, n / 2 + 0.9)
    ax.set_ylim(ybot - 0.9, 1.6)
    ms_peg = max(3.0, 9 - 0.4 * n)
    for r in range(n):
        ax.plot(-r / 2 + np.arange(r + 1), np.full(r + 1, -r), "o", color="#6B7280", ms=ms_peg)
    for j in range(n + 2):
        xw = j - n / 2 - 0.5
        ax.plot([xw, xw], [ybot, -n + 0.15], color="#9CA3AF", lw=1.2)
    ax.plot([-n / 2 - 0.5, n / 2 + 0.5], [ybot, ybot], color="#374151", lw=1.6)
    cols = ["#DC2626" if j == k else "#2563EB" for j in range(n + 1)]
    bars = ax.bar(np.arange(n + 1) - n / 2, np.zeros(n + 1), width=0.78, bottom=ybot, color=cols, alpha=0.85)
    expl, = ax.plot([], [], "o-", color="#E07B39", lw=2, ms=4, zorder=6)
    trace, = ax.plot([], [], "--", color="#E07B39", lw=1.4)
    balls, = ax.plot([], [], "o", color="#7C3AED", ms=max(4.0, 9 - 0.35 * n), zorder=7)
    for j in range(n + 1):
        ax.text(j - n / 2, ybot - 0.12, str(j), ha="center", va="top", fontsize=8.5 if n <= 10 else 7.5,
                color="#DC2626" if j == k else "#6B7280", fontweight="bold" if j == k else "normal")
    ax.set_title((f"Galton tahtası: {n} sıra çivi, {B} top" if tr else f"Galton board: {n} rows of pegs, {B} balls"),
                 fontsize=12)

    def pos(jj, tt):
        x = np.zeros(len(jj))
        y = np.zeros(len(jj))
        a = tt < 1
        y[a] = 1.3 - (1.3 - 0.32) * tt[a]
        b = ~a
        if b.any():
            r = np.minimum((tt[b] - 1).astype(int), n - 1)
            u = (tt[b] - 1) - r
            jb = jj[b]
            xa = R[jb, r] - r / 2.0
            xb = R[jb, r + 1] - (r + 1) / 2.0
            x[b] = xa + (xb - xa) * u
            y[b] = (-r + 0.32) - u + 0.6 * u * (1 - u)
        return x, y

    tt0 = np.linspace(0, n + 1, 240)
    px0, py0 = pos(np.zeros(240, dtype=int), tt0)
    info = tx.text(0.02, 0.985, "", transform=tx.transAxes, va="top", fontsize=10.5,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    h3 = ("bekl.", "göz.") if tr else ("exp.", "obs.")
    hdr = f"{'k':<2} {'C(n,k)':>6}  {'P(K=k)':<6} {h3[0]:>6} {h3[1]:>5}"
    ty0 = 0.74
    dy = min(0.05, 0.7 / (n + 2))
    tx.text(0.02, ty0, hdr, transform=tx.transAxes, va="top", family="DejaVu Sans Mono", fontsize=9,
            fontweight="bold")
    rows = [tx.text(0.02, ty0 - dy * (j + 1), "", transform=tx.transAxes, va="top",
                    family="DejaVu Sans Mono", fontsize=9, color=("#DC2626" if j == k else "#111827"),
                    fontweight=("bold" if j == k else "normal"))
            for j in range(n + 1)]
    prob = Fraction(math.comb(n, k), 2 ** n)

    def update(i):
        act = (start <= i) & (i < land)
        jj = js[act]
        tt = (i - start[act]) / T * (n + 1)
        x, y = pos(jj, tt)
        balls.set_data(x, y)
        c = cnt[i]
        for b, v in zip(bars, c):
            b.set_height(v * scale)
        if i < 64:
            m = int(np.searchsorted(tt0, min(n + 1.0, (i - start[0]) / T * (n + 1)), side="right"))
            trace.set_data(px0[:m], py0[:m])
        else:
            trace.set_data([], [])
        landed = int(c.sum())
        done = i >= land[-1]
        if done:
            expl.set_data(np.arange(n + 1) - n / 2, ybot + B * pmf * scale)
        else:
            expl.set_data([], [])
        for j, t in enumerate(rows):
            t.set_text(f"{j:<2d} {math.comb(n, j):>6d}  {pmf[j]:.4f} {B * pmf[j]:>6.1f} {c[j]:>5d}")
        if i < start[min(B - 1, 3)]:
            info.set_text(("Her çivide top ½ sola, ½ sağa sapar.\nKutu no = sağa sapma sayısı" if tr else
                           "At each peg: ½ left, ½ right.\nBin number = number of right bounces"))
        elif not done:
            info.set_text((f"Kutuya düşen top: {landed} / {B}\nK ~ Binom({n}, 1/2)" if tr else
                           f"Balls landed: {landed} / {B}\nK ~ Bin({n}, 1/2)"))
        else:
            info.set_text((f"P(K = {k}) = C({n},{k}) / 2^{n}\n= {_fr(prob)} ≈ {float(prob):.4f}\n"
                           f"beklenen {B * float(prob):.1f} top, gözlenen {c[k]}" if tr else
                           f"P(K = {k}) = C({n},{k}) / 2^{n}\n= {_fr(prob)} ≈ {float(prob):.4f}\n"
                           f"expected {B * float(prob):.1f} balls, observed {c[k]}"))
        return []

    return N, update


def vary(P, rnd):
    n = rnd.choice([6, 8, 8, 10, 12])
    balls = 2 ** n if n <= 8 else rnd.choice([200, 300, 400])
    return {"rows": n, "balls": balls, "k": rnd.randint(1, n - 1), "seed": rnd.randint(1, 9999)}
''',
}
EXAMPLES += [
    {"id": "prob-galton-1", "kind": "galton_board",
     "title": ("Galton tahtasında orta kutu", "The middle bin of a Galton board"),
     "q": ("{rows} sıra çivili bir Galton tahtasına {balls} top bırakılıyor ({bins} kutu). Bir topun "
           "{k} numaralı kutuya düşme olasılığı nedir? Bu kutuya kaç top beklenir?",
           "{balls} balls are dropped through a Galton board with {rows} rows of pegs ({bins} bins). What is "
           "the probability that a ball lands in bin {k}? How many balls are expected there?"),
     "P": {"rows": 10, "balls": 200, "k": 5, "seed": 5}},
    {"id": "prob-galton-2", "kind": "galton_board",
     "title": ("Pascal üçgeni ve yollar", "Pascal's triangle and paths"),
     "q": ("{rows} sıralı tahtada toplam {paths} eş olası yol var. {balls} top bırakılırsa {k} numaralı "
           "kutuya kaç top düşmesi beklenir?",
           "A board with {rows} rows has {paths} equally likely paths. If {balls} balls are dropped, how "
           "many are expected to land in bin {k}?"),
     "P": {"rows": 8, "balls": 256, "k": 2, "seed": 8}},
    {"id": "prob-galton-3", "kind": "galton_board",
     "title": ("Kenar kutusu", "The edge bin"),
     "q": ("{rows} sıra çivili tahtada top hep sola saparsa {k} numaralı kutuya düşer. Bunun olasılığı "
           "nedir? {balls} topta kaç tane beklenir?",
           "On a board with {rows} rows, a ball that always bounces left ends in bin {k}. What is the "
           "probability of that? How many of {balls} balls are expected there?"),
     "P": {"rows": 6, "balls": 128, "k": 0, "seed": 2}},
]
