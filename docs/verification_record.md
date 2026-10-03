# Verification record — v0.2

## Current offline verification — 2026-10-03

Verified the exact PR head `9f241074a23d0b5c4828db0df1ca9f5788aac752` in an isolated Linux checkout, using Python 3.12.14. No repository `AGENTS.md` or `.agents/skills` instructions were present. No runtime packages or operating-system features were installed.

- **Clean baseline: 21 tests passed.** The existing 20-test historical record below predates the feasibility-screen test. The clean-head fixture freeze records the exact source commit. [Baseline results](../runs/verification-2026-10-03-linux/baseline/summary.json) and [test output](../runs/verification-2026-10-03-linux/baseline/tests.txt)
- **Patched suite: 24 tests passed.** Three added test methods verify exact threshold equality, each of six threshold failures independently, zero B successes, and eight incomplete/unpriced cases. [Full test output](../runs/verification-2026-10-03-linux/patched/tests.txt) and [individual boundary subcases](../runs/verification-2026-10-03-linux/gate-cases.json)
- **Gate decisions were executed:** exact equality yields `PASS_FURTHER_STUDY`; each threshold violation and zero B successes yields `FAIL_FEASIBILITY_SCREEN`; each incomplete/unpriced condition yields `INCONCLUSIVE`. The existing fixture test confirms `NOT_APPLICABLE`. A passing screen never authorizes adoption.
- **Fresh CLI fixture: 20 scripted stage calls, 40 ledger events, zero missing stages.** A, B and C each intentionally score 2/4. The decision remains `NO_EFFICACY_INFERENCE_FIXTURE`. [Patched run summary](../runs/verification-2026-10-03-linux/patched/summary.json)
- **Resume: no duplicate requests.** Repeating `run` left the ledger byte-for-byte unchanged. SHA-256 before and after: `1b736b7b6f769061c3faa79298ddaf1d5a1f8232cf3c954fcc6991857994956f`. An independent adapter-failure sentinel also confirms that a completed resume invokes no adapter.
- **Nine independent integrity probes passed on both versions:** freeze overwrite refusal; modified freeze, task bytes, answer-key bytes and runtime hash rejection; duplicate-ledger rejection on run and analysis; exclusive POSIX lock; adapter-free, unchanged resume. [Patched integrity results](../runs/verification-2026-10-03-linux/patched/integrity.json)
- **Offline controls:** validation processes used a Python audit hook rejecting network-connect, resolution and datagram-send events. CLI runs unset `PILOT_API_KEY`; the HTTP-contract unit test uses a mocked transport and dummy credential. No live model requests, inference expenditure or real credentials were involved. [Environment and scope](../runs/verification-2026-10-03-linux/environment.json)

Runtime `pilot/core.py` is unchanged from the PR head, SHA-256 `b32be121601ca4c69392de54b9fb4700eee45ea9569ef4150bae72f97b436aa7`. The patched run truthfully records a dirty worktree and the base commit, with no clean source-commit claim. Its freeze identifier is `908dd0b85d8ea9f85ac8b86e2b3bb9317613d056c3d4aba6bc818056fb0b569b`. Raw [freeze](../runs/verification-2026-10-03-linux/patched/freeze.json), [ledger](../runs/verification-2026-10-03-linux/patched/run/events.jsonl), [metadata](../runs/verification-2026-10-03-linux/patched/run/run.json), and [analysis](../runs/verification-2026-10-03-linux/patched/run/analysis.json) are retained.

The transferred test/static-evidence patch was SHA-256 `836b98b9cb06d87dac3abe001c8809b948a933ef15d736bc4f99e8c8b7027b88`. Its documentation header had a dash-character context mismatch; the current report replaces that hunk. The test file was applied unchanged (SHA-256 `5add7c8d6f0bd4a6b94f51ea5655b66b438fe43ef656874b63c9aa0209b789bf`). No commit, push, merge or deployment was performed.

### Reproduce current checks

From the repository root on Python 3.12/Linux or macOS:

```bash
export PYTHONPATH="$PWD/runs/verification-2026-10-03-linux:$PWD"
unset PILOT_API_KEY
python -m unittest discover -s tests -v
python runs/verification-2026-10-03-linux/check_gate_cases.py
python runs/verification-2026-10-03-linux/check_integrity.py
```

Then follow the README freeze/run/analyze commands using a new output name. The `sitecustomize.py` in this verification directory provides the offline network audit guard. Fixture token counts are synthetic; local fixture timings are not model latency. The probe scripts are additional checks, not extra unittest methods included in the 24-test count.

### Native Windows review limitation

An earlier isolated native-Windows checkout of the same head used Python 3.12.14. Importing `pilot.core` failed with `ModuleNotFoundError: No module named 'fcntl'`; zero application tests executed there. WSL was not installed and no supported Linux runtime was identified on that computer. No runtime installation, feature enabling, lock shim or security change was attempted. The Linux execution above resolves the offline verification blocker without claiming native-Windows support.

The Windows review parsed/compiled eight Python files without executing them and parsed four JSON files; its historical [static result](../runs/verification-2026-10-03-windows/static-checks.json) and [check script](../runs/verification-2026-10-03-windows/static_check.py) are preserved. Windows hashes describe its checkout bytes and may differ from Linux because of line endings. Do not rerun that script in place if preserving the historical Windows artifact.

## Historical Linux verification — 2026-09-13


Executed on 2026-09-13 with Python 3.12.14 on Linux. Source commit: `23be2e9e0a644eb1f3bbb9cb4dde41f535f4272e`. The checkout was clean when frozen.

- Automated verification: **20 tests passed**; [full test output](../runs/verification-v0.2/tests.txt).
- CLI fixture run: **20 scripted stage calls, 40 ledger events, zero missing stage records**. No network inference requests or inference expenditure.
- Resume check: repeating the run left the ledger byte-for-byte unchanged.
- Scorer checks: each condition intentionally has two correct answers among four fixtures. B versus A contains one repair and one regression; B versus C contains two of each. These values were scripted in advance to exercise accounting, not observed model quality.
- Fixture tokens are synthetic and request durations measure local fixture execution. They cannot estimate live model cost, latency or accuracy.

Freeze: [`verification-v0.2.json`](../freezes/verification-v0.2.json), identifier `e70760a953fa15907ae749305fa96fbb32f4a669cc398f31db0fbccfe3be1483`. Raw [ledger](../runs/verification-v0.2/events.jsonl), [run metadata](../runs/verification-v0.2/run.json), and [analysis](../runs/verification-v0.2/analysis.json) are retained. The analysis decision is `NO_EFFICACY_INFERENCE_FIXTURE`.

Tests address numeric and format scoring, paired task assignment, shared drafts, exclusion of evaluator fields, fixed denominators, missing usage, budget incidents, output/request limits, interruption recovery, duplicate prevention, immutable inputs, exact interval boundaries, and the simulated HTTP response contract. Data preparation also has a split/provenance test.

The candidate public dataset was downloaded and deterministically partitioned separately; see [data manifests](../data/manifests). No feasibility task was submitted to a model. Authenticated live HTTP compatibility, provider billing limits, treatment effectiveness and operational validity remain untested.

## Reproduce the software check

Use the README fixture commands with a new freeze/run name. To reproduce this exact runtime and scorer, check out the source commit above. Timestamps, run identifiers, local timing and freeze identifiers will differ on a new run; scripted outcomes and stage assignments should agree. The recorded freeze embeds prompts/configuration and hashes of runtime code, preparation code, specification and data. Hosted inference, if later used, may not be bitwise reproducible even with identical settings.

## Decision

Current offline software, gate-boundary and integrity checks pass on supported Linux. This supports retaining the minimal harness. Live endpoint smoke testing still requires a confirmed model route, task acceptance, execution authority and budget; authenticated compatibility, billing, efficacy and operational validity remain untested. This evidence does not support adopting critique, selecting an operational model or adding production architecture. See [the decision record](decision_record.md) for requirements and unresolved user decisions.
