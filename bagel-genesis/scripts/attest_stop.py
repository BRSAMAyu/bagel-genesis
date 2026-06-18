#!/usr/bin/env python3
"""Claude Code Stop hook — runs the BAGEL validator suite when the agent's turn
ends, independently of whether the agent chose to run it.

This closes the "voluntary substrate" residual (enforcement-honesty.md:39):
the suite is no longer something the agent can simply not run. The Stop hook
fires on every turn end (or subagent stop) and executes bagel_v3_check.py,
surfacing failures to the user.

Install (merge into .claude/settings.json):
    "Stop": [
      {"matcher": "", "hooks": [{"type":"command","command":"python3 .../attest_stop.py"}]}
    ]

Behavior:
  - Runs `python3 scripts/bagel_v3_check.py <project_root>`.
  - On failure: prints the failure summary to stderr AND adds context to stdout
    so the user sees it. The hook does NOT block the stop (exit 0) by default —
    it informs rather than traps, because a blocked Stop can wedge the session.
    Set BAGEL_STOP_HOOK_BLOCK=1 in the shell env to make failures block (exit 2).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def _skill_dir() -> Path:
    return Path(__file__).resolve().parent


def main() -> int:
    root = _project_root()
    suite = _skill_dir() / "bagel_v3_check.py"
    if not suite.exists():
        return 0
    # Only run if this looks like a BAGEL project (avoid noisy runs on non-BAGEL dirs).
    if not (root / ".bagel").exists():
        return 0
    result = subprocess.run(
        [sys.executable, str(suite), str(root)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120,
    )
    if result.returncode != 0:
        # Surface the tail of the failure to the user.
        tail = "\n".join(result.stdout.splitlines()[-12:])
        sys.stderr.write(
            "BAGEL Stop-hook validator FAILED at turn end:\n"
            f"{tail}\n"
            "These gates were not satisfied. The agent's output this turn is not BAGEL-verified.\n"
        )
        if os.environ.get("BAGEL_STOP_HOOK_BLOCK") == "1":
            sys.stdout.write(f'{{"decision":"block","reason":"BAGEL validator suite failed at turn end; see stderr."}}')
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
