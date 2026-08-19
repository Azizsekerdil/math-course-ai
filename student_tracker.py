# -*- coding: utf-8 -*-
"""
Student Tracker / Öğrenci Takip Sistemi
=======================================

Adds the three things the program was missing:

1. **Student profiles** — multiple learners, each with their own history.
2. **Question bank** — upload/enter questions (course, topic, difficulty, answer,
   source PDF + page, tags) and track *solved / wrong / unsolved / review* per
   student. This is the "çözdüğüm–çözemediğim soru" tracking.
3. **Exam / test engine** — build a test from the bank (filters + count, e.g.
   "only the ones I got wrong"), take it question by question, self-mark against
   the stored answer, and store the graded result.
4. **Progress analytics** — overview, per-topic mastery, weak topics, exam trend.

The logic layer (stores/engine/analytics) has NO Tkinter dependency, so it is
fully unit-testable head-less. Only StudentTrackerPanel touches Tk.
"""

import os
import csv
import json
import random
import sqlite3
import threading
from datetime import datetime, date, timedelta
from pathlib import Path

try:
    from mca_common import app_lang, t2
except Exception:      # mca_common yoksa panel yine Türkçe çalışsın
    def app_lang(app, default="tr"):
        try:
            return "en" if str(getattr(app, "language", default)).lower().startswith("en") else "tr"
        except Exception:
            return "tr"

    def t2(tr, en, lang="tr"):
        return en if (str(lang).lower().startswith("en") and en) else tr

# User data lives in %APPDATA%\MathCourseAI\data (moved there in V43 so it
# survives program moves and rebuilds). app_paths copies the old project-folder
# databases over automatically on first run.
try:
    from app_paths import DATA_DIR
except Exception:  # pragma: no cover — headless fallback
    DATA_DIR = Path(os.getenv("APPDATA") or Path.home()) / "MathCourseAI" / "data"
DB_PATH = DATA_DIR / "student_tracker.sqlite"

STATUSES = ("unsolved", "solved", "wrong", "review")
DIFFICULTIES = ("Easy", "Medium", "Hard")
CHOICE_LETTERS = ("A", "B", "C", "D", "E")


def question_images_dir():
    """Folder for question images cropped from PDFs (user data → APPDATA)."""
    d = DATA_DIR / "question_images"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


DARK_MODE = False   # apply_dark_palette() bunu True yapar (koyu tema V2)


def render_math_image(text, max_width_px=560, fontsize=13, dpi=115, dark=None):
    """Render text with $...$ mathtext segments to a PIL Image.

    matplotlib's mathtext covers the everyday LaTeX subset (fractions, roots,
    powers, integrals, Greek letters) with no network call at all — the desktop equivalent of
    a KaTeX preview. Returns (image, error); image is None when matplotlib or
    Pillow are missing or the LaTeX fails to parse."""
    text = str(text or "").strip()
    if not text:
        return None, "empty"
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from PIL import Image as PILImage
        import io as _io
    except Exception as exc:
        return None, f"matplotlib/Pillow gerekli: {exc}"
    # Koyu tema V2: onizleme ARAYUZ parcasi oldugu icin temayi izler; sinavdaki
    # soru gorseli ICERIKTIR ve bilerek acik kalir (cagiran dark=False geciyor).
    koyu = DARK_MODE if dark is None else bool(dark)
    murekkep = "#EDE5D8" if koyu else "#2B2620"
    zemin = "#1B1712" if koyu else "#FFFFFF"
    try:
        fig = Figure(figsize=(max_width_px / dpi, 5), dpi=dpi)
        FigureCanvasAgg(fig)
        fig.text(0.01, 0.99, text, va="top", ha="left", fontsize=fontsize,
                 wrap=True, color=murekkep)
        buf = _io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.08,
                    facecolor=zemin)
        buf.seek(0)
        return PILImage.open(buf), ""
    except Exception as exc:
        return None, f"LaTeX çözümlenemedi: {exc}"


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return datetime.now().strftime("%Y-%m-%d")


def normalize_answer(text):
    """Loose normalisation so '2 x + 1' == '2X+1' for a quick auto-suggestion."""
    s = str(text or "").strip().lower()
    for a, b in (("×", "*"), ("÷", "/"), ("−", "-"), (",", "."), ("^", "**")):
        s = s.replace(a, b)
    return "".join(ch for ch in s if not ch.isspace())


def _sympy_answer_parts(text):
    """Parse an answer string into a list of sympy expressions, or None.

    Accepts the common shapes stored in the bank: '7', '3/4', 'x = 2', 'x = 2, 3',
    'x = 2, y = -1', "f'(x) = 6x + 2", '12π', '{2, 3}'. Each comma-separated
    chunk is parsed after stripping a leading 'name =' part, so equivalent
    forms like 'x=2, y=3' vs '2, 3' compare equal part-by-part."""
    s = str(text or "").strip().lower()
    if not s:
        return None
    try:
        from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                                implicit_multiplication_application,
                                                convert_xor)
    except Exception:
        return None
    for a, b in (("π", "pi"), ("×", "*"), ("÷", "/"), ("−", "-"), ("√", "sqrt"),
                 ("²", "^2"), ("³", "^3"), ("{", ""), ("}", "")):
        s = s.replace(a, b)
    transformations = standard_transformations + (implicit_multiplication_application,
                                                  convert_xor)
    parts = []
    math_words = {"pi", "e", "oo", "inf", "sqrt", "abs", "sin", "cos", "tan", "log", "ln", "exp"}
    for chunk in s.split(","):
        chunk = chunk.strip()
        if "=" in chunk:
            chunk = chunk.split("=")[-1].strip()
        if not chunk:
            continue
        # A plain word ('elma', 'dogru') is text, not math — implicit
        # multiplication would silently parse it as e*l*m*a, so refuse it here.
        if len(chunk) > 1 and chunk.isalpha() and chunk not in math_words:
            return None
        try:
            parts.append(parse_expr(chunk, transformations=transformations))
        except Exception:
            return None
    return parts or None


def _sympy_equal(a, b):
    try:
        import sympy
        diff = sympy.simplify(a - b)
        return bool(diff == 0)
    except Exception:
        try:
            return bool(a == b)
        except Exception:
            return False


def answer_verdict(user_answer, correct_answer):
    """Compare a student's answer with the stored one.

    Returns one of:
      'match'      — identical after loose normalisation
      'equivalent' — mathematically equal per sympy (e.g. '0.5' vs '1/2',
                     'x=2, y=3' vs 'y = 3, x = 2', '2x+2x' vs '4x')
      'different'  — both sides parsed and they are NOT equal
      'unknown'    — could not be parsed; the student must decide

    Math answers have many equivalent forms, so even 'different' is shown only
    as a *suggestion* — the student always makes the final Doğru/Yanlış call."""
    u, c = normalize_answer(user_answer), normalize_answer(correct_answer)
    if not u or not c:
        return "unknown"
    if u == c:
        return "match"
    pu, pc = _sympy_answer_parts(user_answer), _sympy_answer_parts(correct_answer)
    if not pu or not pc:
        return "unknown"
    # A bare word ('elma', 'dogru') parses as a Symbol; that is text, not math —
    # no verdict can be given, the student decides.
    if any(getattr(p, "is_Symbol", False) for p in pu + pc):
        return "unknown"
    if len(pu) != len(pc):
        return "different"
    remaining = list(pc)
    for expr in pu:          # order-independent: 'y=3, x=2' matches 'x=2, y=3'
        for i, other in enumerate(remaining):
            if _sympy_equal(expr, other):
                del remaining[i]
                break
        else:
            return "different"
    return "equivalent"


def check_answer(user_answer, correct_answer):
    """True when the two answers match exactly or are mathematically equivalent."""
    return answer_verdict(user_answer, correct_answer) in ("match", "equivalent")


# ===========================================================================
# Spaced repetition (Leitner) — computed purely from the attempt history,
# so no schema change and no separate scheduler state to migrate.
# ===========================================================================
SRS_INTERVALS = (1, 3, 7, 14, 30, 60)   # days until next review per streak


def srs_schedule(history, today=None):
    """Next review date for one question from its attempt history.

    `history` is [(status, attempted_at 'YYYY-MM-DD ...'), ...] oldest→newest.
    Returns {'due': date, 'box': int, 'overdue_days': int} or None when the
    question is not in the review cycle (never attempted, or reset to unsolved).

      • last attempt wrong/review  → due immediately (box 0)
      • last attempt solved        → streak of trailing solves = box,
                                     due = last date + SRS_INTERVALS[box-1]
    """
    if not history:
        return None
    today = today or date.today()
    status, stamp = history[-1]
    try:
        last_day = datetime.strptime(str(stamp)[:10], "%Y-%m-%d").date()
    except Exception:
        last_day = today
    if status == "unsolved":
        return None
    if status in ("wrong", "review"):
        return {"due": last_day, "box": 0, "overdue_days": max(0, (today - last_day).days)}
    streak = 0
    for st, _ in reversed(history):
        if st == "solved":
            streak += 1
        else:
            break
    interval = SRS_INTERVALS[min(streak, len(SRS_INTERVALS)) - 1]
    due = last_day + timedelta(days=interval)
    return {"due": due, "box": streak, "overdue_days": max(0, (today - due).days)}


# ===========================================================================
# StudentStore (SQLite) — students + questions + attempts + exams
# ===========================================================================
class StudentStore:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    # -- schema --
    def _create_tables(self):
        with self._lock:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE, note TEXT,
                    is_active INTEGER DEFAULT 0, created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course TEXT, topic TEXT, difficulty TEXT DEFAULT 'Medium',
                    question_text TEXT, answer_text TEXT,
                    source_pdf TEXT, page_number INTEGER, tags TEXT,
                    image_path TEXT, source_pack TEXT, license_text TEXT, lang TEXT,
                    choices TEXT, correct_choice TEXT,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER, student_id INTEGER,
                    status TEXT DEFAULT 'unsolved', user_answer TEXT,
                    is_correct INTEGER DEFAULT 0, duration_sec INTEGER DEFAULT 0,
                    note TEXT, attempted_at TEXT
                );
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER, title TEXT, course TEXT, topic TEXT,
                    question_count INTEGER DEFAULT 0, correct_count INTEGER DEFAULT 0,
                    score REAL DEFAULT 0, duration_sec INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active', created_at TEXT, finished_at TEXT
                );
                CREATE TABLE IF NOT EXISTS exam_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER, question_id INTEGER, order_index INTEGER DEFAULT 0,
                    user_answer TEXT, is_correct INTEGER DEFAULT 0,
                    duration_sec INTEGER DEFAULT 0, answered_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_attempts_q ON attempts(question_id);
                CREATE INDEX IF NOT EXISTS idx_attempts_s ON attempts(student_id);
                CREATE INDEX IF NOT EXISTS idx_exam_items_e ON exam_items(exam_id);
                """
            )
            self._migrate()
            self.conn.commit()

    def _ensure_columns(self, table, columns):
        existing = {r["name"] for r in self.conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, ddl in columns.items():
            if name in existing:
                continue
            try:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
            except sqlite3.OperationalError as exc:
                if "duplicate column" not in str(exc).lower():
                    raise

    def _migrate(self):
        """Safe/idempotent — re-running never raises and never drops data."""
        self._ensure_columns("students", {"name": "TEXT", "note": "TEXT",
                                          "is_active": "INTEGER DEFAULT 0", "created_at": "TEXT"})
        self._ensure_columns("questions", {
            "course": "TEXT", "topic": "TEXT", "difficulty": "TEXT DEFAULT 'Medium'",
            "question_text": "TEXT", "answer_text": "TEXT", "source_pdf": "TEXT",
            "page_number": "INTEGER", "tags": "TEXT", "image_path": "TEXT",
            "source_pack": "TEXT", "license_text": "TEXT", "lang": "TEXT",
            "choices": "TEXT", "correct_choice": "TEXT",
            "created_at": "TEXT", "updated_at": "TEXT"})
        self._ensure_columns("attempts", {
            "question_id": "INTEGER", "student_id": "INTEGER", "status": "TEXT DEFAULT 'unsolved'",
            "user_answer": "TEXT", "is_correct": "INTEGER DEFAULT 0",
            "duration_sec": "INTEGER DEFAULT 0", "note": "TEXT", "attempted_at": "TEXT"})
        self._ensure_columns("exams", {
            "student_id": "INTEGER", "title": "TEXT", "course": "TEXT", "topic": "TEXT",
            "question_count": "INTEGER DEFAULT 0", "correct_count": "INTEGER DEFAULT 0",
            "score": "REAL DEFAULT 0", "duration_sec": "INTEGER DEFAULT 0",
            "status": "TEXT DEFAULT 'active'", "created_at": "TEXT", "finished_at": "TEXT",
            # Sureli miydi? VARSAYILANI YOK (NULL) — eski sinavlarda bunu
            # GERCEKTEN bilmiyoruz; 0 yazmak "suresizdi" demek olurdu.
            # NULL -> arayuzde "?", 0 -> "süresiz", >0 -> dakika.
            "time_limit_sec": "INTEGER"})
        self._ensure_columns("exam_items", {
            "exam_id": "INTEGER", "question_id": "INTEGER", "order_index": "INTEGER DEFAULT 0",
            "user_answer": "TEXT", "is_correct": "INTEGER DEFAULT 0",
            "duration_sec": "INTEGER DEFAULT 0", "answered_at": "TEXT"})

    # -- students --
    def add_student(self, name, note=""):
        name = (name or "").strip()
        if not name:
            return None
        with self._lock:
            row = self.conn.execute("SELECT id FROM students WHERE name=?", (name,)).fetchone()
            if row:
                return row["id"]
            cur = self.conn.execute(
                "INSERT INTO students (name, note, is_active, created_at) VALUES (?,?,0,?)",
                (name, note, _now()))
            self.conn.commit()
            sid = cur.lastrowid
            if not self.active_student():
                self.set_active_student(sid)
            return sid

    def list_students(self):
        with self._lock:
            return self.conn.execute("SELECT * FROM students ORDER BY name").fetchall()

    def get_student(self, student_id):
        with self._lock:
            return self.conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()

    def set_active_student(self, student_id):
        with self._lock:
            self.conn.execute("UPDATE students SET is_active=0")
            self.conn.execute("UPDATE students SET is_active=1 WHERE id=?", (student_id,))
            self.conn.commit()
            return True

    def active_student(self):
        with self._lock:
            return self.conn.execute("SELECT * FROM students WHERE is_active=1 LIMIT 1").fetchone()

    def delete_student(self, student_id):
        """Erase a learner and EVERYTHING recorded about them.

        `exam_items` has no student_id column and is reachable only through
        `exams.id`, so it must be deleted BEFORE the exams rows disappear —
        otherwise every typed answer, correctness flag and timestamp of that
        learner is retained forever with no path left to reach or purge it.
        That was a real right-to-erasure defect (GDPR Art. 17 / KVKK m.7);
        `delete_question` and `delete_by_pack` already did it correctly.

        Returns a dict of row counts so a caller (and the test suite) can
        prove the erasure actually happened.
        """
        with self._lock:
            silinen = {}
            cur = self.conn.execute(
                "DELETE FROM exam_items WHERE exam_id IN "
                "(SELECT id FROM exams WHERE student_id=?)", (student_id,))
            silinen["exam_items"] = cur.rowcount
            for tablo in ("attempts", "exams"):
                cur = self.conn.execute(
                    "DELETE FROM %s WHERE student_id=?" % tablo, (student_id,))  # nosec B608 - tablo comes from the literal tuple above
                silinen[tablo] = cur.rowcount
            cur = self.conn.execute("DELETE FROM students WHERE id=?", (student_id,))
            silinen["students"] = cur.rowcount
            self.conn.commit()
            self.last_erasure = silinen
            return True

    def ensure_default_student(self):
        act = self.active_student()
        if act:
            return act["id"]
        rows = self.list_students()
        if rows:
            self.set_active_student(rows[0]["id"])
            return rows[0]["id"]
        return self.add_student("Öğrenci 1")

    # -- questions --
    def add_question(self, question_text, answer_text="", course="", topic="",
                     difficulty="Medium", source_pdf="", page_number=0, tags="",
                     image_path="", source_pack="", license_text="", lang="",
                     choices=None, correct_choice=""):
        """`choices` is a list of option texts (A..E order) for multiple-choice
        questions; `correct_choice` is the letter ('A'..'E'). Image-only
        questions (cropped from a PDF) may pass a placeholder question_text."""
        question_text = (question_text or "").strip()
        if not question_text:
            return None
        choices_json = ""
        if choices:
            try:
                cleaned = [str(c).strip() for c in choices]
                while cleaned and not cleaned[-1]:
                    cleaned.pop()
                if cleaned:
                    choices_json = json.dumps(cleaned, ensure_ascii=False)
            except Exception:
                choices_json = ""
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO questions (course, topic, difficulty, question_text, answer_text, "
                "source_pdf, page_number, tags, image_path, source_pack, license_text, lang, "
                "choices, correct_choice, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (course, topic, difficulty or "Medium", question_text, answer_text,
                 source_pdf, int(page_number or 0), tags, image_path,
                 source_pack, license_text, lang, choices_json,
                 (correct_choice or "").strip().upper()[:1], _now(), _now()))
            self.conn.commit()
            return cur.lastrowid

    @staticmethod
    def parse_choices(row):
        """Choices list from a question row ([] when not multiple-choice)."""
        try:
            raw = row["choices"]
        except Exception:
            raw = None
        if not raw:
            return []
        try:
            out = json.loads(raw)
            return [str(c) for c in out] if isinstance(out, list) else []
        except Exception:
            return []

    def update_question(self, question_id, **fields):
        allowed = ("course", "topic", "difficulty", "question_text", "answer_text",
                   "source_pdf", "page_number", "tags", "image_path",
                   "choices", "correct_choice")
        sets, vals = [], []
        for k, v in fields.items():
            if k in allowed:
                sets.append(f"{k}=?")
                vals.append(v)
        if not sets:
            return False
        sets.append("updated_at=?")
        vals.append(_now())
        vals.append(question_id)
        with self._lock:
            cur = self.conn.execute(f"UPDATE questions SET {', '.join(sets)} WHERE id=?", vals)  # nosec B608 - keys filtered against `allowed` above; values bound
            self.conn.commit()
            return cur.rowcount > 0

    def delete_question(self, question_id):
        with self._lock:
            cur = self.conn.execute("DELETE FROM questions WHERE id=?", (question_id,))
            self.conn.execute("DELETE FROM attempts WHERE question_id=?", (question_id,))
            self.conn.execute("DELETE FROM exam_items WHERE question_id=?", (question_id,))
            self.conn.commit()
            return cur.rowcount > 0

    def get_question(self, question_id):
        with self._lock:
            return self.conn.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()

    def count_questions(self):
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) c FROM questions").fetchone()["c"]

    def distinct_values(self, column):
        if column not in ("course", "topic", "difficulty", "source_pack", "lang"):
            return []
        with self._lock:
            rows = self.conn.execute(
                f"SELECT DISTINCT {column} v FROM questions WHERE {column} IS NOT NULL "  # nosec B608 - column checked against an explicit allowlist above
                f"AND {column}!='' ORDER BY {column}").fetchall()
            return [r["v"] for r in rows]

    def status_map(self, student_id):
        """{question_id: latest status} for one student."""
        with self._lock:
            rows = self.conn.execute(
                "SELECT question_id, status FROM attempts WHERE student_id=? ORDER BY id ASC",
                (student_id,)).fetchall()
        out = {}
        for r in rows:                      # later rows overwrite -> latest wins
            out[r["question_id"]] = r["status"]
        return out

    def list_questions(self, student_id=None, course=None, topic=None, difficulty=None,
                       status=None, query=None, limit=1000, source_pack=None, lang=None):
        sql = "SELECT * FROM questions WHERE 1=1"
        params = []
        for col, val in (("course", course), ("topic", topic), ("difficulty", difficulty),
                         ("source_pack", source_pack), ("lang", lang)):
            if val:
                sql += f" AND {col}=?"
                params.append(val)
        if query:
            sql += " AND (question_text LIKE ? OR answer_text LIKE ? OR tags LIKE ?)"
            like = f"%{query}%"
            params += [like, like, like]
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(int(limit))
        with self._lock:
            rows = self.conn.execute(sql, params).fetchall()
        if not status or student_id is None:
            return rows
        smap = self.status_map(student_id)
        return [r for r in rows if smap.get(r["id"], "unsolved") == status]

    def delete_by_pack(self, source_pack):
        """Remove every question imported from one pack (+ its attempts/exam items)."""
        with self._lock:
            ids = [r["id"] for r in self.conn.execute(
                "SELECT id FROM questions WHERE source_pack=?", (source_pack,)).fetchall()]
            if not ids:
                return 0
            marks = ",".join("?" * len(ids))
            self.conn.execute(f"DELETE FROM attempts WHERE question_id IN ({marks})", ids)  # nosec B608 - marks is a run of "?"; ids are bound
            self.conn.execute(f"DELETE FROM exam_items WHERE question_id IN ({marks})", ids)  # nosec B608 - marks is a run of "?"; ids are bound
            cur = self.conn.execute("DELETE FROM questions WHERE source_pack=?", (source_pack,))
            self.conn.commit()
            return cur.rowcount

    def pack_summary(self):
        """[{source_pack, license_text, count}] for the imported packs."""
        with self._lock:
            rows = self.conn.execute(
                "SELECT COALESCE(source_pack,'') p, COALESCE(license_text,'') l, COUNT(*) c "
                "FROM questions GROUP BY p, l ORDER BY c DESC").fetchall()
        return [{"source_pack": r["p"] or "(manuel)", "license_text": r["l"], "count": r["c"]}
                for r in rows]

    # -- attempts --
    def record_attempt(self, question_id, student_id, status, user_answer="",
                       is_correct=None, duration_sec=0, note=""):
        if status not in STATUSES:
            status = "unsolved"
        if is_correct is None:
            is_correct = 1 if status == "solved" else 0
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO attempts (question_id, student_id, status, user_answer, is_correct, "
                "duration_sec, note, attempted_at) VALUES (?,?,?,?,?,?,?,?)",
                (question_id, student_id, status, user_answer, int(bool(is_correct)),
                 int(duration_sec or 0), note, _now()))
            self.conn.commit()
            return cur.lastrowid

    def question_status(self, question_id, student_id):
        with self._lock:
            row = self.conn.execute(
                "SELECT status FROM attempts WHERE question_id=? AND student_id=? "
                "ORDER BY id DESC LIMIT 1", (question_id, student_id)).fetchone()
        return row["status"] if row else "unsolved"

    def attempt_history(self, student_id):
        """{question_id: [(status, attempted_at), ...]} oldest→newest, one student."""
        with self._lock:
            rows = self.conn.execute(
                "SELECT question_id, status, attempted_at FROM attempts "
                "WHERE student_id=? ORDER BY id ASC", (student_id,)).fetchall()
        out = {}
        for r in rows:
            out.setdefault(r["question_id"], []).append((r["status"], r["attempted_at"]))
        return out

    def list_attempts(self, student_id, limit=200):
        with self._lock:
            return self.conn.execute(
                "SELECT a.*, q.question_text, q.course, q.topic FROM attempts a "
                "LEFT JOIN questions q ON q.id=a.question_id WHERE a.student_id=? "
                "ORDER BY a.id DESC LIMIT ?", (student_id, limit)).fetchall()

    # -- exams --
    def create_exam(self, student_id, title, course="", topic=""):
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO exams (student_id, title, course, topic, status, created_at) "
                "VALUES (?,?,?,?,'active',?)", (student_id, title, course, topic, _now()))
            self.conn.commit()
            return cur.lastrowid

    def add_exam_item(self, exam_id, question_id, order_index):
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO exam_items (exam_id, question_id, order_index) VALUES (?,?,?)",
                (exam_id, question_id, int(order_index)))
            self.conn.execute("UPDATE exams SET question_count=question_count+1 WHERE id=?", (exam_id,))
            self.conn.commit()
            return cur.lastrowid

    def answer_exam_item(self, exam_id, question_id, user_answer, is_correct, duration_sec=0):
        with self._lock:
            self.conn.execute(
                "UPDATE exam_items SET user_answer=?, is_correct=?, duration_sec=?, answered_at=? "
                "WHERE exam_id=? AND question_id=?",
                (user_answer, int(bool(is_correct)), int(duration_sec or 0), _now(), exam_id, question_id))
            self.conn.commit()
            return True

    def exam_items(self, exam_id):
        with self._lock:
            return self.conn.execute(
                "SELECT ei.*, q.question_text, q.answer_text, q.course, q.topic, q.difficulty, "
                "q.choices, q.correct_choice, q.image_path "
                "FROM exam_items ei LEFT JOIN questions q ON q.id=ei.question_id "
                "WHERE ei.exam_id=? ORDER BY ei.order_index ASC", (exam_id,)).fetchall()

    def finish_exam(self, exam_id, duration_sec=0):
        with self._lock:
            # COUNT(answered_at): gercekten isaretlenen soru sayisi — Atla ile
            # gecilen ya da sure asiminda kalan sorular answered_at NULL kalir
            # (skor paydasi yine TUM sorulardir; cevaplanmayan yanlis sayilir).
            row = self.conn.execute(
                "SELECT COUNT(*) n, COALESCE(SUM(is_correct),0) c, COUNT(answered_at) a "
                "FROM exam_items WHERE exam_id=?",
                (exam_id,)).fetchone()
            n, c, a = int(row["n"] or 0), int(row["c"] or 0), int(row["a"] or 0)
            score = round((c / n) * 100.0, 1) if n else 0.0
            self.conn.execute(
                "UPDATE exams SET status='finished', correct_count=?, score=?, duration_sec=?, "
                "finished_at=? WHERE id=?", (c, score, int(duration_sec or 0), _now(), exam_id))
            self.conn.commit()
            return {"question_count": n, "correct_count": c, "score": score, "answered_count": a}

    def get_exam(self, exam_id):
        with self._lock:
            return self.conn.execute("SELECT * FROM exams WHERE id=?", (exam_id,)).fetchone()

    def set_exam_time_limit(self, exam_id, seconds):
        """Sınavın süre sınırını kaydeder (0 = süresiz). Bilinmeyen = dokunma."""
        with self._lock:
            self.conn.execute("UPDATE exams SET time_limit_sec=? WHERE id=?",
                              (int(seconds or 0), exam_id))
            self.conn.commit()
        return True

    def exam_detail(self, exam_id):
        """Bir sınavın soru dökümü: soru metni + verilen cevap + doğru mu + süre."""
        with self._lock:
            return self.conn.execute(
                "SELECT ei.order_index, ei.question_id, ei.user_answer, ei.is_correct, "
                "       ei.duration_sec, ei.answered_at, "
                "       q.question_text, q.answer_text, q.course, q.topic, q.difficulty "
                "FROM exam_items ei LEFT JOIN questions q ON q.id = ei.question_id "
                "WHERE ei.exam_id=? ORDER BY ei.order_index ASC", (exam_id,)).fetchall()

    def attempts_between(self, student_id, start_day, end_day):
        """[gün, durum, kurs, konu, süre] — [start_day, end_day] ARALIĞI DÂHİL.

        Tarihler 'YYYY-MM-DD'; attempted_at 'YYYY-MM-DD HH:MM:SS' olduğu için
        gün karşılaştırması substr ile yapılır (indeks kaybı önemsiz, tablo küçük).
        """
        with self._lock:
            return self.conn.execute(
                "SELECT substr(a.attempted_at,1,10) gun, a.status, a.is_correct, "
                "       a.duration_sec, q.course, q.topic "
                "FROM attempts a LEFT JOIN questions q ON q.id = a.question_id "
                "WHERE a.student_id=? AND substr(a.attempted_at,1,10) BETWEEN ? AND ? "
                "ORDER BY a.id ASC",
                (student_id, str(start_day), str(end_day))).fetchall()

    def list_exams(self, student_id, limit=50):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM exams WHERE student_id=? ORDER BY id DESC LIMIT ?",
                (student_id, limit)).fetchall()

    # -- export --
    def export_questions_csv(self, path):
        rows = self.list_questions(limit=100000)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["id", "course", "topic", "difficulty", "question", "answer",
                        "source_pdf", "page", "tags"])
            for r in rows:
                w.writerow([r["id"], r["course"], r["topic"], r["difficulty"],
                            r["question_text"], r["answer_text"], r["source_pdf"],
                            r["page_number"], r["tags"]])
        return len(rows)


# ===========================================================================
# QuestionBank — bulk import helpers
# ===========================================================================
class QuestionBank:
    def __init__(self, store):
        self.store = store

    def import_text_block(self, text, course="", topic="", difficulty="Medium",
                          source_pdf="", page_number=0):
        """Import 'question = answer' (or 'question | answer') lines, one per row.

        Blank lines are skipped. A line with no separator becomes a question with
        an empty answer. Returns the number of imported questions.
        """
        added = 0
        for raw in str(text or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            q, a = line, ""
            for sep in ("|", "=>", "=", ";"):
                if sep in line:
                    q, a = line.split(sep, 1)
                    break
            qid = self.store.add_question(q.strip(), a.strip(), course=course, topic=topic,
                                          difficulty=difficulty, source_pdf=source_pdf,
                                          page_number=page_number)
            if qid:
                added += 1
        return added

    def import_csv(self, path, course="", topic=""):
        added = 0
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    q = (row.get("question") or row.get("question_text") or "").strip()
                    if not q:
                        continue
                    if self.store.add_question(
                            q, (row.get("answer") or row.get("answer_text") or "").strip(),
                            course=(row.get("course") or course).strip(),
                            topic=(row.get("topic") or topic).strip(),
                            difficulty=(row.get("difficulty") or "Medium").strip() or "Medium",
                            source_pdf=(row.get("source_pdf") or "").strip(),
                            page_number=int(row.get("page") or 0 or 0),
                            tags=(row.get("tags") or "").strip()):
                        added += 1
        except Exception:
            return added
        return added


# ===========================================================================
# ExamEngine — build / run / grade a test
# ===========================================================================
class ExamEngine:
    def __init__(self, store):
        self.store = store

    def build(self, student_id, title="", course="", topic="", difficulty="",
              count=10, only_status=None, shuffle=True, question_ids=None):
        """Create an exam from the bank. `only_status` e.g. 'unsolved' or 'wrong'
        makes a targeted drill; `question_ids` builds from an explicit list (used
        by the spaced-repetition drill). Returns (exam_id, items) or (None, [])."""
        if question_ids:
            pool = [self.store.get_question(qid) for qid in question_ids]
            pool = [p for p in pool if p is not None]
        else:
            pool = self.store.list_questions(student_id=student_id, course=course or None,
                                             topic=topic or None, difficulty=difficulty or None,
                                             status=only_status or None, limit=100000)
        pool = list(pool)
        if not pool:
            return None, []
        if shuffle:
            random.shuffle(pool)
        pool = pool[:max(1, int(count or 1))]
        exam_id = self.store.create_exam(student_id, title or f"Test {_today()}", course, topic)
        for i, q in enumerate(pool):
            self.store.add_exam_item(exam_id, q["id"], i)
        return exam_id, self.store.exam_items(exam_id)

    def answer(self, exam_id, question_id, student_id, user_answer, is_correct, duration_sec=0):
        """Record one exam answer AND the matching bank attempt (so the question's
        solved/wrong status stays in sync with the test result)."""
        self.store.answer_exam_item(exam_id, question_id, user_answer, is_correct, duration_sec)
        self.store.record_attempt(question_id, student_id,
                                  "solved" if is_correct else "wrong",
                                  user_answer=user_answer, is_correct=is_correct,
                                  duration_sec=duration_sec, note=f"exam:{exam_id}")
        return True

    def finish(self, exam_id, duration_sec=0):
        return self.store.finish_exam(exam_id, duration_sec)


# ===========================================================================
# ProgressAnalytics — the numbers behind the tracking panel
# ===========================================================================
class ProgressAnalytics:
    def __init__(self, store):
        self.store = store

    def overview(self, student_id):
        total = self.store.count_questions()
        smap = self.store.status_map(student_id)
        solved = sum(1 for v in smap.values() if v == "solved")
        wrong = sum(1 for v in smap.values() if v == "wrong")
        review = sum(1 for v in smap.values() if v == "review")
        attempted = len(smap)
        graded = solved + wrong
        exams = self.store.list_exams(student_id, limit=1000)
        finished = [e for e in exams if e["status"] == "finished"]
        avg = round(sum(float(e["score"] or 0) for e in finished) / len(finished), 1) if finished else 0.0
        return {
            "total_questions": total,
            "attempted": attempted,
            "solved": solved,
            "wrong": wrong,
            "review": review,
            "unsolved": max(0, total - attempted),
            "accuracy": round((solved / graded) * 100.0, 1) if graded else 0.0,
            "exams": len(finished),
            "avg_score": avg,
        }

    def by_topic(self, student_id):
        smap = self.store.status_map(student_id)
        rows = self.store.list_questions(limit=100000)
        agg = {}
        for r in rows:
            key = (r["course"] or "-", r["topic"] or "-")
            d = agg.setdefault(key, {"total": 0, "solved": 0, "wrong": 0})
            d["total"] += 1
            st = smap.get(r["id"])
            if st == "solved":
                d["solved"] += 1
            elif st == "wrong":
                d["wrong"] += 1
        out = []
        for (course, topic), d in agg.items():
            graded = d["solved"] + d["wrong"]
            out.append({
                "course": course, "topic": topic, "total": d["total"],
                "solved": d["solved"], "wrong": d["wrong"],
                "accuracy": round((d["solved"] / graded) * 100.0, 1) if graded else 0.0,
                "graded": graded,
            })
        out.sort(key=lambda x: (-x["total"], x["course"], x["topic"]))
        return out

    def weak_topics(self, student_id, limit=5, min_graded=1):
        rows = [r for r in self.by_topic(student_id) if r["graded"] >= min_graded]
        rows.sort(key=lambda x: (x["accuracy"], -x["wrong"]))
        return rows[:limit]

    def due_questions(self, student_id, today=None, include_upcoming_days=0):
        """Spaced-repetition queue: questions whose review date has arrived.

        Returns [{question_id, due, box, overdue_days, course, topic, status}]
        sorted most-overdue first. `include_upcoming_days=N` also returns the
        ones due within the next N days (overdue_days will be 0 for those)."""
        today = today or date.today()
        history = self.store.attempt_history(student_id)
        if not history:
            return []
        qmeta = {r["id"]: r for r in self.store.list_questions(limit=100000)}
        out = []
        for qid, hist in history.items():
            sched = srs_schedule(hist, today=today)
            if sched is None or qid not in qmeta:
                continue
            if sched["due"] > today + timedelta(days=max(0, int(include_upcoming_days))):
                continue
            r = qmeta[qid]
            out.append({"question_id": qid, "due": sched["due"], "box": sched["box"],
                        "overdue_days": sched["overdue_days"],
                        "course": r["course"] or "-", "topic": r["topic"] or "-",
                        "status": hist[-1][0]})
        out.sort(key=lambda x: (-x["overdue_days"], x["box"], x["question_id"]))
        return out

    def due_summary(self, student_id, today=None):
        """Counts for the dashboard: due now / due within a week / per-course."""
        today = today or date.today()
        due_now = self.due_questions(student_id, today=today)
        week = self.due_questions(student_id, today=today, include_upcoming_days=7)
        return {
            "due_now": len(due_now),
            "due_week": len(week),
            "due_ids": [d["question_id"] for d in due_now],
        }

    def course_progress(self, student_id):
        """[{course, total, solved, percent}] — how much of each course's bank
        the student has actually solved (latest status wins)."""
        smap = self.store.status_map(student_id)
        rows = self.store.list_questions(limit=100000)
        agg = {}
        for r in rows:
            key = r["course"] or "-"
            d = agg.setdefault(key, {"total": 0, "solved": 0})
            d["total"] += 1
            if smap.get(r["id"]) == "solved":
                d["solved"] += 1
        out = [{"course": c, "total": d["total"], "solved": d["solved"],
                "percent": round(d["solved"] * 100.0 / d["total"], 1) if d["total"] else 0.0}
               for c, d in agg.items()]
        out.sort(key=lambda x: (-x["total"], x["course"]))
        return out


# ===========================================================================
# StudyAdvisor — "📌 Bu Hafta" önerileri (kural tabanlı, AI ÇAĞRISI YOK)
# ===========================================================================
#
# Neden AI yok: bu kart Bugün panosunun içinde duruyor ve pano ANINDA açılmak
# zorunda. Bir LM Studio çağrısı (soğuk başlangıçta saniyeler) panoyu bekletir,
# LM kapalıyken de kartı boş bırakırdı. Kurallar veriyi doğrudan okur.
#
# Neden bu üç kural: elde biriken veri tam olarak bunları söyleyebiliyor —
# neyi yanlış yapıyorsun (konu doğruluğu), neyi bıraktın (kurs sessizliği),
# neyin üstüne yığılıyor (tekrar kuyruğu). Bunların dışına çıkmak tahmin
# üretmek olurdu; veri yetmiyorsa motor SUSAR ve nedenini söyler.
ZAYIF_DOGRULUK = 60.0     # bu yüzdenin ALTI zayıf sayılır
ZAYIF_MIN_DENEME = 5      # en az bu kadar puanlanmış DENEME olmadan konuşma
IHMAL_GUN = 7             # bu kadar gündür dokunulmamış kurs "ihmal" sayılır
YIGILMA_ESIK = 12         # tek güne bu kadar tekrar düşerse yığılma denir
ONERI_SAYISI = 3          # panoda gösterilecek en fazla öneri


class StudyAdvisor:
    """Denemeler ve tekrar kuyruğundan kural tabanlı çalışma önerileri üretir.

    Tkinter'sız: panel bunu yalnızca çağırır. `suggest()` her zaman
    {"oneriler": [...], "mesaj": "..."} döndürür; öneri üretilemediğinde liste
    boştur ve `mesaj` NEDENİNİ söyler — "veri yok" ile "her şey yolunda"
    aynı şey değildir.
    """

    def __init__(self, store, analytics=None, lang="tr"):
        self.store = store
        self.stats = analytics or ProgressAnalytics(store)
        # Oneri METINLERI iki dilli: motor Tk'siz oldugu icin dili disaridan alir.
        self.lang = "en" if str(lang).lower().startswith("en") else "tr"

    def _t(self, tr, en):
        return t2(tr, en, self.lang)

    # ---------------------------------------------------------- yardımcı --
    @staticmethod
    def _gun(stamp):
        try:
            return datetime.strptime(str(stamp)[:10], "%Y-%m-%d").date()
        except Exception:
            return None

    def _deneme_dokumu(self, student_id):
        """(konu_bazli, kurs_son_gun, toplam_puanli_deneme).

        konu_bazli: {(course, topic): {"dogru", "yanlis", "toplam", "qids"}}
        kurs_son_gun: {course: en son deneme tarihi}
        Yalnızca PUANLANMIŞ denemeler (solved/wrong) doğruluğa katılır;
        "review"/"unsolved" işaretleri bir bilgi taşımaz, orana sokulmaz.
        """
        gecmis = self.store.attempt_history(student_id)
        qmeta = {r["id"]: r for r in self.store.list_questions(limit=100000)}
        konu, kurs_gun, toplam = {}, {}, 0
        for qid, denemeler in gecmis.items():
            r = qmeta.get(qid)
            if r is None:
                continue                        # silinmiş soru: sessizce atla
            course = r["course"] or "-"
            topic = r["topic"] or "-"
            d = konu.setdefault((course, topic),
                                {"dogru": 0, "yanlis": 0, "toplam": 0, "qids": []})
            d["qids"].append(qid)
            for status, stamp in denemeler:
                gun = self._gun(stamp)
                if gun and (course not in kurs_gun or gun > kurs_gun[course]):
                    kurs_gun[course] = gun
                if status == "solved":
                    d["dogru"] += 1
                    d["toplam"] += 1
                    toplam += 1
                elif status == "wrong":
                    d["yanlis"] += 1
                    d["toplam"] += 1
                    toplam += 1
        return konu, kurs_gun, toplam

    # ------------------------------------------------------------ kurallar --
    def zayif_konular(self, student_id, konu_dokumu=None):
        """(a) Doğruluğu eşiğin altında VE yeterli denemesi olan konular."""
        konu = konu_dokumu if konu_dokumu is not None else \
            self._deneme_dokumu(student_id)[0]
        out = []
        for (course, topic), d in konu.items():
            if d["toplam"] < ZAYIF_MIN_DENEME:
                continue                        # az veriden oran uydurma
            oran = round(d["dogru"] * 100.0 / d["toplam"], 1)
            if oran >= ZAYIF_DOGRULUK:
                continue
            out.append({
                "tur": "zayif_konu", "kurs": course, "konu": topic,
                "baslik": topic if topic != "-" else course,
                "dogruluk": oran, "deneme": d["toplam"], "qids": sorted(d["qids"]),
                "gerekce": self._t(f"son {d['toplam']} denemede %{oran:g} doğruluk",
                            f"{oran:g}% correct over the last {d['toplam']} attempts"),
                "eylem": "sinav_konu",
                "eylem_metni": self._t("→ Bu konudan 10 soruluk sınav",
                                 "→ 10-question exam on this topic"),
                "oncelik": 100 + (ZAYIF_DOGRULUK - oran),
            })
        out.sort(key=lambda x: (x["dogruluk"], -x["deneme"]))
        return out

    def ihmal_edilen_kurslar(self, student_id, today=None, kurs_gun=None):
        """(b) IHMAL_GUN gündür hiç denenmemiş — ama daha önce çalışılmış kurslar.

        HİÇ denenmemiş kurslar buraya girmez: onlar zaten panonun "🆕
        Denenmemiş" kartının işi ve "bıraktığın kurs" demek yanlış olurdu.
        """
        today = today or date.today()
        if kurs_gun is None:
            kurs_gun = self._deneme_dokumu(student_id)[1]
        out = []
        for course, gun in kurs_gun.items():
            bosluk = (today - gun).days
            if bosluk < IHMAL_GUN:
                continue
            out.append({
                "tur": "ihmal_edilen_kurs", "kurs": course, "konu": "",
                "baslik": course, "gun": bosluk, "son_gun": gun.isoformat(),
                "gerekce": self._t(f"{bosluk} gündür hiç soru çözmedin (son: {gun.isoformat()})",
                            f"{bosluk} days without a single question (last: {gun.isoformat()})"),
                "eylem": "kursa_devam",
                "eylem_metni": self._t("→ Kursa devam et", "→ Continue the course"),
                "oncelik": 50 + min(30, bosluk),
            })
        out.sort(key=lambda x: -x["gun"])
        return out

    def tekrar_yigilmasi(self, student_id, today=None):
        """(c) Tekrar kuyruğunda tek güne yığılan sorular."""
        today = today or date.today()
        kuyruk = self.stats.due_questions(student_id, today=today,
                                          include_upcoming_days=7)
        if not kuyruk:
            return []
        gunler = {}
        for k in kuyruk:
            gunler.setdefault(k["due"], []).append(k["question_id"])
        yigin = [(g, ids) for g, ids in gunler.items() if len(ids) >= YIGILMA_ESIK]
        if not yigin:
            return []
        yigin.sort(key=lambda x: (-len(x[1]), x[0]))
        gun, ids = yigin[0]
        ne_zaman = self._t("bugün", "today") if gun <= today else gun.isoformat()
        return [{
            "tur": "tekrar_yigilmasi", "kurs": "", "konu": "",
            "baslik": self._t("Tekrar yığılması", "Review pile-up"), "gun_str": ne_zaman, "adet": len(ids),
            "qids": sorted(ids),
            "gerekce": self._t(
                f"{len(ids)} soru {ne_zaman} tekrar vaktine geliyor — bir kısmını öne al",
                f"{len(ids)} questions come up for review {ne_zaman} — pull some forward"),
            "eylem": "sinav_tekrar",
            "eylem_metni": self._t("→ 10 soruluk tekrar sınavı", "→ 10-question review exam"),
            "oncelik": 90 + min(30, len(ids)),
        }]

    # -------------------------------------------------------------- birleşik --
    def suggest(self, student_id, today=None, limit=ONERI_SAYISI):
        """{"oneriler": [...en fazla `limit`...], "mesaj": "..."}."""
        today = today or date.today()
        konu, kurs_gun, puanli = self._deneme_dokumu(student_id)
        if puanli == 0:
            return {"oneriler": [], "mesaj": self._t(
                "Öneri için henüz yeterli veri yok — birkaç soru çözdükçe "
                "burada ne çalışman gerektiğini söyleyeceğim.",
                "Not enough data yet — solve a few questions and I will tell you "
                "what to work on here.")}

        zayif = self.zayif_konular(student_id, konu_dokumu=konu)
        ihmal = self.ihmal_edilen_kurslar(student_id, today=today, kurs_gun=kurs_gun)
        yigin = self.tekrar_yigilmasi(student_id, today=today)

        # Cesitlilik: uc zayif konu yerine uc FARKLI sinyal daha kullanisli.
        aday = zayif[:2] + ihmal[:1] + yigin[:1]
        aday.sort(key=lambda x: -x["oncelik"])
        aday = aday[:max(1, int(limit))]
        if not aday:
            return {"oneriler": [], "mesaj": self._t(
                f"Şu an öne çıkan bir zayıflık yok — {puanli} denemede konu "
                f"doğrulukların %{ZAYIF_DOGRULUK:g} eşiğinin üstünde, kurslara "
                f"son {IHMAL_GUN} gün içinde dokunmuşsun. Böyle devam. 🎉",
                f"No weak spot stands out — across {puanli} attempts your topic "
                f"accuracies are above the {ZAYIF_DOGRULUK:g}% threshold and you have "
                f"touched every course within {IHMAL_GUN} days. Keep it up. 🎉")}
        return {"oneriler": aday,
                "mesaj": self._t(f"{puanli} denemeden çıkarıldı · kural tabanlı, AI kullanılmadı",
                                  f"derived from {puanli} attempts · rule-based, no AI used")}


# ===========================================================================
# 📄 Haftalık Özet raporu — Tk'sız; education.py'nin sayfa şablonunu kullanır
# ===========================================================================
GUN_ADLARI = ("Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz")
RAPOR_MIN_DENEME = 3      # haftalık zayıf konu için en az bu kadar deneme


def _sure_metni(saniye):
    try:
        saniye = int(saniye or 0)
    except Exception:
        return "—"
    if saniye <= 0:
        return "—"
    dk, sn = divmod(saniye, 60)
    return f"{dk} dk {sn} sn" if dk else f"{sn} sn"


def sinav_sure_modu(row):
    """Sınavın süreli olup olmadığını DÜRÜSTÇE söyler.

    time_limit_sec sütunu V48'de eklendi: eski sınavlarda değeri NULL'dur ve
    o sınavların süreli olup olmadığı GERÇEKTEN bilinmiyor — '?' döner.
    """
    try:
        deger = row["time_limit_sec"]
    except Exception:
        deger = None
    if deger is None:
        return "?"
    try:
        deger = int(deger)
    except Exception:
        return "?"
    return f"{deger // 60} dk" if deger > 0 else "süresiz"


GUN_ADLARI_EN = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def haftalik_rapor_verisi(store, student_id, today=None, gun_sayisi=7, lang="tr"):
    """Haftalık raporun TÜM sayıları — Tk'sız, tek kaynak (rapor + testler).

    Aralık: [today - (gun_sayisi-1), today] (bugün dâhil). Karşılaştırma için
    bir önceki aynı uzunluktaki dönem de hesaplanır.
    """
    today = today or date.today()
    bas = today - timedelta(days=max(1, int(gun_sayisi)) - 1)
    onceki_bitis = bas - timedelta(days=1)
    onceki_bas = onceki_bitis - timedelta(days=max(1, int(gun_sayisi)) - 1)

    satirlar = store.attempts_between(student_id, bas.isoformat(), today.isoformat())
    onceki = store.attempts_between(student_id, onceki_bas.isoformat(),
                                    onceki_bitis.isoformat())

    def _dogruluk(rows):
        puanli = [r for r in rows if r["status"] in ("solved", "wrong")]
        if not puanli:
            return None, 0, 0
        dogru = sum(1 for r in puanli if r["status"] == "solved")
        return round(dogru * 100.0 / len(puanli), 1), dogru, len(puanli) - dogru

    dogruluk, dogru, yanlis = _dogruluk(satirlar)
    onceki_dogruluk, _, _ = _dogruluk(onceki)

    gunler = []
    for i in range(max(1, int(gun_sayisi))):
        g = bas + timedelta(days=i)
        gs = g.isoformat()
        gun_satir = [r for r in satirlar if r["gun"] == gs]
        gunler.append({
            "gun": gs,
            "ad": (GUN_ADLARI_EN if str(lang).lower().startswith("en")
                   else GUN_ADLARI)[g.weekday()],
            "deneme": len(gun_satir),
            "dogru": sum(1 for r in gun_satir if r["status"] == "solved"),
        })

    konu = {}
    for r in satirlar:
        if r["status"] not in ("solved", "wrong"):
            continue
        anahtar = (r["course"] or "-", r["topic"] or "-")
        d = konu.setdefault(anahtar, {"dogru": 0, "toplam": 0})
        d["toplam"] += 1
        if r["status"] == "solved":
            d["dogru"] += 1
    zayif = []
    for (kurs, kon), d in konu.items():
        if d["toplam"] < RAPOR_MIN_DENEME:
            continue          # 1-2 denemeden hafta yorumu cikarilmaz
        zayif.append({"kurs": kurs, "konu": kon, "deneme": d["toplam"],
                      "dogru": d["dogru"],
                      "dogruluk": round(d["dogru"] * 100.0 / d["toplam"], 1)})
    zayif.sort(key=lambda x: (x["dogruluk"], -x["deneme"]))

    sinavlar = []
    for e in store.list_exams(student_id, limit=500):
        if e["status"] != "finished":
            continue
        ts = (e["finished_at"] or e["created_at"] or "")[:10]
        if not (bas.isoformat() <= ts <= today.isoformat()):
            continue
        sinavlar.append({
            "tarih": ts, "baslik": e["title"] or "-",
            "soru": e["question_count"] or 0, "dogru": e["correct_count"] or 0,
            "puan": round(float(e["score"] or 0), 1),
            "sure": _sure_metni(e["duration_sec"]),
            "sure_modu": sinav_sure_modu(e),
        })
    sinavlar.sort(key=lambda x: x["tarih"])

    return {
        "baslangic": bas.isoformat(), "bitis": today.isoformat(),
        "gunler": gunler,
        "calisma_gunu": sum(1 for g in gunler if g["deneme"]),
        "gun_sayisi": len(gunler),
        "toplam_deneme": len(satirlar),
        "dogru": dogru, "yanlis": yanlis,
        "dogruluk": dogruluk,
        "onceki_dogruluk": onceki_dogruluk,
        "degisim": (None if (dogruluk is None or onceki_dogruluk is None)
                    else round(dogruluk - onceki_dogruluk, 1)),
        "zayif_konular": zayif,
        "sinavlar": sinavlar,
        "veri_var": bool(satirlar or sinavlar),
    }


def _r_kart(baslik, deger, alt=""):
    return ('<div style="flex:1;min-width:150px;border:1px solid var(--line);'
            'border-radius:10px;background:var(--soft);padding:12px 14px">'
            f'<div style="font-size:12px;color:var(--mut);font-weight:700">{baslik}</div>'
            f'<div style="font-size:26px;font-weight:700;line-height:1.2">{deger}</div>'
            f'<div style="font-size:12px;color:var(--mut)">{alt}</div></div>')


def _r_yok(metin="Bu hafta veri yok."):
    """Boş bölüm: grafik/tablo ÇİZİLMEZ, neden boş olduğu yazılır."""
    return f'<div class="note" style="background:#F6EFE4;border-color:#E4D7C4">{metin}</div>'


def haftalik_rapor_html(store, student_id, today=None, ogrenci_adi="",
                        gun_sayisi=7, veri=None, lang="tr"):
    """Tek sayfa HTML haftalık özet (Tkinter YOK) — tarayıcıda açılır/yazdırılır."""
    EN = str(lang).lower().startswith("en")

    def _r(tr, en):
        return en if EN else tr

    d = veri if veri is not None else haftalik_rapor_verisi(
        store, student_id, today=today, gun_sayisi=gun_sayisi, lang=lang)
    parcalar = []

    # -- özet kartları --
    dogruluk_metni = f"%{d['dogruluk']:g}" if d["dogruluk"] is not None else "—"
    if d["degisim"] is None:
        degisim_alt = ("önceki hafta verisi yok" if d["dogruluk"] is not None
                       else "puanlanmış deneme yok")
    else:
        ok = "▲" if d["degisim"] > 0 else ("▼" if d["degisim"] < 0 else "=")
        degisim_alt = f"geçen haftaya göre {ok} {abs(d['degisim']):g} puan"
    parcalar.append(
        '<div style="display:flex;gap:12px;flex-wrap:wrap;margin:14px 0">'
        + _r_kart(_r("Çalışma günü", "Study days"),
                  f"{d['calisma_gunu']}/{d['gun_sayisi']}",
                  _r("soru çözülen gün sayısı", "days with questions answered"))
        + _r_kart(_r("Çözülen soru", "Questions answered"), d["toplam_deneme"],
                  _r(f"{d['dogru']} doğru · {d['yanlis']} yanlış",
                     f"{d['dogru']} correct · {d['yanlis']} wrong"))
        + _r_kart("Doğruluk", dogruluk_metni, degisim_alt)
        + _r_kart("Sınav", len(d["sinavlar"]),
                  "bu hafta bitirilen sınav" if d["sinavlar"] else "bu hafta sınav yok")
        + '</div>')

    # -- günlük etkinlik (boşsa çizilmez) --
    parcalar.append(_h3_r(_r("Günlük etkinlik", "Daily activity"), "gunluk"))
    if d["toplam_deneme"]:
        en_yuksek = max(g["deneme"] for g in d["gunler"]) or 1
        cubuklar = ""
        for g in d["gunler"]:
            yuzde = int(round(g["deneme"] * 100.0 / en_yuksek))
            renk = "var(--green)" if g["deneme"] else "var(--line)"
            cubuklar += (
                '<div style="flex:1;text-align:center">'
                f'<div style="height:90px;display:flex;align-items:flex-end">'
                f'<div style="width:100%;height:{max(yuzde, 2)}%;background:{renk};'
                'border-radius:5px 5px 0 0"></div></div>'
                f'<div style="font-size:12px;margin-top:4px">{g["ad"]}</div>'
                f'<div style="font-size:11px;color:var(--mut)">{g["deneme"]}</div>'
                '</div>')
        parcalar.append('<div style="display:flex;gap:8px;align-items:flex-end;'
                        'border:1px solid var(--line);border-radius:10px;padding:12px">'
                        + cubuklar + '</div>')
    else:
        parcalar.append(_r_yok(_r("Bu hafta hiç soru çözülmemiş — grafik çizilmedi.",
                                  "No questions answered this week — no chart drawn.")))

    # -- zayıf konular --
    parcalar.append(_h3_r(_r("Bu haftanın zayıf konuları", "This week's weak topics"), "zayif"))
    if d["zayif_konular"]:
        parcalar.append(_tablo_r(
            _r(["Kurs", "Konu", "Deneme", "Doğru", "Doğruluk"],
               ["Course", "Topic", "Attempts", "Correct", "Accuracy"]),
            [[z["kurs"], z["konu"], z["deneme"], z["dogru"], f"%{z['dogruluk']:g}"]
             for z in d["zayif_konular"][:10]]))
    else:
        parcalar.append(_r_yok(_r(
            f"Bu hafta hiçbir konuda {RAPOR_MIN_DENEME} veya daha fazla puanlanmış "
            "deneme yok — az veriden konu yorumu çıkarılmadı.",
            f"No topic has {RAPOR_MIN_DENEME} or more graded attempts this week — no "
            "conclusions drawn from too little data.")))

    # -- sınavlar --
    parcalar.append(_h3_r(_r("Sınav sonuçları", "Exam results"), "sinav"))
    if d["sinavlar"]:
        parcalar.append(_tablo_r(
            _r(["Tarih", "Sınav", "Soru", "Doğru", "Puan", "Süre", "Süreli mi?"],
               ["Date", "Exam", "Questions", "Correct", "Score", "Time", "Timed?"]),
            [[s["tarih"], s["baslik"], s["soru"], s["dogru"], f"%{s['puan']:g}",
              s["sure"], s["sure_modu"]] for s in d["sinavlar"]]))
        if any(s["sure_modu"] == "?" for s in d["sinavlar"]):
            parcalar.append('<div style="font-size:12px;color:var(--mut)">'
                            + _r('“?” = bu sınav, süre bilgisi kaydedilmeye başlamadan '
                                 'önce yapılmış (V48 öncesi).',
                                 '“?” = this exam was taken before the timed/untimed flag '
                                 'was recorded (pre-V48).') + '</div>')
    else:
        parcalar.append(_r_yok(_r("Bu hafta bitirilmiş sınav yok.", "No exams finished this week.")))

    govde = ('<div class="wrap" style="grid-template-columns:1fr"><main class="content">'
             + "".join(parcalar)
             + '<div class="foot"><span class="dot"></span>'
             + _r('<span>Math Course AI — haftalık çalışma özeti.</span>'
                  '<span class="r">Sayılar yalnızca senin bilgisayarındaki '
                  'kayıtlardan üretildi.</span>',
                  '<span>Math Course AI — weekly study summary.</span>'
                  '<span class="r">Every number comes from records on your own '
                  'computer.</span>')
             + '</div></main></div>')
    ad = f"{ogrenci_adi} · " if ogrenci_adi else ""
    return _sayfa(_r(f"Haftalık Özet — {d['baslangic']} → {d['bitis']}",
                     f"Weekly Summary — {d['baslangic']} → {d['bitis']}"),
                  _r(f"{ad}{d['gun_sayisi']} günlük çalışma raporu. "
                     "Renkli ya da gri yazdırılabilir (A4).",
                     f"{ad}{d['gun_sayisi']}-day study report. Printable in colour or "
                     "grayscale (A4)."),
                  _r("HAFTALIK RAPOR", "WEEKLY REPORT"), govde, lang=lang)


def _h3_r(baslik, _id):
    return f'<h3 id="{_id}" style="margin-top:26px">{baslik}</h3>'


def _tablo_r(basliklar, satirlar):
    th = "".join(f"<th>{b}</th>" for b in basliklar)
    trs = "".join("<tr>" + "".join(f"<td>{h}</td>" for h in s) + "</tr>" for s in satirlar)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def _sayfa(baslik, alt, kicker, govde, lang="tr"):
    """education.sayfa_html'e köprü; modül yoksa iskelet HTML ile devam eder."""
    try:
        import education
        return education.sayfa_html(baslik, alt, kicker, govde, lang=lang)
    except Exception:
        return (f"<!DOCTYPE html><html lang='tr'><head><meta charset='utf-8'>"
                f"<title>{baslik}</title></head><body><h1>{baslik}</h1>"
                f"<p>{alt}</p>{govde}</body></html>")


def haftalik_rapor_ac(store, student_id, today=None, ogrenci_adi="", lang="tr"):
    """Raporu geçici dosyaya yazıp tarayıcıda açar → (ok, yol|hata)."""
    import tempfile
    import time as _time
    import webbrowser
    try:
        klasor = Path(tempfile.gettempdir()) / "MathCourseAI_Rapor"
        klasor.mkdir(parents=True, exist_ok=True)
        yol = klasor / ("haftalik_ozet_%d.html" % int(_time.time()))
        yol.write_text(haftalik_rapor_html(store, student_id, today=today,
                                           ogrenci_adi=ogrenci_adi, lang=lang),
                       encoding="utf-8")
        webbrowser.open("file:///" + str(yol).replace("\\", "/"))
        return True, str(yol)
    except Exception as exc:
        return False, str(exc)


# ===========================================================================
# Tk panel
# ===========================================================================
try:
    import question_packs as qpacks   # built-in generators + external open packs
except Exception:  # pragma: no cover
    qpacks = None

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except Exception:  # pragma: no cover
    tk = None

BG = "#FBF7F1"
PANEL_BG = "#FFFFFF"
FG = "#2B2620"
MUTED = "#8A7E6E"
ACCENT = "#E07B39"
GREEN = "#16A55A"
DANGER = "#C0392B"


def apply_dark_palette():
    """Ana uygulama karanlik temadayken panel kurulmadan ONCE cagrilir.

    Sabitler widget kurulumu sirasinda okundugu icin modul globallerini
    degistirmek yeterlidir (import aninda baska yapiya gomulmuyorlar)."""
    global BG, PANEL_BG, FG, MUTED, ACCENT, GREEN, DANGER, DARK_MODE
    DARK_MODE = True
    BG = "#2A241C"
    PANEL_BG = "#1B1712"
    FG = "#EDE5D8"
    MUTED = "#A6987F"
    ACCENT = "#E07B39"
    GREEN = "#2FBF71"
    DANGER = "#E25B4A"
STATUS_TR = {"unsolved": "Çözülmedi", "solved": "Çözdüm", "wrong": "Yanlış", "review": "Tekrar"}


class StudentTrackerPanel(ttk.Frame if tk is not None else object):
    """Öğrenci Takip: profiles, question bank, exams, analytics (4 sub-tabs)."""

    def __init__(self, parent, app, db_path=None):
        super().__init__(parent)
        self.app = app
        self.store = StudentStore(db_path)   # db_path=None -> the real DB_PATH
        self.bank = QuestionBank(self.store)
        self.exams = ExamEngine(self.store)
        self.stats = ProgressAnalytics(self.store)
        self.advisor = StudyAdvisor(self.store, self.stats, lang=app_lang(app))
        # Panel dili: sahibi uygulamadan okunur. Panel V48'de TEMBEL kurulduğu
        # için dil değişiminden SONRA açıldığında zaten yeni dille kurulur;
        # zaten kuruluysa ana uygulamanın "yeniden başlat" notu geçerlidir.
        self.lang = app_lang(app)
        self.student_id = self.store.ensure_default_student()
        self._q_rows = []
        self._sel_qid = None
        self._exam_id = None
        self._exam_items = []
        self._exam_idx = 0
        self._exam_started = None
        self._exam_deadline = None   # sureli sinav: bitis ani (None = suresiz)
        self._exam_timer_job = None  # geri sayim after() is kimligi
        self._build()

    # -- small helpers -------------------------------------------------- #
    def _t(self, tr, en):
        """Panel metni: dil, panel kurulurken sahibinden okunur (bkz. __init__)."""
        return t2(tr, en, getattr(self, "lang", "tr"))

    def _set_text(self, widget, content):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content or "")
        widget.config(state="disabled")

    def _status(self, label, msg, color=None):
        try:
            label.config(text=msg, fg=color or MUTED)
        except Exception:
            pass

    def _build(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self._build_dashboard_tab()
        self._build_student_tab()
        self._build_bank_tab()
        self._build_packs_tab()
        self._build_exam_tab()
        self._build_stats_tab()
        self.refresh_all()

    def refresh_all(self):
        for fn in (self._refresh_students, self._refresh_bank, self._refresh_filters,
                   self._refresh_packs, self._refresh_stats, self._refresh_dashboard):
            try:
                fn()
            except Exception:
                pass

    # ---- Tab 0: Bugün / Today — the daily study plan ---- #
    def _build_dashboard_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self._t("Bugün", "Today"))
        self.dash_tab = tab
        header = ttk.Frame(tab)
        header.pack(fill="x", padx=8, pady=(8, 0))
        self.dash_title = tk.Label(header, text=self._t("Bugün", "Today"), bg=BG, fg=FG,
                                   font=("Segoe UI Semibold", 13))
        self.dash_title.pack(side="left")
        ttk.Button(header, text=self._t("Yenile", "Refresh"), command=self.refresh_all).pack(side="right")
        self.dash_sub = tk.Label(tab, text="", bg=BG, fg=MUTED,
                                 font=("Segoe UI", 9), anchor="w")
        self.dash_sub.pack(fill="x", padx=8, pady=(0, 4))

        cards = ttk.Frame(tab)
        cards.pack(fill="x", padx=6, pady=4)
        self._dash_cards = {}
        specs = (
            ("due", "🔁 Tekrar vakti", ACCENT, "Tekrar Sınavı", lambda: self._start_drill("due")),
            ("wrong", "✘ Yanlışlar", DANGER, "Yanlış Drill", lambda: self._start_drill("wrong")),
            ("unsolved", "🆕 Denenmemiş", "#2563EB", "Yeni Soru Sınavı", lambda: self._start_drill("unsolved")),
            ("accuracy", "🎯 Doğruluk", GREEN, None, None),
        )
        for key, label, color, btext, cmd in specs:
            card = tk.Frame(cards, bg=PANEL_BG, highlightbackground="#E0D5C5",
                            highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=3)
            tk.Label(card, text=label, bg=PANEL_BG, fg=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 0))
            num = tk.Label(card, text="-", bg=PANEL_BG, fg=color,
                           font=("Segoe UI Semibold", 22))
            num.pack(anchor="w", padx=10)
            hint = tk.Label(card, text="", bg=PANEL_BG, fg=MUTED, font=("Segoe UI", 8))
            hint.pack(anchor="w", padx=10)
            btn = None
            if btext:
                btn = ttk.Button(card, text=btext, command=cmd)
                btn.pack(anchor="w", padx=10, pady=(3, 9))
            else:
                tk.Label(card, text="", bg=PANEL_BG, font=("Segoe UI", 2)).pack(pady=(3, 9))
            self._dash_cards[key] = {"num": num, "hint": hint, "btn": btn}

        # 📌 Bu Hafta — kural tabanli oneriler (AI cagrisi YOK, pano aninda acilir)
        oneri_kart = tk.Frame(tab, bg=PANEL_BG, highlightbackground=ACCENT,
                              highlightthickness=1)
        oneri_kart.pack(fill="x", padx=9, pady=(8, 2))
        basliklar = tk.Frame(oneri_kart, bg=PANEL_BG)
        basliklar.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(basliklar, text="📌 Bu Hafta", bg=PANEL_BG, fg=ACCENT,
                 font=("Segoe UI Semibold", 11)).pack(side="left")
        self.dash_advice_note = tk.Label(basliklar, text="", bg=PANEL_BG, fg=MUTED,
                                         font=("Segoe UI", 8))
        self.dash_advice_note.pack(side="right")
        self.dash_advice_body = tk.Frame(oneri_kart, bg=PANEL_BG)
        self.dash_advice_body.pack(fill="x", padx=10, pady=(2, 9))
        # Takip paneli sag rayda ~350 px'e kadar daralabiliyor; sabit
        # wraplength gerekce metnini sagdan keserdi (ayni tuzak V47'de
        # karsilama kartinda yasandi).
        self._dash_advice_labels = []
        self.dash_advice_body.bind("<Configure>", self._sync_advice_wrap)

        body = ttk.Panedwindow(tab, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8, pady=4)
        leftf = ttk.Frame(body)
        body.add(leftf, weight=1)
        ttk.Label(leftf, text=self._t("Zayıf konular — önce bunları çalış", "Weak topics — study these first"),
                  style="Header.TLabel").pack(anchor="w", pady=(2, 2))
        self.dash_weak = tk.Text(leftf, height=8, wrap="word", bg=PANEL_BG, fg=FG,
                                 relief="flat", font=("Segoe UI", 10))
        self.dash_weak.pack(fill="both", expand=True)
        self.dash_weak.config(state="disabled")
        rightf = ttk.Frame(body)
        body.add(rightf, weight=1)
        ttk.Label(rightf, text=self._t("Kurs ilerlemesi — çözülen soru", "Course progress — questions solved"),
                  style="Header.TLabel").pack(anchor="w", pady=(2, 2))
        self.dash_course_frame = ttk.Frame(rightf)
        self.dash_course_frame.pack(fill="both", expand=True)

    def _refresh_dashboard(self):
        act = self.store.get_student(self.student_id)
        self.dash_title.config(text=f"Bugün — {_today()}")
        o = self.stats.overview(self.student_id)
        due = self.stats.due_summary(self.student_id)
        self._dash_due_ids = due["due_ids"]
        name = act["name"] if act else "-"
        self.dash_sub.config(
            text=f"Öğrenci: {name}   •   bankada {o['total_questions']} soru   •   "
                 f"7 gün içinde tekrar vakti gelecek: {due['due_week']} soru")
        c = self._dash_cards
        c["due"]["num"].config(text=str(due["due_now"]))
        c["due"]["hint"].config(text=self._t("tekrar zamanı gelen soru", "questions due for review") if due["due_now"] else self._t("bugün tekrar yok 🎉", "nothing due today 🎉"))
        c["wrong"]["num"].config(text=str(o["wrong"]))
        c["wrong"]["hint"].config(text=self._t("son denemesi yanlış", "last attempt was wrong"))
        c["unsolved"]["num"].config(text=str(o["unsolved"]))
        c["unsolved"]["hint"].config(text=self._t("hiç denenmemiş soru", "never attempted"))
        c["accuracy"]["num"].config(text=f"%{o['accuracy']}")
        c["accuracy"]["hint"].config(text=f"sınav ort. %{o['avg_score']} ({o['exams']} sınav)")
        for key, count in (("due", due["due_now"]), ("wrong", o["wrong"]),
                           ("unsolved", o["unsolved"])):
            btn = c[key]["btn"]
            if btn is not None:
                btn.state(["!disabled"] if count else ["disabled"])
        self._refresh_advice()
        # weak topics
        weak = self.stats.weak_topics(self.student_id)
        if weak:
            lines = [f"• {w['course']} / {w['topic']}   →   %{w['accuracy']} doğruluk "
                     f"({w['solved']}✔ {w['wrong']}✘)" for w in weak]
        else:
            lines = ["Henüz yeterli veri yok.",
                     "Soru çözdükçe zayıf konuların burada listelenir."]
        self._set_text(self.dash_weak, "\n".join(lines))
        # course progress bars
        for child in self.dash_course_frame.winfo_children():
            child.destroy()
        rows = self.stats.course_progress(self.student_id)
        if not rows:
            tk.Label(self.dash_course_frame,
                     text="Bankada soru yok. Soru Paketleri sekmesinden aktar\n"
                          "veya Soru Bankası'na kendi sorularını ekle.",
                     bg=BG, fg=MUTED, justify="left").pack(anchor="w", pady=4)
        for r in rows[:8]:
            box = ttk.Frame(self.dash_course_frame)
            box.pack(fill="x", pady=2)
            tk.Label(box, text=f"{r['course']}   ({r['solved']}/{r['total']}  •  %{r['percent']})",
                     bg=BG, fg=FG, font=("Segoe UI", 9)).pack(anchor="w")
            bar = ttk.Progressbar(box, maximum=100, value=r["percent"])
            bar.pack(fill="x")

    # ------------------------------------------------------- 📌 Bu Hafta --
    def _refresh_advice(self):
        """Öneri kartını yeniden kurar. Kural tabanlı motor + tek tık eylem."""
        kutu = getattr(self, "dash_advice_body", None)
        if kutu is None:
            return
        for child in kutu.winfo_children():
            child.destroy()
        self._dash_advice_labels = []
        hata_var = False
        try:
            sonuc = self.advisor.suggest(self.student_id)
        except Exception as exc:            # öneri kartı panoyu ASLA çökertmesin
            hata_var = True
            sonuc = {"oneriler": [], "mesaj": f"Öneriler hesaplanamadı: {exc}"}
        self._dash_advice = sonuc["oneriler"]
        self.dash_advice_note.config(text=sonuc["mesaj"])
        if not sonuc["oneriler"]:
            bos = tk.Label(kutu, text=sonuc["mesaj"], bg=PANEL_BG, fg=MUTED,
                           font=("Segoe UI", 9), justify="left", wraplength=900,
                           anchor="w")
            bos.pack(fill="x", pady=2)
            self._dash_advice_labels.append(bos)
            # Hata durumunda ust kose "her sey normal" demesin.
            self.dash_advice_note.config(
                text=self._t("hesaplanamadı", "could not be computed") if hata_var else self._t("kural tabanlı · AI kullanılmadı", "rule-based · no AI used"))
            self._sync_advice_wrap()
            return
        for i, o in enumerate(sonuc["oneriler"]):
            satir = tk.Frame(kutu, bg=PANEL_BG)
            satir.pack(fill="x", pady=2)
            metin = tk.Frame(satir, bg=PANEL_BG)
            metin.pack(side="left", fill="x", expand=True)
            tk.Label(metin, text=f"{i + 1}. {o['baslik']}", bg=PANEL_BG, fg=FG,
                     font=("Segoe UI Semibold", 10), anchor="w").pack(fill="x")
            # Gerekce GORUNUR olmali: "neden bu?" sorusunun cevabi kartta dursun.
            alt = o["gerekce"]
            if o.get("kurs") and o["tur"] == "zayif_konu":
                alt = f"{o['kurs']} · {alt}"
            gerekce_lbl = tk.Label(metin, text=alt, bg=PANEL_BG, fg=MUTED,
                                   font=("Segoe UI", 9), anchor="w", justify="left",
                                   wraplength=760)
            gerekce_lbl.pack(fill="x")
            self._dash_advice_labels.append(gerekce_lbl)
            ttk.Button(satir, text=o["eylem_metni"],
                       command=lambda k=i: self._run_advice(k)).pack(side="right", padx=4)
        self._sync_advice_wrap()

    def _sync_advice_wrap(self, event=None):
        """Gerekçe metinleri panel genişliğine göre sarılır (kesilmez)."""
        genislik = event.width if event is not None else \
            (self.dash_advice_body.winfo_width() or 760)
        # Eylem dugmesi sagda ~230 px yer kapliyor; metne kalani ver.
        hedef = max(160, int(genislik) - 250)
        for lbl in getattr(self, "_dash_advice_labels", []):
            try:
                lbl.config(wraplength=hedef)
            except Exception:
                pass

    def _run_advice(self, index):
        """Öneri kartındaki tek tık eylemi."""
        try:
            o = (getattr(self, "_dash_advice", None) or [])[index]
        except Exception:
            return
        if o["eylem"] == "sinav_konu":
            exam_id, items = self.exams.build(
                self.student_id, title=f"{o['konu']} çalışması {_today()}",
                course=o.get("kurs") or "", topic=o.get("konu") or "", count=10)
            if not exam_id:
                self._set_status_safe("Bu konuda sınav kuracak soru bulunamadı.")
                return
            self._begin_exam(exam_id, items)
        elif o["eylem"] == "sinav_tekrar":
            ids = list(o.get("qids") or [])[:10]
            exam_id, items = self.exams.build(
                self.student_id, title=f"Tekrar {_today()}",
                count=len(ids), question_ids=ids, shuffle=False)
            if not exam_id:
                self._set_status_safe("Tekrar kuyruğundaki sorular bulunamadı.")
                return
            self._begin_exam(exam_id, items)
        elif o["eylem"] == "kursa_devam":
            app = getattr(self, "app", None)
            acildi = False
            if app is not None and hasattr(app, "open_course_resource"):
                try:
                    acildi = bool(app.open_course_resource(o.get("kurs")))
                except Exception:
                    acildi = False
            if not acildi:
                # Kurs klasoru bulunamadi: sessiz kalmak yerine bankadan calistir.
                exam_id, items = self.exams.build(
                    self.student_id, title=f"{o.get('kurs')} {_today()}",
                    course=o.get("kurs") or "", count=10)
                if exam_id:
                    self._set_status_safe(
                        f"'{o.get('kurs')}' kurs klasörü bulunamadı — bankadan sınav açıldı.")
                    self._begin_exam(exam_id, items)
                else:
                    self._set_status_safe(
                        f"'{o.get('kurs')}' için ne kurs klasörü ne de soru bulunabildi.")

    def _set_status_safe(self, metin):
        app = getattr(self, "app", None)
        if app is not None and hasattr(app, "set_status"):
            try:
                app.set_status(metin)
                return
            except Exception:
                pass
        try:
            self.dash_advice_note.config(text=metin)
        except Exception:
            pass

    def _begin_exam(self, exam_id, items):
        """Drill/öneri sınavlarının ortak başlatma yolu (süresiz — bilinçli)."""
        self._exam_id, self._exam_items, self._exam_idx = exam_id, list(items), 0
        self._exam_started = datetime.now()
        self._exam_deadline = None
        try:
            self.store.set_exam_time_limit(exam_id, 0)   # drill'ler suresiz
        except Exception:
            pass
        self._start_exam_countdown()
        try:
            self.nb.select(self.exam_tab)
        except Exception:
            pass
        self._show_question()

    def _start_drill(self, kind):
        """One-click targeted exam from the dashboard cards."""
        count = 10
        title_map = {"due": "Tekrar", "wrong": "Yanlış Drill", "unsolved": "Yeni Sorular"}
        if kind == "due":
            ids = list(getattr(self, "_dash_due_ids", []) or
                       self.stats.due_summary(self.student_id)["due_ids"])
            if not ids:
                return
            exam_id, items = self.exams.build(
                self.student_id, title=f"{title_map[kind]} {_today()}",
                count=min(count, len(ids)), question_ids=ids[:count], shuffle=False)
        else:
            exam_id, items = self.exams.build(
                self.student_id, title=f"{title_map[kind]} {_today()}",
                count=count, only_status=kind)
        if not exam_id:
            return
        # Bugun panosundan tek-tik drill'ler BILEREK suresizdir: Sinav
        # sekmesindeki sure spinbox'inin degeri buraya sizmasin (_begin_exam
        # deadline'i None yapar).
        self._begin_exam(exam_id, items)

    # ---- Tab 1: Student ---- #
    def _build_student_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self._t("Öğrenci", "Student"))
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text=self._t("Aktif öğrenci:", "Active student:")).pack(side="left")
        self.student_combo = ttk.Combobox(top, state="readonly", width=24)
        self.student_combo.pack(side="left", padx=4)
        self.student_combo.bind("<<ComboboxSelected>>", lambda e: self._select_student())
        self.new_student_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.new_student_var, width=18).pack(side="left", padx=(12, 2))
        ttk.Button(top, text=self._t("Öğrenci Ekle", "Add student"), command=self._add_student).pack(side="left", padx=2)
        ttk.Button(top, text="Sil", command=self._delete_student).pack(side="left", padx=2)
        self.student_status = tk.Label(tab, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.student_status.pack(fill="x", padx=6)
        ttk.Label(tab, text=self._t("Özet", "Summary"), style="Header.TLabel").pack(anchor="w", padx=6, pady=(8, 2))
        self.student_overview = tk.Text(tab, height=10, wrap="word", bg=PANEL_BG, fg=FG,
                                        relief="flat", font=("Consolas", 10))
        self.student_overview.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.student_overview.config(state="disabled")

    def _refresh_students(self):
        rows = self.store.list_students()
        names = [r["name"] for r in rows]
        self._student_rows = rows
        self.student_combo["values"] = names
        act = self.store.active_student()
        if act:
            self.student_id = act["id"]
            try:
                self.student_combo.set(act["name"])
            except Exception:
                pass
        self._refresh_overview()

    def _refresh_overview(self):
        o = self.stats.overview(self.student_id)
        act = self.store.get_student(self.student_id)
        lines = [
            f"Öğrenci                : {act['name'] if act else '-'}",
            "",
            f"Bankadaki toplam soru   : {o['total_questions']}",
            f"Denenen soru            : {o['attempted']}",
            f"Çözdüm                  : {o['solved']}",
            f"Yanlış                  : {o['wrong']}",
            f"Tekrar edilecek         : {o['review']}",
            f"Hiç denenmemiş          : {o['unsolved']}",
            "",
            f"Doğruluk (çözdüm/denenen): %{o['accuracy']}",
            f"Bitmiş sınav sayısı     : {o['exams']}",
            f"Sınav ortalaması        : %{o['avg_score']}",
        ]
        self._set_text(self.student_overview, "\n".join(lines))

    def _select_student(self):
        i = self.student_combo.current()
        if i < 0 or i >= len(self._student_rows):
            return
        self.store.set_active_student(self._student_rows[i]["id"])
        self.student_id = self._student_rows[i]["id"]
        self._status(self.student_status, f"Aktif öğrenci: {self._student_rows[i]['name']}", GREEN)
        self.refresh_all()

    def _add_student(self):
        name = (self.new_student_var.get() or "").strip()
        if not name:
            self._status(self.student_status, self._t("Önce bir isim yaz.", "Type a name first."), DANGER)
            return
        sid = self.store.add_student(name)
        if sid:
            self.store.set_active_student(sid)
            self.new_student_var.set("")
            self._status(self.student_status, f"Öğrenci eklendi: {name}", GREEN)
            self.refresh_all()

    def _delete_student(self):
        act = self.store.get_student(self.student_id)
        if not act:
            return
        if not messagebox.askyesno(self._t("Öğrenci sil", "Delete student"),
                                   f"'{act['name']}' ve TÜM deneme/sınav kayıtları silinsin mi?",
                                   icon="warning"):
            return
        self.store.delete_student(self.student_id)
        self.student_id = self.store.ensure_default_student()
        self._status(self.student_status, self._t("Öğrenci silindi.", "Student deleted."), GREEN)
        self.refresh_all()

    # ---- Tab 2: Question bank ---- #
    def _build_bank_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self._t("Soru Bankası", "Questions"))
        # filters
        f = ttk.Frame(tab)
        f.pack(fill="x", padx=6, pady=(6, 2))
        ttk.Label(f, text="Kurs:").pack(side="left")
        self.f_course = ttk.Combobox(f, state="readonly", width=16, values=[""])
        self.f_course.pack(side="left", padx=2)
        ttk.Label(f, text="Konu:").pack(side="left", padx=(6, 0))
        self.f_topic = ttk.Combobox(f, state="readonly", width=14, values=[""])
        self.f_topic.pack(side="left", padx=2)
        ttk.Label(f, text="Zorluk:").pack(side="left", padx=(6, 0))
        self.f_diff = ttk.Combobox(f, state="readonly", width=9, values=[""] + list(DIFFICULTIES))
        self.f_diff.pack(side="left", padx=2)
        ttk.Label(f, text="Durum:").pack(side="left", padx=(6, 0))
        self.f_status = ttk.Combobox(f, state="readonly", width=11,
                                     values=[""] + [STATUS_TR[s] for s in STATUSES])
        self.f_status.pack(side="left", padx=2)
        ttk.Label(f, text="Paket:").pack(side="left", padx=(6, 0))
        self.f_pack = ttk.Combobox(f, state="readonly", width=14, values=[""])
        self.f_pack.pack(side="left", padx=2)
        self.f_query = tk.StringVar()
        ttk.Entry(f, textvariable=self.f_query, width=16).pack(side="left", padx=(8, 2))
        ttk.Button(f, text="Filtrele", command=self._refresh_bank).pack(side="left", padx=2)
        ttk.Button(f, text="Temizle", command=self._clear_filters).pack(side="left", padx=2)

        split = ttk.Panedwindow(tab, orient="horizontal")
        split.pack(fill="both", expand=True, padx=6, pady=4)
        left = ttk.Frame(split)
        split.add(left, weight=3)
        cols = ("id", "course", "topic", "diff", "status", "q")
        self.q_tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for c, t, w in (("id", "#", 44), ("course", "Kurs", 120), ("topic", "Konu", 110),
                        ("diff", "Zorluk", 70), ("status", "Durum", 84), ("q", "Soru", 320)):
            self.q_tree.heading(c, text=t)
            self.q_tree.column(c, width=w, anchor="w")
        self.q_tree.pack(fill="both", expand=True)
        self.q_tree.bind("<<TreeviewSelect>>", lambda e: self._on_q_select())
        # Status is visible at a glance: green = solved, red = wrong, amber = review.
        self.q_tree.tag_configure("solved", background="#E4F5EA", foreground="#14532D")
        self.q_tree.tag_configure("wrong", background="#FBE7E4", foreground="#7F1D1D")
        self.q_tree.tag_configure("review", background="#FDF3DC", foreground="#713F12")

        right = ttk.Frame(split)
        split.add(right, weight=2)
        self.bank_status = tk.Label(right, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.bank_status.pack(fill="x")
        form = ttk.Frame(right)
        form.pack(fill="x", pady=2)
        self.q_course = tk.StringVar(); self.q_topic = tk.StringVar()
        self.q_diff = tk.StringVar(value="Medium"); self.q_tags = tk.StringVar()
        for lbl, var, w in (("Kurs", self.q_course, 22), ("Konu", self.q_topic, 22), ("Etiket", self.q_tags, 22)):
            r = ttk.Frame(form); r.pack(fill="x", pady=1)
            ttk.Label(r, text=lbl, width=7).pack(side="left")
            ttk.Entry(r, textvariable=var, width=w).pack(side="left", fill="x", expand=True)
        r = ttk.Frame(form); r.pack(fill="x", pady=1)
        ttk.Label(r, text="Zorluk", width=7).pack(side="left")
        ttk.Combobox(r, textvariable=self.q_diff, state="readonly", width=10,
                     values=list(DIFFICULTIES)).pack(side="left")
        ttk.Button(r, text="Seçili PDF'den al", command=self._prefill_from_pdf).pack(side="left", padx=6)
        ttk.Label(right, text="Soru").pack(anchor="w")
        self.q_text = tk.Text(right, height=5, wrap="word", bg=PANEL_BG, fg=FG, relief="solid",
                              borderwidth=1, font=("Segoe UI", 10))
        self.q_text.pack(fill="x")
        ttk.Label(right, text="Cevap").pack(anchor="w")
        self.a_text = tk.Text(right, height=2, wrap="word", bg=PANEL_BG, fg=FG, relief="solid",
                              borderwidth=1, font=("Segoe UI", 10))
        self.a_text.pack(fill="x")
        # Multiple-choice editor: filled options become clickable in the exam.
        chf = ttk.Frame(right)
        chf.pack(fill="x", pady=(3, 0))
        self.q_choice_vars = [tk.StringVar() for _ in CHOICE_LETTERS]
        for i, letter in enumerate(CHOICE_LETTERS):
            row, col = divmod(i, 2)
            cell = ttk.Frame(chf)
            cell.grid(row=row, column=col, sticky="we", padx=(0, 6), pady=1)
            ttk.Label(cell, text=f"{letter})", width=3).pack(side="left")
            ttk.Entry(cell, textvariable=self.q_choice_vars[i]).pack(side="left", fill="x", expand=True)
        chf.columnconfigure(0, weight=1)
        chf.columnconfigure(1, weight=1)
        crow = ttk.Frame(right)
        crow.pack(fill="x", pady=(2, 0))
        ttk.Label(crow, text=self._t("Doğru şık:", "Correct choice:")).pack(side="left")
        self.q_correct = tk.StringVar()
        ttk.Combobox(crow, textvariable=self.q_correct, state="readonly", width=4,
                     values=[""] + list(CHOICE_LETTERS)).pack(side="left", padx=4)
        self.latex_preview_on = tk.BooleanVar(value=False)
        ttk.Checkbutton(crow, text=self._t("∑ Canlı LaTeX önizleme", "∑ Live LaTeX preview"),
                        variable=self.latex_preview_on,
                        command=self._update_latex_preview).pack(side="left", padx=10)
        self.q_preview = tk.Label(right, bg=PANEL_BG, anchor="w", justify="left")
        self.q_preview.pack(fill="x", pady=(2, 0))
        self.q_image_label = tk.Label(right, bg=BG, anchor="w")
        self.q_image_label.pack(anchor="w")
        self.q_text.bind("<KeyRelease>", lambda e: self._schedule_latex_preview())
        b1 = ttk.Frame(right); b1.pack(fill="x", pady=3)
        ttk.Button(b1, text="Ekle", command=self._add_q).pack(side="left", padx=2)
        ttk.Button(b1, text=self._t("Güncelle", "Update"), command=self._update_q).pack(side="left", padx=2)
        ttk.Button(b1, text="Sil", command=self._delete_q).pack(side="left", padx=2)
        ttk.Button(b1, text=self._t("Yeni/Boşalt", "New/Clear"), command=self._clear_form).pack(side="left", padx=2)
        b2 = ttk.Frame(right); b2.pack(fill="x", pady=2)
        ttk.Label(b2, text=self._t("Seçili soru:", "Selected question:"), style="Muted.TLabel").pack(side="left")
        ttk.Button(b2, text=self._t("Çözdüm ✔", "Solved ✔"), command=lambda: self._mark("solved")).pack(side="left", padx=2)
        ttk.Button(b2, text=self._t("Yanlış ✘", "Wrong ✘"), command=lambda: self._mark("wrong")).pack(side="left", padx=2)
        ttk.Button(b2, text="Tekrar", command=lambda: self._mark("review")).pack(side="left", padx=2)
        ttk.Button(b2, text=self._t("Sıfırla", "Reset"), command=lambda: self._mark("unsolved")).pack(side="left", padx=2)
        b3 = ttk.Frame(right); b3.pack(fill="x", pady=2)
        ttk.Button(b3, text=self._t("Toplu Metinden İçe Aktar", "Bulk text import"), command=self._bulk_import).pack(side="left", padx=2)
        ttk.Button(b3, text=self._t("CSV İçe Aktar", "Import CSV"), command=self._csv_import).pack(side="left", padx=2)
        ttk.Button(b3, text=self._t("CSV Dışa Aktar", "Export CSV"), command=self._csv_export).pack(side="left", padx=2)
        ttk.Button(b3, text=self._t("📤 Paketi Dışa Aktar", "📤 Export pack"), command=self._export_pack).pack(side="left", padx=2)

    def _clear_filters(self):
        for cb in (self.f_course, self.f_topic, self.f_diff, self.f_status, self.f_pack):
            cb.set("")
        self.f_query.set("")
        self._refresh_bank()

    def _refresh_filters(self):
        self.f_course["values"] = [""] + self.store.distinct_values("course")
        self.f_topic["values"] = [""] + self.store.distinct_values("topic")
        self.f_pack["values"] = [""] + self.store.distinct_values("source_pack")

    def _status_from_tr(self, tr):
        for k, v in STATUS_TR.items():
            if v == tr:
                return k
        return None

    def _bank_filter_kwargs(self):
        """Soru Bankasi filtrelerinin list_questions argumanlari.

        _refresh_bank ile _export_rows ayni sozlugu kullanir ki gorunum ve
        disa aktarma filtreleri birbirinden sapamasin."""
        return dict(
            student_id=self.student_id,
            course=self.f_course.get() or None, topic=self.f_topic.get() or None,
            difficulty=self.f_diff.get() or None,
            status=self._status_from_tr(self.f_status.get()),
            source_pack=self.f_pack.get() or None,
            query=(self.f_query.get() or "").strip() or None)

    def _export_rows(self):
        """Filtreye uyan TUM sorular (gorunumun 1000 satirlik sinirsiz hali).

        Gorunum listesi (self._q_rows) list_questions'in varsayilan
        limit=1000 siniriyla kirpilir; disa aktarma CSV yoluyla ayni sekilde
        sinirsiz calismali, yoksa buyuk bankalarda paket sessizce eksik olur."""
        return list(self.store.list_questions(limit=100000, **self._bank_filter_kwargs()))

    def _refresh_bank(self):
        rows = self.store.list_questions(**self._bank_filter_kwargs())
        self._q_rows = list(rows)
        smap = self.store.status_map(self.student_id)
        self.q_tree.delete(*self.q_tree.get_children())
        counts = {"solved": 0, "wrong": 0, "review": 0, "unsolved": 0}
        for i, r in enumerate(self._q_rows):
            raw = smap.get(r["id"], "unsolved")
            counts[raw] = counts.get(raw, 0) + 1
            st = STATUS_TR.get(raw, "-")
            q = (r["question_text"] or "").replace("\n", " ")[:70]
            self.q_tree.insert("", "end", iid=str(i), tags=(raw,),
                               values=(r["id"], r["course"], r["topic"], r["difficulty"], st, q))
        self._status(self.bank_status,
                     f"{len(self._q_rows)} soru  •  ✔ {counts['solved']} çözdüm  •  "
                     f"✘ {counts['wrong']} yanlış  •  ↻ {counts['review']} tekrar  •  "
                     f"{counts['unsolved']} denenmemiş", MUTED)
        self._refresh_overview()

    def _on_q_select(self):
        sel = self.q_tree.selection()
        if not sel:
            return
        try:
            r = self._q_rows[int(sel[0])]
        except Exception:
            return
        self._sel_qid = r["id"]
        self.q_course.set(r["course"] or ""); self.q_topic.set(r["topic"] or "")
        self.q_diff.set(r["difficulty"] or "Medium"); self.q_tags.set(r["tags"] or "")
        self.q_text.delete("1.0", "end"); self.q_text.insert("1.0", r["question_text"] or "")
        self.a_text.delete("1.0", "end"); self.a_text.insert("1.0", r["answer_text"] or "")
        ch = StudentStore.parse_choices(r)
        for i, v in enumerate(self.q_choice_vars):
            v.set(ch[i] if i < len(ch) else "")
        try:
            self.q_correct.set((r["correct_choice"] or "").strip().upper())
        except Exception:
            self.q_correct.set("")
        try:
            self._show_question_image(r["image_path"] or "")
        except Exception:
            self._show_question_image("")
        self._schedule_latex_preview()
        src = r["source_pdf"] or ""
        self._status(self.bank_status,
                     f"#{r['id']} seçildi." + (f"  Kaynak: {Path(src).name} s.{r['page_number']}" if src else ""),
                     MUTED)

    def _clear_form(self):
        self._sel_qid = None
        self.q_text.delete("1.0", "end"); self.a_text.delete("1.0", "end")
        self.q_tags.set("")
        for v in self.q_choice_vars:
            v.set("")
        self.q_correct.set("")
        self._show_question_image("")
        self.q_preview.config(image="", text="")
        self.q_preview.image = None
        self._status(self.bank_status, "Yeni soru: alanları doldur ve Ekle'ye bas.", MUTED)

    # -- LaTeX live preview + question image thumbnail -------------------- #
    def _schedule_latex_preview(self):
        job = getattr(self, "_latex_job", None)
        if job:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._latex_job = self.after(450, self._update_latex_preview)

    def _update_latex_preview(self):
        self._latex_job = None
        if not self.latex_preview_on.get():
            self.q_preview.config(image="", text="")
            self.q_preview.image = None
            return
        text = self.q_text.get("1.0", "end").strip()
        img, err = render_math_image(text, max_width_px=440, fontsize=12)
        if img is None:
            self.q_preview.config(image="", text=("" if err == "empty" else err), fg=DANGER)
            self.q_preview.image = None
            return
        try:
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(img)
            self.q_preview.config(image=photo, text="")
            self.q_preview.image = photo
        except Exception as exc:
            self.q_preview.config(image="", text=f"Önizleme gösterilemedi: {exc}", fg=DANGER)

    def _show_question_image(self, path):
        self.q_image_label.config(image="", text="")
        self.q_image_label.image = None
        if not path:
            return
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img.thumbnail((420, 170))
            photo = ImageTk.PhotoImage(img)
            self.q_image_label.config(image=photo)
            self.q_image_label.image = photo
        except Exception:
            self.q_image_label.config(text=f"[görsel: {Path(str(path)).name}]", fg=MUTED)

    def _choices_json(self):
        vals = [v.get().strip() for v in self.q_choice_vars]
        while vals and not vals[-1]:
            vals.pop()
        return json.dumps(vals, ensure_ascii=False) if vals else ""

    def _prefill_from_pdf(self):
        path = getattr(self.app, "selected_path", None)
        pv = getattr(self.app, "pdf_viewer", None)
        page = int(getattr(pv, "page_index", 0) or 0) + 1 if pv is not None else 0
        if not path:
            self._status(self.bank_status, "Önce Kurs Kaynakları'ndan bir PDF seç.", DANGER)
            return
        self._pending_source = (str(path), page)
        course = getattr(self.app, "selected_course", "") or ""
        if course and not self.q_course.get():
            self.q_course.set(course)
        self._status(self.bank_status, f"Kaynak alındı: {Path(str(path)).name} s.{page}", GREEN)

    def _form_source(self):
        src, page = getattr(self, "_pending_source", ("", 0))
        return src, page

    def _add_q(self):
        q = self.q_text.get("1.0", "end").strip()
        if not q:
            self._status(self.bank_status, self._t("Soru metni boş olamaz.", "The question text cannot be empty."), DANGER)
            return
        src, page = self._form_source()
        qid = self.store.add_question(q, self.a_text.get("1.0", "end").strip(),
                                      course=self.q_course.get().strip(),
                                      topic=self.q_topic.get().strip(),
                                      difficulty=self.q_diff.get() or "Medium",
                                      source_pdf=src, page_number=page,
                                      tags=self.q_tags.get().strip(),
                                      choices=[v.get() for v in self.q_choice_vars],
                                      correct_choice=self.q_correct.get())
        if qid:
            self._sel_qid = qid
            self._refresh_filters(); self._refresh_bank()
            self._status(self.bank_status, f"Soru eklendi (#{qid}).", GREEN)

    def _update_q(self):
        if not self._sel_qid:
            self._status(self.bank_status, self._t("Önce listeden bir soru seç.", "Select a question from the list first."), DANGER)
            return
        self.store.update_question(
            self._sel_qid, course=self.q_course.get().strip(), topic=self.q_topic.get().strip(),
            difficulty=self.q_diff.get() or "Medium", tags=self.q_tags.get().strip(),
            question_text=self.q_text.get("1.0", "end").strip(),
            answer_text=self.a_text.get("1.0", "end").strip(),
            choices=self._choices_json(),
            correct_choice=(self.q_correct.get() or "").strip().upper()[:1])
        self._refresh_filters(); self._refresh_bank()
        self._status(self.bank_status, f"Soru güncellendi (#{self._sel_qid}).", GREEN)

    def _delete_q(self):
        if not self._sel_qid:
            return
        if not messagebox.askyesno("Soru sil", f"#{self._sel_qid} silinsin mi?", icon="warning"):
            return
        self.store.delete_question(self._sel_qid)
        self._sel_qid = None
        self._clear_form(); self._refresh_bank()

    def _mark(self, status):
        if not self._sel_qid:
            self._status(self.bank_status, self._t("Önce listeden bir soru seç.", "Select a question from the list first."), DANGER)
            return
        self.store.record_attempt(self._sel_qid, self.student_id, status)
        self._refresh_bank()
        try:
            self._refresh_dashboard()
        except Exception:
            pass
        self._status(self.bank_status, f"#{self._sel_qid} → {STATUS_TR[status]}", GREEN)

    def _bulk_import(self):
        win = tk.Toplevel(self)
        win.title("Toplu Soru İçe Aktar")
        win.geometry("640x460")
        tk.Label(win, text="Her satır bir soru.  'soru = cevap'  ya da  'soru | cevap'  yazabilirsin.\n"
                           "Cevapsız satırlar da eklenir.", fg=MUTED, bg=BG, justify="left").pack(anchor="w", padx=10, pady=8)
        txt = tk.Text(win, wrap="word", bg=PANEL_BG, fg=FG, relief="solid", borderwidth=1)
        txt.pack(fill="both", expand=True, padx=10)
        row = ttk.Frame(win); row.pack(fill="x", padx=10, pady=8)

        def do():
            n = self.bank.import_text_block(
                txt.get("1.0", "end"), course=self.q_course.get().strip(),
                topic=self.q_topic.get().strip(), difficulty=self.q_diff.get() or "Medium")
            self._refresh_filters(); self._refresh_bank()
            self._status(self.bank_status, f"{n} soru içe aktarıldı.", GREEN)
            win.destroy()
        ttk.Button(row, text=self._t("İçe Aktar", "Import"), command=do).pack(side="left")
        ttk.Button(row, text="Kapat", command=win.destroy).pack(side="left", padx=4)

    def _csv_import(self):
        p = filedialog.askopenfilename(title="Soru CSV", filetypes=[("CSV", "*.csv")])
        if not p:
            return
        n = self.bank.import_csv(p, course=self.q_course.get().strip(), topic=self.q_topic.get().strip())
        self._refresh_filters(); self._refresh_bank()
        self._status(self.bank_status, f"{n} soru CSV'den aktarıldı.", GREEN)

    def _csv_export(self):
        p = filedialog.asksaveasfilename(title="CSV kaydet", defaultextension=".csv",
                                         filetypes=[("CSV", "*.csv")])
        if not p:
            return
        n = self.store.export_questions_csv(p)
        self._status(self.bank_status, f"{n} soru CSV'ye yazıldı.", GREEN)

    def _export_pack(self):
        """Filtrelenmis gorunumdeki sorulari acik paket JSON'una yazar.

        CSV'den farki: paket formati lisans + atif tasir ve dosya bir
        arkadasin question_packs/ klasorune kopyalandiginda Soru Paketleri
        sekmesinden dogrudan ice aktarilabilir (siklar dahil).
        """
        if qpacks is None:
            self._status(self.bank_status, self._t("question_packs modülü yüklenemedi.", "The question_packs module could not be loaded."), DANGER)
            return
        # Gorunum 1000 satirla sinirli; disa aktarma filtreye uyan HER SEYI alir.
        rows = self._export_rows()
        if not rows:
            self._status(self.bank_status, self._t("Dışa aktarılacak soru yok — filtreleri kontrol et.", "Nothing to export — check your filters."), DANGER)
            return
        exportable = sum(0 if qpacks.is_image_only(r["question_text"]) else 1 for r in rows)
        image_only = len(rows) - exportable
        # V48: .mcpack (ZIP) bicimi gorselleri de tasir; gorsel dosyasi
        # gercekten diskte duran "gorsel-yalnizca" sorular artik atlanmaz.
        gorselli = sum(1 for r in rows
                       if str(r["image_path"] or "").strip()
                       and Path(str(r["image_path"])).exists())
        if not exportable and not gorselli:
            self._status(self.bank_status,
                         "Dışa aktarılacak soru yok: görsel dosyaları da bulunamadı.", DANGER)
            return

        win = tk.Toplevel(self)
        win.title("Paketi Dışa Aktar")
        win.transient(self.winfo_toplevel())
        win.grab_set()  # kucuk form; icinden yalnizca (zaten modal) dosya diyalogu acilir
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)
        head = f"Filtreye uyan {exportable} metin sorusu dışa aktarılacak."
        if gorselli:
            head += f"\n{gorselli} sorunun görseli var — .mcpack biçimi bunları da taşır."
        if image_only and not gorselli:
            head += f"\n({image_only} görsel-yalnızca soru pakete yazılamaz, atlanacak.)"
        ttk.Label(frm, text=head + "\n(Kapsamı daraltmak için önce Soru Bankası filtrelerini kullan.)",
                  justify="left").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        cur_course = (self.f_course.get() or "").strip()
        name_var = tk.StringVar(value=(cur_course + " Soruları").strip() if cur_course else "Sorularım")
        course_var = tk.StringVar(value=cur_course)
        lang_var = tk.StringVar(value="tr")
        lic_var = tk.StringVar(value="")
        attr_var = tk.StringVar(value="")
        url_var = tk.StringVar(value="")

        def row(r, label, widget):
            ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", pady=2)
            widget.grid(row=r, column=1, sticky="we", pady=2, padx=(8, 0))

        frm.columnconfigure(1, weight=1)
        row(1, "Paket adı", ttk.Entry(frm, textvariable=name_var))
        row(2, "Kurs", ttk.Entry(frm, textvariable=course_var))
        lang_row = ttk.Frame(frm)
        ttk.Radiobutton(lang_row, text="Türkçe", variable=lang_var, value="tr").pack(side="left")
        ttk.Radiobutton(lang_row, text="English", variable=lang_var, value="en").pack(side="left", padx=8)
        row(3, "Dil", lang_row)
        row(4, "Lisans", ttk.Combobox(frm, textvariable=lic_var,
                                      values=["", "CC BY 4.0", "CC BY-SA 4.0", "CC0 1.0"]))
        row(5, "Atıf (kim hazırladı)", ttk.Entry(frm, textvariable=attr_var))
        row(6, "Kaynak URL (opsiyonel)", ttk.Entry(frm, textvariable=url_var))
        bicim_var = tk.StringVar(value="mcpack" if gorselli else "json")
        bicim_row = ttk.Frame(frm)
        ttk.Radiobutton(bicim_row, text=self._t(".mcpack (görselli, ZIP)", ".mcpack (with images, ZIP)"), variable=bicim_var,
                        value="mcpack").pack(side="left")
        ttk.Radiobutton(bicim_row, text=self._t(".json (yalnız metin)", ".json (text only)"), variable=bicim_var,
                        value="json").pack(side="left", padx=8)
        row(7, "Biçim", bicim_row)
        ttk.Label(frm, text="Lisans boş bırakılırsa paket alıcıda UNKNOWN olarak işaretlenir\n"
                            "ve içe aktarmadan önce uyarı gösterilir (kişisel paylaşım için uygundur).\n"
                            ".json biçimi eski sürümlerle uyumludur ama görsel taşımaz.",
                  justify="left").grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 4))

        def do_export():
            base = "".join(ch if (ch.isalnum() or ch in "-_") else "_" for ch in name_var.get().strip())
            # Taze kurulumda question_packs/ klasoru yoktur; olusturmadan
            # verilirse Windows dosya diyalogu gecersiz initialdir'i sessizce
            # yok sayip son kullanilan klasorde acilir ve dosya PACKS_DIR
            # disinda kalir (Soru Paketleri sekmesi akisi hic calismazdi).
            try:
                Path(qpacks.PACKS_DIR).mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            zipli = bicim_var.get() == "mcpack"
            uzanti = qpacks.MCPACK_UZANTI if zipli else ".json"
            p = filedialog.asksaveasfilename(
                parent=win, title="Paketi kaydet",
                initialdir=str(qpacks.PACKS_DIR), initialfile=(base or "paket") + uzanti,
                defaultextension=uzanti,
                filetypes=([("Görselli paket", "*" + qpacks.MCPACK_UZANTI)] if zipli
                           else [("JSON", "*.json")]))
            if not p:
                return
            try:
                written, skipped = qpacks.export_pack(
                    rows, p, name=name_var.get().strip(), course=course_var.get().strip(),
                    lang=lang_var.get(), license_text=lic_var.get().strip(),
                    attribution=attr_var.get().strip(), source_url=url_var.get().strip(),
                    include_images=zipli)
            except Exception as exc:
                self._status(self.bank_status, f"Paket yazılamadı: {exc}", DANGER)
                win.destroy()
                return
            win.destroy()
            if not written:
                self._status(self.bank_status,
                             "Paket oluşturulmadı: görünümdeki sorular görsel-yalnızca.", DANGER)
                return
            msg = f"{written} soru pakete yazıldı"
            if skipped:
                msg += f" ({skipped} görsel-yalnızca soru atlandı)"
            try:
                if Path(p).resolve().parent == Path(qpacks.PACKS_DIR).resolve():
                    self._refresh_packs()
                    msg += " — Soru Paketleri sekmesinde hazır"
            except Exception:
                pass
            self._status(self.bank_status, msg + ".", GREEN)

        btns = ttk.Frame(frm)
        btns.grid(row=8, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(btns, text=self._t("Vazgeç", "Cancel"), command=win.destroy).pack(side="right", padx=4)
        ttk.Button(btns, text=self._t("📤 Dışa Aktar", "📤 Export"), command=do_export).pack(side="right")

    # ---- Tab 3: Question packs ---- #
    def _build_packs_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self._t("Soru Paketleri", "Question Packs"))
        self.packs_tab = tab  # dis kod (karsilama karti) index yerine bunu secer
        tk.Label(tab, text="Telif notu: Türkçe ticari/MEB soru bankaları TELİFLİDİR ve gömülmez. "
                           "Aşağıdaki paketler ya bu programın kendi ÜRETEÇLERİdir (sınırsız, "
                           "telifsiz) ya da senin question_packs/ klasörüne koyduğun açık lisanslı "
                           "JSON paketlerdir; lisans her soruyla birlikte saklanır.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8), wraplength=980, justify="left").pack(
            fill="x", padx=6, pady=(6, 2))
        ctl = ttk.Frame(tab)
        ctl.pack(fill="x", padx=6, pady=2)
        ttk.Label(ctl, text="Dil:").pack(side="left")
        self.p_lang = ttk.Combobox(ctl, state="readonly", width=5, values=["tr", "en"])
        self.p_lang.current(0)
        self.p_lang.pack(side="left", padx=2)
        self.p_lang.bind("<<ComboboxSelected>>", lambda e: self._refresh_packs())
        ttk.Label(ctl, text="Zorluk:").pack(side="left", padx=(6, 0))
        self.p_diff = ttk.Combobox(ctl, state="readonly", width=9, values=[""] + list(DIFFICULTIES))
        self.p_diff.pack(side="left", padx=2)
        ttk.Label(ctl, text="Adet:").pack(side="left", padx=(6, 0))
        self.p_count = tk.IntVar(value=20)
        ttk.Spinbox(ctl, from_=1, to=500, width=5, textvariable=self.p_count).pack(side="left", padx=2)
        ttk.Button(ctl, text=self._t("Önizle", "Preview"), command=self._preview_pack).pack(side="left", padx=(8, 2))
        ttk.Button(ctl, text="Bankaya Aktar", command=self._import_pack).pack(side="left", padx=2)
        ttk.Button(ctl, text=self._t("Yenile", "Refresh"), command=self._refresh_packs).pack(side="left", padx=2)

        split = ttk.Panedwindow(tab, orient="vertical")
        split.pack(fill="both", expand=True, padx=6, pady=4)
        top = ttk.Frame(split)
        split.add(top, weight=3)
        cols = ("name", "course", "kind", "langs", "count", "license")
        self.p_tree = ttk.Treeview(top, columns=cols, show="headings", height=8, selectmode="browse")
        for c, t, w in (("name", "Paket", 210), ("course", "Kurs", 190), ("kind", "Tür", 80),
                        ("langs", "Dil", 60), ("count", "Soru", 60), ("license", "Lisans", 300)):
            self.p_tree.heading(c, text=t)
            self.p_tree.column(c, width=w, anchor="w")
        self.p_tree.pack(fill="both", expand=True)
        self.packs_status = tk.Label(top, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.packs_status.pack(fill="x")

        bottom = ttk.Frame(split)
        split.add(bottom, weight=2)
        ttk.Label(bottom, text=self._t("Önizleme / Bankadaki paketler", "Preview / packs in your bank"), style="Header.TLabel").pack(anchor="w")
        self.p_preview = tk.Text(bottom, height=8, wrap="word", bg=PANEL_BG, fg=FG,
                                 relief="flat", font=("Consolas", 9))
        self.p_preview.pack(fill="both", expand=True)
        self.p_preview.config(state="disabled")
        mrow = ttk.Frame(bottom)
        mrow.pack(fill="x", pady=3)
        ttk.Label(mrow, text="Bankadaki paket:", style="Muted.TLabel").pack(side="left")
        self.p_installed = ttk.Combobox(mrow, state="readonly", width=26, values=[])
        self.p_installed.pack(side="left", padx=4)
        ttk.Button(mrow, text=self._t("Bu Paketin Sorularını Sil", "Delete this pack's questions"),
                   command=self._delete_pack_questions).pack(side="left", padx=2)

    def _selected_pack(self):
        sel = self.p_tree.selection()
        if not sel:
            return None
        try:
            return self._pack_rows[int(sel[0])]
        except Exception:
            return None

    def _refresh_packs(self):
        self._pack_rows = []
        self.p_tree.delete(*self.p_tree.get_children())
        if qpacks is None:
            self._status(self.packs_status, self._t("question_packs.py bulunamadı.", "question_packs.py was not found."), DANGER)
            return
        lang = self.p_lang.get() or "tr"
        try:
            self._pack_rows = qpacks.list_packs(lang=lang)
        except Exception as exc:
            self._status(self.packs_status, f"Paketler okunamadı: {exc}", DANGER)
            return
        for i, p in enumerate(self._pack_rows):
            self.p_tree.insert("", "end", iid=str(i),
                               values=(p["name"], p["course"], p["kind"], p["langs"],
                                       p["count"], p["license"]))
        self._status(self.packs_status,
                     f"{len(self._pack_rows)} paket. (üreteç = sınırsız/telifsiz, "
                     f"external = question_packs/ klasöründen)", MUTED)
        # installed packs (for management)
        try:
            summary = self.store.pack_summary()
            self._installed = summary
            self.p_installed["values"] = [f"{s['source_pack']} ({s['count']})" for s in summary]
        except Exception:
            self._installed = []

    def _preview_pack(self):
        p = self._selected_pack()
        if not p or qpacks is None:
            self._status(self.packs_status, self._t("Önce listeden bir paket seç.", "Select a pack from the list first."), DANGER)
            return
        rows = qpacks.get_questions(p["id"], count=min(10, int(self.p_count.get() or 10)),
                                    lang=self.p_lang.get() or "tr",
                                    difficulty=self.p_diff.get() or None)
        if not rows:
            self._set_text(self.p_preview, "Bu filtreyle örnek soru üretilemedi.")
            return
        lines = [f"PAKET   : {p['name']}", f"LİSANS  : {p['license']}"]
        if p.get("attribution"):
            lines.append(f"ATIF    : {p['attribution']}")
        if p.get("source_url"):
            lines.append(f"KAYNAK  : {p['source_url']}")
        lines.append("")
        for i, r in enumerate(rows, 1):
            lines.append(f"{i}. [{r['topic']} / {r['difficulty']}] {r['question']}")
            lines.append(f"   → {r['answer']}")
        self._set_text(self.p_preview, "\n".join(lines))
        self._status(self.packs_status, f"{p['name']} önizlendi.", GREEN)

    def _import_pack(self):
        p = self._selected_pack()
        if not p or qpacks is None:
            self._status(self.packs_status, self._t("Önce listeden bir paket seç.", "Select a pack from the list first."), DANGER)
            return
        if str(p.get("license", "")).startswith("UNKNOWN"):
            if not messagebox.askyesno(
                    "Lisans bilinmiyor",
                    "Bu paketin lisansı belirtilmemiş. Telifli içerik olabilir.\n\n"
                    "Yine de aktarılsın mı?", icon="warning"):
                return
        n = qpacks.import_into_store(self.store, p["id"],
                                     count=int(self.p_count.get() or 20),
                                     lang=self.p_lang.get() or "tr",
                                     difficulty=self.p_diff.get() or None)
        self._refresh_filters(); self._refresh_bank(); self._refresh_packs()
        self._status(self.packs_status,
                     f"{n} soru bankaya aktarıldı ({p['name']}). Tekrarlar atlandı.",
                     GREEN if n else MUTED)

    def _delete_pack_questions(self):
        i = self.p_installed.current()
        if i < 0 or i >= len(getattr(self, "_installed", [])):
            self._status(self.packs_status, self._t("Önce bankadaki bir paket seç.", "Select an installed pack first."), DANGER)
            return
        s = self._installed[i]
        pack = s["source_pack"]
        real = "" if pack == "(manuel)" else pack
        if not messagebox.askyesno("Paketi sil",
                                   f"'{pack}' paketinden gelen {s['count']} soru ve bunlara ait "
                                   "tüm çözüm kayıtları silinsin mi?", icon="warning"):
            return
        n = self.store.delete_by_pack(real)
        self._refresh_filters(); self._refresh_bank(); self._refresh_packs()
        self._status(self.packs_status, f"{n} soru silindi ({pack}).", GREEN)

    # ---- Tab 4: Exam ---- #
    def _build_exam_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self._t("Sınav", "Exam"))
        self.exam_tab = tab
        setup = ttk.Frame(tab)
        setup.pack(fill="x", padx=6, pady=6)
        ttk.Label(setup, text="Kurs:").pack(side="left")
        self.e_course = ttk.Combobox(setup, state="readonly", width=16, values=[""])
        self.e_course.pack(side="left", padx=2)
        ttk.Label(setup, text="Konu:").pack(side="left", padx=(6, 0))
        self.e_topic = ttk.Combobox(setup, state="readonly", width=14, values=[""])
        self.e_topic.pack(side="left", padx=2)
        ttk.Label(setup, text="Zorluk:").pack(side="left", padx=(6, 0))
        self.e_diff = ttk.Combobox(setup, state="readonly", width=9, values=[""] + list(DIFFICULTIES))
        self.e_diff.pack(side="left", padx=2)
        ttk.Label(setup, text=self._t("Soru sayısı:", "Questions:")).pack(side="left", padx=(6, 0))
        self.e_count = tk.IntVar(value=10)
        ttk.Spinbox(setup, from_=1, to=100, width=5, textvariable=self.e_count).pack(side="left", padx=2)
        ttk.Label(setup, text="Havuz:").pack(side="left", padx=(6, 0))
        self.e_pool = ttk.Combobox(setup, state="readonly", width=14,
                                   values=["Hepsi", "Çözülmedi", "Yanlış", "Tekrar", "Tekrar Vakti"])
        self.e_pool.current(0)
        self.e_pool.pack(side="left", padx=2)
        ttk.Label(setup, text=self._t("⏱ Süre (dk):", "⏱ Duration (min):")).pack(side="left", padx=(6, 0))
        self.e_duration = tk.IntVar(value=0)  # 0 = süresiz (eski davranış)
        ttk.Spinbox(setup, from_=0, to=180, width=5, textvariable=self.e_duration).pack(side="left", padx=2)
        ttk.Button(setup, text=self._t("Sınavı Başlat", "Start exam"), command=self._start_exam).pack(side="left", padx=8)
        ttk.Button(setup, text="Bitir", command=self._finish_exam).pack(side="left")
        self.exam_timer_label = tk.Label(setup, text="", bg=BG, fg=DANGER,
                                         font=("Segoe UI", 10, "bold"))
        self.exam_timer_label.pack(side="left", padx=(10, 0))
        self.exam_status = tk.Label(tab, text=self._t("Sınav başlatılmadı.", "No exam started."), bg=BG, fg=MUTED,
                                    font=("Segoe UI", 9, "bold"), anchor="w")
        self.exam_status.pack(fill="x", padx=6)
        body = ttk.Frame(tab)
        body.pack(fill="both", expand=True, padx=6, pady=4)
        ttk.Label(body, text="Soru", style="Header.TLabel").pack(anchor="w")
        self.e_question = tk.Text(body, height=4, wrap="word", bg=PANEL_BG, fg=FG,
                                  relief="flat", font=("Segoe UI", 11))
        self.e_question.pack(fill="x")
        self.e_question.config(state="disabled")
        # Cropped question image or rendered LaTeX goes here.
        self.e_image = tk.Label(body, bg=BG, anchor="w")
        self.e_image.pack(anchor="w")
        # Clickable A–E choices (built per question when the bank row has them).
        self.e_choice_frame = ttk.Frame(body)
        self.e_choice_frame.pack(fill="x", pady=(2, 0))
        self._exam_choice_buttons = {}
        self._exam_correct_choice = ""
        row = ttk.Frame(body); row.pack(fill="x", pady=4)
        ttk.Label(row, text=self._t("Cevabın:", "Your answer:")).pack(side="left")
        self.e_answer = tk.StringVar()
        ttk.Entry(row, textvariable=self.e_answer, width=40).pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(row, text=self._t("Cevabı Göster", "Show answer"), command=self._reveal).pack(side="left", padx=2)
        # Sinav bitisinde ozeti paylasmak icin: baslangicta PASIF (kopyalanacak
        # bir sey yokken aktif dugme yanlis vaat olurdu).
        self.e_copy_btn = ttk.Button(row, text=self._t("📋 Panoya kopyala", "📋 Copy summary"),
                                     command=self._sinav_ozeti_panoya)
        self.e_copy_btn.pack(side="left", padx=2)
        self.e_copy_btn.state(["disabled"])
        ttk.Label(body, text=self._t("Doğru cevap / Değerlendirme", "Correct answer / assessment")).pack(anchor="w")
        self.e_reveal = tk.Text(body, height=4, wrap="word", bg=PANEL_BG, fg=FG,
                                relief="flat", font=("Segoe UI", 10))
        self.e_reveal.pack(fill="x")
        self.e_reveal.config(state="disabled")
        mark = ttk.Frame(body); mark.pack(fill="x", pady=4)
        ttk.Button(mark, text=self._t("Doğru ✔  (sonraki)", "Correct ✔  (next)"), command=lambda: self._mark_exam(True)).pack(side="left", padx=2)
        ttk.Button(mark, text=self._t("Yanlış ✘  (sonraki)", "Wrong ✘  (next)"), command=lambda: self._mark_exam(False)).pack(side="left", padx=2)
        ttk.Button(mark, text="Atla", command=self._next_question).pack(side="left", padx=2)
        # Digital scratch pad: draw the solution steps with mouse / pen tablet.
        sk = ttk.Frame(body)
        sk.pack(fill="both", expand=True, pady=(4, 0))
        skbar = ttk.Frame(sk)
        skbar.pack(fill="x")
        ttk.Label(skbar, text=self._t("✏️ Karalama Alanı", "✏️ Scratch pad"), style="Header.TLabel").pack(side="left")
        ttk.Button(skbar, text="Kalem", command=lambda: self._set_scratch_tool("pen")).pack(side="left", padx=2)
        ttk.Button(skbar, text="Silgi", command=lambda: self._set_scratch_tool("erase")).pack(side="left", padx=2)
        ttk.Button(skbar, text="Temizle", command=self._clear_scratch).pack(side="left", padx=2)
        self.scratch_hint = tk.Label(skbar, text="fare veya kalemli tablet ile çöz — soru değişince temizlenir",
                                     bg=BG, fg=MUTED, font=("Segoe UI", 8))
        self.scratch_hint.pack(side="left", padx=8)
        self.scratch = tk.Canvas(sk, bg="#FFFFFF", highlightthickness=1,
                                 highlightbackground="#D8C9B6", height=150)
        self.scratch.pack(fill="both", expand=True)
        self._scratch_tool = "pen"
        self._scratch_last = None
        self.scratch.bind("<ButtonPress-1>", self._scratch_press)
        self.scratch.bind("<B1-Motion>", self._scratch_drag)
        self.scratch.bind("<ButtonRelease-1>", lambda e: setattr(self, "_scratch_last", None))

    # -- exam scratch pad -------------------------------------------------- #
    def _set_scratch_tool(self, tool):
        self._scratch_tool = tool
        self.scratch_hint.config(text="silgi: çizgilerin üzerinden geç" if tool == "erase"
                                 else "fare veya kalemli tablet ile çöz — soru değişince temizlenir")

    def _clear_scratch(self):
        try:
            self.scratch.delete("all")
        except Exception:
            pass
        self._scratch_last = None

    def _scratch_press(self, event):
        self._scratch_last = (event.x, event.y)
        if self._scratch_tool == "erase":
            self._scratch_erase(event.x, event.y)

    def _scratch_drag(self, event):
        if self._scratch_tool == "erase":
            self._scratch_erase(event.x, event.y)
            return
        last = self._scratch_last
        if last:
            self.scratch.create_line(last[0], last[1], event.x, event.y,
                                     fill="#1F2937", width=2, capstyle="round", smooth=True)
        self._scratch_last = (event.x, event.y)

    def _scratch_erase(self, x, y):
        for item in self.scratch.find_overlapping(x - 9, y - 9, x + 9, y + 9):
            self.scratch.delete(item)

    # -- exam choices ------------------------------------------------------ #
    def _build_exam_choices(self, item):
        for w in self.e_choice_frame.winfo_children():
            w.destroy()
        self._exam_choice_buttons = {}
        try:
            self._exam_correct_choice = (item["correct_choice"] or "").strip().upper()
        except Exception:
            self._exam_correct_choice = ""
        choices = StudentStore.parse_choices(item)
        for i, ctext in enumerate(choices[:len(CHOICE_LETTERS)]):
            letter = CHOICE_LETTERS[i]
            b = tk.Button(self.e_choice_frame, text=f"{letter})  {ctext}", anchor="w",
                          relief="ridge", bd=1, bg=PANEL_BG, fg=FG,
                          activebackground="#FBEADD", font=("Segoe UI", 10),
                          command=lambda L=letter: self._pick_choice(L))
            b.pack(fill="x", pady=1)
            self._exam_choice_buttons[letter] = b

    def _pick_choice(self, letter):
        self.e_answer.set(letter)
        # Pastel arka planlar ACIK renkler oldugu icin fg de birlikte
        # verilmeli: koyu temada FG fildisi kalirsa secilen sik okunmaz
        # (q_tree etiketlerindeki pastel+koyu-fg deseninin aynisi).
        for L, b in self._exam_choice_buttons.items():
            if L == letter:
                b.config(bg="#FBEADD", fg="#2B2620")
            else:
                b.config(bg=PANEL_BG, fg=FG)

    def _color_choices_after_reveal(self):
        sel = (self.e_answer.get() or "").strip().upper()[:1]
        for L, b in self._exam_choice_buttons.items():
            if L == self._exam_correct_choice:
                b.config(bg="#D9F2E2", fg="#14532D")
            elif L == sel:
                b.config(bg="#FADBD5", fg="#7F1D1D")

    def _show_exam_visual(self, item):
        """Question image (cropped from a PDF) or rendered LaTeX text."""
        self.e_image.config(image="", text="")
        self.e_image.image = None
        path = ""
        try:
            path = item["image_path"] or ""
        except Exception:
            path = ""
        if path and Path(str(path)).exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(path)
                img.thumbnail((760, 300))
                photo = ImageTk.PhotoImage(img)
                self.e_image.config(image=photo)
                self.e_image.image = photo
                return
            except Exception:
                pass
        text = item["question_text"] or ""
        if "$" in text:
            # Sinavdaki soru gorseli ICERIKTIR (kagit gibi) — koyu temada bile
            # acik kalir; PDF sayfalari ve ders karti posterleriyle ayni karar.
            img, _err = render_math_image(text, max_width_px=740, fontsize=13,
                                          dark=False)
            if img is not None:
                try:
                    from PIL import ImageTk
                    photo = ImageTk.PhotoImage(img)
                    self.e_image.config(image=photo)
                    self.e_image.image = photo
                except Exception:
                    pass

    def _start_exam(self):
        pool_map = {"Hepsi": None, "Çözülmedi": "unsolved", "Yanlış": "wrong", "Tekrar": "review"}
        count = int(self.e_count.get() or 10)
        if self.e_pool.get() == "Tekrar Vakti":
            ids = self.stats.due_summary(self.student_id)["due_ids"]
            if not ids:
                self._status(self.exam_status, self._t("Bugün tekrar vakti gelen soru yok. 🎉", "Nothing is due for review today. 🎉"), GREEN)
                return
            exam_id, items = self.exams.build(
                self.student_id, title=f"Tekrar {_today()}",
                count=min(count, len(ids)), question_ids=ids[:count], shuffle=False)
        else:
            exam_id, items = self.exams.build(
                self.student_id, title=f"Test {_today()}",
                course=self.e_course.get(), topic=self.e_topic.get(),
                difficulty=self.e_diff.get(), count=count,
                only_status=pool_map.get(self.e_pool.get()))
        if not exam_id:
            self._status(self.exam_status, "Bu filtreye uyan soru yok. Önce Soru Bankası'na soru ekle.", DANGER)
            return
        self._exam_id, self._exam_items, self._exam_idx = exam_id, list(items), 0
        self._exam_started = datetime.now()
        # Sureli mod: spinbox 0'dan buyukse geri sayim baslar, sure dolunca
        # sinav otomatik bitirilir. 0 = suresiz (eski davranis).
        parse_warning = False
        try:
            minutes = min(180, max(0, int(self.e_duration.get())))
        except Exception:
            # Spinbox'a elle "3o" gibi bozuk deger girilmis olabilir; sessizce
            # suresiz baslatmak yaziyi niyetten ayirt edilemez kilardi.
            minutes = 0
            parse_warning = True
        self._exam_deadline = (datetime.now() + timedelta(minutes=minutes)) if minutes else None
        # Sinav gecmisi "sureli miydi" diyebilsin diye KAYDEDILIR; yoksa
        # sonradan bunu bilmenin yolu yok (bozuk deger -> 0 = suresiz, cunku
        # sinav gercekten suresiz basladi).
        try:
            self.store.set_exam_time_limit(exam_id, minutes * 60)
        except Exception:
            pass
        self._start_exam_countdown()
        if parse_warning:
            # Uyari zamanlayici etiketinde kalir; exam_status'u _show_question
            # hemen soru sayaciyla ezdigi icin oraya yazmak ise yaramazdi.
            try:
                self.exam_timer_label.config(text=self._t("⏱ Süre anlaşılamadı — süresiz", "⏱ Duration not understood — untimed"), fg=MUTED)
            except Exception:
                pass
        self._show_question()

    def _start_exam_countdown(self):
        self._cancel_exam_countdown()
        if self._exam_deadline is None:
            try:
                self.exam_timer_label.config(text="")
            except Exception:
                pass
            return
        self._tick_exam_countdown()

    def _cancel_exam_countdown(self):
        job = getattr(self, "_exam_timer_job", None)
        if job is not None:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._exam_timer_job = None

    def _tick_exam_countdown(self):
        self._exam_timer_job = None
        # Sinav bittiyse/panel yok edildiyse sessizce dur (after guvenligi).
        if not self._exam_id or self._exam_deadline is None:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        remaining = int((self._exam_deadline - datetime.now()).total_seconds())
        mins, secs = divmod(max(0, remaining), 60)
        try:
            self.exam_timer_label.config(text=f"⏱ {mins:02d}:{secs:02d}",
                                         fg=DANGER if remaining <= 60 else GREEN)
        except Exception:
            pass
        if remaining <= 0:
            self._finish_exam(timed_out=True)
            return
        self._exam_timer_job = self.after(1000, self._tick_exam_countdown)

    def _show_question(self):
        if not self._exam_items or self._exam_idx >= len(self._exam_items):
            self._finish_exam()
            return
        it = self._exam_items[self._exam_idx]
        self._q_shown_at = datetime.now()
        self._set_text(self.e_question, it["question_text"] or "")
        self._set_text(self.e_reveal, "")
        self.e_answer.set("")
        self._build_exam_choices(it)
        self._show_exam_visual(it)
        self._clear_scratch()
        self._status(self.exam_status,
                     f"Soru {self._exam_idx + 1}/{len(self._exam_items)}   "
                     f"[{it['course'] or '-'} / {it['topic'] or '-'} / {it['difficulty'] or '-'}]",
                     ACCENT)

    def _reveal(self):
        if not self._exam_items or self._exam_idx >= len(self._exam_items):
            return
        it = self._exam_items[self._exam_idx]
        correct = it["answer_text"] or "(bu soru için kayıtlı cevap yok)"
        if self._exam_correct_choice:
            # Multiple choice: the letter comparison is definitive.
            sel = (self.e_answer.get() or "").strip().upper()[:1]
            ok = sel == self._exam_correct_choice
            hint = (f"Doğru şık: {self._exam_correct_choice}   •   senin seçimin: {sel or '-'}"
                    f"   →   {'DOĞRU ✔' if ok else 'YANLIŞ ✘'}")
            self._color_choices_after_reveal()
            body = f"Doğru cevap:\n{self._exam_correct_choice}) " + (correct if correct else "")
            self._set_text(self.e_reveal, f"{body}\n\n{hint}")
            return
        verdict = answer_verdict(self.e_answer.get(), it["answer_text"] or "")
        hint = {
            "match": "otomatik kontrol: EŞLEŞTİ ✔ (birebir aynı)",
            "equivalent": "otomatik kontrol: EŞDEĞER ✔ (farklı yazım, matematiksel olarak aynı)",
            "different": "otomatik kontrol: FARKLI görünüyor ✘ (yine de son kararı sen ver)",
            "unknown": "otomatik kontrol: karar verilemedi — sen karar ver",
        }[verdict]
        self._set_text(self.e_reveal, f"Doğru cevap:\n{correct}\n\nSenin cevabın:\n{self.e_answer.get()}\n\n{hint}")

    def _mark_exam(self, is_correct):
        if not self._exam_id or self._exam_idx >= len(self._exam_items):
            return
        it = self._exam_items[self._exam_idx]
        shown = getattr(self, "_q_shown_at", None)
        dur = int((datetime.now() - shown).total_seconds()) if shown else 0
        self.exams.answer(self._exam_id, it["question_id"], self.student_id,
                          self.e_answer.get(), is_correct, duration_sec=dur)
        self._next_question()

    def _next_question(self):
        self._exam_idx += 1
        if self._exam_idx >= len(self._exam_items):
            self._finish_exam()
        else:
            self._show_question()

    def _sinav_ozet_metni(self, res, dur, answered, timed_out):
        """Sınav özeti — EKRAN ve PANO aynı metni kullansın diye tek yerde."""
        baslik = (self._t("SINAV BİTTİ — ⏱ SÜRE DOLDU", "EXAM FINISHED — ⏱ TIME UP")
                  if timed_out else self._t("SINAV BİTTİ", "EXAM FINISHED"))
        eksik = ""
        if answered < res["question_count"]:
            eksik = self._t(
                f"Cevaplanmayan  : {res['question_count'] - answered} "
                "(puanda yanlış sayıldı; bankadaki durumu değişmedi)\n",
                f"Unanswered     : {res['question_count'] - answered} "
                "(counted wrong in the score; bank status unchanged)\n")
        govde = self._t(
            f"Soru sayısı : {res['question_count']}\n"
            f"Doğru       : {res['correct_count']}\n"
            f"Puan        : %{res['score']}\n"
            f"Süre        : {dur} sn\n",
            f"Questions   : {res['question_count']}\n"
            f"Correct     : {res['correct_count']}\n"
            f"Score       : {res['score']}%\n"
            f"Time        : {dur} s\n")
        kuyruk = self._t(
            "Yanlışların Soru Bankası'nda 'Yanlış' olarak işaretlendi — "
            "Havuz='Yanlış' seçip tekrar sınav yapabilirsin.",
            "Your wrong answers are marked 'Wrong' in the question bank — "
            "pick Pool='Wrong' to drill them again.")
        return f"{baslik}\n\n{govde}{eksik}\n{kuyruk}"

    def _sinav_ozeti_panoya(self):
        """📋 Sınav özetini panoya kopyalar (paylaşmak/not almak için)."""
        metin = getattr(self, "_son_sinav_ozeti", "")
        if not metin:
            self._status(self.exam_status,
                         self._t("Önce bir sınavı bitir.", "Finish an exam first."), MUTED)
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(metin)
            self._status(self.exam_status,
                         self._t("Sınav özeti panoya kopyalandı.",
                                 "Exam summary copied to the clipboard."), GREEN)
        except Exception as exc:
            self._status(self.exam_status,
                         self._t(f"Kopyalanamadı: {exc}", f"Could not copy: {exc}"), DANGER)

    def _finish_exam(self, timed_out=False):
        if not self._exam_id:
            self._status(self.exam_status, self._t("Aktif sınav yok.", "No active exam."), MUTED)
            return
        self._cancel_exam_countdown()
        self._exam_deadline = None
        try:
            self.exam_timer_label.config(text=self._t("⏱ Süre doldu!", "⏱ Time is up!") if timed_out else "")
        except Exception:
            pass
        dur = int((datetime.now() - self._exam_started).total_seconds()) if self._exam_started else 0
        res = self.exams.finish(self._exam_id, dur)
        self._set_text(self.e_question, "")
        for w in self.e_choice_frame.winfo_children():
            w.destroy()
        self._exam_choice_buttons = {}
        self._exam_correct_choice = ""
        self.e_image.config(image="", text="")
        self.e_image.image = None
        self._clear_scratch()
        # DB'deki gercek sayim: Atla ile gecilenler de cevaplanmamis sayilir
        # (_exam_idx bunlari cevaplandi sanardi).
        answered = res.get("answered_count", self._exam_idx)
        self._son_sinav_ozeti = self._sinav_ozet_metni(res, dur, answered, timed_out)
        self._set_text(self.e_reveal, self._son_sinav_ozeti)
        try:
            self.e_copy_btn.state(["!disabled"])
        except Exception:
            pass
        self._status(self.exam_status,
                     ("⏱ Süre doldu — " if timed_out else "Bitti: ") +
                     f"{res['correct_count']}/{res['question_count']}  •  %{res['score']}",
                     GREEN if res["score"] >= 50 else DANGER)
        self._exam_id, self._exam_items, self._exam_idx = None, [], 0
        self._refresh_bank(); self._refresh_stats()
        try:
            self._refresh_dashboard()
        except Exception:
            pass

    # ---- Tab 4: Stats ---- #
    def _build_stats_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text=self._t("İstatistik", "Statistics"))
        top = ttk.Frame(tab); top.pack(fill="x", padx=6, pady=6)
        ttk.Button(top, text=self._t("Yenile", "Refresh"), command=self._refresh_stats).pack(side="left")
        ttk.Button(top, text=self._t("📄 Haftalık Özet", "📄 Weekly summary"),
                   command=self._open_weekly_report).pack(side="left", padx=6)
        self.stats_status = tk.Label(top, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9))
        self.stats_status.pack(side="left", padx=8)
        # Graphical dashboard: weak topics jump out in red, exam trend at a glance.
        self.charts_holder = ttk.Frame(tab)
        self.charts_holder.pack(fill="x", padx=6)
        self._stats_fig = None
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            self._stats_fig = Figure(figsize=(9.4, 2.7), dpi=100, facecolor=BG)
            self._stats_canvas = FigureCanvasTkAgg(self._stats_fig, master=self.charts_holder)
            self._stats_canvas.get_tk_widget().pack(fill="x")
        except Exception:
            self._stats_fig = None
        ttk.Label(tab, text=self._t("Konu bazlı ustalık", "Mastery by topic"), style="Header.TLabel").pack(anchor="w", padx=6)
        cols = ("course", "topic", "total", "solved", "wrong", "acc")
        self.s_tree = ttk.Treeview(tab, columns=cols, show="headings", height=10)
        for c, t, w in (("course", "Kurs", 150), ("topic", "Konu", 130), ("total", "Soru", 60),
                        ("solved", "Çözdüm", 70), ("wrong", "Yanlış", 66), ("acc", "Doğruluk %", 86)):
            self.s_tree.heading(c, text=t)
            self.s_tree.column(c, width=w, anchor="w")
        self.s_tree.pack(fill="both", expand=True, padx=6, pady=2)
        ttk.Label(tab, text=self._t("Sınavlar — satıra çift tıkla, soru dökümü açılsın", "Exams — double-click a row for the question breakdown"),
                  style="Header.TLabel").pack(anchor="w", padx=6)
        ecols = ("date", "title", "count", "score", "dur", "timed")
        self.exam_tree = ttk.Treeview(tab, columns=ecols, show="headings", height=7)
        for c, t, w in (("date", "Tarih", 96), ("title", "Sınav", 230),
                        ("count", "Soru", 60), ("score", "Puan", 70),
                        ("dur", "Süre", 90), ("timed", "Süreli mi?", 84)):
            self.exam_tree.heading(c, text=t)
            self.exam_tree.column(c, width=w, anchor="w" if c == "title" else "center")
        self.exam_tree.pack(fill="both", expand=True, padx=6, pady=2)
        self.exam_tree.bind("<Double-1>", lambda e: self._open_exam_detail())
        self.exam_tree.bind("<Return>", lambda e: self._open_exam_detail())
        self._exam_rows = []

        ttk.Label(tab, text=self._t("Zayıf konular + son sınavlar", "Weak topics + recent exams"), style="Header.TLabel").pack(anchor="w", padx=6)
        self.s_text = tk.Text(tab, height=8, wrap="word", bg=PANEL_BG, fg=FG,
                              relief="flat", font=("Consolas", 10))
        self.s_text.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.s_text.config(state="disabled")

    def _draw_stats_charts(self):
        """Two live charts: per-topic accuracy (weak topics red) + exam trend."""
        if self._stats_fig is None:
            return
        fig = self._stats_fig
        fig.clear()
        topics = [r for r in self.stats.by_topic(self.student_id) if r["graded"] > 0]
        topics.sort(key=lambda r: r["graded"], reverse=True)
        topics = topics[:8]
        exams = [e for e in self.store.list_exams(self.student_id, limit=15)
                 if e["status"] == "finished"]
        exams.reverse()   # chronological
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor(PANEL_BG)
        if topics:
            labels = [f"{(r['topic'] or '-')[:16]}" for r in topics][::-1]
            accs = [r["accuracy"] for r in topics][::-1]
            colors = ["#C0392B" if a < 50 else ("#D97706" if a < 75 else "#16A55A")
                      for a in accs]
            ax1.barh(labels, accs, color=colors, height=0.62)
            ax1.set_xlim(0, 100)
            # tick/baslik/spine renkleri FG/MUTED'dan: matplotlib varsayilani
            # siyahtir ve koyu temada grafik yazilari okunmazdi.
            ax1.tick_params(labelsize=7, colors=FG)
            for spine in ("top", "right"):
                ax1.spines[spine].set_visible(False)
            for spine in ("left", "bottom"):
                ax1.spines[spine].set_color(MUTED)
        else:
            ax1.text(0.5, 0.5, "Henüz çözülmüş soru yok", ha="center", va="center",
                     fontsize=9, color=MUTED)
            ax1.set_xticks([]); ax1.set_yticks([])
        ax1.set_title("Konu doğruluğu %  (kırmızı = zayıf)", fontsize=8, color=FG)
        ax2 = fig.add_subplot(122)
        ax2.set_facecolor(PANEL_BG)
        if len(exams) >= 2:
            scores = [float(e["score"] or 0) for e in exams]
            ax2.plot(range(1, len(scores) + 1), scores, marker="o", color="#E07B39",
                     linewidth=2, markersize=4)
            ax2.set_ylim(0, 105)
            ax2.axhline(50, color="#C0392B", linewidth=0.7, linestyle="--", alpha=0.5)
            ax2.tick_params(labelsize=7, colors=FG)
            for spine in ("top", "right"):
                ax2.spines[spine].set_visible(False)
            for spine in ("left", "bottom"):
                ax2.spines[spine].set_color(MUTED)
        else:
            ax2.text(0.5, 0.5, "Trend için en az 2 sınav gerekli", ha="center", va="center",
                     fontsize=9, color=MUTED)
            ax2.set_xticks([]); ax2.set_yticks([])
        ax2.set_title("Sınav puanı trendi", fontsize=8, color=FG)
        try:
            fig.tight_layout()
        except Exception:
            pass
        try:
            self._stats_canvas.draw()
        except Exception:
            pass

    def _refresh_stats(self):
        try:
            self._draw_stats_charts()
        except Exception:
            pass
        rows = self.stats.by_topic(self.student_id)
        self.s_tree.delete(*self.s_tree.get_children())
        for r in rows:
            self.s_tree.insert("", "end", values=(r["course"], r["topic"], r["total"],
                                                  r["solved"], r["wrong"], r["accuracy"]))
        o = self.stats.overview(self.student_id)
        lines = [f"Genel: {o['solved']} çözdüm / {o['wrong']} yanlış / {o['unsolved']} denenmemiş"
                 f"   •   doğruluk %{o['accuracy']}   •   sınav ort. %{o['avg_score']}", ""]
        weak = self.stats.weak_topics(self.student_id)
        lines.append("Zayıf konular (önce bunları çalış):")
        if weak:
            for w in weak:
                lines.append(f"  • {w['course']} / {w['topic']}  →  %{w['accuracy']} "
                             f"({w['solved']}✔ {w['wrong']}✘)")
        else:
            lines.append("  (henüz yeterli veri yok)")
        lines.append("")
        lines.append("Son sınavlar:")
        exams = [e for e in self.store.list_exams(self.student_id, limit=10) if e["status"] == "finished"]
        if exams:
            for e in exams:
                lines.append(f"  • {e['created_at']}  {e['title']}  →  "
                             f"{e['correct_count']}/{e['question_count']}  %{e['score']}")
        else:
            lines.append("  (henüz bitmiş sınav yok)")
        self._set_text(self.s_text, "\n".join(lines))
        self._refresh_exam_list()

    # ------------------------------------------------- Sınavlar alt görünümü --
    def _refresh_exam_list(self):
        """Geçmiş sınavlar tablosu (tarih · başlık · soru · puan · süre · süreli mi)."""
        tree = getattr(self, "exam_tree", None)
        if tree is None:
            return
        tree.delete(*tree.get_children())
        self._exam_rows = [e for e in self.store.list_exams(self.student_id, limit=200)
                           if e["status"] == "finished"]
        for i, e in enumerate(self._exam_rows):
            tree.insert("", "end", iid=str(i), values=(
                (e["finished_at"] or e["created_at"] or "")[:16],
                e["title"] or "-",
                f"{e['correct_count'] or 0}/{e['question_count'] or 0}",
                f"%{round(float(e['score'] or 0), 1):g}",
                _sure_metni(e["duration_sec"]),
                sinav_sure_modu(e)))

    def _open_exam_detail(self):
        """Seçili sınavın soru dökümü: hangi soruda ne kadar kalındı, doğru/yanlış."""
        sec = self.exam_tree.selection()
        if not sec:
            return
        try:
            e = self._exam_rows[int(sec[0])]
        except Exception:
            return
        satirlar = self.store.exam_detail(e["id"])
        win = tk.Toplevel(self)
        win.title(f"Sınav dökümü — {e['title'] or '-'}")
        win.geometry("980x560")
        win.configure(bg=BG)
        tk.Label(win, text=f"{e['title'] or '-'}", bg=BG, fg=FG,
                 font=("Segoe UI Semibold", 13)).pack(anchor="w", padx=12, pady=(10, 0))
        tk.Label(win, text=(f"{(e['finished_at'] or e['created_at'] or '')[:16]}  ·  "
                            f"{e['correct_count'] or 0}/{e['question_count'] or 0} doğru  ·  "
                            f"puan %{round(float(e['score'] or 0), 1):g}  ·  "
                            f"toplam süre {_sure_metni(e['duration_sec'])}  ·  "
                            f"süreli mi: {sinav_sure_modu(e)}"),
                 bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(0, 8))
        cols = ("no", "soru", "cevabin", "dogru_cevap", "sonuc", "sure")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c, t, w in (("no", "#", 34), ("soru", "Soru", 340), ("cevabin", "Cevabın", 130),
                        ("dogru_cevap", "Doğru cevap", 130), ("sonuc", "Sonuç", 74),
                        ("sure", "Süre", 84)):
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor="w" if c in ("soru", "cevabin", "dogru_cevap")
                        else "center")
        kaydirma = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=kaydirma.set)
        tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        kaydirma.pack(side="right", fill="y", pady=(0, 12), padx=(0, 12))
        tree.tag_configure("dogru", foreground=GREEN)
        tree.tag_configure("yanlis", foreground=DANGER)
        tree.tag_configure("bos", foreground=MUTED)
        for r in satirlar:
            metin = " ".join((r["question_text"] or "").split())
            cevaplandi = bool(r["answered_at"])
            if not cevaplandi:
                sonuc, etiket = "atlandı", "bos"
            elif r["is_correct"]:
                sonuc, etiket = "✔ doğru", "dogru"
            else:
                sonuc, etiket = "✘ yanlış", "yanlis"
            tree.insert("", "end", tags=(etiket,), values=(
                (r["order_index"] or 0) + 1,
                metin[:120] + ("…" if len(metin) > 120 else ""),
                (r["user_answer"] or "—")[:40],
                (r["answer_text"] or "—")[:40],
                sonuc,
                _sure_metni(r["duration_sec"])))

    def _open_weekly_report(self):
        """📄 Haftalık Özet — tarayıcıda açılan tek sayfa HTML rapor."""
        ogrenci = self.store.get_student(self.student_id)
        ok, sonuc = haftalik_rapor_ac(self.store, self.student_id,
                                      ogrenci_adi=(ogrenci["name"] if ogrenci else ""),
                                      lang=getattr(self, "lang", "tr"))
        try:
            self.stats_status.config(
                text=(self._t("Rapor tarayıcıda açıldı.", "Report opened in your browser.")
                      if ok else self._t(f"Rapor açılamadı: {sonuc}", f"Could not open report: {sonuc}")),
                fg=(GREEN if ok else DANGER))
        except Exception:
            pass
        self._refresh_overview()
        self.e_course["values"] = [""] + self.store.distinct_values("course")
        self.e_topic["values"] = [""] + self.store.distinct_values("topic")
