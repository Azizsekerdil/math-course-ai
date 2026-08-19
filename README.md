# Math Course AI

A single-user **Windows desktop** workstation for studying a maths course: read your
course PDFs, clip questions out of them into your own question bank, practise with
spaced repetition, and get step-by-step worked solutions — with an **optional** AI
tutor that runs **on your own machine** by default.

> **Status: beta / personal project.** One maintainer, one platform (Windows 10/11),
> one user per installation. There is no server, no account, no multi-user mode and
> no mobile client. It is useful today; it is not a product with a support contract.

---

## What it does — and what it does not

**It does**

- Show your course folder as a tree, track which files you have read, and take you
  back to where you stopped.
- Open PDFs with pen/highlight/text annotation written to a **separate sidecar file**
  — your original PDF is never modified.
- Clip a question out of a PDF page with a rectangle and file it in your own SQLite
  question bank with course, topic, difficulty and the source page.
- Run exams (timed or untimed) over pools such as *untried*, *wrong* or *due for
  review*, and schedule the next review from your own attempt history (Leitner).
- Produce a weekly summary you can print to A4.
- Show worked solutions with `sympy` and plots with `matplotlib`, plus embedded
  interactive simulations and formula cards.
- Provide a bilingual (Turkish/English) dictionary, a scientific calculator, a tablet
  drawing board and five science labs.

**It does not**

- **It is not "fully offline" in an absolute sense.** The default AI provider is a
  **local** model and nothing leaves your machine while you use it — but the program
  also ships an **optional cloud provider** (NVIDIA NIM). It is never selected
  automatically, and it will not send anything until you pick it *and* accept a
  consent dialog **in that session**. See [AI_TRANSPARENCY.md](AI_TRANSPARENCY.md).
- It does not ship, download or redistribute any course material. You supply your own.
- It does not grade you, certify you, or give financial, legal, medical or
  psychological advice. AI answers can be wrong; check them.
- It does not sync, back up to a cloud, or share anything between users.
- It does not run AI-generated code by default — see
  [docs/known-limitations.md](docs/known-limitations.md).

---

## Install

Requires **Windows 10/11**, **Python 3.11**, and a desktop session (it is a Tkinter
GUI; there is no headless mode).

```powershell
git clone https://github.com/<owner>/math-course-ai.git
cd math-course-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python Math_Course_AI.pyw
```

`requirements.txt` pins the versions this release was tested with.
`requirements-optional.txt` holds features that are not needed to start the program
(PDF rendering, OCR, Word/PowerPoint export).

> **PyMuPDF is licensed AGPL-3.0-or-commercial.** It is listed as an *optional*
> dependency and is **not** distributed with this project — you install it yourself
> if you want in-app PDF rendering. This repository ships **source only**; it builds
> no binary and bundles no third-party library. See
> [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for why that matters.

## Demo in two commands

The repository contains a **synthetic** demo course library — generated content only,
no real course material, no personal data:

```powershell
python tools\make_demo_resources.py demo_resources
$env:MATH_COURSE_AI_RESOURCES = "demo_resources"
python Math_Course_AI.pyw
```

Everything you see in the screenshots and in the presentation was captured against
exactly this demo set, on a profile with no learner data. **All demo data is
synthetic.** No real student, name, contact detail, exam result or course file
appears anywhere in this repository.

---

## Configuration and environment variables

No secret is ever required to start the program, and none is stored in the
repository. `.env.example` lists every variable with empty or placeholder values.

| Variable | Purpose | Default |
|---|---|---|
| `MATH_COURSE_AI_RESOURCES` | folder holding your own course PDFs | `<program>\Resources` |
| `MATH_COURSE_AI_EXPORTS` | where exports are written | `<program>\exports` |
| `MATH_COURSE_AI_SETTINGS` | per-installation UI/session state | `<program>\settings` |
| `MATH_COURSE_AI_LEGACY_DATA` | one-time migration source for pre-V43 databases | unset |
| `MATH_COURSE_AI_ENABLE_CODE_EXECUTION` | opt in to running AI-written Python (**off by default — read the risk first**) | unset = off |
| `NVIDIA_API_KEY` | key for the **optional** cloud provider; you supply it after install | unset |

Your study data lives in `%APPDATA%\MathCourseAI\`, never in the repository.

**API keys.** No key is needed for anything except the optional cloud provider. When
no key is configured, that provider reports `NOT_CONFIGURED` and **makes no call**;
the local model and every non-AI feature keep working. The interface shows only the
provider name, its status and the **last four characters** of the key. A key you save
goes into the Windows Credential Manager under this program's own entry — never to a
plaintext file, never to a log, and never to the work record.

---

## AI providers

| | Local — LM Studio | Cloud — NVIDIA NIM |
|---|---|---|
| Default | **yes** | no, never automatic |
| Where it runs | `http://127.0.0.1:1234` on your machine | `https://integrate.api.nvidia.com` |
| Data leaves the machine | no | **yes** — your prompt and the last 12 turns |
| Consent | not needed | **explicit, per session**, via a dialog |
| Provider-side logging | none | NVIDIA logs trial requests and answers |
| Needed to use the program | no | no |

Details, including exactly which fields are transmitted and what is *not*, are in
[AI_TRANSPARENCY.md](AI_TRANSPARENCY.md).

## Privacy and the human-approval boundary

- Study data (learner name, answers, timings, notes) stays in a local SQLite database
  under `%APPDATA%`. It is never uploaded and never sent to any AI provider
  automatically.
- The AI Terminal's **work record** deliberately stores the full text of your requests
  and the model's answers, on your machine. The token ledger stores counters only.
  Both are documented in the app and in [PRIVACY.md](PRIVACY.md).
- Deleting a learner erases every row belonging to them, including exam answers.
- **Nothing the AI writes is executed without you.** Code execution is additionally
  **disabled by default** in this release; see
  [docs/known-limitations.md](docs/known-limitations.md).

## Screenshots and presentation

Screenshots live in [`tanitim_gorseller/`](tanitim_gorseller) and are **real captures
of the running program**, taken by `tanitim_ekran.py` against the synthetic demo
profile — not mock-ups.

The slide deck's content lives in one place, [`tanitim_icerik.py`](tanitim_icerik.py).
The **published** PDF in [`docs/presentation/`](docs/presentation) is rendered from it
by `tanitim_pdf.py` (matplotlib, libre font embedded, no Office required):

```powershell
python tanitim_pdf.py
```

`tanitim_uret.py` builds the editable PPTX/HTML version for authoring; its
PowerPoint-exported PDF is not the published artifact.

## Running the tests

```powershell
$env:MPLBACKEND = "Agg"
python test_visual_math_lab.py
python test_language_dictionary.py
python test_student_tracker.py
python test_topic_knowledge.py
python test_workspace_docking_manager.py
python test_ai_terminal.py
python test_egitim_token.py
python test_ai_code_guard.py
python test_public_claims.py
python smoke_dark_theme.py
python smoke_lazy_panels.py
```

Every suite is a plain script that prints one line per assertion and a `RESULT:`
summary, and exits non-zero on failure. The measured totals for this release are
recorded in [`PUBLIC_RELEASE_MANIFEST.json`](PUBLIC_RELEASE_MANIFEST.json) — this
README does not restate them, so the two can never drift apart.

`test_visual_math_lab.py` skips a group of checks when no course library is present;
the suite prints how many it skipped. That is expected on a clean checkout and on CI.

`python tools/measure_facts.py` prints every countable fact about the codebase. No
number in this repository's public documents may be written by hand — it must come
from there.

> **CI:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs all suites on
> `windows-latest` / Python 3.11. This README carries **no status badge** and asserts
> **no defect-free state**: a badge is a claim about a run that has not happened yet.
> Open the Actions tab for the real state.

## Licence

Source code: **MIT** — see [LICENSE](LICENSE), which is plain unmodified MIT text.

The precise **scope** of that licence, the course material it does *not* cover, and
every third-party dependency licence — including the AGPL-3.0 status of the optional
PyMuPDF — are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) §1 and §4.

## Reporting a vulnerability

See [SECURITY.md](SECURITY.md). Please do not open a public issue for a security
report.

## Known limitations and roadmap

[docs/known-limitations.md](docs/known-limitations.md) lists, honestly, what is
missing, what is only partly done, and what is deliberately off. Read it before
relying on this program for anything that matters.
