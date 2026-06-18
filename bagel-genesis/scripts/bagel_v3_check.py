#!/usr/bin/env python3
"""Run the BAGEL V4 executable expert-runtime validator suite.

The filename remains bagel_v3_check.py for backward compatibility with
existing BAGEL runs and docs that invoke the unified validator by this path.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# P0-1 fix: the validator suite's single declared third-party dependency is
# PyYAML (requirements.txt). Every sub-check imports `yaml`. If it is missing
# the sub-processes would each emit a ModuleNotFoundError stack trace that
# looks like an environment bug rather than a gate result. Surface it once,
# clearly, with the exact remediation, before dispatching any sub-check.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bagel_deps import ensure_yaml_optional  # noqa: E402

if ensure_yaml_optional() is None:
    sys.stderr.write(
        "FAIL: BAGEL V4 check cannot run — PyYAML is not installed.\n"
        "      Every sub-validator imports `yaml`. Without it the suite "
        "crashes instead of enforcing gates.\n"
        "      Fix:  pip install -r requirements.txt   (or:  pip install "
        "PyYAML>=6.0)\n"
        "      Then re-run:  python scripts/bagel_v3_check.py <project-root>\n"
    )
    raise SystemExit(1)


CHECKS = [
    "attestation_check.py",
    "audit_verifier.py",
    "ci_readiness_check.py",
    "liveness_check.py",
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
    "research_governance_check.py",
    "research_lab_check.py",
    "environment_lock_check.py",
    "roi_check.py",
    "alignment_freshness_check.py",
    "reference_load_check.py",
    "emergency_stop_check.py",
    "production_surface_check.py",
    "non_functional_quality_check.py",
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

    # T1.1 fix: emergency stop circuit breaker. If STOP_REQUESTED exists or run_status
    # is emergency_stopped, the suite short-circuits with a single clear message — it does
    # NOT run the other 18 checks (which would produce repairable "failures" the agent is
    # pressured to fix, undoing the user's stop). This is the kill switch.
    stop_requested = (project_root / ".bagel/STOP_REQUESTED").exists()
    run_status = str(state.get("run_status") or "")
    if stop_requested or run_status == "emergency_stopped":
        print("HALT: emergency stop is active (.bagel/STOP_REQUESTED exists or run_status=emergency_stopped).")
        print("      The run is stopped. Do NOT 'repair' this — clear STOP_REQUESTED only when the user explicitly resumes.")
        return 1

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
        # T1.2 fix: evidence_replay_check must run with --replay by default so cited
        # commands are actually re-executed (was: bare call, allowing fabrication).
        # V5: also pass --attested so metric_recompute extracts_from is bound to a
        # platform-attested command output when the attestation tier is configured.
        # The flag self-disables when BAGEL_ATTEST_KEY is unset (no-op, UNATTESTED).
        if script == "evidence_replay_check.py":
            command.append("--replay")
            command.append("--attested")
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(f"== {script} ==")
        print(result.stdout, end="")
        if result.returncode != 0:
            failures.append(script)
    if failures:
        print("BAGEL V4 check failed: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("BAGEL V4 check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
