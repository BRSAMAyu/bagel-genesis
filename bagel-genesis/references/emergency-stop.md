# Emergency Stop

Use when the user explicitly stops a run or BAGEL detects a hard-stop that must halt all normal work.

Emergency stop is preservation-first. Never run destructive reset automatically.

Run:

```bash
python scripts/emergency_stop.py <project-root> --reason "user_requested_stop"
```

The script:

1. writes `.bagel/STOP_REQUESTED`,
2. captures git status,
3. writes `.bagel/emergency/recovery-instructions.md`,
4. sets `state.run_status = emergency_stopped`,
5. records that no destructive reset was performed.

Resume only after user clearance or a new explicit instruction. Verify with:

```bash
python scripts/emergency_stop_check.py <project-root>
```
