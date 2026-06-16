---
name: bagel-genesis
description: "Use when Codex, Claude Code, or another agent must turn a vague high-level vision or an existing partially built project into an excellent finished deliverable through deep upfront alignment and long-running autonomous iteration. Use for: blank-slate builds, existing project takeover, autonomous optimization and iteration, research projects, writing projects, complex artifacts, multi-day autonomous work, project understanding synthesis, user-aligned decision discovery, architecture/narrative/argument drift prevention, quality gatekeeping, loop runtime design, and multi-agent orchestration. Do NOT use for: trivial scripts, quick fixes, narrowly specified tickets, or tasks where the user only wants a small code change."
---

# BAGEL Genesis

Turn a vague vision or an existing partially built project into an excellent finished deliverable by running a constraint-first, context-sparse, multi-agent build loop.

BAGEL Genesis is a skill-level operating protocol, not a monolithic prompt. V2 is the **Measured Autonomous Runtime**: it first performs deeper-than-native planning alignment, then runs an autonomous external loop that keeps improving the deliverable through continuous positive optimization while proving capabilities, replaying evidence, measuring context pressure, validating handoffs, controlling scope, and preventing governance-only progress. Persist only the smallest state needed to keep the run moving.

## Core Philosophy

BAGEL exists to turn user trust, time, and tokens into exceptional finished work through deep alignment followed by sustained autonomous execution. The workflow should expand the agent system's useful autonomy, not make it timid.

After the user explicitly delegates long-running autonomy, the default answer to friction is **continue**:

- repair the issue,
- create missing tools or verifiers,
- shrink the task,
- try an alternative implementation or theory,
- dispatch diagnosis/review/brainstorm subagents,
- work on another independent high-value task,
- improve setup, tests, UX, docs, experiments, or briefing,
- rollback the agent's own bad change and retry.

Do not idle, wait for routine approval, or stop early while useful work remains. A pre-final pause is allowed only for hard-stop boundaries: irreversible or non-recoverable destructive action, serious security/privacy/legal/financial/production-data risk, credentials or paid external resources, core product/research identity changes, or an explicit user-forbidden boundary. Everything else is an autonomy problem for the agent system to solve.

### Non-Overridable Tie-Breaker

When any rule, gate, review, uncertainty, missing tool, failed attempt, or platform limitation makes the agent inclined to stop and ask the user, continue instead unless the situation hits a hard-stop boundary above. If a lane cannot safely merge, isolate it and advance another positive-EV lane. If three cycles show no net progress, switch strategy rather than stopping.

### How to isolate a lane (works in all modes, no reference needed)

When the tie-breaker says "isolate," do this without stopping and without loading `full`-mode references:

1. Move the blocked change onto its own branch or worktree (e.g. `git worktree add ../.bagel-worktrees/<repo>/lane-<id> -b lane/<id>`). Never force-push, reset, or delete user changes.
2. Record the lane as `isolated` in `.bagel/state.yaml` under `blocked_lanes:` with: lane id, why it cannot merge (e.g. R3 unavailable, gate fail), the branch/worktree path, and residual risk.
3. Pick the next path-disjoint positive-EV task and continue the run on the main line.
4. Revisit isolated lanes when the blocker clears (review capacity returns, gate passes, tool becomes available) or at the next excellence-loop discovery pass.

If isolation itself would require a destructive or irreversible action (a true hard-stop), only then wake the user.

## Operating Rule

Load only the prompt needed for the current stage and role.

Do not paste this whole skill, all references, or all history into workers. On Claude Code/Codex with true subagents, the main model becomes the **Supervisor**: it handles user alignment, heartbeat, hard-stop arbitration, and Orchestrator respawn. It immediately spawns a fresh **Orchestrator** subagent/session to run BAGEL's internal workflow. The Orchestrator reads the minimum stage capsule, dispatches bounded subagents for all product code, tests, skeleton, runtime/tooling diagnosis, evaluation design, and review work, verifies returned artifacts, then saves durable state under `.bagel/`. Neither Supervisor nor Orchestrator writes product code while subagents are available.

`.bagel/` artifacts are the control plane, not the user's deliverable. Never put "create BAGEL alignment files", "fill constitution", "update STATUS", "run BAGEL checks", or other governance work into the user-facing product task queue or completion horizon. Governance work may appear only in state/ledger/dispatch records as control-plane tasks. The deliverable is the app, experiment, research result, document, site, or artifact the user asked for.

Before any long run or file modification, choose the lightest control plane that can keep the run safe and observable:

- `quick_autonomy`: default for existing projects, bounded modules, clear optimization/research goals, or user requests under roughly 500 words. Create only `.bagel/state.yaml`, `.bagel/constitution.yaml`, `.bagel/context.yaml` when needed, `.bagel/ledger.yaml`, and `.bagel/STATUS.md`; expand lazily only when the current task needs more structure.
- `full_genesis`: use for blank-slate products, multi-day autonomous builds, high-risk scope, broad project takeover, or when the user explicitly wants full governance. Create the detailed artifacts listed below as needed by each stage.
- `parallel_advanced`: enable locks, merge queue, agent registry, and git governance only when parallel write agents or multiple worktrees are actually active.

Run capability detection first. Prefer `scripts/detect_runtime_capabilities.py` when available, then read `references/runtime-capabilities.md` and the matching platform adapter only for gaps.

V2 capability rule: platform adapter claims are not proof. R3/R4 review, scheduled resume, hooks, and visual claims require `runtime_capabilities.capabilities.<name>.observed: true` plus a real `proof_ref` under `.bagel/evidence/runtime/`. If the proof is missing, keep working but downgrade the claim and repair the runtime substrate.

**Supervisor layer comes first on Claude Code/Codex.** If true subagents are available, load `references/supervisor-resilience.md`, bind a low-frequency Supervisor heartbeat, write `.bagel/supervisor/resume-capsule.md`, then spawn the inner Orchestrator from clean context. The Supervisor remains the user-facing proxy and last-resort recovery layer. If true subagents are unavailable, record `supervisor.mode: collapsed_no_true_subagents` and continue with the older main-as-Orchestrator model.

**Loop binding is immediate after capability detection.** The moment runtime capabilities are detected (and the user has expressed intent for autonomous work), bind the platform-native loop (`<= 25` min interval) *before* entering the Align phase. Alignment, project exploration, and baseline capture all happen *inside* the running loop, not before it. This ensures the run never enters a long Align/Explore phase with no wake mechanism - if the session is interrupted mid-alignment, the loop brings it back. Do not defer loop binding to "when Build starts"; by then the run may have spent an hour unprotected. See `references/loop-runtime.md` Start Gate.

Before any file modification in an autonomous run, guarantee the working folder is a git repository (`git rev-parse --is-inside-work-tree`). If it is not, initialize one (see `references/git-governance.md` Step 0) or refuse to start autonomous write work. Version control is the precondition for rollback and branch isolation; without it every overnight change is irreversible. The `project_under_version_control` hard gate enforces this.

If a platform cannot support timers, true subagents, or automatic resume after exhausting every native mechanism named in the platform adapter, record `degraded_resume` and mark `.bagel/STATUS.md`. Continue useful work in the current session and write a durable resume plan instead of stopping early. `degraded_resume` is a marked downgrade, never an equal mode - never present it as successful autonomous iteration.

Autonomy is the default reason this skill exists. On Claude Code or Codex, first try to bind BAGEL to the platform-native loop, scheduling, subagent, hook, worktree, browser, computer-use, cloud, and non-interactive capabilities described in `references/platform-claude-code.md` or `references/platform-codex.md`. Treat missing local verifiers, screenshots, test scripts, environment setup, or experiment harnesses as work for the agent system to create inside the autonomy contract, not as a reason to stop.

## Roles

After loading this skill, the main model **adopts the Supervisor role** when true subagents are available, then spawns a BAGEL Orchestrator subagent/session. All product code, tests, skeleton, runtime diagnosis, evaluation design, and independent review **must be dispatched below the Orchestrator** (Claude Code Task tool / custom subagent, Codex subagent / custom agent). Doing implementation directly while subagents are available is the #1 failure smell (see `references/agent-operating-model.md`). Only if the platform truly has no subagent capability may the main model collapse into the Orchestrator role - and then independent review must be downgraded and recorded as non-independent (R1 max), never presented as R3.

| Role | Reads | Writes | Must Not Do |
|---|---|---|---|
| Supervisor | user messages, `.bagel/supervisor/*`, constitution/state/status summaries | user-intake, heartbeat, resume capsule, respawn log | implement, debug, review, or run normal slice loop |
| Orchestrator | `.bagel/state.yaml` (quick) or `state.json` (full); `.bagel/constitution.yaml` (quick) or `constitution.json` (full); current stage capsule | state, ledgers, dispatch envelopes | write product code |
| Artifact Drafter | vision notes, current stage schema | `.bagel` governance artifacts | write product code |
| Project Cartographer | repository/artifact evidence, current behavior, docs | agent-facing project understanding | change product behavior |
| Evaluation Architect | constitution, artifact profile, baseline evidence, target set | evaluation specs, metrics, rubrics | implement, approve, or choose product direction |
| Runtime Doctor | failed command, logs, runtime facts, allowed paths | environment/tooling repair handoff + evidence | change product behavior or lower gates |
| Skeleton Builder | architecture brief, route map, contracts | skeleton code, typed stubs, contract tests | implement real value slices |
| Implementer | assigned slice spec, relevant contracts, local code files | code and tests for one slice | read full skill/history, change product scope |
| Spec Reviewer | slice spec, changed files, contracts | review report | propose new product ideas |
| Code Quality Reviewer | changed files, local patterns, test output | review report | reinterpret vision |
| Independent Reviewer | task spec, diff, tests, risk profile | merge-blocking review | rely on implementer explanation |
| Integration Manager | merge queue, branches, locks, reviews, verification | integrated changes, conflict reports | implement features broadly |
| Constitutional Court | constitution, proposed amendment, evidence | accept/reject amendment | consider implementation difficulty as justification |
| Red-Team Oracle | constitution, decisions, baseline/final candidate | adversarial findings | fix issues directly |
| Brainstormer | constitution + taste kernel, current artifact, progress-deltas, state.excellence | improvement ideas under ONE assigned lens | read other brainstormers' output, propose implementation, work outside assigned lens |
| Product Visionary | constitution, taste kernel, artifact state, progress evidence | divergent concept candidates + falsifiable probes | implement, review, or mutate the constitution directly |
| Judgment Councilor | one decision, one judgment dimension, constitution, proposal evidence | dimension verdict for Judgment Council | generate ideas, implement, or see other councilors' verdicts |
| User Alignment Curator | alignment artifacts, decision ledger, progress state | STATUS.md narrative sections + HTML dashboard + user_briefing/ | hide risks or unresolved decisions, write STATUS.md mechanical sections

Role prompts live in `agents/`. Give an agent one role prompt plus one task envelope; do not give it other role prompts.

### Per-role reference budget

A worker should not browse the `references/` directory freely. The orchestrator puts only the triggered references (per the Loading Matrix) into the dispatch envelope. Default per-role ceilings:

| Role | May read from references/ | Ceiling |
|---|---|---|
| Supervisor | supervisor-resilience, alignment-protocol, platform adapter | 2-3 |
| Orchestrator | any triggered by the Loading Matrix | unrestricted, but one decision loads one row |
| Project Cartographer | project-understanding, artifact-types | 2 |
| Evaluation Architect | evaluation-framework, artifact-types | 2 |
| Runtime Doctor | runtime-capabilities, platform adapter only if needed | 1-2 |
| Skeleton Builder | ghost-ship-gate, artifact-types | 2 |
| Implementer | none beyond its envelope (quality-assurance only if writing tests) | 0-1 |
| Spec / Code Quality / Independent Reviewer | quality-assurance, gate-predicates | 1-2 |
| Red-Team Oracle | quality-assurance, recovery-protocol (adversarial lens) | 1-2 |
| Constitutional Court | constitutional-court, constitution-template | 1-2 |
| Brainstormer | none beyond its envelope (excellence-loop only if ranking ideas) | 0-1 |
| Product Visionary | innovation-protocol | 1 |
| Judgment Councilor | taste-judgment only | 1 |
| User Alignment Curator | user-briefing, alignment-protocol | 1-2 |

If a worker's task cannot be completed within its ceiling, the orchestrator derives a compact brief and puts that in the envelope instead of widening the ceiling. This is how "read strictly when needed, do not read otherwise" stays enforceable.

## Durable State

Default quick control state under `.bagel/`:

```text
.bagel/
├── state.yaml          # run mode, current phase, task queue, gates, budget, progress
├── constitution.yaml   # vision, completion horizon, excellence horizon, autonomy contract, taste kernel
├── context.yaml        # current project facts, conventions, module map, feature inventory
├── ledger.yaml         # decisions, recovery, evolution, rejected improvements, user decisions
├── STATUS.md           # human-readable live progress
├── supervisor/         # heartbeat, resume capsule, user proxy, respawn log
├── evidence/
│   └── progress-deltas.yaml
├── telemetry/
│   └── cycles.yaml
├── handoffs/
├── actions/
├── scope/
├── innovation/
└── lessons/
```

Expand to detailed state only when it pays for itself. Full mode may create:

```text
.bagel/
├── constitution.json
├── completion_horizon.yaml
├── taste_kernel.yaml
├── coherence_rules.yaml
├── state.json
├── STATUS.md
├── supervisor/
├── run_mode.yaml
├── runtime_capabilities.yaml
├── artifact_profile.yaml
├── schema-registry.yaml
├── context_policy.yaml
├── vision_summary.md
├── alignment/
├── agent_context/
├── user_briefing/
├── project_inventory/
├── evolution/
├── git/
├── agents/
├── gates/
├── excellence_horizon.yaml
├── task_queue.json
├── progress.json
├── decisions/
├── evidence/
├── missing_beliefs/
├── slices/
├── product_graph.yaml
├── contracts/
├── stubs/
├── reviews/
├── redteam/
├── simulations/
├── ledger/
├── snapshots/
├── crystals/
├── innovation/
└── lessons/
```

Treat `.bagel/` as the memory, not the conversation transcript. Save decisions, evidence, open risks, gate results, and next actions. Do not save chain-of-thought or long narrative logs.

## Workflow

Use the phase loop by default. The numbered state machine is the full-mode expansion, not a mandatory waterfall for every task.

```text
Align: use choice prompts, open prompts with neutral guidance, and project-evidence veto drafts to make the vision executable. Do not treat BAGEL alignment/governance artifacts as user deliverables.
Build: evaluation spec -> slice -> implement -> verify -> record progress delta -> next slice.
Iterate: finish current target set -> record iteration -> generate higher-value target set -> continue until max_iterations/budget/user/hard-stop.
Polish: critique -> improve -> verify -> record progress delta -> next highest-EV pass.
```

## Loading Matrix (authoritative)

This single table replaces all scattered "load X when Y" instructions. **Read the row only when its trigger is true.** When a trigger is true, open that file and read it strictly and completely for the decision at hand — do not skim. When the trigger is false, do not load it. The `quick?` column says whether the file is needed in `quick_autonomy` mode: `always` = load when triggered even in quick mode; `full` = skip in quick mode unless the trigger is a hard gate failure.

| File | Read strictly when... | Do not load when... | quick? |
|---|---|---|---|
| `references/alignment-protocol.md` | entering Align phase; conducting any user alignment conversation | already aligned and constitution locked | always |
| `references/supervisor-resilience.md` | Claude Code/Codex true subagents are available; handling compaction/resume/new conversation; spawning or respawning Orchestrator; translating user instructions into BAGEL state | single-session work with no long-run autonomy or no true subagent support | always |
| `references/platform-claude-code.md` / `references/platform-codex.md` | detected platform is CC/Codex and you must bind dispatch, subagents, hooks, loop, resume, or visual checks to native capabilities | platform is other, or run is single-session with no native loop needed | always |
| `references/runtime-capabilities.md` | before first autonomous cycle; before promising timers/resume/subagents | capabilities already detected and recorded in state | always |
| `references/v2-measured-runtime.md` | configuring or repairing V2 validators, evidence replay, telemetry, idempotent resume, or measured-autonomy checks | doing a one-off non-autonomous task | always |
| `references/telemetry-protocol.md` | recording cycle telemetry, governance budget, context pressure, or deliverable/control-plane delta | no autonomous cycle has started | always |
| `references/evidence-protocol.md` | recording command, benchmark, screenshot, experiment, or metric evidence | no evidence claim is being made | always |
| `references/handoff-integrity.md` | replacing Orchestrator/worker/helper, resuming from new conversation, or validating idempotency | no replacement/resume/action boundary exists | always |
| `references/scope-control.md` | dispatching or merging any write task with allowed paths/dependencies/sensitive surfaces | read-only analysis only | always |
| `references/alignment-freshness.md` | iteration end, user instruction change, taste-sensitive work, final delivery, or direction change | alignment is fresh and no taste-sensitive change occurred | always |
| `references/reference-loading.md` | diagnosing over-reading or updating reference digest telemetry | short single-cycle work with no reference telemetry | full |
| `references/start-prompts.md` | user asks how to launch BAGEL or needs a copy-paste start prompt | an active run is already aligned and started | full |
| `references/packaging-boundary.md` | packaging/releasing the skill or deciding whether README is runtime context | normal run execution | full |
| `references/artifact-types.md` | choosing gates or QA for a new artifact type (software / research / writing / data) | artifact type already profiled and recorded | always |
| `references/evaluation-framework.md` | generating or refreshing metrics/rubrics for an iteration, slice, research hypothesis, UI polish pass, strategy switch, or final delivery | a fresh active evaluation spec already covers the decision | always |
| `references/project-understanding.md` | workspace is non-empty and you will modify existing behavior | blank-slate build | full |
| `references/constitution-template.md` | drafting or amending the constitution | constitution exists and is stable | always |
| `references/coherence-rules.md` | defining taste/style/UX/writing/research gates for the artifact | gates already defined in constitution.taste_kernel | full |
| `references/missing-belief-discovery.md` | in Align/Build when a product or research belief is unresolved and could change scope | all P0/P1 beliefs are explicit | full |
| `references/upmg-schema.md` | modeling a complex multi-component product graph | product is simple enough for a flat slice list | full |
| `references/ghost-ship-gate.md` | building a software skeleton and verifying end-to-end runnability before filling value | non-software artifact, or no skeleton needed | full |
| `references/quality-assurance.md` | choosing run mode, review level, risk class, or verification strategy for a change | doing pure alignment/governance work with no artifact change | always |
| `references/gate-predicates.md` | checking, failing, waiving, or recording any hard gate | no gate check is due this cycle | always |
| `references/governance-data-model.md` | creating, validating, or migrating `.bagel/` state file schemas | state files already conform | full |
| `references/clearing-policy.md` | finishing a value slice and before starting the next | mid-slice, or pure polish work | full |
| `references/rework-sandbox.md` | isolating a risky change in a worktree/sandbox branch | change is small and reversible in-place | full |
| `references/simulations.md` | running scenario/deterministic user-flow checks on a built artifact | artifact is not yet runnable | full |
| `references/excellence-loop.md` | baseline passes and you enter Polish; ranking improvement tasks by EV; **or experiment/research results are poor or stalled (lateral/backward deltas) and you need to decide whether to switch hypothesis vs keep iterating** | still in Build phase before baseline, with no polish/stall decision pending | always |
| `references/iteration-contract.md` | starting, completing, partially completing, counting, pushing, or raising targets for an iteration | doing a single worker task inside an already-defined iteration | always |
| `references/taste-judgment.md` | selecting innovation survivors, choosing a bar-raise direction, switching strategy after lateral cycles, final delivery acceptance, or constitution-level direction changes | routine reversible implementation or mechanical telemetry | always |
| `references/collective-decisions.md` | a high-impact decision needs multiple independent perspectives or you are deciding whether multi-agent judgment is warranted | ordinary slice implementation, naming, test details, or mechanical deltas | always |
| `references/orchestration-flow.md` | deciding what stage/dispatch/merge rule comes next in a long autonomous run | a single local task is already clearly in progress | always |
| `references/innovation-protocol.md` | user asks for innovation/novelty/wow; blank-slate product needs concept exploration; bar-raising or recovery has locally converged; or `innovation_contract.ambition` is differentiated/breakthrough | execution-only task with a locked concept and no plateau | always |
| `references/lesson-memory.md` | recovery occurred; the same failure recurred; environment/tooling was repaired; a reviewer finding repeats; or a useful workaround should persist across runs | no recovery/learning trigger this cycle | always |
| `references/loop-runtime.md` | configuring a multi-cycle unattended loop, checkpoint cadence, or quota/resume | single-session work that finishes in one cycle | full |
| `references/runtime-protocol.md` | handling context compaction, checkpointing, snapshot/resume, or cross-platform long runs | run is short and fits one session | full |
| `references/recovery-protocol.md` | drift, repeated bug, tool/env failure, a gate fails 3×, **or three consecutive lateral progress deltas on the same approach (see excellence-loop stop criteria)** | work is progressing cleanly with forward deltas | always |
| `references/constitutional-court.md` | a proposed scope reduction, identity change, or P0 removal appears | no scope/identity amendment is proposed | always |
| `references/evolution-ledger.md` | recording a meaningful change for audit/rollback, or diagnosing a regression | change is trivial (typo, comment) | full |
| `references/user-briefing.md` | updating the human-facing briefing layers or STATUS.md beyond the quick template | no user-visible change or decision this cycle | always |
| `references/alignment-dashboard-html.md` | user wants visual/HTML briefing, alignment needs a dashboard, or long-run status should be inspectable at a glance | Markdown STATUS is sufficient and user did not request HTML | always |
| `references/alignment-information-architecture.md` | designing or repairing the progressive-disclosure capsule/context-index system | quick mode with a flat context.yaml suffices | full |
| `references/agent-operating-model.md` | the skill has just been loaded (binds the main model to the Orchestrator role + Separation Principle + failure smells); or designing/rewriting a role prompt in `agents/` | never - the Separation Principle binds from run start | always |
| `references/git-governance.md` | before the first file modification of any autonomous run (Step 0 repo guarantee); or multiple write agents/worktrees are active (parallel_advanced) | run has not yet reached any file-writing phase | always |
| `references/multi-agent-coordination.md` | dispatching more than one worker concurrently with dependencies or shared files | single-agent serial work | full |
| `references/state-machine.md` | you need the full detailed S-2..S17 transition logic (full_genesis only) | running quick phase loop | full |
| `references/crystals.md` | extracting a reusable decision pattern after a successful build, with user opt-in | never loaded by default; opt-in only | full |

**Discipline rules for this matrix:**

- When a trigger fires, read the whole file for the decision at hand. Do not skim the heading and guess.
- When no trigger fires, do not load the file "just in case." Idle reads cost tokens and dilute attention.
- **Read-once caching:** several `always` files (runtime-capabilities, platform adapters, artifact-types, constitution-template) establish stable facts that do not change cycle-to-cycle. Read them once at run start, record the key facts into `.bagel/state.yaml` or `.bagel/constitution.yaml`, and consult the recorded facts on later cycles instead of re-reading the file. Only re-read if the underlying capability/artifact type actually changes.
- The per-cycle `always` files (quality-assurance, gate-predicates, recovery-protocol, excellence-loop) contain decision rules that apply every cycle — read them when their decision is due, not proactively.
- In `quick_autonomy`, the `full` rows are skipped unless a hard gate fails or the run escalates to `full_genesis`.
- If a worker needs content from a file not in its dispatch envelope, it must request a smaller derived brief, not the whole file (see Dispatch Envelope).

**Token-budget awareness:** governance overhead must stay proportionate to the task. For a quick_autonomy task touching one module, the orchestrator should spend well under 30% of the cycle on governance reads/writes; the rest goes to the product artifact. If governance consumes most of a simple task's budget, you are over-reading — cache more, read fewer rows.

## Blank Project vs Existing Project

If the workspace is not empty, do not treat it as a blank slate. First choose takeover scope:

- `limited_takeover`: one module, artifact, feature, or optimization target; create only the context needed for that scope.
- `full_takeover`: project-wide autonomous build/optimization; create the full context package below.

Record target root, excluded directories, allowed `.bagel/` location, discovery budget, and user/user-delegated approval. In `quick_autonomy`, store this in the `takeover_scope:` section of `.bagel/context.yaml`. In `full_genesis`, store it in `.bagel/project_inventory/takeover-scope.yaml`. Before changing behavior, create evidence-backed project understanding proportional to the takeover scope.

For existing projects, do not ask the user to explain facts the repository can reveal. Run project discovery first, draft protected vs. replaceable surfaces from evidence, then ask the user only to veto or correct intent-sensitive classifications.

**`quick_autonomy` (store compactly inside `.bagel/context.yaml`):** a `project_facts:` block (concise facts workers need), a `conventions:` block (local patterns, naming, test norms, style), a `module_map:` block (important modules, ownership, integration points), a `feature_inventory:` block (what exists / partial / missing), a `do_not_duplicate:` block (existing utilities to reuse), and a `current_behavior:` note (verified behavior and known gaps). One file, short sections.

**`full_genesis` (detailed separate files):**

- `.bagel/agent_context/project-facts.yaml`: concise facts workers need.
- `.bagel/agent_context/global-capsule.yaml`: small whole-project map loaded often.
- `.bagel/agent_context/context-index.yaml`: routes topics to deeper capsules.
- `.bagel/agent_context/freshness.yaml`: marks context fresh, stale, or disputed.
- `.bagel/agent_context/conventions.md`: local patterns, naming, architecture, test norms, style rules.
- `.bagel/agent_context/module-map.md`: important modules, ownership, responsibilities, integration points.
- `.bagel/agent_context/feature-inventory.md`: what already exists, what is partial, what is missing.
- `.bagel/agent_context/do-not-duplicate.md`: existing utilities/components/services to reuse.
- `.bagel/agent_context/current-behavior.md`: verified current behavior and known gaps.
- `.bagel/project_inventory/evidence.md`: commands, files, docs, and observations supporting the above.

These are agent-facing control documents. They must be short, factual, and continuously updated so future workers do not rediscover the repo or accidentally rebuild existing systems.

## Alignment Before Autonomy

Do materially more upfront alignment than native plan modes - this is enforced by depth floors in `references/alignment-protocol.md`: standard requires all 8 choice cards + >= 3 open questions; deep requires >= 2 rounds, >= 8 total questions, all 8 cards + >= 5 open questions. The constitution is not locked (and Build must not start) until the floor for the selected depth is met. Before autonomous implementation, capture the alignment content below. In `quick_autonomy`, store it compactly inside `.bagel/constitution.yaml` (vision/taste/non-goals/assumptions), `.bagel/ledger.yaml` (decisions/human-decisions), and `.bagel/STATUS.md` (briefing); you do not need the separate files. In `full_genesis`, produce and review the detailed files:

- `.bagel/alignment/vision-canon.md` (full) **or** the `vision:`/`taste:`/`non_goals:`/`assumptions:` sections of `.bagel/constitution.yaml` (quick): user intent, taste, success definition, non-goals, hidden assumptions.
- `.bagel/agent_context/project-facts.yaml` (full, existing projects) **or** the `project_facts:` section of `.bagel/context.yaml` (quick): the current true project state.
- `.bagel/alignment/decision-map.yaml` (full) **or** the `decisions:` section of `.bagel/ledger.yaml` (quick): decisions made, delegated, or requiring consensus.
- `.bagel/alignment/human-decisions.yaml` (full) **or** the `human_decisions:` section of `.bagel/ledger.yaml` (quick): approval status for autonomy-sensitive decisions.
- `.bagel/alignment/autonomy-contract.yaml` (full) **or** the `autonomy_contract:` section of `.bagel/constitution.yaml` (quick): what the system may decide alone, how it challenges user instructions, when to wake the user.
- `.bagel/user_briefing/README.md` (full) **or** `.bagel/STATUS.md` (quick): layered project explanation.
- `.bagel/excellence_horizon.yaml` (full) **or** the `excellence_horizon:` section of `.bagel/constitution.yaml` (quick): the **starting** quality bar — meeting it is the signal to raise the bar, not to stop (see `references/excellence-loop.md` Bar-Raising Protocol).

If the user's instruction conflicts with project reality, do not silently comply. Explain the risk, propose alternatives, reach consensus, then persist the decision.

Maintain two different alignment surfaces:

- Agent-facing context in `.bagel/agent_context/`: compact operational truth for future agents.
- Human-facing briefing in `.bagel/STATUS.md` and `.bagel/user_briefing/`: layered explanation for user trust, decisions, and handoff. `.bagel/STATUS.md` is the single human entry point.

Both surfaces use progressive disclosure. Agents get a global capsule plus a task/domain capsule, not the whole project model. Users get quick status, decision dashboard, evolution summary, and deep dives.

## Vision Intake

Start with a deep alignment conversation, not a build. Do not proceed until these are explicit:

- North star: one sentence that names the product and the core value.
- Primary users and excluded users.
- Must-have value slices or artifact sections for the baseline deliverable.
- Forbidden directions and non-goals.
- Constraints: platform, integrations, privacy, budget, deadline, deployment target.
- Autonomy policy: what the agent may decide alone and what requires the user.
- Excellence horizon: the quality level expected after autonomous iteration, including polish, robustness, documentation, and "no obvious improvement remains" criteria.
- Long-run delegation: whether the user wants maximum autonomous momentum, how much time/token budget to spend, and which hard-stop boundaries remain non-negotiable.
- Execution strategy: `fast_parallel`, `balanced_parallel`, or `stable_long_run`.
- Alignment depth: `snap_alignment`, `standard_alignment`, or `deep_alignment`. Once chosen, the run must reach that depth's floor (see `references/alignment-protocol.md` Run-Mode Depth) before entering Build; the `constitution_approved` gate enforces this.
- Innovation ambition: whether the system should optimize the supplied concept, differentiate it, or spend explicit budget on breakthrough-level concept probes.
- **Stop Contract (MANDATORY — see `references/alignment-protocol.md` Stop Contract):** persist as `stop_contract` with max_iterations (hard ceiling), budget_limit (available_night / strict_cap / baseline_first), hard_stops (what wakes the user), within_autonomy (what does NOT stop the run), morning_return (what the user wants to see), deadline (wall-clock or none). The run must not bind the loop or enter Build until the Stop Contract is captured in `.bagel/constitution.yaml`. This is the single most important alignment artifact — it defines when the overnight run ends.
- Briefing format: Markdown only or optional HTML dashboard, plus update frequency.

Use `references/alignment-protocol.md` for the question tree and choice cards. When the platform supports structured user choices, use them for autonomy level, run budget, takeover aggressiveness, taste source, research verification, and hard-stop boundaries. For open questions, include why the question matters, neutral examples, and the default if skipped.

Write `.bagel/vision_summary.md`, then `.bagel/constitution.yaml` (quick) or `.bagel/constitution.json` (full), and `.bagel/completion_horizon.yaml`. If the user has granted long-run delegation, bind loop/timer capability before implementation and continue without stopping; record the canon in `.bagel/alignment/human-decisions.yaml` and surface it in the user briefing for later review. Only pause for S1 confirmation when a hard-stop boundary is unresolved (core promise, privacy/legal/financial/safety posture, target audience, production data, credentials/paid resources, or an irreversible direction).

## Context Policy

Create `.bagel/context_policy.yaml` before long implementation:

```yaml
context_policy:
  orchestrator_context:
    keep: [current_state, constitution, completion_horizon, current_gate, next_3_actions]
    reload_every_transition: [constitution, state]
    avoid: [full_history, old_logs, worker_transcripts]
  worker_context:
    max_files_read: 8
    task_budget: one_slice_or_smaller
    discard_after: report_saved
    must_consult_when_existing_project: [agent_context/project-facts.yaml, agent_context/conventions.md, relevant module-map excerpt]
    cannot_read: [full_skill, full_references_directory, unrelated_slices, activity_log]
  checkpointing:
    after: [state_transition, value_slice, gate_failure, amendment, baseline_candidate, final_candidate]
    save: [state_json, progress_json, evolution_change_record, decision_records, human_decisions, gate_status, review_reports, test_commands, open_risks, next_action, agent_context_freshness, user_briefing]
  quality:
    run_mode: unattended_stable
    review_matrix: references/quality-assurance.md
    no_self_approval: true
  git_and_agents:
    required_for_parallel_work: [.bagel/git/locks.yaml, .bagel/git/branches.yaml, .bagel/git/merge-queue.yaml, .bagel/agents/registry.yaml]
    merge_owner: orchestrator_or_integration_manager
    worker_may_merge: false
```

Hard rule: context that is not needed for the next decision should become an artifact or be dropped.

## Dispatch Envelope

Every worker receives a bounded envelope:

```text
ROLE: Implementer
AGENT_ID: agent-impl-vs003
STATE: S8
TASK: Implement VS-003 only.
BRANCH_OR_WORKTREE:
- ../.bagel-worktrees/repo/RUN-001/VS-003
LOCKS:
- LOCK-001
READ ONLY:
- .bagel/constitution.json
- .bagel/agent_context/project-facts.yaml
- .bagel/agent_context/conventions.md
- .bagel/slices/VS-003.md
- .bagel/contracts/billing.ts
- src/billing/*
WRITE ONLY:
- src/billing/*
- tests/billing/*
EXIT CRITERIA:
- listed requirements pass
- tests added and run
- no scope change
RETURN:
- status: DONE | BLOCKED | NEEDS_CONTEXT
- files_changed
- commands_run
- open_risks
- scope_expansion_requests
- context_update_proposals
- gate_predicate_results
```

If a worker asks for broad history, narrow the task or generate a smaller artifact. Do not satisfy the request by dumping the transcript.

For existing projects, every dispatch must include the relevant agent-facing project context or a task-local brief derived from it. Do not make each worker rediscover the codebase from scratch.

Every dispatch should cite the context capsule versions used. If a worker discovers mismatched or stale context, it must report proposed context updates instead of silently working around it.

## Hard Gates

Block progress when any predicate in `references/gate-predicates.md` fails. Record results in `.bagel/gates/status.yaml` (full) or in the `gates:` section of `.bagel/state.yaml` (quick). Core predicates:

- `constitution_approved`
- `project_understanding_current`
- `evolution_record_present`
- `context_fresh_for_dispatch`
- `parallel_ownership_safe`
- `worker_did_not_merge`
- `review_level_satisfied`
- `rollback_point_present_for_risk`
- `merge_inputs_clean`
- `typed_contracts_present_when_required`
- `skeleton_gate_passed_when_required`
- `artifact_specific_slice_coverage_present`
- `decision_mutations_cleared`
- `red_team_blockers_resolved`
- `scope_reduction_authorized`
- `project_under_version_control`
- `flywheel_integrity_passed`
- `no_regression_vs_green_floor`
- `metric_delta_has_evidence_artifact`
- `review_level_consistent_with_registry`
- `bar_raise_has_value_class`
- `runtime_capability_observed_with_proof`
- `handoff_validation_passed`
- `action_idempotency_safe`
- `evidence_replay_integrity_passed`
- `governance_budget_respected`
- `scope_delta_within_contract`
- `alignment_freshness_current`

After repeated failures of the same gate, enter autonomous recovery within the permissions listed in `references/recovery-protocol.md`: shrink the task, isolate in a worktree, dispatch a diagnostic reviewer, brainstorm alternatives, try another implementation/research/design path, perform local repairs, create missing verifiers, or roll back and retry from the last valid checkpoint. Wake the user only for hard-stop boundaries: irreversible or non-recoverable destructive action, serious security/privacy/legal/financial/production-data risk, credentials or paid external resources, core identity changes, explicit forbidden boundaries, or genuine impossibility after useful alternatives are exhausted. Always write `.bagel/ledger/recovery-log.md` (full) or append to the `recovery:` section of `.bagel/ledger.yaml` (quick).

## Long-Run Loop

For long autonomous work, run in cycles:

1. Re-anchor: read constitution and state.
2. Select one bounded next action.
3. Load only the stage capsule and role prompt needed.
4. Execute or dispatch.
5. Verify with tests/reviews/gates.
6. Write a progress delta in `.bagel/evidence/progress-deltas.yaml`.
7. Update `.bagel/STATUS.md` with: run status, current focus, timeline, budget allocation, latest delta assessment, recent autonomous decisions, blocked lanes, and next action. See `references/runtime-protocol.md` for the full template.
8. Update loop telemetry: elapsed time, cycles, agents dispatched, compactions, recovery events, timer wakeups, tests, screenshots, token estimate when available.
9. Run `python scripts/bagel_v2_check.py <project-root>` as the main validator. It calls the operational, flywheel, memory, telemetry, handoff, evidence replay, scope, alignment freshness, and reference-load checks.
10. Treat any V2 check failure as a gate failure: repair evidence/state, rollback or isolate a bad change, dispatch the missing agent/reviewer/curator, validate a handoff, or switch strategy before continuing.
11. Persist structured output.
12. Replace non-root context when pressure rises: write handoff, validate it, dispatch a fresh child. Do not routine-compact Orchestrator/workers.
13. Continue, switch strategy, or wake later depending on platform support.

If the current task cannot progress, use the tie-breaker. Select the next best autonomous action: repair, diagnose, provision tools, create a verifier, reduce scope, rollback agent-owned changes, explore alternatives, or advance another high-value independent task. The run should keep converting time and tokens into verified value until final completion, budget exhaustion, user stop, or a hard-stop boundary.

On Codex, Claude Code, or another platform, use only capabilities detected in `.bagel/runtime_capabilities.yaml`, but do not under-detect platform-native autonomy. On Codex and Claude Code, attempt every native loop mechanism in the platform adapter (in priority order) before falling back to `degraded_resume`; only record `degraded_resume` after all native mechanisms are proven unavailable, and mark STATUS.md `[DEGRADED]`. When no timer exists, end each cycle with a durable checkpoint and a single next command/action so another agent can resume without the transcript. If true multi-agent isolation is unavailable, downgrade independent review claims according to `references/quality-assurance.md`.

## Completion

The deliverable is not complete because it runs once. Baseline completion is only the start of the excellence loop.

Baseline completion requires:

- completion horizon passes,
- all P0/P1 value slices run end-to-end,
- tests and contract checks pass,
- artifact can be locally run/read/used and, if requested, deployed or published,
- red-team P0/P1 findings are resolved,
- stub/mock/placeholder registry is closed or explicitly accepted,
- user briefing is updated.

Final delivery requires the excellence horizon too:

- multiple independent critique/ideation/review passes find no unresolved P0/P1/P2 issue with positive expected value,
- all meaningful improvements within the autonomy contract and budget have been attempted or intentionally rejected with rationale,
- environment/setup/reproducibility is verified,
- user-facing briefing explains the project at quick, standard, and deep levels,
- final report includes what was built, how to verify it, decisions made autonomously, residual risks, and suggested future directions.

Do not stop merely because the baseline runs — that is the start of the excellence loop, not the end. In delegated long-run mode the run continues through continuous positive optimization (generating and raising standards, see `references/excellence-loop.md`) until: budget/token capacity is exhausted with a resume checkpoint (the normal, expected end state), the user stops it, a hard-stop boundary requires a pause, or the stringent anti-laziness Stop Criteria bar is met (genuine optimization exhaustion independently confirmed). Stopping early while measurable improvement remains possible is a failure.
