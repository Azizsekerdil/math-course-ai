# -*- coding: utf-8 -*-
"""Simülasyon Oynatıcı — kurs ağacındaki her konunun ▶ düğmesiyle açılır.

Sol: konuya uyan gömülü örnekler (+ kaynaktan taranan örnekler).
Orta: soru, matplotlib tuvali ve oynatma denetimleri (oynat/duraklat, adım,
      başa sar, kare sürgüsü, hız, döngü, yeni sayılar, GIF/.py kaydet).
Sağ: adım adım çözüm (animasyonla eşzamanlı açılır) ve çalıştırılan Python
     kaynağı (düzenlenebilir; politika denetiminden geçerse yeniden oynatılır).
"""

from __future__ import annotations

import queue
import random
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from mca_common import THEME, RoundedButton, t2

from . import engine, scanner

SPEEDS = ["0.25x", "0.5x", "1x", "1.5x", "2x", "4x"]
BASE_INTERVAL_MS = 45


class SimulationPlayer(tk.Toplevel):
    """Tek pencere: yeni bir konu seçildiğinde load_topic ile yeniden doldurulur."""

    def __init__(self, app, lang="tr"):
        super().__init__(app)
        self.app = app
        self.lang = lang if lang in ("tr", "en") else "tr"
        self.title(self.T("▶ Simülasyon Oynatıcı", "▶ Simulation Player"))
        self.geometry("1360x820")
        self.minsize(980, 620)
        self.configure(bg=THEME["bg"])
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.topic_label = ""
        self.course_key = ""
        self.scan_path = None
        self.topic_examples = []
        self.course_examples = []
        self.scanned_examples = []
        self.list_rows = []
        self.sim = None
        self.update_fn = None
        self.n_frames = 1
        self.frame = 0
        self.playing = False
        self._after = None
        self._busy = False
        self._last_step_count = -1
        # İş parçacıkları Tk'ye DOĞRUDAN dokunmaz: sonuçlar bu kuyruktan
        # ana iş parçacığında _poll_queue ile alınır.
        self._q = queue.Queue()
        self._poll_after = None

        self._build()
        self.bind("<space>", lambda e: (self.toggle_play(), "break")[1])
        self.bind("<Right>", lambda e: self.step(1))
        self.bind("<Left>", lambda e: self.step(-1))
        self.bind("<Home>", lambda e: self.seek(0))
        self.bind("<End>", lambda e: self.seek(self.n_frames - 1))

    # ------------------------------------------------------------------ util
    def T(self, tr, en):
        return t2(tr, en, self.lang)

    def _btn(self, parent, tr, en, cmd, accent=False, bg=None):
        kw = {}
        if accent:
            kw.update(bg=THEME["accent"], fg="#FFFFFF", hover="#EC8A4B")
        return RoundedButton(parent, text=self.T(tr, en), command=cmd, parent_bg=bg or THEME["panel"],
                             radius=10, padx=10, pady=6, **kw)

    # ------------------------------------------------------------------ UI
    def _build(self):
        head = tk.Frame(self, bg=THEME["panel"])
        head.pack(fill="x")
        self.head_title = tk.Label(head, text="", bg=THEME["panel"], fg=THEME["text"],
                                   font=("Segoe UI Semibold", 13), anchor="w")
        self.head_title.pack(side="left", padx=14, pady=8)
        self.head_sub = tk.Label(head, text="", bg=THEME["panel"], fg=THEME["muted"],
                                 font=("Segoe UI", 9), anchor="w")
        self.head_sub.pack(side="left", padx=6)
        self.status = tk.Label(head, text="", bg=THEME["panel"], fg=THEME["green"],
                               font=("Segoe UI", 9, "bold"))
        self.status.pack(side="right", padx=14)

        body = tk.PanedWindow(self, orient="horizontal", sashwidth=6, bg=THEME["border"], bd=0)
        body.pack(fill="both", expand=True, padx=6, pady=6)

        # ---- left: example list
        left = tk.Frame(body, bg=THEME["panel"])
        body.add(left, width=300, minsize=220)
        tk.Label(left, text=self.T("Örnek sorular", "Example problems"), bg=THEME["panel"],
                 fg=THEME["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=10, pady=(10, 2))
        self.filter_var = tk.StringVar()
        self.filter_box = ttk.Combobox(left, textvariable=self.filter_var, state="readonly")
        self.filter_box.pack(fill="x", padx=8, pady=2)
        self.filter_box.bind("<<ComboboxSelected>>", lambda e: self._fill_list())
        self.search_var = tk.StringVar()
        ent = ttk.Entry(left, textvariable=self.search_var)
        ent.pack(fill="x", padx=8, pady=(2, 4))
        ent.bind("<KeyRelease>", lambda e: self._fill_list())
        lf = tk.Frame(left, bg=THEME["panel"])
        lf.pack(fill="both", expand=True, padx=8)
        self.listbox = tk.Listbox(lf, activestyle="none", bg=THEME["surface"], fg=THEME["text"],
                                  selectbackground=THEME["accent"], selectforeground="#FFFFFF",
                                  font=("Segoe UI", 10), relief="flat", highlightthickness=1,
                                  highlightbackground=THEME["border"], exportselection=False)
        sb = ttk.Scrollbar(lf, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_pick)
        scan_box = tk.Frame(left, bg=THEME["panel"])
        scan_box.pack(fill="x", padx=8, pady=8)
        self.scan_btn = self._btn(scan_box, "📄 Kaynaktaki örnekleri tara", "📄 Scan source examples",
                                  self.start_scan)
        self.scan_btn.pack(fill="x", pady=2)
        self.change_var = tk.BooleanVar(value=True)
        tk.Checkbutton(scan_box, text=self.T("Sayıları değiştir (önerilir)", "Change the numbers (recommended)"),
                       variable=self.change_var, bg=THEME["panel"], fg=THEME["text"],
                       selectcolor=THEME["surface"], activebackground=THEME["panel"],
                       activeforeground=THEME["text"]).pack(anchor="w")
        self.scan_info = tk.Label(scan_box, text="", bg=THEME["panel"], fg=THEME["muted"],
                                  font=("Segoe UI", 8), wraplength=270, justify="left")
        self.scan_info.pack(anchor="w")

        # ---- center: question + canvas + controls
        center = tk.Frame(body, bg=THEME["bg"])
        body.add(center, minsize=520)
        self.q_title = tk.Label(center, text="", bg=THEME["bg"], fg=THEME["accent"],
                                font=("Segoe UI Semibold", 11), anchor="w")
        self.q_title.pack(fill="x", padx=8, pady=(6, 0))
        self.q_text = tk.Label(center, text="", bg=THEME["bg"], fg=THEME["text"], justify="left",
                               font=("Segoe UI", 11), anchor="w", wraplength=640)
        self.q_text.pack(fill="x", padx=8)
        self.q_src = tk.Label(center, text="", bg=THEME["bg"], fg=THEME["muted"],
                              font=("Segoe UI", 8), anchor="w")
        self.q_src.pack(fill="x", padx=8)
        center.bind("<Configure>", lambda e: self.q_text.configure(wraplength=max(300, e.width - 30)))

        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.fig = Figure(figsize=(8, 5.4), dpi=96, facecolor="white")
        self.canvas = FigureCanvasTkAgg(self.fig, master=center)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=6)

        ctl = tk.Frame(center, bg=THEME["panel"])
        ctl.pack(fill="x", padx=8, pady=(0, 2))
        self._btn(ctl, "⏮", "⏮", lambda: self.seek(0)).pack(side="left", padx=2, pady=4)
        self._btn(ctl, "◀ Adım", "◀ Step", lambda: self.step(-1)).pack(side="left", padx=2)
        self.play_btn = self._btn(ctl, "▶ Oynat", "▶ Play", self.toggle_play, accent=True)
        self.play_btn.pack(side="left", padx=2)
        self._btn(ctl, "Adım ▶", "Step ▶", lambda: self.step(1)).pack(side="left", padx=2)
        self._btn(ctl, "⏭", "⏭", lambda: self.seek(self.n_frames - 1)).pack(side="left", padx=2)
        self.frame_var = tk.IntVar(value=0)
        self.scale = ttk.Scale(ctl, from_=0, to=100, orient="horizontal",
                               command=lambda v: self._on_scale(v))
        self.scale.pack(side="left", fill="x", expand=True, padx=8)
        self.frame_lbl = tk.Label(ctl, text="0/0", bg=THEME["panel"], fg=THEME["muted"],
                                  font=("Consolas", 9), width=9)
        self.frame_lbl.pack(side="left")
        self.speed_var = tk.StringVar(value="1x")
        ttk.Combobox(ctl, textvariable=self.speed_var, values=SPEEDS, width=5,
                     state="readonly").pack(side="left", padx=4)
        self.loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctl, text=self.T("Döngü", "Loop"), variable=self.loop_var, bg=THEME["panel"],
                       fg=THEME["text"], selectcolor=THEME["surface"], activebackground=THEME["panel"],
                       activeforeground=THEME["text"]).pack(side="left", padx=4)

        ctl2 = tk.Frame(center, bg=THEME["bg"])
        ctl2.pack(fill="x", padx=8, pady=(2, 6))
        self._btn(ctl2, "🎲 Yeni sayılar", "🎲 New numbers", self.new_numbers, bg=THEME["bg"]).pack(side="left", padx=2)
        self._btn(ctl2, "↺ Orijinal soru", "↺ Original problem", self.reset_example, bg=THEME["bg"]).pack(side="left", padx=2)
        self._btn(ctl2, "💾 GIF kaydet", "💾 Save GIF", self.save_gif, bg=THEME["bg"]).pack(side="left", padx=2)
        self._btn(ctl2, "💾 .py kaydet", "💾 Save .py", self.save_py, bg=THEME["bg"]).pack(side="left", padx=2)
        self._btn(ctl2, "🖼 PNG kaydet", "🖼 Save PNG", self.save_png, bg=THEME["bg"]).pack(side="left", padx=2)

        # ---- right: solution + code
        right = tk.Frame(body, bg=THEME["panel"])
        body.add(right, width=380, minsize=260)
        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True, padx=4, pady=4)
        solf = tk.Frame(self.nb, bg=THEME["surface"])
        self.nb.add(solf, text=self.T("Çözüm adımları", "Solution steps"))
        self.sol_text = tk.Text(solf, wrap="word", bg=THEME["surface"], fg=THEME["text"], relief="flat",
                                font=("Segoe UI", 10), padx=10, pady=8, spacing1=3, spacing3=3)
        self.sol_text.pack(fill="both", expand=True)
        self.sol_text.tag_configure("head", font=("Segoe UI Semibold", 11), foreground=THEME["accent"])
        self.sol_text.tag_configure("cur", background=THEME["accent_soft"])
        self.sol_text.tag_configure("ans", font=("Segoe UI Semibold", 11), foreground=THEME["green"])
        self.sol_text.tag_configure("muted", foreground=THEME["muted"])
        self.show_all_var = tk.BooleanVar(value=False)
        tk.Checkbutton(solf, text=self.T("Tüm adımları hemen göster", "Show all steps now"),
                       variable=self.show_all_var, command=lambda: self._render_steps(force=True),
                       bg=THEME["surface"], fg=THEME["text"], selectcolor=THEME["surface"],
                       activebackground=THEME["surface"], activeforeground=THEME["text"]).pack(anchor="w")

        codef = tk.Frame(self.nb, bg=THEME["surface"])
        self.nb.add(codef, text=self.T("Python kodu", "Python code"))
        cbar = tk.Frame(codef, bg=THEME["surface"])
        cbar.pack(fill="x")
        self._btn(cbar, "▶ Kodu çalıştır", "▶ Run code", self.run_code, accent=True,
                  bg=THEME["surface"]).pack(side="left", padx=4, pady=4)
        self._btn(cbar, "↺ Koda geri dön", "↺ Revert code", self.revert_code,
                  bg=THEME["surface"]).pack(side="left", padx=2, pady=4)
        cwrap = tk.Frame(codef, bg=THEME["surface"])
        cwrap.pack(fill="both", expand=True)
        self.code_text = tk.Text(cwrap, wrap="none", bg=THEME["surface"], fg=THEME["text"],
                                 insertbackground=THEME["text"], relief="flat", font=("Consolas", 9),
                                 undo=True, padx=6, pady=4)
        csy = ttk.Scrollbar(cwrap, orient="vertical", command=self.code_text.yview)
        csx = ttk.Scrollbar(codef, orient="horizontal", command=self.code_text.xview)
        self.code_text.configure(yscrollcommand=csy.set, xscrollcommand=csx.set)
        csy.pack(side="right", fill="y")
        self.code_text.pack(side="left", fill="both", expand=True)
        csx.pack(fill="x")
        tk.Label(codef, text=self.T(
            "Bu, oynatıcının çalıştırdığı kaynağın ta kendisidir. Değiştirilen kod çalışmadan önce "
            "izin politikasından geçer (dosya, ağ ve süreç erişimi reddedilir).",
            "This is exactly the source the player runs. Edited code must pass the permission "
            "policy first (file, network and process access are refused)."),
            bg=THEME["surface"], fg=THEME["muted"], font=("Segoe UI", 8), wraplength=340,
            justify="left").pack(fill="x", padx=6, pady=4)

    # ------------------------------------------------------------- topic load
    def load_topic(self, topic_label, course_key, examples, matched, scan_path=None):
        self.stop()
        self.topic_label = topic_label or ""
        self.course_key = course_key or ""
        self.scan_path = scan_path
        self.topic_examples = list(examples) if matched else []
        self.course_examples = engine.examples_for_course(course_key) if course_key else list(examples)
        self.scanned_examples = []
        cname = engine.pick(engine.COURSES.get(course_key, ("", "")), self.lang) if course_key else ""
        self.head_title.configure(text="▶ " + (self.topic_label or self.T("Simülasyonlar", "Simulations")))
        self.head_sub.configure(text=(cname + " · " if cname else "") + self.T(
            f"{len(self.topic_examples)} konuya özel, {len(self.course_examples)} kurs örneği",
            f"{len(self.topic_examples)} topic-specific, {len(self.course_examples)} course examples"))
        self.scan_info.configure(text=self._scan_hint())
        self._refresh_filters(prefer="topic" if self.topic_examples else "course")
        self.deiconify()
        self.lift()

    def _scan_hint(self):
        if not self.scan_path:
            return self.T("Tarama için ağaçtan bir konu klasörü/PDF seçin.",
                          "Pick a topic folder/PDF in the tree to scan it.")
        txt = self.T(f"Taranacak: {Path(self.scan_path).name}", f"To scan: {Path(self.scan_path).name}")
        if not scanner.pdf_support():
            txt += self.T("\nPDF metni için pypdf veya PyMuPDF gerekir (şu an yalnızca .txt taranır).",
                          "\nPDF text needs pypdf or PyMuPDF (only .txt is scanned now).")
        return txt

    def _refresh_filters(self, prefer=None):
        self._filters = []
        if self.scanned_examples:
            self._filters.append(("scan", self.T(f"Kaynaktan taranan ({len(self.scanned_examples)})",
                                                 f"Scanned from source ({len(self.scanned_examples)})")))
        if self.topic_examples:
            self._filters.append(("topic", self.T(f"Bu konu ({len(self.topic_examples)})",
                                                  f"This topic ({len(self.topic_examples)})")))
        if self.course_examples:
            self._filters.append(("course", self.T(f"Tüm kurs ({len(self.course_examples)})",
                                                   f"Whole course ({len(self.course_examples)})")))
        self._filters.append(("all", self.T(f"Tüm dersler ({len(engine.all_examples())})",
                                            f"All courses ({len(engine.all_examples())})")))
        self.filter_box.configure(values=[lbl for _, lbl in self._filters])
        keys = [k for k, _ in self._filters]
        idx = keys.index(prefer) if prefer in keys else 0
        self.filter_box.current(idx)
        self._fill_list(select_first=True)

    def _current_pool(self):
        key = self._filters[self.filter_box.current()][0] if self._filters else "all"
        return {"scan": self.scanned_examples, "topic": self.topic_examples,
                "course": self.course_examples}.get(key, engine.all_examples())

    def _fill_list(self, select_first=False):
        q = self.search_var.get().strip().lower()
        pool = self._current_pool()
        self.list_rows = []
        self.listbox.delete(0, "end")
        last_course = None
        for ex in pool:
            title = engine.pick(ex.get("title"), self.lang)
            if q and q not in title.lower() and q not in ex["kind"]:
                continue
            if ex["course"] != last_course and self._filters[self.filter_box.current()][0] == "all":
                last_course = ex["course"]
                self.listbox.insert("end", "── " + engine.pick(engine.COURSES.get(last_course, (last_course,) * 2),
                                                               self.lang))
                self.listbox.itemconfigure("end", foreground=THEME["muted"])
                self.list_rows.append(None)
            self.listbox.insert("end", ("📄 " if ex.get("source") else "▶ ") + title)
            self.list_rows.append(ex)
        if select_first:
            for i, ex in enumerate(self.list_rows):
                if ex is not None:
                    self.listbox.selection_clear(0, "end")
                    self.listbox.selection_set(i)
                    self.listbox.see(i)
                    self.open_example(ex)
                    break

    def _on_pick(self, _e=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        ex = self.list_rows[sel[0]] if sel[0] < len(self.list_rows) else None
        if ex is not None:
            self.open_example(ex)

    # ------------------------------------------------------------- running
    def open_example(self, ex, autoplay=True):
        try:
            sim = engine.Simulation(ex, self.lang)
        except Exception as e:
            self._error(e)
            return
        self.set_simulation(sim, autoplay)

    def set_simulation(self, sim, autoplay=True):
        self.stop()
        self.fig.clear()
        try:
            n, upd = sim.build(self.fig)
            sol = sim.solution()
        except Exception as e:
            self.fig.clear()
            self.canvas.draw()
            self._error(e)
            return
        self.sim, self.update_fn, self.n_frames = sim, upd, n
        self.q_title.configure(text=sim.title() + (self.T("  · düzenlenmiş kod", "  · edited code")
                                                   if sim.custom_code else ""))
        self.q_text.configure(text=sim.question())
        self.q_src.configure(text=sim.source_note())
        self.scale.configure(to=max(1, n - 1))
        self._sol = sol
        self._last_step_count = -1
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", sim.editor_source())
        self._set_status(self.T(f"{n} kare · Boşluk: oynat/duraklat, ←/→: adım",
                                f"{n} frames · Space: play/pause, ←/→: step"))
        self.seek(0)
        if autoplay:
            self.play()

    def _draw(self):
        if not self.update_fn:
            return
        try:
            self.update_fn(self.frame)
            self.canvas.draw()
        except Exception as e:
            self.stop()
            self._error(e)
            return
        self.frame_lbl.configure(text=f"{self.frame + 1}/{self.n_frames}")
        self._scale_guard = True
        try:
            self.scale.set(self.frame)
        finally:
            self._scale_guard = False
        self._render_steps()

    def _render_steps(self, force=False):
        if not self.sim:
            return
        steps = self._sol["steps"]
        last = self.frame >= self.n_frames - 1
        if self.show_all_var.get() or last:
            k = len(steps)
        else:
            k = min(len(steps), 1 + int(self.frame / max(1, self.n_frames - 1) * len(steps)))
        if k == self._last_step_count and not force:
            return
        self._last_step_count = k
        t = self.sol_text
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", self.T("Soru\n", "Problem\n"), "head")
        t.insert("end", self.sim.question() + "\n\n")
        t.insert("end", self.T("Çözüm\n", "Solution\n"), "head")
        for i, s in enumerate(steps[:k]):
            t.insert("end", f"{i + 1}. {s}\n", "cur" if (i == k - 1 and not last) else ())
        if k < len(steps):
            t.insert("end", self.T(f"… {len(steps) - k} adım daha (oynatmaya devam)\n",
                                   f"… {len(steps) - k} more steps (keep playing)\n"), "muted")
        if last or self.show_all_var.get():
            t.insert("end", "\n" + self.T("Cevap: ", "Answer: ") + self._sol["answer"] + "\n", "ans")
        t.configure(state="disabled")

    def _interval(self):
        try:
            sp = float(self.speed_var.get().rstrip("x"))
        except Exception:
            sp = 1.0
        return max(8, int(BASE_INTERVAL_MS / sp))

    def _tick(self):
        """Zamana bağlı oynatma: çizim yavaşsa kare atlanır, süre aynı kalır."""
        self._after = None
        if not self.playing:
            return
        now = time.perf_counter()
        adv = (now - self._t_last) * 1000.0 / self._interval() + self._carry
        k = max(1, int(adv))
        self._carry = max(0.0, adv - k)
        self._t_last = now
        if self.frame >= self.n_frames - 1:
            if self.loop_var.get():
                self.frame = 0
            else:
                self.stop()
                return
        else:
            self.frame = min(self.n_frames - 1, self.frame + k)
        self._draw()
        if self.playing:
            self._after = self.after(self._interval(), self._tick)

    def play(self):
        if not self.update_fn:
            return
        if self.frame >= self.n_frames - 1:
            self.frame = 0
        self.playing = True
        self._t_last = time.perf_counter()
        self._carry = 0.0
        self.play_btn.config(text=self.T("⏸ Duraklat", "⏸ Pause"))
        if self._after is None:
            self._after = self.after(self._interval(), self._tick)

    def stop(self):
        self.playing = False
        if self._after is not None:
            try:
                self.after_cancel(self._after)
            except Exception:
                pass
            self._after = None
        try:
            self.play_btn.config(text=self.T("▶ Oynat", "▶ Play"))
        except Exception:
            pass

    def toggle_play(self):
        self.stop() if self.playing else self.play()

    def seek(self, i):
        self.frame = max(0, min(self.n_frames - 1, int(i)))
        self._draw()

    def step(self, d):
        self.stop()
        self.seek(self.frame + d)

    def _on_scale(self, v):
        if getattr(self, "_scale_guard", False) or not self.update_fn:
            return
        i = int(float(v))
        if i != self.frame:
            self.stop()
            self.seek(i)

    # ------------------------------------------------------------- actions
    def new_numbers(self):
        if not self.sim:
            return
        try:
            self.set_simulation(self.sim.varied(random.randrange(1 << 30)))
            self._set_status(self.T("Aynı soru tipi, yeni sayılar.", "Same problem type, new numbers."))
        except Exception as e:
            self._error(e)

    def reset_example(self):
        if self.sim:
            self.open_example(self.sim.example)

    def run_code(self):
        if not self.sim:
            return
        src = self.code_text.get("1.0", "end-1c")
        try:
            sim = engine.Simulation.from_editor_source(src, self.sim)
        except ValueError as e:
            messagebox.showerror(self.T("Kod çalıştırılmadı", "Code not run"),
                                 self.T("Kod izin politikasından geçmedi veya hatalı:\n\n",
                                        "The code failed the permission policy or is invalid:\n\n") + str(e),
                                 parent=self)
            return
        except Exception as e:
            messagebox.showerror(self.T("Kod hatası", "Code error"), f"{type(e).__name__}: {e}", parent=self)
            return
        self.set_simulation(sim)
        self.nb.select(0)

    def revert_code(self):
        if self.sim:
            self.code_text.delete("1.0", "end")
            self.code_text.insert("1.0", self.sim.editor_source())

    def _safe_name(self):
        base = engine.pick(self.sim.example.get("title"), self.lang) if self.sim else "simulation"
        return "".join(c if c.isalnum() or c in "-_ " else "_" for c in base).strip()[:60] or "simulation"

    def save_py(self):
        if not self.sim:
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".py",
                                            initialfile=self._safe_name() + ".py",
                                            filetypes=[("Python", "*.py")])
        if path:
            Path(path).write_text(self.sim.standalone_script(), encoding="utf-8")
            self._set_status(self.T("Python betiği kaydedildi.", "Python script saved."))

    def save_png(self):
        if not self.sim:
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".png",
                                            initialfile=self._safe_name() + ".png",
                                            filetypes=[("PNG", "*.png")])
        if path:
            self.fig.savefig(path, dpi=130)
            self._set_status(self.T("Kare PNG olarak kaydedildi.", "Frame saved as PNG."))

    def save_gif(self):
        if not self.sim or self._busy:
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".gif",
                                            initialfile=self._safe_name() + ".gif",
                                            filetypes=[("GIF", "*.gif")])
        if not path:
            return
        sim = self.sim
        self._busy = True
        self._set_status(self.T("GIF hazırlanıyor…", "Rendering GIF…"), THEME["muted"])

        def work():
            try:
                engine.export_gif(sim, path)
                msg = (self.T("GIF kaydedildi: ", "GIF saved: ") + Path(path).name, None)
            except Exception as e:
                msg = (f"GIF: {type(e).__name__}: {e}", THEME["danger"])
            self._q.put(("gif", msg))
        threading.Thread(target=work, daemon=True).start()
        self._poll_queue()

    def start_scan(self):
        if self._busy or not self.scan_path:
            if not self.scan_path:
                self._set_status(self._scan_hint(), THEME["danger"])
            return
        self._busy = True
        path, course, change = self.scan_path, self.course_key, self.change_var.get()
        self._set_status(self.T("Kaynak taranıyor…", "Scanning the source…"), THEME["muted"])

        def prog(i, n, name):
            self._q.put(("progress", (i, n, name)))

        def work():
            try:
                res = scanner.scan(path, course, change=change, progress=prog)
                err = None
            except Exception as e:
                res, err = None, e
            self._q.put(("scan", (res, err)))
        threading.Thread(target=work, daemon=True).start()
        self._poll_queue()

    def _poll_queue(self):
        self._poll_after = None
        try:
            while True:
                kind, data = self._q.get_nowait()
                if kind == "progress":
                    i, n, name = data
                    self.scan_info.configure(text=self.T(f"Taranıyor {i}/{n}: {name}",
                                                         f"Scanning {i}/{n}: {name}"))
                elif kind == "scan":
                    self._scan_done(*data)
                elif kind == "gif":
                    self._busy = False
                    self._set_status(*data)
        except queue.Empty:
            pass
        if self._busy:
            self._poll_after = self.after(120, self._poll_queue)

    def _scan_done(self, res, err):
        self._busy = False
        if err is not None:
            self._error(err)
            return
        self.scanned_examples = res["examples"]
        n = len(self.scanned_examples)
        info = self.T(f"{res['files']} dosya tarandı, {n} örnek simülasyona çevrildi.",
                      f"{res['files']} files scanned, {n} examples turned into simulations.")
        if res["skipped_pdfs"]:
            info += self.T(f"\n{res['skipped_pdfs']} PDF atlandı: PDF metni için pypdf veya PyMuPDF kurulu değil "
                           "(pip install pypdf).",
                           f"\n{res['skipped_pdfs']} PDFs skipped: neither pypdf nor PyMuPDF is installed "
                           "(pip install pypdf).")
        info += self.T("\nKitap metni saklanmaz; soru programın kendi cümlesiyle yazılır.",
                       "\nNo book text is stored; questions are reworded by the program.")
        self.scan_info.configure(text=info)
        self._set_status(info.splitlines()[0])
        self._refresh_filters(prefer="scan" if n else None)

    # ------------------------------------------------------------- misc
    def _set_status(self, text, color=None):
        try:
            self.status.configure(text=text, fg=color or THEME["green"])
        except Exception:
            pass

    def _error(self, e):
        self._set_status(f"{type(e).__name__}: {e}"[:160], THEME["danger"])

    def close(self):
        self.stop()
        if self._poll_after is not None:
            try:
                self.after_cancel(self._poll_after)
            except Exception:
                pass
        try:
            self.app._simulation_player = None
        except Exception:
            pass
        self.destroy()


def open_player(app, path=None, course_name="", rel_parts=(), lang="tr"):
    """Kurs ağacından çağrılır: konu için uygun örneklerle oynatıcıyı açar/yeniler."""
    course_key = engine.course_key_from_name(course_name)
    if not course_key:
        for part in rel_parts:
            course_key = engine.course_key_from_name(part)
            if course_key:
                break
    parts = [p for p in rel_parts if p]
    examples, matched = engine.match_examples(parts, course_key)
    label = Path(parts[-1]).stem if parts else (course_name or "")
    label = label.lstrip("0123456789 .-_") or label
    win = getattr(app, "_simulation_player", None)
    try:
        alive = win is not None and win.winfo_exists()
    except Exception:
        alive = False
    if alive and win.lang != lang:
        win.close()
        alive = False
    if not alive:
        win = SimulationPlayer(app, lang)
        app._simulation_player = win
    win.load_topic(label, course_key, examples, matched, scan_path=path)
    return win
