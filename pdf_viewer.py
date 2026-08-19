# -*- coding: utf-8 -*-
"""Math Course AI — PDF goruntuleyici ve ayna paneli.

Ana dosyadan (Math_Course_AI.pyw) V48'de mekanik olarak cikarildi.
PDFViewer: zoom/sayfa/annotasyon (kalem-isaretleme-metin-silgi),
notlari %APPDATA% sidecar'ina kaydetme, isaretli PDF disa aktarma,
✂ Soru Kirp. ResourceMirrorPanel: Cift Pencere duzeninin salt-okunur
es goruntuleyicisi. Her ikisi (master, app) alir.
"""

import os
import re
import io
import json
import math
import time
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog


try:
    from mca_common import app_lang, t2
except Exception:      # mca_common yoksa panel yine Türkçe çalışsın
    def app_lang(app, default="tr"):
        try:
            return "en" if str(getattr(app, "language", default)).lower().startswith("en") else "tr"
        except Exception:
            return "tr"

    def t2(tr, en, lang="tr"):
        return en if (str(lang).lower().startswith("en") and en) else tr

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

from mca_common import ANNOTATION_DIR, APP_FOLDER, THEME, RoundedButton, short_name
from whiteboard import MathWhiteboard

class ResourceMirrorPanel(ttk.Frame):
    """A course-resource tree used inside a separate dual reader window (A or B).

    It drives ONLY its own PDFViewer (the app attribute named by `viewer_attr`,
    e.g. "pdf_viewer_a" / "pdf_viewer_b") via its own `self.selected_path`, fully
    independent of the other reader. It reads app.courses (the same scanned
    data); the main window's resource panel + app.pdf_viewer are never touched.
    """

    def __init__(self, master, app, viewer_attr="pdf_viewer_b", label_suffix=" (B)"):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        self.viewer_attr = viewer_attr   # which app PDFViewer this tree drives
        self.path_by_iid = {}
        self.selected_path = None
        ttk.Label(self, text=app.t("course_resources") + label_suffix, style="Header.TLabel").pack(fill="x", padx=8, pady=(8, 4))
        srow = ttk.Frame(self, style="Panel.TFrame")
        srow.pack(fill="x", padx=8, pady=(0, 4))
        self.search_var = tk.StringVar()
        ent = ttk.Entry(srow, textvariable=self.search_var)
        ent.pack(side="left", fill="x", expand=True)
        ent.bind("<KeyRelease>", lambda e: self.populate())
        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        btns = ttk.Frame(self, style="Panel.TFrame")
        btns.pack(fill="x", padx=8, pady=(0, 8))
        RoundedButton(btns, text=app.t("read_show"), parent_bg=THEME["panel"], bg=THEME["accent"],
                      fg="#FFFFFF", hover="#EC8A4B", command=self._read).pack(side="left", fill="x", expand=True, padx=2, pady=2)
        RoundedButton(btns, text=app.t("open_resource"), parent_bg=THEME["panel"],
                      command=self._open_external).pack(side="left", fill="x", expand=True, padx=2, pady=2)
        self.populate()

    def populate(self):
        self.tree.delete(*self.tree.get_children())
        self.path_by_iid.clear()
        query = self.search_var.get().strip().lower()

        def match(path):
            return not query or query in Path(path).name.lower() or query in str(path).lower()

        for course in getattr(self.app, "courses", []) or []:
            ciid = self.tree.insert("", "end", text=course["name"], open=True)
            self.path_by_iid[ciid] = course["path"]
            for res in course.get("resources", []):
                if match(res):
                    iid = self.tree.insert(ciid, "end", text="📄 " + res.name)
                    self.path_by_iid[iid] = str(res)
            for sec in course.get("children", []):
                self._add_section(ciid, sec, match)

    def _add_section(self, parent, sec, match):
        siid = self.tree.insert(parent, "end", text="📁 " + sec["name"], open=False)
        self.path_by_iid[siid] = sec["path"]
        count = 0
        for item in sec.get("items", []):
            if match(item):
                iid = self.tree.insert(siid, "end", text="📄 " + item.name)
                self.path_by_iid[iid] = str(item)
                count += 1
        for child in sec.get("children", []):
            self._add_section(siid, child, match)
            count += 1
        if self.search_var.get().strip() and count:
            self.tree.item(siid, open=True)

    def _viewer(self):
        return getattr(self.app, self.viewer_attr, None)

    def _on_select(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        path = self.path_by_iid.get(sel[0])
        if not path:
            return
        self.selected_path = path  # this reader's OWN selection, independent of the other
        vb = self._viewer()
        if vb is None:
            return
        try:
            p = Path(path)
            if p.is_file() and p.suffix.lower() == ".pdf":
                vb.load_pdf(p)
        except Exception:
            pass

    def _read(self):
        """Open B's current selection in the B reader (or externally)."""
        if not self.selected_path:
            return
        p = Path(self.selected_path)
        vb = self._viewer()
        try:
            if p.is_dir():
                self.app.open_folder(p)
            elif p.suffix.lower() == ".pdf" and vb is not None:
                vb.load_pdf(p)
            else:
                self._open_external()
        except Exception:
            pass

    def _open_external(self):
        if not self.selected_path:
            return
        p = Path(self.selected_path)
        if p.exists():
            try:
                if os.name == "nt":
                    os.startfile(str(p))
                else:
                    webbrowser.open(str(p))
            except Exception:
                pass


class PDFViewer(ttk.Frame):

    def _t(self, tr, en):
        """Panel metni: dil, panel kurulurken sahibinden okunur."""
        return t2(tr, en, getattr(self, "lang", "tr"))

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.lang = app_lang(getattr(self, "app", None))
        self.path = None
        self.doc = None
        self.page_index = 0
        self.zoom = 1.25
        self.photo = None
        self.mode = "select"
        self.annotations = []
        self.current_draw = None
        self.selected_ann = None
        self.dragging_ann = False
        self.drag_offset = (0, 0)
        self.default_text_size = 14
        self.default_text_color = "#2563eb"
        self._build()

    def _build(self):
        tb = ttk.Frame(self)
        tb.pack(fill="x", padx=4, pady=3)
        RoundedButton(tb, text="Open External", command=self.open_external).pack(side="left", padx=2)
        RoundedButton(tb, text="◀", command=self.prev_page).pack(side="left", padx=2)
        self.page_var = tk.StringVar(value="1")
        self.page_entry = ttk.Entry(tb, textvariable=self.page_var, width=6)
        self.page_entry.pack(side="left", padx=(4, 2))
        self.page_entry.bind("<Return>", lambda e: self.go_page())
        RoundedButton(tb, text="Go", command=self.go_page).pack(side="left", padx=2)
        self.page_label = ttk.Label(tb, text="/ -")
        self.page_label.pack(side="left", padx=5)
        RoundedButton(tb, text="▶", command=self.next_page).pack(side="left", padx=2)
        RoundedButton(tb, text="Zoom -", command=lambda: self.change_zoom(0.85)).pack(side="left", padx=2)
        RoundedButton(tb, text="Zoom +", command=lambda: self.change_zoom(1.18)).pack(side="left", padx=2)
        RoundedButton(tb, text="Fit Width", command=self.fit_width).pack(side="left", padx=2)
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=6)
        RoundedButton(tb, text="Select/Move", command=lambda: self.set_mode("select")).pack(side="left", padx=2)
        RoundedButton(tb, text="Pen", command=lambda: self.set_mode("pen")).pack(side="left", padx=2)
        RoundedButton(tb, text="Highlight", command=lambda: self.set_mode("highlight")).pack(side="left", padx=2)
        RoundedButton(tb, text="Text", command=lambda: self.set_mode("text")).pack(side="left", padx=2)
        RoundedButton(tb, text="Eraser", command=lambda: self.set_mode("erase")).pack(side="left", padx=2)
        RoundedButton(tb, text=self._t("✂ Soru Kırp", "✂ Clip question"), bg=THEME["accent"], fg="#FFFFFF", hover="#EC8A4B",
                      parent_bg=THEME["bg"], command=lambda: self.set_mode("crop")).pack(side="left", padx=2)
        RoundedButton(tb, text="Text -", command=lambda: self.change_text_size(-2)).pack(side="left", padx=2)
        RoundedButton(tb, text="Text +", command=lambda: self.change_text_size(2)).pack(side="left", padx=2)
        RoundedButton(tb, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=2)
        RoundedButton(tb, text="Save Notes", style="Save.TButton", command=self.save_annotations).pack(side="left", padx=2)
        RoundedButton(tb, text="Export Annotated PDF", command=self.export_annotated_pdf).pack(side="left", padx=2)
        RoundedButton(tb, text="Ekran Alintisi ile Gonder", command=self.send_screenshot_hint_to_visual_math).pack(side="left", padx=2)
        RoundedButton(tb, text="Translate Screenshot", command=lambda: self.app.open_image_translation()).pack(side="left", padx=2)
        self.mode_label = ttk.Label(tb, text="Mode: Select")
        self.mode_label.pack(side="right", padx=6)
        # Smart Wacom Student Board show/hide + pop-out (frees PDF width).
        self.wacom_var = tk.BooleanVar(value=True)
        RoundedButton(tb, text=self._t("Tablet Çizimi Ayrı Pencerede Aç", "Open drawing board in a window"), command=self.popout_wacom).pack(side="right", padx=2)
        ttk.Checkbutton(tb, text=self._t("Tablet Çizim Tahtası", "Tablet Drawing Board"), variable=self.wacom_var,
                        command=self._on_wacom_check).pack(side="right", padx=4)

        hint = ttk.Label(self, text="Tip: type a page number and press Go. Use Text mode to write on the page; use Select/Move to drag text; Text +/- changes selected text size.", style="Muted.TLabel")
        hint.pack(fill="x", padx=8, pady=(0, 3))

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True)

        holder = ttk.Frame(body)
        body.add(holder, weight=3)
        self.canvas = tk.Canvas(holder, bg=THEME["canvas"], highlightthickness=0)
        self.vbar = ttk.Scrollbar(holder, orient="vertical", command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(holder, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.vbar.pack(side="right", fill="y")
        self.hbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)

        # --- Smart Wacom Student Board: toggle-able + pop-out-able pane ---
        self._wacom_body = body
        self._wacom_weight = 2
        self._wacom_float = None
        self._wacom_float_board = None
        self._wacom_visible = True
        self.wacom_holder = ttk.Frame(body)
        whead = ttk.Frame(self.wacom_holder)
        whead.pack(fill="x")
        ttk.Label(whead, text="Akıllı Tablet Çizim Tahtası", style="Header.TLabel").pack(side="left", padx=4, pady=2)
        RoundedButton(whead, text="Ayrı Pencerede Aç", command=self.popout_wacom).pack(side="right", padx=2, pady=2)
        RoundedButton(whead, text="Gizle", command=lambda: self.set_wacom_visible(False)).pack(side="right", padx=2, pady=2)
        self.math_board = MathWhiteboard(self.wacom_holder, self.app)
        self.math_board.pack(fill="both", expand=True)
        body.add(self.wacom_holder, weight=self._wacom_weight)

        # Restore the saved Wacom visibility preference (persists across runs).
        try:
            from ui_preferences import UIPreferences
            self._wacom_prefs = UIPreferences()
            if not self._wacom_prefs.get("wacom_visible", True):
                self.after(80, lambda: self.set_wacom_visible(False, save=False))
        except Exception:
            self._wacom_prefs = None

    # ------------------------------------------------------------------ #
    # Smart Wacom Student Board: show / hide / pop-out / persistence
    # ------------------------------------------------------------------ #
    def _on_wacom_check(self):
        self.set_wacom_visible(bool(self.wacom_var.get()))

    def set_wacom_visible(self, visible, save=True):
        body = getattr(self, "_wacom_body", None)
        holder = getattr(self, "wacom_holder", None)
        if body is None or holder is None:
            return
        try:
            panes = [str(p) for p in body.panes()]
            if visible:
                if self._wacom_float is not None:
                    self.dock_wacom_back(save=False)
                if str(holder) not in panes:
                    body.add(holder, weight=getattr(self, "_wacom_weight", 2))
                self._wacom_visible = True
            else:
                if str(holder) in panes:
                    body.forget(holder)
                self._wacom_visible = False
        except Exception:
            return
        if hasattr(self, "wacom_var"):
            try:
                self.wacom_var.set(self._wacom_visible)
            except Exception:
                pass
        if save:
            self._save_wacom_pref()

    def toggle_wacom(self):
        self.set_wacom_visible(not getattr(self, "_wacom_visible", True))

    def popout_wacom(self):
        # Duplicate prevention: focus the existing floating Wacom window.
        if self._wacom_float is not None:
            try:
                if self._wacom_float.winfo_exists():
                    self._wacom_float.deiconify()
                    self._wacom_float.lift()
                    self._wacom_float.focus_force()
                    return
            except Exception:
                pass
        self.set_wacom_visible(False, save=False)
        try:
            top = tk.Toplevel(self)
            top.title("Akıllı Tablet Çizim Tahtası")
            top.minsize(700, 500)
            try:
                geo = self._wacom_prefs.get("wacom_window_geometry", "") if getattr(self, "_wacom_prefs", None) else ""
                if geo:
                    top.geometry(geo)
            except Exception:
                pass
            top.protocol("WM_DELETE_WINDOW", self.dock_wacom_back)
            bar = ttk.Frame(top)
            bar.pack(fill="x")
            ttk.Label(bar, text="Akıllı Tablet Çizim Tahtası", style="Header.TLabel").pack(side="left", padx=6, pady=3)
            RoundedButton(bar, text=self._t("Geri Yerleştir", "Dock back"), command=self.dock_wacom_back).pack(side="right", padx=4, pady=2)
            board = MathWhiteboard(top, self.app)
            board.pack(fill="both", expand=True)
            self._wacom_float = top
            self._wacom_float_board = board
            if getattr(self, "_wacom_prefs", None):
                self._wacom_prefs.save({"wacom_floating": True})
        except Exception as exc:
            messagebox.showerror("Tablet Çizim Tahtası", f"Pop out failed:\n{exc}")
            self.set_wacom_visible(True, save=False)

    def dock_wacom_back(self, save=True):
        win = self._wacom_float
        self._wacom_float = None
        self._wacom_float_board = None
        if win is not None:
            try:
                if win.winfo_exists():
                    if getattr(self, "_wacom_prefs", None):
                        try:
                            self._wacom_prefs.save({"wacom_window_geometry": win.winfo_geometry(),
                                                    "wacom_floating": False})
                        except Exception:
                            pass
                    win.destroy()
            except Exception:
                pass
        self.set_wacom_visible(True, save=save)

    def _save_wacom_pref(self):
        prefs = getattr(self, "_wacom_prefs", None)
        if prefs is not None:
            try:
                prefs.save({"wacom_visible": bool(getattr(self, "_wacom_visible", True))})
            except Exception:
                pass

    def set_mode(self, mode):
        self.mode = mode
        self.mode_label.config(text=f"Mode: {mode.title()}")

    def send_screenshot_hint_to_visual_math(self):
        messagebox.showinfo(
            "Visual Math Lab",
            "Windows ekran alintisi ile soruyu kirpin, sonra Visual Math Lab'de Paste Screenshot'a basin.\n\n"
            "Use Windows screenshot/snipping to crop the question, then switch to Visual Math Lab and press Paste Screenshot."
        )
        try:
            if getattr(self.app, "visual_math_tab", None) is not None:
                self.app.tabs.select(self.app.visual_math_tab)
        except Exception:
            pass

    def load_pdf(self, path):
        self.path = Path(path)
        self.page_index = 0
        self.selected_ann = None
        self.annotations = self.load_annotations()
        if fitz is None or Image is None or ImageTk is None:
            self.canvas.delete("all")
            self.canvas.create_text(30, 30, anchor="nw", fill="white", text="PDF rendering requires PyMuPDF and Pillow.\nRun: pip install PyMuPDF pillow")
            return
        try:
            self.doc = fitz.open(str(self.path))
            self.render()
        except Exception as exc:
            messagebox.showerror("PDF Error", str(exc))

    def render(self):
        self.canvas.delete("all")
        if not self.doc:
            return
        page = self.doc[self.page_index]
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo, tags=("page",))
        self.canvas.config(scrollregion=(0, 0, img.width, img.height))
        total = len(self.doc)
        self.page_var.set(str(self.page_index + 1))
        self.page_label.config(text=f"/ {total}")
        self.draw_annotations()

    def draw_annotations(self):
        if not self.path:
            return
        for ann in self.annotations:
            if ann.get("page") != self.page_index:
                continue
            t = ann.get("type")
            pts = ann.get("points", [])
            if t == "pen" and len(pts) > 1:
                coords = [v for p in [(x*self.zoom, y*self.zoom) for x, y in pts] for v in p]
                self.canvas.create_line(*coords, fill=ann.get("color", "#ff5555"), width=max(1, int(ann.get("width", 2)*self.zoom)), smooth=True, tags=("ann",))
            elif t == "highlight" and len(pts) == 2:
                (x1, y1), (x2, y2) = pts
                self.canvas.create_rectangle(x1*self.zoom, y1*self.zoom, x2*self.zoom, y2*self.zoom, fill=ann.get("color", "#fde047"), stipple="gray50", outline="", tags=("ann",))
            elif t == "text":
                x, y = ann.get("x", 10), ann.get("y", 10)
                size = max(6, int(ann.get("size", self.default_text_size) * self.zoom))
                text = ann.get("text", "")
                color = ann.get("color", self.default_text_color)
                self.canvas.create_text(x*self.zoom, y*self.zoom, anchor="nw", text=text, fill=color, font=("Arial", size, "bold"), tags=("ann",))
                if ann is self.selected_ann:
                    x1, y1, x2, y2 = self.text_bbox(ann)
                    self.canvas.create_rectangle(x1*self.zoom, y1*self.zoom, x2*self.zoom, y2*self.zoom, outline="#60a5fa", width=2, dash=(4, 2), tags=("ann",))

    def text_bbox(self, ann):
        size = ann.get("size", self.default_text_size)
        text = ann.get("text", "") or " "
        lines = text.splitlines() or [text]
        width = max(len(line) for line in lines) * size * 0.62 + 12
        height = max(1, len(lines)) * size * 1.35 + 8
        x, y = ann.get("x", 10), ann.get("y", 10)
        return x, y, x + width, y + height

    def hit_test_text(self, x, y):
        for ann in reversed(self.annotations):
            if ann.get("page") != self.page_index or ann.get("type") != "text":
                continue
            x1, y1, x2, y2 = self.text_bbox(ann)
            if x1 <= x <= x2 and y1 <= y <= y2:
                return ann
        return None

    def canvas_to_page(self, x, y):
        return self.canvas.canvasx(x) / self.zoom, self.canvas.canvasy(y) / self.zoom

    def on_press(self, event):
        if not self.doc:
            return
        x, y = self.canvas_to_page(event.x, event.y)
        self.start_x, self.start_y = x, y
        if self.mode == "select":
            ann = self.hit_test_text(x, y)
            self.selected_ann = ann
            if ann:
                self.dragging_ann = True
                self.drag_offset = (x - ann.get("x", 0), y - ann.get("y", 0))
            self.render()
        elif self.mode == "pen":
            self.current_draw = {"type": "pen", "page": self.page_index, "points": [(x, y)], "color": "#ff5555", "width": 2}
        elif self.mode == "highlight":
            self.current_draw = {"type": "highlight", "page": self.page_index, "points": [(x, y), (x, y)], "color": "#fde047"}
        elif self.mode == "text":
            text = simpledialog.askstring("Text Note", "Write text to place here:")
            if text:
                ann = {"type": "text", "page": self.page_index, "x": x, "y": y, "text": text, "size": self.default_text_size, "color": self.default_text_color}
                self.annotations.append(ann)
                self.selected_ann = ann
                self.mode = "select"
                self.mode_label.config(text="Mode: Select")
                self.render()
        elif self.mode == "crop":
            self.current_draw = {"type": "crop", "page": self.page_index,
                                 "points": [(x, y), (x, y)]}
        elif self.mode == "erase":
            self.erase_near(x, y)

    def on_drag(self, event):
        x, y = self.canvas_to_page(event.x, event.y)
        if self.dragging_ann and self.selected_ann:
            ox, oy = self.drag_offset
            self.selected_ann["x"] = x - ox
            self.selected_ann["y"] = y - oy
            self.render()
            return
        if not self.current_draw:
            return
        if self.current_draw["type"] == "pen":
            self.current_draw["points"].append((x, y))
        elif self.current_draw["type"] in ("highlight", "crop"):
            self.current_draw["points"][1] = (x, y)
        self.render()
        if self.current_draw["type"] == "pen":
            pts = self.current_draw["points"]
            if len(pts) > 1:
                coords = [v for p in [(a*self.zoom, b*self.zoom) for a, b in pts] for v in p]
                self.canvas.create_line(*coords, fill="#ff5555", width=2, smooth=True, tags=("preview",))
        elif self.current_draw["type"] == "highlight":
            (x1, y1), (x2, y2) = self.current_draw["points"]
            self.canvas.create_rectangle(x1*self.zoom, y1*self.zoom, x2*self.zoom, y2*self.zoom, fill="#fde047", stipple="gray50", outline="", tags=("preview",))
        elif self.current_draw["type"] == "crop":
            (x1, y1), (x2, y2) = self.current_draw["points"]
            self.canvas.create_rectangle(x1*self.zoom, y1*self.zoom, x2*self.zoom, y2*self.zoom,
                                         outline="#2563EB", width=2, dash=(5, 3), tags=("preview",))

    def on_release(self, event):
        if self.dragging_ann:
            self.dragging_ann = False
            self.render()
            return
        if self.current_draw and self.current_draw.get("type") == "crop":
            pts = self.current_draw["points"]
            self.current_draw = None
            self.render()
            self._crop_question(pts)
            return
        if self.current_draw:
            self.annotations.append(self.current_draw)
            self.current_draw = None
            self.render()

    def _crop_question(self, pts):
        """Cut the dragged region out of the page at high resolution and hand it
        to the question-bank dialog (image + source PDF + page prefilled)."""
        if not self.doc or fitz is None:
            return
        (x1, y1), (x2, y2) = pts
        rect = fitz.Rect(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        if rect.width < 15 or rect.height < 10:
            return  # accidental click, not a selection
        try:
            import student_tracker as _st
            page = self.doc[self.page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=rect, alpha=False)
            out = _st.question_images_dir() / f"soru_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
            pix.save(str(out))
        except Exception as exc:
            messagebox.showerror(self._t("Soru Kırp", "Clip question"), f"Kırpma başarısız: {exc}")
            return
        self.mode = "select"
        self.mode_label.config(text="Mode: Select")
        self.app.open_question_crop_dialog(str(out), source_pdf=str(self.path or ""),
                                           page_number=self.page_index + 1)

    def erase_near(self, x, y):
        new = []
        for ann in self.annotations:
            if ann.get("page") != self.page_index:
                new.append(ann)
                continue
            keep = True
            if ann["type"] == "text":
                x1, y1, x2, y2 = self.text_bbox(ann)
                keep = not (x1 <= x <= x2 and y1 <= y <= y2)
            else:
                pts = ann.get("points", [])
                if pts:
                    keep = min(math.hypot(px-x, py-y) for px, py in pts) > 20
            if keep:
                new.append(ann)
        self.annotations = new
        self.selected_ann = None
        self.render()

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_ctrl_mousewheel(self, event):
        self.change_zoom(1.1 if event.delta > 0 else 0.9)
        return "break"

    def prev_page(self):
        if self.doc and self.page_index > 0:
            self.page_index -= 1
            self.selected_ann = None
            self.render()

    def next_page(self):
        if self.doc and self.page_index < len(self.doc)-1:
            self.page_index += 1
            self.selected_ann = None
            self.render()

    def go_page(self):
        if not self.doc:
            return
        try:
            n = int(self.page_var.get().strip())
            n = max(1, min(len(self.doc), n))
            self.page_index = n - 1
            self.selected_ann = None
            self.render()
        except Exception:
            messagebox.showwarning("Page", "Enter a valid page number.")

    def change_zoom(self, factor):
        self.zoom = max(0.35, min(5.0, self.zoom * factor))
        self.render()

    def change_text_size(self, delta):
        if self.selected_ann and self.selected_ann.get("type") == "text":
            self.selected_ann["size"] = max(6, min(72, int(self.selected_ann.get("size", self.default_text_size)) + delta))
            self.render()
        else:
            self.default_text_size = max(6, min(72, self.default_text_size + delta))
            self.mode_label.config(text=f"Mode: {self.mode.title()} | Text size: {self.default_text_size}")

    def delete_selected(self):
        if self.selected_ann and self.selected_ann in self.annotations:
            self.annotations.remove(self.selected_ann)
            self.selected_ann = None
            self.render()

    def fit_width(self):
        if not self.doc:
            return
        page = self.doc[self.page_index]
        width = page.rect.width
        canvas_width = max(300, self.canvas.winfo_width() - 30)
        self.zoom = max(0.35, min(5.0, canvas_width / width))
        self.render()

    def open_external(self):
        if self.path:
            os.startfile(str(self.path)) if os.name == "nt" else webbrowser.open(str(self.path))

    def ann_path(self):
        if not self.path:
            return None
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", str(self.path).replace(":", ""))
        return ANNOTATION_DIR / (safe + ".annotations.json")

    def load_annotations(self):
        p = self.ann_path()
        if p and p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def save_annotations(self):
        p = self.ann_path()
        if p:
            p.write_text(json.dumps(self.annotations, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("Saved", f"Annotations saved:\n{p}")

    def export_annotated_pdf(self):
        if not self.path or fitz is None:
            messagebox.showwarning("Export", "PyMuPDF is required for PDF export.")
            return
        out = filedialog.asksaveasfilename(title="Export Annotated PDF", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not out:
            return
        try:
            doc = fitz.open(str(self.path))
            for ann in self.annotations:
                page = doc[ann.get("page", 0)]
                if ann["type"] == "text":
                    fontsize = int(ann.get("size", self.default_text_size))
                    page.insert_text(fitz.Point(ann.get("x", 10), ann.get("y", 10)), ann.get("text", ""), fontsize=fontsize, color=(0.1, 0.35, 0.85))
                elif ann["type"] == "highlight" and len(ann.get("points", [])) == 2:
                    (x1, y1), (x2, y2) = ann["points"]
                    rect = fitz.Rect(min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
                    annot = page.add_rect_annot(rect)
                    annot.set_colors(stroke=(1, 0.85, 0), fill=(1, 0.85, 0))
                    annot.set_opacity(0.25)
                    annot.update()
                elif ann["type"] == "pen" and len(ann.get("points", [])) > 1:
                    shape = page.new_shape()
                    pts = ann["points"]
                    shape.draw_polyline([fitz.Point(x, y) for x, y in pts])
                    shape.finish(color=(1, 0, 0), width=1.3)
                    shape.commit()
            doc.save(out)
            doc.close()
            messagebox.showinfo("Exported", out)
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))


