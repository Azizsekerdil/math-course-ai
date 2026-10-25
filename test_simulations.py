# -*- coding: utf-8 -*-
"""Simülasyon motoru test paketi (headless).

Her gömülü simülasyon türü için:
  * kaynak ai_code_guard izin politikasından geçer, pyplot kullanmaz;
  * solve() iki dilde cevap + adım üretir, soru metninde boş yer tutucu kalmaz;
  * build() her kareyi hatasız çizer ve kareye ATLAMA (seek) güvenlidir;
  * vary() geçerli yeni sayılar üretir; düzenleyici kaynağı geri okunabilir;
  * bağımsız .py betiği derlenir.
Ayrıca ders/konu eşleştirme ve PDF örnek tarayıcısının sınıflandırması sınanır.

    python test_simulations.py                     # hepsi
    python test_simulations.py --module templates_geo
    python test_simulations.py --kind quadratic --full
"""

import io
import os
import sys
import tempfile
import time

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MATH_COURSE_AI_SETTINGS", tempfile.mkdtemp(prefix="mcai-sim-s-"))
os.environ.setdefault("MATH_COURSE_AI_EXPORTS", tempfile.mkdtemp(prefix="mcai-sim-e-"))
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ast
import pprint

import numpy as np

from simulations import engine

PASSED = 0
FAILED = 0
FAILS = []


def check(cond, label):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"   [PASS] {label}")
    else:
        FAILED += 1
        FAILS.append(label)
        print(f"   [FAIL] {label}")


def _arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        return sys.argv[i + 1] if i + 1 < len(sys.argv) else default
    return default


ONLY_MODULE = _arg("--module")
ONLY_KIND = _arg("--kind")
FULL = "--full" in sys.argv


def _selected_kinds():
    kinds = []
    for mod in engine._TEMPLATE_MODULES:
        name = mod.__name__.rsplit(".", 1)[-1]
        if ONLY_MODULE and name != ONLY_MODULE:
            continue
        for k in getattr(mod, "TEMPLATES", {}):
            if not ONLY_KIND or k == ONLY_KIND:
                kinds.append(k)
    return kinds


def _img_diff(a, b):
    x = np.asarray(a, dtype=np.int16)
    y = np.asarray(b, dtype=np.int16)
    if x.shape != y.shape:
        return 999.0
    return float(np.abs(x - y).mean())


def _safe(label, fn):
    try:
        return True, fn()
    except Exception as e:  # noqa: BLE001 - test raporu
        import traceback
        traceback.print_exc()
        check(False, f"{label}: {type(e).__name__}: {e}")
        return False, None


def test_registry():
    print("== Kayıt defteri ==")
    ok, tpls = _safe("şablonlar yüklenir", engine.all_templates)
    if not ok:
        return
    ok, exs = _safe("örnekler yüklenir", engine.all_examples)
    if not ok:
        return
    check(len(tpls) > 0, f"{len(tpls)} simülasyon türü kayıtlı")
    used = {e["kind"] for e in exs}
    for kind in _selected_kinds():
        check(kind in used, f"{kind}: en az bir gömülü örnek soru var")


def test_kind(kind):
    tpl = engine.all_templates()[kind]
    print(f"== {kind} ==")
    check(tpl.get("course") in engine.COURSES, f"{kind}: geçerli kurs anahtarı ({tpl.get('course')})")
    t = tpl.get("title")
    check(isinstance(t, tuple) and len(t) == 2 and all(t), f"{kind}: TR/EN başlık")
    check(len(tpl.get("topics", [])) >= 3, f"{kind}: en az 3 konu anahtar kelimesi")
    code = tpl.get("code", "")
    check("pyplot" not in code and "plt." not in code, f"{kind}: pyplot kullanmaz (Tk içine gömülür)")
    ok, problems = engine.check_source_policy(code)
    check(ok, f"{kind}: kaynak ai_code_guard politikasından geçer {problems[:3]}")
    ok, _ = _safe(f"{kind}: kaynak derlenir", lambda: engine.compiled_template(kind))
    if not ok:
        return
    for ex in [e for e in engine.all_examples() if e["kind"] == kind]:
        test_example(ex)


def test_example(ex):
    eid = ex["id"]
    q = ex.get("q")
    check(isinstance(q, tuple) and len(q) == 2 and all(q), f"{eid}: TR/EN soru metni")
    check(isinstance(ex.get("P"), dict), f"{eid}: P sözlüğü")
    for lang in ("tr", "en"):
        ok, sim = _safe(f"{eid}/{lang}: Simulation kurulur", lambda: engine.Simulation(ex, lang))
        if not ok:
            return
        ok, sol = _safe(f"{eid}/{lang}: solve()", sim.solution)
        if not ok:
            return
        check(bool(sol["answer"].strip()), f"{eid}/{lang}: cevap boş değil")
        check(len(sol["steps"]) >= 2, f"{eid}/{lang}: en az 2 çözüm adımı")
        qq = sim.question()
        check("{" not in qq and "}" not in qq, f"{eid}/{lang}: soruda doldurulmamış yer tutucu yok ({qq[:70]})")
    sim = engine.Simulation(ex, "tr")
    t0 = time.time()
    n = sim.build(engine.new_figure())[0]
    stride = 1 if FULL else 3
    seq = sorted(set(range(0, n, stride)) | {n - 1})
    ok, res = _safe(f"{eid}: kareler sırayla çizilir",
                    lambda: engine.render_frames(sim, seq, size=(6.4, 4.3), dpi=40))
    if not ok:
        return
    _, imgs = res
    by_idx = dict(zip(seq, imgs))
    check(engine.MIN_FRAMES <= n <= engine.MAX_FRAMES and len(imgs) == len(seq),
          f"{eid}: {n} kare ({time.time() - t0:.1f} sn)")
    # seek safety: jump around on a fresh figure, compare with sequential frames
    probe = [n - 1, 0, seq[len(seq) // 2], seq[len(seq) // 3]]
    ok, res2 = _safe(f"{eid}: karelere atlama", lambda: engine.render_frames(
        sim, probe, size=(6.4, 4.3), dpi=40))
    if ok:
        _, jimgs = res2
        diffs = [_img_diff(jimgs[k], by_idx[probe[k]]) for k in (1, 2, 3)]
        check(max(diffs) < 1.5, f"{eid}: kareye atlama güvenli (fark {max(diffs):.2f})")
    # english frame renders too
    _safe(f"{eid}: EN son kare", lambda: engine.render_frames(sim.with_lang("en"), [n - 1], dpi=30))
    # variations
    for seed in (1, 2, 3):
        ok, v = _safe(f"{eid}: vary(seed={seed})", lambda: sim.varied(seed))
        if not ok:
            continue
        lit_ok = True
        try:
            lit_ok = ast.literal_eval(pprint.pformat(v.params)) == v.params
        except Exception:
            lit_ok = False
        check(lit_ok, f"{eid}: vary {seed} parametreleri düz Python sabiti ({v.params})")
        ok, s2 = _safe(f"{eid}: vary {seed} solve", v.solution)
        if ok:
            check(bool(s2["answer"].strip()), f"{eid}: vary {seed} cevap var")
            check("{" not in v.question(), f"{eid}: vary {seed} soru dolu")
        nv = v.build(engine.new_figure())[0]
        _safe(f"{eid}: vary {seed} kareler", lambda: engine.render_frames(
            v, [0, nv // 2, nv - 1], size=(6.4, 4.3), dpi=30))
    # editor round trip + standalone script
    src = sim.editor_source()
    ok, back = _safe(f"{eid}: düzenleyici kaynağı geri okunur",
                     lambda: engine.Simulation.from_editor_source(src, sim))
    if ok:
        check(back.params == sim.params, f"{eid}: düzenleyici P değerlerini korur")
        check(back.editor_source() == src, f"{eid}: düzenleyici kaynağı kararlı")
    _safe(f"{eid}: bağımsız betik derlenir", lambda: compile(sim.standalone_script(), eid, "exec"))


def test_editor_policy():
    print("== Düzenlenmiş kod politikası ==")
    ex = engine.all_examples()[0]
    sim = engine.Simulation(ex, "tr")
    bad = sim.editor_source() + "\nimport os\nos.remove('x')\n"
    try:
        engine.Simulation.from_editor_source(bad, sim)
        check(False, "dosya sistemi erişen kod reddedilir")
    except ValueError as e:
        check("os" in str(e), "dosya sistemi erişen kod reddedilir")
    bad2 = sim.editor_source() + "\nopen('x', 'w')\n"
    try:
        engine.Simulation.from_editor_source(bad2, sim)
        check(False, "open() reddedilir")
    except ValueError:
        check(True, "open() reddedilir")


COURSE_NAMES = [
    ("Fundamentals of Math Course", "fund"), ("Algebra Course", "alg"),
    ("Geometry Course", "geo"), ("Linear Algebra Course", "linalg"),
    ("Calculus 1 Course", "calc1"), ("Calculus 2 Course", "calc2"),
    ("Calculus 3 Course", "calc3"), ("Differential Equations Course", "diffeq"),
    ("Probability & Statistics Course", "prob"), ("Lineer Cebir", "linalg"),
    ("Kalkülüs 2", "calc2"), ("Olasılık", "prob"), ("Random Folder", ""),
]

# (course name, path parts below the course folder, kinds that must lead the list)
TOPIC_CASES = [
    ("Algebra Course", ["01 Algebra 1", "02 Notes", "05 Functions and graphing", "02 Slope.pdf"],
     {"line_slope_point", "line_two_points", "parallel_perp"}),
    ("Algebra Course", ["01 Algebra 1", "02 Notes", "08 Quadratics", "03 Quadratic formula.pdf"],
     {"quadratic"}),
    ("Algebra Course", ["01 Algebra 1", "02 Notes", "06 Systems of equations"], {"system_2x2"}),
    ("Calculus 1 Course", ["02 Notes", "03 Derivatives", "01 Definition of the derivative.pdf"],
     {"derivative_expr"}),
    ("Calculus 1 Course", ["02 Notes", "02 Limits", "04 Limits at infinity.pdf"], {"limit_expr"}),
    ("Calculus 2 Course", ["02 Notes", "05 Applications of integrals", "02 Disc method.pdf"],
     {"volume_revolution"}),
    ("Calculus 2 Course", ["02 Notes", "09 Taylor series.pdf"], {"taylor_series"}),
    ("Calculus 3 Course", ["02 Notes", "04 Partial derivatives.pdf"], {"partial_derivatives"}),
    ("Calculus 3 Course", ["02 Notes", "06 Double integrals.pdf"], {"double_integral"}),
    ("Linear Algebra Course", ["02 Notes", "07 Eigenvalues and eigenvectors.pdf"], {"eigen"}),
    ("Linear Algebra Course", ["02 Notes", "02 Gauss-Jordan elimination.pdf"], {"gaussian_elim"}),
    ("Differential Equations Course", ["02 Notes", "01 First order", "03 Separable equations.pdf"],
     {"slope_field_expr", "exp_growth_decay"}),
    ("Differential Equations Course", ["02 Notes", "Euler's method.pdf"], {"euler_method"}),
    ("Geometry Course", ["02 Notes", "08 Right triangles", "01 Pythagorean theorem.pdf"],
     {"pythagorean"}),
    ("Geometry Course", ["02 Notes", "10 Circles", "Area and circumference.pdf"],
     {"circle_area", "arc_sector"}),
    ("Probability & Statistics Course", ["02 Notes", "Normal distribution.pdf"], {"normal_area"}),
    ("Probability & Statistics Course", ["02 Notes", "Binomial distribution.pdf"], {"binomial", "galton_board"}),
    ("Fundamentals of Math Course", ["02 Notes", "02 Fractions", "03 Adding fractions.pdf"],
     {"fraction_add"}),
    ("Fundamentals of Math Course", ["02 Notes", "Order of operations.pdf"], {"order_ops"}),
]


def test_course_and_topic_matching():
    print("== Kurs ve konu eşleştirme ==")
    for name, key in COURSE_NAMES:
        check(engine.course_key_from_name(name) == key, f"kurs adı '{name}' -> '{key}'")
    kinds = engine.all_templates()
    for course, parts, want in TOPIC_CASES:
        if not (want & set(kinds)):
            continue                       # o türler henüz bu dalda yoksa atla
        exs, matched = engine.match_examples(parts, engine.course_key_from_name(course))
        top = [e["kind"] for e in exs[:3]]
        check(matched and bool(want & set(top)), f"'{parts[-1]}' -> {sorted(want)} (ilk 3: {top})")
    exs, matched = engine.match_examples(["01 Formula Sheet"], "alg")
    check(not matched and exs and all(e["course"] == "alg" for e in exs),
          "konu adı olmayan klasör (Formula Sheet) kursun tüm örneklerini gösterir")
    per = engine.stats()["per_course"]
    for key in engine.COURSES:
        if per.get(key):
            check(per[key] >= 6, f"kurs '{key}' için en az 6 gömülü örnek ({per[key]})")


SCAN_TEXT = """Practice set
Example 1. Find the equation of the line with slope 3/4 that passes through (2, -1).
Example 2. Find the slope of the line through the points (1, 2) and (5, 10).
Example 3. Solve the system 2x + y = 7 and x - y = 2.
Example 4. Solve 2x2 - 3x - 5 = 0 using the quadratic formula.
Example 5. Find the derivative of f(x) = 3x3 - 5x + 2 at x = 1.
Example 6. Evaluate lim x->2 (x^2 - 4)/(x - 2).
Example 7. Evaluate the integral of f(x) = x^2 + 1 from 0 to 3.
Example 8. Sketch the slope field for dy/dx = x - y with y(0) = 1.
Example 9. A right triangle has legs 6 and 8. Find the hypotenuse.
Example 10. Simplify 3 + 4*(6 - 2)^2 / 8 using the order of operations.
Example 11. Two dice are rolled. What is the probability that the sum is 7?
Example 12. A circle has radius 7. Find its area.
"""


def test_scanner():
    print("== Kaynak tarayıcı ==")
    from simulations import scanner
    for raw in ("__import__('os').system('x')", "x**2; import os", "open('f')", "x.__class__",
                "lambda: 1", "exec(x)", "x" * 200):
        check(scanner.to_sympy_string(raw) is None, f"zararlı/uygunsuz ifade reddedilir: {raw[:30]}")
    check(scanner.to_sympy_string("3x2 - 5x + 2") == "3*x**2 - 5*x + 2", "düzleşmiş üs (3x2) okunur")
    check(scanner.to_sympy_string("2 sin x + x^3") is not None, "örtük çarpma / fonksiyon okunur")
    d = tempfile.mkdtemp(prefix="mcai-scan-")
    topic = os.path.join(d, "Algebra Course", "02 Notes")
    os.makedirs(topic)
    with open(os.path.join(topic, "Examples.txt"), "w", encoding="utf-8") as fh:
        fh.write(SCAN_TEXT)
    res = scanner.scan(topic, "alg", change=False)
    got = {e["kind"] for e in res["examples"]}
    want = {"line_slope_point", "line_two_points", "system_2x2", "quadratic", "derivative_expr",
            "limit_expr", "integral_expr", "slope_field_expr", "pythagorean", "order_ops",
            "dice_sum", "circle_area"} & set(engine.all_templates())
    check(want <= got, f"metindeki örnek türleri bulundu (eksik: {sorted(want - got)})")
    exact = {e["kind"]: e["P"] for e in res["examples"]}
    if "quadratic" in exact:
        check(exact["quadratic"] == {"a": 2, "b": -3, "c": -5}, f"katsayılar doğru okunur {exact['quadratic']}")
    if "system_2x2" in exact:
        s = engine.Simulation(next(e for e in res["examples"] if e["kind"] == "system_2x2"), "en")
        check(s.solution()["answer"] == "x = 3, y = 1", "taranan sistem doğru çözülür")
    import json as _json
    blob = _json.dumps(res["examples"], ensure_ascii=False)
    check("Find the equation of the line" not in blob and "Practice set" not in blob,
          "taranan örneklerde kitap cümlesi SAKLANMAZ")
    for e in res["examples"]:
        sim = engine.Simulation(e, "tr")
        ok, _ = _safe(f"taranan {e['kind']} çalışır", lambda: engine.render_frames(sim, [0, 1], dpi=30))
        check("{" not in sim.question(), f"taranan {e['kind']} sorusu dolu: {sim.question()[:60]}")
        check(bool(sim.source_note()), f"taranan {e['kind']} kaynak referansı taşır")
    res2 = scanner.scan(topic, "alg", change=True)
    changed = sum(1 for a, b in zip(res["examples"], res2["examples"]) if a["P"] != b["P"])
    check(changed >= max(1, len(res2["examples"]) // 2),
          f"'sayıları değiştir' parametreleri değiştirir ({changed}/{len(res2['examples'])})")
    cache = scanner._cache_path()
    if cache and cache.is_file():
        txt = cache.read_text(encoding="utf-8")
        check("Find the equation" not in txt, "tarama önbelleği kitap metni içermez")


def main():
    t0 = time.time()
    test_registry()
    for kind in _selected_kinds():
        test_kind(kind)
    if not ONLY_MODULE and not ONLY_KIND:
        test_editor_policy()
        test_course_and_topic_matching()
        test_scanner()
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed  ({time.time() - t0:.0f} sn)")
    if FAILS:
        print("Başarısız:")
        for f in FAILS[:40]:
            print("  -", f)
    print("=" * 64)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
