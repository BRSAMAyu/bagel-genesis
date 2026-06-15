# Runtime Protocol

Use this reference when BAGEL Genesis must run for many cycles, across context compaction, thread resumes, timers, or multiple agents.

## Core Invariant

The transcript is disposable. `.bagel/` is durable.

Persist only structured state needed for future decisions:

- product constraints and constitution
- alignment canon and autonomy contract
- agent-facing project understanding for existing projects
- excellence horizon
- completion horizon
- current state and current slice
- run mode and review matrix
- task queue and progress ledger
- progress deltas and budget allocation
- decision records and evidence links
- evolution ledger and rollback points
- git branches, locks, merge queue, and agent registry
- runtime capabilities, artifact profile, gate predicates, and human decisions
- contracts and stub registry
- review findings and gate results
- open risks and next action

Do not persist long narrative reasoning, raw worker transcripts, or unrelated command output. Summarize them into facts, decisions, risks, and commands.

## Context Classes

| Class | Lifetime | Examples | Storage |
|---|---|---|---|
| Constitutional | whole project | north star, forbidden directions, autonomy boundaries | `.bagel/constitution.yaml` or `.bagel/constitution.json` |
| Strategic | phase or milestone | value slice order, architecture direction, release risks | `.bagel/state.yaml` (quick) or `.bagel/state.json` + `.bagel/progress.json` (full), decisions |
| Quality Mode | active run | speed/stability profile, review depth, parallelism limits | `.bagel/run_mode.yaml` |
| Project Reality | until changed | current modules, features, conventions, run commands | `.bagel/agent_context/` |
| Evolution | whole project | changes, rollback points, audit trail | `.bagel/evolution/` |
| Coordination | active run | locks, branches, merge queue, agent registry | `.bagel/git/`, `.bagel/agents/` |
| Contractual | until amended | schemas, APIs, events, data models | `.bagel/contracts/`, decisions |
| Tactical | one task | files changed, local test failures, implementation notes | worker context, then review report |
| Ephemeral | minutes | failed command noise, exploratory snippets | discard |

Only constitutional, strategic, and contractual context should routinely survive compaction.

## Checkpoint Triggers

Write a checkpoint after:

- S0/S1 approval
- every state transition
- every value slice completion or abort
- every meaningful project/context/briefing change
- every branch/worktree/lock/merge queue state change
- every hard gate failure
- every amendment proposal and verdict
- every red-team pass
- every baseline or final candidate attempt
- before stopping for time, context, or platform limits
- before quota/rate-limit exhaustion if detectable

Checkpoint format:

```yaml
checkpoint:
  timestamp: "ISO-8601"
  state: "S8"
  current_slice: "VS-003"
  constitution_hash: "sha256..."
  changed_artifacts:
    - ".bagel/decisions/ADR-014.json"
  commands_run:
    - "npm test -- billing"
  gate_status:
    ghost_ship: pass
    slice_completion: fail
  open_risks:
    - id: "RISK-004"
      severity: "P1"
      owner: "orchestrator"
      next_action: "Dispatch implementer with failing test only"
  next_action:
    role: "implementer"
    envelope: ".bagel/ledger/next-dispatch.md"
```

Also write or update an evolution change record for meaningful changes. The checkpoint captures resumability; the evolution ledger captures reviewability and rollback reasoning.

## Progress and Status Protocol

Every cycle must update two observable surfaces:

- `.bagel/evidence/progress-deltas.yaml`: append the objective delta for the just-finished cycle.
- `.bagel/STATUS.md`: update the human-readable live status.

### STATUS.md Ownership Split (v1.1)

STATUS.md has two owners with **non-overlapping sections** - this prevents both the dual-ownership conflict and orchestrator context pollution from narrative-writing:

- **Orchestrator writes the mechanical sections every cycle** (it already has this data, no extra reasoning needed):
  `Last Updated`, `Run Status`, `Loop Binding`, `Delta Trend`, `Timeline`, `Budget`, `Telemetry`, `Recent Autonomous Decisions`, `Blocked or Isolated Lanes`, `Next Action`. These are data fields pulled from `.bagel/` state - no narrative composition, no risk-prioritization reasoning.

- **User Alignment Curator writes the narrative sections on a trigger cadence** (milestones, recoveries, before/after excellence loop, before final delivery, when user instruction changes):
  `Morning Briefing` (the 4-line block a groggy user reads first), `Current Focus` narrative. The Curator owns risk-prioritization and human-framing because that is a distinct skill from cycle coordination, and it keeps the orchestrator's context free of "how do I explain this to the user" reasoning.

- On cycles where no Curator dispatch fires, the Orchestrator writes a **minimal Morning Briefing** (status line + "nothing irreversible" line) so the file is never stale, then the Curator rewrites the full briefing at the next trigger. The minimal version is explicitly marked `[auto-minimal - full briefing pending]`.

**The HTML dashboard (`.bagel/user_briefing/alignment-dashboard.html`) is owned exclusively by the User Alignment Curator**, generated from STATUS.md + progress-deltas at the user-selected frequency (`every_milestone` default). The orchestrator never writes HTML. See `references/alignment-dashboard-html.md`.

Use this `STATUS.md` shape. The **Morning Briefing** block at the top is mandatory and must be written first every cycle - it is what a groggy user reads at 8am in 10 seconds:

```markdown
## Morning Briefing (read this first)
1. **Status:** {finished | still running | hit a wall}
2. **Nothing irreversible happened while you slept:** {yes | NO: <one-line what>} — no production data, credentials, or destructive actions were touched except: {none | <item>}.
3. **Decision you need to make now:** {none, safe to ignore | <one-line decision>} — {why it can't be auto-decided}.
4. **Revert the biggest overnight decision:** {nothing to revert | `git revert <sha>` / `<one command>`}.

## Last Updated
{ISO timestamp}

## Run Status
{progressing | recovering | excellence_loop | waiting_for_capacity | blocked_hard_stop | complete}

- `blocked_hard_stop` = the run exhausted all autonomous avenues and hit a genuine hard-stop boundary (credentials, paid resources, production data, irreversible action, or no safe path remains). This is NOT laziness — the run tried: {list 2-3 things attempted}. It needs your decision on: {item}.
- `waiting_for_capacity` = quota/runtime temporarily exhausted, resume plan exists. The run will continue when capacity returns.

## Loop Binding
{scheduled_resume | external_harness | active_session_loop | degraded_resume}
Timer interval: {n} minutes  (HARD MAX 25)
Next wakeup: {ISO timestamp | unavailable}
Proof: {automation id | scheduled task id | cron/launchd entry | active loop config | harness command}
Degraded marker: {none | [DEGRADED - no native loop bound]}

## Current Focus
{one sentence}

## Delta Trend
{last 6 deltas as sparkline, e.g. f f l f b f} — latest: {forward | lateral | backward}
Mechanical stop counters: lateral={n}/2, no-finding rounds={n}/2, open P0/P1={n}/{n}
Flywheel integrity: {pass | fail | not_run} — latest `scripts/flywheel_check.py`: {one-line result}

## Timeline
- [x] 14:00 Alignment complete
- [x] 14:30 VS-001 complete
- [/] 15:10 VS-002 in progress
- [ ] VS-003 pending

## Budget
Runtime/token estimate: {used} / {limit or unknown}
Remaining allocation: P0 {..}%, P1 {..}%, polish {..}%

## Telemetry
Elapsed: {minutes}
Cycles: {completed}/{target or max}
Agents dispatched: {n}; review agents: {n}; context compactions: {n}
Recovery events: {n}; timer wakeups: {n}; tests/checks run: {n}; screenshots/renders: {n}
Token usage: {platform_reported | estimated | unavailable}: {value}

## Recent Autonomous Decisions (top 5 by impact)
1. {decision + reason + reversibility + revert command}

## Blocked or Isolated Lanes
- {lane}: {why not merged, what continues instead}

## Next Action
{single executable next action}
```

**Mandatory regardless of mode:** the Morning Briefing block and the `blocked_hard_stop` status must exist in both quick and full mode. A run that hits a hard-stop must never leave the user with a STATUS.md that reads as silence or "waiting." The difference between "I hit a real wall after trying X, Y, Z" and "I gave up" is the entire bedtime contract.

If three consecutive deltas are `lateral`, update `STATUS.md` with the strategy switch. If a delta is `backward`, record the rollback/isolation/repair action before starting unrelated polish.

After updating `STATUS.md`, run `scripts/flywheel_check.py <project-root>` when `.bagel/state.yaml` exists. If the check fails, set Run Status to `recovering`, list the failed gate under Current Focus, and make the Next Action the repair/rollback/isolation/strategy-switch needed to restore flywheel integrity.

## Snapshot Protocol

Use snapshots for recovery across long unattended runs and context loss. A snapshot is a compact, validated copy of the durable control state, not a copy of the whole repository.

Create `.bagel/snapshots/manifest.json`:

```json
{
  "latest": "SNAP-20260615-153000",
  "snapshots": [
    {
      "id": "SNAP-20260615-153000",
      "created_at": "2026-06-15T15:30:00Z",
      "state": "S8",
      "current_slice": "VS-003",
      "files": [
        ".bagel/snapshots/SNAP-20260615-153000/state.json",
        ".bagel/snapshots/SNAP-20260615-153000/handoff.md"
      ],
      "constitution_hash": "sha256:...",
      "state_hash": "sha256:..."
    }
  ]
}
```

Each snapshot directory should contain:

- `state.json` or `state.yaml`: copy of the active state file
- `handoff.md`: operational summary under 200 lines
- `open-risks.yaml`
- `next-action.md`
- `checksums.txt`

Write snapshots after major checkpoints and before compaction. Keep the latest useful snapshots; archive or delete only after confirming they are not the latest recovery point.

## Resume Algorithm

On resume:

1. Read `.bagel/snapshots/manifest.json` if present.
2. Load the latest snapshot and verify checksums when available.
3. Compare snapshot state with live `.bagel/state.yaml` or `.bagel/state.json`.
4. If live state is newer and valid, use live state.
5. If live state is missing or corrupted, restore from the latest valid snapshot.
6. Re-read constitution and completion horizon.
7. Execute only the saved `next-action.md` or deliberately replace it with a new checkpointed action.

If snapshot and live state disagree in ways that affect scope, contracts, or completed slices, stop and write `.bagel/ledger/resume-conflict.md` instead of guessing.

## Compaction Protocol

Compact whenever:

- the next task does not need the last task's detailed reasoning,
- worker returns DONE/BLOCKED/NEEDS_CONTEXT,
- a state transition completes,
- context grows enough that attention to constitution or current files may degrade,
- switching from orchestration to implementation or review.

Before compaction:

1. Update `.bagel/state.yaml` or `.bagel/state.json`.
2. Save or update decisions, reviews, risks, and next action.
3. Save proposed updates to `.bagel/agent_context/` when project reality changed.
4. Update `.bagel/agent_context/freshness.yaml`.
5. Write evolution change records for meaningful changes.
6. Update `.bagel/git/` and `.bagel/agents/` when coordination state changed.
7. Record test commands and results, not full logs unless needed.
8. Drop implementation discussion that is already reflected in code, tests, agent-facing context, user briefing, evolution ledger, or handoff.
9. Reopen with constitution, state, global capsule, current task envelope, relevant project context, coordination state, and relevant files only.

## Loop and Timer Behavior

Use platform-native background loops, reminders, wakeups, scheduled tasks, automations, cloud tasks, non-interactive CLI runs, or continuation features when available. The loop is an external runtime around agent sessions: select task, build context, run worker, verify, write memory, choose next action. Keep each loop small enough to finish cleanly:

```text
cycle_budget = one gate OR one worker dispatch OR one review OR one small repair
```

At the end of every cycle, choose exactly one:

- continue immediately with a new bounded envelope,
- enter recovery with a smaller/alternative task,
- isolate the blocked lane and continue another high-value task when possible,
- pause only for a hard-stop boundary in the autonomy contract,
- schedule/wake the next cycle if the platform supports timers,
- stop with a checkpoint if platform support is absent.

Never rely on "I will remember next time." The next cycle must be resumable from `.bagel/`.

When multiple agents are active, each cycle must reconcile `.bagel/agents/registry.yaml`, `.bagel/git/locks.yaml`, and `.bagel/git/merge-queue.yaml` before dispatching more work.

## Drift Controls

Use these controls throughout the run:

- Re-read constitution at every state transition and before any scope decision.
- Re-read runtime capabilities before promising continuation, timers, or independent agents.
- Re-read artifact profile before applying software-specific gates.
- Read global capsule and relevant freshness entries before dispatch.
- Read run mode before choosing parallelism, review depth, or merge policy.
- Compare each slice against completion horizon before implementing it.
- Route scope reductions, P0 removals, privacy changes, and business model changes to the Constitutional Court.
- Require reviewers to inspect artifacts, not the implementer's explanation.
- Require context updates when implementation changes project reality.
- Require lock/branch ownership before write work.
- Require review level R3/R4 when the QA matrix calls for independent review. If R3/R4 is unavailable for high-risk unattended work, isolate that lane without merging, continue safe independent work, and wake the user only when no useful autonomous path remains.
- Merge only through orchestrator or integration manager.
- Keep code workers unaware of budget pressure unless budget changes their task envelope.
- Treat repeated "simplify/defer/users won't notice" language as engineering escape evidence.

## Recovery Protocols

### Gate fails once

Log the exact failed predicate and repair locally.

### Same gate fails twice

Create a smaller task envelope or dispatch a reviewer to identify the mismatch.

### Same gate fails three times

Do not repeat the same approach. Enter recovery mode and write `.bagel/ledger/recovery-log.md`:

- gate name
- failed attempts
- evidence
- likely root causes
- strategy change
- next smaller or alternative task
- whether user wake is required by the autonomy contract

Wake the user only if recovery requires a hard-stop boundary: credential, paid service, production/irreversible/destructive action, serious safety/privacy/legal/financial risk, or core direction change.

### Agent interference or lock conflict

Stop conflicting work, preserve both branches/worktrees, classify conflict, and create an integration or serialization task. Do not let workers resolve each other's scope conflicts directly.

### Worker needs broad context

Do not give broad context by default. Instead:

1. Generate a small artifact answering the missing question.
2. Add it to the worker envelope.
3. If this repeats, the slice spec is too vague; return to S3/S5.

## Cross-Platform Notes

Codex, Claude Code, and similar tools differ in subagent support, context compaction, and scheduled continuation. For Codex and Claude Code, load the matching platform adapter before degrading capability. The protocol must survive all three modes:

- With subagents: dispatch isolated roles and close/discard workers after reports.
- Without subagents: run role prompts sequentially and explicitly clear/compact between roles; do not call the result independent review unless QA permits the recorded review level.
- With timers: schedule the next bounded cycle from the saved checkpoint.
- Without timers: leave a precise next action so the user or future agent can resume.

The protocol should constrain drift, not creativity. Give agents freedom inside the current bounded problem; keep product boundaries, contracts, and gates outside their control.

## Missing Capability Policy

Missing local tooling should usually become a task in the loop, not a stop condition. If the run needs UI screenshots, browser checks, benchmark scripts, data validation, reproducibility harnesses, or experiment automation, assign a bounded worker to create the smallest project-local version and verify it. Record the tool, command, and trust boundary in `.bagel/ledger/gate-verifiers.md` or the relevant evidence ledger.

Do not let this policy override the autonomy contract. Credentials, paid resources, production infrastructure, destructive actions, major framework replacement, or changes to core promise/privacy/business model still require the configured approval path. While any such approval is pending, do not idle: continue safe independent high-EV work, isolate the blocked lane, and surface the pending decision in the user briefing.

## Quota Exhaustion

If API quota, rate limit, session duration, or platform budget prevents progress:

1. Save state, progress, handoff, and next dispatch.
2. Mark `.bagel/state.yaml` or `.bagel/state.json` with `waiting_for_capacity`.
3. Schedule a wakeup/continuation if the platform supports it.
4. If scheduling is unavailable, leave a single precise resume action.
5. On resume, reconstruct from `.bagel/`, not transcript memory.

Never leave a long autonomous run in an ambiguous state where the next agent cannot tell whether work is done, blocked, or waiting for capacity.
