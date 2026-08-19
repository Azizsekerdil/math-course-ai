# Security policy

## Reporting a vulnerability

**Please do not open a public GitHub issue for a security problem.**

Use GitHub's **private vulnerability reporting** on this repository
(*Security → Report a vulnerability*). If that is unavailable, open a public issue
that says only *"security report, please open a private channel"* — with no technical
detail — and wait to be contacted.

Please include: what you did, what happened, what you expected, the affected file and
line if you know it, and your platform and Python version. A proof of concept is
welcome; please do not test against anyone else's machine or data.

This is a personal project with one maintainer. Expect a first response within about
a week, and please allow 90 days before public disclosure.

## Scope

**In scope** — anything in this repository:

- the static policy checker and the guarded runner (`ai_code_guard.py`);
- the cloud consent gate (`cloud_consent.py`) and the provider (`nvidia_provider.py`);
- credential handling and masking;
- untrusted input handling: `.mcpack` question packs, PDFs, OCR output;
- SQL construction in `student_tracker.py` and `language_dictionary.py`;
- the expression evaluators in `calculator.py` and `Math_Course_AI.pyw`.

**Out of scope**

- Anything requiring an attacker who already has your Windows account. This is a
  single-user desktop program with no privilege boundary against its own user.
- Vulnerabilities in LM Studio, NVIDIA NIM, or any third-party dependency — report
  those upstream (we will happily bump a pin).
- "AI gave a wrong answer." That is a known property of language models and is
  documented in [AI_TRANSPARENCY.md](AI_TRANSPARENCY.md).

## Threat model in one paragraph

There is no server, no listening socket, no authentication and no multi-tenancy —
those categories do not exist here, so they are not "secure", they are **absent**.
The realistic threats are: (1) a hostile or malformed input file (`.mcpack`, PDF)
reaching a parser or the model's context, (2) model-written code being run on the
host, and (3) an API key leaking through the interface, a log, a screenshot or the
presentation. The controls below map onto those three.

## Controls in this release

| Threat | Control | Test |
|---|---|---|
| Model-written code runs on the host | Feature **disabled by default**; human approval dialog; static allowlist policy; isolated per-run workspace; scrubbed environment; Windows Job Object memory/process caps; 180 s timeout | `test_ai_code_guard.py` |
| Data silently leaving the machine | Local provider is the hardcoded default; cloud refuses to build a request without explicit per-session consent | `test_ai_code_guard.py`, `test_ai_terminal.py` |
| API key exposure | Windows Credential Manager only; never plaintext, never logged; UI shows provider, status and last 4 characters only; no other app's credential store is read; child processes inherit no key | `test_ai_terminal.py` |
| Hostile `.mcpack` | Zip-slip defence (no absolute paths, no `..`, no subdirectories, extension allowlist); member-count, declared-size and compression-ratio caps; hard byte ceiling during extraction | `test_ai_code_guard.py` |
| SQL identifier injection | Values always bound with `?`; the two `**fields` UPDATE builders now validate column names against an explicit allowlist | `test_ai_code_guard.py` |
| Unsafe evaluation | Both expression evaluators parse to an AST and validate every node before `eval`; an emptied `__builtins__` is not relied on as a boundary | `test_visual_math_lab.py`, `test_ai_code_guard.py` |
| Right-to-erasure gap | `delete_student` removes `exam_items` as well | `test_ai_code_guard.py` |

## Bootstrap / default credentials

**There are none, and there is no place to put any.**

This program has no login, no admin role, no user table, no session, no token and no
network listener. It runs as the signed-in Windows user and stores its data under that
user's `%APPDATA%`. A bootstrap administrator account (for example `admin`/`admin`
behind a forced password change) would add an authentication surface where none
exists, so it has deliberately **not** been added.

That claim is enforced mechanically, not just asserted:
`test_ai_code_guard.py :: test_no_default_credentials` scans every shipped source file
for hardcoded default passwords and for any web-server, socket-listener or
network-login construct, and asserts the database schema contains no `users`,
`sessions`, `roles`, `accounts` or `permissions` table. If anyone ever adds one, that
test fails and this section must be rewritten before release.

## What is deliberately *not* claimed

- The static code checker is **not** a sandbox and can be bypassed.
- The Job Object caps **resources**, not permissions.
- Databases are **not** encrypted at rest.
- No formal audit, penetration test or certification has been performed.

## Supported versions

Only the latest commit on the default branch. There are no backported fixes.
