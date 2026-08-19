# -*- coding: utf-8 -*-
"""Claim-truth suite: the public documents may not say things the code does not do.

This suite exists because the most likely defect in this repository is no longer a
crash — it is a sentence. It checks three families of claim:

  1. NUMBERS   every count printed in README / the deck / the manifest must equal
               what tools/measure_facts.py measures, or the recorded test run.
  2. HONESTY   forbidden absolutes ("fully offline", "nothing leaves the machine",
               "sandboxed", "zero errors", a CI badge) must not reappear, and the
               documents must state the cloud path and the disabled feature.
  3. RESIDUE   no maintainer path, no sibling-product name, no third-party course
               brand, no key-shaped literal anywhere in the shipped tree.

Run headless, no network, writes nothing outside a temp directory.
"""

import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MATH_COURSE_AI_SETTINGS", tempfile.mkdtemp(prefix="mcai-cs-"))
os.environ.setdefault("MATH_COURSE_AI_EXPORTS", tempfile.mkdtemp(prefix="mcai-ce-"))

PASSED = 0
FAILED = 0
SELF = Path(__file__).name


def check(cond, label):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"   [PASS] {label}")
    else:
        FAILED += 1
        print(f"   [FAIL] {label}")


def _read(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


# Built from fragments so this file does not match its own scans.
_SIBLING = "Finansal" + "AnalizPro"
_SIBLING_SHORT = "FA" + "P"
_MAINT_DIR = "D:" + chr(92) + "Math"
_USERS_DIR = "C:" + chr(92) + "Users"
_BRANDS = ["Ud" + "emy", "Become a" + "n Algebra Master", "Master the Fund" + "amentals of Math"]
_KEY_SHAPES = [r"nvapi-[A-Za-z0-9_\-]{16,}", r"sk-[A-Za-z0-9]{20,}",
               r"ghp_[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}", r"AIza[0-9A-Za-z_\-]{20,}",
               r"hf_[A-Za-z0-9]{20,}", r"glpat-[A-Za-z0-9_\-]{16,}",
               r"-----BEGIN [A-Z ]*PRIVATE KEY-----"]

TEXT_SUFFIXES = {".py", ".pyw", ".md", ".txt", ".json", ".yml", ".yaml", ".ps1",
                 ".bat", ".cfg", ".ini", ".toml", ".example", ".html", ".spec"}


def _shipped_text_files():
    out = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        parts = set(p.parts)
        # Skip build/runtime output that .gitignore already keeps out of git.
        if parts & {"__pycache__", ".git", ".venv", "venv", "build", "dist",
                    "exports", "settings", "data", "Resources"}:
            continue
        if p.suffix.lower() in TEXT_SUFFIXES or p.name in (".gitignore", ".gitattributes"):
            out.append(p)
    return out


# ══════════════════════════════════════════════════════════════════════════
# 1. REQUIRED PUBLIC FILES
# ══════════════════════════════════════════════════════════════════════════
REQUIRED = ["README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "SECURITY.md",
            "PRIVACY.md", "AI_TRANSPARENCY.md", "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md", "CHANGELOG.md", "docs/known-limitations.md",
            ".env.example", ".gitignore", ".github/dependabot.yml",
            ".github/workflows/ci.yml", "requirements.txt",
            "requirements-optional.txt", "PUBLIC_RELEASE_MANIFEST.json"]


def test_public_file_set():
    print("== Kamuya acik dosya kumesi eksiksiz ==")
    for rel in REQUIRED:
        check((ROOT / rel).is_file(), f"{rel} var")
    lic = _read("LICENSE")
    check("MIT License" in lic or "MIT Licence" in lic, "LICENSE MIT")
    # Every relative link the README makes must resolve
    kirik = []
    for hedef in re.findall(r"\]\(([^)#:]+?)\)", _read("README.md")):
        h = hedef.strip()
        if h.startswith(("http", "mailto", "#", "<")):
            continue
        if not (ROOT / h).exists():
            kirik.append(h)
    check(not kirik, f"README'deki dosya baglantilari cozuluyor (kirik: {kirik[:5]})")


# ══════════════════════════════════════════════════════════════════════════
# 2. NUMBERS MUST BE MEASURED
# ══════════════════════════════════════════════════════════════════════════
def test_numbers_are_measured():
    print("== Belgelerdeki sayilar OLCULEN degerlerle ayni ==")
    sys.path.insert(0, str(ROOT / "tools"))
    import measure_facts
    f = measure_facts.measure()

    import tanitim_icerik as ti
    deck = json.dumps(ti.SLAYTLAR, ensure_ascii=False)

    def deckte(sayi):
        s = str(sayi)
        bosluklu = f"{int(sayi):,}".replace(",", " ")
        virgullu = f"{int(sayi):,}"
        return any(x in deck for x in (s, bosluklu, virgullu))

    check(deckte(f["topic_knowledge_entries"]),
          f"konu girisi sayisi ({f['topic_knowledge_entries']}) destede olculen degerle ayni")
    check(str(f["embedded_simulations"]) in deck and str(f["formula_cards"]) in deck,
          f"simulasyon/formul sayilari ({f['embedded_simulations']}/{f['formula_cards']}) dogru")
    check(deckte(f["workspaces"]), f"calisma alani sayisi ({f['workspaces']}) dogru")
    check(str(f["science_labs"]) in deck, f"bilim lab sayisi ({f['science_labs']}) dogru")
    check(str(f["guide_chapters"]) in deck, f"kilavuz bolum sayisi ({f['guide_chapters']}) dogru")

    # Retired claims must not come back
    for eski in ("667", "668", "2 181", "2,181", "2209", "%46", "46% faster"):
        check(eski not in deck, f"geri cekilen sayi destede yok: {eski}")

    # The manifest is the single source of truth for the test totals, and the
    # deck must agree with it.
    man = json.loads(_read("PUBLIC_RELEASE_MANIFEST.json") or "{}")
    toplam = (man.get("verification", {}).get("tests", {}) or {}).get("checks_passed")
    atlanan = (man.get("verification", {}).get("tests", {}) or {}).get("checks_skipped")
    check(isinstance(toplam, int) and toplam > 0, "manifest test toplamini kaydediyor")
    if isinstance(toplam, int):
        check(deckte(toplam), f"deste test toplami manifestle ayni ({toplam})")
    if isinstance(atlanan, int):
        check(deckte(atlanan), f"deste atlanan kontrol sayisi manifestle ayni ({atlanan})")
    check(man.get("verification", {}).get("tests", {}).get("checks_failed") == 0,
          "manifest sifir basarisiz kontrol kaydediyor (yoksa yayinlanmamali)")

    # Screenshots referenced by the deck actually exist, in both languages
    kayip = []
    for s in ti.SLAYTLAR:
        adlar = []
        if s.get("tip") == "gorsel" and s.get("gorsel"):
            adlar.append(s["gorsel"])
        if s.get("tip") == "galeri":
            adlar += [o[0] for o in (s.get("ogeler") or [])
                      if isinstance(o, (tuple, list)) and isinstance(o[0], str)]
        for ad in adlar:
            for dil in ("tr", "en"):
                if not (ROOT / "tanitim_gorseller" / dil / ad).is_file():
                    kayip.append(f"{dil}/{ad}")
    check(not kayip, f"destedeki her gorsel depoda var (eksik: {kayip[:5]})")
    check(f["screenshots"] == 16, f"16 ekran goruntusu ({f['screenshots']})")


# ══════════════════════════════════════════════════════════════════════════
# 3. HONESTY OF THE PUBLIC DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════
FORBIDDEN_ABSOLUTES = [
    "fully offline", "100% offline", "completely offline",
    "nothing leaves the machine", "no data ever leaves",
    "no cloud, no account, no internet", "no internet required",
    "%100 yerel", "tamamen çevrimdışı", "veri bilgisayardan çıkmaz",
    "bulut yok, hesap yok, internet yok",
    "0 hata", "zero errors", "0 failures", "sıfır hata",
]


def test_no_false_absolutes():
    print("== Yanlis mutlak iddialar geri gelmemis ==")
    belgeler = ["README.md", "PRIVACY.md", "AI_TRANSPARENCY.md", "SECURITY.md",
                "docs/known-limitations.md", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md"]
    import tanitim_icerik as ti
    metinler = {rel: _read(rel).lower() for rel in belgeler}
    metinler["<deste>"] = json.dumps(ti.SLAYTLAR, ensure_ascii=False).lower()

    for rel, metin in metinler.items():
        for kalip in FORBIDDEN_ABSOLUTES:
            k = kalip.lower()
            # the README is allowed to QUOTE the retired claim while denying it
            if rel == "README.md" and k == "fully offline" and '"fully offline"' in metin:
                continue
            check(k not in metin, f"{rel}: yasak mutlak ifade yok -> {kalip}")

    readme = _read("README.md")
    check("![" not in readme.split("## ")[0] or "badge" not in readme.lower(),
          "README'de CI rozeti YOK")
    check("shields.io" not in readme and "badge.svg" not in readme,
          "README'de rozet URL'si YOK")

    # The README must actively disclose the things that used to be hidden
    for parca, etiket in [
        ("NVIDIA", "bulut saglayici adiyla aciklanir"),
        ("optional", "bulut saglayici ISTEGE BAGLI diye yazilir"),
        ("consent", "oturumluk onay anlatilir"),
        ("synthetic", "demo verinin sentetik oldugu yazilir"),
        ("AGPL", "PyMuPDF/AGPL durumu yazilir"),
        ("MATH_COURSE_AI_ENABLE_CODE_EXECUTION", "kod calistirma anahtari yazilir"),
        ("beta", "olgunluk seviyesi yazilir"),
    ]:
        check(parca.lower() in readme.lower(), f"README: {etiket}")

    for parca in ("financial", "legal", "medical"):
        check(parca in readme.lower(), f"README: '{parca}' tavsiyesi verilmedigi yazilir")

    # "sandbox" may only appear as a denial, never as a feature claim
    kd = _read("docs/known-limitations.md").lower()
    check("not a sandbox" in kd or "sandbox could not" in kd or "no os-enforced" in kd
          or "not an operating-system security boundary" in kd.lower(),
          "known-limitations kum havuzu OLMADIGINI soyler")
    check("bypassable" in kd or "can be bypassed" in kd,
          "known-limitations statik denetimin atlatilabilir oldugunu soyler")

    ait = _read("AI_TRANSPARENCY.md").lower()
    for parca in ("retention", "region", "training opt-out", "cost cap"):
        check(parca in ait, f"AI_TRANSPARENCY eksigi acikca yazar: {parca}")

    sec = _read("SECURITY.md").lower()
    check("bootstrap" in sec and "there are none" in sec,
          "SECURITY varsayilan kimlik bilgisi OLMADIGINI yazar")


# ══════════════════════════════════════════════════════════════════════════
# 4. RESIDUE
# ══════════════════════════════════════════════════════════════════════════
def test_no_residue():
    print("== Kalinti taramasi: yol, kardes urun, marka, anahtar ==")
    dosyalar = [p for p in _shipped_text_files() if p.name != SELF]
    check(len(dosyalar) > 40, f"metin dosyalari tarandi ({len(dosyalar)})")

    bulgular = {"maintainer_path": [], "sibling": [], "brand": [], "key": []}
    for p in dosyalar:
        metin = p.read_text(encoding="utf-8", errors="replace")
        rel = p.relative_to(ROOT).as_posix()
        if _MAINT_DIR in metin or _USERS_DIR in metin:
            bulgular["maintainer_path"].append(rel)
        if _SIBLING in metin or re.search(r"\b%s\b" % _SIBLING_SHORT, metin):
            bulgular["sibling"].append(rel)
        for b in _BRANDS:
            if b.lower() in metin.lower():
                bulgular["brand"].append(f"{rel}:{b[:8]}")
        for rx in _KEY_SHAPES:
            if re.search(rx, metin):
                bulgular["key"].append(f"{rel}:{rx[:12]}")

    check(not bulgular["maintainer_path"],
          f"gelistirici mutlak yolu YOK ({bulgular['maintainer_path'][:3]})")
    check(not bulgular["sibling"],
          f"yayinlanmamis kardes urun izi YOK ({bulgular['sibling'][:3]})")
    check(not bulgular["brand"],
          f"ucuncu taraf kurs markasi YOK ({bulgular['brand'][:3]})")
    check(not bulgular["key"], f"anahtar bicimli deger YOK ({bulgular['key'][:3]})")

    # Files that must not be in a public tree at all
    for yasak in ["GELECEK_ISLER.md", "ONERILER.md", "build_v42_log.txt",
                  "Yedekle_ve_Gonder.bat", "Math Course AI.spec",
                  "build_math_course_ai_exe.bat", "_qa_verify_sources.py",
                  ".secrets.baseline"]:
        check(not (ROOT / yasak).exists(), f"ic belge/otomasyon depoda yok: {yasak}")
    check(not (ROOT / "scripts").exists(), "otomatik push boru hatti tamamen yok")
    check(not list(ROOT.glob("*_backup_*.py")), "olu yedek modul yok")

    # .env.example must be inert
    env = _read(".env.example")
    check(env.strip(), ".env.example var ve bos degil")
    for satir in env.splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#") or "=" not in satir:
            continue
        deger = satir.split("=", 1)[1].strip().strip('"').strip("'")
        check(deger == "" or deger.startswith("YOUR_") or deger.endswith("_HERE"),
              f".env.example degeri bos ya da yer tutucu: {satir.split('=')[0]}")
    for rx in _KEY_SHAPES:
        check(not re.search(rx, env), ".env.example'da anahtar bicimli deger yok")


# ══════════════════════════════════════════════════════════════════════════
# 5. CI WORKFLOW SANITY
# ══════════════════════════════════════════════════════════════════════════
def test_ci_workflow():
    print("== CI is akisi ==")
    ci = _read(".github/workflows/ci.yml")
    check("permissions:" in ci and "contents: read" in ci, "en dar izin (contents: read)")
    check("pull_request_target" not in ci, "pull_request_target KULLANILMAZ")
    check("requirements.txt" in ci, "bagimliliklar sabitlenmis dosyadan kurulur")
    for suite in ("test_ai_code_guard.py", "test_public_claims.py",
                  "test_student_tracker.py", "smoke_lazy_panels.py"):
        check(suite in ci, f"CI {suite} kosar")
    check("secrets." not in ci, "CI hicbir gizli degere dokunmaz")
    check("uses: actions/checkout@" in ci, "checkout kullanilir")
    # actions must be pinned to a full 40-char commit SHA
    for m in re.finditer(r"uses:\s*([\w\-./]+)@([^\s#]+)", ci):
        ad, ref = m.group(1), m.group(2)
        check(re.fullmatch(r"[0-9a-f]{40}", ref) is not None,
              f"{ad} tam commit SHA'sina sabitlenmis ({ref[:12]})")

    dep = _read(".github/dependabot.yml")
    check("package-ecosystem" in dep and "pip" in dep, "dependabot pip icin yapilandirilmis")
    check("github-actions" in dep, "dependabot GitHub Actions icin yapilandirilmis")


# ══════════════════════════════════════════════════════════════════════════
# 6. CODE MATCHES THE DOCUMENTED BEHAVIOUR
# ══════════════════════════════════════════════════════════════════════════
def test_code_matches_docs():
    print("== Kod, belgelerin soyledigini gercekten yapiyor ==")
    import ai_code_guard as g
    import cloud_consent as cc
    import nvidia_provider as nv

    check(g.execution_enabled({}) is False,
          "belge 'varsayilan kapali' diyor, kod da kapali")
    cc.reset_for_tests()
    check(cc.is_granted() is False, "belge 'oturumluk onay' diyor, kod izinsiz basliyor")
    check(cc.state()["persisted"] is False, "belge 'diske yazilmaz' diyor, kod yazmiyor")

    src = (ROOT / "nvidia_provider.py").read_text(encoding="utf-8")
    check(src.count("_ANAHTAR_HEDEF") >= 1 and _SIBLING not in src,
          "yalnizca bu programin kendi kimlik kaydi okunur")
    check("cloud_consent.is_granted()" in src, "saglayici onay kapisini kodda tasir")

    eski = nv.anahtar_oku
    sahte = "nv" + "api-" + "PLACEHOLDERBODY" + "1234"   # assembled: not scanner bait
    nv.anahtar_oku = lambda: sahte
    try:
        m = nv.anahtar_maskeli()
        check("nv" + "api-" not in m and "PLACEHOLDERBODY" not in m and m.endswith("1234"),
              "belge 'yalnizca son 4' diyor, kod da oyle yapiyor")
    finally:
        nv.anahtar_oku = eski

    # Every fitz import must be optional, as THIRD_PARTY_NOTICES claims
    sert = []
    for p in list(ROOT.glob("*.py")) + list(ROOT.glob("*.pyw")):
        satirlar = p.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, satir in enumerate(satirlar):
            if re.match(r"\s*import\s+(fitz|pymupdf)\b", satir):
                onceki = "\n".join(satirlar[max(0, i - 6):i])
                if "try:" not in onceki:
                    sert.append(f"{p.name}:{i + 1}")
    check(not sert, f"her fitz/PyMuPDF ice aktarimi ISTEGE BAGLI (sert: {sert})")

    tpn = _read("THIRD_PARTY_NOTICES.md")
    check("AGPL-3.0" in tpn and "no binary" in tpn.lower(),
          "THIRD_PARTY_NOTICES AGPL kararini ve ikili dagitmama sozunu yazar")
    req = _read("requirements.txt").lower()
    check("pymupdf" not in req, "PyMuPDF ZORUNLU bagimliliklarda DEGIL")
    check("pymupdf" in _read("requirements-optional.txt").lower(),
          "PyMuPDF istege bagli bagimliliklarda")
    for pin in ("sympy==", "numpy==", "matplotlib==", "pillow==", "requests=="):
        check(pin in req, f"surum sabitlenmis: {pin[:-2]}")

    # The PUBLISHED pdf is rendered by tanitim_pdf.py with a libre font only.
    import tanitim_pdf as tp
    check(tp.FONT_LIBRE is True, f"yayinlanan PDF libre yazi tipi kullanir ({tp.FONT_AILESI})")
    check(tp.FONT_AILESI in tpn, "kullanilan yazi tipi THIRD_PARTY_NOTICES'ta kayitli")
    check(matplotlib_fonttype_42(), "PDF TrueType alt kumesi gomer (pdf.fonttype=42)")
    for ad in ("Math_Course_AI_Tanitim_TR_PUBLIC.pdf", "Math_Course_AI_Intro_EN_PUBLIC.pdf"):
        yol = ROOT / "docs" / "presentation" / ad
        check(yol.is_file() and yol.stat().st_size > 100_000,
              f"yayinlanan sunum dosyasi var ve bos degil: {ad}")


def matplotlib_fonttype_42():
    import matplotlib
    import tanitim_pdf  # noqa: F401  (sets the rcParam on import)
    return matplotlib.rcParams.get("pdf.fonttype") == 42


def main():
    test_public_file_set()
    test_numbers_are_measured()
    test_no_false_absolutes()
    test_no_residue()
    test_ci_workflow()
    test_code_matches_docs()
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 64)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
