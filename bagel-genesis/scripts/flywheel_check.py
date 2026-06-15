#!/usr/bin/env python3
"""Validate BAGEL flywheel state for positive autonomous iteration.

Every check here exists because a prior audit found the corresponding
guarantee was prose-only or self-reported. This script is the mechanical
floor beneath those guarantees.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


SEVERITY_ORDER = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4}

BAR_RAISE_VALUE_CLASSES = {
    "defect_prevention",
    "adversarial",
    "growth_dimension",
    "astonishing_completeness",
    "stronger_evidence",
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


def validate_progress_deltas(root, state, errors, warnings):
    deltas = load_yaml(root / ".bagel/evidence/progress-deltas.yaml", [])
    if not isinstance(deltas, list) or not deltas:
        fail(errors, "progress-deltas.yaml is missing or empty; flywheel progress cannot be audited")
        return
    consecutive_lateral = 0
    for i, delta in enumerate(deltas, start=1):
        d = as_dict(delta)
        assessment = d.get("net_assessment")
        if assessment not in {"forward", "lateral", "backward", "low_confidence"}:
            fail(errors, f"cycle {i}: net_assessment must be forward|lateral|backward|low_confidence")
        evidence = as_list(d.get("evidence"))
        if not evidence:
            fail(errors, f"cycle {i}: missing evidence list")
        else:
            for ev in evidence:
                if not isinstance(ev, str):
                    continue
                ev_path = root / ev
                if not ev_path.exists():
                    fail(errors, f"cycle {i}: cited evidence path does not exist: {ev}")
                elif ev_path.is_file() and ev_path.stat().st_size == 0:
                    fail(errors, f"cycle {i}: cited evidence file is empty: {ev}")
        reviewer = as_dict(d.get("independent_assessment"))
        if not reviewer:
            fail(errors, f"cycle {i}: missing independent_assessment; implementer self-report is not enough")
        if reviewer and reviewer.get("review_level") not in SEVERITY_ORDER:
            fail(errors, f"cycle {i}: independent_assessment.review_level must be R0-R4")
        if assessment in {"lateral", "low_confidence"}:
            consecutive_lateral += 1
        else:
            consecutive_lateral = 0
        if consecutive_lateral >= 3 and d.get("next_strategy") in {None, "continue current lane"}:
            fail(errors, f"cycle {i}: three lateral/low_confidence cycles require a real strategy switch")
        if assessment == "backward" and d.get("next_strategy") not in {
            "rollback", "isolate lane", "repair verifier", "switch hypothesis", "advance independent task",
        }:
            fail(errors, f"cycle {i}: backward delta must trigger rollback/isolation/repair/strategy switch")
    excel = get_excellence_state(state)
    recorded = excel.get("consecutive_lateral_cycles")
    if isinstance(recorded, int) and recorded != consecutive_lateral:
        fail(errors, f"state.excellence.consecutive_lateral_cycles={recorded} does not match deltas tail={consecutive_lateral}")
    if not isinstance(recorded, int):
        warn(warnings, "state.excellence.consecutive_lateral_cycles missing")


def validate_review_registry(root, state, errors, warnings):
    registry = as_dict(state.get("review_registry"))
    registry_path = root / ".bagel/agents/registry.yaml"
    if registry_path.exists():
        registry = {**registry, **as_dict(load_yaml(registry_path, {}))}
    if not registry:
        warn(warnings, "review registry missing; R-level claims cannot be mechanically derived")
        return
    reviews = as_list(registry.get("reviews") or registry.get("agents") or registry.get("review_events"))
    reviewer_history = []
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
            if not reviewer_id or not worker_id:
                fail(errors, f"review {i}: derived {derived} requires both reviewer_id and worker_id to confirm distinct contexts")
        if claimed in SEVERITY_ORDER and derived in SEVERITY_ORDER:
            if SEVERITY_ORDER[claimed] > SEVERITY_ORDER[derived]:
                fail(errors, f"review {i}: claimed {claimed} exceeds registry-derived {derived}")
        if reviewer_id:
            reviewer_history.append(reviewer_id)
            if len(reviewer_history) >= 5:
                window = reviewer_history[-5:]
                if len(set(window)) == 1:
                    warn(warnings, f"review {i}: same reviewer '{reviewer_id}' accepted last 5 consecutive reviews (reviewer capture risk)")


def validate_green_floors(root, state, errors, warnings):
    excel = get_excellence_state(state)
    floors = as_dict(excel.get("green_floors"))
    current_metrics = as_list(excel.get("metrics"))
    iterations_completed = excel.get("iterations_completed", 0)
    if not floors:
        if isinstance(iterations_completed, int) and iterations_completed >= 1:
            fail(errors, "green_floors missing despite iterations_completed>=1; regression protection defeated")
        else:
            warn(warnings, "green_floors empty; regression protection starts after first completed iteration")
        return
    current_by_name = {m.get("metric"): m for m in current_metrics if isinstance(m, dict) and m.get("metric")}
    for iteration, metrics in floors.items():
        for metric_name, floor_value in as_dict(metrics).items():
            metric = current_by_name.get(metric_name)
            if not metric:
                fail(errors, f"metric '{metric_name}' has green floor from iteration {iteration} but is no longer in current metric set — dropped/renamed metrics cannot escape regression protection")
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


def validate_iteration_budget(state, errors, warnings):
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
        warn(warnings, "remaining budget allocation missing")


def validate_budget_monotonic(root, state, errors, warnings):
    deltas = load_yaml(root / ".bagel/evidence/progress-deltas.yaml", [])
    prev_used = None
    for i, delta in enumerate(as_list(deltas), start=1):
        d = as_dict(delta)
        cost = as_dict(d.get("cost"))
        used = numeric(cost.get("cumulative_tokens") or cost.get("tokens_used"))
        if used is None:
            continue
        if prev_used is not None and used < prev_used:
            fail(errors, f"cycle {i}: cumulative token usage {used} < previous {prev_used} — budget must be monotonically non-decreasing")
        prev_used = used


def validate_bar_raises(root, errors, warnings):
    raises = load_yaml(root / ".bagel/evidence/bar-raises.yaml", [])
    if not raises:
        warn(warnings, "bar-raises.yaml missing; flywheel may not prove standards were raised")
        return
    for i, item in enumerate(as_list(raises), start=1):
        row = as_dict(item)
        why = row.get("why_class")
        if why not in BAR_RAISE_VALUE_CLASSES:
            fail(errors, f"bar raise {i}: why_class '{why}' not in canonical set {sorted(BAR_RAISE_VALUE_CLASSES)}")
            continue
        if why == "churn":
            review_level = row.get("review_level")
            accepted = row.get("accepted")
            if review_level not in {"R3", "R4"} or accepted is not True:
                fail(errors, f"bar raise {i}: churn requires R3/R4 acceptance, got review_level={review_level} accepted={accepted}")
        if not row.get("evidence"):
            fail(errors, f"bar raise {i}: missing evidence")


def validate_stuck_metrics(state, root, errors, warnings):
    excel = get_excellence_state(state)
    stuck = as_list(excel.get("stuck_metrics"))
    if not stuck:
        return
    for i, entry in enumerate(stuck, start=1):
        e = as_dict(entry)
        metric_name = e.get("metric")
        classification = e.get("classification")
        if classification not in {"impossible", "needs_deescalation"}:
            fail(errors, f"stuck metric {i}: classification must be impossible|needs_deescalation, got '{classification}'")
            continue
        if classification == "impossible":
            signoff = e.get("review_level")
            if signoff not in {"R3", "R4"}:
                fail(errors, f"stuck metric {i} ({metric_name}): 'impossible' requires R3/R4 independent sign-off")
        cycles_stuck = e.get("cycles_stuck")
        if not isinstance(cycles_stuck, int) or cycles_stuck < 1:
            fail(errors, f"stuck metric {i} ({metric_name}): must record cycles_stuck >= 1")


def validate_flat_climbing(state, root, errors, warnings):
    excel = get_excellence_state(state)
    slope = as_dict(excel.get("trajectory_slope"))
    metrics = as_list(excel.get("metrics"))
    for m in metrics:
        md = as_dict(m)
        eps = md.get("epsilon")
        if eps is None:
            warn(warnings, f"metric '{md.get('metric')}' has no epsilon; flat-climbing detection cannot bound it")
        else:
            eps_num = numeric(eps)
            target_num = numeric(str(md.get("target", "")))
            if eps_num is not None and target_num is not None and eps_num > target_num * 0.5:
                fail(errors, f"metric '{md.get('metric')}': epsilon={eps_num} >50% of target — enables false flat_climbing")
    if not slope:
        warn(warnings, "trajectory_slope missing; low-yield forward movement cannot be detected")
        return
    recorded_flat = slope.get("flat_climbing")
    iter_deltas = as_list(slope.get("iteration_best_deltas"))
    if len(iter_deltas) >= 2:
        epsilons = {as_dict(m).get("metric"): numeric(as_dict(m).get("epsilon")) for m in metrics}
        last_two = iter_deltas[-2:]
        computed_flat = True
        for d in last_two:
            d_dict = as_dict(d)
            metric_name = d_dict.get("metric")
            delta_val = numeric(d_dict.get("delta"))
            eps = epsilons.get(metric_name)
            if delta_val is not None and eps is not None and delta_val >= eps:
                computed_flat = False
                break
        if recorded_flat is not None and recorded_flat != computed_flat:
            fail(errors, f"trajectory_slope.flat_climbing={recorded_flat} but recomputed={computed_flat} from deltas — boolean must match computed value")
    if slope.get("flat_climbing") is True:
        status = state.get("status") or state.get("run_status")
        if status not in {"flat_climbing", "complete", "waiting_for_capacity"}:
            fail(errors, "flat_climbing=true must be surfaced in run status")
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
    validate_green_floors(root, state, errors, warnings)
    validate_iteration_budget(state, errors, warnings)
    validate_budget_monotonic(root, state, errors, warnings)
    validate_bar_raises(root, errors, warnings)
    validate_stuck_metrics(state, root, errors, warnings)
    validate_flat_climbing(state, root, errors, warnings)
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
