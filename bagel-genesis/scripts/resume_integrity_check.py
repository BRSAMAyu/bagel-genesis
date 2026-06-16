#!/usr/bin/env python3
"""Validate V2 handoff capsules and idempotent bounded actions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_HANDOFF = {"current_state", "open_risks", "next_action", "last_git_ref"}
REQUIRED_ACTION = {"action_id", "idempotency_key", "status", "owner_agent_id", "git_ref_start", "side_effects"}


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
        if key:
            if key in seen_keys:
                prev = seen_keys[key]
                policy = as_dict(action.get("replay_or_resume_policy"))
                if policy.get("safe_to_retry") is not True:
                    errors.append(f"{path}: duplicate idempotency_key also seen in {prev} without safe_to_retry=true")
            seen_keys[key] = path

    if state.get("supervisor", {}).get("mode") == "nested_supervisor" and not handoff_records:
        warnings.append("nested supervisor has no handoff records yet; replacement safety cannot be audited")
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
