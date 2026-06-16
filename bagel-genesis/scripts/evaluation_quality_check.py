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

# S4 gameable-metric pairing detector.
# Retrieval/ranking-style metrics that are trivially gameable when used as the
# SOLE headline (memorized index, inverted lookup, test-set overfit all maximize
# these without improving real retrieval quality).
GAMEABLE_HEADLINE_METRICS = (
    "hit@1", "hit@k", "hit_at_1", "hit_at_k", "top1", "top_1_accuracy",
    "precision@1", "precision_at_1", "accuracy@1", "recall@1", "recall_at_1",
    "exact_match@1", "exact_match", "em@1",
)
# Metrics that measure robustness/ranking quality, not just top-1 correctness.
# When at least one of these is present alongside a gameable headline, the spec
# is considered paired (not sole-gameable).
ROBUSTNESS_PAIR_METRICS = (
    "mrr", "mean_reciprocal_rank", "ndcg", "ndcg@k", "ndcg_at_k",
    "map", "mean_average_precision", "average_precision",
    "recall@10", "recall@100", "recall_at_10", "recall_at_100",
    "nDCG", "NDCG", "MRR",
    "held_out", "held-out", "heldout", "generalization_gap", "generalization gap",
    "out_of_distribution", "ood", "transfer_accuracy", "cross_domain",
    "diversity", "coverage", "calibration", "ece",
)


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


def validate_gameable_metric_pairing(metrics: list[dict[str, Any]], errors: list[str]) -> None:
    """S4 scenario gate: a gameable headline metric cannot be the sole quality signal.

    Two-tier check (paraphrase-proof):
    PRIMARY: if metrics declare a structured `metric_role` from the fixed enum
    (gameable_top1 / ranking_robustness / held_out_generalization / qualitative /
    other), check structurally — a metric_role=gameable_top1 without a sibling
    metric_role=ranking_robustness or held_out_generalization fails. The role is
    declared, not inferred from the metric name, so it cannot be paraphrased away.
    FALLBACK: for metrics without a metric_role, scan the name/id/decision_use blob
    for gameable headline substrings (hit@1/precision@1/exact-match) without a
    robustness pair (MRR/nDCG/MAP/recall@k/held-out). This is evadable by renaming
    the metric; the structured role path is the authoritative check.
    """
    if not metrics:
        return
    metric_dicts = [as_dict(m) for m in metrics]
    # PRIMARY: structured metric_role declarations
    roles = [str(m.get("metric_role") or "").lower() for m in metric_dicts]
    has_structured_role = any(roles)
    if has_structured_role:
        has_gameable_role = any(r == "gameable_top1" for r in roles)
        has_robustness_role = any(r in ("ranking_robustness", "held_out_generalization") for r in roles)
        if has_gameable_role and not has_robustness_role:
            errors.append(
                "evaluation_critic: a metric with metric_role=gameable_top1 is declared "
                "without a paired metric_role=ranking_robustness or held_out_generalization. "
                "A gameable top-1 metric cannot be the sole quality signal — declare a "
                "robustness/ranking role alongside it (structured role path, paraphrase-proof)."
            )
            return
        # If structured roles are present and the pairing holds (or no gameable role),
        # the structured path is authoritative — do not also run the weaker substring path.
        if has_gameable_role and has_robustness_role:
            return
    # FALLBACK: name/id/decision_use substring matching (evadable by renaming)
    blob_parts: list[str] = []
    for m in metric_dicts:
        for key in ("name", "id", "metric", "decision_use", "real_quality_link"):
            blob_parts.append(str(m.get(key) or ""))
    blob = " ".join(blob_parts).lower()
    has_gameable_headline = any(g in blob for g in GAMEABLE_HEADLINE_METRICS)
    if not has_gameable_headline:
        return  # no gameable headline present — pairing rule does not apply
    has_robustness_pair = any(p.lower() in blob for p in ROBUSTNESS_PAIR_METRICS)
    if not has_robustness_pair:
        errors.append(
            "evaluation_critic: a gameable retrieval headline metric (hit@1/precision@1/"
            "exact-match@1) is present without a paired robustness/ranking metric "
            "(MRR/nDCG/MAP/recall@k/held-out/generalization). A gameable headline "
            "cannot be the sole quality signal — pair it with a metric that resists "
            "memorization/index overfit, OR declare metric_role on each metric "
            "(structured path, paraphrase-proof). (see evaluation-critic surface_overfit_risk)."
        )


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
    # S4 gameable-metric pairing check (applies before per-metric discrimination)
    validate_gameable_metric_pairing(metrics, errors)
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
