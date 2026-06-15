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
- `manual_resume`: write the exact command/message/action needed to continue.
- `scheduled_resume`: schedule the next cycle if the platform exposes a scheduler; record schedule id.
- `external_harness`: write machine-readable task queue and allow the harness to launch the next agent session.

If a scheduler is unavailable, do not claim that the run will wake itself. State `manual_resume_required` in `.bagel/state.yaml` or `.bagel/state.json`.

## Cycle Stop Check

At the end of every cycle, write:

```json
{
  "stop_semantics": "progressing | waiting_for_capacity | manual_resume_required | blocked_hard_stop | complete",
  "next_action": "",
  "resume_artifact": ".bagel/runs/<run_id>/handoff.json"
}
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
