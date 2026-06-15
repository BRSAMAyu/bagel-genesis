# Runtime Capabilities

Use before promising autonomous long-running work, dispatching agents, scheduling resume, or handling quota exhaustion.

BAGEL is autonomy-first. Do not copy the example booleans below as platform facts. Detect the actual runtime, then bind to the strongest available native loop, scheduler, subagent, hook, browser, cloud, and non-interactive capabilities. Downgrade only after a concrete capability check fails or the user/platform policy forbids it.

Prefer the runtime detector before hand-writing this file:

```bash
python scripts/detect_runtime_capabilities.py --out .bagel/runtime_capabilities.yaml
```

The detector gives conservative observed facts; platform adapter references explain how to upgrade or bind the available primitives.

## Required Artifact

Create `.bagel/runtime_capabilities.yaml`:

```yaml
runtime:
  platform: codex | claude_code | other
  platform_adapter: "references/platform-codex.md | references/platform-claude-code.md | custom | none"
  session_mode: single_session | degraded_resume | scheduled_resume | external_harness
  supports_true_subagents: detected_true_or_false
  supports_context_isolation: detected_true_or_false
  supports_timers_or_wakeup: detected_true_or_false
  supports_background_execution: detected_true_or_false
  supports_git_worktrees: detected_true_or_false
  supports_browser_or_visual_checks: detected_true_or_false
  supports_tool_self_provisioning: detected_true_or_false
  max_safe_cycle_minutes: 45
  permitted_claims:
    - "Can leave durable checkpoints"
  forbidden_claims:
    - "Will keep running after quota exhaustion without a scheduler"
  resume_artifact: ".bagel/runs/<run_id>/handoff.json"
  next_action_artifact: ".bagel/ledger/next-dispatch.md"
```

## Capability Levels

| Level | Meaning | Allowed Promise |
|---|---|---|
| `single_session` | One agent call/session only | Finish current bounded task or write handoff |
| `degraded_resume` (was `manual_resume`) | User or later agent must restart; reached only after all native loops/harnesses proven unavailable | Stop with exact resume instruction + STATUS.md `[DEGRADED]` marker |
| `scheduled_resume` | Platform can wake a thread/task | Schedule/checkpoint and continue later |
| `external_harness` | Separate loop runner can launch sessions | Run queued tasks under explicit harness policy |

If uncertain, choose the lower capability level. Do not describe degraded resume as unattended progress. Note: on Claude Code and Codex the platform-native loop (`/loop`, automations, scheduled tasks, cloud tasks, `codex exec`) is timer-capable even when crontab/launchctl are absent - do not falsely force `degraded_resume` on these platforms.

For known agentic platforms, uncertainty means "check the adapter," not "assume false":

- Codex: read `references/platform-codex.md`. Codex can use app automations, project/worktree background runs, cloud tasks, `codex exec`, subagents, hooks, in-app browser, and worktrees when enabled by the user's environment.
- Claude Code: read `references/platform-claude-code.md`. Claude Code can use scheduled tasks, `/loop`, cloud/desktop scheduling, subagents, background agents/teams, hooks, worktrees, and `claude -p`/SDK automation when enabled by the user's environment.
- Other platforms: document the equivalent native loop/scheduler/agent primitives or fall back to `degraded_resume` (only after proving native mechanisms unavailable).

## Preflight

1. Detect platform and load the matching adapter reference when available.
2. Map native scheduling/loop capability to `scheduled_resume` or `external_harness` - attempt every native mechanism first; `degraded_resume` is only for after all are proven unavailable.
3. Map native subagents/background agents to R3 review capability when they have isolated context and inspect artifacts rather than worker self-justification.
4. Map native hooks/non-interactive mode/cloud tasks to gate enforcement, resume, and automation options.
5. Record unsupported features explicitly only after checking the adapter and current environment.
6. Choose run mode from `references/quality-assurance.md`.
7. Set maximum cycle length and checkpoint cadence.
8. If quota/rate limit is likely, require `loop-runtime.md` handoff and resume artifacts before implementation.

For explicit autonomous iteration, manual planning is not an acceptable terminal state. The preflight must produce one of:

- configured loop/timer/automation/scheduled task,
- configured external harness or CLI command that will relaunch cycles,
- active platform loop with checkpoint cadence,
- `degraded_resume` with a clear statement that true unattended continuation is unavailable AND a red `[DEGRADED - no native loop bound]` marker in STATUS.md - only reached after all native mechanisms are proven unavailable.

Do not ask the user to enter a generic Plan mode after they have delegated autonomous iteration. Use alignment choices to capture decisions, then start or bind the loop.

## Self-Provisioning Rule

If a needed verifier, scenario runner, screenshot check, benchmark harness, experiment script, or setup command is missing, BAGEL should create or configure the smallest project-local capability needed to continue, then record it in `.bagel/ledger/gate-verifiers.md` or the relevant experiment/evidence ledger. Missing tooling is a task, not a blocker, unless creating it crosses an autonomy-contract boundary. **The authoritative, complete carve-out list lives in `references/recovery-protocol.md` (Environment and Tool Failures → gray-zone rule).** Read it before concluding a missing tool is a hard-stop — common cases like adding a dev dependency that touches a lockfile are *not* hard-stops when the change is pre-authorized, small, reversible, project-local, or isolated to a disposable worktree branch; they are hard-stops only when none of those apply. Do not decide from the summary list here alone.

## Stop Semantics

Every cycle must end in one of:

- `progressing`: another cycle is already scheduled or running.
- `waiting_for_capacity`: quota/runtime unavailable; resume artifact exists.
- `degraded_resume`: no scheduler exists after exhausting native mechanisms; exact next action exists; STATUS.md marked `[DEGRADED]`.
- `blocked_hard_stop`: a genuine hard-stop boundary was hit (credentials, paid resources, production data, irreversible action, or no safe autonomous path remains after recovery). Not laziness — the run tried and exhausted alternatives. Distinct from `degraded_resume` (no scheduler) and `waiting_for_capacity` (temporary).
- `complete`: completion and excellence gates passed.

Never leave the state ambiguous.
