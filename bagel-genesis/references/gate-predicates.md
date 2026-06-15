# Gate Predicates

Use whenever BAGEL checks readiness, blocks progress, waives a gate, or records completion.

## Required Artifact

Create `.bagel/gates/status.yaml`:

```yaml
gates:
  - id: constitution_approved
    status: pass | fail | not_applicable | waived
    evidence:
      - ".bagel/constitution.yaml (quick) or .bagel/constitution.json (full)"
    checked_at: "ISO-8601"
    checked_by: "orchestrator"
    notes: ""
```

`waived` requires a linked human decision or autonomy-contract clause. `not_applicable` requires artifact-type rationale.

## Core Predicates

| ID | Pass Condition |
|---|---|
| `constitution_approved` | `.bagel/constitution.json` exists and approval/delegation is recorded in `alignment/human-decisions.yaml` |
| `project_understanding_current` | Existing-project work has fresh, scoped `agent_context` for affected paths |
| `evolution_record_present` | Meaningful change has a linked record under `.bagel/evolution/` |
| `context_fresh_for_dispatch` | Required context capsules are fresh or task is a refresh task |
| `parallel_ownership_safe` | Locks, branch/worktree owner, dependencies, and shared-file policy have no unresolved conflict |
| `worker_did_not_merge` | Worker branch/diff is returned for integration; base was not merged by worker |
| `review_level_satisfied` | Required review level from QA matrix is met and residual independence risk is recorded |
| `rollback_point_present_for_risk` | Medium/high/critical changes have a rollback point before merge |
| `merge_inputs_clean` | No stale context, lock overlap, out-of-scope edits, or unverified generated/shared files |
| `typed_contracts_present_when_required` | APIs, data models, AI pipelines, external integrations, or structured claims have typed/schema/contract evidence when applicable |
| `skeleton_gate_passed_when_required` | Software/app artifacts have Ghost Ship or equivalent boot/read/use gate before value filling |
| `artifact_specific_slice_coverage_present` | Slice coverage matches artifact profile: tests, scenarios, citations, continuity checks, examples, or manual evidence |
| `decision_mutations_cleared` | Changes to committed decisions/contracts are approved, migrated, and cascaded before next slice |
| `red_team_blockers_resolved` | No unresolved P0/P1 red-team finding in baseline or final candidate |
| `scope_reduction_authorized` | Any implementation-driven scope reduction passed Constitutional Court and required human approval |

## Detector Rules

- A predicate is checkable only if it names evidence files, commands, or review reports.
- If evidence is unavailable, mark `fail`, not `pass`.
- Replace vague phrases such as "significant change" with a task-local threshold: user-visible behavior, public API, data, architecture, contract, cost, security, privacy, or project intent.
- Replace "when applicable" with artifact profile rules from `references/artifact-types.md`.

## Failure Record

Every failed gate writes:

```yaml
failure:
  gate_id: ""
  blocking_state: ""
  missing_evidence: []
  recovery_options: []
  wake_user_required: false
```
