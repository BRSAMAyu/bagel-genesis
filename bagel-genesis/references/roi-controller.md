# ROI Controller

Use before choosing BAGEL mode and after every autonomous cycle.

## Worth-It Check

```yaml
bagel_worth_it_check:
  task_complexity: low | medium | high
  ambiguity: low | medium | high
  expected_iteration_value: low | medium | high
  risk_of_naive_agent_failure: low | medium | high
  need_for_alignment: low | medium | high
  need_for_verification: low | medium | high
  need_for_expert_strategy: low | medium | high
  recommended_mode: no_bagel | quick_autonomy | measured_run | full_expert_run
  expert_layer_mode: off | lite | standard | full
```

## Per-Cycle Value Accounting

```yaml
value_accounting:
  cycle_id: CYCLE-001
  cost:
    estimated_tokens: 0
    wall_time: ""
    user_questions_asked: 0
    governance_files_touched: 0
    subagent_count: 0
  value:
    hard_value:
      P0_closed: 0
      P1_closed: 0
      primary_metric_delta: null
      deliverable_delta_ref: ""
      replayable_evidence_refs: []
      user_visible_improvement_ref: ""
    soft_value:
      knowledge_gained: ""
      option_value_created: ""
      risk_reduced: ""
      reusable_lesson_created: ""
      evidence_refs: []
  roi_assessment:
    marginal_value: high | medium | low | negative
    continue_same_strategy: true | false
    reason: ""
    high_roi_without_delta_explanation: ""
```

Rules:

- medium/high ROI requires hard value or explicitly evidenced option value.
- knowledge gained, option value, risk reduced, and reusable lessons require evidence refs.
- two soft-value-only cycles require strategy switch or a hard-value probe.
- three low/negative ROI cycles require strategy switch, scope shrink, breakthrough search, or stopping at a user/budget boundary.
