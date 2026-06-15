# Immediate Clearing Policy

Technical debt cannot cross Value Slices. This document defines the clearing protocol.

## Core Invariant

> No committed-node mutation can remain uncleared before next slice.

## State-Machine Position

Run clearing after every completed value slice:

```text
S8(slice N implementation) -> S9(clear slice N mutations) -> S8(slice N+1)
```

Only proceed from S9 to simulations/release when all planned value slices are complete and the clearing invariant is satisfied.

## Uncleared Mutation

An uncleared mutation exists when:
1. A committed node is modified
2. The modification is not reflected in all dependent nodes
3. The next value slice begins

## Detection

On each slice completion (S8 exit):

Use a project-local clearing checker if one exists. If not, perform a structured check and save it to `.bagel/evidence/clearing-VS-NNN.md`:

- committed decisions/contracts touched by the slice,
- dependent files, tests, routes, and documentation,
- whether each dependent artifact was updated,
- commands run,
- remaining uncleared mutations.

If output is non-empty:
1. Create an evidence chain for each mutation
2. Calculate clearing cost for each
3. Apply clearing policy
4. Execute in sandbox if cascade
5. Log to clearing ledger

The agent that caused the mutation may propose cost/depth, but Orchestrator or a reviewer verifies the evidence chain before cascade rework.

## Clearing Options

### Option 1: Full Cascade Rework

**Conditions:**
- `time_to_clear < remaining_budget * 0.5`
- `causality_depth <= 2`
- `reversibility in [high, medium]`

**Procedure:** See references/rework-sandbox.md

### Option 2: Controlled Rollback

**Conditions:**
- `time_to_clear >= remaining_budget * 0.5`
- `reversibility == high`

**Procedure:**
1. Inspect worktree status and protect user changes.
2. Identify rollback point.
3. Create rollback branch or patch.
4. Revert only the mutation under review.
5. Test.
6. Merge, apply, or discard without losing unrelated work.

### Option 3: Human Checkpoint / Fork

**Conditions:**
- `time_to_clear >= remaining_budget * 0.5`
- `reversibility in [medium, low]`
- OR `causality_depth > 2`

**Procedure:**
1. Pause execution
2. Present options to user
3. Await decision
4. Execute per user instruction

### Option 4: Reject and Alternative

**Conditions:**
- `causality_depth > 2`
- No viable rollback path

**Procedure:**
1. Reject mutation
2. Propose alternative implementation
3. Resume with alternative

## Cost Calculation

### Time to Clear

Estimate in hours:
- Single node fix: 0.5-2 hours
- 2-node cascade: 2-4 hours
- 3+ node cascade: 4-8 hours (stop here)

### Causality Depth

```
Level 0: Direct mutation (A → mutation)
Level 1: First-order dependency (A → B → mutation)
Level 2: Second-order dependency (A → B → C → mutation)
Level 3+: STOP - reject mutation
```

Depth is not a bare number. Record concrete evidence:

```yaml
causality_chain:
  - from: "ADR-014"
    to: "src/billing/contract.ts"
    evidence: "contract field changed"
  - from: "src/billing/contract.ts"
    to: "tests/billing/checkout.test.ts"
    evidence: "test fixture imports changed field"
```

If the chain cannot be stated with files/decisions/tests, classify depth as disputed and stop for review. Depth >= 2 requires reviewer confirmation before autonomous cascade; depth > 2 requires human checkpoint unless the user explicitly pre-approved this class of rework.

### Remaining Budget

```
total_budget - time_elapsed
```

Budget is user-specified or estimated from completion horizon.

## Policy Matrix

| Time | Depth | Reversibility | Action |
|------|-------|--------------|--------|
| < 50% | <= 2 | High/Medium | Cascade Rework |
| >= 50% | <= 2 | High | Controlled Rollback |
| >= 50% | <= 2 | Low | Human Checkpoint |
| Any | > 2 | Any | Reject |

## Clearing Ledger Schema

This is the only authoritative clearing ledger schema. Other references should link here instead of defining another shape. All clearing actions are logged to `.bagel/ledger/clearing_log.md`:

```yaml
clearing_action:
  id: CA-YYYY-NNN
  timestamp: ISO-8601
  
  mutation:
    node_id: NODE-XXX
    description: "Changed X to Y"
    reason: "User feedback"
    
  assessment:
    time_estimate_hours: 3
    causality_depth: 1
    causality_chain:
      - from: "..."
        to: "..."
        evidence: "..."
    verified_by: "orchestrator | reviewer"
    reversibility: high
    remaining_budget_hours: 20
    
  decision:
    option: cascade_rework
    rationale: "Cost < 50%, depth <= 2"
    
  execution:
    method: atomic_rework_sandbox | controlled_rollback | reject_alternative | human_checkpoint
    sandbox: rework_20260615_143000
    outcome: merge
    actual_time_hours: 2.5
    
  lessons:
    - "Always validate before commit"
    - "Check dependencies first"
```

## Anti-Patterns

### "We'll fix it in the next sprint"
No. Fix it now or stop.

### "It's just a small change"
Size doesn't matter. Causality depth does.

### "The tests pass"
Tests don't catch all cascading effects.

### "We can add a TODO"
No TODOs for committed nodes.

## Integration with State Machine

- S9: Clearing check after each slice
- Any state: Can trigger if mutation detected

## Escalation

If clearing check fails (cannot clear with available options):

1. Stop execution
2. Report to user
3. Await decision:
   - Provide more budget
   - Accept reduced scope
   - Fork product
