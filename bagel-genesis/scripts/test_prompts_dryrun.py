#!/usr/bin/env python3
"""V3.4 test-prompts dryrun CI (Tier 1 static check).

For each test prompt in test-prompts.json, verify that the gates and validators it
expects actually exist in the skill (gate-predicates.md, scripts/). This turns the
test prompts from documentation into a lightweight regression suite that catches
dangling references to gates/scripts that were renamed or removed.

This is a CI/skill-self-consistency tool, NOT a runtime validator — it does not run
against a .bagel/ project state.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_skill_text(root: Path, rel: str) -> str:
    p = root / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def extract_gates(gate_predicates: str) -> set[str]:
    """Extract gate names from the Core Predicates table."""
    out: set[str] = set()
    for m in re.finditer(r"`([a-z_]+)`\s*\|", gate_predicates):
        out.add(m.group(1))
    return out


def extract_scripts(root: Path) -> set[str]:
    """Extract script filenames present in scripts/."""
    scripts_dir = root / "scripts"
    if not scripts_dir.exists():
        return set()
    return {f.name for f in scripts_dir.glob("*.py")}


def extract_gates_from_text(text: str) -> set[str]:
    """Find gate names referenced in a prompt's expected/trap text."""
    return set(re.findall(r"`?([a-z][a-z_]+_check(?:ed)?)`?\b", text))


def extract_scripts_from_text(text: str) -> set[str]:
    """Find script filenames referenced in text."""
    return set(re.findall(r"\b([a-z_]+_check\.py)\b", text))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    tp_path = root / "test-prompts.json"
    if not tp_path.exists():
        print("test-prompts.json not found; nothing to dryrun")
        return 0

    with tp_path.open("r", encoding="utf-8") as fh:
        prompts = json.load(fh)

    gate_predicates = load_skill_text(root, "references/gate-predicates.md")
    known_gates = extract_gates(gate_predicates)
    known_scripts = extract_scripts(root)

    failures: list[str] = []
    checked = 0
    for item in prompts:
        name = item.get("name") or item.get("id")
        combined = " ".join(str(v) for v in (item.get("expected", ""), item.get("trap", ""), item.get("expected_output", "")))
        ref_gates = extract_gates_from_text(combined)
        ref_scripts = extract_scripts_from_text(combined)
        # check gates that end in _checked (our naming convention for gates)
        for g in ref_gates:
            if g.endswith("_checked") and g not in known_gates:
                failures.append(f"{name}: references gate `{g}` not found in gate-predicates.md")
        for s in ref_scripts:
            if s not in known_scripts:
                failures.append(f"{name}: references script `{s}` not found in scripts/")
        checked += 1

    print(f"test-prompts dryrun: checked {checked} prompts, {len(failures)} dangling reference(s)")
    for f in failures:
        print(f"  FAIL: {f}")
    if failures:
        return 1
    print("test-prompts dryrun passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
