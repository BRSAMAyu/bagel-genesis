#!/usr/bin/env python3
"""Statistical-rigor gate for research Mode 1 (protocol_execution) — the bundle
that separates "passed BAGEL governance" from "would survive NeurIPS/ICML/ICLR
review." research_governance_check.py already locks down provenance (plan
hashing, pre-result write binding, post-hoc labeling, authority refs). It does
NOT enforce that a *confirmatory* claim is statistically honest. This gate does.

It is the mechanical encoding of the top reasons a top-tier referee desk-rejects
an empirical paper:

  1. Single-seed / no-variance headline. A point estimate with no dispersion over
     a declared number of runs is not a result. Top venues require error bars.
  2. "Significant" with no test. A comparative claim with no test statistic,
     p-value, and effect size is an assertion, not evidence.
  3. Uncorrected multiple comparisons. >1 confirmatory comparison with no
     multiple-comparison correction is p-hacking surface.
  4. Statistically-significant-but-trivial. A real effect below the *preregistered*
     practical-significance threshold cannot be a headline.
  5. Unfair baselines. A method compared to a baseline that did not get comparable
     tuning/compute/data budget is the single most common "unfair comparison"
     reject — parity must be declared, asymmetry must be justified.
  6. No compute reporting. The NeurIPS reproducibility checklist requires the
     accelerator and total run count behind the numbers.

Scope: only research-like runs, only after Build starts, and only CONFIRMATORY or
headline claims are held to this bar — exploratory/negative/limitation claims and
non-research runs are untouched (discovery stays cheap; only the load-bearing
headline is held to paper grade).

Schema additions (documented in references/research-governance.md):

    experiment_plan:
      analysis_plan:
        statistical_test: "paired bootstrap, 10k resamples"
        correction: "Holm-Bonferroni"   # required once >1 confirmatory comparison
        min_seeds: 5                     # hard floor: >= 3
        effect_size_metric: "Cohen's d"
      seeds: [0, 1, 2, 3, 4]             # len(seeds) >= min_seeds
      baselines:
        - id: "baseline-A"
          parity:
            tuning_budget_matched: true
            compute_matched: true
            data_matched: true
            justification: ""            # required if ANY matched flag is false
      compute_budget:
        accelerator: "A100-80GB"
        total_runs: 30
        gpu_hours: 12.5                  # warned-if-missing, not failed

    claim_evidence_matrix:
      claims:
        - claim_id: C1
          claim_type: confirmatory
          allowed_in_headline: true
          statistics:
            n_runs: 5                    # >= min_seeds
            aggregation: mean            # mean | median
            dispersion_type: ci95        # std | sem | ci95 | iqr
            dispersion_value: 0.012
            comparison_baseline: "baseline-A"   # which baseline this beats
            test: "paired bootstrap, 10k resamples"
            p_value: 0.003
            effect_size: 0.81
            effect_size_metric: "Cohen's d"
            meets_practical_significance: true   # effect vs prereg threshold

Honest limit (same class as the rest of the suite): this verifies the *shape and
internal consistency* of the reported statistics — that error bars, a test, an
effect size, correction, parity, and compute are present and mutually coherent.
It does not recompute the p-value from raw per-seed data (that is the job of
metric_recompute evidence + an external referee). It makes the statistically
dishonest run impossible to pass *by omission*; it cannot by itself catch a
fabricated-but-well-formed number. Pair with metric_recompute + a research
referee for full closure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

RESEARCH_SIGNALS = ("research", "experiment", "benchmark", "study", "theory", "analysis")
AGGREGATIONS = {"mean", "median"}
DISPERSIONS = {"std", "sem", "ci95", "ci99", "iqr", "stderr"}
MIN_SEEDS_FLOOR = 3


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


def is_research_like(root: Path, state: dict, constitution: dict) -> bool:
    artifact_type = str(
        as_dict(state.get("artifact_profile")).get("type")
        or constitution.get("artifact_type")
        or state.get("artifact_type")
        or ""
    ).lower()
    if any(sig in artifact_type for sig in RESEARCH_SIGNALS):
        return True
    if as_dict(constitution.get("research_autonomy")):
        return True
    return (root / ".bagel/research").exists()


def build_started(state: dict, root: Path) -> bool:
    phase = str(state.get("run_phase") or state.get("phase") or "").lower()
    if phase in {"build", "iterate", "polish", "excellence_loop", "complete"}:
        return True
    if state.get("task_queue"):
        return True
    return (root / ".bagel/evidence/progress-deltas.yaml").exists()


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))

    if not is_research_like(root, state, constitution):
        return errors, warnings
    mode = str(as_dict(constitution.get("research_autonomy")).get("mode") or "")
    if not build_started(state, root):
        return errors, warnings

    plan_doc = as_dict(load_yaml(root / ".bagel/research/experiment-plan.yaml", {}))
    plan = as_dict(plan_doc.get("experiment_plan")) or plan_doc
    claims_doc = as_dict(load_yaml(root / ".bagel/research/claim-evidence.yaml", {}))
    matrix = as_dict(claims_doc.get("claim_evidence_matrix")) or claims_doc
    claims = [as_dict(c) for c in as_list(matrix.get("claims"))]

    # Confirmatory or explicitly-headline claims are held to paper grade.
    headline_claims = [
        c for c in claims
        if c.get("claim_type") == "confirmatory"
        or c.get("allowed_in_headline") is True
        or c.get("is_headline") is True
    ]
    if not headline_claims:
        # No load-bearing claim yet — nothing to hold to this bar.
        return errors, warnings

    analysis = as_dict(plan.get("analysis_plan"))
    seeds = as_list(plan.get("seeds"))

    # ---- Plan-level statistical declarations -------------------------------
    min_seeds = analysis.get("min_seeds")
    if not isinstance(min_seeds, int):
        errors.append(
            "statistical_rigor: analysis_plan.min_seeds is required (int) once a "
            "confirmatory/headline claim exists — declare the seed floor that "
            "headline numbers must aggregate over"
        )
        min_seeds = None
    elif min_seeds < MIN_SEEDS_FLOOR:
        errors.append(
            f"statistical_rigor: analysis_plan.min_seeds={min_seeds} is below the "
            f"hard floor of {MIN_SEEDS_FLOOR}; a single/double-seed headline is not "
            "a top-venue result"
        )
    if min_seeds and len(seeds) < min_seeds:
        errors.append(
            f"statistical_rigor: plan declares min_seeds={min_seeds} but only "
            f"{len(seeds)} seeds are registered in plan.seeds"
        )

    # Multiple comparisons → correction required.
    comparative = [
        c for c in headline_claims
        if as_dict(c.get("statistics")).get("comparison_baseline")
    ]
    if len(comparative) > 1 and not str(analysis.get("correction") or "").strip():
        errors.append(
            f"statistical_rigor: {len(comparative)} confirmatory comparative claims "
            "exist but analysis_plan.correction is empty — uncorrected multiple "
            "comparisons are p-hacking surface (declare Holm/Bonferroni/BH/etc.)"
        )

    # Compute reporting (NeurIPS checklist).
    compute = as_dict(plan.get("compute_budget"))
    if not str(compute.get("accelerator") or "").strip():
        errors.append(
            "statistical_rigor: compute_budget.accelerator is required for headline "
            "results (e.g. 'A100-80GB', 'CPU-only') — reviewers need the hardware"
        )
    if not is_number(compute.get("total_runs")):
        errors.append(
            "statistical_rigor: compute_budget.total_runs (numeric) is required — "
            "the total number of runs behind the reported numbers"
        )
    if not is_number(compute.get("gpu_hours")) and not str(compute.get("wall_clock") or "").strip():
        warnings.append(
            "statistical_rigor: compute_budget has neither gpu_hours nor wall_clock; "
            "top venues expect a compute cost estimate"
        )

    # Baseline parity table indexed by id.
    baselines = {}
    for b in as_list(plan.get("baselines")):
        if isinstance(b, dict):
            bid = str(b.get("id") or b.get("name") or "")
            if bid:
                baselines[bid] = b

    # Per-hypothesis practical-significance thresholds.
    practical_threshold = {}
    for h in as_list(plan.get("hypotheses")):
        h = as_dict(h)
        hid = str(h.get("id") or "")
        if hid:
            practical_threshold[hid] = h.get("practical_significance_threshold")

    # ---- Per-claim statistical honesty -------------------------------------
    for c in headline_claims:
        cid = c.get("claim_id") or "<claim>"
        stats = as_dict(c.get("statistics"))
        if not stats:
            errors.append(
                f"statistical_rigor: {cid} is confirmatory/headline but has no "
                "`statistics` block — a headline number needs runs, dispersion, a "
                "test, and an effect size"
            )
            continue

        n_runs = stats.get("n_runs")
        if not isinstance(n_runs, int):
            errors.append(f"statistical_rigor: {cid} statistics.n_runs (int) is required")
        elif min_seeds and n_runs < min_seeds:
            errors.append(
                f"statistical_rigor: {cid} aggregates n_runs={n_runs} but plan "
                f"min_seeds={min_seeds}; headline must aggregate at least the seed floor"
            )

        if str(stats.get("aggregation") or "") not in AGGREGATIONS:
            errors.append(
                f"statistical_rigor: {cid} statistics.aggregation must be one of "
                f"{sorted(AGGREGATIONS)}"
            )
        if str(stats.get("dispersion_type") or "") not in DISPERSIONS:
            errors.append(
                f"statistical_rigor: {cid} statistics.dispersion_type must be one of "
                f"{sorted(DISPERSIONS)} — a point estimate with no error bar is not a result"
            )
        if not is_number(stats.get("dispersion_value")):
            errors.append(
                f"statistical_rigor: {cid} statistics.dispersion_value (numeric) is "
                "required — report the actual error bar"
            )

        # Comparative confirmatory claims need a real test + effect size.
        baseline_ref = str(stats.get("comparison_baseline") or "")
        if baseline_ref:
            if not str(stats.get("test") or "").strip():
                errors.append(
                    f"statistical_rigor: {cid} compares to baseline {baseline_ref!r} "
                    "but statistics.test is empty — declare the significance test"
                )
            else:
                declared_test = str(analysis.get("statistical_test") or "").strip().lower()
                if declared_test and declared_test not in str(stats.get("test")).strip().lower() \
                        and str(stats.get("test")).strip().lower() not in declared_test:
                    warnings.append(
                        f"statistical_rigor: {cid} statistics.test does not match the "
                        "preregistered analysis_plan.statistical_test"
                    )
            if not is_number(stats.get("p_value")):
                errors.append(
                    f"statistical_rigor: {cid} comparative claim needs a numeric p_value"
                )
            if not is_number(stats.get("effect_size")):
                errors.append(
                    f"statistical_rigor: {cid} comparative claim needs a numeric "
                    "effect_size (statistical significance without effect size is "
                    "uninterpretable)"
                )
            if not str(stats.get("effect_size_metric") or "").strip():
                errors.append(
                    f"statistical_rigor: {cid} needs effect_size_metric (e.g. "
                    "Cohen's d, rel. improvement)"
                )
            # Baseline parity for the compared baseline.
            b = as_dict(baselines.get(baseline_ref))
            parity = as_dict(b.get("parity"))
            if not b:
                errors.append(
                    f"statistical_rigor: {cid} compares to baseline {baseline_ref!r} "
                    "not declared in plan.baselines"
                )
            elif not parity:
                errors.append(
                    f"statistical_rigor: baseline {baseline_ref!r} (compared by {cid}) "
                    "has no parity block — declare tuning/compute/data parity vs the method"
                )
            else:
                unmatched = [
                    k for k in ("tuning_budget_matched", "compute_matched", "data_matched")
                    if parity.get(k) is not True
                ]
                if unmatched and not str(parity.get("justification") or "").strip():
                    errors.append(
                        f"statistical_rigor: baseline {baseline_ref!r} parity has "
                        f"unmatched {unmatched} without a justification — an unequal "
                        "comparison must be explicitly justified"
                    )

            # Practical significance: effect must clear the preregistered threshold,
            # or the claim must be explicitly marked as not meeting it (and then not
            # headlined).
            mps = stats.get("meets_practical_significance")
            if not isinstance(mps, bool):
                errors.append(
                    f"statistical_rigor: {cid} statistics.meets_practical_significance "
                    "(bool) is required — compare the effect to the preregistered "
                    "practical_significance_threshold"
                )
            elif mps is False and c.get("allowed_in_headline") is True:
                errors.append(
                    f"statistical_rigor: {cid} does not meet practical significance "
                    "but is allowed_in_headline — a statistically-significant but "
                    "practically-trivial effect must not be a headline"
                )
            hid = str(c.get("hypothesis_id") or "")
            if hid and practical_threshold.get(hid) in (None, "") and hid in practical_threshold:
                warnings.append(
                    f"statistical_rigor: hypothesis {hid} has no "
                    "practical_significance_threshold to compare {cid}'s effect against"
                )

    if mode == "protocol_execution":
        # In strict mode every confirmatory claim must bind to a registered
        # hypothesis (no orphan headline introduced during execution).
        hyp_ids = {str(as_dict(h).get("id")) for h in as_list(plan.get("hypotheses"))}
        for c in headline_claims:
            if c.get("claim_type") == "confirmatory" and str(c.get("hypothesis_id") or "") not in hyp_ids:
                errors.append(
                    f"statistical_rigor: confirmatory {c.get('claim_id')} is not bound "
                    "to a preregistered hypothesis_id (protocol_execution forbids "
                    "orphan confirmatory claims)"
                )
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--strict-warnings", action="store_true",
                        help="treat warnings as failures")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()
    errors, warnings = validate(Path(args.root).resolve())
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL statistical-rigor check passed.")
    return 0


def _GOOD_PLAN() -> dict:
    return {"experiment_plan": {
        "schema_version": "research_experiment_plan_v1",
        "seeds": [0, 1, 2, 3, 4],
        "hypotheses": [{"id": "H1", "practical_significance_threshold": "Cohen's d >= 0.5"}],
        "analysis_plan": {"statistical_test": "paired bootstrap, 10k resamples",
                          "correction": "Holm-Bonferroni", "min_seeds": 5,
                          "effect_size_metric": "Cohen's d"},
        "baselines": [{"id": "baseline-A", "parity": {
            "tuning_budget_matched": True, "compute_matched": True, "data_matched": True}}],
        "compute_budget": {"accelerator": "A100-80GB", "total_runs": 30, "gpu_hours": 12.5},
    }}


def _GOOD_CLAIM() -> dict:
    return {"claim_id": "C1", "claim_type": "confirmatory", "hypothesis_id": "H1",
            "allowed_in_headline": True, "statistics": {
                "n_runs": 5, "aggregation": "mean", "dispersion_type": "ci95",
                "dispersion_value": 0.012, "comparison_baseline": "baseline-A",
                "test": "paired bootstrap, 10k resamples", "p_value": 0.003,
                "effect_size": 0.81, "effect_size_metric": "Cohen's d",
                "meets_practical_significance": True}}


def _self_test() -> int:
    import copy
    import tempfile

    def run(plan, claim):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rdir = root / ".bagel" / "research"
            rdir.mkdir(parents=True)
            (root / ".bagel" / "constitution.yaml").write_text(
                yaml.safe_dump({"research_autonomy": {"mode": "protocol_execution"}}),
                encoding="utf-8")
            (root / ".bagel" / "state.yaml").write_text(
                yaml.safe_dump({"run_phase": "iterate"}), encoding="utf-8")
            (rdir / "experiment-plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
            (rdir / "claim-evidence.yaml").write_text(
                yaml.safe_dump({"claim_evidence_matrix": {"claims": [claim]}}), encoding="utf-8")
            return validate(root)

    cases = []
    cases.append(("fully-rigorous confirmatory claim -> OK", _GOOD_PLAN(), _GOOD_CLAIM(), True))

    p = copy.deepcopy(_GOOD_PLAN()); p["experiment_plan"]["analysis_plan"]["min_seeds"] = 1
    cases.append(("min_seeds below floor -> FAIL", p, _GOOD_CLAIM(), False))

    c = copy.deepcopy(_GOOD_CLAIM()); del c["statistics"]["dispersion_type"]; del c["statistics"]["dispersion_value"]
    cases.append(("no error bar -> FAIL", _GOOD_PLAN(), c, False))

    c = copy.deepcopy(_GOOD_CLAIM()); del c["statistics"]["p_value"]; del c["statistics"]["effect_size"]
    cases.append(("comparison without test stats -> FAIL", _GOOD_PLAN(), c, False))

    c = copy.deepcopy(_GOOD_CLAIM()); c["statistics"]["meets_practical_significance"] = False
    cases.append(("headline below practical significance -> FAIL", _GOOD_PLAN(), c, False))

    p = copy.deepcopy(_GOOD_PLAN())
    p["experiment_plan"]["baselines"][0]["parity"] = {
        "tuning_budget_matched": False, "compute_matched": True, "data_matched": True}
    cases.append(("unmatched baseline parity w/o justification -> FAIL", p, _GOOD_CLAIM(), False))

    p = copy.deepcopy(_GOOD_PLAN()); del p["experiment_plan"]["compute_budget"]["accelerator"]
    cases.append(("no compute accelerator -> FAIL", p, _GOOD_CLAIM(), False))

    c = copy.deepcopy(_GOOD_CLAIM()); c["statistics"]["n_runs"] = 2
    cases.append(("n_runs below min_seeds -> FAIL", _GOOD_PLAN(), c, False))

    # Exploratory claim is untouched even if it has no statistics.
    c = {"claim_id": "E1", "claim_type": "exploratory", "hypothesis_id": "H1"}
    cases.append(("exploratory claim, no stats -> OK (not held to bar)", _GOOD_PLAN(), c, True))

    passed = 0
    for name, plan, claim, expect_pass in cases:
        errors, _ = run(plan, claim)
        ok = (len(errors) == 0) == expect_pass
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  (errors={errors})"))
        passed += int(ok)
    print(f"{passed}/{len(cases)} self-test cases passed.")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
