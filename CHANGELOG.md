# Changelog

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Per-release feature notes from before the first public release are kept verbatim in
[`docs/release-notes/`](docs/release-notes).

---

## [Unreleased] — first public release candidate

This is the first version of Math Course AI prepared for publication. The program's
features are those of V48; everything below is what changed **for the public
release**. Several entries correct claims that were previously wrong.

### Security

- **AI-generated code execution is now DISABLED by default.** A real OS sandbox could
  not be completed for this release, so the honest default is off
  (`MATH_COURSE_AI_ENABLE_CODE_EXECUTION`). See
  [docs/known-limitations.md](docs/known-limitations.md).
- **New `ai_code_guard.py`**: an explicit allowed-operation policy (module and builtin
  allowlists), a static AST checker that fails closed and runs *before* the approval
  dialog, a fresh isolated workspace per run, a scrubbed child environment that
  inherits no API key or `%APPDATA%` path, and Windows Job Object caps on memory and
  process count. The approval dialog now shows the checker's verdict and states
  plainly that these are resource limits, not permission limits.
- **New `cloud_consent.py`**: routing anything to the cloud provider now requires an
  explicit consent recorded **in the current session**. Consent is never written to
  disk and cannot be pre-set by an environment variable.
- Removed the credential-lookup fallback that read a **different product's** Windows
  Credential Manager entry. Only this program's own entry is read.
- Key masking tightened: the interface now shows the provider, the status and the
  **last four characters** only — no prefix, no length.
- `.mcpack` archives are now capped by member count, declared size, compression ratio
  and a hard per-file byte ceiling during extraction (zip-bomb defence). The existing
  zip-slip defence is unchanged and now has regression tests.
- The two `UPDATE ... SET` builders in `language_dictionary.py` validate column names
  against an explicit allowlist instead of interpolating caller-supplied keys.
- The bare `eval()` in the main entry point now parses to an AST and validates every
  node first, matching the evaluator in `calculator.py`.

### Fixed

- **Right to erasure:** `delete_student` deleted the learner, their attempts and their
  exams but not `exam_items` — every typed exam answer, correctness flag and timestamp
  survived deletion with no path left to reach it. It is now deleted first, and the
  method returns row counts so the erasure can be verified.
- **The default AI provider is now always local.** It previously switched to the cloud
  automatically whenever any API key could be found on the machine — including one
  stored by another application — while the in-app guide told the user the opposite.
- Corrected a false-positive in the presentation test: the bilingual-pair walker did
  not understand the `galeri` slide type and flagged image *filenames* as missing
  translations. The walker is now slide-type aware **and** additionally verifies that
  every screenshot a slide references actually exists in both languages.
- Replaced every hardcoded absolute development path with a resolver based on an
  environment variable falling back to the program folder. The affected modules never
  worked correctly on anyone else's machine.

### Changed — public documentation

- **The absolute offline/privacy wording is gone.** The old summary asserted that the
  product had no cloud path at all and that data could never leave the machine, which
  the optional cloud provider shipped in the same repository contradicted. The README,
  the privacy pages and the slide deck now state: local by default, optional cloud,
  only on explicit per-session consent.
- **No CI badge, and no assertion of a defect-free state.** A badge asserts something
  about a run that has not happened yet.
- Retired unverifiable figures rather than restating them: the startup-speed
  percentage (no benchmark harness exists in this repository) and the
  "N of M topics ready" figure (the reference tree was never in the repository).
- Every remaining number is produced by `tools/measure_facts.py` or by a recorded test
  run, and `test_public_claims.py` fails the build if a document and the code disagree.
- Screenshots regenerated from a **synthetic** demo course library on an empty profile.
  The previous set rendered an absolute development path and a third party's
  commercial course catalogue in every frame.
- The generated deck now uses a **libre** font family (Inter → Source Sans 3 → DejaVu
  Sans) instead of a proprietary system font, and records which one it used.

### Removed

- The automatic publication pipeline: the `post-commit` push hook installer, the
  `git add -A` sync script and the daily scheduled task. On a public repository these
  would have published anything dropped into the folder, unattended and unreviewed.
- The PyInstaller specification and the one-command EXE build. **Binary distribution
  is out of scope for this release**, which resolves the AGPL-3.0 conflict created by
  bundling PyMuPDF into an executable advertised as MIT. See
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) §1.
- PyMuPDF moved from required to **optional** dependencies; every `fitz` import is
  guarded so the program runs without it.
- Internal roadmap and product-strategy documents, a PyInstaller build log containing
  the maintainer's OS path, a design specification for an unimplemented feature, dead
  phase-backup modules, and a developer QA helper hardcoded to a local path.
- All references to an unpublished sibling product — its name, module names, internal
  version decisions and local path.

### Added

- `SECURITY.md`, `PRIVACY.md`, `AI_TRANSPARENCY.md`, `CODE_OF_CONDUCT.md`,
  `THIRD_PARTY_NOTICES.md`, `docs/known-limitations.md`, `.env.example`,
  `.github/dependabot.yml`, SPDX and CycloneDX SBOMs, and this changelog.
- `tools/make_demo_resources.py` — generates the synthetic demo course library.
- `tools/measure_facts.py` — the only sanctioned source of any number in a public
  document.
- `test_ai_code_guard.py` and `test_public_claims.py`.
- CI rewritten: least-privilege permissions, actions pinned to full commit SHAs,
  dependencies installed from pinned `requirements.txt`, and every suite run.

---

## Earlier releases

V42–V48 feature notes are preserved unedited in
[`docs/release-notes/`](docs/release-notes). They describe the program's development
before publication was considered and are kept for provenance, not as current
documentation — where they disagree with this changelog, this changelog wins.
