# Experiment specification v0.2

Status: candidate feasibility protocol, 2026-09-13. This document replaces the v0.1 draft. A machine-readable freeze binds this specification's hash, code, prompts, configuration and data manifest to each run. Only fixture verification is executable with the supplied configuration. No live experimental freeze or final outcomes exist.

## Decision, scope and assumptions

Determine whether a fixed, single-model critique workflow warrants a larger, decision-calibrated evaluation. The eventual architecture question is whether its improvement justifies its costs. The current pilot can establish execution feasibility and estimate task-specific effects; it cannot authorise production adoption.

Provisional question: on English multistep arithmetic word problems, does one explicit critique followed by revision improve exact final numeric accuracy relative to direct answering and additional solving, at comparable call counts and output ceilings?

Arithmetic is a design assumption chosen for an objective, inexpensive scorer. Its relevance to the intended users' work remains unconfirmed. The project has supplied no measured current accuracy, task distribution, cost baseline, service target or acceptable error severity. A benchmark cannot substitute for that diagnosis.

Proposed mechanism: identifying a specific flaw supplies useful information for revision. Competing explanations include additional computation, another solution attempt, changed wording, anchoring on the initial draft, variable input tokens and benchmark contamination. The intervention manipulates an observable prompt sequence; it does not identify internal reasoning mechanisms.

## Conditions and information access

| Stage | Inputs and behaviour | Output ceiling |
|---|---|---|
| A | Question; solve with a short checkable calculation and final number | 512 |
| B1 | Question and A; assess specific errors or state no error found | 256 |
| B2 | Question, A and B1; retain or change any part of the solution as warranted | 512 |
| C1 | Question and A; develop another solution without a prescribed critique report | 256 |
| C2 | Question, A and C1; same finalisation instruction as B2 | 512 |

All stages use the same fixed model/deployment, system prompt and temperature (candidate 0.2). No tools, retrieval, reference answers, correctness feedback, oracle stopping or cross-task conversation history are supplied. B and C share the actual A output. C may still contain incidental criticism; inference is limited to prescribing explicit critique versus additional solving with these prompts.

Tasks and B/C branch order are shuffled with seed 271828. A must precede its dependent stages. Each branch is executed consecutively. This reduces but does not eliminate time/order effects. Record returned model identity, request ID and system fingerprint when provided; unavailable provider revisions limit exact replication. Seed is sent only if the chosen endpoint supports it.

Physical maximum: 300 calls for 60 tasks. Standalone workflows A/B/C require 1/3/3 calls respectively. B/C each have 1,280 total output-token ceiling, including A. Matching is by calls and output ceilings, not measured FLOPs, input tokens, total cost or elapsed time. All actual reported token counts and request durations are retained. The 256-token intermediate ceiling is a provisional constraint to check on development tasks before freezing.

## Data, sampling and separation

Candidate: [GSM8K main](https://huggingface.co/datasets/openai/gsm8k), English arithmetic, train 7,473 / test 1,319. The primary output is a final number. MIT dataset terms apply; it is public and ungated. Obtain JSONL from `openai/grade-school-math` commit `3101c7d5072418e28b9008a6636bde82a006892c`. Hugging Face metadata was inspected at `740312add88f781978c0658806c59bc2815b9866`; that is a separate revision, not the acquisition commit.

`pilot/prepare_data.py` samples 20 development items from train, then 60 evaluation items from test using the seeded generator. Before sampling, exclude test questions exactly matching any train question after trimming whitespace. No further exclusions based on model outcomes. Source row IDs, source hashes, sample IDs, question-only hashes and key hashes are in the manifests. Preparation found zero exact cross-split duplicates. Near duplicates and model training contamination remain unknown.

The runner only accepts `id` and `question`; evaluation answers enter the offline analyzer alone. Prepared keys have restricted file permissions and are ignored by Git. This is application-level separation, not separate operating-system identities. The operator can access keys; the model has no filesystem or tools. Only toy fixture keys are committed. Do not inspect held-out answers to develop prompts. Any tuning using feasibility outcomes makes those tasks development evidence; use fresh held-out tasks for the next claim.

Sixty tasks is a pragmatic **feasibility** sample, not a powered efficacy design. As one calibration, zero task-level pipeline failures among 60 independent tasks gives a one-sided 95% binomial upper bound of approximately 4.87%; it would not demonstrate very high reliability. Model quality intervals may be wide. Twenty development items are for debugging, with no inferential claim. A larger study needs an accepted practical effect, plausible discordance rate, precision/power calculation and application-relevant sampling before its freeze.

## Outcomes and analysis

Primary endpoint: exact final numeric accuracy on every planned task. The strict scorer accepts one terminal `FINAL: <number>` line, finite signed decimals and correctly grouped thousands separators. Numerically equal decimals match. Units, fractions, percentages, ambiguous or repeated final lines and extra text after the final line are invalid. Missing, failed, nonterminal provider responses and invalid outputs score zero. This measures number-and-format task success, not explanation quality or general factual reliability.

Primary paired contrasts: B−A and B−C. Report absolute accuracies with exact 95% binomial intervals; corrections, regressions and paired differences. For each contrast, form exact 98.75% intervals for gain and loss probabilities, then subtract their endpoints. Bonferroni across the four underlying intervals provides conservative simultaneous coverage of at least 95% for both differences, assuming independent task units. Exact two-sided McNemar p-values are descriptive, with a two-comparison Bonferroni adjustment also reported. Do not interpret lack of significance as equivalence. This v0.2 analysis supports one generation per stage; repeated samples or clusters require a amended analysis.

Secondary diagnostics: final number changes, text changes from initially correct answers, format failures, non-OK finals, missing stages, call statuses, known token totals and cost estimates. A text change is not automatically unnecessary or harmful. Refusal-like text without the required answer is a format failure; there is no validated semantic refusal classifier. Error severity and rationale correctness require later reviewed evaluation if relevant to the chosen application.

Timing is the sum of measured request durations for complete successful workflows, with sample counts, mean and exploratory p95. It excludes orchestration overhead and is **not** directly measured standalone end-to-end latency. Physical totals count shared A once; standalone costs count A in each workflow. Record all unpriced attempts. Token-based costs are estimates using supplied rates, not reconciled invoices. Research/development time, human review and maintenance costs are separate and currently unmeasured. No unvalidated model judge is used.

## Limits, deviations and stopping

Preflight requires explicit live execution authority, task acceptance, a fixed endpoint/deployment, dated prices, and an all-inclusive per-call reservation whose full planned total fits the budget. The default 3,600-second scheduler horizon stops starting calls; an in-flight call can extend past it. Socket timeout is 60 seconds for the candidate live template, not a strict total-response deadline. Request data is bounded to 65,536 encoded bytes, response to 1 MiB, and per-stage output caps are checked. Provider enforcement and billing bounds must be verified before live use.

No automatic retries. Persist each start before sending; a lost response is an unknown-charge attempt, never silently retried. Failures skip dependent stages but remain in the denominator. Missing/invalid usage or an exceeded cost bound stops further calls and blocks resumption until investigated. A detected overspend cannot undo that call's charge. Provider-side limits complement local reservation checks. Preserve failed runs; corrective changes require an amendment and new freeze. Do not stop based on interim accuracy.

## Decision rules

For this feasibility pilot: any unresolved leakage, scorer, provenance, billing or ledger defect blocks efficacy interpretation. Successful execution with complete accounting permits assessing the need and sample size for a further study. Wide intervals or missing business thresholds mean **defer judgment**, not equivalence or adoption.

Before a subsequent efficacy freeze, the owner must set minimum useful accuracy gain, maximum regression rate, affordable cost and acceptable latency. Adoption would require effects satisfying those thresholds against relevant alternatives with adequate uncertainty bounds, followed by bounded operational validation. Evidence confined to a subgroup requires fresh validation before routing. A useful effect ruled out under accepted bounds supports retaining A; repairable failures support amendment and retesting. No numeric utility weights or adoption thresholds have been invented. No automatic adaptation or deployment is implemented.
