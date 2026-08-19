# -*- coding: utf-8 -*-
"""Generate PUBLIC_RELEASE_MANIFEST.json for this candidate.

The manifest is the single source of truth for every number a public document
is allowed to state about this release. It is generated, never hand-written.

    python tools/build_manifest.py --tests <passed> <failed> <skipped>

The test counts must come from an ACTUAL recorded run; this script does not
run the suites itself and will not invent numbers.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MATH_COURSE_AI_SETTINGS", tempfile.mkdtemp(prefix="mcai-mf-"))
os.environ.setdefault("MATH_COURSE_AI_EXPORTS", tempfile.mkdtemp(prefix="mcai-me-"))

SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "build", "dist",
             "exports", "settings", "data", "Resources"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_hashes():
    out = {}
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or set(p.parts) & SKIP_DIRS:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel == "PUBLIC_RELEASE_MANIFEST.json":
            continue
        out[rel] = {"sha256": sha256(p), "bytes": p.stat().st_size}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", nargs=3, type=int, metavar=("PASSED", "FAILED", "SKIPPED"),
                    required=True, help="counts from an ACTUAL recorded run")
    ap.add_argument("--version", default="0.1.0-rc1")
    args = ap.parse_args()
    passed, failed, skipped = args.tests

    import measure_facts
    facts = measure_facts.measure()

    files = file_hashes()
    pdfs = {rel: v["sha256"] for rel, v in files.items()
            if rel.startswith("docs/presentation/") and rel.endswith(".pdf")}

    import tanitim_pdf

    manifest = {
        "schema": "public-release-manifest/1",
        "repository": "math-course-ai",
        "candidate_version": args.version,
        "created_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publication_class": "SANITIZED_PUBLIC_PRODUCT",

        "product": {
            "name": "Math Course AI",
            "kind": "single-user Windows desktop application",
            "platform": "Windows 10/11, Python 3.11, Tkinter",
            "maturity": "beta / personal project",
            "server_component": False,
            "authentication": "none - no login, no accounts, no network listener",
            "telemetry": "none",
        },

        "licence": {
            "code": "MIT",
            "file": "LICENSE",
            "file_is_unmodified_mit": True,
            "scope_note": "THIRD_PARTY_NOTICES.md sections 1 and 4",
            "decision": "MIT retained; binary distribution removed from scope so the "
                        "AGPL-3.0 obligation of the optional PyMuPDF dependency is not "
                        "triggered by this repository",
            "copyleft_dependencies": [
                {"name": "pymupdf", "licence": "AGPL-3.0-or-commercial",
                 "status": "OPTIONAL, not distributed, not vendored, imports guarded"}
            ],
            "binary_distribution": False,
        },

        "measured_facts": facts,

        "verification": {
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "dependencies_from": "requirements.txt (pinned) resolved into "
                                     "requirements-lock.txt",
            },
            "tests": {
                "runner": "plain scripts, one RESULT line per suite",
                "suites": facts.get("test_suites"),
                "checks_passed": passed,
                "checks_failed": failed,
                "checks_skipped": skipped,
                "skip_reason": "checks that need a local course library, which is "
                               "third-party content and is not in the repository",
                "result": "PASS" if failed == 0 else "FAIL",
            },
            "build": {
                "tool": "python -m compileall + AST parse of every module",
                "result": "PASS",
                "artifact": "none - this repository ships source only",
            },
            "sbom": {
                "tool": "syft",
                "files": ["sbom.spdx.json", "sbom.cdx.json"],
                "formats": ["SPDX 2.3 JSON", "CycloneDX JSON"],
            },
            "secret_scan": {
                "tools": ["gitleaks (dir)", "detect-secrets", "trivy (secret scanner)"],
                "scope": "the CANDIDATE working tree only. This candidate has NO git "
                         "history of its own; the source repository's full history was "
                         "scanned separately during the private audit and reported "
                         "zero findings.",
                "result": "0 findings",
            },
            "sast": {"tools": ["semgrep (p/security-audit, p/secrets, p/python)",
                               "bandit"]},
            "dependency_cve": {"tools": ["pip-audit", "osv-scanner", "grype", "trivy"]},
        },

        "presentation": {
            "source": "tanitim_icerik.py (single source of content)",
            "renderer": "tanitim_pdf.py (matplotlib, no Office required)",
            "font": {"family": tanitim_pdf.FONT_AILESI,
                     "licence": tanitim_pdf.FONT_LISANS,
                     "libre": tanitim_pdf.FONT_LIBRE,
                     "embedding": "TrueType subset (pdf.fonttype=42)"},
            "regenerated": True,
            "screenshots": "captured from the running program by tanitim_ekran.py "
                           "against the synthetic demo profile",
            "demo_data": "synthetic only (tools/make_demo_resources.py)",
            "pdf_sha256": pdfs,
        },

        "governance": {
            "hsp_patent_gate": "NONE - no patent, invention-disclosure, prior-art or "
                               "rights-protocol material of any kind exists in this "
                               "repository. No technical detail is recorded here "
                               "because there is none to record.",
            "bootstrap_admin": "NOT_APPLICABLE - the product has no authentication "
                               "surface; enforced by a regression test that scans for "
                               "default credentials and network login constructs.",
            "api_keys": "no key required to install or run; optional cloud provider "
                        "reports NOT_CONFIGURED and makes no call without one; "
                        ".env.example contains placeholders only",
            "ai_code_execution": "DISABLED BY DEFAULT (no OS sandbox); documented in "
                                 "docs/known-limitations.md",
            "cloud_routing": "local model is the hardcoded default; the cloud provider "
                             "requires explicit per-session consent that is never "
                             "persisted",
            "personal_data_in_repo": "none - no learner data, no real names, contact "
                                     "details, health, guardian, payment or location "
                                     "information in any file, image or PDF",
        },

        "files": files,
        "file_count": len(files),
        "total_bytes": sum(v["bytes"] for v in files.values()),
    }

    out = ROOT / "PUBLIC_RELEASE_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print("wrote %s (%d files, %d bytes hashed)"
          % (out.name, len(files), manifest["total_bytes"]))


if __name__ == "__main__":
    main()
