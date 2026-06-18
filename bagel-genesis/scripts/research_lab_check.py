#!/usr/bin/env python3
"""Validate research-lab automation scaffolding for unattended experiments.

This complements research_governance_check.py. Governance answers "is the
science allowed and preregistered?"; this file answers "can an agent run the
experiment factory without inventing numbers or bothering the researcher?"

The check is intentionally generic, with optional Harness4Testing policy fields.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


TERMINAL_OR_ACTIVE = {"queued", "blocked", "running", "completed", "failed", "frozen"}
RESULT_STATUSES = {"running", "completed", "failed"}
APPROVED_BUILD_REFS = {"human_approved_build_unlock", "approved_detailed_experiment_plan"}
EXECUTION_RE = re.compile(
    r"(^|\s)(python3?|bash|zsh|node|Rscript|julia|perl|ruby)\s+"
    r"|\b(?:sh|bash|zsh)\s+-c\b"
    r"|\bcurl\s+|\bwget\s+|\bmake\s+\S+|\bpytest\b|\bnpm\s+(?:run|test|start)\b"
    r"|\buv\s+run\b|\bclaude\s+-p\b",
    re.I,
)
LLM_SIGNAL_RE = re.compile(
    r"\bclaude\s+-p\b|\bopenai\b|\banthropic\b|\blitellm\b|call_claude|chatgpt|completion|secret_llm",
    re.I,
)
CANONICAL_LLM_ENTRYPOINT = "experiments/tools/claude_call.py"


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if data is None else data


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def walk_strings(value: Any, path: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(".".join(path), value)]
    if isinstance(value, dict):
        out: list[tuple[str, str]] = []
        for key, child in value.items():
            out.extend(walk_strings(child, path + (str(key),)))
        return out
    if isinstance(value, list):
        out: list[tuple[str, str]] = []
        for i, child in enumerate(value):
            out.extend(walk_strings(child, path + (str(i),)))
        return out
    return []


def is_research_like(root: Path) -> bool:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    profile = as_dict(state.get("artifact_profile")).get("type") or constitution.get("artifact_type")
    return profile == "research_experiment" or (root / ".bagel/research").exists()


def build_started(root: Path) -> bool:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    phase = str(state.get("run_phase") or state.get("phase") or "").lower()
    return phase in {"build", "iterate", "polish", "excellence_loop", "complete"}


def build_unlocked(root: Path) -> bool:
    """Build start must be tied to preregistration approval, not phase metadata."""
    if not build_started(root):
        return False
    data = as_dict(load_yaml(root / ".bagel/research/preregistration.yaml", {}))
    prereg = as_dict(data.get("preregistration")) or data
    approval = str(prereg.get("approval_ref") or "")
    if approval not in APPROVED_BUILD_REFS:
        return False
    if not prereg.get("plan_commit") or prereg.get("plan_commit") == "":
        return False
    return True


def validate_policy(root: Path, errors: list[str]) -> dict[str, Any]:
    data = as_dict(load_yaml(root / ".bagel/research/lab-policy.yaml", {}))
    policy = as_dict(data.get("research_lab_policy")) or data
    if not policy:
        errors.append("research_lab_policy: .bagel/research/lab-policy.yaml is required for research automation")
        return {}
    if not policy.get("mode1_protocol_execution_ready"):
        errors.append("research_lab_policy: mode1_protocol_execution_ready must be true before unattended experiment automation")
    chain = as_list(policy.get("required_artifact_chain"))
    required_chain = ["harness_card", "run_command", "trace", "results", "summary", "claims_ledger", "bagel_claim_evidence"]
    missing_chain = [item for item in required_chain if item not in chain]
    for item in missing_chain:
        errors.append(f"research_lab_policy: required_artifact_chain missing {item}")
    if not as_list(policy.get("allowed_llm_entrypoints")):
        errors.append("research_lab_policy: allowed_llm_entrypoints is required")
    if as_list(policy.get("allowed_llm_entrypoints")) != [CANONICAL_LLM_ENTRYPOINT]:
        errors.append(f"research_lab_policy: allowed_llm_entrypoints must be exactly [{CANONICAL_LLM_ENTRYPOINT}]")
    if policy.get("no_experiment_before_build_unlock") is not True:
        errors.append("research_lab_policy: no_experiment_before_build_unlock must be true")
    return policy


def validate_harness_adapter(root: Path, policy: dict[str, Any], errors: list[str]) -> None:
    adapter_data = as_dict(load_yaml(root / ".bagel/research/harness-adapter.yaml", {}))
    adapter = as_dict(adapter_data.get("harness4testing_adapter")) or adapter_data
    if not adapter:
        return
    for path in (
        "docs/research-design.md",
        "docs/verification-protocol.md",
        "docs/claims-ledger.md",
            CANONICAL_LLM_ENTRYPOINT,
    ):
        if not (root / path).exists():
            errors.append(f"harness4testing_adapter: required project file missing: {path}")
    entrypoints = set(str(x) for x in as_list(policy.get("allowed_llm_entrypoints")))
    if entrypoints != {CANONICAL_LLM_ENTRYPOINT}:
        errors.append(f"harness4testing_adapter: {CANONICAL_LLM_ENTRYPOINT} must be the only allowed LLM entrypoint")
    locked = set(str(x) for x in as_list(adapter.get("locked_protocol_elements")))
    for item in ("research_questions", "datasets", "metrics_policy", "llm_entrypoint", "claims_ledger"):
        if item not in locked:
            errors.append(f"harness4testing_adapter: locked_protocol_elements missing {item}")


def validate_run_matrix(root: Path, policy: dict[str, Any], errors: list[str]) -> None:
    data = as_dict(load_yaml(root / ".bagel/research/run-matrix.yaml", {}))
    matrix = as_dict(data.get("research_run_matrix")) or data
    if not matrix:
        errors.append("research_run_matrix: .bagel/research/run-matrix.yaml is required")
        return
    lanes = [as_dict(x) for x in as_list(matrix.get("lanes"))]
    if not lanes:
        errors.append("research_run_matrix: lanes must not be empty")
        return
    seen: set[str] = set()
    pre_build = not build_unlocked(root)
    for i, lane in enumerate(lanes, start=1):
        lane_id = str(lane.get("lane_id") or "")
        if not lane_id:
            errors.append(f"research_run_matrix: lane {i} missing lane_id")
        elif lane_id in seen:
            errors.append(f"research_run_matrix: duplicate lane_id {lane_id}")
        seen.add(lane_id)
        status = str(lane.get("status") or "")
        if status not in TERMINAL_OR_ACTIVE:
            errors.append(f"research_run_matrix: lane {lane_id or i} status must be one of {sorted(TERMINAL_OR_ACTIVE)}")
        if pre_build and status in RESULT_STATUSES:
            errors.append(f"research_run_matrix: lane {lane_id or i} has status {status} before Build unlock")
        if pre_build and lane.get("execution_authorized") not in {False, None}:
            errors.append(f"research_run_matrix: lane {lane_id or i} execution_authorized must be false/null before Build unlock")
        if not lane.get("rq"):
            errors.append(f"research_run_matrix: lane {lane_id or i} missing rq")
        if not lane.get("purpose"):
            errors.append(f"research_run_matrix: lane {lane_id or i} missing purpose")
        string_fields = walk_strings(lane)
        if pre_build:
            for path, text in string_fields:
                if EXECUTION_RE.search(text):
                    errors.append(
                        f"research_run_matrix: lane {lane_id or i} carries executable command-like text "
                        f"before Build unlock at {path}"
                    )
        if status in RESULT_STATUSES:
            for field in ("harness_card", "run_command", "trace_glob", "results_glob", "aggregate_or_verify_command", "claims_ledger_ref"):
                if not lane.get(field):
                    errors.append(f"research_run_matrix: active/result lane {lane_id or i} missing {field}")
            for field in ("harness_card", "claims_ledger_ref"):
                ref = lane.get(field)
                if isinstance(ref, str) and ref and not (root / ref).exists():
                    errors.append(f"research_run_matrix: lane {lane_id or i} {field} does not exist: {ref}")
        llm_entrypoint = str(lane.get("llm_entrypoint") or "")
        if lane.get("llm_required") is True and llm_entrypoint != CANONICAL_LLM_ENTRYPOINT:
            errors.append(f"research_run_matrix: lane {lane_id or i} uses unapproved llm_entrypoint {llm_entrypoint!r}")
        if llm_entrypoint and llm_entrypoint != CANONICAL_LLM_ENTRYPOINT:
            errors.append(f"research_run_matrix: lane {lane_id or i} declares non-canonical llm_entrypoint {llm_entrypoint!r}")
        for path, text in string_fields:
            if path == "llm_entrypoint" and text == CANONICAL_LLM_ENTRYPOINT:
                continue
            if LLM_SIGNAL_RE.search(text) and llm_entrypoint != CANONICAL_LLM_ENTRYPOINT:
                errors.append(
                    f"research_run_matrix: lane {lane_id or i} text at {path} has LLM signals "
                    "but no canonical llm_entrypoint"
                )
            if LLM_SIGNAL_RE.search(text) and path != "llm_entrypoint" and CANONICAL_LLM_ENTRYPOINT not in text:
                errors.append(
                    f"research_run_matrix: lane {lane_id or i} text at {path} references LLM tooling "
                    f"without routing through {CANONICAL_LLM_ENTRYPOINT}"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not is_research_like(root):
        print("research_lab_check: not research-like; skipped")
        return 0
    errors: list[str] = []
    policy = validate_policy(root, errors)
    validate_harness_adapter(root, policy, errors)
    validate_run_matrix(root, policy, errors)
    if errors:
        print("research_lab_check failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("research_lab_check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
