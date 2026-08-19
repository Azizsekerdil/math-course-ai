# -*- coding: utf-8 -*-
"""Math Course AI — 🖥 AI Terminali çalışma tutanağı (kalıcı kayıt).

Neden bu modül var
------------------
AI Terminali'ne yazdırılan kod ve işler pencere kapanınca kayboluyordu:
"geçen hafta şu grafiği çizdiren kodu yazdırmıştım" diyen kullanıcının
elinde hiçbir şey kalmıyordu. Bu modül her tamamlanan işi
``%APPDATA%\\MathCourseAI\\terminal_tutanak.jsonl`` dosyasına yazar.

Depo biçimi JSONL (token defteri de JSONL; dosya tabanlı yedekleme kolay):
  • Her kayıt o anki program **sürümüyle damgalanır**.
  • Saklama sınırı vardır (``EN_FAZLA_KAYIT``); sınır aşılınca **en eski**
    kayıtlar düşer — tutanak bir günlük defteridir, arşiv madeni değil.
  • Yanıt metni **kırpılmaz**: kırpma, veri uydurmanın sessiz biçimidir.
  • Kayıt hatası **yutulur** (False döner) — tutanak, terminali ASLA
    bozmamalıdır; kayıt işi asıl işi engellemez.

GİZLİLİK — token defterinden farkı
----------------------------------
📒 Token defteri yalnız SAYAÇ tutar (model, token, saniye); istek metnini
bilerek saklamaz. Bu tutanak ise **isteğin ve yanıtın tam metnini saklar** —
zaten var oluş sebebi budur. Terminal penceresi ve tutanak penceresi bunu
kullanıcıya açıkça yazar. Dosya %APPDATA% altında olduğu için mevcut Drive
yedeğinin kapsamına kendiliğinden girer (bkz. scripts/README.md).

Tkinter YOK — bu katman baştan sona headless test edilir.
"""

import json
import os
import tempfile
import time
from pathlib import Path

from mca_common import APP_FOLDER, VERSION

__all__ = ["TUTANAK_PATH", "EN_FAZLA_KAYIT", "kaydet", "kod_ekle", "kayitlar",
           "ara", "ozet", "normalize", "metne_cevir", "yeni_id"]

TUTANAK_PATH = APP_FOLDER / "terminal_tutanak.jsonl"
EN_FAZLA_KAYIT = 2000

# Kayıt şeması — okurken eksik alanlar bu varsayılanlarla tamamlanır, böylece
# eski/yarım satırlar arayüzü çökertmez (token defterinin geriye uyum kararı).
_ALANLAR = {
    "id": "", "ts": "", "surum": "", "saglayici": "", "model": "",
    "istem": "", "yanit": "", "sure": None, "durum": "ok",
    "kod": "", "kod_cikti": "", "kod_durum": "",
}


def _yol(path=None):
    return Path(path) if path else TUTANAK_PATH


def yeni_id():
    """Zaman tabanlı benzersiz kayıt kimliği (aynı saniyede ikisi çakışmasın)."""
    return time.strftime("%Y%m%d-%H%M%S") + "-%06d" % (time.perf_counter_ns() % 1_000_000)


def normalize(ham):
    """Ham JSON satırını tam şemaya tamamlar; sayısal alanları güvenli okur."""
    if not isinstance(ham, dict):
        return None
    k = dict(_ALANLAR)
    for alan in _ALANLAR:
        if alan in ham and ham[alan] is not None:
            k[alan] = ham[alan]
    for alan in ("saglayici", "model", "istem", "yanit", "durum",
                 "kod", "kod_cikti", "kod_durum", "id", "ts", "surum"):
        k[alan] = str(k[alan] or "")
    try:
        k["sure"] = round(float(k["sure"]), 2) if k["sure"] not in ("", None) else None
    except Exception:
        k["sure"] = None
    return k


def _oku_ham(path=None):
    """Dosyadaki tüm kayıtlar, DOSYA SIRASIYLA (eskiden yeniye). Hata → []."""
    p = _yol(path)
    out = []
    try:
        if not p.exists():
            return out
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                try:
                    k = normalize(json.loads(satir))
                except Exception:
                    continue          # bozuk satır kaydı yutulur, dosya okunmaya devam
                if k:
                    out.append(k)
    except Exception:
        return []
    return out


def _yaz_hepsi(kayitlar_listesi, path=None):
    """Tüm kayıtları atomik olarak yeniden yazar (kırpma/güncelleme yolları).

    Geçici dosyaya yazıp os.replace ile taşırız: yazma yarıda kalırsa eski
    tutanak olduğu gibi durur, yarım dosya oluşmaz.
    """
    p = _yol(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, gecici = tempfile.mkstemp(dir=str(p.parent), prefix=".tutanak_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for k in kayitlar_listesi:
                    f.write(json.dumps(k, ensure_ascii=False) + "\n")
            os.replace(gecici, str(p))
        except Exception:
            try:
                os.unlink(gecici)
            except Exception:
                pass
            raise
        return True
    except Exception:
        return False


def kaydet(saglayici, model, istem, yanit, sure=None, durum="ok",
           kod="", kod_cikti="", kod_durum="", surum=None, path=None,
           en_fazla=EN_FAZLA_KAYIT, kayit_id=None):
    """Tamamlanan bir terminal işini tutanağa ekler → kayıt kimliği ya da None.

    Hata yutulur (None döner): tutanak terminali asla bozmamalı.
    """
    p = _yol(path)
    kid = kayit_id or yeni_id()
    kayit = {
        "id": kid,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "surum": surum if surum is not None else VERSION,
        "saglayici": str(saglayici or ""),
        "model": str(model or ""),
        "istem": str(istem or ""),
        "yanit": str(yanit or ""),
        "sure": None,
        "durum": str(durum or "ok"),
        "kod": str(kod or ""),
        "kod_cikti": str(kod_cikti or ""),
        "kod_durum": str(kod_durum or ""),
    }
    try:
        kayit["sure"] = round(float(sure), 2) if sure not in (None, "") else None
    except Exception:
        kayit["sure"] = None
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    except Exception:
        return None
    _kirp(en_fazla, path)
    return kid


def _kirp(en_fazla=EN_FAZLA_KAYIT, path=None):
    """Saklama sınırı: sınır aşıldıysa en ESKİ kayıtlar düşer."""
    try:
        en_fazla = int(en_fazla)
    except Exception:
        return False
    if en_fazla <= 0:
        return False
    hepsi = _oku_ham(path)
    if len(hepsi) <= en_fazla:
        return False
    return _yaz_hepsi(hepsi[-en_fazla:], path)


def kod_ekle(kayit_id, kod, cikti="", kod_durum="", path=None):
    """Var olan işe çalıştırılan kodu + çıktısını ekler → True/False.

    Kod, yanıt geldikten SONRA (onay penceresinden geçerek) çalışıyor; bu
    yüzden aynı işin kaydı güncellenir, ikinci bir satır açılmaz — kullanıcı
    tutanakta "bir iş" görmek ister, iki yarım kayıt değil.
    """
    if not kayit_id:
        return False
    hepsi = _oku_ham(path)
    bulundu = False
    for k in hepsi:
        if k["id"] == kayit_id:
            k["kod"] = str(kod or "")
            k["kod_cikti"] = str(cikti or "")
            k["kod_durum"] = str(kod_durum or "")
            bulundu = True
            break
    if not bulundu:
        return False
    return _yaz_hepsi(hepsi, path)


def kayitlar(limit=200, saglayici=None, path=None):
    """Kayıtlar YENİDEN ESKİYE → [dict]. Hata hâlinde boş liste."""
    hepsi = _oku_ham(path)
    if saglayici:
        hepsi = [k for k in hepsi if k["saglayici"] == saglayici]
    hepsi = list(reversed(hepsi))
    try:
        limit = int(limit)
    except Exception:
        limit = 200
    return hepsi[:limit] if limit > 0 else hepsi


def ara(sorgu, limit=200, saglayici=None, path=None):
    """İstem/yanıt/model/kod/çıktı alanlarında büyük-küçük harf duyarsız arama.

    Boş sorgu = filtre yok (liste görünümü aynı fonksiyondan beslenebilsin).
    """
    hepsi = kayitlar(limit=0, saglayici=saglayici, path=path)
    q = (sorgu or "").strip().lower()
    if q:
        alanlar = ("istem", "yanit", "model", "kod", "kod_cikti", "saglayici", "ts")
        hepsi = [k for k in hepsi if any(q in (k[a] or "").lower() for a in alanlar)]
    try:
        limit = int(limit)
    except Exception:
        limit = 200
    return hepsi[:limit] if limit > 0 else hepsi


def ozet(path=None):
    """{"toplam", "saglayicilar", "kodlu", "ilk_ts", "son_ts", "yol"}.

    Kayıt yoksa toplam=0 döner (None değil): arayüz "henüz kayıt yok" der.
    """
    hepsi = _oku_ham(path)
    dagilim = {}
    for k in hepsi:
        ad = k["saglayici"] or "?"
        dagilim[ad] = dagilim.get(ad, 0) + 1
    return {
        "toplam": len(hepsi),
        "saglayicilar": dagilim,
        "kodlu": sum(1 for k in hepsi if k["kod"]),
        "ilk_ts": hepsi[0]["ts"] if hepsi else "",
        "son_ts": hepsi[-1]["ts"] if hepsi else "",
        "yol": str(_yol(path)),
    }


def metne_cevir(kayit):
    """Tek işi düz metne çevirir (dışa aktarma + önizleme aynı kaynaktan)."""
    k = normalize(kayit) or dict(_ALANLAR)
    sure = f"{k['sure']} sn" if k["sure"] is not None else "?"
    satirlar = [
        "=" * 70,
        "Math Course AI — AI Terminali çalışma tutanağı",
        "=" * 70,
        f"Tarih      : {k['ts']}",
        f"Sürüm      : {k['surum'] or '?'}",
        f"Sağlayıcı  : {k['saglayici'] or '?'}",
        f"Model      : {k['model'] or '?'}",
        f"Süre       : {sure}",
        f"Durum      : {k['durum'] or '?'}",
        "",
        "--- İSTEK " + "-" * 60,
        k["istem"] or "(boş)",
        "",
        "--- YANIT " + "-" * 60,
        k["yanit"] or "(boş)",
    ]
    if k["kod"]:
        satirlar += ["", "--- ÇALIŞTIRILAN KOD " + "-" * 49, k["kod"]]
        satirlar += ["", "--- KOD ÇIKTISI " + "-" * 54,
                     (k["kod_cikti"] or "(çıktı yok)")
                     + (("\n" + k["kod_durum"]) if k["kod_durum"] else "")]
    else:
        satirlar += ["", "(bu işte kod çalıştırılmadı)"]
    return "\n".join(satirlar) + "\n"
