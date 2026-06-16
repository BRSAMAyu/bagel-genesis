#!/usr/bin/env python3
"""Validate that a real BAGEL run is wired for autonomous execution.

This complements flywheel_check.py. flywheel_check validates quality progress;
this script validates the operational substrate: git rollback, loop binding,
agent dispatch, role separation, and briefing ownership.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

import yaml


VALID_LOOP_MODES = {"scheduled_resume", "external_harness", "active_session_loop", "degraded_resume"}
VALID_STOP = {"progressing", "recovering", "excellence_loop", "waiting_for_capacity", "blocked_hard_stop", "complete"}
IMPLEMENTER_ROLES = {"Implementer", "Skeleton Builder"}
REVIEWER_ROLES = {"Spec Reviewer", "Code Quality Reviewer", "Independent Reviewer", "Red-Team Oracle"}
EXPLORER_LENSES = {"structure", "behavior", "convention", "surface"}
EVALUATION_ROLES = {"Evaluation Architect"}
RUNTIME_ROLES = {"Runtime Doctor"}
CONTROL_PLANE_TERMS = {
    ".bagel",
    "bagel alignment",
    "constitution.yaml",
    "constitution.json",
    "alignment file",
    "status.md",
    "control plane",
    "run check",
    "flywheel_check",
    "bagel_run_check",
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


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def warn(warnings: list[str], message: str) -> None:
    warnings.append(message)


def git_ok(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except Exception:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def collect_registry(root: Path, state: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key in ("agent_dispatches", "dispatches", "agents"):
        records.extend([as_dict(item) for item in as_list(state.get(key))])

    registry_path = root / ".bagel/agents/registry.yaml"
    registry = load_yaml(registry_path, {})
    if isinstance(registry, dict):
        for key in ("agent_dispatches", "dispatches", "agents", "reviews", "review_events"):
            records.extend([as_dict(item) for item in as_list(registry.get(key))])

    dispatch_dir = root / ".bagel/agents/dispatches"
    if dispatch_dir.exists():
        for path in sorted(dispatch_dir.glob("*.yaml")):
            records.append(as_dict(load_yaml(path, {})))

    return [record for record in records if record]


def record_role(record: dict[str, Any]) -> str:
    return str(record.get("role") or record.get("agent_role") or record.get("type") or "")


def record_id(record: dict[str, Any]) -> str:
    return str(record.get("agent_id") or record.get("session_id") or record.get("id") or record.get("reviewer_id") or "")


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def baseline_manifest(root: Path) -> tuple[list[dict[str, Any]], bool]:
    manifest_path = root / ".bagel" / "evidence" / "baseline" / "manifest.yaml"
    manifest = load_yaml(manifest_path, {})
    if isinstance(manifest, dict):
        commands = as_list(manifest.get("commands") or manifest.get("verification_evidence"))
        return [as_dict(item) for item in commands], manifest_path.exists()
    if isinstance(manifest, list):
        return [as_dict(item) for item in manifest], manifest_path.exists()
    return [], manifest_path.exists()


def validate_judgment_record(root: Path, judgment_ref: Any, expected_type: str, errors: list[str]) -> None:
    if not judgment_ref:
        fail(errors, f"complete run requires {expected_type} judgment_ref")
        return
    path = root / str(judgment_ref)
    if not path.exists():
        fail(errors, f"judgment_ref does not exist: {judgment_ref}")
        return
    record = as_dict(load_yaml(path, {}))
    if record.get("decision_type") != expected_type:
        fail(errors, f"judgment decision_type must be {expected_type}, got {record.get('decision_type')!r}")
    councilors = [as_dict(item) for item in as_list(record.get("councilors"))]
    if len(councilors) < 3:
        fail(errors, "final Judgment Council requires >=3 councilors")
    dimensions = {str(item.get("dimension")) for item in councilors if item.get("dimension")}
    if len(dimensions) < 3:
        fail(errors, "final Judgment Council requires >=3 distinct dimensions")
    ids = {str(item.get("agent_id") or item.get("session_id")) for item in councilors if item.get("agent_id") or item.get("session_id")}
    if len(ids) < len(councilors):
        fail(errors, "final Judgment Council agent/session ids must be distinct and recorded")
    merge = as_dict(record.get("merge_result"))
    if merge.get("status") != "passed" or merge.get("judgment_passed") is not True:
        fail(errors, "final delivery judgment must pass before state can be complete")


def validate_git(root: Path, state: dict[str, Any], errors: list[str]) -> None:
    if not git_ok(root):
        fail(errors, "project root is not a git repository; rollback and worktree isolation are unavailable")
    gates = as_dict(state.get("gates"))
    gate_value = gates.get("project_under_version_control")
    if gate_value not in {True, "pass", "passed"}:
        fail(errors, "state.gates.project_under_version_control must be pass/true before autonomous write work")


def validate_loop(state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    loop = as_dict(state.get("loop_binding"))
    if not loop:
        fail(errors, "state.loop_binding is missing; autonomous iteration has no timer/loop proof")
        return
    mode = loop.get("mode")
    if mode not in VALID_LOOP_MODES:
        fail(errors, f"loop_binding.mode must be one of {sorted(VALID_LOOP_MODES)}, got {mode!r}")
    interval = loop.get("trigger_interval_minutes")
    if not isinstance(interval, int) or interval <= 0:
        fail(errors, "loop_binding.trigger_interval_minutes must be a positive integer")
    elif interval > 25:
        fail(errors, f"loop trigger interval {interval} exceeds HARD MAX 25 minutes")
    if mode in {"scheduled_resume", "external_harness", "active_session_loop"} and not as_list(loop.get("proof")):
        fail(errors, f"loop_binding.mode={mode} requires proof (schedule id, loop config, harness command, etc.)")
    if mode == "degraded_resume":
        attempts = as_list(loop.get("attempts"))
        attempted = {as_dict(item).get("tier") or as_dict(item).get("mechanism") for item in attempts}
        if not attempts:
            fail(errors, "degraded_resume requires recorded P1/P2 attempts proving loop binding was unavailable")
        if not any("P1" in str(item) or str(item) in {"native_platform_loop", "/loop", "automation", "scheduled_task"} for item in attempted):
            warn(warnings, "degraded_resume does not show a clearly labeled P1/native loop attempt")
        if not any("P2" in str(item) or str(item) in {"external_harness", "cron", "launchd", "cli_loop"} for item in attempted):
            warn(warnings, "degraded_resume does not show a clearly labeled P2/external harness attempt")

    detected_at = parse_time(as_dict(state.get("runtime_capabilities")).get("detected_at"))
    alignment_started_at = parse_time(as_dict(state.get("alignment")).get("started_at"))
    loop_created_at = parse_time(loop.get("created_at"))
    if detected_at and alignment_started_at and loop_created_at and loop_created_at > alignment_started_at:
        fail(errors, "loop_binding.created_at is after alignment.started_at; v1.2 requires loop binding before Align/Explore")
    elif alignment_started_at and not loop_created_at:
        warn(warnings, "alignment has started but loop_binding.created_at is missing; cannot prove loop was bound before Align")


def validate_alignment_floor(state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    alignment = as_dict(state.get("alignment"))
    depth = alignment.get("depth") or as_dict(state.get("autonomy_contract")).get("alignment_depth")
    if not depth:
        warn(warnings, "alignment depth missing; cannot verify deep-alignment floor")
        return
    cards = int(alignment.get("choice_cards_answered") or 0)
    open_q = int(alignment.get("open_questions_answered") or 0)
    rounds = int(alignment.get("rounds") or 0)
    if depth == "snap_alignment":
        if cards + open_q < 4:
            fail(errors, "snap_alignment requires at least 4 answered/defaulted alignment items")
    elif depth == "standard_alignment":
        if cards < 8 or open_q < 3:
            fail(errors, "standard_alignment requires all 8 choice cards and >=3 open questions")
    elif depth == "deep_alignment":
        if rounds < 2 or cards < 8 or open_q < 5 or cards + open_q < 8:
            fail(errors, "deep_alignment requires >=2 rounds, all 8 cards, >=5 open questions, >=8 total")
    else:
        fail(errors, f"unknown alignment depth {depth!r}")


def validate_stop_contract(root: Path, state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Verify the Stop Contract was captured before autonomous work began.

    The Stop Contract (max_iterations, budget_limit, hard_stops, within_autonomy,
    morning_return, deadline) is the single most important alignment artifact:
    it defines when the overnight run ends. If the loop is bound (alignment done,
    run started) but the Stop Contract is missing, the agent began autonomous
    work without agreeing with the user on when it stops.
    """
    loop = as_dict(state.get("loop_binding"))
    has_progress = (root / ".bagel" / "evidence" / "progress-deltas.yaml").exists()
    run_started = bool(loop) or has_progress or as_list(state.get("task_queue"))
    if not run_started:
        return  # still in alignment; not yet enforceable

    bagel = root / ".bagel"
    constitution = load_yaml(bagel / "constitution.yaml", {})
    if not isinstance(constitution, dict) or not constitution:
        constitution = load_yaml(bagel / "constitution.json", {})
    if not isinstance(constitution, dict):
        constitution = {}

    stop = as_dict(constitution.get("stop_contract"))
    if not stop:
        stop = as_dict(state.get("stop_contract"))

    if not stop:
        fail(errors, "stop_contract is missing from constitution - the run started without agreeing with the user on when it ends (max_iterations, budget, hard_stops, deadline). This is the core overnight contract and must be captured before Build.")
        return

    max_iter = stop.get("max_iterations")
    if max_iter is None and stop.get("budget_limit") is None:
        fail(errors, "stop_contract must specify max_iterations or budget_limit - without one, the run has no defined end")

    if not as_list(stop.get("hard_stops")):
        fail(errors, "stop_contract.hard_stops is empty - the user was never asked what should wake them")


def validate_dispatch(root: Path, state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    records = collect_registry(root, state)
    telemetry = as_dict(state.get("telemetry"))
    agents_dispatched = telemetry.get("agents_dispatched")
    if isinstance(agents_dispatched, int) and agents_dispatched > len(records):
        warn(warnings, "telemetry.agents_dispatched exceeds registry records; registry may be incomplete")

    if not records:
        fail(errors, "no agent dispatch/registry records found; main model may be doing work directly")
        return

    roles = {record_role(record) for record in records}
    if not (roles & IMPLEMENTER_ROLES):
        fail(errors, "no Implementer/Skeleton Builder dispatch found for write work")
    if not (roles & REVIEWER_ROLES):
        fail(errors, "no reviewer/red-team dispatch found; review may be self-approved")

    implementer_ids = {record_id(record) for record in records if record_role(record) in IMPLEMENTER_ROLES and record_id(record)}
    reviewer_ids = {record_id(record) for record in records if record_role(record) in REVIEWER_ROLES and record_id(record)}
    overlap = implementer_ids & reviewer_ids
    if overlap:
        fail(errors, f"same agent id used for implementation and review: {sorted(overlap)}")

    for record in records:
        role = record_role(record)
        if role in IMPLEMENTER_ROLES:
            read = "\n".join(str(item) for item in as_list(record.get("read") or record.get("read_only") or record.get("allowed_read_paths")))
            if "SKILL.md" in read or "references/" in read:
                fail(errors, f"{role} dispatch {record_id(record) or '<unknown>'} reads global skill/reference context")
        if role == "Brainstormer":
            if not record.get("lens"):
                fail(errors, f"Brainstormer dispatch {record_id(record) or '<unknown>'} missing lens")
            if record.get("saw_other_brainstormers") is True:
                fail(errors, f"Brainstormer dispatch {record_id(record) or '<unknown>'} saw other brainstormer outputs")
        if role in EVALUATION_ROLES:
            output = str(record.get("output") or record.get("writes") or record.get("return_format") or "")
            if "evaluation" not in output.lower() and "rubric" not in output.lower() and "metric" not in output.lower():
                warn(warnings, f"Evaluation Architect dispatch {record_id(record) or '<unknown>'} does not visibly request evaluation spec output")
        if role in RUNTIME_ROLES:
            if record.get("allowed_product_behavior_change") is True:
                fail(errors, f"Runtime Doctor dispatch {record_id(record) or '<unknown>'} must not be authorized for broad product behavior changes")


def validate_task_queue_not_control_plane(state: dict[str, Any], errors: list[str]) -> None:
    """Prevent BAGEL governance work from being mistaken for the user's deliverable."""
    for i, item in enumerate(as_list(state.get("task_queue")), start=1):
        row = as_dict(item)
        text = " ".join(
            str(row.get(key) or "")
            for key in ("id", "title", "task", "description", "goal", "acceptance_criteria", "lane_type")
        ).lower()
        if row.get("lane_type") == "control_plane":
            fail(errors, f"task_queue item {i}: control_plane work must not live in the user-facing deliverable task_queue")
        for term in CONTROL_PLANE_TERMS:
            if term in text:
                fail(errors, f"task_queue item {i}: appears to treat BAGEL control-plane work as deliverable work ({term!r})")
                break


def validate_evaluation_and_iteration_state(root: Path, state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Build/iteration work must be governed by a project-specific evaluation system."""
    has_progress = (root / ".bagel" / "evidence" / "progress-deltas.yaml").exists()
    has_tasks = bool(as_list(state.get("task_queue")))
    run_status = state.get("run_status") or state.get("status")
    if not has_progress and not has_tasks and run_status not in {"excellence_loop", "complete"}:
        return

    evaluation = as_dict(state.get("evaluation"))
    evaluation_path = root / ".bagel" / "evaluation" / "current.yaml"
    if not evaluation and evaluation_path.exists():
        evaluation = as_dict(load_yaml(evaluation_path, {}))
    if not evaluation:
        fail(errors, "Build/iteration work has started but no active evaluation spec exists; dispatch Evaluation Architect before implementation")
    else:
        metrics = as_list(evaluation.get("metrics"))
        rubric = as_list(evaluation.get("qualitative_rubric"))
        if not metrics and not rubric:
            fail(errors, "active evaluation spec must include metrics and/or qualitative_rubric")
        if not evaluation.get("completion_rule"):
            fail(errors, "active evaluation spec missing completion_rule")
        for i, metric in enumerate(metrics, start=1):
            m = as_dict(metric)
            if not m.get("decision_use"):
                fail(errors, f"evaluation metric {i}: missing decision_use")
            if not m.get("anti_gaming_note"):
                fail(errors, f"evaluation metric {i}: missing anti_gaming_note")

    excel = as_dict(state.get("excellence"))
    max_iterations = excel.get("max_iterations") or as_dict(as_dict(load_yaml(root / ".bagel/constitution.yaml", {})).get("stop_contract")).get("max_iterations")
    iterations_completed = excel.get("iterations_completed")
    if run_status == "complete" and isinstance(max_iterations, int):
        if not isinstance(iterations_completed, int) or iterations_completed < max_iterations:
            fail(errors, f"run_status=complete but iterations_completed={iterations_completed!r} is below max_iterations={max_iterations}; completing preset goals is one iteration, not final completion")
    current_iteration = excel.get("current_iteration")
    if has_progress and current_iteration is None:
        warn(warnings, "state.excellence.current_iteration missing; iteration accounting may be ambiguous")


def validate_status_and_briefing(root: Path, state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    status_path = root / ".bagel/STATUS.md"
    if not status_path.exists():
        fail(errors, ".bagel/STATUS.md is missing")
        return
    status_text = status_path.read_text(encoding="utf-8")
    required = ["Morning Briefing", "Loop Binding", "Telemetry", "Next Action"]
    for section in required:
        if section not in status_text:
            fail(errors, f"STATUS.md missing required section: {section}")
    run_status = state.get("run_status") or state.get("status")
    if run_status and run_status not in VALID_STOP:
        fail(errors, f"state run status {run_status!r} is not a valid BAGEL status")
    if run_status == "complete":
        final_ref = state.get("final_judgment_ref") or as_dict(state.get("final_delivery")).get("judgment_ref")
        validate_judgment_record(root, final_ref, "final_delivery", errors)
    if "degraded_resume" in str(as_dict(state.get("loop_binding")).get("mode")) and "[DEGRADED" not in status_text:
        fail(errors, "degraded_resume must be visibly marked in STATUS.md")

    briefing = as_dict(as_dict(state.get("briefing")).get("html_dashboard"))
    if briefing.get("enabled") is True:
        path = root / ".bagel/user_briefing/alignment-dashboard.html"
        if not path.exists():
            fail(errors, "HTML dashboard enabled but .bagel/user_briefing/alignment-dashboard.html is missing")
        elif path.stat().st_size == 0:
            fail(errors, "HTML dashboard exists but is empty")
        owner = briefing.get("owner")
        if owner and owner != "User Alignment Curator":
            fail(errors, "HTML dashboard owner must be User Alignment Curator")


def validate_context_verified(root: Path, state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Verify that project understanding was built from real exploration, not doc-trusting.

    If the run has entered Build (task_queue non-empty or progress-deltas exist) but
    context.yaml shows no verification evidence (commands actually run), the Cartographer
    likely trusted documents instead of exploring. This catches the failure mode where
    stale/wrong docs silently corrupt the project model.
    """
    context_path = root / ".bagel" / "context.yaml"
    context = load_yaml(context_path, {})
    if not isinstance(context, dict) or not context:
        return  # not an existing-project takeover; skip

    # Only enforce once the run has progressed past discovery into Build
    deltas_path = root / ".bagel" / "evidence" / "progress-deltas.yaml"
    has_progress = deltas_path.exists() and deltas_path.stat().st_size > 0
    task_queue = as_list(state.get("task_queue"))
    if not has_progress and not task_queue:
        return  # still in discovery; not yet enforceable

    commands, manifest_exists = baseline_manifest(root)
    verified_commands = []
    all_not_available = len(commands) > 0
    for item in commands:
        command = item.get("command")
        output_path = item.get("output_path") or item.get("evidence")
        result = item.get("result") or item.get("verdict")
        exit_code_present = "exit_code" in item or result == "not_available"
        captured_at = item.get("captured_at") or item.get("executed_at") or item.get("created_at")
        if not command:
            fail(errors, "baseline manifest command entry is missing command")
            continue
        if not output_path:
            fail(errors, f"baseline manifest command {command!r} is missing output_path/evidence")
            continue
        evidence_path = root / str(output_path)
        if not evidence_path.exists() or evidence_path.stat().st_size == 0:
            fail(errors, f"baseline manifest command {command!r} points to missing/empty evidence: {output_path}")
            continue
        # P0-13: anti-fabrication heuristic - evidence must be >50 bytes (not a 1-byte placeholder)
        if result != "not_available" and evidence_path.stat().st_size < 50:
            fail(errors, f"baseline manifest command {command!r} evidence file is only {evidence_path.stat().st_size} bytes - too small to be real command output; likely fabricated")
        if ".bagel/evidence/baseline/" not in str(output_path):
            fail(errors, f"baseline evidence for {command!r} must live under .bagel/evidence/baseline/")
        if not exit_code_present:
            fail(errors, f"baseline manifest command {command!r} must record exit_code or result=not_available")
        if not captured_at:
            fail(errors, f"baseline manifest command {command!r} must record captured_at/executed_at")
        if result != "not_available":
            verified_commands.append(item)
        else:
            all_not_available = all_not_available and True

    if not manifest_exists:
        fail(errors, "missing .bagel/evidence/baseline/manifest.yaml; baseline command outputs must be indexed, not inferred from arbitrary files")
    elif not verified_commands:
        # P0-5: non-runnable projects (LaTeX, data notebooks, static sites with no build step)
        # may have ALL commands as not_available. Allow through only if the Cartographer
        # explicitly confirmed no runnable commands OR provisioned a local verifier.
        no_runnable_confirmed = context.get("no_runnable_commands_confirmed") is True
        verifiers_provisioned = as_list(context.get("verifiers_provisioned"))
        if all_not_available and (no_runnable_confirmed or verifiers_provisioned):
            warn(warnings, "all baseline commands are not_available; passed because no_runnable_commands_confirmed or verifiers_provisioned is set - verify this is a genuine non-runnable artifact, not laziness")
        else:
            fail(errors, "baseline manifest has no executed verifier command; at least one real command output is required before Build (if the project genuinely has no runnable commands, set context.no_runnable_commands_confirmed: true or provision a local verifier)")

    # Check for doc-vs-reality discrepancies recorded (proves verification happened)
    has_discrepancy_log = any(
        "discrepanc" in str(k).lower() or "discrepanc" in str(v).lower()
        for k, v in _flatten_items(context)
    )

    if not has_discrepancy_log and not verified_commands:
        fail(errors, "no doc-vs-reality discrepancies recorded AND no verified baseline commands — the Cartographer almost certainly did not verify findings against live code")

    explorers = [as_dict(item) for item in as_list(context.get("explorers_dispatched"))]
    records = collect_registry(root, state)
    for record in records:
        lens = record.get("lens")
        role = record_role(record).lower()
        if lens or "explorer" in role:
            explorers.append(record)
    lenses = {
        str(item.get("lens") or item.get("exploration_lens") or "").lower()
        for item in explorers
        if str(item.get("lens") or item.get("exploration_lens") or "").lower() in EXPLORER_LENSES
    }
    if len(lenses) < 2:
        fail(errors, "existing-project takeover requires >=2 recorded exploration lenses before Build")

    runtime_caps = as_dict(state.get("runtime_capabilities"))
    true_subagents = runtime_caps.get("supports_true_subagents")
    if true_subagents is not False:
        explorer_ids = {record_id(item) for item in explorers if record_id(item)}
        if len(lenses) >= 2 and len(explorer_ids) < 2:
            fail(errors, "exploration lenses were recorded but do not show >=2 distinct agent/session ids")


def _flatten_items(d: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    """Yield (key, value) pairs from nested dicts/lists for substring search."""
    out: list[tuple[str, Any]] = []
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else str(k)
        out.append((full, v))
        if isinstance(v, dict):
            out.extend(_flatten_items(v, full))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    out.extend(_flatten_items(item, f"{full}[{i}]"))
    return out


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    if not bagel.exists():
        return ["no .bagel/ directory found; BAGEL run state does not exist"], []
    state = load_yaml(bagel / "state.yaml", {})
    if not isinstance(state, dict):
        return [".bagel/state.yaml is missing or malformed"], []
    errors: list[str] = []
    warnings: list[str] = []
    validate_git(root, state, errors)
    validate_loop(state, errors, warnings)
    validate_alignment_floor(state, errors, warnings)
    validate_stop_contract(root, state, errors, warnings)
    validate_dispatch(root, state, errors, warnings)
    validate_task_queue_not_control_plane(state, errors)
    validate_evaluation_and_iteration_state(root, state, errors, warnings)
    validate_context_verified(root, state, errors, warnings)
    validate_status_and_briefing(root, state, errors, warnings)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Project root containing .bagel/")
    parser.add_argument("--strict-warnings", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors, warnings = validate(root)
    for message in warnings:
        print(f"WARN: {message}", file=sys.stderr)
    for message in errors:
        print(f"FAIL: {message}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL run check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
