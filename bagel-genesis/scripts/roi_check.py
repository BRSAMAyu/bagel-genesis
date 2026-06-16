#!/usr/bin/env python3
"""Validate BAGEL V3 value accounting and ROI controller state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


VALUE_KEYS = {"P0_closed", "P1_closed", "primary_metric_delta", "user_visible_improvement", "risk_reduced", "knowledge_gained", "reusable_lesson_created", "option_value_created"}


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


def collect_cycles(root: Path) -> list[dict[str, Any]]:
    cycles: list[dict[str, Any]] = []
    for path in (root / ".bagel/telemetry").glob("cycles*.yaml") if (root / ".bagel/telemetry").exists() else []:
        data = load_yaml(path, {})
        rows = data.get("cycles") if isinstance(data, dict) else data
        cycles.extend(as_dict(item) for item in as_list(rows))
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    cycles.extend(as_dict(item) for item in as_list(as_dict(state.get("telemetry")).get("cycles")))
    return [cycle for cycle in cycles if cycle]


def validate(root: Path) -> tuple[list[str], list[str]]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    run_started = state.get("phase") in {"Build", "Iterate", "Polish"} or state.get("task_queue")
    errors: list[str] = []
    warnings: list[str] = []

    worth = as_dict(load_yaml(root / ".bagel/expert/bagel-worth-it.yaml", {})) or as_dict(state.get("bagel_worth_it_check"))
    if not worth and run_started:
        errors.append("bagel_worth_it_check is required before autonomous Build")
    elif worth:
        if worth.get("recommended_mode") not in {"no_bagel", "quick_autonomy", "measured_run", "full_expert_run"}:
            errors.append("bagel_worth_it_check.recommended_mode is invalid")
        for field in ("task_complexity", "ambiguity", "risk_of_naive_agent_failure", "need_for_expert_strategy"):
            if not worth.get(field):
                errors.append(f"bagel_worth_it_check missing {field}")

    cycles = collect_cycles(root)
    low_roi_streak = 0
    for i, cycle in enumerate(cycles, start=1):
        accounting = as_dict(cycle.get("value_accounting"))
        if not accounting:
            errors.append(f"cycle {i}: missing value_accounting")
            continue
        cost = as_dict(accounting.get("cost"))
        value = as_dict(accounting.get("value"))
        roi = as_dict(accounting.get("roi_assessment"))
        if not cost.get("estimated_tokens") and not cost.get("wall_time"):
            errors.append(f"cycle {i}: value_accounting.cost needs estimated_tokens or wall_time")
        if not any(value.get(key) for key in VALUE_KEYS):
            errors.append(f"cycle {i}: value_accounting.value has no user-relevant value signal")
        if roi.get("marginal_value") not in {"high", "medium", "low", "negative"}:
            errors.append(f"cycle {i}: roi_assessment.marginal_value invalid")
        if not roi.get("reason"):
            errors.append(f"cycle {i}: roi_assessment.reason missing")
        if roi.get("marginal_value") in {"low", "negative"}:
            low_roi_streak += 1
        else:
            low_roi_streak = 0
        if low_roi_streak >= 3 and roi.get("continue_same_strategy") is True:
            errors.append(f"cycle {i}: three low/negative ROI cycles require strategy switch")

    controller = as_dict(load_yaml(root / ".bagel/expert/roi-controller.yaml", {})) or as_dict(state.get("roi_controller"))
    if run_started and not controller:
        errors.append("roi_controller is required after autonomous Build starts")
    elif controller and controller.get("decision") not in {"continue", "switch_strategy", "shrink_scope", "escalate_to_breakthrough_search", "stop_at_budget_boundary"}:
        errors.append("roi_controller.decision is invalid")
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
    print("BAGEL ROI check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
