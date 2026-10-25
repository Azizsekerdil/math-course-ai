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
from matplotlib.ticker import FuncFormatter, NullLocator
from matplotlib.patches import Patch


def _g(x, nd=4):
    s = f"{float(x):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _names(P):
    # (success_tr, success_en, failure_tr, failure_en, custom?) — default: a coin (heads = tura)
    s, f = P.get("succ"), P.get("fail")
    if isinstance(s, (list, tuple)) and len(s) == 2 and isinstance(f, (list, tuple)) and len(f) == 2:
        return str(s[0]), str(s[1]), str(f[0]), str(f[1]), True
    return "tura", "heads", "yazı", "tails", False


def _flips(P):
    n = max(10, min(20000, int(P["n"])))
    rng = np.random.default_rng(int(P.get("seed", 0)))
    return n, (rng.random(n) < float(P["p"])).astype(int)


def solve(P):
    n, fl = _flips(P)
    s_tr, s_en, f_tr, f_en, custom = _names(P)
    w_tr, w_en = ("deneme", "trials") if custom else ("atış", "flips")
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
        (f"X = {s_tr} sayısı ~ Binom(n = {n}, p = {_g(p)});  E[X] = n·p = {n}·{_g(p)} = {_g(ex)}",
         f"X = number of {s_en} ~ Bin(n = {n}, p = {_g(p)});  E[X] = n·p = {n}·{_g(p)} = {_g(ex)}"),
        (f"Var(X) = n·p·(1 − p) = {n}·{_g(p)}·{_g(q)} = {_g(var)};  σ_X = √{_g(var)} ≈ {_g(sdx, 3)}",
         f"Var(X) = n·p·(1 − p) = {n}·{_g(p)}·{_g(q)} = {_g(var)};  σ_X = √{_g(var)} ≈ {_g(sdx, 3)}"),
        (f"Oran p̂ = X/n:  E[p̂] = p = {_g(p)},  σ(p̂) = √(p(1 − p)/n) = √({_g(p * q)}/{n}) ≈ {_g(sdp)}",
         f"Proportion p̂ = X/n:  E[p̂] = p = {_g(p)},  σ(p̂) = √(p(1 − p)/n) = √({_g(p * q)}/{n}) ≈ {_g(sdp)}"),
        (f"p(1 − p) ≤ 1/4 olduğundan 2σ(p̂) ≤ 1/√n = 1/√{n} ≈ {_g(band)}  ⇒  ≈%95 bant: [{_g(lo)}, {_g(hi)}]",
         f"Since p(1 − p) ≤ 1/4, 2σ(p̂) ≤ 1/√n = 1/√{n} ≈ {_g(band)}  ⇒  ≈95% band: [{_g(lo)}, {_g(hi)}]"),
        (f"Simülasyon: {n} {w_tr} içinde {heads} {s_tr} ⇒ p̂ = {heads}/{n} = {_g(ph)}  "
         + ("(bandın içinde ✓)" if ok else "(bandın dışında — nadir bir durum)"),
         f"Simulation: {heads} {s_en} in {n} {w_en} ⇒ p̂ = {heads}/{n} = {_g(ph)}  "
         + ("(inside the band ✓)" if ok else "(outside the band — a rare event)")),
        ("Büyük sayılar yasası: n arttıkça p̂ → p; sapma 1/√n hızıyla küçülür",
         "Law of large numbers: as n grows, p̂ → p; the spread shrinks like 1/√n"),
    ]
    ans = (f"E[X] = {_g(ex)} {s_tr};  p̂ ≈ {_g(p)} ± {_g(band)}  (simülasyon: p̂ = {_g(ph)})",
           f"E[X] = {_g(ex)} {s_en};  p̂ ≈ {_g(p)} ± {_g(band)}  (simulation: p̂ = {_g(ph)})")
    return {"answer": ans, "steps": steps,
            "fmt": {"pct": _g(100 * p, 2), "band": _g(band), "expected": _g(ex)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    n, fl = _flips(P)
    s_tr, s_en, f_tr, f_en, custom = _names(P)
    sn, fn = (s_tr, f_tr) if tr else (s_en, f_en)
    l1, l0 = sn[:1].upper(), fn[:1].upper()
    if l1 == l0:
        l1, l0 = "+", "−"
    if not custom:
        l1, l0 = ("T", "Y") if tr else ("H", "T")
    wd = ("deneme" if tr else "trial") if custom else ("atış" if tr else "flip")
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
    ax.xaxis.set_minor_locator(NullLocator())
    ax.grid(alpha=0.3)
    ax.set_xlabel((f"{wd} sayısı n (log ölçek)" if tr else f"number of {wd}s n (log scale)"))
    ax.set_ylabel((f"{sn} oranı " if tr else f"proportion of {sn} ") + PH)
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
    bx.set_xticklabels([f"{sn} ({l1})", f"{fn} ({l0})"], fontsize=9)
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
    if custom:
        intro = (f"{n} bağımsız deneme; her denemede P({sn}) = p = {p:g}" if tr else
                 f"{n} independent trials; each has P({sn}) = p = {p:g}")
    else:
        intro = (f"Bir para {n} kez atılıyor; her atışta P(tura) = p = {p:g}" if tr else
                 f"A coin is flipped {n} times; each flip has P(heads) = p = {p:g}")

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
            header.set_text(intro)
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
            recent.set_text(" ".join((l1 if v else l0) for v in last))
            if i < B:
                header.set_text((f"{k}. {wd}: {h} {sn}  ⇒  " if tr else f"{wd} {k}: {h} {sn}  ⇒  ")
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
    p0 = float(Fraction(str(P["p"])))
    if p0 == 0.5:
        p = 0.5
    elif p0 < 0.5:
        p = rnd.choice([0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4])
    else:
        p = rnd.choice([0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9])
    out = {"p": p, "n": rnd.choice([400, 900, 1600, 2500, 10000]), "seed": rnd.randint(1, 9999)}
    for key in ("succ", "fail"):
        if key in P:
            out[key] = P[key]
    return out
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
     "q": ("Bir basketbolcunun serbest atış isabet oranı %{pct}. {n} atışta beklenen basket sayısı nedir? "
           "Gözlenen isabet oranı uzun vadede neye yaklaşır?",
           "A basketball player makes {pct}% of free throws. What is the expected number of baskets in "
           "{n} attempts? What does the long-run success rate approach?"),
     "P": {"p": 0.7, "n": 400, "seed": 3, "succ": ["basket", "baskets"], "fail": ["ıska", "misses"]}},
    {"id": "prob-coin-3", "kind": "coin_lln", "topics": ["defective", "quality control", "kusurlu ürün"],
     "title": ("Kusurlu ürün oranı", "Defect rate in production"),
     "q": ("Bir üretim hattında kusurlu ürün oranı %{pct}. {n} ürün rastgele incelenirse beklenen kusurlu "
           "sayısı nedir? Gözlenen oran p = {p} değerine nasıl yaklaşır?",
           "{pct}% of the items on a production line are defective. If {n} items are inspected, how many "
           "defective items are expected? How does the observed proportion approach p = {p}?"),
     "P": {"p": 0.2, "n": 10000, "seed": 11, "succ": ["kusurlu", "defective"],
           "fail": ["sağlam", "good"]}},
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
    dx.set_ylim(-0.5, 1.2)
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
    dsum = dx.text(W / 2, 0.0, "", ha="center", va="top", fontsize=11, fontweight="bold")
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
    d = max(1, min(5, int(P.get("dice", 2))))
    cmp = P.get("cmp", "eq")
    if cmp not in _SYM:
        cmp = "eq"
    lo, hi, mid = d, 6 * d, (7 * d) // 2
    if cmp in ("ge", "gt"):
        t = rnd.randint(mid + 1, hi - 1)
    elif cmp in ("le", "lt"):
        t = rnd.randint(lo + 1, max(lo + 1, mid - 1))
    else:
        t = rnd.randint(lo + 1, hi - 1)
    out = {"dice": d, "trials": rnd.choice([300, 600, 1000]), "target": t, "seed": rnd.randint(1, 9999)}
    if "cmp" in P:
        out["cmp"] = cmp
    return out
''',
}
EXAMPLES += [
    {"id": "prob-dice-1", "kind": "dice_sum",
     "title": ("İki zarın toplamı", "The sum of two dice"),
     "q": ("İki zar atılıyor. P({event}) nedir? {trials} atışlık bir simülasyonla karşılaştır.",
           "Two dice are rolled. What is P({event})? Compare with a simulation of {trials} rolls."),
     "P": {"dice": 2, "trials": 600, "target": 7, "seed": 1}},
    {"id": "prob-dice-2", "kind": "dice_sum", "topics": ["board game", "kutu oyunu"],
     "title": ("Kutu oyunu: yüksek toplam", "Board game: a high total"),
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
    n0 = int(P.get("rows", 10))
    k0 = int(P.get("k", n0 // 2))
    n = rnd.choice([6, 8, 8, 10, 12])
    if k0 == n0 // 2:
        k = n // 2
    elif k0 <= 0:
        k = 0
    elif k0 >= n0:
        k = n
    else:
        k = rnd.randint(1, n - 1)
    balls = 2 ** n if n <= 8 else rnd.choice([200, 300, 400])
    return {"rows": n, "balls": balls, "k": k, "seed": rnd.randint(1, 9999)}
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

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["binomial"] = {
    "course": "prob",
    "title": ("Binom dağılımı", "Binomial distribution"),
    "topics": ["binomial", "binomial distribution", "binomial probability", "binomial random variable",
               "bernoulli trials", "binomial formula", "successes in n trials", "at least", "at most",
               "binom", "binom dağılımı", "binom olasılığı", "bernoulli denemesi", "başarı sayısı", "en az",
               "en çok"],
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


def _dec(v, maxd=6):
    v = Fraction(v)
    for d in range(maxd + 1):
        if (v * 10 ** d).denominator == 1:
            return f"{float(v):.{d}f}"
    return None


def _num(v):
    s = _dec(v)
    return s if s is not None else _fr(v)


def _val(v):
    s = _dec(v)
    return s if s is not None else _g(v, 6)


def _eqv(v):
    s = _dec(v)
    return ("= " + s) if s is not None else ("≈ " + _g(v, 6))


def _setup(P):
    n = max(1, min(40, int(P["n"])))
    k = max(0, min(n, int(P["k"])))
    p = Fraction(str(P["p"]))
    if p < 0 or p > 1:
        p = Fraction(1, 2)
    cmp = P.get("cmp", "le")
    if cmp not in ("le", "ge"):
        cmp = "le"
    return n, k, p, 1 - p, cmp


def _pmf(n, p, q):
    return [math.comb(n, j) * p ** j * q ** (n - j) for j in range(n + 1)]


def _terms(js):
    if len(js) <= 4:
        return " + ".join(f"P({j})" for j in js)
    return f"P({js[0]}) + P({js[1]}) + … + P({js[-1]})"


def _sumtxt(pm, js):
    vals = [_g(pm[j]) for j in js]
    if len(vals) > 5:
        vals = vals[:2] + ["…"] + vals[-2:]
    return " + ".join(vals)


def solve(P):
    n, k, p, q, cmp = _setup(P)
    pm = _pmf(n, p, q)
    c = math.comb(n, k)
    pk, qk = p ** k, q ** (n - k)
    prob = pm[k]
    sk, snk = str(k).translate(_SUP), str(n - k).translate(_SUP)
    ps, qs = _num(p), _num(q)
    pb = f"({ps})" if "/" in ps else ps
    qb = f"({qs})" if "/" in qs else qs
    res = (f"= {_fr(prob)} ≈ {_g(prob)}" if prob.denominator <= 100000 and prob.denominator > 1
           else f"≈ {_g(prob)}")
    js = list(range(0, k + 1)) if cmp == "le" else list(range(k, n + 1))
    cum = sum(pm[j] for j in js)
    sym = "≤" if cmp == "le" else "≥"
    mu, var = n * p, n * p * q
    sd = math.sqrt(float(var))
    steps = [
        (f"X ~ Binom(n = {n}, p = {ps});  başarısızlık olasılığı q = 1 − p = {qs}",
         f"X ~ Bin(n = {n}, p = {ps});  failure probability q = 1 − p = {qs}"),
        ("Formül: P(X = k) = C(n, k) · pᵏ · qⁿ⁻ᵏ", "Formula: P(X = k) = C(n, k) · pᵏ · qⁿ⁻ᵏ"),
        (f"C({n}, {k}) = {n}! / ({k}!·{n - k}!) = {c}", f"C({n}, {k}) = {n}! / ({k}!·{n - k}!) = {c}"),
        (f"p{sk} = {pb}{sk} {_eqv(pk)};   q{snk} = {qb}{snk} {_eqv(qk)}",
         f"p{sk} = {pb}{sk} {_eqv(pk)};   q{snk} = {qb}{snk} {_eqv(qk)}"),
        (f"P(X = {k}) = {c} · {_val(pk)} · {_val(qk)} {res}", f"P(X = {k}) = {c} · {_val(pk)} · {_val(qk)} {res}"),
        (f"P(X {sym} {k}) = {_terms(js)} = {_sumtxt(pm, js)} ≈ {_g(cum)}",
         f"P(X {sym} {k}) = {_terms(js)} = {_sumtxt(pm, js)} ≈ {_g(cum)}"),
        (f"Ortalama μ = n·p = {n}·{ps} = {_num(mu)};  varyans σ² = n·p·q = {_num(var)};  σ ≈ {_g(sd, 3)}",
         f"Mean μ = n·p = {n}·{ps} = {_num(mu)};  variance σ² = n·p·q = {_num(var)};  σ ≈ {_g(sd, 3)}"),
    ]
    ans = (f"P(X = {k}) ≈ {_g(prob)};  P(X {sym} {k}) ≈ {_g(cum)};  μ = {_num(mu)}, σ² = {_num(var)}",
           f"P(X = {k}) ≈ {_g(prob)};  P(X {sym} {k}) ≈ {_g(cum)};  μ = {_num(mu)}, σ² = {_num(var)}")
    return {"answer": ans, "steps": steps,
            "fmt": {"pct": _g(100 * p, 2), "q": qs, "nk": str(n - k),
                    "event": ((f"en çok {k}" if cmp == "le" else f"en az {k}"),
                              (f"at most {k}" if cmp == "le" else f"at least {k}"))}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    n, k, p, q, cmp = _setup(P)
    pmF = _pmf(n, p, q)
    pm = np.array([float(v) for v in pmF])
    xs = np.arange(n + 1)
    js = list(range(0, k + 1)) if cmp == "le" else list(range(k, n + 1))
    sym = "≤" if cmp == "le" else "≥"
    ps, qs = _num(p), _num(q)
    pb = f"({ps})" if "/" in ps else ps
    qb = f"({qs})" if "/" in qs else qs
    c = math.comb(n, k)
    mu = float(n * p)
    sd = math.sqrt(float(n * p * q))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1], left=0.08, right=0.99, top=0.9, bottom=0.11,
                          wspace=0.05)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    bars = ax.bar(xs, np.zeros(n + 1), width=0.78, color="#2563EB", alpha=0.85, edgecolor="#991B1B",
                  linewidth=0)
    top = pm.max() * 1.45
    ax.set_ylim(0, top)
    ax.set_xlim(-0.7, n + 0.7)
    ax.set_xticks(xs if n <= 16 else xs[::2])
    ax.grid(axis="y", alpha=0.3)
    ax.set_xlabel("başarı sayısı k" if tr else "number of successes k")
    ax.set_ylabel("P(X = k)")
    ax.set_title(f"X ~ Binom(n = {n}, p = {ps})" if tr else f"X ~ Bin(n = {n}, p = {ps})", fontsize=12)
    klab = ax.text(k, 0, "", ha="center", va="bottom", fontsize=9, color="#DC2626", fontweight="bold",
                   zorder=6, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    mline, = ax.plot([], [], "--", color="#7C3AED", lw=2)
    sline, = ax.plot([], [], color="#7C3AED", lw=2.5, marker="|", ms=14, mew=2.5)
    mtxt = ax.text(0, 0, "", va="center", fontsize=10, color="#7C3AED", fontweight="bold")
    info = ax.text(0.02, 0.97, "", transform=ax.transAxes, va="top", fontsize=10.5,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    lines = [tx.text(0.03, 0.97 - 0.093 * m, "", transform=tx.transAxes, va="top", fontsize=10.5)
             for m in range(10)]
    cumv = np.cumsum([pm[j] for j in js])
    L = [(8, f"X ~ Binom({n}, {ps})" if tr else f"X ~ Bin({n}, {ps})", "#111827"),
         (8, f"q = 1 − p = {qs}", "#111827"),
         (20, "P(X=k) = C(n,k)·pᵏ·qⁿ⁻ᵏ", "#111827"),
         (32, f"C({n},{k}) = {n}!/({k}!·{n - k}!) = {c}", "#2563EB"),
         (44, f"p{str(k).translate(_SUP)} = {pb}{str(k).translate(_SUP)} {_eqv(p ** k)}", "#2563EB"),
         (56, f"q{str(n - k).translate(_SUP)} = {qb}{str(n - k).translate(_SUP)} {_eqv(q ** (n - k))}", "#2563EB"),
         (68, f"P(X={k}) = {c}·{_val(p ** k)}·{_val(q ** (n - k))}", "#DC2626"),
         (68, f"          ≈ {pm[k]:.4f}", "#DC2626"),
         (92, "", "#E07B39"),
         (128, f"μ = np = {mu:g},  σ² = npq = {float(n * p * q):g}", "#7C3AED")]
    N = 165

    def ramp(i, a, b):
        return min(1.0, max(0.0, (i - a) / (b - a)))

    def update(i):
        nsel = int(math.ceil(len(js) * ramp(i, 94, 120)))
        lit = set(js[:nsel])
        for j, b in enumerate(bars):
            u = ramp(i, 16 * j / (n + 1), 16 * j / (n + 1) + 8)
            b.set_height(pm[j] * u)
            if j == k and i >= 68:
                b.set_color("#DC2626" if j not in lit else "#E07B39")
                b.set_linewidth(2.5 if j in lit else 0)
                b.set_edgecolor("#991B1B")
            else:
                b.set_color("#E07B39" if j in lit else "#2563EB")
                b.set_linewidth(0)
        if i >= 68:
            klab.set_text(f"{pm[k]:.4f}")
            klab.set_y(pm[k] + top * 0.01)
        else:
            klab.set_text("")
        for m, (fr0, txt, col) in enumerate(L):
            t = lines[m]
            if i < fr0:
                t.set_text("")
                continue
            if m == 8:
                part = float(cumv[nsel - 1]) if nsel else 0.0
                t.set_text(f"P(X {sym} {k}) = ΣP ≈ {part:.4f}")
            else:
                t.set_text(txt)
            t.set_color(col)
            t.set_fontweight("bold" if m in (7, 8) and i >= 120 else "normal")
        if i >= 128:
            mline.set_data([mu, mu], [0, top * 0.8])
            sline.set_data([mu - sd, mu + sd], [top * 0.8, top * 0.8])
            right = mu <= n / 2
            mtxt.set_position((mu + sd + 0.35 if right else mu - sd - 0.35, top * 0.8))
            mtxt.set_ha("left" if right else "right")
            mtxt.set_text(f"μ ± σ = {mu:g} ± {sd:.2f}")
        else:
            mline.set_data([], [])
            sline.set_data([], [])
            mtxt.set_text("")
        if i < 20:
            info.set_text((f"{n} bağımsız deneme,\nher birinde başarı olasılığı p = {ps}" if tr else
                           f"{n} independent trials,\neach succeeds with p = {ps}"))
        elif i < 92:
            info.set_text((f"P(X = {k}): tam {k} başarı\nC({n},{k}) farklı sırayla" if tr else
                           f"P(X = {k}): exactly {k} successes\nin C({n},{k}) different orders"))
        elif i < 128:
            info.set_text((f"P(X {sym} {k}): turuncu çubukların\ntoplamı ≈ {float(cumv[-1]):.4f}" if tr else
                           f"P(X {sym} {k}): sum of the orange\nbars ≈ {float(cumv[-1]):.4f}"))
        else:
            info.set_text((f"Ortalama μ = {mu:g}\nstandart sapma σ ≈ {sd:.3f}" if tr else
                           f"Mean μ = {mu:g}\nstandard deviation σ ≈ {sd:.3f}"))
        return []

    return N, update


def vary(P, rnd):
    p0 = float(Fraction(str(P["p"])))
    if p0 == 0.5:
        p = 0.5
    elif p0 < 0.5:
        p = rnd.choice([0.1, 0.2, 0.25, 0.3, 0.4])
    else:
        p = rnd.choice([0.6, 0.7, 0.75, 0.8, 0.9])
    n = rnd.randint(5, 12)
    k = max(0, min(n, int(round(n * p)) + rnd.randint(-2, 2)))
    cmp = P.get("cmp", "le")
    k = max(1, k) if cmp == "ge" else min(n - 1, k)
    out = {"n": n, "p": p, "k": k}
    if "cmp" in P:
        out["cmp"] = cmp
    return out
''',
}
EXAMPLES += [
    {"id": "prob-binom-1", "kind": "binomial", "topics": ["multiple choice", "guessing", "çoktan seçmeli"],
     "title": ("Çoktan seçmeli sınavda tahmin", "Guessing on a multiple-choice test"),
     "q": ("Bir öğrenci çoktan seçmeli bir sınavın {n} sorusunun hepsini rastgele işaretliyor; her sorunun "
           "doğru olma olasılığı p = {p}. Tam {k} doğru ve {event} doğru yapma olasılıklarını bul.",
           "A student guesses all {n} questions of a multiple-choice test; each guess is correct with "
           "probability p = {p}. Find the probability of exactly {k} correct answers and of {event} correct."),
     "P": {"n": 10, "p": 0.25, "k": 3}},
    {"id": "prob-binom-2", "kind": "binomial", "topics": ["free throw", "serbest atış"],
     "title": ("Serbest atışlarda en az k basket", "At least k made free throws"),
     "q": ("İsabet oranı %{pct} olan bir oyuncu {n} serbest atış kullanıyor. P(X = {k}) ve "
           "P({event} basket) nedir? Beklenen basket sayısı kaçtır?",
           "A player who makes {pct}% of free throws takes {n} shots. Find P(X = {k}) and "
           "P({event} baskets). What is the expected number of baskets?"),
     "P": {"n": 8, "p": 0.7, "k": 6, "cmp": "ge"}},
    {"id": "prob-binom-3", "kind": "binomial", "topics": ["coin", "para"],
     "title": ("Altı kez para atma", "Flipping a coin six times"),
     "q": ("Hilesiz bir para {n} kez atılıyor. Tam {k} tura gelme olasılığı nedir? En çok {k} tura?",
           "A fair coin is flipped {n} times. What is the probability of exactly {k} heads? Of at most {k}?"),
     "P": {"n": 6, "p": 0.5, "k": 2}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["monte_carlo_pi"] = {
    "course": "prob",
    "title": ("Monte Carlo yöntemiyle π tahmini", "Estimating π with Monte Carlo"),
    "topics": ["monte carlo", "estimating pi", "geometric probability", "random points",
               "simulation", "area by simulation", "random sampling",
               "monte carlo yöntemi", "pi tahmini", "geometrik olasılık", "rastgele nokta", "benzetim",
               "simülasyon"],
    "code": r'''
import math
import numpy as np
from matplotlib.patches import Circle, Rectangle, Patch
from matplotlib.ticker import FuncFormatter, NullLocator


def _pts(P):
    n = max(50, min(20000, int(P["n"])))
    rng = np.random.default_rng(int(P.get("seed", 0)))
    xy = rng.uniform(-1.0, 1.0, size=(n, 2))
    ins = (xy ** 2).sum(axis=1) <= 1.0
    return n, xy, ins


def solve(P):
    n, xy, ins = _pts(P)
    M = int(ins.sum())
    est = 4 * M / n
    pr = math.pi / 4
    se = 4 * math.sqrt(pr * (1 - pr) / n)
    steps = [
        ("Kare [−1, 1] × [−1, 1]: alanı 2·2 = 4;  içine çizilen birim dairenin alanı π·1² = π",
         "Square [−1, 1] × [−1, 1]: area 2·2 = 4;  the inscribed unit disc has area π·1² = π"),
        ("Kareye düzgün rastgele atılan nokta için P(x² + y² ≤ 1) = (daire alanı)/(kare alanı) = π/4 ≈ 0.7854",
         "For a uniform random point in the square, P(x² + y² ≤ 1) = (disc area)/(square area) = π/4 ≈ 0.7854"),
        (f"Simülasyon: n = {n} noktanın M = {M} tanesi dairenin içinde ⇒ M/n = {M / n:.4f}",
         f"Simulation: M = {M} of the n = {n} points land inside the disc ⇒ M/n = {M / n:.4f}"),
        (f"π ≈ 4·M/n = 4·{M}/{n} = {est:.4f}", f"π ≈ 4·M/n = 4·{M}/{n} = {est:.4f}"),
        (f"Hata: |{est:.4f} − π| = {abs(est - math.pi):.4f};  tipik hata (standart hata) "
         f"4·√(p(1 − p)/n) ≈ {se:.4f}, p = π/4",
         f"Error: |{est:.4f} − π| = {abs(est - math.pi):.4f};  typical error (standard error) "
         f"4·√(p(1 − p)/n) ≈ {se:.4f}, p = π/4"),
        ("Nokta sayısını 4 katına çıkarmak hatayı yaklaşık yarıya indirir (hata ∝ 1/√n)",
         "Using 4 times as many points roughly halves the error (error ∝ 1/√n)"),
    ]
    return {"answer": (f"π ≈ 4·{M}/{n} = {est:.4f}  (hata {abs(est - math.pi):.4f})",
                       f"π ≈ 4·{M}/{n} = {est:.4f}  (error {abs(est - math.pi):.4f})"),
            "steps": steps, "fmt": {"se": f"{se:.3f}"}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    n, xy, ins = _pts(P)
    cin = np.cumsum(ins)
    ks = np.arange(1, n + 1)
    est = 4.0 * cin / ks
    XI, XO = xy[ins], xy[~ins]
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.3], left=0.04, right=0.98, top=0.83, bottom=0.12,
                          wspace=0.2)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[0, 1])
    ax.set_xlim(-1.04, 1.04)
    ax.set_ylim(-1.04, 1.04)
    ax.set_aspect("equal")
    ax.set_xticks([-1, 0, 1])
    ax.set_yticks([-1, 0, 1])
    ax.add_patch(Rectangle((-1, -1), 2, 2, fill=False, ec="#111827", lw=1.5))
    ax.add_patch(Circle((0, 0), 1, fill=False, ec="#16A34A", lw=2.2, zorder=5))
    ms = 3.4 if n <= 1000 else (2.3 if n <= 4000 else 1.6)
    pin, = ax.plot([], [], "o", color="#2563EB", ms=ms, mew=0, alpha=0.85)
    pout, = ax.plot([], [], "o", color="#E07B39", ms=ms, mew=0, alpha=0.85)
    last, = ax.plot([], [], "o", mfc="none", mec="#DC2626", ms=11, mew=2, zorder=6)
    ax.set_title("mavi: içeride (x²+y² ≤ 1) · turuncu: dışarıda" if tr else
                 "blue: inside (x²+y² ≤ 1) · orange: outside", fontsize=9.5)
    bx.set_xscale("log")
    bx.set_xlim(1, n * 1.5)
    bx.set_ylim(2.5, 3.8)
    bx.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:g}"))
    bx.xaxis.set_minor_locator(NullLocator())
    bx.grid(alpha=0.3)
    bx.set_xlabel("nokta sayısı n (log ölçek)" if tr else "number of points n (log scale)")
    bx.set_ylabel("4·M/n")
    xb = np.unique(np.round(np.logspace(0, math.log10(n), 300))).astype(float)
    pr = math.pi / 4
    se = 4 * np.sqrt(pr * (1 - pr) / xb)
    bx.fill_between(xb, math.pi - 2 * se, math.pi + 2 * se, color="#16A34A", alpha=0.13, lw=0)
    pil = bx.axhline(math.pi, color="#16A34A", ls="--", lw=2, label="π = 3.14159…")
    eline, = bx.plot([], [], color="#7C3AED", lw=1.5, label=("tahmin 4·M/n" if tr else "estimate 4·M/n"))
    edot, = bx.plot([], [], "o", color="#DC2626", ms=6, zorder=5)
    bx.legend(handles=[eline, pil, Patch(color="#16A34A", alpha=0.25, label="π ± 2·SE")],
              loc="lower right", fontsize=9)
    header = fig.text(0.5, 0.965, "", ha="center", va="top", fontsize=12,
                      bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    N, A, B = 150, 6, 124
    M = int(cin[-1])

    def kof(i):
        if i < A:
            return 0
        u = min(1.0, (i - A) / (B - A))
        return max(1, min(n, int(round(1 + (n - 1) * u ** 2.6))))

    def update(i):
        k = kof(i)
        if k == 0:
            for a in (pin, pout, last, eline, edot):
                a.set_data([], [])
            header.set_text(("Kareye rastgele noktalar atılıyor: bir noktanın dairede olma olasılığı π/4"
                             if tr else "Random points in the square: each lands in the disc with probability π/4"))
            return []
        m_in = int(cin[k - 1])
        m_out = k - m_in
        pin.set_data(XI[:m_in, 0], XI[:m_in, 1])
        pout.set_data(XO[:m_out, 0], XO[:m_out, 1])
        if i < B:
            last.set_data([xy[k - 1, 0]], [xy[k - 1, 1]])
        else:
            last.set_data([], [])
        eline.set_data(ks[:k], est[:k])
        edot.set_data([k], [est[k - 1]])
        if i < B:
            header.set_text((f"n = {k} nokta, içeride M = {m_in}   ⇒   π ≈ 4·{m_in}/{k} = {est[k - 1]:.4f}"
                             if tr else
                             f"n = {k} points, M = {m_in} inside   ⇒   π ≈ 4·{m_in}/{k} = {est[k - 1]:.4f}"))
        else:
            e = est[-1]
            header.set_text((f"n = {n}:  π ≈ 4·{M}/{n} = {e:.4f}   (gerçek π = 3.14159…, hata {abs(e - math.pi):.4f})"
                             if tr else
                             f"n = {n}:  π ≈ 4·{M}/{n} = {e:.4f}   (true π = 3.14159…, error {abs(e - math.pi):.4f})"))
        return []

    return N, update


def vary(P, rnd):
    if int(P["n"]) <= 1000:
        n = rnd.choice([200, 300, 500, 800, 1000])
    else:
        n = rnd.choice([2000, 3000, 4000, 5000, 10000])
    return {"n": n, "seed": rnd.randint(1, 9999)}
''',
}
EXAMPLES += [
    {"id": "prob-mcpi-1", "kind": "monte_carlo_pi",
     "title": ("Rastgele noktalarla π", "π from random points"),
     "q": ("[−1, 1] × [−1, 1] karesine {n} rastgele nokta atılıyor. Birim dairenin içine düşen noktaların "
           "oranını kullanarak π'yi tahmin et.",
           "{n} random points are thrown into the square [−1, 1] × [−1, 1]. Estimate π from the fraction "
           "of points that land inside the unit disc."),
     "P": {"n": 2000, "seed": 7}},
    {"id": "prob-mcpi-2", "kind": "monte_carlo_pi", "topics": ["darts", "dart"],
     "title": ("Dart tahtası deneyi", "A dartboard experiment"),
     "q": ("Kare bir panoya içine teğet daire çizilmiş. Rastgele {n} dart atılıyor. Daireye isabet oranı "
           "π/4'e yaklaşırsa π ≈ ? (tipik hata ≈ {se})",
           "A circle is inscribed in a square board and {n} darts land at random on the board. The hit rate "
           "in the circle approaches π/4, so π ≈ ? (typical error ≈ {se})"),
     "P": {"n": 10000, "seed": 3}},
    {"id": "prob-mcpi-3", "kind": "monte_carlo_pi",
     "title": ("Az noktayla tahmin", "An estimate with few points"),
     "q": ("Sadece {n} rastgele nokta ile π tahmini ne kadar iyi olur? Tahmini ve hatayı bul.",
           "How good is an estimate of π from only {n} random points? Find the estimate and its error."),
     "P": {"n": 500, "seed": 12}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["bayes_grid"] = {
    "course": "prob",
    "title": ("Bayes teoremi: tıbbi test (doğal frekanslar)", "Bayes' theorem: a medical test (natural frequencies)"),
    "topics": ["bayes", "bayes theorem", "bayes' theorem", "conditional probability", "medical test",
               "false positive", "sensitivity", "specificity", "base rate", "natural frequencies",
               "bayes teoremi", "koşullu olasılık", "tıbbi test", "yanlış pozitif", "duyarlılık", "özgüllük"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


def _g(x, nd=4):
    s = f"{float(x):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _fr(v):
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _num(v):
    v = Fraction(v)
    for d in range(7):
        if (v * 10 ** d).denominator == 1:
            return f"{float(v):.{d}f}"
    return _fr(v)


def _v(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else _g(x, 1)


def _pc(x, tr):
    s = _g(100 * Fraction(x), 1)
    return ("%" + s) if tr else (s + "%")


def _cap(w):
    return ("İ" if w[:1] == "i" else w[:1].upper()) + w[1:]


def _names(P):
    c, h = P.get("cond"), P.get("nocond")
    if isinstance(c, (list, tuple)) and len(c) == 2 and isinstance(h, (list, tuple)) and len(h) == 2:
        return (str(c[0]), str(c[1])), (str(h[0]), str(h[1]))
    return ("hasta", "sick"), ("sağlıklı", "healthy")


def _counts(P):
    N = max(10, int(P["population"]))
    prev = Fraction(str(P["prevalence"]))
    sens = Fraction(str(P["sensitivity"]))
    spec = Fraction(str(P["specificity"]))
    D = N * prev
    H = N - D
    TP = D * sens
    FP = H * (1 - spec)
    return N, prev, sens, spec, D, H, TP, D - TP, FP, H - FP


def solve(P):
    N, prev, sens, spec, D, H, TP, FN, FP, TN = _counts(P)
    (c_tr, c_en), (h_tr, h_en) = _names(P)
    pos = TP + FP
    post = TP / pos if pos else Fraction(0)
    npv = TN / (TN + FN) if (TN + FN) else Fraction(0)
    good = npv >= Fraction(95, 100)
    num = sens * prev
    den = sens * prev + (1 - spec) * (1 - prev)
    red = "" if f"{_v(TP)}/{_v(pos)}" == _fr(post) else f" = {_fr(post)}"
    bt = (f"({_num(sens)}·{_num(prev)}) / ({_num(sens)}·{_num(prev)} + {_num(1 - spec)}·{_num(1 - prev)}) "
          f"= {_num(num)}/{_num(den)} ≈ {_g(post)}")
    steps = [
        (f"{N} kişide {c_tr} (D): {N}·{_num(prev)} = {_v(D)};  {h_tr}: {N} − {_v(D)} = {_v(H)}",
         f"Among {N} people, {c_en} (D): {N}·{_num(prev)} = {_v(D)};  {h_en}: {N} − {_v(D)} = {_v(H)}"),
        (f"{_cap(c_tr)} grubunda testi pozitif çıkan (duyarlılık {_num(sens)}): {_v(D)}·{_num(sens)} = {_v(TP)} "
         f"doğru pozitif;  {_v(FN)} yanlış negatif",
         f"Positive tests in the {c_en} group (sensitivity {_num(sens)}): {_v(D)}·{_num(sens)} = {_v(TP)} "
         f"true positive(s);  {_v(FN)} false negative(s)"),
        (f"{_cap(h_tr)} grubunda testi pozitif çıkan (1 − özgüllük = {_num(1 - spec)}): {_v(H)}·{_num(1 - spec)} "
         f"= {_v(FP)} yanlış pozitif",
         f"Positive tests in the {h_en} group (1 − specificity = {_num(1 - spec)}): {_v(H)}·{_num(1 - spec)} "
         f"= {_v(FP)} false positive(s)"),
        (f"Pozitif sonuçların toplamı: {_v(TP)} + {_v(FP)} = {_v(pos)}",
         f"All positive results: {_v(TP)} + {_v(FP)} = {_v(pos)}"),
        (f"P(D | +) = (doğru pozitif)/(tüm pozitifler) = {_v(TP)}/{_v(pos)}{red} ≈ {_g(post)} "
         f"({_pc(post, True)})",
         f"P(D | +) = true positives / all positives = {_v(TP)}/{_v(pos)}{red} ≈ {_g(post)} "
         f"({_pc(post, False)})"),
        ("Bayes formülü: P(D|+) = P(+|D)·P(D) / [P(+|D)·P(D) + P(+|D')·P(D')] = " + bt,
         "Bayes' formula: P(D|+) = P(+|D)·P(D) / [P(+|D)·P(D) + P(+|D')·P(D')] = " + bt),
        (f"Ayrıca P({h_tr} | −) = {_v(TN)}/{_v(TN + FN)} ≈ {_g(npv)}"
         + (": negatif sonuç çok güvenilir" if good else ""),
         f"Also P({h_en} | −) = {_v(TN)}/{_v(TN + FN)} ≈ {_g(npv)}"
         + (": a negative result is very reliable" if good else "")),
    ]
    return {"answer": (f"P({c_tr} | +) = {_v(TP)}/{_v(pos)} ≈ {_g(post)} ({_pc(post, True)})",
                       f"P({c_en} | +) = {_v(TP)}/{_v(pos)} ≈ {_g(post)} ({_pc(post, False)})"),
            "steps": steps,
            "fmt": {"prev_pct": _g(100 * prev, 2), "sens_pct": _g(100 * sens, 2),
                    "spec_pct": _g(100 * spec, 2)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    N, prev, sens, spec, D, H, TP, FN, FP, TN = _counts(P)
    cn, hn = (x[0 if tr else 1] for x in _names(P))
    pos = TP + FP
    post = TP / pos if pos else Fraction(0)
    unit = 1.0 if N <= 2000 else N / 1000.0
    M = int(round(N / unit))
    d_ic = max(0, min(M, int(round(float(D) / unit))))
    tp_ic = max(0, min(d_ic, int(round(float(TP) / unit))))
    fp_ic = max(0, min(M - d_ic, int(round(float(FP) / unit))))
    rows = max(1, int(round(math.sqrt(M / 1.6))))
    cols = int(math.ceil(M / rows))
    idx = np.arange(M)
    gx = idx // rows
    gy = rows - 1 - (idx % rows)
    GRAY, RED, PINK, ORANGE = (to_rgba("#CBD5E1"), to_rgba("#DC2626"), to_rgba("#FCA5A5"),
                               to_rgba("#E07B39"))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.75, 1], left=0.015, right=0.99, top=0.9, bottom=0.15,
                          wspace=0.05)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    tx.axis("off")
    ax.axis("off")
    ax.set_xlim(-0.8, cols - 0.2)
    ax.set_ylim(-0.8, rows - 0.2)
    ax.set_aspect("equal")
    size = (4.4 * 72 / max(cols, 1)) ** 2 * 0.45
    sc = ax.scatter(gx, gy, s=size * 1.2, c=np.tile(GRAY, (M, 1)), marker="o", linewidths=0)
    title = ax.set_title("", fontsize=11)
    hs = [Line2D([], [], marker="o", ls="", color=c, ms=8, label=l) for c, l in (
        ("#DC2626", f"{cn}, test +"), ("#FCA5A5", f"{cn}, test −"),
        ("#E07B39", f"{hn}, test +"), ("#CBD5E1", f"{hn}, test −"))]
    ax.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=4, fontsize=8.5,
              frameon=False, handletextpad=0.2, columnspacing=1.0)
    unit_note = "" if unit == 1.0 else ((f" (1 simge = {unit:g} kişi)") if tr else (f" (1 icon = {unit:g} people)"))
    L = [(0, (f"Topluluk: {N} kişi" if tr else f"Population: {N} people") + unit_note, "#111827", 10.5),
         (18, f"{cn} (D): {N}·{_num(prev)} = {_v(D)}",
          "#DC2626", 10.5),
         (48, (f"Doğru pozitif: {_v(D)}·{_num(sens)} = {_v(TP)}" if tr else
               f"True positive: {_v(D)}·{_num(sens)} = {_v(TP)}"), "#B91C1C", 10.5),
         (56, (f"Yanlış negatif: {_v(D)} − {_v(TP)} = {_v(FN)}" if tr else
               f"False negative: {_v(D)} − {_v(TP)} = {_v(FN)}"), "#F87171", 10.5),
         (74, (f"Yanlış pozitif: {_v(H)}·{_num(1 - spec)} = {_v(FP)}" if tr else
               f"False positive: {_v(H)}·{_num(1 - spec)} = {_v(FP)}"), "#C2410C", 10.5),
         (104, (f"Pozitif sonuç: {_v(TP)} + {_v(FP)} = {_v(pos)}" if tr else
                f"Positive results: {_v(TP)} + {_v(FP)} = {_v(pos)}"), "#111827", 10.5),
         (122, f"P({cn} | +) = {_v(TP)}/{_v(pos)}",
          "#111827", 11.5),
         (122, f"≈ {_pc(post, tr)}", "#DC2626", 17)]
    tl = []
    yy = 0.97
    for fr0, txt, col, fs in L:
        tl.append((fr0, tx.text(0.03, yy, txt, transform=tx.transAxes, va="top", fontsize=fs, color=col,
                                fontweight=("bold" if fs > 11 else "normal"))))
        yy -= 0.085 if fs < 12 else 0.1
    wtp = float(TP / pos) if pos else 0.0
    rtp = tx.add_patch(Rectangle((0.03, 0.06), 0, 0.09, transform=tx.transAxes, fc="#DC2626", lw=0))
    rfp = tx.add_patch(Rectangle((0.03, 0.06), 0, 0.09, transform=tx.transAxes, fc="#E07B39", lw=0))
    bl = tx.text(0.03, 0.17, "", transform=tx.transAxes, fontsize=9, color="#374151")
    N_FR = 150

    def ramp(i, a, b):
        return min(1.0, max(0.0, (i - a) / (b - a)))

    def update(i):
        col = np.tile(GRAY, (M, 1))
        nd = int(round(ramp(i, 18, 42) * d_ic))
        col[:nd] = RED
        nfn = int(round(ramp(i, 48, 68) * (d_ic - tp_ic)))
        col[tp_ic:tp_ic + nfn] = PINK
        nfp = int(round(ramp(i, 74, 98) * fp_ic))
        col[d_ic:d_ic + nfp] = ORANGE
        u5 = ramp(i, 104, 118)
        if u5 > 0:
            dim = 1.0 - 0.8 * u5
            col[tp_ic:d_ic, 3] = dim
            col[d_ic + fp_ic:, 3] = dim
        sc.set_facecolors(col)
        for fr0, t in tl:
            t.set_visible(i >= fr0)
        ub = ramp(i, 122, 140)
        rtp.set_width(0.94 * wtp * ub)
        rfp.set_x(0.03 + 0.94 * wtp * ub)
        rfp.set_width(0.94 * (1 - wtp) * ub)
        bl.set_text(((f"pozitiflerin içinde: {cn} {_v(TP)} | {hn} {_v(FP)}") if tr else
                     (f"among positives: {cn} {_v(TP)} | {hn} {_v(FP)}")) if ub > 0 else "")
        if i < 18:
            title.set_text((f"Her nokta bir kişi: {N} kişilik topluluk" if tr else
                            f"Each dot is a person: a population of {N}") if unit == 1.0 else
                           (f"{N} kişilik topluluk (1 simge = {unit:g} kişi)" if tr else
                            f"A population of {N} (1 icon = {unit:g} people)"))
        elif i < 48:
            title.set_text((f"Yaygınlık {_pc(prev, True)}: {_v(D)} kişi {cn}" if tr else
                            f"Prevalence {_pc(prev, False)}: {_v(D)} people are {cn}"))
        elif i < 74:
            title.set_text((f"{_cap(cn)} grubunda test (duyarlılık {_pc(sens, True)}): {_v(TP)} pozitif, {_v(FN)} negatif"
                            if tr else
                            f"Test in the {cn} group (sensitivity {_pc(sens, False)}): {_v(TP)} positive, {_v(FN)} negative"))
        elif i < 104:
            title.set_text((f"{_cap(hn)} grubunda yanlış alarm (özgüllük {_pc(spec, True)}): {_v(FP)} pozitif" if tr else
                            f"False alarms in the {hn} group (specificity {_pc(spec, False)}): {_v(FP)} positive"))
        elif i < 122:
            title.set_text(("Yalnızca testi pozitif çıkanlara bak" if tr else "Look only at the positive results"))
        else:
            title.set_text((f"{_v(pos)} pozitiften yalnızca {_v(TP)} kişi gerçekten {cn}" if tr else
                            f"Only {_v(TP)} of the {_v(pos)} positives are really {cn}"))
        return []

    return N_FR, update


def vary(P, rnd):
    while True:
        N = rnd.choice([1000, 1000, 2000])
        if float(Fraction(str(P["prevalence"]))) <= 0.01:
            prev = rnd.choice([0.005, 0.01, 0.01, 0.02])
        else:
            prev = rnd.choice([0.02, 0.05, 0.1])
        sens = rnd.choice([0.8, 0.9, 0.95])
        spec = rnd.choice([0.8, 0.9, 0.95, 0.98])
        D = N * Fraction(str(prev))
        H = N - D
        ok = all(Fraction(v).denominator == 1 for v in (D, D * Fraction(str(sens)), H * (1 - Fraction(str(spec)))))
        if ok and D * Fraction(str(sens)) > 0:
            out = {"prevalence": prev, "sensitivity": sens, "specificity": spec, "population": N}
            for key in ("cond", "nocond"):
                if key in P:
                    out[key] = P[key]
            return out
''',
}
EXAMPLES += [
    {"id": "prob-bayes-1", "kind": "bayes_grid",
     "title": ("Tarama testi: pozitif sonuç ne anlama gelir?", "Screening test: what does a positive mean?"),
     "q": ("Bir hastalığın yaygınlığı %{prev_pct}. Testin duyarlılığı %{sens_pct}, özgüllüğü %{spec_pct}. "
           "Testi pozitif çıkan birinin gerçekten hasta olma olasılığı nedir? ({population} kişilik bir "
           "toplulukla düşün.)",
           "A disease has prevalence {prev_pct}%. The test has sensitivity {sens_pct}% and specificity "
           "{spec_pct}%. What is the probability that someone with a positive result is really sick? "
           "(Think of a group of {population} people.)"),
     "P": {"prevalence": 0.02, "sensitivity": 0.9, "specificity": 0.95, "population": 1000}},
    {"id": "prob-bayes-2", "kind": "bayes_grid", "topics": ["rare disease", "nadir hastalık"],
     "title": ("Nadir hastalık paradoksu", "The rare-disease paradox"),
     "q": ("Görülme sıklığı %{prev_pct} olan bir hastalığın testinde duyarlılık %{sens_pct}, özgüllük "
           "%{spec_pct}. {population} kişi test edilirse pozitif çıkanların ne kadarı gerçekten hastadır?",
           "A disease affects {prev_pct}% of people; the test has sensitivity {sens_pct}% and specificity "
           "{spec_pct}%. If {population} people are tested, what fraction of the positives are really sick?"),
     "P": {"prevalence": 0.01, "sensitivity": 0.9, "specificity": 0.9, "population": 1000}},
    {"id": "prob-bayes-3", "kind": "bayes_grid", "topics": ["drug test", "spam filter", "doping"],
     "title": ("Doping testi", "A doping test"),
     "q": ("Sporcular arasında yasaklı madde kullanım oranı %{prev_pct}. Test, kullananları %{sens_pct} "
           "olasılıkla yakalıyor; kullanmayanları %{spec_pct} olasılıkla temiz gösteriyor. {population} "
           "sporcu test ediliyor: testi pozitif çıkan bir sporcunun gerçekten kullanıcı olma olasılığı nedir?",
           "{prev_pct}% of athletes use a banned substance. The test catches {sens_pct}% of users and clears "
           "{spec_pct}% of non-users. Among {population} athletes, what is the probability that a positive "
           "athlete is really a user?"),
     "P": {"prevalence": 0.05, "sensitivity": 0.95, "specificity": 0.98, "population": 2000,
           "cond": ["kullanıcı", "users"], "nocond": ["temiz", "clean"]}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["probability_tree"] = {
    "course": "prob",
    "title": ("Olasılık ağacı: toplam olasılık ve Bayes", "Probability tree: total probability and Bayes"),
    "topics": ["tree diagram", "probability tree", "total probability", "law of total probability",
               "conditional probability", "bayes", "dependent events", "multiplication rule",
               "ağaç diyagramı", "olasılık ağacı", "toplam olasılık", "koşullu olasılık", "bağımlı olaylar",
               "çarpma kuralı"],
    "code": r'''
import numpy as np
from fractions import Fraction


def _g(x, nd=4):
    s = f"{float(x):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _fr(v):
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _n(v):
    v = Fraction(v)
    for d in range(7):
        if (v * 10 ** d).denominator == 1:
            return f"{float(v):.{d}f}"
    return _fr(v)


def _setup(P):
    pA = Fraction(str(P["pA"]))
    pBA = Fraction(str(P["pBA"]))
    pBnA = Fraction(str(P["pBnA"]))
    names = {}
    for key, dflt in (("A", "A"), ("Ac", "A'"), ("B", "B"), ("Bc", "B'")):
        v = P.get(key)
        if isinstance(v, (list, tuple)) and len(v) == 2:
            names[key] = (str(v[0]), str(v[1]))
        elif isinstance(v, str) and v:
            names[key] = (v, v)
        else:
            names[key] = (dflt, dflt)
    return pA, pBA, pBnA, names


def _calc(pA, pBA, pBnA):
    pAc = 1 - pA
    j1, j2 = pA * pBA, pAc * pBnA
    pB = j1 + j2
    post = j1 / pB if pB else Fraction(0)
    return pAc, j1, j2, pB, post


def solve(P):
    pA, pBA, pBnA, nm = _setup(P)
    pAc, j1, j2, pB, post = _calc(pA, pBA, pBnA)
    pst = f"{_fr(post)} ≈ {_g(post)}" if post.denominator > 1 else _fr(post)
    steps = [
        (f"Olaylar: A = {nm['A'][0]}, A' = {nm['Ac'][0]};  B = {nm['B'][0]}, B' = {nm['Bc'][0]}",
         f"Events: A = {nm['A'][1]}, A' = {nm['Ac'][1]};  B = {nm['B'][1]}, B' = {nm['Bc'][1]}"),
        (f"1. aşama dalları: P(A) = {_n(pA)},  P(A') = 1 − {_n(pA)} = {_n(pAc)}",
         f"First-stage branches: P(A) = {_n(pA)},  P(A') = 1 − {_n(pA)} = {_n(pAc)}"),
        (f"2. aşama (koşullu) dallar: P(B|A) = {_n(pBA)}, P(B'|A) = {_n(1 - pBA)};  "
         f"P(B|A') = {_n(pBnA)}, P(B'|A') = {_n(1 - pBnA)}",
         f"Second-stage (conditional) branches: P(B|A) = {_n(pBA)}, P(B'|A) = {_n(1 - pBA)};  "
         f"P(B|A') = {_n(pBnA)}, P(B'|A') = {_n(1 - pBnA)}"),
        (f"Dal boyunca çarp: P(A ∩ B) = P(A)·P(B|A) = {_n(pA)}·{_n(pBA)} = {_n(j1)};  "
         f"P(A' ∩ B) = {_n(pAc)}·{_n(pBnA)} = {_n(j2)}",
         f"Multiply along the branches: P(A ∩ B) = P(A)·P(B|A) = {_n(pA)}·{_n(pBA)} = {_n(j1)};  "
         f"P(A' ∩ B) = {_n(pAc)}·{_n(pBnA)} = {_n(j2)}"),
        (f"Toplam olasılık: P(B) = P(A ∩ B) + P(A' ∩ B) = {_n(j1)} + {_n(j2)} = {_n(pB)}",
         f"Total probability: P(B) = P(A ∩ B) + P(A' ∩ B) = {_n(j1)} + {_n(j2)} = {_n(pB)}"),
        (f"Bayes: P(A | B) = P(A ∩ B) / P(B) = {_n(j1)} / {_n(pB)} = {pst}",
         f"Bayes: P(A | B) = P(A ∩ B) / P(B) = {_n(j1)} / {_n(pB)} = {pst}"),
    ]
    return {"answer": (f"P(B) = {_n(pB)};  P(A | B) = {pst}", f"P(B) = {_n(pB)};  P(A | B) = {pst}"),
            "steps": steps,
            "fmt": {"nA": nm["A"], "nAc": nm["Ac"], "nB": nm["B"], "nBc": nm["Bc"],
                    "pApct": _g(100 * pA, 2), "pAcpct": _g(100 * pAc, 2), "pBApct": _g(100 * pBA, 2),
                    "pBnApct": _g(100 * pBnA, 2)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    L = 0 if tr else 1
    pA, pBA, pBnA, nm = _setup(P)
    pAc, j1, j2, pB, post = _calc(pA, pBA, pBnA)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.6, 1], left=0.01, right=0.99, top=0.9, bottom=0.04,
                          wspace=0.03)
    ax = fig.add_subplot(gs[0, 0])
    tx = fig.add_subplot(gs[0, 1])
    ax.axis("off")
    tx.axis("off")
    ax.set_xlim(-0.25, 3.85)
    ax.set_ylim(-2.3, 2.3)
    root, nA, nAc = (0.0, 0.0), (1.1, 1.15), (1.1, -1.15)
    lv = [(2.3, 1.75), (2.3, 0.55), (2.3, -0.55), (2.3, -1.75)]
    edges = [(root, nA, pA), (root, nAc, pAc), (nA, lv[0], pBA), (nA, lv[1], 1 - pBA),
             (nAc, lv[2], pBnA), (nAc, lv[3], 1 - pBnA)]
    t_edge = [(4, 18), (12, 26), (30, 44), (38, 52), (46, 60), (54, 68)]
    elines = [ax.plot([], [], color="#6B7280", lw=2.2, solid_capstyle="round")[0] for _ in edges]
    elabs = []
    for (p0, p1, pr) in edges:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        up = p1[1] > p0[1]
        elabs.append(ax.text(mx - 0.05, my + (0.17 if up else -0.17), _n(pr), ha="center",
                             va="bottom" if up else "top", fontsize=10.5, color="#1D4ED8",
                             fontweight="bold", visible=False))
    ax.plot([0], [0], "o", color="#111827", ms=8)
    box = dict(boxstyle="round,pad=0.3", fc="#EFF6FF", ec="#2563EB")
    lbox = dict(boxstyle="round,pad=0.25", fc="#F9FAFB", ec="#9CA3AF")
    nodes = [ax.text(nA[0], nA[1], nm["A"][L], ha="center", va="center", fontsize=10.5, bbox=box,
                     visible=False),
             ax.text(nAc[0], nAc[1], nm["Ac"][L], ha="center", va="center", fontsize=10.5, bbox=box,
                     visible=False)]
    lnames = [nm["B"][L], nm["Bc"][L], nm["B"][L], nm["Bc"][L]]
    leaves = [ax.text(x, y, lnames[m], ha="center", va="center", fontsize=10, bbox=dict(lbox),
                      visible=False) for m, (x, y) in enumerate(lv)]
    prods = [(pA, pBA, j1), (pA, 1 - pBA, pA * (1 - pBA)), (pAc, pBnA, j2), (pAc, 1 - pBnA, pAc * (1 - pBnA))]
    ptx = [ax.text(2.62, y, f"{_n(a)}·{_n(b)} = {_n(c)}", ha="left", va="center", fontsize=10,
                   visible=False) for (a, b, c), (x, y) in zip(prods, lv)]
    t_prod = [72, 80, 88, 96]
    title = ax.set_title("", fontsize=11.5)
    named = nm["A"][L] != "A" or nm["B"][L] != "B"
    rl = [(0, f"A: {nm['A'][L]}    A': {nm['Ac'][L]}" if named else "", "#1D4ED8", 10),
          (0, f"B: {nm['B'][L]}    B': {nm['Bc'][L]}" if named else "", "#374151", 10),
          (72, f"P(A ∩ B) = {_n(pA)}·{_n(pBA)} = {_n(j1)}", "#111827", 10.5),
          (88, f"P(A' ∩ B) = {_n(pAc)}·{_n(pBnA)} = {_n(j2)}", "#111827", 10.5),
          (104, "Toplam olasılık:" if tr else "Total probability:", "#15803D", 10),
          (104, f"P(B) = {_n(j1)} + {_n(j2)} = {_n(pB)}", "#15803D", 11.5),
          (120, "Bayes:", "#DC2626", 10),
          (120, "P(A | B) = P(A ∩ B) / P(B)", "#DC2626", 11),
          (130, f"= {_n(j1)} / {_n(pB)}", "#DC2626", 11),
          (136, f"= {_fr(post)} ≈ {_g(post)}" if post.denominator > 1 else f"= {_fr(post)}", "#DC2626", 14)]
    rtxt = []
    yy = 0.95
    for fr0, s, col, fs in rl:
        rtxt.append((fr0, tx.text(0.02, yy, s, transform=tx.transAxes, va="top", fontsize=fs, color=col,
                                  fontweight="bold" if fs >= 11.5 else "normal", visible=False)))
        yy -= 0.075 if fs <= 10 else (0.09 if fs < 14 else 0.11)
    N = 150

    def ramp(i, a, b):
        return min(1.0, max(0.0, (i - a) / (b - a)))

    def update(i):
        for m, ((p0, p1, pr), ln, (a, b)) in enumerate(zip(edges, elines, t_edge)):
            u = ramp(i, a, b)
            ln.set_data([p0[0], p0[0] + (p1[0] - p0[0]) * u], [p0[1], p0[1] + (p1[1] - p0[1]) * u])
            elabs[m].set_visible(u >= 1)
            col, lw = "#6B7280", 2.2
            if i >= 120:
                if m in (0, 2):
                    col, lw = "#DC2626", 4.2
                elif m == 1 or m == 4:
                    col, lw = "#86EFAC", 3.0
                else:
                    col = "#D1D5DB"
            elif i >= 104 and m in (0, 1, 2, 4):
                col, lw = "#16A34A", 3.6
            ln.set_color(col)
            ln.set_linewidth(lw)
        nodes[0].set_visible(i >= t_edge[0][1])
        nodes[1].set_visible(i >= t_edge[1][1])
        for m, t in enumerate(leaves):
            t.set_visible(i >= t_edge[m + 2][1])
        for m, t in enumerate(ptx):
            t.set_visible(i >= t_prod[m])
            green = i >= 104 and m in (0, 2)
            red = i >= 120 and m == 0
            t.set_color("#DC2626" if red else ("#15803D" if green else "#111827"))
            t.set_fontweight("bold" if green else "normal")
        for fr0, t in rtxt:
            t.set_visible(i >= fr0)
        if i < 30:
            title.set_text(("1. aşama: A ya da A'" if tr else "Stage 1: A or A'"))
        elif i < 72:
            title.set_text(("2. aşama: koşullu olasılıklar P(B|A), P(B|A')" if tr else
                            "Stage 2: conditional probabilities P(B|A), P(B|A')"))
        elif i < 104:
            title.set_text(("Her yol için dallardaki olasılıkları çarp" if tr else
                            "Multiply the probabilities along each path"))
        elif i < 120:
            title.set_text((f"B'ye giden yolları topla: P(B) = {_n(pB)}" if tr else
                            f"Add the paths that end in B: P(B) = {_n(pB)}"))
        else:
            title.set_text((f"Bayes: kırmızı yol / yeşil yollar ⇒ P(A|B) ≈ {_g(post)}" if tr else
                            f"Bayes: red path / green paths ⇒ P(A|B) ≈ {_g(post)}"))
        return []

    return N, update


def vary(P, rnd):
    small = max(float(Fraction(str(P["pBA"]))), float(Fraction(str(P["pBnA"])))) <= 0.1
    opts = ([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.1] if small else
            [0.05, 0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
    while True:
        pA = rnd.choice([0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8])
        b1 = rnd.choice(opts)
        b2 = rnd.choice(opts)
        if b1 != b2:
            break
    out = {"pA": pA, "pBA": b1, "pBnA": b2}
    for key in ("A", "Ac", "B", "Bc"):
        if key in P:
            out[key] = P[key]
    return out
''',
}
EXAMPLES += [
    {"id": "prob-tree-1", "kind": "probability_tree", "topics": ["defective", "factory", "kusurlu"],
     "title": ("İki makine ve kusurlu ürün", "Two machines and a defective item"),
     "q": ("Bir fabrikada üretimin %{pApct} kadarı 1. makineden, geri kalanı 2. makineden çıkıyor. Kusur "
           "oranları sırasıyla %{pBApct} ve %{pBnApct}. Rastgele bir ürünün kusurlu olma olasılığı nedir? "
           "Kusurlu bir ürünün 1. makineden gelme olasılığı nedir?",
           "Machine 1 makes {pApct}% of a factory's items and machine 2 the rest. Their defect rates are "
           "{pBApct}% and {pBnApct}%. What is the probability that a random item is defective? Given that "
           "an item is defective, what is the probability it came from machine 1?"),
     "P": {"pA": 0.6, "pBA": 0.03, "pBnA": 0.05, "A": ["Makine 1", "Machine 1"],
           "Ac": ["Makine 2", "Machine 2"], "B": ["Kusurlu", "Defective"], "Bc": ["Sağlam", "OK"]}},
    {"id": "prob-tree-2", "kind": "probability_tree", "topics": ["weather", "hava durumu"],
     "title": ("Yağmur ve geç kalma", "Rain and being late"),
     "q": ("Bir günün yağmurlu olma olasılığı {pA}. Yağmurlu günde servisin gecikme olasılığı {pBA}, "
           "kuru günde {pBnA}. Servisin gecikme olasılığı nedir? Servis geciktiyse o gün yağmur yağmış "
           "olma olasılığı nedir?",
           "The chance of rain on a given day is {pA}. On a rainy day the bus is late with probability {pBA}, "
           "on a dry day with probability {pBnA}. What is the probability that the bus is late? If the bus "
           "was late, what is the probability that it rained?"),
     "P": {"pA": 0.3, "pBA": 0.4, "pBnA": 0.1, "A": ["Yağmur", "Rain"], "Ac": ["Kuru", "Dry"],
           "B": ["Gecikme", "Late"], "Bc": ["Zamanında", "On time"]}},
    {"id": "prob-tree-3", "kind": "probability_tree",
     "title": ("Ağaç diyagramıyla P(B) ve P(A|B)", "P(B) and P(A|B) from a tree diagram"),
     "q": ("P(A) = {pA}, P(B|A) = {pBA}, P(B|A') = {pBnA} veriliyor. Ağaç diyagramı çizerek P(B) ve "
           "P(A|B) değerlerini bul.",
           "Given P(A) = {pA}, P(B|A) = {pBA} and P(B|A') = {pBnA}, draw a tree diagram and find P(B) "
           "and P(A|B)."),
     "P": {"pA": 0.5, "pBA": 0.2, "pBnA": 0.6}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["counting"] = {
    "course": "prob",
    "title": ("Sayma: permütasyon ve kombinasyon", "Counting: permutations and combinations"),
    "topics": ["permutation", "permutations", "combination", "combinations", "counting principle",
               "fundamental counting principle", "factorial", "arrangements", "n choose r", "npr", "ncr",
               "permütasyon", "kombinasyon", "sayma", "faktöriyel", "sıralama", "çarpma ilkesi"],
    "code": r'''
import itertools
import math
import numpy as np
from matplotlib.patches import Rectangle

_PAL = ["#2563EB", "#E07B39", "#16A34A", "#DC2626", "#7C3AED", "#0891B2", "#DB2777", "#CA8A04", "#4B5563"]


def _setup(P):
    n = max(1, min(9, int(P["n"])))
    r = max(0, min(n, int(P["r"])))
    mode = "comb" if str(P.get("mode", "perm")).lower().startswith("c") else "perm"
    items = P.get("items")
    if isinstance(items, (list, tuple)) and len(items) >= n:
        labels = [str(v) for v in items[:n]]
    else:
        labels = list("ABCDEFGHI")[:n]
    return n, r, mode, labels


def _prod(n, r):
    return "·".join(str(n - j) for j in range(r)) if r else "1"


def solve(P):
    n, r, mode, labels = _setup(P)
    npr, ncr, fr = math.perm(n, r), math.comb(n, r), math.factorial(r)
    fn, fnr = math.factorial(n), math.factorial(n - r)
    slots_tr = ", ".join(f"{j + 1}. yer {n - j}" for j in range(r))
    slots_en = ", ".join(f"slot {j + 1}: {n - j}" for j in range(r))
    if mode == "perm":
        steps = [
            (f"Sıra önemli, tekrar yok ⇒ permütasyon: {n} öğeden {r} tanesi sıralanıyor",
             f"Order matters, no repetition ⇒ permutation: {r} of {n} items are arranged"),
            (f"Çarpma ilkesi — seçenek sayıları: {slots_tr}", f"Multiplication principle — choices: {slots_en}"),
            (f"P({n},{r}) = {n}!/({n} − {r})! = {fn}/{fnr} = {_prod(n, r)} = {npr}",
             f"P({n},{r}) = {n}!/({n} − {r})! = {fn}/{fnr} = {_prod(n, r)} = {npr}"),
            (f"Kontrol: ilk öğeye göre {n} grup, her grupta {npr // n} dizilim ⇒ {n}·{npr // n} = {npr}",
             f"Check: {n} groups by the first item, {npr // n} arrangements each ⇒ {n}·{npr // n} = {npr}"),
        ]
        ans = (f"P({n},{r}) = {npr}", f"P({n},{r}) = {npr}")
    else:
        steps = [
            (f"Sıra önemsiz ⇒ kombinasyon: {n} öğeden {r} tanesi seçiliyor",
             f"Order does not matter ⇒ combination: choose {r} of {n} items"),
            (f"Önce sıralı seçimler: P({n},{r}) = {_prod(n, r)} = {npr}",
             f"First count ordered selections: P({n},{r}) = {_prod(n, r)} = {npr}"),
            (f"Aynı {r} öğe {r}! = {fr} farklı sırada sayıldı ⇒ sonucu {fr} ile böl",
             f"Each group of {r} was counted {r}! = {fr} times (once per order) ⇒ divide by {fr}"),
            (f"C({n},{r}) = P({n},{r})/{r}! = {npr}/{fr} = {ncr}  (= {n}!/({r}!·{n - r}!))",
             f"C({n},{r}) = P({n},{r})/{r}! = {npr}/{fr} = {ncr}  (= {n}!/({r}!·{n - r}!))"),
        ]
        if ncr <= 20 and all(len(s) == 1 for s in labels):
            grp = ", ".join("".join(labels[j] for j in c) for c in itertools.combinations(range(n), r))
            steps.append((f"Gruplar: {grp}", f"Groups: {grp}"))
        ans = (f"C({n},{r}) = {ncr}", f"C({n},{r}) = {ncr}")
    return {"answer": ans, "steps": steps,
            "fmt": {"npr": str(npr), "ncr": str(ncr), "items": ", ".join(labels)}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    n, r, mode, labels = _setup(P)
    npr, ncr, fr = math.perm(n, r), math.comb(n, r), math.factorial(r)
    single = all(len(s) == 1 for s in labels)

    def word(t):
        return ("" if single else "-").join(labels[j] for j in t) or "∅"

    RMAX, CMAX = 15, 8
    cells = []
    if mode == "perm":
        allp = list(itertools.permutations(range(n), r))
        ncol = n if r >= 1 else 1
        nrow = max(1, len(allp) // ncol)
        for idx, t in enumerate(allp):
            cells.append((idx % nrow, idx // nrow, word(t), True, t[0] if t else 0))
    else:
        combos = list(itertools.combinations(range(n), r))
        ncol, nrow = fr, len(combos)
        for rr, cb in enumerate(combos):
            for c, t in enumerate(itertools.permutations(cb)):
                cells.append((rr, c, word(t), c == 0, 0))
    shown = [cl for cl in cells if cl[0] < RMAX and cl[1] < CMAX]
    nr_s, nc_s = min(nrow, RMAX), min(ncol, CMAX)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    maxlen = max(len(c[2]) for c in shown) if shown else 1
    rowh_pt = 0.72 * 0.96 * 5.4 * 72 / nr_s
    gw = min(0.96, max(0.3, 0.17 * nc_s))
    gx0 = 0.5 - gw / 2
    colw_pt = gw * 0.96 * 8 * 72 / nc_s
    fs = max(6.0, min(14.0, 0.55 * rowh_pt, 0.85 * colw_pt / (0.62 * maxlen + 0.5)))
    texts = []
    for (rr, c, w, keep, first) in shown:
        x = gx0 + (c + 0.5) * gw / nc_s
        y = 0.75 - (rr + 0.5) * 0.72 / nr_s
        col = _PAL[first % len(_PAL)] if mode == "perm" else "#111827"
        texts.append(ax.text(x, y, w, ha="center", va="center", fontsize=fs, family="DejaVu Sans Mono",
                             color=col, alpha=0))
    if mode == "perm" and nc_s > 1:
        for c in range(1, nc_s):
            xs = gx0 + c * gw / nc_s
            ax.plot([xs, xs], [0.03, 0.765], color="#E5E7EB", lw=1)
    keepbg = Rectangle((gx0, 0.03), gw / nc_s, 0.735, fc="#DCFCE7", ec="#16A34A", lw=1.2, alpha=0, zorder=0)
    ax.add_patch(keepbg)
    hidden = len(cells) - len(shown)
    more = ax.text(0.98, 0.0, ((f"… (+{hidden} tane daha)" if tr else f"… (+{hidden} more)") if hidden else ""),
                   ha="right", va="bottom", fontsize=9.5, color="#6B7280", alpha=0)
    ax.text(0.01, 0.94, "Öğeler:" if tr else "Items:", va="center", fontsize=11, fontweight="bold")
    sp = max(0.055, 0.012 * max(len(s) for s in labels) + 0.03)
    itm = [ax.text(0.14 + j * sp, 0.94, s, ha="center", va="center", fontsize=11, color="white",
                   fontweight="bold", alpha=0,
                   bbox=dict(boxstyle="round,pad=0.35", fc=_PAL[j % len(_PAL)], ec="none", alpha=0))
           for j, s in enumerate(labels)]
    ax.text(0.01, 0.855, ("Yerler:" if mode == "perm" else "Sıralı:") if tr else
            ("Slots:" if mode == "perm" else "Ordered:"), va="center", fontsize=11, fontweight="bold")
    slots = []
    for j in range(r):
        x0 = 0.14 + j * 0.085
        rect = Rectangle((x0 - 0.0275, 0.825), 0.055, 0.06, fc="#EFF6FF", ec="#2563EB", lw=1.5, alpha=0)
        ax.add_patch(rect)
        tnum = ax.text(x0, 0.855, str(n - j), ha="center", va="center", fontsize=13, fontweight="bold",
                       color="#1D4ED8", alpha=0)
        times = ax.text(x0 + 0.0425, 0.855, "×" if j < r - 1 else "", ha="center", va="center",
                        fontsize=13, alpha=0)
        slots.append((rect, tnum, times))
    res = ax.text(0.14 + max(r, 1) * 0.085 - 0.03, 0.855, "", va="center", fontsize=13, fontweight="bold",
                  color="#111827")
    info = ax.text(0.99, 0.975, "", ha="right", va="top", fontsize=11.5,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    N = 150
    nsh = len(shown)

    def ramp(i, a, b):
        return min(1.0, max(0.0, (i - a) / (b - a)))

    def update(i):
        a = ramp(i, 0, 8)
        for t in itm:
            t.set_alpha(a)
            t.get_bbox_patch().set_alpha(a)
        for j, (rect, tnum, times) in enumerate(slots):
            b = ramp(i, 10 + j * 20 / max(r, 1), 14 + j * 20 / max(r, 1))
            rect.set_alpha(b)
            tnum.set_alpha(b)
            times.set_alpha(b)
        if i >= 30:
            res.set_text(f"= {npr}" + ((f"   ÷ {r}! = {ncr}") if (mode == "comb" and i >= 105) else ""))
        else:
            res.set_text("")
        u = ramp(i, 30, 105)
        nshow = u * nsh
        fade = ramp(i, 105, 120) if mode == "comb" else 0.0
        keepbg.set_alpha(0.9 * fade)
        for m, ((rr, c, w, keep, first), t) in enumerate(zip(shown, texts)):
            al = min(1.0, max(0.0, nshow - m))
            if mode == "comb" and fade > 0:
                al = 1.0 if keep else 1.0 - 0.8 * fade
                t.set_color("#16A34A" if keep else "#9CA3AF")
                t.set_fontweight("bold" if keep else "normal")
            elif mode == "comb":
                t.set_color("#111827")
                t.set_fontweight("normal")
            t.set_alpha(al)
        more.set_alpha(1.0 if u >= 1 else 0.0)
        cnt = min(len(cells), int(round(u * len(cells))))
        if i < 30:
            info.set_text(("Kaç farklı sıralama var?\nHer yerin seçenek sayısını çarp" if tr else
                           "How many orderings?\nMultiply the choices for each slot") if mode == "perm" else
                          ("Önce sıralı seçimleri say,\nsonra sıraları ele" if tr else
                           "Count ordered selections first,\nthen remove the orderings"))
        elif i < 105:
            info.set_text(((f"Dizilimler: {cnt} / {npr}\n(sütun = ilk öğe)" if tr else
                            f"Arrangements: {cnt} / {npr}\n(column = first item)") if mode == "perm" else
                           (f"Sıralı seçimler: {cnt} / {npr}\n(her satır aynı grup)" if tr else
                            f"Ordered selections: {cnt} / {npr}\n(each row = the same group)")))
        elif mode == "perm":
            info.set_text(f"P({n},{r}) = {n}!/{n - r}! = {_prod(n, r)} = {npr}")
        elif i < 125:
            info.set_text((f"Her grup {r}! = {fr} kez sayıldı\n→ her satırdan 1 tane kalır" if tr else
                           f"Each group was counted {r}! = {fr} times\n→ keep 1 per row"))
        else:
            info.set_text(f"C({n},{r}) = {npr}/{r}! = {npr}/{fr} = {ncr}")
        return []

    return N, update


def vary(P, rnd):
    mode = "comb" if str(P.get("mode", "perm")).lower().startswith("c") else "perm"
    r = max(1, min(4, int(P["r"])))
    n = rnd.choice([v for v in range(r + 1, min(8, r + 3) + 1) if v != int(P["n"])] or [r + 1])
    out = {"n": n, "r": r, "mode": mode}
    if isinstance(P.get("items"), list) and len(P["items"]) >= n:
        out["items"] = list(P["items"])
    return out
''',
}
EXAMPLES += [
    {"id": "prob-count-1", "kind": "counting", "topics": ["podium", "race", "madalya"],
     "title": ("Madalya sıralaması (permütasyon)", "Medal podium (permutation)"),
     "q": ("{n} koşucunun ({items}) yarıştığı bir finalde altın, gümüş ve bronz madalyalar kaç farklı "
           "şekilde dağıtılabilir?",
           "{n} runners ({items}) compete in a final. In how many different ways can the gold, silver and "
           "bronze medals be awarded?"),
     "P": {"n": 5, "r": 3, "mode": "perm"}},
    {"id": "prob-count-2", "kind": "counting", "topics": ["choosing books", "selection", "seçim"],
     "title": ("Kitap seçimi (kombinasyon)", "Choosing books (combination)"),
     "q": ("Raftaki {n} kitaptan ({items}) tatile {r} tanesi götürülecek. Kaç farklı seçim yapılabilir?",
           "You take {r} of the {n} books on a shelf ({items}) on holiday. How many different selections "
           "are possible?"),
     "P": {"n": 5, "r": 3, "mode": "comb"}},
    {"id": "prob-count-3", "kind": "counting", "topics": ["handshake", "tokalaşma", "committee", "komite"],
     "title": ("Tokalaşma problemi", "The handshake problem"),
     "q": ("Bir toplantıda {n} kişinin her biri diğer herkesle bir kez tokalaşıyor. Toplam kaç tokalaşma "
           "olur? (Her tokalaşma {r} kişilik bir seçimdir.)",
           "At a meeting each of {n} people shakes hands once with everyone else. How many handshakes take "
           "place? (Each handshake is a choice of {r} people.)"),
     "P": {"n": 6, "r": 2, "mode": "comb"}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["expected_value"] = {
    "course": "prob",
    "title": ("Beklenen değer ve varyans", "Expected value and variance"),
    "topics": ["expected value", "expectation", "mean of a random variable", "discrete random variable",
               "variance of a random variable", "fair game", "probability distribution table",
               "beklenen değer", "kesikli rastgele değişken", "rastgele değişkenin varyansı", "adil oyun",
               "olasılık dağılımı tablosu"],
    "code": r'''
import math
import numpy as np
from fractions import Fraction
from matplotlib.ticker import FuncFormatter, NullLocator
from matplotlib.patches import Patch
from matplotlib.transforms import blended_transform_factory


def _g(x, nd=4):
    s = f"{float(x):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _fr(v):
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def _n(v):
    v = Fraction(v)
    for d in range(7):
        if (v * 10 ** d).denominator == 1:
            return f"{float(v):.{d}f}"
    return _fr(v)


def _nd(v):
    s = _n(v)
    return s + (f" ≈ {_g(v)}" if "/" in s else "")


def _setup(P):
    vals = [Fraction(str(v)) for v in P["values"]]
    probs = [Fraction(str(p)) for p in P["probs"]]
    m = max(1, min(len(vals), len(probs)))
    vals, probs = vals[:m], probs[:m]
    probs = [max(Fraction(0), p) for p in probs]
    tot = sum(probs)
    if tot <= 0:
        probs, tot = [Fraction(1, m)] * m, Fraction(1)
    norm = tot != 1
    probs = [p / tot for p in probs]
    plays = max(20, min(20000, int(P.get("plays", 1000))))
    return vals, probs, norm, tot, plays


def _signed(parts):
    out = ""
    for k, v in enumerate(parts):
        if k == 0:
            out = _n(v)
        else:
            out += (" − " if v < 0 else " + ") + _n(abs(v))
    return out


def _moments(vals, probs):
    E = sum(v * p for v, p in zip(vals, probs))
    E2 = sum(v * v * p for v, p in zip(vals, probs))
    return E, E2, E2 - E * E


def _sim(P, vals, probs, plays):
    rng = np.random.default_rng(int(P.get("seed", 0)))
    pf = np.array([float(p) for p in probs])
    pick = rng.choice(len(vals), size=plays, p=pf / pf.sum())
    X = np.array([float(v) for v in vals])[pick]
    return np.cumsum(X) / np.arange(1, plays + 1)


def solve(P):
    vals, probs, norm, tot, plays = _setup(P)
    E, E2, var = _moments(vals, probs)
    sd = math.sqrt(max(0.0, float(var)))
    terms = " + ".join(f"({_n(v)})·{_n(p)}" if v < 0 else f"{_n(v)}·{_n(p)}" for v, p in zip(vals, probs))
    terms2 = " + ".join(f"{_n(v * v)}·{_n(p)}" for v, p in zip(vals, probs))
    avg = _sim(P, vals, probs, plays)
    steps = []
    if norm:
        steps.append((f"Olasılıkların toplamı {_n(tot)} ≠ 1; her olasılık bu toplama bölünerek normalize edildi",
                      f"The probabilities add up to {_n(tot)} ≠ 1; each was divided by {_n(tot)} to normalise"))
    else:
        steps.append((f"Kontrol: olasılıkların toplamı {' + '.join(_n(p) for p in probs)} = 1 ✓",
                      f"Check: the probabilities add up to {' + '.join(_n(p) for p in probs)} = 1 ✓"))
    steps += [
        (f"E[X] = Σ x·P(x) = {terms} = {_signed([v * p for v, p in zip(vals, probs)])} = {_nd(E)}",
         f"E[X] = Σ x·P(x) = {terms} = {_signed([v * p for v, p in zip(vals, probs)])} = {_nd(E)}"),
        (f"E[X²] = Σ x²·P(x) = {terms2} = {_nd(E2)}", f"E[X²] = Σ x²·P(x) = {terms2} = {_nd(E2)}"),
        (f"Var(X) = E[X²] − (E[X])² = {_n(E2)} − ({_n(E)})² = {_nd(var)};  σ = √Var(X) ≈ {_g(sd, 3)}",
         f"Var(X) = E[X²] − (E[X])² = {_n(E2)} − ({_n(E)})² = {_nd(var)};  σ = √Var(X) ≈ {_g(sd, 3)}"),
        (f"Simülasyon: {plays} oyunun ortalaması {float(avg[-1]):.4f} → E[X] = {_g(E)} (büyük sayılar yasası)",
         f"Simulation: the mean of {plays} plays is {float(avg[-1]):.4f} → E[X] = {_g(E)} (law of large numbers)"),
    ]
    if E > 0:
        steps.append((f"Yorum: oyun uzun vadede oyun başına ortalama {_g(E)} kazandırır",
                      f"Interpretation: in the long run the game pays {_g(E)} per play on average"))
    elif E < 0:
        steps.append((f"Yorum: oyun uzun vadede oyun başına ortalama {_g(-E)} kaybettirir",
                      f"Interpretation: in the long run the game loses {_g(-E)} per play on average"))
    else:
        steps.append(("Yorum: E[X] = 0 ⇒ adil oyun (uzun vadede ne kazanç ne kayıp)",
                      "Interpretation: E[X] = 0 ⇒ a fair game (no gain or loss in the long run)"))
    dist = ", ".join(f"{_n(v)} ({_n(p)})" for v, p in zip(vals, probs))
    return {"answer": (f"E[X] = {_nd(E)};  Var(X) = {_nd(var)};  σ ≈ {_g(sd, 3)}",
                       f"E[X] = {_nd(E)};  Var(X) = {_nd(var)};  σ ≈ {_g(sd, 3)}"),
            "steps": steps, "fmt": {"dist": dist, "w": _n(vals[0]), "l": _n(-vals[-1])}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    vals, probs, norm, tot, plays = _setup(P)
    E, E2, var = _moments(vals, probs)
    Ef, sd = float(E), math.sqrt(max(0.0, float(var)))
    vf = np.array([float(v) for v in vals])
    pf = np.array([float(p) for p in probs])
    m = len(vals)
    avg = _sim(P, vals, probs, plays)
    ks = np.arange(1, plays + 1)
    header = fig.text(0.5, 0.965, "", ha="center", va="top", fontsize=11.5,
                      bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.2], left=0.07, right=0.98, top=0.82, bottom=0.12,
                          wspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    bx = fig.add_subplot(gs[0, 1])
    lo, hi = min(vf.min(), Ef - sd), max(vf.max(), Ef + sd)
    span = max(hi - lo, 1.0)
    x0, x1 = lo - 0.12 * span, hi + 0.12 * span
    ax.set_xlim(x0, x1)
    xa = min(0.8, max(0.2, (Ef - x0) / (x1 - x0)))
    bt = blended_transform_factory(ax.transAxes, ax.transData)
    uv = np.unique(vf)
    gap = np.diff(uv).min() if len(uv) > 1 else span
    width = min(0.6 * gap, 0.08 * span)
    top = pf.max() * 1.32
    ax.set_ylim(-0.26 * top, top)
    step = 0.5
    for st in (0.02, 0.05, 0.1, 0.2, 0.25, 0.5):
        if pf.max() / st <= 5:
            step = st
            break
    ax.set_yticks(np.arange(0, pf.max() + 1e-9, step))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:g}"))
    ax.axhline(0, color="#374151", lw=2.5)
    ax.grid(axis="y", alpha=0.3)
    ax.set_xlabel("x (kazanç)" if tr else "x (payoff)")
    ax.set_ylabel("P(X = x)")
    ax.set_title("Olasılık dağılımı" if tr else "Probability distribution", fontsize=11)
    bars = ax.bar(vf, np.zeros(m), width=width, color="#2563EB", alpha=0.85)
    plab = [ax.text(v, 0, "", ha="center", va="bottom", fontsize=9, color="#1D4ED8") for v in vf]
    ful, = ax.plot([], [], "^", color="#7C3AED", ms=17, zorder=6)
    eln, = ax.plot([], [], "--", color="#7C3AED", lw=2)
    etx = ax.text(xa, top * 0.93, "", ha="center", va="top", fontsize=10, color="#7C3AED", fontweight="bold",
                  transform=bt, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    sln, = ax.plot([], [], color="#DC2626", lw=2.5, marker="|", ms=10, mew=2.5)
    stx = ax.text(xa, -0.175 * top, "", ha="center", va="top", fontsize=9.5, color="#DC2626", transform=bt)
    bx.set_xscale("log")
    bx.set_xlim(1, plays * 1.5)
    bx.xaxis.set_major_formatter(FuncFormatter(lambda v, pos: f"{v:g}"))
    bx.xaxis.set_minor_locator(NullLocator())
    k0 = min(9, plays - 1)
    dev = max(float(np.abs(avg[k0:] - Ef).max()) * 1.15, 4 * sd / math.sqrt(plays), 1e-3)
    bx.set_ylim(Ef - dev, Ef + dev)
    xb = np.unique(np.round(np.logspace(0, math.log10(plays), 300))).astype(float)
    bx.fill_between(xb, Ef - 2 * sd / np.sqrt(xb), Ef + 2 * sd / np.sqrt(xb), color="#16A34A", alpha=0.13, lw=0)
    eh = bx.axhline(Ef, color="#7C3AED", ls="--", lw=2, label=f"E[X] = {_g(E)}")
    aln, = bx.plot([], [], color="#2563EB", lw=1.6, label=("ortalama kazanç" if tr else "average payoff"))
    adt, = bx.plot([], [], "o", color="#DC2626", ms=6, zorder=5)
    bx.legend(handles=[aln, eh, Patch(color="#16A34A", alpha=0.25, label="E[X] ± 2σ/√n")],
              loc="upper right", fontsize=9)
    bx.grid(alpha=0.3)
    bx.set_xlabel("oyun sayısı n (log ölçek)" if tr else "number of plays n (log scale)")
    bx.set_title("Simülasyon: n oyunun ortalaması" if tr else "Simulation: mean of n plays", fontsize=11)
    term_s = [(f"({_n(v)})·{_n(p)}" if v < 0 else f"{_n(v)}·{_n(p)}") for v, p in zip(vals, probs)]
    N, T0, T1, F0, S0, S1, V0 = 165, 18, 60, 62, 76, 140, 142

    def ramp(i, a, b):
        return min(1.0, max(0.0, (i - a) / (b - a)))

    def update(i):
        u = ramp(i, 0, 16)
        nterm = 0 if i < T0 else min(m, 1 + int((i - T0) * m / (T1 - T0)))
        for j, (b, t) in enumerate(zip(bars, plab)):
            b.set_height(pf[j] * u)
            t.set_y(pf[j] * u + top * 0.01)
            t.set_text(_n(probs[j]) if u >= 1 else "")
            b.set_color("#E07B39" if (T0 <= i < F0 and j == nterm - 1) else "#2563EB")
        if i >= F0:
            ful.set_data([Ef], [-0.06 * top])
            eln.set_data([Ef, Ef], [0, top * 0.8])
            etx.set_text(f"E[X] = {_g(E)}")
        else:
            ful.set_data([], [])
            eln.set_data([], [])
            etx.set_text("")
        if i >= V0:
            sln.set_data([Ef - sd, Ef + sd], [-0.145 * top, -0.145 * top])
            stx.set_text(f"E[X] ± σ  (σ ≈ {sd:.3g})")
        else:
            sln.set_data([], [])
            stx.set_text("")
        if i >= S0:
            uu = ramp(i, S0, S1)
            k = max(1, min(plays, int(round(plays ** uu))))
            aln.set_data(ks[:k], avg[:k])
            adt.set_data([k], [avg[k - 1]])
        else:
            k = 0
            aln.set_data([], [])
            adt.set_data([], [])
        if i < T0:
            header.set_text(("Bir oyunun kazanç dağılımı: X = x değeri P(X = x) olasılıkla" if tr else
                             "A game's payoff distribution: X = x with probability P(X = x)"))
        elif i < F0:
            header.set_text("E[X] = Σ x·P(x) = " + " + ".join(term_s[:nterm]) + (" + …" if nterm < m else ""))
        elif i < S0:
            header.set_text((f"E[X] = {_nd(E)}: dağılımın denge (ağırlık) noktası" if tr else
                             f"E[X] = {_nd(E)}: the balance point of the distribution"))
        elif i < V0:
            header.set_text((f"{k} oyunun ortalama kazancı = {avg[k - 1]:.3f}   →   E[X] = {_g(E)}" if tr else
                             f"Average payoff of {k} plays = {avg[k - 1]:.3f}   →   E[X] = {_g(E)}"))
        else:
            header.set_text(f"Var(X) = E[X²] − (E[X])² = {_n(E2)} − ({_n(E)})² = {_nd(var)};   σ ≈ {sd:.3f}")
        return []

    return N, update


def vary(P, rnd):
    vals, probs = list(P["values"]), list(P["probs"])
    plays, seed = rnd.choice([1000, 2000, 3000]), rnd.randint(1, 9999)
    if len(vals) == 2 and len(probs) == 2:
        return {"values": [rnd.choice([2, 3, 4, 5, 6, 8]), -rnd.choice([1, 2])], "probs": probs,
                "plays": plays, "seed": seed}
    if len(vals) == 3 and len(probs) == 3 and float(Fraction(str(probs[0]))) < 0.05:
        c = rnd.choice([1, 2, 3, 5])
        p1, p2 = rnd.choice([0.005, 0.01, 0.02]), rnd.choice([0.03, 0.04, 0.05, 0.1])
        return {"values": [rnd.choice([50, 100, 200]) - c, rnd.choice([10, 20, 30]) - c, -c],
                "probs": [p1, p2, round(1 - p1 - p2, 3)], "plays": 3000, "seed": seed}
    p1 = rnd.choice([0.05, 0.1, 0.1, 0.2])
    p2 = rnd.choice([0.2, 0.25, 0.3, 0.4])
    return {"values": [rnd.choice([10, 15, 20, 25, 50]), rnd.choice([1, 2, 3, 5]), -rnd.choice([1, 2, 3, 4])],
            "probs": [p1, p2, round(1 - p1 - p2, 2)], "plays": plays, "seed": seed}
''',
}
EXAMPLES += [
    {"id": "prob-ev-1", "kind": "expected_value", "topics": ["game", "oyun", "kazanç"],
     "title": ("Bir şans oyununun beklenen kazancı", "Expected payoff of a game of chance"),
     "q": ("Bir oyunda kazanç X; değerler ve olasılıklar: {dist}. E[X], Var(X) ve σ nedir? Oyun oynanmaya "
           "değer mi?",
           "In a game the payoff X takes values (with probabilities) {dist}. Find E[X], Var(X) and σ. Is "
           "the game worth playing?"),
     "P": {"values": [10, 2, -1], "probs": [0.1, 0.3, 0.6], "plays": 1000, "seed": 3}},
    {"id": "prob-ev-2", "kind": "expected_value", "topics": ["dice game", "zar oyunu", "fair game"],
     "title": ("Zar oyunu adil mi?", "Is the dice game fair?"),
     "q": ("Bir zar atılıyor: 6 gelirse {w} TL kazanıyorsun, aksi halde {l} TL kaybediyorsun. Kazanç "
           "dağılımı: {dist}. Oyun adil mi? Varyansı bul.",
           "A die is rolled: you win {w} if it shows a 6, otherwise you lose {l}. Payoff distribution: "
           "{dist}. Is the game fair? Find the variance."),
     "P": {"values": [5, -1], "probs": ["1/6", "5/6"], "plays": 2000, "seed": 8}},
    {"id": "prob-ev-3", "kind": "expected_value", "topics": ["lottery", "piyango", "raffle"],
     "title": ("Piyango biletinin beklenen değeri", "Expected value of a lottery ticket"),
     "q": ("Bir piyango bileti {l} TL. Bilet başına net kazanç X'in dağılımı: {dist}. Beklenen net kazanç "
           "ve standart sapma nedir?",
           "A lottery ticket costs {l}. The net gain X per ticket has distribution {dist}. Find the expected "
           "net gain and the standard deviation."),
     "P": {"values": [98, 18, -2], "probs": [0.01, 0.04, 0.95], "plays": 3000, "seed": 5}},
]

# ──────────────────────────────────────────────────────────────────────────
TEMPLATES["poisson"] = {
    "course": "prob",
    "title": ("Poisson dağılımı", "Poisson distribution"),
    "topics": ["poisson", "poisson distribution", "poisson process", "rare events", "events per interval",
               "arrivals", "average rate", "poisson dağılımı", "nadir olaylar", "birim zamanda olay",
               "ortalama oran", "poisson süreci"],
    "code": r'''
import math
import numpy as np

_SYM = {"eq": "=", "le": "≤", "ge": "≥"}
_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _g(x, nd=4):
    s = f"{float(x):.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _setup(P):
    lam = min(30.0, max(0.1, float(P["lam"])))
    k = max(0, min(60, int(P["k"])))
    cmp = P.get("cmp", "eq")
    if cmp not in _SYM:
        cmp = "eq"
    M = max(20, min(2000, int(P.get("trials", 200))))
    return lam, k, cmp, M


def _pmf(lam, j):
    return math.exp(-lam) * lam ** j / math.factorial(j)


def _hit(j, k, cmp):
    return j == k if cmp == "eq" else (j <= k if cmp == "le" else j >= k)


def _prob(lam, k, cmp):
    if cmp == "eq":
        return _pmf(lam, k)
    if cmp == "le":
        return sum(_pmf(lam, j) for j in range(k + 1))
    return 1.0 - sum(_pmf(lam, j) for j in range(k))


def _sim(P, lam, M):
    rng = np.random.default_rng(int(P.get("seed", 0)))
    counts = rng.poisson(lam, M)
    times = [np.sort(rng.random(int(c))) for c in counts]
    return counts, times


def _sumtxt(lam, js):
    t = [_g(lam ** j / math.factorial(j), 4) for j in js]
    if len(t) > 5:
        t = t[:2] + ["…"] + t[-2:]
    return " + ".join(t)


def solve(P):
    lam, k, cmp, M = _setup(P)
    sym = _SYM[cmp]
    ls = _g(lam)
    e = math.exp(-lam)
    pr = _prob(lam, k, cmp)
    counts, _ = _sim(P, lam, M)
    obs = int(sum(1 for c in counts if _hit(int(c), k, cmp)))
    steps = [
        (f"X ~ Poisson(λ = {ls}): sabit bir aralıktaki olay sayısı;  E[X] = Var(X) = λ = {ls}",
         f"X ~ Poisson(λ = {ls}): number of events in a fixed interval;  E[X] = Var(X) = λ = {ls}"),
        ("Formül: P(X = k) = e^(−λ)·λᵏ / k!", "Formula: P(X = k) = e^(−λ)·λᵏ / k!"),
    ]
    if cmp == "eq":
        s = (f"P(X = {k}) = e^(−{ls})·{ls}{str(k).translate(_SUP)} / {k}! = {e:.6f}·{_g(lam ** k, 6)} / "
             f"{math.factorial(k)} ≈ {pr:.4f}")
        steps.append((s, s))
    elif cmp == "le":
        js = list(range(k + 1))
        S = sum(lam ** j / math.factorial(j) for j in js)
        s = (f"P(X ≤ {k}) = e^(−{ls})·Σ λʲ/j! (j = 0…{k}) = {e:.6f}·({_sumtxt(lam, js)}) = "
             f"{e:.6f}·{_g(S, 4)} ≈ {pr:.4f}")
        steps.append((s, s))
        vals = ", ".join(f"P({j}) ≈ {_pmf(lam, j):.4f}" for j in js[:6])
        steps.append((f"Tek tek: {vals}", f"Term by term: {vals}"))
    else:
        js = list(range(k))
        if k == 0:
            steps.append(("P(X ≥ 0) = 1 (her zaman)", "P(X ≥ 0) = 1 (always)"))
        else:
            c = sum(_pmf(lam, j) for j in js)
            s = (f"P(X ≥ {k}) = 1 − P(X ≤ {k - 1}) = 1 − e^(−{ls})·({_sumtxt(lam, js)}) = 1 − {c:.4f} "
                 f"≈ {pr:.4f}")
            steps.append(("Tümleyen: " + s, "Complement: " + s))
    steps.append((f"Simülasyon: {M} aralığın {obs} tanesinde X {sym} {k} ⇒ oran {obs / M:.3f};  "
                  f"ortalama olay sayısı {counts.mean():.3f} ≈ λ",
                  f"Simulation: X {sym} {k} in {obs} of {M} intervals ⇒ rate {obs / M:.3f};  "
                  f"mean count {counts.mean():.3f} ≈ λ"))
    words = ({"eq": f"tam {k}", "le": f"en çok {k}", "ge": f"en az {k}"}[cmp],
             {"eq": f"exactly {k}", "le": f"at most {k}", "ge": f"at least {k}"}[cmp])
    return {"answer": (f"P(X {sym} {k}) ≈ {pr:.4f}", f"P(X {sym} {k}) ≈ {pr:.4f}"),
            "steps": steps, "fmt": {"event": f"X {sym} {k}", "words": words}}


def build(fig, P):
    tr = P.get("lang", "tr") == "tr"
    lam, k, cmp, M = _setup(P)
    sym = _SYM[cmp]
    counts, times = _sim(P, lam, M)
    kq = 0
    acc = _pmf(lam, 0)
    while acc < 0.999 and kq < 80:
        kq += 1
        acc += _pmf(lam, kq)
    kmax = int(max(kq, counts.max(), k + 1))
    js = np.arange(kmax + 1)
    pm = np.array([_pmf(lam, int(j)) for j in js])
    hit = np.array([_hit(int(j), k, cmp) for j in js])
    pr = _prob(lam, k, cmp)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.9, 1], height_ratios=[1, 2.7], left=0.07, right=0.985,
                          top=0.92, bottom=0.1, wspace=0.08, hspace=0.45)
    tl = fig.add_subplot(gs[0, 0])
    ax = fig.add_subplot(gs[1, 0])
    tx = fig.add_subplot(gs[:, 1])
    tx.axis("off")
    tl.set_xlim(0, 1)
    tl.set_ylim(0, 1)
    tl.set_yticks([])
    tl.set_xticks([0, 0.25, 0.5, 0.75, 1])
    tl.set_xlabel("zaman (bir aralık)" if tr else "time (one interval)", fontsize=9, labelpad=1)
    arr, = tl.plot([], [], "|", color="#DC2626", ms=24, mew=2.5)
    scan, = tl.plot([], [], color="#2563EB", lw=2)
    tlab = tl.text(0, 1.08, "", transform=tl.transAxes, fontsize=10.5, fontweight="bold")
    bars = ax.bar(js, np.zeros(kmax + 1), width=0.78, color=["#DC2626" if h else "#2563EB" for h in hit],
                  alpha=0.85)
    expl, = ax.plot([], [], "o-", color="#E07B39", ms=4, lw=1.6,
                    label=("beklenen: m·P(X = j)" if tr else "expected: m·P(X = j)"))
    ax.bar([0], [0], color="#2563EB", label=("gözlenen aralık sayısı" if tr else "observed intervals"))
    ax.set_xlim(-0.7, kmax + 0.7)
    ax.set_ylim(0, 1)
    ax.set_xticks(js if kmax <= 16 else js[::2])
    ax.set_xlabel("aralıktaki olay sayısı j" if tr else "events in an interval j")
    ax.set_ylabel("aralık sayısı" if tr else "number of intervals")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    info = tx.text(0.03, 0.985, "", transform=tx.transAxes, va="top", fontsize=10.5,
                   bbox=dict(boxstyle="round", fc="white", ec="#D1D5DB"))
    lines = [tx.text(0.03, 0.8 - 0.083 * m, "", transform=tx.transAxes, va="top", fontsize=10.5)
             for m in range(9)]
    N, S0, SL = 165, 6, 13
    NS = min(4, M)
    F0 = S0 + NS * SL
    F1 = 128

    def state(i):
        if i < S0:
            return 0, -1, 0.0
        if i < F0:
            j = (i - S0) // SL
            u = min(1.0, ((i - S0) % SL) / (SL - 3))
            return j + (1 if u >= 1 else 0), j, u
        u = min(1.0, (i - F0) / (F1 - F0))
        m = NS + int(round((M - NS) * u ** 1.5))
        return m, m - 1, 1.0

    def update(i):
        m, cur, u = state(i)
        if cur >= 0:
            tt = times[cur]
            vis = tt[tt <= u]
            arr.set_data(vis, np.full(len(vis), 0.5))
            if i < F0 and u < 1:
                scan.set_data([u, u], [0, 1])
            else:
                scan.set_data([], [])
            tlab.set_text((f"{cur + 1}. aralık: X = {len(vis)} olay" if tr else
                           f"interval {cur + 1}: X = {len(vis)} events"))
        else:
            arr.set_data([], [])
            scan.set_data([], [])
            tlab.set_text("")
        c = np.bincount(counts[:m], minlength=kmax + 1)[:kmax + 1] if m else np.zeros(kmax + 1, dtype=int)
        for b, v in zip(bars, c):
            b.set_height(v)
        ax.set_ylim(0, max(c.max(), m * pm.max(), 1) * 1.4 + 1)
        if m:
            expl.set_data(js, m * pm)
        else:
            expl.set_data([], [])
        obs = int(c[hit].sum())
        txt = [(f"X ~ Poisson(λ = {_g(lam)})", "#111827"),
               ("P(X = j) = e^(−λ)·λʲ / j!", "#111827")]
        if i >= 20:
            txt.append((f"E[X] = Var(X) = λ = {_g(lam)}", "#7C3AED"))
        if m:
            txt.append(((f"aralık: {m} / {M}" if tr else f"intervals: {m} / {M}"), "#374151"))
            txt.append(((f"X {sym} {k} olan: {obs} ({obs / m:.3f})" if tr else
                         f"with X {sym} {k}: {obs} ({obs / m:.3f})"), "#2563EB"))
            txt.append(((f"örnek ortalaması: {counts[:m].mean():.3f}" if tr else
                         f"sample mean: {counts[:m].mean():.3f}"), "#374151"))
        if i >= F1:
            txt.append((f"P(X {sym} {k}) ≈ {pr:.4f}", "#DC2626"))
            if cmp == "eq":
                txt.append((f"= e^(−{_g(lam)})·{_g(lam)}{str(k).translate(_SUP)}/{k}!", "#DC2626"))
            elif cmp == "le":
                txt.append((f"= P(0) + … + P({k})", "#DC2626"))
            else:
                txt.append((f"= 1 − P(X ≤ {k - 1})" if k > 0 else "= 1", "#DC2626"))
        for mm, t in enumerate(lines):
            if mm < len(txt):
                t.set_text(txt[mm][0])
                t.set_color(txt[mm][1])
                t.set_fontweight("bold" if (i >= F1 and mm >= 6) else "normal")
                t.set_fontsize(13 if (i >= F1 and mm == 6) else 10.5)
            else:
                t.set_text("")
        if i < S0:
            info.set_text((f"Olaylar rastgele ve bağımsız gelir;\nbir aralıkta ortalama λ = {_g(lam)} olay" if tr else
                           f"Events arrive at random, independently;\non average λ = {_g(lam)} per interval"))
        elif i < F0:
            info.set_text(("Bir aralığı tara ve olayları say;\nsayı histograma eklenir" if tr else
                           "Scan one interval and count events;\nthe count goes into the histogram"))
        elif i < F1:
            info.set_text((f"{m} aralık: histogram Poisson\nolasılıklarına yaklaşıyor" if tr else
                           f"{m} intervals: the histogram approaches\nthe Poisson probabilities"))
        else:
            info.set_text((f"Kırmızı çubuklar: X {sym} {k}\nP ≈ {pr:.4f}, gözlenen {obs / m:.4f}" if tr else
                           f"Red bars: X {sym} {k}\nP ≈ {pr:.4f}, observed {obs / m:.4f}"))
        return []

    return N, update


def vary(P, rnd):
    lam = rnd.choice([1, 1.5, 2, 2.5, 3, 4, 5, 6])
    cmp = P.get("cmp", "eq")
    if cmp not in _SYM:
        cmp = "eq"
    base = int(round(lam))
    if cmp == "ge":
        k = rnd.randint(1, max(1, base + 1))
    else:
        k = max(0, base + rnd.randint(-2, 1))
    out = {"lam": lam, "k": k, "trials": rnd.choice([200, 300, 500]), "seed": rnd.randint(1, 9999)}
    if "cmp" in P:
        out["cmp"] = cmp
    return out
''',
}
EXAMPLES += [
    {"id": "prob-pois-1", "kind": "poisson", "topics": ["call center", "çağrı merkezi"],
     "title": ("Çağrı merkezine gelen aramalar", "Calls to a call centre"),
     "q": ("Bir çağrı merkezine dakikada ortalama λ = {lam} arama geliyor. Belirli bir dakikada {words} "
           "arama gelme olasılığı, P({event}), nedir?",
           "A call centre receives on average λ = {lam} calls per minute. What is the probability of "
           "{words} calls in a given minute, P({event})?"),
     "P": {"lam": 4, "k": 2, "cmp": "eq", "trials": 200, "seed": 6}},
    {"id": "prob-pois-2", "kind": "poisson", "topics": ["typos", "yazım hatası"],
     "title": ("Sayfa başına yazım hatası", "Typos per page"),
     "q": ("Bir kitapta sayfa başına ortalama {lam} yazım hatası var. Rastgele bir sayfada {words} hata "
           "olma olasılığı nedir?",
           "A book has on average {lam} typos per page. What is the probability that a random page has "
           "{words} typos?"),
     "P": {"lam": 1.5, "k": 1, "cmp": "le", "trials": 300, "seed": 4}},
    {"id": "prob-pois-3", "kind": "poisson", "topics": ["customers", "müşteri"],
     "title": ("Dükkâna gelen müşteriler", "Customers arriving at a shop"),
     "q": ("Bir dükkâna 10 dakikada ortalama {lam} müşteri geliyor. 10 dakikalık bir aralıkta {words} "
           "müşteri gelme olasılığı nedir?",
           "A shop gets on average {lam} customers per 10 minutes. What is the probability of {words} "
           "customer(s) in a 10-minute interval?"),
     "P": {"lam": 3, "k": 1, "cmp": "ge", "trials": 200, "seed": 9}},
]
