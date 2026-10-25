# -*- coding: utf-8 -*-
"""Math Course AI — tek PDF katmanı (görüntüleme + metin).

Neden: PyMuPDF (fitz) AGPL-3.0'dır ve yayımlanan Windows/macOS paketlerine
bilerek konmaz (THIRD_PARTY_NOTICES.md §1). Önceki sürümlerde bu yüzden
paketlenmiş programda PDF sayfaları HİÇ görünmüyordu ("PDF rendering
requires PyMuPDF"). Bu modül sırayla şu arka uçları dener:

  1. PyMuPDF   — kullanıcı kendisi kurduysa (kaynaktan çalıştırma)
  2. pypdfium2 — Google'ın PDFium motoru; Apache-2.0 / BSD-3. Paketlerde bu var.
  3. pypdf     — BSD-3, saf Python; yalnızca METİN (sayfa çizemez)

Arayüz fitz'e benzer ve küçüktür:

    doc = open_pdf(path)        # len(doc), doc[i], for page in doc, with ...
    page.size                   # (genişlik, yükseklik) PDF puntosu
    page.render(zoom, clip)     # PIL.Image (zoom=1 -> 72 dpi; clip=(x1,y1,x2,y2) punto)
    page.get_text()             # düz metin
"""

from __future__ import annotations

import threading
from pathlib import Path

try:
    import fitz  # PyMuPDF — isteğe bağlı (AGPL), dağıtılan paketlerde YOK
except Exception:  # pragma: no cover - ortama bağlı
    fitz = None

try:
    import pypdfium2 as _pdfium  # Apache-2.0 OR BSD-3-Clause (PDFium: BSD-3)
except Exception:  # pragma: no cover - ortama bağlı
    _pdfium = None

try:
    import pypdf as _pypdf  # BSD-3-Clause, yalnızca metin
except Exception:  # pragma: no cover - ortama bağlı
    _pypdf = None

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

# PDFium iş parçacığı güvenli değildir: tüm çağrılar tek kilitten geçer.
_LOCK = threading.RLock()


def render_backend():
    """Sayfa ÇİZEBİLEN arka ucun adı ya da None."""
    if Image is None:
        return None
    if fitz is not None:
        return "pymupdf"
    if _pdfium is not None:
        return "pdfium"
    return None


def text_backend():
    if fitz is not None:
        return "pymupdf"
    if _pdfium is not None:
        return "pdfium"
    if _pypdf is not None:
        return "pypdf"
    return None


def can_render():
    return render_backend() is not None


def can_extract_text():
    return text_backend() is not None


# ══════════════════════════════════════════════════════════════════════════
class _Page:
    def __init__(self, doc, index):
        self._doc = doc
        self.index = index

    @property
    def size(self):
        return self._doc._size(self.index)

    def render(self, zoom=1.0, clip=None):
        return self._doc._render(self.index, zoom, clip)

    def get_text(self, *_a, **_k):
        return self._doc._text(self.index)


class PdfDoc:
    def __init__(self, path, backend=None):
        self.path = Path(path)
        self.backend = backend or text_backend()
        if self.backend is None:
            raise RuntimeError("PDF desteği yok: pip install pypdfium2 (veya pypdf / PyMuPDF)")
        with _LOCK:
            if self.backend == "pymupdf":
                self._d = fitz.open(str(self.path))
            elif self.backend == "pdfium":
                self._d = _pdfium.PdfDocument(str(self.path))
            elif self.backend == "pypdf":
                self._d = _pypdf.PdfReader(str(self.path))
            else:
                raise ValueError(f"bilinmeyen PDF arka ucu: {backend}")

    # ---- container protocol ------------------------------------------------
    def __len__(self):
        with _LOCK:
            if self.backend == "pypdf":
                return len(self._d.pages)
            return len(self._d)

    def __getitem__(self, index):
        n = len(self)
        if index < 0:
            index += n
        if not 0 <= index < n:
            raise IndexError(index)
        return _Page(self, index)

    def __iter__(self):
        for i in range(len(self)):
            yield _Page(self, i)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        with _LOCK:
            try:
                if self.backend in ("pymupdf", "pdfium"):
                    self._d.close()
            except Exception:
                pass

    # ---- backend specific --------------------------------------------------
    def _size(self, i):
        with _LOCK:
            if self.backend == "pymupdf":
                r = self._d[i].rect
                return float(r.width), float(r.height)
            if self.backend == "pdfium":
                w, h = self._d[i].get_size()
                return float(w), float(h)
            box = self._d.pages[i].mediabox
            return float(box.width), float(box.height)

    def _render(self, i, zoom, clip):
        if Image is None:
            raise RuntimeError("Pillow yok")
        zoom = float(zoom)
        with _LOCK:
            if self.backend == "pymupdf":
                kw = {}
                if clip:
                    kw["clip"] = fitz.Rect(*clip)
                pix = self._d[i].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False, **kw)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                return img
            if self.backend == "pdfium":
                page = self._d[i]
                img = page.render(scale=zoom).to_pil().convert("RGB")
            else:
                raise RuntimeError("Bu PDF arka ucu sayfa çizemez (yalnızca metin): pip install pypdfium2")
        if clip:
            x1, y1, x2, y2 = clip
            box = (max(0, int(round(min(x1, x2) * zoom))), max(0, int(round(min(y1, y2) * zoom))),
                   min(img.width, int(round(max(x1, x2) * zoom))),
                   min(img.height, int(round(max(y1, y2) * zoom))))
            img = img.crop(box)
        return img

    def _text(self, i):
        with _LOCK:
            try:
                if self.backend == "pymupdf":
                    return self._d[i].get_text("text") or ""
                if self.backend == "pdfium":
                    page = self._d[i]
                    tp = page.get_textpage()
                    try:
                        txt = tp.get_text_bounded() or ""
                    finally:
                        tp.close()
                    return txt.replace("\r\n", "\n")
                return self._d.pages[i].extract_text() or ""
            except Exception:
                return ""


def open_pdf(path, for_render=False):
    """PDF'i açar. for_render=True ise yalnızca sayfa çizebilen arka uç seçilir."""
    backend = render_backend() if for_render else text_backend()
    if backend is None:
        raise RuntimeError(
            "PDF görüntüleme için pypdfium2 gerekir: pip install pypdfium2" if for_render
            else "PDF metni için pypdfium2, pypdf veya PyMuPDF gerekir: pip install pypdfium2")
    return PdfDoc(path, backend)


def page_texts(path, max_pages=60):
    """[(sayfa_no, metin), ...] — hata olursa o ana kadar okunanlar."""
    out = []
    try:
        with open_pdf(path) as doc:
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                out.append((i + 1, page.get_text()))
    except Exception:
        return out
    return out


def status_text(lang="tr"):
    rb, tb = render_backend(), text_backend()
    names = {"pymupdf": "PyMuPDF", "pdfium": "PDFium (pypdfium2)", "pypdf": "pypdf"}
    if lang == "en":
        return (f"PDF rendering: {names.get(rb, 'not available')} · "
                f"text: {names.get(tb, 'not available')}")
    return (f"PDF görüntüleme: {names.get(rb, 'yok')} · metin: {names.get(tb, 'yok')}")
