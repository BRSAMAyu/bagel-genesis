#!/usr/bin/env python3
"""Validate that BAGEL evaluation specs discriminate real quality."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


PASS_FAIL_FIELDS = {
    "metric_correlates_with_real_quality",
    "metric_not_easy_to_game",
    "covers_user_value",
    "covers_domain_excellence",
}
REQUIRED_CRITIC_FIELDS = PASS_FAIL_FIELDS | {"negative_examples", "baseline_comparison", "surface_overfit_risk"}
SURFACE_RISK = {"low", "medium", "high"}


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


def active_evaluation(root: Path) -> dict[str, Any]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    evaluation = as_dict(state.get("evaluation"))
    if evaluation:
        return evaluation
    return as_dict(load_yaml(root / ".bagel/evaluation/current.yaml", {}))


def validate_discrimination(root: Path, metric: dict[str, Any], idx: int, errors: list[str]) -> None:
    check = as_dict(metric.get("metric_discrimination_check"))
    if not check:
        errors.append(f"metric {idx}: missing metric_discrimination_check")
        return
    for side in ("bad_example", "strong_example"):
        row = as_dict(check.get(side))
        for field in ("description", "expected_metric_result"):
            if not row.get(field):
                errors.append(f"metric {idx}: {side} missing {field}")
        if side == "bad_example" and not row.get("why_bad"):
            errors.append(f"metric {idx}: bad_example missing why_bad")
        if side == "strong_example" and not row.get("why_strong"):
            errors.append(f"metric {idx}: strong_example missing why_strong")
    if check.get("distinguishes_bad_from_strong") is not True:
        errors.append(f"metric {idx}: metric_discrimination_check must distinguish bad from strong")
    ref = check.get("evidence_ref")
    if not ref or not (root / str(ref)).exists():
        errors.append(f"metric {idx}: metric_discrimination_check.evidence_ref missing or nonexistent")


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    run_started = state.get("phase") in {"Build", "Iterate", "Polish"} or state.get("task_queue") or (root / ".bagel/evidence/progress-deltas.yaml").exists()
    evaluation = active_evaluation(root)
    if not evaluation:
        return (["expert evaluation quality cannot be checked because active evaluation spec is missing"], []) if run_started else ([], [])

    critic = as_dict(evaluation.get("evaluation_critic"))
    if not critic:
        errors.append("active evaluation spec requires evaluation_critic review")
    else:
        missing = sorted(field for field in REQUIRED_CRITIC_FIELDS if field not in critic)
        if missing:
            errors.append("evaluation_critic missing checks: " + ", ".join(missing))
        if not critic.get("critic_agent_id") or not critic.get("review_ref"):
            errors.append("evaluation_critic requires critic_agent_id and review_ref")
        for key in PASS_FAIL_FIELDS:
            if critic.get(key) not in {True, "pass"}:
                errors.append(f"evaluation_critic.{key} must pass")
        if not as_list(critic.get("negative_examples")):
            errors.append("evaluation_critic.negative_examples must be a non-empty list")
        if not as_list(critic.get("baseline_comparison")):
            errors.append("evaluation_critic.baseline_comparison must be a non-empty list")
        if critic.get("surface_overfit_risk") not in SURFACE_RISK:
            errors.append("evaluation_critic.surface_overfit_risk must be low|medium|high")

    domain_model = as_dict(evaluation.get("domain_excellence_model"))
    if not domain_model:
        errors.append("evaluation spec requires domain_excellence_model")
    else:
        for field in ("what_excellent_means", "top_1_percent_work", "common_failure_modes", "hidden_quality_dimensions"):
            if not domain_model.get(field):
                errors.append(f"domain_excellence_model missing {field}")

    metrics = as_list(evaluation.get("metrics"))
    rubrics = as_list(evaluation.get("qualitative_rubric"))
    if not metrics and not rubrics:
        errors.append("evaluation spec must include metrics or qualitative_rubric")
    has_compensating_rubric = any(as_dict(item).get("compensates_surface_overfit") is True for item in rubrics)
    for i, metric in enumerate(metrics, start=1):
        m = as_dict(metric)
        for field in ("decision_use", "anti_gaming_note", "real_quality_link", "failure_mode_if_optimized"):
            if not m.get(field):
                errors.append(f"metric {i}: missing {field}")
        validate_discrimination(root, m, i, errors)
        if m.get("surface_overfit_risk") == "high" and m.get("gates_iteration_completion") is True and not has_compensating_rubric:
            errors.append(f"metric {i}: high surface_overfit_risk cannot gate iteration completion without compensating qualitative rubric")
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
    print("BAGEL evaluation quality check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
