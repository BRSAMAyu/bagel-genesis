#!/usr/bin/env python3
"""Validate that BAGEL evaluation specs are expert-grade, not shallow proxy metrics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_CRITIC = {
    "metric_correlates_with_real_quality",
    "metric_not_easy_to_game",
    "covers_user_value",
    "covers_domain_excellence",
    "negative_examples",
    "baseline_comparison",
    "surface_overfit_risk",
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


def active_evaluation(root: Path) -> dict[str, Any]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    evaluation = as_dict(state.get("evaluation"))
    if evaluation:
        return evaluation
    return as_dict(load_yaml(root / ".bagel/evaluation/current.yaml", {}))


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
        missing = sorted(field for field in REQUIRED_CRITIC if field not in critic)
        if missing:
            errors.append("evaluation_critic missing checks: " + ", ".join(missing))
        if not critic.get("critic_agent_id") or not critic.get("review_ref"):
            errors.append("evaluation_critic requires critic_agent_id and review_ref")
        for key in REQUIRED_CRITIC:
            value = critic.get(key)
            if value in {False, "fail", "missing"}:
                errors.append(f"evaluation_critic.{key} failed")

    domain_model = as_dict(evaluation.get("domain_excellence_model"))
    if not domain_model:
        errors.append("evaluation spec requires domain_excellence_model")
    else:
        for field in ("what_excellent_means", "top_1_percent_work", "mediocre_work", "common_failure_modes", "hidden_quality_dimensions", "expert_review_questions"):
            if not domain_model.get(field):
                errors.append(f"domain_excellence_model missing {field}")

    metrics = as_list(evaluation.get("metrics"))
    rubrics = as_list(evaluation.get("qualitative_rubric"))
    if not metrics and not rubrics:
        errors.append("evaluation spec must include metrics or qualitative_rubric")
    for i, metric in enumerate(metrics, start=1):
        m = as_dict(metric)
        for field in ("decision_use", "anti_gaming_note", "real_quality_link", "failure_mode_if_optimized"):
            if not m.get(field):
                errors.append(f"metric {i}: missing {field}")
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
