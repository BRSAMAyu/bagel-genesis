#!/usr/bin/env python3
"""Validate V2 handoff capsules and idempotent bounded actions."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_HANDOFF = {"current_state", "open_risks", "next_action", "last_git_ref", "handoff_validation_report"}
REQUIRED_VALIDATION = {"validator_agent_id", "validator_session_id", "validated_at", "parent_or_child", "valid", "missing_fields", "state_hash_matches", "next_action_safe_to_start"}
REQUIRED_ACTION = {"action_id", "idempotency_key", "status", "owner_agent_id", "git_ref_start", "side_effects", "task_id", "allowed_paths", "intent"}


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


def collect_yaml(root: Path, dirs: list[str]) -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    for rel in dirs:
        base = root / rel
        if base.is_file():
            out.append((base, as_dict(load_yaml(base, {}))))
        elif base.exists():
            for path in sorted(base.rglob("*.yaml")):
                out.append((path, as_dict(load_yaml(path, {}))))
    return out


def canonical_hash(value: Any) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def idempotency_key(action: dict[str, Any]) -> str:
    parts = [
        str(action.get("task_id") or ""),
        str(action.get("git_ref_start") or ""),
        ",".join(sorted(str(item) for item in as_list(action.get("allowed_paths")))),
        " ".join(str(action.get("intent") or "").split()),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    if not bagel.exists():
        return [], []
    errors: list[str] = []
    warnings: list[str] = []
    state = as_dict(load_yaml(bagel / "state.yaml", {}))

    handoff_records = collect_yaml(root, [".bagel/handoffs", ".bagel/supervisor/handoffs"])
    if as_dict(state.get("handoff")):
        handoff_records.append((bagel / "state.yaml#handoff", as_dict(state.get("handoff"))))

    for path, record in handoff_records:
        missing = sorted(field for field in REQUIRED_HANDOFF if field not in record)
        if missing:
            errors.append(f"{path}: handoff missing required fields: {', '.join(missing)}")
        report = as_dict(record.get("handoff_validation_report"))
        if not report:
            errors.append(f"{path}: handoff_validation_report is required")
        else:
            missing_report = sorted(field for field in REQUIRED_VALIDATION if field not in report)
            if missing_report:
                errors.append(f"{path}: handoff_validation_report missing required fields: {', '.join(missing_report)}")
            if report.get("handoff_ref") and str(report.get("handoff_ref")) not in {str(path), str(path.relative_to(root)) if path.is_absolute() and root in path.parents else str(path)}:
                errors.append(f"{path}: handoff_validation_report.handoff_ref must match actual handoff path")
        old_agent = record.get("old_agent_id") or record.get("owner_agent_id")
        if old_agent and report.get("validator_agent_id") == old_agent:
            errors.append(f"{path}: handoff validator_agent_id must differ from old/owner agent")
        if report and report.get("parent_or_child") not in {"parent", "fresh_child"}:
            errors.append(f"{path}: handoff_validation_report.parent_or_child must be parent|fresh_child")
        if report and report.get("state_hash_matches") is not True:
            errors.append(f"{path}: handoff_validation_report.state_hash_matches must be true")
        if report:
            state_ref = report.get("state_ref")
            state_hash = report.get("state_hash")
            algorithm = report.get("state_hash_algorithm")
            if algorithm != "sha256":
                errors.append(f"{path}: handoff_validation_report.state_hash_algorithm must be sha256")
            if state_ref and state_hash:
                actual = file_hash(root / str(state_ref))
                if actual != state_hash:
                    errors.append(f"{path}: handoff_validation_report.state_hash does not match {state_ref}")
            elif state_hash:
                if canonical_hash(record.get("current_state")) != state_hash:
                    errors.append(f"{path}: handoff_validation_report.state_hash does not match current_state")
            else:
                errors.append(f"{path}: handoff_validation_report requires state_hash")
        if report and report.get("valid") is not True:
            errors.append(f"{path}: handoff_validation_report.valid is not true")
        if report and report.get("next_action_safe_to_start") is not True:
            errors.append(f"{path}: next_action_safe_to_start is not true")

    actions: list[tuple[Path, dict[str, Any]]] = []
    actions.extend(collect_yaml(root, [".bagel/actions", ".bagel/ledger/actions.yaml"]))
    for item in as_list(state.get("actions")):
        actions.append((bagel / "state.yaml#actions", as_dict(item)))

    seen_keys: dict[str, Path] = {}
    for path, action in actions:
        missing = sorted(field for field in REQUIRED_ACTION if field not in action)
        if missing:
            errors.append(f"{path}: action missing required fields: {', '.join(missing)}")
        status = action.get("status")
        if status not in {"planned", "running", "committed", "verified", "abandoned"}:
            errors.append(f"{path}: invalid action.status {status!r}")
        if status == "running":
            policy = as_dict(action.get("replay_or_resume_policy"))
            if "safe_to_retry" not in policy:
                errors.append(f"{path}: running action requires replay_or_resume_policy.safe_to_retry")
        key = str(action.get("idempotency_key") or "")
        expected_key = idempotency_key(action)
        if key and key != expected_key:
            errors.append(f"{path}: idempotency_key does not match task_id/git_ref_start/allowed_paths/intent")
        if key:
            if key in seen_keys:
                prev = seen_keys[key]
                policy = as_dict(action.get("replay_or_resume_policy"))
                if policy.get("safe_to_retry") is not True:
                    errors.append(f"{path}: duplicate idempotency_key also seen in {prev} without safe_to_retry=true")
            seen_keys[key] = path

    if state.get("supervisor", {}).get("mode") == "nested_supervisor" and not handoff_records:
        warnings.append("nested supervisor has no handoff records yet; replacement safety cannot be audited")

    # S6: stale-state / "current-skill-outranks-stale" check.
    # When a run records the SKILL.md content hash at spawn time (skill_content_hash),
    # a resume that finds a DIFFERENT hash means the loaded skill instructions have
    # changed since spawn — the run may obey stale .bagel topology that the current
    # skill no longer declares. The agent must re-anchor, not blindly obey old state.
    # This is the mechanical backstop for SKILL.md L78 "current skill instructions
    # outrank stale .bagel/ artifacts".
    spawn_hash = str((as_dict(state.get("supervisor"))).get("skill_content_hash") or state.get("skill_content_hash") or "")
    if spawn_hash:
        # Find the SKILL.md relative to the run root (control plane is sibling to skill)
        skill_candidates = [
            root / "SKILL.md",
            root.parent / "SKILL.md",
            root / ".bagel" / "skill_snapshot.md",
        ]
        current_hash = None
        for cand in skill_candidates:
            if cand.exists():
                current_hash = hashlib.sha256(cand.read_bytes()).hexdigest()
                break
        if current_hash and current_hash != spawn_hash and not state.get("skill_reanchored"):
            errors.append(
                "stale_skill_state: skill_content_hash at spawn does not match current SKILL.md. "
                "The loaded skill instructions have changed; the run must re-anchor (set state.skill_reanchored "
                "after migrating to current instructions) rather than obey stale .bagel topology. "
                "(SKILL.md: current skill instructions outrank stale .bagel/ artifacts)"
            )
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    errors, warnings = validate(Path(args.root).resolve())
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL resume integrity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
