#!/usr/bin/env python3
"""Validate BAGEL V2 telemetry, context pressure, and governance budget."""

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


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def warn(warnings: list[str], message: str) -> None:
    warnings.append(message)


def collect_cycles(root: Path) -> list[dict[str, Any]]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    cycles: list[dict[str, Any]] = []
    for item in as_list(as_dict(state.get("telemetry")).get("cycles")):
        cycles.append(as_dict(item))
    for path in (root / ".bagel/telemetry").glob("cycles*.yaml") if (root / ".bagel/telemetry").exists() else []:
        data = load_yaml(path, [])
        if isinstance(data, dict):
            cycles.extend(as_dict(item) for item in as_list(data.get("cycles") or data.get("cycle_telemetry")))
        else:
            cycles.extend(as_dict(item) for item in as_list(data))
    return [cycle for cycle in cycles if cycle]


def configured_budget(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    defaults = {
        "max_control_plane_share_per_cycle": 0.30,
        "first_deliverable_delta_required_by_cycle": 2,
        "max_cycles_without_deliverable_delta": 2,
    }
    budget = {**defaults, **as_dict(state.get("governance_budget"))}
    file_budget = as_dict(load_yaml(root / ".bagel/telemetry/governance-budget.yaml", {}))
    return {**budget, **file_budget}


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    if not bagel.exists():
        return [], []
    state = as_dict(load_yaml(bagel / "state.yaml", {}))
    errors: list[str] = []
    warnings: list[str] = []
    cycles = collect_cycles(root)
    if not cycles:
        if state.get("phase") in {"Build", "Iterate", "Polish"} or state.get("task_queue"):
            fail(errors, "Build/Iterate work has started but no V2 cycle telemetry exists")
        return errors, warnings

    budget = configured_budget(root, state)
    max_share = float(budget.get("max_control_plane_share_per_cycle", 0.30))
    max_no_delta = int(budget.get("max_cycles_without_deliverable_delta", 2))
    first_delta_by = int(budget.get("first_deliverable_delta_required_by_cycle", 2))

    no_deliverable_streak = 0
    high_governance_streak = 0
    first_deliverable_seen_at: int | None = None

    for idx, cycle in enumerate(cycles, start=1):
        outputs = as_dict(cycle.get("outputs"))
        budget_block = as_dict(cycle.get("budget"))
        pressure = as_dict(cycle.get("context_pressure"))
        deliverable_delta = outputs.get("deliverable_delta")
        control_delta = outputs.get("control_plane_delta")
        share = budget_block.get("governance_token_share")

        if deliverable_delta is True and first_deliverable_seen_at is None:
            first_deliverable_seen_at = idx
        if deliverable_delta is False and control_delta is True:
            no_deliverable_streak += 1
        elif deliverable_delta is True:
            no_deliverable_streak = 0
        if no_deliverable_streak > max_no_delta:
            fail(errors, f"cycle {idx}: exceeded max_cycles_without_deliverable_delta={max_no_delta}")

        if isinstance(share, (int, float)) and share > max_share:
            high_governance_streak += 1
        else:
            high_governance_streak = 0
        if high_governance_streak >= 2:
            warn(warnings, f"cycle {idx}: governance_token_share exceeded {max_share:.2f} for 2 consecutive cycles")

        threshold = pressure.get("replacement_threshold_percent")
        orch = pressure.get("orchestrator_estimated_tokens")
        max_tokens = pressure.get("orchestrator_context_window_tokens")
        replacement_due = pressure.get("replacement_due")
        handoff_ref = pressure.get("handoff_ref") or cycle.get("handoff_ref")
        if isinstance(orch, int) and isinstance(max_tokens, int) and isinstance(threshold, int):
            percent = (orch / max_tokens) * 100 if max_tokens else 0
            if percent >= threshold and replacement_due is not True:
                fail(errors, f"cycle {idx}: Orchestrator context crossed threshold but replacement_due is not true")
            if percent >= threshold and not handoff_ref:
                fail(errors, f"cycle {idx}: Orchestrator context crossed threshold without handoff_ref")

        supervisor_tokens = pressure.get("supervisor_estimated_tokens")
        supervisor_soft = pressure.get("supervisor_soft_max_tokens") or 200000
        if isinstance(supervisor_tokens, int) and isinstance(supervisor_soft, int):
            if supervisor_tokens > supervisor_soft:
                fail(errors, f"cycle {idx}: Supervisor exceeded soft max {supervisor_soft} tokens")
            elif supervisor_tokens > supervisor_soft * 0.75 and not pressure.get("supervisor_continuity_capsule_ref"):
                warn(warnings, f"cycle {idx}: Supervisor above 75% soft max without continuity capsule ref")

    if first_deliverable_seen_at is None and len(cycles) >= first_delta_by:
        fail(errors, f"no deliverable_delta by cycle {first_delta_by}")
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
    print("BAGEL telemetry check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
