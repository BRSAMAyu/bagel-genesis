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

## Ops event-driven mode (mandatory for ops/SRE runs)

Ops work is event-driven, not iteration-driven. An ops run that cycles through build/iterate without an event trigger burns budget on monitoring theater. Declare the mode explicitly:

```yaml
ops_event_mode:
  mode: observe_only | staging_autofix | production_guarded
  event_trigger:           # what starts real work (not idle monitoring)
    - alert
    - log_anomaly
    - healthcheck_fail
    - deployment_failure
    - user_reported_incident
  idle_policy:             # what to do when no event is active (do NOT invent work)
    if_no_event:
      - update_runbook
      - improve_observability
      - verify_backup
      - no_op_checkpoint    # an explicit idle checkpoint is valid; burning cycles is not
  production_mutation_requires_approval: true
```

### Mode rules

- **observe_only**: detect and document anomalies; do not change any infrastructure. Output is a runbook/diagnosis, not a fix.
- **staging_autofix**: may fix issues in staging/test environments autonomously, with rollback plans and canary checks. Never touches production without escalation.
- **production_guarded**: production changes require explicit approval (🔴 CHECKPOINT hard-stop). Only reversible, observable changes with a tested rollback are candidates.

### Anti-patterns enforced

- **Unbounded restart loop** (`common_amateur_failures`): a service that restarts repeatedly without diagnosis is not "fixed" — it is masking the failure. Cap restart attempts and require a postmortem after the cap.
- **No event, no work**: without an active `event_trigger`, the run must follow `idle_policy` — update runbooks, improve observability, verify backups. It must NOT fabricate incidents to justify iteration cycles.
- **Green log line trap** (`evaluation_traps`): a single successful healthcheck does not prove recovery. Require sustained health (N consecutive healthy checks) and check error-rate delta, not just one green log line.
- **Blast radius**: every ops change declares its blast radius (what systems are affected if it is wrong). `production_guarded` mode changes with unbounded blast radius require Constitutional Court review.
