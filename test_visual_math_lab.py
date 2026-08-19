# -*- coding: utf-8 -*-
"""
Comprehensive test suite for Visual Math Lab (Phases 1-7).

Covers, for every problem family: parser detection, deterministic solver,
step-by-step text, and Matplotlib PNG export. Runs head-less (no Tk window).

Run with:
    python test_visual_math_lab.py
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Kurs PDF'leri depoya girmez (ucuncu taraf telifi + boyut), bu yuzden CI
# runner'inda Resources/ YOKTUR. Yollar artik dosyanin kendi konumundan
# turetiliyor (sahibinin makinesinde birebir ayni sonuc) ve MCA_RESOURCES
# ortam degiskeniyle baska bir klasore yonlendirilebiliyor.
PROJECT = Path(__file__).resolve().parent
RESOURCES = Path(os.environ.get("MCA_RESOURCES") or (PROJECT / "Resources"))
# Resources yoksa "alintilanan PDF gercekten duruyor mu" kontrolleri
# ATLANIR (calisamazlar) — sayilari ozet satirinda raporlanir.
RESOURCES_AVAILABLE = RESOURCES.is_dir() and any(RESOURCES.rglob("*.pdf"))


def _pdf_resolves(rel):
    if not rel:
        return False
    if (RESOURCES / rel).exists() or (PROJECT / rel).exists():
        return True
    try:
        return any(True for _ in RESOURCES.rglob(Path(rel).name))
    except Exception:
        return False

# Keep console output safe on Windows code pages (√, °, … characters).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")  # head-less backend, no Tk needed
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

import visual_math_lab as vml
from visual_math_lab import (
    VisualMathEngine,
    SlopeInterceptVisualizer, TwoPointLineVisualizer, PointSlopeVisualizer,
    ParallelLineVisualizer, PerpendicularLineVisualizer,
    QuadraticVisualizer, SystemOfEquationsVisualizer,
    TriangleTrigVisualizer, UnitCircleVisualizer, TrigWaveVisualizer,
    DerivativeVisualizer, IntegralVisualizer, VectorVisualizer,
    GRAPHS_DIR, ANIMATIONS_DIR, REPORTS_DIR, MANIM_AVAILABLE, BG,
    normalize_extracted_math_text, extract_text_with_tesseract, grab_clipboard_image,
)


# ---------------------------------------------------------------------------
# Skip Phase 4-7 if SymPy is not installed (deterministic solver needs sp)
# ---------------------------------------------------------------------------
def _skip_if_no_sympy():
    if vml.sp is None:
        print("   [SKIP] sympy not installed — Phase 4-7 tests skipped")
        return True
    return False

PASSED = 0
FAILED = 0
SKIPPED = 0


def check(cond, label):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"   [PASS] {label}")
    else:
        FAILED += 1
        print(f"   [FAIL] {label}")


def skip(label):
    """Ortam yoklugu yuzunden calisamayan kontrol (basarisiz DEGIL)."""
    global SKIPPED
    SKIPPED += 1
    print(f"   [SKIP] {label}")


def detect(text):
    return VisualMathEngine(text)


def export_png(viz, name):
    """Render a visualizer to a >=150 dpi PNG and confirm the file exists."""
    fig = Figure(figsize=getattr(viz, "fig_size", (6, 5)), dpi=130, facecolor=BG)
    if hasattr(viz, "render_figure"):
        viz.render_figure(fig, lang="en", real_life=False)
    else:  # linear families are drawn from get_graph_data
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG)
        m = getattr(viz, "new_m", getattr(viz, "m", 0))
        b = getattr(viz, "new_b", getattr(viz, "b", 0))
        xs, ys = viz.get_graph_data(m, b)
        ax.plot(xs, ys)
    FigureCanvasAgg(fig)
    path = GRAPHS_DIR / f"test_{name}.png"
    fig.savefig(path, facecolor=BG, dpi=150)
    return path.exists()


# --------------------------------------------------------------------------- #
def test_phase1():
    print("\nPHASE 1 — Slope-Intercept")
    variations = [
        "Find the slope-intercept form of the line that passes through (0, -2) and has a slope of 1/2.",
        "Find the equation of a line with slope 1/2 passing through (0, -2).",
        "A line passes through (0, -2) and has slope 1/2. Find y = mx + b.",
        "Slope is 1/2 and y-intercept is -2.",
        "m = 1/2, b = -2",
        "Eğimi 1/2 olan ve (0, -2) noktasından geçen doğrunun denklemini bulun.",
    ]
    for txt in variations:
        e = detect(txt)
        check(e.problem_type == "slope_intercept" and abs(e.params["m"] - 0.5) < 1e-9
              and abs(e.params["b"] + 2) < 1e-9, f"parser: {txt[:45]}...")
    viz = SlopeInterceptVisualizer(0.5, (0, -2))
    check(viz.equation_str == "y = 1/2x - 2", "solver equation = y = 1/2x - 2")
    check(viz.b == -2.0, "solver b = -2")
    steps_en = viz.build_steps("en")
    steps_tr = viz.build_steps("tr")
    check("y = 1/2x - 2" in steps_en, "step text contains final equation")
    check("A. What is given?" in steps_en and "A. Verilenler" in steps_tr, "A-H labels bilingual")
    check("ramp" in viz.build_real_life("en").lower(), "real-life mentions ramp")
    check(export_png(viz, "phase1_slope"), "PNG export")


def test_phase2():
    print("\nPHASE 2 — Manim safety + Real Life View")
    check(isinstance(MANIM_AVAILABLE, bool), "MANIM_AVAILABLE is a bool (no crash if missing)")
    viz = SlopeInterceptVisualizer(0.5, (0, -2))
    rl_en = viz.build_real_life("en")
    rl_tr = viz.build_real_life("tr")
    check(len(rl_en) > 20 and "ramp" in rl_en.lower(), "Real-Life View (en) generated")
    check(len(rl_tr) > 20 and "rampa" in rl_tr.lower(), "Real-Life View (tr) generated")
    check(ANIMATIONS_DIR.exists(), "animations export folder exists")


def test_phase3():
    print("\nPHASE 3 — Linear Functions Pack")
    # two-point
    e = detect("Find the equation of the line passing through (1, 2) and (5, 4).")
    check(e.problem_type == "two_point_line", "two-point parser")
    v2 = TwoPointLineVisualizer((1, 2), (5, 4))
    check(abs(v2.m - 0.5) < 1e-9 and abs(v2.b - 1.5) < 1e-9, "two-point solver m=1/2, b=3/2")
    check("m = (y2 - y1)" in v2.build_steps("en"), "two-point step text")
    check(export_png(v2, "phase3_two_point"), "two-point PNG export")
    # point-slope
    e = detect("Write the point-slope form of the line with slope 3 passing through (2, 5).")
    check(e.problem_type == "point_slope", "point-slope parser")
    v3 = PointSlopeVisualizer(3, (2, 5))
    check(v3.slope_intercept == "y = 3x - 1", "point-slope -> y = 3x - 1")
    check("y - 5 = 3(x - 2)" in v3.point_slope_form, "point-slope form y - 5 = 3(x - 2)")
    check(export_png(v3, "phase3_point_slope"), "point-slope PNG export")
    # parallel
    e = detect("Find the equation of the line parallel to y = 2x + 1 passing through (3, 4).")
    check(e.problem_type == "parallel_line", "parallel parser")
    v4 = ParallelLineVisualizer(2, 1, (3, 4))
    check(v4.new_eq == "y = 2x - 2", "parallel -> y = 2x - 2")
    check(export_png(v4, "phase3_parallel"), "parallel PNG export")
    # perpendicular
    e = detect("Find the equation of the line perpendicular to y = 2x + 1 passing through (3, 4).")
    check(e.problem_type == "perpendicular_line", "perpendicular parser")
    v5 = PerpendicularLineVisualizer(2, 1, (3, 4))
    check(v5.new_eq == "y = -1/2x + 11/2", "perpendicular -> y = -1/2x + 11/2")
    check(export_png(v5, "phase3_perpendicular"), "perpendicular PNG export")


def test_phase4():
    print("\nPHASE 4 — Quadratic + Systems")
    if _skip_if_no_sympy():
        return
    e = detect("Graph y = x^2 - 4x + 3.")
    check(e.problem_type == "quadratic" and e.params["a"] == 1 and e.params["b"] == -4
          and e.params["c"] == 3, "quadratic parser a=1,b=-4,c=3")
    q = QuadraticVisualizer(1, -4, 3)
    check((q.vx, q.vy) == (2.0, -1.0), "quadratic vertex = (2, -1)")
    check(q.roots == [1.0, 3.0], "quadratic roots = 1 and 3")
    check("vertex" in q.build_steps("en").lower(), "quadratic step text")
    check(export_png(q, "phase4_quadratic"), "quadratic PNG export")

    e = detect("Solve and graph the system: y = 2x + 1 and y = -x + 4.")
    check(e.problem_type == "system_of_equations", "system parser")
    s = SystemOfEquationsVisualizer((2, 1), (-1, 4))
    check((s.ix, s.iy) == (1.0, 3.0), "system intersection = (1, 3)")
    check("Intersection" in s.build_steps("en"), "system step text")
    check(export_png(s, "phase4_system"), "system PNG export")


def test_phase5():
    print("\nPHASE 5 — Trigonometry / Unit Circle / Waves")
    no_sp = _skip_if_no_sympy()
    # triangle trig and wave tests don't strictly need sp, but unit circle exact does
    e = detect("Find sin, cos, and tan for a right triangle with opposite = 3, adjacent = 4, hypotenuse = 5.")
    check(e.problem_type == "trig_triangle", "triangle parser")
    t = TriangleTrigVisualizer(3, 4, 5)
    check((t.sin, t.cos, t.tan) == ("3/5", "4/5", "3/4"), "triangle sin=3/5 cos=4/5 tan=3/4")
    check(export_png(t, "phase5_triangle"), "triangle PNG export")

    e = detect("Show sin and cos on the unit circle for 30 degrees.")
    check(e.problem_type == "unit_circle", "unit-circle parser")
    u = UnitCircleVisualizer(30)
    check(abs(u.cos_v - (3 ** 0.5) / 2) < 1e-9, "unit circle cos 30 = sqrt(3)/2")
    check(abs(u.sin_v - 0.5) < 1e-9, "unit circle sin 30 = 1/2")
    if not no_sp:
        check("3" in u.cos_str, "unit circle exact cos string")
    check(export_png(u, "phase5_unit_circle"), "unit-circle PNG export")

    e = detect("Graph y = sin(x).")
    check(e.problem_type == "trig_wave", "wave parser")
    w = TrigWaveVisualizer("sin")
    check("amplitude" in w.build_steps("en").lower(), "wave step text")
    check(export_png(w, "phase5_wave"), "wave PNG export")


def test_phase6():
    print("\nPHASE 6 — Derivative / Tangent Line")
    if _skip_if_no_sympy():
        return
    e = detect("Find the derivative of f(x) = x^2 and show the tangent line at x = 2.")
    check(e.problem_type == "derivative", "derivative parser")
    d = DerivativeVisualizer("x^2", 2)
    check(d.deriv_str == "2x", "derivative f'(x) = 2x")
    check(d.slope == 4.0, "slope at x=2 is 4")
    check(d.tangent_str == "y = 4x - 4", "tangent line y = 4x - 4")
    check("tangent" in d.build_steps("en").lower(), "derivative step text")
    check(export_png(d, "phase6_derivative"), "derivative PNG export")


def test_phase7():
    print("\nPHASE 7 — Integral / Area / Riemann")
    if _skip_if_no_sympy():
        return
    e = detect("Find the area under f(x) = x^2 from x = 0 to x = 2.")
    check(e.problem_type == "integral", "integral parser")
    it = IntegralVisualizer("x^2", 0, 2)
    check(abs(it.exact_val - 8 / 3) < 1e-9, "integral exact = 8/3")
    check(it.exact_str == "8/3", "integral exact string = 8/3")
    a5 = it.riemann(5, "mid")
    a50 = it.riemann(50, "mid")
    a500 = it.riemann(500, "mid")
    check(a5 is not None and a50 is not None and a500 is not None, "Riemann sums numeric")
    check(abs(a500 - 8 / 3) < abs(a5 - 8 / 3) and abs(a500 - 8 / 3) < 1e-2,
          "Riemann converges toward 8/3 as n grows")
    check("Area" in it.build_steps("en"), "integral step text")
    check(export_png(it, "phase7_integral"), "integral PNG export")


def test_extra_vectors():
    print("\nEXTRA — Vectors")
    e = detect("Vectors v1 = (3, 4) and v2 = (1, 2). Find the magnitude and the sum.")
    check(e.problem_type == "vector_basic", "vector parser")
    vec = VectorVisualizer((3, 4), (1, 2))
    check(abs(vec.mag1 - 5.0) < 1e-9, "vector magnitude = 5")
    check(vec.sum == (4.0, 6.0), "vector sum = (4, 6)")
    check(export_png(vec, "extra_vector"), "vector PNG export")

def test_image_question_support():
    print("\nIMAGE QUESTION INPUT - OCR / Vision pipeline helpers")
    raw = (
        "Write the equation of the line in point-slope form.\n"
        "m= - 1 / 4\n"
        "( -6, 1 )"
    )
    expected = (
        "Write the equation of the line in point-slope form.\n"
        "m = -1/4\n"
        "(-6, 1)"
    )
    normalized = normalize_extracted_math_text(raw)
    check(normalized == expected, "OCR normalizer cleans fraction, spaces, and point")
    check(normalize_extracted_math_text("m= - l / 4") == "m = -1/4", "OCR normalizer fixes l/1 slope confusion")
    check(normalize_extracted_math_text("m= - I / 4") == "m = -1/4", "OCR normalizer fixes I/1 slope confusion")

    e = detect(expected)
    check(e.problem_type == "point_slope", "image-extracted point-slope parser")
    check(abs(e.params["m"] + 0.25) < 1e-9, "image parser m = -1/4")
    check(e.params["point"] == (-6.0, 1.0), "image parser point = (-6, 1)")

    viz = PointSlopeVisualizer(e.params["m"], e.params["point"])
    check(viz.point_slope_form == "y - 1 = -1/4(x + 6)", "negative x0 point-slope format")
    check(viz.slope_intercept == "y = -1/4x - 1/2", "negative slope-intercept form")
    check("goes downward" in viz.build_real_life("en").lower(), "negative slope real-life explanation")

    tri = viz.get_slope_triangle(viz.m, viz.b)
    second_point = (viz.point[0] + tri["run"], viz.point[1] + tri["rise"])
    check(tri["run"] == 4 and tri["rise"] == -1, "negative slope triangle run=4 rise=-1")
    check(second_point == (-2.0, 0.0), "negative slope second point = (-2, 0)")
    check(abs(viz.b + 0.5) < 1e-9, "y-intercept = -1/2")
    check(export_png(viz, "image_question_negative_slope"), "negative slope PNG export")

    text, status = extract_text_with_tesseract(str(GRAPHS_DIR / "missing_ocr_input.png"))
    check(isinstance(text, str) and isinstance(status, str), "OCR unavailable safety returns strings")

    original_grab = getattr(vml.ImageGrab, "grabclipboard", None) if vml.ImageGrab is not None else None
    if vml.ImageGrab is not None and original_grab is not None:
        try:
            vml.ImageGrab.grabclipboard = lambda: None
            img, msg = grab_clipboard_image()
            check(img is None and "No image found" in msg, "clipboard no image warning")
        finally:
            vml.ImageGrab.grabclipboard = original_grab
    else:
        img, msg = grab_clipboard_image()
        check(img is None and isinstance(msg, str), "clipboard support missing handled safely")


def test_embedded_course_simulations():
    print("\nEMBEDDED COURSE SIMULATIONS")
    import embedded_course_simulations as emb
    sims = emb.EMBEDDED_COURSE_SIMULATIONS
    check(len(sims) >= 10, f"embedded count >= 10 (got {len(sims)})")
    ENGINE_SUPPORTED_TYPES = {
        "slope_intercept", "point_slope", "two_point_line",
        "parallel_line", "perpendicular_line", "quadratic",
        "system_of_equations", "trig_triangle", "unit_circle",
        "trig_wave", "vector", "derivative", "integral"
    }
    for rec in sims:
        sid = rec["id"]
        ptype = rec.get("problem_type", "")
        # Skip quadratic/system tests if SymPy is missing (test-environment limitation)
        if ptype in ("quadratic", "derivative", "integral") and vml.sp is None:
            print(f"   [SKIP] {sid}: sympy not installed — {ptype} tests skipped")
            continue
        check(bool(sid), f"{sid}: has id")
        check(rec.get("source_type") == "embedded", f"{sid}: source_type = embedded")
        check(rec.get("status") == "ready", f"{sid}: status = ready")
        check(rec.get("verified") is True, f"{sid}: verified = true")
        q = rec.get("normalized_question") or rec.get("question_text", "")
        check(bool(q), f"{sid}: has question text")
        # Only graphable records (graph_required=True) must re-parse and draw.
        # Concept cards / algebraic worked examples are validated by content only.
        if rec.get("graph_required") and ptype in ENGINE_SUPPORTED_TYPES:
            e = VisualMathEngine(q)
            check(e.problem_type == ptype, f"{sid}: parser problem_type = {ptype}")
            check(e.is_supported(), f"{sid}: parser is_supported")
            try:
                viz = None
                p = e.params
                if ptype == "slope_intercept":
                    viz = SlopeInterceptVisualizer(p["m"], p["point"])
                elif ptype == "point_slope":
                    viz = PointSlopeVisualizer(p["m"], p["point"])
                elif ptype == "two_point_line":
                    viz = TwoPointLineVisualizer(p["p1"], p["p2"])
                elif ptype == "parallel_line":
                    viz = ParallelLineVisualizer(p["orig_m"], p.get("orig_b", 0), p["point"])
                elif ptype == "perpendicular_line":
                    viz = PerpendicularLineVisualizer(p["orig_m"], p.get("orig_b", 0), p["point"])
                elif ptype == "quadratic":
                    viz = QuadraticVisualizer(p["a"], p["b"], p["c"])
                elif ptype == "system_of_equations":
                    viz = SystemOfEquationsVisualizer(p["lines"][0], p["lines"][1])
                if viz:
                    check(export_png(viz, f"embedded_{sid}"), f"{sid}: PNG export")
            except Exception as exc:
                check(False, f"{sid}: graph export error ({exc})")
        else:
            print(f"   [INFO] {sid}: parser/graph not tested (type '{ptype}' not yet in engine)")
        sol = rec.get("solution_text", "")
        check(len(sol) > 20, f"{sid}: solution text present")
        check(len(rec.get("real_life_text", "")) > 10, f"{sid}: real_life text present")
        check(len(rec.get("real_life_text_tr", "")) > 10, f"{sid}: real_life_tr text present")
        pdf_rel = rec.get("source_pdf", "")
        if pdf_rel:
            pdf_path = RESOURCES / pdf_rel
            if not pdf_path.exists():
                skip(f"{sid}: source PDF exists ({pdf_path} yok)")
            else:
                check(True, f"{sid}: source PDF exists")
        check(isinstance(rec.get("page_number"), int) and rec["page_number"] >= 0, f"{sid}: page_number valid")


def test_course_simulation_library():
    print("\nCOURSE SIMULATION LIBRARY")
    import course_simulation_library as csl
    rec = csl.SimulationRecord(id="test_001", title="Test", problem_type="point_slope", status="ready")
    check(rec.id == "test_001", "SimulationRecord.id")
    check(rec.get("title") == "Test", "SimulationRecord.get")
    check(rec.to_dict()["id"] == "test_001", "SimulationRecord.to_dict")
    lib = csl.CourseSimulationLibrary()
    check(lib is not None, "CourseSimulationLibrary init")
    import embedded_course_simulations as emb
    lib2 = csl.CourseSimulationLibrary(emb.EMBEDDED_COURSE_SIMULATIONS)
    all_sims = lib2.all_simulations()
    check(len(all_sims) >= len(emb.EMBEDDED_COURSE_SIMULATIONS), "all_simulations includes embedded")
    emb_only = lib2.filter_by(source="embedded")
    check(len(emb_only) >= len(emb.EMBEDDED_COURSE_SIMULATIONS), "filter_by source=embedded")
    ps_only = lib2.filter_by(ptype="point_slope")
    check(len(ps_only) >= 3, "filter_by ptype=point_slope")
    slope_sims = lib2.filter_by(query="slope")
    check(len(slope_sims) >= 3, "filter_by query=slope")
    counts = lib2.count_by_source()
    check("embedded" in counts, "count_by_source has embedded")
    found = lib2.get_by_id(emb.EMBEDDED_COURSE_SIMULATIONS[0]["id"])
    check(found is not None, "get_by_id finds first embedded")
    check(csl.SIM_JSON.parent.exists(), "SIM_DIR exists")
    extractor = csl.PDFQuestionExtractor(resources_dir=str(RESOURCES))
    check(extractor is not None, "PDFQuestionExtractor init")
    builder = csl.CourseSimulationBuilder()
    check(builder is not None, "CourseSimulationBuilder init")
    mock_cand = {
        "raw_text": "Write the equation of the line in point-slope form. m = -1/4, point = (-6, 1)",
        "pdf_path": "mock.pdf", "pdf_hash": "abc", "page_number": 1, "hint_type": "point_slope",
    }
    rec = builder.build(mock_cand)
    check(rec is not None, "builder returns SimulationRecord")
    check(rec.get("status") in ("ready", "unsupported"), f"builder status = {rec.get('status')}")
    lib3 = csl.CourseSimulationLibrary(emb.EMBEDDED_COURSE_SIMULATIONS)
    dup = dict(emb.EMBEDDED_COURSE_SIMULATIONS[0])
    dup["source_type"] = "dynamic"
    lib3.add_dynamic_record(csl.SimulationRecord(dup))
    all_after = lib3.all_simulations()
    check(len(all_after) == len(emb.EMBEDDED_COURSE_SIMULATIONS), "duplicate dedup by id")


# ===========================================================================
# QA Suite (Claude QA pass, 2026-06-20)
# Real quality gates: data integrity, ready/needs_review hygiene, source PDFs,
# preview-data builders, and headless Load-Simulation UI wiring.
# ===========================================================================
REQUIRED_SIM_FIELDS = [
    "id", "source_type", "course", "title", "source_pdf", "page_number",
    "question_text", "normalized_question", "problem_type", "parameters",
    "solution_text", "visual_type", "status", "confidence", "verified",
]
REQUIRED_FORMULA_FIELDS = [
    "id", "source_type", "course", "topic", "title", "visual_type",
    "source_pdf", "page_number", "status",
]


def _viz_for(ptype, p):
    if ptype == "slope_intercept":
        return SlopeInterceptVisualizer(p["m"], p["point"])
    if ptype == "point_slope":
        return PointSlopeVisualizer(p["m"], p["point"])
    if ptype == "two_point_line":
        return TwoPointLineVisualizer(p["p1"], p["p2"])
    if ptype == "parallel_line":
        return ParallelLineVisualizer(p["orig_m"], p.get("orig_b", 0), p["point"])
    if ptype == "perpendicular_line":
        return PerpendicularLineVisualizer(p["orig_m"], p.get("orig_b", 0), p["point"])
    if ptype == "quadratic":
        return QuadraticVisualizer(p["a"], p["b"], p["c"])
    if ptype == "system_of_equations":
        return SystemOfEquationsVisualizer(p["lines"][0], p["lines"][1])
    return None


def test_qa_embedded_quality():
    print("\nQA — EMBEDDED SIMULATION QUALITY")
    import embedded_course_simulations as emb                                 # item 2
    sims = emb.EMBEDDED_COURSE_SIMULATIONS
    check(len(sims) >= 10, f"embedded import ok ({len(sims)} records)")
    ids = [r.get("id") for r in sims]
    check(len(ids) == len(set(ids)), "no duplicate simulation ids")           # item 3
    norms = [(r.get("normalized_question") or r.get("question_text") or "").strip().lower()
             for r in sims]
    check(len(norms) == len(set(norms)), "no duplicate normalized questions")
    ready = [r for r in sims if r.get("status") == "ready"]
    needs = [r for r in sims if r.get("status") == "needs_review"]
    print(f"   [INFO] ready={len(ready)} needs_review={len(needs)} total={len(sims)}")
    for r in sims:
        sid = r.get("id")
        missing = [f for f in REQUIRED_SIM_FIELDS if r.get(f) in (None, "")]   # item 4
        check(not missing, f"{sid}: required fields present (missing={missing})")
        check(bool((r.get("question_text") or "").strip()),                   # item 5
              f"{sid}: question_text not empty")
        if r.get("status") == "ready":
            check(bool((r.get("solution_text") or "").strip()),               # item 6
                  f"{sid}: solution_text not empty")
            check(bool(r.get("answer") or r.get("alternate_answer")),         # item 8
                  f"{sid}: has an answer")
        pn = r.get("page_number")
        check(isinstance(pn, int) and pn >= 1, f"{sid}: page_number >= 1 ({pn})")  # item 12
        if RESOURCES_AVAILABLE:                                                # item 11
            check(_pdf_resolves(r.get("source_pdf", "")), f"{sid}: source_pdf resolves")
        else:
            skip(f"{sid}: source_pdf resolves (Resources/ bu ortamda yok)")
    for r in ready:                                                           # items 7 + 9
        if not r.get("graph_required"):
            continue
        ptype = r.get("problem_type")
        if ptype == "quadratic" and vml.sp is None:
            print(f"   [SKIP] {r['id']}: sympy missing for quadratic graph")
            continue
        q = r.get("normalized_question") or r.get("question_text", "")
        e = VisualMathEngine(q)
        check(e.problem_type == ptype, f"{r['id']}: graphable re-parses as {ptype}")
        check(e.is_supported(), f"{r['id']}: graphable is_supported")
        viz = _viz_for(ptype, e.params)
        if viz is not None:
            check(export_png(viz, f"qa_{r['id']}"), f"{r['id']}: graph PNG export")
    concepts = [r for r in sims if not r.get("graph_required")]               # item 16
    check(all(r.get("visual_type") == "concept_card" for r in concepts),
          "all non-graph records are concept_card")
    check(all(r.get("status") != "ready" for r in needs) or not needs,        # item 10
          "needs_review records are not status=ready")


def test_qa_specific_samples():
    print("\nQA — SPECIFIC EMBEDDED SAMPLES")
    import embedded_course_simulations as emb
    by_id = {r["id"]: r for r in emb.EMBEDDED_COURSE_SIMULATIONS}
    ps = by_id.get("emb_alg1_point_slope_001")                               # item 18 + 19
    check(ps is not None, "point_slope sample present")
    if ps:
        e = VisualMathEngine(ps["normalized_question"])
        check(e.problem_type == "point_slope", "point_slope sample parses")
        check(ps["parameters"]["m"] < 0, "point_slope sample has negative slope")
        viz = PointSlopeVisualizer(e.params["m"], e.params["point"])
        check("downward" in viz.build_real_life("en").lower(), "negative slope real-life ok")
    sysrec = next((r for r in emb.EMBEDDED_COURSE_SIMULATIONS                 # item 17
                   if r.get("problem_type") == "system_of_equations" and r.get("graph_required")), None)
    check(sysrec is not None, "system_of_equations sample present")
    if sysrec:
        e = VisualMathEngine(sysrec["normalized_question"])
        check(e.problem_type == "system_of_equations", "system sample parses")
        s = SystemOfEquationsVisualizer(e.params["lines"][0], e.params["lines"][1])
        check(export_png(s, "qa_system_sample"), "system sample graph export")


def test_qa_formula_library():
    print("\nQA — FORMULA LIBRARY")
    import embedded_formula_library as flib                                   # item 1
    forms = flib.EMBEDDED_FORMULA_LIBRARY
    check(len(forms) >= 10, f"formula library import ok ({len(forms)} records)")
    ids = [r.get("id") for r in forms]
    check(len(ids) == len(set(ids)), "no duplicate formula ids")
    for r in forms:
        fid = r.get("id")
        missing = [f for f in REQUIRED_FORMULA_FIELDS if r.get(f) in (None, "")]  # item 13
        check(not missing, f"{fid}: required formula fields present (missing={missing})")
        check(bool(r.get("formula_plain") or r.get("description")),
              f"{fid}: has formula_plain or description")
        fl = r.get("formula_latex", "") or ""
        check(not (fl.rstrip().endswith("\\{") and len(fl) < 16),
              f"{fid}: latex not truncated ({fl!r})")
        if RESOURCES_AVAILABLE:
            check(_pdf_resolves(r.get("source_pdf", "")), f"{fid}: source_pdf resolves")
        else:
            skip(f"{fid}: source_pdf resolves (Resources/ bu ortamda yok)")


def test_qa_preview_builder():
    print("\nQA — PREVIEW DATA BUILDERS")
    import embedded_course_simulations as emb
    import embedded_formula_library as flib

    class _Stub:
        pass
    stub = _Stub()
    stub._lang = "en"
    rec = emb.EMBEDDED_COURSE_SIMULATIONS[0]
    segs = vml.VisualMathLab._format_sim_preview(stub, rec)                   # item 14
    text = "".join(t for t, _ in segs)
    check(rec["title"] in text, "sim preview includes title")
    check(rec["question_text"] in text, "sim preview includes FULL question text")
    check("SOLUTION" in text, "sim preview includes solution section")
    check("Source PDF" in text and "Page Number" in text, "sim preview shows source+page")
    check("FINAL ANSWER" in text, "sim preview includes final answer")
    frec = flib.EMBEDDED_FORMULA_LIBRARY[0]
    fsegs = vml.VisualMathLab._format_formula_preview(stub, frec)
    ftext = "".join(t for t, _ in fsegs)
    check(frec["title"] in ftext, "formula preview includes title")
    check("FORMULA" in ftext, "formula preview includes formula section")


def test_qa_headless_load():
    print("\nQA — HEADLESS LOAD SIMULATION (UI wiring)")
    import tkinter as tk
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print(f"   [SKIP] Tk unavailable: {exc}")
        return

    class _App:
        language = "en"
    try:
        lab = vml.VisualMathLab(root, _App())
        root.update_idletasks()
        # The library now lives in the Simulation Studio window (built on open).
        studio = lab._open_simulation_studio()
        root.update_idletasks()
        check(studio is not None and lab._sim_tree is not None, "studio builds the library tree")
        # locate an embedded graphable record actually shown in the live table
        gidx = next((i for i, r in enumerate(lab._sim_list)
                     if r.get("source_type") == "embedded" and r.get("graph_required")), None)
        check(gidx is not None, "embedded graphable record present in list")
        if gidx is not None:
            lab._sim_tree.selection_set(str(gidx))
            lab._sim_selected_index = gidx
            lab._on_sim_tree_select()
            rec = lab._sim_list[gidx]
            # studio big-graph renders for a graphable record
            check(studio._figure is not None, "studio renders a graph for graphable record")
            # Load to Visual Math Lab populates the main lab panels
            lab.load_simulation_payload(rec)                                   # item 15
            root.update_idletasks()
            qtext = lab.question_text.get("1.0", "end").strip()
            check(len(qtext) > 0, "Load to VML populates the question field")
            step = lab.step_text.get("1.0", "end")
            check(rec["solution_text"][:20] in step, "Load fills step panel with curated solution")
        # concept-card: studio shows placeholder (no figure), load does not crash
        cidx = next((i for i, r in enumerate(lab._sim_list)
                     if r.get("source_type") == "embedded" and not r.get("graph_required")), None)
        if cidx is not None:
            crec = lab._sim_list[cidx]
            studio.render_graph(crec)                                          # item 16
            check(studio._figure is None, "concept card -> studio shows no figure")
            lab.load_simulation_payload(crec)
            root.update_idletasks()
            check(True, "concept card load does not crash")
        # item 20: missing graph_png_path is handled safely
        fake = dict(lab._sim_list[cidx if cidx is not None else 0])
        fake["graph_png_path"] = "exports/__does_not_exist__12345.png"
        studio.render_graph(fake)
        check(True, "missing graph_png_path handled without crash")
        lab._update_sim_preview(lab._sim_list[0])
        check(True, "preview update runs without crash")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        check(False, f"headless studio load raised: {exc}")
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def test_lesson_card_generator():
    print("\nVISUAL LESSON CARD GENERATOR")
    import tempfile
    import visual_lesson_card as vlc
    from visual_lesson_card import VisualLessonCardGenerator
    check(VisualLessonCardGenerator is not None, "VisualLessonCardGenerator import")
    tmp = Path(tempfile.gettempdir()) / "vml_lesson_cards_test"
    gen = VisualLessonCardGenerator(out_dir=tmp)
    check(tmp.exists(), "lesson_cards export folder created")
    # slope-intercept line card
    p = gen.generate_line_card(m=0.5, b=-2, given_points=[(0, -2)],
                               problem_type="slope_intercept", lang="en")
    check(Path(p).exists(), "slope-intercept line card file exists")
    check(Path(p).stat().st_size > 0, "slope-intercept line card size > 0")
    # point-slope, negative slope (the reference example)
    p2 = gen.generate_line_card(m=-5, b=6, given_points=[(2, -4)], problem_type="point_slope",
                                eq_transform="y + 4 = -5(x - 2)  ->  y = -5x + 6", lang="tr")
    check(Path(p2).exists(), "point-slope negative-slope card exists")
    check(Path(p2).stat().st_size > 5000, "negative-slope card size reasonable")
    # from a live visualizer
    viz = SlopeInterceptVisualizer(2, (0, 1))
    p3 = gen.generate_from_visualizer(viz, "slope_intercept", title="Test", lang="en")
    check(Path(p3).exists(), "generate_from_visualizer produces a card")
    # concept fallback card (non-line problem)
    p4 = gen.generate_concept_card(title="Pythagoras", question="a=3, b=4",
                                   solution="c = sqrt(9+16) = 5", answer="c = 5", lang="en")
    check(Path(p4).exists(), "concept card produces a file")
    # from an embedded record
    import embedded_course_simulations as emb
    rec = next(r for r in emb.EMBEDDED_COURSE_SIMULATIONS
               if r.get("problem_type") == "slope_intercept")
    p5 = gen.generate_from_record(rec, lang="en")
    check(Path(p5).exists(), "generate_from_record produces a card")


def test_qa_headless_pro_ui():
    print("\nQA — HEADLESS PRO UI (toolbar, layout, needs_review safety)")
    import tkinter as tk
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print(f"   [SKIP] Tk unavailable: {exc}")
        return

    class _App:
        language = "en"
    try:
        lab = vml.VisualMathLab(root, _App())
        root.update_idletasks()
        check(all(hasattr(lab, a) for a in ("_outer_paned", "_left_paned", "_right_paned")),
              "resizable PanedWindows created")
        check(hasattr(lab, "_toolbar_status_var"), "toolbar built")
        # compact launcher panel exists in the main lab
        check(getattr(lab, "_compact_selected_var", None) is not None, "compact library launcher built")
        lab._reset_layout()
        check(True, "reset layout runs without crash")
        lab.question_text.insert("1.0", "stuff")
        lab._new_question()
        check(lab.question_text.get("1.0", "end").strip() == "", "new question clears field")
        # Duplicate-window prevention: re-opening returns the SAME instance
        s1 = lab._open_simulation_studio()
        s2 = lab._open_simulation_studio()
        check(s1 is s2 and s1 is lab._studio_window, "duplicate studio window prevented")
        check(isinstance(s1, vml.SimulationStudioWindow), "SimulationStudioWindow instance")
        # GÖREV 11 #11 — loading a needs_review simulation must not crash
        fake = {
            "id": "fake_needs_review", "source_type": "embedded", "title": "Fake needs review",
            "problem_type": "concept_card", "question_text": "Explain something.",
            "normalized_question": "Explain something.", "solution_text": "Because reasons here.",
            "real_life_text": "Real life meaning.", "status": "needs_review", "verified": False,
            "confidence": 0.4, "graph_required": False, "source_pdf": "", "page_number": 1,
            "source_verified": False, "review_reason": "test",
        }
        lab._sim_list = [fake]
        lab._sim_selected_index = 0
        lab._update_sim_preview(fake)
        lab.load_simulation_payload(fake)
        check(True, "needs_review simulation loads without crash")
        # studio.render_graph for the needs_review concept card -> no figure, no crash
        s1.render_graph(fake)
        check(s1._figure is None, "needs_review concept card -> no studio figure")
        # Lesson card from a freshly solved line problem (no os.startfile in tests)
        from visual_lesson_card import VisualLessonCardGenerator
        lab._solve_problem_text("Find the slope-intercept form of the line through (0, -2) with slope 1/2.")
        gen = VisualLessonCardGenerator()
        path = gen.generate_from_visualizer(lab._current_viz, lab._current_type, lang="en")
        check(Path(path).exists(), "lesson card generated from a loaded problem")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        check(False, f"pro UI headless raised: {exc}")
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def test_studio_logic():
    print("\nSIMULATION STUDIO LOGIC (no Tk)")
    check(hasattr(vml, "SimulationStudioWindow"), "SimulationStudioWindow import")        # item 1
    check(hasattr(vml, "build_record_figure"), "build_record_figure import")
    import embedded_course_simulations as emb
    g = next(r for r in emb.EMBEDDED_COURSE_SIMULATIONS
             if r.get("graph_required") and r.get("problem_type") == "slope_intercept")
    check(bool(g.get("question_text")), "selected simulation has question_text")          # item 3
    check(bool(g.get("solution_text")), "selected simulation has solution_text")          # item 4
    if vml.sp is not None:
        fig = vml.build_record_figure(g, "en")                                            # item 7
        check(fig is not None, "build_record_figure renders a graphable record")
    c = next(r for r in emb.EMBEDDED_COURSE_SIMULATIONS if not r.get("graph_required"))
    check(vml.build_record_figure(c, "en") is None,                                       # item 8
          "build_record_figure returns None for a concept card")
    check(vml.build_record_figure({"graph_required": True, "normalized_question": ""}, "en") is None,
          "build_record_figure safe on empty question")
    check(vml.build_record_figure(None, "en") is None, "build_record_figure safe on None")


def main():
    print("=" * 64)
    print("Visual Math Lab — Phases 1-7 Test Suite")
    print(f"Manim available: {MANIM_AVAILABLE}  |  graphs -> {GRAPHS_DIR}")
    print("=" * 64)
    for fn in (test_phase1, test_phase2, test_phase3, test_phase4,
               test_phase5, test_phase6, test_phase7, test_extra_vectors,
               test_image_question_support, test_embedded_course_simulations,
               test_course_simulation_library,
               test_qa_embedded_quality, test_qa_specific_samples,
               test_qa_formula_library, test_qa_preview_builder,
               test_qa_headless_load, test_lesson_card_generator,
               test_qa_headless_pro_ui, test_studio_logic):
        try:
            fn()
        except Exception as exc:
            global FAILED
            FAILED += 1
            import traceback
            traceback.print_exc()
            print(f"   [ERROR] {fn.__name__}: {exc}")
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed"
          + (f", {SKIPPED} skipped (ortam)" if SKIPPED else ""))
    print("=" * 64)
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
