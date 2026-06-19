#!/usr/bin/env python3
"""Claude Code PostToolUse hook for the Task (subagent) tool — writes a signed
attestation of every REAL isolated subagent dispatch, and refreshes the
true_subagents runtime proof from that dispatch.

Why this exists (RUN-001 finding 3): `runtime_proof_check.py` is honest but
shape-bound — a hand-written `.bagel/evidence/runtime/subagent-proof.yaml` with
zero real dispatch behind it passes, byte-indistinguishable from a genuine one.
This hook closes the lazy path: the proof's `verifier_agent_id` and the bound
attestation come from the platform's `tool_response` for a real Task call,
captured by the HOOK process (not typed by the agent). Under attested mode,
`runtime_proof_check.py` requires the true_subagents proof to be backed by a
real signed Task attestation, so a forged proof file with no matching
attestation now FAILS.

Install (merge into .claude/settings.json hooks.PostToolUse):

    {"matcher": "Task",
     "hooks": [{"type": "command",
                "command": "python3 /abs/path/to/bagel-genesis/scripts/attest_subagent.py"}]}

Honest limit (same as the rest of the attestation layer, see
references/platform-attestation.md): the signing key is readable from the
agent's Bash subprocess, so an *informed* agent can still mint a forged Task
attestation. This raises the bar against the uninformed/lazy path and binds the
proof to a real dispatch whenever key isolation holds; full closure is external
(CI). The Task `tool_response` shape also varies by harness version, so agent-id
extraction is best-effort with several fallbacks.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(cwd).resolve()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_AGENT_ID_RE = re.compile(r"agent[ _-]?id['\"]?\s*[:=]\s*['\"]?([0-9a-fA-F]{8,})", re.IGNORECASE)
_TOKENS_RE = re.compile(r"subagent_tokens['\"]?\s*[:=]\s*(\d+)", re.IGNORECASE)


def _deep_find(obj: Any, keys: tuple[str, ...]) -> Any:
    """Find the first value for any of `keys` anywhere in a nested dict/list."""
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if str(k) in keys and v not in (None, "", {}):
                    return v
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def _extract_dispatch(event: dict[str, Any]) -> dict[str, Any]:
    """Best-effort, harness-shape-tolerant extraction of the real dispatch."""
    tool_input = event.get("tool_input") or {}
    tool_response = event.get("tool_response")

    agent_id = _deep_find(event, ("agent_id", "agentId", "agentID")) or ""
    tokens = _deep_find(event, ("subagent_tokens",))

    # Fallback: parse the agent id / tokens out of a text tool_response.
    text = ""
    if isinstance(tool_response, str):
        text = tool_response
    elif isinstance(tool_response, dict):
        # Common text-bearing keys.
        for k in ("output", "text", "content", "result", "stdout"):
            v = tool_response.get(k)
            if isinstance(v, str):
                text += "\n" + v
    if not agent_id and text:
        m = _AGENT_ID_RE.search(text)
        if m:
            agent_id = m.group(1)
    if tokens is None and text:
        m = _TOKENS_RE.search(text)
        if m:
            tokens = int(m.group(1))

    return {
        "agent_id": str(agent_id or ""),
        "subagent_type": str(tool_input.get("subagent_type") or ""),
        "description": str(tool_input.get("description") or ""),
        "subagent_tokens": tokens,
        # A returned-and-completed Task call is an isolated-context dispatch by
        # construction on Claude Code/Codex; record it as such for the proof.
        "isolated_context": True,
    }


def _write_proof(root: Path, dispatch: dict[str, Any], attestation_id: str | None) -> None:
    """Refresh the convenience runtime proof file from the REAL dispatch. The
    authoritative binding is the signed attestation; this file mirrors it so the
    existing runtime_proof_check shape gate also sees a real verifier_agent_id."""
    import yaml  # local import: keep the hook importable without yaml for --self-test

    proof_dir = root / ".bagel" / "evidence" / "runtime"
    proof_dir.mkdir(parents=True, exist_ok=True)
    proof = {
        "proof_id": "PROOF-SUBAGENT-001",
        "capability": "true_subagents",
        "observed_at": _now_iso(),
        "mechanism": "Claude Code Task tool — isolated subagent dispatch (hook-attested)",
        "isolated_context": True,
        "verifier_agent_id": dispatch["agent_id"] or "unknown",
        "result": "pass",
        "attestation_ref": attestation_id or "",
        "subagent_type": dispatch["subagent_type"],
        "subagent_tokens": dispatch["subagent_tokens"],
        "proof_summary": (
            "Hook-captured real Task dispatch. verifier_agent_id and "
            "attestation_ref come from the platform tool_response, not agent text."
        ),
        "written_by": "attest_subagent.py (PostToolUse hook)",
    }
    (proof_dir / "subagent-proof.yaml").write_text(
        yaml.safe_dump(proof, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def _mark_observed(root: Path) -> None:
    """Flip runtime_capabilities.true_subagents.observed → true FROM the real
    dispatch the hook just witnessed. The detector now defaults this to
    `unknown` (CLI presence is not observation); the hook is the honest writer
    that turns it true, because it ran in the harness on a genuine Task call.
    Guarded round-trip: any failure is a no-op so the turn never wedges."""
    import yaml

    rc_path = root / ".bagel" / "runtime_capabilities.yaml"
    if not rc_path.exists():
        return
    data = yaml.safe_load(rc_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return
    rc = data.get("runtime_capabilities")
    caps = rc.get("capabilities") if isinstance(rc, dict) else None
    ts = caps.get("true_subagents") if isinstance(caps, dict) else None
    if not isinstance(ts, dict):
        return
    ts["observed"] = True
    ts["last_verified_at"] = _now_iso()
    rc_path.write_text(
        yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    tool_name = str(event.get("tool_name") or "")
    if tool_name.lower() not in {"task", "agent"}:
        return 0

    root = _project_root()
    dispatch = _extract_dispatch(event)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from attestation_lib import write_record  # noqa: E402

    written = write_record(
        root=root,
        tool="Task",
        tool_input={
            "subagent_type": dispatch["subagent_type"],
            "description": dispatch["description"],
        },
        tool_output={
            "agent_id": dispatch["agent_id"],
            "isolated_context": dispatch["isolated_context"],
            "subagent_tokens": dispatch["subagent_tokens"],
        },
    )
    attestation_id = written.stem if written is not None else None

    # Always refresh the proof file from the real dispatch, even unattested —
    # so the verifier_agent_id is platform-sourced rather than agent-typed. When
    # the key IS set, the proof is additionally bound to the signed attestation.
    try:
        _write_proof(root, dispatch, attestation_id)
        _mark_observed(root)
    except Exception:
        # A proof-write failure must never wedge the agent's turn.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
