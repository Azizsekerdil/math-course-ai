# -*- coding: utf-8 -*-
"""
Tests for topic_knowledge.py — the embedded "Nedir ve Ne İçin Kullanılır?"
knowledge base (V45). Headless, no Tk needed.

Run with:
    python test_topic_knowledge.py
"""

import os
import re
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PASSED = 0
FAILED = 0


def check(cond, label):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"   [PASS] {label}")
    else:
        FAILED += 1
        print(f"   [FAIL] {label}")


def test_normalize_and_lookup():
    print("\nNORMALIZE + LOOKUP")
    from topic_knowledge import normalize_topic_key, get_topic_info

    check(normalize_topic_key("L'Hospital's Rule") == normalize_topic_key("l'hospitals rule"),
          "case + apostrophe variants of the same spelling normalise identically")
    check(normalize_topic_key("Hôpital") == normalize_topic_key("Hopital"),
          "accented vs unaccented spelling of the same word normalise identically")
    check(normalize_topic_key("Bayes' Theorem") == normalize_topic_key("Bayes Theorem"),
          "apostrophe-s variants normalise the same")
    check(normalize_topic_key("A=LU factorization") == "a lu factorization",
          "'=' sign is treated as a separator")
    check(normalize_topic_key("  Slope   ") == "slope", "whitespace collapsed/stripped")

    check(get_topic_info("Pythagorean Theorem") is not None, "known topic resolves")
    check(get_topic_info("pythagorean theorem") is not None, "lookup is case-insensitive")
    check(get_topic_info("PYTHAGOREAN THEOREM") is not None, "lookup handles all-caps")
    check(get_topic_info("") is None, "empty string -> None")
    check(get_topic_info(None) is None, "None -> None")
    check(get_topic_info("Completely Made Up Topic Zzyzx 12345") is None,
          "unrelated nonsense topic -> None (no false positive)")

    # near-miss should still resolve via the fuzzy fallback
    close = get_topic_info("Pythagorean Theorm")   # typo
    check(close is not None, "minor typo still resolves via fuzzy match")


def test_entry_shape():
    print("\nENTRY SHAPE + CONTENT QUALITY")
    from topic_knowledge import TOPIC_KNOWLEDGE, coverage_count

    check(coverage_count() >= 600, f"at least 600 embedded topic keys (got {coverage_count()})")
    sample_keys = list(TOPIC_KNOWLEDGE.keys())
    for k in sample_keys:
        entry = TOPIC_KNOWLEDGE[k]
        if not (isinstance(entry, dict) and "course" in entry and "body" in entry):
            check(False, f"entry '{k}' has course+body keys")
            break
    else:
        check(True, "every entry is a dict with 'course' and 'body'")

    missing_structure = [k for k, e in TOPIC_KNOWLEDGE.items()
                         if "Nedir?" not in e["body"] or "Ne İçin Kullanılır?" not in e["body"]]
    check(not missing_structure,
          f"every body has 'Nedir?' + 'Ne İçin Kullanılır?' sections "
          f"(missing: {missing_structure[:5]})")

    too_short = [k for k, e in TOPIC_KNOWLEDGE.items() if len(e["body"]) < 300]
    check(not too_short, f"no suspiciously short (<300 char) entries (found: {too_short[:5]})")

    # spot-check real historical facts are present on a few flagship topics
    pyth = None
    from topic_knowledge import get_topic_info
    pyth = get_topic_info("Pythagorean Theorem")
    check(pyth and "Pisagor" in pyth["body"], "Pythagorean Theorem entry names Pythagoras")
    grass = get_topic_info("Basis")
    check(grass and "Grassmann" in grass["body"], "Basis entry credits Hermann Grassmann")
    bayes = get_topic_info("Bayes' Theorem")
    check(bayes and "1763" in bayes["body"], "Bayes' Theorem entry gives the 1763 publication year")
    newton = get_topic_info("Definition of the derivative")
    check(newton and "Newton" in newton["body"] and "Leibniz" in newton["body"],
          "derivative entry credits both Newton and Leibniz")


def test_real_tree_coverage():
    print("\nCOVERAGE AGAINST THE REAL RESOURCE TREE")
    from topic_knowledge import get_topic_info

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Resources")
    if not os.path.isdir(base):
        print("   [SKIP] Resources folder not present in this environment")
        return
    files = glob.glob(os.path.join(base, "**", "Notes by section", "**", "*.pdf"), recursive=True)
    if not files:
        print("   [SKIP] no 'Notes by section' PDFs found")
        return

    def topic_display_name(path):
        stem = os.path.splitext(os.path.basename(path))[0]
        return re.sub(r"^\s*\d+[\s\.\-_]*", "", stem).strip() or stem

    names = sorted({topic_display_name(f) for f in files})
    found = sum(1 for n in names if get_topic_info(n) is not None)
    pct = found * 100 // len(names)
    check(len(names) > 400, f"real tree has a substantial topic count ({len(names)})")
    check(found >= 650, f"at least 650 real tree topics resolve to embedded content "
                        f"(got {found}/{len(names)}, %{pct}) - round 2 closed the gap "
                        f"from round 1's 274/668 to near-total coverage")


def test_delatex():
    print("\nDELATEX (LaTeX -> readable plain text for the info window)")
    from topic_knowledge import delatex, TOPIC_KNOWLEDGE

    check(delatex(None) == "", "None -> empty string, no crash")
    check(delatex("") == "", "empty string -> empty string")
    check(delatex("no math here") == "no math here", "plain text passes through unchanged")
    check(delatex("$\\sqrt{9} = 3$") == "√(9) = 3", "simple sqrt renders cleanly")
    check("kök(8)" in delatex("$\\sqrt[3]{8}$"), "nth-root renders with the root index")
    check(delatex("$x^2$") == "x²", "simple superscript -> Unicode superscript digit")
    check(delatex("$a_1$") == "a₁", "simple subscript -> Unicode subscript digit")
    check("(-b" in delatex("$\\dfrac{-b \\pm \\sqrt{b^2-4ac}}{2a}$"),
          "nested braces in \\dfrac{...\\sqrt{...}...}{...} resolve correctly (regression: "
          "a naive non-nested regex used to mangle this into 'dfrac-b (b2-4ac)2a')")
    check(delatex("$\\pi r^2$") == "π r²", "Greek letter + superscript combine cleanly")
    check("h→" in delatex("$\\lim_{h\\to 0}$"),
          "complex subscript content (arrows/spaces) falls back to parens, not per-char "
          "garbage like '_h_→_ 0' (regression from the naive first version)")
    check("|v|" in delatex("$\\|v\\|$"), "norm delimiters \\|...\\| render as |...|")
    no_leftovers = delatex("$\\det[[a, b], [c, d]]=ad-bc$")
    check("\\" not in no_leftovers and "{" not in no_leftovers and "}" not in no_leftovers,
          "no leftover backslashes/braces after a realistic mixed expression")

    # sweep every embedded entry: delatex must never raise and must never
    # leave a literal backslash, brace, or $ in the output.
    bad = []
    for key, entry in TOPIC_KNOWLEDGE.items():
        try:
            out = delatex(entry["body"])
        except Exception as exc:
            bad.append(f"{key}: exception {exc}")
            continue
        if "\\" in out or "{" in out or "}" in out or "$" in out:
            bad.append(key)
    check(not bad, f"every embedded entry delatexes cleanly (offenders: {bad[:5]})")


def test_round2_merge():
    print("\nROUND 2 MERGE (Döngü Mühendisliği 2. tur)")
    import topic_knowledge_round2  # noqa: F401 - importable standalone
    from topic_knowledge import get_topic_info

    # spot-check a few round-2-only topics resolve and carry genuine history
    galileo = get_topic_info("Ball thrown up from the ground")
    check(galileo and "Galileo" in galileo["body"], "free-fall entry credits Galileo")
    fermat = get_topic_info("Applied optimization")
    check(fermat and "Fermat" in fermat["body"], "optimization entry credits Fermat's adequality")
    frenet = get_topic_info("Curvature")
    check(frenet and "Frenet" in frenet["body"], "curvature entry credits Frenet-Serret")
    pappus = get_topic_info("Theorem of Pappus")
    check(pappus and "Pappus" in pappus["body"] and "İskenderiye" in pappus["body"],
          "Pappus entry names the ancient Alexandrian mathematician")
    # a purely procedural round-2 topic should have NO fabricated history section
    rounding_like = get_topic_info("Balancing equations")
    check(rounding_like and "Tarih ve Biyografi" not in rounding_like["body"],
          "purely procedural round-2 topic has no fabricated history section")


def main():
    print("=" * 64)
    print("Topic Knowledge — Test Suite")
    print("=" * 64)
    for fn in (test_normalize_and_lookup, test_entry_shape, test_delatex, test_round2_merge,
               test_real_tree_coverage):
        try:
            fn()
        except Exception as exc:
            global FAILED
            FAILED += 1
            import traceback
            traceback.print_exc()
            print(f"   [ERROR] {fn.__name__}: {exc}")
    print("=" * 64)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    print("=" * 64)
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
