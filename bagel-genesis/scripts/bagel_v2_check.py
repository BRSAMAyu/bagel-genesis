#!/usr/bin/env python3
"""Run the BAGEL V2 measured-autonomy validator suite."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


CHECKS = [
    "bagel_run_check.py",
    "flywheel_check.py",
    "bagel_memory_check.py",
    "bagel_telemetry_check.py",
    "resume_integrity_check.py",
    "evidence_replay_check.py",
    "scope_check.py",
    "alignment_freshness_check.py",
    "reference_load_check.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--strict-warnings", action="store_true")
    parser.add_argument("--skip-flywheel-if-no-deltas", action="store_true", default=True)
    args = parser.parse_args()

    project_root = Path(args.root).resolve()
    script_dir = Path(__file__).resolve().parent
    failures: list[str] = []
    for script in CHECKS:
        if script == "flywheel_check.py" and args.skip_flywheel_if_no_deltas and not (project_root / ".bagel/evidence/progress-deltas.yaml").exists():
            print("SKIP: flywheel_check.py (no progress-deltas.yaml yet)")
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
        print("BAGEL V2 check failed: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("BAGEL V2 check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
