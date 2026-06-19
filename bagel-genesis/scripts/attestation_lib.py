#!/usr/bin/env python3
"""Platform attestation layer — append-only, signed records written ONLY by
platform hooks (Claude Code PostToolUse/PreToolUse/Stop), never by the agent.

This closes the structural residual disclosed at enforcement-honesty.md:39
("every validator reads agent-authored YAML; verifies shape, almost never
ground truth"). Attestations are written by a process the agent cannot
control (the hook runs in the harness, not the agent's tool surface) and are
HMAC-signed with a key the agent cannot read. Validators verify the signature
and the append-only monotonic chain, then bind research claims to attested
command outputs — so a claimed metric value must trace to bytes a real
command actually produced, not to an agent-authored YAML.

Design:
- Records live at .bagel/attestations/ATT-NNNNNN.yaml, IDs strictly monotonic.
- Each record carries an HMAC-SHA256 signature over a canonical record body.
  The signing key (BAGEL_ATTEST_KEY env var) is set in the user's shell and
  is NOT readable from the agent's Bash tool (hooks run in the parent harness
  process; the agent's subprocesses do not inherit it).
- The directory is append-only in intent; Step 2's Write/Edit hook will
  reject any mutation of .bagel/attestations/ by the agent. Step 1 relies on
  signature + chain verification to detect tampering post hoc.
- When the key is absent (platform without hooks, or user hasn't configured
  the key), validators run in "unattested" mode and clearly degrade: the
  attestation tier is unavailable, gates fall back to shape-only, and the
  report labels the run UNATTESTED.

This module is imported by both the hook scripts and the validators.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ATTEST_DIR_NAME = "attestations"
ATTEST_ID_RE = re.compile(r"^ATT-(\d{6})$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

# Canonical field order for signing — determinism across writers.
SIGNED_FIELDS = (
    "attestation_id",
    "timestamp",
    "tool",
    "tool_input",
    "tool_output",
    "prev_hash",
)


class AttestationError(Exception):
    """Raised on tampering, broken chain, or bad signature."""


def attest_dir(root: Path) -> Path:
    return root / ".bagel" / ATTEST_DIR_NAME


def get_key() -> bytes | None:
    raw = os.environ.get("BAGEL_ATTEST_KEY")
    if not raw:
        return None
    return raw.encode("utf-8")


def has_key() -> bool:
    return get_key() is not None


def _canonical_body(record: dict[str, Any]) -> bytes:
    """Stable serialization of the signed subset of the record."""
    subset = {k: record.get(k) for k in SIGNED_FIELDS}
    return yaml.safe_dump(subset, sort_keys=True, default_flow_style=False).encode("utf-8")


def sign_record(record: dict[str, Any], key: bytes) -> str:
    digest = hmac.new(key, _canonical_body(record), hashlib.sha256).hexdigest()
    return f"hmac-sha256:{digest}"


def verify_signature(record: dict[str, Any], key: bytes) -> bool:
    sig = str(record.get("signature") or "")
    if not sig.startswith("hmac-sha256:"):
        return False
    expected = sign_record(record, key).split(":", 1)[1]
    return hmac.compare_digest(sig.split(":", 1)[1], expected)


def _next_id(records: list[dict[str, Any]]) -> str:
    max_n = 0
    for r in records:
        m = ATTEST_ID_RE.match(str(r.get("attestation_id") or ""))
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"ATT-{max_n + 1:06d}"


def _chain_hash(records: list[dict[str, Any]]) -> str:
    """Hash over the concatenation of prior (id, timestamp, signature) — a
    simple forward chain so inserting or reordering a record breaks it."""
    h = hashlib.sha256()
    for r in records:
        h.update(str(r.get("attestation_id") or "").encode())
        h.update(str(r.get("timestamp") or "").encode())
        h.update(str(r.get("signature") or "").encode())
    return h.hexdigest()


def load_records(root: Path) -> list[dict[str, Any]]:
    """Load all attestation records sorted by numeric id. Returns [] if absent."""
    d = attest_dir(root)
    if not d.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(d.glob("ATT-*.yaml")):
        if not ATTEST_ID_RE.match(path.stem):
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            raise AttestationError(f"attestation {path.name}: unparseable YAML")
        if isinstance(data, dict):
            data["_path"] = str(path.relative_to(root))
            out.append(data)
    return out


def validate_chain(root: Path, key: bytes | None) -> tuple[list[str], list[dict[str, Any]]]:
    """Verify signatures + monotonic chain. Returns (errors, verified_records).

    If key is None, every record's signature is treated as unverifiable and
    an error is emitted per record — callers should check has_key() first to
    decide between 'unattested mode' (no records expected) and 'tampered'.
    """
    errors: list[str] = []
    records = load_records(root)
    if not records:
        return errors, []

    prev_chain = _chain_hash([])  # genesis: empty-record-set hash, matches write_record's seed
    last_n = 0
    verified: list[dict[str, Any]] = []
    for r in records:
        rid = str(r.get("attestation_id") or "")
        m = ATTEST_ID_RE.match(rid)
        if not m:
            errors.append(f"attestation: bad id {rid!r}")
            continue
        n = int(m.group(1))
        if n != last_n + 1:
            errors.append(f"attestation: chain gap or reorder at {rid} (expected ATT-{last_n + 1:06d})")
        last_n = n
        if r.get("prev_hash") != prev_chain:
            errors.append(f"attestation: {rid} prev_hash mismatch (chain broken)")
        if not str(r.get("timestamp") or ""):
            errors.append(f"attestation: {rid} missing timestamp")
        if key is None:
            errors.append(
                f"attestation: {rid} present but BAGEL_ATTEST_KEY not set — "
                "signature cannot be verified; run is UNATTESTED"
            )
        elif not verify_signature(r, key):
            errors.append(f"attestation: {rid} signature invalid — record tampered or forged")
        else:
            verified.append(r)
        prev_chain = _chain_hash([r])
    return errors, verified


def write_record(
    root: Path,
    tool: str,
    tool_input: dict[str, Any],
    tool_output: dict[str, Any],
) -> Path | None:
    """Hook-only writer. Returns the path written, or None if no key configured.

    This is called from hook scripts running in the harness process. It MUST
    NOT be called from agent tooling — the agent has no way to set the key in
    the hook process's env, so even if it invoked this function directly it
    could not produce a valid signature.
    """
    key = get_key()
    if key is None:
        return None
    d = attest_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    records = load_records(root)
    rid = _next_id(records)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record: dict[str, Any] = {
        "attestation_id": rid,
        "timestamp": ts,
        "tool": tool,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "prev_hash": _chain_hash(records),
    }
    record["signature"] = sign_record(record, key)
    path = d / f"{rid}.yaml"
    path.write_text(
        yaml.safe_dump(record, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return path


def index_outputs(verified: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build {command: attestation} for every Bash attestation whose command
    produced a stdout file. Validators use this to bind a claim's extracts_from
    / run_ref to a real attested command output."""
    out: dict[str, dict[str, Any]] = {}
    for r in verified:
        if str(r.get("tool") or "") != "Bash":
            continue
        ti = r.get("tool_input") or {}
        to = r.get("tool_output") or {}
        cwd = str(ti.get("cwd") or ".")
        # The attested artifact = stdout bytes captured by the harness.
        stdout_sha = str(to.get("stdout_sha256") or "")
        if not SHA256_RE.match(stdout_sha):
            continue
        out[str(ti.get("command") or "")] = {
            "command": str(ti.get("command") or ""),
            "cwd": cwd,
            "exit_code": to.get("exit_code"),
            "stdout_sha256": stdout_sha,
            "stdout_bytes": to.get("stdout_bytes"),
            "wall_time_seconds": to.get("wall_time_seconds"),
            "attestation_id": r.get("attestation_id"),
            "timestamp": r.get("timestamp"),
        }
    return out


def index_writes(verified: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Build {file_path: [attestations...]} for every Write/Edit attestation,
    ordered by timestamp ascending. Validators use this to prove a file
    (e.g. experiment-plan.yaml) was written BEFORE a result-producing Bash
    command — closing the HARKing / post-result preregistration surface."""
    out: dict[str, list[dict[str, Any]]] = {}
    for r in verified:
        if str(r.get("tool") or "") != "Write":
            continue
        ti = r.get("tool_input") or {}
        fp = str(ti.get("file_path") or "")
        if not fp:
            continue
        out.setdefault(fp, []).append({
            "file_path": fp,
            "timestamp": r.get("timestamp"),
            "attestation_id": r.get("attestation_id"),
            "content_sha256": (r.get("tool_output") or {}).get("content_sha256"),
        })
    for fp in out:
        out[fp].sort(key=lambda a: str(a.get("timestamp") or ""))
    return out


def index_subagents(verified: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a list of every attested Task/Agent (subagent) dispatch, ordered by
    timestamp ascending. Written ONLY by the Task PostToolUse hook
    (attest_subagent.py) in the harness process — the agent cannot mint a valid
    signed Task attestation, so this is a real-dispatch witness that the
    true_subagents runtime proof can bind to (closing RUN-001 finding 3: a
    hand-written subagent-proof.yaml is shape-valid but has no attested dispatch
    behind it)."""
    out: list[dict[str, Any]] = []
    for r in verified:
        if str(r.get("tool") or "") != "Task":
            continue
        ti = r.get("tool_input") or {}
        to = r.get("tool_output") or {}
        out.append({
            "agent_id": str(to.get("agent_id") or ""),
            "subagent_type": str(ti.get("subagent_type") or ""),
            "description": str(ti.get("description") or ""),
            "isolated_context": to.get("isolated_context"),
            "subagent_tokens": to.get("subagent_tokens"),
            "attestation_id": r.get("attestation_id"),
            "timestamp": r.get("timestamp"),
        })
    out.sort(key=lambda a: str(a.get("timestamp") or ""))
    return out


def first_write_timestamp(index: dict[str, list[dict[str, Any]]], file_path_substring: str) -> str | None:
    """Earliest attested write timestamp for any file whose path contains the
    given substring (e.g. 'experiment-plan.yaml'). None if no attested write."""
    earliest: str | None = None
    for fp, atts in index.items():
        if file_path_substring not in fp.replace("\\", "/"):
            continue
        for a in atts:
            ts = str(a.get("timestamp") or "")
            if ts and (earliest is None or ts < earliest):
                earliest = ts
    return earliest


def first_run_timestamp(bash_index: dict[str, dict[str, Any]]) -> str | None:
    """Earliest attested Bash command timestamp (any real command). None if none."""
    earliest: str | None = None
    for att in bash_index.values():
        ts = str(att.get("timestamp") or "")
        if ts and (earliest is None or ts < earliest):
            earliest = ts
    return earliest
