# -*- coding: utf-8 -*-
"""
Course Simulation Library — Dynamic PDF scanner + Embedded pack merger
for Visual Math Lab.

Dependencies: PyMuPDF (fitz) for text extraction; Pillow for thumbnails.
"""
import os
import re
import json
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from fractions import Fraction

# Optional PyMuPDF
try:
    import fitz
except Exception:
    fitz = None

try:
    from PIL import Image
except Exception:
    Image = None

# Import Visual Math Engine components (graceful if missing)
_VML = None
_VME = None
try:
    import visual_math_lab as _VML
    from visual_math_lab import VisualMathEngine, normalize_extracted_math_text
    _VME = VisualMathEngine
except Exception:
    pass

# ---------------------------------------------------------------------------
# Export / cache directories
# ---------------------------------------------------------------------------
from app_paths import exports_dir as _exports_dir, resources_dir as _default_resources_dir

EXPORTS_DIR = _exports_dir()
SIM_DIR = EXPORTS_DIR / "course_simulations"
SIM_GRAPHS_DIR = SIM_DIR / "graphs"
SIM_PAGES_DIR = SIM_DIR / "pages"
SIM_CACHE_DIR = SIM_DIR / "cache"
SIM_JSON = SIM_DIR / "simulations.json"

for _d in (SIM_DIR, SIM_GRAPHS_DIR, SIM_PAGES_DIR, SIM_CACHE_DIR):
    try:
        _d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# SimulationRecord
# ---------------------------------------------------------------------------
class SimulationRecord:
    """Immutable-ish data holder for a single course simulation."""

    TYPE_LABELS = {
        "slope_intercept": "Slope-Intercept",
        "point_slope": "Point-Slope",
        "two_point_line": "Two-Point Line",
        "parallel_line": "Parallel Line",
        "perpendicular_line": "Perpendicular Line",
        "quadratic": "Quadratic",
        "system_of_equations": "System of Equations",
        "trig_triangle": "Right Triangle Trig",
        "unit_circle": "Unit Circle",
        "trig_wave": "Trig Wave",
        "derivative": "Derivative",
        "integral": "Integral",
        "vector_basic": "Vectors",
        "unknown": "Unknown",
        "unsupported": "Unsupported",
    }

    def __init__(self, data=None, **kwargs):
        d = dict(data or {})
        d.update(kwargs)
        self._data = d

    def __getitem__(self, key):
        return self._data.get(key)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def to_dict(self):
        return dict(self._data)

    @property
    def id(self):
        return self._data.get("id", "")

    @property
    def source_type(self):
        return self._data.get("source_type", "dynamic")

    @property
    def title(self):
        return self._data.get("title", "")

    @property
    def problem_type(self):
        return self._data.get("problem_type", "unknown")

    @property
    def status(self):
        return self._data.get("status", "unknown")

    @property
    def verified(self):
        return bool(self._data.get("verified", False))

    @property
    def confidence(self):
        return float(self._data.get("confidence", 0.0))

    @property
    def source_pdf(self):
        return self._data.get("source_pdf", "")

    @property
    def page_number(self):
        return self._data.get("page_number", 0)

    def type_label(self):
        return self.TYPE_LABELS.get(self.problem_type, self.problem_type)


# ---------------------------------------------------------------------------
# PDFQuestionExtractor
# ---------------------------------------------------------------------------
class PDFQuestionExtractor:
    """Extract text from PDFs and yield candidate question blocks."""

    _HINTS = [
        ("slope_intercept", re.compile(r'slope[-\s]?intercept|e\u011fim[-\s]?kesme|y\s*=\s*mx\s*\+\s*b', re.I)),
        ("point_slope", re.compile(r'point[-\s]?slope|nokta[-\s]?e\u011fim', re.I)),
        ("two_point_line", re.compile(r'two points|passing through.*\([^)]+\).*(?:and|&).*(?:\([^)]+\))', re.I)),
        ("parallel_line", re.compile(r'parallel.*line|paralel.*do\u011fru', re.I)),
        ("perpendicular_line", re.compile(r'perpendicular.*line|dik.*do\u011fru', re.I)),
        ("quadratic", re.compile(r'quadratic|parabol|x\^2|x\u00b2|vertex', re.I)),
        ("system_of_equations", re.compile(r'system of equations|denklem sistemi|solve the system', re.I)),
        ("trig_triangle", re.compile(r'sin\s*\u03b8|cos\s*\u03b8|tan\s*\u03b8|hypotenuse', re.I)),
        ("unit_circle", re.compile(r'unit circle|birim \u00e7ember', re.I)),
        ("derivative", re.compile(r'derivative|t\u00fcrev|tangent line|te\u011fet', re.I)),
        ("integral", re.compile(r'integral|area under|riemann', re.I)),
    ]

    def __init__(self, resources_dir=None):
        self.resources_dir = Path(resources_dir) if resources_dir else _default_resources_dir()

    def _pdf_hash(self, path):
        st = os.stat(path)
        return f"{int(st.st_mtime)}-{st.st_size}"

    def _find_pdfs(self):
        if not self.resources_dir.exists():
            return
        for p in self.resources_dir.rglob("*.pdf"):
            yield p

    def _extract_text(self, path):
        if fitz is None:
            return []
        try:
            doc = fitz.open(str(path))
            out = []
            for i, page in enumerate(doc):
                out.append((i + 1, page.get_text()))
            doc.close()
            return out
        except Exception:
            return []

    def _detect_hint(self, text):
        best = None
        best_score = 0
        for ptype, pat in self._HINTS:
            m = pat.search(text)
            if m:
                score = len(m.group(0))
                if ptype in ("slope_intercept", "point_slope", "two_point_line"):
                    if re.search(r'\bm\s*=\s*[-\d/]|\bpoint\s*=\s*\(|\(\s*[-\d/]+\s*,\s*[-\d/]+\s*\)', text):
                        score += 10
                if score > best_score:
                    best_score = score
                    best = ptype
        return best

    def _chunk_text(self, text):
        chunks = re.split(r'\n\s*\n|\n\s*(?:Example|Ex\.|Problem|Q\.|Question)\s*\d+', text)
        return [c.strip() for c in chunks if len(c.strip()) > 40]

    def extract_candidates(self, path):
        pages = self._extract_text(path)
        pdf_hash = self._pdf_hash(path)
        for page_num, text in pages:
            for chunk in self._chunk_text(text):
                hint = self._detect_hint(chunk)
                if hint is None:
                    continue
                yield {
                    "pdf_path": str(path),
                    "pdf_hash": pdf_hash,
                    "page_number": page_num,
                    "raw_text": chunk,
                    "hint_type": hint,
                }

    def scan_all(self, progress_callback=None):
        candidates = []
        pdfs = list(self._find_pdfs())
        total = len(pdfs)
        for i, path in enumerate(pdfs, 1):
            if progress_callback:
                progress_callback(f"Scanning {i}/{total}: {path.name}")
            for cand in self.extract_candidates(path):
                candidates.append(cand)
        return candidates


# ---------------------------------------------------------------------------
# CourseSimulationBuilder
# ---------------------------------------------------------------------------
class CourseSimulationBuilder:
    """Turn a candidate into a SimulationRecord using the Visual Math Engine."""

    def _make_id(self, cand):
        base = re.sub(r"[^A-Za-z0-9]+", "_", cand["raw_text"][:40]).strip("_")
        # Content fingerprint for a stable, readable simulation id - NOT a
        # security primitive. usedforsecurity=False says so to the runtime
        # and to scanners; a collision here only means two examples share
        # an id suffix, which the surrounding text already disambiguates.
        h = hashlib.md5(cand["raw_text"].encode("utf-8"),
                        usedforsecurity=False).hexdigest()[:8]
        return f"dyn_{cand['hint_type']}_{base}_{h}"[:64]

    def build(self, candidate):
        raw = candidate["raw_text"]
        norm = normalize_extracted_math_text(raw) if 'normalize_extracted_math_text' in globals() else raw
        engine = None
        if _VME is not None:
            try:
                engine = _VME(norm)
            except Exception:
                engine = None
        ptype = engine.problem_type if engine else candidate.get("hint_type", "unknown")
        supported = engine.is_supported() if engine else False

        if not supported or ptype is None:
            return SimulationRecord({
                "id": self._make_id(candidate),
                "source_type": "dynamic",
                "title": candidate["raw_text"][:80].replace("\n", " "),
                "problem_type": candidate.get("hint_type", "unknown"),
                "status": "unsupported",
                "confidence": 0.0,
                "source_pdf": candidate["pdf_path"],
                "page_number": candidate["page_number"],
                "question_text": raw,
                "normalized_question": norm,
                "parameters": {},
                "solution_text": "",
                "real_life_text": "",
                "real_life_text_tr": "",
                "graph_png_path": None,
                "animation_path": None,
                "verified": False,
                "created_at": datetime.now().isoformat(),
                "pdf_hash": candidate.get("pdf_hash", ""),
            })

        params = engine.params or {}
        title = self._auto_title(ptype, params)
        solution_text = ""
        graph_png = None
        try:
            viz = self._build_visualizer(ptype, params)
            if viz is not None:
                solution_text = viz.build_steps("en")
                graph_png = self._export_graph(viz, ptype)
        except Exception:
            pass

        rec = SimulationRecord({
            "id": self._make_id(candidate),
            "source_type": "dynamic",
            "title": title,
            "problem_type": ptype,
            "status": "ready" if supported else "needs_review",
            "confidence": 0.85 if supported else 0.4,
            "source_pdf": candidate["pdf_path"],
            "page_number": candidate["page_number"],
            "question_text": raw,
            "normalized_question": norm,
            "parameters": self._serialize_params(params),
            "solution_text": solution_text,
            "real_life_text": "",
            "real_life_text_tr": "",
            "graph_png_path": str(graph_png) if graph_png else None,
            "animation_path": None,
            "verified": False,
            "created_at": datetime.now().isoformat(),
            "pdf_hash": candidate.get("pdf_hash", ""),
        })
        return rec

    def _auto_title(self, ptype, params):
        if ptype == "slope_intercept":
            return f"Slope-intercept: m={self._fmt(params.get('m'))}, b={self._fmt(params.get('b'))}"
        if ptype == "point_slope":
            pt = params.get("point")
            return f"Point-slope: m={self._fmt(params.get('m'))}, point={pt}"
        if ptype == "two_point_line":
            return f"Two-point line: {params.get('p1')} and {params.get('p2')}"
        if ptype == "quadratic":
            return f"Quadratic: a={self._fmt(params.get('a'))}, b={self._fmt(params.get('b'))}, c={self._fmt(params.get('c'))}"
        if ptype == "parallel_line":
            return f"Parallel line through {params.get('point')}"
        if ptype == "perpendicular_line":
            return f"Perpendicular line through {params.get('point')}"
        if ptype == "system_of_equations":
            return "System of two linear equations"
        if ptype == "derivative":
            return f"Derivative: f(x)={params.get('func','?')} at x={params.get('x0',0)}"
        if ptype == "integral":
            return f"Integral: {params.get('func','?')} from {params.get('a',0)} to {params.get('b',0)}"
        return ptype.replace("_", " ").title()

    @staticmethod
    def _fmt(val):
        if val is None:
            return "?"
        if val == int(val):
            return str(int(val))
        try:
            fr = Fraction(val).limit_denominator(1000)
            if abs(float(fr) - val) < 1e-9 and fr.denominator <= 20:
                return str(fr)
        except Exception:
            pass
        return f"{val:.3f}".rstrip("0").rstrip(".")

    @staticmethod
    def _serialize_params(params):
        out = {}
        for k, v in params.items():
            if isinstance(v, (list, tuple)):
                out[k] = [float(x) if x is not None else None for x in v]
            elif isinstance(v, (int, float, str, bool, type(None))):
                out[k] = v
            else:
                out[k] = str(v)
        return out

    def _build_visualizer(self, ptype, params):
        if _VML is None:
            return None
        p = params
        try:
            if ptype == "slope_intercept":
                return _VML.SlopeInterceptVisualizer(p["m"], p["point"])
            if ptype == "point_slope":
                return _VML.PointSlopeVisualizer(p["m"], p["point"])
            if ptype == "two_point_line":
                return _VML.TwoPointLineVisualizer(p["p1"], p["p2"])
            if ptype == "parallel_line":
                return _VML.ParallelLineVisualizer(p["orig_m"], p.get("orig_b", 0), p["point"])
            if ptype == "perpendicular_line":
                return _VML.PerpendicularLineVisualizer(p["orig_m"], p.get("orig_b", 0), p["point"])
            if ptype == "quadratic":
                return _VML.QuadraticVisualizer(p["a"], p["b"], p["c"])
            if ptype == "system_of_equations":
                return _VML.SystemOfEquationsVisualizer(p["lines"][0], p["lines"][1])
            if ptype == "trig_triangle":
                return _VML.TriangleTrigVisualizer(p.get("opposite"), p.get("adjacent"), p.get("hyp"))
            if ptype == "unit_circle":
                return _VML.UnitCircleVisualizer(p["angle"])
            if ptype == "trig_wave":
                return _VML.TrigWaveVisualizer(p.get("trig_fn", "sin"))
            if ptype == "derivative":
                return _VML.DerivativeVisualizer(p["func"], p.get("x0", 0.0))
            if ptype == "integral":
                return _VML.IntegralVisualizer(p["func"], p["a"], p["b"])
            if ptype == "vector_basic":
                return _VML.VectorVisualizer(p.get("v1"), p.get("v2"))
        except Exception:
            return None
        return None

    def _export_graph(self, viz, ptype):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            fig = Figure(figsize=(6, 5), dpi=130, facecolor="#0f1b28")
            if hasattr(viz, "render_figure"):
                viz.render_figure(fig, lang="en", real_life=False)
            else:
                ax = fig.add_subplot(111)
                ax.set_facecolor("#0f1b28")
                m = getattr(viz, "new_m", getattr(viz, "m", 0))
                b = getattr(viz, "new_b", getattr(viz, "b", 0))
                xs, ys = viz.get_graph_data(m, b)
                ax.plot(xs, ys)
            canvas = FigureCanvasAgg(fig)
            slug = getattr(viz, "slug", ptype + "_graph")
            path = SIM_GRAPHS_DIR / f"{slug}.png"
            fig.savefig(path, facecolor="#0f1b28", dpi=150)
            return path
        except Exception:
            return None


# ---------------------------------------------------------------------------
# CourseSimulationLibrary
# ---------------------------------------------------------------------------
class CourseSimulationLibrary:
    """Manages embedded + dynamic simulations with caching."""

    def __init__(self, embedded_simulations=None):
        self._embedded = [
            SimulationRecord(d) if isinstance(d, dict) else d
            for d in (embedded_simulations or [])
        ]
        self._dynamic = []
        self._load_cache()

    def _load_cache(self):
        if SIM_JSON.exists():
            try:
                with open(SIM_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._dynamic = [SimulationRecord(d) for d in data.get("records", [])]
            except Exception:
                self._dynamic = []

    def _save_cache(self):
        try:
            payload = {
                "updated_at": datetime.now().isoformat(),
                "records": [r.to_dict() for r in self._dynamic],
            }
            with open(SIM_JSON, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def all_simulations(self):
        seen = set()
        out = []
        for r in self._embedded:
            rid = r.id
            if rid and rid not in seen:
                seen.add(rid)
                out.append(r)
        for r in self._dynamic:
            rid = r.id
            if rid and rid not in seen:
                seen.add(rid)
                out.append(r)
        return out

    def filter_by(self, source=None, ptype=None, status=None, query=None):
        out = self.all_simulations()
        if source:
            out = [r for r in out if r.source_type == source]
        if ptype:
            out = [r for r in out if r.problem_type == ptype]
        if status:
            out = [r for r in out if r.status == status]
        if query:
            q = query.lower()
            out = [r for r in out if q in (r.title or "").lower()
                   or q in (r.get("normalized_question") or "").lower()
                   or q in (r.source_pdf or "").lower()]
        return out

    def scan_resources(self, progress_callback=None, done_callback=None):
        def task():
            try:
                extractor = PDFQuestionExtractor()
                builder = CourseSimulationBuilder()
                if progress_callback:
                    progress_callback("Finding PDFs...")
                cands = extractor.scan_all(progress_callback)
                if progress_callback:
                    progress_callback(f"Found {len(cands)} candidates. Building...")
                records = []
                for i, cand in enumerate(cands, 1):
                    if progress_callback:
                        progress_callback(f"Building {i}/{len(cands)}...")
                    rec = builder.build(cand)
                    if rec is not None:
                        records.append(rec)
                self._dynamic = records
                self._save_cache()
                if done_callback:
                    done_callback(True, f"Scanned {len(cands)} candidates, built {len(records)} simulations.")
            except Exception as exc:
                if done_callback:
                    done_callback(False, str(exc))
        t = threading.Thread(target=task, daemon=True)
        t.start()
        return t

    def rebuild_dynamic(self, progress_callback=None, done_callback=None):
        self._dynamic = []
        return self.scan_resources(progress_callback, done_callback)

    def add_dynamic_record(self, record):
        if isinstance(record, dict):
            record = SimulationRecord(record)
        self._dynamic.append(record)
        self._save_cache()

    def clear_dynamic(self):
        self._dynamic = []
        self._save_cache()

    def count_by_source(self):
        counts = {"embedded": 0, "dynamic": 0, "built_in": 0}
        for r in self.all_simulations():
            counts[r.source_type] = counts.get(r.source_type, 0) + 1
        return counts

    def get_by_id(self, sid):
        for r in self.all_simulations():
            if r.id == sid:
                return r
        return None
