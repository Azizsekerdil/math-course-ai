# -*- coding: utf-8 -*-
"""Math Course AI — newcomer tour deck (TR + EN), rendered to PDF.

Why a second deck?
------------------
`tanitim_icerik.py` → `tanitim_pdf.py` is the complete public fact sheet: every
claim, every caveat, CI and licence notes. This module is the *guided tour* for
someone who has never seen the program: it walks through the real interface,
screen by screen, with numbered call-outs on the actual screenshots, and then
explains what each workspace is for.

    python tanitim_tur.py            # both languages into docs/presentation/
    python tanitim_tur.py --tr       # one language
    python tanitim_tur.py --html     # also keep the HTML next to the PDF

Rules it keeps (same as the rest of the repository):

  * Screenshots are the REAL captures in `tanitim_gorseller/<lang>/`, produced
    by `tanitim_ekran.py` against the synthetic demo library. They are only
    cropped here (CSS), never edited or mocked up.
  * Every count comes from `tools/measure_facts.py`; none is hand-written.
  * Local by default, cloud optional and only on per-session consent — no
    absolute offline/privacy wording.

Rendering: the slides are HTML/CSS printed to PDF by a Chromium-family browser
in headless mode (Chromium, Chrome or Edge; set MCA_CHROMIUM to choose one).
Font: Inter (SIL Open Font License 1.1) → Source Sans 3 → DejaVu Sans, all libre.
Set MCA_FONT_DIR to a folder holding the static Inter-*.ttf files (from the
Inter release's extras/ttf/) to get a TrueType-embedded PDF; otherwise the
installed family is used.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

GORSEL_KLASOR = ROOT / "tanitim_gorseller"
CIKTI_KLASOR = ROOT / "docs" / "presentation"
ADLAR = {"tr": "Math_Course_AI_Sunum_TR.pdf",
         "en": "Math_Course_AI_Presentation_EN.pdf"}

RELEASE = "v1.0.0"
REPO = "github.com/Azizsekerdil/math-course-ai"


def _surum_kodu():
    """'V48' from mca_common.VERSION, read statically (no GUI import)."""
    src = (ROOT / "mca_common.py").read_text(encoding="utf-8")
    m = re.search(r'^VERSION = "([^"]+)"', src, re.M)
    return m.group(1).split("—")[0].strip() if m else ""


#: Static Inter TTFs (SIL OFL 1.1) to load explicitly, if MCA_FONT_DIR points at
#: them. Static TrueType is embedded by Chromium as a TrueType subset; the
#: CFF-flavoured .otf many systems install ends up as Type 3 outlines instead.
_INTER_TTF = [("Regular", 400, "normal"), ("Italic", 400, "italic"),
              ("Medium", 500, "normal"), ("SemiBold", 600, "normal"),
              ("Bold", 700, "normal"), ("ExtraBold", 800, "normal")]


def _font_face_css():
    kok = os.environ.get("MCA_FONT_DIR")
    if not kok:
        return ""
    kurallar = []
    for ad, agirlik, stil in _INTER_TTF:
        p = Path(kok) / f"Inter-{ad}.ttf"
        if p.is_file():
            kurallar.append(f'@font-face {{ font-family: "Inter TTF"; src: url("{p.as_uri()}"); '
                            f"font-weight: {agirlik}; font-style: {stil}; }}")
    return "\n".join(kurallar)


def _png_boyut(yol):
    with open(yol, "rb") as f:
        bas = f.read(24)
    if bas[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"PNG değil / not a PNG: {yol}")
    return struct.unpack(">II", bas[16:24])


# ══════════════════════════════════════════════════════════════════════════
# Styles
# ══════════════════════════════════════════════════════════════════════════
CSS = r"""
@page { size: 1280px 720px; margin: 0; }
:root {
  --paper: #FBF8F3; --panel: #F3ECE2; --line: #E5DACB; --white: #FFFFFF;
  --ink: #221D18; --muted: #6E645A; --faint: #9A8F84;
  --accent: #E2762C; --accent-deep: #B4561A; --accent-soft: #FBE7D6;
  --green: #1F9D55; --blue: #2E6BD9; --red: #CC3F2C;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--paper); }
body {
  font-family: "Inter TTF", "Inter", "Source Sans 3", "DejaVu Sans", sans-serif;
  color: var(--ink); -webkit-print-color-adjust: exact; print-color-adjust: exact;
  font-feature-settings: "cv11", "ss03";
}
.slide {
  width: 1280px; height: 720px; position: relative; overflow: hidden;
  background: var(--paper); padding: 50px 64px 60px;
  display: flex; flex-direction: column; break-after: page;
}
.slide:last-child { break-after: auto; }
.kicker {
  font-size: 12.5px; font-weight: 600; letter-spacing: .16em; text-transform: uppercase;
  color: var(--muted); display: flex; gap: 12px; align-items: center;
}
.kicker .no { color: var(--accent-deep); }
.kicker .bar { width: 28px; height: 2px; background: var(--accent); }
h1, h2, h3, p { margin: 0; }
h2 { font-size: 35px; line-height: 1.14; font-weight: 700; letter-spacing: -0.02em;
     margin-top: 12px; max-width: 1080px; }
.lead { font-size: 17px; line-height: 1.5; color: var(--muted); margin-top: 10px;
        max-width: 1000px; }
.body { flex: 1; min-height: 0; margin-top: 26px; display: flex; gap: 40px;
        align-items: flex-start; }
.foot {
  position: absolute; left: 64px; right: 64px; bottom: 22px; display: flex;
  justify-content: space-between; align-items: center; font-size: 11.5px; color: var(--faint);
}
.foot .brand { display: flex; align-items: center; gap: 8px; }
.foot .mini { width: 16px; height: 16px; border-radius: 4px; background: var(--accent);
  color: #fff; font-size: 11px; font-weight: 700; display: flex; align-items: center;
  justify-content: center; }
.note { font-size: 12.5px; color: var(--faint); line-height: 1.45; }
b, strong { font-weight: 600; }
.mono { font-family: "DejaVu Sans Mono", monospace; font-size: .86em; background: var(--panel);
  padding: 1px 6px; border-radius: 5px; color: var(--ink); white-space: nowrap; }

/* screenshots */
.shotwrap { position: relative; flex: none; }
.shot { position: relative; overflow: hidden; border-radius: 10px; width: 100%; height: 100%;
  border: 1px solid var(--line); background: #fff;
  box-shadow: 0 18px 40px -24px rgba(70, 45, 20, .55); }
.shot img { position: absolute; max-width: none; }
.pin { position: absolute; transform: translate(-50%, -50%); z-index: 3;
  width: 26px; height: 26px; border-radius: 50%; background: var(--accent); color: #fff;
  font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 0 3px #fff, 0 3px 10px rgba(0, 0, 0, .28); }
.hl { position: absolute; z-index: 2; border: 2px solid var(--accent); border-radius: 7px;
  background: rgba(226, 118, 44, .07); }
.cap { font-size: 12.5px; color: var(--faint); margin-top: 10px; line-height: 1.45; }

/* numbered legend */
.legend { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column;
  gap: 13px; }
.legend li { display: grid; grid-template-columns: 26px 1fr; column-gap: 13px; }
.legend .n { width: 26px; height: 26px; border-radius: 50%; background: var(--accent);
  color: #fff; font-size: 13px; font-weight: 700; display: flex; align-items: center;
  justify-content: center; }
.legend b { display: block; font-size: 15.5px; line-height: 1.3; padding-top: 3px; }
.legend .d { display: block; font-size: 13.8px; line-height: 1.45; color: var(--muted);
  margin-top: 2px; }
.legend.tight { gap: 10px; }
.legend.compact { gap: 7px; }
.legend.compact li { grid-template-columns: 22px 1fr; column-gap: 10px; }
.legend.compact .n { width: 22px; height: 22px; font-size: 12px; }
.legend.compact b { display: inline; font-size: 14.2px; padding-top: 0; line-height: 22px; }
.legend.compact .d { display: inline; font-size: 13.4px; margin: 0; }
.legend.compact .d::before { content: " — "; }
.legend.tight .d { font-size: 13.2px; }

/* bullets */
.dots { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column;
  gap: 11px; }
.dots li { position: relative; padding-left: 20px; font-size: 15.5px; line-height: 1.45; }
.dots li::before { content: ""; position: absolute; left: 2px; top: 8px; width: 7px;
  height: 7px; border-radius: 50%; background: var(--accent); }
.dots.small li { font-size: 13.8px; }
.dots.big { gap: 14px; }
.dots.big li { font-size: 16.5px; }
.dots.big li::before { top: 9px; }

/* cards */
.grid { display: grid; gap: 16px; width: 100%; }
.card { background: var(--white); border: 1px solid var(--line); border-radius: 14px;
  padding: 20px 22px; }
.card h3 { font-size: 18px; font-weight: 600; line-height: 1.3; }
.card p { font-size: 15px; line-height: 1.52; color: var(--muted); margin-top: 7px; }
.card .tag { display: inline-block; font-size: 11px; font-weight: 600; letter-spacing: .08em;
  text-transform: uppercase; color: var(--accent-deep); background: var(--accent-soft);
  padding: 3px 8px; border-radius: 999px; margin-bottom: 9px; }
.card.accent { border-color: #F0C9A8; background: #FFF9F3; }

/* cover */
.cover { padding: 0; }
.cover .slab { position: absolute; right: -150px; top: -90px; width: 820px; height: 900px;
  background: var(--panel); border-radius: 56px; transform: rotate(-7deg); }
.cover .text { position: absolute; left: 72px; top: 92px; width: 520px; }
.logo { width: 60px; height: 60px; border-radius: 14px; background: var(--accent); color: #fff;
  font-size: 36px; font-weight: 700; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 10px 24px -12px rgba(180, 86, 26, .8); }
.cover h1 { font-size: 64px; font-weight: 800; letter-spacing: -0.035em; line-height: 1.02;
  margin-top: 28px; }
.cover .tag { font-size: 25px; font-weight: 600; line-height: 1.3; margin-top: 18px;
  letter-spacing: -0.01em; }
.cover .sub { font-size: 16.5px; line-height: 1.55; color: var(--muted); margin-top: 18px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 28px; }
.chip { font-size: 12.5px; font-weight: 500; padding: 6px 12px; border-radius: 999px;
  border: 1px solid var(--line); background: var(--white); color: var(--ink); }
.chip.on { background: var(--accent); border-color: var(--accent); color: #fff; }
.cover .hero { position: absolute; left: 640px; top: 150px; }
.cover .foot { left: 72px; }

/* problem → solution table */
.ps { width: 100%; display: grid; grid-template-columns: 34px 360px 1fr; column-gap: 18px; }
.ps .h { font-size: 11.5px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase;
  color: var(--faint); padding-bottom: 10px; border-bottom: 2px solid var(--ink); }
.ps .c { padding: 14px 0; border-bottom: 1px solid var(--line); font-size: 15.5px;
  line-height: 1.45; }
.ps .i { font-weight: 700; color: var(--accent-deep); }
.ps .q { color: var(--muted); font-style: italic; }
.ps .s b { color: var(--ink); }

/* number tiles */
.tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; width: 100%; }
.tile { background: var(--white); border: 1px solid var(--line); border-radius: 16px;
  padding: 30px 30px 28px; }
.tile .v { font-size: 64px; font-weight: 800; letter-spacing: -0.03em; color: var(--accent);
  line-height: 1; font-variant-numeric: tabular-nums; }
.tile .l { font-size: 17px; line-height: 1.45; margin-top: 12px; color: var(--ink); }
.tile .l span { color: var(--muted); }

/* flow */
.flow { display: flex; align-items: stretch; gap: 0; width: 100%; }
.step { flex: 1; background: var(--white); border: 1px solid var(--line); border-radius: 14px;
  padding: 22px 20px 18px; display: flex; flex-direction: column; min-height: 300px; }
.step .k { font-size: 44px; font-weight: 800; color: var(--accent); line-height: 1; }
.step h3 { font-size: 19px; font-weight: 600; margin-top: 16px; line-height: 1.25; }
.step p { font-size: 15px; line-height: 1.5; color: var(--muted); margin-top: 8px; flex: 1; }
.step .w { margin-top: 14px; font-size: 12px; font-weight: 600; color: var(--accent-deep);
  background: var(--accent-soft); border-radius: 7px; padding: 6px 9px; line-height: 1.35; }
.arrow { flex: none; width: 26px; display: flex; align-items: center; justify-content: center;
  color: var(--accent); font-size: 20px; font-weight: 700; }
.band { margin-top: 28px; background: var(--panel); border-radius: 14px; padding: 16px 22px;
  display: flex; align-items: center; gap: 16px; flex-wrap: wrap; font-size: 15px; }
.band .lbl { font-weight: 600; }

/* leitner */
.ladder { display: flex; align-items: flex-end; gap: 12px; height: 330px;
  padding: 0 4px; border-bottom: 2px solid var(--ink); }
.rung { flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: flex-end; height: 100%; }
.rung .val { font-size: 13px; font-weight: 600; margin-bottom: 6px; white-space: nowrap; }
.rung .bar { width: 100%; border-radius: 8px 8px 0 0; background: var(--accent); }
.rung.wrong .bar { background: var(--red); }
.rung.wrong .val { color: var(--red); }
.ladder-x { display: flex; gap: 12px; padding: 8px 4px 0; }
.ladder-x div { flex: 1; text-align: center; font-size: 12.5px; color: var(--muted); }

/* privacy map */
.flowmap { display: flex; align-items: center; gap: 0; }
.flowmap .home { border: 1.5px dashed #D9BFA3; background: #FFF9F3; border-radius: 16px;
  padding: 12px 16px 14px; }
.flowmap .home .lbl { font-size: 11px; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; color: var(--accent-deep); }
.flowmap .row { display: flex; align-items: center; margin-top: 8px; }
.flowmap .node { background: var(--white); border: 1px solid var(--line); border-radius: 12px;
  padding: 12px 16px; width: 250px; }
.flowmap .node h3 { font-size: 16px; font-weight: 600; }
.flowmap .node p { font-size: 12.8px; color: var(--muted); margin-top: 3px; line-height: 1.4; }
.flowmap .node.cloud { border-style: dashed; background: transparent; width: 230px; }
.flowmap .link { width: 120px; display: flex; flex-direction: column; align-items: center;
  gap: 5px; padding: 0 8px; }
.flowmap .link span { font-size: 11.5px; font-weight: 600; color: var(--green);
  text-align: center; line-height: 1.3; }
.flowmap .link .line { width: 100%; height: 0; border-top: 2px solid var(--green);
  position: relative; }
.flowmap .link .line::after { content: ""; position: absolute; right: -2px; top: -6px;
  border: 5px solid transparent; border-left: 8px solid var(--green); }
.flowmap .link.gate { width: 170px; }
.flowmap .link.gate span { color: var(--accent-deep); }
.flowmap .link.gate .line { border-top: 2px dashed var(--accent); }
.flowmap .link.gate .line::after { border-left-color: var(--accent); }
.dots.mid { gap: 10px; }
.dots.mid li { font-size: 15px; }

/* closing */
.closing { background: #221D18; color: #FBF8F3; }
.closing .kicker { color: #B9AC9E; }
.closing .foot { color: #8E8276; }
.closing h2 { font-size: 54px; letter-spacing: -0.03em; }
.closing .lead { color: #D9CCBE; font-size: 19px; }
.closing .chip { background: transparent; color: #FBF8F3; border-color: #5A4E43; }
.closing .chip.on { background: var(--accent); border-color: var(--accent); }
.closing .card { background: #2C2620; border-color: #463C33; }
.closing .card h3 { color: #FBF8F3; }
.closing .card p { color: #CDBFB1; }
"""


# ══════════════════════════════════════════════════════════════════════════
# The deck
# ══════════════════════════════════════════════════════════════════════════
class Deste:
    def __init__(self, dil, olcum):
        self.dil = dil
        self.f = olcum
        self.surum = _surum_kodu()
        self.slaytlar = []

    # ── helpers ──────────────────────────────────────────────────────────
    def t(self, tr, en):
        return en if self.dil == "en" else tr

    def shot(self, ad, kirp=None, genislik=600, pinler=(), kutular=(), stil=""):
        """A cropped, call-out annotated view of a real screenshot.

        kirp    : (x, y, w, h) in source pixels; None = the whole image
        pinler  : (label, x, y) in source pixels
        kutular : (x, y, w, h) highlight rectangles in source pixels
        """
        yol = GORSEL_KLASOR / self.dil / ad
        if not yol.is_file():
            yol = GORSEL_KLASOR / "tr" / ad
        iw, ih = _png_boyut(yol)
        x, y, w, h = kirp or (0, 0, iw, ih)
        s = genislik / w
        yuk = round(h * s)
        # Pins live outside the clipped frame so they may sit on its edge.
        parca = [f'<div class="shotwrap" style="width:{genislik}px;height:{yuk}px;{stil}">'
                 '<div class="shot">',
                 f'<img src="{yol.as_uri()}" style="left:{-x * s:.1f}px;top:{-y * s:.1f}px;'
                 f'width:{iw * s:.1f}px;height:{ih * s:.1f}px" alt="">']
        for bx, by, bw, bh in kutular:
            parca.append(f'<span class="hl" style="left:{(bx - x) * s:.1f}px;'
                         f'top:{(by - y) * s:.1f}px;width:{bw * s:.1f}px;'
                         f'height:{bh * s:.1f}px"></span>')
        parca.append("</div>")
        for etiket, px, py in pinler:
            parca.append(f'<span class="pin" style="left:{(px - x) * s:.1f}px;'
                         f'top:{(py - y) * s:.1f}px">{etiket}</span>')
        parca.append("</div>")
        return "".join(parca)

    @staticmethod
    def kenar(kirp, py, sag=False):
        """A pin centred just outside the left (or right) edge of a crop."""
        x, _, w, _ = kirp
        return (x + w + 12, py) if sag else (x - 12, py)

    @staticmethod
    def legend(ogeler, ilk=1, sinif=""):
        satirlar = [f'<li><span class="n">{i}</span><div><b>{b}</b>'
                    f'<span class="d">{d}</span></div></li>'
                    for i, (b, d) in enumerate(ogeler, ilk)]
        return f'<ol class="legend {sinif}">' + "".join(satirlar) + "</ol>"

    @staticmethod
    def dots(ogeler, sinif=""):
        return f'<ul class="dots {sinif}">' + "".join(f"<li>{o}</li>" for o in ogeler) + "</ul>"

    @staticmethod
    def card(baslik, metin, etiket="", sinif=""):
        tag = f'<span class="tag">{etiket}</span>' if etiket else ""
        return f'<div class="card {sinif}">{tag}<h3>{baslik}</h3><p>{metin}</p></div>'

    def slayt(self, govde, kicker=None, baslik=None, lead=None, sinif="", ham=False):
        no = len(self.slaytlar) + 1
        bas = ""
        if kicker:
            bas += (f'<div class="kicker"><span class="no">{no:02d}</span>'
                    f'<span class="bar"></span><span>{kicker}</span></div>')
        if baslik:
            bas += f"<h2>{baslik}</h2>"
        if lead:
            bas += f'<p class="lead">{lead}</p>'
        ic = govde if ham else f'<div class="head">{bas}</div><div class="body">{govde}</div>'
        alt = (f'<div class="foot"><div class="brand"><span class="mini">Σ</span>'
               f'Math Course AI · {self.t("Tanıtım", "Introduction")}</div>'
               f'<div>{no} / __TOPLAM__</div></div>')
        self.slaytlar.append(f'<section class="slide {sinif}">{ic}{alt}</section>')

    # ── slides ───────────────────────────────────────────────────────────
    def kapak(self):
        t = self.t
        govde = (
            '<div class="slab"></div>'
            '<div class="text">'
            '<div class="logo">Σ</div>'
            '<h1>Math Course AI</h1>'
            '<p class="tag">' + t(
                "Matematik kursunu takip ederken ihtiyacın olan her şey — tek pencerede.",
                "Everything you need while following a maths course — in one window.")
            + '</p><p class="sub">' + t(
                "PDF'lerini oku ve not al, soruları kendi bankana kırp, aralıklı tekrarla "
                "çalış; takıldığında kendi bilgisayarında çalışan yapay zekâya sor.",
                "Read and annotate your PDFs, clip questions into your own bank, study with "
                "spaced repetition — and when you get stuck, ask an AI that runs on your own "
                "computer.")
            + '</p><div class="chips">'
            f'<span class="chip on">{RELEASE}</span>'
            '<span class="chip">Windows 10/11 (x64)</span>'
            '<span class="chip">macOS (Apple Silicon)</span>'
            '<span class="chip">Türkçe · English</span>'
            '<span class="chip">' + t("Açık kaynak · MIT", "Open source · MIT") + '</span>'
            '</div></div>'
            '<div class="hero">' + self.shot("visual.png", genislik=740) + '</div>'
        )
        self.slayt(govde, sinif="cover", ham=True)

    def neden(self):
        t = self.t
        satirlar = [
            (t("PDF bir yerde, notlar başka yerde, sorular defterde.",
               "The PDF is in one place, notes in another, questions in a notebook."),
             t("<b>Tek pencere, tek veritabanı.</b> Kaynakların, notların ve soruların bir "
               "arada; program kaldığın yeri hatırlar.",
               "<b>One window, one database.</b> Your material, notes and questions live "
               "together, and the program remembers where you left off.")),
            (t("Bugün ne çalışacağımı bilmiyorum.", "I don't know what to study today."),
             t("<b>Bugün panosu</b> tekrar vakti gelenleri, yanlışlarını ve hiç denemediklerini "
               "gösterir; tek tıkla o havuzdan sınav başlar.",
               "<b>The Today dashboard</b> shows what is due, what you got wrong and what you "
               "never tried; one click starts an exam on it.")),
            (t("Öğrendiğimi unutuyorum.", "I forget what I learned."),
             t("<b>Aralıklı tekrar:</b> doğru bildiğin soru 1 → 3 → 7 → 14 → 30 → 60 gün "
               "sonra, yanlış bildiğin hemen geri gelir.",
               "<b>Spaced repetition:</b> a question you get right returns after "
               "1 → 3 → 7 → 14 → 30 → 60 days; one you get wrong comes back at once.")),
            (t("Takıldığımda soracak kimse yok.", "There is nobody to ask when I'm stuck."),
             t("<b>Yerel yapay zekâ öğretmen</b> (LM Studio) ve adım adım çözüm gösteren "
               "<b>Görsel Matematik Lab</b>.",
               "<b>A local AI tutor</b> (LM Studio) and the <b>Visual Math Lab</b> with "
               "step-by-step solutions.")),
            (t("Pratik yapacak soru bulamıyorum.", "I can't find practice questions."),
             t("<b>Yerleşik üreteçler</b> sınırsız, telifsiz, iki dilli soru üretir; "
               "PDF'ten de <b>Soru Kırp</b> ile soru alırsın.",
               "<b>Built-in generators</b> make unlimited, licence-free, bilingual questions; "
               "or take questions straight from a PDF with <b>Clip Question</b>.")),
        ]
        h = (f'<div class="ps"><div class="h"></div><div class="h">{t("Sorun", "The problem")}'
             f'</div><div class="h">{t("Math Course AI ne yapar?", "What Math Course AI does")}'
             '</div>')
        for i, (q, s) in enumerate(satirlar, 1):
            h += (f'<div class="c i">{i:02d}</div><div class="c q">“{q}”</div>'
                  f'<div class="c s">{s}</div>')
        h += "</div>"
        self.slayt(h, t("Neden?", "Why"),
                   t("Kurs takip etmek dağınık bir iş. Math Course AI onu toplar.",
                     "Course work is scattered. Math Course AI gathers it up."))

    def bakis(self):
        t, f = self.t, self.f
        tiles = [
            (f["workspaces"], t("çalışma alanı", "workspaces"),
             t("PDF, yapay zekâ, sınav, lab'lar, sözlük…", "PDF, AI, exams, labs, dictionary…")),
            (f["science_labs"], t("bilim laboratuvarı", "science labs"),
             t("Veri, Fizik, Kimya, DNA, Kuantum", "Data, Physics, Chemistry, DNA, Quantum")),
            (f["topic_knowledge_entries"], t("konu bilgi notu", "topic notes"),
             t("yapay zekâ olmadan, anında açılır", "open instantly, no AI involved")),
            (f["embedded_simulations"], t("gömülü simülasyon", "embedded simulations"),
             t("kurs konularının etkileşimli görselleri", "interactive visuals of course topics")),
            (f["formula_cards"], t("formül kartı", "formula cards"),
             t("formülün ne söylediğini gösterir", "show what a formula actually says")),
            (f["guide_chapters"], t("bölümlük kullanma kılavuzu", "chapter user guide"),
             t("program içinde, çevrimdışı, TR ve EN", "inside the program, offline, TR and EN")),
        ]
        h = '<div style="width:100%"><div class="tiles">'
        for v, l, d in tiles:
            h += f'<div class="tile"><div class="v">{v}</div><div class="l">{l}<br><span>{d}</span></div></div>'
        h += ('</div><p class="note" style="margin-top:18px">' + t(
            "Sayılar elle yazılmadı: hepsi depodaki tools/measure_facts.py ile kaynak koddan "
            "ölçüldü.",
            "None of these numbers is hand-written: each is measured from the source code by "
            "tools/measure_facts.py.") + "</p></div>")
        self.slayt(h, t("Bir bakışta", "At a glance"),
                   t("Tek uygulama, eksiksiz bir çalışma masası",
                     "One application, a complete study desk"),
                   t("Hesap açmak, sunucu kurmak gerekmez. Çalışma verilerin kendi "
                     "bilgisayarında, yerel bir veritabanında durur.",
                     "No account to create and no server to run. Your study data lives in a "
                     "local database on your own computer."))

    def anatomi(self):
        t = self.t
        kutular = [(4, 6, 1286, 46), (1296, 8, 298, 40), (4, 60, 1592, 38),
                   (8, 106, 342, 806), (366, 106, 882, 806), (1254, 106, 342, 806)]
        pinler = [(1, 22, 20), (2, 1310, 16), (3, 22, 72), (4, 26, 122), (5, 384, 122),
                  (6, 1272, 122)]
        sol = self.shot("ai.png", genislik=760, kutular=kutular, pinler=pinler)
        sol += ('<p class="cap">' + t(
            "Bu ve sonraki ekranlar çalışan programdan alınmış gerçek ekran görüntüleridir "
            "(sentetik demo kurs kitaplığı, boş öğrenci profili).",
            "This and the following screens are real captures of the running program "
            "(synthetic demo course library, empty learner profile). Some panels still show "
            "Turkish labels because they were built before the language was switched; they "
            "come up in English after a restart.") + "</p>")
        sag = self.legend([
            (t("Üst çubuk", "Top bar"),
             t("Menü, açık çalışma alanının adı, Kaynakları Yenile, Token Raporları, "
               "API Test ve Ayarlar.",
               "Menu, the name of the open workspace, Refresh Resources, Token Reports, "
               "API Test and Settings.")),
            (t("Yapay zekâ durum ışığı", "AI status light"),
             t("Yeşil: hazır (modelin adıyla) · sarı: model yüklü değil · kırmızı: kapalı.",
               "Green: ready (with the model's name) · amber: no model loaded · red: off.")),
            (t("Çalışma alanı şeridi", "Workspace strip"),
             t("Araçlar arasında tek tıkla geçiş; kullanmadığını × ile gizle.",
               "Switch tools in one click; hide the ones you don't use with ×.")),
            (t("Kurs Kaynakları", "Course Resources"),
             t("Kendi kurs klasörünün ağacı, arama ve aç/oku düğmeleri.",
               "The tree of your own course folder, search and open/read buttons.")),
            (t("Çalışma alanı", "The workspace"),
             t("PDF, yapay zekâ, sınav, lab… seçtiğin araç burada açılır.",
               "PDF, AI, exams, labs… the tool you pick opens here.")),
            (t("Kurs Takibi", "Course Tracker"),
             t("Her kurs için bitirdiğin dosyalar ve ilerleme yüzdesi.",
               "Files finished and progress per course.")),
        ], sinif="tight")
        self.slayt(f'<div style="width:760px">{sol}</div><div style="flex:1">{sag}</div>',
                   t("Arayüz", "Interface"),
                   t("Ana pencereyi tanıyalım: üç sütun, tek pencere",
                     "Meet the main window: three columns, one window"))

    def akis(self):
        t = self.t
        adimlar = [
            (t("Kaynaklarını ekle", "Add your material"),
             t("Kurs PDF'lerini Resources klasörüne koy ya da Gözat ile kendi klasörünü seç.",
               "Put your course PDFs into the Resources folder, or pick your own folder with "
               "Browse."),
             t("Kurs Kaynakları", "Course Resources")),
            (t("Oku ve not al", "Read and annotate"),
             t("PDF'i aç; kalemle çiz, işaretle, yaz. Kaldığın sayfa hatırlanır.",
               "Open a PDF; draw, highlight, type. Your page is remembered."),
             t("PDF Okuyucu", "PDF Reader")),
            (t("Soruyu bankana al", "Bank the question"),
             t("Soru Kırp ile soruyu dikdörtgenle seç; kurs, konu ve zorlukla kaydolur.",
               "Drag a rectangle with Clip Question; it is saved with course, topic and "
               "difficulty."),
             t("PDF Okuyucu → Kırp", "PDF Reader → Clip")),
            (t("Pratik yap", "Practise"),
             t("Sınav başlat; aralıklı tekrar neyin ne zaman döneceğini planlar.",
               "Start an exam; spaced repetition plans what comes back and when."),
             t("Öğrenci Takip → Sınav", "Student Tracker → Exam")),
            (t("İlerlemeni gör", "See your progress"),
             t("Bugün panosu, istatistikler ve yazdırılabilir haftalık özet.",
               "The Today dashboard, statistics and a printable weekly summary."),
             t("Öğrenci Takip → Bugün", "Student Tracker → Today")),
        ]
        h = '<div style="width:100%"><div class="flow">'
        for i, (b, d, w) in enumerate(adimlar, 1):
            if i > 1:
                h += '<div class="arrow">→</div>'
            h += f'<div class="step"><div class="k">{i}</div><h3>{b}</h3><p>{d}</p><div class="w">{w}</div></div>'
        h += ('</div><div class="band"><span class="lbl">' + t(
            "Takıldığında hep yanında:", "Whenever you get stuck:") + "</span>")
        for a in (t("Yapay zekâ öğretmen", "AI tutor"), t("Görsel Matematik", "Visual Math"),
                  t("Sözlük", "Dictionary"), t("Hesap makinesi", "Calculator"),
                  t("Çizim tahtası", "Drawing board"), t("Konu bilgisi", "Topic notes")):
            h += f'<span class="chip">{a}</span>'
        h += "</div></div>"
        self.slayt(h, t("Çalışma akışı", "Workflow"),
                   t("Tipik bir çalışma: beş adım", "A typical study session in five steps"),
                   t("Program bir kursu baştan sona takip etmen için kurgulandı: oku → biriktir "
                     "→ tekrar et → ölç.",
                     "The program is built around following a course end to end: read → "
                     "collect → review → measure."))

    def kaynaklar(self):
        t = self.t
        k1, k2 = (8, 150, 342, 760), (1256, 106, 340, 804)
        sol = self.shot("pdf.png", kirp=k1, genislik=216,
                        pinler=[(1, *self.kenar(k1, 248)), (2, *self.kenar(k1, 290)),
                                (3, *self.kenar(k1, 342, sag=True)),
                                (4, *self.kenar(k1, 866))],
                        kutular=[(304, 330, 26, 440)])
        orta = self.shot("pdf.png", kirp=k2, genislik=204,
                         pinler=[(5, *self.kenar(k2, 215)), (6, *self.kenar(k2, 824))])
        sag = self.legend([
            (t("Arama", "Search"),
             t("Yazdıkça ağaç süzülür; büyük bir kursta bile konunu hemen bulursun.",
               "The tree filters as you type, so even in a big course your topic is right "
               "there.")),
            (t("Ders ağacı", "Lesson tree"),
             t("Her şey iki kök altında: Dersler ve Soru Bankaları. Bitirdiğin dosyanın "
               "kutucuğunu işaretle; PDF açınca otomatik “Okunuyor” olur.",
               "Everything sits under two roots: Lessons and Question Banks. Tick a file when "
               "you finish it; opening a PDF marks it “Reading” automatically.")),
            (t("Konu bilgisi (i)", "Topic notes (i)"),
             t(f"{self.f['topic_knowledge_entries']} konu için yapay zekâsız, anında "
               "açıklama: günlük hayattan benzetme → nedir → ne işe yarar → varsa tarihçe.",
               f"Instant notes for {self.f['topic_knowledge_entries']} topics with no AI: an "
               "everyday analogy → what it is → what it is for → its history where there is "
               "any. (The notes are written in Turkish.)")),
            (t("Aç · Oku/Göster · Yazdır", "Open · Read/Show · Print"),
             t("Seçili dosyayı programda aç, klasörünü göster ya da yazdır.",
               "Open the selected file in the program, show its folder or print it.")),
            (t("Kurs Takibi", "Course Tracker"),
             t("Her kurs için kaç dosyayı bitirdiğin ve yüzde ilerleme; istersen elle "
               "ilerleme ve zorluk notu.",
               "How many files you finished in each course and the percentage, plus "
               "optional manual progress and difficulty notes.")),
            (t("İlerlemeyi Kaydet", "Save Progress"),
             t("Program son PDF'ini, sayfasını ve yakınlaştırmayı da hatırlar.",
               "The program also remembers your last PDF, its page and zoom.")),
        ], sinif="tight")
        self.slayt(f'<div style="display:flex;gap:34px;padding-left:8px">{sol}{orta}</div>'
                   f'<div style="flex:1">{sag}</div>',
                   t("Kurs kaynakları", "Course resources"),
                   t("Kendi kurs klasörün, düzenli bir ağaç olarak",
                     "Your own course folder, as a tidy tree"))

    def pdf(self):
        t = self.t
        k = (370, 150, 876, 760)
        sol = self.shot("pdf.png", kirp=k, genislik=560,
                        pinler=[(1, 690, 205), (2, 1170, 205), (3, 440, 385),
                                (4, *self.kenar(k, 300, sag=True))],
                        kutular=[(440, 385, 155, 75)])
        sag = self.legend([
            (t("Gezinme ve yakınlaştırma", "Navigation and zoom"),
             t("Sayfaya git, ileri/geri, yakınlaştır, Genişliğe Sığdır.",
               "Go to a page, previous/next, zoom in and out, Fit Width.")),
            (t("Not araçları", "Annotation tools"),
             t("Kalem, işaretleyici, metin ve silgi. Notlar ayrı bir dosyaya yazılır — "
               "orijinal PDF hiç değişmez.",
               "Pen, highlighter, text and eraser. Notes go to a separate sidecar file — "
               "the original PDF is never modified.")),
            (t("Soru Kırp", "Clip Question"),
             t("Sorunun etrafına dikdörtgen çiz: yüksek çözünürlükte kesilir; kurs, konu, "
               "zorluk ve şıklarla bankana girer. Kaynak PDF ve sayfa no otomatik saklanır.",
               "Drag a rectangle around a question: it is cut at high resolution and enters "
               "your bank with course, topic, difficulty and choices. The source PDF and page "
               "are stored automatically.")),
            (t("Yanında çizim tahtası", "A drawing board alongside"),
             t("Çözümü sayfanın yanında çiz; istersen gizle ya da ayrı pencerede aç.",
               "Work the solution out next to the page; hide it or pop it out.")),
        ])
        sag += ('<p class="cap" style="margin-top:16px">' + t(
            "İşaretli PDF'i dışa aktarabilir, yazdırabilir ya da paylaşabilirsin.",
            "You can export, print or share the annotated PDF.") + "</p>")
        self.slayt(f"<div style='width:560px'>{sol}</div><div style='flex:1'>{sag}</div>",
                   t("PDF okuyucu", "PDF reader"),
                   t("Oku, not al, soruyu kırp", "Read, annotate, clip the question"))

    def ai(self):
        t = self.t
        k = (372, 160, 872, 340)
        sol = self.shot("ai.png", kirp=k, genislik=600,
                        pinler=[(1, *self.kenar(k, 180)), (2, *self.kenar(k, 350)),
                                (3, 618, 396), (4, *self.kenar(k, 422)), (5, 920, 396)])
        sol += ('<div style="margin-top:18px;display:flex;align-items:center;gap:14px">'
                + self.shot("ai.png", kirp=(1296, 12, 296, 34), genislik=300)
                + '<p class="cap" style="margin:0;max-width:280px">' + t(
                    "Üst çubuktaki durum ışığı her 30 saniyede bir gerçekten yoklanır; "
                    "tıklayınca bağlantı testi açılır.",
                    "The status light in the top bar is genuinely polled every 30 seconds; "
                    "click it for a connection test.") + "</p></div>")
        sol += '<div style="margin-top:18px">' + self.dots([
            t("<b>Varsayılan sağlayıcı yereldir:</b> LM Studio kendi bilgisayarında çalışır, "
              "modele yalnızca senin seçtiğin metin ve bağlam gider.",
              "<b>The default provider is local:</b> LM Studio runs on your own computer, and "
              "the model only receives the text and context you selected."),
            t("<b>İsteğe bağlı:</b> yapay zekâ olmadan da PDF, notlar, soru bankası, sınavlar, "
              "lab'lar ve sözlük tam çalışır.",
              "<b>Optional:</b> without any AI the PDFs, notes, question bank, exams, labs and "
              "dictionary all work fully."),
        ], "small") + "</div>"
        sag = self.legend([
            (t("Sorunu yaz", "Type your question"),
             t("Anlamadığın soruyu ya da konuyu yaz.",
               "The problem or topic you don't understand.")),
            (t("Görsel ekle", "Attach an image"),
             t("Sorunun fotoğrafı ya da ekran görüntüsü: önce OCR denenir, gerekirse görsel "
               "modele gider.",
               "A photo or screenshot of the question: OCR is tried first, the vision model "
               "if needed.")),
            (t("Soruyu Çöz", "Solve Question"),
             t("Yanıt alttaki “AI / Çözücü Cevabı” alanına gelir.",
               "The answer appears in the “AI / Solver Answer” area below.")),
            (t("Seçili kaynağı sor", "Ask about the selected resource"),
             t("Ağaçta seçtiğin dosya hakkında soru sor.",
               "Ask about the file you selected in the tree.")),
            (t("Geri bildirim raporu", "Feedback report"),
             t("Soru, cevap ve kurs ilerlemesini sonraki adımlarla birlikte rapora döker.",
               "Turns the question, the answer and your course progress into a report with "
               "next steps.")),
            (t("Model profilleri", "Model profiles"),
             t("Matematik, görsel, kimya… her iş ona uygun modele yönlendirilir; bir model "
               "silinirse özellik bozulmaz, yalnızca kalite düşer.",
               "Maths, vision, chemistry… each job is routed to a suitable model; removing a "
               "model lowers quality instead of breaking the feature.")),
        ], sinif="tight")
        self.slayt(f"<div style='width:600px'>{sol}</div><div style='flex:1'>{sag}</div>",
                   t("Yapay zekâ öğretmen", "AI tutor"),
                   t("Takıldığında sor — yapay zekâ kendi bilgisayarında",
                     "Ask when you're stuck — the AI runs on your own computer"))

    def terminal(self):
        t = self.t
        kartlar = [
            self.card(t("İki sağlayıcı", "Two providers"),
                      t("<b>Yerel LM Studio</b> varsayılandır. <b>NVIDIA NIM</b> isteğe bağlıdır: "
                        "yalnızca o oturumda seçip onay penceresini kabul edersen kullanılır; "
                        "istekler NVIDIA tarafında loglanır ve pencere bunu açıkça yazar.",
                        "<b>Local LM Studio</b> is the default. <b>NVIDIA NIM</b> is optional: it "
                        "is only used if you pick it in that session and accept the consent "
                        "dialog; requests are logged on NVIDIA's side, and the window says so."),
                      t("Sağlayıcı", "Provider")),
            self.card(t("Onay kapısı", "The approval gate"),
                      t("Yapay zekânın yazdığı kodun tamamı ayrı bir pencerede gösterilir; sen "
                        "onaylamadan hiçbir şey çalışmaz. Bu sürümde kod çalıştırma "
                        "<b>varsayılan olarak kapalıdır</b>.",
                        "The complete code the AI wrote is shown in a separate window; nothing "
                        "runs until you approve it. In this release code execution is "
                        "<b>off by default</b>."),
                      t("Güvenlik", "Safety")),
            self.card(t("Çalışma tutanağı", "Work record"),
                      t("Biten her iş kalıcı, aranabilir bir kayda geçer: soru, yanıt, model, "
                        "süre — çalıştırıldıysa kod ve çıktısı. Metne aktar ya da panoya kopyala.",
                        "Every finished job goes into a permanent, searchable record: question, "
                        "answer, model, duration — plus code and output if it ran. Export it as "
                        "text or copy it."),
                      t("Hafıza", "Memory")),
            self.card(t("Token defteri", "Token ledger"),
                      t("Hangi model ne kadar çalıştı: bugün, 7 gün, 30 gün; modele, sağlayıcıya "
                        "ve güne göre. İstek metni saklanmaz, yalnızca sayaçlar. CSV'ye aktarılır.",
                        "Which model did how much work: today, 7 days, 30 days; by model, provider "
                        "and day. No request text is stored, only counters. Exports to CSV."),
                      t("Farkındalık", "Awareness")),
        ]
        h = ('<div style="width:100%"><div class="grid" style="grid-template-columns:1fr 1fr">'
             + "".join(kartlar) + '</div><div class="band" style="margin-top:18px">'
             '<span class="lbl">' + t("Kısayollar:", "Shortcuts:") + '</span>'
             '<span><span class="mono">Ctrl+Enter</span> ' + t("gönder", "send") + '</span>'
             '<span><span class="mono">Ctrl+L</span> ' + t("temizle", "clear") + '</span>'
             '<span><span class="mono">Esc</span> ' + t("durdur", "stop") + '</span>'
             '<span style="color:var(--muted);font-size:13.5px">' + t(
                 "API anahtarı yalnızca bu programın kendi Windows Kimlik Bilgisi kaydında "
                 "tutulur; ekranda son 4 karakteri görünür.",
                 "The API key is kept only in this program's own Windows Credential Manager "
                 "entry; the screen shows its last 4 characters.") + '</span></div></div>')
        self.slayt(h, t("AI Terminali", "AI Terminal"),
                   t("Kod yazdır — sen onaylamadan hiçbir şey çalışmaz",
                     "Have code written — nothing runs until you approve it"),
                   t("Ayarlar → AI Terminali: sympy çözümleri, matplotlib grafikleri ve küçük "
                     "yardımcı betikler için.",
                     "Settings → AI Terminal: for sympy solutions, matplotlib plots and small "
                     "helper scripts."))

    def takip(self):
        t = self.t
        k = (372, 152, 870, 520)
        sol = self.shot("takip.png", kirp=k, genislik=640,
                        pinler=[(1, *self.kenar(k, 177)), (2, *self.kenar(k, 300)),
                                (3, 548, 417), (4, *self.kenar(k, 484)),
                                (5, *self.kenar(k, 588))],
                        kutular=[(386, 280, 844, 168)])
        sol += ('<p class="cap">' + t(
            "Görüntü boş bir demo profilinden: veri yokken pano tahmin üretmez, bunu açıkça "
            "söyler.",
            "Captured on an empty demo profile: with no data the dashboard invents nothing — "
            "and says so.") + "</p>")
        sag = self.legend([
            (t("Altı alt sekme", "Six sub-tabs"),
             t("Bugün · Öğrenci · Soru Bankası · Soru Paketleri · Sınav · İstatistik",
               "Today · Learner · Question Bank · Question Packs · Exam · Statistics")),
            (t("Dört kart", "Four cards"),
             t("Tekrar vakti gelenler, yanlışlar, denenmemişler ve doğruluk oranı.",
               "Due for review, wrong answers, untried questions and accuracy.")),
            (t("Tek tıkla sınav", "One-click exam"),
             t("Kartın düğmesi o havuzdan hemen sınav başlatır.",
               "Each card's button starts an exam on that pool right away.")),
            (t("Bu Hafta önerileri", "This Week suggestions"),
             t("Verinden en fazla 3 gerekçeli öneri; kural tabanlı, yapay zekâ kullanılmaz. "
               "Örn. “Türev — son 12 denemede %41,7 doğruluk”.",
               "Up to three reasoned suggestions from your data; rule-based, no AI. "
               "E.g. “Derivatives — 41.7% over the last 12 attempts”.")),
            (t("Zayıf konular & ilerleme", "Weak topics & progress"),
             t("Önce neyi çalışman gerektiği ve her kursun çözüm durumu.",
               "What to study first, and how far each course has got.")),
        ], sinif="tight")
        self.slayt(f"<div style='width:640px'>{sol}</div><div style='flex:1'>{sag}</div>",
                   t("Öğrenci Takip", "Student Tracker"),
                   t("“Bugün ne çalışayım?” sorusunun on saniyelik cevabı",
                     "A ten-second answer to “what do I study today?”"))

    def sinav(self):
        t = self.t
        basamak = [(t("hemen", "at once"), 0, t("Yanlış", "Wrong")),
                   (t("1 gün", "1 day"), 1, "1."), (t("3 gün", "3 days"), 3, "2."),
                   (t("7 gün", "7 days"), 7, "3."), (t("14 gün", "14 days"), 14, "4."),
                   (t("30 gün", "30 days"), 30, "5."), (t("60 gün", "60 days"), 60, "6.+")]
        ladder = '<div class="ladder">'
        alt = '<div class="ladder-x">'
        for val, gun, lbl in basamak:
            yuk = 26 if gun == 0 else round(30 + 48 * math.log2(gun + 1))
            sinif = "rung wrong" if gun == 0 else "rung"
            ladder += f'<div class="{sinif}"><div class="val">{val}</div><div class="bar" style="height:{yuk}px"></div></div>'
            alt += f"<div>{lbl}</div>"
        ladder += "</div>"
        alt += "</div>"
        sol = (f'<div style="width:500px"><h3 style="font-size:18px;font-weight:600;margin-bottom:18px">'
               + t("Bir soru ne zaman geri gelir?", "When does a question come back?")
               + "</h3>" + ladder + alt
               + '<p class="cap" style="margin-top:14px">' + t(
                   "Alt eksen: üst üste doğru cevap sayısı. Tarih her sorunun kendi deneme "
                   "geçmişinden hesaplanır; Bugün panosu ve “Tekrar Vakti” havuzu bu kuyruğu okur.",
                   "Bottom axis: correct answers in a row. The date is computed from each "
                   "question's own attempt history; the Today dashboard and the “Due” pool both "
                   "read this queue.") + "</p></div>")
        sag = self.dots([
            t("<b>Soru ekle:</b> elle, toplu yapıştır (soru = cevap), CSV ya da PDF'ten Soru "
              "Kırp ile.",
              "<b>Add questions</b> by hand, by bulk paste (question = answer), from CSV, or "
              "with Clip Question from a PDF."),
            t("<b>Havuz seç:</b> Hepsi · Çözülmedi · Yanlış · Tekrar · Tekrar Vakti.",
              "<b>Pick a pool:</b> All · Untried · Wrong · Review · Due."),
            t("<b>Şıklı sorular</b> otomatik puanlanır. <b>Açık uçlularda</b> sympy eşdeğerliği "
              "tanır (0,5 = 1/2, 2x+2x = 4x) ve EŞLEŞTİ / EŞDEĞER / FARKLI önerir — son karar "
              "senin.",
              "<b>Multiple-choice</b> is graded automatically. For <b>open answers</b> sympy "
              "recognises equivalence (0.5 = 1/2, 2x+2x = 4x) and suggests MATCH / EQUIVALENT / "
              "DIFFERENT — you make the final call."),
            t("<b>Süreli mod:</b> geri sayım işler, son dakika kırmızıdır; süre bitince sınav "
              "kendini kapatır.",
              "<b>Timed mode:</b> a countdown runs, red in the last minute; when time is up the "
              "exam closes itself."),
            t("<b>Karalama alanı:</b> her sorunun altında fare ya da kalemle çalış.",
              "<b>Scratch pad:</b> work under every question with a mouse or pen."),
            t("<b>Sınav dökümü:</b> sonra satıra çift tıkla — ne yazdın, doğrusu neydi, ne "
              "kadar sürdü, soru soru.",
              "<b>Exam breakdown:</b> double-click a row afterwards — what you answered, the "
              "correct answer and the time spent, question by question."),
        ])
        self.slayt(f"{sol}<div style='flex:1;padding-top:4px'>{sag}</div>",
                   t("Sınav & tekrar", "Exams & review"),
                   t("Soru bankası, sınav ve aralıklı tekrar",
                     "Question bank, exams and spaced repetition"))

    def paketler(self):
        t = self.t
        kartlar = [
            self.card(t("Yerleşik soru üreteçleri", "Built-in question generators"),
                      t("Pre-Algebra, Cebir, Geometri, Lineer Cebir ve Calculus: soruyu ve kesin "
                        "cevabını üretir. Sınırsız, telifsiz, Türkçe ve İngilizce.",
                        "Pre-Algebra, Algebra, Geometry, Linear Algebra and Calculus: each "
                        "produces the question and its exact answer. Unlimited, licence-free, "
                        "Turkish and English."),
                      t("Soru Paketleri", "Question Packs")),
            self.card(t(".mcpack ile paylaş", "Share with .mcpack"),
                      t("Filtrelediğin soruları lisans ve atıfla tek dosyaya aktar; Soru Kırp ile "
                        "aldığın görselli sorular da taşınır. Arkadaşın tek tıkla içe aktarır.",
                        "Export the questions you filtered, with licence and attribution, into "
                        "one file; image questions you clipped travel too. A friend imports it "
                        "in one click."),
                      t("Paylaşım", "Sharing")),
            self.card(t("Haftalık özet raporu", "Weekly summary report"),
                      t("Tarayıcıda tek sayfa: çalışma günleri, çözülen soru, doğruluğun geçen "
                        "haftaya göre değişimi, zayıf konular, biten sınavlar. Renkli ya da gri "
                        "A4 PDF olarak kaydedilir.",
                        "One page in your browser: study days, questions answered, accuracy "
                        "against last week, weak topics, finished exams. Saves as a colour or "
                        "grayscale A4 PDF."),
                      t("Rapor", "Report")),
            self.card(t("İstatistik", "Statistics"),
                      t("Genel doğruluk, konu bazında ustalık tablosu, zayıf konular ve sınav "
                        "puanı eğilimi. Veri yoksa boş grafik çizilmez — “bu hafta veri yok” der.",
                        "Overall accuracy, a per-topic mastery table, weak topics and the exam "
                        "score trend. With no data it draws no empty chart — it says “no data "
                        "this week”."),
                      t("Ölçüm", "Measurement")),
        ]
        paketler = [
            ("Pre-Algebra", t("aritmetik, kesirler, yüzdeler, oranlar",
                              "arithmetic, fractions, percentages, ratios")),
            (t("Cebir", "Algebra"), t("denklemler, ikinci derece, sistemler, üsler",
                                      "equations, quadratics, systems, exponents")),
            (t("Geometri", "Geometry"), t("alan/çevre, Pisagor, çember",
                                          "area/perimeter, Pythagoras, circles")),
            (t("Lineer Cebir", "Linear Algebra"), t("determinant, matrisler, iç çarpım",
                                                    "determinants, matrices, dot product")),
            ("Calculus", t("eğim, türev", "slope, derivatives")),
        ]
        serit = ('<div class="grid" style="grid-template-columns:repeat(5,1fr);gap:10px;'
                 'margin-top:16px">' + "".join(
                     f'<div class="card" style="padding:12px 14px;background:var(--panel);'
                     f'border-color:var(--panel)"><h3 style="font-size:14.5px">{b}</h3>'
                     f'<p style="font-size:12.8px;margin-top:3px">{d}</p></div>'
                     for b, d in paketler) + "</div>")
        h = ('<div style="width:100%"><div class="grid" style="grid-template-columns:1fr 1fr">'
             + "".join(kartlar) + "</div>" + serit
             + '<p class="note" style="margin-top:14px">' + t(
                 "Telif kuralı: telifli soru bankaları programa gömülmez. Lisansı belirtilmeyen "
                 "harici paket UNKNOWN olarak işaretlenir ve içe aktarmadan önce uyarı verilir; "
                 "paketteki dosya yolları doğrulanır.",
                 "Licence rule: copyrighted question banks are never embedded. An external pack "
                 "with no licence is marked UNKNOWN and warned about before import, and file "
                 "paths inside a pack are validated.") + "</p></div>")
        self.slayt(h, t("Paketler & rapor", "Packs & reports"),
                   t("Sınırsız soru, paylaşılabilir paketler, haftalık rapor",
                     "Unlimited questions, shareable packs, a weekly report"))

    def gorsel(self):
        t = self.t
        k = (372, 152, 872, 750)
        sol = self.shot("visual.png", kirp=k, genislik=560,
                        pinler=[(1, *self.kenar(k, 176)), (2, *self.kenar(k, 220)),
                                (3, 1212, 262), (4, *self.kenar(k, 718)), (5, 1070, 650),
                                (6, *self.kenar(k, 456))])
        sag = self.legend([
            (t("Araç çubuğu", "Toolbar"),
             t("Yeni soru, görsel yükle, ekran görüntüsü yapıştır, Çöz, Görselleştir.",
               "New, load an image, paste a screenshot, Solve, Visualize.")),
            (t("Hazır örnekler", "Ready-made examples"),
             t("Bir örnek seç (ör. eğim + nokta) ya da kendi sorunu yaz / görsel ekle.",
               "Pick an example (e.g. slope + point) or type your own question / attach an "
               "image.")),
            (t("Grafik", "Graph"),
             t("matplotlib grafiği; PNG kaydet, ders kartı üret, ayrı pencerede aç.",
               "A matplotlib plot; save it as PNG, make a lesson card, pop it out.")),
            (t("Adım adım çözüm", "Step-by-step solution"),
             t("sympy ile: ne verildi → ne isteniyor → formül → işlem.",
               "With sympy: what is given → what is asked → formula → working.")),
            (t("Gerçek hayat açıklaması", "Real-life explanation"),
             t("Konu günlük bir benzetmeyle anlatılır: eğim = rampanın dikliği.",
               "The topic told through an everyday picture: slope = how steep a ramp is.")),
            (t("Simülasyon Stüdyosu", "Simulation Studio"),
             t(f"{self.f['embedded_simulations']} gömülü etkileşimli simülasyon ve "
               f"{self.f['formula_cards']} formül kartı; kurs klasöründen üretilenler de "
               "listeye eklenir.",
               f"{self.f['embedded_simulations']} embedded interactive simulations and "
               f"{self.f['formula_cards']} formula cards; ones built from your course folder "
               "are added to the list.")),
        ], sinif="tight")
        self.slayt(f"<div style='width:560px'>{sol}</div><div style='flex:1'>{sag}</div>",
                   t("Görsel Matematik", "Visual Math"),
                   t("Cevabı değil, yolu gör", "See the path, not just the answer"))

    def lablar(self):
        t = self.t
        k = (372, 152, 872, 400)
        sol = self.shot("lab.png", kirp=k, genislik=580,
                        pinler=[(1, *self.kenar(k, 178)), (2, 600, 271), (3, 1058, 298),
                                (4, *self.kenar(k, 400))])
        sol += '<div style="margin-top:18px">' + self.legend([
            (t("Beş lab, tek sekmede", "Five labs, one tab"),
             t("Veri · Fizik · Kimya · DNA · Kuantum iç sekmeleri.",
               "Inner tabs for Data · Physics · Chemistry · DNA · Quantum.")),
            (t("Olayı seç", "Pick a phenomenon"),
             t("Ör. atış hareketi; varsayılan değerleri yükle.",
               "E.g. projectile motion; load the default values.")),
            (t("Matematiğe Dönüştür", "Convert to maths"),
             t("Olay denkleme, vektöre, fonksiyona ya da diferansiyel denkleme çevrilir.",
               "The phenomenon becomes an equation, vector, function or differential "
               "equation.")),
            (t("Parametreler", "Parameters"),
             t("Her satıra anahtar=değer yaz (v0=20, theta=45…).",
               "One key=value per line (v0=20, theta=45…).")),
        ], sinif="tight") + "</div>"
        lablar = [
            (t("Veri Lab'ı", "Data Lab"),
             t("Görüntü, metin, ses ve video verisini vektör, matris, tensör, frekans ve "
               "gömmelere çevirir.",
               "Turns image, text, audio and video data into vectors, matrices, tensors, "
               "frequencies and embeddings.")),
            (t("Fizik Lab'ı", "Physics Lab"),
             t("Hareket, Newton, atış, harmonik hareket, dalgalar, elektrik alanı.",
               "Motion, Newton, projectiles, harmonics, waves, electric field.")),
            (t("Kimya Lab'ı", "Chemistry Lab"),
             t("İdeal gaz, hız yasası, pH, bozunma, difüzyon, tamponlar; periyodik tablo, mol "
               "ve stokiyometri.",
               "Ideal gas, rate law, pH, decay, diffusion, buffers; periodic table, moles and "
               "stoichiometry.")),
            (t("DNA Lab'ı", "DNA Lab"),
             t("DNA ↔ matematik: dizi, vektör, k-mer, bilgi; kodon tablosu; dijital veri → DNA.",
               "DNA ↔ maths: string, vector, k-mer, information; codon table; digital data → "
               "DNA.")),
            (t("Kuantum", "Quantum"),
             t("Kübit, kapılar, ölçüm, dolanıklık (Bell), QFT, Grover — vektör ve matris "
               "diliyle.",
               "Qubits, gates, measurement, entanglement (Bell), QFT, Grover — in the language "
               "of vectors and matrices.")),
        ]
        sag = '<div class="grid" style="gap:10px">' + "".join(
            f'<div class="card" style="padding:13px 16px"><h3 style="font-size:15px">{b}</h3>'
            f'<p style="margin-top:3px;font-size:13px">{d}</p></div>' for b, d in lablar) + "</div>"
        if self.dil == "en":
            sag += ('<p class="note" style="margin-top:10px">Note: the labs\' interface labels '
                    'are still in Turkish.</p>')
        self.slayt(f"<div style='width:580px'>{sol}</div><div style='flex:1'>{sag}</div>",
                   t("Bilim lab'ları", "Science labs"),
                   t("Beş bilim laboratuvarı — ortak fikir: konuyu matematiğe çevirmek",
                     "Five science labs — one idea: turn the subject into maths"))

    def sozluk(self):
        t = self.t
        k = (372, 152, 872, 640)
        sol = self.shot("sozluk.png", kirp=k, genislik=580,
                        pinler=[(1, *self.kenar(k, 183)), (2, *self.kenar(k, 222)),
                                (3, *self.kenar(k, 268)), (4, 759, 670)])
        sag = self.legend([
            (t("Dokuz alt sekme", "Nine sub-tabs"),
             t("Sözlük, cümle ve görsel çeviri, PDF terimleri, PDF kelime tarayıcı, geçmiş, "
               "sıklık, favoriler, model profilleri.",
               "Dictionary, sentence and image translation, PDF terms, PDF vocabulary scanner, "
               "history, frequency, favourites, model profiles.")),
            (t("Kaynak → hedef dil", "Source → target language"),
             t("İngilizce ↔ Türkçe ara; beğendiğini favorilere ekle.",
               "Search English ↔ Turkish; add what you need to your favourites.")),
            (t("Terim listesi", "Term list"),
             t("Terim ve karşılığı; seçince ayrıntısı yanda açılır.",
               "Term and translation; select one to see its details alongside.")),
            (t("Kelimeyi yapay zekâya sor", "Ask the AI about a word"),
             t("“graph ile chart arasındaki fark nedir?” — bir kelimenin matematikteki "
               "anlamını sor.",
               "“What is the difference between graph and chart?” — ask what a word means in "
               "maths.")),
        ])
        sag += '<div style="margin-top:20px">' + self.dots([
            t("<b>PDF kelime tarayıcı:</b> bütün bir PDF'teki yabancı kelimeleri tek seferde "
              "çıkarır.",
              "<b>PDF vocabulary scanner:</b> pulls the unfamiliar words out of a whole PDF "
              "at once."),
            t("<b>Görsel/OCR çeviri:</b> ekran görüntüsündeki metni okur ve çevirir.",
              "<b>Image/OCR translation:</b> reads and translates the text in a screenshot."),
        ], "small") + "</div>"
        self.slayt(f"<div style='width:580px'>{sol}</div><div style='flex:1'>{sag}</div>",
                   t("Sözlük", "Dictionary"),
                   t("Dil & Bilim Sözlüğü: İngilizce bir kursta kelime engeline takılma",
                     "Language & Science Dictionary: get past the vocabulary barrier"))

    def hesap_tahta(self):
        t = self.t
        k1, k2 = (376, 160, 862, 560), (374, 156, 866, 560)
        hesap = self.shot("hesap.png", kirp=k1, genislik=540,
                          pinler=[(1, *self.kenar(k1, 443)), (2, 620, 391), (3, 1060, 228),
                                  (4, 702, 664)])
        tahta = self.shot("tahta.png", kirp=k2, genislik=540,
                          pinler=[(5, *self.kenar(k2, 213)), (6, 935, 253), (7, 855, 173)])
        sol = hesap + '<div style="margin-top:16px">' + self.legend([
            (t("Tuş takımı", "Keypad"),
             t("Kesir duyarlı (3/4 + 2/5 → tam kesir); sqrt, log, sin…",
               "Fraction-aware (3/4 + 2/5 → an exact fraction); sqrt, log, sin…")),
            (t("RAD / DEG · Açıkla", "RAD / DEG · Explain"),
             t("Açı birimini seç; sonucu açıklat.", "Pick the angle unit; have the result "
               "explained.")),
            (t("Geçmiş & eğitim notu", "History & study note"),
             t("Her hesap kaydedilir; kullanım ipuçları yanda.",
               "Every calculation is kept; usage tips alongside.")),
            (t("Yapay zekâya sor", "Ask the AI"),
             t("“200'e %15 KDV ekle”, “x²−5x+6=0 çöz”.",
               "“Add 15% VAT to 200”, “solve x²−5x+6=0”.")),
        ], sinif="compact") + "</div>"
        sag = tahta + '<div style="margin-top:16px">' + self.legend([
            (t("Çizim araçları", "Drawing tools"),
             t("Kalem, silgi, çizgi, ok, dikdörtgen, çember, üçgen, metin; ızgara ve koordinat.",
               "Pen, eraser, line, arrow, rectangle, circle, triangle, text; grid and axes.")),
            (t("Ne çizdim? · Adım adım açıkla", "What did I draw? · Explain step by step"),
             t("Çizimin görsel modele gider ve yorumlanır: çözümünü kontrol ettir.",
               "Your drawing goes to the vision model and is interpreted — get your working "
               "checked.")),
            (t("Gönder · Kaydet", "Send · Save"),
             t("AI öğretmene gönder ya da PNG olarak kaydet. Fare, kalemli ekran ya da çizim "
               "tableti.",
               "Send it to the AI tutor or save it as PNG. Mouse, pen display or graphics "
               "tablet.")),
        ], ilk=5, sinif="compact") + "</div>"
        self.slayt(f"<div style='width:540px'>{sol}</div><div style='width:540px'>{sag}</div>",
                   t("Hesap & tahta", "Calculator & board"),
                   t("Bilimsel hesap makinesi ve tablet çizim tahtası",
                     "A scientific calculator and a tablet drawing board"))

    def ayarlar(self):
        t = self.t
        serit = self.shot("ai.png", kirp=(0, 58, 1600, 42), genislik=1152)
        kartlar = [
            self.card(t("Türkçe / English", "Türkçe / English"),
                      t("Arayüz, kılavuz ve yapay zekâya giden sistem talimatı seçtiğin dile geçer.",
                        "The interface, the guide and the system instruction sent to the AI all "
                        "switch to the language you choose.")),
            self.card(t("Koyu tema", "Dark theme"),
                      t("Gece çalışması için sıcak bir koyu palet (yeniden başlatınca uygulanır). "
                        "PDF sayfaları kâğıt gibi açık kalır.",
                        "A warm dark palette for night study (applied on restart). PDF pages stay "
                        "light, like paper.")),
            self.card(t("X Düzeni", "X Layout"),
                      t("Klasik, ayna ya da iki bağımsız PDF penceresi: dersle çözümü yan yana aç.",
                        "Classic, mirrored or two independent PDF windows: put the lesson and the "
                        "solution side by side.")),
            self.card(t("Açılış ekranı", "Startup screen"),
                      t("Son oturumdan devam et (son PDF sayfası ve yakınlaştırma dâhil) ya da "
                        "doğrudan Bugün panosuyla aç.",
                        "Carry on from your last session (last PDF page and zoom included) or "
                        "open straight on the Today dashboard.")),
            self.card(t("Kullanma kılavuzu", "User guide"),
                      t(f"Ayarlar → Kullanma Kılavuzu: {self.f['guide_chapters']} bölüm, "
                        "program içinde, Türkçe ve İngilizce.",
                        f"Settings → User Guide: {self.f['guide_chapters']} chapters inside the "
                        "program, in Turkish and English.")),
            self.card(t("Hafif açılış", "Light start-up"),
                      t("Paneller ilk kullanıldıklarında kurulur; hiç açmadığın lab programı "
                        "yavaşlatmaz.",
                        "Panels are built the first time you use them; a lab you never open never "
                        "slows the program down.")),
        ]
        h = ('<div style="width:100%">' + serit + '<p class="cap">' + t(
            f"Çalışma alanı şeridi: kullanmadığın alanı × ile gizle; Çalışma Alanı Yöneticisi'nden "
            f"{self.f['workspaces']} alanın hepsini tek listeden yönet.",
            f"The workspace strip: hide what you don't use with ×; manage all "
            f"{self.f['workspaces']} workspaces from one list in the Workspace Manager.")
            + '</p><div class="grid" style="grid-template-columns:repeat(3,1fr);margin-top:18px">'
            + "".join(kartlar) + "</div></div>")
        self.slayt(h, t("Kişiselleştirme", "Make it yours"),
                   t("Programı kendi çalışma düzenine göre ayarla",
                     "Shape the program around the way you study"))

    def gizlilik(self):
        t = self.t
        sol = (f'<div class="card accent" style="flex:1"><span class="tag">'
               + t("Varsayılan olarak", "By default") + '</span>' + self.dots([
                   t("Yapay zekâ <b>yereldir</b>: LM Studio kendi bilgisayarında çalışır.",
                     "The AI is <b>local</b>: LM Studio runs on your own computer."),
                   t("Çalışma verilerin (öğrenci, cevaplar, süreler, notlar) yerel bir SQLite "
                     "veritabanında durur — Windows'ta <span class='mono'>%APPDATA%\\MathCourseAI</span>.",
                     "Your study data (learner, answers, timings, notes) stays in a local SQLite "
                     "database — on Windows under <span class='mono'>%APPDATA%\\MathCourseAI</span>."),
                   t("Hesap, giriş ya da sunucu yok. Telemetri, analitik ve güncelleme kontrolü "
                     "yok.",
                     "No account, no login, no server. No telemetry, no analytics, no update "
                     "check."),
                   t("Kurs içeriği dağıtılmaz: kendi materyalini sen getirirsin.",
                     "No course content is shipped: you bring your own material."),
               ], "mid") + "</div>")
        sag = (f'<div class="card" style="flex:1"><span class="tag">'
               + t("Bilmen gerekenler", "Good to know") + '</span>' + self.dots([
                   t("Bulut sağlayıcı (NVIDIA NIM) <b>isteğe bağlıdır</b>: yalnızca AI "
                     "Terminali'nde o oturumda seçip onay verirsen kullanılır. O zaman istemin ve "
                     "son 12 tur NVIDIA'ya gider ve orada loglanır.",
                     "The cloud provider (NVIDIA NIM) is <b>optional</b>: it is only used if you "
                     "pick it in the AI Terminal in that session and give consent. Then your "
                     "prompt and the last 12 turns go to NVIDIA and are logged there."),
                   t("Yapay zekânın yazdığı kod sen onaylamadan çalışmaz; bu sürümde kod "
                     "çalıştırma varsayılan olarak kapalıdır.",
                     "Code the AI writes never runs without your approval; in this release code "
                     "execution is off by default."),
                   t("Bir öğrenciyi silmek, sınav cevapları dâhil ona ait tüm kayıtları siler.",
                     "Deleting a learner erases every record belonging to them, exam answers "
                     "included."),
                   t("Yapay zekâ cevapları yanlış olabilir — her zaman kontrol et.",
                     "AI answers can be wrong — always check them."),
               ], "mid") + "</div>")
        sema = (
            '<div class="flowmap"><div class="home"><span class="lbl">'
            + t("Senin bilgisayarın", "Your computer") + '</span><div class="row">'
            '<div class="node"><h3>Math Course AI</h3><p>'
            + t("PDF'ler · notlar · soru bankası · çalışma geçmişi",
                "PDFs · notes · question bank · study history") + '</p></div>'
            '<div class="link"><span>' + t("varsayılan", "default") + '</span>'
            '<div class="line"></div></div>'
            '<div class="node"><h3>LM Studio</h3><p>'
            + t("yerel model · 127.0.0.1", "local model · 127.0.0.1") + '</p></div>'
            '</div></div>'
            '<div class="link gate"><span>' + t("onay — yalnızca o oturum",
                                                "consent — this session only")
            + '</span><div class="line"></div></div>'
            '<div class="node cloud"><h3>NVIDIA NIM</h3><p>'
            + t("isteğe bağlı bulut · yalnızca AI Terminali",
                "optional cloud · AI Terminal only") + '</p></div></div>')
        self.slayt(f'<div style="width:100%">{sema}<div style="display:flex;gap:28px;'
                   f'margin-top:22px">{sol}{sag}</div></div>', t("Gizlilik", "Privacy"),
                   t("Varsayılan yerel — bulut yalnızca senin onayınla",
                     "Local by default — cloud only with your consent"),
                   t("Ayrıntılar depodaki PRIVACY.md ve AI_TRANSPARENCY.md dosyalarında.",
                     "Details are in PRIVACY.md and AI_TRANSPARENCY.md in the repository."))

    def baslarken(self):
        t = self.t
        indir = self.card(
            t("1 · İndir ve çalıştır", "1 · Download and run"),
            t(f"<b>Windows 10/11 (x64):</b> Math Course AI-Windows.zip → bir klasöre çıkar → "
              f"<i>Math Course AI.exe</i>.<br><br><b>macOS (Apple Silicon):</b> Math Course "
              f"AI-macOS.zip → çıkar → ilk açılışta sağ tık → <i>Aç</i> (notarize edilmemiştir)."
              f"<br><br><b>İndirme:</b> {REPO}/releases ({RELEASE})<br><br><b>Kaynaktan:</b> "
              f"Python 3.11 · <span class='mono'>pip install -r requirements.txt</span> · "
              f"<span class='mono'>python Math_Course_AI.pyw</span>",
              f"<b>Windows 10/11 (x64):</b> Math Course AI-Windows.zip → extract to a folder → "
              f"<i>Math Course AI.exe</i>.<br><br><b>macOS (Apple Silicon):</b> Math Course "
              f"AI-macOS.zip → extract → first launch: right-click → <i>Open</i> (not notarised)."
              f"<br><br><b>Download:</b> {REPO}/releases ({RELEASE})<br><br><b>From source:</b> "
              f"Python 3.11 · <span class='mono'>pip install -r requirements.txt</span> · "
              f"<span class='mono'>python Math_Course_AI.pyw</span>"))
        ilk = self.card(
            t("2 · İlk 10 dakika", "2 · The first 10 minutes"),
            t("① Kurs PDF'lerini <i>Resources</i> klasörüne koy ya da Gözat ile seç.<br>"
              "② Ağaçta bir PDF'e çift tıkla.<br>③ Soru Kırp ile bir soruyu bankana al.<br>"
              "④ Öğrenci Takip → Sınav ile başla.<br><br><b>PDF'in yok mu?</b> Soru Paketleri'nden "
              "yerleşik bir üreteci içe aktar ve hemen çalış.",
              "① Put your course PDFs into <i>Resources</i>, or pick a folder with Browse.<br>"
              "② Double-click a PDF in the tree.<br>③ Bank a question with Clip Question.<br>"
              "④ Start with Student Tracker → Exam.<br><br><b>No PDFs?</b> Import a built-in "
              "generator from Question Packs and start straight away."))
        ai = self.card(
            t("3 · Yapay zekâyı aç (isteğe bağlı)", "3 · Turn on the AI (optional)"),
            t("① lmstudio.ai'den LM Studio'yu kur.<br>② Bir model indir (ör. "
              "qwen2.5-math-7b-instruct).<br>③ LM Studio'da sunucuyu başlat: "
              "<span class='mono'>127.0.0.1:1234</span><br>④ Ayarlar → model profilleri ya da "
              "“Yüklü Modelleri Otomatik Algıla”.<br><br>Üst çubuktaki ışık yeşile döner.",
              "① Install LM Studio from lmstudio.ai.<br>② Download a model (e.g. "
              "qwen2.5-math-7b-instruct).<br>③ Start the server in LM Studio: "
              "<span class='mono'>127.0.0.1:1234</span><br>④ Settings → model profiles, or "
              "“Auto Detect Loaded Models”.<br><br>The light in the top bar turns green."))
        h = (f'<div style="width:100%"><div class="grid" style="grid-template-columns:1.25fr 1fr 1fr">'
             f'{indir}{ilk}{ai}</div><div class="band"><span class="lbl">'
             + t("Takılırsan:", "If you get stuck:") + "</span><span>" + t(
                 f"Ayarlar → Kullanma Kılavuzu ({self.f['guide_chapters']} bölüm) içindeki "
                 "<b>Sorun Giderme</b> bölümü · <b>Hakkında</b> penceresi sürümü ve kısayolları "
                 "gösterir.",
                 f"Settings → User Guide ({self.f['guide_chapters']} chapters), chapter "
                 "<b>Troubleshooting</b> · the <b>About</b> window shows your version and the "
                 "shortcuts.") + "</span></div></div>")
        self.slayt(h, t("Başlarken", "Getting started"),
                   t("Üç adımda çalışmaya başla", "Up and running in three steps"))

    def kapanis(self):
        t = self.t
        h = ('<div style="width:100%;display:flex;flex-direction:column;justify-content:center">'
             '<div class="logo" style="width:64px;height:64px;font-size:38px">Σ</div>'
             '<h2 style="margin-top:26px">Math Course AI</h2>'
             '<p class="lead" style="max-width:860px">' + t(
                 "Oku · Not al · Soruları biriktir · Tekrar et · Takıldığında sor — hepsi tek "
                 "pencerede, yapay zekâ varsayılan olarak kendi bilgisayarında.",
                 "Read · Annotate · Collect questions · Review · Ask when stuck — all in one "
                 "window, with the AI on your own computer by default.") + "</p>"
             '<div class="chips"><span class="chip on">' + REPO + '</span>'
             f'<span class="chip">{RELEASE} · {self.surum}</span>'
             '<span class="chip">' + t("Kaynak kod: MIT", "Source code: MIT") + '</span>'
             '<span class="chip">' + t("Beta · kişisel proje", "Beta · personal project")
             + '</span></div>'
             '<div class="grid" style="grid-template-columns:repeat(3,1fr);margin-top:40px;max-width:1000px">'
             + self.card(t("Kimin için?", "Who is it for?"),
                         t("Bir matematik kursunu kendi başına takip eden, sınava hazırlanan ya da "
                           "konularını düzenli tekrar etmek isteyen herkes.",
                           "Anyone following a maths course on their own, preparing for an exam, "
                           "or wanting to review topics regularly."))
             + self.card(t("Ne gerekir?", "What do you need?"),
                         t("Windows 10/11 ya da Apple Silicon Mac ve kendi kurs PDF'lerin — ya da "
                           "yerleşik soru üreteçleri.",
                           "Windows 10/11 or an Apple Silicon Mac and your own course PDFs — or "
                           "the built-in question generators."))
             + self.card(t("Ne değildir?", "What it is not"),
                         t("Not veren ya da sertifika veren bir sistem değildir; kurs içeriği "
                           "dağıtmaz. Yapay zekâ cevaplarını kontrol et.",
                           "It does not grade or certify you and ships no course content. Check "
                           "the AI's answers."))
             + "</div></div>")
        self.slayt(h, t("Özet", "Summary"), sinif="closing")

    def uret(self):
        for adim in (self.kapak, self.neden, self.bakis, self.anatomi, self.akis,
                     self.kaynaklar, self.pdf, self.ai, self.terminal, self.takip, self.sinav,
                     self.paketler, self.gorsel, self.lablar, self.sozluk, self.hesap_tahta,
                     self.ayarlar, self.gizlilik, self.baslarken, self.kapanis):
            adim()
        toplam = str(len(self.slaytlar))
        govde = "\n".join(s.replace("__TOPLAM__", toplam) for s in self.slaytlar)
        baslik = self.t("Math Course AI — Tanıtım", "Math Course AI — Introduction")
        return (f'<!doctype html><html lang="{self.dil}"><head><meta charset="utf-8">'
                f"<title>{baslik}</title><style>{_font_face_css()}\n{CSS}</style></head>"
                f"<body>{govde}</body></html>")


# ══════════════════════════════════════════════════════════════════════════
# Rendering
# ══════════════════════════════════════════════════════════════════════════
def tarayici_bul():
    """A Chromium-family browser that can print to PDF headless."""
    aday = [os.environ.get("MCA_CHROMIUM")]
    for ad in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable",
               "chrome", "msedge", "microsoft-edge"):
        aday.append(shutil.which(ad))
    pw = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    aday += [str(p) for p in sorted(pw.glob("chromium-*/chrome-linux/chrome"), reverse=True)]
    for kok in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if kok:
            aday.append(str(Path(kok) / "Microsoft" / "Edge" / "Application" / "msedge.exe"))
            aday.append(str(Path(kok) / "Google" / "Chrome" / "Application" / "chrome.exe"))
    aday.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    aday.append("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")
    for a in aday:
        if a and Path(a).is_file():
            return a
    return None


def pdf_yaz(html, cikti, tarayici):
    cikti = Path(cikti)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mcai-tur-") as tmp:
        sayfa = Path(tmp) / "deck.html"
        sayfa.write_text(html, encoding="utf-8")
        komut = [tarayici, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                 "--allow-file-access-from-files", "--virtual-time-budget=15000",
                 f"--user-data-dir={Path(tmp) / 'profile'}",
                 f"--print-to-pdf={cikti}", sayfa.as_uri()]
        if sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0:
            komut.insert(1, "--no-sandbox")
        subprocess.run(komut, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=180)
    if not cikti.is_file() or cikti.stat().st_size < 50_000:
        raise RuntimeError(f"PDF üretilemedi / PDF was not produced: {cikti}")
    return cikti


def main(argv):
    import measure_facts
    olcum = measure_facts.measure()

    diller = ["tr"] if "--tr" in argv else ["en"] if "--en" in argv else ["tr", "en"]
    tarayici = tarayici_bul()
    if not tarayici:
        print("[HATA] Chromium/Chrome/Edge bulunamadı — MCA_CHROMIUM ile yolu verin.\n"
              "[ERROR] No Chromium/Chrome/Edge found — point MCA_CHROMIUM at one.")
        return 2
    print("Math Course AI — newcomer tour deck")
    for dil in diller:
        deste = Deste(dil, olcum)
        html = deste.uret()
        hedef = CIKTI_KLASOR / ADLAR[dil]
        pdf_yaz(html, hedef, tarayici)
        if "--html" in argv:
            hedef.with_suffix(".html").write_text(html, encoding="utf-8")
        print(f"  [OK] {hedef.relative_to(ROOT)}  ({len(deste.slaytlar)} slides, "
              f"{hedef.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
