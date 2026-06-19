# Runtime Capabilities

Use before promising autonomous long-running work, dispatching agents, scheduling resume, or handling quota exhaustion.

BAGEL is autonomy-first. Do not copy the example booleans below as platform facts. Detect the actual runtime, then bind to the strongest available native loop, scheduler, subagent, hook, browser, cloud, and non-interactive capabilities. Downgrade only after a concrete capability check fails or the user/platform policy forbids it.

Prefer the runtime detector before hand-writing this file:

```bash
python scripts/detect_runtime_capabilities.py <project-root>
# writes <project-root>/.bagel/runtime_capabilities.yaml (positional, like every
# other BAGEL script). `--out <path>` still overrides; no args prints to stdout.
```

The detector gives conservative observed facts; platform adapter references explain how to upgrade or bind the available primitives.

`true_subagents.observed` starts as **`unknown`**, not `true` — CLI presence is an *adapter claim*, never an observation. It is flipped to `observed: true` only by the Task PostToolUse hook (`scripts/attest_subagent.py`) when a real isolated dispatch actually runs, which also writes the bound proof. Under attested mode the proof must trace to that signed dispatch (see `references/platform-attestation.md`).

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
runtime_capabilities:
  platform: codex | claude_code | other
  detected_at: "ISO-8601"
  capabilities:
    true_subagents:
      adapter_claim: true
      observed: true | false | unknown
      proof_ref: ".bagel/evidence/runtime/subagent-proof.yaml"
      last_verified_at: "ISO-8601"
    timers_or_wakeup:
      adapter_claim: true
      observed: true | false | unknown
      proof_ref: ".bagel/evidence/runtime/loop-proof.yaml"
      last_verified_at: "ISO-8601"
    hooks:
      adapter_claim: true
      observed: true | false | unknown
      proof_ref: ".bagel/evidence/runtime/hooks-proof.yaml"
      last_verified_at: "ISO-8601"
    browser_or_visual:
      adapter_claim: true
      observed: true | false | unknown
      proof_ref: ".bagel/evidence/runtime/visual-proof.yaml"
      last_verified_at: "ISO-8601"
```

V2 rule: `adapter_claim` is not proof. It only says the platform adapter believes the capability should exist. `observed: true` requires a real `proof_ref` file created during this run.

Proof files must be structured YAML and pass `scripts/runtime_proof_check.py`. Empty files or unrelated notes are not proof.

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
2. Map native scheduling/loop capability to `scheduled_resume` or `external_harness` - attempt every native mechanism first; `degraded_resume` is only for after all are proven unavailable. `scheduled_resume` requires `timers_or_wakeup.observed: true` and a proof file.
3. Map native subagents/background agents to R3 review capability only when `true_subagents.observed: true` and the proof shows isolated context. Adapter claims alone are R1/R2 at most.

## Review Honesty Mode

```yaml
review_environment:
  true_subagents_observed: true | false
  session_isolation: true | false
  review_honesty_mode: isolated_review | single_session_honesty
```

If `single_session_honesty`, same-session review is capped at R1/R2 by platform proof. Do not claim R3/R4, do not final-accept high-risk or full expert runs without external/true-subagent review, and mark STATUS with `[REVIEW INDEPENDENCE LIMITED]`.
4. Map native hooks/non-interactive mode/cloud tasks to gate enforcement, resume, and automation options. Hooks cannot be marked enabled unless `hooks.observed: true`.
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
