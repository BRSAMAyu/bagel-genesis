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
| `bar_raise_has_judgment` | Directional bar-raises have `judgment_passed: true` and a valid `.bagel/decisions/judgment-*.yaml`, or a narrow `judgment_skipped_reason` for non-directional mechanical tightening. Prevents standards from being raised toward low-taste directions. |
| `active_evaluation_spec_present` | Before Build or any iteration work, an active evaluation spec exists with metrics and/or qualitative rubric, completion_rule, decision_use, and anti_gaming_note for numeric metrics. Prevents agents from building without knowing how quality will be judged. |
| `task_queue_excludes_control_plane` | User-facing task_queue contains deliverable work only; `.bagel/` setup, constitution, STATUS, lint, and governance work live in control-plane ledgers/dispatch records and do not count as product progress. |
| `iteration_count_not_bypassed` | `run_status=complete` is valid only when `iterations_completed >= max_iterations` plus final delivery gates pass. Completing the initially listed goals counts as one iteration, not final completion. |
| `supervisor_layer_bound` | On Claude Code/Codex with true subagents, the main session runs as Supervisor, `.bagel/supervisor/heartbeat.yaml` and `resume-capsule.md` exist, and a current Orchestrator agent/session is recorded. |
| `resume_capsule_current` | A long run has `.bagel/supervisor/resume-capsule.md` pointing to STATUS, state, constitution, current context capsule, and exactly one next action. It excludes raw transcripts and reasoning. |
| `context_tree_budget_policy_present` | Nested Supervisor runs declare `context_budget.root_supervisor_soft_max_tokens <= 200000`, `non_root_policy: replace_not_compact`, and a replacement threshold. Non-root agents continue by handoff + replacement, not routine self-compaction. |
| `project_under_version_control` | Before the first file modification of an autonomous run, `git rev-parse --is-inside-work-tree` succeeds in the working folder, OR the user explicitly approved `git init` and a baseline commit exists. Without version control, rollback and branch isolation are impossible, so autonomous write work must not start. See `references/git-governance.md` Step 0. |
| `runtime_capability_observed_with_proof` | R3/R4 review, scheduled resume, hooks, and visual claims use `runtime_capabilities.capabilities.<name>.observed: true` plus an existing `proof_ref`; adapter claims alone do not count. |
| `handoff_validation_passed` | Replacement/resume handoffs include current state, open risks, next action, last git ref, and a validation report proving the next action is safe to start. |
| `action_idempotency_safe` | Every bounded action records an idempotency key, side effects, git refs, and retry policy; duplicate keys are retry-safe or fail. |
| `evidence_replay_integrity_passed` | Runnable evidence records include command/cwd/git_ref/exit_code/stdout/stderr hashes/env digest/replay policy, and recorded hashes match files. |
| `governance_budget_respected` | Cycle telemetry proves deliverable deltas appear on schedule and governance share does not repeatedly exceed the configured limit. |
| `scope_delta_within_contract` | Write tasks stay within allowed paths/dependencies/sensitive surfaces, or cite approval/contract/Court evidence. |
| `alignment_freshness_current` | Iteration end, final delivery, user instruction changes, and taste-sensitive direction changes have evidence-backed alignment freshness review. |
| `domain_excellence_model_present` | `.bagel/expert/domain-excellence.yaml` defines what excellent, mediocre, hidden quality, failure modes, and expert review questions mean for this artifact. |
| `problem_framing_locked` | `.bagel/expert/problem-framing.yaml` records stated problem, inferred real problem, considered reframings, chosen framing, and rejected framings before Build. |
| `leverage_map_current` | `.bagel/expert/leverage-map.yaml` identifies bottlenecks and cites the top leverage action used for iteration target selection. |
| `evaluation_critic_passed` | Active evaluation spec includes Evaluation Critic review and metric discrimination checks against bad/strong examples. |
| `expert_decision_present` | High-impact choices have a Principal Expert `expert_decision` with selected direction, rejected alternatives, thesis, confidence, reversibility, evidence, uncertainty, kill criteria, and next action. |
| `roi_controller_positive_or_switched` | Per-cycle value accounting shows user-relevant value; low/negative ROI streaks trigger strategy switch, scope shrink, breakthrough search, or budget stop. |
| `supervisor_boundary_respected` | Supervisor action logs contain only alignment, heartbeat, respawn, hard-stop, resume, or user-proxy actions; no implementation/debug/test/browser work. |
| `supervisor_role_guard_passed` | Nested Supervisor action logs include `role_guard` on every action, affirm current skill overrides stale state, record no task-size exemption, and include spawn/respawn proof for the inner Orchestrator. |
| `dispatch_envelope_valid` | Every dispatch envelope passes read/write path, context, lock, role-boundary, and branch/worktree preflight before the worker starts. |
| `emergency_stop_preserves_state` | Emergency stop writes STOP_REQUESTED, captures git status, preserves changes, writes recovery instructions, and performs no destructive reset. |
| `requirement_coherence_checked` | The requirement set has been checked for joint satisfiability against the contradiction families (CAP/latency-bandwidth/strong-vs-eventual-merge/real-time-vs-offline/cost-vs-capability). Every matched family has either no match, or a recorded human decision in `.bagel/ledger.yaml` `human_decisions:` dropping/relaxing a requirement or accepting a tradeoff. "你看着办" is not a resolution. Fails the cycle if a matched contradiction has no recorded human decision. See SKILL.md Requirement Coherence Check. |
| `premise_falsifiable` | For research/theory/benchmark artifact types, the hypothesis fills the research-experiment §1 template with a concrete metric AND a concrete falsifier, recorded in `.bagel/expert/problem-framing.yaml`, after at most one documented reframe attempt. An unfalsifiable premise (no operational definition, no experimental criterion that could disprove the claim) fails the gate and routes to 🔴 CHECKPOINT S1 hard-stop — it must NOT be resolved by proxy-substitution. |
| `named_dependency_real_protocol` | When a user prompt names an external dependency (database/cache/API/gateway), the local runnable chain exercises that dependency's real client and network protocol — not an in-process substitute that swaps the protocol (e.g. a HashMap for a named Redis dependency). The Runtime Doctor repair evidence in `.bagel/evidence/` records the provisioning command and a healthcheck proving the real client connects. In-process stubs for named external services fail this gate. See SKILL.md Runtime Doctor repair primitives. |
| `premise_fidelity_proven` | When problem framing records a `premise_fidelity` block, the agent did not silently substitute a proxy for the user's claim. proxy_used=true requires user_authority_ref; core_claim_preserved=false requires checkpoint_required=true. An unfalsifiable premise cannot be converted into a proxy experiment without explicit labeling. See research-experiment.md §1 premise fidelity record. |
| `dataset_integrity_checked` | For empirical dataset-based claims, `.bagel/expert/dataset-integrity.yaml` exists with train/val/test split hashes, a split_disjointness_check_ref, tuning_used_test_set=false, and justified preprocessing_fit_on. See references/dataset-integrity.md. |

## Enforcement Model (honest)

Not every predicate has a mechanical validator behind it. Predicates split into two tiers:

**Mechanically enforced** (a script fails the cycle if violated — cannot be talked out of):

| Predicate | Validator |
|---|---|
| `project_under_version_control` | `bagel_run_check.py` |
| `constitution_approved` (alignment floor + Stop Contract) | `bagel_run_check.py` |
| `flywheel_integrity_passed` | `flywheel_check.py` (bundles the checks below) |
| `no_regression_vs_green_floor` | `flywheel_check.py` |
| `metric_delta_has_evidence_artifact` | `flywheel_check.py` |
| `review_level_consistent_with_registry` | `flywheel_check.py` + `bagel_run_check.py` |
| `bar_raise_has_value_class` | `flywheel_check.py` |
| `bar_raise_preceded_by_brainstormers` | `flywheel_check.py` (>= 2 brainstormer_dispatch_ids per bar-raise) |
| `bar_raise_has_judgment` | `flywheel_check.py` |
| `active_evaluation_spec_present` | `bagel_run_check.py` |
| `task_queue_excludes_control_plane` | `bagel_run_check.py` |
| `iteration_count_not_bypassed` | `bagel_run_check.py` |
| `supervisor_layer_bound` | `bagel_run_check.py` |
| `resume_capsule_current` | `bagel_run_check.py` |
| `context_tree_budget_policy_present` | `bagel_run_check.py` |
| `runtime_capability_observed_with_proof` | `bagel_run_check.py` |
| `handoff_validation_passed` | `resume_integrity_check.py` |
| `action_idempotency_safe` | `resume_integrity_check.py` |
| `evidence_replay_integrity_passed` | `evidence_replay_check.py` |
| `governance_budget_respected` | `bagel_telemetry_check.py` |
| `scope_delta_within_contract` | `scope_check.py` |
| `alignment_freshness_current` | `alignment_freshness_check.py` |
| `domain_excellence_model_present` | `expert_strategy_check.py` |
| `problem_framing_locked` | `expert_strategy_check.py` |
| `leverage_map_current` | `expert_strategy_check.py` |
| `evaluation_critic_passed` | `evaluation_quality_check.py` |
| `expert_decision_present` | `expert_strategy_check.py` |
| `requirement_coherence_checked` | `expert_strategy_check.py` |
| `premise_falsifiable` | `expert_strategy_check.py` |
| `premise_fidelity_proven` | `expert_strategy_check.py` |
| `named_dependency_real_protocol` | `expert_strategy_check.py` |
| `dataset_integrity_checked` | `expert_strategy_check.py` |
| `roi_controller_positive_or_switched` | `roi_check.py` |
| `supervisor_boundary_respected` | `supervisor_boundary_check.py` |
| `supervisor_role_guard_passed` | `supervisor_boundary_check.py` |
| `dispatch_envelope_valid` | `dispatch_envelope_check.py` |
| `emergency_stop_preserves_state` | `emergency_stop_check.py` |

**Agent-attested** (the agent records pass/fail based on evidence files, but no script independently re-verifies — these depend on the agent honestly inspecting the cited evidence):

`project_understanding_current`, `evolution_record_present`, `context_fresh_for_dispatch`, `parallel_ownership_safe`, `worker_did_not_merge`, `rollback_point_present_for_risk`, `merge_inputs_clean`, `typed_contracts_present_when_required`, `skeleton_gate_passed_when_required`, `artifact_specific_slice_coverage_present`, `decision_mutations_cleared`, `red_team_blockers_resolved`, `scope_reduction_authorized`, `review_level_satisfied` (the QA-matrix-required-level part).

These agent-attested gates are still mandatory — the agent must check them and record evidence — but they are not independently re-verified by a script. The periodic Independent Flywheel Audit (excellence-loop.md) is the intended backstop: an R3+ reviewer re-checks a sample of agent-attested gates against real repo state. If you need a guarantee that is impossible to self-attest falsely, rely only on the mechanically-enforced set above.

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
