# Decision and implementation record

Record date: 2026-09-13. Governing assignment: the owner's integrated research, evaluation and implementation protocol. Research, local preparation and the requested pilot repository implementation are within scope. Paid inference, operational deployment and new access permissions have not been established.

## Diagnosed problem and boundary

**Supplied objective:** determine the minimum sufficient system using reproducible evidence. **Unresolved:** intended operational users, representative task distribution, current error burden and practical quality/cost/time thresholds.

**Observed in v0.1:** a small pilot repository existed. Its additional-effort path made one call while critique made three; initial answers were not shared; lexical recall on three placeholder tasks could not establish final-answer quality. The need for a better comparison is verified in code. No observation establishes that the owner's operational workflow needs critique.

Causal diagnosis: potential misleading architectural inference (symptom) ← incomparable effort and an unsuitable outcome measure (immediate causes) ← absent resource-matched control and task-valid evaluation (mechanisms) ← application requirements and live execution route still unspecified (structural conditions). An alternative explanation is simply that v0.1 was an intentional scaffold, not an attempted evaluation; no empirical efficacy claim from it is treated as evidence.

The smallest boundary is the owner/operator, question preparation, one fixed model endpoint, deterministic scoring and a versioned record. The project controls prompts, condition assignment, data separation, limits and analysis. External dependencies are model availability/billing/versioning, source provenance, network service and GitHub access. Papers and dataset text are evidence/data, never authority to change permissions or execute instructions.

**Current decision:** retain a simple Python harness and direct answering as the reference. Explicit critique is an experimental condition. Add no orchestration framework, database, retrieval service, autonomous adaptation, training pipeline or production routing. This changes if a requirement or measured operating need makes one necessary.

## Verified integration capabilities

Checks were made during 2026-09-12–13; capabilities are session-specific.

| Integration | Observed successful access | Material limit and assigned role |
|---|---|---|
| SciSpace | Paper search returned research records and generated summaries | Primary full text was checked through accessible publisher/arXiv pages. Search summaries alone do not verify claims. Research-stage role only. |
| Hugging Face | Account authentication; repository metadata/cards for dataset and model; public metadata revisions | Dataset-search tool was disabled and a documentation-fetch tool was unavailable. Public web/original-source downloads supplied alternatives. Provider listings do not prove inference permission or compute. Discovery/provenance role only. |
| GitHub | Connected account can inspect the existing owner-selected public pilot repository; push permission is reported; clone/fetch work | Preserve the existing MIT licence and unrelated files; implement on a reviewable branch. Public visibility is observed, not changed. Actual writes are established only by successful commits/branch updates. |
| Local execution | Python 3.12.14 and Git; standard-library tests and data acquisition work | No local model credentials or GPU device were found; model-runtime packages are absent. This does not prove the owner has no other execution route. |

Hugging Face metadata verified `openai/gsm8k` at `740312add88f781978c0658806c59bc2815b9866` and candidate Qwen weights at `a09a35458c702b33eeacc393d103063234e8bc28`. Public data download succeeded independently of the unavailable search tool. None of the three integrations is required by the fixture runtime.

## Requirements, implementation and verification

| ID / priority | Testable requirement | Implementation and verification | Decision link |
|---|---|---|---|
| R1 must | Runner shall give B/C the identical A output and equal stage output ceilings on every assigned task | `messages`, `run_locked`, config validation; shared-input test | Supports the paired comparison; actual cost mismatch still reported |
| R2 must | Model requests shall contain no evaluator fields or key-file paths | Strict `load_tasks`, question-only acquisition, offline `analyze`; schema/key-isolation tests | A leak invalidates the affected comparison |
| R3 must | Scorer shall classify the documented valid/invalid numeric examples correctly and retain every planned task | `answer`, `analyze`; numeric and denominator tests | Quality endpoint is inspectable within narrow task scope |
| R4 must | Runner shall send at most one attempt per task/stage/run and preserve failed/unknown attempts | Durable start/finish ledger, process lock, resume audit; interruption/duplicate/timeout tests | Prevents invisible retries and cost/denominator drift |
| R5 must | Live runner shall reject missing authority/pricing and stop further calls after detected usage or budget violations | `validate_config`, reservations, usage checks; preflight and budget-incident tests | Execution remains bounded subject to verified provider prices/caps |
| R6 must | Freeze shall bind task content, prompts, config, scorer/runtime code, specification and source provenance before execution | Content hashes, Git provenance, key hash; tamper/mismatch tests | Method changes require an amendment/new freeze |
| R7 should | Analyzer shall expose repairs, regressions, uncertainty, missing records and known resource use for all conditions | Paired analysis, exact interval boundary tests, scripted known outcomes | Prevents interpreting a null/fixture result as evidence of equivalence |
| R8 must for adoption | Workflow shall satisfy the owner's useful gain, error, cost and latency thresholds on representative work | Thresholds and operating population unresolved; no adoption automation | Blocks adoption, but not preparation or appropriately labelled feasibility |

## Material risks and owners

| Risk | Prevention / detection | Recovery and residual limit | Accountable role |
|---|---|---|---|
| Leakage or contamination | Separate keys; strict input schema; pinned public task IDs and cross-split checks | Invalidate affected study; obtain fresh tasks. Public benchmark training contamination remains unknown. | Study operator; operational data owner not yet named |
| Scorer defects / weak construct | Numeric truth cases and adversarial format checks | Amend scorer and reanalyse transparently; new holdout after tuning. Correct rationale and error severity remain unmeasured. | Study maintainer |
| Missing logs or duplicate calls | Start fsync before sending, finish records, one run lock | Resume marks lost responses unknown and never retries them. Partial/corrupt ledger lines fail loudly; preserve originals for documented manual recovery. | Run operator |
| Overspend / endpoint drift | Whole-sample reservations, token/byte/call limits, dated rates, returned IDs | Stop on missing usage or bound violation; reconcile invoice/provider caps. Detection occurs after the offending call; hosted version changes may be opaque. | Budget owner and run operator, to be specified |
| Sensitive disclosure | Public toy data/manifests committed; credentials, downloads, keys and live runs ignored; no raw exception text | Review before publication. Logs include task content/model outputs and need access controls if future tasks are sensitive. | Repository owner and run operator |

No elapsed-time or cost claims are derived from fixture timings. Marginal inference costs, human review, development costs and maintenance burden must remain distinct. The first two require live/application evidence; development time was not metered.

## Verification and remaining work

Source verification uses the tests in `tests/test_core.py`. A recorded CLI fixture run will include its exact source commit, code/spec hashes, frozen configuration and complete ledger. Scripted outcomes must always retain `verification_only=true` and `NO_EFFICACY_INFERENCE_FIXTURE`.

Prepared: reproducible acquisition, 20 development and 60 separate candidate evaluation tasks, manifests, versioned prompts/config, frozen-run machinery, HTTP adapter and offline analysis. Evaluated: **no real model**. Operationally validated: **no**. Live endpoint smoke testing and provider billing verification remain required before the held-out feasibility run.

Only three user decisions currently block live work: accept or replace the arithmetic feasibility population; identify an accessible fixed model/provider execution route; establish a total spending cap for smoke/development/evaluation. The operator can then derive call reservations from verified prices and fill the config. Practical outcome/resource thresholds are additionally required before an efficacy/adoption study. Credentials belong in the execution environment, not conversation text. Repository destination has already been resolved.

## Amendment from v0.1

| Change | Rationale | Affected comparisons / revalidation |
|---|---|---|
| Share A; give C a solution and common finalisation stage | Remove avoidable initial-draft variation and a one-versus-three-call mismatch | All A/B/C results; rerun on a new freeze |
| Replace lexical recall with strict numeric scoring and separate keys | Match the provisional arithmetic endpoint and prevent direct key exposure | No v0.1 scores are interchangeable; validate scorer and task fit |
| Introduce structured config, frozen inputs, durable ledger and fail-closed HTTP adapter | Make provenance, cost assumptions and failed calls inspectable | New CLI/config and run schemas; old command-backend interface is retired |
| Distinguish fixture, development and feasibility records | Prevent scaffold outputs from becoming efficacy claims | Revalidate live transport separately; retain old history |

This is a consequential methodological amendment, not a reanalysis of compatible v0.1 results. `data/dev.jsonl` and the original licence remain intact. No operational workflow has been changed.
