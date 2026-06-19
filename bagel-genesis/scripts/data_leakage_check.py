#!/usr/bin/env python3
"""Data-hygiene / leakage gate for research Mode 1 — the integrity failures that
sink a paper even when the statistics are impeccable. statistical_rigor_check.py
proves the numbers are well-formed; this proves the numbers are not contaminated.

The three classic leakage rejects:

  1. Preprocessing fit on all data. `preprocessing_scope: all_data` means scalers /
     vocabularies / feature selection saw the test set — the reported number is
     optimistic by an unknown amount. For a confirmatory claim this must be audited
     and justified, never silent.
  2. Selecting on the test set. Hyperparameters / model checkpoints chosen by test
     performance turns the "test" number into a training number. Selection must use
     a validation (or train) split, never test.
  3. Outcome-dependent exclusions. Dropping runs/examples *because* they hurt the
     result, decided after seeing outcomes, is p-hacking. Exclusions must be
     preregistered (outcome-independent) or explicitly labeled post-hoc.

Scope: research-like runs, after Build, CONFIRMATORY/headline claims only.

Schema (documented in references/research-governance.md):

    experiment_plan:
      analysis_plan:
        preprocessing_scope: train_only | train_val | all_data
      data_hygiene:
        test_set_policy:
          touch_count: 1                     # times the test set was evaluated
          selection_used: validation         # validation | train  (NEVER test)
          leakage_audited: true              # train/test overlap explicitly checked
          leakage_justification: ""          # REQUIRED if preprocessing_scope == all_data
                                             # or touch_count > 1
        exclusions:
          - criterion: "runs that NaN'd in first 100 steps"
            preregistered: true              # outcome-independent
            posthoc: false

Honest limit: this checks that the run *declares* leakage-free handling and that the
declaration is internally consistent — it cannot read the training data to prove no
overlap exists. It makes silent contamination impossible to pass and forces an
explicit, reviewable audit; the audit itself is the researcher's + referee's job.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

RESEARCH_SIGNALS = ("research", "experiment", "benchmark", "study", "theory", "analysis")


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
    if not is_research_like(root, state, constitution) or not build_started(state, root):
        return errors, warnings

    plan_doc = as_dict(load_yaml(root / ".bagel/research/experiment-plan.yaml", {}))
    plan = as_dict(plan_doc.get("experiment_plan")) or plan_doc
    claims_doc = as_dict(load_yaml(root / ".bagel/research/claim-evidence.yaml", {}))
    matrix = as_dict(claims_doc.get("claim_evidence_matrix")) or claims_doc
    claims = [as_dict(c) for c in as_list(matrix.get("claims"))]
    headline = [
        c for c in claims
        if c.get("claim_type") == "confirmatory"
        or c.get("allowed_in_headline") is True
        or c.get("is_headline") is True
    ]
    if not headline:
        return errors, warnings

    analysis = as_dict(plan.get("analysis_plan"))
    hygiene = as_dict(plan.get("data_hygiene"))
    policy = as_dict(hygiene.get("test_set_policy"))

    if not hygiene or not policy:
        errors.append(
            "data_leakage: a confirmatory/headline claim exists but plan.data_hygiene."
            "test_set_policy is missing — declare touch_count, selection_used, and "
            "leakage_audited before a test-set number can be a headline"
        )
        return errors, warnings

    # 1. Preprocessing scope leakage.
    scope = str(analysis.get("preprocessing_scope") or "")
    if scope == "all_data":
        if policy.get("leakage_audited") is not True or not str(policy.get("leakage_justification") or "").strip():
            errors.append(
                "data_leakage: preprocessing_scope=all_data (preprocessing saw the test "
                "set) requires test_set_policy.leakage_audited=true AND a non-empty "
                "leakage_justification — silent all-data preprocessing is leakage"
            )
    elif scope not in {"train_only", "train_val"}:
        errors.append(
            "data_leakage: analysis_plan.preprocessing_scope must be one of "
            "train_only | train_val | all_data"
        )

    # 2. Selecting on the test set.
    selection = str(policy.get("selection_used") or "").lower()
    if selection == "test":
        errors.append(
            "data_leakage: test_set_policy.selection_used=test — hyperparameter/"
            "checkpoint selection on the test set turns the test number into a "
            "training number; select on a validation split"
        )
    elif selection not in {"validation", "val", "train"}:
        errors.append(
            "data_leakage: test_set_policy.selection_used must be validation/val/train "
            "(never test) — declare the split used for model selection"
        )

    # 3. Test-set touch accounting.
    touch = policy.get("touch_count")
    if not isinstance(touch, int):
        errors.append("data_leakage: test_set_policy.touch_count (int) is required")
    elif touch > 1 and not str(policy.get("leakage_justification") or "").strip():
        errors.append(
            f"data_leakage: test set evaluated {touch} times without a "
            "leakage_justification — repeated test evaluation inflates the result; "
            "justify why this is not test-set tuning"
        )

    # 4. Explicit overlap audit.
    if policy.get("leakage_audited") is not True:
        errors.append(
            "data_leakage: test_set_policy.leakage_audited must be true — explicitly "
            "attest that train/test overlap (and pretraining contamination, for "
            "benchmark claims) was checked"
        )

    # 5. Outcome-dependent exclusions must be preregistered or labeled post-hoc.
    for i, ex in enumerate(as_list(hygiene.get("exclusions")), start=1):
        ex = as_dict(ex)
        if not str(ex.get("criterion") or "").strip():
            errors.append(f"data_leakage: exclusion {i} missing criterion")
            continue
        preregistered = ex.get("preregistered") is True
        posthoc = ex.get("posthoc") is True
        if not preregistered and not posthoc:
            errors.append(
                f"data_leakage: exclusion {i} ({ex.get('criterion')!r}) is neither "
                "preregistered nor labeled posthoc — an outcome-dependent exclusion "
                "decided after seeing results is p-hacking"
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
    print("BAGEL data-leakage check passed.")
    return 0


def _GOOD():
    return {"experiment_plan": {
        "analysis_plan": {"preprocessing_scope": "train_only"},
        "data_hygiene": {
            "test_set_policy": {"touch_count": 1, "selection_used": "validation",
                                "leakage_audited": True},
            "exclusions": [{"criterion": "NaN in first 100 steps", "preregistered": True}],
        }}}


def _self_test() -> int:
    import copy
    import tempfile

    def run(plan):
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / ".bagel/research").mkdir(parents=True)
        (root / ".bagel/constitution.yaml").write_text(
            yaml.safe_dump({"research_autonomy": {"mode": "protocol_execution"}}), encoding="utf-8")
        (root / ".bagel/state.yaml").write_text(
            yaml.safe_dump({"run_phase": "iterate"}), encoding="utf-8")
        (root / ".bagel/research/experiment-plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
        (root / ".bagel/research/claim-evidence.yaml").write_text(
            yaml.safe_dump({"claim_evidence_matrix": {"claims": [
                {"claim_id": "C1", "claim_type": "confirmatory"}]}}), encoding="utf-8")
        return validate(root)

    cases = []
    cases.append(("clean train_only + audited + 1 touch -> OK", _GOOD(), True))

    p = copy.deepcopy(_GOOD()); p["experiment_plan"]["analysis_plan"]["preprocessing_scope"] = "all_data"
    cases.append(("all_data without justification -> FAIL", p, False))

    p = copy.deepcopy(_GOOD())
    p["experiment_plan"]["analysis_plan"]["preprocessing_scope"] = "all_data"
    p["experiment_plan"]["data_hygiene"]["test_set_policy"]["leakage_justification"] = "fit on train fold only within CV"
    cases.append(("all_data WITH audit+justification -> OK", p, True))

    p = copy.deepcopy(_GOOD()); p["experiment_plan"]["data_hygiene"]["test_set_policy"]["selection_used"] = "test"
    cases.append(("selecting on test -> FAIL", p, False))

    p = copy.deepcopy(_GOOD()); p["experiment_plan"]["data_hygiene"]["test_set_policy"]["touch_count"] = 7
    cases.append(("7 test touches w/o justification -> FAIL", p, False))

    p = copy.deepcopy(_GOOD()); p["experiment_plan"]["data_hygiene"]["test_set_policy"]["leakage_audited"] = False
    cases.append(("no overlap audit -> FAIL", p, False))

    p = copy.deepcopy(_GOOD())
    p["experiment_plan"]["data_hygiene"]["exclusions"] = [{"criterion": "dropped low scorers", "preregistered": False, "posthoc": False}]
    cases.append(("outcome-dependent exclusion, unlabeled -> FAIL", p, False))

    p = copy.deepcopy(_GOOD()); del p["experiment_plan"]["data_hygiene"]
    cases.append(("no data_hygiene block at all -> FAIL", p, False))

    passed = 0
    for name, plan, expect_pass in cases:
        errors, _ = run(plan)
        ok = (len(errors) == 0) == expect_pass
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  (errors={errors})"))
        passed += int(ok)
    print(f"{passed}/{len(cases)} self-test cases passed.")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
