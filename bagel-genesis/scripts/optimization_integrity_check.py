#!/usr/bin/env python3
"""Optimizer (Mode 2, objective: optimization) anti-gaming gate. An agent pointed at
a benchmark score is the textbook setup for the worst integrity failures — test
leakage, validation overfit, seed cherry-picking, "improving the measurement not the
method." Style B is therefore NOT lighter than Mode 1; it is the full Mode-1 rigor
stack (statistical_rigor + data_leakage + reproducibility + referee, which fire on the
confirmatory headline) PLUS the optimization-specific checks here.

The freedom is in the *method* (the agent may tune, swap components, or replace the
user's method entirely); the rigor on the *number* is absolute:

  1. Target locked first. `.bagel/research/optimization-target.yaml` declares each
     benchmark, metric, goal, and the user's `current_baseline` (the bar to beat) and
     a split policy — written before gains are claimed. You cannot move a bar you
     never wrote down.
  2. Selection on validation, never test. Every KEPT variant in the optimization log
     must have been selected on a validation/train split, not test. A kept variant
     selected on test turns the benchmark into a training signal.
  3. Honest denominator. Every variant tried is logged (not just the winner), so a
     gain that is really one-in-N noise is visible. Once enough variants were tried,
     the headline must be confirmed on held-out test (touched once) — the held-out
     evaluation is the correction for having shopped many variants on validation.
  4. The headline gain binds the Mode-1 confirmatory stack. The improvement claim must
     be `claim_type: confirmatory` (so statistical_rigor/data_leakage/reproducibility
     all apply), must beat `current_baseline`, and must be evaluated on test, not val.
  5. The gain is attributed. An ablation must tie the improvement to the specific
     change — a 0.82->0.87 headline with no ablation is an unattributed (possibly
     spurious) jump, not a method improvement.

Scope: research-like runs where the constitution declares
`research_autonomy.objective: optimization` (or an `optimization_contract` exists),
after Build. Inert otherwise.

Honest limit: this proves the optimization *protocol* was honest (locked target,
val-selection, logged denominator, held-out confirmation, attribution). It cannot,
by itself, prove the test set was never seen during training — that is the
`data_leakage` audit's job, which this gate composes with rather than duplicates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

RESEARCH_SIGNALS = ("research", "experiment", "benchmark", "study", "theory", "analysis")
VAL_SPLITS = {"validation", "val", "train", "dev", "development"}


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


def is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def optimization_active(constitution: dict) -> bool:
    ra = as_dict(constitution.get("research_autonomy"))
    if not ra:
        return False
    return str(ra.get("objective") or "").lower() == "optimization" or bool(
        as_dict(ra.get("optimization_contract"))
    )


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
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    if not optimization_active(constitution):
        return errors, warnings
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    if not build_started(state, root):
        return errors, warnings

    claims_doc = as_dict(load_yaml(root / ".bagel/research/claim-evidence.yaml", {}))
    matrix = as_dict(claims_doc.get("claim_evidence_matrix")) or claims_doc
    claims = [as_dict(c) for c in as_list(matrix.get("claims"))]
    gain_claims = [
        c for c in claims
        if c.get("claim_type") == "confirmatory"
        or c.get("is_optimization_headline") is True
        or c.get("allowed_in_headline") is True
    ]

    target_doc = as_dict(load_yaml(root / ".bagel/research/optimization-target.yaml", {}))
    target = as_dict(target_doc.get("optimization_target")) or target_doc
    targets = [as_dict(t) for t in as_list(target.get("targets"))]

    log_doc = as_dict(load_yaml(root / ".bagel/research/optimization-log.yaml", {}))
    opt_log = as_dict(log_doc.get("optimization_log")) or log_doc
    variants = [as_dict(v) for v in as_list(opt_log.get("variants"))]

    # ---- 1. Target locked --------------------------------------------------
    if not targets:
        # Only required once a gain is being claimed (in-progress runs may not have
        # picked a winner yet, but they MUST have locked the target before claiming).
        if gain_claims:
            errors.append(
                "optimization_integrity: a headline gain is claimed but "
                ".bagel/research/optimization-target.yaml declares no targets — the "
                "benchmark, metric, and current_baseline must be locked before claiming"
            )
        return errors, warnings
    for i, t in enumerate(targets, start=1):
        if not str(t.get("benchmark") or "").strip():
            errors.append(f"optimization_integrity: target {i} has no benchmark name")
        if not str(t.get("metric") or "").strip():
            errors.append(f"optimization_integrity: target {i} has no metric")
        if not is_number(t.get("current_baseline")):
            errors.append(
                f"optimization_integrity: target {i} has no numeric current_baseline — "
                "the bar to beat must be a recorded number, not 'the user's method'"
            )
        if str(t.get("goal") or "").lower() not in {"maximize", "minimize"}:
            errors.append(f"optimization_integrity: target {i} goal must be maximize|minimize")

    # ---- 2. Selection on validation, never test ----------------------------
    kept = [v for v in variants if v.get("kept") is True]
    for v in variants:
        split = str(v.get("selection_split") or "").lower()
        if v.get("kept") is True:
            if not split:
                errors.append(
                    f"optimization_integrity: kept variant {v.get('variant_id')!r} does not "
                    "declare selection_split — every kept improvement must say which split "
                    "selected it"
                )
            elif split == "test":
                errors.append(
                    f"optimization_integrity: kept variant {v.get('variant_id')!r} was selected "
                    "on the TEST split — selecting on test turns the benchmark into a training "
                    "signal; select on validation"
                )
            elif split not in VAL_SPLITS:
                errors.append(
                    f"optimization_integrity: kept variant {v.get('variant_id')!r} selection_split "
                    f"{split!r} is not a validation/train split"
                )

    if not gain_claims:
        # Optimization underway but no headline yet — target + selection discipline is
        # all we can check. (The honest denominator + held-out confirmation are required
        # only when a gain is actually claimed.)
        return errors, warnings

    # ---- 3 + 4 + 5. Headline gain must be honest ---------------------------
    if not variants:
        errors.append(
            "optimization_integrity: a headline gain is claimed but "
            ".bagel/research/optimization-log.yaml lists no variants — the honest "
            "denominator (every variant tried, not just the winner) must be recorded"
        )

    baselines = {str(t.get("benchmark")): t.get("current_baseline") for t in targets}

    for c in gain_claims:
        cid = c.get("claim_id") or c.get("title") or "?"
        stats = as_dict(c.get("statistics"))
        eval_split = str(
            c.get("evaluated_on") or stats.get("split") or c.get("split") or ""
        ).lower()
        # 4a. headline must be on held-out test, not validation.
        if eval_split and eval_split in VAL_SPLITS:
            errors.append(
                f"optimization_integrity: headline gain claim {cid!r} reports a "
                f"{eval_split!r} score — the headline must be the held-out TEST evaluation "
                "(touched once), not the validation number it was selected on"
            )
        elif not eval_split:
            errors.append(
                f"optimization_integrity: headline gain claim {cid!r} does not declare "
                "evaluated_on (expected: test) — a benchmark headline must name the held-out "
                "split it was measured on"
            )
        # 4b. must beat the recorded baseline.
        final = c.get("final_score")
        if not is_number(final):
            errors.append(
                f"optimization_integrity: headline gain claim {cid!r} has no numeric "
                "final_score to compare against the locked baseline"
            )
        else:
            bench = str(c.get("benchmark") or (targets[0].get("benchmark") if targets else ""))
            base = baselines.get(bench, targets[0].get("current_baseline") if targets else None)
            goal = str((targets[0].get("goal") if targets else "maximize")).lower()
            if is_number(base):
                better = final > base if goal == "maximize" else final < base
                if not better:
                    errors.append(
                        f"optimization_integrity: headline gain claim {cid!r} final_score "
                        f"{final} does not beat the locked baseline {base} (goal={goal}) — "
                        "do not headline a non-improvement"
                    )
        # 5. gain must be attributed by an ablation.
        if not (
            str(c.get("ablation_ref") or "").strip()
            or as_dict(c.get("ablation"))
            or c.get("gain_attributed") is True
        ):
            errors.append(
                f"optimization_integrity: headline gain claim {cid!r} has no ablation_ref/"
                "ablation attributing the improvement to the specific change — an "
                "unattributed score jump is not a method improvement"
            )

    # 3b. Honest denominator: many variants shopped on val -> the held-out test
    # confirmation IS required (already enforced above by evaluated_on==test), and a
    # multiple-comparison correction should be declared on the claim's statistics.
    if len(kept) + len([v for v in variants if v.get("kept") is not True]) >= 3:
        for c in gain_claims:
            stats = as_dict(c.get("statistics"))
            if not str(stats.get("correction") or "").strip():
                warnings.append(
                    f"optimization_integrity: {len(variants)} variants were shopped but headline "
                    f"claim {c.get('claim_id')!r} declares no multiple-comparison correction in "
                    "its statistics — selecting the best of many inflates significance"
                )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--strict-warnings", action="store_true")
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
    print("BAGEL optimization-integrity check passed.")
    return 0


def _GOOD_TARGET():
    return {"optimization_target": {"targets": [
        {"benchmark": "GSM8K", "metric": "accuracy", "goal": "maximize",
         "current_baseline": 0.82, "split_policy": "select_on_val_test_once"}]}}


def _GOOD_LOG():
    return {"optimization_log": {"variants": [
        {"variant_id": "V1", "change": "better prompt", "selection_split": "validation",
         "val_score": 0.84, "kept": True},
        {"variant_id": "V2", "change": "swap retriever", "selection_split": "validation",
         "val_score": 0.80, "kept": False}]}}


def _GOOD_CLAIM():
    return {"claim_evidence_matrix": {"claims": [
        {"claim_id": "C1", "claim_type": "confirmatory", "benchmark": "GSM8K",
         "evaluated_on": "test", "final_score": 0.87, "ablation_ref": "ablation/v1.yaml",
         "statistics": {"correction": "Holm"}}]}}


def _self_test() -> int:
    import copy
    import tempfile

    def run(target, log, claim):
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / ".bagel/research").mkdir(parents=True)
        (root / ".bagel/constitution.yaml").write_text(yaml.safe_dump(
            {"research_autonomy": {"mode": "autonomous_researcher", "objective": "optimization"}}),
            encoding="utf-8")
        (root / ".bagel/state.yaml").write_text(yaml.safe_dump({"run_phase": "iterate"}), encoding="utf-8")
        if target is not None:
            (root / ".bagel/research/optimization-target.yaml").write_text(yaml.safe_dump(target), encoding="utf-8")
        if log is not None:
            (root / ".bagel/research/optimization-log.yaml").write_text(yaml.safe_dump(log), encoding="utf-8")
        if claim is not None:
            (root / ".bagel/research/claim-evidence.yaml").write_text(yaml.safe_dump(claim), encoding="utf-8")
        return validate(root)

    cases = []
    cases.append(("locked target + val-selection + held-out attributed headline -> OK",
                  _GOOD_TARGET(), _GOOD_LOG(), _GOOD_CLAIM(), True))

    cases.append(("gain claimed but no target -> FAIL", None, _GOOD_LOG(), _GOOD_CLAIM(), False))

    t = copy.deepcopy(_GOOD_TARGET()); del t["optimization_target"]["targets"][0]["current_baseline"]
    cases.append(("target without numeric baseline -> FAIL", t, _GOOD_LOG(), _GOOD_CLAIM(), False))

    lg = copy.deepcopy(_GOOD_LOG()); lg["optimization_log"]["variants"][0]["selection_split"] = "test"
    cases.append(("kept variant selected on test -> FAIL", _GOOD_TARGET(), lg, _GOOD_CLAIM(), False))

    cl = copy.deepcopy(_GOOD_CLAIM()); cl["claim_evidence_matrix"]["claims"][0]["evaluated_on"] = "validation"
    cases.append(("headline on validation not test -> FAIL", _GOOD_TARGET(), _GOOD_LOG(), cl, False))

    cl = copy.deepcopy(_GOOD_CLAIM()); cl["claim_evidence_matrix"]["claims"][0]["final_score"] = 0.80
    cases.append(("headline does not beat baseline -> FAIL", _GOOD_TARGET(), _GOOD_LOG(), cl, False))

    cl = copy.deepcopy(_GOOD_CLAIM()); del cl["claim_evidence_matrix"]["claims"][0]["ablation_ref"]
    cases.append(("unattributed gain (no ablation) -> FAIL", _GOOD_TARGET(), _GOOD_LOG(), cl, False))

    cases.append(("gain claimed but empty variant log -> FAIL", _GOOD_TARGET(),
                  {"optimization_log": {"variants": []}}, _GOOD_CLAIM(), False))

    # In-progress: target + variants but no headline yet -> OK (discipline only)
    cases.append(("optimization underway, no headline -> OK", _GOOD_TARGET(), _GOOD_LOG(), None, True))

    passed = 0
    for name, target, log, claim, expect_pass in cases:
        errors, _ = run(target, log, claim)
        ok = (len(errors) == 0) == expect_pass
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  (errors={errors})"))
        passed += int(ok)
    print(f"{passed}/{len(cases)} self-test cases passed.")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
