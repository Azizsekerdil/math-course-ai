# -*- coding: utf-8 -*-
"""Math Course AI — Python simülasyon motoru.

Her simülasyon TÜRÜ (kind) bir Python kaynak metnidir (template). Kaynak üç
fonksiyon tanımlar:

    solve(P)       -> {"answer": ..., "steps": [...], "fmt": {...}}
    build(fig, P)  -> (N, update)   # update(i), 0 <= i < N, kare i'yi çizer
    vary(P, rnd)   -> yeni P        # aynı soru tipi, farklı sayılar

Kaynaklar programın İÇİNE gömülüdür (simulations/templates_*.py); harici
Manim, FFmpeg, TeX veya video oynatıcı gerekmez — yalnızca programın zaten
zorunlu bağımlılıkları olan numpy + matplotlib (+ sympy) kullanılır.

Kullanıcı oynatıcıdaki kod düzenleyicisinde bir kaynağı değiştirip
çalıştırabilir; değiştirilmiş kaynak önce ai_code_guard.analyze() izin
politikasından geçmek ZORUNDADIR (dosya/ağ/süreç erişimi reddedilir).
"""

from __future__ import annotations

import ast
import builtins
import json
import pprint
import random
import re
from fractions import Fraction
from pathlib import Path

from . import (templates_fund, templates_alg, templates_alg2, templates_geo,
               templates_linalg, templates_calc, templates_calc2, templates_calc3,
               templates_diffeq, templates_prob, templates_stats)

_TEMPLATE_MODULES = (templates_fund, templates_alg, templates_alg2, templates_geo,
                     templates_linalg, templates_calc, templates_calc2, templates_calc3,
                     templates_diffeq, templates_prob, templates_stats)

#: Kurs anahtarları ve ekranda görünen adları (marka içermeyen genel ders adları).
COURSES = {
    "fund":   ("Temel Matematik", "Fundamentals of Math"),
    "alg":    ("Cebir", "Algebra"),
    "geo":    ("Geometri", "Geometry"),
    "linalg": ("Lineer Cebir", "Linear Algebra"),
    "calc1":  ("Kalkülüs 1", "Calculus 1"),
    "calc2":  ("Kalkülüs 2", "Calculus 2"),
    "calc3":  ("Kalkülüs 3", "Calculus 3"),
    "diffeq": ("Diferansiyel Denklemler", "Differential Equations"),
    "prob":   ("Olasılık ve İstatistik", "Probability & Statistics"),
}

MIN_FRAMES, MAX_FRAMES = 2, 400


def pick(value, lang="tr"):
    """(tr, en) çiftinden dile uygun olanı seçer; düz metni aynen döndürür."""
    if isinstance(value, (tuple, list)) and len(value) == 2 and all(
            isinstance(v, str) for v in value):
        return value[1] if lang == "en" and value[1] else value[0]
    return "" if value is None else str(value)


def fmt_num(v):
    """Soru metni için sayı biçimi: 3.0 -> '3', 0.5 -> '0.5', Fraction -> 'a/b'."""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, Fraction):
        return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15:
            return str(int(v))
        return f"{v:.4g}"
    return str(v)


_SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def pretty_expr(s):
    """'3*x**2 - x**(-1) + sqrt(x)' -> '3x² − x⁻¹ + √(x)' (yalnızca görüntü için)."""
    s = str(s)
    s = re.sub(r"\*\*\(?(-?\d+)\)?", lambda m: m.group(1).translate(_SUP), s)
    s = s.replace("**", "^")
    s = re.sub(r"(\d)\*(?=[A-Za-z(])", r"\1", s)
    s = s.replace("*", "·").replace("sqrt", "√").replace("^", "^")
    s = re.sub(r"(?<=\s)-(?=\s)", "−", s)
    return s


class _SafeFormat(dict):
    def __missing__(self, key):
        return "{" + key + "}"


# ══════════════════════════════════════════════════════════════════════════
# Template registry
# ══════════════════════════════════════════════════════════════════════════
_TEMPLATES = None
_EXAMPLES = None
_COMPILED = {}


def all_templates():
    """kind -> {"course", "topics", "title", "code"}"""
    global _TEMPLATES
    if _TEMPLATES is None:
        merged = {}
        for mod in _TEMPLATE_MODULES:
            for kind, tpl in getattr(mod, "TEMPLATES", {}).items():
                if kind in merged:
                    raise ValueError(f"duplicate simulation kind: {kind}")
                merged[kind] = tpl
        _TEMPLATES = merged
    return _TEMPLATES


def all_examples():
    """Programa gömülü örnek soruların tamamı (kurs sırasıyla)."""
    global _EXAMPLES
    if _EXAMPLES is None:
        tpls = all_templates()
        out, seen = [], set()
        for mod in _TEMPLATE_MODULES:
            for ex in getattr(mod, "EXAMPLES", []):
                if ex["id"] in seen:
                    raise ValueError(f"duplicate example id: {ex['id']}")
                if ex["kind"] not in tpls:
                    raise ValueError(f"example {ex['id']} uses unknown kind {ex['kind']}")
                seen.add(ex["id"])
                e = dict(ex)
                e.setdefault("course", tpls[ex["kind"]]["course"])
                out.append(e)
        order = list(COURSES)
        out.sort(key=lambda e: order.index(e["course"]) if e["course"] in order else 99)
        _EXAMPLES = out
    return _EXAMPLES


def example_by_id(eid):
    for e in all_examples():
        if e["id"] == eid:
            return e
    return None


def load_source(code, name="<simulation>"):
    """Compile + exec a template source and return its namespace."""
    ns = {"__builtins__": builtins, "__name__": "mca_simulation"}
    exec(compile(code, name, "exec"), ns)  # noqa: S102 — gömülü / politika denetimli kaynak
    for fn in ("solve", "build", "vary"):
        if not callable(ns.get(fn)):
            raise ValueError(f"simülasyon kaynağında '{fn}' fonksiyonu yok")
    return ns


def compiled_template(kind):
    ns = _COMPILED.get(kind)
    if ns is None:
        ns = _COMPILED[kind] = load_source(all_templates()[kind]["code"], f"<sim:{kind}>")
    return ns


def check_source_policy(code):
    """Düzenlenmiş kaynak için izin politikası. (ok, [mesaj, ...])"""
    try:
        import ai_code_guard
    except Exception as e:  # pragma: no cover - modül her zaman pakette
        return False, [f"ai_code_guard yüklenemedi: {e}"]
    res = ai_code_guard.analyze(code)
    if res.ok:
        return True, []
    return False, [f"satır {v.line}: {v.message}" for v in res.violations][:12]


# ══════════════════════════════════════════════════════════════════════════
# A runnable simulation = one example + its parameters + the code that runs it
# ══════════════════════════════════════════════════════════════════════════
class Simulation:
    def __init__(self, example, lang="tr", params=None, code=None, namespace=None):
        self.example = dict(example)
        self.kind = example["kind"]
        self.lang = lang if lang in ("tr", "en") else "tr"
        tpl = all_templates().get(self.kind, {})
        self.template = tpl
        self.code = code if code is not None else tpl.get("code", "")
        self.custom_code = code is not None
        self._ns = namespace if namespace is not None else (
            load_source(self.code) if self.custom_code else compiled_template(self.kind))
        self.params = dict(params if params is not None else example.get("P", {}))
        self._solution = None

    # ---- data ------------------------------------------------------------
    def _P(self):
        p = dict(self.params)
        p["lang"] = self.lang
        return p

    @property
    def id(self):
        return self.example.get("id", "")

    @property
    def course(self):
        return self.example.get("course", self.template.get("course", ""))

    def title(self):
        return pick(self.example.get("title") or self.template.get("title"), self.lang)

    def solution(self):
        if self._solution is None:
            raw = self._ns["solve"](self._P()) or {}
            steps = [pick(s, self.lang) for s in raw.get("steps", [])]
            self._solution = {
                "answer": pick(raw.get("answer", ""), self.lang),
                "steps": steps,
                "fmt": dict(raw.get("fmt", {}) or {}),
            }
        return self._solution

    def format_map(self):
        fm = _SafeFormat()
        for k, v in self.params.items():
            if isinstance(v, (int, float, Fraction)) and not isinstance(v, bool):
                fm[k] = fmt_num(v)
                fm["s_" + k] = ("+ " if v >= 0 else "- ") + fmt_num(abs(v))
            elif isinstance(v, (list, tuple)):
                fm[k] = ", ".join(fmt_num(x) for x in v)
            else:
                fm[k] = str(v)
                fm["pretty_" + k] = pretty_expr(str(v))
        for k, v in self.solution()["fmt"].items():
            fm[k] = pick(v, self.lang) if isinstance(v, (tuple, list)) else (
                fmt_num(v) if isinstance(v, (int, float, Fraction)) else str(v))
        return fm

    def question(self):
        q = pick(self.example.get("q", ""), self.lang)
        try:
            return q.format_map(self.format_map())
        except Exception:
            return q

    def source_note(self):
        src = self.example.get("source")
        if not src:
            return ""
        page = src.get("page")
        name = Path(str(src.get("file", ""))).name
        tail = (f" — s.{page}" if self.lang == "tr" else f" — p.{page}") if page else ""
        return (f"Kaynaktaki örnekten üretildi: {name}{tail}" if self.lang == "tr"
                else f"Generated from a source example: {name}{tail}")

    # ---- running ---------------------------------------------------------
    def build(self, fig):
        n, update = self._ns["build"](fig, self._P())
        n = int(max(MIN_FRAMES, min(MAX_FRAMES, n)))
        return n, update

    def varied(self, seed=None):
        rnd = random.Random(seed)
        newp = self._ns["vary"](dict(self.params), rnd) or dict(self.params)
        newp.pop("lang", None)
        sim = Simulation(self.example, self.lang, newp,
                         code=self.code if self.custom_code else None,
                         namespace=self._ns)
        sim.custom_code = self.custom_code
        return sim

    def with_lang(self, lang):
        sim = Simulation(self.example, lang, self.params,
                         code=self.code if self.custom_code else None, namespace=self._ns)
        sim.custom_code = self.custom_code
        return sim

    # ---- source views ----------------------------------------------------
    def editor_source(self):
        """Düzenleyicide gösterilen ve AYNEN çalıştırılan kaynak."""
        head = ("# Math Course AI — Python simülasyonu\n"
                f"# {self.title()}\n"
                "# P sözlüğündeki sayıları değiştirip 'Kodu Çalıştır' ile yeniden oynatabilirsiniz.\n")
        params = "P = " + pprint.pformat(self.params, sort_dicts=False, width=88) + "\n\n"
        return head + params + self.code.strip() + "\n"

    def standalone_script(self):
        """Program dışında `python dosya.py` ile çalışan bağımsız betik."""
        q = self.question().replace("\n", " ")
        ans = self.solution()["answer"].replace("\n", " ")
        return (
            "# -*- coding: utf-8 -*-\n"
            f"# Math Course AI — {self.title()}\n"
            f"# Soru / Question: {q}\n"
            f"# Cevap / Answer: {ans}\n"
            "# Gereken: numpy, matplotlib (ve gerekiyorsa sympy).\n\n"
            + "P = " + pprint.pformat(self.params, sort_dicts=False, width=88) + "\n"
            + f"P['lang'] = {self.lang!r}\n\n"
            + self.code.strip() + "\n\n\n"
            "if __name__ == '__main__':\n"
            "    import matplotlib.pyplot as plt\n"
            "    from matplotlib.animation import FuncAnimation\n"
            "    sol = solve(P)\n"
            "    for s in sol.get('steps', []):\n"
            "        print(s if isinstance(s, str) else s[0 if P['lang'] == 'tr' else 1])\n"
            "    fig = plt.figure(figsize=(9, 6))\n"
            "    N, update = build(fig, P)\n"
            "    anim = FuncAnimation(fig, update, frames=N, interval=40, repeat=False)\n"
            "    plt.show()\n"
        )

    @classmethod
    def from_editor_source(cls, text, base):
        """Düzenleyicideki kaynaktan yeni simülasyon. Politika ihlali -> ValueError."""
        ok, problems = check_source_policy(text)
        if not ok:
            raise ValueError("\n".join(problems))
        ns = load_source(text, "<düzenlenmiş simülasyon>")
        params = ns.get("P")
        if not isinstance(params, dict):
            raise ValueError("Kaynakta 'P = {...}' parametre sözlüğü bulunamadı.")
        params = {k: v for k, v in params.items() if k != "lang"}
        # P atamasını ve başlık yorumlarını ayıkla: kalan kısım "kod"dur ve
        # editor_source() onu yeni P ile yeniden birleştirir.
        lines = text.splitlines()
        drop = set()
        for node in ast.parse(text).body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "P"):
                drop.update(range(node.lineno - 1, node.end_lineno))
        kept = [l for i, l in enumerate(lines) if i not in drop
                and not l.startswith(("# Math Course AI —", "# P sözlüğündeki"))]
        if kept and kept[0].startswith("# ") and kept[0][2:].strip() == base.title():
            kept = kept[1:]
        code = "\n".join(kept).strip() + "\n"
        return cls(base.example, base.lang, params, code=code, namespace=ns)


# ══════════════════════════════════════════════════════════════════════════
# Offscreen rendering (GIF/PNG export + headless tests)
# ══════════════════════════════════════════════════════════════════════════
def new_figure(size=(8.0, 5.4), dpi=100):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig = Figure(figsize=size, dpi=dpi, facecolor="white")
    FigureCanvasAgg(fig)
    return fig


def render_frames(sim, frames=None, size=(8.0, 5.4), dpi=80):
    """Render the given frame indices (default: every frame) to PIL images."""
    from PIL import Image
    fig = new_figure(size, dpi)
    n, update = sim.build(fig)
    idx = range(n) if frames is None else [i for i in frames if 0 <= i < n]
    images = []
    for i in idx:
        update(i)
        fig.canvas.draw()
        buf = fig.canvas.buffer_rgba()
        images.append(Image.frombuffer("RGBA", fig.canvas.get_width_height(), buf).convert("RGB"))
    return n, images


def export_gif(sim, path, fps=20, max_frames=160):
    n_total = sim.build(new_figure())[0]
    step = max(1, n_total // max_frames)
    _, imgs = render_frames(sim, range(0, n_total, step))
    imgs += [imgs[-1]] * 15  # son karede kısa bekleme
    imgs[0].save(str(path), save_all=True, append_images=imgs[1:],
                 duration=int(1000 / fps), loop=0, optimize=True)
    return path


# ══════════════════════════════════════════════════════════════════════════
# Course / topic matching (tree path -> relevant simulations)
# ══════════════════════════════════════════════════════════════════════════
_COURSE_RULES = [
    ("linalg", (r"linear\s*algebra", r"lineer\s*cebir", r"do[gğ]rusal\s*cebir", r"matri")),
    ("diffeq", (r"differential", r"diferansiyel", r"\bode\b")),
    ("prob",   (r"probab", r"statist", r"olas[ıi]l[ıi]k", r"istatisti")),
    ("calc3",  (r"calc\w*\s*(3|iii)\b", r"multivar", r"kalk[üu]l[üu]s\s*(3|iii)\b")),
    ("calc2",  (r"calc\w*\s*(2|ii)\b", r"kalk[üu]l[üu]s\s*(2|ii)\b")),
    ("calc1",  (r"calc\w*\s*(1|i)\b", r"calculus", r"kalk[üu]l[üu]s", r"\bt[üu]rev")),
    ("geo",    (r"geometr", r"trigonometr")),
    ("alg",    (r"algebra", r"cebir", r"precalc")),
    ("fund",   (r"fundamental", r"arithmetic", r"aritmeti", r"\btemel\b", r"basic\s*math",
                r"pre-?algebra")),
]


def _lower(text):
    """Türkçe güvenli küçük harf: 'İ'.lower() Python'da 'i̇' (i + birleşik nokta) olur."""
    return (text or "").replace("İ", "i").lower().replace("\u0307", "")


#: İngiliz/Amerikan yazım farkları — konu adı ile anahtar kelime aynı biçime gelsin.
_SPELLING = [(r"\bdiscs?\b", "disk"), (r"\bcentre\b", "center"), (r"\bmodelling\b", "modeling")]


def _norm(text):
    t = _lower(text)
    for pat, rep in _SPELLING:
        t = re.sub(pat, rep, t)
    return t


def course_key_from_name(name):
    n = _lower(name)
    for key, pats in _COURSE_RULES:
        if any(re.search(p, n) for p in pats):
            return key
    return ""


def _words(text):
    text = re.sub(r"\.(pdf|png|jpe?g|txt|docx?|pptx?)$", "", _norm(text))
    text = re.sub(r"^\s*\d+[\s.\-_]*", "", text)
    return re.sub(r"[_\-]+", " ", text)


def _topic_score(keywords, topic_text):
    """En uzun (en özgül) eşleşen anahtar kelime belirleyicidir; eşleşme sayısı
    yalnızca eşitliği bozar. Böylece 'systems of linear equations' adı, genel
    'linear equation' yerine 'systems of linear equations' anahtarına gider."""
    best, hits = 0, 0
    for kw in set(_norm(k).strip() for k in keywords):
        if kw and re.search(r"(?<![a-zçğıöşü])" + re.escape(kw), topic_text):
            best = max(best, len(kw))
            hits += 1
    return 0 if not best else 10 * (4 + best) + min(hits, 9)


def match_examples(parts, course_key="", limit=None):
    """Bir ağaç düğümü için ilgili gömülü örnekleri puanlayarak döndürür.

    parts: düğümün yolu (kurs klasöründen dosyaya kadar ad listesi). Son ad
    (konu/dosya adı) en yüksek ağırlığı alır. Hiç konu eşleşmezse kursun
    tüm örnekleri döner — '01 Formula Sheet' gibi genel klasörler için.
    Dönen: (örnekler, eşleşme_var_mı)
    """
    tpls = all_templates()
    parts = [p for p in (parts or []) if p]
    leaf = _words(parts[-1]) if parts else ""
    parents = " ".join(_words(p) for p in parts[:-1])
    scored = []
    for ex in all_examples():
        kws = list(tpls[ex["kind"]].get("topics", ())) + list(ex.get("topics", ()))
        s = 3 * _topic_score(kws, leaf) + _topic_score(kws, parents)
        if course_key and ex["course"] == course_key:
            s += 1 if s else 0
        if s > 1:
            scored.append((s, ex))
    if course_key:
        same = [(s, e) for s, e in scored if e["course"] == course_key]
        if same:
            scored = same
    scored.sort(key=lambda t: -t[0])
    found = [e for _, e in scored]
    if found:
        return (found[:limit] if limit else found), True
    pool = [e for e in all_examples() if not course_key or e["course"] == course_key]
    return (pool[:limit] if limit else pool), False


def examples_for_course(course_key):
    return [e for e in all_examples() if e["course"] == course_key]


def stats():
    ex = all_examples()
    per = {}
    for e in ex:
        per[e["course"]] = per.get(e["course"], 0) + 1
    return {"kinds": len(all_templates()), "examples": len(ex), "per_course": per}


def dump_catalog_json(path):
    rows = [{"id": e["id"], "course": e["course"], "kind": e["kind"],
             "title": pick(e.get("title"), "en")} for e in all_examples()]
    Path(path).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
