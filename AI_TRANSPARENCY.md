# AI transparency

What the AI features in Math Course AI actually do, what they send, and where the
human stays in control.

---

## 1. AI is optional

The program is fully usable with the AI turned off entirely. PDF reading and
annotation, the question bank, exams, spaced repetition, the weekly report, the
labs, the calculator, the drawing board and the dictionary's stored content all work
with no model, no key and no network.

## 2. Two providers, and the default is local

| | **Local — LM Studio** | **Cloud — NVIDIA NIM** |
|---|---|---|
| Selected by default | **Yes, always** | No — never automatically |
| Endpoint | `http://127.0.0.1:1234` (your machine) | `https://integrate.api.nvidia.com/v1/chat/completions` |
| Data leaves your machine | **No** | **Yes** |
| Requires a key | No | Yes, one you supply after install |
| Requires consent | No | **Yes — explicit, every session** |
| Logged by the provider | No | Yes (NVIDIA API Trial terms) |

**Having a key on the machine is not consent.** Earlier versions of this program
selected the cloud provider automatically whenever a key could be found. That was
wrong and it has been fixed: the default provider is now hardcoded to local, and the
cloud provider refuses to build a request until `cloud_consent.grant_for_session()`
has been called — which only happens when a human reads a disclosure dialog and
accepts it. Switching back to the local model revokes consent immediately, and
consent is never written to disk, so closing the program always resets it.

Regression tests: `test_ai_code_guard.py :: test_cloud_consent`,
`test_default_provider_is_local`, and `test_ai_terminal.py :: test_no_key_no_network`.

## 3. What is sent to the cloud provider, exactly

When — and only when — you have chosen the cloud provider in the current session:

**Sent**

- the system prompt (a fixed instruction, visible in `ai_terminal.py`),
- the last **12 turns** of the conversation in that terminal window, verbatim,
- the model name, `stream` flag and a `max_tokens` value.

**Not sent**

- learner names, the student tracker database, attempt history, exam results, notes;
- the AI Terminal work record;
- the token ledger;
- your course files, unless you paste text from one yourself;
- any file path, machine name or environment variable.

Nothing is masked or pseudonymised before sending. **Whatever you type is what goes.**
Do not type personal, health, financial or otherwise sensitive information.

## 4. What is *not* guaranteed on the cloud path

Stated plainly because these are real gaps, not oversights we hope you miss:

- **Retention** — NVIDIA logs trial requests and responses. This project does not
  know or control for how long.
- **Region** — the data location is not stated anywhere and is not controlled here.
- **Training opt-out** — none is negotiated or implemented.
- **Cost cap** — none. There is no budget or request quota in this program.
- **DPA** — this project has no data-processing agreement with NVIDIA.

If any of that is unacceptable in your context, use the local model. It is the
default for exactly this reason.

## 5. API keys

- No key is required to install or start the program.
- With no key configured, the cloud provider reports `NOT_CONFIGURED` and makes **no
  call at all**.
- A key you enter is stored in the **Windows Credential Manager** under this program's
  own entry. It is never written to a plaintext file, a log, the token ledger, the
  work record, a backup or a screenshot.
- The interface shows only the provider name, the status and the **last four
  characters**. Neither the prefix nor the length is displayed.
- This program does **not** read any other application's credential store. (A previous
  version fell back to a sibling product's entry; that path has been removed.)
- No key value appears anywhere in this repository. `.env.example` contains
  placeholders only.

## 6. Human control

- **Nothing the AI writes is executed automatically.** The ▶ button opens an approval
  window showing the complete code.
- On top of the human gate there is a static policy check with an explicit
  allowed-operation list, an isolated per-run workspace, a scrubbed child environment
  and Windows Job Object resource caps.
- **The feature is disabled by default in this release** because none of those layers
  is an operating-system security boundary. See
  [docs/known-limitations.md](docs/known-limitations.md).
- Answer checking is advisory. `sympy` proposes MATCH / EQUIVALENT / DIFFERENT; the
  human decides. Only multiple-choice items are graded automatically.
- The "This Week" study suggestions are **rule-based** and make no AI call at all;
  the dashboard states the reason for every suggestion.

## 7. Limits of what AI answers mean

Model output in this program is a study aid. It is **not**:

- a grade, a qualification or an assessment of ability;
- financial, legal, medical, psychological or safety advice;
- a source you should trust without checking.

Models produce confident wrong answers. The program shows working steps precisely so
you can catch them.

## 8. Prompt injection

Untrusted text reaches the model by design: PDF text, OCR output and third-party
`.mcpack` question packs all flow into the interface and can flow into a prompt. A
crafted file could try to steer the model. The mitigations are the static code check
(which runs *before* the approval dialog), the human approval gate, and the
default-off execution switch. Treat model output about a document you did not write
with the same suspicion you would give the document.
