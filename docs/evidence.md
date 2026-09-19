# Bounded evidence review

Question: when does intrinsic critique followed by revision add value beyond direct answering and additional effort? Discovery and primary-source checks: 2026-09-12–13.

SciSpace search worked and returned studies on intrinsic self-correction, reflection, planning and critique training. Search concepts included self-critique without external feedback, direct baselines, additional inference effort and supportive/adverse outcomes. Generated summaries were used as discovery aids. The four records below were checked against accessible primary full text; version dates were checked against arXiv metadata. This is a targeted design review, not an exhaustive or systematic review. No publication-count or pooled-effect claim is made.

## Primary studies

| Source and version | Method and comparison | Finding and uncertainty | Applicability and experimental implication |
|---|---|---|---|
| Madaan et al., *Self-Refine: Iterative Refinement with Self-Feedback*, [v2, 2023-05-25](https://arxiv.org/pdf/2303.17651v2) | Same-model feedback and iterative refinement across seven tasks; direct generation and feedback ablations | Supportive task-specific improvements under human and automatic evaluations. Different metrics, prompting and iteration budgets prevent reading the reported aggregate as one transferable accuracy effect. | Supports testing explicit feedback. Sections 4 and appendix analyses also show feedback/model-quality limitations. Do not assume benefits for this one-round arithmetic configuration. |
| Huang et al., *Large Language Models Cannot Self-Correct Reasoning Yet*, ICLR 2024, [v2, 2024-03-14](https://arxiv.org/pdf/2310.01798v2) | Intrinsic correction on reasoning benchmarks, including GSM8K; contrasts with external/oracle feedback and different initial prompting | Often no improvement or deterioration in the tested models. Their analysis identifies correctness-based stopping and weaker initial prompting as potential explanations for apparent gains. These are historical model/configuration results, not an impossibility theorem. | Strong reason to keep gold answers out of all generation stages, use a credible A, add C, and count regressions. Closest reviewed task match; not evidence about the selected deployment. |
| Li, Yang and Ettinger, *When Hindsight is Not 20/20: Testing Limits on Reflective Thinking in Large Language Models*, NAACL Findings 2024, [v1, 2024-04-14](https://arxiv.org/pdf/2404.09129v1) | Reflection without external correctness feedback; multiple candidate answers, including K=4 configurations, then revision on TruthfulQA and HotpotQA | Benefits on TruthfulQA and adverse results on HotpotQA. Initial correctness, difficulty and scoring choices influence interpretation; lexical scoring can miss semantic correctness. | Motivates repairs-versus-regressions reporting and a task-valid scorer. Multiple-candidate QA differs from this shared-draft arithmetic intervention; no expected effect size is imported. |
| Bohnet et al., *Enhancing LLM Planning Capabilities through Intrinsic Self-Critique*, [v1, 2025-12-30](https://arxiv.org/html/2512.24103v1) | Blocksworld, Logistics and Mini-grid; strong many-shot baselines, repeated critique loops, some critique-consistency variants | Gains for some evaluated models, with modest/null results in weaker configurations. Multiple loops and explicit planning representations change the treatment. The paper evaluates model checkpoints from 2024 despite its 2025 posting date. | Counters a universal claim that intrinsic critique cannot help. It supports a conditional hypothesis, not a prediction for one-round arithmetic or current-model superiority. |

No reviewed effect size is used to power the pilot: populations, feedback mechanisms and compute allocations differ. Study-specific uncertainty does not resolve the unmeasured effect on the proposed model. Detailed task/model tables should be revisited only if a different population or treatment becomes the target.

## Claim-to-design map

| Claim under consideration | Support and conflict | Remaining uncertainty | Consequence |
|---|---|---|---|
| Critique can add value | Self-Refine and some planning conditions support it; Huang and parts of Li show failures | Selected task/model/prompts may behave differently | Include both positive and negative outcomes in the hypothesis |
| Improvement is specifically due to prescribed critique | Direct-baseline gains alone cannot establish this; adverse work highlights effort and feedback confounds | B/C inputs and actual resource use still differ in length/content | Shared A, equal B/C output ceilings, common finalisation, actual-usage records; limit attribution |
| A benchmark gain warrants architecture change | None of these studies validates this project's users or economics | Real task distribution and practical thresholds are absent | Feasibility first; retain the simplest architecture pending relevant evidence |

Additional trained-critic/fine-tuning studies surfaced in discovery but were not selected because they change weights, training data or feedback sources. A systematic latest-model ranking would not change the currently blocked execution decision. Stop rule reached: the reviewed evidence already changes the design in the material ways above; further searching has lower value than establishing task fit and running the bounded comparison.

## Resource provenance

The [GSM8K dataset card](https://huggingface.co/datasets/openai/gsm8k/blob/main/README.md) and [original dataset repository](https://github.com/openai/grade-school-math) provide source format, splits and licence context. Exact revisions and acquired-content hashes are in `data/manifests`.

[Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) is a provisional public, Apache-2.0 candidate with a recorded weight revision in `config/live.template.json`. Its catalogue entry and listed inference providers establish discovery, not authenticated execution or suitability. A hosted provider may not expose the exact weight revision. The [official chat-completion contract](https://huggingface.co/docs/inference-providers/tasks/chat-completion) informed the HTTP adapter; its live endpoint compatibility remains untested.
