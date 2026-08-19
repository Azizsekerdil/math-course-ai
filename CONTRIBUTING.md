# Contributing

Thanks for looking. This is a one-maintainer personal project, so please open an
issue before writing anything large — it may already be out of scope.

## Ground rules

1. **Pull requests only.** Nothing goes directly to `main`. CI must be green.
2. **No automation that pushes.** This repository has no post-commit hook, no
   `git add -A` job and no scheduled sync. An earlier version had all three; they
   were removed because on a public repository they would publish whatever landed in
   the folder, unattended and unreviewed. Please do not reintroduce them.
3. **Never commit real data.** No course PDF, no learner name, no screenshot of a
   populated profile, no `.env`, no key. Demo content must come from
   `tools/make_demo_resources.py`.
4. **Never write a number by hand.** If a document states a count, it must come from
   `python tools/measure_facts.py` or from a recorded test run.
   `test_public_claims.py` enforces this and will fail the PR.

## Setting up

```powershell
git clone https://github.com/<owner>/math-course-ai.git
cd math-course-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-optional.txt   # only if you need PDF/OCR/export work
python tools\make_demo_resources.py demo_resources
$env:MATH_COURSE_AI_RESOURCES = "demo_resources"
python Math_Course_AI.pyw
```

Windows 10/11 and Python 3.11. The program is a Tkinter GUI and needs a desktop
session.

## Running the tests

```powershell
$env:MPLBACKEND = "Agg"
foreach ($s in @(
  "test_visual_math_lab.py","test_language_dictionary.py","test_student_tracker.py",
  "test_topic_knowledge.py","test_workspace_docking_manager.py","test_ai_terminal.py",
  "test_egitim_token.py","test_ai_code_guard.py","test_public_claims.py",
  "smoke_dark_theme.py","smoke_lazy_panels.py")) { python $s }
```

Every suite is a plain script: one line per assertion, a `RESULT:` summary, non-zero
exit on failure. There is no pytest and no test runner to learn.

**Do not delete or weaken a test to make a build pass.** If a test is wrong, fix the
test and say in the PR why the new expectation is stricter than the old one.

## Style

- Python 3.11, four spaces, UTF-8 source with the coding header.
- Comments and docstrings explain **why**, not what. Several modules in this
  repository carry a paragraph recording a decision and the bug that caused it —
  keep that habit.
- Turkish and English are both used. UI strings must exist in **both**;
  `test_egitim_token.py` checks the pairs.
- No new third-party dependency without a note in the PR covering its licence, why a
  standard-library approach will not do, and whether it is required or optional.
  Copyleft dependencies must be optional and must be recorded in
  `THIRD_PARTY_NOTICES.md`.

## Security-sensitive areas

Changes to any of these need an explicit justification in the PR and matching tests:

| Area | File | Contract you must not break |
|---|---|---|
| AI code execution | `ai_code_guard.py` | allowlist stays an allowlist; the feature stays default-off until a real OS sandbox exists |
| Cloud routing | `cloud_consent.py`, `nvidia_provider.py` | local stays the default; no request is built without per-session consent; consent is never persisted |
| Credentials | `nvidia_provider.py` | no plaintext on disk; no other application's credential store; UI shows at most the last 4 characters |
| Untrusted archives | `question_packs.py` | zip-slip defence and the size/ratio caps stay |
| SQL | `student_tracker.py`, `language_dictionary.py` | values bound with `?`; identifiers only from an allowlist |
| Erasure | `student_tracker.py` | `delete_student` removes `exam_items` too |

If you find a security problem, follow [SECURITY.md](SECURITY.md) instead of opening
a public issue or PR.

## Presentation and screenshots

Screenshots are generated, never hand-made:

```powershell
python tools\make_demo_resources.py demo_resources
$env:MATH_COURSE_AI_RESOURCES = "demo_resources"   # relative on purpose: an
                                                   # absolute path would bake your
                                                   # user name into every frame
python tanitim_ekran.py     # 16 PNGs from the real running program
python tanitim_uret.py      # PPTX / PDF / HTML from tanitim_icerik.py
```

Use a throwaway profile with no learner data, and check the result before committing.
`tanitim_ekran.py` verifies that each frame really shows the screen its caption
claims, and fails loudly if not — that check exists because a wrong screenshot once
shipped with the right caption.

## Commit messages

One line, imperative, in either language. Say what changed and why. If the change
touches a security contract, say which one.
