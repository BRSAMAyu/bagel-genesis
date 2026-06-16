#!/usr/bin/env python3
"""Preflight BAGEL dispatch envelopes before workers start."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


IMPLEMENTER_ROLES = {"Implementer", "Skeleton Builder"}
SUPERVISOR_FORBIDDEN_OWNERS = IMPLEMENTER_ROLES | {"Runtime Doctor", "Spec Reviewer", "Code Quality Reviewer", "Independent Reviewer"}


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


def normalized_rel(path: str) -> bool:
    p = Path(path)
    return bool(path) and not p.is_absolute() and ".." not in p.parts


def paths_overlap(a: str, b: str) -> bool:
    """P0-5: detect parent/child path conflicts, not just exact matches."""
    pa, pb = Path(a), Path(b)
    return a == b or pa in pb.parents or pb in pa.parents


def collect(root: Path, state: dict[str, Any]) -> list[tuple[Path, dict[str, Any]]]:
    rows: list[tuple[Path, dict[str, Any]]] = []
    for item in as_list(state.get("dispatch_envelopes")) + as_list(state.get("dispatches")):
        rows.append((root / ".bagel/state.yaml", as_dict(item)))
    d = root / ".bagel/agents/dispatches"
    if d.exists():
        for path in sorted(d.glob("*.yaml")):
            rows.append((path, as_dict(load_yaml(path, {}))))
    return [(p, r) for p, r in rows if r]


def lock_exists(root: Path, lock: Any) -> bool:
    if isinstance(lock, str):
        return (root / ".bagel/git/locks" / lock).is_dir() or (root / lock).exists()
    row = as_dict(lock)
    resource = row.get("resource") or row.get("resource_id")
    if resource and (root / ".bagel/git/locks" / str(resource)).is_dir():
        return True
    ref = row.get("lock_ref")
    return bool(ref and (root / str(ref)).exists())


def validate(root: Path) -> tuple[list[str], list[str]]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    rows = collect(root, state)
    errors: list[str] = []
    warnings: list[str] = []
    active_writes: dict[str, str] = {}
    if not rows:
        # C1 finding (Judge S2+S5): omission-as-pass. If build evidence exists (parallel/
        # dispatched work started) but NO dispatch envelopes were recorded, warn — an agent
        # that dispatches workers without envelopes bypasses path-overlap and role-boundary
        # checks. This is a warning (not error) because quick serial work may legitimately
        # not use envelopes; full_genesis/parallel_advanced with zero envelopes is suspicious.
        run_mode = str(state.get("run_mode") or state.get("bagel_mode") or "").lower()
        has_build_evidence = (root / ".bagel/evidence/progress-deltas.yaml").exists()
        if has_build_evidence and run_mode in {"full_genesis", "full", "parallel_advanced", "parallel"}:
            warnings.append(
                "dispatch_envelope_valid: build evidence exists in full/parallel mode but NO dispatch "
                "envelopes were recorded. Workers dispatched without envelopes bypass path-overlap and "
                "role-boundary checks. Record a dispatch envelope for each dispatched worker."
            )
        return errors, warnings
    for path, env in rows:
        label = str(path.relative_to(root)) if path.is_absolute() and root in path.parents else str(path)
        for field in ("role", "agent_id", "task_id", "exit_criteria"):
            if not env.get(field):
                errors.append(f"{label}: dispatch envelope missing {field}")
        role = str(env.get("role") or "")
        # P0-6: prefer structured git_target over ambiguous branch_or_worktree
        git_target = as_dict(env.get("git_target"))
        if git_target:
            gtype = str(git_target.get("type") or "")
            if gtype == "worktree":
                wpath = git_target.get("worktree_path")
                if wpath and not (root / str(wpath)).exists():
                    errors.append(f"{label}: git_target worktree_path does not exist: {wpath}")
            elif gtype == "branch":
                # branch names may contain '/'; validate as a branch name, not a filesystem path
                bname = str(git_target.get("branch") or "")
                if bname and (".." in bname or bname.startswith("/") or bname.endswith(".lock")):
                    errors.append(f"{label}: git_target branch name is invalid: {bname}")
            elif gtype == "current":
                # only valid for serial / non-parallel-safe work
                if as_list(env.get("locks")) and not env.get("parallel_safe"):
                    pass  # current with locks is fine for serial work
            else:
                errors.append(f"{label}: git_target.type must be branch|worktree|current; got {gtype!r}")
        else:
            # legacy fallback: branch_or_worktree
            branch = env.get("branch_or_worktree") or env.get("worktree") or env.get("branch")
            if branch and "/" in str(branch):
                errors.append(f"{label}: use git_target.type=branch for branch names containing '/'; ambiguous branch_or_worktree={branch} treated as path")
        read_paths = as_list(env.get("read_only") or env.get("allowed_read_paths") or env.get("read"))
        for p in read_paths:
            if not isinstance(p, str):
                continue
            if p in {"SKILL.md"} or p.startswith("references/"):
                if role in IMPLEMENTER_ROLES:
                    errors.append(f"{label}: {role} cannot read global skill/reference context")
            if normalized_rel(p) and not (root / p).exists() and not p.startswith(".bagel/agent_context"):
                errors.append(f"{label}: read path does not exist: {p}")
        write_paths = as_list(env.get("write_only") or env.get("allowed_paths") or env.get("allowed_write_paths"))
        for p in write_paths:
            if not isinstance(p, str) or not normalized_rel(p):
                errors.append(f"{label}: write/allowed path must be normalized relative path: {p!r}")
                continue
            # P0-5: check parent/child overlap against ALL active write paths
            for existing_path, existing_owner in active_writes.items():
                if existing_owner != str(env.get("agent_id")) and paths_overlap(p, existing_path):
                    errors.append(f"{label}: write path {p!r} overlaps active worker {existing_owner} path {existing_path!r}")
            active_writes[p] = str(env.get("agent_id"))
        for p in as_list(env.get("forbidden_paths")):
            if isinstance(p, str) and not normalized_rel(p):
                errors.append(f"{label}: forbidden path must be normalized relative path: {p!r}")
        context_refs = as_list(env.get("context_refs"))
        for ref in context_refs:
            if isinstance(ref, str) and not (root / ref).exists():
                errors.append(f"{label}: context_ref does not exist: {ref}")
        if write_paths and not as_list(env.get("locks")):
            errors.append(f"{label}: write dispatch requires locks")
        for lock in as_list(env.get("locks")):
            if not lock_exists(root, lock):
                errors.append(f"{label}: lock missing or not atomically acquired: {lock}")
        if env.get("dispatcher_role") == "Supervisor" and role in SUPERVISOR_FORBIDDEN_OWNERS:
            errors.append(f"{label}: Supervisor cannot dispatch itself or directly own {role} work")
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
    print("BAGEL dispatch envelope check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
