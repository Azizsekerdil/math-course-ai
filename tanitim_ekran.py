# -*- coding: utf-8 -*-
"""Math Course AI — tanıtım sunumu için ekran görüntülerini GERÇEK programdan çeker.

`tanitim_icerik.py`'deki "gorsel"/"galeri" slaytları bu betiğin ürettiği
PNG'leri kullanır. Görseller mock-up değildir: program bu betikle gerçekten
başlatılır, sekme sekme gezilir ve pencere fotoğraflanır — sunumda görünen
arayüz ile kullanıcının göreceği arayüz TANIM GEREĞİ aynıdır.

Çıktı:  tanitim_gorseller/tr/*.png  ve  tanitim_gorseller/en/*.png
Kullanım:  python tanitim_ekran.py

Notlar:
  * Süreç DPI-aware yapılır: Tk koordinatları = fiziksel piksel, yani
    ImageGrab kırpması ölçek ne olursa olsun tam pencereyi yakalar.
  * Dil, uygulamanın KENDİ set_language()'i ile değiştirilir (config'e
    yazar); betik biterken kullanıcının orijinal dili GERİ YÜKLENİR.
  * Çekim öncesi BÜTÜN çalışma alanları görünür yapılır. Sebebi bir
    hatayla öğrenildi: geliştiricinin config'inde Sözlük sekmesi gizliydi,
    select_workspace sessizce başarısız oldu ve sunuma "Sözlük" altyazısıyla
    Fizik Lab'ının fotoğrafı girdi. Deste, kimsenin kişisel sekme
    tercihlerine bağlı olmamalı. Görünürlük save=False ile değiştirilir ve
    dil geri yüklenmeden ÖNCE eski hâline döndürülür (dil kaydı config'i
    yazdığı için sıra önemlidir).
  * Pencere görünür olmak zorundadır (ekran görüntüsü ekrandan alınır);
    çekim sırasında pencere birkaç saniye öne gelir, bu normaldir.
"""

import ctypes
import importlib.util
import io
import os
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# DPI farkındalığı Tk penceresi kurulmadan ÖNCE açılmalı — sonra açılırsa
# winfo_rootx() sanal, ImageGrab fiziksel piksel döndürür ve kırpma kayar.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from PIL import ImageGrab  # noqa: E402  (DPI ayarından sonra gelmeli)

CIKTI = ROOT / "tanitim_gorseller"


def _uygulama_yukle():
    spec = importlib.util.spec_from_file_location("mca_main", ROOT / "Math_Course_AI.pyw")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bekle(app, saniye):
    """update() döngüsüyle GERÇEK zaman geçirir (after kuyrukları işlesin)."""
    bitis = time.time() + saniye
    while time.time() < bitis:
        app.update()
        time.sleep(0.03)


def _cek(app, yol):
    app.update_idletasks()
    app.lift()
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    yol.parent.mkdir(parents=True, exist_ok=True)
    img.save(yol)
    print(f"   [OK] {yol.relative_to(ROOT)}  ({img.width}x{img.height})")


def _gorunurluk_ac(app):
    """Bütün çalışma alanlarını görünür yapar → eski durumu döndürür.

    save=False: kullanıcının config'i YAZILMAZ. Geri yükleme _gorunurluk_yaz
    ile yapılır ve dil geri yüklemesinden önce çağrılmalıdır.
    """
    eski = dict(getattr(app, "workspace_visible", {}))
    for anahtar in list(eski):
        if not eski[anahtar]:
            try:
                app.set_workspace_visible(anahtar, True, save=False)
            except Exception as exc:
                print(f"   [!] {anahtar} görünür yapılamadı: {exc}")
    return eski


def _gorunurluk_yaz(app, eski):
    for anahtar, gorunur in eski.items():
        if not gorunur:
            try:
                app.set_workspace_visible(anahtar, False, save=False)
            except Exception:
                pass
    # config_data ile workspace_visible ayni sozlugu paylasabiliyor; sonraki
    # config yazimi (set_language) kullanicinin ESKI degerlerini yazsin.
    try:
        app.config_data["workspace_visible"] = dict(eski)
    except Exception:
        pass


def _ornek_pdf(app):
    """Görüntülenecek bir PDF bul: açık olan varsa o, yoksa kaynaklardan ilki."""
    pv = getattr(app, "pdf_viewer", None)
    if pv is not None and getattr(pv, "path", None):
        return None                      # zaten açık, dokunma
    kok = Path(app.config_data.get("resource_dir") or (ROOT / "Resources"))
    if not kok.exists():
        return None
    for p in sorted(kok.rglob("*.pdf")):
        return p
    return None


def _pdf_hazirla(app):
    pdf = _ornek_pdf(app)
    pv = getattr(app, "pdf_viewer", None)
    if pdf is not None and pv is not None:
        try:
            pv.load_pdf(pdf)
            # Kapak sayfası yerine içerikli bir sayfa göster.
            if getattr(pv, "doc", None) is not None and len(pv.doc) > 3:
                pv.page_index = 2
                pv.render()
        except Exception as exc:
            print(f"   [!] PDF açılamadı: {exc}")


def _ekranlar(app, dil):
    """(ad, beklenen çalışma alanı, hazırlık, bekleme sn) — anlatım sırası."""
    def sec(anahtar):
        return lambda: app.select_workspace(anahtar)

    def takip():
        app.select_workspace("StudentTracker")
        panel = app._ensure_student_tracker()
        if panel is not None and hasattr(panel, "nb"):
            panel.nb.select(0)           # Bugün panosu

    def sozluk():
        app.select_workspace("Dictionary")
        app._ensure_dictionary()
        sozluk_panel = getattr(app, "dictionary", None)
        if sozluk_panel is not None and hasattr(sozluk_panel, "nb"):
            sozluk_panel.nb.select(0)

    return [
        ("pdf",    "PDF",            lambda: (sec("PDF")(), _pdf_hazirla(app)), 1.5),
        ("ai",     "AI",             sec("AI"), 1.0),
        ("takip",  "StudentTracker", takip, 1.5),
        ("visual", "VisualMath",     sec("VisualMath"), 2.5),
        ("lab",    "Physics",        sec("Physics"), 2.5),
        ("sozluk", "Dictionary",     sozluk, 1.5),
        ("hesap",  "Calculator",     sec("Calculator"), 1.0),
        ("tahta",  "Wacom",          sec("Wacom"), 1.0),
    ]


def _dogrula(app, ad, beklenen):
    """Fotoğraflanacak sekme GERÇEKTEN beklenen mi? Değilse yüksek sesle söyle.

    Sunuma yanlış ekranın "doğru" altyazıyla girmesi sessiz bir hatadır ve
    bir kez gerçekten yaşandı; bu yüzden kare kare doğrulanır.
    """
    try:
        secili = app.workspace_key_from_tab_id(app.tabs.select())
    except Exception as exc:
        print(f"   [!] {ad}: seçili sekme okunamadı ({exc})")
        return False
    if secili != beklenen:
        print(f"   [HATA] {ad}: beklenen '{beklenen}', ekranda '{secili}' — "
              f"bu kare sunuma YANLIŞ girer!")
        return False
    return True


def main():
    print("Math Course AI — sunum ekran görüntüleri çekiliyor")
    print("-" * 60)
    mca = _uygulama_yukle()
    app = mca.MathCourseApp()

    ekran_w = app.winfo_screenwidth()
    ekran_h = app.winfo_screenheight()
    w = min(1600, ekran_w - 40)
    h = min(920, ekran_h - 80)
    app.geometry(f"{w}x{h}+{(ekran_w - w) // 2}+{max(0, (ekran_h - h) // 2 - 20)}")
    app.attributes("-topmost", True)

    orijinal_dil = app.language
    _bekle(app, 3.0)                     # oturum geri yükleme after(500) ile gelir
    eski_gorunurluk = _gorunurluk_ac(app)
    _bekle(app, 0.5)

    hatali = []
    try:
        for dil in ("tr", "en"):
            print(f"\n== {dil.upper()} ==")
            if app.language != dil:
                app.set_language(dil)
                _bekle(app, 1.0)
            for ad, beklenen, hazirla, bekleme in _ekranlar(app, dil):
                try:
                    hazirla()
                except Exception as exc:
                    print(f"   [!] {ad}: hazırlık hatası: {exc}")
                _bekle(app, bekleme)
                if not _dogrula(app, ad, beklenen):
                    hatali.append(f"{dil}/{ad}")
                _cek(app, CIKTI / dil / f"{ad}.png")
    finally:
        # Kullanıcının ayarları neyse o kalsın — betik iz bırakmasın.
        # SIRA ÖNEMLİ: görünürlük dilden ÖNCE, çünkü set_language config'i yazar.
        _gorunurluk_yaz(app, eski_gorunurluk)
        if app.language != orijinal_dil:
            try:
                app.set_language(orijinal_dil)
            except Exception:
                pass
        try:
            app.destroy()
        except Exception:
            pass

    if hatali:
        print(f"\n[HATA] {len(hatali)} kare yanlış ekranı gösteriyor: "
              f"{', '.join(hatali)}")
        print("       Bu kareler sunuma girmemeli — sebebi düzeltip tekrar koşun.")
        return 1
    print("\n[OK] Bitti — 16 karenin hepsi beklenen ekranı gösteriyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
