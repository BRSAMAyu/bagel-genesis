# Ops SRE Expert Pack

```yaml
expert_pack:
  artifact_type: ops_sre
  top_1_percent_traits: [observe, diagnose, staging_fix, runbook, canary, rollback, postmortem]
  common_amateur_failures: [prod_mutation_without_approval, no_rollback, no_logs, unbounded_restart_loop]
  hidden_quality_dimensions: [blast_radius, alert_fatigue, graceful_degradation]
  evaluation_traps: [service_started_once, green_log_line, no_canary]
  minimum_evidence: [environment_classification, logs, runbook_ref, rollback_plan]
  useful_metrics: [error_rate_delta, recovery_time, alert_count, canary_health]
  qualitative_rubric: [safety, observability, reversibility]
  red_team_questions: [What is production?, What can be observed only?, How do we rollback?]
  breakthrough_operators_to_prioritize: [constraint_as_feature, exploit_tooling_affordance, bottleneck_inversion]
  final_delivery_standard: "Production changes require approval; staging fixes are observable, reversible, and documented."
```
