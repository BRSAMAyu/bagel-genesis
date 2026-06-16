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
    "wake_user_for_hard_stop",
    "status_proxy",
    "resume_capsule_update",
    "create_minimal_bagel_directories",
    "write_initial_state",
    "write_initial_supervisor_heartbeat",
    "write_bootstrap_role_guard_marker",
}
PREBOOT_ACTIONS = {
    "create_minimal_bagel_directories",
    "write_initial_state",
    "write_initial_supervisor_heartbeat",
    "write_bootstrap_role_guard_marker",
}
FORBIDDEN_TERMS = {
    "npm test",
    "pnpm test",
    "yarn test",
    "bun test",
    "pytest",
    "uv run pytest",
    "mvn",
    "gradle",
    "go test",
    "cargo test",
    "make test",
    "deno test",
    "dotnet test",
    "package install",
    "npm install",
    "pip install",
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


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(walk_strings(item))
        return out
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(walk_strings(item))
        return out
    return [str(value).lower()]


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
        text = " ".join(walk_strings(action))
        if kind and kind not in ALLOWED_SUPERVISOR_ACTIONS:
            errors.append(f"{path}: Supervisor action_type {kind!r} is outside allowed boundary")
        guard = as_dict(action.get("role_guard"))
        preboot = bool(action.get("pre_boot_exemption")) or kind in PREBOOT_ACTIONS
        if preboot:
            if kind not in PREBOOT_ACTIONS:
                errors.append(f"{path}: pre_boot_exemption used for non-preboot action {kind!r}")
            for forbidden in ("product_file_edit", "tests", "runtime_debug", "dependency_install", "project_file_read", "product_file_write"):
                if action.get(forbidden) is True:
                    errors.append(f"{path}: pre_boot_exemption forbids {forbidden}")
        else:
            # P0-4: schema enforcement for post-bootstrap Supervisor actions.
            # Supervisor must delegate, not execute product/test/debug work directly.
            if action.get("command_executed") is True:
                errors.append(f"{path}: post-bootstrap Supervisor action command_executed=true is forbidden (delegate to Orchestrator)")
            product_read = as_list(action.get("product_files_read"))
            product_written = as_list(action.get("product_files_written"))
            if product_read:
                errors.append(f"{path}: Supervisor read product files {product_read} (forbidden; delegate to Orchestrator)")
            if product_written:
                errors.append(f"{path}: Supervisor wrote product files {product_written} (forbidden; delegate to Orchestrator)")
            tools_used = [str(t).lower() for t in as_list(action.get("tools_used"))]
            for tool in tools_used:
                if tool in {"edit", "write"} or (tool == "bash" and any(
                    term in text for term in FORBIDDEN_TERMS
                )):
                    errors.append(f"{path}: Supervisor used tool {tool!r} on product/test work (forbidden)")
            # Supervisor actions must record delegation intent
            if action.get("delegated_to_orchestrator") is False and kind not in {"status_proxy", "resume_capsule_update"}:
                errors.append(f"{path}: post-bootstrap Supervisor action should delegate_to_orchestrator=true (kind={kind!r})")
        if mode == "nested_supervisor" and not preboot:
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
    if mode == "nested_supervisor":
        bootstrap_done = any(
            as_dict(action).get("bootstrap_complete") is True
            or as_dict(action).get("action_type") == "write_bootstrap_role_guard_marker"
            for _, action in actions
        )
        if not bootstrap_done:
            errors.append("nested_supervisor requires bootstrap_complete marker after pre-boot setup")
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
