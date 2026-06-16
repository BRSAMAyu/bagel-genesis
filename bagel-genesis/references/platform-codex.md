# Codex Platform Adapter

Use when `runtime.platform: codex`. This adapter maps BAGEL's abstract orchestration model to Codex-native capabilities. Source facts come from the Codex manual sections for Automations, Cloud environments, Non-interactive mode, Subagents, Hooks, Browser, and Worktrees.

## Capability Mapping

Record capabilities in `.bagel/runtime_capabilities.yaml` using the strongest capability actually available in the current Codex surface:

```yaml
runtime:
  platform: codex
  platform_adapter: "references/platform-codex.md"
  session_mode: scheduled_resume | external_harness | degraded_resume
  supports_true_subagents: true
  supports_context_isolation: true
  supports_timers_or_wakeup: true
  supports_background_execution: true
  supports_git_worktrees: true
  supports_browser_or_visual_checks: true
  supports_tool_self_provisioning: true
```

You **must attempt** each native loop mechanism in priority order before any fallback: (1) thread automation (same-thread heartbeat), (2) standalone/project automation for independent scheduled runs, (3) cloud task, (4) `codex exec` driven by cron/launchd/CI. Record proof for each attempt. Only when **all** of these are proven unavailable or user-forbidden may you record `degraded_resume` (formerly `manual_resume`) and mark STATUS.md `[DEGRADED - no native loop bound]`. `degraded_resume` is a marked downgrade, never an equal mode. Loop interval must be <= 25 minutes.

## Native Primitives

| BAGEL Need | Codex Primitive |
|---|---|
| Supervisor heartbeat | App thread automation, standalone/project automation, cloud task, or `codex exec` under cron/launchd |
| Inner Orchestrator | Fresh Codex subagent/custom agent/thread spawned by Supervisor |
| Repeated wake/resume | App thread automation for same-thread heartbeat; standalone/project automation for independent scheduled runs |
| Background repository work | App automation in local project or background worktree; Codex cloud task when cloud environment is available |
| Scriptable loop runner | `codex exec`, optionally JSONL output, output schema, and `resume` |
| Worker/reviewer isolation | Codex subagents or custom agents; use worktrees for write isolation |
| Gate hooks | Codex hooks such as `Stop`, `SubagentStop`, `PostToolUse`, `PreCompact`, and `SessionStart` |
| Browser/visual checks | Codex in-app browser, Browser plugin, Playwright, or project-local screenshot tooling |
| Work isolation | Codex worktrees or BAGEL sibling `../.bagel-worktrees/...` |

## Dispatch Mapping

Map BAGEL roles to Codex agents:

- Supervisor: main thread or automation prompt. Owns user proxying, heartbeat, hard-stop arbitration, and Orchestrator respawn.
- Orchestrator: fresh subagent/custom agent/separate thread spawned by Supervisor when true subagents are available. Collapse into main only when true subagents are unavailable and record `supervisor.mode: collapsed_no_true_subagents`.
- Project Cartographer: read-heavy explorer/custom agent.
- Implementer: worker/custom agent with write scope and allowed paths.
- Spec Reviewer, Code Quality Reviewer, Independent Reviewer, Red-Team Oracle: separate subagents that read artifacts/diffs/tests, not implementer chat.
- Integration Manager: main thread mode or dedicated custom agent with merge-queue scope.

For R3 review, the reviewer must be a true subagent or separate Codex run with a clean prompt and artifact inputs. Same-thread role switching remains R1/R2.

## Nested Supervisor Pattern

Codex runs should prefer:

```text
Main thread/automation: BAGEL Supervisor
  -> BAGEL Orchestrator subagent/custom agent/thread
      -> specialist subagents (Implementer, Reviewer, Runtime Doctor, Evaluation Architect)
```

The Supervisor heartbeat can be 30-60 minutes if the inner BAGEL loop is healthy. The inner BAGEL loop remains <=25 minutes. If subagent timers are unavailable, schedule only the Supervisor; it reads `.bagel/supervisor/heartbeat.yaml`, checks Orchestrator liveness, and respawns or nudges the inner Orchestrator when needed.

## Automation Prompt Contract

The wake prompt must be a **pointer, not a script**. It must NOT contain run mechanisms (which cycle to run, which files to read, how to dispatch) - those live in SKILL.md and `.bagel/` state. Stuffing mechanism into the wake prompt causes repetition pollution every cycle, drift from SKILL.md, and token waste. The wake prompt's only job is: orient the agent and point it at its state.

```text
You are resuming a BAGEL Genesis autonomous run. Read .bagel/STATUS.md and .bagel/state.yaml to see where the run is, then follow the BAGEL Genesis SKILL.md for the next bounded action. If state.yaml fails to parse (corrupted by a crash), read .bagel/snapshots/manifest.json, restore the latest valid snapshot, and continue from there.
```

For Supervisor heartbeats:

```text
You are the BAGEL Genesis Supervisor heartbeat. Read .bagel/supervisor/resume-capsule.md, .bagel/supervisor/heartbeat.yaml, .bagel/STATUS.md, and .bagel/state.yaml. If the Orchestrator is stale or state is corrupted, restore/respawn according to references/supervisor-resilience.md; otherwise do not absorb worker details.
```

**Why this is enough:** STATUS.md carries the Morning Briefing (phase, last delta, next action, blockers); state.yaml carries the full machine state (task queue, gates, budget, loop_binding, telemetry). SKILL.md's Loading Matrix tells the agent which reference to read for the current decision. The agent progressively discloses only what the current phase needs.

Use a thread automation when continuity in the current conversation matters. Use a standalone/project automation or cloud task when each cycle should start fresh from `.bagel/` and report findings independently.

## Non-Interactive and Cloud Runs

Use `codex exec` when BAGEL must be launched from CI, cron, launchd, or another scheduler. Prefer JSONL and schema outputs for machine-readable handoff. Use `codex exec resume` only when preserving a previous Codex session is useful; BAGEL's primary resume source remains `.bagel/`.

Use Codex cloud tasks when a remote container, setup script, pinned runtimes, secrets handling, or cached environment is preferable. Record environment assumptions and setup commands in `.bagel/project_inventory/commands.md` and `.bagel/evidence/setup.md`.

## Hooks

Use hooks to reinforce, not replace, BAGEL judgment:

- `Stop`: verify `stop_semantics` is written and not ambiguous.
- `SubagentStop`: require a structured handoff from workers/reviewers.
- `PostToolUse`: run formatting, lightweight lint, or command-output capture.
- `PreCompact`/`PostCompact`: ensure state, progress, and next dispatch are persisted.
- `SessionStart`: remind the agent to reconstruct from `.bagel/`.

If hooks are unavailable or untrusted, record that and continue with explicit cycle checks.

## Autonomy Bias

When a verifier or tool is missing, create the smallest project-local script, Playwright check, screenshot capture, benchmark, or evidence table needed to continue. Ask the user only when setup requires credentials, paid services, production changes, destructive operations, major dependency/framework replacement, or a constitution/autonomy boundary.
