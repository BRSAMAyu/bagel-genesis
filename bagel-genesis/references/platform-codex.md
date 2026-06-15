# Codex Platform Adapter

Use when `runtime.platform: codex`. This adapter maps BAGEL's abstract orchestration model to Codex-native capabilities. Source facts come from the Codex manual sections for Automations, Cloud environments, Non-interactive mode, Subagents, Hooks, Browser, and Worktrees.

## Capability Mapping

Record capabilities in `.bagel/runtime_capabilities.yaml` using the strongest capability actually available in the current Codex surface:

```yaml
runtime:
  platform: codex
  platform_adapter: "references/platform-codex.md"
  session_mode: scheduled_resume | external_harness | manual_resume
  supports_true_subagents: true
  supports_context_isolation: true
  supports_timers_or_wakeup: true
  supports_background_execution: true
  supports_git_worktrees: true
  supports_browser_or_visual_checks: true
  supports_tool_self_provisioning: true
```

Use `manual_resume` only when app automations, cloud tasks, non-interactive execution, and local scheduling are all unavailable or forbidden.

## Native Primitives

| BAGEL Need | Codex Primitive |
|---|---|
| Repeated wake/resume | App thread automation for same-thread heartbeat; standalone/project automation for independent scheduled runs |
| Background repository work | App automation in local project or background worktree; Codex cloud task when cloud environment is available |
| Scriptable loop runner | `codex exec`, optionally JSONL output, output schema, and `resume` |
| Worker/reviewer isolation | Codex subagents or custom agents; use worktrees for write isolation |
| Gate hooks | Codex hooks such as `Stop`, `SubagentStop`, `PostToolUse`, `PreCompact`, and `SessionStart` |
| Browser/visual checks | Codex in-app browser, Browser plugin, Playwright, or project-local screenshot tooling |
| Work isolation | Codex worktrees or BAGEL sibling `../.bagel-worktrees/...` |

## Dispatch Mapping

Map BAGEL roles to Codex agents:

- Orchestrator: main thread or automation prompt. Owns `.bagel/` state and merge decisions.
- Project Cartographer: read-heavy explorer/custom agent.
- Implementer: worker/custom agent with write scope and allowed paths.
- Spec Reviewer, Code Quality Reviewer, Independent Reviewer, Red-Team Oracle: separate subagents that read artifacts/diffs/tests, not implementer chat.
- Integration Manager: main thread mode or dedicated custom agent with merge-queue scope.

For R3 review, the reviewer must be a true subagent or separate Codex run with a clean prompt and artifact inputs. Same-thread role switching remains R1/R2.

## Automation Prompt Contract

Codex automations should be durable and resume from `.bagel/`, not from chat memory:

```text
Use $bagel-genesis. Resume the BAGEL run in this project.
Read .bagel/runtime_capabilities.yaml, state.yaml or state.json,
progress state, gates/status.yaml, and ledger/next-dispatch.md.
Execute exactly one bounded cycle: select or continue the next task,
dispatch subagents when useful, run verification, update .bagel state,
and schedule/continue unless stop_semantics is complete or blocked_by_contract.
Do not stop at baseline; continue until the excellence horizon passes.
```

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
