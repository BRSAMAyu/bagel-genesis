#!/usr/bin/env python3
"""Validate V3.1 executable expert strategy artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_EXPERT_FILES = {
    ".bagel/expert/domain-excellence.yaml": (
        "what_excellent_means",
        "top_1_percent_work",
        "common_failure_modes",
        "hidden_quality_dimensions",
    ),
    ".bagel/expert/problem-framing.yaml": (
        "user_stated_problem",
        "inferred_real_problem",
        "possible_reframings",
        "chosen_framing",
        "rejected_framings",
    ),
    ".bagel/expert/leverage-map.yaml": ("bottlenecks", "top_leverage_action"),
}
REQUIRED_COUNCIL = {"Domain Expert", "Evaluation Skeptic", "User Proxy"}
CONDITIONAL_COUNCIL = {
    "high_risk": "Risk Officer",
    "architecture": "Systems Architect",
    "breakthrough": "Innovation Strategist",
}
GENERIC_TERMS = {"robust", "scalable", "user-friendly", "polished", "high quality", "excellent", "good", "fast"}
EXPERT_DECISION_TYPES = {
    "framing",
    "iteration_target",
    "major_route",
    "breakthrough_probe",
    "strategy_switch",
    "bar_raise",
    "final_delivery",
    "identity_or_scope_change",
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


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def collect_dispatches(root: Path, state: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key in ("agent_dispatches", "dispatches", "agents"):
        records.extend(as_dict(item) for item in as_list(state.get(key)))
    reg = load_yaml(root / ".bagel/agents/registry.yaml", {})
    if isinstance(reg, dict):
        for key in ("agent_dispatches", "dispatches", "agents", "council_dispatches"):
            records.extend(as_dict(item) for item in as_list(reg.get(key)))
    dispatch_dir = root / ".bagel/agents/dispatches"
    if dispatch_dir.exists():
        for path in sorted(dispatch_dir.glob("*.yaml")):
            rec = as_dict(load_yaml(path, {}))
            if rec:
                rec.setdefault("_path", str(path.relative_to(root)))
                records.append(rec)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for rec in records:
        agent_id = str(rec.get("agent_id") or rec.get("id") or "")
        session_id = str(rec.get("session_id") or "")
        if agent_id:
            out[(agent_id, session_id)] = rec
            out[(agent_id, "")] = rec
    return out


def run_started(state: dict[str, Any]) -> bool:
    return state.get("phase") in {"Build", "Iterate", "Polish", "excellence_loop", "complete"} or bool(state.get("task_queue"))


def expert_mode(state: dict[str, Any]) -> str:
    mode = state.get("expert_layer_mode") or as_dict(state.get("bagel_worth_it_check")).get("expert_layer_mode")
    return str(mode or "standard")


def validate_domain_model(root: Path, data: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    if not data:
        return
    if not data.get("constitution_hash"):
        warnings.append(".bagel/expert/domain-excellence.yaml: missing constitution_hash")
    if not data.get("artifact_profile_hash"):
        warnings.append(".bagel/expert/domain-excellence.yaml: missing artifact_profile_hash")
    source_basis = as_list(data.get("source_basis"))
    if not source_basis:
        errors.append(".bagel/expert/domain-excellence.yaml: missing source_basis")
    for i, trait in enumerate(as_list(data.get("what_excellent_means")), start=1):
        row = as_dict(trait)
        text = str(row.get("trait") or "").strip().lower()
        required = ("observable_signal", "why_it_matters", "weak_version", "strong_version", "evidence_or_probe")
        for field in required:
            if not row.get(field):
                errors.append(f"domain excellence trait {i}: missing {field}")
        if text in GENERIC_TERMS and not all(row.get(field) for field in required):
            errors.append(f"domain excellence trait {i}: generic adjective without observable weak/strong evidence")


def validate_council_participants(
    root: Path,
    participants: list[Any],
    dispatches: dict[tuple[str, str], dict[str, Any]],
    errors: list[str],
    *,
    decision_type: str,
    risk_level: str,
) -> None:
    rows = [as_dict(p) for p in participants]
    roles = {str(p.get("role") or "") for p in rows}
    required = set(REQUIRED_COUNCIL)
    if risk_level in {"high", "critical"}:
        required.add(CONDITIONAL_COUNCIL["high_risk"])
    if decision_type in {"major_route", "identity_or_scope_change"}:
        required.add(CONDITIONAL_COUNCIL["architecture"])
    if decision_type == "breakthrough_probe":
        required.add(CONDITIONAL_COUNCIL["breakthrough"])
    if not required <= roles:
        errors.append(f"expert council participants missing required roles: {sorted(required - roles)}")
    for p in rows:
        role = str(p.get("role") or "")
        agent_id = str(p.get("agent_id") or "")
        session_id = str(p.get("session_id") or "")
        output_ref = p.get("output_ref")
        if not agent_id or not session_id:
            errors.append(f"participant {role or '<unknown>'}: agent_id and session_id are required")
            continue
        dispatch = dispatches.get((agent_id, session_id)) or dispatches.get((agent_id, ""))
        if not dispatch:
            errors.append(f"participant {role}: no matching dispatch registry record for {agent_id}/{session_id}")
        else:
            dispatch_role = str(dispatch.get("role") or dispatch.get("agent_role") or "")
            if dispatch_role != role:
                errors.append(f"participant {agent_id}: role {role!r} does not match dispatch role {dispatch_role!r}")
        if not output_ref or not (root / str(output_ref)).exists():
            errors.append(f"participant {role}: output_ref missing or does not exist")
        else:
            validate_council_output(root, path_ref, p, errors)


def validate_council_output(
    root: Path,
    source_path: Path,
    participant: dict[str, Any],
    errors: list[str],
) -> None:
    """P0-1: parse and validate the *content* of a councilor output_ref, not just its existence.

    A file that exists but is empty or holds only template fields is not a real verdict.
    """
    role = str(participant.get("role") or "<unknown>")
    agent_id = str(participant.get("agent_id") or "")
    session_id = str(participant.get("session_id") or "")
    output_ref = participant.get("output_ref")
    out_path = root / str(output_ref)
    data = load_yaml(out_path, None)
    if data is None:
        errors.append(f"{source_path}: participant {role} output_ref is empty: {output_ref}")
        return
    verdict = as_dict(as_dict(data).get("expert_council_verdict")) or as_dict(data.get("expert_council_verdict"))
    if not verdict:
        errors.append(f"{source_path}: participant {role} output_ref missing expert_council_verdict")
        return
    LEGAL = {"support", "reject", "needs_probe", "outside_authority"}
    perspective = str(verdict.get("perspective") or "")
    v_agent = str(verdict.get("agent_id") or "")
    v_session = str(verdict.get("session_id") or "")
    verdict_value = str(verdict.get("verdict") or "")
    key_reason = str(verdict.get("key_reason") or "")
    evidence_refs = as_list(verdict.get("evidence_refs"))
    missing_evidence = as_list(verdict.get("missing_evidence"))
    # perspective must match role
    if perspective and perspective != role:
        errors.append(f"{source_path}: participant {role} verdict.perspective {perspective!r} != role")
    # agent_id/session_id must match participant
    if v_agent and v_agent != agent_id:
        errors.append(f"{source_path}: participant {role} verdict.agent_id {v_agent!r} != participant {agent_id!r}")
    if v_session and v_session != session_id:
        errors.append(f"{source_path}: participant {role} verdict.session_id {v_session!r} != participant {session_id!r}")
    # verdict must be a legal enum
    if verdict_value not in LEGAL:
        errors.append(f"{source_path}: participant {role} verdict must be one of {sorted(LEGAL)}; got {verdict_value!r}")
    # key_reason must be non-empty and meaningfully long (>=30 chars)
    if len(key_reason.strip()) < 30:
        errors.append(f"{source_path}: participant {role} verdict.key_reason must be non-empty and >=30 chars")
    # verdict-specific evidence requirements
    if verdict_value == "support" and not evidence_refs:
        errors.append(f"{source_path}: participant {role} support verdict requires evidence_refs")
    if verdict_value == "reject" and not evidence_refs and not missing_evidence:
        errors.append(f"{source_path}: participant {role} reject verdict requires evidence_refs or missing_evidence")
    if verdict_value == "needs_probe" and not missing_evidence:
        errors.append(f"{source_path}: participant {role} needs_probe verdict requires missing_evidence")
    if verdict_value == "outside_authority":
        if not missing_evidence and not key_reason:
            errors.append(f"{source_path}: participant {role} outside_authority verdict must explain the authority boundary")
    # detect template-only / placeholder content
    if key_reason.strip() in {"", '""', "''"} or key_reason.strip().lower() in {"todo", "tbd", "placeholder", "n/a"}:
        errors.append(f"{source_path}: participant {role} verdict.key_reason is a placeholder, not a real verdict")


def validate_expert_decision(
    root: Path,
    path: Path,
    record: dict[str, Any],
    dispatches: dict[tuple[str, str], dict[str, Any]],
    errors: list[str],
) -> None:
    decision = as_dict(record.get("expert_decision")) or record
    if decision.get("schema_version") != "expert_decision_v1":
        errors.append(f"{path}: expert_decision.schema_version must be expert_decision_v1")
    required = (
        "decision_id",
        "decision_type",
        "decision_owner",
        "options_considered",
        "selected_option_id",
        "selected_direction",
        "expert_thesis",
        "why_this_now",
        "rejected_alternatives",
        "participants",
        "domain_model_ref",
        "problem_framing_ref",
        "leverage_map_ref",
        "evaluation_critic_ref",
        "roi_ref",
        "confidence",
        "reversibility",
        "decisive_evidence",
        "biggest_uncertainty",
        "kill_criteria",
        "next_probe_or_action",
    )
    for field in required:
        if not decision.get(field):
            errors.append(f"{path}: expert_decision missing {field}")
    if decision.get("decision_type") and decision.get("decision_type") not in EXPERT_DECISION_TYPES:
        errors.append(f"{path}: invalid decision_type {decision.get('decision_type')!r}")
    owner = as_dict(decision.get("decision_owner"))
    if owner.get("role") != "Principal Expert" or not owner.get("agent_id") or not owner.get("session_id"):
        errors.append(f"{path}: decision_owner must be Principal Expert with agent_id/session_id")
    else:
        # P0-2: owner must correspond to a real dispatch registry record (not just fields existing)
        o_agent = str(owner.get("agent_id"))
        o_session = str(owner.get("session_id"))
        owner_dispatch = dispatches.get((o_agent, o_session)) or dispatches.get((o_agent, ""))
        if not owner_dispatch:
            errors.append(f"{path}: decision_owner {o_agent}/{o_session} has no matching dispatch registry record")
        else:
            dispatch_role = str(owner_dispatch.get("role") or owner_dispatch.get("agent_role") or "")
            if dispatch_role != "Principal Expert":
                errors.append(f"{path}: decision_owner dispatch role {dispatch_role!r} != Principal Expert")
    for ref_field in ("domain_model_ref", "problem_framing_ref", "leverage_map_ref", "evaluation_critic_ref", "roi_ref"):
        ref = decision.get(ref_field)
        if ref and not (root / str(ref)).exists():
            errors.append(f"{path}: {ref_field} does not exist: {ref}")
    validate_council_participants(
        root,
        as_list(decision.get("participants")),
        dispatches,
        errors,
        decision_type=str(decision.get("decision_type") or ""),
        risk_level=str(decision.get("risk_level") or "medium"),
    )
    # P0-3: derived risk checks — do not trust self-report alone
    risk_level = str(decision.get("risk_level") or "medium")
    risk_basis = as_dict(decision.get("risk_basis"))
    affected = {str(s) for s in as_list(risk_basis.get("affected_surfaces"))}
    SENSITIVE_SURFACES = {"auth", "privacy", "payment", "production_data", "user_identity", "legal", "financial"}
    reversibility = str(decision.get("reversibility") or "")
    decision_type = str(decision.get("decision_type") or "")
    # sensitive surface touched -> risk must be high/critical
    if affected & SENSITIVE_SURFACES and risk_level not in {"high", "critical"}:
        errors.append(f"{path}: risk_basis.affected_surfaces touches sensitive surface {sorted(affected & SENSITIVE_SURFACES)} but risk_level={risk_level!r} (must be high/critical)")
    # costly/irreversible -> risk cannot be low
    if reversibility in {"costly", "irreversible"} and risk_level == "low":
        errors.append(f"{path}: reversibility={reversibility!r} but risk_level=low (must be at least medium)")
    # identity/scope change -> requires Systems Architect + Risk Officer (council_participants already enforces via decision_type, double-check risk_level)
    if decision_type == "identity_or_scope_change" and risk_level not in {"high", "critical"}:
        errors.append(f"{path}: identity_or_scope_change decision must have risk_level high/critical")
    if not as_list(decision.get("rejected_alternatives")):
        errors.append(f"{path}: expert_decision requires rejected_alternatives")
    for i, item in enumerate(as_list(decision.get("rejected_alternatives")), start=1):
        row = as_dict(item)
        if not row.get("option_id") or not row.get("why_rejected") or not row.get("decisive_evidence_or_assumption"):
            errors.append(f"{path}: rejected_alternative {i} requires option_id, why_rejected, decisive_evidence_or_assumption")
    for i, item in enumerate(as_list(decision.get("kill_criteria")), start=1):
        row = as_dict(item)
        if not row.get("criterion") or not row.get("check_method") or not row.get("action_if_triggered"):
            errors.append(f"{path}: kill_criteria {i} requires criterion, check_method, action_if_triggered")
    if decision.get("reversibility") in {"costly", "irreversible"} and not decision.get("authority_ref"):
        errors.append(f"{path}: costly/irreversible direction requires authority_ref")
    council_result = as_dict(decision.get("council_result"))
    if council_result.get("status") in {"vetoed", "disputed", "deadlocked"} and not decision.get("new_decisive_evidence_ref"):
        errors.append(f"{path}: cannot override {council_result.get('status')} council without new_decisive_evidence_ref")


def validate_breakthrough(root: Path, state: dict[str, Any], errors: list[str]) -> None:
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    innovation = as_dict(state.get("innovation_contract")) or as_dict(constitution.get("innovation_contract"))
    ambition = innovation.get("ambition")
    path = root / ".bagel/expert/breakthrough-search.yaml"
    data = as_dict(load_yaml(path, {}))
    if ambition == "breakthrough" and not data:
        errors.append("innovation_contract.ambition=breakthrough requires .bagel/expert/breakthrough-search.yaml")
        return
    if not data:
        return
    search = as_dict(data.get("breakthrough_search")) or data
    if len(as_list(search.get("operators_used"))) < 3:
        errors.append("breakthrough_search.operators_used requires >=3 operators")
    if len(as_list(search.get("competing_theses"))) < 3:
        errors.append("breakthrough_search.competing_theses requires >=3 theses")
    for i, raw in enumerate(as_list(search.get("candidates")), start=1):
        c = as_dict(raw)
        for field in (
            "what_assumption_it_breaks",
            "why_existing_solution_space_misses_it",
            "why_it_could_be_10x_better",
            "cheapest_falsifiable_probe",
            "risk_if_wrong",
            "evidence_needed_to_adopt",
            "adoption_threshold",
            "rejection_threshold",
        ):
            if not c.get(field):
                errors.append(f"breakthrough candidate {i}: missing {field}")
        quality = as_dict(c.get("breakthrough_quality"))
        true_count = sum(1 for value in quality.values() if value is True)
        if true_count < 2:
            errors.append(f"breakthrough candidate {i}: breakthrough_quality needs at least 2 true properties")


def validate(root: Path) -> tuple[list[str], list[str]]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    mode = expert_mode(state)
    errors: list[str] = []
    warnings: list[str] = []
    if not run_started(state):
        return errors, warnings
    if mode in {"off", "lite"}:
        # Lite still needs a non-generic domain note when present, but does not
        # require the full council/Principal Expert ritual for quick runs.
        domain = as_dict(load_yaml(root / ".bagel/expert/domain-excellence.yaml", {}))
        validate_domain_model(root, domain, errors, warnings)
        validate_breakthrough(root, state, errors)
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
        if rel.endswith("domain-excellence.yaml"):
            validate_domain_model(root, data, errors, warnings)

    dispatches = collect_dispatches(root, state)
    decisions: list[tuple[Path, dict[str, Any]]] = []
    decisions_dir = root / ".bagel/expert/strategy-decisions"
    if decisions_dir.exists():
        for path in sorted(decisions_dir.glob("*.yaml")):
            decisions.append((path, as_dict(load_yaml(path, {}))))
    for item in as_list(state.get("strategy_decisions")):
        decisions.append((root / ".bagel/state.yaml#strategy_decisions", as_dict(item)))
    if not decisions:
        errors.append("Build/Iterate work requires at least one expert_decision_v1 strategy decision")
    for path, record in decisions:
        validate_expert_decision(root, path, record, dispatches, errors)
    validate_breakthrough(root, state, errors)
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
