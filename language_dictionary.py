# -*- coding: utf-8 -*-
"""
Language & Science Dictionary / Dil ve Bilim Sözlüğü
====================================================

Upgrades the old Science Dictionary into an offline-first language assistant:
local SQLite dictionary, search history, frequent words, favorites, sentence
translation, image (OCR/Vision) translation, a personal PDF-terms notebook, and
LM-Studio model profiles — all degrading safely when LM Studio is closed or has
no model loaded.

The logic layer (stores, profile manager, translation client, image pipeline)
has NO Tkinter dependency so it is fully unit-testable head-less. Only
LanguageDictionaryPanel touches Tk.
"""

import os
import csv
import json
import re
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

import app_paths as _app_paths
from mca_common import guard_url as _mca_guard_url

# User data lives in %APPDATA%\MathCourseAI\data (moved there in V43 so it
# survives program moves and rebuilds). app_paths copies the old project-folder
# databases over automatically on first run.
try:
    from app_paths import DATA_DIR
except Exception:  # pragma: no cover — headless fallback
    import os as _os
    DATA_DIR = Path(_os.getenv("APPDATA") or Path.home()) / "MathCourseAI" / "data"
DB_PATH = DATA_DIR / "language_dictionary.sqlite"
DEFAULT_BASE_URL = "http://127.0.0.1:1234"

# ---- LM Studio model profiles ----
# These are STARTING POINTS, not fixed wiring. Three layers can override them,
# most specific first:
#   1. model_profiles.json in DATA_DIR (edit without touching code)
#   2. profiles saved in SQLite (set from the UI)
#   3. these defaults
# Whatever wins is then resolved against the models actually installed
# (match_model + PROFILE_KEYWORDS), so a removed model degrades instead of breaking.
DEFAULT_PROFILES = {
    "translation": "qwen/qwen3-v1-8b",
    "high_quality_translation": "gemma-4-12b-qat",
    "vision_translation": "moondream-2b-2025-04-14",
    "math": "qwen2.5-math-7b-instruct",
    "bio_dictionary": "biomistral-7b",
    "finance_dictionary": "gemma-4-12b-qat",
    "general_fallback": "gemma-4-12b-qat",
}

# Optional JSON override: {"math": ["qwen2.5-math", "gemma-4-12b"], ...}
PROFILE_OVERRIDE_FILE = "model_profiles.json"

PROFILE_PURPOSE = {
    "translation": "Dictionary + fast sentence translation",
    "high_quality_translation": "High quality academic translation",
    "vision_translation": "Image OCR / vision text extraction",
    "math": "Math terms / Visual Math Lab",
    "bio_dictionary": "Biology / genomics terms",
    "finance_dictionary": "Finance terms (optional)",
    "general_fallback": "General fallback model",
}

# Ordered fallback patterns per profile, best first. Matching is substring-based, so
# "gemma-4-12b" finds both "gemma-4-12b-qat" and "google/gemma-4-12b-qat".
#
# WARNING about ordering: a bare "mistral" used to sit in high_quality_translation.
# Once mistral-small was uninstalled that pattern matched **biomistral-7b** — a
# biomedical model silently doing academic translation. Broad patterns must therefore
# come AFTER specific ones, and every list ends with a general-purpose model.
PROFILE_KEYWORDS = {
    "translation": ["qwen3-v1", "qwen3", "qwen2.5-7b", "qwen2.5", "qwen",
                    "gemma-4-12b", "gemma-4", "gemma"],
    "high_quality_translation": ["gemma-4-12b", "gemma-4", "gemma",
                                 "mistral-small-3.2", "mistral-small"],
    "vision_translation": ["moondream", "gemma-4-12b", "gemma-4-e4b",
                           "qwen2.5-vl", "qwen3-vl", "qwen2-vl", "llava", "-vl"],
    "math": ["qwen2.5-math", "qwen-math", "mathstral", "math",
             "gemma-4-12b", "gemma-4", "gemma"],
    "bio_dictionary": ["biomistral", "bio-mistral", "bio",
                       "gemma-4-12b", "gemma-4", "gemma"],
    "finance_dictionary": ["finance-llm", "finma",
                           "gemma-4-12b", "gemma-4", "gemma"],
    "general_fallback": ["gemma-4-12b", "gemma-4", "gemma", "gemma-4-e4b",
                         "meta-llama-3", "llama-3", "llama"],
}

# Optional vision models we may recommend (info only — not required).
RECOMMENDED_VISION = [
    ("Qwen2.5-VL-7B-Instruct", "Better image translation / OCR"),
    ("Qwen2.5-VL-3B-Instruct", "Lightweight vision alternative"),
    ("Qwen2.5-VL-32B-Instruct", "High-quality heavy vision"),
]

NO_SERVER_MSG = (
    "LM Studio server is not reachable. You can keep using the local dictionary, "
    "history and favorites.\n"
    "LM Studio sunucusuna ulaşılamıyor. Yerel sözlük, geçmiş ve favorileri "
    "kullanmaya devam edebilirsiniz."
)
NO_MODEL_MSG = (
    "LM Studio server is running, but no model is loaded. Please load a model first.\n"
    "LM Studio sunucusu çalışıyor ancak yüklü model yok. Lütfen önce bir model yükleyin."
)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _compact_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _clip_text(text, limit=80):
    text = _compact_text(text).strip(" \t\r\n\"'“”‘’.,;:")
    return text[:limit].rstrip()


def _row_value(row, key, default=""):
    try:
        if isinstance(row, dict):
            value = row.get(key, default)
        elif hasattr(row, "keys") and key in row.keys():
            value = row[key]
        else:
            return default
        return default if value is None else value
    except Exception:
        return default


def extract_short_translation(query, result):
    """Extract a compact Turkish meaning from a longer dictionary response."""
    try:
        text = _compact_text(result)
        if not text:
            return ""
        low = text.lower()
        if text == "(pending)" or "lm studio server is not reachable" in low:
            return ""
        if "no model is loaded" in low or low.startswith("ai request failed"):
            return ""

        for arrow in ("→", "->", "=>", ":"):
            if arrow in text and len(text.split(arrow, 1)[0]) <= max(60, len(query or "") + 30):
                rhs = text.split(arrow, 1)[1]
                rhs = re.split(r"(?:\.|\n|;)", rhs, 1)[0]
                short = _clip_text(rhs)
                if short:
                    return short

        quote_patterns = [
            r"'([^']{1,60})'",
            r'"([^"]{1,60})"',
            r"“([^”]{1,60})”",
            r"‘([^’]{1,60})’",
        ]
        if "türkçede" in low or "turkish" in low or "türkçe" in low:
            quoted = []
            for pattern in quote_patterns:
                quoted.extend(_clip_text(m) for m in re.findall(pattern, text, flags=re.IGNORECASE))
            quoted = [q for q in quoted if q and _norm(q) != _norm(query)]
            if quoted:
                return " / ".join(quoted[:4])

        label_patterns = [
            r"(?:turkish(?:\s+(?:translation|meaning))?|türkçe(?:\s+(?:karşılık|anlam))?)\s*[:\-]\s*([^.;\n]{1,100})",
            r"(?:çeviri|translation|meaning|anlam)\s*[:\-]\s*([^.;\n]{1,100})",
        ]
        for pattern in label_patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                short = _clip_text(m.group(1))
                if short:
                    return short

        first = re.split(r"(?:\n|[.!?])", text, 1)[0]
        return _clip_text(first or text)
    except Exception:
        return _clip_text(result)


def match_model(models, preferred="", keywords=None):
    """Pick the best available model id for a preferred name + keyword hints."""
    if not models:
        return preferred or ""
    preferred = (preferred or "").strip()
    if preferred and preferred.lower() != "auto":
        pn = _norm(preferred)
        for m in models:
            if pn and pn == _norm(m):
                return m
        for m in models:
            if preferred.lower() in m.lower() or (pn and pn in _norm(m)):
                return m
    for kw in (keywords or []):
        kn = _norm(kw)
        for m in models:
            if kw.lower() in m.lower() or (kn and kn in _norm(m)):
                return m
    return models[0] if models else (preferred or "")


# ===========================================================================
# DictionaryStore (SQLite) — terms + pdf_terms + model_profiles
# ===========================================================================
class DictionaryStore:
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

    def _create_tables(self):
        with self._lock:
            c = self.conn
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT, lang TEXT, translation TEXT, definition TEXT,
                    category TEXT, example TEXT, source TEXT,
                    tr_explanation TEXT, en_explanation TEXT,
                    favorite INTEGER DEFAULT 0, search_count INTEGER DEFAULT 0,
                    model_used TEXT, note TEXT, hidden_from_frequent INTEGER DEFAULT 0,
                    created_at TEXT, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT, source_lang TEXT, target_lang TEXT,
                    result TEXT, translation TEXT, short_translation TEXT,
                    category TEXT, source_context TEXT,
                    model_used TEXT, timestamp TEXT
                );
                CREATE TABLE IF NOT EXISTS sentence_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_text TEXT, translated_text TEXT,
                    source_lang TEXT, target_lang TEXT,
                    model_used TEXT, timestamp TEXT
                );
                CREATE TABLE IF NOT EXISTS image_translation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT, extracted_text TEXT, translated_text TEXT,
                    vision_model_used TEXT, translation_model_used TEXT, timestamp TEXT
                );
                CREATE TABLE IF NOT EXISTS pdf_terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT, translation TEXT, definition TEXT, category TEXT,
                    source_pdf TEXT, page_number INTEGER, note TEXT,
                    difficulty TEXT DEFAULT 'medium', learned INTEGER DEFAULT 0,
                    review_count INTEGER DEFAULT 0, last_reviewed TEXT,
                    favorite INTEGER DEFAULT 0, created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS model_profiles (
                    profile_name TEXT PRIMARY KEY,
                    model_name TEXT, purpose TEXT, updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS extracted_vocabulary_terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT, lemma TEXT, translation TEXT,
                    cefr_level TEXT, difficulty_score INTEGER DEFAULT 0,
                    tags TEXT, category TEXT, source_pdf TEXT, page_number INTEGER,
                    frequency INTEGER DEFAULT 1, context_sentence TEXT,
                    status TEXT DEFAULT 'new', added_to_dictionary INTEGER DEFAULT 0,
                    favorite INTEGER DEFAULT 0, learned INTEGER DEFAULT 0,
                    created_at TEXT, updated_at TEXT,
                    UNIQUE(term, source_pdf)
                );
                CREATE TABLE IF NOT EXISTS pdf_vocabulary_scan_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_pdf TEXT UNIQUE, pdf_hash TEXT, modified_time TEXT,
                    page_count INTEGER DEFAULT 0, scanned_at TEXT,
                    term_count INTEGER DEFAULT 0, status TEXT DEFAULT 'ok'
                );
                CREATE TABLE IF NOT EXISTS technical_vocabulary_overrides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT UNIQUE, translation TEXT, category TEXT,
                    difficulty_level TEXT, tags TEXT, user_note TEXT, created_at TEXT
                );
                CREATE TABLE IF NOT EXISTS dictionary_ai_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT, question TEXT, answer TEXT, model TEXT,
                    created_at TEXT, source_language TEXT, target_language TEXT,
                    source_context TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_terms_term ON terms(term);
                CREATE INDEX IF NOT EXISTS idx_vocab_term ON extracted_vocabulary_terms(term);
                """
            )
            self._migrate_existing_tables()
            c.execute("CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query)")
            c.commit()

    def _ensure_columns(self, table, columns):
        existing = {
            row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, definition in columns.items():
            if name in existing:
                continue
            try:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
            except sqlite3.OperationalError as exc:
                if "duplicate column" not in str(exc).lower():
                    raise

    def _migrate_existing_tables(self):
        self._ensure_columns("search_history", {
            "source_lang": "TEXT",
            "target_lang": "TEXT",
            "result": "TEXT",
            "translation": "TEXT",
            "short_translation": "TEXT",
            "category": "TEXT",
            "source_context": "TEXT",
            "model_used": "TEXT",
            "timestamp": "TEXT",
        })
        self._ensure_columns("terms", {
            "term": "TEXT",
            "lang": "TEXT",
            "translation": "TEXT",
            "definition": "TEXT",
            "category": "TEXT",
            "example": "TEXT",
            "source": "TEXT",
            "tr_explanation": "TEXT",
            "en_explanation": "TEXT",
            "favorite": "INTEGER DEFAULT 0",
            "search_count": "INTEGER DEFAULT 0",
            "model_used": "TEXT",
            "note": "TEXT",
            "hidden_from_frequent": "INTEGER DEFAULT 0",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        })
        self._ensure_columns("pdf_terms", {
            "term": "TEXT",
            "translation": "TEXT",
            "definition": "TEXT",
            "category": "TEXT",
            "source_pdf": "TEXT",
            "page_number": "INTEGER",
            "note": "TEXT",
            "difficulty": "TEXT DEFAULT 'medium'",
            "learned": "INTEGER DEFAULT 0",
            "review_count": "INTEGER DEFAULT 0",
            "last_reviewed": "TEXT",
            "favorite": "INTEGER DEFAULT 0",
            "created_at": "TEXT",
        })
        # PDF Vocabulary Scanner tables (safe on old databases).
        for tbl in ("extracted_vocabulary_terms", "pdf_vocabulary_scan_cache",
                    "technical_vocabulary_overrides"):
            try:
                self.conn.execute(f"SELECT 1 FROM {tbl} LIMIT 1")  # nosec B608 - tbl comes from the literal tuple above
            except sqlite3.OperationalError:
                continue
        self._ensure_columns("extracted_vocabulary_terms", {
            "term": "TEXT", "lemma": "TEXT", "translation": "TEXT", "cefr_level": "TEXT",
            "difficulty_score": "INTEGER DEFAULT 0", "tags": "TEXT", "category": "TEXT",
            "source_pdf": "TEXT", "page_number": "INTEGER", "frequency": "INTEGER DEFAULT 1",
            "context_sentence": "TEXT", "status": "TEXT DEFAULT 'new'",
            "added_to_dictionary": "INTEGER DEFAULT 0", "favorite": "INTEGER DEFAULT 0",
            "learned": "INTEGER DEFAULT 0", "created_at": "TEXT", "updated_at": "TEXT",
        })
        self._ensure_columns("pdf_vocabulary_scan_cache", {
            "source_pdf": "TEXT", "pdf_hash": "TEXT", "modified_time": "TEXT",
            "page_count": "INTEGER DEFAULT 0", "scanned_at": "TEXT",
            "term_count": "INTEGER DEFAULT 0", "status": "TEXT DEFAULT 'ok'",
        })
        self._ensure_columns("technical_vocabulary_overrides", {
            "term": "TEXT", "translation": "TEXT", "category": "TEXT",
            "difficulty_level": "TEXT", "tags": "TEXT", "user_note": "TEXT", "created_at": "TEXT",
        })
        # Dictionary "Ask AI about this term" Q&A log (safe on old databases).
        self._ensure_columns("dictionary_ai_questions", {
            "term": "TEXT", "question": "TEXT", "answer": "TEXT", "model": "TEXT",
            "created_at": "TEXT", "source_language": "TEXT", "target_language": "TEXT",
            "source_context": "TEXT",
        })

    # -- terms --
    def add_term(self, term, translation="", lang="en", definition="", category="",
                 example="", source="", tr_explanation="", en_explanation="",
                 model_used="", favorite=0):
        with self._lock:
            existing = self.get_term(term, lang)
            now = _now()
            if existing:
                self.conn.execute(
                    "UPDATE terms SET translation=?, definition=?, category=?, example=?, "
                    "source=?, tr_explanation=?, en_explanation=?, model_used=?, updated_at=? "
                    "WHERE id=?",
                    (translation or existing["translation"], definition or existing["definition"],
                     category or existing["category"], example or existing["example"],
                     source or existing["source"], tr_explanation or existing["tr_explanation"],
                     en_explanation or existing["en_explanation"], model_used or existing["model_used"],
                     now, existing["id"]))
                self.conn.commit()
                return existing["id"]
            cur = self.conn.execute(
                "INSERT INTO terms (term, lang, translation, definition, category, example, "
                "source, tr_explanation, en_explanation, model_used, favorite, search_count, "
                "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,0,?,?)",
                (term, lang, translation, definition, category, example, source,
                 tr_explanation, en_explanation, model_used, int(favorite), now, now))
            self.conn.commit()
            return cur.lastrowid

    def get_term(self, term, lang=None):
        with self._lock:
            if lang:
                row = self.conn.execute(
                    "SELECT * FROM terms WHERE lower(term)=lower(?) AND lang=? LIMIT 1",
                    (term, lang)).fetchone()
                if row:
                    return row
            return self.conn.execute(
                "SELECT * FROM terms WHERE lower(term)=lower(?) LIMIT 1", (term,)).fetchone()

    def search_terms(self, query, limit=50):
        with self._lock:
            q = f"%{(query or '').strip().lower()}%"
            return self.conn.execute(
                "SELECT * FROM terms WHERE lower(term) LIKE ? OR lower(translation) LIKE ? "
                "ORDER BY search_count DESC, term ASC LIMIT ?", (q, q, limit)).fetchall()

    def increment_search_count(self, term, lang=None):
        with self._lock:
            row = self.get_term(term, lang)
            if row:
                self.conn.execute("UPDATE terms SET search_count=search_count+1, updated_at=? WHERE id=?",
                                  (_now(), row["id"]))
                self.conn.commit()
                return row["search_count"] + 1
            return 0

    def set_favorite(self, term, favorite=True, lang=None, note=None):
        with self._lock:
            row = self.get_term(term, lang)
            if not row:
                self.add_term(term, lang=lang or "en")
                row = self.get_term(term, lang)
            if row:
                if note is not None:
                    self.conn.execute("UPDATE terms SET favorite=?, note=?, updated_at=? WHERE id=?",
                                      (1 if favorite else 0, note, _now(), row["id"]))
                else:
                    self.conn.execute("UPDATE terms SET favorite=?, updated_at=? WHERE id=?",
                                      (1 if favorite else 0, _now(), row["id"]))
                self.conn.commit()
                return True
            return False

    def _row_dict_with_display_translation(self, row):
        data = {k: row[k] for k in row.keys()}
        data["display_translation"] = self.display_translation_for(
            data.get("term", ""), data)
        return data

    def latest_history_translation(self, term):
        with self._lock:
            row = self.conn.execute(
                "SELECT translation, short_translation, result FROM search_history "
                "WHERE lower(query)=lower(?) ORDER BY id DESC LIMIT 1",
                (term or "",)).fetchone()
            if not row:
                return ""
            return (_row_value(row, "translation") or
                    _row_value(row, "short_translation") or
                    extract_short_translation(term, _row_value(row, "result")))

    def display_translation_for(self, term, row=None):
        direct = _row_value(row, "translation") if row is not None else ""
        if direct:
            return direct
        return self.latest_history_translation(term)

    def list_favorites(self, limit=200):
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM terms WHERE favorite=1 ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            return [self._row_dict_with_display_translation(r) for r in rows]

    def list_frequent(self, limit=50):
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM terms WHERE search_count > 0 AND COALESCE(hidden_from_frequent,0)=0 "
                "ORDER BY search_count DESC, term ASC LIMIT ?", (limit,)).fetchall()
            return [self._row_dict_with_display_translation(r) for r in rows]

    # -- Frequent / Favorites management -- #
    def get_term_by_text(self, term, lang=None):
        row = self.get_term(term, lang)
        return self._row_dict_with_display_translation(row) if row else None

    def update_term(self, term, translation="", definition="", category="",
                    source="", note="", lang=None):
        with self._lock:
            row = self.get_term(term, lang)
            if not row:
                return False
            self.conn.execute(
                "UPDATE terms SET translation=?, definition=?, category=?, source=?, note=?, "
                "updated_at=? WHERE id=?",
                (translation, definition, category, source, note, _now(), row["id"]))
            self.conn.commit()
            return True

    def reset_search_count(self, term, lang=None):
        with self._lock:
            cur = self.conn.execute(
                "UPDATE terms SET search_count=0, updated_at=? WHERE lower(term)=lower(?)",
                (_now(), term))
            self.conn.commit()
            return cur.rowcount > 0

    def hide_from_frequent(self, term, lang=None):
        with self._lock:
            cur = self.conn.execute(
                "UPDATE terms SET hidden_from_frequent=1, updated_at=? WHERE lower(term)=lower(?)",
                (_now(), term))
            self.conn.commit()
            return cur.rowcount > 0

    def unhide_from_frequent(self, term, lang=None):
        with self._lock:
            cur = self.conn.execute(
                "UPDATE terms SET hidden_from_frequent=0, updated_at=? WHERE lower(term)=lower(?)",
                (_now(), term))
            self.conn.commit()
            return cur.rowcount > 0

    def clear_all_frequent_counts(self):
        with self._lock:
            cur = self.conn.execute(
                "UPDATE terms SET search_count=0, updated_at=? WHERE search_count > 0", (_now(),))
            self.conn.commit()
            return cur.rowcount

    def clear_all_favorites(self):
        with self._lock:
            cur = self.conn.execute(
                "UPDATE terms SET favorite=0, updated_at=? WHERE favorite=1", (_now(),))
            self.conn.commit()
            return cur.rowcount

    def delete_term(self, term, lang=None):
        with self._lock:
            cur = self.conn.execute("DELETE FROM terms WHERE lower(term)=lower(?)", (term,))
            self.conn.commit()
            return cur.rowcount > 0

    def add_term_to_pdf_terms(self, term, translation, source_pdf="", page_number=None, note=""):
        return self.add_pdf_term(term=term, translation=translation, source_pdf=source_pdf,
                                 page_number=int(page_number or 0), note=note)

    def add_term_to_history(self, term, translation, result="", model_used="manual",
                            category="", source_context=""):
        with self._lock:
            short = translation or extract_short_translation(term, result)
            cur = self.conn.execute(
                "INSERT INTO search_history (query, source_lang, target_lang, result, translation, "
                "short_translation, category, source_context, model_used, timestamp) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (term, "en", "tr", result or translation, translation, short, category,
                 source_context, model_used, _now()))
            self.conn.commit()
            return cur.lastrowid

    def count_terms(self):
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]

    def seed_terms(self, term_dicts):
        """Seed built-in terms once (skips if dictionary already populated)."""
        with self._lock:
            if self.count_terms() > 0:
                return 0
        n = 0
        for d in term_dicts or []:
            try:
                self.add_term(
                    term=d.get("en", ""), translation=d.get("tr", ""), lang="en",
                    category=d.get("category", ""), example=d.get("example", ""),
                    tr_explanation=d.get("tr_explanation", ""),
                    en_explanation=d.get("en_explanation", ""), source="built-in")
                n += 1
            except Exception:
                pass
        return n

    # -- pdf terms --
    def add_pdf_term(self, term, translation="", definition="", category="",
                     source_pdf="", page_number=0, note="", difficulty="medium"):
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO pdf_terms (term, translation, definition, category, source_pdf, "
                "page_number, note, difficulty, learned, review_count, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,0,0,?)",
                (term, translation, definition, category, source_pdf, int(page_number or 0),
                 note, difficulty, _now()))
            self.conn.commit()
            return cur.lastrowid

    #: Columns `update_pdf_term` may write. Anything else is refused rather
    #: than interpolated into SQL. Today's callers only pass literal keyword
    #: names, so this closes a latent identifier-injection point, not a live
    #: one — same guarantee student_tracker.update_question already gives.
    PDF_TERM_UPDATABLE = ("term", "translation", "definition", "category",
                          "source_pdf", "page_number", "note", "difficulty",
                          "learned", "review_count", "last_reviewed", "favorite")

    def update_pdf_term(self, term_id, **fields):
        if not fields:
            return False
        bilinmeyen = [k for k in fields if k not in self.PDF_TERM_UPDATABLE]
        if bilinmeyen:
            raise ValueError("update_pdf_term: bilinmeyen alan / unknown column: %s"
                             % ", ".join(sorted(bilinmeyen)))
        cols = ", ".join(f"{k}=?" for k in fields)
        with self._lock:
            self.conn.execute(f"UPDATE pdf_terms SET {cols} WHERE id=?",  # nosec B608 - column names validated against PDF_TERM_UPDATABLE above; values bound
                              (*fields.values(), term_id))
            self.conn.commit()
            return True

    def delete_pdf_term(self, term_id):
        with self._lock:
            self.conn.execute("DELETE FROM pdf_terms WHERE id=?", (term_id,))
            self.conn.commit()
            return True

    def list_pdf_terms(self, limit=500):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM pdf_terms ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()

    def mark_pdf_term_learned(self, term_id, learned=True):
        with self._lock:
            self.conn.execute(
                "UPDATE pdf_terms SET learned=?, last_reviewed=?, review_count=review_count+1 WHERE id=?",
                (1 if learned else 0, _now(), term_id))
            self.conn.commit()
            return True

    def export_pdf_terms_csv(self, path):
        rows = self.list_pdf_terms(limit=100000)
        fields = ["term", "translation", "definition", "category", "source_pdf",
                  "page_number", "note", "difficulty", "learned"]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({k: r[k] for k in fields})
        return len(rows)

    def import_pdf_terms_csv(self, path):
        n = 0
        with open(path, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                self.add_pdf_term(
                    term=row.get("term", ""), translation=row.get("translation", ""),
                    definition=row.get("definition", ""), category=row.get("category", ""),
                    source_pdf=row.get("source_pdf", ""), page_number=row.get("page_number", 0) or 0,
                    note=row.get("note", ""), difficulty=row.get("difficulty", "medium"))
                n += 1
        return n

    # -- model profiles --
    def get_profile(self, profile_name):
        with self._lock:
            row = self.conn.execute(
                "SELECT model_name FROM model_profiles WHERE profile_name=?", (profile_name,)).fetchone()
            return row["model_name"] if row else None

    def set_profile(self, profile_name, model_name, purpose=""):
        with self._lock:
            self.conn.execute(
                "INSERT INTO model_profiles (profile_name, model_name, purpose, updated_at) "
                "VALUES (?,?,?,?) ON CONFLICT(profile_name) DO UPDATE SET model_name=excluded.model_name, "
                "purpose=excluded.purpose, updated_at=excluded.updated_at",
                (profile_name, model_name, purpose, _now()))
            self.conn.commit()
            return True

    def all_profiles(self):
        with self._lock:
            return {r["profile_name"]: r["model_name"]
                    for r in self.conn.execute("SELECT profile_name, model_name FROM model_profiles").fetchall()}

    # -- dictionary AI questions --
    def add_ai_question(self, term, question, answer, model="",
                        source_language="", target_language="",
                        source_context="dictionary_ai_question"):
        """Log one Ask-AI-about-this-term Q&A. Returns the new row id."""
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO dictionary_ai_questions "
                "(term, question, answer, model, created_at, source_language, "
                "target_language, source_context) VALUES (?,?,?,?,?,?,?,?)",
                (term, question, answer, model, _now(), source_language,
                 target_language, source_context))
            self.conn.commit()
            return cur.lastrowid

    def list_ai_questions(self, term=None, limit=100):
        with self._lock:
            if term:
                return self.conn.execute(
                    "SELECT * FROM dictionary_ai_questions WHERE lower(term)=lower(?) "
                    "ORDER BY id DESC LIMIT ?", (term, limit)).fetchall()
            return self.conn.execute(
                "SELECT * FROM dictionary_ai_questions ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()


# ===========================================================================
# TranslationHistoryStore — history tables (shares the DictionaryStore conn)
# ===========================================================================
class TranslationHistoryStore:
    #: Columns `update_search_history` may write. Anything else is refused
    #: rather than interpolated into SQL — the same identifier allowlist rule
    #: student_tracker.update_question already applies.
    SEARCH_HISTORY_UPDATABLE = ("query", "source_lang", "target_lang", "result",
                                "translation", "short_translation", "category",
                                "source_context", "model_used", "timestamp")

    def __init__(self, store):
        self.store = store
        self.conn = store.conn
        self._lock = store._lock

    def add_search(self, query, source_lang, target_lang, result, model_used="",
                   translation="", short_translation="", category="", source_context=""):
        with self._lock:
            short = short_translation or translation or extract_short_translation(query, result)
            trans = translation or short
            cur = self.conn.execute(
                "INSERT INTO search_history (query, source_lang, target_lang, result, translation, "
                "short_translation, category, source_context, model_used, timestamp) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (query, source_lang, target_lang, result, trans, short, category,
                 source_context, model_used, _now()))
            self.conn.commit()
            return cur.lastrowid

    def update_search(self, history_id, result=None, model_used=None, translation=None,
                      short_translation=None, category=None, source_context=None):
        if not history_id:
            return False
        fields = {}
        if result is not None:
            fields["result"] = result
        if model_used is not None:
            fields["model_used"] = model_used
        if translation is not None:
            fields["translation"] = translation
        if short_translation is not None:
            fields["short_translation"] = short_translation
        elif result is not None and translation is None:
            short_translation = extract_short_translation("", result)
            fields["short_translation"] = short_translation
            fields["translation"] = short_translation
        if category is not None:
            fields["category"] = category
        if source_context is not None:
            fields["source_context"] = source_context
        if not fields:
            return False
        bilinmeyen = [k for k in fields if k not in self.SEARCH_HISTORY_UPDATABLE]
        if bilinmeyen:
            raise ValueError("update_search_history: bilinmeyen alan / unknown column: %s"
                             % ", ".join(sorted(bilinmeyen)))
        cols = ", ".join(f"{k}=?" for k in fields)
        with self._lock:
            self.conn.execute(f"UPDATE search_history SET {cols} WHERE id=?",  # nosec B608 - column names validated against SEARCH_HISTORY_UPDATABLE above; values bound
                              (*fields.values(), history_id))
            self.conn.commit()
            return True

    def list_search(self, limit=100):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM search_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    # -- history management (delete / clear / manual add / edit) -- #
    def get_search_history_item(self, history_id):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM search_history WHERE id=?", (history_id,)).fetchone()

    def delete_search_history_item(self, history_id):
        with self._lock:
            cur = self.conn.execute("DELETE FROM search_history WHERE id=?", (history_id,))
            self.conn.commit()
            return cur.rowcount > 0

    def delete_search_history_items(self, history_ids):
        ids = [int(i) for i in (history_ids or [])]
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with self._lock:
            cur = self.conn.execute(
                f"DELETE FROM search_history WHERE id IN ({placeholders})", ids)  # nosec B608 - placeholders is a run of "?"; ids are bound
            self.conn.commit()
            return cur.rowcount

    def clear_search_history(self):
        with self._lock:
            cur = self.conn.execute("DELETE FROM search_history")
            self.conn.commit()
            return cur.rowcount

    def add_search_history_item(self, query, result, translation="", short_translation="",
                                source_lang="en", target_lang="tr", model_used="manual",
                                category="manual", source_context=""):
        return self.add_search(query, source_lang, target_lang, result,
                               model_used=model_used or "manual", translation=translation,
                               short_translation=short_translation,
                               category=category or "manual", source_context=source_context)

    def update_search_history_item(self, history_id, query, result, translation="",
                                   short_translation="", model_used="", category="",
                                   source_context=""):
        if not history_id:
            return False
        if not short_translation:
            short_translation = translation or extract_short_translation(query or "", result or "")
        with self._lock:
            cur = self.conn.execute(
                "UPDATE search_history SET query=?, result=?, translation=?, short_translation=?, "
                "model_used=?, category=?, source_context=? WHERE id=?",
                (query, result, translation or short_translation, short_translation,
                 model_used, category, source_context, history_id))
            self.conn.commit()
            return cur.rowcount > 0

    def add_sentence(self, source_text, translated_text, source_lang, target_lang, model_used=""):
        with self._lock:
            self.conn.execute(
                "INSERT INTO sentence_history (source_text, translated_text, source_lang, target_lang, "
                "model_used, timestamp) VALUES (?,?,?,?,?,?)",
                (source_text, translated_text, source_lang, target_lang, model_used, _now()))
            self.conn.commit()

    def list_sentence(self, limit=100):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM sentence_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def add_image(self, image_path, extracted_text, translated_text,
                  vision_model_used="", translation_model_used=""):
        with self._lock:
            self.conn.execute(
                "INSERT INTO image_translation_history (image_path, extracted_text, translated_text, "
                "vision_model_used, translation_model_used, timestamp) VALUES (?,?,?,?,?,?)",
                (image_path, extracted_text, translated_text, vision_model_used,
                 translation_model_used, _now()))
            self.conn.commit()

    def list_image(self, limit=100):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM image_translation_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()


# ===========================================================================
# LanguageModelProfileManager
# ===========================================================================
def load_profile_overrides(path=None):
    """Read model_profiles.json → {profile: [pattern, ...]}.

    Lets models be swapped without editing code. Missing file is the normal case
    (returns {}); a malformed file is ignored rather than raised, because a bad
    config must not stop the dictionary from working — it still has SQLite
    profiles, the built-in defaults and keyword matching behind it.
    """
    p = Path(path) if path else (DATA_DIR / PROFILE_OVERRIDE_FILE)
    try:
        if not p.exists():
            return {}
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f) or {}
    except Exception:
        return {}
    out = {}
    for key, value in raw.items():
        if key not in DEFAULT_PROFILES:
            continue
        if isinstance(value, str) and value.strip():
            out[key] = [value.strip()]
        elif isinstance(value, (list, tuple)):
            patterns = [str(v).strip() for v in value if str(v).strip()]
            if patterns:
                out[key] = patterns
    return out


class LanguageModelProfileManager:
    def __init__(self, store=None, overrides=None):
        self.store = store
        self._profiles = dict(DEFAULT_PROFILES)
        self._keywords = {k: list(v) for k, v in PROFILE_KEYWORDS.items()}

        # JSON overrides win over the built-in defaults and also replace the
        # keyword chain, so a user-chosen model is tried before anything else.
        for key, patterns in (overrides if overrides is not None
                              else load_profile_overrides()).items():
            self._profiles[key] = patterns[0]
            self._keywords[key] = patterns + [k for k in self._keywords.get(key, [])
                                              if k not in patterns]

        if store is not None:
            saved = store.all_profiles()
            for k, v in saved.items():
                if k in self._profiles and v:
                    self._profiles[k] = v
            # Persist defaults the first time.
            for k, v in DEFAULT_PROFILES.items():
                if k not in saved:
                    try:
                        store.set_profile(k, self._profiles[k], PROFILE_PURPOSE.get(k, ""))
                    except Exception:
                        pass

    def defaults(self):
        return dict(DEFAULT_PROFILES)

    def all(self):
        return dict(self._profiles)

    def get(self, profile):
        return self._profiles.get(profile, DEFAULT_PROFILES.get(profile, ""))

    def set(self, profile, model_name):
        self._profiles[profile] = model_name
        if self.store is not None:
            try:
                self.store.set_profile(profile, model_name, PROFILE_PURPOSE.get(profile, ""))
            except Exception:
                pass
        return True

    def keywords(self, profile):
        """Fallback chain for a profile (JSON overrides already merged in)."""
        return list(self._keywords.get(profile, PROFILE_KEYWORDS.get(profile, [])))

    def resolve(self, profile, available_models):
        """Best concrete model id for a profile given the loaded models."""
        return match_model(available_models, self.get(profile), self.keywords(profile))

    def suggest(self, available_models):
        return {p: match_model(available_models, self.get(p), self.keywords(p))
                for p in DEFAULT_PROFILES}


# ===========================================================================
# LMStudioTranslationClient — safe text translation / lookup
# ===========================================================================
class LMStudioTranslationClient:
    def __init__(self, base_url=DEFAULT_BASE_URL, profile_manager=None, complete_fn=None):
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.profiles = profile_manager or LanguageModelProfileManager()
        # complete_fn(system, user, model) -> (text, ok_bool); when None we POST ourselves.
        self.complete_fn = complete_fn

    @staticmethod
    def classify(reachable, models):
        if not reachable:
            return "no_server"
        if not models:
            return "no_model"
        return "connected"

    def list_models(self, timeout=6):
        import urllib.request
        try:
            hedef = _mca_guard_url(self.base_url + "/v1/models")
            with urllib.request.urlopen(hedef, timeout=timeout) as resp:  # nosec B310 - guard_url() allows only http(s)
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return True, [m.get("id", "") for m in data.get("data", []) if m.get("id")]
        except Exception:
            return False, []

    def server_status(self):
        reachable, models = self.list_models()
        return self.classify(reachable, models), models

    def _raw_complete(self, system_prompt, user_prompt, model, timeout=120):
        import urllib.request
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": user_prompt}],
            "temperature": 0.15, "top_p": 0.85, "max_tokens": 1024, "stream": False,
        }
        req = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            _mca_guard_url(req.full_url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - guard_url() allows only http(s)
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return text, True
        except Exception as exc:
            return f"AI request failed: {exc}", False

    def _complete(self, system_prompt, user_prompt, model):
        if self.complete_fn is not None:
            try:
                return self.complete_fn(system_prompt, user_prompt, model)
            except Exception as exc:
                return f"AI request failed: {exc}", False
        return self._raw_complete(system_prompt, user_prompt, model)

    def translate(self, text, source_lang="English", target_lang="Turkish",
                  profile="translation"):
        """Translate text. Returns (result_text, model_used, status)."""
        status, models = self.server_status()
        if status == "no_server":
            return NO_SERVER_MSG, "", "no_server"
        if status == "no_model":
            return NO_MODEL_MSG, "", "no_model"
        model = self.profiles.resolve(profile, models)
        system = (
            "You are a precise academic translator. Translate the following "
            f"{source_lang} educational/math/science text into clear {target_lang}. "
            "Preserve mathematical symbols, formulas, variable names, units, and "
            "formatting. Do not solve the problem unless asked. Return the translation "
            "and a short glossary of important terms."
        )
        out, ok = self._complete(system, text, model)
        return out, model, ("ok" if ok else "error")

    def lookup_word(self, term, source_lang="English", target_lang="Turkish",
                    profile="translation"):
        """Look up a single word/term. Returns (result_text, model_used, status)."""
        status, models = self.server_status()
        if status == "no_server":
            return NO_SERVER_MSG, "", "no_server"
        if status == "no_model":
            return NO_MODEL_MSG, "", "no_model"
        model = self.profiles.resolve(profile, models)
        system = (
            f"You are a bilingual {source_lang}-{target_lang} math/science dictionary. "
            f"For the given term give: the {target_lang} translation, a one-line "
            f"{target_lang} definition, the math/science context, and one short example. "
            "Keep it concise."
        )
        out, ok = self._complete(system, f"Term: {term}", model)
        return out, model, ("ok" if ok else "error")

    def ask_about_term(self, term, question, translation="", definition="",
                       category="", source_context="", source_lang="English",
                       target_lang="Turkish", profile="translation"):
        """Answer a free-form user question about a dictionary term.

        The term and all known context are always embedded, so even a vague
        question like 'bunu daha basit anlat' still resolves to the right word.
        Returns (result_text, model_used, status); degrades safely to
        ('no_server' / 'no_model') when LM Studio is unavailable.
        """
        status, models = self.server_status()
        if status == "no_server":
            return NO_SERVER_MSG, "", "no_server"
        if status == "no_model":
            return NO_MODEL_MSG, "", "no_model"
        model = self.profiles.resolve(profile, models)
        system = (
            "Sen İngilizce matematik/bilim kaynakları okuyan, Türkçe konuşan bir "
            "öğrenciye yardımcı olan bir sözlük asistanısın. Açıklamaların öğrenci "
            "dostu, sade ve matematik öğrenen biri için anlaşılır olsun. Cevabı "
            "ağırlıklı Türkçe ver; önemli İngilizce terimleri parantez içinde "
            "koru; uygunsa kısa bir örnek, bir benzetme ve matematik bağlamını ekle."
        )
        user = (
            f"Kelime (term): {term}\n"
            f"Türkçe karşılık (translation): {translation or '-'}\n"
            f"Mevcut açıklama (definition): {definition or '-'}\n"
            f"Kategori (category): {category or '-'}\n"
            f"Kaynak bağlamı (source context): {source_context or '-'}\n"
            f"Diller: {source_lang} -> {target_lang}\n\n"
            f"Kullanıcının sorusu: {question}\n\n"
            f"Yukarıdaki '{term}' kelimesi/terimi hakkında bu soruyu Türkçe yanıtla."
        )
        out, ok = self._complete(system, user, model)
        return out, model, ("ok" if ok else "error")


# ===========================================================================
# ImageTranslationPipeline — vision OCR (reuses app vision) + safe fallbacks
# ===========================================================================
VISION_OCR_PROMPT = (
    "You are an OCR and translation extraction assistant for educational "
    "math/science screenshots. Read the image carefully. Extract the visible "
    "English text exactly. Preserve formulas, symbols, variable names, fractions, "
    "exponents, and line breaks. Do not solve the math problem. Return the "
    "extracted text only."
)


class ImageTranslationPipeline:
    def __init__(self, vision_fn=None, ocr_fn=None):
        # vision_fn(system, user, image_path) -> (text, status)
        # ocr_fn(image_path) -> (text, status)
        self.vision_fn = vision_fn
        self.ocr_fn = ocr_fn

    def extract_text(self, image_path):
        """Try Vision model, then OCR, else manual. Returns (text, status)."""
        if not image_path or not Path(image_path).exists():
            return "", "no_image"
        # 1) Vision model
        if self.vision_fn is not None:
            try:
                text, status = self.vision_fn(VISION_OCR_PROMPT,
                                              "Extract the English text from this image.",
                                              str(image_path))
                if text and status not in ("no_vision_model", "error", "vision_http_error"):
                    return text.strip(), "vision"
            except Exception:
                pass
        # 2) OCR fallback
        if self.ocr_fn is not None:
            try:
                text, status = self.ocr_fn(str(image_path))
                if text and "unavailable" not in (status or "").lower():
                    return text.strip(), "ocr"
            except Exception:
                pass
        # 3) Manual
        return ("", "manual")


# ===========================================================================
# PDF Vocabulary Scanner — embedded glossaries, classifier, store, scanner
# ===========================================================================
import re as _re

MATH_TR = {
    "slope": "eğim", "intercept": "kesişim", "y-intercept": "y-kesişimi",
    "x-intercept": "x-kesişimi", "coordinate": "koordinat", "coordinates": "koordinatlar",
    "cartesian": "Kartezyen", "origin": "orijin", "axis": "eksen", "axes": "eksenler",
    "plane": "düzlem", "equation": "denklem", "equations": "denklemler",
    "expression": "ifade", "function": "fonksiyon", "domain": "tanım kümesi",
    "range": "değer kümesi", "denominator": "payda", "numerator": "pay",
    "fraction": "kesir", "polynomial": "polinom", "quadratic": "ikinci dereceden",
    "vertex": "tepe noktası", "factor": "çarpan", "coefficient": "katsayı",
    "constant": "sabit", "variable": "değişken", "parallel": "paralel",
    "perpendicular": "dik", "derivative": "türev", "integral": "integral",
    "matrix": "matris", "determinant": "determinant", "vector": "vektör",
    "scalar": "skaler", "asymptote": "asimptot", "exponent": "üs",
    "radical": "köklü ifade", "rational": "rasyonel", "irrational": "irrasyonel",
    "theorem": "teorem", "postulate": "postülat", "congruent": "eş",
    "similar": "benzer", "transversal": "kesen", "hypotenuse": "hipotenüs",
    "horizontal": "yatay", "vertical": "dikey", "two-dimensional": "iki boyutlu",
    "three-dimensional": "üç boyutlu", "magnitude": "büyüklük", "tangent": "teğet",
}

SCIENCE_TR = {
    "hypothesis": "hipotez", "theory": "teori", "experiment": "deney",
    "control": "kontrol", "sample": "örnek", "measurement": "ölçüm",
    "density": "yoğunluk", "velocity": "hız", "acceleration": "ivme",
    "force": "kuvvet", "energy": "enerji", "molecule": "molekül", "atom": "atom",
    "cell": "hücre", "gene": "gen", "protein": "protein", "genome": "genom",
    "nucleotide": "nükleotit", "enzyme": "enzim", "frequency": "frekans",
    "wavelength": "dalga boyu", "amplitude": "genlik", "momentum": "momentum",
}

ACADEMIC_TR = {
    "represent": "temsil etmek", "determine": "belirlemek",
    "evaluate": "değerlendirmek", "derive": "türetmek", "indicate": "göstermek",
    "correspond": "karşılık gelmek", "consistent": "tutarlı",
    "approximately": "yaklaşık olarak", "therefore": "bu nedenle",
    "although": "her ne kadar", "whereas": "oysa", "analyze": "çözümlemek",
    "concept": "kavram", "significant": "anlamlı", "approach": "yaklaşım",
    "define": "tanımlamak", "defined": "tanımlanmış", "graph": "grafik",
}

STOPWORDS = set("""
a an the and or but if then else of to in on at by for with from into over under
is are was were be been being am do does did can could should would may might must
this that these those it its as we you they he she him her them our your their
not no nor so such than too very just only also more most some any each every both
one two three four five six seven eight nine ten first second third here there when
where which who whom whose what why how all out up down off about above below
""".split())

NUMBER_WORDS = set("zero one two three four five six seven eight nine ten".split())

TECHNICAL_KEEP = set("""
slope intercept coordinate perpendicular parallel denominator numerator polynomial
equation expression function domain range derivative integral matrix determinant
vector scalar quadratic vertex asymptote coefficient variable constant factor
exponent radical rational irrational theorem postulate congruent similar transversal
hypotenuse cartesian coordinates axes origin plane horizontal vertical magnitude
hypothesis molecule velocity acceleration momentum frequency wavelength amplitude
""".split())

# Heuristic CEFR/TOEFL candidate hints (estimated, NOT exam-grade).
TOEFL_ACADEMIC = set(ACADEMIC_TR.keys()) | set("""
analyze approach assess assume concept context derive establish evaluate factor
function indicate interpret method principle process represent significant variable
hypothesis theory structure component sufficient consistent approximate
""".split())
C2_ADVANCED = set("""
asymptote determinant perpendicular hypotenuse transversal postulate irrational
cartesian polynomial coefficient differentiation eigenvalue orthogonal logarithmic
""".split())


class VocabularyDifficultyClassifier:
    """Rule-based difficulty / CEFR-ish tagging for extracted vocabulary."""

    def __init__(self, math=None, science=None, academic=None):
        self.math = {k.lower(): v for k, v in (math or MATH_TR).items()}
        self.science = {k.lower(): v for k, v in (science or SCIENCE_TR).items()}
        self.academic = {k.lower(): v for k, v in (academic or ACADEMIC_TR).items()}

    def embedded_translation(self, term):
        t = (term or "").lower()
        return self.math.get(t) or self.science.get(t) or self.academic.get(t) or ""

    def classify(self, term, frequency=1, known=False, dict_translation="", context=""):
        t = (term or "").strip().lower()
        score = 0
        tags = []
        category = "general"
        if len(t) >= 8:
            score += 1
        if t in self.academic or t in TOEFL_ACADEMIC:
            score += 2
            tags.append("academic")
            category = "academic"
        if t in self.math:
            score += 3
            tags.append("technical_math")
            category = "math"
        if t in self.science:
            score += 3
            tags.append("technical_science")
            category = "science"
        if frequency >= 3:
            score += 1
            tags.append("frequent_in_course")
        if known:
            tags.append("already_known")
        else:
            score += 1
            tags.append("new_to_user")
        # C1/C2 candidate hints
        if len(t) >= 8 or t in self.math or t in self.science:
            score += 0  # already covered, but mark
        if t in C2_ADVANCED or len(t) >= 12:
            score += 2
            tags.append("C2_candidate")
        elif len(t) >= 9 or t in self.academic:
            tags.append("C1_candidate")
        if t in TOEFL_ACADEMIC:
            score += 2
            tags.append("TOEFL")
        translation = dict_translation or self.embedded_translation(t)
        if not translation:
            score += 1
        if score <= 1:
            cefr = "basic"
        elif score == 2:
            cefr = "B1/common"
        elif score == 3:
            cefr = "B2"
        elif score == 4:
            cefr = "C1"
        else:
            cefr = "C2/technical"
        # de-duplicate tags, keep order
        seen = set()
        tags = [x for x in tags if not (x in seen or seen.add(x))]
        return {"cefr_level": cefr, "difficulty_score": score, "tags": tags,
                "category": category, "translation": translation}


class ExtractedVocabularyStore:
    """Manages extracted_vocabulary_terms + scan cache + overrides."""

    def __init__(self, store):
        self.store = store
        self.conn = store.conn
        self._lock = store._lock

    def add_or_update(self, term, lemma="", translation="", cefr_level="", difficulty_score=0,
                      tags="", category="", source_pdf="", page_number=0,
                      frequency=1, context_sentence=""):
        with self._lock:
            now = _now()
            row = self.conn.execute(
                "SELECT id, frequency FROM extracted_vocabulary_terms WHERE term=? AND source_pdf=?",
                (term, source_pdf)).fetchone()
            if row:
                # Preserve existing classification when an update passes empty/default
                # values (e.g. a partial update); a full re-scan overwrites normally.
                self.conn.execute(
                    "UPDATE extracted_vocabulary_terms SET frequency=?, "
                    "translation=CASE WHEN ?<>'' THEN ? ELSE translation END, "
                    "cefr_level=CASE WHEN ?<>'' THEN ? ELSE cefr_level END, "
                    "difficulty_score=CASE WHEN ?>0 THEN ? ELSE difficulty_score END, "
                    "tags=CASE WHEN ?<>'' THEN ? ELSE tags END, "
                    "category=CASE WHEN ?<>'' THEN ? ELSE category END, "
                    "context_sentence=COALESCE(NULLIF(context_sentence,''), ?), updated_at=? WHERE id=?",
                    (frequency, translation, translation, cefr_level, cefr_level,
                     difficulty_score, difficulty_score, tags, tags, category, category,
                     context_sentence, now, row["id"]))
                self.conn.commit()
                return row["id"]
            cur = self.conn.execute(
                "INSERT INTO extracted_vocabulary_terms (term, lemma, translation, cefr_level, "
                "difficulty_score, tags, category, source_pdf, page_number, frequency, "
                "context_sentence, status, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,'new',?,?)",
                (term, lemma, translation, cefr_level, difficulty_score, tags, category,
                 source_pdf, int(page_number or 0), frequency, context_sentence, now, now))
            self.conn.commit()
            return cur.lastrowid

    def list_terms(self, level=None, category=None, status=None, source_pdf=None,
                   min_frequency=0, query=None, limit=2000):
        sql = "SELECT * FROM extracted_vocabulary_terms WHERE 1=1"
        args = []
        if level and level != "all":
            sql += " AND cefr_level LIKE ?"
            args.append(f"%{level}%")
        if category and category != "all":
            sql += " AND category=?"
            args.append(category)
        if status and status != "all":
            if status == "favorite":
                sql += " AND favorite=1"
            elif status == "learned":
                sql += " AND learned=1"
            elif status == "added":
                sql += " AND added_to_dictionary=1"
            elif status == "new":
                sql += " AND learned=0 AND added_to_dictionary=0"
        if source_pdf and source_pdf != "all":
            sql += " AND source_pdf=?"
            args.append(source_pdf)
        if min_frequency:
            sql += " AND frequency>=?"
            args.append(int(min_frequency))
        if query:
            sql += " AND (lower(term) LIKE ? OR lower(translation) LIKE ? OR lower(tags) LIKE ?)"
            q = f"%{query.lower()}%"
            args += [q, q, q]
        sql += " ORDER BY difficulty_score DESC, frequency DESC, term ASC LIMIT ?"
        args.append(limit)
        with self._lock:
            return self.conn.execute(sql, args).fetchall()

    def get(self, term_id):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM extracted_vocabulary_terms WHERE id=?", (term_id,)).fetchone()

    def set_flag(self, term_id, field, value):
        if field not in ("favorite", "learned", "added_to_dictionary", "status", "translation"):
            return False
        with self._lock:
            self.conn.execute(
                f"UPDATE extracted_vocabulary_terms SET {field}=?, updated_at=? WHERE id=?",  # nosec B608 - field checked against an explicit allowlist above
                (value, _now(), term_id))
            self.conn.commit()
            return True

    def distinct_pdfs(self):
        with self._lock:
            return [r["source_pdf"] for r in self.conn.execute(
                "SELECT DISTINCT source_pdf FROM extracted_vocabulary_terms ORDER BY source_pdf").fetchall()
                if r["source_pdf"]]

    def count(self):
        with self._lock:
            return self.conn.execute("SELECT COUNT(*) FROM extracted_vocabulary_terms").fetchone()[0]

    def clear_for_pdf(self, source_pdf):
        with self._lock:
            self.conn.execute("DELETE FROM extracted_vocabulary_terms WHERE source_pdf=?", (source_pdf,))
            self.conn.execute("DELETE FROM pdf_vocabulary_scan_cache WHERE source_pdf=?", (source_pdf,))
            self.conn.commit()

    def clear_all(self):
        with self._lock:
            self.conn.execute("DELETE FROM extracted_vocabulary_terms")
            self.conn.execute("DELETE FROM pdf_vocabulary_scan_cache")
            self.conn.commit()

    def get_cache(self, source_pdf):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM pdf_vocabulary_scan_cache WHERE source_pdf=?", (source_pdf,)).fetchone()

    def set_cache(self, source_pdf, pdf_hash, modified_time, page_count, term_count, status="ok"):
        with self._lock:
            self.conn.execute(
                "INSERT INTO pdf_vocabulary_scan_cache (source_pdf, pdf_hash, modified_time, "
                "page_count, scanned_at, term_count, status) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(source_pdf) DO UPDATE SET pdf_hash=excluded.pdf_hash, "
                "modified_time=excluded.modified_time, page_count=excluded.page_count, "
                "scanned_at=excluded.scanned_at, term_count=excluded.term_count, status=excluded.status",
                (source_pdf, pdf_hash, modified_time, page_count, _now(), term_count, status))
            self.conn.commit()

    def export_csv(self, path, rows=None):
        rows = rows if rows is not None else self.list_terms(limit=100000)
        fields = ["term", "translation", "cefr_level", "difficulty_score", "tags",
                  "category", "source_pdf", "page_number", "frequency",
                  "context_sentence", "status"]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({k: (r[k] if k in r.keys() else "") for k in fields})
        return len(rows)

    # overrides
    def set_override(self, term, translation="", category="", difficulty_level="", tags="", user_note=""):
        with self._lock:
            self.conn.execute(
                "INSERT INTO technical_vocabulary_overrides (term, translation, category, "
                "difficulty_level, tags, user_note, created_at) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(term) DO UPDATE SET translation=excluded.translation, "
                "category=excluded.category, difficulty_level=excluded.difficulty_level, "
                "tags=excluded.tags, user_note=excluded.user_note",
                (term, translation, category, difficulty_level, tags, user_note, _now()))
            self.conn.commit()

    def get_override(self, term):
        with self._lock:
            return self.conn.execute(
                "SELECT * FROM technical_vocabulary_overrides WHERE term=?", (term,)).fetchone()


class PDFVocabularyScanner:
    """Scans Resources PDFs for technical/academic vocabulary with caching."""

    def __init__(self, store, vocab_store=None, classifier=None,
                 resources_dir=None, translate_fn=None, known_fn=None):
        self.store = store
        self.vocab = vocab_store or ExtractedVocabularyStore(store)
        self.classifier = classifier or VocabularyDifficultyClassifier()
        self.resources_dir = Path(resources_dir) if resources_dir else _app_paths.resources_dir()
        self.translate_fn = translate_fn      # optional LM (term, context) -> translation
        self.known_fn = known_fn              # optional (term) -> bool (user already knows / in dict)
        self._stop = False

    def find_pdfs(self):
        if not self.resources_dir.exists():
            return []
        try:
            return sorted(self.resources_dir.rglob("*.pdf"))
        except Exception:
            return []

    @staticmethod
    def pdf_signature(path):
        try:
            st = os.stat(path)
            return f"{int(st.st_mtime)}-{st.st_size}", str(int(st.st_mtime))
        except Exception:
            return "", ""

    def split_sentences(self, text):
        parts = _re.split(r"(?<=[.!?])\s+|\n{2,}", text or "")
        return [p.strip() for p in parts if len(p.strip()) > 3]

    def tokenize(self, text):
        return _re.findall(r"[A-Za-z][A-Za-z'\-]*[A-Za-z]", text or "")

    def is_candidate(self, token):
        t = (token or "").strip().lower().strip("-'")
        if t in TECHNICAL_KEEP:
            return True
        if len(t) < 3:
            return False
        if t in STOPWORDS or t in NUMBER_WORDS:
            return False
        if t.isdigit():
            return False
        if not _re.match(r"^[a-z][a-z\-]*[a-z]$", t):
            return False
        return True

    def extract_candidates(self, text):
        """Yield (term_lower, context_sentence) from text."""
        for sentence in self.split_sentences(text):
            for tok in self.tokenize(sentence):
                t = tok.lower().strip("-'")
                if self.is_candidate(t):
                    yield t, sentence

    def _resolve_translation(self, term, context):
        # 1) embedded glossary, 2) existing dictionary, 3) optional LM
        tr = self.classifier.embedded_translation(term)
        if tr:
            return tr
        try:
            row = self.store.get_term(term, "en")
            if row and row["translation"]:
                return row["translation"]
        except Exception:
            pass
        if self.translate_fn is not None:
            try:
                return self.translate_fn(term, context) or ""
            except Exception:
                return ""
        return ""

    def stop(self):
        self._stop = True

    def scan(self, progress_cb=None, done_cb=None, rebuild=False, use_lm=False, background=True):
        """Scan all PDFs. Runs in a background thread by default."""
        self._stop = False

        def report(msg):
            if progress_cb:
                try:
                    progress_cb(msg)
                except Exception:
                    pass

        def work():
            try:
                fitz = None
                try:
                    import fitz as _fitz
                    fitz = _fitz
                except Exception:
                    fitz = None
                if fitz is None:
                    if done_cb:
                        done_cb(False, "PyMuPDF (fitz) not available — cannot extract PDF text.")
                    return
                pdfs = self.find_pdfs()
                report(f"Scanning PDFs... found {len(pdfs)} files")
                total_terms = 0
                for i, path in enumerate(pdfs, 1):
                    if self._stop:
                        break
                    rel = str(path.relative_to(self.resources_dir)) if str(path).startswith(str(self.resources_dir)) else str(path)
                    sig, mtime = self.pdf_signature(path)
                    cache = self.vocab.get_cache(rel)
                    if not rebuild and cache and cache["pdf_hash"] == sig:
                        report(f"Processing file {i}/{len(pdfs)}: {path.name} (cached)")
                        continue
                    if rebuild:
                        self.vocab.clear_for_pdf(rel)
                    report(f"Processing file {i}/{len(pdfs)}: {path.name}")
                    try:
                        doc = fitz.open(str(path))
                    except Exception:
                        self.vocab.set_cache(rel, sig, mtime, 0, 0, status="error")
                        continue
                    freq = {}
                    context = {}
                    page_first = {}
                    npages = len(doc)
                    for pno, page in enumerate(doc, 1):
                        if self._stop:
                            break
                        if pno % 5 == 0:
                            report(f"{path.name}: page {pno}/{npages}")
                        try:
                            text = page.get_text()
                        except Exception:
                            continue
                        for term, sentence in self.extract_candidates(text):
                            freq[term] = freq.get(term, 0) + 1
                            if term not in context:
                                context[term] = sentence[:300]
                                page_first[term] = pno
                    doc.close()
                    # store
                    count = 0
                    for term, f in freq.items():
                        known = bool(self.known_fn(term)) if self.known_fn else False
                        tr = self._resolve_translation(term, context.get(term, "")) if (use_lm or True) else ""
                        info = self.classifier.classify(term, frequency=f, known=known,
                                                        dict_translation=tr, context=context.get(term, ""))
                        self.vocab.add_or_update(
                            term=term, lemma=term, translation=info["translation"],
                            cefr_level=info["cefr_level"], difficulty_score=info["difficulty_score"],
                            tags=",".join(info["tags"]), category=info["category"],
                            source_pdf=rel, page_number=page_first.get(term, 0),
                            frequency=f, context_sentence=context.get(term, ""))
                        count += 1
                    total_terms += count
                    self.vocab.set_cache(rel, sig, mtime, npages, count, status="ok")
                    report(f"Extracted terms: {total_terms}")
                if done_cb:
                    done_cb(True, f"Done. {total_terms} terms from {len(pdfs)} PDFs.")
            except Exception as exc:
                if done_cb:
                    done_cb(False, f"Scan error: {exc}")

        if background:
            threading.Thread(target=work, daemon=True).start()
        else:
            work()


# ===========================================================================
# LanguageDictionaryPanel — the Tk UI
# ===========================================================================
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

STATUS_COLORS = {"connected": "#16A55A", "no_model": "#C99A2E",
                 "no_server": "#C0392B", "error": "#C0392B"}


def apply_dark_palette():
    """Ana uygulama karanlik temadayken panel kurulmadan ONCE cagrilir."""
    global BG, PANEL_BG, FG, MUTED, ACCENT
    BG = "#2A241C"
    PANEL_BG = "#1B1712"
    FG = "#EDE5D8"
    MUTED = "#A6987F"
    ACCENT = "#E07B39"
    STATUS_COLORS.update({"connected": "#2FBF71", "no_model": "#D9A94A",
                          "no_server": "#E25B4A", "error": "#E25B4A"})


class LanguageDictionaryPanel(ttk.Frame if tk is not None else object):
    """The Language & Science Dictionary tab (8 sub-tabs)."""

    def __init__(self, parent, app, seed_terms=None):
        super().__init__(parent)
        self.app = app
        self._lang = getattr(app, "language", "en")
        self.store = DictionaryStore()
        self.history = TranslationHistoryStore(self.store)
        self.profiles = LanguageModelProfileManager(self.store)
        base_url = DEFAULT_BASE_URL
        try:
            if getattr(app, "client", None) is not None:
                base_url = app.client.base_url
        except Exception:
            pass
        self.translator = LMStudioTranslationClient(base_url, self.profiles)
        self.image_pipeline = ImageTranslationPipeline(vision_fn=self._app_vision,
                                                       ocr_fn=self._ocr_fn)
        # PDF Vocabulary Scanner (offline-first: embedded glossary + existing
        # dictionary; LM is used only on demand per term, not during bulk scan).
        self.vocab_classifier = VocabularyDifficultyClassifier()
        self.vocab = ExtractedVocabularyStore(self.store)
        self.vocab_scanner = PDFVocabularyScanner(
            self.store, self.vocab, self.vocab_classifier,
            translate_fn=None,
            known_fn=lambda t: bool(self.store.get_term(t, "en")))
        self._vocab_selected = None
        self._image_path = None
        self._image_photo = None
        self._selected_term = None
        try:
            self.store.seed_terms(seed_terms or [])
        except Exception:
            pass
        self._build()

    # -- LM helpers ---------------------------------------------------- #
    def _app_vision(self, system, user, path):
        client = getattr(self.app, "client", None)
        if client is None or not hasattr(client, "complete_with_image"):
            return "", "no_vision_model"
        try:
            text, _usage, finish = client.complete_with_image(system, user, path)
            return text, finish
        except Exception as exc:
            return f"vision error: {exc}", "error"

    def _ocr_fn(self, path):
        try:
            import visual_math_lab as vml
            if hasattr(vml, "extract_text_with_tesseract"):
                return vml.extract_text_with_tesseract(path)
        except Exception:
            pass
        return "", "ocr unavailable"

    def _run_async(self, work, on_done):
        """Run a blocking LM call off the UI thread, post the result back."""
        def task():
            try:
                result = work()
            except Exception as exc:
                result = ("error", str(exc))
            try:
                self.after(0, lambda: on_done(result))
            except Exception:
                pass
        threading.Thread(target=task, daemon=True).start()

    def _set_text(self, widget, content):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content or "")
        widget.config(state="disabled")

    def _display_translation(self, row, term=None):
        direct = (_row_value(row, "display_translation") or
                  _row_value(row, "translation") or
                  _row_value(row, "short_translation"))
        if direct:
            return direct
        result = _row_value(row, "result") or _row_value(row, "definition")
        return extract_short_translation(term or _row_value(row, "term") or _row_value(row, "query"), result)

    def _refresh_word_lists(self):
        for name in ("_refresh_history", "_refresh_frequent", "_refresh_favorites"):
            try:
                getattr(self, name)()
            except Exception:
                pass

    def _normalize_lookup_result(self, result):
        try:
            if isinstance(result, tuple) and len(result) == 3:
                return result
            if isinstance(result, tuple) and len(result) == 2:
                return result[1], "", result[0]
        except Exception:
            pass
        return str(result), "", "error"

    # -- UI build ------------------------------------------------------ #
    def _build(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)
        self._build_dictionary_tab()
        self._build_sentence_tab()
        self._build_image_tab()
        self._build_pdf_terms_tab()
        self._build_vocab_scanner_tab()
        self._build_history_tab()
        self._build_frequent_tab()
        self._build_favorites_tab()
        self._build_profiles_tab()

    def refresh_ui(self):
        self._lang = getattr(self.app, "language", "en")

    # ---- Tab 1: Dictionary ---- #
    def _build_dictionary_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Dictionary / Sözlük")
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=4, pady=4)
        ttk.Label(top, text="Source:").pack(side="left")
        self.dict_src = ttk.Combobox(top, state="readonly", width=9,
                                     values=["Auto", "English", "Turkish"])
        self.dict_src.current(1)
        self.dict_src.pack(side="left", padx=2)
        ttk.Label(top, text="Target:").pack(side="left", padx=(6, 0))
        self.dict_tgt = ttk.Combobox(top, state="readonly", width=9,
                                     values=["Turkish", "English"])
        self.dict_tgt.current(0)
        self.dict_tgt.pack(side="left", padx=2)
        self.dict_query = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self.dict_query, width=26)
        ent.pack(side="left", padx=6)
        ent.bind("<Return>", lambda e: self._do_search())
        ttk.Button(top, text="Search", command=self._do_search).pack(side="left", padx=2)
        ttk.Button(top, text="Add to Favorites", command=self._fav_current).pack(side="left", padx=2)
        ttk.Button(top, text="Save to Dictionary", command=self._save_current).pack(side="left", padx=2)
        ttk.Button(top, text="Clear", command=self._clear_dict).pack(side="left", padx=2)

        split = ttk.Panedwindow(tab, orient="horizontal")
        split.pack(fill="both", expand=True, padx=4, pady=4)
        left = ttk.Frame(split)
        split.add(left, weight=2)
        cols = ("term", "tr", "cat", "n")
        self.dict_tree = ttk.Treeview(left, columns=cols, show="headings", height=12, selectmode="browse")
        for c, t, w in (("term", "Term", 150), ("tr", "Turkish / Türkçe Karşılık", 210),
                        ("cat", "Category", 130), ("n", "Count", 60)):
            self.dict_tree.heading(c, text=t)
            self.dict_tree.column(c, width=w, anchor="w" if c != "n" else "center")
        self.dict_tree.pack(fill="both", expand=True)
        self.dict_tree.bind("<<TreeviewSelect>>", lambda e: self._on_dict_select())
        right = ttk.Frame(split)
        split.add(right, weight=3)
        self.dict_status = tk.Label(right, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.dict_status.pack(fill="x")
        # Right side splits vertically: explanation (top) + Ask-AI box (bottom).
        rsplit = ttk.Panedwindow(right, orient="vertical")
        rsplit.pack(fill="both", expand=True)
        detail_frame = ttk.Frame(rsplit)
        rsplit.add(detail_frame, weight=3)
        self.dict_detail = tk.Text(detail_frame, wrap="word", bg=PANEL_BG, fg=FG, relief="flat",
                                   font=("Consolas", 10))
        self.dict_detail.pack(fill="both", expand=True)
        self.dict_detail.config(state="disabled")
        ai_frame = ttk.Frame(rsplit)
        rsplit.add(ai_frame, weight=2)
        self._build_dict_ai_box(ai_frame)

    def _do_search(self):
        term = (self.dict_query.get() or "").strip()
        if not term:
            return
        src = self.dict_src.get()
        tgt = self.dict_tgt.get()
        lang = "tr" if src == "Turkish" else "en"
        # 1) local
        rows = self.store.search_terms(term)
        self._populate_dict_tree(rows)
        local = self.store.get_term(term, lang)
        if local:
            self.store.increment_search_count(term, lang)
            local = self.store.get_term(term, lang) or local
            translation = self._display_translation(local, term)
            result_text = (local["definition"] or local["tr_explanation"] or
                           local["en_explanation"] or translation)
            self._show_term_row(local)
            self.history.add_search(
                term, src, tgt, result_text, "local",
                translation=translation, short_translation=translation,
                category=local["category"], source_context=local["source"])
            self._populate_dict_tree(self.store.search_terms(term))
            self._refresh_word_lists()
            return
        # 2) LM Studio (async)
        self.dict_status.config(text="Looking up via LM Studio…", fg=ACCENT)
        history_id = self.history.add_search(
            term, src, tgt, "(pending)", "",
            category="general", source_context="lm-studio")

        def work():
            return self.translator.lookup_word(term, src, tgt, "translation")

        def done(result):
            out, model, status = self._normalize_lookup_result(result)
            color = STATUS_COLORS.get(status, MUTED)
            self.dict_status.config(text=f"Model: {model or '-'}  |  {status}", fg=color)
            short = extract_short_translation(term, out)
            translation = short if status == "ok" else ""
            self.history.update_search(
                history_id, result=out, model_used=model,
                translation=translation, short_translation=translation,
                category="general", source_context="lm-studio")
            selected = {"term": term, "lang": lang, "translation": translation,
                        "short_translation": translation, "definition": out,
                        "category": "general", "example": "", "source": "lm-studio",
                        "tr_explanation": "", "en_explanation": "",
                        "favorite": 0, "search_count": 0, "model_used": model}
            if status == "ok":
                self.store.add_term(term=term, translation=translation, lang=lang,
                                    definition=out, category="general",
                                    source="lm-studio", model_used=model)
                self.store.increment_search_count(term, lang)
                saved = self.store.get_term(term, lang)
                if saved:
                    selected = saved
                    self._populate_dict_tree(self.store.search_terms(term))
            self._show_term_row(selected)
            self._refresh_word_lists()
        self._run_async(work, done)

    def _populate_dict_tree(self, rows):
        self.dict_tree.delete(*self.dict_tree.get_children())
        self._dict_rows = list(rows)
        for i, r in enumerate(rows):
            self.dict_tree.insert("", "end", iid=str(i),
                                  values=(r["term"], self._display_translation(r),
                                          r["category"], r["search_count"]))

    def _on_dict_select(self):
        sel = self.dict_tree.selection()
        if not sel:
            return
        try:
            r = self._dict_rows[int(sel[0])]
        except Exception:
            return
        self.store.increment_search_count(r["term"], r["lang"])
        fresh = self.store.get_term(r["term"], r["lang"]) or r
        self._show_term_row(fresh)

    def _show_term_row(self, r):
        self._selected_term = dict(r) if not isinstance(r, dict) else r
        term = _row_value(r, "term")
        translation = self._display_translation(r, term)
        favorite = _row_value(r, "favorite", 0)
        explanation = (_row_value(r, "definition") or _row_value(r, "tr_explanation") or
                       _row_value(r, "en_explanation"))
        lines = [
            f"English term           : {term}",
            f"Turkish meaning        : {translation}",
            f"Explanation            : {explanation}",
            f"Category               : {_row_value(r, 'category')}",
            f"Example                : {_row_value(r, 'example')}",
            f"Search count           : {_row_value(r, 'search_count', 0)}",
            f"Favorite status        : {'yes' if favorite else 'no'}",
            f"Model used             : {_row_value(r, 'model_used') or '-'}",
            "",
            f"TR explanation         : {_row_value(r, 'tr_explanation')}",
            f"EN explanation         : {_row_value(r, 'en_explanation')}",
            f"Source                 : {_row_value(r, 'source')}",
        ]
        self._set_text(self.dict_detail, "\n".join(lines))
        source = _row_value(r, "source") or "local dictionary"
        self.dict_status.config(text=f"{term} — {source}", fg=STATUS_COLORS["connected"])

    def _fav_current(self):
        t = self._selected_term
        if not t:
            return
        term = _row_value(t, "term")
        lang = _row_value(t, "lang", "en")
        translation = self._display_translation(t, term)
        existing = self.store.get_term(term, lang)
        if not existing or (translation and not existing["translation"]):
            self.store.add_term(term=term, translation=translation, lang=lang,
                                definition=_row_value(t, "definition"),
                                category=_row_value(t, "category"),
                                source=_row_value(t, "source") or "dictionary",
                                model_used=_row_value(t, "model_used"))
        self.store.set_favorite(term, True, lang)
        self._refresh_favorites()
        self.dict_status.config(text=f"Added to favorites: {term}", fg=STATUS_COLORS["connected"])

    def _save_current(self):
        t = self._selected_term
        if not t:
            return
        term = _row_value(t, "term")
        self.store.add_term(term=term, translation=self._display_translation(t, term),
                            lang=_row_value(t, "lang", "en"),
                            definition=_row_value(t, "definition"),
                            category=_row_value(t, "category"),
                            model_used=_row_value(t, "model_used"),
                            source=_row_value(t, "source") or "lm-studio")
        self._populate_dict_tree(self.store.search_terms(term))
        self._refresh_word_lists()
        self.dict_status.config(text=f"Saved to dictionary: {term}", fg=STATUS_COLORS["connected"])

    def _clear_dict(self):
        self.dict_query.set("")
        self.dict_tree.delete(*self.dict_tree.get_children())
        self._set_text(self.dict_detail, "")
        self.dict_status.config(text="")

    # ---- Dictionary tab: "Ask AI about this term" box ---- #
    DICT_AI_PLACEHOLDER = ("Bu kelimeyle ilgili sorunuzu yazın…  "
                           "Örn: graph ile chart arasındaki fark nedir?")

    def _build_dict_ai_box(self, parent):
        """Ask-AI message box under the explanation panel (beige/orange theme)."""
        box = ttk.Frame(parent)
        box.pack(fill="both", expand=True, pady=(6, 0))
        tk.Label(box, text="Kelime hakkında yapay zekaya sor / Ask AI about this term",
                 bg=BG, fg=ACCENT, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", padx=2, pady=(0, 2))
        # Multi-line question box with a lightweight placeholder.
        self.dict_ai_q = tk.Text(box, height=3, wrap="word", bg=PANEL_BG, fg=MUTED,
                                 relief="solid", borderwidth=1, font=("Segoe UI", 10),
                                 insertbackground=FG)
        self.dict_ai_q.pack(fill="x", padx=2)
        self._dict_ai_ph_active = True
        self.dict_ai_q.insert("1.0", self.DICT_AI_PLACEHOLDER)
        self.dict_ai_q.bind("<FocusIn>", self._dict_ai_focus_in)
        self.dict_ai_q.bind("<FocusOut>", self._dict_ai_focus_out)
        self.dict_ai_q.bind("<Control-Return>", lambda e: (self._dict_ai_ask(), "break")[1])
        btns = ttk.Frame(box)
        btns.pack(fill="x", padx=2, pady=3)
        self.dict_ai_ask_btn = ttk.Button(btns, text="AI'ye Sor", command=self._dict_ai_ask)
        self.dict_ai_ask_btn.pack(side="left")
        ttk.Button(btns, text="Temizle", command=self._dict_ai_clear).pack(side="left", padx=4)
        ttk.Button(btns, text="Cevabı Kopyala", command=self._dict_ai_copy).pack(side="left")
        self.dict_ai_status = tk.Label(box, text="", bg=BG, fg=MUTED,
                                       font=("Segoe UI", 9), anchor="w")
        self.dict_ai_status.pack(fill="x", padx=2)
        ansrow = ttk.Frame(box)
        ansrow.pack(fill="both", expand=True, padx=2, pady=(0, 2))
        self.dict_ai_answer = tk.Text(ansrow, wrap="word", bg=PANEL_BG, fg=FG, relief="flat",
                                      font=("Segoe UI", 10), height=6)
        ascroll = ttk.Scrollbar(ansrow, orient="vertical", command=self.dict_ai_answer.yview)
        self.dict_ai_answer.configure(yscrollcommand=ascroll.set)
        self.dict_ai_answer.pack(side="left", fill="both", expand=True)
        ascroll.pack(side="right", fill="y")
        self.dict_ai_answer.config(state="disabled")

    def _dict_ai_focus_in(self, _e=None):
        if getattr(self, "_dict_ai_ph_active", False):
            self.dict_ai_q.delete("1.0", "end")
            self.dict_ai_q.config(fg=FG)
            self._dict_ai_ph_active = False

    def _dict_ai_focus_out(self, _e=None):
        if not self.dict_ai_q.get("1.0", "end").strip():
            self.dict_ai_q.delete("1.0", "end")
            self.dict_ai_q.insert("1.0", self.DICT_AI_PLACEHOLDER)
            self.dict_ai_q.config(fg=MUTED)
            self._dict_ai_ph_active = True

    def _dict_ai_get_question(self):
        if getattr(self, "_dict_ai_ph_active", False):
            return ""
        return self.dict_ai_q.get("1.0", "end").strip()

    def _dict_ai_set_status(self, msg, color=None):
        try:
            self.dict_ai_status.config(text=msg, fg=color or MUTED)
        except Exception:
            pass

    def _dict_ai_ask(self):
        if getattr(self, "dict_ai_q", None) is None:
            return
        question = self._dict_ai_get_question()
        if not question:
            self._dict_ai_set_status("Lütfen bir soru yazın.", STATUS_COLORS["no_model"])
            return
        term_row = self._selected_term
        if not term_row:
            self._dict_ai_set_status("Önce bir kelime aratın veya listeden seçin.",
                                     STATUS_COLORS["no_model"])
            return
        term = _row_value(term_row, "term")
        translation = self._display_translation(term_row, term)
        definition = (_row_value(term_row, "definition") or
                      _row_value(term_row, "tr_explanation") or
                      _row_value(term_row, "en_explanation"))
        category = _row_value(term_row, "category")
        source_context = _row_value(term_row, "source")
        src = self.dict_src.get()
        tgt = self.dict_tgt.get()
        self.dict_ai_ask_btn.config(state="disabled")
        self._dict_ai_set_status("Yanıt hazırlanıyor…", ACCENT)

        def work():
            return self.translator.ask_about_term(
                term, question, translation=translation, definition=definition,
                category=category, source_context=source_context,
                source_lang=src, target_lang=tgt)

        def done(result):
            out, model, status = self._normalize_lookup_result(result)
            try:
                self.dict_ai_ask_btn.config(state="normal")
            except Exception:
                pass
            if status in ("no_server", "no_model"):
                warn = ("LM Studio bağlantısı yok. Lütfen LM Studio server/model "
                        "durumunu kontrol edin.")
                self._set_text(self.dict_ai_answer, warn + "\n\n" + (out or ""))
                self._dict_ai_set_status(warn, STATUS_COLORS.get(status, STATUS_COLORS["no_server"]))
                return
            if status != "ok":
                self._set_text(self.dict_ai_answer,
                               "Yanıt alınamadı:\n" + (out or "Bilinmeyen hata."))
                self._dict_ai_set_status("Hata oluştu, tekrar deneyin.", STATUS_COLORS["error"])
                return
            self._set_text(self.dict_ai_answer, out)
            self._dict_ai_set_status(f"Model: {model or '-'}", STATUS_COLORS["connected"])
            try:
                self.store.add_ai_question(
                    term, question, out, model=model,
                    source_language=src, target_language=tgt,
                    source_context="dictionary_ai_question")
            except Exception:
                pass

        self._run_async(work, done)

    def _dict_ai_clear(self):
        try:
            self.dict_ai_q.delete("1.0", "end")
            self.dict_ai_q.insert("1.0", self.DICT_AI_PLACEHOLDER)
            self.dict_ai_q.config(fg=MUTED)
            self._dict_ai_ph_active = True
        except Exception:
            pass
        self._set_text(self.dict_ai_answer, "")
        self._dict_ai_set_status("")

    def _dict_ai_copy(self):
        try:
            text = self.dict_ai_answer.get("1.0", "end").strip()
        except Exception:
            text = ""
        if not text:
            self._dict_ai_set_status("Kopyalanacak cevap yok.", MUTED)
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._dict_ai_set_status("Cevap panoya kopyalandı.", STATUS_COLORS["connected"])
        except Exception:
            self._dict_ai_set_status("Kopyalama başarısız.", STATUS_COLORS["error"])

    # ---- Tab 2: Sentence Translation ---- #
    def _build_sentence_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Sentence Translation / Cümle Çevirisi")
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=4, pady=4)
        ttk.Label(top, text="Source:").pack(side="left")
        self.sent_src = ttk.Combobox(top, state="readonly", width=9, values=["Auto", "English", "Turkish"])
        self.sent_src.current(1)
        self.sent_src.pack(side="left", padx=2)
        ttk.Label(top, text="Target:").pack(side="left", padx=(6, 0))
        self.sent_tgt = ttk.Combobox(top, state="readonly", width=9, values=["Turkish", "English"])
        self.sent_tgt.current(0)
        self.sent_tgt.pack(side="left", padx=2)
        ttk.Label(top, text="Quality:").pack(side="left", padx=(6, 0))
        self.sent_profile = ttk.Combobox(top, state="readonly", width=14,
                                         values=["Fast", "High Quality", "Fallback"])
        self.sent_profile.current(0)
        self.sent_profile.pack(side="left", padx=2)
        ttk.Button(top, text="Translate", command=self._do_sentence).pack(side="left", padx=4)
        ttk.Button(top, text="Clear", command=lambda: (self.sent_in.delete("1.0", "end"),
                                                       self._set_text(self.sent_out, ""))).pack(side="left", padx=2)
        ttk.Button(top, text="Copy Result", command=lambda: self._copy(self.sent_out.get("1.0", "end"))).pack(side="left", padx=2)

        split = ttk.Panedwindow(tab, orient="horizontal")
        split.pack(fill="both", expand=True, padx=4, pady=4)
        lf = ttk.Frame(split)
        split.add(lf, weight=1)
        self.sent_in = tk.Text(lf, wrap="word", bg=PANEL_BG, fg=FG, relief="flat", font=("Consolas", 11))
        self.sent_in.pack(fill="both", expand=True)
        self.sent_count = tk.Label(lf, text="0 chars", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.sent_count.pack(fill="x")
        self.sent_in.bind("<KeyRelease>", lambda e: self.sent_count.config(
            text=f"{len(self.sent_in.get('1.0','end'))-1} chars"))
        rf = ttk.Frame(split)
        split.add(rf, weight=1)
        self.sent_status = tk.Label(rf, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.sent_status.pack(fill="x")
        self.sent_out = tk.Text(rf, wrap="word", bg=PANEL_BG, fg=FG, relief="flat", font=("Consolas", 11))
        self.sent_out.pack(fill="both", expand=True)
        self.sent_out.config(state="disabled")

    def _do_sentence(self):
        text = (self.sent_in.get("1.0", "end") or "").strip()
        if not text:
            return
        src, tgt = self.sent_src.get(), self.sent_tgt.get()
        profile = {"Fast": "translation", "High Quality": "high_quality_translation",
                   "Fallback": "general_fallback"}.get(self.sent_profile.get(), "translation")
        self.sent_status.config(text="Translating…", fg=ACCENT)

        def work():
            return self.translator.translate(text, src, tgt, profile)

        def done(result):
            out, model, status = result
            self.sent_status.config(text=f"Model: {model or '-'}  |  {status}",
                                    fg=STATUS_COLORS.get(status, MUTED))
            self._set_text(self.sent_out, out)
            if status == "ok":
                self.history.add_sentence(text, out, src, tgt, model)
        self._run_async(work, done)

    # ---- Tab 3: Image Translation ---- #
    def _build_image_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Image Translation / Görsel Çeviri")
        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=4, pady=4)
        for text, cmd in (("Load Image", self._img_load), ("Paste Screenshot", self._img_paste),
                          ("Extract Text", self._img_extract), ("Translate Extracted Text", self._img_translate),
                          ("Send to Visual Math Lab", self._img_send_vml), ("Clear", self._img_clear),
                          ("Copy Translation", lambda: self._copy(self.img_out.get("1.0", "end")))):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=2)
        self.img_status = tk.Label(tab, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.img_status.pack(fill="x", padx=4)
        body = ttk.Panedwindow(tab, orient="horizontal")
        body.pack(fill="both", expand=True, padx=4, pady=4)
        lf = ttk.Frame(body)
        body.add(lf, weight=1)
        self.img_preview = tk.Label(lf, text="No image loaded.", bg=PANEL_BG, fg=MUTED, height=8)
        self.img_preview.pack(fill="x", pady=(0, 4))
        ttk.Label(lf, text="Extracted Text (editable):").pack(anchor="w")
        self.img_extracted = tk.Text(lf, wrap="word", bg=PANEL_BG, fg=FG, relief="flat", font=("Consolas", 10), height=10)
        self.img_extracted.pack(fill="both", expand=True)
        rf = ttk.Frame(body)
        body.add(rf, weight=1)
        ttk.Label(rf, text="Translation:").pack(anchor="w")
        self.img_out = tk.Text(rf, wrap="word", bg=PANEL_BG, fg=FG, relief="flat", font=("Consolas", 10))
        self.img_out.pack(fill="both", expand=True)
        self.img_out.config(state="disabled")

    def _img_load(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if path:
            self._image_path = path
            self._show_image_preview(path)

    def _img_paste(self):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is None:
                self.img_status.config(text="No image found in clipboard.", fg=STATUS_COLORS["no_model"])
                return
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            out = DATA_DIR / f"clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img.save(str(out))
            self._image_path = str(out)
            self._show_image_preview(str(out))
        except Exception as exc:
            self.img_status.config(text=f"Paste failed: {exc}", fg=STATUS_COLORS["error"])

    def _show_image_preview(self, path):
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img.thumbnail((280, 200))
            self._image_photo = ImageTk.PhotoImage(img)
            self.img_preview.config(image=self._image_photo, text="")
            self.img_status.config(text=f"Loaded: {Path(path).name}", fg=STATUS_COLORS["connected"])
        except Exception:
            self.img_preview.config(text=Path(path).name, image="")

    def _img_extract(self):
        if not self._image_path:
            self.img_status.config(text="Load an image first.", fg=STATUS_COLORS["no_model"])
            return
        self.img_status.config(text="Extracting text…", fg=ACCENT)

        def work():
            return self.image_pipeline.extract_text(self._image_path)

        def done(result):
            text, status = result
            self.img_extracted.delete("1.0", "end")
            if text:
                self.img_extracted.insert("1.0", text)
                self.img_status.config(text=f"Extracted via {status}. Edit if needed.",
                                       fg=STATUS_COLORS["connected"])
            else:
                self.img_status.config(text="No text extracted — type it manually below.",
                                       fg=STATUS_COLORS["no_model"])
        self._run_async(work, done)

    def _img_translate(self):
        text = (self.img_extracted.get("1.0", "end") or "").strip()
        if not text:
            self.img_status.config(text="Nothing to translate — extract or type text first.",
                                   fg=STATUS_COLORS["no_model"])
            return
        self.img_status.config(text="Translating…", fg=ACCENT)

        def work():
            return self.translator.translate(text, "English", "Turkish", "translation")

        def done(result):
            out, model, status = result
            self._set_text(self.img_out, out)
            self.img_status.config(text=f"Model: {model or '-'}  |  {status}",
                                   fg=STATUS_COLORS.get(status, MUTED))
            if status == "ok":
                self.history.add_image(self._image_path or "", text, out, "vision", model)
        self._run_async(work, done)

    def _img_send_vml(self):
        text = (self.img_extracted.get("1.0", "end") or "").strip()
        if not text:
            return
        try:
            if hasattr(self.app, "question_text"):
                self.app.question_text.delete("1.0", "end")
                self.app.question_text.insert("1.0", text)
            if hasattr(self.app, "select_workspace"):
                self.app.select_workspace("VisualMath")
            self.img_status.config(text="Sent to Visual Math Lab.", fg=STATUS_COLORS["connected"])
        except Exception as exc:
            self.img_status.config(text=f"Send failed: {exc}", fg=STATUS_COLORS["error"])

    def _img_clear(self):
        self._image_path = None
        self._image_photo = None
        self.img_preview.config(image="", text="No image loaded.")
        self.img_extracted.delete("1.0", "end")
        self._set_text(self.img_out, "")
        self.img_status.config(text="")

    # ---- Tab 4: PDF Terms ---- #
    def _build_pdf_terms_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="PDF Terms / PDF Terimleri")
        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=4, pady=4)
        for text, cmd in (("Add Term", self._pdf_add), ("Delete Term", self._pdf_delete),
                          ("Mark as Learned", self._pdf_learned), ("Export CSV", self._pdf_export),
                          ("Import CSV", self._pdf_import), ("Refresh", self._refresh_pdf_terms)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=2)
        cols = ("term", "tr", "pdf", "page", "diff", "learned")
        self.pdf_tree = ttk.Treeview(tab, columns=cols, show="headings", height=14, selectmode="browse")
        for c, t, w in (("term", "Term", 150), ("tr", "Turkish / Türkçe Karşılık", 210), ("pdf", "Source PDF", 160),
                        ("page", "Page", 50), ("diff", "Difficulty", 80), ("learned", "Learned", 70)):
            self.pdf_tree.heading(c, text=t)
            self.pdf_tree.column(c, width=w, anchor="w" if c in ("term", "tr", "pdf") else "center")
        self.pdf_tree.pack(fill="both", expand=True, padx=4, pady=4)
        self._refresh_pdf_terms()

    def _refresh_pdf_terms(self):
        self.pdf_tree.delete(*self.pdf_tree.get_children())
        self._pdf_rows = self.store.list_pdf_terms()
        for r in self._pdf_rows:
            self.pdf_tree.insert("", "end", iid=str(r["id"]),
                                 values=(r["term"], r["translation"], r["source_pdf"],
                                         r["page_number"], r["difficulty"], "yes" if r["learned"] else "no"))

    def _pdf_add(self):
        self.store.add_pdf_term(term="(new term)", translation="", source_pdf="", page_number=0)
        self._refresh_pdf_terms()

    def _pdf_delete(self):
        sel = self.pdf_tree.selection()
        if sel:
            self.store.delete_pdf_term(int(sel[0]))
            self._refresh_pdf_terms()

    def _pdf_learned(self):
        sel = self.pdf_tree.selection()
        if sel:
            self.store.mark_pdf_term_learned(int(sel[0]), True)
            self._refresh_pdf_terms()

    def _pdf_export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            n = self.store.export_pdf_terms_csv(path)
            messagebox.showinfo("PDF Terms", f"Exported {n} terms.")

    def _pdf_import(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            n = self.store.import_pdf_terms_csv(path)
            self._refresh_pdf_terms()
            messagebox.showinfo("PDF Terms", f"Imported {n} terms.")

    def add_pdf_term_external(self, term, translation="", source_pdf="", page_number=0, note=""):
        """Called by the PDF Reader to push a selected term into the notebook."""
        self.store.add_pdf_term(term=term, translation=translation, source_pdf=source_pdf,
                                page_number=page_number, note=note)
        try:
            self._refresh_pdf_terms()
        except Exception:
            pass

    # ---- Tab: PDF Vocabulary Scanner ---- #
    def _build_vocab_scanner_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="PDF Vocabulary Scanner / PDF Kelime Tarayıcı")
        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=4, pady=(4, 2))
        for text, cmd in (("Scan PDFs", lambda: self._vocab_scan(False)),
                          ("Rebuild Index", lambda: self._vocab_scan(True)),
                          ("Refresh", self._refresh_vocab),
                          ("Add to Dictionary", self._vocab_add_dict),
                          ("Add to Favorites", self._vocab_fav),
                          ("Add to PDF Terms", self._vocab_add_pdf),
                          ("Mark Learned", self._vocab_learned),
                          ("Export CSV", self._vocab_export),
                          ("Open Source PDF", self._vocab_open_pdf),
                          ("Clear Filters", self._vocab_clear_filters)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=1)

        filt = ttk.Frame(tab)
        filt.pack(fill="x", padx=4, pady=2)
        ttk.Label(filt, text="Level:").pack(side="left")
        self.vc_level = ttk.Combobox(filt, state="readonly", width=11,
                                     values=["all", "B1", "B2", "C1", "C2", "TOEFL", "technical"])
        self.vc_level.current(0)
        self.vc_level.pack(side="left", padx=2)
        self.vc_level.bind("<<ComboboxSelected>>", lambda e: self._refresh_vocab())
        ttk.Label(filt, text="Category:").pack(side="left", padx=(6, 0))
        self.vc_cat = ttk.Combobox(filt, state="readonly", width=10,
                                   values=["all", "math", "science", "academic", "general"])
        self.vc_cat.current(0)
        self.vc_cat.pack(side="left", padx=2)
        self.vc_cat.bind("<<ComboboxSelected>>", lambda e: self._refresh_vocab())
        ttk.Label(filt, text="Status:").pack(side="left", padx=(6, 0))
        self.vc_status = ttk.Combobox(filt, state="readonly", width=9,
                                      values=["all", "new", "added", "learned", "favorite"])
        self.vc_status.current(0)
        self.vc_status.pack(side="left", padx=2)
        self.vc_status.bind("<<ComboboxSelected>>", lambda e: self._refresh_vocab())
        ttk.Label(filt, text="PDF:").pack(side="left", padx=(6, 0))
        self.vc_pdf = ttk.Combobox(filt, state="readonly", width=18, values=["all"])
        self.vc_pdf.current(0)
        self.vc_pdf.pack(side="left", padx=2)
        self.vc_pdf.bind("<<ComboboxSelected>>", lambda e: self._refresh_vocab())
        ttk.Label(filt, text="Freq≥").pack(side="left", padx=(6, 0))
        self.vc_freq = tk.StringVar(value="0")
        fe = ttk.Entry(filt, textvariable=self.vc_freq, width=4)
        fe.pack(side="left", padx=2)
        fe.bind("<Return>", lambda e: self._refresh_vocab())
        ttk.Label(filt, text="Search:").pack(side="left", padx=(6, 0))
        self.vc_query = tk.StringVar()
        se = ttk.Entry(filt, textvariable=self.vc_query, width=16)
        se.pack(side="left", padx=2)
        se.bind("<Return>", lambda e: self._refresh_vocab())

        self.vocab_progress = tk.Label(tab, text="", bg=BG, fg=ACCENT, font=("Segoe UI", 9), anchor="w")
        self.vocab_progress.pack(fill="x", padx=4)

        split = ttk.Panedwindow(tab, orient="horizontal")
        split.pack(fill="both", expand=True, padx=4, pady=4)
        left = ttk.Frame(split)
        split.add(left, weight=3)
        cols = ("term", "tr", "level", "tags", "cat", "freq", "pdf", "page", "status")
        self.vocab_tree = ttk.Treeview(left, columns=cols, show="headings", height=14, selectmode="browse")
        heads = {"term": ("Term", 130), "tr": ("Türkçe", 130), "level": ("Level", 90),
                 "tags": ("Tags", 150), "cat": ("Category", 80), "freq": ("Freq", 45),
                 "pdf": ("Source PDF", 150), "page": ("Pg", 40), "status": ("Status", 70)}
        for c in cols:
            t, w = heads[c]
            self.vocab_tree.heading(c, text=t)
            self.vocab_tree.column(c, width=w, anchor="w" if c in ("term", "tr", "tags", "pdf") else "center")
        self.vocab_tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(left, orient="vertical", command=self.vocab_tree.yview)
        vsb.pack(side="right", fill="y")
        self.vocab_tree.configure(yscrollcommand=vsb.set)
        self.vocab_tree.bind("<<TreeviewSelect>>", lambda e: self._on_vocab_select())

        right = ttk.Frame(split)
        split.add(right, weight=2)
        self.vocab_detail = tk.Text(right, wrap="word", bg=PANEL_BG, fg=FG, relief="flat",
                                    font=("Consolas", 10))
        self.vocab_detail.pack(fill="both", expand=True)
        self.vocab_detail.config(state="disabled")
        rb = ttk.Frame(right)
        rb.pack(fill="x")
        for text, cmd in (("Translate via LM", self._vocab_translate_lm),
                          ("Search in Dictionary", self._vocab_search_dict),
                          ("Open PDF", self._vocab_open_pdf)):
            ttk.Button(rb, text=text, command=cmd).pack(side="left", padx=2, pady=2)
        self._refresh_vocab()

    def _refresh_vocab(self):
        try:
            self.vc_pdf.configure(values=["all"] + self.vocab.distinct_pdfs())
        except Exception:
            pass
        try:
            min_freq = int(self.vc_freq.get() or 0)
        except Exception:
            min_freq = 0
        rows = self.vocab.list_terms(level=self.vc_level.get(), category=self.vc_cat.get(),
                                     status=self.vc_status.get(), source_pdf=self.vc_pdf.get(),
                                     min_frequency=min_freq, query=(self.vc_query.get() or "").strip())
        self._vocab_rows = list(rows)
        self.vocab_tree.delete(*self.vocab_tree.get_children())
        for r in rows:
            st = "fav" if r["favorite"] else ("learned" if r["learned"] else
                 ("added" if r["added_to_dictionary"] else r["status"]))
            self.vocab_tree.insert("", "end", iid=str(r["id"]),
                                   values=(r["term"], r["translation"], r["cefr_level"], r["tags"],
                                           r["category"], r["frequency"], Path(r["source_pdf"]).name,
                                           r["page_number"], st))
        self.vocab_progress.config(text=f"{len(rows)} terms shown / {self.vocab.count()} total")

    def _selected_vocab(self):
        sel = self.vocab_tree.selection()
        if not sel:
            return None
        return self.vocab.get(int(sel[0]))

    def _on_vocab_select(self):
        r = self._selected_vocab()
        if not r:
            return
        lines = [
            f"{r['term']}", "",
            f"Türkçe / Turkish : {r['translation'] or '(yok — Translate via LM)'}",
            f"CEFR/TOEFL level : {r['cefr_level']}",
            f"Difficulty score : {r['difficulty_score']}",
            f"Tags             : {r['tags']}",
            f"Category         : {r['category']}",
            f"Frequency        : {r['frequency']}",
            f"Source PDF       : {r['source_pdf']}",
            f"Page             : {r['page_number']}",
            f"In dictionary    : {'yes' if r['added_to_dictionary'] else 'no'}",
            f"Favorite         : {'yes' if r['favorite'] else 'no'}",
            f"Learned          : {'yes' if r['learned'] else 'no'}",
            "", "Context:", (r["context_sentence"] or ""),
        ]
        self._set_text(self.vocab_detail, "\n".join(lines))

    def _vocab_scan(self, rebuild=False):
        self.vocab_progress.config(text="Starting scan…")

        def progress(msg):
            self.after(0, lambda: self.vocab_progress.config(text=msg))

        def done(ok, info):
            self.after(0, lambda: (self.vocab_progress.config(text=info), self._refresh_vocab()))
        self.vocab_scanner.scan(progress_cb=progress, done_cb=done, rebuild=rebuild, background=True)

    def _vocab_add_dict(self):
        r = self._selected_vocab()
        if not r:
            return
        self.store.add_term(term=r["term"], translation=r["translation"], lang="en",
                            category=r["category"], example=r["context_sentence"],
                            source=r["source_pdf"])
        self.vocab.set_flag(r["id"], "added_to_dictionary", 1)
        self._refresh_vocab()
        self.vocab_progress.config(text=f"Added to dictionary: {r['term']}")

    def _vocab_add_pdf(self):
        r = self._selected_vocab()
        if not r:
            return
        self.store.add_pdf_term(term=r["term"], translation=r["translation"],
                                category=r["category"], source_pdf=r["source_pdf"],
                                page_number=r["page_number"], note=r["context_sentence"])
        try:
            self._refresh_pdf_terms()
        except Exception:
            pass
        self.vocab_progress.config(text=f"Added to PDF Terms: {r['term']}")

    def _vocab_fav(self):
        r = self._selected_vocab()
        if not r:
            return
        self.store.add_term(term=r["term"], translation=r["translation"], lang="en",
                            category=r["category"], source=r["source_pdf"])
        self.store.set_favorite(r["term"], True, "en")
        self.vocab.set_flag(r["id"], "favorite", 1)
        self._refresh_vocab()
        try:
            self._refresh_favorites()
        except Exception:
            pass

    def _vocab_learned(self):
        r = self._selected_vocab()
        if r:
            self.vocab.set_flag(r["id"], "learned", 1)
            self._refresh_vocab()

    def _vocab_export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            n = self.vocab.export_csv(path, self._vocab_rows)
            messagebox.showinfo("PDF Vocabulary", f"Exported {n} terms.")

    def _vocab_open_pdf(self):
        r = self._selected_vocab()
        if not r or not r["source_pdf"]:
            return
        try:
            p = Path(self.vocab_scanner.resources_dir) / r["source_pdf"]
            if p.exists():
                os.startfile(str(p))
            else:
                messagebox.showinfo("PDF", f"PDF not found:\n{r['source_pdf']}")
        except Exception as exc:
            messagebox.showerror("PDF", str(exc))

    def _vocab_search_dict(self):
        r = self._selected_vocab()
        if not r:
            return
        self.dict_query.set(r["term"])
        self.nb.select(0)
        self._do_search()

    def _vocab_translate_lm(self):
        r = self._selected_vocab()
        if not r:
            return
        self.vocab_progress.config(text=f"Translating {r['term']} via LM…")

        def work():
            return self.translator.lookup_word(r["term"], "English", "Turkish", "translation")

        def done(result):
            out, model, status = result
            if status == "ok":
                short = extract_short_translation(r["term"], out)
                self.vocab.set_flag(r["id"], "translation", short)
                self._refresh_vocab()
                self.vocab_progress.config(text=f"{r['term']} → {short}")
            else:
                self.vocab_progress.config(text=f"{r['term']}: {status}")
        self._run_async(work, done)

    def _vocab_clear_filters(self):
        self.vc_level.current(0)
        self.vc_cat.current(0)
        self.vc_status.current(0)
        self.vc_pdf.current(0)
        self.vc_freq.set("0")
        self.vc_query.set("")
        self._refresh_vocab()

    # ---- Tab 5: History ---- #
    def _build_history_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="History / Geçmiş")
        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=4, pady=4)
        for text, cmd in (("Refresh", self._refresh_history),
                          ("Search Again", self._history_again),
                          ("Add Manual", self._history_add_manual),
                          ("Edit Selected", self._history_edit_selected),
                          ("Delete Selected", self._history_delete_selected),
                          ("Clear History", self._history_clear),
                          ("Add to Dictionary", self._history_to_dictionary),
                          ("Add to Favorites", self._history_to_favorites)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=1)
        cols = ("time", "query", "tr", "result", "model")
        self.hist_tree = ttk.Treeview(tab, columns=cols, show="headings", height=16, selectmode="extended")
        for c, t, w in (("time", "Time", 140), ("query", "Query", 160),
                        ("tr", "Turkish / Türkçe Karşılık", 220),
                        ("result", "Result", 280), ("model", "Model", 130)):
            self.hist_tree.heading(c, text=t)
            self.hist_tree.column(c, width=w, anchor="w")
        self.hist_tree.pack(fill="both", expand=True, padx=4, pady=(4, 0))
        self.hist_tree.bind("<Double-1>", lambda e: self._history_again())
        self.hist_status = tk.Label(tab, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.hist_status.pack(fill="x", padx=4, pady=(0, 4))
        # Right-click context menu
        try:
            self._hist_menu = tk.Menu(self, tearoff=0)
            self._hist_menu.add_command(label="Search Again", command=self._history_again)
            self._hist_menu.add_command(label="Edit", command=self._history_edit_selected)
            self._hist_menu.add_command(label="Delete", command=self._history_delete_selected)
            self._hist_menu.add_separator()
            self._hist_menu.add_command(label="Add to Dictionary", command=self._history_to_dictionary)
            self._hist_menu.add_command(label="Add to Favorites", command=self._history_to_favorites)
            self.hist_tree.bind("<Button-3>", self._history_context_menu)
        except Exception:
            self._hist_menu = None
        self._refresh_history()

    def _refresh_history(self):
        self.hist_tree.delete(*self.hist_tree.get_children())
        for r in self.history.list_search():
            translation = self._display_translation(r, _row_value(r, "query"))
            self.hist_tree.insert("", "end", iid=str(r["id"]),
                                  values=(r["timestamp"], r["query"], translation,
                                          (r["result"] or "")[:80], r["model_used"]))

    def _history_again(self):
        sel = self.hist_tree.selection()
        if not sel:
            return
        vals = self.hist_tree.item(sel[0], "values")
        if vals:
            self.dict_query.set(vals[1])
            self.nb.select(0)
            self._do_search()

    # -- history management helpers -- #
    def _hist_status_set(self, msg):
        try:
            self.hist_status.config(text=msg)
        except Exception:
            pass

    def _history_selected_ids(self):
        ids = []
        for iid in self.hist_tree.selection():
            try:
                ids.append(int(iid))
            except Exception:
                pass
        return ids

    def _history_single_row(self):
        ids = self._history_selected_ids()
        if not ids:
            messagebox.showinfo("History", "Please select a history item.\n"
                                           "Lütfen bir geçmiş kaydı seçin.")
            return None
        return self.history.get_search_history_item(ids[0])

    def _history_context_menu(self, event):
        if self._hist_menu is None:
            return
        iid = self.hist_tree.identify_row(event.y)
        if iid and iid not in self.hist_tree.selection():
            self.hist_tree.selection_set(iid)
        try:
            self._hist_menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                self._hist_menu.grab_release()
            except Exception:
                pass

    def _history_dialog(self, title, initial, on_save):
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=BG)
        win.resizable(False, False)
        fields = [("Query / Aranan kelime", "query"), ("Turkish / Türkçe Karşılık", "translation"),
                  ("Result / Sonuç", "result"), ("Model Used / Model", "model_used"),
                  ("Category / Kategori", "category"), ("Source Context / Bağlam", "source_context")]
        vars_ = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=8, pady=3)
            v = tk.StringVar(value=str(initial.get(key, "") or ""))
            vars_[key] = v
            ttk.Entry(win, textvariable=v, width=50).grid(row=i, column=1, padx=8, pady=3)

        def save():
            data = {k: v.get().strip() for k, v in vars_.items()}
            if not data["query"]:
                messagebox.showwarning("History", "Query cannot be empty.\n"
                                                  "Aranan kelime boş olamaz.")
                return
            on_save(data)
            win.destroy()
        btns = ttk.Frame(win)
        btns.grid(row=len(fields), column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Save / Kaydet", command=save).pack(side="left", padx=4)
        ttk.Button(btns, text="Cancel / İptal", command=win.destroy).pack(side="left", padx=4)
        try:
            win.grab_set()
        except Exception:
            pass

    def _history_add_manual(self):
        def on_save(d):
            self.history.add_search_history_item(
                query=d["query"], result=d["result"], translation=d["translation"],
                model_used=d["model_used"] or "manual", category=d["category"] or "manual",
                source_context=d["source_context"])
            self._refresh_history()
            self._hist_status_set(f"Added manual history: {d['query']}")
        self._history_dialog("Add Manual History / Manuel Geçmiş Ekle",
                             {"model_used": "manual", "category": "manual"}, on_save)

    def _history_edit_selected(self):
        ids = self._history_selected_ids()
        if not ids:
            messagebox.showinfo("History", "Please select a history item.\n"
                                           "Lütfen bir geçmiş kaydı seçin.")
            return
        if len(ids) != 1:
            messagebox.showinfo("History", "Please select only one item to edit.\n"
                                           "Lütfen düzenlemek için tek kayıt seçin.")
            return
        row = self.history.get_search_history_item(ids[0])
        if not row:
            return
        keys = row.keys()
        initial = {k: (row[k] if k in keys else "") for k in
                   ("query", "translation", "result", "model_used", "category", "source_context")}

        def on_save(d):
            self.history.update_search_history_item(
                ids[0], query=d["query"], result=d["result"], translation=d["translation"],
                model_used=d["model_used"], category=d["category"], source_context=d["source_context"])
            self._refresh_history()
            self._hist_status_set(f"Updated history: {d['query']}")
        self._history_dialog("Edit History / Geçmişi Düzenle", initial, on_save)

    def _history_delete_selected(self):
        ids = self._history_selected_ids()
        if not ids:
            messagebox.showinfo("History", "Please select a history item.\n"
                                           "Lütfen bir geçmiş kaydı seçin.")
            return
        if not messagebox.askyesno("History", f"Delete selected history item(s)? ({len(ids)})\n"
                                              "Seçili geçmiş kayıtları silinsin mi?"):
            return
        n = self.history.delete_search_history_items(ids)
        self._refresh_history()
        self._hist_status_set(f"Deleted {n} history item(s).")

    def _history_clear(self):
        if not messagebox.askyesno("History", "This will delete all search history. Continue?\n"
                                              "Bu işlem tüm arama geçmişini silecek. Devam edilsin mi?"):
            return
        n = self.history.clear_search_history()
        self._refresh_history()
        self._hist_status_set(f"Cleared {n} history item(s).")

    def _history_to_dictionary(self):
        row = self._history_single_row()
        if not row:
            return
        query = row["query"]
        tr = self._display_translation(row, query)
        keys = row.keys()
        category = (row["category"] if "category" in keys else "") or "general"
        result = (row["result"] if "result" in keys else "") or ""
        self.store.add_term(term=query, translation=tr, lang="en", category=category,
                            definition=result, example=result, source="history")
        try:
            self._refresh_favorites()
        except Exception:
            pass
        self._hist_status_set(f"Added to dictionary: {query} → {tr}")

    def _history_to_favorites(self):
        row = self._history_single_row()
        if not row:
            return
        query = row["query"]
        tr = self._display_translation(row, query)
        self.store.add_term(term=query, translation=tr, lang="en", source="history")
        self.store.set_favorite(query, True, "en")
        try:
            self._refresh_favorites()
        except Exception:
            pass
        self._hist_status_set(f"Added to favorites: {query}")

    # ---- Tab 6: Frequent ---- #
    def _build_frequent_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Frequent / Sık Arananlar")
        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=4, pady=4)
        for text, cmd in (("Refresh", self._refresh_frequent),
                          ("Search Again", self._freq_open),
                          ("Edit Selected", self._freq_edit),
                          ("Add to Favorites", self._freq_to_fav),
                          ("Add to PDF Terms", self._freq_to_pdf),
                          ("Remove from Frequent", self._freq_remove),
                          ("Reset Count", self._freq_reset_count),
                          ("Clear Frequent Counts", self._freq_clear_counts),
                          ("Delete Term", self._freq_delete_term)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=1)
        cols = ("term", "tr", "cat", "n")
        self.freq_tree = ttk.Treeview(tab, columns=cols, show="headings", height=18, selectmode="browse")
        for c, t, w in (("term", "Term", 180), ("tr", "Turkish / Türkçe Karşılık", 230),
                        ("cat", "Category", 140), ("n", "Count", 70)):
            self.freq_tree.heading(c, text=t)
            self.freq_tree.column(c, width=w, anchor="w" if c != "n" else "center")
        self.freq_tree.pack(fill="both", expand=True, padx=4, pady=(4, 0))
        self.freq_tree.bind("<Double-1>", lambda e: self._freq_open())
        self.freq_status = tk.Label(tab, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.freq_status.pack(fill="x", padx=4, pady=(0, 4))
        try:
            self._freq_menu = tk.Menu(self, tearoff=0)
            for label, cmd in (("Search Again", self._freq_open), ("Edit", self._freq_edit),
                               ("Add to Favorites", self._freq_to_fav),
                               ("Add to PDF Terms", self._freq_to_pdf),
                               ("Remove from Frequent", self._freq_remove),
                               ("Reset Count", self._freq_reset_count),
                               ("Delete Term", self._freq_delete_term)):
                self._freq_menu.add_command(label=label, command=cmd)
            self.freq_tree.bind("<Button-3>", lambda e: self._popup_menu(self._freq_menu, self.freq_tree, e))
        except Exception:
            self._freq_menu = None
        self._refresh_frequent()

    def _refresh_frequent(self):
        self.freq_tree.delete(*self.freq_tree.get_children())
        for r in self.store.list_frequent():
            self.freq_tree.insert("", "end", iid=r["term"],
                                  values=(r["term"], self._display_translation(r),
                                          r["category"], r["search_count"]))

    def _freq_open(self):
        sel = self.freq_tree.selection()
        if sel:
            self.dict_query.set(sel[0])
            self.nb.select(0)
            self._do_search()

    # ---- Tab 7: Favorites ---- #
    def _build_favorites_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Favorites / Favoriler")
        bar = ttk.Frame(tab)
        bar.pack(fill="x", padx=4, pady=4)
        for text, cmd in (("Refresh", self._refresh_favorites),
                          ("Search Again", self._fav_open),
                          ("Edit Selected", self._fav_edit),
                          ("Remove from Favorites", self._fav_remove),
                          ("Add to PDF Terms", self._fav_to_pdf),
                          ("Add to History", self._fav_to_history),
                          ("Clear Favorites", self._fav_clear),
                          ("Delete Term", self._fav_delete_term)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=1)
        cols = ("term", "tr", "cat", "src")
        self.fav_tree = ttk.Treeview(tab, columns=cols, show="headings", height=18, selectmode="browse")
        for c, t, w in (("term", "Term", 170), ("tr", "Turkish / Türkçe Karşılık", 230),
                        ("cat", "Category", 140), ("src", "Source", 150)):
            self.fav_tree.heading(c, text=t)
            self.fav_tree.column(c, width=w, anchor="w")
        self.fav_tree.pack(fill="both", expand=True, padx=4, pady=(4, 0))
        self.fav_tree.bind("<Double-1>", lambda e: self._fav_open())
        self.fav_status = tk.Label(tab, text="", bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
        self.fav_status.pack(fill="x", padx=4, pady=(0, 4))
        try:
            self._fav_menu = tk.Menu(self, tearoff=0)
            for label, cmd in (("Search Again", self._fav_open), ("Edit", self._fav_edit),
                               ("Remove from Favorites", self._fav_remove),
                               ("Add to PDF Terms", self._fav_to_pdf),
                               ("Add to History", self._fav_to_history),
                               ("Delete Term", self._fav_delete_term)):
                self._fav_menu.add_command(label=label, command=cmd)
            self.fav_tree.bind("<Button-3>", lambda e: self._popup_menu(self._fav_menu, self.fav_tree, e))
        except Exception:
            self._fav_menu = None
        self._refresh_favorites()

    def _refresh_favorites(self):
        if not hasattr(self, "fav_tree"):
            return
        self.fav_tree.delete(*self.fav_tree.get_children())
        for r in self.store.list_favorites():
            self.fav_tree.insert("", "end", iid=r["term"],
                                 values=(r["term"], self._display_translation(r),
                                         r["category"], r["source"]))

    def _fav_open(self):
        sel = self.fav_tree.selection()
        if sel:
            self.dict_query.set(sel[0])
            self.nb.select(0)
            self._do_search()

    # -- Frequent / Favorites management helpers -- #
    def _popup_menu(self, menu, tree, event):
        if menu is None:
            return
        iid = tree.identify_row(event.y)
        if iid and iid not in tree.selection():
            tree.selection_set(iid)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    def _freq_status_set(self, msg):
        try:
            self.freq_status.config(text=msg)
        except Exception:
            pass

    def _fav_status_set(self, msg):
        try:
            self.fav_status.config(text=msg)
        except Exception:
            pass

    def _tree_selected_term(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Dictionary", "Please select an item.\nLütfen bir kayıt seçin.")
            return None
        return sel[0]

    def _selected_term_tr(self, term):
        rec = self.store.get_term_by_text(term, "en") or {}
        return rec.get("display_translation") or rec.get("translation") or ""

    def _term_edit_dialog(self, term):
        rec = self.store.get_term_by_text(term, "en")
        if not rec:
            return
        win = tk.Toplevel(self)
        win.title("Edit Term / Kelimeyi Düzenle")
        win.configure(bg=BG)
        win.resizable(False, False)
        fields = [("Term / Kelime", "term", True),
                  ("Turkish / Türkçe Karşılık", "translation", False),
                  ("Definition / Açıklama", "definition", False),
                  ("Category / Kategori", "category", False),
                  ("Source / Kaynak", "source", False),
                  ("Note / Not", "note", False)]
        vars_ = {}
        for i, (label, key, ro) in enumerate(fields):
            ttk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=8, pady=3)
            init = rec.get(key, "") or ""
            if key == "translation":
                init = rec.get("translation") or rec.get("display_translation") or ""
            v = tk.StringVar(value=str(init))
            vars_[key] = v
            ttk.Entry(win, textvariable=v, width=50,
                      state=("readonly" if ro else "normal")).grid(row=i, column=1, padx=8, pady=3)

        def save():
            d = {k: v.get().strip() for k, v in vars_.items()}
            self.store.update_term(term=term, translation=d["translation"], definition=d["definition"],
                                   category=d["category"], source=d["source"], note=d["note"])
            self._refresh_frequent()
            self._refresh_favorites()
            try:
                self._refresh_pdf_terms()
            except Exception:
                pass
            self._freq_status_set(f"Updated: {term} → {d['translation']}")
            self._fav_status_set(f"Updated: {term} → {d['translation']}")
            win.destroy()
        btns = ttk.Frame(win)
        btns.grid(row=len(fields), column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Save / Kaydet", command=save).pack(side="left", padx=4)
        ttk.Button(btns, text="Cancel / İptal", command=win.destroy).pack(side="left", padx=4)
        try:
            win.grab_set()
        except Exception:
            pass

    # -- Frequent actions -- #
    def _freq_edit(self):
        term = self._tree_selected_term(self.freq_tree)
        if term:
            self._term_edit_dialog(term)

    def _freq_to_fav(self):
        term = self._tree_selected_term(self.freq_tree)
        if not term:
            return
        self.store.set_favorite(term, True, "en")
        self._refresh_favorites()
        self._freq_status_set(f"Added to favorites: {term} → {self._selected_term_tr(term)}")

    def _freq_to_pdf(self):
        term = self._tree_selected_term(self.freq_tree)
        if not term:
            return
        rec = self.store.get_term_by_text(term, "en") or {}
        self.store.add_term_to_pdf_terms(term, self._selected_term_tr(term),
                                         note=rec.get("category", "") or rec.get("source", ""))
        try:
            self._refresh_pdf_terms()
        except Exception:
            pass
        self._freq_status_set(f"Added to PDF Terms: {term}")

    def _freq_remove(self):
        term = self._tree_selected_term(self.freq_tree)
        if not term:
            return
        self.store.hide_from_frequent(term)
        self._refresh_frequent()
        self._freq_status_set(f"Removed from frequent: {term}")

    def _freq_reset_count(self):
        term = self._tree_selected_term(self.freq_tree)
        if not term:
            return
        self.store.reset_search_count(term)
        self._refresh_frequent()
        self._freq_status_set(f"Reset count: {term}")

    def _freq_clear_counts(self):
        if not messagebox.askyesno("Frequent", "Reset ALL frequent counts to zero?\n"
                                              "Tüm sık aranan sayaçları sıfırlansın mı?\n\n"
                                              "(Terms are NOT deleted / Kelimeler silinmez.)"):
            return
        n = self.store.clear_all_frequent_counts()
        self._refresh_frequent()
        self._freq_status_set(f"Cleared {n} frequent counts (terms kept).")

    def _freq_delete_term(self):
        term = self._tree_selected_term(self.freq_tree)
        if not term:
            return
        if not messagebox.askyesno("Delete Term",
                                   "This will PERMANENTLY delete the term from the dictionary. Continue?\n"
                                   f"'{term}' kelimesi sözlükten KALICI olarak silinecek. Devam edilsin mi?",
                                   icon="warning"):
            return
        self.store.delete_term(term)
        self._refresh_frequent()
        self._refresh_favorites()
        self._freq_status_set(f"Deleted term: {term}")

    # -- Favorites actions -- #
    def _fav_edit(self):
        term = self._tree_selected_term(self.fav_tree)
        if term:
            self._term_edit_dialog(term)

    def _fav_remove(self):
        term = self._tree_selected_term(self.fav_tree)
        if not term:
            return
        self.store.set_favorite(term, False, "en")
        self._refresh_favorites()
        self._fav_status_set(f"Removed from favorites: {term}")

    def _fav_to_pdf(self):
        term = self._tree_selected_term(self.fav_tree)
        if not term:
            return
        rec = self.store.get_term_by_text(term, "en") or {}
        self.store.add_term_to_pdf_terms(term, self._selected_term_tr(term),
                                         note=rec.get("category", "") or rec.get("source", ""))
        try:
            self._refresh_pdf_terms()
        except Exception:
            pass
        self._fav_status_set(f"Added to PDF Terms: {term}")

    def _fav_to_history(self):
        term = self._tree_selected_term(self.fav_tree)
        if not term:
            return
        rec = self.store.get_term_by_text(term, "en") or {}
        self.store.add_term_to_history(term, self._selected_term_tr(term),
                                       result=rec.get("definition", "") or rec.get("example", ""),
                                       model_used="favorite", category=rec.get("category", ""))
        try:
            self._refresh_history()
        except Exception:
            pass
        self._fav_status_set(f"Added to history: {term}")

    def _fav_clear(self):
        if not messagebox.askyesno("Favorites", "Remove ALL terms from favorites?\n"
                                               "Tüm favoriler kaldırılsın mı?\n\n"
                                               "(Terms are NOT deleted / Kelimeler silinmez.)"):
            return
        n = self.store.clear_all_favorites()
        self._refresh_favorites()
        self._fav_status_set(f"Cleared {n} favorites (terms kept).")

    def _fav_delete_term(self):
        term = self._tree_selected_term(self.fav_tree)
        if not term:
            return
        if not messagebox.askyesno("Delete Term",
                                   "This will PERMANENTLY delete the term from the dictionary. Continue?\n"
                                   f"'{term}' kelimesi sözlükten KALICI olarak silinecek. Devam edilsin mi?",
                                   icon="warning"):
            return
        self.store.delete_term(term)
        self._refresh_favorites()
        self._refresh_frequent()
        self._fav_status_set(f"Deleted term: {term}")

    # ---- Tab 8: Model Profiles ---- #
    def _build_profiles_tab(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Model Profiles / Model Profilleri")
        status = ttk.Frame(tab)
        status.pack(fill="x", padx=6, pady=6)
        ttk.Label(status, text=f"Server: {self.translator.base_url}").pack(side="left")
        self.prof_status = tk.Label(status, text="(not checked)", bg=BG, fg=MUTED, font=("Segoe UI", 9, "bold"))
        self.prof_status.pack(side="left", padx=10)
        ttk.Button(status, text="Refresh Models", command=self._refresh_models).pack(side="right", padx=2)
        ttk.Button(status, text="Test Translation Model", command=lambda: self._test_profile("translation")).pack(side="right", padx=2)
        ttk.Button(status, text="Test Vision Model", command=self._test_vision).pack(side="right", padx=2)

        body = ttk.Panedwindow(tab, orient="horizontal")
        body.pack(fill="both", expand=True, padx=6, pady=4)
        left = ttk.Frame(body)
        body.add(left, weight=2)
        ttk.Label(left, text="Profile assignments (editable):", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.prof_vars = {}
        for prof in DEFAULT_PROFILES:
            row = ttk.Frame(left)
            row.pack(fill="x", pady=1)
            ttk.Label(row, text=prof, width=24).pack(side="left")
            var = tk.StringVar(value=self.profiles.get(prof))
            self.prof_vars[prof] = var
            ent = ttk.Entry(row, textvariable=var, width=34)
            ent.pack(side="left", padx=2)
            ttk.Button(row, text="Save", width=6,
                       command=lambda p=prof: self._save_profile(p)).pack(side="left", padx=2)

        right = ttk.Frame(body)
        body.add(right, weight=2)
        ttk.Label(right, text="Available models / Recommended:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.prof_info = tk.Text(right, wrap="word", bg=PANEL_BG, fg=FG, relief="flat", font=("Consolas", 9))
        self.prof_info.pack(fill="both", expand=True)
        self.prof_info.config(state="disabled")
        self._render_profile_info([], status="(press Refresh Models)")

    def _render_profile_info(self, models, status=""):
        lines = [f"Status: {status}", ""]
        if models:
            lines.append("Loaded models:")
            lines += [f"  - {m}" for m in models]
            lines.append("")
            lines.append("Suggested mapping for your models:")
            for p, m in self.profiles.suggest(models).items():
                lines.append(f"  {p}: {m}")
        lines += ["", "Optional recommended vision models (not required):"]
        for name, why in RECOMMENDED_VISION:
            lines.append(f"  - {name} — {why}")
        lines += ["", "The system works with moondream-2b by default."]
        self._set_text(self.prof_info, "\n".join(lines))

    def _refresh_models(self):
        self.prof_status.config(text="checking…", fg=ACCENT)

        def work():
            return self.translator.server_status()

        def done(result):
            status, models = result
            self.prof_status.config(text=status, fg=STATUS_COLORS.get(status, MUTED))
            msg = {"connected": "LM Studio reachable, model(s) loaded.",
                   "no_model": NO_MODEL_MSG, "no_server": NO_SERVER_MSG}.get(status, status)
            self._render_profile_info(models, msg)
        self._run_async(work, done)

    def _save_profile(self, prof):
        self.profiles.set(prof, self.prof_vars[prof].get().strip())
        self.prof_status.config(text=f"saved {prof}", fg=STATUS_COLORS["connected"])

    def _test_profile(self, profile):
        self.prof_status.config(text="testing…", fg=ACCENT)

        def work():
            return self.translator.translate("Hello, this is a test.", "English", "Turkish", profile)

        def done(result):
            out, model, status = result
            self.prof_status.config(text=f"{status} ({model or '-'})", fg=STATUS_COLORS.get(status, MUTED))
            self._render_profile_info([], f"Test result:\n{out[:300]}")
        self._run_async(work, done)

    def _test_vision(self):
        client = getattr(self.app, "client", None)
        if client is None:
            self.prof_status.config(text="no app client", fg=STATUS_COLORS["error"])
            return
        status, models = self.translator.server_status()
        if status != "connected":
            self.prof_status.config(text=status, fg=STATUS_COLORS.get(status, MUTED))
            self._render_profile_info(models, NO_MODEL_MSG if status == "no_model" else NO_SERVER_MSG)
            return
        self.prof_status.config(text="vision ok (load image to test fully)", fg=STATUS_COLORS["connected"])

    # -- small utils -- #
    def _copy(self, text):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass
