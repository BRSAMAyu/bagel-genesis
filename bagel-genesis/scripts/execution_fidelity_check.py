#!/usr/bin/env python3
"""Execution-fidelity gate — does the work the run CLAIMS match the artifacts the
designed protocol would have produced? This closes the deepest residual: every
other validator is *skip-if-absent* — it polices the shape of work that was done,
not whether the designed work happened at all. A coding agent that is "not willing"
to engage the machinery (never dispatches the referee, never writes the review
record, never produces statistics) sails through a suite of skip-if-absent checks
because there is nothing to check.

This gate inverts that for the consequential moments: where a CLAIM implies work
that should have left an artifact, the *absence* of that artifact is a failure,
not a skip. It does not (cannot) force an agent to engage mid-run — a validator
only sees state the agent wrote. What it does is make "going through the motions"
fail loudly at turn end (the Stop hook runs the suite), so the gap is visible to
the user instead of hidden behind a green check.

Honest limit: an agent can still refuse to set `run_status: complete` and simply
stop with the work half-done — this gate then shows an incomplete run rather than
a false-complete one, which is the correct outcome, but it cannot compel the agent
to continue. The action-boundary forcing function for engagement lives in
attest_fileop.py (control-plane-first PreToolUse block); full closure is external
(CI auditor + empirical live runs). See enforcement-honesty.md.

Checks (each fires only when its triggering CLAIM/phase is present, and fails on
absent BACKING):

  A. Research completion needs real review+stats. If the run is research-like and
     `run_status: complete`, then claim-evidence.yaml must exist with >=1
     confirmatory/negative_result claim, every confirmatory claim must carry a
     `statistics` block, AND >=1 Research Referee record (.bagel/reviews/REF-*.yaml)
     must exist. A research run cannot be "done" without an evidenced, reviewed claim.

  B. R3/R4 review claims need a real dispatch. Any progress-delta whose
     independent_assessment.review_level is R3/R4 requires
     runtime_capabilities true_subagents.observed=true (+ proof) — you cannot claim
     independent review without an observed real isolated dispatch.

  C. Completed risky runs need a real dispatch. If `run_status: complete`,
     true_subagents.observed=true, and risk_class is medium+, then the run must
     record >=1 dispatched agent (telemetry/registry). A high-risk "complete" run
     with zero dispatches on a subagent-capable platform did the work solo and only
     narrated the topology.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

RESEARCH_SIGNALS = ("research", "experiment", "benchmark", "study", "theory", "analysis")
RISKY = {"medium", "high", "critical"}


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


def true_subagents_observed(root: Path) -> bool:
    data = as_dict(load_yaml(root / ".bagel/runtime_capabilities.yaml", {}))
    caps = as_dict(as_dict(data.get("runtime_capabilities") or data).get("capabilities"))
    rec = as_dict(caps.get("true_subagents"))
    if rec.get("observed") is not True:
        return False
    proof = str(rec.get("proof_ref") or "")
    return bool(proof and (root / proof).exists())


def count_dispatches(root: Path, state: dict) -> int:
    telem = as_dict(state.get("telemetry"))
    n = telem.get("agents_dispatched")
    if isinstance(n, int):
        return n
    registry = as_dict(load_yaml(root / ".bagel/agents/registry.yaml", {}))
    reviews = registry.get("reviews") or registry.get("agents") or registry.get("review_events")
    return len(as_list(reviews))


def referee_records(root: Path) -> list[Path]:
    rdir = root / ".bagel/reviews"
    if not rdir.exists():
        return []
    return sorted(rdir.glob("REF-*.yaml"))


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    run_status = str(state.get("run_status") or state.get("status") or "")
    complete = run_status == "complete"
    research = is_research_like(root, state, constitution)

    # ---- A. Research completion needs real review + stats ------------------
    if complete and research:
        claims_doc = as_dict(load_yaml(root / ".bagel/research/claim-evidence.yaml", {}))
        matrix = as_dict(claims_doc.get("claim_evidence_matrix")) or claims_doc
        claims = [as_dict(c) for c in as_list(matrix.get("claims"))]
        if not claims:
            errors.append(
                "execution_fidelity: research run is complete but "
                ".bagel/research/claim-evidence.yaml has no claims — a finished study "
                "must record its evidenced claims, not just pass governance shape"
            )
        load_bearing = [c for c in claims if c.get("claim_type") in {"confirmatory", "negative_result"}]
        if claims and not load_bearing:
            errors.append(
                "execution_fidelity: research run is complete with claims but none are "
                "confirmatory or negative_result — a study with only exploratory claims "
                "has not concluded anything"
            )
        for c in claims:
            if c.get("claim_type") == "confirmatory" and not as_dict(c.get("statistics")):
                errors.append(
                    f"execution_fidelity: confirmatory claim {c.get('claim_id')!r} at "
                    "completion has no statistics block — the headline was never made "
                    "paper-grade (see statistical_rigor_check)"
                )
        if not referee_records(root):
            errors.append(
                "execution_fidelity: research run is complete but no Research Referee "
                "record (.bagel/reviews/REF-*.yaml) exists — the adversarial validity "
                "review was skipped. Dispatch agents/research-referee.md before completion"
            )
        has_confirmatory_headline = any(
            c.get("claim_type") == "confirmatory"
            or c.get("allowed_in_headline") is True
            or c.get("is_headline") is True
            for c in claims
        )
        if has_confirmatory_headline and not (
            root / ".bagel/research/reproducibility-checklist.yaml"
        ).exists():
            errors.append(
                "execution_fidelity: research run is complete with a confirmatory/headline "
                "claim but .bagel/research/reproducibility-checklist.yaml is missing — the "
                "submission-ready reproducibility checklist was never produced "
                "(see reproducibility_checklist_check)"
            )

    # ---- B. R3/R4 review claims need a real dispatch -----------------------
    deltas_doc = load_yaml(root / ".bagel/evidence/progress-deltas.yaml", {})
    if isinstance(deltas_doc, dict):
        deltas = [as_dict(d) for d in as_list(deltas_doc.get("deltas") or deltas_doc.get("progress_deltas"))]
    else:
        deltas = [as_dict(d) for d in as_list(deltas_doc)]
    observed = true_subagents_observed(root)
    for i, d in enumerate(deltas, start=1):
        level = str(as_dict(d.get("independent_assessment")).get("review_level") or "")
        if level in {"R3", "R4"} and not observed:
            errors.append(
                f"execution_fidelity: cycle {i} claims independent_assessment "
                f"{level} but runtime_capabilities true_subagents.observed is not true "
                "with a proof — an R3/R4 review claim requires a real isolated dispatch, "
                "not a same-session role switch"
            )

    # ---- C. Completed risky runs need a real dispatch ----------------------
    if complete and observed:
        risk = str(state.get("risk_class") or "").lower()
        if risk in RISKY and count_dispatches(root, state) < 1:
            errors.append(
                f"execution_fidelity: run is complete at risk_class={risk!r} on a "
                "subagent-capable platform but records zero dispatched agents — the "
                "designed multi-agent review topology was narrated, not executed"
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
    print("BAGEL execution-fidelity check passed.")
    return 0


def _self_test() -> int:
    import tempfile

    def build(files: dict) -> Path:
        d = tempfile.mkdtemp()
        root = Path(d)
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(yaml.safe_dump(content) if isinstance(content, (dict, list)) else content,
                         encoding="utf-8")
        return root

    proof_caps = {"runtime_capabilities": {"capabilities": {"true_subagents": {
        "observed": True, "proof_ref": ".bagel/evidence/runtime/subagent-proof.yaml"}}}}

    cases = []

    # A1: research complete, no claims -> FAIL
    cases.append(("research complete, no claim-evidence -> FAIL", {
        ".bagel/constitution.yaml": {"research_autonomy": {"mode": "protocol_execution"}},
        ".bagel/state.yaml": {"run_status": "complete"},
        ".bagel/research/.keep": "x",
    }, False))

    # A2: research complete, confirmatory claim w/o statistics, no referee -> FAIL
    cases.append(("research complete, confirmatory w/o stats + no referee -> FAIL", {
        ".bagel/constitution.yaml": {"research_autonomy": {"mode": "protocol_execution"}},
        ".bagel/state.yaml": {"run_status": "complete"},
        ".bagel/research/claim-evidence.yaml": {"claim_evidence_matrix": {"claims": [
            {"claim_id": "C1", "claim_type": "confirmatory"}]}},
    }, False))

    # A3: research complete, confirmatory w/ stats + referee record -> OK
    cases.append(("research complete, stats + referee present -> OK", {
        ".bagel/constitution.yaml": {"research_autonomy": {"mode": "protocol_execution"}},
        ".bagel/state.yaml": {"run_status": "complete"},
        ".bagel/research/claim-evidence.yaml": {"claim_evidence_matrix": {"claims": [
            {"claim_id": "C1", "claim_type": "confirmatory", "statistics": {"n_runs": 5}}]}},
        ".bagel/reviews/REF-1.yaml": {"review": {"review_id": "REF-1", "net_assessment": "forward"}},
        ".bagel/research/reproducibility-checklist.yaml": {"reproducibility_checklist": {"items": {}}},
    }, True))

    # B: R3 claim without observed dispatch -> FAIL
    cases.append(("R3 delta claim without observed dispatch -> FAIL", {
        ".bagel/state.yaml": {"run_status": "iterate"},
        ".bagel/evidence/progress-deltas.yaml": {"deltas": [
            {"net_assessment": "forward", "independent_assessment": {"review_level": "R3"}}]},
    }, False))

    # C: complete high-risk, observed subagents, zero dispatches -> FAIL
    cases.append(("complete high-risk, zero dispatches -> FAIL", {
        ".bagel/state.yaml": {"run_status": "complete", "risk_class": "high",
                              "telemetry": {"agents_dispatched": 0}},
        ".bagel/runtime_capabilities.yaml": proof_caps,
        ".bagel/evidence/runtime/subagent-proof.yaml": {"result": "pass"},
    }, False))

    # Non-research, not complete, no claims -> OK (skip everything)
    cases.append(("non-research pre-complete minimal -> OK", {
        ".bagel/state.yaml": {"run_status": "build"},
    }, True))

    passed = 0
    for name, files, expect_pass in cases:
        root = build(files)
        errors, _ = validate(root)
        ok = (len(errors) == 0) == expect_pass
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  (errors={errors})"))
        passed += int(ok)
    print(f"{passed}/{len(cases)} self-test cases passed.")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
