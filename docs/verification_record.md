# Verification record — v0.2

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

The software is ready for endpoint smoke testing once a model route, task acceptance and execution budget are established. This evidence supports retaining the minimal harness. It does not support adopting critique, selecting an operational model or adding production architecture. See [the decision record](decision_record.md) for requirements and unresolved user decisions.
