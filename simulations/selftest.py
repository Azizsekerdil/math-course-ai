# -*- coding: utf-8 -*-
"""Paketlenmiş programın (EXE/.app) simülasyon öz testi.

    "Math Course AI.exe" --sim-selftest rapor.txt

Pencere açmadan önce çalışır: her gömülü örneği iki dilde çözer, ilk ve son
karesini çizer, PDF tarayıcısının çalıştığını ve (Tk varsa) oynatıcı
penceresinin açılıp oynadığını doğrular. Raporun son satırı
"RESULT: <n> passed, <m> failed" biçimindedir; çıkış kodu başarısızlıkta 1.

Amaç: "kaynakta çalışıyor ama EXE'de çalışmıyor" durumunu (eksik paketlenmiş
modül, sympy ayrıştırıcısı, pypdf) derleme sırasında yakalamak.
"""

from __future__ import annotations

import sys
import tempfile
import time
import traceback
from pathlib import Path


def run(out_path=None, gui=True):
    lines, counts = [], {"ok": 0, "fail": 0}

    def rec(ok, label):
        counts["ok" if ok else "fail"] += 1
        lines.append(("[PASS] " if ok else "[FAIL] ") + label)

    t0 = time.time()
    try:
        from simulations import engine, scanner
        st = engine.stats()
        rec(st["kinds"] > 0 and st["examples"] > 0,
            f"motor yüklendi: {st['kinds']} tür, {st['examples']} örnek, {st['per_course']}")
    except Exception:
        rec(False, "motor yüklenemedi:\n" + traceback.format_exc())
        return _finish(lines, counts, out_path, t0)

    bad = []
    for ex in engine.all_examples():
        try:
            for lang in ("tr", "en"):
                sim = engine.Simulation(ex, lang)
                if not sim.solution()["answer"]:
                    raise ValueError("boş cevap")
            n = sim.build(engine.new_figure())[0]
            engine.render_frames(sim, [0, n - 1], size=(5, 3.4), dpi=40)
        except Exception as e:
            bad.append(f"{ex['id']}: {type(e).__name__}: {e}")
    rec(not bad, f"tüm örnekler çözülür ve çizilir ({len(engine.all_examples()) - len(bad)}"
                 f"/{len(engine.all_examples())})" + ("".join("\n    " + b for b in bad[:20])))

    try:
        res = scanner.classify("Find the derivative of f(x) = 3x2 - 5x + 2 at x = 1.")
        rec(res is not None and res[1].get("f") == "3*x**2 - 5*x + 2",
            f"tarayıcı sympy ayrıştırıcısı çalışır ({res})")
    except Exception:
        rec(False, "tarayıcı:\n" + traceback.format_exc())
    rec(scanner.pdf_support(), "PDF metin desteği var (pypdf veya PyMuPDF)")

    try:
        d = Path(tempfile.mkdtemp(prefix="mcai-selftest-"))
        (d / "ornek.txt").write_text("Example. Solve x^2 - 5x + 6 = 0.\n", encoding="utf-8")
        out = scanner.scan(d, "alg", change=False)
        rec(any(e["kind"] == "quadratic" for e in out["examples"]), "kaynak taraması örnek üretir")
    except Exception:
        rec(False, "tarama:\n" + traceback.format_exc())

    if gui:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.language = "tr"
            from simulations.player import open_player
            win = open_player(root, None, "Calculus 1", ("02 Notes", "Derivatives"), lang="tr")
            t = time.time()
            while time.time() - t < 2.0:
                root.update()
                time.sleep(0.01)
            ok = win.sim is not None and win.frame > 0
            rec(ok, f"oynatıcı penceresi açılır ve oynar ({win.sim.id if win.sim else None}, "
                    f"kare {win.frame}/{win.n_frames})")
            win.close()
            root.destroy()
        except Exception:
            rec(False, "oynatıcı penceresi:\n" + traceback.format_exc())
    return _finish(lines, counts, out_path, t0)


def _finish(lines, counts, out_path, t0):
    lines.append(f"RESULT: {counts['ok']} passed, {counts['fail']} failed ({time.time() - t0:.0f} s)")
    text = "\n".join(lines) + "\n"
    if out_path:
        Path(out_path).write_text(text, encoding="utf-8")
    else:
        try:
            sys.stdout.write(text)
        except Exception:
            pass
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else None))
