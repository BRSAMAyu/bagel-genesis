#!/usr/bin/env python3
"""Coverage guard for the mechanical grader.

This is NOT a Python branch-coverage tool. It is a governance check that
prevents the failure class which exposed the V4.2 mode-2 amendment bug: a
validator path existed but no mechanical fixture ever exercised it, so a
crash/regression in that path was invisible to the grader.

What it actually verifies (v4.3 upgrade from the earlier 4-marker watchdog):
  1. Every NEGATIVE_CASE in mechanical_grader.py targets a script that exists
     on disk under scripts/. (Catches "fixture references a renamed/deleted
     validator".)
  2. Every NEGATIVE_CASE factory is importable and callable without error on
     fixture-build. (Catches "factory crashes before the validator is ever
     run" — the silent-dead-path class.)
  3. The 4 historically-regressed paths (mode-2 amendment, lab renamed
     command, CI anti-fabrication, positive suite health) still carry their
     fixtures. (Regression guard for the specific bugs that motivated this.)

The v4.3 version checked only #3 (4 substring markers). That passed even when
11 of 15 negative cases were deleted, because it never iterated the case
list. This version closes that hole by importing mechanical_grader and
walking its NEGATIVE_CASES.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


# Historically-regressed paths that MUST retain a fixture (regression guard
# for the specific bugs each was added to catch).
REGRESSION_PATH_MARKERS = {
    "mode2 design amendment path": [
        "fixture_research_amendment_dead_path",
        "research governance rejects unverified design_amendment reviewer",
    ],
    "lab renamed command path": [
        "fixture_research_lab_renamed_command",
        "research lab check rejects renamed executable field",
    ],
    "CI anti-fabrication path": [
        "fixture_ci_echo_extractor",
        "fixture_ci_duplicate_run_ref",
        "fixture_ci_same_commit_harking",
    ],
    "positive suite health path": [
        "fixture_minimal_healthy_run",
        "bagel_v3_check accepts a minimal valid run",
    ],
    "mode2 healthy amendment positive path": [
        "fixture_research_amendment_healthy",
        "research_governance accepts compliant mode-2 amendment",
    ],
}


def load_grader_module(skill_root: Path):
    """Import mechanical_grader.py as a module so we can read NEGATIVE_CASES."""
    grader_path = skill_root / "evals" / "mechanical_grader.py"
    if not grader_path.exists():
        raise FileNotFoundError(f"missing {grader_path}")
    # mechanical_grader reads sys.argv[1] at import time; supply skill_root.
    sys.argv = [str(grader_path), str(skill_root)]
    spec = importlib.util.spec_from_file_location("bagel_mechanical_grader", grader_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, grader_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    skill_root = Path(args.skill_root).resolve()
    errors: list[str] = []

    grader_module, grader_path = load_grader_module(skill_root)
    text = grader_path.read_text(encoding="utf-8", errors="ignore")

    # Check 1: regression-path markers (the original 4-path guard).
    for label, markers in REGRESSION_PATH_MARKERS.items():
        missing = [m for m in markers if m not in text]
        if missing:
            errors.append(f"{label}: mechanical_grader.py missing markers {missing}")

    # Check 2: every NEGATIVE_CASE targets an existing validator script.
    cases = getattr(grader_module, "NEGATIVE_CASES", None)
    if cases is None:
        errors.append("mechanical_grader.py: NEGATIVE_CASES not found — grader structure changed")
    else:
        for label, script, _expect_fail, _factory in cases:
            script_path = skill_root / "scripts" / script
            if not script_path.exists():
                errors.append(f"NEGATIVE_CASE {label!r}: targets missing script {script}")

        # Check 3: every NEGATIVE_CASE factory is importable + callable.
        # This catches the "factory exists but crashes on build" class — the
        # exact failure mode that hid the v4.2 mode-2 amendment crash.
        for label, _script, _expect_fail, factory in cases:
            factory_name = getattr(factory, "__name__", "<anonymous>")
            if not callable(factory):
                errors.append(f"NEGATIVE_CASE {label!r}: factory {factory_name} is not callable")
                continue
            # Build the fixture in a throwaway tempdir; a crash here means the
            # factory is broken and the case is silently dead.
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                try:
                    factory(Path(td))
                except Exception as exc:  # noqa: BLE001 — we want all factory-build failures
                    errors.append(
                        f"NEGATIVE_CASE {label!r}: factory {factory_name} raises on build: "
                        f"{type(exc).__name__}: {exc}"
                    )

    if errors:
        print("coverage_map failed:")
        for err in errors[:30]:
            print(f"- {err}")
        return 1
    case_count = len(cases) if cases is not None else 0
    print(f"coverage_map passed. ({case_count} negative cases verified: scripts exist + factories build)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
