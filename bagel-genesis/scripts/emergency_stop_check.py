#!/usr/bin/env python3
"""Validate BAGEL emergency stop state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    state = as_dict(load_yaml(bagel / "state.yaml", {}))
    stop_requested = (bagel / "STOP_REQUESTED").exists() or state.get("run_status") == "emergency_stopped"
    if not stop_requested:
        return [], []
    errors: list[str] = []
    stop = as_dict(state.get("emergency_stop"))
    if state.get("run_status") != "emergency_stopped":
        errors.append("STOP_REQUESTED exists but state.run_status is not emergency_stopped")
    for field in ("requested_at", "reason", "git_status_ref", "recovery_instructions_ref"):
        if not stop.get(field):
            errors.append(f"emergency_stop missing {field}")
    if stop.get("destructive_reset_performed") is True:
        errors.append("emergency stop must not perform destructive reset automatically")
    for ref in ("git_status_ref", "recovery_instructions_ref"):
        value = stop.get(ref)
        if value and not (root / str(value)).exists():
            errors.append(f"emergency_stop.{ref} does not exist: {value}")
    return errors, []


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
    print("BAGEL emergency stop check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
