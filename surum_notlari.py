# -*- coding: utf-8 -*-
"""Math Course AI — sürüm bilgisi, kısayollar ve lisans özeti (Tkinter'sız).

Tek güncelleme noktası: "ℹ Hakkında" penceresi bu modülden beslenir. Yeni sürüm çıkınca **yalnızca bu dosya** güncellenir:
  1) SURUM_TARIH değiştirilir (sürüm numarasının kendisi mca_common.VERSION'dan
     okunur — iki yerde tutulup ayrışmasın),
  2) SURUM_GECMISI listesinin BAŞINA yeni kayıt eklenir,
  3) gerekiyorsa KISAYOLLAR tazelenir.

Tkinter yok: içerik saf veri, pencereyi ana uygulama kurar. Böylece hem
headless test edilebilir hem de ileride kılavuza/sunuma beslenebilir.
"""

from mca_common import VERSION

__all__ = ["APP_ADI", "SURUM", "SURUM_TARIH", "SLOGAN", "SLOGAN_EN", "TANIM",
           "TANIM_EN", "LISANS", "LISANS_EN", "KISAYOLLAR", "SURUM_GECMISI",
           "hakkinda_metni"]

APP_ADI = "Math Course AI"
SURUM = VERSION                      # tek kaynak: mca_common.VERSION
SURUM_TARIH = "15 Ağustos 2026"

SLOGAN = "Oku. Çöz. Tekrar et. Hepsi tek pencerede, hepsi senin bilgisayarında."
SLOGAN_EN = "Read. Solve. Revise. All in one window, all on your own machine."

TANIM = (
    "Çevrimiçi matematik kurslarını takip etmek için tasarlanmış, yerel öncelikli "
    "bir masaüstü öğrenme platformu: PDF okuma ve not alma, soru "
    "bankası ve sınav motoru, aralıklı tekrar, görsel matematik laboratuvarı, "
    "beş bilim lab'ı, dil sözlüğü ve LM Studio üzerinden yerel yapay zekâ "
    "öğretmen. Kurs dosyaların, notların ve çalışma geçmişin hiçbir yapay "
    "zekâ sağlayıcısına gönderilmez. İsteğe bağlı bir bulut sağlayıcı vardır "
    "ve yalnızca o oturumda açıkça izin verirsen devreye girer."
)
TANIM_EN = (
    "A local-first desktop learning platform built for following online maths "
    "courses: PDF reading and annotation, a question bank with an exam engine, "
    "spaced repetition, a visual maths lab, five science labs, a language "
    "dictionary and a local AI tutor through LM Studio. Your course files, "
    "notes and study history are never sent to any AI provider. An optional "
    "cloud provider exists and activates only with your explicit consent in "
    "that session."
)

LISANS = (
    "Program kodu MIT lisanslıdır. Kurs içeriği (Resources/) üçüncü taraf "
    "telifidir; program onları yalnızca yerelde okur, dağıtmaz. Yerleşik soru "
    "üreteçleri bu programın özgün içeriğidir. Bağımlılıklar (sympy, "
    "matplotlib, NumPy, Pillow, PyMuPDF, Tesseract…) kendi lisanslarına tabidir."
)
LISANS_EN = (
    "The program code is MIT licensed. Course content (Resources/) is "
    "third-party copyright; the program only reads it locally and never "
    "redistributes it. The built-in question generators are original content. "
    "Dependencies (sympy, matplotlib, NumPy, Pillow, PyMuPDF, Tesseract…) keep "
    "their own licences."
)

# (kısayol, TR açıklama, EN açıklama) — Hakkında penceresi ve kılavuz aynı listeyi okur
KISAYOLLAR = [
    ("Ctrl+Enter", "AI Terminali: isteği gönder", "AI Terminal: send the request"),
    ("Ctrl+L", "AI Terminali: ekranı ve geçmişi temizle",
     "AI Terminal: clear the screen and history"),
    ("Esc", "AI Terminali: süren isteği durdur", "AI Terminal: stop the running request"),
    ("Çift tık", "İstatistik > Sınavlar: o sınavın soru dökümü",
     "Statistics > Exams: that exam's question breakdown"),
    ("Orta tık", "Sekme şeridi: o çalışma alanını gizle",
     "Tab strip: hide that workspace"),
    ("Shift+Tekerlek", "Kaynak ağacı: yatay kaydırma",
     "Resource tree: horizontal scroll"),
]

# En yeniden eskiye. Yeni sürüm BAŞA eklenir.
SURUM_GECMISI = [
    ("V48", "AI Terminali + çalışma tutanağı · koyu tema · 📌 Bu Hafta önerileri · "
            "haftalık rapor · .mcpack görselli paketler · gerçek TR/EN · "
            "açılış %46 hızlandı · modül bölünmesi"),
    ("V47", "Konu bilgisinde ham LaTeX düzeltildi · tik/ℹ sütunları geri geldi · "
            "yanıltıcı ✅ kaldırıldı"),
    ("V46", "Konu bilgi bankası kapsamı %41 → %99.9 (667/668 konu)"),
    ("V45", "Gömülü konu bilgi bankası + açık lisanslı kütüphane 13 kitaba çıktı"),
    ("V44", "Kurs ağacında tik · ✂ Soru Kırp · etkileşimli sınav · grafiksel istatistik"),
    ("V43", "Bugün panosu · aralıklı tekrar · sympy eşdeğerlik · okuma takibi"),
    ("V42", "Öğrenci Takip sistemi · soru paketleri · X Düzeni · oturum geri yükleme"),
]


def hakkinda_metni(lang="tr"):
    """Hakkında penceresinin gövde metni (düz metin, panoya kopyalanabilir)."""
    en = str(lang).lower().startswith("en")
    satirlar = [
        f"{APP_ADI} — {SURUM}",
        ("Release date: " if en else "Sürüm tarihi: ") + SURUM_TARIH,
        "",
        SLOGAN_EN if en else SLOGAN,
        "",
        TANIM_EN if en else TANIM,
        "",
        ("KEYBOARD SHORTCUTS" if en else "KISAYOLLAR"),
    ]
    for tus, tr, ing in KISAYOLLAR:
        satirlar.append(f"  {tus:<16} {ing if en else tr}")
    satirlar += ["", ("VERSION HISTORY" if en else "SÜRÜM GEÇMİŞİ")]
    for surum, ozet in SURUM_GECMISI:
        satirlar.append(f"  {surum}  {ozet}")
    satirlar += ["", ("LICENCE" if en else "LİSANS"), LISANS_EN if en else LISANS]
    return "\n".join(satirlar)
