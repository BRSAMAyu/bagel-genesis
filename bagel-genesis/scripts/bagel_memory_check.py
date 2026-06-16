#!/usr/bin/env python3
"""Validate BAGEL innovation and lesson-memory state.

This script catches two failure modes that prose rules do not reliably prevent:
1. Ambitious/novelty-seeking runs that never perform divergent concept exploration.
2. Recovery-heavy runs that fix failures but do not distill reusable lessons.
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


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def warn(warnings: list[str], message: str) -> None:
    warnings.append(message)


def constitution(root: Path) -> dict[str, Any]:
    bagel = root / ".bagel"
    data = load_yaml(bagel / "constitution.yaml", {})
    if not isinstance(data, dict) or not data:
        data = load_yaml(bagel / "constitution.json", {})
    return as_dict(data)


def ledger(root: Path) -> dict[str, Any]:
    return as_dict(load_yaml(root / ".bagel" / "ledger.yaml", {}))


def collect_lessons(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    led = ledger(root)
    records.extend(as_dict(item) for item in as_list(led.get("lessons")))

    lessons_dir = root / ".bagel" / "lessons"
    for name in ("index.yaml", "gotchas.yaml", "environment.yaml", "engineering.yaml", "product.yaml", "research.yaml"):
        data = load_yaml(lessons_dir / name, {})
        if isinstance(data, dict):
            records.extend(as_dict(item) for item in as_list(data.get("lessons")))
        elif isinstance(data, list):
            records.extend(as_dict(item) for item in data)
    return [item for item in records if item]


def recovery_events(root: Path) -> list[Any]:
    led = ledger(root)
    events = as_list(led.get("recovery"))
    recovery_log = root / ".bagel" / "ledger" / "recovery-log.md"
    if recovery_log.exists() and recovery_log.stat().st_size > 0:
        events.append({"source": str(recovery_log), "size": recovery_log.stat().st_size})
    return events


def collect_concepts(root: Path) -> list[dict[str, Any]]:
    data = load_yaml(root / ".bagel" / "innovation" / "ledger.yaml", {})
    if isinstance(data, dict):
        return [as_dict(item) for item in as_list(data.get("concepts"))]
    if isinstance(data, list):
        return [as_dict(item) for item in data]
    return []


def innovation_contract(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    c = constitution(root)
    contract = as_dict(c.get("innovation_contract"))
    if contract:
        return contract
    return as_dict(state.get("innovation_contract"))


def validate_lessons(root: Path, errors: list[str], warnings: list[str]) -> None:
    events = recovery_events(root)
    if not events:
        return
    lessons = collect_lessons(root)
    if not lessons:
        fail(errors, "recovery events exist but no lessons were captured in .bagel/lessons/ or ledger.yaml#lessons")
        return
    for lesson in lessons:
        lesson_id = lesson.get("id") or "<unknown>"
        for field in ("title", "category", "trigger", "rule", "applies_when", "verification", "confidence", "status"):
            if field not in lesson:
                fail(errors, f"lesson {lesson_id} missing required field: {field}")
        trigger = as_dict(lesson.get("trigger"))
        verification = as_dict(lesson.get("verification"))
        if not trigger.get("evidence"):
            fail(errors, f"lesson {lesson_id} must link trigger.evidence to the recovery event")
        if not verification.get("evidence") and not verification.get("command"):
            fail(errors, f"lesson {lesson_id} must include verification.command or verification.evidence")
        if lesson.get("confidence") == "high" and not lesson.get("last_confirmed_at"):
            warn(warnings, f"high-confidence lesson {lesson_id} has no last_confirmed_at")


def validate_innovation(root: Path, state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    contract = innovation_contract(root, state)
    ambition = contract.get("ambition")
    if not ambition:
        return
    if ambition not in {"execution_excellence", "differentiated", "breakthrough"}:
        fail(errors, f"innovation_contract.ambition has unknown value: {ambition!r}")
        return
    if ambition == "execution_excellence":
        return

    concepts = collect_concepts(root)
    if not concepts:
        fail(errors, f"innovation_contract.ambition={ambition} but .bagel/innovation/ledger.yaml has no concept candidates")
        return
    required = 2 if ambition == "breakthrough" else 1
    if len(concepts) < required:
        fail(errors, f"innovation ambition {ambition} requires at least {required} concept candidate(s), found {len(concepts)}")
    for concept in concepts:
        cid = concept.get("id") or "<unknown>"
        for field in ("title", "novelty_type", "fit_with_constitution", "expected_upside", "risk", "falsifiable_probe", "decision"):
            if field not in concept:
                fail(errors, f"innovation concept {cid} missing required field: {field}")
        if concept.get("decision") in {"probe", "adopt"} and not as_list(concept.get("evidence")):
            fail(errors, f"innovation concept {cid} decision={concept.get('decision')} requires evidence for its probe/adoption")
        if concept.get("constitution_change_needed") is True and concept.get("decision") == "adopt":
            fail(errors, f"innovation concept {cid} requires constitution change but was adopted directly")

    if ambition == "breakthrough":
        breakthrough = as_dict(load_yaml(root / ".bagel/expert/breakthrough-search.yaml", {}))
        if not breakthrough:
            fail(errors, "breakthrough ambition requires .bagel/expert/breakthrough-search.yaml")
        lenses = {
            lens
            for concept in concepts
            for lens in as_list(concept.get("lenses"))
            if lens
        }
        if len(lenses) < 2:
            fail(errors, "breakthrough ambition requires concept candidates from >=2 distinct innovation lenses")


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    if not bagel.exists():
        return ["no .bagel/ directory found; BAGEL memory state does not exist"], []
    state = as_dict(load_yaml(bagel / "state.yaml", {}))
    errors: list[str] = []
    warnings: list[str] = []
    validate_lessons(root, errors, warnings)
    validate_innovation(root, state, errors, warnings)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Project root containing .bagel/")
    parser.add_argument("--strict-warnings", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()
    errors, warnings = validate(Path(args.root).resolve())
    for message in warnings:
        print(f"WARN: {message}", file=sys.stderr)
    for message in errors:
        print(f"FAIL: {message}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL memory check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
