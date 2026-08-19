# -*- coding: utf-8 -*-
"""Koyu tema smoke paketi — Gorsel Mat + LaTeX onizlemesi + acik tema regresyonu.

Koyu tema V1 (ONERILER #8) arayuzu kapsamisti; V2 Gorsel Mat'in ESKI
gorsellestirici yollarini ve LaTeX onizlemesini de paletle bagladi. Bu paket
ikisinin de geri kaymamasini bekcilik eder:
  * modul paletleri (zemin koyulasir, murekkep acilir, kontrast korunur)
  * visual_math_lab'de gomulu acik literal KALMAMASI
  * BILINCLI acik adalarin (Manim sahneleri, ders karti posteri) DOKUNULMAMASI
  * gercek matplotlib cizimi: eski yol (_draw_linear_on_ax) + paylasilan yol
  * LaTeX onizlemesi temayi izler, SINAV soru gorseli her zaman acik kalir
  * gercek Tk panelinde hicbir Text kutusunda zemin/metin cakismasi olmamasi

Kullanim:
    python smoke_dark_theme.py            # ikisini de kosar (CI bunu kullanir)
    python smoke_dark_theme.py dark       # tek tema
"""
import io
import os
import re
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
os.chdir(_HERE)

# Argumansiz cagrilirsa IKI temayi da alt surecte kosar ve toplar: tema
# paleti modul globallerini tek yonlu degistirdigi icin ikisi ayni surecte
# kosamaz (apply_dark_palette geri alinamaz — bu bilincli bir tasarim).
if len(sys.argv) == 1:
    import subprocess
    toplam_ok = toplam_fail = 0
    for mod in ("light", "dark"):
        r = subprocess.run([sys.executable, os.path.abspath(__file__), mod],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        print(r.stdout, end="")
        if r.stderr.strip():
            print(r.stderr, end="")
        for satir in (r.stdout or "").splitlines():
            m = re.match(r"RESULT: (\d+) passed, (\d+) failed", satir)
            if m:
                toplam_ok += int(m.group(1))
                toplam_fail += int(m.group(2))
    print("=" * 64)
    print(f"RESULT: {toplam_ok} passed, {toplam_fail} failed  (light + dark)")
    print("=" * 64)
    sys.exit(1 if toplam_fail else 0)

MOD = sys.argv[1]
KOYU = MOD == "dark"
ok = fail = 0


def check(label, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"   [PASS] {label}" + (f" — {extra}" if extra else ""))
    else:
        fail += 1
        print(f"   [FAIL] {label}" + (f" — {extra}" if extra else ""))


def parlaklik(hex_renk):
    h = hex_renk.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b


print(f"== KOYU TEMA V2 SMOKE ({MOD}) ==")

import mca_common
if KOYU:
    mca_common.THEME.update(mca_common.DARK_THEME)

import visual_math_lab as vml
import student_tracker as st
if KOYU:
    vml.apply_dark_palette()
    st.apply_dark_palette()

print("\n-- 1) Modul paleti --")
# ZEMIN renkleri koyu temada koyulasir; MUREKKEP renkleri (AXIS/FG) tam tersi
# acilir — ikisini ayni kurala sokmak yanlis olurdu.
for ad in ("BG", "PANEL_BG", "GRID"):
    deger = getattr(vml, ad)
    check(f"vml.{ad} zemini {'koyu' if KOYU else 'acik'}",
          (parlaklik(deger) < 110) == KOYU, deger)
check(f"vml.FG murekkebi {'acik' if KOYU else 'koyu'}",
      (parlaklik(vml.FG) > 110) == KOYU, vml.FG)
# AXIS bilerek MAT bir ton (acik temada #8A7E6E, koyuda #A6987F): mutlak
# parlakligi iki temada da orta bantta kalir, dogru olcut ZEMINE gore
# kontrasttir.
check("vml.AXIS zemine gore okunur kaliyor",
      abs(parlaklik(vml.AXIS) - parlaklik(vml.BG)) > 70,
      f"{vml.AXIS} / {vml.BG}")
check("vml.FG ile vml.BG arasinda kontrast var",
      abs(parlaklik(vml.FG) - parlaklik(vml.BG)) > 90,
      f"{vml.FG} / {vml.BG}")
check("vml.FG ile vml.PANEL_BG arasinda kontrast var",
      abs(parlaklik(vml.FG) - parlaklik(vml.PANEL_BG)) > 90,
      f"{vml.FG} / {vml.PANEL_BG}")

print("\n-- 2) Gomulu acik literal kalmadi mi --")
kaynak = Path("visual_math_lab.py").read_text(encoding="utf-8").splitlines()
DOKUNMA = [(100, 135), (1094, 1143), (4253, 4337)]
kacak = []
for i, s in enumerate(kaynak, 1):
    if any(a <= i <= b for a, b in DOKUNMA):
        continue
    if '("selected", "#ffffff")' in s:
        continue
    for renk in ("#FBF7F1", "#FFFFFF", "#ECE3D8", "#8A7E6E", "#2B2620", "#3A352D"):
        if f'"{renk}"' in s:
            kacak.append((i, renk))
check("eski gorsellestirici yollarinda gomulu acik renk kalmadi",
      not kacak, str(kacak[:4]))
savefig_acik = [s for s in kaynak if "savefig" in s and "#FBF7F1" in s]
check("savefig facecolor'lari palete bagli", not savefig_acik, str(savefig_acik[:2]))

print("\n-- 3) Bilincli acik adalar KORUNDU --")
manim_bolge = "\n".join(kaynak[1093:1143] + kaynak[4252:4337])
check("Manim sahnelerine dokunulmadi",
      "#8A7E6E" in manim_bolge or "#2B2620" in manim_bolge,
      "sahne renkleri literal olarak duruyor")
poster = Path("visual_lesson_card.py").read_text(encoding="utf-8")
check("ders karti posteri acik kaldi (visual_lesson_card)",
      "#ffffff" in poster.lower() and "apply_dark_palette" not in poster)

print("\n-- 4) Gercek grafik uretimi (matplotlib) --")
import matplotlib
matplotlib.use("Agg")
eng = vml.VisualMathEngine("Write the equation of the line with slope 2 through (0, 3)")
check("motor bir problem tipi cozdu", bool(eng.problem_type), str(eng.problem_type))
# ESKI GORSELLESTIRICI YOLU: dogrusal aile render_figure() yerine
# _draw_linear_on_ax() ile ciziliyor — koyu tema V2'nin asil hedefi burasi.
from matplotlib.figure import Figure
viz = vml.SlopeInterceptVisualizer(2, (0, 3))
fig = Figure(figsize=(6, 5), dpi=100, facecolor=vml.BG)
ax0 = fig.add_subplot(111)
vml._draw_linear_on_ax(ax0, viz)
check("eski yol (_draw_linear_on_ax) cizdi", bool(ax0.lines))
# Paylasilan yol: render_figure'lu bir gorsellestirici
fig2 = Figure(figsize=(6, 5), dpi=100, facecolor=vml.BG)
vml.QuadraticVisualizer(1, -3, 2).render_figure(fig2, lang="tr", real_life=False)
check("paylasilan yol (render_figure) cizdi", bool(fig2.axes))
if fig is not None:
    yuz = fig.get_facecolor()
    yuz_hex = "#%02X%02X%02X" % tuple(int(c * 255) for c in yuz[:3])
    check(f"figur zemini {'koyu' if KOYU else 'acik'}",
          (parlaklik(yuz_hex) < 110) == KOYU, yuz_hex)
    ax = ax0
    ax_hex = "#%02X%02X%02X" % tuple(int(c * 255) for c in ax.get_facecolor()[:3])
    check(f"eksen zemini {'koyu' if KOYU else 'acik'}",
          (parlaklik(ax_hex) < 110) == KOYU, ax_hex)
    tick = ax.xaxis.get_ticklabels()
    if tick:
        t_hex = matplotlib.colors.to_hex(tick[0].get_color()).upper()
        check("tick etiketleri zemine gore okunur",
              abs(parlaklik(t_hex) - parlaklik(ax_hex)) > 70, t_hex)
    tmp = Path(tempfile.mkdtemp(prefix="vmlsmoke_")) / "g.png"
    fig.savefig(str(tmp), facecolor=vml.BG, dpi=90)
    check("PNG diske yazildi", tmp.exists() and tmp.stat().st_size > 1000,
          f"{tmp.stat().st_size} bayt")

print("\n-- 5) LaTeX onizlemesi (student_tracker) --")
check("DARK_MODE bayragi dogru", st.DARK_MODE == KOYU, str(st.DARK_MODE))
img, err = st.render_math_image(r"$\frac{-b \pm \sqrt{b^2-4ac}}{2a}$")
check("onizleme uretildi", img is not None, err)
if img is not None:
    kose = img.convert("RGB").getpixel((2, 2))
    kose_hex = "#%02X%02X%02X" % kose
    check(f"onizleme zemini {'koyu' if KOYU else 'acik'} (ARAYUZ, temayi izler)",
          (parlaklik(kose_hex) < 110) == KOYU, kose_hex)
icerik, _ = st.render_math_image(r"$x^2$", dark=False)
if icerik is not None:
    k2 = icerik.convert("RGB").getpixel((2, 2))
    k2_hex = "#%02X%02X%02X" % k2
    check("sinav soru gorseli HER ZAMAN acik (icerik adasi)",
          parlaklik(k2_hex) > 200, k2_hex)

print("\n-- 6) Tk paneli gercekten kuruluyor mu --")
try:
    import tkinter as tk
    from tkinter import ttk
    root = tk.Tk()
    root.withdraw()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    lab = vml.VisualMathLab(root, None)
    check("VisualMathLab paneli kuruldu", lab.winfo_exists() == 1)
    metinler = []

    def gez(w):
        for c in w.winfo_children():
            if isinstance(c, tk.Text):
                metinler.append(c)
            gez(c)
    gez(lab)
    check("panelde Text alani var", len(metinler) > 0, f"{len(metinler)} adet")
    hatali = []
    for t in metinler:
        try:
            bg = str(t.cget("bg"))
            fg = str(t.cget("fg"))
            if bg.startswith("#") and fg.startswith("#"):
                if abs(parlaklik(bg) - parlaklik(fg)) < 70:
                    hatali.append((bg, fg))
        except Exception:
            pass
    check("hicbir Text kutusunda zemin/metin cakismasi yok", not hatali, str(hatali[:3]))
    zeminler = {str(t.cget("bg")) for t in metinler if str(t.cget("bg")).startswith("#")}
    check(f"Text zeminleri {'koyu' if KOYU else 'acik'}",
          all((parlaklik(z) < 110) == KOYU for z in zeminler), str(sorted(zeminler)))
    lab.destroy()
    root.destroy()
except Exception as exc:
    check("Tk paneli kuruldu", False, str(exc))

print("=" * 64)
print(f"RESULT: {ok} passed, {fail} failed  ({MOD})")
print("=" * 64)
sys.exit(1 if fail else 0)
