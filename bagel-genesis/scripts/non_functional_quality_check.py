#!/usr/bin/env python3
"""Validate non-functional quality gates (C7: accessibility, performance, i18n).

Judge S5 found these dimensions were mentioned across 15+ files but NEVER gated.
For UI/software artifacts, an inaccessible UI or performance regression passed all
53 gates. This validator adds a declaration-based floor: the agent declares a
non_functional_quality record with baseline metrics; regressions fail the cycle.

This does NOT run axe-core/Lighthouse (that requires platform tooling). It enforces
that the agent DECLARES and TRACKS these dimensions — omission is caught, regression
is caught. The human/agent still runs the actual measurement tools.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


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


# Artifact types that require non-functional quality gates
UI_TYPES = {"design_ui", "ui", "frontend", "web_app", "website", "mobile_app"}
SOFTWARE_TYPES = {"software_product", "software", "app", "service", "api", "cli", "backend"}

# Required NFR dimensions per artifact type
REQUIRED_NFR = {
    "ui": {
        "accessibility": ("contrast_ratio_min", "keyboard_nav_complete", "screen_reader_labels"),
        "responsive": ("breakpoints_tested", "min_width_supported"),
    },
    "software": {
        "performance": ("p95_latency_ms", "throughput_rps"),
    },
}


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    errors: list[str] = []
    warnings: list[str] = []
    if not bagel.exists():
        return errors, warnings
    state = as_dict(load_yaml(bagel / "state.yaml", {}))
    if state.get("phase") not in {"Build", "Iterate", "Polish", "complete"} and not state.get("task_queue"):
        return errors, warnings

    artifact_type = str(
        as_dict(state.get("artifact_profile")).get("type")
        or as_dict(load_yaml(bagel / "constitution.yaml", {})).get("artifact_type")
        or ""
    ).lower()

    is_ui = any(t in artifact_type for t in UI_TYPES)
    is_software = any(t in artifact_type for t in SOFTWARE_TYPES)
    if not (is_ui or is_software):
        return errors, warnings  # NFR gates only apply to UI/software artifacts

    nfr_path = bagel / "expert" / "non-functional-quality.yaml"
    nfr = as_dict(load_yaml(nfr_path, {}))

    # Phase 1: once Build has started + an iteration is complete, the NFR record MUST exist
    has_iteration = bool(as_dict(state.get("excellence")).get("iterations_completed"))
    progress_exists = (bagel / "evidence/progress-deltas.yaml").exists()
    if (has_iteration or progress_exists) and not nfr_path.exists():
        dims = []
        if is_ui:
            dims.extend(["accessibility (contrast/keyboard/screen-reader)", "responsive (breakpoints)"])
        if is_software:
            dims.append("performance (latency/throughput)")
        errors.append(
            f"non_functional_quality: artifact type '{artifact_type}' requires a non-functional quality "
            f"record at .bagel/expert/non-functional-quality.yaml tracking: {dims}. These dimensions were "
            f"mentioned in the expert pack but never gated — declare a baseline so regressions are caught."
        )
        return errors, warnings

    if not nfr:
        return errors, warnings

    # Phase 2: validate declared dimensions have required fields + check regression
    if is_ui:
        _check_dimension(nfr, "accessibility", REQUIRED_NFR["ui"]["accessibility"], errors, "ui")
        _check_dimension(nfr, "responsive", REQUIRED_NFR["ui"]["responsive"], errors, "ui")
    if is_software:
        _check_dimension(nfr, "performance", REQUIRED_NFR["software"]["performance"], errors, "software")

    # Phase 3: regression check — current values must not be worse than baseline
    for dim_name, dim_data in as_dict(nfr.get("dimensions") or nfr).items():
        dim = as_dict(dim_data)
        baseline = as_dict(dim.get("baseline"))
        current = as_dict(dim.get("current"))
        if not baseline or not current:
            continue
        for metric, base_val in baseline.items():
            if not isinstance(base_val, (int, float)):
                continue
            curr_val = current.get(metric)
            if not isinstance(curr_val, (int, float)):
                continue
            # For latency/time metrics: lower is better (current > baseline = regression)
            # For contrast/completeness metrics: higher is better (current < baseline = regression)
            lower_is_better = any(k in metric.lower() for k in ("latency", "time", "error", "overflow", "missing"))
            if lower_is_better and curr_val > base_val * 1.1:  # 10% tolerance
                errors.append(
                    f"non_functional_quality: {dim_name}.{metric} regressed from baseline {base_val} to {curr_val} "
                    f"(lower is better; >10% regression). A non-functional quality regression fails the cycle."
                )
            elif not lower_is_better and curr_val < base_val * 0.9:  # 10% tolerance
                errors.append(
                    f"non_functional_quality: {dim_name}.{metric} regressed from baseline {base_val} to {curr_val} "
                    f"(higher is better; >10% regression). A non-functional quality regression fails the cycle."
                )

    return errors, warnings


def _check_dimension(nfr: dict[str, Any], dim_name: str, required_fields: tuple[str, ...], errors: list[str], category: str) -> None:
    dims = as_dict(nfr.get("dimensions") or nfr)
    dim = as_dict(dims.get(dim_name))
    if not dim:
        errors.append(
            f"non_functional_quality: {category} artifact requires a '{dim_name}' dimension in "
            f"non-functional-quality.yaml with fields: {list(required_fields)}"
        )
        return
    baseline = as_dict(dim.get("baseline"))
    if not baseline:
        errors.append(f"non_functional_quality: {dim_name}.baseline is required (declare initial measured values)")
        return
    for field in required_fields:
        if field not in baseline:
            errors.append(
                f"non_functional_quality: {dim_name}.baseline missing required metric '{field}' "
                f"(the agent must measure and declare this — mention without measurement is not a gate)"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    errors, warnings = validate(Path(args.root).resolve())
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors:
        return 1
    print("BAGEL non-functional quality check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
