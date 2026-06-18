#!/usr/bin/env python3
"""Validate BAGEL long-run liveness timestamps."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
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
    return value if isinstance(value, list) else [value]


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def max_timestamp(root: Path, state: dict[str, Any]) -> datetime | None:
    candidates: list[datetime] = []
    for key in ("last_checked_at", "updated_at", "heartbeat_at", "last_heartbeat_at"):
        dt = parse_time(state.get(key))
        if dt:
            candidates.append(dt)
    heartbeat_paths = [
        root / ".bagel/supervisor/heartbeat.yaml",
        root / ".bagel/heartbeat.yaml",
    ]
    for path in heartbeat_paths:
        hb = as_dict(load_yaml(path, {}))
        for key in ("last_checked_at", "updated_at", "heartbeat_at", "last_heartbeat_at"):
            dt = parse_time(hb.get(key))
            if dt:
                candidates.append(dt)
    cycles = load_yaml(root / ".bagel/telemetry/cycles.yaml", {})
    rows = as_list(as_dict(cycles).get("cycles")) if isinstance(cycles, dict) else as_list(cycles)
    for row in rows:
        r = as_dict(row)
        for key in ("ended_at", "finished_at", "updated_at"):
            dt = parse_time(r.get(key))
            if dt:
                candidates.append(dt)
    return max(candidates) if candidates else None


def interval_minutes(state: dict[str, Any]) -> float:
    loop = as_dict(state.get("loop_binding"))
    raw = loop.get("trigger_interval_minutes") or as_dict(state.get("heartbeat")).get("interval_minutes")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = 15.0
    return max(1.0, value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--now", help="Override current time for tests (ISO-8601)")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    if not state:
        print("BAGEL liveness check passed (no run state).")
        return 0
    run_status = str(state.get("run_status") or state.get("status") or "")
    phase = str(state.get("run_phase") or state.get("phase") or "").lower()
    if run_status in {"complete", "emergency_stopped"} or phase in {"complete"}:
        print("BAGEL liveness check passed (inactive terminal state).")
        return 0
    last = max_timestamp(root, state)
    if not last:
        print("FAIL: liveness timestamp missing; no heartbeat or telemetry timestamp can prove the run is alive.", file=sys.stderr)
        return 1
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    assert now is not None
    age_minutes = (now - last).total_seconds() / 60.0
    limit = 2 * interval_minutes(state)
    if age_minutes > limit:
        print(
            f"FAIL: BAGEL liveness stale: last heartbeat/telemetry is {age_minutes:.1f} min old "
            f"(limit {limit:.1f} min). External watchdog or resume loop must wake/kill/recover.",
            file=sys.stderr,
        )
        return 1
    print("BAGEL liveness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
