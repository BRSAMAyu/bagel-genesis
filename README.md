# BAGEL Genesis

> Deep upfront alignment + long-running autonomous iteration for Claude Code, Codex, and similar agentic coding systems.

**English** | [简体中文](README.zh-CN.md)

---

## The one-paragraph pitch

A bare agent stops at the first ambiguity, drifts as its context grows, rubber-stamps its own work, and calls "it runs" done. BAGEL Genesis is a skill-level operating protocol that makes an agent **keep working for hours after you go to sleep** — aligning deeply first, then driving a continuous positive-optimization loop where every quality bar, once met, gets *raised* rather than declared finished. The difference from a long prompt is that the load-bearing guarantees are **verified by scripts, not self-reported**: progress deltas must cite real evidence files, independent review is *derived from registry state*, regressions below a green floor fail the cycle, and a flat-spin detector catches a loop that's "working hard" without actually climbing.

## What's new in v1.1

Four mandates tighten the overnight contract, all mechanically lint-checked:

- **Mandatory loop, max 25 min.** Before the first autonomous cycle the agent *must* bind a platform-native loop (`/loop`, scheduled task, Codex automation, `codex exec`+cron) with an interval ≤ 25 minutes, and keep it bound until the run ends. `degraded_resume` is a marked fallback only after every native mechanism is proven unavailable.
- **Mandatory git.** The working folder must be a git repo before any file is modified — `git init` + baseline commit if needed, enforced by the `project_under_version_control` hard gate. Without it, rollback and branch isolation are impossible.
- **Mandatory dispatch.** After loading the skill, the main model *adopts the Orchestrator role* and dispatches all product code/tests/review to subagents. It writes only `.bagel/` governance artifacts. Doing implementation itself is the #1 failure smell.
- **Depth-floored alignment.** `standard` requires all 8 choice cards + ≥ 3 open questions; `deep` requires ≥ 2 rounds, ≥ 8 questions. The fast-path 4 questions are valid *only* in `snap`.

Plus an **information-architecture upgrade** built on one axiom — *context is the resource to protect*:

- **Context-Isolation Axiom:** a separate subagent call *is* a separate context. Workers share *findings* (structured, artifact-grounded), never *reasoning* (chain-of-thought, design debate).
- **Brainstormer role:** ≥ 2 lens-pinned, isolated-context agents dispatched before every bar-raise, so insight diversity is *manufactured* rather than hoped for.
- **STATUS.md ownership split:** the orchestrator writes mechanical data (telemetry, deltas, gates); the Curator writes narrative (Morning Briefing, risks) and owns the HTML dashboard exclusively.
- **Orchestrator firewall:** widened to block implementation reasoning from entering the coordinator's context — not just "long transcripts."

## What's new in v1.2

Three fixes to the *operational substrate*, found by watching a real run:

- **Verify, don't trust (exploration).** The Cartographer no longer accepts documentation claims. It must run actual commands (build/test/lint), grep real code, and record `documented_but_broken` when docs lie. Existing `.bagel/` context is a *hint to re-verify*, never truth. The orchestrator dispatches ≥ 2 exploration subagents (structure/behavior/convention/surface lenses) that cross-verify each other before context is written. `bagel_run_check.py` now fails a run that reached Build with no real command outputs in `.bagel/evidence/baseline/` — catching the "trusted stale docs" failure mode.
- **Immediate loop binding.** The loop is bound *immediately after capability detection*, before the Align phase — not deferred to "when Build starts." Alignment and exploration happen inside the running loop, so a session interruption mid-alignment doesn't lose the run.
- **Pointer-only wake prompts.** The loop wake prompt was reduced from 5 lines of mechanism instructions to a 1-sentence pointer: *read STATUS.md + state.yaml, then follow SKILL.md.* Mechanism in the wake prompt causes repetition pollution every cycle, drift from SKILL.md, and token waste. The agent progressively discloses what it needs after waking — it doesn't reload the whole skill.

---

BAGEL Genesis is a skill-level operating protocol for turning a vague vision or a partially built project into a finished, high-quality deliverable. It is designed for the common workflow where you align with an agent before bed, delegate a difficult task, and expect the system to keep working instead of stopping at the first ambiguity.

It is not a single mega-prompt. It is a structured skill with:

- an entry point: [`bagel-genesis/SKILL.md`](bagel-genesis/SKILL.md)
- role prompts in [`bagel-genesis/agents/`](bagel-genesis/agents/)
- trigger-loaded protocols in [`bagel-genesis/references/`](bagel-genesis/references/)
- validation and runtime helper scripts in [`bagel-genesis/scripts/`](bagel-genesis/scripts/)
- behavior evals in [`bagel-genesis/evals/evals.json`](bagel-genesis/evals/evals.json)

## What BAGEL Is For

Use BAGEL when you want an agent to:

- clarify a fuzzy product, research, writing, or optimization goal before execution
- take over an existing project without drifting away from its real architecture and conventions
- run for hours through implementation, verification, review, recovery, and polish
- keep making measurable progress instead of waiting for routine approval
- create missing local tools, tests, screenshots, benchmarks, and verifiers when needed
- return a readable morning briefing that explains what happened, what changed, and what still needs a decision

Do not use BAGEL for trivial scripts, tiny code edits, narrowly specified tickets, or tasks where you want a quick one-shot answer.

## Core Idea

BAGEL runs a continuous positive-optimization loop:

```text
Align  ->  Build  ->  Raise the bar  ->  Build again   (until budget/iterations exhausted)
```

- **Align:** make the user's intent, hard boundaries, runtime strategy, and quality bar executable.
- **Build:** implement one bounded slice at a time, verify it, record objective progress, and continue.
- **Raise the bar:** when the current metric set is all-green, generate a higher standard (tighter target, new dimension, adversarial perspective, astonishing completeness, stronger evidence) and keep going.

After the user delegates autonomous work, BAGEL's tie-breaker is:

> If a rule, review, failed attempt, missing tool, or platform limitation makes the agent want to stop and ask the user, continue instead unless the situation hits a true hard-stop boundary.

Hard-stops are intentionally narrow: irreversible or non-recoverable destructive action, serious security/privacy/legal/financial/production-data risk, credentials or paid external resources, core product/research identity changes, or an explicit user-forbidden boundary.

**Stopping rules are mechanical, not self-judged.** A run ends only when the user-set `max_iterations` is exhausted, the token/budget wall is hit, the user stops it, or a true hard-stop boundary is reached. "I think it's good enough" is never a stop reason.

## Why It Works

The loop diagram above is not the value — any agent can draw that. The value is the machinery that makes each step actually hold up over an unattended multi-hour run, where the agent's context will be compacted, its tools will be missing, and its self-reports cannot be trusted. BAGEL replaces "the agent judges" with "a script verifies state" wherever it can.

We label every mechanism below by how hard it is enforced, so you know what is load-bearing:

- **code-forced** — `flywheel_check.py` fails the cycle if the condition is violated. Cannot be talked out of.
- **gate-forced** — a hard gate blocks progress (merge, next slice, completion) until the condition passes.
- **protocol-forced** — written into the role prompts and references; load-bearing on the agent following its instructions.

### Failure modes it is built to defeat

| Without a skill, the agent tends to… | BAGEL's counter-mechanism | Enforcement |
|---|---|---|
| Drift as context grows | `constitution.yaml` anchor, re-anchored every state transition; each worker sees only its dispatch envelope, not history | protocol |
| Stop and ask at the first difficulty | Non-overridable tie-breaker: the default answer to friction is *continue*; the hard-stop list is deliberately narrow | protocol |
| Treat "it runs" as "it's done" | Baseline completion is only the *start* of the excellence loop, not the end | protocol + code |
| Review its own work (rubber-stamp) | Review registry records `reviewer_id`/`session_id`; independence is *derived*, not asserted | **code** |
| Report progress that isn't real | Every forward/lateral/backward delta must cite a real, non-empty evidence file on disk | **code** |
| Silently regress a green metric | Green-floor regression gate; dropped/renamed metrics cannot escape protection | **code** |
| Declare "good enough" and stop | No self-judged stop; bar must be *raised* (5 canonical moves) when all-green; flat-spin detector catches negligible gains | **code** |
| Burn budget re-trying the same dead end | Three lateral cycles force a strategy switch; a param/wording tweak counts as the *same* strategy | **code** |

`flywheel_check.py` states its own design intent in its header: *"Every check here exists because a prior audit found the corresponding guarantee was prose-only or self-reported."*

### How it runs for hours without you (long-run durability)

Four layers stack to make a long run durable rather than dependent on the model "remembering to continue":

1. **The loop is external, not model-internal.** One cycle = one bounded unit (one gate, one dispatch, one review, or one small repair). Each cycle ends by choosing exactly one action: continue / enter recovery / isolate the lane and advance another / pause only for a hard-stop / schedule the next cycle.
2. **The transcript is disposable; `.bagel/` is durable.** This is the core invariant. Every cycle writes a checkpoint (state, progress, task queue, decisions, risks, next action) and then discards raw worker reasoning and long logs. The next cycle rebuilds from `.bagel/`, never from "I'll remember next time."
3. **Snapshots survive crashes and compaction.** Before each compaction, a compact snapshot of control state is written with checksums. On resume: load the latest snapshot, verify checksums, compare to live state, execute only the saved `next-action.md`. If snapshot and live state disagree on scope, contracts, or completed slices, it *stops and writes a conflict report instead of guessing*.
4. **Platform timer binding.** On Claude Code this binds to scheduled tasks / `/loop` / cloud Routines / external cron invoking `claude -p`; on Codex to automations / cloud tasks / `codex exec` / `PreCompact`·`SessionStart` hooks.

**Honest caveat:** if no scheduler exists on the platform, BAGEL *must first bind a native loop* (`/loop`, scheduled task, Codex automation, `codex exec`+cron) with an interval <= 25 min before the first cycle. Only after exhausting every native mechanism may it record `degraded_resume` (marked `[DEGRADED]` in STATUS) - and even then it is *forbidden* from claiming unattended continuation. The overnight promise is conditional on a real wake mechanism actually being configured and recorded with proof.

### How it recovers instead of stopping (the recovery ladder)

When something breaks — a gate fails, a tool is missing, a test regresses, a hypothesis stalls, a reviewer disagrees — BAGEL climbs a nine-rung ladder before it ever considers waking you:

1. Local repair + rerun verification
2. Shrink the task scope
3. Dispatch a reviewer/debugger with only the failing evidence
4. Try an alternative path (different implementation/design/research method)
5. Rework in an isolated worktree/sandbox
6. Rollback to the last valid checkpoint + replay a safer plan
7. Re-plan (update task queue + decision map)
8. **Switch lanes** — isolate the blocked task and advance another independent high-value task
9. Wake the user — only for a true hard-stop boundary

**Anti-gaming rule:** changing a hyperparameter, threshold, or variable name counts as the *same* strategy and keeps counting toward the three-strike limit. A genuine strategy switch must change the approach, core assumption, artifact structure, or evidence source. A missing verifier is recovery work — the agent builds the smallest local test/benchmark/screenshot script needed — not a reason to waive a gate or stop.

### How the agents divide labor and stay honest

BAGEL is a hub-and-spoke model: one **Orchestrator** dispatches *one bounded worker at a time* inside a strict **dispatch envelope** (`ROLE / READ-ONLY / WRITE-ONLY / LOCKS / EXIT-CRITERIA` with exact file paths, not directories). Workers never read the full skill, never read history, and never read other workers' transcripts. Per-role reference budgets cap how many protocol files a worker may touch (Implementer: 0–1; reviewers: 1–2).

Parallel work is opt-in (`parallel_advanced`) and guarded by git worktrees, path locks, and a merge queue. The rule "a worker may never merge its own work" is repeated across four files. Merging is owned by the Integration Manager after five gate predicates pass.

**Independent review is derived from registry state, not asserted.** `flywheel_check.py` fails if a claimed R3/R4 review reuses the implementer's agent or session identity. On a platform with no real subagents, BAGEL runs roles sequentially, labels that R1 (explicitly *not* independent), and for any high-risk unattended change it **refuses to merge that lane** — isolating it on a branch and advancing safe work — rather than silently downgrading the review.

**Honest caveat:** even an R3 "true subagent" on Claude Code or Codex is usually the same underlying model family. The independence is *contextual/identity isolation* (separate context window, separate session, no implementer narrative), not different training. True model-diversity independence (R4) requires an external or human reviewer.

### Skeleton first, then value

For software, a **Skeleton Builder** erects a runnable "ghost ship" — routes, error/auth boundaries, typed contracts, registered stubs, minimal tests, a mock core journey — and a hard **Ghost Ship Gate** blocks all value-slice work until 10 structural conditions pass with real command/test/browser output. No self-certification; a named command in the doc is not a pass.

For research, the equivalent skeleton is a **research protocol + bibliography map** before any claim is filled in. The "scaffold first, then advance" principle applies to every artifact type; only the skeleton's shape changes.

### Engineering rigor vs. research rigor

BAGEL does not treat a research project as "build software in disguise." `artifact-types.md` switches the baseline unit, skeleton gate, and verification mode by type:

| Type | Baseline unit | Skeleton gate | Verification |
|---|---|---|---|
| software | value slice | ghost ship (runnable shell) | tests, typecheck, e2e/browser |
| existing software | bounded improvement | behavior-preservation gate | regression checks, diff review |
| **research** | **claim / experiment / section** | **research protocol + bibliography map** | **citation checks, methodology critique, reproducibility** |
| writing | chapter / scene / argument | outline + voice/continuity bible | continuity, structure, voice |
| data analysis | dataset / question / chart | data pipeline + assumptions map | data validation, statistical critique |

For computational research the excellence loop explicitly requires a hypothesis ledger, benchmark harness, baseline comparison, ablation/failure notes, and winner-retention criteria. When results stall (three lateral cycles), the prescribed switch is *change the hypothesis* — not tune a parameter.

**Honest caveat:** `flywheel_check.py` enforces that a research bar-raise tagged `stronger_evidence` has an evidence file that exists — but it cannot verify that the file is genuinely a falsification test or a real baseline comparison. Semantic research rigor rests on the independent reviewer and the periodic independent flywheel audit, not on the script.

### What is enforced by code vs. protocol — and the one gap

Eight anti-hallucination properties are enforced by `flywheel_check.py` as a hard gate: evidence-artifact existence, review-independence derivation, green-floor regression (direction-aware, dropped-metric-safe), iteration budget, budget monotonicity, bar-raise value classes, stuck-metric classification, and flat-climbing recompute.

One guarantee is **still prose-only**: the periodic *independent flywheel audit* (an R3+ reviewer that re-checks the agent's own `.bagel/` evidence against the real repo, to catch a determined agent writing internally-consistent fiction) is described as mandatory every N cycles, but no script verifies it was actually performed. This is the largest remaining prose-vs-code gap. The practical defense today is that the other eight checks raise the cost of fabrication high enough that the audit's job is bounded — but a fully code-enforced audit is the obvious next hardening step.

## Key Features

### Deep Alignment Before Autonomy

BAGEL avoids shallow "plan mode" alignment. It asks decision-oriented questions and persists the answers into `.bagel/` state.

Alignment supports three depths:

| Depth | Use when | Behavior |
|---|---|---|
| `snap_alignment` | urgent or low-stakes | capture essentials, default reversible details, start quickly |
| `standard_alignment` | default | ask key choice cards plus the most relevant open questions |
| `deep_alignment` | important, ambiguous, high-budget | keep asking decision points until the user's mental model is clear enough |

Choice cards cover autonomy level, execution strategy, run budget, takeover aggressiveness, taste source, research verification, hard-stop boundaries, and HTML briefing preferences.

### Continuous Positive Optimization (the flywheel)

BAGEL never stops at "good enough." Each iteration drives a target set to all-green; when green, it raises the standard and starts the next iteration. The run is guarded by two mechanical validators: one for the operational substrate and one for progress integrity.

```bash
python bagel-genesis/scripts/bagel_run_check.py /path/to/project
python bagel-genesis/scripts/flywheel_check.py /path/to/project
```

`bagel_run_check.py` verifies that the run is actually wired for autonomy: git rollback exists, a <=25 minute loop/timer is bound, alignment floors were met, agent dispatch records exist, implementer/reviewer roles are separate, STATUS.md is complete, and HTML dashboard ownership is not ambiguous.

`flywheel_check.py` mechanically verifies six properties of every run: objective deltas, no false independence, no regression below green floors, no budget burning, no redundant bar raises, no flat-spin. All evidence must point to real files/commands/reports.

### Context Is the Resource to Protect (information architecture)

Long runs fail not from laziness but from *context pollution*: the coordinating agent absorbs implementation detail, the reviewer absorbs the implementer's rationalization, every brainstorm converges on the obvious. BAGEL's v1.1 architecture treats context as a scarce resource and controls its flow explicitly:

- **The orchestrator is a coordinator, not an implementer.** It dispatches, verifies, and persists state — it never writes product code. Its firewall blocks implementation reasoning, design debate, and debug narrative from entering its context.
- **Every role gets a clean context.** A subagent call *is* a separate context window. Workers receive a dispatch envelope (ROLE / READ-ONLY files / WRITE-ONLY files / EXIT-CRITERIA), never the full skill, never history, never another worker's chain-of-thought.
- **Findings flow; reasoning does not.** A worker may read another worker's *findings* (a review report, a test result, a benchmark number). It must never read another worker's *reasoning* (why they chose that approach). This is how collaboration happens without contamination.
- **Insight diversity is manufactured.** Before raising the bar, the orchestrator dispatches ≥ 2 **Brainstormer** subagents, each pinned to one lens (performance / resilience / user_value / simplicity / completeness / evidence_strength / adversarial), each isolated from the others' output. The orchestrator merges *after* all return. This is the only mechanism that produces genuinely divergent ideas instead of converging on the obvious.
- **Doc ownership is split, not shared.** The orchestrator writes STATUS.md's mechanical sections every cycle (telemetry, delta trend, loop binding, gates); the User Alignment Curator writes the narrative sections (Morning Briefing, risk framing) on a trigger cadence and owns the HTML dashboard exclusively. No file has two writers.

### Three Execution Strategies

| Strategy | Use when | Behavior |
|---|---|---|
| `stable_long_run` | overnight / unattended work | lower write parallelism, stronger verification, continuous cycles |
| `balanced_parallel` | speed and reliability both matter | moderate concurrency and review depth |
| `fast_parallel` | user is nearby and rollback is cheap | faster exploration, more aggressive parallelism |

### Risk-Tiered Review Cadence

To keep governance overhead acceptable, independent review is tiered by risk:

- **R3 review required** for behavior changes, regressions, P0/P1 changes.
- **Low-risk polish** uses an orchestrator diff check plus one R3 review every 4 cycles.

This keeps the autonomous loop efficient instead of bottlenecking on every cycle.

### Runtime Loop and Timer Binding

When the user says "start autonomous iteration," BAGEL must bind to the strongest available runtime:

- `scheduled_resume`: platform automation, scheduled task, or timer
- `external_harness`: cron, launchd, cloud task, CLI loop, or other harness
- `active_session_loop`: current platform loop is actively running
- `degraded_resume`: every native loop mechanism was proven unavailable, so unattended continuation is not guaranteed (STATUS marked `[DEGRADED]`)

Loop state records trigger interval, next wake time, schedule proof, resume command, and telemetry.

### Objective Progress Signals

Every cycle appends to `.bagel/evidence/progress-deltas.yaml`. Each delta is classified as:

- `forward`: measurable improvement or closed risk
- `lateral`: activity without measurable progress
- `backward`: regression, new blocker, degraded metric, or worse artifact state

Three consecutive lateral cycles force a strategy switch. Backward cycles require repair, rollback, or isolation before unrelated polish.

### Existing Project Takeover

For existing projects, BAGEL does not ask the user to explain facts the repository can reveal. It runs a Project Cartographer pass and drafts current stack, entrypoints, run/verify commands, behavior baseline, protected surfaces (public APIs, data contracts, user-visible flows), replaceable surfaces, and reusable assets. The user can veto or correct the draft instead of reconstructing the project from memory.

### Human-Readable Briefing

BAGEL maintains `.bagel/STATUS.md` (with a forced `Morning Briefing` block) and `.bagel/user_briefing/`. Optional HTML dashboard support is defined in [`bagel-genesis/references/alignment-dashboard-html.md`](bagel-genesis/references/alignment-dashboard-html.md).

## Repository Layout

```text
.
└── bagel-genesis/
    ├── SKILL.md              # entry point
    ├── README.md             # skill-folder-local readme
    ├── agents/               # role prompts (orchestrator, implementer, reviewers, cartographer, ...)
    ├── references/           # 31 trigger-loaded protocols
    ├── scripts/
    │   ├── detect_runtime_capabilities.py
    │   ├── bagel_run_check.py    # operational runtime substrate validator
    │   ├── flywheel_check.py     # mechanical flywheel integrity validator
    │   └── skill_lint.py         # skill self-consistency lint
    └── evals/
        └── evals.json        # 47 behavior evals
```

## Installation

### From GitHub

```bash
git clone https://github.com/BRSAMAyu/bagel-genesis.git
```

Then copy or symlink the `bagel-genesis` directory into the skill location used by your agent platform.

### Codex

```bash
mkdir -p ~/.codex/skills
cp -R bagel-genesis ~/.codex/skills/
```

Then in a Codex session:

```text
Use the bagel-genesis skill. I want to align on this product idea, then run stable long-run autonomous iteration overnight.
```

### Claude Code

Clone the repo somewhere Claude Code can read it, then ask Claude Code to use the `bagel-genesis` skill folder directly:

```text
Use /path/to/bagel-genesis as the BAGEL Genesis skill. First run deep alignment, then start stable long-run autonomous iteration. Do not remain in planning-only mode after alignment.
```

For long unattended work, configure Claude Code's loop/scheduled-task mechanism, or let BAGEL detect and record whether only manual resume is available.

## Quick Start

### Blank-Slate Product

```text
Use bagel-genesis.

I want to build a polished app from this rough idea:
...

Start with standard alignment. Then use stable_long_run autonomous iteration for up to 12 cycles, checkpoint every 30 minutes, and wake me only for true hard-stops.
```

### Existing Project Takeover

```text
Use bagel-genesis.

This repo is an existing product. First run Project Cartographer to understand what exists, what must be preserved, and what can be redesigned. Then ask me to veto the protected/replaceable draft. After that, run stable_long_run polish and implementation.
```

### Research or Optimization Run

```text
Use bagel-genesis.

I want an autonomous experiment loop. Align on the benchmark, baseline, and stop criteria. If the first approach stalls, generate alternative hypotheses and keep testing. Record progress deltas and preserve all evidence.
```

## Runtime Configuration

Before promising autonomous continuation, BAGEL should run:

```bash
python bagel-genesis/scripts/detect_runtime_capabilities.py --out .bagel/runtime_capabilities.yaml
```

This detects platform clues, CLI tools, scheduler availability, Git support, browser/visual-check support, and local tool-provisioning capability. The agent then maps those facts to one of `single_session`, `degraded_resume`, `scheduled_resume`, or `external_harness`.

For explicit autonomous iteration, BAGEL must record a loop binding:

```yaml
loop_binding:
  mode: scheduled_resume | external_harness | active_session_loop | degraded_resume   # <= 25 min interval
  platform: codex | claude_code | other
  schedule_id: ""
  trigger_interval_minutes: 10
  next_wakeup_at: "ISO-8601"
  resume_command_or_action: ""
  proof:
    - "automation id, cron entry, scheduled task, active /loop config, or harness command"
```

If the result is `degraded_resume`, the agent must not claim it will continue unattended and STATUS.md is marked `[DEGRADED]`.

## `.bagel/` Runtime State

BAGEL writes project-local durable state under `.bagel/`. This directory is runtime state and should usually be Git-ignored.

Quick mode uses a compact control plane (`state.yaml`, `constitution.yaml`, `context.yaml`, `ledger.yaml`, `STATUS.md`, `evidence/`, `user_briefing/`). Full mode expands into detailed files for broad, high-risk, multi-day, or parallel work.

## Validation

Validate the skill itself:

```bash
python bagel-genesis/scripts/skill_lint.py bagel-genesis
python3 -m json.tool bagel-genesis/evals/evals.json >/dev/null
```

Validate a BAGEL run's operational substrate and flywheel evidence:

```bash
python bagel-genesis/scripts/bagel_run_check.py /path/to/project
python bagel-genesis/scripts/flywheel_check.py /path/to/project
```

`bagel_run_check.py` verifies that the real `.bagel/` run has git rollback, loop binding, <=25 minute wake interval, alignment floors, agent dispatch records, implementer/reviewer separation, STATUS sections, and HTML dashboard ownership.

`flywheel_check.py` verifies evidence paths, green-floor regressions, review-level claims, bar-raise value classes, stuck metrics, budget monotonicity, and other failure modes that can make a long run look productive when it is not.

## Safety Model

BAGEL is autonomy-first, but not reckless. It should continue through ordinary friction (missing tests, broken local setup, failing experiments, UI gaps, review failures, temporary blocked lanes, need for local scripts/screenshots/benchmarks). It should stop or wake the user only for true hard-stops: irreversible/non-recoverable destructive action, production data or infrastructure changes, credentials/tokens/paid accounts, serious security/privacy/legal/financial risk, core product/research identity changes, or explicit user-forbidden boundaries.

## Current Status

BAGEL Genesis v1.2 is documentation-complete and internally validated:

- skill metadata validation passes
- BAGEL consistency lint passes
- evals JSON is valid and sequential
- 47 behavior evals cover alignment depth floors, project takeover, mandatory loop/git/dispatch, context isolation, brainstormer diversity, verify-dont-trust exploration, immediate loop binding, pointer-only wake prompts, runtime effectiveness audit, loop binding, recovery, flywheel integrity, visual evidence, and HTML briefing

The remaining proof is empirical: run it on real projects overnight and compare the results against ordinary agent use.

## License

MIT
