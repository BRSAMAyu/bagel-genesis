# Evidence Replay Protocol

Use whenever a worker claims a command, benchmark, visual check, research verifier, or metric result.

V2 evidence is not just "a file exists." It must be replayable or explicitly non-replayable with reviewer evidence.

## Evidence Record

Store runnable evidence under `.bagel/evidence/**/evidence.yaml`:

```yaml
evidence:
  - evidence_id: EV-047-NPM-TEST
    command: "npm test"
    cwd: "."
    git_ref: "abc123"
    started_at: "ISO-8601"
    finished_at: "ISO-8601"
    exit_code: 0
    stdout_path: ".bagel/evidence/cycle-047/npm-test.stdout.txt"
    stderr_path: ".bagel/evidence/cycle-047/npm-test.stderr.txt"
    stdout_sha256: "..."
    stderr_sha256: "..."
    env_digest:
      platform: "darwin"
      node: "v22"
      python: "3.12"
      package_lock_hash: "sha256..."
    replay_policy:
      mode: exact | sampled | not_replayable
      reason_if_not_replayable: null
```

For `not_replayable`, record `manual_evidence_reviewer` and why replay is impossible.

Run:

```bash
python scripts/evidence_replay_check.py <project-root>
```

Use `--replay` only when exact commands are safe and `git_ref` matches current HEAD.
