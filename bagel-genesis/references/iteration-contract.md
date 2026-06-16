# Iteration Contract Protocol

Use this whenever autonomous work starts, when an iteration begins or ends, and when the system decides what to do after all current goals are complete.

## Definition

An iteration is not one chat turn, one commit, or one worker task.

One BAGEL iteration means:

1. a target set exists,
2. all tasks required by that target set are completed or explicitly classified,
3. all metrics in the active evaluation spec are green or legitimately carried forward,
4. required independent review finds no blocking P0/P1/P2 for the iteration scope,
5. regression floors from prior iterations still hold,
6. the iteration record is written and pushed/committed when git policy requires it.

Only then increment `iterations_completed`.

## Iteration Record

Persist each iteration under `.bagel/iterations/ITER-NNN.yaml` or quick mode `.bagel/state.yaml#iterations`:

```yaml
iteration:
  id: "ITER-001"
  status: planned | running | complete | partial | blocked_hard_stop
  target_set_ref: ".bagel/evaluation/iteration-01.yaml"
  started_at: "ISO-8601"
  completed_at: null
  required_tasks: []
  completed_tasks: []
  carried_forward: []
  metrics_result: []
  review_refs: []
  judgment_ref: ".bagel/decisions/judgment-ITER-001.yaml"
  value_class:
    - closes_P0_or_P1 | primary_metric_delta | new_quality_dimension | reproducibility_gain | user_visible_friction_removed | hypothesis_result
  evidence_refs: []
  git_ref_start: ""
  git_ref_end: ""
  next_iteration_seed:
    sources:
      - Evaluation Architect
      - Brainstormer
      - Red-Team Oracle
      - Product Visionary
      - Judgment Council
    candidate_targets: []
```

## Adaptive Iteration Budget

Prefer:

```yaml
iteration_budget:
  target_iterations: 4
  max_iterations: 8
  min_meaningful_iterations: 2
  expected_cycles_by_iteration: [2, 3, 4]
  hard_cap: "wall-clock or token cap"
```

`max_iterations` remains the hard ceiling, but a completed iteration must pass the Iteration Value Gate below.

## Iteration Value Gate

An iteration is meaningful only if it includes at least one:

- `closes_P0_or_P1`
- `primary_metric_delta`
- `new_quality_dimension`
- `reproducibility_gain`
- `user_visible_friction_removed`
- `hypothesis_result`

Forbidden as the sole basis:

- governance-only progress,
- cosmetic churn only,
- unverifiable claims,
- metrics that do not affect decisions.

`scripts/flywheel_check.py` validates `value_class` and `evidence_refs` for completed iteration records.

## Near-Ceiling Detector

When a metric appears flat, classify it:

```yaml
near_ceiling:
  metric: ""
  current_value: 0.998
  target_value: 1.0
  ratio_to_target: 0.998
  recent_delta: 0.001
  classification: still_climbable | near_ceiling | bad_metric
```

Do not punish a run for tiny absolute deltas when the metric is already near its real ceiling; switch to a better metric or quality dimension.

## Iteration Start

At the start of every iteration:

1. dispatch Evaluation Architect to generate or refresh the target set and evaluation spec,
2. if the prior iteration was complete, dispatch Brainstormers and, when novelty or plateau signals exist, Product Visionary,
3. use Judgment Council for high-impact next-target direction,
4. record the target set before implementation begins,
5. allocate an iteration cycle cap from remaining budget.

## Iteration End

When all current targets pass:

1. run required checks and independent review,
2. record green floors,
3. write the iteration record,
4. commit/push according to git governance and user/platform policy,
5. generate the next iteration's candidate goals.

Meeting all preset goals is not final completion unless `iterations_completed >= max_iterations`. It is the trigger to design the next higher-value iteration.

## Partial Iterations

If the cycle cap or budget sub-allocation is exhausted before all-green:

- record `status: partial`,
- carry forward unmet targets with evidence,
- dispatch strategy-switch judgment if the same approach has stalled,
- continue if global budget and max_iterations allow.

Do not erase partial work by pretending the iteration completed.

## Stop Logic

The normal final stop is `iterations_completed >= max_iterations`, not "I feel done." If target set N completes and N is below `max_iterations`, the system must start iteration N+1 by generating a stronger target set.
