# Git Governance

Use this for any BAGEL run that modifies files in a git repository, especially with multiple agents or long autonomous work.

## Goals

- Keep each task's blast radius small.
- Preserve user changes.
- Make rollback cheap.
- Let agents work in parallel without corrupting each other.
- Merge only verified, reviewable increments.

## Core Rules

1. Never use destructive git commands unless the user explicitly asks.
2. Inspect worktree state before branch, merge, rollback, or cleanup.
3. Separate user changes from agent changes.
4. One task gets one branch/worktree when isolation is available.
5. No agent writes outside its declared ownership without renegotiating.
6. Merge through the orchestrator, not directly by workers.
7. Every merge requires verification evidence and a change record.

## Repository Preflight

### Step 0: Repo Guarantee (MANDATORY before any file modification)

Before dispatching any write work, guarantee the working folder is a git repository. Rollback, branch isolation, and the `rollback_point_present_for_risk` gate all depend on this and silently break otherwise.

```bash
git rev-parse --is-inside-work-tree
```

If it succeeds, continue to Step 1. If it fails (not a repo):

1. Ask the user once: "This folder is not a git repo. BAGEL needs one for safe rollback and branch isolation during the autonomous run. Initialize one now? (recommended: yes)"
2. On **yes** or default: `git init` -> **add `.bagel/` to the user's `.gitignore` before any commit** (see warning below) -> add a baseline `.gitignore` if none exists -> `git add -A` -> `git commit -m "BAGEL baseline before autonomous run"`. Record the commit SHA as the rollback floor in `.bagel/state.yaml`.

**🔴 T1.3 Privacy protection (MANDATORY):** Before `git add -A`, ensure `.bagel/` is in the user's project `.gitignore`. The `.bagel/` control plane contains user goals, decisions, captured screenshots/evidence, error logs, and potentially PII or secrets from runtime captures. Committing it to the user's repo is an irreversible privacy leak. Run:
```bash
# Add .bagel/ to user .gitignore if not already present
grep -qxF '.bagel/' .gitignore 2>/dev/null || echo '.bagel/' >> .gitignore
grep -qxF '*.bagel-worktrees/' .gitignore 2>/dev/null || echo '*.bagel-worktrees/' >> .gitignore
```
If the user explicitly wants `.bagel/` tracked (rare), they must opt in explicitly — the default is to ignore it.
3. On **explicit no**: set the `project_under_version_control` hard gate to `fail`. Do not start autonomous write work. Explain that without version control every change is irreversible and rollback is impossible - this is a true precondition, not a negotiable preference.

Never modify project files in a non-git folder during an autonomous run. Git init is the single cheapest insurance against an overnight run producing damage you cannot undo.

### Step 1: Worktree state

Before dispatching write work:

```bash
git status --short
git branch --show-current
git rev-parse --show-toplevel
git worktree list
```

Classify:

- **User changes:** pre-existing, unrelated, or not produced by current worker.
- **Agent changes:** produced by current BAGEL task.
- **Generated changes:** build outputs, caches, reports.
- **Unknown changes:** require caution; do not overwrite.

If the worktree is dirty, either:

- create a worktree from the current state when safe,
- stash/commit only agent-owned changes with explicit record,
- if unknown/user changes block safe isolation, isolate the rework onto a fresh non-destructive branch that preserves those changes intact and continue; pause only if preservation itself would require a destructive or irreversible action (a true hard-stop).

Do not reset, checkout over, clean, or force-delete user changes.

## Branch and Worktree Model

Recommended names:

```text
bagel/<run-id>/base
bagel/<run-id>/task/<task-id>
bagel/<run-id>/review/<task-id>
bagel/<run-id>/recovery/<issue-id>
```

Worktree location:

```text
../.bagel-worktrees/<repo-name>/<run-id>/<task-id>/
```

Prefer a sibling directory outside the main worktree. Do not place nested Git worktrees under the repository's tracked tree unless the repository already has an explicit ignored convention for that path.

Branch metadata:

```yaml
branch:
  name: "bagel/RUN-001/task/VS-003"
  task_id: "VS-003"
  base_ref: "..."
  owner_agent: "implementer-2"
  allowed_paths:
    - "src/billing/**"
    - "tests/billing/**"
  forbidden_paths:
    - ".bagel/constitution.yaml (quick) or .bagel/constitution.json (full)"
  status: active | ready_for_review | merged | discarded | blocked
  worktree_path: "../.bagel-worktrees/repo/RUN-001/VS-003"
```

Store metadata in `.bagel/git/branches.yaml`.

## File Ownership and Locks

Before parallel work, create `.bagel/git/locks.yaml`. These YAML records are the authoritative ownership ledger, but acquisition must be serialized by the orchestrator or an integration manager. Workers do not edit lock state unless assigned a lock-management task.

```yaml
locks:
  - id: "LOCK-001"
    owner: "agent-implementer-vs003"
    task_id: "VS-003"
    paths:
      - "src/billing/**"
      - "tests/billing/**"
    mode: write
    acquired_at: "ISO-8601"
    heartbeat_at: "ISO-8601"
    expires_at: "ISO-8601"
    status: requested | active | stale | released | revoked
```

Lock modes:

- `read`: may inspect, not edit.
- `write`: may edit listed paths.
- `exclusive`: no other writer may touch related files.
- `coordination`: orchestrator-only files such as `.bagel/state.yaml` or `.bagel/state.json`, task queue, evolution ledger.

Workers can request lock expansion when they discover a real need. The orchestrator may grant it after checking conflicts. Workers must not silently edit outside ownership.

## Lock Acquisition Protocol

In `parallel_advanced`, acquire the filesystem lock first with atomic `mkdir`:

```bash
mkdir ".bagel/git/locks/<resource-id>" 2>/dev/null
```

If `mkdir` fails, another worker owns the lock. Do not proceed until the lock expires and is safely reclaimed, or choose a path-disjoint task.

Inside the lock directory write:

```yaml
lock:
  resource: ""
  owner_agent_id: ""
  owner_session_id: ""
  acquired_at: "ISO-8601"
  expires_at: "ISO-8601"
  heartbeat_ref: ""
```

Then use this sequence for every write lock:

1. Refresh `.bagel/git/locks.yaml`, `.bagel/git/branches.yaml`, and `.bagel/agents/registry.yaml`.
2. Check path overlap using exact paths plus glob expansion when possible.
3. Check shared-file policy for generated files, schemas, lockfiles, configs, and `.bagel/*`.
4. Write a `requested` lock record.
5. Re-read the lock file and confirm no conflicting request appeared.
6. Promote to `active`, set `acquired_at`, `heartbeat_at`, `expires_at`, owner, and task.
7. Dispatch only after the active lock appears in the worker envelope.

If the platform has no atomic filesystem lock primitive, only the orchestrator/integration manager may perform this sequence, and concurrent lock grants are forbidden.

## Heartbeat and Stale Locks

- Active workers update heartbeat through their status report, not by editing lock files directly.
- Orchestrator updates `heartbeat_at` when it receives evidence that the worker is alive.
- A lock is stale only when `expires_at` passed and the worker has no recent registry heartbeat.
- Before reclaiming a stale lock, preserve branch/worktree path, diff summary, handoff if any, and commands run.
- Reclaimed locks become `revoked`; replacement workers receive a fresh lock id.

Do not expire locks merely because a task is slow. Expire only after evidence preservation.

## Single-Agent Mode

When only one writer exists and no parallel work is planned:

- path locks may be represented as one coarse `single_writer` lock,
- branch/worktree isolation is still preferred for risky or existing-project changes,
- merge queue may be a simple checklist,
- no worker may merge to base without the orchestrator/integration step.

## Parallel Safety

Tasks can run in parallel only when:

- allowed path sets do not overlap,
- no shared generated files will be written,
- no shared schema/contract/migration is touched by more than one task,
- dependency order is clear,
- verification can run independently.

Do not parallelize:

- broad refactors,
- dependency upgrades,
- migrations,
- shared design system rewrites,
- global state/routing/auth changes,
- generated lockfiles unless one owner controls them,
- `.bagel/` control state writes except by orchestrator.

## Worker Git Contract

Workers may:

- edit files inside allowed paths,
- run verification,
- report needed path expansion,
- produce patch/diff summary.

Workers must not:

- merge to base,
- rebase shared branches,
- delete branches/worktrees,
- rewrite history,
- modify lockfiles unless assigned,
- commit unrelated changes,
- resolve conflicts by choosing blindly.

## Merge Queue

Use `.bagel/git/merge-queue.yaml`:

```yaml
queue:
  - task_id: "VS-003"
    branch: "bagel/RUN-001/task/VS-003"
    status: pending_review
    required_checks:
      - "unit"
      - "typecheck"
      - "spec_review"
    affected_paths:
      - "src/billing/**"
```

Merge process:

1. Verify worker handoff and diff.
2. Run required checks.
3. Run spec/code review when risk warrants it.
4. Rebase or merge latest base in the isolated branch if needed.
5. Resolve conflicts explicitly and record rationale.
6. Run post-merge verification.
7. Write evolution change record.
8. Update agent context and user briefing if needed.
9. Release or revoke locks and update agent registry.

Before merge, evaluate the gate predicates `parallel_ownership_safe`, `worker_did_not_merge`, `merge_inputs_clean`, `review_level_satisfied`, and `rollback_point_present_for_risk`.

## Conflict Handling

Conflict classes:

- **Text conflict:** same lines changed.
- **Semantic conflict:** no textual conflict but behavior overlaps.
- **Contract conflict:** schema/API/event changed incompatibly.
- **Generated artifact conflict:** lockfile, snapshot, generated code.
- **Governance conflict:** `.bagel` state, task queue, decisions, context.

Rules:

- Text conflicts require a small integration task.
- Semantic conflicts require reviewer or domain owner.
- Contract conflicts block dependent merges until contract decision is recorded.
- Generated artifact conflicts should be regenerated by one owner.
- Governance conflicts are resolved only by orchestrator.

Never let a worker resolve conflicts by guessing across another worker's scope.

## Rollback

Rollback should be scoped:

- task branch not merged: discard branch/worktree after preserving evidence.
- merged task: revert that merge/patch when possible.
- partial file regression: revert hunks only if ownership is clear.
- broad failure: restore from rollback point and replay safe tasks.

Every rollback needs:

- rollback point,
- affected change records,
- verification after rollback,
- updated task queue,
- updated context freshness.

## Corner Cases

### Dirty base branch

Do not start parallel workers from ambiguous dirty state. Classify changes and create a safe base snapshot first.

### Two workers need same file

Pause one worker, split the file by ownership if possible, or serialize through merge queue.

### Worker discovers required out-of-scope file

Return `NEEDS_SCOPE_EXPANSION` with rationale, path, risk, and verification plan. Orchestrator decides.

### Generated files differ by environment

Assign one generator owner. Other workers do not edit generated output.

### Dependency lockfile changes

Single owner only. Run install/test in integration branch. Do not merge competing lockfile changes.

### User edits during run

Treat user edits as higher priority. Refresh project understanding, mark affected locks stale, and rebase/replan around the user's changes.

### Merge passes tests but changes product intent

Block and route to Constitutional Court or user alignment review.
