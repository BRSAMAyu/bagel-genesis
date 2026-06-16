# Telemetry and Context Pressure Protocol

Use every autonomous cycle. V2 measures whether BAGEL is converting time into deliverable value.

## Cycle Telemetry

Write `.bagel/telemetry/cycles.yaml`:

```yaml
cycles:
  - cycle_id: CYCLE-047
    started_at: "ISO-8601"
    ended_at: "ISO-8601"
    phase: Build
    current_iteration: 2
    context_pressure:
      supervisor_estimated_tokens: 42000
      supervisor_soft_max_tokens: 200000
      orchestrator_estimated_tokens: 90000
      token_estimate_is_advisory: true
      orchestrator_context_window_tokens: 128000
      worker_max_estimated_tokens: 48000
      replacement_threshold_percent: 70
      cycles_since_orchestrator_spawn: 0
      dispatches_since_spawn: 0
      reference_full_reads_since_spawn: 0
      handoff_size_bytes: 0
      state_load_failures: 0
      repeated_confusion_events: 0
      stale_context_reports: 0
      replacement_due: true
      replacement_due_reason: token_estimate | cycles_since_spawn | full_reads_exceeded | stale_context | failed_handoff_probe | state_load_failure | confusion_events
      handoff_ref: ".bagel/handoffs/orch-047.yaml"
    budget:
      estimated_tokens_used_this_cycle: 32000
      governance_token_share: 0.22
      product_token_share: 0.78
      reference_reads_count: 3
      subagents_dispatched: 5
    outputs:
      control_plane_delta: true
      deliverable_delta: true
      deliverable_delta_detail:
        changed_paths: []
        git_diff_ref: "abc123"
        artifact_surface_changed: true
        user_visible_or_metric_relevant: true
        evidence_refs: []
      evidence_refs: []
```

Token estimates are advisory unless the platform provides actual counts. Behavioral pressure signals can trigger replacement even when token estimates look safe.

Governance budget defaults:

```yaml
governance_budget:
  max_control_plane_share_per_cycle: 0.30
  first_deliverable_delta_required_by_cycle: 2
  max_cycles_without_deliverable_delta: 2
```

Run:

```bash
python scripts/bagel_telemetry_check.py <project-root>
```
