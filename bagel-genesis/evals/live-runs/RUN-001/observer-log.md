# RUN-001 Observer Log — leak hunt

Real run: invoked `bagel-genesis` as Supervisor on product workspace `D:\code\bagel-liverun-001`, task = build `linkcheck`. Deliberately bounded to **boot → runtime-capability/proof layer → one real engine probe** — the high-value structural leaks reproduced concretely there, so the full toy build was not ground out (diminishing findings per token). The deliverable of this run is the findings below, not the CLI.

Severity: P0 (breaks trust model / run) · P1 (materially weakens a frontier) · P2 (papercut/cost) · INFO.
Frontier tags: `[anchor]` ground-truth/external verification · `[engine]` iteration/idea/taste quality · `[complexity]` governance↔outcome.

## Findings

| # | phase | tag | sev | observation | proposed fix |
|---|---|---|---|---|---|
| 1 | boot | [complexity] | P2 | `detect_runtime_capabilities.py` takes `--out`, but **every other** BAGEL script (`bagel_v3_check.py <root>`, `runtime_proof_check.py <root>`, …) takes a positional `<root>`. An autonomous agent following the dominant convention calls `detect…py .` → `error: unrecognized arguments: .`. First command of every run. | Accept a positional `root` (write `<root>/.bagel/runtime_capabilities.yaml` by default) OR have SKILL.md's Boot Sequence name the exact invocation. Normalize the script CLI convention repo-wide. |
| 2 | boot | [anchor] | P1 | The detector sets `true_subagents.observed: true` from **mere CLI presence** (`true_subagents_observed = claude_cli`, line 135) — before any real dispatch — while timers/hooks correctly default to `unknown` pending proof. So every fresh run starts with an over-claim that `runtime_proof_check` will then reject until a proof file appears. Inconsistent and it *teaches* the agent that `observed:true` precedes evidence. | Default `true_subagents.observed: unknown` like timers/hooks. Flip to `true` only when a real proof file is written. Removes the boot-time over-claim and the guaranteed-then-repaired gate dance. |
| 3 | boot | [anchor] | **P0** | **Core leak, reproduced.** `runtime_proof_check.py` is *not* a rubber stamp (it requires the proof file to exist, be non-empty, have `isolated_context:true`, `result:pass`, `verifier_agent_id`, …) — but it checks **shape, not ground truth**. A hand-written `subagent-proof.yaml` with **zero real dispatch behind it** PASSES, byte-indistinguishable from the proof backed by the real Brainstormer dispatch `a2d7e21234fad199a`. This is the system's own "unifying residual" (enforcement-honesty.md:39) instantiated on a concrete artifact. | Bind runtime proofs to something the agent didn't author: a **Task-tool `PostToolUse` hook** that records the real dispatch (agentId, isolated context) into the proof — the hook process writes it, not the agent. `.claude/settings.json` currently hooks Bash/Write/Edit/Stop but **not** the Agent/Task tool, so a real-dispatch proof can't be auto-captured today. The CI auditor remains the only fully-external anchor. |
| 4 | engine | [engine] | INFO (positive) | A real Brainstormer (one pinned lens, isolated context) produced **genuinely expert-level, non-obvious** linkcheck candidates: per-generator slug rules (GitHub vs kramdown vs MkDocs), duplicate-heading `-N` suffixes, `{#custom-id}` overrides, **case-only mismatch that passes on Windows/macOS but 404s on Linux CI**, code-fence/inline-code exclusion, reference-style link resolution, SARIF output, syscall-count perf assertion. Each with a falsifiable breaking test. | No deficiency in the *idea* engine. Updates the prior: raw generation is strong **when the lens is sharp and context is fed**. The leverage is orchestration discipline (reliably pinning sharp lenses) + the **selection/taste** layer — which is exactly where mode-2 (科研品位) lives. Invest there, not in idea-generation capacity. |
| 5 | boot | [complexity] | P1 | Front-load is real: the run consumed SKILL.md (~13k tok) + boot reads + validator inspection and created 2 `.bagel/` control-plane files **before a single line of product code**. (Not a representative per-cycle ratio — full build not run — but the cold-start tax is concretely heavy and front-loaded.) | Measure `governance_token_share` on a real full cycle (next run). If boot tax dominates short tasks, add a `snap_autonomy` tier below `quick_autonomy` for bounded tasks that skips more of the boot machinery. |

## Frontier verdicts (evidence-backed, replacing the earlier inference)

- **#1 Ground-truth anchor — confirmed the #1 gap, now with a concrete repro (finding 3).** The validator suite is honest and non-trivial but shape-bound; the only real closure is external (Task-tool hook → proof, or the CI auditor). This is where to invest.
- **#2 Iteration engine — prior partially overturned (finding 4).** Raw idea generation is strong. The real lever is the *selection/taste* layer and orchestration discipline, not idea capacity.
- **#3 Complexity→outcome — heavy cold-start confirmed (finding 5); per-cycle share still to be measured on a full build.**

## Resolution — frontier-1 fix applied & verified (2026-06-19)

Findings 1, 2, 3 fixed in the skill repo:
- **F1 (CLI):** `detect_runtime_capabilities.py` now takes positional `<root>` (writes `<root>/.bagel/runtime_capabilities.yaml`); `--out` still works.
- **F2 (over-claim):** detector defaults `true_subagents.observed: unknown`; flipped to `true` only by the hook on a real dispatch.
- **F3 (P0 leak): closed under attested mode.** New `scripts/attest_subagent.py` (Task PostToolUse hook) writes a signed `tool: Task` attestation whose `agent_id` comes from the platform `tool_response`, refreshes the proof's `verifier_agent_id`/`attestation_ref`, and flips `observed`. `runtime_proof_check.py` now binds the `true_subagents` proof to a real signed Task dispatch when `BAGEL_ATTEST_KEY` is set.

Verified in `D:\code\bagel-liverun-001`:
- real dispatch → `verifier_agent_id: a2d7e21234fad199a`, bound proof PASSES.
- **forged proof (fake id, no matching attestation) → FAILS (exit 1).** ← leak closed.
- no key → shape-only PASSES (backward compatible, honest UNATTESTED).
- regression: `skill_lint` passes; mechanical_grader 17/20 both before and after my change (the 3 failures are pre-existing fixture drift, unrelated — see below); all 4 modified scripts compile.

Honest residual (unchanged class): an *informed* agent that reads `BAGEL_ATTEST_KEY` can still mint a forged Task attestation. This binds the proof to a real dispatch under key isolation and kills the uninformed/lazy path; full closure stays external (CI auditor).

## Pre-existing issues found in passing (NOT caused by this run)
- mechanical_grader 17/20 on pristine HEAD: 3 fixtures fail — (1) "CI auditor signed PASS verifies" (`scripts/extract_metric.py` sha256 ≠ preregistered hash), (2) "audit verifier rejects untrusted public-key fingerprint", (3) "research_governance accepts compliant mode-2 amendment". Fixture/hash drift; worth a separate fix.

## RUN-002 — net_assessment independence, tested live with real Haiku subagents (2026-06-19)

Real isolated dispatches (model=haiku): Implementer `a097f5cd5345be398` (30.7k tok) built a real linkcheck baseline (4 files, 17 passing tests, exit codes work); independent Reviewer `a8e930ead74b2a1ff` (37.5k tok), **separate context, NOT shown the implementer's self-report**, told to be adversarial.

| # | tag | sev | observation |
|---|---|---|---|
| 6 | [anchor] | INFO (positive) | **Independence works in substance.** Implementer self-reported "complete and tested… covers all scenarios" (would self-assess `forward`). The independent reviewer returned **`backward`, 8 findings (1 P0, 6 P1, 1 P2)** — overriding the optimistic self-report. Several findings (code-fence over-reporting, duplicate-heading `-1`, `{#custom-id}`, `%20` decode, reference-style links) are exactly the non-obvious issues the Brainstormer predicted. The two-track rule (net_assessment from reviewer, not implementer) produces a genuinely harder, different verdict. |
| 7 | [anchor] | **P1** | **A single reviewer is NOT ground truth.** Orchestrator verified findings against the real code: the reviewer's **P0 ("bare `#` must be reported broken") is FALSE** — spec says skip `#`-only links and the impl correctly does; `[bare](#)` is not flagged. Its code-fence P1 is **confirmed real** (`[x](nope.md)` inside ``` ``` IS over-reported). So the reviewer is rigorous but produced one confidently-wrong finding. Shape checks can prove "a reviewer ran"; they cannot prove "its findings are correct." |
| 8 | [complexity] | INFO | One real build+review cycle = ~68k subagent tokens on Haiku (30.7k + 37.5k), producing real code + a real review. Concrete per-cycle datapoint. |

**Actionable synthesis (ties anchor↔engine):** the reviewer/brainstormer already emit `demonstrating_input` for every finding. **Auto-execute those inputs as throwaway regression checks** — a finding whose input reproduces the claimed wrong behavior is CONFIRMED; one that doesn't (the bare-`#` P0) is auto-rejected. This converts review from shape-trusted opinion into executably-verified evidence, and is the strongest available `net_assessment` anchor wherever the artifact is runnable. Proposed as the next frontier-1 fix.

## Still not tested
- Real `governance_token_share` over a full orchestrated cycle (these were direct dispatches, no orchestrator governance overhead measured).
- Whether the excellence-loop bar-raise actually consumes the non-obvious candidates vs converging on obvious polish.
