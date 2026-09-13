# Frozen pilot specification — draft v1

## Decision

Determine whether an explicit critique-and-revision workflow merits further testing with a real model on a task population relevant to the intended use.

## Default estimand

For matched tasks, estimate the paired difference in final-answer quality between `critique_revision` and `direct`, and between `critique_revision` and `additional_effort`, while reporting calls, tokens, latency, failures, and unnecessary changes.

The current implementation has no valid sample-size basis and is designated **feasibility/smoke only**. The included development dataset must not be used for an effectiveness claim.

## Conditions

| Condition | Procedure | Purpose |
|---|---|---|
| `direct` | One answer using a fixed prompt/configuration | Incumbent performance |
| `critique_revision` | Initial answer → explicit critique → revision | Complete intervention |
| `additional_effort` | Initial task prompt → fresh second solving attempt | Controls for extra inference effort |

The same task is used across conditions. A production study should share initial drafts between revision conditions where possible and randomise or interleave execution when service conditions may bias results.

## Unit and data roles

The task is the experimental unit. Development material is used for smoke testing and prompt/debugging only. A final evaluation set must be protected from answer generation, candidate selection, and scorer modification. If the intended claim concerns transfer, an independently sourced external-validation set is required.

## Primary outcome

The repository currently exposes `lexical_recall` as a transparent development metric. It is not a validated general-purpose quality measure. Before final evaluation, replace or supplement it with a task-valid rubric, deterministic scorer, calibrated blinded human review, or another justified evaluator. Define the practically meaningful improvement, tolerable regression, uncertainty requirement, and resource basis before inspecting final outcomes.

## Interpretation rules

- Improvement, deterioration, negligible change, and inconclusive evidence remain possible.
- A positive result against `direct` alone does not establish that critique is better than additional effort.
- A benchmark effect does not establish operational value.
- No claim about persistence, self-modification, recursive self-improvement, or production suitability follows from this pilot.
