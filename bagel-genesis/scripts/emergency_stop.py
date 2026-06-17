#!/usr/bin/env python3
"""Request a safe BAGEL emergency stop without destructive reset."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return default if data is None else data
    except yaml.YAMLError:
        # T2.8 fix: catch corrupted YAML instead of crashing with a traceback.
        # A half-written state.yaml from a crashed write should produce a clean
        # error, not an unhandled exception.
        return default


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def atomic_write(path: Path, content: str) -> None:
    """T2.8 fix: atomic write via tempfile + os.replace.

    Prevents half-written state files if the process crashes mid-write. A truncated
    state.yaml would crash every downstream validator with a YAMLError traceback.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def run(root: Path, args: argparse.Namespace) -> int:
    bagel = root / ".bagel"
    bagel.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    atomic_write(bagel / "STOP_REQUESTED", f"requested_at: {now}\nreason: {args.reason}\n")
    # T2.8 fix: add timeout to prevent indefinite hang on a locked git repo
    status = subprocess.run(["git", "-C", str(root), "status", "--short"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
    checkpoint_dir = bagel / "emergency"
    checkpoint_dir.mkdir(exist_ok=True)
    atomic_write(checkpoint_dir / "git-status.txt", status.stdout)
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
    atomic_write(state_path, yaml.safe_dump(state, sort_keys=False))
    instructions = (
        "# BAGEL Emergency Stop Recovery\n\n"
        "1. Do not run destructive reset automatically.\n"
        "2. Inspect `.bagel/emergency/git-status.txt`.\n"
        "3. Preserve or branch/stash uncommitted user and agent changes before resuming.\n"
        "4. Resume only after the user clears the stop request or provides new instructions.\n"
    )
    atomic_write(checkpoint_dir / "recovery-instructions.md", instructions)
    print("BAGEL emergency stop requested. State preserved; no destructive reset performed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--reason", default="user_requested_stop")
    return run(Path(parser.parse_args().root).resolve(), parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
