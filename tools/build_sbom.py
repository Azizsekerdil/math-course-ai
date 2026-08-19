# -*- coding: utf-8 -*-
"""Generate sbom.spdx.json / sbom.cdx.json, with build-machine paths removed.

Syft records the directory it scanned. On any developer machine that is an
absolute path containing the operator's user name, and a published SBOM should
not carry it. This wrapper runs syft (if available) and then rewrites every
absolute path in the output to the repository name, so the SBOM is about the
project rather than about whoever built it.

    python tools/build_sbom.py             # regenerate + sanitise
    python tools/build_sbom.py --sanitise  # sanitise existing files only
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = "math-course-ai"
OUTPUTS = {"spdx-json": ROOT / "sbom.spdx.json",
           "cyclonedx-json": ROOT / "sbom.cdx.json"}

#: Any absolute Windows or POSIX path, and any file:// URL built from one.
_ABS = re.compile(r"(?:[A-Za-z]:\\\\[^\"\\\\]*(?:\\\\[^\"\\\\]*)*"
                  r"|[A-Za-z]:\\[^\"\\]*(?:\\[^\"\\]*)*"
                  r"|/(?:home|Users|mnt|opt|srv)/[^\"\s]*)")


def sanitise(path: Path) -> int:
    if not path.is_file():
        print("   [skip] %s not present" % path.name)
        return 0
    text = path.read_text(encoding="utf-8")
    before = len(_ABS.findall(text))
    text = _ABS.sub(PROJECT, text)
    # keep it valid JSON and stable
    data = json.loads(text)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    after = len(_ABS.findall(path.read_text(encoding="utf-8")))
    print("   [ok] %s: %d absolute paths removed (%d left)"
          % (path.name, before - after, after))
    return before - after


def generate() -> bool:
    syft = shutil.which("syft")
    if not syft:
        print("syft not on PATH - skipping generation, sanitising existing files")
        return False
    for fmt, out in OUTPUTS.items():
        subprocess.run([syft, "scan", "dir:%s" % ROOT, "-o", "%s=%s" % (fmt, out), "-q"],
                       check=True)
        print("   [ok] generated", out.name)
    return True


def main(argv):
    print("Math Course AI - SBOM")
    if "--sanitise" not in argv:
        generate()
    for out in OUTPUTS.values():
        sanitise(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
