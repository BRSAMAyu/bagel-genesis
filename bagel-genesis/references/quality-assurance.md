# Quality Assurance and Correctness

Use this to keep long autonomous work correct, robust, and self-correcting.

## Principle

Long unattended runs optimize for verified forward progress: stability and correctness without idle waiting. Fast broken work is bad, but premature stopping is also failure when useful autonomous work remains.

## Run Modes

Set `.bagel/run_mode.yaml`:

```yaml
run_mode:
  mode: interactive_fast | balanced | unattended_stable
  user_presence: online | intermittently_available | asleep_or_absent
  risk_tolerance: ambitious | high | medium | low
  max_parallel_write_agents: 1
  required_review_level: strict
  default_if_unspecified: unattended_stable
```

If the user is absent or asks for overnight/multi-day autonomy, default to `unattended_stable`. If the user is present and explicitly prioritizes speed, use `interactive_fast`. Otherwise use `balanced`.

### interactive_fast

Use when user is present and wants speed.

- More parallel exploration allowed.
- Small reversible code tasks may merge after normal checks.
- User can resolve ambiguities quickly.
- Still require locks and merge queue.

### balanced

Default mode.

- Parallelize path-disjoint tasks.
- Require spec and code review for user-facing or shared code.
- Require rollback point for medium-risk changes.

### unattended_stable

Use when user is absent, sleeping, or wants maximum reliability.

- Prefer sequential integration even if parallel exploration is allowed.
- Keep write parallelism low.
- Require R3/R4 review for all behavior changes. On Claude Code and Codex, prefer a real subagent (Task tool / Codex subagent) to satisfy R3 so high-risk behavior changes can be reviewed and merged without idling. If R3 is genuinely unavailable, do not merge that lane; isolate it, keep working on safe independent positive-EV tasks, and wake the user only when no useful autonomous path remains.
- Require stronger verification before merge.
- Avoid broad refactors, dependency upgrades, migrations, and shared-file edits unless necessary for the agreed goal or explicitly preapproved by the autonomy contract.
- Continue progress aggressively through bounded implementation, local verifier creation, tests, docs, experiments, isolated improvements, recovery, and review loops.

When the user explicitly delegates long-run autonomy, `unattended_stable` is not a passive or minimal mode. It is the high-reliability autonomous mode: use platform-native loops/subagents, self-provision missing local verification, and keep working until the completion and excellence horizons pass or the autonomy contract requires a pause.

## Autonomous Momentum

When long-run delegation is active:

Apply the SKILL.md tie-breaker. Convert friction into repair, isolation, verifier creation, strategy change, or another positive-EV lane unless the autonomy contract hard-stops it.

## Risk Classification

Classify every task:

```yaml
risk:
  blast_radius: local | module | cross_module | global
  reversibility: high | medium | low
  user_visible: true
  touches_shared_contract: false
  touches_data_migration: false
  touches_auth_privacy_money: false
  confidence: high | medium | low
```

High-risk if any:

- global blast radius,
- low reversibility,
- auth/privacy/money/data migration,
- shared contract/schema,
- broad refactor,
- dependency/toolchain upgrade,
- repeated previous failure,
- user-visible core flow.

## Severity Rubric

Use this rubric everywhere. Reviewer prompts must not define competing severity meanings or numeric scores.

| Severity | Blocks Merge/Acceptance | Meaning |
|---|---|---|
| P0 | Yes | Broken core requirement, data loss, security/privacy breach, invalid central claim, unrecoverable artifact failure |
| P1 | Yes before merge/final acceptance | Missing required state/evidence/test, significant regression, maintainability or correctness risk likely to compound |
| P2 | No, unless accumulated | Useful improvement, non-blocking quality issue, moderate clarity/usability/reproducibility gap |
| INFO | No | Observation, trace, optional suggestion, or evidence note |

`P3` and numeric scores are not part of BAGEL governance. If an external reviewer uses them, map them to this rubric before integration.

## Reviewer Responsibility Matrix

Avoid duplicate review. Each reviewer owns one primary question:

| Reviewer | Owns | Does Not Re-check |
|---|---|---|
| Spec Reviewer | Required behavior/artifact unit matches the slice spec; no unapproved extra scope | Code style, broad security, architecture taste |
| Code Quality Reviewer | Maintainability, local patterns, security basics in changed code | Spec coverage already verified by Spec Reviewer |
| Independent Reviewer | Integration/regression/risk evidence and whether prior reviews are sufficient for the risk level | Full spec/code review unless evidence is missing or contradictory |
| Red-Team Oracle | Adversarial failure modes, hidden assumptions, privacy/safety/taste/philosophy attacks | Routine code style or duplicate test enumeration |
| Scenario Generator | Produces deterministic/scenario checks; reports trace failures | Merge approval |

The orchestrator deduplicates findings by root cause and keeps the highest severity. A missing test should be owned by Spec Reviewer when it is required by the spec, by Code Quality Reviewer when it affects maintainability/regression confidence, and by Independent Reviewer only when earlier reviews missed evidence required by the risk level.

## Review Matrix

| Risk | Required Before Merge |
|---|---|
| Low | tests/checks + orchestrator diff review |
| Medium | spec review + code quality review + relevant tests |
| High | R3/R4 independent reviewer + red-team/diagnostic review + rollback point + post-merge verification |
| Critical | serialize work, no unattended merge; R4 or explicit human review required before merge, while other safe work may continue |

In `unattended_stable`, upgrade every task by one review level.

## Review Independence Levels

Record the actual level used; do not overstate it.

| Level | Name | Counts As Independent? | Use |
|---|---|---|---|
| R0 | self-check | No | Only for low-risk drafts or preflight |
| R1 | same-session role switch | No | Sequential emulation when no isolation exists; record residual risk |
| R2 | fresh-context same model/session reset | Partial | Medium risk if context can be materially cleared |
| R3 | true subagent or separate agent context | Yes | Required for high-risk unattended behavior changes |
| R4 | external/human/domain reviewer | Yes | Critical changes, publication-quality work, legal/privacy/money risk |

If a matrix entry says "independent reviewer", satisfy it with R3 or R4. If the platform can only provide R1/R2, block that high-risk unattended merge, isolate the lane, continue safe autonomous work, and record the residual risk; do not create an autonomous waiver.

When platform routing allows model choice, prefer cross-model or cross-family review for Red-Team Oracle, Independent Reviewer, and final visual/product critique. Cross-model review is preferred, not required; do not stop useful work just because it is unavailable.

## Independent Review Rules

Independent reviewers:

- must not share the implementer's working context,
- inspect artifacts/diffs/tests, not self-justification,
- receive minimal task spec and changed files,
- can block merge with P0/P1 findings,
- can request diagnostic reproduction.
- may request implementer history only through a separate evidence request that names the exact transcript segment needed, why artifact evidence is insufficient, and the independence risk introduced. The orchestrator records this in the review report.

No self-approval: the worker that implemented a change cannot be the final checker.

## Artifact-Specific QA

Read `.bagel/artifact_profile.yaml` and apply only relevant hard gates:

- Software/existing software: tests, typecheck/lint when present, regression checks, setup/run evidence, review for duplicate implementation.
- Research: claim-evidence map, source quality, methodology critique, limitations, reproducibility notes.
- Writing: structure, continuity, voice consistency, pacing, unresolved plot/argument issues, reader experience.
- Document/deck: rendered output, layout/overflow checks, hierarchy, factual consistency, export/readability.
- Data analysis: data provenance, cleaning assumptions, validation checks, chart/table correctness, reproducibility.

For UI, game, visual product, deck, document, and layout-heavy artifacts, require rendered evidence before final acceptance:

```yaml
visual_evidence:
  artifacts:
    - "screenshots/desktop.png"
    - "screenshots/mobile.png"
  compared_against:
    - ".bagel/constitution.yaml#taste_kernel"
  findings:
    - severity: P1 | P2 | INFO
      evidence: "..."
      fix_task: "..."
```

If no screenshot/render tool exists, creating a minimal local visual verifier is a normal autonomous task.

Style heuristics such as function length, route coverage, visual tokens, loading/empty/error states, or browser checks are hard gates only when the artifact profile makes them applicable. Otherwise record `not_applicable` in `.bagel/gates/status.yaml`.

## Verification Ladder

Use the strongest relevant checks:

1. static/schema checks,
2. unit tests,
3. typecheck/lint,
4. integration tests,
5. e2e/browser/CLI scenario,
6. regression tests for touched behavior,
7. manual evidence table when automation is unavailable,
8. post-merge verification.

Do not skip lower-level checks just because a higher-level demo appears to work.

When automation is unavailable or irrelevant, replace it with a manual evidence table:

```yaml
manual_evidence:
  claim_or_requirement: ""
  inspection_method: ""
  artifact_paths: []
  reviewer: ""
  result: pass | fail
```

## Defect Handling

When review finds a defect:

1. Classify severity and root cause.
2. Link to task, branch, change record, and tests.
3. Decide: repair in same branch, create follow-up task, rollback, or reject.
4. Add regression test or evidence when possible.
5. Update agent context if defect reveals misunderstood project reality.

Repeated defects of same class trigger recovery protocol and task strategy change.

## System Self-Iteration

When BAGEL modifies its own prompts, skills, workflow files, scripts, or governance docs:

- treat as high-risk,
- use the required review level from this matrix,
- run skill validation or equivalent,
- forward-test with neutral tasks when practical,
- update evolution ledger,
- do not rely on the authoring agent's confidence.

## Merge Correctness Gate

Before merge:

- task acceptance criteria satisfied,
- required review matrix satisfied,
- checks pass or failures are documented and accepted by policy,
- no out-of-scope edits,
- no stale/disputed context used,
- rollback point exists for medium/high risk,
- post-merge verification plan exists.
- relevant gate predicates in `.bagel/gates/status.yaml` pass or have authorized waivers.

After merge:

- run post-merge checks,
- update evolution ledger,
- update freshness and project context,
- release locks,
- update user briefing when user-visible.
