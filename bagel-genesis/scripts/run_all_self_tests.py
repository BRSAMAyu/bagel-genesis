#!/usr/bin/env python3
"""Run every validator's `--self-test` in one command and report a single verdict.

Each BAGEL validator script ships an internal `--self-test` that exercises its own
PASS/FAIL fixtures (the schema it polices, in isolation, no repo state needed). This
runner discovers every script in `scripts/` that advertises a `--self-test` flag,
runs each in its own subprocess, and aggregates the result — so a maintainer (or a CI
job, or an agent about to rely on the gates) can confirm the whole validator suite is
green with one command instead of 30.

Discovery is by static scan: a script is included iff its source contains the literal
`--self-test` (the argparse flag) AND a `def _self_test` or `--self-test` handler. This
avoids importing the scripts (which could have side effects) and avoids a hand-maintained
list that silently rots when a new validator is added without registration.

Usage:
    python scripts/run_all_self_tests.py            # run all, human summary
    python scripts/run_all_self_tests.py --list     # just list discovered scripts
    python scripts/run_all_self_tests.py --quiet     # only the final line + failures

Exit code is 0 iff every discovered self-test passed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PY = sys.executable
SCRIPTS_DIR = Path(__file__).resolve().parent

# Scripts that are libraries or runners, not self-testing validators — skip even if the
# token appears (e.g. this file itself, or a dispatcher that shells out to others).
SKIP = {
    "run_all_self_tests.py",
    "_bagel_deps.py",
    "attestation_lib.py",
}


def discovers_self_test(path: Path) -> bool:
    try:
        src = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return "--self-test" in src and ("_self_test" in src or "self_test" in src or "args.self_test" in src)


def discover() -> list[Path]:
    found = []
    for p in sorted(SCRIPTS_DIR.glob("*.py")):
        if p.name in SKIP:
            continue
        if discovers_self_test(p):
            found.append(p)
    return found


def run_one(path: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [PY, str(path), "--self-test"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT after 120s"
    ok = proc.returncode == 0
    # Pull the summary line (".../N self-test cases passed.") if present.
    tail = ""
    for line in reversed((proc.stdout or "").strip().splitlines()):
        if "self-test" in line.lower() or "passed" in line.lower():
            tail = line.strip()
            break
    if not ok and not tail:
        tail = ((proc.stderr or proc.stdout or "").strip().splitlines() or ["(no output)"])[-1][:200]
    return ok, tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list discovered self-testing scripts and exit")
    parser.add_argument("--quiet", action="store_true", help="only print failures and the final summary")
    args = parser.parse_args()

    scripts = discover()
    if args.list:
        for p in scripts:
            print(p.name)
        print(f"\n{len(scripts)} self-testing scripts discovered.")
        return 0

    passed = 0
    failures: list[str] = []
    for p in scripts:
        ok, tail = run_one(p)
        passed += int(ok)
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failures.append(f"{p.name}: {tail}")
        if not args.quiet or not ok:
            print(f"{mark}  {p.name:<40} {tail}")

    total = len(scripts)
    print(f"\n{'=' * 60}")
    print(f"{passed}/{total} validator self-tests passed.")
    if failures:
        print(f"\n{len(failures)} FAILED:")
        for f in failures:
            print(f"  - {f}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
