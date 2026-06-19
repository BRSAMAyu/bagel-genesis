#!/usr/bin/env python3
"""Reproducibility-checklist gate for research Mode 1 — the submission-ready,
NeurIPS/ICML-style structured checklist that a venue forces every author to
complete, plus the cross-checks that make a "yes" answer mean something.

statistical_rigor_check proves the headline numbers are well-formed; data_leakage
proves they are uncontaminated; this proves the *paper around them is complete and
honest* — every reproducibility item is answered (no blanks), and every "yes" that
maps to a mechanical artifact is cross-checked against that artifact so a checked
box cannot lie.

The checklist (`.bagel/research/reproducibility-checklist.yaml`):

    reproducibility_checklist:
      items:
        code_released:        {answer: yes|no|na, evidence_ref: "..."}   # repo/path or planned-release note
        datasets_documented:  {answer: yes, evidence_ref: "experiment-plan.yaml#datasets"}
        seeds_reported:       {answer: yes, evidence_ref: "..."}
        hyperparameters_reported: {answer: yes, evidence_ref: "configs/"}
        compute_reported:     {answer: yes, evidence_ref: "..."}
        error_bars_reported:  {answer: yes, evidence_ref: "..."}
        significance_reported: {answer: yes, evidence_ref: "..."}
        train_test_split_documented: {answer: yes, evidence_ref: "..."}
        limitations_section:  {answer: yes, evidence_ref: "..."}
        broader_impacts:      {answer: yes|na, evidence_ref: "..."}
        assets_licensed:      {answer: yes|na, evidence_ref: "..."}

Rules (research-like, after Build, when a confirmatory/headline claim exists):
  * The checklist file must exist and answer EVERY required item (no blanks).
  * answer must be one of yes|no|na; a "yes" with no evidence_ref is an empty box.
  * "no" on a hard-required reproducibility item (seeds, compute, error bars,
    significance, train/test split, limitations) fails — these are not optional
    for a confirmatory headline.
  * MECHANICAL CROSS-CHECKS — a "yes" must be backed by the artifact it claims:
      - seeds_reported=yes        => analysis_plan.seeds has >=3 entries
      - compute_reported=yes      => plan.compute_budget has accelerator+total_runs
      - error_bars_reported=yes   => every confirmatory claim has statistics.dispersion
      - significance_reported=yes => every comparative confirmatory claim has p_value
      - train_test_split_documented=yes => plan.data_hygiene.test_set_policy exists
    A box checked "yes" whose backing artifact is missing is a false attestation and
    fails — this is the whole point: the checklist cannot be greener than the work.

Honest limit: items with no mechanical artifact (limitations text quality, broader
impacts depth, license correctness) are checked for *presence of an answer + ref*,
not for substance — that judgment is the Research Referee's. This gate guarantees
the checklist is complete and its mechanical claims are true; it does not grade prose.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

RESEARCH_SIGNALS = ("research", "experiment", "benchmark", "study", "theory", "analysis")

VALID_ANSWERS = {"yes", "no", "na", "n/a"}

# Items every confirmatory-headline research run must answer.
REQUIRED_ITEMS = [
    "code_released",
    "datasets_documented",
    "seeds_reported",
    "hyperparameters_reported",
    "compute_reported",
    "error_bars_reported",
    "significance_reported",
    "train_test_split_documented",
    "limitations_section",
    "broader_impacts",
    "assets_licensed",
]

# Items where "no" is not acceptable for a confirmatory headline (na still allowed
# only where it genuinely doesn't apply — but these all apply to an empirical claim).
HARD_REQUIRED_YES = {
    "seeds_reported",
    "compute_reported",
    "error_bars_reported",
    "significance_reported",
    "train_test_split_documented",
    "limitations_section",
}


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


def _answer(item: Any) -> str:
    # YAML 1.1 coerces unquoted yes/no into booleans, so an agent writing the
    # NeurIPS-convention `answer: yes` lands here as Python True (and `no` as False,
    # which is also falsy — `False or ""` would wrongly blank it). Map booleans back
    # to the canonical strings so correct work is not rejected on a YAML technicality.
    raw = as_dict(item).get("answer")
    if raw is True:
        return "yes"
    if raw is False:
        return "no"
    return str(raw or "").strip().lower()


def _ref(item: Any) -> str:
    return str(as_dict(item).get("evidence_ref") or "").strip()


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
    confirmatory = [c for c in claims if c.get("claim_type") == "confirmatory"]
    headline = [
        c for c in claims
        if c.get("claim_type") == "confirmatory"
        or c.get("allowed_in_headline") is True
        or c.get("is_headline") is True
    ]
    if not headline:
        return errors, warnings

    checklist_doc = as_dict(load_yaml(root / ".bagel/research/reproducibility-checklist.yaml", {}))
    checklist = as_dict(checklist_doc.get("reproducibility_checklist")) or checklist_doc
    items = as_dict(checklist.get("items"))
    if not items:
        errors.append(
            "reproducibility_checklist: a confirmatory/headline claim exists but "
            ".bagel/research/reproducibility-checklist.yaml is missing or has no items — "
            "produce the NeurIPS-style checklist before the result is submission-grade"
        )
        return errors, warnings

    # 1. Completeness + well-formed answers.
    for key in REQUIRED_ITEMS:
        if key not in items:
            errors.append(f"reproducibility_checklist: required item {key!r} is unanswered (missing)")
            continue
        ans = _answer(items[key])
        if ans not in VALID_ANSWERS:
            errors.append(
                f"reproducibility_checklist: item {key!r} answer must be yes|no|na (got {ans!r})"
            )
            continue
        if ans == "yes" and not _ref(items[key]):
            errors.append(
                f"reproducibility_checklist: item {key!r}=yes has no evidence_ref — "
                "a checked box with no pointer is an empty box"
            )
        if key in HARD_REQUIRED_YES and ans in {"no", "na", "n/a"}:
            errors.append(
                f"reproducibility_checklist: item {key!r} is {ans!r} — this is mandatory "
                "for a confirmatory headline (seeds, compute, error bars, significance, "
                "train/test split, limitations are not optional)"
            )

    # 2. Mechanical cross-checks — a "yes" must match the real artifact.
    analysis = as_dict(plan.get("analysis_plan"))
    if _answer(items.get("seeds_reported")) == "yes":
        seeds = as_list(analysis.get("seeds"))
        if len(seeds) < 3:
            errors.append(
                "reproducibility_checklist: seeds_reported=yes but "
                f"analysis_plan.seeds has {len(seeds)} (<3) — the box is greener than the work"
            )

    if _answer(items.get("compute_reported")) == "yes":
        budget = as_dict(plan.get("compute_budget"))
        if not budget.get("accelerator") or budget.get("total_runs") is None:
            errors.append(
                "reproducibility_checklist: compute_reported=yes but plan.compute_budget "
                "lacks accelerator/total_runs — checked box with no backing artifact"
            )

    if _answer(items.get("error_bars_reported")) == "yes":
        for c in confirmatory:
            stats = as_dict(c.get("statistics"))
            if stats.get("dispersion_value") is None and not stats.get("dispersion_type"):
                errors.append(
                    f"reproducibility_checklist: error_bars_reported=yes but confirmatory "
                    f"claim {c.get('claim_id')!r} has no dispersion in its statistics block"
                )
                break

    if _answer(items.get("significance_reported")) == "yes":
        for c in confirmatory:
            stats = as_dict(c.get("statistics"))
            if c.get("comparison") or stats.get("test"):
                if stats.get("p_value") is None:
                    errors.append(
                        "reproducibility_checklist: significance_reported=yes but "
                        f"comparative claim {c.get('claim_id')!r} has no p_value"
                    )
                    break

    if _answer(items.get("train_test_split_documented")) == "yes":
        policy = as_dict(as_dict(plan.get("data_hygiene")).get("test_set_policy"))
        if not policy:
            errors.append(
                "reproducibility_checklist: train_test_split_documented=yes but "
                "plan.data_hygiene.test_set_policy is absent (see data_leakage_check)"
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
    print("BAGEL reproducibility-checklist check passed.")
    return 0


def _GOOD_PLAN():
    return {"experiment_plan": {
        "analysis_plan": {"seeds": [1, 2, 3], "preprocessing_scope": "train_only"},
        "compute_budget": {"accelerator": "A100", "total_runs": 12},
        "data_hygiene": {"test_set_policy": {"touch_count": 1, "selection_used": "validation",
                                             "leakage_audited": True}},
    }}


def _GOOD_CLAIM():
    return {"claim_evidence_matrix": {"claims": [{
        "claim_id": "C1", "claim_type": "confirmatory", "comparison": True,
        "statistics": {"dispersion_type": "ci95", "dispersion_value": 0.4,
                       "test": "paired_t", "p_value": 0.003}}]}}


def _GOOD_CHECKLIST():
    yes = lambda ref: {"answer": "yes", "evidence_ref": ref}  # noqa: E731
    return {"reproducibility_checklist": {"items": {
        "code_released": yes("repo/"),
        "datasets_documented": yes("plan#datasets"),
        "seeds_reported": yes("plan#seeds"),
        "hyperparameters_reported": yes("configs/"),
        "compute_reported": yes("plan#compute"),
        "error_bars_reported": yes("claims#stats"),
        "significance_reported": yes("claims#stats"),
        "train_test_split_documented": yes("plan#hygiene"),
        "limitations_section": yes("paper#limits"),
        "broader_impacts": {"answer": "na", "evidence_ref": ""},
        "assets_licensed": {"answer": "na", "evidence_ref": ""},
    }}}


def _self_test() -> int:
    import copy
    import tempfile

    def run(plan, claim, checklist):
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / ".bagel/research").mkdir(parents=True)
        (root / ".bagel/constitution.yaml").write_text(
            yaml.safe_dump({"research_autonomy": {"mode": "protocol_execution"}}), encoding="utf-8")
        (root / ".bagel/state.yaml").write_text(yaml.safe_dump({"run_phase": "iterate"}), encoding="utf-8")
        (root / ".bagel/research/experiment-plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
        (root / ".bagel/research/claim-evidence.yaml").write_text(yaml.safe_dump(claim), encoding="utf-8")
        if checklist is not None:
            (root / ".bagel/research/reproducibility-checklist.yaml").write_text(
                yaml.safe_dump(checklist), encoding="utf-8")
        return validate(root)

    cases = []
    cases.append(("complete + cross-checks satisfied -> OK", _GOOD_PLAN(), _GOOD_CLAIM(), _GOOD_CHECKLIST(), True))

    cases.append(("no checklist file -> FAIL", _GOOD_PLAN(), _GOOD_CLAIM(), None, False))

    ck = copy.deepcopy(_GOOD_CHECKLIST()); del ck["reproducibility_checklist"]["items"]["seeds_reported"]
    cases.append(("missing required item -> FAIL", _GOOD_PLAN(), _GOOD_CLAIM(), ck, False))

    ck = copy.deepcopy(_GOOD_CHECKLIST()); ck["reproducibility_checklist"]["items"]["compute_reported"] = {"answer": "yes", "evidence_ref": ""}
    cases.append(("yes with no evidence_ref -> FAIL", _GOOD_PLAN(), _GOOD_CLAIM(), ck, False))

    ck = copy.deepcopy(_GOOD_CHECKLIST()); ck["reproducibility_checklist"]["items"]["error_bars_reported"] = {"answer": "no", "evidence_ref": ""}
    cases.append(("hard-required item = no -> FAIL", _GOOD_PLAN(), _GOOD_CLAIM(), ck, False))

    # seeds_reported=yes but plan has <3 seeds -> cross-check FAIL
    p = copy.deepcopy(_GOOD_PLAN()); p["experiment_plan"]["analysis_plan"]["seeds"] = [1]
    cases.append(("seeds box yes but <3 seeds -> FAIL", p, _GOOD_CLAIM(), _GOOD_CHECKLIST(), False))

    # compute_reported=yes but no compute_budget -> cross-check FAIL
    p = copy.deepcopy(_GOOD_PLAN()); del p["experiment_plan"]["compute_budget"]
    cases.append(("compute box yes but no budget -> FAIL", p, _GOOD_CLAIM(), _GOOD_CHECKLIST(), False))

    # significance_reported=yes but claim missing p_value -> cross-check FAIL
    cl = copy.deepcopy(_GOOD_CLAIM()); del cl["claim_evidence_matrix"]["claims"][0]["statistics"]["p_value"]
    cases.append(("significance box yes but no p_value -> FAIL", _GOOD_PLAN(), cl, _GOOD_CHECKLIST(), False))

    # YAML 1.1 coerces unquoted yes/no into booleans: `answer: yes` -> True, `no` -> False.
    # An agent writing the natural NeurIPS-convention checklist must still pass.
    ck = copy.deepcopy(_GOOD_CHECKLIST())
    for k, v in ck["reproducibility_checklist"]["items"].items():
        if v.get("answer") == "yes":
            v["answer"] = True   # what safe_load produces for unquoted `answer: yes`
    cases.append(("YAML-boolean yes (unquoted) accepted -> OK", _GOOD_PLAN(), _GOOD_CLAIM(), ck, True))

    # And a YAML-boolean False must be read as "no" (not silently blanked by `False or ''`),
    # so a hard-required item written as unquoted `no` is still caught.
    ck = copy.deepcopy(_GOOD_CHECKLIST())
    ck["reproducibility_checklist"]["items"]["error_bars_reported"] = {"answer": False, "evidence_ref": ""}
    cases.append(("YAML-boolean no on hard-required item -> FAIL", _GOOD_PLAN(), _GOOD_CLAIM(), ck, False))

    passed = 0
    for name, plan, claim, checklist, expect_pass in cases:
        errors, _ = run(plan, claim, checklist)
        ok = (len(errors) == 0) == expect_pass
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  (errors={errors})"))
        passed += int(ok)
    print(f"{passed}/{len(cases)} self-test cases passed.")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
