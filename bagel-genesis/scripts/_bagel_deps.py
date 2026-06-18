"""Shared dependency bootstrap for BAGEL validator scripts.

Every validator in scripts/ imports `yaml` (PyYAML). If PyYAML is not
installed, the script crashes with a `ModuleNotFoundError` stack trace that
looks like an environment bug rather than a real gate failure — which risks
the suite being silently skipped or misread as "broken, ignore".

This module provides `ensure_yaml()` which, on success, returns the `yaml`
module, and on failure prints a single clear FAIL line to stderr and exits
non-zero. Validators call it once at import time:

    from _bagel_deps import ensure_yaml
    yaml = ensure_yaml()

This keeps the validator suite honest: a missing dependency is surfaced as a
real, named failure, not swallowed.
"""

from __future__ import annotations

import sys


def ensure_yaml():
    """Return the PyYAML module, or print a clear FAIL and exit non-zero.

    The exit message names the exact remediation so an operator (human or
    agent) cannot mistake a missing dependency for a broken gate.
    """
    try:
        import yaml  # type: ignore
        return yaml
    except ModuleNotFoundError:
        prog = "BAGEL validator"
        sys.stderr.write(
            f"FAIL: {prog} cannot run — PyYAML is not installed in this "
            f"environment.\n"
            f"       The validator suite (scripts/*.py) imports `yaml`, which "
            f"is declared in requirements.txt.\n"
            f"       Fix:  pip install -r requirements.txt   "
            f"(or:  pip install PyYAML>=6.0)\n"
            f"       This is a dependency failure, not a gate result — after "
            f"installing, re-run:\n"
            f"            python scripts/bagel_v3_check.py <project-root>\n"
        )
        raise SystemExit(1)


def ensure_yaml_optional():
    """Return the PyYAML module or None, without exiting.

    Use only in scripts that have a meaningful non-yaml fallback (e.g. a
    suite orchestrator that can still emit a usage message). Most validators
    should use `ensure_yaml()` instead.
    """
    try:
        import yaml  # type: ignore
        return yaml
    except ModuleNotFoundError:
        return None
