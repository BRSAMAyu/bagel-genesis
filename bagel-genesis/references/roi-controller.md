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
    P0_closed: 0
    P1_closed: 0
    primary_metric_delta: null
    user_visible_improvement: ""
    risk_reduced: ""
    knowledge_gained: ""
    reusable_lesson_created: ""
    option_value_created: ""
  roi_assessment:
    marginal_value: high | medium | low | negative
    continue_same_strategy: true | false
    reason: ""
```

Three low/negative ROI cycles require strategy switch, scope shrink, breakthrough search, or stopping at a user/budget boundary.
