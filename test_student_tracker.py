# -*- coding: utf-8 -*-
"""
Tests for the Student Tracker (logic layer + head-less UI).

Run with:
    python test_student_tracker.py
"""

import sys
import os
import csv
import tempfile

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
    fd, path = tempfile.mkstemp(suffix=".sqlite", prefix="sttrack_")
    os.close(fd)
    os.unlink(path)
    return path


def test_import():
    print("\nIMPORT")
    import student_tracker as st
    for cls in ("StudentStore", "QuestionBank", "ExamEngine", "ProgressAnalytics",
                "StudentTrackerPanel"):
        check(hasattr(st, cls), f"{cls} import")
    check(st.STATUSES == ("unsolved", "solved", "wrong", "review"), "STATUSES defined")


def test_answer_matching():
    print("\nANSWER NORMALISATION")
    from student_tracker import normalize_answer, check_answer
    check(normalize_answer(" 2 X + 1 ") == "2x+1", "normalize strips space + lowercases")
    check(normalize_answer("3×4") == "3*4", "× -> *")
    check(check_answer("2x + 1", "2X+1") is True, "equivalent answers match")
    check(check_answer("5", "6") is False, "different answers do not match")
    check(check_answer("", "5") is False, "empty answer never matches")


def test_students():
    print("\nSTUDENTS")
    from student_tracker import StudentStore
    s = StudentStore(_tmp_db())
    a = s.add_student("Aziz")
    b = s.add_student("Ayse")
    check(bool(a) and bool(b) and a != b, "two students added")
    check(s.add_student("Aziz") == a, "duplicate name returns the same id")
    check(len(s.list_students()) == 2, "list_students -> 2")
    check(s.active_student()["id"] == a, "first student auto-activated")
    s.set_active_student(b)
    check(s.active_student()["id"] == b, "set_active_student switches")
    check(s.ensure_default_student() == b, "ensure_default keeps the active one")
    s.delete_student(b)
    check(len(s.list_students()) == 1, "delete_student removes it")
    check(s.ensure_default_student() == a, "ensure_default falls back to remaining student")
    s2 = StudentStore(_tmp_db())
    check(bool(s2.ensure_default_student()), "empty store creates a default student")


def test_questions():
    print("\nQUESTION BANK")
    from student_tracker import StudentStore
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    q1 = s.add_question("2+2=?", "4", course="Algebra", topic="Toplama", difficulty="Easy")
    q2 = s.add_question("x^2-5x+6=0", "x=2,3", course="Algebra", topic="Denklem", difficulty="Hard")
    s.add_question("Türev nedir?", "değişim hızı", course="Calculus", topic="Türev")
    check(bool(q1) and bool(q2), "questions added")
    check(s.add_question("   ") is None, "blank question rejected")
    check(s.count_questions() == 3, "count_questions -> 3")
    check(sorted(s.distinct_values("course")) == ["Algebra", "Calculus"], "distinct courses")
    check(s.distinct_values("bogus") == [], "unknown column -> []")
    check(len(s.list_questions(course="Algebra")) == 2, "filter by course")
    check(len(s.list_questions(difficulty="Hard")) == 1, "filter by difficulty")
    check(len(s.list_questions(query="türev")) == 1, "text query filter")
    check(s.update_question(q1, topic="Aritmetik") is True, "update_question")
    check(s.get_question(q1)["topic"] == "Aritmetik", "update persisted")
    check(s.delete_question(q1) is True and s.count_questions() == 2, "delete_question")
    check(s.delete_question(99999) is False, "deleting a missing question -> False")


def test_attempts_and_status():
    print("\nATTEMPTS / SOLVED-UNSOLVED TRACKING")
    from student_tracker import StudentStore
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    q = s.add_question("2+2=?", "4", course="Algebra", topic="Toplama")
    check(s.question_status(q, sid) == "unsolved", "new question starts 'unsolved'")
    s.record_attempt(q, sid, "wrong", user_answer="5")
    check(s.question_status(q, sid) == "wrong", "recorded 'wrong'")
    s.record_attempt(q, sid, "solved", user_answer="4")
    check(s.question_status(q, sid) == "solved", "latest attempt wins -> 'solved'")
    check(s.status_map(sid).get(q) == "solved", "status_map reflects latest")
    s.record_attempt(q, sid, "bogus")
    check(s.question_status(q, sid) == "unsolved", "invalid status falls back to 'unsolved'")
    check(len(s.list_attempts(sid)) == 3, "attempt history kept")
    # per-student isolation
    other = s.add_student("Diger")
    check(s.question_status(q, other) == "unsolved", "another student's status is independent")
    # status filter in list_questions
    s.record_attempt(q, sid, "solved")
    check(len(s.list_questions(student_id=sid, status="solved")) == 1, "filter questions by status")
    check(len(s.list_questions(student_id=sid, status="wrong")) == 0, "no 'wrong' left")


def test_bulk_import():
    print("\nBULK IMPORT")
    from student_tracker import StudentStore, QuestionBank
    s = StudentStore(_tmp_db())
    bank = QuestionBank(s)
    n = bank.import_text_block("2+2 = 4\n3*3 | 9\n\nSadece soru\n", course="Algebra", topic="Temel")
    check(n == 3, "import_text_block -> 3 questions")
    rows = s.list_questions()
    texts = {r["question_text"]: r["answer_text"] for r in rows}
    check(texts.get("2+2") == "4", "'=' separator parsed")
    check(texts.get("3*3") == "9", "'|' separator parsed")
    check(texts.get("Sadece soru") == "", "separator-less line -> empty answer")
    check(all(r["course"] == "Algebra" for r in rows), "course applied to all")
    check(bank.import_text_block("") == 0, "empty text -> 0")
    # CSV round-trip
    p = os.path.join(tempfile.gettempdir(), "sttrack_q.csv")
    s.export_questions_csv(p)
    s2 = StudentStore(_tmp_db())
    n2 = QuestionBank(s2).import_csv(p)
    check(n2 == 3, "import_csv round-trip -> 3")
    check(s2.count_questions() == 3, "CSV questions landed in the new store")


def test_exam_engine():
    print("\nEXAM ENGINE")
    from student_tracker import StudentStore, ExamEngine
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    ids = [s.add_question(f"q{i}", f"a{i}", course="Algebra", topic="T", difficulty="Easy")
           for i in range(5)]
    eng = ExamEngine(s)
    exam_id, items = eng.build(sid, course="Algebra", count=3)
    check(bool(exam_id) and len(items) == 3, "build -> exam with 3 items")
    check(s.get_exam(exam_id)["question_count"] == 3, "exam question_count stored")
    # answer 2 correct, 1 wrong
    eng.answer(exam_id, items[0]["question_id"], sid, "a?", True)
    eng.answer(exam_id, items[1]["question_id"], sid, "a?", True)
    eng.answer(exam_id, items[2]["question_id"], sid, "zzz", False)
    res = eng.finish(exam_id, duration_sec=42)
    check(res["question_count"] == 3 and res["correct_count"] == 2, "graded 2/3")
    check(res["score"] == 66.7, f"score = 66.7 (got {res['score']})")
    check(s.get_exam(exam_id)["status"] == "finished", "exam marked finished")
    check(s.get_exam(exam_id)["duration_sec"] == 42, "duration stored")
    # exam answers sync back into the bank's solved/wrong tracking
    check(s.question_status(items[0]["question_id"], sid) == "solved", "correct answer -> 'solved' in bank")
    check(s.question_status(items[2]["question_id"], sid) == "wrong", "wrong answer -> 'wrong' in bank")
    # targeted drill: only the wrong ones
    exam2, items2 = eng.build(sid, only_status="wrong", count=10)
    check(len(items2) == 1, "only_status='wrong' pool -> the 1 missed question")
    # empty pool is safe
    e3, i3 = eng.build(sid, course="YokBoyleKurs", count=5)
    check(e3 is None and i3 == [], "empty pool -> (None, []) not a crash")


def test_analytics():
    print("\nPROGRESS ANALYTICS")
    from student_tracker import StudentStore, ProgressAnalytics, ExamEngine
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    a1 = s.add_question("a1", "1", course="Algebra", topic="Denklem")
    a2 = s.add_question("a2", "2", course="Algebra", topic="Denklem")
    c1 = s.add_question("c1", "3", course="Calculus", topic="Türev")
    s.add_question("c2", "4", course="Calculus", topic="Türev")   # never attempted
    s.record_attempt(a1, sid, "solved")
    s.record_attempt(a2, sid, "wrong")
    s.record_attempt(c1, sid, "solved")
    an = ProgressAnalytics(s)
    o = an.overview(sid)
    check(o["total_questions"] == 4, "overview total")
    check(o["solved"] == 2 and o["wrong"] == 1, "overview solved/wrong")
    check(o["unsolved"] == 1, "overview never-attempted")
    check(o["accuracy"] == 66.7, f"overview accuracy 66.7 (got {o['accuracy']})")
    bt = an.by_topic(sid)
    alg = [r for r in bt if r["topic"] == "Denklem"][0]
    check(alg["total"] == 2 and alg["solved"] == 1 and alg["wrong"] == 1, "by_topic counts")
    check(alg["accuracy"] == 50.0, "by_topic accuracy")
    weak = an.weak_topics(sid, limit=1)
    check(weak and weak[0]["topic"] == "Denklem", "weak_topics finds the 50% topic first")
    # exam average
    eng = ExamEngine(s)
    eid, items = eng.build(sid, count=2)
    for it in items:
        eng.answer(eid, it["question_id"], sid, "x", True)
    eng.finish(eid)
    check(an.overview(sid)["exams"] == 1, "overview counts finished exams")
    check(an.overview(sid)["avg_score"] == 100.0, "overview avg_score")


def test_migration_safety():
    print("\nMIGRATION SAFETY")
    from student_tracker import StudentStore
    p = _tmp_db()
    s = StudentStore(p)
    sid = s.ensure_default_student()
    q = s.add_question("keep me", "1", course="A", topic="B")
    s.record_attempt(q, sid, "solved")
    s._create_tables()          # re-run create + migrate
    s._migrate()                # and again
    check(s.count_questions() == 1, "re-running create/migrate keeps questions")
    check(s.question_status(q, sid) == "solved", "re-running keeps attempts")
    s2 = StudentStore(p)        # reopen the same file
    check(s2.count_questions() == 1, "reopen keeps data")


def test_panel_headless():
    print("\nSTUDENT TRACKER PANEL (headless Tk)")
    try:
        import tkinter as tk
    except Exception:
        print("   [SKIP] Tk unavailable")
        return
    import types
    from student_tracker import StudentTrackerPanel, StudentStore
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print(f"   [SKIP] no display: {exc}")
        return
    try:
        app = types.SimpleNamespace(selected_path=None, selected_course="Algebra",
                                    pdf_viewer=None, set_status=lambda *a, **k: None,
                                    language="tr")
        panel = StudentTrackerPanel(root, app, db_path=_tmp_db())
        check(panel.student_id is not None, "panel creates/loads a default student")
        check(hasattr(panel, "q_tree") and hasattr(panel, "e_question"), "bank + exam widgets built")
        check(panel.nb.index("end") == 6, "6 sub-tabs (Bugün/Öğrenci/Soru/Paketler/Sınav/İstatistik)")
        check(hasattr(panel, "dash_tab") and hasattr(panel, "_dash_cards"), "dashboard tab built")
        check(set(panel._dash_cards.keys()) == {"due", "wrong", "unsolved", "accuracy"},
              "dashboard has the four cards")
        check(hasattr(panel, "dash_advice_body") and hasattr(panel, "advisor"),
              "📌 Bu Hafta karti + motor panele bagli")
        # V44 widgets: choice editor, scratch pad, exam choice frame
        check(len(panel.q_choice_vars) == 5 and hasattr(panel, "q_correct"),
              "bank form has A-E choice editor")
        check(hasattr(panel, "scratch") and hasattr(panel, "e_choice_frame"),
              "exam has scratch pad + choice frame")
        qid_mc = panel.store.add_question("MC test", "17", choices=["13", "15", "17"],
                                          correct_choice="C")
        item = panel.store.exam_items(
            panel.exams.build(panel.student_id, question_ids=[qid_mc], count=1)[0])[0]
        panel._build_exam_choices(item)
        check(set(panel._exam_choice_buttons.keys()) == {"A", "B", "C"},
              "exam choice buttons built from row")
        panel._pick_choice("C")
        check(panel.e_answer.get() == "C", "clicking a choice fills the answer")
        check(panel._exam_correct_choice == "C", "correct choice tracked for auto-grade")
        panel._clear_scratch()
        # add a question through the form
        panel.q_course.set("Algebra"); panel.q_topic.set("Denklem")
        panel.q_text.insert("1.0", "2+2=?"); panel.a_text.insert("1.0", "4")
        panel._add_q()
        check(panel.store.count_questions() == 2, "form Ekle -> question stored")  # +1 MC test above
        check(len(panel._q_rows) == 2, "tree refreshed with the new question")
        # mark it solved
        panel._mark("solved")
        check(panel.store.question_status(panel._sel_qid, panel.student_id) == "solved",
              "Çözdüm button records a solved attempt")
        # run a 1-question exam end to end
        panel.e_count.set(1)
        panel._start_exam()
        check(panel._exam_id is not None and len(panel._exam_items) == 1, "exam started with 1 item")
        panel.e_answer.set("4")
        panel._reveal()
        check("Doğru cevap" in panel.e_reveal.get("1.0", "end"), "reveal shows the stored answer")
        panel._mark_exam(True)
        check(panel._exam_id is None, "marking the last question finishes the exam")
        check(panel.stats.overview(panel.student_id)["exams"] == 1, "finished exam recorded")
        check(panel._exam_timer_job is None, "suresiz sinavda geri sayim isi yok")

        # SURELI sinav: geri sayim kurulur; sure dolunca otomatik biter
        from datetime import datetime as _dt, timedelta as _td
        panel.e_count.set(1)
        panel.e_duration.set(5)
        panel._start_exam()
        check(panel._exam_id is not None and panel._exam_deadline is not None,
              "sureli sinav baslatildi (deadline kuruldu)")
        check(panel._exam_timer_job is not None, "geri sayim after isi kuruldu")
        timed_exam_id = panel._exam_id
        # zaman asimini simule et: deadline gecmise cekilip tick dogrudan cagrilir
        panel._exam_deadline = _dt.now() - _td(seconds=1)
        panel._tick_exam_countdown()
        check(panel._exam_id is None, "sure dolunca sinav otomatik bitti")
        check(panel._exam_timer_job is None, "bitiste geri sayim isi iptal edildi")
        row = panel.store.get_exam(timed_exam_id)
        check(row is not None and row["status"] == "finished", "sure asimi sinavi 'finished' yazdi")
        check("Süre doldu" in panel.exam_status.cget("text"), "durum mesaji sure asimini soyluyor")

        # Atla (skip) cevaplanmis sayilmamali: 3 soruluk sinav, 2 atla + sure asimi
        for i in range(3):
            panel.store.add_question(f"atla testi {i}?", str(i), course="Algebra")
        panel.e_count.set(3)
        panel.e_duration.set(5)
        panel._start_exam()
        panel._next_question()  # atla
        panel._next_question()  # atla
        skip_exam_id = panel._exam_id
        panel._exam_deadline = _dt.now() - _td(seconds=1)
        panel._tick_exam_countdown()
        row2 = panel.store.get_exam(skip_exam_id)
        summary = panel.e_reveal.get("1.0", "end")
        check("Cevaplanmayan  : 3" in summary, "atlanan sorular cevaplanmamis sayildi (DB'den)")
        check("puanda yanlış sayıldı" in summary, "ozet metni puanlamayla celismiyor")
        check(row2 is not None and row2["status"] == "finished", "atla+sure asimi sinavi kapatti")
        panel.e_duration.set(0)
        panel._refresh_stats()
        check(True, "stats tab refresh runs without crash")
        # Disa aktarma, gorunumun 1000 satirlik sinirina takilmamali:
        # _export_rows ayni filtreyle TUM kumeyi getirir (_bank_filter_kwargs).
        for i in range(1005):
            panel.store.add_question(f"otomatik toplu soru {i}?", str(i), course="TopluTest")
        panel.f_course["values"] = list(panel.f_course["values"]) + ["TopluTest"]
        panel.f_course.set("TopluTest")
        panel._refresh_bank()
        check(len(panel._q_rows) == 1000, "gorunum 1000 satirla sinirli (bilinen gorunum siniri)")
        check(len(panel._export_rows()) == 1005, "_export_rows filtreli kumenin tamamini getirir")
        panel.f_course.set("")
        root.destroy()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        check(False, f"panel raised: {exc}")
        try:
            root.destroy()
        except Exception:
            pass


def test_question_packs():
    print("\nQUESTION PACKS (generators + licensing)")
    import json
    import question_packs as qp
    from student_tracker import StudentStore
    check(len(qp.BUILTIN_PACKS) >= 5, "at least 5 built-in generator packs")
    ids = [p["id"] for p in qp.BUILTIN_PACKS]
    check("prealgebra_core" in ids and "algebra_core" in ids, "core packs present")

    rows = qp.generate("algebra_core", count=12, lang="tr", seed=7)
    check(len(rows) == 12, f"generate -> 12 questions (got {len(rows)})")
    check(len({r["question"] for r in rows}) == 12, "generated questions are unique")
    r0 = rows[0]
    for k in ("question", "answer", "topic", "difficulty", "course", "lang",
              "source_pack", "license"):
        check(k in r0 and str(r0[k]) != "", f"generated row has '{k}'")
    check(all(r["answer"].strip() for r in rows), "every generated question has an answer")
    check(r0["license"] == qp.BUILTIN_LICENSE, "built-in pack carries the original-content licence")
    check("third-party" in qp.BUILTIN_LICENSE, "licence text states no third-party rights")

    tr = qp.generate("prealgebra_core", count=6, lang="tr", seed=3)
    en = qp.generate("prealgebra_core", count=6, lang="en", seed=3)
    check(tr[0]["lang"] == "tr" and en[0]["lang"] == "en", "lang recorded on rows")
    check(any(t["topic"] != e["topic"] for t, e in zip(tr, en)), "topics are localised (tr != en)")
    again = qp.generate("algebra_core", count=12, lang="tr", seed=7)
    check([r["question"] for r in again] == [r["question"] for r in rows], "seed -> deterministic")
    hard = qp.generate("algebra_core", count=5, lang="tr", seed=1, difficulty="Hard")
    check(hard and all(r["difficulty"] == "Hard" for r in hard), "difficulty filter honoured")
    check(qp.generate("no_such_pack", count=5) == [], "unknown pack -> []")

    packs = qp.list_packs(lang="tr")
    check(len(packs) >= 5, "list_packs includes built-ins")
    check(all(p.get("license") for p in packs), "every listed pack exposes a licence")

    # external JSON pack (openly licensed) round-trip.
    # NOTE: a FRESH temp dir every run — a fixed folder would keep last run's
    # packs and break the "exactly one pack" assertion below.
    folder = tempfile.mkdtemp(prefix="qp_ext_")
    ext = {"id": "ext_demo", "name": "Ext Demo", "course": "Algebra", "lang": "en",
           "license": "CC BY 4.0", "attribution": "Demo Author", "source_url": "https://example.org",
           "questions": [{"question": "1+1=?", "answer": "2", "topic": "Add", "difficulty": "Easy"},
                         {"question": "2+2=?", "answer": "4", "topic": "Add", "difficulty": "Easy"}]}
    with open(os.path.join(folder, "ext_demo.json"), "w", encoding="utf-8") as f:
        json.dump(ext, f)
    loaded = qp.load_external_packs(folder)
    check(len(loaded) == 1 and loaded[0]["id"] == "ext_demo", "external JSON pack discovered")
    check(loaded[0]["license"] == "CC BY 4.0", "external licence read")
    check(loaded[0]["count"] == 2, "external pack question count")
    eq = qp.external_questions(loaded[0])
    check(len(eq) == 2 and eq[0]["license"] == "CC BY 4.0", "external questions carry the licence")
    # a pack with no licence is flagged, not silently trusted
    with open(os.path.join(folder, "nolic.json"), "w", encoding="utf-8") as f:
        json.dump({"id": "nolic", "name": "No Licence",
                   "questions": [{"question": "q", "answer": "a"}]}, f)
    flagged = [p for p in qp.load_external_packs(folder) if p["id"] == "nolic"]
    check(flagged and flagged[0]["license"].startswith("UNKNOWN"), "missing licence -> UNKNOWN flag")

    # import into the bank
    s = StudentStore(_tmp_db())
    n = qp.import_into_store(s, "geometry_core", count=8, lang="tr", seed=5)
    check(n == 8, f"import_into_store -> 8 (got {n})")
    q = s.list_questions(limit=1)[0]
    check(q["source_pack"] == "geometry_core", "imported question records source_pack")
    check(q["license_text"] == qp.BUILTIN_LICENSE, "imported question stores the licence")
    check(q["lang"] == "tr", "imported question stores lang")
    n2 = qp.import_into_store(s, "geometry_core", count=8, lang="tr", seed=5)
    check(n2 == 0, "re-importing the same questions is de-duplicated")
    check(len(s.list_questions(source_pack="geometry_core")) == 8, "filter bank by source_pack")
    check(s.distinct_values("source_pack") == ["geometry_core"], "distinct source_pack")
    summary = s.pack_summary()
    check(summary and summary[0]["count"] == 8, "pack_summary counts imported questions")
    check(s.delete_by_pack("geometry_core") == 8, "delete_by_pack removes the pack's questions")
    check(s.count_questions() == 0, "bank empty after pack delete")


def test_answer_verdict():
    print("\nANSWER VERDICT (sympy equivalence)")
    from student_tracker import answer_verdict, check_answer
    check(answer_verdict("7", "7") == "match", "identical -> match")
    check(answer_verdict("x = 2", "2") == "equivalent", "'x = 2' vs '2' -> equivalent")
    check(answer_verdict("0.5", "1/2") == "equivalent", "decimal vs fraction -> equivalent")
    check(answer_verdict("y = 3, x = 2", "x = 2, y = 3") == "equivalent",
          "system answers order-independent")
    check(answer_verdict("12pi", "12π") == "equivalent", "pi symbol handled")
    check(answer_verdict("4x", "2x + 2x") == "equivalent", "algebraic simplification")
    check(answer_verdict("x=2,3", "{2, 3}") == "equivalent", "root list vs set braces")
    check(answer_verdict("f'(x) = 6x + 2", "6x+2") == "equivalent", "derivative prefix stripped")
    check(answer_verdict("m = 3/4", "0.75") == "equivalent", "named fraction vs decimal")
    check(answer_verdict("5", "6") == "different", "clearly different values")
    check(answer_verdict("x = 2", "x = 2, y = 3") == "different", "part-count mismatch")
    check(answer_verdict("elma", "5") == "unknown", "plain word -> unknown (student decides)")
    check(answer_verdict("", "5") == "unknown", "empty -> unknown")
    check(check_answer("x = 2", "2") is True, "check_answer accepts equivalence")
    check(check_answer("elma", "5") is False, "check_answer refuses unknown")


def test_srs():
    print("\nSPACED REPETITION (Leitner)")
    from datetime import date
    from student_tracker import srs_schedule, SRS_INTERVALS
    today = date(2026, 7, 15)

    def h(*pairs):
        return [(s, d + " 10:00:00") for s, d in pairs]

    check(srs_schedule([], today=today) is None, "no history -> not scheduled")
    check(srs_schedule(h(("unsolved", "2026-07-10")), today=today) is None,
          "reset to unsolved -> not scheduled")
    w = srs_schedule(h(("wrong", "2026-07-10")), today=today)
    check(w and w["box"] == 0 and w["due"] == date(2026, 7, 10), "wrong -> due immediately, box 0")
    check(w["overdue_days"] == 5, "wrong 5 days ago -> 5 days overdue")
    s1 = srs_schedule(h(("solved", "2026-07-14")), today=today)
    check(s1 and s1["box"] == 1 and s1["due"] == date(2026, 7, 15), "1 solve -> due next day")
    s2 = srs_schedule(h(("solved", "2026-07-01"), ("solved", "2026-07-05")), today=today)
    check(s2 and s2["box"] == 2 and s2["due"] == date(2026, 7, 8), "2 solves -> +3 days")
    check(s2["overdue_days"] == 7, "overdue days computed")
    mixed = srs_schedule(h(("solved", "2026-07-01"), ("wrong", "2026-07-02"),
                           ("solved", "2026-07-10")), today=today)
    check(mixed and mixed["box"] == 1, "streak resets after a wrong")
    check(len(SRS_INTERVALS) >= 5, "interval ladder defined")


def test_due_analytics():
    print("\nDUE QUEUE + DASHBOARD ANALYTICS")
    from student_tracker import StudentStore, ProgressAnalytics, ExamEngine
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    stats = ProgressAnalytics(s)
    q1 = s.add_question("1+1=?", "2", course="PreAlg", topic="Add")
    q2 = s.add_question("2+2=?", "4", course="PreAlg", topic="Add")
    q3 = s.add_question("3*3=?", "9", course="Alg", topic="Mul")
    check(stats.due_questions(sid) == [], "empty history -> nothing due")
    s.record_attempt(q1, sid, "wrong")            # due immediately
    s.record_attempt(q2, sid, "solved")           # due tomorrow, not today
    s.record_attempt(q3, sid, "review")           # due immediately
    due = stats.due_questions(sid)
    due_ids = {d["question_id"] for d in due}
    check(due_ids == {q1, q3}, f"wrong+review due now, fresh solve not (got {due_ids})")
    summary = stats.due_summary(sid)
    check(summary["due_now"] == 2 and set(summary["due_ids"]) == {q1, q3}, "due_summary counts")
    check(summary["due_week"] >= 3, "week window includes tomorrow's review")
    cp = stats.course_progress(sid)
    pre = next(c for c in cp if c["course"] == "PreAlg")
    check(pre["total"] == 2 and pre["solved"] == 1 and pre["percent"] == 50.0,
          "course_progress per course")
    # exam built from an explicit id list (the dashboard drill path)
    engine = ExamEngine(s)
    exam_id, items = engine.build(sid, title="Tekrar", question_ids=summary["due_ids"],
                                  count=10, shuffle=False)
    check(exam_id is not None and len(items) == 2, "exam built from due ids")
    got = [it["question_id"] for it in items]
    check(set(got) == {q1, q3}, "due drill contains exactly the due questions")


def _geri_tarihle(store, question_id, gun):
    """Bir sorunun TÜM denemelerini `gun` gün geriye alır (sentetik senaryolar).

    record_attempt bilerek zaman damgası parametresi almıyor (üretimde her
    deneme 'şimdi'dir); testler tarihi doğrudan yazar.
    """
    from datetime import datetime, timedelta
    stamp = (datetime.now() - timedelta(days=gun)).strftime("%Y-%m-%d %H:%M:%S")
    store.conn.execute("UPDATE attempts SET attempted_at=? WHERE question_id=?",
                       (stamp, question_id))
    store.conn.commit()


def test_study_advisor():
    print("\n📌 BU HAFTA — KURAL TABANLI ÖNERİ MOTORU")
    from student_tracker import (StudentStore, StudyAdvisor, ZAYIF_DOGRULUK,
                                 ZAYIF_MIN_DENEME, IHMAL_GUN, YIGILMA_ESIK)
    check(ZAYIF_DOGRULUK == 60.0 and ZAYIF_MIN_DENEME == 5 and IHMAL_GUN == 7,
          "esikler belgelenen degerlerde (%60 / 5 deneme / 7 gun)")

    # --- 1) veri yokken SUSAR ve nedenini soyler ---
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    adv = StudyAdvisor(s)
    r = adv.suggest(sid)
    check(r["oneriler"] == [], "denemesiz bankada oneri uretilmez")
    check("yeterli veri yok" in r["mesaj"], "nedeni acikca yaziliyor (istatistik uydurulmuyor)")
    q0 = s.add_question("1+1=?", "2", course="PreAlg", topic="Toplama")
    check(adv.suggest(sid)["oneriler"] == [], "soru var ama deneme yoksa yine susar")

    # --- 2) zayif konu esikleri ---
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    adv = StudyAdvisor(s)
    # Turev: 12 deneme, 5 dogru -> %41.7  (zayif)
    turev = [s.add_question(f"turev {i}", "x", course="Calculus 1", topic="Türev")
             for i in range(6)]
    for i, qid in enumerate(turev):
        s.record_attempt(qid, sid, "solved" if i < 2 else "wrong")
        s.record_attempt(qid, sid, "solved" if i < 3 else "wrong")
    # Limit: 4 denemeli konu (esigin ALTINDA veri) -> konusma
    az = s.add_question("az veri", "x", course="Calculus 1", topic="Seri")
    for _ in range(4):
        s.record_attempt(az, sid, "wrong")
    # Tam esikte: 5 deneme, 3 dogru = %60 -> zayif DEGIL (esik dahil degil)
    esik = s.add_question("esik", "x", course="Calculus 1", topic="Limit")
    for i in range(5):
        s.record_attempt(esik, sid, "solved" if i < 3 else "wrong")

    zayif = adv.zayif_konular(sid)
    konular = {z["konu"] for z in zayif}
    check("Türev" in konular, "dusuk dogruluklu + yeterli denemeli konu onerilir")
    check("Seri" not in konular, f"{ZAYIF_MIN_DENEME} denemenin altinda konu ONERILMEZ")
    check("Limit" not in konular, "tam %60 zayif SAYILMAZ (esik disarida)")
    t = next(z for z in zayif if z["konu"] == "Türev")
    check(t["deneme"] == 12 and t["dogruluk"] == 41.7,
          f"dogruluk denemelerden hesaplanir ({t['deneme']} deneme, %{t['dogruluk']})")
    check("12 denemede" in t["gerekce"] and "41.7" in t["gerekce"],
          f"gerekce gorunur ve sayilari tasir: {t['gerekce']!r}")
    check(t["eylem"] == "sinav_konu" and "sınav" in t["eylem_metni"],
          "tek tik eylemi: bu konudan sinav")

    # --- 3) ihmal edilen kurs ---
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    adv = StudyAdvisor(s)
    eski = s.add_question("eski", "1", course="Geometry", topic="Açı")
    yeni = s.add_question("yeni", "1", course="Algebra", topic="Denklem")
    s.add_question("hic", "1", course="Trigonometry", topic="Sinüs")   # deneme yok
    s.record_attempt(eski, sid, "solved")
    s.record_attempt(yeni, sid, "solved")
    _geri_tarihle(s, eski, 10)
    _geri_tarihle(s, yeni, 3)
    ihmal = adv.ihmal_edilen_kurslar(sid)
    kurslar = {i["kurs"] for i in ihmal}
    check("Geometry" in kurslar, f"{IHMAL_GUN}+ gundur dokunulmamis kurs onerilir")
    check("Algebra" not in kurslar, "3 gun once calisilan kurs onerilmez")
    check("Trigonometry" not in kurslar,
          "HIC denenmemis kurs 'biraktigin kurs' sayilmaz (o, Denenmemis kartinin isi)")
    g = next(i for i in ihmal if i["kurs"] == "Geometry")
    check(g["gun"] == 10 and "10 gündür" in g["gerekce"], "gerekce gun sayisini yazar")
    check(g["eylem"] == "kursa_devam", "eylem: kursa devam et")

    # --- 4) tekrar yigilmasi ---
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    adv = StudyAdvisor(s)
    az_qids = [s.add_question(f"az{i}", "1", course="C", topic="T") for i in range(5)]
    for qid in az_qids:
        s.record_attempt(qid, sid, "wrong")
    check(adv.tekrar_yigilmasi(sid) == [],
          f"{YIGILMA_ESIK} esiginin altinda yigilma denmez")
    for i in range(YIGILMA_ESIK):
        qid = s.add_question(f"cok{i}", "1", course="C", topic="T")
        s.record_attempt(qid, sid, "wrong")
    yig = adv.tekrar_yigilmasi(sid)
    check(len(yig) == 1 and yig[0]["adet"] >= YIGILMA_ESIK,
          f"esik asilinca tek yigilma onerisi ({yig[0]['adet'] if yig else 0} soru)")
    check(yig[0]["gun_str"] == "bugün", "bugune yigilan tekrarlar 'bugün' der")
    check(len(yig[0]["qids"]) == yig[0]["adet"], "eylem icin soru kimlikleri tasinir")

    # --- 5) birlestirme: en fazla 3, cesitli, oncelikli ---
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    adv = StudyAdvisor(s)
    for k, konu in enumerate(("A", "B", "C", "D")):        # 4 zayif konu
        for i in range(3):
            qid = s.add_question(f"{konu}{i}", "1", course="Kurs1", topic=konu)
            s.record_attempt(qid, sid, "wrong")
            s.record_attempt(qid, sid, "wrong")
    eski_q = s.add_question("eski", "1", course="Kurs2", topic="Z")
    s.record_attempt(eski_q, sid, "solved")
    _geri_tarihle(s, eski_q, 20)
    r = adv.suggest(sid)
    check(len(r["oneriler"]) == 3, f"en fazla 3 oneri ({len(r['oneriler'])})")
    turler = [o["tur"] for o in r["oneriler"]]
    check(turler.count("zayif_konu") <= 2, "cesitlilik: en fazla 2 zayif konu")
    check("ihmal_edilen_kurs" in turler or "tekrar_yigilmasi" in turler,
          "diger sinyallere de yer birakilir")
    onc = [o["oncelik"] for o in r["oneriler"]]
    check(onc == sorted(onc, reverse=True), "oneriler oncelige gore sirali")
    check("AI kullanılmadı" in r["mesaj"], "mesaj AI cagrisi olmadigini soyler")
    check(len(adv.suggest(sid, limit=1)["oneriler"]) == 1, "limit uygulanir")

    # --- 6) her sey yolundayken: bos liste AMA farkli mesaj ---
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    adv = StudyAdvisor(s)
    for i in range(6):
        qid = s.add_question(f"iyi{i}", "1", course="Kurs", topic="Konu")
        s.record_attempt(qid, sid, "solved")
    r = adv.suggest(sid)
    check(r["oneriler"] == [], "zayiflik yokken oneri cikmaz")
    check("yeterli veri yok" not in r["mesaj"] and "🎉" in r["mesaj"],
          f"'veri yok' ile 'her sey yolunda' ayri mesajlar: {r['mesaj'][:40]!r}")

    # --- 7) silinmis soru gecmiste kalirsa cokmez ---
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    adv = StudyAdvisor(s)
    qid = s.add_question("silinecek", "1", course="K", topic="T")
    for _ in range(6):
        s.record_attempt(qid, sid, "wrong")
    s.delete_question(qid)
    r = adv.suggest(sid)
    check(isinstance(r["oneriler"], list), "silinmis soruya ait denemeler sessizce atlanir")


def test_iki_dillilik():
    print("\n🌍 İKİ DİLLİLİK (TR/EN)")
    from mca_common import t2, normalize_lang, app_lang
    import types as _t
    check(t2("Kaydet", "Save", "tr") == "Kaydet", "t2 varsayilan TR")
    check(t2("Kaydet", "Save", "en") == "Save", "t2 EN")
    check(t2("Kaydet", "Save", "English") == "Save", "dil adi esnek ('English')")
    check(t2("Kaydet", "", "en") == "Kaydet", "bos EN cevirisi TR'ye duser (bos etiket yok)")
    check(normalize_lang("EN-us") == "en" and normalize_lang(None) == "tr",
          "normalize_lang")
    check(app_lang(_t.SimpleNamespace(language="en")) == "en", "app_lang panelden okur")
    check(app_lang(object()) == "tr", "app'te dil yoksa TR (panel testte de kurulabilsin)")

    from student_tracker import (StudentStore, StudyAdvisor, haftalik_rapor_html,
                                 haftalik_rapor_verisi)
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    for i in range(6):
        qid = s.add_question(f"soru {i}", "1", course="Kurs", topic="Konu")
        s.record_attempt(qid, sid, "wrong")

    tr = StudyAdvisor(s, lang="tr").suggest(sid)
    en = StudyAdvisor(s, lang="en").suggest(sid)
    check(tr["oneriler"] and en["oneriler"], "iki dilde de oneri uretiliyor")
    check("denemede" in tr["oneriler"][0]["gerekce"], f"TR gerekce: {tr['oneriler'][0]['gerekce']}")
    check("attempts" in en["oneriler"][0]["gerekce"], f"EN gerekce: {en['oneriler'][0]['gerekce']}")
    check("sınav" in tr["oneriler"][0]["eylem_metni"]
          and "exam" in en["oneriler"][0]["eylem_metni"], "eylem metni iki dilde")
    check("kural tabanlı" in tr["mesaj"] and "rule-based" in en["mesaj"],
          "ozet mesaji iki dilde")
    bos = StudentStore(_tmp_db())
    bsid = bos.ensure_default_student()
    check("yeterli veri yok" in StudyAdvisor(bos, lang="tr").suggest(bsid)["mesaj"],
          "TR 'veri yok' mesaji")
    check("Not enough data" in StudyAdvisor(bos, lang="en").suggest(bsid)["mesaj"],
          "EN 'veri yok' mesaji")

    h_tr = haftalik_rapor_html(s, sid, lang="tr")
    h_en = haftalik_rapor_html(s, sid, lang="en")
    check("Haftalık Özet" in h_tr and "Weekly Summary" in h_en, "rapor basligi iki dilde")
    check("Çalışma günü" in h_tr and "Study days" in h_en, "rapor kartlari iki dilde")
    check('<html lang="tr"' in h_tr and '<html lang="en"' in h_en,
          "HTML dil etiketi dogru")
    check("Bu haftanın zayıf konuları" in h_tr and "weak topics" in h_en,
          "rapor bolum basliklari iki dilde")
    d_en = haftalik_rapor_verisi(s, sid, lang="en")
    check(d_en["gunler"][0]["ad"] in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
          f"gun adlari EN ({d_en['gunler'][0]['ad']})")

    # Panel: dil sahibinden okunur
    try:
        import tkinter as tk
        from student_tracker import StudentTrackerPanel
        root = tk.Tk()
        root.withdraw()
    except Exception:
        print("   [SKIP] Tk yok — panel dil kontrolleri atlandi")
        return
    try:
        app_en = _t.SimpleNamespace(selected_path=None, selected_course="", pdf_viewer=None,
                                    language="en", set_status=lambda *a, **k: None)
        p_en = StudentTrackerPanel(root, app_en, db_path=_tmp_db())
        etiketler = [p_en.nb.tab(i, "text") for i in range(p_en.nb.index("end"))]
        check("Today" in etiketler and "Questions" in etiketler,
              f"panel sekmeleri EN ({etiketler})")
        check(p_en.advisor.lang == "en", "oneri motoru da EN")
        p_en.destroy()
        app_tr = _t.SimpleNamespace(selected_path=None, selected_course="", pdf_viewer=None,
                                    language="tr", set_status=lambda *a, **k: None)
        p_tr = StudentTrackerPanel(root, app_tr, db_path=_tmp_db())
        etiketler_tr = [p_tr.nb.tab(i, "text") for i in range(p_tr.nb.index("end"))]
        check("Bugün" in etiketler_tr and "Soru Bankası" in etiketler_tr,
              f"panel sekmeleri TR ({etiketler_tr})")
        p_tr.destroy()
    finally:
        root.destroy()


def test_mcpack_images():
    print("\n📦 GÖRSELLİ PAKET (.mcpack) — TAM TUR")
    import json as _json
    import shutil as _sh
    import tempfile as _tf
    import zipfile as _zip
    from pathlib import Path as _P
    import question_packs as qp
    from student_tracker import StudentStore

    klasor = _P(_tf.mkdtemp(prefix="mcpack_"))
    gorsel = klasor / "soru_01.png"
    gorsel.write_bytes(b"\x89PNG\r\n\x1a\n" + b"sahte-png-icerigi" * 8)

    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    q_metin = s.add_question("2+2=?", "4", course="PreAlg", topic="Toplama")
    q_gorsel = s.add_question(qp.IMAGE_ONLY_PREFIX + " sayfa 12", "17",
                              course="PreAlg", topic="Fonksiyon",
                              image_path=str(gorsel))
    q_kayip = s.add_question(qp.IMAGE_ONLY_PREFIX + " sayfa 13", "5",
                             course="PreAlg", topic="Fonksiyon",
                             image_path=str(klasor / "yok.png"))
    rows = s.list_questions(limit=100)

    # --- 1) ESKI DUZ .json bicimi AYNEN calisir (geriye uyum) ---
    duz = klasor / "eski.json"
    yazilan, atlanan = qp.export_pack(rows, duz, name="Eski", course="PreAlg")
    check(duz.exists() and yazilan == 1 and atlanan == 2,
          f".json bicimi metin sorusunu yazar, gorselleri atlar ({yazilan}/{atlanan})")
    veri = _json.loads(duz.read_text(encoding="utf-8"))
    check("images" not in veri and "format" not in veri,
          ".json paketi eski semayi bozmadan yaziyor")
    check(all("image" not in q for q in veri["questions"]),
          "duz pakette gorsel alani yok")

    # --- 2) .mcpack: ZIP + images/ ---
    zipli = klasor / "yeni.mcpack"
    yazilan2, atlanan2 = qp.export_pack(rows, zipli, name="Yeni", course="PreAlg",
                                        license_text="CC BY 4.0", attribution="Test")
    check(zipli.exists(), ".mcpack dosyasi olustu")
    check(yazilan2 == 2, f"metin + gorselli soru yazildi ({yazilan2})")
    check(atlanan2 == 1, f"gorsel DOSYASI kayip olan soru yine atlandi ({atlanan2})")
    with _zip.ZipFile(zipli) as z:
        adlar = set(z.namelist())
        icerik = _json.loads(z.read(qp.MCPACK_JSON).decode("utf-8"))
    check(qp.MCPACK_JSON in adlar, "zip icinde paket.json var")
    check(any(a.startswith("images/") for a in adlar), f"zip icinde images/ var ({adlar})")
    check(icerik.get("format") == "mcpack/1" and icerik.get("images") == 1,
          "paket.json bicim ve gorsel sayisini bildiriyor")
    gorselli_kayit = [q for q in icerik["questions"] if q.get("image")]
    check(len(gorselli_kayit) == 1 and gorselli_kayit[0]["image"] == "images/soru_01.png",
          f"soru kaydinda image alani ({gorselli_kayit[:1]})")
    check(icerik["license"] == "CC BY 4.0", "lisans zip'te de tasiniyor")

    # --- 3) Yukleyici ikisini de goruyor ---
    paketler = {p["id"]: p for p in qp.load_external_packs(klasor)}
    check(len(paketler) == 2, f"hem .json hem .mcpack listelendi ({sorted(paketler)})")
    check(paketler["eski"]["kind_detail"] == "json"
          and paketler["yeni"]["kind_detail"] == "mcpack", "bicim ayrimi dogru")
    check(paketler["yeni"]["images"] == 1, "paket listesi gorsel sayisini gosteriyor")

    sorular = qp.external_questions(paketler["yeni"])
    gorselli = [q for q in sorular if q.get("image_in_pack")]
    check(len(gorselli) == 1, "gorselli soru yukleyiciden geciyor")
    check(gorselli[0]["_zip"] == str(zipli), "gorselin hangi pakette oldugu tasiniyor")
    # --- 4) Ice aktarma: gorsel gercekten cikariliyor ---
    hedef = _P(_tf.mkdtemp(prefix="qimg_"))
    eski_fn = qp._gorsel_hedef_klasoru
    qp._gorsel_hedef_klasoru = lambda: hedef
    try:
        # Onizleme (external_questions) diske DOKUNMAMALI: kullanici paketi
        # yalnizca listelerken dosya sistemine sizinti olmasin.
        qp.external_questions(paketler["yeni"])
        check(not list(hedef.iterdir()),
              "onizleme diske dosya YAZMAZ (cikarma ice aktarmada olur)")
        s2 = StudentStore(_tmp_db())
        eklendi = qp.import_into_store(s2, "yeni", count=50, folder=klasor)
        check(eklendi == 2, f"iki soru da bankaya girdi ({eklendi})")
        yeni_rows = s2.list_questions(limit=50)
        yollar = [str(r["image_path"] or "") for r in yeni_rows if r["image_path"]]
        check(len(yollar) == 1, f"bir soruya gorsel baglandi ({yollar})")
        check(_P(yollar[0]).exists(), "gorsel diske gercekten cikarildi")
        check(_P(yollar[0]).read_bytes().startswith(b"\x89PNG"),
              "cikarilan dosya kaynakla ayni icerikte")
        check(_P(yollar[0]).parent == hedef, "gorsel question_images klasorune gitti")

        # ayni paketi tekrar aktarmak var olan dosyanin UZERINE YAZMAZ
        s3 = StudentStore(_tmp_db())
        qp.import_into_store(s3, "yeni", count=50, folder=klasor)
        dosyalar = sorted(p.name for p in hedef.iterdir())
        check(len(dosyalar) == 2 and "soru_01.png" in dosyalar,
              f"ikinci aktarim yeni ad uretti, ustune yazmadi ({dosyalar})")

        # --- 5) Guvenlik: kotu yollar reddedilir ---
        check(qp._guvenli_gorsel_adi("images/a.png") == "a.png", "normal yol kabul")
        for kotu in ("../../evil.png", "images/../../evil.png", "/etc/passwd",
                     "images/alt/x.png", "images/x.exe", "", None,
                     "C:/Windows/System32/x.png"):
            check(qp._guvenli_gorsel_adi(kotu) is None, f"reddedildi: {kotu!r}")

        # --- 6) Bozuk .mcpack listeyi cokertmez ---
        (klasor / "bozuk.mcpack").write_bytes(b"bu bir zip degil")
        paketler2 = qp.load_external_packs(klasor)
        check(len(paketler2) == 2, "bozuk paket sessizce atlanir, digerleri durur")
    finally:
        qp._gorsel_hedef_klasoru = eski_fn
        _sh.rmtree(klasor, ignore_errors=True)
        _sh.rmtree(hedef, ignore_errors=True)


def test_exam_history_and_weekly_report():
    print("\n📄 SINAV GEÇMİŞİ + HAFTALIK ÖZET RAPORU")
    import re as _re
    from datetime import date, timedelta
    from student_tracker import (StudentStore, ExamEngine, haftalik_rapor_verisi,
                                 haftalik_rapor_html, sinav_sure_modu,
                                 RAPOR_MIN_DENEME)
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    bugun = date.today()

    # --- 1) bos hafta: rapor URETILIR ama bolumler "veri yok" der ---
    d = haftalik_rapor_verisi(s, sid, today=bugun)
    check(d["toplam_deneme"] == 0 and d["veri_var"] is False, "bos haftada sayilar sifir")
    check(d["dogruluk"] is None and d["degisim"] is None,
          "veri yokken dogruluk 0 DEGIL None (uydurma yok)")
    html = haftalik_rapor_html(s, sid, today=bugun)
    check(html.startswith("<!DOCTYPE html>") and html.rstrip().endswith("</html>"),
          "bos haftada da tam HTML belgesi uretilir")
    check(html.count("Bu hafta") >= 3 or "veri yok" in html,
          "bos bolumler 'veri yok' diyor")
    check("<div style=\"flex:1;text-align:center\"" not in html,
          "BOS GRAFIK CIZILMEZ (cubuk yok)")

    # --- 2) sentetik haftalik veri: sayilar dogru mu ---
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    q = {}
    for konu, adet_dogru, adet_yanlis in (("Türev", 2, 6), ("Limit", 5, 1)):
        for i in range(adet_dogru + adet_yanlis):
            qid = s.add_question(f"{konu} {i}", "x", course="Calculus 1", topic=konu)
            s.record_attempt(qid, sid, "solved" if i < adet_dogru else "wrong")
            q.setdefault(konu, []).append(qid)
    d = haftalik_rapor_verisi(s, sid, today=bugun)
    check(d["toplam_deneme"] == 14, f"toplam deneme 14 (bulundu {d['toplam_deneme']})")
    check(d["dogru"] == 7 and d["yanlis"] == 7, "dogru/yanlis ayrimi")
    check(d["dogruluk"] == 50.0, f"haftalik dogruluk %50 (bulundu {d['dogruluk']})")
    check(d["calisma_gunu"] == 1, "tek gunde calisildi -> calisma gunu 1")
    check(len(d["gunler"]) == 7 and d["gunler"][-1]["gun"] == bugun.isoformat(),
          "7 gunluk pencere, son gun bugun")
    check(sum(g["deneme"] for g in d["gunler"]) == 14, "gunluk dagilim toplami tutuyor")
    zayif = {z["konu"]: z for z in d["zayif_konular"]}
    check("Türev" in zayif and zayif["Türev"]["dogruluk"] == 25.0,
          "haftalik zayif konu dogrulugu (Türev %25)")
    check(zayif["Türev"]["deneme"] == 8, "zayif konu deneme sayisi")
    check(d["zayif_konular"][0]["konu"] == "Türev", "en dusuk dogruluk basta")

    # az denemeli konu haftalik yoruma girmez
    az = s.add_question("Seri 1", "x", course="Calculus 1", topic="Seri")
    s.record_attempt(az, sid, "wrong")
    d2 = haftalik_rapor_verisi(s, sid, today=bugun)
    check(all(z["konu"] != "Seri" for z in d2["zayif_konular"]),
          f"{RAPOR_MIN_DENEME} denemenin altindaki konu haftalik raporda yorumlanmaz")

    # --- 3) onceki haftayla karsilastirma ---
    onceki_q = s.add_question("gecen hafta", "x", course="C", topic="T")
    s.record_attempt(onceki_q, sid, "solved")
    gecen = (bugun - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")
    s.conn.execute("UPDATE attempts SET attempted_at=? WHERE question_id=?",
                   (gecen, onceki_q))
    s.conn.commit()
    d3 = haftalik_rapor_verisi(s, sid, today=bugun)
    check(d3["onceki_dogruluk"] == 100.0, "onceki donem dogrulugu ayri hesaplanir")
    check(d3["degisim"] is not None and d3["degisim"] < 0,
          f"degisim gecen haftaya gore hesaplanir ({d3['degisim']})")

    # --- 4) hafta disi veri rapora SIZMAZ ---
    check(d3["toplam_deneme"] == 15,
          f"9 gun onceki deneme bu haftaya girmez (bulundu {d3['toplam_deneme']})")

    # --- 5) sinav gecmisi: sureli mi bilgisi ---
    engine = ExamEngine(s)
    exam_id, items = engine.build(sid, title="Süreli deneme", count=3)
    s.set_exam_time_limit(exam_id, 25 * 60)
    for it in items:
        engine.answer(exam_id, it["question_id"], sid, "x", True, duration_sec=12)
    engine.finish(exam_id, duration_sec=300)
    e = [x for x in s.list_exams(sid) if x["id"] == exam_id][0]
    check(sinav_sure_modu(e) == "25 dk", f"sureli sinav '25 dk' der ({sinav_sure_modu(e)})")
    exam2, items2 = engine.build(sid, title="Süresiz", count=2)
    s.set_exam_time_limit(exam2, 0)
    engine.finish(exam2, duration_sec=60)
    e2 = [x for x in s.list_exams(sid) if x["id"] == exam2][0]
    check(sinav_sure_modu(e2) == "süresiz", "sifir limit 'süresiz' der")
    exam3, _ = engine.build(sid, title="Eski kayıt", count=1)   # time_limit_sec NULL
    engine.finish(exam3, duration_sec=30)
    e3 = [x for x in s.list_exams(sid) if x["id"] == exam3][0]
    check(sinav_sure_modu(e3) == "?",
          "V48 oncesi kayitlarda sureli olup olmadigi UYDURULMAZ ('?')")

    # --- 6) sinav dokumu ---
    dokum = s.exam_detail(exam_id)
    check(len(dokum) == 3, "sinav dokumu tum sorulari getirir")
    check(dokum[0]["question_text"] and dokum[0]["duration_sec"] == 12,
          "dokumde soru metni + soru basina sure var")
    check([r["order_index"] for r in dokum] == [0, 1, 2], "dokum sira ile geliyor")

    # --- 7) rapor HTML butunlugu (dolu hafta) ---
    d4 = haftalik_rapor_verisi(s, sid, today=bugun)
    html = haftalik_rapor_html(s, sid, today=bugun, ogrenci_adi="Test Öğrenci", veri=d4)
    check(html.startswith("<!DOCTYPE html>") and html.rstrip().endswith("</html>"),
          "tam HTML belgesi")
    check("__" not in html.split("<style>")[0], "sablon yer tutuculari dolduruldu")
    check("window.print()" in html and "@media print" in html,
          "education sablonundan yazdirma serit + print CSS'i miras alindi")
    check("Test Öğrenci" in html, "ogrenci adi basliga giriyor")
    # Not: 5. adimdaki sinav yanitlari bankaya da deneme yaziyor, bu yuzden
    # oranlar degisti — sabit sayi yerine HESAPLANAN veriyle karsilastir.
    en_zayif = d4["zayif_konular"][0]
    check(en_zayif["konu"] in html and f"%{en_zayif['dogruluk']:g}" in html,
          f"zayif konu tablosu raporda ({en_zayif['konu']} %{en_zayif['dogruluk']:g})")
    check("Süreli deneme" in html and "25 dk" in html, "sinav satiri + sureli bilgisi raporda")
    check(html.count("<table") >= 2, "iki tablo (zayif konular + sinavlar)")
    kapaniyor = html.count("<table") == html.count("</table>")
    check(kapaniyor, "tablo etiketleri dengeli")
    check('style="grid-template-columns:1fr"' in html,
          "rapor icindekiler sutunu olmadan tek sutuna geciyor")
    acik = len(_re.findall(r"<div\b", html))
    kapali = len(_re.findall(r"</div>", html))
    check(acik == kapali, f"div etiketleri dengeli ({acik}/{kapali})")
    check("?" in html and "V48 öncesi" in html,
          "bilinmeyen sure modu icin aciklama dipnotu var")


def test_panel_advice_card():
    """📌 Bu Hafta kartı — kendi panel örneğiyle (soru sayıları başka testleri
    etkilemesin diye ayrı bir test)."""
    print("\n📌 BU HAFTA KARTI (headless Tk)")
    try:
        import tkinter as tk
        from tkinter import ttk as _ttk
    except Exception:
        print("   [SKIP] Tk unavailable")
        return
    import types
    from student_tracker import StudentTrackerPanel
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as exc:
        print(f"   [SKIP] no display: {exc}")
        return
    try:
        durumlar = []
        app = types.SimpleNamespace(selected_path=None, selected_course="Kurs",
                                    pdf_viewer=None, language="tr",
                                    set_status=lambda m, *a, **k: durumlar.append(m))
        panel = StudentTrackerPanel(root, app, db_path=_tmp_db())
        panel._refresh_advice()
        check(panel._dash_advice == [], "veri yokken kart bos oneri listesiyle kurulur")
        bos = panel.dash_advice_body.winfo_children()[0].cget("text")
        check("yeterli veri yok" in bos, "kart nedeni yaziyor (uydurmuyor)")

        for i in range(6):
            qid = panel.store.add_question(f"zayif {i}", "1", course="Kurs", topic="Konu")
            panel.store.record_attempt(qid, panel.student_id, "wrong")
        panel._refresh_advice()
        check(len(panel._dash_advice) == 1, "zayif konu karta dustu")
        etiketler = [w.cget("text") for f in panel.dash_advice_body.winfo_children()
                     for m in f.winfo_children() for w in m.winfo_children()
                     if isinstance(w, tk.Label)]
        check(any("Konu" in t for t in etiketler), "oneri basligi kartta")
        check(any("denemede" in t for t in etiketler), "GEREKCE kartta gorunuyor")
        dugmeler = [w for f in panel.dash_advice_body.winfo_children()
                    for w in f.winfo_children() if isinstance(w, _ttk.Button)]
        check(len(dugmeler) == 1 and "sınav" in dugmeler[0].cget("text"),
              "tek tik eylem dugmesi var")
        panel._sync_advice_wrap(types.SimpleNamespace(width=420))
        dar = [int(str(w.cget("wraplength")))
               for f in panel.dash_advice_body.winfo_children()
               for m in f.winfo_children() for w in m.winfo_children()
               if isinstance(w, tk.Label) and str(w.cget("wraplength")) not in ("", "0")]
        check(dar and max(dar) <= 420, "dar panelde gerekce sarmasi kuculur")

        dugmeler[0].invoke()
        check(panel._exam_id is not None and panel._exam_deadline is None,
              "oneri eylemi sinav baslatir ve BILEREK suresizdir")

        # "Kursa devam et": app kopru metodu yoksa sessiz kalmaz, bankadan sinav acar
        panel._dash_advice = [{"tur": "ihmal_edilen_kurs", "kurs": "Kurs", "konu": "",
                               "baslik": "Kurs", "eylem": "kursa_devam",
                               "eylem_metni": "→ Kursa devam et", "gerekce": "x"}]
        panel._run_advice(0)
        check(any("bulunamadı" in d for d in durumlar),
              f"kurs klasoru yoksa kullaniciya soylenir ({durumlar[-1][:40] if durumlar else '-'})")

        # Motor patlarsa pano ayakta kalir
        panel.advisor = types.SimpleNamespace(
            suggest=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("bozuk")))
        panel._refresh_advice()
        check("hesaplanamadı" in panel.dash_advice_note.cget("text"),
              "motor hatasi panoyu cokertmez, kartta yazar")

        # --- İstatistik > Sınavlar alt gorunumu ---
        check(hasattr(panel, "exam_tree"), "Sinavlar tablosu kuruldu")
        panel._refresh_stats()
        check(len(panel.exam_tree.get_children()) == 0,
              "biten sinav yokken tablo bos (aktif sinav listelenmez)")
        panel.exams.finish(panel._exam_id, duration_sec=45)
        panel._refresh_stats()
        check(len(panel.exam_tree.get_children()) == 1, "biten sinav tabloya dustu")
        deger = panel.exam_tree.item("0", "values")
        check(deger[5] == "süresiz", f"oneri sinavi 'süresiz' kaydedildi ({deger[5]})")
        panel._open_exam_detail()          # secim yok -> sessizce doner
        panel.exam_tree.selection_set("0")
        panel._open_exam_detail()
        dokum = [w for w in (list(panel.winfo_children())
                             + list(panel.winfo_toplevel().winfo_children()))
                 if isinstance(w, tk.Toplevel) and "döküm" in w.title()]
        check(len(dokum) == 1, "cift tik soru dokumu penceresi acar")
        agac = [w for w in dokum[0].winfo_children() if isinstance(w, _ttk.Treeview)]
        check(agac and len(agac[0].get_children()) >= 1, "dokumde soru satirlari var")
        dokum[0].destroy()
    finally:
        root.destroy()


def test_choices_and_media():
    print("\nMULTIPLE CHOICE + MEDIA (V44)")
    from student_tracker import (StudentStore, ExamEngine, render_math_image,
                                 question_images_dir, CHOICE_LETTERS)
    check(CHOICE_LETTERS == ("A", "B", "C", "D", "E"), "choice letters defined")
    s = StudentStore(_tmp_db())
    sid = s.ensure_default_student()
    qid = s.add_question("f(1)=5, f(3)=11 ise f(5)=?", "17",
                         course="Algebra", topic="Fonksiyon",
                         choices=["13", "15", "17", "19", "21"], correct_choice="c",
                         image_path="C:/tmp/örnek.png")
    r = s.get_question(qid)
    check(StudentStore.parse_choices(r) == ["13", "15", "17", "19", "21"],
          "choices stored and parsed back")
    check(r["correct_choice"] == "C", "correct choice normalised to upper letter")
    check(r["image_path"].endswith("örnek.png"), "image path stored")
    # trailing empty options are trimmed
    q2 = s.add_question("2+2=?", "4", choices=["3", "4", "", "", ""], correct_choice="B")
    check(StudentStore.parse_choices(s.get_question(q2)) == ["3", "4"],
          "trailing empty choices trimmed")
    # non-choice question parses to []
    q3 = s.add_question("serbest soru", "x")
    check(StudentStore.parse_choices(s.get_question(q3)) == [], "no choices -> []")
    # update path (panel sends the JSON string)
    import json as _json
    s.update_question(q2, choices=_json.dumps(["3", "4", "5"]), correct_choice="C")
    check(StudentStore.parse_choices(s.get_question(q2)) == ["3", "4", "5"],
          "update_question can rewrite choices")
    # exam items carry the choice columns
    engine = ExamEngine(s)
    _eid, items = engine.build(sid, question_ids=[qid], count=1, shuffle=False)
    it = items[0]
    check(it["correct_choice"] == "C" and StudentStore.parse_choices(it),
          "exam item exposes choices + correct_choice")
    check(it["image_path"].endswith("örnek.png"), "exam item exposes image_path")
    # LaTeX rendering (matplotlib is a project dependency)
    img, err = render_math_image(r"Kök bul: $x^2 - 5x + 6 = 0$")
    check(img is not None and img.width > 40, f"mathtext render works ({err})")
    bad, err2 = render_math_image(r"$\frac{1$")
    check(bad is None and err2, "broken LaTeX -> clear error, no crash")
    d = question_images_dir()
    check(d.exists() and d.name == "question_images", "question images dir created in APPDATA")


def test_pack_export():
    """export_pack: yaz -> load_external_packs ile geri oku -> ikinci store'a
    ice aktar. Siklarin, lisansin ve atifin tam tur korunmasini dogrular."""
    print("== Pack export (disa aktar + tam tur) ==")
    import tempfile as _tf
    import question_packs as qp
    from student_tracker import StudentStore
    s = StudentStore(_tmp_db())
    s.add_question("2+2=?", "4", course="Algebra", topic="Toplama", difficulty="Easy",
                   choices=["3", "4", "5"], correct_choice="b")
    s.add_question("x² ifadesinin türevi nedir?", "2x", course="Calculus", topic="Türev")
    s.add_question("[Görsel soru] kitap.pdf s.3", "A", course="Algebra",
                   image_path="yok.png", choices=["1", "2"], correct_choice="a")
    s.add_question("What is 3+3?", "6", course="Algebra", topic="Addition", lang="en")
    rows = s.list_questions(limit=100)
    check(len(rows) == 4, "4 soru bankada")

    folder = _tf.mkdtemp(prefix="mca_packs_")
    p = os.path.join(folder, "arkadas_paketi.json")
    written, skipped = qp.export_pack(rows, p, name="Arkadaş Paketi", course="Algebra",
                                      lang="tr", license_text="", attribution="Aziz")
    check(written == 3, "gorsel-disi 3 soru yazildi")
    check(skipped == 1, "gorsel-yalnizca soru atlandi")
    check(os.path.exists(p), "paket dosyasi olustu")

    packs = qp.load_external_packs(folder)
    check(len(packs) == 1 and packs[0]["id"] == "arkadas_paketi", "paket geri yuklendi")
    pk = packs[0]
    check(pk["license"].startswith("UNKNOWN"), "bos lisans UNKNOWN isaretlendi")
    check(pk["attribution"] == "Aziz", "atif korundu")
    check(pk["name"] == "Arkadaş Paketi", "unicode paket adi korundu")

    qs = qp.external_questions(pk)
    m = {q["question"]: q for q in qs}
    check(m.get("2+2=?", {}).get("choices") == ["3", "4", "5"], "siklar paket uzerinden korundu")
    check(m.get("2+2=?", {}).get("correct_choice") == "B", "dogru sik korundu (buyuk harfe normalize)")
    check("türevi" in " ".join(m.keys()), "unicode soru metni korundu")

    s2 = StudentStore(_tmp_db())
    n = qp.import_into_store(s2, "arkadas_paketi", count=100, lang="tr", folder=folder)
    check(n == 3, "ikinci bankaya 3 soru aktarildi")
    rows2 = {r["question_text"]: r for r in s2.list_questions(limit=100)}
    r2 = rows2.get("2+2=?")
    check(r2 is not None and (r2["correct_choice"] or "") == "B", "correct_choice DB'ye ulasti")
    check(r2 is not None and StudentStore.parse_choices(r2) == ["3", "4", "5"], "choices DB'ye ulasti")
    check(r2 is not None and (r2["license_text"] or "").startswith("UNKNOWN"), "lisans DB'ye ulasti")
    # Karisik banka: satirin KENDI kurs/dil bilgisi paket duzeyini ezmeli
    r3 = rows2.get("x² ifadesinin türevi nedir?")
    check(r3 is not None and r3["course"] == "Calculus", "satirin kendi kursu tam turda korundu")
    r4 = rows2.get("What is 3+3?")
    check(r4 is not None and (r4["lang"] or "") == "en", "satirin kendi dili tam turda korundu")

    # Hepsi gorsel-yalnizca ise dosya olusturulmamali
    w2, k2 = qp.export_pack([rows[0]] if rows[0]["question_text"].startswith("[Görsel") else
                            [r for r in rows if r["question_text"].startswith("[Görsel")],
                            os.path.join(folder, "bos.json"))
    check(w2 == 0 and not os.path.exists(os.path.join(folder, "bos.json")),
          "tamami gorsel-yalnizca ise dosya yazilmadi")


def main():
    print("=" * 64)
    print("Student Tracker — Test Suite")
    print("=" * 64)
    for fn in (test_import, test_answer_matching, test_answer_verdict, test_srs,
               test_students, test_questions,
               test_attempts_and_status, test_bulk_import, test_exam_engine,
               test_analytics, test_due_analytics, test_study_advisor,
               test_exam_history_and_weekly_report, test_choices_and_media,
               test_migration_safety,
               test_question_packs, test_pack_export, test_mcpack_images,
               test_iki_dillilik,
               test_panel_headless, test_panel_advice_card):
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
