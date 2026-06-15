# Excellence Loop

Use after baseline completion. The loop keeps improving until additional work has low expected value, not merely until the artifact runs.

## Principle

Baseline completion proves viability. Excellence loop creates quality through **continuous positive optimization** — the run does not seek a stopping point, it seeks to keep converting time and tokens into verifiable improvement until budget is exhausted, the user stops it, or a hard-stop boundary is reached.

The system should actively discover improvements the user did not specify, decide reversible issues autonomously, generate and raise quantitative standards as the artifact matures, and keep iterating. **"Good enough" is not a concept in this loop.** The only legitimate end states are: budget/token exhaustion (with resume checkpoint), user stop, hard-stop boundary, or genuine exhaustion of all positive-optimization avenues confirmed by independent review across multiple rounds and multiple discovery lenses.

Stopping early — declaring done while measurable improvement remains possible — is the single most serious failure mode of this loop. Anti-laziness is a first-class design goal, equal to correctness.

## Iteration Model

The excellence loop runs as a fixed number of **iterations**, each ending when the current target set is fully met (all metrics green + no open P0/P1). The user sets `max_iterations` during alignment (default 3 if unspecified). Each iteration produces a higher target set for the next. **Stopping is determined by iteration count — a hard, user-set, fully auditable boundary — not by the agent judging "can't improve further."**

## Flywheel Integrity Gate

After every build, recovery, research, or polish cycle, run:

```bash
python scripts/flywheel_check.py <project-root>
```

This is a gate, not a report. If it fails, the run must repair the failed condition before claiming progress. The validator mechanically checks the six load-bearing properties of the autonomy flywheel:

1. **Objective deltas:** every cycle has saved artifact/output evidence and independent assessment.
2. **No fake independence:** review levels are derived from registry/context, not self-reported.
3. **No regression:** current metric values do not fall below prior green floors.
4. **No budget burn:** iteration cycle caps and remaining budget allocation protect core scope.
5. **No churn bar-raises:** raised standards have a valid `why_class` and evidence.
6. **No low-yield spinning:** `trajectory_slope.flat_climbing` is surfaced with an action.

When the validator fails, use recovery protocol: fix missing evidence, dispatch an independent reviewer, rollback or isolate a regressing change, switch hypothesis/lane, or update the budget/target state. Do not continue to the next cycle with a failing flywheel integrity gate.

```text
iteration = 0
target_set[0] = baseline targets + agent-generated metrics (see Metric Self-Generation)

while iteration < max_iterations and run_budget_allows and autonomy_contract_allows:
    iteration += 1

    # --- Inner loop: drive current target_set to all-green WITHOUT regressing prior iterations ---
    while not target_set[iteration].all_green():
        run_current_metrics()
        # REGRESSION GATE: before declaring all-green, verify no metric from any
        # previously-green iteration has dropped below its achieved value.
        # The floor is the last-known-good value, not the original target.
        if all_green and review_finds_no_P0_P1_P2 and no_regression_vs_prior_iterations:
            break                     # target set met AND nothing regressed → iteration complete
        if all_green and not no_regression_vs_prior_iterations:
            # All current targets met but a prior floor was broken — do NOT complete.
            # Treat as backward: rollback the offending change or fix the regression first.
            handle_regression()
            continue
        select_and_execute_best_improvement()
        verify(); review(); record_progress_delta()
        if blocked: recover_or_switch_lane()
        if cycles_in_this_iteration >= iteration_cycle_cap: break  # concrete cap (see below)
        if run_budget_exhausted: break

    # Record the green floor of this iteration for the next iteration's regression gate
    if iteration_completed_normally:
        record_green_floor(iteration, metric_values_at_completion)

    # --- Record this iteration in the evolution ledger ---
    record_iteration(iteration, target_set[iteration], metrics_trajectory, bar_raises, cost)

    # --- If iterations remain, generate the next higher target set ---
    if iteration < max_iterations and run_budget_allows:
        target_set[iteration+1] = generate_higher_target_set(target_set[iteration])
        # Bar-Raising Protocol: tighten targets, add dimensions, adversarial lenses, etc.

# Stop: max_iterations reached, or budget exhausted, or hard-stop
write_final_summary(iterations_completed, trajectory, final_quality_state)
```

### Per-iteration guards (prevent collapse and death-loops)

**Iteration cycle cap:** each iteration gets a concrete cycle budget, not an open-ended inner loop. Compute it at iteration start:

```text
iteration_cycle_cap = max(3, floor(run_budget_remaining_cycles / (max_iterations - iterations_completed)))
```

If `cycles_in_this_iteration >= iteration_cycle_cap`, the iteration ends as `partial` regardless of all-green status. Record which targets were unmet. This guarantees one broken build or one hard metric cannot consume the entire run — the flywheel advances to the next iteration (or stops if it was the last).

**Stuck-metric detector:** if a single metric stays red for >K cycles (K = iteration_cycle_cap / 2) despite ≥2 genuine strategy switches (per recovery-protocol.md's definition — not parameter tweaks), classify it:

- **impossible:** the target cannot be met given current constraints (e.g. "100% type safety" on dynamically-typed code, "0 a11y violations" needs an external service that's down). Reclassify to `unmet_impossible`, carry forward to the iteration record with a user note, and exclude from the all-green gate. The iteration can complete without it.
- **needs-deescalation:** the target is achievable but the current approach is wrong. Relax the target to the last-known-green value for this iteration and record the higher target as a future goal.

This prevents the "impossible target" death-loop where the inner loop hammers an unreachable metric until budget death.

**Automatic rollback on self-inflicted breakage:** if the agent's own change breaks the build/tests and one local repair attempt fails, immediately roll back the change (do not climb the full 9-rung recovery ladder). The tie-breaker already authorizes "rollback the agent's own bad change and retry." This prevents one broken change from burning the iteration cap on recovery.

```

**Why iteration-count stopping is more reliable than judgment-based stopping:** the agent never decides "should I stop?" — the user already decided by setting `max_iterations`. The agent's autonomy is fully directed at *how to optimize within each iteration* and *what higher targets to set for the next*. This eliminates the single most unreliable judgment in the loop (self-assessed "no improvement remains") and replaces it with a counter.

**What "one iteration" means precisely:** one iteration completes when the current `target_set` reaches all-green (every metric at or above target, `open_P0 == 0`, `open_P1 == 0`, independent review finds no P0/P1/P2). If the inner loop exhausts its budget sub-allocation before all-green, the iteration is recorded as `partial` with the unmet targets carried forward.

**If `max_iterations` is not set:** default to 3. The run records this default in the ledger so the user can adjust for next time based on the trajectory (did quality plateau by iteration 2? fewer iterations suffice. Still climbing at iteration 3? raise it).

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
    - command: "npm test"
      path: ".bagel/evidence/cycle-047/npm-test.txt"
    - path: "screenshots/dashboard-mobile.png"
  independent_assessment:
    reviewer_id: "agent-review-vs003"
    review_level: "R3"
    review_report: ".bagel/reviews/REV-047.yaml"
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
  phase: build | polish | done
  max_iterations: 3                  # user-set during alignment (default 3)
  iterations_completed: 0           # incremented when a target set reaches all-green
  current_iteration: 1              # which iteration is in progress
  current_target_set: []            # the metrics+targets for the current iteration
  consecutive_lateral_cycles: 0     # within current iteration; increment on lateral, reset on forward
  last_backward_cycle: null
  open_P0: 0
  open_P1: 0
  metrics:                          # agent-generated, refreshed per artifact type
    # - {metric, target, command, direction, current_value, met: bool}
  iteration_cycle_cap: null          # concrete per-iteration cycle budget, computed at iteration start
  green_floors: {}                   # {iteration_number: {metric: last_known_good_value}} — regression gate floor
  stuck_metrics: []                  # metrics red >K cycles despite strategy switches; classified impossible/needs-deescalation
```

**Within an iteration,** `consecutive_lateral_cycles` and `open_P0/P1` drive strategy switches (not stopping). Three lateral cycles or any backward cycle → switch hypothesis/lens/lane, but keep going — the iteration isn't over until the target set is all-green or budget is exhausted. The run as a whole stops only per Stop Criteria (iteration count / budget / user / hard-stop).

The `net_assessment` values that feed the lateral counter are **independently assessed per the two-track rule above** — not self-declared by the implementing agent. A "high-evidence finding" is a reviewer finding (at the required independence level) that produced an accepted artifact change. The `ev_score: 1-5` integer is for *ranking* candidate tasks only; it must not gate iteration completion or stopping.

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

The run stops when any of these is true:

1. **All iterations complete** — `iterations_completed >= max_iterations`. This is the normal, expected completion path. The user set the count; the agent executed each iteration to target-set-all-green; the run is done.
2. **Budget/token exhausted** — write a resume checkpoint (see `loop-runtime.md`), set state to `waiting_for_capacity`. Budget exhaustion during a delegated long run is normal and expected, not a failure. Record which iteration was in progress and whether it completed.
3. **User stop** — the user halted the run.
4. **Hard-stop boundary** — set state to `blocked_hard_stop` (see STATUS.md wall state). Record what was attempted and what decision is needed.

**There is no "I think it's good enough" stop.** The agent never decides to stop based on its own quality judgment — that path is closed. Stopping is determined by the iteration counter (user-set), budget (finite), or external boundaries. Within an iteration, the agent optimizes toward all-green; between iterations, it raises the bar. Both are autonomous; stopping is not.

**Anti-laziness guarantee:** because stopping is counter-based, the only way to "stop early" is to declare a target set green when it isn't, or to generate a weak next target set. Both are prevented: target-set-green requires independent review confirmation (Track 1) + metric verification (Track 2); next target sets must pass the Bar-Raising Protocol's five moves. An agent that tries to game either will fail the independent review check and the iteration won't complete legitimately — it will keep running until it either meets the bar honestly or exhausts budget.

If the runtime cannot schedule resume after budget exhaustion, mark `manual_resume_required`; do not imply automatic continuation.

## Flat-Climbing Detector (efficiency guard)

The lateral counter catches *zero* movement. But a flywheel can produce *tiny* movement every cycle (coverage 80.0%→80.1%→80.2%) that is technically `forward`, never trips the lateral counter, and burns full budget on negligible gain. This is the efficiency failure the user named: the wheel turns but produces nothing worth the cost.

**Detection:** after each iteration completes, compute the **best metric delta magnitude** of that iteration (the largest real movement across all metrics, in absolute terms). Compare across the last 2 completed iterations:

```yaml
# in state.yaml excellence section, updated after each iteration
trajectory_slope:
  iteration_1_best_delta: 5.2     # e.g. coverage +5.2%
  iteration_2_best_delta: 0.3     # coverage +0.3%
  flat_climbing: false            # true if last 2 iterations each <epsilon AND no P0/P1 closed
```

**`flat_climbing` is true when ALL hold:**
- last 2 completed iterations each delivered <ε real metric movement (ε is metric-specific: e.g. <1% coverage, <0.5 Lighthouse points, <2% benchmark — set per metric at generation time), AND
- no P0/P1 was closed in either iteration, AND
- the bar was raised (so it's not that targets were already maxed — the agent is climbing a near-flat slope).

**Action when `flat_climbing`:**
1. Surface in STATUS.md Morning Briefing: "Flywheel turning but low-yield — iterations {N-1},{N} each moved metrics <ε. Consider: (a) reduce remaining iterations, (b) redirect to a different quality dimension, (c) the artifact may be near its achievable ceiling."
2. If the autonomy contract permits mid-run adjustment: reduce `max_iterations` to `iterations_completed + 1` (allow one more iteration to confirm the plateau, then stop). This is the *one controlled exception* to the hard anti-early-stop stance — justified because flat-climbing *is* the efficiency failure, and continuing to spin is worse than stopping with evidence.
3. Record the flat-climbing detection and the decision in the iteration record so the user can see the plateau was evidence-based, not laziness.

This does NOT permit the agent to self-declare "I think it's flat" — `flat_climbing` is computed from recorded metric deltas, not judgment. The agent acts on a computed signal.

## Anti-Perfection Rule (re-framed: this guards against *low-value* work, not against *continuing*)

This rule does NOT license early stopping. It guards against spending cycles on changes that don't actually improve the artifact. The distinction matters: continuous positive optimization is the goal; random churn disguised as polish is not.

A candidate improvement is **low-value** (defer or reject) only when it meets ALL of:

- it does not move any quantitative metric,
- independent review would not classify it as P0/P1/P2,
- it does not open a new quality dimension or raise an existing bar,
- its risk exceeds its real (not self-scored) benefit.

When the current lane yields only low-value candidates, do NOT stop — **switch to a higher-value discovery lens**: bar-raising (is there a higher target?), red-team (what breaks?), user-persona (what confuses?), architecture (what's fragile?), a new metric dimension (what's unmeasured?). Stopping is only legitimate after the stringent Stop Criteria bar is met, never because "the easy improvements ran out."

Record genuinely rejected low-value candidates in `.bagel/ledger/rejected-improvements.md` with the reason — this proves the agent evaluated and prioritized rather than churned.
