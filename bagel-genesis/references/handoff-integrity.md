# Handoff Integrity Protocol

Use whenever an Orchestrator, worker, Runtime Doctor, or nested helper is replaced. V2 continuation is replace-not-compact, so handoff quality is the recovery boundary.

## Handoff Capsule

Write handoffs under `.bagel/handoffs/` or `.bagel/supervisor/handoffs/`:

```yaml
current_state: {}
open_risks: []
next_action: {}
last_git_ref: "abc123"
handoff_validation_report:
  handoff_ref: ".bagel/handoffs/orch-001.yaml"
  valid: true
  missing_fields: []
  state_hash_matches: true
  last_action_status: verified
  next_action_safe_to_start: true
```

The parent validates the handoff before dispatching a fresh child. A new Orchestrator must not continue from a vague narrative summary.

## Bounded Action Idempotency

Every bounded action needs an action record:

```yaml
action_id: ACT-20260616-001
idempotency_key: "sha256(task_id + git_ref_start + allowed_paths + intent)"
status: planned | running | committed | verified | abandoned
owner_agent_id: agent-impl-001
started_at: "ISO-8601"
completed_at: null
git_ref_start: "abc123"
git_ref_end: null
side_effects:
  files_changed: []
  commands_run: []
  external_resources: []
replay_or_resume_policy:
  safe_to_retry: false
  retry_requires_check: []
```

Run:

```bash
python scripts/resume_integrity_check.py <project-root>
```
