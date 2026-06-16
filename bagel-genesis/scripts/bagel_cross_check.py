#!/usr/bin/env python3
"""Cross-reference consistency checks for BAGEL V2 docs and scripts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_TERMS = {
    "replace_not_compact": ["references/supervisor-resilience.md", "references/agent-operating-model.md", "scripts/bagel_run_check.py"],
    "degraded_resume": ["SKILL.md", "references/runtime-capabilities.md", "references/loop-runtime.md"],
    "stop_contract": ["SKILL.md", "references/alignment-protocol.md", "scripts/bagel_run_check.py"],
    "delta_type": ["references/runtime-protocol.md", "scripts/flywheel_check.py"],
    "observed": ["references/runtime-capabilities.md", "scripts/bagel_run_check.py"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = Path(args.skill_root).resolve()
    failures: list[str] = []
    for term, files in REQUIRED_TERMS.items():
        for rel in files:
            path = root / rel
            if not path.exists():
                failures.append(f"{rel}: missing file for term {term}")
                continue
            if term not in path.read_text(encoding="utf-8"):
                failures.append(f"{rel}: missing cross-reference term {term}")
    if failures:
        print("BAGEL cross-check failed:", file=sys.stderr)
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("BAGEL cross-check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
