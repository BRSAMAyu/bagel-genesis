#!/usr/bin/env python3
"""Validate BAGEL runtime capability proof files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


REQUIRED_BY_KIND = {
    "true_subagents": {"proof_id", "capability", "observed_at", "mechanism", "isolated_context", "verifier_agent_id"},
    "timers_or_wakeup": {"proof_id", "capability", "observed_at", "mechanism", "schedule_ref", "trigger_interval_minutes"},
    "hooks": {"proof_id", "capability", "observed_at", "mechanism", "hook_name", "test_result"},
    "browser_or_visual": {"proof_id", "capability", "observed_at", "mechanism", "artifact_ref"},
}


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return default if data is None else data


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _attested_subagents(root: Path) -> tuple[list[dict], list[str], bool]:
    """When the attestation tier is active (BAGEL_ATTEST_KEY set), return the
    list of real signed Task dispatches plus any chain errors. The third value
    is `active` — True only when a key is configured, so callers keep the
    pre-attestation shape-only behavior when it is off (honest degradation)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import attestation_lib as al
    except Exception:
        return [], [], False
    if not al.has_key():
        return [], [], False
    chain_errors, verified = al.validate_chain(root, al.get_key())
    return al.index_subagents(verified), chain_errors, True


def validate(root: Path) -> tuple[list[str], list[str]]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    rc = as_dict(state.get("runtime_capabilities"))
    file_rc = as_dict(load_yaml(root / ".bagel/runtime_capabilities.yaml", {}))
    if not rc and "runtime_capabilities" in file_rc:
        rc = as_dict(file_rc.get("runtime_capabilities"))
    errors: list[str] = []
    warnings: list[str] = []
    caps = as_dict(rc.get("capabilities"))

    # Attested-mode binding (RUN-001 finding 3): when the attestation tier is
    # active, the true_subagents proof must trace to a REAL signed Task dispatch,
    # not merely be shape-valid. Off when no key → shape-only fallback unchanged.
    attested_subagents, chain_errors, attested_active = _attested_subagents(root)
    if attested_active and chain_errors:
        errors.extend(f"attestation chain: {e}" for e in chain_errors)
    attested_agent_ids = {str(d.get("agent_id") or "") for d in attested_subagents if d.get("agent_id")}
    attested_ids = {str(d.get("attestation_id") or "") for d in attested_subagents}

    for name, raw in caps.items():
        cap = as_dict(raw)
        if cap.get("observed") is not True:
            continue
        proof_ref = cap.get("proof_ref")
        if not isinstance(proof_ref, str) or not proof_ref:
            errors.append(f"{name}: observed=true requires proof_ref")
            continue
        path = root / proof_ref
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"{name}: proof_ref missing or empty: {proof_ref}")
            continue
        proof = as_dict(load_yaml(path, {}))
        required = REQUIRED_BY_KIND.get(name, {"proof_id", "capability", "observed_at", "mechanism"})
        missing = sorted(field for field in required if field not in proof)
        if missing:
            errors.append(f"{proof_ref}: missing runtime proof fields: {', '.join(missing)}")
        if proof.get("capability") != name:
            errors.append(f"{proof_ref}: capability must be {name!r}")
        if proof.get("result") not in {True, "pass", "passed", "observed"}:
            errors.append(f"{proof_ref}: result must be pass/observed")
        if name == "true_subagents" and proof.get("isolated_context") is not True:
            errors.append(f"{proof_ref}: true_subagents proof requires isolated_context=true")
        if name == "true_subagents" and attested_active:
            # Tier-3: the proof must be backed by a real signed Task dispatch.
            ref = str(proof.get("attestation_ref") or "")
            vid = str(proof.get("verifier_agent_id") or "")
            if not attested_subagents:
                errors.append(
                    f"{proof_ref}: attested mode active but NO signed Task dispatch exists — "
                    "observed:true is not backed by a real subagent attestation "
                    "(install the Task PostToolUse hook attest_subagent.py)"
                )
            elif ref not in attested_ids and vid not in attested_agent_ids:
                errors.append(
                    f"{proof_ref}: proof not bound to any attested Task dispatch "
                    f"(attestation_ref={ref!r}, verifier_agent_id={vid!r} match none of "
                    f"{sorted(attested_ids) or sorted(attested_agent_ids)}) — forged or stale proof"
                )
        if name == "timers_or_wakeup":
            interval = proof.get("trigger_interval_minutes")
            if not isinstance(interval, int) or interval <= 0 or interval > 25:
                errors.append(f"{proof_ref}: trigger_interval_minutes must be 1..25")
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
    print("BAGEL runtime proof check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
