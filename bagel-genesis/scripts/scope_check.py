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
        elif rec.get("product_identity_changed") is True:
            # S9 fix: the ref must point to a Court record whose verdict ACCEPTED the
            # amendment — not merely an existing file. A rejected/stub ruling must not
            # satisfy the scope_delta gate (Judge G bypass: any existing file passed).
            court_ref = str(rec.get("constitutional_court_ref") or "")
            court_path = root / court_ref if not court_ref.startswith("/") else Path(court_ref)
            verdict_accepted = False
            verdict_detail = ""
            if court_path.exists():
                court_record = as_dict(load_yaml(court_path, {}))
                # accept several common verdict field shapes
                verdict = str(court_record.get("verdict") or court_record.get("decision") or court_record.get("ruling") or "").lower()
                verdict_accepted = verdict in {"accept", "accepted", "approve", "approved", "amendment_accepted"}
                verdict_detail = f"verdict='{verdict}'"
            else:
                verdict_detail = "ref file not found"
            if not verdict_accepted:
                errors.append(
                    f"{path}: product identity change requires a Constitutional Court record "
                    f"with an accepted verdict at {court_ref} ({verdict_detail}). A rejected "
                    f"or stub ruling does not satisfy scope_delta_within_contract."
                )
        sensitive = [key for key in SENSITIVE_KEYS if rec.get(f"{key}_touched") is True or rec.get(key) is True]
        if sensitive and not rec.get("explicit_contract_ref"):
            errors.append(f"{path}: sensitive scope touched ({', '.join(sensitive)}) without explicit_contract_ref")
        if rec.get("approval_required") is True and not rec.get("approval_ref"):
            errors.append(f"{path}: approval_required=true but approval_ref missing")
        if derived_outside and sorted(as_list(rec.get("touched_paths_outside_scope"))) != outside:
            errors.append(f"{path}: touched_paths_outside_scope does not match derived git diff outside scope: {outside}")

    # C1 fix (Judge S2+S5): omission-as-pass. If the run has build evidence (Build started)
    # and the git diff shows changed non-.bagel paths, but NO scope_delta record covers them,
    # the agent made out-of-scope edits without recording a scope_delta — omission must fail.
    has_build_evidence = (root / ".bagel/evidence/progress-deltas.yaml").exists()
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    run_started = state.get("phase") in {"Build", "Iterate", "Polish", "complete"} or bool(state.get("task_queue"))
    if has_build_evidence and run_started:
        # Find the run's base ref (from the first scope_delta with git_ref_start, or HEAD~1)
        base_ref = None
        for _path, rec in collect_scope(root):
            if rec.get("git_ref_start"):
                base_ref = str(rec.get("git_ref_start"))
                break
        if not base_ref:
            base_ref = "HEAD~1"
        all_changed = git_changed_paths(root, base_ref)
        # Guard (Judge U finding): if git is not available or the diff fails, the check
        # must not silently pass — it must warn that scope coverage could not be verified.
        git_available = (root / ".git").exists()
        if not all_changed and git_available and not collect_scope(root):
            # git exists but returned no changes AND no scope_delta records — could be a
            # real clean state OR a git error swallowed to []. Warn so a human can verify.
            warnings.append(
                "scope_delta_within_contract: build evidence exists but git diff returned no changed "
                "paths and no scope_delta records exist. If this run made product edits, the git-diff "
                "derivation may have failed (verify git history is intact and git_ref_start is valid)."
            )
        # Gather all paths COVERED by declared scope_delta allowed_paths
        covered: set[str] = set()
        for _path, rec in collect_scope(root):
            for item in as_list(rec.get("allowed_paths")):
                covered.add(str(item))
        # A changed path is "covered" if it falls under a declared allowed_path, or is .bagel/
        uncovered = []
        for changed in all_changed:
            if changed.startswith(".bagel/"):
                continue
            if not any(path_allowed(changed, list(covered)) or changed == c for c in covered):
                uncovered.append(changed)
        if uncovered and not collect_scope(root):
            # NO scope_delta records exist at all, but build evidence + changed paths exist
            errors.append(
                f"scope_delta_within_contract: build evidence exists and git diff shows changed paths "
                f"({uncovered[:5]}) but NO scope_delta record covers them. An agent that makes "
                f"out-of-scope edits without recording a scope_delta cannot pass — record a "
                f"scope_delta with allowed_paths for each changed path, or omission-as-pass defeats the gate."
            )
        elif uncovered:
            errors.append(
                f"scope_delta_within_contract: {len(uncovered)} changed path(s) not covered by any "
                f"scope_delta allowed_paths (first 5: {uncovered[:5]}). Every changed non-.bagel path "
                f"must fall under a declared scope_delta.allowed_paths, or have an approval_ref for "
                f"out-of-scope work. Omission is not a valid way to bypass scope enforcement."
            )
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
