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
        if ".bagel/evidence/baseline/" not in str(output_path):
            fail(errors, f"baseline evidence for {command!r} must live under .bagel/evidence/baseline/")
        if not exit_code_present:
            fail(errors, f"baseline manifest command {command!r} must record exit_code or result=not_available")
        if not captured_at:
            fail(errors, f"baseline manifest command {command!r} must record captured_at/executed_at")
        if result != "not_available":
            verified_commands.append(item)

    if not manifest_exists:
        fail(errors, "missing .bagel/evidence/baseline/manifest.yaml; baseline command outputs must be indexed, not inferred from arbitrary files")
    elif not verified_commands:
        fail(errors, "baseline manifest has no executed verifier command; at least one real command output is required before Build")

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
    validate_dispatch(root, state, errors, warnings)
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
