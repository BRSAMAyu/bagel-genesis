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
| `gameable_metric_paired` | When the evaluation spec contains a gameable retrieval headline metric (hit@1/precision@1/exact-match@1), it is paired with at least one robustness/ranking metric (MRR/nDCG/MAP/recall@k/held-out/generalization). A gameable headline cannot be the sole quality signal. |
| `statistical_rigor_paper_grade` | For research runs, every confirmatory/headline claim passes `scripts/statistical_rigor_check.py`: a declared seed floor ≥3 with enough registered seeds; per-claim error bars (aggregation + dispersion type + value); a real significance test, numeric p-value, effect size, and effect-size metric for any baseline comparison; a multiple-comparison correction once >1 comparative claim exists; declared baseline parity (tuning/compute/data, asymmetry justified); a compute budget (accelerator + total runs); and `meets_practical_significance` so a stat-sig-but-trivial effect cannot be headlined. Encodes the top empirical desk-reject reasons as mechanical predicates; exploratory/negative claims and non-research runs are untouched. Verifies shape+consistency of the statistics, not the arithmetic — pair with `metric_recompute` + external referee. |
| `findings_executably_verified` | Every `.bagel/reviews/<REV>.yaml` record passes `scripts/finding_verification_check.py`: a P0/P1 finding may only carry `counts_toward_net_assessment: true` if it has a `reproduction` block whose `result: reproduced`; a `not_reproduced` finding cannot count; `net_assessment: forward` is invalid while any confirmed P0/P1 counts. Under attested mode (`BAGEL_ATTEST_KEY`) a `reproduced` finding must bind to a real attested command whose stdout contains the finding's `expectation` — so a load-bearing defect verdict traces to bytes a command produced, not to reviewer opinion. Converts review from shape-trusted opinion into executably-verified evidence (closes RUN-002 finding 7: a confidently-wrong reviewer P0 that does not reproduce can no longer drive `net_assessment`). |
| `data_hygiene_leakage_free` | For research runs with a confirmatory/headline claim, `scripts/data_leakage_check.py` requires a declared `plan.data_hygiene.test_set_policy`: `preprocessing_scope: all_data` (preprocessing saw the test set) is only allowed with `leakage_audited: true` AND a non-empty `leakage_justification`; model selection must use a validation/train split (never `selection_used: test`); `touch_count` must be an int and any value >1 needs justification; `leakage_audited` must be true (an explicit train/test-overlap + pretraining-contamination audit); and every exclusion must be `preregistered: true` (outcome-independent) or explicitly `posthoc: true`. Encodes the three classic integrity rejects — all-data preprocessing, selecting on test, and outcome-dependent exclusions — that sink a paper even when the statistics are impeccable. Honest limit: it verifies the run *declares* leakage-free handling and that the declaration is internally consistent; it cannot read the training data to prove no overlap exists (that audit is the researcher's + referee's job). |
| `reproducibility_checklist_complete` | For research runs with a confirmatory/headline claim, `scripts/reproducibility_checklist_check.py` requires `.bagel/research/reproducibility-checklist.yaml` to answer every NeurIPS/ICML-style item (code/datasets/seeds/hyperparameters/compute/error-bars/significance/train-test-split/limitations/broader-impacts/assets) with `yes|no|na`; a `yes` needs a non-empty `evidence_ref` (no empty boxes); hard-required items (seeds, compute, error bars, significance, train/test split, limitations) cannot be `no`/`na`; and every mechanical `yes` is cross-checked against the real artifact (seeds≥3 in the plan, compute_budget present, claim statistics carry dispersion + p_value, test_set_policy exists) so the checklist can never be greener than the work. Honest limit: items with no mechanical artifact (limitations/impacts/license prose) are checked for presence of an answer + ref, not substance — that judgment is the Research Referee's. |
| `discovery_sandbox_clean` | For `autonomous_researcher` runs with `objective: discovery` (the Explorer), `scripts/discovery_sandbox_check.py` enforces two properties. **Zero blast radius:** every changed file (git porcelain when available, else the platform file-write attestation log) must fall under `discovery_contract.sandbox_path` (default `.bagel/explore/`) or `.bagel/` — a discovery run that modifies the user's real project tree fails, so it cannot screw up the project by construction. **Report integrity:** every idea in `.bagel/explore/discovery-report.yaml` must be self-validated — a non-empty `novelty_record.what_is_new`, a `probe` with a real `result`, a `council_verdict`, and a `falsifiable_next`; a bare-assertion idea cannot enter the deliverable. Honest limit: the blast-radius check sees the changed-file set, not intent (it proves the sandbox was respected, not that the work was good); with neither git nor attestations available it degrades to a WARN rather than a false pass. |
| `optimization_integrity_clean` | For `autonomous_researcher` runs with `objective: optimization` (the Optimizer), `scripts/optimization_integrity_check.py` enforces the leaderboard-honesty contract once Build has started. **Target locked:** `.bagel/research/optimization-target.yaml` must declare each benchmark, metric, goal (maximize\|minimize), and a numeric `current_baseline` before any gain is claimed — you cannot move a bar you never wrote down. **Selection on validation, never test:** every kept variant in `.bagel/research/optimization-log.yaml` must carry a `selection_split` in {validation, val, dev, train} — a kept variant selected on `test` turns the benchmark into a training signal and fails. **Honest denominator + held-out headline:** once a gain is claimed, every variant tried must be logged (not just the winner), the headline must be `claim_type: confirmatory` evaluated on `test` (not the validation split it was selected on), must beat the locked `current_baseline` in the declared direction, and must be attributed by an `ablation_ref`/`ablation` tying the gain to the specific change; ≥3 variants shopped without a declared multiple-comparison correction warns. Composes with the full Mode-1 floor (statistical_rigor + data_leakage + reproducibility_checklist + R3/R4 referee), which all fire on the confirmatory headline. Honest limit: it proves the optimization *protocol* was honest (locked target, val-selection, logged denominator, held-out confirmation, attribution); it cannot by itself prove the test set never leaked into training — that is the `data_leakage` audit's job, which it composes with rather than duplicates. |
| `expert_decision_present` | High-impact choices have a Principal Expert `expert_decision` with selected direction, rejected alternatives, thesis, confidence, reversibility, evidence, uncertainty, kill criteria, and next action. |
| `roi_controller_positive_or_switched` | Per-cycle value accounting shows user-relevant value; low/negative ROI streaks trigger strategy switch, scope shrink, breakthrough search, or budget stop. |
| `supervisor_boundary_respected` | Supervisor action logs contain only alignment, heartbeat, respawn, hard-stop, resume, or user-proxy actions; no implementation/debug/test/browser work. |
| `supervisor_role_guard_passed` | Nested Supervisor action logs include `role_guard` on every action, affirm current skill overrides stale state, record no task-size exemption, and include spawn/respawn proof for the inner Orchestrator. |
| `dispatch_envelope_valid` | Every dispatch envelope passes read/write path, context, lock, role-boundary, and branch/worktree preflight before the worker starts. |
| `emergency_stop_preserves_state` | Emergency stop writes STOP_REQUESTED, captures git status, preserves changes, writes recovery instructions, and performs no destructive reset. |
| `liveness_current` | Active long-running BAGEL runs have a fresh heartbeat or telemetry timestamp. `scripts/liveness_check.py` fails when the newest heartbeat/telemetry is older than 2× the loop/heartbeat interval. This is a local gate; full enforcement still needs an external watchdog/loop driver. |
| `requirement_coherence_checked` | The requirement set has been checked for joint satisfiability against the contradiction families (CAP/latency-bandwidth/strong-vs-eventual-merge/real-time-vs-offline/cost-vs-capability). Every matched family has either no match, or a recorded human decision in `.bagel/ledger.yaml` `human_decisions:` dropping/relaxing a requirement or accepting a tradeoff. "你看着办" is not a resolution. Fails the cycle if a matched contradiction has no recorded human decision. See SKILL.md Requirement Coherence Check. |
| `premise_falsifiable` | For research/theory/benchmark artifact types, the hypothesis fills the research-experiment §1 template with a concrete metric AND a concrete falsifier, recorded in `.bagel/expert/problem-framing.yaml`, after at most one documented reframe attempt. An unfalsifiable premise (no operational definition, no experimental criterion that could disprove the claim) fails the gate and routes to 🔴 CHECKPOINT S1 hard-stop — it must NOT be resolved by proxy-substitution. |
| `named_dependency_real_protocol` | When a user prompt names an external dependency (database/cache/API/gateway), the local runnable chain exercises that dependency's real client and network protocol — not an in-process substitute that swaps the protocol (e.g. a HashMap for a named Redis dependency). The Runtime Doctor repair evidence in `.bagel/evidence/` records the provisioning command and a healthcheck proving the real client connects. In-process stubs for named external services fail this gate. See SKILL.md Runtime Doctor repair primitives. |
| `premise_fidelity_proven` | When problem framing records a `premise_fidelity` block, the agent did not silently substitute a proxy for the user's claim. proxy_used=true requires user_authority_ref; core_claim_preserved=false requires checkpoint_required=true. An unfalsifiable premise cannot be converted into a proxy experiment without explicit labeling. See research-experiment.md §1 premise fidelity record. |
| `dataset_integrity_checked` | For empirical dataset-based claims, `.bagel/expert/dataset-integrity.yaml` exists with train/val/test split hashes, a split_disjointness_check_ref, tuning_used_test_set=false, and justified preprocessing_fit_on. See references/dataset-integrity.md. |
| `research_mode_declared` | Research/experiment/benchmark/theory and data-analysis-with-empirical-claims runs declare `.bagel/constitution.yaml research_autonomy.mode` as `protocol_execution` or `autonomous_researcher`, with a researcher intent lock and permission model. `protocol_execution` must set experiment-design, hypothesis, primary-metric, and dataset/split mutation permissions to false. See `references/research-governance.md`. |
| `experiment_plan_preregistered` | Before research Build, `.bagel/research/experiment-plan.yaml` exists with `research_experiment_plan_v1`, the selected research mode, objective, hypotheses, falsifiable metric/falsifier, primary metric, decision threshold, practical significance threshold, baselines, controls, seeds, analysis plan, and stopping rule. |
| `experiment_event_log_current` | Once research Build starts, `.bagel/research/experiment-log.yaml` exists with `research_experiment_log_v1` and non-empty events for runs, repairs, design amendments, analyses, claims, and negative results. In `protocol_execution`, any protected design change requires `authority_ref`. |
| `confirmatory_claim_not_posthoc` | `.bagel/research/claim-evidence.yaml` confirmatory claims are not post-hoc, cite hypothesis/metric/run refs, have non-missing ablation and reproducibility status, and are allowed in headline. Post-hoc analyses must remain exploratory until rerun under a fresh preregistered plan. |
| `production_data_hardstop_respected` | When source/config/dispatch scans detect production-data/credential signals (cloud keys, non-localhost production connection strings, prod-host patterns, cloud-SDK usage with region), a recorded hard-stop acknowledgment must exist in `.bagel/ledger.yaml` human_decisions:. Otherwise the cycle fails — the agent must remove the production connection (use a local stub per Runtime Doctor) or record the 🔴 CHECKPOINT · S1 HARD-STOP acknowledgment. See scripts/production_surface_check.py. |
| `no_hardcoded_secrets` | Generated source/config must not contain hardcoded secret/key patterns (AWS AKIA keys, GitHub PATs, private key blocks, Stripe live keys, Slack tokens). This fails UNCONDITIONALLY — no acknowledgment can clear it, because a committed secret is an irreversible leak. The agent must remove the secret and load it from an environment variable or secrets manager. See scripts/production_surface_check.py. |
| `non_functional_quality_checked` | For UI/software artifacts, `.bagel/expert/non-functional-quality.yaml` declares baseline metrics for accessibility (contrast/keyboard/screen-reader), responsive (breakpoints), and performance (latency/throughput). A >10% regression from baseline fails the cycle. The record is mandatory once Build starts + an iteration completes. See scripts/non_functional_quality_check.py. |
| `evidence_has_minimum_content` | Cited evidence files in progress-deltas.yaml must be ≥50 bytes — a real evidence artifact (command output, screenshot, benchmark, rendered file) is never smaller. Stub/placeholder evidence files are caught. See scripts/flywheel_check.py validate_progress_deltas. |
| `execution_fidelity_satisfied` | The anti-skip-if-absent gate (`scripts/execution_fidelity_check.py`). Every *other* validator polices the shape of work that was done, not whether the designed work happened at all, so an agent that never engages the machinery passes vacuously. This gate inverts that at the consequential moments — where a CLAIM implies an artifact, the artifact's *absence* is a failure, not a skip: (A) a research run with `run_status: complete` must have ≥1 confirmatory/negative_result claim, a `statistics` block on every confirmatory claim, ≥1 Research Referee record (`.bagel/reviews/REF-*.yaml`), and (if a confirmatory/headline claim exists) the reproducibility checklist; (B) any progress-delta claiming an R3/R4 `independent_assessment` requires `runtime_capabilities.true_subagents.observed: true` with proof; (C) a `complete` medium+-risk run on a subagent-capable platform must record ≥1 dispatched agent. Honest limit: it makes "going through the motions" fail loudly at turn end (the Stop hook runs the suite) rather than hide behind a green check — but it cannot compel an agent to continue; an agent can still stop early with `run_status` unset, which correctly reads as incomplete. The willingness-independent forcing function is the control-plane PreToolUse block (see Enforcement Model). |
| `control_plane_first` | OPT-IN action-boundary forcing function (`attest_fileop.py` PreToolUse Write/Edit, enabled by `BAGEL_REQUIRE_CONTROL_PLANE=1`). While enabled and `.bagel/constitution.yaml` does not yet exist, the agent may not write product/source files — only bootstrap paths (`.bagel/`, `status.md`, `.git*`). This converts "the agent ignored the skill and just wrote code" from a silent pass into a *blocked action with an instruction*, at the tool boundary, independent of the agent's willingness to read SKILL.md. Off by default so it never surprises a non-BAGEL repo; a no-op once the control plane exists. This is the only enforcement in the suite that does not depend on the agent choosing to engage. |

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
| `gameable_metric_paired` | `evaluation_quality_check.py` |
| `findings_executably_verified` | `finding_verification_check.py` |
| `expert_decision_present` | `expert_strategy_check.py` |
| `requirement_coherence_checked` | `expert_strategy_check.py` |
| `premise_falsifiable` | `expert_strategy_check.py` |
| `premise_fidelity_proven` | `expert_strategy_check.py` |
| `named_dependency_real_protocol` | `expert_strategy_check.py` |
| `dataset_integrity_checked` | `expert_strategy_check.py` |
| `research_mode_declared` | `research_governance_check.py` |
| `experiment_plan_preregistered` | `research_governance_check.py` |
| `experiment_event_log_current` | `research_governance_check.py` |
| `confirmatory_claim_not_posthoc` | `research_governance_check.py` |
| `statistical_rigor_paper_grade` | `statistical_rigor_check.py` |
| `data_hygiene_leakage_free` | `data_leakage_check.py` |
| `reproducibility_checklist_complete` | `reproducibility_checklist_check.py` |
| `discovery_sandbox_clean` | `discovery_sandbox_check.py` |
| `optimization_integrity_clean` | `optimization_integrity_check.py` |
| `execution_fidelity_satisfied` | `execution_fidelity_check.py` |
| `control_plane_first` (opt-in) | `attest_fileop.py` PreToolUse (`BAGEL_REQUIRE_CONTROL_PLANE=1`) |
| `production_data_hardstop_respected` | `production_surface_check.py` |
| `no_hardcoded_secrets` | `production_surface_check.py` |
| `non_functional_quality_checked` | `non_functional_quality_check.py` |
| `evidence_has_minimum_content` | `flywheel_check.py` |
| `roi_controller_positive_or_switched` | `roi_check.py` |
| `supervisor_boundary_respected` | `supervisor_boundary_check.py` |
| `supervisor_role_guard_passed` | `supervisor_boundary_check.py` |
| `dispatch_envelope_valid` | `dispatch_envelope_check.py` |
| `emergency_stop_preserves_state` | `emergency_stop_check.py` |
| `liveness_current` | `liveness_check.py` |

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
