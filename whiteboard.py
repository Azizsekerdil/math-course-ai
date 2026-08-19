# -*- coding: utf-8 -*-
"""Math Course AI — akilli tablet cizim tahtasi (MathWhiteboard).

Ana dosyadan (Math_Course_AI.pyw) V48'de mekanik olarak cikarildi.
Fare/kalemli ekran/cizim tabletiyle cizim, izgara/eksen, PNG disari
aktarma ve "ne cizdim?" AI koprusu (app uzerinden). PDFViewer'in
karalama katmani da bu sinifi kullanir.
"""

import os
import io
import json
import math
import time
from collections import Counter
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
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

from mca_common import APP_FOLDER, THEME, RoundedButton

class MathWhiteboard(ttk.Frame):
    """Smart Wacom-friendly student board for handwriting, shapes, vectors and AI explanation.

    This board is designed for learners, not only teachers. Standard Tkinter receives most
    Wacom pen input as normal mouse/stylus drag events, so it works for handwriting and
    shape sketching. Advanced pressure data needs dedicated Wintab/Windows Ink support,
    so this version focuses on reliable pen drawing, geometry tools, export, and AI feedback.
    """


    def _t(self, tr, en):
        """Panel metni: dil, panel kurulurken sahibinden okunur."""
        return t2(tr, en, getattr(self, "lang", "tr"))

    def __init__(self, master, app, title=None):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        self.lang = app_lang(app)
        # Baslik varsayilani DIL BILINDIKTEN SONRA cozulur: imza icinde
        # self._t(...) cagrilamaz (sinif govdesinde self yok).
        self.title = title or self._t("Akıllı Tablet Çizim Tahtası",
                                      "Smart Tablet Drawing Board")
        self.tool = "pen"
        # THEME'den okunur ki karanlik temada tahta da kararsin (eskiden acik
        # temanin literal kopyalariydi); kalem rengi murekkep = THEME["text"].
        self.color = THEME["text"] if THEME["text"] != "#2B2620" else "#1f2937"
        self.width = tk.IntVar(value=4)
        self.show_grid = tk.BooleanVar(value=True)
        self.show_axes = tk.BooleanVar(value=False)
        self.bg_color = THEME["panel"]
        self.grid_color = THEME["line"]
        self.axis_color = THEME["muted"]
        self.items = []
        self.current_item = None
        self.start_xy = None
        self.last_xy = None
        self.preview_id = None
        self._build()

    def _build(self):
        header = ttk.Frame(self, style="Panel.TFrame")
        header.pack(fill="x", padx=6, pady=(4, 2))
        ttk.Label(header, text=self.title, style="Header.TLabel").pack(side="left")
        RoundedButton(header, text="PNG Kaydet", command=self.save_png).pack(side="right", padx=2)
        RoundedButton(header, text=self._t("AI Açıkla", "Explain with AI"), command=self.ai_explain_board).pack(side="right", padx=2)
        RoundedButton(header, text="AI Tutor'a Gönder", command=self.send_board_to_ai_tutor).pack(side="right", padx=2)

        tools = ttk.Frame(self, style="Panel.TFrame")
        tools.pack(fill="x", padx=6, pady=2)
        for label, tool in [
            ("Kalem", "pen"), ("Silgi", "eraser"), ("Çizgi", "line"), ("Ok/Vektör", "arrow"),
            ("Dikdörtgen", "rect"), ("Çember", "oval"), ("Üçgen", "triangle"), ("Metin", "text"),
        ]:
            RoundedButton(tools, text=label, command=lambda t=tool: self.set_tool(t)).pack(side="left", padx=2, pady=1)
        RoundedButton(tools, text="Geri Al", command=self.undo).pack(side="left", padx=2)
        RoundedButton(tools, text="Temizle", command=self.clear).pack(side="left", padx=2)

        settings = ttk.Frame(self, style="Panel.TFrame")
        settings.pack(fill="x", padx=6, pady=2)
        ttk.Label(settings, text=self._t("Kalınlık:", "Width:"), style="Muted.TLabel").pack(side="left", padx=(0, 3))
        ttk.Combobox(settings, textvariable=self.width, width=4, values=[2, 4, 6, 8, 12, 16, 22], state="readonly").pack(side="left", padx=(0, 6))
        ttk.Checkbutton(settings, text="Grid", variable=self.show_grid, command=self.redraw).pack(side="left", padx=4)
        ttk.Checkbutton(settings, text="Koordinat", variable=self.show_axes, command=self.redraw).pack(side="left", padx=4)
        RoundedButton(settings, text=self._t("Ne çizdim?", "What did I draw?"), command=self.local_explain_board).pack(side="left", padx=8)
        RoundedButton(settings, text=self._t("Adım adım açıkla", "Explain step by step"), command=self.ai_explain_board).pack(side="left", padx=2)

        colors = ttk.Frame(self, style="Panel.TFrame")
        colors.pack(fill="x", padx=6, pady=(2, 4))
        for label, col in [
            ("Beyaz", "#e5e7eb"), ("Kırmızı", "#ef4444"), ("Mavi", "#38bdf8"),
            ("Yeşil", "#22c55e"), ("Sarı", "#facc15"), ("Mor", "#a78bfa"),
            # Koyu temada "Siyah" kalem koyu tahtada gorunmez; murekkep rengi
            # THEME'den gelir (acikta koyu, koyuda fildisi).
            ("Mürekkep", THEME["text"]),
        ]:
            tk.Button(colors, text=" ", width=2, bg=col, activebackground=col, relief="raised", command=lambda c=col: self.set_color(c)).pack(side="left", padx=2)
        self.tool_label = ttk.Label(colors, text="Araç: Kalem | Öğrenci modu", style="Muted.TLabel")
        self.tool_label.pack(side="left", padx=8)

        body = ttk.PanedWindow(self, orient="vertical")
        body.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        canvas_frame = ttk.Frame(body, style="Panel.TFrame")
        self.canvas = tk.Canvas(canvas_frame, bg=self.bg_color, highlightthickness=1, highlightbackground=THEME["line"], cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        body.add(canvas_frame, weight=5)

        out_frame = ttk.Frame(body, style="Panel.TFrame")
        ttk.Label(out_frame, text="Tahta Açıklaması / Öğrenme Notu", style="Muted.TLabel").pack(anchor="w", padx=4, pady=(2,0))
        self.board_output = tk.Text(out_frame, height=6, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 9))
        self.board_output.pack(fill="both", expand=True, padx=4, pady=4)
        self.board_output.insert("1.0", "Mouse, kalemli ekran veya çizim tableti ile çiz. Sonra 'Ne çizdim?' veya 'AI Açıkla' butonuna bas.\n")
        body.add(out_frame, weight=1)

        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", lambda e: self.set_tool("eraser"))
        self.canvas.bind("<Double-Button-1>", lambda e: self.set_tool("pen"))
        self.redraw()

    def set_tool(self, tool):
        self.tool = tool
        names = {
            "pen": "Kalem", "eraser": "Silgi", "line": "Çizgi", "arrow": "Ok/Vektör",
            "rect": "Dikdörtgen", "oval": "Çember", "triangle": "Üçgen", "text": "Metin",
        }
        self.tool_label.config(text=f"Araç: {names.get(tool, tool)} | Öğrenci modu")
        self.canvas.config(cursor="xterm" if tool == "text" else ("dotbox" if tool == "eraser" else "crosshair"))

    def set_color(self, color):
        self.color = color
        self.set_tool("pen")

    def draw_grid(self):
        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        if self.show_grid.get():
            step = 28
            for x in range(0, w, step):
                self.canvas.create_line(x, 0, x, h, fill=self.grid_color, width=1, tags=("grid",))
            for y in range(0, h, step):
                self.canvas.create_line(0, y, w, y, fill=self.grid_color, width=1, tags=("grid",))
        if self.show_axes.get():
            cx, cy = w // 2, h // 2
            self.canvas.create_line(0, cy, w, cy, fill=self.axis_color, width=2, arrow="last", tags=("grid",))
            self.canvas.create_line(cx, h, cx, 0, fill=self.axis_color, width=2, arrow="last", tags=("grid",))
            self.canvas.create_text(w - 16, cy - 12, text="x", fill=self.axis_color, tags=("grid",))
            self.canvas.create_text(cx + 12, 14, text="y", fill=self.axis_color, tags=("grid",))

    def redraw(self):
        self.canvas.delete("all")
        self.draw_grid()
        for item in self.items:
            self.draw_item(item)
        if self.current_item:
            self.draw_item(self.current_item)

    def draw_item(self, item):
        t = item.get("type")
        color = item.get("color", self.color)
        width = int(item.get("width", self.width.get()))
        if t == "stroke":
            pts = item.get("points", [])
            if len(pts) >= 2:
                self.canvas.create_line(*[v for xy in pts for v in xy], fill=color, width=width, smooth=True, capstyle="round", joinstyle="round", tags=("draw",))
        elif t in ("line", "arrow", "vector"):
            x1, y1, x2, y2 = item.get("coords", (0,0,0,0))
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, arrow=("last" if t in ("arrow", "vector") else "none"), capstyle="round", tags=("draw",))
        elif t == "rect":
            self.canvas.create_rectangle(*item.get("coords", (0,0,0,0)), outline=color, width=width, tags=("draw",))
        elif t == "oval":
            self.canvas.create_oval(*item.get("coords", (0,0,0,0)), outline=color, width=width, tags=("draw",))
        elif t == "triangle":
            x1, y1, x2, y2 = item.get("coords", (0,0,0,0))
            pts = (x1 + (x2-x1)/2, y1, x1, y2, x2, y2)
            self.canvas.create_polygon(*pts, outline=color, fill="", width=width, tags=("draw",))
        elif t == "text":
            x, y = item.get("xy", (0,0))
            self.canvas.create_text(x, y, text=item.get("text", ""), fill=color, anchor="nw", font=("Segoe UI", max(12, width*3)), tags=("draw",))

    def on_press(self, event):
        self.start_xy = (event.x, event.y)
        self.last_xy = (event.x, event.y)
        if self.tool == "text":
            txt = simpledialog.askstring("Tahtaya Metin Ekle", "Yazılacak metni/formülü gir:")
            if txt:
                self.items.append({"type": "text", "xy": (event.x, event.y), "text": txt, "color": self.color, "width": int(self.width.get())})
                self.redraw()
            return
        if self.tool in ("pen", "eraser"):
            color = self.bg_color if self.tool == "eraser" else self.color
            width = max(12, int(self.width.get()) * 3) if self.tool == "eraser" else int(self.width.get())
            self.current_item = {"type": "stroke", "tool": self.tool, "color": color, "width": width, "points": [(event.x, event.y)]}
        else:
            shape_type = "vector" if self.tool == "arrow" else self.tool
            self.current_item = {"type": shape_type, "color": self.color, "width": int(self.width.get()), "coords": (event.x, event.y, event.x, event.y)}

    def on_drag(self, event):
        if not self.current_item:
            return
        if self.current_item.get("type") == "stroke":
            self.current_item["points"].append((event.x, event.y))
            if self.last_xy:
                x1, y1 = self.last_xy
                self.canvas.create_line(x1, y1, event.x, event.y, fill=self.current_item["color"], width=self.current_item["width"], smooth=True, capstyle="round", joinstyle="round", tags=("draw",))
            self.last_xy = (event.x, event.y)
        else:
            x1, y1 = self.start_xy or (event.x, event.y)
            self.current_item["coords"] = (x1, y1, event.x, event.y)
            self.redraw()

    def on_release(self, event):
        if not self.current_item:
            return
        if self.current_item.get("type") == "stroke":
            if len(self.current_item.get("points", [])) > 1:
                self.items.append(self.current_item)
        else:
            x1, y1 = self.start_xy or (event.x, event.y)
            if abs(event.x-x1) > 4 or abs(event.y-y1) > 4:
                self.current_item["coords"] = (x1, y1, event.x, event.y)
                self.items.append(self.current_item)
        self.current_item = None
        self.last_xy = None
        self.start_xy = None
        self.redraw()

    def undo(self):
        if self.items:
            self.items.pop()
            self.redraw()

    def clear(self):
        if self.items and not messagebox.askyesno(
                self._t("Tahtayı Temizle", "Clear board"),
                self._t("Tahtadaki çizimleri silmek istiyor musun?",
                        "Delete everything drawn on the board?")):
            return
        self.items.clear()
        self.current_item = None
        self.redraw()
        self.board_output.delete("1.0", "end")
        self.board_output.insert("1.0", "Tahta temizlendi. Yeni çizim yapabilirsin.\n")

    def local_explain_board(self):
        counts = Counter(item.get("type", "unknown") for item in self.items)
        total = sum(counts.values())
        lines = []
        lines.append("SMART WACOM STUDENT BOARD - Yerel yorum\n")
        if total == 0:
            lines.append("Henüz çizim yok. Mouse, kalemli ekran veya çizim tableti ile bir işlem, şekil, grafik veya vektör çiz.\n")
        else:
            lines.append(f"Tahtada yaklaşık {total} çizim nesnesi var. Dağılım: {dict(counts)}\n\n")
            if counts.get("stroke"):
                lines.append("• Serbest kalem çizimleri: el yazısı işlem, not, grafik veya şekil taslağı olabilir.\n")
            if counts.get("vector") or counts.get("arrow"):
                lines.append("• Ok/Vektör: Matematikte yön + büyüklük taşıyan vektör olarak yorumlanabilir. Fizikte kuvvet, hız veya ivme oku olabilir.\n")
            if counts.get("oval"):
                lines.append("• Çember/oval: Geometride çember, fizikte yörünge veya dalga cephesi olabilir. Formül örneği: x² + y² = r².\n")
            if counts.get("rect"):
                lines.append("• Dikdörtgen: Alan, çevre, koordinat bölgesi veya matris hücresi olarak incelenebilir.\n")
            if counts.get("triangle"):
                lines.append("• Üçgen: Açı, alan, trigonometri ve vektör bileşenleri için kullanılabilir.\n")
            if self.show_axes.get():
                lines.append("• Koordinat modu açık: çizimleri R² düzleminde konum, fonksiyon veya vektör olarak düşünebilirsin.\n")
        lines.append("\nÖğrenci modu önerisi:\n1. Önce çizimi yap.\n2. 'AI Açıkla' ile çizimi görsel olarak yorumlat.\n3. AI Tutor ekranında 'adım adım' çözüm iste.\n")
        self.board_output.delete("1.0", "end")
        self.board_output.insert("1.0", "".join(lines))

    def _render_to_image(self):
        if Image is None:
            raise RuntimeError("Pillow is required for PNG export. Run: pip install pillow")
        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        img = Image.new("RGB", (w, h), self.bg_color)
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        if self.show_grid.get():
            step = 28
            for x in range(0, w, step):
                draw.line((x, 0, x, h), fill=self.grid_color, width=1)
            for y in range(0, h, step):
                draw.line((0, y, w, y), fill=self.grid_color, width=1)
        if self.show_axes.get():
            cx, cy = w // 2, h // 2
            draw.line((0, cy, w, cy), fill=self.axis_color, width=2)
            draw.line((cx, h, cx, 0), fill=self.axis_color, width=2)
        for item in self.items:
            t = item.get("type")
            color = item.get("color", self.color)
            width = int(item.get("width", self.width.get()))
            if t == "stroke":
                pts = item.get("points", [])
                if len(pts) > 1:
                    draw.line(pts, fill=color, width=width, joint="curve")
            elif t in ("line", "arrow", "vector"):
                draw.line(item.get("coords", (0,0,0,0)), fill=color, width=width)
            elif t == "rect":
                draw.rectangle(item.get("coords", (0,0,0,0)), outline=color, width=width)
            elif t == "oval":
                draw.ellipse(item.get("coords", (0,0,0,0)), outline=color, width=width)
            elif t == "triangle":
                x1, y1, x2, y2 = item.get("coords", (0,0,0,0))
                pts = [(x1 + (x2-x1)/2, y1), (x1, y2), (x2, y2)]
                draw.polygon(pts, outline=color)
                draw.line(pts + [pts[0]], fill=color, width=width)
            elif t == "text":
                draw.text(item.get("xy", (0,0)), item.get("text", ""), fill=color)
        return img

    def save_board_image(self, path):
        img = self._render_to_image()
        img.save(path)
        return path

    def save_png(self):
        out = filedialog.asksaveasfilename(title="Tablet Çizim Tahtasını PNG Kaydet", defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not out:
            return
        try:
            self.save_board_image(out)
            messagebox.showinfo("Kaydedildi", f"Tahta PNG olarak kaydedildi:\n{out}")
        except Exception as exc:
            messagebox.showerror(self._t("PNG Kaydetme Hatası", "PNG save error"), str(exc))

    def _temp_board_png(self):
        temp_dir = APP_FOLDER / "board_exports"
        temp_dir.mkdir(parents=True, exist_ok=True)
        out = temp_dir / f"wacom_board_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.save_board_image(out)
        return str(out)

    def send_board_to_ai_tutor(self):
        try:
            img_path = self._temp_board_png()
            self.app.attached_image_path = img_path
            self.app.image_label.config(text=f"Attached board: {Path(img_path).name}")
            if Image and ImageTk:
                img = Image.open(img_path)
                img.thumbnail((220, 160))
                self.app.attached_image_photo = ImageTk.PhotoImage(img)
                self.app.image_preview.config(image=self.app.attached_image_photo)
            self.app.question_text.delete("1.0", "end")
            self.app.question_text.insert("1.0", "Bu tablet çizim tahtasında çizdiğim işlem/şekil/grafiği oku. Matematik öğrencisine anlatır gibi adım adım açıkla ve gerekiyorsa çöz.")
            self.app.tabs.select(self.app.ai_tab)
            self.app.set_status("Tablet çizim tahtası AI Tutor'a eklendi.")
        except Exception as exc:
            messagebox.showerror("Tahtayı AI Tutor'a Gönderme Hatası", str(exc))

    def ai_explain_board(self):
        if not self.items:
            messagebox.showinfo(self._t("Çizim yok", "Nothing drawn"), "Önce mouse, kalemli ekran veya çizim tableti ile tahtaya bir işlem, şekil, grafik veya vektör çiz.")
            return
        try:
            img_path = self._temp_board_png()
            self.app.tabs.select(self.app.ai_tab)
            self.app.attached_image_path = img_path
            self.app.question_text.delete("1.0", "end")
            self.app.question_text.insert("1.0", "Tahtadaki çizimi oku. Ben matematik hocası değilim; öğrenci seviyesinde açıkla. Çizimi matematiksel dile çevir: vektör, fonksiyon, geometri, fizik, 3D uzay veya işlem olarak yorumla. Sonra adım adım anlat ve benzer bir pratik öner.")
            system = (
                "You are a patient math/physics tutor inside a Wacom-enabled learning board. "
                "The user is a learner, not a teacher. Read the board image, identify handwritten math, geometry, vectors, graphs or physics diagrams, "
                "then explain in simple Turkish. Do not only describe the image; translate it into mathematics and teach step by step."
            )
            prompt = (
                "Wacom board screenshot is attached. Analyze it as a learning board.\n\n"
                "Use this structure in Turkish:\n"
                "1. Tahtada ne görüyorum?\n"
                "2. Matematiksel karşılığı nedir?\n"
                "3. Formül / uzay / temsil\n"
                "4. Adım adım açıklama\n"
                "5. Öğrenci için pratik öneri"
            )
            self.app.run_ai(system, prompt, kind="answer", image_path=img_path, profile="vision")
        except Exception as exc:
            messagebox.showerror(self._t("AI Açıklama Hatası", "AI explanation error"), str(exc))


