# Claude Code Platform Adapter

Use when `runtime.platform: claude_code`. This adapter maps BAGEL's abstract orchestration model to Claude Code-native capabilities. Source facts come from Claude Code docs for subagents, scheduled tasks, hooks, CLI/programmatic usage, web/desktop/cloud sessions, and agent teams.

## Capability Mapping

Record capabilities in `.bagel/runtime_capabilities.yaml` using the strongest capability actually available:

```yaml
runtime:
  platform: claude_code
  platform_adapter: "references/platform-claude-code.md"
  session_mode: scheduled_resume | external_harness | degraded_resume
  supports_true_subagents: true
  supports_context_isolation: true
  supports_timers_or_wakeup: true
  supports_background_execution: true
  supports_git_worktrees: true
  supports_browser_or_visual_checks: true
  supports_tool_self_provisioning: true
```

You **must attempt** each native loop mechanism in priority order before any fallback: (1) `/loop` for same-session repeated work, (2) scheduled task / cloud Routine / desktop scheduled task invoking Claude, (3) CLI non-interactive execution (`claude -p`/SDK) driven by an external scheduler. Record proof for each attempt. Only when **all** of these are proven unavailable or user-forbidden may you record `degraded_resume` (formerly `manual_resume`) and mark STATUS.md `[DEGRADED - no native loop bound]`. `degraded_resume` is a marked downgrade, never an equal mode. Loop interval must be <= 25 minutes.

## Native Primitives

| BAGEL Need | Claude Code Primitive |
|---|---|
| Repeated wake/resume | Scheduled tasks, `/loop`, cloud Routines, desktop scheduled tasks, or external cron/CI invoking Claude |
| Main orchestrator loop | Main conversation, `/goal`, `/loop`, scheduled prompt, or programmatic/SDK session |
| Worker/reviewer isolation | Built-in/custom subagents, background agents, agent teams, or separate sessions |
| Role prompt mapping | `.claude/agents/*.md`, `~/.claude/agents/*.md`, `--agents` JSON, or agent teams |
| Work isolation | Subagent `isolation: worktree`, background agents, or BAGEL sibling worktrees |
| Gate hooks | Claude Code hooks for lifecycle events, notifications, blocking protected edits, formatting, context reinjection, and audits |
| Scriptable execution | `claude -p`, SDK, CI, or shell scheduler |

## Dispatch Mapping

Map BAGEL roles to Claude Code agents:

- Orchestrator: main session, scheduled task prompt, `/goal`, or programmatic driver.
- Artifact Drafter and Project Cartographer: read/write `.bagel/` governance agents with narrow scopes.
- Implementer: custom subagent with allowed tools and write paths; use worktree isolation for risky or parallel work.
- Spec Reviewer, Code Quality Reviewer, Independent Reviewer, Red-Team Oracle: separate subagents with clean context and artifact-only inputs.
- Integration Manager: main session mode or dedicated agent with merge queue, locks, and post-merge verification.

For R3 review, use a true subagent, background agent, agent team member, or separate session that did not implement the change. Same conversation role switching is not R3.

## Scheduled Prompt Contract

The wake prompt must be a **pointer, not a script**. It must NOT contain run mechanisms (which cycle to run, which files to read, how to dispatch) - those belong in SKILL.md and `.bagel/` state, which the agent loads via progressive disclosure after waking. Stuffing mechanism into the wake prompt causes (a) repetition pollution every cycle, (b) drift from SKILL.md as the skill evolves, (c) token waste. The wake prompt's only job is: orient the agent and point it at its state.

```text
You are resuming a BAGEL Genesis autonomous run. Read .bagel/STATUS.md and .bagel/state.yaml to see where the run is, then follow the BAGEL Genesis SKILL.md for the next bounded action. If state.yaml fails to parse (corrupted by a crash), read .bagel/snapshots/manifest.json, restore the latest valid snapshot, and continue from there.
```

**Why this is enough:** STATUS.md contains the Morning Briefing (current phase, last delta, next action, blocking issues) and state.yaml contains the full machine state (task queue, gates, budget, loop_binding, telemetry). SKILL.md's Loading Matrix tells the agent exactly which reference to read for the decision at hand. The agent progressively discloses only what the current phase needs - it does not load all 31 references or the full skill on every wake.

Use `/loop` for same-session repeated work and polling. Use cloud/desktop scheduled tasks or external CLI scheduling when the run must persist independently of an open session.

## Subagent Files

When project-local agent definitions are useful, create `.claude/agents/` entries that wrap BAGEL role prompts:

```markdown
---
name: bagel-implementer
description: Implements one BAGEL value slice or repair from a dispatch envelope.
tools: Read, Grep, Glob, Bash, Edit, Write
isolation: worktree
---
Read the assigned BAGEL dispatch envelope. Follow agents/implementer.md.
Do not read full SKILL.md, unrelated references, or old transcripts.
Return structured handoff evidence only.
```

Use read-only tools for reviewers and cartographers unless the role owns a `.bagel/` artifact update. Preload only the needed skill/reference content.

## Hooks

Use hooks to make autonomy more reliable:

- Notify only when BAGEL reaches `blocked_hard_stop`.
- Format or lint after edits when project-local commands exist.
- Block protected files unless the current lock/dispatch permits them.
- Re-inject `.bagel/ledger/next-dispatch.md` after compaction or resume.
- Audit settings, dependency, or deployment config changes against the autonomy contract.

Hooks should enforce deterministic checks. Judgment calls still route through BAGEL reviewers, Red-Team, or Constitutional Court.

## Autonomy Bias

When a verifier, visual tool, screenshot pipeline, benchmark, or experiment harness is missing, create the smallest project-local capability that lets the loop continue. Prefer local scripts, temporary fixtures, Playwright/browser checks, benchmark scripts, and manual evidence tables over stopping. Ask the user only for credentials, paid services, production infrastructure, destructive actions, major framework replacement, or constitution/autonomy-boundary decisions.
