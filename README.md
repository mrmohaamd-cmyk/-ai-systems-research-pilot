# Critique-and-Revision Pilot

Small, reproducible harness for testing whether an explicit critique followed by revision improves answer quality enough to justify additional effort.

## Scope

The pilot implements three conditions:

1. `direct`: one answer from the configured model.
2. `critique_revision`: an initial answer, explicit critique, and revision.
3. `additional_effort`: an initial answer followed by an unconstrained second solving attempt.

The third condition is included so any observed benefit can be compared with additional inference effort rather than attributed automatically to critique.

This repository contains the harness and a tiny development dataset. It does not claim treatment effectiveness. No production deployment, persistent adaptation, scaffold modification, or recursive self-improvement is implemented.

## Quick start

Requires Python 3.10+.

```bash
python -m pilot.run --condition all --dataset data/dev.jsonl --backend mock --out runs/smoke.jsonl
python -m pilot.analyze --input runs/smoke.jsonl
python -m unittest discover -s tests -v
```

The mock backend is only for pipeline verification. It intentionally produces predictable outputs and must not be used as evidence about model quality.

## Real model execution

The runner accepts a JSONL backend protocol so a model provider can be connected without changing the experiment logic:

```bash
python -m pilot.run --condition all --dataset data/dev.jsonl --backend command \
  --command 'python my_backend.py' --out runs/real.jsonl
```

The command receives one JSON object per line on stdin and must return one JSON object per line on stdout containing at least `text`; optional `input_tokens`, `output_tokens`, and `latency_ms` are recorded. The request contains `task`, `messages`, and `condition`.

## Status and limitations

- Implemented: task loading, condition assignment, prompt versioning, backend abstraction, failure recording, resource accounting, JSONL run records, deterministic scoring, and summary analysis.
- Smoke-tested: mock execution and unit tests.
- Not evaluated: no real-model results are included.
- Not operationally validated: no deployment or external side effects are supported.
- The development dataset is a placeholder and is not a valid basis for a substantive conclusion.

Before a final study, freeze the task population, protected evaluation set, scoring rubric, practical threshold, resource basis, sample-size rationale, and analysis plan in a versioned experiment specification.
