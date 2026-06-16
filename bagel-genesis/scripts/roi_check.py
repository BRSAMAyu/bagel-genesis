#!/usr/bin/env python3
"""Validate BAGEL V3.1 evidence-backed ROI controller state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


HARD_VALUE_KEYS = {"P0_closed", "P1_closed", "primary_metric_delta", "deliverable_delta_ref", "user_visible_improvement_ref"}
SOFT_VALUE_KEYS = {"knowledge_gained", "option_value_created", "risk_reduced", "reusable_lesson_created"}
VALID_DECISIONS = {"continue", "switch_strategy", "shrink_scope", "escalate_to_breakthrough_search", "stop_at_budget_boundary"}


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


def evidence_exists(root: Path, refs: Any) -> bool:
    return any(isinstance(ref, str) and (root / ref).exists() for ref in as_list(refs))


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
        if worth.get("expert_layer_mode") not in {"off", "lite", "standard", "full"}:
            errors.append("bagel_worth_it_check.expert_layer_mode must be off|lite|standard|full")
        for field in ("task_complexity", "ambiguity", "risk_of_naive_agent_failure", "need_for_expert_strategy"):
            if not worth.get(field):
                errors.append(f"bagel_worth_it_check missing {field}")

    cycles = collect_cycles(root)
    low_roi_streak = 0
    soft_only_streak = 0
    for i, cycle in enumerate(cycles, start=1):
        accounting = as_dict(cycle.get("value_accounting"))
        if not accounting:
            errors.append(f"cycle {i}: missing value_accounting")
            continue
        cost = as_dict(accounting.get("cost"))
        value = as_dict(accounting.get("value"))
        hard = as_dict(value.get("hard_value"))
        soft = as_dict(value.get("soft_value"))
        roi = as_dict(accounting.get("roi_assessment"))
        if not cost.get("estimated_tokens") and not cost.get("wall_time"):
            errors.append(f"cycle {i}: value_accounting.cost needs estimated_tokens or wall_time")
        has_hard = any(hard.get(key) for key in HARD_VALUE_KEYS)
        has_soft = any(soft.get(key) for key in SOFT_VALUE_KEYS)
        if not has_hard and not has_soft:
            errors.append(f"cycle {i}: value_accounting.value has no hard_value or soft_value signal")
        if hard.get("deliverable_delta_ref") and not (root / str(hard.get("deliverable_delta_ref"))).exists():
            errors.append(f"cycle {i}: hard_value.deliverable_delta_ref does not exist")
        for key in SOFT_VALUE_KEYS:
            if soft.get(key) and not evidence_exists(root, soft.get("evidence_refs")):
                errors.append(f"cycle {i}: soft_value.{key} requires evidence_refs")
        marginal = roi.get("marginal_value")
        if marginal not in {"high", "medium", "low", "negative"}:
            errors.append(f"cycle {i}: roi_assessment.marginal_value invalid")
        if not roi.get("reason"):
            errors.append(f"cycle {i}: roi_assessment.reason missing")
        evidenced_option = soft.get("option_value_created") and evidence_exists(root, soft.get("evidence_refs"))
        if marginal in {"high", "medium"} and not has_hard and not evidenced_option:
            errors.append(f"cycle {i}: medium/high ROI requires hard_value or evidenced option_value_created")
        if marginal == "high" and not has_hard and not roi.get("high_roi_without_delta_explanation"):
            errors.append(f"cycle {i}: high ROI without deliverable/metric movement needs explanation")
        if marginal in {"low", "negative"}:
            low_roi_streak += 1
        else:
            low_roi_streak = 0
        if has_soft and not has_hard:
            soft_only_streak += 1
        else:
            soft_only_streak = 0
        if soft_only_streak >= 2 and roi.get("continue_same_strategy") is True:
            errors.append(f"cycle {i}: two soft-value-only cycles require strategy switch or hard-value probe")
        if low_roi_streak >= 3 and roi.get("continue_same_strategy") is True:
            errors.append(f"cycle {i}: three low/negative ROI cycles require strategy switch")

    controller = as_dict(load_yaml(root / ".bagel/expert/roi-controller.yaml", {})) or as_dict(state.get("roi_controller"))
    if run_started and not controller:
        errors.append("roi_controller is required after autonomous Build starts")
    elif controller and controller.get("decision") not in VALID_DECISIONS:
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
