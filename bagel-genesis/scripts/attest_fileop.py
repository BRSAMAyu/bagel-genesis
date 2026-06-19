#!/usr/bin/env python3
"""Claude Code hook for file-write attestation + emergency-stop interception.

Handles THREE hook surfaces (configure all three in .claude/settings.json):

  1. PostToolUse on Write|Edit|MultiEdit — attest file writes. This gives the
     platform a timestamped record of WHEN each .bagel/ file was created/edited,
     signed by the harness key. Validators use this to prove preregistration
     happened BEFORE results (closing the HARKing surface): experiment-plan.yaml's
     attested write-time must precede any attested Bash run that produced a metric.

  2. PreToolUse on Bash — hard-stop interception. If .bagel/STOP_REQUESTED exists,
     the hook returns a non-zero exit with a decision JSON that BLOCKS the tool
     call. This converts the V4 emergency_stop from "advisory, next-cycle" to
     "next-ANY-action" — the user's kill switch actually stops in-flight work.

  3. PreToolUse on Write|Edit|MultiEdit — reject any mutation of
     .bagel/attestations/ by the agent (append-only layer; only the hook may
     write there). This makes the attestation directory tamper-proof at the
     action layer, not just detectable post-hoc.

Install (merge into .claude/settings.json hooks):
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type":"command","command":"python3 .../attest_fileop.py"}]},
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type":"command","command":"python3 .../attest_fileop.py"}]}
    ],
    "PostToolUse": [
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type":"command","command":"python3 .../attest_fileop.py"}]}
    ]

Hook input/output protocol (Claude Code):
  - stdin: JSON {hook_event_name, tool_name, tool_input, tool_response?}
  - PreToolUse exit 0 = allow; exit 2 + JSON {decision:"block", reason:...} = block.
  - PostToolUse always exit 0 (we only observe, never block post-facto).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()


def _read_stdin() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _block(reason: str) -> int:
    """PreToolUse block: exit 2 with Claude Code decision JSON."""
    payload = json.dumps({"decision": "block", "reason": reason})
    sys.stdout.write(payload)
    return 2


def attest_write(root: Path, event: dict) -> None:
    """PostToolUse Write/Edit: sign a file-write attestation."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from attestation_lib import write_record, get_key
    except Exception:
        return
    if get_key() is None:
        return
    ti = event.get("tool_input") or {}
    file_path = str(ti.get("file_path") or ti.get("path") or "")
    if not file_path:
        return
    # Content hash (after write) — re-read the file. For Edit we hash the result.
    try:
        abspath = (root / file_path) if not os.path.isabs(file_path) else Path(file_path)
        content_sha = hashlib.sha256(abspath.read_bytes()).hexdigest() if abspath.exists() else ""
    except Exception:
        content_sha = ""
    write_record(
        root=root,
        tool="Write",
        tool_input={"file_path": file_path},
        tool_output={"content_sha256": content_sha, "op": event.get("tool_name")},
    )


def pretooluse_bash_stop_check(root: Path) -> int | None:
    """PreToolUse Bash: if STOP_REQUESTED, block. Returns exit code or None."""
    if (root / ".bagel/STOP_REQUESTED").exists():
        return _block(
            "BAGEL emergency stop is active (.bagel/STOP_REQUESTED exists). "
            "The user has stopped this run. Clear STOP_REQUESTED only on explicit user resume."
        )
    return None


def pretooluse_write_attestations_guard(root: Path, event: dict) -> int | None:
    """PreToolUse Write/Edit: reject mutation of .bagel/attestations/ by the agent."""
    ti = event.get("tool_input") or {}
    file_path = str(ti.get("file_path") or ti.get("path") or "")
    if ".bagel/attestations/" in file_path.replace("\\", "/"):
        return _block(
            "BAGEL attestation layer is append-only and writable only by platform hooks. "
            f"Refusing agent mutation of {file_path}."
        )
    return None


# Files the agent is always allowed to write even before the control plane exists,
# because they are needed to bootstrap it (the control plane itself, the status
# board, and version-control scaffolding).
_BOOTSTRAP_ALLOW = (".bagel/", "status.md", ".git", ".gitignore", ".gitattributes")


def pretooluse_control_plane_gate(root: Path, event: dict) -> int | None:
    """PreToolUse Write/Edit: the action-boundary forcing function for engagement.

    OPT-IN via BAGEL_REQUIRE_CONTROL_PLANE=1 in the shell env. When enabled, the
    agent may NOT write product/source files until it has actually engaged the
    skill — i.e. until `.bagel/constitution.yaml` exists (the Align artifact). This
    converts "the agent ignored the skill and just wrote code" from a silent pass
    into a blocked action with an instruction. It is the one enforcement that does
    not depend on the agent's willingness, because hooks fire at the tool boundary.

    Disabled by default (returns None) so it never surprises a non-BAGEL repo. Once
    the control plane exists, this is a no-op — engagement has happened.
    """
    if os.environ.get("BAGEL_REQUIRE_CONTROL_PLANE") != "1":
        return None
    if (root / ".bagel/constitution.yaml").exists():
        return None  # control plane engaged; nothing to force
    ti = event.get("tool_input") or {}
    file_path = str(ti.get("file_path") or ti.get("path") or "")
    norm = file_path.replace("\\", "/").lower()
    rel = norm.split(str(root).replace("\\", "/").lower() + "/")[-1]
    if any(rel == a or rel.startswith(a) or a in rel for a in _BOOTSTRAP_ALLOW):
        return None  # bootstrap path — allowed so the agent CAN create the plane
    return _block(
        "BAGEL control plane is not initialized (BAGEL_REQUIRE_CONTROL_PLANE=1). "
        f"Refusing to write product file {file_path} before the run engages the skill. "
        "Create .bagel/constitution.yaml first (Align phase: north star, stop_contract, "
        "research_autonomy if applicable) per SKILL.md Boot Sequence, then proceed. This "
        "block exists because product code written outside the BAGEL control plane is "
        "unreviewed, ungated, and untracked."
    )


def main() -> int:
    event = _read_stdin()
    if not event:
        return 0
    hook_event = str(event.get("hook_event_name") or "")
    tool_name = str(event.get("tool_name") or "")
    root = _project_root()

    # PreToolUse interceptors
    if hook_event == "PreToolUse":
        if tool_name == "Bash":
            blocked = pretooluse_bash_stop_check(root)
            if blocked is not None:
                return blocked
        if tool_name in {"Write", "Edit", "MultiEdit"}:
            blocked = pretooluse_write_attestations_guard(root, event)
            if blocked is not None:
                return blocked
            blocked = pretooluse_control_plane_gate(root, event)
            if blocked is not None:
                return blocked
        return 0

    # PostToolUse Write/Edit: attest the write
    if hook_event == "PostToolUse" and tool_name in {"Write", "Edit", "MultiEdit"}:
        attest_write(root, event)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
