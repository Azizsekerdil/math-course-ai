# -*- coding: utf-8 -*-
"""Math Course AI — the PUBLISHED presentation PDF, rendered with a libre font.

Why this module exists instead of just exporting the PPTX
---------------------------------------------------------
`tanitim_uret.py` builds the editable PPTX/HTML deck and can export a PDF
through PowerPoint COM. That export is fine for personal use, but it has two
properties that make it wrong for a *published* artifact:

  * it needs Microsoft PowerPoint, so the published file cannot be rebuilt on
    CI or on anyone else's machine; and
  * PowerPoint substitutes whatever font the machine happens to have, so the
    PDF ends up embedding proprietary system fonts whose redistribution depends
    on their own embedding permission bits.

This renderer draws the same content (`tanitim_icerik.SLAYTLAR`) straight to
PDF with **matplotlib**, which is already a required dependency and ships
**DejaVu Sans** (DejaVu Fonts License — freely redistributable, embedding
allowed). `pdf.fonttype = 42` embeds a TrueType subset, so the published deck
carries only a libre font.

    python tanitim_pdf.py            # both languages into docs/presentation/
    python tanitim_pdf.py --tr       # one language

The content is single-sourced: this module never restates a fact. If a number
is wrong, it is wrong in `tanitim_icerik.py`.
"""

from __future__ import annotations

import os
import re
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages               # noqa: E402
from matplotlib.patches import FancyBboxPatch                      # noqa: E402

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tanitim_icerik import SLAYTLAR, ALTBASLIK                     # noqa: E402
from mca_common import VERSION, APP_NAME                           # noqa: E402

#: The one font this document is allowed to use. Bundled with matplotlib.
FONT_AILESI = "DejaVu Sans"
FONT_LISANS = "DejaVu Fonts License (Bitstream Vera derivative)"
FONT_LIBRE = True

matplotlib.rcParams.update({
    "font.family": FONT_AILESI,
    "pdf.fonttype": 42,          # embed a TrueType subset, not Type 3 outlines
    "pdf.compression": 6,
    "figure.dpi": 200,
})

GORSEL_KLASOR = ROOT / "tanitim_gorseller"
CIKTI_KLASOR = ROOT / "docs" / "presentation"

EN, BOY = 13.333, 7.5                                              # 16:9 inches

# ── Print palette: light paper, warm identity, high contrast ───────────────
ZEMIN = "#FFFFFF"
PANEL = "#F6F1E8"
CIZGI = "#DFD4C2"
METIN = "#241F1A"
SOLUK = "#6B6055"
VURGU = "#C2611F"

#: DejaVu Sans has no emoji coverage; rendering them would produce tofu boxes.
#: They are decorative in this deck, so they are dropped for the PDF only.
_EMOJI = re.compile(
    "[" "\U0001F000-\U0001FAFF" "←-⇿" "⌀-⏿" "①-➿"
    "⬀-⯿" "️" "‍" "]+")


def _c(cift, dil):
    """(tr, en) → the string for `dil`, falling back to Turkish."""
    if isinstance(cift, (tuple, list)) and len(cift) == 2:
        s = cift[1] if dil == "en" else cift[0]
        return (s or cift[0] or "").strip()
    return str(cift or "").strip()


def _temiz(s):
    return _EMOJI.sub("", str(s or "")).replace("  ", " ").strip()


def _yeni_sayfa(pdf_ekle=None):
    fig = plt.figure(figsize=(EN, BOY))
    fig.patch.set_facecolor(ZEMIN)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _kutu(ax, x, y, w, h, renk=PANEL, kenar=CIZGI):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
                                linewidth=0.8, edgecolor=kenar, facecolor=renk,
                                transform=ax.transAxes, zorder=1))


def _yaz(ax, x, y, s, boyut=12, renk=METIN, kalin=False, hiza="left",
         dikey="top", genislik=None):
    s = _temiz(s)
    if genislik:
        s = "\n".join(textwrap.fill(par, genislik) for par in s.split("\n"))
    ax.text(x, y, s, fontsize=boyut, color=renk, ha=hiza, va=dikey,
            fontweight="bold" if kalin else "normal", transform=ax.transAxes,
            linespacing=1.35, zorder=3)
    return s.count("\n") + 1


def _baslik_bandi(ax, veri, dil, no, toplam):
    _yaz(ax, 0.055, 0.945, _c(veri.get("baslik"), dil), 25, METIN, True, genislik=62)
    ax.plot([0.055, 0.945], [0.875, 0.875], color=VURGU, linewidth=2.4,
            transform=ax.transAxes, zorder=2)
    if veri.get("alt"):
        _yaz(ax, 0.055, 0.855, _c(veri["alt"], dil), 12.5, SOLUK, genislik=115)
    _yaz(ax, 0.945, 0.038, f"{APP_NAME}  ·  {no}/{toplam}", 8.5, SOLUK, hiza="right",
         dikey="bottom")


def _dipnot(ax, veri, dil):
    if veri.get("dipnot"):
        _yaz(ax, 0.055, 0.085, _c(veri["dipnot"], dil), 8.8, SOLUK, genislik=150)


# ── slide renderers ───────────────────────────────────────────────────────
def _kapak(ax, veri, dil, no, toplam):
    ax.add_patch(FancyBboxPatch((0.0, 0.0), 1.0, 1.0, boxstyle="square,pad=0",
                                linewidth=0, facecolor=PANEL,
                                transform=ax.transAxes, zorder=0))
    _yaz(ax, 0.5, 0.62, _c(veri.get("baslik"), dil), 46, METIN, True, hiza="center",
         dikey="center")
    ax.plot([0.33, 0.67], [0.545, 0.545], color=VURGU, linewidth=3.0,
            transform=ax.transAxes, zorder=2)
    _yaz(ax, 0.5, 0.47, _c(veri.get("alt"), dil), 14, SOLUK, hiza="center",
         dikey="top", genislik=78)
    _yaz(ax, 0.5, 0.14, _c(veri.get("dipnot"), dil), 10, SOLUK, hiza="center",
         dikey="top", genislik=104)


def _madde(ax, veri, dil, no, toplam):
    _baslik_bandi(ax, veri, dil, no, toplam)
    y = 0.79 if not veri.get("alt") else 0.75
    for oge in veri.get("ogeler") or []:
        metin = _temiz(_c(oge, dil))
        sarilmis = textwrap.fill(metin, 104)
        ax.text(0.070, y, "•", fontsize=13, color=VURGU, va="top",
                transform=ax.transAxes, zorder=3)
        ax.text(0.093, y, sarilmis, fontsize=12.2, color=METIN, va="top",
                transform=ax.transAxes, linespacing=1.4, zorder=3)
        y -= 0.055 + 0.036 * sarilmis.count("\n")
    _dipnot(ax, veri, dil)


def _kart(ax, veri, dil, no, toplam):
    _baslik_bandi(ax, veri, dil, no, toplam)
    ogeler = veri.get("ogeler") or []
    ust = 0.78 if not veri.get("alt") else 0.74
    sutun, kw = 2, 0.415
    kh = min(0.27, (ust - 0.14) / max(1, (len(ogeler) + 1) // sutun) - 0.03)
    for i, (bas, govde) in enumerate(ogeler):
        cx = 0.055 + (i % sutun) * (kw + 0.06)
        cy = ust - (i // sutun) * (kh + 0.035) - kh
        _kutu(ax, cx, cy, kw, kh)
        _yaz(ax, cx + 0.018, cy + kh - 0.03, _c(bas, dil), 12.6, VURGU, True, genislik=40)
        _yaz(ax, cx + 0.018, cy + kh - 0.098, _c(govde, dil), 10.4, METIN, genislik=52)
    _dipnot(ax, veri, dil)


def _sayi(ax, veri, dil, no, toplam):
    _baslik_bandi(ax, veri, dil, no, toplam)
    ogeler = veri.get("ogeler") or []
    n = max(1, len(ogeler))
    kw = (0.89 - 0.03 * (n - 1)) / n
    for i, (sayi, etiket) in enumerate(ogeler):
        cx = 0.055 + i * (kw + 0.03)
        _kutu(ax, cx, 0.34, kw, 0.36)
        _yaz(ax, cx + kw / 2, 0.60, _c(sayi, dil), 34, VURGU, True, hiza="center",
             dikey="center")
        _yaz(ax, cx + kw / 2, 0.51, _c(etiket, dil), 10.6, METIN, hiza="center",
             dikey="top", genislik=26)
    _dipnot(ax, veri, dil)


def _tablo(ax, veri, dil, no, toplam):
    _baslik_bandi(ax, veri, dil, no, toplam)
    satirlar = veri.get("ogeler") or []
    y = 0.72
    yuk = min(0.075, (y - 0.16) / max(1, len(satirlar)))
    for i, (sol, sag) in enumerate(satirlar):
        if i == 0:
            _kutu(ax, 0.055, y - yuk, 0.89, yuk, renk="#EFE3D0")
        elif i % 2 == 0:
            _kutu(ax, 0.055, y - yuk, 0.89, yuk, renk="#FBF7F1", kenar="#FBF7F1")
        _yaz(ax, 0.078, y - yuk / 2, _c(sol, dil), 11.4, METIN, i == 0, dikey="center")
        _yaz(ax, 0.50, y - yuk / 2, _c(sag, dil), 11.4, METIN if i else METIN,
             i == 0, dikey="center")
        y -= yuk + 0.006
    _dipnot(ax, veri, dil)


def _gorsel_yolu(ad, dil):
    for d in (dil, "tr", "en"):
        p = GORSEL_KLASOR / d / ad
        if p.is_file():
            return p
    return None


def _resim(fig, yol, x, y, w, h):
    """Place an image inside (x, y, w, h) in figure coords, preserving aspect."""
    img = plt.imread(str(yol))
    ih, iw = img.shape[0], img.shape[1]
    hedef = (w * EN) / (h * BOY)
    kaynak = iw / ih
    if kaynak > hedef:
        yeni_h = (w * EN / kaynak) / BOY
        y += (h - yeni_h) / 2
        h = yeni_h
    else:
        yeni_w = (h * BOY * kaynak) / EN
        x += (w - yeni_w) / 2
        w = yeni_w
    iax = fig.add_axes([x, y, w, h], zorder=4)
    iax.imshow(img)
    iax.axis("off")
    for kenar in iax.spines.values():
        kenar.set_visible(False)


def _gorsel(fig, ax, veri, dil, no, toplam):
    _baslik_bandi(ax, veri, dil, no, toplam)
    yol = _gorsel_yolu(veri.get("gorsel") or "", dil)
    ust = 0.13
    if yol:
        _resim(fig, yol, 0.075, ust, 0.85, (0.80 if not veri.get("alt") else 0.74) - ust)
    else:
        _yaz(ax, 0.5, 0.45, "[%s]" % (veri.get("gorsel") or "?"), 12, SOLUK,
             hiza="center", dikey="center")
    _dipnot(ax, veri, dil)


def _galeri(fig, ax, veri, dil, no, toplam):
    _baslik_bandi(ax, veri, dil, no, toplam)
    ogeler = veri.get("ogeler") or []
    n = max(1, len(ogeler))
    kw = (0.89 - 0.04 * (n - 1)) / n
    for i, (ad, altyazi) in enumerate(ogeler):
        cx = 0.055 + i * (kw + 0.04)
        yol = _gorsel_yolu(ad, dil)
        if yol:
            _resim(fig, yol, cx, 0.27, kw, 0.50)
        _yaz(ax, cx + kw / 2, 0.235, _c(altyazi, dil), 10.6, METIN, hiza="center",
             dikey="top", genislik=52)
    _dipnot(ax, veri, dil)


def _kapanis(ax, veri, dil, no, toplam):
    _madde(ax, veri, dil, no, toplam)


def sayfa_ciz(fig, ax, veri, dil, no, toplam):
    tip = veri.get("tip")
    if tip == "kapak":
        _kapak(ax, veri, dil, no, toplam)
    elif tip in ("madde", "kapanis"):
        _madde(ax, veri, dil, no, toplam)
    elif tip == "kart":
        _kart(ax, veri, dil, no, toplam)
    elif tip == "sayi":
        _sayi(ax, veri, dil, no, toplam)
    elif tip == "tablo":
        _tablo(ax, veri, dil, no, toplam)
    elif tip == "gorsel":
        _gorsel(fig, ax, veri, dil, no, toplam)
    elif tip == "galeri":
        _galeri(fig, ax, veri, dil, no, toplam)
    else:                                    # unknown type: fail loudly, not silently
        raise ValueError("bilinmeyen slayt tipi / unknown slide type: %r" % tip)


def uret(dil, cikti):
    cikti = Path(cikti)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    toplam = len(SLAYTLAR)
    with PdfPages(str(cikti)) as pdf:
        for i, veri in enumerate(SLAYTLAR, 1):
            fig, ax = _yeni_sayfa()
            sayfa_ciz(fig, ax, veri, dil, i, toplam)
            pdf.savefig(fig, facecolor=ZEMIN)
            plt.close(fig)
        # Deliberately minimal metadata: no author, no machine, no local path.
        info = pdf.infodict()
        info["Title"] = "%s — %s" % (APP_NAME, _c(ALTBASLIK, dil))
        info["Subject"] = VERSION
        info["Author"] = ""
        info["Creator"] = "tanitim_pdf.py (matplotlib)"
        info["Producer"] = "matplotlib"
        info["Keywords"] = ""
    return cikti


def main(argv):
    diller = []
    if "--tr" in argv:
        diller = ["tr"]
    elif "--en" in argv:
        diller = ["en"]
    else:
        diller = ["tr", "en"]
    adlar = {"tr": "Math_Course_AI_Tanitim_TR_PUBLIC.pdf",
             "en": "Math_Course_AI_Intro_EN_PUBLIC.pdf"}
    print("Math Course AI — published presentation PDF")
    print("font: %s (%s)" % (FONT_AILESI, FONT_LISANS))
    for dil in diller:
        yol = uret(dil, CIKTI_KLASOR / adlar[dil])
        print("  [OK] %s  (%d slides, %d bytes)"
              % (yol.name, len(SLAYTLAR), yol.stat().st_size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
