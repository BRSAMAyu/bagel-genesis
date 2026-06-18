#!/usr/bin/env python3
"""Claude Code PostToolUse hook for Bash — writes a signed attestation of
every Bash command the agent runs.

Install (in the project's .claude/settings.json, hooks section):

    {
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": "python3 /abs/path/to/bagel-genesis/scripts/attest_bash.py"}]
          }
        ]
      }
    }

The hook receives on stdin a JSON object with the tool name and the
tool_response (stdout/stderr/exit code). It writes an HMAC-signed
attestation to .bagel/attestations/ATT-NNNNNN.yaml. The signing key is read
from BAGEL_ATTEST_KEY in the hook process's environment — set it in the
user's shell rc, NOT in the repo, and NOT in any file the agent can read:

    # ~/.zshrc  (user shell, not the agent)
    export BAGEL_ATTEST_KEY="$(openssl rand -hex 32)"

The agent's Bash subprocesses DO inherit this variable (Claude Code's Bash
tool runs in the full process env; see references/platform-attestation.md for
the honest threat model). The signature layer therefore raises the bar against
an uninformed/lazy agent but does not, on its own, bind a claim to bytes a real
command produced against an informed agent. The gates that DO bind regardless
of key secrecy are the action-layer ones: the append-only guard on
.bagel/attestations/ and the STOP_REQUESTED interception in attest_fileop.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    """Claude Code hooks run with cwd = project root. Fall back to env."""
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(cwd).resolve()


def _capture_stdout_file(root: Path, stdout_bytes: bytes) -> tuple[str, str]:
    """Persist the captured stdout under .bagel/attestations/outputs/ and
    return (relative_path, sha256). The validator reads this file back to
    re-extract metrics, so extracts_from binds to attested bytes."""
    out_dir = root / ".bagel/attestations/outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(stdout_bytes).hexdigest()
    rel = f".bagel/attestations/outputs/{digest}.out"
    (root / rel).write_bytes(stdout_bytes)
    return rel, digest


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed hook input is not the agent's research to fail on — no-op.
        return 0

    tool_name = str(event.get("tool_name") or "")
    # PostToolUse events may nest the tool name under tool_response in some
    # harness versions; accept either shape.
    if tool_name.lower() not in {"bash", "bash"}:
        return 0

    tool_input = event.get("tool_input") or {}
    tool_response = event.get("tool_response") or {}
    command = str(tool_input.get("command") or "")
    cwd = str(tool_input.get("cwd") or os.getcwd())

    # tool_response shape varies by harness; normalize.
    stdout = tool_response.get("stdout")
    stderr = tool_response.get("stderr")
    exit_code = tool_response.get("exit_code")
    if stdout is None and isinstance(tool_response, str):
        stdout = tool_response
    if stdout is None:
        stdout = ""
    if stderr is None:
        stderr = ""
    if exit_code is None:
        # Some harnesses put exit under "metadata" or as "interrupted".
        exit_code = 0 if not tool_response.get("interrupted") else 130

    stdout_bytes = stdout.encode("utf-8") if isinstance(stdout, str) else bytes(stdout)
    stderr_bytes = stderr.encode("utf-8") if isinstance(stderr, str) else bytes(stderr)

    root = _project_root()
    rel_out, stdout_sha = _capture_stdout_file(root, stdout_bytes)
    stderr_sha = hashlib.sha256(stderr_bytes).hexdigest()

    # Import the signing lib lazily so the hook can be syntax-checked without
    # the rest of the skill installed.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from attestation_lib import write_record  # noqa: E402

    tool_output = {
        "exit_code": int(exit_code),
        "stdout_path": rel_out,
        "stdout_sha256": stdout_sha,
        "stderr_sha256": stderr_sha,
        "stdout_bytes": len(stdout_bytes),
        "wall_time_seconds": None,  # populated in Step 2 via PreToolUse pairing
    }
    written = write_record(
        root=root,
        tool="Bash",
        tool_input={"command": command, "cwd": cwd},
        tool_output=tool_output,
    )
    if written is None:
        # No key configured — silently no-op. The validator will report the
        # run as UNATTESTED so the user knows the attestation tier is off.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
