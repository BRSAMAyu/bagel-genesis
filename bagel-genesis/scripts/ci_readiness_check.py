#!/usr/bin/env python3
"""Report whether a research project is configured for CI-verified claims.

This is intentionally a reporting gate, not a local hard fail: branch
protection is a repository-admin setting and cannot always be verified from a
local checkout. It emits NOT_CI_PROTECTED unless the project records an explicit
attestation that the required GitHub settings are active.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


REQUIRED_TRUE = (
    "no_force_push",
    "required_bagel_audit_check",
    "protect_workflow_files",
    "audit_secret_configured",
    "public_key_committed",
)


def load_yaml(path: Path) -> Any:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def is_research_like(root: Path) -> bool:
    return (root / ".bagel/research").exists() or (root / ".bagel/constitution.yaml").exists()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not is_research_like(root):
        print("ci_readiness_check: not research-like; skipped")
        return 0
    path = root / ".bagel/audit/ci-protection.yaml"
    data = load_yaml(path)
    body = data.get("ci_protection") if isinstance(data, dict) else {}
    if not isinstance(body, dict):
        body = {}
    missing = [key for key in REQUIRED_TRUE if body.get(key) is not True]
    if missing:
        print("ci_readiness_check: NOT_CI_PROTECTED")
        print("  CI-verified headline claims require .bagel/audit/ci-protection.yaml with:")
        for key in missing:
            print(f"  - {key}: true")
        print("  Local validation continues, but audit_verifier will not upgrade claims without a signed CI verdict.")
        return 0
    print("ci_readiness_check: CI_PROTECTION_ATTESTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
