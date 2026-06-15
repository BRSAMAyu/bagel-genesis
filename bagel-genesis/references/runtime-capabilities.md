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
  session_mode: single_session | manual_resume | scheduled_resume | external_harness
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
| `manual_resume` | User or later agent must restart | Stop with exact resume instruction |
| `scheduled_resume` | Platform can wake a thread/task | Schedule/checkpoint and continue later |
| `external_harness` | Separate loop runner can launch sessions | Run queued tasks under explicit harness policy |

If uncertain, choose the lower capability level. Do not describe manual resume as unattended progress.

For known agentic platforms, uncertainty means "check the adapter," not "assume false":

- Codex: read `references/platform-codex.md`. Codex can use app automations, project/worktree background runs, cloud tasks, `codex exec`, subagents, hooks, in-app browser, and worktrees when enabled by the user's environment.
- Claude Code: read `references/platform-claude-code.md`. Claude Code can use scheduled tasks, `/loop`, cloud/desktop scheduling, subagents, background agents/teams, hooks, worktrees, and `claude -p`/SDK automation when enabled by the user's environment.
- Other platforms: document the equivalent native loop/scheduler/agent primitives or fall back to `manual_resume`.

## Preflight

1. Detect platform and load the matching adapter reference when available.
2. Map native scheduling/loop capability to `scheduled_resume` or `external_harness` before considering `manual_resume`.
3. Map native subagents/background agents to R3 review capability when they have isolated context and inspect artifacts rather than worker self-justification.
4. Map native hooks/non-interactive mode/cloud tasks to gate enforcement, resume, and automation options.
5. Record unsupported features explicitly only after checking the adapter and current environment.
6. Choose run mode from `references/quality-assurance.md`.
7. Set maximum cycle length and checkpoint cadence.
8. If quota/rate limit is likely, require `loop-runtime.md` handoff and resume artifacts before implementation.

## Self-Provisioning Rule

If a needed verifier, scenario runner, screenshot check, benchmark harness, experiment script, or setup command is missing, BAGEL should create or configure the smallest project-local capability needed to continue, then record it in `.bagel/ledger/gate-verifiers.md` or the relevant experiment/evidence ledger. Missing tooling is a task, not a blocker, unless creating it crosses an autonomy-contract boundary such as paid resources, credentials, production infrastructure, destructive migration, or major framework replacement.

## Stop Semantics

Every cycle must end in one of:

- `progressing`: another cycle is already scheduled or running.
- `waiting_for_capacity`: quota/runtime unavailable; resume artifact exists.
- `manual_resume_required`: no scheduler exists; exact next action exists.
- `blocked_by_contract`: user decision or external access is required.
- `complete`: completion and excellence gates passed.

Never leave the state ambiguous.
