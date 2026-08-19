# -*- coding: utf-8 -*-
"""
Lightweight UI preference store for the Math Course AI program.

Currently used for the Smart Wacom Student Board visibility / pop-out state so
the user's choice survives a restart. Pure and head-less testable: never raises
on a missing or corrupted file (falls back to defaults).
"""

import json
from pathlib import Path

from app_paths import settings_dir as _settings_dir

SETTINGS_DIR = _settings_dir()
PREFS_PATH = SETTINGS_DIR / "ui_preferences.json"

DEFAULTS = {
    "wacom_visible": True,
    "wacom_width": 600,
    "wacom_floating": False,
    "wacom_window_geometry": "900x600+200+100",
}


class UIPreferences:
    """Reads/writes a small JSON of UI preferences with safe defaults."""

    def __init__(self, path=None, defaults=None):
        self.path = Path(path) if path else PREFS_PATH
        self.defaults = dict(defaults if defaults is not None else DEFAULTS)

    def load(self):
        """Return defaults merged with whatever is on disk. Missing/corrupted
        files yield the defaults (never raises)."""
        data = dict(self.defaults)
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as fh:
                    disk = json.load(fh)
                if isinstance(disk, dict):
                    data.update(disk)
        except Exception:
            pass
        return data

    def save(self, data):
        """Persist the full dict (merged onto current). Returns True on success."""
        try:
            current = self.load()
            current.update(data or {})
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(current, fh, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get(self, key, default=None):
        return self.load().get(key, self.defaults.get(key, default))

    def set(self, key, value):
        """Update a single key and persist. Returns True on success."""
        return self.save({key: value})
