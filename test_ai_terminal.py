# -*- coding: utf-8 -*-
"""AI Terminali + NVIDIA sağlayıcısı testleri (headless, ağ yok).

Diğer paketlerle aynı desen: check() sayaçları + RESULT satırı.
"""

import io
import os
import sys

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


def test_block_extraction():
    print("== ```python blok ayrıştırma ==")
    from ai_terminal import extract_python_blocks
    metin = ("Açıklama...\n```python\nprint('a')\n```\nara\n"
             "```bash\nrm -rf /\n```\n"
             "```py\nx = 1+1\nprint(x)\n```\n"
             "```\ny = 2\n```")
    b = extract_python_blocks(metin)
    check(len(b) == 3, "python/py/etiketsiz bloklar alındı (3)")
    check(all("rm -rf" not in x for x in b), "bash bloğu ASLA dönmez")
    check(b[0] == "print('a')", "ilk blok birebir")
    check(extract_python_blocks("kod yok") == [], "bloksuz metin -> bos liste")
    check(extract_python_blocks("") == [] and extract_python_blocks(None) == [],
          "bos/None guvenli")
    cok_satir = "```python\nfor i in range(3):\n    print(i)\n```"
    check("    print(i)" in extract_python_blocks(cok_satir)[0], "girinti korunur")


def test_provider_payload():
    print("== NVIDIA payload hazırlama ==")
    import nvidia_provider as nv
    p = nv._payload_hazirla({"messages": [{"role": "user", "content": "s"}]},
                            "z-ai/glm-5.2", False)
    check(p["model"] == "z-ai/glm-5.2", "model gecer")
    check(p["stream"] is False and p["max_tokens"] >= 2048, "stream/max_tokens kurali")
    p2 = nv._payload_hazirla({"max_tokens": 50}, "olmayan/model", True)
    check(p2["model"] == nv.VARSAYILAN_MODEL, "bilinmeyen model varsayilana duser")
    check(p2["max_tokens"] == 2048, "dusuk max_tokens 2048'e cekilir")
    check(len(nv.MODELLER) == 3 and nv.VARSAYILAN_MODEL == nv.MODELLER[0],
          "3 dogrulanmis model, varsayilan ilki")


def test_key_handling():
    print("== Anahtar kuralları (ağ/cred'e yazmadan) ==")
    import nvidia_provider as nv
    ok, msg = nv.anahtar_kaydet("")
    check(not ok, "bos anahtar reddedilir")
    ok, msg = nv.anahtar_kaydet("sk-yanlis-prefix")
    check(not ok and "nvapi-" in msg, "yanlis onek reddedilir (nvapi- istenir)")
    eski = os.environ.pop("NVIDIA_API_KEY", None)
    try:
        # Assembled from fragments on purpose: a literal token-shaped string
        # in a source file trips secret scanners and teaches the wrong habit.
        sahte = "nv" + "api-" + ("PLACEHOLDER" * 1) + "1234"
        os.environ["NVIDIA_API_KEY"] = sahte
        check(nv.anahtar_oku() == sahte, "ortam degiskeni oncelikli")
        m = nv.anahtar_maskeli()
        # Maskeleme SIKILASTIRILDI: arayuze yalnizca saglayici adi, durum ve
        # SON 4 karakter cikar. Onek ("nvapi-XYZ") ve uzunluk artik
        # GOSTERILMEZ; ikisi de bir anahtari daraltmaya yarar ve ekran
        # goruntusu/sunum yoluyla disari sizabilir. Bu kontrol eskisinden
        # DAHA DAR: anahtarin son 4 disindaki HICBIR parcasi gorunmemeli.
        check(sahte not in m, "maskeli gosterim tam anahtari sizdirmaz")
        check("nv" + "api-" not in m, "maskeli gosterim anahtar onekini sizdirmaz")
        check(m.endswith("1234") and m.count("1234") == 1,
              "maskeli gosterim yalnizca son 4 karakteri gosterir")
        check("PLACEHOLDER" not in m,
              "maskeli gosterimde anahtar govdesinden parca yok")
        check(len(m) < 40, "maskeli gosterim kisa (uzunluk sizmasi yok)")
    finally:
        os.environ.pop("NVIDIA_API_KEY", None)
        if eski:
            os.environ["NVIDIA_API_KEY"] = eski


def test_no_key_no_network():
    """Buluta cikan yolda IKI kapi var; ikisi de aga cikmadan reddeder.

    KAPI 1 (yeni): cloud_consent — kullanici BU OTURUMDA acikca izin
    vermediyse istek KURULMAZ. Makinede anahtar bulunmasi izin degildir.
    KAPI 2: anahtar yoksa yine ok=False, istisna yok.
    """
    print("== Bulut cagrisi: once oturum izni, sonra anahtar ==")
    import nvidia_provider as nv
    import cloud_consent

    cloud_consent.reset_for_tests()
    # Anahtar VAR gibi davran; izin olmadigi icin yine de gitmemeli.
    eski_oku = nv.anahtar_oku
    # Assembled from fragments: a token-shaped literal in a source file
    # trips secret scanners and teaches the wrong habit.
    nv.anahtar_oku = lambda: "nv" + "api-" + "PLACEHOLDERBODY" + "1234"
    try:
        s = nv.sohbet({"messages": [{"role": "user", "content": "x"}]})
        check(s["ok"] is False, "izin yokken ok=False")
        check("izin" in (s["hata"] or "").lower() or "consent" in (s["hata"] or "").lower(),
              "izin yokken hata oturum iznini soyler (istek GONDERILMEDI)")
        check(cloud_consent.is_granted() is False,
              "reddedilen cagri kendiliginden izin uretmez")
    finally:
        nv.anahtar_oku = eski_oku

    # Simdi izin ver ama anahtari kaldir: ikinci kapi devrede.
    cloud_consent.grant_for_session("NVIDIA NIM")
    nv.anahtar_oku = lambda: None
    try:
        s = nv.sohbet({"messages": [{"role": "user", "content": "x"}]})
        check(s["ok"] is False and "anahtar" in (s["hata"] or "").lower(),
              "anahtar yoksa ok=False + aciklayici hata (istisna yok)")
    finally:
        nv.anahtar_oku = eski_oku
        cloud_consent.reset_for_tests()
    check(cloud_consent.is_granted() is False, "izin oturum sonunda geri alindi")


def test_window_headless():
    print("== Terminal penceresi (headless Tk) ==")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
    except Exception:
        print("   [SKIP] display yok")
        return
    import types
    import ai_terminal

    class SahteClient:
        model_profiles = {"math": "test-model"}
        def get_models(self):
            return ["test-model"]
        def complete(self, sysp, userp, max_tokens=None, profile="math"):
            return ("CEVAP:\n```python\nprint(2+2)\n```", {}, "stop")

    app = types.SimpleNamespace(client=SahteClient())
    # Toplevel master gerektirir; app ayni zamanda Tk widget gibi davranamaz —
    # gercek kullanim MathCourseApp(tk.Tk). Testte root'a client iliştiririz.
    root.client = SahteClient()
    win = ai_terminal.AITerminalWindow(root)
    check(win.winfo_exists() == 1, "pencere kuruldu")
    check(win.sag_var.get() in ("Yerel (LM Studio)", "NVIDIA NIM"),
          "saglayici varsayilani gecerli")
    win._history = [{"role": "assistant",
                     "content": "```python\nprint('calisti')\n```"}]
    kod, idx = win._son_python_blogu()
    check(kod == "print('calisti')" and idx == 0,
          "son python blogu + asistan mesaj indeksi bulunur")
    win._history.append({"role": "assistant", "content": "kod yok"})
    # Tasarim: son BLOKLU yanit kullanilir (reversed tarama) — bloksuz son
    # yanit varken bir onceki yanitin blogu bulunmali:
    check(win._son_python_blogu()[0] == "print('calisti')",
          "bloksuz son yanitta bir onceki bloklu yanita duser")
    win.destroy()
    root.destroy()


# ═══════════════════════════════════════════════════════════════════════
#  ÇALIŞMA TUTANAĞI (terminal_tutanak.py) — saf mantık, Tk yok
# ═══════════════════════════════════════════════════════════════════════

def _gecici_tutanak():
    """Testler GERÇEK tutanağa asla dokunmaz: her test kendi dosyasını alır."""
    import tempfile
    d = tempfile.mkdtemp(prefix="mca_tutanak_")
    return os.path.join(d, "terminal_tutanak.jsonl")


def test_tutanak_yaz_oku():
    print("== Tutanak: yazma / okuma / sıralama ==")
    import terminal_tutanak as tt
    yol = _gecici_tutanak()
    k1 = tt.kaydet("yerel", "m1", "birinci soru", "birinci yanit",
                   sure=1.234, path=yol)
    k2 = tt.kaydet("nvidia", "z-ai/glm-5.2", "ikinci soru", "ikinci yanit",
                   sure=6.9, path=yol)
    check(bool(k1) and bool(k2) and k1 != k2, "iki kayit yazildi, kimlikler farkli")
    kl = tt.kayitlar(path=yol)
    check(len(kl) == 2, "iki kayit okunuyor")
    check(kl[0]["istem"] == "ikinci soru", "sira YENIDEN ESKIYE")
    check(kl[0]["sure"] == 6.9 and kl[1]["sure"] == 1.23, "sure yuvarlanarak saklanir")
    check(kl[1]["surum"], "kayit program surumuyle damgalanir")
    check(kl[0]["yanit"] == "ikinci yanit", "yanit metni KIRPILMADAN saklanir")
    check(tt.kayitlar(saglayici="nvidia", path=yol)[0]["model"] == "z-ai/glm-5.2",
          "saglayiciya gore filtre")
    check(tt.kayitlar(limit=1, path=yol) and len(tt.kayitlar(limit=1, path=yol)) == 1,
          "limit uygulanir")


def test_tutanak_geriye_uyum():
    print("== Tutanak: bozuk/eksik satır dayanıklılığı ==")
    import terminal_tutanak as tt
    yol = _gecici_tutanak()
    tt.kaydet("yerel", "m", "soru", "yanit", path=yol)
    with open(yol, "a", encoding="utf-8") as f:
        f.write("{bu gecerli json degil\n")                 # bozuk satir
        f.write('{"ts": "2020-01-01 00:00:00", "istem": "eski kayit"}\n')  # eksik alanli
        f.write("\n")                                        # bos satir
    kl = tt.kayitlar(path=yol)
    check(len(kl) == 2, "bozuk satir yutulur, gecerli satirlar okunur")
    eski = [k for k in kl if k["istem"] == "eski kayit"][0]
    check(eski["saglayici"] == "" and eski["kod"] == "" and eski["sure"] is None,
          "eksik alanlar varsayilanla tamamlanir (arayuz cokmez)")
    check(tt.normalize("dizi degil") is None, "sozluk olmayan girdi None doner")
    check(tt.normalize({"sure": "abc"})["sure"] is None, "bozuk sure guvenli okunur")


def test_tutanak_saklama_siniri():
    print("== Tutanak: saklama sınırı (en eski düşer) ==")
    import terminal_tutanak as tt
    yol = _gecici_tutanak()
    for i in range(7):
        tt.kaydet("yerel", "m", f"soru {i}", f"yanit {i}", path=yol, en_fazla=5)
    kl = tt.kayitlar(path=yol)
    check(len(kl) == 5, "sinir uygulanir (5)")
    check(kl[0]["istem"] == "soru 6", "en yeni durur")
    check(all(k["istem"] != "soru 0" for k in kl), "EN ESKI dusmus")
    import glob
    artik = glob.glob(os.path.join(os.path.dirname(yol), ".tutanak_*.tmp"))
    check(not artik, "atomik yazimdan gecici dosya artigi kalmaz")


def test_tutanak_kod_ekleme():
    print("== Tutanak: çalıştırılan kod aynı işe eklenir ==")
    import terminal_tutanak as tt
    yol = _gecici_tutanak()
    kid = tt.kaydet("yerel", "m", "kok bul", "iste kod", sure=2, path=yol)
    tt.kaydet("yerel", "m", "baska is", "baska yanit", path=yol)
    ok = tt.kod_ekle(kid, "print(1+1)", "2", "[bitti, kod 0]", path=yol)
    check(ok, "kod_ekle True doner")
    kl = tt.kayitlar(path=yol)
    check(len(kl) == 2, "ikinci bir satir ACILMAZ (ayni is guncellenir)")
    hedef = [k for k in kl if k["id"] == kid][0]
    check(hedef["kod"] == "print(1+1)" and hedef["kod_cikti"] == "2",
          "kod ve cikti dogru kayda yazildi")
    check(hedef["istem"] == "kok bul", "isin ozgun alanlari bozulmadi")
    digeri = [k for k in kl if k["id"] != kid][0]
    check(digeri["kod"] == "", "diger is etkilenmedi")
    check(tt.kod_ekle("olmayan-id", "x", path=yol) is False, "bilinmeyen id -> False")
    check(tt.kod_ekle("", "x", path=yol) is False, "bos id -> False")


def test_tutanak_arama_ozet():
    print("== Tutanak: arama ve özet ==")
    import terminal_tutanak as tt
    yol = _gecici_tutanak()
    tt.kaydet("yerel", "qwen-math", "türev nasıl alınır", "türev kuralları", path=yol)
    tt.kaydet("nvidia", "glm-5.2", "integral sorusu", "çözüm", path=yol,
              kod="import sympy", kod_cikti="ok")
    check(len(tt.ara("TÜREV", path=yol)) == 1, "buyuk-kucuk harf duyarsiz arama")
    check(len(tt.ara("sympy", path=yol)) == 1, "kod alaninda da arar")
    check(len(tt.ara("glm", path=yol)) == 1, "model adinda arar")
    check(len(tt.ara("", path=yol)) == 2, "bos sorgu = filtre yok")
    check(len(tt.ara("hicbiryerde", path=yol)) == 0, "eslesmeyen sorgu bos doner")
    check(len(tt.ara("integral", saglayici="yerel", path=yol)) == 0,
          "arama + saglayici filtresi birlikte calisir")
    o = tt.ozet(path=yol)
    check(o["toplam"] == 2 and o["kodlu"] == 1, "ozet sayilari")
    check(o["saglayicilar"] == {"yerel": 1, "nvidia": 1}, "saglayici dagilimi")
    check(tt.ozet(path=_gecici_tutanak())["toplam"] == 0,
          "dosya yoksa toplam=0 (istisna degil)")


def test_tutanak_metne_cevir():
    print("== Tutanak: metne aktarma ==")
    import terminal_tutanak as tt
    metin = tt.metne_cevir({"ts": "2026-08-15 05:00:00", "saglayici": "nvidia",
                            "model": "glm-5.2", "istem": "SORUM", "yanit": "YANITIM",
                            "sure": 3.5, "kod": "KODUM", "kod_cikti": "CIKTIM",
                            "kod_durum": "[bitti, kod 0]"})
    check(all(x in metin for x in ("SORUM", "YANITIM", "KODUM", "CIKTIM")),
          "istek/yanit/kod/cikti metne giriyor")
    check("3.5 sn" in metin and "glm-5.2" in metin, "sure ve model basiliyor")
    kodsuz = tt.metne_cevir({"istem": "s", "yanit": "y"})
    check("kod çalıştırılmadı" in kodsuz, "kodsuz iste bu acikca yaziliyor")
    check(tt.metne_cevir({}).count("=" * 70) == 2, "bos kayit bile coken metin uretmez")


def test_tutanak_hata_yutulur():
    print("== Tutanak: kayıt hatası terminali bozmaz ==")
    import terminal_tutanak as tt
    # Yazilamayacak bir yol (klasor yerine dosya-icinde-dosya)
    yol = _gecici_tutanak()
    tt.kaydet("yerel", "m", "s", "y", path=yol)
    bozuk = os.path.join(yol, "alt", "tutanak.jsonl")   # yol bir DOSYA, klasor degil
    check(tt.kaydet("yerel", "m", "s", "y", path=bozuk) is None,
          "yazilamayan yolda None doner (istisna firlatmaz)")
    check(tt.kayitlar(path=bozuk) == [], "okunamayan yolda bos liste")
    check(tt.ozet(path=bozuk)["toplam"] == 0, "ozet de guvenli")


def test_tutanak_terminal_entegrasyonu():
    print("== Tutanak: terminal penceresiyle uçtan uca ==")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
    except Exception:
        print("   [SKIP] display yok")
        return
    import ai_terminal
    import terminal_tutanak as tt

    class SahteClient:
        model_profiles = {"math": "test-model"}
        def get_models(self):
            return ["test-model"]
        def complete(self, sysp, userp, max_tokens=None, profile="math"):
            return ("```python\nprint(2+2)\n```", {}, "stop")

    root.client = SahteClient()
    eski_yol = tt.TUTANAK_PATH
    tt.TUTANAK_PATH = __import__("pathlib").Path(_gecici_tutanak())
    try:
        win = ai_terminal.AITerminalWindow(root)
        win._history = [{"role": "user", "content": "kare kokleri yaz"},
                        {"role": "assistant", "content": "```python\nprint(2+2)\n```"}]
        kid = win._tutanaga_yaz(ai_terminal.YEREL, "test-model", "kare kokleri yaz",
                                "```python\nprint(2+2)\n```", None, 1.5)
        check(bool(kid), "tamamlanan is tutanaga yazildi")
        check(win._tutanak_ids.get(1) == kid, "kimlik asistan mesajinin indeksine baglandi")
        kayit = tt.kayitlar()[0]
        check(kayit["istem"] == "kare kokleri yaz" and kayit["durum"] == "ok",
              "istek metni ve durum dogru")

        kod, idx = win._son_python_blogu()

        # DEGISEN DAVRANIS: kod calistirma bu surumde VARSAYILAN OLARAK KAPALI
        # (gercek bir OS kum havuzu yetismedi). Kapali oldugunda ALT SUREC
        # ACILMAZ; kayda "kapali" durumu duser. Bu, eski beklentiden daha dar
        # bir kontrol: sadece cikti degil, hic calismadigi da dogrulanir.
        import ai_code_guard
        os.environ.pop(ai_code_guard.ENABLE_ENV_VAR, None)
        check(ai_code_guard.execution_enabled() is False,
              "kod calistirma varsayilan olarak KAPALI")
        win._kod_kos(kod, win._tutanak_ids.get(idx))
        guncel = tt.kayitlar()[0]
        check(guncel["kod"] == "print(2+2)", "calistirilan kod ayni kayda islendi")
        check("4" not in (guncel["kod_cikti"] or ""),
              "kapaliyken alt surec CALISMAZ (cikti yok)")

        # Acikca acildiginda: politika gecer, alt surec kosar, cikti kayda duser.
        os.environ[ai_code_guard.ENABLE_ENV_VAR] = "1"
        try:
            check(ai_code_guard.execution_enabled() is True, "acik onay ile etkinlesir")
            win._kod_kos(kod, win._tutanak_ids.get(idx))
            guncel = tt.kayitlar()[0]
            check("4" in (guncel["kod_cikti"] or ""), "alt surec ciktisi kayda dustu")
        finally:
            os.environ.pop(ai_code_guard.ENABLE_ENV_VAR, None)
        check(len(tt.kayitlar()) == 1, "kod calismasi ikinci kayit ACMAZ")

        hatali = win._tutanaga_yaz(ai_terminal.NVIDIA, "glm", "soru", "", "baglanti yok", None)
        check(tt.kayitlar()[0]["durum"] == "hata",
              "hatali istek de tutanaga 'hata' olarak girer")
        check(hatali not in win._tutanak_ids.values(),
              "yanitsiz kayit indeks haritasina baglanmaz")

        # Tutanak penceresi gercekten kuruluyor ve kayitlari listeliyor mu
        tw = ai_terminal.TutanakWindow(win)
        check(tw.winfo_exists() == 1, "tutanak penceresi kuruldu")
        check(len(tw.tree.get_children()) == 2, "iki is listelendi")
        tw.ara_var.set("kare kokleri")
        check(len(tw.tree.get_children()) == 1, "arama kutusu listeyi filtreler")
        tw.ara_var.set("")
        tw.tree.selection_set("0")
        tw._goster()
        check("İSTEK" in tw.detay.get("1.0", "end"), "secili is detayda gosteriliyor")
        # Ekran dogrulamasinda yakalanan iki kusurun regresyon testi:
        import types as _t
        eski_sarma = win.aciklama_lbl.cget("wraplength")
        win._sarmayi_esitle(_t.SimpleNamespace(width=520, widget=win))
        check(win.aciklama_lbl.cget("wraplength") < eski_sarma,
              "dar pencerede aciklama sarmasi kuculur (sagdan kesilmez)")
        win._sarmayi_esitle(_t.SimpleNamespace(width=120, widget=win))
        check(win.aciklama_lbl.cget("wraplength") >= 280, "sarma taban degerin altina inmez")
        win._sarmayi_esitle(_t.SimpleNamespace(width=99999, widget=win.inp))
        check(win.aciklama_lbl.cget("wraplength") < 1000,
              "alt widget'in Configure olayi sarmayi degistirmez")
        giris = [w for w in tw.winfo_children()[3].winfo_children()
                 if isinstance(w, tk.Entry)]
        check(giris and int(giris[0].cget("highlightthickness")) >= 1,
              "arama kutusunun gorunur cercevesi var (koyu temada kayboluyordu)")

        tw.destroy()
        win.destroy()
    finally:
        tt.TUTANAK_PATH = eski_yol
        root.destroy()


def main():
    print("=" * 64)
    print("AI Terminali — Test Suite")
    print("=" * 64)
    for fn in (test_block_extraction, test_provider_payload, test_key_handling,
               test_no_key_no_network, test_window_headless,
               test_tutanak_yaz_oku, test_tutanak_geriye_uyum,
               test_tutanak_saklama_siniri, test_tutanak_kod_ekleme,
               test_tutanak_arama_ozet, test_tutanak_metne_cevir,
               test_tutanak_hata_yutulur, test_tutanak_terminal_entegrasyonu):
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
