#!/usr/bin/env python3
"""Lightweight BAGEL skill consistency lint.

This catches documentation contradictions that normal skill metadata validation
does not cover.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


BAD_PATTERNS = {
    r"\.bagel/worktrees": "Use sibling ../.bagel-worktrees paths, not nested .bagel/worktrees.",
    r"\.bagel/sandboxes": "Use sibling ../.bagel-worktrees paths, not old .bagel/sandboxes.",
    r"single source of truth for product state": "UPMG is optional; governance-data-model is canonical.",
    r"check_constraint\s*\(": "SQLite has no built-in check_constraint function.",
    r"severity:\s*P0 \| P1 \| P2 \| P3": "Use P0/P1/P2/INFO severity rubric.",
    r"SCORE:\s*1-10": "Use severity rubric, not numeric reviewer scores.",
    r"Static Fuzzing|fuzzing-taxonomy": "Use Missing-Belief Discovery and references/missing-belief-discovery.md.",
    r"progress-delta\.yaml": "Use progress-deltas.yaml (plural), not progress-delta.yaml.",
}

EXPECTED_REFERENCE_TITLES = {
    "references/missing-belief-discovery.md": "# Missing-Belief Discovery Taxonomy",
}


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    failures: list[str] = []

    for path in sorted(root.rglob("*")):
        if path.is_dir() or ".DS_Store" in path.name:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] in {"evals", "examples"}:
            continue
        if path.suffix not in {".md", ".json", ".yaml", ".yml", ".py"}:
            continue
        text = path.read_text(encoding="utf-8")
        rel_posix = rel.as_posix()
        expected_title = EXPECTED_REFERENCE_TITLES.get(rel_posix)
        if expected_title:
            first_heading = next((line.strip() for line in text.splitlines() if line.startswith("#")), "")
            if first_heading != expected_title:
                failures.append(f"{rel}:1: Expected title {expected_title!r}, found {first_heading!r}.")
        for pattern, message in BAD_PATTERNS.items():
            for match in re.finditer(pattern, text):
                line = text.count("\n", 0, match.start()) + 1
                failures.append(f"{rel}:{line}: {message}")
        if path.suffix == ".md":
            previous_number: int | None = None
            previous_indent: int | None = None
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = re.match(r"^(\s*)(\d+)\.\s+", line)
                if not match:
                    previous_number = None
                    previous_indent = None
                    continue
                indent = len(match.group(1))
                number = int(match.group(2))
                if previous_indent == indent and previous_number is not None:
                    expected_number = previous_number + 1
                    if number != expected_number:
                        failures.append(
                            f"{rel}:{line_no}: Expected markdown list number {expected_number}, found {number}."
                        )
                previous_number = number
                previous_indent = indent

    # Flywheel gate wiring check: every gate predicate defined in gate-predicates.md
    # that is a flywheel-critical gate must be implemented in flywheel_check.py.
    # This prevents defining a gate in docs but never wiring it to verification.
    flywheel_critical_gates = {
        "no_regression_vs_green_floor": "validate_green_floors",
        "metric_delta_has_evidence_artifact": "validate_progress_deltas",
        "review_level_consistent_with_registry": "validate_review_registry",
        "bar_raise_has_value_class": "validate_bar_raises",
    }
    gp = root / "references" / "gate-predicates.md"
    fc = root / "scripts" / "flywheel_check.py"
    if gp.exists() and fc.exists():
        gp_text = gp.read_text(encoding="utf-8")
        fc_text = fc.read_text(encoding="utf-8")
        for gate_id, func_name in flywheel_critical_gates.items():
            if gate_id in gp_text and func_name not in fc_text:
                failures.append(
                    f"flywheel gate '{gate_id}' is defined in gate-predicates.md "
                    f"but not implemented in flywheel_check.py (expected function '{func_name}')."
                )

    failures.extend(check_v11_requirements(root))
    failures.extend(check_v12_requirements(root))
    failures.extend(check_v13_innovation_memory(root))
    failures.extend(check_v14_judgment_council(root))
    failures.extend(check_v15_evaluation_iteration_orchestration(root))
    failures.extend(check_v16_supervisor_resilience(root))
    failures.extend(check_v20_measured_runtime(root))
    failures.extend(check_loading_matrix_files_exist(root))
    failures.extend(check_v34_schema_drift(root))
    failures.extend(check_version_drift(root))
    failures.extend(check_anti_pattern_refs(root))
    failures.extend(check_v41_research_wiring(root))

    if failures:
        print("BAGEL skill lint failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("BAGEL skill lint passed.")
    return 0


def check_v11_requirements(root: Path) -> list[str]:
    """v1.1 cross-file consistency checks.

    Each v1.1 mandate (mandatory loop <=25min, mandatory git, mandatory dispatch,
    depth-floored alignment, context-isolation axiom, brainstormer role, STATUS
    ownership split) asserts something in one file that other files must reflect.
    These checks catch propagation debt.
    """
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    skill = read("SKILL.md")
    align = read("references/alignment-protocol.md")
    git_gov = read("references/git-governance.md")
    loop_rt = read("references/loop-runtime.md")
    aom = read("references/agent-operating-model.md")
    gate = read("references/gate-predicates.md")

    # 1. Mandatory loop interval <= 25 min
    if "25" not in loop_rt or "HARD MAX 25" not in loop_rt:
        out.append("loop-runtime.md: v1.1 requires trigger_interval_minutes HARD MAX 25.")

    # 2. manual_resume_required renamed to degraded_resume (no bare old name left as a live mode)
    # Allow "formerly manual_resume" / "was manual_resume" explanatory mentions, but not as a mode.
    for rel, text in (("references/loop-runtime.md", loop_rt),
                       ("references/runtime-capabilities.md", read("references/runtime-capabilities.md"))):
        # A live mode line still using manual_resume_required (not in a "formerly/was" context)
        for m in re.finditer(r"manual_resume_required", text):
            window = text[max(0, m.start() - 40): m.end() + 10]
            if "formerly" not in window and "was " not in window and "renamed" not in window:
                out.append(f"{rel}: stale 'manual_resume_required' mode reference; rename to degraded_resume.")

    # 3. Mandatory git: Step 0 + project_under_version_control gate
    if "Step 0" not in git_gov or "git init" not in git_gov:
        out.append("git-governance.md: v1.1 requires Step 0 repo guarantee with git init.")
    if "project_under_version_control" not in skill:
        out.append("SKILL.md: v1.1 requires project_under_version_control hard gate.")
    if "project_under_version_control" not in gate:
        out.append("gate-predicates.md: v1.1 requires project_under_version_control predicate definition.")

    # 4. Mandatory dispatch: v1.6 uses Supervisor-first; older collapse mode uses Orchestrator.
    if "adopts the Supervisor role" not in skill and "adopts the Orchestrator role" not in skill:
        out.append("SKILL.md: requires main model to adopt Supervisor or Orchestrator role mandate.")
    # Loading Matrix row for agent-operating-model must be 'always'
    m = re.search(r"\| `references/agent-operating-model\.md` \|.*\| (\w+) \|", skill)
    if m and m.group(1) != "always":
        out.append(f"SKILL.md Loading Matrix: agent-operating-model.md must be 'always', found '{m.group(1)}'.")

    # 5. Depth-floored alignment: three tiers each need a numeric floor
    for tier in ("snap_alignment", "standard_alignment", "deep_alignment"):
        if tier not in align:
            out.append(f"alignment-protocol.md: missing depth tier {tier}.")
    if "Floor:" not in align:
        out.append("alignment-protocol.md: v1.1 requires numeric 'Floor:' per depth tier.")
    if "ONLY valid when depth = `snap_alignment`" not in align and "ONLY valid when the selected depth is `snap_alignment`" not in align:
        out.append("alignment-protocol.md: fast-path must be gated to snap_alignment only.")

    # 6. Context-Isolation Axiom + findings/reasoning boundary + orchestrator firewall
    if "Context-Isolation Axiom" not in aom:
        out.append("agent-operating-model.md: v1.1 requires the Context-Isolation Axiom section.")
    if "Findings vs reasoning" not in aom and "findings vs reasoning" not in aom.lower():
        out.append("agent-operating-model.md: v1.1 requires the findings-vs-reasoning boundary.")
    if "implementation reasoning" not in aom:
        out.append("agent-operating-model.md: orchestrator_denied firewall must block implementation reasoning.")

    # 7. Brainstormer agent exists + wired into role table + excellence-loop dispatch rule
    if not (root / "agents" / "brainstormer.md").exists():
        out.append("agents/brainstormer.md: v1.1 requires the Brainstormer role prompt.")
    if "Brainstormer" not in skill:
        out.append("SKILL.md: role table must include Brainstormer.")
    excellence = read("references/excellence-loop.md")
    if ">= 2" not in excellence or "Brainstormer" not in excellence:
        out.append("excellence-loop.md: v1.1 requires >= 2 lens-pinned Brainstormer dispatch before bar-raise.")

    # 8. STATUS.md ownership split documented
    runtime_proto = read("references/runtime-protocol.md")
    if "Ownership Split" not in runtime_proto:
        out.append("runtime-protocol.md: v1.1 requires STATUS.md Ownership Split (orchestrator mechanical / Curator narrative).")

    # 9. Runtime effectiveness auditor exists and is wired into the run loop.
    if not (root / "scripts" / "bagel_run_check.py").exists():
        out.append("scripts/bagel_run_check.py: v1.1 requires an operational run auditor.")
    if "bagel_run_check.py" not in skill and "bagel_v2_check.py" not in skill and "bagel_v3_check.py" not in skill:
        out.append("SKILL.md: long-run loop must call BAGEL runtime validators.")
    if "bagel_run_check.py" not in runtime_proto and "bagel_v2_check.py" not in runtime_proto and "bagel_v3_check.py" not in runtime_proto:
        out.append("runtime-protocol.md: runtime checks must include BAGEL runtime validators.")

    return out


def check_v12_requirements(root: Path) -> list[str]:
    """v1.2 cross-file consistency checks.

    v1.2 adds: Cartographer must verify-not-trust (run commands, multi-agent
    cross-verification, don't trust stale .bagel/ context), and loop binding
    must happen immediately after capability detection (not deferred to Build).
    Also: loop wake prompts must be pointer-only, not mechanism-stuffed.
    """
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    cart = read("agents/project-cartographer.md")
    pu = read("references/project-understanding.md")
    skill = read("SKILL.md")
    loop_rt = read("references/loop-runtime.md")
    cc = read("references/platform-claude-code.md")
    codex = read("references/platform-codex.md")
    run_check = read("scripts/bagel_run_check.py")

    # 1. Cartographer verify-dont-trust
    if "Verify, Don't Trust" not in cart and "Verify, Don" not in cart:
        out.append("agents/project-cartographer.md: v1.2 requires 'Verify, Don't Trust' principle.")
    if "documented_but_broken" not in cart:
        out.append("agents/project-cartographer.md: must record documented_but_broken when docs lie.")
    if "explorers_dispatched" not in cart:
        out.append("agents/project-cartographer.md: return format must include explorers_dispatched (multi-agent cross-verification).")
    if "baseline_manifest" not in cart or "captured_at" not in cart:
        out.append("agents/project-cartographer.md: return format must include baseline_manifest and captured_at for command evidence.")

    # 2. project-understanding cross-verification
    if "Multi-Agent Cross-Verification" not in pu and "Cross-Verification" not in pu:
        out.append("references/project-understanding.md: v1.2 requires Multi-Agent Cross-Verification section.")
    if "hint" not in pu.lower() or "not a source of truth" not in pu.lower():
        out.append("references/project-understanding.md: existing .bagel/ context must be marked as hint-not-truth.")
    if ".bagel/evidence/baseline/manifest.yaml" not in pu:
        out.append("references/project-understanding.md: v1.2 requires a baseline manifest for command evidence.")

    # 3. Immediate loop binding after capability detection
    if "immediate after capability detection" not in skill.lower():
        out.append("SKILL.md: v1.2 requires loop binding immediately after capability detection.")
    if "immediately after capability detection" not in loop_rt.lower() and "after capability detection" not in loop_rt.lower():
        out.append("references/loop-runtime.md: Start Gate must trigger immediately after capability detection.")

    # 4. Wake prompts must be pointer-only (not stuffed with mechanism instructions)
    # The old prompts had ~5 lines of mechanism; new ones should be ~2 lines pointing to state+SKILL
    for adapter_name, adapter_text in (("platform-claude-code.md", cc), ("platform-codex.md", codex)):
        # Find the scheduled/automation prompt block
        if "Execute exactly one bounded cycle" in adapter_text and "dispatch subagents for ALL" in adapter_text:
            out.append(f"references/{adapter_name}: wake prompt still stuffs mechanism instructions (bounded cycle, dispatch subagents, etc). Must be pointer-only per v1.2.")
        pointer = "Read .bagel/STATUS.md and .bagel/state.yaml"
        if pointer not in adapter_text or "follow the BAGEL Genesis SKILL.md" not in adapter_text:
            out.append(f"references/{adapter_name}: wake prompt must contain the pointer-only STATUS/state/SKILL contract.")

    # 5. Runtime auditor must enforce the v1.2 guarantees mechanically.
    for required in ("baseline_manifest", "manifest.yaml", "ARTIFACT_LENS_PACKS", "loop_binding.created_at"):
        if required not in run_check:
            out.append(f"scripts/bagel_run_check.py: v1.2 runtime audit missing {required}.")

    # 6. Stop Contract mandatory (v1.2) - the overnight "when do I stop" agreement
    align = read("references/alignment-protocol.md")
    if "Stop Contract" not in align or "MANDATORY" not in align:
        out.append("references/alignment-protocol.md: v1.2 requires a MANDATORY Stop Contract section.")
    if "stop_contract" not in align or "max_iterations" not in align:
        out.append("references/alignment-protocol.md: Stop Contract must include stop_contract schema with max_iterations.")
    if "Stop Contract" not in skill:
        out.append("SKILL.md: Vision Intake must reference the mandatory Stop Contract.")
    if "validate_stop_contract" not in run_check:
        out.append("scripts/bagel_run_check.py: must implement validate_stop_contract (Stop Contract presence check).")

    return out


def check_loading_matrix_files_exist(root: Path) -> list[str]:
    """Every File value in the Loading Matrix table must resolve to a real file.
    Prevents an agent from being told to read a reference that doesn't exist."""
    out: list[str] = []
    skill = (root / "SKILL.md").read_text(encoding="utf-8") if (root / "SKILL.md").exists() else ""
    # Extract all `references/<name>.md` from the Loading Matrix table rows
    for m in re.finditer(r"`references/([^`|]+)`", skill):
        ref_name = m.group(1).strip()
        parts = [ref_name]
        if " / " in ref_name:
            parts = [p.strip().replace("references/", "") for p in ref_name.split(" / ")]
        for part in parts:
            if part.endswith(".md") or part.endswith(".yaml"):
                full = root / "references" / part
                if not full.exists():
                    out.append(f"SKILL.md Loading Matrix references 'references/{part}' but the file does not exist.")
    return out


def check_v13_innovation_memory(root: Path) -> list[str]:
    """v1.3+ innovation and lesson-memory consistency checks."""
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    skill = read("SKILL.md")
    align = read("references/alignment-protocol.md")
    excellence = read("references/excellence-loop.md")
    recovery = read("references/recovery-protocol.md")
    governance = read("references/governance-data-model.md")
    memory_check = read("scripts/bagel_memory_check.py")

    for rel in ("references/innovation-protocol.md", "references/lesson-memory.md", "agents/product-visionary.md", "scripts/bagel_memory_check.py"):
        if not (root / rel).exists():
            out.append(f"{rel}: v1.3 requires this innovation/lesson-memory file.")

    if "Product Visionary" not in skill or "innovation-protocol.md" not in skill:
        out.append("SKILL.md: must include Product Visionary and innovation-protocol in the Loading Matrix.")
    if "lesson-memory.md" not in skill or ("bagel_memory_check.py" not in skill and "bagel_v2_check.py" not in skill and "bagel_v3_check.py" not in skill):
        out.append("SKILL.md: must include lesson-memory and run BAGEL memory validation.")
    if "Innovation Ambition" not in align or "innovation_contract" not in align:
        out.append("alignment-protocol.md: must capture Innovation Ambition and innovation_contract.")
    if "Product Visionary" not in excellence or "novelty/paradigm" not in excellence:
        out.append("excellence-loop.md: must dispatch Product Visionary for novelty/paradigm exploration.")
    if "Capture lesson" not in recovery or "lesson-memory.md" not in recovery:
        out.append("recovery-protocol.md: recovery ladder must capture reusable lessons.")
    if ".bagel/innovation/ledger.yaml" not in governance or ".bagel/lessons" not in governance:
        out.append("governance-data-model.md: must define innovation ledger and lesson memory canonical files.")
    for required in ("validate_lessons", "validate_innovation", "innovation_contract", "collect_lessons"):
        if required not in memory_check:
            out.append(f"scripts/bagel_memory_check.py: missing {required}.")

    return out


def check_v14_judgment_council(root: Path) -> list[str]:
    """v1.4 taste judgment and collective-decision consistency checks."""
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    skill = read("SKILL.md")
    taste = read("references/taste-judgment.md")
    collective = read("references/collective-decisions.md")
    flow = read("references/orchestration-flow.md")
    councilor = read("agents/judgment-councilor.md")
    excellence = read("references/excellence-loop.md")
    flywheel = read("scripts/flywheel_check.py")
    run_check = read("scripts/bagel_run_check.py")
    orchestrator = read("agents/orchestrator.md")
    innovation = read("references/innovation-protocol.md")

    for rel in (
        "references/taste-judgment.md",
        "references/collective-decisions.md",
        "references/orchestration-flow.md",
        "agents/judgment-councilor.md",
    ):
        if not (root / rel).exists():
            out.append(f"{rel}: v1.4 requires this Judgment Council file.")

    for ref in ("taste-judgment.md", "collective-decisions.md", "orchestration-flow.md"):
        if ref not in skill:
            out.append(f"SKILL.md Loading Matrix must include references/{ref}.")
    if "Judgment Councilor" not in skill:
        out.append("SKILL.md role table must include Judgment Councilor.")
    for phrase in ("strong_no", "strong_yes", "judgment_passed", "taste_adjusted"):
        if phrase not in taste:
            out.append(f"taste-judgment.md missing {phrase} rule.")
    if "Explicit Non-Use Cases" not in collective or "ordinary slice implementation" not in collective:
        out.append("collective-decisions.md must explicitly exclude routine implementation decisions.")
    for phrase in ("RUN", "Final Delivery", "Run End", "Judgment Council"):
        if phrase not in flow:
            out.append(f"orchestration-flow.md must cover {phrase}.")
    if "Judgment Councilor" not in councilor or "verdict: strong_yes | yes | neutral | no | strong_no" not in councilor:
        out.append("agents/judgment-councilor.md must define the verdict schema.")
    if "judgment_passed" not in excellence or "taste-adjusted" not in excellence:
        out.append("excellence-loop.md must include judgment_passed taste-adjusted EV selection.")
    if "validate_judgment_record" not in flywheel or "judgment_skipped_reason" not in flywheel:
        out.append("flywheel_check.py must validate bar-raise judgment records.")
    if "final_judgment_ref" not in run_check or "final_delivery" not in run_check:
        out.append("bagel_run_check.py must require final delivery Judgment Council before complete.")
    if "orchestration-flow.md" not in orchestrator:
        out.append("orchestrator.md must point to orchestration-flow.md.")
    if "Judgment Council" not in innovation:
        out.append("innovation-protocol.md must route survivor selection through Judgment Council.")

    return out


def check_v15_evaluation_iteration_orchestration(root: Path) -> list[str]:
    """v1.5 checks for control-plane separation, evaluation specs, iteration accounting, and runtime-doctor dispatch."""
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    skill = read("SKILL.md")
    orchestrator = read("agents/orchestrator.md")
    aom = read("references/agent-operating-model.md")
    align = read("references/alignment-protocol.md")
    excellence = read("references/excellence-loop.md")
    flow = read("references/orchestration-flow.md")
    run_check = read("scripts/bagel_run_check.py")

    for rel in (
        "agents/evaluation-architect.md",
        "agents/runtime-doctor.md",
        "references/evaluation-framework.md",
        "references/iteration-contract.md",
    ):
        if not (root / rel).exists():
            out.append(f"{rel}: v1.5 requires this file.")

    for phrase in ("Evaluation Architect", "Runtime Doctor", "evaluation-framework.md", "iteration-contract.md"):
        if phrase not in skill:
            out.append(f"SKILL.md must wire v1.5 phrase/reference: {phrase}.")
    if "control plane" not in skill.lower() or "not the user's deliverable" not in skill:
        out.append("SKILL.md must state that .bagel control-plane artifacts are not user deliverables.")
    for phrase in ("Runtime Doctor", "Evaluation Architect", "must not personally perform iterative environment debugging"):
        if phrase not in orchestrator:
            out.append(f"orchestrator.md missing v1.5 dispatch boundary: {phrase}.")
    for phrase in ("lane type", "control_plane", "Runtime Doctor", "Evaluation Architect"):
        if phrase not in aom:
            out.append(f"agent-operating-model.md missing v1.5 context-boundary term: {phrase}.")
    if "not user deliverables" not in align and "not user deliverable" not in align:
        out.append("alignment-protocol.md must prevent treating alignment artifacts as user deliverables.")
    for phrase in ("Completing all currently known user-requested goals counts as", "dispatch_evaluation_architect", "anti_gaming_note"):
        if phrase not in excellence:
            out.append(f"excellence-loop.md missing v1.5 iteration/evaluation rule: {phrase}.")
    for phrase in ("Evaluation Architect", "Runtime Doctor", "lane_type: deliverable", "control-plane"):
        if phrase not in flow:
            out.append(f"orchestration-flow.md missing v1.5 flow term: {phrase}.")
    for phrase in (
        "validate_task_queue_not_control_plane",
        "validate_evaluation_and_iteration_state",
        "CONTROL_PLANE_TERMS",
        "iterations_completed",
        "anti_gaming_note",
    ):
        if phrase not in run_check:
            out.append(f"bagel_run_check.py missing v1.5 runtime audit: {phrase}.")

    return out


def check_v16_supervisor_resilience(root: Path) -> list[str]:
    """v1.6 checks for Supervisor layer, Claude Code nesting, and resumability."""
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    skill = read("SKILL.md")
    supervisor = read("agents/supervisor.md")
    sup_ref = read("references/supervisor-resilience.md")
    cc = read("references/platform-claude-code.md")
    runtime = read("references/runtime-protocol.md")
    loop = read("references/loop-runtime.md")
    governance = read("references/governance-data-model.md")
    aom = read("references/agent-operating-model.md")
    run_check = read("scripts/bagel_run_check.py")

    for rel in ("agents/supervisor.md", "references/supervisor-resilience.md"):
        if not (root / rel).exists():
            out.append(f"{rel}: v1.6 requires this Supervisor resilience file.")
    for phrase in ("Supervisor", "supervisor-resilience.md", "resume-capsule.md", "collapsed_no_true_subagents"):
        if phrase not in skill:
            out.append(f"SKILL.md missing v1.6 Supervisor wiring: {phrase}.")
    for phrase in ("Orchestrator respawn", "resume-capsule.md", "heartbeat.yaml", "user-facing alignment"):
        if phrase not in supervisor:
            out.append(f"agents/supervisor.md missing v1.6 role term: {phrase}.")
    for phrase in ("nested_supervisor", "Respawn Procedure", "User Proxy Rule", "Claude Code Nested Agent Guidance", "Context Tree Principle", "replace_not_compact"):
        if phrase not in sup_ref:
            out.append(f"supervisor-resilience.md missing required section/term: {phrase}.")
    for phrase in ("Nested Supervisor Pattern", "Supervisor heartbeat", "BAGEL Orchestrator subagent"):
        if phrase not in cc:
            out.append(f"platform-claude-code.md missing nested Supervisor mapping: {phrase}.")
    for phrase in ("resume-capsule.md", "Supervisor Resume Capsule", "respawn Orchestrator"):
        if phrase not in runtime:
            out.append(f"runtime-protocol.md missing Supervisor resume term: {phrase}.")
    if "heartbeat_interval_minutes: 30" not in loop or "nested_supervisor" not in loop or "replace_not_compact" not in loop:
        out.append("loop-runtime.md must define nested_supervisor heartbeat interval shape.")
    for phrase in ("supervisor_heartbeat", "supervisor_resume_capsule", ".bagel/supervisor/"):
        if phrase not in governance:
            out.append(f"governance-data-model.md missing Supervisor canonical source/schema: {phrase}.")
    for phrase in ("Supervisor-To-Orchestrator Flow", "supervisor_denied", "user-facing alignment", "Replace-Not-Compact Rule"):
        if phrase not in aom:
            out.append(f"agent-operating-model.md missing Supervisor context hygiene rule: {phrase}.")
    for phrase in ("validate_supervisor", "SUPERVISOR_MODES", "resume-capsule.md", "current_orchestrator", "replace_not_compact"):
        if phrase not in run_check:
            out.append(f"bagel_run_check.py missing Supervisor runtime audit: {phrase}.")

    return out


def check_v20_measured_runtime(root: Path) -> list[str]:
    """v2.0 checks for measured autonomy, replay, telemetry, and scope control."""
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    skill = read("SKILL.md")
    runtime_caps = read("references/runtime-capabilities.md")
    runtime_proto = read("references/runtime-protocol.md")
    gate = read("references/gate-predicates.md")
    run_check = read("scripts/bagel_run_check.py")
    flywheel = read("scripts/flywheel_check.py")
    v3_check = read("scripts/bagel_v3_check.py")
    v2_check = read("scripts/bagel_v2_check.py") + v3_check

    for rel in (
        "references/v2-measured-runtime.md",
        "references/telemetry-protocol.md",
        "references/evidence-protocol.md",
        "references/handoff-integrity.md",
        "references/scope-control.md",
        "references/alignment-freshness.md",
        "references/reference-loading.md",
    ):
        if not (root / rel).exists():
            out.append(f"{rel}: v2.0 requires this measured-runtime reference.")
        elif Path(rel).name not in skill:
            out.append(f"SKILL.md Loading Matrix must include {rel}.")

    for script in (
        "runtime_proof_check.py",
        "deliverable_delta_check.py",
        "bagel_telemetry_check.py",
        "resume_integrity_check.py",
        "evidence_replay_check.py",
        "scope_check.py",
        "evaluation_quality_check.py",
        "expert_strategy_check.py",
        "roi_check.py",
        "supervisor_boundary_check.py",
        "alignment_freshness_check.py",
        "reference_load_check.py",
        "bagel_cross_check.py",
    ):
        if not (root / "scripts" / script).exists():
            out.append(f"scripts/{script}: v2.0 requires this validator.")
        elif script != "bagel_cross_check.py" and script not in v2_check:
            out.append(f"bagel_v2_check.py must call {script}.")

    for phrase in ("adapter_claim", "observed", "proof_ref", "not proof"):
        if phrase not in runtime_caps:
            out.append(f"runtime-capabilities.md missing V2 proof-model term: {phrase}.")
    for phrase in ("validate_runtime_capability_proofs", "observed_true", "proof_exists"):
        if phrase not in run_check:
            out.append(f"bagel_run_check.py missing V2 runtime proof audit: {phrase}.")
    for phrase in ("delta_type", "ITERATION_VALUE_CLASSES", "blocking_concern"):
        if phrase not in flywheel:
            out.append(f"flywheel_check.py missing V2 flywheel audit: {phrase}.")
    for phrase in ("delta_type", ".bagel/telemetry/cycles.yaml"):
        if phrase not in runtime_proto:
            out.append(f"runtime-protocol.md missing V2 runtime term: {phrase}.")
    if "bagel_v2_check.py" not in runtime_proto and "bagel_v3_check.py" not in runtime_proto:
        out.append("runtime-protocol.md missing V2/V3 runtime validator command.")
    for gate_id in (
        "runtime_capability_observed_with_proof",
        "handoff_validation_passed",
        "action_idempotency_safe",
        "evidence_replay_integrity_passed",
        "governance_budget_respected",
        "scope_delta_within_contract",
        "alignment_freshness_current",
    ):
        if gate_id not in gate:
            out.append(f"gate-predicates.md missing V2 gate: {gate_id}.")
    if not (root / "evals" / "long-run" / "tasks.yaml").exists():
        out.append("evals/long-run/tasks.yaml: v2.0 requires long-run benchmark scaffold.")
    if "Measured Autonomous Runtime" not in skill:
        out.append("SKILL.md must name V2 as the Measured Autonomous Runtime.")

    out.extend(check_v30_expert_autonomy(root))

    return out


def check_v30_expert_autonomy(root: Path) -> list[str]:
    """v3.0 checks for expert autonomy and anti-laziness enforcement."""
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    skill = read("SKILL.md")
    orch = read("agents/orchestrator.md")
    supervisor = read("agents/supervisor.md")
    gate = read("references/gate-predicates.md")
    v2_check = read("scripts/bagel_v2_check.py") + read("scripts/bagel_v3_check.py")

    for rel in (
        "agents/principal-expert.md",
        "references/expert-autonomy.md",
        "references/domain-excellence-model.md",
        "references/problem-framing.md",
        "references/leverage-map.md",
        "references/evaluation-critic.md",
        "references/expert-strategy-council.md",
        "references/breakthrough-search.md",
        "references/roi-controller.md",
    ):
        if not (root / rel).exists():
            out.append(f"{rel}: v3.0 requires this expert-autonomy file.")
        elif Path(rel).name not in skill and not rel.startswith("agents/"):
            out.append(f"SKILL.md Loading Matrix must include {rel}.")

    if "Principal Expert" not in skill or "Principal Expert" not in orch:
        out.append("SKILL.md and orchestrator.md must wire the Principal Expert role.")
    for phrase in ("High-Impact Decision Gate", "domain excellence model", "leverage map", "Evaluation Critic", "ROI state"):
        if phrase not in orch:
            out.append(f"orchestrator.md missing V3 high-impact decision invariant: {phrase}.")
    for phrase in ("Do not run BAGEL validators", "boundary_policy", "role_guard", "small task", "current_skill_overrides_stale_state"):
        if phrase not in supervisor:
            out.append(f"supervisor.md missing hard Supervisor boundary term: {phrase}.")
    sup_ref = read("references/supervisor-resilience.md")
    for phrase in ("Current Skill Beats Stale State", "Role Guard", "task_size_exemption_used", "supervisor_boundary_check.py"):
        if phrase not in sup_ref:
            out.append(f"supervisor-resilience.md missing anti-laziness enforcement term: {phrase}.")
    sup_check = read("scripts/supervisor_boundary_check.py")
    for phrase in ("task_size_exemption_used", "current_skill_overrides_stale_state", "spawn_orchestrator", "role_guard"):
        if phrase not in sup_check:
            out.append(f"supervisor_boundary_check.py missing anti-laziness validator term: {phrase}.")
    for script in ("evaluation_quality_check.py", "expert_strategy_check.py", "roi_check.py", "supervisor_boundary_check.py", "runtime_proof_check.py", "deliverable_delta_check.py", "dispatch_envelope_check.py", "emergency_stop_check.py"):
        if script not in v2_check:
            out.append(f"bagel_v2_check.py must call V3 validator {script}.")
    for gate_id in (
        "domain_excellence_model_present",
        "problem_framing_locked",
        "leverage_map_current",
        "evaluation_critic_passed",
        "expert_decision_present",
        "roi_controller_positive_or_switched",
        "supervisor_boundary_respected",
        "supervisor_role_guard_passed",
        "dispatch_envelope_valid",
        "emergency_stop_preserves_state",
    ):
        if gate_id not in gate:
            out.append(f"gate-predicates.md missing V3 gate: {gate_id}.")

    out.extend(check_v31_executable_expert_runtime(root))

    return out


def check_v31_executable_expert_runtime(root: Path) -> list[str]:
    """v3.1 executable expert runtime checks."""
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    skill = read("SKILL.md")
    flow = read("references/orchestration-flow.md")
    expert = read("references/expert-autonomy.md")
    principal = read("agents/principal-expert.md")
    council = read("references/expert-strategy-council.md")
    run_check = read("scripts/bagel_run_check.py")
    expert_check = read("scripts/expert_strategy_check.py")
    eval_check = read("scripts/evaluation_quality_check.py")
    roi_check = read("scripts/roi_check.py")
    dispatch_check = read("scripts/dispatch_envelope_check.py")

    for phrase in ("Authoritative Boot Sequence", "align_protection", "autonomous_build", "Build/Iterate before Stop Contract is forbidden"):
        if phrase not in skill:
            out.append(f"SKILL.md missing V3.1 boot invariant: {phrase}.")
    for phrase in ("RUN START", "ALIGN / CALIBRATE", "Expert Strategy Council", "Principal Expert locks initial strategy", "Build unlock gate"):
        if phrase not in flow:
            out.append(f"orchestration-flow.md missing V3.1 executable flow phrase: {phrase}.")
    for rel in (
        "agents/domain-expert.md",
        "agents/systems-architect.md",
        "agents/evaluation-skeptic.md",
        "agents/innovation-strategist.md",
        "agents/user-proxy.md",
        "agents/risk-officer.md",
        "references/dispatch-envelope.md",
        "references/emergency-stop.md",
        "scripts/bagel_v3_check.py",
        "scripts/dispatch_envelope_check.py",
        "scripts/emergency_stop.py",
        "scripts/emergency_stop_check.py",
    ):
        if not (root / rel).exists():
            out.append(f"{rel}: V3.1 requires this file.")
    for phrase in ("schema_version: expert_decision_v1", "selected_option_id", "kill_criteria", "domain_model_ref"):
        if phrase not in principal or phrase not in expert:
            out.append(f"Principal Expert / expert-autonomy schema missing {phrase}.")
    for phrase in ("real subagent dispatches", "output_ref", "deadlocked", "needs_probe"):
        if phrase not in council:
            out.append(f"expert-strategy-council.md missing V3.1 dispatch/quorum rule: {phrase}.")
    for phrase in ("collect_dispatches", "schema_version", "breakthrough_quality", "GENERIC_TERMS"):
        if phrase not in expert_check:
            out.append(f"expert_strategy_check.py missing V3.1 enforcement term: {phrase}.")
    for phrase in ("metric_discrimination_check", "bad_example", "surface_overfit_risk"):
        if phrase not in eval_check:
            out.append(f"evaluation_quality_check.py missing V3.1 discrimination term: {phrase}.")
    for phrase in ("hard_value", "soft_value", "soft-value-only", "expert_layer_mode"):
        if phrase not in roi_check:
            out.append(f"roi_check.py missing V3.1 ROI term: {phrase}.")
    for phrase in ("loop_phase", "single_session_honesty", "Stop Contract"):
        if phrase not in run_check:
            out.append(f"bagel_run_check.py missing V3.1 lifecycle/review term: {phrase}.")
    for phrase in ("normalized relative", "locks", "context_ref"):
        if phrase not in dispatch_check:
            out.append(f"dispatch_envelope_check.py missing V3.1 preflight term: {phrase}.")
    for rel in (
        "references/expert-packs/software-product.md",
        "references/expert-packs/research-experiment.md",
        "references/expert-packs/writing-longform.md",
        "references/expert-packs/design-ui.md",
        "references/expert-packs/data-analysis.md",
        "references/expert-packs/ops-sre.md",
    ):
        if not (root / rel).exists():
            out.append(f"{rel}: V3.1 requires artifact expert pack.")
    return out


def check_v34_schema_drift(root: Path) -> list[str]:
    """V3.4 semantic integrity: detect schema drift between the canonical agent/schema docs
    and the validator scripts that enforce them. This prevents the exact failure mode seen
    in V3.3 (validator reading fields the schema never declared)."""
    out: list[str] = []
    import re

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8") if p.exists() else ""

    # --- 1. expert_decision_v1: principal-expert.md YAML block vs expert_strategy_check.py required tuple ---
    pe = read("agents/principal-expert.md")
    # extract field keys from the ```yaml expert_decision: ... ``` block
    yaml_match = re.search(r"```yaml\s*\nexpert_decision:\s*\n(.*?)```", pe, re.DOTALL)
    schema_fields: set[str] = set()
    if yaml_match:
        for line in yaml_match.group(1).splitlines():
            m = re.match(r"  ([a-z_]+):\s?", line)
            if m:
                schema_fields.add(m.group(1))
    esc = read("scripts/expert_strategy_check.py")
    # extract the required = ( ... ) tuple INSIDE validate_expert_decision only
    fn_match = re.search(r"def validate_expert_decision\(.*?\n((?:.|\n)*?)(?=\ndef )", esc)
    req_match = re.search(r'required\s*=\s*\(([^)]+)\)', fn_match.group(1) if fn_match else esc, re.DOTALL)
    enforced_fields: set[str] = set()
    if req_match:
        for token in req_match.group(1).split(","):
            t = token.strip().strip('"').strip("'")
            if t:
                enforced_fields.add(t)
    if schema_fields and enforced_fields:
        # schema-only fields: declared in schema, validated by expert_strategy_check.py via
        # conditional/derived logic rather than the unconditional required tuple.
        SCHEMA_ONLY = {
            "schema_version",      # checked at line: schema_version != "expert_decision_v1"
            "hard_stop_triggered", # metadata flag, checked separately
            "risk_level",          # P0-3: derived risk checks use this conditionally
            "risk_basis",          # P0-3: nested under risk_level, validated when present
            "authority_ref",       # required only when reversibility is costly/irreversible
        }
        only_in_schema = schema_fields - enforced_fields - SCHEMA_ONLY
        only_in_enforced = enforced_fields - schema_fields
        for f in sorted(only_in_schema):
            out.append(f"schema drift: expert_decision field {f!r} declared in principal-expert.md but NOT enforced in expert_strategy_check.py required tuple")
        for f in sorted(only_in_enforced):
            out.append(f"schema drift: expert_decision field {f!r} enforced in expert_strategy_check.py but NOT declared in principal-expert.md schema")

    # --- 2. council verdict schema: councilor prompts have a shared shape; expert_strategy_check validates it ---
    # the council output validator checks: perspective, agent_id, session_id, verdict, key_reason, evidence_refs, missing_evidence
    expected_verdict_fields = {"perspective", "agent_id", "session_id", "verdict", "key_reason", "evidence_refs", "missing_evidence"}
    for councilor in ("domain-expert", "systems-architect", "evaluation-skeptic", "innovation-strategist", "user-proxy", "risk-officer"):
        cpe = read(f"agents/{councilor}.md")
        vm = re.search(r"```yaml\s*\nexpert_council_verdict:\s*\n(.*?)```", cpe, re.DOTALL)
        if not vm:
            continue
        declared: set[str] = set()
        for line in vm.group(1).splitlines():
            m = re.match(r"\s{2}(\w+):\s", line)
            if m:
                declared.add(m.group(1))
        missing = expected_verdict_fields - declared
        for f in sorted(missing):
            out.append(f"schema drift: {councilor}.md expert_council_verdict missing expected field {f!r}")

    return out


def check_version_drift(root: Path) -> list[str]:
    """v3.7 cross-file version-consistency checks (Judge S1 finding C5+C6) + P1-2 version pin.

    Catches: (1) deprecated bagel_v2_check.py references in agent/reference prompts
    (the real suite is bagel_v3_check.py); (2) the "compact" instruction in orchestrator.md
    contradicting the replace-not-compact policy; (3) SKILL.md gate-index under-counting
    gate-predicates.md (the static list was replaced with a pointer, but verify it stays
    a pointer, not a re-enumerated list that drifts); (4) P1-2: a canonical VERSION file
    pins the current version; live labels in scripts/SKILL.md must match it, while
    historical changelog headings (### v3.x) and named test ids are exempt.
    """
    out: list[str] = []
    # C6a: no agent/reference prompt should reference the deprecated bagel_v2_check.py
    for mdfile in sorted(root.glob("agents/*.md")) + sorted(root.glob("references/*.md")):
        content = mdfile.read_text(encoding="utf-8", errors="ignore")
        if "bagel_v2_check.py" in content:
            out.append(f"{mdfile.relative_to(root)}: references deprecated bagel_v2_check.py — use bagel_v3_check.py (the v2 file is a legacy shim)")
    # C6b: orchestrator.md must not instruct self-compaction (replace-not-compact policy)
    orch_path = root / "agents/orchestrator.md"
    orch = orch_path.read_text(encoding="utf-8", errors="ignore") if orch_path.exists() else ""
    if re.search(r"(?im)^\s*compact\s+(after|or discard|context)", orch):
        out.append("agents/orchestrator.md: instructs self-compaction which contradicts the replace-not-compact policy (supervisor-resilience.md). Use handoff-and-replace.")
    # C5: SKILL.md Hard Gates section should reference gate-predicates.md, not re-enumerate
    skill_path = root / "SKILL.md"
    skill = skill_path.read_text(encoding="utf-8", errors="ignore") if skill_path.exists() else ""
    if "## Hard Gates" in skill:
        gates_section = skill.split("## Hard Gates")[1].split("##")[0]
        if "gate-predicates.md" not in gates_section:
            out.append("SKILL.md: Hard Gates section does not reference gate-predicates.md as the authoritative source — a static list here will drift from the real predicate table")
    # P1-2: canonical VERSION file is the single source of truth for the current version.
    version_file = root / "VERSION"
    if not version_file.exists():
        out.append("VERSION: missing — the canonical version pin file (single source of truth) must exist at repo root.")
    else:
        canon_major_minor = ".".join(version_file.read_text(encoding="utf-8").strip().split(".")[:2])  # e.g. "3.9"
        # Live labels in scripts (docstrings, output banners) must match the canonical version.
        # Exempt: historical changelog headings (### v3.x lines in README.md) and named test ids.
        for pyfile in sorted(root.glob("scripts/*.py")):
            if pyfile.name == "skill_lint.py":
                continue
            content = pyfile.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"[Vv]3\.(\d)", content):
                found_minor = m.group(1)
                if found_minor != canon_major_minor.split(".")[1]:
                    line_no = content.count("\n", 0, m.start()) + 1
                    out.append(
                        f"{pyfile.relative_to(root)}:{line_no}: live version label 'V3.{found_minor}' "
                        f"diverges from canonical VERSION '{canon_major_minor}' — update the label or VERSION."
                    )
    return out


def check_anti_pattern_refs(root: Path) -> list[str]:
    """Anti-Patterns table references must not use bare `Lxx` line numbers.

    Line-number citations in a frequently-edited prose file drift silently
    (an earlier audit found ~13 of 15 stale). Section-anchor references
    ("§ Roles", "§ Boot Sequence step 8") are stable across edits. This check
    fails if the Anti-Patterns table reintroduces any `L\\d+` citation, so the
    drift cannot recur unnoticed.
    """
    out: list[str] = []
    skill_path = root / "SKILL.md"
    if not skill_path.exists():
        return out
    text = skill_path.read_text(encoding="utf-8")
    # Scope to the Anti-Patterns table region only (between its heading and
    # the next ## heading), so legitimate Lxx elsewhere (if any) is untouched.
    if "## Anti-Patterns" not in text:
        return out
    table_region = text.split("## Anti-Patterns", 1)[1].split("\n## ", 1)[0]
    for m in re.finditer(r"\bL\d+\b", table_region):
        line_no = text.count("\n", 0, text.index(table_region) + m.start()) + 1
        out.append(
            f"SKILL.md:{line_no}: Anti-Patterns table uses bare line-ref 'L{m.group(0)[1:]}' "
            f"— line numbers drift; use a section-anchor reference like '§ Boot Sequence step 8' instead."
        )
    return out


def check_v41_research_wiring(root: Path) -> list[str]:
    """V4.1 research governance must stay wired into docs, suite, and gates."""
    out: list[str] = []

    def read(rel: str) -> str:
        p = root / rel
        return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

    suite = read("scripts/bagel_v3_check.py")
    gates = read("references/gate-predicates.md")
    skill = read("SKILL.md")
    research = read("references/research-governance.md")
    checker = read("scripts/research_governance_check.py")
    replay = read("scripts/evidence_replay_check.py")
    auditor = read("scripts/ci_auditor.py")
    verifier = read("scripts/audit_verifier.py")
    lab_check = read("scripts/research_lab_check.py")
    workflow = read(".github/workflows/bagel-audit.yml")
    ci_doc = read("references/ci-audit.md")
    lab_doc = read("references/research-lab-automation.md")
    required_gates = {
        "research_mode_declared",
        "experiment_plan_preregistered",
        "experiment_event_log_current",
        "confirmatory_claim_not_posthoc",
    }
    if "research_governance_check.py" not in suite:
        out.append("scripts/bagel_v3_check.py: V4.1 requires research_governance_check.py in CHECKS.")
    if "research_lab_check.py" not in suite:
        out.append("scripts/bagel_v3_check.py: V4.1 requires research_lab_check.py in CHECKS.")
    if "environment_lock_check.py" not in suite:
        out.append("scripts/bagel_v3_check.py: V4.3 requires environment_lock_check.py in CHECKS.")
    if "ci_readiness_check.py" not in suite:
        out.append("scripts/bagel_v3_check.py: V4.1 requires ci_readiness_check.py in CHECKS.")
    if "liveness_check.py" not in suite:
        out.append("scripts/bagel_v3_check.py: V4.1 requires liveness_check.py as a top-level CHECK.")
    for gate_id in required_gates:
        if gate_id not in gates:
            out.append(f"references/gate-predicates.md: missing V4.1 research gate {gate_id}.")
    for token in ("protocol_execution", "autonomous_researcher", "research_autonomy.mode"):
        if token not in skill:
            out.append(f"SKILL.md: missing V4.1 research mode token {token}.")
    for token in ("preregistered_plan_sha256", "research_design_amendment", "authority_ref"):
        if token not in checker and token not in research:
            out.append(f"V4.1 research governance missing {token} in checker/reference.")
    if "metric_recompute" not in replay:
        out.append("scripts/evidence_replay_check.py: V4.1 requires metric_recompute mode.")
    for token in ("research_run_matrix", "allowed_llm_entrypoints", "no_experiment_before_build_unlock"):
        if token not in lab_check + lab_doc + skill:
            out.append(f"research lab automation wiring missing {token}.")
    for token in ("walk_strings", "EXECUTION_RE", "CANONICAL_LLM_ENTRYPOINT"):
        if token not in lab_check:
            out.append(f"scripts/research_lab_check.py: V4.3 requires recursive command/LLM scan token {token}.")
    for token in ("capability_observed_with_proof", "registry_confirms_reviewer", "fresh_preregistration_valid"):
        if token not in checker:
            out.append(f"scripts/research_governance_check.py: V4.3 amendment governance missing {token}.")
    coverage_map = read("evals/coverage_map.py")
    grader = read("evals/mechanical_grader.py")
    for token in ("design_amendment", "renamed executable field", "coverage_map"):
        if token == "coverage_map":
            if not coverage_map:
                out.append("evals/coverage_map.py: V4.3 requires eval coverage governance.")
        elif token not in grader:
            out.append(f"evals/mechanical_grader.py: V4.3 missing fixture coverage token {token}.")
    env_lock = read("scripts/environment_lock_check.py")
    if "research_environment_lock_v1" not in env_lock:
        out.append("scripts/environment_lock_check.py: V4.3 environment-lock schema check missing.")
    for token in ("preregistration.yaml", "extracts_from_sha256", "TRIVIAL_EXTRACTOR_RE", "run_ref"):
        if token not in auditor:
            out.append(f"scripts/ci_auditor.py: V4.1 CI closure missing {token}.")
    for token in ("openssl-sha256", "BAGEL_AUDIT_PRIVATE_KEY_PEM"):
        if token not in auditor + verifier + workflow + ci_doc:
            out.append(f"CI audit asymmetric signing docs/wiring missing {token}.")
    if "set -euo pipefail" not in workflow or "PIPESTATUS[0]" not in workflow:
        out.append(".github/workflows/bagel-audit.yml: CI auditor must preserve auditor exit status through tee with pipefail/PIPESTATUS.")
    if re.search(r"Optional but recommended.*branch protection", ci_doc, re.I | re.S):
        out.append("references/ci-audit.md: branch protection must be documented as required, not optional.")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
