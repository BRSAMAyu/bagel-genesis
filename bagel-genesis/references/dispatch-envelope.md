# Dispatch Envelope

Use before Orchestrator sends any worker, reviewer, Runtime Doctor, Expert Councilor, or Principal Expert.

```yaml
dispatch_envelope:
  role: ""
  agent_id: ""
  session_id: ""
  task_id: ""
  dispatcher_role: Orchestrator
  git_target:
    type: branch | worktree | current  # branch names may contain '/'; worktree_path must exist; current = serial/non-parallel-safe only
    branch: ""
    worktree_path: ""
  # legacy field branch_or_worktree is deprecated; use git_target instead
  read_only: []
  write_only: []
  allowed_paths: []
  forbidden_paths: []
  locks:
    - resource: ""
      lock_ref: ".bagel/git/locks/<resource-id>/lock.yaml"
  context_refs: []
  exit_criteria: []
  lane_type: deliverable | control_plane
```

Preflight with `scripts/dispatch_envelope_check.py` before the worker starts.

Rules:

- read paths must exist unless they are generated task-local capsules,
- write/allowed paths are normalized relative paths,
- write tasks require atomic locks,
- context refs must exist and be fresh enough for the task,
- Implementers must not read full `SKILL.md`, global references, or history,
- Supervisor does not dispatch itself or directly own implementation/debug/review tasks.
