#!/usr/bin/env python3
"""Validate replayable BAGEL evidence records and file hashes."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_RUNNABLE = {"evidence_id", "command", "cwd", "git_ref", "started_at", "finished_at", "exit_code", "stdout_path", "stderr_path", "stdout_sha256", "stderr_sha256", "env_digest", "replay_policy"}


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


def validate(root: Path, replay: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    records = collect_records(root)
    if not records:
        return errors, warnings
    current_head = git_head(root)
    hash_history: dict[tuple[str, str], int] = {}

    for path, record in records:
        policy = as_dict(record.get("replay_policy"))
        mode = policy.get("mode")
        if mode not in {"exact", "sampled", "not_replayable"}:
            errors.append(f"{path}: evidence {record.get('evidence_id', '<unknown>')} replay_policy.mode must be exact|sampled|not_replayable")
            continue
        if mode == "not_replayable":
            if not policy.get("reason_if_not_replayable"):
                errors.append(f"{path}: not_replayable evidence requires reason_if_not_replayable")
            if not record.get("manual_evidence_reviewer"):
                errors.append(f"{path}: not_replayable evidence requires manual_evidence_reviewer")
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
            actual = sha256(p)
            if expected and actual != expected:
                errors.append(f"{path}: {key} hash mismatch for {record.get(key)}")
        if current_head and record.get("git_ref") and str(record.get("git_ref")) != current_head:
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
