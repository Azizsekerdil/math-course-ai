# -*- coding: utf-8 -*-
"""Eğitim modülü + Token defteri testleri (headless, ağ yok, disk yazmaz)."""

import io
import re
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PASSED = 0
FAILED = 0


def check(cond, label):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"   [PASS] {label}")
    else:
        FAILED += 1
        print(f"   [FAIL] {label}")


# ── EĞİTİM MODÜLÜ ────────────────────────────────────────────────────────
def test_egitim_html():
    print("== Eğitim modülü: HTML üretimi ==")
    import education
    for lang in ("tr", "en"):
        h = education.egitim_html(lang)
        check(h.startswith("<!DOCTYPE html>") and h.rstrip().endswith("</html>"),
              f"[{lang}] tam HTML belgesi")
        check("__" not in h.split("<style>")[0], f"[{lang}] yer tutucular dolduruldu")
        check(f'<html lang="{lang}"' in h, f"[{lang}] dil etiketi dogru")
        h2 = re.findall(r'<h2 id="([a-z0-9-]+)"', h)
        check(len(h2) == education.BOLUM_SAYISI,
              f"[{lang}] {education.BOLUM_SAYISI} bolum ({len(h2)} bulundu)")
        check(len(set(h2)) == len(h2), f"[{lang}] bolum kimlikleri benzersiz")
        # Icindekiler baglantilarinin HEPSI gercek bir capaya gitmeli
        toc = re.findall(r'<a class="(?:top|sub)" href="#([a-z0-9-]+)"', h)
        capalar = set(re.findall(r'<h[23] id="([a-z0-9-]+)"', h))
        kirik = [t for t in toc if t not in capalar]
        check(not kirik, f"[{lang}] kirik icindekiler baglantisi yok ({kirik[:3]})")
        check("window.print()" in h, f"[{lang}] yazdirma dugmeleri var")
        check("@media print" in h and "@page" in h, f"[{lang}] yazdirma CSS'i var")


def test_egitim_dil_esligi():
    print("== Eğitim modülü: iki dil aynı çapaları taşır ==")
    import education
    tr = set(re.findall(r'<h2 id="([a-z0-9-]+)"', education.egitim_html("tr")))
    en = set(re.findall(r'<h2 id="([a-z0-9-]+)"', education.egitim_html("en")))
    check(tr == en, f"TR/EN bolum kimlikleri ayni (fark: {tr ^ en})")
    # V48: EN govde TR derinligine cikarildi — alt basliklar da AYNI ve AYNI SIRADA.
    tr_h3 = re.findall(r'<h3 id="([a-z0-9-]+)"', education.egitim_html("tr"))
    en_h3 = re.findall(r'<h3 id="([a-z0-9-]+)"', education.egitim_html("en"))
    check(tr_h3 == en_h3,
          f"TR/EN alt baslik kimlikleri ayni ve ayni sirada "
          f"(TR {len(tr_h3)} / EN {len(en_h3)}, fark: {set(tr_h3) ^ set(en_h3)})")
    check(len(tr_h3) >= 26, f"alt baslik sayisi beklenen derinlikte ({len(tr_h3)})")
    # Derinlik gostergeleri: neden-sonuc-fayda bloklari ve tablolar da esit olmali,
    # yoksa "ayni capalar ama yarim icerik" durumu sessizce geri gelebilir.
    for etiket, desen in (("neden-sonuc-fayda blogu", 'class="cause"'),
                          ("tablo", "<table")):
        t = education.egitim_html("tr").count(desen)
        e = education.egitim_html("en").count(desen)
        check(t == e, f"TR/EN {etiket} sayisi esit ({t} / {e})")
    en_kelime = len(re.sub(r"<[^>]+>", " ", education.egitim_html("en")).split())
    check(en_kelime >= 3800, f"EN govde derinligi korunuyor ({en_kelime} kelime)")
    check(education.egitim_html("English") == education.egitim_html("en"),
          "dil adi esnek cozumlenir ('English' -> en)")
    check(education.egitim_html("zz") == education.egitim_html("tr"),
          "bilinmeyen dil TR'ye duser")


def test_tanitim_sunumu():
    print("== Tanıtım sunumu: içerik bütünlüğü + TR/EN eşliği ==")
    import tanitim_icerik as ti
    # python-pptx is an OPTIONAL dependency (see requirements-optional.txt), so
    # the authoring generator may legitimately be unavailable. The CONTENT
    # checks below must still run; only the checks that need the generator's
    # renderer table are skipped, and the skip is announced rather than turned
    # into a false failure.
    try:
        import tanitim_uret as tu
    except ImportError as exc:
        tu = None
        print(f"   [SKIP] tanitim_uret yuklenemedi (istege bagli bagimlilik): {exc}")

    check(len(ti.SLAYTLAR) >= 15, f"sunum yeterli uzunlukta ({len(ti.SLAYTLAR)} slayt)")
    check(ti.SLAYTLAR[0]["tip"] == "kapak", "ilk slayt kapak")
    check(ti.SLAYTLAR[-1]["tip"] == "kapanis", "son slayt kapanis")
    # The PUBLISHED renderer is tanitim_pdf.py, which is always importable
    # (matplotlib only), so slide-type coverage is checked against it. The
    # optional PPTX generator is checked too when it is installed.
    import tanitim_pdf as tp
    tipler = {s["tip"] for s in ti.SLAYTLAR}
    eksik_pdf = []
    for t in sorted(tipler):
        fig, ax = tp._yeni_sayfa()
        try:
            tp.sayfa_ciz(fig, ax, next(s for s in ti.SLAYTLAR if s["tip"] == t),
                         "tr", 1, len(ti.SLAYTLAR))
        except Exception as exc:
            eksik_pdf.append(f"{t}: {exc}")
        finally:
            tp.plt.close(fig)
    check(not eksik_pdf, f"yayin PDF ureticisi her slayt tipini cizebiliyor (hata: {eksik_pdf})")
    if tu is not None:
        bilinen = set(tu.CIZICILER)
        bilinmeyen = tipler - bilinen
        check(not bilinmeyen, f"her slayt tipinin PPTX cizicisi var (eksik: {bilinmeyen})")
    else:
        print("   [SKIP] PPTX cizici kontrolu (python-pptx kurulu degil)")

    # TR/EN esligi: KILAVUZDAKI ayni disiplin — bir dil unutulamaz.
    def _cift_mi(d):
        return isinstance(d, (tuple, list)) and len(d) == 2 and all(
            isinstance(x, str) and x.strip() for x in d)

    eksik = []
    for i, s in enumerate(ti.SLAYTLAR, 1):
        if not _cift_mi(s.get("baslik")):
            eksik.append(f"{i}.baslik")
        for alan in ("alt", "dipnot"):
            if s.get(alan) is not None and not _cift_mi(s[alan]):
                eksik.append(f"{i}.{alan}")
        # Slayt TIPINE gore yurumek gerekiyor. "galeri" tipinde her oge
        #   (gorsel_dosya_adi, (tr, en))
        # bicimindedir; ilk parca bir DOSYA ADIDIR, cevrilecek bir metin
        # degil. Eski yurutucu bunu bilmedigi icin gorsel adlarini "eksik
        # ceviri" sayiyor ve 4 sahte hata uretiyordu (slayt 20 ve 22).
        # Asagisi tipi dikkate alir; ayrica gorselin GERCEKTEN VAR OLDUGUNU
        # da dogrular — eski surumun hic yapmadigi bir kontrol.
        tip = s.get("tip")
        for j, oge in enumerate(s.get("ogeler") or [], 1):
            if tip == "galeri":
                if not (isinstance(oge, (tuple, list)) and len(oge) == 2):
                    eksik.append(f"{i}.oge{j}.bicim")
                    continue
                ad, altyazi = oge
                if not (isinstance(ad, str) and ad.strip()):
                    eksik.append(f"{i}.oge{j}.gorsel_adi")
                if not _cift_mi(altyazi):
                    eksik.append(f"{i}.oge{j}.altyazi")
                continue
            parcalar = oge if isinstance(oge, tuple) and _cift_mi(oge) is False else (oge,)
            if isinstance(oge, tuple) and not _cift_mi(oge):
                parcalar = oge
            for k, p in enumerate(parcalar):
                if not _cift_mi(p):
                    eksik.append(f"{i}.oge{j}.{k}")
    check(not eksik, f"her metin TR+EN cifti tasiyor (eksik: {eksik[:5]})")

    # Sunumda adi gecen HER gorsel gercekten depoda duruyor mu (iki dilde de)?
    kok = Path(__file__).resolve().parent / "tanitim_gorseller"
    kayip = []
    for i, s in enumerate(ti.SLAYTLAR, 1):
        adlar = []
        if s.get("tip") == "gorsel" and s.get("gorsel"):
            adlar.append(s["gorsel"])
        if s.get("tip") == "galeri":
            adlar += [o[0] for o in (s.get("ogeler") or [])
                      if isinstance(o, (tuple, list)) and o and isinstance(o[0], str)]
        for ad in adlar:
            for dil in ("tr", "en"):
                if not (kok / dil / ad).is_file():
                    kayip.append(f"{dil}/{ad} (slayt {i})")
    check(not kayip, f"sunumdaki her gorsel depoda var (eksik: {kayip[:5]})")

    # Iki dilde de gercekten FARKLI metin uretiliyor mu (kopyala-yapistir tuzagi)
    # Language selection is also implemented by the published renderer, so the
    # bilingual checks below work with or without the optional PPTX generator.
    import tanitim_pdf as _tp
    _sec = tu._c if tu is not None else _tp._c
    tr_ler = [_sec(s["baslik"], "tr") for s in ti.SLAYTLAR]
    en_ler = [_sec(s["baslik"], "en") for s in ti.SLAYTLAR]
    ayni = [a for a, b in zip(tr_ler, en_ler) if a == b]
    check(len(ayni) <= 2, f"basliklarin cogu gercekten cevrilmis (ayni kalan: {ayni})")
    check(_sec(("a", "b"), "en") == "b" and _sec(("a", "b"), "tr") == "a",
          "_c dil secici")
    check(_sec(("a", ""), "en") == "a", "bos ceviri TR'ye duser")

    # Surum sunumda gorunuyor mu (elle guncelleme unutulmasin)
    from mca_common import VERSION
    kapak = ti.SLAYTLAR[0]
    check(VERSION.split("—")[0].strip() in _sec(kapak["dipnot"], "tr"),
          "kapakta surum yaziyor (koddan okunur)")

    # Tasarim: ekran koyu, baski acik — sunum programin paletinden turuyor
    if tu is None:
        print("   [SKIP] PPTX tasarim paleti kontrolleri (python-pptx kurulu degil)")
        return
    ekran = tu._Tasarim("ekran")
    baski = tu._Tasarim("baski")

    def parlaklik(h):
        h = h.lstrip("#")
        return 0.299 * int(h[0:2], 16) + 0.587 * int(h[2:4], 16) + 0.114 * int(h[4:6], 16)
    check(parlaklik(ekran.zemin) < 110, f"ekran surumu koyu ({ekran.zemin})")
    check(parlaklik(baski.zemin) > 200, f"baski surumu acik ({baski.zemin})")
    check(abs(parlaklik(ekran.metin) - parlaklik(ekran.zemin)) > 90,
          "ekran surumunde metin/zemin kontrasti")
    check(abs(parlaklik(baski.metin) - parlaklik(baski.zemin)) > 90,
          "baski surumunde metin/zemin kontrasti")

    # HTML: PNG olmadan da okunur metin uretmeli (PowerPoint yoksa)
    metin = tu._slayt_metni_html(ti.SLAYTLAR[1], "en")
    check(metin.startswith('<div class="txt">') and "<h2>" in metin,
          "PNG'siz HTML metin slaydi uretiliyor")
    check("&" not in metin.replace("&amp;", "").replace("&#", ""),
          "HTML kacisi uygulaniyor")

def test_surum_notlari():
    print("== Sürüm notları / ℹ Hakkında (tek güncelleme noktası) ==")
    import surum_notlari as sn
    from mca_common import VERSION
    check(sn.SURUM == VERSION,
          "surum TEK KAYNAKTAN okunur (mca_common.VERSION) — iki yerde ayrisamaz")
    check(sn.SURUM_GECMISI and sn.SURUM_GECMISI[0][0].startswith("V48"),
          f"gecmisin BASINDA guncel surum var ({sn.SURUM_GECMISI[0][0]})")
    surumler = [v for v, _ in sn.SURUM_GECMISI]
    check(len(surumler) == len(set(surumler)), "surum gecmisinde yineleme yok")
    check(all(isinstance(o, str) and o.strip() for _, o in sn.SURUM_GECMISI),
          "her surumun bir ozeti var")
    check(len(sn.KISAYOLLAR) >= 5, f"kisayol listesi dolu ({len(sn.KISAYOLLAR)})")
    check(all(len(k) == 3 and all(str(x).strip() for x in k) for k in sn.KISAYOLLAR),
          "her kisayol (tus, TR, EN) uclusu tasiyor")
    tuslar = [k[0] for k in sn.KISAYOLLAR]
    check("Ctrl+L" in tuslar and "Esc" in tuslar,
          "yeni terminal kisayollari listede (Ctrl+L, Esc)")

    tr = sn.hakkinda_metni("tr")
    en = sn.hakkinda_metni("en")
    check(sn.APP_ADI in tr and VERSION in tr, "hakkinda metninde ad + surum")
    check("KISAYOLLAR" in tr and "KEYBOARD SHORTCUTS" in en, "bolum basliklari iki dilde")
    check("LİSANS" in tr and "LICENCE" in en, "lisans bolumu iki dilde")
    check("MIT" in tr and "MIT" in en, "MIT lisansi aciklaniyor")
    check(tr != en and len(en) > 800, f"iki dil gercekten farkli ({len(tr)} / {len(en)})")
    for tus, _, _ in sn.KISAYOLLAR:
        if tus not in tr:
            check(False, f"kisayol metne girmemis: {tus}")
            break
    else:
        check(True, "tum kisayollar metinde gorunuyor")


def test_egitim_yardimcilar():
    print("== Eğitim modülü: yardımcı biçimleyiciler ==")
    import education
    c = education._cause("A", "B", "C")
    check("Neden" in c and "Sonuç" in c and "Fayda" in c, "TR etiketleri")
    check("Why" in education._cause("A", "B", "C", "en"), "EN etiketleri")
    t = education._tablo(["X", "Y"], [["1", "2"], ["3", "4"]])
    check(t.count("<tr>") == 3 and t.count("<td>") == 4, "tablo satir/hucre sayisi")
    check('id="abc"' in education._h2("1", "Baslik", "abc"), "h2 capasi")


# ── TOKEN DEFTERİ ────────────────────────────────────────────────────────
def _ornek_kayitlar():
    return [
        {"time": "2026-08-14 10:00:00", "provider": "yerel", "profile": "math",
         "model": "qwen2.5-math", "prompt_tokens": 100, "completion_tokens": 200,
         "total_tokens": 300, "finish_reason": "stop", "seconds": 5.0},
        {"time": "2026-08-14 11:00:00", "provider": "nvidia", "profile": "terminal",
         "model": "z-ai/glm-5.2", "prompt_tokens": 50, "completion_tokens": 150,
         "total_tokens": 200, "finish_reason": "stop", "seconds": 4.0},
        {"time": "2026-08-01 09:00:00", "provider": "yerel", "profile": "math",
         "model": "qwen2.5-math", "prompt_tokens": 10, "completion_tokens": 20,
         "total_tokens": 30, "finish_reason": "length", "seconds": 1.0},
    ]


def test_token_normalize():
    print("== Token defteri: normalize (geriye uyum) ==")
    import token_ledger as tl
    eski = {"time": "2026-06-05 12:54:33", "model": "moondream",
            "prompt_tokens": 892, "completion_tokens": 76, "total_tokens": 968,
            "finish_reason": "stop", "seconds": 5.7}
    r = tl.normalize(eski)
    check(r["provider"] == "yerel", "eski kayit yerel sayilir (tarihsel olgu)")
    check(r["profile"] == "?", "eksik profil uydurulmaz, '?' isaretlenir")
    check(r["total_tokens"] == 968, "mevcut toplam korunur")
    r2 = tl.normalize({"prompt_tokens": 5, "completion_tokens": 7})
    check(r2["total_tokens"] == 12, "toplam yoksa girdi+ciktidan hesaplanir")
    check(tl.normalize("bozuk") is None and tl.normalize(None) is None,
          "sozluk olmayan girdi None doner")


def test_token_ozet():
    print("== Token defteri: özet ==")
    import token_ledger as tl
    kayitlar = [tl.normalize(r) for r in _ornek_kayitlar()]
    o = tl.summarize(kayitlar, today="2026-08-14")
    check(o["tum"]["istek"] == 3 and o["tum"]["token"] == 530, "tum zamanlar toplami")
    check(o["bugun"]["istek"] == 2 and o["bugun"]["token"] == 500, "bugun filtresi")
    check(o["son7"]["istek"] == 2, "son 7 gun (1 Agustos disarida)")
    check(o["son30"]["istek"] == 3, "son 30 gun hepsini kapsar")
    check(o["kesilen"] == 1, "yarida kesilen istek sayilir (finish=length)")
    check(o["ilk_kayit"].startswith("2026-08-01"), "ilk kayit zamani")
    bos = tl.summarize([])
    check(bos["tum"]["istek"] == 0 and bos["ortalama_sure"] == 0.0, "bos defter cokmez")


def test_token_gruplama():
    print("== Token defteri: gruplama ==")
    import token_ledger as tl
    kayitlar = [tl.normalize(r) for r in _ornek_kayitlar()]
    m = tl.group_by(kayitlar, "model")
    check(m[0]["anahtar"] == "qwen2.5-math" and m[0]["token"] == 330,
          "modele gore, token'a gore azalan")
    p = {h["anahtar"]: h for h in tl.group_by(kayitlar, "provider")}
    check(p["yerel"]["istek"] == 2 and p["nvidia"]["istek"] == 1, "saglayiciya gore")
    g = tl.group_by(kayitlar, "gun")
    check([h["anahtar"] for h in g] == ["2026-08-01", "2026-08-14"], "gunler kronolojik")
    check(tl.group_by([], "model") == [], "bos liste guvenli")


def test_token_maliyet_ve_csv():
    print("== Token defteri: maliyet + CSV ==")
    import token_ledger as tl
    kayitlar = [tl.normalize(r) for r in _ornek_kayitlar()]
    tutar, bilinen = tl.record_cost(kayitlar[0])
    check(tutar == 0.0 and bilinen, "yerel model ucretsiz ve BILINEN")
    tutar2, bilinen2 = tl.record_cost(kayitlar[1])
    check(tutar2 == 0.0 and bilinen2, "NVIDIA ucretsiz uc ve BILINEN")
    t3, b3 = tl.record_cost({"provider": "baska", "model": "?", "total_tokens": 1000})
    check(t3 == 0.0 and not b3, "bilinmeyen saglayici ucretsizmis gibi sunulmaz")
    ucretli, _ = tl.record_cost({"provider": "x", "model": "pahali", "total_tokens": 1_000_000},
                                prices={"pahali": 3.0})
    check(abs(ucretli - 3.0) < 1e-9, "1M token fiyati dogru hesaplanir")
    yol = Path(tempfile.mkdtemp()) / "defter.csv"
    n = tl.to_csv(kayitlar, yol)
    icerik = yol.read_text(encoding="utf-8-sig")
    check(n == 3 and icerik.count("\n") >= 4, "CSV satir sayisi (baslik + 3)")
    check("provider" in icerik.splitlines()[0], "CSV basligi alan adlarini icerir")


def test_token_okuma():
    print("== Token defteri: dosyadan okuma ==")
    import json
    import token_ledger as tl
    yol = Path(tempfile.mkdtemp()) / "log.jsonl"
    yol.write_text("\n".join([json.dumps(r) for r in _ornek_kayitlar()]
                             + ["{bozuk json", "", "   "]), encoding="utf-8")
    kayitlar = tl.read_records(yol)
    check(len(kayitlar) == 3, "bozuk ve bos satirlar atlanir")
    check(tl.read_records(Path("olmayan_dosya.jsonl")) == [], "olmayan dosya bos liste")
    check(len(tl.read_records(yol, limit=2)) == 2, "limit son N satiri okur")


def test_gercek_defter():
    print("== Token defteri: kullanıcının gerçek defteri (salt okuma) ==")
    import token_ledger as tl
    kayitlar = tl.read_records()
    check(isinstance(kayitlar, list), "gercek defter okunabiliyor")
    if kayitlar:
        o = tl.summarize(kayitlar)
        check(o["tum"]["token"] >= 0 and o["tum"]["istek"] == len(kayitlar),
              f"{len(kayitlar)} kayit ozetlendi ({o['tum']['token']} token)")
        check(all(tl.group_by(kayitlar, k) is not None
                  for k in ("model", "provider", "profile", "gun")),
              "dort gruplama da gercek veride calisiyor")
    else:
        print("   [SKIP] defter bos")


def main():
    print("=" * 64)
    print("Eğitim Modülü & Token Defteri — Test Suite")
    print("=" * 64)
    for fn in (test_egitim_html, test_egitim_dil_esligi, test_egitim_yardimcilar, test_tanitim_sunumu, test_surum_notlari,
               test_token_normalize, test_token_ozet, test_token_gruplama,
               test_token_maliyet_ve_csv, test_token_okuma, test_gercek_defter):
        try:
            fn()
        except Exception as exc:
            global FAILED
            FAILED += 1
            import traceback
            traceback.print_exc()
            print(f"   [ERROR] {fn.__name__}: {exc}")
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
