# Evolution Ledger

Use this to make project evolution traceable, reviewable, and recoverable.

## Purpose

Every meaningful project change should answer:

- What changed?
- Why did it change?
- Who/which role initiated it?
- What evidence justified it?
- What artifacts were affected?
- How was it verified?
- How can it be reviewed or rolled back?

Do not rely on chat history for evolution. Persist it.

## Files

Create:

```text
.bagel/evolution/
├── index.yaml
├── timeline.md
├── change-records/
│   └── CHG-YYYYMMDD-NNN.yaml
├── rollback-points/
│   └── RB-YYYYMMDD-NNN.yaml
├── audit-reports/
└── conflict-reports/
```

## Change Record

Write one record for every state transition, value slice, major refactor, alignment update, user instruction, recovery action, or excellence-loop improvement:

```yaml
change:
  id: "CHG-20260615-001"
  timestamp: "ISO-8601"
  category: alignment | implementation | refactor | recovery | verification | briefing | context_update
  initiator: user | orchestrator | implementer | reviewer | court | red_team
  summary: "..."
  rationale: "..."
  linked_decisions: ["ADR-014"]
  linked_tasks: ["VS-003", "EX-012"]
  affected_artifacts:
    - path: "src/..."
      kind: code | test | doc | config | bagel_state
  verification:
    commands: []
    reviews: []
    evidence_files: []
  rollback:
    safe_to_revert: true
    rollback_point: "RB-20260615-001"
    notes: "..."
  alignment_impact:
    updates_agent_context: true
    updates_user_briefing: true
    changes_constitution: false
```

## Rollback Point

Create rollback points before risky changes:

- architecture or data model changes,
- broad refactors,
- replacing existing behavior,
- dependency/toolchain changes,
- recovery actions,
- any action marked low reversibility.

Rollback record:

```yaml
rollback_point:
  id: "RB-20260615-001"
  created_before: "CHG-20260615-004"
  git_ref: "branch-or-commit-if-available"
  snapshot: ".bagel/snapshots/SNAP-..."
  protected_user_changes:
    - "..."
  restore_instructions:
    - "..."
```

If git is unavailable, use snapshots, patches, copied artifacts, or explicit file manifests. Never use destructive rollback that risks user changes.

## Timeline

Maintain `.bagel/evolution/timeline.md` as a human-scannable changelog:

```text
2026-06-15
- CHG-001: Established project understanding from repo evidence.
- CHG-002: Implemented VS-001 onboarding loop; verified with npm test.
- CHG-003: Updated agent_context after module responsibility changed.
```

The timeline is for orientation. The YAML change records are authoritative.

## Audit Pass

Run an audit pass before major milestones and final delivery:

- every implemented task has a change record,
- every major decision links to evidence,
- every context update links to a source change,
- every rollback point is valid or intentionally expired,
- user instructions are reflected in decision map and briefing,
- no worker changed behavior without updating relevant context.

Write results to `.bagel/evolution/audit-reports/`.

## Conflict Handling

When change records, code reality, agent context, and user briefing disagree:

1. Treat code/artifact evidence and verified commands as primary for current reality.
2. Treat constitution/autonomy contract as primary for intended direction.
3. Mark stale documents explicitly.
4. Write `.bagel/evolution/conflict-reports/CONFLICT-*.md`.
5. Assign resolution owner: Orchestrator, Project Cartographer, User Alignment Curator, or Constitutional Court.
6. Do not dispatch implementation depending on disputed facts until resolved or scoped around the conflict.
