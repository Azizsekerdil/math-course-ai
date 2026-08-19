# -*- coding: utf-8 -*-
"""
app_paths — shared user-data locations
======================================

User data (SQLite databases) lives in %APPDATA%\\MathCourseAI\\data so that it
survives program moves, PyInstaller rebuilds and reinstalls. Before V43 the
databases lived next to the source in <project>\\data; the first import copies
any databases found there into the new location (copy, never move/overwrite,
never delete — the old folder stays as a backup).

Content that ships WITH the program (external question packs) stays
program-relative: see packs_dir().
"""

import os
import sys
import shutil
from pathlib import Path

_APPDATA_ROOT = Path(os.getenv("APPDATA") or Path.home())
APP_FOLDER = _APPDATA_ROOT / "MathCourseAI"
DATA_DIR = APP_FOLDER / "data"


def _program_dir():
    """Folder of the running program: the source folder in dev, the folder of
    the EXE when frozen (PyInstaller sets sys.frozen; __file__ would point at
    the temporary extraction dir)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _legacy_data_candidates():
    """Pre-V43 database locations, relative to the running program only.

    NOTE: this used to also carry the original author's absolute development
    path. That is machine-specific, useless on any other computer, and leaks
    the maintainer's folder layout, so it is gone. Anyone migrating from an
    unusual location can point MATH_COURSE_AI_LEGACY_DATA at it.
    """
    base = _program_dir()
    cands = [base / "data", base.parent / "data"]   # dist\data or project\data
    extra = (os.getenv("MATH_COURSE_AI_LEGACY_DATA") or "").strip()
    if extra:
        cands.append(Path(extra))
    return cands


def _migrate_legacy_data():
    """One-time, additive copy of old project-folder databases into APPDATA.
    Files already present in the new location are never overwritten."""
    for legacy in _legacy_data_candidates():
        try:
            if not legacy.is_dir() or legacy.resolve() == DATA_DIR.resolve():
                continue
            for src in legacy.iterdir():
                if not src.is_file():
                    continue
                dst = DATA_DIR / src.name
                if not dst.exists():
                    shutil.copy2(src, dst)
        except Exception:
            continue


try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_data()
except Exception:
    # Last resort (e.g. exotic permissions): fall back to a program-local
    # data folder so the app still starts.
    DATA_DIR = _program_dir() / "data"
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# ── Portable, per-installation folders ──────────────────────────────────────
# Every one of these was a hardcoded absolute path on the original author's
# machine. They are now resolved from (1) an environment variable, so a
# packaged or multi-user install can redirect them, else (2) the folder of the
# running program. Nothing here names a specific computer.

ENV_RESOURCES = "MATH_COURSE_AI_RESOURCES"
ENV_EXPORTS = "MATH_COURSE_AI_EXPORTS"
ENV_SETTINGS = "MATH_COURSE_AI_SETTINGS"


def _resolve(env_var, default_name):
    raw = (os.getenv(env_var) or "").strip()
    return Path(raw) if raw else (_program_dir() / default_name)


def resources_dir():
    """Folder holding the user's own course PDFs. NOT shipped, NOT redistributed.

    Course material is third-party content; see LICENSE and THIRD_PARTY_NOTICES.md.
    """
    return _resolve(ENV_RESOURCES, "Resources")


def exports_dir():
    """Where the program writes graphs, lesson cards, reports the user asks for."""
    return _resolve(ENV_EXPORTS, "exports")


def settings_dir():
    """Per-installation UI/session state (layouts, preferences)."""
    return _resolve(ENV_SETTINGS, "settings")


def packs_dir():
    """Folder for external openly-licensed question packs (program content,
    not user data): <program>\\question_packs."""
    return _program_dir() / "question_packs"
