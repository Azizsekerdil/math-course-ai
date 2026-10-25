# -*- coding: utf-8 -*-
"""Render a contact sheet of simulation frames to a PNG for visual review.

    python tools/sim_preview.py <example_id|kind> [out.png] [--en] [--seed N]
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from simulations import engine  # noqa: E402


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    key = args[0]
    out = Path(args[1]) if len(args) > 1 else Path(f"preview_{key}.png")
    ex = engine.example_by_id(key) or next(
        (e for e in engine.all_examples() if e["kind"] == key), None)
    if ex is None:
        print("unknown id/kind:", key)
        return 2
    sim = engine.Simulation(ex, "en" if "--en" in sys.argv else "tr")
    if "--seed" in sys.argv:
        sim = sim.varied(int(sys.argv[sys.argv.index("--seed") + 1]))
    n = sim.build(engine.new_figure())[0]
    idx = sorted({int(round(k * (n - 1) / 5)) for k in range(6)})
    _, imgs = engine.render_frames(sim, idx, size=(8, 5.4), dpi=70)
    w, h = imgs[0].size
    sheet = Image.new("RGB", (w * 3, h * 2), "white")
    for k, im in enumerate(imgs):
        sheet.paste(im, ((k % 3) * w, (k // 3) * h))
    sheet.save(out)
    sol = sim.solution()
    print("Q:", sim.question())
    print("A:", sol["answer"])
    for s in sol["steps"]:
        print("  -", s)
    print("frames:", n, "->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
