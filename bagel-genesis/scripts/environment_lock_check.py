#!/usr/bin/env python3
"""Require reproducibility environment capture for started research runs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


RESEARCH_SIGNALS = ("research", "experiment", "benchmark", "study", "analysis")


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if data is None else data


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def is_research_like(root: Path) -> bool:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    constitution = as_dict(load_yaml(root / ".bagel/constitution.yaml", {}))
    profile = str(as_dict(state.get("artifact_profile")).get("type") or constitution.get("artifact_type") or "").lower()
    return (root / ".bagel/research").exists() or any(signal in profile for signal in RESEARCH_SIGNALS)


def build_started(root: Path) -> bool:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    phase = str(state.get("run_phase") or state.get("phase") or "").lower()
    if phase in {"build", "iterate", "polish", "excellence_loop", "complete"}:
        return True
    return (root / ".bagel/evidence/progress-deltas.yaml").exists()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if not is_research_like(root):
        print("environment_lock_check: not research-like; skipped")
        return 0
    if not build_started(root):
        print("environment_lock_check: pre-Build research run; skipped")
        return 0

    path = root / ".bagel/research/environment-lock.yaml"
    data = as_dict(load_yaml(path, {}))
    lock = as_dict(data.get("environment_lock")) or data
    errors: list[str] = []
    if not lock:
        errors.append("environment_lock: .bagel/research/environment-lock.yaml is required once research Build starts")
    if lock and lock.get("schema_version") != "research_environment_lock_v1":
        errors.append("environment_lock: schema_version must be research_environment_lock_v1")
    for field in ("python_version", "platform", "package_freeze_sha256", "created_at"):
        if not str(lock.get(field) or "").strip():
            errors.append(f"environment_lock: missing {field}")
    freeze_sha = str(lock.get("package_freeze_sha256") or "")
    if freeze_sha and not re.fullmatch(r"[a-f0-9]{64}", freeze_sha):
        errors.append("environment_lock: package_freeze_sha256 must be 64 lowercase hex")
    flags = as_dict(lock.get("determinism"))
    for field in ("pythonhashseed", "seed_policy", "torch_deterministic"):
        if field not in flags:
            errors.append(f"environment_lock: determinism.{field} is required")

    if errors:
        print("environment_lock_check failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("environment_lock_check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
