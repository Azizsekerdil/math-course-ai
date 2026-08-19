# -*- coding: utf-8 -*-
"""
Visual Math Lab — Visual Math Engine (Phase 7 — Calculus Pack)
Math Course AI Program extension module.

Supported problem types:
- slope_intercept ......... given point + slope → find equation              (Phase 1)
- two_point_line .......... given two points → find equation                 (Phase 3)
- point_slope ............. given point + slope → point-slope + slope-intercept (Phase 3)
- parallel_line ........... given line + point → parallel line               (Phase 3)
- perpendicular_line ...... given line + point → perpendicular line          (Phase 3)
- quadratic ............... y = a x^2 + b x + c → vertex, roots, intercepts   (Phase 4)
- system_of_equations ..... two lines → intersection point                   (Phase 4)
- trig_triangle ........... right triangle → sin / cos / tan                  (Phase 5)
- unit_circle ............. angle → sin / cos on the unit circle             (Phase 5)
- trig_wave ............... y = A sin(f x + p) → wave with amp/freq/phase     (Phase 5)
- derivative .............. f(x) → f'(x) + tangent line at x0                 (Phase 6)
- integral ................ area under f(x) on [a, b] + Riemann sum          (Phase 7)
- vector_basic ............ two vectors → sum / magnitude                     (extra)

Features:
- Matplotlib embedded graph (coordinate plane, parabola, unit circle, area shading, ...)
- Step-by-step A-H explanations in English and Turkish
- Real-Life view for every problem family
- PNG export (>=150 dpi) to <exports>/graphs (see app_paths.exports_dir())
- Manim animation (optional) for slope_intercept, quadratic, derivative, integral, unit_circle
- Per-problem interactive controls (m/b, a/b/c, amplitude/freq/phase, x0, bounds + n)
- Optional LM Studio AI enrichment (deterministic solver first, AI explanation second)
- Extended parser for English and Turkish question variations

Dependencies:
- sympy, matplotlib, numpy
- manim (optional, for MP4 animation export)
"""

import os
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from fractions import Fraction
from pathlib import Path

# ---------------------------------------------------------------------------
# Optional dependency handling
# ---------------------------------------------------------------------------
try:
    import sympy as sp
except Exception:
    sp = None

try:
    import numpy as np
except Exception:
    np = None

try:
    from PIL import Image, ImageTk, ImageGrab
except Exception:
    Image = None
    ImageTk = None
    ImageGrab = None

try:
    import pytesseract
except Exception:
    pytesseract = None

# Optional course simulation modules (lazy import in VisualMathLab)
_CSL = None
_EMB = None

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except Exception:
    FigureCanvasTkAgg = None
    Figure = None

MANIM_AVAILABLE = False
try:
    import manim
    # A wildcard import brings in mobjects (Axes, Dot, Line, ...) AND the
    # direction constants (UP, DOWN, LEFT, RIGHT, ORIGIN) that the scenes use.
    from manim import *  # noqa: F401,F403
    MANIM_AVAILABLE = True
except Exception:
    manim = None

# ---------------------------------------------------------------------------
# Export directories
# ---------------------------------------------------------------------------
from app_paths import exports_dir as _exports_dir, resources_dir as _resources_dir

EXPORTS_DIR = _exports_dir()
RESOURCES_DIR = _resources_dir()
GRAPHS_DIR = EXPORTS_DIR / "graphs"
ANIMATIONS_DIR = EXPORTS_DIR / "animations"
REPORTS_DIR = EXPORTS_DIR / "reports"
IMAGE_QUESTIONS_DIR = EXPORTS_DIR / "image_questions"
for _d in (GRAPHS_DIR, ANIMATIONS_DIR, REPORTS_DIR, IMAGE_QUESTIONS_DIR):
    try:
        _d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Theme colors (shared by all visualizers)
# ---------------------------------------------------------------------------
BG = "#FBF7F1"
PANEL_BG = "#FFFFFF"
GRID = "#ECE3D8"
AXIS = "#8A7E6E"
FG = "#2B2620"


def apply_dark_palette():
    """Ana uygulama karanlik temadayken VisualMathLab kurulmadan ONCE cagrilir.

    Yalnizca ortak cizim yolunu (_style_ax, render_figure, Studio) etkiler;
    eski gorsellestirici yollarindaki gomulu acik renkler bilerek birakildi
    (icerik adalari — bkz. ONERILER karanlik tema notu)."""
    global BG, PANEL_BG, GRID, AXIS, FG
    BG = "#2A241C"
    PANEL_BG = "#1B1712"
    GRID = "#3A3226"
    AXIS = "#A6987F"
    FG = "#EDE5D8"
C_BLUE = "#2f80ed"
C_YELLOW = "#C99A2E"
C_GREEN = "#16A55A"
C_PURPLE = "#8b5cf6"
C_RED = "#ef4444"
C_GRAY = "#64748b"
C_CYAN = "#22d3ee"


# ---------------------------------------------------------------------------
# Symbolic / numeric helpers
# ---------------------------------------------------------------------------
def _sym_parse(expr_str):
    """Parse a human-typed expression like '4x + x^2' into a SymPy expression.

    Handles implicit multiplication (4x -> 4*x) and caret powers (x^2 -> x**2).
    Returns None on failure or when SymPy is unavailable.
    """
    if sp is None or not expr_str:
        return None
    try:
        from sympy.parsing.sympy_parser import (
            parse_expr, standard_transformations,
            implicit_multiplication_application, convert_xor,
        )
        tr = standard_transformations + (implicit_multiplication_application, convert_xor)
        return parse_expr(str(expr_str).strip(), transformations=tr)
    except Exception:
        return None


def _linspace(a, b, n=400):
    """numpy.linspace with a pure-python fallback."""
    if np is not None:
        return np.linspace(a, b, n)
    if n < 2:
        return [a]
    step = (b - a) / (n - 1)
    return [a + i * step for i in range(n)]


def _evalf(expr, x_sym, value):
    """Evaluate a SymPy expression at x = value, returning a float (or None)."""
    if sp is None or expr is None:
        return None
    try:
        return float(expr.subs(x_sym, value))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Bilingual UI strings
# ---------------------------------------------------------------------------
_VML_TEXT = {
    "en": {
        "question_input": "Question / Problem",
        "load_example": "Load Example",
        "solve_visualize": "Solve & Visualize",
        "graph_panel": "Graph",
        "save_graph": "Save Graph PNG",
        "step_solution": "Step-by-Step Solution",
        "real_life": "Real-Life Explanation",
        "controls": "Controls",
        "m_label": "Slope (m):",
        "b_label": "Y-intercept (b):",
        "reset_example": "Reset Example",
        "create_animation": "Create Animation",
        "manim_missing": "Manim is not installed. Please install it with: pip install manim",
        "problem_not_supported": "This problem type is not supported yet.",
        "invalid_input": "Please enter a valid math problem or use the example.",
        "graph_error": "Could not draw the graph. Matplotlib may be unavailable.",
        "show_real_life": "Show Real Life View",
        "open_animation": "Open Animation",
        "open_folder": "Open Folder",
        "animation_created": "Animation created",
        "animation_created_at": "Animation saved to",
        "graph_saved_to": "Graph saved to",
        "anim_rendering": "Rendering...",
        "anim_failed": "Render failed",
        "anim_only_slope_intercept": "Animation is currently available for slope-intercept problems only.",
        "detected_type": "Detected: {ptype}",
        # Step labels
        "step_A": "A. What is given?",
        "step_B": "B. What do we need to find?",
        "step_C": "C. Formula / Concept",
        "step_D": "D. Substitute values",
        "step_E": "E. Solve",
        "step_F": "F. Final answer",
        "step_G": "G. Visual meaning",
        "step_H": "H. Real life meaning",
        # Problem type names
        "ptype_slope_intercept": "Slope-Intercept",
        "ptype_two_point": "Two-Point Line",
        "ptype_point_slope": "Point-Slope",
        "ptype_parallel": "Parallel Line",
        "ptype_perpendicular": "Perpendicular Line",
        "ptype_quadratic": "Quadratic Function",
        "ptype_system": "System of Equations",
        "ptype_trig_triangle": "Right Triangle Trigonometry",
        "ptype_unit_circle": "Unit Circle",
        "ptype_trig_wave": "Trigonometric Wave",
        "ptype_derivative": "Derivative / Tangent Line",
        "ptype_integral": "Integral / Area Under Curve",
        "ptype_vector": "Vectors",
        "ptype_unknown": "Unknown",
        # Newer UI strings
        "select_example": "Choose an example:",
        "explain_ai": "Explain with AI",
        "ai_thinking": "AI is thinking...",
        "ai_unavailable": "AI explanation is unavailable (LM Studio not reachable). The built-in explanation is shown instead.",
        "ai_done": "AI explanation ready.",
        "anim_not_for_type": "Animation is not implemented for this problem type yet.",
        "ctrl_a": "a:", "ctrl_b": "b:", "ctrl_c": "c:",
        "ctrl_amp": "Amplitude:", "ctrl_freq": "Frequency:", "ctrl_phase": "Phase:",
        "ctrl_x0": "x0:", "ctrl_lower": "Lower bound:", "ctrl_upper": "Upper bound:",
        "ctrl_n": "Rectangles (n):", "ctrl_method": "Riemann method:",
        "method_left": "Left", "method_right": "Right", "method_mid": "Midpoint",
    },
    "tr": {
        "question_input": "Soru / Problem",
        "load_example": "Örneği Yükle",
        "solve_visualize": "Çöz ve Görselleştir",
        "graph_panel": "Grafik",
        "save_graph": "Grafiği PNG olarak kaydet",
        "step_solution": "Adım Adım Çözüm",
        "real_life": "Gerçek Hayat Açıklaması",
        "controls": "Kontroller",
        "m_label": "Eğim (m):",
        "b_label": "Y-kesme noktası (b):",
        "reset_example": "Örneği Sıfırla",
        "create_animation": "Animasyon Oluştur",
        "manim_missing": "Manim kurulu değil. Kurmak için: pip install manim",
        "problem_not_supported": "Bu problem türü henüz desteklenmiyor.",
        "invalid_input": "Lütfen geçerli bir matematik problemi girin veya örneği kullanın.",
        "graph_error": "Grafik çizilemedi. Matplotlib kullanılamıyor olabilir.",
        "show_real_life": "Gerçek Hayat Görünümünü Göster",
        "open_animation": "Animasyonu Aç",
        "open_folder": "Klasörü Aç",
        "animation_created": "Animasyon oluşturuldu",
        "animation_created_at": "Animasyon kaydedildi",
        "graph_saved_to": "Grafik kaydedildi",
        "anim_rendering": "Render ediliyor...",
        "anim_failed": "Render hatası",
        "anim_only_slope_intercept": "Animasyon şu anda sadece eğim-kesme noktası soruları için kullanılabilir.",
        "detected_type": "Algılanan: {ptype}",
        "step_A": "A. Verilenler",
        "step_B": "B. Ne bulmamız gerekiyor?",
        "step_C": "C. Formül / Kavram",
        "step_D": "D. Değerleri yerine koy",
        "step_E": "E. Çöz",
        "step_F": "F. Son cevap",
        "step_G": "G. Grafikte anlamı",
        "step_H": "H. Gerçek hayattaki anlamı",
        "ptype_slope_intercept": "Eğim-Kesme Noktası",
        "ptype_two_point": "İki Noktadan Geçen Doğru",
        "ptype_point_slope": "Nokta-Eğim Formu",
        "ptype_parallel": "Paralel Doğru",
        "ptype_perpendicular": "Dik Doğru",
        "ptype_quadratic": "Parabol / İkinci Dereceden Fonksiyon",
        "ptype_system": "Denklem Sistemi",
        "ptype_trig_triangle": "Dik Üçgen Trigonometrisi",
        "ptype_unit_circle": "Birim Çember",
        "ptype_trig_wave": "Trigonometrik Dalga",
        "ptype_derivative": "Türev / Teğet Doğru",
        "ptype_integral": "İntegral / Eğri Altındaki Alan",
        "ptype_vector": "Vektörler",
        "ptype_unknown": "Bilinmiyor",
        # Newer UI strings
        "select_example": "Bir örnek seçin:",
        "explain_ai": "AI ile Açıkla",
        "ai_thinking": "AI düşünüyor...",
        "ai_unavailable": "AI açıklaması kullanılamıyor (LM Studio'ya ulaşılamadı). Bunun yerine yerleşik açıklama gösteriliyor.",
        "ai_done": "AI açıklaması hazır.",
        "anim_not_for_type": "Bu problem türü için animasyon henüz uygulanmadı.",
        "ctrl_a": "a:", "ctrl_b": "b:", "ctrl_c": "c:",
        "ctrl_amp": "Genlik:", "ctrl_freq": "Frekans:", "ctrl_phase": "Faz:",
        "ctrl_x0": "x0:", "ctrl_lower": "Alt sınır:", "ctrl_upper": "Üst sınır:",
        "ctrl_n": "Dikdörtgen (n):", "ctrl_method": "Riemann yöntemi:",
        "method_left": "Sol", "method_right": "Sağ", "method_mid": "Orta nokta",
    },
}


# ---------------------------------------------------------------------------
# Helper: pretty number formatter
# ---------------------------------------------------------------------------
def _fmt(val):
    if val is None:
        return "?"
    if isinstance(val, (list, tuple)):
        return val
    if val == int(val):
        return str(int(val))
    try:
        frac = Fraction(val).limit_denominator(1000)
        if abs(float(frac) - val) < 1e-9 and frac.denominator <= 20:
            return str(frac)
    except Exception:
        pass
    return f"{val:.3f}".rstrip("0").rstrip(".")


def normalize_extracted_math_text(text: str) -> str:
    """Clean common OCR artifacts while preserving math structure."""
    if not text:
        return ""
    cleaned = str(text)
    replacements = {
        "\u2212": "-", "\u2013": "-", "\u2014": "-", "\u2010": "-",
        "—": "-", "–": "-",
        "siope": "slope", "Siope": "Slope", "SlOpe": "Slope",
        "point-siope": "point-slope", "Point-siope": "Point-slope",
    }
    for src, dst in replacements.items():
        cleaned = cleaned.replace(src, dst)

    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\s*/\s*", "/", cleaned)
    cleaned = re.sub(r"\bm\s*=\s*-\s*(\d+(?:/\d+)?)", r"m = -\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bm\s*=\s*([+-]?\d+(?:/\d+)?)", r"m = \1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bb\s*=\s*([+-]?\d+(?:/\d+)?)", r"b = \1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(\s*([+-]?\d+(?:/\d+)?)\s*,\s*([+-]?\d+(?:/\d+)?)\s*\)", r"(\1, \2)", cleaned)
    cleaned = re.sub(r"\bpoint\s*(?=\()", "point = ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bpoint\s*=\s*\(\s*([+-]?\d+(?:/\d+)?)\s*,\s*([+-]?\d+(?:/\d+)?)\s*\)", r"point = (\1, \2)", cleaned, flags=re.IGNORECASE)

    # Simple OCR context fixes: l/I often become 1 in short math labels or fractions.
    cleaned = re.sub(r"(?<=/)[Il](?=\b)", "1", cleaned)
    cleaned = re.sub(r"\b([+-]?)[Il]\s*/\s*(\d+)\b", r"\g<1>1/\2", cleaned)
    cleaned = re.sub(r"\bm\s*=\s*-\s*[Il]\s*/\s*(\d+)\b", r"m = -1/\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bm\s*=\s*-\s*(\d+(?:/\d+)?)", r"m = -\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bm\s*=\s*([+-]?\d+(?:/\d+)?)", r"m = \1", cleaned, flags=re.IGNORECASE)

    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def extract_text_with_tesseract(image_path):
    """Return (text, status). Never raises if pytesseract or Tesseract is missing."""
    if not image_path:
        return "", "No image selected."
    if Image is None:
        return "", "Pillow is not available. You can type the problem manually."
    if pytesseract is None:
        return "", "pytesseract is not installed. You can type the problem manually."
    try:
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                pytesseract.pytesseract.tesseract_cmd = candidate
                break
        img = Image.open(image_path).convert("L")
        if min(img.size) < 900:
            img = img.resize((img.width * 2, img.height * 2))
        raw = pytesseract.image_to_string(img, config="--psm 6")
        text = normalize_extracted_math_text(raw)
        if text:
            return text, "OCR extracted text with Tesseract."
        return "", "OCR did not find readable text. You can type or correct the problem manually."
    except Exception as exc:
        return "", f"OCR unavailable. You can type the problem manually. ({exc.__class__.__name__}: {exc})"


def grab_clipboard_image():
    """Return (PIL image, message). Safe when clipboard has no image or Pillow is missing."""
    if ImageGrab is None:
        return None, "Clipboard image support requires Pillow ImageGrab."
    try:
        data = ImageGrab.grabclipboard()
        if data is None:
            return None, "No image found in clipboard."
        if Image is not None and isinstance(data, Image.Image):
            return data.convert("RGB"), ""
        if isinstance(data, list) and data:
            for item in data:
                try:
                    return Image.open(item).convert("RGB"), ""
                except Exception:
                    continue
        return None, "No image found in clipboard."
    except Exception as exc:
        return None, f"Could not read clipboard image: {exc}"


# ---------------------------------------------------------------------------
# Visual Math Engine
# ---------------------------------------------------------------------------
class VisualMathEngine:
    """Detects problem type and extracts parameters."""

    def __init__(self, text):
        self.text = text or ""
        self.problem_type = None
        self.params = {}
        self._detect()

    def _detect(self):
        txt = self.text
        if not txt:
            return

        # =====================================================================
        # Phase 4-7 specialized types are detected first because their patterns
        # are more specific than the generic linear-equation heuristics below.
        # Each block sets problem_type then validates with is_supported().
        # =====================================================================

        # --- system_of_equations: two or more linear y = ... equations ---
        lin_eqs = self._find_linear_equations(txt)
        if len(lin_eqs) >= 2 and not re.search(r"parallel|paralel|perpendicular|\bdik\b", txt, re.IGNORECASE):
            self.params = {"lines": lin_eqs[:2]}
            self.problem_type = "system_of_equations"
            if self.is_supported():
                return
            self.problem_type = None

        # --- derivative / tangent line (check before quadratic: f(x)=x^2 ...) ---
        if re.search(r"derivative|t[uü]rev|tangent|te[gğ]et|f\s*'", txt, re.IGNORECASE):
            self._extract_calculus()
            self.problem_type = "derivative"
            if self.is_supported():
                return
            self.problem_type = None

        # --- integral / area under curve (check before quadratic: area under x^2) ---
        if re.search(r"integral|area under|alt[ıi]nda|\balan|∫", txt, re.IGNORECASE):
            self._extract_calculus()
            self.problem_type = "integral"
            if self.is_supported():
                return
            self.problem_type = None

        # --- quadratic: single equation containing x^2 / parabola ---
        if re.search(r"x\s*\^\s*2|x\s*\*\*\s*2|x²|parabol|quadratic", txt, re.IGNORECASE):
            self._extract_quadratic()
            self.problem_type = "quadratic"
            if self.is_supported():
                return
            self.problem_type = None

        # --- unit circle (check before trig wave / triangle) ---
        if re.search(r"unit circle|birim [cç]ember", txt, re.IGNORECASE):
            self._extract_unit_circle()
            self.problem_type = "unit_circle"
            if self.is_supported():
                return
            self.problem_type = None

        # --- trigonometric wave: graph of sin/cos/tan ---
        if re.search(r"\b(sin|cos|tan)\s*\(", txt, re.IGNORECASE) and re.search(r"graph|[cç]iz|wave|dalga|y\s*=", txt, re.IGNORECASE):
            self._extract_trig_wave()
            self.problem_type = "trig_wave"
            if self.is_supported():
                return
            self.problem_type = None

        # --- right triangle trigonometry ---
        if re.search(r"opposite|adjacent|hypotenuse|kar[şs][ıi]|kom[şs]u|hipoten[uü]s|right triangle|dik [uü][cç]gen", txt, re.IGNORECASE):
            self._extract_triangle_trig()
            self.problem_type = "trig_triangle"
            if self.is_supported():
                return
            self.problem_type = None

        # --- basic vectors ---
        if re.search(r"vector|vekt[oö]r", txt, re.IGNORECASE):
            self._extract_vectors()
            self.problem_type = "vector_basic"
            if self.is_supported():
                return
            self.problem_type = None

        # --- slope_intercept ---
        has_si = bool(re.search(r"slope[-\s]?intercept|eğim[-\s]?kesme", txt, re.IGNORECASE))
        has_slope = bool(re.search(r"(?:slope|eğim)[\w]*\s+(?:of\s+|is\s+|=\s*)?-?\d", txt, re.IGNORECASE))
        has_m = bool(re.search(r"\bm\s*=\s*([\d/\-\.]+)", txt, re.IGNORECASE))
        has_b = bool(re.search(r"\b(?:b|y[-\s]?intercept|kesme)\s*(?:=|is)\s*([\d/\-\.]+)", txt, re.IGNORECASE))
        has_point = bool(re.search(r"\(\s*([\d/\-\.]+)\s*,\s*([\d/\-\.]+)\s*\)", txt, re.IGNORECASE))
        has_line = bool(re.search(r"(?:line|doğru|denklem)", txt, re.IGNORECASE))
        has_passing = bool(re.search(r"(?:pass(?:es|ing)?\s+through|geçen|noktasından\s+geçen)", txt, re.IGNORECASE))

        is_ps_kw = bool(re.search(r"point[-\s]?slope|nokta[-\s]?e[gğ]im", txt, re.IGNORECASE))
        if (not is_ps_kw) and (has_si or (has_slope and has_point) or (has_slope and has_b) or (has_m and has_b) or (has_line and has_passing and has_point)):
            self._extract_slope_intercept()
            self.problem_type = "slope_intercept"
            if self.is_supported():
                return
            self.problem_type = None

        # --- two_point_line ---
        points = re.findall(r"\(\s*([\d/\-\.]+)\s*,\s*([\d/\-\.]+)\s*\)", txt, re.IGNORECASE)
        if len(points) >= 2 and (has_line or bool(re.search(r"(?:through|passing|noktasından|noktaları)", txt, re.IGNORECASE))):
            try:
                p1 = (float(Fraction(points[0][0])), float(Fraction(points[0][1])))
                p2 = (float(Fraction(points[1][0])), float(Fraction(points[1][1])))
                self.params = {"p1": p1, "p2": p2}
                self.problem_type = "two_point_line"
                return
            except Exception:
                pass

        # --- point_slope ---
        if has_point and (has_slope or has_m) and (bool(re.search(r"point[-\s]?slope|nokta[-\s]?eğim", txt, re.IGNORECASE)) or (has_line and has_passing)):
            self._extract_slope_intercept()
            self.problem_type = "point_slope"
            if self.is_supported():
                return
            self.problem_type = None

        # --- parallel_line ---
        if bool(re.search(r"parallel|paralel", txt, re.IGNORECASE)) and has_line and has_point:
            self._extract_line_and_point()
            if self.params.get("orig_m") is not None and self.params.get("point") is not None:
                self.problem_type = "parallel_line"
                return

        # --- perpendicular_line ---
        if bool(re.search(r"perpendicular|dik", txt, re.IGNORECASE)) and has_line and has_point:
            self._extract_line_and_point()
            if self.params.get("orig_m") is not None and self.params.get("point") is not None:
                self.problem_type = "perpendicular_line"
                return

    def _extract_slope_intercept(self):
        txt = self.text
        m = None
        for pat in [r"(?:slope|eğim)[\w]*\s+of\s+([\d/\-\.]+)", r"(?:slope|eğim)[\w]*\s+(?:is|=)\s*([\d/\-\.]+)", r"(?:slope|eğim)[\w]*\s+(-?\d[\d/\.]*)", r"\bm\s*=\s*([\d/\-\.]+)"]:
            m_match = re.search(pat, txt, re.IGNORECASE)
            if m_match:
                try:
                    raw = m_match.group(1).strip()
                    if "/" in raw:
                        m = float(Fraction(re.sub(r"[^\d/\-]", "", raw)))
                    else:
                        m = float(re.sub(r"[^\d\-.]", "", raw))
                except Exception:
                    pass
                break
        b = None
        for pat in [r"(?:y[-\s]?intercept|kesme)\s+(?:is|=)\s*([\d/\-\.]+)", r"\bb\s*=\s*([\d/\-\.]+)"]:
            b_match = re.search(pat, txt, re.IGNORECASE)
            if b_match:
                try:
                    raw = b_match.group(1).strip()
                    if "/" in raw:
                        b = float(Fraction(re.sub(r"[^\d/\-]", "", raw)))
                    else:
                        b = float(re.sub(r"[^\d\-.]", "", raw))
                except Exception:
                    pass
                break
        point = None
        p_match = re.search(r"\(\s*([\d/\-\.]+)\s*,\s*([\d/\-\.]+)\s*\)", txt, re.IGNORECASE)
        if p_match:
            try:
                x = float(Fraction(p_match.group(1))) if "/" in p_match.group(1) else float(p_match.group(1))
                y = float(Fraction(p_match.group(2))) if "/" in p_match.group(2) else float(p_match.group(2))
                point = (x, y)
            except Exception:
                pass
        if m is not None and b is not None and point is None:
            point = (0.0, b)
        if m is not None and point is not None and b is None:
            b = point[1] - m * point[0]
        self.params = {"m": m, "b": b, "point": point}

    def _extract_line_and_point(self):
        txt = self.text
        # Extract original line equation y = mx + b
        orig_m = None
        orig_b = None
        line_match = re.search(r"y\s*=\s*([\d/\-\.]+)\s*x\s*([\+\-])\s*([\d/\-\.]+)", txt, re.IGNORECASE)
        if line_match:
            try:
                m_raw = line_match.group(1).strip()
                sign = -1 if line_match.group(2).strip() == "-" else 1
                b_raw = line_match.group(3).strip()
                orig_m = float(Fraction(m_raw)) if "/" in m_raw else float(m_raw)
                orig_b = sign * (float(Fraction(b_raw)) if "/" in b_raw else float(b_raw))
            except Exception:
                pass
        # Extract point
        point = None
        p_match = re.search(r"\(\s*([\d/\-\.]+)\s*,\s*([\d/\-\.]+)\s*\)", txt, re.IGNORECASE)
        if p_match:
            try:
                x = float(Fraction(p_match.group(1))) if "/" in p_match.group(1) else float(p_match.group(1))
                y = float(Fraction(p_match.group(2))) if "/" in p_match.group(2) else float(p_match.group(2))
                point = (x, y)
            except Exception:
                pass
        self.params = {"orig_m": orig_m, "orig_b": orig_b, "point": point}

    # ------------------------------------------------------------------ #
    # Phase 4-7 extraction helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _num(tok):
        tok = str(tok).replace(" ", "")
        if tok in ("", "+"):
            return 1.0
        if tok == "-":
            return -1.0
        try:
            return float(Fraction(tok)) if "/" in tok else float(tok)
        except Exception:
            return None

    def _find_linear_equations(self, txt):
        """Return a list of (m, b) for every 'y = m x + b' found in the text."""
        out = []
        pat = r"y\s*=\s*([+\-]?\s*\d*\.?\d*(?:/\d+)?)\s*\*?\s*x\s*([+\-])\s*(\d+\.?\d*(?:/\d+)?)"
        for mm in re.finditer(pat, txt, re.IGNORECASE):
            m = self._num(mm.group(1))
            b = self._num(mm.group(3))
            if m is None or b is None:
                continue
            if mm.group(2) == "-":
                b = -b
            out.append((m, b))
        return out

    @staticmethod
    def _extract_rhs(txt, var="y"):
        """Return the right-hand side expression string after 'var ='."""
        if var:
            m = re.search(rf"{var}\s*=\s*([^=]+)", txt, re.IGNORECASE)
        else:
            m = re.search(r"=\s*([^=]+)", txt)
        if not m:
            return None
        rhs = re.split(
            r"[.\n;]|\bfrom\b|\bat\b|\bfor\b|\bwhere\b|\band\b|\bve\b|\bile\b|parabol|e[ğg]ri|alt[ıi]nda|aras|fonksiyon",
            m.group(1), flags=re.IGNORECASE,
        )[0]
        return rhs.strip() or None

    def _extract_quadratic(self):
        txt = self.text
        expr = self._extract_rhs(txt, var="y") or self._extract_rhs(txt, var=None)
        a = b = c = None
        e = _sym_parse(expr)
        if e is not None and sp is not None:
            try:
                x = sp.Symbol("x")
                poly = sp.Poly(e, x)
                deg = poly.degree()
                coeffs = [float(v) for v in poly.all_coeffs()]
                if deg == 2:
                    a, b, c = coeffs
                elif deg == 1:
                    a, b, c = 0.0, coeffs[0], coeffs[1]
                elif deg == 0:
                    a, b, c = 0.0, 0.0, coeffs[0]
            except Exception:
                pass
        self.params = {"a": a, "b": b, "c": c, "expr": expr}

    def _extract_calculus(self):
        txt = self.text
        func = self._extract_rhs(txt, var=r"f\(x\)") or self._extract_rhs(txt, var="y")
        if func is None:
            m = re.search(
                r"(?:derivative of|t[uü]revi(?:ni)?|area under|alt[ıi]ndaki alan|integral of)\s+"
                r"([0-9xX\^\*\+\-\.\s/\(\)]+)", txt, re.IGNORECASE)
            if m:
                func = m.group(1).strip()
        x0 = None
        mm = re.search(r"x\s*=\s*(-?\d+\.?\d*(?:/\d+)?)", txt, re.IGNORECASE)
        if mm:
            x0 = self._num(mm.group(1))
        a = b = None
        bm = re.search(r"from\s*x?\s*=?\s*(-?\d+\.?\d*)\s*to\s*x?\s*=?\s*(-?\d+\.?\d*)", txt, re.IGNORECASE)
        if bm:
            a, b = self._num(bm.group(1)), self._num(bm.group(2))
        else:
            xeq = re.findall(r"x\s*=\s*(-?\d+\.?\d*)", txt, re.IGNORECASE)
            if len(xeq) >= 2:
                a, b = self._num(xeq[0]), self._num(xeq[1])
            else:
                bm2 = re.search(r"(-?\d+\.?\d*)\s*(?:ile|ve|to|,)\s*(-?\d+\.?\d*)\s*aras", txt, re.IGNORECASE)
                if bm2:
                    a, b = self._num(bm2.group(1)), self._num(bm2.group(2))
        self.params = {"func": func, "x0": x0, "a": a, "b": b}

    def _extract_unit_circle(self):
        angle = None
        m = re.search(r"(-?\d+\.?\d*)\s*(?:degree|degrees|derece|°)", self.text, re.IGNORECASE)
        if m:
            angle = self._num(m.group(1))
        self.params = {"angle": angle}

    def _extract_trig_wave(self):
        m = re.search(r"\b(sin|cos|tan)\b", self.text, re.IGNORECASE)
        fn = m.group(1).lower() if m else None
        self.params = {"trig_fn": fn, "amplitude": 1.0, "frequency": 1.0, "phase": 0.0}

    def _extract_triangle_trig(self):
        txt = self.text

        def grab(words):
            for w in words:
                m = re.search(rf"{w}[^\d]{{0,15}}(\d+\.?\d*)", txt, re.IGNORECASE)
                if m:
                    return self._num(m.group(1))
            return None

        self.params = {
            "opposite": grab(["opposite", "kar[şs][ıi]"]),
            "adjacent": grab(["adjacent", "kom[şs]u"]),
            "hyp": grab(["hypotenuse", "hipoten[uü]s"]),
        }

    def _extract_vectors(self):
        pts = re.findall(r"[\(<]\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*[\)>]", self.text)
        v1 = (self._num(pts[0][0]), self._num(pts[0][1])) if len(pts) >= 1 else None
        v2 = (self._num(pts[1][0]), self._num(pts[1][1])) if len(pts) >= 2 else None
        self.params = {"v1": v1, "v2": v2}

    def is_supported(self):
        if self.problem_type == "slope_intercept":
            return self.params.get("m") is not None and self.params.get("point") is not None
        if self.problem_type == "two_point_line":
            return len(self.params.get("p1", ())) == 2 and len(self.params.get("p2", ())) == 2
        if self.problem_type == "point_slope":
            return self.params.get("m") is not None and self.params.get("point") is not None
        if self.problem_type in ("parallel_line", "perpendicular_line"):
            return self.params.get("orig_m") is not None and self.params.get("point") is not None
        if self.problem_type == "quadratic":
            return self.params.get("a") is not None
        if self.problem_type == "system_of_equations":
            return len(self.params.get("lines", [])) >= 2
        if self.problem_type == "trig_triangle":
            vals = [self.params.get("opposite"), self.params.get("adjacent"), self.params.get("hyp")]
            return sum(v is not None for v in vals) >= 2
        if self.problem_type == "unit_circle":
            return self.params.get("angle") is not None
        if self.problem_type == "trig_wave":
            return self.params.get("trig_fn") is not None
        if self.problem_type == "derivative":
            return self.params.get("func") is not None
        if self.problem_type == "integral":
            return (self.params.get("func") is not None
                    and self.params.get("a") is not None
                    and self.params.get("b") is not None)
        if self.problem_type == "vector_basic":
            return self.params.get("v1") is not None
        return False


# ---------------------------------------------------------------------------
# Base Visualizer
# ---------------------------------------------------------------------------
class BaseVisualizer:
    """Common utilities for all linear equation visualizers."""

    @staticmethod
    def fmt(val):
        return _fmt(val)

    def get_graph_data(self, m, b, x_range=(-6, 10), num_points=400):
        if np is not None:
            xs = np.linspace(x_range[0], x_range[1], num_points)
            ys = m * xs + b
        else:
            xs = [x_range[0] + i * (x_range[1] - x_range[0]) / num_points for i in range(num_points)]
            ys = [m * x + b for x in xs]
        return xs, ys

    def get_slope_triangle(self, m, b):
        if m == 0:
            return None
        try:
            frac = Fraction(m).limit_denominator(20)
            rise = frac.numerator
            run = frac.denominator
        except Exception:
            rise, run = 1, int(1 / m) if m != 0 else (1, 1)
        x0, y0 = 0.0, b
        x1, y1 = x0 + run, y0 + rise
        return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "rise": rise, "run": run}

    def build_common_steps(self, lang, given, need, formula, substitute, solve, final_eq, visual, real):
        t = _VML_TEXT.get(lang, _VML_TEXT["en"])
        lines = [
            f"{t['step_A']}", f"   {given}",
            "",
            f"{t['step_B']}", f"   {need}",
            "",
            f"{t['step_C']}", f"   {formula}",
            "",
            f"{t['step_D']}", f"   {substitute}",
            "",
            f"{t['step_E']}", f"   {solve}",
            "",
            f"{t['step_F']}", f"   {final_eq}",
            "",
            f"{t['step_G']}", f"   {visual}",
            "",
            f"{t['step_H']}", f"   {real}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Slope-Intercept Visualizer
# ---------------------------------------------------------------------------
class SlopeInterceptVisualizer(BaseVisualizer):
    def __init__(self, m, point):
        self.m = float(m)
        self.point = tuple(float(v) for v in point)
        self.b = self.point[1] - self.m * self.point[0]
        self.equation_str = self._build_eq(self.m, self.b)

    @staticmethod
    def _build_eq(m, b):
        m_str = _fmt(m)
        b_str = _fmt(b)
        if abs(b) < 1e-9:
            return f"y = {m_str}x"
        sign = " + " if b >= 0 else " - "
        return f"y = {m_str}x{sign}{_fmt(abs(b))}"

    def build_steps(self, lang="en"):
        t = _VML_TEXT.get(lang, _VML_TEXT["en"])
        px, py = self.point
        m_str = self.fmt(self.m)
        b_str = self.fmt(self.b)
        given = f"m = {m_str}, point = ({px}, {py})"
        need = t["step_B"]
        formula = "y = m x + b"
        substitute = f"{py} = {m_str} * {px} + b"
        solve = f"b = {py} - {m_str} * {px} = {b_str}"
        final_eq = self.equation_str
        visual = f"Slope {m_str} means for every 1 unit right, the line changes {m_str} units vertically."
        real = "Think of a ramp: the starting height is the y-intercept, and the steepness is the slope."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        t = _VML_TEXT.get(lang, _VML_TEXT["en"])
        tri = self.get_slope_triangle(self.m, self.b)
        rise = abs(tri["rise"]) if tri else 1
        run = abs(tri["run"]) if tri else 1
        m_str = self.fmt(self.m)
        b_str = self.fmt(self.b)
        if lang == "tr":
            return "\n".join([
                "Bunu bir rampa veya düz bir yol gibi düşün.",
                f"Başlangıç yüksekliği {b_str} (y-kesme noktası).",
                f"Sağa doğru her {run} birim gittiğinde (yatay), {rise} birim yukarı çıkarsın (dikey).",
                f"Bu dikey/yatay oranı eğimdir ({m_str}); rampanın ne kadar dik olduğunu gösterir.",
            ])
        return "\n".join([
            "Imagine a ramp or a straight road.",
            f"The starting height is {b_str} (y-intercept).",
            f"For every {run} units you move to the right (run), you go up {rise} units (rise).",
            f"That rise-over-run ratio is the slope {m_str}, which tells you how steep the ramp is.",
        ])


# ---------------------------------------------------------------------------
# Two-Point Line Visualizer
# ---------------------------------------------------------------------------
class TwoPointLineVisualizer(BaseVisualizer):
    def __init__(self, p1, p2):
        self.p1 = tuple(float(v) for v in p1)
        self.p2 = tuple(float(v) for v in p2)
        self.m = (self.p2[1] - self.p1[1]) / (self.p2[0] - self.p1[0]) if self.p2[0] != self.p1[0] else 0
        self.b = self.p1[1] - self.m * self.p1[0]
        self.equation_str = SlopeInterceptVisualizer._build_eq(self.m, self.b)

    def build_steps(self, lang="en"):
        t = _VML_TEXT.get(lang, _VML_TEXT["en"])
        p1_str = f"({self.p1[0]}, {self.p1[1]})"
        p2_str = f"({self.p2[0]}, {self.p2[1]})"
        m_str = self.fmt(self.m)
        b_str = self.fmt(self.b)
        given = f"point1 = {p1_str}, point2 = {p2_str}"
        need = "Find the slope-intercept equation of the line through these two points."
        formula = "m = (y2 - y1) / (x2 - x1),  then b = y1 - m * x1"
        substitute = f"m = ({self.p2[1]} - {self.p1[1]}) / ({self.p2[0]} - {self.p1[0]}) = {m_str}"
        solve = f"b = {self.p1[1]} - {m_str} * {self.p1[0]} = {b_str}"
        final_eq = self.equation_str
        visual = f"The line passes through {p1_str} and {p2_str}. The slope {m_str} is the steepness between them."
        real = "Imagine two cities on a map. The straight road connecting them has a slope (steepness) and a starting elevation (y-intercept)."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        p1_str = f"({self.p1[0]}, {self.p1[1]})"
        p2_str = f"({self.p2[0]}, {self.p2[1]})"
        m_str = self.fmt(self.m)
        b_str = self.fmt(self.b)
        if lang == "tr":
            return "\n".join([
                "Bir yürüyüş parkurundaki iki noktayı düşün.",
                f"{p1_str} noktasından başla, {p2_str} noktasında bitir.",
                f"Parkurun eğimi {m_str}; yani her 1 birim ileri gidişte {m_str} birim yükselir.",
                f"Başlangıç yüksekliği {b_str}.",
            ])
        return "\n".join([
            "Imagine two points on a hiking trail.",
            f"Start at {p1_str} and end at {p2_str}.",
            f"The slope of the trail is {m_str}, meaning the trail rises {m_str} units for every 1 unit forward.",
            f"The starting height is {b_str}.",
        ])


# ---------------------------------------------------------------------------
# Point-Slope Visualizer
# ---------------------------------------------------------------------------
class PointSlopeVisualizer(BaseVisualizer):
    def __init__(self, m, point):
        self.m = float(m)
        self.point = tuple(float(v) for v in point)
        self.b = self.point[1] - self.m * self.point[0]
        self.point_slope_form = f"{self._lhs_y(self.point[1])} = {self.fmt(self.m)}({self._rhs_x(self.point[0])})"
        self.slope_intercept = SlopeInterceptVisualizer._build_eq(self.m, self.b)

    @classmethod
    def _signed_term(cls, var, value):
        value = float(value)
        if value < 0:
            return f"{var} + {cls.fmt(abs(value))}"
        return f"{var} - {cls.fmt(value)}"

    @classmethod
    def _lhs_y(cls, y0):
        return cls._signed_term("y", y0)

    @classmethod
    def _rhs_x(cls, x0):
        return cls._signed_term("x", x0)

    def build_steps(self, lang="en"):
        t = _VML_TEXT.get(lang, _VML_TEXT["en"])
        px, py = self.point
        m_str = self.fmt(self.m)
        b_str = self.fmt(self.b)
        given = f"m = {m_str}, point = ({self.fmt(px)}, {self.fmt(py)})"
        need = "Write point-slope form, then convert to slope-intercept form."
        formula = "y - y1 = m(x - x1)"
        substitute = self.point_slope_form
        solve = f"y = {m_str}x + {b_str}"
        final_eq = f"Point-slope: {self.point_slope_form}\nSlope-intercept: {self.slope_intercept}"
        visual = f"The point ({self.fmt(px)}, {self.fmt(py)}) is marked on the line. The slope {m_str} tells you the direction."
        real = "You know a starting location and the direction (slope). Point-slope gives the path; slope-intercept tells you where it starts."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        px, py = self.point
        m_str = self.fmt(self.m)
        if self.m < 0:
            frac = Fraction(self.m).limit_denominator(20)
            run = abs(frac.denominator)
            rise = abs(frac.numerator)
            if lang == "tr":
                return (
                    "Bu doğru sağa doğru gidildikçe aşağı iner. "
                    f"Eğim {m_str} olduğu için her {run} birim sağa gidildiğinde {rise} birim aşağı inilir."
                )
            return (
                "The line goes downward as you move to the right. "
                f"Since the slope is {m_str}, for every {run} units to the right, the line goes down {rise} unit{'s' if rise != 1 else ''}."
            )
        if lang == "tr":
            return "\n".join([
                "Bir tepenin üzerinde bir noktada duruyorsun.",
                f"Konumun ({px}, {py}).",
                f"Tepe her 1 birim ileride {m_str} eğimle yükseliyor.",
                "Nokta-eğim formu durduğun yerden gidişi anlatır; eğim-kesme formu tepenin genel şeklini söyler.",
            ])
        return "\n".join([
            "You are standing at a point on a hill.",
            f"Your location is ({px}, {py}).",
            f"The hill rises at a slope of {m_str} for every 1 unit forward.",
            "Point-slope tells you the path from where you stand; slope-intercept tells you the hill's overall shape."
        ])


# ---------------------------------------------------------------------------
# Parallel Line Visualizer
# ---------------------------------------------------------------------------
class ParallelLineVisualizer(BaseVisualizer):
    def __init__(self, orig_m, orig_b, point):
        self.orig_m = float(orig_m)
        self.orig_b = float(orig_b) if orig_b is not None else 0
        self.point = tuple(float(v) for v in point)
        self.new_m = self.orig_m
        self.new_b = self.point[1] - self.new_m * self.point[0]
        self.orig_eq = SlopeInterceptVisualizer._build_eq(self.orig_m, self.orig_b)
        self.new_eq = SlopeInterceptVisualizer._build_eq(self.new_m, self.new_b)

    def build_steps(self, lang="en"):
        t = _VML_TEXT.get(lang, _VML_TEXT["en"])
        px, py = self.point
        given = f"Original line: {self.orig_eq}, point = ({px}, {py})"
        need = "Find the line parallel to the original that passes through the given point."
        formula = "Parallel lines have the same slope: m_new = m_orig"
        substitute = f"m_new = {self.fmt(self.orig_m)}"
        solve = f"b_new = {py} - {self.fmt(self.new_m)} * {px} = {self.fmt(self.new_b)}"
        final_eq = f"Original: {self.orig_eq}\nParallel: {self.new_eq}"
        visual = f"Both lines have slope {self.fmt(self.orig_m)}. They never cross because they rise at the same rate."
        real = "Think of two train tracks side by side. They stay the same distance apart forever because they have the same slope."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "İki paralel yol asla kesişmez.",
                f"Bir yol {self.orig_eq}. Diğer yol {self.new_eq}.",
                "Aynı dikliğe sahipler, bu yüzden sonsuza dek aynı uzaklıkta kalırlar.",
            ])
        return "\n".join([
            "Two parallel roads never meet.",
            f"One road is {self.orig_eq}. The other road is {self.new_eq}.",
            "They have the same steepness, so they stay the same distance apart forever.",
        ])


# ---------------------------------------------------------------------------
# Perpendicular Line Visualizer
# ---------------------------------------------------------------------------
class PerpendicularLineVisualizer(BaseVisualizer):
    def __init__(self, orig_m, orig_b, point):
        self.orig_m = float(orig_m)
        self.orig_b = float(orig_b) if orig_b is not None else 0
        self.point = tuple(float(v) for v in point)
        self.new_m = -1 / self.orig_m if self.orig_m != 0 else 0
        self.new_b = self.point[1] - self.new_m * self.point[0]
        self.orig_eq = SlopeInterceptVisualizer._build_eq(self.orig_m, self.orig_b)
        self.new_eq = SlopeInterceptVisualizer._build_eq(self.new_m, self.new_b)

    def build_steps(self, lang="en"):
        t = _VML_TEXT.get(lang, _VML_TEXT["en"])
        px, py = self.point
        given = f"Original line: {self.orig_eq}, point = ({px}, {py})"
        need = "Find the line perpendicular to the original that passes through the given point."
        formula = "m_perp = -1 / m_orig"
        substitute = f"m_perp = -1 / {self.fmt(self.orig_m)} = {self.fmt(self.new_m)}"
        solve = f"b_perp = {py} - {self.fmt(self.new_m)} * {px} = {self.fmt(self.new_b)}"
        final_eq = f"Original: {self.orig_eq}\nPerpendicular: {self.new_eq}"
        visual = f"The two lines cross at a right angle. The slope flipped and became negative reciprocal: {self.fmt(self.new_m)}."
        real = "Think of a ladder leaning against a wall. The wall and floor are perpendicular. The ladder's slope is the negative reciprocal of the wall's slope."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "Bir duvara yaslanan merdiven, zeminle dik açı oluşturur.",
                f"Zemin orijinal doğru gibidir ({self.orig_eq}).",
                f"Merdiven dik doğru gibidir ({self.new_eq}).",
                "Eğimleri negatif terstir, bu yüzden 90°'de buluşurlar.",
            ])
        return "\n".join([
            "A ladder leaning against a wall forms a right angle with the ground.",
            f"The ground is like the original line ({self.orig_eq}).",
            f"The ladder is like the perpendicular line ({self.new_eq}).",
            f"Their slopes are negative reciprocals, so they meet at 90°."
        ])


# ---------------------------------------------------------------------------
# Manim Scene (slope-intercept only)
# ---------------------------------------------------------------------------
if MANIM_AVAILABLE:
    class SlopeInterceptScene(Scene):
        def __init__(self, viz, lang="en", **kwargs):
            self.viz = viz
            self.lang = lang
            super().__init__(**kwargs)

        def construct(self):
            t = _VML_TEXT.get(self.lang, _VML_TEXT["en"])
            m_str = self.viz.fmt(self.viz.m)
            b_str = self.viz.fmt(self.viz.b)
            px, py = self.viz.point
            title_text = "Slope-Intercept Form" if self.lang == "en" else "Eğim-Kesme Noktası Formu"
            title = Text(title_text, font_size=40)
            self.play(Write(title)); self.wait(1)
            self.play(title.animate.to_edge(UP).scale(0.6))
            form = Text("y = m x + b", font_size=36)
            self.play(Write(form)); self.wait(1); self.play(FadeOut(form))
            given_m = Text(f"m = {m_str}", font_size=30)
            given_p = Text(f"point = ({px}, {py})", font_size=30)
            given_group = VGroup(given_m, given_p).arrange(RIGHT, buff=1)
            self.play(Write(given_group)); self.wait(1); self.play(FadeOut(given_group))
            sub = Text(f"{py} = {m_str} * {px} + b", font_size=32)
            self.play(Write(sub)); self.wait(1)
            solved_b = Text(f"b = {b_str}", font_size=32)
            self.play(Transform(sub, solved_b)); self.wait(1); self.play(FadeOut(sub))
            final = Text(self.viz.equation_str, font_size=36)
            self.play(Write(final)); self.wait(1)
            self.play(final.animate.to_edge(UP).shift(DOWN * 0.3))
            axes = Axes(x_range=[-6, 10, 2], y_range=[-6, 6, 2], axis_config={"color": "#2f80ed"}, tips=False).scale(0.55).shift(DOWN * 0.3)
            self.play(Create(axes))
            line_graph = axes.plot(lambda x: self.viz.m * x + self.viz.b, x_range=[-6, 10], color="#C99A2E")
            self.play(Create(line_graph))
            p1 = Dot(axes.c2p(0, self.viz.b), color="#16A55A")
            p2 = Dot(axes.c2p(2, self.viz.m * 2 + self.viz.b), color="#8b5cf6")
            self.play(FadeIn(p1), FadeIn(p2))
            tri = self.viz.get_slope_triangle(self.viz.m, self.viz.b)
            if tri:
                x0, y0, x1, y1 = tri["x0"], tri["y0"], tri["x1"], tri["y1"]
                run_line = Line(axes.c2p(x0, y0), axes.c2p(x1, y0), color="#ef4444")
                rise_line = Line(axes.c2p(x1, y0), axes.c2p(x1, y1), color="#ef4444")
                self.play(Create(run_line), Create(rise_line))
            msg_text = t.get("anim_final_msg", "Every 2 units right, the line rises 1 unit.")
            msg = Text(msg_text, font_size=22).to_edge(DOWN)
            self.play(Write(msg)); self.wait(2)


# ---------------------------------------------------------------------------
# Visual Math Lab UI
# ---------------------------------------------------------------------------
class VisualMathLab(ttk.Frame):
    """Tkinter workspace for the Visual Math Engine."""

    EXAMPLES = {
        "en": {
            "slope_intercept": "Find the slope-intercept form of the line that passes through (0, -2) and has a slope of 1/2.",
            "two_point": "Find the equation of the line passing through (1, 2) and (5, 4).",
            "point_slope": "Write the point-slope form of the line with slope 3 passing through (2, 5).",
            "parallel": "Find the equation of the line parallel to y = 2x + 1 passing through (3, 4).",
            "perpendicular": "Find the equation of the line perpendicular to y = 2x + 1 passing through (3, 4).",
            "quadratic": "Graph y = x^2 - 4x + 3.",
            "system": "Solve and graph the system: y = 2x + 1 and y = -x + 4.",
            "trig_triangle": "Find sin, cos, and tan for a right triangle with opposite = 3, adjacent = 4, hypotenuse = 5.",
            "unit_circle": "Show sin and cos on the unit circle for 30 degrees.",
            "trig_wave": "Graph y = sin(x).",
            "derivative": "Find the derivative of f(x) = x^2 and show the tangent line at x = 2.",
            "integral": "Find the area under f(x) = x^2 from x = 0 to x = 2.",
            "vector": "Vectors v1 = (3, 4) and v2 = (1, 2). Find the magnitude and the sum.",
        },
        "tr": {
            "quadratic": "y = x^2 - 4x + 3 parabolünü çizin; tepe noktasını ve köklerini bulun.",
            "system": "y = 2x + 1 ve y = -x + 4 doğrularının kesişim noktasını bulun.",
            "trig_triangle": "Karşı kenar 3, komşu kenar 4, hipotenüs 5 ise sin, cos ve tan değerlerini bulun.",
            "unit_circle": "30 derece için birim çemberde sin ve cos değerlerini gösterin.",
            "trig_wave": "y = sin(x) grafiğini çizin.",
            "derivative": "f(x) = x^2 fonksiyonunun türevini bulun ve x = 2 noktasındaki teğeti gösterin.",
            "integral": "f(x) = x^2 eğrisi altında x = 0 ile x = 2 arasındaki alanı bulun.",
            "vector": "v1 = (3, 4) ve v2 = (1, 2) vektörleri. Büyüklüğü ve toplamı bulun.",
            "slope_intercept": "(0, -2) noktasından geçen ve eğimi 1/2 olan doğrunun denklemini bulun.",
            "two_point": "(1, 2) ve (5, 4) noktalarından geçen doğrunun denklemini bulun.",
            "point_slope": "Eğimi 3 olan ve (2, 5) noktasından geçen doğruyu nokta-eğim formunda yazın.",
            "parallel": "y = 2x + 1 doğrusuna paralel ve (3, 4) noktasından geçen doğruyu bulun.",
            "perpendicular": "y = 2x + 1 doğrusuna dik ve (3, 4) noktasından geçen doğruyu bulun.",
        },
    }

    # Ordered example selector entries: (display label, example key)
    EXAMPLE_MENU = [
        ("Phase 1: Slope + Point", "slope_intercept"),
        ("Phase 3: Two Points", "two_point"),
        ("Phase 3: Point-Slope", "point_slope"),
        ("Phase 3: Parallel Line", "parallel"),
        ("Phase 3: Perpendicular Line", "perpendicular"),
        ("Phase 4: Quadratic / Parabola", "quadratic"),
        ("Phase 4: System of Equations", "system"),
        ("Phase 5: Right Triangle Trig", "trig_triangle"),
        ("Phase 5: Unit Circle", "unit_circle"),
        ("Phase 5: Trig Wave (sin)", "trig_wave"),
        ("Phase 6: Derivative / Tangent", "derivative"),
        ("Phase 7: Integral / Area", "integral"),
    ]

    # Map detected problem_type -> example key (for the Reset Example button)
    _TYPE_TO_EXAMPLE = {
        "slope_intercept": "slope_intercept", "two_point_line": "two_point",
        "point_slope": "point_slope", "parallel_line": "parallel",
        "perpendicular_line": "perpendicular", "quadratic": "quadratic",
        "system_of_equations": "system", "trig_triangle": "trig_triangle",
        "unit_circle": "unit_circle", "trig_wave": "trig_wave",
        "derivative": "derivative", "integral": "integral", "vector_basic": "vector",
    }

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._lang = getattr(app, "language", "en")
        self._current_viz = None
        self._current_type = None
        self._figure = None
        self._canvas = None
        self._last_anim_path = None
        self._suspend_controls = False
        self._dyn_params = {}
        self.current_image_path = None
        # Course Simulation Library state
        self._sim_lib = None
        self._sim_records = []
        self._sim_combo = None
        self._sim_source_var = None
        self._sim_filter_var = None
        self._sim_search_var = None
        self._sim_status_var = tk.StringVar(value="")
        self._image_preview_photo = None
        self._extract_status_var = tk.StringVar(value="")
        # Formula Library state
        self._formula_records = []
        self._formula_combo = None
        self._formula_search_var = None
        self._formula_status_var = tk.StringVar(value="")
        self._build_ui()
        self._init_course_simulation_library()
        self._refresh_formula_list()

    def _t(self, key):
        return _VML_TEXT.get(self._lang, _VML_TEXT["en"]).get(key, key)

    def _ptype_name(self, ptype):
        key = f"ptype_{ptype}"
        return _VML_TEXT.get(self._lang, _VML_TEXT["en"]).get(key, ptype)

    def _build_ui(self):
        # Top professional command toolbar
        self._build_toolbar()

        # Resizable split layout:
        #   outer (horizontal): [ left work column | right graph column ]
        #   left  (vertical):   work area / library / step solution
        #   right (vertical):   interactive graph / real-life lesson card
        outer = ttk.PanedWindow(self, orient="horizontal")
        outer.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self._outer_paned = outer
        left_paned = ttk.PanedWindow(outer, orient="vertical")
        right_paned = ttk.PanedWindow(outer, orient="vertical")
        outer.add(left_paned, weight=2)
        outer.add(right_paned, weight=3)
        self._left_paned = left_paned
        self._right_paned = right_paned

        # ================= LEFT TOP: work area =================
        left_top = ttk.Frame(left_paned, style="Panel.TFrame")
        left_top.columnconfigure(0, weight=1)
        left_paned.add(left_top, weight=2)

        # Example selector
        sel_frame = ttk.Frame(left_top, style="Panel.TFrame")
        sel_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(sel_frame, text=self._t("load_example"), style="Header.TLabel").pack(anchor="w", padx=4, pady=(4, 2))
        ex_row = ttk.Frame(sel_frame)
        ex_row.pack(fill="x", padx=4, pady=2)
        self._example_map = {label: key for label, key in self.EXAMPLE_MENU}
        self._example_combo = ttk.Combobox(ex_row, state="readonly", width=32,
                                            values=[label for label, _ in self.EXAMPLE_MENU])
        self._example_combo.current(0)
        self._example_combo.pack(side="left", padx=2)
        self._example_combo.bind("<<ComboboxSelected>>", lambda e: self._load_selected_example())
        ttk.Button(ex_row, text=self._t("load_example"), command=self._load_selected_example).pack(side="left", padx=2)

        # Detected type label
        self._type_label_var = tk.StringVar(value="")
        tk.Label(sel_frame, textvariable=self._type_label_var, bg=BG, fg="#16A55A", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=4, pady=2)

        # Question input
        q_frame = ttk.Frame(left_top, style="Panel.TFrame")
        q_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self._input_tabs = ttk.Notebook(q_frame)
        self._input_tabs.pack(fill="x", expand=True, padx=4, pady=4)

        text_tab = ttk.Frame(self._input_tabs)
        self._input_tabs.add(text_tab, text="Text Question")
        ttk.Label(text_tab, text=self._t("question_input"), style="Header.TLabel").pack(anchor="w", padx=4, pady=(4, 2))
        self.question_text = tk.Text(text_tab, height=4, wrap="word", bg=PANEL_BG, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 10))
        self.question_text.pack(fill="x", expand=True, padx=4, pady=2)
        btn_row = ttk.Frame(text_tab)
        btn_row.pack(fill="x", padx=4, pady=4)
        ttk.Button(btn_row, text=self._t("solve_visualize"), command=self._solve_visualize).pack(side="left", padx=2)

        image_tab = ttk.Frame(self._input_tabs)
        self._image_tab = image_tab
        self._input_tabs.add(image_tab, text="Image Question")
        ttk.Label(image_tab, text="Image Question Input / Gorsel Soru Girisi", style="Header.TLabel").pack(anchor="w", padx=4, pady=(4, 2))
        img_btn_row = ttk.Frame(image_tab)
        img_btn_row.pack(fill="x", padx=4, pady=2)
        ttk.Button(img_btn_row, text="Load Image", command=self._load_image_question).pack(side="left", padx=2)
        ttk.Button(img_btn_row, text="Paste Screenshot", command=self._paste_screenshot).pack(side="left", padx=2)
        ttk.Button(img_btn_row, text="Extract Text", command=self._extract_image_text).pack(side="left", padx=2)
        ttk.Button(img_btn_row, text="Solve Image Question", command=self._solve_image_question).pack(side="left", padx=2)
        ttk.Button(img_btn_row, text="Clear Image", command=self._clear_image_question).pack(side="left", padx=2)
        preview_row = ttk.Frame(image_tab)
        preview_row.pack(fill="x", padx=4, pady=2)
        self.image_preview = tk.Label(preview_row, text="No image loaded.", bg=PANEL_BG, fg=AXIS, width=28, height=5)
        self.image_preview.pack(side="left", padx=(0, 6), pady=2)
        extracted_frame = ttk.Frame(preview_row)
        extracted_frame.pack(side="left", fill="both", expand=True)
        ttk.Label(extracted_frame, text="Extracted Text (editable)").pack(anchor="w")
        self.extracted_text = tk.Text(extracted_frame, height=5, wrap="word", bg=PANEL_BG, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 10))
        self.extracted_text.pack(fill="both", expand=True)
        tk.Label(image_tab, textvariable=self._extract_status_var, bg=BG, fg=AXIS, font=("Segoe UI", 9)).pack(anchor="w", padx=4, pady=(0, 4))
        image_tab.bind_all("<Control-v>", self._on_visual_math_paste, add="+")

        # Controls
        ctrl_frame = ttk.Frame(left_top, style="Panel.TFrame")
        ctrl_frame.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(ctrl_frame, text=self._t("controls"), style="Header.TLabel").pack(anchor="w", padx=4, pady=(4, 2))

        self.linear_ctrl_frame = ttk.Frame(ctrl_frame)
        self.linear_ctrl_frame.pack(fill="x")
        m_row = ttk.Frame(self.linear_ctrl_frame)
        m_row.pack(fill="x", padx=4, pady=2)
        ttk.Label(m_row, text=self._t("m_label")).pack(side="left")
        self.m_var = tk.StringVar(value="1/2")
        self.m_entry = ttk.Entry(m_row, textvariable=self.m_var, width=10)
        self.m_entry.pack(side="left", padx=4)
        self.m_slider = tk.Scale(m_row, from_=-5, to=5, resolution=0.1, orient="horizontal", command=self._on_slider_change, bg=BG, fg=FG, highlightthickness=0)
        self.m_slider.set(0.5)
        self.m_slider.pack(side="left", fill="x", expand=True, padx=4)

        b_row = ttk.Frame(self.linear_ctrl_frame)
        b_row.pack(fill="x", padx=4, pady=2)
        ttk.Label(b_row, text=self._t("b_label")).pack(side="left")
        self.b_var = tk.StringVar(value="-2")
        self.b_entry = ttk.Entry(b_row, textvariable=self.b_var, width=10)
        self.b_entry.pack(side="left", padx=4)
        self.b_slider = tk.Scale(b_row, from_=-10, to=10, resolution=0.5, orient="horizontal", command=self._on_slider_change, bg=BG, fg=FG, highlightthickness=0)
        self.b_slider.set(-2)
        self.b_slider.pack(side="left", fill="x", expand=True, padx=4)

        # Dynamic per-problem controls (populated for advanced problem types)
        self.dyn_controls = ttk.Frame(ctrl_frame)
        self.dyn_controls.pack(fill="x")
        self._dyn_widgets = []

        act_row = ttk.Frame(ctrl_frame)
        act_row.pack(fill="x", padx=4, pady=4)
        ttk.Button(act_row, text=self._t("reset_example"), command=self._reset_example).pack(side="left", padx=2)
        ttk.Button(act_row, text=self._t("explain_ai"), command=self._ai_explain).pack(side="left", padx=2)
        self.anim_button = ttk.Button(act_row, text=self._t("create_animation"), command=self._create_animation)
        self.anim_button.pack(side="left", padx=2)
        if not MANIM_AVAILABLE:
            self.anim_button.config(state="disabled")

        rl_row = ttk.Frame(ctrl_frame)
        rl_row.pack(fill="x", padx=4, pady=2)
        self._show_rl_var = tk.BooleanVar(value=False)
        tk.Checkbutton(rl_row, text=self._t("show_real_life"), variable=self._show_rl_var,
                       command=self._toggle_real_life, bg=BG, fg=FG,
                       selectcolor=BG, activebackground=BG, activeforeground=FG).pack(side="left")

        anim_row = ttk.Frame(ctrl_frame)
        anim_row.pack(fill="x", padx=4, pady=2)
        self._anim_status_var = tk.StringVar(value="")
        tk.Label(anim_row, textvariable=self._anim_status_var, bg=BG, fg=AXIS, font=("Segoe UI", 9)).pack(side="left")
        self._open_anim_button = ttk.Button(anim_row, text=self._t("open_animation"), command=self._open_animation, state="disabled")
        self._open_anim_button.pack(side="right", padx=2)
        self._open_folder_button = ttk.Button(anim_row, text=self._t("open_folder"), command=self._open_animations_folder, state="disabled")
        self._open_folder_button.pack(side="right", padx=2)

        self.m_var.trace_add("write", lambda *args: self._on_entry_change())
        self.b_var.trace_add("write", lambda *args: self._on_entry_change())

        # ================= LEFT MIDDLE: Course Simulation / Formula Library =================
        # Populated by _build_course_simulation_ui() into this resizable pane.
        self._sim_container = ttk.Frame(left_paned, style="Panel.TFrame")
        self._sim_container.columnconfigure(0, weight=1)
        self._sim_container.rowconfigure(0, weight=1)
        left_paned.add(self._sim_container, weight=3)

        # ================= LEFT BOTTOM: step-by-step solution =================
        step_frame = ttk.Frame(left_paned, style="Panel.TFrame")
        left_paned.add(step_frame, weight=2)
        shead = ttk.Frame(step_frame)
        shead.pack(fill="x")
        ttk.Label(shead, text=self._t("step_solution"), style="Header.TLabel").pack(side="left", anchor="w", padx=4, pady=(4, 2))
        ttk.Button(shead, text="Pop Out", width=9,
                   command=lambda: self._popout_text(self._t("step_solution"), self.step_text)).pack(side="right", padx=4, pady=2)
        self.step_text = tk.Text(step_frame, wrap="word", bg=PANEL_BG, fg=FG, insertbackground=FG, relief="flat", font=("Consolas", 10))
        self.step_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.step_text.config(state="disabled")

        # ================= RIGHT TOP: interactive graph =================
        graph_frame = ttk.Frame(right_paned, style="Panel.TFrame")
        right_paned.add(graph_frame, weight=3)
        ghead = ttk.Frame(graph_frame)
        ghead.pack(fill="x")
        ttk.Label(ghead, text=self._t("graph_panel"), style="Header.TLabel").pack(side="left", anchor="w", padx=4, pady=(4, 2))
        ttk.Button(ghead, text="Pop Out", width=9, command=self._popout_graph).pack(side="right", padx=2, pady=2)
        ttk.Button(ghead, text="Lesson Card", width=12, command=self._generate_lesson_card).pack(side="right", padx=2, pady=2)
        ttk.Button(ghead, text=self._t("save_graph"), command=self._save_graph).pack(side="right", padx=2, pady=2)
        self.graph_container = ttk.Frame(graph_frame)
        self.graph_container.pack(fill="both", expand=True, padx=4, pady=4)

        # ================= RIGHT BOTTOM: real-life / lesson card =================
        life_frame = ttk.Frame(right_paned, style="Panel.TFrame")
        right_paned.add(life_frame, weight=2)
        lhead = ttk.Frame(life_frame)
        lhead.pack(fill="x")
        ttk.Label(lhead, text=self._t("real_life"), style="Header.TLabel").pack(side="left", anchor="w", padx=4, pady=(4, 2))
        ttk.Button(lhead, text="Pop Out", width=9,
                   command=lambda: self._popout_text(self._t("real_life"), self.life_text)).pack(side="right", padx=4, pady=2)
        self.life_text = tk.Text(life_frame, wrap="word", bg=PANEL_BG, fg=FG, insertbackground=FG, relief="flat", font=("Segoe UI", 10))
        self.life_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.life_text.config(state="disabled")

        # Apply a sensible default split once the panes have a real size.
        self.after(260, self._apply_default_layout)

    def _load_example(self, key):
        ex = self.EXAMPLES.get(self._lang, self.EXAMPLES["en"]).get(key, "")
        self.question_text.delete("1.0", "end")
        self.question_text.insert("1.0", ex)
        self._solve_visualize()

    def _load_selected_example(self):
        key = self._example_map.get(self._example_combo.get())
        if key:
            self._load_example(key)

    # ------------------------------------------------------------------ #
    # Image question input
    # ------------------------------------------------------------------ #
    def _on_visual_math_paste(self, event=None):
        widget = self.focus_get()
        if isinstance(widget, (tk.Text, tk.Entry, ttk.Entry)):
            return None
        try:
            selected_tab = self.nametowidget(self._input_tabs.select())
        except Exception:
            selected_tab = None
        if selected_tab is self._image_tab and self._focus_inside_self():
            self._paste_screenshot()
            return "break"
        return None

    def _focus_inside_self(self):
        widget = self.focus_get()
        while widget is not None:
            if widget is self:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _load_image_question(self):
        path = filedialog.askopenfilename(
            title="Load Image / Gorsel Yukle",
            filetypes=[
                ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.load_image_question_path(path)

    def load_image_question_path(self, path):
        if Image is None or ImageTk is None:
            messagebox.showwarning("Visual Math Lab", "Pillow is required for image preview.")
            self.current_image_path = str(path)
            return
        try:
            img = Image.open(path).convert("RGB")
            self.current_image_path = str(path)
            self._show_image_preview(img)
            self._extract_status_var.set(f"Image loaded: {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Could not load image:\n{exc}")

    def _paste_screenshot(self):
        img, msg = grab_clipboard_image()
        if img is None:
            self._extract_status_var.set(f"{msg} / Panoda gorsel bulunamadi.")
            messagebox.showinfo("Visual Math Lab", f"{msg}\nPanoda gorsel bulunamadi.")
            return
        try:
            IMAGE_QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
            name = f"image_question_clipboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = IMAGE_QUESTIONS_DIR / name
            img.save(path)
            self.current_image_path = str(path)
            self._show_image_preview(img)
            self._extract_status_var.set(f"Clipboard image saved: {path}")
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Could not save clipboard image:\n{exc}")

    def _show_image_preview(self, img):
        if ImageTk is None:
            self.image_preview.config(text="Image loaded. Preview requires Pillow.")
            return
        preview = img.copy()
        preview.thumbnail((220, 120))
        self._image_preview_photo = ImageTk.PhotoImage(preview)
        self.image_preview.config(image=self._image_preview_photo, text="")

    def _clear_image_question(self):
        self.current_image_path = None
        self._image_preview_photo = None
        self.image_preview.config(image="", text="No image loaded.")
        self.extracted_text.delete("1.0", "end")
        self._extract_status_var.set("")

    def _extract_image_text(self):
        if not self.current_image_path:
            messagebox.showwarning("Visual Math Lab", "Load or paste an image first.")
            return
        self._extract_status_var.set("Extracting text...")

        def task():
            text, status = self._extract_with_vision()
            if not text:
                text, status = extract_text_with_tesseract(self.current_image_path)
            text = normalize_extracted_math_text(text)
            if not text:
                status = status or "No OCR text was extracted. Type or correct the problem manually."
            self.after(0, lambda: self._finish_extract_text(text, status))

        threading.Thread(target=task, daemon=True).start()

    def _extract_with_vision(self):
        client = getattr(self.app, "client", None)
        if client is None or not hasattr(client, "complete_with_image"):
            return "", "LM Studio Vision is not connected; trying OCR/manual fallback."
        system = (
            "You are a math OCR and visual question extraction assistant.\n"
            "Read the image carefully and extract the math problem exactly.\n"
            "Preserve fractions, signs, parentheses, points, exponents, and equations.\n"
            "Return only the cleaned problem statement and given values.\n"
            "Do not solve unless explicitly asked.\n"
            "If the image contains a point-slope problem, write it in plain text clearly.\n\n"
            "Sen bir matematik OCR ve gorsel soru cikarma asistanisin.\n"
            "Gorseli dikkatle oku ve matematik sorusunu dogru sekilde cikar.\n"
            "Kesirleri, isaretleri, parantezleri, noktalari, usleri ve denklemleri koru.\n"
            "Sadece temizlenmis soru metnini ve verilen degerleri dondur.\n"
            "Acikca istenmedikce cozme.\n"
            "Gorsel point-slope sorusu iceriyorsa duz metin olarak acikca yaz."
        )
        prompt = "Extract the math question from this image. Return only the problem text and given values."
        try:
            text, _usage, finish = client.complete_with_image(system, prompt, self.current_image_path, max_tokens=600, timeout=120)
            if finish in ("no_vision_model", "vision_http_error", "vision_error", "error"):
                return "", f"LM Studio Vision unavailable ({finish}); trying OCR/manual fallback."
            return text, "LM Studio Vision extracted text."
        except Exception as exc:
            return "", f"LM Studio Vision unavailable; trying OCR/manual fallback. ({exc})"

    def _finish_extract_text(self, text, status):
        self.extracted_text.delete("1.0", "end")
        if text:
            self.extracted_text.insert("1.0", text)
        self._extract_status_var.set(status)
        if not text:
            messagebox.showinfo("Visual Math Lab", status)

    def _solve_image_question(self):
        raw = self.extracted_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("Visual Math Lab", "Extract text first, or type the problem in the editable extracted text box.")
            return
        raw = normalize_extracted_math_text(raw)
        self.extracted_text.delete("1.0", "end")
        self.extracted_text.insert("1.0", raw)
        self.question_text.delete("1.0", "end")
        self.question_text.insert("1.0", raw)
        self._solve_problem_text(raw)

    # ------------------------------------------------------------------ #
    # Dynamic per-problem controls
    # ------------------------------------------------------------------ #
    def _show_linear_controls(self, show):
        if show:
            if not self.linear_ctrl_frame.winfo_ismapped():
                self.linear_ctrl_frame.pack(fill="x", before=self.dyn_controls)
        else:
            self.linear_ctrl_frame.pack_forget()

    def _clear_dynamic_controls(self):
        for w in getattr(self, "_dyn_widgets", []):
            try:
                w.destroy()
            except Exception:
                pass
        self._dyn_widgets = []

    def _add_dyn_slider(self, label, key, frm, to, init, step):
        row = ttk.Frame(self.dyn_controls)
        row.pack(fill="x", padx=4, pady=1)
        self._dyn_widgets.append(row)
        ttk.Label(row, text=label, width=14).pack(side="left")
        self._dyn_params[key] = float(init)

        def on_change(v):
            try:
                self._dyn_params[key] = float(v)
            except Exception:
                return
            self._rebuild_dynamic_viz()

        s = tk.Scale(row, from_=frm, to=to, resolution=step, orient="horizontal",
                     command=on_change, bg=BG, fg=FG, highlightthickness=0)
        s.set(init)
        s.pack(side="left", fill="x", expand=True, padx=4)

    def _populate_dynamic_controls(self):
        self._clear_dynamic_controls()
        self._dyn_params = {}
        viz, t = self._current_viz, self._current_type
        if t == "quadratic":
            self._add_dyn_slider(self._t("ctrl_a"), "a", -5, 5, viz.a, 0.5)
            self._add_dyn_slider(self._t("ctrl_b"), "b", -10, 10, viz.b, 0.5)
            self._add_dyn_slider(self._t("ctrl_c"), "c", -10, 10, viz.c, 0.5)
        elif t == "trig_wave":
            self._add_dyn_slider(self._t("ctrl_amp"), "A", 0.1, 5, viz.A, 0.1)
            self._add_dyn_slider(self._t("ctrl_freq"), "f", 0.25, 5, viz.f, 0.25)
            self._add_dyn_slider(self._t("ctrl_phase"), "phase", -3.14, 3.14, viz.phase, 0.1)
        elif t == "derivative":
            self._add_dyn_slider(self._t("ctrl_x0"), "x0", -5, 5, viz.x0, 0.5)
        elif t == "integral":
            self._add_dyn_slider(self._t("ctrl_lower"), "a", -5, 5, viz.a, 0.5)
            self._add_dyn_slider(self._t("ctrl_upper"), "b", -5, 5, viz.b, 0.5)
            self._add_dyn_slider(self._t("ctrl_n"), "n", 1, 100, viz.n, 1)
        # system_of_equations, unit_circle, trig_triangle and vectors have no live sliders.

    def _rebuild_dynamic_viz(self):
        t, p = self._current_type, self._dyn_params
        try:
            if t == "quadratic":
                self._current_viz = QuadraticVisualizer(p["a"], p["b"], p["c"])
            elif t == "trig_wave":
                self._current_viz = TrigWaveVisualizer(self._current_viz.fn, p["A"], p["f"], p["phase"])
            elif t == "derivative":
                self._current_viz = DerivativeVisualizer(self._current_viz.func_str, p["x0"])
            elif t == "integral":
                lo, hi = p["a"], p["b"]
                if hi <= lo:
                    hi = lo + 1
                self._current_viz = IntegralVisualizer(self._current_viz.func_str, lo, hi,
                                                       int(p["n"]), self._current_viz.method)
            else:
                return
        except Exception:
            return
        self._draw_graph()
        self._update_text_panels()

    # ------------------------------------------------------------------ #
    # Optional AI enrichment (deterministic solver first, AI second)
    # ------------------------------------------------------------------ #
    def _ai_explain(self):
        if self._current_viz is None:
            messagebox.showwarning("Visual Math Lab", self._t("invalid_input"))
            return
        client = getattr(self.app, "client", None)
        if client is None:
            messagebox.showinfo("Visual Math Lab", self._t("ai_unavailable"))
            return
        self._set_text(self.life_text, self._t("ai_thinking"))
        question = self.question_text.get("1.0", "end").strip()
        steps = self._current_viz.build_steps(self._lang)
        lang = self._lang

        def task():
            try:
                if lang == "tr":
                    system = ("Sabırlı bir matematik öğretmeni gibi açıkla. Çözümü adım adım anlat. "
                              "Grafikteki anlamını ve gerçek hayattaki anlamını açıkla. "
                              "Başlangıç seviyesindeki öğrenciye uygun sade bir dil kullan.")
                else:
                    system = ("You are a patient math teacher. Explain the solution step by step. "
                              "Explain the visual meaning and real-life meaning. "
                              "Keep the explanation suitable for a beginner.")
                user = f"{question}\n\nDeterministic solution:\n{steps}"
                result = client.complete(system, user, profile="math")
                text = result[0] if isinstance(result, (tuple, list)) else str(result)
                self.after(0, lambda: self._set_text(self.life_text, text or ""))
            except Exception:
                self.after(0, self._ai_failed)

        threading.Thread(target=task, daemon=True).start()

    def _ai_failed(self):
        messagebox.showinfo("Visual Math Lab", self._t("ai_unavailable"))
        if self._current_viz is not None:
            self._set_text(self.life_text, self._current_viz.build_real_life(self._lang))

    def _solve_visualize(self):
        raw = self.question_text.get("1.0", "end").strip()
        self._solve_problem_text(raw)

    def _solve_problem_text(self, raw):
        if not raw:
            messagebox.showwarning("Visual Math Lab", self._t("invalid_input"))
            return

        engine = VisualMathEngine(raw)
        if not engine.is_supported():
            messagebox.showinfo("Visual Math Lab", self._t("problem_not_supported"))
            return

        self._current_type = engine.problem_type
        self._type_label_var.set(self._t("detected_type").format(ptype=self._ptype_name(self._current_type)))

        p = engine.params
        self._suspend_controls = True   # programmatic m/b .set() must not clobber state
        if self._current_type == "slope_intercept":
            self._current_viz = SlopeInterceptVisualizer(p["m"], p["point"])
            self.m_var.set(self._current_viz.fmt(self._current_viz.m)); self.m_slider.set(self._current_viz.m)
            self.b_var.set(self._current_viz.fmt(self._current_viz.b)); self.b_slider.set(self._current_viz.b)
        elif self._current_type == "two_point_line":
            self._current_viz = TwoPointLineVisualizer(p["p1"], p["p2"])
            self.m_var.set(self._current_viz.fmt(self._current_viz.m)); self.m_slider.set(self._current_viz.m)
            self.b_var.set(self._current_viz.fmt(self._current_viz.b)); self.b_slider.set(self._current_viz.b)
        elif self._current_type == "point_slope":
            self._current_viz = PointSlopeVisualizer(p["m"], p["point"])
            self.m_var.set(self._current_viz.fmt(self._current_viz.m)); self.m_slider.set(self._current_viz.m)
            self.b_var.set(self._current_viz.fmt(self._current_viz.b)); self.b_slider.set(self._current_viz.b)
        elif self._current_type == "parallel_line":
            self._current_viz = ParallelLineVisualizer(p["orig_m"], p.get("orig_b"), p["point"])
            self.m_var.set(self._current_viz.fmt(self._current_viz.new_m)); self.m_slider.set(self._current_viz.new_m)
            self.b_var.set(self._current_viz.fmt(self._current_viz.new_b)); self.b_slider.set(self._current_viz.new_b)
        elif self._current_type == "perpendicular_line":
            self._current_viz = PerpendicularLineVisualizer(p["orig_m"], p.get("orig_b"), p["point"])
            self.m_var.set(self._current_viz.fmt(self._current_viz.new_m)); self.m_slider.set(self._current_viz.new_m)
            self.b_var.set(self._current_viz.fmt(self._current_viz.new_b)); self.b_slider.set(self._current_viz.new_b)
        elif self._current_type == "quadratic":
            self._current_viz = QuadraticVisualizer(p["a"], p["b"], p["c"])
        elif self._current_type == "system_of_equations":
            self._current_viz = SystemOfEquationsVisualizer(p["lines"][0], p["lines"][1])
        elif self._current_type == "trig_triangle":
            self._current_viz = TriangleTrigVisualizer(p.get("opposite"), p.get("adjacent"), p.get("hyp"))
        elif self._current_type == "unit_circle":
            self._current_viz = UnitCircleVisualizer(p["angle"])
        elif self._current_type == "trig_wave":
            self._current_viz = TrigWaveVisualizer(p.get("trig_fn") or "sin")
        elif self._current_type == "derivative":
            self._current_viz = DerivativeVisualizer(p["func"], p.get("x0") or 0.0)
        elif self._current_type == "integral":
            self._current_viz = IntegralVisualizer(p["func"], p["a"], p["b"])
        elif self._current_type == "vector_basic":
            self._current_viz = VectorVisualizer(p.get("v1"), p.get("v2"))
        self._suspend_controls = False

        if self._current_type in ("slope_intercept", "two_point_line", "point_slope",
                                  "parallel_line", "perpendicular_line"):
            self._show_linear_controls(True)
            self._clear_dynamic_controls()
        else:
            self._show_linear_controls(False)
            self._populate_dynamic_controls()

        self._draw_graph()
        self._update_text_panels()

    def _reset_example(self):
        key = self._TYPE_TO_EXAMPLE.get(self._current_type)
        if key:
            self._load_example(key)

    def _toggle_real_life(self):
        if self._current_viz is not None:
            self._draw_graph()

    def _create_animation(self):
        if not MANIM_AVAILABLE:
            messagebox.showinfo("Visual Math Lab", self._t("manim_missing"))
            return
        scene_map = {
            "slope_intercept": SlopeInterceptScene,
            "quadratic": QuadraticScene,
            "derivative": DerivativeScene,
            "integral": IntegralScene,
            "unit_circle": UnitCircleScene,
        }
        scene_cls = scene_map.get(self._current_type)
        if scene_cls is None:
            messagebox.showinfo("Visual Math Lab", self._t("anim_not_for_type"))
            return
        if self._current_viz is None:
            messagebox.showwarning("Visual Math Lab", self._t("invalid_input"))
            return

        self._anim_status_var.set(self._t("anim_rendering"))
        self.anim_button.config(state="disabled")

        def render_task():
            try:
                from manim import config
                old_media = config.media_dir
                old_preview = config.preview
                old_quality = config.quality
                config.media_dir = str(ANIMATIONS_DIR)
                config.preview = False
                config.quality = "low_quality"
                scene = scene_cls(self._current_viz, self._lang)
                scene.render()
                mp4_files = list(ANIMATIONS_DIR.rglob("*.mp4"))
                if mp4_files:
                    mp4_path = max(mp4_files, key=lambda p: p.stat().st_mtime)
                    self._last_anim_path = str(mp4_path)
                    self.after(0, self._animation_finished, True, str(mp4_path))
                else:
                    self.after(0, self._animation_finished, False, "No MP4 file found")
            except Exception as exc:
                self.after(0, self._animation_finished, False, str(exc))
            finally:
                try:
                    config.media_dir = old_media
                    config.preview = old_preview
                    config.quality = old_quality
                except Exception:
                    pass

        t = threading.Thread(target=render_task, daemon=True)
        t.start()

    def _animation_finished(self, success, info):
        self.anim_button.config(state="normal" if MANIM_AVAILABLE else "disabled")
        if success:
            self._anim_status_var.set(self._t("animation_created"))
            self._open_anim_button.config(state="normal")
            self._open_folder_button.config(state="normal")
            messagebox.showinfo("Visual Math Lab", self._t("animation_created_at") + f"\n{info}")
        else:
            self._anim_status_var.set(self._t("anim_failed"))
            self._open_anim_button.config(state="disabled")
            messagebox.showerror("Visual Math Lab", f"Animation failed:\n{info}")

    def _open_animation(self):
        if self._last_anim_path and Path(self._last_anim_path).exists():
            try:
                os.startfile(self._last_anim_path)
            except Exception:
                messagebox.showerror("Visual Math Lab", f"Could not open:\n{self._last_anim_path}")
        else:
            messagebox.showwarning("Visual Math Lab", "No animation file found.")

    def _open_animations_folder(self):
        try:
            os.startfile(str(ANIMATIONS_DIR))
        except Exception:
            pass

    def _on_slider_change(self, _event=None):
        if getattr(self, "_suspend_controls", False):
            return
        try:
            m = float(self.m_slider.get())
        except Exception:
            return
        try:
            b = float(self.b_slider.get())
        except Exception:
            return
        self.m_var.set(_fmt(m))
        self.b_var.set(_fmt(b))
        self._draw_graph_from_controls()

    def _on_entry_change(self):
        if getattr(self, "_suspend_controls", False):
            return
        try:
            m_str = self.m_var.get().strip()
            m = float(Fraction(m_str)) if "/" in m_str else float(m_str)
            self.m_slider.set(m)
        except Exception:
            return
        try:
            b_str = self.b_var.get().strip()
            b = float(Fraction(b_str)) if "/" in b_str else float(b_str)
            self.b_slider.set(b)
        except Exception:
            return
        self._draw_graph_from_controls()

    def _draw_graph_from_controls(self):
        # The m/b controls only drive the linear families; ignore them when an
        # advanced (quadratic, trig, calculus, ...) visualizer is on screen.
        if self._current_type not in (None, "slope_intercept", "two_point_line",
                                      "point_slope", "parallel_line", "perpendicular_line"):
            return
        try:
            m_str = self.m_var.get().strip()
            m = float(Fraction(m_str)) if "/" in m_str else float(m_str)
            b_str = self.b_var.get().strip()
            b = float(Fraction(b_str)) if "/" in b_str else float(b_str)
        except Exception:
            return
        self._current_viz = SlopeInterceptVisualizer(m, (0, b))
        self._current_type = "slope_intercept"
        self._draw_graph()
        self._update_text_panels()

    def _update_text_panels(self):
        if self._current_viz is None:
            return
        self._set_text(self.step_text, self._current_viz.build_steps(self._lang))
        self._set_text(self.life_text, self._current_viz.build_real_life(self._lang))

    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def _draw_graph(self):
        if self._current_viz is None:
            return
        if Figure is None or FigureCanvasTkAgg is None:
            self._set_text(self.step_text, self._t("graph_error"))
            return

        # --- Phase 4-7 visualizers render themselves onto the figure ---
        if hasattr(self._current_viz, "render_figure"):
            for child in self.graph_container.winfo_children():
                child.destroy()
            try:
                fig = Figure(figsize=getattr(self._current_viz, "fig_size", (6.2, 5.6)), dpi=110, facecolor=BG)
                self._current_viz.render_figure(fig, lang=self._lang, real_life=self._show_rl_var.get())
            except Exception as exc:
                fig = Figure(figsize=(6, 5), dpi=110, facecolor=BG)
                ax = fig.add_subplot(111)
                ax.set_facecolor(BG)
                ax.text(0.5, 0.5, f"Graph error:\n{exc}", color="#C0392B",
                        ha="center", va="center", transform=ax.transAxes, wrap=True)
            self._figure = fig
            canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            self._canvas = canvas
            return

        for child in self.graph_container.winfo_children():
            child.destroy()

        show_rl = self._show_rl_var.get()

        if show_rl:
            fig = Figure(figsize=(6, 9.5), dpi=100, facecolor=BG)
            ax = fig.add_subplot(2, 1, 1)
            ax.set_facecolor(BG)
            ax2 = fig.add_subplot(2, 1, 2)
            ax2.set_facecolor(BG)
        else:
            fig = Figure(figsize=(6, 5.5), dpi=120, facecolor=BG)
            ax = fig.add_subplot(1, 1, 1)
            ax.set_facecolor(BG)
            ax2 = None

        viz = self._current_viz

        # Determine which lines to draw
        lines_to_draw = []
        if isinstance(viz, SlopeInterceptVisualizer):
            lines_to_draw = [(viz.m, viz.b, viz.equation_str, "#2f80ed", True)]
            points = [(0, viz.b), (2, viz.m * 2 + viz.b)]
            tri = viz.get_slope_triangle(viz.m, viz.b)
        elif isinstance(viz, TwoPointLineVisualizer):
            lines_to_draw = [(viz.m, viz.b, viz.equation_str, "#2f80ed", True)]
            points = [viz.p1, viz.p2]
            tri = viz.get_slope_triangle(viz.m, viz.b)
        elif isinstance(viz, PointSlopeVisualizer):
            lines_to_draw = [(viz.m, viz.b, viz.slope_intercept, "#2f80ed", True)]
            tri = viz.get_slope_triangle(viz.m, viz.b)
            if tri:
                points = [viz.point, (viz.point[0] + tri["run"], viz.point[1] + tri["rise"])]
            else:
                points = [viz.point]
        elif isinstance(viz, ParallelLineVisualizer):
            lines_to_draw = [
                (viz.orig_m, viz.orig_b, viz.orig_eq, "#555", False),
                (viz.new_m, viz.new_b, viz.new_eq, "#2f80ed", True),
            ]
            points = [viz.point]
            tri = viz.get_slope_triangle(viz.new_m, viz.new_b)
        elif isinstance(viz, PerpendicularLineVisualizer):
            lines_to_draw = [
                (viz.orig_m, viz.orig_b, viz.orig_eq, "#555", False),
                (viz.new_m, viz.new_b, viz.new_eq, "#2f80ed", True),
            ]
            points = [viz.point]
            tri = viz.get_slope_triangle(viz.new_m, viz.new_b)
        else:
            lines_to_draw = [(0, 0, "y = 0", "#2f80ed", True)]
            points = []
            tri = None

        # Draw coordinate graph (polished: auto-ranged, high-contrast, readable)
        ax.grid(True, color=GRID, linestyle="-", linewidth=0.6, zorder=0)
        ax.axhline(0, color=FG, linewidth=1.5, zorder=1)
        ax.axvline(0, color=FG, linewidth=1.5, zorder=1)

        # Auto-fit the view to the line's key points instead of a fixed window.
        primary = next((l for l in lines_to_draw if l[4]), lines_to_draw[0])
        pm, pb = primary[0], primary[1]
        interest = list(points) + [(0, pb)]
        if abs(pm) > 1e-9:
            interest.append((-pb / pm, 0))
        if tri and len(lines_to_draw) == 1:
            interest.append((tri["x1"], tri["y1"]))
        xs_i = [p[0] for p in interest] + [0]
        ys_i = [p[1] for p in interest] + [0]
        xpad = max(3.0, (max(xs_i) - min(xs_i)) * 0.4)
        ypad = max(3.0, (max(ys_i) - min(ys_i)) * 0.4)
        xlo, xhi = min(xs_i) - xpad, max(xs_i) + xpad
        ylo, yhi = min(ys_i) - ypad, max(ys_i) + ypad

        for m, b, eq, color, show_label in lines_to_draw:
            xs, ys = viz.get_graph_data(m, b, x_range=(xlo, xhi))
            ax.plot(xs, ys, color=color, linewidth=3.0 if show_label else 2.0,
                    label=(eq if show_label else None), solid_capstyle="round",
                    alpha=1.0 if show_label else 0.6, zorder=4)

        if tri and len(lines_to_draw) == 1:
            x0, y0, x1, y1 = tri["x0"], tri["y0"], tri["x1"], tri["y1"]
            ax.plot([x0, x1], [y0, y0], color="#D86A5C", linewidth=2.0, linestyle=(0, (5, 3)), zorder=3)
            ax.plot([x1, x1], [y0, y1], color="#D86A5C", linewidth=2.0, linestyle=(0, (5, 3)), zorder=3)
            ax.annotate(f"run = {tri['run']}", xy=((x0 + x1) / 2, y0), color="#D86A5C",
                        fontsize=11, ha="center", va="top", fontweight="bold",
                        xytext=(0, -6), textcoords="offset points")
            ax.annotate(f"rise = {tri['rise']}", xy=(x1, (y0 + y1) / 2), color="#D86A5C",
                        fontsize=11, ha="left", va="center", fontweight="bold",
                        xytext=(6, 0), textcoords="offset points")

        for i, pt in enumerate(points):
            color = "#16A55A" if i == 0 else "#a78bfa"
            ax.scatter([pt[0]], [pt[1]], s=110, color=color, edgecolors="white",
                       linewidths=1.6, zorder=6)
            ax.annotate(f"({_fmt(pt[0])}, {_fmt(pt[1])})", xy=pt, color=color, fontsize=11,
                        fontweight="bold", ha="left", va="bottom",
                        xytext=(8, 7), textcoords="offset points", zorder=7)

        if isinstance(viz, PerpendicularLineVisualizer):
            ax.scatter([viz.point[0]], [viz.point[1]], s=150, color="#C99A2E", marker="D",
                       edgecolors="white", linewidths=1.5, zorder=6)
            ax.annotate("Intersection", xy=viz.point, color="#C99A2E", fontsize=11,
                        fontweight="bold", ha="center", va="bottom",
                        xytext=(0, 10), textcoords="offset points")

        ax.set_xlabel("x", color=FG, fontsize=12)
        ax.set_ylabel("y", color=FG, fontsize=12, rotation=0, labelpad=12)
        ax.tick_params(colors=AXIS, labelsize=11)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        if any(l[4] for l in lines_to_draw):
            leg = ax.legend(loc="upper left", facecolor=PANEL_BG, edgecolor=GRID,
                            labelcolor=FG, fontsize=12, framealpha=0.95)
            leg.set_zorder(8)
        ax.set_xlim(xlo, xhi)
        ax.set_ylim(ylo, yhi)

        # Real Life ramp view
        if ax2 is not None:
            ax2.set_xlim(-1, 6)
            y_min = min(-3, viz.b - 1) if hasattr(viz, 'b') else -3
            y_max = max(3, viz.b + 3) if hasattr(viz, 'b') else 3
            ax2.set_ylim(y_min, y_max)
            ax2.grid(True, color=GRID, linestyle="--", linewidth=0.5)
            ax2.axhline(0, color="#555", linewidth=2)

            m_draw = getattr(viz, 'new_m', getattr(viz, 'm', 0.5))
            b_draw = getattr(viz, 'new_b', getattr(viz, 'b', -2))
            tri2 = viz.get_slope_triangle(m_draw, b_draw) if hasattr(viz, 'get_slope_triangle') else None
            if tri2:
                run, rise = tri2["run"], tri2["rise"]
                x_end = run
                y_end = b_draw + rise
            else:
                run, rise = 2, 1
                x_end = 2
                y_end = b_draw + 1

            ax2.plot([0, x_end], [b_draw, y_end], color="#2f80ed", linewidth=4)
            ax2.plot([0, x_end], [b_draw, b_draw], color="#ef4444", linewidth=1.5, linestyle="--")
            ax2.plot([x_end, x_end], [b_draw, y_end], color="#ef4444", linewidth=1.5, linestyle="--")
            ax2.annotate("", xy=(x_end, y_end), xytext=(0, b_draw),
                         arrowprops=dict(arrowstyle="->", color="#C99A2E", lw=2))
            ax2.annotate(f"Start height = {_fmt(b_draw)}", xy=(0, b_draw), color="#16A55A", fontsize=10, ha="center", va="bottom" if b_draw < 0 else "top")
            ax2.annotate(f"run = {run}", xy=(x_end / 2, b_draw), color="#ef4444", fontsize=10, ha="center", va="bottom")
            ax2.annotate(f"rise = {rise}", xy=(x_end, (b_draw + y_end) / 2), color="#ef4444", fontsize=10, ha="left", va="center")
            title_rl = "Ramp Representation" if self._lang == "en" else "Rampa Gösterimi"
            ax2.set_title(title_rl, color=FG, fontsize=11)
            ax2.set_xlabel("Horizontal distance / Yatay mesafe", color=AXIS)
            ax2.set_ylabel("Height / Yükseklik", color=AXIS)
            ax2.tick_params(colors=AXIS)
            for spine in ax2.spines.values():
                spine.set_color(GRID)

        fig.tight_layout()
        self._figure = fig

        canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas = canvas

    def _auto_filename(self):
        if self._current_viz is None:
            return "graph.png"
        slug = getattr(self._current_viz, "slug", None)
        if slug:
            return f"{slug}.png"
        eq = getattr(self._current_viz, 'equation_str', getattr(self._current_viz, 'new_eq', 'graph'))
        eq = eq.replace(" ", "_").replace("/", "_").replace("=", "_")
        ptype = self._current_type or "line"
        return f"{ptype}_{eq}.png"

    def _save_graph(self):
        if self._figure is None:
            messagebox.showwarning("Visual Math Lab", self._t("graph_error"))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            initialdir=str(GRAPHS_DIR),
            initialfile=self._auto_filename(),
        )
        if path:
            try:
                self._figure.savefig(path, facecolor=BG, dpi=150)
                messagebox.showinfo("Visual Math Lab", self._t("graph_saved_to") + f"\n{path}")
            except Exception as exc:
                messagebox.showerror("Visual Math Lab", f"Save failed:\n{exc}")

    # ------------------------------------------------------------------
    # Toolbar / commands / layout / pop-out
    # ------------------------------------------------------------------
    def _setup_commands(self):
        """Central command registry so toolbars/menus share one callback per
        action instead of duplicating button logic (duplicate-button cleanup)."""
        try:
            from command_registry import CommandRegistry
        except Exception:
            self._commands = None
            return None
        reg = CommandRegistry()
        reg.register_many([
            ("command.open_simulation_studio", "Open Simulation Studio", self._open_simulation_studio, {"group": "global"}),
            ("command.open_formula_library", "Open Formula Library", self._open_formula_studio, {"group": "global"}),
            ("command.workspace_manager", "Workspace Manager", self._open_workspace_manager, {"group": "global"}),
            ("command.new_question", "New", self._new_question, {"group": "vml"}),
            ("command.load_image", "Load Image", self._load_image_question, {"group": "vml"}),
            ("command.paste_screenshot", "Paste Screenshot", self._paste_screenshot, {"group": "vml"}),
            ("command.solve", "Solve", self._solve_visualize, {"group": "vml"}),
            ("command.visualize", "Visualize", self._visualize_current, {"group": "vml"}),
            ("command.generate_lesson_card", "Lesson Card", self._generate_lesson_card, {"group": "vml"}),
            ("command.export_png", "Export PNG", self._save_graph, {"group": "export"}),
            ("command.export_pdf", "Export PDF", self._export_pdf, {"group": "export"}),
            ("command.open_source_pdf", "Open Source PDF", self._open_simulation_pdf, {"group": "export"}),
            ("command.reset_layout", "Reset Layout", self._reset_layout, {"group": "layout"}),
            ("command.save_layout", "Save Layout", self._save_layout, {"group": "layout"}),
            ("command.settings", "Settings", self._open_settings, {"group": "global"}),
        ])
        self._commands = reg
        return reg

    def _build_toolbar(self):
        """Professional top command bar, built from the central command registry."""
        self._setup_commands()
        bar = ttk.Frame(self, style="Panel.TFrame")
        bar.pack(fill="x", padx=4, pady=(4, 2))
        left = ttk.Frame(bar)
        left.pack(side="left")
        right = ttk.Frame(bar)
        right.pack(side="right")
        if self._commands is not None:
            self._commands.build_toolbar(left, [
                "command.open_simulation_studio", "command.new_question",
                "command.load_image", "command.paste_screenshot",
                "command.solve", "command.visualize", "command.generate_lesson_card",
            ])
            self._commands.build_toolbar(right, [
                "command.workspace_manager", "command.settings", "command.reset_layout",
                "command.open_source_pdf", "command.export_pdf", "command.export_png",
            ], side="right")
        self._toolbar_status_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self._toolbar_status_var, bg=BG, fg="#E07B39",
                 font=("Segoe UI", 9)).pack(side="left", padx=10)

    # ------------------------------------------------------------------
    # Workspace docking integration
    # ------------------------------------------------------------------
    def _ensure_dock_manager(self):
        """Create (once) a WorkspaceDockingManager with the lab's panels
        registered as dockable views bound to the lab's live data."""
        mgr = getattr(self, "_dock_manager", None)
        if mgr is not None:
            return mgr
        try:
            from workspace_docking_manager import WorkspaceDockingManager, WorkspaceLayoutStore
        except Exception:
            self._dock_manager = None
            return None
        mgr = WorkspaceDockingManager(app=self.winfo_toplevel(),
                                      layout_store=WorkspaceLayoutStore(),
                                      commands=getattr(self, "_commands", None))
        mgr.register_panel("graph_panel", "Graph", self._make_graph_view, default_region="center")
        mgr.register_panel("step_solution_panel", "Step-by-step Solution", self._make_step_view, default_region="center")
        mgr.register_panel("real_life_panel", "Real-Life Explanation", self._make_life_view, default_region="center")
        mgr.register_panel("formula_library_panel", "Formula Library", self._make_formula_launcher, default_region="center")
        mgr.register_panel("simulation_studio_panel", "Simulation Studio", self._make_studio_launcher, default_region="center")
        mgr.register_panel("wacom_board_panel", "Tablet Çizim Tahtası", self._make_wacom_launcher, default_region="center")
        mgr.register_panel("language_dictionary_panel", "Language & Science Dictionary",
                           self._make_language_dict_launcher, default_region="center")
        self._dock_manager = mgr
        return mgr

    def _make_graph_view(self, parent):
        frame = ttk.Frame(parent)
        if self._figure is not None and FigureCanvasTkAgg is not None:
            try:
                out = GRAPHS_DIR / "_dock_graph.png"
                self._figure.savefig(str(out), facecolor=BG, dpi=130)
                from PIL import Image, ImageTk
                img = Image.open(str(out))
                img.thumbnail((900, 720))
                frame._photo = ImageTk.PhotoImage(img)
                tk.Label(frame, image=frame._photo, bg=BG).pack(fill="both", expand=True)
                return frame
            except Exception:
                pass
        tk.Label(frame, text="No graph yet — solve a problem first.",
                 bg=BG, fg=AXIS, font=("Segoe UI", 11)).pack(fill="both", expand=True)
        return frame

    def _make_text_view(self, parent, source_widget, empty_msg):
        frame = ttk.Frame(parent)
        txt = tk.Text(frame, wrap="word", bg=PANEL_BG, fg=FG,
                      relief="flat", font=("Consolas", 11))
        txt.pack(fill="both", expand=True)
        try:
            content = source_widget.get("1.0", "end").strip()
        except Exception:
            content = ""
        txt.insert("1.0", content or empty_msg)
        txt.config(state="disabled")
        return frame

    def _make_step_view(self, parent):
        return self._make_text_view(parent, self.step_text, "No solution yet.")

    def _make_life_view(self, parent):
        return self._make_text_view(parent, self.life_text, "No real-life explanation yet.")

    def _make_formula_launcher(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Formula Library", style="Header.TLabel").pack(anchor="w", padx=6, pady=6)
        ttk.Button(frame, text="Open Formula Library Window",
                   command=self._open_formula_studio).pack(anchor="w", padx=6, pady=4)
        return frame

    def _make_studio_launcher(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Simulation Studio", style="Header.TLabel").pack(anchor="w", padx=6, pady=6)
        ttk.Button(frame, text="Open Simulation Studio Window",
                   command=self._open_simulation_studio).pack(anchor="w", padx=6, pady=4)
        return frame

    def _make_wacom_launcher(self, parent):
        """Workspace Manager control for the Smart Wacom Board (which lives in
        the PDF Reader tab). Show/Hide here drive the real PDF-side toggle."""
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Akıllı Tablet Çizim Tahtası", style="Header.TLabel").pack(anchor="w", padx=6, pady=6)
        pv = getattr(self.app, "pdf_viewer", None)
        if pv is not None and hasattr(pv, "set_wacom_visible"):
            ttk.Button(frame, text="Tablet Çizimini Göster (PDF Okuyucu)",
                       command=lambda: pv.set_wacom_visible(True)).pack(anchor="w", padx=6, pady=2)
            ttk.Button(frame, text="Tablet Çizimini Gizle (PDF Okuyucu)",
                       command=lambda: pv.set_wacom_visible(False)).pack(anchor="w", padx=6, pady=2)
            ttk.Button(frame, text="Tablet Çizimi Ayrı Pencerede Aç",
                       command=pv.popout_wacom).pack(anchor="w", padx=6, pady=2)
        else:
            ttk.Label(frame, text="Tablet çizim tahtasını kullanmak için PDF Okuyucu sekmesini açın.",
                      foreground=AXIS).pack(anchor="w", padx=6, pady=2)
        return frame

    def _make_language_dict_launcher(self, parent):
        """Workspace Manager control for the Language & Science Dictionary."""
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Language & Science Dictionary", style="Header.TLabel").pack(anchor="w", padx=6, pady=6)
        app = self.app
        if hasattr(app, "open_dictionary_subtab"):
            ttk.Button(frame, text="Open Dictionary",
                       command=lambda: app.open_dictionary_subtab(0)).pack(anchor="w", padx=6, pady=2)
            ttk.Button(frame, text="Sentence Translation",
                       command=lambda: app.open_dictionary_subtab(1)).pack(anchor="w", padx=6, pady=2)
            ttk.Button(frame, text="Image Translation",
                       command=lambda: app.open_dictionary_subtab(2)).pack(anchor="w", padx=6, pady=2)
        else:
            ttk.Label(frame, text="Open the Dictionary tab to use the language assistant.",
                      foreground=AXIS).pack(anchor="w", padx=6, pady=2)
        return frame

    def _open_workspace_manager(self):
        """Open (or focus) the Workspace Manager window listing all dockable
        panels with show/hide/tab/pop-out/dock/reset + layout presets."""
        mgr = self._ensure_dock_manager()
        if mgr is None:
            messagebox.showinfo("Visual Math Lab", "Workspace manager module is unavailable.")
            return None
        win = getattr(self, "_workspace_manager_win", None)
        if win is not None:
            try:
                if win.winfo_exists():
                    win.deiconify()
                    win.lift()
                    win.focus_force()
                    win.refresh()
                    return win
            except Exception:
                pass
        try:
            from workspace_docking_manager import WorkspaceManagerWindow
            self._workspace_manager_win = WorkspaceManagerWindow(mgr, app=self.winfo_toplevel())
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Workspace Manager failed:\n{exc}")
            return None
        return self._workspace_manager_win

    def _set_status(self, msg):
        try:
            self._toolbar_status_var.set(msg)
        except Exception:
            pass

    def _new_question(self):
        try:
            self.question_text.delete("1.0", "end")
            self._input_tabs.select(0)
            self.question_text.focus_set()
            self._set_status("New question")
        except Exception:
            pass

    def _visualize_current(self):
        if self._current_viz is not None:
            self._draw_graph()
            self._update_text_panels()
        else:
            self._solve_visualize()

    def _generate_lesson_card(self):
        """Render a poster-quality Visual Lesson Card PNG for the current problem."""
        if self._current_viz is None:
            messagebox.showinfo("Visual Math Lab",
                                "Solve or load a problem first.\n"
                                "Önce bir problem çöz veya yükle.")
            return
        try:
            from visual_lesson_card import VisualLessonCardGenerator
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Lesson card module unavailable:\n{exc}")
            return
        try:
            gen = VisualLessonCardGenerator(lang=self._lang)
            title = None
            try:
                rec = self._selected_sim_record()
                if rec and rec.get("title"):
                    title = rec.get("title")
            except Exception:
                pass
            path = gen.generate_from_visualizer(self._current_viz, self._current_type,
                                                title=title, lang=self._lang)
            self._last_lesson_card = path
            self._set_status(f"Lesson card saved: {path}")
            try:
                os.startfile(path)
            except Exception:
                pass
            messagebox.showinfo("Visual Math Lab", f"Lesson card created:\n{path}")
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Lesson card failed:\n{exc}")

    def _export_pdf(self):
        if self._figure is None:
            messagebox.showwarning("Visual Math Lab", self._t("graph_error"))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")],
            initialdir=str(REPORTS_DIR),
            initialfile=self._auto_filename().replace(".png", ".pdf"))
        if path:
            try:
                self._figure.savefig(path, facecolor=BG)
                messagebox.showinfo("Visual Math Lab", f"PDF saved:\n{path}")
            except Exception as exc:
                messagebox.showerror("Visual Math Lab", f"PDF export failed:\n{exc}")

    def _open_folder(self, path):
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            os.startfile(str(path))
        except Exception:
            pass

    # --- resizable layout: defaults, reset, save, load ---
    def _layout_file(self):
        return Path(EXPORTS_DIR).parent / "settings" / "visual_math_layout.json"

    def _apply_default_layout(self):
        if not self._load_layout():
            self._reset_layout(initial=True)

    def _reset_layout(self, initial=False):
        try:
            self.update_idletasks()
            ow = self._outer_paned.winfo_width()
            if ow > 120:
                self._outer_paned.sashpos(0, int(ow * 0.42))
            lh = self._left_paned.winfo_height()
            if lh > 150:
                self._left_paned.sashpos(0, int(lh * 0.32))
                self._left_paned.sashpos(1, int(lh * 0.70))
            rh = self._right_paned.winfo_height()
            if rh > 150:
                self._right_paned.sashpos(0, int(rh * 0.60))
            if not initial:
                self._set_status("Layout reset")
        except Exception:
            pass

    def _save_layout(self):
        try:
            import json
            self.update_idletasks()
            ow = max(1, self._outer_paned.winfo_width())
            lh = max(1, self._left_paned.winfo_height())
            rh = max(1, self._right_paned.winfo_height())
            data = {
                "outer": self._outer_paned.sashpos(0) / ow,
                "left0": self._left_paned.sashpos(0) / lh,
                "left1": self._left_paned.sashpos(1) / lh,
                "right0": self._right_paned.sashpos(0) / rh,
            }
            f = self._layout_file()
            f.parent.mkdir(parents=True, exist_ok=True)
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            self._set_status("Layout saved")
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Save layout failed:\n{exc}")

    def _load_layout(self):
        try:
            import json
            p = self._layout_file()
            if not p.exists():
                return False
            with open(p, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.update_idletasks()
            ow = self._outer_paned.winfo_width()
            lh = self._left_paned.winfo_height()
            rh = self._right_paned.winfo_height()
            if ow > 120 and "outer" in data:
                self._outer_paned.sashpos(0, int(ow * float(data["outer"])))
            if lh > 150:
                if "left0" in data:
                    self._left_paned.sashpos(0, int(lh * float(data["left0"])))
                if "left1" in data:
                    self._left_paned.sashpos(1, int(lh * float(data["left1"])))
            if rh > 150 and "right0" in data:
                self._right_paned.sashpos(0, int(rh * float(data["right0"])))
            return True
        except Exception:
            return False

    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title("Visual Math Lab — Settings")
        win.configure(bg=BG)
        win.geometry("340x300")
        ttk.Label(win, text="Layout", style="Header.TLabel").pack(anchor="w", padx=10, pady=(12, 2))
        ttk.Button(win, text="Save Layout", command=self._save_layout).pack(fill="x", padx=10, pady=2)
        ttk.Button(win, text="Reset Layout", command=self._reset_layout).pack(fill="x", padx=10, pady=2)
        ttk.Label(win, text="Folders", style="Header.TLabel").pack(anchor="w", padx=10, pady=(12, 2))
        ttk.Button(win, text="Open Lesson Cards Folder",
                   command=lambda: self._open_folder(EXPORTS_DIR / "lesson_cards")).pack(fill="x", padx=10, pady=2)
        ttk.Button(win, text="Open Exports Folder",
                   command=lambda: self._open_folder(EXPORTS_DIR)).pack(fill="x", padx=10, pady=2)
        tk.Label(win, text="Lesson card DPI: 200   |   Theme: dark",
                 bg=BG, fg=AXIS, font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(12, 4))
        ttk.Button(win, text="Close", command=win.destroy).pack(side="bottom", pady=10)

    # --- pop-out / detachable panels ---
    def _popout_graph(self):
        if self._figure is None:
            messagebox.showinfo("Visual Math Lab", "No graph to pop out yet.")
            return
        out = GRAPHS_DIR / "_popout_graph.png"
        try:
            self._figure.savefig(str(out), facecolor=BG, dpi=150)
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Pop out failed:\n{exc}")
            return
        try:
            from PIL import Image, ImageTk
        except Exception:
            try:
                os.startfile(str(out))
            except Exception:
                pass
            return
        win = tk.Toplevel(self)
        win.title("Graph — Visual Math Lab")
        win.configure(bg=BG)
        win.geometry("840x700")
        lbl = tk.Label(win, bg=BG)
        lbl.pack(fill="both", expand=True)
        state = {"img": Image.open(str(out)), "photo": None, "job": None}

        def render():
            w = max(200, lbl.winfo_width())
            h = max(200, lbl.winfo_height())
            im = state["img"].copy()
            im.thumbnail((w, h))
            state["photo"] = ImageTk.PhotoImage(im)
            lbl.config(image=state["photo"])

        def on_configure(_e=None):
            if state["job"] is not None:
                try:
                    win.after_cancel(state["job"])
                except Exception:
                    pass
            state["job"] = win.after(80, render)
        win.bind("<Configure>", on_configure)
        win.after(150, render)
        ttk.Button(win, text="Always on top",
                   command=lambda: win.attributes("-topmost", not win.attributes("-topmost"))).pack(side="bottom", pady=4)

    def _popout_text(self, title, source_widget):
        try:
            content = source_widget.get("1.0", "end")
        except Exception:
            content = ""
        win = tk.Toplevel(self)
        win.title(str(title))
        win.configure(bg=BG)
        win.geometry("560x520")
        txt = tk.Text(win, wrap="word", bg=PANEL_BG, fg=FG,
                      insertbackground=FG, relief="flat", font=("Consolas", 11))
        txt.pack(fill="both", expand=True, padx=6, pady=6)
        txt.insert("1.0", content)
        barf = ttk.Frame(win)
        barf.pack(fill="x")
        ttk.Button(barf, text="Refresh", command=lambda: (
            txt.delete("1.0", "end"), txt.insert("1.0", source_widget.get("1.0", "end")))).pack(side="left", padx=6, pady=4)
        ttk.Button(barf, text="Always on top",
                   command=lambda: win.attributes("-topmost", not win.attributes("-topmost"))).pack(side="left", padx=6, pady=4)
        ttk.Button(barf, text="Close", command=win.destroy).pack(side="right", padx=6, pady=4)

    # ------------------------------------------------------------------
    # Course Simulation Library UI
    # ------------------------------------------------------------------
    def _init_course_simulation_library(self):
        """Load embedded pack and build the simulation UI panel."""
        global _CSL, _EMB
        if _CSL is None:
            try:
                import course_simulation_library as _CSL_mod
                _CSL = _CSL_mod
            except Exception:
                _CSL = None
        if _EMB is None:
            try:
                import embedded_course_simulations as _EMB_mod
                _EMB = _EMB_mod
            except Exception:
                _EMB = None
        # The full library UI (Treeview + preview) now lives in the separate
        # Simulation Studio window, built lazily on first open. The main lab
        # only shows a compact launcher panel.
        self._sim_notebook = None
        self._sim_tree = None
        self._sim_preview = None
        self._sim_banner = None
        self._formula_tree = None
        self._formula_preview = None
        self._sim_list = []
        self._formula_list = []
        self._sim_selected_index = -1
        self._formula_selected_index = -1
        self._studio_window = None
        self._last_loaded_rec = None
        self._build_compact_library_panel()
        self._refresh_formula_list()
        self._refresh_simulation_list()

    def _build_compact_library_panel(self):
        """Compact launcher shown in the main lab; the full library (table,
        preview, big graph) lives in the separate Simulation Studio window."""
        parent = getattr(self, "_sim_container", None)
        if parent is None:
            return
        for child in parent.winfo_children():
            child.destroy()
        wrap = ttk.Frame(parent, style="Panel.TFrame")
        wrap.pack(fill="both", expand=True, padx=4, pady=4)
        ttk.Label(wrap, text="Simulation Studio / Simülasyon Stüdyosu",
                  style="Header.TLabel").pack(anchor="w", padx=4, pady=(4, 2))
        btns = ttk.Frame(wrap)
        btns.pack(fill="x", padx=4, pady=2)
        ttk.Button(btns, text="Open Simulation Studio",
                   command=self._open_simulation_studio).pack(side="left", padx=2)
        ttk.Button(btns, text="Open Formula Library",
                   command=self._open_formula_studio).pack(side="left", padx=2)
        ttk.Button(btns, text="Load Last Simulation",
                   command=self._load_last_simulation).pack(side="left", padx=2)
        self._compact_selected_var = tk.StringVar(value="Selected: (none)")
        tk.Label(wrap, textvariable=self._compact_selected_var, bg=BG, fg=FG,
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=6, pady=(6, 0))
        self._compact_counts_var = tk.StringVar(value="")
        tk.Label(wrap, textvariable=self._compact_counts_var, bg=BG, fg=AXIS,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=6, pady=(0, 2))
        tk.Label(wrap, text="Browse the full library, previews and big graphs in the Studio window.",
                 bg=BG, fg="#7f93a8", font=("Segoe UI", 9), anchor="w",
                 wraplength=380, justify="left").pack(fill="x", padx=6, pady=(2, 4))

    def _open_simulation_studio(self, initial_tab=0):
        """Open (or focus) the single shared Simulation Studio window."""
        win = getattr(self, "_studio_window", None)
        if win is not None:
            try:
                if win.winfo_exists():
                    win.deiconify()
                    win.lift()
                    win.focus_force()
                    if initial_tab:
                        win.select_tab(initial_tab)
                    return win
            except Exception:
                pass
        try:
            self._studio_window = SimulationStudioWindow(self, initial_tab=initial_tab)
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Could not open Simulation Studio:\n{exc}")
            return None
        return self._studio_window

    def _open_formula_studio(self):
        self._open_simulation_studio(initial_tab=1)

    def _load_last_simulation(self):
        rec = getattr(self, "_last_loaded_rec", None)
        if rec is None:
            lst = getattr(self, "_sim_list", [])
            rec = lst[0] if lst else None
        if rec is None:
            messagebox.showinfo("Visual Math Lab",
                                "No simulation has been loaded yet.\nHenüz simülasyon yüklenmedi.")
            return
        self.load_simulation_payload(rec)

    def _setup_vml_tree_style(self):
        """Dark Treeview style, scoped to this lab so other app tables are untouched."""
        try:
            style = ttk.Style()
            style.configure("VML.Treeview", background=PANEL_BG, fieldbackground=PANEL_BG,
                            foreground=FG, rowheight=20, font=("Segoe UI", 9))
            style.configure("VML.Treeview.Heading", background="#F6EFE4",
                            foreground=FG, font=("Segoe UI", 9, "bold"))
            style.map("VML.Treeview", background=[("selected", "#1d70b8")],
                      foreground=[("selected", "#ffffff")])
        except Exception:
            pass

    def _build_course_simulation_ui(self, parent):
        """Course Simulations + Formula Library tabs, built into `parent`
        (normally the Simulation Studio window body).

        Each tab pairs a multi-column browse Treeview with a rich, scrollable
        preview so the user immediately sees the FULL question, source PDF/page,
        problem type, status, solution and graph info for whatever is selected.
        """
        self._setup_vml_tree_style()
        self._sim_selected_index = -1
        self._formula_selected_index = -1
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        sim_frame = ttk.Frame(parent, style="Panel.TFrame")
        sim_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        sim_frame.columnconfigure(0, weight=1)
        sim_frame.rowconfigure(0, weight=1)

        sim_nb = ttk.Notebook(sim_frame)
        sim_nb.grid(row=0, column=0, sticky="nsew")
        self._sim_notebook = sim_nb

        # =============== Tab 1: Course Simulations ===============
        cs_tab = ttk.Frame(sim_nb)
        cs_tab.columnconfigure(0, weight=1)
        cs_tab.rowconfigure(1, weight=1)
        sim_nb.add(cs_tab, text="Course Simulations")

        filt = ttk.Frame(cs_tab)
        filt.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        ttk.Label(filt, text="Source:").pack(side="left", padx=(2, 1))
        self._sim_source_var = tk.StringVar(value="all")
        sc = ttk.Combobox(filt, state="readonly", width=10, textvariable=self._sim_source_var,
                          values=["all", "built_in", "embedded", "dynamic"])
        sc.pack(side="left", padx=2)
        sc.bind("<<ComboboxSelected>>", lambda e: self._refresh_simulation_list())
        ttk.Label(filt, text="Status:").pack(side="left", padx=(6, 1))
        self._sim_status_filter_var = tk.StringVar(value="all")
        st = ttk.Combobox(filt, state="readonly", width=13, textvariable=self._sim_status_filter_var,
                          values=["all", "ready", "needs_review", "unsupported", "error"])
        st.pack(side="left", padx=2)
        st.bind("<<ComboboxSelected>>", lambda e: self._refresh_simulation_list())
        ttk.Label(filt, text="Search:").pack(side="left", padx=(6, 1))
        self._sim_search_var = tk.StringVar(value="")
        se = ttk.Entry(filt, textvariable=self._sim_search_var, width=16)
        se.pack(side="left", padx=2)
        se.bind("<Return>", lambda e: self._refresh_simulation_list())
        ttk.Button(filt, text="Go", width=4, command=self._refresh_simulation_list).pack(side="left", padx=2)

        split = ttk.PanedWindow(cs_tab, orient="horizontal")
        split.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)

        left = ttk.Frame(split)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        cols = ("source", "course", "topic", "type", "title", "page", "status", "conf", "ver")
        self._sim_tree = ttk.Treeview(left, columns=cols, show="headings", height=7,
                                      style="VML.Treeview", selectmode="browse")
        headers = {"source": ("Src", 46), "course": ("Course", 95), "topic": ("Topic", 115),
                   "type": ("Type", 100), "title": ("Title", 240), "page": ("Pg", 38),
                   "status": ("Status", 86), "conf": ("Conf", 44), "ver": ("Ver", 34)}
        for c in cols:
            txt, w = headers[c]
            self._sim_tree.heading(c, text=txt)
            anchor = "w" if c in ("course", "topic", "type", "title") else "center"
            self._sim_tree.column(c, width=w, anchor=anchor, stretch=(c == "title"))
        self._sim_tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(left, orient="vertical", command=self._sim_tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._sim_tree.configure(yscrollcommand=sb.set)
        self._sim_tree.bind("<<TreeviewSelect>>", lambda e: self._on_sim_tree_select())
        self._sim_tree.bind("<Double-1>", lambda e: self._load_selected_simulation())
        self._sim_tree.tag_configure("needs_review", foreground="#C99A2E")
        self._sim_tree.tag_configure("unsupported", foreground="#C0392B")
        self._sim_tree.tag_configure("unverified", foreground="#C4632A")
        split.add(left, weight=3)

        right = ttk.Frame(split, style="Panel.TFrame")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        self._sim_banner = tk.Label(right, text="Select a simulation to preview / Onizlemek icin secin",
                                    bg=BG, fg=AXIS, font=("Segoe UI", 9, "bold"),
                                    anchor="w", padx=6, pady=3)
        self._sim_banner.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 0))
        self._sim_source_lbl_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self._sim_source_lbl_var, bg=BG, fg="#E07B39",
                 font=("Segoe UI", 9), anchor="w").grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=(1, 2))
        self._sim_preview = tk.Text(right, wrap="word", bg=PANEL_BG, fg=FG,
                                    insertbackground=FG, relief="flat", font=("Consolas", 9), height=12)
        self._sim_preview.grid(row=2, column=0, sticky="nsew", padx=(2, 0), pady=2)
        pvsb = ttk.Scrollbar(right, orient="vertical", command=self._sim_preview.yview)
        pvsb.grid(row=2, column=1, sticky="ns")
        self._sim_preview.configure(yscrollcommand=pvsb.set, state="disabled")
        self._sim_preview.tag_configure("h", foreground="#16A55A", font=("Consolas", 9, "bold"))
        self._sim_preview.tag_configure("q", foreground="#C99A2E", font=("Consolas", 10, "bold"))
        self._sim_preview.tag_configure("k", foreground=AXIS)
        sbtn = ttk.Frame(right)
        sbtn.grid(row=3, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 2))
        self._sim_load_btn = ttk.Button(sbtn, text="Load Simulation", command=self._load_selected_simulation)
        self._sim_load_btn.pack(side="left", padx=2)
        self._sim_pdf_btn = ttk.Button(sbtn, text="Open PDF", command=self._open_simulation_pdf)
        self._sim_pdf_btn.pack(side="left", padx=2)
        self._sim_graph_btn = ttk.Button(sbtn, text="Open Graph", command=self._open_simulation_graph)
        self._sim_graph_btn.pack(side="left", padx=2)
        ttk.Button(sbtn, text="Refresh", command=self._refresh_simulation_list).pack(side="left", padx=2)
        ttk.Button(sbtn, text="Scan PDFs", command=self._scan_course_pdfs).pack(side="left", padx=2)
        ttk.Button(sbtn, text="Rebuild", command=self._rebuild_dynamic_library).pack(side="left", padx=2)
        ttk.Button(sbtn, text="Validate Library", command=self._validate_library).pack(side="left", padx=2)
        split.add(right, weight=4)

        tk.Label(cs_tab, textvariable=self._sim_status_var, bg=BG, fg=AXIS,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", padx=4, pady=(0, 4))

        # =============== Tab 2: Formula Library ===============
        fl_tab = ttk.Frame(sim_nb)
        fl_tab.columnconfigure(0, weight=1)
        fl_tab.rowconfigure(1, weight=1)
        sim_nb.add(fl_tab, text="Formula Library")

        ffilt = ttk.Frame(fl_tab)
        ffilt.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 2))
        ttk.Label(ffilt, text="Course:").pack(side="left", padx=(2, 1))
        self._formula_course_var = tk.StringVar(value="all")
        fcc = ttk.Combobox(ffilt, state="readonly", width=13, textvariable=self._formula_course_var,
                           values=["all", "Pre-Algebra", "Algebra 1", "Geometry", "Linear Algebra", "Algebra 2"])
        fcc.pack(side="left", padx=2)
        fcc.bind("<<ComboboxSelected>>", lambda e: self._refresh_formula_list())
        ttk.Label(ffilt, text="Search:").pack(side="left", padx=(6, 1))
        self._formula_search_var = tk.StringVar(value="")
        fse = ttk.Entry(ffilt, textvariable=self._formula_search_var, width=16)
        fse.pack(side="left", padx=2)
        fse.bind("<Return>", lambda e: self._refresh_formula_list())
        ttk.Button(ffilt, text="Go", width=4, command=self._refresh_formula_list).pack(side="left", padx=2)

        fsplit = ttk.PanedWindow(fl_tab, orient="horizontal")
        fsplit.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)

        fleft = ttk.Frame(fsplit)
        fleft.columnconfigure(0, weight=1)
        fleft.rowconfigure(0, weight=1)
        fcols = ("course", "topic", "title", "visual", "page", "status")
        self._formula_tree = ttk.Treeview(fleft, columns=fcols, show="headings", height=7,
                                          style="VML.Treeview", selectmode="browse")
        fheaders = {"course": ("Course", 95), "topic": ("Topic", 130), "title": ("Title", 220),
                    "visual": ("Visual", 100), "page": ("Pg", 38), "status": ("Status", 80)}
        for c in fcols:
            txt, w = fheaders[c]
            self._formula_tree.heading(c, text=txt)
            anchor = "w" if c in ("course", "topic", "title", "visual") else "center"
            self._formula_tree.column(c, width=w, anchor=anchor, stretch=(c == "title"))
        self._formula_tree.grid(row=0, column=0, sticky="nsew")
        fsb = ttk.Scrollbar(fleft, orient="vertical", command=self._formula_tree.yview)
        fsb.grid(row=0, column=1, sticky="ns")
        self._formula_tree.configure(yscrollcommand=fsb.set)
        self._formula_tree.bind("<<TreeviewSelect>>", lambda e: self._on_formula_tree_select())
        self._formula_tree.bind("<Double-1>", lambda e: self._load_selected_formula())
        fsplit.add(fleft, weight=3)

        fright = ttk.Frame(fsplit, style="Panel.TFrame")
        fright.columnconfigure(0, weight=1)
        fright.rowconfigure(1, weight=1)
        self._formula_source_lbl_var = tk.StringVar(value="Select a formula to preview / Onizlemek icin secin")
        tk.Label(fright, textvariable=self._formula_source_lbl_var, bg=BG, fg="#E07B39",
                 font=("Segoe UI", 9), anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=(2, 2))
        self._formula_preview = tk.Text(fright, wrap="word", bg=PANEL_BG, fg=FG,
                                        insertbackground=FG, relief="flat", font=("Consolas", 9), height=12)
        self._formula_preview.grid(row=1, column=0, sticky="nsew", padx=(2, 0), pady=2)
        ffpvsb = ttk.Scrollbar(fright, orient="vertical", command=self._formula_preview.yview)
        ffpvsb.grid(row=1, column=1, sticky="ns")
        self._formula_preview.configure(yscrollcommand=ffpvsb.set, state="disabled")
        self._formula_preview.tag_configure("h", foreground="#16A55A", font=("Consolas", 9, "bold"))
        self._formula_preview.tag_configure("q", foreground="#C99A2E", font=("Consolas", 11, "bold"))
        self._formula_preview.tag_configure("k", foreground=AXIS)
        fbtn = ttk.Frame(fright)
        fbtn.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 2))
        ttk.Button(fbtn, text="Load Formula", command=self._load_selected_formula).pack(side="left", padx=2)
        ttk.Button(fbtn, text="Visualize Formula", command=self._visualize_formula).pack(side="left", padx=2)
        ttk.Button(fbtn, text="Copy Formula", command=self._copy_formula).pack(side="left", padx=2)
        ttk.Button(fbtn, text="Open Source PDF", command=self._open_formula_pdf).pack(side="left", padx=2)
        fsplit.add(fright, weight=4)

        tk.Label(fl_tab, textvariable=self._formula_status_var, bg=BG, fg=AXIS,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", padx=4, pady=(0, 4))

    def _set_rich(self, widget, segments):
        """Render a list of (text, tag) segments into a read-only Text widget."""
        widget.config(state="normal")
        widget.delete("1.0", "end")
        for text, tag in segments:
            if tag:
                widget.insert("end", text, tag)
            else:
                widget.insert("end", text)
        widget.config(state="disabled")
        widget.yview_moveto(0.0)

    def _refresh_simulation_list(self):
        """Rebuild the simulation table from built-in + embedded + dynamic records."""
        self._sim_records = []
        # 1. Built-in examples
        for label, key in self.EXAMPLE_MENU:
            txt = self.EXAMPLES.get(self._lang, self.EXAMPLES["en"]).get(key, "")
            if txt:
                self._sim_records.append({
                    "id": f"builtin_{key}", "source_type": "built_in", "title": label,
                    "course": "Visual Math Lab", "topic": "Built-in example",
                    "problem_type": key, "question_text": txt, "normalized_question": txt,
                    "status": "ready", "verified": True, "confidence": 1.0,
                    "graph_required": True, "source_pdf": "", "page_number": 0,
                })
        # 2. Embedded pack
        if _EMB is not None:
            for emb in getattr(_EMB, "EMBEDDED_COURSE_SIMULATIONS", []):
                self._sim_records.append(dict(emb))
        # 3. Dynamic cache (via CourseSimulationLibrary) — skip embedded to avoid dups
        if _CSL is not None:
            try:
                lib = _CSL.CourseSimulationLibrary()
                for rec in lib.all_simulations():
                    d = rec.to_dict()
                    if d.get("source_type") != "embedded":
                        self._sim_records.append(d)
            except Exception:
                pass
        # Filters: source + status + free-text search (filter widgets only exist
        # once the Studio window has been built; default gracefully before then).
        source = self._sim_source_var.get() if getattr(self, "_sim_source_var", None) else "all"
        sfilter = self._sim_status_filter_var.get() if getattr(self, "_sim_status_filter_var", None) else "all"
        query = (self._sim_search_var.get() or "").lower().strip() if getattr(self, "_sim_search_var", None) else ""
        filtered = []
        for r in self._sim_records:
            if source != "all" and r.get("source_type", "") != source:
                continue
            if sfilter != "all" and r.get("status", "") != sfilter:
                continue
            if query:
                hay = (f"{r.get('title','')} {r.get('normalized_question','')} "
                       f"{r.get('question_text','')} {r.get('source_pdf','')} "
                       f"{r.get('problem_type','')} {r.get('topic','')} "
                       f"page {r.get('page_number','')}").lower()
                if query not in hay:
                    continue
            filtered.append(r)
        self._sim_list = filtered
        tree = getattr(self, "_sim_tree", None)
        if tree is not None:
            tree.delete(*tree.get_children())
            for i, r in enumerate(filtered):
                src = (r.get("source_type", "?") or "?")[:3].upper()
                conf = r.get("confidence")
                conf_s = f"{float(conf):.2f}" if isinstance(conf, (int, float)) else "-"
                if r.get("source_type") == "built_in":
                    ver = "-"
                else:
                    ver = "Y" if r.get("verified") else "N"
                status = r.get("status", "")
                if status == "needs_review":
                    tags = ("needs_review",)
                elif status in ("unsupported", "error"):
                    tags = ("unsupported",)
                elif not r.get("source_verified", True):
                    tags = ("unverified",)
                else:
                    tags = ()
                vals = (src, r.get("course", ""), (r.get("topic") or r.get("section", "")),
                        r.get("problem_type", ""), r.get("title", "Untitled"),
                        r.get("page_number", 0), status, conf_s, ver)
                tree.insert("", "end", iid=str(i), values=vals, tags=tags)
            if filtered:
                tree.selection_set("0")
                tree.focus("0")
                self._sim_selected_index = 0
                self._update_sim_preview(filtered[0])
            else:
                self._sim_selected_index = -1
                self._update_sim_preview(None)
        self._sim_status_var.set(f"Simulations: {len(filtered)} shown / {len(self._sim_records)} total")
        if getattr(self, "_compact_counts_var", None) is not None:
            n_formula = len(getattr(self, "_formula_records", []) or [])
            self._compact_counts_var.set(f"{len(self._sim_records)} simulations  ·  {n_formula} formulas")

    def _on_sim_tree_select(self):
        if getattr(self, "_sim_tree", None) is None:
            return
        sel = self._sim_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except Exception:
            return
        if 0 <= idx < len(getattr(self, "_sim_list", [])):
            self._sim_selected_index = idx
            rec = self._sim_list[idx]
            self._update_sim_preview(rec)
            # Mirror the selection into the Studio's big graph pane, if open.
            studio = getattr(self, "_studio_window", None)
            if studio is not None:
                try:
                    if studio.winfo_exists():
                        studio.render_graph(rec)
                except Exception:
                    pass

    def _selected_sim_record(self):
        lst = getattr(self, "_sim_list", [])
        idx = getattr(self, "_sim_selected_index", -1)
        if 0 <= idx < len(lst):
            return lst[idx]
        sel = self._sim_tree.selection() if getattr(self, "_sim_tree", None) else ()
        if sel:
            try:
                i = int(sel[0])
                if 0 <= i < len(lst):
                    return lst[i]
            except Exception:
                pass
        return None

    def _update_sim_preview(self, rec):
        """Refresh banner, source label and the rich detail text for a record."""
        if getattr(self, "_sim_preview", None) is None or getattr(self, "_sim_banner", None) is None:
            return
        if not rec:
            self._sim_banner.config(text="Select a simulation to preview / Onizlemek icin secin",
                                    bg=BG, fg=AXIS)
            self._sim_source_lbl_var.set("")
            self._set_rich(self._sim_preview, [("", None)])
            return
        status = rec.get("status", "")
        verified = bool(rec.get("verified", False))
        src_ver = rec.get("source_verified", True)
        if status in ("unsupported", "error"):
            self._sim_banner.config(text="  This simulation is not supported / Bu simulasyon desteklenmiyor",
                                    bg="#5a1d1d", fg="#ffd6d6")
        elif status == "needs_review":
            self._sim_banner.config(text="  This simulation needs review. / Bu simulasyon kontrol gerektiriyor.",
                                    bg="#5a4a16", fg="#ffe9a8")
        elif not src_ver:
            self._sim_banner.config(text="  Ready, but source page is unverified / Hazir, kaynak sayfa dogrulanmadi",
                                    bg="#5a3d16", fg="#ffe1b0")
        elif verified:
            self._sim_banner.config(text="  Ready & verified / Hazir ve dogrulanmis", bg="#13402a", fg="#9ff0c2")
        else:
            self._sim_banner.config(text="  Ready / Hazir", bg="#13402a", fg="#9ff0c2")
        pdf = rec.get("source_pdf", "")
        page = rec.get("page_number", 0)
        if pdf:
            self._sim_source_lbl_var.set(f"Source: {pdf}  -  page {page}")
        elif rec.get("source_type") == "built_in":
            self._sim_source_lbl_var.set("Source: built-in example (no PDF)")
        else:
            self._sim_source_lbl_var.set("Source: (none)")
        self._set_rich(self._sim_preview, self._format_sim_preview(rec))

    def _format_sim_preview(self, rec):
        def g(k, d=""):
            v = rec.get(k, d)
            return d if v in (None, "") else v
        segs = [(f"{g('title', '(untitled)')}\n", "q"), ("\n", None)]

        def row(label, value):
            segs.append((f"{label}: ", "k"))
            segs.append((f"{value}\n", None))
        row("Source Type", g("source_type"))
        row("Course", g("course"))
        row("Topic", g("topic") or g("section"))
        row("Problem Type", g("problem_type"))
        row("Source PDF", g("source_pdf") or "(none)")
        row("Page Number", g("page_number", 0))
        row("Status", g("status"))
        conf = rec.get("confidence")
        row("Confidence", f"{float(conf):.2f}" if isinstance(conf, (int, float)) else "-")
        row("Verified", "yes" if rec.get("verified") else "no")
        row("Source Verified", "yes" if rec.get("source_verified", True) else "no")
        if rec.get("graph_required"):
            gs = "available (will be drawn on Load)"
        elif rec.get("graph_png_path"):
            gs = "available (saved image)"
        else:
            gs = "concept card - no graph"
        row("Graph", gs)
        if rec.get("review_reason"):
            row("Review reason", rec.get("review_reason"))
        segs.append(("\n", None))
        segs.append(("FULL QUESTION\n", "h"))
        segs.append((f"{g('question_text') or g('normalized_question')}\n\n", None))
        ans = g("answer") or g("alternate_answer")
        if ans:
            segs.append(("FINAL ANSWER\n", "h"))
            segs.append((f"{ans}\n\n", None))
        sol = g("solution_text")
        if sol:
            segs.append(("SOLUTION\n", "h"))
            segs.append((f"{sol}\n\n", None))
        rl = g("real_life_text") or g("explanation")
        rl_tr = g("real_life_text_tr")
        if self._lang == "tr" and rl_tr:
            rl = rl_tr
        if rl:
            segs.append(("REAL-LIFE MEANING\n", "h"))
            segs.append((f"{rl}\n", None))
        return segs

    def _load_selected_simulation(self):
        rec = self._selected_sim_record()
        if not rec:
            messagebox.showinfo("Visual Math Lab", "Select a simulation first.")
            return
        self.load_simulation_payload(rec)

    def load_simulation_payload(self, rec):
        """Load a simulation record into the main Visual Math Lab panels
        (question box, detected type, graph, step solution, real-life).
        Reusable by the Studio's 'Load to Visual Math Lab' button and the
        compact 'Load Last Simulation' button."""
        if not rec:
            return
        self._last_loaded_rec = rec
        if getattr(self, "_compact_selected_var", None) is not None:
            self._compact_selected_var.set(f"Selected: {rec.get('title', '(none)')}")
        src = rec.get("source_type", "")
        if src == "built_in":
            key = rec.get("problem_type", "")
            self._load_example(key)
            self._update_sim_preview(rec)
            self._sim_status_var.set(f"Loaded built-in: {rec.get('title','')}")
            return
        display_q = rec.get("question_text") or rec.get("normalized_question", "")
        solve_q = rec.get("normalized_question") or rec.get("question_text", "")
        # Always populate the question box so the user sees what is simulated.
        self.question_text.delete("1.0", "end")
        self.question_text.insert("1.0", display_q)
        drew = False
        if rec.get("graph_required"):
            try:
                engine = VisualMathEngine(solve_q)
                if engine.is_supported():
                    self._solve_problem_text(solve_q)  # draws graph, sets type + panels
                    drew = True
            except Exception:
                drew = False
        if not drew:
            # Concept card (or text parser could not detect it): no live graph.
            self._current_viz = None
            self._current_type = rec.get("problem_type")
            ptype = rec.get("problem_type", "concept")
            try:
                self._type_label_var.set(self._t("detected_type").format(ptype=self._ptype_name(ptype)))
            except Exception:
                self._type_label_var.set(f"Type: {ptype}")
            try:
                self._show_linear_controls(False)
                self._clear_dynamic_controls()
            except Exception:
                pass
            self._show_concept_graph(rec)
        # Override step + real-life panels with the record's curated text.
        sol = rec.get("solution_text", "")
        if sol:
            self._set_text(self.step_text, sol)
        rl = rec.get("real_life_text") or rec.get("explanation", "")
        rl_tr = rec.get("real_life_text_tr", "")
        if self._lang == "tr" and rl_tr:
            rl = rl_tr
        if rl:
            self._set_text(self.life_text, rl)
        self._update_sim_preview(rec)
        self._sim_status_var.set(f"Loaded: {rec.get('title','')}  [{rec.get('status','')}]")

    def _show_concept_graph(self, rec):
        """Show a saved PNG if present, else a friendly 'no graph' placeholder."""
        try:
            for child in self.graph_container.winfo_children():
                child.destroy()
        except Exception:
            return
        png = rec.get("graph_png_path")
        if png:
            p = Path(png)
            if not p.is_absolute():
                p = EXPORTS_DIR / png
            if p.exists():
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(str(p))
                    img.thumbnail((560, 460))
                    self._concept_graph_photo = ImageTk.PhotoImage(img)
                    tk.Label(self.graph_container, image=self._concept_graph_photo, bg=BG).pack(fill="both", expand=True)
                    return
                except Exception:
                    pass
        msg = ("This is a concept card - no graph is generated.\n"
               "Read the step-by-step solution and real-life panels.\n\n"
               "Bu bir kavram kartidir - grafik uretilmez.\n"
               "Asagidaki cozum ve gercek hayat panellerini okuyun.")
        tk.Label(self.graph_container, text=msg, bg=BG, fg=AXIS,
                 font=("Segoe UI", 10), justify="center").pack(fill="both", expand=True)
        self._figure = None

    def _scan_course_pdfs(self):
        if _CSL is None:
            messagebox.showwarning("Visual Math Lab", "Course simulation library module is not available.")
            return
        try:
            lib = _CSL.CourseSimulationLibrary()
            self._sim_status_var.set("Scanning PDFs in background...")

            def progress(msg):
                self.after(0, lambda: self._sim_status_var.set(msg))

            def done(ok, info):
                self.after(0, lambda: self._on_scan_done(ok, info))

            lib.scan_resources(progress_callback=progress, done_callback=done)
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Scan failed: {exc}")

    def _rebuild_dynamic_library(self):
        if _CSL is None:
            messagebox.showwarning("Visual Math Lab", "Course simulation library module is not available.")
            return
        if not messagebox.askyesno("Visual Math Lab", "Clear dynamic cache and rescan all PDFs? This may take a while."):
            return
        try:
            lib = _CSL.CourseSimulationLibrary()
            self._sim_status_var.set("Rebuilding library...")

            def progress(msg):
                self.after(0, lambda: self._sim_status_var.set(msg))

            def done(ok, info):
                self.after(0, lambda: self._on_scan_done(ok, info))

            lib.rebuild_dynamic(progress_callback=progress, done_callback=done)
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Rebuild failed: {exc}")

    def _on_scan_done(self, ok, info):
        if ok:
            self._refresh_simulation_list()
            messagebox.showinfo("Visual Math Lab", f"Scan complete.\n{info}")
        else:
            messagebox.showerror("Visual Math Lab", f"Scan failed:\n{info}")
        self._sim_status_var.set(info)

    def _resolve_pdf(self, pdf_rel):
        """Resolve a source_pdf reference to a real file (Resources, project
        root, or recursive search by file name)."""
        if not pdf_rel:
            return None
        for base in (RESOURCES_DIR, Path(__file__).resolve().parent):
            p = base / pdf_rel
            if p.exists():
                return p
        try:
            name = Path(pdf_rel).name
            hits = list(RESOURCES_DIR.rglob(name))
            if hits:
                return hits[0]
        except Exception:
            pass
        return None

    def _open_simulation_pdf(self):
        rec = self._selected_sim_record()
        if not rec:
            messagebox.showinfo("Visual Math Lab", "Select a simulation first.")
            return
        pdf_rel = rec.get("source_pdf", "")
        if not pdf_rel:
            messagebox.showinfo("Visual Math Lab", "No source PDF for this simulation (built-in example).")
            return
        pdf_path = self._resolve_pdf(pdf_rel)
        if pdf_path is None:
            messagebox.showwarning("Visual Math Lab", f"PDF not found:\n{pdf_rel}")
            return
        try:
            os.startfile(str(pdf_path))
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Could not open PDF:\n{exc}")

    def _open_simulation_graph(self):
        """Save the currently drawn graph and open it. Concept cards have none."""
        if self._figure is None:
            messagebox.showinfo("Visual Math Lab",
                                "No graph available for this item.\n"
                                "Concept cards do not generate a graph.")
            return
        try:
            out_dir = EXPORTS_DIR / "course_simulations" / "graphs"
            out_dir.mkdir(parents=True, exist_ok=True)
            rec = self._selected_sim_record() or {}
            slug = _slugify(rec.get("id") or rec.get("title") or "simulation")
            path = out_dir / f"{slug}.png"
            self._figure.savefig(str(path), facecolor=BG, dpi=150)
            os.startfile(str(path))
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Could not open graph:\n{exc}")

    def _validate_library(self):
        """Quick integrity report over the embedded simulation pack."""
        try:
            import embedded_course_simulations as emb
            sims = emb.EMBEDDED_COURSE_SIMULATIONS
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Cannot load embedded pack:\n{exc}")
            return
        total = len(sims)
        ready = sum(1 for r in sims if r.get("status") == "ready")
        needs = sum(1 for r in sims if r.get("status") == "needs_review")
        graphable = sum(1 for r in sims if r.get("graph_required"))
        unverified_src = sum(1 for r in sims if not r.get("source_verified", True))
        ids = [r.get("id") for r in sims]
        dups = sorted({i for i in ids if ids.count(i) > 1})
        empty_q = [r.get("id") for r in sims if not (r.get("question_text") or "").strip()]
        empty_sol = [r.get("id") for r in sims
                     if r.get("status") == "ready" and not (r.get("solution_text") or "").strip()]
        msg = (f"Embedded simulations: {total}\n"
               f"  ready: {ready}    needs_review: {needs}\n"
               f"  graphable: {graphable}    concept cards: {total - graphable}\n"
               f"  source unverified: {unverified_src}\n"
               f"  duplicate ids: {len(dups)}\n"
               f"  empty question_text: {len(empty_q)}\n"
               f"  empty solution_text (ready): {len(empty_sol)}\n")
        if dups or empty_q or empty_sol:
            if dups:
                msg += f"\n  dup ids: {', '.join(dups)}"
            if empty_q:
                msg += f"\n  empty Q: {', '.join(empty_q[:6])}"
            if empty_sol:
                msg += f"\n  empty sol: {', '.join(empty_sol[:6])}"
            messagebox.showwarning("Validate Library", msg)
        else:
            messagebox.showinfo("Validate Library", msg + "\nNo blocking issues. Library looks healthy.")
        self._set_status(f"Validate: {ready} ready / {needs} needs_review / {total} total")

    # --- Formula Library helpers ---
    def _refresh_formula_list(self):
        """Rebuild the formula table from embedded_formula_library."""
        self._formula_records = []
        try:
            import embedded_formula_library as flib
            for rec in getattr(flib, "EMBEDDED_FORMULA_LIBRARY", []):
                self._formula_records.append(dict(rec))
        except Exception:
            pass
        course = self._formula_course_var.get() if getattr(self, "_formula_course_var", None) else "all"
        query = (self._formula_search_var.get() or "").lower().strip() if getattr(self, "_formula_search_var", None) else ""
        filtered = []
        for r in self._formula_records:
            if course != "all" and r.get("course", "") != course:
                continue
            if query:
                hay = (f"{r.get('title','')} {r.get('topic','')} {r.get('formula_plain','')} "
                       f"{r.get('description','')} {r.get('example_question','')} "
                       f"{r.get('visual_type','')} page {r.get('page_number','')}").lower()
                if query not in hay:
                    continue
            filtered.append(r)
        self._formula_list = filtered
        tree = getattr(self, "_formula_tree", None)
        if tree is not None:
            tree.delete(*tree.get_children())
            for i, r in enumerate(filtered):
                vals = (r.get("course", ""), r.get("topic", ""), r.get("title", "Untitled"),
                        r.get("visual_type", ""), r.get("page_number", 0), r.get("status", ""))
                tree.insert("", "end", iid=str(i), values=vals)
            if filtered:
                tree.selection_set("0")
                tree.focus("0")
                self._formula_selected_index = 0
                self._update_formula_preview(filtered[0])
            else:
                self._formula_selected_index = -1
                self._update_formula_preview(None)
        self._formula_status_var.set(f"Formulas: {len(filtered)} shown / {len(self._formula_records)} total")

    def _on_formula_tree_select(self):
        if getattr(self, "_formula_tree", None) is None:
            return
        sel = self._formula_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except Exception:
            return
        if 0 <= idx < len(getattr(self, "_formula_list", [])):
            self._formula_selected_index = idx
            self._update_formula_preview(self._formula_list[idx])

    def _selected_formula_record(self):
        lst = getattr(self, "_formula_list", [])
        idx = getattr(self, "_formula_selected_index", -1)
        if 0 <= idx < len(lst):
            return lst[idx]
        sel = self._formula_tree.selection() if getattr(self, "_formula_tree", None) else ()
        if sel:
            try:
                i = int(sel[0])
                if 0 <= i < len(lst):
                    return lst[i]
            except Exception:
                pass
        return None

    def _update_formula_preview(self, rec):
        if getattr(self, "_formula_preview", None) is None:
            return
        if not rec:
            self._formula_source_lbl_var.set("Select a formula to preview / Onizlemek icin secin")
            self._set_rich(self._formula_preview, [("", None)])
            return
        pdf = rec.get("source_pdf", "")
        page = rec.get("page_number", 0)
        sup = "supported by Visual Math" if rec.get("supported_by_visual_math") else "concept card"
        self._formula_source_lbl_var.set(f"Source: {pdf or '(none)'}  -  page {page}   |   {sup}")
        self._set_rich(self._formula_preview, self._format_formula_preview(rec))

    def _format_formula_preview(self, rec):
        def g(k, d=""):
            v = rec.get(k, d)
            return d if v in (None, "") else v
        segs = [(f"{g('title', '(untitled)')}\n", "q"), ("\n", None)]

        def row(label, value):
            segs.append((f"{label}: ", "k"))
            segs.append((f"{value}\n", None))
        row("Course", g("course"))
        row("Topic", g("topic"))
        row("Visual Type", g("visual_type"))
        row("Source PDF", g("source_pdf") or "(none)")
        row("Page Number", g("page_number", 0))
        row("Status", g("status"))
        row("Supported by Visual Math", "yes" if rec.get("supported_by_visual_math") else "no")
        rel = rec.get("related_simulation_ids") or rec.get("related_simulations")
        if rel:
            row("Related simulations", ", ".join(rel) if isinstance(rel, (list, tuple)) else rel)
        segs.append(("\n", None))
        segs.append(("FORMULA\n", "h"))
        segs.append((f"{g('formula_plain') or g('formula_latex')}\n\n", None))
        if g("formula_latex"):
            segs.append(("LaTeX\n", "h"))
            segs.append((f"{g('formula_latex')}\n\n", None))
        if g("description"):
            segs.append(("DESCRIPTION\n", "h"))
            segs.append((f"{g('description')}\n\n", None))
        if g("example_question"):
            segs.append(("EXAMPLE QUESTION\n", "h"))
            segs.append((f"{g('example_question')}\n", None))
        return segs

    def _load_selected_formula(self):
        rec = self._selected_formula_record()
        if not rec:
            messagebox.showinfo("Visual Math Lab", "Select a formula first.")
            return
        q = rec.get("example_question") or rec.get("formula_plain", "")
        self.question_text.delete("1.0", "end")
        self.question_text.insert("1.0", q)
        self._update_formula_preview(rec)
        self._formula_status_var.set(f"Loaded: {rec.get('title','')} (edit & Solve, or use Visualize)")

    def _visualize_formula(self):
        rec = self._selected_formula_record()
        if not rec:
            messagebox.showinfo("Visual Math Lab", "Select a formula first.")
            return
        q = rec.get("example_question") or rec.get("formula_plain", "")
        self.question_text.delete("1.0", "end")
        self.question_text.insert("1.0", q)
        try:
            engine = VisualMathEngine(q)
            if engine.is_supported():
                self._solve_problem_text(q)
                self._formula_status_var.set(f"Visualized: {rec.get('title','')}")
                return
        except Exception:
            pass
        messagebox.showinfo("Visual Math Lab",
                            "This formula is a concept card - Visual Math cannot graph it.\n"
                            "Bu formul bir kavram kartidir - Visual Math grafik cizemez.")
        self._formula_status_var.set(f"{rec.get('title','')}: concept card (no graph)")

    def _copy_formula(self):
        rec = self._selected_formula_record()
        if not rec:
            messagebox.showinfo("Visual Math Lab", "Select a formula first.")
            return
        text = rec.get("formula_plain") or rec.get("formula_latex", "")
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._formula_status_var.set(f"Copied: {text[:50]}")
        except Exception:
            pass

    def _open_formula_pdf(self):
        rec = self._selected_formula_record()
        if not rec:
            messagebox.showinfo("Visual Math Lab", "Select a formula first.")
            return
        pdf_rel = rec.get("source_pdf", "")
        if not pdf_rel:
            messagebox.showinfo("Visual Math Lab", "No source PDF for this formula.")
            return
        pdf_path = self._resolve_pdf(pdf_rel)
        if pdf_path is None:
            messagebox.showwarning("Visual Math Lab", f"PDF not found:\n{pdf_rel}")
            return
        try:
            os.startfile(str(pdf_path))
        except Exception as exc:
            messagebox.showerror("Visual Math Lab", f"Could not open PDF:\n{exc}")

    def refresh_ui(self):
        self._lang = getattr(self.app, "language", "en")
        if self._current_viz is not None:
            self._update_text_panels()
        self._refresh_simulation_list()
        self._refresh_formula_list()

# ===========================================================================
# Phase 4-7 — shared helpers for the advanced visualizers
# ===========================================================================
def _slugify(s):
    s = (s or "graph").replace("²", "2").replace("√", "sqrt")
    s = s.replace("+", "plus").replace("-", "minus").replace("/", "over")
    s = re.sub(r"[^0-9A-Za-z]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")[:60] or "graph"


def _pretty_sym(expr):
    try:
        s = sp.sstr(expr) if sp is not None else str(expr)
    except Exception:
        s = str(expr)
    return s.replace("**", "^").replace("*", "")


def _approx(v):
    """Decimal display of a value (so 8/3 shows as 2.667, not 8/3 again)."""
    if v is None:
        return "?"
    return f"{v:.3f}".rstrip("0").rstrip(".")


def _style_ax(ax, title="", xlabel="x", ylabel="y", legend=False):
    ax.set_facecolor(BG)
    ax.grid(True, color=GRID, linestyle="--", linewidth=0.5)
    ax.axhline(0, color=AXIS, linewidth=0.8)
    ax.axvline(0, color=AXIS, linewidth=0.8)
    if title:
        ax.set_title(title, color=FG, fontsize=11)
    ax.set_xlabel(xlabel, color=AXIS)
    ax.set_ylabel(ylabel, color=AXIS)
    ax.tick_params(colors=AXIS)
    for spn in ax.spines.values():
        spn.set_color(GRID)
    if legend:
        ax.legend(loc="best", facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=8)


def _sample_expr(expr, a, b, n=400):
    """Sample a SymPy expression on [a, b]; returns (xs, ys)."""
    xs = _linspace(a, b, n)
    if sp is None or expr is None:
        return xs, [0.0 for _ in xs]
    x = sp.Symbol("x")
    try:
        fn = sp.lambdify(x, expr, modules=["numpy"] if np is not None else ["math"])
    except Exception:
        fn = None
    if np is not None:
        xs = np.linspace(a, b, n)
        try:
            ys = np.asarray(fn(xs), dtype=float)
            if ys.shape != xs.shape:
                ys = np.full_like(xs, float(ys))
        except Exception:
            ys = np.array([_evalf(expr, x, float(v)) or float("nan") for v in xs])
        return xs, ys
    ys = []
    for v in xs:
        try:
            ys.append(float(fn(v)) if fn else (_evalf(expr, x, v) or float("nan")))
        except Exception:
            ys.append(float("nan"))
    return xs, ys


# ===========================================================================
# Phase 4 — Quadratic / Parabola
# ===========================================================================
class QuadraticVisualizer(BaseVisualizer):
    def __init__(self, a, b, c):
        self.a, self.b, self.c = float(a), float(b), float(c)
        self.x = sp.Symbol("x") if sp is not None else None
        self.expr = (self.a * self.x ** 2 + self.b * self.x + self.c) if sp is not None else None
        self.vx = (-self.b / (2 * self.a)) if self.a != 0 else 0.0
        self.vy = self.a * self.vx ** 2 + self.b * self.vx + self.c
        self.disc = self.b ** 2 - 4 * self.a * self.c
        self.roots = []
        if self.a != 0 and self.disc >= 0:
            r = self.disc ** 0.5
            self.roots = sorted({(-self.b + r) / (2 * self.a), (-self.b - r) / (2 * self.a)})
        self.yint = self.c
        self.equation_str = self._poly_str()
        self.slug = "quadratic_" + _slugify(self.equation_str)
        self.fig_size = (6.6, 5.8)

    def _poly_str(self):
        s = f"y = {_fmt(self.a)}x²"
        if self.b:
            s += f" {'+' if self.b > 0 else '-'} {_fmt(abs(self.b))}x"
        if self.c:
            s += f" {'+' if self.c > 0 else '-'} {_fmt(abs(self.c))}"
        return s

    def _roots_str(self):
        if not self.roots:
            return "no real roots" if self.disc < 0 else "?"
        return " and ".join(f"x = {_fmt(r)}" for r in self.roots)

    def build_steps(self, lang="en"):
        a, b, c = _fmt(self.a), _fmt(self.b), _fmt(self.c)
        given = f"a = {a}, b = {b}, c = {c}   ({self.equation_str})"
        need = "Find the vertex, the x-intercepts (roots) and the y-intercept."
        formula = "Vertex x = -b / (2a);  roots from the quadratic formula;  y-intercept = (0, c)"
        substitute = f"vertex x = -({b}) / (2 * {a}) = {_fmt(self.vx)}"
        solve = (f"vertex = ({_fmt(self.vx)}, {_fmt(self.vy)});  "
                 f"{self._roots_str()};  y-intercept = (0, {c})")
        final_eq = (f"Vertex ({_fmt(self.vx)}, {_fmt(self.vy)}), "
                    f"roots {self._roots_str()}, axis of symmetry x = {_fmt(self.vx)}")
        opens = "upward" if self.a > 0 else "downward"
        visual = f"The parabola opens {opens}; the vertex is its lowest/highest point and x = {_fmt(self.vx)} is the mirror line."
        real = "A parabola models a thrown ball, a bridge arch, a fountain's water path, or a profit curve."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "Parabol gerçek hayatta çok yerde görülür:",
                "• Havaya atılan bir topun izlediği yol.",
                "• Bir köprü kemeri veya fıskiyeden çıkan suyun şekli.",
                f"• Tepe noktası ({_fmt(self.vx)}, {_fmt(self.vy)}) en yüksek/en alçak noktadır (ör. topun en yüksek anı).",
                "• Kâr-zarar eğrilerinde en yüksek kârın olduğu nokta.",
            ])
        return "\n".join([
            "A parabola shows up everywhere in real life:",
            "• The path of a ball thrown into the air.",
            "• The shape of a bridge arch or a water fountain.",
            f"• The vertex ({_fmt(self.vx)}, {_fmt(self.vy)}) is the highest/lowest point (e.g. the ball's peak).",
            "• In a profit curve, the vertex is the point of maximum profit.",
        ])

    def render_figure(self, fig, lang="en", real_life=False):
        span = max(4.0, abs(self.vx) + 4.0)
        lo, hi = self.vx - span, self.vx + span
        if self.roots:
            lo = min(lo, min(self.roots) - 2)
            hi = max(hi, max(self.roots) + 2)
        if real_life:
            ax = fig.add_subplot(2, 1, 1)
            ax2 = fig.add_subplot(2, 1, 2)
        else:
            ax = fig.add_subplot(1, 1, 1)
            ax2 = None
        xs, ys = _sample_expr(self.expr, lo, hi, 400)
        ax.plot(xs, ys, color=C_BLUE, linewidth=2.2, label=self.equation_str)
        ax.axvline(self.vx, color=C_GRAY, linestyle=":", linewidth=1.3, label=f"axis x = {_fmt(self.vx)}")
        ax.plot([self.vx], [self.vy], "D", color=C_YELLOW, markersize=9)
        ax.annotate(f"vertex ({_fmt(self.vx)}, {_fmt(self.vy)})", (self.vx, self.vy),
                    color=C_YELLOW, fontsize=9, ha="center", va="bottom")
        for r in self.roots:
            ax.plot([r], [0], "o", color=C_GREEN, markersize=8)
            ax.annotate(f"({_fmt(r)}, 0)", (r, 0), color=C_GREEN, fontsize=9, ha="center", va="top")
        ax.plot([0], [self.yint], "s", color=C_PURPLE, markersize=8)
        ax.annotate(f"(0, {_fmt(self.yint)})", (0, self.yint), color=C_PURPLE, fontsize=9, ha="left", va="bottom")
        _style_ax(ax, title=self.equation_str, legend=True)
        if ax2 is not None:
            xs2, ys2 = _sample_expr(self.expr, lo, hi, 400)
            ax2.plot(xs2, ys2, color=C_CYAN, linewidth=2.4)
            ax2.fill_between(list(xs2), list(ys2), color=C_CYAN, alpha=0.12)
            ax2.plot([self.vx], [self.vy], "D", color=C_YELLOW, markersize=9)
            title_rl = "Projectile / arch view" if lang == "en" else "Atış / kemer görünümü"
            _style_ax(ax2, title=title_rl, xlabel="distance", ylabel="height")
        fig.tight_layout()


# ===========================================================================
# Phase 4 — System of Equations
# ===========================================================================
class SystemOfEquationsVisualizer(BaseVisualizer):
    def __init__(self, line1, line2):
        self.m1, self.b1 = float(line1[0]), float(line1[1])
        self.m2, self.b2 = float(line2[0]), float(line2[1])
        self.eq1 = SlopeInterceptVisualizer._build_eq(self.m1, self.b1)
        self.eq2 = SlopeInterceptVisualizer._build_eq(self.m2, self.b2)
        self.parallel = abs(self.m1 - self.m2) < 1e-12
        if not self.parallel:
            self.ix = (self.b2 - self.b1) / (self.m1 - self.m2)
            self.iy = self.m1 * self.ix + self.b1
        else:
            self.ix = self.iy = None
        self.equation_str = f"{self.eq1} ; {self.eq2}"
        self.slug = "system_" + _slugify(f"{self.eq1}_{self.eq2}")
        self.fig_size = (6.4, 5.6)

    def build_steps(self, lang="en"):
        given = f"Line 1: {self.eq1}    Line 2: {self.eq2}"
        need = "Find the intersection point (the (x, y) that satisfies both equations)."
        formula = "Set the two right-hand sides equal: m1 x + b1 = m2 x + b2"
        if self.parallel:
            substitute = f"{_fmt(self.m1)}x + {_fmt(self.b1)} = {_fmt(self.m2)}x + {_fmt(self.b2)}"
            solve = "The slopes are equal, so the lines are parallel and never intersect."
            final_eq = "No solution (parallel lines)."
            visual = "Two parallel lines stay the same distance apart and never cross."
        else:
            substitute = f"{_fmt(self.m1)}x + {_fmt(self.b1)} = {_fmt(self.m2)}x + {_fmt(self.b2)}"
            solve = f"x = ({_fmt(self.b2)} - {_fmt(self.b1)}) / ({_fmt(self.m1)} - {_fmt(self.m2)}) = {_fmt(self.ix)}, then y = {_fmt(self.iy)}"
            final_eq = f"Intersection = ({_fmt(self.ix)}, {_fmt(self.iy)})"
            visual = f"The lines cross at ({_fmt(self.ix)}, {_fmt(self.iy)}); that single point lies on both lines."
        real = "The crossing point is where two plans/speeds/prices become exactly equal."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            base = ["İki doğrunun kesişimi gerçek hayatta 'eşit oldukları an'dır:",
                    "• İki farklı fiyat planının aynı tutara geldiği nokta.",
                    "• İki aracın aynı konuma geldiği an (hız-zaman doğruları)."]
            if not self.parallel:
                base.append(f"• Burada bu nokta ({_fmt(self.ix)}, {_fmt(self.iy)}).")
            else:
                base.append("• Burada doğrular paralel, yani hiç eşitlenmiyorlar.")
            return "\n".join(base)
        base = ["The intersection of two lines is the moment they become equal:",
                "• Where two pricing plans cost exactly the same.",
                "• Where two moving objects meet (speed-time lines)."]
        if not self.parallel:
            base.append(f"• Here that point is ({_fmt(self.ix)}, {_fmt(self.iy)}).")
        else:
            base.append("• Here the lines are parallel, so they never become equal.")
        return "\n".join(base)

    def render_figure(self, fig, lang="en", real_life=False):
        ax = fig.add_subplot(1, 1, 1)
        lo, hi = -6, 10
        for m, b, eq, col in [(self.m1, self.b1, self.eq1, C_BLUE), (self.m2, self.b2, self.eq2, C_YELLOW)]:
            xs = _linspace(lo, hi, 200)
            ys = [m * v + b for v in (xs.tolist() if np is not None else xs)]
            ax.plot(list(xs), ys, color=col, linewidth=2.2, label=eq)
        if not self.parallel:
            ax.plot([self.ix], [self.iy], "D", color=C_GREEN, markersize=11)
            ax.annotate(f"({_fmt(self.ix)}, {_fmt(self.iy)})", (self.ix, self.iy),
                        color=C_GREEN, fontsize=10, ha="left", va="bottom")
            note = "This point satisfies both equations" if lang == "en" else "Bu nokta iki denklemi de sağlar"
            ax.text(0.5, 0.02, note, transform=ax.transAxes, color=C_GREEN, fontsize=9, ha="center")
        _style_ax(ax, title="System of equations", legend=True)
        ax.set_xlim(lo, hi)
        fig.tight_layout()


# ===========================================================================
# Phase 5 — Right Triangle Trigonometry
# ===========================================================================
class TriangleTrigVisualizer(BaseVisualizer):
    def __init__(self, opposite, adjacent, hyp):
        import math as _m
        self.opp = opposite
        self.adj = adjacent
        self.hyp = hyp
        # complete the triangle with the Pythagorean theorem if a side is missing
        if self.hyp is None and self.opp is not None and self.adj is not None:
            self.hyp = _m.hypot(self.opp, self.adj)
        elif self.opp is None and self.hyp is not None and self.adj is not None:
            self.opp = _m.sqrt(max(self.hyp ** 2 - self.adj ** 2, 0))
        elif self.adj is None and self.hyp is not None and self.opp is not None:
            self.adj = _m.sqrt(max(self.hyp ** 2 - self.opp ** 2, 0))
        self.sin = self._ratio(self.opp, self.hyp)
        self.cos = self._ratio(self.adj, self.hyp)
        self.tan = self._ratio(self.opp, self.adj)
        self.sin_v = (self.opp / self.hyp) if self.hyp else None
        self.cos_v = (self.adj / self.hyp) if self.hyp else None
        self.tan_v = (self.opp / self.adj) if self.adj else None
        self.theta = _m.degrees(_m.atan2(self.opp or 0, self.adj or 1))
        self.equation_str = f"sin={self.sin}, cos={self.cos}, tan={self.tan}"
        self.slug = "triangle_trig_" + _slugify(f"{self.opp}_{self.adj}_{self.hyp}")
        self.fig_size = (6.2, 5.6)

    @staticmethod
    def _ratio(num, den):
        if num is None or den in (None, 0):
            return "?"
        try:
            fr = Fraction(num).limit_denominator(1000) / Fraction(den).limit_denominator(1000)
            return f"{fr.numerator}/{fr.denominator}" if fr.denominator != 1 else f"{fr.numerator}"
        except Exception:
            return _fmt(num / den)

    def build_steps(self, lang="en"):
        given = f"opposite = {_fmt(self.opp)}, adjacent = {_fmt(self.adj)}, hypotenuse = {_fmt(self.hyp)}"
        need = "Find sin θ, cos θ and tan θ."
        formula = "sin θ = opposite / hypotenuse,  cos θ = adjacent / hypotenuse,  tan θ = opposite / adjacent"
        substitute = (f"sin θ = {_fmt(self.opp)}/{_fmt(self.hyp)},  "
                      f"cos θ = {_fmt(self.adj)}/{_fmt(self.hyp)},  tan θ = {_fmt(self.opp)}/{_fmt(self.adj)}")
        solve = f"sin θ = {self.sin},  cos θ = {self.cos},  tan θ = {self.tan}"
        final_eq = f"sin θ = {self.sin},  cos θ = {self.cos},  tan θ = {self.tan}  (θ ≈ {self.theta:.1f}°)"
        visual = "Each ratio compares two sides of the right triangle; θ is the angle at the corner between the adjacent side and the hypotenuse."
        real = "Trig ratios let you find heights and distances you cannot measure directly (ramps, roofs, ladders, surveying)."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "Dik üçgen trigonometrisi ulaşamadığın uzunlukları bulmanı sağlar:",
                "• Bir merdivenin duvarla yaptığı açı ve yüksekliği.",
                "• Bir çatının eğimi.",
                "• Karşı kıyıdaki bir ağacın yüksekliği (sadece açı ve mesafe ile).",
                f"Burada sin θ = {self.sin}, cos θ = {self.cos}, tan θ = {self.tan}.",
            ])
        return "\n".join([
            "Right-triangle trig lets you find lengths you cannot reach:",
            "• The angle and height a ladder makes against a wall.",
            "• The slope of a roof.",
            "• The height of a tree across a river (from angle and distance only).",
            f"Here sin θ = {self.sin}, cos θ = {self.cos}, tan θ = {self.tan}.",
        ])

    def render_figure(self, fig, lang="en", real_life=False):
        ax = fig.add_subplot(1, 1, 1)
        ox, oy = 0.0, 0.0
        adj = self.adj or 1.0
        opp = self.opp or 1.0
        ax.plot([ox, ox + adj], [oy, oy], color=C_BLUE, linewidth=3)          # adjacent
        ax.plot([ox + adj, ox + adj], [oy, oy + opp], color=C_GREEN, linewidth=3)  # opposite
        ax.plot([ox, ox + adj], [oy, oy + opp], color=C_YELLOW, linewidth=3)  # hypotenuse
        ax.add_patch(__import__("matplotlib").patches.Rectangle((ox + adj - 0.35, oy), 0.35, 0.35, fill=False, edgecolor=AXIS))
        ax.annotate(f"adjacent = {_fmt(self.adj)}", (ox + adj / 2, oy), color=C_BLUE, fontsize=10, ha="center", va="top")
        ax.annotate(f"opposite = {_fmt(self.opp)}", (ox + adj, oy + opp / 2), color=C_GREEN, fontsize=10, ha="left", va="center")
        ax.annotate(f"hyp = {_fmt(self.hyp)}", (ox + adj / 2, oy + opp / 2), color=C_YELLOW, fontsize=10, ha="right", va="bottom")
        ax.annotate("θ", (ox + 0.4, oy + 0.12), color=FG, fontsize=13, ha="left", va="bottom")
        ax.text(0.5, 0.94, f"sin θ = {self.sin}   cos θ = {self.cos}   tan θ = {self.tan}",
                transform=ax.transAxes, color=FG, fontsize=10, ha="center")
        _style_ax(ax, title="Right triangle", xlabel="", ylabel="")
        ax.set_xlim(-1, adj + 2)
        ax.set_ylim(-1, opp + 2)
        ax.set_aspect("equal", adjustable="box")
        fig.tight_layout()


# ===========================================================================
# Phase 5 — Unit Circle
# ===========================================================================
class UnitCircleVisualizer(BaseVisualizer):
    def __init__(self, angle_deg):
        import math as _m
        self.angle = float(angle_deg)
        self.rad = _m.radians(self.angle)
        self.cos_v = _m.cos(self.rad)
        self.sin_v = _m.sin(self.rad)
        if sp is not None:
            ang = sp.Rational(int(round(self.angle)), 1)
            self.cos_exact = sp.nsimplify(sp.cos(sp.pi * ang / 180), rational=False)
            self.sin_exact = sp.nsimplify(sp.sin(sp.pi * ang / 180), rational=False)
            self.cos_str = _pretty_sym(self.cos_exact).replace("sqrt", "√")
            self.sin_str = _pretty_sym(self.sin_exact).replace("sqrt", "√")
        else:
            self.cos_str = _fmt(self.cos_v)
            self.sin_str = _fmt(self.sin_v)
        self.equation_str = f"angle {_fmt(self.angle)}deg cos={self.cos_str} sin={self.sin_str}"
        self.slug = "unit_circle_" + _slugify(f"{int(self.angle)}deg")
        self.fig_size = (5.8, 5.8)

    def build_steps(self, lang="en"):
        given = f"angle θ = {_fmt(self.angle)}°"
        need = "Find cos θ (the x-coordinate) and sin θ (the y-coordinate) on the unit circle."
        formula = "On the unit circle: point = (cos θ, sin θ), radius = 1"
        substitute = f"cos {_fmt(self.angle)}° and sin {_fmt(self.angle)}°"
        solve = f"cos θ = {self.cos_str} ≈ {_fmt(self.cos_v)},  sin θ = {self.sin_str} ≈ {_fmt(self.sin_v)}"
        final_eq = f"cos {_fmt(self.angle)}° = {self.cos_str},  sin {_fmt(self.angle)}° = {self.sin_str}"
        visual = "The angle sweeps from the positive x-axis; the point where it meets the circle has coordinates (cos θ, sin θ)."
        real = "Anything that rotates — a clock hand, a Ferris wheel seat, a wheel — traces sine and cosine over time."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "Birim çember dönen her şeyi anlatır:",
                "• Saat ibresinin ucunun yüksekliği zamanla sin/cos çizer.",
                "• Dönme dolaptaki bir koltuğun yüksekliği.",
                f"{_fmt(self.angle)}° için: yatay = cos θ = {self.cos_str}, dikey = sin θ = {self.sin_str}.",
            ])
        return "\n".join([
            "The unit circle describes anything that rotates:",
            "• The height of a clock hand's tip over time traces sine/cosine.",
            "• The height of a seat on a Ferris wheel.",
            f"For {_fmt(self.angle)}°: horizontal = cos θ = {self.cos_str}, vertical = sin θ = {self.sin_str}.",
        ])

    def render_figure(self, fig, lang="en", real_life=False):
        import math as _m
        ax = fig.add_subplot(1, 1, 1)
        ts = _linspace(0, 2 * _m.pi, 200)
        cx = [_m.cos(t) for t in (ts.tolist() if np is not None else ts)]
        cy = [_m.sin(t) for t in (ts.tolist() if np is not None else ts)]
        ax.plot(cx, cy, color=C_GRAY, linewidth=1.6)
        ax.plot([0, self.cos_v], [0, self.sin_v], color=C_YELLOW, linewidth=2.4)
        ax.plot([self.cos_v], [self.sin_v], "o", color=C_GREEN, markersize=9)
        ax.plot([self.cos_v, self.cos_v], [0, self.sin_v], color=C_RED, linestyle="--", linewidth=1.4)
        ax.plot([0, self.cos_v], [self.sin_v, self.sin_v], color=C_RED, linestyle="--", linewidth=1.4)
        ax.annotate(f"({self.cos_str}, {self.sin_str})", (self.cos_v, self.sin_v),
                    color=C_GREEN, fontsize=10, ha="left", va="bottom")
        ax.annotate(f"cos = {self.cos_str}", (self.cos_v / 2 if self.cos_v else 0, 0), color=C_RED, fontsize=9, ha="center", va="top")
        ax.annotate(f"sin = {self.sin_str}", (0, self.sin_v / 2 if self.sin_v else 0), color=C_RED, fontsize=9, ha="right", va="center")
        _style_ax(ax, title=f"Unit circle — {_fmt(self.angle)}°")
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)
        ax.set_aspect("equal", adjustable="box")
        fig.tight_layout()


# ===========================================================================
# Phase 5 — Trigonometric Wave
# ===========================================================================
class TrigWaveVisualizer(BaseVisualizer):
    def __init__(self, fn="sin", amplitude=1.0, frequency=1.0, phase=0.0):
        self.fn = (fn or "sin").lower()
        self.A = float(amplitude)
        self.f = float(frequency)
        self.phase = float(phase)
        self.equation_str = f"y = {_fmt(self.A)}{self.fn}({_fmt(self.f)}x {'+' if self.phase>=0 else '-'} {_fmt(abs(self.phase))})"
        self.slug = "trig_wave_" + _slugify(f"{self.fn}_{self.A}_{self.f}_{self.phase}")
        self.fig_size = (7.2, 5.0)

    def _f(self, x):
        import math as _m
        base = {"sin": _m.sin, "cos": _m.cos, "tan": _m.tan}.get(self.fn, _m.sin)
        return self.A * base(self.f * x + self.phase)

    def build_steps(self, lang="en"):
        import math as _m
        period = (2 * _m.pi / self.f) if (self.fn in ("sin", "cos") and self.f) else _m.pi / (self.f or 1)
        given = f"{self.equation_str}  (amplitude A = {_fmt(self.A)}, frequency = {_fmt(self.f)}, phase = {_fmt(self.phase)})"
        need = "Describe and graph the wave: amplitude, period, zeros, peaks and troughs."
        formula = "y = A · " + self.fn + "(f·x + phase);  period = 2π / f"
        substitute = f"A = {_fmt(self.A)}, f = {_fmt(self.f)}, phase = {_fmt(self.phase)}"
        solve = f"amplitude = {_fmt(abs(self.A))}, period ≈ {_fmt(period)}"
        final_eq = self.equation_str
        visual = "The curve repeats every period; the amplitude is how high the peaks reach above the centre line."
        real = "Waves model sound, light, vibrations, alternating current and ocean waves."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "Trigonometrik dalgalar tekrar eden her şeyi modeller:",
                "• Ses dalgaları (yükseklik = ses şiddeti).",
                "• Işık ve radyo dalgaları.",
                "• Bir yayın titreşimi, deniz dalgaları, alternatif akım.",
                f"Genlik = {_fmt(abs(self.A))}, frekans = {_fmt(self.f)}.",
            ])
        return "\n".join([
            "Trig waves model anything that repeats:",
            "• Sound waves (amplitude = loudness).",
            "• Light and radio waves.",
            "• A vibrating spring, ocean waves, alternating current.",
            f"Amplitude = {_fmt(abs(self.A))}, frequency = {_fmt(self.f)}.",
        ])

    def render_figure(self, fig, lang="en", real_life=False):
        import math as _m
        ax = fig.add_subplot(1, 1, 1)
        lo, hi = -2 * _m.pi, 2 * _m.pi
        xs = _linspace(lo, hi, 600)
        xl = xs.tolist() if np is not None else xs
        ys = []
        for v in xl:
            try:
                y = self._f(v)
                ys.append(y if abs(y) < 50 else float("nan"))
            except Exception:
                ys.append(float("nan"))
        ax.plot(xl, ys, color=C_BLUE, linewidth=2.2, label=self.equation_str)
        if self.fn in ("sin", "cos"):
            ax.axhline(self.A, color=C_GRAY, linestyle=":", linewidth=1)
            ax.axhline(-self.A, color=C_GRAY, linestyle=":", linewidth=1)
        _style_ax(ax, title=self.equation_str, legend=True)
        ax.set_xlim(lo, hi)
        fig.tight_layout()


# ===========================================================================
# Phase 6 — Derivative / Tangent Line
# ===========================================================================
class DerivativeVisualizer(BaseVisualizer):
    def __init__(self, func_expr, x0=0.0):
        self.x = sp.Symbol("x") if sp is not None else None
        self.expr = _sym_parse(func_expr)
        self.func_str = _pretty_sym(self.expr) if self.expr is not None else str(func_expr)
        self.x0 = float(x0)
        if sp is not None and self.expr is not None:
            self.deriv = sp.diff(self.expr, self.x)
            self.deriv_str = _pretty_sym(self.deriv)
            self.slope = _evalf(self.deriv, self.x, self.x0)
            self.y0 = _evalf(self.expr, self.x, self.x0)
        else:
            self.deriv = None
            self.deriv_str = "?"
            self.slope = None
            self.y0 = None
        if self.slope is not None and self.y0 is not None:
            self.tb = self.y0 - self.slope * self.x0
            self.tangent_str = SlopeInterceptVisualizer._build_eq(self.slope, self.tb)
        else:
            self.tb = None
            self.tangent_str = "?"
        self.equation_str = f"f(x) = {self.func_str}, tangent {self.tangent_str}"
        self.slug = "derivative_" + _slugify(f"{self.func_str}_at_{self.x0}")
        self.fig_size = (6.6, 5.8)

    def build_steps(self, lang="en"):
        given = f"f(x) = {self.func_str},  point x0 = {_fmt(self.x0)}"
        need = "Find f'(x), the slope at x0, and the tangent line at x0."
        formula = "f'(x) = d/dx f(x);  tangent: y - f(x0) = f'(x0)(x - x0)"
        substitute = f"f'(x) = {self.deriv_str};  f'({_fmt(self.x0)}) = {_fmt(self.slope)};  f({_fmt(self.x0)}) = {_fmt(self.y0)}"
        solve = f"tangent: y - {_fmt(self.y0)} = {_fmt(self.slope)}(x - {_fmt(self.x0)})"
        final_eq = f"f'(x) = {self.deriv_str};  slope at x0 = {_fmt(self.slope)};  tangent: {self.tangent_str}"
        visual = f"The tangent line just touches the curve at ({_fmt(self.x0)}, {_fmt(self.y0)}); its steepness equals the derivative there."
        real = "The derivative is an instantaneous rate of change — like the exact speed shown on a speedometer at one moment."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "Türev 'o andaki değişim hızı'dır:",
                "• Hız-zaman grafiğinde türev, o anki ivmedir.",
                "• Konum-zaman grafiğinde türev, o anki hızdır (hız göstergesi).",
                f"Burada x0 = {_fmt(self.x0)} noktasında eğim (anlık hız) = {_fmt(self.slope)}.",
            ])
        return "\n".join([
            "The derivative is the instantaneous rate of change:",
            "• On a distance-time graph it is the exact speed at one instant (a speedometer).",
            "• On a speed-time graph it is the acceleration at that instant.",
            f"Here at x0 = {_fmt(self.x0)} the slope (instant rate) = {_fmt(self.slope)}.",
        ])

    def render_figure(self, fig, lang="en", real_life=False):
        ax = fig.add_subplot(1, 1, 1)
        lo, hi = self.x0 - 4, self.x0 + 4
        xs, ys = _sample_expr(self.expr, lo, hi, 400)
        ax.plot(xs, ys, color=C_BLUE, linewidth=2.2, label=f"f(x) = {self.func_str}")
        if self.slope is not None:
            txs = _linspace(lo, hi, 50)
            txl = txs.tolist() if np is not None else txs
            tys = [self.slope * v + self.tb for v in txl]
            ax.plot(txl, tys, color=C_YELLOW, linewidth=2.0, linestyle="--", label=f"tangent {self.tangent_str}")
            ax.plot([self.x0], [self.y0], "o", color=C_GREEN, markersize=9)
            ax.annotate(f"({_fmt(self.x0)}, {_fmt(self.y0)}), slope = {_fmt(self.slope)}",
                        (self.x0, self.y0), color=C_GREEN, fontsize=9, ha="left", va="top")
            if real_life:
                for dx in (1.5, 1.0, 0.5):
                    x1 = self.x0 + dx
                    y1 = _evalf(self.expr, self.x, x1)
                    if y1 is None:
                        continue
                    sec = (y1 - self.y0) / dx
                    sxs = _linspace(lo, hi, 30)
                    sxl = sxs.tolist() if np is not None else sxs
                    ax.plot(sxl, [sec * (v - self.x0) + self.y0 for v in sxl],
                            color=C_GRAY, linewidth=0.9, alpha=0.6)
        _style_ax(ax, title=f"f(x) = {self.func_str}", legend=True)
        fig.tight_layout()


# ===========================================================================
# Phase 7 — Integral / Area Under Curve / Riemann Sum
# ===========================================================================
class IntegralVisualizer(BaseVisualizer):
    def __init__(self, func_expr, a, b, n=10, method="left"):
        self.x = sp.Symbol("x") if sp is not None else None
        self.expr = _sym_parse(func_expr)
        self.func_str = _pretty_sym(self.expr) if self.expr is not None else str(func_expr)
        self.a, self.b = float(a), float(b)
        self.n = max(1, int(n))
        self.method = method if method in ("left", "right", "mid") else "left"
        if sp is not None and self.expr is not None:
            try:
                a_s = sp.nsimplify(self.a, rational=True)
                b_s = sp.nsimplify(self.b, rational=True)
                self.exact = sp.integrate(self.expr, (self.x, a_s, b_s))
                self.exact_val = float(self.exact)
                self.exact_str = _pretty_sym(self.exact)
            except Exception:
                self.exact = None
                self.exact_val = None
                self.exact_str = "?"
        else:
            self.exact = None
            self.exact_val = None
            self.exact_str = "?"
        self.approx = self.riemann(self.n, self.method)
        self.equation_str = f"integral of {self.func_str} from {_fmt(self.a)} to {_fmt(self.b)} = {self.exact_str}"
        self.slug = "integral_" + _slugify(f"{self.func_str}_{self.a}_{self.b}")
        self.fig_size = (6.8, 5.8)

    def riemann(self, n, method="left"):
        n = max(1, int(n))
        if sp is None or self.expr is None:
            return None
        h = (self.b - self.a) / n
        try:
            fn = sp.lambdify(self.x, self.expr, "math")
        except Exception:
            return None
        total = 0.0
        for i in range(n):
            if method == "left":
                xi = self.a + i * h
            elif method == "right":
                xi = self.a + (i + 1) * h
            else:
                xi = self.a + (i + 0.5) * h
            try:
                total += fn(xi) * h
            except Exception:
                return None
        return total

    def build_steps(self, lang="en"):
        given = f"f(x) = {self.func_str}, from x = {_fmt(self.a)} to x = {_fmt(self.b)}"
        need = "Find the area under the curve (the definite integral)."
        formula = "Area = ∫ from a to b of f(x) dx"
        F = "?"
        if sp is not None and self.expr is not None:
            try:
                F = _pretty_sym(sp.integrate(self.expr, self.x))
            except Exception:
                F = "?"
        substitute = f"∫ from {_fmt(self.a)} to {_fmt(self.b)} of {self.func_str} dx = [{F}] from {_fmt(self.a)} to {_fmt(self.b)}"
        solve = f"= {self.exact_str} ≈ {_approx(self.exact_val)}"
        final_eq = f"Area = {self.exact_str} ≈ {_approx(self.exact_val)}   (Riemann n={self.n}: ≈ {_approx(self.approx)})"
        visual = "The integral is the shaded area between the curve and the x-axis; more rectangles approximate it better."
        real = "An integral is a total accumulation: area under a speed-time graph is total distance travelled."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "İntegral 'toplam birikim'dir:",
                "• Hız-zaman grafiğinde eğri altındaki alan = toplam yol.",
                "• Maliyet oranı grafiğinde alan = toplam maliyet.",
                "• Bir musluğun akış hızının altındaki alan = biriken su.",
                f"Burada alan = {self.exact_str} ≈ {_approx(self.exact_val)}.",
            ])
        return "\n".join([
            "An integral is a total accumulation:",
            "• Area under a speed-time graph = total distance travelled.",
            "• Area under a cost-rate graph = total cost.",
            "• Area under a flow-rate graph = total water collected.",
            f"Here the area = {self.exact_str} ≈ {_approx(self.exact_val)}.",
        ])

    def render_figure(self, fig, lang="en", real_life=False):
        ax = fig.add_subplot(1, 1, 1)
        pad = max(1.0, (self.b - self.a) * 0.4)
        lo, hi = self.a - pad, self.b + pad
        xs, ys = _sample_expr(self.expr, lo, hi, 400)
        ax.plot(xs, ys, color=C_BLUE, linewidth=2.2, label=f"f(x) = {self.func_str}")
        axs, ays = _sample_expr(self.expr, self.a, self.b, 200)
        ax.fill_between(list(axs), list(ays), color=C_CYAN, alpha=0.25)
        # Riemann rectangles
        h = (self.b - self.a) / self.n
        try:
            fn = sp.lambdify(self.x, self.expr, "math") if (sp is not None and self.expr is not None) else None
        except Exception:
            fn = None
        if fn is not None:
            for i in range(self.n):
                if self.method == "left":
                    xi = self.a + i * h
                elif self.method == "right":
                    xi = self.a + (i + 1) * h
                else:
                    xi = self.a + (i + 0.5) * h
                try:
                    hgt = fn(xi)
                except Exception:
                    continue
                ax.add_patch(__import__("matplotlib").patches.Rectangle(
                    (self.a + i * h, 0), h, hgt, facecolor=C_YELLOW, edgecolor=C_RED, alpha=0.25, linewidth=0.8))
        ax.axvline(self.a, color=C_GRAY, linestyle=":", linewidth=1)
        ax.axvline(self.b, color=C_GRAY, linestyle=":", linewidth=1)
        ax.text(0.5, 0.95, f"Area = {self.exact_str} ≈ {_approx(self.exact_val)}   (n={self.n} → {_approx(self.approx)})",
                transform=ax.transAxes, color=FG, fontsize=9, ha="center")
        _style_ax(ax, title=f"Area under f(x) = {self.func_str}", legend=True)
        fig.tight_layout()


# ===========================================================================
# Extra — Basic Vectors
# ===========================================================================
class VectorVisualizer(BaseVisualizer):
    def __init__(self, v1, v2=None):
        import math as _m
        self.v1 = (float(v1[0]), float(v1[1]))
        self.v2 = (float(v2[0]), float(v2[1])) if v2 else None
        self.mag1 = _m.hypot(*self.v1)
        if self.v2:
            self.sum = (self.v1[0] + self.v2[0], self.v1[1] + self.v2[1])
            self.mag2 = _m.hypot(*self.v2)
        else:
            self.sum = None
            self.mag2 = None
        self.equation_str = f"v1={self.v1}" + (f" + v2={self.v2}" if self.v2 else "")
        self.slug = "vector_" + _slugify(str(self.v1) + ("_" + str(self.v2) if self.v2 else ""))
        self.fig_size = (6.0, 5.8)

    def build_steps(self, lang="en"):
        given = f"v1 = {self.v1}" + (f", v2 = {self.v2}" if self.v2 else "")
        need = "Find the magnitude" + (" and the vector sum." if self.v2 else " of the vector.")
        formula = "|v| = √(x² + y²);  v1 + v2 = (x1+x2, y1+y2)"
        substitute = f"|v1| = √({_fmt(self.v1[0])}² + {_fmt(self.v1[1])}²)"
        solve = f"|v1| = {_fmt(self.mag1)}" + (f";  v1 + v2 = {self.sum}" if self.v2 else "")
        final_eq = f"|v1| = {_fmt(self.mag1)}" + (f", sum = {self.sum}" if self.v2 else "")
        visual = "A vector is an arrow with length (magnitude) and direction; adding vectors places them tip-to-tail."
        real = "Vectors model forces, velocities and displacements (e.g. wind pushing a plane off course)."
        return self.build_common_steps(lang, given, need, formula, substitute, solve, final_eq, visual, real)

    def build_real_life(self, lang="en"):
        if lang == "tr":
            return "\n".join([
                "Vektörler yön ve büyüklüğü olan nicelikleri anlatır:",
                "• Rüzgârın bir uçağa uyguladığı kuvvet ve yön.",
                "• Bir geminin hızı ve gittiği yön.",
                f"Burada |v1| = {_fmt(self.mag1)}" + (f", v1 + v2 = {self.sum}." if self.v2 else "."),
            ])
        return "\n".join([
            "Vectors describe quantities with direction and size:",
            "• The force and direction of wind on a plane.",
            "• The speed and heading of a ship.",
            f"Here |v1| = {_fmt(self.mag1)}" + (f", v1 + v2 = {self.sum}." if self.v2 else "."),
        ])

    def render_figure(self, fig, lang="en", real_life=False):
        ax = fig.add_subplot(1, 1, 1)
        ax.annotate("", xy=self.v1, xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=2.4))
        ax.annotate("v1", self.v1, color=C_BLUE, fontsize=11, ha="left", va="bottom")
        pts = [self.v1]
        if self.v2:
            ax.annotate("", xy=(self.v1[0] + self.v2[0], self.v1[1] + self.v2[1]), xytext=self.v1,
                        arrowprops=dict(arrowstyle="->", color=C_YELLOW, lw=2.2))
            ax.annotate("", xy=self.sum, xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=C_GREEN, lw=2.4))
            ax.annotate(f"sum {self.sum}", self.sum, color=C_GREEN, fontsize=10, ha="left", va="bottom")
            pts += [self.v2, self.sum]
        lim = max(2.0, *(abs(c) for p in pts for c in p)) + 1
        _style_ax(ax, title="Vectors")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal", adjustable="box")
        fig.tight_layout()


# ===========================================================================
# Optional Manim scenes (only defined when manim is importable)
# Priority order: slope_intercept, quadratic, derivative, integral, unit_circle
# ===========================================================================
if MANIM_AVAILABLE:
    class QuadraticScene(Scene):
        def __init__(self, viz, lang="en", **kwargs):
            self.viz = viz
            self.lang = lang
            super().__init__(**kwargs)

        def construct(self):
            title = Text("Quadratic Function" if self.lang == "en" else "İkinci Dereceden Fonksiyon", font_size=40)
            self.play(Write(title)); self.wait(1)
            self.play(title.animate.to_edge(UP).scale(0.6))
            eq = Text(self.viz.equation_str, font_size=32)
            self.play(Write(eq)); self.wait(1); self.play(FadeOut(eq))
            axes = Axes(x_range=[self.viz.vx - 5, self.viz.vx + 5, 2], y_range=[-6, 8, 2], tips=False).scale(0.55).shift(DOWN * 0.3)
            self.play(Create(axes))
            graph = axes.plot(lambda x: self.viz.a * x ** 2 + self.viz.b * x + self.viz.c, color="#2f80ed")
            self.play(Create(graph))
            vdot = Dot(axes.c2p(self.viz.vx, self.viz.vy), color="#C99A2E")
            self.play(FadeIn(vdot)); self.wait(2)

    class DerivativeScene(Scene):
        def __init__(self, viz, lang="en", **kwargs):
            self.viz = viz
            self.lang = lang
            super().__init__(**kwargs)

        def construct(self):
            title = Text("Derivative & Tangent" if self.lang == "en" else "Türev ve Teğet", font_size=40)
            self.play(Write(title)); self.wait(1)
            self.play(title.animate.to_edge(UP).scale(0.6))
            axes = Axes(x_range=[self.viz.x0 - 4, self.viz.x0 + 4, 2], y_range=[-2, 10, 2], tips=False).scale(0.55).shift(DOWN * 0.3)
            self.play(Create(axes))
            import sympy as _sp
            f = _sp.lambdify(self.viz.x, self.viz.expr, "math")
            graph = axes.plot(lambda x: f(x), color="#2f80ed")
            self.play(Create(graph))
            if self.viz.slope is not None:
                tangent = axes.plot(lambda x: self.viz.slope * x + self.viz.tb, color="#C99A2E")
                self.play(Create(tangent))
                self.play(FadeIn(Dot(axes.c2p(self.viz.x0, self.viz.y0), color="#16A55A")))
            self.wait(2)

    class IntegralScene(Scene):
        def __init__(self, viz, lang="en", **kwargs):
            self.viz = viz
            self.lang = lang
            super().__init__(**kwargs)

        def construct(self):
            title = Text("Area Under the Curve" if self.lang == "en" else "Eğri Altındaki Alan", font_size=40)
            self.play(Write(title)); self.wait(1)
            self.play(title.animate.to_edge(UP).scale(0.6))
            axes = Axes(x_range=[self.viz.a - 1, self.viz.b + 1, 1], y_range=[0, 8, 2], tips=False).scale(0.55).shift(DOWN * 0.3)
            self.play(Create(axes))
            import sympy as _sp
            f = _sp.lambdify(self.viz.x, self.viz.expr, "math")
            graph = axes.plot(lambda x: f(x), x_range=[self.viz.a - 1, self.viz.b + 1], color="#2f80ed")
            self.play(Create(graph))
            area = axes.get_area(graph, x_range=[self.viz.a, self.viz.b], color="#22d3ee", opacity=0.4)
            self.play(FadeIn(area)); self.wait(2)

    class UnitCircleScene(Scene):
        def __init__(self, viz, lang="en", **kwargs):
            self.viz = viz
            self.lang = lang
            super().__init__(**kwargs)

        def construct(self):
            title = Text("Unit Circle" if self.lang == "en" else "Birim Çember", font_size=40)
            self.play(Write(title)); self.wait(1)
            self.play(title.animate.to_edge(UP).scale(0.6))
            circle = Circle(radius=2.2, color="#8A7E6E").shift(DOWN * 0.3)
            self.play(Create(circle))
            tip = circle.get_center() + 2.2 * np.array([self.viz.cos_v, self.viz.sin_v, 0]) if np is not None else circle.get_center()
            radius = Line(circle.get_center(), tip, color="#C99A2E")
            self.play(Create(radius))
            self.play(FadeIn(Dot(tip, color="#16A55A"))); self.wait(2)


# ===========================================================================
# Reusable graph rendering for records (shared by the Simulation Studio)
# ===========================================================================
def _draw_linear_on_ax(ax, viz):
    """Draw a linear-family visualizer onto a Matplotlib axes (dark theme,
    polished). Mirrors VisualMathLab._draw_graph's single-axes rendering so the
    Simulation Studio graph looks the same as the main lab graph."""
    ax.set_facecolor(BG)
    if isinstance(viz, SlopeInterceptVisualizer):
        lines_to_draw = [(viz.m, viz.b, viz.equation_str, "#2f80ed", True)]
        points = [(0, viz.b), (2, viz.m * 2 + viz.b)]
        tri = viz.get_slope_triangle(viz.m, viz.b)
    elif isinstance(viz, TwoPointLineVisualizer):
        lines_to_draw = [(viz.m, viz.b, viz.equation_str, "#2f80ed", True)]
        points = [viz.p1, viz.p2]
        tri = viz.get_slope_triangle(viz.m, viz.b)
    elif isinstance(viz, PointSlopeVisualizer):
        lines_to_draw = [(viz.m, viz.b, viz.slope_intercept, "#2f80ed", True)]
        tri = viz.get_slope_triangle(viz.m, viz.b)
        points = [viz.point, (viz.point[0] + tri["run"], viz.point[1] + tri["rise"])] if tri else [viz.point]
    elif isinstance(viz, ParallelLineVisualizer):
        lines_to_draw = [(viz.orig_m, viz.orig_b, viz.orig_eq, "#555", False),
                         (viz.new_m, viz.new_b, viz.new_eq, "#2f80ed", True)]
        points = [viz.point]
        tri = viz.get_slope_triangle(viz.new_m, viz.new_b)
    elif isinstance(viz, PerpendicularLineVisualizer):
        lines_to_draw = [(viz.orig_m, viz.orig_b, viz.orig_eq, "#555", False),
                         (viz.new_m, viz.new_b, viz.new_eq, "#2f80ed", True)]
        points = [viz.point]
        tri = viz.get_slope_triangle(viz.new_m, viz.new_b)
    else:
        lines_to_draw = [(0, 0, "y = 0", "#2f80ed", True)]
        points = []
        tri = None

    ax.grid(True, color=GRID, linestyle="-", linewidth=0.6, zorder=0)
    ax.axhline(0, color=FG, linewidth=1.5, zorder=1)
    ax.axvline(0, color=FG, linewidth=1.5, zorder=1)
    primary = next((l for l in lines_to_draw if l[4]), lines_to_draw[0])
    pm, pb = primary[0], primary[1]
    interest = list(points) + [(0, pb)]
    if abs(pm) > 1e-9:
        interest.append((-pb / pm, 0))
    if tri and len(lines_to_draw) == 1:
        interest.append((tri["x1"], tri["y1"]))
    xs_i = [p[0] for p in interest] + [0]
    ys_i = [p[1] for p in interest] + [0]
    xpad = max(3.0, (max(xs_i) - min(xs_i)) * 0.4)
    ypad = max(3.0, (max(ys_i) - min(ys_i)) * 0.4)
    xlo, xhi = min(xs_i) - xpad, max(xs_i) + xpad
    ylo, yhi = min(ys_i) - ypad, max(ys_i) + ypad
    for m, b, eq, color, show_label in lines_to_draw:
        xs, ys = viz.get_graph_data(m, b, x_range=(xlo, xhi))
        ax.plot(xs, ys, color=color, linewidth=3.0 if show_label else 2.0,
                label=(eq if show_label else None), solid_capstyle="round",
                alpha=1.0 if show_label else 0.6, zorder=4)
    if tri and len(lines_to_draw) == 1:
        x0, y0, x1, y1 = tri["x0"], tri["y0"], tri["x1"], tri["y1"]
        ax.plot([x0, x1], [y0, y0], color="#D86A5C", linewidth=2.0, linestyle=(0, (5, 3)), zorder=3)
        ax.plot([x1, x1], [y0, y1], color="#D86A5C", linewidth=2.0, linestyle=(0, (5, 3)), zorder=3)
        ax.annotate(f"run = {tri['run']}", xy=((x0 + x1) / 2, y0), color="#D86A5C",
                    fontsize=11, ha="center", va="top", fontweight="bold",
                    xytext=(0, -6), textcoords="offset points")
        ax.annotate(f"rise = {tri['rise']}", xy=(x1, (y0 + y1) / 2), color="#D86A5C",
                    fontsize=11, ha="left", va="center", fontweight="bold",
                    xytext=(6, 0), textcoords="offset points")
    for i, pt in enumerate(points):
        color = "#16A55A" if i == 0 else "#a78bfa"
        ax.scatter([pt[0]], [pt[1]], s=110, color=color, edgecolors="white",
                   linewidths=1.6, zorder=6)
        ax.annotate(f"({_fmt(pt[0])}, {_fmt(pt[1])})", xy=pt, color=color, fontsize=11,
                    fontweight="bold", ha="left", va="bottom",
                    xytext=(8, 7), textcoords="offset points", zorder=7)
    if isinstance(viz, PerpendicularLineVisualizer):
        ax.scatter([viz.point[0]], [viz.point[1]], s=150, color="#C99A2E", marker="D",
                   edgecolors="white", linewidths=1.5, zorder=6)
    ax.set_xlabel("x", color=FG, fontsize=12)
    ax.set_ylabel("y", color=FG, fontsize=12, rotation=0, labelpad=12)
    ax.tick_params(colors=AXIS, labelsize=11)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    if any(l[4] for l in lines_to_draw):
        leg = ax.legend(loc="upper left", facecolor=PANEL_BG, edgecolor=GRID,
                        labelcolor=FG, fontsize=12, framealpha=0.95)
        leg.set_zorder(8)
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ylo, yhi)


def _viz_from_engine(engine):
    """Construct the matching visualizer from a parsed engine, or None."""
    t = engine.problem_type
    p = engine.params or {}
    try:
        if t == "slope_intercept":
            return SlopeInterceptVisualizer(p["m"], p["point"])
        if t == "two_point_line":
            return TwoPointLineVisualizer(p["p1"], p["p2"])
        if t == "point_slope":
            return PointSlopeVisualizer(p["m"], p["point"])
        if t == "parallel_line":
            return ParallelLineVisualizer(p["orig_m"], p.get("orig_b"), p["point"])
        if t == "perpendicular_line":
            return PerpendicularLineVisualizer(p["orig_m"], p.get("orig_b"), p["point"])
        if t == "quadratic":
            return QuadraticVisualizer(p["a"], p["b"], p["c"])
        if t == "system_of_equations":
            return SystemOfEquationsVisualizer(p["lines"][0], p["lines"][1])
        if t == "trig_triangle":
            return TriangleTrigVisualizer(p.get("opposite"), p.get("adjacent"), p.get("hyp"))
        if t == "unit_circle":
            return UnitCircleVisualizer(p["angle"])
        if t == "trig_wave":
            return TrigWaveVisualizer(p.get("trig_fn") or "sin")
        if t == "derivative":
            return DerivativeVisualizer(p["func"], p.get("x0") or 0.0)
        if t == "integral":
            return IntegralVisualizer(p["func"], p["a"], p["b"])
        if t == "vector_basic":
            return VectorVisualizer(p.get("v1"), p.get("v2"))
    except Exception:
        return None
    return None


def build_record_figure(rec, lang="en", figsize=(8.0, 6.4)):
    """Build a Matplotlib Figure for a simulation record, or None if the record
    is not graphable. Used by the Simulation Studio's big graph pane."""
    if Figure is None or rec is None:
        return None
    if not rec.get("graph_required"):
        return None
    q = rec.get("normalized_question") or rec.get("question_text") or ""
    try:
        engine = VisualMathEngine(q)
        if not engine.is_supported():
            return None
        viz = _viz_from_engine(engine)
    except Exception:
        return None
    if viz is None:
        return None
    try:
        fig = Figure(figsize=figsize, dpi=120, facecolor=BG)
        if hasattr(viz, "render_figure"):
            viz.render_figure(fig, lang=lang, real_life=False)
        else:
            ax = fig.add_subplot(111)
            _draw_linear_on_ax(ax, viz)
        return fig
    except Exception:
        return None


# ===========================================================================
# Simulation Studio — large, resizable window for the library + big graph
# ===========================================================================
class SimulationStudioWindow(tk.Toplevel):
    """Hosts the full simulation/formula library (Treeview + rich preview,
    reused from the parent VisualMathLab) alongside a large graph preview.
    Closing only hides it; re-opening focuses the same single window."""

    def __init__(self, lab, initial_tab=0):
        super().__init__(lab)
        self.lab = lab
        self._figure = None
        self._photo = None
        self._notebook = None
        self.title("Simulation Studio / Simülasyon Stüdyosu")
        try:
            self.configure(bg=BG)
        except Exception:
            pass
        self.geometry("1500x850")
        self.minsize(1200, 750)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.hide)
        self._build()
        try:
            if initial_tab and self._notebook is not None:
                self._notebook.select(initial_tab)
        except Exception:
            pass

    def _build(self):
        bar = ttk.Frame(self, style="Panel.TFrame")
        bar.pack(fill="x", padx=6, pady=(6, 2))
        for text, cmd in (
            ("Refresh", self.lab._refresh_simulation_list),
            ("Scan PDFs", self.lab._scan_course_pdfs),
            ("Rebuild Library", self.lab._rebuild_dynamic_library),
            ("Validate Library", self.lab._validate_library),
            ("Load to Visual Math Lab", self._load_to_lab),
            ("Open Source PDF", self.lab._open_simulation_pdf),
            ("Export Graph", self._export_graph),
            ("Generate Lesson Card", self._generate_lesson_card),
        ):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=2)
        ttk.Button(bar, text="Close", command=self.hide).pack(side="right", padx=2)

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=6, pady=6)

        nb_holder = ttk.Frame(body, style="Panel.TFrame")
        body.add(nb_holder, weight=3)
        # Reuse the lab's tested Treeview + preview notebook, built right here.
        self.lab._build_course_simulation_ui(nb_holder)
        self._notebook = getattr(self.lab, "_sim_notebook", None)

        gpane = ttk.Frame(body, style="Panel.TFrame")
        body.add(gpane, weight=3)
        ghead = ttk.Frame(gpane)
        ghead.pack(fill="x")
        ttk.Label(ghead, text="Graph Preview / Grafik Önizleme",
                  style="Header.TLabel").pack(side="left", padx=4, pady=(4, 2))
        self.graph_box = ttk.Frame(gpane)
        self.graph_box.pack(fill="both", expand=True, padx=4, pady=4)
        gbtn = ttk.Frame(gpane)
        gbtn.pack(fill="x", pady=(0, 4))
        for text, cmd in (
            ("Regenerate Graph", self._regenerate),
            ("Open Graph", self._open_graph),
            ("Export PNG", self._export_graph),
            ("Generate Lesson Card", self._generate_lesson_card),
            ("Pop Out Graph", self._popout),
        ):
            ttk.Button(gbtn, text=text, command=cmd).pack(side="left", padx=2)

        try:
            self.lab._refresh_simulation_list()
            self.lab._refresh_formula_list()
        except Exception:
            pass
        self.render_graph(self._current_rec())

    def select_tab(self, idx):
        try:
            if self._notebook is not None:
                self._notebook.select(idx)
        except Exception:
            pass

    def _current_rec(self):
        lst = getattr(self.lab, "_sim_list", [])
        idx = getattr(self.lab, "_sim_selected_index", -1)
        if 0 <= idx < len(lst):
            return lst[idx]
        return None

    def render_graph(self, rec):
        """Big graph pane: saved PNG if present, else re-render via the engine,
        else a clear placeholder."""
        for ch in self.graph_box.winfo_children():
            ch.destroy()
        self._figure = None
        if not rec:
            self._placeholder("Select a simulation to preview its graph.\n"
                              "Grafiği görmek için bir simülasyon seçin.")
            return
        png = rec.get("graph_png_path")
        if png:
            p = Path(png) if Path(png).is_absolute() else (EXPORTS_DIR / png)
            if p.exists():
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(str(p))
                    img.thumbnail((1000, 760))
                    self._photo = ImageTk.PhotoImage(img)
                    tk.Label(self.graph_box, image=self._photo, bg=BG).pack(fill="both", expand=True)
                    return
                except Exception:
                    pass
        fig = build_record_figure(rec, getattr(self.lab, "_lang", "en"), figsize=(8.4, 6.8))
        if fig is None:
            self._placeholder("Graph is not available for this simulation.\n"
                              "Bu simülasyon için grafik mevcut değil.")
            return
        self._figure = fig
        if FigureCanvasTkAgg is not None:
            canvas = FigureCanvasTkAgg(fig, master=self.graph_box)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

    def _placeholder(self, msg):
        tk.Label(self.graph_box, text=msg, bg=BG, fg=AXIS,
                 font=("Segoe UI", 12), justify="center").pack(fill="both", expand=True)

    def _regenerate(self):
        self.render_graph(self._current_rec())

    def _open_graph(self):
        if self._figure is None:
            messagebox.showinfo("Simulation Studio", "No graph to open.")
            return
        try:
            out = GRAPHS_DIR / "_studio_graph.png"
            self._figure.savefig(str(out), facecolor=BG, dpi=150)
            os.startfile(str(out))
        except Exception as exc:
            messagebox.showerror("Simulation Studio", str(exc))

    def _export_graph(self):
        if self._figure is None:
            messagebox.showinfo("Simulation Studio", "No graph to export.")
            return
        rec = self._current_rec() or {}
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG files", "*.png")],
            initialdir=str(GRAPHS_DIR),
            initialfile=_slugify(rec.get("id") or "studio_graph") + ".png")
        if path:
            try:
                self._figure.savefig(path, facecolor=BG, dpi=150)
                messagebox.showinfo("Simulation Studio", f"Saved:\n{path}")
            except Exception as exc:
                messagebox.showerror("Simulation Studio", str(exc))

    def _popout(self):
        if self._figure is None:
            messagebox.showinfo("Simulation Studio", "No graph to pop out.")
            return
        try:
            out = GRAPHS_DIR / "_studio_popout.png"
            self._figure.savefig(str(out), facecolor=BG, dpi=150)
            os.startfile(str(out))
        except Exception:
            pass

    def _generate_lesson_card(self):
        rec = self._current_rec()
        if not rec:
            messagebox.showinfo("Simulation Studio", "Select a simulation first.")
            return
        try:
            from visual_lesson_card import VisualLessonCardGenerator
            gen = VisualLessonCardGenerator(lang=getattr(self.lab, "_lang", "en"))
            path = gen.generate_from_record(rec, lang=getattr(self.lab, "_lang", "en"))
            os.startfile(path)
        except Exception as exc:
            messagebox.showerror("Simulation Studio", f"Lesson card failed:\n{exc}")

    def _load_to_lab(self):
        rec = self._current_rec()
        if not rec:
            messagebox.showinfo("Simulation Studio", "Select a simulation first.")
            return
        try:
            self.lab.load_simulation_payload(rec)
        except Exception as exc:
            messagebox.showerror("Simulation Studio", f"Load failed:\n{exc}")
            return
        try:
            self.lab.winfo_toplevel().lift()
            self.lab.winfo_toplevel().focus_force()
        except Exception:
            pass

    def hide(self):
        try:
            self.withdraw()
        except Exception:
            pass
