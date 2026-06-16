#!/usr/bin/env python3
"""Validate that claimed deliverable deltas are backed by non-control-plane diff/evidence."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


DOC_EXTS = {".md", ".txt", ".rst"}


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


def git_changed_paths(root: Path, ref: str | None) -> list[str]:
    if not ref:
        return []
    try:
        result = subprocess.run(["git", "-C", str(root), "diff", "--name-only", ref, "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []
    return []


def collect_cycles(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in (root / ".bagel/telemetry").glob("cycles*.yaml") if (root / ".bagel/telemetry").exists() else []:
        data = load_yaml(path, {})
        rows = data.get("cycles") if isinstance(data, dict) else data
        out.extend(as_dict(item) for item in as_list(rows))
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    out.extend(as_dict(item) for item in as_list(as_dict(state.get("telemetry")).get("cycles")))
    return [row for row in out if row]


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for i, cycle in enumerate(collect_cycles(root), start=1):
        outputs = as_dict(cycle.get("outputs"))
        if outputs.get("deliverable_delta") is not True:
            continue
        detail = as_dict(outputs.get("deliverable_delta_detail") or outputs.get("deliverable_delta"))
        changed = as_list(detail.get("changed_paths"))
        diff_ref = detail.get("git_diff_ref") or cycle.get("git_ref_start")
        if not changed:
            changed = git_changed_paths(root, str(diff_ref) if diff_ref else None)
        non_control = [p for p in changed if not str(p).startswith(".bagel/")]
        if not non_control:
            errors.append(f"cycle {i}: deliverable_delta=true but changed_paths are empty or control-plane-only")
        if not detail.get("artifact_surface_changed") and not detail.get("user_visible_or_metric_relevant"):
            errors.append(f"cycle {i}: deliverable_delta requires artifact_surface_changed or user_visible_or_metric_relevant")
        if not as_list(detail.get("evidence_refs") or outputs.get("evidence_refs")):
            errors.append(f"cycle {i}: deliverable_delta requires evidence_refs")
        artifact_type = str(detail.get("artifact_type") or cycle.get("artifact_type") or "")
        if non_control and all(Path(p).suffix in DOC_EXTS for p in non_control) and artifact_type not in {"writing", "research", "document_deck", "docs"}:
            warnings.append(f"cycle {i}: deliverable_delta only changed docs/text; confirm docs are the deliverable")
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
    print("BAGEL deliverable delta check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
