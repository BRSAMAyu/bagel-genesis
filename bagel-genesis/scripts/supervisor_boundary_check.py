#!/usr/bin/env python3
"""Validate that the root Supervisor did not perform Orchestrator/worker work."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


ALLOWED_SUPERVISOR_ACTIONS = {
    "align_user",
    "normalize_user_instruction",
    "bind_heartbeat",
    "spawn_orchestrator",
    "respawn_orchestrator",
    "hard_stop_arbitration",
    "status_proxy",
    "resume_capsule_update",
}
FORBIDDEN_TERMS = {
    "npm test",
    "pytest",
    "mvn",
    "gradle",
    "package install",
    "browser screenshot",
    "runtime debug",
    "implementation",
    "code edit",
    "product test",
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


def collect_actions(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    for path in (root / ".bagel/supervisor").glob("*.yaml") if (root / ".bagel/supervisor").exists() else []:
        data = load_yaml(path, {})
        if isinstance(data, dict):
            for key in ("actions", "supervisor_actions", "events"):
                for item in as_list(data.get(key)):
                    out.append((path, as_dict(item)))
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    supervisor = as_dict(state.get("supervisor"))
    for item in as_list(supervisor.get("actions") or supervisor.get("events")):
        out.append((root / ".bagel/state.yaml#supervisor", as_dict(item)))
    return out


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    supervisor = as_dict(state.get("supervisor"))
    heartbeat = as_dict(load_yaml(root / ".bagel/supervisor/heartbeat.yaml", {}))
    mode = supervisor.get("mode") or heartbeat.get("mode")
    if mode != "nested_supervisor" and not (root / ".bagel/supervisor").exists():
        return errors, warnings
    actions = collect_actions(root)
    if not actions:
        if mode == "nested_supervisor":
            errors.append("nested_supervisor requires an auditable Supervisor action log")
        else:
            warnings.append("no supervisor action log found; cannot audit Supervisor boundary")
        return errors, warnings
    has_spawn = False
    for path, action in actions:
        kind = str(action.get("action_type") or action.get("type") or "")
        text = " ".join(str(v).lower() for v in action.values())
        if kind and kind not in ALLOWED_SUPERVISOR_ACTIONS:
            errors.append(f"{path}: Supervisor action_type {kind!r} is outside allowed boundary")
        guard = as_dict(action.get("role_guard"))
        if mode == "nested_supervisor":
            if not guard:
                errors.append(f"{path}: Supervisor action missing role_guard")
            elif guard.get("current_role") != "Supervisor":
                errors.append(f"{path}: role_guard.current_role must be Supervisor")
            if action.get("task_size_exemption_used") is True or guard.get("task_size_exemption_used") is True:
                errors.append(f"{path}: task size is never a Supervisor boundary exemption")
            if guard.get("current_skill_overrides_stale_state") is not True:
                errors.append(f"{path}: role_guard must affirm current_skill_overrides_stale_state=true")
            if guard.get("allowed_by_supervisor_boundary") is not True:
                errors.append(f"{path}: role_guard.allowed_by_supervisor_boundary must be true for Supervisor-owned actions")
        if kind in {"spawn_orchestrator", "respawn_orchestrator"}:
            has_spawn = True
            if not (
                action.get("orchestrator_agent_id")
                and (action.get("orchestrator_session_id") or action.get("session_id"))
            ):
                errors.append(f"{path}: {kind} must record orchestrator_agent_id and orchestrator_session_id")
            if not (action.get("dispatch_ref") or action.get("handoff_ref") or action.get("resume_capsule_ref")):
                errors.append(f"{path}: {kind} must cite dispatch_ref, handoff_ref, or resume_capsule_ref")
        for term in FORBIDDEN_TERMS:
            if term in text:
                errors.append(f"{path}: Supervisor action appears to perform forbidden worker/orchestrator work: {term}")
    if mode == "nested_supervisor" and not has_spawn:
        errors.append("nested_supervisor requires a recorded spawn_orchestrator or respawn_orchestrator action")
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
    print("BAGEL supervisor boundary check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
