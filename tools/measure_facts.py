# -*- coding: utf-8 -*-
"""Measure every number the README and the presentation are allowed to claim.

Rule for this repository: a public document may not state a count that this
script did not produce. Nothing here is copied from an older document.

    python tools/measure_facts.py            # human readable
    python tools/measure_facts.py --json     # machine readable

Import-time side effects are avoided by pointing the app's data folders at a
temporary directory before any application module is imported.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_TMP = Path(tempfile.mkdtemp(prefix="mcai-measure-"))
os.environ.setdefault("MATH_COURSE_AI_SETTINGS", str(_TMP / "settings"))
os.environ.setdefault("MATH_COURSE_AI_EXPORTS", str(_TMP / "exports"))
os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, str(ROOT))

TEST_SUITES = [
    "test_visual_math_lab.py", "test_language_dictionary.py",
    "test_student_tracker.py", "test_topic_knowledge.py",
    "test_workspace_docking_manager.py", "test_ai_terminal.py",
    "test_egitim_token.py", "test_ai_code_guard.py", "test_public_claims.py",
    "smoke_dark_theme.py", "smoke_lazy_panels.py",
]


def _count_sqlite_tables():
    """CREATE TABLE statements across the two SQLite-backed modules."""
    total, per_file = 0, {}
    for name in ("student_tracker.py", "language_dictionary.py"):
        src = (ROOT / name).read_text(encoding="utf-8")
        n = len(re.findall(r"CREATE TABLE IF NOT EXISTS\s+(\w+)", src))
        per_file[name] = n
        total += n
    return total, per_file


def _count_python_modules():
    py = sorted(p.name for p in ROOT.glob("*.py")
                if not p.name.startswith(("test_", "smoke_")))
    return len(py) + 1, py            # +1 for the .pyw entry point


def _count_test_functions():
    total, per_file = 0, {}
    for s in TEST_SUITES:
        p = ROOT / s
        if not p.is_file():
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        # every call to check(...) is one assertion the suite prints
        n = sum(1 for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "check")
        per_file[s] = n
        total += n
    return total, per_file


def measure():
    facts = {}

    import topic_knowledge
    import topic_knowledge_round2
    base = dict(topic_knowledge.TOPIC_KNOWLEDGE)
    extra = getattr(topic_knowledge_round2, "TOPIC_KNOWLEDGE_ROUND2", {})
    merged = dict(base)
    merged.update(extra or {})
    facts["topic_knowledge_entries"] = len(merged)
    facts["topic_knowledge_entries_base"] = len(base)

    import embedded_course_simulations as ecs
    import embedded_formula_library as efl
    facts["embedded_simulations"] = int(getattr(ecs, "EMBEDDED_COUNT", 0)) or len(
        getattr(ecs, "EMBEDDED_SIMULATIONS", []) or [])
    facts["formula_cards"] = int(getattr(efl, "FORMULA_COUNT", 0)) or len(
        getattr(efl, "FORMULAS", []) or [])

    import education
    facts["guide_chapters"] = int(getattr(education, "BOLUM_SAYISI", 0))

    import tanitim_icerik
    facts["presentation_slides"] = len(tanitim_icerik.SLAYTLAR)

    # WORKSPACE_KEYS lives in the .pyw entry point; read it statically rather
    # than importing the GUI main module.
    src = (ROOT / "Math_Course_AI.pyw").read_text(encoding="utf-8")
    m = re.search(r"^WORKSPACE_KEYS = (\[.*?\])$", src, re.M)
    keys = ast.literal_eval(m.group(1)) if m else []
    labs = [k for k in keys if k in ("Data", "Physics", "Chemistry", "DNA", "Quantum")]
    facts["workspaces"] = len(keys)
    facts["science_labs"] = len(labs)
    facts["workspace_tab_entries"] = len(keys) - len(labs) + (1 if labs else 0)

    import ai_code_guard
    facts["code_guard_allowed_modules"] = len(ai_code_guard.ALLOWED_MODULES)
    facts["code_guard_blocked_builtins"] = len(ai_code_guard.BLOCKED_BUILTINS)
    facts["code_execution_default_enabled"] = ai_code_guard.execution_enabled({})

    import nvidia_provider
    facts["cloud_providers"] = 1
    facts["cloud_models"] = len(nvidia_provider.MODELLER)

    tables, per_file = _count_sqlite_tables()
    facts["sqlite_tables"] = tables
    facts["sqlite_tables_per_module"] = per_file

    mods, names = _count_python_modules()
    facts["python_modules"] = mods

    checks, per_suite = _count_test_functions()
    facts["test_suites"] = len([s for s in TEST_SUITES if (ROOT / s).is_file()])
    facts["test_assertions_static"] = checks
    facts["test_assertions_per_suite"] = per_suite

    facts["screenshots"] = len(list((ROOT / "tanitim_gorseller").rglob("*.png")))
    return facts


if __name__ == "__main__":
    f = measure()
    if "--json" in sys.argv:
        print(json.dumps(f, indent=2, ensure_ascii=False))
    else:
        for k, v in f.items():
            if isinstance(v, dict):
                print("%-34s" % k)
                for kk, vv in v.items():
                    print("    %-32s %s" % (kk, vv))
            else:
                print("%-34s %s" % (k, v))
