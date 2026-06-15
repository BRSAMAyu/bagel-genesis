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
| `flywheel_integrity_passed` | `python scripts/flywheel_check.py <project-root>` passes after the cycle's delta/status/state updates. This bundles the no-regression, evidence, review-registry, budget, bar-raise, and flat-climbing checks. |
| `no_regression_vs_green_floor` | Excellence-loop iteration N does not complete if any metric value dropped below its last-known-good value from a prior completed iteration. The floor is recorded in `.bagel/state.yaml.excellence.green_floors` (quick) or equivalent full-mode state. Fails if any component regressed, even if current target set is all-green. |
| `metric_delta_has_evidence_artifact` | Each forward/lateral/backward metric delta in progress-deltas.yaml cites a saved artifact/output path containing actual command output, screenshot, benchmark output, rendered file, or checksum, not just the command string. Prevents hallucinated deltas. |
| `review_level_consistent_with_registry` | The recorded review_level (R0-R4) is consistent with `.bagel/agents/registry.yaml`: R3+ requires ≥2 distinct agent contexts active in the review cycle. If only one context was active, max claimable is R1. Prevents overstating independence. |
| `bar_raise_has_value_class` | Each new/raised target has a `why_class` from the canonical set: `defect_prevention`, `adversarial`, `growth_dimension`, `astonishing_completeness`, `stronger_evidence`, or `churn`. `churn` requires R3+ reviewer acceptance. The canonical set is defined in `scripts/flywheel_check.py` BAR_RAISE_VALUE_CLASSES and must not diverge. Prevents busywork disguised as bar-raising. |

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
