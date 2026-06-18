#!/usr/bin/env python3
"""Validate V4 research governance artifacts."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from typing import Any

import yaml


RESEARCH_SIGNALS = ("research", "experiment", "benchmark", "study", "theory", "analysis")
PROTECTED_PROTOCOL_FIELDS = {
    "hypothesis",
    "primary_metric",
    "decision_threshold",
    "dataset",
    "dataset_split",
    "baseline",
    "seed_policy",
    "exclusion_criteria",
    "statistical_test",
    "analysis_plan",
}
DESIGN_CHANGE_CLASSES = {"design_amendment", "posthoc_analysis", "core_identity_change"}
# Falsifier must carry a concrete numeric/operational threshold so a vague
# sentence like "if the result differs" is rejected. Note: word boundaries
# (\b) must be single-escaped in a raw string; the prior doubled backslashes
# silently broke the whole alternation (it matched nothing, including
# operator+number forms), which made research_governance_check fail every
# spec-compliant research run. Verified empirically.
NUMERIC_THRESHOLD_RE = re.compile(
    r"(>=|<=|>|<|=|±|\bdelta\b|\bchange\b|\bthreshold\b|improves?|decreases?|reduces?|increases?|exceeds?|drops?|below|above|under|over|worse|better|beat)"
    r".*[+-]?\d+(?:\.\d+)?"
    r"|[+-]?\d+(?:\.\d+)?.*(?:%|percent|bp|bpb|bleu|f1|auc|acc|loss|p\b|p_|alpha|seed|epoch|step)",
    re.I,
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
    return value if isinstance(value, list) else [value]


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) == 0
    return False


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_preregistration(root: Path) -> dict[str, Any]:
    data = as_dict(load_yaml(root / ".bagel/research/preregistration.yaml", {}))
    return as_dict(data.get("preregistration")) or data


def load_runtime_capabilities(root: Path) -> dict[str, Any]:
    data = as_dict(load_yaml(root / ".bagel/runtime_capabilities.yaml", {}))
    return as_dict(data.get("runtime_capabilities")) or data


def capability_observed_with_proof(root: Path, capability: str) -> bool:
    caps = as_dict(load_runtime_capabilities(root).get("capabilities"))
    rec = as_dict(caps.get(capability))
    if rec.get("observed") is not True:
        return False
    proof_ref = str(rec.get("proof_ref") or "")
    return bool(proof_ref and (root / proof_ref).exists())


def load_review_registry(root: Path) -> list[dict[str, Any]]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    registry = as_dict(state.get("review_registry"))
    registry_path = root / ".bagel/agents/registry.yaml"
    if registry_path.exists():
        registry = {**registry, **as_dict(load_yaml(registry_path, {}))}
    reviews = registry.get("reviews") or registry.get("review_events") or registry.get("agents")
    return [as_dict(r) for r in as_list(reviews)]


def registry_confirms_reviewer(
    root: Path,
    *,
    reviewer_agent: str,
    reviewer_session: str,
    actor_agent: str,
    actor_session: str,
) -> bool:
    if not reviewer_agent:
        return False
    for rec in load_review_registry(root):
        rec_reviewer = str(rec.get("reviewer_id") or rec.get("agent_id") or "")
        rec_session = str(rec.get("session_id") or rec.get("reviewer_session_id") or "")
        rec_worker = str(rec.get("worker_id") or rec.get("implements_agent_id") or rec.get("actor_agent_id") or "")
        rec_worker_session = str(rec.get("worker_session_id") or rec.get("actor_session_id") or "")
        derived = str(rec.get("derived_level") or rec.get("review_level") or "")
        if rec_reviewer != reviewer_agent:
            continue
        if reviewer_session and rec_session and rec_session != reviewer_session:
            continue
        if actor_agent and rec_worker and rec_worker != actor_agent:
            continue
        if actor_session and rec_worker_session and rec_worker_session == actor_session:
            continue
        if actor_agent and rec_worker and rec_worker == reviewer_agent:
            continue
        if derived in {"R3", "R4"}:
            return True
    return False


def fresh_preregistration_valid(root: Path, ref: Any, event_ts: Any, original_prereg: dict[str, Any]) -> tuple[bool, str]:
    if not ref:
        return False, "missing fresh_preregistration_ref"
    path = root / str(ref)
    if not path.exists():
        return False, f"fresh_preregistration_ref does not exist: {ref}"
    fresh_data = as_dict(load_yaml(path, {}))
    fresh = as_dict(fresh_data.get("preregistration")) or fresh_data
    fresh_hash = str(fresh.get("plan_sha256") or "")
    original_hash = str(original_prereg.get("plan_sha256") or "")
    if not re.fullmatch(r"[a-f0-9]{64}", fresh_hash):
        return False, "fresh preregistration must include a 64-hex plan_sha256"
    if original_hash and fresh_hash == original_hash:
        return False, "fresh preregistration must pin a different plan_sha256 from the original preregistration"
    if not fresh.get("plan_commit"):
        return False, "fresh preregistration must include plan_commit"
    registered_at = str(fresh.get("registered_at") or "")
    event_time = str(event_ts or "")
    if registered_at and event_time and registered_at < event_time:
        return False, "fresh preregistration registered_at must be no earlier than the amendment event timestamp"
    return True, ""


def is_research_like(root: Path, state: dict[str, Any], constitution: dict[str, Any]) -> bool:
    artifact_type = str(
        as_dict(state.get("artifact_profile")).get("type")
        or constitution.get("artifact_type")
        or state.get("artifact_type")
        or ""
    ).lower()
    if any(signal in artifact_type for signal in RESEARCH_SIGNALS):
        return True
    if as_dict(constitution.get("research_autonomy")):
        return True
    if (root / ".bagel/research").exists():
        return True
    task_text = (str(state.get("task_queue") or "") + "\n" + str(constitution.get("vision") or "")).lower()
    return any(signal in task_text for signal in RESEARCH_SIGNALS)


def build_started(state: dict[str, Any], root: Path) -> bool:
    phase = str(state.get("run_phase") or state.get("phase") or "").lower()
    if phase in {"build", "iterate", "polish", "excellence_loop", "complete"}:
        return True
    if state.get("task_queue"):
        return True
    return (root / ".bagel/evidence/progress-deltas.yaml").exists()


def validate_research_autonomy(constitution: dict[str, Any], errors: list[str]) -> str:
    research = as_dict(constitution.get("research_autonomy"))
    if not research:
        errors.append("research_mode_declared: .bagel/constitution.yaml missing research_autonomy")
        return ""
    mode = str(research.get("mode") or "")
    if mode not in {"protocol_execution", "autonomous_researcher"}:
        errors.append("research_mode_declared: research_autonomy.mode must be protocol_execution or autonomous_researcher")
    intent = as_dict(research.get("researcher_intent_lock"))
    if not intent.get("objective"):
        errors.append("research_mode_declared: researcher_intent_lock.objective is required")
    if not as_list(intent.get("protected_protocol_elements")):
        errors.append("research_mode_declared: researcher_intent_lock.protected_protocol_elements is required")
    perm = as_dict(research.get("permission_model"))
    if mode == "protocol_execution":
        for field in (
            "may_change_experiment_design",
            "may_generate_new_hypotheses",
            "may_retire_unpromising_hypotheses",
            "may_change_primary_metric",
            "may_change_dataset_or_splits",
        ):
            if perm.get(field) is not False:
                errors.append(f"protocol_execution permission_model.{field} must be false")
    if mode == "autonomous_researcher" and perm.get("may_change_experiment_design") is not True:
        errors.append("autonomous_researcher requires permission_model.may_change_experiment_design=true")
    return mode


def research_state(state: dict[str, Any], constitution: dict[str, Any]) -> dict[str, Any]:
    return as_dict(state.get("research")) or as_dict(constitution.get("research_state"))


def validate_plan(root: Path, mode: str, state: dict[str, Any], constitution: dict[str, Any], errors: list[str], prereg_bindings: dict[str, str | None] | None = None) -> dict[str, Any]:
    path = root / ".bagel/research/experiment-plan.yaml"
    plan = as_dict(load_yaml(path, {}))
    body = as_dict(plan.get("experiment_plan")) or plan
    if not body:
        errors.append("experiment_plan_preregistered: .bagel/research/experiment-plan.yaml is required before research Build")
        return {}
    prereg = load_preregistration(root)
    expected_hash = prereg.get("plan_sha256")
    expected_path = prereg.get("plan_path") or ".bagel/research/experiment-plan.yaml"
    actual_hash = sha256_file(path)
    if not prereg:
        errors.append(
            "experiment_plan_preregistered: .bagel/research/preregistration.yaml is required. "
            "State/constitution hashes are agent-writable and are not accepted as the authoritative preregistration record."
        )
    elif expected_path != ".bagel/research/experiment-plan.yaml":
        errors.append(
            "experiment_plan_preregistered: preregistration plan_path must be "
            ".bagel/research/experiment-plan.yaml"
        )
    elif not isinstance(expected_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_hash):
        errors.append(
            "experiment_plan_preregistered: preregistration.yaml requires plan_sha256 "
            "(64 lowercase hex)."
        )
    elif expected_hash != actual_hash:
        errors.append(
            "experiment_plan_preregistered: experiment-plan.yaml sha256 does not match "
            "the preregistration.yaml hash; this looks like post-result plan mutation."
        )
    # V5 attested pre-result binding: when Write attestations exist, the plan's
    # attested write-time must PRECEDE any attested Bash run that produced a
    # metric. This closes the HARKing surface (writing the plan after seeing
    # results) that hash-pinning alone leaves open. prereg_bindings is None in
    # unattested mode → this check is skipped (shape-only fallback).
    if prereg_bindings is not None:
        plan_ts = prereg_bindings.get("plan_write_ts")
        run_ts = prereg_bindings.get("first_run_ts")
        if plan_ts and run_ts and plan_ts > run_ts:
            errors.append(
                "experiment_plan_preregistered: attested write of experiment-plan.yaml "
                f"(timestamp {plan_ts}) is LATER than the first attested Bash run "
                f"(timestamp {run_ts}) — the plan was written after results existed; "
                "this is HARKing under the attestation layer and is rejected."
            )
        elif run_ts and not plan_ts:
            errors.append(
                "experiment_plan_preregistered: attested Bash runs exist but no attested "
                "Write of experiment-plan.yaml was recorded — the plan was never registered "
                "through the platform before experiments ran."
            )
    if body.get("schema_version") != "research_experiment_plan_v1":
        errors.append("experiment_plan_preregistered: schema_version must be research_experiment_plan_v1")
    if mode and body.get("mode") != mode:
        errors.append(f"experiment_plan_preregistered: plan mode {body.get('mode')!r} does not match research_autonomy.mode {mode!r}")
    for field in ("study_id", "objective", "baselines", "controls", "seeds", "analysis_plan", "stopping_rule"):
        if not body.get(field):
            errors.append(f"experiment_plan_preregistered: missing {field}")
    hypotheses = [as_dict(h) for h in as_list(body.get("hypotheses"))]
    if not hypotheses:
        errors.append("experiment_plan_preregistered: at least one hypothesis is required")
    for i, h in enumerate(hypotheses, start=1):
        for field in (
            "id",
            "statement",
            "falsifiable_metric",
            "falsifier",
            "primary_metric",
            "decision_threshold",
            "practical_significance_threshold",
        ):
            if not h.get(field):
                errors.append(f"experiment_plan_preregistered: hypothesis {i} missing {field}")
        falsifier = str(h.get("falsifier") or "")
        if falsifier and not NUMERIC_THRESHOLD_RE.search(falsifier):
            errors.append(
                f"experiment_plan_preregistered: hypothesis {i} falsifier must contain a concrete "
                "numeric/operational threshold, not a vague non-empty sentence"
            )
    return body


def collect_human_decisions(root: Path) -> list[dict[str, Any]]:
    ledger = as_dict(load_yaml(root / ".bagel/ledger.yaml", {}))
    out = [as_dict(d) for d in as_list(ledger.get("human_decisions"))]
    full = root / ".bagel/alignment/human-decisions.yaml"
    data = load_yaml(full, {})
    if isinstance(data, dict):
        out.extend(as_dict(d) for d in as_list(data.get("human_decisions") or data.get("decisions")))
    elif isinstance(data, list):
        out.extend(as_dict(d) for d in data)
    return out


def authority_ref_valid(root: Path, authority_ref: Any, protected_field: str, event_ts: Any) -> bool:
    ref = str(authority_ref or "")
    if not ref:
        return False
    decisions = collect_human_decisions(root)
    for d in decisions:
        decision_id = str(d.get("id") or d.get("decision_id") or d.get("ref") or "")
        if ref not in {decision_id, str(d.get("authority_ref") or "")}:
            continue
        if d.get("decision_type") != "research_design_change":
            continue
        fields = {str(x) for x in as_list(d.get("protected_fields") or d.get("fields") or d.get("field"))}
        if protected_field and protected_field not in fields and "*" not in fields:
            continue
        if d.get("approved") is False or d.get("status") in {"rejected", "denied"}:
            continue
        # If both timestamps exist, authority must not postdate the event.
        decision_ts = str(d.get("timestamp") or d.get("decided_at") or "")
        event_time = str(event_ts or "")
        if decision_ts and event_time and decision_ts > event_time:
            continue
        return True
    return False


def load_amendment(root: Path, ref: Any) -> tuple[Path | None, dict[str, Any]]:
    if not ref:
        return None, {}
    path = root / str(ref)
    if path.exists():
        data = as_dict(load_yaml(path, {}))
        return path, as_dict(data.get("research_design_amendment")) or data
    amend_dir = root / ".bagel/research/amendments"
    if amend_dir.exists():
        for candidate in amend_dir.glob("*.yaml"):
            data = as_dict(load_yaml(candidate, {}))
            body = as_dict(data.get("research_design_amendment")) or data
            if str(body.get("amendment_id") or "") == str(ref):
                return candidate, body
    return None, {}


def validate_amendment(
    root: Path,
    event: dict[str, Any],
    amendment: dict[str, Any],
    forbidden_directions: list[Any],
    original_prereg: dict[str, Any],
    errors: list[str],
) -> None:
    event_id = event.get("event_id") or "<unknown>"
    required = (
        "amendment_id",
        "triggering_evidence_ref",
        "proposed_change",
        "change_class",
        "preserves_research_identity",
        "expected_information_gain",
        "confound_risk",
        "preregistration_boundary",
        "posthoc_label_required",
        "reviewer_ref",
    )
    for field in required:
        if is_blank(amendment.get(field)):
            errors.append(f"research_design_amendment: event {event_id} amendment missing {field}")
    info_gain = as_dict(amendment.get("expected_information_gain"))
    for field in ("decision_resolved", "uncertainty_reduced", "candidate_outcomes", "measurement_plan", "cost_budget"):
        if is_blank(info_gain.get(field)):
            errors.append(f"research_design_amendment: event {event_id} expected_information_gain missing structured field {field}")
    confound = as_dict(amendment.get("confound_risk"))
    for field in ("confound_classes", "mitigations", "could_invert_result"):
        if is_blank(confound.get(field)):
            errors.append(f"research_design_amendment: event {event_id} confound_risk missing structured field {field}")
    impact = as_dict(amendment.get("protected_field_impact"))
    if not impact:
        errors.append(f"research_design_amendment: event {event_id} protected_field_impact is required")
    elif impact.get("changes_protected_fields") is True and not event.get("authority_ref"):
        errors.append(f"research_design_amendment: event {event_id} changes protected fields without authority_ref")
    if amendment.get("preserves_research_identity") is not True:
        errors.append(f"research_design_amendment: event {event_id} does not preserve research identity")
    reviewer_ref = amendment.get("reviewer_ref")
    reviewer_path = root / str(reviewer_ref) if reviewer_ref else None
    if not reviewer_ref or not reviewer_path.exists():
        errors.append(f"research_design_amendment: event {event_id} reviewer_ref missing or nonexistent")
    else:
        reviewer = as_dict(load_yaml(reviewer_path, {}))
        reviewer_agent = str(reviewer.get("agent_id") or as_dict(reviewer.get("reviewer")).get("agent_id") or "")
        reviewer_session = str(reviewer.get("session_id") or as_dict(reviewer.get("reviewer")).get("session_id") or "")
        actor_agent = str(event.get("actor_agent_id") or event.get("agent_id") or "")
        actor_session = str(event.get("actor_session_id") or event.get("session_id") or "")
        if actor_agent and reviewer_agent and actor_agent == reviewer_agent:
            errors.append(f"research_design_amendment: event {event_id} reviewer_ref must be a different agent_id")
        level = str(reviewer.get("derived_level") or reviewer.get("review_level") or "")
        if level not in {"R3", "R4"}:
            errors.append(f"research_design_amendment: event {event_id} reviewer_ref must record derived_level/review_level R3 or R4")
        elif not capability_observed_with_proof(root, "true_subagents"):
            errors.append(
                f"research_design_amendment: event {event_id} claims {level} reviewer independence "
                "without runtime_capabilities.capabilities.true_subagents.observed=true and proof_ref"
            )
        elif not registry_confirms_reviewer(
            root,
            reviewer_agent=reviewer_agent,
            reviewer_session=reviewer_session,
            actor_agent=actor_agent,
            actor_session=actor_session,
        ):
            errors.append(
                f"research_design_amendment: event {event_id} reviewer_ref is not backed by "
                ".bagel/agents/registry.yaml or state.review_registry derived R3/R4 independence"
            )
        if reviewer.get("verdict") not in {"approve", "approved", "pass", "passed"}:
            errors.append(f"research_design_amendment: event {event_id} reviewer_ref must approve/pass the amendment")
        if not as_list(reviewer.get("inspected_artifacts")):
            errors.append(f"research_design_amendment: event {event_id} reviewer_ref must list inspected_artifacts")
        for field in ("invalidation_condition", "forbidden_direction_proximity", "confound_that_could_invert", "fresh_prereg_required"):
            if is_blank(reviewer.get(field)):
                errors.append(f"research_design_amendment: event {event_id} reviewer_ref missing adversarial field {field}")
    if amendment.get("posthoc_label_required") is True or amendment.get("preregistration_boundary") == "after_results":
        fresh = amendment.get("fresh_preregistration_ref")
        ok, reason = fresh_preregistration_valid(root, fresh, event.get("timestamp"), original_prereg)
        if not ok:
            errors.append(
                f"research_design_amendment: event {event_id} post-hoc amendment requires valid "
                f"fresh_preregistration_ref ({reason})"
            )
    proposed = str(amendment.get("proposed_change") or "").lower()
    for forbidden in forbidden_directions:
        f = str(forbidden).strip().lower()
        if f and f in proposed:
            errors.append(f"research_design_amendment: event {event_id} proposed_change overlaps forbidden direction {forbidden!r}")
    if amendment.get("change_class") == "baseline_strengthening":
        delta = as_dict(amendment.get("baseline_strength_delta"))
        if not delta.get("before") or not delta.get("after") or not delta.get("metric"):
            errors.append(
                f"research_design_amendment: event {event_id} baseline_strengthening requires "
                "baseline_strength_delta with metric, before, and after"
            )


def validate_log(root: Path, mode: str, plan: dict[str, Any], constitution: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    path = root / ".bagel/research/experiment-log.yaml"
    log = as_dict(load_yaml(path, {}))
    body = as_dict(log.get("experiment_log")) or log
    events = [as_dict(e) for e in as_list(body.get("events"))]
    amendments: dict[str, dict[str, Any]] = {}
    if not body:
        errors.append("experiment_event_log_current: .bagel/research/experiment-log.yaml is required once research Build starts")
        return amendments
    if body.get("schema_version") != "research_experiment_log_v1":
        errors.append("experiment_event_log_current: schema_version must be research_experiment_log_v1")
    if not events:
        errors.append("experiment_event_log_current: events must not be empty")
    seen: set[str] = set()
    amendment_count = 0
    protected_amendment_count = 0
    for i, event in enumerate(events, start=1):
        event_id = str(event.get("event_id") or "")
        if not event_id:
            errors.append(f"experiment_event_log_current: event {i} missing event_id")
        elif event_id in seen:
            errors.append(f"experiment_event_log_current: duplicate event_id {event_id}")
        seen.add(event_id)
        for field in ("timestamp", "actor_role", "event_type"):
            if not event.get(field):
                errors.append(f"experiment_event_log_current: event {event_id or i} missing {field}")
        changed_design = event.get("changed_design") is True
        change_class = str(event.get("change_class") or "none")
        protected_field = str(event.get("protected_field") or "")
        if mode == "protocol_execution" and (changed_design or protected_field in PROTECTED_PROTOCOL_FIELDS):
            if not authority_ref_valid(root, event.get("authority_ref"), protected_field, event.get("timestamp")):
                errors.append(
                    f"protocol_execution: event {event_id or i} changes protected design "
                    "without a valid ledger.yaml human_decisions authority_ref"
                )
        if change_class == "core_identity_change" and not event.get("authority_ref"):
            errors.append(f"research hard-stop: event {event_id or i} core_identity_change requires authority_ref")
        if change_class in DESIGN_CHANGE_CLASSES or changed_design:
            amendment_count += 1
            amendment_ref = event.get("amendment_ref") or event.get("research_design_amendment_ref")
            _, amendment = load_amendment(root, amendment_ref)
            if not amendment:
                errors.append(f"experiment_event_log_current: event {event_id or i} requires a research_design_amendment ref")
            else:
                amend_id = str(amendment.get("amendment_id") or amendment_ref)
                amendments[amend_id] = amendment
                if amendment_ref:
                    amendments[str(amendment_ref)] = amendment
                if as_dict(amendment.get("protected_field_impact")).get("changes_protected_fields") is True:
                    protected_amendment_count += 1
                validate_amendment(
                    root,
                    event,
                    amendment,
                    as_list(as_dict(constitution.get("research_autonomy")).get("researcher_intent_lock", {}).get("forbidden_directions")),
                    load_preregistration(root),
                    errors,
                )
    if mode == "autonomous_researcher":
        if amendment_count > 5:
            errors.append(
                "research_design_amendment: autonomous_researcher amendment rate limit exceeded "
                f"({amendment_count} design-change events; hard cap is 5 before human review)"
            )
        if protected_amendment_count > 2:
            errors.append(
                "research_design_amendment: protected-field drift cap exceeded "
                f"({protected_amendment_count} amendments touched protected fields; hard cap is 2 before human review)"
            )
    return amendments


def validate_claims(root: Path, plan: dict[str, Any], amendments: dict[str, dict[str, Any]], errors: list[str]) -> None:
    path = root / ".bagel/research/claim-evidence.yaml"
    if not path.exists():
        if plan:
            errors.append("claim_evidence_matrix: .bagel/research/claim-evidence.yaml is required for research Build")
        return
    matrix = as_dict(load_yaml(path, {}))
    body = as_dict(matrix.get("claim_evidence_matrix")) or matrix
    if body.get("schema_version") != "research_claim_evidence_v1":
        errors.append("claim_evidence_matrix: schema_version must be research_claim_evidence_v1")
    metric_evidence = collect_metric_recompute_evidence(root)
    claims = [as_dict(raw) for raw in as_list(body.get("claims"))]
    for i, claim in enumerate(claims, start=1):
        claim_id = claim.get("claim_id") or f"claim {i}"
        if claim.get("claim_type") == "confirmatory":
            if claim.get("posthoc") is True:
                errors.append(f"confirmatory_claim_not_posthoc: {claim_id} is confirmatory but posthoc=true")
            if claim.get("allowed_in_headline") is False:
                errors.append(f"confirmatory_claim_not_posthoc: {claim_id} marked not allowed in headline")
            for field in ("metric_refs", "run_refs", "hypothesis_id"):
                if not claim.get(field):
                    errors.append(f"claim_evidence_matrix: confirmatory {claim_id} missing {field}")
            if claim.get("ablation_status") in {"missing", "pending", None, ""}:
                errors.append(f"claim_evidence_matrix: confirmatory {claim_id} lacks completed ablation status")
            if claim.get("reproducibility_status") in {"missing", None, ""}:
                errors.append(f"claim_evidence_matrix: confirmatory {claim_id} lacks reproducibility status")
            amend_ref = str(claim.get("originating_amendment_ref") or "")
            amendment = amendments.get(amend_ref)
            if amend_ref:
                if not amendment:
                    errors.append(
                        f"confirmatory_claim_not_posthoc: {claim_id} cites unknown originating_amendment_ref {amend_ref}"
                    )
                if not claim.get("prereg_plan_ref"):
                    errors.append(
                        f"confirmatory_claim_not_posthoc: {claim_id} cites amendment {amend_ref} "
                        "but lacks prereg_plan_ref for the confirmatory rerun"
                    )
                if not as_list(claim.get("rerun_event_refs")):
                    errors.append(
                        f"confirmatory_claim_not_posthoc: {claim_id} cites amendment {amend_ref} "
                        "but lacks rerun_event_refs proving a fresh rerun"
                    )
                if amendment and (
                    amendment.get("posthoc_label_required") is True
                    or amendment.get("preregistration_boundary") == "after_results"
                ):
                    fresh_ref = amendment.get("fresh_preregistration_ref")
                    if not fresh_ref or str(fresh_ref) != str(claim.get("prereg_plan_ref")):
                        errors.append(
                            f"confirmatory_claim_not_posthoc: {claim_id} originates from post-hoc amendment "
                            f"{amend_ref}; prereg_plan_ref must equal its fresh_preregistration_ref"
                        )
        # Metric recompute binding applies to confirmatory claims AND any claim
        # promoted to a headline. This closes the "relabel confirmatory as
        # exploratory to skip the binding" bypass: a headline claim of any type
        # must still back its numbers with recompute evidence.
        is_headline = claim.get("allowed_in_headline") is True or claim.get("is_headline") is True
        if claim.get("claim_type") == "confirmatory" or is_headline:
            validate_metric_value_bindings(claim_id, claim, metric_evidence, errors)
    hypothesis_ids = {str(as_dict(h).get("id")) for h in as_list(plan.get("hypotheses")) if as_dict(h).get("id")}
    covered = {
        str(c.get("hypothesis_id"))
        for c in claims
        if c.get("claim_type") in {"confirmatory", "negative_result", "limitation"}
    }
    for hid in sorted(hypothesis_ids - covered):
        errors.append(f"negative_results_complete: registered hypothesis {hid} has no confirmatory/negative_result/limitation claim")


def collect_metric_recompute_evidence(root: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    base = root / ".bagel/evidence"
    if not base.exists():
        return out
    for path in sorted(base.rglob("*.yaml")):
        data = load_yaml(path, {})
        if isinstance(data, dict) and ("evidence" in data or "evidence_id" in data):
            rows = as_list(data.get("evidence")) if "evidence" in data else [data]
        elif isinstance(data, list):
            rows = data
        else:
            continue
        for raw in rows:
            rec = as_dict(raw)
            evidence_id = str(rec.get("evidence_id") or "")
            policy = as_dict(rec.get("replay_policy"))
            mode = str(policy.get("mode") or "")
            has_extractor = bool(rec.get("metric_extractor") or policy.get("metric_extractor"))
            if mode == "metric_recompute" or (mode == "not_replayable" and has_extractor):
                rec["_path"] = str(path.relative_to(root))
                out[evidence_id] = rec
                out[rec["_path"]] = rec
    return out


def validate_metric_value_bindings(
    claim_id: Any,
    claim: dict[str, Any],
    metric_evidence: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    values = [as_dict(v) for v in as_list(claim.get("metric_values"))]
    if not values:
        errors.append(f"metric_recompute: confirmatory {claim_id} requires metric_values with evidence-backed recompute records")
        return
    for i, value in enumerate(values, start=1):
        evidence_ref = str(value.get("evidence_ref") or value.get("evidence_id") or "")
        if not evidence_ref:
            errors.append(f"metric_recompute: confirmatory {claim_id} metric_values[{i}] missing evidence_ref")
            continue
        evidence = metric_evidence.get(evidence_ref)
        if not evidence:
            errors.append(
                f"metric_recompute: confirmatory {claim_id} metric_values[{i}] evidence_ref "
                f"{evidence_ref!r} does not point to a metric_recompute evidence record"
            )
            continue
        policy = as_dict(evidence.get("replay_policy"))
        if policy.get("mode") == "not_replayable" and not (evidence.get("metric_extractor") or policy.get("metric_extractor")):
            errors.append(
                f"metric_recompute: confirmatory {claim_id} metric_values[{i}] uses not_replayable "
                "evidence without metric_extractor"
            )
        declared = evidence.get("declared_value", policy.get("declared_value"))
        if "value" in value and isinstance(declared, (int, float)):
            try:
                if float(value["value"]) != float(declared):
                    errors.append(
                        f"metric_recompute: confirmatory {claim_id} metric_values[{i}] value "
                        f"{value['value']} does not match evidence declared_value {declared}"
                    )
            except (TypeError, ValueError):
                errors.append(f"metric_recompute: confirmatory {claim_id} metric_values[{i}] value is not numeric")
        if value.get("seed") is not None and "value" in value and not value.get("run_ref"):
            errors.append(
                f"metric_recompute: confirmatory {claim_id} metric_values[{i}] is a per-seed "
                "literal without run_ref provenance"
            )
        run_ref = str(value.get("run_ref") or "")
        if run_ref and run_ref not in metric_evidence:
            errors.append(
                f"metric_recompute: confirmatory {claim_id} metric_values[{i}] run_ref "
                f"{run_ref!r} does not point to a metric_recompute evidence record"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    errors: list[str] = []

    if not is_research_like(root, state, constitution):
        print("research_governance_check: not research-like; skipped")
        return 0

    mode = validate_research_autonomy(constitution, errors)
    plan: dict[str, Any] = {}
    amendments: dict[str, dict[str, Any]] = {}
    # V5: load attestation indices when the platform key is configured, so the
    # plan-hash gate can additionally check the plan was written BEFORE any run
    # (pre-result binding). In unattested mode these are None → check skipped.
    prereg_bindings: dict[str, str | None] | None = None
    try:
        import attestation_lib as al
        if al.has_key():
            _errs, verified = al.validate_chain(root, al.get_key())
            write_idx = al.index_writes(verified)
            bash_idx = al.index_outputs(verified)
            prereg_bindings = {
                "plan_write_ts": al.first_write_timestamp(write_idx, "experiment-plan.yaml"),
                "first_run_ts": al.first_run_timestamp(bash_idx),
            }
    except Exception:
        prereg_bindings = None
    if build_started(state, root):
        plan = validate_plan(root, mode, state, constitution, errors, prereg_bindings)
        amendments = validate_log(root, mode, plan, constitution, errors)
    validate_claims(root, plan, amendments, errors)

    if errors:
        print("research_governance_check failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("research_governance_check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
