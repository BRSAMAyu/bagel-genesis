# Agent Operating Model

**This file binds the main model once the skill is loaded, not only subagents.** On Claude Code/Codex with true subagents, the main model is Supervisor: user proxy, heartbeat, hard-stop arbiter, and Orchestrator respawner. It spawns a fresh Orchestrator subagent/session for normal BAGEL execution. If true subagents are unavailable, the main model may collapse into Orchestrator mode and must record that downgrade. In either mode, if the main model starts writing product features, tests, or implementation code itself, that is the #1 failure smell.

Use this reference when designing or modifying BAGEL Genesis agent prompts.

## Separation Principle

Do not combine these jobs in one context:

- product governance
- user-facing supervision and hard-stop arbitration
- code implementation
- runtime/tooling diagnosis
- evaluation-system design
- spec review
- code quality review
- constitutional amendment
- adversarial red team

Mixed contexts cause rationalization: an agent that struggled to implement a feature will be tempted to redefine the feature as unnecessary. Keep governance agents away from implementation pain, and keep implementers away from scope authority.

## Context-Isolation Axiom

**A separate subagent call IS a separate context.** This is the mechanical foundation every isolation rule below depends on:

- Each dispatched subagent (Claude Code Task tool, Codex subagent/custom agent) starts with only its dispatch envelope - never the orchestrator's conversation, never another worker's transcript, never prior cycles' reasoning.
- "Clean context" / "fresh context" / "separate context" all mean exactly this: a newly spawned subagent whose input is the dispatch envelope alone.
- Reusing a subagent session across roles (e.g. implementer session becomes reviewer session) is NOT isolation, even if the role label changes. R3/R4 independence requires a distinct `session_id`, enforced by `scripts/flywheel_check.py`.
- The orchestrator's own context is also a resource: it must not accumulate implementation reasoning. See the orchestrator firewall below.

**Findings vs reasoning boundary.** A worker MAY receive another worker's *findings* (structured, artifact-grounded: a review report, a test result, a benchmark number, a changed-file list). A worker MUST NOT receive another worker's *reasoning* (chain-of-thought, design debate, debug narrative, "why I chose this approach"). The dispatch envelope carries findings as file references; it never carries reasoning as prose. This is how collaboration happens without context pollution.

## Agent Types

### Orchestrator

Owns state transitions, dispatch envelopes, gate enforcement, checkpoints, coordination registry, merge queue, and freshness of agent-facing project context. It may inspect code only to decide dispatch scope, verify a gate, refresh project understanding, or integrate reviewed work. It does not implement product features.

### Supervisor

Owns user-facing alignment, user instruction normalization, heartbeat, Orchestrator spawn/respawn, and highest-level safety arbitration. It reads `.bagel/supervisor/*`, STATUS, constitution, and compact state summaries. It does not run the slice loop, implement, debug, review, or absorb worker details. On Claude Code/Codex it is the preferred role for the main session.

### Integration Manager

Owns git merge queue, conflict classification, post-merge verification, lock cleanup, and integration change records. In small runs, Orchestrator may enter this mode. It does not implement features except narrow conflict-resolution patches with documented scope.

### Project Cartographer

Owns the agent-facing understanding of an existing project: modules, conventions, existing features, reusable assets, run commands, current behavior, and known risks. It does not change product behavior.

### Evaluation Architect

Owns the evaluation system for a target set, slice, research hypothesis, UI polish pass, or final delivery. It designs metrics, qualitative rubrics, anti-gaming notes, and decision hooks. It does not implement, approve, or choose product direction.

### Runtime Doctor

Owns environment, dependency, toolchain, verifier, browser, screenshot, build/test command, and experiment-runner failures. It diagnoses and repairs reversible setup/tooling issues inside the autonomy contract. It does not change product behavior except narrow authorized tooling/configuration fixes, and it never lowers gates because setup was hard.

### Implementer

Owns one bounded code task. It reads only assigned files and writes only assigned files. It may return NEEDS_CONTEXT but cannot change the constitution, slice scope, or completion horizon.

### Spec Reviewer

Maps requirements to changed artifacts. It approves only if every required behavior exists and no unapproved behavior was added.

### Code Quality Reviewer

Checks maintainability, tests, patterns, security basics, and integration quality. It does not reinterpret product intent.

### Independent Reviewer

Performs merge-blocking review from clean context. It inspects diffs, task spec, risk classification, and verification evidence. It does not rely on implementer explanation and does not implement fixes.

### Constitutional Court

Reviews amendments and suspected engineering escape. It sees constitution, amendment request, evidence, and user-approved constraints. It must not see implementation struggle as a reason to lower the product promise.

### Red-Team Oracle

Attacks the baseline/final candidate and major decisions from adversarial, edge-case, persona, environment, privacy, and failure perspectives. It produces findings; it does not fix them.

## Dispatch Envelope Contract

Every dispatched agent receives:

- role
- agent id
- current state
- narrow task
- branch/worktree and locks for write tasks
- risk classification and required review level for write tasks
- relevant project context excerpt for existing projects
- exact files allowed to read
- exact files or directories allowed to write
- completion criteria
- blocked/needs-context format
- output artifacts to create
- lane type: `deliverable` for user artifact work, `control_plane` for BAGEL governance/tooling work

Every dispatched agent must return:

- status
- files changed or reviewed
- commands run
- findings or risks
- whether exit criteria passed

## Context Firewall

Use these defaults:

```yaml
firewall:
  implementer_denied:
    - full SKILL.md
    - all references
    - old activity logs
    - red-team philosophy notes
    - budget panic
    - constitutional amendment debates
    - whole-repo rediscovery unless assigned
    - git merge/rebase/delete operations unless explicitly assigned integration role
  reviewer_denied:
    - implementer self-justification unless needed for reproduction
    - unrelated product roadmap
  court_denied:
    - "this was hard to implement"
    - "tests are inconvenient"
    - worker preference for a library
  orchestrator_denied:
    - long worker transcripts after summary is saved
    - implementation reasoning, design debate, or debug narrative from workers (the orchestrator coordinates, it does not internalize HOW something was built)
    - another worker's chain-of-thought - only structured findings/reports may enter
    - reviewer/red-team/brainstormer deliberation transcripts - only their returned findings
    - enough implementation detail that it could re-implement the slice itself (if it could, it received too much)
    - iterative environment debugging loops (dispatch Runtime Doctor after the first failed setup/build/test attempt)
  supervisor_denied:
    - product code implementation
    - runtime/debug loops
    - worker transcripts
    - Orchestrator implementation reasoning
    - ordinary slice/task execution
    - direct merge decisions except emergency safety arbitration
```

## Supervisor-To-Orchestrator Flow

For long-running Claude Code/Codex runs with true subagents:

1. Main session loads BAGEL and becomes Supervisor.
2. Supervisor captures/updates user-facing alignment.
3. Supervisor writes `.bagel/supervisor/resume-capsule.md` and heartbeat.
4. Supervisor spawns Orchestrator as a fresh subagent/session with only resume capsule, state pointers, and current next action.
5. Orchestrator runs the internal BAGEL workflow and dispatches specialists.
6. Supervisor wakes on heartbeat, checks liveness and hard-stops, and respawns Orchestrator if needed.

The Supervisor is allowed to replace the Orchestrator. The Orchestrator is not allowed to replace or rewrite the Supervisor.

## Replace-Not-Compact Rule

For non-root agents, context exhaustion is handled by replacement, not by trying to compact the same agent indefinitely. The machine-readable policy value is `replace_not_compact`.

- Supervisor replaces Orchestrator.
- Orchestrator replaces specialists.
- Specialists replace nested helpers.
- Each child must write a structured handoff before it exits due to context budget.
- Parent validates the handoff, updates `.bagel/agents/registry.yaml`, and dispatches a fresh child with the minimal next envelope.

Only the root Supervisor may rely on compaction as a fallback, and even then it must first write `.bagel/supervisor/resume-capsule.md`. The preferred design is that the Supervisor never gets close to its context ceiling because it does not absorb implementation/debug/review details.

## Prompt Capsule Size

Prefer small capsules:

- role prompt: under 200 lines
- task envelope: under 120 lines
- stage reference: under 250 lines
- worker readable file list: usually under 8 files
- root Supervisor soft maximum: 200k tokens regardless of larger platform windows
- non-root replacement threshold: 70% of available context unless platform reports a safer lower threshold

If an agent needs more, create a task-local brief from durable artifacts rather than loading more global history.

## Multi-Agent Flow

For a value slice:

1. Orchestrator creates `.bagel/slices/VS-NNN.md`.
2. Evaluation Architect attaches acceptance metrics/rubric when the slice or iteration lacks them.
3. For existing projects, Orchestrator derives a task brief from `.bagel/agent_context/`.
4. Orchestrator assigns locks and branch/worktree.
5. Spec Reviewer checks slice clarity before implementation if ambiguity is high.
6. Implementer builds only that slice.
7. Runtime Doctor handles command/tooling failures if the implementer cannot run verification.
8. Spec Reviewer reviews changed files against slice spec and evaluation spec.
9. Code Quality Reviewer reviews changed files and tests.
10. Integration Manager/Orchestrator queues and merges only after checks pass.
11. Orchestrator updates project context if reality changed.
12. Orchestrator decides: accept, repair, clear debt, or escalate.
13. Orchestrator checkpoints and discards worker contexts.

For control-plane work:

1. Keep it out of the user-facing deliverable task queue.
2. Mark dispatch records with `lane_type: control_plane`.
3. Treat `.bagel/` setup as an autonomy enabler, not as product progress.
4. Do not count control-plane completion toward iteration all-green unless the active evaluation spec explicitly requires it as a verifier/reproducibility target.

For parallel work:

1. Verify tasks are path-disjoint and dependency-safe.
2. Create locks, branches/worktrees, and agent registry entries.
3. Dispatch workers with ownership boundaries.
4. Merge through queue, one integration at a time.
5. Refresh task briefs after shared state changes.

For review:

1. Apply risk/run mode review matrix.
2. Use the review level required by `references/quality-assurance.md`; medium/high risk unattended behavior changes need R3/R4. On Claude Code/Codex, prefer a real subagent to satisfy R3. If R3/R4 is genuinely unavailable, do not stop: downgrade the independence claim, isolate the change without merging, and continue safe independent high-EV work; wake the user only if no useful autonomous path remains.
3. Block merge on P0/P1 or missing evidence at required review level.

For a major uncertainty:

1. Orchestrator writes the uncertainty as a Missing Belief or ADR candidate.
2. Red-Team or reviewer attacks the options.
3. Orchestrator classifies the decision:
   - A logic-driven: decide and document.
   - B convention-driven: decide with evidence.
   - C taste-driven: create variants or ask user when high impact.
   - D philosophy-driven: user or Constitutional Court required.

## Independence Rules

Use independent agents for review and brainstorming after substantial skill changes or baseline/final candidate gates. Give them the artifact and a neutral task. Do not pass your diagnosis or intended fix unless the assignment requires it. If only same-session role switching is available, label it R1/R2 review, not independent review.

Good:

```text
Review this skill for long-run context hygiene and multi-agent drift risks.
```

Bad:

```text
Confirm that my new runtime protocol solves context pollution.
```

## Failure Smells

Revise prompts or workflow when you see:

- implementer asks to read entire history,
- reviewer approves based on explanation instead of files,
- orchestrator starts writing features,
- orchestrator repeatedly runs setup/build/test/debug commands instead of dispatching Runtime Doctor,
- BAGEL alignment/state/STATUS work appears in the user-facing deliverable task queue,
- an iteration starts without an Evaluation Architect evaluation spec or equivalent persisted criteria,
- court cites implementation difficulty,
- red team suggests fixes instead of findings,
- bar is raised from the orchestrator's own imagination without dispatching >= 2 lens-pinned brainstormers (converges on the obvious),
- a single brainstormer is dispatched where >= 2 were required, or brainstormers can see each other's output (destroys the diversity the role exists to manufacture),
- checkpoints contain prose but no next action,
- agent-facing project context is stale or absent for existing projects,
- lock overlap is unresolved,
- worker edited outside allowed scope,
- branch/worktree state is unknown,
- merge queue has unverified work,
- implementation was self-approved,
- unattended run merged medium/high risk work without the required R3/R4 review,
- repeated worker confusion about scope,
- old decisions re-litigated because ADRs are missing.
