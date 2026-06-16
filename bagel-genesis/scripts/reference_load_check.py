#!/usr/bin/env python3
"""Validate reference-loading telemetry and digest-cache discipline."""

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


def validate(root: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    reads = []
    for path in (root / ".bagel/telemetry").glob("reference-reads*.yaml") if (root / ".bagel/telemetry").exists() else []:
        data = load_yaml(path, {})
        reads.extend(as_dict(item) for item in as_list(data.get("reference_reads") if isinstance(data, dict) else data))
    full_by_ref: dict[str, int] = {}
    for item in reads:
        ref = str(item.get("reference") or "")
        if not item.get("trigger"):
            warnings.append(f"{ref or '<unknown>'}: reference read missing trigger")
        if item.get("read_mode") == "full":
            full_by_ref[ref] = full_by_ref.get(ref, 0) + 1
        if item.get("token_estimate") and isinstance(item.get("token_estimate"), int) and item["token_estimate"] > 12000:
            warnings.append(f"{ref}: large reference read token_estimate={item['token_estimate']}")
    for ref, count in full_by_ref.items():
        if ref and count > 2:
            warnings.append(f"{ref}: repeated full reads ({count}); use digest cache unless stale")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--strict-warnings", action="store_true")
    args = parser.parse_args()
    errors, warnings = validate(Path(args.root).resolve())
    for msg in warnings:
        print(f"WARN: {msg}", file=sys.stderr)
    for msg in errors:
        print(f"FAIL: {msg}", file=sys.stderr)
    if errors or (args.strict_warnings and warnings):
        return 1
    print("BAGEL reference load check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
