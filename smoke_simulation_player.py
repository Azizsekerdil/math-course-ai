# -*- coding: utf-8 -*-
"""Simülasyon Oynatıcı smoke paketi (gerçek Tk penceresi).

Oynatıcı penceresini kurs ağacının kullandığı open_player() yoluyla açar ve
kullanıcının yapacağı her şeyi sırayla dener: oynat, duraklat, adım, başa
sar, kareye atla, hız, yeni sayılar, kod düzenleyip çalıştırma (geçerli ve
politikaya takılan kod), filtre değiştirme, kaynak tarama ve kapatma.
Ana programda ▶ sütununun bağlı olduğu da kaynak üzerinden doğrulanır.

Ekran yoksa (headless Linux) Tk testleri ATLANIR ve bu sayılır.
"""

import io
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MATH_COURSE_AI_SETTINGS", tempfile.mkdtemp(prefix="mcai-sp-s-"))
os.environ.setdefault("MATH_COURSE_AI_EXPORTS", tempfile.mkdtemp(prefix="mcai-sp-e-"))
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

PASSED = FAILED = SKIPPED = 0


def check(cond, label):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"   [PASS] {label}")
    else:
        FAILED += 1
        print(f"   [FAIL] {label}")


def test_main_window_wiring():
    print("== Ana pencere bağlantısı (kaynak) ==")
    src = (ROOT / "Math_Course_AI.pyw").read_text(encoding="utf-8")
    check('columns=("st", "info", "sim")' in src, "kurs ağacında ▶ (sim) sütunu var")
    check('if col == "#3":' in src and "open_simulation_for_item(iid)" in src,
          "▶ sütununa tıklamak oynatıcıyı açar")
    check(src.count('"ℹ", "▶")') >= 3, "dosya, klasör ve kurs satırlarına ▶ konur")
    check("simulation_btn" in src and "open_selected_simulation" in src,
          "sol panelde '▶ Simülasyon' düğmesi var")
    check("from simulations.player import open_player" in src, "oynatıcı tembel import edilir")


def _pump(root, sec):
    t = time.time()
    while time.time() - t < sec:
        root.update()
        time.sleep(0.01)


def test_player():
    global SKIPPED
    print("== Oynatıcı penceresi ==")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        SKIPPED += 1
        print(f"   [SKIP] Tk penceresi açılamadı: {e}")
        return
    root.language = "tr"
    from simulations import engine
    from simulations.player import open_player

    d = Path(tempfile.mkdtemp(prefix="mcai-sp-lib-"))
    topic = d / "Algebra Course" / "02 Notes" / "05 Functions and graphing"
    topic.mkdir(parents=True)
    (topic / "02 Slope.txt").write_text(
        "Example 1. Find the equation of the line with slope 3/4 that passes through (2, -1).\n"
        "Example 2. Solve the system 2x + y = 7 and x - y = 2.\n", encoding="utf-8")

    win = open_player(root, str(topic / "02 Slope.txt"), "Algebra Course",
                      ("02 Notes", "05 Functions and graphing", "02 Slope.txt"), lang="tr")
    _pump(root, 0.6)
    check(win.winfo_exists(), "oynatıcı açıldı")
    check(win.sim is not None and win.sim.kind in ("line_slope_point", "line_two_points", "parallel_perp"),
          f"konuya uygun ilk simülasyon seçildi ({win.sim.kind if win.sim else None})")
    check(win.playing, "otomatik oynatma başladı")
    _pump(root, 1.5)
    check(win.frame > 3, f"kareler ilerliyor ({win.frame}/{win.n_frames})")
    win.toggle_play()
    f = win.frame
    _pump(root, 0.4)
    check(not win.playing and win.frame == f, "duraklat çalışır")
    win.step(1)
    check(win.frame == f + 1, "adım ileri")
    win.step(-1)
    check(win.frame == f, "adım geri")
    win.seek(win.n_frames - 1)
    _pump(root, 0.2)
    sol_txt = win.sol_text.get("1.0", "end")
    check(("Cevap" in sol_txt) and win.sim.solution()["answer"] in sol_txt,
          "son karede cevap ve tüm adımlar görünür")
    win.seek(0)
    check(win.frame == 0, "başa sar")
    win.speed_var.set("4x")
    win.play()
    _pump(root, 2.5)
    check(win.frame >= win.n_frames - 1 and not win.playing, "4x hızda sona kadar oynar ve durur")

    old = dict(win.sim.params)
    for _ in range(4):
        win.new_numbers()
        _pump(root, 0.2)
        if win.sim.params != old:
            break
    check(win.sim.params != old, "yeni sayılar üretilir")
    check("{" not in win.q_text.cget("text"), "yeni sorunun metni dolu")

    # edit the code: change P and run
    src = win.code_text.get("1.0", "end-1c")
    good = src.replace("P = {", "P = {'_edited': 1, ", 1)
    win.code_text.delete("1.0", "end")
    win.code_text.insert("1.0", good)
    win.run_code()
    _pump(root, 0.3)
    check(win.sim.custom_code and win.sim.params.get("_edited") == 1, "düzenlenen kod çalıştırılır")
    # policy refusal must NOT replace the running simulation (messagebox is patched)
    import tkinter.messagebox as mb
    shown = []
    orig = mb.showerror
    mb.showerror = lambda *a, **k: shown.append(a)
    try:
        win.code_text.insert("end", "\nimport os\n")
        before = win.sim
        win.run_code()
        check(shown and win.sim is before, "izin politikasına takılan kod çalıştırılmaz")
    finally:
        mb.showerror = orig
    win.revert_code()

    # filters
    vals = list(win.filter_box.cget("values"))
    check(any("Tüm dersler" in v for v in vals), "filtre: tüm dersler")
    win.filter_box.current(len(vals) - 1)
    win._fill_list()
    check(sum(1 for r in win.list_rows if r) == len(engine.all_examples()), "tüm örnekler listelenir")

    # scan
    win.start_scan()
    t = time.time()
    while win._busy and time.time() - t < 30:
        _pump(root, 0.1)
    _pump(root, 0.3)
    check(len(win.scanned_examples) >= 2, f"kaynak taraması örnek üretir ({len(win.scanned_examples)})")
    check(win.sim is not None and win.sim.example.get("source"), "taranan ilk örnek açılır")

    # every embedded example can be opened in the real window (first frame + last frame)
    bad = []
    for ex in engine.all_examples():
        win.open_example(ex, autoplay=False)
        win.seek(win.n_frames - 1)
        root.update()
        if win.sim is None or win.sim.id != ex["id"] or "Error" in win.status.cget("text"):
            bad.append(ex["id"])
    check(not bad, f"tüm gömülü örnekler pencerede açılır ve son kareye gider (hatalı: {bad[:5]})")

    # language switch recreates the window in English
    win2 = open_player(root, None, "Calculus 1 Course", ("02 Notes", "03 Derivatives"), lang="en")
    _pump(root, 0.3)
    check(win2.lang == "en" and win2 is not win, "dil değişince oynatıcı İngilizce açılır")
    win2.close()
    _pump(root, 0.1)
    check(getattr(root, "_simulation_player", None) is None, "kapatma temiz")
    root.destroy()


def main():
    test_main_window_wiring()
    test_player()
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed, {SKIPPED} skipped (ortam)")
    print("=" * 64)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
