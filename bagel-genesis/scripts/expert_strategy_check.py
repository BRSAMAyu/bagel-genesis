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
    source_path: Path | None = None,
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
            validate_council_output(root, source_path or Path("council"), p, errors)


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
        source_path=path,
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


# Contradiction families for requirement_coherence_checked (S2 scenario gate).
# PRIMARY: structured declared axes (paraphrase-proof). FALLBACK: signal substring
# matching for runs that have not yet declared structured requirement axes.
#
# The structured path is authoritative: the agent must tag each requirement with a
# {requirement_axis, strength} pair from a fixed enum below. A contradiction is matched
# when two requirements carry conflicting axis strengths (e.g. consistency=strong AND
# partition_tolerance=required). This cannot be paraphrased away — the axis is declared,
# not inferred from free text. The signal-substring path is a fallback for pre-structured
# runs only and is explicitly weaker (a synonym can evade it).

# Fixed enum of requirement axes. An axis maps to a contradiction family when two
# requirements demand incompatible axis strengths.
_REQUIREMENT_AXES = {
    "consistency": {"strong", "eventual", "none"},
    "availability": {"high", "best_effort"},
    "partition_tolerance": {"required", "not_required"},
    "latency": {"hard_realtime", "soft", "unbounded"},
    "offline_window": {"bounded", "unbounded", "none"},
    "merge_model": {"automatic", "manual", "none"},
    "cost": {"zero_infra", "budgeted", "enterprise"},
    "capability": {"minimal", "standard", "enterprise"},
}

# Axis pairs that conflict (contradiction families). If req A demands the left strength
# and req B demands the right strength for the same pair, the set is jointly unsatisfiable.
_AXIS_CONFLICTS = {
    "cap_consistency_vs_availability": (
        ("consistency", "strong"), ("availability", "high"), ("partition_tolerance", "required"),
    ),
    "latency_bandwidth": (
        ("consistency", "strong"), ("latency", "hard_realtime"),
    ),
    "strong_vs_eventual_merge": (
        ("consistency", "strong"), ("offline_window", "unbounded"), ("merge_model", "automatic"),
    ),
    "realtime_vs_offline": (
        ("latency", "hard_realtime"), ("offline_window", "unbounded"),
    ),
    "cost_vs_capability": (
        ("cost", "zero_infra"), ("capability", "enterprise"),
    ),
}

# FALLBACK signal substring families (pre-structured runs only). These are evadable by
# paraphrase — the structured axis path above is the authoritative, paraphrase-proof check.
_REQUIREMENT_CONTRADICTION_FAMILIES = {
    "cap_consistency_vs_availability": (
        "strong consistency", "强一致", "linearizable", "serializable", "strictly ordered",
        "high availability", "高可用", "极高可用", "partition tolerance", "分区容忍",
        "断网继续写", "partition-tolerant writes", "total order broadcast", "raft quorum",
    ),
    "latency_bandwidth": (
        "p99 < 10ms", "p99<10ms", "p99 < 5ms", "p99 < 1ms",
        "sub-10ms", "sub 10ms", "毫秒级", "极低延迟",
        "cross-region strong consistency", "跨大洲强一致", "跨区域强一致",
    ),
    "strong_vs_eventual_merge": (
        "strong consistency", "强一致",
        "offline", "离线", "offline 24h", "离线24", "离线编辑", "long offline mutation",
        "auto-merge", "自动合并", "automatic merge", "conflict-free merge",
    ),
    "realtime_vs_offline": (
        "hard real-time", "硬实时", "real-time guarantee", "实时保证",
        "unbounded offline", "无限离线", "offline buffering", "离线缓冲",
    ),
    "cost_vs_capability": (
        "enterprise", "企业级",
        "no dependencies", "不许加依赖", "zero infra", "zero budget", "不加任何依赖",
    ),
}


def _collect_declared_requirement_axes(root: Path, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect structured requirement_axis declarations (paraphrase-proof path).

    The agent may declare requirements with explicit axis tags in
    .bagel/expert/problem-framing.yaml under requirement_axes:, or in
    .bagel/constitution.yaml under requirements:. Each entry should carry an id,
    a requirement_axis from _REQUIREMENT_AXES, and a strength.
    """
    out: list[dict[str, Any]] = []
    framing = as_dict(load_yaml(root / ".bagel/expert/problem-framing.yaml", {}))
    for raw in as_list(framing.get("requirement_axes")):
        out.append(as_dict(raw))
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    for raw in as_list(constitution.get("requirements")):
        d = as_dict(raw)
        if d.get("requirement_axis") or d.get("axis"):
            out.append(d)
    for raw in as_list(state.get("declared_requirements")):
        out.append(as_dict(raw))
    return out


def _requirement_text(root: Path, state: dict[str, Any]) -> str:
    """Collect the full requirement/claim text for contradiction/falsifiability scanning."""
    chunks: list[str] = []
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    for key in ("vision", "north_star", "non_goals", "assumptions", "requirements", "completion_horizon"):
        chunks.append(str(constitution.get(key) or ""))
    chunks.append(str(state.get("task_queue") or ""))
    chunks.append(str(state.get("current_requirements") or ""))
    framing = as_dict(load_yaml(root / ".bagel/expert/problem-framing.yaml", {}))
    chunks.append(str(framing.get("user_stated_problem") or ""))
    chunks.append(str(framing.get("inferred_real_problem") or ""))
    return "\n".join(chunks).lower()


def validate_requirement_coherence(root: Path, state: dict[str, Any], errors: list[str]) -> None:
    """requirement_coherence_checked gate (S2 scenario).

    MANDATORY structured-declaration check (paraphrase-proof) + fallback.
    The structured path is REQUIRED for Build/Iterate runs that declare any requirement:
    the agent must tag requirements with {requirement_axis, strength} from the fixed enum.
    This closes the synonym-evasion gap because the axis is declared, not inferred.

    Hardened against 5 bypasses found by Darwin judges:
    1. enum-validation: a declared strength NOT in _REQUIREMENT_AXES[axis] is rejected
    2. single-axis starvation: fewer than 2 declared axes is flagged (cannot detect conflicts)
    3. declared-vs-freetext inconsistency: if free text carries a signal the declared axes
       contradict (e.g. declared consistency=eventual but vision says "强一致"), flag it
    4. the structured path is MANDATORY when requirements exist (not opt-in)
    5. a matched contradiction requires a family-linked + action-verb human decision

    A generic "tradeoff" note that does not name the family/requirement does NOT clear
    the gate. "你看着办" is explicitly NOT a resolution.
    """
    text = _requirement_text(root, state)
    declared = _collect_declared_requirement_axes(root, state)
    matched_families: dict[str, list[str]] = {}

    # --- Structured-path integrity checks (bypasses 1, 2, 4) ---
    valid_axis_strengths: set[tuple[str, str]] = set()
    has_requirements_text = bool(text.strip())
    # The structured declaration is MANDATORY once alignment has produced a problem-framing
    # artifact (the post-alignment requirement record) — NOT gated behind a paraphrase-evadable
    # risk-signal check (Judge M+N finding: gating the mandatory path on a substring matcher
    # reintroduces the evasion one level up). A pre-alignment run with only a task_queue is not
    # yet forced (no requirement record exists to tag). A trivial aligned build attests
    # no_contradiction_axes_needed: true (an auditable self-attest the fallback still scans).
    framing_path = root / ".bagel/expert/problem-framing.yaml"
    has_problem_framing = framing_path.exists()
    framing = as_dict(load_yaml(framing_path, {}))
    axes_attested_none = framing.get("no_contradiction_axes_needed") is True
    has_stated_problem = bool(str(framing.get("user_stated_problem") or "").strip())

    # Cross-validate a "no axes needed" attestation against the stated-problem text:
    # if the text carries a strong-axis freetext signal (consistency/availability/
    # partition/latency/offline/merge), the attestation is a lie and must be refused
    # (Judge O finding: unvalidated attestation was a clean escape for a paraphrased
    # contradiction). This reuses the _FREETEXT_AXIS_SIGNALS table defined below.
    stated_text = str(framing.get("user_stated_problem") or "").lower()
    inferred_text = str(framing.get("inferred_real_problem") or "").lower()
    attestation_text = stated_text + "\n" + inferred_text
    _STRONG_AXIS_SIGNALS = {
        "consistency": ("strong consistency", "强一致", "linearizable", "serializable", "strictly ordered", "线性一致"),
        "availability": ("high availability", "高可用", "always-on", "极高可用", "永远在线", "continuously reachable"),
        "partition_tolerance": ("partition", "分区", "断网", "network split", "disconnected"),
        "latency": ("p99", "毫秒", "极低延迟", "real-time", "实时", "sub-10ms"),
        "offline_window": ("offline", "离线", "unbounded offline"),
        "merge_model": ("auto-merge", "自动合并", "automatic merge"),
    }
    attestation_contradicted = any(
        any(sig in attestation_text for sig in signals)
        for signals in _STRONG_AXIS_SIGNALS.values()
    )
    if axes_attested_none and attestation_contradicted:
        errors.append(
            "requirement_coherence_checked: no_contradiction_axes_needed=true is attested but "
            "the stated/inferred problem carries a strong-axis signal (consistency/availability/"
            "partition/latency/offline/merge). The attestation contradicts the requirement text — "
            "declare the real requirement_axes instead of attesting none apply."
        )
        axes_attested_none = False  # treat as not-attested so the mandatory branch fires

    if has_problem_framing and has_stated_problem:
        if not declared and not axes_attested_none:
            # MANDATORY: either declare real axes, or explicitly attest none apply.
            errors.append(
                "requirement_coherence_checked: a problem-framing with a stated problem exists "
                "but no requirement_axes are declared in .bagel/expert/problem-framing.yaml. Tag "
                "each requirement with {requirement_axis, strength} from the fixed enum "
                "(consistency/availability/partition_tolerance/latency/offline_window/merge_model/"
                "cost/capability) so the contradiction check is paraphrase-proof. If genuinely no "
                "contradiction axes apply, set no_contradiction_axes_needed: true (the substring "
                "fallback still scans)."
            )
        elif declared:
            # Bypass 2: single-axis starvation — need >=2 axes to detect any conflict
            parsed_axes: list[tuple[str, str, str]] = []  # (axis, strength, source_id)
            for d in declared:
                axis = str(d.get("requirement_axis") or d.get("axis") or "").lower()
                strength = str(d.get("strength") or d.get("value") or "").lower()
                rid = str(d.get("id") or "")
                if not axis or not strength:
                    errors.append(
                        f"requirement_coherence_checked: declared requirement_axis entry "
                        f"{rid or '(no id)'} missing requirement_axis or strength"
                    )
                    continue
                # Bypass 1: enum-validation — reject unknown axis or strength
                if axis not in _REQUIREMENT_AXES:
                    errors.append(
                        f"requirement_coherence_checked: declared axis '{axis}' "
                        f"(req {rid}) is not in the fixed enum {sorted(_REQUIREMENT_AXES)}"
                    )
                    continue
                if strength not in _REQUIREMENT_AXES[axis]:
                    errors.append(
                        f"requirement_coherence_checked: declared strength '{strength}' for "
                        f"axis '{axis}' (req {rid}) is not in the allowed set "
                        f"{sorted(_REQUIREMENT_AXES[axis])}"
                    )
                    continue
                parsed_axes.append((axis, strength, rid))
                valid_axis_strengths.add((axis, strength))
            # Bypass 2: need >=2 valid axes to detect conflicts
            if len(parsed_axes) < 2:
                errors.append(
                    "requirement_coherence_checked: fewer than 2 valid requirement_axes "
                    "declared — contradiction conflicts require >=2 axes to detect. "
                    "Declare an axis for each distinct requirement."
                )

    # --- Conflict detection (structured path, paraphrase-proof) ---
    for family, conflict_axes in _AXIS_CONFLICTS.items():
        hits = [f"{a}={s}" for (a, s) in conflict_axes if (a, s) in valid_axis_strengths]
        if len(hits) >= 2:
            matched_families[family] = [f"declared:{h}" for h in hits]

    # --- Bypass 3: declared-vs-freetext inconsistency ---
    # If the agent declared structured axes BUT the free text contains a signal that
    # contradicts a declared axis (e.g. declared consistency=eventual, text says "强一致"),
    # the declaration is inconsistent with the stated requirement — flag it.
    if has_requirements_text and valid_axis_strengths:
        _FREETEXT_AXIS_SIGNALS = {
            "consistency": ("strong consistency", "强一致", "linearizable", "serializable", "strictly ordered"),
            "availability": ("high availability", "高可用", "always-on", "极高可用"),
            "partition_tolerance": ("partition", "分区", "断网", "network split"),
            "latency": ("p99 < 10ms", "p99<10ms", "毫秒", "极低延迟", "real-time", "实时"),
            "offline_window": ("offline", "离线", "unbounded offline"),
            "merge_model": ("auto-merge", "自动合并", "automatic merge"),
        }
        for axis, signals in _FREETEXT_AXIS_SIGNALS.items():
            text_hit = any(s in text for s in signals)
            if not text_hit:
                continue
            # What did the agent declare for this axis?
            declared_for_axis = {s for (a, s) in valid_axis_strengths if a == axis}
            # Strong signals in text vs weak declaration = inconsistency
            strong_strengths = {"strong", "high", "required", "hard_realtime", "unbounded", "automatic", "enterprise"}
            if declared_for_axis and not (declared_for_axis & strong_strengths):
                errors.append(
                    f"requirement_coherence_checked: declared {axis}={declared_for_axis} but "
                    f"free-text requirements reference a strong {axis} signal "
                    f"({[s for s in signals if s in text][:2]}). The structured declaration "
                    f"is inconsistent with the stated requirement — re-tag the axis honestly "
                    f"or the contradiction check cannot be trusted."
                )

    # --- FALLBACK: signal-substring (for families the structured path did not match) ---
    if has_requirements_text:
        for family, signals in _REQUIREMENT_CONTRADICTION_FAMILIES.items():
            if family in matched_families:
                continue
            matched = [s for s in signals if s in text]
            if len(matched) >= 2:
                matched_families[family] = [f"signal:{s}" for s in matched[:3]]

    # --- Resolution check (family-linked + action-verb) ---
    ledger = as_dict(load_yaml(root / ".bagel/ledger.yaml", {}))
    human_decisions = as_list(ledger.get("human_decisions"))
    RESOLUTION_KEYWORDS = ("relax", "drop", "relaxed", "dropped", "tradeoff", "trade-off",
                           "accept", "降低", "放弃", "妥协", "权衡", "取舍", "接受")
    for family, evidence in matched_families.items():
        family_id = family.lower()
        evidence_tokens = tuple(e.lower() for e in evidence)
        resolved = False
        for d in human_decisions:
            dtext = str(d).lower()
            references_family = family_id in dtext or any(tok in dtext for tok in evidence_tokens)
            has_action = any(kw in dtext for kw in RESOLUTION_KEYWORDS)
            if references_family and has_action:
                resolved = True
                break
        if not resolved:
            path_note = "structured-axis (authoritative)" if any("declared:" in e for e in evidence) else "signal-substring (fallback)"
            errors.append(
                f"requirement_coherence_checked: contradiction family '{family}' matched "
                f"({path_note}; evidence: {evidence[:3]}). This requires a human decision in "
                f".bagel/ledger.yaml human_decisions: that BOTH references this family "
                f"(id '{family}' or one of its axes/signals: {evidence_tokens[:3]}) AND names the "
                f"requirement dropped/relaxed or the tradeoff accepted. A generic unrelated "
                f"'tradeoff' note does not clear this gate. '你看着办' is not a resolution."
            )


# Unfalsifiability signals — premises that cannot be operationalized into a test.
# When these name an undefinable subject, the premise must be reframed, not run.
_UNFALSIFIABLE_SUBJECTS = (
    "consciousness", "意识", "qualia", "感受质", "free will", "自由意志",
    "subjective experience", "主观体验", "what it is like", "phenomenal",
    "hard problem of consciousness",
)
_UNFALSIFIABLE_CLAIM_MARKERS = (
    "prove", "证明", "disprove", "is computable", "可计算", "can be computed",
    "is real", "是真实的", "exists", "qualia exists",
)
# A falsifiable premise must record a concrete metric AND a concrete falsifier.
_FALSIFIER_REQUIRED_FIELDS = ("falsifiable_metric", "falsifier")


def validate_premise_falsifiable(root: Path, state: dict[str, Any], errors: list[str]) -> None:
    """premise_falsifiable gate (S3 scenario).

    For research/theory/benchmark runs, the premise must be operationalizable. If the
    stated problem names an unfalsifiable subject (consciousness/qualia/free will) with
    a proof/exists claim and records no concrete metric + falsifier, the gate fails and
    routes to a CHECKPOINT S1 hard-stop — the agent must NOT silently run the experiment
    or substitute a proxy.
    """
    artifact_type = str(
        as_dict(state.get("artifact_profile")).get("type")
        or as_dict(load_yaml(root / ".bagel/constitution.yaml", {})).get("artifact_type")
        or ""
    ).lower()
    is_research_like = any(t in artifact_type for t in ("research", "theory", "benchmark", "experiment", "study"))
    framing = as_dict(load_yaml(root / ".bagel/expert/problem-framing.yaml", {}))
    stated = str(framing.get("user_stated_problem") or "").lower()
    # Detect an unfalsifiable subject + proof/exists claim even outside an explicit research type
    has_unfalsifiable_subject = any(s in stated for s in _UNFALSIFIABLE_SUBJECTS)
    has_proof_claim = any(m in stated for m in _UNFALSIFIABLE_CLAIM_MARKERS)
    if not (is_research_like or (has_unfalsifiable_subject and has_proof_claim)):
        return  # gate only applies to research/theory or a clearly unfalsifiable claim
    # premise_fidelity or a dedicated falsifier block records the operationalization
    pf = as_dict(framing.get("premise_fidelity"))
    falsifier_block = as_dict(framing.get("falsifiability") or framing.get("falsifier_record"))
    source = pf or falsifier_block
    # If the premise was reframed to a falsifiable sub-question, it must be labeled as such
    reframed_as_falsifiable = (
        source.get("reframed_as_subquestion") is True
        or source.get("checkpoint_required") is True
        or source.get("falsifiable_metric")
    )
    if has_unfalsifiable_subject and has_proof_claim and not reframed_as_falsifiable:
        errors.append(
            "premise_falsifiable: the stated problem names an unfalsifiable subject "
            "(e.g. consciousness/qualia/free will) with a prove/exists claim but records "
            "no reframing to a falsifiable sub-question. This premise CANNOT be run as-is; "
            "it must route to a 🔴 CHECKPOINT S1 hard-stop and be reframed into a concrete "
            "metric + falsifier (see research-experiment §1). Do not silently run it or "
            "substitute a proxy."
        )
        return
    # When a falsifier is expected, require both a metric and a falsifier
    if is_research_like and not source.get("falsifiable_metric") and not source.get("falsifier"):
        errors.append(
            "premise_falsifiable: research/theory artifact requires a concrete "
            "falsifiable_metric AND a concrete falsifier recorded in "
            ".bagel/expert/problem-framing.yaml (premise_fidelity or falsifiability block)"
        )


def validate_premise_fidelity(root: Path, errors: list[str]) -> None:
    """P0-8: premise fidelity / proxy-substitution defense.

    When problem framing records a premise_fidelity block, verify the agent did not
    silently substitute a proxy for the user's actual claim. An unfalsifiable premise
    cannot be converted into a narrow proxy experiment and presented as answering the
    original question.
    """
    framing = as_dict(load_yaml(root / ".bagel/expert/problem-framing.yaml", {}))
    pf = as_dict(framing.get("premise_fidelity"))
    if not pf:
        return  # not all tasks need premise_fidelity; only research/theory typically
    proxy_used = pf.get("proxy_used")
    core_preserved = pf.get("core_claim_preserved")
    user_auth = pf.get("user_authority_ref")
    checkpoint = pf.get("checkpoint_required")
    # proxy_used=true without explicit user authority -> the agent swapped the question
    if proxy_used is True and not user_auth:
        errors.append("problem-framing.premise_fidelity: proxy_used=true but no user_authority_ref (proxy substitution without consent)")
    # core claim changed without a checkpoint -> silent rewrite of the user's premise
    if core_preserved is False and checkpoint is not True:
        errors.append("problem-framing.premise_fidelity: core_claim_preserved=false but checkpoint_required is not true (silent premise rewrite)")
    # if chosen_framing is explicitly a proxy, the output must label it a sub-question, not an answer
    chosen = str(pf.get("chosen_framing") or "")
    if proxy_used is True and "sub-question" not in chosen.lower() and "proxy" not in chosen.lower():
        errors.append("problem-framing.premise_fidelity: proxy framing must be labeled as a sub-question/proxy, not as answering the original premise")


def _collect_source_files(root: Path) -> list[Path]:
    """Collect candidate source files to scan for fallback labels (product + test code)."""
    root = Path(root)  # coerce in case a str is passed
    out: list[Path] = []
    for subdir in ("src", "lib", "app", "tests", "test", "internal", "cmd", "pkg"):
        d = root / subdir
        if d.exists():
            for ext in ("*.py", "*.ts", "*.js", "*.tsx", "*.jsx", "*.go", "*.rs", "*.java", "*.rb", "*.swift", "*.kt"):
                out.extend(d.rglob(ext))
    return out


def validate_named_dependency_protocol(root: Path, errors: list[str]) -> None:
    """P0-9: protocol substitution defense.

    Detect the "started real Redis, but product code uses in-memory fallback" cheat.
    Each named dependency must attest that product/test code uses the real endpoint,
    not an in-process substitute. Scans ALL source files (not just agent-declared paths)
    for fallback labels in both English and Chinese.
    """
    # Bilingual fallback labels — covers English + Chinese paraphrasing attempts
    SUSPICIOUS_FALLBACK_LABELS = (
        # English
        "in_memory", "in-memory", "inmemory", "fake_redis", "mock_redis",
        "test_only_store", "hashmap fallback", "hash_map fallback", "hashmapfallback",
        "dict fallback", "memory_store", "memorystore",
        "in_process", "inprocess", "local_cache", "stub_redis", "fake_client",
        "mock_client", "dummy_store", "noop_store", "singleton_cache",
        # Chinese
        "内存", "字典替代", "字典缓存", "假数据", "假redis", "模拟redis",
        "内存存储", "内存缓存", "本地缓存替代", "缓存替代",
        # common paraphrases
        "kv cache", "kv_cache", "in-process store", "in_process_store",
        "memory backend", "memorybackend", "fallback to memory", "fallbacktomemory",
    )
    # Bilingual dependency signals — detects whether named deps were declared
    NAMED_DEP_SIGNALS = (
        # English
        "redis", "postgres", "postgresql", "mysql", "mongo", "mongodb",
        "kafka", "rabbitmq", "elasticsearch", "grpc_service", "grpc service",
        "payment_gateway", "payment gateway", "stripe", "paypal",
        "docker-compose", "docker_compose", "docker run",
        # Chinese
        "数据库", "缓存", "消息队列", "支付网关", "分布式", "集群",
        "redis集群", "数据库集群", "第三方服务", "外部依赖",
    )
    reg_path = root / ".bagel/expert/named-dependency-protocol.yaml"
    if not reg_path.exists():
        # P0-9 hole fix: infer whether named dependencies were declared
        framing = as_dict(load_yaml(root / ".bagel/expert/problem-framing.yaml", {}))
        framing_text = str(framing).lower()
        runtime_evidence_signals = False
        evidence_dir = root / ".bagel/evidence"
        if evidence_dir.exists():
            for ef in evidence_dir.glob("*.yaml"):
                try:
                    if any(s in ef.read_text(encoding="utf-8", errors="ignore").lower() for s in NAMED_DEP_SIGNALS):
                        runtime_evidence_signals = True
                        break
                except OSError:
                    continue
        # also scan constitution + state for dependency signals (user prompt may mention deps)
        state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
        constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
        meta_text = (str(state) + str(constitution)).lower()
        has_named_dep_signal = (
            any(s in framing_text for s in NAMED_DEP_SIGNALS)
            or runtime_evidence_signals
            or any(s in meta_text for s in NAMED_DEP_SIGNALS)
        )
        if has_named_dep_signal:
            errors.append("named dependencies were declared but .bagel/expert/named-dependency-protocol.yaml is missing (cannot skip protocol-substitution check by omitting the record)")
        return
    data = as_dict(load_yaml(reg_path, {}))
    deps = as_list(data.get("named_dependencies") or data.get("dependencies"))
    for dep in deps:
        d = as_dict(dep)
        name = str(d.get("dependency") or "<unknown>")
        test_uses_real = d.get("test_uses_real_endpoint")
        fallbacks = as_list(d.get("forbidden_fallbacks_detected"))
        waiver = d.get("waiver_ref")
        if test_uses_real is False:
            errors.append(f"named_dependency {name}: test_uses_real_endpoint=false (product/test code does not exercise real dependency)")
        if fallbacks and not waiver:
            errors.append(f"named_dependency {name}: forbidden_fallbacks_detected={fallbacks} without waiver_ref (cannot count as real-protocol pass)")
        # P0-9 hardening: scan ALL source files for fallback labels, not just agent-declared paths
        # This prevents an agent from hiding a fallback by not listing the file in refs
        scan_paths: list[Path] = []
        # include agent-declared paths
        for pref in as_list(d.get("product_code_path_refs")) + as_list(d.get("test_path_refs")):
            if isinstance(pref, str):
                p = root / pref
                if p.exists() and p not in scan_paths:
                    scan_paths.append(p)
        # also scan all source files under src/tests (agent cannot hide by omission)
        scan_paths.extend(_collect_source_files(root))
        # deduplicate
        seen: set[str] = set()
        for fpath in scan_paths:
            key = str(fpath)
            if key in seen:
                continue
            seen.add(key)
            if not fpath.exists() or not fpath.is_file():
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            for label in SUSPICIOUS_FALLBACK_LABELS:
                if label in content:
                    rel = fpath.relative_to(root) if root in fpath.parents else fpath
                    errors.append(f"named_dependency {name}: suspicious fallback label {label!r} found in {rel}")
                    break


def validate_dataset_integrity(root: Path, errors: list[str]) -> None:
    """P0-10: research dataset integrity defense.

    Empirical dataset-based claims require split hashes, disjointness checks, and no
    test-set tuning. This catches the "held-out trick" where the test set leaks.
    """
    di_path = root / ".bagel/expert/dataset-integrity.yaml"
    if not di_path.exists():
        # check if the run made empirical claims that require dataset_integrity
        claims = as_dict(load_yaml(root / ".bagel/expert/claim-evidence.yaml", {}))
        has_dataset_claim = any(
            "dataset" in str(as_dict(c).get("evidence_type") or "").lower()
            or "empirical" in str(as_dict(c).get("evidence_type") or "").lower()
            for c in as_list(claims.get("claims"))
        )
        if has_dataset_claim:
            errors.append("empirical dataset claim present but .bagel/expert/dataset-integrity.yaml missing")
        return
    di = as_dict(load_yaml(di_path, {}))
    dataset_id = di.get("dataset_id")
    if not dataset_id:
        errors.append("dataset_integrity: dataset_id is required")
    # split hashes required for dataset-based claims
    split_hashes = {
        "train": di.get("train_split_hash"),
        "val": di.get("val_split_hash"),
        "test": di.get("test_split_hash"),
    }
    missing = [k for k, v in split_hashes.items() if not v]
    if missing:
        errors.append(f"dataset_integrity: missing split hashes: {missing}")
    # disjointness check required
    if not di.get("split_disjointness_check_ref"):
        errors.append("dataset_integrity: split_disjointness_check_ref is required (no proof train/val/test are disjoint)")
    # test-set tuning = headline claim fail
    if di.get("tuning_used_test_set") is True:
        errors.append("dataset_integrity: tuning_used_test_set=true (headline claim invalidated — test set was used for tuning)")
    # preprocessing fit on all data without justification = leakage
    if di.get("preprocessing_fit_on") == "all_data" and not di.get("all_data_justification"):
        errors.append("dataset_integrity: preprocessing_fit_on=all_data without justification (potential leakage)")


def validate_claim_evidence_matrix(root: Path, state: dict[str, Any], errors: list[str]) -> None:
    """C3 fix (Judge S4): the claim-evidence matrix (research-experiment §7) was never validated.

    For research/theory/benchmark artifacts with a claim-evidence.yaml, each claim row must
    carry a metric, non-empty run_refs (evidence files that exist), an ablation_status, and a
    reproducibility_status. A headline claim with ablation_status=pending or reproducibility_status
    =missing fails — the claim outruns its evidence.
    """
    artifact_type = str(
        as_dict(state.get("artifact_profile")).get("type")
        or as_dict(load_yaml(root / ".bagel/constitution.yaml", {})).get("artifact_type")
        or ""
    ).lower()
    if not any(t in artifact_type for t in ("research", "theory", "benchmark", "experiment", "study")):
        return  # claim-evidence matrix only applies to empirical/research artifacts
    ce_path = root / ".bagel/expert/claim-evidence.yaml"
    if not ce_path.exists():
        # check whether the run made headline claims that require a matrix
        framing = as_dict(load_yaml(root / ".bagel/expert/problem-framing.yaml", {}))
        has_headline_claim = bool(framing.get("headline_claim") or framing.get("primary_claim"))
        if has_headline_claim:
            errors.append(
                "claim_evidence_matrix: a headline claim is recorded but no .bagel/expert/"
                "claim-evidence.yaml exists. Every research claim must map to a claim-evidence "
                "row with metric, run_refs, ablation_status, and reproducibility_status "
                "(research-experiment §7)."
            )
        return
    ce = as_dict(load_yaml(ce_path, {}))
    claims = as_list(ce.get("claims") or ce.get("claim_evidence"))
    if not claims:
        errors.append("claim_evidence_matrix: claim-evidence.yaml exists but has no claim rows")
        return
    for i, raw in enumerate(claims, start=1):
        c = as_dict(raw)
        for field in ("claim_text", "metric", "run_refs"):
            if not c.get(field):
                errors.append(f"claim_evidence_matrix: claim {i} missing required field {field}")
        run_refs = as_list(c.get("run_refs"))
        if run_refs:
            missing_refs = [str(r) for r in run_refs if not (root / str(r)).exists()]
            if missing_refs:
                errors.append(f"claim_evidence_matrix: claim {i} run_refs point to nonexistent files: {missing_refs[:3]}")
        ablation = str(c.get("ablation_status") or "").lower()
        repro = str(c.get("reproducibility_status") or "").lower()
        is_headline = c.get("is_headline") is True or "headline" in str(c.get("claim_text") or "").lower()
        if is_headline and ablation == "pending":
            errors.append(f"claim_evidence_matrix: claim {i} is a headline claim but ablation_status=pending — a headline claim must survive ablation before it can be reported")
        if is_headline and repro == "missing":
            errors.append(f"claim_evidence_matrix: claim {i} is a headline claim but reproducibility_status=missing — a headline claim must have verified or claimed reproducibility")


def validate_statistical_rigor(root: Path, state: dict[str, Any], errors: list[str]) -> None:
    """C2 fix (Judge S4): statistical rigor was prose-only — no validator enforced it.

    For research/theory/benchmark artifacts with headline claims, require:
    - n_seeds >= 3 (>= 5 for headline claims)
    - a test_result block with {test_type, statistic, p_value, effect_size, correction_applied}
      where test_type is paired_t or wilcoxon and correction_applied is bonferroni/bh/none
    - a pre_registered_threshold; if changed, a threshold_change_reason + checkpoint
    Catches: single-seed wins, missing p-values, post-hoc threshold movement.
    """
    artifact_type = str(
        as_dict(state.get("artifact_profile")).get("type")
        or as_dict(load_yaml(root / ".bagel/constitution.yaml", {})).get("artifact_type")
        or ""
    ).lower()
    if not any(t in artifact_type for t in ("research", "theory", "benchmark", "experiment", "study")):
        return
    # Only enforce when a statistical-results record exists OR headline claims exist
    sr_path = root / ".bagel/expert/statistical-rigor.yaml"
    ce_path = root / ".bagel/expert/claim-evidence.yaml"
    has_headline = False
    if ce_path.exists():
        ce = as_dict(load_yaml(ce_path, {}))
        for raw in as_list(ce.get("claims") or ce.get("claim_evidence")):
            c = as_dict(raw)
            if c.get("is_headline") is True or "headline" in str(c.get("claim_text") or "").lower():
                has_headline = True
                break
    if not sr_path.exists():
        if has_headline:
            errors.append(
                "statistical_rigor: headline research claims exist but no .bagel/expert/"
                "statistical-rigor.yaml record exists. Headline claims require n_seeds>=5, "
                "a test_result block (paired_t/wilcoxon + p_value + effect_size + correction), "
                "and a pre_registered_threshold (research-experiment §8)."
            )
        return
    sr = as_dict(load_yaml(sr_path, {}))
    n_seeds = sr.get("n_seeds")
    if not isinstance(n_seeds, (int, float)) or n_seeds < 3:
        errors.append(f"statistical_rigor: n_seeds={n_seeds} is below the minimum of 3 (>=5 for headline claims) — a single-seed result is not statistically valid")
    elif has_headline and n_seeds < 5:
        errors.append(f"statistical_rigor: n_seeds={n_seeds} is below 5 for a headline claim — headline claims need >=5 seeds")
    seeds = as_list(sr.get("seeds"))
    if seeds and len(seeds) < 3:
        errors.append(f"statistical_rigor: seeds list has {len(seeds)} entries, below the minimum of 3")
    test = as_dict(sr.get("test_result"))
    if has_headline or sr.get("test_result"):
        for field in ("test_type", "statistic", "p_value", "effect_size", "correction_applied"):
            if not test.get(field):
                errors.append(f"statistical_rigor: test_result missing required field {field}")
        test_type = str(test.get("test_type") or "").lower()
        if test_type and test_type not in {"paired_t", "paired-t", "wilcoxon", "t_test", "t-test", "bootstrap"}:
            errors.append(f"statistical_rigor: test_result.test_type='{test_type}' is not a recognized significance test (paired_t/wilcoxon/bootstrap)")
        correction = str(test.get("correction_applied") or "").lower()
        if correction and correction not in {"none", "bonferroni", "bh", "benjamini-hochberg", "holm"}:
            errors.append(f"statistical_rigor: test_result.correction_applied='{correction}' is not recognized (none/bonferroni/bh/holm)")
        # Significance check (Judge U finding): p_value must actually be below the
        # pre-registered threshold for a headline "win" claim — presence-only is theater.
        p_value = test.get("p_value")
        threshold = sr.get("pre_registered_threshold")
        if has_headline and isinstance(p_value, (int, float)) and isinstance(threshold, (int, float)):
            if p_value >= threshold:
                errors.append(
                    f"statistical_rigor: headline claim reports p_value={p_value} >= pre_registered_threshold={threshold} "
                    f"— the result is NOT statistically significant at the pre-registered threshold. "
                    f"A headline 'win' claim requires p_value < threshold."
                )
    pre_threshold = sr.get("pre_registered_threshold")
    if pre_threshold is not None and sr.get("threshold_changed") is True:
        if not sr.get("threshold_change_reason"):
            errors.append("statistical_rigor: threshold_changed=true but no threshold_change_reason — moving a pre-registered threshold post-hoc without justification is p-hacking")
        if sr.get("checkpoint_required") is not True:
            errors.append("statistical_rigor: threshold_changed=true but checkpoint_required is not true — a moved threshold requires a user checkpoint (potential p-hacking)")


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
        # S2/S3 scenario safety gates run in every mode (they are safety checks, not
        # expert-ritual checks): a CAP contradiction or unfalsifiable premise must be
        # caught even in a lite run, not silently built.
        validate_requirement_coherence(root, state, errors)
        validate_premise_falsifiable(root, state, errors)
        # C2/C3: research integrity (statistical rigor + claim-evidence matrix)
        validate_claim_evidence_matrix(root, state, errors)
        validate_statistical_rigor(root, state, errors)
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
    # P0-8/9/10: research integrity anti-cheat (applies to any research/theory run)
    validate_premise_fidelity(root, errors)
    validate_named_dependency_protocol(root, errors)
    validate_dataset_integrity(root, errors)
    # S2/S3 scenario gates: requirement coherence + premise falsifiability
    validate_requirement_coherence(root, state, errors)
    validate_premise_falsifiable(root, state, errors)
    # C2/C3: research integrity (statistical rigor + claim-evidence matrix)
    validate_claim_evidence_matrix(root, state, errors)
    validate_statistical_rigor(root, state, errors)
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
