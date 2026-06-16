# Supervisor Resilience Protocol

Use this on Claude Code/Codex long-running work where context compaction, context length limits, session crashes, or failed resume can stall the system. This protocol adds an outer Supervisor layer above the BAGEL Orchestrator.

## Core Design

The main agent that loads BAGEL becomes **Supervisor**, not the inner Orchestrator, when true subagents are available. The Supervisor is the user-facing guardian and last-resort recovery layer. It immediately spawns a fresh BAGEL Orchestrator subagent/session to run the internal workflow.

```text
User
  -> Supervisor main context (alignment, user proxy, heartbeat, hard-stop arbitration)
      -> Orchestrator subagent/session (BAGEL state machine)
          -> Specialist workers (Implementer, Reviewer, Runtime Doctor, Evaluation Architect, ...)
```

This extra layer protects the most precious context:

- Supervisor context stays small because it does not implement or debug.
- Orchestrator context can compact or fail without losing the whole run.
- Workers remain isolated from user ambiguity and Supervisor reasoning.
- User instructions are translated into clean BAGEL state updates before they enter the internal system.

If true subagents are unavailable, the main agent may fall back to the older single-Orchestrator model, but it must record `supervisor.mode: collapsed_no_true_subagents`.

## Supervisor Duties

Supervisor owns:

- user conversation and deep alignment,
- user instruction normalization into `.bagel/constitution.yaml`, `.bagel/ledger.yaml`, and `.bagel/supervisor/user-intake.yaml`,
- hard-stop arbitration,
- heartbeat and liveness checks,
- Orchestrator spawn/respawn,
- resume capsule maintenance,
- detecting corrupted/ambiguous BAGEL state before restarting work.

Supervisor must not own:

- product implementation,
- environment debugging,
- review,
- bar-raise selection,
- routine task queue execution.

## Required Files

Quick mode:

```text
.bagel/supervisor/
├── heartbeat.yaml
├── resume-capsule.md
├── orchestration-ledger.yaml
├── user-intake.yaml
└── respawn-log.yaml
```

Full mode may add:

```text
.bagel/supervisor/
├── handoff-to-orchestrator.yaml
├── state-digest.yaml
├── compact-context-index.yaml
└── safety-arbitration.yaml
```

## Heartbeat

Supervisor heartbeat may be looser than the inner BAGEL loop because it is a guardian, not the work engine.

```yaml
supervisor:
  mode: nested_supervisor | collapsed_no_true_subagents
  heartbeat_interval_minutes: 30
  last_checked_at: "ISO-8601"
  next_check_at: "ISO-8601"
  platform: claude_code | codex | other
  proof:
    - "scheduled task id, /loop proof, automation id, cron entry, or active session note"
  current_orchestrator:
    agent_id: "bagel-orchestrator-001"
    session_id: "session-..."
    spawned_at: "ISO-8601"
    status: active | stale | failed | replaced
  liveness:
    last_orchestrator_heartbeat_at: "ISO-8601"
    max_stale_minutes: 45
```

The inner BAGEL loop still obeys the <=25 minute runtime interval. The Supervisor heartbeat can be 30-60 minutes if the inner loop is healthy.

## Resume Capsule

`.bagel/supervisor/resume-capsule.md` is the fastest safe re-entry point after compaction, new conversation, or Orchestrator failure. It must be under 200 lines and contain only operational facts:

```markdown
# BAGEL Resume Capsule

## Identity
- run_id:
- artifact:
- user goal:
- hard-stops:

## Current State
- phase:
- current_iteration:
- iterations_completed / max_iterations:
- active target set:
- latest git ref:
- loop binding:

## What To Read Next
1. .bagel/STATUS.md
2. .bagel/state.yaml
3. .bagel/constitution.yaml
4. relevant context capsule:
5. one reference from Loading Matrix:

## Next Action
Exactly one bounded action.

## Safety Notes
- blocked lanes:
- hard-stop risks:
- user decisions pending:
```

Do not include chain-of-thought, old transcripts, or worker reasoning.

## Respawn Procedure

Supervisor respawns Orchestrator when any of these happen:

- Orchestrator heartbeat is stale beyond `max_stale_minutes`,
- Orchestrator reports context corruption or compaction failure,
- `.bagel/state.yaml` is corrupted but a valid snapshot exists,
- Orchestrator performs implementation/debugging directly after being warned,
- Orchestrator cannot continue after context compression,
- user gives a new instruction that changes the BAGEL contract and requires a fresh internal run context.

Procedure:

1. Validate `.bagel/state.yaml`; if invalid, restore latest valid snapshot.
2. Read `resume-capsule.md`, `STATUS.md`, `constitution.yaml`, and state.
3. Write `.bagel/supervisor/respawn-log.yaml` with cause, old session id, new session id, and state hash.
4. Spawn a new Orchestrator subagent/session with only the resume capsule, state pointers, and current next action.
5. Mark old Orchestrator `replaced`.
6. Continue the run unless the cause is a true hard-stop.

## User Proxy Rule

Raw user messages do not go straight to internal workers. Supervisor converts them into one of:

- constitution amendment proposal,
- new alignment decision,
- hard-stop decision,
- task queue update,
- evaluation/taste update,
- instruction that is outside autonomy and should pause.

Then the internal BAGEL system receives the structured state update, not the whole conversation.

## Claude Code Nested Agent Guidance

On Claude Code, prefer this nesting when available:

1. Main session: Supervisor.
2. Subagent/background agent: BAGEL Orchestrator.
3. Orchestrator-dispatched subagents: specialists.
4. Optional specialist subagents/worktrees for nested diagnostics or reviews.

Project-local `.claude/agents/` definitions may wrap Supervisor and Orchestrator prompts. The Supervisor heartbeat can use `/loop`, scheduled tasks, cloud Routines, desktop scheduled tasks, or `claude -p` under cron/launchd. The inner Orchestrator uses the normal BAGEL loop and dispatch rules.

If Claude Code cannot set timers for subagents directly, keep the timer at Supervisor level. The Supervisor wakes, reads state, and respawns or nudges the inner Orchestrator only when needed.
