# Multi-Agent Coordination

Use this when BAGEL dispatches more than one agent or alternates between governance and execution roles.

## Principle

Maximize agent autonomy inside clear ownership boundaries. Do not solve coordination by over-constraining agents; solve it by defining ownership, escalation, evidence, merge gates, and recovery.

## Agent Layers

### Governance Layer

- Orchestrator
- Project Cartographer
- User Alignment Curator
- Constitutional Court
- Integration Manager when separate

These roles own coordination, truth, gates, and alignment. They do not implement product code.

### Execution Layer

- Implementers
- Scenario/Test generators
- Debuggers
- Refactor workers
- Reviewers
- Red-team agents

These roles own bounded tasks. They do not change scope, merge branches, or rewrite governance state unless assigned.

## When To Use Multiple Agents

Use parallel agents when tasks are:

- independently verifiable,
- path-disjoint or safely lockable,
- not dependent on unmerged decisions,
- not touching shared schemas/migrations/design systems,
- small enough to merge independently.

Use sequential agents when tasks:

- touch the same files,
- change shared contracts,
- require global architecture decisions,
- need ordered migration/refactor steps,
- involve user-facing direction changes.

Use reviewers at the independence level required by `references/quality-assurance.md`. Use R3/R4 independent reviewers when:

- implementation risk is medium/high,
- worker touched shared code,
- behavior is user-facing,
- prior attempts failed,
- final/excellence-loop quality is being assessed.

## Dispatch Registry

Maintain `.bagel/agents/registry.yaml`:

```yaml
agents:
  - id: "agent-impl-vs003"
    role: "implementer"
    task_id: "VS-003"
    branch: "bagel/RUN/task/VS-003"
    locks: ["LOCK-001"]
    status: active | done | blocked | cancelled | merged
    started_at: "ISO-8601"
    last_seen: "ISO-8601"
```

Maintain `.bagel/agents/dependencies.yaml`:

```yaml
dependencies:
  - task: "VS-004"
    waits_for: ["VS-003"]
    reason: "Uses billing contract introduced by VS-003"
```

## Dispatch Envelope Additions

Every worker gets:

```text
AGENT_ID:
TASK_ID:
BRANCH_OR_WORKTREE:
LOCKS:
ALLOWED_PATHS:
FORBIDDEN_PATHS:
DEPENDENCIES:
CONTEXT_CAPSULES:
SCOPE_EXPANSION_PROTOCOL:
MERGE_POLICY: worker never merges
```

## Freedom With Guardrails

Workers may challenge the orchestrator when local evidence shows the plan is wrong.

Challenge format:

```yaml
status: NEEDS_PLAN_REVISION
evidence:
  - "..."
problem: "..."
recommended_change: "..."
scope_impact: local | task | milestone | global
risk_if_ignored: "..."
```

The orchestrator must evaluate these challenges. Do not force a worker to follow a stale plan when it has better local evidence. If the challenge changes product intent, route to alignment/court.

## Coordination Loop

1. Orchestrator selects tasks.
2. Check dependency graph.
3. Check path locks.
4. Assign branch/worktree.
5. Dispatch worker.
6. Worker reports status and proposed scope/context changes.
7. Reviewer verifies if required.
8. Merge queue integrates.
9. Orchestrator updates evolution, context, briefing, task queue.

## Shared File Policy

Shared files require serialization or an owner:

- package/dependency manifests,
- lockfiles,
- global route maps,
- shared schemas/contracts,
- design tokens,
- auth/session providers,
- root config,
- `.bagel/*` governance files.

If multiple tasks need shared files:

1. Create a separate shared-foundation task.
2. Merge it first.
3. Rebase/recreate dependent task briefs.
4. Resume parallel work after shared state stabilizes.

## Dead Agent and Timeout

If an agent stalls:

1. Check registry heartbeat.
2. Preserve branch/worktree.
3. Mark agent `stalled`.
4. Inspect handoff/diff if any.
5. Either resume with same context, spawn replacement with handoff, or discard isolated work.

Do not let stalled locks block the project indefinitely. Expire locks only after preserving evidence.

## Conflicting Agents

If agents disagree:

- factual/code reality → reviewer or Project Cartographer decides from evidence,
- product intent → Orchestrator/User/Constitutional Court,
- quality judgment → reviewer at required QA independence level or red-team,
- merge conflict → Integration Manager/Orchestrator,
- scope expansion → Orchestrator with autonomy contract.

Record the resolution in evolution ledger.

## Integration Manager

For large parallel runs, assign an Integration Manager role or let Orchestrator enter that mode. It owns:

- merge queue,
- conflict classification,
- post-merge verification,
- context freshness updates,
- rollback point validation,
- ensuring worker output is not accepted without evidence.

Integration Manager does not implement features except small conflict-resolution patches within documented scope.

## Anti-Interference Gates

Block dispatch or merge when:

- lock overlap is unresolved,
- dependency is unmet,
- worker edited outside allowed paths without approved scope expansion,
- branch base is stale and risky,
- generated/shared file conflict exists,
- context capsule is stale/disputed,
- user changed relevant files mid-run,
- verification does not cover affected behavior.
