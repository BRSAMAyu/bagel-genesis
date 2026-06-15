# Excellence Loop

Use after baseline completion. The loop keeps improving until additional work has low expected value, not merely until the artifact runs.

## Principle

Baseline completion proves viability. Excellence loop creates quality.

The system should actively discover improvements the user did not specify, decide reversible issues autonomously, and keep iterating while valuable improvements remain within the autonomy contract. In delegated long-run mode, BAGEL should continue until the excellence horizon passes, budget/token capacity is exhausted, the user stops the run, or a hard-stop boundary is reached.

## Loop Shape

```text
while run_budget_allows and autonomy_contract_allows and not excellence_horizon_passed:
  discover_improvements()
  rank_by_expected_value()
  select_best_high_value_task_or_exploration()
  isolate_work()
  execute()
  verify()
  review_at_required_independence_level()
  record_progress_delta()
  if blocked:
    recover_or_switch_to_next_high_value_task()
  update_progress_and_user_briefing()
```

Budget is not implicit. Before entering this loop, create or update the budget section in `.bagel/state.yaml` or `.bagel/run_budget.yaml` as described in `references/loop-runtime.md`.

Default budget allocation for delegated long runs:

```yaml
remaining_budget_share:
  P0_unfinished: 50
  P1_unfinished: 30
  excellence_polish: 20
```

If no P0/P1 work remains, redistribute to the highest-EV improvement classes. Do not spend the majority of remaining budget on polish while required core slices, validation, or reproducibility are incomplete.

## Improvement Sources

Use multiple independent sources:

- spec compliance review,
- code/content/research quality review,
- UX/editorial/argument critique,
- red-team/adversarial review,
- environment/setup reproducibility check,
- accessibility/performance/security checks when relevant,
- "what would embarrass us in a demo/review/publication" pass,
- brainstormer pass for missing opportunities,
- user briefing review for clarity gaps.
- "what else could make this astonishingly complete?" pass,
- experiment/theory alternative generation when results stall,
- toolchain/environment improvement pass when setup limits progress.

For UI, product, game, deck, document, or other visual artifacts, visual verification is part of the loop rather than optional polish:

- capture screenshots or rendered pages for each important state/viewport,
- compare against `taste_kernel` exemplars and anti-examples when available,
- inspect spacing, hierarchy, contrast, overflow, empty/loading/error states, motion, and perceived quality,
- produce concrete fix tasks from the visual evidence,
- repeat after changes until visual P0/P1/P2 findings are resolved or objectively low-EV.

When platform visual tools are missing, create the smallest local screenshot/render harness that is practical before judging visual quality.

For non-software work, replace tests with domain evidence:

- research: citation checks, methodology critique, reproducibility, argument validity,
- computational research/optimization: hypothesis ledger, benchmark harness, baseline comparison, repeated runs or confidence intervals when practical, ablation/failure notes, and winner-retention criteria,
- writing: structure, voice, pacing, continuity, reader experience,
- strategy: assumptions, counterexamples, decision robustness.

Empirical science claims that require physical experiments, proprietary data collection, wet-lab work, human-subject evidence, or real-world deployment must be labeled as outside the autonomous verification boundary unless the needed evidence pipeline is already available and authorized.

## Progress Delta Gate

Every build, recovery, research, and excellence cycle must append to `.bagel/evidence/progress-deltas.yaml`:

```yaml
- cycle: 47
  timestamp: "ISO-8601"
  task: "EX-012"
  tests_delta: "+12 -3"
  coverage_delta: "+2.1%"
  benchmark_delta: "+0.04"
  defects_open: "7 -> 4"
  artifact_state: "P1 slices 8/12, 2 blocked, 0 idle"
  evidence:
    - "npm test"
    - "screenshots/dashboard-mobile.png"
  net_assessment: forward | lateral | backward
  next_strategy: "continue current lane | switch hypothesis | isolate lane | repair verifier | advance independent task"
```

`net_assessment` must be evidence-backed:

- `forward`: fewer open blockers, stronger verification, completed slice, improved benchmark, resolved visual defect, clearer reproducibility, or accepted high-EV improvement.
- `lateral`: activity happened but no measurable artifact, evidence, or blocker state improved.
- `backward`: new regression, broken build, degraded metric, worse visual output, or increased blocker count.

Three consecutive `lateral` cycles or any `backward` cycle requires a strategy change: switch hypothesis, dispatch independent diagnosis, reduce scope, create a better verifier, rollback agent-owned changes, or advance another high-EV lane. It is not a reason to stop unless the change needed crosses a hard-stop boundary.

### Mechanical stop counters (store in state.yaml, do not recompute from narrative)

The lateral counter and the no-finding counter must be stored as **scalar fields** in `.bagel/state.yaml`, updated every cycle, never recomputed from memory or from reading the delta file tail (which fails under context compaction):

```yaml
# .bagel/state.yaml — excellence section
excellence:
  phase: polish | done
  consecutive_lateral_cycles: 0      # increment on lateral, reset to 0 on forward
  last_backward_cycle: null          # cycle id of the most recent backward delta
  rounds_without_high_evidence_finding: 0  # increment per round with no accepted artifact change from a review finding, reset to 0 when one occurs
  open_P0: 0
  open_P1: 0
```

**Mechanical stop rule (replaces self-judged "no positive-EV remains"):** the run enters `done` only when ALL of:
- `consecutive_lateral_cycles >= 2`, AND
- `rounds_without_high_evidence_finding >= 2`, AND
- `open_P0 == 0 AND open_P1 == 0`.

A "high-evidence finding" is an **objective event**: a reviewer finding that produced an accepted artifact change in the same round (a diff landed). It is NOT a self-scored `ev_score`. The `ev_score: 1-5` integer is for *ranking* tasks only; it must not gate stopping. This removes self-assessment from the termination path entirely.

## Task Selection

Every improvement task needs:

```yaml
task:
  id: "EX-012"
  source: "red_team"
  expected_value: high | medium | low
  cost: small | medium | large
  risk: low | medium | high
  ev_score: 1-5
  cost_score: 1-5
  risk_score: 1-5
  acceptance_criteria:
    - "..."
  allowed_scope:
    - "..."
```

Prefer high-value, bounded improvements. Accept moderate risk when rollback is cheap and the expected value is high. Do not spend many cycles on low-value polish unless the excellence horizon explicitly requires it, but do continue searching for higher-value feature, UX, research, setup, verifier, or architecture improvements.

Expected value rule:

- Execute when `ev_score > cost_score + risk_score` or the issue is P0/P1.
- Defer only when value is real but a better positive-EV task exists, or the change crosses the autonomy contract.
- Reject when value is low, speculative, or outside constitution.

Raise the bar as polishing matures:

```yaml
ev_threshold_by_round:
  round_1: medium
  round_2: high
  round_3_plus: P0_or_P1_or_objectively_high
diminishing_returns_signal:
  - "two consecutive rounds produce no accepted high-EV artifact change"
  - "accepted changes are below 30% of the previous productive round"
  - "progress deltas are lateral across three cycles"
```

The threshold prevents endless minor polishing. It does not permit stopping while unfinished P0/P1 scope, broken verification, or high-EV tasks remain.

Default cap when the user has not specified long-run delegation: at most 3 excellence discovery rounds and 6 implementation cycles after baseline. When the user explicitly delegates long-run autonomy, this cap does not apply; use `.bagel/run_budget.yaml`, available token/runtime capacity, and the stop criteria below.

## No Self-Approval

The worker that made an improvement cannot approve it. Completion requires evidence from:

- tests or executable checks,
- reviewer at the QA-required independence level,
- artifact diff inspection,
- user-facing briefing update,
- domain-specific verification.

## Stop Criteria

In delegated long-run mode, stop before final delivery only for user stop, budget/token exhaustion with a resume checkpoint, or a hard-stop boundary.

**The stop condition is mechanical, read from `state.yaml.excellence`, not self-judged.** Final delivery requires ALL of:

- baseline completion passes,
- `consecutive_lateral_cycles >= 2` (two cycles with no measurable improvement),
- `rounds_without_high_evidence_finding >= 2` (two review rounds where no reviewer finding produced an accepted artifact change — an objective diff event, not a self-score),
- `open_P0 == 0 AND open_P1 == 0`,
- final user briefing is coherent and complete,
- objective stop evidence exists in `.bagel/evidence/excellence-stop.md`.

When these hold, write `.bagel/evidence/excellence-stop.md` with the scalar values and the two most recent review round summaries as proof. Do NOT add "no unresolved high/medium EV improvement" as a separate self-judged criterion — that path is closed; the `rounds_without_high_evidence_finding` scalar replaces it.

If R3 independent review is genuinely unavailable (no subagents) AND the work is high-risk, the mechanical stop cannot be satisfied for that lane. Do not fake R3 or call R1 independent. Instead: isolate the lane (see SKILL.md tie-breaker isolation procedure), mark `state.yaml.excellence.phase = done_for_safe_lanes`, continue safe work, and surface in STATUS.md that high-risk lane X awaits R3 or user review. The run is not "done" until that lane is resolved, but it is also not idle.

The EV formula supports ranking only; it is not by itself proof of final quality and must not gate stopping.

If budget or quota runs out before this, write a resume checkpoint and continue when capacity returns.

If the runtime cannot schedule resume, mark `manual_resume_required`; do not imply automatic continuation.

## Anti-Perfection Rule

Excellence is not random polishing. Reject improvements when:

- expected value is low,
- change risk exceeds benefit,
- it violates the constitution,
- it expands scope beyond the agreed deliverable,
- it delays delivery without user-visible or domain-significant gain.

When all generated improvements are low-value, run a different discovery lens before stopping: red-team, user persona, design critique, benchmark/experiment alternative, setup/reproducibility, or architecture simplification. Stop for diminishing returns only after multiple distinct lenses fail to produce positive-EV work.

Document rejected improvements in `.bagel/ledger/rejected-improvements.md`.
