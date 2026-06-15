# User Briefing Protocol

Use this to keep the user aligned without forcing them to read raw logs or implementation chatter.

## Purpose

The user should be able to understand the project at different depths:

- quick confidence check,
- practical decision review,
- deep project understanding,
- handoff material for another person.

For existing projects, the briefing must explain both current reality and intended direction: what already exists, what will be preserved, what will be changed, and what remains uncertain.

## Files

Use the canonical tree in `references/governance-data-model.md`. The required human entry point is `.bagel/STATUS.md`; deeper files live under `.bagel/user_briefing/`.

For non-software projects, adapt names:

- `architecture-or-structure.md` can describe research structure, book outline, argument map, dataset plan, or creative system.
- `quality-and-risks.md` covers factual, logical, aesthetic, editorial, experimental, or engineering risks.

## Layer 1: Quick Status

Write for a user with one minute:

- current phase,
- what is done,
- what is being improved,
- whether autonomy is safe to continue,
- next autonomous action,
- whether user input is needed.

`.bagel/STATUS.md` must contain this layer first and link to `user_briefing/quick-status.md`, `decision-dashboard.md`, and `quality-and-risks.md`.

## Layer 2: Decision Dashboard

Write for a user making decisions:

```yaml
decision:
  id: "D-014"
  status: decided | proposed | needs_user | challenged
  summary: "..."
  rationale: "..."
  alternatives: ["...", "..."]
  impact: local | milestone | global
  reversibility: high | medium | low
```

Include system-made decisions so the user can audit autonomy.

## Layer 3: Deep Dive

Write for full understanding:

- original vision and how it evolved,
- current project state and how it was verified,
- key tradeoffs,
- why the current approach is coherent,
- how to run/verify/review the work,
- remaining risks,
- future directions that were intentionally not executed.

## Update Cadence

Update user briefing:

- after deep alignment,
- after each milestone,
- after major recovery,
- before and after excellence loop,
- before final delivery,
- whenever user instruction changes direction.
- whenever evolution ledger records a user-visible or decision-relevant change.

Do not dump raw logs. Convert logs into decisions, evidence, risks, and next actions.

## Progressive Disclosure

Do not make one giant user document. Use layers:

- `.bagel/STATUS.md`: single entry point and conflict indicator.
- `quick-status.md`: one-minute confidence and next action.
- `current-project-reality.md`: what exists now and how verified.
- `decision-dashboard.md`: what was decided, by whom, and what needs the user.
- `evolution-summary.md`: major changes over time with links to change records.
- `deep-dives/`: complete explanations for users who want depth.

Each layer should link downward to deeper evidence instead of duplicating all detail.

If canonical state files disagree — in quick mode: `state.yaml`, `constitution.yaml`, `ledger.yaml`; in full mode: `state.json`, `progress.json`, `task_queue.json`, `gates/status.yaml`, `human-decisions.yaml` — mark `.bagel/STATUS.md` as `STATE CONFLICT` and stop normal autonomous continuation until the orchestrator reconciles the source files.

## Reliability

User-facing briefing must distinguish:

- verified fact,
- system inference,
- user-approved decision,
- open assumption,
- stale or disputed information.

When briefing conflicts with agent-facing context or code reality, mark it stale, write a conflict report, and update only after evidence review.

## User Instruction Handling

When the user sends a new instruction mid-run:

1. Treat it as highest priority input.
2. Compare it to the constitution, decision map, and current state.
3. If aligned, incorporate it and update briefing.
4. If risky or contradictory, challenge it with options.
5. Persist the resulting decision before continuing.

The user is the authority over goals, but the system must be honest about consequences.
