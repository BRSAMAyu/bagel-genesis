#!/usr/bin/env python3
"""Run the BAGEL V3.1 executable expert-runtime validator suite."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


CHECKS = [
    "bagel_run_check.py",
    "supervisor_boundary_check.py",
    "runtime_proof_check.py",
    "dispatch_envelope_check.py",
    "flywheel_check.py",
    "bagel_memory_check.py",
    "bagel_telemetry_check.py",
    "deliverable_delta_check.py",
    "resume_integrity_check.py",
    "evidence_replay_check.py",
    "scope_check.py",
    "evaluation_quality_check.py",
    "expert_strategy_check.py",
    "roi_check.py",
    "alignment_freshness_check.py",
    "reference_load_check.py",
    "emergency_stop_check.py",
]


def has_build_evidence(project_root: Path) -> bool:
    evidence_root = project_root / ".bagel/evidence"
    if (evidence_root / "progress-deltas.yaml").exists():
        return True
    if not evidence_root.exists():
        return False
    for child in evidence_root.iterdir():
        if child.name in {"runtime", "baseline", "progress-deltas.yaml"}:
            continue
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--strict-warnings", action="store_true")
    parser.add_argument("--allow-no-deltas-before-build", action="store_true", default=True)
    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    script_dir = Path(__file__).resolve().parent
    state = {}
    try:
        import yaml
        state_path = project_root / ".bagel/state.yaml"
        if state_path.exists():
            state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    except Exception:
        state = {}
    phase = state.get("phase") or state.get("status") or state.get("run_status")
    has_actions = (project_root / ".bagel/actions").exists() or bool(state.get("actions"))
    has_telemetry = (project_root / ".bagel/telemetry/cycles.yaml").exists() or bool((state.get("telemetry") or {}).get("cycles") if isinstance(state.get("telemetry"), dict) else False)
    build_started = phase in {"Build", "Iterate", "Polish", "excellence_loop", "complete"} or bool(state.get("task_queue")) or has_actions or has_telemetry or has_build_evidence(project_root)

    failures: list[str] = []
    for script in CHECKS:
        if script == "flywheel_check.py" and not (project_root / ".bagel/evidence/progress-deltas.yaml").exists():
            if args.allow_no_deltas_before_build and not build_started:
                print("SKIP: flywheel_check.py (no progress-deltas.yaml before Build)")
                continue
            print("== flywheel_check.py ==")
            print("FAIL: Build/Iterate/Polish has started but progress-deltas.yaml is missing")
            failures.append(script)
            continue
        command = [sys.executable, str(script_dir / script), str(project_root)]
        if args.strict_warnings and script != "flywheel_check.py":
            command.append("--strict-warnings")
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(f"== {script} ==")
        print(result.stdout, end="")
        if result.returncode != 0:
            failures.append(script)
    if failures:
        print("BAGEL V3.1 check failed: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("BAGEL V3.1 check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
