# -*- coding: utf-8 -*-
"""
Visual Lesson Card Generator for Visual Math Lab.

Produces high-resolution, poster-quality educational PNG cards (header,
equation transformation, clean coordinate graph with marked points and a
slope triangle, and explanation / note / final-answer boxes).

Self-contained: depends only on matplotlib (Agg backend) so it can run
head-less in tests. It deliberately does NOT import visual_math_lab to keep
the dependency one-directional and avoid circular imports.

Turkish glyphs (ş ğ ı İ ç ö ü) render correctly with the default DejaVu Sans
font that ships with matplotlib.
"""

import re
import math
from pathlib import Path
from fractions import Fraction

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.patches import FancyBboxPatch

from app_paths import exports_dir as _exports_dir

EXPORTS_DIR = _exports_dir()
LESSON_CARDS_DIR = EXPORTS_DIR / "lesson_cards"

# ---- Light "education poster" palette ------------------------------------
PAGE_BG = "#ffffff"
HEADER_BG = "#1f3b63"
HEADER_FG = "#ffffff"
HEADER_SUB = "#cfe0f5"
INK = "#10202f"
MUTED = "#4b5b6b"
LINE_C = "#2563eb"
GREEN = "#16a34a"
RED = "#dc2626"
PURPLE = "#7c3aed"
CYAN = "#0891b2"
GRID_C = "#dbe4ee"
AXIS_C = "#334155"

BOX_STYLES = {
    "points": ("#eef4ff", "#2563eb", "#1e3a8a"),
    "slope": ("#fff5e6", "#d97706", "#92400e"),
    "explain": ("#eafaf1", "#16a34a", "#14532d"),
    "note": ("#f5f3ff", "#7c3aed", "#4c1d95"),
    "answer": (HEADER_BG, HEADER_BG, "#ffffff"),
    "plain": ("#f1f5f9", "#94a3b8", "#0f2233"),
}

TITLES = {
    "line": ("DOĞRU GRAFİĞİ", "LINE GRAPH"),
    "slope_intercept": ("DOĞRU GRAFİĞİ", "LINE GRAPH"),
    "point_slope": ("DOĞRU GRAFİĞİ", "LINE GRAPH"),
    "two_point_line": ("DOĞRU GRAFİĞİ", "LINE GRAPH"),
    "parallel_line": ("PARALEL DOĞRU", "PARALLEL LINE"),
    "perpendicular_line": ("DİK DOĞRU", "PERPENDICULAR LINE"),
    "quadratic": ("PARABOL", "PARABOLA"),
    "system_of_equations": ("DENKLEM SİSTEMİ", "SYSTEM OF EQUATIONS"),
    "concept": ("KAVRAM KARTI", "CONCEPT CARD"),
}

LINE_TYPES = {"slope_intercept", "point_slope", "two_point_line",
              "parallel_line", "perpendicular_line", "line"}


def _n(v):
    """Format a number: integers without trailing .0, else up to 2 decimals."""
    try:
        f = float(v)
    except Exception:
        return str(v)
    if abs(f - round(f)) < 1e-9:
        return str(int(round(f)))
    return f"{f:.2f}".rstrip("0").rstrip(".")


def _frac(v):
    try:
        fr = Fraction(float(v)).limit_denominator(50)
        if fr.denominator == 1:
            return str(fr.numerator)
        return f"{fr.numerator}/{fr.denominator}"
    except Exception:
        return _n(v)


def _slugify(s):
    s = (s or "card").lower().replace("²", "2").replace("√", "sqrt")
    s = s.replace("+", "plus").replace("-", "minus").replace("/", "over").replace("=", "eq")
    s = re.sub(r"[^0-9a-z]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")[:60] or "card"


def _eq_line(m, b):
    ms = _frac(m)
    if abs(float(b)) < 1e-9:
        return f"y = {ms}x"
    sign = "+" if b >= 0 else "-"
    return f"y = {ms}x {sign} {_frac(abs(b))}"


class VisualLessonCardGenerator:
    """Render poster-quality lesson cards and save them as high-DPI PNGs."""

    def __init__(self, out_dir=None, lang="en", dpi=200):
        self.out_dir = Path(out_dir) if out_dir else LESSON_CARDS_DIR
        self.lang = lang
        self.dpi = dpi
        try:
            self.out_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Public entry points
    # ------------------------------------------------------------------ #
    def generate_from_visualizer(self, viz, problem_type, title=None, lang=None):
        """Build a card from a live visualizer object (best quality for lines)."""
        lang = lang or self.lang
        pt = problem_type or ""
        if pt in LINE_TYPES and hasattr(viz, "m"):
            m = getattr(viz, "m", None)
            if pt in ("parallel_line", "perpendicular_line"):
                m = getattr(viz, "new_m", m)
                b = getattr(viz, "new_b", getattr(viz, "b", 0.0))
            else:
                b = getattr(viz, "b", 0.0)
            given = []
            if hasattr(viz, "p1") and hasattr(viz, "p2"):
                given = [tuple(viz.p1), tuple(viz.p2)]
            elif getattr(viz, "point", None) is not None:
                given = [tuple(viz.point)]
            eq_final = getattr(viz, "equation_str", None) or getattr(viz, "new_eq", None) \
                or getattr(viz, "slope_intercept", None) or _eq_line(m, b)
            eq_transform = self._transform_for(viz, pt, m, b)
            return self.generate_line_card(
                m=m, b=b, given_points=given, title=title, eq_final=eq_final,
                eq_transform=eq_transform, problem_type=pt, lang=lang)
        # Non-line: concept-style poster using the visualizer's own step text.
        steps = ""
        try:
            steps = viz.build_steps(lang)
        except Exception:
            pass
        return self.generate_concept_card(
            title=title or TITLES.get(pt, TITLES["concept"])[1],
            question="", solution=steps,
            answer=getattr(viz, "equation_str", ""), problem_type=pt, lang=lang)

    def generate_from_record(self, record, lang=None):
        """Build a card from a simulation/embedded record dict."""
        lang = lang or self.lang
        pt = record.get("problem_type", "")
        params = record.get("parameters", {}) or {}
        title = record.get("title")
        if pt in LINE_TYPES:
            m = params.get("m")
            b = params.get("b")
            given = []
            if params.get("point") is not None:
                given = [tuple(params["point"])]
            elif params.get("p1") and params.get("p2"):
                given = [tuple(params["p1"]), tuple(params["p2"])]
            if m is not None and b is None and given:
                b = given[0][1] - float(m) * given[0][0]
            if m is not None and b is not None:
                return self.generate_line_card(
                    m=m, b=b, given_points=given, title=title,
                    eq_final=record.get("answer") or _eq_line(m, b),
                    eq_transform=None, problem_type=pt, lang=lang)
        # Fallback: concept poster from the record's curated text.
        return self.generate_concept_card(
            title=title or "Lesson Card",
            question=record.get("question_text", ""),
            solution=record.get("solution_text", ""),
            answer=record.get("answer") or record.get("alternate_answer") or "",
            problem_type=pt, lang=lang)

    # Type-specific helpers (line is full quality; the rest reuse the
    # concept/line renderers for now — see TODO in generate_quadratic_card).
    def generate_system_card(self, *a, **k):
        return self.generate_concept_card(*a, **k)

    def generate_quadratic_card(self, *a, **k):
        # TODO: dedicated parabola card (vertex, roots, axis of symmetry).
        return self.generate_concept_card(*a, **k)

    def generate_geometry_card(self, *a, **k):
        return self.generate_concept_card(*a, **k)

    # ------------------------------------------------------------------ #
    # Line lesson card (full quality)
    # ------------------------------------------------------------------ #
    def generate_line_card(self, *, m, b, given_points=None, title=None,
                           eq_final=None, eq_transform=None,
                           problem_type="line", lang="en", filename=None):
        m = float(m)
        b = float(b)
        given_points = [tuple(float(c) for c in p) for p in (given_points or [])]
        eq_final = eq_final or _eq_line(m, b)
        tr_tr, tr_en = TITLES.get(problem_type, TITLES["line"])

        y_int = (0.0, b)
        x_int = (-b / m, 0.0) if abs(m) > 1e-9 else None
        run, rise = self._run_rise(m)
        second_pt = (float(run), b + float(rise)) if run else None

        fig = Figure(figsize=(14, 9), dpi=self.dpi, facecolor=PAGE_BG)
        axbg = fig.add_axes([0, 0, 1, 1])
        axbg.set_xlim(0, 1)
        axbg.set_ylim(0, 1)
        axbg.axis("off")

        # --- A. Header band ---
        axbg.add_patch(FancyBboxPatch((0, 0.905), 1.0, 0.095, boxstyle="square,pad=0",
                                      facecolor=HEADER_BG, edgecolor="none",
                                      transform=axbg.transAxes, zorder=1))
        axbg.text(0.035, 0.952, tr_tr if lang == "tr" else tr_en, color=HEADER_FG,
                  fontsize=30, fontweight="bold", va="center", ha="left")
        axbg.text(0.035, 0.921, (tr_en if lang == "tr" else tr_tr), color=HEADER_SUB,
                  fontsize=14, va="center", ha="left")
        if title:
            axbg.text(0.965, 0.94, title, color=HEADER_SUB, fontsize=12.5,
                      va="center", ha="right", style="italic", wrap=True)

        # --- B. Equation transformation strip ---
        transform = eq_transform or eq_final
        axbg.text(0.5, 0.866, transform, color=INK, fontsize=19, fontweight="bold",
                  va="center", ha="center")

        # --- C. Main graph (large, left) ---
        axg = fig.add_axes([0.045, 0.305, 0.52, 0.495])
        self._draw_line_graph(axg, m, b, given_points, y_int, x_int,
                              run, rise, second_pt, eq_final)

        # --- D. Important points (right, top) ---
        pts_lines = [("y-intercept / y-kesişimi", f"(0, {_n(b)})", GREEN)]
        if x_int is not None:
            pts_lines.append(("x-intercept / x-kesişimi", f"({_n(x_int[0])}, 0)", RED))
        for i, gp in enumerate(given_points):
            lab = "given point / verilen nokta" if len(given_points) == 1 else f"point {i+1} / nokta {i+1}"
            pts_lines.append((lab, f"({_n(gp[0])}, {_n(gp[1])})", PURPLE))
        if second_pt is not None:
            pts_lines.append(("second point / ikinci nokta", f"({_n(second_pt[0])}, {_n(second_pt[1])})", CYAN))
        self._point_box(axbg, 0.59, 0.58, 0.385, 0.22,
                        "ÖNEMLİ NOKTALAR / IMPORTANT POINTS" if lang == "tr" else "IMPORTANT POINTS",
                        pts_lines)

        # --- E. Slope / concept box (right, middle) ---
        slope_lines = [
            f"m = {_frac(m)}",
            f"slope = rise / run = {_n(rise)} / {_n(run)}" if run else f"slope = {_frac(m)}",
        ]
        if m < 0:
            slope_lines.append("x 1 artarken y {0} azalır".format(_n(abs(m))) if lang == "tr"
                               else f"as x increases by 1, y decreases by {_n(abs(m))}")
        else:
            slope_lines.append("x 1 artarken y {0} artar".format(_n(abs(m))) if lang == "tr"
                               else f"as x increases by 1, y increases by {_n(abs(m))}")
        self._text_box(axbg, 0.59, 0.425, 0.385, 0.13, "slope",
                       "EĞİM / SLOPE" if lang == "tr" else "SLOPE", slope_lines)

        # --- H. Final answer box (right, prominent) ---
        self._answer_box(axbg, 0.59, 0.295, 0.385, 0.115,
                         "DOĞRU DENKLEMİ / FINAL ANSWER" if lang == "tr" else "FINAL ANSWER",
                         eq_final)

        # --- F. Explanation + G. Note (full-width bottom strip) ---
        if lang == "tr":
            explain = ["Bu grafik bir doğrudur.", "Başlangıç/bitiş noktası yoktur.",
                       "Doğru sonsuza uzanır.", "Çizmek için iki nokta yeterlidir."]
            note = ["x ve y değişkendir.", "Doğru üzerindeki her nokta denklemi sağlar."]
            ex_t, no_t = "AÇIKLAMA / EXPLANATION", "NOT / NOTE"
        else:
            explain = ["This graph is a straight line.", "It has no start or end point.",
                       "The line extends to infinity.", "Two points are enough to draw it."]
            note = ["x and y are variables.", "Every point on the line satisfies the equation."]
            ex_t, no_t = "EXPLANATION", "NOTE"
        self._text_box(axbg, 0.045, 0.03, 0.52, 0.235, "explain", ex_t, explain, body_size=13)
        self._text_box(axbg, 0.59, 0.03, 0.385, 0.235, "note", no_t, note, body_size=13)

        return self._finalize(fig, filename, problem_type, eq_final)

    # ------------------------------------------------------------------ #
    # Concept lesson card (text poster fallback)
    # ------------------------------------------------------------------ #
    def generate_concept_card(self, *, title=None, question="", solution="",
                              answer="", problem_type="concept", lang="en", filename=None):
        tr_tr, tr_en = TITLES.get(problem_type, TITLES["concept"])
        fig = Figure(figsize=(14, 9), dpi=self.dpi, facecolor=PAGE_BG)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(FancyBboxPatch((0, 0.905), 1.0, 0.095, boxstyle="square,pad=0",
                                    facecolor=HEADER_BG, edgecolor="none", zorder=1))
        ax.text(0.035, 0.952, tr_tr if lang == "tr" else tr_en, color=HEADER_FG,
                fontsize=30, fontweight="bold", va="center")
        ax.text(0.035, 0.921, tr_en if lang == "tr" else tr_tr, color=HEADER_SUB,
                fontsize=14, va="center")
        if title:
            ax.text(0.5, 0.862, title, color=INK, fontsize=18, fontweight="bold",
                    va="center", ha="center", wrap=True)
        if question:
            self._wrapped_box(ax, 0.05, 0.60, 0.90, 0.21, "plain",
                              "SORU / QUESTION" if lang == "tr" else "QUESTION", question)
        if solution:
            self._wrapped_box(ax, 0.05, 0.20, 0.90, 0.355, "explain",
                              "ÇÖZÜM / SOLUTION" if lang == "tr" else "SOLUTION", solution)
        if answer:
            self._answer_box(ax, 0.05, 0.03, 0.90, 0.13,
                             "CEVAP / FINAL ANSWER" if lang == "tr" else "FINAL ANSWER", str(answer))
        return self._finalize(fig, filename, problem_type, answer or title or "concept")

    # ------------------------------------------------------------------ #
    # Drawing helpers
    # ------------------------------------------------------------------ #
    def _run_rise(self, m):
        if abs(m) < 1e-9:
            return 1, 0
        fr = Fraction(m).limit_denominator(20)
        return fr.denominator, fr.numerator

    def _draw_line_graph(self, ax, m, b, given_points, y_int, x_int, run, rise, second_pt, eq_final):
        pts = [y_int] + list(given_points)
        if x_int is not None:
            pts.append(x_int)
        if second_pt is not None:
            pts.append(second_pt)
        xs = [p[0] for p in pts] + [0.0]
        ys = [p[1] for p in pts] + [0.0]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        padx = max(2.0, (xmax - xmin) * 0.45)
        pady = max(2.0, (ymax - ymin) * 0.45)
        xlo, xhi = xmin - padx, xmax + padx
        ylo, yhi = ymin - pady, ymax + pady

        ax.set_facecolor("#fbfdff")
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xlim(xlo, xhi)
        ax.set_ylim(ylo, yhi)
        ax.set_xticks(range(math.ceil(xlo), math.floor(xhi) + 1))
        ax.set_yticks(range(math.ceil(ylo), math.floor(yhi) + 1))
        ax.tick_params(colors=MUTED, labelsize=11)
        ax.grid(True, color=GRID_C, linewidth=0.9, zorder=0)

        # Bold axes through the origin with arrow heads.
        ax.annotate("", xy=(xhi, 0), xytext=(xlo, 0),
                    arrowprops=dict(arrowstyle="-|>", color=AXIS_C, linewidth=1.8), zorder=2)
        ax.annotate("", xy=(0, yhi), xytext=(0, ylo),
                    arrowprops=dict(arrowstyle="-|>", color=AXIS_C, linewidth=1.8), zorder=2)
        ax.text(xhi, -0.04 * (yhi - ylo), "x", color=AXIS_C, fontsize=14, fontweight="bold", ha="right", va="top")
        ax.text(-0.02 * (xhi - xlo), yhi, "y", color=AXIS_C, fontsize=14, fontweight="bold", ha="right", va="top")

        # The line itself.
        ax.plot([xlo, xhi], [m * xlo + b, m * xhi + b], color=LINE_C, linewidth=3.4,
                solid_capstyle="round", zorder=3, label=eq_final)

        # Slope triangle from the y-intercept.
        if run:
            x0, y0 = 0.0, b
            ax.plot([x0, x0 + run], [y0, y0], color="#64748b", linewidth=2.2,
                    linestyle=(0, (5, 3)), zorder=3)
            ax.plot([x0 + run, x0 + run], [y0, y0 + rise], color="#64748b", linewidth=2.2,
                    linestyle=(0, (5, 3)), zorder=3)
            ax.text(x0 + run / 2.0, y0 - 0.05 * (yhi - ylo), f"run = {_n(run)}",
                    color="#475569", fontsize=12, ha="center", va="top", fontweight="bold")
            ax.text(x0 + run + 0.015 * (xhi - xlo), y0 + rise / 2.0, f"rise = {_n(rise)}",
                    color="#475569", fontsize=12, ha="left", va="center", fontweight="bold")

        def mark(p, color, label):
            ax.scatter([p[0]], [p[1]], s=150, color=color, edgecolors="white",
                       linewidths=1.8, zorder=6)
            ax.annotate(label, (p[0], p[1]), textcoords="offset points", xytext=(9, 9),
                        color=color, fontsize=12, fontweight="bold", zorder=7)

        mark(y_int, GREEN, f"y-int (0, {_n(b)})")
        if x_int is not None and abs(x_int[0]) > 1e-9:
            mark(x_int, RED, f"x-int ({_n(x_int[0])}, 0)")
        for gp in given_points:
            mark(gp, PURPLE, f"({_n(gp[0])}, {_n(gp[1])})")
        if second_pt is not None and abs(second_pt[0]) > 1e-9:
            ax.scatter([second_pt[0]], [second_pt[1]], s=110, color=CYAN,
                       edgecolors="white", linewidths=1.6, zorder=6)

        ax.legend(loc="upper left", fontsize=12, framealpha=0.92, edgecolor=GRID_C)

    def _rounded(self, ax, x, y, w, h, face, edge):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.006,rounding_size=0.014",
                                    facecolor=face, edgecolor=edge, linewidth=2.0,
                                    mutation_aspect=0.62, zorder=3))

    def _text_box(self, ax, x, y, w, h, style, title, lines, body_size=13, _h=None):
        if _h is not None:
            h = _h
        face, edge, tcol = BOX_STYLES[style]
        self._rounded(ax, x, y, w, h, face, edge)
        ax.text(x + 0.013, y + h - 0.028, title, color=tcol, fontsize=12.5,
                fontweight="bold", va="top", ha="left")
        ty = y + h - 0.072
        for ln in lines:
            ax.text(x + 0.018, ty, ln, color=INK, fontsize=body_size, va="top", ha="left")
            ty -= 0.040

    def _point_box(self, ax, x, y, w, h, title, point_lines):
        face, edge, tcol = BOX_STYLES["points"]
        self._rounded(ax, x, y, w, h, face, edge)
        ax.text(x + 0.013, y + h - 0.028, title, color=tcol, fontsize=12.5,
                fontweight="bold", va="top", ha="left")
        ty = y + h - 0.072
        for label, val, color in point_lines:
            ax.scatter([x + 0.025], [ty + 0.006], s=70, color=color,
                       edgecolors="white", linewidths=1.2, transform=ax.transAxes, zorder=5)
            ax.text(x + 0.045, ty, label, color=MUTED, fontsize=11, va="top", ha="left")
            ax.text(x + w - 0.015, ty, val, color=INK, fontsize=12.5, va="top",
                    ha="right", fontweight="bold")
            ty -= 0.039

    def _answer_box(self, ax, x, y, w, h, title, answer):
        face, edge, tcol = BOX_STYLES["answer"]
        self._rounded(ax, x, y, w, h, face, edge)
        ax.text(x + 0.015, y + h - 0.026, title, color=HEADER_SUB, fontsize=11.5,
                fontweight="bold", va="top", ha="left")
        ax.text(x + w / 2.0, y + h * 0.30, answer, color="#ffffff", fontsize=19,
                fontweight="bold", va="center", ha="center")

    def _wrapped_box(self, ax, x, y, w, h, style, title, text):
        face, edge, tcol = BOX_STYLES[style]
        self._rounded(ax, x, y, w, h, face, edge)
        ax.text(x + 0.013, y + h - 0.028, title, color=tcol, fontsize=12.5,
                fontweight="bold", va="top", ha="left")
        wrapped = self._wrap(text, 110)
        ax.text(x + 0.018, y + h - 0.066, wrapped, color=INK, fontsize=12.5,
                va="top", ha="left", linespacing=1.4)

    @staticmethod
    def _wrap(text, width):
        out = []
        for para in str(text).split("\n"):
            line = ""
            for word in para.split(" "):
                if len(line) + len(word) + 1 > width:
                    out.append(line)
                    line = word
                else:
                    line = (line + " " + word).strip()
            out.append(line)
        return "\n".join(out[:22])

    def _transform_for(self, viz, pt, m, b):
        if pt == "point_slope" and hasattr(viz, "point_slope_form"):
            return f"{viz.point_slope_form}    →    {getattr(viz, 'slope_intercept', _eq_line(m, b))}"
        if pt in ("parallel_line", "perpendicular_line") and hasattr(viz, "orig_eq"):
            return f"{viz.orig_eq}    →    {getattr(viz, 'new_eq', _eq_line(m, b))}"
        if pt == "two_point_line" and hasattr(viz, "p1"):
            return f"({_n(viz.p1[0])}, {_n(viz.p1[1])}) , ({_n(viz.p2[0])}, {_n(viz.p2[1])})    →    {getattr(viz, 'equation_str', _eq_line(m, b))}"
        return _eq_line(m, b)

    def _finalize(self, fig, filename, problem_type, label):
        if not filename:
            filename = f"lesson_card_{problem_type}_{_slugify(label)}.png"
        if not filename.lower().endswith(".png"):
            filename += ".png"
        path = self.out_dir / filename
        FigureCanvasAgg(fig)
        fig.savefig(str(path), facecolor=PAGE_BG, dpi=self.dpi, bbox_inches=None)
        return str(path)


if __name__ == "__main__":
    g = VisualLessonCardGenerator()
    p = g.generate_line_card(m=-5, b=6, given_points=[(2, -4)],
                             title="Algebra 1 — point-slope",
                             eq_transform="y + 4 = -5(x - 2)    →    y = -5x + 6",
                             problem_type="point_slope", lang="tr")
    print("Wrote", p)
