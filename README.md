# Critique-and-revision pilot

A small experiment for deciding whether explicit critique deserves further testing. Version 0.2 uses shared drafts, a comparable additional-effort control, protected scoring inputs, and an auditable execution ledger.

**Status:** implemented and locally verified with scripted fixtures. Public benchmark samples have been prepared. No live model evaluation or operational validation has occurred. The proposed arithmetic population and model are candidates, not accepted project requirements. Nothing here establishes recursive self-improvement.

## The comparison

| Condition | Procedure | Output-token ceilings, including the shared draft |
|---|---|---|
| A | Produce one answer | 512 |
| B | Use A → explicit critique → finalise | 512 + 256 + 512 |
| C | Use A → additional solution → finalise | 512 + 256 + 512 |

B and C receive identical initial answers and use the same finalisation prompt. Each task needs five physical calls; each revision workflow would need three standalone calls. Equal call counts and output ceilings do **not** guarantee equal actual tokens, cost or time.

Read the [experiment specification](docs/experiment_spec.md), [evidence synthesis](docs/evidence.md), and [decision and capability record](docs/decision_record.md).

## Verify locally

Use Python 3.12 on Linux or macOS; verification used Python 3.12.14 on Linux. There are no third-party runtime dependencies and no installation step. POSIX file locking means native Windows is currently unsupported. Run from this repository's root:

```bash
python -m unittest discover -s tests -v
python -m pilot freeze --config config/fixture.json --tasks data/fixtures/tasks.jsonl --manifest data/fixtures/manifest.json --out freezes/local-fixture.json
python -m pilot run --freeze freezes/local-fixture.json --tasks data/fixtures/tasks.jsonl --out runs/local-fixture
python -m pilot analyze --run runs/local-fixture --key data/fixtures/key.jsonl
```

These commands make no model requests. Fixtures intentionally exercise corrections, regressions, an invalid answer format and a refusal-like response. Their token counts are synthetic; their scores are software checks. Repeating `run` resumes the same run without repeating requests. A freeze refuses overwrite; use a new name after a documented change.

`events.jsonl` records attempted and skipped stages; `run.json` embeds the frozen configuration; `analysis.json` preserves the full task denominator, paired results and resource limitations. A clean source commit is recorded when available; a dirty checkout is explicitly labelled and its runtime code is hashed.

## Acquire the candidate dataset

```bash
python -m pilot.prepare_data --download --revision 3101c7d5072418e28b9008a6636bde82a006892c --source-dir data/downloads --out data/prepared
```

This retrieves pinned public GSM8K JSONL files from their original repository. It prepares 20 development tasks and 60 separate feasibility tasks with seed 271828. It checks exact cross-split duplicates and separates `{id, question}` inputs from evaluator keys. Existing output directories are never overwritten. The [committed manifests](data/manifests) contain source and content hashes, not answer keys. Acquisition timestamps will differ on regeneration; content hashes should match. `data/dev.jsonl` is the preserved v0.1 placeholder and is not used by v0.2.

## Live execution requirements

`config/live.template.json` intentionally fails preflight until the task population, provider endpoint, model/deployment, operator, execution authority and budget are supplied. Copy it to ignored `config/live.json`. Credentials are read from `PILOT_API_KEY` in the execution environment; do not put them in configuration, prompts or commits.

The HTTP adapter accepts a nonstreaming chat-completion response with text, finish reason and input/output usage. Its contract is unit-tested with a simulated response; authenticated inference remains unverified. Use a fixed provider/deployment, check the dated price schedule and all-inclusive per-call reservation, and establish provider-side spending limits. See the [provider protocol](https://huggingface.co/docs/inference-providers/tasks/chat-completion). Hugging Face discovery access alone does not establish this access.

After live access is established, first smoke-test the four public fixtures using a separate HTTP configuration and run name. That freeze remains labelled verification-only. Resolve failures on development tasks; then commit prompts/configuration and freeze the 60-task feasibility run before examining its outcomes:

```bash
python -m pilot freeze --config config/live.json --tasks data/prepared/eval_tasks.jsonl --manifest data/prepared/eval_manifest.json --out freezes/live-feasibility-v1.json
python -m pilot run --freeze freezes/live-feasibility-v1.json --tasks data/prepared/eval_tasks.jsonl --out runs/live-feasibility-v1
python -m pilot analyze --run runs/live-feasibility-v1 --key data/prepared/private/eval_key.jsonl
```

The last commands require completed live configuration; they have **not** been executed. Keep live outputs private until reviewed for publication. Record amendments and a fresh run whenever methods change. The repository's MIT licence does not replace third-party data/model licences.
