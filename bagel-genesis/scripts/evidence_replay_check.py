#!/usr/bin/env python3
"""Validate replayable BAGEL evidence records and file hashes."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_RUNNABLE = {"evidence_id", "command", "cwd", "git_ref", "started_at", "finished_at", "exit_code", "stdout_path", "stderr_path", "stdout_sha256", "stderr_sha256", "env_digest", "replay_policy"}
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_bytes(value: bytes) -> bytes:
    return b"\n".join(line.rstrip() for line in value.replace(b"\r\n", b"\n").split(b"\n")).strip()


def collect_records(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    base = root / ".bagel/evidence"
    if not base.exists():
        return out
    for path in sorted(base.rglob("*.yaml")):
        data = load_yaml(path, {})
        if isinstance(data, dict) and ("evidence" in data or "evidence_id" in data):
            rows = as_list(data.get("evidence")) if "evidence" in data else [data]
        elif isinstance(data, list):
            rows = data
        else:
            continue
        for row in rows:
            rec = as_dict(row)
            if rec.get("evidence_id") or rec.get("command"):
                out.append((path, rec))
    return out


def git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def referenced_evidence(root: Path) -> list[str]:
    refs: list[str] = []
    progress = load_yaml(root / ".bagel/evidence/progress-deltas.yaml", [])
    for row in as_list(progress):
        refs.extend(str(item) for item in as_list(as_dict(row).get("evidence")))
    for path in (root / ".bagel/telemetry").glob("cycles*.yaml") if (root / ".bagel/telemetry").exists() else []:
        data = load_yaml(path, {})
        rows = data.get("cycles") if isinstance(data, dict) else data
        for row in as_list(rows):
            refs.extend(str(item) for item in as_list(as_dict(as_dict(row).get("outputs")).get("evidence_refs")))
    return [ref for ref in refs if ref and ref != "None"]


def validate(root: Path, replay: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    records = collect_records(root)
    refs = referenced_evidence(root)
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    build_started = state.get("phase") in {"Build", "Iterate", "Polish"} or bool(state.get("task_queue"))
    if not records:
        if refs or build_started:
            errors.append("evidence references or Build state exist but no indexed evidence records were found")
        return errors, warnings
    record_ids = {str(as_dict(record).get("evidence_id")) for _, record in records if as_dict(record).get("evidence_id")}
    record_paths = {str(path.relative_to(root)) for path, _ in records}
    for ref in refs:
        if ref.startswith("EV-") and ref not in record_ids:
            errors.append(f"referenced evidence_id has no validated evidence record: {ref}")
        elif ref.startswith(".bagel/evidence/") and ref not in record_paths and not (root / ref).exists():
            errors.append(f"referenced evidence path does not exist: {ref}")
    current_head = git_head(root)
    hash_history: dict[tuple[str, str], int] = {}

    for path, record in records:
        policy = as_dict(record.get("replay_policy"))
        mode = policy.get("mode")
        if mode not in {"exact", "sampled", "not_replayable"}:
            errors.append(f"{path}: evidence {record.get('evidence_id', '<unknown>')} replay_policy.mode must be exact|sampled|not_replayable")
            continue
        if mode == "not_replayable":
            if not record.get("evidence_id"):
                errors.append(f"{path}: not_replayable evidence requires evidence_id")
            if not policy.get("reason_if_not_replayable"):
                errors.append(f"{path}: not_replayable evidence requires reason_if_not_replayable")
            if not record.get("manual_evidence_reviewer"):
                errors.append(f"{path}: not_replayable evidence requires manual_evidence_reviewer")
            if record.get("command") and policy.get("reason_if_not_replayable") not in {"external_resource", "privacy_sensitive", "paid_or_rate_limited", "manual_visual_judgment", "time_dependent"}:
                errors.append(f"{path}: command-like not_replayable evidence requires an allowed reason enum")
            continue

        missing = sorted(field for field in REQUIRED_RUNNABLE if field not in record)
        if missing:
            errors.append(f"{path}: runnable evidence missing fields: {', '.join(missing)}")
            continue
        for key in ("stdout_path", "stderr_path"):
            p = root / str(record.get(key))
            if not p.exists():
                errors.append(f"{path}: {key} missing file {record.get(key)}")
                continue
            expected = record.get(key.replace("_path", "_sha256"))
            if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
                errors.append(f"{path}: {key.replace('_path', '_sha256')} must be a non-empty lowercase 64-char sha256")
                continue
            actual = sha256(p)
            if actual != expected:
                errors.append(f"{path}: {key} hash mismatch for {record.get(key)}")
        if current_head and record.get("git_ref") and str(record.get("git_ref")) != current_head:
            if mode == "exact" or state.get("run_status") == "complete" or state.get("status") == "complete":
                errors.append(f"{path}: exact/final evidence git_ref differs from current HEAD")
            else:
                warnings.append(f"{path}: evidence git_ref differs from current HEAD; replay may require checkout")
        key = (str(record.get("command")), str(record.get("stdout_sha256")))
        hash_history[key] = hash_history.get(key, 0) + 1
        if hash_history[key] >= 3:
            warnings.append(f"{path}: same command/stdout hash reused {hash_history[key]} times; confirm evidence is not stale")
        if replay and mode == "exact" and str(record.get("git_ref")) == current_head:
            cwd = root / str(record.get("cwd") or ".")
            result = subprocess.run(str(record["command"]), shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False, timeout=120)
            if result.returncode != record.get("exit_code") and not policy.get("nondeterminism_note"):
                errors.append(f"{path}: replay exit code {result.returncode} != recorded {record.get('exit_code')}")
            for stream, actual_bytes in (("stdout", result.stdout), ("stderr", result.stderr)):
                compare = policy.get(f"compare_{stream}", "normalized" if mode == "exact" else "ignore")
                recorded_path = root / str(record.get(f"{stream}_path"))
                if compare == "ignore":
                    continue
                if not recorded_path.exists():
                    errors.append(f"{path}: replay compare_{stream} requested but recorded file missing")
                    continue
                recorded = recorded_path.read_bytes()
                if compare == "exact" and actual_bytes != recorded and not policy.get("nondeterminism_note"):
                    errors.append(f"{path}: replay {stream} differs from recorded {stream}")
                elif compare == "normalized" and normalize_bytes(actual_bytes) != normalize_bytes(recorded) and not policy.get("nondeterminism_note"):
                    errors.append(f"{path}: replay normalized {stream} differs from recorded {stream}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--replay", action="store_true", help="Rerun exact commands when git_ref matches current HEAD")
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    errors, warnings = validate(Path(args.root).resolve(), replay=args.replay)
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL evidence replay check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
