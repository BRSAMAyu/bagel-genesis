# Atomic Rework Sandbox Procedure

When a mutation to a committed node requires cascade rework, execute in isolation.

## When to Use

Use Atomic Rework Sandbox when:
1. A mutation affects committed nodes
2. Causality depth > 1 (A → B, B → C)
3. Clearing cost < 50% of remaining budget

## Why Isolation?

Cascade rework without isolation causes:
- Conflicting changes across agents
- Lost work
- State corruption
- Difficulty rollback

## Sandbox Types

### Type A: Git Worktree (Recommended)
- Full repository isolation
- Easy merge/discard
- Best for code changes
- Required for parallel risky code changes when git is available

### Type B: Copy Directory
- Copy entire project
- Manual diff/merge
- Best for structural changes

### Type C: Branch
- Create feature branch
- Merge when validated
- Best for long rewrites

## Procedure: Git Worktree Method

For general branch, lock, merge queue, and multi-agent rules, read `references/git-governance.md` and `references/multi-agent-coordination.md`. This file only describes isolated rework.

### Step 0: Safety Preflight

Before creating, merging, deleting, or reverting anything:

```bash
git status --short
git branch --show-current
git worktree list
```

Classify changes as user changes, agent changes, or generated artifacts. Do not overwrite, delete, reset, or revert user changes. If classification is unclear, do not stop: branch/worktree the rework on a non-destructive path that preserves all ambiguous changes intact, record the classification uncertainty in `.bagel/ledger/recovery-log.md`, and continue. Prefer patches and non-destructive branches over destructive cleanup. Pause only if the ambiguous change is a true hard-stop (irreversible/non-recoverable).

Also check `.bagel/git/locks.yaml` and `.bagel/agents/registry.yaml` if they exist. Do not start rework that overlaps active locks unless the orchestrator serializes or cancels the conflicting work.

### Step 1: Create Sandbox

```bash
cd /path/to/project
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
SANDBOX_NAME="rework_${TIMESTAMP}"
git worktree add ../.bagel-worktrees/${REPO_NAME}/${SANDBOX_NAME} -b rework/${TIMESTAMP}
```

### Step 2: Perform Rework in Sandbox

```bash
cd ../.bagel-worktrees/${REPO_NAME}/${SANDBOX_NAME}
# Apply mutation
# Test changes
# Verify product graph consistency
```

### Step 3: Validate

Run validation for hard coherence gates, contract checks, slice completion, and relevant unit/integration/browser tests. Use existing project commands when available. If no verifier exists, create the smallest project-local verifier or record exact manual evidence.

### Step 4: Merge or Discard

**If valid:** merge or apply the sandbox changes only after confirming the base branch and preserving unrelated work. Do not assume the branch is `main`.

**If invalid:** discard the sandbox only after confirming it contains no unsaved user work. Avoid force deletion unless the branch/worktree contains only generated rework.

## Max Causality Depth

Default: **2**

```
A breaks B: ALLOWED
fixing B breaks C: STOP
```

If depth would exceed 2:
1. Reject mutation
2. Propose alternative approach
3. Escalate to human

**Rationale:** Deep cascades are unpredictable and can consume remaining budget.

## Clearing Ledger

Log clearing actions using the single authoritative schema in `references/clearing-policy.md`. Do not define a second clearing ledger shape here.

## Alternative: Controlled Rollback

If rework cost is high but reversibility is high:

Create a rollback branch or patch from the current branch, revert only affected commits or hunks, then run the relevant verification. Do not use destructive reset/checkout flows for rollback unless the user explicitly approves.

## Integration with State Machine

- S9: Clearing check runs this procedure if needed
- Any state: Can trigger if mutation detected

## Failure Modes

### Depth Exceeded
**Signal:** "Causality depth would exceed 2"
**Action:** Reject mutation, escalate

### Sandbox Validation Fails
**Signal:** Validation suite reports failures
**Action:** Discard sandbox, find alternative approach

### Sandbox Merge Conflict
**Signal:** Git merge conflicts
**Action:** Manual resolution required, may need human

### Budget Exhausted
**Signal:** Remaining budget < clearing cost
**Action:** Isolate the mutation, record the budget conflict, continue safe independent work, and notify the user only if no useful autonomous path remains or a hard-stop boundary is involved.
