
# -*- coding: utf-8 -*-
"""
Math Course AI
English-only course resource tracker, PDF reader/annotator, math whiteboard, LM Studio AI helper, image problem solver, Math Data Lab, Physics-to-Math Lab, Math DNA Lab, Math Kuantum Lab, Smart Wacom Student Board, Blender-style workspace UI, scientific calculator, folder-location opener, and print helper.

Main design goals:
- Read local course resources from the folder configured in Settings
  (default: <program folder>\Resources, override with MATH_COURSE_AI_RESOURCES).
- - Provide a cleaner course-following UI.
- Provide PDF viewing with zoom, page navigation, and sidecar annotations.
- Ask a local LM Studio model about selected resources and unsolved questions.
- Keep token usage reports.

Recommended LM Studio models for this version:
- Text math model: Qwen2.5-Math-7B-Instruct-Q5_K_M.gguf loaded as qwen2.5-math-7b-instruct
- Image/vision model: Qwen2.5-VL, Qwen2-VL, LLaVA, MiniCPM-V, InternVL, Pixtral, Gemma 3, or another LM Studio vision model

Note: The AI model cannot see files directly. This program reads files locally and sends only
selected text/context to LM Studio. For attached problem images, V24 either extracts OCR text
or sends the image to a prioritized vision-capable LM Studio model, then sends the extracted problem to the math model for the final answer.
"""

import ast
import os
import re
import json
import glob
import time
import queue
import urllib.request
import urllib.error
import threading
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from fractions import Fraction
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# V48: ortak temel katman ayri modulde (bkz. mca_common.py docstring).
from mca_common import (
    APP_NAME, VERSION, DEFAULT_RESOURCE_DIR, DEFAULT_BASE_URL, DEFAULT_MODEL,
    guard_url,
    DEFAULT_MATH_MODEL, DEFAULT_SCIENCE_MODEL, DEFAULT_PHYSICS_MODEL,
    DEFAULT_CHEMISTRY_MODEL, DEFAULT_DNA_MODEL, DEFAULT_CODE_MODEL,
    DEFAULT_VISION_MODEL, ICON_FILENAME, resource_path, APP_FOLDER,
    CONFIG_PATH, PROGRESS_PATH, TOKEN_LOG_PATH, TOPIC_INFO_CACHE_PATH,
    SUPPORTED_EXTS,
    THEME, DARK_THEME, _lazy_pytesseract, safe_json_load,
    safe_json_save, now_iso, read_text_file,
    natural_key, is_ignored_resource, course_key,
    safe_output_tokens, RoundedButton,
)

# Visual Math Lab bilerek burada import EDILMEZ: modulu sympy+matplotlib'i
# tepede yukledigi icin tek basina ~1.5 sn tutuyor ve bu bedel, sekmesini hic
# acmayan kullanici dahil her acilista odeniyordu. Import + panel kurulumu
# artik sekme ilk secildiginde yapilir (_ensure_visual_math_lab).

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


try:
    import numpy as np
except Exception:
    np = None

try:
    import cv2
except Exception:
    cv2 = None

# Bilingual UI text. English keys are stable for old config compatibility.
UI_TEXT = {
    "en": {
        "settings":"Settings", "setting_menu":"Setting", "language":"Language / Dil", "refresh_resources":"Refresh Resources", "token_reports":"Token Reports", "api_test":"API Test", "ai_terminal":"🖥 AI Terminal", "token_ledger":"📒 Token Ledger", "user_guide":"🎓 User Guide", "about":"ℹ About", "backup_health":"💾 Backup status", "guide_opened":"Guide opened in your browser", "guide_failed":"Guide could not be opened: {err}",
        "toggle_tracker":"Toggle Tracker", "toggle_resources":"Toggle Resources", "workspace_manager":"Workspace Manager", "workspace":"Workspace:", "layout_mode":"Layout", "layout_x_plus":"Classic — resources left", "layout_x_minus":"Mirror — resources right", "layout_dual":"Dual — two reader windows", "layout_btn_classic":"Classic", "layout_btn_mirror":"Mirror", "layout_btn_dual":"Dual Window", "labs_group":"Labs ▾",
        "startup_view":"Startup screen", "startup_last":"Last session", "startup_today":"Today dashboard",
        "welcome_title":"Welcome! 🎓", "welcome_intro":"No course PDFs in this folder yet.\nThree ways to get started:",
        "welcome_step1":"1) Put your course PDFs in the folder above, or pick another folder:", "welcome_browse":"📁 Choose course folder",
        "welcome_step2":"2) Optional: connect the local AI (LM Studio).\nEverything except AI answers works offline without it.", "welcome_settings":"🤖 Open AI settings",
        "welcome_step3":"3) No PDFs at hand? Start solving right away with the\nbuilt-in question packs (unlimited, bilingual, no license worries):", "welcome_packs":"📦 Open Question Packs",
        "welcome_guide_text":"Want the full tour? The guide explains every screen\nin why → result → benefit form:", "welcome_guide":"🎓 Open the user guide",
        "ai_status_checking":"⏳ AI…", "ai_status_on":"🟢 AI ready", "ai_status_off":"🔴 AI off (offline features work)", "ai_status_no_model":"🟡 AI server up, no model loaded",
        "labs_tab":"🧪 Labs",
        "theme_mode":"Theme", "theme_light":"☀ Light", "theme_dark":"🌙 Dark",
        "theme_saved":"Theme saved — restart to apply / Tema kaydedildi, yeniden başlatınca uygulanır",
        "course_resources":"Course Resources", "pdf_reader":"PDF Reader / Annotator", "ai_tutor":"AI Tutor", "smart_wacom":"Smart Tablet Drawing Board", "calculator":"Calculator",
        "data_lab":"Math Data Lab", "physics_lab":"Physics → Math Lab", "chemistry_lab":"Chemistry → Math Lab", "dna_lab":"Math DNA Lab", "quantum_lab":"Math Quantum Lab", "dictionary":"Science Dictionary", "visual_math_lab":"Visual Math Lab", "student_tracker":"Student Tracker",
        "course_resources_full":"Course Resources / Kurs Kaynakları", "calculator_full":"Calculator / Hesap Makinesi", "dictionary_full":"Science Dictionary / Bilim Sözlüğü", "visual_math_lab_full":"Visual Math Lab / Görsel Matematik Laboratuvarı", "student_tracker_full":"Student Tracker / Öğrenci Takip",
        "browse":"Browse", "search":"Search", "open_resource":"Open Resource", "read_show":"Read / Show", "open_folder_location":"Open Folder Location", "print":"Print",
        "course_tracker":"Course Tracker", "track_progress":"Track progress, difficulty, and feedback.", "save_progress":"Save Progress", "open_token_log_folder":"Open Token Log Folder", "open_resources_folder":"Open Resources Folder",
        "question_topic":"Question / Topic You Do Not Understand", "attach_image":"Attach PNG/JPEG Problem Image", "clear_image":"Clear Image", "no_image":"No image attached.",
        "ask_ai_resource":"Ask AI About Selected Resource", "solve_question":"Solve Question", "solve_image":"Solve Attached Image", "feedback_report":"Create Feedback Report", "clear":"Clear", "ai_answer":"AI / Solver Answer",
        "apply":"Apply", "reset_default":"Reset Default", "close":"Close", "save":"Save", "lookup":"Lookup", "ask_ai_term":"Ask AI About This Term",
        "select_visible":"Select which workspace shortcut buttons should be visible. Use the × on the Screen UI bar to hide a section quickly.",
        "at_least_one":"At least one workspace must remain visible.", "bar_updated":"Workspace bar updated.", "hidden_status":"Workspace hidden: {label}. Reopen it from Settings > Workspace Manager.", "shown_status":"Workspace shown: {label}.",
        "language_saved":"Language saved. Restart the program to refresh every static label.", "dictionary_hint":"Choose Mathematics, Physics, DNA, or Chemistry, then search in English or Turkish. Explanations are built into the program; no AI call is needed."
    },
    "tr": {
        "settings":"Ayarlar", "setting_menu":"Ayar", "language":"Dil / Language", "refresh_resources":"Kaynakları Yenile", "token_reports":"Token Raporları", "api_test":"API Test", "ai_terminal":"🖥 AI Terminali", "token_ledger":"📒 Token Defteri", "user_guide":"🎓 Kullanma Kılavuzu", "about":"ℹ Hakkında", "backup_health":"💾 Yedek durumu", "guide_opened":"Kılavuz tarayıcıda açıldı", "guide_failed":"Kılavuz açılamadı: {err}",
        "toggle_tracker":"Takip Panelini Aç/Kapat", "toggle_resources":"Kaynak Panelini Aç/Kapat", "workspace_manager":"Çalışma Alanı Yöneticisi", "workspace":"Çalışma Alanı:", "layout_mode":"Düzen", "layout_x_plus":"Klasik — kaynaklar solda", "layout_x_minus":"Ayna — kaynaklar sağda", "layout_dual":"Çift — iki bağımsız okuyucu penceresi", "layout_btn_classic":"Klasik", "layout_btn_mirror":"Ayna", "layout_btn_dual":"Çift Pencere", "labs_group":"Lab'lar ▾",
        "startup_view":"Açılış ekranı", "startup_last":"Son oturum", "startup_today":"Bugün panosu",
        "welcome_title":"Hoş geldin! 🎓", "welcome_intro":"Bu klasörde henüz kurs PDF'i yok.\nBaşlamak için üç yol:",
        "welcome_step1":"1) Kurs PDF'lerini yukarıdaki klasöre koy ya da başka klasör seç:", "welcome_browse":"📁 Kurs klasörünü seç",
        "welcome_step2":"2) İsteğe bağlı: yerel yapay zekâyı bağla (LM Studio).\nAI cevapları dışında her şey onsuz da çevrimdışı çalışır.", "welcome_settings":"🤖 AI ayarlarını aç",
        "welcome_step3":"3) Elinde PDF yok mu? Yerleşik soru paketleriyle hemen\nçözmeye başla (sınırsız, iki dilli, telif derdi yok):", "welcome_packs":"📦 Soru Paketleri'ni aç",
        "welcome_guide_text":"Tam turu ister misin? Kılavuz her ekranı\nneden → sonuç → fayda biçiminde anlatır:", "welcome_guide":"🎓 Kullanma kılavuzunu aç",
        "ai_status_checking":"⏳ AI…", "ai_status_on":"🟢 AI hazır", "ai_status_off":"🔴 AI kapalı (offline özellikler çalışır)", "ai_status_no_model":"🟡 AI sunucu açık, model yüklü değil",
        "labs_tab":"🧪 Lab'lar",
        "theme_mode":"Tema", "theme_light":"☀ Açık", "theme_dark":"🌙 Koyu",
        "theme_saved":"Tema kaydedildi — yeniden başlatınca uygulanır / restart to apply",
        "course_resources":"Kurs Kaynakları", "pdf_reader":"PDF Okuyucu / Not Alma", "ai_tutor":"Yapay Zeka Öğretmen", "smart_wacom":"Akıllı Tablet Çizim Tahtası", "calculator":"Hesap Makinesi",
        "data_lab":"Matematik Veri Laboratuvarı", "physics_lab":"Fizik → Matematik Laboratuvarı", "chemistry_lab":"Kimya → Matematik Laboratuvarı", "dna_lab":"Matematik DNA Laboratuvarı", "quantum_lab":"Matematik Kuantum Laboratuvarı", "dictionary":"Bilim Sözlüğü", "visual_math_lab":"Görsel Matematik Laboratuvarı", "student_tracker":"Öğrenci Takip",
        "course_resources_full":"Course Resources / Kurs Kaynakları", "calculator_full":"Calculator / Hesap Makinesi", "dictionary_full":"Science Dictionary / Bilim Sözlüğü", "visual_math_lab_full":"Visual Math Lab / Görsel Matematik Laboratuvarı", "student_tracker_full":"Student Tracker / Öğrenci Takip",
        "browse":"Gözat", "search":"Ara", "open_resource":"Kaynağı Aç", "read_show":"Oku / Göster", "open_folder_location":"Klasör Konumu Aç", "print":"Yazdır",
        "course_tracker":"Kurs Takibi", "track_progress":"İlerleme, zorluk ve geri bildirimi takip et.", "save_progress":"İlerlemeyi Kaydet", "open_token_log_folder":"Token Log Klasörünü Aç", "open_resources_folder":"Kaynak Klasörünü Aç",
        "question_topic":"Anlamadığın Soru / Konu", "attach_image":"PNG/JPEG Soru Görseli Ekle", "clear_image":"Görseli Temizle", "no_image":"Görsel eklenmedi.",
        "ask_ai_resource":"Seçili Kaynağı AI'a Sor", "solve_question":"Soruyu Çöz", "solve_image":"Ekli Görseli Çöz", "feedback_report":"Geri Bildirim Raporu Oluştur", "clear":"Temizle", "ai_answer":"AI / Çözücü Cevabı",
        "apply":"Uygula", "reset_default":"Varsayılana Dön", "close":"Kapat", "save":"Kaydet", "lookup":"Sorgula", "ask_ai_term":"Bu Terimi AI'a Sor",
        "select_visible":"Screen UI çubuğunda hangi çalışma alanı butonlarının görüneceğini seç. Bir bölümü hızlı gizlemek için çubuktaki × işaretini kullan.",
        "at_least_one":"En az bir çalışma alanı görünür kalmalıdır.", "bar_updated":"Çalışma alanı çubuğu güncellendi.", "hidden_status":"Çalışma alanı gizlendi: {label}. Yeniden açmak için Ayarlar > Çalışma Alanı Yöneticisi'ni kullan.", "shown_status":"Çalışma alanı gösterildi: {label}.",
        "language_saved":"Dil ayarı kaydedildi. Tüm sabit etiketlerin yenilenmesi için programı yeniden başlat.", "dictionary_hint":"Önce Matematik, Fizik, DNA veya Kimya sözlüğünü seç; sonra İngilizce ya da Türkçe terimi ara. Açıklamalar programın içinde hazırdır; AI çağrısı yapılmaz."
    },
}
WORKSPACE_KEYS = ["CourseResources", "PDF", "AI", "Wacom", "Calculator", "Data", "Physics", "Chemistry", "DNA", "Quantum", "Dictionary", "VisualMath", "StudentTracker"]
# The five science labs are shown as ONE "Lab'lar ▾" chip on the workspace bar
# so the bar stays readable; each lab is still its own workspace/tab.
LAB_WORKSPACES = ("Data", "Physics", "Chemistry", "DNA", "Quantum")
WORKSPACE_TEXT_KEYS = {"CourseResources":"course_resources_full", "PDF":"pdf_reader", "AI":"ai_tutor", "Wacom":"smart_wacom", "Calculator":"calculator_full", "Data":"data_lab", "Physics":"physics_lab", "Chemistry":"chemistry_lab", "DNA":"dna_lab", "Quantum":"quantum_lab", "Dictionary":"dictionary_full", "VisualMath":"visual_math_lab_full", "StudentTracker":"student_tracker_full"}
WORKSPACE_SHORT_TEXT_KEYS = {"CourseResources":"course_resources", "PDF":"pdf_reader", "AI":"ai_tutor", "Wacom":"smart_wacom", "Calculator":"calculator", "Data":"data_lab", "Physics":"physics_lab", "Chemistry":"chemistry_lab", "DNA":"dna_lab", "Quantum":"quantum_lab", "Dictionary":"dictionary", "VisualMath":"visual_math_lab", "StudentTracker":"student_tracker"}







# ── Arithmetic evaluation, AST-validated ───────────────────────────────────
# `eval` with an emptied __builtins__ is a speed bump, not a boundary: an
# attacker-shaped expression can still walk object internals. Both evaluators
# in this program therefore parse first and validate every node, exactly as
# calculator.ScientificCalculator._safe_eval does.
_ARITH_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Call, ast.Name,
    ast.Load, ast.Tuple,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub,
)


def _arith_eval(expr, names):
    """Evaluate a pure-arithmetic expression, or raise ValueError.

    Only numeric literals, the arithmetic operators and the callables named in
    `names` (today: Fraction) are permitted. Attribute access, subscripting,
    comprehensions, lambdas, strings and every other node type are refused.
    """
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ARITH_NODES):
            raise ValueError("Unsupported expression part: %s" % type(node).__name__)
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float, complex)):
            raise ValueError("Only numeric literals are allowed.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in names:
                raise ValueError("Only the allowed numeric helpers may be called.")
            if node.keywords:
                raise ValueError("Keyword arguments are not allowed.")
        if isinstance(node, ast.Name) and node.id not in names:
            raise ValueError("Unknown name: %s" % node.id)
    # nosec B307 - every AST node was validated above against _ARITH_NODES
    # and `names`; this is not an unchecked eval().
    return eval(compile(tree, "<arith>", "eval"), {"__builtins__": {}}, dict(names))  # nosec B307 - AST-validated above  # noqa: S307


class LocalSolver:
    """Very small local solver for simple arithmetic/fractions."""
    allowed_chars = re.compile(r"^[0-9\s\+\-\*/\(\)\.\/]+$")

    @staticmethod
    def normalize_question(q):
        q = q.strip()
        q = q.replace("×", "*").replace("÷", "/")
        q = q.replace("^", "**")
        q = re.sub(r"solve|calculate|what is|find|=|\?", "", q, flags=re.I)
        return q.strip()

    @staticmethod
    def try_solve(q):
        expr = LocalSolver.normalize_question(q)
        if not expr or not LocalSolver.allowed_chars.match(expr):
            return None
        try:
            # Fraction-friendly expression. Only digits/operators are allowed above.
            # An empty __builtins__ is a speed bump, not a boundary. Parse to an
            # AST and validate every node BEFORE evaluating, the same way
            # calculator._safe_eval does — one evaluator pattern, one review.
            if "/" in expr:
                # token-level conversion: 2/3 + 1/6 -> Fraction(2,3)+Fraction(1,6)
                expr2 = re.sub(r"(?<![\w.])(\d+)\s*/\s*(\d+)(?![\w.])", r"Fraction(\1,\2)", expr)
                val = _arith_eval(expr2, {"Fraction": Fraction})
            else:
                val = _arith_eval(expr, {})
            if isinstance(val, Fraction):
                result = f"{val.numerator}/{val.denominator}" if val.denominator != 1 else str(val.numerator)
            else:
                result = str(val)
            return f"Given\nThe question is: {q.strip()}\n\nSolution Steps\nWe simplify the expression step by step.\n\nResult\n{result}"
        except Exception:
            return None


class ResourceScanner:
    def __init__(self, root):
        self.root = Path(root)
        self.courses = []
        self.root_readme = ""

    def scan(self):
        self.courses = []
        if not self.root.exists():
            return []
        # V20: READ ME files are intentionally ignored.
        course_dirs = [p for p in self.root.iterdir() if p.is_dir() and not is_ignored_resource(p)]
        course_dirs.sort(key=lambda p: course_key(p.name))
        for cdir in course_dirs:
            course = self._scan_course(cdir)
            if course["resources"] or course["readmes"] or course["children"]:
                self.courses.append(course)
        return self.courses

    def _find_root_readme(self):
        candidates = list(self.root.glob("00 READ ME.rtf")) + list(self.root.glob("*READ*ME*.rtf"))
        if candidates:
            return read_text_file(candidates[0], 100_000)
        return ""

    def _scan_course(self, cdir):
        # V20: do not read or display READ ME.rtf / README files.
        readmes = []
        resources = []
        children = []
        for item in sorted(cdir.iterdir(), key=lambda p: (not p.is_dir(), natural_key(p.name))):
            if is_ignored_resource(item):
                continue
            if item.is_dir():
                children.append(self._scan_section(item))
            elif item.suffix.lower() in SUPPORTED_EXTS:
                resources.append(item)
        return {
            "name": cdir.name,
            "path": str(cdir),
            "readmes": [],
            "readme_text": "",
            "resources": resources,
            "children": children,
        }

    def _scan_section(self, folder):
        items = []
        subfolders = []
        for p in sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), natural_key(x.name))):
            if is_ignored_resource(p):
                continue
            if p.is_dir():
                subfolders.append(self._scan_section(p))
            elif p.suffix.lower() in SUPPORTED_EXTS:
                items.append(p)
        return {"name": folder.name, "path": str(folder), "items": items, "children": subfolders}



from lm_studio_client import LMStudioClient



from whiteboard import MathWhiteboard




from science_labs import MathDataLab, PhysicsMathLab, MathDNALab, MathQuantumLab, ChemistryMathLab








from calculator import ScientificCalculator


from pdf_viewer import ResourceMirrorPanel, PDFViewer










from classic_dictionary import EnglishTurkishDictionary

class MathCourseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} | {VERSION}")
        self.set_app_icon()
        self.geometry("1600x920")
        self.minsize(1200, 760)
        self.configure(bg=THEME["bg"])
        default_config = {
            "resource_dir": DEFAULT_RESOURCE_DIR,
            "base_url": DEFAULT_BASE_URL,
            "model": DEFAULT_MODEL,
            "math_model": DEFAULT_MATH_MODEL,
            "science_model": DEFAULT_SCIENCE_MODEL,
            "physics_model": DEFAULT_PHYSICS_MODEL,
            "chemistry_model": DEFAULT_CHEMISTRY_MODEL,
            "dna_model": DEFAULT_DNA_MODEL,
            "code_model": DEFAULT_CODE_MODEL,
            "vision_model": DEFAULT_VISION_MODEL,
            "language": "tr",
            "theme": "light",
            "startup_view": "last",
            "workspace_visible": {key: True for key in WORKSPACE_KEYS},
        }
        self.config_data = safe_json_load(CONFIG_PATH, default_config)
        self.language = self.config_data.get("language", "tr") if self.config_data.get("language", "tr") in ("tr", "en") else "tr"
        # Karanlik tema ACILISTA uygulanir: THEME sozlugu _setup_style ve
        # _build_ui'den once yerinde guncellenir; yardimci modullerin kendi
        # paletleri de degistirilir (visual_math_lab TEMBEL yuklendigi icin
        # onunki _ensure_visual_math_lab icinde yapilir — burada import etmek
        # sympy'yi acilista geri getirirdi).
        self.dark_mode = str(self.config_data.get("theme", "light")) == "dark"
        if self.dark_mode:
            THEME.update(DARK_THEME)
            self.configure(bg=THEME["bg"])  # kok bg yukarida acik renkle set edilmisti
            for _mod_name in ("student_tracker", "language_dictionary"):
                try:
                    _m = __import__(_mod_name)
                    _m.apply_dark_palette()
                except Exception:
                    pass
            try:
                # clam temasinin bilinen eksigi: Combobox acilir listesi ttk
                # stilinden etkilenmez; option database'ten ayarlanmali.
                self.option_add("*TCombobox*Listbox.background", THEME["surface"])
                self.option_add("*TCombobox*Listbox.foreground", THEME["text"])
                self.option_add("*TCombobox*Listbox.selectBackground", THEME["accent"])
                self.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
            except Exception:
                pass
        # "X Düzeni" — 3 layout modes (layout-only, no content flip), persisted:
        #   x_plus = classic (resources left, PDF right)
        #   x_minus = mirror (resources right, PDF left)
        #   dual = X+ on the left + a synced read-only PDF preview on the right
        _mode = self.config_data.get("pdf_reader_layout_mode")
        if _mode not in ("x_plus", "x_minus", "dual"):
            # Migrate the older boolean "pdf_reader_mirror_x" if present.
            _mode = "x_minus" if self.config_data.get("pdf_reader_mirror_x", False) else "x_plus"
        self.pdf_reader_layout_mode = _mode
        self.progress = safe_json_load(PROGRESS_PATH, {})
        self.client = LMStudioClient(
            self.config_data.get("base_url", DEFAULT_BASE_URL),
            self.config_data.get("model", DEFAULT_MODEL),
            self.config_data.get("vision_model", DEFAULT_VISION_MODEL),
            self.config_data,
        )
        self.scanner = ResourceScanner(self.config_data.get("resource_dir", DEFAULT_RESOURCE_DIR))
        self.courses = []
        self.path_by_iid = {}
        self.selected_path = None
        self.selected_course = None
        self.worker_busy = False
        self.uiq = queue.Queue()
        self.workspace_labels = list(WORKSPACE_KEYS)
        old_visible = self.config_data.get("workspace_visible", {label: True for label in self.workspace_labels})
        self.workspace_visible = {}
        for label in self.workspace_labels:
            self.workspace_visible[label] = bool(old_visible.get(label, True))
        self.config_data["workspace_visible"] = self.workspace_visible
        self._setup_style()
        self._build_ui()
        self._apply_panel_layout()  # apply persisted Mirror X state at startup
        self.after(120, self.process_ui_queue)
        self.refresh_resources()
        self.test_api(silent=True)
        self.after(1500, self._poll_ai_health)   # AI durum gostergesi (30 sn'de bir yineler)
        self.protocol("WM_DELETE_WINDOW", self._on_close)   # save session on quit
        self.after(500, self._restore_session)              # reopen last PDF/page/zoom/tab

    def set_app_icon(self):
        """Apply the custom math AI icon to the Tk window.

        PyInstaller also uses this same .ico file for the EXE icon via the build BAT.
        """
        try:
            icon_path = resource_path(ICON_FILENAME)
            if Path(icon_path).exists():
                self.iconbitmap(icon_path)
        except Exception:
            pass

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        # --- Surfaces & text -------------------------------------------------
        style.configure("TFrame", background=THEME["bg"])
        style.configure("Panel.TFrame", background=THEME["panel"])
        style.configure("TLabel", background=THEME["bg"], foreground=THEME["text"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=THEME["panel"], foreground=THEME["muted"], font=("Segoe UI", 9))
        style.configure("Header.TLabel", font=("Segoe UI Semibold", 14), foreground=THEME["text"], background=THEME["panel"])

        # --- Buttons: soft sand default, amber primary -----------------------
        style.configure(
            "TButton", padding=(12, 7), font=("Segoe UI Semibold", 9),
            background=THEME["panel2"], foreground=THEME["text"],
            borderwidth=1, relief="flat", focuscolor=THEME["accent_soft"],
        )
        style.map(
            "TButton",
            background=[("pressed", THEME["line"]), ("active", THEME["accent_soft"])],
            bordercolor=[("!disabled", THEME["line"])],
            foreground=[("disabled", THEME["muted"])],
        )
        style.configure("Workspace.TButton", padding=(12, 7), font=("Segoe UI Semibold", 9))
        style.configure("Calc.TButton", padding=10, font=("Segoe UI Semibold", 13), background=THEME["surface"])
        style.map("Calc.TButton", background=[("active", THEME["accent_soft"]), ("pressed", THEME["line"])])
        # Amber call-to-action button (use style="Accent.TButton" for primary actions).
        style.configure(
            "Accent.TButton", padding=(14, 8), font=("Segoe UI Semibold", 10),
            background=THEME["accent"], foreground="#FFFFFF", borderwidth=0, relief="flat",
        )
        style.map("Accent.TButton", background=[("pressed", "#C4632A"), ("active", "#EC8A4B")])
        # Green save button.
        style.configure(
            "Save.TButton", padding=(14, 8), font=("Segoe UI Semibold", 10),
            background=THEME["green"], foreground="#FFFFFF", borderwidth=0, relief="flat",
        )
        style.map("Save.TButton", background=[("pressed", "#0E8A48"), ("active", "#23B768")])

        # --- Notebook tabs: paper cards, amber active --------------------------
        style.configure("TNotebook", background=THEME["bg"], borderwidth=0, padding=4)
        style.configure(
            "TNotebook.Tab", padding=(16, 8), font=("Segoe UI Semibold", 9),
            background=THEME["panel2"], foreground=THEME["muted"], borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["panel"]), ("active", THEME["accent_soft"])],
            foreground=[("selected", THEME["accent"]), ("active", THEME["text"])],
        )

        # --- Treeview (course tree) ------------------------------------------
        style.configure(
            "Treeview", background=THEME["surface"], fieldbackground=THEME["surface"],
            foreground=THEME["text"], rowheight=26, borderwidth=0, font=("Segoe UI", 10),
        )
        style.map(
            "Treeview",
            background=[("selected", THEME["accent"])],
            foreground=[("selected", "#FFFFFF")],
        )
        style.configure(
            "Treeview.Heading", font=("Segoe UI Semibold", 9),
            background=THEME["panel2"], foreground=THEME["text"], relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", THEME["accent_soft"])])

        # --- Inputs: flat surface, 1px defined border, amber focus ring ------
        for _inp in ("TEntry", "TCombobox", "TSpinbox"):
            style.configure(
                _inp, fieldbackground=THEME["surface"], background=THEME["surface"],
                foreground=THEME["text"], bordercolor=THEME["border"],
                lightcolor=THEME["border"], darkcolor=THEME["border"],
                borderwidth=1, relief="flat", padding=6,
                arrowcolor=THEME["muted"], arrowsize=13, insertcolor=THEME["text"],
                selectbackground=THEME["accent_soft"], selectforeground=THEME["text"],
            )
            style.map(
                _inp,
                bordercolor=[("focus", THEME["accent"]), ("active", THEME["muted"])],
                lightcolor=[("focus", THEME["accent"])], darkcolor=[("focus", THEME["accent"])],
                fieldbackground=[("readonly", THEME["surface"]), ("disabled", THEME["panel2"])],
                foreground=[("disabled", THEME["muted"])],
            )
        style.map("TCombobox", foreground=[("readonly", THEME["text"])],
                  selectbackground=[("readonly", THEME["surface"])],
                  selectforeground=[("readonly", THEME["text"])])
        # --- Checkbuttons & radiobuttons: amber indicator --------------------
        for _ck in ("TCheckbutton", "TRadiobutton"):
            style.configure(_ck, background=THEME["panel"], foreground=THEME["text"],
                            font=("Segoe UI", 9), focuscolor=THEME["accent_soft"])
            style.map(_ck, background=[("active", THEME["panel"])],
                      indicatorcolor=[("selected", THEME["accent"]), ("!selected", THEME["surface"])],
                      foreground=[("disabled", THEME["muted"])])
        # --- Scrollbars: slim, flat, no 3D bevel -----------------------------
        style.configure("TScrollbar", background=THEME["panel2"], troughcolor=THEME["bg"],
                        bordercolor=THEME["bg"], lightcolor=THEME["panel2"], darkcolor=THEME["panel2"],
                        borderwidth=0, arrowcolor=THEME["muted"], arrowsize=13)
        style.map("TScrollbar", background=[("active", THEME["accent_soft"]), ("pressed", THEME["accent"])])
        style.configure("Horizontal.TProgressbar", background=THEME["accent"], troughcolor=THEME["line"],
                        bordercolor=THEME["line"], lightcolor=THEME["accent"], darkcolor=THEME["accent"], borderwidth=0)
        style.configure("Vertical.TProgressbar", background=THEME["accent"], troughcolor=THEME["line"], borderwidth=0)
        style.configure("TPanedwindow", background=THEME["bg"])

    def t(self, key):
        return UI_TEXT.get(self.language, UI_TEXT["en"]).get(key, UI_TEXT["en"].get(key, key))

    def workspace_display(self, label, short=False):
        if short:
            compact_tr = {
                "CourseResources": "Kaynaklar",
                "PDF": "PDF",
                "AI": "AI",
                "Wacom": "Tablet Çizim",
                "Calculator": "Hesap",
                "Data": "Veri Lab",
                "Physics": "Fizik Lab",
                "Chemistry": "Kimya Lab",
                "DNA": "DNA Lab",
                "Quantum": "Kuantum",
                "Dictionary": "Sözlük",
                "VisualMath": "Görsel Mat",
                "StudentTracker": "Öğrenci Takip",
            }
            compact_en = {
                "CourseResources": "Resources",
                "PDF": "PDF",
                "AI": "AI",
                "Wacom": "Tablet Drawing",
                "Calculator": "Calc",
                "Data": "Data Lab",
                "Physics": "Physics Lab",
                "Chemistry": "Chem Lab",
                "DNA": "DNA Lab",
                "Quantum": "Quantum",
                "Dictionary": "Dictionary",
                "VisualMath": "Visual Math",
                "StudentTracker": "Tracker",
            }
            compact = compact_tr if self.language == "tr" else compact_en
            return compact.get(label, label)
        text_key = WORKSPACE_TEXT_KEYS.get(label, label)
        return self.t(text_key)

    def workspace_tab_display(self, label):
        """Notebook tab label. Close a workspace from the top workspace bar's ×
        button (or middle-click the tab) — NOT by left-clicking the tab."""
        return self.workspace_display(label)

    def ai_language_instruction(self):
        if self.language == "tr":
            return "Türkçe cevap ver. Matematik öğretmeni gibi açık, adım adım ve öğrencinin seviyesine uygun anlat."
        return "Answer in English. Explain clearly, step by step, like a math tutor."

    def apply_language_to_window(self):
        try:
            self.settings_button.config(text=self.t("settings")); self.refresh_button.config(text=self.t("refresh_resources")); self.token_button.config(text=self.t("token_reports")); self.api_button.config(text=self.t("api_test"))
            self.workspace_title_label.config(text=self.t("workspace")); self.workspace_manager_button.config(text=self.t("workspace_manager")); self.toggle_resources_button.config(text=self.t("toggle_resources")); self.toggle_tracker_button.config(text=self.t("toggle_tracker"))
            if hasattr(self, "layout_mode_title"): self.layout_mode_title.config(text=self.t("layout_mode") + ":")
            self._update_layout_mode_buttons()
            self.left_header_label.config(text=self.t("course_resources")); self.search_label.config(text=self.t("search")); self.open_resource_button.config(text=self.t("open_resource")); self.read_show_button.config(text=self.t("read_show")); self.open_location_button.config(text=self.t("open_folder_location")); self.print_button.config(text=self.t("print"))
            self.tracker_header_label.config(text=self.t("course_tracker")); self.tracker_desc_label.config(text=self.t("track_progress")); self.save_progress_button.config(text=self.t("save_progress")); self.open_token_folder_button.config(text=self.t("open_token_log_folder")); self.open_resources_folder_button.config(text=self.t("open_resources_folder"))
            self.ai_question_label.config(text=self.t("question_topic")); self.attach_image_button.config(text=self.t("attach_image")); self.clear_image_button.config(text=self.t("clear_image")); self.ask_ai_resource_button.config(text=self.t("ask_ai_resource")); self.solve_question_button.config(text=self.t("solve_question")); self.solve_image_button.config(text=self.t("solve_image")); self.feedback_button.config(text=self.t("feedback_report")); self.clear_ai_button.config(text=self.t("clear")); self.ai_answer_label.config(text=self.t("ai_answer"))
            if not self.attached_image_path: self.image_label.config(text=self.t("no_image"))
            self.refresh_notebook_tabs()
        except Exception:
            pass
        try:
            # Karsilama karti goruluyorsa yeni dille bastan kurulur.
            if getattr(self, "welcome_card", None) is not None:
                self._update_welcome_card()
        except Exception:
            pass
        try:
            # AI durum gostergesi son bilinen durumla yeni dilde tazelenir.
            last = getattr(self, "_ai_health_last", None)
            if last is not None:
                self._apply_ai_health(last[0], last[1])
            elif getattr(self, "ai_status_label", None) is not None:
                self.ai_status_label.config(text=self.t("ai_status_checking"), fg=THEME["muted"])
        except Exception:
            pass
        try:
            # Tembel: sozluk henuz kurulmadiysa dil degisimi onu KURMAZ —
            # kurulunca zaten yeni dille kurulur.
            if getattr(self, "dictionary", None) is not None:
                self.dictionary.refresh_ui()
        except Exception:
            pass
        try:
            if hasattr(self, "visual_math_lab") and self.visual_math_lab is not None:
                self.visual_math_lab.refresh_ui()
        except Exception:
            pass
        self.rebuild_workspace_buttons()

    def set_language(self, lang):
        if lang not in ("tr", "en"): return
        self.language = lang
        self.config_data["language"] = lang
        safe_json_save(CONFIG_PATH, self.config_data)
        self.apply_language_to_window()
        self.set_status(self.t("language_saved"))

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(side="top", fill="x")
        tk.Label(top, text="☰", fg=THEME["muted"], bg=THEME["panel"], font=("Segoe UI", 14)).pack(side="left", padx=(12, 6), pady=10)
        tk.Label(top, text="∑", fg="#FFFFFF", bg=THEME["accent"], font=("Segoe UI", 12, "bold"), width=2, padx=2).pack(side="left", pady=10)
        tk.Label(top, text=f" {APP_NAME}", fg=THEME["text"], bg=THEME["panel"], font=("Segoe UI Semibold", 13)).pack(side="left", padx=(2, 0), pady=10)
        tk.Label(top, text=f"· {VERSION}", fg=THEME["muted"], bg=THEME["panel"], font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))
        self.status_label = tk.Label(top, text="Starting...", fg=THEME["green"], bg=THEME["panel"], font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="left", padx=18)
        # Kalici AI durum gostergesi: set_status'un surekli ezdigi status_label'in
        # aksine hep gorunur; tiklaninca API Test penceresi acilir. Sag gruba
        # ILK pack edilir (= en sag kose): pack'te alan daralinca EN SON pack
        # edilen once feda edilir — gosterge en gerekli oldugu anda (AI kapali
        # + uzun hata metni) kaybolmasin diye kurban sirasinin en sonunda.
        self.ai_status_label = tk.Label(top, text=self.t("ai_status_checking"), bg=THEME["panel"],
                                        fg=THEME["muted"], font=("Segoe UI", 9, "bold"), cursor="hand2")
        self.ai_status_label.pack(side="right", padx=(6, 14))
        self.ai_status_label.bind("<Button-1>", lambda e: self.open_api_test_window())
        self.settings_button = RoundedButton(top, text=self.t("settings"), parent_bg=THEME["panel"], bg=THEME["accent"], fg="#FFFFFF", hover="#EC8A4B", command=self.show_settings_menu)
        self.settings_button.pack(side="right", padx=6)
        self.api_button = RoundedButton(top, text=self.t("api_test"), parent_bg=THEME["panel"], command=self.test_api)
        self.api_button.pack(side="right", padx=6)
        self.token_button = RoundedButton(top, text=self.t("token_reports"), parent_bg=THEME["panel"], command=self.show_token_reports)
        self.token_button.pack(side="right", padx=6)
        self.refresh_button = RoundedButton(top, text=self.t("refresh_resources"), parent_bg=THEME["panel"], command=self.refresh_resources)
        self.refresh_button.pack(side="right", padx=6)

        # Blender-inspired customizable workspace strip: fast context switching, hide/show buttons.
        workspace = ttk.Frame(self, style="Panel.TFrame")
        self.workspace_bar = workspace
        # Compact workspace shortcut bar: visible sections appear here as clean buttons.
        # Each button includes a small × close control. Hidden sections can be restored
        # from Settings > Workspace Manager.
        workspace.pack(side="top", fill="x", padx=8, pady=(2, 0))
        self.workspace_title_label = tk.Label(workspace, text=self.t("workspace"), fg=THEME["muted"], bg=THEME["panel"], font=("Segoe UI", 9, "bold"))
        self.workspace_title_label.pack(side="left", padx=(8, 4))
        self.workspace_button_frame = ttk.Frame(workspace, style="Panel.TFrame")
        self.workspace_button_frame.pack(side="left", fill="x", expand=True)
        self.workspace_buttons = {}
        self.rebuild_workspace_buttons()
        self.workspace_manager_button = RoundedButton(workspace, text=self.t("workspace_manager"), parent_bg=THEME["panel"], radius=11, padx=12, pady=6, command=self.open_workspace_manager)
        self.workspace_manager_button.pack(side="right", padx=3)
        self.toggle_resources_button = RoundedButton(workspace, text=self.t("toggle_resources"), parent_bg=THEME["panel"], radius=11, padx=12, pady=6, command=self.toggle_left_panel)
        self.toggle_resources_button.pack(side="right", padx=3)
        self.toggle_tracker_button = RoundedButton(workspace, text=self.t("toggle_tracker"), parent_bg=THEME["panel"], radius=11, padx=12, pady=6, command=self.toggle_right_panel)
        self.toggle_tracker_button.pack(side="right", padx=3)
        # "X Düzeni" segmented control — [X+] [X-] [X+ / X-] (layout only, no flip).
        layout_frame = ttk.Frame(workspace, style="Panel.TFrame")
        layout_frame.pack(side="right", padx=3)
        self.layout_mode_title = tk.Label(layout_frame, text=self.t("layout_mode") + ":", fg=THEME["muted"], bg=THEME["panel"], font=("Segoe UI", 9, "bold"))
        self.layout_mode_title.pack(side="left", padx=(0, 4))
        self.layout_mode_buttons = {}
        for _val, _key in (("x_plus", "layout_btn_classic"), ("x_minus", "layout_btn_mirror"),
                           ("dual", "layout_btn_dual")):
            _b = RoundedButton(layout_frame, text=self.t(_key), parent_bg=THEME["panel"], radius=10, padx=10, pady=6,
                               command=lambda v=_val: self.set_layout_mode(v, save=True))
            _b.pack(side="left", padx=1)
            self.layout_mode_buttons[_val] = _b
        self._update_layout_mode_buttons()

        main = ttk.Frame(self)
        self.main_frame = main
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(main, style="Panel.TFrame")
        self.left_panel = left
        self.left_panel_visible = True
        left.pack(side="left", fill="y", padx=(0, 8))
        # Horizontally resizable: width persists, the grip on the inner edge is
        # dragged to widen the tree (long topic names stop truncating).
        self._left_panel_width = int(self.config_data.get("left_panel_width", 350) or 350)
        left.config(width=self._left_panel_width)
        left.pack_propagate(False)
        self.left_grip = tk.Frame(left, width=6, bg=THEME["border"], cursor="sb_h_double_arrow")
        self.left_grip.pack(side="right", fill="y")
        self.left_grip.bind("<ButtonPress-1>", self._left_grip_press)
        self.left_grip.bind("<B1-Motion>", self._left_grip_drag)
        self.left_grip.bind("<ButtonRelease-1>", self._left_grip_release)
        self.left_header_label = ttk.Label(left, text=self.t("course_resources"), style="Header.TLabel")
        self.left_header_label.pack(fill="x", padx=8, pady=(8,4))
        pathrow = ttk.Frame(left, style="Panel.TFrame")
        pathrow.pack(fill="x", padx=8, pady=4)
        self.resource_var = tk.StringVar(value=self.config_data.get("resource_dir", DEFAULT_RESOURCE_DIR))
        ttk.Entry(pathrow, textvariable=self.resource_var, width=32).pack(side="left", fill="x", expand=True)
        self.browse_button = RoundedButton(pathrow, text=self.t("browse"), parent_bg=THEME["panel"], radius=10, padx=14, pady=6, command=self.browse_resources)
        self.browse_button.pack(side="left", padx=4)
        self.search_label = ttk.Label(left, text=self.t("search"), style="Muted.TLabel")
        self.search_label.pack(anchor="w", padx=10, pady=(8,2))
        self.search_var = tk.StringVar()
        search = ttk.Entry(left, textvariable=self.search_var)
        search.pack(fill="x", padx=8)
        search.bind("<KeyRelease>", lambda e: self.populate_tree())
        # Course-tree: a checkbox column (tick = bitirdim) and an info
        # column — clicking ℹ opens the "Nedir ve Ne İçin Kullanılır?" window.
        # #0's width is tuned to the DEFAULT panel width so both extra columns
        # stay visible without horizontal scrolling; #0 stretches into any
        # extra room when the panel is widened via the drag grip, while ☐/ℹ
        # stay pinned at their fixed width on the right. The horizontal
        # scrollbar is only a fallback for very long names in a narrowed panel.
        tree_holder = ttk.Frame(left, style="Panel.TFrame")
        tree_holder.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree = ttk.Treeview(tree_holder, show="tree", columns=("st", "info"))
        self.tree.column("#0", width=258, minwidth=160, stretch=True)
        self.tree.column("st", width=28, anchor="center", stretch=False)
        self.tree.column("info", width=26, anchor="center", stretch=False)
        tree_vs = ttk.Scrollbar(tree_holder, orient="vertical", command=self.tree.yview)
        tree_hs = ttk.Scrollbar(tree_holder, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_vs.set, xscrollcommand=tree_hs.set)
        tree_hs.pack(side="bottom", fill="x")
        tree_vs.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Button-1>", self.on_tree_click)
        # Shift+wheel for horizontal scroll — the thin scrollbar is easy to miss.
        self.tree.bind("<Shift-MouseWheel>", lambda e: self.tree.xview_scroll(-1 if e.delta > 0 else 1, "units"))
        # Right-click a file to mark it ✅ done / 📖 reading — feeds the course
        # read counters and the tracker panel's reading progress.
        self.tree.bind("<Button-3>", self.show_tree_context_menu)
        btns = ttk.Frame(left, style="Panel.TFrame")
        btns.pack(fill="x", padx=8, pady=(0,8))
        resource_row1 = ttk.Frame(btns, style="Panel.TFrame")
        resource_row1.pack(fill="x")
        self.open_resource_button = RoundedButton(resource_row1, text=self.t("open_resource"), parent_bg=THEME["panel"], command=self.open_resource)
        self.open_resource_button.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        self.read_show_button = RoundedButton(resource_row1, text=self.t("read_show"), parent_bg=THEME["panel"], bg=THEME["accent"], fg="#FFFFFF", hover="#EC8A4B", command=self.read_selected)
        self.read_show_button.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        resource_row2 = ttk.Frame(btns, style="Panel.TFrame")
        resource_row2.pack(fill="x")
        self.open_location_button = RoundedButton(resource_row2, text=self.t("open_folder_location"), parent_bg=THEME["panel"], command=self.open_selected_location)
        self.open_location_button.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        self.print_button = RoundedButton(resource_row2, text=self.t("print"), parent_bg=THEME["panel"], command=self.print_selected_resource)
        self.print_button.pack(side="left", fill="x", expand=True, padx=2, pady=2)

        center = ttk.Frame(main)
        self.center_panel = center
        center.pack(side="left", fill="both", expand=True)
        self.tabs = ttk.Notebook(center)
        self.tabs.pack(fill="both", expand=True)
        self.pdf_tab = ttk.Frame(self.tabs)
        self.ai_tab = ttk.Frame(self.tabs)
        # 5 bilim laboratuvari tek "Lab'lar" sekmesinde IC sekmelerdir: ana
        # serit 12'den 8'e iner ve paneller acilista degil, sekme ilk kez
        # secildiginde kurulur (_ensure_labs_built). Workspace anahtarlari
        # (Data/Physics/Chemistry/DNA/Quantum) geriye uyum icin aynen yasar:
        # eski config'lerin gorunurluk tercihi, cip menusu ve session.tab
        # kayitlari degismeden calisir — hepsi ayni labs_tab'a cozumlenir.
        self.labs_tab = ttk.Frame(self.tabs)
        self.labs_nb = ttk.Notebook(self.labs_tab)
        self.labs_nb.pack(fill="both", expand=True)
        self._lab_frames = {}
        for _lab_key in LAB_WORKSPACES:
            _f = ttk.Frame(self.labs_nb)
            self.labs_nb.add(_f, text=self.workspace_display(_lab_key, short=True))
            self._lab_frames[_lab_key] = _f
        self._labs_built = False
        self._labs_error = None
        # Ic lab basligina orta-tik = o lab'i gizle (dis sekmelerle ayni jest;
        # ic baslik hangi lab'i kastettigini kesin soyledigi icin en dogru yer).
        self.labs_nb.bind("<Button-2>", self._on_lab_subtab_middle_click, add="+")
        self.wacom_board_tab = ttk.Frame(self.tabs)
        self.calculator_tab = ttk.Frame(self.tabs)
        self.dictionary_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.pdf_tab, text=self.workspace_tab_display("PDF"))
        self.tabs.add(self.ai_tab, text=self.workspace_tab_display("AI"))
        self.tabs.add(self.labs_tab, text=self.t("labs_tab"))
        self.tabs.add(self.wacom_board_tab, text=self.workspace_tab_display("Wacom"))
        self.tabs.add(self.calculator_tab, text=self.workspace_tab_display("Calculator"))
        self.visual_math_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.visual_math_tab, text=self.workspace_tab_display("VisualMath"))
        self.student_tracker_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.student_tracker_tab, text=self.workspace_tab_display("StudentTracker"))
        self.tabs.bind("<Button-2>", self.on_notebook_tab_click, add="+")  # middle-click closes; left-click just selects
        self.refresh_notebook_tabs()

        self.pdf_viewer = PDFViewer(self.pdf_tab, self)
        self.pdf_viewer.pack(fill="both", expand=True)

        # Lab panelleri burada KURULMAZ: _ensure_labs_built ilk secimde kurar.
        # (Olculdu: paneller hafif, kazanc ~10 ms — tembellik hiz icin degil,
        # "kullanilmayan is yapilmasin" ilkesi icin.) Attribute adlari korunur.
        self.math_data_lab = None
        self.physics_math_lab = None
        self.chemistry_math_lab = None
        self.math_dna_lab = None
        self.math_quantum_lab = None
        self.smart_wacom_board = MathWhiteboard(self.wacom_board_tab, self, title="Akıllı Matematik & 3D Tablet Çizim Tahtası")
        self.smart_wacom_board.pack(fill="both", expand=True)
        self.calculator = ScientificCalculator(self.calculator_tab, self)
        self.calculator.pack(fill="both", expand=True)
        # Sozluk ve Ogrenci Takip panelleri BURADA KURULMAZ: olculdu, ikisi
        # birlikte _build_ui'nin yaklasik %61'ini yiyordu (medyan 294 ms + 192
        # ms / 793 ms). Ilk ihtiyacta kurulurlar — VisualMath/Lab'lar deseni.
        # "Ilk ihtiyac" yalnizca sekmeye gecmek degil: kilit her giris noktasi
        # (_ensure_dictionary / _ensure_student_tracker) once paneli kurar.
        self.dictionary = None
        self._dictionary_error = None
        # Visual Math Lab: sekme ilk secildiginde kurulur (acilis ~1.5 sn
        # kisalir). Programatik tabs.select() de <<NotebookTabChanged>>
        # uretdigi icin "Grafik" gibi kisayollar da bu yoldan gecer.
        self.visual_math_lab = None
        self._visual_math_error = None
        self.tabs.bind("<<NotebookTabChanged>>", self._on_tab_changed, add="+")
        # Student Tracker: profiles + question bank + exams + progress analytics.
        self.student_tracker = None
        self._student_tracker_error = None

        self.ai_question_label = ttk.Label(self.ai_tab, text=self.t("question_topic"), style="Header.TLabel")
        self.ai_question_label.pack(fill="x", padx=8, pady=(8,2))
        self.question_text = tk.Text(self.ai_tab, height=6, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.question_text.pack(fill="x", padx=8, pady=6)
        self.attached_image_path = None
        self.attached_image_photo = None
        imgrow = ttk.Frame(self.ai_tab)
        imgrow.pack(fill="x", padx=8, pady=(0, 4))
        self.attach_image_button = RoundedButton(imgrow, text=self.t("attach_image"), parent_bg=THEME["bg"], command=self.attach_image)
        self.attach_image_button.pack(side="left", padx=3)
        self.clear_image_button = RoundedButton(imgrow, text=self.t("clear_image"), parent_bg=THEME["bg"], command=self.clear_image)
        self.clear_image_button.pack(side="left", padx=3)
        self.image_label = ttk.Label(imgrow, text=self.t("no_image"), style="Muted.TLabel")
        self.image_label.pack(side="left", padx=8)
        self.image_preview = tk.Label(self.ai_tab, bg=THEME["surface"])
        self.image_preview.pack(anchor="w", padx=8, pady=(0, 4))
        ai_btns = ttk.Frame(self.ai_tab)
        ai_btns.pack(fill="x", padx=8, pady=4)
        self.ask_ai_resource_button = RoundedButton(ai_btns, text=self.t("ask_ai_resource"), parent_bg=THEME["bg"], command=self.ask_ai_resource)
        self.ask_ai_resource_button.pack(side="left", padx=3)
        self.solve_question_button = RoundedButton(ai_btns, text=self.t("solve_question"), parent_bg=THEME["bg"], bg=THEME["accent"], fg="#FFFFFF", hover="#EC8A4B", command=self.solve_question)
        self.solve_question_button.pack(side="left", padx=3)
        self.solve_image_button = RoundedButton(ai_btns, text=self.t("solve_image"), parent_bg=THEME["bg"], command=self.solve_attached_image)
        self.solve_image_button.pack(side="left", padx=3)
        self.feedback_button = RoundedButton(ai_btns, text=self.t("feedback_report"), parent_bg=THEME["bg"], command=self.create_feedback_report)
        self.feedback_button.pack(side="left", padx=3)
        self.clear_ai_button = RoundedButton(ai_btns, text=self.t("clear"), parent_bg=THEME["bg"], command=lambda: self.ai_answer.delete("1.0", "end"))
        self.clear_ai_button.pack(side="left", padx=3)
        self.ai_answer_label = ttk.Label(self.ai_tab, text=self.t("ai_answer"), style="Header.TLabel")
        self.ai_answer_label.pack(fill="x", padx=8, pady=(10,2))
        self.ai_answer = tk.Text(self.ai_tab, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.ai_answer.pack(fill="both", expand=True, padx=8, pady=8)

        right = ttk.Frame(main, style="Panel.TFrame")
        self.right_panel = right
        self.right_panel_visible = True
        right.pack(side="right", fill="y", padx=(8,0))
        right.config(width=310)
        self.tracker_header_label = ttk.Label(right, text=self.t("course_tracker"), style="Header.TLabel")
        self.tracker_header_label.pack(fill="x", padx=8, pady=(8,4))
        self.tracker_desc_label = ttk.Label(right, text=self.t("track_progress"), style="Muted.TLabel")
        self.tracker_desc_label.pack(fill="x", padx=10, pady=(0,8))
        self.progress_frame = ttk.Frame(right, style="Panel.TFrame")
        self.progress_frame.pack(fill="x", padx=8, pady=2)
        self.save_progress_button = RoundedButton(right, text=self.t("save_progress"), parent_bg=THEME["panel"], bg=THEME["green"], fg="#FFFFFF", hover="#23B768", command=self.save_progress)
        self.save_progress_button.pack(fill="x", padx=10, pady=6)
        self.open_token_folder_button = RoundedButton(right, text=self.t("open_token_log_folder"), parent_bg=THEME["panel"], command=self.open_log_folder)
        self.open_token_folder_button.pack(fill="x", padx=10, pady=4)
        self.open_resources_folder_button = RoundedButton(right, text=self.t("open_resources_folder"), parent_bg=THEME["panel"], command=lambda: self.open_folder(self.resource_var.get()))
        self.open_resources_folder_button.pack(fill="x", padx=10, pady=4)
        ttk.Label(right, text="LM Studio Guide", style="Header.TLabel").pack(fill="x", padx=8, pady=(18,4))
        guide = (
            "Recommended settings:\n"
            "• Load Qwen2.5-Math-7B-Instruct-Q5_K_M.gguf\n"
            "• Model ID: qwen2.5-math-7b-instruct\n"
            "• Max Concurrent Predictions: 1\n"
            "• Context Length: 4096\n"
            "• Keep Model in Memory: On\n"
            "• Flash Attention: On\n\n"
            "Qwen does not read D: directly.\nThis app reads your files and sends selected context to Qwen."
        )
        tk.Label(right, text=guide, justify="left", fg=THEME["muted"], bg=THEME["panel"], wraplength=270).pack(fill="x", padx=12, pady=4)

        if not self.workspace_visible.get("CourseResources", True):
            self.set_left_panel_visible(False, save=False)


    def _on_tab_changed(self, event=None):
        try:
            sel = self.tabs.select()
            if getattr(self, "visual_math_tab", None) is not None and \
                    sel == str(self.visual_math_tab):
                self._ensure_visual_math_lab()
            elif getattr(self, "labs_tab", None) is not None and \
                    sel == str(self.labs_tab):
                self._ensure_labs_built()
            elif getattr(self, "dictionary_tab", None) is not None and \
                    sel == str(self.dictionary_tab):
                self._ensure_dictionary()
            elif getattr(self, "student_tracker_tab", None) is not None and \
                    sel == str(self.student_tracker_tab):
                self._ensure_student_tracker()
        except Exception:
            pass

    def _ensure_dictionary(self):
        """Dil & Bilim Sozlugunu ilk ihtiyacta kurar → panel ya da None.

        Yeni modul yuklenemezse klasik gomulu sozluge duser (eski davranis).
        Bir kere kurulamadiysa her sekme gecisinde yeniden denenmez."""
        if self.dictionary is not None or self._dictionary_error is not None:
            return self.dictionary
        loading = ttk.Label(self.dictionary_tab,
                            text="⏳ Sözlük yükleniyor… / Loading dictionary…")
        loading.pack(pady=40)
        self.dictionary_tab.update_idletasks()
        try:
            import language_dictionary as _langdict
            if getattr(self, "dark_mode", False):
                try:
                    _langdict.apply_dark_palette()
                except Exception:
                    pass
            seed = []
            for _name in dir(EnglishTurkishDictionary):
                if _name.endswith("_TERMS"):
                    _v = getattr(EnglishTurkishDictionary, _name)
                    if isinstance(_v, list):
                        seed.extend(_v)
            self.dictionary = _langdict.LanguageDictionaryPanel(
                self.dictionary_tab, self, seed_terms=seed)
        except Exception as _exc:
            try:
                print(f"Language Dictionary unavailable, using classic dictionary: {_exc}")
            except Exception:
                pass
            try:
                self.dictionary = EnglishTurkishDictionary(self.dictionary_tab, self)
            except Exception as _exc2:
                self._dictionary_error = _exc2
                loading.config(text=f"Sözlük yüklenemedi: {_exc2}")
                return None
        loading.destroy()
        self.dictionary.pack(fill="both", expand=True)
        return self.dictionary

    def _ensure_student_tracker(self):
        """Ogrenci Takip panelini ilk ihtiyacta kurar → panel ya da None."""
        if self.student_tracker is not None or self._student_tracker_error is not None:
            return self.student_tracker
        loading = ttk.Label(self.student_tracker_tab,
                            text="⏳ Öğrenci Takip yükleniyor… / Loading tracker…")
        loading.pack(pady=40)
        self.student_tracker_tab.update_idletasks()
        try:
            import student_tracker as _sttrack
            if getattr(self, "dark_mode", False):
                try:
                    _sttrack.apply_dark_palette()
                except Exception:
                    pass
            self.student_tracker = _sttrack.StudentTrackerPanel(
                self.student_tracker_tab, self)
        except Exception as _exc:
            self._student_tracker_error = _exc
            try:
                print(f"Student Tracker unavailable: {_exc}")
            except Exception:
                pass
            loading.config(text=f"Öğrenci Takip yüklenemedi: {_exc}")
            return None
        loading.destroy()
        self.student_tracker.pack(fill="both", expand=True)
        return self.student_tracker

    def _ensure_labs_built(self):
        """5 lab panelini ilk ihtiyacta kurar (bkz. _build_ui'daki tembel not).

        Kurulamazsa hata ic sekmede gorunur kalir ve her sekme gecisinde
        yeniden denenmez (_labs_error) — VisualMath desenidir."""
        if self._labs_built or self._labs_error is not None:
            return
        loading = ttk.Label(self.labs_tab,
                            text="⏳ Laboratuvarlar yükleniyor… / Loading labs…")
        # before=labs_nb: etiket ic notebook'un USTUNDE durur; sona pack
        # edilseydi alt kenarda ince bir serit olarak ezilirdi ve hata
        # mesaji gozden kacardi.
        loading.pack(pady=30, before=self.labs_nb)
        self.labs_tab.update_idletasks()
        try:
            for key, cls, attr in (("Data", MathDataLab, "math_data_lab"),
                                   ("Physics", PhysicsMathLab, "physics_math_lab"),
                                   ("Chemistry", ChemistryMathLab, "chemistry_math_lab"),
                                   ("DNA", MathDNALab, "math_dna_lab"),
                                   ("Quantum", MathQuantumLab, "math_quantum_lab")):
                panel = cls(self._lab_frames[key], self)
                panel.pack(fill="both", expand=True)
                setattr(self, attr, panel)
            self._labs_built = True
        except Exception as exc:
            self._labs_error = exc
            loading.config(text=f"Laboratuvarlar yüklenemedi: {exc}")
            return
        loading.destroy()

    def _ensure_visual_math_lab(self):
        """Visual Math Lab'i ilk ihtiyacta import edip kurar (bkz. _build_ui)."""
        if self.visual_math_lab is not None or self._visual_math_error is not None:
            return
        loading = ttk.Label(self.visual_math_tab,
                            text="⏳ Görsel Matematik Laboratuvarı yükleniyor… / Loading Visual Math Lab…")
        loading.pack(pady=40)
        self.visual_math_tab.update_idletasks()
        try:
            import visual_math_lab as _vml_mod
            if getattr(self, "dark_mode", False):
                # Modul tembel yuklendigi icin karanlik paleti burada uygulanir
                # (acilista import etmek sympy'yi geri getirirdi).
                try:
                    _vml_mod.apply_dark_palette()
                except Exception:
                    pass
            VisualMathLab = _vml_mod.VisualMathLab
            self.visual_math_lab = VisualMathLab(self.visual_math_tab, self)
        except Exception as exc:
            # Bir kere kurulamadiysa her sekme gecisinde yeniden denemeyelim;
            # hata sekmede gorunur kalsin.
            self._visual_math_error = exc
            loading.config(text=f"Görsel Matematik Laboratuvarı yüklenemedi: {exc}")
            return
        loading.destroy()
        self.visual_math_lab.pack(fill="both", expand=True)

    def rebuild_workspace_buttons(self):
        """Rebuild the compact Screen UI workspace buttons with small × close controls.

        The five science labs collapse into a single "Lab'lar ▾" menu chip so the
        bar stays short; every other workspace keeps its own chip."""
        if not hasattr(self, "workspace_button_frame"):
            return
        for child in self.workspace_button_frame.winfo_children():
            child.destroy()
        self.workspace_buttons = {}
        labs_chip_added = False
        for label in self.workspace_labels:
            if not self.workspace_visible.get(label, True):
                continue
            if label in LAB_WORKSPACES:
                if not labs_chip_added:
                    self._add_labs_group_chip()
                    labs_chip_added = True
                continue
            holder = tk.Frame(self.workspace_button_frame, bg=THEME["panel"])
            holder.pack(side="left", padx=3, pady=2)
            main = RoundedButton(
                holder,
                text=self.workspace_display(label, short=True),
                command=lambda name=label: self.select_workspace(name),
                parent_bg=THEME["panel"],
                bg=THEME["panel2"], fg=THEME["text"], hover=THEME["accent_soft"],
                radius=11, padx=12, pady=6, font=("Segoe UI Semibold", 9),
            )
            main.pack(side="left")
            close = RoundedButton(
                holder,
                text="×",
                command=lambda name=label: self.hide_workspace_button(name),
                parent_bg=THEME["panel"],
                bg=THEME["panel2"], fg=THEME["muted"],
                hover="#F4D6CC" if not getattr(self, "dark_mode", False) else "#5A3A31",
                radius=11, padx=7, pady=6, font=("Segoe UI Semibold", 10),
            )
            close.pack(side="left", padx=(2, 0))
            main.bind("<Button-3>", lambda event, name=label: self.hide_workspace_button(name))
            self.workspace_buttons[label] = holder

    def _add_labs_group_chip(self):
        holder = tk.Frame(self.workspace_button_frame, bg=THEME["panel"])
        holder.pack(side="left", padx=3, pady=2)
        btn = RoundedButton(
            holder,
            text=self.t("labs_group"),
            command=self._open_labs_menu,
            parent_bg=THEME["panel"],
            bg=THEME["panel2"], fg=THEME["text"], hover=THEME["accent_soft"],
            radius=11, padx=12, pady=6, font=("Segoe UI Semibold", 9),
        )
        btn.pack(side="left")
        self._labs_group_button = btn
        self.workspace_buttons["_labs"] = holder

    def _open_labs_menu(self):
        menu = tk.Menu(self, tearoff=0)
        for label in LAB_WORKSPACES:
            if self.workspace_visible.get(label, True):
                menu.add_command(label=self.workspace_display(label, short=True),
                                 command=lambda name=label: self.select_workspace(name))
        menu.add_separator()
        menu.add_command(label=self.t("workspace_manager"), command=self.open_workspace_manager)
        btn = getattr(self, "_labs_group_button", None)
        try:
            x = btn.winfo_rootx()
            y = btn.winfo_rooty() + btn.winfo_height()
        except Exception:
            x = self.winfo_rootx() + 60
            y = self.winfo_rooty() + 90
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def visible_workspace_count(self):
        return sum(1 for label in self.workspace_labels if self.workspace_visible.get(label, True))

    def set_workspace_visible(self, label, visible, save=True):
        if label not in self.workspace_labels:
            return
        visible = bool(visible)
        if not visible and self.workspace_visible.get(label, True) and self.visible_workspace_count() <= 1:
            messagebox.showwarning(self.t("workspace_manager"), self.t("at_least_one"))
            return
        self.workspace_visible[label] = visible
        if label == "CourseResources" and hasattr(self, "left_panel"):
            self.set_left_panel_visible(visible, save=False)
        if save:
            self.config_data["workspace_visible"] = self.workspace_visible
            safe_json_save(CONFIG_PATH, self.config_data)
        self.rebuild_workspace_buttons()
        self.refresh_notebook_tabs()
        if visible:
            self.set_status(self.t("shown_status").format(label=self.workspace_display(label)))
        else:
            self.select_first_visible_workspace_if_needed(label)
            self.set_status(self.t("hidden_status").format(label=self.workspace_display(label)))

    def hide_workspace_button(self, label):
        self.set_workspace_visible(label, False, save=True)

    def select_first_visible_workspace_if_needed(self, hidden_label):
        try:
            current = self.tabs.select()
        except Exception:
            return
        # Gizlenen bir IC lab'sa ve baska lab gorunur kaldiysa Labs sekmesi
        # seritte yerinde duruyor demektir — kullanici oradan atilmaz
        # (_refresh_lab_subtabs ic secimi zaten gorunur olana tasidi).
        if hidden_label in LAB_WORKSPACES and \
                any(self.workspace_visible.get(k, True) for k in LAB_WORKSPACES):
            return
        tab_map = self.workspace_tab_mapping()
        if hidden_label in tab_map and str(tab_map[hidden_label]) == str(current):
            for label in self.workspace_labels:
                if self.workspace_visible.get(label, True) and label in tab_map:
                    self.tabs.select(tab_map[label]); break

    def open_workspace_manager(self):
        win = tk.Toplevel(self)
        win.title(self.t("workspace_manager"))
        win.geometry("560x620")
        win.configure(bg=THEME["bg"])
        win.transient(self); win.grab_set()
        tk.Label(win, text=self.t("workspace_manager"), fg=THEME["text"], bg=THEME["bg"], font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=14, pady=(14, 4))
        tk.Label(win, text=self.t("select_visible"), fg=THEME["muted"], bg=THEME["bg"], wraplength=500, justify="left").pack(anchor="w", padx=14, pady=(0, 12))
        vars_by_label = {}
        list_frame = ttk.Frame(win, style="Panel.TFrame")
        list_frame.pack(fill="both", expand=True, padx=14, pady=6)
        for label in self.workspace_labels:
            var = tk.BooleanVar(value=self.workspace_visible.get(label, True))
            vars_by_label[label] = var
            cb = tk.Checkbutton(list_frame, text=self.workspace_display(label), variable=var, fg=THEME["text"], bg=THEME["panel"], selectcolor=THEME["bg"], activebackground=THEME["panel"], activeforeground=THEME["text"], font=("Segoe UI", 10, "bold"), anchor="w")
            cb.pack(fill="x", padx=12, pady=4)
        def apply_changes():
            if not any(var.get() for var in vars_by_label.values()):
                messagebox.showwarning(self.t("workspace_manager"), self.t("at_least_one")); return
            for label, var in vars_by_label.items():
                self.workspace_visible[label] = bool(var.get())
            self.set_left_panel_visible(self.workspace_visible.get("CourseResources", True), save=False)
            self.config_data["workspace_visible"] = self.workspace_visible
            safe_json_save(CONFIG_PATH, self.config_data)
            self.rebuild_workspace_buttons(); self.refresh_notebook_tabs(); self.set_status(self.t("bar_updated"))
        def reset_defaults():
            for label, var in vars_by_label.items(): var.set(True)
            apply_changes()
        row = ttk.Frame(win); row.pack(fill="x", padx=14, pady=12)
        RoundedButton(row, text=self.t("apply"), command=apply_changes).pack(side="left", fill="x", expand=True, padx=3)
        RoundedButton(row, text=self.t("reset_default"), command=reset_defaults).pack(side="left", fill="x", expand=True, padx=3)
        RoundedButton(row, text=self.t("close"), command=win.destroy).pack(side="left", fill="x", expand=True, padx=3)

    def workspace_tab_mapping(self):
        # 5 lab anahtari da ayni labs_tab'a cozumlenir (ic sekme secimi
        # select_workspace/_restore_session'daki _select_lab ile yapilir).
        mapping = {}
        for key, attr in [("PDF", "pdf_tab"), ("AI", "ai_tab"), ("Data", "labs_tab"), ("Physics", "labs_tab"), ("Chemistry", "labs_tab"), ("DNA", "labs_tab"), ("Quantum", "labs_tab"), ("Wacom", "wacom_board_tab"), ("Calculator", "calculator_tab"), ("Dictionary", "dictionary_tab"), ("VisualMath", "visual_math_tab"), ("StudentTracker", "student_tracker_tab")]:
            if hasattr(self, attr): mapping[key] = getattr(self, attr)
        return mapping

    def tab_workspace_keys(self):
        return ["PDF", "AI", "Data", "Physics", "Chemistry", "DNA", "Quantum", "Wacom", "Calculator", "Dictionary", "VisualMath", "StudentTracker"]

    def _active_lab_key(self):
        """Ic lab notebook'unda o an secili lab'in workspace anahtari."""
        nb = getattr(self, "labs_nb", None)
        if nb is not None:
            try:
                sel = nb.select()
                for key, frame in getattr(self, "_lab_frames", {}).items():
                    if str(frame) == sel:
                        return key
            except Exception:
                pass
        for key in LAB_WORKSPACES:
            if self.workspace_visible.get(key, True):
                return key
        return LAB_WORKSPACES[0]

    def _on_lab_subtab_middle_click(self, event):
        """Ic lab sekme basligina orta-tik: o lab'i gizler."""
        nb = getattr(self, "labs_nb", None)
        if nb is None:
            return
        try:
            index = nb.index(f"@{event.x},{event.y}")  # baslik disinda raise eder
            tab_id = nb.tabs()[index]
        except Exception:
            return
        key = next((k for k, f in getattr(self, "_lab_frames", {}).items()
                    if str(f) == str(tab_id)), None)
        if key:
            self.set_workspace_visible(key, False, save=True)
            return "break"

    def _select_lab(self, key):
        frame = getattr(self, "_lab_frames", {}).get(key)
        if frame is None:
            return
        try:
            self.labs_nb.select(frame)
        except Exception:
            pass

    def workspace_key_from_tab_id(self, tab_id):
        # Labs sekmesi 5 anahtara birden karsilik gelir; oturum kaydi ve
        # orta-tik gizleme icin AKTIF ic lab'in anahtari dondurulur.
        if getattr(self, "labs_tab", None) is not None and str(tab_id) == str(self.labs_tab):
            return self._active_lab_key()
        for key, widget in self.workspace_tab_mapping().items():
            if str(widget) == str(tab_id):
                return key
        return None

    # ---- Session restore: reopen the last PDF (page + zoom) and tab ---- #
    def _current_session(self):
        sess = {}
        try:
            sess["tab"] = self.workspace_key_from_tab_id(self.tabs.select())
        except Exception:
            pass
        pv = getattr(self, "pdf_viewer", None)
        try:
            if pv is not None and getattr(pv, "path", None):
                sess["pdf_path"] = str(pv.path)
                sess["pdf_page"] = int(getattr(pv, "page_index", 0) or 0)
                sess["pdf_zoom"] = float(getattr(pv, "zoom", 1.25) or 1.25)
        except Exception:
            pass
        return sess

    def _save_session(self):
        try:
            self.config_data["session"] = self._current_session()
            safe_json_save(CONFIG_PATH, self.config_data)
        except Exception:
            pass

    def _restore_session(self):
        sess = self.config_data.get("session") or {}
        if not isinstance(sess, dict):
            # Bozuk session "hic session yok" gibi davransin: asagidaki
            # startup_view=="today" yolu session verisine ihtiyac duymaz,
            # erken donus kullanicinin acilis tercihini de yutuyordu.
            sess = {}
        pv = getattr(self, "pdf_viewer", None)
        path = sess.get("pdf_path")
        if path and pv is not None:
            try:
                p = Path(path)
                if p.exists():
                    pv.load_pdf(p)
                    if getattr(pv, "doc", None) is not None:
                        pv.page_index = max(0, min(len(pv.doc) - 1, int(sess.get("pdf_page", 0) or 0)))
                        pv.zoom = max(0.35, min(5.0, float(sess.get("pdf_zoom", pv.zoom) or pv.zoom)))
                        pv.render()
                    self.selected_path = str(p)
            except Exception:
                pass
        # Acilis ekrani tercihi: "today" ise son oturumun sekmesi yerine
        # "Bugun" panosu one gelir (yukaridaki PDF geri yukleme yine calisir,
        # kullanici PDF sekmesine gecince kaldigi yerde bulur). Pano
        # gosterilemezse (Ogrenci Takip kurulamamissa) eski davranisa duser.
        if self.config_data.get("startup_view", "last") == "today" and self._show_today_dashboard():
            return
        tabk = sess.get("tab")
        if tabk:
            try:
                m = self.workspace_tab_mapping()
                if tabk in m and self.workspace_visible.get(tabk, True):
                    self.tabs.select(m[tabk])
                    if tabk in LAB_WORKSPACES:
                        # Eski oturumlar "Physics" gibi lab anahtari kaydeder;
                        # dogru ic sekme de secilir.
                        self._select_lab(tabk)
            except Exception:
                pass

    def set_theme_mode(self, value):
        if value not in ("light", "dark"):
            return
        self.config_data["theme"] = value
        safe_json_save(CONFIG_PATH, self.config_data)
        # Canli gecis bilerek yok: renkler kurulum aninda okunuyor, tum
        # pencereyi yeniden insa etmeden dogru uygulanamaz.
        self.set_status(self.t("theme_saved"), THEME["accent"])

    def set_startup_view(self, value):
        if value not in ("last", "today"):
            return
        self.config_data["startup_view"] = value
        safe_json_save(CONFIG_PATH, self.config_data)
        self.set_status(self.t("startup_view") + ": " +
                        self.t("startup_last" if value == "last" else "startup_today"))

    def _show_today_dashboard(self):
        """'Bugun' panosunu one getirir; basaramazsa False doner.

        Ogrenci Takip calisma alani gizliyse KALICI olarak gorunur yapilir
        (save=True): "acilista Bugun panosu" tercihi bu alanin gorunur olmasini
        gerektirir ve workspace_visible sozlugu config_data ile ayni nesneye
        referans olabildigi icin (set_workspace_visible save=True yolundaki
        atama) "oturumluk" bir degisiklik zaten sessizce diske sizabilirdi —
        acikca kalici yapmak durumu durust kilar."""
        # startup_view="today": panel TEMBEL kuruluyor, burada kurulmasi gerekir.
        st = self._ensure_student_tracker()
        if st is None:
            return False
        try:
            if not self.workspace_visible.get("StudentTracker", True):
                self.set_workspace_visible("StudentTracker", True, save=True)
            self.tabs.select(self.student_tracker_tab)
            st.nb.select(st.dash_tab)
            st._refresh_dashboard()
            return True
        except Exception:
            return False

    def _on_close(self):
        try:
            self._save_session()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def _refresh_lab_subtabs(self):
        """Ic lab sekmelerini workspace gorunurluk tercihine gore dizer.

        Dis notebook ile ayni desen: once hepsi hide, sonra gorunurler sirayla
        insert. Boylece eski config'lerdeki tek tek lab gizleme tercihleri
        (orn. "Physics": false) birlesmis sekmede de aynen calisir."""
        nb = getattr(self, "labs_nb", None)
        if nb is None:
            return
        frames = getattr(self, "_lab_frames", {})
        # Secimi HIDE DONGUSUNDEN ONCE kaydet: secili sekme de gizlenince
        # nb.select() bosalir ve sonda "eskisini koru" karari verilemezdi —
        # her yenilemede ic sekme ilk gorunur lab'a ziplardi.
        prev_key = None
        try:
            cur = nb.select()
            prev_key = next((k for k, f in frames.items() if str(f) == cur), None)
        except Exception:
            pass
        for key in LAB_WORKSPACES:
            f = frames.get(key)
            if f is None:
                continue
            try:
                nb.hide(f)
            except Exception:
                pass
        visible = [k for k in LAB_WORKSPACES if self.workspace_visible.get(k, True)]
        for i, key in enumerate(visible):
            f = frames.get(key)
            if f is None:
                continue
            title = self.workspace_display(key, short=True)
            try:
                nb.insert(i, f, text=title)
            except Exception:
                try:
                    nb.add(f, text=title)
                except Exception:
                    pass
            try:
                # insert() gizliyi geri gostermez; state="normal" sart
                # (dis notebook'taki ayni duzeltmenin ic esi).
                nb.tab(f, text=title, state="normal")
            except Exception:
                pass
        if visible:
            try:
                target = prev_key if prev_key in visible else visible[0]
                nb.select(frames[target])
            except Exception:
                pass

    def refresh_notebook_tabs(self):
        if not hasattr(self, "tabs"):
            return
        tab_map = self.workspace_tab_mapping()
        current_key = None
        try:
            current = self.tabs.select()
            current_key = self.workspace_key_from_tab_id(current)
        except Exception:
            current = None
        for key in self.tab_workspace_keys():
            tab = tab_map.get(key)
            if tab is None:
                continue
            try:
                self.tabs.hide(tab)
            except Exception:
                pass
        visible_keys = [key for key in self.tab_workspace_keys() if self.workspace_visible.get(key, True)]
        # 5 lab anahtari ayni labs_tab'a cozumlendigi icin yerlesim listesi
        # widget bazinda TEKILLESTIRILIR; labs_tab, ilk gorunur lab anahtarinin
        # konumuna girer ve sabit "Lab'lar" basligini tasir.
        placed, seen = [], set()
        for key in visible_keys:
            tab = tab_map.get(key)
            if tab is None or str(tab) in seen:
                continue
            seen.add(str(tab))
            placed.append((key, tab))
        for index, (key, tab) in enumerate(placed):
            if tab is getattr(self, "labs_tab", None):
                label = self.t("labs_tab")
            else:
                label = self.workspace_tab_display(key)
            try:
                self.tabs.insert(index, tab, text=label)
            except Exception:
                try:
                    self.tabs.add(tab, text=label)
                except Exception:
                    pass
            try:
                # state="normal" SART: ttk'da insert() gizli sekmeyi tasir ama
                # GERI GOSTERMEZ. Bu satir olmadan her yenilemede secili sekme
                # disindaki her sey seritten kayboluyordu (uzun suredir var olan
                # sessiz hata; cipler select() ile tek tek geri gosterdigi icin
                # fark edilmemisti).
                self.tabs.tab(tab, text=label, state="normal")
            except Exception:
                pass
        self._refresh_lab_subtabs()
        if visible_keys:
            if current_key in visible_keys:
                target_key = current_key
            elif current_key in LAB_WORKSPACES and any(k in visible_keys for k in LAB_WORKSPACES):
                # Gizlenen aktif IC lab'di ama baska lab hala gorunur:
                # kullanici PDF'e firlatilmaz, Labs sekmesinde kalir
                # (_refresh_lab_subtabs ic secimi zaten gorunur olana tasidi).
                target_key = next(k for k in LAB_WORKSPACES if k in visible_keys)
            else:
                target_key = visible_keys[0]
            target_tab = tab_map.get(target_key)
            if target_tab is not None:
                try:
                    self.tabs.select(target_tab)
                except Exception:
                    pass

    def on_notebook_tab_click(self, event):
        """Middle-click (Button-2) a notebook tab to hide that workspace.

        NOTE: bound to middle-click, not left-click. `ttk.Notebook.bbox()` returns
        (0,0,0,0) for tab headers, so the old left-click "× close zone" fired on
        EVERY tab click and silently hid the workspace — now left-click just
        selects (the notebook's default), and hiding is explicit (middle-click or
        the top workspace bar's × button).
        """
        if not hasattr(self, "tabs"):
            return
        try:
            index = self.tabs.index(f"@{event.x},{event.y}")  # raises unless on a tab header
            tab_id = self.tabs.tabs()[index]
        except Exception:
            return
        key = self.workspace_key_from_tab_id(tab_id)
        if key:
            self.set_workspace_visible(key, False, save=True)
            return "break"

    def select_workspace(self, name):
        if name == "CourseResources":
            self.set_left_panel_visible(True, save=True)
            self.set_status(self.workspace_display(name)); return
        mapping = self.workspace_tab_mapping()
        tab = mapping.get(name)
        if tab is not None:
            self.tabs.select(tab)
            if name in LAB_WORKSPACES:
                self._select_lab(name)
            self.set_status(self.workspace_display(name))

    def open_dictionary_subtab(self, index=0):
        """Open the Language & Science Dictionary and select one of its sub-tabs."""
        try:
            self.select_workspace("Dictionary")
            # Sekme gizliyse <<NotebookTabChanged>> tetiklenmemis olabilir;
            # panelin var oldugunu burada da garantile (tembel kurulum).
            self._ensure_dictionary()
            if getattr(self, "dictionary", None) is not None and hasattr(self.dictionary, "nb"):
                self.dictionary.nb.select(index)
        except Exception:
            pass

    def open_image_translation(self):
        """Jump to the Dictionary's Image Translation tab (used by PDF Reader)."""
        self.open_dictionary_subtab(2)
        try:
            messagebox.showinfo(
                "Translate Screenshot / Ekran Görüntüsünü Çevir",
                "Windows ekran alıntısı ile metni kırpın, sonra Görsel Çeviri sekmesinde "
                "Paste Screenshot kullanın.\n\nUse Windows snipping to crop the text, then press "
                "Paste Screenshot in the Image Translation tab.")
        except Exception:
            pass

    def set_left_panel_visible(self, visible, save=True):
        if visible:
            self.left_panel_visible = True
            self.workspace_visible["CourseResources"] = True
            self.set_status("Resource panel shown." if self.language == "en" else "Kaynak paneli gösterildi.")
        else:
            self.left_panel_visible = False
            self.workspace_visible["CourseResources"] = False
            self.set_status("Resource panel hidden." if self.language == "en" else "Kaynak paneli gizlendi.")
        self._apply_panel_layout()
        if save:
            self.config_data["workspace_visible"] = self.workspace_visible
            safe_json_save(CONFIG_PATH, self.config_data)
            self.rebuild_workspace_buttons()
            self.refresh_notebook_tabs()

    def toggle_left_panel(self):
        self.set_left_panel_visible(not getattr(self, "left_panel_visible", True), save=True)

    # ---- resource panel resize grip (yatay genişletme) -------------------- #
    def _left_grip_press(self, event):
        self._grip_start = (event.x_root, self.left_panel.winfo_width())

    def _left_grip_drag(self, event):
        start = getattr(self, "_grip_start", None)
        if not start:
            return
        delta = event.x_root - start[0]
        if getattr(self, "pdf_reader_layout_mode", "x_plus") == "x_minus":
            delta = -delta   # mirror layout: panel sits on the right side
        w = max(240, min(820, start[1] + delta))
        self._left_panel_width = w
        try:
            self.left_panel.config(width=w)
        except Exception:
            pass

    def _left_grip_release(self, event):
        self._grip_start = None
        self.config_data["left_panel_width"] = int(getattr(self, "_left_panel_width", 350))
        safe_json_save(CONFIG_PATH, self.config_data)

    def toggle_right_panel(self):
        self.right_panel_visible = not getattr(self, "right_panel_visible", True)
        self._apply_panel_layout()
        if self.right_panel_visible:
            self.set_status("Tracker panel shown." if self.language == "en" else "Takip paneli gösterildi.")
        else:
            self.set_status("Tracker panel hidden." if self.language == "en" else "Takip paneli gizlendi.")

    # ---- "X Düzeni": X+ Normal / X- Ayna / X+ / X- Çift Görünüm ------------- #
    # Layout-only: panels are re-packed on different sides; nothing is ever
    # image-flipped or negatively scaled, so PDF/toolbar/math stay readable.
    def _open_dual_reader(self, win_attr, viewer_attr, mirror_attr, title, geo_key,
                          label_suffix, seed_from_main=False):
        """Open (or re-show) ONE independent reader window = [resources | PDFViewer].
        A single Toplevel per side is reused (withdraw/deiconify) so its loaded
        PDF + annotations survive toggling. Closing it (X) reverts to X+ Normal."""
        win = getattr(self, win_attr, None)
        if win is not None:
            try:
                if win.winfo_exists():
                    win.deiconify()
                    win.lift()
                    try:
                        win.focus_force()
                    except Exception:
                        pass
                    return
            except Exception:
                pass
        win = tk.Toplevel(self)
        win.title(title)
        try:
            geo = self.config_data.get(geo_key, "")
            win.geometry(geo if geo else "1100x840")
        except Exception:
            win.geometry("1100x840")
        try:
            ip = resource_path(ICON_FILENAME)
            if Path(ip).exists():
                win.iconbitmap(ip)
        except Exception:
            pass
        body = ttk.Frame(win)
        body.pack(fill="both", expand=True, padx=6, pady=6)
        mirror = ResourceMirrorPanel(body, self, viewer_attr=viewer_attr, label_suffix=label_suffix)
        mirror.pack(side="left", fill="y", padx=(0, 6))
        viewer = PDFViewer(body, self)
        viewer.pack(side="left", fill="both", expand=True)
        setattr(self, viewer_attr, viewer)
        setattr(self, mirror_attr, mirror)
        win.protocol("WM_DELETE_WINDOW", lambda: self.set_layout_mode("x_plus", save=True))
        setattr(self, win_attr, win)
        # Seed window A with whatever PDF the main reader currently shows.
        if seed_from_main:
            try:
                mv = getattr(self, "pdf_viewer", None)
                if mv is not None and getattr(mv, "path", None):
                    viewer.load_pdf(mv.path)
            except Exception:
                pass

    def _close_dual_reader(self, win_attr, geo_key):
        win = getattr(self, win_attr, None)
        if win is None:
            return
        try:
            if win.winfo_exists() and win.state() != "withdrawn":
                try:
                    self.config_data[geo_key] = win.winfo_geometry()
                    safe_json_save(CONFIG_PATH, self.config_data)
                except Exception:
                    pass
                win.withdraw()
        except Exception:
            pass

    def _open_dual_windows(self):
        self._open_dual_reader("dual_window_a", "pdf_viewer_a", "resource_mirror_a",
                               "Math Course AI — PDF Okuyucu A", "dual_window_a_geometry",
                               " (A)", seed_from_main=True)
        self._open_dual_reader("dual_window_b", "pdf_viewer_b", "resource_mirror_b",
                               "Math Course AI — PDF Okuyucu B", "dual_window_b_geometry", " (B)")

    def _close_dual_windows(self):
        self._close_dual_reader("dual_window_a", "dual_window_a_geometry")
        self._close_dual_reader("dual_window_b", "dual_window_b_geometry")

    def _ensure_dual_hint(self):
        if getattr(self, "_dual_hint", None) is None:
            try:
                self._dual_hint = tk.Label(self.main_frame, text="", fg=THEME["muted"],
                                           bg=THEME["bg"], font=("Segoe UI", 13), justify="center")
            except Exception:
                self._dual_hint = None
        return getattr(self, "_dual_hint", None)

    def _apply_panel_layout(self):
        """Lay out the main window. In x_plus/x_minus the A pair fills the main
        body; in dual the body is EMPTIED (only a hint + the top bars remain)
        and readers A & B each open in their OWN OS window. Layout only —
        nothing is image-flipped or negatively scaled."""
        left = getattr(self, "left_panel", None)
        center = getattr(self, "center_panel", None)
        right = getattr(self, "right_panel", None)
        if center is None:
            return
        mode = getattr(self, "pdf_reader_layout_mode", "x_plus")
        left_vis = bool(getattr(self, "left_panel_visible", True))
        right_vis = bool(getattr(self, "right_panel_visible", True))
        hint = self._ensure_dual_hint()
        for w in (left, center, right, hint):
            if w is not None:
                try:
                    w.pack_forget()
                except Exception:
                    pass
        try:
            center.pack_propagate(True)
        except Exception:
            pass
        if mode == "dual":
            # Main body stays EMPTY (only the top bars remain); readers A & B
            # each open in their own OS window.
            if hint is not None:
                hint.config(text=(
                    "X+ / X- Dual view is on.\n\nReaders A and B are open in separate windows.\n"
                    "Press  X+  (top bar) to return to the classic view."
                    if self.language == "en" else
                    "X+ / X- Çift Görünüm açık.\n\nA ve B okuyucuları ayrı pencerelerde açık.\n"
                    "Klasik görünüme dönmek için üstteki  X+  düğmesine bas."))
                hint.pack(fill="both", expand=True, padx=20, pady=40)
            self._open_dual_windows()
        else:
            if mode == "x_minus":
                # Mirror: tracker on the left, resources on the right, center middle.
                if right is not None and right_vis:
                    right.pack(side="left", fill="y", padx=(0, 8))
                if left is not None and left_vis:
                    left.pack(side="right", fill="y", padx=(8, 0))
                center.pack(side="left", fill="both", expand=True)
            else:
                # x_plus (classic): resources left, tracker right, center middle.
                if left is not None and left_vis:
                    left.pack(side="left", fill="y", padx=(0, 8))
                if right is not None and right_vis:
                    right.pack(side="right", fill="y", padx=(8, 0))
                center.pack(side="left", fill="both", expand=True)
            self._close_dual_windows()

    def _update_layout_mode_buttons(self):
        btns = getattr(self, "layout_mode_buttons", None)
        if not btns:
            return
        active = getattr(self, "pdf_reader_layout_mode", "x_plus")
        for val, b in btns.items():
            try:
                b.config(bg=THEME["accent"] if val == active else THEME["panel2"])
            except Exception:
                pass

    def set_layout_mode(self, mode, save=True):
        if mode not in ("x_plus", "x_minus", "dual"):
            mode = "x_plus"
        self.pdf_reader_layout_mode = mode
        self._apply_panel_layout()
        self._update_layout_mode_buttons()
        if hasattr(self, "_layout_mode_var"):
            try:
                self._layout_mode_var.set(mode)
            except Exception:
                pass
        msgs = {
            "x_plus": ("X+ Normal — resources left, PDF right.",
                       "X+ Normal — kaynaklar solda, PDF sağda."),
            "x_minus": ("X- Mirror — resources right, PDF left.",
                        "X- Ayna — kaynaklar sağda, PDF solda."),
            "dual": ("X+ / X- Dual — readers A and B opened in two separate windows; main body emptied.",
                     "X+ / X- Çift Görünüm — A ve B okuyucu iki ayrı pencerede açıldı; ana pencere boşaltıldı."),
        }
        en, tr = msgs.get(mode, ("", ""))
        self.set_status(en if self.language == "en" else tr)
        if save:
            self.config_data["pdf_reader_layout_mode"] = mode
            safe_json_save(CONFIG_PATH, self.config_data)

    def show_settings_menu(self):
        menu = tk.Menu(self, tearoff=False, bg=THEME["panel"], fg=THEME["text"], activebackground=THEME["accent"], activeforeground="white")
        setting = tk.Menu(menu, tearoff=False, bg=THEME["panel"], fg=THEME["text"], activebackground=THEME["accent"], activeforeground="white")
        setting.add_command(label=self.t("toggle_resources"), command=self.toggle_left_panel)
        setting.add_command(label=self.t("toggle_tracker"), command=self.toggle_right_panel)
        self._layout_mode_var = tk.StringVar(value=getattr(self, "pdf_reader_layout_mode", "x_plus"))
        for _val, _key in (("x_plus", "layout_x_plus"), ("x_minus", "layout_x_minus"), ("dual", "layout_dual")):
            setting.add_radiobutton(label=self.t(_key), value=_val, variable=self._layout_mode_var,
                                    command=lambda v=_val: self.set_layout_mode(v, save=True))
        setting.add_separator()
        self._startup_view_var = tk.StringVar(value=self.config_data.get("startup_view", "last"))
        for _val, _key in (("last", "startup_last"), ("today", "startup_today")):
            setting.add_radiobutton(label=self.t("startup_view") + ": " + self.t(_key), value=_val,
                                    variable=self._startup_view_var,
                                    command=lambda v=_val: self.set_startup_view(v))
        setting.add_separator()
        self._theme_mode_var = tk.StringVar(value=self.config_data.get("theme", "light"))
        for _val, _key in (("light", "theme_light"), ("dark", "theme_dark")):
            setting.add_radiobutton(label=self.t("theme_mode") + ": " + self.t(_key), value=_val,
                                    variable=self._theme_mode_var,
                                    command=lambda v=_val: self.set_theme_mode(v))
        setting.add_separator()
        setting.add_command(label=self.t("workspace_manager"), command=self.open_workspace_manager)
        setting.add_command(label=self.t("settings"), command=self.open_settings)
        setting.add_command(label=self.t("token_reports"), command=self.show_token_reports)
        setting.add_command(label=self.t("api_test"), command=self.test_api)
        setting.add_command(label=self.t("ai_terminal"), command=self.open_ai_terminal)
        setting.add_command(label=self.t("token_ledger"), command=self.open_token_ledger)
        setting.add_separator()
        setting.add_command(label=self.t("user_guide"), command=self.open_user_guide)
        setting.add_command(label=self.t("about"), command=self.open_about)
        setting.add_command(label=self._backup_menu_label(),
                            command=self.open_backup_folder)
        setting.add_command(label=self.t("refresh_resources"), command=self.refresh_resources)
        menu.add_cascade(label=self.t("setting_menu"), menu=setting)
        workspace_menu = tk.Menu(menu, tearoff=False, bg=THEME["panel"], fg=THEME["text"], activebackground=THEME["accent"], activeforeground="white")
        self._settings_workspace_vars=[]
        for label in self.workspace_labels:
            var=tk.BooleanVar(value=self.workspace_visible.get(label, True)); self._settings_workspace_vars.append(var)
            workspace_menu.add_checkbutton(label=self.workspace_display(label), variable=var, command=lambda name=label, v=var: self.set_workspace_visible(name, v.get(), save=True))
        workspace_menu.add_separator(); workspace_menu.add_command(label=self.t("workspace_manager"), command=self.open_workspace_manager)
        menu.add_cascade(label=self.t("workspace_manager"), menu=workspace_menu)
        lang_menu = tk.Menu(menu, tearoff=False, bg=THEME["panel"], fg=THEME["text"], activebackground=THEME["accent"], activeforeground="white")
        lang_menu.add_command(label="Türkçe", command=lambda: self.set_language("tr")); lang_menu.add_command(label="English", command=lambda: self.set_language("en"))
        menu.add_cascade(label=self.t("language"), menu=lang_menu)
        try:
            x=self.settings_button.winfo_rootx(); y=self.settings_button.winfo_rooty()+self.settings_button.winfo_height(); menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def set_status(self, text, color=None):
        # Uzun hata metinleri (orn. WinError'lu baglanti hatalari) ust cubugu
        # tasirip sag taraftaki gostergeleri/dugmeleri ekrandan dusurebiliyordu;
        # tam metin zaten API Test penceresinde gorulebilir.
        text = str(text)
        if len(text) > 90:
            text = text[:89] + "…"
        self.status_label.config(text=text, fg=color or THEME["green"])

    def browse_resources(self):
        folder = filedialog.askdirectory(initialdir=self.resource_var.get() or DEFAULT_RESOURCE_DIR)
        if folder:
            self.resource_var.set(folder)
            self.config_data["resource_dir"] = folder
            safe_json_save(CONFIG_PATH, self.config_data)
            self.refresh_resources()

    def refresh_resources(self):
        self.scanner = ResourceScanner(self.resource_var.get())
        self.courses = self.scanner.scan()
        self.populate_tree()
        for _attr in ("resource_mirror_a", "resource_mirror_b"):
            _m = getattr(self, _attr, None)
            if _m is not None:
                try:
                    _m.populate()
                except Exception:
                    pass
        self.build_progress_ui()
        self._update_welcome_card()
        self.set_status(f"Resources loaded: {len(self.courses)} course folders.")

    def _update_welcome_card(self):
        """Kaynak taramasi BOS ise agacin ustune 3 adimlik baslangic karti koyar.

        Yeni kullanici / yeni klon bos bir agacla karsilasiyordu ve programin
        PDF'siz de calisabildigini (yerlesik uretecler) hicbir sey soylemiyordu.
        refresh_resources'in sonunda cagrilir: Gozat, Yenile, ayar kaydetme ve
        acilis dahil TUM tarama tetikleyicilerinde dogru gorunur/kaybolur.
        populate_tree'ye konmadi cunku onu arama kutusu da tetikliyor ve arama
        sonucu bos olmasi "kaynak yok" demek degil. Kart her gosterimde yeniden
        kurulur; boylece dil degisiminde metinler tazedir.
        """
        old = getattr(self, "welcome_card", None)
        if old is not None:
            try:
                old.destroy()
            except Exception:
                pass
            self.welcome_card = None
        # Kurs listesi dolu gorunse bile icinde TEK BIR gercek kaynak dosyasi
        # olmayabilir (bos klasor iskeleti, yalnizca desteklenmeyen dosyalar):
        # tarayici alt klasoru olan her klasoru "kurs" sayar. Kartin hedefi tam
        # da bu yeni-kullanici durumu oldugundan dosya duzeyinde bakilir.
        courses = getattr(self, "courses", None) or []
        if any(self._course_files(c) for c in courses):
            return
        try:
            holder = self.tree.master
        except Exception:
            return
        card = tk.Frame(holder, bg=THEME["panel"],
                        highlightbackground=THEME["border"], highlightthickness=1)
        card.place(relx=0, rely=0, relwidth=1, relheight=1)
        inner = tk.Frame(card, bg=THEME["panel"])
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        wrap_labels = []

        def _label(key, pack_pady=(0, 2), **kw):
            defaults = dict(bg=THEME["panel"], fg=THEME["text"], justify="left",
                            anchor="w", wraplength=290)
            defaults.update(kw)
            lbl = tk.Label(inner, text=self.t(key), **defaults)
            lbl.pack(fill="x", pady=pack_pady)
            wrap_labels.append(lbl)
            return lbl

        _label("welcome_title", font=("Segoe UI", 13, "bold"))
        _label("welcome_intro", fg=THEME["muted"])

        def _step(text_key, btn_key, command, accent=False):
            _label(text_key, pack_pady=(8, 2))
            extra = dict(bg=THEME["accent"], fg="#FFFFFF", hover="#EC8A4B") if accent else {}
            btn = RoundedButton(inner, text=self.t(btn_key), parent_bg=THEME["panel"],
                                command=command, **extra)
            btn.pack(anchor="w", padx=2, pady=(2, 4))
            return btn

        def _open_packs():
            st = self._ensure_student_tracker()      # tembel: once kur
            if st is None:
                # Panel kurulamamissa bos sekmeye goturmek karti anlamsiz kilar;
                # sessiz kalmak yerine nedenini soyle.
                self.set_status("Öğrenci Takip paneli yüklenemedi — soru paketleri açılamıyor.",
                                THEME["danger"])
                return
            try:
                if not self.workspace_visible.get("StudentTracker", True):
                    self.set_workspace_visible("StudentTracker", True, save=True)
                self.tabs.select(self.student_tracker_tab)
                st.nb.select(getattr(st, "packs_tab", 3))
            except Exception:
                pass

        _step("welcome_step1", "welcome_browse", self.browse_resources, accent=True)
        _step("welcome_step2", "welcome_settings", self.open_settings)
        _step("welcome_step3", "welcome_packs", _open_packs, accent=True)
        # Yeni kullanicinin kilavuzu bulacagi en dogal yer: bos ekran.
        _step("welcome_guide_text", "welcome_guide", self.open_user_guide)

        def _sync_wrap(event, _labels=wrap_labels):
            # Sol panel 240 px'e kadar daraltilabilir ve genislik config'te
            # kalicidir; sabit wraplength dar panelde metni sagdan keserdi.
            w = max(120, event.width - 8)
            for lb in _labels:
                try:
                    lb.config(wraplength=w)
                except Exception:
                    pass
        inner.bind("<Configure>", _sync_wrap)
        self.welcome_card = card

    # ---- reading progress: ✅ done / 📖 reading marks on resource files ---- #
    def _course_files(self, course):
        """Every resource file path (str) under one course dict."""
        files = [str(res) for res in course.get("resources", [])]

        def walk(sec):
            for item in sec.get("items", []):
                files.append(str(item))
            for child in sec.get("children", []):
                walk(child)

        for sec in course.get("children", []):
            walk(sec)
        return files

    def file_read_status(self, course_name, path):
        return (self.progress.get(course_name, {}).get("files", {}) or {}).get(str(path), "")

    def set_file_read_status(self, course_name, path, status):
        """Mark one resource file as done/reading (or clear the mark) and persist."""
        if not course_name:
            return
        p = self.progress.setdefault(course_name, {})
        files = p.setdefault("files", {})
        if status:
            files[str(path)] = status
        else:
            files.pop(str(path), None)
        safe_json_save(PROGRESS_PATH, self.progress)
        # update in place — a full repopulate would collapse the open sections
        self._update_tree_item_icon(course_name, path)
        self._update_course_header(course_name)
        self.build_progress_ui()
        labels = {"done": "✅ Bitirdim", "reading": "📖 Okunuyor", "": "işaret kaldırıldı"}
        self.set_status(f"{Path(str(path)).name} → {labels.get(status, status)}")

    def _update_tree_item_icon(self, course_name, path):
        iid = getattr(self, "iid_by_path", {}).get(str(path))
        if not iid:
            return
        try:
            self.tree.item(iid, text=self._read_icon(course_name, path) + Path(str(path)).name,
                           values=(self._read_check(course_name, path), "ℹ"))
        except Exception:
            pass

    def _update_course_header(self, course_name):
        for iid, cname in getattr(self, "course_name_by_iid", {}).items():
            if cname != course_name:
                continue
            course = next((c for c in self.courses if c["name"] == course_name), None)
            if course is not None:
                done, total = self.course_read_stats(course)
                header = self._course_header_text(course_name, done, total)
                try:
                    self.tree.item(iid, text=header)
                except Exception:
                    pass
            break

    def course_read_stats(self, course):
        """(done, total) resource-file counts for one course dict."""
        files = self._course_files(course)
        fmap = self.progress.get(course["name"], {}).get("files", {}) or {}
        done = sum(1 for f in files if fmap.get(f) == "done")
        return done, len(files)

    @staticmethod
    def _course_header_text(name, done, total):
        """Tree row label for a course. The ✅ only appears once the course is
        ACTUALLY finished — showing it at 0/N misleadingly reads as 'done'."""
        if not total:
            return name
        if done == total:
            return f"{name}  —  {total}/{total} ✅"
        if done == 0:
            return f"{name}  —  0/{total}"
        pct = int(round(done * 100.0 / total))
        return f"{name}  —  {done}/{total}  (%{pct})"

    def _read_icon(self, course_name, path):
        return {"done": "✅ ", "reading": "📖 "}.get(
            self.file_read_status(course_name, path), "📄 ")

    def _read_check(self, course_name, path):
        """Checkbox-column glyph for a resource file (course-tree tick)."""
        return {"done": "☑", "reading": "☐"}.get(
            self.file_read_status(course_name, path), "☐")

    def _is_bank_course(self, name):
        n = (name or "").lower()
        return "soru bank" in n or "question bank" in n

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.path_by_iid.clear()
        self.course_name_by_iid = {}
        self.iid_by_path = {}
        query = self.search_var.get().strip().lower()

        def match(path):
            return not query or query in Path(path).name.lower() or query in str(path).lower()

        # Two roots: lessons and question banks.
        lessons = [c for c in self.courses if not self._is_bank_course(c["name"])]
        banks = [c for c in self.courses if self._is_bank_course(c["name"])]
        groups = []
        if lessons:
            groups.append(("📘 Dersler" if self.language == "tr" else "📘 Lessons", lessons))
        if banks:
            groups.append(("📝 Soru Bankaları" if self.language == "tr" else "📝 Question Banks", banks))
        for group_label, group_courses in groups:
            group_iid = self.tree.insert("", "end", text=group_label, open=True, values=("", ""))
            for course in group_courses:
                done, total = self.course_read_stats(course)
                header = self._course_header_text(course["name"], done, total)
                course_iid = self.tree.insert(group_iid, "end", text=header, open=True, values=("", ""))
                self.path_by_iid[course_iid] = course["path"]
                self.course_name_by_iid[course_iid] = course["name"]
                for res in course.get("resources", []):
                    if match(res):
                        iid = self.tree.insert(course_iid, "end",
                                               text=self._read_icon(course["name"], res) + res.name,
                                               values=(self._read_check(course["name"], res), "ℹ"))
                        self.path_by_iid[iid] = str(res)
                        self.iid_by_path[str(res)] = iid
                for sec in course.get("children", []):
                    self.add_section(course_iid, sec, match, course["name"])

    def add_section(self, parent, sec, match, course_name=""):
        sec_iid = self.tree.insert(parent, "end", text="📁 " + sec["name"], open=False, values=("", "ℹ"))
        self.path_by_iid[sec_iid] = sec["path"]
        count = 0
        for item in sec.get("items", []):
            if match(item):
                iid = self.tree.insert(sec_iid, "end",
                                       text=self._read_icon(course_name, item) + item.name,
                                       values=(self._read_check(course_name, item), "ℹ"))
                self.path_by_iid[iid] = str(item)
                self.iid_by_path[str(item)] = iid
                count += 1
        for child in sec.get("children", []):
            self.add_section(sec_iid, child, match, course_name)
            count += 1
        if self.search_var.get().strip() and count:
            self.tree.item(sec_iid, open=True)

    def tree_course_name(self, iid):
        """Course name for any tree item (walks up to the course row; the tree
        roots are the Dersler / Soru Bankaları group headers)."""
        item = iid
        names = getattr(self, "course_name_by_iid", {})
        while item:
            if item in names:
                return names[item]
            item = self.tree.parent(item)
        return ""

    def on_tree_click(self, event):
        """Course-tree tick + info: column #1 toggles ✅ Bitirdim, column #2 (ℹ)
        opens the "Nedir ve Ne İçin Kullanılır?" window. Other clicks behave
        normally."""
        try:
            col = self.tree.identify_column(event.x)
        except Exception:
            return
        if col not in ("#1", "#2"):
            return
        iid = self.tree.identify_row(event.y)
        path = self.path_by_iid.get(iid)
        if not path:
            return
        if col == "#2":
            p = Path(str(path))
            if not (p.is_file() or p.is_dir()):
                return
            self.open_topic_info_window(self.topic_display_name(p),
                                        self.tree_course_name(iid))
            return "break"
        if not Path(str(path)).is_file():
            return
        course_name = self.tree_course_name(iid)
        cur = self.file_read_status(course_name, path)
        self.set_file_read_status(course_name, path, "" if cur == "done" else "done")
        return "break"

    # ---- ℹ topic info: "Nedir ve Ne İçin Kullanılır?" ---------------------- #
    @staticmethod
    def topic_display_name(path):
        """'03 Domains of composite functions.pdf' → 'Domains of composite functions'."""
        p = Path(str(path))
        stem = p.stem if p.suffix else p.name
        return re.sub(r"^\s*\d+[\s\.\-_]*", "", stem).strip() or stem

    def _topic_info_cache_load(self):
        return safe_json_load(TOPIC_INFO_CACHE_PATH, {})

    def _topic_info_cache_save(self, cache):
        safe_json_save(TOPIC_INFO_CACHE_PATH, cache)

    def open_topic_info_window(self, topic, course_name=""):
        """Separate window explaining one topic: Nedir? + Ne İçin Kullanılır?

        V45: the PRIMARY source is the embedded, hand-written knowledge base
        (topic_knowledge.py) — no AI call and no network at all, includes real
        math history/biography. Local LM Studio AI is now only an OPTIONAL,
        manual fallback for topics not yet documented (button, not automatic)."""
        topic = (topic or "").strip()
        if not topic:
            return
        wins = getattr(self, "_topic_info_windows", None)
        if wins is None:
            wins = self._topic_info_windows = {}
        old = wins.get(topic)
        if old is not None:
            try:
                if old.winfo_exists():
                    old.deiconify(); old.lift(); old.focus_force()
                    return
            except Exception:
                pass
        win = tk.Toplevel(self)
        wins[topic] = win
        win.title(f"ℹ {topic} — Nedir ve Ne İçin Kullanılır?")
        win.geometry("780x660")
        win.configure(bg=THEME["bg"])
        tk.Label(win, text=topic, bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI Semibold", 13), wraplength=720,
                 justify="left").pack(anchor="w", padx=14, pady=(12, 0))
        sub = f"Kurs: {course_name}" if course_name else ""
        tk.Label(win, text=sub, bg=THEME["bg"], fg=THEME["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14)
        status = tk.Label(win, text="", bg=THEME["bg"], fg=THEME["muted"],
                          font=("Segoe UI", 9, "bold"))
        status.pack(anchor="w", padx=14, pady=(2, 0))
        holder = ttk.Frame(win)
        holder.pack(fill="both", expand=True, padx=12, pady=6)
        txt = tk.Text(holder, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                      relief="solid", borderwidth=1, font=("Segoe UI", 10),
                      padx=10, pady=8)
        sb = ttk.Scrollbar(holder, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        def show_text(content, note, color=None):
            if not win.winfo_exists():
                return
            # Bodies (embedded or AI-generated) carry light $...$ LaTeX by
            # convention; delatex() downgrades it to readable plain Unicode
            # since this is a plain Text widget, not a math renderer. Status/
            # placeholder messages have no LaTeX so this is a harmless no-op.
            try:
                import topic_knowledge as _tkb
                content = _tkb.delatex(content)
            except Exception:
                pass
            txt.config(state="normal")
            txt.delete("1.0", "end")
            txt.insert("1.0", content)
            txt.config(state="disabled")
            status.config(text=note, fg=color or THEME["muted"])

        cache_key = topic.lower()
        ai_button = {}   # filled once the button is created, so we can rename it

        def try_embedded():
            try:
                import topic_knowledge as tkb
            except Exception:
                return None
            return tkb.get_topic_info(topic)

        def ask_ai(force=False):
            cache = self._topic_info_cache_load()
            if not force and cache.get(cache_key):
                show_text(cache[cache_key],
                          "🤖 Yerel AI tarafından daha önce üretilmiş (kayıtlı) — "
                          "yerleşik bilgi bankasında henüz yok.", THEME["accent"])
                return
            show_text("⏳ Yerel AI açıklama üretiyor…\n\nLM Studio'daki matematik modeli "
                      "bu konu için 'Nedir ve ne için kullanılır?' açıklaması yazıyor.",
                      "⏳ Üretiliyor…", THEME["accent"])

            def worker():
                system_prompt = (
                    "Sen deneyimli, sabırlı bir matematik öğretmenisin. SADECE Türkçe yaz. "
                    "Sana verilen matematik konusunu şu yapıda açıkla:\n"
                    "1) Konuyu tek cümlede, günlük hayattan sezgisel bir benzetmeyle tanıt.\n"
                    "2) 'Nedir?' başlığı altında net, doğru ve anlaşılır bir tanım yap; "
                    "gerektiğinde $...$ içinde LaTeX gösterimi kullan; konunun İngilizce adını "
                    "parantez içinde bir kez ver.\n"
                    "3) 'Ne İçin Kullanılır?' başlığı altında 2-4 numaralı madde yaz: matematik "
                    "içindeki önemi + gerçek hayat / bilim / yazılım uygulamaları.\n"
                    "Lise-üniversite arası seviyede, akıcı ve motive edici bir dille yaz. "
                    "Uydurma tarihçe veya kaynak verme.")
                user_prompt = (f"Konu: {topic}" +
                               (f"  (bağlam: '{course_name}' kursu)" if course_name else "") +
                               "\n\nBu konu nedir ve ne için kullanılır? Açıkla.")
                text, _usage, finish = self.client.complete(system_prompt, user_prompt,
                                                            profile="math", timeout=180)
                def done():
                    if not win.winfo_exists():
                        return
                    if finish == "error" or text.startswith("AI request failed"):
                        show_text("Açıklama üretilemedi.\n\n" + text +
                                  "\n\nLM Studio'yu başlatıp tekrar dene.",
                                  "✘ AI'ya ulaşılamadı", THEME["danger"])
                        return
                    cache2 = self._topic_info_cache_load()
                    cache2[cache_key] = text
                    self._topic_info_cache_save(cache2)
                    show_text(text, "✔ AI tarafından üretildi ve kaydedildi.", THEME["green"])
                win.after(0, done)
            threading.Thread(target=worker, daemon=True).start()

        def copy_text():
            try:
                self.clipboard_clear()
                self.clipboard_append(txt.get("1.0", "end").strip())
                status.config(text="📋 Panoya kopyalandı.", fg=THEME["green"])
            except Exception:
                pass

        btns = ttk.Frame(win)
        btns.pack(fill="x", padx=12, pady=(0, 10))
        embedded = try_embedded()
        if embedded:
            show_text(embedded["body"],
                      "📚 Yerleşik bilgi bankası — çevrimdışı, anında, gerçek tarih/biyografi "
                      "içerir (AI kullanılmadı).", THEME["green"])
            ai_button["btn"] = RoundedButton(btns, text="🤖 Farklı Açıklama İste (AI)",
                                             parent_bg=THEME["bg"],
                                             command=lambda: ask_ai(force=True))
        else:
            cache = self._topic_info_cache_load()
            if cache.get(cache_key):
                show_text(cache[cache_key],
                          "🤖 Yerel AI tarafından daha önce üretilmiş (kayıtlı) — "
                          "yerleşik bilgi bankasında henüz yok.", THEME["accent"])
            else:
                show_text("Bu konu için yerleşik açıklama henüz eklenmedi.\n\n"
                          "İstersen aşağıdaki '🤖 Yerel AI'dan Sor' düğmesiyle LM Studio'daki "
                          "matematik modeline bu konuyu anlık olarak sorabilirsin — bunun için "
                          "LM Studio'nun açık ve bir modelin yüklü olması gerekir.",
                          "ℹ Henüz belgelenmedi (yerleşik bilgi bankası büyümeye devam ediyor)",
                          THEME["muted"])
            ai_button["btn"] = RoundedButton(btns, text="🤖 Yerel AI'dan Sor",
                                             parent_bg=THEME["bg"], bg=THEME["accent"],
                                             fg="#FFFFFF", hover="#EC8A4B",
                                             command=lambda: ask_ai(force=True))
        ai_button["btn"].pack(side="left", padx=2)
        RoundedButton(btns, text="📋 Kopyala", parent_bg=THEME["bg"],
                      command=copy_text).pack(side="left", padx=2)
        RoundedButton(btns, text="Kapat", parent_bg=THEME["bg"],
                      command=win.destroy).pack(side="right", padx=2)

    def show_tree_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        path = self.path_by_iid.get(iid)
        if not path or not Path(str(path)).is_file():
            return
        course_name = self.tree_course_name(iid)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✅ Bitirdim olarak işaretle",
                         command=lambda: self.set_file_read_status(course_name, path, "done"))
        menu.add_command(label="📖 Okunuyor olarak işaretle",
                         command=lambda: self.set_file_read_status(course_name, path, "reading"))
        menu.add_command(label="İşareti kaldır",
                         command=lambda: self.set_file_read_status(course_name, path, ""))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        path = self.path_by_iid.get(sel[0])
        self.selected_path = path
        # update selected course based on the course row (the display text
        # carries a read counter, so use the stored clean name)
        self.selected_course = self.tree_course_name(sel[0])
        if not path:   # Dersler / Soru Bankaları group headers carry no path
            return
        # V20: selecting a PDF immediately opens it in the PDF viewer.
        try:
            p = Path(path)
            if p.is_file() and p.suffix.lower() == ".pdf":
                self.pdf_viewer.load_pdf(p)
                self.tabs.select(self.pdf_tab)
                self.mark_last_resource(p)
        except Exception as exc:
            self.set_status(f"PDF preview failed: {exc}", THEME["danger"])

    def read_selected(self):
        if not self.selected_path:
            return
        path = Path(self.selected_path)
        if path.is_dir():
            self.open_folder(path)
            return
        if path.suffix.lower() == ".pdf":
            self.pdf_viewer.load_pdf(path)
            self.tabs.select(self.pdf_tab)
            self.mark_last_resource(path)
            return
        # Resource Text tab was removed in V21. Non-PDF files open externally and can still be used as AI context.
        self.open_resource()
        self.mark_last_resource(path)
        self.set_status("Opened resource externally. The AI Tutor can still use this file as context.")

    def set_reader_text(self, text):
        # Kept for backward compatibility with older code paths. Resource Text tab is removed.
        pass

    def open_resource(self):
        if self.selected_path:
            p = Path(self.selected_path)
            if p.exists():
                if os.name == "nt":
                    os.startfile(str(p))
                else:
                    webbrowser.open(str(p))

    def open_folder(self, folder):
        p = Path(folder)
        if p.exists():
            if os.name == "nt":
                os.startfile(str(p))
            else:
                webbrowser.open(str(p))

    def open_selected_location(self):
        """Open the folder that contains the selected course resource.

        On Windows, files are highlighted in Explorer with /select so the student
        can immediately see the exact PDF/worksheet location. If a folder is
        selected, that folder opens directly.
        """
        if not self.selected_path:
            messagebox.showinfo("No resource selected", "Please select a course resource first.")
            return

        p = Path(self.selected_path)
        if not p.exists():
            messagebox.showerror("File not found", f"The selected resource does not exist:\n{p}")
            return

        try:
            if os.name == "nt":
                if p.is_file():
                    subprocess.Popen(["explorer", "/select,", str(p)])
                else:
                    os.startfile(str(p))
            else:
                target = p if p.is_dir() else p.parent
                webbrowser.open(str(target))
            self.set_status("Folder location opened.")
        except Exception as exc:
            messagebox.showerror("Open Folder Location Error", str(exc))

    def print_selected_resource(self):
        """Send the selected file to the operating system's default printer.

        Windows uses the file type's registered Print action. This works best for
        PDFs, images, Word documents, and text files when a default app/printer is
        configured.
        """
        if not self.selected_path:
            messagebox.showinfo("No resource selected", "Please select a printable course resource first.")
            return

        p = Path(self.selected_path)
        if not p.exists():
            messagebox.showerror("File not found", f"The selected resource does not exist:\n{p}")
            return
        if p.is_dir():
            messagebox.showinfo("Cannot print folder", "Please select a file such as a PDF, image, DOCX, or TXT file.")
            return

        try:
            if os.name == "nt":
                os.startfile(str(p), "print")
            else:
                subprocess.Popen(["lpr", str(p)])
            self.set_status("Print command sent to the default printer.")
        except Exception as exc:
            messagebox.showerror(
                "Print Error",
                "Could not send this file to the printer. Make sure a default printer and a default app for this file type are configured.\n\n" + str(exc),
            )

    def mark_last_resource(self, path):
        if not self.selected_course:
            return
        p = self.progress.setdefault(self.selected_course, {})
        p["last_resource"] = str(path)
        p["last_opened"] = now_iso()
        # Opening a file auto-marks it 📖 "reading" (unless already ✅ done), so
        # "hangi konudayım?" is always answered by the tree itself.
        files = p.setdefault("files", {})
        if files.get(str(path)) not in ("done", "reading"):
            files[str(path)] = "reading"
            self._update_tree_item_icon(self.selected_course, str(path))
        safe_json_save(PROGRESS_PATH, self.progress)
        self.build_progress_ui()

    def _find_last_opened(self):
        """(course_name, path, stamp) of the most recently opened resource, or None."""
        best = None
        for cname, data in (self.progress or {}).items():
            if not isinstance(data, dict):
                continue
            path, stamp = data.get("last_resource"), data.get("last_opened", "")
            if not path or not Path(str(path)).exists():
                continue
            if best is None or stamp > best[2]:
                best = (cname, str(path), stamp)
        return best

    def resume_last_resource(self):
        last = self._find_last_opened()
        if not last:
            return
        cname, path, _ = last
        p = Path(path)
        self.selected_path = str(p)
        self.selected_course = cname
        if p.suffix.lower() == ".pdf":
            self.pdf_viewer.load_pdf(p)
            self.tabs.select(self.pdf_tab)
        else:
            self.open_resource()
        self.set_status(("Kaldığın yerden devam: " if self.language == "tr" else "Resumed: ") + p.name)

    @staticmethod
    def _course_name_key(name):
        """Kurs adlarini karsilastirilabilir hale getirir ('&' ve bosluk gurultusu)."""
        return re.sub(r"[^a-z0-9]+", " ", str(name or "").lower().replace("&", "and")).strip()

    def open_course_resource(self, course_name):
        """Belirli bir kursu kaldigi yerden acar (Bugun panosu onerileri).

        Soru bankasindaki kurs adi ile Resources agacindaki klasor adi HER
        ZAMAN birebir ayni degil (paketler klasor adlarina eslenmis, ✂ kirpma
        ise secili kurstan dolduruyor). Bu yuzden once tam, sonra normalize
        edilmis, sonra kapsayan eslesme denenir. Hicbiri tutmazsa False
        doner — cagiran taraf sessiz kalmak yerine kullaniciya soyler.
        """
        hedef = self._course_name_key(course_name)
        if not hedef:
            return False
        # 1) Ilerleme kaydinda bu kursun son actigi dosya var mi?
        for cname, data in (self.progress or {}).items():
            if not isinstance(data, dict):
                continue
            if self._course_name_key(cname) != hedef:
                continue
            path = data.get("last_resource")
            if path and Path(str(path)).exists():
                p = Path(str(path))
                self.selected_path, self.selected_course = str(p), cname
                if p.suffix.lower() == ".pdf":
                    self.pdf_viewer.load_pdf(p)
                    self.tabs.select(self.pdf_tab)
                else:
                    self.open_resource()
                self.set_status(("Kursa devam: " if self.language == "tr"
                                 else "Resumed course: ") + p.name)
                return True
        # 2) Kayit yok ama klasor duruyorsa: agacta kursu sec, kaynak paneline gec
        for course in (self.courses or []):
            ad = course.get("name", "")
            k = self._course_name_key(ad)
            if k == hedef or hedef in k or k in hedef:
                for iid, path in (self.path_by_iid or {}).items():
                    if str(path) == course.get("path"):
                        try:
                            self.tree.see(iid)
                            self.tree.selection_set(iid)
                            self.tree.focus(iid)
                        except Exception:
                            pass
                        break
                self.set_left_panel_visible(True, save=False)
                self.set_status((f"'{ad}' kursu ağaçta seçildi — bir dosya aç."
                                 if self.language == "tr"
                                 else f"Course '{ad}' selected in the tree — open a file."))
                return True
        return False

    def open_question_crop_dialog(self, image_path, source_pdf="", page_number=0):
        """Metadata dialog for a question cropped out of a PDF: course/topic/
        difficulty, optional LaTeX text, A–E choices + correct answer. Saves
        straight into the Student Tracker question bank."""
        tracker = self._ensure_student_tracker()     # tembel: once kur
        if tracker is None:
            messagebox.showwarning("Soru Kırp", "Öğrenci Takip modülü yüklü değil.")
            return
        import student_tracker as _st
        win = tk.Toplevel(self)
        win.title("✂ Soru Kırp → Soru Bankasına Ekle")
        win.configure(bg=THEME["bg"])
        win.transient(self)
        win.grab_set()

        img_label = tk.Label(win, bg=THEME["surface"], bd=1, relief="solid")
        if Image is not None and ImageTk is not None:
            try:
                img = Image.open(image_path)
                img.thumbnail((680, 340))
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo)
                img_label.image = photo
            except Exception as exc:
                img_label.config(text=f"Önizleme açılamadı: {exc}")
        img_label.pack(padx=12, pady=(10, 4))
        src_note = f"Kaynak: {Path(source_pdf).name} · sayfa {page_number}" if source_pdf else ""
        tk.Label(win, text=src_note, bg=THEME["bg"], fg=THEME["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w", padx=14)

        frm = ttk.Frame(win)
        frm.pack(fill="x", padx=12, pady=4)
        course_var = tk.StringVar(value=self.selected_course or "")
        topic_var = tk.StringVar()
        diff_var = tk.StringVar(value="Medium")
        answer_var = tk.StringVar()
        correct_var = tk.StringVar(value="")
        known_courses = sorted({c["name"] for c in self.courses} |
                               set(tracker.store.distinct_values("course")))
        r1 = ttk.Frame(frm); r1.pack(fill="x", pady=2)
        ttk.Label(r1, text="Kurs", width=8).pack(side="left")
        ttk.Combobox(r1, textvariable=course_var, values=known_courses, width=38).pack(side="left")
        ttk.Label(r1, text="Zorluk", width=8).pack(side="left", padx=(10, 0))
        ttk.Combobox(r1, textvariable=diff_var, state="readonly", width=9,
                     values=["Easy", "Medium", "Hard"]).pack(side="left")
        r2 = ttk.Frame(frm); r2.pack(fill="x", pady=2)
        ttk.Label(r2, text="Konu", width=8).pack(side="left")
        ttk.Entry(r2, textvariable=topic_var, width=40).pack(side="left")
        ttk.Label(r2, text="Cevap", width=8).pack(side="left", padx=(10, 0))
        ttk.Entry(r2, textvariable=answer_var, width=14).pack(side="left")

        ttk.Label(frm, text="Soru metni (opsiyonel — $...$ LaTeX destekler; boşsa görsel tek başına kullanılır)",
                  style="Muted.TLabel").pack(anchor="w", pady=(6, 0))
        qtext = tk.Text(frm, height=3, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                        relief="solid", borderwidth=1, font=("Segoe UI", 10))
        qtext.pack(fill="x")

        ttk.Label(frm, text="Şıklar (opsiyonel — dolduranlar sınavda tıklanabilir olur)",
                  style="Muted.TLabel").pack(anchor="w", pady=(6, 0))
        choice_vars = []
        cf = ttk.Frame(frm); cf.pack(fill="x")
        for i, letter in enumerate(_st.CHOICE_LETTERS):
            row, col = divmod(i, 2)
            cell = ttk.Frame(cf)
            cell.grid(row=row, column=col, sticky="we", padx=(0, 8), pady=1)
            ttk.Label(cell, text=f"{letter})", width=3).pack(side="left")
            v = tk.StringVar()
            ttk.Entry(cell, textvariable=v, width=32).pack(side="left", fill="x", expand=True)
            choice_vars.append(v)
        cf.columnconfigure(0, weight=1); cf.columnconfigure(1, weight=1)
        rc = ttk.Frame(frm); rc.pack(fill="x", pady=(4, 0))
        ttk.Label(rc, text="Doğru şık:").pack(side="left")
        ttk.Combobox(rc, textvariable=correct_var, state="readonly", width=4,
                     values=[""] + list(_st.CHOICE_LETTERS)).pack(side="left", padx=4)

        status_lbl = tk.Label(win, text="", bg=THEME["bg"], fg=THEME["danger"], font=("Segoe UI", 9))
        status_lbl.pack(anchor="w", padx=14)

        def save():
            text = qtext.get("1.0", "end").strip()
            if not text:
                base = Path(source_pdf).name if source_pdf else Path(image_path).name
                text = f"[Görsel soru] {base} s.{page_number}"
            choices = [v.get().strip() for v in choice_vars]
            if correct_var.get() and not choices[ord(correct_var.get()) - 65]:
                status_lbl.config(text=f"Doğru şık {correct_var.get()} seçili ama {correct_var.get()} şıkkı boş.")
                return
            qid = tracker.store.add_question(
                text, answer_var.get().strip(), course=course_var.get().strip(),
                topic=topic_var.get().strip(), difficulty=diff_var.get() or "Medium",
                source_pdf=source_pdf, page_number=page_number, tags="kırpılmış",
                image_path=image_path, choices=choices, correct_choice=correct_var.get())
            if qid:
                tracker.refresh_all()
                self.set_status(f"✂ Soru bankaya eklendi (#{qid}).")
                win.destroy()

        btns = ttk.Frame(win)
        btns.pack(fill="x", padx=12, pady=8)
        RoundedButton(btns, text="Bankaya Ekle", parent_bg=THEME["bg"], bg=THEME["green"],
                      fg="#FFFFFF", hover="#23B768", command=save).pack(side="left", padx=2)
        RoundedButton(btns, text="Vazgeç", parent_bg=THEME["bg"],
                      command=win.destroy).pack(side="left", padx=2)

    def build_progress_ui(self):
        for child in self.progress_frame.winfo_children():
            child.destroy()
        # "Kaldığın yer" card: the fastest answer to "nerede kalmıştım?"
        last = self._find_last_opened()
        if last:
            cname, path, _ = last
            box = ttk.Frame(self.progress_frame, style="Panel.TFrame")
            box.pack(fill="x", pady=(0, 8))
            ttk.Label(box, text="📌 Kaldığın yer" if self.language == "tr" else "📌 Continue where you left off",
                      font=("Segoe UI", 9, "bold")).pack(anchor="w")
            tk.Label(box, text=f"{Path(path).name}\n({cname})", justify="left",
                     fg=THEME["muted"], bg=THEME["panel"], font=("Segoe UI", 8),
                     wraplength=270).pack(anchor="w")
            RoundedButton(box, text="▶ Devam Et" if self.language == "tr" else "▶ Resume",
                          parent_bg=THEME["panel"], bg=THEME["accent"], fg="#FFFFFF",
                          hover="#EC8A4B", radius=10, padx=12, pady=6,
                          command=self.resume_last_resource).pack(fill="x", pady=(3, 0))
        # Manual Progress%/Difficulty is collapsed by default per course — with
        # 8+ courses now, showing it expanded for every one made this panel
        # extremely long and mostly duplicated the automatic reading bar right
        # above it. Collapsed keeps each course to ~3 compact lines; nothing
        # is removed, it's one click away.
        if not hasattr(self, "_manual_progress_expanded"):
            self._manual_progress_expanded = {}
        for course in self.courses:
            name = course["name"]
            data = self.progress.setdefault(name, {"percent": 0, "difficulty": "Medium", "feedback": ""})
            box = ttk.Frame(self.progress_frame, style="Panel.TFrame")
            box.pack(fill="x", pady=4)
            ttk.Label(box, text=name, font=("Segoe UI", 9, "bold")).pack(anchor="w")
            # Automatic reading progress from the ✅ marks in the resource tree.
            done, total = self.course_read_stats(course)
            if total:
                pct = int(round(done * 100.0 / total))
                ttk.Label(box, text=f"📖 {done}/{total} dosya bitti  (%{pct})",
                          style="Muted.TLabel").pack(anchor="w")
                rbar = ttk.Progressbar(box, style="Horizontal.TProgressbar",
                                       maximum=100, value=pct)
                rbar.pack(fill="x", pady=(2, 0))
            expanded = self._manual_progress_expanded.get(name, False)
            toggle = tk.Label(box, text=("▴ Elle ilerleme/zorluk" if expanded else "▾ Elle ilerleme/zorluk"),
                              bg=THEME["panel"], fg=THEME["muted"], font=("Segoe UI", 8, "underline"),
                              cursor="hand2")
            toggle.pack(anchor="w", pady=(3, 0))
            toggle.bind("<Button-1>", lambda e, n=name: self._toggle_manual_progress(n))
            if not expanded:
                continue
            row = ttk.Frame(box, style="Panel.TFrame")
            row.pack(fill="x", pady=(2, 0))
            ttk.Label(row, text="Progress %", style="Muted.TLabel").pack(side="left")
            var = tk.IntVar(value=int(data.get("percent", 0)))
            sp = ttk.Spinbox(row, from_=0, to=100, width=5, textvariable=var, command=lambda n=name, v=var: self.set_progress(n, v))
            sp.pack(side="left", padx=4)
            sp.bind("<KeyRelease>", lambda e, n=name, v=var: self.set_progress(n, v))
            ttk.Label(row, text="Difficulty", style="Muted.TLabel").pack(side="left", padx=(8,2))
            diff = ttk.Combobox(row, values=["Easy", "Medium", "Hard"], width=8, state="readonly")
            diff.set(data.get("difficulty", "Medium"))
            diff.pack(side="left")
            diff.bind("<<ComboboxSelected>>", lambda e, n=name, d=diff: self.set_difficulty(n, d.get()))
            # Live progress bar that mirrors the spinbox value.
            bar = ttk.Progressbar(box, style="Horizontal.TProgressbar", maximum=100, value=int(data.get("percent", 0)))
            bar.pack(fill="x", pady=(4, 0))
            def _sync_bar(*_a, _b=bar, _v=var):
                try:
                    _b.configure(value=max(0, min(100, int(_v.get()))))
                except Exception:
                    pass
            var.trace_add("write", _sync_bar)

    def _toggle_manual_progress(self, course_name):
        cur = self._manual_progress_expanded.get(course_name, False)
        self._manual_progress_expanded[course_name] = not cur
        self.build_progress_ui()

    def set_progress(self, name, var):
        try:
            self.progress.setdefault(name, {})["percent"] = int(var.get())
        except Exception:
            pass

    def set_difficulty(self, name, diff):
        self.progress.setdefault(name, {})["difficulty"] = diff

    def save_progress(self):
        safe_json_save(PROGRESS_PATH, self.progress)
        messagebox.showinfo("Saved", f"Progress saved:\n{PROGRESS_PATH}")


    def attach_image(self):
        path = filedialog.askopenfilename(
            title="Attach a problem image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        self.attached_image_path = path
        self.image_label.config(text=f"Attached: {Path(path).name}")
        self.show_image_preview(path)

    def clear_image(self):
        self.attached_image_path = None
        self.attached_image_photo = None
        self.image_label.config(text=self.t("no_image"))
        self.image_preview.config(image="", text="")

    def show_image_preview(self, path):
        if Image is None or ImageTk is None:
            self.image_preview.config(text="Image attached. Preview requires Pillow.", fg=THEME["muted"])
            return
        try:
            img = Image.open(path)
            img.thumbnail((280, 160))
            self.attached_image_photo = ImageTk.PhotoImage(img)
            self.image_preview.config(image=self.attached_image_photo, text="")
        except Exception as exc:
            self.image_preview.config(text=f"Preview failed: {exc}", fg=THEME["danger"])

    def try_ocr_image(self, path):
        """Try OCR first so text-only math models can solve clean screenshots too.

        This uses pytesseract when available. On Windows, the Python package alone is
        not enough; the Tesseract OCR app must also be installed. If OCR is not
        available, the program falls back to the LM Studio vision model path.
        """
        if not path or Image is None:
            return ""
        pytesseract = _lazy_pytesseract()
        if pytesseract is None:
            return ""
        try:
            if os.name == "nt":
                possible = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                ]
                for exe in possible:
                    if Path(exe).exists():
                        try:
                            pytesseract.pytesseract.tesseract_cmd = exe
                        except Exception:
                            pass
                        break
            img = Image.open(path).convert("L")
            # Improve small screenshot OCR by scaling and using a high-contrast threshold.
            w, h = img.size
            if max(w, h) < 1600:
                scale = max(2, int(1600 / max(w, h)))
                img = img.resize((w * scale, h * scale))
            img = img.point(lambda x: 0 if x < 185 else 255)
            text = pytesseract.image_to_string(img, config="--psm 6")
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text.strip()
        except Exception:
            return ""

    def ask_ai_resource(self):
        question = self.question_text.get("1.0", "end").strip()
        if not question:
            messagebox.showwarning("Question required", "Write the topic or question you do not understand.")
            return
        context = ""
        if self.selected_path and Path(self.selected_path).is_file():
            context = read_text_file(self.selected_path, 30_000)
        system = (
            self.ai_language_instruction() + " "
            "You are a math tutor inside a math course companion app. "
            "The app reads local PDF/resource text and sends selected context to you. "
            "Use Qwen2.5 Math style: concise, correct, step-by-step, and focused on the course topic. "
            "Do not claim that you can browse folders directly. If context is insufficient, explain what is missing."
        )
        if self.language == "tr":
            structure = "1. Bu ne anlama geliyor\n2. Adım adım açıklama\n3. Örnek\n4. Pratik ipucu"
            prompt = f"Seçili kurs: {self.selected_course or 'Bilinmiyor'}\nSeçili dosya: {self.selected_path or 'Yok'}\n\nKurs bağlamı:\n{context}\n\nÖğrenci sorusu:\n{question}\n\nŞu yapıyla cevap ver:\n{structure}"
        else:
            structure = "1. What this means\n2. Step-by-step explanation\n3. Example\n4. Practice tip"
            prompt = f"Selected course: {self.selected_course or 'Unknown'}\nSelected file: {self.selected_path or 'None'}\n\nCourse context:\n{context}\n\nStudent question:\n{question}\n\nAnswer with this structure:\n{structure}"
        self.run_ai(system, prompt, kind="resource", image_path=self.attached_image_path, profile="math")

    def solve_attached_image(self):
        if not self.attached_image_path:
            messagebox.showwarning("Image required", "Attach a PNG/JPEG math problem image first.")
            return
        current = self.question_text.get("1.0", "end").strip()
        if not current:
            self.question_text.insert("1.0", "Ekli görseldeki problemi oku ve çöz." if self.language == "tr" else "Read the problem from the attached image and solve it.")
        self.solve_question()

    def solve_question(self):
        q = self.question_text.get("1.0", "end").strip()
        if not q and self.attached_image_path:
            q = "Ekli görseldeki matematik problemini oku ve çöz." if self.language == "tr" else "Read the math problem from the attached image and solve it."
        if not q:
            messagebox.showwarning("Question required", "Paste/type the math question or attach a problem image.")
            return
        # Only use the tiny local solver for typed text, not image instructions.
        if not self.attached_image_path:
            local = LocalSolver.try_solve(q)
            if local:
                self.ai_answer.delete("1.0", "end")
                self.ai_answer.insert("1.0", local)
                return
        context = ""
        if self.selected_path and Path(self.selected_path).is_file():
            context = read_text_file(self.selected_path, 12_000)
        system = (
            self.ai_language_instruction() + " "
            "You are a math solver inside a desktop course app. "
            "If an image is attached, first read/transcribe the visible question from the image, then solve it. "
            "For multiple choice questions, identify the correct option and explain briefly. "
            "Solve clearly, verify the result, and avoid unnecessary extra final boxes."
        )
        if self.language == "tr":
            prompt = f"Kurs/bağlam alıntısı:\n{context}\n\nÖğrenci isteği/sorusu:\n{q}\n\nTam olarak şu formatı kullan:\n1. Verilen / Okunan problem\n2. Çözüm adımları\n3. Sonuç / Doğru seçenek\n4. Kaçınılması gereken yaygın hata"
        else:
            prompt = f"Course/context excerpt:\n{context}\n\nStudent request/question:\n{q}\n\nUse exactly this format:\n1. Given / Transcribed problem\n2. Solution Steps\n3. Result / Correct choice\n4. Common mistake to avoid"
        self.run_ai(system, prompt, kind="answer", image_path=self.attached_image_path, profile="math")

    def create_feedback_report(self):
        course = self.selected_course or "General"
        question = self.question_text.get("1.0", "end").strip()
        answer = self.ai_answer.get("1.0", "end").strip()
        report = f"Feedback Report\nGenerated: {now_iso()}\nCourse: {course}\nResource: {self.selected_path or 'None'}\n\nProgress Data:\n{json.dumps(self.progress.get(course, {}), indent=2)}\n\nStudent Question / Notes:\n{question}\n\nAI / Solver Answer:\n{answer}\n\nSuggested Next Action:\n1. Re-read the selected resource.\n2. Solve two similar questions.\n3. Mark this topic as Hard if it still feels unclear."
        out_dir = Path(self.resource_var.get()).parent if Path(self.resource_var.get()).exists() else APP_FOLDER
        reports = out_dir / "Reports"
        reports.mkdir(parents=True, exist_ok=True)
        fname = reports / f"feedback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        fname.write_text(report, encoding="utf-8")
        messagebox.showinfo("Report Created", str(fname))
        self.open_folder(reports)

    def infer_ai_profile(self, system, prompt, image_path=None):
        text = f"{system}\n{prompt}".lower()
        if any(k in text for k in ["dna", "genom", "genome", "gene", "mutation", "k-mer", "biyoinformatik", "bioinformatics"]):
            return "dna"
        if any(k in text for k in ["chemistry", "kimya", "chemical", "stoichiometry", "stokiyometri", "mole", "mol", "ph", "acid", "base", "asit", "baz", "reaction", "reaksiyon"]):
            return "chemistry"
        if any(k in text for k in ["physics", "fizik", "force", "kuvvet", "velocity", "hız", "acceleration", "ivme", "electric", "wave", "dalga", "newton"]):
            return "physics"
        if any(k in text for k in ["code", "python", "tkinter", "program", "software", "debug", "hata", "kod"]):
            return "code"
        return "math"

    def run_ai(self, system, prompt, kind="answer", image_path=None, profile=None):
        if self.worker_busy:
            messagebox.showinfo("AI Busy", "The current AI request is still running. Please wait.")
            return
        self.worker_busy = True
        profile = profile or self.infer_ai_profile(system, prompt, image_path=image_path)
        self.set_status(f"AI request running... Profile: {profile}", THEME["accent"])
        self.ai_answer.delete("1.0", "end")
        self.ai_answer.insert("1.0", "Working...\n")
        def worker():
            full_prompt = prompt
            if image_path:
                ocr_text = self.try_ocr_image(image_path)
                if ocr_text and len(ocr_text) >= 8:
                    full_prompt += (
                        "\n\nOCR text extracted from attached image. "
                        "Use this as the main problem text; if OCR has small mistakes, correct them from context:\n"
                        f"{ocr_text}"
                    )
                    text, usage, finish = self.client.complete(system, full_prompt, max_tokens=safe_output_tokens(full_prompt, kind), timeout=150, profile=profile)
                else:
                    # Vision-first, math-second pipeline.
                    # The vision model reads/transcribes the image; the math model then
                    # produces the final step-by-step answer. This prevents weak vision
                    # models from stopping at a generic image description.
                    vision_prompt = (
                        "The attached image contains a math problem or worksheet question.\n"
                        "Do NOT describe the paper, background, layout, or colors.\n"
                        "Your job is to extract the actual problem text and answer choices exactly as visible, then solve it.\n"
                        "For multiple choice, include the correct letter and value.\n"
                        "If the image text is partly small or blurry, infer carefully from the visible text.\n\n"
                        f"Student/context prompt:\n{full_prompt}\n\n"
                        "Return this format only:\n"
                        "TRANSCRIBED_PROBLEM: ...\n"
                        "ANSWER_CHOICES: ...\n"
                        "SOLUTION: ...\n"
                        "FINAL_ANSWER: ..."
                    )
                    vision_system = (
                        "You are a vision OCR and math extraction assistant. "
                        "Never answer with a generic image description. Always extract the math question and solve it."
                    )
                    vision_text, vision_usage, vision_finish = self.client.complete_with_image(
                        vision_system,
                        vision_prompt,
                        image_path,
                        max_tokens=safe_output_tokens(vision_prompt, kind),
                        timeout=180,
                    )
                    if vision_finish in ("no_vision_model", "vision_http_error", "vision_error"):
                        text, usage, finish = vision_text, vision_usage, vision_finish
                    else:
                        solve_prompt = (
                            f"{prompt}\n\n"
                            "Vision model extraction / first pass from the attached image:\n"
                            f"{vision_text}\n\n"
                            "Now produce the final math answer. Do not describe the image. "
                            "Use the extracted question/choices as the problem. "
                            "If the problem asks for the identity number for addition, remember that adding 0 leaves any number unchanged.\n\n"
                            "Use exactly this format:\n"
                            "1. Given / Transcribed problem\n"
                            "2. Solution Steps\n"
                            "3. Result / Correct choice\n"
                            "4. Common mistake to avoid"
                        )
                        text, usage, finish = self.client.complete(
                            system,
                            solve_prompt,
                            max_tokens=safe_output_tokens(solve_prompt, kind),
                            timeout=150,
                            profile=profile,
                        )
            else:
                text, usage, finish = self.client.complete(system, full_prompt, max_tokens=safe_output_tokens(full_prompt, kind), timeout=150, profile=profile)
            self.uiq.put(("ai_done", text, usage, finish))
        threading.Thread(target=worker, daemon=True).start()

    def process_ui_queue(self):
        try:
            while True:
                msg = self.uiq.get_nowait()
                if msg[0] == "ai_done":
                    _, text, usage, finish = msg
                    self.ai_answer.delete("1.0", "end")
                    self.ai_answer.insert("1.0", text)
                    self.worker_busy = False
                    total = usage.get("total_tokens", "-") if usage else "-"
                    self.set_status(f"AI complete. Tokens: {total}. Finish: {finish}")
                elif msg[0] == "status":
                    self.set_status(msg[1], msg[2])
                elif msg[0] == "message":
                    messagebox.showinfo(msg[1], msg[2])
                elif msg[0] == "ai_health":
                    self._apply_ai_health(msg[1], msg[2])
        except queue.Empty:
            pass
        self.after(120, self.process_ui_queue)

    # Editable prompt templates for the API Test window ("prompt şablonları").
    PROMPT_TEMPLATES = {
        "Soru Çöz (adım adım)": (
            "Sen deneyimli bir matematik öğretmenisin. Türkçe cevap ver. Adım adım, "
            "öğrencinin seviyesine uygun ve net anlat. Son satırda cevabı 'CEVAP: ...' "
            "biçiminde tekrar et.",
            "Şu soruyu adım adım çöz: 2x + 5 = 17"),
        "Kavram Açıkla": (
            "Sen sabırlı bir matematik öğretmenisin. Türkçe cevap ver. Kavramı önce bir "
            "cümleyle tanımla, sonra günlük hayattan bir örnek ver, sonra kısa bir örnek "
            "soru çöz.",
            "Türev kavramını lise öğrencisine açıkla."),
        "Cevap Kontrol": (
            "Sen bir matematik öğretmenisin. Türkçe cevap ver. Öğrencinin cevabının doğru "
            "olup olmadığını söyle ve tek cümlede gerekçelendir.",
            "Soru: x^2 - 5x + 6 = 0.  Öğrencinin cevabı: x = 2, 3.  Doğru mu?"),
        "İngilizce → Türkçe Çeviri": (
            "You are a math-aware translator. Translate the user's English math text to "
            "clear Turkish, keeping the mathematical notation unchanged.",
            "The derivative of a function measures the instantaneous rate of change."),
    }

    AI_HEALTH_INTERVAL_MS = 30000

    def _check_ai_health_now(self):
        """Tek atimlik AI baglanti denetimi (after zinciri kurmaz).

        client.get_models BILEREK kullanilmaz: onbellegi hata durumunda bayat
        listeyi dondurdugu icin sunucu kapansa bile gosterge yesil kalirdi.
        /v1/models GOVDESI de okunur: sunucu acik ama model yuklu degilse
        200 doner — o durum yesil degil, ayri bir "model yok" durumudur.
        Gosterilen ad, isteklerin GERCEKTE kullanacagi modeldir (ayni
        match_model mantigi), config'teki dilek degil."""
        client = self.client  # worker kosarken Ayarlar client'i degistirebilir
        def worker():
            state, model = "off", ""
            try:
                url = guard_url((client.base_url or "").rstrip("/") + "/v1/models")
                with urllib.request.urlopen(url, timeout=4) as resp:  # nosec B310 - guard_url() allows only http(s)
                    ok = 200 <= getattr(resp, "status", 200) < 300
                    body = resp.read() if ok else b""
                if ok:
                    try:
                        data = json.loads(body.decode("utf-8", errors="ignore"))
                        ids = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
                    except Exception:
                        ids = []
                    if ids:
                        cfg = client.model_profiles.get("math") or client.model or ""
                        model = str(LMStudioClient.match_model(
                            ids, cfg, LMStudioClient.PROFILE_KEYWORDS.get("math", [])))
                        state = "on"
                    else:
                        state = "no_model"
            except Exception:
                state = "off"
            try:
                self.uiq.put(("ai_health", state, model))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _poll_ai_health(self):
        """Periyodik denetim: tek atimlik kontrol + kendini yeniden kurma."""
        self._check_ai_health_now()
        self.after(self.AI_HEALTH_INTERVAL_MS, self._poll_ai_health)

    def _apply_ai_health(self, state, model=""):
        lbl = getattr(self, "ai_status_label", None)
        if lbl is None:
            return
        if state is True:
            state = "on"
        elif state is False:
            state = "off"
        self._ai_health_last = (state, model)
        if state == "on":
            short = (model or "").split("/")[-1]
            if len(short) > 26:
                short = short[:23] + "…"
            text = self.t("ai_status_on") + (f" · {short}" if short else "")
            lbl.config(text=text, fg=THEME["green"])
        elif state == "no_model":
            lbl.config(text=self.t("ai_status_no_model"), fg=THEME["accent"])
        else:
            lbl.config(text=self.t("ai_status_off"), fg=THEME["danger"])

    # ────────────────────────────────────────── ℹ Hakkında + 💾 Yedek durumu ──
    def _backup_dir(self):
        """Drive yedek klasörü (scripts/common.ps1 ile AYNI yol) → Path ya da None.

        Yol kişiye özeldir; scripts/local_config.ps1 varsa oradaki değer
        kazanır. Klasör yoksa None döner — uydurma tarih gösterilmez.
        """
        adaylar = []
        for dosya in ("scripts/local_config.ps1", "scripts/common.ps1"):
            p = Path(__file__).resolve().parent / dosya
            try:
                if not p.exists():
                    continue
                for satir in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "DriveBackupPattern" in satir and "=" in satir:
                        deger = satir.split("=", 1)[1].strip().strip("'\"")
                        if deger and not deger.startswith("#"):
                            adaylar.append(deger)
            except Exception:
                continue
        for ham in adaylar:
            try:
                # Desen joker icerebilir; en yeni eslesen klasoru al.
                eslesenler = [Path(x) for x in glob.glob(ham) if Path(x).is_dir()]
                if eslesenler:
                    return max(eslesenler, key=lambda x: x.stat().st_mtime)
                p = Path(ham)
                if p.is_dir():
                    return p
            except Exception:
                continue
        return None

    def backup_health(self):
        """(durum, mesaj) — durum: 'ok' | 'eski' | 'yok' | 'klasor_yok'.

        Uydurma yok: klasör bulunamazsa 'bilinmiyor' denir, tarih tahmin edilmez.
        """
        klasor = self._backup_dir()
        if klasor is None:
            return "klasor_yok", self.t2x("Yedek klasörü bulunamadı",
                                          "Backup folder not found")
        try:
            arsivler = [p for p in klasor.iterdir()
                        if p.is_file() and p.suffix.lower() in (".rar", ".zip", ".7z")]
        except Exception:
            return "klasor_yok", self.t2x("Yedek klasörü okunamadı",
                                          "Backup folder unreadable")
        if not arsivler:
            return "yok", self.t2x("Henüz yedek alınmamış", "No backup taken yet")
        son = max(arsivler, key=lambda p: p.stat().st_mtime)
        gun = int((time.time() - son.stat().st_mtime) // 86400)
        if gun <= 0:
            metin = self.t2x("Son yedek: bugün", "Last backup: today")
        elif gun == 1:
            metin = self.t2x("Son yedek: dün", "Last backup: yesterday")
        else:
            metin = self.t2x(f"Son yedek: {gun} gün önce",
                             f"Last backup: {gun} days ago")
        return ("ok" if gun <= 7 else "eski"), metin

    def t2x(self, tr, en):
        """Kısa iki dilli metin (ana dosyanın UI_TEXT'ine girmeyecek kadar dinamik)."""
        return en if str(getattr(self, "language", "tr")).lower().startswith("en") else tr

    def _backup_menu_label(self):
        durum, mesaj = self.backup_health()
        isaret = {"ok": "💾", "eski": "⚠", "yok": "⚠", "klasor_yok": "❔"}.get(durum, "💾")
        return f"{isaret} {mesaj}"

    def open_backup_folder(self):
        """Yedek klasörünü açar; yoksa nedenini durum çubuğunda söyler."""
        durum, mesaj = self.backup_health()
        klasor = self._backup_dir()
        if klasor is None:
            self.set_status(mesaj + self.t2x(
                " — scripts/local_config.ps1 ile kendi klasörünü tanımlayabilirsin.",
                " — you can point it at your own folder with scripts/local_config.ps1."),
                THEME["danger"])
            return
        self.open_folder(klasor)
        self.set_status(mesaj)

    def open_about(self):
        """ℹ Hakkında: sürüm, açıklama, kısayollar, sürüm geçmişi, lisans."""
        try:
            import surum_notlari
        except Exception as exc:
            messagebox.showwarning("Hakkında", f"surum_notlari yüklenemedi: {exc}")
            return
        win = getattr(self, "_about_win", None)
        if win is not None and win.winfo_exists():
            win.deiconify(); win.lift(); return
        win = tk.Toplevel(self)
        self._about_win = win
        win.title(self.t("about") + " — " + surum_notlari.APP_ADI)
        win.geometry("760x620")
        win.configure(bg=THEME["bg"])
        tk.Label(win, text=f"{surum_notlari.APP_ADI}", bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=16, pady=(14, 0))
        tk.Label(win, text=f"{surum_notlari.SURUM}  ·  {surum_notlari.SURUM_TARIH}",
                 bg=THEME["bg"], fg=THEME["accent"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16)
        tk.Label(win, text=(surum_notlari.SLOGAN_EN if self.language == "en"
                            else surum_notlari.SLOGAN),
                 bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 10),
                 wraplength=700, justify="left").pack(anchor="w", padx=16, pady=(4, 8))
        kutu = tk.Text(win, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                       insertbackground=THEME["text"], relief="flat",
                       font=("Consolas", 10))
        kutu.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        kutu.insert("1.0", surum_notlari.hakkinda_metni(self.language))
        kutu.configure(state="disabled")
        alt = tk.Frame(win, bg=THEME["bg"])
        alt.pack(fill="x", padx=16, pady=(0, 14))
        RoundedButton(alt, text=self.t("user_guide"), parent_bg=THEME["bg"],
                      command=self.open_user_guide).pack(side="left")

        def panoya():
            try:
                self.clipboard_clear()
                self.clipboard_append(surum_notlari.hakkinda_metni(self.language))
                self.set_status(self.t2x("Hakkında metni panoya kopyalandı.",
                                         "About text copied to the clipboard."))
            except Exception:
                pass

        RoundedButton(alt, text=self.t2x("📋 Panoya kopyala", "📋 Copy"),
                      parent_bg=THEME["bg"], command=panoya).pack(side="left", padx=8)
        RoundedButton(alt, text=self.t2x("Kapat", "Close"), parent_bg=THEME["bg"],
                      command=win.destroy).pack(side="right")
        return win

    def open_user_guide(self):
        """🎓 Kullanma Kilavuzu — arayuz diliyle acilir (tarayicida)."""
        try:
            import education
            ok, sonuc = education.kilavuz_ac(self.language)
        except Exception as exc:
            ok, sonuc = False, str(exc)
        if ok:
            self.set_status(self.t("guide_opened"), THEME["green"])
        else:
            self.set_status(self.t("guide_failed").format(err=sonuc), THEME["danger"])

    def open_token_ledger(self):
        """📒 Token Defteri — acik pencere varsa one getirir."""
        win = getattr(self, "_token_ledger_win", None)
        try:
            if win is not None and win.winfo_exists():
                win.lift()
                win.focus_force()
                return
        except Exception:
            pass
        try:
            import token_ledger
            self._token_ledger_win = token_ledger.token_defteri_ac(self)
        except Exception as exc:
            self.set_status(f"Token defteri açılamadı: {exc}", THEME["danger"])

    def open_ai_terminal(self):
        """🖥 AI Terminali — acik pencere varsa one getirir, yoksa acar."""
        win = getattr(self, "_ai_terminal_win", None)
        try:
            if win is not None and win.winfo_exists():
                win.lift()
                win.focus_force()
                return
        except Exception:
            pass
        try:
            import ai_terminal
            self._ai_terminal_win = ai_terminal.ai_terminali_ac(self)
        except Exception as exc:
            self.set_status(f"AI Terminali açılamadı: {exc}", THEME["danger"])

    def test_api(self, silent=False):
        if not silent:
            self.open_api_test_window()
            return
        def worker():
            try:
                report, suggestions = self.client.profile_report()
                chosen = suggestions.get("math") or self.client.choose_model()
                self.uiq.put(("status", f"API connected. Math model: {chosen}", THEME["green"]))
            except Exception as exc:
                self.uiq.put(("status", f"API not connected: {exc}", THEME["danger"]))
        threading.Thread(target=worker, daemon=True).start()
        self.after(150, self._process_non_ai_messages)

    def open_api_test_window(self):
        """API Test: connection + profile report AND a live prompt-template
        tester (profile seç, şablonu düzenle, gönder, gecikme/token gör)."""
        win = tk.Toplevel(self)
        win.title("API Test — LM Studio & Prompt Şablonları")
        win.geometry("900x760")
        win.configure(bg=THEME["bg"])
        win.transient(self)

        head = ttk.Frame(win); head.pack(fill="x", padx=12, pady=(10, 2))
        status_lbl = tk.Label(head, text="Bağlantı test ediliyor…", bg=THEME["bg"],
                              fg=THEME["muted"], font=("Segoe UI", 10, "bold"))
        status_lbl.pack(side="left")
        report_txt = tk.Text(win, height=8, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                             relief="solid", borderwidth=1, font=("Consolas", 9))
        report_txt.pack(fill="x", padx=12, pady=4)
        report_txt.config(state="disabled")

        def set_report(msg, ok):
            if not win.winfo_exists():
                return
            status_lbl.config(text="✔ LM Studio bağlı" if ok else "✘ Bağlantı yok",
                              fg=THEME["green"] if ok else THEME["danger"])
            report_txt.config(state="normal")
            report_txt.delete("1.0", "end")
            report_txt.insert("1.0", msg)
            report_txt.config(state="disabled")

        def run_connection_test():
            def worker():
                try:
                    report, suggestions = self.client.profile_report()
                    chosen = suggestions.get("math") or ""
                    self.uiq.put(("status", f"API connected. Math model: {chosen}", THEME["green"]))
                    win.after(0, lambda: set_report(report, True))
                except Exception as exc:
                    self.uiq.put(("status", f"API not connected: {exc}", THEME["danger"]))
                    win.after(0, lambda e=exc: set_report(
                        f"Bağlantı kurulamadı: {e}\n\nLM Studio > Local Server'ı başlat "
                        f"({self.client.base_url}) ve bir model yükle.", False))
            threading.Thread(target=worker, daemon=True).start()
            self.after(150, self._process_non_ai_messages)

        RoundedButton(head, text="Yeniden Test Et", parent_bg=THEME["bg"],
                      command=run_connection_test).pack(side="right")

        ttk.Label(win, text="Prompt Şablonu Testi", style="Header.TLabel").pack(anchor="w", padx=12, pady=(8, 0))
        ctl = ttk.Frame(win); ctl.pack(fill="x", padx=12, pady=2)
        ttk.Label(ctl, text="Şablon:").pack(side="left")
        tmpl_var = tk.StringVar(value=next(iter(self.PROMPT_TEMPLATES)))
        tmpl_cb = ttk.Combobox(ctl, textvariable=tmpl_var, state="readonly", width=28,
                               values=list(self.PROMPT_TEMPLATES))
        tmpl_cb.pack(side="left", padx=4)
        ttk.Label(ctl, text="Profil:").pack(side="left", padx=(10, 0))
        profile_var = tk.StringVar(value="math")
        ttk.Combobox(ctl, textvariable=profile_var, state="readonly", width=10,
                     values=["math", "science", "physics", "chemistry", "dna", "code"]).pack(side="left", padx=4)
        metrics_lbl = tk.Label(ctl, text="", bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 9))
        metrics_lbl.pack(side="right")

        ttk.Label(win, text="System prompt (düzenlenebilir)", style="Muted.TLabel").pack(anchor="w", padx=12)
        sys_txt = tk.Text(win, height=4, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                          relief="solid", borderwidth=1, font=("Segoe UI", 9))
        sys_txt.pack(fill="x", padx=12)
        ttk.Label(win, text="Kullanıcı mesajı", style="Muted.TLabel").pack(anchor="w", padx=12, pady=(4, 0))
        user_txt = tk.Text(win, height=3, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                           relief="solid", borderwidth=1, font=("Segoe UI", 9))
        user_txt.pack(fill="x", padx=12)

        def load_template(*_a):
            sp, up = self.PROMPT_TEMPLATES.get(tmpl_var.get(), ("", ""))
            sys_txt.delete("1.0", "end"); sys_txt.insert("1.0", sp)
            user_txt.delete("1.0", "end"); user_txt.insert("1.0", up)
        tmpl_cb.bind("<<ComboboxSelected>>", load_template)
        load_template()

        out_txt = tk.Text(win, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                          relief="solid", borderwidth=1, font=("Segoe UI", 10))
        out_txt.pack(fill="both", expand=True, padx=12, pady=(6, 4))

        def send():
            sp = sys_txt.get("1.0", "end").strip()
            up = user_txt.get("1.0", "end").strip()
            if not up:
                return
            metrics_lbl.config(text="gönderiliyor…")
            out_txt.delete("1.0", "end")
            out_txt.insert("1.0", "⏳ Model düşünüyor…")
            t0 = time.time()
            def worker():
                text, usage, finish = self.client.complete(sp, up, profile=profile_var.get(), timeout=120)
                dt = time.time() - t0
                def show():
                    if not win.winfo_exists():
                        return
                    out_txt.delete("1.0", "end")
                    out_txt.insert("1.0", text)
                    metrics_lbl.config(
                        text=f"{dt:.1f} sn  •  prompt {usage.get('prompt_tokens', '?')} tok  •  "
                             f"cevap {usage.get('completion_tokens', '?')} tok  •  finish: {finish or '-'}")
                win.after(0, show)
            threading.Thread(target=worker, daemon=True).start()

        brow = ttk.Frame(win); brow.pack(fill="x", padx=12, pady=(0, 10))
        RoundedButton(brow, text="Gönder ▶", parent_bg=THEME["bg"], bg=THEME["accent"],
                      fg="#FFFFFF", hover="#EC8A4B", command=send).pack(side="left")
        RoundedButton(brow, text="Kapat", parent_bg=THEME["bg"], command=win.destroy).pack(side="right")
        run_connection_test()

    def _process_non_ai_messages(self):
        try:
            while True:
                msg = self.uiq.get_nowait()
                if msg[0] == "status":
                    self.set_status(msg[1], msg[2])
                elif msg[0] == "message":
                    messagebox.showinfo(msg[1], msg[2])
                else:
                    self.uiq.put(msg)
                    break
        except queue.Empty:
            return

    def open_settings(self):
        win = tk.Toplevel(self)
        win.title(self.t("settings"))
        win.geometry("980x720")
        win.configure(bg=THEME["bg"])
        ttk.Label(win, text="Local AI Model Profiles / Yerel AI Model Profilleri", style="Header.TLabel").pack(fill="x", padx=12, pady=10)
        frm = ttk.Frame(win)
        frm.pack(fill="both", expand=True, padx=12, pady=8)
        base = tk.StringVar(value=self.config_data.get("base_url", DEFAULT_BASE_URL))
        math_model = tk.StringVar(value=self.config_data.get("math_model", self.config_data.get("model", DEFAULT_MATH_MODEL)))
        science_model = tk.StringVar(value=self.config_data.get("science_model", DEFAULT_SCIENCE_MODEL))
        physics_model = tk.StringVar(value=self.config_data.get("physics_model", self.config_data.get("science_model", DEFAULT_PHYSICS_MODEL)))
        chemistry_model = tk.StringVar(value=self.config_data.get("chemistry_model", DEFAULT_CHEMISTRY_MODEL))
        dna_model = tk.StringVar(value=self.config_data.get("dna_model", DEFAULT_DNA_MODEL))
        vision_model = tk.StringVar(value=self.config_data.get("vision_model", DEFAULT_VISION_MODEL))
        code_model = tk.StringVar(value=self.config_data.get("code_model", DEFAULT_CODE_MODEL))
        res = tk.StringVar(value=self.resource_var.get())
        lang = tk.StringVar(value=self.language)

        rows = [
            ("LM Studio Base URL", base),
            ("Math Model / Matematik", math_model),
            ("General Science / Genel Bilim", science_model),
            ("Physics Model / Fizik", physics_model),
            ("Chemistry Model / Kimya", chemistry_model),
            ("DNA / Bio Model", dna_model),
            ("Vision Model / Görsel", vision_model),
            ("Code Model / Kod", code_model),
            ("Resources Folder", res),
        ]
        for label, var in rows:
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label, width=28).pack(side="left")
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)

        lang_row = ttk.Frame(frm)
        lang_row.pack(fill="x", pady=6)
        ttk.Label(lang_row, text="UI + AI Language / Dil", width=28).pack(side="left")
        ttk.Radiobutton(lang_row, text="Türkçe", variable=lang, value="tr").pack(side="left", padx=4)
        ttk.Radiobutton(lang_row, text="English", variable=lang, value="en").pack(side="left", padx=4)

        startup = tk.StringVar(value=self.config_data.get("startup_view", "last"))
        # Pencere modal degil: acikken ☰ menuden ayni ayar degistirilebilir.
        # save() bu yuzden yalnizca BU pencerede gercekten degistirildiyse yazar;
        # yoksa menuden gelen guncel deger bayat anlik goruntuyle ezilirdi.
        startup_initial = startup.get()
        theme_var = tk.StringVar(value=self.config_data.get("theme", "light"))
        theme_initial = theme_var.get()
        sv_row = ttk.Frame(frm)
        sv_row.pack(fill="x", pady=6)
        ttk.Label(sv_row, text="Startup screen / Açılış ekranı", width=28).pack(side="left")
        ttk.Radiobutton(sv_row, text="Last session / Son oturum", variable=startup, value="last").pack(side="left", padx=4)
        ttk.Radiobutton(sv_row, text="Today dashboard / Bugün panosu", variable=startup, value="today").pack(side="left", padx=4)

        th_row = ttk.Frame(frm)
        th_row.pack(fill="x", pady=6)
        ttk.Label(th_row, text="Theme / Tema (restart)", width=28).pack(side="left")
        ttk.Radiobutton(th_row, text="☀ Light / Açık", variable=theme_var, value="light").pack(side="left", padx=4)
        ttk.Radiobutton(th_row, text="🌙 Dark / Koyu", variable=theme_var, value="dark").pack(side="left", padx=4)

        info = (
            "Recommended local LM Studio mapping:\n"
            "• Math: qwen2.5-math-7b-instruct\n"
            "• Vision: qwen3-vl-8b or qwen2.5-vl-7b-instruct\n"
            "• DNA/Bio: BioMistral-7B-GGUF-Q5_K_M\n"
            "• Chemistry/Science: Mistral Small 3.2 24B Instruct or qwen3-vl-8b\n"
            "The program auto-detects loaded LM Studio models and routes AI calls by profile. Local server must be running."
        )
        ttk.Label(frm, text=info, style="Muted.TLabel").pack(fill="x", pady=10)

        def save(close_after=True):
            self.config_data["base_url"] = base.get().strip() or DEFAULT_BASE_URL
            self.config_data["model"] = math_model.get().strip() or DEFAULT_MATH_MODEL
            self.config_data["math_model"] = math_model.get().strip() or DEFAULT_MATH_MODEL
            self.config_data["science_model"] = science_model.get().strip() or DEFAULT_SCIENCE_MODEL
            self.config_data["physics_model"] = physics_model.get().strip() or science_model.get().strip() or DEFAULT_PHYSICS_MODEL
            self.config_data["chemistry_model"] = chemistry_model.get().strip() or DEFAULT_CHEMISTRY_MODEL
            self.config_data["dna_model"] = dna_model.get().strip() or DEFAULT_DNA_MODEL
            self.config_data["vision_model"] = vision_model.get().strip() or DEFAULT_VISION_MODEL
            self.config_data["code_model"] = code_model.get().strip() or DEFAULT_CODE_MODEL
            self.config_data["resource_dir"] = res.get().strip() or DEFAULT_RESOURCE_DIR
            self.config_data["language"] = lang.get() if lang.get() in ("tr", "en") else "tr"
            if startup.get() != startup_initial:
                self.config_data["startup_view"] = startup.get() if startup.get() in ("last", "today") else "last"
            theme_changed = theme_var.get() != theme_initial
            if theme_changed:
                self.config_data["theme"] = theme_var.get() if theme_var.get() in ("light", "dark") else "light"
            self.language = self.config_data["language"]
            self.resource_var.set(self.config_data["resource_dir"])
            safe_json_save(CONFIG_PATH, self.config_data)
            self.client = LMStudioClient(self.config_data["base_url"], self.config_data["math_model"], self.config_data["vision_model"], self.config_data)
            # Eski sunucuya ait gosterge durumu yeni client icin gecersiz:
            # once "kontrol ediliyor"a dusur, sonra aninda yeniden yokla
            # (yoksa 30 sn'lik periyoda kadar bayat yesil/kirmizi kalirdi).
            self._ai_health_last = None
            self.apply_language_to_window()
            self.refresh_resources()
            self._check_ai_health_now()
            # Tema notu EN SON: "Model profiles saved" onu ezmesin (yeniden
            # baslatma bilgisi kullanicinin gormesi gereken mesaj).
            if theme_changed:
                self.set_status(self.t("theme_saved"), THEME["accent"])
            else:
                self.set_status("Model profiles saved / Model profilleri kaydedildi", THEME["green"])
            if close_after:
                win.destroy()

        def auto_detect():
            try:
                temp_client = LMStudioClient(base.get().strip() or DEFAULT_BASE_URL, math_model.get(), vision_model.get(), self.config_data)
                models = temp_client.get_models()
                suggestions = LMStudioClient.suggest_profiles_from_models(models, self.config_data)
                math_model.set(suggestions.get("math", math_model.get()))
                science_model.set(suggestions.get("science", science_model.get()))
                physics_model.set(suggestions.get("physics", physics_model.get()))
                chemistry_model.set(suggestions.get("chemistry", chemistry_model.get()))
                dna_model.set(suggestions.get("dna", dna_model.get()))
                vision_model.set(suggestions.get("vision", vision_model.get()))
                code_model.set(suggestions.get("code", code_model.get()))
                messagebox.showinfo("Auto Detect", "Loaded LM Studio models were mapped to profiles. Review them, then Save.\n\n" + "\n".join(models))
            except Exception as exc:
                messagebox.showerror("Auto Detect Failed", str(exc))

        btns = ttk.Frame(win)
        btns.pack(fill="x", padx=12, pady=12)
        RoundedButton(btns, text="Auto Detect Loaded Models", command=auto_detect).pack(side="left", padx=4)
        RoundedButton(btns, text="Test API + Profiles", command=lambda: (save(close_after=False), self.test_api(silent=False))).pack(side="left", padx=4)
        RoundedButton(btns, text=self.t("save"), command=lambda: save(close_after=True)).pack(side="right", padx=4)
        RoundedButton(btns, text=self.t("close"), command=win.destroy).pack(side="right", padx=4)

    def show_token_reports(self):
        win = tk.Toplevel(self)
        win.title("Token Usage Reports")
        win.geometry("850x600")
        ttk.Label(win, text="Token Usage Reports", style="Header.TLabel").pack(fill="x", padx=10, pady=8)
        txt = tk.Text(win, wrap="none", bg=THEME["surface"], fg=THEME["text"], font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=10, pady=8)
        records = []
        if TOKEN_LOG_PATH.exists():
            for line in TOKEN_LOG_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-500:]:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
        total = sum(r.get("total_tokens", 0) for r in records)
        txt.insert("end", f"Log file: {TOKEN_LOG_PATH}\nRecords shown: {len(records)}\nTotal tokens shown: {total}\n\n")
        for r in records[-100:]:
            txt.insert("end", json.dumps(r, ensure_ascii=False) + "\n")

    def open_log_folder(self):
        self.open_folder(APP_FOLDER)


if __name__ == "__main__":
    app = MathCourseApp()
    # handle non-AI status queue too
    def pump_misc():
        app._process_non_ai_messages()
        app.after(500, pump_misc)
    app.after(500, pump_misc)
    app.mainloop()
