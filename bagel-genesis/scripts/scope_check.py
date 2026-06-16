#!/usr/bin/env python3
"""Validate V2 scope deltas and hard-stop boundaries."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


SENSITIVE_KEYS = ("auth", "privacy", "payment", "production_data", "data_migration")


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


def collect_scope(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    for base in (root / ".bagel/scope", root / ".bagel/actions"):
        if base.exists():
            for path in sorted(base.rglob("*.yaml")):
                data = load_yaml(path, {})
                rows = as_list(data.get("scope_deltas")) if isinstance(data, dict) and "scope_deltas" in data else [data]
                for row in rows:
                    rec = as_dict(row.get("scope_delta")) if isinstance(row, dict) and "scope_delta" in row else as_dict(row)
                    if rec:
                        out.append((path, rec))
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    for row in as_list(state.get("scope_deltas")):
        out.append((root / ".bagel/state.yaml#scope_deltas", as_dict(row)))
    return out


def is_safe_rel(path: str) -> bool:
    p = Path(path)
    return not p.is_absolute() and ".." not in p.parts and str(path).strip() not in {"", "."}


def path_allowed(path: str, allowed: list[str]) -> bool:
    p = Path(path)
    for item in allowed:
        base = Path(item)
        if p == base or base in p.parents:
            return True
    return False


def git_changed_paths(root: Path, ref: str | None) -> list[str]:
    if not ref:
        return []
    try:
        result = subprocess.run(["git", "-C", str(root), "diff", "--name-only", ref, "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        changed = [line.strip() for line in result.stdout.splitlines() if line.strip()] if result.returncode == 0 else []
        untracked = subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        if untracked.returncode == 0:
            changed.extend(line.strip() for line in untracked.stdout.splitlines() if line.strip())
        return sorted(path for path in set(changed) if not path.startswith(".bagel/"))
    except Exception:
        return []


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for path, rec in collect_scope(root):
        allowed = [str(item) for item in as_list(rec.get("allowed_paths"))]
        touched = [str(item) for item in as_list(rec.get("touched_paths"))]
        actual = git_changed_paths(root, str(rec.get("git_ref_start"))) if rec.get("git_ref_start") else []
        if actual:
            touched = sorted(set(touched) | set(actual))
        outside = sorted(set(str(item) for item in as_list(rec.get("touched_paths_outside_scope"))))
        if not allowed:
            errors.append(f"{path}: allowed_paths is required for scope enforcement")
        for item in allowed + touched:
            if not is_safe_rel(item):
                errors.append(f"{path}: path must be normalized relative path, got {item!r}")
        derived_outside = [item for item in touched if allowed and not path_allowed(item, allowed)]
        if derived_outside:
            outside = sorted(set(outside) | set(derived_outside))
        if outside and not rec.get("approval_ref"):
            errors.append(f"{path}: touched_paths_outside_scope requires approval_ref")
        deps = as_list(rec.get("new_dependencies"))
        dep_scope = rec.get("dependency_scope")
        if deps and dep_scope in {None, "", "runtime", "major_framework"} and not rec.get("dependency_justification"):
            errors.append(f"{path}: new runtime/major dependency requires dependency_justification")
        if rec.get("architecture_boundary_changed") is True and not rec.get("approval_ref"):
            errors.append(f"{path}: architecture boundary change requires approval_ref")
        if rec.get("product_identity_changed") is True and not rec.get("constitutional_court_ref"):
            errors.append(f"{path}: product identity change requires constitutional_court_ref")
        sensitive = [key for key in SENSITIVE_KEYS if rec.get(f"{key}_touched") is True or rec.get(key) is True]
        if sensitive and not rec.get("explicit_contract_ref"):
            errors.append(f"{path}: sensitive scope touched ({', '.join(sensitive)}) without explicit_contract_ref")
        if rec.get("approval_required") is True and not rec.get("approval_ref"):
            errors.append(f"{path}: approval_required=true but approval_ref missing")
        if derived_outside and sorted(as_list(rec.get("touched_paths_outside_scope"))) != outside:
            errors.append(f"{path}: touched_paths_outside_scope does not match derived git diff outside scope: {outside}")
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
    print("BAGEL scope check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
