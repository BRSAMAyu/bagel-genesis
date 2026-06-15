#!/usr/bin/env python3
"""Validate BAGEL flywheel state for positive autonomous iteration.

This is intentionally a lightweight project-run validator, not a full schema
engine. It checks the gates that are most likely to turn long autonomy into
churn, hallucination, regression, or collapse.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


SEVERITY_ORDER = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4}
BAR_RAISE_CLASSES = {
    "tighten_target",
    "new_dimension",
    "adversarial_lens",
    "astonishing_completeness",
    "stronger_research_evidence",
    "defect_prevention",
    "adversarial",
    "growth_dimension",
    "churn",
}


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def warn(warnings: list[str], msg: str) -> None:
    warnings.append(msg)


def numeric(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip().rstrip("%"))
        except ValueError:
            return None
    return None


def get_excellence_state(state: dict[str, Any]) -> dict[str, Any]:
    return as_dict(state.get("excellence"))


def validate_progress_deltas(root: Path, state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    deltas = load_yaml(root / ".bagel/evidence/progress-deltas.yaml", [])
    if not isinstance(deltas, list) or not deltas:
        fail(errors, "progress-deltas.yaml is missing or empty; flywheel progress cannot be audited")
        return

    consecutive_lateral = 0
    for i, delta in enumerate(deltas, start=1):
        d = as_dict(delta)
        assessment = d.get("net_assessment")
        if assessment not in {"forward", "lateral", "backward"}:
            fail(errors, f"cycle {i}: net_assessment must be forward|lateral|backward")
        evidence = as_list(d.get("evidence"))
        if not evidence:
            fail(errors, f"cycle {i}: missing evidence list")
        if evidence:
            has_artifact_evidence = False
            for item in evidence:
                if isinstance(item, dict):
                    candidate = item.get("path") or item.get("artifact")
                else:
                    candidate = str(item)
                if "/" in candidate or candidate.startswith(".bagel/"):
                    has_artifact_evidence = True
                    break
            if not has_artifact_evidence:
                fail(errors, f"cycle {i}: evidence must include at least one saved artifact/output path, not only command names")
        reviewer = as_dict(d.get("independent_assessment"))
        if not reviewer:
            fail(errors, f"cycle {i}: missing independent_assessment; implementer self-report is not enough")
        if reviewer and reviewer.get("review_level") not in SEVERITY_ORDER:
            fail(errors, f"cycle {i}: independent_assessment.review_level must be R0-R4")
        if assessment == "lateral":
            consecutive_lateral += 1
        else:
            consecutive_lateral = 0
        if consecutive_lateral >= 3 and d.get("next_strategy") in {None, "continue current lane"}:
            fail(errors, f"cycle {i}: three lateral cycles require a real strategy switch")
        if assessment == "backward" and d.get("next_strategy") not in {
            "rollback",
            "isolate lane",
            "repair verifier",
            "switch hypothesis",
            "advance independent task",
        }:
            fail(errors, f"cycle {i}: backward delta must trigger rollback/isolation/repair/strategy switch")

    excel = get_excellence_state(state)
    recorded = excel.get("consecutive_lateral_cycles")
    if isinstance(recorded, int) and recorded != consecutive_lateral:
        fail(errors, f"state.excellence.consecutive_lateral_cycles={recorded} does not match progress deltas tail={consecutive_lateral}")
    if not isinstance(recorded, int):
        warn(warnings, "state.excellence.consecutive_lateral_cycles missing; context compaction may lose stop/switch counters")


def validate_review_registry(root: Path, state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    registry = as_dict(state.get("review_registry"))
    registry_path = root / ".bagel/agents/registry.yaml"
    if registry_path.exists():
        registry = {**registry, **as_dict(load_yaml(registry_path, {}))}
    if not registry:
        warn(warnings, "review registry missing; R-level claims cannot be mechanically derived")
        return

    reviews = as_list(registry.get("reviews") or registry.get("agents") or registry.get("review_events"))
    for i, review in enumerate(reviews, start=1):
        r = as_dict(review)
        claimed = r.get("claimed_level") or r.get("review_level")
        derived = r.get("derived_level")
        reviewer_id = r.get("reviewer_id") or r.get("agent_id")
        worker_id = r.get("worker_id") or r.get("implements_agent_id")
        session_id = r.get("session_id")
        worker_session_id = r.get("worker_session_id")

        if claimed in SEVERITY_ORDER and not derived:
            fail(errors, f"review {i}: claimed {claimed} without derived_level from registry")
        if derived in {"R3", "R4"}:
            if reviewer_id and worker_id and reviewer_id == worker_id:
                fail(errors, f"review {i}: derived {derived} cannot use same reviewer and worker id")
            if session_id and worker_session_id and session_id == worker_session_id:
                fail(errors, f"review {i}: derived {derived} cannot share worker session context")
        if claimed in SEVERITY_ORDER and derived in SEVERITY_ORDER:
            if SEVERITY_ORDER[claimed] > SEVERITY_ORDER[derived]:
                fail(errors, f"review {i}: claimed {claimed} exceeds registry-derived {derived}")


def validate_green_floors(state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    excel = get_excellence_state(state)
    floors = as_dict(excel.get("green_floors"))
    current_metrics = as_list(excel.get("metrics"))
    if not floors:
        warn(warnings, "green_floors missing; regression protection starts only after first completed iteration")
        return
    current_by_name = {m.get("metric"): m for m in current_metrics if isinstance(m, dict) and m.get("metric")}
    for iteration, metrics in floors.items():
        for metric_name, floor_value in as_dict(metrics).items():
            metric = current_by_name.get(metric_name)
            if not metric:
                continue
            current = numeric(metric.get("current_value"))
            floor = numeric(floor_value)
            direction = metric.get("direction", "higher_is_better")
            if current is None or floor is None:
                continue
            if direction == "lower_is_better" and current > floor:
                fail(errors, f"metric {metric_name} regressed above green floor from iteration {iteration}: {current} > {floor}")
            if direction != "lower_is_better" and current < floor:
                fail(errors, f"metric {metric_name} regressed below green floor from iteration {iteration}: {current} < {floor}")


def validate_iteration_budget(state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    excel = get_excellence_state(state)
    cap = excel.get("iteration_cycle_cap")
    used = excel.get("cycles_in_current_iteration", 0)
    if not isinstance(cap, int) or cap <= 0:
        fail(errors, "state.excellence.iteration_cycle_cap must be a positive integer")
        return
    if isinstance(used, int) and used > cap:
        fail(errors, f"cycles_in_current_iteration={used} exceeds iteration_cycle_cap={cap}")
    remaining = as_dict(state.get("budget")).get("remaining_budget_share") or excel.get("remaining_budget_share")
    if isinstance(remaining, dict):
        p0_open = excel.get("open_P0", 0)
        p1_open = excel.get("open_P1", 0)
        polish = numeric(remaining.get("excellence_polish", 0)) or 0
        core = (numeric(remaining.get("P0_unfinished", 0)) or 0) + (numeric(remaining.get("P1_unfinished", 0)) or 0)
        if (p0_open or p1_open) and polish > core:
            fail(errors, "budget allocation gives polish more share than unfinished P0/P1 scope")
    else:
        warn(warnings, "remaining budget allocation missing; low-value polish may crowd out core work")


def validate_bar_raises(root: Path, errors: list[str], warnings: list[str]) -> None:
    raises = load_yaml(root / ".bagel/evidence/bar-raises.yaml", [])
    if not raises:
        warn(warnings, "bar-raises.yaml missing; flywheel may not prove standards were raised")
        return
    for i, item in enumerate(as_list(raises), start=1):
        row = as_dict(item)
        why = row.get("why_class")
        if why not in BAR_RAISE_CLASSES:
            fail(errors, f"bar raise {i}: missing valid why_class")
        if why == "churn":
            review_level = row.get("review_level")
            accepted = row.get("accepted")
            if review_level not in {"R3", "R4"} or accepted is not True:
                fail(errors, f"bar raise {i}: churn requires R3/R4 acceptance")
        if not row.get("evidence"):
            fail(errors, f"bar raise {i}: missing evidence")


def validate_flat_climbing(state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    excel = get_excellence_state(state)
    slope = as_dict(excel.get("trajectory_slope"))
    if not slope:
        warn(warnings, "trajectory_slope missing; low-yield forward movement cannot be detected")
        return
    if slope.get("flat_climbing") is True:
        status = state.get("status") or state.get("run_status")
        if status not in {"flat_climbing", "complete", "waiting_for_capacity"}:
            fail(errors, "flat_climbing=true must be surfaced in run status or final/waiting state")
        if not slope.get("action"):
            fail(errors, "flat_climbing=true requires an action: redirect, reduce iterations, or one-confirmation iteration")


def validate(root: Path) -> tuple[list[str], list[str]]:
    state = load_yaml(root / ".bagel/state.yaml", {})
    if not isinstance(state, dict):
        return ["state.yaml is missing or malformed"], []
    errors: list[str] = []
    warnings: list[str] = []
    validate_progress_deltas(root, state, errors, warnings)
    validate_review_registry(root, state, errors, warnings)
    validate_green_floors(state, errors, warnings)
    validate_iteration_budget(state, errors, warnings)
    validate_bar_raises(root, errors, warnings)
    validate_flat_climbing(state, errors, warnings)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Project root containing .bagel/")
    parser.add_argument("--strict-warnings", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors, warnings = validate(root)
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL flywheel check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
