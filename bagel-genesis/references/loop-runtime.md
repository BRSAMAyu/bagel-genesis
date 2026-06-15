# External Loop Runtime

Use when BAGEL runs unattended for hours or days. The loop is an external harness around agent sessions, not a model-internal infinite loop.

## Components

```text
Loop Runtime
├── Trigger / Scheduler
├── Task Selector
├── Context Builder
├── Worktree or Sandbox Manager
├── Agent Runner
├── Verifier
├── Memory Writer
├── Retry / Rollback Policy
└── Reporter
```

When the platform provides native loop, scheduler, subagent, hook, cloud, or non-interactive primitives, use them directly. When it cannot implement a component directly, emulate that component with `.bagel/` artifacts and resumable next actions.

Before configuring the loop, read `references/runtime-capabilities.md`. The loop may only use capabilities recorded in `.bagel/runtime_capabilities.yaml`.

For Codex and Claude Code, load the matching platform adapter before deciding the loop cannot continue unattended. These platforms can often supply the trigger, scheduler, agent runner, worktree isolation, and verifier execution directly.

## Autonomous Iteration Start Gate

When the user says to start autonomous iteration, do not remain in planning-only mode. Complete the required alignment choices, then **bind a loop before the first autonomous cycle**. Loop binding is MANDATORY, not optional. Work through the mechanisms in priority order; record proof for each attempt. Only when every native mechanism is proven unavailable may you record `degraded_resume`.

**P1 - Native platform loop (must attempt first on Claude Code / Codex):**
- Claude Code: `/loop`, scheduled task, cloud Routine, or desktop scheduled task invoking Claude.
- Codex: thread automation (same-thread heartbeat), standalone/project automation, cloud task, or `codex exec` driven by a scheduler.

**P2 - External harness (fallback when P1 is unavailable):**
- cron, launchd, CI scheduler, SDK/CLI loop, or other external process that relaunches cycles. Record the exact command and schedule.

**P3 - Degraded resume (only after P1 AND P2 are both proven unavailable):**
- `degraded_resume`: no native loop and no external harness could be bound. The run continues in the current session only. STATUS.md must carry a red `[DEGRADED - no native loop bound]` marker. This is a marked downgrade, never an equal mode, and must never be presented as successful autonomous iteration.

If a mechanism binds, record `scheduled_resume` (P1), `external_harness` (P2), or `active_session_loop` (an in-session platform loop is actively running with checkpoint cadence). Do not record `degraded_resume` while any P1/P2 option remains unattempted.

```yaml
loop_binding:
  mode: scheduled_resume | external_harness | active_session_loop | degraded_resume   # degraded_resume only after P1+P2 exhausted
  platform: codex | claude_code | other
  schedule_id: ""
  trigger_interval_minutes: 10   # HARD MAX 25; lower is better for overnight runs. Must not exceed 25.
  created_at: "ISO-8601"
  next_wakeup_at: "ISO-8601"
  resume_command_or_action: ""
  proof:
    - "automation id, cron entry, scheduled task, active /loop config, or harness command"
  attempts:                       # record every P1/P2 mechanism tried, pass or fail
    - mechanism: "/loop"
      result: bound | unavailable | forbidden
      note: ""
```

### Loop Persistence Rule

Once a loop/timer is bound, it **must stay bound until the run ends**. The run ends only when: the user-set `max_iterations` is exhausted, the token/budget wall is hit, the user stops it, or a true hard-stop boundary is reached. Do not close, cancel, or unregister the schedule mid-run. Only during end-of-run cleanup (after the final cycle) may the schedule/automation be torn down. Closing the loop early to "take a break" or because the current cycle finished is a violation - the next cycle must still be able to wake.

## Required State

In `quick_autonomy`, task queue, progress, and budget live inside `.bagel/state.yaml`. Create separate files only in `full_genesis`:

- `.bagel/progress.json` (full mode; quick mode uses `state.yaml`)
- `.bagel/task_queue.json` (full mode; quick mode uses `state.yaml`)
- `.bagel/runs/<run_id>/handoff.json`
- `.bagel/ledger/recovery-log.md` (or `ledger.yaml` recovery section in quick mode)
- `.bagel/ledger/next-dispatch.md`
- `.bagel/runtime_capabilities.yaml`
- `.bagel/run_budget.yaml` (or `state.yaml` budget section in quick mode)

Task shape:

```json
{
  "id": "EX-012",
  "goal": "Improve first-run setup reliability",
  "priority": "high",
  "acceptance_criteria": [
    "Fresh clone setup command succeeds",
    "Failure modes are documented"
  ],
  "allowed_files": ["package.json", "README.md", "scripts/setup.*"],
  "status": "pending"
}
```

Budget shape:

```yaml
budget:
  max_cycles: 12
  max_wall_clock_hours: 8
  max_cost_usd: null
  max_consecutive_failures_same_gate: 3
  checkpoint_every_minutes: 30
  stop_when_budget_exhausted: write_resume_checkpoint
```

Telemetry shape:

```yaml
telemetry:
  run_started_at: "ISO-8601"
  elapsed_minutes: 0
  cycles_started: 0
  cycles_completed: 0
  agents_dispatched: 0
  review_agents_dispatched: 0
  context_compactions: 0
  recovery_events: 0
  timer_wakeups: 0
  screenshots_captured: 0
  tests_run: 0
  estimated_tokens_used: null
  token_source: unavailable | platform_reported | estimated_from_transcript
```

Update telemetry at every cycle and surface the key numbers in `.bagel/STATUS.md`. If token usage is unavailable, say so; do not invent precision.

## Session Contract

Each agent session:

1. Reads assigned task, acceptance criteria, constraints, and progress.
2. Handles exactly one bounded unit.
3. Forms a short hypothesis before editing.
4. Works in the smallest safe scope.
5. Runs relevant verification.
6. Does not delete, weaken, or bypass tests/checks to pass.
7. Writes handoff.
8. Leaves clean state or records why it cannot.
9. Never declares success without evidence.

10. Updates telemetry before handoff.

## Self-Provisioning Contract

If the next cycle needs a missing local capability, create it as part of the work when inside the autonomy contract:

- test, lint, typecheck, benchmark, screenshot, browser, layout, or experiment scripts,
- project-local fixtures, seed data, mock servers, or reproducibility harnesses,
- small gate-verifier scripts recorded in `.bagel/ledger/gate-verifiers.md`,
- manual evidence tables when automation is not yet practical.

Do not stop merely because the project did not already contain a verifier. Stop only when provisioning requires credentials, paid external resources, production infrastructure, destructive migration/deletion, major dependency or framework replacement not preapproved, or a core product/research direction decision.

## Handoff

Write `.bagel/runs/<run_id>/handoff.json`:

```json
{
  "task_id": "",
  "status": "passed | failed | blocked | partial",
  "summary": "",
  "hypothesis": "",
  "files_changed": [],
  "commands_run": [],
  "verification_results": [],
  "remaining_risks": [],
  "next_step": ""
}
```

## Clean State Rule

Each cycle should leave:

- no obvious broken build,
- no temporary debug code,
- no unrelated file changes,
- no hidden failing checks,
- no removed tests used to fake success,
- progress ledger updated,
- next action written.

If clean state is impossible, isolate the work and mark the run `partial` or `failed`.

## Quota and Resume

If model/API quota, rate limit, or platform runtime expires:

1. Write checkpoint and handoff.
2. Set `.bagel/state.yaml` (or `.bagel/state.json` in full mode) to `waiting_for_capacity`.
3. Record the next runnable command/action.
4. Schedule a wakeup or leave a precise resume instruction when scheduling is unavailable.
5. On resume, continue from the latest valid checkpoint and progress state.

The user should not wake up to an ambiguous stopped state. The project must either be progressing, waiting for capacity with a resume plan, or explicitly blocked by an autonomy-contract boundary.

## Capability-Based Resume

Use the detected capability level:

- `single_session`: finish one bounded unit, then write handoff and stop.
- `degraded_resume` (was `manual_resume`): write the exact command/message/action needed to continue, and mark STATUS.md `[DEGRADED - no native loop bound]`. Only reached after P1+P2 in the Start Gate are exhausted.
- `scheduled_resume`: schedule the next cycle if the platform exposes a scheduler; record schedule id.
- `external_harness`: write machine-readable task queue and allow the harness to launch the next agent session.

If a scheduler is unavailable after exhausting P1+P2, do not claim that the run will wake itself. State `degraded_resume` in `.bagel/state.yaml` or `.bagel/state.json` and mark STATUS.md.

## Cycle Stop Check

At the end of every cycle, write:

```json
{
  "stop_semantics": "progressing | waiting_for_capacity | degraded_resume | blocked_hard_stop | complete",
  "next_action": "",
  "resume_artifact": ".bagel/runs/<run_id>/handoff.json"
}
```

Also update:

```yaml
cycle_accounting:
  cycle_id: 7
  started_at: "ISO-8601"
  ended_at: "ISO-8601"
  elapsed_minutes: 12
  agents_dispatched_delta: 2
  compactions_delta: 1
  verification_commands_delta: 3
  timer_wakeup_used: true
```

## Worktree Isolation

Use isolated worktrees/sandboxes for risky or parallel work when available. Before using them, protect user changes according to `references/rework-sandbox.md`.

Success path:

- verify,
- merge/apply,
- update progress,
- checkpoint.

Failure path:

- record evidence,
- rollback/discard isolated work,
- create a smaller retry task or alternative approach.
