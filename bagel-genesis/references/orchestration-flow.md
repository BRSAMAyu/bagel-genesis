# Orchestration Flow

Authoritative V3.1 end-to-end execution map. It defines phase, required dispatches, durable records, merge rules, and validators.

## RUN START

1. **Runtime capability detection**
   - Record: `.bagel/runtime_capabilities.yaml` or `state.yaml.runtime_capabilities`.
   - Verify: `runtime_proof_check.py`, `bagel_run_check.py`.
2. **Pre-boot initialization**
   - Allowed Supervisor actions only: create minimal `.bagel/` directories, write initial state, write initial heartbeat, write bootstrap role guard marker.
   - Forbidden: product edits, tests, runtime debug, dependency install.
   - Record: `.bagel/supervisor/orchestration-ledger.yaml` with `bootstrap_complete: true`.
   - Verify: `supervisor_boundary_check.py`.
3. **Supervisor binding**
   - Dispatch: main context remains Supervisor; spawn a fresh Orchestrator when true subagents exist.
   - Record: heartbeat, resume capsule, current Orchestrator id/session.
   - Verify: `bagel_run_check.py`, `supervisor_boundary_check.py`.
4. **Loop binding in `align_protection` mode**
   - Loop may bind before Stop Contract only to protect Align/Resume.
   - Build/Iterate remains forbidden until Stop Contract and build unlock gates pass.
   - Verify: `bagel_run_check.py`.
5. **BAGEL worth-it check**
   - Record: `.bagel/expert/bagel-worth-it.yaml`.
   - Output: `recommended_mode` and `expert_layer_mode` (`off|lite|standard|full`).
   - Verify: `roi_check.py`.

## ALIGN / CALIBRATE

1. **Stop Contract first**
   - Capture max iterations/budget, hard-stops, deadline, morning expectation.
   - Build may not start without it.
   - Verify: `bagel_run_check.py`.
2. **Alignment depth and run mode**
   - Capture alignment depth, execution strategy, taste source, innovation ambition, review honesty mode.
   - Verify: alignment floor in `bagel_run_check.py`.
3. **Existing-project cartography if needed**
   - Dispatch: Project Cartographer plus artifact-specific explorers.
   - Record: `.bagel/context.yaml`, baseline evidence manifest.
   - Verify: `bagel_run_check.py`.
4. **Domain Excellence Model**
   - Dispatch: Domain Expert if full/standard; Orchestrator may create compact lite model only in quick/lite mode.
   - Record: `.bagel/expert/domain-excellence.yaml`.
   - Verify: `expert_strategy_check.py`, `alignment_freshness_check.py`.
5. **Problem Framing**
   - Record stated problem, inferred real problem, reframings, chosen framing, rejected framings.
   - Verify: `expert_strategy_check.py`.
6. **Leverage Map v0**
   - Identify bottlenecks and top leverage action.
   - Verify: `expert_strategy_check.py`.
7. **Evaluation Architect**
   - Dispatch: Evaluation Architect.
   - Record: active evaluation spec.
   - Verify: `bagel_run_check.py`.
8. **Evaluation Critic**
   - Dispatch: Evaluation Skeptic or Evaluation Critic role.
   - Require bad/strong metric discrimination and anti-gaming review.
   - Verify: `evaluation_quality_check.py`.
9. **Innovation / Breakthrough Search**
   - If ambition is `breakthrough`, dispatch Product Visionary and Innovation Strategist.
   - Require operators, competing theses, candidates, cheap probes.
   - Verify: `expert_strategy_check.py`, `bagel_memory_check.py`.
10. **Expert Strategy Council**
   - Dispatch real council agents. Required: Domain Expert, Evaluation Skeptic, User Proxy. Add Systems Architect/Risk Officer/Innovation Strategist when architecture, high-risk, or breakthrough.
   - Record each `expert_council_verdict` and dispatch ids.
   - Verify: `expert_strategy_check.py`.
11. **Principal Expert locks initial strategy**
   - Dispatch: Principal Expert.
   - Record: `expert_decision_v1` under `.bagel/expert/strategy-decisions/`.
   - Verify: `expert_strategy_check.py`.
12. **Build unlock gate**
   - Requires Stop Contract, evaluation, Evaluation Critic, required expert artifacts for the selected `expert_layer_mode`, dispatch envelope validation, and loop phase switch to `autonomous_build`.

## BUILD

1. **Dispatch envelope validation**
   - Record: `.bagel/agents/dispatches/*.yaml`.
   - Dispatch records use `lane_type: deliverable` for user artifact work and `control_plane` for governance/tooling work.
   - Verify: `dispatch_envelope_check.py`.
2. **Implementer / Runtime Doctor / Reviewer**
   - Implementer writes bounded deliverable work.
   - Runtime Doctor handles setup/tool/verifier failures.
   - Reviewers verify according to risk and review honesty mode.
3. **Evidence protocol**
   - Commands, screenshots, benchmarks, reviews, and probes cite replayable evidence or constrained non-replayable reasons.
   - Verify: `evidence_replay_check.py`.
4. **Deliverable delta**
   - User artifact changes must be non-control-plane and evidence-backed.
   - Verify: `deliverable_delta_check.py`.
5. **Scope delta**
   - Derive touched paths from git diff/untracked files, not self-report.
   - Verify: `scope_check.py`.
6. **Progress delta**
   - Record forward/lateral/backward delta with independent assessment.
   - Verify: `flywheel_check.py`.
7. **ROI value accounting**
   - Split hard value and soft value. Soft-only streaks force strategy change.
   - Verify: `roi_check.py`.
8. **V3.1 check**
   - Run `scripts/bagel_v3_check.py`.

## ITERATE

1. Refresh leverage map when bottleneck changes or cycles go lateral.
2. Refresh evaluation when target set, artifact type, or quality definition changes.
3. Evaluation Critic re-checks changed metrics.
4. Expert Strategy Council runs for high-impact target/strategy changes.
5. Principal Expert selects next target set with `expert_decision_v1`.
6. Execute bounded cycle through dispatch envelopes.
7. Record iteration value, evidence, ROI, and lessons.
8. Bar-raise, strategy switch, breakthrough probe, or continue based on evidence.

## FINAL / PAUSE

This is the **Final Delivery** and pause path.

1. Final evidence replay.
2. Expert final decision by Principal Expert.
3. Judgment Council if taste-sensitive.
4. Curator briefing and optional HTML dashboard.
5. Emergency stop, hard-stop, complete, or resume state.

There is no other run-end path.

## RUN END

Run End is complete, waiting for capacity, emergency stopped, or blocked hard-stop. No other terminal state is valid.
