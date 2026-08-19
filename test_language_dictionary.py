# -*- coding: utf-8 -*-
"""
Tests for the Language & Science Dictionary (logic layer, head-less).

Run with:
    python test_language_dictionary.py
"""

import sys
import os
import tempfile
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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


def _tmp_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite", prefix="langdict_")
    os.close(fd)
    os.unlink(path)
    return path


def test_import():
    print("\nIMPORT")
    import language_dictionary as ld                                   # item 1
    for cls in ("DictionaryStore", "TranslationHistoryStore", "LMStudioTranslationClient",
                "ImageTranslationPipeline", "LanguageModelProfileManager", "LanguageDictionaryPanel"):
        check(hasattr(ld, cls), f"{cls} import")


def test_store_terms():
    print("\nDICTIONARY STORE — terms")
    from language_dictionary import DictionaryStore
    store = DictionaryStore(_tmp_db())                                 # item 2
    check(store.count_terms() == 0, "fresh store is empty")
    store.add_term("derivative", "türev", lang="en", category="Calculus",
                   en_explanation="rate of change", example="d/dx x^2 = 2x")  # item 3
    rows = store.search_terms("deriv")
    check(len(rows) == 1 and rows[0]["term"] == "derivative", "add + search term")
    check(rows[0]["translation"] == "türev", "dictionary results contain Turkish translation")
    n1 = store.increment_search_count("derivative", "en")             # item 4
    n2 = store.increment_search_count("derivative", "en")
    check(n2 == n1 + 1 and n2 == 2, "search_count increments")
    # seed only runs when empty
    seeded = store.seed_terms([{"en": "x", "tr": "y"}])
    check(seeded == 0, "seed skipped when dictionary already has terms")


def test_translation_column_migration():
    print("\nSEARCH HISTORY TRANSLATION MIGRATION")
    from language_dictionary import DictionaryStore, TranslationHistoryStore
    path = _tmp_db()
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE search_history (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT, result TEXT)")
    conn.execute("INSERT INTO search_history (query, result) VALUES (?, ?)", ("old", "old result"))
    conn.commit()
    conn.close()
    store = DictionaryStore(path)
    cols = {r["name"] for r in store.conn.execute("PRAGMA table_info(search_history)").fetchall()}
    for col in ("translation", "short_translation", "category", "source_context",
                "source_lang", "target_lang", "model_used", "timestamp"):
        check(col in cols, f"migration adds search_history.{col}")
    hist = TranslationHistoryStore(store)
    hist.add_search("run", "English", "Turkish", "koşmak", "local", translation="koşmak")
    check(hist.list_search()[0]["translation"] == "koşmak", "migrated table accepts translation writes")


def test_extract_short_translation():
    print("\nSHORT TRANSLATION EXTRACTION")
    from language_dictionary import extract_short_translation
    sample = "run kelimesi Türkçede 'koşmak', 'çalıştırmak' veya bağlama göre 'işlemek' anlamına gelir."
    check(extract_short_translation("run", sample) == "koşmak / çalıştırmak / işlemek",
          "quoted Turkish meanings extracted")
    check(extract_short_translation("go", "go -> gitmek") == "gitmek", "arrow format extracted")
    long = "This term means a useful compact explanation that should be clipped cleanly after the first sentence. More text."
    check(extract_short_translation("x", long).startswith("This term means"), "fallback first sentence extracted")


def test_favorites():
    print("\nFAVORITES")
    from language_dictionary import DictionaryStore
    store = DictionaryStore(_tmp_db())
    store.add_term("integral", "integral", lang="en")
    store.set_favorite("integral", True)                              # item 7
    favs = store.list_favorites()
    check(len(favs) == 1 and favs[0]["term"] == "integral", "favorite added + listed")
    check(favs[0]["display_translation"] == "integral", "favorite row contains Turkish translation")
    store.set_favorite("integral", False)
    check(len(store.list_favorites()) == 0, "favorite removed")


def test_frequent():
    print("\nFREQUENT")
    from language_dictionary import DictionaryStore
    store = DictionaryStore(_tmp_db())
    for t in ("a", "b", "c"):
        store.add_term(t, lang="en")
    store.add_term("run", "koşmak / çalıştırmak", lang="en", category="general")
    for _ in range(3):
        store.increment_search_count("c", "en")
        store.increment_search_count("run", "en")
    store.increment_search_count("b", "en")
    freq = store.list_frequent()                                       # item 6
    check(freq and freq[0]["term"] == "c", "frequent sorted by count desc")
    check(all(freq[i]["search_count"] >= freq[i + 1]["search_count"]
              for i in range(len(freq) - 1)), "frequent ordering monotonic")
    run = [r for r in freq if r["term"] == "run"][0]
    check(run["display_translation"] == "koşmak / çalıştırmak", "frequent row contains Turkish translation")


def test_history():
    print("\nHISTORY STORES")
    from language_dictionary import DictionaryStore, TranslationHistoryStore
    store = DictionaryStore(_tmp_db())
    hist = TranslationHistoryStore(store)
    hid = hist.add_search("slope", "English", "Turkish", "eğim", "qwen",
                          translation="eğim", category="mathematics")  # item 5
    hist.add_search("vector", "English", "Turkish", "vektör", "qwen")
    rows = hist.list_search()
    check(len(rows) == 2 and rows[0]["query"] == "vector", "search history save/load (newest first)")
    check(rows[1]["translation"] == "eğim", "history row contains Turkish translation")
    hist.update_search(hid, result="slope -> eğim", model_used="qwen",
                       translation="eğim", short_translation="eğim")
    updated = hist.list_search(limit=10)[1]
    check(updated["result"] != "(pending)" and updated["short_translation"] == "eğim",
          "history row can be updated after pending result")
    hist.add_sentence("Hello", "Merhaba", "English", "Turkish", "qwen")  # item 8
    check(len(hist.list_sentence()) == 1, "sentence history save/load")
    hist.add_image("/x.png", "x^2", "x kare", "moondream", "qwen")    # item 9
    check(len(hist.list_image()) == 1, "image translation history no-crash")


def test_pdf_terms():
    print("\nPDF TERMS NOTEBOOK")
    from language_dictionary import DictionaryStore
    store = DictionaryStore(_tmp_db())
    tid = store.add_pdf_term("eigenvalue", "özdeğer", source_pdf="LinAlg.pdf",
                             page_number=12, difficulty="hard")        # item 14
    check(len(store.list_pdf_terms()) == 1, "pdf term added")
    check("translation" in store.list_pdf_terms()[0].keys(), "pdf terms expose translation column")
    store.update_pdf_term(tid, translation="öz değer")
    check(store.list_pdf_terms()[0]["translation"] == "öz değer", "pdf term edited")
    store.mark_pdf_term_learned(tid, True)
    check(store.list_pdf_terms()[0]["learned"] == 1, "pdf term marked learned")
    # export/import CSV
    csv_path = _tmp_db() + ".csv"
    n = store.export_pdf_terms_csv(csv_path)                           # item 15
    check(n == 1 and Path(csv_path).exists(), "pdf terms export CSV")
    store2 = DictionaryStore(_tmp_db())
    m = store2.import_pdf_terms_csv(csv_path)
    check(m == 1 and store2.list_pdf_terms()[0]["term"] == "eigenvalue", "pdf terms import CSV")
    store.delete_pdf_term(tid)
    check(len(store.list_pdf_terms()) == 0, "pdf term deleted")


def test_profiles():
    print("\nMODEL PROFILES")
    from language_dictionary import (DictionaryStore, LanguageModelProfileManager,
                                     DEFAULT_PROFILES)
    store = DictionaryStore(_tmp_db())
    pm = LanguageModelProfileManager(store)                            # item 16
    check(pm.get("translation") == "qwen/qwen3-v1-8b", "default translation profile")
    check(pm.get("vision_translation") == "moondream-2b-2025-04-14", "default vision profile")
    check(pm.get("general_fallback") == "gemma-4-12b-qat", "default fallback profile")
    pm.set("translation", "custom-model")                             # item 17
    pm2 = LanguageModelProfileManager(store)
    check(pm2.get("translation") == "custom-model", "profile update persists (save/load)")
    # available model matching for the user's actual models               # item 18
    models = ["qwen/qwen3-v1-8b", "mistral-small-3.2-24b-instruct", "moondream-2b-2025-04-14",
              "qwen2.5-math-7b-instruct", "biomistral-7b", "finance-llm-13b", "meta-llama-3-8b-instruct"]
    pm3 = LanguageModelProfileManager(DictionaryStore(_tmp_db()))
    check(pm3.resolve("translation", models) == "qwen/qwen3-v1-8b", "match translation -> qwen3")
    check(pm3.resolve("high_quality_translation", models) == "mistral-small-3.2-24b-instruct", "match HQ -> mistral-small")
    check(pm3.resolve("vision_translation", models) == "moondream-2b-2025-04-14", "match vision -> moondream")
    check(pm3.resolve("math", models) == "qwen2.5-math-7b-instruct", "match math -> qwen-math")
    check(pm3.resolve("bio_dictionary", models) == "biomistral-7b", "match bio -> biomistral")
    check(pm3.resolve("general_fallback", models) == "meta-llama-3-8b-instruct", "match fallback -> llama3")

    # ---- Flexible resolution: models get uninstalled, routes must not break ----
    from language_dictionary import LanguageModelProfileManager as PM
    # After removing mistral-small and meta-llama-3 and adding Gemma. Note the id is
    # fuller than the pattern ("google/gemma-4-12b-qat"): matching is by substring, so
    # renaming or re-quantising a model must not break the profile.
    after = ["google/gemma-4-12b-qat", "qwen/qwen3-vl-8b",
             "biomistral-7b", "qwen2.5-math-7b-instruct", "moondream-2b-2025-04-14"]
    pm4 = PM(DictionaryStore(_tmp_db()))
    hq = pm4.resolve("high_quality_translation", after)
    check(hq == "google/gemma-4-12b-qat", "HQ translation falls back to Gemma, not a random model")
    # REGRESSION: a bare "mistral" keyword used to match biomistral-7b once
    # mistral-small was gone — a biomedical model doing academic translation.
    check("biomistral" not in hq, "HQ translation must never resolve to the biomedical model")
    check(pm4.resolve("math", after) == "qwen2.5-math-7b-instruct", "installed domain model keeps priority")
    check(pm4.resolve("general_fallback", after) == "google/gemma-4-12b-qat", "fallback resolves to installed Gemma")

    # JSON overrides: swap a model without touching code
    pm5 = PM(DictionaryStore(_tmp_db()), overrides={"math": ["gemma-4-12b"],
                                                    "translation": ["yok-boyle-model", "qwen3-vl"]})
    check(pm5.resolve("math", after) == "google/gemma-4-12b-qat", "override wins over the installed domain model")
    check(pm5.resolve("translation", after) == "qwen/qwen3-vl-8b", "override falls through to its 2nd choice")
    check(PM(DictionaryStore(_tmp_db()), overrides={}).get("math") == "qwen2.5-math-7b-instruct",
          "empty override leaves defaults alone")

    # LM Studio closed: keep the configured name rather than guessing
    check(pm4.resolve("math", []) == "qwen2.5-math-7b-instruct", "no models reported -> keep default name")


def test_translation_client_fallbacks():
    print("\nLM STUDIO TRANSLATION FALLBACKS")
    from language_dictionary import (LMStudioTranslationClient, LanguageModelProfileManager,
                                     NO_SERVER_MSG, NO_MODEL_MSG)
    # classify logic
    check(LMStudioTranslationClient.classify(False, []) == "no_server", "classify no server")  # item 10
    check(LMStudioTranslationClient.classify(True, []) == "no_model", "classify no model")     # item 11
    check(LMStudioTranslationClient.classify(True, ["m"]) == "connected", "classify connected")
    # real dead-port server -> no_server, safe (no crash)
    client = LMStudioTranslationClient("http://127.0.0.1:59999", LanguageModelProfileManager())
    out, model, status = client.translate("Hello", "English", "Turkish")
    check(status == "no_server" and out == NO_SERVER_MSG, "translate offline -> safe no_server message")
    # simulate server-up-no-model by monkeypatching server_status
    client.server_status = lambda: ("no_model", [])
    out2, model2, status2 = client.translate("Hi")
    check(status2 == "no_model" and out2 == NO_MODEL_MSG, "server running, no model -> safe message")
    out3, model3, status3 = client.lookup_word("slope")
    check(status3 == "no_model", "lookup_word safe when no model")


def test_dictionary_ai_questions():
    print("\nDICTIONARY — ASK AI ABOUT THIS TERM")
    from language_dictionary import (DictionaryStore, LMStudioTranslationClient,
                                     LanguageModelProfileManager, NO_SERVER_MSG)
    store = DictionaryStore(_tmp_db())
    # New table exists with the agreed columns.
    cols = {r["name"] for r in
            store.conn.execute("PRAGMA table_info(dictionary_ai_questions)").fetchall()}
    need = {"id", "term", "question", "answer", "model", "created_at",
            "source_language", "target_language", "source_context"}
    check(need <= cols, "dictionary_ai_questions table has all columns")
    # add + list
    rid = store.add_ai_question("graph", "graph ile chart farki nedir?",
                                "Grafik (graph) ...", model="qwen",
                                source_language="English", target_language="Turkish")
    check(bool(rid), "add_ai_question returns an id")
    rows = store.list_ai_questions("graph")
    check(len(rows) == 1 and rows[0]["question"].startswith("graph"),
          "list_ai_questions returns the row")
    check(rows[0]["source_context"] == "dictionary_ai_question",
          "default source_context tag stored")
    check(store.list_ai_questions("missing") == [], "list_ai_questions empty for unknown term")
    # Migration is re-runnable (no crash, data preserved).
    store._create_tables()
    check(len(store.list_ai_questions("graph")) == 1, "re-running create/migrate keeps data")
    # ask_about_term happy path (stub network, fake completion; no real LM needed).
    captured = {}
    def fake_complete(system, user, model):
        captured.update(system=system, user=user, model=model)
        return "Turkce aciklama (graph).", True
    client = LMStudioTranslationClient(profile_manager=LanguageModelProfileManager(store),
                                       complete_fn=fake_complete)
    client.server_status = lambda: ("connected", ["qwen/qwen3-v1-8b"])
    out, model, status = client.ask_about_term(
        "graph", "Bunu daha basit anlat", translation="grafik",
        definition="Verilerin gorsel temsili", category="general",
        source_context="lm-studio")
    check(status == "ok", "ask_about_term ok when server connected")
    check("graph" in captured.get("user", ""), "term embedded as context in the prompt")
    check("Bunu daha basit anlat" in captured.get("user", ""),
          "user question embedded in the prompt")
    check(bool(model), "ask_about_term resolves a concrete model id (not hard-coded)")
    # LM Studio closed -> safe no_server (dead port), no crash.
    offline = LMStudioTranslationClient("http://127.0.0.1:59999", LanguageModelProfileManager(store))
    o2, m2, s2 = offline.ask_about_term("graph", "x")
    check(s2 == "no_server" and o2 == NO_SERVER_MSG,
          "ask_about_term offline -> safe no_server message")
    # Server up, no model -> safe.
    offline.server_status = lambda: ("no_model", [])
    o3, m3, s3 = offline.ask_about_term("graph", "x")
    check(s3 == "no_model", "ask_about_term safe when no model loaded")


def test_image_pipeline_fallbacks():
    print("\nIMAGE PIPELINE FALLBACKS")
    from language_dictionary import ImageTranslationPipeline
    img = Path(tempfile.gettempdir()) / "langdict_blank.png"
    try:
        from PIL import Image
        Image.new("RGB", (40, 20), "white").save(str(img))
        have_img = True
    except Exception:
        have_img = False
    # No vision + no OCR -> manual (item 12 / 13)
    pipe = ImageTranslationPipeline(vision_fn=None, ocr_fn=None)
    if have_img:
        text, status = pipe.extract_text(str(img))
        check(status == "manual", "no vision + no OCR -> manual fallback (no crash)")
    # vision reports no model -> falls through to manual
    pipe2 = ImageTranslationPipeline(vision_fn=lambda s, u, p: ("", "no_vision_model"), ocr_fn=None)
    if have_img:
        text2, status2 = pipe2.extract_text(str(img))
        check(status2 == "manual", "vision unavailable -> manual fallback")
    # missing image -> no crash
    t3, s3 = pipe.extract_text("does_not_exist_999.png")
    check(s3 == "no_image", "missing image path handled safely")


def test_command_registry_language():
    print("\nLANGUAGE COMMAND REGISTRATION")
    import command_registry as cr
    reg = cr.CommandRegistry()

    class FakeApp:
        def __init__(self):
            self.calls = []

        def open_dictionary_subtab(self, idx):
            self.calls.append(idx)
    app = FakeApp()
    cr.register_language_commands(reg, app)
    for cid in cr.LANGUAGE_DICTIONARY_COMMANDS:
        check(reg.has(cid), f"{cid} registered")
    reg.invoke("command.translate_image")
    check(app.calls == [2], "translate_image opens image sub-tab (index 2)")


SAMPLE_TEXT = (
    "The Cartesian coordinate system is the two-dimensional plane in which we graph "
    "points and equations. The plane is defined by the coordinate axes. The horizontal "
    "axis is the x-axis and the vertical axis is the y-axis. The axes meet at the origin."
)


def test_vocab_scanner_imports():
    print("\nPDF VOCABULARY SCANNER — imports")
    import language_dictionary as ld
    for cls in ("PDFVocabularyScanner", "VocabularyDifficultyClassifier", "ExtractedVocabularyStore"):
        check(hasattr(ld, cls), f"{cls} import")                       # items 1-3


def test_vocab_classifier():
    print("\nVOCAB CLASSIFIER")
    from language_dictionary import VocabularyDifficultyClassifier
    c = VocabularyDifficultyClassifier()
    m = c.classify("slope", frequency=5)                              # item 4
    check("technical_math" in m["tags"] and m["category"] == "math", "math term -> technical_math")
    check(m["translation"] == "eğim", "math term gets embedded Turkish translation")
    s = c.classify("velocity")                                        # item 5
    check("technical_science" in s["tags"] and s["category"] == "science", "science term -> technical_science")
    a = c.classify("represent")                                       # item 6
    check("academic" in a["tags"], "academic term -> academic tag")
    basic = c.classify("the")
    check(basic["cefr_level"] == "basic" or basic["difficulty_score"] <= 2, "common word -> low level")
    adv = c.classify("perpendicular", frequency=4)
    check(adv["cefr_level"] in ("C1", "C2/technical"), "long technical term -> C1/C2")


def test_vocab_tokenize_filter():
    print("\nVOCAB TOKENIZE / STOPWORD / CONTEXT")
    from language_dictionary import PDFVocabularyScanner, DictionaryStore
    scn = PDFVocabularyScanner(DictionaryStore(_tmp_db()))
    check(not scn.is_candidate("the"), "stopword 'the' filtered")     # item 7
    check(not scn.is_candidate("x"), "single variable 'x' filtered")
    check(not scn.is_candidate("12"), "pure number filtered")
    check(scn.is_candidate("slope"), "technical term 'slope' kept")
    cands = list(scn.extract_candidates(SAMPLE_TEXT))                 # item 8
    terms = {t for t, _ in cands}
    for expected in ("cartesian", "coordinate", "axes", "origin", "plane",
                     "equations", "horizontal", "vertical", "two-dimensional"):
        check(expected in terms, f"token extraction finds '{expected}'")
    ctx = [ctx for t, ctx in cands if t == "origin"]                  # item 9
    check(ctx and "origin" in ctx[0].lower(), "context sentence captured for 'origin'")


def test_vocab_store_and_filters():
    print("\nEXTRACTED VOCABULARY STORE + FILTERS")
    from language_dictionary import DictionaryStore, ExtractedVocabularyStore
    store = DictionaryStore(_tmp_db())
    cols = {r["name"] for r in store.conn.execute(
        "PRAGMA table_info(extracted_vocabulary_terms)").fetchall()}
    for c in ("term", "translation", "cefr_level", "tags", "source_pdf", "frequency"):
        check(c in cols, f"extracted_vocabulary_terms.{c} migrated")  # item 10
    cache_cols = {r["name"] for r in store.conn.execute(
        "PRAGMA table_info(pdf_vocabulary_scan_cache)").fetchall()}
    check("pdf_hash" in cache_cols, "scan cache table migrated")      # item 11
    vs = ExtractedVocabularyStore(store)
    vs.add_or_update("slope", translation="eğim", cefr_level="C1", difficulty_score=4,
                     tags="technical_math,C1_candidate", category="math",
                     source_pdf="Algebra.pdf", page_number=3, frequency=5, context_sentence="the slope is")
    vs.add_or_update("the", translation="", cefr_level="basic", difficulty_score=0,
                     tags="", category="general", source_pdf="Algebra.pdf", frequency=99)
    vs.add_or_update("velocity", translation="hız", cefr_level="B2", difficulty_score=3,
                     tags="technical_science", category="science", source_pdf="Phys.pdf", frequency=2)
    check(vs.count() == 3, "3 extracted terms stored")
    # dedup: same term+pdf updates, not duplicates
    vs.add_or_update("slope", translation="eğim", source_pdf="Algebra.pdf", frequency=7)
    check(vs.count() == 3, "same term+pdf does not duplicate")
    c1 = vs.list_terms(level="C1")                                    # item 16
    check(len(c1) == 1 and c1[0]["term"] == "slope", "filter C1 level")
    tm = vs.list_terms(category="math")                              # item 17
    check(len(tm) == 1 and tm[0]["term"] == "slope", "filter technical_math category")
    fq = vs.list_terms(min_frequency=5)
    check(all(r["frequency"] >= 5 for r in fq), "frequency filter works")
    pdf_only = vs.list_terms(source_pdf="Phys.pdf")
    check(len(pdf_only) == 1 and pdf_only[0]["term"] == "velocity", "filter by source PDF")


def test_vocab_integration_actions():
    print("\nVOCAB -> DICTIONARY / PDF TERMS / FAVORITE / LEARNED")
    from language_dictionary import DictionaryStore, ExtractedVocabularyStore
    store = DictionaryStore(_tmp_db())
    vs = ExtractedVocabularyStore(store)
    vid = vs.add_or_update("integral", translation="integral", category="math",
                           source_pdf="Calc.pdf", page_number=8, context_sentence="the integral of")
    # add to dictionary (item 12)
    store.add_term(term="integral", translation="integral", lang="en", category="math",
                   source="Calc.pdf")
    vs.set_flag(vid, "added_to_dictionary", 1)
    check(store.get_term("integral", "en") is not None, "extracted term added to dictionary")
    check(vs.get(vid)["added_to_dictionary"] == 1, "added_to_dictionary flag set")
    # add to PDF terms (item 13)
    store.add_pdf_term(term="integral", translation="integral", source_pdf="Calc.pdf", page_number=8)
    check(len(store.list_pdf_terms()) == 1, "extracted term added to PDF Terms")
    # favorite (item 15)
    store.add_term(term="integral", lang="en")
    store.set_favorite("integral", True, "en")
    vs.set_flag(vid, "favorite", 1)
    check(len(store.list_favorites()) == 1 and vs.get(vid)["favorite"] == 1, "favorite extracted term")
    # learned (item 14)
    vs.set_flag(vid, "learned", 1)
    check(vs.get(vid)["learned"] == 1, "mark learned")
    # export CSV (item 18)
    csv_path = _tmp_db() + ".csv"
    n = vs.export_csv(csv_path)
    check(n >= 1 and Path(csv_path).exists(), "extracted vocabulary export CSV")


def test_vocab_scan_safety():
    print("\nVOCAB SCAN SAFETY (LM/fitz/empty)")
    from language_dictionary import DictionaryStore, PDFVocabularyScanner
    import tempfile as _tf
    empty_dir = Path(_tf.mkdtemp(prefix="vocab_empty_"))
    store = DictionaryStore(_tmp_db())
    # translate_fn that raises must not crash scan (item 19)
    scn = PDFVocabularyScanner(store, resources_dir=empty_dir,
                               translate_fn=lambda t, c: (_ for _ in ()).throw(RuntimeError("LM down")))
    results = {}

    def done(ok, info):
        results["ok"] = ok
        results["info"] = info
    scn.scan(progress_cb=None, done_cb=done, background=False)
    check("ok" in results, "scan on empty Resources completes (no crash)")
    # _resolve_translation must swallow LM errors
    check(scn._resolve_translation("zzxqterm", "ctx") == "", "LM failure -> empty translation (no crash)")


def test_vocab_old_db_migration():
    print("\nVOCAB OLD DB MIGRATION (no crash)")
    import sqlite3 as _sq
    from language_dictionary import DictionaryStore
    path = _tmp_db()
    conn = _sq.connect(path)
    conn.execute("CREATE TABLE terms (id INTEGER PRIMARY KEY, term TEXT)")  # legacy minimal db
    conn.commit()
    conn.close()
    store = DictionaryStore(path)                                     # item 20
    cols = {r["name"] for r in store.conn.execute(
        "PRAGMA table_info(extracted_vocabulary_terms)").fetchall()}
    check("cefr_level" in cols, "old db gains extracted_vocabulary_terms safely")
    check(store.count_terms() >= 0, "old db opens without crash")


def test_history_management_store():
    print("\nHISTORY MANAGEMENT — store")
    from language_dictionary import DictionaryStore, TranslationHistoryStore
    store = DictionaryStore(_tmp_db())
    hist = TranslationHistoryStore(store)
    # add manual (item 1)
    hid = hist.add_search_history_item(
        "run", "run means koşmak or çalıştırmak depending on context.",
        translation="koşmak / çalıştırmak", model_used="manual")
    check(hid and len(hist.list_search()) == 1, "add manual history item")
    row = hist.get_search_history_item(hid)                            # item 7
    check(row is not None and row["query"] == "run" and row["model_used"] == "manual",
          "get history item")
    check(row["translation"] == "koşmak / çalıştırmak", "manual item keeps Turkish translation")
    # update (item 2)
    ok = hist.update_search_history_item(hid, query="run", result="updated result",
                                         translation="koşmak", model_used="edited")
    check(ok, "update returns True")
    row2 = hist.get_search_history_item(hid)
    check(row2["translation"] == "koşmak" and row2["result"] == "updated result", "update changes fields")
    # delete single (item 3)
    check(hist.delete_search_history_item(hid) is True, "delete single history item")
    check(len(hist.list_search()) == 0, "history empty after delete")
    # delete missing (item 6)
    check(hist.delete_search_history_item(999999) is False, "delete missing item -> False (no crash)")
    # delete multiple (item 4)
    a = hist.add_search_history_item("a", "ra")
    b = hist.add_search_history_item("b", "rb")
    c = hist.add_search_history_item("c", "rc")
    n = hist.delete_search_history_items([a, b])
    check(n == 2 and len(hist.list_search()) == 1, "delete multiple history items")
    check(hist.delete_search_history_items([]) == 0, "delete empty list -> 0 (no crash)")
    # clear (item 5) — and does not touch terms/favorites (items 10/11)
    store.add_term("derivative", "türev", lang="en")
    store.set_favorite("derivative", True, "en")
    hist.add_search_history_item("x", "rx")
    cleared = hist.clear_search_history()
    check(cleared >= 1 and len(hist.list_search()) == 0, "clear search history")
    check(store.get_term("derivative", "en") is not None, "clear history keeps terms")  # item 10
    check(len(store.list_favorites()) == 1, "clear history keeps favorites")            # item 11


def test_history_management_ui():
    print("\nHISTORY MANAGEMENT — UI helpers (headless)")
    import tkinter as tk
    import language_dictionary as ld
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print(f"   [SKIP] Tk unavailable: {exc}")
        return
    # auto-confirm dialogs so no window blocks the test
    ld.messagebox.askyesno = lambda *a, **k: True
    ld.messagebox.showinfo = lambda *a, **k: None
    ld.messagebox.showwarning = lambda *a, **k: None
    ld.DB_PATH = Path(tempfile.gettempdir()) / "histmgmt_ui.sqlite"
    try:
        os.unlink(str(ld.DB_PATH))
    except Exception:
        pass

    class _App:
        language = "en"
        client = None
    try:
        panel = ld.LanguageDictionaryPanel(root, _App(), seed_terms=[])
        root.update_idletasks()
        hid = panel.history.add_search_history_item("run", "run -> koşmak", translation="koşmak")
        panel._refresh_history()
        check(len(panel.hist_tree.get_children()) == 1, "history tree shows the row")
        panel.hist_tree.selection_set(str(hid))
        check(panel._history_selected_ids() == [hid], "selected ids helper works")
        # add to dictionary (item 8)
        panel._history_to_dictionary()
        check(panel.store.get_term("run", "en") is not None, "history -> add to dictionary")
        # add to favorites (item 9)
        panel._history_to_favorites()
        check(len(panel.store.list_favorites()) == 1, "history -> add to favorites")
        # delete selected (item 12 — no crash, auto-confirmed)
        panel.hist_tree.selection_set(str(hid))
        panel._history_delete_selected()
        root.update_idletasks()
        check(len(panel.hist_tree.get_children()) == 0, "delete selected via UI (no crash)")
        # clear history (no crash)
        panel.history.add_search_history_item("z", "rz")
        panel._refresh_history()
        panel._history_clear()
        check(len(panel.hist_tree.get_children()) == 0, "clear history via UI (no crash)")
        check(True, "history UI action helpers run without crash")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        check(False, f"history UI raised: {exc}")
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def test_frequent_favorites_store():
    print("\nFREQUENT / FAVORITES MANAGEMENT — store")
    from language_dictionary import DictionaryStore, TranslationHistoryStore
    store = DictionaryStore(_tmp_db())
    cols = {r["name"] for r in store.conn.execute("PRAGMA table_info(terms)").fetchall()}
    check("hidden_from_frequent" in cols, "terms.hidden_from_frequent migrated")        # item 1
    store.add_term("slope", "eğim", lang="en", category="mathematics")
    for _ in range(5):
        store.increment_search_count("slope", "en")
    store.add_term("run", "koşmak", lang="en", category="general")
    for _ in range(3):
        store.increment_search_count("run", "en")
    store.set_favorite("slope", True, "en")
    store.set_favorite("run", True, "en")
    check("slope" in [r["term"] for r in store.list_frequent()], "frequent shows counted term")
    # reset count (item 2)
    check(store.reset_search_count("slope") is True, "reset_search_count returns True")
    check(store.get_term("slope", "en")["search_count"] == 0, "count reset to 0")
    check(store.get_term("slope", "en") is not None, "reset_search_count keeps term")
    for _ in range(4):
        store.increment_search_count("slope", "en")
    # hide / unhide (item 3 + 16)
    store.hide_from_frequent("slope")
    check("slope" not in [r["term"] for r in store.list_frequent()], "hidden term excluded from frequent")
    check(store.get_term("slope", "en") is not None, "hide keeps term in dictionary")
    store.unhide_from_frequent("slope")
    check("slope" in [r["term"] for r in store.list_frequent()], "unhide restores frequent")
    # clear all frequent counts (item 4 + 14)
    n = store.clear_all_frequent_counts()
    counts = [r["search_count"] for r in store.conn.execute("SELECT search_count FROM terms").fetchall()]
    check(n >= 1 and all(c == 0 for c in counts), "clear_all_frequent_counts zeroes all")
    check(store.get_term("run", "en") is not None, "clear counts keeps terms")
    # set_favorite False (item 5)
    store.set_favorite("run", False, "en")
    check("run" not in [r["term"] for r in store.list_favorites()], "set_favorite False removes from favorites")
    check(store.get_term("run", "en") is not None, "set_favorite False keeps term")
    # clear all favorites (item 6 + 15)
    store.clear_all_favorites()
    check(len(store.list_favorites()) == 0, "clear_all_favorites empties favorites")
    check(store.get_term("slope", "en") is not None, "clear favorites keeps terms")
    # edit translation (item 7/8/17)
    check(store.update_term("slope", translation="meyil", category="geometry") is True, "update_term returns True")
    check(store.get_term("slope", "en")["translation"] == "meyil", "update_term changes translation")
    store.set_favorite("slope", True, "en")
    fav = [r for r in store.list_favorites() if r["term"] == "slope"][0]
    check(fav["display_translation"] == "meyil", "favorites list shows updated Turkish translation")
    # add to pdf terms (item 9/10)
    store.add_term_to_pdf_terms("slope", "meyil", source_pdf="Geo.pdf", page_number=3, note="math")
    check(any(r["term"] == "slope" for r in store.list_pdf_terms()), "add_term_to_pdf_terms works")
    # add to history (item 11)
    store.add_term_to_history("slope", "meyil", result="slope means eğim", model_used="favorite")
    th = TranslationHistoryStore(store)
    check(any(r["query"] == "slope" for r in th.list_search()), "add_term_to_history works")
    # delete term (item 12 + 13)
    check(store.delete_term("slope") is True, "delete_term removes term")
    check(store.get_term("slope", "en") is None, "term gone after delete")
    check(store.delete_term("nonexistent_zzz") is False, "delete missing term -> False (no crash)")
    check(store.get_term_by_text("run", "en") is not None, "get_term_by_text returns dict")


def test_frequent_favorites_ui():
    print("\nFREQUENT / FAVORITES MANAGEMENT — UI helpers (headless)")
    import tkinter as tk
    import language_dictionary as ld
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print(f"   [SKIP] Tk unavailable: {exc}")
        return
    ld.messagebox.askyesno = lambda *a, **k: True
    ld.messagebox.showinfo = lambda *a, **k: None
    ld.DB_PATH = Path(tempfile.gettempdir()) / "freqfav_ui.sqlite"
    try:
        os.unlink(str(ld.DB_PATH))
    except Exception:
        pass

    class _App:
        language = "en"
        client = None
    try:
        panel = ld.LanguageDictionaryPanel(root, _App(), seed_terms=[])
        st = panel.store
        st.add_term("slope", "eğim", lang="en", category="math")
        for _ in range(5):
            st.increment_search_count("slope", "en")
        st.set_favorite("slope", True, "en")
        panel._refresh_frequent()
        panel._refresh_favorites()
        check(len(panel.freq_tree.get_children()) >= 1, "frequent tree populated")
        check(len(panel.fav_tree.get_children()) >= 1, "favorites tree populated")
        # Frequent: remove (hide) keeps term
        panel.freq_tree.selection_set("slope")
        panel._freq_remove()
        root.update_idletasks()
        check("slope" not in panel.freq_tree.get_children(), "freq remove hides from frequent")
        check(st.get_term("slope", "en") is not None, "freq remove keeps term")
        # Frequent: add to favorites + PDF terms
        st.unhide_from_frequent("slope")
        panel._refresh_frequent()
        panel.freq_tree.selection_set("slope")
        panel._freq_to_pdf()
        check(any(r["term"] == "slope" for r in st.list_pdf_terms()), "freq add to PDF terms")
        # Favorites: add to history, remove, delete (auto-confirmed)
        panel.fav_tree.selection_set("slope")
        panel._fav_to_history()
        check(any(r["query"] == "slope" for r in panel.history.list_search()), "fav add to history")
        panel.fav_tree.selection_set("slope")
        panel._fav_remove()
        root.update_idletasks()
        check("slope" not in panel.fav_tree.get_children(), "fav remove works")
        check(st.get_term("slope", "en") is not None, "fav remove keeps term")
        st.set_favorite("slope", True, "en")
        panel._refresh_favorites()
        panel.fav_tree.selection_set("slope")
        panel._fav_delete_term()
        root.update_idletasks()
        check(st.get_term("slope", "en") is None, "fav delete term removes term (confirmed)")
        check(True, "frequent/favorites UI helpers run without crash")
    except Exception as exc:
        import traceback
        traceback.print_exc()
        check(False, f"freq/fav UI raised: {exc}")
    finally:
        try:
            root.destroy()
        except Exception:
            pass


def main():
    print("=" * 64)
    print("Language & Science Dictionary — Test Suite")
    print("=" * 64)
    for fn in (test_import, test_store_terms, test_translation_column_migration,
               test_extract_short_translation, test_favorites, test_frequent, test_history,
               test_pdf_terms, test_profiles, test_translation_client_fallbacks,
               test_dictionary_ai_questions,
               test_image_pipeline_fallbacks, test_command_registry_language,
               test_vocab_scanner_imports, test_vocab_classifier, test_vocab_tokenize_filter,
               test_vocab_store_and_filters, test_vocab_integration_actions,
               test_vocab_scan_safety, test_vocab_old_db_migration,
               test_history_management_store, test_history_management_ui,
               test_frequent_favorites_store, test_frequent_favorites_ui):
        try:
            fn()
        except Exception as exc:
            global FAILED
            FAILED += 1
            import traceback
            traceback.print_exc()
            print(f"   [ERROR] {fn.__name__}: {exc}")
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 64)
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
