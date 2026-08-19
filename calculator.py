# -*- coding: utf-8 -*-
"""Math Course AI — bilimsel hesap makinesi.

Ana dosyadan (Math_Course_AI.pyw) V48'de mekanik olarak cikarildi.
Guvenli ifade degerlendirici (ast tabanli), RAD/DEG, kesir-duyarli
sonuclar, gecmis ve cok turlu AI sohbet kutusu (app.client uzerinden).
"""

import re
import ast
import math
import json
import time
import threading
from fractions import Fraction
import tkinter as tk
from tkinter import ttk, messagebox

from mca_common import THEME, RoundedButton, safe_output_tokens


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

class ScientificCalculator(ttk.Frame):
    """Student-friendly calculator for quick arithmetic, fractions and scientific functions."""

    SAFE_NAMES = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "log": math.log,
        "log10": math.log10,
        "ln": math.log,
        "abs": abs,
        "round": round,
        "pi": math.pi,
        "e": math.e,
        "pow": pow,
    }

    # Python 3.14+ compatibility: ast.Num was removed/aliased differently in some builds.
    # ast.Constant safely covers numeric literals in modern Python.
    ALLOWED_NODES = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
        ast.USub, ast.UAdd, ast.Load, ast.Call, ast.Name, ast.Tuple
    )


    def _t(self, tr, en):
        """Panel metni: dil, panel kurulurken sahibinden okunur."""
        return t2(tr, en, getattr(self, "lang", "tr"))

    def __init__(self, master, app):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        self.lang = app_lang(getattr(self, "app", None))
        self.expr_var = tk.StringVar()
        self.result_var = tk.StringVar(value="0")
        self.angle_mode = tk.StringVar(value="RAD")
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Calculator / Hesap Makinesi", style="Header.TLabel").pack(side="left")
        RoundedButton(top, text="Copy Result", command=self.copy_result).pack(side="right", padx=4)
        RoundedButton(top, text="Clear History", command=lambda: self.history.delete("1.0", "end")).pack(side="right", padx=4)

        body = ttk.Frame(self, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=6)
        left = ttk.Frame(body, style="Panel.TFrame")
        left.pack(side="left", fill="both", expand=False, padx=(0,10))
        right = ttk.Frame(body, style="Panel.TFrame")
        right.pack(side="left", fill="both", expand=True)

        display = ttk.Frame(left, style="Panel.TFrame")
        display.pack(fill="x")
        self.entry = tk.Entry(display, textvariable=self.expr_var, bg=THEME["panel2"], fg=THEME["text"], insertbackground=THEME["text"], font=("Segoe UI", 18), justify="right", relief="flat")
        self.entry.pack(fill="x", ipady=10, pady=(0, 4))
        self.entry.bind("<Return>", lambda e: self.evaluate())
        tk.Label(display, textvariable=self.result_var, bg=THEME["panel2"], fg=THEME["text"], font=("Segoe UI", 28, "bold"), anchor="e").pack(fill="x", ipady=10)

        mode_row = ttk.Frame(left, style="Panel.TFrame")
        mode_row.pack(fill="x", pady=(8,4))
        ttk.Radiobutton(mode_row, text="RAD", variable=self.angle_mode, value="RAD").pack(side="left")
        ttk.Radiobutton(mode_row, text="DEG", variable=self.angle_mode, value="DEG").pack(side="left", padx=8)
        RoundedButton(mode_row, text="Explain", command=self.explain_current).pack(side="right")

        buttons = [
            ["%", "CE", "C", "⌫"],
            ["1/x", "x²", "√x", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["±", "0", ".", "="],
            ["(", ")", "π", "^"],
            ["sin", "cos", "tan", "ln"],
        ]
        grid = ttk.Frame(left, style="Panel.TFrame")
        grid.pack(fill="both", expand=True)
        for r, row in enumerate(buttons):
            grid.rowconfigure(r, weight=1)
            for c, label in enumerate(row):
                grid.columnconfigure(c, weight=1)
                RoundedButton(grid, text=label, style="Calc.TButton", command=lambda x=label: self.press(x)).grid(row=r, column=c, sticky="nsew", padx=2, pady=2)

        # Right side splits vertically: history/notes on top, Ask-AI chat below.
        rsplit = ttk.Panedwindow(right, orient="vertical")
        rsplit.pack(fill="both", expand=True)
        hist_frame = ttk.Frame(rsplit, style="Panel.TFrame")
        rsplit.add(hist_frame, weight=3)
        ttk.Label(hist_frame, text="History / Eğitim Notu", style="Header.TLabel").pack(fill="x")
        self.history = tk.Text(hist_frame, bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], wrap="word", relief="flat", font=("Consolas", 10))
        self.history.pack(fill="both", expand=True, pady=(4,0))
        self.history.insert("end", "Kullanım:\n• 6*8 yaz ve Enter'a bas.\n• Kesir için 3/4 + 2/5 yazabilirsin.\n• Fonksiyonlar: sqrt(25), sin(pi/2), log(100, 10 yerine log10(100)).\n• DEG modunda sin(30) derece gibi hesaplanır.\n\n")
        ai_frame = ttk.Frame(rsplit, style="Panel.TFrame")
        rsplit.add(ai_frame, weight=2)
        self._build_calc_ai_box(ai_frame)

    def press(self, label):
        if label == "C":
            self.expr_var.set(""); self.result_var.set("0"); return
        if label == "CE":
            self.expr_var.set(""); return
        if label == "⌫":
            self.expr_var.set(self.expr_var.get()[:-1]); return
        if label == "=":
            self.evaluate(); return
        if label == "±":
            text = self.expr_var.get().strip()
            self.expr_var.set(text[1:] if text.startswith("-") else "-" + text)
            return
        mapping = {
            "÷": "/", "×": "*", "−": "-", "^": "**", "π": "pi",
            "√x": "sqrt(", "x²": "**2", "1/x": "1/(",
            "sin": "sin(", "cos": "cos(", "tan": "tan(", "ln": "ln(", "%": "/100",
        }
        self.expr_var.set(self.expr_var.get() + mapping.get(label, label))
        self.entry.focus_set()
        self.entry.icursor("end")

    def _safe_eval(self, expr):
        expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/").replace("−", "-")
        tree = ast.parse(expr, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, self.ALLOWED_NODES):
                raise ValueError(f"Unsupported expression part: {type(node).__name__}")
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in self.SAFE_NAMES:
                    raise ValueError("Only supported math functions are allowed.")
            if isinstance(node, ast.Name) and node.id not in self.SAFE_NAMES:
                raise ValueError(f"Unknown name: {node.id}")
        names = dict(self.SAFE_NAMES)
        if self.angle_mode.get() == "DEG":
            names["sin"] = lambda x: math.sin(math.radians(x))
            names["cos"] = lambda x: math.cos(math.radians(x))
            names["tan"] = lambda x: math.tan(math.radians(x))
        # nosec B307 - every AST node was validated above against
        # ALLOWED_NODES/SAFE_NAMES; this is not an unchecked eval().
        return eval(compile(tree, "<calculator>", "eval"), {"__builtins__": {}}, names)  # nosec B307 - AST-validated above  # noqa: S307

    def evaluate(self):
        expr = self.expr_var.get().strip()
        if not expr:
            return
        try:
            value = self._safe_eval(expr)
            if isinstance(value, float) and abs(value - round(value)) < 1e-12:
                value = int(round(value))
            text = str(value)
            # Add a fraction view for simple rational decimal results when useful.
            frac_note = ""
            try:
                frac = Fraction(value).limit_denominator(100000)
                if str(frac) != text and abs(float(frac) - float(value)) < 1e-10:
                    frac_note = f"  ≈ {frac}"
            except Exception:
                pass
            self.result_var.set(text)
            self.history.insert("end", f"{expr} = {text}{frac_note}\n")
            self.history.see("end")
        except Exception as exc:
            self.result_var.set("Error")
            self.history.insert("end", f"Hata: {expr} → {exc}\n")
            self.history.see("end")

    def copy_result(self):
        self.clipboard_clear()
        self.clipboard_append(self.result_var.get())
        self.app.set_status("Calculator result copied.")

    def explain_current(self):
        expr = self.expr_var.get().strip()
        result = self.result_var.get()
        if not expr:
            return
        explanation = (
            f"İşlem: {expr}\n"
            f"Sonuç: {result}\n\n"
            "Eğitim notu: Bu hesap makinesi işlemi önce matematiksel ifadeye çevirir, "
            "sonra işlem önceliğine göre değerlendirir. Parantezler en önce, sonra üs/kök, "
            "sonra çarpma-bölme, en son toplama-çıkarma gelir.\n"
        )
        self.history.insert("end", "\n" + explanation + "\n")
        self.history.see("end")

    # ---- Calculator: "Ask AI" chat box (LM Studio, math profile) ---- #
    CALC_AI_PLACEHOLDER = ("Örn: 'bu sonucu açıkla'  •  \"200'e %15 KDV ekle\"  •  "
                           "'x²-5x+6=0 çöz'  •  'radyanı dereceye çevir'")

    def _build_calc_ai_box(self, parent):
        box = ttk.Frame(parent, style="Panel.TFrame")
        box.pack(fill="both", expand=True, pady=(6, 0))
        head = ttk.Frame(box, style="Panel.TFrame")
        head.pack(fill="x")
        tk.Label(head, text="Hesap makinesiyle yapay zekâya sor / Ask AI", bg=THEME["panel"],
                 fg=THEME["accent"], font=("Segoe UI", 10, "bold"), anchor="w").pack(side="left", padx=2, pady=(0, 2))
        self.calc_ai_context = tk.BooleanVar(value=True)
        ttk.Checkbutton(head, text=self._t("Geçerli hesabı bağlam gönder", "Send the current calculation as context"),
                        variable=self.calc_ai_context).pack(side="right", padx=2)
        self.calc_ai_q = tk.Text(box, height=3, wrap="word", bg=THEME["surface"], fg=THEME["muted"],
                                 relief="solid", borderwidth=1, font=("Segoe UI", 10),
                                 insertbackground=THEME["text"])
        self.calc_ai_q.pack(fill="x", padx=2)
        self._calc_ai_ph = True
        self.calc_ai_q.insert("1.0", self.CALC_AI_PLACEHOLDER)
        self.calc_ai_q.bind("<FocusIn>", self._calc_ai_focus_in)
        self.calc_ai_q.bind("<FocusOut>", self._calc_ai_focus_out)
        self.calc_ai_q.bind("<Control-Return>", lambda e: (self._calc_ai_ask(), "break")[1])
        btns = ttk.Frame(box, style="Panel.TFrame")
        btns.pack(fill="x", padx=2, pady=3)
        self.calc_ai_ask_btn = RoundedButton(btns, text="AI'ye Sor", bg=THEME["accent"], fg="#FFFFFF",
                                             hover="#EC8A4B", parent_bg=THEME["panel"], command=self._calc_ai_ask)
        self.calc_ai_ask_btn.pack(side="left", padx=2)
        RoundedButton(btns, text="Sonucu Hesapla", parent_bg=THEME["panel"], command=self._calc_ai_compute).pack(side="left", padx=2)
        RoundedButton(btns, text="Temizle", parent_bg=THEME["panel"], command=self._calc_ai_clear).pack(side="left", padx=2)
        RoundedButton(btns, text=self._t("Cevabı Kopyala", "Copy answer"), parent_bg=THEME["panel"], command=self._calc_ai_copy).pack(side="left", padx=2)
        self.calc_ai_status = tk.Label(box, text="", bg=THEME["panel"], fg=THEME["muted"],
                                       font=("Segoe UI", 9), anchor="w")
        self.calc_ai_status.pack(fill="x", padx=2)
        ansrow = ttk.Frame(box, style="Panel.TFrame")
        ansrow.pack(fill="both", expand=True, padx=2, pady=(0, 2))
        self.calc_ai_answer = tk.Text(ansrow, wrap="word", bg=THEME["surface"], fg=THEME["text"], relief="flat",
                                      font=("Segoe UI", 10), height=6)
        ascroll = ttk.Scrollbar(ansrow, orient="vertical", command=self.calc_ai_answer.yview)
        self.calc_ai_answer.configure(yscrollcommand=ascroll.set)
        self.calc_ai_answer.pack(side="left", fill="both", expand=True)
        ascroll.pack(side="right", fill="y")
        self.calc_ai_answer.config(state="disabled")
        self._calc_ai_hist = []   # multi-turn memory: list of (question, answer)
        self._calc_ai_last = ""   # last AI answer (for copy + compute bridge)

    def _calc_ai_focus_in(self, _e=None):
        if getattr(self, "_calc_ai_ph", False):
            self.calc_ai_q.delete("1.0", "end")
            self.calc_ai_q.config(fg=THEME["text"])
            self._calc_ai_ph = False

    def _calc_ai_focus_out(self, _e=None):
        if not self.calc_ai_q.get("1.0", "end").strip():
            self.calc_ai_q.delete("1.0", "end")
            self.calc_ai_q.insert("1.0", self.CALC_AI_PLACEHOLDER)
            self.calc_ai_q.config(fg=THEME["muted"])
            self._calc_ai_ph = True

    def _calc_ai_reset_q(self):
        try:
            self.calc_ai_q.delete("1.0", "end")
            self.calc_ai_q.insert("1.0", self.CALC_AI_PLACEHOLDER)
            self.calc_ai_q.config(fg=THEME["muted"])
            self._calc_ai_ph = True
        except Exception:
            pass

    def _calc_ai_get_q(self):
        if getattr(self, "_calc_ai_ph", False):
            return ""
        return self.calc_ai_q.get("1.0", "end").strip()

    def _calc_ai_set_status(self, msg, color=None):
        try:
            self.calc_ai_status.config(text=msg, fg=color or THEME["muted"])
        except Exception:
            pass

    def _calc_ai_append(self, text):
        self.calc_ai_answer.config(state="normal")
        self.calc_ai_answer.insert("end", text)
        self.calc_ai_answer.see("end")
        self.calc_ai_answer.config(state="disabled")

    def _calc_ai_ask(self):
        question = self._calc_ai_get_q()
        if not question:
            self._calc_ai_set_status(self._t("Lütfen bir soru yazın.", "Please type a question."), THEME["danger"])
            return
        client = getattr(self.app, "client", None)
        if client is None or not hasattr(client, "complete"):
            self._calc_ai_set_status(self._t("LM Studio bağlantısı yok. Server/model durumunu kontrol edin.", "No LM Studio connection. Check the server/model status."), THEME["danger"])
            return
        ctx = ""
        if bool(self.calc_ai_context.get()):
            expr = self.expr_var.get().strip()
            ctx = (f"Hesap makinesi durumu:\n- Ekrandaki ifade: {expr or '(boş)'}\n"
                   f"- Son sonuç: {self.result_var.get()}\n- Açı modu: {self.angle_mode.get()}\n\n")
        convo = ""
        for q, a in self._calc_ai_hist[-4:]:
            convo += f"Kullanıcı: {q}\nAsistan: {a}\n"
        system = (
            "Sen bir bilimsel hesap makinesinin içindeki yardımcı matematik asistanısın. "
            "Kullanıcıya Türkçe, sade ve adım adım yardım et: hesapları açıkla, sözel "
            "problemleri çöz, formülleri uygula, birim/biçim dönüşümü yap. Net ve kısa ol. "
            "Kesin sayısal sonuç verirken hesabı mümkünse tek satırlık bir ifadeyle de göster "
            "(backtick içinde, örn. `(3+4)*2` veya `sqrt(2)`), ki kullanıcı yerel motorla "
            "doğrulayabilsin."
        )
        user = ctx + (("Önceki konuşma:\n" + convo + "\n") if convo else "") + f"Soru: {question}"
        try:
            self.calc_ai_ask_btn.config(state="disabled")
        except Exception:
            pass
        self._calc_ai_set_status(self._t("Yanıt hazırlanıyor…", "Preparing the answer…"), THEME["accent"])

        def work():
            try:
                return client.complete(system, user, profile="math")
            except Exception as exc:
                return (f"AI request failed: {exc}", {}, "error")

        def done(result):
            try:
                self.calc_ai_ask_btn.config(state="normal")
            except Exception:
                pass
            if isinstance(result, tuple) and len(result) == 3:
                text, _usage, finish = result
            else:
                text, finish = str(result), "error"
            if finish == "error" or (text or "").startswith("AI request failed"):
                self._calc_ai_append("Sen: " + question + "\n\n[Hata] LM Studio bağlantısı yok ya da "
                                     "model yüklü değil. Lütfen server/model durumunu kontrol edin.\n\n"
                                     + "—" * 30 + "\n\n")
                self._calc_ai_set_status(self._t("Bağlantı/model hatası.", "Connection/model error."), THEME["danger"])
                return
            self._calc_ai_last = text
            self._calc_ai_append(f"Sen: {question}\n\nAI: {text}\n\n" + "—" * 30 + "\n\n")
            self._calc_ai_hist.append((question, text))
            self._calc_ai_reset_q()
            self._calc_ai_set_status("Yanıt geldi. ('Sonucu Hesapla' ile ifadeyi yerelde doğrulayabilirsin.)",
                                     THEME["green"])

        def task():
            r = work()
            try:
                self.after(0, lambda: done(r))
            except Exception:
                pass
        threading.Thread(target=task, daemon=True).start()

    def _calc_ai_compute(self):
        """Pull a calculable expression out of the last AI answer and evaluate it
        with the LOCAL exact engine (guards against LLM arithmetic slips)."""
        answer = self._calc_ai_last or ""
        if not answer.strip():
            self._calc_ai_set_status("Önce bir soru sor; sonra AI'nın ifadesini hesaplarım.", THEME["danger"])
            return
        candidates = re.findall(r"`([^`\n]{1,200})`", answer)  # backtick spans first
        for line in answer.splitlines():
            s = line.strip().strip("`").strip()
            if s and s not in candidates:
                candidates.append(s)
        for cand in candidates:
            expr = cand.split("=")[0].strip() if "=" in cand else cand.strip()
            if not expr or not any(ch.isdigit() for ch in expr):
                continue
            try:
                self._safe_eval(expr)   # validate it parses + evaluates locally
            except Exception:
                continue
            self.expr_var.set(expr)
            self.evaluate()
            self._calc_ai_set_status(f"AI ifadesi yerelde hesaplandı: {expr}", THEME["green"])
            return
        self._calc_ai_set_status("Cevapta hesaplanabilir bir ifade bulamadım (örn. `(3+4)*2`).", THEME["danger"])

    def _calc_ai_clear(self):
        self._calc_ai_hist = []
        self._calc_ai_last = ""
        self._calc_ai_reset_q()
        try:
            self.calc_ai_answer.config(state="normal")
            self.calc_ai_answer.delete("1.0", "end")
            self.calc_ai_answer.config(state="disabled")
        except Exception:
            pass
        self._calc_ai_set_status("")

    def _calc_ai_copy(self):
        text = (self._calc_ai_last or "").strip()
        if not text:
            self._calc_ai_set_status("Kopyalanacak cevap yok.", THEME["muted"])
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._calc_ai_set_status(self._t("Cevap panoya kopyalandı.", "Answer copied to the clipboard."), THEME["green"])
        except Exception:
            self._calc_ai_set_status(self._t("Kopyalama başarısız.", "Copy failed."), THEME["danger"])


