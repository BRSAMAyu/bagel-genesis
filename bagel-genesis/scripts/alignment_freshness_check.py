#!/usr/bin/env python3
"""Validate V2 alignment freshness and taste drift records."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
import hashlib


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    if not bagel.exists():
        return [], []
    state = as_dict(load_yaml(bagel / "state.yaml", {}))
    freshness = as_dict(state.get("alignment_freshness"))
    if not freshness:
        freshness = as_dict(load_yaml(bagel / "alignment/freshness.yaml", {}))
    errors: list[str] = []
    warnings: list[str] = []
    run_status = state.get("run_status") or state.get("status")
    if run_status in {"excellence_loop", "complete"} and not freshness:
        errors.append("alignment_freshness is required before excellence/final delivery")
        return errors, warnings
    if not freshness:
        return errors, warnings
    consistency = as_dict(freshness.get("consistency"))
    for key in ("vision", "non_goals", "taste", "autonomy_contract"):
        value = consistency.get(key)
        if value not in {"pass", "drift_risk", "fail"}:
            errors.append(f"alignment_freshness.consistency.{key} must be pass|drift_risk|fail")
        if value == "fail":
            errors.append(f"alignment_freshness reports {key}=fail")
    if not freshness.get("reviewer_ref"):
        errors.append("alignment_freshness requires reviewer_ref; self-score is not enough")
    # P0-7: domain freshness hard-enforce by expert layer mode
    mode = str(state.get("expert_layer_mode") or as_dict(state.get("bagel_worth_it_check")).get("expert_layer_mode") or "standard")
    hard = mode in {"standard", "full"}
    missing_hashes = []
    if not freshness.get("constitution_hash"):
        missing_hashes.append("constitution_hash")
    if not freshness.get("taste_kernel_hash"):
        missing_hashes.append("taste_kernel_hash")
    if missing_hashes:
        if hard:
            errors.append(f"alignment_freshness missing {missing_hashes} (standard/full mode requires both)")
        else:
            warnings.append(f"alignment_freshness missing {missing_hashes}")
    domain = as_dict(load_yaml(bagel / "expert/domain-excellence.yaml", {}))
    if domain:
        current_constitution = file_hash(bagel / "constitution.yaml") or file_hash(bagel / "constitution.json")
        if current_constitution and domain.get("constitution_hash") and domain.get("constitution_hash") != current_constitution:
            errors.append("domain_excellence_model constitution_hash is stale; refresh domain model before continuing")
        # P0-7: in standard/full, missing constitution_hash on domain model is also a fail (not just staleness)
        if hard and not domain.get("constitution_hash"):
            errors.append("domain_excellence_model missing constitution_hash (standard/full mode requires it)")
        if hard and not domain.get("artifact_profile_hash") and (bagel / "artifact_profile.yaml").exists():
            errors.append("domain_excellence_model missing artifact_profile_hash while artifact_profile exists (standard/full mode requires it)")
        artifact_profile = file_hash(bagel / "artifact_profile.yaml")
        if artifact_profile and domain.get("artifact_profile_hash") and domain.get("artifact_profile_hash") != artifact_profile:
            errors.append("domain_excellence_model artifact_profile_hash is stale; refresh domain model before continuing")
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
    print("BAGEL alignment freshness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
