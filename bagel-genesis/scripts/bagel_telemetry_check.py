#!/usr/bin/env python3
"""Validate BAGEL V2 telemetry, context pressure, and governance budget."""

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


def collect_cycles(root: Path) -> list[dict[str, Any]]:
    state = as_dict(load_yaml(root / ".bagel/state.yaml", {}))
    cycles: list[dict[str, Any]] = []
    for item in as_list(as_dict(state.get("telemetry")).get("cycles")):
        cycles.append(as_dict(item))
    for path in (root / ".bagel/telemetry").glob("cycles*.yaml") if (root / ".bagel/telemetry").exists() else []:
        data = load_yaml(path, [])
        if isinstance(data, dict):
            cycles.extend(as_dict(item) for item in as_list(data.get("cycles") or data.get("cycle_telemetry")))
        else:
            cycles.extend(as_dict(item) for item in as_list(data))
    return [cycle for cycle in cycles if cycle]


def configured_budget(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    # Mode-aware default ceiling, matching SKILL.md governance-budget rule:
    # quick_autonomy ≤ 25%, full_genesis ≤ 40%, parallel_advanced ≤ 40%.
    # The run mode is recorded in state.run_mode (or state.bagel_mode).
    mode = str(state.get("run_mode") or state.get("bagel_mode") or "").lower()
    if mode in {"full_genesis", "full", "parallel_advanced", "parallel"}:
        mode_ceiling = 0.40
    elif mode in {"quick_autonomy", "quick"}:
        mode_ceiling = 0.25
    else:
        # Unknown/unset mode: use the stricter default so a missing run_mode cannot
        # silently widen the governance budget beyond the quick_autonomy ceiling.
        mode_ceiling = 0.25
    defaults = {
        "max_control_plane_share_per_cycle": mode_ceiling,
        "first_deliverable_delta_required_by_cycle": 2,
        "max_cycles_without_deliverable_delta": 2,
    }
    budget = {**defaults, **as_dict(state.get("governance_budget"))}
    file_budget = as_dict(load_yaml(root / ".bagel/telemetry/governance-budget.yaml", {}))
    return {**budget, **file_budget}


def validate(root: Path) -> tuple[list[str], list[str]]:
    bagel = root / ".bagel"
    if not bagel.exists():
        return [], []
    state = as_dict(load_yaml(bagel / "state.yaml", {}))
    errors: list[str] = []
    warnings: list[str] = []
    cycles = collect_cycles(root)
    if not cycles:
        if state.get("phase") in {"Build", "Iterate", "Polish"} or state.get("task_queue"):
            fail(errors, "Build/Iterate work has started but no V2 cycle telemetry exists")
        return errors, warnings

    budget = configured_budget(root, state)
    max_share = float(budget.get("max_control_plane_share_per_cycle", 0.30))
    max_no_delta = int(budget.get("max_cycles_without_deliverable_delta", 2))
    first_delta_by = int(budget.get("first_deliverable_delta_required_by_cycle", 2))

    no_deliverable_streak = 0
    high_governance_streak = 0
    first_deliverable_seen_at: int | None = None

    for idx, cycle in enumerate(cycles, start=1):
        outputs = as_dict(cycle.get("outputs"))
        budget_block = as_dict(cycle.get("budget"))
        pressure = as_dict(cycle.get("context_pressure"))
        deliverable_delta = outputs.get("deliverable_delta")
        control_delta = outputs.get("control_plane_delta")
        if deliverable_delta not in {True, False}:
            fail(errors, f"cycle {idx}: outputs.deliverable_delta must be boolean")
            deliverable_delta = False
        if control_delta not in {True, False}:
            fail(errors, f"cycle {idx}: outputs.control_plane_delta must be boolean")
            control_delta = False
        share = budget_block.get("governance_token_share")
        # Gap-2 fix: derive share from a token_log so it's recomputable, not just self-attested.
        # When a cycle records a token_log of [{role, tokens, category}] entries, recompute the
        # governance share = sum(governance-category tokens) / sum(all tokens) and compare to the
        # declared share. A mismatch > 0.05 means the agent lied about its share — fail.
        token_log = as_list(cycle.get("token_log") or budget_block.get("token_log"))
        if token_log:
            GOVERNANCE_CATEGORIES = {"governance", "control_plane", "alignment", "review", "telemetry", "state", "dispatch"}
            gov_tokens = 0
            all_tokens = 0
            for entry in token_log:
                e = as_dict(entry)
                tokens = e.get("tokens")
                category = str(e.get("category") or e.get("role") or "").lower()
                if isinstance(tokens, (int, float)) and tokens >= 0:
                    all_tokens += tokens
                    if any(g in category for g in GOVERNANCE_CATEGORIES):
                        gov_tokens += tokens
            if all_tokens > 0 and isinstance(share, (int, float)):
                derived_share = gov_tokens / all_tokens
                if abs(derived_share - share) > 0.05:
                    fail(errors, f"cycle {idx}: governance_token_share {share:.2f} does not match derived share {derived_share:.2f} from token_log (governance={gov_tokens}/{all_tokens} tokens). The reported share is inconsistent with the per-entry token log — recompute honestly.")
                # Use the derived share for the ceiling check (it's the recomputable truth)
                share = derived_share
        # P1-3: governance budget breakdown — warn if a single category dominates
        breakdown = as_dict(budget_block.get("governance_budget_breakdown"))
        if breakdown:
            total = sum(float(v) for v in breakdown.values() if isinstance(v, (int, float)))
            for cat, val in breakdown.items():
                if isinstance(val, (int, float)) and total > 0 and val / total > 0.6:
                    warn(warnings, f"cycle {idx}: governance category {cat} consumes {val/total:.0%} of budget (single-category dominance)")
                    break

        if deliverable_delta is True and first_deliverable_seen_at is None:
            first_deliverable_seen_at = idx
        if deliverable_delta is False and control_delta is True:
            no_deliverable_streak += 1
        elif deliverable_delta is True:
            no_deliverable_streak = 0
        if no_deliverable_streak > max_no_delta:
            fail(errors, f"cycle {idx}: exceeded max_cycles_without_deliverable_delta={max_no_delta}")

        if isinstance(share, (int, float)) and share > max_share:
            high_governance_streak += 1
            # Per-cycle hard fail: a single cycle breaching the governance ceiling is a
            # governance_budget_respected gate failure, not just a warning. The ceiling is
            # mode-aware (quick ≤0.25, full ≤0.40) per SKILL.md L337.
            fail(errors, f"cycle {idx}: governance_token_share {share:.2f} exceeds ceiling {max_share:.2f} for this run mode (governance_budget_respected gate)")
        else:
            high_governance_streak = 0
        if high_governance_streak >= 2:
            warn(warnings, f"cycle {idx}: governance_token_share exceeded {max_share:.2f} for 2 consecutive cycles")
        # Hard guardrail: the configured ceiling must not exceed the mode's documented cap
        # (quick_autonomy 0.25, full_genesis/parallel_advanced 0.40) without an approval_ref.
        # SKILL.md L337: quick ≤25%, full ≤40%. An unapproved ceiling above the mode cap
        # means governance silently widened beyond what the run mode permits.
        mode = str(state.get("run_mode") or state.get("bagel_mode") or "").lower()
        if mode in {"full_genesis", "full", "parallel_advanced", "parallel"}:
            mode_cap = 0.40
        else:
            mode_cap = 0.25  # quick_autonomy and unknown both get the stricter cap
        if max_share > mode_cap and not budget.get("approval_ref"):
            fail(errors, f"governance_budget.max_control_plane_share_per_cycle cannot exceed {mode_cap:.2f} for {mode or 'quick_autonomy'} mode without approval_ref (SKILL.md governance-budget rule)")
        if max_no_delta > 2 and not budget.get("approval_ref"):
            fail(errors, "governance_budget.max_cycles_without_deliverable_delta cannot exceed 2 without approval_ref")

        threshold = pressure.get("replacement_threshold_percent")
        orch = pressure.get("orchestrator_estimated_tokens")
        max_tokens = pressure.get("orchestrator_context_window_tokens")
        replacement_due = pressure.get("replacement_due")
        handoff_ref = pressure.get("handoff_ref") or cycle.get("handoff_ref")
        if isinstance(orch, int) and isinstance(max_tokens, int) and isinstance(threshold, int):
            percent = (orch / max_tokens) * 100 if max_tokens else 0
            if percent >= threshold and replacement_due is not True:
                warn(warnings, f"cycle {idx}: advisory token estimate crossed replacement threshold")

        behavioral_pressure = any(
            pressure.get(key)
            for key in ("state_load_failures", "repeated_confusion_events", "stale_context_reports")
        )
        if pressure.get("cycles_since_orchestrator_spawn", 0) and pressure.get("cycles_since_orchestrator_spawn", 0) >= pressure.get("max_cycles_since_spawn", 999999):
            behavioral_pressure = True
        if pressure.get("reference_full_reads_since_spawn", 0) and pressure.get("reference_full_reads_since_spawn", 0) >= pressure.get("max_full_reads_since_spawn", 999999):
            behavioral_pressure = True
        if behavioral_pressure and replacement_due is not True:
            fail(errors, f"cycle {idx}: behavioral context pressure requires replacement_due=true")
        if replacement_due is True and not pressure.get("replacement_due_reason"):
            fail(errors, f"cycle {idx}: replacement_due requires replacement_due_reason")
        if replacement_due is True and not handoff_ref:
            fail(errors, f"cycle {idx}: replacement_due without handoff_ref")
        elif replacement_due is True and handoff_ref and not (root / str(handoff_ref)).exists():
            fail(errors, f"cycle {idx}: handoff_ref does not exist: {handoff_ref}")

        supervisor_tokens = pressure.get("supervisor_estimated_tokens")
        supervisor_soft = pressure.get("supervisor_soft_max_tokens") or 200000
        if isinstance(supervisor_tokens, int) and isinstance(supervisor_soft, int):
            if supervisor_tokens > supervisor_soft:
                fail(errors, f"cycle {idx}: Supervisor exceeded soft max {supervisor_soft} tokens")
            elif supervisor_tokens > supervisor_soft * 0.75 and not pressure.get("supervisor_continuity_capsule_ref"):
                warn(warnings, f"cycle {idx}: Supervisor above 75% soft max without continuity capsule ref")

    if first_deliverable_seen_at is None and len(cycles) >= first_delta_by:
        fail(errors, f"no deliverable_delta by cycle {first_delta_by}")
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
    print("BAGEL telemetry check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
