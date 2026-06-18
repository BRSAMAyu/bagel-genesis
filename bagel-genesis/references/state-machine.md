# BAGEL Genesis State Machine

Full-mode S-2 through S17 state definitions with entry conditions, required artifacts, exit conditions, hard gates, and failure handling.

Do not use this as a mandatory waterfall. `quick_autonomy` uses the three-phase loop from `SKILL.md`: Align, Build, Polish. Enter the detailed states only when the task needs them, such as blank-slate product generation, broad takeover, multi-day work, skeleton-first architecture, parallel work, or high-risk gates.

Before applying state-specific gates, load `.bagel/artifact_profile.yaml` and `references/artifact-types.md`. Software gates such as routes, Ghost Ship, design tokens, browser checks, and auth boundaries apply only when the artifact profile makes them relevant.

## State Machine Overview

```
S-2 Existing Project Intake (only when workspace/project is non-blank)
 ↓
S0 Vision Intake            ← captures vision_summary.md first (the input to alignment)
 ↓
S-1 Deep Alignment          ← produces vision-canon, autonomy-contract, etc. (alignment OUTPUTS)
 ↓
S1 Constitution + Horizon   ← Stop Contract + BUILD UNLOCK checkpoint fires at S1 exit
 ↓
S2 Taste Kernel + Coherence
 ↓
S3 Missing-Belief Discovery
 ↓
S4 Product Graph Initialization (optional UPMG backend)
 ↓
S5 Decision Classification
 ↓
S6 Skeleton Era
 ↓
S7 Skeleton/Ghost Ship Gate  ← the align→build run_phase transition fires here
 ↓
S8 Value Slice Filling Loop
 ↓
S9 Immediate Clearing Check (after each slice)
 ↓
S10 Level 1 Deterministic Simulation
 ↓
S11 Level 2 Generated Scenarios
 ↓
S12 Level 3 Shadow User Simulation
 ↓
S13 Counterfactual Red-Team
 ↓
S14 Vision Amendment / Fork Check
 ↓
S15 Baseline Candidate
 ↓
S16 Excellence Loop + Independent Critique
 ↓
S17 Final Delivery
```

**Ordering rationale (P2-1 fix):** S0 Vision Intake must precede S-1 Deep Alignment. S-1's required artifacts (`vision-canon.md`, `decision-map.yaml`, `autonomy-contract.yaml`, `excellence_horizon.yaml`) are the *outputs* of deep alignment, which can only be produced once the vision itself is captured in S0's `vision_summary.md`. The previous ordering (S-1 before S0) asked the agent to produce alignment artifacts before the vision they align to. Each S-state's `run_phase` is mapped in `references/run-phase-model.md`.

## S-2: Existing Project Intake

**Entry:** Workspace contains an existing project, partial implementation, prior research/writing artifact, or user asks for autonomous optimization of current work.

**Required Artifacts:**
- `.bagel/agent_context/global-capsule.yaml`
- `.bagel/agent_context/context-index.yaml`
- `.bagel/agent_context/freshness.yaml`
- `.bagel/agent_context/project-facts.yaml`
- `.bagel/agent_context/conventions.md`
- `.bagel/agent_context/module-map.md`
- `.bagel/agent_context/feature-inventory.md`
- `.bagel/agent_context/current-behavior.md`
- `.bagel/agent_context/do-not-duplicate.md`
- `.bagel/project_inventory/evidence.md`
- `.bagel/project_inventory/open-questions.md`
- `.bagel/evolution/change-records/CHG-*.yaml`

**Process:**
1. Dispatch Project Cartographer or run its protocol sequentially.
2. Inspect repository/artifact structure, docs, configs, tests, entrypoints, representative modules, and current behavior.
3. Identify what is implemented, partial, stubbed, broken, missing, and intentionally preserved.
4. Identify local conventions and reusable modules/assets to prevent duplicate work.
5. Compare current reality with the user's stated vision.
6. Write agent-facing context and human-facing project reality briefing.
7. Write initial evolution change record.
8. Bring unresolved questions into S-1 alignment.

**Exit Conditions:**
- Agent-facing context exists and cites evidence.
- Global capsule and context index exist.
- Freshness is marked fresh or explicitly disputed with owner.
- Current behavior and project conventions are understood enough to dispatch bounded workers.
- Open questions are classified by severity.

**Hard Gates:**
- No behavior-changing work before project understanding exists.
- No worker dispatch without relevant agent-facing context or task-local brief.
- No worker dispatch from stale/disputed context unless refreshing or resolving that context.
- No duplicate implementation when existing module/service/component is known.

**Skip:** If the project is truly blank, record that S-2 is not applicable and proceed to S-1.

---

## S0: Vision Intake

**Entry:** User invokes BAGEL Genesis with a vision.

**Required Artifacts:**
- `.bagel/vision_summary.md`

**Process:**
1. Read user's vision description
2. If vision is vague, run a short native brainstorming pass: ask for the north star, target users, excluded directions, core workflows, constraints, and non-goals. External brainstorming tools are optional, not required.
3. Ask clarifying questions (purpose, users, constraints)
4. Identify implicit assumptions
5. Draft vision summary

**Exit Conditions:**
- Vision summary approved by user **or** the user has delegated approval under a long-run autonomy contract (record the delegation in `.bagel/ledger.yaml` or `.bagel/alignment/human-decisions.yaml`)
- No ambiguity in product purpose

**Hard Gates:**
- User has explicitly approved the vision summary **or** delegated approval under a long-run autonomy contract. Under delegation, do not stop for S0 confirmation unless a hard-stop boundary is unresolved (core promise, privacy/legal/financial/safety posture, target audience, production data, credentials/paid resources, or an irreversible direction).

---

## S-1: Deep Alignment

**Entry:** S0 complete — `vision_summary.md` exists (S-1 consumes it as input).

**Required Artifacts:**
- `.bagel/alignment/vision-canon.md`
- `.bagel/alignment/decision-map.yaml`
- `.bagel/alignment/autonomy-contract.yaml`
- `.bagel/alignment/assumption-ledger.yaml`
- `.bagel/user_briefing/README.md`
- `.bagel/excellence_horizon.yaml`
- `.bagel/evolution/index.yaml`

**Process:**
1. Clarify the vision more deeply than a native plan mode.
2. Surface hidden assumptions and unresolved decisions.
3. Challenge user choices that appear risky or contradictory.
4. Classify which decisions the system may make autonomously.
5. Define how the user will stay aligned through layered briefing.
6. Define excellence horizon beyond runnable baseline.

**Exit Conditions:**
- User approves the alignment artifacts or explicitly delegates remaining ambiguity.
- Autonomy boundaries are clear enough for unattended operation.

**Hard Gates:**
- No long autonomous execution without autonomy contract.
- No baseline-only stop condition when the user requested high completion.
- No autonomous run without evolution ledger initialized.

---

## S1: Vision Constitution + Completion Horizon

**Entry:** S0 complete.

**Required Artifacts:**
- .bagel/constitution.yaml (quick) or .bagel/constitution.json (full)
- `.bagel/completion_horizon.yaml`

**Process:**
1. Draft Vision Constitution from vision summary (see references/constitution-template.md)
2. Define forbidden directions explicitly
3. Define autonomy policy (what system can/cannot decide)
4. Define Completion Horizon (must_include, excludes, stopping_trigger)
5. Constitutional Court review (self-review against engineering escape evidence)

**Exit Conditions:**
- Constitution passed Constitutional Court review
- Completion Horizon is internally consistent

**Hard Gates:**
- `target_users.primary` is non-empty
- `target_users.excluded` is non-empty
- `forbidden_directions` has at least 3 items
- `autonomy_policy.human_checkpoint_required` includes:
  - "core_positioning_change"
  - "privacy_policy_change"
  - "business_model_change"

**Failure Handling:**
- Constitution vague → return to S0 for more clarification
- Forbidden directions too generic → ask user for specifics

---

## S2: Taste Kernel + Coherence Invariants

**Entry:** S1 complete.

**Required Artifacts:**
- `.bagel/taste_kernel.yaml`
- `.bagel/coherence_rules.yaml`
- `.bagel/design_tokens.yaml` (only for visual/interface artifacts)
- `.bagel/artifact_profile.yaml`

**Process:**
1. Draft Taste Kernel based on artifact type
2. Identify forbidden directions for the artifact: visuals, writing, research claims, architecture, interaction, data assumptions, or domain style
3. Define interaction, writing, research, or presentation direction as applicable
4. Classify coherence rules (hard_gate, soft_gate, advisory)
5. Set design tokens only when visual/interface quality applies

**Exit Conditions:**
- Required profile-specific files created
- Each rule has enforcement type defined

**Hard Gates:**
- At least 5 `hard_gates` defined
- At least 3 forbidden directions defined for the artifact type
- Design tokens include spacing_unit, primary color, radius, and font family only when visual/interface gates are applicable

---

## S3: Missing-Belief Discovery

**Entry:** S2 complete.

**Required Artifacts:**
- `.bagel/missing_beliefs/*.json` (one per identified gap)
- `.bagel/decisions/ADR-*.json` (for resolved gaps)

**Process:**
1. Scan all relevant taxonomies (see references/missing-belief-discovery.md):
   - Edge states (empty, error, loading, permission, network, timeout, offline)
   - User journeys (first-time, returning, abandonment, wrong choice)
   - Data cases (zero, large, malformed, unicode, duplicates)
   - Privacy (unauthenticated, sensitive, owner check)
   - AI pipeline (timeout, low confidence, malformed, fallback)
2. For each identified gap, create Missing Belief Card
3. For each Missing Belief, determine resolution:
   - Industry convention → automatic decision (ADR)
   - User decision needed → escalate
   - Multiple options → create variants

**Exit Conditions:**
- All taxonomies have been scanned
- All Missing Beliefs have status (resolved, escalated, deferred)

**Hard Gates:**
- Critical taxonomies (edge_state, user_journey) fully scanned
- No unresolved Missing Beliefs of P0 severity

---

## Product Graph Backends

BAGEL uses a product graph abstraction. Valid backends:

- **File-backed graph:** `.bagel/product_graph.yaml` plus `.bagel/state.json`, `.bagel/decisions/`, and `.bagel/slices/`. Use this for most projects.
- **UPMG backend:** `.bagel/upmg.sqlite` or another graph store. Use this only when project complexity justifies it.

All gates that mention graph, route, journey, or node state accept either backend. Do not require UPMG for the simplified path.

## S4: Product Graph Initialization (Optional UPMG Backend)

**Entry:** S3 complete.

**Required Artifacts:**
- For simple projects: `.bagel/product_graph.yaml`, `.bagel/decisions/`, `.bagel/slices/`, and `.bagel/state.json`
- For complex projects: `.bagel/upmg.sqlite` or graph database

**Process:**
1. Create belief nodes from constitution
2. Create journey nodes from vision
3. Create architecture nodes from skeleton plan
4. Create data contract nodes from stubs
5. Create verification nodes from coherence rules
6. Link dependencies

**Exit Conditions:**
- All ADRs represented in the chosen product graph backend
- All seed nodes or file-backed records have proper dependency links

**Hard Gates:**
- Every belief has at least one child journey, architecture, slice, or decision record
- No orphan graph nodes or unlinked file-backed records

**Simplified Path:** For most projects, use file-based tracking instead of full graph database. Skip S4 unless project complexity warrants it.

---

## S5: Decision Classification

**Entry:** S4 complete (or S3 for simplified path).

**Required Artifacts:**
- Updated `.bagel/decisions/ADR-*.json` with classification

**Process:**
1. For each ADR, classify as:
   - **A: Logic-driven** (API idempotency, error codes, data normalization) → Full autopilot
   - **B: Convention-driven** (login flow, settings page, empty states) → Delegated with ADR
   - **C: Taste-driven** (visual density, animation rhythm, copy tone) → Variants or checkpoint
   - **D: Philosophy-driven** (privacy boundaries, business model, core positioning) → Human checkpoint
2. Assign uncertainty vector
3. For Class C/D decisions, schedule checkpoints
4. Document evidence types

**Exit Conditions:**
- All ADRs classified
- All Class D decisions have checkpoint schedules

**Hard Gates:**
- No Class A decision at "low" confidence
- All Class D decisions have explicit human_checkpoint dates

---

## S6: Skeleton Era

**Entry:** S5 complete.

**Required Artifacts:**
- Profile-specific skeleton: runnable shell, outline, protocol, template, analysis pipeline, or mixed module map
- Required contract/schema/claim maps
- Stub/mock/placeholder registry initialized when applicable

**Process:**
1. Generate artifact structure
2. For each identified API/data interface, structured claim, section, or pipeline boundary, create the relevant contract:
   - TypeScript interface
   - Zod schema (or Pydantic, OpenAPI, etc.)
   - Contract test
   - Mock server / fixture
   - claim-evidence map, outline constraint, or data validation rule for non-software artifacts
3. Register all stubs/placeholders with replacement policies
4. Implement profile-specific skeleton:
   - Software: routes/commands/screens exist, error/auth/state boundaries exist when relevant
   - Research: protocol, claim map, source plan, reproducibility scaffold
   - Writing: outline, continuity bible, voice/tone guide, section/chapter map
   - Document/deck: template, narrative spine, layout system, section map
   - Data analysis: pipeline scaffold, data dictionary, assumptions map, validation checks

**Exit Conditions:**
- Skeleton can be opened, run, read, rendered, or executed enough to verify structure
- Navigation, outline, pipeline, or argument flow has no dead ends
- All stubs/placeholders registered when applicable

**Hard Gates:**
- Every applicable API/data model/AI pipeline/structured claim has a typed contract, schema, or evidence map
- Every stub/placeholder has replacement criteria
- Error/auth boundaries exist only when the artifact profile requires them
- Non-software skeleton gates from `references/artifact-types.md` pass

**Why Skeleton-First:** Value slices filled before skeleton leads to architecture, argument, narrative, or analysis myopia. The skeleton gate ensures all integration points exist before filling real value.

---

## S7: Skeleton/Ghost Ship Integration Gate

**Entry:** S6 complete.

**Required Artifacts:**
- Skeleton/Ghost Ship validation report

**Process:**
1. Boot, render, open, read, or execute the artifact skeleton in the target runtime/form
2. Run contract/schema/claim/outline checks
3. Verify route, section, pipeline, argument, or narrative accessibility
4. Verify stub/placeholder registration
5. Verify auth/error boundaries only when applicable
6. Complete core user journey, reader journey, research trace, deck narrative, or analysis path with mock/placeholder data
7. Run coherence guard

**Exit Conditions (ALL must pass):**
1. Artifact skeleton opens/runs/renders/executes in its target form
2. All graph, route-map, outline, claim, section, or pipeline nodes are reachable
3. All applicable contracts/schemas/claim maps have checks or evidence
4. All checks pass
5. All stubs/placeholders are registered with typed schemas or replacement criteria
6. All critical stubs/placeholders have expiration or acceptance policy
7. Error boundary works when applicable
8. Auth/access boundary can be instantiated when applicable
9. Core ghost journey/path can be completed with mock data/placeholders
10. No hard coherence gate violation

**Failure Handling:**
- contract/schema/claim failure → return to S6, regenerate contracts or evidence map
- route/section/claim/pipeline dead end → repair graph, outline, route-map, or pipeline artifact
- unregistered stub → block progression
- auth boundary missing → block progression
- target runtime boot failure → debug, return to S6 if needed

**Hard Gates:**
- Skeleton/Ghost Ship Gate is a HARD GATE. Value slice filling cannot begin until all profile-specific conditions pass.

**Consecutive Failure Protocol:**
- If gate fails 3+ times consecutively, stop repeating the same approach and enter `references/recovery-protocol.md`.
- Allowed autonomous choices: repair S6, shrink the verifier, use independent diagnosis, sandbox rework, rollback to last valid checkpoint, or amend scope through S14 when justified.
- Wake the user only for hard-stop boundaries in the autonomy contract. Do not skip S7; adapt it to the artifact profile, create missing local verifiers, or continue another high-value task while the S7 lane is isolated.

---

## S8: Value Slice Filling Loop

**Entry:** S7 complete.

**Required Artifacts:**
- For each slice: completed artifact unit, profile-specific verification, review or simulation report

**Process:**
1. Select next value slice from queue (highest priority first)
2. Implement by dispatching an implementer subagent when available; otherwise enter Implementer mode sequentially, then compact before returning to Orchestrator mode
3. Implementation includes the profile-specific slice unit:
   - Software: UI/CLI/API/data flow, state, error/loading/empty/retry states, tests, deterministic scenario
   - Existing software: bounded change, preserved current behavior, no duplicate implementation, regression evidence
   - Research: claim/section/experiment, citations, methodology, counterarguments, limitations, reproducibility notes
   - Writing: chapter/scene/section, continuity, voice, pacing, unresolved narrative/argument issues
   - Document/deck: section/slide group, rendered layout, hierarchy, factual consistency, export/readability
   - Data analysis: dataset/question/chart, provenance, cleaning assumptions, validation checks, reproducible output
4. Verify slice completion using `.bagel/artifact_profile.yaml` and `references/artifact-types.md`
5. Update product graph and state
6. Loop until all slices complete

**Slice Completion Criteria (ALL must pass):**
1. Required profile-specific unit is complete.
2. Required profile-specific verification passes or has an authorized waiver.
3. Contracts, schemas, claim maps, outlines, or data validation pass when applicable.
4. Edge/failure/continuity/counterargument states required by the profile are covered.
5. Hard coherence gates pass.
6. Product graph/file-backed state, task queue, and gate status are updated.
7. Slice budget not exceeded (>150% of estimate triggers abort review).

**Exit Conditions:**
- All P0 slices verified
- All P1 slices verified or stubbed with clear label

**Slice Abort Protocol:**
- If slice exceeds 150% of time estimate → trigger abort review
- Options: extend budget, simplify scope (via amendment), abandon slice
- Document decision in `.bagel/ledger/clearing_log.md`

**Pivot Protocol:**
- If user requests major pivot mid-slice → pause all work
- Classify pivot: small (return to S6) or major (return to S0)
- Major pivots require fresh Vision Constitution

---

## S9: Immediate Clearing Check

**Entry:** Each slice completion.

**Required Artifacts:**
- `.bagel/ledger/clearing_log.md` updated

**Process:**
1. Scan for uncleared mutations to committed nodes
2. Calculate clearing cost (time, depth)
3. Apply clearing policy (see references/clearing-policy.md):
   - Cascade if cost < 50% budget and depth ≤ 2
   - Rollback if cost ≥ 50% and reversibility high
   - Human checkpoint if cost ≥ 50% and reversibility low
4. Execute in Atomic Rework Sandbox if cascade
5. Log to clearing ledger

**Exit Conditions:**
- No uncleared mutations
- Clearing log updated

**Hard Gates:**
- Zero uncleared committed-node mutations

**Why Immediate:** Technical debt crossing Value Slices compounds. Each deferred fix makes the next slice harder. Immediate clearing prevents accumulation.

---

## S10: Level 1 Deterministic Verification

**Entry:** After each completed S8 slice before S9 clears it, and after integration of any high-risk patch. Do not run S10 for every intermediate edit inside a worker; workers run narrow local checks before handoff.

**Required Artifacts:**
- L1 deterministic verification report

**Process:**
Run deterministic checks selected by artifact profile:

- Software: routes/commands/screens accessible, no dead-end navigation, forms validate, async actions have loading/error/retry, protected routes enforce auth, controls have accessible names.
- Existing software: changed behavior works, preserved behavior still works, no duplicate implementation, no unexpected public API/config changes.
- Research: claim-evidence links resolve, citations exist, methods/assumptions are stated, limitations and counterarguments are present.
- Writing: outline slots filled, continuity bible satisfied, voice/tone constraints respected, unresolved plot/argument markers tracked.
- Document/deck: render/export succeeds, no text overflow, visual hierarchy and factual claims checked.
- Data analysis: pipeline runs or is reproducible, data validation passes, charts/tables trace to source data, assumptions recorded.

**Exit Conditions:**
- All profile-required checks pass or have authorized waivers

**Hard Gates:**
- Zero dead-end nodes for the artifact profile: routes, commands, sections, claims, chapters, slides, or pipeline steps
- Required validation for the profile passes

---

## S11: Level 2 Generated Scenarios

**Entry:** Each value slice.

**Required Artifacts:**
- Generated scenario scripts
- Simulation traces

**Process:**
1. Read value slice from `.bagel/slices/`, `.bagel/product_graph.yaml`, or UPMG
2. Extract expected journey, argument path, reader path, research trace, deck narrative, or analysis path
3. Map to UI locators, commands, document sections, claims, chapters, slides, or pipeline steps
4. Generate scenario/check artifact appropriate to the profile
5. Dry-run against the target runtime/form
6. Execute scenario or inspection
7. Write result to simulation ledger

**Exit Conditions:**
- All scenarios pass

**Hard Gates:**
- All P0 scenarios pass

---

## S12: Level 3 Shadow User Simulation

**Entry:** Milestones only.

**Required Artifacts:**
- L3 simulation report

**Process:**
1. Dispatch L3 simulation/review subagent with persona or domain lens
2. Run persona/domain-based scenarios:
   - Anxious user
   - Privacy-sensitive user
   - Busy user
   - Skeptical user
   - First-time user
   - Critical reader/reviewer
   - Domain expert
   - Reproducer/auditor
3. Collect failure reports

**Exit Conditions (for blocking milestones):**
- No core journey impossibility
- No privacy misunderstanding
- No missing entry point
- No core argument, narrative, deck, or analysis path impossibility when applicable

**Hard Gates:**
- L3 simulation has been run (may have non-blocking findings)

**When to Run L3:**
- After Skeleton/Ghost Ship gate (S7)
- After core P0 slices complete
- Before Baseline Candidate (S15)

---

## S13: Counterfactual Red-Team

**Entry:** Required S10/S11 checks for the current milestone are complete.

**Required Artifacts:**
- `.bagel/redteam/report-*.md`

**Process:**
1. Dispatch Red-Team Oracle subagent (see agents/red-team-oracle.md)
2. Attack all Class C/D decisions
3. Attack all P0 value slices
4. Attack all privacy-sensitive flows
5. Generate attack report

**Attack Families:**
- Environment/context counterfactuals relevant to the artifact profile
- Persona counterfactuals (anxious, privacy-sensitive, skeptical)
- Failure counterfactuals (AI timeout, empty data, mid-exit)
- Philosophy counterfactuals (violates low_cognitive_load?)
- Adversarial counterfactuals (malicious user, spammer)

**Exit Conditions:**
- All attacks documented
- All P0/P1 findings resolved

**Hard Gates:**
- No P0 findings remain
- No P1 findings remain unresolved

---

## S14: Vision Amendment Check

**Entry:** S13 complete OR amendment proposed.

**Required Artifacts:**
- Amendment decisions logged

**Process:**
1. Scan for pending amendments
2. Dispatch Constitutional Court (see agents/constitutional-court.md)
3. Court reviews:
   - Aligns with original vision?
   - Not engineering escape?
   - Doesn't change core promise?
4. Execute accepted amendments
5. Cascade changes through the chosen product graph backend

**Court Isolation:**
- Court ONLY reviews: original constitution, taste kernel, completion horizon, amendment proposal, L3 failure reports
- Court does NOT see: current code complexity, executor failures, library preferences

**Engineering Escape Evidence Basis:**
- executor-originated reduction, deferral, weaker substitute, or narrowing of a P0/P1 promise,
- affected constitution or completion-horizon clause,
- missing user-approved constraint or external reality,
- alternatives that preserve the promise but were not attempted,
- repeated rationale class from `.bagel/ledger/amendment-history.yaml`.

**Exit Conditions:**
- No pending amendments
- All amendments logged

**Hard Gates:**
- No executive-proposed vision changes accepted without user sign-off
- Court consistency check: if 3+ same-type amendments rejected with similar reasons → system review

---

## S15: Baseline Candidate

**Entry:** S14 complete.

**Required Artifacts:**
- Baseline candidate package
- All reports compiled

**Process:**
1. Final verification suite
2. Compile all reports:
   - Test report
   - Contract report
   - Simulation report
   - Red-team report
   - Coherence report
   - Decision ledger
3. User acceptance review

**Exit Conditions:**
- Baseline candidate is accepted for excellence-loop entry

**Hard Gates:**
- No P0 issues remain
- No P1 issues remain
- All P2 issues documented

---

## S16: Excellence Loop + Independent Critique

**Entry:** S15 baseline candidate passes.

**Required Artifacts:**
- `.bagel/excellence_horizon.yaml`
- `.bagel/task_queue.json`
- `.bagel/progress.json`
- `.bagel/reviews/excellence-round-*.md`
- `.bagel/ledger/rejected-improvements.md`

**Process:**
1. Run independent critique, red-team, brainstorm, reproducibility, and briefing review passes.
2. Convert high/medium expected-value findings into bounded tasks.
3. Execute tasks through isolated workers.
4. Verify with tests, reviews, or domain evidence.
5. Update user briefing and progress ledger.
6. Repeat until stop criteria pass.

**Exit Conditions:**
- Excellence horizon passes.
- Two independent rounds find no unresolved high/medium expected-value improvements in scope.
- Remaining improvements are rejected, out of scope, or require user decision.

**Hard Gates:**
- Worker cannot self-approve.
- No final delivery while P0/P1/P2 high-value findings remain unresolved.
- No hidden setup/reproducibility failure.

---

## S16b: Crystal Extraction

**Entry:** S16 complete.

**Required Artifacts:**
- `.bagel/crystals/*.yaml`

**Process:**
1. Identify high-quality decision chains (slices that passed L3 + Red-Team)
2. For each, extract crystal with:
   - Context (user_type, platform, first_session_goal)
   - Proven decisions
   - Anti-patterns
   - Applicability conditions
   - Mutation requirements
3. Verify applicability score

**Crystal Applicability Rules (prevent blind adoption):**
- No direct crystal adoption
- Only crystal-informed decision synthesis
- Context match score must be ≥ 0.7
- Mutation requirements must be explicitly documented

**Exit Conditions:**
- At least 3 crystals extracted (if applicable)

**Hard Gates:**
- All crystals have applicability conditions
- No crystal is blindly adoptable

---

## S17: Final Delivery

**Entry:** S16 complete, and S16b complete if crystal extraction applies.

**Required Artifacts:**
- Complete delivery package
- Evolution audit report
- Git/merge audit report when repository changes were made
- Agent coordination audit report when multiple agents were used
- Quality/review audit report
- Fresh agent-facing context
- Current user briefing

**Delivery Package:**
- Running product (deployed or local)
- Source code
- Setup script
- Deployment guide
- README
- Environment example
- Test report
- Contract report
- Simulation report
- Red-team report
- Decision ledger
- Stub closeout report
- Coherence report
- Crystal extraction report
- Evolution timeline and audit report
- Git branch/merge/rollback summary
- Agent registry/lock/merge queue summary
- Review matrix and recorded review-independence level summary
- Agent context freshness report
- User briefing layers

**Exit Conditions:**
- User confirms delivery accepted

**Hard Gates:**
- All required artifacts present
- App runs from clean setup
- Evolution ledger audit passes.
- Git audit passes: no unmerged required branch, unresolved lock, unknown dirty state, or missing rollback record for risky changes.
- Multi-agent audit passes: no active/stalled agent blocks delivery, no unresolved ownership conflict, no unverified merge.
- Quality audit passes: no self-approved behavior change, required reviews completed for risk/run mode, no unresolved P0/P1 correctness issue.
- Agent-facing context has no unresolved stale/disputed entries relevant to delivered scope.
- User briefing reflects final state and links to evolution summary.

---

## Simplified Path

For simpler projects, use this path:
```
[S-2 if existing project] → S0 → S-1 → S1 → S2 → S3 → S5 → S6 → S7 → [S8(slice) → S9(clear)] repeated → S10 → S13 → S15 → S16 → S17
```
Skip S-2 only for truly blank projects. Skip S4's UPMG backend, S11 (L2 scenarios), S12 (L3 simulation), and S16b (crystals) unless project complexity warrants them. Keep the lightweight file-backed product graph and excellence loop for all long autonomous projects.

## Anti-Drift Mechanisms Per State

| State | Drift Risk | Counter |
|-------|-----------|---------|
| S0-S1 | User ambiguity becomes constitution | Constitutional Court review |
| S2 | Taste rules too vague to enforce | Hard gate on ≥5 specific rules |
| S3 | Taxonomy gaps missed | P0 hard gate on edge_state + user_journey |
| S6 | Stubs become permanent | Expiration policy + Ghost Ship Gate |
| S8 | Quality decay per slice | Slice completion checklist (10 criteria) |
| S9 | Tech debt accumulates | Immediate clearing invariant |
| S13 | Overconfidence | Counterfactual attacks |
| S14 | Engineering escape | Court isolation + signal detection |
