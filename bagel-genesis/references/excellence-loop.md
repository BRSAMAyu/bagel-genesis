# Excellence Loop

Use after baseline completion. The loop keeps improving until additional work has low expected value, not merely until the artifact runs.

## Principle

Baseline completion proves viability. Excellence loop creates quality through **continuous positive optimization** — the run does not seek a stopping point, it seeks to keep converting time and tokens into verifiable improvement until budget is exhausted, the user stops it, or a hard-stop boundary is reached.

The system should actively discover improvements the user did not specify, decide reversible issues autonomously, generate and raise quantitative standards as the artifact matures, and keep iterating. **"Good enough" is not a concept in this loop.** The only legitimate end states are: budget/token exhaustion (with resume checkpoint), user stop, hard-stop boundary, or genuine exhaustion of all positive-optimization avenues confirmed by independent review across multiple rounds and multiple discovery lenses.

Stopping early — declaring done while measurable improvement remains possible — is the single most serious failure mode of this loop. Anti-laziness is a first-class design goal, equal to correctness.

## Loop Shape

```text
while run_budget_allows and autonomy_contract_allows:
  # Drive A: generate/refresh metrics appropriate to this artifact
  ensure_metrics_exist()        # if none yet, generate them (see Metric Self-Generation)
  run_current_metrics()

  # Drive B: discover improvements via independent review + multiple lenses
  discover_improvements()       # independent review, red-team, brainstorm, new-dimension search
  rank_by_expected_value()

  # Drive C: if all current metrics are green AND review finds nothing new,
  #          RAISE THE BAR instead of stopping (see Bar-Raising Protocol)
  if all_metrics_green and review_finds_no_P0_P1_P2:
    raise_bar_or_find_new_dimension()
    if bar_could_not_be_raised:   # only path toward considering done
      increment_diminishing_counter()
    else:
      reset_diminishing_counter()
      continue                    # new higher targets exist — keep iterating

  # Drive D: execute the best improvement
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

The loop has no `excellence_horizon_passed` exit condition in the normal path. The horizon defines the *starting* quality bar, not the stopping point. Stopping is a last resort triggered only by the stringent conditions in Stop Criteria below.

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

## Metric Self-Generation

The agent generates quantitative metrics appropriate to the current artifact — it does not wait for the user to hand them a checklist, and it does not hardcode software-only metrics. The goal is an objective, runnable signal that distinguishes real improvement from subjective "feels better."

**Generation process (runs at first polish cycle, refreshed when artifact type shifts):**

1. Identify the artifact type (software / research / writing / data / mixed) from `.bagel/artifact_profile.yaml` or the constitution.
2. For that type, propose 2-6 metrics that genuinely reflect quality for *this specific project*. Examples by type (illustrative, not exhaustive — the agent must reason about what actually matters for this artifact, not copy a template):
   - software/app: test coverage, e2e pass rate, Lighthouse/performance, bundle size, a11y violations, type errors, lint errors, crash rate.
   - research/computational: benchmark score vs baseline, reproducibility (does re-run match?), statistical confidence, ablation delta, error-bar width.
   - writing/document: word-count targets per section, reading-grade-level, structural continuity checks, citation completeness, claim-evidence coverage.
   - data analysis: validation-rule pass rate, schema conformance, null/outlier counts, chart/table correctness checks.
3. For each metric, define a runnable command (or a manual evidence procedure when automation is impossible) and a target. Record in `.bagel/state.yaml` under `excellence.metrics`.
4. Run them every cycle. The delta (improved / flat / regressed) feeds Track 2 of the progress assessment.

**Critical:** metrics are *generated*, not *received as gospel*. If a metric turns out to be gameable or not correlated with real quality (e.g. coverage hits 100% but tests are trivial), the agent must replace it with a better signal and note the replacement in the evolution ledger. The point is a truthful objective anchor, not a number to satisfy.

Metrics that resist automation (e.g. "is the argument convincing?") stay in Track 1 (independent review). Do not force a fake quantitative proxy for something genuinely qualitative — but do keep searching for a real one.

## Bar-Raising Protocol

When all current metrics are green AND independent review finds no new P0/P1/P2, **do not stop. Raise the bar.** This is the core anti-laziness mechanism: "meeting the current standard" is a signal to define a higher standard, not a signal to declare done.

**Bar-raising moves (try in order each time the current bar is cleared):**

1. **Tighten existing targets:** coverage 80%→90%, Lighthouse 85→95, benchmark +5%→+15% vs baseline, a11y violations 5→0, bundle size <250kb→<180kb. Each tightening is a new row in `excellence.metrics` with a higher target.
2. **Add new quality dimensions not yet measured:** if performance is green but you never measured memory usage, add it. If tests pass but you never checked error-recovery paths, add scenario tests for them. If the app works but you never measured cold-start time on slow devices, add it.
3. **Add adversarial/edge lenses:** fuzz inputs, malformed data, concurrent access, offline behavior, accessibility for real assistive tech, i18n, security review. Each can generate new metrics or new review findings.
4. **Pursue "astonishingly complete" discovery:** what would make a skeptical expert reviewer say "I didn't expect this level of polish"? Documentation depth, error message quality, developer onboarding, observability, graceful degradation. Generate tasks for the gaps.
5. **For research/experiment artifacts:** when the current hypothesis is validated, ask whether a stronger hypothesis, a larger eval, an ablation, a failure-mode analysis, or a competing-approach comparison would strengthen the claim. Raise the evidentiary bar.

**Recording bar raises:** every raised target or new dimension goes into `.bagel/evidence/bar-raises.yaml` with: what was raised, why, the new target, and which cycle. This makes the optimization trajectory auditable — the user can see the artifact didn't just "pass," it was driven upward through N bar raises.

**When bar-raising itself stalls:** if the agent attempts all five moves and genuinely cannot identify a higher target or new dimension, AND an independent reviewer (different agent/context) also cannot after inspecting the artifact and the current metric set, increment the diminishing-returns counter. This is the only path toward considering the run done — and it requires independent confirmation, not self-declaration. See Stop Criteria.

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

`net_assessment` must be evidence-backed and **independently assessed, not self-declared by the implementing agent**.

### How forward / lateral / backward is determined (the assessment must not be self-evaluated)

`net_assessment` is the single most load-bearing judgment in the loop, because the stop counters and the strategy-switch trigger both depend on it. It must not be a free-text self-report by the agent that did the work. Use this two-track assessment:

**Track 1 — Independent review (primary, always applies):** a reviewer at the QA-required independence level (R3/R4 when available; see `quality-assurance.md`) inspects the diff/evidence and produces findings classified P0/P1/P2/INFO. The reviewer — not the implementer — contributes the qualitative component of `net_assessment`:
- `forward` requires the reviewer to find net reduction in P0/P1 findings, or an accepted improvement with no new P0/P1.
- `lateral` means the reviewer found no net change in P0/P1 (activity without measurable quality movement).
- `backward` means the reviewer found new P0/P1 or a regression.

**Track 2 — Quantitative metrics (objective anchor, when defined):** if the alignment phase defined quantitative metrics in `excellence_horizon.yaml.quantitative` (test coverage, benchmark score, Lighthouse, e2e pass rate, error count, etc.), the agent runs those commands every cycle and records the delta. These metrics are objective — they either moved or they didn't. When available, they override the qualitative track on factual questions (did coverage go up? did the benchmark improve?).

**Combined rule:** when both tracks exist, `forward` requires BOTH the reviewer to find no new P0/P1 AND at least one quantitative metric to improve (or all already at target). When only the qualitative track exists (no metrics defined), the assessment is marked `low_confidence` in the delta record — the run continues but the stop counters treat `low_confidence` as `lateral` (does not count toward forward), so a run cannot declare "done" purely on subjective review.

This prevents the failure mode where an agent self-declares `forward` on its own work, runs up the counters, and stops early — or the inverse, where it loops forever on subjective "improvements" because nothing objective ever moves.

Three consecutive `lateral` cycles (or `low_confidence` cycles) or any `backward` cycle requires a strategy change: switch hypothesis, dispatch independent diagnosis, reduce scope, create a better verifier, rollback agent-owned changes, or advance another high-EV lane. It is not a reason to stop unless the change needed crosses a hard-stop boundary.

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

**Stop rule:** the counters are mechanical (stored as scalars, incremented by rule), but the `net_assessment` values that feed them are **independently assessed per the two-track rule above** — not self-declared by the implementing agent. The run enters `done` only when ALL of:
- `consecutive_lateral_cycles >= 2` (two cycles where independent review + metrics found no net improvement), AND
- `rounds_without_high_evidence_finding >= 2` (two review rounds where no reviewer finding produced an accepted artifact change), AND
- `open_P0 == 0 AND open_P1 == 0`.

A "high-evidence finding" is a reviewer finding (at the required independence level) that produced an accepted artifact change in the same round — an objective diff event, not a self-scored `ev_score`. The `ev_score: 1-5` integer is for *ranking* candidate tasks only; it must not gate stopping.

This is not "purely mechanical" — it is mechanical-counters-fed-by-independent-assessment. The judgment still lives in the review (Track 1) and metrics (Track 2), but it is no longer the implementing agent judging its own work, and the stop condition is no longer a free-form self-declaration of "no improvements remain."

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

**The default is: do not stop.** In delegated long-run mode the run continues until budget/token exhaustion (with resume checkpoint), user stop, or a hard-stop boundary. Declaring "done" before those is the exception, not the rule, and requires meeting a stringent bar designed to make early exit very hard.

**Done requires ALL of the following (the bar is intentionally high to prevent laziness):**

1. **No open P0/P1** — `open_P0 == 0 AND open_P1 == 0`.
2. **Bar-raising exhausted** — the agent attempted all five Bar-Raising moves (tighten targets, add dimensions, adversarial lenses, astonishingly-complete discovery, stronger evidence) and could not produce a new target or finding, AND an **independent reviewer** (separate context/agent) also attempted and agreed nothing could be raised. Self-declaration that "I can't think of anything better" does not count. Record both attempts in `.bagel/evidence/bar-raises.yaml`.
3. **Independent review finds nothing** — at least 2 consecutive review rounds at the required QA independence level produced no P0/P1/P2 finding that led to an accepted artifact change.
4. **Multiple discovery lenses exhausted** — red-team, user-persona, design/architecture critique, and at least one domain-specific lens (benchmark, reproducibility, security, etc.) all returned no positive-optimization opportunity in the last round.
5. **Diminishing-returns counter met** — `consecutive_no_optimization_rounds >= 2` (stored as scalar in state.yaml, incremented only when conditions 2-4 all hold for a round, reset to 0 the moment any of them produces work).
6. **Final briefing complete** — STATUS.md Morning Briefing reflects the final state, all bar raises are documented, the optimization trajectory is auditable.

Only when ALL six hold, write `.bagel/evidence/excellence-stop.md` with: the scalar counter values, the last 2 review round summaries, the list of bar-raise attempts that failed, and the discovery lenses tried. This evidence must show *genuine exhaustion confirmed independently*, not "the agent got tired."

**Anti-laziness override:** if any of conditions 1-5 is not met, the run is NOT done — continue. If the agent "feels done" but cannot satisfy condition 2 or 3, that feeling is not evidence; dispatch another independent review or try another bar-raise move. The most common laziness pattern is satisfying conditions 1,4,5,6 while skipping 2 and 3 (bar-raising and independent review) — explicitly check for this.

If R3 independent review is genuinely unavailable (no subagents) AND the work is high-risk, the done bar cannot be satisfied for that lane — isolate it, continue safe work, surface in STATUS.md. The run is not done until resolved, but it is not idle.

If budget/token/quota is exhausted before done: write a resume checkpoint (see `loop-runtime.md`), set state to `waiting_for_capacity`, and continue when capacity returns. **Budget exhaustion is a normal, expected end state for a delegated long run — it is not a failure.** The failure mode is stopping early with budget remaining while optimization was still possible.

If the runtime cannot schedule resume, mark `manual_resume_required`; do not imply automatic continuation.

## Anti-Perfection Rule (re-framed: this guards against *low-value* work, not against *continuing*)

This rule does NOT license early stopping. It guards against spending cycles on changes that don't actually improve the artifact. The distinction matters: continuous positive optimization is the goal; random churn disguised as polish is not.

A candidate improvement is **low-value** (defer or reject) only when it meets ALL of:

- it does not move any quantitative metric,
- independent review would not classify it as P0/P1/P2,
- it does not open a new quality dimension or raise an existing bar,
- its risk exceeds its real (not self-scored) benefit.

When the current lane yields only low-value candidates, do NOT stop — **switch to a higher-value discovery lens**: bar-raising (is there a higher target?), red-team (what breaks?), user-persona (what confuses?), architecture (what's fragile?), a new metric dimension (what's unmeasured?). Stopping is only legitimate after the stringent Stop Criteria bar is met, never because "the easy improvements ran out."

Record genuinely rejected low-value candidates in `.bagel/ledger/rejected-improvements.md` with the reason — this proves the agent evaluated and prioritized rather than churned.
