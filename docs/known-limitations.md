# Known limitations

This file exists so that nothing in the README has to be read optimistically.
Everything below is a real limitation of the released code, not a roadmap wish.

---

## 1. Running AI-generated code is DISABLED by default

The AI Terminal can ask a model to write a Python program. Actually running that
program is **off in this release** and must be turned on deliberately:

```powershell
$env:MATH_COURSE_AI_ENABLE_CODE_EXECUTION = "1"
```

### Why it is off

A genuine operating-system sandbox (AppContainer, a restricted token, or a
container) could not be completed for this release. What exists instead is:

| Layer | What it actually does | What it does **not** do |
|---|---|---|
| Human approval dialog | Shows the complete code, refuses to run until you click Approve | Cannot help if you approve without reading |
| Static policy check (`ai_code_guard.analyze`) | Refuses anything outside an explicit module/builtin allowlist; reports the offending line and capability | Is **bypassable**. A static checker is a filter, not a boundary |
| Isolated workspace | Fresh empty directory per run; runs never see each other's files | Does not stop the code reaching files elsewhere |
| Scrubbed environment | No API key, token or `%APPDATA%` path is inherited by the child | Does not stop the code reading those files from disk |
| Windows Job Object | Caps memory (1 GiB), forbids spawning further processes, kills the tree | Caps **resources**, not **permissions** |
| Timeout | 180 s hard limit | — |

None of that is a sandbox — the static check is **not a sandbox**, and neither is the
Job Object. **Read the table as a whole: approved code still runs with your user
account's full rights.** It can read, write and delete any file you can, and it can reach the
network. The layers above make an accident less likely and a hostile program more
obvious; they do not make it impossible.

This matters more than it looks, because untrusted text reaches the model by design
(PDF text, OCR output, third-party `.mcpack` question packs). A crafted document
could try to steer the model into writing something hostile. That is why the static
check runs *before* the approval dialog opens and why the feature ships off.

### Roadmap

Ship this feature on only when it runs inside a real OS-enforced sandbox with no
network by default.

---

## 2. The cloud provider is optional but real

The default is a local model and the program is fully usable with no network at all.
But an optional NVIDIA NIM provider exists, and if you choose it in a session, your
prompt and the last 12 conversation turns are sent to NVIDIA, which logs trial
requests and answers.

Not implemented: masking or pseudonymisation of what you type, a stated data region,
a stated retention period, a training opt-out, or any spend cap. If any of those
matter to you, stay on the local model. See [AI_TRANSPARENCY.md](../AI_TRANSPARENCY.md).

---

## 3. Platform and scale

- **Windows only.** The credential store uses `advapi32`, the Job Object uses
  `kernel32`, and the presentation pipeline drives PowerPoint through COM. Nothing
  has been tested on macOS or Linux.
- **Single user, single machine.** No accounts, no roles, no login, no server, no
  network listener. If two people share one Windows account they share one database.
- **No encryption at rest.** The SQLite databases under `%APPDATA%\MathCourseAI` are
  plain files protected only by the operating system's file permissions.

---

## 4. Data protection

- Deleting a learner now erases their exams, exam answers and attempts as well as the
  learner row. Regression test: `test_ai_code_guard.py :: test_right_to_erasure`.
- There is **no export-my-data button** and no automatic retention limit on the study
  database. The AI Terminal work record does cap itself and drops the oldest entries.
- The work record stores the **full text** of your prompts and the model's answers.
  That is its purpose, it is stated in the app, and it stays on your machine — but if
  you paste something sensitive into the terminal, it is written to disk.

---

## 5. Third-party dependencies

- **PyMuPDF is AGPL-3.0-or-commercial** and is therefore an *optional* dependency
  that this project does not distribute. Without it, in-app PDF rendering is
  unavailable; everything else works. See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
- `pytesseract` needs a separate Tesseract binary that this project does not ship.
- `manim` is imported by one optional animation path and is not in `requirements.txt`;
  that path is unavailable unless you install it yourself.
- No binary is built or published from this repository.

---

## 6. Content and correctness

- The embedded topic knowledge bank is **hand written** and covers a fixed set of
  entries (`python tools/measure_facts.py` prints the exact number). It is not a
  curriculum and it is not authoritative.
- `sympy` equivalence checking suggests MATCH / EQUIVALENT / DIFFERENT — **you** make
  the final call. Automatic grading is only used for multiple-choice items.
- Several performance figures that appeared in earlier marketing material (startup
  time improvements, "N of M topics ready") were never reproducible from this
  repository and have been **removed** rather than restated.

---

## 7. Testing and CI

- The suites are plain scripts, not `pytest`. There is no coverage measurement.
- `test_visual_math_lab.py` skips a group of checks when no course library is present.
  It prints how many; a clean checkout and CI will always skip them.
- There is no status badge in the README on purpose. A badge asserts something about
  a run that may not have happened yet.
- Dependencies in CI are installed from the pinned `requirements.txt`, but there is no
  hash-pinned lockfile.

---

## 8. Presentation assets

The slide deck is generated, not hand-edited, and its content lives in exactly one
place (`tanitim_icerik.py`).

- The **published** PDF in `docs/presentation/` is rendered by `tanitim_pdf.py` using
  matplotlib, so it needs no Microsoft Office and embeds only a libre font. Its
  layout is deliberately plain: it is a faithful, redistributable rendering, not a
  designer's deck.
- The **editable** PPTX/HTML deck (`tanitim_uret.py`) is for authoring. Exporting a
  PDF from it goes through PowerPoint COM and is therefore Windows-and-Office-only,
  and it embeds whatever font that machine has. Do not publish that export.
- Screenshots are captured from the real running program by `tanitim_ekran.py`, which
  needs a desktop session. They cannot be regenerated on CI.
