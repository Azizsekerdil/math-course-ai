# -*- coding: utf-8 -*-
"""Math Course AI — bilim laboratuvarlari.

Ana dosyadan (Math_Course_AI.pyw) V48'de mekanik olarak cikarildi.
Bes panel: MathDataLab (veri->matematik), PhysicsMathLab, ChemistryMathLab
(+periyodik tablo araclari), MathDNALab, MathQuantumLab. Hepsi ana
uygulamadaki tek "🧪 Lab'lar" sekmesinin ic sekmelerinde yasar ve
_ensure_labs_built ile tembel kurulur; her sinif (master, app) alir.
"""

import os
import re
import io
import json
import math
import time
import wave
import struct
import random
import threading
from pathlib import Path
from datetime import datetime
from fractions import Fraction
from collections import Counter
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import numpy as np
except Exception:
    np = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

try:
    import cv2
except Exception:
    cv2 = None

from mca_common import (
    APP_FOLDER, THEME, RoundedButton, now_iso, read_text_file, short_name,
)

class MathDataLab(ttk.Frame):
    """Educational data-to-math laboratory.

    This module turns images, text, WAV audio, and video metadata into a clear
    explanation of the mathematical object behind the data: vector, matrix,
    tensor, frequency domain, or embedding space.
    """

    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".aac"}
    VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    TEXT_EXTS = {".txt", ".md", ".rtf", ".docx", ".pdf"}

    def __init__(self, master, app):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        self.file_path = None
        self.last_report = ""
        self._build()

    def _build(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Math Data Lab", style="Header.TLabel").pack(side="left")
        ttk.Label(
            top,
            text="Fotoğraf, ses, video ve metni matematiksel uzaya indirger.",
            style="Muted.TLabel",
        ).pack(side="left", padx=12)

        row = ttk.Frame(self, style="Panel.TFrame")
        row.pack(fill="x", padx=8, pady=4)
        RoundedButton(row, text="Dosya Yükle", command=self.choose_file).pack(side="left", padx=3)
        RoundedButton(row, text="Seçili Kaynağı Kullan", command=self.use_selected_resource).pack(side="left", padx=3)
        RoundedButton(row, text="Analiz Et", command=self.analyze).pack(side="left", padx=3)
        RoundedButton(row, text="Rapor Kaydet", command=self.save_report).pack(side="left", padx=3)
        self.file_label = ttk.Label(row, text="Dosya seçilmedi.", style="Muted.TLabel")
        self.file_label.pack(side="left", padx=10)

        info = (
            "Bu modül veri bilimi mantığını öğretmek için tasarlandı: "
            "girdi türünü algılar, veriyi sayısal temsile çevirir, kullanılan formülü LaTeX olarak verir "
            "ve verinin hangi matematiksel uzaya düştüğünü açıklar."
        )
        tk.Label(self, text=info, justify="left", fg=THEME["muted"], bg=THEME["panel"], wraplength=1180).pack(fill="x", padx=12, pady=(0, 8))

        self.output = tk.Text(self, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.output.pack(fill="both", expand=True, padx=8, pady=8)
        self.output.insert("1.0", self.default_intro())

    def default_intro(self):
        return (
            "Math Data Lab hazır.\n\n"
            "Kullanım:\n"
            "1. Dosya Yükle ile fotoğraf/ses/video/metin seç.\n"
            "2. Analiz Et butonuna bas.\n"
            "3. Program şu bilgileri verir:\n"
            "   - Veri türü\n"
            "   - Matematiksel temsil\n"
            "   - LaTeX formül\n"
            "   - Eğitici açıklama\n"
            "   - Verinin ait olduğu matematiksel uzay\n\n"
            "Örnek: Bir görsel = H x W x 3 boyutlu tensör, bir ses = zaman sinyali ve FFT sonrası frekans uzayı, metin = token/embedding vektör uzayıdır."
        )

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Math Data Lab için dosya seç",
            filetypes=[
                ("Supported", "*.png;*.jpg;*.jpeg;*.bmp;*.webp;*.wav;*.mp3;*.flac;*.m4a;*.mp4;*.avi;*.mov;*.mkv;*.webm;*.txt;*.md;*.rtf;*.docx;*.pdf"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.file_path = path
            self.file_label.config(text=short_name(path, 80))

    def use_selected_resource(self):
        if not self.app.selected_path:
            messagebox.showinfo("Kaynak seçilmedi", "Soldaki Course Resources listesinden bir dosya seç.")
            return
        p = Path(self.app.selected_path)
        if p.is_dir():
            messagebox.showinfo("Dosya gerekli", "Bir klasör değil, PDF/metin/görsel/ses/video dosyası seç.")
            return
        self.file_path = str(p)
        self.file_label.config(text=short_name(p, 80))

    def analyze(self):
        if not self.file_path:
            messagebox.showwarning("Dosya gerekli", "Önce analiz edilecek bir dosya seç.")
            return
        path = Path(self.file_path)
        if not path.exists():
            messagebox.showerror("Dosya bulunamadı", str(path))
            return
        try:
            ext = path.suffix.lower()
            if ext in self.IMAGE_EXTS:
                report = self.analyze_image(path)
            elif ext in self.TEXT_EXTS:
                report = self.analyze_text(path)
            elif ext in self.AUDIO_EXTS:
                report = self.analyze_audio(path)
            elif ext in self.VIDEO_EXTS:
                report = self.analyze_video(path)
            else:
                report = self.analyze_unknown(path)
            self.last_report = report
            self.output.delete("1.0", "end")
            self.output.insert("1.0", report)
        except Exception as exc:
            messagebox.showerror("Analiz hatası", str(exc))

    def header(self, title, path):
        return (
            f"{title}\n"
            f"Dosya: {path}\n"
            f"Oluşturulma zamanı: {now_iso()}\n"
            + "=" * 72 + "\n\n"
        )

    def analyze_image(self, path):
        if Image is None:
            return self.header("GÖRÜNTÜ ANALİZİ", path) + "Pillow kurulu değil. Görüntü analizi için: pip install pillow"
        img = Image.open(path).convert("RGB")
        w, h = img.size
        lines = [self.header("GÖRÜNTÜ ANALİZİ", path)]
        lines.append("1. Veri türü\nGirdi bir görüntü dosyasıdır. Bilgisayar görüntüyü piksellerden oluşan sayısal bir yapı olarak tutar.\n")
        lines.append("2. Matematiksel temsil\nRenkli bir görüntü şu tensörle temsil edilir:\n")
        lines.append("LaTeX: I \u2208 R^{H \\times W \\times 3}\n")
        lines.append("Burada H yükseklik, W genişlik, 3 ise RGB renk kanallarıdır.\n")
        lines.append(f"Bu dosyada yaklaşık boyut: H={h}, W={w}, C=3. Yani tensör boyutu: {h} x {w} x 3.\n")
        lines.append("3. Piksel formülü\nLaTeX: I(x,y) = [R(x,y), G(x,y), B(x,y)]\n")
        lines.append("Anlamı: Her piksel konumunda kırmızı, yeşil ve mavi kanal değerleri vardır.\n")
        lines.append("4. Gri tonlama dönüşümü\nLaTeX: Y = 0.299R + 0.587G + 0.114B\n")
        lines.append("Anlamı: Renkli görüntü tek kanallı yoğunluk matrisine dönüştürülür. İnsan gözü yeşile daha duyarlı olduğu için G katsayısı daha büyüktür.\n")

        if np is not None:
            arr = np.array(img, dtype=np.float32)
            means = arr.reshape(-1, 3).mean(axis=0)
            mins = arr.reshape(-1, 3).min(axis=0)
            maxs = arr.reshape(-1, 3).max(axis=0)
            gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            lines.append("5. Sayısal özet\n")
            lines.append(f"Ortalama RGB: R={means[0]:.2f}, G={means[1]:.2f}, B={means[2]:.2f}\n")
            lines.append(f"Minimum RGB: R={mins[0]:.0f}, G={mins[1]:.0f}, B={mins[2]:.0f}\n")
            lines.append(f"Maksimum RGB: R={maxs[0]:.0f}, G={maxs[1]:.0f}, B={maxs[2]:.0f}\n")
            lines.append(f"Gri ton ortalaması: {gray.mean():.2f}, standart sapma: {gray.std():.2f}\n\n")
            try:
                thumb = img.resize((min(96, w), min(96, h))).convert("L")
                g = np.array(thumb, dtype=np.float32) / 255.0
                svals = np.linalg.svd(g, compute_uv=False)[:5]
                lines.append("6. Matris ayrıştırma / SVD fikri\n")
                lines.append("LaTeX: A = U \\Sigma V^T\n")
                lines.append("Anlamı: Görüntü matrisi temel desenlere ayrılır. Büyük singular değerler görüntünün ana yapısını taşır.\n")
                lines.append("İlk 5 singular değer: " + ", ".join(f"{v:.3f}" for v in svals) + "\n\n")
            except Exception:
                pass
            try:
                fft = np.fft.fftshift(np.fft.fft2(gray))
                mag = np.log1p(np.abs(fft))
                lines.append("7. Frekans analizi / 2D FFT\n")
                lines.append("LaTeX: F(u,v) = \\\sum_x \\\sum_y I(x,y)e^{-j2\\pi(ux/H + vy/W)}\n")
                lines.append("Anlamı: Görüntüdeki yavaş değişimler düşük frekans, keskin kenarlar ve detaylar yüksek frekans olarak görünür.\n")
                lines.append(f"FFT log-genlik ortalaması: {mag.mean():.3f}\n\n")
            except Exception:
                pass
        else:
            pixels = list(img.resize((min(w, 200), min(h, 200))).getdata())
            n = max(1, len(pixels))
            means = [sum(px[i] for px in pixels) / n for i in range(3)]
            lines.append("5. Sayısal özet\n")
            lines.append(f"Ortalama RGB yaklaşık: R={means[0]:.2f}, G={means[1]:.2f}, B={means[2]:.2f}\n")
            lines.append("Not: SVD ve FFT analizi için numpy kurulu olmalı: pip install numpy\n\n")

        lines.append("8. Matematiksel uzay tanımı\n")
        lines.append(f"Bu görüntü R^{{{h} x {w} x 3}} uzayında bir tensördür. Gri tonlama sonrası R^{{{h} x {w}}} uzayında bir matristir. FFT sonrası frekans uzayında karmaşık değerli bir matris gibi yorumlanır.\n")
        return "".join(lines)

    def analyze_text(self, path):
        text = read_text_file(path, 120_000)
        tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+", text.lower())
        counter = Counter(tokens)
        vocab = len(counter)
        total = len(tokens)
        top = counter.most_common(12)
        dim = 64
        vec = [0.0] * dim
        for tok in tokens:
            vec[hash(tok) % dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vec = [v / norm for v in vec]
        sample = ", ".join(f"{v:.3f}" for v in vec[:10])
        lines = [self.header("METİN ANALİZİ", path)]
        lines.append("1. Veri türü\nGirdi metindir. Metin doğrudan sayı olmadığı için önce tokenlara, sonra vektör temsiline dönüştürülür.\n\n")
        lines.append("2. Tokenizasyon\nLaTeX: text \\rightarrow (token_1, token_2, ..., token_n)\n")
        lines.append(f"Bu dosyada bulunan token sayısı: {total}, benzersiz token sayısı: {vocab}.\n")
        if top:
            lines.append("En sık tokenlar: " + ", ".join(f"{w}:{c}" for w, c in top) + "\n\n")
        lines.append("3. Bag-of-Words vektörü\nLaTeX: x_i = count(token_i)\n")
        lines.append("Anlamı: Her kelime bir boyut gibi düşünülür; kelimenin kaç kez geçtiği o boyuttaki değerdir.\n\n")
        lines.append("4. Basit embedding / hashing vektörü\nLaTeX: e = f(text) \\in R^d\n")
        lines.append(f"Bu demo metni d={dim} boyutlu normalize edilmiş bir vektöre indirger. İlk 10 değer: [{sample}]\n\n")
        lines.append("5. Matematiksel uzay tanımı\n")
        lines.append(f"Metin önce ayrık semboller dizisidir. Bag-of-Words ile R^{vocab} uzayına, hashing embedding ile R^{dim} uzayına aktarılır. Böylece metin üzerinde uzaklık, benzerlik, sınıflandırma ve kümeleme yapılabilir.\n")
        return "".join(lines)

    def analyze_audio(self, path):
        ext = path.suffix.lower()
        lines = [self.header("SES ANALİZİ", path)]
        lines.append("1. Veri türü\nSes, zamana bağlı bir sinyaldir. Matematikte x(t) veya ayrık durumda x[n] olarak gösterilir.\n\n")
        lines.append("2. Zaman alanı temsili\nLaTeX: x[n], n = 0,1,2,...,N-1\n")
        lines.append("Anlamı: Mikrofonun ölçtüğü basınç değişimleri belirli aralıklarla örneklenir.\n\n")
        if ext != ".wav":
            lines.append("Bu sürümde sayısal ses okuma yerleşik olarak WAV dosyalarında çalışır. MP3/FLAC/M4A için ffmpeg/pydub gibi çözücü gerekir.\n\n")
        else:
            try:
                with wave.open(str(path), "rb") as wf:
                    channels = wf.getnchannels()
                    rate = wf.getframerate()
                    frames = wf.getnframes()
                    sampwidth = wf.getsampwidth()
                    duration = frames / float(rate or 1)
                    raw = wf.readframes(min(frames, rate * 10))
                lines.append(f"Örnekleme oranı: {rate} Hz\nKanal sayısı: {channels}\nÖrnek sayısı: {frames}\nSüre: {duration:.2f} saniye\nÖrnek genişliği: {sampwidth} byte\n\n")
                if np is not None and raw:
                    if sampwidth == 1:
                        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128
                    elif sampwidth == 2:
                        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                    elif sampwidth == 4:
                        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32)
                    else:
                        data = np.array([], dtype=np.float32)
                    if data.size and channels > 1:
                        data = data.reshape(-1, channels).mean(axis=1)
                    if data.size:
                        rms = float(np.sqrt(np.mean(data ** 2)))
                        data = data[: min(data.size, rate * 5)]
                        spec = np.fft.rfft(data * np.hanning(data.size))
                        freqs = np.fft.rfftfreq(data.size, d=1.0 / rate)
                        mag = np.abs(spec)
                        top_idx = np.argsort(mag)[-5:][::-1]
                        top_freqs = [(float(freqs[i]), float(mag[i])) for i in top_idx if freqs[i] > 0]
                        lines.append(f"RMS enerji yaklaşık: {rms:.2f}\n")
                        lines.append("Baskın frekanslar: " + ", ".join(f"{f:.1f} Hz" for f, _ in top_freqs[:5]) + "\n\n")
                elif np is None:
                    lines.append("FFT sayısal analizi için numpy kurulu olmalı: pip install numpy\n\n")
            except Exception as exc:
                lines.append(f"WAV okuma hatası: {exc}\n\n")
        lines.append("3. Frekans alanı / FFT\nLaTeX: X_k = \\\sum_{n=0}^{N-1} x_n e^{-i2\\pi kn/N}\n")
        lines.append("Anlamı: Sesin zaman içindeki dalgası frekans bileşenlerine ayrılır. Yani hangi frekansların güçlü olduğunu görürüz.\n\n")
        lines.append("4. Matematiksel uzay tanımı\n")
        lines.append("Ham ses R^N uzayında bir vektördür. Stereo ses R^{N x 2} matrisidir. FFT sonrası karmaşık frekans uzayında C^K vektörü olarak yorumlanır.\n")
        return "".join(lines)

    def analyze_video(self, path):
        lines = [self.header("VİDEO ANALİZİ", path)]
        lines.append("1. Veri türü\nVideo, zaman boyunca sıralanmış görüntü karelerinden oluşur.\n\n")
        lines.append("2. Matematiksel temsil\nLaTeX: V \\in R^{T \\times H \\times W \\times C}\n")
        lines.append("Burada T kare sayısı, H yükseklik, W genişlik, C renk kanalıdır.\n\n")
        if cv2 is not None:
            try:
                cap = cv2.VideoCapture(str(path))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                ok, frame = cap.read()
                cap.release()
                lines.append(f"Genişlik: {w}\nYükseklik: {h}\nKare sayısı: {frames}\nFPS: {fps:.2f}\nTahmini süre: {frames / fps:.2f} saniye\n\n" if fps else f"Genişlik: {w}\nYükseklik: {h}\nKare sayısı: {frames}\nFPS okunamadı\n\n")
                if ok and np is not None:
                    mean_bgr = frame.mean(axis=(0, 1))
                    lines.append(f"İlk karenin ortalama BGR değeri: B={mean_bgr[0]:.2f}, G={mean_bgr[1]:.2f}, R={mean_bgr[2]:.2f}\n\n")
            except Exception as exc:
                lines.append(f"Video metadata okuma hatası: {exc}\n\n")
        else:
            lines.append("OpenCV kurulu olmadığı için bu sürüm videonun metadata bilgisini okuyamadı. Kurulum: pip install opencv-python\n\n")
        lines.append("3. Hareketin matematiği\nLaTeX: \\Delta I_t = I_{t+1} - I_t\n")
        lines.append("Anlamı: Ardışık kareler çıkarılarak hareket veya değişim bölgeleri bulunabilir.\n\n")
        lines.append("4. Matematiksel uzay tanımı\nVideo, zaman boyutu eklenmiş bir tensördür. Bu yüzden görüntüden daha zengindir: hem mekansal yapı hem zamansal değişim içerir.\n")
        return "".join(lines)

    def analyze_unknown(self, path):
        return (
            self.header("BİLİNMEYEN VERİ TÜRÜ", path)
            + "Bu dosya türü için özel okuyucu tanımlı değil. Yine de temel fikir aynıdır: bilgisayar veriyi bayt dizisi olarak görür.\n\n"
            + "LaTeX: b = (b_1, b_2, ..., b_N), b_i \\in {0,...,255}\n\n"
            + "Matematiksel uzay: Ham dosya R^N veya {0,...,255}^N üzerinde ayrık bir vektör gibi düşünülebilir. Anlamlı analiz için dosya türüne özel çözücü gerekir.\n"
        )

    def save_report(self):
        if not self.last_report:
            self.last_report = self.output.get("1.0", "end").strip()
        if not self.last_report:
            messagebox.showinfo("Rapor yok", "Önce bir analiz yap.")
            return
        reports = APP_FOLDER / "Reports"
        reports.mkdir(parents=True, exist_ok=True)
        default_name = reports / f"math_data_lab_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        out = filedialog.asksaveasfilename(title="Math Data Lab raporu kaydet", initialfile=default_name.name, initialdir=str(reports), defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not out:
            return
        Path(out).write_text(self.last_report, encoding="utf-8")
        messagebox.showinfo("Kaydedildi", out)


class PhysicsMathLab(ttk.Frame):
    """Physics-to-math educational module."""

    DEFAULTS = {
        "Düzgün doğrusal hareket": "x0=0\nv=5\nt=3",
        "Newton 2. yasa": "m=2\na=9.8",
        "Atış hareketi": "v0=20\ntheta=45\ng=9.81\ny0=0",
        "Basit harmonik hareket": "m=1\nk=4\nA=2\nphi=0\nt=1",
        "Dalga hareketi": "A=1\nlambda=2\nf=3\nx=1\nt=0.25\nphi=0",
        "Elektrik alan": "q=0.000001\nr=0.5\nk=8987551792.3",
    }

    def __init__(self, master, app):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        self.scenario = tk.StringVar(value="Atış hareketi")
        self._build()
        self.load_defaults()

    def _build(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Physics → Math Lab", style="Header.TLabel").pack(side="left")
        ttk.Label(top, text="Fizik olayını denkleme, vektöre, fonksiyona veya diferansiyel denkleme çevirir.", style="Muted.TLabel").pack(side="left", padx=12)

        row = ttk.Frame(self, style="Panel.TFrame")
        row.pack(fill="x", padx=8, pady=4)
        ttk.Label(row, text="Fizik olayı:", style="Muted.TLabel").pack(side="left")
        combo = ttk.Combobox(row, textvariable=self.scenario, values=list(self.DEFAULTS.keys()), width=32, state="readonly")
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda e: self.load_defaults())
        RoundedButton(row, text="Varsayılan Değerleri Yükle", command=self.load_defaults).pack(side="left", padx=3)
        RoundedButton(row, text="Matematiğe Dönüştür", command=self.analyze).pack(side="left", padx=3)
        RoundedButton(row, text="Rapor Kaydet", command=self.save_report).pack(side="left", padx=3)
        RoundedButton(row, text="Grafik Çiz", command=self.draw_graph).pack(side="left", padx=3)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(body, style="Panel.TFrame")
        right = ttk.Frame(body, style="Panel.TFrame")
        body.add(left, weight=1)
        body.add(right, weight=3)

        ttk.Label(left, text="Parametreler", style="Header.TLabel").pack(fill="x", padx=8, pady=(8, 2))
        ttk.Label(left, text="Her satıra key=value yaz. Örnek: v0=20", style="Muted.TLabel").pack(fill="x", padx=8, pady=(0, 6))
        self.params_text = tk.Text(left, height=14, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.params_text.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Label(right, text="Fiziğin Matematiğe Yansıması", style="Header.TLabel").pack(fill="x", padx=8, pady=(8, 2))
        self.output = tk.Text(right, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.output.pack(fill="both", expand=True, padx=8, pady=8)
        self.graph_canvas = tk.Canvas(right, height=230, bg=THEME["surface"], highlightbackground=THEME["line"], highlightthickness=1)
        self.graph_canvas.pack(fill="x", padx=8, pady=(0, 8))

    def load_defaults(self):
        self.params_text.delete("1.0", "end")
        self.params_text.insert("1.0", self.DEFAULTS.get(self.scenario.get(), ""))

    def parse_params(self):
        vals = {}
        for line in self.params_text.get("1.0", "end").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().replace(",", ".")
            try:
                vals[k] = float(v)
            except Exception:
                vals[k] = v
        return vals

    def analyze(self):
        vals = self.parse_params()
        sc = self.scenario.get()
        if sc == "Düzgün doğrusal hareket":
            report = self.linear_motion(vals)
        elif sc == "Newton 2. yasa":
            report = self.newton_second(vals)
        elif sc == "Atış hareketi":
            report = self.projectile(vals)
        elif sc == "Basit harmonik hareket":
            report = self.harmonic(vals)
        elif sc == "Dalga hareketi":
            report = self.wave_motion(vals)
        elif sc == "Elektrik alan":
            report = self.electric_field(vals)
        else:
            report = "Bilinmeyen senaryo."
        self.output.delete("1.0", "end")
        self.output.insert("1.0", report)

    def base_header(self, title):
        return f"{title}\nOluşturulma zamanı: {now_iso()}\n" + "=" * 72 + "\n\n"

    def linear_motion(self, v):
        x0 = float(v.get("x0", 0)); vel = float(v.get("v", 0)); t = float(v.get("t", 0))
        x = x0 + vel * t
        return (
            self.base_header("DÜZGÜN DOĞRUSAL HAREKET")
            + "Fiziksel fikir: Cisim sabit hızla ilerliyorsa konum zamana göre doğrusal değişir.\n\n"
            + "Matematiksel model:\nLaTeX: x(t) = x_0 + vt\n\n"
            + f"Hesap: x({t}) = {x0} + {vel} * {t} = {x:.4g}\n\n"
            + "Matematiksel uzay: Konum x gerçek sayı doğrusunda R içindedir. Durum vektörü olarak [x, v] kullanırsak sistem R^2 uzayında temsil edilir.\n"
        )

    def newton_second(self, v):
        m = float(v.get("m", 1)); a = float(v.get("a", 0)); F = m * a
        return (
            self.base_header("NEWTON 2. YASA")
            + "Fiziksel fikir: Kuvvet, kütlenin ivmeye karşı verdiği dinamik tepkiyi ölçer.\n\n"
            + "Matematiksel model:\nLaTeX: \\vec{F} = m\\vec{a}\n\n"
            + f"Hesap: F = {m} * {a} = {F:.4g} N\n\n"
            + "Matematiksel uzay: Tek boyutta F ve a R içindedir. Üç boyutlu uzayda kuvvet ve ivme R^3 vektörleridir. Bu yüzden yasa bir vektör denklemdir.\n"
        )

    def projectile(self, v):
        v0 = float(v.get("v0", 20)); theta = math.radians(float(v.get("theta", 45))); g = float(v.get("g", 9.81)); y0 = float(v.get("y0", 0))
        vx = v0 * math.cos(theta); vy = v0 * math.sin(theta)
        rng = (v0 ** 2) * math.sin(2 * theta) / g if abs(y0) < 1e-12 and g else None
        hmax = y0 + (vy ** 2) / (2 * g) if g else None
        t_flight = (2 * vy / g) if abs(y0) < 1e-12 and g else None
        return (
            self.base_header("ATIŞ HAREKETİ")
            + "Fiziksel fikir: Yatay hareket sabit hızlı, düşey hareket ise yerçekimi nedeniyle ivmelidir.\n\n"
            + "Matematiksel model:\nLaTeX: x(t)=v_0\\cos(\\theta)t\n"
            + "LaTeX: y(t)=y_0+v_0\\sin(\\theta)t-\\\frac{1}{2}gt^2\n\n"
            + f"Bileşenler: vx={vx:.4g}, vy={vy:.4g}\n"
            + (f"Menzil yaklaşık: R={rng:.4g}\n" if rng is not None else "Menzil için genel ikinci derece denklem çözülmelidir.\n")
            + (f"Maksimum yükseklik yaklaşık: H={hmax:.4g}\n" if hmax is not None else "")
            + (f"Uçuş süresi yaklaşık: T={t_flight:.4g}\n\n" if t_flight is not None else "\n")
            + "Matematiksel uzay: Konum r(t)=[x(t),y(t)] bir R^2 vektörüdür. Zaman parametresi t değiştikçe bu vektör parabolik bir eğri çizer.\n"
        )

    def harmonic(self, v):
        m = float(v.get("m", 1)); k = float(v.get("k", 1)); A = float(v.get("A", 1)); phi = float(v.get("phi", 0)); t = float(v.get("t", 0))
        omega = math.sqrt(k / m) if m else 0
        x = A * math.cos(omega * t + phi)
        return (
            self.base_header("BASİT HARMONİK HAREKET")
            + "Fiziksel fikir: Yay gibi sistemlerde geri çağırıcı kuvvet konuma zıt yöndedir.\n\n"
            + "Matematiksel model:\nLaTeX: m\\\frac{d^2x}{dt^2}+kx=0\n"
            + "LaTeX: x(t)=A\\cos(\\omega t + \\varphi), \\omega=\\\sqrt{k/m}\n\n"
            + f"Açısal frekans: omega={omega:.4g}\n"
            + f"Hesap: x({t})={x:.4g}\n\n"
            + "Matematiksel uzay: Sistem ikinci dereceden diferansiyel denklemle tanımlanır. Durum vektörü [x, v] alınırsa faz uzayı R^2 olur.\n"
        )

    def wave_motion(self, v):
        A = float(v.get("A", 1)); lam = float(v.get("lambda", 1)); f = float(v.get("f", 1)); x = float(v.get("x", 0)); t = float(v.get("t", 0)); phi = float(v.get("phi", 0))
        k = 2 * math.pi / lam if lam else 0
        omega = 2 * math.pi * f
        speed = f * lam
        y = A * math.sin(k * x - omega * t + phi)
        return (
            self.base_header("DALGA HAREKETİ")
            + "Fiziksel fikir: Dalga, enerjinin uzay ve zamanda periyodik yayılmasıdır.\n\n"
            + "Matematiksel model:\nLaTeX: y(x,t)=A\\sin(kx-\\omega t+\\varphi)\n"
            + "LaTeX: k=\\\frac{2\\pi}{\\lambda}, \\omega=2\\pi f, v=f\\lambda\n\n"
            + f"k={k:.4g}, omega={omega:.4g}, dalga hızı={speed:.4g}\n"
            + f"Hesap: y({x},{t})={y:.4g}\n\n"
            + "Matematiksel uzay: Dalga bir fonksiyon uzayının elemanıdır. Her t anında y(x) bir fonksiyon; ayrık örneklenirse R^N vektörüdür.\n"
        )

    def electric_field(self, v):
        q = float(v.get("q", 1e-6)); r = float(v.get("r", 1)); kk = float(v.get("k", 8.9875517923e9))
        E = kk * q / (r ** 2) if r else float("inf")
        return (
            self.base_header("ELEKTRİK ALAN")
            + "Fiziksel fikir: Bir yük çevresinde başka yüklere kuvvet uygulayabilecek bir alan oluşturur.\n\n"
            + "Matematiksel model:\nLaTeX: \\vec{E}(r)=k\\\frac{q}{r^2}\\hat{r}\n"
            + "LaTeX: \\vec{F}=q_0\\vec{E}\n\n"
            + f"Hesap: E = {kk:.4g} * {q} / {r}^2 = {E:.4g} N/C\n\n"
            + "Matematiksel uzay: Elektrik alan her noktaya bir vektör atar. Bu yüzden R^3 üzerinde tanımlı bir vektör alanıdır: E: R^3 -> R^3.\n"
        )


    def draw_series(self, points, title="Grafik", xlabel="x", ylabel="y"):
        canvas = getattr(self, "graph_canvas", None)
        if canvas is None:
            return
        canvas.delete("all")
        w = max(canvas.winfo_width(), 700)
        h = max(canvas.winfo_height(), 220)
        margin = 42
        canvas.create_text(12, 10, anchor="nw", fill=THEME["text"], text=title, font=("Segoe UI", 10, "bold"))
        if not points:
            canvas.create_text(margin, h/2, anchor="w", fill=THEME["muted"], text="Grafik için yeterli veri yok.")
            return
        xs = [p[0] for p in points]; ys = [p[1] for p in points]
        xmin, xmax = min(xs), max(xs); ymin, ymax = min(ys), max(ys)
        if abs(xmax - xmin) < 1e-12:
            xmax = xmin + 1
        if abs(ymax - ymin) < 1e-12:
            ymax = ymin + 1
        def sx(x): return margin + (x - xmin) / (xmax - xmin) * (w - 2*margin)
        def sy(y): return h - margin - (y - ymin) / (ymax - ymin) * (h - 2*margin)
        canvas.create_line(margin, h-margin, w-margin, h-margin, fill=THEME["muted"])
        canvas.create_line(margin, margin, margin, h-margin, fill=THEME["muted"])
        canvas.create_text(w/2, h-12, fill=THEME["muted"], text=xlabel)
        canvas.create_text(12, h/2, fill=THEME["muted"], text=ylabel, angle=90)
        canvas.create_text(margin, h-margin+14, fill=THEME["muted"], text=f"{xmin:.3g}")
        canvas.create_text(w-margin, h-margin+14, fill=THEME["muted"], text=f"{xmax:.3g}")
        canvas.create_text(margin-8, h-margin, anchor="e", fill=THEME["muted"], text=f"{ymin:.3g}")
        canvas.create_text(margin-8, margin, anchor="e", fill=THEME["muted"], text=f"{ymax:.3g}")
        coords = []
        for x, y in points:
            coords.extend([sx(x), sy(y)])
        if len(coords) >= 4:
            canvas.create_line(*coords, fill=THEME["accent"], width=2, smooth=True)
        for x, y in points[::max(1, len(points)//18)]:
            canvas.create_oval(sx(x)-2, sy(y)-2, sx(x)+2, sy(y)+2, fill=THEME["green"], outline="")

    def draw_graph(self):
        vals = self.parse_params()
        sc = self.scenario.get()
        points = []
        title = sc
        xlabel = "t"
        ylabel = "y"
        try:
            if sc == "Düzgün doğrusal hareket":
                x0 = float(vals.get("x0", 0)); vel = float(vals.get("v", 0)); tmax = max(float(vals.get("t", 5)), 1.0)
                points = [(i*tmax/80, x0 + vel*(i*tmax/80)) for i in range(81)]
                title = "Konum - zaman grafiği: x(t)=x0+vt"; xlabel="t"; ylabel="x(t)"
            elif sc == "Newton 2. yasa":
                m = max(float(vals.get("m", 1)), 1e-9); amax = max(abs(float(vals.get("a", 10))), 1.0)
                points = [(-amax + 2*amax*i/80, m*(-amax + 2*amax*i/80)) for i in range(81)]
                title = "Kuvvet - ivme grafiği: F=ma"; xlabel="a"; ylabel="F"
            elif sc == "Atış hareketi":
                v0 = float(vals.get("v0", 20)); theta = math.radians(float(vals.get("theta", 45))); g = float(vals.get("g", 9.81)); y0 = float(vals.get("y0", 0))
                vy = v0 * math.sin(theta); vx = v0 * math.cos(theta)
                tmax = max(2*vy/g if g and vy > 0 else float(vals.get("t", 5)), 1.0)
                points = []
                for i in range(101):
                    t = i*tmax/100
                    x = vx*t
                    y = y0 + vy*t - 0.5*g*t*t
                    points.append((x, y))
                title = "Atış hareketi y(x) grafiği"; xlabel="x"; ylabel="y"
            elif sc == "Basit harmonik hareket":
                m = float(vals.get("m", 1)); k = float(vals.get("k", 1)); A = float(vals.get("A", 1)); phi = float(vals.get("phi", 0))
                omega = math.sqrt(k/m) if m else 1
                tmax = max(2*math.pi/omega*2 if omega else 10, 1.0)
                points = [(i*tmax/120, A*math.cos(omega*(i*tmax/120)+phi)) for i in range(121)]
                title = "Basit harmonik hareket: x(t)"; xlabel="t"; ylabel="x(t)"
            elif sc == "Dalga hareketi":
                A = float(vals.get("A", 1)); lam = float(vals.get("lambda", 1)); f = float(vals.get("f", 1)); t = float(vals.get("t", 0)); phi = float(vals.get("phi", 0))
                k = 2*math.pi/lam if lam else 1; omega = 2*math.pi*f
                xmax = max(lam*2, 1.0)
                points = [(i*xmax/120, A*math.sin(k*(i*xmax/120)-omega*t+phi)) for i in range(121)]
                title = "Dalga profili: y(x,t)"; xlabel="x"; ylabel="y"
            elif sc == "Elektrik alan":
                q = float(vals.get("q", 1e-6)); kk = float(vals.get("k", 8.9875517923e9)); r0 = max(float(vals.get("r", 0.5)), 0.05)
                rmax = max(r0*4, 1.0)
                points = [(0.05 + (rmax-0.05)*i/100, kk*q/((0.05 + (rmax-0.05)*i/100)**2)) for i in range(101)]
                title = "Elektrik alan: E(r)=kq/r²"; xlabel="r"; ylabel="E"
            self.draw_series(points, title, xlabel, ylabel)
        except Exception as exc:
            self.graph_canvas.delete("all")
            self.graph_canvas.create_text(20, 30, anchor="nw", fill=THEME["danger"], text=f"Grafik hatası: {exc}")

    def save_report(self):
        report = self.output.get("1.0", "end").strip()
        if not report:
            messagebox.showinfo("Rapor yok", "Önce Matematiğe Dönüştür butonuna bas.")
            return
        reports = APP_FOLDER / "Reports"
        reports.mkdir(parents=True, exist_ok=True)
        default_name = reports / f"physics_math_lab_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        out = filedialog.asksaveasfilename(title="Physics Math Lab raporu kaydet", initialfile=default_name.name, initialdir=str(reports), defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not out:
            return
        Path(out).write_text(report, encoding="utf-8")
        messagebox.showinfo("Kaydedildi", out)


class MathDNALab(ttk.Frame):
    """Educational DNA-to-math and digital-data-to-DNA laboratory.

    This is an in-silico learning module. It teaches how DNA can be represented
    as strings, vectors, k-mer frequency vectors, information, and simple digital
    storage codes. It does not design organisms or provide wet-lab protocols.
    """

    BASES = "ACGT"
    COMPLEMENT = str.maketrans("ACGTUacgtu", "TGCAAtgcaa")
    BIT_TO_BASE = {"00": "A", "01": "C", "10": "G", "11": "T"}
    BASE_TO_BIT = {"A": "00", "C": "01", "G": "10", "T": "11"}
    CODON_TABLE = {
        "TTT":"F","TTC":"F","TTA":"L","TTG":"L","TCT":"S","TCC":"S","TCA":"S","TCG":"S",
        "TAT":"Y","TAC":"Y","TAA":"*","TAG":"*","TGT":"C","TGC":"C","TGA":"*","TGG":"W",
        "CTT":"L","CTC":"L","CTA":"L","CTG":"L","CCT":"P","CCC":"P","CCA":"P","CCG":"P",
        "CAT":"H","CAC":"H","CAA":"Q","CAG":"Q","CGT":"R","CGC":"R","CGA":"R","CGG":"R",
        "ATT":"I","ATC":"I","ATA":"I","ATG":"M","ACT":"T","ACC":"T","ACA":"T","ACG":"T",
        "AAT":"N","AAC":"N","AAA":"K","AAG":"K","AGT":"S","AGC":"S","AGA":"R","AGG":"R",
        "GTT":"V","GTC":"V","GTA":"V","GTG":"V","GCT":"A","GCC":"A","GCA":"A","GCG":"A",
        "GAT":"D","GAC":"D","GAA":"E","GAG":"E","GGT":"G","GGC":"G","GGA":"G","GGG":"G",
    }

    EXAMPLE_DNA = ">example_sequence\nATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"

    def __init__(self, master, app):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        self.mode = tk.StringVar(value="DNA Sequence Analysis")
        self.mutation_rate = tk.StringVar(value="0.05")
        self.last_report = ""
        self._build()
        self.load_example()

    def _build(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Math DNA Lab", style="Header.TLabel").pack(side="left")
        ttk.Label(top, text="DNA'yı algoritma, vektör, k-mer, bilgi ve dijital veri kodlama dili olarak öğretir.", style="Muted.TLabel").pack(side="left", padx=12)

        row = ttk.Frame(self, style="Panel.TFrame")
        row.pack(fill="x", padx=8, pady=4)
        ttk.Label(row, text="Mod:", style="Muted.TLabel").pack(side="left")
        combo = ttk.Combobox(row, textvariable=self.mode, values=[
            "DNA Sequence Analysis",
            "Digital Text → DNA",
            "DNA → Digital Text",
            "Mutation Simulator",
        ], width=26, state="readonly")
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda e: self.on_mode_change())
        RoundedButton(row, text="Dosya Yükle", command=self.load_file).pack(side="left", padx=3)
        RoundedButton(row, text="Seçili Kaynağı Kullan", command=self.use_selected_resource).pack(side="left", padx=3)
        RoundedButton(row, text="Örnek Yükle", command=self.load_example).pack(side="left", padx=3)
        RoundedButton(row, text="Çalıştır", command=self.run).pack(side="left", padx=3)
        RoundedButton(row, text="Rapor Kaydet", command=self.save_report).pack(side="left", padx=3)
        ttk.Label(row, text="Mutasyon oranı:", style="Muted.TLabel").pack(side="left", padx=(16, 3))
        ttk.Entry(row, textvariable=self.mutation_rate, width=7).pack(side="left")

        note = (
            "Bu modül biyoinformatik mantığıyla çalışır: DNA dizisini bilgisayar dilinde string, vektör, k-mer sayım vektörü, "
            "olasılık dağılımı ve bilgi taşıyıcı kod olarak gösterir. Dijital veriyi DNA'ya kodlama bölümü eğitim amaçlıdır; 00=A, 01=C, 10=G, 11=T eşlemesini kullanır."
        )
        tk.Label(self, text=note, justify="left", fg=THEME["muted"], bg=THEME["panel"], wraplength=1180).pack(fill="x", padx=12, pady=(0, 8))

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(body, style="Panel.TFrame")
        right = ttk.Frame(body, style="Panel.TFrame")
        body.add(left, weight=1)
        body.add(right, weight=2)

        ttk.Label(left, text="Girdi", style="Header.TLabel").pack(fill="x", padx=8, pady=(8, 2))
        self.help_label = ttk.Label(left, text="FASTA/DNA dizisi yaz veya dosya yükle.", style="Muted.TLabel")
        self.help_label.pack(fill="x", padx=8, pady=(0, 6))
        self.input_text = tk.Text(left, height=18, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.input_text.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Label(right, text="DNA'nın Matematiğe ve Dijital Veriye Yansıması", style="Header.TLabel").pack(fill="x", padx=8, pady=(8, 2))
        self.output = tk.Text(right, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.output.pack(fill="both", expand=True, padx=8, pady=8)
        self.output.insert("1.0", self.intro_report())

    def intro_report(self):
        return (
            "Math DNA Lab hazır.\n\n"
            "Bu laboratuvarın fikri:\n"
            "DNA bir kod gibi düşünülebilir. Bilgisayar biliminde bu kod; string, vektör, olasılık dağılımı, k-mer frekans vektörü ve bilgi taşıyıcı dizi olarak incelenir.\n\n"
            "Modlar:\n"
            "1. DNA Sequence Analysis: GC oranı, baz sayımı, k-mer vektörü, ters-tamamlayıcı ve protein çevirisi.\n"
            "2. Digital Text → DNA: Metni UTF-8 byte dizisine, byte'ları ikili koda, ikili kodu A/C/G/T dizisine çevirir.\n"
            "3. DNA → Digital Text: 00=A, 01=C, 10=G, 11=T eşlemesiyle kodlanmış DNA'yı tekrar metne çevirir.\n"
            "4. Mutation Simulator: DNA dizisinde basit rastgele baz değişimi simülasyonu yapar.\n"
        )

    def on_mode_change(self):
        mode = self.mode.get()
        if mode == "Digital Text → DNA":
            self.help_label.config(text="Kodlanacak dijital metni yaz. Örnek: Hello Math DNA")
        elif mode == "DNA → Digital Text":
            self.help_label.config(text="Daha önce üretilmiş DNA_CODE dizisini veya A/C/G/T kodunu yapıştır.")
        elif mode == "Mutation Simulator":
            self.help_label.config(text="Mutasyon simülasyonu için DNA/FASTA dizisi yaz. Mutasyon oranı 0.01 - 0.10 gibi girilebilir.")
        else:
            self.help_label.config(text="FASTA/DNA dizisi yaz veya dosya yükle.")

    def load_example(self):
        self.input_text.delete("1.0", "end")
        if self.mode.get() == "Digital Text → DNA":
            self.input_text.insert("1.0", "DNA bir koddur. Matematik onu sayılara, vektörlere ve bilgiye çevirir.")
        elif self.mode.get() == "DNA → Digital Text":
            self.input_text.insert("1.0", "DNA_CODE: " + self.text_to_dna_code("Hello DNA"))
        else:
            self.input_text.insert("1.0", self.EXAMPLE_DNA)

    def load_file(self):
        path = filedialog.askopenfilename(
            title="Math DNA Lab için dosya seç",
            filetypes=[("DNA/Text", "*.fa;*.fasta;*.fna;*.dna;*.txt;*.md"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = Path(path).read_text(encoding="utf-8", errors="ignore")
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", data)
        except Exception as exc:
            messagebox.showerror("Dosya okuma hatası", str(exc))

    def use_selected_resource(self):
        if not self.app.selected_path:
            messagebox.showinfo("Kaynak seçilmedi", "Soldaki Course Resources listesinden bir FASTA/TXT/DNA dosyası seç.")
            return
        p = Path(self.app.selected_path)
        if p.is_dir():
            messagebox.showinfo("Dosya gerekli", "Bir klasör değil, DNA/metin dosyası seç.")
            return
        try:
            data = p.read_text(encoding="utf-8", errors="ignore")
            self.input_text.delete("1.0", "end")
            self.input_text.insert("1.0", data)
        except Exception as exc:
            messagebox.showerror("Kaynak okuma hatası", str(exc))

    def run(self):
        raw = self.input_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showinfo("Girdi yok", "Önce DNA dizisi veya dijital metin gir.")
            return
        mode = self.mode.get()
        try:
            if mode == "Digital Text → DNA":
                report = self.encode_text_report(raw)
            elif mode == "DNA → Digital Text":
                report = self.decode_dna_report(raw)
            elif mode == "Mutation Simulator":
                report = self.mutation_report(raw)
            else:
                report = self.sequence_analysis_report(raw)
            self.last_report = report
            self.output.delete("1.0", "end")
            self.output.insert("1.0", report)
        except Exception as exc:
            messagebox.showerror("Math DNA Lab Hatası", str(exc))

    def parse_fasta_sequences(self, raw):
        sequences = []
        current = []
        has_header = False
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                has_header = True
                if current:
                    sequences.append(self.clean_sequence("".join(current)))
                    current = []
            else:
                current.append(line)
        if current:
            sequences.append(self.clean_sequence("".join(current)))
        if not has_header and not sequences:
            sequences = [self.clean_sequence(raw)]
        if not has_header:
            sequences = [self.clean_sequence(raw)]
        return [s for s in sequences if s]

    def clean_sequence(self, raw):
        return "".join(ch for ch in raw.upper().replace("U", "T") if ch in "ACGT")

    def reverse_complement(self, seq):
        return seq.translate(self.COMPLEMENT)[::-1].upper().replace("U", "T")

    def kmer_counts(self, seq, k=3):
        counts = Counter(seq[i:i+k] for i in range(0, max(0, len(seq)-k+1)) if len(seq[i:i+k]) == k)
        return counts

    def shannon_entropy(self, seq):
        n = len(seq)
        if n == 0:
            return 0.0
        ent = 0.0
        for base in self.BASES:
            p = seq.count(base) / n
            if p > 0:
                ent -= p * math.log2(p)
        return ent

    def translate_frame(self, seq, limit_codons=60):
        aas = []
        for i in range(0, min(len(seq)-2, limit_codons*3), 3):
            codon = seq[i:i+3]
            aas.append(self.CODON_TABLE.get(codon, "?"))
        return "".join(aas)

    def hamming_distance(self, a, b):
        if len(a) != len(b):
            return None
        return sum(x != y for x, y in zip(a, b))

    def levenshtein_distance(self, a, b, max_len=300):
        a, b = a[:max_len], b[:max_len]
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            curr = [i]
            for j, cb in enumerate(b, 1):
                curr.append(min(prev[j] + 1, curr[j-1] + 1, prev[j-1] + (ca != cb)))
            prev = curr
        return prev[-1]

    def sequence_analysis_report(self, raw):
        seqs = self.parse_fasta_sequences(raw)
        if not seqs:
            raise ValueError("Geçerli DNA harfi bulunamadı. A, C, G, T içeren bir dizi gir.")
        seq = seqs[0]
        n = len(seq)
        counts = Counter(seq)
        gc = (counts["G"] + counts["C"]) / n if n else 0
        at = (counts["A"] + counts["T"]) / n if n else 0
        entropy = self.shannon_entropy(seq)
        k2 = self.kmer_counts(seq, 2)
        k3 = self.kmer_counts(seq, 3)
        top2 = ", ".join(f"{k}:{v}" for k, v in k2.most_common(8))
        top3 = ", ".join(f"{k}:{v}" for k, v in k3.most_common(10))
        rc = self.reverse_complement(seq)
        protein = self.translate_frame(seq)
        start_count = sum(1 for i in range(len(seq)-2) if seq[i:i+3] == "ATG")
        stop_count = sum(1 for i in range(len(seq)-2) if seq[i:i+3] in {"TAA", "TAG", "TGA"})
        lines = []
        lines.append("MATH DNA LAB - DNA SEQUENCE ANALYSIS\n")
        lines.append("="*72 + "\n\n")
        lines.append("1. DNA neden matematiksel bir nesnedir?\n")
        lines.append("DNA dizisi sembolik bir dizidir: s = (s_1, s_2, ..., s_N), s_i ∈ {A,C,G,T}.\n")
        lines.append("Bilgisayarda bu, önce string olarak tutulur; sonra sayım vektörü, olasılık dağılımı veya k-mer vektörüne çevrilir.\n\n")
        lines.append("2. Temel ölçümler\n")
        lines.append(f"Uzunluk N: {n}\n")
        lines.append(f"Baz sayımları: A={counts['A']}, C={counts['C']}, G={counts['G']}, T={counts['T']}\n")
        lines.append(f"GC oranı: {gc:.4f} = %{gc*100:.2f}\n")
        lines.append(f"AT oranı: {at:.4f} = %{at*100:.2f}\n")
        lines.append(f"Shannon bilgi entropisi: H={entropy:.4f} bit/baz\n\n")
        lines.append("3. LaTeX formüller\n")
        lines.append("GC oranı:\nLaTeX: GC(s)=\\\frac{\\#G + \\#C}{N}\n")
        lines.append("k-mer vektörü:\nLaTeX: \\phi_k(s) = (c_w)_{w \\in \\{A,C,G,T\\}^k}\n")
        lines.append("Entropi:\nLaTeX: H(s)=-\\\sum_{b\\in\\{A,C,G,T\\}} p_b\\log_2(p_b)\n\n")
        lines.append("4. k-mer frekans vektörü\n")
        lines.append(f"En sık 2-mer değerleri: {top2 or 'yok'}\n")
        lines.append(f"En sık 3-mer değerleri: {top3 or 'yok'}\n")
        lines.append("Anlamı: k-mer vektörü DNA'yı makine öğrenmesi için sayısal özellik vektörüne dönüştürür. Örneğin 3-mer için teorik uzay boyutu 4^3 = 64'tür.\n\n")
        lines.append("5. Ters-tamamlayıcı ve biyolojik algoritma mantığı\n")
        lines.append(f"Reverse complement ilk 120 baz: {rc[:120]}{'...' if len(rc)>120 else ''}\n")
        lines.append("LaTeX: rc(s)=reverse(complement(s)), complement(A)=T, complement(C)=G\n\n")
        lines.append("6. Kodon/protein çevirisi fikri\n")
        lines.append(f"Başlangıç kodonu ATG sayısı: {start_count}\n")
        lines.append(f"Stop kodon sayısı: {stop_count}\n")
        lines.append(f"1. okuma çerçevesi protein önizlemesi: {protein}{'...' if len(seq)>180 else ''}\n")
        lines.append("LaTeX: codon_i = (s_{3i}, s_{3i+1}, s_{3i+2})\n")
        lines.append("Anlamı: 3 bazlık gruplar amino asit sembollerine çevrilir. Bu, DNA'nın algoritmik kod gibi okunmasının temel örneğidir.\n\n")
        lines.append("7. Matematiksel uzay tanımı\n")
        lines.append("DNA ham hâlde sembolik diziler uzayındadır: {A,C,G,T}^N.\n")
        lines.append("Sayım yapınca R^4 vektörüne, k-mer çıkarınca R^{4^k} özellik vektörüne, embedding kullanınca R^d öğrenilmiş vektör uzayına taşınır.\n\n")
        if len(seqs) >= 2:
            a, b = seqs[0], seqs[1]
            hd = self.hamming_distance(a, b)
            lev = self.levenshtein_distance(a, b)
            lines.append("8. İki dizi karşılaştırması\n")
            if hd is None:
                lines.append("Hamming mesafesi: Diziler aynı uzunlukta olmadığı için uygulanmadı.\n")
            else:
                lines.append(f"Hamming mesafesi: {hd}\n")
            lines.append(f"Levenshtein/edit mesafesi ilk 300 baz için: {lev}\n")
            lines.append("LaTeX: d_H(x,y)=\\\sum_i 1[x_i \\ne y_i]\n")
        return "".join(lines)

    def text_to_dna_code(self, text):
        data = text.encode("utf-8")
        bases = []
        for byte in data:
            bits = format(byte, "08b")
            for i in range(0, 8, 2):
                bases.append(self.BIT_TO_BASE[bits[i:i+2]])
        return "".join(bases)

    def dna_code_to_text(self, dna):
        seq = self.extract_dna_code(dna)
        if len(seq) % 4 != 0:
            raise ValueError(f"DNA kod uzunluğu 4'ün katı olmalı. Şu an uzunluk: {len(seq)}")
        bits = "".join(self.BASE_TO_BIT[b] for b in seq)
        by = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
        return by.decode("utf-8", errors="replace"), seq

    def extract_dna_code(self, raw):
        m = re.search(r"DNA_CODE\s*:\s*([ACGTacgt\s]+)", raw)
        if m:
            return self.clean_sequence(m.group(1))
        return self.clean_sequence(raw)

    def encode_text_report(self, raw):
        dna = self.text_to_dna_code(raw)
        n_bytes = len(raw.encode("utf-8"))
        gc = (dna.count("G") + dna.count("C")) / len(dna) if dna else 0
        lines = []
        lines.append("MATH DNA LAB - DIGITAL TEXT TO DNA\n")
        lines.append("="*72 + "\n\n")
        lines.append("1. Dijital veri nasıl DNA'ya kodlanır?\n")
        lines.append("Bilgisayarda metin UTF-8 byte dizisine çevrilir. Her byte 8 bittir. DNA'da 4 harf olduğu için her baz 2 bit bilgi taşır.\n\n")
        lines.append("2. Kodlama eşlemesi\n")
        lines.append("00 → A\n01 → C\n10 → G\n11 → T\n\n")
        lines.append("LaTeX: f:\\{0,1\\}^2 \\rightarrow \\{A,C,G,T\\}\n")
        lines.append("LaTeX: 1\\ byte = 8\\ bit = 4\\ DNA\\ bases\n\n")
        lines.append(f"Metin byte uzunluğu: {n_bytes}\n")
        lines.append(f"Üretilen DNA baz uzunluğu: {len(dna)}\n")
        lines.append(f"GC oranı: %{gc*100:.2f}\n\n")
        lines.append("3. DNA kodu\n")
        lines.append("DNA_CODE: " + dna + "\n\n")
        lines.append("4. Eğitimci açıklaması\n")
        lines.append("Bu işlem biyoinformatikteki temel fikri gösterir: Anlamlı bilgi, sembollere; semboller de matematiksel kodlara çevrilebilir. Burada DNA biyolojik bir molekül olarak değil, A/C/G/T alfabeli dijital bir depolama dili olarak modellenir.\n\n")
        lines.append("5. Matematiksel uzay tanımı\n")
        lines.append("Dijital metin önce {0,1}^M ikili uzayına, sonra {A,C,G,T}^{M/2} sembolik DNA uzayına taşınır. Sayısallaştırılırsa R^N vektörü veya k-mer özellik uzayı olarak makine öğrenmesine verilebilir.\n")
        return "".join(lines)

    def decode_dna_report(self, raw):
        text, seq = self.dna_code_to_text(raw)
        lines = []
        lines.append("MATH DNA LAB - DNA TO DIGITAL TEXT\n")
        lines.append("="*72 + "\n\n")
        lines.append("1. DNA kodu tekrar dijital veriye nasıl döner?\n")
        lines.append("Her baz önce 2 bite çevrilir; 4 baz = 8 bit = 1 byte olur. Byte dizisi UTF-8 olarak okununca metin geri gelir.\n\n")
        lines.append("LaTeX: g:\\{A,C,G,T\\} \\rightarrow \\{0,1\\}^2\n")
        lines.append("LaTeX: byte_i = (b_{4i}, b_{4i+1}, b_{4i+2}, b_{4i+3})\n\n")
        lines.append(f"Okunan DNA baz uzunluğu: {len(seq)}\n")
        lines.append(f"Çözülen byte sayısı: {len(seq)//4}\n\n")
        lines.append("ÇÖZÜLEN METİN:\n")
        lines.append(text + "\n\n")
        lines.append("Matematiksel anlam: Bu, sembolik DNA uzayından ikili sayı uzayına geri dönüş fonksiyonudur.\n")
        return "".join(lines)

    def mutation_report(self, raw):
        seqs = self.parse_fasta_sequences(raw)
        if not seqs:
            raise ValueError("Mutasyon için A/C/G/T içeren DNA dizisi gerekli.")
        seq = seqs[0]
        try:
            rate = float(self.mutation_rate.get().replace(",", "."))
        except Exception:
            rate = 0.05
        rate = max(0.0, min(1.0, rate))
        mutated = []
        changes = []
        for i, b in enumerate(seq):
            if random.random() < rate:
                choices = [x for x in self.BASES if x != b]
                nb = random.choice(choices)
                mutated.append(nb)
                changes.append((i+1, b, nb))
            else:
                mutated.append(b)
        mutated = "".join(mutated)
        hd = self.hamming_distance(seq, mutated)
        lines = []
        lines.append("MATH DNA LAB - MUTATION SIMULATOR\n")
        lines.append("="*72 + "\n\n")
        lines.append("1. Basit mutasyon modeli\n")
        lines.append("Bu simülasyon her baz için p olasılıkla rastgele başka bir baza dönüşüm uygular.\n")
        lines.append("LaTeX: P(s_i' \\ne s_i)=p\n")
        lines.append("LaTeX: d_H(s,s')=\\\sum_i 1[s_i \\ne s_i']\n\n")
        lines.append(f"Dizi uzunluğu: {len(seq)}\n")
        lines.append(f"Mutasyon oranı p: {rate}\n")
        lines.append(f"Gerçekleşen değişim sayısı: {len(changes)}\n")
        lines.append(f"Hamming mesafesi: {hd}\n\n")
        lines.append("2. Değişen ilk pozisyonlar\n")
        if changes:
            lines.append(", ".join(f"{pos}:{old}->{new}" for pos, old, new in changes[:30]) + ("..." if len(changes) > 30 else "") + "\n\n")
        else:
            lines.append("Bu çalıştırmada mutasyon oluşmadı. Oranı artırıp tekrar deneyebilirsin.\n\n")
        lines.append("3. Mutant dizi\n")
        lines.append(mutated[:1000] + ("..." if len(mutated) > 1000 else "") + "\n\n")
        lines.append("4. Matematiksel uzay tanımı\n")
        lines.append("Mutasyon, {A,C,G,T}^N sembolik uzayında bir noktadan başka bir noktaya geçiştir. Hamming mesafesi bu iki noktanın kaç koordinatta farklı olduğunu ölçer.\n")
        return "".join(lines)

    def save_report(self):
        report = self.output.get("1.0", "end").strip()
        if not report:
            messagebox.showinfo("Rapor yok", "Önce Çalıştır butonuna bas.")
            return
        self.last_report = report
        reports = APP_FOLDER / "Reports"
        reports.mkdir(parents=True, exist_ok=True)
        default_name = reports / f"math_dna_lab_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        out = filedialog.asksaveasfilename(title="Math DNA Lab raporu kaydet", initialfile=default_name.name, initialdir=str(reports), defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not out:
            return
        Path(out).write_text(report, encoding="utf-8")
        messagebox.showinfo("Kaydedildi", out)


class MathQuantumLab(ttk.Frame):
    """Educational quantum-algorithm laboratory.

    This module is a small in-silico learning environment. It does not require
    quantum hardware. It teaches how qubits, gates, amplitudes, measurement,
    entanglement, QFT and Grover-style search are represented with vectors,
    matrices, tensor products and probability distributions.
    """

    MODES = [
        "Concept Library",
        "Single Qubit Playground",
        "Bell Entanglement",
        "Grover Search Toy",
        "Quantum Fourier Transform",
        "Custom Circuit Simulator",
        "Algorithm Roadmap",
    ]

    ALGORITHM_LIBRARY = [
        ("Hadamard / Superposition", "Lineer cebir", "H|0>=(|0>+|1>)/sqrt(2)", "Klasik 0/1 durumundan olasılık genliklerinin üst üste binmesine geçiş."),
        ("Pauli Gates", "2x2 matrisler", "X=[[0,1],[1,0]], Z=[[1,0],[0,-1]]", "Qubit durumunu bit-flip, phase-flip veya ikisini birlikte dönüştürür."),
        ("Phase Gates", "Kompleks düzlem", "R_z(θ)=diag(e^{-iθ/2}, e^{iθ/2})", "Genlik büyüklüğünü değil, faz bilgisini değiştirir."),
        ("CNOT", "Tensör çarpım uzayı", "CNOT|a,b>=|a,a xor b>", "İki qubit arasında koşullu mantık ve dolanıklık kurar."),
        ("Bell State", "Dolanık vektör", "(|00>+|11>)/sqrt(2)", "İki qubit ayrı ayrı değil, ortak bir kuantum durumu olarak davranır."),
        ("Deutsch Algorithm", "Oracle sorgusu", "f(0) xor f(1)", "Tek sorguyla fonksiyonun sabit mi dengeli mi olduğunu sezdirir."),
        ("Deutsch-Jozsa", "Hadamard + oracle", "H^{⊗n} U_f H^{⊗n}|0...0>|1>", "Klasik çoklu sorgu yerine tek kuantum sorgu fikrini öğretir."),
        ("Grover Search", "Genlik yükseltme", "O_s=I-2|s><s|", "Aranan durumun genliğini büyütür; ölçüm olasılığını artırır."),
        ("Quantum Fourier Transform", "Üniter dönüşüm", "QFT|x>=1/sqrt(N) sum_y e^{2πixy/N}|y>", "Periyodik yapıları faz desenlerine çevirir."),
        ("Phase Estimation", "Özdeğer/faz bulma", "U|ψ>=e^{2πiφ}|ψ>", "Bir üniter operatörün fazını tahmin eder."),
        ("Shor Algorithm", "Periyot bulma", "a^r ≡ 1 mod N", "Çarpanlara ayırmayı periyot bulma problemine dönüştürür."),
        ("VQE", "Varyasyonel optimizasyon", "E(θ)=<ψ(θ)|H|ψ(θ)>", "Kuantum devresi + klasik optimizasyon ile düşük enerji durumu arar."),
        ("QAOA", "Optimizasyon", "|γ,β>=U_B(β)U_C(γ)|+>^{⊗n}", "Kombinatoryal optimizasyon için katmanlı kuantum devresi fikri."),
        ("Quantum Walk", "Graf + üniter evrim", "|ψ_{t+1}>=U|ψ_t>", "Klasik rastgele yürüyüşün kuantum genlikli karşılığı."),
        ("Error Correction", "Kod altuzayı", "|0_L>, |1_L>", "Qubit hatalarını ölçmeden koruma fikrini öğretir."),
    ]

    def __init__(self, master, app):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        self.mode = tk.StringVar(value="Concept Library")
        self.qubit_count = tk.IntVar(value=2)
        self.target_item = tk.IntVar(value=3)
        self.last_report = ""
        self._build()

    def _build(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Math Kuantum Lab", style="Header.TLabel").pack(side="left")
        ttk.Label(top, text="Kuantum algoritmalarını vektör, matris, tensör ve olasılık diliyle öğretir.", style="Muted.TLabel").pack(side="left", padx=12)

        row = ttk.Frame(self, style="Panel.TFrame")
        row.pack(fill="x", padx=8, pady=4)
        ttk.Label(row, text="Mod:", style="Muted.TLabel").pack(side="left", padx=(0,4))
        combo = ttk.Combobox(row, textvariable=self.mode, values=self.MODES, state="readonly", width=28)
        combo.pack(side="left", padx=3)
        combo.bind("<<ComboboxSelected>>", lambda e: self.on_mode_change())
        ttk.Label(row, text="Qubit:", style="Muted.TLabel").pack(side="left", padx=(12,4))
        ttk.Spinbox(row, from_=1, to=3, textvariable=self.qubit_count, width=4).pack(side="left", padx=3)
        ttk.Label(row, text="Target:", style="Muted.TLabel").pack(side="left", padx=(12,4))
        ttk.Spinbox(row, from_=0, to=7, textvariable=self.target_item, width=5).pack(side="left", padx=3)
        RoundedButton(row, text="Örnek Yükle", command=self.load_example).pack(side="left", padx=4)
        RoundedButton(row, text="Çalıştır / Anlat", command=self.run).pack(side="left", padx=4)
        RoundedButton(row, text="Rapor Kaydet", command=self.save_report).pack(side="left", padx=4)

        info = (
            "Bu modül eğitim amaçlı küçük bir kuantum devre simülatörü ve algoritma kütüphanesidir. "
            "Kubit durumlarını kompleks vektör, kapıları üniter matris, çoklu kubit sistemlerini tensör çarpımı, "
            "ölçümü ise olasılık dağılımı olarak açıklar."
        )
        tk.Label(self, text=info, justify="left", fg=THEME["muted"], bg=THEME["panel"], wraplength=1180).pack(fill="x", padx=12, pady=(0,8))

        panes = ttk.PanedWindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(panes, style="Panel.TFrame")
        right = ttk.Frame(panes, style="Panel.TFrame")
        panes.add(left, weight=1)
        panes.add(right, weight=2)

        ttk.Label(left, text="Geliştirilebilir Devre Scripti", style="Header.TLabel").pack(fill="x", padx=8, pady=(8,2))
        self.help_label = ttk.Label(left, text="Komutlar: H q, X q, Y q, Z q, S q, T q, RX q theta, RY q theta, RZ q theta, CNOT c t, SWAP a b", style="Muted.TLabel", wraplength=430)
        self.help_label.pack(fill="x", padx=8, pady=(0,6))
        self.input_text = tk.Text(left, height=20, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.input_text.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Label(right, text="Kuantum Algoritmalarının Matematiğe Yansıması", style="Header.TLabel").pack(fill="x", padx=8, pady=(8,2))
        self.output = tk.Text(right, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.output.pack(fill="both", expand=True, padx=8, pady=8)
        self.output.insert("1.0", self.default_intro())
        self.load_example()

    def default_intro(self):
        return (
            "Math Kuantum Lab hazır.\n\n"
            "Amaç:\n"
            "- Kuantum algoritmalarını ezber formül olarak değil, vektör/matris/tensör dönüşümü olarak öğretmek.\n"
            "- Öğrencinin küçük devreler yazarak H, X, Z, CNOT, faz, ölçüm, Bell durumu, Grover ve QFT mantığını geliştirmesini sağlamak.\n\n"
            "Temel matematiksel fikir:\n"
            "- Tek qubit: |ψ> = α|0> + β|1>, |α|^2 + |β|^2 = 1\n"
            "- n qubit: |ψ> ∈ C^{2^n}\n"
            "- Gate: üniter matris U, yeni durum |ψ'> = U|ψ>\n"
            "- Ölçüm: P(x)=|α_x|^2\n\n"
            "Sol tarafa basit devre komutları yazıp Çalıştır / Anlat butonuna basabilirsin."
        )

    def on_mode_change(self):
        mode = self.mode.get()
        if mode == "Single Qubit Playground":
            self.qubit_count.set(1)
            self.help_label.config(text="Tek qubit üzerinde süperpozisyon, faz ve dönüş kapılarını dene.")
        elif mode == "Bell Entanglement":
            self.qubit_count.set(2)
            self.help_label.config(text="H 0 ve CNOT 0 1 ile Bell dolanıklığı oluşturulur.")
        elif mode == "Grover Search Toy":
            self.qubit_count.set(2)
            self.help_label.config(text="2 qubitlik oyuncak Grover araması. Target 0-3 arası seçilebilir.")
        elif mode == "Quantum Fourier Transform":
            self.qubit_count.set(2)
            self.help_label.config(text="QFT, hesaplama tabanındaki bilgiyi faz/frekans desenine çevirir.")
        elif mode == "Custom Circuit Simulator":
            self.help_label.config(text="Komutlar: H q, X q, Y q, Z q, S q, T q, RX q theta, RY q theta, RZ q theta, CNOT c t, SWAP a b")
        else:
            self.help_label.config(text="Algoritma kütüphanesi ve öğrenme yol haritası.")
        self.load_example()

    def load_example(self):
        mode = self.mode.get()
        examples = {
            "Single Qubit Playground": "# Tek qubit süperpozisyon örneği\nH 0\nZ 0\nH 0\n",
            "Bell Entanglement": "# Bell durumu: (|00> + |11>) / sqrt(2)\nH 0\nCNOT 0 1\n",
            "Grover Search Toy": "# Grover Search Toy modunda target alanını kullan.\n# 2 qubit için target 0,1,2,3 olabilir.\n",
            "Quantum Fourier Transform": "# QFT modunda input basis state target alanından alınır.\n# Örnek: target=1 ve qubit=2 için |01> durumuna QFT uygulanır.\n",
            "Custom Circuit Simulator": "# 0. qubit en soldaki / en anlamlı qubit olarak düşünülür.\nH 0\nCNOT 0 1\nZ 1\nH 1\n",
        }
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", examples.get(mode, "# Bu mod açıklama üretir.\n# Çalıştır / Anlat butonuna bas.\n"))

    def run(self):
        try:
            mode = self.mode.get()
            if mode == "Concept Library":
                report = self.concept_library_report()
            elif mode == "Algorithm Roadmap":
                report = self.algorithm_roadmap_report()
            elif mode == "Bell Entanglement":
                report = self.bell_report()
            elif mode == "Grover Search Toy":
                report = self.grover_report()
            elif mode == "Quantum Fourier Transform":
                report = self.qft_report()
            else:
                n = int(self.qubit_count.get())
                n = max(1, min(3, n))
                script = self.input_text.get("1.0", "end")
                report = self.custom_circuit_report(script, n, title="MATH KUANTUM LAB - CUSTOM CIRCUIT" if mode == "Custom Circuit Simulator" else "MATH KUANTUM LAB - SINGLE QUBIT PLAYGROUND")
            self.last_report = report
            self.output.delete("1.0", "end")
            self.output.insert("1.0", report)
        except Exception as exc:
            messagebox.showerror("Math Kuantum Lab Hatası", str(exc))

    def header(self, title):
        return f"{title}\nOluşturulma zamanı: {now_iso()}\n" + "=" * 72 + "\n\n"

    def concept_library_report(self):
        lines = [self.header("MATH KUANTUM LAB - CONCEPT LIBRARY")]
        lines.append("1. Qubit nedir?\n")
        lines.append("Klasik bit 0 veya 1 değerindedir. Qubit ise iki baz durumunun kompleks katsayılı birleşimidir.\n")
        lines.append("LaTeX: |ψ\\rangle = α|0\\rangle + β|1\\rangle,\\quad |α|^2 + |β|^2 = 1\n")
        lines.append("Anlamı: α ve β doğrudan olasılık değildir; olasılık genliğidir. Ölçümde |0> için |α|^2, |1> için |β|^2 olasılığı çıkar.\n\n")
        lines.append("2. Gate nedir?\n")
        lines.append("Kuantum kapısı, durum vektörüne uygulanan üniter bir matristir.\n")
        lines.append("LaTeX: |ψ'\\rangle = U|ψ\\rangle,\\quad U^†U=I\n")
        lines.append("Anlamı: Üniterlik toplam olasılığın 1 kalmasını sağlar.\n\n")
        lines.append("3. Çoklu qubit uzayı\n")
        lines.append("LaTeX: |ψ\\rangle ∈ C^{2^n}\n")
        lines.append("Anlamı: n qubitlik sistem 2^n boyutlu kompleks vektör uzayında temsil edilir. 3 qubit için 8 genlik vardır.\n\n")
        lines.append("4. Dolanıklık\n")
        lines.append("LaTeX: |Φ^+\\rangle = (|00\\rangle + |11\\rangle)/\\\sqrt{2}\n")
        lines.append("Anlamı: Bu durum iki ayrı tek-qubit vektörünün basit çarpımı olarak yazılamaz; sistem bir bütün olarak düşünülür.\n\n")
        lines.append("5. Ölçüm\n")
        lines.append("LaTeX: P(x)=|α_x|^2\n")
        lines.append("Anlamı: Simülatör her basis state için ölçüm olasılığını hesaplar.\n\n")
        lines.append("Kullanım önerisi: Önce Single Qubit Playground, sonra Bell Entanglement, sonra Grover ve QFT modlarını dene.\n")
        return "".join(lines)

    def algorithm_roadmap_report(self):
        lines = [self.header("MATH KUANTUM LAB - ALGORITHM ROADMAP")]
        lines.append("Bu bölüm kuantum algoritmalarını öğrenme ve geliştirme yol haritasıdır. Her algoritma bir matematiksel yapıya bağlanır.\n\n")
        for i, (name, structure, formula, meaning) in enumerate(self.ALGORITHM_LIBRARY, 1):
            lines.append(f"{i}. {name}\n")
            lines.append(f"   Matematiksel yapı: {structure}\n")
            lines.append(f"   Formül: {formula}\n")
            lines.append(f"   Eğitimci açıklaması: {meaning}\n")
            lines.append("   Geliştirme görevi: Bu algoritma için küçük bir devre örneği yaz, state vector sonucunu incele, sonra ölçüm olasılıklarını yorumla.\n\n")
        lines.append("Program içi geliştirme sistemi önerisi:\n")
        lines.append("- Algoritma Kartı: amaç, formül, devre, örnek çıktı.\n")
        lines.append("- Devre Scripti: kullanıcı H/X/Z/CNOT gibi kapılarla algoritmayı değiştirir.\n")
        lines.append("- State Vector İncelemesi: her basis state için kompleks genlik ve olasılık gösterilir.\n")
        lines.append("- Görevler: 'Bell oluştur', 'fazı değiştir', 'Grover target seç', 'QFT faz desenini açıkla'.\n")
        return "".join(lines)

    def zero_state(self, n):
        state = [0j] * (2 ** n)
        state[0] = 1 + 0j
        return state

    def basis_state(self, n, index):
        size = 2 ** n
        index = max(0, min(size - 1, int(index)))
        state = [0j] * size
        state[index] = 1 + 0j
        return state

    def apply_single_gate(self, state, n, q, gate):
        q = int(q)
        if q < 0 or q >= n:
            raise ValueError(f"Qubit index geçersiz: {q}. Geçerli aralık: 0-{n-1}")
        mask = 1 << (n - 1 - q)
        new = state[:]
        g00, g01 = gate[0]
        g10, g11 = gate[1]
        for i in range(len(state)):
            if (i & mask) == 0:
                j = i | mask
                a0, a1 = state[i], state[j]
                new[i] = g00 * a0 + g01 * a1
                new[j] = g10 * a0 + g11 * a1
        return new

    def apply_cnot(self, state, n, control, target):
        control, target = int(control), int(target)
        if control == target:
            raise ValueError("CNOT için control ve target farklı olmalı.")
        if control < 0 or control >= n or target < 0 or target >= n:
            raise ValueError("CNOT qubit index aralığı dışında.")
        cmask = 1 << (n - 1 - control)
        tmask = 1 << (n - 1 - target)
        new = [0j] * len(state)
        for i, amp in enumerate(state):
            j = i ^ tmask if (i & cmask) else i
            new[j] += amp
        return new

    def apply_swap(self, state, n, a, b):
        a, b = int(a), int(b)
        if a == b:
            return state
        if a < 0 or a >= n or b < 0 or b >= n:
            raise ValueError("SWAP qubit index aralığı dışında.")
        amask = 1 << (n - 1 - a)
        bmask = 1 << (n - 1 - b)
        new = [0j] * len(state)
        for i, amp in enumerate(state):
            abit = bool(i & amask)
            bbit = bool(i & bmask)
            j = i
            if abit != bbit:
                j ^= amask
                j ^= bmask
            new[j] += amp
        return new

    def gate_matrix(self, name, theta=None):
        name = name.upper()
        s = 1 / math.sqrt(2)
        if name == "H":
            return [[s, s], [s, -s]]
        if name == "X":
            return [[0, 1], [1, 0]]
        if name == "Y":
            return [[0, -1j], [1j, 0]]
        if name == "Z":
            return [[1, 0], [0, -1]]
        if name == "S":
            return [[1, 0], [0, 1j]]
        if name == "T":
            return [[1, 0], [0, complex(math.cos(math.pi/4), math.sin(math.pi/4))]]
        if name in {"RX", "RY", "RZ"}:
            if theta is None:
                raise ValueError(f"{name} için açı gerekli. Örnek: {name} 0 1.5708")
            th = float(theta)
            c = math.cos(th/2)
            s2 = math.sin(th/2)
            if name == "RX":
                return [[c, -1j*s2], [-1j*s2, c]]
            if name == "RY":
                return [[c, -s2], [s2, c]]
            if name == "RZ":
                return [[complex(math.cos(-th/2), math.sin(-th/2)), 0], [0, complex(math.cos(th/2), math.sin(th/2))]]
        raise ValueError(f"Bilinmeyen gate: {name}")

    def simulate_circuit(self, script, n):
        state = self.zero_state(n)
        steps = []
        for raw in script.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.replace(",", " ").split()
            cmd = parts[0].upper()
            if cmd in {"H", "X", "Y", "Z", "S", "T"}:
                if len(parts) < 2:
                    raise ValueError(f"{cmd} için qubit index gerekli.")
                q = int(parts[1])
                state = self.apply_single_gate(state, n, q, self.gate_matrix(cmd))
                steps.append(f"{cmd} gate applied to qubit {q}")
            elif cmd in {"RX", "RY", "RZ"}:
                if len(parts) < 3:
                    raise ValueError(f"{cmd} için qubit ve theta gerekli. Örnek: {cmd} 0 1.5708")
                q = int(parts[1])
                theta = float(parts[2])
                state = self.apply_single_gate(state, n, q, self.gate_matrix(cmd, theta))
                steps.append(f"{cmd}({theta}) gate applied to qubit {q}")
            elif cmd in {"CNOT", "CX"}:
                if len(parts) < 3:
                    raise ValueError("CNOT için control ve target gerekli. Örnek: CNOT 0 1")
                state = self.apply_cnot(state, n, int(parts[1]), int(parts[2]))
                steps.append(f"CNOT applied: control {parts[1]}, target {parts[2]}")
            elif cmd == "SWAP":
                if len(parts) < 3:
                    raise ValueError("SWAP için iki qubit gerekli. Örnek: SWAP 0 1")
                state = self.apply_swap(state, n, int(parts[1]), int(parts[2]))
                steps.append(f"SWAP applied: qubit {parts[1]} <-> {parts[2]}")
            elif cmd in {"MEASURE", "M"}:
                steps.append("MEASURE: simülatör olasılıkları raporlar; rastgele tek ölçüm yapmaz.")
            else:
                raise ValueError(f"Bilinmeyen komut: {cmd}")
        return state, steps

    def fmt_complex(self, z):
        a = z.real
        b = z.imag
        if abs(a) < 1e-10: a = 0.0
        if abs(b) < 1e-10: b = 0.0
        if b == 0:
            return f"{a:.4f}"
        if a == 0:
            return f"{b:.4f}i"
        sign = "+" if b >= 0 else "-"
        return f"{a:.4f}{sign}{abs(b):.4f}i"

    def basis_label(self, index, n):
        return "|" + format(index, f"0{n}b") + ">"

    def state_vector_report(self, state, n):
        lines = []
        lines.append("State vector sonucu:\n")
        for i, amp in enumerate(state):
            prob = abs(amp) ** 2
            if prob > 1e-8 or abs(amp) > 1e-8:
                lines.append(f"  {self.basis_label(i,n)} : amplitude={self.fmt_complex(amp)}, P={prob:.4f}\n")
        total = sum(abs(a) ** 2 for a in state)
        lines.append(f"Toplam olasılık: {total:.6f}\n\n")
        lines.append("Ölçüm dağılımı:\n")
        for i, amp in enumerate(state):
            prob = abs(amp) ** 2
            if prob > 1e-6:
                bars = "█" * max(1, int(prob * 30))
                lines.append(f"  {self.basis_label(i,n)} {prob*100:6.2f}% {bars}\n")
        return "".join(lines)

    def custom_circuit_report(self, script, n, title):
        state, steps = self.simulate_circuit(script, n)
        lines = [self.header(title)]
        lines.append(f"Qubit sayısı: {n}\n")
        lines.append(f"Matematiksel uzay: C^{{2^{n}}} = C^{2**n}\n\n")
        lines.append("1. Kullanılan devre\n")
        lines.append(script.strip() + "\n\n")
        lines.append("2. Adım adım uygulanan işlemler\n")
        if steps:
            for i, st in enumerate(steps, 1):
                lines.append(f"   {i}. {st}\n")
        else:
            lines.append("   Devre komutu yok. Başlangıç durumu |0...0> kaldı.\n")
        lines.append("\n3. Matematiksel formül\n")
        lines.append("LaTeX: |ψ_{out}\\rangle = U_k U_{k-1} ... U_1 |0...0\\rangle\n")
        lines.append("Anlamı: Yazdığın her gate bir matris dönüşümüdür; devre soldan sağa değil, durum vektörüne sırayla uygulanır.\n\n")
        lines.append("4. Sonuç\n")
        lines.append(self.state_vector_report(state, n))
        lines.append("5. Geliştirme görevi\n")
        lines.append("Bir H gate ekleyerek süperpozisyonu, CNOT ekleyerek dolanıklığı, Z/RZ ekleyerek faz etkisini gözlemle.\n")
        return "".join(lines)

    def bell_report(self):
        n = 2
        script = "H 0\nCNOT 0 1\n"
        state, steps = self.simulate_circuit(script, n)
        lines = [self.header("MATH KUANTUM LAB - BELL ENTANGLEMENT")]
        lines.append("Amaç: İki qubit arasında dolanıklık oluşumunu göstermek.\n\n")
        lines.append("Devre:\nH 0\nCNOT 0 1\n\n")
        lines.append("LaTeX: |00\\rangle \\xrightarrow{H_0} (|00\\rangle+|10\\rangle)/\\\sqrt{2} \\xrightarrow{CNOT} (|00\\rangle+|11\\rangle)/\\\sqrt{2}\n\n")
        lines.append("Eğitici açıklama: İlk qubit süperpozisyona alınır. CNOT, ilk qubit 1 olduğunda ikinci qubit'i çevirir. Sonuçta |00> ve |11> birlikte görünür; sistem ayrı ayrı iki qubit gibi değil, ortak bir vektör gibi davranır.\n\n")
        lines.append(self.state_vector_report(state, n))
        lines.append("Matematiksel uzay: C^4. Bell durumu bu uzayda ayrıştırılamayan özel bir vektördür.\n")
        return "".join(lines)

    def grover_report(self):
        n = 2
        N = 4
        target = max(0, min(3, int(self.target_item.get())))
        state = [1 / math.sqrt(N)] * N
        # Oracle: mark target by phase flip.
        state[target] *= -1
        # Diffusion: reflection around mean.
        mean = sum(state) / N
        state = [2 * mean - a for a in state]
        state = [complex(a, 0) for a in state]
        lines = [self.header("MATH KUANTUM LAB - GROVER SEARCH TOY")]
        lines.append(f"Oyuncak problem: 4 elemanlı aramada hedef durum {self.basis_label(target,n)}.\n\n")
        lines.append("1. Matematiksel fikir\n")
        lines.append("Klasik aramada hedefi bulmak için ortalama daha çok deneme gerekebilir. Grover fikri, hedefin genliğini oracle + diffusion adımlarıyla büyütür.\n\n")
        lines.append("LaTeX: |s\\rangle = \\\frac{1}{\\\sqrt{N}}\\\sum_x |x\\rangle\n")
        lines.append("LaTeX: O_t|x\\rangle = -|x\\rangle \\quad x=t,\\quad O_t|x\\rangle=|x\\rangle \\quad x\\ne t\n")
        lines.append("LaTeX: D = 2|s\\rangle\\\langle s| - I\n\n")
        lines.append("2. Eğitimci açıklaması\n")
        lines.append("Oracle hedef duruma eksi faz verir. Diffusion adımı genlikleri ortalama etrafında yansıtır. 4 elemanlı bu basit örnekte tek iterasyon hedef olasılığını çok güçlü biçimde artırır.\n\n")
        lines.append("3. Sonuç\n")
        lines.append(self.state_vector_report(state, n))
        lines.append("Geliştirme görevi: Target değerini 0,1,2,3 olarak değiştir; hangi basis state'in olasılığının yükseldiğini gözlemle.\n")
        return "".join(lines)

    def qft_report(self):
        n = max(1, min(3, int(self.qubit_count.get())))
        N = 2 ** n
        x = max(0, min(N - 1, int(self.target_item.get())))
        state = []
        for y in range(N):
            angle = 2 * math.pi * x * y / N
            state.append(complex(math.cos(angle), math.sin(angle)) / math.sqrt(N))
        lines = [self.header("MATH KUANTUM LAB - QUANTUM FOURIER TRANSFORM")]
        lines.append(f"Girdi basis state: {self.basis_label(x,n)}\n")
        lines.append(f"Qubit sayısı: {n}, uzay boyutu: {N}\n\n")
        lines.append("1. Matematiksel formül\n")
        lines.append("LaTeX: QFT|x\\rangle = \\\frac{1}{\\\sqrt{N}}\\\sum_{y=0}^{N-1} e^{2\\pi ixy/N}|y\\rangle\n\n")
        lines.append("2. Eğitimci açıklama\n")
        lines.append("Klasik Fourier dönüşümü bir sinyali frekans bileşenlerine ayırır. QFT de basis durumunu kompleks faz desenine çevirir. Olasılıklar eşit görünebilir; asıl bilgi fazlardadır.\n\n")
        lines.append("3. Sonuç\n")
        lines.append(self.state_vector_report(state, n))
        lines.append("Geliştirme görevi: Target değerini değiştir. Olasılıkların çoğu zaman aynı kaldığını, fakat kompleks fazların değiştiğini gözlemle.\n")
        return "".join(lines)

    def save_report(self):
        report = self.output.get("1.0", "end").strip()
        if not report:
            messagebox.showinfo("Rapor yok", "Önce Çalıştır / Anlat butonuna bas.")
            return
        self.last_report = report
        reports = APP_FOLDER / "Reports"
        reports.mkdir(parents=True, exist_ok=True)
        default_name = reports / f"math_kuantum_lab_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        out = filedialog.asksaveasfilename(title="Math Kuantum Lab raporu kaydet", initialfile=default_name.name, initialdir=str(reports), defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not out:
            return
        Path(out).write_text(report, encoding="utf-8")
        messagebox.showinfo("Kaydedildi", out)


class ChemistryMathLab(ttk.Frame):
    """Chemistry-to-math educational module with extra chemistry tools."""

    DEFAULTS = {
        "İdeal gaz yasası": "P=1\nV=22.4\nn=1\nR=0.082057\nT=273.15",
        "Reaksiyon hız yasası": "k=0.12\nA=0.50\nm=1",
        "Asitlik ve pH": "H=0.001",
        "Birinci dereceden bozunma": "C0=2.0\nk=0.35\nt=4",
        "Difüzyon akısı": "D=1.2e-9\ndc_dx=-250",
        "Henderson-Hasselbalch tamponu": "pKa=4.76\nbase=0.20\nacid=0.10",
    }

    PERIODIC_TABLE = {
        'H': {'name': 'Hydrogen', 'tr_name': 'Hidrojen', 'number': 1, 'mass': 1.008, 'group': 1, 'period': 1, 'type': 'Nonmetal'},
        'He': {'name': 'Helium', 'tr_name': 'Helyum', 'number': 2, 'mass': 4.0026, 'group': 18, 'period': 1, 'type': 'Noble Gas'},
        'Li': {'name': 'Lithium', 'tr_name': 'Lityum', 'number': 3, 'mass': 6.94, 'group': 1, 'period': 2, 'type': 'Alkali Metal'},
        'Be': {'name': 'Beryllium', 'tr_name': 'Berilyum', 'number': 4, 'mass': 9.0122, 'group': 2, 'period': 2, 'type': 'Alkaline Earth Metal'},
        'B': {'name': 'Boron', 'tr_name': 'Bor', 'number': 5, 'mass': 10.81, 'group': 13, 'period': 2, 'type': 'Metalloid'},
        'C': {'name': 'Carbon', 'tr_name': 'Karbon', 'number': 6, 'mass': 12.011, 'group': 14, 'period': 2, 'type': 'Nonmetal'},
        'N': {'name': 'Nitrogen', 'tr_name': 'Azot', 'number': 7, 'mass': 14.007, 'group': 15, 'period': 2, 'type': 'Nonmetal'},
        'O': {'name': 'Oxygen', 'tr_name': 'Oksijen', 'number': 8, 'mass': 15.999, 'group': 16, 'period': 2, 'type': 'Nonmetal'},
        'F': {'name': 'Fluorine', 'tr_name': 'Flor', 'number': 9, 'mass': 18.998, 'group': 17, 'period': 2, 'type': 'Halogen'},
        'Ne': {'name': 'Neon', 'tr_name': 'Neon', 'number': 10, 'mass': 20.180, 'group': 18, 'period': 2, 'type': 'Noble Gas'},
        'Na': {'name': 'Sodium', 'tr_name': 'Sodyum', 'number': 11, 'mass': 22.990, 'group': 1, 'period': 3, 'type': 'Alkali Metal'},
        'Mg': {'name': 'Magnesium', 'tr_name': 'Magnezyum', 'number': 12, 'mass': 24.305, 'group': 2, 'period': 3, 'type': 'Alkaline Earth Metal'},
        'Al': {'name': 'Aluminium', 'tr_name': 'Alüminyum', 'number': 13, 'mass': 26.982, 'group': 13, 'period': 3, 'type': 'Post-transition Metal'},
        'Si': {'name': 'Silicon', 'tr_name': 'Silisyum', 'number': 14, 'mass': 28.085, 'group': 14, 'period': 3, 'type': 'Metalloid'},
        'P': {'name': 'Phosphorus', 'tr_name': 'Fosfor', 'number': 15, 'mass': 30.974, 'group': 15, 'period': 3, 'type': 'Nonmetal'},
        'S': {'name': 'Sulfur', 'tr_name': 'Kükürt', 'number': 16, 'mass': 32.06, 'group': 16, 'period': 3, 'type': 'Nonmetal'},
        'Cl': {'name': 'Chlorine', 'tr_name': 'Klor', 'number': 17, 'mass': 35.45, 'group': 17, 'period': 3, 'type': 'Halogen'},
        'Ar': {'name': 'Argon', 'tr_name': 'Argon', 'number': 18, 'mass': 39.948, 'group': 18, 'period': 3, 'type': 'Noble Gas'},
        'K': {'name': 'Potassium', 'tr_name': 'Potasyum', 'number': 19, 'mass': 39.098, 'group': 1, 'period': 4, 'type': 'Alkali Metal'},
        'Ca': {'name': 'Calcium', 'tr_name': 'Kalsiyum', 'number': 20, 'mass': 40.078, 'group': 2, 'period': 4, 'type': 'Alkaline Earth Metal'},
        'Cr': {'name': 'Chromium', 'tr_name': 'Krom', 'number': 24, 'mass': 51.996, 'group': 6, 'period': 4, 'type': 'Transition Metal'},
        'Mn': {'name': 'Manganese', 'tr_name': 'Manganez', 'number': 25, 'mass': 54.938, 'group': 7, 'period': 4, 'type': 'Transition Metal'},
        'Fe': {'name': 'Iron', 'tr_name': 'Demir', 'number': 26, 'mass': 55.845, 'group': 8, 'period': 4, 'type': 'Transition Metal'},
        'Co': {'name': 'Cobalt', 'tr_name': 'Kobalt', 'number': 27, 'mass': 58.933, 'group': 9, 'period': 4, 'type': 'Transition Metal'},
        'Ni': {'name': 'Nickel', 'tr_name': 'Nikel', 'number': 28, 'mass': 58.693, 'group': 10, 'period': 4, 'type': 'Transition Metal'},
        'Cu': {'name': 'Copper', 'tr_name': 'Bakır', 'number': 29, 'mass': 63.546, 'group': 11, 'period': 4, 'type': 'Transition Metal'},
        'Zn': {'name': 'Zinc', 'tr_name': 'Çinko', 'number': 30, 'mass': 65.38, 'group': 12, 'period': 4, 'type': 'Transition Metal'},
        'Br': {'name': 'Bromine', 'tr_name': 'Brom', 'number': 35, 'mass': 79.904, 'group': 17, 'period': 4, 'type': 'Halogen'},
        'Ag': {'name': 'Silver', 'tr_name': 'Gümüş', 'number': 47, 'mass': 107.8682, 'group': 11, 'period': 5, 'type': 'Transition Metal'},
        'I': {'name': 'Iodine', 'tr_name': 'İyot', 'number': 53, 'mass': 126.904, 'group': 17, 'period': 5, 'type': 'Halogen'},
        'Ba': {'name': 'Barium', 'tr_name': 'Baryum', 'number': 56, 'mass': 137.327, 'group': 2, 'period': 6, 'type': 'Alkaline Earth Metal'},
        'Pt': {'name': 'Platinum', 'tr_name': 'Platin', 'number': 78, 'mass': 195.084, 'group': 10, 'period': 6, 'type': 'Transition Metal'},
        'Au': {'name': 'Gold', 'tr_name': 'Altın', 'number': 79, 'mass': 196.9666, 'group': 11, 'period': 6, 'type': 'Transition Metal'},
        'Hg': {'name': 'Mercury', 'tr_name': 'Cıva', 'number': 80, 'mass': 200.592, 'group': 12, 'period': 6, 'type': 'Transition Metal'},
        'Pb': {'name': 'Lead', 'tr_name': 'Kurşun', 'number': 82, 'mass': 207.2, 'group': 14, 'period': 6, 'type': 'Post-transition Metal'},
    }

    def __init__(self, master, app):
        super().__init__(master, style="Panel.TFrame")
        self.app = app
        self.scenario = tk.StringVar(value="İdeal gaz yasası")
        self.element_var = tk.StringVar(value='H')
        self.formula_var = tk.StringVar(value='H2O')
        self.mass_var = tk.StringVar(value='18')
        self.reaction_var = tk.StringVar(value='2H2 + O2 -> 2H2O')
        self.given_species_var = tk.StringVar(value='H2')
        self.given_mass_var = tk.StringVar(value='4')
        self.target_species_var = tk.StringVar(value='H2O')
        self.actual_yield_var = tk.StringVar(value='30')
        self._build()
        self.load_defaults()
        self.show_element_info()

    def _build(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Chemistry → Math Lab", style="Header.TLabel").pack(side="left")
        ttk.Label(top, text="Kimyasal olayı denklem, fonksiyon, hız yasası, denge veya diferansiyel denklem mantığıyla açıklar.", style="Muted.TLabel").pack(side="left", padx=12)

        row = ttk.Frame(self, style="Panel.TFrame")
        row.pack(fill="x", padx=8, pady=4)
        ttk.Label(row, text="Kimyasal olay:", style="Muted.TLabel").pack(side="left")
        combo = ttk.Combobox(row, textvariable=self.scenario, values=list(self.DEFAULTS.keys()), width=34, state="readonly")
        combo.pack(side="left", padx=6)
        combo.bind("<<ComboboxSelected>>", lambda e: self.load_defaults())
        RoundedButton(row, text="Varsayılan Değerleri Yükle", command=self.load_defaults).pack(side="left", padx=3)
        RoundedButton(row, text="Matematiğe Dönüştür", command=self.analyze).pack(side="left", padx=3)
        RoundedButton(row, text="Rapor Kaydet", command=self.save_report).pack(side="left", padx=3)
        RoundedButton(row, text="Grafik Çiz", command=self.draw_graph).pack(side="left", padx=3)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(body, style="Panel.TFrame")
        right = ttk.Frame(body, style="Panel.TFrame")
        body.add(left, weight=1)
        body.add(right, weight=3)

        ttk.Label(left, text="Parametreler", style="Header.TLabel").pack(fill="x", padx=8, pady=(8, 2))
        ttk.Label(left, text="Her satıra key=value yaz. Örnek: P=1 veya k=0.25", style="Muted.TLabel").pack(fill="x", padx=8, pady=(0, 6))
        self.params_text = tk.Text(left, height=14, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.params_text.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Label(right, text="Kimyanın Matematiğe Yansıması", style="Header.TLabel").pack(fill="x", padx=8, pady=(8, 2))
        self.output = tk.Text(right, height=14, wrap="word", bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        self.output.pack(fill="both", expand=True, padx=8, pady=8)
        self.graph_canvas = tk.Canvas(right, height=210, bg=THEME["surface"], highlightbackground=THEME["line"], highlightthickness=1)
        self.graph_canvas.pack(fill="x", padx=8, pady=(0,8))

        tools = ttk.LabelFrame(self, text="Kimya Araçları / Chemistry Tools")
        tools.pack(fill="both", expand=False, padx=8, pady=(0,8))
        trow = ttk.Frame(tools, style="Panel.TFrame")
        trow.pack(fill="both", expand=True, padx=6, pady=6)
        periodic = ttk.Frame(trow, style="Panel.TFrame")
        molcalc = ttk.Frame(trow, style="Panel.TFrame")
        stoich = ttk.Frame(trow, style="Panel.TFrame")
        periodic.pack(side='left', fill='both', expand=True, padx=4)
        molcalc.pack(side='left', fill='both', expand=True, padx=4)
        stoich.pack(side='left', fill='both', expand=True, padx=4)

        ttk.Label(periodic, text='Periyodik Tablo Bilgisi', style='Header.TLabel').pack(anchor='w', pady=(0,4))
        ttk.Combobox(periodic, textvariable=self.element_var, values=sorted(self.PERIODIC_TABLE.keys(), key=lambda s: (self.PERIODIC_TABLE[s]['number'], s)), width=12, state='readonly').pack(anchor='w')
        RoundedButton(periodic, text='Elementi Göster', command=self.show_element_info).pack(anchor='w', pady=4)
        RoundedButton(periodic, text='Tam Periyodik Tablo', command=self.open_periodic_table).pack(anchor='w', pady=2)
        self.element_output = tk.Text(periodic, height=10, wrap='word', bg=THEME["surface"], fg=THEME['text'], insertbackground=THEME["text"], relief='flat', font=('Consolas', 10))
        self.element_output.pack(fill='both', expand=True)

        ttk.Label(molcalc, text='Mol Hesaplayıcı', style='Header.TLabel').pack(anchor='w', pady=(0,4))
        ttk.Label(molcalc, text='Formül').pack(anchor='w')
        ttk.Entry(molcalc, textvariable=self.formula_var, width=18).pack(anchor='w', fill='x')
        ttk.Label(molcalc, text='Kütle (g)').pack(anchor='w', pady=(6,0))
        ttk.Entry(molcalc, textvariable=self.mass_var, width=18).pack(anchor='w', fill='x')
        RoundedButton(molcalc, text='Molü Hesapla', command=self.compute_moles).pack(anchor='w', pady=6)
        self.mol_output = tk.Text(molcalc, height=10, wrap='word', bg=THEME["surface"], fg=THEME['text'], insertbackground=THEME["text"], relief='flat', font=('Consolas', 10))
        self.mol_output.pack(fill='both', expand=True)

        ttk.Label(stoich, text='Stokiyometri Aracı', style='Header.TLabel').pack(anchor='w', pady=(0,4))
        ttk.Label(stoich, text='Denklem').pack(anchor='w')
        ttk.Entry(stoich, textvariable=self.reaction_var, width=30).pack(anchor='w', fill='x')
        ttk.Label(stoich, text='Bilinen tür ve kütle (g)').pack(anchor='w', pady=(6,0))
        row2 = ttk.Frame(stoich, style='Panel.TFrame'); row2.pack(fill='x')
        ttk.Entry(row2, textvariable=self.given_species_var, width=10).pack(side='left', fill='x', expand=True)
        ttk.Entry(row2, textvariable=self.given_mass_var, width=10).pack(side='left', fill='x', expand=True, padx=(4,0))
        ttk.Label(stoich, text='Hedef tür').pack(anchor='w', pady=(6,0))
        ttk.Entry(stoich, textvariable=self.target_species_var, width=10).pack(anchor='w', fill='x')
        RoundedButton(stoich, text='Denklemi Dengele', command=self.balance_reaction_ui).pack(anchor='w', pady=(6,2))
        RoundedButton(stoich, text='Stokiyometri Hesapla', command=self.compute_stoichiometry).pack(anchor='w', pady=2)
        ttk.Label(stoich, text='Sınırlayıcı/verim için giren kütleleri (g)').pack(anchor='w', pady=(6,0))
        self.reactant_masses_text = tk.Text(stoich, height=3, wrap='word', bg=THEME["surface"], fg=THEME['text'], insertbackground=THEME["text"], relief='flat', font=('Consolas', 9))
        self.reactant_masses_text.pack(anchor='w', fill='x')
        self.reactant_masses_text.insert('1.0', 'H2=4\nO2=32')
        ttk.Label(stoich, text='Gerçek ürün kütlesi (g)').pack(anchor='w', pady=(6,0))
        ttk.Entry(stoich, textvariable=self.actual_yield_var, width=10).pack(anchor='w', fill='x')
        RoundedButton(stoich, text='Sınırlayıcı Madde + Verim', command=self.compute_limiting_yield).pack(anchor='w', pady=6)
        self.stoich_output = tk.Text(stoich, height=10, wrap='word', bg=THEME["surface"], fg=THEME['text'], insertbackground=THEME["text"], relief='flat', font=('Consolas', 10))
        self.stoich_output.pack(fill='both', expand=True)

    def load_defaults(self):
        self.params_text.delete("1.0", "end")
        self.params_text.insert("1.0", self.DEFAULTS.get(self.scenario.get(), ""))

    def parse_params(self):
        vals = {}
        for line in self.params_text.get("1.0", "end").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip(); v = v.strip().replace(",", ".")
            try:
                vals[k] = float(v)
            except Exception:
                vals[k] = v
        return vals

    def base_header(self, title):
        return f"{title}\nOluşturulma zamanı: {now_iso()}\n" + "=" * 72 + "\n\n"

    def parse_formula_counts(self, formula):
        formula = (formula or '').strip()
        if not formula:
            raise ValueError('Boş formül')
        tokens = re.findall(r'[A-Z][a-z]?|\(|\)|\d+', formula)
        if not tokens:
            raise ValueError('Geçersiz formül')
        stack = [Counter()]
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok == '(':
                stack.append(Counter())
                i += 1
            elif tok == ')':
                if len(stack) == 1:
                    raise ValueError('Parantez hatası')
                group = stack.pop()
                i += 1
                mult = 1
                if i < len(tokens) and tokens[i].isdigit():
                    mult = int(tokens[i]); i += 1
                for k, v in group.items():
                    stack[-1][k] += v * mult
            elif re.fullmatch(r'[A-Z][a-z]?', tok):
                elem = tok
                if elem not in self.PERIODIC_TABLE:
                    raise ValueError(f'Bilinmeyen element: {elem}')
                i += 1
                count = 1
                if i < len(tokens) and tokens[i].isdigit():
                    count = int(tokens[i]); i += 1
                stack[-1][elem] += count
            else:
                raise ValueError('Formül çözümleme hatası')
        if len(stack) != 1:
            raise ValueError('Parantezler kapanmadı')
        return dict(stack[0])

    def molar_mass(self, formula):
        counts = self.parse_formula_counts(formula)
        return sum(self.PERIODIC_TABLE[el]['mass'] * n for el, n in counts.items())

    def analyze(self):
        vals = self.parse_params()
        sc = self.scenario.get()
        if sc == 'İdeal gaz yasası':
            report = self.ideal_gas(vals)
        elif sc == 'Reaksiyon hız yasası':
            report = self.rate_law(vals)
        elif sc == 'Asitlik ve pH':
            report = self.ph_report(vals)
        elif sc == 'Birinci dereceden bozunma':
            report = self.first_order(vals)
        elif sc == 'Difüzyon akısı':
            report = self.diffusion(vals)
        elif sc == 'Henderson-Hasselbalch tamponu':
            report = self.buffer_report(vals)
        else:
            report = 'Bilinmeyen kimya senaryosu.'
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', report)

    def ideal_gas(self, v):
        P = float(v.get('P', 1)); V = float(v.get('V', 1)); n = float(v.get('n', 1)); R = float(v.get('R', 0.082057)); T = float(v.get('T', 273.15))
        lhs = P * V; rhs = n * R * T
        return (self.base_header('İDEAL GAZ YASASI')
            + 'Kimyasal fikir: Gazlar basınç, hacim, mol sayısı ve sıcaklık arasında düzenli bir ilişki gösterir.\n\n'
            + 'Matematiksel model:\nLaTeX: PV=nRT\n\n'
            + f'Hesap: P*V = {P} * {V} = {lhs:.4g}\n'
            + f'Karşı taraf: n*R*T = {n} * {R} * {T} = {rhs:.4g}\n\n'
            + 'Matematiksel yorum: Bu denklem dört değişkenli cebirsel bir bağıntıdır. Bir değişken bilinmiyorsa diğerleri kullanılarak çözülebilir.\n')

    def rate_law(self, v):
        k = float(v.get('k', 0.1)); A = float(v.get('A', 1.0)); m = float(v.get('m', 1.0)); rate = k * (A ** m)
        return (self.base_header('REAKSİYON HIZ YASASI')
            + 'Kimyasal fikir: Tepkimenin ne kadar hızlı olduğu derişime bağlı olabilir.\n\n'
            + 'Matematiksel model:\nLaTeX: r = k[A]^m\n\n'
            + f'Hesap: r = {k} * ({A})^{m} = {rate:.4g}\n\n'
            + 'Matematiksel yorum: Hız bir fonksiyon olarak derişime bağlıdır. Üs m deneysel olarak belirlenir; doğrusal olmayan büyüme görülebilir.\n')

    def ph_report(self, v):
        H = float(v.get('H', 1e-7)); pH = -math.log10(H) if H > 0 else float('inf')
        return (self.base_header('ASİTLİK VE pH')
            + 'Kimyasal fikir: Çözeltideki hidrojen iyonu derişimi arttıkça ortam daha asidik olur.\n\n'
            + 'Matematiksel model:\nLaTeX: pH = -log10[H+]\n\n'
            + f'Hesap: pH = -log10({H}) = {pH:.4g}\n\n'
            + 'Matematiksel yorum: Burada logaritmik fonksiyon kullanılır; derişimdeki 10 kat değişim pH değerini 1 birim değiştirir.\n')

    def first_order(self, v):
        C0 = float(v.get('C0', 1.0)); k = float(v.get('k', 0.1)); t = float(v.get('t', 1.0)); C = C0 * math.exp(-k * t)
        return (self.base_header('BİRİNCİ DERECEDEN BOZUNMA')
            + 'Kimyasal fikir: Bazı türlerin derişimi zamanla mevcut miktarıyla orantılı biçimde azalır.\n\n'
            + 'Matematiksel model:\nLaTeX: dC/dt=-kC\nLaTeX: C(t)=C_0 e^{-kt}\n\n'
            + f'Hesap: C({t}) = {C0} * exp(-{k} * {t}) = {C:.4g}\n\n'
            + 'Matematiksel yorum: Bu bir diferansiyel denklem modelidir. Çözüm üstel azalma fonksiyonudur.\n')

    def diffusion(self, v):
        D = float(v.get('D', 1e-9)); grad = float(v.get('dc_dx', -1.0)); J = -D * grad
        return (self.base_header('DİFÜZYON AKISI')
            + 'Kimyasal fikir: Tanecikler yüksek derişimden düşük derişime doğru taşınır.\n\n'
            + 'Matematiksel model:\nLaTeX: J = -D dc/dx\n\n'
            + f'Hesap: J = -{D} * ({grad}) = {J:.4g}\n\n'
            + 'Matematiksel yorum: Bu ilişki türevsel gradyan kavramını kullanır. İşaret, akının azalan derişim yönüne olduğunu gösterir.\n')

    def buffer_report(self, v):
        pKa = float(v.get('pKa', 4.76)); base = float(v.get('base', 0.1)); acid = float(v.get('acid', 0.1)); ratio = base / acid if acid else float('inf'); pH = pKa + math.log10(ratio) if ratio > 0 else float('inf')
        return (self.base_header('HENDERSON-HASSELBALCH TAMPONU')
            + 'Kimyasal fikir: Zayıf asit ve eşlenik baz karışımı pH değişimine direnç gösterir.\n\n'
            + 'Matematiksel model:\nLaTeX: pH = pKa + log10([A-]/[HA])\n\n'
            + f'Hesap: oran = {base}/{acid} = {ratio:.4g}\n'
            + f'pH = {pKa} + log10({ratio:.4g}) = {pH:.4g}\n\n'
            + 'Matematiksel yorum: Bu model logaritmik bir bağıntıdır ve oran üzerinden çalışır.\n')

    def show_element_info(self):
        sym = (self.element_var.get() or 'H').strip()
        info = self.PERIODIC_TABLE.get(sym)
        self.element_output.delete('1.0', 'end')
        if not info:
            self.element_output.insert('1.0', 'Element bulunamadı.')
            return
        self.element_output.insert('end', f"Sembol: {sym}\n")
        self.element_output.insert('end', f"Adı: {info['name']} / {info['tr_name']}\n")
        self.element_output.insert('end', f"Atom numarası: {info['number']}\n")
        self.element_output.insert('end', f"Atomik kütle: {info['mass']} g/mol\n")
        self.element_output.insert('end', f"Grup: {info['group']}\n")
        self.element_output.insert('end', f"Periyot: {info['period']}\n")
        self.element_output.insert('end', f"Tür: {info['type']}\n")

    def compute_moles(self):
        self.mol_output.delete('1.0', 'end')
        try:
            formula = self.formula_var.get().strip()
            mass = float((self.mass_var.get() or '0').replace(',', '.'))
            mm = self.molar_mass(formula)
            moles = mass / mm if mm else 0.0
            counts = self.parse_formula_counts(formula)
            self.mol_output.insert('end', f"Formül: {formula}\n")
            self.mol_output.insert('end', f"Bileşim: {counts}\n")
            self.mol_output.insert('end', f"Molar kütle: {mm:.5g} g/mol\n")
            self.mol_output.insert('end', f"Verilen kütle: {mass:.5g} g\n")
            self.mol_output.insert('end', f"Mol sayısı: n = m/M = {mass:.5g}/{mm:.5g} = {moles:.5g} mol\n")
        except Exception as exc:
            self.mol_output.insert('end', f"Hata: {exc}\n")

    def parse_reaction(self, reaction):
        reaction = reaction.replace('=>', '->').replace('=', '->')
        if '->' not in reaction:
            raise ValueError('Reaksiyon denkleminde -> bulunmalı')
        left, right = [side.strip() for side in reaction.split('->', 1)]
        def parse_side(side):
            items = []
            for part in side.split('+'):
                part = part.strip()
                m = re.match(r'^([0-9]*\.?[0-9]*)\s*([A-Za-z][A-Za-z0-9()]*)$', part)
                if not m:
                    raise ValueError(f'Bileşen çözümlenemedi: {part}')
                coeff = float(m.group(1)) if m.group(1) else 1.0
                formula = m.group(2)
                items.append((coeff, formula))
            return items
        return parse_side(left), parse_side(right)

    def compute_stoichiometry(self):
        self.stoich_output.delete('1.0', 'end')
        try:
            left, right = self.parse_reaction(self.reaction_var.get().strip())
            all_items = {f: c for c, f in left + right}
            given = self.given_species_var.get().strip()
            target = self.target_species_var.get().strip()
            if given not in all_items or target not in all_items:
                raise ValueError('Bilinen veya hedef tür denklemde bulunamadı')
            given_mass = float((self.given_mass_var.get() or '0').replace(',', '.'))
            given_mm = self.molar_mass(given)
            target_mm = self.molar_mass(target)
            given_moles = given_mass / given_mm if given_mm else 0.0
            target_moles = given_moles * (all_items[target] / all_items[given])
            target_mass = target_moles * target_mm
            self.stoich_output.insert('end', f"Denklem: {self.reaction_var.get().strip()}\n")
            self.stoich_output.insert('end', f"Bilinen tür: {given} ({given_mass:.5g} g)\n")
            self.stoich_output.insert('end', f"Bilinen tür molar kütle: {given_mm:.5g} g/mol\n")
            self.stoich_output.insert('end', f"Bilinen mol: {given_moles:.5g} mol\n\n")
            self.stoich_output.insert('end', f"Katsayı oranı: {all_items[target]:.5g} / {all_items[given]:.5g}\n")
            self.stoich_output.insert('end', f"Hedef tür: {target}\n")
            self.stoich_output.insert('end', f"Hedef mol: {target_moles:.5g} mol\n")
            self.stoich_output.insert('end', f"Hedef molar kütle: {target_mm:.5g} g/mol\n")
            self.stoich_output.insert('end', f"Hedef kütle: {target_mass:.5g} g\n")
        except Exception as exc:
            self.stoich_output.insert('end', f"Hata: {exc}\n")


    def draw_series(self, points, title="Grafik", xlabel="x", ylabel="y"):
        canvas = getattr(self, "graph_canvas", None)
        if canvas is None:
            return
        canvas.delete("all")
        w = max(canvas.winfo_width(), 700)
        h = max(canvas.winfo_height(), 210)
        margin = 42
        canvas.create_text(12, 10, anchor="nw", fill=THEME["text"], text=title, font=("Segoe UI", 10, "bold"))
        if not points:
            canvas.create_text(margin, h/2, anchor="w", fill=THEME["muted"], text="Grafik için yeterli veri yok.")
            return
        xs = [p[0] for p in points]; ys = [p[1] for p in points]
        xmin, xmax = min(xs), max(xs); ymin, ymax = min(ys), max(ys)
        if abs(xmax-xmin) < 1e-12:
            xmax = xmin + 1
        if abs(ymax-ymin) < 1e-12:
            ymax = ymin + 1
        def sx(x): return margin + (x-xmin)/(xmax-xmin)*(w-2*margin)
        def sy(y): return h-margin - (y-ymin)/(ymax-ymin)*(h-2*margin)
        canvas.create_line(margin, h-margin, w-margin, h-margin, fill=THEME["muted"])
        canvas.create_line(margin, margin, margin, h-margin, fill=THEME["muted"])
        canvas.create_text(w/2, h-12, fill=THEME["muted"], text=xlabel)
        canvas.create_text(12, h/2, fill=THEME["muted"], text=ylabel, angle=90)
        canvas.create_text(margin, h-margin+14, fill=THEME["muted"], text=f"{xmin:.3g}")
        canvas.create_text(w-margin, h-margin+14, fill=THEME["muted"], text=f"{xmax:.3g}")
        canvas.create_text(margin-8, h-margin, anchor="e", fill=THEME["muted"], text=f"{ymin:.3g}")
        canvas.create_text(margin-8, margin, anchor="e", fill=THEME["muted"], text=f"{ymax:.3g}")
        coords = []
        for x, y in points:
            coords.extend([sx(x), sy(y)])
        if len(coords) >= 4:
            canvas.create_line(*coords, fill=THEME["accent"], width=2, smooth=True)
        for x, y in points[::max(1, len(points)//18)]:
            canvas.create_oval(sx(x)-2, sy(y)-2, sx(x)+2, sy(y)+2, fill=THEME["green"], outline="")

    def draw_graph(self):
        vals = self.parse_params()
        sc = self.scenario.get()
        points = []
        title = sc
        xlabel = "x"; ylabel = "y"
        try:
            if sc == "İdeal gaz yasası":
                n = float(vals.get("n", 1)); R = float(vals.get("R", 0.082057)); T = float(vals.get("T", 273.15)); V0 = max(float(vals.get("V", 22.4)), 0.1)
                vmax = max(V0*2, 1.0)
                points = [(0.1 + (vmax-0.1)*i/100, n*R*T/(0.1 + (vmax-0.1)*i/100)) for i in range(101)]
                title = "İdeal gaz: P(V)=nRT/V"; xlabel="V"; ylabel="P"
            elif sc == "Reaksiyon hız yasası":
                k = float(vals.get("k", 0.12)); m = float(vals.get("m", 1)); A0 = max(float(vals.get("A", 0.5)), 0.1)
                xmax = max(A0*2, 1.0)
                points = [(xmax*i/100, k*((xmax*i/100)**m)) for i in range(101)]
                title = "Hız yasası: r=k[A]^m"; xlabel="[A]"; ylabel="r"
            elif sc == "Asitlik ve pH":
                points = [(10**(-i/10), i/10) for i in range(0, 141)]
                title = "pH = -log10[H+]"; xlabel="[H+]"; ylabel="pH"
            elif sc == "Birinci dereceden bozunma":
                C0 = float(vals.get("C0", 2)); k = float(vals.get("k", 0.35)); tmax = max(float(vals.get("t", 4))*2, 10)
                points = [(tmax*i/120, C0*math.exp(-k*(tmax*i/120))) for i in range(121)]
                title = "Birinci dereceden bozunma: C(t)=C0e^(-kt)"; xlabel="t"; ylabel="C(t)"
            elif sc == "Difüzyon akısı":
                D = float(vals.get("D", 1.2e-9)); g0 = abs(float(vals.get("dc_dx", -250))) or 1.0
                points = [(-g0 + 2*g0*i/100, -D*(-g0 + 2*g0*i/100)) for i in range(101)]
                title = "Fick yasası: J=-D dc/dx"; xlabel="dc/dx"; ylabel="J"
            elif sc == "Henderson-Hasselbalch tamponu":
                pKa = float(vals.get("pKa", 4.76))
                points = [(0.1 + 9.9*i/100, pKa + math.log10(0.1 + 9.9*i/100)) for i in range(101)]
                title = "Tampon: pH=pKa+log10([A-]/[HA])"; xlabel="[A-]/[HA]"; ylabel="pH"
            self.draw_series(points, title, xlabel, ylabel)
        except Exception as exc:
            self.graph_canvas.delete("all")
            self.graph_canvas.create_text(20, 30, anchor="nw", fill=THEME["danger"], text=f"Grafik hatası: {exc}")

    def open_periodic_table(self):
        win = tk.Toplevel(self)
        win.title("Tam Periyodik Tablo / Full Periodic Table")
        win.geometry("1180x560")
        win.configure(bg=THEME["bg"])
        ttk.Label(win, text="Tam Periyodik Tablo / Full Periodic Table", style="Header.TLabel").pack(fill="x", padx=10, pady=8)
        table = tk.Frame(win, bg=THEME["bg"])
        table.pack(fill="both", expand=True, padx=10, pady=10)
        symbols = [
            "H","He","Li","Be","B","C","N","O","F","Ne","Na","Mg","Al","Si","P","S","Cl","Ar",
            "K","Ca","Sc","Ti","V","Cr","Mn","Fe","Co","Ni","Cu","Zn","Ga","Ge","As","Se","Br","Kr",
            "Rb","Sr","Y","Zr","Nb","Mo","Tc","Ru","Rh","Pd","Ag","Cd","In","Sn","Sb","Te","I","Xe",
            "Cs","Ba","La","Ce","Pr","Nd","Pm","Sm","Eu","Gd","Tb","Dy","Ho","Er","Tm","Yb","Lu",
            "Hf","Ta","W","Re","Os","Ir","Pt","Au","Hg","Tl","Pb","Bi","Po","At","Rn",
            "Fr","Ra","Ac","Th","Pa","U","Np","Pu","Am","Cm","Bk","Cf","Es","Fm","Md","No","Lr",
            "Rf","Db","Sg","Bh","Hs","Mt","Ds","Rg","Cn","Nh","Fl","Mc","Lv","Ts","Og"
        ]
        positions = {
            "H":(1,1),"He":(1,18),
            "Li":(2,1),"Be":(2,2),"B":(2,13),"C":(2,14),"N":(2,15),"O":(2,16),"F":(2,17),"Ne":(2,18),
            "Na":(3,1),"Mg":(3,2),"Al":(3,13),"Si":(3,14),"P":(3,15),"S":(3,16),"Cl":(3,17),"Ar":(3,18),
            "K":(4,1),"Ca":(4,2),"Sc":(4,3),"Ti":(4,4),"V":(4,5),"Cr":(4,6),"Mn":(4,7),"Fe":(4,8),"Co":(4,9),"Ni":(4,10),"Cu":(4,11),"Zn":(4,12),"Ga":(4,13),"Ge":(4,14),"As":(4,15),"Se":(4,16),"Br":(4,17),"Kr":(4,18),
            "Rb":(5,1),"Sr":(5,2),"Y":(5,3),"Zr":(5,4),"Nb":(5,5),"Mo":(5,6),"Tc":(5,7),"Ru":(5,8),"Rh":(5,9),"Pd":(5,10),"Ag":(5,11),"Cd":(5,12),"In":(5,13),"Sn":(5,14),"Sb":(5,15),"Te":(5,16),"I":(5,17),"Xe":(5,18),
            "Cs":(6,1),"Ba":(6,2),"La":(8,3),"Ce":(8,4),"Pr":(8,5),"Nd":(8,6),"Pm":(8,7),"Sm":(8,8),"Eu":(8,9),"Gd":(8,10),"Tb":(8,11),"Dy":(8,12),"Ho":(8,13),"Er":(8,14),"Tm":(8,15),"Yb":(8,16),"Lu":(8,17),
            "Hf":(6,4),"Ta":(6,5),"W":(6,6),"Re":(6,7),"Os":(6,8),"Ir":(6,9),"Pt":(6,10),"Au":(6,11),"Hg":(6,12),"Tl":(6,13),"Pb":(6,14),"Bi":(6,15),"Po":(6,16),"At":(6,17),"Rn":(6,18),
            "Fr":(7,1),"Ra":(7,2),"Ac":(9,3),"Th":(9,4),"Pa":(9,5),"U":(9,6),"Np":(9,7),"Pu":(9,8),"Am":(9,9),"Cm":(9,10),"Bk":(9,11),"Cf":(9,12),"Es":(9,13),"Fm":(9,14),"Md":(9,15),"No":(9,16),"Lr":(9,17),
            "Rf":(7,4),"Db":(7,5),"Sg":(7,6),"Bh":(7,7),"Hs":(7,8),"Mt":(7,9),"Ds":(7,10),"Rg":(7,11),"Cn":(7,12),"Nh":(7,13),"Fl":(7,14),"Mc":(7,15),"Lv":(7,16),"Ts":(7,17),"Og":(7,18)
        }
        atomic_numbers = {sym:i+1 for i, sym in enumerate(symbols)}
        info_panel = tk.Text(win, height=6, bg=THEME["surface"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", font=("Consolas", 10))
        info_panel.pack(fill="x", padx=10, pady=(0,10))
        def show(sym):
            info_panel.delete("1.0","end")
            base = self.PERIODIC_TABLE.get(sym, {})
            info_panel.insert("end", f"Sembol: {sym}\n")
            info_panel.insert("end", f"Atom numarası: {atomic_numbers.get(sym, '?')}\n")
            if base:
                info_panel.insert("end", f"Adı: {base['name']} / {base['tr_name']}\n")
                info_panel.insert("end", f"Atomik kütle: {base['mass']} g/mol\nGrup: {base['group']}  Periyot: {base['period']}\nTür: {base['type']}\n")
            else:
                info_panel.insert("end", "Bu element tablo görünümünde yer alır. Ayrıntılı kütle/veri daha sonra genişletilebilir.\n")
        for c in range(1,19):
            tk.Label(table, text=str(c), bg=THEME["bg"], fg=THEME["muted"], font=("Segoe UI", 8)).grid(row=0, column=c, sticky="nsew")
        for sym, (r,c) in positions.items():
            btn = tk.Button(table, text=f"{atomic_numbers.get(sym,'')}\n{sym}", width=5, height=2, bg=THEME["panel2"], fg=THEME["text"], activebackground=THEME["accent"], activeforeground="white", command=lambda s=sym: show(s))
            btn.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")
        tk.Label(table, text="Lanthanides", bg=THEME["bg"], fg=THEME["muted"]).grid(row=8, column=1, columnspan=2, sticky="e")
        tk.Label(table, text="Actinides", bg=THEME["bg"], fg=THEME["muted"]).grid(row=9, column=1, columnspan=2, sticky="e")
        show(self.element_var.get() or "H")

    def balance_reaction_coefficients(self, reaction):
        left, right = self.parse_reaction(reaction)
        compounds = left + right
        formulas = [f for c, f in compounds]
        elements = sorted(set().union(*(set(self.parse_formula_counts(f).keys()) for f in formulas)))
        matrix = []
        for el in elements:
            row = []
            for idx, (coef, formula) in enumerate(compounds):
                count = self.parse_formula_counts(formula).get(el, 0)
                sign = 1 if idx < len(left) else -1
                row.append(Fraction(sign * count))
            matrix.append(row)
        m = len(matrix); n = len(formulas)
        A = [row[:] for row in matrix]
        pivot_cols = []
        r = 0
        for c in range(n):
            pivot = None
            for i in range(r, m):
                if A[i][c] != 0:
                    pivot = i
                    break
            if pivot is None:
                continue
            A[r], A[pivot] = A[pivot], A[r]
            pv = A[r][c]
            A[r] = [x / pv for x in A[r]]
            for i in range(m):
                if i != r and A[i][c] != 0:
                    factor = A[i][c]
                    A[i] = [A[i][j] - factor*A[r][j] for j in range(n)]
            pivot_cols.append(c)
            r += 1
            if r == m:
                break
        free_cols = [c for c in range(n) if c not in pivot_cols]
        if not free_cols:
            free_cols = [n-1]
        x = [Fraction(0) for _ in range(n)]
        for fc in free_cols:
            x[fc] = Fraction(1)
        for row_i, pc in reversed(list(enumerate(pivot_cols))):
            total = sum(A[row_i][j] * x[j] for j in free_cols)
            x[pc] = -total
        den_lcm = 1
        for val in x:
            den_lcm = den_lcm * val.denominator // math.gcd(den_lcm, val.denominator)
        ints = [int(val * den_lcm) for val in x]
        if all(v <= 0 for v in ints):
            ints = [-v for v in ints]
        if any(v < 0 for v in ints):
            ints = [abs(v) for v in ints]
        g = 0
        for v in ints:
            g = math.gcd(g, abs(v))
        if g:
            ints = [v//g for v in ints]
        return left, right, ints

    def format_balanced_reaction(self, left, right, coeffs):
        left_coeffs = coeffs[:len(left)]
        right_coeffs = coeffs[len(left):]
        def fmt(items, cs):
            parts = []
            for coeff, (old_coeff, formula) in zip(cs, items):
                parts.append((("" if coeff == 1 else str(coeff)) + formula))
            return " + ".join(parts)
        return fmt(left, left_coeffs) + " -> " + fmt(right, right_coeffs)

    def balance_reaction_ui(self):
        self.stoich_output.delete("1.0", "end")
        try:
            left, right, coeffs = self.balance_reaction_coefficients(self.reaction_var.get().strip())
            balanced = self.format_balanced_reaction(left, right, coeffs)
            self.reaction_var.set(balanced)
            self.stoich_output.insert("end", "Dengelenmiş denklem:\n")
            self.stoich_output.insert("end", balanced + "\n\n")
            self.stoich_output.insert("end", "Katsayılar atom sayıları iki tarafta eşit olacak şekilde hesaplandı.\n")
        except Exception as exc:
            self.stoich_output.insert("end", f"Dengeleme hatası: {exc}\n")

    def parse_mass_lines(self):
        masses = {}
        raw = getattr(self, "reactant_masses_text").get("1.0", "end")
        for line in raw.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            masses[k.strip()] = float(v.strip().replace(",", "."))
        return masses

    def compute_limiting_yield(self):
        self.stoich_output.delete("1.0", "end")
        try:
            reaction = self.reaction_var.get().strip()
            left, right, coeffs = self.balance_reaction_coefficients(reaction)
            balanced = self.format_balanced_reaction(left, right, coeffs)
            all_coeffs = {formula: coeffs[i] for i, (old, formula) in enumerate(left + right)}
            reactant_formulas = [formula for old, formula in left]
            masses = self.parse_mass_lines()
            target = self.target_species_var.get().strip()
            if target not in all_coeffs:
                raise ValueError("Hedef tür denklemde bulunamadı")
            ratios = []
            for formula in reactant_formulas:
                if formula not in masses:
                    continue
                mm = self.molar_mass(formula)
                mol = masses[formula] / mm
                ratio = mol / all_coeffs[formula]
                ratios.append((ratio, formula, mol, mm, masses[formula]))
            if not ratios:
                raise ValueError("En az bir giren kütlesi yaz: H2=4 gibi")
            limiting_ratio, limiting_formula, _, _, _ = min(ratios, key=lambda x: x[0])
            target_moles = limiting_ratio * all_coeffs[target]
            target_mass = target_moles * self.molar_mass(target)
            actual_raw = (self.actual_yield_var.get() or "").strip().replace(",", ".")
            actual = float(actual_raw) if actual_raw else None
            percent = (actual / target_mass * 100) if actual is not None and target_mass else None
            self.stoich_output.insert("end", f"Dengelenmiş denklem: {balanced}\n\n")
            for ratio, formula, mol, mm, mass in ratios:
                self.stoich_output.insert("end", f"{formula}: {mass:.5g} g / {mm:.5g} g/mol = {mol:.5g} mol; mol/katsayı = {ratio:.5g}\n")
            self.stoich_output.insert("end", f"\nSınırlayıcı madde: {limiting_formula}\n")
            self.stoich_output.insert("end", f"Teorik {target}: {target_moles:.5g} mol = {target_mass:.5g} g\n")
            if percent is not None:
                self.stoich_output.insert("end", f"Gerçek ürün: {actual:.5g} g\n")
                self.stoich_output.insert("end", f"Yüzde verim: {percent:.4g}%\n")
        except Exception as exc:
            self.stoich_output.insert("end", f"Sınırlayıcı/verim hatası: {exc}\n")

    def save_report(self):
        report = self.output.get('1.0', 'end').strip()
        if not report:
            messagebox.showinfo('Rapor yok', 'Önce Matematiğe Dönüştür butonuna bas.')
            return
        reports = APP_FOLDER / 'Reports'
        reports.mkdir(parents=True, exist_ok=True)
        default_name = reports / f"chemistry_math_lab_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        out = filedialog.asksaveasfilename(title='Chemistry Math Lab raporu kaydet', initialfile=default_name.name, initialdir=str(reports), defaultextension='.txt', filetypes=[('Text', '*.txt')])
        if not out:
            return
        Path(out).write_text(report, encoding='utf-8')
        messagebox.showinfo('Kaydedildi', out)


