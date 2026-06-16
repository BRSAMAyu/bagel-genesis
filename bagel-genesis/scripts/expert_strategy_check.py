#!/usr/bin/env python3
"""Validate V3 Expert Autonomy Layer strategy artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_EXPERT_FILES = {
    ".bagel/expert/domain-excellence.yaml": ("domain", "artifact_type", "what_excellent_means", "top_1_percent_work", "mediocre_work", "common_failure_modes", "hidden_quality_dimensions", "expert_review_questions"),
    ".bagel/expert/problem-framing.yaml": ("user_stated_problem", "inferred_real_problem", "possible_reframings", "chosen_framing", "rejected_framings"),
    ".bagel/expert/leverage-map.yaml": ("bottlenecks", "top_leverage_action"),
}


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


def validate_strategy_decision(path: Path, record: dict[str, Any], errors: list[str]) -> None:
    for field in ("decision_type", "options_considered", "selected_option", "rejected_options", "decisive_evidence", "biggest_uncertainty", "next_probe"):
        if not record.get(field):
            errors.append(f"{path}: strategy decision missing {field}")
    participants = as_list(record.get("participants"))
    required = {"Domain Expert", "Evaluation Skeptic", "User Proxy"}
    roles = {str(as_dict(p).get("role")) for p in participants}
    if not required <= roles:
        errors.append(f"{path}: strategy decision requires participants {sorted(required)}")
    if len({str(as_dict(p).get("agent_id")) for p in participants if as_dict(p).get("agent_id")}) < min(3, len(participants)):
        errors.append(f"{path}: strategy participants must record distinct agent_id values")


def validate(root: Path) -> tuple[list[str], list[str]]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    run_started = state.get("phase") in {"Build", "Iterate", "Polish"} or state.get("task_queue")
    errors: list[str] = []
    warnings: list[str] = []
    if not run_started:
        return errors, warnings

    for rel, required_fields in REQUIRED_EXPERT_FILES.items():
        path = root / rel
        data = as_dict(load_yaml(path, {}))
        if not data:
            errors.append(f"{rel}: required before Build/Iterate expert autonomy")
            continue
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{rel}: missing {field}")

    decisions_dir = root / ".bagel/expert/strategy-decisions"
    decisions = []
    if decisions_dir.exists():
        for path in sorted(decisions_dir.glob("*.yaml")):
            decisions.append((path, as_dict(load_yaml(path, {}))))
    for item in as_list(state.get("strategy_decisions")):
        decisions.append((root / ".bagel/state.yaml#strategy_decisions", as_dict(item)))
    if not decisions:
        errors.append("Build/Iterate work requires at least one expert strategy decision")
    for path, record in decisions:
        validate_strategy_decision(path, record, errors)

    breakthrough = as_dict(load_yaml(root / ".bagel/expert/breakthrough-search.yaml", {}))
    if breakthrough:
        operators = set(as_list(breakthrough.get("operators_used")))
        if len(operators) < 3:
            errors.append("breakthrough_search requires at least 3 operators when invoked")
        for i, candidate in enumerate(as_list(breakthrough.get("candidates")), start=1):
            c = as_dict(candidate)
            for field in ("what_assumption_it_breaks", "why_existing_solution_space_misses_it", "why_it_could_be_10x_better", "cheapest_falsifiable_probe", "risk_if_wrong", "evidence_needed_to_adopt"):
                if not c.get(field):
                    errors.append(f"breakthrough candidate {i}: missing {field}")
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
    print("BAGEL expert strategy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
