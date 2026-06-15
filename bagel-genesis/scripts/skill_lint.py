#!/usr/bin/env python3
"""Lightweight BAGEL skill consistency lint.

This catches documentation contradictions that normal skill metadata validation
does not cover.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


BAD_PATTERNS = {
    r"\.bagel/worktrees": "Use sibling ../.bagel-worktrees paths, not nested .bagel/worktrees.",
    r"\.bagel/sandboxes": "Use sibling ../.bagel-worktrees paths, not old .bagel/sandboxes.",
    r"single source of truth for product state": "UPMG is optional; governance-data-model is canonical.",
    r"check_constraint\s*\(": "SQLite has no built-in check_constraint function.",
    r"severity:\s*P0 \| P1 \| P2 \| P3": "Use P0/P1/P2/INFO severity rubric.",
    r"SCORE:\s*1-10": "Use severity rubric, not numeric reviewer scores.",
    r"Static Fuzzing|fuzzing-taxonomy": "Use Missing-Belief Discovery and references/missing-belief-discovery.md.",
    r"progress-delta\.yaml": "Use progress-deltas.yaml (plural), not progress-delta.yaml.",
}

EXPECTED_REFERENCE_TITLES = {
    "references/missing-belief-discovery.md": "# Missing-Belief Discovery Taxonomy",
}


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    failures: list[str] = []

    for path in sorted(root.rglob("*")):
        if path.is_dir() or ".DS_Store" in path.name:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] in {"evals", "examples"}:
            continue
        if path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"}:
            continue
        text = path.read_text(encoding="utf-8")
        rel_posix = rel.as_posix()
        expected_title = EXPECTED_REFERENCE_TITLES.get(rel_posix)
        if expected_title:
            first_heading = next((line.strip() for line in text.splitlines() if line.startswith("#")), "")
            if first_heading != expected_title:
                failures.append(f"{rel}:1: Expected title {expected_title!r}, found {first_heading!r}.")
        for pattern, message in BAD_PATTERNS.items():
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                failures.append(f"{rel}:{line}: {message}")
        if path.suffix == ".md":
            previous_number: int | None = None
            previous_indent: int | None = None
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = re.match(r"^(\s*)(\d+)\.\s+", line)
                if not match:
                    previous_number = None
                    previous_indent = None
                    continue
                indent = len(match.group(1))
                number = int(match.group(2))
                if previous_indent == indent and previous_number is not None:
                    expected_number = previous_number + 1
                    if number != expected_number:
                        failures.append(
                            f"{rel}:{line_no}: Expected markdown list number {expected_number}, found {number}."
                        )
                previous_number = number
                previous_indent = indent

    if failures:
        print("BAGEL skill lint failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("BAGEL skill lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
