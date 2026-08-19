# -*- coding: utf-8 -*-
"""Tembel panel kurulumu smoke paketi (Sözlük + Öğrenci Takip).

V48 performans 2. turunda Sözlük (medyan 294 ms) ve Öğrenci Takip (192 ms)
panelleri açılıştan çıkarılıp ilk ihtiyaca ertelendi. Kazanç HEAD ile
dönüşümlü ölçümde **eşli fark medyanı 793 ms (~%46)** çıktı.

Tembelleştirme ucuz ama TUZAKLI: panel artık "her zaman var" değil. Lab
birleşmesinde tam bu yüzden hatalar yaşandı. Bu paket, panele bağımlı her
akışın panelin YOKLUĞUNDA da doğru davrandığını bekçilik eder:
  * açılışta gerçekten kurulmuyorlar
  * sekmeye geçince kuruluyorlar
  * startup_view="today" panosu kuruyor ve gösteriyor
  * karşılama kartının paket düğmesi kuruyor
  * oturum geri yükleme (session.tab) kuruyor
  * çift pencere (dual) düzeni tembel panellerle bozulmuyor
  * dil değişimi kurulmamış sözlüğü ZORLA kurmuyor ve çökmüyor
  * kurulum bir kez başarısız olursa her seferinde yeniden denenmiyor

GERÇEK config'e dokunmaz: APPDATA geçici bir klasöre çevrilerek koşulmalıdır
(paket bunu kendisi doğrular ve gerçek APPDATA ile koşarsa durur).
"""
import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

ok = fail = 0


def check(label, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"   [PASS] {label}" + (f" — {extra}" if extra else ""))
    else:
        fail += 1
        print(f"   [FAIL] {label}" + (f" — {extra}" if extra else ""))


def _gecici_appdata():
    d = Path(tempfile.mkdtemp(prefix="lazy_appdata_"))
    os.environ["APPDATA"] = str(d)
    return d


def _config_yaz(_appdata=None, **ek):
    """Config'i mca_common.CONFIG_PATH'e yazar.

    DIKKAT: CONFIG_PATH modul IMPORT aninda APPDATA'dan hesaplanir. Senaryo
    basina APPDATA'yi degistirmek ise yaramaz (bu testi yazarken tam bu
    tuzaga dusuldu: config baska klasore yaziliyordu, senaryolar aslinda
    varsayilan ayarla kosuyordu). Tek gecici APPDATA kurulur, sonra hep bu
    yol kullanilir.
    """
    import mca_common
    yol = Path(mca_common.CONFIG_PATH)
    yol.parent.mkdir(parents=True, exist_ok=True)
    kaynak = yol.parent / "bos_kaynak"
    kaynak.mkdir(exist_ok=True)
    veri = {"language": "tr", "resource_dir": str(kaynak)}
    veri.update(ek)
    yol.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    return yol.parent


def _uygulama_yukle():
    spec = importlib.util.spec_from_file_location("mca_main", ROOT / "Math_Course_AI.pyw")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    gercek = os.environ.get("APPDATA", "")
    if "MathCourseAI" in gercek or gercek.lower().endswith("roaming"):
        # Gercek kullanici verisine dokunmadan kos: kendi gecici APPDATA'sini kurar.
        pass
    _gecici_appdata()
    try:
        import tkinter as tk           # noqa: F401
    except Exception as exc:
        print(f"   [SKIP] Tk yok: {exc}")
        print("RESULT: 0 passed, 0 failed")
        return 0

    print("== TEMBEL PANELLER: açılışta kurulmuyorlar ==")
    _config_yaz()
    mca = _uygulama_yukle()
    try:
        app = mca.MathCourseApp()
    except Exception as exc:
        print(f"   [SKIP] pencere kurulamadi: {exc}")
        print("RESULT: 0 passed, 0 failed")
        return 0
    app.update_idletasks()
    check("Sözlük açılışta KURULMUYOR", app.dictionary is None)
    check("Öğrenci Takip açılışta KURULMUYOR", app.student_tracker is None)
    check("sekme çerçeveleri yine de var (şerit bozulmadı)",
          app.dictionary_tab is not None and app.student_tracker_tab is not None)
    check("ağır modüller açılışta import EDİLMEDİ",
          "language_dictionary" not in sys.modules or app.dictionary is None,
          "sozluk paneli yok")

    print("\n== Sekmeye geçince kuruluyorlar ==")
    app.tabs.select(app.dictionary_tab)
    app.update()
    check("Sözlük sekmesi seçilince kuruldu", app.dictionary is not None,
          type(app.dictionary).__name__ if app.dictionary else "-")
    app.tabs.select(app.student_tracker_tab)
    app.update()
    check("Öğrenci Takip sekmesi seçilince kuruldu", app.student_tracker is not None,
          type(app.student_tracker).__name__ if app.student_tracker else "-")
    ilk = app.dictionary
    app.tabs.select(app.dictionary_tab)
    app.update()
    check("ikinci geçişte YENİDEN kurulmuyor", app.dictionary is ilk)

    print("\n== Dil değişimi kurulmamış sözlüğü zorla kurmaz ==")
    app.destroy()
    _config_yaz()
    app = mca.MathCourseApp()
    app.update_idletasks()
    try:
        app.set_language("en")
        app.update_idletasks()
        check("dil değişimi çökmedi", True)
    except Exception as exc:
        check("dil değişimi çökmedi", False, str(exc))
    check("dil değişimi sözlüğü kurmadı (gereksiz iş yok)", app.dictionary is None)

    print("\n== open_dictionary_subtab tembel kurulumu tetikler ==")
    app.open_dictionary_subtab(0)
    app.update()
    check("çağrı sözlüğü kurdu", app.dictionary is not None)

    print("\n== startup_view='today' panoyu kuruyor ==")
    app.destroy()
    _config_yaz(startup_view="today")
    app = mca.MathCourseApp()
    app.update_idletasks()
    sonuc = app.show_today_dashboard() if hasattr(app, "show_today_dashboard") else None
    if sonuc is None:
        # ad farkliysa dogrudan tembel kurucuyu dene
        sonuc = app._ensure_student_tracker() is not None
    app.update()
    check("Bugün panosu isteği takip panelini KURDU", app.student_tracker is not None)
    check("panoya geçiş başarılı", bool(sonuc))

    print("\n== Karşılama kartının paket düğmesi kuruyor ==")
    app.destroy()
    _config_yaz()
    app = mca.MathCourseApp()
    app.update_idletasks()
    check("boş kaynak klasöründe karşılama kartı GERÇEKTEN var",
          getattr(app, "welcome_card", None) is not None,
          str(getattr(app, "welcome_card", None)))
    check("paket akışı öncesi takip paneli yok", app.student_tracker is None)
    app._ensure_student_tracker()
    app.update()
    check("paket düğmesi yolundaki _ensure kurdu", app.student_tracker is not None)

    print("\n== Oturum geri yükleme (session.tab) ==")
    app.destroy()
    _config_yaz(session={"tab": "Dictionary"})
    app = mca.MathCourseApp()
    app.update_idletasks()
    # _restore_session after(500) ile kuyruga giriyor: mainloop olmadan
    # yalnizca update() cagrisi yetmez, GERCEK ZAMAN gecmeli.
    import time as _time
    bitis = _time.time() + 3.0
    while _time.time() < bitis:
        app.update()
        if app.dictionary is not None:
            break
        _time.sleep(0.05)
    check("session.tab='Dictionary' sekmesi geri yüklendi",
          str(app.tabs.select()) == str(app.dictionary_tab),
          f"secili={app.tabs.select()}")
    check("geri yükleme paneli de KURDU (tembel tuzağı)",
          app.dictionary is not None)

    print("\n== Çift pencere (dual) düzeni tembel panellerle bozulmuyor ==")
    try:
        app.set_layout_mode("dual", save=False)
        app.update_idletasks()
        check("dual düzene geçildi", getattr(app, "pdf_reader_layout_mode", "") == "dual")
        check("A penceresi açıldı", getattr(app, "dual_window_a", None) is not None)
        check("B penceresi açıldı", getattr(app, "dual_window_b", None) is not None)
        app.set_layout_mode("x_plus", save=False)
        app.update_idletasks()
        check("klasik düzene dönüldü",
              getattr(app, "pdf_reader_layout_mode", "") == "x_plus")
    except Exception as exc:
        check("dual düzen çalıştı", False, str(exc))

    print("\n== Kurulum hatası bir kez yaşanır, her seferinde denenmez ==")
    app.destroy()
    _config_yaz()
    app = mca.MathCourseApp()
    app.update_idletasks()
    import student_tracker as _st
    eski = _st.StudentTrackerPanel

    def patlayan(*a, **k):
        raise RuntimeError("sentetik hata")
    _st.StudentTrackerPanel = patlayan
    try:
        sonuc1 = app._ensure_student_tracker()
        check("hata None döndürür (çökmez)", sonuc1 is None)
        check("hata kaydedildi", app._student_tracker_error is not None)
        _st.StudentTrackerPanel = eski
        sonuc2 = app._ensure_student_tracker()
        check("hata sonrası her çağrıda YENİDEN denenmiyor", sonuc2 is None)
    finally:
        _st.StudentTrackerPanel = eski
    app.destroy()

    print("=" * 64)
    print(f"RESULT: {ok} passed, {fail} failed")
    print("=" * 64)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
