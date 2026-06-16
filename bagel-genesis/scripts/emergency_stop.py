#!/usr/bin/env python3
"""Request a safe BAGEL emergency stop without destructive reset."""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
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


def run(root: Path, args: argparse.Namespace) -> int:
    bagel = root / ".bagel"
    bagel.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    (bagel / "STOP_REQUESTED").write_text(f"requested_at: {now}\nreason: {args.reason}\n", encoding="utf-8")
    status = subprocess.run(["git", "-C", str(root), "status", "--short"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    checkpoint_dir = bagel / "emergency"
    checkpoint_dir.mkdir(exist_ok=True)
    (checkpoint_dir / "git-status.txt").write_text(status.stdout, encoding="utf-8")
    state_path = bagel / "state.yaml"
    state = as_dict(load_yaml(state_path, {}))
    state["run_status"] = "emergency_stopped"
    state["emergency_stop"] = {
        "requested_at": now,
        "reason": args.reason,
        "git_status_ref": ".bagel/emergency/git-status.txt",
        "destructive_reset_performed": False,
        "recovery_instructions_ref": ".bagel/emergency/recovery-instructions.md",
    }
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    instructions = (
        "# BAGEL Emergency Stop Recovery\n\n"
        "1. Do not run destructive reset automatically.\n"
        "2. Inspect `.bagel/emergency/git-status.txt`.\n"
        "3. Preserve or branch/stash uncommitted user and agent changes before resuming.\n"
        "4. Resume only after the user clears the stop request or provides new instructions.\n"
    )
    (checkpoint_dir / "recovery-instructions.md").write_text(instructions, encoding="utf-8")
    print("BAGEL emergency stop requested. State preserved; no destructive reset performed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--reason", default="user_requested_stop")
    return run(Path(parser.parse_args().root).resolve(), parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
