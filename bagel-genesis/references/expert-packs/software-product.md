# Software Product Expert Pack

```yaml
expert_pack:
  artifact_type: software_product
  top_1_percent_traits: [correctness, robustness, architecture, UX, performance, security, maintainability]
  common_amateur_failures: [feature_count_without_flow, fragile_state, no_error_states, untested_integration, inaccessible_ui]
  hidden_quality_dimensions: [failure_recovery, latency_feel, information_architecture, operability]
  evaluation_traps: [counting_features, screenshot_exists, happy_path_only]
  minimum_evidence: [tests_or_scenarios, browser_or_runtime_check, diff_summary, rollback_point]
  useful_metrics: [P0_closed, scenario_pass_rate, latency_budget, visual_regression_notes]
  qualitative_rubric: [task_flow_coherence, edge_states, visual_hierarchy, maintainability]
  red_team_questions: [What breaks on empty data?, What happens offline?, What user action is irreversible?]
  breakthrough_operators_to_prioritize: [change_unit_of_optimization, exploit_tooling_affordance, bottleneck_inversion]
  final_delivery_standard: "Runs, demonstrates key flows, handles edge states, and has evidence-backed quality."
```
