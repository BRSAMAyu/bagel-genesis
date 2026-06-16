# Orchestration Flow

Use this as the authoritative end-to-end decision map for BAGEL. It answers: what decision is due, who is dispatched, how outputs are merged, where state is recorded, and which script verifies it.

## RUN START (Run Start)

1. Detect runtime capabilities.
   - Dispatch: none.
   - Record: `.bagel/runtime_capabilities.yaml` or `state.yaml.runtime_capabilities`.
   - Verify: `bagel_run_check.py`.
2. Bind loop before Align when autonomy is requested.
   - Dispatch: none.
   - Record: `state.yaml.loop_binding`.
   - Merge rule: P1 native loop first, then P2 harness, only then degraded resume.
   - Verify: `bagel_run_check.py`.

## Align

1. Capture Stop Contract as the first alignment artifact.
   - Record: `constitution.yaml.stop_contract`.
   - Verify: `bagel_run_check.py`.
2. Capture alignment depth, execution strategy, hard-stops, taste source, and innovation ambition.
   - Record: `constitution.yaml`, `ledger.yaml.decisions`.
   - Verify: alignment floor checks in `bagel_run_check.py`.
3. Existing project takeover.
   - Dispatch: Project Cartographer plus >=2 exploration lenses.
   - Record: `.bagel/context.yaml`, `.bagel/evidence/baseline/manifest.yaml`.
   - Merge rule: resolve explorer contradictions before writing context.
   - Verify: `bagel_run_check.py`.
4. Breakthrough or differentiated innovation.
   - Dispatch: Product Visionary with required lenses.
   - Record: `.bagel/innovation/ledger.yaml`.
   - Merge rule: concept candidates are not adopted until Judgment Council evaluates them.
   - Verify: `bagel_memory_check.py`.
5. Innovation survivor selection.
   - Dispatch: >=3 Judgment Councilors.
   - Record: `.bagel/decisions/judgment-<id>.yaml`.
   - Merge rule: strong_no veto; >=2 strong_yes and no no/strong_no passes; otherwise disputed.
   - Verify: `bagel_memory_check.py` for ledger presence; `bagel_run_check.py` for final state where applicable.
6. Lock constitution.
   - Dispatch: Constitutional Court only if identity/scope/hard-stop changes are proposed.
   - Record: `constitution.yaml`, `ledger.yaml`.
   - Verify: gate predicates.
7. Separate control plane from deliverable.
   - Dispatch: none.
   - Record: `state.yaml.task_queue` must contain user deliverable work only; BAGEL setup lives in control-plane lanes/ledger.
   - Merge rule: `.bagel/` artifacts enable autonomy but are not the product.
   - Verify: `bagel_run_check.py`.

## Build

1. Start or refresh the current iteration.
   - Dispatch: Evaluation Architect.
   - Record: `.bagel/iterations/ITER-NNN.yaml` or `state.yaml.iterations`; `state.yaml.evaluation`.
   - Merge rule: no deliverable implementation begins until the target set has decision-useful metrics/rubrics.
   - Verify: `bagel_run_check.py`, `flywheel_check.py`.
2. Select next slice.
   - Dispatch: none by default if the evaluation spec already exists; otherwise Evaluation Architect first.
   - Merge rule: use EV ranking; if a candidate has `judgment_passed: true`, use taste-adjusted EV threshold.
   - Record: `state.yaml.task_queue` with `lane_type: deliverable`.
3. Implement.
   - Dispatch: Implementer.
   - Record: changed artifact files and worker handoff.
   - Verify: project tests/checks.
4. Runtime/tooling failure.
   - Dispatch: Runtime Doctor after the first failed setup/build/test/verifier command or missing tool diagnosis.
   - Merge rule: Runtime Doctor can repair reversible tooling but cannot lower gates or change product behavior broadly.
   - Record: command evidence, repair handoff, reusable lesson candidate.
   - Verify: rerun the failed command or record hard-stop boundary.
5. Review.
   - Dispatch: Spec Reviewer / Code Quality Reviewer / Independent Reviewer per risk.
   - Merge rule: required review level must pass; same-session review cannot claim R3.
   - Record: `.bagel/reviews/`.
   - Verify: `flywheel_check.py`.
6. Record progress.
   - Record: `.bagel/evidence/progress-deltas.yaml`, `.bagel/STATUS.md`.
   - Verify: `flywheel_check.py`.
7. Recovery if a gate fails.
   - Dispatch: Independent diagnosis as needed.
   - Merge rule: recovery ladder; hard-stops only for true boundaries.
   - Record: recovery log plus lesson memory if reusable.
   - Verify: `bagel_memory_check.py`.

## Polish And Excellence

1. Current target set not green.
   - Dispatch: bounded implement/review cycle.
   - Record: progress deltas.
   - Verify: `flywheel_check.py`.
2. Current target set all-green.
   - Dispatch: Evaluation Architect to draft the next iteration evaluation spec.
   - Dispatch: >=2 Brainstormers with distinct lenses.
   - Dispatch: >=3 Judgment Councilors for bar-raise direction.
   - Merge rule: Judgment Council veto/pass/disputed.
   - Record: completed iteration, `.bagel/evidence/bar-raises.yaml` with `brainstormer_dispatch_ids` and `judgment_ref` or `judgment_skipped_reason`.
   - Verify: `flywheel_check.py`.
3. Three lateral cycles.
   - Dispatch: Red-Team Oracle for why stuck, Brainstormer for alternatives, Judgment Council for strategy switch.
   - Merge rule: strong_no blocks a switch; passed switch updates strategy; disputed records more evidence needed.
   - Record: `state.yaml.excellence`, `.bagel/decisions/`.
   - Verify: `flywheel_check.py` and `bagel_memory_check.py` if recovery occurred.
4. Breakthrough ambition plus plateau.
   - Dispatch: Product Visionary again before declaring diminishing returns.
   - Record: innovation ledger.
   - Verify: `bagel_memory_check.py`.

## Final Delivery

1. Candidate final artifact.
   - Dispatch: Spec Reviewer, Code Quality Reviewer, Red-Team Oracle.
   - Merge rule: P0/P1 blocks; unresolved positive-EV P2 blocks final unless explicitly accepted.
   - Record: reviews and final diff summary.
2. Final Judgment Council.
   - Dispatch: >=3 Judgment Councilors.
   - Merge rule: any strong_no blocks delivery; >=2 strong_yes and no no/strong_no passes; otherwise disputed and not final.
   - Record: `.bagel/decisions/judgment-final.yaml`.
   - Verify: `bagel_run_check.py`.
3. Curator briefing.
   - Dispatch: User Alignment Curator.
   - Record: `.bagel/STATUS.md`, optional HTML dashboard, final-diff summary links.
4. Final validators.
   - Run: `bagel_run_check.py`, `flywheel_check.py`, `bagel_memory_check.py`.
   - Merge rule: all must pass or the run is not complete.

## RUN END (Run End)

1. If complete: write final briefing, leave loop teardown note, and stop.
2. If budget/token exhausted: write resume checkpoint and set `waiting_for_capacity`.
3. If hard-stop: set `blocked_hard_stop`, record decision needed, and continue only safe independent lanes if available.

There is no other run-end path.
